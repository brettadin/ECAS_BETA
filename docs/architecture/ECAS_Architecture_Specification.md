# ECAS Architecture Specification

**Document status:** Revised working draft for review  
**Project:** ECAS — Exoplanetary Characterization & Astrochemistry Suite  
**Implementation status:** This document defines architectural intent. It does not authorize implementation.  
**Supersedes:** Draft 0.3, upon approval  
**Authority:** This specification establishes the overall architectural direction. Detailed behavior is defined by the relevant architecture documents and approved decisions.

---

## 1. Purpose and scope

ECAS is a Python desktop application intended to support exoplanetary atmospheric characterization through spectroscopic data management, comparison with molecular reference data, and evidence-based candidate evaluation.

The application is being developed incrementally. Its architecture must support the intended scientific workflow without requiring every planned capability to exist in the initial implementation.

The long-term system should support:

- Importing supported local spectral files.
- Discovering and retrieving real astronomical observations from scientific archives.
- Acquiring and managing molecular reference data.
- Preserving source information, metadata, and processing history.
- Validating data structure and assessing scientific suitability.
- Preparing compatible inputs for selected analysis methods.
- Comparing observations with molecular references.
- Evaluating methods against appropriate scientific benchmarks.
- Persisting projects, analysis configurations, results, and associated artifacts.
- Inspecting saved work offline when the required data and software are available.

These capabilities are architectural objectives, not a declaration that every feature has been implemented.

### 1.1 Governing principles

ECAS must prioritize:

1. **Scientific integrity:** Never represent a candidate match as a confirmed molecular detection without sufficient evidence.
2. **Traceability:** Preserve the origin and identity of observations, references, and derived products.
3. **Reproducibility:** Retain the inputs, settings, processing history, and software information needed to investigate or repeat an analysis.
4. **Explicit uncertainty:** Preserve available uncertainties and communicate missing information and methodological limitations.
5. **Separation of responsibilities:** Keep user-interface behavior, data acquisition, persistence, scientific calculations, and presentation appropriately separated.
6. **Incremental development:** Build and verify small, usable capabilities before adding interconnected systems.
7. **Evidence-based decisions:** Base scientific and architectural choices on actual data, documented requirements, and verification.
8. **Maintainability:** Introduce abstractions when they establish useful boundaries, not merely because a future feature might need them.
9. **Offline resilience:** Support saved work without requiring unnecessary network access.
10. **Honest status reporting:** Distinguish implemented behavior, verified behavior, proposed designs, and unresolved decisions.

## 2. Current implementation and target architecture

The architecture must distinguish the existing application from the intended system.

### 2.1 Established implementation baseline

The current project state, as recorded in the development plan and supplied project context, includes:

- A Python desktop application using PySide6.
- A CSV import workflow for the currently supported input schema.
- A structured `SpectrumData` representation.
- SQLite-backed persistence for spectrum records.
- A spectral-data table in the desktop interface.
- A PyQtGraph-based spectral visualization component.
- Automated tests for importing, persistence, plotting, and relevant interface behavior.

The development records report completion of the core persistence and plotting work, including preservation of the spectrum model's fields through persistence and tests of plotted-coordinate fidelity.

These statements describe the supplied project baseline. They do not independently establish the state of any uncommitted local changes or subsequent work.

The existing CSV importer must not be interpreted as universal CSV/TXT support, nor should a provider-specific CSV workflow be interpreted as a general online archive integration system.

The current `SpectrumData` model and SQLite persistence implementation must be inspected before extending them. Their existence does not establish that they can represent all required astronomical observations, measured molecular references, theoretical line lists, or synthesized spectra.

### 2.2 Target architecture

The target architecture extends the existing application through controlled additions to data acquisition, scientific data representation, validation, preparation, analysis, and reproducibility.

The target design must evolve from verified implementation experience. Proposed modules and interfaces must not be treated as existing infrastructure merely because they appear in an architecture document.

