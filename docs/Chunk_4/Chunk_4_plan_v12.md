# **Chunk 4 Plan v12 — Targeted Corrections Only**

## Scope: Only Plan Revision (No File Modifications or Test Execution)

---

## 1. The Corrected Archive-Mode Algorithm (Implementation Order)

### Step A: Initialize and Validate Parameters
```python
def import_spectrum_csv(
    file_path: str | Path,
    archive_schema: dict[str, str] = None,
) -> SpectrumData:
    
    # Default: generic behavior if no schema provided
    use_archive_mode = (archive_schema is not None and archive_schema == WASP_39_B_SCHEMA)
    
    path = Path(file_path)
    WARP_39_B_SCHEMA = {"wavelength": "centralwavelng", "signal": "pl_transdep"}  # Immutable constant
    
    if use_archive_mode:
        # Reject unsupported schemas explicitly
        if not (archive_schema == WASP_39_B_SCHEMA):
            raise SpectrumImportError(
                f"Unsupported archive schema. Only WASP-39 b schema is supported."
            )
    
    # Generic or invalid schema defaults to empty dict-like state
    effective_schema = archive_schema if use_archive_mode else {}
```

### Step B: Open File and Read Headers
```python
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        
        # Validate file structure
        if not reader.fieldnames or any(h is None or not h.strip() for h in reader.fieldnames):
            raise SpectrumImportError("CSV contains empty column name.")
        
        original_headers = list(reader.fieldnames)  # Preserve exact order
```

### Step C: Normalize Source Headers Independently (NOT via archive_schema)
```python
    # CRITICAL FIX: Normalize using COLUMN_ALIASES or lowercase, NOT archive_schema
    if use_archive_mode:
        # Archive mode still uses generic normalization for source headers
        normalized_sources = tuple(
            COLUMN_ALIASES.get(h.strip().lower(), h.strip().lower())
            for h in original_headers
        )
    else:
        # Generic path unchanged
        normalized_sources = tuple(
            COLUMN_ALIASES.get(h.strip().lower(), h.strip().lower())
            for h in original_headers
        )
```

### Step D: Reject Duplicate Source Headers After Normalization
```python
    if len(normalized_sources) != len(set(normalized_sources)):
        raise SpectrumImportError(
            "CSV contains duplicate or conflicting column names after header normalization."
        )
```

### Step E: Validate Required Archive Source Fields
```python
    if use_archive_mode:
        # Check both required source columns exist (before any alias additions)
        if "centralwavelng" not in normalized_sources:
            raise SpectrumImportError("Missing required source column: centralwavelng")
        if "pl_transdep" not in normalized_sources:
            raise SpectrumImportError("Missing required source column: pl_transdep")
        
        # Reject if wavelength or signal appear as source headers (they're canonical aliases)
        for idx, norm_header in enumerate(normalized_sources):
            if norm_header in ("wavelength", "signal"):
                raise SpectrumImportError(
                    f"Source header '{norm_header}' conflicts with canonical alias."
                )
```

### Step F: Construct Final Column Tuple (21 sources + 2 canonical)
```python
    columns_tuple: tuple[str, ...] = normalized_sources
    
    if use_archive_mode:
        # Append canonical aliases at END after all 21 source columns
        columns_tuple = columns_tuple + ("wavelength", "signal")
    
    # Ensure deterministic 23 unique entries when archive mode is active
    assert len(columns_tuple) == 23 and len(set(columns_tuple)) == 23
```

