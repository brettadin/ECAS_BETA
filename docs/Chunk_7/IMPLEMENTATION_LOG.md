# ECAS Chunk 7 — Implementation Log

## Overview
Implemented **Chunk 7 — Scientific Resources, Interoperability, and Atmospheric Modeling Foundation** across `ecas/resources/`, `ecas/ui/`, `ecas/ingestion/`, `ecas/comparison/`, `docs/Chunk_7/`, and `tests/`.

## Stages Completed

### Stage 7.1 — Structured Scientific Resource Catalog & `References & Resources` Tab
- **`ecas/resources/catalog.py` & `ecas/resources/__init__.py`**:
  - Defined `CATEGORY_FILTERS = ('All', 'Software', 'Data archive', 'Molecular data', 'Python library', 'Publication')` and `EVIDENCE_STATUSES` (`reported_detection`, `independent_confirmation`, `tentative_or_disputed`, `upper_limit_or_non_detection`, `model_predicted_presence`, `not_assessed`).
  - Populated 17 verified canonical `ScientificResource` entries with clean HTTPS URLs (validated by `_verify_clean_https_url` to reject tracking query parameters), DOIs, SPDX licenses, citations, ECAS contribution summaries, and traceable `ecas_components`.
  - Added `MolecularDatabaseSpec` (`ExoMol`, `HITRAN`, `HITEMP`, `NIST Atomic Spectra Database`, `GEISA`) and `validate_temperature_applicability(database_id, temperature_k)` to flag high-temperature opacity gaps (such as using room-temperature `HITRAN` or `GEISA` above $\sim 500\,\text{K}$).
  - Added `BenchmarkPlanetRecord` and `SpeciesEvidenceRecord` for `WASP-39 b` and `K2-18 b`.
- **`ecas/ui/resources_browser.py`, `ecas/ui/main_window.py`, `ecas/ui/workspace_pages.py`**:
  - Implemented `ResourcesBrowser` with interactive category filter pills (`All`, `Software`, `Data archive`, `Molecular data`, `Python library`, `Publication`), search box, read-only resource table, detail provenance view, and `Copy link`, `Copy citation`, and `Open link` controls.
  - Added `References & Resources` to `ECASWindow` at navigation index `6` and added a corresponding shortcut in `OverviewPage`.

### Stage 7.2 — Scientific Data Interoperability, Format Expansion & Wavenumber Transformation
- **`ecas/ingestion/tabular_formats.py`**:
  - Implemented `import_ecsv_spectrum` (Astropy `# %ECSV` headers, column units, and metadata), `import_ascii_spectrum` (`.dat`, `.tsv`, `.txt`, `.asc` tables with `#`/`%` metadata headers), and `import_fits_bintable_spectrum` (zero-dependency IEEE-754 big-endian 2880-byte FITS `BINTABLE` reader).
  - Explicitly distinguished astronomical observations (`Transmission` transit depth) from laboratory FTIR/UV-Vis reference measurements (`wavenumber` + `absorbance`/`transmittance` $\rightarrow$ `axis_unit='cm^-1'`, `signal_type='Laboratory FTIR Absorbance'` / `'Laboratory FTIR Transmittance'`), preventing laboratory spectra from being promoted to `observable='transit_depth'` in `observation_input()`.
- **`ecas/comparison/alignment.py`**:
  - Added `convert_wavenumber_to_microns(item)` to convert strictly increasing wavenumbers ($\text{cm}^{-1}$) to strictly increasing wavelengths ($\mu\text{m}$ via $\lambda = 10^4 / \tilde{\nu}$), applying the exact order-reversing permutation $P$ to coordinates, values, $\boldsymbol{\sigma}$, and covariance $\mathbf{C}' = P \mathbf{C} P^{\mathsf{T}}$ so quadratic forms $\mathbf{r}^{\mathsf{T}}\mathbf{C}^{-1}\mathbf{r}$ remain invariant.
  - Extended `_SIGNAL_FACTORS` (`ppm` $\leftrightarrow$ `fraction`/`percent`) and `_AXIS_FACTORS` (`um`, `angstrom`).

### Stage 7.3 & 7.4 — External Forward-Model Adapters & Research Foundation
- **`ecas/comparison/model_adapters.py`**:
  - Defined `EXTERNAL_MODELING_SOFTWARE` evaluating `petitRADTRANS`, `POSEIDON`, `TauREx 3`, `PLATON`, and `Pyrat Bay` and linking each to its verified `ScientificResource` record.
  - Implemented `export_external_forward_model()` to convert external model curves (`microns`, `um`, SI `m`, cgs `cm`, `nm`, `angstroms`, or wavenumber `cm^-1`; `fraction`, `percent`, or `ppm`) into verified `ecas-forward-model-v1` JSON files and `LoadedForwardModel` instances, while checking molecular-database temperature applicability at `representative_temperature_k`.
- **`docs/Chunk_7/RESEARCH_AND_MODELING_FOUNDATION.md`**:
  - Documented the 10-dimension atmospheric software comparison matrix, radiative-transfer and retrieval theory, observational archives (`NASA Exoplanet Archive`, `MAST`, `ExoFOP`, `Gaia`, `Exoplanet.eu`, `VizieR`, `NASA ADS`), molecular databases, file formats, benchmark planet evidence tables (`WASP-39 b` and `K2-18 b`), and modeling integration assessment.

### Stage 7.5 & 7.6 — Cleanup, Benchmark Verification & Documentation Sync
- Removed 0-byte `ecas/ui/main_window_temp.py`.
- Added `tests/test_chunk7_resources_and_modeling.py` covering catalog integrity, UI filtering and clipboard actions, `.ecsv`/`.dat`/`.fits` ingestion, laboratory FTIR vs. planetary transit-depth separation, wavenumber-to-micron covariance permutation invariance, and end-to-end WASP-39 b benchmark forward-model comparison and persistence reproduction.

