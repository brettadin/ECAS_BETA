# ECAS Validation Strategy

## 1. Purpose

This document defines the strategy for validating data, software behavior, and scientific analysis within **ECAS — Exoplanetary Characterization & Astrochemistry Suite**.

Validation must establish that:

- Imported data are structurally valid and retain their scientific meaning and provenance.
- Stored data remain consistent and can be retrieved without unintended changes.
- Analysis procedures operate within their documented assumptions and limitations.
- Scientific comparisons are reproducible, interpretable, and supported by traceable evidence.
- Results do not overstate what the available observations or analysis methods establish.

Validation is an ongoing process throughout development. Passing software tests does not, by itself, establish scientific validity.

## 2. Scope

This strategy covers five areas:

1. **Data validation:** checking the structure, values, metadata, units, and provenance of imported data.
2. **Persistence validation:** checking data integrity during storage, retrieval, update, and deletion.
3. **Software validation:** checking that application components behave as specified.
4. **Scientific validation:** checking that analysis methods and interpretations are appropriate for the available evidence.
5. **Reproducibility and traceability:** preserving enough information to understand and repeat an analysis.

The strategy applies to currently implemented functionality and provides requirements for future capabilities.

The presence of a requirement in this document does not establish that the corresponding feature, automated check, or scientific evaluation has already been implemented.

## 3. Validation Principles

### 3.1 Scientific integrity

ECAS must distinguish between measured observations, processed observations, theoretical molecular reference data, and synthesized or simulated spectra.

These data types must not be treated as interchangeable. Their origin and intended use must remain identifiable throughout the workflow.

Spectral similarity or overlap is evidence for further investigation, not proof of a molecule's presence in an exoplanet atmosphere.

Scientific conclusions must reflect the limitations of the data, analysis method, uncertainties, and available supporting evidence.

### 3.2 Traceability

Validation outcomes must be traceable to the data, software behavior, or scientific procedure being evaluated.

Where applicable, records should identify:

- The source file, archive record, publication, or reference dataset.
- The relevant observation, instrument, or data product.
- The validation rules applied.
- The software and analysis configuration used.
- Any transformations, exclusions, or corrections applied.
- The outcome of the validation and any unresolved limitations.

Information that is unavailable must not be invented or silently inferred.

### 3.3 Reproducibility

A validation result should be reproducible from the retained inputs, configuration, and documented procedure, subject to the availability of the original sources and software dependencies.

Changes to data, validation rules, reference datasets, or analysis methods must not silently overwrite the context needed to understand earlier results.

### 3.4 Explicit uncertainty

Missing, ambiguous, or insufficient information must be represented explicitly.

ECAS must not silently assign units, axis meanings, instrument properties, uncertainties, or scientific classifications when the available evidence does not support them.

### 3.5 Proportionate validation

Validation depth must reflect the risk and purpose of the operation.

Basic file parsing requires different checks from a scientific comparison intended to support an atmospheric interpretation. Neither level should be treated as a substitute for the other.

## 4. Validation Layers

Validation should be organized into distinct layers so that a successful check at one level is not mistaken for proof of correctness at another.

### 4.1 Structural validation

Structural validation checks whether data can be read and represented in the expected form.

Depending on the input format, checks may include:

- File readability and supported format.
- Expected columns, fields, headers, or schema.
- Numeric conversion and handling of missing values.
- Detection of malformed rows and inconsistent field counts.
- Verification that required fields are present.
- Detection of empty or unusable datasets.
- Validation of array lengths and other structural relationships.

A structurally valid file may still contain scientifically unsuitable or incorrectly labelled data.

### 4.2 Semantic and metadata validation

Semantic validation checks whether values and metadata are interpretable within the declared data model.

Checks should include, where applicable:

- Whether spectral axes and intensity values have identifiable meanings.
- Whether units are supplied and recognized.
- Whether wavelength, frequency, wavenumber, or other axis conventions are correctly identified.
- Whether metadata are consistent with the selected input schema.
- Whether instrument, observation, processing, and source identifiers are preserved.
- Whether required metadata are missing or ambiguous.

