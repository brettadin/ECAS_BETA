# ECAS — Exoplanetary Characterization & Astrochemistry Suite

ECAS is a scientific software project focused on exoplanetary characterization and astrochemistry. Its long-term goal is to support the inspection, preparation, comparison, and interpretation of scientific data relevant to exoplanet atmospheres and their chemical composition.

The project is being developed incrementally, with an emphasis on scientific integrity, traceable data, transparent validation, and maintainable software architecture.

> **Project status:** ECAS is under active development. The current application, verified capabilities, outstanding work, and known limitations are recorded in [`docs/brains/PROJECT_STATE.md`](docs/brains/PROJECT_STATE.md). Architectural proposals and long-term goals must not be interpreted as implemented functionality.

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

Before installing dependencies, inspect the repository for its dependency and environment configuration, such as `requirements.txt`, `pyproject.toml`, or other setup files.

Create and activate an isolated Python environment appropriate for your platform. Install dependencies using the configuration actually maintained by the project.

Do not install an assumed dependency list without checking the repository.

### 3. Launch the application

Inspect the current entry points and project instructions to determine the supported launch command. Do not assume that similarly named entry-point files are interchangeable.

### 4. Run the tests

The project has used pytest. If pytest and the required dependencies are configured in the current environment, run the relevant test suite using the repository's documented commands.

For example:

```bash
python -m pytest
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