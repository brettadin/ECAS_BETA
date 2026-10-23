# ECAS - Design Decisions Log

## Project Overview
ECAS is a spectrum analysis application that stores, retrieves, and processes spectral data from NMR experiments. The system uses SQLite for persistent storage of spectrum data organized by project.

---


## Decision: WASP-39b Archive CSV Import Schema

**Date:** 2026-10-23
**Status:** Implemented and tested

### Context
Chunk 4 requires ECAS to ingest a real archive dataset whose CSV column names differ from the application's canonical spectrum coordinate and signal names.

### Decision
The CSV importer supports an explicit WASP-39b archive schema that maps source columns to canonical fields:

- `centralwavelng` → `wavelength`
- `pl_trandep` → `signal`

The schema is defined in `ecas/ingestion/csv_importer.py`. Archive-specific behavior is enabled by explicitly supplying the supported archive schema.

### Scope and Constraints
- This implementation supports the identified WASP-39b CSV schema; it does not establish general compatibility with arbitrary astronomical archive CSV files.
- When no archive schema is supplied, the existing generic CSV import behavior remains in effect.
- An explicitly supplied unsupported archive schema raises `SpectrumImportError` rather than silently falling back to generic import behavior.
- Source columns are retained, and the canonical `wavelength` and `signal` columns are appended to the imported dataset.
- The implementation validates archive CSV headers, row widths, required numeric values, optional numeric values, and metadata according to the archive importer tests.

### Verification
- The real WASP-39b source file is `data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`.
- The dataset imports 331 rows.
- The imported dataset contains 23 columns: the 21 original source columns followed by `wavelength` and `signal`.
- Automated verification reported 105 passing tests in `tests/test_archive_csv_importer.py` and 145 passing tests in the full test suite.

### Future Considerations
Additional archive schemas and file formats, including research data supplied as TXT files, require separate implementation and verification. This decision does not establish support for online archive retrieval or general-purpose scientific unit conversion.


## Decision: PyQtGraph for Spectral Visualization

**Date:** 2026-10-22
**Status:** Adopted and verified; application integration complete

### Context
ECAS needs to display imported spectral measurements for inspection.

### Decision
The current plotting component uses PyQtGraph through the PySide6 Qt
binding. The component is implemented in
`ecas/visualization/spectra_plot.py` as `SpectraPlot`, a QWidget
containing a PyQtGraph PlotWidget.

### Scope
This decision covers visualization of an imported `SpectrumData` object.
It does not select or implement a molecular matching, atmospheric inference,
or candidate-scoring algorithm.

### Implementation and Verification
The plotting component is implemented in the repository. The automated tests pass (**all tests in `tests/test_spectra_plot.py` passed**). Application integration has been verified: the application launches successfully, and manual import of `test_spectrum` displays correct plotting with proper axis labels and data integrity maintained.

### Decision: PyQtGraph
- **Rationale:**
  - Excellent support for scatter plots via `ScatterPlotItem`
  - Seamless integration with PySide6 (Qt bindings) used by ECAS
  - Lightweight and well-suited for spectrum visualization
  - No additional complex dependencies required beyond what is already installed

### Implementation Details
- Module: `ecas/visualization/spectra_plot.py`
- Widget class: `SpectraPlot` extends `QWidget` with embedded `PlotWidget`
- Uses `ScatterPlotItem` to render spectrum data points with connected markers
- Axis labels configured via `setLabel()` on bottom and left axes
- Handles missing metadata by showing column names without invented units

### Verification Status
- Automated test suite: **all tests passing** in `tests/test_spectra_plot.py`.
- Test coverage includes coordinate loading, missing values, axis labels, clearing/resetting, immutability, and repeated imports.
- All tests verified using Python 3.14.0 via pytest.

### Manual verification (Chunk 3)
- Application launched successfully.
- Import of `test_spectrum` confirmed correct plotting display.
- Axis labels show available column names without invented units.

### Scope
This decision concerns only the current plotting component in `SpectrumData` visualization. It does not extend to the scientific comparison algorithm or future visualization features like spectrum comparison overlays.

---

## Decision: SQLite BLOB Storage for Spectrum Data

**Date:** 2026-10-21  
**Status:** Implemented

### Context
The persistence layer needed to store complete `SpectrumData` objects (which can be large with arrays of spectral intensity and time data) alongside metadata in a database.

### Options Considered
1. **SQLite BLOB storage**: Store each spectrum as JSON text embedded in a single-column table using SQLite's built-in TEXT type.
2. **Separate tables per spectrum component**: Split rows/columns/time points into separate normalized tables.
3. **External file reference**: Store data in external files (HDF5/Parquet) and store only paths in SQLite.

