# ECAS Module Responsibilities

**Document status:** Draft for review  
**Project:** Exoplanet Characterization and Spectral Analysis (ECAS)  
**Primary language:** Python  
**Related documents:** `ECAS.md`, `ARCHITECTURE.md`, `DATA_FLOW.md`  
**Implementation status:** This document does not authorize implementation.

---

## 1. Purpose

This document defines the proposed software modules for ECAS, including their responsibilities, expected inputs and outputs, dependency boundaries, and provisional interfaces.

Its purpose is to give implementation agents a consistent understanding of where functionality belongs, how components should communicate, and which architectural rules must be preserved.

The module structure is provisional. It should provide enough organization to support independent development and testing without requiring unnecessary abstractions or prematurely fixing unsettled technical decisions.

### 1.1 Governing documents

- `docs/ECAS.md` defines the project's purpose, scientific principles, and long-term direction.
- `docs/architecture/ARCHITECTURE.md` defines the system architecture, component responsibilities, and dependency rules.
- `docs/architecture/DATA_FLOW.md` defines the movement and transformation of data through the application.
- `docs/architecture/MODULE_RESPONSIBILITIES.md` defines proposed module boundaries and interfaces.
- `docs/architecture/DATA_MODELS.md` will define domain entities, relationships, identifiers, required metadata, and persistence constraints.
- `docs/architecture/VALIDATION_STRATEGY.md` will define scientific benchmark selection, evaluation, and threshold derivation.
- `docs/brains/DECISIONS.md` will record approved decisions and rationale.
- `docs/brains/PROJECT_STATE.md` will record verified project status.

If these documents conflict, agents must identify the conflict rather than silently choose an interpretation.

### 1.2 Scope

The initial application will support:

- A native-style Python desktop application.
- One research project per exoplanet, with multiple observations and analyses.
- Online archive retrieval and local-file import.
- Traceable observation and molecular reference data.
- Distinct handling of measured or experimentally derived spectra, theoretical line lists, and synthesized spectra.
- Input validation and scientific comparability assessment.
- Documented spectral preparation where required.
- Pluggable spectral comparison methods and candidate scoring.
- Persistent projects, cached inputs, analysis results, and provenance.
- Offline access to saved projects and analyses when the required resources are available.

The first comparison method, UI framework, archive providers, supported import formats, and final data schemas remain undecided.

---

## 2. Module Design Principles

All modules must follow these principles.

### 2.1 Single, clear responsibility

Each module must have a defined purpose. Responsibilities should not be duplicated across the UI, application services, scientific services, and persistence layer.

Related responsibilities may share a module when separating them would add complexity without improving testability or maintainability.

### 2.2 Explicit inputs and outputs

Operations should receive their required data and configuration explicitly and return defined results.

Modules must not depend on hidden UI state, implicit global configuration, or undocumented side effects.

### 2.3 Dependency direction

The desktop UI calls application services. Application services coordinate workflows. Scientific services operate on defined data objects. Source adapters handle provider-specific interactions. Persistence services manage stored records and artifacts.

Scientific algorithms must not depend on the UI, directly access provider APIs, or independently manage database transactions.

### 2.4 Scientific meaning must be preserved

Modules must preserve distinctions between observations, molecular references, theoretical line lists, synthesized products, and processed data.

A numeric array alone does not establish that two datasets represent compatible scientific quantities.

### 2.5 Provenance is part of the data contract

Modules that acquire, transform, synthesize, compare, or persist data must preserve the source identity and processing history relevant to their operation.

Derived data must remain linked to their inputs. Historical analyses must retain the identity of the exact inputs and settings used.

### 2.6 Errors must be explicit

Modules must distinguish invalid inputs, unsupported operations, unavailable dependencies, scientific incompatibility, incomplete execution, and persistence failures.

An unsuccessful operation must not return a result that appears to represent a successful analysis.

### 2.7 Keep implementation proportional to current requirements

Do not implement speculative abstractions, generic plugin marketplaces, distributed processing, full atmospheric retrieval, or unrelated future capabilities merely because the architecture may eventually support them.

---

## 3. Proposed Python Package Structure

The following tree is a provisional organization proposal. It is intended to guide implementation planning, not to require the immediate creation of every file.

```text
ECAS/
├── docs/
│   ├── ECAS.md
│   ├── architecture/
│   │   ├── ARCHITECTURE.md
│   │   ├── DATA_FLOW.md
│   │   ├── MODULE_RESPONSIBILITIES.md
│   │   ├── DATA_MODELS.md
│   │   └── VALIDATION_STRATEGY.md
│   └── brains/
│       ├── DECISIONS.md
│       └── PROJECT_STATE.md
│
├── src/
│   └── ecas/
│       ├── __init__.py
│       ├── __main__.py
│       ├── bootstrap.py
│       │
│       ├── app/
│       │   ├── __init__.py
│       │   ├── services.py
│       │   └── errors.py
│       │
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_window.py
│       │   ├── projects/
│       │   ├── observations/
│       │   ├── references/
│       │   └── analysis/
│       │
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── planets.py
│       │   ├── projects.py
│       │   ├── observations.py
│       │   ├── references.py
│       │   ├── spectra.py
│       │   └── analyses.py
│       │
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── importers.py
│       │   ├── validation.py
│       │   └── registry.py
│       │
│       ├── sources/
│       │   ├── __init__.py
│       │   ├── observations.py
│       │   └── references.py
│       │
│       ├── science/
│       │   ├── __init__.py
│       │   ├── comparability.py
│       │   ├── preparation.py
│       │   ├── comparison.py
│       │   ├── scoring.py
│       │   └── validation.py
│       │
│       ├── library/
│       │   ├── __init__.py
│       │   └── references.py
│       │
│       ├── projects/
│       │   ├── __init__.py
│       │   └── service.py
│       │
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── repositories.py
│       │   ├── artifacts.py
│       │   └── cache.py
│       │
│       ├── visualization/
│       │   ├── __init__.py
│       │   ├── plots.py
│       │   └── reports.py
│       │
│       └── diagnostics/
│           ├── __init__.py
│           └── logging_config.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── scientific/
│   └── fixtures/
│
├── pyproject.toml
└── README.md
```

