### **Plan v17 — Final Correctness Fixes Before ACT** ###

---

## Defect Resolution Summary (v16 → v17)

| Issue # | Plan v16 Defect | v17 Correction |
|---------|-----------------|----------------|
| 1 | Required fields (`centralwavelng`, `pl_transdep`) returned `None` for blank; added warnings instead of raising | Raise `SpectrumImportError` immediately when required field is blank/whitespace-only/malformed/non-finite |
| 2 | Finite check only applied to `"numeric"` type, not `"signed-numeric"` | Apply `math.isfinite(num)` before returning **all** numeric types; preserve signed error offsets exactly |
| 3 | Row shape validation checked before adding canonical fields (`wavelength`, `signal`) → rejected valid rows | Add canonical fields after parsing all 21 sources, then validate final row has exactly 23 keys |
| 4 | Archive headers mutated global `COLUMN_ALIASES` and compared against generic source names | Isolate archive-specific normalization; do not use or mutate `COLUMN_ALIASES`; preserve input order; validate exact 21 expected sources |
| 5 | `normalized_sources + ("wavelength", "signal")` type mismatch (list + tuple) → crash | Convert final columns to tuple explicitly, e.g. `tuple(normalized_sources + ["wavelength", "signal"])` |
| 6 | NaN/Inf tests used placeholder headers; `-inf` test wrote second row after import attempt | All validation tests use complete 21-column header and fully populated rows; separate fixtures for `nan`, `inf`, `-inf` on each required field |
| 7 | Mixed exception names (`SpectrumInfoError`) → inconsistent error signaling | Use `SpectrumImportError` consistently for all archive-mode failures (unsupported schema, malformed fields, invalid headers) |
| 8 | Required-field warning path would bypass rejection logic | Remove warning paths entirely; required-field validation raises immediately on any non-finite or blank value |

---

## Corrected Implementation Plan (v17)

### 1. Strict Schema Validation (No Generic Fallback for Invalid Schemas)

```python
def _validate_archive_schema(schema: dict[str, str] | None) -> tuple[bool, dict[str, str] | None]:
    """
    Validate supplied archive schema.
    Returns (is_supported, validated_schema):
      - is_supported = True only for exact WASP-39 b match
      - is_supported = False → generic mode invoked
      - raises SpectrumImportError for any unsupported schema (not silent fallback)
    """
    
    # None → generic path (explicitly permitted; no exception raised)
    if schema is None:
        return False, None  # Generic mode
    
    # Check that schema is a dict with exactly two keys
    if not isinstance(schema, dict):
        raise SpectrumImportError("Unsupported archive schema.")
    
    required_keys = frozenset(["wavelength", "signal"])
    if set(schema.keys()) != required_keys:
        raise SpectrumImportError("Unsupported archive schema.")
    
    # Validate exact mappings
    expected_mappings = {
        "wavelength": "centralwavelng",
        "signal": "pl_transdep"
    }
    
    for canonical_name, expected_source in expected_mappings.items():
        if schema[canonical_name] != expected_source:
            raise SpectrumImportError("Unsupported archive schema.")
    
    # Schema is exactly WASP-39 b → archive mode permitted
    return True, schema


def import_spectrum_csv(
    file_path: str | Path,
    archive_schema: dict[str, str] = None,  # Public API unchanged
) -> SpectrumData:
    
    is_supported, validated_schema = _validate_archive_schema(archive_schema)
    
    if not is_supported:
        # Generic path invoked (archive_schema=None or unsupported schema triggers generic mode)
        return _import_generic_spectrum_csv(file_path)
    
    # Archive-specific path continues here...
    ...


def _import_generic_spectrum_csv(file_path: str | Path) -> SpectrumData:
    """Existing generic importer logic (unchanged)."""
    # Existing code runs here; handles all generic CSV imports
    ...
```

---

### 2. Field Classification Schema (All 21 Fields Explicitly Classified)

