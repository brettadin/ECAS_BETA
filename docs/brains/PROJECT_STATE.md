# ECAS - Project State Document

**Last Updated:** 2026-10-22  
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

### ⏳ visualization/spectra_plot.py - IN PROGRESS (Chunk 3)

**Location:** `ecas/visualization/spectra_plot.py`

**Role:**
- Receives normalized `SpectrumData`.
- Uses PyQtGraph to display spectral coordinates.
- Is intended to replace the previous plotted dataset when a new one loads.

**Verification requirements:**
- Axis labels use only available column names and explicitly supplied units.
- Missing, non-numeric, and non-finite values are handled correctly.
- Failed loads clear both visible and internal state.
- The original measurement rows, columns, and metadata remain unchanged.
- Automated tests verify actual plotted coordinates and failure behavior.
- Application integration and manual verification are tracked separately.

**Current limitation:** The plotting component exists, but its integration
with the main application must be verified and completed before Chunk 3
can be considered complete.

### ⏳ Other Components - IN PROGRESS

- **Main window UI:** Desktop shell, navigation, CSV import, and measurement table exist. The plotting widget must be integrated into the Spectral Data page and verified.
- **Scientific comparison algorithm:** Not yet defined or implemented (future work)
- **Online archive integration:** Chunk 4 deferred for later implementation

---

## Known Issues / TODOs

### Persistence (Chunk 2):
- Comprehensive change-history/provenance tracking remains a future design decision.

### Visualization (Chunk 3)
- [ ] Integrate the plotting widget with the main window and CSV import workflow.
- [ ] Verify axis units, invalid-value filtering, and failed-load state handling.
- [ ] Strengthen automated tests for plotted coordinates and data immutability.
- [ ] Perform manual application verification.
- [ ] Resolve the planned dataset-selection behavior.

---

## Testing Summary

**Previously reported passing tests:** 28 (historical result; rerun required)
- Persistence: 20 tests (`tests/test_persistence.py`)  
- Visualization: 8 tests (`tests/test_spectra_plot.py`)  

**Test Environment:**
- Python interpreter: Python 3.14.0  
- Pytest version: pytest-9.1.1  
- PyQtGraph: Installed and configured for visualization testing

---

## Next Steps

1. Complete and verify the persistence layer (Chunk 2).
2. Complete the plotting component and integrate it into the main window.
3. Verify import, plotting, and table behavior together.
4. Resolve dataset-selection requirements for Chunk 3.
5. Run targeted and full automated tests.
6. Complete manual verification and update the Chunk 3 checklist.
7. Continue to later chunks only after the current completion criteria are met.

---

## Verification Note

**Automated vs. Manual Verification:**
- Automated tests verify core functionality independently of the GUI.
- Manual verification requires running ECAS and inspecting the plot widget in action; this is separate from automated test results and will be documented once performed.
