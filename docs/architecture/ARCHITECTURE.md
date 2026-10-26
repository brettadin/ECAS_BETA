# ECAS Architecture

**Document status:** Draft for user review  
**Project:** Exoplanetary Characterization & Astrochemistry Suite (ECAS) 
**Primary language:** Python  
**Implementation status:** Architecture proposal; implementation status is tracked separately in `docs/brains/PROJECT_STATE.md`
**Authority:** Proposed detailed architecture consistent with `docs/ECAS.md` and *ECAS Architecture Specification — Draft 0.3*

---

## 1. Purpose

This document describes the proposed software architecture for ECAS: a Python desktop application for investigating exoplanet atmospheres using real, traceable scientific data.

The initial application will focus on exoplanet transmission spectra and molecular reference data. It will support online archive retrieval and local-file import, preserve source data and provenance, provide a pluggable framework for spectral comparison and candidate scoring, and organize research under one project per planet.

This is an architectural design, not an implementation plan for every future capability. It defines responsibilities, boundaries, and constraints while leaving decisions that require later evidence explicitly unresolved.

### 1.1 Relationship to other project documents

- `docs/ECAS.md` defines the project's purpose, scientific principles, and long-term direction.
- `docs/architecture/ARCHITECTURE.md` defines the system structure and major design rules.
- `docs/architecture/DATA_FLOW.md` will detail the movement and transformation of data.
- `docs/architecture/MODULE_RESPONSIBILITIES.md` will define module ownership and interfaces.
- `docs/architecture/DATA_MODELS.md` will define conceptual entities, relationships, and required metadata.
- `docs/architecture/VALIDATION_STRATEGY.md` will define benchmark selection and evaluation.
- `docs/brains/DECISIONS.md` will record approved decisions and rationale.
- `docs/brains/PROJECT_STATE.md` will record verified current project state.

If documents conflict, do not silently choose one. Identify the conflict and request a decision. The master blueprint's scientific principles remain governing requirements unless the user explicitly changes them.

## 2. Scope

### 2.1 Initial release

The initial release is intended to support one end-to-end workflow:

1. Find or identify an exoplanet.
2. Retrieve a transmission-spectrum observation from a supported archive or import a local file.
3. validate the input structure, metadata, units, and basic scientific suitability.
4. Preserve the original input and record its provenance.
5. Find or retrieve molecular reference datasets.
6. Distinguish measured or experimentally derived spectra from theoretical line lists.
7. Assess whether selected observation and reference data can be meaningfully compared.
8. Prepare comparison inputs through explicit, documented transformations where required.
9. Execute a selected comparison method through a common method interface.
10. Present candidate scores, diagnostics, warnings, and citations without overstating the evidence.
11. Save the analysis under the planet's project so it can be reopened and, when its dependencies are available, rerun offline.

The initial comparison algorithm, first benchmark cases, initial archive providers, supported local file formats, and desktop UI framework are not selected by this document.

### 2.2 Explicitly outside the initial scope

Unless separately approved, the initial architecture does not require:

- Quantitative atmospheric abundance estimation.
- Full atmospheric retrieval or Bayesian inference.
- A general-purpose radiative-transfer engine.
- Support for every archive, instrument, molecular database, or file format.
- Automatic confirmation of molecular detections based on a similarity score.
- Standalone packaging before the application workflow stabilizes.
- Distributed processing, cloud services, or a client-server architecture.
- A large plugin marketplace or arbitrary third-party executable plugins.

The architecture should permit justified future extensions without implementing speculative abstractions now.

## 3. Requirements, decisions, and verification

This section connects ECAS's requirements to the mechanisms needed to satisfy them and the evidence needed to verify them. A requirement is not considered implemented merely because its intended mechanism is documented.

The table distinguishes established project requirements from proposed architectural mechanisms. Detailed implementation choices must be recorded in `docs/brains/DECISIONS.md` when approved. Verified implementation status belongs in `docs/brains/PROJECT_STATE.md`.

### 3.1 Requirements and verification criteria

