# ECAS Data Models

**Project:** ECAS — Exoplanetary Characterization & Astrochemistry Suite  
**Document status:** Draft for review  
**Implementation status:** Conceptual design only; this document does not authorize implementation.  
**Primary language:** Python

---

## 1. Purpose

This document defines the conceptual data models required by ECAS. It describes the information the application must preserve, the relationships between scientific datasets and research projects, and the requirements for data identity, provenance, persistence, and reproducibility.

ECAS currently supports local CSV import, a `SpectrumData` representation, SQLite persistence, and spectral visualization. The future workflow is intended to expand to astronomical archive retrieval, molecular reference datasets, scientific compatibility assessment, spectral preparation, comparison, and benchmark validation.

This document distinguishes existing implementation from proposed capabilities. A conceptual entity described here does not imply that a corresponding Python class, database table, or feature already exists.

### 1.1 Governing principles

The data model must support the following principles:

1. **Preserve scientific meaning.** Spectral coordinates, signal quantities, units, and data types must not be silently reinterpreted.
2. **Preserve source information.** Datasets must remain traceable to their original files, archives, publications, or other sources.
3. **Preserve original inputs.** Processing must not silently overwrite original scientific data.
4. **Represent uncertainty honestly.** Missing uncertainty information must remain distinguishable from known zero uncertainty.
5. **Separate validation stages.** Successful parsing does not establish scientific validity or comparability.
6. **Support reproducibility.** Saved analyses must identify the inputs, processing steps, method, configuration, and outputs used.
7. **Support offline access.** Saved records and available local artifacts must remain inspectable without contacting their original sources.
8. **Preserve history.** Updating a dataset must not silently change the inputs associated with an earlier analysis.
9. **Avoid unnecessary complexity.** Conceptual entities may share implementation classes or storage structures where their scientific meaning and identity remain clear.
10. **Avoid unsupported conclusions.** A candidate score or spectral correspondence must not automatically be represented as a confirmed molecular detection.

### 1.2 Status terminology

- **Implemented:** Verified as part of the current application baseline described in this document.
- **Required:** A requirement established by the project's scientific or functional goals.
- **Proposed:** A recommended design awaiting review or implementation.
- **Unresolved:** A decision requiring further evidence or explicit approval.

These labels describe the status of the design or capability, not the existence of a particular database table or class.

---

## 2. Current implementation baseline

The current application uses Python, PySide6 for the desktop interface, PyQtGraph for spectral plotting, and SQLite for structured persistence.

The following behavior is established by the current development record:

| Area | Current status |
|---|---|
| Local CSV import | Implemented for the supported importer schema |
| `SpectrumData` | Implemented as a frozen data model |
| Source path and column information | Preserved by the existing model |
| Scientific units and signal meaning | May be unknown; must not be inferred without evidence |
| Import validation | Implemented for supported structural and numeric checks |
| Scientific comparability assessment | Not established as a complete workflow |
| SQLite persistence | Implemented for existing spectrum records |
| Spectrum save/load | Verified through persistence round-trip tests |
| Spectral plotting | Implemented for imported data |
| Online astronomical archive integration | Future capability; verify current status before implementation |
| Molecular reference library | Future capability unless separately verified |
| Derived-spectrum provenance | Not established as a complete workflow |
| Reproducible comparison records | Future capability |

The precise current implementation must be checked against the working repository before any implementation task. This table is not a substitute for current code inspection or test execution.

### 2.1 Existing `SpectrumData`

The current `SpectrumData` model represents imported spectral measurements in a form that can be validated, persisted, and plotted.

Its existing persistence contract covers seven fields, including the source file, column information, units, signal type, and import warnings. The exact field names and types remain defined by the implemented model and persistence code.

The existing model is suitable for the current import-and-plot workflow, but it must not automatically be treated as a complete representation of every future ECAS dataset.

In particular, an astronomical observation, an experimental molecular spectrum, a calculated spectrum, and a theoretical line list can require different metadata and scientific interpretation.

Future extensions must preserve the existing import, persistence, and plotting behavior unless an explicitly reviewed change requires otherwise.

---

## 3. Conceptual model overview

The following entities describe the proposed scientific and persistence model.

