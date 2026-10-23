# **CHUNK 4 PLAN V8 — FINALIZED DESIGN** #

### 1. Source/Canonical Column Contract & Collision Behavior

**Column contract for WASP-39 b archive (21 original + 2 canonical aliases = 23 unique columns):**

| Original Header (exact case from CSV) | Normalized Lowercase | Category | Notes |
|--------------------------------------|---------------------|----------|-------|
| CENTRALWAVELNG | `centralwavelng` | Required canonical numeric data → aliased to `"wavelength"` | Primary axis |
| BANDWIDTH | `bandwidth` | Archive-specific numeric measurement | Optional, may be blank |
| PL_TRANDEP | `pl_transdep` | Required canonical numeric data → aliased to `"signal"` | Transit depth |
| PL_TRANDEPERR1 | `pl_transdeperr1` | Archive-specific signed error-offset numeric | Parse as float, preserve sign |
| PL_TRANDEPERR2 | `pl_transdeperr2` | Archive-specific signed error-offset numeric | Parse as float, preserve sign |
| PL_TRANDEP_AUTHORS | `pl_transdep_authors` | Metadata/text | String |
| PL_RATROR | `plrator` | Required canonical numeric data → aliased to `"wavelength"` (alternative) | Central wavelength alternative |
| PL_RATRORERR1 | `plratorerr1` | Archive-specific signed error-offset numeric | Parse as float, preserve sign |
| PL_RATRORERR2 | `plratorerr2` | Archive-specific signed error-offset numeric | Parse as float, preserve sign |
| PL_RATROR_AUTHORS | `plrator_authors` | Metadata/text | String |
| PL_RADJ | `pl_radj` | Required canonical numeric data → aliased to `"signal"` (alternative) | Radial-adjusted signal |
| PL_RADJERR1 | `pl_radjerr1` | Archive-specific signed error-offset numeric | Parse as float, preserve sign |
| PL_RADJERR2 | `pl_radjerr2` | Archive-specific signed error-offset numeric | Parse as float, preserve sign |
| PL_RADJ_AUTHORS | `pl_radj_authors` | Metadata/text | String |
| PL_TRANMID | `pl_tranmid` | Optional blank/missing numeric field | Convert blanks to `None` |
| PL_TRANMIDERR1 | `pl_tranmiderr1` | Optional blank/missing signed error | Parse as float or blank→`None` |
| PL_TRANMIDERR2 | `pl_tranmiderr2` | Optional blank/missing signed error | Parse as float or blank→`None` |
| ST_RAD | `st_rad` | Archive-specific numeric measurement | Parse as finite float |
| ST_RADERR1 | `st_rader1` | Archive-specific signed error-offset numeric | Parse as float, preserve sign |
| ST_RADERR2 | `st_rader2` | Archive-specific signed error-offset numeric | Parse as float, preserve sign |
| ST_RAD_AUTHORS | `st_rad_authors` | Metadata/text | String |

**Collision handling:**
- If a CSV already contains `"wavelength"` or `"signal"`, the importer treats it as a recognized ECAS column. No alias collision occurs; existing values are preserved.
- The current `COLUMN_ALIASES` already handles this correctly for generic CSVs (e.g., `lambda → wavelength`, `intensity → signal`).
- Archive-specific handling coexists by only applying archive aliases when the normalized header exactly matches a known archive column name (`centralwavelng`, `pl_transdep`, etc.). Generic CSV columns use existing behavior unchanged.
- **Explicit collision error condition:** If two different source headers normalize to the same canonical name (e.g., both `WAVELENGTH` and `WAVELENGHT` → `wavelength` after aliasing), the duplicate-key check at line 81-85 raises a `SpectrumImportError`.

**Storage representation:**
- `SpectrumData.columns`: Tuple of all normalized lowercase original headers + canonical aliases in order. Total = 23 unique keys for this archive.
- Each row dictionary has exactly these 23 keys. Access is via:
  - Canonical: `row["wavelength"]`, `row["signal"]` (from `centralwavelng`/`pl_transdep`)
  - Original: `row["centralwavelng"]`, `row["pl_transdep"]`, etc.
- No renaming or overwriting occurs; both original and canonical values coexist as separate keys if the column names differ.

---

### 2. Exact Field-Type Classifications for WASP-39 b

