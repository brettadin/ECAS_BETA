# ECAS Module Responsibilities

**Document status:** Draft for review  
**Project:** ECAS — Exoplanetary Characterization & Astrochemistry Suite  
**Related documents:** `ECAS.md`, `ARCHITECTURE.md`, `DATA_FLOW.md`, `DATA_MODELS.md`, `VALIDATION_STRATEGY.md`, `DECISIONS.md`, `PROJECT_STATE.md`  
**Implementation status:** This document defines proposed responsibilities and boundaries. It does not authorize implementation.

---

## 1. Purpose

This document defines the responsibilities, ownership boundaries, and dependency rules for ECAS software components.

Its purpose is to establish where functionality belongs, how components should interact, and which architectural boundaries must be preserved as the application develops.

The proposed architecture must support ECAS's scientific goals without implying that planned components already exist. Module boundaries are provisional and may be combined or refined when implementation evidence demonstrates a need.

### 1.1 Governing documents

- `docs/ECAS.md` defines project purpose, scientific principles, and long-term direction.
- `docs/architecture/ARCHITECTURE.md` describes the overall architecture and dependency rules.
- `docs/architecture/DATA_FLOW.md` describes the intended movement of data through ECAS.
- `docs/architecture/DATA_MODELS.md` defines domain entities, their relationships, and scientific metadata requirements.
- `docs/architecture/VALIDATION_STRATEGY.md` defines scientific benchmark and evaluation requirements.
- `docs/brains/DECISIONS.md` records approved decisions and their rationale.
- `docs/brains/PROJECT_STATE.md` records verified implementation status.

If these documents conflict, the discrepancy must be identified and reviewed rather than resolved through an undocumented assumption.

### 1.2 Current implementation and intended architecture

The supplied project state establishes an existing application with:

- A Python desktop interface using PySide6.
- CSV ingestion through the existing importer.
- A `SpectrumData` representation for imported spectral data.
- SQLite-backed persistence.
- A spectral data table and PyQtGraph visualization.
- Automated tests for ingestion, persistence, the interface, and plotting.

These capabilities form the foundation for future development. The current repository and latest implementation reports remain authoritative for the precise status of each feature.

The broader architecture described here includes capabilities that are not established as implemented, including general online source integration, molecular reference management, scientific comparability assessment, spectral preparation, comparison methods, benchmark evaluation, and comprehensive provenance tracking.

Those capabilities must be introduced incrementally, following explicit planning and approval.

---

## 2. Module design principles

### 2.1 Clear responsibility

Each component must have a defined purpose. Responsibilities should not be duplicated across the UI, application coordination, scientific processing, source integration, and persistence.

Related functionality may remain together when separating it would add complexity without improving maintainability, testability, or clarity.

### 2.2 Explicit inputs and outputs

Operations should receive required data and configuration explicitly and return defined results.

Components must not rely on hidden UI state, undocumented global state, or implicit side effects.

### 2.3 Scientific meaning must be preserved

ECAS must distinguish between:

- Astronomical observations, including exoplanet transmission spectra.
- Experimentally measured or experimentally derived molecular spectra.
- Theoretical spectroscopic line lists.
- Calculated or synthesized molecular spectra.
- Processed or otherwise derived datasets.

These categories may share carefully defined low-level numerical utilities, but they must not be forced into an undifferentiated scientific model that loses their meaning, provenance, units, or applicable assumptions.

### 2.4 Provenance must survive processing

Acquisition, import, transformation, calculation, comparison, and persistence must preserve the source identities and processing history necessary to interpret the resulting data.

Derived products must remain distinguishable from their source inputs.

### 2.5 Dependency direction

The UI initiates operations through application-level coordination. Source adapters handle external systems. Scientific services operate on explicit data objects. Persistence components manage stored records and artifacts.

Scientific algorithms must not depend on the UI, independently retrieve network data, or manage database writes.

### 2.6 Proportional architecture

Do not create modules, abstractions, registries, interfaces, or plugin systems solely because they appear in a proposed architecture.

Introduce them when they have a concrete responsibility and improve the implementation.

---

## 3. Proposed component organization

The following is a conceptual organization of responsibilities, not a required directory tree.

