from ecas.ingestion.csv_importer import (
    ARCHIVE_METADATA_FIELDS,
    EXPECTED_ARCHIVE_SOURCES,
    OPTIONAL_ARCHIVE_NUMERIC_FIELDS,
    REQUIRED_ARCHIVE_NUMERIC_FIELDS,
    import_spectrum_csv,
    WASP39B_SCHEMA,
)

def test_import_archive_schema_column_mapping(tmp_path):
    """Verify WASP-39b columns are remapped to canonical names."""
    path = tmp_path / "wasp.csv"
    
    # Build valid fixture with all 21 required source headers from EXPECTED_ARCHIVE_SOURCES
    header_row = ",".join(EXPECTED_ARCHIVE_SOURCES)
    
    # Create row values that match the header order exactly
    def _make_row_values(start_wave=400.0, idx=0):
        """Generate a single valid row aligned to EXPECTED_ARCHIVE_SOURCES in exact order."""
        values = []
        
        for field in EXPECTED_ARCHIVE_SOURCES:
            if field == "centralwavelng":
                value = f"{start_wave + 0.12 + idx * 0.01:.4f}"
            elif field == "bandwidth":
                value = "50"
            elif field == "pl_trandep":
                value = f"-{start_wave * 0.0001 + 0.01 + idx * 0.002:.4f}"
            elif field == "pl_trandeperr1":
                value = "0.2"
            elif field == "pl_trandeperr2":
                value = "0.3"
            elif field == "pl_trandep_authors":
                value = "Feinstein et al. 2023"
            elif field == "pl_ratror":
                value = "0.6"
            elif field == "pl_ratrorerr1":
                value = "0.5"
            elif field == "pl_ratrorerr2":
                value = "0.5"
            elif field == "pl_ratror_authors":
                value = "Feinstein et al. 2023"
            elif field == "pl_radj":
                value = "0.0"
            elif field == "pl_radjerr1":
                value = "0.0"
            elif field == "pl_radjerr2":
                value = "0.0"
            elif field == "pl_radj_authors":
                value = "Feinstein et al. 2023"
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
            
            values.append(value)
        
        return ",".join(values)
    
    fixture_row_1 = _make_row_values(start_wave=400.0, idx=1)
    fixture_row_2 = _make_row_values(start_wave=400.56, idx=2)
    
    content = f"{header_row}\n{fixture_row_1}\n{fixture_row_2}"
    path.write_text(content)
    
    spectrum = import_spectrum_csv(path, archive_schema=WASP39B_SCHEMA)
    
    # After fix, columns should be canonical names only (wavelength and signal added)
    assert "wavelength" in spectrum.columns
    assert "signal" in spectrum.columns
    assert "centralwavelng" not in spectrum.columns  # Original name replaced
    # All source columns are retained alongside canonical mappings (21 + 2 = 23)
    expected_cols = tuple(EXPECTED_ARCHIVE_SOURCES) + ("wavelength", "signal")
    assert len(spectrum.columns) == len(expected_cols)
    assert spectrum.columns[:len(EXPECTED_ARCHIVE_SOURCES)] == expected_cols[:len(EXPECTED_ARCHIVE_SOURCES)]
