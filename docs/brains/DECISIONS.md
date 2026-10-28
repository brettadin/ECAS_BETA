# ECAS - Design Decisions Log

## Project Overview
ECAS — Exoplanetary Characterization & Astrochemistry Suite is a scientific desktop
application for exoplanet spectroscopy. It uses SQLite for project spectrum
persistence and currently has a separate NASA raw-product/provenance cache.

## Current decision context — 2026-10-28

Workspace pages: Overview summarizes already loaded state on entry without
scanning projects/caches. Settings mirrors the existing CSV-schema selector
bidirectionally and displays configured storage paths read-only. The setting
remains session-only; no relocation, persistent preference format or new network
policy is introduced. See `../Chunk_5_1/WORKSPACE_PAGES_IMPLEMENTATION.md`.
Argon's first six feedback reviews were accepted by the user; the new workspace
increment awaits separate review and desktop acceptance.

Comparison-selection continuation: explicit observation additions copy imported
values into session choices; independently selected ExoMol cache records are
validated at discovery and selection. Inspection uses separate original-value
tables without writing projects or changing the two existing displays. The
compatibility explanation blocks the supported cross-section pairings; it does
not promote the research eligibility contract into a production service or invent
physical-model/response/noise declarations. See
`../Chunk_5_1/COMPARISON_SELECTION_IMPLEMENTATION.md`. All five earlier Argon
feedback reports were received with zero findings; Batch 6 subsequently approved
the selection snapshot with zero findings. Desktop acceptance remains separate.

The source of current implementation status is PROJECT_STATE.md; older verification
counts below describe historical checkpoints. NASA exact-name discovery, supported
transmission-table import and sidecar cache decisions are recorded in
`../Chunk_4/Chunk_4_decisions.md`. The cache is separate from project SQLite.
Current CSV output order is `wavelength`, the 21 source columns, then `signal`;
the earlier descriptions of appending both aliases do not describe current order.
Source fields and both aliases remain present. No general format/unit conversion
or scientific compatibility is implied by this ordering or by successful parsing.

Initial comparison method: compatible-observable overlay with explicit response
handling and residual inspection, with weighted diagnostics only when justified.
See `../Chunk_5/INITIAL_METHOD_DECISION.md`; user subsequently confirmed independent
foundation review complete. It does not implement production comparison or establish
empirical validity. Real-data validation is deferred by user instruction. Initial
reference source: ExoMol anonymous catalogue search and narrow two-column,
zero-pressure .sigma representation. Bounded CO2 / 12C-16O2 / UCL-4000 retrieval,
separate reference display and provenance cache/offline reopening are implemented.
An approved actual Qt download/reopen check passed for one 11-point product; this
does not establish atmospheric validity or coverage for other molecules/settings.
New work awaits independent review and desktop acceptance. See
`../Chunk_5_1/PRODUCT_RETRIEVAL_IMPLEMENTATION.md`. The initial project provenance-transfer
contract is described below. Do not infer
selection of NIST, JCAMP-DX, line matching or forward modelling from historical plans.

User-feedback follow-up: verified water (H2O / 1H2-16O / POKAZATEL) and methane
(CH4 / 12C-1H4 / MM) are now explicit service mappings alongside CO2. Immutable
mapping entries bind identity, endpoint, description, limits and citations; no
arbitrary catalogue slug becomes a download URL. Requests/cache records carry the
isotopologue; missing identity in original v1 records means the historical CO2
service only. Catalogue context must match the validated request. Old records are
not rewritten. Provider-specific limits are checked before any request; switching
selected entries does not silently change the chosen settings. New work awaits
Argon and desktop review; see USER_FEEDBACK_WORKFLOW_20261028.md under Chunk_5_1.

### Project source attachments — 2026-10-28

Project UI uses application services (`ProjectStore`) and the persistence backend;
the widgets do not issue SQL. Existing project IDs and SQLite spectrum row IDs are
retained. New records optionally add `ecas-project-source-v1` to their existing
JSON payload; no table migration or rewrite of legacy rows is performed. Original
source bytes are base64-encoded in the same saved record as parsed values, units,
source hash, CSV schema where applicable, and NASA table/cache metadata. Cache
records and exact metadata-response bytes are retained when available. Files are
snapshotted rather than linked so cache cleanup cannot invalidate saved projects.

Validate the displayed data against the current source before attaching. Reopening
checks a digest binding the normalized spectrum and attachment, plus the raw-body
hash. These detect changes, not malicious replacement by a party able to recompute
the hashes or establish remote authenticity. Legacy data is explicitly unverified
with respect to original bytes and can be opened without inventing provenance.
Source copies are capped at 16 MiB and records at 64 MiB as application memory
limits. Read-only project loading does not create or migrate databases; project
creation is exclusive and writes require an explicit UI action. Project storage
is checkout-local under ignored `projects/`. No project deletion/rename or bulk
migration feature is introduced. The new API rejects linked roots/folders/databases;
this is not a claim of race-proof isolation on a hostile filesystem.

NASA-relative URLs are expanded only in the table's presentation layer for known
NASA-table imports/project attachments. Source rows and raw bytes remain unchanged.
Only HTTP(S) links without embedded credentials can be opened, on explicit double-
click, through the system browser. Other text is retained without link behavior.

### NASA target name resolution — 2026-10-28

Use NASA's documented System Aliases service before canonical-name spectroscopy
queries: https://exoplanetarchive.ipac.caltech.edu/docs/sysaliases.html . Inspected
real responses for the four human-feedback cases. Require status OK, matching
requested name, exactly one planet explicitly marked requested_object=True, and
agreement among the planet key, default_name and manifest resolved_name. Never
select the first planet of a returned system. Host-only, ambiguous, malformed or
inconsistent responses stop with a visible error. Names, sizes and JSON structure
are bounded; the same anonymous/cancellable client is used with the newly allowed
exact alias-service path. Canonical metadata/query identity is retained in the
existing spectrum cache. Original interactive input is displayed in resolution
status, not added as a new persisted cache-schema field.

An empty canonical-name inventory means no products in the queried spectroscopy
table, not that the planet is unknown, its data are FITS, or all archives lack
observations. Changing measurement-format support is a separate task.

---


### WASP-39 b Archive CSV Schema Validation
**Date:** 2026-10-27
**Status:** Existing behavior retained.

The WASP-39 b archive importer requires the expected 21 source columns for its supported schema. Files with a different source-column structure must not be silently treated as valid archive files.

Generic CSV import remains a separate path. Manual column mapping for generic CSV files is planned but has not yet been implemented.

This decision does not establish support for all archive schema variants or all generic CSV formats. Any relaxation of archive validation must be justified by a defined schema requirement and accompanied by appropriate tests.

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
