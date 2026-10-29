# ECAS v1 and Beta Comparison — Category 3
## Scientific and Numerical Implementation

**Scope:** Compare the scientific calculations, numerical methods, assumptions, uncertainty handling, and validation boundaries of ECAS v1 and ECAS Beta.

**Evidence basis:** The supplied source archives and findings from the respective seven-pass reviews. This assessment does not claim fresh execution of the scientific calculations, reproduction of numerical concerns, or independent validation against observational data.

---

## 1. Executive Assessment

ECAS v1 already contains meaningful scientific computation. Its reviewed capabilities include spectral feature identification, gas-multiplier fitting, transit-depth extraction, transit-model analysis, and optional atmospheric forward modeling through petitRADTRANS. These workflows have documented assumptions and limitations, particularly around atmospheric-model simplifications, instrument response, and uncertainty treatment.

Beta develops a more explicit framework for scientific comparison. Its `ComparisonInput` structure records source identity, hashes, roles, observable types, units, coordinate frames, response metadata, measurements, and uncertainties. Dedicated modules implement eligibility checks, spectral alignment, residual diagnostics, and a native transmission forward model.

The key advancement is that Beta makes more of the conditions required for comparing scientific datasets explicit in the software. It introduces more structured checks around compatibility, alignment, uncertainty assumptions, and model interpretation.

However, **Beta's additional numerical infrastructure does not establish that its results are scientifically more accurate than v1's results.** The models have different implementations and assumptions, and several numerical edge cases identified during the review still require targeted verification. Neither review establishes comprehensive end-to-end empirical validation.

## 2. Side-by-Side Scientific Capability Matrix

| Scientific area | ECAS v1 | ECAS Beta | Comparative assessment |
|---|---|---|---|
| Spectral feature identification | Identifies absorption features and matches them against known bands within supported workflows. | Provides structured molecular-reference access and comparison-preparation capabilities; equivalent production molecular-detection performance is not established. | V1 has an explicit integrated feature-identification workflow. Beta improves the supporting reference-data and comparison infrastructure. |
| Gas fitting | Fits gas multipliers against configured model spectra and can fit continuum level and tilt over supported coverage. | Contains comparison and forward-model components, but an equivalent general-purpose fitting workflow was not established in the review. | V1 retains a documented fitting capability; Beta's new model-generation code should not be treated as equivalent to a completed fitting or retrieval system. |
| Transit-depth extraction | Extracts wavelength-dependent transit depths from suitable JWST spectral time series, subject to data and workflow constraints. | The reviewed comparison framework handles supported transit-depth representations, units, and alignment, but equivalent integrated time-series extraction was not established. | V1 provides a more explicit integrated extraction workflow. Beta adds downstream comparison safeguards. |
| Spectral coordinate handling | Supports wavelength/wavenumber interpretation and spectral workflows with documented conversion and coverage limitations. | Explicit unit conversion, including wavenumber-to-micrometer conversion with reversed ordering and corresponding covariance permutation. | Beta's alignment pipeline makes coordinate transformations and their data-ordering consequences more explicit. |
| Measurement compatibility | Analysis behavior depends on the measurement type and workflow, including restrictions on emission-flux and transmission-like inputs. | Eligibility checks require supported roles and observables, explicit units, coordinate frame and response metadata, source hash, finite points, and increasing coordinates. | Beta introduces a more explicit gate before comparison. Passing eligibility checks is not proof that two datasets are physically equivalent. |
| Spectral alignment | Supports the transformations needed by its existing spectroscopy and modeling workflows. | Implements selected transit-depth conversions and response-aware top-hat bin integration without extrapolation. | Beta has a more explicit comparison-specific alignment layer. Its supported transformations remain bounded by implementation. |
| Atmospheric forward model | Optional petitRADTRANS 3 clear-atmosphere model, with documented physical and instrument-related limitations. | Native one-dimensional isothermal hydrostatic transmission model with molecular absorption, background continuum contributions, and optional gray clouds. | Both implement model-based calculations. Neither can be declared more accurate without comparable validation and clearly matched assumptions. |
| Atmospheric parameter exploration | Conditional one-dimensional gas-abundance profile scan in the documented v1 workflow. | Leave-one-out model sensitivity diagnostics under specified model assumptions. | Both support restricted parameter/model exploration, but these operations are not equivalent to a full atmospheric retrieval. |
| Residual analysis | Residual and χ² diagnostics are available in the optional model-overlay workflow, alongside other diagnostics such as time-correlated-noise assessment. | Unweighted residual summaries and weighted diagnostics using Cholesky-whitened residuals and a quadratic statistic, where assumptions are satisfied. | Beta provides a more explicit weighted-residual pathway. Its statistic is not automatically calibrated statistical evidence. |
| Uncertainty handling | Supports transit-depth uncertainties and optional inverse-variance channel binning; the documented model workflows have limitations in noise treatment. | Requires explicit uncertainty and independence assumptions for weighted diagnostics; alignment includes covariance permutation for supported coordinate reversal. | Beta more explicitly represents some assumptions and transformations. Complete covariance modeling and empirically calibrated uncertainties are not established. |
| Molecular cross sections | Uses configured model spectra and gas data in its supported fitting/modeling workflows. | Supports selected molecular-reference products and cross-section-based model generation, with source and configuration metadata. | Beta improves reference-data management and integration into model preparation. Reference availability does not guarantee model suitability or physical correctness. |
| External scientific models | Documents optional petitRADTRANS integration for a defined modeling workflow. | Defines JSON model-import/provenance boundaries for petitRADTRANS, POSEIDON, TauREx 3, PLATON, and Pyrat Bay. | Beta's adapter definitions broaden the intended integration surface. Live integration with every named model was not verified. |
| Numerical validation | The v1 review identified possible numerical concerns, including covariance scaling, requiring synthetic reproduction. | The Beta review identified cross-section input-validation and parameter-validation concerns requiring targeted checks. | Both have unresolved numerical verification needs. The evidence does not establish that one version is numerically defect-free. |
| Empirical scientific validation | Not established end-to-end by the review. | Not established end-to-end by the review. | Neither version should be described as empirically validated across the complete research workflow on this evidence. |

