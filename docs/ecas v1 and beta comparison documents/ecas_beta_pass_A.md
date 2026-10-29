# ECAS Beta Review — Pass A: Architecture and Application Structure

Review basis: `ecas beta zip.zip`, inspected directly from the supplied archive. This pass is a source-and-document review only. I have not run the application or tests, changed files, or independently verified the historical test reports.

## 1. Overall architecture

ECAS Beta has a more specialized and developed structure than the v1 application reviewed earlier. Its architecture is organized around a desktop interface, scientific data ingestion, project persistence, molecular reference resources, and spectral comparison.

Application entry points

`main.py` · `app.py`

Desktop interface — `ecas/ui/`

Main window, workspace, projects, NASA, molecular references, comparisons and resources

`ecas/ingestion/`

CSV and tabular imports, NASA and ExoMol integration, catalogue and product handling, planet resolution and caches

`ecas/comparison/`

Eligibility, alignment, candidate handling, model generation, adapters, residuals and comparison records

`ecas/models/` and `ecas/resources/`

Spectrum data model and resource catalogue

Persistence and visualization

SQLite-backed project data, project operations, spectral plots and residual plots

Conceptual map of the inspected package structure, not a verified runtime call graph.

The structure is consistent with the intended direction documented in `docs/architecture/ARCHITECTURE.md`. The important distinction is that a module's existence does not prove every intended workflow is complete or scientifically validated.

## 2. Entry points and packaging

| File             | Observed role                                                                          | Assessment                                                                                              |
| ---------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `main.py`        | Creates the PySide6 application, instantiates `ECASWindow`, and starts the event loop. | Current-looking desktop entry point.                                                                    |
| `app.py`         | Contains effectively the same startup sequence as `main.py`.                           | Duplicate entry point; the intended canonical choice is not clear from these files alone.               |
| `main_backup.py` | Contains a separate, simpler window with placeholder workspace pages.                  | Appears to be an older prototype, not the same application as the current `ecas/ui/main_window.py`.     |
| `build_exe.py`   | Builds a Windows executable with PyInstaller and includes local `data/`.               | Provides a build path, but I have not tested it.                                                        |
| `ECAS.spec`      | PyInstaller specification with explicit paths and hidden imports.                      | Contains a machine-specific absolute source path, making this checked-in spec potentially non-portable. |

Finding A1 — Duplicate startup paths. `main.py` and `app.py` currently have the same essential startup implementation. This is not necessarily a functional defect, but it creates a maintenance question: which entry point should users, tests, packaging, and documentation treat as authoritative?

Finding A2 — Packaging configuration differs in portability. `build_exe.py` derives paths from its own directory, while `ECAS.spec` hard-codes a Windows path tied to a particular development directory. That is a concrete portability concern for the spec file, although it does not establish that the build script itself fails.

Finding A3 — Backup prototype remains in the repository archive. `main_backup.py` is visibly a different, placeholder-style interface. Its presence may cause confusion if it is mistaken for the current application. Whether it should be retained or removed is a repository-maintenance decision, not a reason to alter it during this review.

## 3. Package boundaries

The principal package responsibilities are reasonably distinct.

- `ecas/ui/` contains the main window and focused interfaces, including `comparison_browser.py`, `molecular_browser.py`, `nasa_browser.py`, `project_browser.py`, `resources_browser.py`, and `workspace_pages.py`.
- `ecas/ingestion/` groups local-file parsing and source-specific retrieval. NASA and ExoMol handling are represented by multiple dedicated modules rather than one general-purpose importer.
- `ecas/comparison/` separates several comparison concerns: alignment, eligibility, candidate selection, forward-model generation, model adapters, residual diagnostics, and persistence.
- `ecas/models/spectrum.py` defines a frozen `SpectrumData` data model with rows, columns, source path, optional units and signal type, and warnings.
- `ecas/persistence.py` and `ecas/projects.py` divide lower-level spectrum persistence from higher-level project operations.
- `ecas/visualization/` contains separate plotting components for spectra, references, and residuals.