### 3.1 Interpretation of the tree

The tree identifies proposed ownership boundaries, not a final directory contract.

Some entries may be combined or split after the actual workflow, dependencies, and data models are established. In particular:

- The UI subdirectories depend on the UI framework selected later.
- Source adapters should be added only for supported providers.
- Importers should be added only for explicitly supported formats.
- The comparison implementation must remain independent of the first algorithm selected.
- Domain models and repository interfaces must be refined alongside `DATA_MODELS.md`.
- Test directories may be adjusted to match the eventual testing strategy.

Do not create empty placeholder modules solely to match the tree. Create modules when they have a real, defined responsibility.

---

## 4. Dependency Overview

The intended dependency direction is:

```text
Desktop UI
    |
    v
Application Services
    |
    +-------------------+
    |                   |
    v                   v
Scientific Services   Project/Data Services
    |                   |
    +---------+---------+
              |
              v
       Domain Models
              |
              v
     Interfaces / Storage
              |
              v
    External Sources and Files
```

This is a conceptual diagram, not a requirement for a rigid implementation in which every operation traverses every layer.

### 4.1 Dependency rules

1. UI modules may call application services and use UI-specific presentation models.
2. UI modules must not query SQLite directly or invoke provider APIs directly.
3. Application services may coordinate ingestion, scientific operations, project management, and persistence.
4. Application services must not duplicate scientific algorithms.
5. Domain models must not depend on the UI framework, source providers, or concrete database implementations.
6. Source adapters may depend on external provider interfaces and parsing libraries.
7. Source adapters must not depend on UI modules or scientific comparison implementations.
8. Scientific modules must consume defined data objects and explicit settings.
9. Scientific modules must not perform hidden network retrieval or direct database writes.
10. Comparison methods must not depend on UI state or provider-specific formats.
11. Persistence implementations must not independently interpret scientific results.
12. Visualization modules must display supplied results rather than independently rerunning scientific calculations.
13. Shared domain concepts and interfaces must not import higher-level application or UI modules.
14. Dependencies must not be circular.
15. New abstractions must provide a concrete benefit in separation, testability, or extensibility.

Where a dependency would violate these rules, introduce an appropriate interface or move responsibility to the correct layer instead of creating a workaround.

---

## 5. Module Responsibilities

## 5.1 Application entry point and bootstrap

**Proposed modules:** `__main__.py`, `bootstrap.py`

**Purpose:** Start ECAS and initialize its required services.

**Responsibilities:**

- Provide a single supported application entry point.
- Initialize configuration and application-wide diagnostics.
- Construct the required service and persistence objects.
- Initialize the desktop UI.
- Handle unrecoverable startup failures clearly.
- Ensure the application uses its intended data and configuration locations.

**Inputs:**

- Application configuration.
- Required runtime dependencies.
- Local application and storage settings.

**Outputs:**

- A running desktop application or a clear startup failure.

**Dependencies:**

- Application services.
- UI entry point.
- Storage initialization.
- Logging configuration.

**Must not:**

- Contain scientific algorithms.
- Implement source-specific retrieval.
- Duplicate project or analysis workflows.
- Assume that optional caches or remote services are available during startup.

**Completion criteria:**

- ECAS has one documented launch path.
- Startup failures are distinguishable from failures that occur after the UI opens.
- Initialization is testable without requiring scientific analysis to run.

## 5.2 Desktop UI

**Proposed modules:** `ui/`

**Purpose:** Present application state and collect user choices.

**Responsibilities:**

- Display planet projects and their contents.
- Support observation discovery and local-file selection.
- Present available molecular references.
- Collect analysis configuration.
- Show progress, validation results, warnings, and errors.
- Display spectra, comparison outputs, and saved analyses.
- Allow users to inspect source information and processing history.

**Inputs:**

- User actions.
- Application-service responses.
- Domain and presentation data.
- Progress and error notifications.

**Outputs:**

- Requests to application services.
- User-selected identifiers, settings, and import paths.
- Rendered information.

**Dependencies:**

- Application-service interfaces.
- UI framework and visualization components.

**Must not:**

- Implement scientific comparison or scoring.
- Directly manipulate database records.
- Parse archive responses independently.
- silently normalize or modify scientific data.
- Convert arbitrary numerical scores into detection claims.
- Hide warnings because they complicate the interface.

**Completion criteria:**

- Core workflows can be performed without bypassing application services.
- Scientific values and units are labeled appropriately.
- Incompatible data and incomplete analyses are clearly distinguished from successful results.

**Open decision:** UI framework and detailed view structure.

## 5.3 Application services

**Proposed modules:** `app/services.py`, with further separation if justified.

**Purpose:** Coordinate complete application workflows.

**Responsibilities:**

