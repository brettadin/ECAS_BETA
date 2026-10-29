# Scientific Comparison, Interpretation, and Projections Methodology

**Document Version:** `ecas-comparison-methodology-v1`  
**Contract Version:** `ecas-comparison-eligibility-v1`  
**Record Schema:** `ecas-comparison-record-v1`  
**Forward-Model File Schema:** `ecas-forward-model-v1`  
**Last Updated:** 2026-10-28

This document defines the scientific, mathematical, chemical, software, and inferential foundations of the ECAS spectral comparison workflow. It maintains an explicit separation between **implemented and tested behavior**, **validated scientific evidence**, and **deferred or unsupported capabilities**.

---

## 1. Scientific and Physical Perspective

### 1.1 What the Inputs Represent
ECAS handles physically distinct families of spectroscopic datasets:

1. **Observational Transmission Spectra (`SpectrumData`):**
   - Represent the wavelength-dependent effective fractional area blocked by an exoplanet's atmospheric limb during primary transit:
     $$\delta(\lambda) = \left(\frac{R_p(\lambda)}{R_\star}\right)^2$$
   - Reported in **percent** ($\%$) or **dimensionless fraction** as a function of wavelength $\lambda$ (typically in **microns**, $\mu\text{m}$), integrated over discrete instrument bandpasses or spectroscopic bins.
2. **Molecular Reference Cross Sections (`MolecularCrossSection`):**
   - Represent the microscopic photon absorption cross section per molecule $\sigma(\tilde{\nu}; T, P)$ in $\text{cm}^2/\text{molecule}$ as a function of wavenumber $\tilde{\nu}$ in $\text{cm}^{-1}$ at specified temperature $T$ and pressure $P$ (for ExoMol `.sigma` products, zero-pressure Doppler-broadened profiles).
3. **Atmospheric Forward-Modelled Transit Spectra (`AtmosphericModelProvenance` -> `ComparisonInput`):**
   - Externally computed radiative-transfer predictions of $\delta(\lambda)$ generated under explicit, documented physical assumptions ($T(P)$ profile, surface gravity $g$, reference pressure $P_0$, planetary radius $R_0$, stellar radius $R_\star$, active species/isotopologues and input mixing ratios, opacity versions/hashes, continuum/cloud decks, coordinate frame, and instrument response).

### 1.2 Why Raw Cross Sections Cannot Be Directly Compared to Transit Depth
A molecular absorption cross section $\sigma(\tilde{\nu})$ is an intensive microscopic property of a single chemical species, whereas transit depth $\delta(\lambda)$ is an extensive macroscopic observable integrated along slant chord paths through an atmosphere and normalized by stellar disk area. Consequently, **ECAS strictly prohibits direct overlay, subtraction, rescaling, or correlation of raw molecular cross sections against transit-depth observations.** Calling `project_cross_section_to_transit_depth()` raises `UnsupportedProjectionError` explaining the required radiative-transfer dependencies.

### 1.3 When Two Spectra Are Comparable
Under contract `ecas-comparison-eligibility-v1`, quantitative residual comparison is permitted only when both inputs:
- Represent the same physical observable (`transit_depth`),
- Have compatible, supported roles (`observation`, `forward_model`, or `reference_measurement`),
- Share identical coordinate units (`microns`), signal units (`percent` or `fraction`, without implicit scaling), coordinate frame (`coordinate_frame`), and instrument response identifier (`response_id`) backed by caller-supplied `response_evidence`,
- Provide at least three finite measurements on strictly increasing, exactly aligned coordinate grids.

---

## 2. Mathematical and Statistical Perspective

### 2.1 Explicit Alignment and Unit Transformations (`ecas/comparison/alignment.py`)
No transformation runs implicitly inside `assess()` or `evaluate_residuals()`. Every permitted transformation must be invoked explicitly and returns an immutable `TransformedInput(original, transformed, steps)` recording exact parameters, `included_indices`, `excluded_indices`, and `exclusion_reason`:

1. **Signal-Unit Scaling (`convert_signal_unit_v1`):**
   - Supports lossless scaling between `'fraction'` and `'percent'` ($s = 100$ for $\text{fraction} \to \text{percent}$; $s = 0.01$ for $\text{percent} \to \text{fraction}$):
     $$y'_i = s\,y_i, \quad \sigma'_i = s\,\sigma_i, \quad C'_{ij} = s^2\,C_{ij}$$
   - Ensures dimensionless weighted quadratics $Q = r^T C^{-1} r$ remain strictly invariant under unit conversion.
2. **Wavelength-Unit Scaling (`convert_axis_unit_v1`):**
   - Converts strictly increasing positive wavelength grids (`'nanometers'` / `'nm'` via $10^{-3}$; `'angstroms'` via $10^{-4}$) to `'microns'` while preserving index order. Wavenumber (`'cm^-1'`) conversion is rejected here.
3. **Shared Exact-Grid Restriction (`restrict_to_shared_coordinates_v1`):**
   - Restricts two grids with identical `axis_unit` and `coordinate_frame` to their exact shared coordinates ($m \ge 3$), slicing covariance submatrices via $C_{\mathcal{I},\mathcal{I}}$ and recording excluded indices with reason `'outside_shared_exact_grid'`. Zero interpolation or extrapolation occurs.
4. **Top-Hat Bin Integration (`integrate_tophat_bins_v1`):**
   - Permitted **only** for `role == 'forward_model'` (observations are never upsampled). For each declared bin $[a_k, b_k]$ fully contained within $[x_{\text{model}, 1}, x_{\text{model}, M}]$, computes exact piecewise-linear trapezoidal average:
     $$\bar{y}_k = \frac{1}{b_k - a_k} \int_{a_k}^{b_k} y_{\text{model}}(x)\,dx$$
   - Partially covered or out-of-domain bins are never clipped or extrapolated; they are recorded in `excluded_indices` with reason `'bin_not_fully_covered_by_model_domain'`.

### 2.2 Residual Convention (`aligned_residual_v1`)
For two eligible inputs $(x, y_{\text{left}})$ and $(x, y_{\text{right}})$ on an aligned grid $x = (x_1, \dots, x_n)$ with $n \ge 3$, the point-by-point residual vector $r \in \mathbb{R}^n$ uses the **`left_minus_right`** convention:

$$r_i = y_{\text{left}, i} - y_{\text{right}, i}, \quad i = 1, \dots, n$$

Unweighted descriptive summaries in the native `signal_unit` are:
$$\bar{r} = \frac{1}{n} \sum_{i=1}^n r_i, \quad \text{MAR} = \frac{1}{n} \sum_{i=1}^n |r_i|, \quad \text{RMS} = \sqrt{\frac{1}{n} \sum_{i=1}^n r_i^2}, \quad r_{\max} = \max_{1 \le i \le n} |r_i|$$

### 2.3 Uncertainty-Weighted Diagnostics (`weighted_residual_v1`)
Weighted evaluation requires explicit `noise_kind` and `noise_evidence` on both inputs plus `cross_dataset_independent=True`:
- `deterministic_model` (`role == 'forward_model'` only): $C = \mathbf{0}_{n \times n}$.
- `independent_gaussian_1sigma` ($\sigma_i > 0$): $C = \operatorname{diag}(\sigma_1^2, \dots, \sigma_n^2)$.
- `gaussian_covariance`: finite symmetric ($C = C^T$, $\text{rtol}=10^{-12}$) positive-definite $C \in \mathbb{R}^{n \times n}$.

Under declared cross-dataset independence (rejected if two stochastic inputs share `source_sha256`), combined covariance $C = C_{\text{left}} + C_{\text{right}}$ is factored via Cholesky decomposition $C = L L^T$:
$$L w = r \implies w = L^{-1} r, \quad Q = w^T w = r^T C^{-1} r$$
$Q$ omits the Gaussian normalization $\ln\det(2\pi C)$ and is neither reduced $\chi^2$ nor a calibrated $p$-value. Asymmetric archive error columns (`pl_trandeperr1`, `pl_trandeperr2`) are preserved in `raw_uncertainty_columns` and never symmetrized into Gaussian weights.