ECAS must not convert or compare values across incompatible representations without an explicit, documented conversion or compatibility procedure.

When metadata are insufficient to determine how data should be interpreted, the system should report the limitation and avoid making unsupported assumptions.

### 4.3 Scientific suitability validation

Scientific suitability validation determines whether data are appropriate for a particular analysis.

Potential checks include:

- Whether the data represent the type of observation or reference spectrum required by the analysis.
- Whether relevant units and axis conventions are compatible.
- Whether the spectral coverage is sufficient for the intended comparison.
- Whether resolution, uncertainty, processing history, and instrumental characteristics are known or adequately addressed.
- Whether the proposed comparison method is applicable to the available data.
- Whether the source and provenance are sufficiently documented for the intended use.

A dataset can pass structural and semantic validation while remaining unsuitable for a particular scientific analysis.

## 5. Input and Import Validation

Import validation must be specific to the supported format or schema rather than assuming all CSV or text files have the same structure.

### 5.1 Input handling

For each supported input type, validation should address the relevant cases:

- Valid input with expected structure.
- Missing required columns or fields.
- Empty files and files containing only headers.
- Malformed rows and inconsistent delimiters.
- Non-numeric values in fields expected to be numeric.
- Missing, infinite, or otherwise invalid numeric values.
- Unexpected units or ambiguous axis labels.
- Duplicate records or repeated spectral coordinates where relevant.
- Unsupported formats and unrecognized schemas.

A failed import must provide a useful explanation and must not leave partially imported data presented as a successful result.

### 5.2 Preservation of source information

The original source file should remain unchanged by ordinary import and analysis operations.

Where supported, ECAS should retain the source location or identifier and record any transformations applied during import.

Parsing and normalization must not silently erase meaningful distinctions in the source data.

### 5.3 Format support boundaries

Passing tests for one CSV schema does not establish general CSV compatibility, and passing CSV tests does not establish support for arbitrary TXT, FTIR, UV-Vis, or other instrument-specific formats.

Each supported format must have documented expectations and appropriate test coverage.

Where representative real-world files are unavailable, clearly identified test fixtures may be used. Results from synthetic fixtures must not be presented as proof of compatibility with real scientific datasets.

## 6. Data Integrity and SQLite Persistence

Persistence validation must establish that stored information remains internally consistent and is retrieved as intended.

### 6.1 Integrity requirements

Tests should verify the relevant behavior of the existing persistence layer, including:

- Successful storage and retrieval of valid records.
- Preservation of values and supported metadata across a round trip.
- Correct handling of missing, invalid, and duplicate data according to documented rules.
- Enforcement of applicable schema constraints and relationships.
- Appropriate handling of failed writes and database errors.
- Consistent behavior when updating or deleting records.
- Prevention of unintended partial or duplicate records.
- Safe handling of database initialization and existing database files.

The exact checks must reflect the actual schema and supported operations. Validation must not assume that transaction, rollback, bulk-write, or connection-reuse behavior exists unless it has been implemented and verified.

### 6.2 Database cleanliness

Database cleanliness requires more than confirming that a write operation succeeded.

Where applicable, validation should detect:

- Records missing required identifying information.
- Invalid references between related records.
- Duplicate records that violate defined uniqueness rules.
- Values that violate declared field constraints.
- Records whose source or provenance links are inconsistent.
- Orphaned records where relationships are expected.
- Conflicting metadata for records that are expected to represent the same entity.

Checks must distinguish genuine integrity violations from valid cases, such as multiple observations of the same planet or multiple spectra from different instruments.

A shared planet identifier must not be treated as sufficient grounds for deduplicating observations.

### 6.3 Failure handling

When a persistence operation fails, ECAS must not report success without evidence that the intended operation completed.

Where transactions are used, tests should verify that failures produce the documented rollback or recovery behavior. Where transactions are not used, the limitations of the current behavior must be documented and tested appropriately.