```python
ARCHIVE_FIELD_CLASSIFICATIONS: dict[str, tuple[str, str]] = {
    # Numeric fields: blank → None, malformed/inf → raise; finite check before return
    "centralwavelng": ("numeric", "required"),      # required; never None
    "bandwidth": ("numeric", "optional"),           # optional blank → None
    "pl_transdep": ("numeric", "required"),         # required; never None
    "pl_transdeperr1": ("signed-numeric", "optional"),  # signed error; preserve ±; finite check
    "pl_transdeperr2": ("signed-numeric", "optional"),
    
    "pl_ratror": ("numeric", "optional"),
    "pl_ratrorerr1": ("signed-numeric", "optional"),
    "pl_ratrorerr2": ("signed-numeric", "optional"),
    
    "pl_radj": ("numeric", "optional"),
    "pl_radjerr1": ("signed-numeric", "optional"),
    "pl_radjerr2": ("signed-numeric", "optional"),
    
    "pl_transmid": ("numeric", "optional"),
    "pl_transmiderr1": ("signed-numeric", "optional"),
    "pl_transmiderr2": ("signed-numeric", "optional"),
    
    "st_rad": ("numeric", "optional"),
    "st_raderr1": ("signed-numeric", "optional"),
    "st_raderr2": ("signed-numeric", "optional"),
    
    # Metadata/author fields: stripped strings; blank → ""
    "pl_transdep_authors": ("metadata", "optional"),
    "pl_ratror_authors": ("metadata", "optional"),
    "pl_radj_authors": ("metadata", "optional"),
    "st_rad_authors": ("metadata", "optional"),
}
```

---

### 3. Archive-Isolated Header Normalization (No Generic Aliases)

```python
# Archive-specific header normalization rules (isolated; no dependency on COLUMN_ALIASES)
ARCHIVE_HEADER_NORMALIZATION: dict[str, str] = {
    # Example: if archive source uses alternate casing/spaces; define mappings here
    # Leave empty if archive headers must match expected sources exactly.
}

# Expected archive source names (canonical input order preserved)
EXPECTED_ARCHIVE_SOURCES = frozenset([
    "centralwavelng", "bandwidth", "pl_transdep",
    "pl_transdeperr1", "pl_transdeperr2", "pl_transdep_authors",
    "pl_ratror", "pl_ratrorerr1", "pl_ratrorerr2", "pl_ratror_authors",
    "pl_radj", "pl_radjerr1", "pl_radjerr2", "pl_radj_authors",
    "pl_transmid", "pl_transmiderr1", "pl_transmiderr2",
    "st_rad", "st_raderr1", "st_raderr2", "st_rad_authors"
])


def _normalize_archive_header(header: str) -> str:
    """Normalize archive source header without using COLUMN_ALIASES."""
    # Strip whitespace and lowercase; optionally apply archive-specific rules
    cleaned = header.strip().lower()
    
    # Archive headers must match expected sources exactly after normalization
    return cleaned


def _import_archive_schema_csv(
    file_path: Path,
    schema: dict[str, str]  # Validated WASP-39 b schema; not used directly here
) -> SpectrumData:
    
    path = Path(file_path).resolve()
    
    if not path.exists() or not path.is_file():
        raise SpectrumImportError(f"File does not exist: {path}")
    
    if path.suffix.lower() != ".csv":
        raise SpectrumImportError("Expected a .csv file.")
    
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames or any(
                fn is None or not fn.strip() for fn in reader.fieldnames
            ):
                raise SpectrumImportError("CSV contains an empty column name.")
            
            # Archive-specific header normalization (no COLUMN_ALIASES)
            original_headers = reader.fieldnames
            normalized_sources: list[str] = []
            
            for header in original_headers:
                # Normalize without mutating global aliases
                cleaned = _normalize_archive_header(header)
                
                # Reject duplicate normalized headers
                if cleaned in normalized_sources:
                    raise SpectrumImportError(
                        "CSV contains duplicate or conflicting column names"
                    )
                
                # Check for canonical-name collisions (generic rejection path)
                if cleaned in ("wavelength", "signal") and \
                   cleaned not in ("centralwavelng", "pl_transdep"):
                    raise SpectrumImportError(
                        f"CSV contains column named '{cleaned}' that conflicts with required sources."
                    )
                
                normalized_sources.append(cleaned)
            
            # Validate all 21 expected source fields present exactly
            if set(normalized_sources) != EXPECTED_ARCHIVE_SOURCES:
                missing = EXPECTED_ARCHIVE_SOURCES - set(normalized_sources)
                raise SpectrumImportError(
                    f"Missing required archive headers: {', '.join(sorted(missing))}"
                )
            
            # Parse all rows using field classification
            parsed_rows: list[dict[str, CellValue]] = []
            
            for line_number, raw_row in enumerate(reader, start=2):
                if None in raw_row.values():
                    raise SpectrumImportError(
                        f"Line {line_number}: more values than header columns."
                    )
                
                # Parse all 21 fields with classification
                parsed_row: dict[str, CellValue] = {}
                
                for field_name in normalized_sources:
                    parsed_row[field_name] = _parse_archive_field(field_name, raw_row.get(field_name))
                
                parsed_rows.append(parsed_row)
            
            if not parsed_rows:
                raise SpectrumImportError("CSV contains no spectrum data rows.")
            
            # Construct final columns: 21 normalized sources + canonical aliases
            # Convert to tuple; avoid list+tuple concatenation error
            columns_tuple = tuple(normalized_sources + ["wavelength", "signal"])
            
            # Build final rows by adding canonical aliases to each parsed row
            model_rows: list[dict[str, CellValue]] = []
            
            for parsed_row in parsed_rows:
                # Add canonical aliases after all 21 sources parsed
                row_dict: dict[str, CellValue] = dict(parsed_row)
                row_dict["wavelength"] = parsed_row["centralwavelng"]
                row_dict["signal"] = parsed_row["pl_transdep"]
                
                # Now validate final shape (should be exactly 23 keys)
                if len(row_dict) != 23:
                    raise SpectrumImportError(
                        f"Row has {len(row_dict)} columns instead of 23."
                    )
                
                model_rows.append(row_dict)
            
            return SpectrumData(
                source_file=path,
                columns=columns_tuple,
                rows=tuple(model_rows),
                warnings=[],  # No warnings for valid rows
            )
```

