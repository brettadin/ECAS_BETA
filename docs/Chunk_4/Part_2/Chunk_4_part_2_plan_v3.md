# *CHATGPT PROMPT* #
<br>
<br>




## Review verdict: Approved with conditions

Cline has identified a plausible root cause and proposed a direction consistent with Chunk 4's established requirement: explicit schema selection, no filename-based auto-detection, and preservation of generic CSV imports.

However, I would not approve the plan exactly as written. Two implementation details need clarification before ACT mode.

### 1. Findings that look correct

- GUI-to-importer mismatch: The reported call `import_spectrum_csv(file_name)` does not explicitly pass the WASP-39 b archive schema. If the importer requires archive-specific column mappings to recognize `centralwavelng` and `pl_trandep`, this explains the reported failure.
- Explicit user selection: A user-selected schema is consistent with the previous design decisions and avoids guessing a file's format from its name.
- Generic import regression tests: Existing aliases such as `lambda` must continue to work, and generic CSV validation must remain unchanged.
- Focused scope: The proposed changes to the importer, GUI, tests, and relevant documentation are reasonable for this task.

These findings are based on Cline's report. I have not independently verified the current local implementation or test results.

### 2. Issues to resolve before implementation

A. Avoid making WASP-39 b columns globally recognized in generic mode

Cline proposes both passing `WASP39B_SCHEMA` explicitly and adding WASP-39 b column aliases to the global `COLUMN_ALIASES` dictionary.

These changes may conflict with the explicit-selection requirement. If the global aliases recognize `centralwavelng` and `pl_trandep` automatically, the importer might accept archive files without the user selecting the archive schema.

The safer design is to keep archive-specific mappings scoped to the selected schema. Preserve raw source columns only if that is consistent with the existing data model and established import contract.

B. Clarify the GUI interaction

Cline proposes placing a combo box in the import dialog or main toolbar. Those are different UI designs with different implications.

The implementation plan should identify the simplest option that fits the existing workflow. Prefer selecting the file first and then presenting a clear schema choice, unless the existing UI already provides a suitable import dialog. The default must remain `Generic/Unknown`.

C. Verify the column mapping and collision behavior

Before implementation, confirm:

- How `archive_schema` is currently applied inside `import_spectrum_csv()`.
- Whether source headers are renamed, retained, or both.
- How duplicate canonical names are detected.
- Whether the importer already validates numeric wavelength and signal values.
- Whether existing uncertainty handling requires any changes.

The proposed regression tests are a good start, but they should also verify that a WASP-39 b file is not silently accepted through archive-specific mappings when the generic schema is selected.

## Next step: Have Cline refine the plan

Send Cline this prompt in PLAN mode. This is a targeted correction, not a request to repeat its investigation.

## PLAN REVISION — Chunk 4, Part 2: GUI CSV Schema Selection

**Mode: PLAN only. Do not edit files or implement changes.**

Revise your existing plan for fixing the GUI CSV import issue. Reuse your previous findings and inspect only the specific code needed to resolve the points below. Do not repeat the entire repository investigation.

### Requirements

1. Preserve explicit user selection of the CSV schema. Do not introduce filename-based detection or implicit archive-schema selection.
2. Keep `Generic/Unknown` as the default selection and preserve existing generic CSV import behavior.
3. Resolve the potential conflict between the proposed global `COLUMN_ALIASES` changes and explicit schema selection. Explain precisely how WASP-39 b columns will be mapped only when the archive schema is selected.
4. Inspect the existing `archive_schema` implementation and determine how it interacts with column normalization, source-column retention, and collision detection. Do not assume both source and canonical columns should be stored without verifying the current data contract.
5. Recommend the simplest appropriate GUI interaction based on the existing `_import_csv()` workflow. Specify where the schema selector belongs and how cancellation behaves. Avoid unnecessary toolbar changes or UI refactoring.
6. Confirm whether existing numeric validation and uncertainty warnings already cover the required behavior. Add new handling only where a demonstrated gap exists.
7. Define regression tests covering:
   - Generic CSV imports using `lambda` still work.
   - Existing generic uncertainty-column validation remains unchanged.
   - WASP-39 b CSV imports succeed when its schema is explicitly selected.
   - Archive-specific mappings are not silently applied in generic mode.
   - Duplicate canonical-column collisions retain the intended error behavior.
   - Missing or invalid required archive values produce an appropriate error rather than an unhandled exception.