| Area | Requirement | Mechanisms to specify or implement | Verification criteria |
|---|---|---|---|
| Scientific integrity | Scientific data and conclusions must retain their meaning and limitations. | Preserve provenance, distinguish measured, experimentally derived, theoretical, synthesized, and processed data, and prevent unsupported interpretations of comparison scores. | Tests verify data-category distinctions and provenance retention; scientific claims are evaluated separately against suitable evidence. |
| Data provenance | Every imported or retrieved dataset must be traceable to its source. | Record available source identifiers, citations, retrieval or import details, versions, and processing history. Preserve original inputs where permitted. | A stored dataset can be traced to its recorded source; derived data can be traced to its inputs and transformations. |
| Input integrity | Malformed or ambiguous input must not silently become trusted scientific data. | Apply format-specific parsing, structural validation, explicit missing-value handling, unit and metadata checks, and clear error reporting. | Tests cover malformed input, missing fields, non-finite values, inconsistent array lengths, and unsupported formats where applicable. |
| Data identity | Distinct observations and dataset versions must remain distinguishable. | Use stable identifiers and, where appropriate, content hashes and source-version metadata. Do not use filenames alone as identity. | Distinct observations remain separately identifiable; changed datasets do not silently replace historical analysis inputs. |
| Persistence integrity | Stored records and artifacts must remain internally consistent. | Validate records before saving, use appropriate database constraints, define transaction boundaries, and handle failed writes and artifact operations explicitly. | Tests cover invalid records, failed writes, retrieval, and consistency between stored records and referenced artifacts. |
| Reproducibility | An analysis must identify the inputs and configuration that produced its result. | Record input identities or versions, processing steps, method and version, settings, relevant software version, outputs, status, and limitations. | A saved analysis exposes its required inputs and settings; reruns can identify missing or changed dependencies rather than silently substituting data. |
| Scientific comparability | Structural validity must not be mistaken for scientific compatibility. | Assess relevant units, spectral quantities, wavelength or frequency coverage, resolution, uncertainty, normalization, and other method-specific requirements before comparison. | Tests distinguish structurally invalid data from valid but incompatible data; warnings and rejection reasons are explicit. |
| Comparison and scoring | Comparison outputs must not imply stronger scientific conclusions than their methods support. | Preserve method-specific score definitions, diagnostics, uncertainty information where justified, and limitations. Keep scoring separate from scientific validation. | Tests verify output interpretation and failure handling; benchmark evaluation supports any claimed performance or threshold. |
| Thresholds and validation | Numerical thresholds must have a defensible basis. | Define the intended decision, select suitable benchmark cases, document metric behavior and uncertainty, and separate threshold selection from independent evaluation where feasible. | Thresholds have documented rationale and supporting evidence; limitations of the benchmark and resulting claims are reported. |
| Persistence and offline work | Saved research should remain usable without unnecessary dependence on live services. | Separate persistent project records from external retrieval; identify local dependencies and report unavailable inputs or services. | Offline tests demonstrate the explicitly supported workflows using locally available inputs and dependencies. |
| User interface | The interface must present scientific information without owning scientific logic. | Keep scientific operations and data-provider parsing outside UI code; display source information, units, warnings, and limitations clearly. | Scientific logic can be tested independently of the UI; critical user workflows report failures without presenting them as successful results. |
| UI technology | The current application uses PySide6 for its desktop interface and PyQtGraph for spectral plotting.	| Keep UI code separate from scientific processing and persistence. Record any future framework change as an explicit decision.	| Confirm the documented frameworks match the implementation and test critical UI and plotting workflows. |
| Scope control | Implementation must follow approved priorities rather than the entire long-term vision. | Define feature-specific scope, acceptance criteria, dependencies, and verification before implementation. Record unresolved decisions explicitly. | Each task is reviewed against its approved scope and acceptance criteria before being declared complete. |

### 3.2 Current implementation versus target architecture

The requirements above describe the intended system, not a claim that every mechanism already exists.

The supplied project snapshot establishes a narrower current application, including a Python desktop interface, spectral visualization, SQLite-backed persistence, and CSV ingestion with support for a specific WASP-39 b archive schema. The exact current state must be confirmed against the working repository and its latest verification results.

The following remain architectural goals unless separately verified:

- General-purpose support for multiple scientific file formats.
- Online archive and molecular-reference retrieval.
- A complete provenance and dataset-versioning system.
- Generalized persistence and artifact-integrity safeguards.
- Comprehensive comparability assessment and spectral preparation.
- A selected, scientifically validated comparison method and defensible candidate thresholds.
- Reproducible analysis records and complete offline reruns.

### 3.3 Decision authority

This document defines architectural requirements and proposed mechanisms. It does not independently authorize implementation or establish that a particular mechanism has been approved.

- `docs/brains/DECISIONS.md` records approved decisions and their rationale.
- `docs/brains/PROJECT_STATE.md` records verified implementation status and outstanding work.
- `docs/architecture/DATA_MODELS.md` defines conceptual data entities, identity, relationships, and persistence constraints.
- `docs/architecture/DATA_FLOW.md` describes how data moves through the workflow and where validation and provenance controls apply.
- `docs/architecture/VALIDATION_STRATEGY.md` defines benchmark methodology, evaluation metrics, threshold derivation, and scientific-claim limitations.

