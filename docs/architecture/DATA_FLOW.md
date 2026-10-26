# ECAS Data Flow

**Project:** ECAS — Exoplanetary Characterization & Astrochemistry Suite  
**Document status:** Architecture specification for review  
**Implementation status:** Describes existing behavior and intended future behavior. Proposed workflows do not authorize implementation.  
**Related documents:** `ECAS.md`, `ARCHITECTURE.md`, `DATA_MODELS.md`, `MODULE_RESPONSIBILITIES.md`, `VALIDATION_STRATEGY.md`, `DECISIONS.md`, `PROJECT_STATE.md`, `ECAS_development_plan.md`

---

## 1. Purpose

This document defines how scientific data should move through ECAS, from acquisition or local import through validation, registration, preparation, comparison, persistence, and presentation.

It establishes the intended sequence of operations, the responsibilities of each stage, the information that must be preserved, and the behavior expected when an operation cannot proceed.

The initial application supports local CSV import, structured spectrum data, SQLite persistence, and spectral visualization. Online archive integration and molecular-reference acquisition are part of the broader development plan and must be treated according to their verified implementation status.

The long-term workflow focuses on exoplanet transmission spectra and molecular reference data. Astronomical observations and molecular references originate from different sources and represent different physical quantities. They must remain scientifically distinguishable throughout the workflow.

This document defines intended behavior rather than finalized implementation details, database schemas, or provider-specific APIs.

### 1.1 Governing principles

All data flows must follow these principles:

1. Preserve original source data whenever permitted and practical.
2. Record provenance and distinguish original data from derived products.
3. Validate data before using them in scientific analysis.
4. Distinguish structural validity from scientific comparability.
5. Record transformations rather than silently altering inputs.
6. Preserve uncertainty, units, metadata, and limitations where available.
7. Make analyses reproducible from their recorded inputs and settings.
8. Support offline workflows when required data and software are available locally.
9. Report failures explicitly rather than silently substituting data or producing misleading results.
10. Never interpret spectral similarity alone as proof of molecular detection.
11. Distinguish implemented behavior, approved decisions, proposals, and unresolved questions.
12. Avoid introducing abstractions or infrastructure that are not justified by the initial supported workflow.

---

## 2. Data Categories

ECAS must distinguish the scientific meaning and provenance of the data it manages.

### 2.1 Astronomical observations

Astronomical observations are measurements or processed data products derived from observations of an exoplanet or its host system.

The initial scientific focus is exoplanet transmission spectroscopy. However, a catalog entry, publication record, time-series observation, or raw instrument product is not automatically a usable transmission spectrum.

Each astronomical dataset must retain its actual product type and processing status. Data requiring additional calibration, extraction, reduction, or interpretation must not be presented as a ready-to-use transmission spectrum.

### 2.2 Experimentally measured molecular spectra

These datasets originate from laboratory measurements or experimentally derived spectral products.

Where available, ECAS should preserve:

- Molecular identity and relevant identifiers.
- Source and citation.
- Spectral coordinate and units.
- Measured signal and its physical meaning and units.
- Experimental conditions.
- Instrumental resolution and other relevant measurement conditions.
- Uncertainty information and quality indicators.
- Processing status and known limitations.

Experimental molecular spectra must not be assumed to be directly comparable with astronomical observations merely because both contain spectral coordinates and numerical values.

### 2.3 Theoretical line lists

A theoretical line list describes discrete spectroscopic transitions and associated molecular parameters. It is not equivalent to a continuous measured spectrum.

A line list may require synthesis before it can be used by a comparison method that expects a continuous spectral representation.

The original line list, its source, its molecular identifiers, and its transition parameters must remain distinguishable from any spectrum generated from it.

### 2.4 Calculated or synthesized spectra

A calculated spectrum is a derived product generated from theoretical data, measured inputs, or another documented model.

Its provenance should identify the underlying inputs, calculation method, software version, physical assumptions, and material parameters.

A calculated spectrum must not be labeled as a direct experimental measurement.

### 2.5 Local imported spectra

Local files may contain astronomical measurements, laboratory spectra, or other spectral data.

Importing a file establishes only that ECAS has read and interpreted the file according to its supported import rules. It does not independently establish the scientific identity or suitability of the data.

The application must not infer a spectral quantity, instrument, wavelength unit, signal unit, or measurement condition without supporting evidence.

---

## 3. End-to-End Workflow

The intended long-term workflow consists of the following stages:

1. Identify an exoplanet and open or create its project.
2. Acquire an astronomical data product through a supported archive or local-file import.
3. Preserve or reference the source artifact and record its provenance.
4. Parse the source into an appropriate internal representation.
5. Perform structural and metadata validation.
6. Register the validated dataset with the appropriate project.
7. Discover or acquire a molecular reference dataset.
8. Parse, validate, and register the reference dataset in the appropriate library.
9. Assess whether the selected observation and reference are suitable for the intended comparison method.
10. Prepare comparison inputs through documented transformations, where necessary.
11. Execute a selected comparison method.
12. generate candidate results, diagnostics, warnings, and supporting metadata.
13. Persist the analysis and its outputs.
14. Present results and their limitations for inspection.

Not every workflow must execute every stage. An existing observation can be reused without downloading it again, a cached reference can be loaded without network access, and a completed analysis can be inspected without being rerun.

A workflow must not proceed past a required stage when its prerequisites have not been satisfied.

The sequence above describes intended system behavior. It does not assert that every stage is currently implemented.

### 3.1 High-level data flow

```text
                        USER / DESKTOP UI
                               |
                               v
                    Select planet or project
                               |
                               v
                    Acquire astronomical data
                         /             \
                        v               v
                 Online archive      Local file
                        \               /
                         v             v
                       Preserve source
                              |
                              v
                        Parse data product
                              |
                              v
                    Structural validation
                              |
                       +------+------+
                       |             |
                    Invalid         Valid
                       |             |
                       v             v
                 Report failure   Register observation
                                      |
                                      v
                            Select molecular reference
                                      |
                                      v
                              Acquire or load reference
                                      |
                                      v
                              Parse and validate reference
                                      |
                                      v
                              Register reference
                                      |
                                      v
                              Assess comparability
                                      |
                             +--------+--------+
                             |                 |
                        Not suitable        Suitable
                             |                 |
                             v                 v
                       Explain issue     Prepare inputs
                                               |
                                               v
                                       Run comparison
                                               |
                                               v
                                      Generate results
                                               |
                                               v
                                      Persist analysis
                                               |
                                               v
                                      Present results
```

This diagram represents the intended successful path and its principal decision points. Individual operations may have additional failure, retry, and recovery paths.

---

## 4. Data Acquisition

ECAS must support local-file import and, as archive integration is implemented, retrieval from supported online scientific sources.

These routes should converge on appropriate parsing and validation workflows without erasing the differences between their source formats or scientific meanings.

### 4.1 Local-file import

The intended sequence is:

1. The user selects a local file.
2. ECAS determines whether the file matches a supported format.
3. The importer parses the file and identifies its available columns and metadata.
4. ECAS checks the structure and identifies missing, ambiguous, malformed, or unsupported values.
5. The original file is preserved or referenced according to the storage policy.
6. The parsed data are represented using the appropriate internal model.
7. The data are validated for the intended use.
8. If the required checks pass, the data can be registered and made available to the project.

Importing a file must not bypass validation merely because the file exists locally.

Missing scientific metadata must not be silently invented. If a required field is absent or ambiguous, ECAS must report the problem and either request clarification or reject the input for the intended operation.

The existing CSV importer and `SpectrumData` model establish the initial import workflow. Their actual supported behavior must be verified in code and tests; this document does not imply that they already implement all the validation and registration stages described above.

The initial supported file formats and column conventions remain subject to documented decisions.

### 4.2 Online archive retrieval

The intended sequence is:

1. The user searches for a planet or selects a known target.
2. ECAS queries a supported scientific archive.
3. Search results identify available data products and provide sufficient metadata to distinguish them.
4. The user selects a specific data product.
5. ECAS retrieves the product and available associated metadata.
6. The application records the source identity, product identifier, retrieval information, and available version information.
7. The downloaded artifact is preserved or cached where permitted.
8. The response is parsed using the relevant provider-specific parser.
9. The resulting data are submitted to the appropriate validation workflow.
10. Valid data are registered with the relevant project.

Archive search results must not automatically be treated as usable observations. The existence of a catalog entry or downloadable file does not establish that its contents are supported or suitable for the intended analysis.

Where multiple products exist for the same planet, each product must retain its own identity, source metadata, and processing status.

### 4.3 Provider responsibilities

Provider-specific code should handle:

- Constructing requests to the source.
- Identifying supported data products.
- Downloading source data.
- Interpreting provider-specific response formats.
- Extracting available source identifiers and metadata.
- Reporting source-specific failures.

Provider code must not silently redefine scientific quantities or bypass common validation rules.

