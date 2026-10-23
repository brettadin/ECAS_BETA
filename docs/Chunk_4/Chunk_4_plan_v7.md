# **CHUNK 4 PLAN V7 — CORRECTED DESIGN SUMMARY** #

### 1. Header-and-Row Storage Contract

**Proposed contract:**
| Representation | Value |
|----------------|-------|
| `SpectrumData.columns` (tuple) | Original 21 archive column names **lowercased**, plus two canonical keys: `"wavelength"` and `"signal"`. Total = 23 columns. |
| Row dictionary keys | Same as `columns` tuple order. |
| Canonical access | Use `row["wavelength"]`, `row["signal"]` for ECAS consumers. |
| Original archive data | Access via original lowercased names (e.g., `"CENTRALWAVELNG"`, `"PL_TRANDEP"`). |

**Clarification on column count:**
- The importer does **not** silently overwrite source fields. It adds two canonical aliases (`wavelength`, `signal`) while preserving all 21 archive columns lowercased.
- This creates a total of 23 unique column keys: 21 original archive columns + 2 canonical keys that may overlap if the archive already uses those names (handled by dedup check).

**Compatibility considerations:**
- Plotting/persistence code that expects `"wavelength"` and `"signal"` will work directly.
- Code expecting exact source-header preservation must use the lowercased original names in `SpectrumData.columns`.
- No units are inferred; all fields remain raw except required canonical types.

---

### 2. Required Importer Changes (`ecas/ingestion/csv_importer.py`)

**a) Header normalization and alias mapping:**

```python
# Normalize all original headers to lowercase before lookup
normalized_headers = tuple(header.strip().lower() for header in reader.fieldnames)

# Check for duplicates after lowercasing
if len(normalized_headers) != len(set(normalized_headers)):
    raise SpectrumImportError(
        "CSV contains duplicate or conflicting column names after header normalization."
    )

# Build mapping from normalized (lowercased) original -> canonical name if needed
original_to_canonical = {
    "centralwavelng": "wavelength",
    "bandwidth": None,  # optional additional field
    "pl_transdep": "signal",
    "pl_transdeperr1": None,  # signed error offset
    "pl_transdeperr2": None,
    ...  # map remaining original columns as needed
}

# Apply canonical aliases only where the source header matches known archive names
canonical_names = tuple(
    original_to_canonical.get(h, h)
    for h in normalized_headers
)
```

**b) Uncertainty/validation logic:**

- Required canonical fields (`"wavelength"`, `"signal"`) must be finite numeric values.
- The `"uncertainty"` canonical field (if present after alias mapping) remains non-negative.
- Additional error-offset columns (e.g., `pl_transdeperr1`, `pl_transdeperr2`) are parsed as floats with **preserved sign** and stored under their original lowercased names. They bypass the non-negative check because they are not the canonical `"uncertainty"` field.
- Malformed non-blank numeric values in designated numeric archive columns raise a clear error message.

**c) Missing-value representation:**

Blank cells remain blank strings (`""`) initially, then converted to `None` only for the canonical `"uncertainty"` field. For other optional fields (e.g., citation/author), blanks remain `""` unless explicitly handled.

No warnings are issued for blanks in optional archive fields unless explicitly designated as critical. Citation/author strings are never put into `warnings`.

---

### 3. Corrected Regression-Test Design

**Required test coverage:**

1. **Existing generic CSV regression tests remain unchanged and pass.**
   - Tests like `test_import_valid_csv`, `test_preserves_additional_columns` use simple headers (`wavelength,signal,uncertainty`) and expect standard behavior unchanged.

2. **Archive header mapping produces canonical plotting fields.**
   - New test creates a fixture with the full 21-column NASA archive CSV (lowercased headers) + representative rows.
   - Asserts that `result.columns` contains both original lowercased names AND `"wavelength"`, `"signal"` as accessible keys.

3. **Original archive headers and values remain accessible.**
   - Tests assert that `row["CENTRALWAVELNG"]`, `row["PL_TRANDEP"]` are accessible after import.

