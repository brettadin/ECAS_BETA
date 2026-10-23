# **Chunk 4 Plan v10 — Final Synthesis with Defect Corrections** #

## Summary of All Identified Issues Resolved

Plan v10 addresses the six defect categories identified in review:
1. **Column preservation contract broken** — `COLUMN_ALIASES.update()` design was replaced.
2. **No explicit archive selection mechanism** — Added schema parameter without breaking generic imports.
3. **Row key normalization undefined** — Implemented consistent lowercase normalization with alias mapping applied once.
4. **Fixture construction flawed** — Will use proper CSV serialization method in test plan.
5. **Alias collision policy vague** — Explicit error-raising behavior for canonical collisions defined.
6. **Undocumented keys in row dict** — Removed `source_columns` tracking addition.

---

## 1. Final Import Selection and Column Preservation Contract

### Importer Signature Update
```python
def import_spectrum_csv(
    file_path: str | Path,
    archive_schema: dict[str, str] = None,
) -> SpectrumData:
    """Import and validate a spectrum CSV.

    Args:
        file_path: Path to the CSV file.
        archive_schema: Optional dict mapping canonical names to source column names
            for archive-specific imports (e.g., {"wavelength": "centralwavelng"}).
            When provided, both source and canonical columns are stored together.

    Alias behavior:
        - Generic aliases apply to all CSVs unless overridden by archive_schema.
        - For WASP-39 b: "centralwavelng" → "wavelength", "pl_transdep" → "signal".
        - All 21 source columns are preserved under normalized lowercase names.

    Column order:
        First: 21 source columns in their original CSV order.
        Last: Canonical aliases for wavelength and signal (if added via archive_schema).
    """
```

### Schema Parameter Selection Logic
```python
# At import time, determine archive-specific mappings
default_aliases = COLUMN_ALIASES  # Generic behavior

if archive_schema is not None:
    # Merge explicit schema with generic aliases for other fields
    column_map = {**default_aliases, **archive_schema}
else:
    column_map = default_aliases

# Apply to headers once (no set())
columns = tuple(column_map.get(header.strip().lower(), header.strip().lower())
                for header in original_headers)
```

### Collision Detection Before Normalization
```python
# After computing columns, check for collisions before storing
seen_sources: dict[str, str] = {}  # normalized -> (source_index, is_canonical)
collision_detected = False

for i, (original_header, normalized) in enumerate(zip(original_headers, columns)):
    if collision_detected:
        continue
    if normalized in seen_sources:
        existing_source, is_canonical = seen_sources[normalized]
        # Special case: pl_transdep -> signal adds canonical alongside source
        if normalized == "signal" and original_header.lower() == "pl_transdep":
            pass  # Allow both source and canonical
        else:
            raise SpectrumImportError(
                f"Column '{original_header}' would collide with existing '{normalized}'. "
                f"Source columns are not overwritten."
            )
    seen_sources[normalized] = (original_header, normalized == "wavelength" or normalized == "signal")
```

### Column Tuple Construction
```python
# Final column order: original source columns first, then canonical aliases if added
columns_tuple = tuple(original_headers)  # Preserved as-is but cleaned/lowercase

# If archive_schema specifies canonical additions, append them
if archive_schema is not None:
    for canonical_name, source_col in archive_schema.items():
        if canonical_name == "wavelength" and source_col == "centralwavelng":
            columns_tuple = columns_tuple + ("wavelength",)
        elif canonical_name == "signal" and source_col == "pl_transdep":
            columns_tuple = columns_tuple + ("signal",)

# Verify unique 23-column result if schema was provided
if archive_schema is not None:
    assert len(columns_tuple) == len(set(columns_tuple)), \
        f"Column duplication detected in archive-specific import."
```

