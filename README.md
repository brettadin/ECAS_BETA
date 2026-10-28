# ECAS — Exoplanetary Characterization & Astrochemistry Suite

ECAS is a scientific software project focused on exoplanetary characterization and astrochemistry. Its long-term goal is to support the inspection, preparation, comparison, and interpretation of scientific data relevant to exoplanet atmospheres and their chemical composition.

The project is being developed incrementally, with an emphasis on scientific integrity, traceable data, transparent validation, and maintainable software architecture.

> **Project status:** ECAS is under active development. The current application, verified capabilities, outstanding work, and known limitations are recorded in [`docs/brains/PROJECT_STATE.md`](docs/brains/PROJECT_STATE.md). Architectural proposals and long-term goals must not be interpreted as implemented functionality.

For the current review branch, start with the
[review checkpoint](docs/REVIEW_CHECKPOINT_20261028.md), covering project/NASA
improvements, the Chunk 5 research foundation and initial molecular references.

## Contents

- [Project goals](#project-goals)
- [Current application](#current-application)
- [Scientific principles](#scientific-principles)
- [Architecture and documentation](#architecture-and-documentation)
- [Getting started](#getting-started)
- [Development workflow](#development-workflow)
- [AI agent instructions](#ai-agent-instructions)
- [Contributing](#contributing)
- [Project status and limitations](#project-status-and-limitations)

## Project goals

ECAS aims to develop a maintainable research application that can support workflows such as:

- Importing and inspecting scientific spectral data.
- Preserving source information and relevant scientific metadata.
- Validating data structure and identifying incompatibilities before comparison.
- Preparing observations and reference data for scientifically appropriate analysis.
- Comparing exoplanetary observations with suitable reference spectra or models.
- Supporting astrochemical characterization while communicating uncertainty and methodological limitations.
- Preserving analysis inputs, configurations, results, and provenance to improve reproducibility.

These goals describe the intended direction of the project. Individual capabilities must be confirmed against the current implementation and project-state records.

## Current application

For the latest feedback update and external review, start with the
[feedback review checkpoint](docs/REVIEW_FEEDBACK_20261028.md).

**Overview** provides workflow shortcuts and a summary of the loaded observation,
displayed reference and session comparison choices when opened. **Settings** shows
active read-only storage paths and the existing CSV-schema choice, synchronized
with Spectral Data. That choice applies to the next CSV import and lasts for the
session; it does not change loaded data or NASA .tbl handling. See
[workspace pages](docs/Chunk_5_1/WORKSPACE_PAGES_IMPLEMENTATION.md).

The **Molecular References** page supports molecular reference catalogue search.
Search Water, H2O or an ExoMol isotope/dataset identifier; select a result to inspect
its identity. It starts with a cached or bundled dated index. **Refresh from ExoMol**
makes one bounded anonymous metadata request and saves a validated snapshot for
offline use; **Cancel request** preserves the prior catalogue. No network request
is made at startup. Catalogue records do not establish spectral availability,
coverage or compatibility.

Supported downloads are **CO2 / 12C-16O2 / UCL-4000**, **H2O / 1H2-16O / POKAZATEL**
and **CH4 / 12C-1H4 / MM**. Search the formula, select the matching record,
choose temperature/range/spacing, then **Download selected reference**. The
calculated zero-pressure, Doppler-only cross section appears in a separate table;
**Open cached reference** revalidates it offline. Retrieval for other catalogue
records remains unsupported. Defaults are reference settings, not inferred planet
conditions. There is no scientific comparison or molecular-detection result.
See [current workflow status](docs/Chunk_5_1/USER_FEEDBACK_WORKFLOW_20261028.md)
for verification, bounds and pending review. Runtime reference caches at
data/ExoMol/cache/ are excluded from Git.

**Comparisons** supports independent session observation choices and validated
cached-reference choices, with separate read-only tables and explicit blocked
comparison explanations. Load/reopen an observation, click **Add current observation**,
then **Refresh cached choices** and select a reference. Analysis is not implemented.
See [selection workflow](docs/Chunk_5_1/COMPARISON_SELECTION_IMPLEMENTATION.md).
Switching pages retains
the current observation, reference selection and any active reference request.
Current feedback work: [workflow notes](docs/Chunk_5_1/USER_FEEDBACK_WORKFLOW_20261028.md).

The supplied project history identifies a Python desktop application using PySide6 for its user interface, PyQtGraph for spectral visualization, and SQLite-backed persistence.

The known development baseline includes spectral data representation, CSV ingestion, persistence, a desktop interface, and spectral plotting. The CSV importer has been described as supporting a specific WASP-39 b archive CSV schema; this should not be interpreted as universal CSV/TXT support or as a complete online archive-retrieval system.

Consult [`docs/brains/PROJECT_STATE.md`](docs/brains/PROJECT_STATE.md) and inspect the current source code for the latest verified status.

### Technology overview

| Area | Known technology or role |
|---|---|
| Language | Python |
| Desktop interface | PySide6 |
| Spectral visualization | PyQtGraph |
| Persistence | SQLite |
| Scientific data | Spectral observations and related metadata |
| Testing | pytest is used in the project history; check current test configuration |

This table reflects the known project baseline and must be reconciled with the current repository when implementation changes occur.

## Scientific principles

Scientific integrity is a core requirement, not an optional feature.

### Preserve provenance

Data should remain traceable to its source. Where applicable, retain source identifiers, citations, relevant metadata, dataset versions, and processing history.

### Distinguish data validation from scientific validity

A file that parses successfully is not necessarily scientifically valid. Structurally valid datasets may still be incompatible because of differences in units, spectral coverage, resolution, uncertainty, calibration, or measurement type.

### Make assumptions explicit

Do not invent missing units, metadata, instrument characteristics, scientific thresholds, or interpretations. Uncertain assumptions must be identified and handled according to an explicit policy.

### Support defensible comparisons

Comparison methods and thresholds require a documented rationale and suitable evidence. Software tests can establish that an implementation behaves as intended; they do not independently establish scientific validity.

### Preserve reproducibility

Where supported by the workflow, analysis records should identify the inputs, processing methods, relevant settings, software versions, results, and limitations needed to understand or reproduce an analysis.

## Architecture and documentation

ECAS uses its repository documentation to preserve project context, technical decisions, scientific requirements, and development history.

Start with these documents:

| Document | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Shared operating instructions for AI agents working on ECAS |
| [`docs/ECAS.md`](docs/ECAS.md) | Master project blueprint, scientific direction, and long-term objectives |
| [`docs/brains/PROJECT_STATE.md`](docs/brains/PROJECT_STATE.md) | Verified implementation state, completed work, known limitations, and outstanding tasks |
| [`docs/brains/DECISIONS.md`](docs/brains/DECISIONS.md) | Approved technical and architectural decisions and their rationale |
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | Architectural requirements, system structure, and boundaries |
| [`docs/architecture/DATA_FLOW.md`](docs/architecture/DATA_FLOW.md) | Data movement through the application and associated validation points |
| [`docs/architecture/DATA_MODELS.md`](docs/architecture/DATA_MODELS.md) | Domain entities, data representations, and relationships |
| [`docs/architecture/ECAS_Architecture_Specification.md`](docs/architecture/ECAS_Architecture_Specification.md) | Broader architectural specification |
| [`docs/architecture/MODULE_RESPONSIBILITIES.md`](docs/architecture/MODULE_RESPONSIBILITIES.md) | Module responsibilities and intended boundaries |
| [`docs/architecture/VALIDATION_STRATEGY.md`](docs/architecture/VALIDATION_STRATEGY.md) | Software validation, scientific evaluation, benchmarks, and threshold rationale |

Verify these paths against the current repository. If a document is absent, renamed, or superseded, update this map rather than leaving misleading links or creating unnecessary duplicates.

### Which document should answer which question?

- **What is ECAS intended to become?** Read `docs/ECAS.md`.
- **What is implemented now?** Read `docs/brains/PROJECT_STATE.md` and inspect the code.
- **Why was a technical choice made?** Read `docs/brains/DECISIONS.md`.
- **How should the application be structured?** Read the architecture documentation.
- **How should scientific and software correctness be assessed?** Read `VALIDATION_STRATEGY.md`.
- **How should an AI agent work on the project?** Read `AGENTS.md`.

When documentation and implementation disagree, investigate the discrepancy. Do not assume that a proposed design has already been implemented.

## Getting started

ECAS is a Python project. The exact installation and launch procedure should be taken from the current repository configuration and verified instructions rather than assumed from this overview.

### 1. Obtain the repository

Clone the repository:

```bash
git clone https://github.com/brettadin/ECAS_BETA.git
cd ECAS_BETA
```

### 2. Inspect the project configuration

Runtime dependencies are recorded in `requirements.txt`; test dependencies are
in `requirements-test.txt`. These versions were verified locally on Windows AMD64
with Python 3.14.5; this is not a claim of compatibility with every Python version.

From the repository directory, create a local environment if needed. The install
step downloads packages and should only be run with the operator's approval:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Launch the application

Run from a terminal using the environment where the dependencies were installed:

```powershell
.\.venv\Scripts\python.exe main.py
```

`main.py` is the primary entry point; `app.py` currently starts the same window.
Opening a Python file in an editor does not launch it. Double-clicking may select
a different Python installation instead of this environment. A terminal keeps any
startup error visible; include its complete traceback when reporting a failure.

### Import the bundled WASP-39 b example

1. Open **Spectral Data** in the navigation.
2. Select **WASP-39 b Archive** under **CSV schema** before clicking **Import Spectrum**.
3. Open `data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`.
4. The table and plot should show the imported dataset (331 rows, 23 columns).

This reads a local file directly; it does not depend on database retrieval or
online archive integration. **Generic / Unknown** expects generic wavelength and
signal columns and intentionally does not infer the archive schema. The bundled
file's uppercase source headers are handled by the archive importer. Original
source fields remain available alongside canonical coordinate/signal fields.
Successful import does not establish units or scientific validity.

### Import a downloaded NASA transmission table

**Import Spectrum** also accepts the specifically supported NASA `.tbl` transmission
format. The captured real product is
`data/NASA/2026-10-27/feinstein-2023.tbl`. Select that file in **Spectral Data**;
the CSV schema selector applies to CSV files only. The NASA table declares its
own type and units. It displays 331 rows with wavelength in microns and transit
depth in percent, retaining all 29 source columns plus two canonical aliases.

The importer preserves signed uncertainties, nulls, source URLs and metadata.
It supports a strict four-header, aligned IPAC transmission-table subset; other
spectrum types, malformed rows and nonzero transit-depth flags are rejected.
It does not convert eclipse/direct-imaging data into transmission spectra.
The captured download URL is session-specific; the online workflow below resolves
a fresh session instead of reusing a saved link.

### Search NASA and reopen cached spectra

1. Open **Spectral Data**, enter a planet name or alias such as `WASP39b`,
   and click **Search NASA**. No request is made until you start a search.
2. Select a transmission spectrum, then click **Download selected spectrum**.
   The application retrieves a fresh download link, validates the table, preserves
   the raw response and metadata, and displays it. **Cancel** stops an active request.
3. Click **Cached spectra**, select an entry, then **Load cached spectrum** to
   reopen it without a network request. Changed or incomplete entries are excluded.

The cache is local to this checkout at `data/NASA/cache/` and is excluded from Git.
It retains raw tables, source URLs, retrieval times, metadata responses and SHA-256
hashes. This registration is separate from project SQLite persistence.

NASA first resolves the input to one explicitly identified planet; the resolved
name is shown. Unresolved, host-only, ambiguous or inconsistent responses stop
with an error rather than choosing a planet. A resolved planet may have no spectra
in this archive's queried table; this is distinct from unsupported spectrum types.
Other archives are not searched.

The canonical-name search is limited to 50 metadata records; a limit warning means
the result may be incomplete. Only the supported transmission subset can load.
Each anonymous NASA request has a 15-second deadline and 1 MiB response cap, with
no automatic retries, redirects, cookies or authentication. A changed NASA session
layout stops the download with an error. There is no proxy-authentication support.

The actual application workflow was tested offscreen against NASA for WASP-39 b:
28 transmission results, a 331-row download and cache reopening with no further
requests. Interactive testing on the friend's computer and independent Argon
review remain pending. This verifies retrieval and display, not scientific validity.

### 4. Save spectra in projects

1. Open **Projects**, enter a project ID (letters, numbers, underscores or hyphens),
   and click **Create project**, or select an existing project.
2. Import a spectrum or load a searched/cached spectrum in **Spectral Data**.
3. Return to **Projects** and click **Add displayed spectrum to project**.
4. Select a saved spectrum and click **Open selected spectrum** to restore the
   plot, data and available metadata. Projects are discovered again after restart.

Projects live inside this checkout's `projects/` directory, excluded from Git.
New attachments retain original file bytes, parsed values, units, source hashes
and provenance. NASA cache attachments also retain the original cache record and
metadata response. Reopening does not require the original file, cache or network.
Changed records fail visibly; these integrity hashes are not proof of authenticity.
Existing database rows remain readable and are labelled as legacy records without
source attachments. To preserve a missing source for such a record, reimport the
original data first; provenance is never fabricated. Adding the same spectrum
again creates another saved record rather than overwriting an earlier one.

The project source-size limit is 16 MiB and the JSON record limit is 64 MiB.
Project deletion, renaming, synchronization and large-project performance work are
not implemented. Back up your `projects/` directory separately when sharing code.

Source-URL cells are underlined and can be opened with a double-click. NASA-relative
calculation links are expanded for display only; raw imported values are preserved.
Opening a link invokes the system browser only after that explicit action.

### 5. Run the tests

After approval for any needed test-dependency downloads:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-test.txt
$env:QT_QPA_PLATFORM = 'offscreen'
.\.venv\Scripts\python.exe -B -m pytest -p no:cacheprovider -q
```

A successful test run applies only to the tests and environment actually used. Follow the validation instructions for the current task, and report failures or unverified checks accurately.

## Development workflow

ECAS is developed incrementally. Changes should be small, reviewable, and supported by evidence.

The recommended workflow is:

1. Establish the current project context.
2. Inspect existing implementation, documentation, decisions, and tests.
3. Define the objective, scope, dependencies, and acceptance criteria.
4. Prepare and review a specific implementation plan for substantive changes.
5. Implement only the approved scope.
6. Run relevant tests and inspect the resulting changes.
7. Update affected documentation and project-state records.
8. Report results, limitations, outstanding work, and the next recommended step.

Preserve existing behavior unless the approved task explicitly changes it. Avoid unrelated refactoring, unnecessary abstractions, duplicate documentation, and unsupported scientific claims.

### Recording development work

Meaningful work must leave a durable record in the repository.

Depending on the task, update:

- `docs/brains/DECISIONS.md` for approved decisions and their rationale.
- `docs/brains/PROJECT_STATE.md` for verified changes in implementation status.
- The relevant development plan or implementation log for progress and historical findings.
- Architecture and validation documents when their requirements, mechanisms, or claims are affected.

Work reports should identify what changed, why it changed, how it was verified, which checks were not performed, and what remains unresolved.

## AI agent instructions

All AI agents contributing to ECAS must read [`AGENTS.md`](AGENTS.md) before undertaking substantive work.

The instructions are model- and tool-independent. They apply whether contributors use one agent or coordinate separate planning, implementation, and review agents.

At a minimum, agents must:

- Load the relevant project context before planning.
- Inspect the current repository instead of relying on conversation history alone.
- Distinguish approved decisions, proposed designs, implemented features, tested behavior, and scientifically validated results.
- Work within an explicitly defined scope.
- Preserve scientific integrity and data provenance.
- Add meaningful comments where they explain non-obvious assumptions, numerical methods, invariants, or design decisions.
- Run and report actual verification steps.
- Update relevant documentation and project records.
- Leave a detailed work report and a usable handoff for the next contributor.

The objective is for a new contributor or a different AI model to continue work without requiring the project owner to reconstruct every prior conversation.

## Contributing

Contributions should respect the project's scientific objectives, existing decisions, and documentation practices.

Before making substantial changes:

1. Read `AGENTS.md` and the relevant project documentation.
2. Check the current project state, decisions, and working-tree status.
3. Identify related existing work before proposing a new implementation.
4. Agree on scope and acceptance criteria.
5. Keep changes focused and testable.

When submitting or handing off work, include:

- A concise statement of the objective.
- The important findings and implementation decisions.
- Files changed and the purpose of each change.
- Tests and commands actually executed, with their results.
- Known limitations, unresolved questions, and risks.
- Documentation updated.
- The next recommended step.

Do not report unverified behavior as complete. Do not silently discard another contributor's work or rewrite historical records to conceal how a decision evolved.

## Project status and limitations

ECAS is an evolving research application. Its long-term scientific scope is broader than the currently established implementation.

Capabilities involving generalized scientific-format ingestion, online archive or molecular-reference retrieval, comprehensive provenance and versioning, generalized spectral comparability assessment, scientifically validated comparison methods, defensible thresholds, and fully reproducible offline analysis must be treated as unimplemented or unverified until the current project records and code establish otherwise.

The authoritative implementation status is maintained in [`docs/brains/PROJECT_STATE.md`](docs/brains/PROJECT_STATE.md). Approved technical decisions are maintained in [`docs/brains/DECISIONS.md`](docs/brains/DECISIONS.md).

**Contributions should move ECAS toward its scientific goals without overstating current capabilities or weakening the evidence supporting its results.**
