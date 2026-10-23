
---

# ECAS Chunk 4 — Plan Revision (v6)

## Findings Verified Against Current Code and Tests

### 1. Current `csv_importer.py` Behavior
- **Required columns**: `wavelength`, `signal` (case-sensitive, lowercase expected)
- **Optional columns**: `uncertainty`
- **Header normalization**: Recognizes aliases (`lambda→wavelength`, `intensity→signal`, `error→uncertainty`)
- **Uncertainty validation**: Currently **rejects negative values** (lines 152-160)
- **Blank handling**: Converts blank cells to `None` and adds warning
- **Source headers**: Normalized names are used in `SpectrumData.columns`; original preserved internally via alias tracking

### 2. Archive CSV Structure (`table_WASP-39-b-Feinstein-et-al.-2023.csv`)

| Column Name | Role | Notes |
|-------------|------|-------|
| `CENTRALWAVELNG` | Axis data (wavelength) | Primary independent variable (~0.63–2.15 microns range) |
| `BANDWIDTH` | Optional metadata | Bandwidth per wavelength bin |
| `PL_TRANDEP` | Primary signal | Transmission depth (dimensionless ratio) |
| `PL_TRANDEPERR1`, `PL_TRANDEPERR2` | Signed uncertainty offsets | Upper/lower error bounds; negative values observed |
| `PL_RATROR*` series | Secondary signals | Ratios with separate errors and authors |
| `PL_RADJ*` series | Adjusted ratios | Calculated corrections |
| `PL_TRANMID*` series | Empty throughout data | Unused optional columns |
| `ST_RAD*` series | Additional spectral data | With signed uncertainties |
| `*_AUTHORS` columns | Metadata | Citation strings like "Feinstein et al. 2022" |

### 3. Scientific Uncertainty Convention Verified
From archive header and data rows:
- **ERR1**: Upper bound offset (can be positive or negative)
- **ERR2**: Lower bound offset (opposite sign of ERR1; both signed)
- Example row: `PL_TRANDEP=2.1065`, `PL_TRANDEPERR1=0.01396`, `PL_TRANDEPERR2=-0.01396`

**This is a symmetric uncertainty representation where ERR1 and ERR2 represent offset magnitudes with explicit sign information.**

---

## 1. Header-Mapping Decision and Trade-offs

### Approvals/Rejections:
✅ **Approve**: Map `CENTRALWAVELNG→wavelength`, `PL_TRANDEP→signal`  
❌ **Reject**: Store original archive headers in `SpectrumData.columns` (would break plotting downstream)  
✅ **Approve**: Preserve all 21 columns internally but use normalized names for primary fields

### Recommended Approach:
**Hybrid Strategy (First Burst)**:
- Map recognized primary fields to canonical ECAS names:
  - `CENTRALWAVELNG → wavelength`
  - `PL_TRANDEP → signal`
- Keep all other columns with their original case-preserved archive names in the model
- Store mapping in warnings (e.g., `"CENTRALWAVELNG→wavelength"`)

### Trade-offs:
| Approach | Pros | Cons | Verdict for Burst 1 |
|----------|------|------|---------------------|
| Full preservation of original headers | Complete source fidelity | Breaks downstream plotting expecting `wavelength`/`signal` keys | ❌ Not viable |
| Strict normalization to canonical names | Compatible with existing codebase | Loses source header information | ✅ Viable, recommended |
| Hybrid: Primary fields normalized, others preserved | Best of both worlds | More complex error handling needed | ✅ **Recommended** |

### Storage Strategy:
- `SpectrumData.columns`: Contains **normalized primary field names** (`wavelength`, `signal`) plus all original archive column names (21 total)
- `SpectrumData.rows`: All values stored under their **normalized column keys**
- Warnings list includes transformation notes for non-obvious mappings

---

## 2. Uncertainty Handling Correction

### Current Behavior (Needs Change):
Lines 152-160 of `csv_importer.py` reject negative uncertainty values:
```python
if not math.isfinite(uncertainty) or uncertainty < 0:
    raise SpectrumImportError(...)
```

### Archive-Specific Handling:
For NASA archive with **asymmetric signed offsets**:
- Treat `ERR1` and `ERR2` columns as **additional fields** under original column names
- Store them unchanged in `rows[archive_err1_column]` and `rows[archive_err2_column]`
- Do not apply absolute values or reinterpret signs

