# ECAS — Exoplanetary Characterization & Astrochemistry Suite

## Master Design Blueprint

**Document type:** Master scientific vision, design principles, and long-term project blueprint  
**Primary language:** Python  
**Project stage:** Incremental development toward a scientific research application  
**Document authority:** Defines project purpose, scientific requirements, intended capabilities, and long-term direction. It does not independently establish implementation status.

---

## 1. Purpose and Scope

ECAS (Exoplanetary Characterization & Astrochemistry Suite) is a scientific software project intended to support the investigation of exoplanet atmospheres through spectroscopy.

The long-term objective is to provide an extensible research environment in which users can obtain real scientific data, organize observations, investigate candidate atmospheric constituents, compare spectra, evaluate evidence, and preserve their research history.

ECAS is intended to connect three principal areas of work:

1. **Scientific data management:** obtaining, validating, organizing, preserving, and tracing observational and molecular reference data.
2. **Spectral investigation:** visualizing and comparing compatible datasets using documented, scientifically defensible methods.
3. **Research continuity:** preserving the data, assumptions, configurations, results, and provenance needed to interpret and reproduce previous work.

The application must be developed incrementally. Its long-term scientific objectives must guide architectural decisions, but documenting a future capability does not establish that the capability exists in the current implementation.

ECAS must prioritize scientific integrity, traceability, transparency, and maintainability over superficial completeness or unsupported analytical claims.

## 2. Project Objectives

### 2.1. Establish a reliable scientific data library

ECAS should support the acquisition and organization of molecular spectral reference data from appropriate scientific databases and other legitimate sources.

The intended library should accommodate, where available:

- Molecular identities and relevant identifiers.
- Spectral coordinates, including wavelength and wavenumber.
- Spectral intensities and their associated units.
- Relevant physical conditions, such as temperature and pressure.
- Spectral resolution, isotopologue information, and other dataset-specific characteristics.
- Source identifiers, original URLs, publications, licensing information, and retrieval metadata.
- Multiple datasets and representations for the same molecule.
- Local storage and reuse of previously acquired reference data.
- Integrity checks and explicit reporting of incomplete, outdated, or unavailable resources.

Reference data must remain distinguishable by source, version, conditions, and representation. A molecular identity alone is not sufficient to establish that two reference datasets are interchangeable.

The library must use real, attributable scientific data for scientific work. Synthetic or illustrative spectra may be used in explicitly identified development or educational contexts, but must never be mistaken for measured reference data.

### 2.2. Establish an exoplanet observational data library

ECAS should support the acquisition and organization of exoplanet information and spectroscopic observations from appropriate scientific archives and databases.

The intended data model should distinguish general planet metadata from individual observational datasets.

Relevant information may include:

- Planet identifiers, aliases, host-star information, and catalog metadata.
- Observational spectra and associated uncertainties.
- Transit, transmission, emission, eclipse, and other relevant observation types.
- Wavelength grids, flux or transit-depth measurements, spectral resolution, and units.
- Telescope, instrument, observing mode, and data-product identifiers.
- Observation dates, processing information, and data-release versions.
- Publication references and source metadata.
- Published atmospheric retrieval results, clearly distinguished from analyses performed by ECAS.

The existence of planet metadata must not be interpreted as evidence that usable spectral observations are available. Likewise, the existence of an observation does not guarantee that it is suitable for every intended analytical method.

### 2.3. Support scientifically defensible spectral investigation

ECAS should ultimately allow users to investigate whether observed spectral features are consistent with candidate molecular signatures.

The intended workflow includes:

- Selecting an exoplanet and one or more observations.
- Identifying relevant reference datasets.
- Inspecting observational and reference spectra.
- Evaluating spectral coverage and compatibility.
- Comparing candidate molecular features with observed structures.
- Examining overlapping features and alternative explanations.
- Assessing the effects of uncertainties, instrument characteristics, and preprocessing.
- Preserving the inputs, methods, settings, warnings, and outputs associated with an analysis.

Spectral overlap is evidence to investigate, not proof of atmospheric composition. ECAS must not present a visual correspondence, correlation, or similarity score as a confirmed molecular detection unless a suitably validated method supports that conclusion.

### 2.4. Support persistent research projects

