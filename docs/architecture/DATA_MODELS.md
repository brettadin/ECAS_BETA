# ECAS Data Models

**Document status:** Draft for review  
**Project:** Exoplanet Characterization and Spectral Analysis (ECAS)  
**Primary language:** Python  
**Implementation status:** Not authorized by this document  
**Authority:** Proposed data-model design consistent with `docs/ECAS.md`, `docs/architecture/ARCHITECTURE.md`, `docs/architecture/DATA_FLOW.md`, and the ECAS Architecture Specification — Draft 0.3.

---

## 1. Purpose

This document defines the conceptual data models required to support ECAS's initial workflow. It identifies the principal entities, their responsibilities, relationships, minimum information requirements, identity rules, and persistence considerations.

The initial application will handle exoplanet transmission-spectrum observations, molecular reference datasets, spectral preparation, comparison and candidate scoring, validation cases, and persistent research projects.

The purpose of this document is to establish a stable scientific data foundation without prematurely fixing every Python class, database table, file format, or numerical representation.

### 1.1 Design principles

All proposed models must support these principles:

1. **Scientific meaning:** Every spectral quantity must have an identifiable meaning and units, or explicitly record that the meaning or units are unknown.
2. **Provenance:** Data must remain traceable to their original sources and versions.
3. **Immutability of scientific inputs:** Processing and updates must not silently overwrite original data or alter the inputs of historical analyses.
4. **Explicit relationships:** Projects, observations, references, transformations, analyses, and results must be connected through stable identifiers.
5. **Reproducibility:** An analysis must preserve enough information to identify its inputs, configuration, method, and outputs.
6. **Uncertainty preservation:** Available measurement uncertainties, quality flags, and known limitations must be retained.
7. **Offline operation:** Saved projects and analyses must be interpretable without live access to their original online sources, provided required local records and artifacts remain available.
8. **Extensibility without speculation:** Models must accommodate the initial workflow and reasonable extensions without prematurely implementing full atmospheric retrieval or other deferred capabilities.

## Governing Documents
Module implementation must remain consistent with the project scope, architecture, data flow, data models, and validation strategy. The implementation plan defines the proposed build sequence and dependencies. If these documents conflict, agents must identify the conflict rather than silently choosing an interpretation. Proposed plans do not constitute implementation authorization.

ECAS.md

ARCHITECTURE.md

DATA_FLOW.md

DATA_MODELS.md

VALIDATION_STRATEGY.md

IMPLEMENTATION_PLAN.md

### 1.2 Model status terminology

This document uses three categories:

- **Required:** Needed to preserve established ECAS requirements.
- **Proposed:** A recommended design to review before implementation.
- **Unresolved:** Requires a later decision, scientific evidence, or confirmation of supported data formats.

A proposed field is not automatically an approved database column. Some information may be represented through relationships, structured metadata, or artifact files once the implementation design is finalized.

---

## 2. Conceptual model overview

The principal model groups are:

| Group | Main entities | Purpose |
|---|---|---|
| Astronomical identity | `Planet`, `Project` | Identify the target and organize research around it |
| Source and provenance | `SourceRecord`, `DatasetVersion`, `StoredArtifact` | Track origins, versions, retrieval, and stored files |
| Observational data | `Observation`, `SpectrumData` | Represent individual astronomical observations and spectral measurements |
| Molecular reference data | `Molecule`, `ReferenceDataset`, `LineListData` | Represent molecular identities and distinct reference-data types |
| Spectral processing | `PreparedSpectrum`, `TransformationRecord`, `ComparabilityAssessment` | Track derived data and whether inputs can be compared |
| Analysis | `AnalysisRun`, `AnalysisInput`, `CandidateResult` | Preserve comparison configuration, execution, and candidate-level results |
| Validation | `BenchmarkCase`, `ValidationRun`, `ValidationMetricResult` | Evaluate supported methods against documented benchmark cases |
| Supporting information | `Citation`, `QualityIssue`, `ResearchNote` | Preserve scientific attribution, warnings, and user-authored context |

These are logical entities. Some may be combined into a smaller number of implementation classes or database tables if that simplifies the system without losing important distinctions.

The model should not assume that each conceptual entity requires its own Python module or physical file.

---

## 3. Relationships between entities

The following diagram describes the proposed logical relationships. It does not prescribe a final relational schema.

```text
Planet
  └── Project
        ├── Observation ─────── SourceRecord
        │       └── SpectrumData / StoredArtifact
        │
        ├── AnalysisRun
        │       ├── AnalysisInput
        │       │      ├── Observation or ReferenceDataset
        │       │      └── PreparedSpectrum
        │       └── CandidateResult ───── Molecule
        │
        ├── ResearchNote
        └── Project-specific selections

Molecule
  └── ReferenceDataset ───── SourceRecord
          ├── DatasetVersion
          ├── SpectrumData
          ├── LineListData
          └── StoredArtifact

PreparedSpectrum
  ├── Source dataset identity
  └── TransformationRecord(s)

BenchmarkCase
  ├── Published evidence / Citation
  ├── Reference observations and expected interpretation
  └── ValidationRun
          └── ValidationMetricResult
```

Important distinctions:

- A planet is not an observation.
- A project is a user's research workspace, not the scientific dataset itself.
- A source record is not the data file it describes.
- A reference dataset is not necessarily a continuous spectrum.
- A prepared spectrum is derived data, not a replacement for its source.
- An analysis run is a particular execution, not merely a saved method configuration.
- A candidate result is an output of a specified method, not automatically a confirmed molecular detection.
- A published scientific conclusion is external evidence and must remain attributable to its authors.

---

## 4. Identity, identifiers, and versioning

### 4.1 Internal identifiers

**Required:** Persistent entities should have stable internal identifiers independent of display names and filesystem paths.