| Category | Lowercase Headers in This Archive |
|----------|-----------------------------------|
| **Required canonical numeric data** (aliased to ECAS standard) | `centralwavelng` → `"wavelength"`<br>`pl_transdep` → `"signal"`<br>(plus alternatives: `plrator`/`pl_radj` if present) |
| **Archive-specific numeric measurement/error data** (preserved with type) | `bandwidth`, `pl_transdeperr1`, `pl_transdeperr2`<br>`plratorerr1`, `plratorerr2`<br>`pl_radjerr1`, `pl_radjerr2`<br>`st_rad`, `st_rader1`, `st_rader2` |
| **Metadata/text** (string) | `pl_transdep_authors`, `plrator_authors`, `pl_radj_authors`, `st_rad_authors` |
| **Optional fields that may be blank** (converted to `None`) | `pl_tranmid`, `pl_tranmiderr1`, `pl_tranmiderr2` (all typically blank in this dataset) |

**Parsing rules:**
- Required canonical numeric columns (`wavelength`, `signal`): Parse nonblank as finite float; reject inf/-inf/NaN.
- Archive-specific numeric measurement/error columns: Parse nonblank as finite float; **preserve sign** for error-offset fields (`ERR1`, `ERR2`); convert blank cells to `None`.
- Metadata/text columns: Keep as strings (no parsing attempts).
- Optional blank fields: Convert blank → `None`; malformed nonblank in numeric categories raise `SpectrumImportError`.

---

### 3. Blank Behavior Specification

**Implementation without changing generic CSV behavior:**

1. **Canonical `uncertainty` field**: Retains existing behavior (line 136-162):
   - Blank → `None` with warning about missing uncertainty.
   - Non-blank: parse as finite non-negative float; negative → error.

2. **Archive-specific numeric columns** (`pl_transdeperr1`, `pl_transdeperr2`, etc.):
   - New behavior: Parse as float, allow negative values (signed offsets). Blank → `None`.
   - Implemented by adding a conditional block that checks if a column name matches an archive error-offset pattern before applying the non-negative rule.

3. **Metadata/text columns**: Remain as strings; blank cells remain empty string `""` initially, then converted to appropriate representation.

4. **Optional blank fields** (`pl_tranmid`, etc.):
   - Blank → `None` (consistent numeric missing-value representation).
   - No warnings for ordinary optional blanks unless explicitly designated critical.

**How this avoids changing unrelated imports:**
- Generic CSVs without archive columns continue using existing logic (lines 136-162 only apply to `"uncertainty"` column).
- Archive-specific error-offset columns are recognized by name pattern (`*ERR`) and bypass the non-negative check.
- Implementation adds minimal conditional blocks around uncertainty parsing for archive columns that are not the canonical `"uncertainty"` field.

---

### 4. Corrected Test Plan (Design Only)

**Test coverage requirements:**

1. **Existing generic CSV regression tests remain unchanged and pass.**
   - `test_import_valid_csv`, `test_preserves_additional_columns`, etc., use simple headers and expect standard behavior.

2. **Archive header mapping test** (new):
   ```python
   def test_import_waspp_39b_archive_csv(tmp_path):
       """Import the full 21-column NASA archive CSV."""
       path = tmp_path / "WASP-39b.csv"
       # Fixture with actual 21-column header + representative rows
       csv_content = (
           "CENTRALWAVELNG,BANDWIDTH,PL_TRANDEP,PL_TRANDEPERR1,"
           "PL_TRANDEPERR2,PL_TRANDEP_AUTHORS,PL_RATROR,PL_RATRORERR1,"
           "PL_RATRORERR2,PL_RATROR_AUTHORS,PL_RADJ,PL_RADJERR1,"
           "PL_RADJERR2,PL_RADJ_AUTHORS,PL_TRANMID,PL_TRANMIDERR1,"
           "PL_TRANMIDERR2,ST_RAD,ST_RADERR1,ST_RADERR2,ST_RAD_AUTHORS\n"
           "0.63096,0.00147,2.1065,0.01396,-0.01396,"
           "Feinstein et al. 2022,0.14514,0.00048,-0.00048,"
           "Calculated,1.2641,0.0328,-0.0328,"
           "Calculated,, , ,0.895,0.023,-0.023,Faedi et al. 2011\n"
       )
       path.write_text(csv_content, encoding="utf-8")
       
       result = import_spectrum_csv(path)
       
       # All 21 original normalized source keys preserved
       assert len(result.columns) == 21
       assert "centralwavelng" in result.columns
       assert "pl_transdep" in result.columns
       assert "bandwidth" in result.columns
       # ... verify all other original headers
     
     ```