ECAS should eventually allow users to organize research around individual exoplanets and save, reopen, and extend their work.

A research project should preserve its scientific context, not merely the most recent graph or imported file.

Depending on the implemented capabilities, a project may contain:

- Selected planets and observational datasets.
- Molecular reference datasets.
- Source references and provenance information.
- Analysis configurations and preprocessing choices.
- Comparison results and validation outcomes.
- User annotations and research notes.
- Historical results and the configurations that produced them.
- Software and dataset versions needed to interpret prior analyses.

A saved project should remain interpretable even when external sources change or new analysis methods become available. Where exact reproduction is impossible, ECAS should make the missing dependencies or changed inputs explicit.

### 2.5. Enable comparisons across multiple observations

ECAS should support comparisons among observations of the same planet where the data and scientific question justify them.

Potential investigations include:

- Whether candidate features recur across observations.
- Whether apparent features depend on an instrument or reduction pipeline.
- Whether differences are meaningful relative to measurement uncertainties.
- Whether observations provide complementary spectral coverage.
- Whether independent datasets support consistent interpretations.
- Whether apparent variation could be explained by observational conditions or processing differences.

Observations must remain individually identifiable. Combining or aligning datasets must not silently discard provenance, uncertainties, units, instrumental characteristics, or other relevant metadata.

### 2.6. Preserve provenance and reproducibility

Every scientific dataset and analytical result should be traceable to its origin.

ECAS should preserve sufficient information to understand how a result was produced, including, where applicable:

- Original data sources and persistent identifiers.
- Dataset versions and retrieval information.
- Input observations and molecular references.
- Preprocessing and transformation steps.
- Analytical methods and parameters.
- Software versions and relevant dependencies.
- Validation results, warnings, and known limitations.
- Output values, uncertainties, and interpretation.

Reproducibility is a system requirement, not a label that can be applied merely because a result has been saved.

---

## 3. Scientific Principles

These principles govern scientific data handling, analysis, interface design, and reporting throughout ECAS development.

### 3.1. Real data and attributable sources

Scientific datasets must originate from identifiable, legitimate sources.

ECAS must not fabricate observational measurements, molecular reference spectra, uncertainties, detection results, or source citations.

When information is missing, unavailable, incomplete, or unsuitable, the application must report the limitation rather than silently inventing or substituting values.

Synthetic data may be used for software tests or demonstrations when appropriately authorized and clearly identified. It must remain distinguishable from real scientific data and must not enter a real-data workflow unnoticed.

### 3.2. Separate measurements from interpretations

ECAS must distinguish source data, transformed data, model outputs, analytical findings, and scientific interpretations.

The application should preserve the difference between:

- **Observed data:** measurements supplied by an identified source.
- **Processed data:** values transformed through documented operations.
- **Reference data:** molecular spectra or other scientific reference information.
- **Spectral correspondence:** overlapping or similar structures between datasets.
- **Candidate identification:** an interpretation supported by a defined body of evidence.
- **Statistical support:** quantitative evidence evaluated by a documented method.
- **Atmospheric characterization:** estimates or constraints derived from an appropriate atmospheric model.
- **Published conclusions:** findings reported by external researchers under their stated assumptions.

These categories are not interchangeable. The interface and reports must not imply a stronger conclusion than the underlying evidence and method support.

### 3.3. Preserve uncertainty

Measurement uncertainties, calibration limitations, instrumental effects, data-quality indicators, and relevant model assumptions must be retained wherever available.

Analysis results should communicate uncertainty and limitations rather than presenting an isolated score or categorical confidence label.

If an input lacks information required for a particular method, ECAS should identify the limitation and avoid unsupported conclusions.

Missing uncertainty information must not be interpreted as zero uncertainty.

### 3.4. Respect physical and observational conditions

Molecular reference spectra may depend on temperature, pressure, isotopic composition, spectral resolution, and other conditions.

Astronomical observations may also be affected by instrumental response, calibration, noise, data reduction, spectral coverage, and measurement geometry.

Before comparison, ECAS should assess whether datasets are compatible for the intended operation. When transformation or approximation is required, the method and its assumptions must be documented.

The ability to display two datasets on the same graph does not establish that they are scientifically comparable.

### 3.5. Preserve original data

Original source data should remain identifiable and recoverable wherever the application has access to them.