When a mechanism remains unresolved, identify the decision needed rather than presenting an unapproved design as settled.


## 4. Architectural principles

### 4.1 Separate presentation from science

The desktop UI presents information and collects user choices. It must not implement spectral comparison, scoring, scientific validation, or data-provider parsing.

Scientific operations must be callable and testable without starting the UI.

### 4.2 Use explicit application workflows

Application services coordinate user workflows: validating prerequisites, requesting data, invoking scientific operations, saving results, and reporting failures. They should not duplicate the scientific logic or provider-specific parsing they coordinate.

### 4.3 Isolate external systems

Archive and reference-source integrations belong behind source-specific adapters. Provider details, network protocols, response formats, and provider errors must not leak throughout the application.

### 4.4 Preserve scientific meaning

Data structures must make clear what a spectral value represents, which units apply, and whether data are observed, measured, processed, calculated, or synthesized. The architecture must not make incompatible quantities appear interchangeable.

### 4.5 Preserve source and history

Original downloaded or imported files should remain distinguishable from parsed, normalized, processed, and synthesized derivatives. Transformations must be documented and reproducible.

### 4.6 Make analysis reproducible

An analysis record must identify its inputs, data versions or content identities, processing steps, method and version, settings, relevant software version, outputs, warnings, and limitations.

### 4.7 Support offline work by design

Core project browsing, viewing saved results, and rerunning analyses must not require live archive access when all required inputs and dependencies are available locally.

### 4.8 Prefer the simplest adequate structure

The proposed components below are responsibility boundaries, not a requirement to create one Python package or file per item. Combine responsibilities when separation would add ceremony without improving testability, clarity, or future change.

## 5. High-level architecture

ECAS is organized into logical layers. These layers describe responsibility and dependency direction, not a requirement that every operation pass through every layer.

```text
┌─────────────────────────────────────────────────────────┐
│                    Desktop UI                           │
│ Projects · Planet search · Data library · Analysis views│
└───────────────────────────┬─────────────────────────────┘
                            │ user actions / view models
┌───────────────────────────▼─────────────────────────────┐
│               Application Services                      │
│ Workflow coordination · Preconditions · Error handling  │
└───────────────┬───────────────────────────┬─────────────┘
                │                           │
┌───────────────▼────────────────┐  ┌───────▼─────────────┐
│       Scientific Services      │  │ Project/Data Services│
│ Validation · Preparation      │  │ Projects · Cache     │
│ Comparison · Scoring          │  │ Metadata · Storage   │
│ Evaluation                    │  │ Provenance            │
└───────────────┬────────────────┘  └───────┬─────────────┘
                │                           │
┌───────────────▼───────────────────────────▼─────────────┐
│             Domain Models and Interfaces                │
│ Planet · Project · Observation · Reference · Analysis   │
└───────────────────────────┬─────────────────────────────┘
                            │ adapters / persistence
┌───────────────────────────▼─────────────────────────────┐
│       External Sources and Local Persistence            │
│ Archives · Local files · SQLite · Data files · Cache    │
└─────────────────────────────────────────────────────────┘
```

The diagram is conceptual. For example, application services use data services to acquire inputs and then invoke scientific services; scientific services should not directly issue network requests or manipulate UI widgets.

## 6. Component responsibilities

### 6.1 Desktop UI

Responsible for:

- Planet and project navigation.
- Searching and browsing available observations and molecular references.
- Local-file selection and import feedback.
- Analysis configuration and progress presentation.
- Plots, result tables, warnings, and source information.
- Project notes and review of previous analyses.

Constraints:

- Must not contain scientific algorithms.
- Must not query SQLite directly.
- Must not independently reinterpret scores or calculate new scientific conclusions.
- Must present unavailable data, compatibility warnings, and analysis limitations clearly.

The UI framework will be selected after dependency and workflow review. No framework is mandated here.

### 6.2 Application services

Responsible for coordinating use cases such as:

- Find a planet and list available observations.
- Import or retrieve an observation.
- Validate and register a dataset.
- Search for and acquire a molecular reference.
- Prepare and execute a comparison.
- Save and reopen a planet project.
- Rerun a saved analysis.
- Run a supported validation workflow.

Application services check preconditions, coordinate transactions and operations, and convert lower-level failures into useful application-level outcomes. They should remain thin enough that scientific logic is reusable outside the UI.