Astronomical providers and molecular-reference providers should retain distinct scientific responsibilities. They may share limited technical infrastructure, such as HTTP request handling or cache utilities, where this reduces duplication without obscuring the differences between the data types.

### 4.4 Molecular reference acquisition

Molecular reference acquisition follows a workflow similar to astronomical acquisition but has different data requirements.

The intended sequence is:

1. The user selects a molecule or searches the reference library.
2. ECAS identifies available reference datasets for that molecule.
3. Reference records expose their source, representation type, units, conditions, and limitations where available.
4. The user selects a reference dataset.
5. ECAS retrieves it from a supported source or loads an existing cached copy.
6. The dataset is parsed according to its actual representation.
7. ECAS validates its structure and available metadata.
8. The reference is registered in the shared reference library or linked to an existing registered version.

A molecule's presence in a catalog does not guarantee that an appropriate reference dataset is available.

Multiple datasets for the same molecule must remain distinguishable. Experimental spectra, theoretical line lists, and synthesized spectra must not be silently treated as interchangeable.

### 4.5 Acquisition failures

Acquisition may fail because of network unavailability, archive errors, missing records, unsupported formats, incomplete downloads, access restrictions, authentication failures, or rate limits.

On failure, ECAS must:

- Report which operation failed.
- Preserve useful diagnostic information.
- Avoid registering an incomplete dataset as a successfully acquired product.
- Retain partial data only when safe and clearly marked as incomplete.
- Allow retry or selection of another source when appropriate.
- Preserve previously valid cached data if a refresh fails.
- Avoid representing an unsuccessful retrieval as a successful registration.

A failed online retrieval must not prevent the user from importing an available local file.

---

## 5. Parsing, Validation, and Registration

Parsing, structural validation, scientific suitability assessment, and registration are separate operations.

A file can be parsed successfully but contain invalid values. A dataset can be structurally valid but unsuitable for a particular scientific comparison.

### 5.1 Parsing

Parsing converts a supported source representation into an internal data representation while preserving its scientific meaning.

The parser should identify the available:

- Spectral coordinates and their units.
- Signal values and their physical meaning and units.
- Uncertainties and quality indicators.
- Dataset and source identifiers.
- Relevant target or molecular identifiers.
- Available observational, experimental, or calculation metadata.
- Original processing status.
- Provenance and version information.

Provider-specific and file-format-specific parsing must remain isolated from scientific comparison methods.

If a parser encounters unsupported structures, ambiguous columns, or unknown scientific quantities, it must report the ambiguity instead of silently assigning meaning.

### 5.2 Structural validation

Structural validation checks whether a parsed dataset satisfies the minimum requirements for its declared representation and intended role.

Checks should include, as applicable:

- Required coordinates and signal values are present.
- Coordinate and signal arrays have compatible dimensions.
- Units are identified or explicitly marked unknown.
- Numeric values are finite where required.
- Missing values and invalid entries are identified.
- Duplicate or non-monotonic coordinates are detected and handled explicitly.
- Uncertainties and quality flags are preserved where supplied.
- Metadata are sufficiently consistent to identify the dataset.
- Provenance information is available.
- The dataset has not been mistaken for a different spectral quantity.
- Required identifiers and representation-specific fields are present.

Validation should distinguish errors that prevent use from warnings that allow limited use.

For example, missing uncertainty information may not prevent a dataset from being displayed, but it may restrict which comparison methods can use it and what conclusions can be supported.

Validation requirements must be appropriate to the dataset type. A molecular line list does not have the same required fields as a continuous measured spectrum, and an astronomical data product may require metadata not applicable to a laboratory measurement.

### 5.3 Scientific suitability

Scientific suitability is assessed separately from structural validity.

This stage considers whether a dataset can serve its intended role. It may depend on the physical meaning of the signal, coordinate units, data coverage, measurement conditions, processing status, and the requirements of a particular method.

A dataset can be structurally valid while unsuitable for a proposed comparison.

Suitability checks must not be treated as proof that the underlying measurements are scientifically correct or that a comparison will produce a valid detection.

### 5.4 Validation outcomes

Validation operations should produce explicit outcomes.

| Outcome | Meaning |
|---|---|
| Valid | The dataset satisfies the requirements checked for its declared role. |
| Valid with warnings | The dataset can be used for the intended limited purpose, but known limitations must remain visible. |
| Invalid | One or more required conditions are not satisfied. |
| Incomplete | The available data are insufficient to finish validation. |

