# CHATGPT PROMPT #
<br>
<br>

# ECAS Chunk 5 — Comparison-Method Investigation and Long-Term Atmospheric Retrieval Strategy

**Mode: PLAN only. No implementation, code changes, or documentation edits.**

## 1. Objective

Investigate established scientific methods for comparing exoplanet observational spectra with molecular reference data, and determine how ECAS should develop from its current capabilities toward its long-term goal: **evidence-based, uncertainty-aware characterization of exoplanet atmospheres using physical modelling and statistical inference.**

This investigation must distinguish between:

- What ECAS can scientifically and technically support now.
- What should be implemented as foundational comparison functionality.
- What additional capabilities and validation are required for increasingly sophisticated analysis.
- The eventual atmospheric characterization system ECAS is intended to become.

Do not reduce the project to wavelength matching, spectral overlays, or a similarity score. These can be useful foundational tools, but they are not the final scientific objective.

## 2. Establish the existing project state first

Inspect the current repository, implementation, authoritative documentation, and relevant historical plans before recommending changes.

At minimum, inspect:

- `docs/ECAS.md`
- `docs/brains/PROJECT_STATE.md`
- `docs/brains/DECISIONS.md`
- `docs/architecture/VALIDATION_STRATEGY.md`
- Relevant architecture, data-flow, and data-model documents.
- Existing Chunk 4 plans, implementation records, and decisions.
- Any existing spectral comparison, data compatibility, uncertainty, or molecular reference functionality.

Verify paths and current contents. Distinguish implemented functionality from proposed architecture and future goals.

Identify dependencies on unfinished Chunk 4 work. Do not assume the current CSV import implementation supports every scientific data format ECAS will eventually need.

## 3. Long-term scientific objective

ECAS should ultimately help characterize exoplanet atmospheres by evaluating which atmospheric compositions and physical conditions best explain available observations, including multiple observations of the same planet.

The intended scientific framework should be investigated in terms of:

### A. Physical forward modelling

Investigate models that predict observable spectra from atmospheric properties, potentially including:

- Molecular composition and abundances.
- Temperature and pressure structures.
- Relevant radiative-transfer physics and opacity data.
- Planetary and observational parameters where relevant.
- Instrumental response and observation-specific effects.

Determine which inputs are necessary, which can be constrained by observations, which require external information, and which must remain uncertain.

### B. Statistical inference and atmospheric retrieval

Investigate established retrieval approaches that infer plausible atmospheric properties from observed spectra by comparing observations against physically generated model predictions.

Consider Bayesian inference and other scientifically appropriate statistical approaches where relevant. Explain how likelihoods, prior assumptions, parameter uncertainties, model degeneracies, and competing atmospheric explanations affect the interpretation.

ECAS must not require the user to know the correct atmospheric composition in advance. Investigate how candidate molecules and uncertain parameters can be explored systematically without pretending that every atmosphere can be uniquely recovered from the available data.

### C. Multiple observations

Investigate how observations of the same planet from different dates, instruments, wavelength ranges, and publications could contribute to a shared atmospheric analysis.

Account for differences in calibration, resolution, noise, uncertainties, and observational conditions. Determine when observations can be combined, when they should be modelled separately, and how inconsistencies should be handled.

### D. Evidence and uncertainty

The eventual system must distinguish between:

- A spectral feature that overlaps a molecular reference feature.
- Evidence that a candidate molecule may contribute to an observation.
- Statistical support for a particular atmospheric model or molecular abundance.
- A defensible atmospheric inference with quantified uncertainty and acknowledged limitations.

Spectral overlap alone must never be presented as proof of molecular presence. Results must communicate uncertainty, alternative explanations, data limitations, and the assumptions on which conclusions depend.

## 4. Investigate the comparison methods that lead toward this objective

Compare established approaches, including:

1. Direct spectral overlays and visual inspection.
2. Wavelength- or wavenumber-aligned feature comparisons.
3. Resolution-aware comparison, including appropriate treatment of instrumental response.
4. Similarity metrics and residual analysis.
5. Statistical comparison of observations against model-generated spectra.
6. Likelihood-based inference and atmospheric retrieval, where supported by the literature.

For each approach, explain:

- Its scientific purpose and appropriate use.
- Required inputs and assumptions.
- Strengths, limitations, and common failure modes.
- How it handles noise, uncertainty, spectral resolution, and overlapping molecular signatures.
- Whether it is appropriate for an initial ECAS capability or requires more advanced infrastructure.
- How it could contribute to, or mislead, eventual atmospheric characterization.

Do not assume that one metric or method can solve the entire problem. Investigate how the methods can complement one another within a coherent scientific workflow.

## 5. Determine a realistic staged development path

Recommend a scientifically defensible progression from current ECAS capabilities to the long-term goal.

Consider, but do not automatically prescribe, stages such as:

- **Foundation:** Reliable spectral data handling, metadata, provenance, units, compatibility checks, and visualization.
- **Initial comparison:** Transparent overlays, aligned spectral features, and clearly qualified comparison results.
- **Quantitative comparison:** Appropriate uncertainty handling, resolution-aware methods, residual analysis, and validated statistical measures.
- **Forward modelling:** Physical generation of spectra under defined atmospheric assumptions.
- **Atmospheric retrieval:** Statistical exploration of atmospheric compositions and physical parameters, with uncertainty estimates.
- **Multi-observation characterization:** Joint or otherwise scientifically justified analysis of observations of the same planet, accounting for their differences.

Adjust these stages to the verified project state and scientific evidence. Identify prerequisites, dependencies, validation requirements, and sensible stopping points.

Do not implement these stages in this task. Do not commit ECAS to a particular algorithm, retrieval framework, or dependency without evaluating alternatives and explaining the rationale.

## 6. Scientific literature and validation

Use credible scientific publications and authoritative technical documentation to support methodological recommendations.

Where relevant, investigate established atmospheric retrieval tools and published validation approaches to determine what ECAS can learn from existing practice rather than unnecessarily reinventing methods.

Distinguish clearly between:

- Established scientific methods.
- Evidence supporting their use.
- Limitations identified in the literature.
- Recommendations specific to ECAS.
- Questions that remain unresolved.

Identify how future implementations could be validated using appropriate reference cases, synthetic observations, known limitations, and well-studied planets where suitable data are available.

Do not invent sources, test results, scientific certainty, or validation outcomes.

## 7. Scope boundaries

- PLAN mode only.
- Do not edit files, implement code, install dependencies, or run application tests.
- Do not turn this investigation into a full atmospheric retrieval implementation plan before the comparison-method investigation is complete.
- Do not assume all required observational data, molecular parameters, or planetary constraints will be available.
- Do not treat missing physical parameters as values that can simply be guessed.
- Do not confuse a model's best fit with proof that its inferred atmosphere is uniquely correct.
- Do not duplicate existing documentation or contradict established decisions without identifying the conflict.
- Preserve the distinction between the current implementation, approved decisions, provisional proposals, and the long-term scientific vision.

## 8. Use the Existing WASP-39 b Dataset as a Practical Example

Investigate whether the existing WASP-39 b dataset can serve as the initial practical example for developing and evaluating ECAS's spectral-comparison methods.

### 8.1 Inspect the Existing Dataset and Integration

- Locate the existing CSV dataset under `data/wasp39b/`.
- Inspect its schema, columns, units, wavelength coverage, measurement values, uncertainties, and metadata where available.
- Determine how this dataset is currently loaded, processed, stored, and passed through the backend.
- Inspect the existing code and tests to establish whether ECAS can already access the dataset's spectral data points and display or otherwise use them in the program.
- Identify which parts of this workflow are already functional and which depend on the unfinished Chunk 4 work being handled by the other contributor.
- Do not assume the dataset is a complete, physically calibrated spectrum or that every column has the meaning its name might suggest. Establish what can be supported by the actual data and its provenance.