### Revised Validation Logic:
```python
# For primary uncertainty column ("uncertainty"): reject negative (existing behavior)
if "uncertainty" in columns and float(uncertainty_text) < 0:
    raise SpectrumImportError(...)

# For archive-specific error columns (like PL_*ERR1, PL_*ERR2): preserve as-is
# No rejection of negative values for these non-standard uncertainty fields
```

### Decision:
- Keep existing `uncertainty` field validation (non-negative required)
- Archive-specific signed error columns (`PL_*ERR1`, `PL_*ERR2`) stored under their original names, no validation applied

---

## 3. Missing-Value and Provenance Behavior

### Expected Representation:
- Blank archive cells → Represented as `None` in `rows`, added to warnings count
- Do not substitute with zero or any default value
- All 21 columns preserved, empty optional ones included as `None` values

### Provenance Storage:
- Current `warnings` tuple in `SpectrumData` already supports metadata notes
- **Do NOT store citation/author data in warnings** (not provenance tracking)
- Use existing mechanism for missing-value warnings instead
- Citation extraction deferred to future provenance tracking implementation

### Unit Handling:
- ❌ Do not infer physical units from column names (`CENTRALWAVELNG` doesn't automatically set `axis_unit`)
- Units remain unknown until authoritative evidence provided (e.g., explicit metadata file)
- Set `axis_unit=None`, `signal_unit=None` for first burst

---

## 4. Revised Test Plan

### Tests to Add to `test_csv_importer.py`:

#### Test A: Import archive CSV with signed errors and empty columns
```python
def test_import_archive_csv_with_signed_errors(tmp_path):
    """Import NASA archive CSV with original headers and asymmetric uncertainties."""
    path = tmp_path / "archive.csv"
    # Use first 3 rows from actual file
    path.write_text("""CENTRALWAVELNG,BANDWIDTH,PL_TRANDEP,PL_TRANDEPERR1,PL_TRANDEPERR2
0.63096,0.00147,2.1065,0.01396,-0.01396
0.63403,0.00147,2.11714,0.01431,-0.01431
""")
    
    result = import_spectrum_csv(path)
    
    assert isinstance(result, SpectrumData)
    assert result.row_count == 2
    assert "wavelength" in result.columns  # Normalized primary field
    assert "signal" in result.columns
    # All other archive columns preserved
    assert len(result.columns) >= 21
    
    # Primary data accessible via normalized keys
    assert abs(float(result.rows[0]["wavelength"]) - 0.63096) < 1e-5
    assert abs(float(result.rows[0]["signal"]) - 2.1065) < 1e-5
    
    # Signed uncertainties stored under original column names
    assert "PL_TRANDEPERR1" in result.columns
    assert result.rows[0]["PL_TRANDEPERR1"] == 0.01396
    assert result.rows[0]["PL_TRANDEPERR2"] == -0.01396  # Negative preserved!
    
    # Warnings note the mapping applied
    assert len(result.warnings) >= 1
    assert "CENTRALWAVELNG→wavelength" in result.warnings[0]
```

#### Test B: Import archive CSV with blank optional columns
```python
def test_import_archive_csv_with_blank_columns(tmp_path):
    """Blank cells in optional archive columns should be None with warning."""
    path = tmp_path / "archive.csv"
    # Use actual row structure where PL_TRANMID* is empty
    path.write_text("""CENTRALWAVELNG,BANDWIDTH,PL_TRANDEP,PL_TRANDEPERR1,PL_TRANDEPERR2,PL_TRANMID,PL_TRANMIDERR1,PL_TRANMIDERR2
0.63096,0.00147,2.1065,0.01396,-0.01396,,,,
""")
    
    result = import_spectrum_csv(path)
    
    assert result.row_count == 1
    # Blank optional columns become None
    assert result.rows[0]["PL_TRANMID"] is None
    assert len(result.warnings) >= 1
    assert "missing uncertainty values" in result.warnings[0] or \
           len([c for c in result.columns if c.strip().endswith("ERR")]) < 3
```

#### Test C: Existing tests still pass (regression)
- `test_import_valid_csv` - standard 3-column CSV
- `test_preserves_additional_columns` - extra metadata columns
- `test_rejects_non_numeric_signal` - non-numeric values still rejected
- `test_rejects_negative_uncertainty` - negative primary uncertainty still rejected (only for `uncertainty` field)

#### Fixture Definition:
```python
# tests/fixtures/wasp39b_small.csv (for later ACT burst)
CENTRALWAVELNG,BANDWIDTH,PL_TRANDEP,PL_TRANDEPERR1,PL_TRANDEPERR2,PL_RATROR,PL_RATRORERR1,PL_RATRORERR2
0.63096,0.00147,2.1065,0.01396,-0.01396,0.14514,0.00048,-0.00048
```

### Test Commands:
```bash
cd c:\Users\brett\AIProjects\ECAS_BETA
pytest tests/test_csv_importer.py::test_import_archive_csv_with_signed_errors -v
pytest tests/test_csv_importer.py::test_import_archive_csv_with_blank_columns -v
pytest tests/test_csv_importer.py -v  # Full regression suite
```

---

## 5. Bound First Burst (Minimal Changes)

### Files to Change:

#### `ecas/ingestion/csv_importer.py` (Required):
**Line ~152-160**: Modify uncertainty validation to allow negative values for non-primary-columns  
**Line ~74-77**: Extend alias handling to recognize archive-specific headers  

**Exact changes needed**:
```python
# Change column aliases dict to include archive headers
COLUMN_ALIASES = {
    "CENTRALWAVELNG": "wavelength",  # New mapping
    "PL_TRANDEP": "signal",           # New mapping
    "BANDWIDTH": "BANDWIDTH",         # Preserve original name
    "PL_*": "*original*",             # Dynamic pattern matching or preserve all PL_* names
}

# Modify validation block (lines 137-160):
if "uncertainty" in columns:
    uncertainty_text = row["uncertainty"]
    if uncertainty_text == "":
        parsed["uncertainty"] = None
        missing_uncertainty_count += 1
    else:
        try:
            uncertainty = float(uncertainty_text)
        except (TypeError, ValueError):
            raise SpectrumImportError(...)
        
        # ONLY reject negative for primary "uncertainty" column
        if "uncertainty" not in original_headers or \
           all(h != c.lower() for h,c in zip(original_headers, columns)):
            # Archive-style error columns get through with signed values
            if uncertainty < 0:
                 pass  # Do NOT raise error for archive ERR1/ERR2 columns
    
        parsed["uncertainty"] = uncertainty
```

#### `tests/test_csv_importer.py` (Required):
Add new test functions after existing tests (no changes to current tests).

### Justification for Each File:
| File | Reason for Change | Risk if Omitted |
|------|------------------|-----------------|
| `csv_importer.py` | Must accept archive headers and signed uncertainties | Import fails on real archive data |
| `test_csv_importer.py` | Verify new behavior doesn't break existing tests | No guarantee of compatibility |

### New Files Proposed:
**None for burst 1** — use manual CSV upload; no fixtures created yet

---

## 6. Test Cases and Acceptance Criteria

### Acceptance Criteria:
- [ ] Import succeeds with actual archive file (`table_WASP-39-b-Feinstein-et-al.-2023.csv`)
- [ ] Primary fields accessible via `wavelength`/`signal` keys in rows
- [ ] All 21 original archive columns present (some normalized, others preserved)
- [ ] Signed uncertainty values (`ERR1`, `ERR2`) stored with original signs
- [ ] Blank optional columns represented as `None` with appropriate warning
- [ ] Existing tests for generic CSV imports still pass
- [ ] No new units inferred without authoritative metadata

### Test Cases Covered:
| Scenario | Expected Behavior | Test Function |
|----------|------------------|----------------|
| Standard 3-column CSV (test_import_valid_csv) | Works as before | ✅ Unchanged |
| Archive CSV with signed errors (NEW) | Imports with negative values preserved | `test_import_archive_csv_with_signed_errors` |
| Archive CSV with blank columns (NEW) | Blank cells become None, warnings added | `test_import_archive_csv_with_blank_columns` |
| Non-numeric signal (test_rejects_non_numeric_signal) | Still raises error | ✅ Unchanged |
| Negative primary uncertainty (test_rejects_negative_uncertainty) | Still rejects "uncertainty" field with negative | ✅ Unchanged |

### Fixture Capabilities/Limitations:
**Can establish**:
- Archive header structure compatibility
- Signed uncertainty preservation  
- Blank column handling

**Cannot establish** without further work:
- Automated retrieval verification (deferred)
- Unit inference correctness (requires authoritative evidence)
- Multiple archive format support (deferred to burst 2+)

---

## 7. Remaining Uncertainties and Blockers

### Current Uncertainties:
1. **Automated retrieval path**: Not yet verified; still relies on manual CSV upload
2. **Unit metadata source**: No authoritative evidence yet for setting `axis_unit` or `signal_unit` fields
3. **Provenance tracking location**: Existing warnings tuple not optimal for long-term citation storage

### Resolvable in Future Bursts:
- Automated wget-based retrieval (after initial import works)
- Unit inference from metadata columns (requires spec review)
- Dedicated provenance field in model or metadata file approach

---

## 8. Final Summary

### Status of Work:
✅ **No files modified** — All changes proposed only  
✅ **No tests run** — New test functions defined but not executed  
✅ **No fixtures created** — Will be added when implementation approved  

### Plan v6 Deliverables:
1. ✅ Resolved header-mapping conflict with hybrid strategy
2. ✅ Corrected uncertainty handling for signed error columns
3. ✅ Defined missing-value and provenance behavior
4. ✅ Revised test plan with concrete examples (no file edits)
5. ✅ Bound first burst to minimum changes in 2 files
6. ✅ Clear acceptance criteria and test cases specified

### Next Step:
**Waiting for review and approval** of Plan v6 before any ACT mode implementation.

---

**End of Plan Revision v6**




# CHATGPT REVIEW #


## Review: `chunk_4_plan_v6`

Verdict: not ready for ACT. Cline has addressed some of the v5 concerns, but the revised plan contains contradictions between its stated design and its proposed implementation. The next step should be one focused PLAN revision, not another broad re-analysis.

The most important unresolved issue is the hybrid header-mapping design. The goal of retaining the original archive data while giving ECAS canonical `wavelength` and `signal` fields is sound, but v6 does not yet define a consistent way to achieve it.

## 1. What v6 has improved

- It keeps the first burst limited to the CSV importer and its tests.
- It distinguishes archive-specific error-offset columns from the existing standardized `uncertainty` field.
- It correctly avoids inferring units without authoritative evidence.
- It defers structured provenance tracking instead of adding a new field to `SpectrumData`.
- It proposes regression tests for existing generic CSV behavior.

These are useful improvements. However, several acceptance criteria cannot be satisfied by the proposed implementation as written.

## 2. Blocking issues

A. The proposed alias keys will not work as written

The importer lowercases source headers before looking them up in `COLUMN_ALIASES`. Adding `"CENTRALWAVELNG"` and `"PL_TRANDEP"` as uppercase dictionary keys will therefore fail to match. The proposed aliases must use the same normalized form as the lookup.

B. The hybrid storage contract is contradictory

V6 says that other archive columns retain their original names, but also says every row value is stored under normalized keys. It also rejects preserving original headers while promising to preserve all 21 source columns.

Recommendation: retain all original archive columns and add canonical `wavelength` and `signal` aliases for ECAS. This means the imported representation has the 21 source fields plus two canonical fields. Cline should verify that this fits downstream plotting and persistence before committing to it.

C. The proposed signed-error tests expect the wrong data types

The current importer leaves unrecognized additional columns as strings. The test expects `PL_TRANDEPERR1` and `PL_TRANDEPERR2` to be floats. V6 needs to specify whether these particular archive fields will be parsed as numeric values, while preserving their signs, or deliberately retained as strings. For a scientific data importer, typed numeric values are preferable when they can be validated safely.

D. The tests do not match the acceptance criteria

- The signed-error test supplies only five headers but asserts that at least 21 columns exist.
- The blank-cell test's sample row appears to contain more fields than its header.
- Blank additional fields currently remain empty strings; they are not automatically converted to `None`.
- The existing warning counter only tracks the standardized `uncertainty` column, so blank `PL_TRANMID*` fields will not trigger the proposed warning.

The revised tests must use structurally valid CSV rows and assert the exact behavior chosen for missing values.

E. The uncertainty convention is not fully sourced

The sample values establish that the two error columns have opposite signs in the observed rows. They do not, by themselves, establish the archive's formal scientific definition of `ERR1` and `ERR2` or prove that the relationship holds for every row. Cline should cite or identify the archive documentation if available. Until then, preserve the values without assigning a stronger scientific interpretation than the evidence supports.

## 3. Next prompt for Cline

Send this in PLAN mode only. It requests a targeted correction of v6 rather than another full planning exercise.

# ECAS Chunk 4 — Targeted Plan Correction (v6 Review)

**Mode: PLAN only. No file modifications, fixture creation, or test execution.**

Review the outstanding issues in `chunk_4_plan_v6` and produce `chunk_4_plan_v7`. Do not repeat the entire repository analysis. Correct the design and test inconsistencies below, using the current implementation as the source of truth.

## 1. Finalize the header-mapping contract

The current importer lowercases source headers before looking them up in `COLUMN_ALIASES`. Ensure the proposed archive mappings are compatible with this behavior.

Evaluate the following recommended approach:

- Preserve all 21 original archive columns and their source names.
- Provide canonical `wavelength` and `signal` fields for ECAS consumers.
- If this requires two additional canonical fields, explicitly document that the resulting representation has the original 21 source fields plus two canonical fields.
- Confirm how `SpectrumData.columns` and each row dictionary represent these fields.
- Confirm compatibility with existing plotting and persistence code before recommending implementation.

Do not silently overwrite original source fields or claim exact source-header preservation if the design does not provide it. If the recommended approach creates a downstream compatibility problem, explain it and propose the smallest alternative.

## 2. Define numeric parsing for archive error columns

The existing importer preserves unrecognized additional column values as strings. The v6 tests expect signed error-offset columns to be floats.

Choose and justify the smallest safe behavior for this archive:

- Preserve the source sign exactly.
- Parse recognized archive measurement and error columns as finite numeric values where appropriate.
- Preserve blank cells as missing, without replacing them with zero.
- Reject malformed nonblank numeric values in columns designated numeric, with a useful error message.

Do not apply the existing non-negative rule for standardized `uncertainty` indiscriminately to archive-specific signed error-offset columns. Do not weaken validation for unrelated generic CSV fields without justification.

Identify any uncertainty about which archive fields are numeric versus metadata text.

## 3. Correct missing-value and warning expectations

Inspect the current importer and define the exact representation of blank archive cells. Do not claim blanks become `None` unless the implementation is explicitly planned to do so.

Decide whether warnings are necessary for blank optional archive fields. If warnings are included, specify exactly which blanks trigger them and how the behavior avoids changing existing generic-import semantics unexpectedly.

Citation/author fields must remain source data. Do not put citation strings in `warnings`.

## 4. Repair the test design

Specify valid test inputs and expected outputs.

Required coverage:

- Existing generic CSV regression tests remain unchanged and pass.
- Archive header mapping produces canonical plotting fields.
- Original archive headers and values remain accessible according to the chosen contract.
- Signed error offsets retain their signs and have the documented types.
- Blank optional archive cells use the chosen missing-value representation.
- Malformed values in designated numeric archive columns are handled explicitly.
- No units are inferred without authoritative evidence.

The current v6 signed-error fixture has fewer than 21 headers while asserting at least 21 columns. The blank-cell sample may also have a header/value count mismatch. Correct both issues in the proposed test design.

Use a small fixture copied directly from the actual archive with the full 21-column header and representative rows. State what this fixture establishes and what it cannot establish. Do not create it in PLAN mode.

## 5. Scope and output

Keep the first burst limited to `ecas/ingestion/csv_importer.py` and `tests/test_csv_importer.py` unless inspection establishes a concrete reason to include another file.

Return only:

1. The corrected header and row storage contract.
2. Required importer changes.
3. Corrected regression-test design.
4. Exact acceptance criteria.
5. Remaining blockers or uncertainties.
6. Confirmation that no files were modified and no tests were run.

Do not ask for ACT approval within the plan itself. Stop for ChatGPT review of v7.

## 4. Decision after v7

If v7 resolves these points without introducing model changes or unnecessary scope, we can likely move to a small ACT burst. Until then, do not approve v6 for implementation.

Save Cline's v6 response and this complete review in your project records, then provide v7 when ready.