Validation must not assume that a database error automatically leaves the database unchanged.

## 7. Software Testing Strategy

Software validation establishes whether implementation behavior matches the defined requirements.

### 7.1 Unit tests

Unit tests should cover individual functions and components, including:

- Input parsing and validation.
- Data model behavior.
- Persistence operations.
- Data transformation functions.
- Scientific calculation functions when implemented.
- Error handling and boundary conditions.

Tests should be focused enough to identify the component responsible for a failure.

### 7.2 Integration tests

Integration tests should verify interactions between components, including relevant workflows such as:

- Importing data and passing it to the application model.
- Persisting and retrieving imported data.
- Displaying imported data in the interface.
- Passing valid data to visualization components.
- Supplying validated inputs to analysis procedures as those procedures are introduced.

Tests must reflect the actual application workflow and must not assume proposed components already exist.

### 7.3 Interface and workflow tests

Where appropriate, tests should verify that the interface:

- Reports successful and failed operations accurately.
- Presents validation errors in an understandable form.
- Prevents invalid inputs from being treated as valid results.
- Displays the data associated with the selected record.
- Does not silently substitute, omit, or misrepresent data.

If GUI behavior cannot be adequately verified through automated tests, record the necessary manual verification steps and their actual outcomes.

### 7.4 Regression testing

Changes must not unintentionally break previously verified behavior.

Run focused tests for the affected component first, followed by broader regression tests when appropriate.

A test should only be reported as passing when it has actually executed successfully. Test discovery failures, environment errors, dependency problems, and ambiguous terminal output must be distinguished from genuine test success.

## 8. Scientific Validation and Reference Evidence

Scientific validation evaluates whether an analysis method and its interpretation are defensible for the intended use.

### 8.1 Reference data

Reference spectra and other scientific datasets must have identifiable sources and appropriate descriptive metadata.

Where available, retain:

- Source organization, archive, or publication.
- Dataset or record identifier.
- Data type and physical meaning.
- Units and spectral coordinate convention.
- Instrument or measurement conditions.
- Processing history and relevant limitations.
- Version or retrieval information where needed for reproducibility.

The provenance and limitations of theoretical, synthesized, simulated, and measured data must remain distinguishable.

### 8.2 Method validation

Scientific methods should be evaluated against documented expectations and, where possible, independently established reference cases.

Validation may examine:

- Whether the method produces expected results for controlled inputs.
- Whether results are stable under reasonable changes to input data or configuration.
- Whether known limitations and assumptions are handled correctly.
- Whether outputs can be reproduced from the recorded inputs and settings.
- Whether uncertainty and compatibility limitations are appropriately represented.

The method and the evidence supporting its suitability must be documented separately from the code tests that verify its implementation.

### 8.3 Interpretation limits

A successful numerical comparison does not establish a scientific detection.

Interpretation must account for relevant alternative explanations, data quality, uncertainties, instrumental effects, and methodological assumptions.

Where the evidence is insufficient, the output should be described as inconclusive or suitable for further investigation rather than presented as a confirmed finding.

## 9. Benchmark and Test Dataset Design

Validation datasets must be selected and documented according to the behavior or scientific question they are intended to test.

### 9.1 Dataset categories

Where applicable, the test collection should distinguish:

- **Synthetic fixtures:** constructed inputs used to test known structural or numerical behavior.
- **Real observational data:** measurements or processed observations obtained from identifiable sources.
- **Reference data:** theoretical, laboratory, or other reference spectra used for comparison.
- **Benchmark cases:** datasets selected because their expected behavior or published interpretation provides a basis for evaluating a method.
- **Invalid or adversarial inputs:** data designed to exercise failure handling and boundary conditions.

These categories serve different purposes and must not be treated as interchangeable evidence.

### 9.2 Expected outcomes

Each benchmark case should define the expected behavior and the basis for that expectation.

Depending on the case, this may include:

- Whether import or validation should succeed.
- Which metadata or values should be retained.
- Which error or warning should be produced.
- Whether an analysis result falls within a documented tolerance.
- Which limitations prevent a stronger scientific conclusion.