### 6.3 Source adapters and ingestion

Source adapters communicate with individual online archives or reference providers. They encapsulate provider-specific search, download, authentication if needed, rate limits, response formats, and error behavior.

Local-file import is another ingestion route, not a special bypass around validation. Import handlers should support only explicitly documented formats and should report ambiguous or missing metadata instead of silently inventing it.

Ingestion should preserve the original file or source payload where permitted, create a source/provenance record, parse a supported representation, and submit the parsed dataset to validation. Network retrieval and local import should converge on shared validation and registration workflows.

### 6.4 Data validation and spectral preparation

These responsibilities should be distinguishable even if initially implemented together.

**Input validation** checks structural and metadata requirements, such as:

- File or response parsing succeeded.
- Required spectral coordinates and values are present.
- Coordinate and signal units are identified or explicitly marked unknown.
- Coordinates and values have compatible lengths.
- Invalid, missing, duplicate, or non-finite values are identified.
- Available uncertainties and quality flags are retained.
- Provenance is recorded.

**Comparability assessment** checks whether a particular observation/reference pair is suitable for the selected method. Relevant factors may include spectral quantity, axis units, coverage, resolution, normalization, uncertainty availability, and the reference's physical conditions.

**Spectral preparation** performs method-required operations such as unit conversion, masking, resampling, resolution matching, or normalization. Each operation must be explicit, scientifically justified, and recorded. Original inputs remain unchanged.

A dataset can be structurally valid but unsuitable for a specific comparison. ECAS must report these as different outcomes.

### 6.5 Molecular reference library

The reference library manages molecular identities, dataset discovery, metadata, local availability, and reference selection.

It must distinguish at least:

1. Measured or experimentally derived spectral products.
2. Theoretical spectroscopic line lists.
3. Spectra synthesized from line lists or other model inputs.
4. Other derived products, where supported.

For measured or experimentally derived spectra, retain reported measurement conditions, spectral quantity and units, resolution, uncertainty, processing status, source, and limitations when available.

For theoretical line lists, retain the source dataset and version plus the transition data and relevant molecular metadata. If a continuous spectrum is synthesized, record the synthesis method, physical assumptions, line-profile treatment, and resolution settings. A synthesized product must never be labeled as a direct experimental measurement.

Shared references should normally be stored in the central cache/library and referenced by projects, not duplicated into every project.

### 6.6 Exoplanet and observation catalog

This component manages planet identity, aliases, host-star context where relevant, and links to observation records.

Planet catalog information must remain distinct from observation data. The existence of a planet record does not imply that a usable transmission spectrum exists.

Each observation remains a separate scientific record with its own source, instrument and observation metadata, wavelength coverage, uncertainties, processing history, and data version. Multiple observations must not be merged in a way that erases their identities.

### 6.7 Comparison engine

The comparison engine exposes a stable contract for independently implemented comparison methods.

A method should receive validated, prepared inputs and explicit settings. It must not be responsible for retrieving online data, reading UI state, or directly saving project records.

The interface should support method-specific requirements and outputs without pretending that all methods calculate the same kind of score. A correlation coefficient, a residual statistic, and a line-feature score have different meanings and must retain their definitions.

The first method will be selected after reviewing accessible benchmark observations, spectral resolution, noise, coverage, reference representations, and intended use. This document does not select an algorithm or numerical threshold.

A method result should identify the method and version, inputs, settings, scores and their meanings, diagnostic outputs, warnings, limitations, and uncertainty/significance information only where the method actually supports it.

### 6.8 Scoring, evaluation, and validation

Candidate scoring translates a comparison method's outputs into documented candidate-level results. It must not convert an arbitrary score into a detection probability or a definitive detection label.

Validation evaluates methods against curated benchmark cases based on published detections, suitable non-detections, or controls. Benchmark selection, metrics, thresholds, and the separation of tuning cases from evaluation cases will be defined in `VALIDATION_STRATEGY.md`.

The validation framework should allow new methods to be evaluated using a consistent process while preserving method-specific metrics and limitations.

### 6.9 Projects and persistence

Project management organizes work around one exoplanet per project. A project can contain multiple observations, reference selections, analyses, notes, and results.

SQLite is the intended store for structured records and relationships. Files should hold larger source datasets, derived arrays, plots, or other artifacts when appropriate. Exact schemas, migration strategy, and storage paths remain to be specified in `DATA_MODELS.md`.