**Proposed:** Use opaque string identifiers for entities that may be referenced by projects, files, or exported records.

An identifier should not encode changeable metadata such as a planet's display name, a molecule's label, or a file's current path.

The exact identifier format is unresolved. UUIDs or another suitable stable identifier scheme may be evaluated during implementation planning.

### 4.2 External identifiers

Where available, retain provider-specific identifiers separately from internal identifiers.

Examples include:

- Planet catalog identifiers and aliases.
- Archive observation identifiers and accession numbers.
- Molecular database identifiers.
- Dataset release identifiers.
- DOI and publication identifiers.

External identifiers should be associated with their issuing provider or namespace. Two identical strings from different providers must not automatically be treated as the same record.

### 4.3 Content identity

**Proposed:** Use a cryptographic content hash, such as SHA-256, for stored files when practical.

A content hash helps detect identical files and verify that an artifact has not changed. It does not by itself establish that two files represent the same scientific dataset, that a dataset is authoritative, or that two differently encoded datasets are scientifically equivalent.

### 4.4 Dataset versions

A dataset may have several relevant identities:

- Its stable logical identity at a provider.
- A provider-declared release or version.
- A specific retrieved file or payload.
- A locally parsed representation.
- A derived or processed representation.

These must not be collapsed into a single version field if doing so would make historical inputs ambiguous.

A newly retrieved version must not silently replace the version used in an existing analysis.

### 4.5 Timestamps

Where relevant, distinguish:

- When an observation was collected.
- When a dataset was published or released.
- When ECAS retrieved or imported it.
- When a record was created in ECAS.
- When a record's descriptive metadata was last updated.
- When an analysis began and completed.

Store timestamps in a consistent machine-readable representation. The exact timezone and serialization convention should be standardized before implementation.

---

## 5. Core astronomical entities

### 5.1 Planet

**Purpose:** Identify an exoplanet independently of any one observation or research project.

**Required or proposed fields:**

| Field | Requirement | Meaning |
|---|---|---|
| `id` | Required | Stable ECAS identifier |
| `primary_name` | Required | Preferred display name |
| `external_identifiers` | Required concept | Catalog identifiers with provider/namespace |
| `aliases` | Required concept | Known alternative names, when available |
| `host_star` | Proposed | Linked host-star record or clearly scoped metadata |
| `catalog_metadata` | Proposed | Relevant source-attributed metadata |
| `created_at` | Proposed | ECAS record creation time |
| `updated_at` | Proposed | Last metadata update time |

The existence of a Planet record does not imply that a usable transmission spectrum exists.

**Identity rule:** Do not use a planet's display name as its sole identifier. Catalog aliases and naming conventions can vary.

**Unresolved:** Whether host stars need a dedicated `Star` entity in the initial release or can remain referenced metadata. A dedicated model should be introduced only if required by the initial workflow.

### 5.2 Project

**Purpose:** Organize research around one planet.

One project is associated with one target planet and may contain multiple observations, analyses, candidate selections, notes, and project-specific settings.

**Proposed fields:**

| Field | Requirement | Meaning |
|---|---|---|
| `id` | Required | Stable project identifier |
| `planet_id` | Required | Target planet |
| `name` | Required | User-visible project name |
| `description` | Optional | User-authored project description |
| `created_at` | Required concept | Creation timestamp |
| `updated_at` | Required concept | Last project update |
| `status` | Proposed | Active, archived, or another explicitly defined lifecycle state |
| `settings` | Proposed | Project-level settings, if needed |
| `notes` | Optional | User-authored research context or linked notes |

**Rules:**

- A project must have exactly one target planet.
- Multiple observations and analyses may be associated with the project.
- Shared molecular references should normally remain in the central library and be referenced by the project.
- Project records must preserve the exact input versions used by historical analyses.
- Renaming a project must not change its identity or invalidate associated records.

**Unresolved:** Whether notes and project settings should be stored directly on the Project record or in separate entities. Prefer separate records if independent history or querying becomes necessary.

---

## 6. Source and provenance models

### 6.1 SourceRecord

**Purpose:** Describe the origin of a dataset or scientific claim.

A source may be an online archive, molecular database, local file import, scientific publication, or another identifiable provider.

**Proposed fields:**

| Field | Requirement | Meaning |
|---|---|---|
| `id` | Required | Stable ECAS source identifier |
| `source_type` | Required | Archive, database, local import, publication, or other defined type |
| `provider_name` | Required when known | Institution, archive, author, or provider |
| `dataset_title` | Required when available | Source-provided title |
| `external_identifier` | Optional | Provider-specific identifier |
| `url` | Optional | Original URL or stable landing page |
| `doi` | Optional | DOI, where applicable |
| `authors` | Optional | Source or publication authors |
| `publication_reference` | Optional | Linked citation or bibliographic information |
| `license` | Optional | License or usage terms |
| `retrieved_at` | Conditional | Retrieval time for acquired material |
| `source_version` | Optional | Provider-declared version or release |
| `description` | Optional | Additional source context |

Unknown metadata must remain unknown rather than being inferred from filenames or unrelated records.

A single SourceRecord may be referenced by multiple dataset versions or artifacts.

### 6.2 DatasetVersion

**Purpose:** Identify a particular version or acquired representation of a logical dataset.

**Proposed fields:**

- `id`
- `dataset_identity`
- `source_record_id`
- `version_label`, if provided by the source
- `content_hash`, where applicable
- `retrieved_at` or `imported_at`
- `original_filename`, where applicable
- `original_artifact_id`, where retained
- `availability_status`
- `completeness_status`
- `metadata_snapshot`, where needed to preserve the information relevant to historical interpretation

The exact relationship between `DatasetVersion`, `Observation`, and `ReferenceDataset` requires a detailed schema decision. The design must not introduce duplicate or conflicting version authorities.

### 6.3 StoredArtifact