### Step G: Build Rows with Source-First Normalization
```python
    rows: list[dict[str, CellValue]] = []
    missing_uncertainty_count = 0
    
    for line_number, raw_row in enumerate(reader, start=2):
        if None in raw_row:
            raise SpectrumImportError(
                f"Line {line_number}: more values than header columns."
            )
        
        # CRITICAL FIX: Construct normalized row from SOURCE columns first
        # Do NOT index using canonical alias names that don't exist in source CSV
        source_row = dict(zip(normalized_sources, raw_row))
        
        # Parse numeric fields (all 17 optional/required numeric + 2 required)
        parsed_row: dict[str, CellValue] = {}
        
        for field_name in normalized_sources:
            if field_name.startswith("pl_transdep") or field_name.startswith("pl_ratror"):
                # Signed error fields preserve negative values
                try:
                    if source_row[field_name].strip() == "":
                        parsed_row[field_name] = None  # Blank numeric → None
                    else:
                        value = float(source_row[field_name])
                        parsed_row[field_name] = value
                        if not math.isfinite(value):
                            raise SpectrumImportError(...)
                except (TypeError, ValueError):
                    raise SpectrumImportError(f"Line {line_number}: '{field_name}' must be numeric.")
            elif field_name.startswith("pl_transmid"):
                # Mid-transit allows blank → None or text values
                try:
                    if source_row[field_name].strip() == "":
                        parsed_row[field_name] = None
                    else:
                        parsed_row[field_name] = float(source_row[field_name])
                except (TypeError, ValueError):
                    parsed_row[field_name] = source_row[field_name].strip()  # Preserve text
            elif field_name.startswith("st_rad") or field_name == "bandwidth":
                try:
                    if source_row[field_name].strip() == "":
                        parsed_row[field_name] = None
                    else:
                        value = float(source_row[field_name])
                        parsed_row[field_name] = value
                        if not math.isfinite(value):
                            raise SpectrumImportError(...)
                except (TypeError, ValueError):
                    raise SpectrumImportError(f"Line {line_number}: '{field_name}' must be numeric.")
            elif field_name.endswith("_authors"):
                # Metadata fields stay as strings; blank → ""
                text = source_row[field_name] or ""
                parsed_row[field_name] = text.strip() if text else ""
            else:
                # Generic numeric/text handling for remaining fields
                try:
                    if source_row[field_name].strip() == "":
                        parsed_row[field_name] = None
                    else:
                        parsed_row[field_name] = float(source_row[field_name])
                except (TypeError, ValueError):
                    parsed_row[field_name] = source_row[field_name].strip()
        
        # Parse uncertainty (generic path only; archive has no uncertainty column)
        if "uncertainty" in normalized_sources:
            uncertainty_text = source_row.get("uncertainty") or ""
            if uncertainty_text.strip() == "":
                parsed_row["uncertainty"] = None
                missing_uncertainty_count += 1
            else:
                try:
                    value = float(uncertainty_text)
                    if not math.isfinite(value) or value < 0:
                        raise SpectrumImportError(...)
                    parsed_row["uncertainty"] = value
                except (TypeError, ValueError):
                    raise SpectrumImportError(...)
        else:
            parsed_row["uncertainty"] = None
        
        # Add canonical aliases from SOURCE VALUES (NOT from CSV column)
        if use_archive_mode:
            for canonical_name, source_col in [("wavelength", "centralwavelng"), 
                                                ("signal", "pl_transdep")]:
                try:
                    value = float(parsed_row[source_col])
                except (TypeError, ValueError):
                    raise SpectrumImportError(...)
                if not math.isfinite(value):
                    raise SpectrumImportError(...)
                parsed_row[canonical_name] = value
        
        rows.append(parsed_row)
```

### Step H: Build Warnings and Model Instance
```python
    warnings: tuple[str, ...] = ()
    if missing_uncertainty_count:
        warnings = (
            f"{missing_uncertainty_count} measurement row(s) have missing "
            "uncertainty values. Missing uncertainty is not zero uncertainty.",
        )
    
    return SpectrumData(
        source_file=path.resolve(),
        columns=tuple(columns_tuple),  # Deterministic order
        rows=tuple(rows),  # Each dict keys match exactly with columns
        warnings=warnings,
    )
```

---

## 2. The Exact 23-Column Expected Tuple (WASP-39 b Archive Mode)