These are conceptual outcomes. Exact status representations and error categories remain implementation decisions.

Scientific suitability and comparability may use a separate result model rather than being collapsed into the structural validation status.

### 5.5 Registration

After successful validation, ECAS registers the dataset in the appropriate project or shared library.

Registration must preserve the relationship between the dataset and its original source.

For observations, registration associates the observation with the relevant planet project. For shared molecular references, registration associates the reference with the central reference library and makes it available to eligible projects.

Registration must not overwrite a previously registered observation or reference merely because a new file has the same name.

Where duplicate or updated content is detected, ECAS should identify the relationship and preserve distinct versions when necessary.

Registration must also preserve the distinction between the original source artifact and the normalized internal representation.

---

## 6. Molecular Reference Representations

Molecular references require representation-specific handling.

### 6.1 Experimental spectra

Where available, ECAS should preserve reported experimental conditions, spectral quantity, units, resolution, uncertainty information, source, and processing status.

The applicability of an experimental spectrum to an exoplanet atmosphere must be assessed separately from the validity of the measurement itself.

Laboratory conditions may differ substantially from the conditions represented by an astronomical observation. ECAS must not imply direct equivalence when relevant differences remain unresolved.

### 6.2 Theoretical line lists

Line lists describe discrete transitions rather than necessarily providing a directly comparable continuous spectrum.

A line list may require synthesis before it can be used by a method expecting a continuous spectral representation.

That operation must record its inputs, method, settings, assumptions, and relevant physical conditions.

ECAS must not silently treat line positions or transition strengths as though they were measured continuous-spectrum values.

### 6.3 Synthesized references

A synthesized spectrum must retain its relationship to the underlying theoretical or measured inputs.

Its provenance should include the synthesis method, software version, applicable physical assumptions, line-profile treatment, spectral resolution, and other settings that materially affect the output.

A synthesized reference must remain identifiable as a derived product rather than a direct experimental measurement.

### 6.4 Shared reference storage

Reference datasets should normally be stored in the shared reference library and reused across planet projects.

Projects should record which reference version or content identity was used for an analysis.

Updating a shared reference must not silently change the historical inputs of an existing analysis.

The initial reference providers and supported representations must be selected through the documented Chunk 4 investigation rather than assumed in advance.

---

## 7. Comparability Assessment and Spectral Preparation

Before a comparison method executes, ECAS must determine whether the selected observation and reference are sufficiently compatible for that method.

This stage is essential because structurally valid spectra may represent different physical quantities or have incompatible units, coverage, resolution, or processing.

### 7.1 Comparability assessment

The assessment should consider the requirements of the selected method, including:

- Spectral quantity and physical meaning.
- Coordinate axis and units.
- Signal units and representation.
- Wavelength or frequency coverage.
- Spectral resolution and sampling.
- Normalization and processing state.
- Available uncertainty information.
- Data-quality limitations.
- Experimental conditions or theoretical assumptions relevant to the reference.
- Additional method-specific requirements.

Not every method will require the same inputs. Comparability must therefore be assessed against a declared method contract rather than a single universal rule.

### 7.2 Comparability outcomes

The assessment should distinguish:

- **Compatible:** the data satisfy the method's required compatibility conditions.
- **Compatible with limitations:** the method can run, but documented limitations affect interpretation.
- **Conditionally compatible:** a specified transformation or additional user decision is required before proceeding.
- **Incompatible:** the data cannot be used meaningfully by the selected method under the current conditions.
- **Undetermined:** insufficient metadata or scientific information prevents a reliable assessment.

The application must explain the reason for a negative or conditional outcome whenever practical.

A method must not be executed merely because two datasets can be represented as numeric arrays.

### 7.3 Spectral preparation

If preparation is required, ECAS creates derived inputs from the registered source datasets.

Potential operations include:

- Unit conversion.
- Selection or masking of spectral regions.
- Resampling onto a compatible coordinate grid.
- Resolution matching.
- Normalization.
- Application of explicitly documented quality filters.
- Synthesis of a continuous spectrum from a theoretical line list.
- Other transformations required by a selected comparison method.

These are possible operations, not a commitment to implement every operation in the initial release.

The first comparison method and benchmark investigation will determine which transformations are scientifically justified and necessary.

Each transformation must record, as applicable:

- Source dataset identity and version.
- Transformation name and version.
- Input and output units.
- Parameters and settings.
- Assumptions and approximations.
- Effects on uncertainty information.
- Warnings or limitations.

Preparation must not modify the original source dataset.