- Find planets and manage project operations.
- Coordinate observation retrieval and import.
- Coordinate validation and registration.
- Coordinate molecular reference discovery and acquisition.
- Initiate comparability assessment and spectral preparation.
- Execute the selected comparison method through its interface.
- Coordinate persistence and result retrieval.
- Handle application-level preconditions and failures.
- Provide workflow results suitable for the UI.

**Inputs:**

- User-selected identifiers and settings.
- Domain objects.
- Requests to retrieve, import, prepare, analyze, or persist data.

**Outputs:**

- Registered records.
- Workflow status and errors.
- Analysis results.
- Saved project or analysis information.

**Dependencies:**

- Domain models and interfaces.
- Ingestion and source services.
- Scientific services.
- Project and persistence services.

**Must not:**

- Contain provider-specific parsing.
- Implement comparison algorithms.
- Perform direct SQL operations throughout workflow code.
- Depend on particular UI widgets.
- silently bypass validation or comparability requirements.

**Completion criteria:**

- Each supported user workflow can be initiated through a defined service boundary.
- Workflow prerequisites and failures are handled consistently.
- Scientific operations can be tested without starting the desktop UI.

## 5.4 Domain models

**Proposed modules:** `domain/`

**Purpose:** Represent ECAS's core scientific and project concepts independently of UI and storage implementations.

**Responsibilities:**

- Represent planets and their identifiers.
- Represent planet projects.
- Represent individual observations and their metadata.
- Represent molecules and molecular reference datasets.
- Represent spectral data and units.
- Represent prepared or synthesized data as derived products.
- Represent analysis runs, candidate results, and relevant status information.
- Represent provenance and relationships between source and derived data.

**Inputs:**

- Validated values and metadata from application and ingestion services.
- Explicit state and relationship information.

**Outputs:**

- Domain objects with well-defined meanings and invariants.

**Dependencies:**

- Standard Python functionality and narrowly justified scientific value types.

**Must not:**

- Depend on the desktop UI framework.
- Make network requests.
- Perform database queries.
- Perform hidden scientific transformations.
- Treat every spectrum-like object as the same physical quantity.

**Completion criteria:**

- Core concepts have stable identities and clearly documented meanings.
- Source, derived, and analysis records remain distinguishable.
- Domain objects do not depend on concrete external providers or storage engines.

**Open decision:** Exact fields, serialization, validation invariants, and relationships belong in `DATA_MODELS.md`.

## 5.5 Observation ingestion

**Proposed modules:** `ingestion/importers.py`, `ingestion/validation.py`, `ingestion/registry.py`

**Purpose:** Convert supported source inputs into validated, registered ECAS datasets.

### Importers

Responsible for:

- Accepting local-file inputs.
- Selecting the appropriate supported parser.
- Extracting available spectral values and metadata.
- Reporting unsupported structures and ambiguous columns.
- Preserving the relationship to the original input.

### Validation

Responsible for:

- Checking structural integrity.
- Checking coordinate and signal dimensions.
- Identifying missing, invalid, or non-finite values.
- Checking units and required metadata.
- Preserving uncertainty and quality information.
- Reporting validation outcomes and warnings.

### Registry

Responsible for:

- Registering successfully validated datasets.
- Associating observations with planet projects.
- Associating shared references with the reference library when appropriate.
- Detecting possible duplicates or updated content without erasing history.

**Inputs:**

- Local files or retrieved source payloads.
- Parsing and format configuration.
- Provenance information.

**Outputs:**

- Parsed datasets.
- Validation reports.
- Registered dataset records.
- Explicit errors for unsupported or invalid inputs.

**Dependencies:**

- Domain models.
- Source adapters or local-file access.
- Persistence interfaces.
- Relevant parsing and validation libraries.

**Must not:**

- Perform molecular comparisons.
- Silently infer missing scientific values.
- Register invalid data as valid.
- overwrite historical inputs without explicit version handling.

**Completion criteria:**

- Online and local inputs converge on shared validation.
- Validation outcomes distinguish invalid data from valid data with limitations.
- Original source identity remains traceable.

**Open decisions:** Initial file formats, minimum required metadata, and exact validation rules.

## 5.6 Source adapters

**Proposed modules:** `sources/observations.py`, `sources/references.py`

**Purpose:** Isolate external data providers from the rest of ECAS.

**Responsibilities:**

- Search supported online archives or reference providers.
- Retrieve selected datasets and associated metadata.
- Handle provider-specific response formats.
- Report network, access, and provider errors.
- Expose provider-independent acquisition results.
- Preserve source identifiers and version information where available.

**Inputs:**

- Search criteria.
- Provider-specific identifiers.
- Retrieval requests and necessary configuration.

**Outputs:**

- Search results.
- Retrieved source payloads and metadata.
- Structured acquisition errors.

**Dependencies:**

- External provider APIs.
- Network and parsing libraries.
- Narrowly defined source-adapter interfaces.

**Must not:**

- Contain scientific comparison logic.
- Directly update UI widgets.
- Decide whether a dataset constitutes a molecular detection.
- Treat successful download as successful scientific validation.
- Silently substitute a different dataset when a requested source is unavailable.

**Completion criteria:**

- Provider-specific details remain isolated.
- Acquisition failures are explicit.
- Retrieved inputs can be passed to the common ingestion and validation workflow.

**Open decisions:** Initial providers, supported source products, authentication needs, rate limits, and source-specific licenses or access restrictions.

## 5.7 Molecular reference library