**Purpose:** Track a file stored outside SQLite.

Artifacts may include:

- Original downloaded observation files.
- User-imported source files.
- Original molecular reference files.
- Parsed or normalized datasets.
- Prepared spectra.
- Synthesized reference spectra.
- Diagnostic outputs.
- Plots and exported reports.

**Proposed fields:**

| Field | Requirement | Meaning |
|---|---|---|
| `id` | Required | Stable artifact identifier |
| `artifact_role` | Required | Original input, parsed data, prepared spectrum, synthesized data, plot, report, or other defined role |
| `storage_reference` | Required | Managed path or storage key |
| `format` | Required when known | File format |
| `content_hash` | Proposed | Integrity and duplicate checking |
| `size_bytes` | Proposed | File size |
| `created_at` | Required concept | Artifact creation or registration time |
| `availability_status` | Required concept | Available, missing, corrupt, or another defined state |
| `media_type` | Optional | MIME type or equivalent classification |

The storage reference should be managed by the storage layer. Domain records must not depend on hard-coded absolute paths that become invalid when the data directory moves.

A database record referencing an artifact must not be considered complete if the required artifact was never successfully stored.

### 6.4 Citation

**Purpose:** Preserve bibliographic attribution for datasets and published scientific claims.

**Proposed fields:**

- `id`
- `title`
- `authors`
- `publication`
- `year`
- `doi`
- `url`
- `citation_text`, where available
- `citation_type`, such as dataset, publication, or software

A citation may be associated with a source, benchmark case, observation, reference dataset, or report.

**Unresolved:** Whether Citation should be a fully normalized entity or a smaller reusable metadata record. A separate entity is preferable if citations are shared across many records and require consistent export.

---

## 7. Observational data models

### 7.1 Observation

**Purpose:** Represent one identifiable astronomical observation or published observational data product relevant to the initial transmission-spectrum workflow.

An Observation is distinct from its source file and from any processed representation derived from it.

**Proposed fields:**

| Field | Requirement | Meaning |
|---|---|---|
| `id` | Required | Stable ECAS observation identifier |
| `planet_id` | Required | Observed target |
| `source_record_id` | Required concept | Origin and attribution |
| `dataset_version_id` | Proposed | Exact source dataset version, where applicable |
| `observation_type` | Required | Transmission spectrum for the initial scope |
| `observation_date` | Optional | Date or interval of observation, when available |
| `publication_date` | Optional | Publication date, distinct from observing date |
| `instrument` | Optional | Instrument or instrument configuration |
| `telescope` | Optional | Telescope or observatory |
| `observing_mode` | Optional | Relevant observing mode |
| `data_product_type` | Required when known | Published spectrum, archive product, or another defined type |
| `spectral_data_id` | Required concept | Link to the structured spectral representation or stored artifact |
| `quality_status` | Required concept | Result of structural and quality checks |
| `metadata_completeness` | Required concept | Whether important metadata are present, missing, or unknown |
| `processing_status` | Required concept | Original, externally processed, or otherwise documented status |
| `created_at` | Required concept | ECAS record creation time |

Additional metadata should be retained when available, including wavelength coverage, spectral resolution, uncertainty representation, data-reduction pipeline, instrument configuration, and publication details.

These properties may be represented directly on Observation or through linked spectral metadata, depending on the final schema.

**Rules:**

- Different observations must remain individually identifiable.
- A planet can have no observations, one observation, or many observations.
- Observation metadata must not be fabricated to complete a record.
- Multiple files belonging to one observation must not automatically be interpreted as multiple independent observations.
- A downloaded observation and a user-imported observation must pass through the same validation and registration requirements.

**Unresolved:** The precise distinction between an observing event, a published spectrum, an archive data product, and a set of files associated with one observation. This should be settled when the first providers and supported formats are selected.

### 7.2 SpectrumData

**Purpose:** Represent the structured numerical spectral content used by scientific services.

A spectrum is not fully described by two numeric arrays alone. Its axes, signal meaning, units, uncertainties, quality flags, and relationship to its source must be explicit.

**Proposed conceptual fields:**

| Field | Requirement | Meaning |
|---|---|---|
| `id` | Required | Stable spectral-data identifier |
| `parent_record_id` | Required concept | Observation, reference, or derived record to which it belongs |
| `spectral_axis_type` | Required | Wavelength, wavenumber, or another explicitly supported coordinate |
| `spectral_axis_unit` | Required concept | Unit or explicitly unknown status |
| `signal_type` | Required | Meaning of the spectral signal |
| `signal_unit` | Required concept | Unit or explicitly unknown status |
| `values_artifact_id` | Proposed | Stored numerical data, when external to SQLite |
| `uncertainty_representation` | Proposed | Description of available uncertainty values |
| `quality_flags_artifact_id` | Optional | Stored quality flags, if present |
| `sample_count` | Required concept | Number of spectral samples |
| `coverage_summary` | Proposed | Descriptive coverage information |
| `resolution_metadata` | Optional | Available spectral resolution information |
| `data_status` | Required concept | Structural validity and completeness |

Possible signal types include transit depth, normalized transit spectrum, flux, absorption cross-section, absorbance, and other explicitly supported physical quantities.

The initial implementation should not assume all of these types are supported. The model must preserve distinctions even when only a subset is initially accepted for comparison.

#### Spectral values and uncertainties

**Required:**

- Spectral coordinates and signal values must have compatible lengths.
- Units and physical meaning must be explicit or marked unknown.
- Missing and invalid values must be represented or flagged deliberately.
- Available uncertainty information must not be discarded.
- Gaps must not be filled silently with invented measurements.
- Quality flags must remain associated with the relevant samples or source representation.

Uncertainty data may be symmetric errors, asymmetric bounds, covariance information, or another source-defined representation. The initial supported forms remain unresolved.

#### Storage decision

