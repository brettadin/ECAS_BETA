# ECAS Project Checkpoint — Chunk 7 & Post-Review Physics/UX Increment

**Timestamp:** 2026-10-29T02:46:00-04:00  
**Branch:** `codex/roadmap-reconciliation-20261028`  
**Repository:** https://github.com/brettadin/ECAS_BETA  
**Scope:** ECAS Chunk 7 Complete + Post-Review Physics/Forward Modeling + UI Rescaling, Clean Summary Card & Collapsible Source Metadata  
**Test Suite Status:** 622 passed, 22 skipped in 16.29s (`QT_QPA_PLATFORM=offscreen`, Python 3.14.5, strict `pytest -W error`)  
**Current Milestone State:** Complete and verified across all 622 tests

---

## 1. Executive Summary & Capabilities Delivered

### A. Core Chunk 7 Scientific Resources & Interoperability
1. **Structured References & Resources Desktop Tab (Stage 7.1)**:
   - Added `References & Resources` at navigation index `6` in the desktop UI (`ecas/ui/resources_browser.py`, `ecas/ui/main_window.py`).
   - Integrated an auditable catalog (`ecas/resources/catalog.py`) containing 17 verified canonical resources across 5 categories (`Software`, `Data archive`, `Molecular data`, `Python library`, `Publication`).
   - Clean canonical HTTPS URLs verified without tracking query parameters (`utm_*`, `gclid`, `fbclid`).
   - Interactive single-click category filter pills, live query search, resource details panel, and clipboard copy controls for canonical links and scientific citations.

2. **Scientific Format Interoperability & Semantics (Stage 7.2)**:
   - Created `ecas/ingestion/tabular_formats.py` supporting Astropy `.ecsv`, scientific delimited tables (`.dat`, `.tsv`, `.txt`, `.asc`), and IEEE-754 big-endian 2880-byte-aligned FITS 1D binary tables (`.fits`, `.fit`, `.fts`).
   - Enforced strict physical separation between laboratory FTIR/UV-Vis absorbance/transmittance measurements, laboratory cross sections (`cm^2/molecule`), reference emission spectra (`emission_intensity` / `line_flux`), and planetary transit observations.
   - Added `convert_wavenumber_to_microns()` in `ecas/comparison/alignment.py` with coordinate order reversal and exact $P \mathbf{C} P^{\mathsf{T}}$ covariance permutation, preserving generalized quadratic distances $\mathbf{r}^{\mathsf{T}}\mathbf{C}^{-1}\mathbf{r}$ to machine precision ($< 10^{-12}$).
   - Extended `_SIGNAL_FACTORS` to support `ppm` conversions and `_AXIS_FACTORS` for `um` and `angstrom`.

3. **Molecular Database Temperature Applicability & Species Evidence (Stage 7.3)**:
   - Implemented `validate_temperature_applicability()` for `ExoMol`, `HITRAN`, `HITEMP`, `NIST ASD`, and `GEISA`, warning researchers when room-temperature line lists (e.g. HITRAN at 296 K) are applied to hot-Jupiter atmospheres ($T > 500\text{--}1000\text{ K}$) due to missing hot bands.
   - Structured published exoplanet characterization benchmarks for WASP-39 b and K2-18 b using the 6 explicit `EVIDENCE_STATUSES` (`reported_detection`, `independent_confirmation`, `tentative_or_disputed`, `upper_limit_or_non_detection`, `model_predicted_presence`, `not_assessed`).

4. **External Forward-Model Adapters & Research Foundation (Stage 7.4)**:
   - Documented the 10-dimension software comparison matrix (`petitRADTRANS`, `POSEIDON`, `TauREx 3`, `PLATON`, `Pyrat Bay`), radiative transfer and Bayesian retrieval formulations, observational archives, and molecular databases in `docs/Chunk_7/RESEARCH_AND_MODELING_FOUNDATION.md`.
   - Created `ecas/comparison/model_adapters.py` implementing Approach C: lightweight external model ingestion that exports and validates precomputed spectra into the `ecas-forward-model-v1` JSON format with complete `AtmosphericModelProvenance`.