### 2.4 Multi-Candidate Fair-Comparison Rules (`ecas/comparison/candidates.py`)
When comparing one `target` against candidates $(c_0, \dots, c_{K-1})$:
- Every candidate is evaluated against the **exact same `target`** grid, units, frame, and response, with zero fitted nuisance parameters.
- Blocked candidates are retained in `CandidateComparisonSummary.candidates` with full `Eligibility` reasons (`blocked_indices`).
- **Covariance Parity Guard:** In `weighted=True` mode, if eligible candidates produce different combined covariance matrices $C_{\text{target}} + C_{c_k}$ (e.g., mixing a `deterministic_model` with a noisy `reference_measurement`), cross-candidate ranking is **blocked** (`fair_ranking_permitted = False`, reason `'candidates.combined_covariance.differs_across_candidates'`) because omitting $\ln\det(2\pi C)$ biases raw $Q$ toward noisier candidates.
- **Ambiguity Preservation:** All eligible candidates within `TIE_ATOL = 1e-12` of the minimum metric are returned together in `closest_candidate_indices`.

---

## 3. Chemical Perspective

### 3.1 Supported Molecular Reference Products
ECAS supports bounded retrieval, validation, and atomic caching for three main-isotopologue ExoMol zero-pressure Doppler-broadened cross-section services:
- **Carbon Dioxide ($\text{CO}_2$):** `12C-16O2`, line list `UCL-4000` ($\tilde{\nu}_{\max} = 20000\text{ cm}^{-1}$, $T_{\max} = 4000\text{ K}$).
- **Water ($\text{H}_2\text{O}$):** `1H2-16O`, line list `POKAZATEL` ($\tilde{\nu}_{\max} = 41200\text{ cm}^{-1}$, $T_{\max} = 5000\text{ K}$).
- **Methane ($\text{CH}_4$):** `12C-1H4`, line list `MM` ($\tilde{\nu}_{\max} = 12000\text{ cm}^{-1}$, $T_{\max} = 2000\text{ K}$).

### 3.2 Spectral Feature Overlap and Degeneracy
Multiple species (e.g., $\text{H}_2\text{O}$ and $\text{CH}_4$ in the near-IR) have overlapping vibrational-rotational bands. Coarse instrumental binning can render distinct narrow band structures indistinguishable (`docs/Chunk_5/RESPONSE_AND_UNCERTAINTY_EXPERIMENT.md`). Candidate closeness within a finite candidate set never rules out unmodelled molecules, hazes, or stellar contamination.

---

## 4. Software and Implementation Perspective

### 4.1 Production Architecture
| Module | Responsibility |
| :--- | :--- |
| `ecas/comparison/eligibility.py` | `ComparisonInput`, `Eligibility`, `assess()`, `describe_reason()` (`ecas-comparison-eligibility-v1`). |
| `ecas/comparison/inputs.py` | `AdaptedInput`, `observation_input()`, `reference_input()`. Preserves raw order, units, and raw uncertainty columns. |
| `ecas/comparison/alignment.py` | `TransformationStep`, `TransformedInput`, `convert_signal_unit()`, `convert_axis_unit()`, `restrict_to_shared_coordinates()`, `integrate_model_over_bins()`. |
| `ecas/comparison/residuals.py` | `IneligibleComparisonError`, `ResidualDiagnostic`, `evaluate_residuals()`. Enforces mandatory `assess()` gate. |
| `ecas/comparison/candidates.py` | `CandidateAssessment`, `CandidateComparisonSummary`, `evaluate_candidates()`. Enforces covariance parity and tie preservation. |
| `ecas/comparison/forward_model.py` | `OpacitySourceSpec`, `AtmosphericModelProvenance`, `LoadedForwardModel`, `forward_model_input()`, `load_forward_model_file()`, `project_cross_section_to_transit_depth()`. |
| `ecas/comparison/persistence.py` | `SCHEMA` (`ecas-comparison-record-v1`), `build_comparison_record()`, `save_comparison_record()`, `load_comparison_records()`, `reproduce_comparison_record()`. |
| `ecas/visualization/residual_plot.py` | `ResidualPlot` displaying aligned overlays and zero-referenced `left - right` residuals with `autoSIPrefix` disabled. |
| `ecas/ui/comparison_browser.py` | Independent native-unit input inspection plus collapsible interactive candidate tools: optional non-conflicting caller metadata attestations, explicit opt-in unit/shared-grid alignment, `ecas-forward-model-v1` JSON loading, per-candidate selector switching (clearing stale plots on blocked candidates), and active-project comparison record save/reproduce controls. |
| `ecas/ui/main_window.py` | Captures raw-byte SHA-256 at CSV/NASA `.tbl` import and verified project-reopen time so session observation snapshots carry verified source hashes without re-reading files. |