**Proposed modules:** `library/references.py`

**Purpose:** Manage molecular reference discovery, metadata, availability, and selection.

**Responsibilities:**

- Find references associated with a molecular identity.
- Distinguish measured or experimentally derived spectra from theoretical line lists.
- Track synthesized spectra and their source inputs.
- Expose reference metadata and limitations.
- Track local availability and cached versions.
- Provide reference selections to analysis workflows.

**Inputs:**

- Molecular identifiers or search criteria.
- Reference catalog records.
- Retrieved or imported reference datasets.
- User-selected reference identities.

**Outputs:**

- Reference search results.
- Reference metadata.
- Selected reference records.
- References available for local use.

**Dependencies:**

- Domain models.
- Reference source adapters.
- Ingestion and validation.
- Persistence and cache services.

**Must not:**

- Treat line lists as measured continuous spectra.
- Claim that a reference is physically applicable to an atmosphere without the required assessment.
- Overwrite historical reference versions silently.
- Duplicate shared reference data unnecessarily across planet projects.

**Completion criteria:**

- Reference types are explicitly identified.
- Source and version information are preserved.
- Projects can refer to shared references without losing analysis-specific provenance.

## 5.8 Comparability assessment

**Proposed module:** `science/comparability.py`

**Purpose:** Determine whether an observation and selected reference can be meaningfully used by a particular comparison method.

**Responsibilities:**

- Check spectral quantities and units.
- Check coordinate coverage and resolution requirements.
- Consider normalization, processing state, uncertainties, and data quality.
- Evaluate method-specific input requirements.
- Identify incompatibilities and missing information.
- Report required preparation steps where justified.

**Inputs:**

- Validated observation.
- Validated reference dataset.
- Declared comparison method requirements.
- Relevant metadata.

**Outputs:**

- A comparability outcome.
- Reasons for warnings or incompatibility.
- Identified preparation requirements.

**Dependencies:**

- Domain models.
- Scientific metadata and unit-handling utilities.
- Comparison-method capability declarations or interfaces.

**Must not:**

- Retrieve data directly.
- Modify the original input.
- Assume all methods require the same input conditions.
- Allow numeric compatibility to substitute for scientific compatibility.

**Completion criteria:**

- Structural validity and scientific comparability remain separate.
- Method-specific requirements are explicit.
- Incompatible inputs cannot proceed silently.

## 5.9 Spectral preparation

**Proposed module:** `science/preparation.py`

**Purpose:** Create documented derived inputs that satisfy a selected comparison method's requirements.

**Responsibilities:**

- Perform supported transformations required by the chosen method.
- Track transformation order and settings.
- Preserve relationships to original inputs.
- Retain or correctly propagate uncertainty information where supported.
- Identify transformations that cannot be performed safely.
- Reuse equivalent prepared inputs when their identities and processing histories match.

**Inputs:**

- Validated source datasets.
- Comparability assessment.
- Explicit transformation requests and parameters.

**Outputs:**

- Prepared spectral data.
- Transformation history.
- Warnings and failures.

**Dependencies:**

- Domain models.
- Scientific numerical libraries.
- Comparability services.
- Defined provenance structures.

**Must not:**

- Modify source datasets in place.
- Apply undocumented normalization or filtering.
- Assume resampling or resolution matching is always valid.
- Discard uncertainty or quality information without documenting the effect.
- Create synthesized spectra without retaining their theoretical or measured source inputs.

**Completion criteria:**

- Each prepared product is identifiable as derived data.
- Transformations and relevant parameters are reproducible.
- Preparation failures are explicit.

**Open decision:** Which transformations are required depends on the selected comparison method and benchmark evidence.

## 5.10 Comparison engine and methods

**Proposed module:** `science/comparison.py`

**Purpose:** Provide a stable interface for executing independently implemented comparison methods.

The comparison engine coordinates method selection and execution. Individual methods implement their own scientifically documented calculations.

**Responsibilities:**

- Define the common method contract.
- Identify method capabilities and requirements.
- Accept validated, prepared inputs and explicit settings.
- Execute the selected method.
- Return method-defined scores and diagnostics.
- Identify the method and version associated with each result.
- Report unsupported inputs and execution failures.

**Inputs:**

- Prepared observation data.
- Prepared molecular reference data.
- Explicit method settings.
- Required method dependencies.

**Outputs:**

- A method-defined comparison result.
- Diagnostics.
- Warnings and limitations.
- Execution status and method identity.

**Dependencies:**

- Domain models.
- Comparability and preparation interfaces.
- Scientific numerical libraries.
- The selected method implementation.

**Must not:**

- Perform online data retrieval.
- Parse provider-specific formats.
- Access desktop UI state.
- Perform hidden preparation outside the documented workflow.
- Write directly to the project database.
- Convert every method output into a common score with an assumed universal meaning.

**Completion criteria:**

- Methods can be introduced without rewriting acquisition or UI components.
- Method-specific outputs retain their definitions.
- Method execution is testable independently of the desktop application.

**Open decisions:** The first method, exact interface requirements, score interpretation, and numerical dependencies will be selected after benchmark investigation.

## 5.11 Candidate scoring and scientific validation

**Proposed modules:** `science/scoring.py`, `science/validation.py`

**Purpose:** Manage candidate-level interpretation and evaluate method behavior against curated benchmark cases.

### Candidate scoring

Responsible for:

- Organizing method outputs by molecular candidate.
- Applying documented scoring or ranking rules where justified.
- Preserving the original method outputs and score definitions.
- Reporting relevant uncertainty, warnings, and limitations.
- Avoiding unsupported claims about detection probability or abundance.

### Scientific validation

Responsible for:

- Executing defined evaluations against curated benchmark cases.
- Separating method-development cases from evaluation cases where required.
- Calculating selected validation metrics.
- Recording the benchmark set and method configuration.
- Reporting limitations and insufficient evidence.

**Inputs:**

- Comparison results.
- Candidate and method metadata.
- Benchmark cases and evaluation configuration.

**Outputs:**

- Candidate-level result records.
- Evaluation metrics.
- Validation reports and warnings.

**Dependencies:**

- Domain models.
- Comparison results.
- Benchmark data and validation strategy.
- Persistence interfaces where results are saved.

**Must not:**

- Invent validation thresholds.
- Treat a candidate score as a probability without justification.
- Treat benchmark inclusion as proof that ECAS must reproduce a published conclusion.
- Use the same evaluation evidence inappropriately for both tuning and independent performance claims.

**Completion criteria:**

- Candidate results preserve the meaning of the underlying method outputs.
- Scientific evaluation is distinguishable from ordinary software testing.
- Validation claims are traceable to the benchmark data and procedures.

**Open decisions:** Benchmark selection, metrics, thresholds, and detailed evaluation procedures belong in `VALIDATION_STRATEGY.md`.

## 5.12 Project management

**Proposed modules:** `projects/service.py`

**Purpose:** Organize research around one exoplanet per project.

**Responsibilities:**

- Create, open, list, and manage planet projects.
- Associate a project with the correct planet identity.
- Track multiple observations and analyses.
- Provide access to project notes and relevant metadata.
- Coordinate project-level persistence.
- Preserve the distinction between project records and shared reference records.

**Inputs:**

- Planet identifiers.
- Project metadata.
- User actions and application-service requests.
- Observation and analysis identifiers.

**Outputs:**

- Project records.
- Project summaries and contents.
- Project-operation status.

**Dependencies:**

- Domain models.
- Persistence services.
- Planet and observation catalog services.

**Must not:**

- Implement scientific comparison.
- Duplicate shared molecular reference data without need.
- Replace historical observation or analysis identities when new data arrive.

**Completion criteria:**

- Each project has one primary planet association.
- Multiple observations and analysis runs can coexist.
- Project reopening does not require live archive access when required records are local.

## 5.13 Persistence and database access

**Proposed modules:** `storage/database.py`, `storage/repositories.py`

**Purpose:** Manage structured records and their relationships.

**Responsibilities:**

- Initialize and access the SQLite database.
- Store and retrieve projects, planets, observations, references, and analysis records.
- Maintain relationships and stable identifiers.
- Apply transactions and appropriate integrity checks.
- Support schema evolution and migration once defined.
- Detect or report persistence failures.
- Prevent partial writes from being reported as completed operations.

**Inputs:**

- Domain records or persistence-specific representations.
- Query criteria.
- Explicit update or transaction requests.

**Outputs:**

- Retrieved records.
- Persistence status.
- Structured storage errors.

**Dependencies:**

- SQLite and the selected database access library.
- Domain models or explicit persistence mappings.

**Must not:**

- Perform scientific interpretation.
- Contain provider-specific network logic.
- Be called directly throughout the UI.
- Silently overwrite historical records.
- Report successful persistence before required writes and artifacts are verified.

**Completion criteria:**

- Structured records have stable identities.
- Relationships between projects, inputs, and analyses are preserved.
- Database failures are explicit and recoverable where practical.

**Open decisions:** Exact schema, database library, migrations, transaction details, and concurrency requirements.

## 5.14 Artifact storage and cache

**Proposed modules:** `storage/artifacts.py`, `storage/cache.py`

**Purpose:** Manage larger source files, prepared datasets, synthesized references, and reusable cached resources.

**Responsibilities:**

- Store and retrieve source files and derived artifacts.
- Associate artifacts with structured records.
- Track file identity and integrity information where practical.
- Support shared cached molecular references.
- Preserve historical artifacts required by saved analyses.
- Identify missing, incomplete, or corrupt files.
- Avoid unnecessary duplication of equivalent resources.

**Inputs:**

- File payloads or paths.
- Artifact metadata.
- Source and derived dataset identifiers.
- Cache lookup and storage requests.

**Outputs:**

- Artifact references.
- Verified file availability.
- Cache lookup results.
- Storage or integrity errors.

**Dependencies:**

- Filesystem operations.
- Persistence metadata.
- Hashing or integrity utilities where appropriate.

**Must not:**

- Treat filenames alone as proof of content identity.
- Silently replace a historical artifact.
- Execute imported file content.
- Delete artifacts still required for reproducibility.

**Completion criteria:**

- Structured records can identify their associated files.
- Missing or corrupt artifacts are reported clearly.
- Cached resources can be reused without changing historical analysis inputs.

**Open decisions:** Storage paths, cache retention, refresh policies, cleanup behavior, and file integrity strategy.

## 5.15 Visualization and reporting

**Proposed modules:** `visualization/plots.py`, `visualization/reports.py`

**Purpose:** Present and export scientific data and analysis outputs.

**Responsibilities:**

- Plot observations, molecular references, and derived spectra.
- Display units, axes, uncertainty information, and relevant dataset identity.
- Show candidate results and method diagnostics.
- Display warnings and limitations.
- Produce reports containing source attribution and analysis metadata.
- Export results without changing their scientific meaning.

