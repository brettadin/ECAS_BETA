# Chunk 6 implementation log — Scientific Comparison, Interpretation, and Projections

## 2026-10-28 — Stage 6.1: production eligibility contract and UI compatibility wiring

Ported the reviewed Chunk 5 eligibility contract and observation adapter into
production modules under `ecas/comparison/` (`eligibility.py`, `inputs.py`) without
importing research scripts from `docs/Chunk_5/`, and extended `inputs.py` with
`reference_input()` for cached ExoMol cross sections. Wired `ComparisonBrowser._explain()`
to run `assess()` on selected observation snapshots and cached ExoMol products,
displaying versioned contract status (`ecas-comparison-eligibility-v1`), plain-language
unmet checks (`describe_reason()`), and exact machine-readable reason codes in the
tooltip while keeping raw cross-section vs. transit-depth comparisons strictly blocked.

User confirmed normal-desktop human UI review complete and functional on 2026-10-28.

## 2026-10-28 — Stage 6.2: aligned-grid unweighted and Cholesky-weighted residuals

Implemented `ecas/comparison/residuals.py` (`IneligibleComparisonError`,
`ResidualDiagnostic`, `evaluate_residuals()`) enforcing a mandatory `assess()` gate
on every call. Computes `left_minus_right` point-by-point residuals, descriptive
summaries (`mean_residual`, `mean_abs_residual`, `rms_residual`, `max_abs_residual`),
and Cholesky-whitened residuals / fixed-covariance quadratics (`weighted_residual_v1`)
without log-determinant fitting or detection-significance claims. Created the
five-perspective standalone methodology reference
`docs/SCIENTIFIC_COMPARISON_AND_INTERPRETATION.md`.

## 2026-10-28 — Stage 6.3: multi-candidate evaluation and UI residual/overlay inspection

Implemented `ecas/comparison/candidates.py` (`evaluate_candidates()`) to evaluate
multiple candidates against one target on shared support while retaining blocked
candidates with full reasons, preserving tied closest candidates within `1e-12`,
and blocking cross-candidate weighted ranking when combined covariances differ
(`candidates.combined_covariance.differs_across_candidates`). Added
`ecas/visualization/residual_plot.py` (`ResidualPlot`, `autoSIPrefix=False`) and
wired lazy diagnostic rendering (`evaluate_inputs()`, `evaluate_candidate_inputs()`,
`_clear_diagnostic()`) into `ecas/ui/comparison_browser.py` so blocked pairs show
zero shared-axis widgets and switching to an incompatible reference clears stale
residuals immediately.

## 2026-10-28 — Stages 6.4–6.6: explicit alignment, persistence, and forward-model contract

- **Explicit alignment (`ecas/comparison/alignment.py`):** Added opt-in,
  provenance-recorded `convert_signal_unit()`, `convert_axis_unit()`,
  `restrict_to_shared_coordinates()`, and `integrate_model_over_bins()`. Preserves
  immutable `original` inputs, scales `sigma` and `covariance` ($s^2$) consistently,
  records `included_indices` and `excluded_indices`, refuses observation upsampling,
  and rejects wavenumber/cross-section conversions.
- **Comparison record persistence (`ecas/comparison/persistence.py`, `ecas/projects.py`):**
  Added atomic, SHA-256-integrity-signed JSON comparison records
  (`ecas-comparison-record-v1`) under `projects/<project_id>/comparisons/*.json`
  with zero SQLite schema changes, plus `reproduce_comparison_record()` and explicit
  `reproducibility_limitations`.
- **Forward-model boundary (`ecas/comparison/forward_model.py`):** Defined
  `AtmosphericModelProvenance`, `OpacitySourceSpec`, `forward_model_input()`, and
  `project_cross_section_to_transit_depth()` (`UnsupportedProjectionError` blocking
  ad-hoc cross-section rescaling or unvalidated abundance retrieval).

## 2026-10-28 — Stage 6.7: interactive desktop candidate workflow, forward-model loader, and project save/reproduce UI

- **Validated forward-model JSON loader (`ecas/comparison/forward_model.py`):** Added
  `MODEL_FILE_SCHEMA` (`ecas-forward-model-v1`), `LoadedForwardModel`, and
  `load_forward_model_file()` enforcing a 4 MiB file limit, symlink/junction rejection,
  raw-byte `source_sha256` binding, full `AtmosphericModelProvenance` validation, and
  native wavelength/signal unit preservation without implicit conversion.
- **CSV & reopened-project raw hash preservation (`ecas/ui/main_window.py`):** Captured
  raw-byte SHA-256 on local CSV imports (`_hash_file_if_present`) and verified saved
  project attachments (`_open_project_spectrum`) so session observation snapshots carry
  verified hashes without re-reading files from disk.
- **Interactive Comparisons workflow (`ecas/ui/comparison_browser.py`):** Added a
  collapsed-by-default candidate & persistence panel supporting non-conflicting caller
  metadata attestations (recorded under `left.provenance.caller_attestations`), explicit
  opt-in unit/shared-grid alignment (`align_checkbox`), forward-model JSON and cached
  ExoMol reference candidate staging, per-candidate selector inspection (clearing stale
  plots whenever a blocked candidate is inspected), active-project comparison saving
  (`save_active_comparison()`), and signed-record integrity/reproducibility verification
  (`reproduce_selected_comparison()`).
- **Verification:** Focused UI + persistence suite: `58 passed in 7.72s`; full offscreen
  suite: `603 passed, 1 skipped in 14.41s`, exit `0`.