Each development chunk should establish:

- A bounded objective.
- The behavior included and excluded.
- The relevant existing code and dependencies.
- The intended design and affected files.
- Appropriate automated and manual verification.
- The remaining limitations and dependencies.

The development plan defines the implementation sequence and completion criteria. This specification does not replace that plan.

## 3. Confirmed decisions and unresolved choices

The following decisions are established in the supplied project specification and development context.

| Topic | Current position |
|---|---|
| Application form | Desktop application |
| Programming language | Python |
| UI framework | PySide6 is used in the current implementation; any proposed replacement requires explicit review |
| Plotting | PyQtGraph is used in the current implementation |
| Structured persistence | SQLite |
| Larger data and artifacts | File-based storage is intended where appropriate; the exact storage design remains to be finalized |
| Initial scientific domain | Exoplanet transmission spectra |
| Project organization | One planet per project, with support for multiple observations and analyses |
| Local input | The currently supported CSV workflow exists; broader format support requires separate decisions |
| Molecular references | Measured or experimentally derived spectra and theoretical line lists must remain distinct |
| Initial analysis goal | Spectral comparison and candidate scoring |
| Scientific validation | Published detections and suitable non-detections or controls should inform method evaluation |
| Offline behavior | Saved projects and locally available inputs should remain usable offline |
| Standalone packaging | Deferred until the workflow is sufficiently stable |
| Full atmospheric retrieval | Outside the initial implementation scope |
| Implementation authorization | Planning documents do not authorize code changes |

The following decisions require evidence and explicit review before implementation where relevant:

- Initial archive and molecular-reference providers.
- Supported source-specific data products and formats.
- The first production comparison method.
- Minimum scientific metadata required for each supported data type.
- The detailed domain model and persistence schema.
- Cache identity, refresh, retention, and invalidation behavior.
- The benchmark set and evaluation methodology.
- Additional module boundaries and interfaces.
- Performance expectations for the initial workflow.

A proposed choice becomes an approved decision only through the project's established decision process. A proposal must not be recorded as an implemented or approved capability merely because it appears in a draft.

## 4. System boundaries and responsibilities

The target architecture separates responsibilities according to the work being performed. These are logical boundaries, not a requirement to create a separate module for every responsibility.

### 4.1 Desktop UI

The UI handles user interaction and presentation.

Its responsibilities include initiating supported workflows, collecting user choices, displaying available data, presenting validation messages, showing plots and results, and communicating errors or limitations.

The UI must not independently implement scientific comparison algorithms, duplicate provider-specific retrieval logic, or bypass the persistence and application workflow to manipulate scientific records directly.

### 4.2 Application workflow coordination

Application-level coordination connects user requests to the relevant operations.

It should coordinate acquisition, validation, registration, preparation, analysis, and persistence while ensuring that required prerequisites are satisfied.

Workflow coordination should not become a general-purpose framework. Introduce abstractions only where they clarify ownership, enforce requirements, or reduce meaningful duplication.

### 4.3 Data acquisition and ingestion

Acquisition components obtain data from supported remote sources or local files.

Source-specific behavior should remain isolated behind appropriate interfaces. Parsing should translate supported source representations into explicit internal data structures without inventing scientific meaning.

Network retrieval, source-specific parsing, structural validation, scientific suitability assessment, and project registration are related but distinct responsibilities.

### 4.4 Scientific data and spectroscopy

Scientific data components represent observations and molecular references, preserve their meaning and metadata, and provide operations needed to inspect and prepare spectral inputs.

They must distinguish between coordinate units, signal units, spectral quantities, measurement conditions, and data origins.

Scientific preparation must be explicit and must not silently modify original source data.

### 4.5 Analysis and evaluation

Analysis components execute a selected method using eligible inputs and return method-defined results.

Evaluation components assess method performance against appropriate benchmarks. They must not confuse software correctness tests with evidence that a scientific method is valid.

