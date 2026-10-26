# *CHATGPT PROMPT* #
<br>
<br>

## Review verdict: Not approved yet — one significant design flaw remains

The plan is close to implementation-ready, but the proposed GUI selector is not wired correctly. We should fix that before approving ACT mode.

### 1. Confirmed design flaw: selector lifetime and state

Cline proposes creating `schema_selector` inside `_import_csv()`, after the file dialog opens, while also proposing to add that selector to the persistent spectral page layout in `_build_spectral_page()`.

Those two approaches are incompatible as written:

- `_build_spectral_page()` constructs the persistent GUI layout.
- `_import_csv()` runs when the user clicks the import button.
- A selector created inside `_import_csv()` does not exist when `_build_spectral_page()` constructs the layout.
- The proposed `_current_schema_index` state can become stale because the code reads the index separately from the widget and introduces unnecessary signal handling.

Required correction: Create the schema selector and its label in `_build_spectral_page()`, retain the selector as an instance attribute, and read its current index directly inside `_import_csv()` immediately before calling the importer.

The intended mapping is straightforward:

```
archive_schema = (    WASP39B_SCHEMA    if self.spectrum_schema_selector.currentIndex() == 1    else None)
```

This is illustrative guidance, not an instruction to implement the code manually.

### 2. Test coverage needs one correction

The existing archive-importer tests cover importer behavior, but they do not prove the GUI passes the selected schema correctly. Cline has acknowledged this gap.

A focused automated GUI test that mocks `import_spectrum_csv()` would be preferable. It should verify both selections:

- Index `0` passes `archive_schema=None`.
- Index `1` passes `archive_schema=WASP39B_SCHEMA`.

If the existing GUI test infrastructure makes this disproportionately difficult, manual verification is acceptable, but the implementation report must distinguish manual verification from automated test coverage.

### 3. Documentation must reflect verified results

Cline's proposed documentation text prematurely states that implementation is complete and tests are passing. Those statements must only be added after implementation and verification actually succeed.

The proposed active plan, `Chunk_4_part_2_plan_v4.md`, should be checked in the local repository before editing. Update the appropriate existing planning record and authoritative project-state documentation only as warranted by the verified changes.

## Next action

Send Cline this short correction in PLAN mode:

## FINAL CORRECTION — GUI Schema Selector Lifecycle

**Mode: PLAN only. No file edits.**

Your plan currently creates `schema_selector` inside `_import_csv()` but also proposes inserting it into the persistent layout in `_build_spectral_page()`. These operations cannot work together as written.

Revise the plan with these requirements:

1. Create the schema label and QComboBox in `_build_spectral_page()`, alongside the existing import controls.
2. Store the combo box as an instance attribute, such as `self.spectrum_schema_selector`, so it persists across import attempts.
3. In `_import_csv()`, read `self.spectrum_schema_selector.currentIndex()` immediately before calling `import_spectrum_csv()`. Map index 0 to `None` and index 1 to `WASP39B_SCHEMA`. Remove the unnecessary signal handler and `_current_schema_index` state.
4. Add a focused GUI test that mocks the importer and verifies both schema selections are passed correctly, if compatible with the existing test infrastructure. Otherwise, specify a concrete manual verification procedure.
5. Verify the actual existing layout and test structure rather than relying on assumed widget positions or test paths.
6. Keep documentation updates conditional on the implementation and tests actually completing successfully.

Return only the corrected implementation plan. Do not implement anything.

Once that lifecycle correction is accepted, the task should be ready for ACT mode.

<br>
<br>
<br>


# *CLINE RESPONSE* #

<br>
<br>

## CORRECTED IMPLEMENTATION PLAN — GUI Schema Selector Lifecycle

### 1. **Widget Creation Location: `_build_spectral_page()`**

Create both the label and QComboBox as instance attributes in `_build_spectral_page()`:

```python
def _build_spectral_page(self):
    # ... existing layout code ...
    
    # NEW: Schema selector widgets (persistent, not recreated on each import)
    schema_label = QLabel("CSV schema:")
    schema_selector = QComboBox()
    schema_selector.addItems(["Generic / Unknown", "WASP-39 b Archive"])
    schema_selector.setCurrentIndex(0)  # Default to Generic
    
    self.spectrum_schema_selector = schema_selector  # Store as instance attribute
    self.spectrum_schema_label = schema_label
```

**Verify existing layout structure** (before inserting):
- Read lines around where the "Import CSV" button is defined in `_build_spectral_page()`
- Identify if using `QVBoxLayout` or `QHBoxLayout` to insert widgets at correct index

### 2. **Widget Usage Location: `_import_csv()`**

Read the current index directly from the stored instance attribute:

```python
def _import_csv(self):
    file_name, _ = QFileDialog.getOpenFileName(...)
    
    if not file_name:
        return
    
    # NEW: Read selection immediately before import call
    schema_map = {
        0: None,
        1: WASP39B_SCHEMA,
    }
    archive_schema = schema_map[self.spectrum_schema_selector.currentIndex()]
    
    spectrum = import_spectrum_csv(file_name, archive_schema=archive_schema)
    # ... rest of method unchanged ...
```

