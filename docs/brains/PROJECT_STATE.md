# ECAS - Project State Document

**Last Updated:** 2026-10-27
**Version:** 1.0 (Beta)

---

## Repository Structure

```
ECAS_BETA/
├── ecas/
│   ├── __init__.py
│   ├── models/
│   │   ├── spectrum.py         # SpectrumData model (frozen dataclass)
│   │   └── __init__.py
│   ├── persistence.py          # SQLite storage layer (COMPLETE)
│   ├── visualization/           # Spectral visualization component
│   │   └── spectra_plot.py      # PyQtGraph spectrum plot widget
│   └── ...
├── docs/
│   └── brains/
│       ├── DECISIONS.md        # Design decisions
│       └── PROJECT_STATE.md    # This file
├── tests/                      # Test directory (complete test coverage for persistence and visualization)
│   ├── test_persistence.py     # Persistence tests (20 passing tests)
│   └── test_spectra_plot.py    # Visualization tests (8 passing tests)
├── README.md
└── ...
```
---

### CSV Import Manager and GUI Integration
10-27-2026
**Status: Implemented and verified by automated tests; manual GUI verification partially completed.**

- Added `ecas/ingestion/import_manager.py` as a format-selection entry point for spectrum imports.
- The import manager currently supports CSV files and delegates CSV parsing and validation to `ecas/ingestion/csv_importer.py`.
- Unsupported extensions, including files without an extension, are rejected with a clear `SpectrumImportError`.
- Updated `ecas/ui/main_window.py` to route CSV imports through the import manager while preserving the existing generic and WASP-39 b archive schema selection.
- Added `tests/test_import_manager.py` covering unsupported formats, extensionless files, generic CSV imports, and forwarding of the WASP-39 b archive schema.

**Automated verification:** The full test suite passed: `150 passed in 3.25s`.

**Manual GUI verification:**
- The WASP-39 b archive CSV imported successfully when `WASP-39 b Archive` was selected.
- The GUI displayed all 331 rows and plotted `centralwavelng` on the X-axis and `pl_trandep` on the Y-axis.
- `wasp39b_test.csv` also imported successfully using the archive schema.
- Other CSV files may fail if they do not match the selected import schema or contain recognizable generic measurement columns.

**Current limitations:**
- The archive importer requires its expected 21-column source schema.
- Generic CSV imports still require recognizable wavelength and signal columns; arbitrary column mapping is not implemented.
- Text-based spectrum imports are not implemented.
- Successful import of the tested archive dataset does not establish compatibility with all archive CSV variants.

**Deferred work:** Plan and implement user-selectable X/Y column mapping for generic CSV imports. Consider text-based import support in a separate, later increment.

---

## Component Status

### ✅ persistence.py - COMPLETE (Chunk 2)

**Functions Implemented:**
| Function | Description | Status |
|----------|-------------|--------|
| `validate_project_id()` | Sanitizes project ID, prevents path traversal | ✅ |
| `get_project_database()` | Gets path to project's SQLite DB | ✅ |
| `_get_connection()` | Opens/creates SQLite connection | ✅ |
| `_initialize_schema()` | Creates spectra table if needed | ✅ |
| `_to_spectrums_dict()` | Deserializes dict back to SpectrumData | ✅ |
| `save_spectrum_to_database()` | Saves spectrum to project DB | ✅ |
| `load_spectra_from_database()` | Loads all spectra for project | ✅ |
| `load_spectrum_by_index()` | Loads specific spectrum by index | ✅ |
| `clear_project_database()` | Empties project's spectra table | ✅ |
| `count_spectra()` | Counts spectra in project DB | ✅ |

**Storage Format:**
- Each spectrum stored as JSON in TEXT column (via SQLite BLOB/TEXT)
- JSON structure:
  ```json
  {
    "source_file": "/path/to/file",
    "rows": [[1.2, 2.3], [3.4, 4.5]],
    "columns": ["frequency", "intensity"],
    "axis_unit": "Hz",
    "signal_unit": "arbitrary units",
    "signal_type": "NMR",
    "warnings": []
  }
  }
  ```

### ✅ models/spectrum.py - COMPLETE (Chunk 1)

