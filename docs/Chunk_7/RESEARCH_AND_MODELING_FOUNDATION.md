# ECAS Chunk 7 — Scientific Research and Modeling Foundation

## 1. Purpose and Scope

This document establishes the peer-reviewed scientific, archival, spectroscopic, and computational foundation for **Chunk 7** of **ECAS — Exoplanetary Characterization & Astrochemistry Suite**. Every architectural choice, data importer, alignment transformation, and resource catalog entry in Chunk 7 is grounded in primary literature, official archive documentation, and reproducible computational contracts.

Core scientific integrity rules enforced throughout ECAS:
1. **Strict Domain Separation**: Observational spectra, laboratory FTIR/UV-Vis measurements, theoretical molecular cross sections ($\text{cm}^2\,\text{molecule}^{-1}$), synthetic forward models, and Bayesian retrieval posteriors are distinct scientific artifacts and are never conflated.
2. **No Visual-Match Detection Claims**: Visual similarity or candidate ranking between a reference curve and an observation is never presented as a molecular detection or abundance measurement.
3. **Explicit Provenance & Reproducibility**: Every imported spectrum, cached reference product, and external forward model carries its source SHA-256 digest, explicit coordinate/signal units, and transformation history.

---

## 2. Evaluation of Established Atmospheric Modeling Software

| Dimension | `petitRADTRANS` | `POSEIDON` | `TauREx 3` | `PLATON` | `Pyrat Bay` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Observing Modes** | Transmission, thermal emission/eclipse, direct imaging, high-res CCF | 1D/2D/3D transmission, thermal emission/eclipse | Transmission, thermal emission, phase curves | Transmission, secondary eclipse/thermal emission | Transmission, thermal emission |
| **2. Radiative Transfer** | 1D plane-parallel chord integration (transmission); Feautrier / two-stream scattering (emission) | 1D/2D/3D cylindrical ray-tracing across terminator/day-night sectors | Plugin-based 1D plane-parallel optical-depth integration | Fast 1D hydrostatic plane-parallel optical-depth integration | 1D plane-parallel line-by-line or opacity-sampling integration |
| **3. Opacity Treatment** | Correlated-$k$ ($R \approx 1000$) and line-by-line ($R \sim 10^6$) HDF5 grids | Opacity sampling on high-resolution HDF5 cross-section grids | Cross-section (`.xsec` / HDF5) or correlated-$k$ (`.ktables`) | Pre-tabulated $(T, P, \lambda)$ absorption cross-section grids | Line-by-line compilation from ExoMol/HITRAN/HITEMP into cross-section grids |
| **4. Chemistry Modes** | Free VMR profiles, equilibrium (`easychem` / `FastChem`), quench-pressure disequilibrium | Uniform/profile/sector free VMR, equilibrium chemistry grid interpolation | Constant/two-layer free VMR, `ACE` / `FastChem` equilibrium, plugins | Equilibrium chemistry ($Z$, $\text{C/O}$) or free species VMR | `TEA` thermochemical equilibrium or uniform free VMR |
| **5. T–P Parameterizations** | Isothermal, Guillot (2010), Madhusudhan & Seager (2009), spline nodes | Isothermal, Guillot (2010), Madhusudhan & Seager (2009), 2D/3D sector gradients | Isothermal, N-point profile, Guillot (2010), radiative equilibrium | Isothermal, Guillot (2010), parametric T–P nodes | Isothermal, Guillot (2010), Madhusudhan & Seager (2009), T–P knots |
| **6. Clouds & Hazes** | Power-law haze slope, gray cloud deck, Ackerman & Marley Mie condensates | Patchy sector clouds, gray cloud deck, power-law haze, Mie aerosols | Gray cloud deck, Lee et al. Mie droplets, Rayleigh slope | Cloud-top pressure $P_{\text{cloud}}$, scattering slope $\alpha$, Mie condensates | Gray cloud deck, Lecavelier des Etangs Rayleigh haze |
| **7. Retrieval Samplers** | `PyMultiNest`, `UltraNest`, `emcee` | `PyMultiNest` | `MultiNest`, `UltraNest`, `Nestle`, `dynesty`, `emcee` | `dynesty`, `emcee` | `MC3` (DEMC / Snooker MCMC), `MultiNest` |
| **8. Data Footprint & Perf.** | ~5–50+ GB HDF5 opacity tables; Fortran/Numba/JAX kernels | ~10–30 GB HDF5 cross-section database; Numba/MPI acceleration | ~1–20 GB `.xsec` / $k$-tables; Python + Numba/C extensions | ~1–4 GB pre-gridded tables; CPU/Numba/CUDA | ~2–25 GB line lists / cross sections; Python + C extensions |
| **9. Primary Citation & DOI** | Mollière et al. (2019), *A&A* 627, A67 (`10.1051/0004-6361/201935470`) | MacDonald & Madhusudhan (2017); MacDonald (2023) (`10.21105/joss.04873`) | Al-Refaie et al. (2021), *ApJ* 917, 37 (`10.3847/1538-4357/ac0252`) | Zhang et al. (2019, 2020), *ApJ* 899, 27 (`10.3847/1538-4357/aba1e6`) | Cubillos & Blecic (2021), *MNRAS* 505, 2675 (`10.1093/mnras/stab1405`) |
| **10. License & ECAS Role** | **MIT** — Primary external forward-model source via `ecas.comparison.model_adapters` | **BSD-3-Clause** — Supported external 1D/multi-D forward-model source | **BSD-3-Clause** — Supported external forward-model source ($\text{cm}^{-1}$ or $\mu\text{m}$) | **MIT** — Supported lightweight external forward-model source (SI $\text{m}$ to $\mu\text{m}$) | **GPL-2.0-only** — External output file ingestion only; never linked or bundled |

