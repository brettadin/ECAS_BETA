"""Frozen real NASA product plus explicitly corrupted derivative fixtures."""
from hashlib import sha256
import json
from pathlib import Path

import pytest

from ecas.ingestion.nasa_table import import_transmission_table
from ecas.ingestion.csv_importer import SpectrumImportError, WASP39B_SCHEMA, import_spectrum_csv


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/NASA/2026-10-27/feinstein-2023.tbl"


def test_real_table_preserves_measurements_units_flags_and_citations():
    result = import_transmission_table(SOURCE)
    spectrum = result.spectrum
    assert spectrum.row_count == 331 and len(spectrum.columns) == 31
    assert result.source_sha256 == sha256(SOURCE.read_bytes()).hexdigest()
    provenance = json.loads(SOURCE.with_suffix(".tbl.provenance.json").read_text())
    assert provenance["success"] and provenance["sha256"] == result.source_sha256
    assert spectrum.axis_unit == "microns" and spectrum.signal_unit == "%"
    assert spectrum.signal_type == "Transmission"
    assert dict(result.metadata)["REFERENCE"] == "Feinstein et al. 2022"
    assert spectrum.rows[0]["pl_trandeperr2"] < 0
    assert spectrum.rows[0]["pl_tranmid"] is None
    assert spectrum.rows[0]["pl_trandep_url"].startswith("https://ui.adsabs.harvard.edu/")
    csv = import_spectrum_csv(ROOT / "data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv",
                              archive_schema=WASP39B_SCHEMA)
    assert csv.row_count == spectrum.row_count
    for old, new in zip(csv.rows, spectrum.rows):
        for name in csv.columns:
            assert old[name] == new[name], name


@pytest.mark.parametrize("field,value", [("pl_trandeplim", "1"), ("pl_trandeplim", "null"),
    ("pl_trandeplim", "0.5"), ("centralwavelng", "nan"), ("pl_trandep", "inf"),
    ("pl_trandep", "null"), ("pl_trandep", "bad"), ("pl_trandeperr2", "nan")])
def test_bad_numeric_or_flagged_rows_are_not_plotted(tmp_path, field, value):
    lines = SOURCE.read_text().splitlines()
    header = next(line for line in lines if line.startswith("|"))
    bars = [i for i, c in enumerate(header) if c == "|"]
    names = [header[a+1:b].strip().lower() for a, b in zip(bars, bars[1:])]
    col = names.index(field)
    row = next(i for i, line in enumerate(lines) if line.strip() and not line.startswith(("|", "\\")))
    a, b = bars[col]+1, bars[col+1]
    lines[row] = lines[row][:a] + value.rjust(b-a) + lines[row][b:]
    path = tmp_path / "corrupted.tbl"
    path.write_text("\n".join(lines))
    with pytest.raises(SpectrumImportError):
        import_transmission_table(path)


@pytest.mark.parametrize("mutation", ["eclipse", "headers", "boundary", "no-data", "duplicate", "oversize"])
def test_unsupported_or_malformed_tables_fail_explicitly(tmp_path, mutation):
    text = SOURCE.read_text()
    if mutation == "eclipse": text = text.replace("SPEC_TYPE = Transmission", "SPEC_TYPE = Eclipse")
    elif mutation == "headers": text = text.replace("|        double|", "|double|", 1)
    elif mutation == "boundary": text = text.replace("        0.63096", "X       0.63096", 1)
    elif mutation == "no-data": text = "\n".join(l for l in text.splitlines() if l.startswith(("|", "\\")))
    elif mutation == "duplicate": text = text.replace("PL_TRANDEPERR1", "PL_TRANDEPERR2", 1)
    else: text = "x" * 1048577
    path = tmp_path / "unsupported.tbl"
    path.write_text(text)
    with pytest.raises(SpectrumImportError):
        import_transmission_table(path)


def _replace_cell(line, bars, column, value):
    a, b = bars[column] + 1, bars[column + 1]
    return line[:a] + value.rjust(b - a) + line[b:]


@pytest.mark.parametrize("marker", ["", "null"])
@pytest.mark.parametrize("field", ["pl_tranmid", "centralwavelng", "pl_trandep", "pl_trandeplim"])
def test_blank_numeric_cells_obey_declared_null_and_required_fields(tmp_path, marker, field):
    lines = SOURCE.read_text().splitlines()
    headers = [i for i, line in enumerate(lines) if line.startswith("|")]
    header = lines[headers[0]]
    bars = [i for i, c in enumerate(header) if c == "|"]
    names = [header[a+1:b].strip().lower() for a, b in zip(bars, bars[1:])]
    column = names.index(field)
    lines[headers[3]] = _replace_cell(lines[headers[3]], bars, column, marker)
    first = headers[-1] + 1
    if marker == "":
        # Changing the column's declaration also changes every existing null
        # representation in this synthetic derivative of the captured table.
        a, b = bars[column] + 1, bars[column + 1]
        for index in range(first, len(lines)):
            if lines[index][a:b].strip() == "null":
                lines[index] = _replace_cell(lines[index], bars, column, "")
    lines[first] = _replace_cell(lines[first], bars, column, "")
    path = tmp_path / "blank.tbl"
    path.write_text("\n".join(lines), encoding="utf-8")
    if field == "pl_tranmid" and marker == "":
        result = import_transmission_table(path)
        assert result.spectrum.rows[0][field] is None
        assert result.spectrum.row_count == 331
        assert result.source_sha256 == sha256(path.read_bytes()).hexdigest()
    else:
        with pytest.raises(SpectrumImportError):
            import_transmission_table(path)


@pytest.mark.parametrize("casing", [str.upper, str.title])
def test_type_casing_preserves_measurements_and_units(tmp_path, casing):
    lines = SOURCE.read_text().splitlines()
    headers = [i for i, line in enumerate(lines) if line.startswith("|")]
    lines[headers[1]] = casing(lines[headers[1]])
    path = tmp_path / "type-case.tbl"
    path.write_text("\n".join(lines), encoding="utf-8")
    original = import_transmission_table(SOURCE)
    changed = import_transmission_table(path)
    assert changed.spectrum.rows == original.spectrum.rows
    assert changed.column_units == original.column_units
    assert changed.metadata == original.metadata
    assert changed.source_sha256 == sha256(path.read_bytes()).hexdigest()