Persistence services should preserve stable identifiers and relationships between projects, observations, references, and analysis runs. A refreshed dataset must not silently replace the historical input to an existing analysis.

### 6.10 Visualization and reporting

Visualization renders data and results supplied by the scientific services. It must not independently recalculate a scientific conclusion.

Plots should label axes and units, distinguish observations from references and synthesized products, identify relevant datasets, and display uncertainty where available. Gaps and missing values should not be plotted in a way that implies measurements exist where they do not.

Reporting gathers result metadata, source attribution, method details, and limitations into traceable exports. Exported results should identify the planet, observations, references, processing, comparison method, settings, outputs, and relevant citations.

### 6.11 Logging and diagnostics

Operational logs should help diagnose network, parsing, storage, and execution failures without replacing the scientific provenance record.

User-facing errors should state what failed and, where practical, what action can be taken. Logs should not claim an operation succeeded unless it actually did. Sensitive local paths or credentials should not be unnecessarily exposed in exported scientific reports.

## 7. Dependency rules and interfaces

The following rules are proposed as architectural constraints:

1. UI code calls application services; it does not call database tables or provider APIs directly.
2. Application services coordinate work but do not duplicate algorithms.
3. Source adapters depend on provider APIs and formats, not on UI components.
4. Scientific processing consumes defined data objects and explicit settings.
5. Comparison methods do not perform network access or depend on desktop UI state.
6. Persistence is accessed through defined services or repositories rather than scattered database queries.
7. Visualization consumes structured data/results rather than re-running the analysis.
8. Provenance is attached to dataset and analysis records and is not reconstructed from filenames alone.
9. Shared domain concepts should not import UI modules.
10. New abstractions must solve a real separation, testability, or extension need; avoid creating layers that merely forward calls without adding value.

The detailed public interfaces and dependency graph will be specified in `MODULE_RESPONSIBILITIES.md` after the first supported data formats and comparison requirements are better understood.

## 8. Core domain concepts

These are conceptual entities, not finalized Python classes or database schemas.

- **Planet:** stable astronomical identity, catalog identifiers, and aliases.
- **Project:** one planet's research workspace and project metadata.
- **Observation:** a particular transmission-spectrum dataset and its source and observational context.
- **Molecule:** molecular identity and relevant identifiers.
- **ReferenceDataset:** a measured/derived spectrum, theoretical line list, or supported reference representation.
- **PreparedSpectrum:** a documented, derived representation used for a particular comparison; linked to its source and transformations.
- **AnalysisRun:** a specific execution with exact inputs, method/version, configuration, processing, outputs, and status.
- **CandidateResult:** a method-defined result for a molecular candidate, including score definition, diagnostics, and limitations.
- **BenchmarkCase:** a curated, cited validation case and the evidence supporting its inclusion.
- **ValidationRun:** an evaluation of a method/configuration against a defined benchmark set.

The relationship model, mandatory fields, stable identity rules, and serialization details belong in `DATA_MODELS.md`. Avoid duplicating large spectral arrays inside structured database records when a file reference and integrity metadata are more appropriate.

## 9. Persistence, cache, and offline behavior

ECAS must preserve research data and analysis history in a way that supports integrity, traceability, recovery, and explicitly defined offline workflows.

These are target architectural requirements. The mechanisms below describe the design that must be specified and verified; they do not assert that every mechanism is already implemented.

### 9.1 Storage responsibilities

Storage design must distinguish three responsibilities:

1. **Structured project records:** identities, metadata, relationships, analysis configurations, results, statuses, and references to scientific data.
2. **Scientific data and artifacts:** original source files, parsed or prepared datasets, synthesized references, plots, and exports where applicable.
3. **Cache and shared reference data:** locally available copies of external datasets that can be reused without confusing cached availability with source authority.

SQLite is the current persistence technology in the supplied project snapshot. The existing implementation stores spectral data as JSON text in SQLite. A future architecture using separate files for large datasets or artifacts is a proposed design, not a description of the current storage implementation.

Before expanding the storage architecture, specify which data belongs in each storage location, how records refer to artifacts, and how consistency is maintained across those locations. Avoid adding a separate artifact store or cache abstraction unless the approved workflow requires it.

### 9.2 Input validation and persisted-data integrity

Data must not become trusted merely because it can be written to the database.

The persistence workflow should define the following controls:

1. Validate the structure and required metadata of an input before accepting it as a valid scientific record.
2. Validate serialized representations before saving and check that retrieved data can be decoded into the expected representation.
3. Use appropriate database constraints for requirements the database can enforce, such as required fields, uniqueness, and relationships where applicable.
4. Define transaction boundaries for related changes so that a failed operation does not leave a partially updated logical record.
5. Define how database errors, malformed stored data, incompatible records, and failed retrievals are reported.
6. Preserve enough identity and provenance information to distinguish original inputs, derived data, and different dataset versions.

Database constraints and serialization checks are necessary but insufficient for scientific validity. Domain-specific validation must also establish whether values, units, metadata, and relationships make sense for the intended scientific operation.

The detailed schema, constraints, and validation rules belong in `DATA_MODELS.md` and the relevant approved persistence decisions. This architecture does not prescribe a final schema before those requirements are resolved.

### 9.3 Dataset identity, versions, and artifact integrity

A dataset must be identifiable independently of its display name or filesystem path.

Where appropriate and technically feasible, the design should use:

- Stable source or dataset identifiers.
- Content hashes to detect byte-identical files and verify file integrity.
- Source-provided version identifiers or equivalent metadata where available.
- Import or retrieval timestamps as provenance, not as proof of dataset identity.
- Explicit relationships between original inputs, derived datasets, and analysis runs.

A content hash establishes identity for particular file contents; it does not prove scientific correctness, authenticity, or equivalence between differently encoded datasets.

When an external source changes or a dataset is refreshed, the system must not silently replace the input associated with a historical analysis. A new version or record should be created when needed, with the relationship to earlier versions made explicit.

If an expected artifact is missing or fails integrity checks, ECAS must report the problem. It must not silently treat a different file as the original artifact.

### 9.4 Transaction and artifact-write behavior

The persistence design must define what happens when a logical operation involves multiple database records or both database records and files.

For database-only changes, use transactions where multiple writes must succeed or fail together.

For operations involving files and database references, define an ordering and recovery policy that avoids committed references to artifacts that were never successfully written. Where appropriate, use temporary files, verify completed writes, and replace final files safely before recording the completed artifact state.

The design must also define how interrupted operations are detected and how incomplete artifacts or stale references are handled during recovery.

These are requirements for the target persistence design. The exact implementation must be selected based on the actual storage workflow; filesystem and database operations should not be described as one atomic transaction unless the implementation genuinely provides that guarantee.

### 9.5 Cache policy and source authority

A cache is a local availability mechanism, not an independent scientific authority.

For every cached data category, the design should define:

- What is cached and why.
- How the cached item is associated with its original source and dataset identity.
- Which metadata identifies the source version or retrieval state.
- When a cached item may be reused.
- How refreshes, changed remote data, invalid cached content, and unavailable sources are handled.
- Whether cached data may be retained indefinitely or requires a documented refresh or expiration policy.

Cache invalidation and refresh rules remain open design decisions until the supported data sources and workflows are selected.

A refresh must not silently change the inputs of a saved analysis. Cached content that differs from the expected dataset must be treated as a different version or investigated according to an explicit policy.

### 9.6 Offline behavior

Offline capabilities must be specified per operation rather than described as a blanket guarantee.

When all required inputs, saved records, and software dependencies are available locally, the target architecture should support:

- Opening and inspecting saved projects.
- Viewing locally stored observations, results, plots, and citations.
- Reviewing saved analysis configurations and diagnostics.
- Importing supported local files.
- Rerunning a supported analysis when its required inputs and dependencies are available locally.
- Running supported validation workflows when their required benchmark inputs are available locally.

Online search, first-time downloads, and remote refresh generally require connectivity.

When a required input or dependency is unavailable, ECAS must identify what is missing and explain which operation cannot proceed. It must not silently substitute a newer, unrelated, or scientifically incompatible dataset.

Offline support should be verified through tests that disable or isolate network access and exercise each claimed workflow. The absence of a network request in a unit test is not, by itself, evidence that the full workflow operates offline.

### 9.7 Failure handling and recovery

The persistence design must define expected behavior for:

- A database that cannot be opened or written.
- Malformed or incompatible stored records.
- Missing, incomplete, or corrupted artifacts.
- Failed downloads or interrupted file writes.
- Missing cached inputs during an offline operation.
- Failed project updates or migrations.
- A saved analysis whose original inputs are no longer available.

Failures must remain distinguishable from successful operations. An incomplete analysis must not be represented as a completed result, and a failed save must not be reported as successful.

Recovery mechanisms, backup policy, schema migrations, and cache retention should be designed to match the initial supported workflow. They should not be claimed as implemented until their behavior has been tested.

### 9.8 Verification requirements

Before a persistence or offline capability is declared complete, its verification should cover the relevant requirements above.