**Proposed:** Store large numerical arrays in files or an appropriate scientific data format, while SQLite stores metadata and artifact references.

This avoids bloating relational records with large arrays and supports reuse of stored scientific artifacts.

**Unresolved:**

- The numerical file format.
- Whether arrays should use separate files or a container format.
- How masks and quality flags should be represented.
- Whether some small arrays should ever be stored directly in SQLite.
- How large datasets should be loaded without excessive memory use.

These choices should follow the first real data formats and expected dataset sizes.

---

## 8. Molecular reference models

### 8.1 Molecule

**Purpose:** Identify a molecular species independently of its individual reference datasets.

**Proposed fields:**

- `id`
- `preferred_name`
- `chemical_formula`
- `external_identifiers`
- `isotopologue_identifier`, where relevant
- `notes`, where useful

The model should preserve source-specific molecular identifiers and distinguish isotopologues when the reference data identify them separately.

A Molecule may have multiple reference datasets from different providers, physical conditions, experiments, or theoretical calculations.

**Unresolved:** The initial canonical identity system for molecules and isotopologues. The implementation should not assume that display names or formulas alone uniquely identify every reference.

### 8.2 ReferenceDataset

**Purpose:** Describe a particular molecular reference dataset and the representation it provides.

**Required conceptual distinction:** ECAS must distinguish at least:

1. Measured or experimentally derived spectra.
2. Theoretical spectroscopic line lists.
3. Spectra synthesized from line lists or other model inputs.
4. Other derived products, if later supported.

These categories must not be treated as interchangeable.

**Proposed fields:**

| Field | Requirement | Meaning |
|---|---|---|
| `id` | Required | Stable reference identifier |
| `molecule_id` | Required concept | Associated molecule or molecules |
| `source_record_id` | Required concept | Origin and attribution |
| `dataset_version_id` | Proposed | Exact source version |
| `reference_type` | Required | Measured, experimentally derived, theoretical line list, synthesized, or other defined category |
| `representation_type` | Required | Continuous spectrum, transition line list, cross-section, or another supported representation |
| `spectral_axis_type` | Required when applicable | Wavelength, wavenumber, or defined alternative |
| `spectral_axis_unit` | Required concept | Unit or explicitly unknown status |
| `signal_type` | Required when applicable | Physical meaning of the values |
| `signal_unit` | Required concept | Unit or explicitly unknown status |
| `physical_conditions` | Conditional | Reported or assumed temperature, pressure, and other relevant conditions |
| `resolution_metadata` | Optional | Available resolution or broadening information |
| `uncertainty_metadata` | Optional | Available uncertainty information |
| `processing_status` | Required concept | Original, processed, synthesized, or another defined state |
| `limitations` | Required concept | Known limitations, or an explicit statement that they are not documented |
| `artifact_id` | Conditional | Stored source or data artifact |
| `availability_status` | Required concept | Local availability and integrity status |

A dataset may be scientifically valid as a reference while being unsuitable for a particular comparison.

#### Measured or experimentally derived references

Preserve, when available:

- Experimental conditions.
- Measurement method and instrument.
- Spectral axis and signal units.
- Resolution and calibration details.
- Uncertainty and quality information.
- Whether the data are raw, calibrated, normalized, or otherwise processed.
- Source attribution and limitations.

#### Theoretical line lists

A line list must not be represented as if it were already a continuous, experimentally measured spectrum.

Its metadata may need to include:

- Transition identifiers or quantum-state information.
- Transition positions.
- Transition strengths or intensities.
- Relevant molecular and isotopologue identity.
- Partition-function or other required source metadata, where applicable.
- Temperature validity or other source limitations.
- Data release and source version.

The exact required line-list fields depend on the first supported sources and the chosen synthesis/comparison method.

### 8.3 LineListData

**Purpose:** Describe transition-level data where a theoretical reference is represented as a line list rather than a continuous spectrum.

This may ultimately be implemented as a specialized form of ReferenceDataset or as a representation-specific data structure.

**Proposed conceptual content:**

- Transition positions and their units.
- Transition strengths or intensities and their units/definitions.
- Molecular and isotopologue identifiers where available.
- Source-specific transition metadata.
- Required supplementary data and assumptions.
- Source version and completeness information.

The initial implementation must not require all possible quantum-mechanical fields from every provider. It should support the selected source format while preserving additional source fields when practical.

**Unresolved:** Whether line-list support belongs in the first release or whether the initial workflow will initially compare continuous measured or derived references while retaining a model capable of representing line lists. The architecture requires the categories to remain distinct but does not yet require a complete line-list synthesis engine.

### 8.4 Synthesized reference spectra

A synthesized spectrum is a derived artifact created from a line list or another model input.

It must retain:

- Its source reference dataset and version.
- The synthesis method and version.
- Relevant physical assumptions and parameter values.
- Line-profile or broadening treatment, where used.
- Resolution and sampling settings.
- Subsequent transformations.
- Software version and execution status.
- Limitations and warnings.

A synthesized spectrum must never be labeled as a direct experimental measurement.

**Proposed representation:** Use the same general spectral-data concepts as SpectrumData, linked to a separate derivation record identifying how it was produced.

**Unresolved:** Whether synthesized spectra should use a dedicated `SynthesisRun` entity or be represented as a specialized processing/analysis run. Choose the simpler option that still preserves the distinction between synthesis and comparison.

---

## 9. Spectral preparation and comparability

### 9.1 PreparedSpectrum

**Purpose:** Represent a derived spectral dataset prepared for a specific analytical use.

A PreparedSpectrum is not an edited copy of the original source. It is a separately identifiable representation linked to the exact input data and transformations that produced it.

**Proposed fields:**