If a transformation changes the data in a way that affects scientific interpretation, that change must remain visible in the analysis record.

### 7.4 Prepared-input identity

Prepared inputs must be identifiable as derived data, not independent observations or original reference measurements.

Where practical, ECAS should reuse an existing prepared dataset when its source identities, transformation sequence, parameters, and relevant software versions match.

Reuse must not occur when the application cannot establish that the prepared data are equivalent for the intended operation.

---

## 8. Comparison and Candidate Scoring

The comparison stage consumes validated, prepared inputs and returns method-defined results.

It must not retrieve external data, parse provider-specific files, access desktop UI state, or independently manage project persistence.

### 8.1 Comparison execution

The intended sequence is:

1. Confirm that the selected observation and reference are available.
2. Confirm that validation and comparability requirements have been satisfied.
3. Resolve or generate the required prepared inputs.
4. Confirm that the selected method and its dependencies are available.
5. Record the method identity, version, settings, and input identities.
6. Execute the comparison.
7. Collect the method output and diagnostic information.
8. Interpret the output only within the method's documented meaning.
9. Persist the resulting analysis and candidate records.

The first production comparison method remains subject to the benchmark investigation and method-selection process.

The architecture should permit additional methods to be introduced through a common integration contract without requiring changes to the entire acquisition, project, or UI architecture.

### 8.2 Method outputs

A comparison method may produce scores, residuals, correlations, feature-level diagnostics, uncertainty estimates, or other method-specific outputs.

ECAS must retain the definition and meaning of each output.

A score from one method must not automatically be treated as numerically equivalent to a score from another method.

Where supported, results should include:

- Candidate molecule.
- Input observation and reference identities.
- Comparison method and version.
- Method configuration.
- Score values and their definitions.
- Relevant diagnostic outputs.
- Uncertainty or significance information justified by the method.
- Warnings and known limitations.
- Execution status.
- References and provenance required to interpret the result.

The exact output structure will be finalized after the first method is selected.

### 8.3 Candidate scoring and interpretation

Candidate scoring must not imply a stronger scientific conclusion than the underlying method supports.

ECAS must distinguish spectral correspondence, candidate ranking, statistical support, and a validated detection claim.

In particular:

- Spectral overlap alone is not sufficient evidence to establish atmospheric presence.
- A numerical score is not a detection probability unless its interpretation has been justified and validated.
- A candidate ranking does not constitute a quantitative abundance measurement.
- Missing uncertainty information must not be silently replaced with assumed certainty.
- Inconclusive results must be permitted and clearly represented.

Thresholds and interpretation rules must be developed through the validation strategy rather than selected arbitrarily.

### 8.4 Failed or incomplete comparisons

If a method cannot execute, ECAS must record the failure or incomplete status and explain the cause where possible.

A failed analysis must not produce a successful candidate result.

If partial outputs are retained for diagnostic purposes, they must be explicitly labeled as incomplete and excluded from workflows that assume successful execution.

---

## 9. Persistence and Project Organization

ECAS organizes research into one project per planet. Each project may contain multiple observations and multiple analysis runs.

The persistence workflow must preserve both the relationships between records and the identity of the exact data used in each analysis.

### 9.1 Storage responsibilities

The intended storage model separates:

- **Structured records:** projects, planets, observations, reference metadata, analysis configurations, results, and relationships.
- **Source artifacts:** original imported or retrieved datasets and associated payloads where permitted.
- **Normalized data:** parsed representations used by ECAS.
- **Derived artifacts:** prepared spectra, synthesized references, plots, exports, and other analysis outputs.
- **Shared cached resources:** downloaded references and other reusable datasets.

SQLite is intended for structured records. Files will hold larger datasets and artifacts where appropriate.

Exact schemas, storage paths, migration behavior, and file lifecycle rules remain the responsibility of the data-model and persistence design.

The existing SQLite persistence implementation supports the current spectrum representation. It must not be assumed to support every future astronomical product, reference representation, or provenance requirement without further design and verification.

### 9.2 Saving an analysis

An analysis record should identify:

- The planet project.
- The observation used.
- The molecular reference or references used.
- The exact source versions or content identities.
- The preparation operations and parameters.
- The comparison method and version.
- The method configuration.
- The software versions needed for reproducibility.
- The results and diagnostics.
- The execution status.
- Warnings, limitations, and relevant citations.

The record must also preserve links to required derived inputs and artifacts.

An analysis should not be considered successfully saved until its required structured records and referenced artifacts have been persisted and verified to the extent required by the storage design.