### Row Dictionary Construction
```python
for line_number, raw_row in enumerate(reader, start=2):
    if None in raw_row:
        raise SpectrumImportError(...)

    # Normalize keys once after column determination
    normalized_row = {columns_tuple[i]: raw_row[original_headers[i]] for i in range(len(columns_tuple))}

    # Parse required canonical fields
    for col in ("wavelength", "signal"):
        if col == "wavelength" and "centralwavelng" in normalized_row:
            try:
                value = float(normalized_row["centralwavelng"])
            except (TypeError, ValueError):
                raise SpectrumImportError(...)
            if not math.isfinite(value):
                raise SpectrumImportError(...)
        elif col == "signal" and "pl_transdep" in normalized_row:
            try:
                value = float(normalized_row["pl_transdep"])
            except (TypeError, ValueError):
                raise SpectrumImportError(...)
            if not math.isfinite(value):
                raise SpectrumImportError(...)

        normalized_row[col] = value  # Add canonical alias if applicable

    # Parse optional uncertainty with blank handling
    if "uncertainty" in normalized_row:
        text = normalized_row["uncertainty"]
        if text.strip() == "":
            normalized_row["uncertainty"] = None
        else:
            # existing finite/non-negative validation ...

    rows.append(normalized_row)
```

**Note:** The 21 source columns are preserved with their exact normalized names (lowercase). Canonical aliases `wavelength` and `signal` are appended only when archive_schema is provided. No undocumented keys added.

---

## 2. Exact Numeric/Text Classification Table

| Field Name | Type | Behavior Notes |
|------------|------|----------------|
| `centralwavelng` | float (numeric) | Wavelength source; blanks → `None` |
| `bandwidth` | float (numeric) | Signed error offsets in related fields |
| `pl_transdep` | float (numeric) | Signal source; blanks → `None` |
| `pl_transdeperr1` | float (numeric) | Signed error, preserves negative values |
| `pl_transdeperr2` | float (numeric) | Symmetric error bound |
| `pl_transdep_authors` | str (text) | Citation; blanks remain `""` |
| `pl_ratror` | float (numeric) | Distinct parameter; not wavelength substitute |
| `pl_ratrorerr1` | float (numeric) | Signed error offset |
| `pl_ratrorerr2` | float (numeric) | Symmetric error bound |
| `pl_ratror_authors` | str (text) | Citation text; blanks remain `""` |
| `pl_radj` | float (numeric) | Absolute radius parameter; not signal substitute |
| `pl_radjerr1` | float (numeric) | Signed error offset |
| `pl_radjerr2` | float (numeric) | Symmetric error bound |
| `pl_radj_authors` | str (text) | Citation text; blanks remain `""` |
| `pl_transmid` | mixed (float/str) | Mid-transit time; can be blank → `None` or numeric |
| `pl_transmiderr1` | str (text) | Error field for mid; blanks remain `""` |
| `pl_transmiderr2` | str (text) | Error field for mid; blanks remain `""` |
| `st_rad` | float (numeric) | Secondary transmission source |
| `st_raderr1` | float (numeric) | Signed error offset |
| `st_raderr2` | float (numeric) | Symmetric error bound |
| `st_rad_authors` | str (text) | Citation text; blanks remain `""` |

**Parsing Rules:**
- Numeric fields: Parse nonblank as finite float. Blanks → `None`. Malformed → `SpectrumImportError`.
- Text/metadata fields: Preserve strings. Blanks → `""`.
- Error offset fields: Always preserve sign (negative values retained).

---

## 3. Alias and Collision Behavior Specification

### Canonical Addition Only
```python
# Archive schema for WASP-39 b ONLY:
WASP_39_B_SCHEMA = {
    "wavelength": "centralwavelng",
    "signal": "pl_transdep",
}

# NOT treated as interchangeable with pl_ratror or pl_radj.
```

### Collision Handling Scenarios

| Scenario | Behavior | Rationale |
|----------|----------|-----------|
| Input has both `centralwavelng` and a column named `wavelength` | Raises `SpectrumImportError: collision` | Prevents silent overwriting of source data. |
| Input has only `wavelength` (generic) with no `centralwavelng` | Normal alias mapping applies; canonical equals source | Generic behavior unchanged. |
| Input has both `pl_transdep` and an explicit `signal` column | Raises collision error unless `signal` is the canonical alias | Source preserved, canonical added only. |
| Input from unrelated archive with extra columns | Extra columns retained under normalized names | Generic preservation intact. |