| Entity | Responsibility | Status |
|---|---|---|
| `Planet` | Stable identity of an astronomical target | Proposed |
| `Project` | Workspace organized around one planet | Proposed; reconcile with existing persistence |
| `SourceRecord` | Origin and access information for a dataset | Proposed |
| `DatasetVersion` | Identity of a particular source-data version | Proposed |
| `StoredArtifact` | Original files and derived data stored locally | Proposed |
| `Observation` | Astronomical observation and its associated metadata | Proposed |
| `SpectrumData` | Numeric spectral data representation | Implemented; extensions unresolved |
| `Molecule` | Stable molecular identity | Proposed |
| `ReferenceDataset` | Molecular reference dataset and its scientific category | Proposed |
| `LineListData` | Molecular transition data | Proposed |
| `PreparedSpectrum` | A derived spectrum created for a defined purpose | Proposed |
| `TransformationRecord` | Record of a processing operation | Proposed |
| `ComparabilityAssessment` | Evaluation of compatibility for a selected method | Proposed |
| `AnalysisRun` | One execution of a comparison workflow | Proposed |
| `AnalysisInput` | The exact datasets and derived inputs used in an analysis | Proposed |
| `CandidateResult` | A method-defined result for a candidate molecule | Proposed |
| `BenchmarkCase` | A documented scientific evaluation case | Proposed |
| `ValidationRun` | Evaluation of a method against benchmark cases | Proposed |
| `Citation` | Attribution to a publication, catalog, or data source | Proposed |
| `QualityIssue` | A validation error, warning, or limitation | Proposed |
| `ResearchNote` | User-authored project context | Optional future capability |

These are logical entities, not a requirement to create one module, class, or table for every row.

### 3.1 Relationship overview

The intended relationships are:

```text
Planet
  └── Project
        ├── Observation
        │     ├── SourceRecord
        │     ├── DatasetVersion
        │     └── StoredArtifact
        │
        ├── AnalysisRun
        │     ├── AnalysisInput
        │     │     ├── Observation
        │     │     ├── ReferenceDataset
        │     │     └── PreparedSpectrum
        │     └── CandidateResult
        │
        └── ResearchNote

Molecule
  └── ReferenceDataset
        ├── SourceRecord
        ├── DatasetVersion
        ├── LineListData, where applicable
        └── StoredArtifact

Source datasets
  └── TransformationRecord
        └── PreparedSpectrum

ComparabilityAssessment
  └── Assessment of specified inputs for a specified method

BenchmarkCase
  └── ValidationRun
        └── ValidationMetricResult
```

The diagram is conceptual. Exact relationships, ownership rules, and storage boundaries require implementation-level design before schema creation.

---

## 4. Identity, identifiers, and versioning

### 4.1 Internal identifiers

ECAS should assign stable internal identifiers to records that must be referenced independently of filenames, display names, or external services.

Relevant records include projects, observations, reference datasets, source records, artifacts, analyses, and derived datasets.

An internal identifier must not change merely because a display name or source URL changes.

The identifier format is unresolved. It should be chosen consistently across the persistence layer and should not be introduced separately by individual modules.

### 4.2 External identifiers

External identifiers must be stored with their source context.

For example, a planet identifier supplied by an astronomical archive must remain distinguishable from a molecule identifier supplied by a spectroscopic database.

Where a source provides multiple identifiers, ECAS should retain those needed to retrieve, disambiguate, or cite the record.

An external identifier must not be assumed to be globally unique unless the source defines it that way.

### 4.3 Dataset identity

A dataset's identity must distinguish the scientific record from the file used to represent it.

The same scientific record may be available in multiple formats or through multiple URLs. Conversely, files associated with the same target may represent different observations, processing versions, or spectral products.

ECAS should distinguish, where applicable:

- Scientific record identity.
- Source or provider identity.
- Source-data version.
- Local artifact identity.
- Derived-data identity.

A filename alone is insufficient to establish dataset identity.

### 4.4 Content identity and versioning

Where practical, ECAS should use a content hash to detect identical stored artifacts and identify changes to downloaded files.

A content hash identifies the bytes that were hashed. It does not, by itself, establish scientific equivalence between two datasets.

When a provider publishes a revised dataset, the new version must not silently replace the version used by a previous analysis.

An analysis should continue to identify its original inputs, even if newer versions become available.

The final versioning scheme and content-hash policy remain unresolved.

### 4.5 Timestamps

Timestamps should distinguish events such as:

- Source publication or release, where known.
- Source-data modification, where known.
- Local retrieval or import.
- Validation.
- Transformation.
- Analysis execution.
- Persistence or cache updates.

Unavailable source timestamps must not be replaced with invented publication or modification dates.

Retrieval timestamps should use a consistent representation, preferably timezone-aware UTC timestamps.

---

## 5. Astronomical entities