## 3. Detailed Comparison

### 3.1 Scientific inputs and compatibility

**V1 baseline**

V1's scientific workflows operate on imported spectra, configured gas reference data, transit measurements, and atmospheric model outputs. The interpretation of those inputs depends on their units, observable type, spectral coverage, and suitability for the chosen workflow.

The v1 review identified limitations in the breadth of the atmospheric model and the handling of provenance and reproducibility. It also flagged a possible covariance-scaling issue in `app/core/fitting.py`, around lines 327–347, that requires a synthetic reproduction before it can be classified as a defect.

**Beta state**

Beta uses a more explicit comparison input structure, `ComparisonInput`, with fields for:

- Source identity and source hash.
- Scientific role and observable type.
- Units and coordinate frame.
- Response metadata.
- Measurements and uncertainties.

Eligibility checks cover supported roles and observables, explicit units, coordinate and response metadata, source hash, at least three finite points, and increasing coordinates. Certain weighted diagnostics require explicit uncertainty and independence assumptions.

**Assessment**

Beta's approach is a significant structural improvement for scientific comparison because it makes input assumptions visible and testable before calculations proceed.

However, metadata completeness is not the same as scientific compatibility. Two datasets can have valid units and increasing wavelength coordinates while still differing in calibration, instrumental response, physical observable, or uncertainty structure. Those differences must be addressed by the relevant scientific workflow rather than inferred from eligibility alone.

### 3.2 Spectral alignment and numerical transformations

**V1 baseline**

V1 supports wavelength and wavenumber interpretation in its existing import and spectroscopy workflows. Its comparison and model calculations remain subject to their documented coverage, scaling, and modeling assumptions.

**Beta state**

Beta implements explicit alignment behavior, including:

- Selected conversions between fractional and percentage transit-depth representations.
- Wavelength-unit conversion.
- Wavenumber-to-micrometer conversion.
- Reversal of spectral ordering where required by the coordinate transformation.
- Corresponding covariance permutation when the data order changes.
- Top-hat bin integration without extrapolation beyond supported model coverage.

**Assessment**

These are meaningful numerical safeguards. A coordinate transformation must preserve the correspondence between measurements, uncertainties, and covariance entries. Reversing the spectral order without also transforming associated arrays would produce incorrect comparisons even if the plotted coordinates looked reasonable.

Beta's explicit covariance permutation addresses this class of ordering problem for the supported transformation. It does not establish that every possible transformation, response function, or covariance convention is supported.

The no-extrapolation behavior also establishes a useful boundary: the alignment layer should not silently invent model values outside the available spectral domain.

### 3.3 Atmospheric forward modeling

**V1 implementation**

