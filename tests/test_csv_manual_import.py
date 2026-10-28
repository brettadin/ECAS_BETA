"""Regression tests for importing the supported archive schema manually."""

from ecas.ingestion.csv_importer import (
    EXPECTED_ARCHIVE_SOURCES,
    import_spectrum_csv,
    WASP39B_SCHEMA,
)


def test_import_archive_schema_column_mapping(tmp_path):
    """Synthetic archive data retains source columns alongside canonical aliases."""
    path = tmp_path / "wasp.csv"

    # Build a valid fixture with all required source headers in their expected order.
    header_row = ",".join(EXPECTED_ARCHIVE_SOURCES)

    def make_row_values(start_wave=400.0, idx=0):
        values = []
        for field in EXPECTED_ARCHIVE_SOURCES:
            if field == "centralwavelng":
                value = f"{start_wave + 0.12 + idx * 0.01:.4f}"
            elif field == "bandwidth":
                value = "50"
            elif field == "pl_trandep":
                value = f"-{start_wave * 0.0001 + 0.01 + idx * 0.002:.4f}"
            elif field in {"pl_trandeperr1", "pl_trandeperr2"}:
                value = "0.2" if field == "pl_trandeperr1" else "0.3"
            elif field in {
                "pl_trandep_authors",
                "pl_ratror_authors",
                "pl_radj_authors",
            }:
                value = "Feinstein et al. 2023"
            elif field == "pl_ratror":
                value = "0.6"
            elif field in {"pl_ratrorerr1", "pl_ratrorerr2"}:
                value = "0.5"
            elif field == "pl_radj":
                value = "0.0"
            elif field in {"pl_radjerr1", "pl_radjerr2"}:
                value = "0.0"
            elif field == "pl_tranmid":
                value = "0.8"
            elif field == "pl_tranmiderr1":
                value = "0.4"
            elif field == "pl_tranmiderr2":
                value = "0.5"
            elif field == "st_rad":
                value = "0.7"
            elif field == "st_raderr1":
                value = "0.7"
            elif field == "st_raderr2":
                value = "0.2"
            elif field == "st_rad_authors":
                value = "Faedi et al. 2011"
            else:  # Keep fixture generation explicit if the schema changes.
                raise AssertionError(f"Fixture has no value for archive field {field!r}")

            values.append(value)

        return ",".join(values)

    path.write_text(
        f"{header_row}\n"
        f"{make_row_values(start_wave=400.0, idx=1)}\n"
        f"{make_row_values(start_wave=400.56, idx=2)}\n",
        encoding="utf-8",
    )

    spectrum = import_spectrum_csv(path, archive_schema=WASP39B_SCHEMA)
    
    # Canonical aliases supplement rather than replace the source data. Compare
    # source order independently of alias placement; the real-data regression
    # in test_archive_csv_importer.py checks the current full output order.
    assert len(spectrum.columns) == len(EXPECTED_ARCHIVE_SOURCES) + 2
    assert set(spectrum.columns) == set(EXPECTED_ARCHIVE_SOURCES) | {"wavelength", "signal"}
    assert tuple(name for name in spectrum.columns if name in EXPECTED_ARCHIVE_SOURCES) == EXPECTED_ARCHIVE_SOURCES
    assert spectrum.row_count == 2
    for row in spectrum.rows:
        assert set(row) == set(spectrum.columns)
        assert row["wavelength"] == row["centralwavelng"]
        assert row["signal"] == row["pl_trandep"]