- `id`
- `source_record_id` or source dataset reference
- `source_version_id`
- `artifact_id`, if values are stored externally
- `spectral_axis_type`
- `spectral_axis_unit`
- `signal_type`
- `signal_unit`
- `preparation_status`
- `transformation_record_ids`
- `created_at`
- `software_version`
- `warnings` and `limitations`

It should be possible to trace a PreparedSpectrum to the original observation or reference dataset and recover the ordered processing history.

**Rules:**

- Preparation must not modify original input data.
- The model must identify which input version was used.
- Processing steps and parameters must be explicit.
- Missing uncertainty information must remain visible.
- The prepared representation must retain enough metadata to assess its suitability for the intended comparison.
- A derived dataset must not be misidentified as a direct measurement.

**Unresolved:** Whether every preparation step produces a separate stored artifact or whether intermediate steps can be represented as an ordered transformation pipeline with only selected outputs persisted. This decision should consider reproducibility, storage cost, and practical rerun performance.

### 9.2 TransformationRecord

**Purpose:** Describe one transformation applied to a spectral dataset.

Potential transformation types include:

- Axis-unit conversion.
- Signal-unit conversion.
- Sorting or coordinate validation.
- Masking or exclusion of invalid regions.
- Normalization.
- Resampling or interpolation.
- Resolution matching or convolution.
- Smoothing, if justified for a specific method.
- Line-list synthesis.
- Other explicitly documented processing operations.

**Proposed fields:**

| Field | Requirement | Meaning |
|---|---|---|
| `id` | Required | Stable transformation identifier |
| `transformation_type` | Required | Defined operation |
| `input_dataset_ids` | Required concept | Exact input identities |
| `output_dataset_id` | Required concept | Resulting representation, where materialized |
| `parameters` | Required concept | Settings needed to understand or repeat the operation |
| `software_name_version` | Required concept | Software identity and version |
| `executed_at` | Proposed | Execution time |
| `status` | Required concept | Completed, failed, or another defined state |
| `warnings` | Required concept | Relevant warnings or limitations |

A transformation record should distinguish between a documented operation and an operation that actually completed successfully.

The order of transformations must be recoverable where order affects results.

### 9.3 ComparabilityAssessment

**Purpose:** Record whether specific inputs can be compared for a particular method and configuration.

This is a relationship-specific assessment, not a permanent universal property of either dataset. The same observation/reference pair might be suitable for one method and unsuitable for another.

**Proposed fields:**

- `id`
- `observation_or_input_id`
- `reference_dataset_id`
- `method_id`, where method-specific assessment applies
- `method_version`, where applicable
- `status`
- `checks_performed`
- `warnings`
- `limitations`
- `reasoning_summary`
- `created_at`

**Proposed status values:**

- `compatible`
- `compatible_with_limitations`
- `conditional`
- `incompatible`
- `undetermined`

The final enumeration and the rules governing transitions remain unresolved.

The assessment should consider, where relevant:

- Spectral quantity and signal units.
- Coordinate type and units.
- Spectral coverage and overlap.
- Sampling and resolution.
- Measurement uncertainty.
- Normalization and processing state.
- Physical conditions associated with reference data.
- The method's explicit input requirements.

A structurally valid dataset can still be unsuitable for a particular comparison. Validation and comparability must remain separate concepts.

---

## 10. Analysis models

### 10.1 AnalysisRun

**Purpose:** Represent one execution of a spectral comparison workflow.

An AnalysisRun must preserve enough information to understand what was run, which inputs were used, which method was executed, what it returned, and whether the result can be reproduced.

**Proposed fields:**

| Field | Requirement | Meaning |
|---|---|---|
| `id` | Required | Stable analysis-run identifier |
| `project_id` | Required | Project containing the analysis |
| `status` | Required | Queued, running, completed, failed, or another defined state |
| `method_id` | Required concept | Identity of the comparison method |
| `method_version` | Required concept | Exact method version |
| `configuration` | Required concept | Method settings and parameters |
| `input_references` | Required concept | Exact observation, reference, and prepared-data versions |
| `preparation_history` | Required concept | Transformations used for this run |
| `comparability_assessments` | Proposed | Relevant input-suitability results |
| `software_version` | Required concept | ECAS version and relevant scientific dependency versions |
| `started_at` | Proposed | Start time |
| `completed_at` | Conditional | Completion time |
| `results` | Required concept | Structured outputs and artifact references |
| `warnings` | Required concept | Warnings and limitations |
| `error_summary` | Conditional | Failure explanation, when unsuccessful |

A configuration must be stored in a form that can be interpreted independently of the current UI state.

An AnalysisRun should distinguish the method's stable identity from a particular execution of that method.

**Rules:**

- A failed run must not be represented as a successful analysis.
- Partial outputs may be preserved if clearly marked incomplete.
- The exact input dataset versions must remain identifiable.
- A new analysis creates a new run record rather than silently rewriting a previous result.
- A rerun may produce a different result if software, inputs, or configuration differ; these differences must be traceable.
- Method-specific output fields must not be forced into a universal score interpretation.

**Unresolved:** Whether a run needs separate lifecycle states for cancelled, incomplete, or blocked by missing data. Final states should be determined by the execution workflow.

### 10.2 AnalysisInput

**Purpose:** Explicitly identify each input used by an AnalysisRun.

A separate input entity is proposed because a run may consume several observations, references, prepared datasets, or auxiliary artifacts.

**Proposed fields:**

- `id`
- `analysis_run_id`
- `input_role`
- `source_entity_type`
- `source_entity_id`
- `source_version_id`, where applicable
- `prepared_spectrum_id`, where applicable
- `content_hash`, where appropriate
- `input_order`, where relevant

The exact input roles depend on the comparison method. They may include target observation, candidate reference, prepared observation, synthesized reference, or another documented input type.

**Unresolved:** Whether AnalysisInput must be a physical table or can be represented by a structured relationship model. A separate entity is recommended if methods need multiple inputs or the system needs detailed input-level provenance.