Normalization, resampling, unit conversion, filtering, interpolation, and other transformations must not silently overwrite the original measurements.

Derived data should be distinguishable from source data, with the transformations and relevant parameters recorded where practical.

Any operation that intentionally changes or replaces source data must be explicit and appropriately controlled.

### 3.6. Prefer transparency over artificial certainty

ECAS must communicate what was checked, what was found, what assumptions were made, and what remains uncertain.

A completed computation is not necessarily a valid scientific analysis. A successful import does not establish scientific suitability. A passing software test does not prove that an analytical method is scientifically valid.

Reports and interface elements must distinguish technical success from scientific validity.

### 3.7. Keep scientific rules explicit

Scientific assumptions, acceptance criteria, thresholds, and comparison rules must be documented and justified.

Arbitrary numerical thresholds must not be introduced merely to produce a definitive-looking result.

Where evidence is insufficient to establish a defensible rule, the uncertainty should remain explicit and the decision should be deferred until appropriate evidence or requirements are available.

---

## 4. Data Sources and Acquisition

### 4.1. Molecular reference data

Potential reference sources include established molecular spectroscopy databases and other scientifically appropriate repositories.

Selection of a source must consider:

- Scientific suitability for the intended analysis.
- Availability and quality of metadata.
- Units, coordinate systems, and physical conditions.
- Data provenance and versioning.
- Licensing and permitted use.
- Retrieval mechanisms and access limitations.
- The distinction between measured, calculated, and model-derived data.

Specific providers and retrieval mechanisms must be selected through documented technical decisions. The existence of this requirement does not imply that any particular provider is currently integrated.

### 4.2. Exoplanet and observational data

Potential sources include established exoplanet catalogs, telescope archives, published datasets, and other appropriate scientific repositories.

Acquisition workflows should distinguish:

- Planet and host-star metadata.
- Individual observations.
- Processed or calibrated data products.
- Published atmospheric retrievals.
- Results generated by ECAS itself.

Source metadata must be retained sufficiently to identify the data product and its scientific context.

Archive access must not be assumed to be universal. Different providers may use different interfaces, schemas, units, access conditions, and release conventions.

### 4.3. Acquisition requirements

Future acquisition capabilities should address:

1. Source identification and dataset selection.
2. Retrieval errors, timeouts, and unavailable resources.
3. Input format and schema validation.
4. Data integrity and completeness checks.
5. Metadata extraction and preservation.
6. Version identification and duplicate handling.
7. Licensing and attribution.
8. Local storage and offline reuse.
9. Clear reporting of rejected, incomplete, or unsupported data.

Acquisition must not silently convert an unsupported input into a scientifically meaningful dataset.

### 4.4. Source attribution

Where available, records should preserve:

- Source organization or provider.
- Dataset identifier and original filename.
- Original URL or persistent identifier.
- Publication and authorship information.
- Retrieval date and relevant data-release version.
- Licensing or usage conditions.
- Processing history and transformations performed by ECAS.

Provenance requirements should be implemented alongside the relevant ingestion and storage capabilities, rather than postponed until after scientific analysis has been added.

---

## 5. Data Library, Storage, and Caching

### 5.1. Intended design

ECAS should provide a reliable local data library that supports repeatable access to observational and reference datasets.

The intended design should distinguish scientific data from the metadata that identifies, describes, and contextualizes it.

The library should support, as appropriate:

- Dataset identification and metadata.
- Original source information.
- Local copies of retrieved data.
- Integrity checks.
- Dataset version tracking.
- Explicit relationships between source and derived data.
- Safe reuse of previously retrieved resources.
- Detection of incomplete or outdated local resources.

The precise storage architecture remains governed by the approved architecture and implementation decisions. This blueprint does not prescribe an unapproved database or file-storage redesign.

### 5.2. Caching requirements

Caching should reduce unnecessary retrieval while preserving source identity and data integrity.

A future cache should distinguish between:

- The source's current remote state, when known.
- The locally stored copy.
- The time and conditions of retrieval.
- The version or release represented by the local copy.
- Whether the resource has been checked for integrity.
- Whether newer source data may be available.

A cached dataset must not automatically be treated as the newest version or as scientifically validated.

### 5.3. Offline behavior

