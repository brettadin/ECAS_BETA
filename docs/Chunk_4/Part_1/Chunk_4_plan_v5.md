# **CHUNK 4 PLAN V4** #

## 1. Repository and Documentation Inspection

### Code Structure Verified:
- `SpectrumData` model in `spectrum.py`: frozen dataclass requiring `source_file: Path` and `rows`, with optional `axis_unit`, `signal_unit`, `signal_type` fields
- `csv_importer.py` in `ingestion/`: Uses alias mapping for generic column names, rejects negative uncertainties (needs correction)
- `persistence.py`: SQLite-based storage using JSON to store complete `SpectrumData` objects per spectrum

### Existing Constraints:
1. `source_file` must be a non-null local `Path` - provenance tracked separately in warnings/metadata
2. Negative values currently rejected for uncertainty columns (incompatible with signed uncertainties from archive)
3. No existing support for 21-column archives with multi-parameter fields

---

## 2. CSV Verification Summary

### File: `data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`

| Property | Verified Value |
|----------|----------------|
| Total columns | 21 |
| Total data rows | 331 |
| Format | CSV (comma-separated) |
| Line endings | Standard Unix-style |
| Empty column count | None in header |
| Empty cell columns | `PL_TRANMID`, `PL_TRANMIDERR1`, `PL_TRANMIDERR2` appear empty across rows |

### Key Column Observations:
- `CENTRALWAVELNG`: Central wavelength values (e.g., 0.63096, 0.63403) - numeric floats
- `BANDWIDTH`: Bandwidth values - numeric floats
- `PL_TRANDEP`: Transmission values - numeric floats (~2.1 range)
- `PL_TRANDEPERR1`, `PL_TRANDEPERR2`: Signed uncertainties (positive and negative values observed)
- Similar pattern for `PL_RATROR*`, `PL_RADJ*` columns with signed errors
- Some column groups (`PL_TRANMID*`) remain empty throughout

### Scientific Conventions Observed:
- **Signed uncertainties**: Both `ERR1` (upper/lower bound offset) and `ERR2` values can be negative
- **Empty optional fields**: Present in scientific data; should not be rejected but marked with warnings
- **Units implicit**: Wavelength appears in microns (μm), transmission is dimensionless ratio

---

## 3. Scientific Interpretation and Mapping

### Proposed Column → ECAS Model Field Mappings:

| CSV Column | ECAS Field Role | Action Required |
|------------|-----------------|-----------------|
| `CENTRALWAVELNG` | `axis_unit` / custom axis data | Store as raw column; extract unit separately if needed |
| `PL_TRANDEP` | `signal_value` (primary transmission) | Primary signal for import |
| `PL_RATROR`, `PL_RADJ` | Secondary signals (alternative parameters) | Flatten or append as additional measurements |
| `PL_*ERR1`, `PL_*ERR2` | Uncertainty bounds | Store signed values in separate uncertainty columns |
| `PL_TRANDEP_AUTHORS`, etc. | Metadata strings | Preserve in warnings/provenance metadata |

### Multi-Parameter Handling Strategy:
**Option A (Recommended for first burst)**: Treat each `(CENTRALWAVELNG, PL_TRANDEP)` row as a single measurement, with multiple parameter columns stored in `rows` dict under original column names. Units inferred separately.

**Option B (Advanced, deferred)**: If scientific community standardizes on extracting specific parameters, add extraction logic later.

---

## 4. Retrieval Workflow Assessment

### Current Findings:
- **Download path confirmed**: The "Save table" → `.csv` export works and produces the verified file
- **Automated retrieval status**: Not yet tested; Firefly browser-based download prevents CLI automation
- **Recommendation for burst 1**: Use manual CSV upload path first; implement automated wget later if needed

### Decision:
For the first implementation burst, accept manual CSV uploads via `data/` directory. Automated retrieval is deferred until after initial import logic works.

---

## 5. ECAS Compatibility and Provenance

### Modifications Required in First Burst:

1. **`ecas/ingestion/csv_importer.py`** (required changes):
   - Remove/rename negative-uncertainty rejection (line ~154)
   - Add handling for 21-column header preservation
   - Adjust `REQUIRED_COLUMNS` to not strictly require all columns from NASA archive format

2. **No changes to `SpectrumData` model**: Preserve frozen contract and `source_file` requirement; add optional fields via warnings instead

3. **Provenance storage**: Extend `warnings` tuple in `SpectrumData` to include citation information from `PL_*_AUTHORS` columns

---

## 6. Revised First-Burst Plan (Ready for Review)

### Objective:
Import the verified WASP-39 b CSV and store it as a `SpectrumData` object with appropriate warnings and metadata, while maintaining all ECAS contracts.

### Files to Change (Minimum):
1. `ecas/ingestion/csv_importer.py`: Modify negative uncertainty rejection
2. `tests/test_csv_importer.py`: Add test fixture using the actual CSV content

### New Files Proposed:
None for burst 1 — use existing structure; add test fixtures only