### 4.2 Persistence and Reproducibility (`ecas-comparison-record-v1`)
- Comparison records are stored atomically (`NamedTemporaryFile` + `os.fsync` + `os.replace`) under `projects/<project_id>/comparisons/<uuid>.json`, leaving `data.sqlite` untouched and avoiding destructive SQLite migrations.
- Every record is signed with a canonical JSON `integrity_sha256` verified on reload; tampered or truncated records are rejected and counted separately.
- `reproduce_comparison_record()` re-executes `assess()` and `evaluate_residuals()` from the saved evaluated inputs and reports `ReproducibilityCheck` alongside explicit `reproducibility_limitations` (noting when raw source files or byte hashes are absent).

---

## 5. Logical and Inferential Perspective

1. **Blocked Status (`incompatible` / `missing_requirements`):** Indicates unmet physical-model, observable, unit, coordinate-frame, grid-alignment, response, or noise requirements—not data corruption. Independent native-unit inspection remains available.
2. **Numerical Closeness vs. Adequacy vs. Significance vs. Composition:**
   - **Numerical closeness** (lower RMS or fixed-covariance $Q$) orders eligible candidates on the shared support only.
   - **Model adequacy** requires inspecting structured residuals and continuum assumptions; the numerically closest candidate in an inadequate set can still be a poor physical description.
   - **Statistical detection significance** requires calibrated null distributions accounting for look-elsewhere search multiplicity (`docs/Chunk_5/MODEL_COMPARISON_PROTOTYPE.md`), which ECAS does not claim.
   - **Atmospheric abundance / composition** requires validated radiative-transfer retrieval and posterior inference, which remain deferred.

---

## 6. Implementation & Verification Matrix

| Capability | Status | Implementation & Test Evidence |
| :--- | :--- | :--- |
| Eligibility contract v1 (`aligned_residual_v1`, `weighted_residual_v1`) | **Implemented & Tested** | `ecas/comparison/eligibility.py`, `tests/test_comparison_eligibility.py` |
| Observation & ExoMol reference input adapters | **Implemented & Tested** | `ecas/comparison/inputs.py`, `tests/test_import_eligibility_adapter.py` |
| Explicit unit conversions, shared-grid restriction & top-hat bin integration | **Implemented & Tested** | `ecas/comparison/alignment.py`, `tests/test_comparison_alignment.py` |
| Unweighted & Cholesky-weighted residual diagnostics | **Implemented & Tested** | `ecas/comparison/residuals.py`, `tests/test_comparison_residuals.py` |
| Multi-candidate comparison, covariance parity & tie preservation | **Implemented & Tested** | `ecas/comparison/candidates.py`, `tests/test_comparison_candidates.py` |
| Aligned overlay & residual plot + stale-state UI clearing | **Implemented & Tested** | `ecas/visualization/residual_plot.py`, `ecas/ui/comparison_browser.py`, `tests/test_comparison_browser.py` |
| Project comparison record persistence & reproducibility verification | **Implemented & Tested** | `ecas/comparison/persistence.py`, `ecas/projects.py`, `tests/test_comparison_persistence_and_model.py` |
| Forward-model provenance contract, JSON loader (`ecas-forward-model-v1`) & ad-hoc projection block | **Implemented & Tested** | `ecas/comparison/forward_model.py`, `tests/test_comparison_persistence_and_model.py` |
| Interactive GUI candidate staging, opt-in alignment, per-candidate inspection & project save/reproduce | **Implemented & Tested** | `ecas/ui/comparison_browser.py`, `ecas/ui/main_window.py`, `tests/test_comparison_browser.py` |
| Built-in radiative-transfer forward solver & abundance retrieval | **Deferred / Unsupported** | Explicitly blocked by `UnsupportedProjectionError` |
| Empirical validation on mission-calibrated forward models | **Deferred** | Synthetic fixtures verify mathematical/contract correctness only |