### 10.3 Comparison method identity

**Purpose:** Give each pluggable comparison method a stable identity independent of its execution results.

**Proposed conceptual fields:**

- `method_id`
- `name`
- `version`
- `description`
- `input_requirements`
- `supported_reference_types`
- `output_definitions`
- `known_limitations`

A method identity may be represented in code metadata and persisted in analysis records rather than maintained as a separate database table.

The persisted record must nevertheless identify the method and version used by each run.

**Unresolved:** Whether method definitions require a persistent database registry. Do not build a general plugin registry unless it serves an identified workflow need.

### 10.4 CandidateResult

**Purpose:** Represent the output associated with a particular molecular candidate within an AnalysisRun.

**Proposed fields:**

| Field | Requirement | Meaning |
|---|---|---|
| `id` | Required | Stable candidate-result identifier |
| `analysis_run_id` | Required | Parent run |
| `molecule_id` | Required concept | Candidate molecular identity |
| `reference_dataset_id` | Required concept | Specific reference used, where applicable |
| `score_value` | Conditional | Numerical score if the method produces one |
| `score_definition` | Required when a score exists | Meaning, scale, and interpretation of the score |
| `method_output` | Required concept | Method-specific structured output |
| `diagnostics` | Proposed | Residuals, feature information, or other diagnostic artifacts |
| `uncertainty_information` | Conditional | Statistical uncertainty, if supported |
| `limitations` | Required concept | Relevant interpretive limitations |
| `warnings` | Required concept | Candidate-specific warnings |
| `candidate_assessment` | Proposed | Qualified result category supported by the method |

CandidateResult must not assume that every method produces one scalar score or a probability.

If a method produces several metrics, each metric must retain its own definition and interpretation.

**Scientific interpretation rules:**

- A spectral correspondence is not automatically a detection.
- A ranking is not a quantitative abundance estimate.
- A score is not a probability unless its meaning is justified and validated.
- Missing uncertainty must not be represented as zero uncertainty.
- Inconclusive outcomes are valid.
- The UI and exported reports must not imply a stronger conclusion than the method supports.

**Unresolved:** The first method's output structure, score semantics, candidate-result categories, and any statistical significance representation. These decisions depend on benchmark investigation and method selection.

### 10.5 PublishedResult

A published atmospheric interpretation may be relevant to a planet, observation, or benchmark case. It must be distinguished from a result produced by ECAS.

**Proposed approach:** Initially represent published findings through source-attributed citations and benchmark metadata where that is sufficient.

A dedicated PublishedResult entity should be introduced only if ECAS needs to query, compare, or preserve published interpretations independently of benchmark cases.

**Unresolved:** Whether a dedicated entity is required for the first release.

---

## 11. Validation models

### 11.1 BenchmarkCase

**Purpose:** Represent a documented scientific case used to evaluate a comparison method.

A BenchmarkCase must preserve the basis for its inclusion and the limitations of its interpretation.

**Proposed fields:**

- `id`
- `name`
- `target_planet_id`, where applicable
- `case_type`
- `citation_ids`
- `observation_version_ids`
- `reference_ids`, where relevant
- `published_conclusion`
- `evidence_summary`
- `inclusion_rationale`
- `known_limitations`
- `data_availability_status`
- `case_version`

Potential case types include a published detection, suitable non-detection, or control case. The actual benchmark set remains undecided.

A published detection should not be treated as guaranteed ground truth without considering the publication's evidence and limitations. Non-detections and controls must also be interpreted within their observational scope and sensitivity.

**Unresolved:**

- Initial benchmark targets and publications.
- The representation of ambiguous or disputed published conclusions.
- Whether a benchmark case should be linked to one observation or a group of related observations.
- How benchmark revisions should be versioned.

### 11.2 ValidationRun

**Purpose:** Record an evaluation of a particular method and configuration against a defined benchmark set.

**Proposed fields:**

- `id`
- `method_id`
- `method_version`
- `configuration`
- `benchmark_case_versions`
- `evaluation_protocol`
- `metric_results`
- `started_at`
- `completed_at`
- `status`
- `software_version`
- `warnings`
- `limitations`

A ValidationRun must preserve which benchmark cases were actually evaluated, rather than referencing only a benchmark collection that might later change.

### 11.3 ValidationMetricResult

**Purpose:** Record one evaluation metric and its result.

**Proposed fields:**

- `id`
- `validation_run_id`
- `metric_name`
- `metric_definition`
- `value`
- `uncertainty`, if supported
- `applicable_case_count`
- `excluded_case_count`
- `limitations`

Metrics and thresholds must not be selected arbitrarily. Their selection belongs to the validation strategy and should follow the method's intended use, benchmark evidence, and uncertainty.

**Unresolved:** The first metric set, threshold policy, and separation of tuning cases from evaluation cases. These are defined in `VALIDATION_STRATEGY.md`, not in this document.

---

## 12. Quality and validation records

### 12.1 Structural validation versus scientific suitability

ECAS should distinguish at least three questions:

1. **Was the input parsed successfully?**
2. **Does it meet structural and metadata requirements?**
3. **Is it suitable for the intended comparison?**

These questions must not be collapsed into a single Boolean `valid` field.

A dataset may be successfully parsed but have missing uncertainties, unknown units, incomplete metadata, or insufficient wavelength coverage. Those limitations should be recorded and communicated explicitly.

### 12.2 QualityIssue

**Purpose:** Represent a detected problem, warning, or limitation associated with an imported dataset, prepared spectrum, analysis, or artifact.

**Proposed fields:**

- `id`
- `severity`
- `category`
- `message`
- `affected_entity_type`
- `affected_entity_id`
- `related_field_or_region`, where applicable
- `detected_at`
- `resolution_status`, if the issue can be resolved
- `resolution_note`, where appropriate