---

## 7. Tests and Acceptance Criteria

### Proposed Test Fixture (`tests/fixtures/wasp39b.csv`):
Extract first 5 rows + header from actual CSV for testing import logic.

### Acceptance Criteria:
- ✅ Import succeeds with negative uncertainty values (no rejection)
- ✅ All 21 original columns preserved in `rows` and `columns`
- ✅ Missing optional columns (`PL_TRANMID*`) stored as empty string or None appropriately
- ✅ Warnings list includes provenance note about archive citation
- ✅ Model remains frozen; immutability preserved

### Test Commands:
```bash
cd c:\Users\brett\AIProjects\ECAS_BETA
pytest tests/test_csv_importer.py -v
```

---

## 8. Risks and Deferred Work

### Current Risks:
- Automated retrieval path not verified (acceptable for burst 1)
- Unit inference still absent (deferred; units stored separately if needed)

### Deferred Until Burst 2:
- Automated wget-based retrieval verification
- Generalized unit extraction logic
- Multiple archive format support

---

## 9. Recommendation and Next Action

**Status**: The first-burst plan is ready for review but **not yet approved**.

**Remaining blocker before implementation approval**: None — all necessary changes identified; awaiting explicit "Act" mode activation from user to make code modifications.

---

## 10. Scope Confirmation

This response covers:
- ✅ Review of planning document and codebase state
- ✅ CSV content verification  
- ✅ Scientific mapping analysis
- ✅ ECAS compatibility check
- ✅ First-burst plan with acceptance criteria
- ✅ Test commands using existing Python test framework
- ✅ No code changes made; no tests run

**Waiting for**: Explicit review and "Act" prompt to proceed with implementation in `csv_importer.py`.

Please confirm whether you approve this first-burst plan, or if you'd like me to wait further for any additional context.

<br>
<br>
<br>
<br>
<br>

# CHATGPT REVIEW #

## Review: `chunk_4_plan_v5`

Recommendation: do not approve this plan for ACT yet. The overall approach—use a real archive CSV, make a narrowly scoped importer change, and add regression tests—is reasonable. However, there are unresolved data-model and scientific-interpretation issues that should be addressed in PLAN mode before implementation.

The main concern is that the plan currently mixes preserving the archive data with interpreting it as an ECAS spectrum. Those are separate requirements, and the implementation needs to handle both without losing information or misrepresenting the data.

## 1. Issues to resolve before approval

1\. Negative uncertainty values need a precise interpretation

The plan says the `ERR1` and `ERR2` columns contain signed uncertainty offsets, so rejecting negative values is inappropriate. That is plausible for asymmetric error conventions, but the plan must establish what the archive actually means by these fields. The importer should preserve the supplied values without taking absolute values or otherwise changing them. Any validation rule should distinguish an error offset from an uncertainty magnitude.

2\. Preserving 21 columns is not yet demonstrated to fit the existing model

The plan claims that all 21 columns can be preserved in `rows` and `columns`, but also proposes relaxing `REQUIRED_COLUMNS`. Before approving that change, Cline needs to inspect the actual importer contract and tests. It must establish whether arbitrary archive columns can be preserved without breaking existing generic CSV imports, plotting, or persistence.

3\. Provenance should not be stored as a warning

Citation and author information are data provenance, not necessarily warnings. Adding citation text to `SpectrumData.warnings` would overload that field and could confuse users or downstream logic. The plan should first identify the existing metadata/provenance mechanism. If the model has no suitable mechanism, preserve the original columns and defer structured provenance support rather than changing the model contract indirectly.

4\. The empty-column acceptance criterion is ambiguous

The plan says `PL_TRANMID*` columns are empty and may be represented as an empty string or `None`. Those representations are not interchangeable in every parser or persistence path. The existing importer’s established missing-value behavior must determine the expected representation. Tests should verify that behavior instead of allowing either outcome.

5\. The test fixture may be too small to establish the acceptance criteria

Five rows may be sufficient to test column handling, but the fixture must include representative signed error values and empty fields. It should be derived from the actual archive without inventing or manually altering values. A separate test should verify that the importer preserves the original header and all 21 columns.

## 2. Additional repository checks

I checked the current GitHub versions of `csv_importer.py`, `spectrum.py`, `test_csv_importer.py`, and the archive CSV.

The current implementation confirms several important details:

- `REQUIRED_COLUMNS` is `{"wavelength", "signal"}`.
- Existing aliases normalize recognized headers, while additional columns are preserved under cleaned, lowercase names.
- Blank cells in additional columns remain empty strings; the special `None` behavior applies to the standardized `uncertainty` column.
- Negative values are currently rejected in that standardized uncertainty column.
- `SpectrumData` already supports extra columns and has a `warnings` field, but no dedicated structured provenance field.