### 9.3 Updating existing data

When new data are retrieved or a source dataset changes, ECAS must not silently replace the input associated with an earlier analysis.

New versions should be registered distinctly where needed. Existing analyses must continue to identify the inputs they originally used.

A user may choose to run a new analysis using updated inputs. That operation should create a new analysis record rather than rewrite the history of the previous run.

### 9.4 Persistence and recovery failures

If persistence fails, ECAS must avoid presenting the operation as successful.

The storage workflow should minimize inconsistent states, such as a database record pointing to a nonexistent artifact or a completed analysis record referring to an unfinished output.

Exact transaction, integrity-check, and recovery procedures will be specified during persistence design.

---

## 10. Caching and Offline Workflows

Offline support is a requirement for saved projects and locally available data.

Network-dependent operations must be separated from operations that can use existing local records and cached inputs.

### 10.1 Cache responsibilities

Caching should support repeat access to retrieved data while preserving source identity and reproducibility.

A cache entry should be associated with enough information to distinguish the source product and its version or content identity.

Where available, cache metadata should include:

- Provider or source identity.
- Provider-specific product identifier.
- Original source URL or stable record URL.
- Retrieval timestamp.
- Source version or content identifier.
- Content checksum, where practical.
- Original artifact location.
- Parse or normalization status.
- Relevant citation and attribution information.

The cache must not treat a matching filename as sufficient evidence that two products are identical.

### 10.2 Repeat retrieval

When a previously retrieved dataset is requested again, ECAS should determine whether an existing cached copy can be reused.

Reuse should be based on source identity and available version or content information, not merely on filename.

The cache should distinguish between:

- A valid cached source artifact.
- A successfully parsed and validated representation.
- A failed or incomplete retrieval.
- A cached product that may have become outdated.
- A new source version.

A failed refresh must not destroy a previously valid cached version.

Exact cache invalidation and refresh policies remain open until the initial providers and their versioning behavior are understood.

### 10.3 Supported offline operations

When the required data and software are available locally, users should be able to:

- Open and inspect saved planet projects.
- Browse previously registered observations and references.
- View saved plots, analysis results, diagnostics, and citations.
- Review previous analysis configurations and processing history.
- Import local files.
- Run supported comparisons using locally available inputs.
- Rerun eligible analyses without retrieving their source data again.
- Run validation workflows using locally available benchmark inputs.

These are intended capabilities. They must not be presented as implemented until verified.

### 10.4 Network-dependent operations

The following operations generally require connectivity unless the necessary information is already cached:

- Searching remote archives.
- Downloading new observations.
- Downloading new molecular references.
- Refreshing remote catalog information.
- Retrieving updated versions of previously cached datasets.

### 10.5 Missing offline dependencies

If an offline operation requires unavailable data, software, or artifacts, ECAS must identify the missing dependency and explain why the operation cannot continue.

The application must not silently substitute a different dataset, retrieve an unrecorded replacement, or claim to have reproduced an analysis when its original inputs are unavailable.

Where possible, users should still be able to inspect saved results and determine what is required to rerun the analysis.

---

## 11. Provenance and Reproducibility

Provenance is a continuous part of the data flow, not a final reporting step.

Every acquisition, transformation, reference selection, and analysis must preserve the information needed to understand where the data came from and how the results were produced.

### 11.1 Provenance chain

The intended provenance chain is:

```text
Original source artifact
          |
          v
Retrieved or imported dataset
          |
          v
Parsed representation
          |
          v
Validated registered dataset
          |
          v
Prepared or synthesized derivative
          |
          v
Comparison execution
          |
          v
Candidate results and diagnostics
          |
          v
Saved analysis and report
```

Not every dataset will pass through every stage. For example, a measured reference may be used without synthesis, while a theoretical line list may require an additional synthesis stage.

Each derived product must retain links to its direct inputs and relevant transformation history.

### 11.2 Provenance requirements

Where available and applicable, ECAS should preserve:

- Source provider and record identifier.
- Original source URL or citation.
- Original filename or artifact identifier.
- Retrieval or import timestamp.
- Source version or content identity.
- Target or molecular identity.
- Spectral coordinate and signal definitions.
- Units and uncertainty information.
- Original processing status.
- Validation outcomes and warnings.
- Transformation names, versions, and parameters.
- Relevant software versions.
- Analysis method and configuration.
- Output identities and execution status.

Unavailable metadata must remain distinguishable from metadata that have been inferred, supplied by the user, or derived during processing.