**Inputs:**

- Validated spectral data.
- Comparison and candidate results.
- Provenance and analysis metadata.

**Outputs:**

- Plots and visual artifacts.
- Reports and exports.
- Presentation-ready result data.

**Dependencies:**

- Scientific plotting libraries.
- Domain and result models.
- UI integration where needed.

**Must not:**

- Independently rerun scientific calculations.
- Alter data silently for presentation.
- Hide missing measurements or uncertainty limitations.
- Label a candidate as a confirmed detection solely because of a score.

**Completion criteria:**

- Plots and reports identify the data and method represented.
- Units and uncertainty information are shown when available.
- Scientific limitations remain visible in exported results.

**Open decision:** Plotting library, report formats, and export capabilities.

## 5.16 Logging and diagnostics

**Proposed modules:** `diagnostics/`

**Purpose:** Support operational debugging and reliable error reporting.

**Responsibilities:**

- Configure application logging.
- Record useful diagnostics for acquisition, parsing, storage, and execution failures.
- Preserve error context across application-service boundaries.
- Support troubleshooting without exposing unnecessary sensitive information.
- Distinguish operational logs from scientific provenance.

**Inputs:**

- Structured diagnostic events.
- Exceptions and operation context.
- Application configuration.

**Outputs:**

- Operational logs.
- Diagnostic information for user-facing error handling.

**Dependencies:**

- Python logging facilities and relevant application components.

**Must not:**

- Substitute for persistent scientific analysis records.
- Claim that an operation succeeded based on its initiation alone.
- Expose credentials or unnecessary sensitive local information.
- Swallow exceptions without recording or appropriately handling them.

**Completion criteria:**

- Failures can be diagnosed without relying exclusively on console output.
- User-facing errors are useful without requiring raw stack traces.
- Scientific provenance remains stored with the corresponding data and analysis.

---

## 6. Provisional Interface Contracts

The following interfaces define important communication boundaries. They are illustrative typed Python signatures, not finalized implementation requirements.

Names, concrete return types, and exact fields must be reconciled with `DATA_MODELS.md` and the selected dependencies before implementation.

### 6.1 Interface conventions

- Use explicit input parameters rather than hidden application state.
- Return structured results for operations that may succeed with warnings or fail for expected reasons.
- Raise or propagate clearly defined exceptions for unexpected failures.
- Keep provider-specific response objects behind source adapters.
- Keep database-specific objects behind persistence implementations.
- Preserve method-specific scientific outputs rather than forcing every method into the same score schema.
- Do not introduce a generic abstraction unless at least one real workflow needs it.

### 6.2 Application-service boundary

A provisional application-service contract:

```python
class ECASApplicationService:
    def list_projects(self) -> list["ProjectSummary"]:
        ...

    def import_observation(
        self,
        file_path: "Path",
        planet_id: "PlanetId",
    ) -> "ImportResult":
        ...

    def retrieve_observation(
        self,
        source_id: str,
        observation_id: str,
        planet_id: "PlanetId",
    ) -> "ImportResult":
        ...

    def run_analysis(
        self,
        request: "AnalysisRequest",
    ) -> "AnalysisRun":
        ...

    def get_analysis(
        self,
        analysis_id: "AnalysisId",
    ) -> "AnalysisRun":
        ...
```

The names `ProjectSummary`, `PlanetId`, `ImportResult`, `AnalysisRequest`, `AnalysisId`, and `AnalysisRun` are provisional. Their definitions belong in the domain and data-model design.

The service coordinates operations; it does not implement the parser, scientific method, or database backend itself.

### 6.3 Source-adapter boundary

A source adapter should expose provider-independent operations.

```python
class ObservationSource:
    def search(
        self,
        query: "ObservationQuery",
    ) -> list["ObservationSummary"]:
        ...

    def retrieve(
        self,
        observation_id: str,
    ) -> "RetrievedDataset":
        ...
```

A reference source may provide a corresponding interface for searching and retrieving molecular references.

The actual contract must accommodate provider-specific identifiers and metadata without allowing provider-specific response structures to leak into the scientific services.

No particular provider or query schema is selected here.

### 6.4 Import and validation boundary

```python
class ObservationImporter:
    def parse(
        self,
        source: "DatasetSource",
    ) -> "ParsedDataset":
        ...


class DatasetValidator:
    def validate(
        self,
        dataset: "ParsedDataset",
    ) -> "ValidationReport":
        ...
```

Parsing and validation must remain distinguishable. A successful parse does not guarantee a valid dataset.

The exact validation requirements will depend on the supported formats and intended dataset role.

### 6.5 Comparability and preparation boundary

```python
class ComparabilityService:
    def assess(
        self,
        observation: "SpectralDataset",
        reference: "ReferenceDataset",
        method_requirements: "MethodRequirements",
    ) -> "ComparabilityReport":
        ...


class SpectralPreparationService:
    def prepare(
        self,
        dataset: "SpectralDataset",
        plan: "PreparationPlan",
    ) -> "PreparedSpectrum":
        ...
```

These signatures illustrate the boundary only. The final model must support different reference representations and method-specific input requirements.

Preparation must return a derived representation with traceable inputs and transformation history. It must not modify the original dataset.

### 6.6 Comparison-method boundary

The comparison interface is one of the most important stable boundaries because the first algorithm remains undecided.

A provisional contract is:

```python
from typing import Protocol


class ComparisonMethod(Protocol):
    @property
    def method_id(self) -> str:
        ...

    @property
    def version(self) -> str:
        ...

    def requirements(self) -> "MethodRequirements":
        ...

    def compare(
        self,
        observation: "PreparedSpectrum",
        reference: "PreparedReference",
        settings: "ComparisonSettings",
    ) -> "ComparisonResult":
        ...
```

This contract establishes that a method:

- Identifies itself and its version.
- Declares its input requirements.
- Receives prepared inputs and explicit settings.
- Returns a structured result.

It does not prescribe a score, algorithm, uncertainty model, or detection threshold.

The final contract must be reviewed against the first selected method and benchmark data. If methods require materially different input structures or produce different result types, the interface must accommodate those differences without misrepresenting them.

### 6.7 Persistence boundary

A provisional repository interface:

```python
class ProjectRepository(Protocol):
    def get(self, project_id: "ProjectId") -> "Project | None":
        ...

    def save(self, project: "Project") -> None:
        ...


class AnalysisRepository(Protocol):
    def get(self, analysis_id: "AnalysisId") -> "AnalysisRun | None":
        ...

    def save(self, analysis: "AnalysisRun") -> None:
        ...
```

These signatures illustrate separation between application logic and storage implementation.

Exact repository boundaries, update semantics, transaction ownership, and record identity rules will be defined alongside `DATA_MODELS.md`.

A repository must not silently replace the historical inputs associated with an analysis.

### 6.8 Interface finalization rules

Before implementation begins:

1. Resolve domain types and identifiers in `DATA_MODELS.md`.
2. Confirm the selected input formats and their parsing requirements.
3. Select the first comparison method after benchmark investigation.
4. Confirm that the comparison contract can represent its requirements and outputs.
5. Define persistence and artifact-reference semantics.
6. Remove provisional signatures that do not correspond to actual requirements.

Do not implement every illustrative signature solely because it appears in this document.

---

## 7. Data Ownership and State Changes

Modules must have clear ownership of the records and transformations they manage.

| Data or state | Primary owner | Rule |
|---|---|---|
| Original imported or retrieved payload | Ingestion and artifact storage | Preserve when permitted; do not mutate in place. |
| Parsed dataset | Ingestion | Maintain source linkage and parsing context. |
| Validation outcome | Validation services | Record status, errors, and warnings. |
| Registered observation | Domain, project, and persistence services | Preserve identity and planet association. |
| Shared molecular reference | Reference library and persistence services | Preserve reference type, source, and version. |
| Prepared spectrum | Spectral preparation | Treat as derived data linked to its inputs. |
| Comparison output | Comparison method and analysis workflow | Preserve method identity, version, and score meaning. |
| Candidate result | Scoring and analysis services | Preserve interpretation limits and supporting diagnostics. |
| Saved analysis | Application and persistence services | Retain exact input identities and settings. |
| Plot or report | Visualization and artifact storage | Preserve its relationship to the underlying analysis. |

No module may silently mutate another module's owned state outside its defined interface.

---

## 8. Cross-Module Error Handling

Expected failures should be represented in a way that the application service can handle without requiring knowledge of provider-specific or database-specific internals.

Examples include:

- `SourceUnavailableError`: a remote source cannot be reached or used.
- `UnsupportedFormatError`: an input format is not supported.
- `DatasetValidationError`: a dataset fails required validation.
- `IncompatibleDataError`: selected inputs do not satisfy a method's requirements.
- `PreparationError`: a required transformation cannot be completed.
- `ComparisonExecutionError`: the selected method fails to execute.
- `PersistenceError`: required records or artifacts cannot be saved.
- `MissingDependencyError`: a required local input or software dependency is unavailable.

These names are illustrative, not a finalized exception hierarchy.

Expected failures should carry useful context, such as the failed operation, affected dataset or analysis identifier where available, and actionable diagnostic details.

Rules:

1. Do not use a generic error message that conceals the failed stage.
2. Do not silently convert errors into empty results.
3. Do not label failed or partial analyses as successful.
4. Preserve completed work when safe.
5. Do not discard valid previous data because an update failed.
6. Avoid exposing credentials or unnecessary sensitive paths in user-facing reports.
7. Distinguish recoverable workflow failures from unrecoverable application startup failures.

---

## 9. Testing Responsibilities

Each module must be testable independently where practical.

### 9.1 Unit tests

Test domain invariants, validation rules, transformation behavior, comparison-method behavior, scoring logic, and repository-level logic without requiring the full desktop application.

### 9.2 Adapter tests

Test each supported archive adapter and file importer against documented source examples or controlled fixtures.

Network-dependent tests should be distinguishable from deterministic tests that can run without live services.

### 9.3 Integration tests

Test complete boundaries, including:

- Local import through validation and registration.
- Online retrieval through validation and registration.
- Reference acquisition through the shared reference library.
- Preparation and comparison through analysis persistence.
- Project reopening and retrieval of saved results.
- Artifact storage and integrity verification.

### 9.4 Offline tests

Verify that saved projects and results remain inspectable without network access.

Verify that eligible analyses can be rerun when their inputs and software dependencies are available locally, and that missing dependencies are reported explicitly.

### 9.5 Scientific validation tests

Evaluate comparison methods against the curated benchmark cases and procedures defined in `VALIDATION_STRATEGY.md`.

Software tests and scientific benchmark evaluations must remain distinct.

Synthetic fixtures may be used for bounded software tests when clearly labeled. They must not be presented as real astronomical observations or used as a substitute for real benchmark evidence.