ECAS should be designed to support meaningful offline work with previously acquired local data.

Offline capabilities depend on what has already been downloaded and stored. The application must not imply that an unavailable online resource can be retrieved or refreshed without a connection.

When online access is unavailable, ECAS should distinguish between usable local data, unavailable resources, and operations that require connectivity.

### 5.4. Storage integrity

Storage operations must preserve the relationship between data and its metadata.

Future storage requirements include:

- Safe handling of invalid or incomplete records.
- Appropriate transaction and error-handling behavior.
- Consistent identification of datasets and projects.
- Detection and reporting of corrupt or missing resources.
- Preservation of source data during updates.
- Clear separation between current storage behavior and proposed artifact-storage designs.

Storage migrations and architectural changes must be supported by explicit decisions, tests, and appropriate recovery procedures.

---

## 6. Spectral Preparation and Analysis

### 6.1. Input characterization

Before an analytical operation, ECAS should establish what the input represents and whether the available information is sufficient for the requested operation.

Relevant properties may include:

- Spectral coordinate values and units.
- Signal or measured quantity and units.
- Column meanings and data types.
- Missing, malformed, or non-finite values.
- Spectral coverage and sampling.
- Measurement uncertainties.
- Instrument and observation metadata.
- Source provenance and data-processing history.

Parsing a file and assigning canonical column names does not establish that the values have the correct physical interpretation.

### 6.2. Data preparation

Potential preparation operations include unit conversion, filtering, normalization, interpolation, resampling, and other transformations justified by the intended analysis.

Each operation must:

- Be appropriate for the data and scientific question.
- Preserve the original source measurements.
- Record relevant parameters and assumptions.
- Handle invalid or missing values explicitly.
- Avoid introducing unsupported physical interpretations.
- Communicate limitations and information loss.

Not every dataset requires the same preparation. ECAS must not apply transformations automatically merely because they are available.

### 6.3. Reference spectrum preparation

Reference spectra must be characterized before being compared with observational data.

Relevant considerations include:

- Coordinate system and units.
- Intensity definition and units.
- Temperature and pressure.
- Isotopologue and molecular identity.
- Spectral resolution and sampling.
- Source type and generation method.
- Applicable uncertainty information.
- Instrumental or physical conditions relevant to comparison.

Where differences require broadening, resampling, conversion, or other processing, the transformation must be appropriate to the scientific context and recorded.

### 6.4. Initial comparison capabilities

The intended comparison framework should support progressively more rigorous analysis.

Possible stages include:

1. Visual inspection of observational and reference spectra.
2. Identification of overlapping spectral regions.
3. Assessment of data compatibility.
4. Quantitative comparison using a defined method.
5. Evaluation of uncertainty and alternative explanations.
6. Comparison among candidate molecules or reference datasets.
7. Recording and interpretation of results.

Each stage requires its own acceptance criteria and limitations. A result from an early exploratory stage must not be presented as equivalent to a validated atmospheric detection.

The methods used for quantitative comparison must be justified for the data and question. No universal matching algorithm or scoring threshold is assumed by this blueprint.

### 6.5. Atmospheric modeling and retrieval

Atmospheric modeling and retrieval are longer-term scientific capabilities that may be introduced when their requirements, dependencies, and validation evidence are established.

Such methods may require additional physical models, priors, uncertainty treatment, model assumptions, and specialized dependencies.

ECAS must distinguish its own computed results from externally published retrievals and must preserve the assumptions and limitations associated with each.

No atmospheric retrieval capability should be considered implemented solely because it appears in this blueprint or in an architecture proposal.

---

## 7. Research Projects and Analysis Records

### 7.1. Project identity

A research project should have a stable identity and sufficient metadata to distinguish it from other projects.

Potential metadata include:

- Project name and identifier.
- Selected exoplanet and related identifiers.
- Creation and modification information.
- Research notes and purpose.
- Associated datasets and source references.
- Analysis history and relevant software versions.

The specific project schema must follow the approved data-model and persistence decisions.

### 7.2. Project contents

A project should preserve the information necessary to understand its scientific work.

Depending on implemented capabilities, this may include:

- Observational datasets and references.
- Molecular reference datasets.
- Source metadata and provenance.
- Selected spectral regions and candidate molecules.
- Analysis configurations and processing parameters.
- Validation outcomes and warnings.
- Comparison outputs and annotations.
- Links between derived results and their input datasets.