---

### 4. Field Parsing with Required/Optional Enforcement and Finite Check

```python
def _parse_archive_field(field_name: str, raw_value: str | None) -> CellValue:
    """Parse archive source field with exact classification."""
    
    if field_name not in ARCHIVE_FIELD_CLASSIFICATIONS:
        raise SpectrumImportError(
            f"Unrecognized archive header '{field_name}'. "
            "All 21 source fields must be classified explicitly."
        )
    
    field_type, field_required = ARCHIVE_FIELD_CLASSIFICATIONS[field_name]
    
    # Strip whitespace for all fields first
    value_str: str = (raw_value or "").strip()
    
    if field_type == "metadata":
        # Metadata fields: strip whitespace; blank → ""
        return value_str
    
    elif field_type in ("numeric", "signed-numeric"):
        # All numeric types: blank after strip → None for optional, raise for required
        if field_required and value_str == "":
            raise SpectrumImportError(
                f"Line 2:'{field_name}' must be provided (required)."
            )
        
        if value_str == "" and not field_required:
            return None  # Optional blank → None
        
        try:
            num = float(value_str)
        except (TypeError, ValueError):
            raise SpectrumImportError(
                f"Line 2:'{field_name}' must be numeric."
            ) from None
        
        # Apply finite check to ALL numeric types before returning
        if not math.isfinite(num):
            raise SpectrumImportError(
                f"Line 2:'{field_name}' must be finite (nan/inf/-inf not allowed)."
            )
        
        return num  # Finite numeric value accepted; signed-numeric preserves sign
```

---

### 5. Complete Malformed-Value Test Fixtures (All 21 Columns)