The reviewed v1 workflow optionally uses petitRADTRANS 3 for a clear-atmosphere transmission spectrum. The review describes a restricted one-dimensional gas-abundance profile scan and documents important limitations, including:

- No complete marginalization over atmospheric parameters.
- No instrument line-spread convolution in the described workflow.
- No correlated-noise likelihood treatment.
- Dependence on the assumptions and configuration of the optional modeling backend.

These limitations restrict the interpretation of generated spectra and fitted parameters.

**Beta implementation**

Beta's `model_generator.py` implements a native one-dimensional isothermal hydrostatic transmission model. Its reviewed components include:

- Spherical-shell chord integration.
- Molecular absorption.
- An H₂/He background with Rayleigh-like continuum contributions.
- Optional gray-cloud treatment.
- Uniform molecular mixing ratios.
- Leave-one-out model sensitivity diagnostics.

The model operates under restricted physical assumptions. The review also identified a reference-temperature mismatch warning that does not correct the cross section itself.

**Assessment**

Beta adds a native model implementation and brings model generation closer to the comparison workflow. That is an architectural and functional advancement.

It does not follow that Beta's model is more physically complete than petitRADTRANS or that its outputs are more accurate. Differences in atmospheric assumptions, cross-section handling, numerical resolution, pressure-temperature structure, clouds, and instrumental response can materially affect generated spectra.

A reference-temperature warning is useful, but a warning alone does not correct a temperature-dependent molecular cross section. That mismatch remains a scientific limitation unless the relevant input is corrected or the calculation explicitly accounts for it.

The appropriate comparison is therefore between the assumptions, numerical methods, and validated outputs of the two model pathways—not merely whether each can generate a spectrum.

### 3.4 Residual diagnostics and statistical interpretation

**V1 baseline**

V1 provides residual and χ² diagnostics within its model-overlay workflow, as well as a time-correlated-noise diagnostic. The review does not establish that the complete workflow uses a general covariance-aware likelihood or that its diagnostic statistics are calibrated across all supported datasets.

**Beta state**

Beta provides unweighted residual summaries and weighted diagnostics. The weighted pathway uses Cholesky-based whitening and a quadratic statistic when the relevant uncertainty and independence assumptions are explicit.

The Beta review specifically distinguishes these diagnostics from calibrated p-values or Bayesian evidence. It also notes that the workflow does not estimate the covariance structure itself.

**Assessment**

Beta's explicit treatment of covariance and weighting is a meaningful improvement in the representation of statistical assumptions. It gives the application a more structured way to evaluate residuals when the required inputs are available.

There are nevertheless important boundaries:

1. A quadratic residual statistic is not automatically a calibrated hypothesis test.
2. Weighted residuals are only as defensible as the supplied uncertainties and covariance assumptions.
3. An independence assumption does not establish that the measurements are actually independent.
4. The diagnostic does not infer an appropriate covariance matrix merely because a covariance-aware calculation exists.
5. Small residuals do not, on their own, establish a molecular detection or uniquely identify an atmospheric composition.

Consequently, Beta's diagnostics should be described as model-comparison diagnostics under stated assumptions, not as definitive evidence for a molecule.

### 3.5 Sensitivity analysis versus retrieval

V1's documented gas-abundance scan explores a restricted parameter dimension under the selected modeling assumptions.

Beta's leave-one-out sensitivity diagnostic evaluates how the generated model changes when a selected component is omitted, under the configured model and inputs.

These answer different but related questions:

- A parameter scan asks how a model output changes as a chosen parameter varies.
- A leave-one-out analysis asks how much a selected model component contributes to the generated spectrum under the current assumptions.
- A retrieval attempts to infer parameters from observations using a defined statistical model and likelihood or equivalent inference procedure.

Neither the v1 parameter scan nor Beta's leave-one-out diagnostic should be equated with a complete atmospheric retrieval. Neither operation alone demonstrates that a component has been detected in observational data.

### 3.6 Numerical edge cases and outstanding verification

The reviews identified several specific areas that should be carried forward into the comparative assessment.

**V1: covariance scaling**

The v1 review flagged a possible covariance-scaling issue in `app/core/fitting.py`, around lines 327–347. This was identified as a potential defect requiring synthetic reproduction, not as a confirmed failure.

**Beta: cross-section input validation**

The Beta review identified a potential issue in which cross-section input paths may not reject every non-finite value before model generation. This requires targeted tests and source-level confirmation.

**Beta: model parameter validation**