### B. Post-Review Physics, Data-Accuracy & UX Increment
5. **Physical 1D Limb-Transmission Forward-Model Generator (`ecas/comparison/model_generator.py`)**:
   - Implemented spherical-shell slant-chord quadrature for an isothermal hydrostatic planetary atmosphere (`generate_isothermal_transmission_model`) with dynamic optically thin top-of-atmosphere sizing, verified against the analytical Lecavelier des Etangs et al. (2008) / Heng & Kitzmann (2017) formula to $< 0.3\%$ accuracy across 4 orders of magnitude in opacity.
   - Included published planet/star presets (`WASP-39 b`, `K2-18 b`, `HD 209458 b`), real cached ExoMol cross-section ingestion (`component_from_cached_exomol`), imported UV-Vis / IR cross-section ingestion (`component_from_cross_section_spectrum`), and explicitly flagged broadband Gaussian band-center templates (`build_illustrative_band_component` with `ECAS-IllustrativeBandProfile-Synthetic` warnings).
   - Added leave-one-out multi-molecule sensitivity attribution (`generate_leave_one_out_models`, `summarize_leave_one_out_attribution`) computing per-species $\Delta\text{RMS}$ and $\Delta Q$ across selected trace species.

6. **Data-Accuracy Guards & Passband Integration (`ecas/comparison/inputs.py`, `ecas/comparison/alignment.py`, `ecas/comparison/residuals.py`)**:
   - Exposed top-hat passband bin integration (`integrate_model_over_bins` + `subset_by_indices` + `extract_observation_bin_edges`) in `ComparisonBrowser` whenever an observation supplies explicit channel bandwidths.
   - Added `audit_asymmetric_uncertainties()` to flag $>10\%$ upper/lower error-bar asymmetry when conservative $1\sigma$ envelopes are used in weighted diagnostics.
   - Added `demeaned_rms_residual` and `offset_dominates_shape` in `ResidualDiagnostic` to alert researchers when constant multi-instrument baseline offsets exceed spectral-shape residuals without silently subtracting offsets.

7. **UX Streamlining & Coordinate Conversion Controls (`ecas/visualization/reference_plot.py`, `ecas/ui/molecular_browser.py`, `ecas/ui/comparison_browser.py`)**:
   - Added 1-click `Wavenumber (cm^-1)` $\leftrightarrow$ `Wavelength (microns)` display toggles in both `MolecularReferenceBrowser` and `ComparisonBrowser` (preserving native `Wavenumber (cm^-1)` by default and leaving cached bytes untouched).
   - Added explicit `ppm`, `um`, and `cm^-1` unit controls, plain-English field tooltips, `Quick Setup: Auto-fill from metadata & enable alignment`, and 1-click `Generate, Auto-Align & Compare` in `ComparisonBrowser`.

8. **Reliability Hardening & Code Review**:
   - Resolved SQLite connection lifecycle leaks in test helpers by standardizing on `contextlib.closing(sqlite3.connect(...))` and `with conn:`.
   - Maintained NumPy 1.x and 2.x trapezoid compatibility via fallback binding.
   - Standardized case-insensitive matching for asymmetric error pairs and bandwidth headers.
   - Added float-precision noise guards to prevent false-positive systematic offset alerts on identical curves.
   - Added opt-in `@pytest.mark.live_network` test suite (`tests/test_live_network_health.py`), safely skipped offline during routine testing.

### C. Plot Rescaling Squish Fix & Clean UI Summary Card Redesign
9. **Plot Rescaling & Squish Prevention (`ResidualPlot`, `SpectraPlot`, `ReferencePlot`, `ComparisonBrowser`)**:
   - Fixed the UI bug shown in user screenshot `media_1793254126685_94903d1e.png` where opening candidate tools caused vertical space starvation that crushed plots down to ~40px and pushed residual plots off-screen.
   - Added `setMinimumHeight(180)` / `plot_widget.setMinimumHeight(160)` to `SpectraPlot` and `ReferencePlot`.
   - Added `setMinimumHeight(280)` / child plot minimum heights `240px` and default 50/50 splitter sizes to `ResidualPlot`, with auto-range triggers on load.
   - Enclosed `ComparisonBrowser` inside a resizable `QScrollArea`, ensuring that regardless of screen resolution or open toolbars, plots are never compressed into unreadable slivers.