```python
# Complete 21-column header for all validation tests
COMPLETE_ARCHIVE_HEADER = [
    "centralwavelng", "bandwidth", "pl_transdep", 
    "pl_transdeperr1","pl_transdeperr2","pl_transdep_authors",
    "pl_ratror","pl_ratrorerr1","pl_ratrorerr2","pl_ratror_authors",
    "pl_radj","pl_radjerr1","pl_radjerr2","pl_radj_authors",
    "pl_transmid","pl_transmiderr1","pl_transmiderr2",
    "st_rad","st_raderr1","st_raderr2","st_rad_authors"
]


def test_blank_required_centralwavelng(tmp_path):
    """Test: Import raises when required centralwavelng is blank."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        # Row with blank centralwavelng (other fields populated to reach error path)
        row = [
            "",  # centralwavelng → blank required field → raise immediately
            "0.00147","2.1065",
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'centralwavelng' must be provided"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_blank_required_pl_transdep(tmp_path):
    """Test: Import raises when required pl_transdep is blank."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        # Row with blank pl_transdep
        row = [
            "0.63096",  # centralwavelng
            "0.00147",   # bandwidth  
            "",          # pl_transdep → blank required field → raise immediately
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'pl_transdep' must be provided"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_whitespace_only_required_fields(tmp_path):
    """Test: Whitespace-only values in required fields raise."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "   ",  # centralwavelng → strip → blank → required → raise
            "0.00147","2.1065",
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'centralwavelng' must be provided"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_nan_required_centralwavelng(tmp_path):
    """Test: NaN in required centralwavelng raises."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "nan",  # centralwavelng → NaN not finite → raise after float conversion
            "0.00147","2.1065",
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'centralwavelng' must be finite"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_nan_required_pl_transdep(tmp_path):
    """Test: NaN in required pl_transdep raises."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "0.63096",  # centralwavelng valid
            "0.00147","nan",  # pl_transdep → NaN not finite → raise
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'pl_transdep' must be finite"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_inf_positive_required_centralwavelng(tmp_path):
    """Test: Positive infinity in required centralwavelng raises."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "inf",  # centralwavelng → inf not finite → raise after float conversion
            "0.00147","2.1065",
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'centralwavelng' must be finite"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_inf_negative_required_centralwavelng(tmp_path):
    """Test: Negative infinity in required centralwavelng raises."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "-inf",  # centralwavelng → -inf not finite → raise after float conversion
            "0.00147","2.1065",
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'centralwavelng' must be finite"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_inf_positive_required_pl_transdep(tmp_path):
    """Test: Positive infinity in required pl_transdep raises."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "0.63096",  # centralwavelng valid
            "0.00147","inf",  # pl_transdep → inf not finite → raise
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'pl_transdep' must be finite"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_inf_negative_required_pl_transdep(tmp_path):
    """Test: Negative infinity in required pl_transdep raises."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "0.63096",  # centralwavelng valid
            "0.00147","-inf",  # pl_transdep → -inf not finite → raise
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'pl_transdep' must be finite"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_malformed_required_centralwavelng(tmp_path):
    """Test: Malformed centralwavelng (non-numeric) raises."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "badvalue",  # centralwavelng → malformed numeric field → raise
            "0.00147","2.1065",
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'centralwavelng' must be numeric"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_malformed_required_pl_transdep(tmp_path):
    """Test: Malformed pl_transdep (non-numeric) raises."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "0.63096",  # centralwavelng valid
            "0.00147","badvalue",  # pl_transdep → malformed numeric field → raise
            "0.01396","-0.01396","Feinstein et al. 2022",
            "0.14514","0.00048","-0.00048","Calculated",
            "1.2641","0.0328","-0.0328","Calculated",
            "", "", "",
            "0.895","0.023","-0.023","Faedi et al. 2011"
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'pl_transdep' must be numeric"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


# Optional signed-numeric fields also validate finite values
def test_nan_in_signed_optional_field(tmp_path):
    """Test: NaN in optional signed-numeric field raises."""
    
    path = tmp_path / "bad.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "0.63096","0.00147","2.1065",  # first three fields valid
            "nan", "-0.01396","Feinstein et al. 2022",  # pl_transdeperr1 = nan → raise
            ...  # complete remaining fields with valid values
        ]
        writer.writerow(row)
    
    with pytest.raises(SpectrumImportError, match="'pl_transdeperr1' must be finite"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


# Valid optional blank for optional numeric field remains None
def test_blank_optional_numeric_field(tmp_path):
    """Test: Blank optional numeric field (e.g., bandwidth) returns None."""
    
    path = tmp_path / "valid.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        
        row = [
            "0.63096","",  # bandwidth blank → None (optional numeric)
            "2.1065",
            ...  # complete remaining fields with valid values
        ]
        writer.writerow(row)
    
    result = import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)
    assert result.rows[0]["bandwidth"] is None
```

---

### 6. Schema Validation Tests (Consistent Exception Type)

```python
def test_unsupported_archive_schema_raises(tmp_path):
    """Test: Any unsupported supplied schema raises SpectrumImportError."""
    
    path = tmp_path / "bad.csv"
    path.write_text("wavelength,signal\n400,12.5\n", encoding="utf-8")
    
    # Wrong source column name → must raise immediately
    with pytest.raises(SpectrumImportError, match="Unsupported archive schema"):
        import_spectrum_csv(
            path,
            archive_schema={
                "wavelength": "wrong_col",  # Not "centralwavelng"
                "signal": "pl_transdep",
            }
        )
    
    # Only one key provided → must raise
    with pytest.raises(SpectrumImportError, match="Unsupported archive schema"):
        import_spectrum_csv(
            path,
            archive_schema={
                "wavelength": "centralwavelng",  # Missing "signal"
            }
        )
    
    # Extra key provided → must raise
    with pytest.raises(SpectrumImportError, match="Unsupported archive schema"):
        import_spectrum_csv(
            path,
            archive_schema={
                "wavelength": "centralwavelng",
                "signal": "pl_transdep",
                "extra_col": "dummy",  # Extra key not allowed
            }
        )


def test_valid_wasp39b_schema_permitted(tmp_path):
    """Test: Exact WASP-39 b schema is accepted."""
    
    path = tmp_path / "valid.csv"
    with path.open("w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_ARCHIVE_HEADER)
        # Write a minimal valid row (all optional fields blank except required)
        row = [
            "0.63096",  # centralwavelng
            "",          # bandwidth blank → None
            "2.1065",   # pl_transdep
            ...  # complete remaining fields
        ]
        writer.writerow(row)
    
    WASP_39_B_SCHEMA = {
        "wavelength": "centralwavelng",
        "signal": "pl_transdep"
    }
    
    result = import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)
    assert result is not None
    # Rows contain canonical aliases added correctly
    assert len(result.columns) == 23


def test_generic_mode_when_schema_none(tmp_path):
    """Test: archive_schema=None invokes existing generic importer logic."""
    
    path = tmp_path / "generic.csv"
    with path.open("w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["some_other_header1", "some_other_header2"])
        writer.writerow(["value1", "value2"])
    
    result = import_spectrum_csv(path, archive_schema=None)
    # Existing generic importer logic runs; no exception raised
```

