## Progress Update — Import Manager Integration and GUI Verification

### Completed

The import manager was added and integrated into the GUI. The GUI now routes CSV imports through `ecas/ingestion/import_manager.py`, which delegates supported CSV parsing to the existing CSV importer.

Automated tests passed:

- `tests/test_import_manager.py`: 4 tests passed.
- Full test suite: 150 tests passed in 3.25 seconds.

### GUI findings

The WASP-39 b archive dataset imported successfully after selecting the `WASP-39 b Archive` option in the GUI. The application displayed 331 rows and plotted the source columns `centralwavelng` and `pl_trandep`.

The `wasp39b_test.csv` fixture also worked with the archive schema. Other CSV files produced archive-schema errors when their source-column count did not match the expected 21 columns. This is consistent with the current strict archive validation and does not, by itself, indicate a regression.

FTIR CSV files with unrecognized measurement headers continue to fail generic import validation because manual column mapping has not yet been implemented.

### Current assessment

The import manager integration is complete for the current scope. The tested archive workflow is functional when the appropriate schema is selected. Broader GUI compatibility across arbitrary CSV structures has not been established.

### Next planned increment

Plan a narrowly scoped generic CSV column-mapping feature:

1. Read and display the available CSV column headers.
2. Let the user select the X-axis and Y-axis columns when automatic identification is insufficient.
3. Validate the selected columns and numeric data before plotting.
4. Preserve source headers and measurements.
5. Preserve the existing generic-import and WASP-39 b archive workflows.
6. Add focused tests and rerun the full suite.

Text-based imports remain deferred to a later increment. No text parser or universal file-format support should be implied by the import-manager implementation.