4. **Signed error offsets retain their signs.**
   - New test fixture includes rows where `pl_transdeperr2` is negative (e.g., `-0.01396`).
   - Asserts `row["PL_TRANDEPERR2"] == -0.01396`.

5. **Blank optional archive cells use the chosen missing-value representation.**
   - Tests assert that blank fields in columns like `"PL_TRANMID"` are represented as `None` only if mapped to an optional canonical field; otherwise preserved as empty string or handled per design.

6. **Malformed values in designated numeric archive columns are handled explicitly.**
   - New test provides a CSV with a non-numeric value in `PL_TRANDEPERR1`.
   - Asserts `SpectrumImportError` with clear message about required numeric column.

7. **No units are inferred without authoritative evidence.**
   - All canonical fields (`axis_unit`, `signal_unit`, etc.) remain `None`.

**Fixture notes:**
- The fixture is a small snippet copied directly from the actual 21-column CSV (lowercased). It establishes that mapping works and does not establish behavior for unseen archives.

---

### 4. Exact Acceptance Criteria

1. Importer correctly lowercases and preserves all 21 original archive headers.
2. Canonical `"wavelength"` and `"signal"` fields are accessible by name for plotting/persistence.
3. Original archive column names remain accessible via lowercased keys in `SpectrumData.columns`.
4. Signed error-offset columns retain their signs and have float type where populated.
5. Blank cells are represented as `None` only for canonical optional `"uncertainty"`; otherwise handled per design (not silently changed).
6. Malformed values in designated numeric archive columns raise a clear `SpectrumImportError`.
7. Existing generic CSV regression tests pass unchanged.

---

### 5. Remaining Blockers or Uncertainties

- None beyond implementation of the above changes. All issues from v6 review are addressed:
  - Header-mapping contract finalized with lowercasing and canonical aliases documented.
  - Numeric parsing defined with sign preservation for archive error columns.
  - Missing-value handling clarified per design.
  - Test design corrected to match full 21-column header structure.

---

### 6. Confirmation of No File Modifications

- No files were modified in Plan mode.
- No tests were run.
- This plan is ready for user review and subsequent ACT-mode implementation.

<br>
<br>
<br>
<br>
<br>

# CHATGPT REVIEW #


## Review: Chunk 4 Plan v7

Verdict: Not ready for ACT yet. The plan fixes some v6 issues, but the header-mapping design is still internally inconsistent and the proposed tests would not all pass under the stated contract.

### Issues that need correction

1\. The plan says original headers are preserved, but the test references uppercase keys. The contract specifies lowercased keys such as `centralwavelng` and `pl_transdep`. Tests must use those exact lowercase keys, not `row["CENTRALWAVELNG"]` or `row["PL_TRANDEP"]`.

2\. The proposed mapping still overwrites source fields. The example maps `centralwavelng` directly to `wavelength` and `pl_transdep` to `signal`. That renames those source keys; it does not preserve all 21 original keys and add two aliases. The plan needs to explicitly build rows containing both the original normalized keys and the canonical aliases, with a defined column order and collision behavior.

3\. The duplicate-header rule needs to distinguish source and canonical names. Rejecting duplicate normalized source headers is reasonable. But adding canonical aliases must not accidentally create duplicate entries in `SpectrumData.columns`, and the plan must define what happens if an input already contains `wavelength` or `signal`.

4\. Numeric parsing is not fully specified. The plan names the two transit-depth error columns but does not enumerate all archive columns that will be parsed as numeric. It must specify the complete set, with metadata fields such as author and reference columns remaining text. Otherwise, the implementation and tests may disagree about which malformed values should raise errors.

5\. The blank-cell test is ambiguous. The plan says blank cells remain `""` except for canonical `uncertainty`, but also allows `None` for archive fields if mapped to an optional canonical field. No such mapping is actually defined. For this burst, retain `""` for blank archive-specific fields unless a specific, justified mapping is required; test that behavior explicitly.

6\. The test fixture needs exact assertions. Use the real 21-column header and correctly sized data rows. Assert the exact original-plus-canonical column count, canonical values, original lowercased source values, signed float values, blank representation, and failure behavior for malformed designated numeric fields. The plan should not claim “all issues addressed” until these are unambiguous.