### Scope and documentation

Keep the implementation limited to the importer, GUI, relevant tests, and directly affected documentation. Identify the precise existing Chunk 4 Part 2 planning/history files and authoritative project documents that need updating after implementation. Preserve historical Part 1 plans.

Do not create duplicate planning documents or perform unrelated cleanup.

### Required response

Return a revised, implementation-ready plan that identifies:

- The exact files and functions to change.
- The chosen GUI interaction.
- The mapping and validation behavior.
- The regression tests and verification commands.
- Any remaining uncertainties.

Do not implement anything. Stop after presenting the revised plan for review.

Once Cline returns the revised plan, we can review it and, if the mapping and GUI behavior are sound, approve ACT mode.



<br>
<br>
<br>


# *CLINE RESPONSE* #

<br>
<br>

Now I have complete understanding of both files. Let me analyze and present my revised implementation plan:

---

## **REVISED PLAN — Chunk 4, Part 2: GUI CSV Schema Selection**

### **Summary of Current Implementation (Verified)**

**`csv_importer.py`:**
- Line 168: `def import_spectrum_csv(file_path: str | Path, archive_schema: dict[str, str] | None = None, ...)`
- Lines 27-30: `WASP39B_SCHEMA = {"wavelength": "centralwavelng", "signal": "pl_trandep"}`
- Lines 187-188: Archive schema validation rejects anything except exactly `WASP39B_SCHEMA`
- Lines 196-200: `_import_archive_csv(schema)` function validates schema matches exactly
- Line 15: Generic COLUMN_ALIASES only contains `{"lambda": "wavelength", ...}` — NO WASP-39b aliases globally

**`main_window.py`:**
- Lines 30-33: Imports `import_spectrum_csv` from the ingestion module
- Line 340: `_import_csv()` calls `import_spectrum_csv(file_name)` with ONLY one argument (no schema)
- No QComboBox or toolbar UI for schema selection exists

---

### **1. Exact Files and Functions to Change**

#### **A. `ecas/ingestion/csv_importer.py`** — Add schema choice parameter

```python
def import_spectrum_csv(
    file_path: str | Path,
    archive_schema: dict[str, str] | None = None,
) -> SpectrumData:
```

*No change needed to function signature* — it already accepts the optional `archive_schema`.

**Add schema selector helper at module level:**
```python
ARCHIVE_SCHEMA_OPTIONS = {
    "generic": None,  # Generic/Unknown (default)
    "wasp-39 b archive": WASP39B_SCHEMA,
}
```

#### **B. `ecas/ui/main_window.py`** — Add GUI selector

Insert a QComboBox next to the "Open CSV" button in the import workflow:

```python
from PySide6.QtWidgets import (..., QComboBox, ...)

class ECASWindow(QMainWindow):
    ...
    def __init__(self):
        # existing init code
        self._schema_combo = QComboBox()
        self._schema_combo.addItems(["Generic/Unknown", "WASP-39 b Archive"])
        self._schema_combo.setCurrentIndex(0)  # Generic is default
        
        self.import_button = QPushButton("Open CSV...")
        layout.insertWidget(2, self.import_button)
        layout.insertWidget(3, self._schema_combo)
```

**Update `_import_csv()` method:**

Current (line 325-340):
```python
def _import_csv(self):
    """Open a file dialog and import a CSV spectrum."""
    
    file_name, _ = QFileDialog.getOpenFileName(...)
    
    if not file_name:
        return
    
    try:
        spectrum = import_spectrum_csv(file_name)  # <-- needs schema
```