**Remove from plan:**
- Unnecessary signal handler (`currentIndexChanged.connect`)
- Separate `_current_schema_index` state variable

### 3. **GUI Test Strategy: Mock-Based Automated Test**

Add test to verify GUI passes correct schema (compatible with existing pytest infrastructure):

```python
# tests/gui_tests/test_schema_selection.py (new file or append)
import pytest
from unittest.mock import patch, MagicMock

def test_gui_generic_schema_select_passed_as_none(qtbot):
    """Verify index 0 passes archive_schema=None"""
    from ecas.ui.main_window import ECASWindow
    
    window = ECASWindow()
    
    # Ensure combo exists and is at default
    assert window.spectrum_schema_selector.currentIndex() == 0
    
    with patch('ecas.ui.main_window.import_spectrum_csv') as mock_import:
        mock_import.return_value = MagicMock(row_count=1, columns=(), rows=[{}], warnings=[], source_file=MagicMock(name="test"))
        
        # Force generic selection by directly manipulating combo before calling import
        window.spectrum_schema_selector.setCurrentIndex(0)
        
        # Trigger _import_csv (or mock it differently to capture call args)
        # ... implementation dependent on exact test approach ...
```

**If GUI test infrastructure is too complex**, fall back to:
```python
def test_gui_archive_schema_select_passed_correctly(qtbot):
    """Verify index 1 passes WASP39B_SCHEMA"""
    from ecas.ui.main_window import ECASWindow
    from ecas.ingestion.csv_importer import WASP39B_SCHEMA
    
    window = ECASWindow()
    
    # Capture the argument that will be passed (via side_effect)
    called_args = {}
    def capture_call(*args, **kwargs):
        called_args['archive_schema'] = kwargs.get('archive_schema')
        return MagicMock(row_count=1, columns=(), rows=[{}], warnings=[], source_file=MagicMock(name="test"))
    
    with patch('ecas.ui.main_window.import_spectrum_csv', side_effect=capture_call):
        window.spectrum_schema_selector.setCurrentIndex(1)  # Select Archive
        # Call the import function (or simulate file selection)
        # ... verify called_args['archive_schema'] == WASP39B_SCHEMA ...
```

**Manual verification fallback:**
```bash
# Manual steps documented if automated test proves too complex:
# 1. Launch ECAS GUI
# 2. Navigate to Spectral Data page  
# 3. Change dropdown from "Generic / Unknown" to "WASP-39 b Archive"
# 4. Import data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv
# 5. Verify ~331 rows imported successfully (confirms archive mode active)
# 6. Reset dropdown and attempt same import—should fail with generic mode
```

### 4. **Layout Verification Commands**

Before implementing, verify actual layout in `_build_spectral_page()`:

```bash
# Inspect widget positions before insertion
Get-Content "c:\Users\brett\AIProjects\ECAS_BETA\ecas\ui\main_window.py" | Select-Object -Index 200..280
```

Look for:
- `QVBoxLayout` or `QHBoxLayout` instance where widgets are added
- Existing button/widget indices to determine insertion point (before import button)

### 5. **Documentation Update Strategy**

Update `docs/Chunk_4/Part_2/Chunk_4_part_2_plan_v4.md` ONLY after:
1. Implementation changes successfully applied to `main_window.py`
2. GUI test passes OR manual verification procedure confirmed working
3. Documentation includes actual results, not premature assertions

**Documentation template (fill only verified items):**

```markdown
## Implementation Completed

### Files Modified
- `ecas/ui/main_window.py`: Added schema selector in `_build_spectral_page()`; updated `_import_csv()` to read `self.spectrum_schema_selector.currentIndex()`

### Test Coverage
- Automated GUI test added to `tests/gui_tests/test_schema_selection.py` (or manual procedure documented if automation not feasible)
- All existing archive importer tests remain passing

### Data Contract
| UI Selection | Passed Value | Behavior |
|-------------|---------------|----------|
| Generic / Unknown | `None` | Generic CSV parsing; fails on WASP-39b columns |
| WASP-39 b Archive | `WASP39B_SCHEMA` | Maps archive columns; validates WASP-39b fields |

### Manual Verification Steps (if automated test not used)
[Insert numbered steps for manual testing]
```

---

## Summary of Corrections Made

| Original Issue | Correction Applied |
|----------------|-------------------|
| Selector created in `_import_csv()` AND layout insertion in `_build_spectral_page()` | Selector created ONLY in `_build_spectral_page()`, stored as `self.spectrum_schema_selector` |
| Unnecessary signal handler and `_current_schema_index` state | Removed; read index directly from attribute |
| Unclear test coverage strategy | Focused mock-based GUI test defined with fallback to manual verification |
| Premature documentation completion claims | Documentation updates now conditional on verified results |

**Ready for ACT mode once approved.**