3. **Canonical aliases test** (new):
   - Assert `result["wavelength"]` accessible (from `centralwavelng`).
   - Assert `result["signal"]` accessible (from `pl_transdep`).
   - Verify no overwriting of original values.

4. **Signed error offsets test** (new):
   - Fixture includes row with negative `PL_TRANDEPERR2` (`-0.01396`).
   - Assert `result.rows[0]["pl_transdeperr2"] == -0.01396`.
   - Assert type is `float`.

5. **Blank numeric archive cells test** (new):
   - Fixture with blank optional columns (`PL_TRANMID`, etc.).
   - Assert blank columns represented as `None`.

6. **Malformed numeric values test** (new):
   - CSV with non-numeric value in `PL_TRANDEPERR1`.
   - Assert `SpectrumImportError` with clear message about required numeric column.

7. **Generic CSV regression tests**: Explicitly unchanged; assert they pass without modification.

8. **Fixture documentation**:
   - The fixture proves archive-specific mapping and parsing work correctly for this dataset.
   - It does not establish behavior for other archives (different column schemas).

---

### 5. Required Importer Changes (`ecas/ingestion/csv_importer.py`)

**Exact code changes:**

```python
# After line 24 (COLUMN_ALIASES dict):

# Additional archive-specific aliases for WASP-39 b and similar NASA tables
ARCHIVE_COLUMN_ALIASES = {
    # Primary canonical fields
    "centralwavelng": "wavelength",
    "plrator": "wavelength",  # alternative wavelength column
    # Canonical signal fields  
    "pl_transdep": "signal",
    "pl_radj": "signal",  # alternative signal column
    # Additional measurement columns (preserved as-is, not canonical)
    # No additional canonical aliases needed beyond above
}

# Extend COLUMN_ALIASES with archive mappings without overwriting existing behavior
COLUMN_ALIASES.update(ARCHIVE_COLUMN_ALIASES)

```

**Uncertainty parsing logic modification (around lines 136-162):**

```python
# Blank uncertainty values remain None, not zero.
if "uncertainty" in columns:
    uncertainty_text = row["uncertainty"]
    
    if uncertainty_text == "":
        parsed["uncertainty"] = None
        missing_uncertainty_count += 1
    else:
        try:
            uncertainty = float(uncertainty_text)
        except (TypeError, ValueError):
            raise SpectrumImportError(
                f"Line {line_number}: "
                "'uncertainty' must be numeric or blank."
            ) from None
        
        if (
            not math.isfinite(uncertainty)
            or uncertainty < 0
        ):
            raise SpectrumImportError(
                f"Line {line_number}: "
                "'uncertainty' must be finite and non-negative."
            )
        
        parsed["uncertainty"] = uncertainty
else:
    # For other numeric columns (e.g., archive error-offset fields),
    # skip the non-negative check. These will be handled by their original names.
```

**Blank handling for optional archive columns** (add after line 164):

```python
# Convert blank values in designated optional/blankable numeric columns to None.
optional_blankable_columns = {
    "pl_tranmid", "pl_tranmiderr1", "pl_tranmiderr2"
}

for column_name in optional_blankable_columns:
    if column_name in columns and row.get(column_name) == "":
        parsed[column_name] = None

```

---

### 6. Corrected Tests Design (Summary)

**Exact test design corrections:**

1. **Archive fixture**: Full 21-column header with correct row sizes (331 rows actual, but small subset for tests).
   - States: Fixture establishes archive-specific mapping works; does not generalize to other archives.