**Class:** `SpectrumData`  
**Attributes:**
- `source_file`: Path to original spectrum file
- `rows`: Tuple of tuples (spectral data matrix, frozen at creation)
- `columns`: Tuple of column names
- `axis_unit`: X-axis unit (e.g., "Hz", may be None)
- `signal_unit`: Y-axis unit (e.g., "arbitrary units", may be None)
- `signal_type`: Signal type (e.g., "NMR", may be None)
- `warnings`: Empty tuple or tuple of warning messages from import

### ✅ visualization/spectra_plot.py - COMPLETE (Chunk 3)

**Location:** `ecas/visualization/spectra_plot.py`

**Role:**
- Receives normalized `SpectrumData`.
- Uses PyQtGraph to display spectral coordinates.
- Is intended to replace the previous plotted dataset when a new one loads.

**Verification results:**
- Automated tests: All plotting tests passed (`tests/test_spectra_plot.py`).
- Full application test suite: **40/40 passing**.
- Manual verification: Application launched successfully; `test_spectrum` imported and displayed with correct plotting.

Current limitation: The generic CSV importer and the explicitly supported WASP-39b archive schema cover the currently implemented CSV paths. Other custom-formatted CSV schemas and research files in TXT or other formats are not necessarily supported. Broader import flexibility and unit selection remain future work. 10-23-2026

**Future work (unchanged):** 
- Additional archive ingestion and online reference-spectrum retrieval (Chunk 4; remaining scope) (10-23-26)
- Spectrum comparison workflow and scientific analysis features (Chunks 5-7)

### ✅ models/spectrum.py - COMPLETE (Chunk 1)

---

### ✅ ingestion/csv_importer.py — ARCHIVE CSV SUPPORT IMPLEMENTED (Chunk 4, current scope)

**Location:** `ecas/ingestion/csv_importer.py`

**Implemented capability:**
- Supports the explicitly configured WASP-39b archive CSV schema.
- Maps `centralwavelng` to canonical `wavelength`.
- Maps `pl_trandep` to canonical `signal`.
- Retains the original source columns and appends the two canonical columns.
- Preserves existing generic CSV import behavior when no archive schema is supplied.
- Rejects unsupported explicitly supplied archive schemas rather than silently using the generic importer.

**Real-data verification:**
- Source: `data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`
- Imported rows: 331
- Imported columns: 23 (21 source columns plus 2 canonical columns)

**Automated verification reported:**
- Archive importer tests: 105 passed.
- Full test suite: 145 passed.

These results reflect the reported test run for the current implementation. Rerun tests after subsequent code changes.

**Scope limitation:** This is support for one identified archive schema, not universal archive CSV compatibility. General online archive retrieval, additional archive schemas, TXT import, and broader unit-handling behavior are not established by this implementation.

---


## Known Issues / TODOs

### Persistence (Chunk 2):
- Comprehensive change-history/provenance tracking remains a future design decision.

### Visualization (Chunk 3) - Completed
- ✅ All automated plotting tests passed.
- ✅ Application launched and `test_spectrum` imported/plotting verified manually.
- ⏳ Dataset-selection behavior deferred per project plan; not implemented in current codebase.

### Testing:
- Full test suite: **40/40 passing** (user-reported result as of 2026-10-22).
---

## Testing Summary

**Latest reported full test suite:** 145 passed.

- Archive CSV importer: 105 tests passed (`tests/test_archive_csv_importer.py`).
- The full suite includes the existing persistence and visualization tests, as well as the new archive importer tests.

**Test Environment:**
- Python interpreter: Python 3.14.0
- Pytest version: pytest-9.1.1

These results describe the reported run and should be refreshed after subsequent code changes.

(10-23-2026)

---

## Next Steps

1. Complete and verify the persistence layer (Chunk 2) — **done**.
2. Complete the plotting component and integrate it into the main window (Chunk 3) — **verified and complete**.
3. Run targeted and full automated tests — **passed (40/40)**.
4. Continue to later chunks only after the current completion criteria are met.

Future work includes:
- Dataset-selection behavior for multiple saved spectra (deferred).
- Online reference-spectrum retrieval from archives (Chunk 4).
- Spectrum comparison workflow and scientific analysis features (Chunks 5-7).

---

## Verification Note

**Automated vs. Manual Verification:**
- Automated tests verify core functionality independently of the GUI.
- Manual verification requires running ECAS and inspecting the plot widget in action; this is separate from automated test results and will be documented once performed.