The project model must not imply that a result is reproducible if required inputs or processing details were not retained.

### 7.3. Project lifecycle

The intended project lifecycle includes creating, saving, reopening, updating, and exporting research work.

Project operations must handle missing, invalid, or incompatible data explicitly. Updating a project must not silently discard information or replace an existing result without appropriate safeguards.

Where project formats or storage schemas evolve, migration behavior should be documented and tested.

### 7.4. Analysis history

When analysis capabilities are introduced, ECAS should preserve enough information to distinguish one analysis from another.

Relevant records may include:

- Input dataset identifiers and versions.
- Processing operations and parameters.
- Method and software version.
- Configuration and acceptance criteria.
- Warnings and validation results.
- Outputs and uncertainty information.
- Date of execution and other relevant context.

A new analysis should not silently overwrite the historical record of a previous result.

---

## 8. Multiple Observations and Comparative Research

Comparing multiple observations is an important long-term objective, but it requires more than placing multiple curves on a graph.

ECAS should preserve the identity and context of each observation, including relevant differences in:

- Observation date and observing conditions.
- Telescope and instrument.
- Data-release version and processing pipeline.
- Spectral coverage and resolution.
- Units, normalization, and calibration.
- Measurement uncertainties and data quality.
- Source publications and provenance.

Before combining observations, the application should assess whether the operation is scientifically justified.

Potential workflows include comparing observations independently, aligning compatible datasets, examining repeated features, evaluating consistency across instruments, and investigating differences over time.

Any combined result must retain traceable links to the contributing observations and transformations.

Differences between observations must not automatically be interpreted as atmospheric variability. Instrumental, observational, calibration, and processing effects may provide alternative explanations.

---

## 9. User Interface and Research Workflow

### 9.1. Design objective

The intended interface should provide a coherent path from data selection to inspection, analysis, interpretation, and preservation of results.

The interface must expose relevant scientific context and limitations without requiring users to infer hidden assumptions from a graph or numerical score.

The current application uses PySide6 for its desktop interface and PyQtGraph for spectral visualization, as recorded in the supplied project documentation. These are current implementation details, not a claim that the complete intended research interface already exists.

### 9.2. Intended workflow

The long-term interface may provide the following functional areas:

- **Planet and observation selection:** identify targets and their available datasets.
- **Data library:** browse local observational and reference data, with source and metadata information.
- **Analysis workspace:** inspect spectra, choose compatible inputs, and configure supported methods.
- **Results and interpretation:** display outputs alongside assumptions, uncertainty, warnings, and provenance.
- **Project management:** save, reopen, and organize research work.
- **Reporting and export:** preserve and communicate selected data and results.

These areas describe intended workflow responsibilities. Their presence in this document does not establish that they are implemented as separate screens, modules, or complete features.

### 9.3. Scientific visualization

Visualization should help users inspect data without implying unsupported conclusions.

Plots should present appropriate axis labels and units when known, preserve the distinction between observational and reference datasets, and communicate relevant uncertainty or quality information when available.

Missing metadata must not be replaced with invented units or physical interpretations.

Where multiple datasets are displayed together, the interface should make their identities and relevant differences clear.

### 9.4. Error and status communication

The interface should distinguish among successful operations, validation failures, warnings, incomplete operations, and inconclusive outcomes.

Messages should identify the affected data or operation and explain what can be done next when practical.

An operation that completes without an exception must not automatically be described as scientifically valid.

---

## 10. Reporting and Export

ECAS should eventually support exporting scientific data and analysis records in forms suitable for inspection, sharing, and further research.

The precise export formats and scope should be selected according to implemented capabilities and user requirements.

Where applicable, exports should preserve:

- Dataset identity and source attribution.
- Relevant units and metadata.
- Processing and transformation history.
- Analysis methods and configuration.
- Results and uncertainty information.
- Validation outcomes and warnings.
- Known limitations and interpretation boundaries.
- Software and dataset versions.

Plots and reports should distinguish source measurements from processed data, model outputs, and interpretations.

A report must not omit qualifications that materially affect the meaning of a result. Exported findings should remain interpretable without relying on undocumented assumptions from the application session.

---