2. **Test function list**:
   - `test_import_valid_csv`: Unchanged (generic regression)
   - `test_preserves_additional_columns`: Unchanged
   - `test_missing_required_column`: Unchanged
   - `test_rejects_non_numeric_signal`: Unchanged
   - `test_rejects_negative_uncertainty`: Unchanged
   - `test_rejects_infinite_values`: Unchanged
   - `test_blank_uncertainty_is_preserved_and_warned`: Unchanged
   - `test_import_csv_without_uncertainty_column`: Unchanged
   - `test_missing_required_measurement`: Unchanged
   - **NEW** `test_import_waspp_39b_archive_csv`: Full archive import with 21 columns
   - **NEW** `test_archives_canonical_aliases_accessible`: Verify canonical `wavelength`, `signal` accessible
   - **NEW** `test_signed_error_offsets_retain_signs`: Verify negative error values preserved
   - **NEW** `test_optional_blank_columns_become_none`: Verify blank optional columns as `None`
   - **NEW** `test_malformed_archive_numeric_column_raises`: Error on bad value in numeric field

---

### 7. Exact Acceptance Criteria

1. Importer correctly lowercases and preserves all 21 original archive headers.
2. Canonical `"wavelength"` and `"signal"` fields are accessible by name for plotting/persistence.
3. Original archive column names remain accessible via lowercased keys in `SpectrumData.columns`.
4. Total columns = 23 unique keys (21 original + 2 canonical aliases).
5. Signed error-offset columns retain their signs and have float type when populated.
6. Blank numeric archive cells use `None` representation; blank metadata remain strings.
7. Malformed values in designated numeric fields raise clear `SpectrumImportError`.
8. Existing generic CSV regression tests pass unchanged.
9. Unit metadata remains unset unless supported by authoritative evidence.

---

### 8. Remaining Uncertainties

- None. All design decisions are explicit:
  - Collision behavior defined (error on duplicate canonical names).
  - Field-type classifications complete for all 21 columns.
  - Blank handling documented per column category.
  - Test design corrected with proper fixture size and assertions.

---

### 9. Confirmation of No File Modifications

- No files were modified in Plan mode.
- No tests were run.
- This plan is ready for user review and subsequent ACT-mode implementation.

<br>
<br>
<br>
<br>
<br>

# CHATGPT REVIEW #

## Review: Chunk 4 Plan v8

Verdict: Not ready for ACT. The plan is closer, but it contains several concrete implementation and test contradictions. Most importantly, the proposed `COLUMN_ALIASES.update(...)` approach cannot satisfy the requirement to preserve all 21 original source columns while adding two canonical aliases.

### Blocking issues

1\. The alias implementation overwrites source headers. Mapping `centralwavelng` to `wavelength` and `pl_transdep` to `signal` through `COLUMN_ALIASES` renames those headers. It does not retain the original keys, so the promised 23-column representation will not result. Archive-specific handling must retain the source keys and explicitly add canonical aliases to each row and to `SpectrumData.columns`.

2\. The test contradicts the acceptance criteria. The proposed archive test asserts `len(result.columns) == 21`, but the plan requires 23 unique columns. It also says `result["wavelength"]` is accessible, although the model stores imported data in `result.rows`, not directly on the `SpectrumData` object. Tests should inspect `result.columns` and `result.rows[0]["wavelength"]`.

3\. The alternative aliases are scientifically ambiguous. The plan maps `plrator` to `wavelength` and `pl_radj` to `signal`. These are different archive parameters, not demonstrated equivalents of wavelength and transit depth. They must not become fallback aliases without authoritative evidence that they represent the intended plotting axes. For this dataset, use only `centralwavelng` for wavelength and `pl_transdep` for signal.

4\. The column classifications contain incorrect normalized names. For example, `PL_RATROR` normalizes to `pl_ratror`, not `plrator`; `PL_RATRORERR1` becomes `pl_ratrorerr1`, and `ST_RADERR1` becomes `st_raderr1`, not `st_rader1`. The plan must use the exact lowercase forms of the actual source headers throughout.

5\. Numeric validation is incomplete. The proposed code only preserves the existing canonical `uncertainty` logic and converts three optional blank fields. It does not implement numeric parsing or finite-value validation for the other designated archive fields. A broad `*ERR` name pattern is also insufficient on its own to define a safe numeric schema.

6\. The fixture’s row structure is still unreliable. The proposed data row contains whitespace-only fields and a long sequence of commas. It needs to be checked against all 21 header positions explicitly. The test should use a correctly sized fixture with unambiguous blank cells and verify the actual field-to-value alignment.

## Next step: targeted Plan v9

Send this to Cline in PLAN mode. This should be the final design correction before considering ACT.

# ECAS Chunk 4 — Final Targeted Plan Correction (v8 Review)