The analysis layer must not independently acquire network data, manipulate UI state, or manage unrelated persistence operations.

### 4.6 Persistence and file management

Persistence manages structured records and their relationships. File management handles original payloads and derived artifacts where appropriate.

The architecture must preserve the association between a saved analysis and the exact inputs used to produce it.

The detailed division between SQLite records, source files, derived artifacts, and caches is governed by the relevant persistence and data-model design.

### 4.7 Visualization and reporting

Visualization presents supplied scientific data and analysis outputs. Reporting communicates results, provenance, citations, limitations, and relevant processing history.

Presentation components must not silently change scientific values or independently derive conclusions that belong to the analysis or evaluation layer.

## 5. Scientific data representations

ECAS must not force scientifically different data products into a single undifferentiated spectrum representation.

At minimum, the target design must distinguish the following categories.

### 5.1 Astronomical observations

Astronomical observations represent measurements or published data products associated with a target, instrument, observing program, or publication.

A transmission spectrum is a specific scientific product. Raw observational files, time-series measurements, transit light curves, processed spectra, and catalog records are not interchangeable.

The availability of an archive record does not establish that a usable transmission spectrum is available.

### 5.2 Measured molecular reference spectra

Measured or experimentally derived molecular spectra represent laboratory measurements or products derived from them.

Their metadata should preserve the source, citation, molecular identity, spectral region, coordinate and signal definitions, units, experimental conditions where available, resolution, uncertainties, and processing state.

Differences between laboratory conditions and astronomical conditions must remain visible. A measured molecular spectrum must not automatically be treated as a direct prediction of an exoplanet atmosphere.

### 5.3 Theoretical line lists

Theoretical spectroscopic line lists contain discrete transitions and associated parameters. They are not necessarily continuous spectra.

Their representation must preserve molecular identity, transition parameters, units, source and version information, and applicable limitations.

A line list must not be silently converted into continuous-spectrum values without a documented calculation or synthesis operation.

### 5.4 Calculated and synthesized spectra

Calculated spectra are generated from theoretical inputs, models, or other data through an explicit computational process.

The derived product must remain linked to its inputs and retain the method, software version, parameters, assumptions, units, and relevant physical conditions.

A calculated spectrum must remain identifiable as calculated rather than being presented as an independent experimental measurement.

### 5.5 Shared metadata requirements

Data models should preserve, where available and applicable:

- Stable record identity.
- Source and source-specific identifiers.
- Target or molecular identity.
- Spectral coordinate values and units.
- Signal definition and units, or transition-parameter definitions for line lists.
- Uncertainties and quality indicators.
- Instrumental or experimental conditions.
- Processing status and transformation history.
- Source version or content identity.
- Citation and provenance information.
- Known limitations and validation warnings.

Missing metadata must remain distinguishable from values that were measured, supplied by a user, inferred under an explicit rule, or derived by calculation.

The detailed entities, fields, relationships, and persistence requirements belong in `DATA_MODELS.md`. This specification establishes the requirement for scientifically distinct representations but does not finalize the schema.

## 6. Acquisition, validation, and data preparation

The target workflow supports remote acquisition and local-file import while keeping their source-specific operations separate from subsequent scientific processing.

### 6.1 Acquisition

Supported sources should provide discoverable records and, where available, downloadable data products.

ECAS should preserve source identifiers, original filenames or URLs, retrieval information, relevant source versions, and associated metadata.

A source's catalog entry, publication record, or search result must not be treated as proof that a suitable numerical dataset is available.

Failed or incomplete retrieval must not be registered as a successful acquisition.

### 6.2 Parsing and structural validation

Parsing converts a supported input into an explicit internal representation.

Structural validation checks such matters as required fields, dimensions, numeric validity, units, missing values, and metadata consistency.

Validation should produce explicit outcomes, distinguish blocking errors from warnings, and preserve useful diagnostics.

Structural validity does not establish scientific comparability.

### 6.3 Scientific suitability and comparability