### 11.3 Reproducibility requirements

An analysis should be reproducible when the required inputs, method, configuration, software dependencies, and execution conditions are available.

The application should preserve enough information to determine:

- Which data were used.
- Which versions were used.
- How the inputs were prepared.
- Which method was executed.
- Which settings were applied.
- Which software versions were involved.
- What outputs were produced.
- Which warnings and limitations applied.

Where exact numerical reproducibility is not possible because of software, hardware, or numerical differences, ECAS should preserve sufficient information to investigate the discrepancy.

A stored result without its input and method history is not a fully traceable analysis.

---

## 12. Error Handling and Recovery

Errors should be handled at the stage where they occur and communicated to the application workflow.

Expected failure categories include:

- Archive or network unavailability.
- Missing or inaccessible files.
- Unsupported or malformed input formats.
- Missing or ambiguous metadata.
- Invalid spectral values or incompatible dimensions.
- Corrupt or incomplete cached data.
- Scientifically incompatible observation and reference pairs.
- Missing preparation capabilities.
- Unavailable comparison methods or dependencies.
- Comparison execution failures.
- Storage or artifact-persistence failures.
- Missing inputs during offline reruns.

### 12.1 Failure-handling rules

1. Do not silently substitute unrelated or newer data.
2. Do not treat incomplete downloads or failed analyses as successful.
3. Preserve useful diagnostics without exposing unnecessary sensitive information.
4. Retain valid prior data when a refresh or update fails.
5. Make it clear whether the failure affects acquisition, validation, analysis, or persistence.
6. Permit retry or recovery when appropriate.
7. Preserve historical analysis records when later operations fail.
8. Distinguish warnings from conditions that prevent an operation from proceeding.
9. Do not silently discard source metadata or uncertainty information during parsing.
10. Do not interpret a successful network response as proof that its contents are a scientifically valid dataset.

### 12.2 Partial progress

A workflow may complete some stages before a later stage fails.

Where safe and useful, completed stages may be retained. For example, a successfully imported observation can remain registered even if a later comparison fails.

However, retained partial progress must have an accurate status and must not be presented as a completed end-to-end analysis.

---

## 13. Workflow Boundaries and Responsibilities

The data flow must preserve the component boundaries established in `ARCHITECTURE.md` and `MODULE_RESPONSIBILITIES.md`.

| Operation | Primary responsibility |
|---|---|
| User selections and workflow initiation | Desktop UI |
| Coordination of acquisition and analysis steps | Application services |
| Online retrieval and source-specific parsing | Source adapters and ingestion |
| Local-file parsing | Import and ingestion components |
| Structural and metadata validation | Validation services |
| Scientific suitability and compatibility assessment | Comparability services |
| Reference discovery and management | Molecular reference library |
| Documented transformations | Spectral preparation services |
| Spectral comparison | Selected comparison method |
| Candidate result interpretation and evaluation | Scoring and validation services |
| Structured record persistence | Persistence services |
| Source artifacts and derived artifact storage | File and cache management |
| Plot construction and result presentation | Visualization and reporting |
| Operational diagnostics | Logging and error-handling services |

These responsibilities do not require a separate module for every row. Implementation should preserve meaningful boundaries without creating unnecessary layers or abstractions.

The desktop UI must not bypass application services to perform scientific analysis or access the database directly.

Scientific comparison methods must not retrieve network data, parse provider-specific formats, or manipulate UI state.

Provider-specific retrieval must remain separate from scientific interpretation. A successful download does not establish comparability or justify a molecular detection claim.

---

## 14. Acceptance Criteria

The following criteria define the intended behavior of the data-flow architecture. They are not claims that every capability is currently implemented.

### 14.1 Acquisition and validation

- [ ] Local-file import and online retrieval use appropriate shared validation stages.
- [ ] Unsupported file formats produce clear errors.
- [ ] Missing or ambiguous metadata are not silently invented.
- [ ] Invalid datasets cannot proceed into analysis as valid inputs.
- [ ] Valid datasets with limitations retain their warnings.
- [ ] Original source identity and provenance are preserved.
- [ ] Catalog entries are distinguished from actual usable data products.
- [ ] Retrieval failures cannot produce falsely successful registrations.

### 14.2 Molecular references

- [ ] Experimental spectra are distinguished from theoretical line lists.
- [ ] Synthesized spectra are identifiable as derived products.
- [ ] Reference versions remain traceable from saved analyses.
- [ ] Shared references can be reused across planet projects without erasing historical versions.
- [ ] Missing reference data are reported rather than silently substituted.