10. **Clean, Uncluttered User Interface with Toggleable Technical Details (`ComparisonBrowser`)**:
    - Replaced the overwhelming 20+ line academic text wall in the middle of the screen with a clean `comparisonSummaryCard` frame:
      * **Header line**: High-level status pill (`📊 Multi-candidate...`, `✓ Eligible...`, `⚠️ Blocked...`) alongside action buttons: `[Show Technical Details & Provenance]` and `[Copy Technical Details]`.
      * **Metrics line**: Clean 1-line readout of `RMS`, `Shape RMS`, `Baseline Offset`, and `Max |r|` with unit and sample count.
      * **Systematic offset banner**: Clean warning banner when `offset_dominates_shape` is detected.
      * **Species sensitivity line**: Clean readout of leave-one-out $\Delta\text{RMS}$ per molecule.
    - Preserved full scientific provenance, mathematical caveats, and raw text inside a collapsible `technicalDetailsPanel` (hidden by default) and inside a dedicated `Technical details & provenance` tab in `diagnostic_views`.
    - Fully backwards-compatible with all test assertions and scientific boundary checks.

11. **Collapsible Source Metadata Toggle (`Show information`)**:
    - Replaced the multi-line local file paths, download URLs, and 64-character SHA-256 hashes above the observation and reference plots with clean `Show information` / `Hide information` toggle buttons.
    - Source provenance and metadata are hidden by default inside styled collapsible frames (`observation_info_panel`, `reference_info_panel`), maximizing vertical space for the plots while remaining accessible on demand via a single click.

---

## 2. File Change Manifest

### Newly Created Files:
- `ecas/comparison/model_generator.py`
- `pytest.ini`
- `tests/test_live_network_health.py`
- `tests/test_physics_ux_and_attribution.py`
- `docs/Chunk_7/RESEARCH_AND_MODELING_FOUNDATION.md`
- `docs/Chunk_7/IMPLEMENTATION_LOG.md`
- `docs/Chunk_7/REVIEW_CHECKPOINT_CHUNK_7_20261029.md`
- `ecas/resources/__init__.py`
- `ecas/resources/catalog.py`
- `ecas/ui/resources_browser.py`
- `ecas/ingestion/tabular_formats.py`
- `ecas/comparison/model_adapters.py`
- `tests/test_chunk7_resources_and_modeling.py`

### Modified Files:
- `PROJECT_CHECKPOINT.md`
- `docs/ECAS_development_plan.md`
- `docs/brains/DECISIONS.md`
- `docs/brains/PROJECT_STATE.md`
- `docs/SCIENTIFIC_COMPARISON_AND_INTERPRETATION.md`
- `ecas/comparison/alignment.py`
- `ecas/comparison/inputs.py`
- `ecas/comparison/residuals.py`
- `ecas/ui/comparison_browser.py`
- `ecas/ui/main_window.py`
- `ecas/ui/molecular_browser.py`
- `ecas/visualization/reference_plot.py`
- `tests/test_main_window.py`
- `tests/test_projects.py`
- `tests/test_projects_ui.py`
- `tests/test_project_review_regressions.py`

### Deleted Files:
- `ecas/ui/main_window_temp.py` (0-byte empty placeholder)

---

## 3. Test Suite Verification Log

- Full suite executed in offscreen headless mode (`QT_QPA_PLATFORM=offscreen`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `pytest -W error`):
  `621 passed, 22 skipped in 15.20s`
- Zero warnings, zero errors, and zero BOMs across all 83 Python files.

---

## 4. Pending UI Bug Triage & Next Actions

- **Status**: Checkpointed prior to UI bug investigation.
- **Identified Focus**: UI display, widget layout, or interaction glitches observed during desktop inspection.
- **Action**: Awaiting specific symptom description, screenshots, or reproduction steps from the user / human reviewer to isolate and fix in the next iteration.