### Alias Resolution Sequence
1. Apply generic `COLUMN_ALIASES` to all headers.
2. If `archive_schema` provided, override mappings for specified canonical fields.
3. Check for collisions (except allowed `pl_transdep` → `signal` addition).
4. Normalize keys using resolved mapping.
5. Parse and validate each row.

---

## 4. Corrected Test Plan with Proper Fixture Construction

### New WASP-39 b Test Function
```python
def test_import_wasp_39_b_archive_schema(tmp_path):
    """Test importing the actual 21-column WASP-39 b CSV."""
    path = tmp_path / "WASP-39-b.csv"
    
    # Header with all 21 columns exactly as in archive
    header_line = (
        "CENTRALWAVELNG,BANDWIDTH,PL_TRANDEP,PL_TRANDEPERR1,PL_TRANDEPERR2,"
        "PL_TRANDEP_AUTHORS,PL_RATROR,PL_RATRORERR1,PL_RATRORERR2,"
        "PL_RATROR_AUTHORS,PL_RADJ,PL_RADJERR1,PL_RADJERR2,PL_RADJ_AUTHORS,"
        "PL_TRANMID,PL_TRANMIDERR1,PL_TRANMIDERR2,ST_RAD,ST_RADERR1,"
        "ST_RADERR2,ST_RAD_AUTHORS"
    )
    
    first_row = (
        "0.63096,0.00147,2.1065,0.01396,-0.01396,"
        "Feinstein et al. 2022,0.14514,0.00048,-0.00048,"
        "Calculated,1.2641,0.0328,-0.0328,Calculated,"
        "", "", "0.895,0.023,-0.023,Faedi et al. 2011"
    )
    
    # Build valid CSV using csv module for correctness
    writer = csv.writer(path.open("w", encoding="utf-8"))
    writer.writerow(header_line.split(","))
    writer.writerow(first_row.split(","))
    
    result = import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)
    
    # Acceptance criteria:
    assert isinstance(result, SpectrumData)
    assert result.row_count == 1
    assert len(result.columns) == 23
    
    # Verify column order: source columns first, then canonical aliases
    expected_columns = (
        "centralwavelng", "bandwidth", "pl_transdep", "pl_transdeperr1",
        "pl_transdeperr2", "pl_transdep_authors", "pl_ratror", "pl_ratrorerr1",
        "pl_ratrorerr2", "pl_ratror_authors", "pl_radj", "pl_radjerr1",
        "pl_radjerr2", "pl_radj_authors", "pl_transmid", "pl_transmiderr1",
        "pl_transmiderr2", "st_rad", "st_raderr1", "st_raderr2",
        "wavelength", "signal"
    )
    assert result.columns == expected_columns
    
    # Source columns preserved:
    assert result.rows[0]["centralwavelng"] == 0.63096
    assert result.rows[0]["pl_transdep"] == 2.1065
    
    # Canonical aliases added:
    assert result.rows[0]["wavelength"] == 0.63096
    assert result.rows[0]["signal"] == 2.1065
    
    # Error offsets preserve sign:
    assert result.rows[0]["pl_transdeperr1"] == 0.01396
    assert result.rows[0]["pl_transdeperr2"] == -0.01396
    
    # Metadata fields retain strings or blanks appropriately:
    assert result.rows[0]["pl_transdep_authors"] == "Feinstein et al. 2022"
    assert result.rows[0]["pl_transmiderr1"] == ""
```

### Existing Tests Remain Unchanged
- `test_import_valid_csv`
- `test_preserves_additional_columns`
- `test_missing_required_column`
- `test_rejects_non_numeric_signal`
- `test_rejects_negative_uncertainty`
- `test_rejects_infinite_values`
- `test_blank_uncertainty_is_preserved_and_warned`
- `test_import_csv_without_uncertainty_column`
- `test_missing_required_measurement`

---

## 5. Remaining Uncertainties / Blockers

