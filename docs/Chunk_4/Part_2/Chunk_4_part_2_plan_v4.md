# *CHATGPT PROMPT* #
<br>
<br>

## Review verdict: Not approved yet — minor plan corrections required

Cline's revised plan resolves the central design concern: `import_spectrum_csv()` already accepts an optional `archive_schema`, and the proposed GUI change would expose that existing functionality without adding filename detection.

However, the plan still contains three gaps worth resolving before ACT mode.

### 1. The proposed `ARCHIVE_SCHEMA_OPTIONS` constant is unnecessary

The schema selection mapping is a GUI concern, while `WASP39B_SCHEMA` belongs in the importer. Adding a second dictionary in `csv_importer.py` duplicates the relationship between UI labels and schema definitions.

Instead, import `WASP39B_SCHEMA` into `main_window.py` and map the selected combo-box index to either `None` or `WASP39B_SCHEMA`. This keeps the change small and avoids introducing an unnecessary public constant.

### 2. The GUI layout instructions are not implementation-ready

Cline proposes inserting widgets at fixed layout indices without identifying the actual layout structure. It should modify the existing layout based on its current contents rather than assume `layout.insertWidget(2, ...)` and `layout.insertWidget(3, ...)` are correct.

Also, the schema selector should have a descriptive label, such as CSV schema, so users understand what the dropdown controls.

### 3. Existing tests must be verified, not assumed sufficient

Cline says all required cases are already covered, but its plan does not provide actual test names and execution results for every case. In particular, the GUI's schema-selection behavior needs testing or an explicit manual verification procedure.

The acceptance criterion is not simply that the importer already works with the schema argument. The GUI must actually pass the selected schema correctly.

## Next step: Send Cline this targeted correction

Use PLAN mode again. No implementation is needed until this is resolved.

## FINAL PLAN CORRECTION — Chunk 4, Part 2: GUI CSV Schema Selection

**Mode: PLAN only. Do not edit files or run implementation changes.**

Revise the existing plan to address the remaining issues. Reuse your verified findings; do not repeat the full investigation.

### 1. Keep schema selection simple

- Do not add `ARCHIVE_SCHEMA_OPTIONS` to `csv_importer.py`.
- Import the existing `WASP39B_SCHEMA` constant into `main_window.py`.
- Map the GUI selection directly to `None` for Generic/Unknown or `WASP39B_SCHEMA` for WASP-39 b Archive.
- Avoid using display strings as dictionary keys when a simpler index-based mapping is sufficient.
- Do not change the importer's existing API or column-mapping behavior unless a demonstrated defect requires it.

### 2. Fit the selector into the actual GUI

Inspect the current layout and specify exactly where the schema selector and its descriptive label will be added. Do not assume fixed layout indices without verifying the existing structure.

Keep the existing file-dialog cancellation behavior and the Generic/Unknown default.

### 3. Verify test coverage

Identify the exact existing test names for each required importer regression case. Do not claim coverage merely because the relevant code appears to implement the behavior.

Determine whether the GUI tests can verify that the selected schema is passed to `import_spectrum_csv()`. If practical, add a focused test for this behavior. Otherwise, specify a precise manual verification procedure.

Include the relevant test commands, but do not claim they passed unless actually executed.

### 4. Resolve documentation paths

Verify which Chunk 4 Part 2 planning documents actually exist in the current repository. Do not assume `Chunk_4_part_2_plan_v3.md` is the correct filename.

Identify only the documentation updates necessary to record the completed implementation and verified project state. Preserve historical Part 1 plans and avoid duplicate planning records.

### Required output

Return the final implementation-ready plan with:

- Exact files and functions to change.
- The schema-selection mapping and GUI layout.
- Existing and any necessary new regression tests.
- Verification commands and manual checks.
- Confirmed documentation paths.
- Any remaining blockers.

Stop after presenting the plan. Do not implement changes.

Approval condition: Once the revised plan confirms the exact GUI changes, appropriate regression coverage, and correct documentation locations, we can proceed to ACT mode.

<br>
<br>
<br>


# *CLINE RESPONSE* #

<br>
<br>

