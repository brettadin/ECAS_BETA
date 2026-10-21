# ECAS Data Flow

**Document status:** Draft for review  
**Project:** Exoplanet Characterization and Spectral Analysis (ECAS)  
**Related documents:** `ECAS.md`, `ARCHITECTURE.md`  
**Implementation status:** This document does not authorize implementation.

---

## 1. Purpose

This document defines how scientific data moves through ECAS, from initial acquisition or import to validation, preparation, comparison, persistence, and presentation of results.

It establishes the expected sequence of operations, the responsibilities of each stage, the information that must be preserved, and the behavior expected when an operation cannot proceed.

The initial workflow focuses on exoplanet transmission spectra and molecular reference data. Both online archive retrieval and local-file import must be supported.

This document describes intended system behavior rather than finalized code, database schemas, or provider-specific implementations.

### 1.1 Governing principles

All data flows must follow these principles:

1. Preserve original source data whenever permitted and practical.
2. Record provenance and distinguish original data from derived products.
3. Validate data before using it in scientific analysis.
4. Distinguish structural validity from scientific comparability.
5. Record transformations rather than silently altering inputs.
6. Preserve uncertainty, units, metadata, and limitations where available.
7. Make analyses reproducible from their recorded inputs and settings.
8. Support offline workflows when the required data and software are available locally.
9. Report failures explicitly rather than silently substituting data or producing misleading results.
10. Never interpret spectral similarity alone as proof of molecular detection.

---

## 2. End-to-End Workflow

The initial ECAS workflow consists of the following stages:

1. Identify an exoplanet and open or create its project.
2. Acquire an observation through an online archive or local-file import.
3. Preserve the source and record its provenance.
4. Parse the input into a supported internal representation.
5. Validate the observation and its metadata.
6. Register the observation with the appropriate project.
7. Find or acquire a molecular reference dataset.
8. Validate and register the reference dataset.
9. Assess whether the observation and reference are scientifically comparable.
10. Prepare comparison inputs through documented transformations, where necessary.
11. Execute a selected comparison method.
12. Generate candidate results, diagnostics, warnings, and supporting metadata.
13. Persist the analysis and its outputs.
14. Present the results for inspection and further investigation.

Not every workflow must execute every stage. For example, an existing observation can be reused without downloading it again, and a previously completed analysis can be inspected without rerunning the comparison.

A workflow must not proceed past a required stage when its prerequisites have not been satisfied.

### 2.1 High-level data flow

```text
                  USER / DESKTOP UI
                         |
                         v
                Select planet/project
                         |
                         v
              Acquire observation data
                  /             \
                 v               v
          Online archive      Local file
                 \               /
                  v             v
                Preserve source
                       |
                       v
                  Parse input
                       |
                       v
                Validate data
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
                      Validate reference
                              |
                              v
                     Assess comparability
                              |
                    +---------+---------+
                    |                   |
               Incompatible          Compatible
                    |                   |
                    v                   v
              Explain issue      Prepare inputs
                                        |
                                        v
                                Run comparison method
                                        |
                                        v
                               Generate candidate results
                                        |
                                        v
                               Persist analysis and outputs
                                        |
                                        v
                                Display results to user
```

This diagram represents the normal successful path and its primary decision points. Individual operations may have additional failure and recovery paths.

---

## 3. Observation Acquisition

ECAS must provide two initial routes for acquiring observation data:

- Retrieval from supported online archives.
- Import from supported local files.

Both routes must converge on the same validation and registration workflow.

### 3.1 Online archive retrieval

The intended sequence is:

1. The user identifies a planet or searches for one.
2. ECAS searches a supported archive for relevant observations.
3. Available observations are presented with sufficient metadata to distinguish datasets.
4. The user selects an observation to retrieve or use.
5. ECAS retrieves the selected source data and available associated metadata.
6. The application records the source identity, retrieval information, and relevant version information.
7. The retrieved payload is preserved where permitted.
8. The data are parsed and submitted to the shared validation workflow.