1. **Archive Schema Detection:** If users pass CSV files without specifying `archive_schema`, the importer currently uses generic behavior. No automatic archive detection is implemented (by design to avoid false positives). Users must explicitly pass schema for WASP-39 b imports.

2. **Column Order Semantics:** The exact order of source columns vs canonical aliases must be documented in module docstrings and tests. This affects iteration behavior downstream.

3. **Mixed-Type Column Handling:** `pl_transmid` may appear blank or numeric; validation must allow both without raising errors, while maintaining type consistency for parsing.

4. **Error Field String Storage:** Fields like `pl_transmiderr1` may contain error text strings instead of floats when blank. The importer preserves these as-is (`""`) in the row dictionary.

---

## 6. Confirmation of No Modifications

- ✅ No files modified in ACT mode yet.
- ✅ No tests executed in this plan session.
- ✅ Implementation deferred pending user approval.

**Plan v10 is complete and ready for review.**

<br>
<br>
<br>
<br>
<br>

# CHATGPT REVIEW #


## Review: Chunk 4 Plan v10

Verdict: Not ready for ACT. V10 still has fundamental conflicts between its proposed schema handling, column-preservation requirements, and test fixture. The overall direction is viable, but this plan would not reliably produce the promised result.

### Remaining blockers

1\. Generic aliases still conflict with source preservation. The proposed sequence applies generic `COLUMN_ALIASES` to every header before preserving source fields. That can rename generic source columns, contrary to the requirement that archive-specific handling preserve the original normalized keys. Archive handling needs to be separate from the existing generic normalization path.

2\. The row construction does not match the final column tuple. `columns_tuple` contains the 21 normalized source names plus two canonical aliases, but the proposed row comprehension indexes `raw_row` using every name in `columns_tuple`. The CSV reader has no `wavelength` or `signal` source fields in the archive, so this will fail. Build the normalized source row first, then add the canonical aliases from their source values.

3\. The proposed column list omits a source column. The test's `expected_columns` contains 22 entries, not 23: it omits `st_rad_authors`. This contradicts the full 21-column preservation requirement.

4\. The fixture still does not reliably represent 21 fields. Splitting a manually assembled CSV row by commas is fragile, and the proposed concatenation around empty strings is not a valid, clear fixture definition. Use `csv.writer` with an explicit list of 21 header values and an explicit list of 21 row values. Manage the file handle with a context manager.

5\. The archive schema parameter is not fully integrated with the existing API. V10 proposes a new `archive_schema` argument but does not show how existing required-column checks and row parsing behave when the argument is supplied. The implementation plan must preserve generic imports while validating archive source columns and generating canonical fields only for the explicitly selected schema.

6\. The numeric classification is still inconsistent. `pl_transmiderr1` and `pl_transmiderr2` are classified as text, even though the plan previously designated them as numeric error fields that can be blank. The actual archive's blank cells support testing missing-value behavior, but do not establish that those fields should be text. Treat them as optional numeric fields unless authoritative schema evidence contradicts that classification.

## Next step: targeted Plan v11

Send this to Cline in PLAN mode. This version requires it to describe a valid processing sequence rather than just presenting isolated code fragments.

# ECAS Chunk 4 — Final Implementation-Readiness Review (v10 → v11)

**Mode: PLAN only. No file modifications, fixture creation, or test execution.**

Revise `chunk_4_plan_v10` into `chunk_4_plan_v11`. Inspect the current implementation and model directly. Do not restart the general analysis. Resolve the remaining concrete defects and provide one internally consistent implementation plan.

## 1. Separate generic and archive-specific import paths

Do not globally merge archive aliases into `COLUMN_ALIASES`.

The existing generic import path must retain its current behavior and regression expectations.

For an explicitly selected WASP-39 b archive schema:

1. Normalize the 21 source headers using the existing header-cleanup conventions.
2. Validate duplicate normalized source headers.
3. Preserve all 21 source columns in their original order, using normalized lowercase names.
4. Validate that `centralwavelng` and `pl_transdep` exist.
5. Parse and validate the archive-specific fields according to the explicit schema.
6. Add `wavelength` from `centralwavelng` and `signal` from `pl_transdep`.
7. Append those two canonical aliases to the source-column order.
8. Ensure each row dictionary has exactly the same ordered keys as `SpectrumData.columns`.