The review also identified parameters such as `haze_slope` and `n_altitude_layers` that were not explicitly validated in the initial validation block. The consequences depend on the downstream calculations and any later validation.

**Beta: reference-temperature mismatch**

The model workflow can warn about a reference-temperature mismatch without correcting the cross section. This is a documented scientific limitation, distinct from a general numerical crash or input-validation defect.

These concerns should not be ranked by severity until they have been reproduced or confirmed against the current implementation. Their presence in the review is evidence of an outstanding verification need, not proof that the affected calculations produce incorrect outputs in every case.

## 4. What the Scientific Progression Means

The main progression is a move toward **more explicit scientific preconditions and better-defined numerical stages**.

Beta separates eligibility, alignment, model generation, and residual analysis into distinct components. This supports targeted testing and makes some assumptions easier to inspect. It also creates more opportunities to test transformations and invalid-input behavior independently.

The remaining gap is scientific validation. A robust research workflow requires more than modular calculations and passing unit tests. It needs suitable reference datasets, known-answer or independently generated synthetic cases, justified uncertainty models, instrument-response treatment where relevant, and documented comparisons against independent scientific results.

The v1 and Beta reviews do not establish that these requirements have been satisfied end to end.

## 5. Category 3 Findings

| Classification | Finding |
|---|---|
| Improved | Explicit comparison-input metadata, eligibility checks, coordinate transformations, covariance permutation, and uncertainty-assumption requirements. |
| Expanded | Native transmission forward modeling, model-sensitivity diagnostics, and structured residual-analysis pathways. |
| Retained from v1 | Integrated feature identification, gas fitting, transit-depth extraction, and optional atmospheric modeling. |
| Unresolved in v1 | Potential covariance-scaling concern requiring synthetic reproduction; model and uncertainty limitations documented in the review. |
| Unresolved in Beta | Potential non-finite cross-section input handling, incomplete explicit parameter validation, and reference-temperature mismatch behavior. |
| Not established | Comparative numerical accuracy, complete covariance estimation, calibrated molecular-detection evidence, full atmospheric retrieval, or end-to-end empirical scientific validation. |
| Confirmed scientific regression | None established by the current evidence. |

## 6. Category 3 Verdict

**Assessment: Beta improves the explicitness and structure of scientific comparison calculations, but its numerical and scientific superiority over v1 has not been demonstrated.**

Beta's strongest advances are its explicit input-eligibility rules, structured spectral alignment, covariance-aware transformations, weighted residual diagnostics, and native forward-model implementation. These capabilities create a more disciplined foundation for comparison workflows and make important assumptions easier to test.

V1 retains meaningful scientific functionality, particularly integrated feature identification, gas fitting, transit analysis, and optional petitRADTRANS modeling. The two versions therefore should not be ranked by the number of scientific modules alone.

The outstanding numerical concerns in both versions also matter. Beta's broader safeguards do not eliminate the need to verify edge cases, and its new model generator introduces its own assumptions and validation requirements.

The defensible conclusion is that Beta has **more explicit scientific-comparison infrastructure and a broader set of comparison-preparation calculations**, while the relative accuracy, robustness, and empirical validity of the two versions remain unproven by these reviews.

**Confidence:** Moderate for the documented differences in implementation and assumptions. Lower for comparative numerical reliability and scientific accuracy, because the concerns were not all reproduced and no new empirical validation was performed for this category.

---

## Review Sources and Audit Trail

Review-document directory:

`docs/ecas v1 and beta comparison documents/`

Relevant records:

- `ecas_v1_pass_0.md` — initial v1 review planning.
- `ecas_v1_pass_A.md` through `ecas_v1_pass_G.md` — v1 review evidence, including scientific implementation and numerical concerns.
- `ecas_beta_pass_0.md` — initial Beta review planning.
- `ecas_beta_pass_A.md` through `ecas_beta_pass_G.md` — Beta review evidence, including eligibility, alignment, model generation, residual diagnostics, and numerical concerns.
- `10_29_26_ecas_beta_review_initial.md` — earlier comprehensive Beta review, retained as a separate historical assessment.
- `comparison_cat_1.md` — architecture and application structure comparison.
- `comparison_cat_2.md` — functional capabilities and workflows comparison.
- `comparison_cat_3.md` — this document.

Potential defects described in the source reviews remain classified as potential until reproduced or confirmed. Source implementation, automated tests, independent review, desktop acceptance, and empirical scientific validation are separate forms of evidence and must remain distinct in the final synthesis.