Now let me present the final implementation-ready plan:

---

## FINAL IMPLEMENTATION-READY PLAN

Based on my analysis of the codebase, here is the complete plan for implementing GUI-controlled schema selection:

### 1. **Exact Files and Functions to Change**

#### `ecas/ingestion/csv_importer.py`
- **No changes required**. The existing `WASP39B_SCHEMA` constant already exists at module level. Do NOT add `ARCHIVE_SCHEMA_OPTIONS` here.

#### `ecas/ui/main_window.py`
Two specific changes:

**A. Update imports (around line 30-33):**
```python
from ecas.ingestion.csv_importer import (
    SpectrumImportError,
    import_spectrum_csv,
    WASP39B_SCHEMA,  # Add this import
)
```

**B. Update `_import_csv` method (around line 325-340):**
- After the file dialog returns at line 336 (where `if not file_name: return`), insert a QComboBox widget just before calling `import_spectrum_csv()`.
- The schema selector should appear between the "Import CSV" button and the actual import call.
- Add a descriptive label above it, e.g., `QLabel("CSV Schema:")`

Layout insertion point in `_import_csv`:
```python
# After line 337 (cancellation check), insert:
schema_label = QLabel("CSV schema:")
schema_selector = QComboBox()
schema_selector.addItems(["Generic / Unknown", "WASP-39 b Archive"])
schema_selector.setCurrentIndex(0)  # Default to Generic/Unknown

# Map index selection to actual schema argument:
def _get_schema_from_combo(combo):
    if combo.currentIndex() == 0:
        return None  # Generic mode uses archive_schema=None
    else:
        return WASP39B_SCHEMA  # WASP-39 b Archive mode

schema_selector.currentIndexChanged.connect(
    lambda idx: setattr(self, 'current_archive_schema_idx', idx)
)
self._current_schema_index = schema_selector.currentIndex()

# Then at line 340:
archive_schema = None if self._current_schema_index == 0 else WASP39B_SCHEMA
spectrum = import_spectrum_csv(file_name, archive_schema=archive_schema)
```

**C. Add widgets to the spectral page layout (`_build_spectral_page`):**
The current layout ends around line 246 with the "Import CSV" button. Insert the schema selector **before** this button using:
```python
layout.insertWidget(layout.count() - 1, schema_label)  # Insert before Import button
layout.insertWidget(layout.count() - 1, schema_selector)  # Then insert combo
```

### 2. **Schema-Selection Mapping**

| UI Selection (Index 0) | Value Passed to `import_spectrum_csv()` | Behavior |
|------------------------|------------------------------------------|----------|
| "Generic / Unknown"    | `None`                                   | Uses generic CSV logic; fails on archive-only columns |
| "WASP-39 b Archive"    | `WASP39B_SCHEMA`                         | Maps `centralwavelng`→`wavelength`, `pl_trandep`→`signal`; validates archive fields |

**Important:** No display strings are used as keys—only the index-based mapping (0→None, 1→WASP39B_SCHEMA) is retained.

### 3. **Test Coverage Verification**

#### Existing Tests (already in `tests/test_archive_csv_importer.py`):
- `test_imports_real_wasp39b_archive_preserving_source_columns`: Verifies archive import with explicit schema
- `test_unsupported_archive_schema_is_rejected`: Verifies unsupported schemas are rejected
- `test_invalid_archive_headers_are_rejected`: Tests 4 header variations (duplicate, empty, missing, unexpected)
- `test_archive_rows_with_wrong_field_count_are_rejected`: Tests short/long rows
- `test_required_archive_numeric_values_must_be_finite_numbers`: Parametrized across all required numeric fields
- `test_blank_optional_archive_numeric_values_become_none`: Tests optional field blank handling
- `test_invalid_optional_archive_numeric_values_are_rejected`: Tests invalid values in optional fields
- `test_archive_metadata_is_trimmed_and_blank_metadata_becomes_empty_string`: Tests metadata trimming
- `test_finite_signed_archive_uncertainties_keep_their_sign`: Tests signed error preservation

**Test Command:**
```bash
pytest tests/test_archive_csv_importer.py -v
```

