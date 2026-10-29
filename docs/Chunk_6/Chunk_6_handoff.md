# ECAS — Chunk 6: Scientific Comparison, Interpretation, and Projections

## 1. Project identity and objective

You are working on **ECAS — Exoplanetary Characterization & Astrochemistry Suite**, a Python desktop application for exoplanetary spectroscopy and atmospheric characterization.

Repository: https://github.com/brettadin/ECAS_BETA

Your task is to lead the development of **Chunk 6 — Scientific Comparison, Interpretation, and Projections**.

This is one of the most scientifically consequential parts of ECAS. Correctness, transparency, reproducibility, maintainability, and scientific defensibility take priority over feature count, visual polish, impressive-looking results, or passing tests.

The objective is not simply to make two spectra overlap or produce a numerical ranking. The objective is to establish a reliable workflow that lets a user compare eligible observational or input spectra with appropriate molecular reference datasets, understand what the results actually demonstrate, investigate candidate agreement, and reproduce the analysis.

Do not fabricate results, relax scientific requirements to make a feature work, invent missing physical parameters, or modify tests to conceal defects.

## 2. How you should work

Work as a technical and scientific development partner. Take responsibility for investigating the problem, developing a plan, examining alternatives, identifying risks, and refining the approach before implementation.

Use this workflow:

1. Inspect the current repository, implementation, development plan, decisions, architecture documentation, and relevant Chunk 5 and Chunk 5.1 records.
2. Establish the verified current state and identify unresolved scientific, mathematical, architectural, and integration questions.
3. Develop an initial plan for Chunk 6, including alternative approaches and their trade-offs.
4. Critically review and refine your own plan. Look for unsupported assumptions, missing compatibility requirements, scientific overclaims, unnecessary complexity, and untested failure modes.
5. Divide the work into small, independently reviewable stages with explicit completion criteria.
6. Present the initial investigation and refined plan for review before making implementation changes.
7. After the plan is reviewed and approved, implement one bounded stage at a time, test it, inspect the resulting changes, and update documentation.
8. Continue to the next stage when the preceding stage's requirements are met. Do not repeatedly ask for permission for routine, already-approved work.
9. Ask for human input only when a genuine scientific decision, material ambiguity, scope change, or other blocker cannot be resolved from available evidence. Explain the alternatives and consequences clearly.

Do not implement anything during the initial investigation and planning response.

Avoid repetitive repository-wide investigations, unnecessary abstractions, large batches of unrelated changes, and repeated requests for information already available in the repository.

If you discover a problem outside the current stage, record it and defer it unless it blocks the approved work.

## 3. Establish the actual starting point

Read the current versions of the following documents, verifying their paths and authority in the repository:

- `docs/ECAS_development_plan.md`
- `docs/ECAS.md`
- `docs/brains/PROJECT_STATE.md`
- `docs/brains/DECISIONS.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/DATA_FLOW.md`
- `docs/architecture/DATA_MODELS.md`
- `docs/architecture/ECAS_Architecture_Specification.md`
- `docs/architecture/MODULE_RESPONSIBILITIES.md`
- `docs/architecture/VALIDATION_STRATEGY.md`
- `docs/Chunk_5/INITIAL_METHOD_DECISION.md`
- `docs/Chunk_5/ELIGIBILITY_CONTRACT_V1.md`
- `docs/Chunk_5/COMPARISON_INPUT_CONTRACT_DRAFT.md`
- `docs/Chunk_5/COMPARISON_READINESS_20261028.md`
- `docs/Chunk_5/IMPLEMENTATION_LOG.md`
- `docs/Chunk_5/MODEL_COMPARISON_PROTOTYPE.md`
- `docs/Chunk_5/RESPONSE_AND_UNCERTAINTY_EXPERIMENT.md`
- `docs/Chunk_5_1/PROVIDER_INVESTIGATION.md`
- `docs/Chunk_5_1/CATALOGUE_IMPLEMENTATION.md`
- `docs/Chunk_5_1/REFERENCE_BROWSER_IMPLEMENTATION.md`
- `docs/Chunk_5_1/PRODUCT_RETRIEVAL_IMPLEMENTATION.md`

Read the relevant implementation, tests, schemas, fixtures, and supporting verification records referenced by these documents. Follow actual imports, callers, and data flows rather than assuming the documented architecture is already implemented.

Do not restrict your investigation to these filenames if additional relevant files exist.

Establish:

- Which Chunk 5 decisions have been made and reviewed.
- Which Chunk 5 requirements are implemented, tested, and integrated into the application.
- Which Chunk 5.1 capabilities are implemented and which remain pending.
- How observational spectra and molecular reference datasets are currently represented, selected, loaded, and persisted.
- Whether source identity, hashes, provenance, units, coordinate frames, uncertainty, response information, and reference conditions survive the entire workflow.
- Which research prototypes are disconnected from production code.
- Which known limitations, incomplete tasks, or documentation conflicts affect Chunk 6.

Distinguish verified facts from claims in documentation, proposed designs, assumptions, and unresolved questions. Do not silently mark Chunk 5 or Chunk 5.1 complete merely because the development plan contains successful test counts.

Use the supplied ZIP as a snapshot, not proof of the current working-tree state. If repository access is available, compare it with the current repository. If not, identify the snapshot date and the limitations of your evidence.

## 4. Preserve the selected comparison method

The existing initial method decision is the starting point:

**Observable-compatible spectral overlay with explicit response handling and residual inspection.**

The intended initial workflow is deliberately conservative:

- Preserve and display original input curves.
- Validate whether the selected inputs represent compatible observables and whether their units, coordinate systems, coverage, and spectral responses permit the requested operation.
- Handle spectral support, resolution, sampling, and binning explicitly.
- Produce comparison overlays and residuals without silently fitting away differences.
- Provide weighted residual diagnostics only when their uncertainty and covariance requirements are justified.
- Report compatibility failures, missing information, exclusions, assumptions, and relevant limitations.
- Distinguish numerical agreement from model adequacy, statistical significance, molecular identification, and atmospheric composition.

Do not replace this method with correlation, peak matching, arbitrary similarity percentages, unconstrained curve fitting, or atmospheric retrieval merely because those alternatives are easier to implement or produce more attractive results.

The existing research prototypes investigate more advanced methods, but a research prototype is not automatically an approved production method.

If repository evidence reveals that the selected method needs to change, explain the evidence, alternatives, consequences, and necessary validation. Document the proposed deviation and obtain review before expanding the method.

## 5. Scientific and mathematical requirements

Develop a complete scientific specification for the comparison workflow.

### A. Input compatibility

Determine the exact requirements for each supported comparison operation.

Consider, as applicable:

- Dataset role and observable type.
- Wavelength or wavenumber coordinates, units, and reference frame.
- Signal units and physical meaning.
- Spectral range and common support.
- Sampling, bin edges, spectral resolution, line-spread function, and instrument response.
- Uncertainty representation, error conventions, and covariance.
- Data quality, missing values, invalid coordinates, and incomplete coverage.
- Reference measurement conditions and physical parameters.
- Whether a reference is an observed spectrum, theoretical line list, cross section, opacity product, or synthesized spectrum.
- Whether a physical model is required to produce a comparable observable.

Missing metadata must not be interpreted as evidence that two datasets are compatible.

Preserve the ability to inspect raw data when quantitative comparison is not justified. Explain which requirements prevent a particular operation instead of silently rejecting all inspection or inventing missing metadata.

Do not assume that a molecular cross section, line list, or zero-pressure reference spectrum is directly comparable with an exoplanet transmission spectrum.

### B. Alignment and response handling

Investigate the mathematical and physical requirements for aligning eligible inputs.

Define when unit conversion, response matching, spectral convolution, bin integration, and grid alignment are permitted.

Avoid:

- Silent extrapolation or clipping.
- Treating interpolation as the creation of new physical information.
- Upsampling observations to manufacture higher resolution.
- Treating identical numerical coordinates as proof of physical compatibility.
- Ignoring instrument-response differences.
- Discarding excluded points without recording them.

Specify how the application will preserve original values and identify every transformation applied.

If an operation cannot be justified from available metadata, stop that operation and explain the limitation.

### C. Residuals and uncertainty

Define the residual convention, such as observed minus reference, and use it consistently.

Specify the mathematical basis for every quantitative diagnostic. Where applicable, document:

- Residual arrays and their units.
- Unweighted residual summaries.
- Conditions required for uncertainty-weighted residuals.
- Covariance construction and independence assumptions.
- Positive-definiteness requirements.
- Handling of asymmetric uncertainties.
- Missing, zero, invalid, or incomplete uncertainty information.
- Numerical stability and failure behavior.
- The distinction between a descriptive residual diagnostic and a statistically calibrated significance measure.

Do not assign arbitrary weights to missing errors. Do not assume independent errors merely because a covariance matrix is unavailable. Do not silently substitute a pseudoinverse or fallback statistical model when required conditions fail.

If a statistic is not meaningful for the selected inputs, do not calculate or display it as though it were.

### D. Multiple molecular candidates

Design a workflow that can compare one selected input against multiple eligible reference datasets where the supported method permits it.