### 5.1 Planet

**Purpose:** Represent the astronomical target associated with a research project.

Proposed information includes:

- Stable internal identifier.
- Canonical planet name.
- External catalog identifiers.
- Source catalog or catalogs.
- Alternative names where relevant.
- Available target metadata and their provenance.

Target metadata should not be duplicated unnecessarily across every observation.

If two sources disagree about a planet property, ECAS must retain enough source context to identify the disagreement rather than silently treating one value as universally authoritative.

The initial implementation need not model every known planetary property.

### 5.2 Project

**Purpose:** Organize research around one planet.

The intended project contains references to multiple observations, analysis runs, and project-specific information.

Proposed information includes:

- Internal project identifier.
- Associated planet identifier.
- Display name or label.
- Creation and modification timestamps.
- Relevant project settings.
- Links to associated observations and analyses.

The current persistence implementation already has project-related behavior. Its existing identifiers, path-handling rules, and lifecycle must be preserved and reconciled with this conceptual model.

A project must not require network access simply to open previously saved data.

---

## 6. Source and provenance models

### 6.1 SourceRecord

**Purpose:** Describe where a scientific dataset originated and how it can be identified or retrieved.

Proposed information includes:

- Source-record identifier.
- Provider or source name.
- External record identifier.
- Source URL or documented retrieval endpoint, where available.
- Record title or description.
- Access or retrieval method.
- Relevant source version or release identifier.
- Associated citations.
- Retrieval timestamp, where applicable.
- Source-specific metadata needed to reproduce retrieval.

Source-specific metadata should be retained without forcing every provider to supply identical fields.

A source record must not imply that the data were successfully downloaded merely because a catalog entry was discovered.

### 6.2 DatasetVersion

**Purpose:** Identify a particular version of an observation, reference dataset, or other source-derived dataset.

Proposed information includes:

- Internal version identifier.
- Associated scientific dataset.
- Source version or release, where provided.
- Content hash, where calculated.
- Retrieval timestamp.
- Relevant format or representation information.
- Relationship to a previous version, when established.

If a source does not publish version identifiers, ECAS may use locally recorded retrieval and content identity information. It must not fabricate an upstream version number.

### 6.3 StoredArtifact

**Purpose:** Represent a file or other persisted data artifact associated with a scientific record.

Artifacts may include:

- Original imported files.
- Downloaded source payloads.
- Parsed or normalized data files.
- Prepared spectra.
- Synthesized reference spectra.
- Plots, reports, or exports.

Proposed metadata include:

- Artifact identifier.
- Storage location or managed path.
- Artifact role and format.
- Related dataset or analysis.
- Content hash, where available.
- Creation or retrieval timestamp.
- Parent artifact or source dataset, where applicable.
- Integrity or availability status.

Structured records and larger file artifacts may use different storage mechanisms. SQLite is intended for structured records; the final file-storage layout remains unresolved.

An artifact record must not be considered valid merely because its database row exists. The application must account for missing, inaccessible, or corrupt files.

### 6.4 Citation

**Purpose:** Preserve attribution and allow users to identify the sources supporting a dataset or result.

Where available, citation information should include:

- Publication title.
- Authors.
- Publication year.
- DOI or another stable identifier.
- Source or archive name.
- Dataset identifier.
- Citation URL.
- Relevant access or licensing information.

Citations may relate to the source dataset, a published observation, a molecular reference, a benchmark, or a method.

A source URL is not necessarily a complete scientific citation. The model should retain both when both are available.

---

## 7. Observational data models

### 7.1 Observation

**Purpose:** Represent an astronomical observational product associated with a planet.

An observation is more than a numeric spectrum. It includes the identity and context needed to interpret the measurements.

Proposed information includes:

- Observation identifier.
- Associated planet and project identifiers.
- Source record and dataset version.
- Observation or product type.
- Instrument and observational metadata, where available.
- Spectral representation.
- Available units and coordinate definitions.
- Uncertainty and quality information.
- Processing status and relevant provenance.
- Links to the original source artifact and normalized data.

The model must distinguish an actual transmission-spectrum product from raw measurements or other astronomical products that require additional processing.

A catalog entry, publication record, or downloadable time series must not automatically be treated as a transmission spectrum.

Missing instrument or observational metadata must remain explicitly unknown.

### 7.2 SpectrumData

**Purpose:** Represent numerical spectral data used by the existing import, persistence, and visualization workflow.

The existing implementation must remain the starting point. Its current fields, validation behavior, and persistence contract must be inspected before changing its definition.