## 11. Software Architecture Philosophy

### 11.1. Incremental and evidence-based development

ECAS should be developed in small, verifiable increments.

Each change should have a defined objective, controlled scope, acceptance criteria, and proportionate verification. Existing behavior should be preserved unless an approved change requires otherwise.

Architectural proposals should guide development without being confused with completed implementation.

### 11.2. Separation of responsibilities

The intended architecture should separate user-interface behavior, scientific data models, ingestion, persistence, visualization, validation, and analytical methods where doing so improves clarity and maintainability.

These boundaries should reduce unnecessary coupling and allow scientific methods to be tested independently of the GUI.

The exact module structure must follow verified code and approved architecture decisions. This blueprint does not establish that every proposed responsibility already has a dedicated implementation module.

### 11.3. Scientific logic and interface independence

Scientific calculations and validation rules should not depend unnecessarily on GUI behavior.

Where practical, data processing and analysis should be testable independently, with clear inputs, outputs, errors, and assumptions.

The interface should communicate scientific outcomes rather than silently determine them through presentation logic.

### 11.4. Data and metadata consistency

Data models should represent the scientific meaning of their contents without inventing information that the source does not provide.

Required and optional metadata should be explicit. Unit conversion, schema mapping, and data transformations should be traceable and tested.

A technically valid representation is not necessarily scientifically complete.

### 11.5. Controlled extensibility

New data sources, formats, analytical methods, and storage capabilities should be introduced through documented requirements and decisions.

Extensibility must not become an excuse for unnecessary abstractions, speculative infrastructure, or unverified compatibility claims.

Changes should solve an established need while preserving a clear path for future development.

### 11.6. Architecture and implementation status

The architecture documents describe system boundaries, requirements, and proposed designs in greater detail.

`docs/brains/PROJECT_STATE.md` is the primary record of verified implementation status, and `docs/brains/DECISIONS.md` records approved technical decisions and their implementation status.

When this blueprint and the code differ, use the current implementation and authoritative project records to establish what exists. Revise the blueprint when a meaningful change to the intended design is approved.

---

## 12. Technology and Tooling Direction

ECAS is a Python project.

The supplied repository documentation identifies the following technologies in the current implementation:

- **Python:** primary implementation language.
- **PySide6:** desktop application interface.
- **PyQtGraph:** spectral visualization.
- **SQLite:** persistence for the currently implemented spectrum-storage workflow.
- **JSON serialization:** representation of spectrum data in the current SQLite storage implementation.
- **pytest:** automated test framework.

These technologies describe the documented implementation snapshot. They do not establish that all long-term capabilities have been completed or that the current architecture cannot evolve through an explicit decision.

Future dependencies should be introduced only when justified by a defined requirement.

Dependency selection should consider scientific suitability, maintainability, compatibility, licensing, platform support, testability, and the cost of long-term maintenance.

The project must not introduce a new framework, database, or scientific library merely because it might be useful later. Proposed changes should identify the concrete requirement, alternatives, consequences, and verification strategy.

---

## 13. Data Integrity, Reliability, and Security

### 13.1. Input integrity

Imported data must be checked against the requirements of the supported input path.

Validation may include file readability, schema recognition, column selection, numeric conversion, missing values, malformed records, and other format-specific constraints.

An importer must not silently reinterpret an unsupported file as a scientifically valid dataset.

Successful parsing does not establish that the data have the correct physical meaning or are suitable for analysis.

### 13.2. Persistence integrity

Persistence operations must preserve the intended relationship between stored data and metadata.

Database errors, invalid identifiers, malformed records, and incomplete operations should be handled explicitly.

Operations that replace or remove data require appropriate safeguards and clear behavior. The actual transaction and connection-management patterns must be documented according to the current implementation and approved decisions.

### 13.3. Provenance integrity

Source identifiers, metadata, and processing history must remain associated with the datasets and results they describe.

A derived dataset must not be presented as an untouched original. Where provenance cannot be established, that limitation must be communicated.

### 13.4. Reproducibility and recovery

Data should be stored and updated in ways that support verification and recovery where practical.

Future requirements may include integrity checks, version-aware updates, backup and recovery procedures, and detection of missing or corrupted resources.

Such capabilities must be implemented and tested before they are described as available.

