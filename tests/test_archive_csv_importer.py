"""Archive-specific tests for the WASP-39b CSV import path."""

import csv
from pathlib import Path

import pytest

from ecas.ingestion.csv_importer import (
    ARCHIVE_METADATA_FIELDS,
    EXPECTED_ARCHIVE_SOURCES,
    OPTIONAL_ARCHIVE_NUMERIC_FIELDS,
    REQUIRED_ARCHIVE_NUMERIC_FIELDS,
    WASP39B_SCHEMA,
    SpectrumImportError,
    import_spectrum_csv,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
WASP39B_CSV = (
    REPO_ROOT
    / "data"
    / "WASP-39b"
    / "table_WASP-39-b-Feinstein-et-al.-2023.csv"
)


def _valid_archive_row():
    """Return a minimally valid row aligned to EXPECTED_ARCHIVE_SOURCES."""
    row = {}
    for field in REQUIRED_ARCHIVE_NUMERIC_FIELDS:
        row[field] = "1.25"
    for field in OPTIONAL_ARCHIVE_NUMERIC_FIELDS:
        row[field] = "0.25"
    for field in ARCHIVE_METADATA_FIELDS:
        row[field] = "Example source"
    return [row[field] for field in EXPECTED_ARCHIVE_SOURCES]


def _write_archive_csv(path, headers=None, rows=None):
    headers = list(EXPECTED_ARCHIVE_SOURCES if headers is None else headers)
    rows = [_valid_archive_row()] if rows is None else rows
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(headers)
        writer.writerows(rows)
    return path


def _set_cell(row, field, value):
    changed = list(row)
    changed[list(EXPECTED_ARCHIVE_SOURCES).index(field)] = value
    return changed


def test_imports_real_wasp39b_archive_preserving_source_columns():
    """Test that the real WASP-39b CSV file can be imported correctly."""
    result = import_spectrum_csv(WASP39B_CSV, archive_schema=WASP39B_SCHEMA)

    assert result.row_count == 331
    
    # After import, columns are canonical names (wavelength, signal) 
    # added alongside source columns (centralwavelng, pl_trandep) for traceability
    expected_columns = (
        "wavelength",      # canonical mapping for centralwavelng  
        *EXPECTED_ARCHIVE_SOURCES,  # All 21 source columns preserved with original names
        "signal",          # canonical mapping for pl_trandep
    )
    
    assert result.columns == expected_columns
    assert "centralwavelng" in result.columns  # Source column preserved alongside canonical
    assert "pl_trandep" in result.columns
    
    # Verify the canonical mappings work correctly
    assert result.rows[0]["wavelength"] == pytest.approx(
        float(result.rows[0]["centralwavelng"])
    )
    assert result.rows[0]["signal"] == pytest.approx(
        float(result.rows[0]["pl_trandep"])
    )


def test_unsupported_archive_schema_is_rejected(tmp_path):
    path = _write_archive_csv(tmp_path / "archive.csv")

    with pytest.raises(
        SpectrumImportError, match="Unsupported archive schema\\."
    ):
        import_spectrum_csv(
            path,
            archive_schema={"wavelength": "some_other_column", "signal": "pl_trandep"},
        )


@pytest.mark.parametrize(
    "header_change",
    [
        "duplicate",
        "empty",
        "missing",
        "unexpected",
    ],
)
def test_invalid_archive_headers_are_rejected(tmp_path, header_change):
    headers = list(EXPECTED_ARCHIVE_SOURCES)
    if header_change == "duplicate":
        headers[1] = headers[0]
    elif header_change == "empty":
        headers[1] = ""
    elif header_change == "missing":
        headers.remove("pl_trandep")
    elif header_change == "unexpected":
        headers.append("unexpected_extra_column")

    row = _valid_archive_row()
    if header_change == "missing":
        row.pop(list(EXPECTED_ARCHIVE_SOURCES).index("pl_trandep"))
    elif header_change == "unexpected":
        row.append("extra")

    path = _write_archive_csv(
        tmp_path / f"{header_change}.csv", headers=headers, rows=[row]
    )
    with pytest.raises(SpectrumImportError):
        import_spectrum_csv(path, archive_schema=WASP39B_SCHEMA)


@pytest.mark.parametrize("row_width", ["short", "long"])
def test_archive_rows_with_wrong_field_count_are_rejected(tmp_path, row_width):
    row = _valid_archive_row()
    if row_width == "short":
        row.pop()
    else:
        row.append("unexpected")

    path = _write_archive_csv(tmp_path / f"{row_width}.csv", rows=[row])
    with pytest.raises(SpectrumImportError):
        import_spectrum_csv(path, archive_schema=WASP39B_SCHEMA)


@pytest.mark.parametrize("field", sorted(REQUIRED_ARCHIVE_NUMERIC_FIELDS))
@pytest.mark.parametrize("bad_value", ["", "   ", "not-a-number", "nan", "inf", "-inf"])
def test_required_archive_numeric_values_must_be_finite_numbers(
    tmp_path, field, bad_value
):
    row = _set_cell(_valid_archive_row(), field, bad_value)
    path = _write_archive_csv(tmp_path / "bad_required.csv", rows=[row])

    with pytest.raises(SpectrumImportError):
        import_spectrum_csv(path, archive_schema=WASP39B_SCHEMA)


@pytest.mark.parametrize("field", sorted(OPTIONAL_ARCHIVE_NUMERIC_FIELDS))
def test_blank_optional_archive_numeric_values_become_none(tmp_path, field):
    row = _set_cell(_valid_archive_row(), field, "   ")
    path = _write_archive_csv(tmp_path / "blank_optional.csv", rows=[row])

    result = import_spectrum_csv(path, archive_schema=WASP39B_SCHEMA)
    assert result.rows[0][field] is None


@pytest.mark.parametrize("field", sorted(OPTIONAL_ARCHIVE_NUMERIC_FIELDS))
@pytest.mark.parametrize("bad_value", ["not-a-number", "nan", "inf", "-inf"])
def test_invalid_optional_archive_numeric_values_are_rejected(
    tmp_path, field, bad_value
):
    row = _set_cell(_valid_archive_row(), field, bad_value)
    path = _write_archive_csv(tmp_path / "bad_optional.csv", rows=[row])

    with pytest.raises(SpectrumImportError):
        import_spectrum_csv(path, archive_schema=WASP39B_SCHEMA)


@pytest.mark.parametrize("field", sorted(ARCHIVE_METADATA_FIELDS))
def test_archive_metadata_is_trimmed_and_blank_metadata_becomes_empty_string(
    tmp_path, field
):
    row = _set_cell(_valid_archive_row(), field, "  Example citation  ")
    second_row = _set_cell(_valid_archive_row(), field, "   ")
    path = _write_archive_csv(
        tmp_path / "metadata.csv", rows=[row, second_row]
    )

    result = import_spectrum_csv(path, archive_schema=WASP39B_SCHEMA)
    assert result.rows[0][field] == "Example citation"
    assert result.rows[1][field] == ""


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("pl_trandeperr1", "-0.01396"),
        ("pl_trandeperr2", "-0.01396"),
        ("pl_ratrorerr1", "-0.00048"),
        ("pl_ratrorerr2", "-0.00048"),
        ("pl_radjerr1", "-0.0328"),
        ("pl_radjerr2", "-0.0328"),
    ],
)
def test_finite_signed_archive_uncertainties_keep_their_sign(
    tmp_path, field, value
):
    row = _set_cell(_valid_archive_row(), field, value)
    path = _write_archive_csv(tmp_path / "signed_errors.csv", rows=[row])

    result = import_spectrum_csv(path, archive_schema=WASP39B_SCHEMA)
    assert result.rows[0][field] == pytest.approx(float(value))