Expected outcomes must be grounded in the test design, source evidence, mathematical properties, or an independently justified reference. They must not be invented merely to make a test pass.

### 9.3 Benchmark provenance

Each real-data benchmark should retain sufficient provenance to locate and identify its source and understand its limitations.

Where published results are used as reference evidence, record the publication or dataset identifier and clarify what the reference actually establishes.

A publication-reported detection, for example, is evidence about the published interpretation under its stated assumptions. It is not automatically independent ground truth for every later analysis.

### 9.4 Separation of development and evaluation data

Where a method is tuned against labelled or benchmark data, the evaluation procedure must account for information leakage.

If observations from the same planet, publication, instrument, or underlying data product are highly related, splitting them across development and evaluation sets may produce misleadingly optimistic results.

The grouping strategy should be selected according to the scientific question and the dependencies in the dataset. Any exclusions, partitions, and tuning decisions should be recorded.

This requirement applies when such evaluation procedures are used; it does not imply that ECAS currently has a machine-learning pipeline or a formal benchmark collection.

## 10. Quantitative Metrics and Acceptance Criteria

Metrics must be selected according to the task being evaluated. No single metric establishes overall scientific validity.

### 10.1 Software and data metrics

Depending on the component, useful measures include:

- Test pass and failure counts.
- Import success and rejection behavior for defined test cases.
- Preservation of values and metadata across persistence round trips.
- Counts of detected integrity violations.
- Agreement with known expected outputs.
- Reproducibility of a result under the same documented inputs and configuration.

These measures evaluate specific properties and must be interpreted within their test coverage.

### 10.2 Scientific metrics

For future spectral comparison or characterization methods, candidate measures may include:

- Residual error or deviation from a defined reference.
- Agreement within documented numerical tolerances.
- Sensitivity to noise and uncertainty.
- Robustness to changes in resolution, sampling, or preprocessing.
- Precision, recall, or related measures where suitable labelled evaluation data exist.
- Calibration and uncertainty assessment where the method produces probabilistic estimates.

Not every metric is appropriate for every method. The choice, definition, and interpretation of a metric must be justified for the scientific task.

### 10.3 Acceptance criteria

Acceptance criteria must be defined before evaluating the results they govern, where practical.

Each criterion should state:

1. The behavior or property being assessed.
2. The evidence or test used.
3. The expected outcome or tolerance.
4. The rationale for the criterion.
5. The handling of failures, uncertainty, and exceptions.

Numerical thresholds must not be introduced without justification. A threshold selected for one dataset, instrument, or analysis method must not be assumed universally valid.

If a defensible threshold has not yet been established, document that limitation rather than inventing one.

## 11. Validation of Scientific Comparability

Before comparing spectra, ECAS should establish whether the relevant data are sufficiently compatible for the intended operation.

Depending on the method, comparability assessment may consider:

- Physical quantity and units.
- Spectral coordinate system and conversion requirements.
- Spectral coverage and sampling.
- Spectral resolution and instrumental response.
- Data processing and normalization.
- Uncertainty information and data quality.
- Observation conditions and relevant metadata.
- Differences between measured and theoretical or synthesized spectra.

A comparison should not proceed as if these differences are irrelevant merely because the data can be plotted together.

If compatibility cannot be established, the limitation should be reported. Any permitted comparison must make the assumptions and unresolved differences explicit.

This section defines a validation requirement; it does not claim that a complete comparability assessment is currently implemented.

## 12. Reproducibility and Analysis Records

Where ECAS supports scientific analysis, an analysis record should preserve enough information to understand how the result was produced.

As applicable, this includes:

- Identifiers for the input observations and reference datasets.
- Source provenance and data versions.
- Analysis method and relevant software version.
- Configuration parameters and thresholds.
- Preprocessing and transformation steps.
- Validation outcomes and warnings.
- Output values, uncertainty information, and interpretation limitations.