### 14.3 Comparability and preparation

- [ ] Comparability is assessed before method execution.
- [ ] Incompatible inputs produce an explanation rather than an arbitrary score.
- [ ] Required preparation steps are documented.
- [ ] Original source datasets remain unchanged by preparation.
- [ ] Prepared inputs retain their source identities and transformation history.
- [ ] Unknown units or scientific quantities are not invented.

### 14.4 Comparison and scoring

- [ ] Comparison methods use a documented integration contract.
- [ ] Method-specific score meanings and limitations are retained.
- [ ] Failed analyses cannot be presented as successful results.
- [ ] Candidate results do not automatically imply confirmed detections or quantitative abundances.
- [ ] Results retain the inputs and settings required for reproducibility.

### 14.5 Persistence and offline operation

- [ ] Projects support multiple observations and analyses for one planet.
- [ ] Saved analyses identify their exact inputs and configurations.
- [ ] Updating a dataset does not silently alter historical analyses.
- [ ] Saved projects can be opened without network access when their required data are local.
- [ ] Offline reruns clearly identify missing dependencies.
- [ ] Persistence failures do not result in falsely reported success.
- [ ] Cached data retain enough source identity and version information to support repeat access.

### 14.6 Reproducibility

- [ ] Derived data retain links to their source inputs.
- [ ] Transformations and relevant settings are recorded.
- [ ] Method identity, version, and configuration are preserved.
- [ ] Results retain diagnostics, warnings, and relevant source information.
- [ ] Software correctness tests remain distinct from scientific benchmark validation.
- [ ] Automated fixture tests are not treated as proof of successful live-source retrieval.

---

## 15. Open Decisions

The following decisions remain unresolved unless separately approved and recorded in `DECISIONS.md`:

1. Initial online archive providers and their supported data products.
2. Initial molecular-reference sources and supported representations.
3. Initial local observation file formats beyond the existing importer capabilities.
4. Minimum metadata and validation rules for each supported data-product type.
5. The first production comparison method and its specific input requirements.
6. Which spectral preparation operations are required for that method.
7. Final domain models and relationships for astronomical observations, measured references, line lists, and calculated spectra.
8. Final database schemas, storage paths, cache policies, and migration behavior.
9. Cache identity, version detection, refresh, and invalidation rules.
10. Exact candidate-result structure and score interpretation.
11. Benchmark cases, evaluation metrics, and threshold selection.
12. The minimum reproducibility record for a saved analysis.
13. Performance expectations for loading, plotting, caching, and analysis.

These decisions can be resolved incrementally as the relevant source data, benchmark evidence, and implementation requirements become available.

They do not prevent defining the general data flow, but they must be resolved before implementing features that depend on them.

---

## 16. Relationship to Other Documents

This document defines workflow behavior and the movement of data between ECAS components.

It should be used alongside:

- `ECAS.md` — project purpose, scope, and governing scientific principles.
- `ARCHITECTURE.md` — system layers, component responsibilities, and dependency rules.
- `DATA_MODELS.md` — entities, relationships, identifiers, metadata, and persistence constraints.
- `MODULE_RESPONSIBILITIES.md` — module ownership and interface definitions.
- `VALIDATION_STRATEGY.md` — benchmark selection, evaluation methods, threshold derivation, and limits of scientific claims.
- `DECISIONS.md` — approved decisions and their rationale.
- `PROJECT_STATE.md` — verified implementation status and outstanding work.
- `ECAS_development_plan.md` — development chunks, scope, and completion criteria.

If a conflict arises between documents, it must be identified and reviewed rather than resolved through an unrecorded assumption.

Implementation status must be verified against the actual code and tests. A planned workflow described here must not be reported as an existing capability without evidence.

---

## 17. Conclusion

ECAS should use a traceable, staged data workflow in which acquisition, parsing, validation, registration, comparability assessment, preparation, comparison, and persistence are distinct responsibilities.

The workflow must support both online and local data sources while preserving source identity, scientific meaning, uncertainty, and provenance. Astronomical observations, experimentally measured molecular spectra, theoretical line lists, and calculated spectra must remain distinguishable throughout acquisition, storage, preparation, and analysis.

The existing application provides a foundation for local spectral import, persistence, and visualization. Additional archive integration, molecular-reference handling, scientific comparison, and reproducibility capabilities must be introduced incrementally and verified against their own acceptance criteria.

This document defines intended behavior. It does not authorize implementation or establish that proposed capabilities have already been delivered.