Before a selected analysis runs, ECAS must assess whether the inputs meet that method's requirements.

Relevant considerations include spectral quantity, coordinate and signal units, wavelength or wavenumber coverage, resolution, sampling, processing state, uncertainty availability, quality information, and reference conditions.

Compatibility must be evaluated against the selected method's requirements. The ability to represent two inputs as numeric arrays is insufficient.

Where required information is unavailable, ECAS should report that the assessment is incomplete rather than silently assuming compatibility.

### 6.4 Preparation

When justified by the selected method, preparation may include unit conversion, region selection, quality filtering, resampling, normalization, resolution matching, or calculation of a continuous spectrum from a line list.

These operations are not all required for the initial release.

Every material transformation must preserve the original input and record the operation, parameters, relevant software version, and effects on uncertainty and interpretation.

The specific preparation operations required for the first production method remain unresolved until the method and benchmark inputs have been selected.

Detailed workflow requirements belong in `DATA_FLOW.md`; method-specific scientific evaluation belongs in `VALIDATION_STRATEGY.md`.

## 7. Persistence, provenance, and reproducibility

ECAS uses SQLite for structured records. Larger source datasets and derived artifacts may be stored as files where appropriate.

The detailed persistence design must establish the ownership of source files, normalized records, derived products, cache entries, and project associations.

### 7.1 Project organization

Each planet project should support multiple observations and analysis runs.

Shared molecular reference data should be reusable across projects where appropriate, without erasing the identity of the version used in a previous analysis.

### 7.2 Analysis records

A saved analysis should identify, as applicable:

- The planet project and observation.
- The molecular reference or references.
- Exact input identities and versions.
- Source and citation information.
- Preparation operations and parameters.
- The comparison method and version.
- Method configuration.
- Relevant software versions and execution information.
- Results, diagnostics, warnings, and limitations.
- Execution and persistence status.
- Links to required derived inputs and artifacts.

A completed analysis must not be reported as successfully saved if required records or artifacts have not been persisted according to the approved storage design.

### 7.3 Historical integrity

Updating a source dataset must not silently alter the inputs associated with an earlier analysis.

Where a new version or distinct content is registered, existing analyses must continue to identify the inputs originally used.

A rerun using updated inputs should create a distinct analysis record rather than rewriting the historical result.

### 7.4 Caching and offline access

Cached data should have a stable identity based on source and record identity, with version or content identity where available.

Repeated retrieval should reuse an eligible cached copy when its identity and integrity can be established. A failed refresh must not destroy a previously valid cached dataset.

Offline operations must clearly identify missing inputs or dependencies. ECAS must not silently substitute another dataset or claim exact reproduction when the required inputs are unavailable.

The exact cache layout, invalidation rules, integrity checks, and retention policies remain subjects for detailed design.

## 8. Analysis and scientific interpretation

The initial analysis goal is spectral comparison with candidate scoring. The production method must be selected through the evidence-based investigation described in the development plan.

The architecture must allow the method to be tested independently of the UI and integrated without requiring the comparison code to own acquisition, persistence, or presentation.

A method must declare or document its input requirements and the meaning of its outputs.

ECAS must distinguish:

- Spectral correspondence.
- Candidate ranking.
- Statistical evidence supported by the method.
- Validated molecular detection.
- Quantitative abundance estimates.

These are not interchangeable conclusions.

A numerical score must not be described as a detection probability unless that interpretation has been justified and validated. Candidate ranking must not be represented as a quantitative abundance measurement.

Full atmospheric retrieval and advanced abundance estimation are deferred capabilities and must not be implied by the initial comparison workflow.

## 9. Validation and scientific evidence

Software verification and scientific validation serve different purposes.

### 9.1 Software verification

Automated tests should establish that supported components behave as specified. Examples include parsing, validation outcomes, persistence round trips, cache behavior, error handling, and correct presentation of supplied data.