At minimum, the applicable test plan should consider:

- Round-trip storage and retrieval of supported data.
- Rejection or explicit handling of invalid records.
- Failed-write and transaction behavior.
- Dataset identity and preservation of historical inputs.
- Artifact existence and integrity checks where separate files are used.
- Cache reuse and refresh behavior where caching is implemented.
- Offline access to saved projects and results.
- Clear failure behavior when an input or dependency is missing.
- Recovery or migration behavior for the failure cases the application claims to support.

Software tests establish that the implemented controls behave as intended under tested conditions. They do not independently establish the scientific validity of the underlying data or analysis.


## 10. Scientific integrity and result interpretation

ECAS must distinguish the following concepts in its data model and interface:

- **Observation:** an astronomical dataset and its recorded measurements.
- **Reference:** measured, experimentally derived, theoretical, or synthesized molecular information.
- **Processed data:** a documented transformation of an input.
- **Spectral correspondence:** overlap or similarity between selected spectral representations.
- **Candidate identification:** evidence consistent with a molecular candidate under a defined method.
- **Statistical support:** a result whose statistical interpretation is justified by the method and validation.
- **Atmospheric constraint:** an inference from an appropriate physical model and analysis.
- **Published result:** a claim made by an external publication, attributed to its authors.

These categories must not be conflated. In particular:

- Spectral overlap alone is not proof of atmospheric presence.
- A score is not a probability unless its interpretation has been justified and validated.
- A candidate ranking is not a quantitative abundance measurement.
- A published detection is benchmark evidence, not an automatically guaranteed outcome of ECAS.
- Repeated features across datasets must be assessed with attention to shared data, calibration, and processing dependencies.
- Missing uncertainty or metadata must be surfaced when it limits interpretation.

The system should be allowed to return inconclusive results and explain why a candidate cannot be assessed reliably.

## 11. Error handling and operational reliability

Expected failure categories include:

- Network or provider unavailability.
- Missing or inaccessible source files.
- Unsupported or malformed import formats.
- Missing units or ambiguous spectral quantities.
- Structurally valid but scientifically incompatible data.
- Incomplete downloads or corrupt cached files.
- Missing analysis dependencies or configuration.
- Comparison methods that cannot run on the supplied inputs.
- Failed persistence or project migration.
- Insufficient benchmark evidence for a proposed validation claim.

Failures should be represented explicitly and reported at the correct level. A failed analysis must not be stored or displayed as a successful candidate result. Partial progress may be retained when useful, but its incomplete status must be clear.

External scientific files are data, not executable instructions. Import and project-loading paths should validate inputs and avoid executing content from imported files.

## 12. Testing boundaries

Testing should follow the architecture's responsibilities:

- **Unit tests:** domain rules, unit handling, validation, processing, scoring, and individual comparison methods.
- **Adapter tests:** parsing and behavior of each supported source or file format, using documented fixtures or appropriately controlled tests.
- **Integration tests:** acquisition-to-storage, import-to-validation, analysis-to-persistence, and project reopen workflows.
- **Offline tests:** saved projects and analyses remain usable with network access unavailable when dependencies are cached.
- **Reproducibility tests:** identical versioned inputs and settings produce equivalent results within defined numerical tolerances.
- **Scientific validation tests:** method performance against curated benchmark cases, kept distinct from ordinary software correctness tests.
- **UI tests:** critical user workflows and error presentation once the framework is selected.

Tests must not quietly substitute fabricated scientific data for real benchmark evidence. Synthetic fixtures may be used for clearly bounded software tests if explicitly labeled and kept separate from real-data validation.

## 13. UI framework and dependency selection

The current implementation uses PySide6 for the desktop UI and PyQtGraph for spectral plotting. These are established implementation choices, not unresolved initial framework selections. Any future replacement or substantial change should be justified against workflow requirements, scientific plotting needs, maintainability, licensing, and dependency complexity.

- A practical native-style Windows desktop experience.
- Scientific plotting integration and interactive performance.
- Compatibility with the scientific Python ecosystem.
- Maintainability, licensing, community support, and documentation.
- Accessibility and layout capabilities.
- Dependency and installation complexity.
- Ability to keep UI code separate from scientific logic.
- A reasonable future packaging path without requiring packaging now.

The same evidence-based approach applies to source adapters, database access libraries, and serialization tools. Candidate dependencies listed in the master blueprint are options to evaluate, not an automatic list of required installations.

## 14. Open decisions and deferred design

### 14.1 Decisions to resolve during planning