Allow users to inspect individual candidates, their overlays, residuals, compatibility results, and limitations.

Establish fair comparison rules. Candidates must not be ranked using different spectral ranges, response conventions, uncertainties, preprocessing choices, or effective fitting freedoms without making the differences explicit and scientifically justified.

A best numerical match is not necessarily the correct molecular explanation. Multiple molecules can have overlapping features, and an incomplete reference set can produce misleading apparent rankings.

Distinguish:

- A candidate that is numerically closer under a defined diagnostic.
- A candidate that provides an adequate description of the data.
- A candidate whose agreement is statistically meaningful under a validated procedure.
- Evidence that supports a physical or atmospheric interpretation.

Do not treat these as interchangeable conclusions.

### E. Projections and atmospheric interpretation

Treat projections as a separate, staged capability rather than an automatic extension of an overlay.

Investigate which outputs can be justified using the existing inputs and method. These may include aligned reference overlays, expected spectral features, residual visualizations, or other explicitly defined diagnostics.

Any forward model, combined-spectrum projection, abundance estimate, or atmospheric interpretation requiring additional physical assumptions must have its model, parameters, data sources, uncertainties, and validation requirements specified before implementation.

Do not rescale an arbitrary molecular reference spectrum and present it as a physical atmospheric model.

Do not estimate molecular abundance or claim atmospheric composition from visual overlap, residual size, or a ranking score alone.

If a scientifically defensible projection requires capabilities outside the current scope, define the dependency and defer it rather than implementing a misleading approximation.

## 6. Reproducibility and data provenance

Design the result record so that a user can understand and reproduce an analysis within clearly stated limits.

Determine how to retain:

- Input dataset identities and versions.
- Source provenance and relevant file or content hashes.
- Reference dataset identity, provider, product identifiers, and retrieval metadata.
- Original data identity and transformations.
- Selected comparison method and method version.
- Compatibility results and reasons.
- Coordinate conversions, alignment, binning, and response settings.
- Uncertainty and covariance assumptions.
- Included and excluded measurements and their reasons.
- Diagnostic outputs and any relevant numerical parameters.
- Software and dependency versions where needed.
- Physical-model assumptions and parameter values, if a model is used.
- Limitations that prevent exact reproduction.

Inspect the existing persistence architecture before proposing changes. Avoid unnecessary schema migrations or duplicate storage mechanisms.

If exact reproduction cannot be guaranteed because source data, software, or metadata are unavailable, state that limitation explicitly. Never claim reproducibility solely because a result has been saved.

## 7. Required scientific methodology document

Create a standalone document under `docs/` with the proposed filename:

`docs/SCIENTIFIC_COMPARISON_AND_INTERPRETATION.md`

Verify that this filename does not duplicate an existing authoritative document before creating it.

This document must eventually describe the comparison methodology from five complementary perspectives:

1. **Scientific and physical:** What the inputs represent, what physical processes are relevant, when two spectra are comparable, and which conclusions the evidence can support.
2. **Mathematical and statistical:** Equations, definitions, units, transformations, residual conventions, uncertainty treatment, assumptions, diagnostic interpretation, and failure conditions.
3. **Chemical:** Molecular identities, isotopologues where relevant, reference-data conditions, spectral-feature overlap, cross sections or line lists, and the limitations of assigning features to particular molecules.
4. **Software and implementation:** Data structures, eligibility contracts, processing steps, validation, interfaces, persistence, error handling, provenance, and the relationship between mathematical definitions and code.
5. **Logical and inferential:** What follows from the analysis, what does not follow, how ambiguity is communicated, how candidate comparisons are interpreted, and which additional evidence would be required for stronger conclusions.

The document must contain enough detail for another developer or scientifically literate reviewer to understand and independently assess how the comparison works.

Include explicit equations and definitions where appropriate, a clearly ordered processing workflow, assumptions and preconditions, failure cases, worked examples where useful, validation evidence, known limitations, and references to relevant implementation modules and tests.

Do not invent equations or physical assumptions merely to make the document look comprehensive. Explain the basis and applicability of each method.

Maintain a clear distinction between:

- Planned methodology.
- Implemented behavior.
- Behavior verified by tests.
- Behavior validated against appropriate scientific evidence.
- Deferred or unsupported capabilities.

Update the document as implementation evolves. It must remain consistent with the code, tests, decisions, and project state.

The standalone document is a required deliverable, not a substitute for tests or correct implementation.

## 8. Verification and scientific integrity

Develop a validation strategy before implementing the corresponding production behavior.

Include tests for:

- Known compatible inputs.
- Known incompatible observables and units.
- Missing or contradictory metadata.
- Unit conversion and coordinate-frame differences.
- Identical and differing sampling grids.
- Different spectral resolutions and responses.
- Partial overlap and no overlap.
- Noisy and incomplete measurements.
- Missing, invalid, asymmetric, and correlated uncertainties.
- Invalid covariance matrices and numerical failures.
- Overlapping molecular features and ambiguous candidate rankings.
- References that require a physical-model step.
- Incorrect or missing provenance.
- Repeated runs and reproducibility.
- Failures during selection, loading, comparison, and persistence.
- Protection against presenting unsupported abundance estimates or atmospheric composition claims.

Use analytic checks, independently calculated expected results, carefully documented synthetic fixtures, and real reference data where justified.

Synthetic fixtures must be labelled as synthetic. They may verify implementation under known conditions but cannot establish real-world scientific validity.

Use real observational data for empirical validation only when the necessary inputs and metadata are available and suitable. If such validation is unavailable or deferred, record the limitation; do not fabricate a substitute or claim that empirical validity has been established.

Tests must verify scientific behavior, not merely that functions execute or that expected text appears in the interface.

## 9. Development and documentation discipline

Work in small, controlled increments.

For each approved stage:

1. State the objective and bounded scope.
2. Identify the relevant existing implementation and decisions.
3. Explain the intended scientific and technical behavior.
4. Define acceptance criteria and focused tests.
5. Implement only the approved change.
6. Run the relevant tests and record actual results.
7. Inspect the changed code and test for regressions.
8. Update the relevant documentation and progress record.
9. Report completed work, remaining limitations, and the next logical stage.

Update `docs/brains/PROJECT_STATE.md` only when verified implementation status changes.

Update `docs/brains/DECISIONS.md` when a material design or scientific decision is approved.

Update `docs/ECAS_development_plan.md` and relevant Chunk 6 progress records as work advances.

Keep `docs/SCIENTIFIC_COMPARISON_AND_INTERPRETATION.md` synchronized with actual behavior.

Create a clear Chunk 6 progress record using the existing documentation conventions. Inspect the current organization first so that you do not create duplicate or conflicting planning histories.

Do not rewrite historical records to make the project appear more complete.

The user will handle manual GitHub commits and pushes. Do not make pushing or committing a requirement of your workflow.

## 10. Initial response required

For your first response, perform the repository and documentation investigation only. Do not edit or create files and do not implement code.

Return a structured report containing:

**A. Verified starting state**
- What Chunk 5 established.
- What Chunk 5.1 established.
- What is actually implemented and integrated.
- What remains incomplete or unverified.
- Relevant tests and existing validation evidence.
- Any discrepancies between the development plan, decisions, documentation, and code.

**B. Scientific and technical gap analysis**
- What must exist before a defensible comparison can run.
- Which requirements can be implemented using the existing architecture.
- Which require additional decisions, metadata, data models, or physical inputs.
- Which projections are currently supportable and which must be deferred.

**C. Proposed comparison architecture**
Describe the end-to-end data flow, component responsibilities, validation boundaries, mathematical processing, result representation, persistence, and user-facing interpretation. Reuse existing architecture where appropriate rather than introducing unnecessary new systems.

**D. Alternative approaches and trade-offs**
Identify credible alternatives where a decision is genuinely open. Explain their scientific validity, assumptions, limitations, complexity, and testing requirements. Recommend a preferred approach with evidence.

**E. Staged Chunk 6 plan**
Break the work into small, ordered stages. Each stage must have:
- Objective.
- Prerequisites.
- Relevant files or modules.
- Intended changes.
- Scientific and mathematical requirements.
- Tests and verification.
- Documentation updates.
- Acceptance criteria.
- Explicit out-of-scope items.

**F. Standalone scientific methodology document**
Propose its detailed outline and explain how its content will remain consistent with the implementation.

**G. Unresolved decisions and blockers**
Separate decisions that genuinely require human input from questions that can be answered by further investigation. Recommend concrete resolutions wherever possible.

**H. Recommended next step**
Identify the smallest valuable next task and provide the rationale.

Do not begin implementation in this first response. The objective is to establish an evidence-based plan that can be reviewed and refined before coding starts.

## 11. Final operating principle

The goal is a scientifically defensible analysis tool, not a system that always produces a match, score, projection, or answer.

When the evidence is insufficient, ECAS must say so.

When two datasets cannot be compared reliably, it must explain why.

When a numerical match is ambiguous, it must preserve that ambiguity.

When a physical interpretation requires assumptions that have not been established, it must not present that interpretation as a scientific result.

Prefer a narrower, transparent, validated method over a broader but misleading one.