### Additional Specialized Packages and Inference Libraries Evaluated
- **Radiative Transfer & Instrument Systematics**: `HELIOS` (Malik et al. 2017, self-consistent radiative-convective equilibrium), `ARCiS` (Min et al. 2020, cloud microphysics & retrieval), `ExoTiC-ISM` / `ExoTiC-LD` (Laginja & Wakeford 2020; Grant & Wakeford 2024, instrument systematics marginalization and stellar limb darkening).
- **Bayesian Sampling & Inference Libraries**: `emcee` (Foreman-Mackey et al. 2013, `10.1086/670067`, MIT), `dynesty` (Speagle 2020, `10.1093/mnras/staa278`, MIT), `UltraNest` (Buchner 2021, `10.21105/joss.03001`, GPL-3.0), and `BlackJAX` (Apache-2.0).

---

## 3. Atmospheric Science Foundations

### 3.1 Observing Modes and Physical Observables
1. **Transmission Spectroscopy**: Measures wavelength-dependent effective transit depth $\Delta F(\lambda) / F_* = [R_p(\lambda) / R_*]^2$ along the planetary limb chord during primary transit:
   $$R_p^2(\lambda) = R_0^2 + 2 \int_{R_0}^{\infty} \left[1 - \exp\left(-\tau_{\text{chord}}(r, \lambda)\right)\right] r \, dr$$
   where $\tau_{\text{chord}}(r, \lambda) = \sum_i \int_{-\infty}^{\infty} n_i(s)\,\sigma_i(\lambda, T(s), P(s))\,ds$ is the slant optical depth along impact parameter $r$. Because $\sigma_i(\lambda, T, P)$ is integrated over altitude, temperature, pressure, and multiple absorbers/clouds, **a single-temperature molecular absorption cross section $\sigma_i(\tilde{\nu})$ in $\text{cm}^2\,\text{molecule}^{-1}$ is physically distinct from transit depth $[R_p(\lambda)/R_*]^2$**.
2. **Thermal Emission / Secondary Eclipse Spectroscopy**: Measures disk-integrated emergent planetary flux relative to stellar flux $F_p(\lambda)/F_*(\lambda)$ across vertical optical depth $\tau_\nu$, strongly sensitive to the vertical $T(P)$ gradient and thermal inversions.
3. **Direct-Imaging Spectroscopy**: Measures absolute or contrast-calibrated emergent flux $F_p(\lambda)$ of young, self-luminous companions at wide angular separations.
4. **High-Resolution Cross-Correlation Spectroscopy (HRCCS)**: Resolves individual rotational-vibrational lines ($R \sim 25{,}000\text{--}100{,}000$), separating planetary Doppler shifts from telluric and stellar lines via cross-correlation functions (CCF) and log-likelihood mappings.
5. **Phase-Resolved Spectroscopy**: Tracks longitudinal brightness and chemical/cloud variations across a full orbital revolution.