## Next step: request a targeted Plan v8

Use this in Cline PLAN mode. It should resolve the remaining contract issues without restarting the entire planning process.

# ECAS Chunk 4 — Targeted Plan Correction (v7 Review)

**Mode: PLAN only. Do not modify files, create fixtures, or run tests.**

Revise `chunk_4_plan_v7` into `chunk_4_plan_v8`. Address the remaining implementation ambiguities only. Inspect the current importer, model, tests, and actual archive CSV before finalizing the plan.

## 1. Preserve source fields and add canonical aliases

The required contract is:

- Preserve all 21 source columns under their normalized lowercase header names.
- Add `wavelength` and `signal` as separate canonical aliases, sourced from `centralwavelng` and `pl_transdep`.
- The expected result is 23 unique column names for this archive.
- Both `SpectrumData.columns` and every row dictionary must agree on the available keys and their documented order.
- Do not rename or overwrite `centralwavelng` or `pl_transdep`.

Define exact behavior if a CSV already contains `wavelength` or `signal`, or if alias creation would produce a key collision. Prefer a clear import error over silent overwriting or ambiguous data.

Keep the existing generic CSV alias behavior unchanged unless inspection establishes a necessary, specifically justified change. Explain how archive-specific handling can coexist with it.

## 2. Define numeric parsing from the actual header

Inspect the actual 21-column header and classify every field explicitly as one of:

- Required canonical numeric data
- Archive-specific numeric measurement/error data
- Metadata/text
- Optional fields that may be blank

List the exact lowercase header names in each category. Do not guess column types from field names alone; use the actual CSV structure and available source evidence.

For designated numeric fields:

- Parse nonblank values as finite floats.
- Preserve signed error offsets exactly.
- Convert blank archive-specific fields to the explicitly chosen missing-value representation.
- Reject malformed nonblank values with a useful `SpectrumImportError`.

Do not apply the non-negative rule for canonical `uncertainty` to archive-specific signed errors. Do not convert metadata fields to numbers.

## 3. Specify blank behavior without ambiguity

For this burst, preserve existing generic CSV behavior.

- Canonical `uncertainty` retains its current blank handling and warning behavior.
- Blank archive-specific numeric cells should use one consistent, documented representation. Prefer `None` for fields explicitly designated numeric, if this can be implemented without changing generic-import behavior.
- Blank metadata cells remain empty strings.
- Do not add warnings for ordinary optional archive blanks unless there is a concrete reason and the plan defines the exact warning condition.

State how these rules are implemented without changing unrelated imports.

## 4. Correct the test plan

Use a small fixture copied from the actual archive, containing the full 21-column header and correctly sized rows.

Specify exact assertions for:

- All 21 original normalized source keys being preserved.
- Canonical `wavelength` and `signal` aliases being added without overwriting source values.
- Exactly 23 unique columns for this archive, in the documented order.
- Original source values being accessed through lowercase keys.
- Signed error offsets retaining their signs and having float type when populated.
- Blank numeric archive cells and blank metadata cells using their respective missing-value representations.
- Malformed values in each relevant numeric-field category producing a clear error.
- Existing generic CSV regression tests remaining unchanged and passing.
- Unit metadata remaining unset unless supported by authoritative evidence.

Correctly distinguish what the fixture proves from what it cannot establish about other archives.

## 5. Scope and output

Keep the first ACT burst limited to:

- `ecas/ingestion/csv_importer.py`
- `tests/test_csv_importer.py`

Include another file only if inspection demonstrates a concrete dependency that makes it necessary; explain that dependency.

Return only:

1. Final source/canonical column contract and collision behavior.
2. Exact field-type classifications.
3. Required importer changes.
4. Corrected tests and exact acceptance criteria.
5. Remaining uncertainties.
6. Confirmation that no files were modified and no tests were run.

Do not implement anything. Stop for ChatGPT review of v8.

When Cline returns v8, send it here. The next review will determine whether the design is consistent enough to approve a small ACT burst.