Potential severities include informational notice, warning, and blocking error.

The final categories and severity scheme are unresolved. Avoid creating an elaborate issue taxonomy before real ingestion and comparison workflows demonstrate the need.

### 12.3 Missing and unknown information

Missing values should distinguish between materially different conditions when practical:

- Not provided by the source.
- Not applicable.
- Not yet retrieved.
- Unknown because parsing or interpretation failed.
- Intentionally omitted.
- Lost or unavailable after a storage failure.

Do not encode these states as invented numeric values or ambiguous empty strings.

The precise representation may differ by field. For example, a missing uncertainty array is not equivalent to a zero-valued uncertainty array.

---

## 13. User annotations and research notes

### 13.1 ResearchNote

**Purpose:** Preserve user-authored context associated with a project or a specific scientific entity.

**Proposed fields:**

- `id`
- `project_id`
- `related_entity_type`, if linked to an entity
- `related_entity_id`, if applicable
- `title`, if useful
- `body`
- `created_at`
- `updated_at`

Notes must remain distinguishable from sourced scientific facts and automatically generated analysis results.

**Unresolved:** Whether annotations on plots and individual wavelength regions require dedicated models in the initial release. Defer region-level annotations until the visualization workflow establishes what information must be preserved.

---

## 14. Persistence and storage boundaries

### 14.1 SQLite responsibilities

SQLite is the intended store for structured records and relationships, including:

- Planet and project metadata.
- Observation and reference metadata.
- Source and citation records.
- Dataset versions and artifact references.
- Analysis configurations and execution status.
- Candidate results and diagnostic metadata.
- Benchmark and validation records.
- Processing history and relevant warnings.

This is a logical list, not a final table schema. Some records may be represented by linked structures or compact serialized metadata where appropriate.

### 14.2 File storage responsibilities

Files should hold larger or independently reusable artifacts, including:

- Original source files where retention is permitted.
- Parsed or normalized spectral data.
- Prepared spectra.
- Synthesized reference products.
- Diagnostic arrays and plots.
- Exported reports and other analysis artifacts.

Each stored artifact must have a structured record describing its role, identity, integrity, and relationships.

### 14.3 Storage integrity

The persistence layer should avoid creating records that point to artifacts that were never successfully written.

Where a workflow writes both files and database records, it should use an explicit recovery strategy. A failed operation must not leave the application reporting a complete analysis when its required result files are missing.

### 14.4 Deletion and retention

**Required principle:** Removing a dataset from a visible project or library must not silently destroy the evidence needed to interpret a saved analysis.

**Unresolved:**

- Whether user-facing deletion initially means unlinking, archiving, or permanent deletion.
- Retention policies for cached source files.
- Handling of orphaned artifacts.
- Whether source files may be removed when licensing or storage constraints apply.
- Backup and recovery procedures.

These policies must be settled before implementing destructive operations.

### 14.5 Schema migrations

The exact database schema and migration framework are deferred until the first workflow and supported data representations are sufficiently defined.

Before implementation, establish:

- How the database schema version is recorded.
- How schema upgrades are applied.
- How failed migrations are recovered.
- How old projects remain interpretable.
- How migration tests protect existing scientific records.

A schema migration must not silently discard provenance, historical input identities, uncertainties, or analysis results.

---

## 15. Offline and reproducibility requirements

A saved project should remain interpretable when the application has no internet connection, provided the required local records and artifacts remain available.

At minimum, ECAS should be able to preserve and reopen:

- Planet and project identity.
- Observation metadata and source attribution.
- Reference dataset identity and version.
- Analysis method and version.
- Analysis configuration.
- The exact input identities used.
- Preparation and transformation history.
- Candidate results and their score definitions.
- Warnings, uncertainty information, and limitations.
- References and citations.
- Links to locally available artifacts.

Rerunning an analysis may require specific scientific libraries, method implementations, or reference artifacts. If a dependency is unavailable, ECAS should report what is missing instead of silently substituting another method or dataset.

**Proposed reproducibility rule:** Preserve the software and dependency version information needed to interpret an analysis. Exact environment-locking and binary reproducibility requirements remain unresolved.

A previous result must remain inspectable even when its original method version is no longer executable.

---

## 16. Proposed Python representation

The following is an illustrative design for discussing model boundaries. It is **not implementation code**, a final schema, or authorization to create Python files.

Prefer typed domain objects for scientific meaning and explicit artifact references for large data.

```python
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class EntityReference:
    entity_type: str
    entity_id: str


@dataclass(frozen=True)
class UnitDescriptor:
    symbol: str | None
    known: bool
    description: str | None = None


@dataclass(frozen=True)
class ArtifactReference:
    artifact_id: str
    content_hash: str | None
    format: str | None


@dataclass(frozen=True)
class SpectralDataDescriptor:
    spectral_axis_type: str
    spectral_axis_unit: UnitDescriptor
    signal_type: str
    signal_unit: UnitDescriptor
    sample_count: int
    values_artifact: ArtifactReference | None


@dataclass(frozen=True)
class AnalysisInputReference:
    role: str
    entity: EntityReference
    version_id: str | None
    content_hash: str | None


@dataclass(frozen=True)
class MethodReference:
    method_id: str
    version: str


@dataclass(frozen=True)
class AnalysisRunDescriptor:
    analysis_id: str
    project_id: str
    method: MethodReference
    status: str
    inputs: tuple[AnalysisInputReference, ...]
    configuration: dict[str, object]
    software_version: str
```

This sketch intentionally avoids defining the complete classes or numerical array types. Several details need to be settled first:

- The actual type system for units and physical quantities.
- Whether missing units should use a dedicated state type rather than a descriptor flag.
- The representation of spectral arrays, masks, and uncertainties.
- Whether frozen dataclasses are appropriate for all domain records.
- How configuration values are validated and serialized.
- Whether typed enums or dedicated value objects should replace string categories.
- Which fields must be normalized into separate database records.

