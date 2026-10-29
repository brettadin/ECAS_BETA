# Pass A — Architecture and application structure

Status: Pass A is substantially complete at the source-inspection level. The review confirms a modular desktop application with distinct scientific, UI, persistence, and external-data components. I have not run the application or its tests, so runtime behavior remains unverified.

## 1. Architecture confirmed

The v1 archive contains a Qt-based desktop application whose core scientific modules are designed to operate independently of the interface.

Application entry point

`main.py` — configuration, startup checks, GUI launch

User interface

`app/ui/main_window.py`

`app/ui/transit_panel.py`

`app/ui/tasks.py`

Scientific core

`app/core/engine.py`

`physics.py`, `fitting.py`, `identify.py`

`transit.py`, `atmosphere.py`, `timeseries.py`

Data and persistence

`tables.py`, `library.py`, `project.py`, `sources.py`

External resources

`archives.py`, `molecule_sources.py`, `spectral_sources.py`

Conceptual grouping based on source inspection, not a verified runtime call graph.

### Main architectural boundaries

- Startup and configuration: `main.py`, `app/core/config.py`
- Spectral modeling: `engine.py`, `physics.py`, `parser.py`
- Observation fitting and identification: `fitting.py`, `identify.py`, `emission.py`, `library.py`
- Transit and time-series analysis: `transit.py`, `timeseries.py`, `spectral_sources.py`
- Optional atmospheric modeling: `atmosphere.py`
- Archive access and source tracking: `archives.py`, `molecule_sources.py`, `sources.py`
- Projects and exports: `project.py`, `export.py`
- Interface and background work: `main_window.py`, `transit_panel.py`, `tasks.py`

This is a meaningful separation of responsibilities. In particular, the scientific engine explicitly describes itself as Qt-independent, which helps keep numerical calculations separate from interface code.

## 2. UI-to-core workflow

The main spectroscopy interface connects user actions to core functions for importing observations, fitting gas multipliers, identifying candidates, and exporting results. The transit panel provides a separate workflow for light curves and wavelength-resolved spectral time series.

The source also confirms a background-task helper in `app/ui/tasks.py`. It runs functions on `QThread` workers and routes completion or error signals back to UI callbacks. Transit analysis uses its own worker; optional atmospheric-model calculations and abundance scans use the shared helper.

Architectural observation: the application already has a mechanism for keeping selected expensive calculations off the UI thread. This is an established implementation feature, not proof that every expensive operation is asynchronous or that thread shutdown is flawless.

## 3. Project persistence

`app/core/project.py` defines the `.ecas` project format:

- `state.json` stores settings, metadata, and project state.
- `arrays.npz` stores numerical arrays for observations, light curves, spectral time series, and transmission-depth spectra.
- A project version is recorded and checked when loading.
- The UI restores input state and re-derives analysis results rather than treating saved results as authoritative.

This is a sensible basis for reproducibility. However, saving input arrays and metadata is not the same as guaranteeing complete scientific provenance. Whether a project retains every source identifier, configuration dependency, processing choice, and relevant software/version detail needs a dedicated data-provenance review.

## 4. Configuration and dependencies

The archive's `pyproject.toml` identifies Python 3.10 or later and the principal dependencies: PyQt6, PyQtGraph, NumPy, SciPy, and Astropy. Additional capabilities include 3D visualization, archive access, testing, and the separately installed `petitRADTRANS` atmospheric-model backend.

The command-line entry point supports configuration selection, grid-point overrides, disabling 3D, and a headless `--check` mode.

These are confirmed from the packaged source and project metadata. I have not tested installation or dependency compatibility in a live environment.

## 5. Findings and risks

| Finding                                                            | Assessment                                                  | Follow-up                                                         |
| ------------------------------------------------------------------ | ----------------------------------------------------------- | ----------------------------------------------------------------- |
| Scientific code is separated from much of the GUI                  | Positive architectural foundation                           | Examine module contracts and data flow                            |
| Multiple analysis workflows share the application                  | Adds useful capability but increases integration complexity | Trace workflow boundaries and state transitions                   |
| Background-task helpers exist                                      | Positive for responsiveness                                 | Review lifecycle, cancellation, stale results, and shutdown       |
| Projects preserve numerical inputs and selected metadata           | Useful persistence foundation                               | Verify provenance completeness and round-trip behavior            |
| Optional scientific dependencies are separated                     | Helps keep the base installation lighter                    | Check graceful handling when optional packages or data are absent |
| Archive contains compiled Python cache files and tooling artifacts | Packaging/maintenance observation, not a functional defect  | Assess significance during repository hygiene review              |

No confirmed functional defect has been established in this pass. These are architectural observations and questions for later verification, not a bug list.

## 6. Pass A conclusion

The source supports describing ECAS v1 as a multi-workflow scientific desktop application, rather than a simple spectrum plotting utility. It includes spectral modeling and fitting, candidate identification, archive interaction, transit analysis, time-series handling, project persistence, and optional physical atmospheric modeling.

The main unresolved architectural questions are how reliably these components interact, how project state and source provenance flow between them, and how well the design is covered by tests. Those questions overlap with the next review passes and should not be prematurely classified as defects.

No files have been modified, and no tests have been run.

Before moving to Pass B, the useful discussion point is whether this architectural summary matches your understanding of v1. If it does, the next pass will examine the implemented workflows and their boundaries in more detail, separating what the code actually supports from what the documentation describes or implies.