This is a meaningful improvement in functional organization compared with the v1 architecture described in the earlier review. Beta now has explicit boundaries for reference data, comparisons, source-specific ingestion, and project workflows.

### Potential architectural pressure point

`ecas/ui/main_window.py` imports and coordinates a substantial number of these subsystems, including ingestion, plotting, project management, NASA browsing, molecular browsing, comparisons, and resources.

That makes it an important integration point and a possible source of coupling. The module's size and imports alone do not establish that the design is broken. Passes B, E, and F will help determine whether the coordination remains manageable, whether responsibilities are duplicated, and whether the integration is adequately tested.

## 4. Dependencies and test configuration

The supplied dependency files specify:

- `PySide6==6.12.0`
- `pyqtgraph==0.14.0`
- `numpy==2.5.4`

`requirements-test.txt` includes `requirements.txt` and adds `pytest==9.2.0`. `pytest.ini` adds the repository root to the Python path and defines an opt-in `live_network` marker for network-health tests.

The runtime requirements file states that these versions were verified on Windows AMD64 with Python 3.14.5. That is a declaration in the file, not a verification I independently reproduced.

Architecture observation: the pinned dependencies and separate test requirements make the basic environment easier to identify. This pass does not establish whether all optional, network-dependent, or packaging-related paths work in a clean installation.

## 5. Architecture documentation versus implementation

The architecture documents explicitly distinguish proposed design from current implementation:

- `docs/architecture/ARCHITECTURE.md` is marked as an architecture proposal, with implementation status tracked separately.
- `docs/architecture/DATA_FLOW.md` describes existing and intended behavior.
- `docs/architecture/DATA_MODELS.md` labels its conceptual design as non-authorizing and distinguishes implemented, required, proposed, and unresolved items.
- `docs/architecture/MODULE_RESPONSIBILITIES.md` defines intended module boundaries rather than asserting that all boundaries are fully implemented.
- `docs/architecture/VALIDATION_STRATEGY.md` separates software testing from scientific validation.
- `docs/brains/PROJECT_STATE.md` and `docs/brains/DECISIONS.md` record implementation status and decisions.

This is a useful governance structure: the project has a place for intended architecture, a record of approved decisions, and a separate account of implementation status.

Finding A4 — Documentation status must be cross-checked, not assumed. The repository contains extensive historical implementation and verification records. Those records can help establish intent and reported outcomes, but they do not independently prove that the current source still matches each record. This is particularly important because the project state describes multiple successive development chunks and test counts.

## 6. Review findings summary

| ID | Finding                                                                  | Classification                               | Priority for later review     |
| -- | ------------------------------------------------------------------------ | -------------------------------------------- | ----------------------------- |
| A1 | `main.py` and `app.py` duplicate startup behavior.                       | Confirmed observation; maintenance concern   | Low                           |
| A2 | `ECAS.spec` contains a machine-specific absolute path.                   | Confirmed portability concern                | Medium                        |
| A3 | `main_backup.py` contains a separate placeholder interface.              | Confirmed repository observation             | Low                           |
| A4 | Extensive historical status records need comparison with current source. | Review control, not a defect                 | High                          |
| A5 | The main window coordinates many subsystems.                             | Potential coupling risk; no defect confirmed | Reassess in Passes B, E and F |

No confirmed scientific or runtime defect has been established in Pass A. No tests were run.

## 7. Discussion before Pass B

The main architecture question is whether you want to treat the duplicate entry points and the hard-coded PyInstaller spec as items to track for a later cleanup, or simply record them and continue the review without assuming changes are needed.

The more important review question is whether the Beta application actually implements the workflows described in its project state. Pass B will examine the user-facing capabilities and their source paths, distinguishing implemented behavior from planned features and historical claims.

I will wait for your discussion or approval before moving to Pass B.