```python
EXPECTED_COLUMNS_WASP_39_B = (
    "centralwavelng",          # 1
    "bandwidth",                # 2
    "pl_transdep",              # 3
    "pl_transdeperr1",         # 4
    "pl_transdeperr2",         # 5
    "pl_transdep_authors",     # 6
    "pl_ratror",               # 7
    "pl_ratrorerr1",           # 8
    "pl_ratrorerr2",           # 9
    "pl_ratror_authors",       # 10
    "pl_radj",                 # 11
    "pl_radjerr1",             # 12
    "pl_radjerr2",             # 13
    "pl_radj_authors",         # 14
    "pl_transmid",             # 15
    "pl_transmiderr1",         # 16
    "pl_transmiderr2",         # 17
    "st_rad",                  # 18
    "st_raderr1",              # 19
    "st_raderr2",              # 20
    "st_rad_authors",          # 21
    "wavelength",              # 22 (canonical alias)
    "signal",                  # 23 (canonical alias)
)

# Assert len(EXPECTED_COLUMNS_WASP_39_B) == 23 and len(set(EXPECTED_COLUMNS_WASP_39_B)) == 23
```

---

## 3. Exact Fixture Rows for WASP-39 b Test Function

### Header Row (21 source columns)
```python
HEADER_LIST = [
    "centralwavelng", "bandwidth", "pl_transdep", "pl_transdeperr1", 
    "pl_transdeperr2", "pl_transdep_authors", "pl_ratror", "pl_ratrorerr1",
    "pl_ratrorerr2", "pl_ratror_authors", "pl_radj", "pl_radjerr1",
    "pl_radjerr2", "pl_radj_authors", "pl_transmid", "pl_transmiderr1",
    "pl_transmiderr2", "st_rad", "st_raderr1", "st_raderr2", "st_rad_authors"
]
```

### First Data Row (All fields populated, uncertainty column excluded)
```python
ROW_1_LIST = [
    "0.63096",      # centralwavelng → wavelength canonical
    "0.00147",      # bandwidth
    "2.1065",       # pl_transdep → signal canonical
    "0.01396",      # pl_transdeperr1 (positive error)
    "-0.01396",     # pl_transdeperr2 (negative error, preserves sign!)
    "Feinstein et al. 2022",  # pl_transdep_authors
    "0.14514",      # pl_ratror
    "0.00048",      # pl_ratrorerr1
    "-0.00048",     # pl_ratrorerr2 (signed)
    "Calculated",   # pl_ratror_authors
    "1.2641",       # pl_radj
    "0.0328",       # pl_radjerr1
    "-0.0328",      # pl_radjerr2 (signed)
    "Calculated",   # pl_radj_authors
    "",             # pl_transmid (blank → None)
    "",             # pl_transmiderr1 (metadata stays "")
    "",             # pl_transmiderr2 (metadata stays "")
    "0.895",        # st_rad
    "0.023",        # st_raderr1
    "-0.023",       # st_raderr2 (signed)
    "Faedi et al. 2011"  # st_rad_authors
]
```

### Second Data Row (Populated pl_transmid, blank others)
```python
ROW_2_LIST = [
    "",             # centralwavelng → None
    "",             # bandwidth → None
    "3.4500",       # pl_transdep → signal canonical
    "0.0150",       # pl_transdeperr1
    "-0.0150",      # pl_transdeperr2 (signed)
    "Example 2023", # pl_transdep_authors
    "",             # pl_ratror → None
    "",             # pl_ratrorerr1 → None
    "",             # pl_ratrorerr2 → None
    "",             # pl_ratror_authors → ""
    "1.5000",       # pl_radj
    "0.0400",       # pl_radjerr1
    "-0.0400",      # pl_radjerr2 (signed)
    "Smith 2020",   # pl_radj_authors
    "3.5000",       # pl_transmid (numeric)
    "",             # pl_transmiderr1 → ""
    "",             # pl_transmiderr2 → ""
    "0.9500",       # st_rad
    "0.030",        # st_raderr1
    "-0.030",       # st_raderr2 (signed)
    "Jones 2018"    # st_rad_authors
]
```