| Component area | Primary responsibility |
|---|---|
| Application entry point | Initialize and launch ECAS |
| Desktop UI | Present application state and collect user input |
| Application services | Coordinate user-requested workflows |
| Domain models | Represent scientific data and application entities |
| Ingestion and validation | Parse supported local inputs and perform structural checks |
| Source adapters | Retrieve data from explicitly supported external providers |
| Molecular reference library | Organize and resolve molecular reference datasets |
| Scientific comparability | Determine whether selected inputs satisfy a method's requirements |
| Spectral preparation | Apply documented transformations when required |
| Comparison methods | Execute the selected scientific comparison |
| Scoring and evaluation | Represent candidate outputs and evaluate methods against benchmarks |
| Project management | Coordinate project lifecycle and project-specific records |
| Persistence | Store and retrieve structured records |
| Artifact storage and cache | Manage source files, derived artifacts, and reusable downloaded data |
| Visualization and reporting | Display supplied data and results with appropriate context |
| Logging and diagnostics | Record operational events and failures |
| Tests | Verify software behavior and scientific evaluation requirements |

These responsibilities do not require a separate Python module for every row. Existing modules should be extended where appropriate, and new modules should be introduced only when their ownership is clear.

---

## 4. Responsibilities and boundaries

### 4.1 Application entry point and initialization

**Responsibility:** Start the application and initialize the dependencies required by the selected workflow.

The entry point should:

- Initialize the desktop application.
- Construct the main window and required application services.
- Load necessary configuration.
- Configure application-level logging where applicable.
- Handle startup failures appropriately.

It must not contain scientific algorithms, provider-specific retrieval logic, or substantive persistence operations.

The authoritative launch path must be verified against the current repository before it is changed.

### 4.2 Desktop UI

**Responsibility:** Present information and collect user input.

The UI should:

- Display projects, observations, molecular references, and results when those capabilities are implemented.
- Collect user selections and workflow parameters.
- Display imported data and plots.
- Present validation errors, warnings, compatibility limitations, and operation status.
- Show provenance and scientific metadata supplied by application services.
- Distinguish unavailable operations from operations that failed.

The existing PySide6 interface and PyQtGraph plotting component are part of the current foundation.

The UI must not:

- Parse external provider responses independently.
- Query SQLite directly.
- Perform scientific comparisons inside view code.
- Invent missing metadata or units.
- Present a failed or incomplete operation as successful.
- Independently reinterpret numerical scores as scientific detections.

UI components should display results supplied by the relevant application or scientific services.

### 4.3 Application services

**Responsibility:** Coordinate complete user-requested operations across components.

Application services may coordinate workflows such as importing a dataset, retrieving an observation, registering a reference, or running a comparison.

They should:

1. Receive explicit user selections and configuration.
2. Invoke the appropriate ingestion, source, validation, or scientific services.
3. Check that required stages have succeeded.
4. Coordinate persistence and artifact handling.
5. Return a result that communicates success, failure, warnings, and relevant identifiers.

Application services should not duplicate parsing, scientific algorithms, or database implementation details.

They are a proposed architectural responsibility. Their exact module boundaries should follow the existing code and the needs of the first integrated workflow.

### 4.4 Domain models

**Responsibility:** Represent application entities and preserve their scientific meaning.

Domain models may include planets, projects, observations, molecular references, prepared datasets, analyses, candidate results, and validation records.

Models should express the information necessary to identify and interpret an entity without depending on the desktop UI or a particular storage implementation.

The existing `SpectrumData` model must remain supported while the architecture evolves. It must not be assumed to represent every future data category adequately.

Before extending the model, determine which additional fields and representations are required and whether a distinct model is scientifically necessary.

In particular, a molecular line list must not be represented as a continuous measured spectrum merely because both contain numerical values.

Final entities, fields, relationships, and identity rules belong in `DATA_MODELS.md`.

### 4.5 Ingestion and structural validation

**Responsibility:** Convert supported local inputs into defined internal representations and identify structural problems.

Ingestion components should:

- Recognize supported file formats and schemas.
- Parse the selected source representation.
- Preserve original column information and available metadata.
- Identify malformed, missing, or ambiguous values.
- Produce explicit errors and warnings.
- Return structured data suitable for subsequent validation and registration.

The existing CSV importer is the foundation for local-file ingestion. Its supported schema must not be generalized to arbitrary CSV or TXT formats without evidence and explicit support.

Structural validation must remain distinct from scientific comparability assessment.

A dataset can be structurally valid but scientifically unsuitable for a particular analysis. Conversely, a dataset that fails required structural checks must not be treated as a valid input.

### 4.6 External source adapters

**Responsibility:** Isolate provider-specific retrieval and response handling.

Source adapters should handle the external details of a supported provider, including:

- Query construction and record discovery.
- Network requests and authentication where required.
- Provider response formats.
- Downloaded file handling.
- Provider identifiers and available metadata.
- Source URLs, citations, version information, and retrieval details.
- Provider-specific failures and access limitations.

