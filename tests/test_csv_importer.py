
import pytest

from ecas.ingestion.csv_importer import (
    SpectrumImportError,
    import_spectrum_csv,
)
from ecas.models.spectrum import SpectrumData


def test_import_valid_csv(tmp_path):
    path = tmp_path / "spectrum.csv"
    path.write_text(
        "wavelength,signal,uncertainty\n"
        "400,12.5,0.2\n"
        "401,13.1,0.3\n",
        encoding="utf-8",
    )

    result = import_spectrum_csv(path)

    # The importer should return the structured model.
    assert isinstance(result, SpectrumData)
    assert result.row_count == 2
    assert result.source_file == path.resolve()
    assert result.columns == ("wavelength", "signal", "uncertainty")

    # Required measurements and optional uncertainty remain numeric.
    assert result.rows[0]["wavelength"] == 400
    assert result.rows[0]["signal"] == 12.5
    assert result.rows[0]["uncertainty"] == 0.2

    # The importer must not invent scientific metadata.
    assert result.axis_unit is None
    assert result.signal_unit is None
    assert result.signal_type is None


def test_preserves_additional_columns(tmp_path):
    path = tmp_path / "spectrum.csv"
    path.write_text(
        "wavelength,signal,source_note\n"
        "400,12.5,reference lamp\n",
        encoding="utf-8",
    )

    result = import_spectrum_csv(path)

    assert result.columns == ("wavelength", "signal", "source_note")
    assert result.rows[0]["source_note"] == "reference lamp"


def test_missing_required_column(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text(
        "wavelength,intensity\n400,12\n",
        encoding="utf-8",
    )

    with pytest.raises(
        SpectrumImportError, match="Missing required columns"
    ):
        import_spectrum_csv(path)


def test_rejects_non_numeric_signal(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text(
        "wavelength,signal\n400,unknown\n",
        encoding="utf-8",
    )

    with pytest.raises(
        SpectrumImportError, match="must be numeric"
    ):
        import_spectrum_csv(path)


def test_rejects_negative_uncertainty(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text(
        "wavelength,signal,uncertainty\n400,12,-0.5\n",
        encoding="utf-8",
    )

    with pytest.raises(
        SpectrumImportError, match="non-negative"
    ):
        import_spectrum_csv(path)


def test_rejects_infinite_values(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text(
        "wavelength,signal\n400,inf\n",
        encoding="utf-8",
    )

    with pytest.raises(
        SpectrumImportError, match="must be finite"
    ):
        import_spectrum_csv(path)


def test_blank_uncertainty_is_preserved_and_warned(tmp_path):
    """Blank uncertainty must remain missing, not become zero."""
    path = tmp_path / "spectrum.csv"
    path.write_text(
        "wavelength,signal,uncertainty\n"
        "400,12.5,0.2\n"
        "401,13.1,\n"
        "402,14.0,0.3\n",
        encoding="utf-8",
    )

    result = import_spectrum_csv(path)

    # All three measurements should be retained.
    assert result.row_count == 3

    # The blank uncertainty is represented explicitly as missing.
    assert result.rows[1]["uncertainty"] is None

    # The importer must report the limitation without rejecting the file.
    assert len(result.warnings) == 1
    assert "1 measurement row(s)" in result.warnings[0]
    assert "not zero uncertainty" in result.warnings[0]