### Fixture Construction Using csv.writer
```python
def test_import_wasp_39_b_archive_schema(tmp_path):
    """Test importing WASP-39 b archive CSV with schema."""
    path = tmp_path / "WASP-39-b.csv"
    
    # Write header and rows using csv.writer (NOT string splitting)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER_LIST)
        writer.writerow(ROW_1_LIST)
        writer.writerow(ROW_2_LIST)
    
    result = import_spectrum_csv(path, archive_schema=WARP_39_B_SCHEMA)
```

### Exact Acceptance Criteria Assertions
```python
    # Column count and uniqueness
    assert len(result.columns) == 23
    assert len(set(result.columns)) == 23
    
    # Exact column order match
    assert result.columns == EXPECTED_COLUMNS_WASP_39_B
    
    # Row keys must exactly match columns tuple (same length, same values)
    for row in result.rows:
        assert set(row.keys()) == set(result.columns)
    
    # First row assertions:
    assert result.rows[0]["centralwavelng"] == 0.63096
    assert result.rows[0]["pl_transdep"] == 2.1065
    assert result.rows[0]["wavelength"] == 0.63096  # Canonical from source
    assert result.rows[0]["signal"] == 2.1065        # Canonical from source
    
    # Error offsets preserve sign:
    assert result.rows[0]["pl_transdeperr1"] == 0.01396
    assert result.rows[0]["pl_transdeperr2"] == -0.01396
    assert result.rows[0]["st_raderr2"] == -0.023
    
    # Metadata strings:
    assert result.rows[0]["pl_transdep_authors"] == "Feinstein et al. 2022"
    assert result.rows[0]["pl_ratror_authors"] == "Calculated"
    assert result.rows[0]["pl_radj_authors"] == "Calculated"
    
    # Blank numeric fields become None:
    assert result.rows[0]["pl_transmid"] is None
    
    # Metadata blanks remain empty strings:
    assert result.rows[0]["pl_transmiderr1"] == ""
    assert result.rows[0]["pl_transmiderr2"] == ""
    
    # Second row assertions:
    assert result.rows[1]["pl_transdep"] == 3.4500
    assert result.rows[1]["signal"] == 3.4500
    assert result.rows[1]["pl_transmid"] == 3.5000  # Populated value
    
    # Error handling assertions:
    # Test missing centralwavelng raises error (needs separate fixture)
    with pytest.raises(SpectrumImportError, match="centralwavelng"):
        import_spectrum_csv(path.with_suffix("_no-central.csv"), 
                           archive_schema=WARP_39_B_SCHEMA)  # Would test missing source
```

---

## 4. How Generic Behavior Remains Unchanged

### Default Path (`archive_schema=None`)
- Uses `COLUMN_ALIASES` dictionary for all header normalization:
  ```python
  COLUMN_ALIASES = {
      "wavelength": "wavelength",
      "lambda": "wavelength",
      "signal": "signal",
      "intensity": "signal",
      "uncertainty": "uncertainty",
      "error": "uncertainty",
  }
  ```

- Generic CSVs can have any number of additional columns preserved.
- Uncertainty validation applies to all generic imports.
- Warning messages for missing uncertainty values remain unchanged.
- No canonical aliases (`wavelength`, `signal`) are added unless they already exist in source headers.
- No archive-specific field names (`pl_transdep`, etc.) affect behavior.

### Archive Schema Path Only Activates When Exact Schema Matched
```python
def import_spectrum_csv(..., archive_schema=None):
    use_archive_mode = (archive_schema is not None 
                       and archive_schema == {"wavelength": "centralwavelng", 
                                               "signal": "pl_transdep"})
```