Provider adapters must not contain UI behavior, project-specific presentation logic, or comparison algorithms.

Astronomical observation providers and molecular reference providers have different scientific data contracts. They should have distinct retrieval interfaces when their operations and returned data differ materially. Shared HTTP, download, or error-handling utilities may be introduced where justified.

Do not implement a generalized multi-provider framework before the first provider demonstrates what the shared interface actually needs.

The initial provider selection and retrieval scope are separate decisions to be made during Chunk 4 planning.

### 4.7 Molecular reference library

**Responsibility:** Organize and resolve molecular reference datasets independently of individual planet projects.

The library should eventually support:

- Molecular identity and relevant identifiers.
- Discovery of available reference datasets.
- Distinguishing measured spectra, theoretical line lists, and calculated spectra.
- Reference provenance, conditions, units, and limitations.
- Selection of an appropriate reference for a requested operation.
- Reuse of locally cached reference data.
- Identification of specific reference versions used by an analysis.

The library must not assume that a molecule's presence in a catalog guarantees that a suitable reference dataset is available.

It must also not imply that laboratory measurements, line lists, and synthesized spectra are interchangeable.

The initial library implementation should be limited to the requirements of the first supported reference source.

### 4.8 Scientific comparability assessment

**Responsibility:** Determine whether selected data satisfy the compatibility requirements of a particular operation.

The assessment should consider relevant factors such as:

- Spectral coordinate definitions and units.
- Signal meaning and units.
- Spectral coverage and sampling.
- Resolution and processing state.
- Available uncertainty information.
- Quality limitations.
- Reference representation and applicable conditions.
- Method-specific requirements.

The service should return an explicit outcome, such as compatible, compatible with limitations, conditionally compatible, incompatible, or undetermined.

It should explain the reason for a restricted or negative outcome where practical.

Comparability assessment must not be replaced by a check that two arrays have matching dimensions or contain numerical values.

This capability is proposed and is not implied to exist in the current importer or plotting workflow.

### 4.9 Spectral preparation

**Responsibility:** Apply explicitly defined transformations required by a selected scientific operation.

Potential transformations include unit conversion, spectral-region selection, resampling, resolution matching, normalization, and quality filtering.

Only transformations justified by the selected workflow should be implemented.

Preparation components should:

- Accept explicit input datasets and parameters.
- Preserve the original source data.
- Record the transformation and its settings.
- Preserve or explicitly account for uncertainty information.
- Identify the resulting data as derived.
- Report assumptions, limitations, and failures.

Preparation must not silently change scientific meaning or make incompatible quantities appear comparable.

The initial transformation set depends on the first comparison method and its benchmark evidence.

### 4.10 Comparison methods

**Responsibility:** Execute a defined scientific comparison on eligible inputs.

A comparison method should consume validated inputs and explicit configuration, then return a defined result containing the outputs and diagnostics supported by that method.

It must not:

- Retrieve external data.
- Parse provider-specific files.
- Manipulate desktop UI state.
- Independently manage project persistence.
- Claim scientific conclusions beyond the method's documented capabilities.

Method identity, version, configuration, input identities, and relevant diagnostics must be available to the surrounding workflow for persistence.

The first production comparison method remains subject to scientific investigation and approval. No particular algorithm is established by this document.

### 4.11 Candidate scoring and scientific evaluation

**Responsibility:** Represent candidate outputs and assess the performance of implemented methods.

Candidate scoring must preserve the meaning of the underlying method outputs. A score must not automatically be interpreted as a probability, detection confidence, or abundance estimate.

Scientific evaluation should manage benchmark definitions, evaluation metrics, test configurations, and recorded performance.

Benchmark evaluation must remain distinguishable from ordinary software unit tests.

The validation strategy must establish appropriate benchmarks and criteria before performance claims are made. The module boundaries must not predetermine arbitrary thresholds.

### 4.12 Project management

**Responsibility:** Coordinate the lifecycle and organization of a planet-specific research project.

A project may contain multiple observations, analysis runs, references used, and associated artifacts.

Project management should coordinate creation, opening, listing, and other project-level operations where implemented.

It must preserve the relationship between a project and its observations and analyses without duplicating the responsibilities of the persistence layer.

Project management should not contain provider-specific retrieval logic or scientific comparison algorithms.

The current persistence implementation must be inspected before deciding whether existing project-related operations already satisfy some of these responsibilities.

### 4.13 Structured persistence

**Responsibility:** Store and retrieve structured application records.