Passing these tests does not establish that a comparison method produces scientifically reliable conclusions.

### 9.2 Scientific method validation

Scientific validation should use documented benchmark cases, including published detections and suitable non-detections or controls where the available evidence supports them.

The benchmark set must be relevant to the intended use and sufficiently documented to interpret the evaluation.

Method selection, evaluation metrics, threshold derivation, and the handling of uncertain or conflicting evidence must be justified. Thresholds must not be selected arbitrarily.

The evaluation must identify limitations and avoid implying that performance on a narrow benchmark generalizes to all planets, instruments, molecules, or observing conditions.

Detailed benchmark selection and evaluation requirements belong in `VALIDATION_STRATEGY.md`.

## 10. Desktop interface and dependency management

The current implementation uses PySide6 for the desktop interface and PyQtGraph for spectral plotting.

The architecture should preserve the separation between presentation and scientific logic. Plotting components should display supplied data and outputs rather than independently alter the scientific interpretation.

Any material change to the UI framework or plotting stack requires an explicit justification based on project requirements, dependency compatibility, maintainability, and practical benefit.

New dependencies should be introduced only when required by an approved task. Dependency installation, packaging, and installer work must not be pulled into unrelated development chunks.

Standalone packaging remains deferred until the core workflow is sufficiently stable.

## 11. Security, reliability, and error handling

The application must handle failures without silently corrupting or misrepresenting scientific data.

Relevant failure categories include:

- Unavailable archives or network connections.
- Missing, malformed, or unsupported source files.
- Missing or ambiguous metadata.
- Invalid numerical values or inconsistent dimensions.
- Missing preparation capabilities.
- Incompatible or undetermined inputs.
- Unavailable analysis dependencies.
- Failed or incomplete comparisons.
- Persistence and artifact-storage failures.
- Missing dependencies during offline operation.

Errors should be reported at the appropriate workflow boundary with sufficient context for diagnosis.

The application must preserve valid prior data when a retrieval or refresh fails. Partial outputs must be labeled accurately and must not be presented as completed results.

Network credentials and other secrets must not be committed to source control. Where a provider requires authentication, credentials should be supplied through an appropriate local configuration mechanism, and deterministic tests should avoid requiring live credentials wherever practical.

Security and data-integrity requirements should be implemented in the components responsible for the relevant operations rather than duplicated across the UI and scientific logic.

## 12. Development approach and agent workflow

ECAS is developed in controlled chunks, with implementation delegated to Cline in VS Code and reviewed through the established PLAN → review → ACT workflow.

Each implementation task must specify its objective, scope, constraints, acceptance criteria, and verification requirements.

### 12.1 Planning

Before proposing changes, an agent should inspect the current repository, relevant architecture documents, approved decisions, and verified project state.

The plan must distinguish existing code from proposed additions and identify conflicts or missing evidence.

PLAN mode is for investigation and planning. It does not authorize file changes, dependency installation, or implementation.

### 12.2 Implementation

ACT mode must remain within the approved scope.

Implementation should proceed in small, testable increments. Existing behavior should be preserved unless an approved requirement changes it.

An agent must not add unrelated abstractions or future features merely because they appear in the target architecture.

### 12.3 Verification and reporting

Agents must report actual changes, test commands, results, manual checks, and unresolved issues.

A proposed test is not a completed test. A passing software test is not proof of scientific validity. A reported implementation is not automatically verified behavior.

### 12.4 Documentation

Documentation must remain synchronized with the code and approved decisions.

`PROJECT_STATE.md` records verified implementation status. `DECISIONS.md` records approved decisions and rationale. Historical agent logs preserve what occurred during individual tasks.

Architecture documents define intended design at their respective levels. They must not be used to override the verified project state or to imply that proposed features already exist.

Conflicts between documents must be identified and resolved explicitly.

## 13. Relationship to the architecture documents

This specification establishes the overall architectural direction and governing constraints. The following documents provide more detailed requirements.

