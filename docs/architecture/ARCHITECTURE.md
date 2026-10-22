# ECAS Architecture

**Document status:** Draft for user review  
**Project:** Exoplanetary Characterization & Astrochemistry Suite (ECAS) 
**Primary language:** Python  
**Implementation status:** Not authorized by this document  
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

## 3. Confirmed requirements and decisions

| Area | Current decision or requirement |
|---|---|
| Application form | Native-style Python desktop window |
| Launch | One-click desktop shortcut or equivalent launcher |
| UI framework | Recommend after reviewing requirements and dependencies; not yet selected |
| Initial observations | Exoplanet transmission spectra |
| Observation input | Online archives and local-file import |
| Molecular references | Measured/experimentally derived spectra and theoretical line lists, handled distinctly |
| Analysis capability | Spectral comparison and candidate scoring |
| Comparison design | Pluggable methods; choose the first method after benchmark investigation |
| Validation | Published detections and suitable non-detections or controls |
| Thresholds | Derive from benchmark evidence, metric uncertainty, and intended use |
| Projects | One project per planet, with multiple observations and analyses |
| Persistence | SQLite for structured records; files for larger datasets and artifacts |
| Offline behavior | Saved projects and cached inputs work offline; new retrieval and refresh generally require connectivity |
| Packaging | Defer until the workflow stabilizes |
| Scientific integrity | Preserve provenance, uncertainties, processing history, and limitations |
| Implementation authorization | This draft does not authorize implementation or changes to the project workspace |

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

### 9.1 Storage responsibilities

Use SQLite for structured records and relationships. Use files for large source datasets and scientific artifacts. The cache, central reference library, and user projects are separate concepts even if they share a storage root.

Each stored file should be associated with metadata that makes its role clear: original source, parsed cache, prepared spectrum, synthesized reference, plot, or exported report.

### 9.2 Dataset identity and integrity

Where practical, use stable source identifiers and content hashes to detect duplicate or changed files. Record retrieval timestamps and source version information where available. Do not rely on a filename or retrieval date alone as proof that two datasets are identical.

Updates should be explicit. New versions can be added without silently changing prior analysis records.

### 9.3 Offline behavior

When all required inputs are present locally, users should be able to:

- Open and inspect a project.
- View saved observations, plots, results, and citations.
- Review analysis configurations and diagnostics.
- Rerun supported analyses using cached inputs and available dependencies.
- Import local data.
- Run validation using locally cached benchmark inputs.

Online search, first-time downloads, and remote refresh generally require connectivity. If a required input is absent, the application should explain what is missing and which operation cannot continue. It must not silently substitute an unrelated or newer dataset.

### 9.4 Transactions and recovery

Project updates and database writes should avoid leaving half-written logical records. Large file operations should use safe write/replace patterns where appropriate, with database references committed only when the corresponding artifact is available and verified. Exact transaction and recovery procedures will be specified with the data models and persistence design.

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

The desktop UI framework remains unresolved. The recommendation should consider:

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