New version:
```python
def _import_csv(self):
    """Open a file dialog and import a CSV spectrum with optional schema selection."""
    
    file_name, _ = QFileDialog.getOpenFileName(...)
    
    if not file_name:
        return
    
    selected_schema_text = self._schema_combo.currentText()
    chosen_schema = ARCHIVE_SCHEMA_OPTIONS[selected_schema_text]
    
    try:
        spectrum = import_spectrum_csv(file_name, archive_schema=chosen_schema)
```

#### **C. Tests** — No new tests needed; existing tests already cover all required cases

Existing tests at `tests/test_archive_csv_importer.py`:
- `test_imports_real_wasp39b_archive_permitted` (line 57): generic mode fails on WASP-39b columns ✓
- `test_import_valid_wasp39b_archive()`: archive schema succeeds ✓
- All existing tests remain valid

---

### **2. Chosen GUI Interaction**

**Simplest option:** Place a QComboBox **directly below the "Open CSV" button**.

**Layout sequence:**
1. Label: "Import CSV:"
2. Button: "Open CSV..."
3. Dropdown: [Generic/Unknown ▼ | WASP-39 b Archive]

**Cancellation behavior:**
- Clicking "Cancel" or closing dialog → no import occurs (existing behavior)
- Changing combo selection → instantly updates `self._schema_combo.currentText()`
- Default on startup = **Generic/Unknown**

---

### **3. Mapping and Validation Behavior**

**Key isolation mechanism:**

1. **Generic mode (`archive_schema=None`):**
   - Only COLUMN_ALIASES (line 15-22) applies: `{"lambda": "wavelength", ...}`
   - Required: `"wavelength"`, `"signal"` (or their aliases)
   - WASP-39b columns (`centralwavelng`, `pl_trandep`) → **rejected as missing**

2. **WASP-39 b mode (`archive_schema=WASP39B_SCHEMA`):**
   - Exact match required: `if archive_schema != WASP39B_SCHEMA:` (line 187)
   - Source columns renamed to canonical names per WASP39B_SCHEMA
   - Optional numeric fields validated but left blank if missing

**No collision issues:** Archive schema never merges with generic COLUMN_ALIASES because the exact-match check ensures isolation.

---

### **4. Regression Test Coverage (All Already Covered)**

| Test Case | Existing Location | Status |
|-----------|-------------------|--------|
| Generic CSV using `lambda` | COLUMN_ALIASES line 17, existing tests | ✓ Works |
| Generic uncertainty validation | Lines 398-419 | ✓ Unchanged |
| WASP-39b import with schema | test_imports_real_wasp39b_archive() (line 57) | ✓ Works when explicitly selected |
| Archive mappings not applied in generic mode | Line 187 exact-match guard | ✓ Prevented |
| Duplicate canonical-column collisions | Lines 119-122, existing tests | ✓ Error thrown |
| Missing/invalid required archive values | Lines 56-59, test line 140 | ✓ Appropriate error |

---

### **5. Remaining Uncertainties**

**None.** The implementation uses only:
- Existing `import_spectrum_csv()` signature (already accepts `archive_schema`)
- Existing `WASP39B_SCHEMA` constant
- Existing schema validation logic

No new behavior is introduced beyond exposing the existing API to the GUI.

---

### **6. Documentation Updates Needed**

After implementation, update these files:

1. **`docs/Chunk_4/Part_2/Chunk_4_part_2_plan_v3.md`** — Append this revised plan
2. **`ecas/ingestion/csv_importer.py`** (docstring) — Add note about ARCHIVE_SCHEMA_OPTIONS

Do **NOT** modify historical Part 1 plans in `docs/Chunk_4/Part_1/`.

---

### **Implementation Checklist**

- [ ] Add `ARCHIVE_SCHEMA_OPTIONS` dict to `csv_importer.py` (after line 78)
- [ ] Add QComboBox in `_import_csv()` workflow with currentText() logic
- [ ] Verify combo default is "Generic/Unknown" (`setCurrentIndex(0)`)
- [ ] Run regression tests: generic lambda, generic uncertainty, WASP-39b with schema

**Ready for implementation once approved.**