For future use, the conceptual spectral representation should be able to describe:

- Spectral coordinate values.
- Coordinate axis meaning and units.
- Signal values.
- Signal quantity and units.
- Optional uncertainty values.
- Optional quality indicators or masks.
- Relevant metadata and provenance references.
- Source column or field mappings where applicable.

These are conceptual requirements, not a claim that every field currently exists in `SpectrumData`.

A future extension may use a distinct data structure if doing so better preserves the scientific meaning of observations and references. Changes must not be made merely to force every data category into one class.

#### Spectral values and uncertainties

Coordinate and signal values must retain their relationship to the original input.

If an uncertainty column is absent, uncertainty must remain unavailable. It must not be represented as zero or silently estimated.

If some points have invalid or missing values, the application must distinguish source data from any filtered representation used for display or analysis.

Quality flags and data masks must not be discarded without a documented reason.

#### Storage decision

The current SQLite persistence layer stores the existing spectrum representation.

Any future model expansion must explicitly assess:

- Backward compatibility with existing saved spectra.
- Schema migration requirements, if any.
- Preservation of existing fields and `None` values.
- Whether larger arrays belong in structured records or file artifacts.
- Whether new metadata can be represented without ambiguous serialization.

These decisions must be made before implementing changes to the current persistence contract.

---

## 8. Molecular reference models

Molecular reference data require a distinct conceptual model from astronomical observations.

ECAS must distinguish experimentally measured spectra, experimentally derived products, calculated spectra, and theoretical line lists. Their numerical representations may differ even when they describe the same molecule.

### 8.1 Molecule

**Purpose:** Represent the identity of a molecular species.

Proposed information includes:

- Internal molecule identifier.
- Canonical name.
- Chemical formula.
- Available stable identifiers from recognized catalogs.
- Relevant isotopologue information, where applicable.
- Source and identity provenance.

Molecular names alone may be ambiguous. Where possible, identifiers and isotopologue information should be retained to distinguish records correctly.

The initial implementation need not support every isotopologue or chemical identity convention.

### 8.2 ReferenceDataset

**Purpose:** Represent a molecular reference dataset and the scientific meaning of its contents.

Each reference must identify its representation category, source, molecule or species identity, and applicable metadata.

Proposed categories include:

1. Measured or experimentally derived spectrum.
2. Theoretical or calculated spectrum.
3. Theoretical spectroscopic line list.

Proposed information includes:

- Reference dataset identifier.
- Associated molecule.
- Source record and dataset version.
- Representation category.
- Spectral region and coordinate definition, where applicable.
- Signal or transition-parameter definitions.
- Units.
- Available experimental or model conditions.
- Resolution or sampling information, where relevant.
- Available uncertainties and quality information.
- Processing or synthesis history, where applicable.
- Known limitations and citations.

The exact required fields depend on the representation category. A single set of mandatory spectral-array fields must not be imposed on all reference types.

#### Measured or experimentally derived spectra

These datasets originate from measurements or products derived from experimental measurements.

Where available, preserve:

- Experimental conditions, including temperature and pressure.
- Sample state and measurement configuration.
- Spectral coordinate and signal definitions.
- Units.
- Instrumental resolution and relevant processing details.
- Uncertainty and quality information.
- Source citation and measurement provenance.

An experimentally derived spectrum may already have been processed. ECAS must not assume that all experimental reference data are raw measurements.

Experimental conditions can affect scientific applicability. A valid laboratory measurement is not automatically a suitable reference for every astronomical observation.

#### Theoretical or calculated spectra

A calculated spectrum must be identifiable as a derived product rather than a direct experimental measurement.

Where available, preserve:

- Underlying model or theoretical source.
- Source line list or other input identities.
- Calculation or synthesis method.
- Software version.
- Physical conditions and assumptions.
- Line-profile and broadening settings, where applicable.
- Output units and spectral resolution.
- Subsequent processing history.

The model must preserve the relationship between the calculated output and the inputs used to generate it.

#### Theoretical line lists

A line list contains discrete transitions and associated parameters. It is not equivalent to a continuous measured spectrum.

The representation may contain:

- Transition positions.
- Transition strengths or intensities.
- Molecular and isotopologue identifiers.
- Lower-state energies and other physical parameters, where supplied.
- Broadening or line-shape parameters, where supplied.
- Units, parameter definitions, and source-specific quality information.

The actual fields depend on the source and line-list format.

A line list must not be passed to a method expecting a measured continuous spectrum without an explicit, scientifically justified conversion or synthesis step.