SQLite is the established persistence direction.

The persistence layer should eventually support the structured records required by implemented workflows, including dataset metadata, projects, analysis configurations, results, and relationships as those entities are introduced.

It should:

- Provide defined storage operations.
- Preserve supported model fields and relationships.
- Handle missing records and storage failures explicitly.
- Protect data integrity during updates.
- Support historical analysis inputs without silently replacing them.
- Avoid embedding scientific interpretation in database operations.

The existing persistence implementation must be preserved and extended only as required by approved data-model changes.

A final schema, migration strategy, and complete provenance record are not established by this document.

### 4.14 Artifact storage and caching

**Responsibility:** Manage files and reusable data that do not belong directly in structured database records.

Potential artifacts include original downloaded files, prepared datasets, calculated spectra, plots, and exported reports.

Caching should support repeat access and offline use where the required data remain available.

Cache identity must be based on stable source identifiers and relevant version or content information, rather than filenames alone.

Cache operations must distinguish successful retrievals from incomplete downloads and failed requests. A failed refresh must not silently replace a valid cached dataset.

Original source artifacts and normalized internal data must remain distinguishable and linked through provenance.

The exact storage paths, cache invalidation rules, retention policy, and transaction behavior remain open design decisions.

### 4.15 Visualization and reporting

**Responsibility:** Present data and analysis outputs for inspection.

Visualization should display the supplied coordinates, values, units, and available metadata without altering the underlying scientific inputs.

Reporting should present results alongside the provenance, assumptions, warnings, and limitations needed to interpret them.

Plotting code must not independently perform scientific comparison or infer missing units.

The current PyQtGraph plotting component is an existing capability. Additional comparison plots and reports are future work unless verified otherwise.

### 4.16 Logging and diagnostics

**Responsibility:** Record operational events and useful diagnostic information.

Diagnostics should support investigation of acquisition, parsing, validation, processing, analysis, and persistence failures.

Errors should retain enough context to identify the failed operation and its cause where possible.

Logs must not expose secrets, credentials, or unnecessary sensitive information.

Logging should complement user-facing error reporting rather than replace it.

---

## 5. Dependency rules

The intended dependency direction is:

```text
Desktop UI
    |
    v
Application Services
    |
    +--------------------------+
    |                          |
    v                          v
Ingestion / Source Services   Project Services
    |                          |
    +-------------+------------+
                  |
                  v
        Domain Data Contracts
                  |
          +-------+-------+
          |               |
          v               v
  Scientific Services   Persistence
          |               |
          v               v
   Prepared Results    Stored Records
```

This diagram is conceptual. It does not require every operation to pass through every component.

The following rules govern the boundaries:

1. The UI calls application-level operations and displays their results.
2. The UI does not directly access SQLite or external provider APIs.
3. Source adapters do not depend on UI components or comparison implementations.
4. Domain models do not depend on the UI framework or concrete persistence implementation.
5. Scientific services operate on defined data objects and explicit settings.
6. Scientific services do not perform hidden network retrieval or independent database writes.
7. Comparison methods do not depend on provider-specific file formats.
8. Persistence components store and retrieve records without independently interpreting scientific conclusions.
9. Visualization presents supplied data and results rather than recomputing scientific conclusions.
10. Application services coordinate workflows without duplicating the logic of the services they call.
11. Dependencies must not form circular imports or circular architectural ownership.
12. New interfaces must solve a demonstrated separation or testing problem rather than exist solely for hypothetical future providers.

Where a dependency violates these rules, correct the ownership or introduce the smallest useful interface.

---

## 6. Cross-component data and error contracts

Components exchanging scientific data must preserve the distinction between source data, normalized representations, validated inputs, and derived products.

Where available and applicable, the workflow must preserve:

- Source and record identity.
- Original filename or source artifact reference.
- Target or molecule identity.
- Spectral coordinate and units.
- Signal meaning and units.
- Uncertainty and quality information.
- Source citations and retrieval details.
- Dataset version or content identity.
- Processing history and relevant assumptions.

Unavailable metadata must remain distinguishable from supplied, inferred, or calculated metadata.

Components should communicate errors using explicit outcomes or well-defined exceptions appropriate to the operation. Exact types and structures should be specified when implementing the relevant interface.

At minimum, the workflow must distinguish:

- Invalid or unsupported input.
- Missing or ambiguous required metadata.
- Source or network failure.
- Scientific incompatibility.
- Missing processing capability.
- Failed or incomplete analysis.
- Persistence or artifact-storage failure.