**Mode: PLAN only. No file modifications, fixture creation, or test execution.**

Revise `chunk_4_plan_v8` into `chunk_4_plan_v9`. Resolve the concrete implementation and test contradictions below. Do not repeat the full repository analysis.

## 1. Implement source preservation without changing generic alias behavior

Do not use `COLUMN_ALIASES.update(ARCHIVE_COLUMN_ALIASES)` as proposed in v8. That renames source headers and cannot meet the 23-column preservation contract.

Plan archive-specific handling that:

- Retains all 21 original archive columns under their normalized lowercase source names.
- Adds `wavelength` from `centralwavelng`.
- Adds `signal` from `pl_transdep`.
- Produces 23 unique column names and matching keys in every row dictionary.
- Defines the order of original and canonical columns.
- Rejects ambiguous collisions explicitly without silently overwriting source data.
- Leaves existing generic CSV alias behavior and regression expectations unchanged.

Inspect how the importer constructs `SpectrumData.columns` and row dictionaries before specifying the changes.

## 2. Remove unsupported alternative aliases

For this WASP-39 b dataset, use only:

- `centralwavelng` → `wavelength`
- `pl_transdep` → `signal`

Do not map `pl_ratror` to wavelength or `pl_radj` to signal. They represent different archive parameters, and the plan has not established that they are interchangeable with the intended plotting fields.

If broader support for other archive schemas is desired, leave it outside this burst unless authoritative evidence and existing project requirements justify it.

## 3. Correct every normalized header name

Use the exact lowercase forms obtained from the actual 21-column CSV. In particular, verify names such as:

- `pl_ratror`, `pl_ratrorerr1`, `pl_ratrorerr2`
- `pl_radj`, `pl_radjerr1`, `pl_radjerr2`
- `st_raderr1`, `st_raderr2`

Do not use shortened or misspelled alternatives such as `plrator` or `st_rader1`.

Provide one definitive classification list containing all 21 exact normalized headers and their intended types.

## 4. Specify complete numeric parsing behavior

For the actual archive schema, define which columns are numeric and which are metadata text. Do not use a wildcard error-column pattern as the sole schema definition.

For every designated numeric archive column:

- Parse nonblank values as finite floats.
- Preserve the sign of error-offset values.
- Convert blank numeric values to `None`.
- Raise a useful `SpectrumImportError` for malformed nonblank numeric values.

Metadata and author/reference fields remain strings; blank metadata values remain `""`.

Preserve the current canonical `uncertainty` validation and warning behavior for generic imports. Explain how the archive-specific parsing is isolated so unrelated imports do not change.

Do not infer units or claim that the fixture proves scientific interpretation.

## 5. Correct the test contract

Use the actual 21-column header and ensure every fixture row has exactly 21 source values. Make blank fields unambiguous and verify each row's field alignment against the header.

Specify tests with correct access patterns:

- `result.columns` contains exactly 23 unique keys for the archive fixture.
- `result.rows[0]["centralwavelng"]` and `result.rows[0]["pl_transdep"]` preserve the source values as floats.
- `result.rows[0]["wavelength"]` and `result.rows[0]["signal"]` contain the corresponding canonical values.
- Original source fields and canonical aliases coexist without overwriting.
- Signed error offsets retain their signs and are floats when populated.
- Blank numeric archive cells become `None`; blank metadata cells remain `""`.
- Malformed values in designated numeric fields raise `SpectrumImportError`.
- Existing generic CSV tests remain unchanged and pass.
- Unit metadata remains unset unless supported by authoritative evidence.

Do not assert that `SpectrumData` itself supports dictionary-style row access. Use the actual model API.

## 6. Scope and output

Keep the proposed ACT burst limited to:

- `ecas/ingestion/csv_importer.py`
- `tests/test_csv_importer.py`

Return only:

1. The finalized column and row storage contract.
2. The definitive 21-column classification list.
3. The exact importer changes required.
4. The corrected test plan and acceptance criteria.
5. Remaining uncertainties or blockers.
6. Confirmation that no files were modified and no tests were run.

Do not implement anything or request ACT approval in the plan. Stop for ChatGPT review of v9.

Once v9 comes back, the key decision is whether Cline has a coherent, minimal implementation that preserves archive data while maintaining generic-import compatibility. If it does, we can move to a tightly scoped ACT burst rather than continuing broad planning.