### 8.3 LineListData

**Purpose:** Represent structured transition data where a line list requires a representation distinct from a sampled spectrum.

This concept may be implemented as a specialized dataset model or as a typed reference representation. The choice remains unresolved until the first supported source and format are selected.

The representation must retain the meaning and units of transition parameters, molecular identifiers, and source metadata.

It must not rely on the existing `SpectrumData` model if doing so would require treating transition parameters as ordinary spectral signal values.

### 8.4 Synthesized reference spectra

A synthesized reference spectrum is a derived artifact generated from theoretical or other supported inputs.

It must retain links to:

- The underlying line list or source data.
- The synthesis method and software version.
- The physical conditions and assumptions.
- The selected spectral region and output grid.
- Line-profile, resolution, and broadening settings, where relevant.
- Any subsequent processing operations.

A synthesized reference is not an independent experimental measurement. Its identity and provenance must preserve that distinction.

---

## 9. Spectral preparation and comparability

### 9.1 PreparedSpectrum

**Purpose:** Represent a derived spectral dataset prepared for a specified analysis or other documented operation.

Potential preparation operations include unit conversion, masking, resampling, normalization, and resolution matching.

A prepared spectrum must retain:

- Its source dataset identities and versions.
- Its resulting coordinate and signal definitions.
- Output units.
- The processing operations applied.
- Relevant parameters and assumptions.
- Effects on uncertainties and quality information.
- Links to the corresponding transformation records.

A prepared spectrum must not replace the original source data.

Its output must remain identifiable as derived data, and its scientific meaning must be clear enough to determine whether it is appropriate for a particular operation.

### 9.2 TransformationRecord

**Purpose:** Record a processing operation that creates or modifies a derived scientific representation.

Proposed information includes:

- Transformation identifier.
- Transformation name and version.
- Input dataset identities.
- Output dataset or artifact identity.
- Parameters and settings.
- Input and output units.
- Execution timestamp.
- Relevant software version.
- Assumptions, warnings, and limitations.

Transformation records must distinguish a documented conversion from an undocumented alteration.

The initial release need not implement every possible transformation. Only operations required by the selected workflow should be implemented.

### 9.3 ComparabilityAssessment

**Purpose:** Record whether specified datasets are suitable for use together by a specified comparison method.

Comparability is contextual. Two datasets may be suitable for one operation and unsuitable for another.

A proposed assessment should identify:

- Input dataset identities and versions.
- The intended comparison method.
- The checks performed.
- The assessment outcome.
- The reasons for warnings or incompatibility.
- Any required preparation or additional user decisions.
- The limitations that remain.

Possible outcomes are:

- Compatible.
- Compatible with limitations.
- Conditionally compatible.
- Incompatible.
- Undetermined.

The assessment must distinguish structural validity from scientific comparability. Two arrays that contain valid numeric values are not necessarily scientifically comparable.

---

## 10. Analysis models

### 10.1 AnalysisRun

**Purpose:** Represent one execution of a comparison workflow.

Proposed information includes:

- Analysis identifier.
- Associated project.
- Exact input dataset identities and versions.
- Selected comparison method and version.
- Configuration and relevant settings.
- Preparation and comparability records.
- Software version and relevant execution information.
- Start time and completion time, where available.
- Execution status.
- Output records and artifact references.
- Warnings, errors, and limitations.

Possible execution states include pending, running, completed, failed, and incomplete. Final status values must be defined consistently during implementation.

A failed analysis must not be represented as a successful result.

### 10.2 AnalysisInput

**Purpose:** Record the specific role of each input to an analysis.

An analysis may use multiple observations, molecular references, or prepared datasets.

The record should identify the input, its role, its exact version or content identity, and any derived representation used by the method.

This ensures that a saved analysis remains traceable even if a source dataset is subsequently updated.

The final representation may use relational records or another structure consistent with the chosen persistence design.

### 10.3 Comparison method identity

The analysis record must identify the comparison method and the version or implementation identity required to interpret its output.

It should preserve relevant settings and distinguish method-specific outputs from universally defined scientific quantities.

The first comparison method and its exact configuration requirements remain unresolved pending benchmark investigation.

### 10.4 CandidateResult

**Purpose:** Represent a method-defined result associated with a candidate molecule.

Proposed information includes:

- Candidate-result identifier.
- Associated analysis.
- Candidate molecule identity.
- Method-defined score or output values.
- Definitions and units for reported quantities, where applicable.
- Diagnostic information.
- Available uncertainty or statistical information.
- Warnings and limitations.
- Result status.