### 8.2 Determine What We Can Test with It Now

Assess whether the existing dataset is suitable for an initial, limited investigation of spectral-comparison methods, such as:

- Inspecting and plotting the available spectral measurements.
- Understanding the dataset's wavelength or spectral-coordinate representation and associated uncertainties.
- Exploring how spectral features could be identified and compared.
- Testing basic wavelength alignment, interpolation, residuals, or similarity measures where scientifically appropriate.
- Establishing how data quality, spectral resolution, wavelength coverage, and uncertainty should affect comparisons.
- Identifying which additional reference spectra, metadata, or physical models would be required before meaningful molecular attribution could be attempted.

Distinguish clearly between methods that could be investigated using the existing dataset alone and methods that require additional reference data, metadata, or forward models.

### 8.3 Treat WASP-39 b as a Development Example, Not a Scientific Conclusion

Use the dataset as a practical starting point for building and validating ECAS's comparison workflow. Do not treat an apparent overlap between spectral features as sufficient evidence that a molecule is present.

Explain what the dataset can legitimately demonstrate, what it cannot establish on its own, and how its limitations should influence the proposed development stages. In particular, distinguish exploratory visual comparisons from quantitative, uncertainty-aware comparisons and eventual model-based atmospheric retrieval.

Do not assume the dataset alone can establish atmospheric composition, molecular abundance, temperature, pressure, or other atmospheric parameters.

### 8.4 Avoid Conflicts with the Ongoing Chunk 4 Work

Because another contributor may currently be implementing Chunk 4, inspect the repository's actual state before proposing any follow-up work.

- Identify which existing dataset-loading, backend, plotting, and data-access capabilities can already be relied upon.
- Flag any relevant functionality that appears incomplete or is currently being changed as part of Chunk 4.
- Do not recommend duplicating or redesigning functionality that is already implemented or actively being developed.
- If the dataset cannot yet be accessed reliably because Chunk 4 work is incomplete, explain the specific dependency and recommend waiting for that work to be completed and verified before building on it.
- If the current integration is sufficient for limited investigation, identify the smallest safe next step that uses it without interfering with the other contributor's work.

### 8.5 Required Findings

Include the following in the final planning report:

1. The dataset's actual structure, provenance, and known limitations.
2. The verified status of its existing integration into ECAS.
3. Which comparison-method investigations are feasible immediately.
4. Which investigations depend on Chunk 4 completion or additional data.
5. The smallest practical next step for using WASP-39 b as an initial development example.
6. How the example fits into the longer-term goal of uncertainty-aware, model-based atmospheric characterization.

This section is investigative and planning-only. Do not modify code or documentation, install dependencies, run implementation tasks, or interfere with the ongoing Chunk 4 work. Report findings and await approval before proceeding.

## 9. Required deliverables

Produce a structured investigation report containing:

1. **Verified current state:** Existing comparison capabilities, relevant decisions, and outstanding dependencies.
2. **Scientific method review:** Candidate methods, trade-offs, assumptions, and supporting literature.
3. **Long-term retrieval framework:** What atmospheric retrieval would require and how it differs from simple spectral matching.
4. **Staged roadmap:** Recommended development sequence, prerequisites, and validation requirements.
5. **Multi-observation strategy:** How observations could contribute to a common atmospheric characterization while accounting for differences.
6. **Scientific limitations:** Identifiability, model degeneracies, missing parameters, uncertainty, and risks of overinterpretation.
7. **Decision points:** Questions ECAS must resolve before selecting specific algorithms or dependencies.
8. **Documentation recommendations:** Which existing authoritative documents would eventually need targeted updates, without editing them now.
9. **Chunk 5 acceptance criteria:** Observable conditions for considering the investigation complete, distinct from implementation acceptance criteria.

Conclude with a justified recommendation for the next smallest development task. Explain what it would establish, what it would deliberately leave for later, and how it advances ECAS toward atmospheric characterization.

**Stop after presenting the report. Await review and approval before any implementation or documentation changes.**