A failed stage must not produce an outcome that falsely indicates successful completion.

---

## 7. Interface design rules

Interfaces should be finalized alongside the first concrete workflows and their data requirements.

When defining an interface:

1. Identify its owner and responsibility.
2. Specify its inputs and outputs.
3. Define expected failure conditions.
4. Identify which metadata and provenance must survive the operation.
5. Specify whether the operation has side effects.
6. Identify the tests that verify its contract.
7. Avoid adding parameters or abstractions for unsupported future use cases.

Provider interfaces should be informed by the first real source integration. Scientific method interfaces should be informed by the selected method and benchmark requirements.

Do not finalize a universal interface before the relevant data contracts and workflows are understood.

---

## 8. Testing responsibilities

Testing should be organized around observable behavior and component boundaries.

| Test category | Primary responsibility |
|---|---|
| Unit tests | Verify individual model, parsing, validation, and processing behavior |
| Provider adapter tests | Verify response parsing, metadata extraction, and provider-specific error handling |
| Persistence tests | Verify round trips, integrity, missing records, and failure behavior |
| Integration tests | Verify interactions between components in an actual workflow |
| Offline tests | Verify operations using saved data without unnecessary network access |
| Scientific benchmark tests | Evaluate implemented methods against documented scientific cases |
| UI tests | Verify user-facing behavior, errors, and integration with application services |

Provider parsing tests should primarily use deterministic fixtures. Live-source verification must be recorded separately and must not be inferred from fixture-based tests.

Scientific benchmark performance must not be inferred from ordinary unit-test success.

The existing test suite must continue to cover established import, persistence, interface, and plotting behavior as new functionality is added.

---

## 9. Implementation-agent rules

Agents working on ECAS must:

1. Inspect the current repository and relevant tests before assuming a module exists.
2. Read the applicable architecture documents and approved decisions.
3. Distinguish existing implementation from proposed responsibilities.
4. Follow the approved task scope and avoid unrelated refactoring.
5. Preserve scientific meaning, provenance, and uncertainty information.
6. Introduce modules only when they have a defined responsibility.
7. Avoid duplicating functionality already implemented elsewhere.
8. Identify conflicts with approved decisions before changing architectural boundaries.
9. Report actual changes, test commands, results, and unresolved issues.
10. Update project-state and decision records only when the relevant information has been verified or approved.

This document does not authorize creating the proposed package structure or implementing the listed future capabilities.

---

## 10. Open decisions

The following matters must be resolved through the relevant planning work rather than assumed here:

1. The exact module boundaries needed by the first real source integration.
2. The initial astronomical provider and molecular reference provider.
3. The minimum distinct data representations required for supported scientific data categories.
4. The first comparison method and its input/output contract.
5. The required preparation operations and comparability rules.
6. The final persistence schema and migration strategy.
7. The minimum reproducibility and provenance record.
8. Cache identity, refresh, retention, and offline behavior.
9. The appropriate location and scope of application-service coordination.
10. Any additional abstractions justified by implementation experience.

These decisions should be resolved incrementally, with the smallest design that satisfies the current workflow.

---

## 11. Acceptance criteria

This document is suitable for implementation planning when:

- Current capabilities are distinguished from proposed components.
- Each component has a clear primary responsibility.
- UI, source retrieval, scientific processing, and persistence boundaries are explicit.
- The existing application can evolve without requiring a wholesale rewrite.
- Scientific data categories and their metadata are preserved.
- Provider-specific behavior is isolated from scientific comparison methods.
- Persistence and caching responsibilities are distinguishable.
- Failure handling and testing ownership are defined.
- Open decisions remain explicitly unresolved until supported by evidence.
- The proposed structure does not require unnecessary modules or premature abstractions.

---

## 12. Relationship to other documents

Use this document with:

- `ECAS.md` for project purpose and scientific principles.
- `ARCHITECTURE.md` for overall architecture and dependency direction.
- `DATA_FLOW.md` for workflow stages and data movement.
- `DATA_MODELS.md` for entities, relationships, identifiers, and required metadata.
- `VALIDATION_STRATEGY.md` for benchmark design and scientific evaluation.
- `DECISIONS.md` for approved decisions and rationale.
- `PROJECT_STATE.md` for verified implementation status.

This document defines proposed module responsibilities. It does not replace the data-flow specification, establish final data schemas, select a scientific algorithm, or authorize implementation.

**Conclusion:** ECAS should evolve through small, testable components with clear ownership and explicit contracts. The architecture must preserve scientific meaning and traceability while remaining proportional to the requirements of the first supported workflow.