The model must not assume that all comparison methods produce the same score type.

A score must not be labeled as a probability unless its probabilistic interpretation has been justified and validated.

A candidate ranking must not be represented as a confirmed detection or quantitative abundance estimate without appropriate scientific support.

### 10.5 PublishedResult

Published scientific results may be associated with observations, benchmark cases, or candidate interpretations.

Where needed, ECAS should retain the publication, source, identifiers, reported conclusion, and relevant caveats.

Published results must remain distinguishable from results generated by ECAS. The application must not imply that a reproduced candidate score independently verifies the conclusion of a publication.

This concept may be combined with benchmark and citation records if a separate entity is unnecessary.

---

## 11. Validation models

### 11.1 BenchmarkCase

**Purpose:** Describe a documented scientific case used to evaluate a comparison method.

Proposed information includes:

- Benchmark identifier.
- Associated astronomical target or observation.
- Relevant molecular candidate or candidates.
- Source data and versions.
- Supporting publication or citation.
- Reported scientific conclusion and its scope.
- Classification as a detection, non-detection, control, or another documented case type.
- Data-quality and interpretation limitations.
- Inclusion rationale.

Benchmark inclusion must be evidence-based. A published claim is not automatically a suitable benchmark if the required data are inaccessible or insufficiently documented.

### 11.2 ValidationRun

**Purpose:** Record an evaluation of a comparison method against a defined benchmark set.

Proposed information includes:

- Validation-run identifier.
- Benchmark cases and versions.
- Method identity and configuration.
- Evaluation settings.
- Software version.
- Execution status.
- Summary outputs and limitations.

Where feasible, development or tuning cases should be distinguished from evaluation cases used to estimate performance.

A validation run must preserve enough information to reproduce or investigate its results.

### 11.3 ValidationMetricResult

**Purpose:** Record a metric calculated during a validation run.

Each metric must retain its definition and applicable interpretation. Metrics from different evaluation procedures must not be assumed to be interchangeable.

The model should support metrics appropriate to the selected task without prematurely specifying a universal metric set.

Threshold selection, benchmark inclusion rules, and the scientific interpretation of validation performance are governed by `VALIDATION_STRATEGY.md`.

---

## 12. Quality and validation records

### 12.1 Structural validation versus scientific suitability

The data model must distinguish at least three concerns:

1. **Parsing:** Can the source representation be read?
2. **Structural and metadata validation:** Does the resulting dataset meet the requirements for its declared role?
3. **Scientific suitability:** Is the dataset appropriate for a particular operation?

These are separate checks. A dataset may pass parsing but fail structural validation. A structurally valid dataset may still be unsuitable for a selected comparison method.

Validation outcomes must identify the scope of the checks performed.

### 12.2 QualityIssue

**Purpose:** Represent a validation error, warning, or limitation associated with a dataset or operation.

Proposed information includes:

- Issue identifier.
- Related dataset, artifact, or operation.
- Severity.
- Category or rule identifier.
- Description.
- Affected field or data region, where applicable.
- Whether the issue prevents a particular operation.
- Suggested corrective action, where appropriate.

Quality issues must distinguish conditions that prevent an operation from warnings that permit limited use.

The exact categories and severity values remain unresolved until the validation rules for supported formats and methods are defined.

### 12.3 Missing and unknown information

Unavailable information must remain distinguishable from known values.

Examples include:

- Unknown units.
- Unreported uncertainty.
- Missing instrument metadata.
- Unknown experimental conditions.
- Unavailable source-version identifiers.

The application must not invent scientific metadata to fill gaps.

If the user supplies a missing value or a value is derived through a documented process, the source of that information should be recorded where it materially affects interpretation.

---

## 13. User annotations and research notes

### 13.1 ResearchNote

A future project may support user-authored notes associated with observations, references, analyses, or the project as a whole.

Where implemented, notes should have stable identifiers and retain their association with the relevant records.

User annotations must remain distinguishable from source-provided metadata and automatically generated scientific results.

This capability is optional for the initial archive-integration proof of concept unless existing project behavior establishes a specific requirement.

---

## 14. Persistence and storage boundaries

### 14.1 SQLite responsibilities

SQLite is the established structured persistence mechanism.

It currently stores the existing spectrum records. Future structured records may include projects, observations, reference metadata, analysis configurations, results, and provenance relationships.

The final schema must be derived from the supported workflow and verified implementation requirements rather than created solely to mirror every conceptual entity in this document.