### 3.2 Forward Modeling vs. Parameter Estimation vs. Atmospheric Retrieval vs. Model Comparison
- **Forward Modeling**: Computes a deterministic synthetic spectrum $\mathbf{m}(\boldsymbol{\theta})$ from explicitly specified physical parameters $\boldsymbol{\theta}$ (fixed $T(P)$, abundances, gravity, radii, clouds, and opacity sources).
- **Parameter Estimation**: Evaluates the posterior probability distribution $p(\boldsymbol{\theta} \mid \mathbf{d}, M) \propto \mathcal{L}(\mathbf{d} \mid \boldsymbol{\theta}, M)\,\pi(\boldsymbol{\theta} \mid M)$ conditioned on a single model $M$ and explicit prior $\pi(\boldsymbol{\theta} \mid M)$.
- **Atmospheric Retrieval**: Combines a parameterized forward model with MCMC or nested sampling to infer posterior credible intervals and parameter degeneracies (e.g., the $(R_0, P_0, \text{VMR}, P_{\text{cloud}})$ degeneracy in transmission spectra).
- **Statistical Model Comparison**: Evaluates the Bayesian evidence (marginal likelihood) $Z_M = \int \mathcal{L}(\mathbf{d} \mid \boldsymbol{\theta}, M)\,\pi(\boldsymbol{\theta} \mid M)\,d\boldsymbol{\theta}$ across competing models $M_1, M_2$ via the Bayes factor $B_{12} = Z_1 / Z_2$. **In ECAS, $\chi^2$, reduced $\chi^2_\nu$, and RMSE are goodness-of-fit and candidate-ordering metrics only—never Bayesian evidence ratios or detection significances.**

---

## 4. Observational Archives & Programmatic Retrieval

| Archive | Primary Holdings | Programmatic Access | Identifier & Provenance Fields |
| :--- | :--- | :--- | :--- |
| **NASA Exoplanet Archive** (`atmospheres` & `ps`) | Published exoplanet transmission & emission tables, composite planetary/stellar parameters | TAP `/TAP/sync` (ADQL) & bulk IPAC `.tbl` / `.csv` (`10.26133/NEA36`) | `pl_name`, `spec_type`, `instrument`, `facility`, `reference`, `centralwavelng`, `pl_trandep`, `source_sha256` |
| **MAST (STScI)** | Calibrated JWST, HST, Kepler, and TESS time-series and 1D extracted spectra | `astroquery.mast` / CAOM REST API & FITS/ECSV HLSP bundles | `obs_id`, `proposal_id`, `target_name`, `instrument_name`, `calib_level`, DOI |
| **ExoFOP** | Community follow-up photometry, radial velocities, stellar parameters, and target notes | REST/HTTP table exports by TIC/TOI/planet identifier | TIC ID, TOI ID, contributor, upload timestamp |
| **Gaia Archive (ESA)** | High-precision stellar parallaxes, spectrophotometry, and host-star radii $R_*$ | TAP+ ADQL service (`gea.esac.esa.int/tap-server/tap`) | `source_id` (DR3), release tag, astrometric/photometric uncertainties |
| **Exoplanet.eu** | European catalog of confirmed and candidate exoplanets and bibliography | TAP/VOTable and CSV catalog downloads | Planet name, discovery/characterization reference, update date |
| **VizieR (CDS)** | Published journal spectral and photometric appendices in standardized VOTable/ASCII/FITS | TAP / `astroquery.vizier` by J/journal/volume catalog ID | CDS catalog ID (e.g., `J/A+A/...`), Bibcode, table name |
| **NASA ADS** | Bibliographic records, DOIs, Bibcodes, and links to arXiv and journal data products | REST API (`api.adsabs.harvard.edu`) | 19-character Bibcode, DOI, publication year, author list |

---

## 5. Molecular Spectroscopy Databases & Temperature Applicability