Archive search results must not automatically be treated as usable observations. The existence of a catalog entry or downloadable file does not establish that its contents are supported or suitable for the intended analysis.

Where multiple observations exist for the same planet, each observation must retain its own identity and metadata.

### 3.2 Local-file import

The intended sequence is:

1. The user selects a local file.
2. ECAS identifies whether the file matches a supported format.
3. The importer parses the file and extracts available metadata.
4. ECAS identifies missing, ambiguous, malformed, or unsupported fields.
5. The source file is preserved or referenced according to the storage policy.
6. The imported data are submitted to the shared validation workflow.
7. If validation succeeds, the observation is registered and made available to the project.

Importing a file must not bypass validation simply because the file exists locally.

ECAS must not silently invent missing scientific metadata. Where a required field is absent or ambiguous, the application must report the problem and either request clarification or reject the input for the intended operation.

The initial supported file formats remain an open decision.

### 3.3 Common acquisition requirements

Regardless of acquisition route, ECAS should preserve the following information where available:

- Source identifier or original filename.
- Source archive or origin.
- Retrieval or import timestamp.
- Planet association and relevant catalog identifiers.
- Instrument and observational metadata.
- Spectral coordinate and signal definitions.
- Units and uncertainty information.
- Original processing status.
- Quality flags and data-quality information.
- Source version or content identity.
- Any limitations affecting interpretation.

Unavailable metadata must remain distinguishable from metadata that have been inferred, supplied by the user, or derived during processing.

### 3.4 Acquisition failures

Acquisition may fail because of network unavailability, archive errors, missing files, unsupported formats, incomplete downloads, or access restrictions.

On failure, ECAS must:

- Report which operation failed.
- Preserve any useful diagnostic information.
- Avoid registering an incomplete dataset as a successfully acquired observation.
- Retain partial data only when doing so is safe and its incomplete status is recorded.
- Allow the user to retry or choose another source when appropriate.

A failed online retrieval must not prevent the user from importing an available local file.

---

## 4. Parsing, Validation, and Registration

Parsing, validation, and scientific suitability assessment are separate operations.

A file can be successfully parsed but contain invalid data. A dataset can be structurally valid but unsuitable for a particular comparison.

### 4.1 Parsing

Parsing converts a supported source representation into an internal data representation without changing its scientific meaning.

The parser should identify the available spectral coordinates, signal values, uncertainties, quality indicators, units, and metadata.

Provider-specific or file-format-specific parsing must remain isolated from the scientific comparison methods.

If a parser encounters unsupported structures or ambiguous columns, it must report the ambiguity instead of silently assigning scientific meaning.

### 4.2 Structural and metadata validation

Validation checks whether a parsed dataset meets the minimum requirements for its declared role.

Checks should include, as applicable:

- Required spectral coordinates and signal values are present.
- Coordinate and signal arrays have compatible dimensions.
- Units are identified or explicitly marked unknown.
- Numeric values are finite where required.
- Missing values and invalid entries are identified.
- Duplicate or non-monotonic coordinates are detected and handled explicitly.
- Uncertainties and quality flags are preserved where supplied.
- Metadata are internally consistent enough to identify the dataset.
- Provenance information is available.
- The dataset has not been mistaken for a different spectral quantity.

Validation should distinguish errors that prevent use from warnings that allow limited use.

For example, missing uncertainty information may not prevent a dataset from being displayed, but it may restrict which comparison methods can use it and what conclusions can be supported.

### 4.3 Validation outcomes

Each validation operation should produce an explicit outcome.

| Outcome | Meaning |
|---|---|
| Valid | The dataset satisfies the requirements checked for its intended role. |
| Valid with warnings | The dataset can be used, but known limitations must remain visible. |
| Invalid | One or more required conditions are not satisfied. |
| Incomplete | The available data are insufficient to finish validation. |

These are conceptual outcomes. Exact status representations and error categories will be defined during implementation planning.

### 4.4 Registration

After successful validation, ECAS registers the dataset and its metadata in the appropriate project or shared library.