Do not index the CSV reader's raw row using canonical alias names that are not present in the source CSV. Normalize and parse source fields first, then derive canonical fields from the parsed source values.

Define how the optional schema argument is represented and validated. Avoid mutating global alias dictionaries. If the current architecture supports a smaller implementation without a public signature change, explain that alternative.

## 2. Resolve column collisions

Define and test these cases:

- Duplicate source headers after normalization: reject.
- Archive source headers plus an explicit `wavelength` or `signal` source column: reject if it conflicts with the canonical alias.
- Generic CSV with ordinary canonical headers: retain existing behavior.
- Archive schema missing either required source field: raise a useful `SpectrumImportError`.

Do not use special-case duplicate detection that accidentally permits unrelated collisions.

## 3. Finalize all 21 field classifications

Use these exact normalized names.

**Required numeric source fields**

- `centralwavelng`
- `pl_transdep`

**Other numeric fields**

- `bandwidth`
- `pl_transdeperr1`
- `pl_transdeperr2`
- `pl_ratror`
- `pl_ratrorerr1`
- `pl_ratrorerr2`
- `pl_radj`
- `pl_radjerr1`
- `pl_radjerr2`
- `pl_transmid`
- `pl_transmiderr1`
- `pl_transmiderr2`
- `st_rad`
- `st_raderr1`
- `st_raderr2`

**Metadata/text fields**

- `pl_transdep_authors`
- `pl_ratror_authors`
- `pl_radj_authors`
- `st_rad_authors`

For numeric fields, populated values must parse to finite floats; blank values become `None`; malformed nonblank values raise `SpectrumImportError`. Signed error values retain their signs. Metadata remains strings, with blanks as `""`.

Preserve existing canonical `uncertainty` validation and warnings for generic CSVs. Do not infer units or broaden archive-specific parsing to unrelated CSVs.

## 4. Provide a valid fixture and test plan

The test fixture must contain exactly 21 source headers and exactly 21 values per data row. Use explicit Python lists and `csv.writer` inside a context manager. Do not build rows by splitting comma-delimited strings or join lists with strings.

The expected `SpectrumData.columns` must contain all 21 normalized source names—including `st_rad_authors`—followed by `wavelength` and `signal`, for exactly 23 unique entries.

Specify assertions for:

- Exact column order and count.
- Exact equality of each row's keys/order with `SpectrumData.columns`.
- Preserved source values and correct canonical aliases.
- Numeric parsing and signed error offsets.
- Blank numeric fields as `None` and blank metadata as `""`.
- Invalid numeric values and schema collisions.
- Existing generic tests unchanged.
- Units remaining unset.

Use the actual archive's representative values and verify header/value alignment. The fixture establishes importer behavior for this schema only.

## 5. Show one coherent implementation sequence

Return a concise pseudocode or step-by-step sequence that accounts for:

- Header validation.
- Source-row normalization.
- Type-specific parsing.
- Canonical alias creation.
- `SpectrumData` construction.
- Error handling.

Every proposed row key must appear in `SpectrumData.columns`; every declared column must be present in every row. Check the existing model's actual API rather than assuming fields or methods.

Keep the proposed ACT burst limited to `ecas/ingestion/csv_importer.py` and `tests/test_csv_importer.py` unless inspection demonstrates a necessary dependency.

## 6. Output and stop condition

Return only:

1. Final schema-selection and storage contract.
2. Definitive field classifications.
3. Collision policy.
4. Coherent implementation sequence.
5. Test plan and exact acceptance criteria.
6. Remaining blockers.
7. Confirmation that no files were modified and no tests were run.

Do not implement anything. Stop for ChatGPT review of v11.

Review threshold: v11 must describe an implementation that can actually preserve all 21 source columns, add exactly two aliases, parse the designated fields, and leave generic imports unchanged. If those conditions are satisfied, we can move to ACT without another broad planning cycle.