| Database | Typical Temperature Range | Spectral Coverage | Primary Formats | Best-Fit Atmospheric Regime | Key Limitation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ExoMol** | $100\text{--}3000+\,\text{K}$ | UV/Visible to far-IR / microwave | `.states`, `.trans`, `.broad`, `.xsec` (`cm^-1`, `cm^2/molecule`) | Hot Jupiters, warm Neptunes, sub-Neptunes, brown dwarfs ($T > 400\,\text{K}$) | High-temperature line lists contain $10^9\text{--}10^{11}$ transitions; cross sections require explicit $(T, P)$ broadening assumptions |
| **HITRAN** | $200\text{--}400\,\text{K}$ ($T_{\text{ref}} = 296\,\text{K}$) | Microwave to UV | 160-char `.par` transitions, `.xsec` cross sections | Terrestrial and temperate exoplanet atmospheres ($T \lesssim 400\,\text{K}$) | **Incomplete at $T \gtrsim 500\,\text{K}$** due to missing hot bands; produces underestimated opacity in hot-Jupiter atmospheres |
| **HITEMP** | $300\text{--}3000\,\text{K}$ | Infrared to visible | HITRAN-format `.par` line lists with hot bands | Hot Jupiters and warm gas giants ($\text{H}_2\text{O}$, $\text{CO}_2$, $\text{CO}$, $\text{CH}_4$, $\text{NO}$, $\text{OH}$, $\text{N}_2\text{O}$, $\text{NO}_2$) | Restricted to 8 core molecules; requires ExoMol for broader chemical species |
| **NIST ASD** | $1000\text{--}50{,}000\,\text{K}$ | X-ray, UV, optical, near-IR | ASCII / CSV / HTML transition tables | Atomic and ionic lines ($\text{Na}\,\text{I}$, $\text{K}\,\text{I}$, $\text{He}\,\text{I}$ $10833\,\text{\AA}$, $\text{Fe}\,\text{I/II}$) in upper atmospheres | Atomic/ionic transitions only; does not provide molecular ro-vibrational bands |
| **GEISA** | $200\text{--}400\,\text{K}$ ($T_{\text{ref}} = 296\,\text{K}$) | Infrared to visible | Fixed-width ASCII transition & cross-section records | Temperate planetary atmospheres and giant-planet tropospheres | Like HITRAN, missing high-$J$ hot bands above $\sim 500\,\text{K}$ |

ECAS enforces these bounds programmatically via `validate_temperature_applicability()` in `ecas/resources/catalog.py` and `export_external_forward_model()` in `ecas/comparison/model_adapters.py`.

---

## 6. File Formats, Data Interoperability & Wavenumber Transformation

Chunk 7 extends ECAS's ingestion and alignment capabilities while preserving existing CSV and NASA IPAC `.tbl` contracts:
- **Supported Formats**:
  - `.csv`: Generic (`wavelength`, `signal`, `uncertainty`) and `WASP39B_SCHEMA` (`ecas/ingestion/csv_importer.py`).
  - `.tbl`: Strict 4-header NASA Exoplanet Archive IPAC transmission tables (`ecas/ingestion/nasa_table.py`).
  - `.ecsv`: Astropy Enhanced Character-Separated Values with `# %ECSV` YAML column units and metadata (`ecas/ingestion/tabular_formats.py`).
  - `.dat`, `.tsv`, `.txt`, `.asc`: Delimited scientific ASCII spectra with `#`/`%` metadata headers (`ecas/ingestion/tabular_formats.py`).
  - `.fits`, `.fit`, `.fts`: IEEE-754 big-endian FITS 1D spectral binary tables (`XTENSION = 'BINTABLE'`, `TTYPEn`, `TFORMn`, `TUNITn`) (`ecas/ingestion/tabular_formats.py`).
- **Laboratory FTIR/UV-Vis vs. Planetary Observation Separation**:
  - When an ASCII or ECSV table declares `wavenumber` and `absorbance` or `transmittance`, `tabular_formats.py` tags `axis_unit='cm^-1'` and `signal_type='Laboratory FTIR Absorbance'` (or `'Laboratory FTIR Transmittance'`) and emits an explicit warning that laboratory spectra are not planetary transit-depth observations.
  - In `ecas/comparison/inputs.py`, `observation_input()` maps only `'Transmission'` to `observable='transit_depth'`, so laboratory FTIR spectra are blocked by `assess()` from being compared directly as planetary transit depth.
- **Explicit Wavenumber-to-Wavelength Transformation (`convert_wavenumber_to_microns`)**:
  - Because $\lambda\,(\mu\text{m}) = 10^4 / \tilde{\nu}\,(\text{cm}^{-1})$ reverses coordinate ordering, `convert_wavenumber_to_microns()` in `ecas/comparison/alignment.py` applies the exact order-reversing permutation $P$ ($P_{i, n-1-i} = 1$) to coordinates, values, $\boldsymbol{\sigma}$, and covariance $\mathbf{C}' = P \mathbf{C} P^{\mathsf{T}}$, preserving the generalized quadratic form $\mathbf{r}^{\mathsf{T}}\mathbf{C}^{-1}\mathbf{r}$ to machine precision.

---

## 7. Published Exoplanet Characterization Benchmarks

ECAS records published characterization conclusions using six distinct `EvidenceStatus` classifications (`ecas/resources/catalog.py`):
- `reported_detection`
- `independent_confirmation`
- `tentative_or_disputed`
- `upper_limit_or_non_detection`
- `model_predicted_presence`
- `not_assessed`