- Generic behavior unchanged when `archive_schema` is omitted or invalid.
- Archive-specific logic isolated to conditional block when mode enabled.

---

## 5. Remaining Blockers / Uncertainties

1. **No Automatic Archive Detection** — Users must explicitly pass schema parameter; no heuristic detection implemented (by design).

2. **Downstream Iteration Order** — The fixed column order affects any code iterating `result.rows[i][col]` or dictionary iteration order. Must be documented in API docs.

3. **Mixed-Type Column Parsing** — `pl_transmiderr1` and `pl_transmiderr2` may contain text error estimates instead of floats; importer preserves these as-is strings.

---

## 6. Confirmation: No Files Modified, No Tests Run

- ✅ No files modified in ACT mode.
- ✅ No tests executed or modified in this plan session.
- ✅ Implementation deferred pending user approval.

**Plan v12 is complete and ready for review.**


# CHATGPT REVIEW for v12 #

Plan v12 is not approved for ACT yet. It corrects several earlier problems, including the missing `st_rad_authors` column, source-first row construction, and fixture writing. However, important contradictions remain. We should make one final, narrowly scoped correction rather than restart planning.

## Remaining blockers

| Priority | Issue                                                                                                                                                                                                                                               | Required correction                                                                                                                                                                                                      |
| -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Critical | Archive schema validation is ineffective. `use_archive_mode` is set only when the schema already matches exactly, so the subsequent unsupported-schema check can never reject an unsupported schema.                                                | Distinguish `None` (generic mode) from a supplied schema. Reject any supplied schema other than the supported WASP-39 b schema.                                                                                          |
| Critical | The archive schema constant is defined after it is referenced. Step A compares against `WASP_39_B_SCHEMA` before the local assignment, which would raise an error. It also alternates between `WARP_39_B_SCHEMA` and `WASP_39_B_SCHEMA`.            | Define one module-level constant before the function and use its exact name consistently.                                                                                                                                |
| Critical | `pl_transmiderr1` and `pl_transmiderr2` are handled inconsistently. The plan says numeric fields must parse as finite floats, but treats these fields as optional text and explicitly expects blank values to be `""`.                              | Define an explicit field-classification table based on the actual 21-column schema. Both transit-midpoint error fields must be numeric; blanks become `None`, and malformed nonblank values raise `SpectrumImportError`. |
| Critical | Required canonical fields are not validated correctly. The second fixture row has blank `centralwavelng`, yet the requirements say this field must be present and finite numeric. The current alias conversion can fail indirectly on `None`.       | Reject blank or malformed `centralwavelng` and `pl_transdep` values with clear `SpectrumImportError` messages. Update the fixture so both required fields are valid in every accepted row.                               |
| High     | Generic behavior may change. The proposed function parses every non-uncertainty column using new fallback rules and assigns `None` to `uncertainty` when the column is absent. The plan does not establish that this matches the existing importer. | Preserve the current generic implementation and isolate archive parsing behind a separate code path. Do not refactor generic parsing as part of this change.                                                             |
| High     | The missing-column test is invalid. `path.with_suffix("_no-central.csv")` does not supply a valid suffix beginning with a dot and does not create the required fixture.                                                                             | Create a separate CSV fixture with `centralwavelng` removed, then assert the expected exception. Add equivalent coverage for missing `pl_transdep`.                                                                      |
| High     | Header normalization can create unintended collisions. The plan uses `COLUMN_ALIASES` on archive source headers before checking for canonical-name collisions.                                                                                      | Preserve the required source-header order, reject duplicate normalized source headers, and explicitly reject source headers that normalize to `wavelength` or `signal`. Do not modify global aliases.                    |

### What is already correct

- The expected 23-column tuple contains all 21 source fields in their intended order, followed by `wavelength` and `signal`.
- `pl_ratror` and `pl_radj` are not mapped to canonical fields.
- Signed error offsets must retain their signs.
- Author fields remain strings, with blank author values represented as `""`.
- Archive-specific behavior must not mutate global `COLUMN_ALIASES`.
- The fixture uses `csv.writer`, which is appropriate for writing the test CSV.