### 13.5. Security and filesystem safety

File paths, project identifiers, imported content, and external resources must be handled defensively.

The application should avoid unintended path traversal, unsafe file operations, accidental data loss, and uncontrolled execution of imported content.

External data must be treated as data, not as trusted instructions or executable behavior.

Security controls should be proportionate to the actual application and its supported workflows.

---

## 14. Extensibility and Future Development

ECAS should be capable of expanding toward its scientific objectives without repeatedly replacing its core architecture.

Potential future areas include:

- Additional scientific data sources and archive schemas.
- Broader support for observational file formats, including applicable text-based formats.
- Molecular reference retrieval and local caching.
- Improved dataset metadata and provenance.
- Project-level research organization.
- Compatibility assessment and data preparation.
- Quantitative spectral comparison.
- Uncertainty-aware analysis.
- Multi-observation comparison.
- Reporting and export.
- Atmospheric modeling or retrieval where justified.

These are development directions, not statements of current functionality.

Each capability should be introduced through a bounded plan that identifies requirements, dependencies, data assumptions, acceptance criteria, and tests.

A new capability should not be considered complete merely because a module exists or a demonstration succeeds. Completion requires verification appropriate to its intended use.

---

## 15. Development and Change Philosophy

### 15.1. Small, controlled increments

Development should proceed in manageable steps, each with a clear objective and explicit completion criteria.

A task should avoid combining unrelated features or expanding into speculative redesign.

Existing tests, decisions, and implementation constraints should be inspected before proposing changes.

### 15.2. Evidence-based verification

Implementation claims must be supported by actual evidence.

Verification should distinguish among:

- Requirements that have been documented.
- Plans that have been approved.
- Code that has been implemented.
- Tests that have been written.
- Tests that have actually run.
- Behavior that has been manually verified.
- Scientific methods that have been evaluated.

A planned test is not an executed test. A passing test is evidence only for the behavior it exercises.

### 15.3. Documentation as part of development

Documentation must remain consistent with the code and approved decisions.

When a change affects the implementation, update the appropriate project-state record, decision record, architecture document, or development history.

Historical plans should retain their historical meaning. They must not be rewritten to imply that a later implementation or decision existed earlier.

Prefer targeted updates to existing documents rather than creating duplicate sources of truth.

### 15.4. Scientific conservatism

When a scientific requirement is unclear, do not fill the gap with arbitrary thresholds, guessed units, fabricated metadata, or unsupported assumptions.

Identify the uncertainty, establish what evidence is available, and determine what additional decision or data is needed.

Where the evidence does not support a conclusion, preserve that limitation rather than forcing a definitive result.

### 15.5. Long-term maintainability

Code and documentation should be understandable to future contributors, including contributors using different development tools or AI agents.

Technical decisions should have a clear rationale. Important non-obvious behavior should be documented where the code is maintained.

Maintainability must not be pursued through unnecessary abstraction or broad refactoring unrelated to the task at hand.

---

## 16. Project Knowledge and Documentation Authority

ECAS uses multiple documents because scientific direction, architecture, implementation status, technical decisions, and development history answer different questions.

They should remain consistent without duplicating one another unnecessarily.

### 16.1. Master design blueprint

**`docs/ECAS.md` — this document**

Defines:

- Project purpose and scientific vision.
- Long-term objectives.
- Scientific principles and constraints.
- Intended data and analysis capabilities.
- Design philosophy and future direction.

It is not the authoritative record of whether a feature is currently implemented.

### 16.2. Repository entry point

**`README.md`**

Provides the practical introduction to ECAS, its current application, repository navigation, setup, testing, contribution workflow, and known limitations.

The README should help a person understand how to approach the repository without repeating the complete scientific blueprint.

### 16.3. AI agent operating instructions

**`AGENTS.md`**

Defines cross-tool instructions for AI agents working on ECAS, including context loading, scope control, code changes, verification, documentation updates, reporting, and handoffs.

Agent instructions govern how work is performed. They do not override approved scientific requirements or establish implementation facts.

### 16.4. Project state

**`docs/brains/PROJECT_STATE.md`**

Records verified implementation status, completed work, current limitations, outstanding tasks, and relevant repository structure.

It must distinguish completed behavior from reported, planned, or unverified work. It should be updated when meaningful implementation status changes.