### Decision: Option 1 - JSON Serialization to TEXT
- **Rationale:** 
  - SpectrumData objects serialize cleanly to JSON with all arrays converted to tuples/lists
  - SQLite has excellent TEXT column handling for large JSON documents
  - No external dependencies required (unlike HDF5/Parquet)
  - Single table design simplifies queries (e.g., "get all spectra for project X")
  - Original schema was designed for this (data JSON NOT NULL)

### Implementation Details
```python
data_json = json.dumps({
    "source_file": str(spectrum.source_file),
    "rows": spectrum.rows,       # array of tuples
    "columns": spectrum.columns, # tuple of values
    "axis_unit": spectrum.axis_unit,
    "signal_unit": spectrum.signal_unit,
    "signal_type": spectrum.signal_type,
    "warnings": spectrum.warnings,  # empty tuple or warning messages
})

conn.execute(
    """INSERT INTO spectra (project_id, data) VALUES (?, ?)""",
    (project_id, data_json),
)
```

---

## Decision: Connection Parameter Design

**Date:** 2026-10-21  
**Status:** Implemented as designed; `database_if_exists` parameter unused in production.

### Context
The persistence layer signature includes an optional `database_if_exists` parameter for potential future bulk-operation patterns (connection reuse). However, current implementation and all exercised paths do not utilize this parameter.

### Current Implementation
- Function accepts optional fourth argument: `database_if_exists: Optional[sqlite3.Connection] = None`
- All existing callers invoke with 3 arguments only, using default `None`
- When `database_if_exists=None`: Function opens its own connection via `_get_connection()`
- When `database_if_exists` provided (never exercised): Connection is reused for the save operation
- **Commit behavior:** Function commits after each INSERT regardless of connection source

### Current Production Usage Pattern
```python
# All existing callers use this pattern:
save_spectrum_to_database(spectrum, project_id, projects_dir)
# → No 4th argument; default None path taken; function manages connection lifecycle
```

### Important Clarifications
- The presence of `database_if_exists` does **not** establish a supported or tested bulk-transaction workflow
- Connection reuse pattern (opening one connection for multiple operations) has not been implemented
- To achieve bulk-transaction semantics in the future, would require changes to commit behavior inside `save_spectrum_to_database()`
- Current function always commits after each save operation, maintaining self-contained transaction boundaries

### Future Considerations
Any bulk-operation or connection-pooling enhancement would be a separate API design decision requiring:
1. Commit-defer capability (to allow multiple operations before committing)
2. Documentation updates to establish new usage contract
3. Production code demonstrating the intended pattern

---

## Decision: Project ID Validation Strategy

**Date:** 2026-10-21  
**Status:** Implemented

### Rationale
Prevent path traversal attacks and filesystem issues by validating project IDs.

### Pattern
```python
PROJECT_ID_PATTERN = "^[a-zA-Z0-9][a-zA-Z0-9_-]*$"
```

### What We Reject
- Empty strings
- Paths with `/`, `\`, `..` (dot-slash sequences)
- Special characters (`<`, `>`, `|`, etc.)

---

## Decision: Database Error Handling

**Date:** 2026-10-21  
**Status:** Implemented

### Custom Exceptions
```python
class PersistenceError(Exception):     # Base exception
    pass

class InvalidProjectIdError(PersistenceError):  # Raised for bad project IDs
    pass

class DatabaseNotFoundError(PersistenceError):   # Raised when expected DB missing
    pass
```

### Error Propagation
- `save_*` functions: Raise `InvalidProjectIdError` on validation failures
- `load_*` functions: Return empty list instead of raising when DB doesn't exist
- `clear_project_database`: Raises `DatabaseNotFoundError` if DB missing (can't clear non-existent DB)

---

## Decision: Schema Initialization Strategy

**Date:** 2026-10-21  
**Status:** Implemented

### Context
SQLite allows lazy schema creation, but we want guaranteed consistency.

### Implementation
```python
def _initialize_schema(conn):
    """Create or initialize the spectrum storage schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS spectra (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL,
            data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
```

### When Schema Is Initialized
1. On first save to a new database (via `save_spectrum_to_database`)
2. Explicitly when needed by other modules

---

# Summary of Implementation

The persistence module provides:
- ✅ Save spectrum to SQLite with JSON serialization
- ✅ Load all spectra from project database  
- ✅ Load specific spectrum by index
- ✅ Clear/emptied all spectra from project
- ✅ Count spectra in project database
- ✅ Project ID validation and path traversal prevention
- ✅ Thread-safe connection management

All functions use proper error handling and resource cleanup (finally blocks).