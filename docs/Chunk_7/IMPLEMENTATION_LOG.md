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