The final design should favor strong typing and explicit semantics where they prevent scientific ambiguity, without creating unnecessary abstraction.

---

## 17. Unresolved decisions register

The following decisions remain open. They must not be treated as approved simply because this document proposes a possible representation.

| ID | Decision | Why it remains open | Recommended timing |
|---|---|---|---|
| DM-01 | Exact database schema and table boundaries | Depends on final relationships and querying needs | Before implementation |
| DM-02 | Spectral array file format | Depends on initial source formats, array size, and processing needs | After initial provider/format selection |
| DM-03 | Supported uncertainty representations | Depends on benchmark observations and selected method | During method planning |
| DM-04 | Canonical molecule and isotopologue identifiers | Must accommodate selected reference sources accurately | Before reference-library implementation |
| DM-05 | Observation identity and grouping rules | Provider products may represent observations differently | During provider selection |
| DM-06 | Line-list support in the first workflow | Requires method and synthesis requirements to be established | After benchmark investigation |
| DM-07 | Prepared-spectrum persistence strategy | Balances reproducibility, storage, and computation | Before processing implementation |
| DM-08 | Comparison-method output schema | Must preserve method-specific metrics and meanings | After initial method selection |
| DM-09 | Candidate-result interpretation categories | Must not overstate scientific evidence | After method and validation planning |
| DM-10 | Benchmark record structure and versioning | Depends on actual benchmark cases and published evidence | During validation planning |
| DM-11 | PublishedResult as a dedicated entity | Initial needs may be satisfied by citations and benchmark metadata | Defer unless needed |
| DM-12 | Dedicated host-star entity | Depends on the initial workflow's use of stellar context | Defer unless needed |
| DM-13 | Citation normalization | Depends on reuse and export requirements | Before reporting implementation |
| DM-14 | Deletion and artifact-retention policy | Must preserve historical analysis integrity | Before destructive operations |
| DM-15 | Database migration tooling | Depends on chosen persistence implementation | Before schema implementation |
| DM-16 | Dependency/environment reproducibility | Required depth depends on initial execution and deployment workflow | Before reproducibility claims |
| DM-17 | Final enums and lifecycle states | Should follow actual ingestion and execution behavior | During interface finalization |
| DM-18 | Exact identifier format | A technical choice that should be consistent across the project | Before implementation |

### 17.1 Decisions that must not be deferred past implementation of the relevant feature

Even though the full schema is deferred, each feature needs its essential model decisions before implementation:

- **Observation ingestion:** observation identity, source provenance, spectral quantity, units, and structural validation outcomes.
- **Reference ingestion:** molecule identity, reference category, representation type, and source version.
- **Spectral preparation:** exact input identity, transformation history, and derived-output identity.
- **Comparison:** method identity/version, input references, configuration, score definitions, and failure state.
- **Persistence:** stable IDs, artifact references, integrity checks, and transaction/recovery behavior.
- **Validation:** benchmark-case identity, source evidence, evaluation configuration, and metric definitions.

---

## 18. Data-model acceptance criteria

The data-model design is ready for implementation planning when:

1. Every core entity has a defined purpose and stable identity rule.
2. Project-to-planet and project-to-analysis relationships are unambiguous.
3. Observations remain distinct from planet metadata and original source files.
4. Source records and dataset versions preserve provenance.
5. Measured/experimentally derived references remain distinguishable from theoretical line lists and synthesized spectra.
6. Spectral data explicitly identify coordinate type, coordinate units, signal meaning, and signal units or their unknown status.
7. Available uncertainties and quality flags can be preserved without inventing missing values.
8. Prepared spectra can be traced to exact inputs and transformations.
9. Analysis runs identify their method, version, configuration, inputs, status, outputs, and limitations.
10. Candidate scores retain their definitions and cannot automatically be interpreted as detection probabilities.
11. Benchmark cases and validation runs preserve their evidence and evaluation configuration.
12. Large artifacts can be stored outside SQLite and reliably referenced.
13. Updating or refreshing data cannot silently change historical analysis inputs.
14. Saved projects remain interpretable offline when the required records and artifacts are available.
15. Open design decisions are documented and assigned to an appropriate planning stage.

---

## 19. Relationship to other architecture documents

- `docs/ECAS.md` governs the project's scientific purpose and principles.
- `docs/architecture/ARCHITECTURE.md` defines architectural layers, responsibilities, and dependency constraints.
- `docs/architecture/DATA_FLOW.md` describes how inputs move through retrieval/import, validation, preparation, analysis, and persistence.
- `docs/architecture/MODULE_RESPONSIBILITIES.md` defines module ownership and service boundaries.
- `docs/architecture/DATA_MODELS.md` defines the conceptual entities and relationships described here.
- `docs/architecture/VALIDATION_STRATEGY.md` will define benchmark selection, evaluation methodology, and interpretation limits.
- `docs/brains/DECISIONS.md` records decisions after they are explicitly approved.
- `docs/brains/PROJECT_STATE.md` records verified project state, not proposed future structure.

If a conflict arises between these documents, it must be surfaced and resolved rather than silently reconciled.

---

## 20. Implementation boundary

This document is a planning draft. It does not authorize:

- Creating or modifying files in the ECAS workspace.
- Implementing Python classes or database tables.
- Selecting or installing dependencies.
- Committing to a specific spectral array format.
- Selecting the initial comparison algorithm.
- Selecting benchmark cases or numerical thresholds.
- Implementing a line-list synthesis engine.
- Implementing atmospheric retrieval or quantitative abundance estimation.

Those steps require review and explicit authorization.

The governing principle is to establish enough structure to preserve scientific identity, meaning, provenance, and reproducibility while postponing choices that depend on actual benchmark data and the initial analytical method.