### Post-Review Physics, Data-Accuracy & UX Streamlining Increment (2026-10-29)
- **Physical 1D Limb-Transmission Forward-Model Generator (`ecas/comparison/model_generator.py`)**:
  - Implemented spherical-shell slant-chord quadrature for an isothermal hydrostatic atmosphere (`generate_isothermal_transmission_model`) with dynamic optically thin top-of-atmosphere sizing, verified against the analytical Lecavelier des Etangs et al. (2008) / Heng & Kitzmann (2017) formula (`lecavelier_analytic_transit_depth`) to $< 0.3\%$ across 4 orders of magnitude in opacity.
  - Added published planetary presets (`WASP-39 b`, `K2-18 b`, `HD 209458 b`), real cached ExoMol cross-section ingestion (`component_from_cached_exomol`), imported UV-Vis / IR cross-section ingestion (`component_from_cross_section_spectrum`), explicitly flagged broadband Gaussian band-center templates (`build_illustrative_band_component` with `ECAS-IllustrativeBandProfile-Synthetic` warning), and leave-one-out multi-molecule sensitivity attribution (`generate_leave_one_out_models`, `summarize_leave_one_out_attribution`).
- **Broader Spectral Regimes (`ecas/ingestion/tabular_formats.py`, `ecas/ui/main_window.py`)**:
  - Added explicit recognition of UV-Vis absorbance/transmittance, `cm^2/molecule` laboratory cross-section spectra, and reference emission spectra (`emission_intensity` / `line_flux`), keeping non-transit observables strictly separated from planetary transit depth. Expanded the file import dialog filter to include `.ecsv`, `.dat`, `.tsv`, `.fits`, `.fit`, and `.fts`.
- **Data-Accuracy Guards & Passband Integration (`ecas/comparison/inputs.py`, `ecas/comparison/alignment.py`, `ecas/comparison/residuals.py`)**:
  - Exposed top-hat passband bin integration (`integrate_model_over_bins` + `subset_by_indices` + `extract_observation_bin_edges`) in `ComparisonBrowser` whenever an observation supplies explicit channel bandwidths.
  - Added `audit_asymmetric_uncertainties()` to flag $>10\%$ upper/lower error-bar asymmetry when conservative $1\sigma$ envelopes are used in weighted diagnostics.
  - Added `demeaned_rms_residual` and `offset_dominates_shape` in `ResidualDiagnostic` to alert researchers when constant multi-instrument baseline offsets exceed spectral-shape residuals without silently subtracting offsets.
- **UX & Coordinate Conversion Controls (`ecas/visualization/reference_plot.py`, `ecas/ui/molecular_browser.py`, `ecas/ui/comparison_browser.py`)**:
  - Added 1-click `Wavenumber (cm^-1)` $\leftrightarrow$ `Wavelength (microns)` display toggles in both `MolecularReferenceBrowser` and `ComparisonBrowser` (preserving native `Wavenumber (cm^-1)` by default and leaving cached bytes untouched).
  - Added explicit `ppm`, `um`, and `cm^-1` unit controls, plain-English field tooltips, `Quick Setup: Auto-fill from metadata & enable alignment`, and 1-click `Generate, Auto-Align & Compare` in `ComparisonBrowser`.
- **Opt-In Live Network Health Suite (`pytest.ini`, `tests/test_live_network_health.py`) & Verification (`tests/test_physics_ux_and_attribution.py`)**:
  - Added `@pytest.mark.live_network` health checks (skipped offline unless `ECAS_RUN_LIVE_NETWORK_TESTS=1`) plus 10 offline physics, data-accuracy, and GUI workflow tests.

### Code Review & Reliability Hardening (2026-10-29)
- **SQLite Connection Lifecycle (`tests/test_projects.py`, `tests/test_projects_ui.py`, `tests/test_project_review_regressions.py`)**:
  - Standardized all raw SQLite test helper connections to `contextlib.closing(sqlite3.connect(...))` and `with conn:`. Resolved latent `ResourceWarning: unclosed database in <sqlite3.Connection>` and `PytestUnraisableExceptionWarning` in Python 3.14 under strict `pytest -W error`.
- **Defensive Error Guards & NumPy Compatibility**:
  - In `ecas/comparison/alignment.py`, wrapped `_trapezoid = getattr(np, 'trapezoid', getattr(np, 'trapz', None))` to maintain backward compatibility across NumPy 1.x and 2.x.
  - In `ecas/visualization/reference_plot.py`, guarded `reference_display_points(None)` to safely return empty point tuples rather than throwing `AttributeError`.
  - In `ecas/ui/comparison_browser.py`, safeguarded `add_current_observation` against `None` or non-dict returns from `metadata_getter()`.
  - In `ecas/comparison/inputs.py`, updated `audit_asymmetric_uncertainties()` and `extract_observation_bin_edges()` to perform case-insensitive column lookups across astronomical variants (`PL_TRANDEPERR1`/`PL_TRANDEPERR2`, `err_high`/`err_low`, `err_plus`/`err_minus`, `unc_upper`/`unc_lower`, `unc_plus`/`unc_minus`, `e_high`/`e_low`, `BANDWIDTH`, `Bin_Width`, `FWHM`).
  - In `ecas/comparison/residuals.py`, added a numerical roundoff guard (`rms_res > 1e-12 and abs(mean_res) > 1e-12`) ensuring identical or near-identical floating-point curves do not trigger false systematic offset alerts.
  - Removed stray Windows cache directory `%SystemDrive%`.
  - Verified full test suite execution: **621 passed, 22 skipped in 15.20s** under `pytest -W error` with zero warnings and zero BOMs.