Registration must preserve the relationship between the dataset and its original source.

For observations, registration associates the observation with the relevant planet project. For shared molecular references, registration associates the reference with the central reference library and makes it available to eligible projects.

Registration must not overwrite a previously registered observation or reference merely because a new file has the same name.

Where duplicate or updated content is detected, ECAS should identify the relationship and preserve distinct versions when necessary.

---

## 5. Molecular Reference Acquisition

Molecular reference data follow a workflow similar to observation acquisition, but their scientific meaning and requirements differ.

ECAS must distinguish at least three relevant representations:

1. Measured or experimentally derived spectral data.
2. Theoretical spectroscopic line lists.
3. Spectra synthesized from theoretical or other model inputs.

These representations must not be treated as interchangeable.

### 5.1 Reference discovery and selection

The intended sequence is:

1. The user selects a molecular candidate or searches the reference library.
2. ECAS identifies available reference datasets for that molecule.
3. Reference records display their source, representation type, units, available conditions, and relevant limitations.
4. The user selects a reference dataset.
5. ECAS retrieves the dataset if necessary or loads its cached copy.
6. The dataset is parsed, validated, and registered if it has not already been registered.

A molecule's presence in the reference catalog does not guarantee that an appropriate reference dataset is available.

The system must allow for missing reference data and multiple reference datasets for the same molecule.

### 5.2 Measured or experimentally derived spectra

Where available, ECAS should retain the reported experimental conditions, spectral quantity, units, resolution, uncertainty information, source, and processing status.

The applicability of an experimental spectrum to an exoplanet atmosphere must be assessed separately from the validity of the measurement itself.

Laboratory conditions may differ substantially from the conditions represented by an astronomical observation. ECAS must not imply direct equivalence when relevant differences remain unresolved.

### 5.3 Theoretical line lists

A line list describes discrete spectroscopic transitions rather than necessarily providing a directly comparable continuous spectrum.

Before a line list can be used by a method requiring a continuous spectral representation, an appropriate conversion or synthesis operation may be necessary.

That operation must record its inputs, method, settings, assumptions, and relevant physical conditions.

ECAS must not silently treat line positions or transition strengths as though they were measured continuous-spectrum values.

### 5.4 Synthesized references

A synthesized spectrum must retain its relationship to the underlying theoretical or measured inputs.

Its provenance should include the synthesis method, software version, applicable physical assumptions, line-profile treatment, spectral resolution, and other settings that materially affect the output.

A synthesized reference must remain identifiable as a derived product rather than a direct experimental measurement.

### 5.5 Shared reference storage

Reference datasets should normally be stored in the shared reference library and reused across planet projects.

Projects should record which reference version or content identity was used for an analysis. Updating a shared reference must not silently change the historical inputs of an existing analysis.

---

## 6. Comparability Assessment and Spectral Preparation

Before a comparison method executes, ECAS must determine whether the selected observation and reference are sufficiently compatible for that method.

This stage is essential because structurally valid spectra may represent different physical quantities or have incompatible units, coverage, resolution, or processing.

### 6.1 Comparability assessment

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
- Any additional method-specific requirements.

Not every method will require the same inputs. Comparability must therefore be assessed against a declared method contract rather than a single universal rule.

### 6.2 Comparability outcomes

The assessment should distinguish:

- **Compatible:** the data satisfy the method's required compatibility conditions.
- **Compatible with limitations:** the method can run, but documented limitations affect interpretation.
- **Conditionally compatible:** a specified transformation or additional user decision is required before proceeding.
- **Incompatible:** the data cannot be used meaningfully by the selected method under the current conditions.
- **Undetermined:** insufficient metadata or scientific information prevents a reliable assessment.

The application must explain the reason for a negative or conditional outcome whenever practical.

A method must not be executed merely because two datasets can be represented as numeric arrays.

### 6.3 Spectral preparation

If preparation is required, ECAS creates derived inputs from the registered source datasets.

Potential operations include:

- Unit conversion.
- Selection or masking of spectral regions.
- Resampling onto a compatible coordinate grid.
- Resolution matching.
- Normalization.
- Application of explicitly documented quality filters.
- Other transformations required by a selected comparison method.

These are examples of possible operations, not a commitment to implement every operation in the initial release.

The first comparison method and benchmark investigation will determine which transformations are scientifically justified and necessary.

Each transformation must record, as applicable:

- Source dataset identity and version.
- Transformation name and version.
- Input and output units.
- Parameters and settings.
- Any assumptions or approximations.
- Effects on uncertainty information.
- Warnings or limitations.

Preparation must not modify the original source dataset.

If a transformation changes the data in a way that affects scientific interpretation, that change must remain visible in the analysis record.

### 6.4 Prepared-input identity

Prepared inputs must be identifiable as derived data, not independent observations or original reference measurements.

Where practical, ECAS should reuse an existing prepared dataset when its source identities, transformation sequence, parameters, and relevant software versions match.

Reuse must not occur when the application cannot establish that the prepared data are equivalent for the intended operation.

---

## 7. Comparison and Candidate Scoring

The comparison stage consumes validated, prepared inputs and returns method-defined results.

It must not retrieve external data, parse provider-specific files, access desktop UI state, or independently manage project persistence.

### 7.1 Comparison execution

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

The first comparison method remains undecided pending benchmark investigation.

The architecture must permit additional methods to be introduced through a common interface without requiring changes to the entire acquisition, project, or UI architecture.

### 7.2 Method outputs

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

### 7.3 Candidate scoring and interpretation

Candidate scoring must not imply a stronger scientific conclusion than the underlying method supports.

ECAS must distinguish spectral correspondence, candidate ranking, statistical support, and a validated detection claim.

In particular:

- Spectral overlap alone is not evidence sufficient to establish atmospheric presence.
- A numerical score is not a detection probability unless its interpretation has been justified and validated.
- A candidate ranking does not constitute a quantitative abundance measurement.
- Missing uncertainty information must not be silently replaced with assumed certainty.
- Inconclusive results must be permitted and clearly represented.

Thresholds and interpretation rules must be developed through the validation strategy rather than selected arbitrarily.

### 7.4 Failed or incomplete comparisons

If a method cannot execute, ECAS must record the failure or incomplete status and explain the cause where possible.

A failed analysis must not produce a successful candidate result.

If partial outputs are retained for diagnostic purposes, they must be explicitly labeled as incomplete and excluded from any workflow that assumes successful execution.

---

## 8. Persistence and Project Organization

ECAS organizes research into one project per planet. Each project may contain multiple observations and multiple analysis runs.

The persistence workflow must preserve both the relationships between records and the identity of the exact data used in each analysis.

### 8.1 Data storage responsibilities

The intended storage model separates:

- **Structured records:** projects, planets, observations, reference metadata, analysis configurations, results, and relationships.
- **Source files:** original imported or retrieved datasets and associated source payloads where permitted.
- **Derived artifacts:** prepared spectra, synthesized references, plots, exports, and other analysis outputs.
- **Shared cached resources:** downloaded references and other reusable datasets.

SQLite is intended for structured records. Files will hold larger datasets and artifacts where appropriate.

Exact schemas, storage paths, migration behavior, and file lifecycle rules remain the responsibility of the data-model and persistence design.

### 8.2 Saving an analysis

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

### 8.3 Updating existing data

When new data are retrieved or a source dataset changes, ECAS must not silently replace the input associated with an earlier analysis.

New versions should be registered distinctly where needed. Existing analyses must continue to identify the inputs they originally used.

A user may choose to run a new analysis using updated inputs. That operation should create a new analysis record rather than rewrite the history of the previous run.

### 8.4 Saving and recovery failures

If persistence fails, ECAS must avoid presenting the operation as successful.

The storage workflow should minimize inconsistent states, such as a database record pointing to a nonexistent artifact or a completed analysis record referring to an unfinished output.

Exact transaction, integrity-check, and recovery procedures will be specified during persistence design.

---

## 9. Offline Workflows