If an input or reference dataset changes, the system should make it possible to distinguish results based on different versions or configurations.

Reproducibility claims must reflect what has actually been retained. If a source becomes unavailable or a required dependency cannot be recovered, that limitation should be documented.

## 13. Error Reporting and Validation Outcomes

Validation outcomes should communicate what was checked and what the result means.

Where appropriate, distinguish:

- **Pass:** the defined checks completed and met their acceptance criteria.
- **Fail:** one or more required checks did not meet their criteria.
- **Warning:** a limitation or concern exists but does not necessarily prevent the operation.
- **Inconclusive:** available information is insufficient to determine whether the relevant criterion is satisfied.
- **Not evaluated:** the check was not performed.

These labels describe validation status, not scientific certainty.

An operation must not be reported as fully validated merely because it completed without raising an exception.

Errors and warnings should identify the affected data or operation and provide enough information to support investigation without exposing misleading or unsupported conclusions.

## 14. Validation Evidence and Reporting

Validation evidence should be proportionate to the importance of the claim being made.

For software changes, retain relevant test commands, actual outcomes, and unresolved failures in the project's established development records.

For scientific methods, retain the applicable test cases, benchmark provenance, evaluation procedure, metrics, acceptance criteria, and limitations.

Reports must distinguish among:

- Requirements that have been defined.
- Tests that have been written.
- Tests that have actually been executed.
- Results that have passed their stated criteria.
- Scientific methods that have been evaluated.
- Capabilities or conclusions that remain unverified.

The existence of a test does not establish that it passed. Passing implementation tests does not establish that a scientific method is valid.

## 15. Current Implementation and Future Work

The validation strategy must remain aligned with the actual application.

Currently verified behavior, planned capabilities, and unresolved requirements must be documented separately. The implementation status recorded elsewhere in the project should be consulted before making claims about supported formats, automated scientific checks, benchmark datasets, or analysis methods.

Future validation work should be introduced alongside the corresponding functionality rather than treated as completed merely because its requirements are documented.

When a new capability is proposed, its implementation plan should identify the validation evidence required to demonstrate that it works as intended.

## 16. Limitations and Open Questions

The following matters require evidence or design decisions before stronger requirements can be established:

- Which real observational and reference datasets will be maintained as formal benchmarks.
- Which scientific methods will require quantitative acceptance thresholds.
- How uncertainty will be represented and propagated by each analysis method.
- Which metadata are mandatory for particular analysis workflows.
- Which compatibility differences can be corrected, accommodated, or must prevent comparison.
- How benchmark versions and evaluation partitions will be maintained as the project evolves.
- Which validation results will be stored persistently and which will remain test or development evidence.

These questions should be resolved when the relevant workflows and methods are sufficiently defined. They should not be answered by introducing arbitrary universal thresholds or unsupported assumptions.

## 17. Related Documents

- `docs/ECAS.md` — Project purpose, scientific principles, and long-term objectives.
- `docs/architecture/ARCHITECTURE.md` — System structure and architectural boundaries.
- `docs/architecture/DATA_FLOW.md` — Current and intended data flows.
- `docs/architecture/DATA_MODELS.md` — Domain entities and data representations.
- `docs/architecture/ECAS_Architecture_Specification.md` — Broader architecture requirements and design.
- `docs/architecture/MODULE_RESPONSIBILITIES.md` — Module responsibilities and boundaries.
- `docs/brains/DECISIONS.md` — Approved technical and architectural decisions.
- `docs/brains/PROJECT_STATE.md` — Verified implementation status and outstanding work.

Paths and document contents should be checked against the current repository. Related documents must distinguish implemented behavior from proposed design.

## 18. Revision Policy

Revise this strategy when significant changes affect data formats, persistence behavior, scientific methods, validation criteria, or the evidence required to support scientific conclusions.

Changes to validation requirements should be justified and traceable. New acceptance criteria should state their rationale, scope, and limitations.

Historical validation evidence must not be rewritten to imply that a newer requirement or method was used in an earlier evaluation.