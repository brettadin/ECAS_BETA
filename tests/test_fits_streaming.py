"""Bounded FITS containers with real-derived measurements.

Large zero image planes are structural engineering fixtures, not fabricated
spectra or scientific-success evidence. Spectral values come from the bundled
unchanged NASA observation.
"""
from pathlib import Path
import hashlib
import struct
import tracemalloc

import pytest

from ecas.ingestion.csv_importer import SpectrumImportError
from ecas.ingestion.nasa_table import import_transmission_table
from ecas.ingestion.tabular_formats import import_fits_bintable_spectrum

ROOT = Path(__file__).resolve().parents[1]


def card(key, value=""):
    return ((f"{key:<8}= {value}" if key != "END" else "END").ljust(80)).encode("ascii")


def header(pairs):
    raw = b"".join(card(k, v) for k, v in pairs) + card("END")
    return raw.ljust((len(raw) + 2879) // 2880 * 2880, b" ")


def primary(image_bytes=0):
    return header([("SIMPLE", "T"), ("BITPIX", "8"), ("NAXIS", "1" if image_bytes else "0")]
                  + ([("NAXIS1", str(image_bytes))] if image_bytes else []))


def measured_rows():
    s = import_transmission_table(ROOT / "data/NASA/2026-10-27/feinstein-2023.tbl").spectrum
    return [(r["wavelength"], r["signal"]) for r in s.rows[:8]]


def table_header(*, changes=None, extra=()):
    pairs = {"XTENSION": "'BINTABLE'", "BITPIX": "8", "NAXIS": "2", "NAXIS1": "16",
             "NAXIS2": "8", "PCOUNT": "0", "GCOUNT": "1", "TFIELDS": "2",
             "TTYPE1": "'wavelength'", "TFORM1": "'1D'", "TUNIT1": "'um'",
             "TTYPE2": "'transit_depth'", "TFORM2": "'1D'", "TUNIT2": "'%'",
             "SPEC_TYP": "'Transmission'", "OBJECT": "'WASP/39''s b'"}
    pairs.update(changes or {})
    return header(list(pairs.items()) + list(extra))


def table_data(rows=None):
    raw = b"".join(struct.pack(">dd", *r) for r in (rows or measured_rows()))
    return raw.ljust((len(raw) + 2879) // 2880 * 2880, b"\0")


@pytest.mark.parametrize("image_in_primary", [True, False])
def test_84mib_image_container_streams_small_real_spectrum(tmp_path, image_in_primary, monkeypatch):
    path = tmp_path / "large-structural-image.fits"
    image_size = 84 * 1024 * 1024
    padded = (image_size + 2879) // 2880 * 2880
    with path.open("wb") as stream:
        stream.write(primary(image_size if image_in_primary else 0))
        if not image_in_primary:
            stream.write(header([("XTENSION", "'IMAGE'"), ("BITPIX", "8"), ("NAXIS", "1"),
                                 ("NAXIS1", str(image_size)), ("PCOUNT", "0"), ("GCOUNT", "1")]))
        stream.seek(padded - 1, 1)
        stream.write(b"\0")  # sparse structural image; never used as measurements
        stream.write(table_header()); stream.write(table_data())
    assert path.stat().st_size > 84 * 1024 * 1024
    def forbidden_read_bytes(*args):
        raise AssertionError("FITS importer must not read the entire container")
    monkeypatch.setattr(Path, "read_bytes", forbidden_read_bytes)
    tracemalloc.start()
    try:
        result = import_fits_bintable_spectrum(path)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 8 * 1024 * 1024
    assert result.row_count == 8
    assert [(r["wavelength"], r["signal"]) for r in result.rows] == measured_rows()
    assert dict(result.metadata)["pl_name"] == "WASP/39's b"
    assert dict(result.metadata)["fits_hdu_index"] == ("1" if image_in_primary else "2")
    from ecas.observations import hash_source_file
    from ecas.ui.main_window import _hash_file_if_present
    with path.open("rb") as stream:
        independent_digest = hashlib.file_digest(stream, "sha256").hexdigest()
    assert hash_source_file(path) == independent_digest
    assert _hash_file_if_present(path) == independent_digest


def test_fits_scaling_and_slashes_are_preserved(tmp_path):
    path = tmp_path / "scaled.fits"
    original = measured_rows()
    stored = [((x - .25) / 2, (y - .1) / 3) for x, y in original]
    path.write_bytes(primary() + table_header(extra=(("TSCAL1", "2D0"), ("TZERO1", ".25"),
                                                   ("TSCAL2", "3"), ("TZERO2", ".1"))) + table_data(stored))
    result = import_fits_bintable_spectrum(path)
    for row, (x, y) in zip(result.rows, original):
        assert row["wavelength"] == pytest.approx(x)
        assert row["signal"] == pytest.approx(y)
    assert "TSCALn" in dict(result.metadata)["fits_numeric_conversion"]


@pytest.mark.parametrize("changes,match", [
    ({"TFORM2": "2D"}, "scalar numeric"),
    ({"NAXIS2": "100001"}, "NAXIS2"),
    ({"NAXIS1": "-16"}, "NAXIS1"),
    ({"NAXIS2": "999999999999999999999"}, "dimensions"),
    ({"TSCAL2": "NaN"}, "TSCAL"),
])
def test_invalid_dimensions_formats_and_scaling_rejected(tmp_path, changes, match):
    path = tmp_path / "invalid.fits"
    with path.open("wb") as stream:
        stream.write(primary() + table_header(changes=changes))
        nrows = int(changes.get("NAXIS2", 8))
        if 0 < nrows <= 100001:
            padded = (16 * nrows + 2879) // 2880 * 2880
            stream.seek(padded - 1, 1); stream.write(b"\0")
        else:
            stream.write(table_data())
    with pytest.raises(SpectrumImportError, match=match):
        import_fits_bintable_spectrum(path)


def test_ambiguous_image_only_and_truncated_containers_rejected(tmp_path):
    path = tmp_path / "ambiguous.fits"
    path.write_bytes(primary() + (table_header() + table_data()) * 2)
    with pytest.raises(SpectrumImportError, match="Ambiguous"):
        import_fits_bintable_spectrum(path)
    path.write_bytes(primary(2880) + b"\0" * 2880)
    with pytest.raises(SpectrumImportError, match="image-only"):
        import_fits_bintable_spectrum(path)
    path.write_bytes(primary() + table_header(changes={"NAXIS2": "400"}) + table_data())
    with pytest.raises(SpectrumImportError, match="truncated"):
        import_fits_bintable_spectrum(path)


def test_unrelated_vector_table_can_precede_scalar_spectrum(tmp_path):
    path = tmp_path / "extensions.fits"
    unrelated = table_header(changes={"TTYPE1": "'detector'", "TTYPE2": "'flags'", "TFORM1": "'2D'"})
    path.write_bytes(primary() + unrelated + table_data() + table_header() + table_data())
    result = import_fits_bintable_spectrum(path)
    assert result.row_count == 8 and dict(result.metadata)["fits_hdu_index"] == "2"


def test_event_list_is_not_misrepresented_as_a_spectrum(tmp_path):
    path = tmp_path / "structural-event-list.fits"
    path.write_bytes(primary() + table_header(changes={"TTYPE1": "'TIME'", "TTYPE2": "'PI'", "EXTNAME": "'EVENTS'"}) + table_data())
    with pytest.raises(SpectrumImportError, match="event-list.*spectral extraction"):
        import_fits_bintable_spectrum(path)


def test_cross_section_unit_with_slash_is_not_truncated(tmp_path):
    from ecas.identification.library import discover_library
    refs = discover_library(ROOT / "data/ECAS_Spectral_Library").datasets
    source = next(r for r in refs if r.modality == "UV-Vis" and r.molecule == "H2O")
    rows = [(r["wavelength"], r["signal"]) for r in source.spectrum.rows[:8]]
    path = tmp_path / "real-derived-uv.fits"
    path.write_bytes(primary() + table_header(changes={"TTYPE2": "'cross_section'", "TUNIT1": "'nm'",
                                                      "TUNIT2": "'cm^2/molecule'", "SPEC_TYP": "'Laboratory Cross Section'"}) + table_data(rows))
    result = import_fits_bintable_spectrum(path)
    assert result.signal_unit == "cm^2/molecule"
    assert result.rows[0]["signal"] == rows[0][1]


def test_decoded_cell_and_header_budgets_reject_before_allocating(tmp_path):
    path = tmp_path / "bounded.fits"
    # Header describes a structural oversized table; no scientific values used.
    changes = {"NAXIS1": "256", "NAXIS2": "40000", "TFIELDS": "32"}
    with path.open("wb") as stream:
        stream.write(primary() + table_header(changes=changes))
        stream.seek((256 * 40000 + 2879) // 2880 * 2880 - 1, 1); stream.write(b"\0")
    with pytest.raises(SpectrumImportError, match="cell limit"):
        import_fits_bintable_spectrum(path)
    path.write_bytes(card("SIMPLE", "T").ljust(2880 * 128, b" "))
    with pytest.raises(SpectrumImportError, match="header exceeds"):
        import_fits_bintable_spectrum(path)


def test_integer_nulls_are_missing_and_required_measurements_cannot_be_null(tmp_path):
    path = tmp_path / "integer-null.fits"
    # Auxiliary integer flags are structural metadata. Real spectral values
    # remain the source-derived floating wavelength/transit-depth pairs.
    changes = {"NAXIS1": "20", "TFIELDS": "3", "TTYPE3": "'quality'", "TFORM3": "'1J'", "TNULL3": "-999"}
    raw = b"".join(struct.pack(">ddi", x, y, -999) for x, y in measured_rows())
    raw = raw.ljust(2880, b"\0")
    path.write_bytes(primary() + table_header(changes=changes) + raw)
    result = import_fits_bintable_spectrum(path)
    assert all(row["quality"] is None for row in result.rows)
    invalid = b"".join(struct.pack(">id", -999, y) for _, y in measured_rows()).ljust(2880, b"\0")
    path.write_bytes(primary() + table_header(changes={"NAXIS1": "12", "TFORM1": "'1J'", "TNULL1": "-999"}) + invalid)
    with pytest.raises(SpectrumImportError, match="Missing required coordinate"):
        import_fits_bintable_spectrum(path)
