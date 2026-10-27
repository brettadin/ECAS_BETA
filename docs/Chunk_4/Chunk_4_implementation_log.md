## CSV Import Manager and GUI Integration

**Date:** 2026-10-27

### Changes implemented

- Added `ecas/ingestion/import_manager.py` as a central entry point for spectrum imports.
- Added explicit CSV extension checking and clear rejection of unsupported formats.
- Kept format-specific parsing and validation in `ecas/ingestion/csv_importer.py`.
- Updated `ecas/ui/main_window.py` to call `import_spectrum()` from the import manager.
- Added `tests/test_import_manager.py` with four tests covering unsupported formats, missing extensions, generic CSV import, and archive schema forwarding.

### Automated validation

Command:

`python -m pytest -v`

Result:

`150 passed in 3.25s`

### Manual GUI verification

- Selected the WASP-39 b archive schema in the GUI.
- Successfully imported the archive CSV from `data/wasp39b`.
- Confirmed all 331 rows were displayed.
- Confirmed the plot used `centralwavelng` for the X-axis and `pl_trandep` for the Y-axis.
- Confirmed `wasp39b_test.csv` imported successfully.
- Observed schema validation errors for other test CSV files that did not contain the required 21 archive source columns.
- Observed the existing generic-import error for FTIR CSV files whose headers were not recognized as wavelength and signal columns.

### Outcome

The import manager is integrated with the GUI, and the automated regression suite passes. The tested WASP-39 b archive workflow works when the correct schema is selected.

### Outstanding work

- Implement manual X/Y column mapping for generic CSV files in a separate increment.
- Add text-based import support in a future increment.
- Retain strict archive schema validation unless a separately justified schema-variation requirement is established.

The GUI checks above were performed manually; they are not substitutes for automated GUI tests.