---

## 10. Implementation-Agent Rules

These rules apply to agents implementing ECAS after implementation has been explicitly authorized.

### 10.1 Before starting work

Agents must:

1. Read `docs/ECAS.md` and the relevant approved architecture documents.
2. Read `docs/brains/PROJECT_STATE.md` and `docs/brains/DECISIONS.md` when present.
3. Inspect the actual workspace and existing code before proposing or creating modules.
4. Identify which requirements and interfaces are already implemented.
5. Confirm the assigned task and its scope.
6. Identify any unresolved decision that materially affects the assigned work.

Do not assume that the proposed package tree already exists.

### 10.2 While implementing

Agents must:

1. Work only within the authorized scope.
2. Respect module ownership and dependency rules.
3. Reuse existing implementations when they satisfy the requirement.
4. Avoid duplicate services, repositories, domain models, and abstractions.
5. Keep scientific operations independent of the UI.
6. Preserve provenance, uncertainty, units, and source identity.
7. Avoid hardcoding unresolved providers, algorithms, formats, or thresholds.
8. Add tests appropriate to the changed behavior.
9. Use actual source data and documented fixtures where scientific behavior is being assessed.
10. Document assumptions and stop for review when a material decision cannot be made safely.

A provisional signature or directory in this document is not permission to implement unrelated infrastructure.

### 10.3 When encountering a conflict

Agents must stop before making a material architectural change when:

- Existing code conflicts with an approved requirement.
- A required interface cannot represent the actual scientific method.
- A data transformation would change scientific meaning without a justified procedure.
- A task requires an unresolved algorithm, threshold, provider, or schema decision.
- The proposed work would modify unrelated modules or exceed the assigned scope.

Agents should report the conflict, relevant evidence, available options, and the specific decision required.

### 10.4 Completion and handoff

Every implementation task should conclude with a concise report containing:

- Summary of work completed.
- Files created or modified.
- Architectural boundaries affected.
- Tests executed and their actual outcomes.
- Any failures or unverified behavior.
- Decisions or assumptions made.
- Outstanding issues and recommended next steps.

Agents must distinguish implemented, tested, and verified behavior. They must not claim success for operations that were not executed or tests that were not run.

`PROJECT_STATE.md` should be updated only with verified project facts, according to the authorized workflow.

---

## 11. Open Decisions

The following decisions remain unresolved and must not be inferred from the provisional structure:

1. **Desktop UI:** framework, detailed view organization, and event-handling approach.
2. **Archive providers:** initial online sources, their APIs, and supported products.
3. **Local import:** initial formats, parser dependencies, and required metadata.
4. **Molecular references:** initial providers and the specific representations supported in the first release.
5. **Comparison method:** algorithm, method-specific requirements, and result structure.
6. **Scientific preparation:** required transformations, supported settings, and uncertainty handling.
7. **Domain models:** exact fields, identifiers, serialization, and relationships.
8. **Persistence:** database access library, schema, migrations, and transaction strategy.
9. **Artifact storage:** paths, cache policy, retention, and integrity verification.
10. **Validation:** benchmark cases, evaluation metrics, and threshold derivation.
11. **Packaging:** standalone packaging and installation strategy.
12. **Performance:** expected dataset sizes, execution time, and responsiveness requirements.

These decisions should be resolved only when the relevant evidence or implementation requirements are available.

---

## 12. Acceptance Criteria

The module design is ready for implementation planning when:

- [ ] Each major responsibility has a clear owner.
- [ ] The provisional package layout does not force unnecessary modules.
- [ ] UI, application services, scientific services, source adapters, and persistence remain separated.
- [ ] Local import and online retrieval converge on shared validation.
- [ ] Measured spectra, theoretical line lists, and synthesized products remain distinct.
- [ ] Comparability assessment precedes comparison execution.
- [ ] Preparation operations preserve source linkage and transformation history.
- [ ] Comparison methods can be integrated without coupling them to the UI or data providers.
- [ ] Method-specific scores and diagnostics retain their meanings.
- [ ] Project and analysis persistence preserves historical input identity.
- [ ] Interfaces communicate through defined inputs, outputs, and errors.
- [ ] Provisional signatures are reconciled with the finalized data models before implementation.
- [ ] Tests distinguish software correctness from scientific benchmark performance.
- [ ] Agent instructions require inspection, scoped changes, testing, and an honest handoff.
- [ ] Unresolved decisions are documented rather than silently assumed.

---

## 13. Relationship to Future Documents

This document establishes provisional module boundaries. It does not finalize every data structure or scientific procedure.

The next supporting documents should resolve the following:

| Document | Primary purpose |
|---|---|
| `DATA_MODELS.md` | Define domain entities, identifiers, relationships, required metadata, and persistence constraints. |
| `VALIDATION_STRATEGY.md` | Define benchmark selection, evaluation methods, threshold derivation, and limits of scientific claims. |
| `DECISIONS.md` | Record approved technical and architectural decisions with their rationale. |
| `PROJECT_STATE.md` | Record verified workspace state, implementation progress, and outstanding work. |

Once the data models and initial comparison requirements are better understood, the provisional interface signatures can be reviewed and narrowed to those actually needed.

---

**Draft conclusion:** This document provides a provisional module structure, responsibility boundaries, interface examples, and implementation-agent rules for ECAS. It is intended to guide consistent implementation while preserving flexibility around unresolved scientific and technical choices. It does not authorize code implementation or workspace modification.