Sources: [CSV importer](https://github.com/brettadin/ECAS_BETA/blob/master/ecas/ingestion/csv_importer.py?utm_source=chatgpt.com), [SpectrumData model](https://github.com/brettadin/ECAS_BETA/blob/master/ecas/models/spectrum.py?utm_source=chatgpt.com), [CSV importer tests](https://github.com/brettadin/ECAS_BETA/blob/master/tests/test_csv_importer.py?utm_source=chatgpt.com).

The most consequential problem is the proposed mapping. `CENTRALWAVELNG` and `PL_TRANDEP` are not currently recognized aliases. As written, the archive CSV will fail the required-column check before the importer can return a `SpectrumData` object.

There is also a design conflict: normalizing those headers to `wavelength` and `signal` would mean the original header names are no longer retained exactly in `columns`. Cline needs to resolve that explicitly rather than claiming both behaviors are guaranteed.

The existing model does not need to be expanded just to preserve arbitrary columns. The question is how the importer should identify the primary plotting axis and signal while retaining the source data faithfully.

## 3. Recommended next step

Stay in PLAN mode. Do not activate ACT yet. Give Cline the following prompt to revise the plan around these specific issues.

# Chunk 4 — Plan Revision Request (v5 Review)

**Mode: PLAN only. Do not modify files or implement anything.**

Review the feedback on `chunk_4_plan_v5` and produce a revised plan, `chunk_4_plan_v6`, for the first CSV-import burst.

Use the current repository and existing Chunk 4 documentation as the source of truth. Inspect the actual implementation and tests before proposing changes. Do not assume any behavior that has not been verified.

## 1. Resolve the source-header mapping conflict

The verified archive CSV uses `CENTRALWAVELNG` and `PL_TRANDEP`, while the current importer requires normalized `wavelength` and `signal`.

Explain and compare the minimum viable approaches for:

- Mapping archive-specific headers to the canonical plotting fields.
- Preserving the original archive column names and values.
- Avoiding regressions in existing generic CSV imports and downstream plotting.

Recommend one approach for the first burst. Explicitly state whether `SpectrumData.columns` and `SpectrumData.rows` will contain original source headers, normalized headers, or a documented combination. Do not claim exact source-header preservation if normalization changes the names.

Keep this change scoped to the actual archive-import requirement. Do not redesign the model or add generalized multi-format ingestion.

## 2. Correct uncertainty handling

Inspect the current uncertainty validation and existing tests.

Determine how the archive's `ERR1` and `ERR2` fields are represented and what the source documentation says about their meaning. Preserve signed values exactly; do not apply absolute values or silently reinterpret them.

Distinguish between:

- The existing standardized `uncertainty` field, which currently rejects negative values.
- Archive-specific asymmetric error-offset columns, which are additional columns under the current importer design.

Recommend the smallest justified change. Do not weaken validation for every input format without establishing that the broader behavior is intended.

## 3. Define missing-value and provenance behavior

Inspect the existing handling of blank cells and warnings.

- Specify the expected representation of blank archive cells, consistent with existing importer behavior.
- Preserve all 21 archive columns and their values without inventing replacements for blank cells.
- Do not store citation/author data in `warnings` merely to make it available.
- Determine whether an existing provenance mechanism can be used. If none exists, propose a minimal approach that preserves source metadata without changing the `SpectrumData` contract in this burst.
- Do not infer physical units solely from column names. Identify what authoritative evidence would be required before setting unit fields.

## 4. Revise the test plan

Inspect `tests/test_csv_importer.py` and propose focused regression tests that cover:

- Existing generic CSV imports still working.
- Successful import of the archive's actual header structure.
- Correct identification of the primary axis and signal for downstream plotting.
- Preservation of all 21 source fields and representative values.
- Signed archive error offsets.
- Blank optional archive fields.
- Existing missing-value and malformed-input behavior remaining intact.

Use a small fixture derived directly from the actual archive, including representative signed errors and blank fields. State exactly what the fixture can and cannot establish.

Do not create or edit the fixture during PLAN mode.

## 5. Bound the first burst

Keep the first burst limited to the minimum importer change and associated tests. Do not add automated retrieval, generalized unit inference, additional archive formats, database changes, or model redesign.

Identify the exact files expected to change and justify each one. Do not include documentation edits unless an existing project decision or documented requirement makes them necessary for this burst.

## 6. Required response

Return:

1. Findings verified against the current code and tests.
2. The header-mapping decision and its trade-offs.
3. The revised implementation plan with exact files and changes.
4. Test cases and acceptance criteria.
5. Remaining uncertainties or blockers.
6. A clear statement that no files were modified and no tests were run in PLAN mode.

Do not request ACT approval as if the revised plan were already accepted. Stop after presenting the revised plan for review.

## 4. What happens after v6

Once Cline returns its revised plan, send it here. I will review it against the outstanding issues and decide whether it is ready for a narrowly scoped ACT prompt or needs another targeted correction.

For now, v5 is not approved, but Chunk 4 does not need to be restarted. The basic approach remains viable; the header-mapping contract and uncertainty semantics need to be settled before implementation.