1. **Benchmark shortlist:** choose accessible, documented detections and suitable non-detections or controls.
2. **First comparison method:** select only after considering benchmark data, resolution, noise, coverage, reference type, and intended interpretation.
3. **Initial data sources and file formats:** support the minimum formats needed by the chosen workflow, including local import.
4. **Minimum reproducibility record:** specify required identifiers, versions, configuration, processing history, and outputs.
5. **UI framework:** compare viable candidates and document trade-offs.
6. **Initial scale and performance expectations:** estimate dataset sizes and responsiveness needs using realistic source data where possible.

These are planning tasks. They do not prevent drafting the architecture or its supporting documents.

### 14.2 Decisions to defer

- Final database schema and migration implementation.
- Detailed cache expiration, refresh, and retention policy.
- Final UI styling and layout.
- Standalone packaging and installer.
- Advanced atmospheric retrieval and abundance estimation.
- Advanced uncertainty methods not required by the first validated comparison workflow.
- Broad support for providers and formats not needed by the initial workflow.

## 15. Implementation and change control

This document does not authorize code implementation or modification of the ECAS workspace. Implementation requires explicit user approval.

When implementation is authorized, agents should:

1. Read the master blueprint, relevant approved architecture documents, `PROJECT_STATE.md`, and `DECISIONS.md` when present.
2. Inspect the actual workspace before assuming a file or subsystem exists.
3. Work only within the assigned scope.
4. Distinguish proposals, changes made, and verified results.
5. Preserve existing work and avoid duplicate infrastructure.
6. Raise conflicts with approved requirements before making material architectural changes.
7. Record changed files, rationale, test evidence, unresolved issues, and handoff notes in their own dated agent log.
8. Update project state only with verified facts.
9. Preserve source attribution, input versions, uncertainty, and processing history in data-related work.
10. Stop and request review if the task exceeds its authorization or requires an unresolved material decision.

The directory tree in other planning materials is a proposal, not a requirement to create every suggested file. Implement only the modules and abstractions justified by the approved design and current scope.

## 16. Planned companion documents

The following documents should complement, not duplicate, this architecture:

| Document | Purpose |
|---|---|
| `DATA_FLOW.md` | Describe acquisition, import, validation, preparation, comparison, persistence, and offline paths. |
| `MODULE_RESPONSIBILITIES.md` | Define module ownership, allowed dependencies, and public interfaces. |
| `DATA_MODELS.md` | Define entities, relationships, identity rules, required metadata, and persistence constraints. |
| `VALIDATION_STRATEGY.md` | Define benchmark inclusion, evaluation metrics, threshold derivation, and limits of claims. |
| `docs/brains/DECISIONS.md` | Record approved decisions and rationale. |
| `docs/brains/PROJECT_STATE.md` | Record verified project status and outstanding work. |

These documents should be drafted against the same confirmed decisions and reviewed together for consistency.

## 17. Review checklist

Before approving this architecture for implementation, verify that:

- [ ] The scope reflects the intended first release without requiring future capabilities immediately.
- [ ] Online archive retrieval and local-file import converge on consistent validation and provenance handling.
- [ ] Measured spectra, theoretical line lists, and synthesized spectra remain distinct.
- [ ] Comparison methods can be added without coupling them to the UI or data providers.
- [ ] Scientific compatibility checks precede comparison.
- [ ] Project-per-planet organization supports multiple individually identifiable observations and analyses.
- [ ] Historical analyses remain tied to the exact inputs and settings used.
- [ ] Cached inputs and saved projects support the required offline workflows.
- [ ] Results communicate uncertainty, limitations, and the distinction between candidate evidence and detection claims.
- [ ] Testing separates software correctness from scientific benchmark validation.
- [ ] The proposed structure avoids both monolithic coupling and unnecessary fragmentation.
- [ ] Unresolved decisions are explicitly recorded rather than filled with unsupported assumptions.

## 18. Related Documents

docs/ECAS_development_plan.md — defines the proposed order for building the architecture described here.

DATA_FLOW.md — describes how data moves through the system.

DATA_MODELS.md — defines the conceptual records and relationships.

MODULE_RESPONSIBILITIES.md — assigns responsibilities and boundaries to modules.

VALIDATION_STRATEGY.md — defines the approach to scientific method evaluation.
---

**Draft conclusion:** This architecture establishes the intended system boundaries and scientific safeguards while leaving the first comparison method, benchmark cases, initial providers/formats, and UI framework open for evidence-based selection. It is ready for review and refinement; it is not, by itself, authorization to implement the application.