## Send Cline this targeted PLAN correction

## Chunk 4 — Plan v13 Targeted Correction

**Mode: PLAN only. Do not edit files or run tests.**

Revise Plan v12 only to resolve the remaining concrete defects below. Do not restart the analysis or expand scope.

### Scope

- `ecas/ingestion/csv_importer.py`
- `tests/test_csv_importer.py`

### Required corrections

1. **Schema validation**
   - Define one module-level immutable schema constant named `WASP_39_B_SCHEMA`.
   - Use it consistently in implementation and tests.
   - `archive_schema=None` must retain the existing generic importer path.
   - If a schema is supplied, reject it with `SpectrumImportError` unless it matches the supported schema exactly.
   - Do not silently treat unsupported schemas as generic imports.
2. **Preserve generic behavior**
   - Keep the existing generic CSV parsing and uncertainty handling unchanged.
   - Add a clearly separated archive-specific parsing path.
   - Do not modify global `COLUMN_ALIASES`.
   - Do not introduce archive-specific coercion into the generic path.
3. **Archive schema and header validation**
   - Preserve all 21 source columns in source order, then append `wavelength` and `signal`.
   - Normalize source headers independently of the schema's canonical-to-source mapping.
   - Reject duplicate normalized source headers.
   - Reject archive source headers that normalize to `wavelength` or `signal`.
   - Require both `centralwavelng` and `pl_transdep` source columns.
   - Ensure the final columns tuple has exactly 23 unique entries for the specified 21-column schema.
4. **Explicit field classification**
   - Use an explicit archive-field classification rather than broad prefix fallbacks that silently allow malformed values.
   - Numeric source fields must parse to finite floats when populated.
   - Blank optional numeric fields become `None`.
   - Malformed nonblank numeric fields raise `SpectrumImportError`.
   - `centralwavelng` and `pl_transdep` are required numeric values in every accepted data row; blank, malformed, NaN, or infinite values must raise `SpectrumImportError`.
   - All signed error offsets retain their original numeric signs.
   - Fields ending in `_authors` remain strings; blank author fields become `""`.
   - Do not classify `pl_transmiderr1` or `pl_transmiderr2` as metadata. They are numeric error fields: blank becomes `None`, populated values must be finite floats, and malformed values raise `SpectrumImportError`.
   - Do not infer units or reinterpret values.
5. **Correct the fixtures**
   - Use the exact 21 source headers and expected 23-column tuple from Plan v12.
   - Ensure every accepted data row contains valid numeric `centralwavelng` and `pl_transdep` values.
   - Keep blank optional numeric values in separate fields to test conversion to `None`.
   - Keep negative error values to verify sign preservation.
   - Keep blank author fields to verify `""` behavior.
   - Construct all fixtures with `csv.writer` and valid context-managed file handling.
6. **Required test coverage**
   - Exact 23-column order and uniqueness.
   - Row keys match the final columns exactly.
   - Canonical aliases equal their corresponding source values.
   - Numeric parsing, signed errors, blank optional numeric fields, and blank author fields.
   - Missing `centralwavelng` header and missing `pl_transdep` header.
   - Blank or malformed required values in data rows.
   - Malformed optional numeric values.
   - Duplicate normalized headers and canonical-name collisions.
   - Unsupported archive schemas.
   - Existing generic importer behavior remains unchanged, including its existing uncertainty and warning semantics.

### Response requirements

Return only the revised plan and a concise list of how each defect above was addressed. Do not modify files, run tests, or enter ACT mode. Do not revisit already settled design decisions or propose unrelated improvements.

After Cline returns Plan v13, review it against these requirements. If it resolves them without introducing new contradictions, proceed directly to a narrowly scoped ACT prompt.