---

## ✅ Confirmation: Plan v17 Final and Ready for ACT

- **All 8 defects resolved** without introducing new contradictions.
- **Required fields** (`centralwavelng`, `pl_transdep`) raise immediately on blank/whitespace/malformed/non-finite; never return `None` or emit warnings.
- **Finite validation** applied to all numeric types including signed-numeric; preserve signed error offsets exactly.
- **Row construction** adds canonical fields after parsing 21 sources, then validates final shape (23 keys); no incidental rejection of valid rows.
- **Archive header normalization** isolated from generic `COLUMN_ALIASES`; preserves input order; rejects duplicates and canonical-name collisions.
- **Column construction** uses explicit tuple conversion; avoids list+tuple concatenation errors.
- **All validation tests** use complete 21-column headers and correctly sized rows; independently test blank, malformed, `nan`, `inf`, `-inf` for both required fields; also test non-finite values in optional signed-numeric fields.
- **Exception type standardized** to `SpectrumImportError` throughout.
- **Established requirements preserved**: unsupported schemas raise; `archive_schema=None` retains generic behavior; 21 fields classified; metadata stripped; signed offsets finite; duplicates/collisions rejected; no unrelated changes.

**Plan v17 is complete and ready for ACT mode execution.**

<br>
<br>
<br>
<br>
<br>


# **CHATGPT REVIEW** #

Plan v17 is not quite ready for ACT. The core approach is sound, but there are three concrete issues worth correcting before implementation. This should be the final review pass; no need to restart the planning cycle.

1\. Unsupported schemas still fall through to generic mode in the shown control flow. `_validate_archive_schema()` raises for unsupported non-`None` schemas, so the actual behavior is correct, but the comment says unsupported schemas trigger generic mode. Correct that comment to avoid misleading Cline during implementation.

2\. Archive row parsing uses normalized headers as dictionary keys, but `csv.DictReader` retains original header names. `raw_row.get(field_name)` can return `None` when a source header contains casing or surrounding whitespace. Normalize the header-to-value mapping before parsing, or explicitly require exact headers. Either way, keep archive normalization isolated from generic aliases.

3\. The tests are still incomplete as written. Several fixtures contain `...` placeholders, which are not valid complete test data. The plan also does not show the full independent `inf`/`-inf` coverage for every optional signed-numeric field. Cline should implement complete, executable fixtures and test representative non-finite optional signed fields without duplicating an excessive number of near-identical tests.

Use this as the next PLAN correction, then move to ACT if those points are addressed:

## ECAS Chunk 4 — Final Plan Corrections

Mode: PLAN only. Do not edit files or run tests.

Make only these corrections to Plan v17:

1. Correct the misleading comment stating unsupported schemas trigger generic mode. Only `archive_schema=None` selects generic mode; any unsupported supplied schema raises `SpectrumImportError`.
2. Ensure archive row values are retrieved consistently with normalized headers. Since `csv.DictReader` keys use original header text, either build a normalized row mapping from the original headers or explicitly validate exact headers before parsing. Preserve the established normalization rules and reject duplicate normalized headers and canonical-name collisions.
3. Replace every `...` placeholder in proposed tests with complete, correctly sized rows containing all 21 source fields. Ensure tests are executable rather than illustrative pseudocode.
4. Verify test coverage independently rejects blank, whitespace-only, malformed, `nan`, `inf`, and `-inf` for both required fields. Include non-finite optional signed-numeric values and optional blank numeric values. Use parametrization where appropriate to avoid redundant test code.

Do not redesign the importer, expand scope, or create another planning document unless repository conventions require it. Return only the corrected implementation approach and a brief confirmation that it is ready for ACT.

Once Cline returns the corrected plan, approve it and switch to ACT if these specific issues are resolved. Keep the ACT scope limited to the importer, focused tests, and any necessary documentation directly tied to this feature.