Schema migrations, referential integrity rules, and versioning behavior require explicit design before new persistent entities are introduced.

### 14.2 File storage responsibilities

Files may hold larger scientific data and artifacts, including original source files, downloaded payloads, prepared datasets, synthesized spectra, plots, and reports.

The storage design must define how file artifacts relate to structured records.

Paths must be handled safely. A database record must not be treated as proof that its referenced file still exists or is intact.

The final storage locations, cache layout, and artifact lifecycle rules remain unresolved.

### 14.3 Storage integrity

Persistence operations must avoid reporting success when required records or artifacts have not been stored successfully.

The design should account for failures that could leave a record pointing to a missing artifact or an analysis marked complete despite incomplete persistence.

The appropriate transaction boundaries and recovery procedures depend on the final storage design.

Existing project-ID validation and path-safety behavior must not be weakened by future changes.

### 14.4 Updates and deletion

Refreshing an observation or reference must not silently change the inputs of historical analyses.

Deletion behavior must account for dependencies. Removing a shared reference artifact, for example, must not silently make historical results appear reproducible when their required inputs are no longer available.

Exact deletion, retention, and cache-invalidation policies remain unresolved.

### 14.5 Schema migrations

Any change to the existing persisted `SpectrumData` representation must consider saved databases and backward compatibility.

A migration must preserve existing values and relationships to the extent required by the approved design. It must not silently assign scientific meaning to previously unknown fields.

Migration strategy and schema versioning must be specified before a persistent schema change is implemented.

---

## 15. Offline access and reproducibility

Saved records should remain interpretable without a live connection to the source provider.

Where the required data and software are locally available, ECAS should support inspecting saved projects, observations, references, analysis results, and relevant processing history.

An offline rerun must use the intended recorded inputs. It must not silently substitute a newer or unrelated dataset.

For reproducibility, an analysis should preserve enough information to establish:

- Which observation and reference datasets were used.
- Which source versions or content identities were used.
- Which derived inputs and transformations were applied.
- Which comparison method and configuration were used.
- Which software version was involved.
- Which outputs and diagnostics were produced.
- Which warnings and limitations applied.

If a required source artifact or dependency is unavailable, the application should explain the limitation. It must distinguish inspecting a saved result from successfully reproducing the analysis.

Exact numerical reproducibility may depend on software and execution conditions. The stored record should preserve sufficient information to investigate discrepancies.

---

## 16. Proposed Python representation

The following illustrates conceptual relationships only. It is not a finalized class design, schema, or instruction to create these classes.

```text
Planet
  └── Project
        ├── Observation
        ├── AnalysisRun
        └── ResearchNote

SourceRecord
  ├── DatasetVersion
  ├── Citation
  └── StoredArtifact

Observation
  └── Spectral representation

Molecule
  └── ReferenceDataset
        ├── Measured spectral representation
        ├── Calculated spectral representation
        └── Line-list representation

Source dataset
  └── TransformationRecord
        └── PreparedSpectrum

Observation + ReferenceDataset
  └── ComparabilityAssessment
        └── AnalysisRun
              ├── AnalysisInput
              └── CandidateResult

BenchmarkCase
  └── ValidationRun
        └── ValidationMetricResult
```

The implementation should use the smallest set of classes and storage structures that preserves these distinctions.

In particular:

- Retain the existing `SpectrumData` model for its current supported role unless a reviewed requirement justifies changing it.
- Do not force line-list records into an ordinary sampled-spectrum representation.
- Avoid duplicate fields where a stable relationship to a source or dataset record is sufficient.
- Keep provider-specific response structures separate from the internal scientific representation.
- Keep data models independent of desktop UI state.
- Avoid building generic abstractions for providers or transformations before the first supported workflow demonstrates a need.

The exact Python types, public interfaces, and module boundaries must be reconciled with `ARCHITECTURE.md` and `MODULE_RESPONSIBILITIES.md` before implementation.

---

## 17. Unresolved decisions

The following decisions remain open and must not be treated as approved merely because this document describes the relevant concepts.

