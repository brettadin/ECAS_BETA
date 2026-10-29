# ECAS Chunk 6 Review Checkpoint — 2026-10-28

## Overview & Authorization

The user authorized creating this checkpoint and pushing to GitHub for external and human review.
- **Repository:** `https://github.com/brettadin/ECAS_BETA`
- **Working Tree:** `C:/AI-Projects/Bwett AI Project UwU/ECAS_BETA`
- **Branch:** `codex/roadmap-reconciliation-20261028`
- **Chunk Scope:** **Chunk 6 — Scientific Comparison, Interpretation, and Projections** (Stages 6.1–6.7 complete).
- **Previous Published Checkpoint:** `49e3b963b06e4a96dc626dd13178ab13f857bcd9` (end of Chunk 5.1).

---

## What Has Been Implemented & Verified in Chunk 6

1. **Stage 6.1 — Production Eligibility Contract & Adapters (`ecas/comparison/eligibility.py`, `ecas/comparison/inputs.py`)**
   - Implemented `assess()` and `describe_reason()` under contract `ecas-comparison-eligibility-v1`.
   - Observation adapter (`observation_input`) and ExoMol cached product adapter (`reference_input`) preserve raw coordinates, units, and raw uncertainty columns without silent inference.
   - Strictly blocks direct comparisons between raw ExoMol cross sections ($\text{cm}^2/\text{molecule}$ on $\text{cm}^{-1}$) and transit depth ($\%$ or fraction on $\mu\text{m}$) with `right.role.requires_physical_model_or_supported_role`.

2. **Stage 6.2 — Aligned-Grid Residual Diagnostics (`ecas/comparison/residuals.py`)**
   - Implemented `evaluate_residuals()` enforcing a mandatory `assess()` gate.
   - Computes point-by-point residuals using the `left_minus_right` convention ($r_i = y_{\text{left}, i} - y_{\text{right}, i}$).
   - Computes descriptive statistics in native signal units (`mean_residual`, `mean_abs_residual`, `rms_residual`, `max_abs_residual`).
   - Implemented Cholesky whitening and fixed-covariance quadratic calculation ($Q = r^T C^{-1} r$) under `weighted_residual_v1`, with log-det normalization omitted and explicit disclaimers against reduced $\chi^2$ or detection-significance claims.

3. **Stage 6.3 — Multi-Candidate Evaluation & Residual Visualization (`ecas/comparison/candidates.py`, `ecas/visualization/residual_plot.py`)**
   - Implemented `evaluate_candidates()` comparing one target against multiple candidate spectra on shared support.
   - Retains blocked candidates with full eligibility reasons (`blocked_indices`).
   - Preserves exact ties within `TIE_ATOL = 1e-12` (`closest_candidate_indices`).
   - **Covariance Parity Guard:** Blocks cross-candidate ranking (`fair_ranking_permitted = False`, reason `'candidates.combined_covariance.differs_across_candidates'`) if candidate combined covariances differ, preventing bias toward noisy models.
   - Added `ResidualPlot` (disabling `autoSIPrefix` on native axes) with lazy instantiation in `ComparisonBrowser`, and automatic clearing of residual plots when an incompatible candidate is inspected.

4. **Stage 6.4 — Explicit, Opt-In Alignment (`ecas/comparison/alignment.py`)**
   - Implemented `convert_signal_unit()` (scaling `values`, `sigma`, and covariance $s^2 C$ invariantly).
   - Implemented `convert_axis_unit()` (`nanometers`/`angstroms` to `microns`).
   - Implemented `restrict_to_shared_coordinates()` without interpolation or extrapolation.
   - Implemented `integrate_model_over_bins()` (forward models only; observations are never upsampled; out-of-domain bins recorded in `excluded_indices`).

5. **Stage 6.5 — Tamper-Evident Project Persistence & Reproducibility (`ecas/comparison/persistence.py`, `ecas/projects.py`)**
   - Added atomic, SHA-256-integrity-signed JSON comparison records (`ecas-comparison-record-v1`) under `projects/<project_id>/comparisons/*.json` without modifying SQLite schemas.
   - Added `reproduce_comparison_record()` re-executing `assess()` and `evaluate_residuals()` from saved arrays, verifying verdict and diagnostic match against disk, and logging explicit `reproducibility_limitations`.

6. **Stage 6.6 — Forward-Model Provenance Contract (`ecas/comparison/forward_model.py`)**
   - Defined `AtmosphericModelProvenance` and `OpacitySourceSpec` capturing explicit radiative-transfer parameters ($T(P)$, gravity, reference pressure, radii, species mixing ratios, opacities, continuum/clouds).
   - Created `project_cross_section_to_transit_depth()` raising `UnsupportedProjectionError`, explicitly blocking unvalidated cross-section rescaling or ad-hoc abundance retrieval.

7. **Stage 6.7 — Interactive Desktop Candidate Workflow & Project Persistence UI (`ecas/ui/comparison_browser.py`, `ecas/ui/main_window.py`)**
   - Implemented `load_forward_model_file()` for `ecas-forward-model-v1` JSON curves (4 MiB limit, raw-byte SHA-256 binding, native unit preservation).
   - Captured raw-byte SHA-256 at CSV import and verified project reopen in `ECASWindow` without rereading files from disk.
   - Added collapsible candidate and persistence tools in `ComparisonBrowser`: caller metadata attestations (never overriding imported facts), opt-in unit/shared-grid alignment, candidate staging (forward models + cached ExoMol references), candidate switching (clearing plots on blocked candidates), active-project comparison saving, and offline verification/reopening.

8. **Methodology Documentation**
   - Published comprehensive five-perspective specification: `docs/SCIENTIFIC_COMPARISON_AND_INTERPRETATION.md`.

---

## Verification Summary

- **Automated Tests:** **603 passed, 1 skipped in 14.41s** (exit code `0`) across the entire repository offscreen (`QT_QPA_PLATFORM=offscreen`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`).
- **Targeted UI & Persistence Regression:** **58 passed in 7.72s** (exit code `0`).
- **Encoding & Integrity:** All modified/added Python and Markdown files verified as valid UTF-8 without byte-order marks (BOM).
- **Human Desktop Review:** Interactive UI review of `main.py` was previously conducted and approved on 2026-10-28.
- **Independent Code Review:** Stages 6.2–6.6 and Stage 6.7 were independently code-reviewed in Gemini 3.8 Flash (Medium) with zero blockers and zero defects.

---

## Explicit Boundaries & Deferred Capabilities

1. **No Built-in Atmospheric Radiative-Transfer Solver or Retrieval:** ECAS does not synthesize planetary atmospheres from scratch or invert observed transit depths into molecular abundances. These require dedicated, validated solvers.
2. **Raw Cross Sections Blocked:** Raw ExoMol cross sections cannot be directly overlaid, subtracted, or scored against transit-depth data.
3. **No Curve Fitting Away of Differences:** Comparison residuals remain un-fit and un-rescaled; no nuisance parameters are adjusted to force agreement.
4. **Reproducibility Scope:** Saved comparison records preserve evaluated arrays, hashes, and transformation history; re-ingesting raw observation files independently requires access to original external source files or project attachments.