Offline support is a requirement for saved projects and locally available data.

Network-dependent operations must be separated from operations that can use existing local records and cached inputs.

### 9.1 Supported offline operations

When the required data and software are available locally, users should be able to:

- Open and inspect saved planet projects.
- Browse previously registered observations and references.
- View saved plots, analysis results, diagnostics, and citations.
- Review previous analysis configurations and processing history.
- Import local files.
- Run supported comparisons using locally available inputs.
- Rerun eligible analyses without retrieving their source data again.
- Run validation workflows using locally available benchmark inputs.

### 9.2 Network-dependent operations

The following operations generally require connectivity unless the necessary information is already cached:

- Searching remote archives.
- Downloading new observations.
- Downloading new molecular references.
- Refreshing remote catalog information.
- Retrieving updated versions of previously cached datasets.

### 9.3 Missing offline dependencies

If an offline operation requires unavailable data, software, or artifacts, ECAS must identify the missing dependency and explain why the operation cannot continue.

The application must not silently substitute a different dataset, retrieve an unrecorded replacement, or claim to have reproduced an analysis when its original inputs are unavailable.

Where possible, users should still be able to inspect the saved results and determine what is required to rerun the analysis.

---

## 10. Provenance and Reproducibility

Provenance is a continuous part of the data flow, not a final reporting step.

Every acquisition, transformation, reference selection, and analysis must preserve the information needed to understand where the data came from and how the results were produced.

### 10.1 Provenance chain

The intended provenance chain is:

```text
Original source
      |
      v
Parsed dataset
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

### 10.2 Reproducibility requirements

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

## 11. Error Handling and Recovery

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

### 11.1 Failure-handling rules

1. Do not silently substitute unrelated or newer data.
2. Do not treat incomplete downloads or failed analyses as successful.
3. Preserve useful diagnostics without exposing unnecessary sensitive information.
4. Retain valid prior data when a refresh or update fails.
5. Make it clear whether the failure affects data acquisition, validation, analysis, or persistence.
6. Permit retry or recovery when appropriate.
7. Preserve historical analysis records when later operations fail.
8. Distinguish warnings from conditions that prevent an operation from proceeding.

### 11.2 Partial progress

A workflow may complete some stages before a later stage fails.

Where safe and useful, completed stages may be retained. For example, a successfully imported observation can remain registered even if a later comparison fails.

However, retained partial progress must have an accurate status and must not be presented as a completed end-to-end analysis.

---

## 12. Workflow Boundaries and Responsibilities

The data flow must preserve the component boundaries established in `ARCHITECTURE.md`.

| Operation | Primary responsibility |
|---|---|
| User selections and workflow initiation | Desktop UI |
| Coordination of acquisition and analysis steps | Application services |
| Online retrieval and source-specific parsing | Source adapters and ingestion |
| Local-file parsing | Import and ingestion components |
| Structural and metadata validation | Validation services |
| Reference discovery and management | Molecular reference library |
| Scientific compatibility assessment | Comparability services |
| Documented transformations | Spectral preparation services |
| Spectral comparison | Selected comparison method |
| Candidate result interpretation and evaluation | Scoring and validation services |
| Structured record persistence | Persistence services |
| Source files and derived artifact storage | File and cache management |
| Plotting and result presentation | Visualization and reporting |
| Operational diagnostics | Logging and error-handling services |

These responsibilities do not require a separate module for every row. Implementation should preserve meaningful boundaries without creating unnecessary layers or abstractions.

The desktop UI must not bypass application services to perform scientific analysis or access the database directly. Scientific comparison methods must not retrieve network data or manipulate UI state.

---

## 13. Acceptance Criteria

The data-flow design will be considered sufficiently defined for implementation planning when the following requirements are understood and agreed upon.

### 13.1 Acquisition and validation

- [ ] Online archive retrieval and local-file import converge on shared validation.
- [ ] Unsupported file formats produce clear errors.
- [ ] Missing or ambiguous metadata are not silently invented.
- [ ] Invalid datasets cannot proceed into analysis as valid inputs.
- [ ] Valid datasets with limitations retain their warnings.
- [ ] Original source identity and provenance are preserved.

### 13.2 Molecular references

- [ ] Measured or experimentally derived spectra are distinguished from theoretical line lists.
- [ ] Synthesized spectra are identifiable as derived products.
- [ ] Reference versions remain traceable from saved analyses.
- [ ] Shared references can be reused across planet projects without erasing historical versions.

### 13.3 Comparison and scoring

- [ ] Comparability is assessed before method execution.
- [ ] Incompatible inputs produce an explanation rather than an arbitrary score.
- [ ] Required preparation steps are documented.
- [ ] Comparison methods use a common integration contract.
- [ ] Method-specific score meanings and limitations are retained.
- [ ] Failed analyses cannot be presented as successful results.
- [ ] Candidate results do not automatically imply confirmed detections or quantitative abundances.

### 13.4 Persistence and offline operation

- [ ] Projects support multiple observations and analyses for one planet.
- [ ] Saved analyses identify their exact inputs and configurations.
- [ ] Updating a dataset does not silently alter historical analyses.
- [ ] Saved projects can be opened without network access.
- [ ] Offline reruns clearly identify missing dependencies.
- [ ] Persistence failures do not result in falsely reported success.

### 13.5 Reproducibility

- [ ] Derived data retain links to their source inputs.
- [ ] Transformations and relevant settings are recorded.
- [ ] Method identity, version, and configuration are preserved.
- [ ] Results retain diagnostics, warnings, and relevant source information.
- [ ] Software correctness tests remain distinct from scientific benchmark validation.

---

## 14. Open Decisions

The following decisions remain unresolved and must not be assumed to have been made by this document:

1. Initial online archive providers.
2. Initial local observation file formats.
3. Initial molecular reference sources and supported representations.
4. The first comparison method and its specific input requirements.
5. Which spectral preparation operations are required for that method.
6. Exact validation rules and minimum metadata requirements for each supported format.
7. Final data schemas, storage paths, cache policies, and migration behavior.
8. Exact candidate-result structure and score interpretation.
9. Benchmark cases, evaluation metrics, and threshold selection.
10. The desktop UI framework and its implementation-specific workflow behavior.

These decisions can be resolved incrementally as the relevant source data, benchmark evidence, and implementation requirements become available. They do not prevent defining the general data flow.

---

## 15. Relationship to Other Documents

This document defines workflow behavior and the movement of data between ECAS components.

It should be used alongside:

- `ECAS.md` — project purpose, scientific principles, and long-term direction.
- `ARCHITECTURE.md` — system layers, component responsibilities, and dependency rules.
- `MODULE_RESPONSIBILITIES.md` — module ownership and interface definitions.
- `DATA_MODELS.md` — entities, relationships, identifiers, metadata, and persistence constraints.
- `VALIDATION_STRATEGY.md` — benchmark selection, evaluation methods, threshold derivation, and limits of scientific claims.
- `DECISIONS.md` — approved decisions and their rationale.
- `PROJECT_STATE.md` — verified project status and outstanding work.

If a conflict arises between documents, it must be identified and reviewed rather than resolved through an unrecorded assumption.

## 16. Related Documents
ECAS.md — defines the overall project purpose and scope.

ARCHITECTURE.md — describes the system components and their boundaries.

DATA_MODELS.md — defines the records used to represent data and processing history.

MODULE_RESPONSIBILITIES.md — identifies which modules own each part of the workflow.

VALIDATION_STRATEGY.md — defines how comparison methods will be evaluated.

IMPLEMENTATION_PLAN.md — defines the proposed order for implementing the workflow.

---

**Draft conclusion:** ECAS should use a traceable, staged data workflow in which acquisition, validation, comparability assessment, preparation, comparison, and persistence are distinct responsibilities. The workflow supports both online and local data sources, preserves scientific provenance, and allows analysis methods to evolve without compromising the integrity of existing projects or results. This document defines intended behavior; it does not authorize implementation.