1. **Initial astronomical provider and product:** Determine which real archival observation can support the first retrieval proof of concept.
2. **Initial molecular reference provider:** Select a source based on scientific suitability, access requirements, and the chosen initial use case.
3. **Reference representation:** Determine whether the first reference is an experimentally measured spectrum, a calculated spectrum, or a theoretical line list.
4. **Model boundaries:** Decide whether observations and references share a common spectral data structure or require distinct typed representations.
5. **Minimum provenance fields:** Define the required source identifiers, version information, retrieval details, citations, and artifact identity for the initial workflow.
6. **Persistence extensions:** Determine whether archive integration requires new database tables, changes to existing records, or a smaller metadata extension.
7. **Artifact storage:** Establish file paths, content identity, integrity checks, and cache reuse behavior.
8. **Validation contracts:** Define structural requirements for each supported source representation.
9. **Uncertainty representation:** Determine how uncertainty arrays, quality masks, and incomplete values will be stored for the first supported products.
10. **Transformation records:** Specify the minimum information needed to preserve the history of the first implemented transformation, if one is required.
11. **Analysis records:** Finalize method-specific input and output requirements after benchmark and comparison-method investigation.
12. **Migration strategy:** Define how persistent model changes will preserve existing saved spectra.
13. **Deletion and retention:** Establish how shared references and derived artifacts can be removed without misleading historical records.
14. **Project and observation relationships:** Reconcile the proposed project model with the existing persistence and project-ID behavior.

Resolve these decisions incrementally as the actual source products, benchmark requirements, and implementation constraints become clear.

---

## 18. Data-model acceptance criteria

The conceptual design is ready to guide detailed implementation planning when the following requirements are understood and agreed upon.

### Current implementation compatibility

- [ ] The existing `SpectrumData` fields and persistence contract are documented accurately.
- [ ] Existing CSV import, persistence, and plotting behavior remains accounted for.
- [ ] Changes to persisted models include an explicit backward-compatibility assessment.
- [ ] Current implementation is distinguished from proposed capabilities.

### Scientific representation

- [ ] Astronomical observations are distinguishable from molecular reference data.
- [ ] Measured spectra, calculated spectra, and theoretical line lists remain distinct.
- [ ] Spectral coordinate and signal meanings are explicit or marked unknown.
- [ ] Units and uncertainty information are preserved where available.
- [ ] Missing metadata are not silently invented.
- [ ] Structural validity is distinct from scientific suitability.

### Provenance and persistence

- [ ] Dataset identity is distinguishable from filename and local storage path.
- [ ] Source identity, citations, and version information are retained where available.
- [ ] Original data remain distinguishable from derived products.
- [ ] Historical analyses identify their original inputs.
- [ ] Structured records and file artifacts have defined relationships.
- [ ] Offline access does not silently substitute different data.

### Analysis and validation

- [ ] Analysis records can identify their inputs, method, settings, and outputs.
- [ ] Method-specific result meanings and limitations are preserved.
- [ ] Failed or incomplete analyses cannot be represented as successful results.
- [ ] Benchmark cases retain their supporting evidence and interpretation limits.
- [ ] Candidate results do not automatically imply confirmed detections or abundance estimates.

These are design acceptance criteria. They do not claim that the corresponding capabilities are currently implemented or tested.

---

## 19. Relationship to other documents

This document defines conceptual data entities, their relationships, and the information that ECAS must preserve.

It should be read alongside:

- `docs/ECAS.md` — project purpose, scope, and scientific principles.
- `docs/architecture/ARCHITECTURE.md` — system boundaries and architectural decisions.
- `docs/architecture/DATA_FLOW.md` — movement of data through acquisition, validation, processing, and persistence.
- `docs/architecture/MODULE_RESPONSIBILITIES.md` — module ownership and interface responsibilities.
- `docs/architecture/VALIDATION_STRATEGY.md` — benchmark selection, evaluation metrics, and interpretation limits.
- `docs/brains/DECISIONS.md` — approved decisions and their rationale.
- `docs/brains/PROJECT_STATE.md` — verified implementation status.
- `docs/ECAS_development_plan.md` — development chunks and their completion criteria.

If the documents conflict, identify the discrepancy and review it explicitly. Do not resolve it by silently treating a proposed model as implemented or an unresolved design choice as approved.

---

## 20. Implementation boundary

This document does not authorize implementation, file creation, schema changes, migrations, dependency installation, or changes to existing application behavior.

Implementation planning should proceed from the verified repository state and the approved scientific workflow.

The first archive-integration proof of concept should determine the minimum additional data structures and persistence changes required to preserve one real source dataset and its provenance. Broader model extensions should follow only when justified by the supported workflow.

**Conclusion:** ECAS should preserve scientific meaning by representing observations, molecular references, derived spectra, and theoretical line lists according to their actual roles. The data model should support traceability, reproducibility, and offline inspection without forcing speculative complexity into the current application.