| Document | Primary responsibility |
|---|---|
| `docs/ECAS.md` | Project purpose, scientific principles, and overall scope |
| `docs/architecture/ARCHITECTURE.md` | System boundaries, architectural structure, and dependency rules |
| `docs/architecture/DATA_FLOW.md` | Workflow stages, transitions, prerequisites, and failure behavior |
| `docs/architecture/DATA_MODELS.md` | Data entities, relationships, identity, and minimum field requirements |
| `docs/architecture/MODULE_RESPONSIBILITIES.md` | Module ownership, interfaces, and responsibility boundaries |
| `docs/architecture/VALIDATION_STRATEGY.md` | Scientific benchmarks, evaluation methods, thresholds, and interpretation limits |
| `docs/brains/DECISIONS.md` | Approved decisions and their rationale |
| `docs/brains/PROJECT_STATE.md` | Verified current implementation status and outstanding work |
| `docs/ECAS_development_plan.md` | Development chunks, implementation order, and completion criteria |

The detailed architecture documents should not independently duplicate this specification in full. Each should define its own subject while remaining consistent with the governing principles and approved decisions.

If a conflict arises, identify the affected requirement and consult the appropriate authority. Do not silently resolve a material disagreement by choosing whichever wording is most convenient for implementation.

## 14. Open decisions and implementation dependencies

The following items remain unresolved in the supplied specification and should be addressed in the appropriate planning phase.

### 14.1 Scientific workflow

- Initial astronomical archive providers and supported data products.
- Initial molecular-reference provider or providers.
- Supported observation and reference file formats.
- Minimum metadata requirements for each supported data type.
- The first comparison method and its required inputs.
- Preparation operations necessary for that method.
- Initial benchmark cases and supporting publications.
- Evaluation metrics and evidence-based threshold derivation.

### 14.2 Data and persistence

- Final domain-model relationships and identifiers.
- Schema evolution and migration behavior.
- Source-file and derived-artifact lifecycle.
- Cache identity, integrity, refresh, and retention policies.
- Minimum reproducibility information for each analysis.
- Performance expectations for loading, plotting, and processing initial datasets.

### 14.3 Application and delivery

- Additional module boundaries where implementation evidence demonstrates a need.
- Authentication and local configuration requirements for selected providers.
- Packaging and installer strategy, once the core workflow stabilizes.
- Detailed interface design beyond the existing desktop shell.

These decisions should be resolved incrementally. They do not justify implementing a broad framework or speculative functionality before the initial scientific workflow is established.

## 15. Acceptance criteria for architectural readiness

The architecture package is ready to guide implementation when:

- [ ] Current implementation is distinguished from proposed functionality.
- [ ] Major component responsibilities and dependency boundaries are understood.
- [ ] The required scientific data categories are represented without conflating their meanings.
- [ ] The workflow distinguishes parsing, structural validation, scientific suitability, preparation, comparison, and persistence.
- [ ] Provenance and reproducibility requirements are defined consistently across the relevant documents.
- [ ] The first provider and analysis-method decisions are supported by documented evidence before their implementation.
- [ ] Scientific validation is distinguished from ordinary software testing.
- [ ] Approved decisions, open questions, and verified project status are recorded in their designated documents.
- [ ] The architecture supports incremental implementation without requiring every target module or feature to exist at once.
- [ ] No unresolved documentation conflict is silently converted into an implementation assumption.

These criteria concern architectural readiness. They do not establish that the application already implements the full target workflow.

## 16. Governing principle

ECAS should prioritize traceable scientific evidence, reproducibility, transparent uncertainty, and maintainable boundaries over apparent completeness or unnecessary architectural complexity.

The architecture must evolve alongside verified implementation and scientific evidence. Each new capability should solve a demonstrated problem, preserve the meaning and provenance of its inputs, and be testable independently wherever practical.

This specification defines the direction of ECAS. It does not authorize implementation beyond the scope explicitly approved for an individual development task.