### Benchmark 1: WASP-39 b (JWST Transiting Exoplanet Community ERS Program)
- **Primary Data & Citations**: JWST NIRSpec PRISM ($0.5\text{--}5.5\,\mu\text{m}$, JWST ERS Program 1366, 2023, *Nature* 614, 649, `10.1038/s41586-022-05269-w`), NIRISS SOSS (Feinstein et al. 2023, *Nature* 614, 670, `10.1038/s41586-022-05674-1`), NIRSpec G395H (Alderson et al. 2023, *Nature* 614, 664, `10.1038/s41586-022-05591-3`), and photochemistry analysis (Tsai et al. 2023, *Nature* 617, 483, `10.1038/s41586-023-05902-2`).
- **Species Evidence Classification**:
  - $\text{CO}_2$ ($4.3\,\mu\text{m}$): **`independent_confirmation`** ($26\,\sigma$ detection in NIRSpec PRISM; independently confirmed in NIRSpec G395H and NIRCam).
  - $\text{H}_2\text{O}$ ($0.9\text{--}3.0\,\mu\text{m}$): **`independent_confirmation`** (multiple resolved bands across NIRISS SOSS, NIRSpec PRISM/G395H, NIRCam).
  - $\text{SO}_2$ ($4.05\,\mu\text{m}$): **`independent_confirmation`** (detected in NIRSpec G395H & PRISM and explained by photochemical models, Tsai et al. 2023).
  - $\text{Na}$ ($0.59\,\mu\text{m}$) & $\text{K}$ ($0.77\,\mu\text{m}$): **`reported_detection`** (NIRSpec PRISM & NIRISS SOSS optical alkali features).
  - $\text{CO}$ ($4.6\text{--}5.0\,\mu\text{m}$): **`reported_detection`** (broad $4.7\,\mu\text{m}$ absorption contribution in NIRSpec G395H/PRISM).
  - $\text{CH}_4$ ($3.3\,\mu\text{m}$): **`upper_limit_or_non_detection`** (absence of $3.3\,\mu\text{m}$ peak places strong upper limit $\text{VMR}_{\text{CH}_4} \lesssim 5 \times 10^{-6}$, consistent with high metallicity and vertical quenching).
  - $\text{H}_2\text{S}$: **`tentative_or_disputed`** (weak/model-dependent retrieval constraints in NIRSpec G395H).

### Benchmark 2: K2-18 b (JWST Temperate Sub-Neptune Transmission Spectroscopy)
- **Primary Citation**: Madhusudhan et al. (2023), *ApJL* 956, L13 (`10.3847/2041-8213/acf577`) and follow-up re-analyses.
- **Species Evidence Classification**:
  - $\text{CH}_4$ ($1\text{--}5\,\mu\text{m}$) & $\text{CO}_2$ ($4.3\,\mu\text{m}$): **`reported_detection`** (JWST NIRISS SOSS + NIRSpec G395H transmission bands).
  - $\text{H}_2\text{O}$, $\text{NH}_3$, $\text{CO}$: **`upper_limit_or_non_detection`** (non-detections used to discuss cold-trap and interior/ocean scenarios).
  - $\text{DMS}$ ($(\text{CH}_3)_2\text{S}$): **`tentative_or_disputed`** (marginal, prior- and baseline-offset-dependent inference; not an established detection).

---

## 8. ECAS Modeling Integration Assessment

We evaluated three architectural options for integrating atmospheric forward modeling into ECAS:
- **Approach A (Direct Hard Dependency on `petitRADTRANS` / `POSEIDON` / `TauREx 3` / `PLATON`)**: Rejected for the core desktop installation because it requires compiled Fortran/C/CUDA toolchains and 5–50 GB of external opacity tables, which would break lightweight cross-platform reproducibility.
- **Approach B (Built-in Unvalidated Toy Transmission Formula)**: Rejected because simplified single-scale-height isothermal approximations without pressure-broadened multi-species opacities violate ECAS's scientific integrity requirement against unvalidated physical projections.
- **Approach C (Selected — Verified External Forward-Model Adapters + `ecas-forward-model-v1` Provenance Contract)**:
  - Implemented in `ecas/comparison/forward_model.py` and `ecas/comparison/model_adapters.py`.
  - Allows researchers to generate synthetic spectra in established community packages (`petitRADTRANS`, `POSEIDON`, `TauREx 3`, `PLATON`, `Pyrat Bay`) and import/export them into ECAS with full `AtmosphericModelProvenance`, SHA-256 verification, native coordinate/signal conversion (`m`, `cm`, `cm^-1`, `ppm`), software citation metadata, and molecular-database temperature-applicability validation.