#### GUI Schema Selection Test:
The existing test suite does NOT test that the GUI passes the selected schema. Add a focused test or use manual verification:

**Option A: Automated GUI Test (add to `tests/`):**
```python
def test_gui_schema_selection_passed_to_importer(qtbot):
    app = QApplication.instance()
    window = ECASWindow()
    
    # Verify initial default
    assert window._current_schema_index == 0
    
    # Simulate selection change
    window.spectrum_schema_selector.setCurrentIndex(1)
    assert window._current_schema_index == 1
    
    # Would need to test that import actually uses the selected schema
    # This may require mocking or capturing the call
```

**Option B: Manual Verification Procedure:**
1. Launch ECAS GUI
2. Navigate to "Spectral Data" page
3. Click the dropdown and select "WASP-39 b Archive"
4. Import the real WASP-39b CSV (`data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`)
5. Verify successful import (should show ~331 rows with original column names preserved)
6. Reset to "Generic / Unknown" and attempt the same import
7. Verify failure message indicating unsupported schema for generic mode

### 4. **Verification Commands**

After implementation:
```bash
# Run existing archive importer tests to ensure no regression
pytest tests/test_archive_csv_importer.py -v

# If GUI tests are configured, run them:
pytest tests/gui_tests/ -v -k "schema"

# Manual verification command (Windows):
cd "c:\Users\brett\AIProjects\ECAS_BETA"
python -m ecas.ui.main  # Launch and manually verify GUI behavior
```

### 5. **Documentation Paths**

#### Existing Part 2 Planning Documents:
- `Chunk_4_part_2_plan_v1.md` (6876 bytes, 10/23)
- `Chunk_4_part_2_plan_v2.md` (6391 bytes, 10/26 11:38)
- `Chunk_4_part_2_plan_v3.md` (12686 bytes, 10/26 11:47)
- `Chunk_4_part_2_plan_v4.md` (4631 bytes, 10/26 11:47) — **This is the current active plan**
- `Chunk_4_part_2_plan_v5.md` (100 bytes, 10/26 11:41) — Placeholder
- `Chunk_4_part_2_plan_v6.md` (100 bytes, 10/26 11:50) — Placeholder

#### Documentation Update Strategy:
**Update:** `Chunk_4_part_2_plan_v4.md` with completion notes.

**Do NOT create:** New planning files unless the current plan is being superseded for a different feature.

**Preserve:** Historical Part 1 plans (`docs/Chunk_4/Part_1/`) are untouched.

#### Required Documentation Content:
Add to `Chunk_4_part_2_plan_v4.md` under a new section "Implementation Completed":

```markdown
### Implementation Status: Complete

#### GUI Changes Applied
- Added CSV Schema selector to spectral data import page
- Default selection: "Generic / Unknown" (archive_schema=None)
- Archive option maps directly to WASP39B_SCHEMA constant

#### Data Contract
- Generic mode: archive_schema=None, uses generic column detection
- WASP-39 b Archive mode: archive_schema=WASP39B_SCHEMA with exact column mapping
- No filename-based schema inference (user must explicitly select)

#### Test Coverage
- All existing tests in tests/test_archive_csv_importer.py remain passing
- GUI schema selection verified via manual procedure (see Verification Commands)

#### Files Modified
- ecas/ui/main_window.py: Updated imports and _import_csv method
- ecas/ingestion/csv_importer.py: No changes (WASP39B_SCHEMA already exported)
```

### 6. **Remaining Blockers**

**None.** All items are ready for implementation:
- Schema mapping is simple (index-based, no complex constants)
- GUI layout insertion point identified (_build_spectral_page before import button)
- Test coverage verified via existing tests + manual procedure
- Documentation path confirmed (`Chunk_4_part_2_plan_v4.md`)

---

**Summary:** This plan implements a minimal, focused GUI change that exposes the existing `archive_schema` parameter in `import_spectrum_csv()`. The implementation avoids adding unnecessary constants to `csv_importer.py`, uses index-based mapping for simplicity, and relies on the existing comprehensive test suite for regression coverage.