# ECAS - Design Decisions Log

## Project Overview
ECAS is a spectrum analysis application that stores, retrieves, and processes spectral data from NMR experiments. The system uses SQLite for persistent storage of spectrum data organized by project.

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