### 16.5. Technical decisions

**`docs/brains/DECISIONS.md`**

Records approved technical and architectural decisions, their rationale, scope, consequences, and implementation status.

A proposed design must not be treated as an approved decision unless the project records establish that status.

### 16.6. Architecture documentation

The documents under `docs/architecture/` provide more detailed architectural requirements and design descriptions.

Their responsibilities include:

- **`ARCHITECTURE.md`:** overall system structure, architectural principles, and boundaries.
- **`DATA_FLOW.md`:** current and intended movement of data through the application.
- **`DATA_MODELS.md`:** domain entities, data representations, and relationships.
- **`ECAS_Architecture_Specification.md`:** broader architecture requirements and design specification.
- **`MODULE_RESPONSIBILITIES.md`:** module roles, boundaries, and dependencies.
- **`VALIDATION_STRATEGY.md`:** software and scientific validation requirements, evaluation methods, and evidence.

These documents may describe target designs or provisional requirements. Their contents must not be interpreted as proof that the corresponding functionality exists.

### 16.7. Development plans and historical records

Chunk plans, implementation logs, and related development records preserve the reasoning, scope, and progress of individual work periods.

They are valuable historical context, but they do not automatically override current code, approved decisions, or verified project-state records.

The current repository determines which planning files and folder organization are authoritative. Contributors should not create duplicate histories or move records without a clear reason.

### 16.8. Resolving discrepancies

When project documents disagree:

1. Identify the specific claim or decision in conflict.
2. Inspect the current code and relevant tests when implementation behavior is at issue.
3. Consult the appropriate authoritative document for the question.
4. Distinguish verified facts, approved decisions, proposed designs, and unresolved questions.
5. Resolve the discrepancy explicitly in the appropriate document.

No single document should be used as a substitute for verifying evidence that belongs to another authority.

---

## 17. Definition of Project Success

ECAS will progress toward its intended purpose as it establishes the following capabilities and qualities.

### 17.1. Reliable data handling

Supported scientific data can be imported, validated, stored, retrieved, and identified without silently losing relevant information or provenance.

Unsupported inputs and incomplete metadata are handled transparently.

### 17.2. Traceable scientific evidence

Datasets, references, transformations, and results can be traced to their origins and relevant versions.

The application distinguishes source information from processed values and interpretations.

### 17.3. Defensible analysis

Spectral comparisons use methods appropriate to the data and scientific question.

Assumptions, uncertainties, compatibility limitations, and alternative explanations are communicated rather than hidden behind an apparently definitive score.

### 17.4. Reproducible research

The system preserves sufficient context to understand and, where dependencies permit, reproduce previous analyses.

Changes to data, methods, or configurations can be distinguished from earlier work.

### 17.5. Maintainable software

The architecture supports incremental development, independent verification of scientific logic, clear module responsibilities, and controlled extension.

Changes are documented and tested in proportion to their impact.

### 17.6. Honest capability reporting

The project accurately distinguishes current functionality from planned capabilities.

Tests and verification records describe what was actually executed and what their results establish.

Scientific claims remain limited to the evidence provided by the data and methods.

---

## 18. Governing Principle

**ECAS must be developed as a reliable scientific research tool, not merely as software that runs or produces visually convincing comparisons.**

Its value depends on the integrity of its data, the traceability of its methods, the transparency of its assumptions, the defensibility of its conclusions, and the ability to understand and verify its behavior.

Every new capability should advance the scientific objectives without weakening those principles.

When convenience, implementation speed, or presentation conflicts with scientific integrity, scientific integrity takes precedence.

---

## 19. Revision Policy

Revise this blueprint when approved changes materially affect the project's scientific objectives, core principles, intended capabilities, or long-term design direction.

Implementation progress alone does not require rewriting the scientific vision. Record ordinary implementation changes in `PROJECT_STATE.md`, technical decisions in `DECISIONS.md`, and detailed architectural changes in the relevant architecture documents.

When a previously intended capability becomes implemented, update the appropriate implementation and architecture records first. Revise this blueprint only when its requirements, direction, or description of intended capabilities needs to change.

Changes to this document should preserve the distinction between scientific requirements, proposed capabilities, approved decisions, and verified implementation.

---

**End of master design blueprint.**