# ECAS — Exoplanetary Characterization & Astrochemistry Suite

ECAS is a scientific desktop software suite for exoplanetary atmospheric characterization, transmission spectroscopy, and astrochemistry. Its mission is to provide an open, transparent, and mathematically rigorous environment for inspecting, modeling, comparing, and interpreting exoplanet atmospheric observations.

The suite consolidates physical radiative-transfer modeling, molecular reference data handling, and statistical residual diagnostics with an intuitive, reproducible research workflow.

> **Latest local status (2026-10-29):** Identification now retains measured plots for blocked fits, exposes multi-input progress and atmospheric handoff, and streams supported large FITS containers. Full offscreen regression: **706 passed, 22 skipped, 0 failed, 0 warnings** under `pytest -W error` (21 opt-in network checks and one unavailable directory-symlink check). This is software verification, not calibrated molecular detection. Authoritative implementation records and limitations are maintained in [`docs/brains/PROJECT_STATE.md`](docs/brains/PROJECT_STATE.md) and [`docs/brains/DECISIONS.md`](docs/brains/DECISIONS.md).

---

## Contents

- [Core Capabilities](#core-capabilities)
  - [1. Spectral Data & Ingestion](#1-spectral-data--ingestion)
  - [2. Atmospheric Forward Modeling](#2-atmospheric-forward-modeling)
  - [3. Molecular Reference Data](#3-molecular-reference-data)
  - [4. Comparisons & Residual Diagnostics](#4-comparisons--residual-diagnostics)
  - [5. Transit & Orbit Visualizer](#5-transit--orbit-visualizer)
  - [6. Research Projects & Provenance](#6-research-projects--provenance)
  - [7. Scientific References & Resources](#7-scientific-references--resources)
  - [8. Local Molecular Identification](#8-local-molecular-identification)
- [Scientific Principles & Boundaries](#scientific-principles--boundaries)
- [Evidence Framework & Evidence Labels](#evidence-framework--evidence-labels)
- [Definition of Done](#definition-of-done)
- [Architecture & Documentation Map](#architecture--documentation-map)
- [Getting Started](#getting-started)
- [Running the Test Suite](#running-the-test-suite)
- [Development Workflow & AI Agent Instructions](#development-workflow--ai-agent-instructions)

---

## Core Capabilities

```
+----------------------------------------------------------------------------------------------------+
|                                           ECAS SUITE                                               |
+--------------------------+------------------------------+------------------------------------------+
|  OBSERVATIONAL DATA      |  FORWARD MODEL & REFERENCES  |  COMPARISON & SIMULATION                 |
|  - NASA Archive (.tbl)   |  - 1D Isothermal Limb RT     |  - Passband Bin Integration              |
|  - Astropy ECSV (.ecsv)  |  - Lecavelier Rayleigh slope |  - Exact Shared-Grid Alignment           |
|  - FITS 1D Tables        |  - ExoMol Line Lists (H2O,   |  - Residuals & Reduced Chi-Square (χ_ν²) |
|  - Generic / WASP-39 CSV |    CO2, CH4 cached sigma)    |  - Geometric Transit Simulator           |
|  - Lab FTIR / UV-Vis     |  - Multi-Molecule LOO Sens.  |  - Limb-Darkened Light Curves            |
+--------------------------+------------------------------+------------------------------------------+
|                        PERSISTENCE: SQLite Projects & Signed SHA-256 JSON                          |
+----------------------------------------------------------------------------------------------------+
```

### 1. Spectral Data & Ingestion
* **NASA Exoplanet Archive Integration**: Search planets by canonical name or alias (e.g. `WASP39b`), preview published transmission spectra, retrieve raw IPAC tables (`.tbl`), and reopen cached products offline. Preserves signed uncertainties, source URLs, retrieval dates, and all 29 original columns alongside canonical coordinate/signal aliases.
* **Broad Tabular & FITS Format Support**: Ingests Astropy ECSV (`.ecsv`), delimited ASCII tables (`.dat`, `.tsv`, `.txt`, `.asc`), and scalar FITS spectral binary tables (`.fits`, `.fit`, `.fts` with `XTENSION = 'BINTABLE'`). FITS containers up to 8 GiB are read using bounded memory; decoded spectra are limited to 100,000 rows and 1,000,000 cells. Images/event lists require spectral extraction, and multiple spectral tables require explicit selection. Raw project attachments retain their separate 16 MiB limit.
* **Local Laboratory Reference Formats**: Imports uncompressed AFFN JCAMP-DX (`.jdx`, `.dx`, `.jcamp`, `.jcm`) and the curated UV–Vis CSV schema, preserving signed measurements and source metadata through project storage.
* **Observable & Unit Distinction**: Distinguishes exoplanet transmission spectra (`observable = 'transit_depth'`, units `%`, `fraction`, or `ppm`) from laboratory FTIR/UV-Vis spectroscopy (`wavenumber` in $\text{cm}^{-1}$, `absorbance`, `transmittance`, or cross section in $\text{cm}^2/\text{molecule}$). Laboratory spectra are blocked from being mistakenly compared directly against planetary transit depths.

### 2. Atmospheric Forward Modeling
* **1D Isothermal Hydrostatic Transmission Model (`ECAS-IsothermalLimbRT`)**:
  Calculates exoplanet transmission spectra from bulk physical parameters ($R_p$, $R_\star$, $T_{\text{eq}}$, $g$, $\mu$, $P_{\text{ref}}$) by integrating optical depths along spherical-shell chord paths:
  $$\tau(b, \lambda) = 2 \int_0^{\infty} \kappa(r, \lambda) \, \rho(r) \, \mathrm{d}s$$
* **Continuum & Aerosol Physics**: Incorporates $\text{H}_2/\text{He}$ Rayleigh scattering ($\sigma \propto \lambda^{-4}$, analytically verified within $0.5\%$ of Lecavelier des Etangs et al. 2008), power-law aerosol haze slopes, and an opaque gray cloud deck floor ($P_{\text{cloud}}$).
* **Leave-One-Out Sensitivity Analysis**: Computes the individual spectral contribution and optical depth share of each molecule ($\text{H}_2\text{O}$, $\text{CO}_2$, $\text{CH}_4$, $\text{SO}_2$, $\text{CO}$, $\text{Na}$, $\text{K}$) across the observation bandpass.
* **External Code Adapters**: Standardized JSON schema adapters (`ecas-forward-model-v1`) for precomputed output from community radiative-transfer codes (`petitRADTRANS`, `POSEIDON`, `TauREx 3`, `PLATON`, `Pyrat Bay`).

### 3. Molecular Reference Data
* **ExoMol Line-List Management**: Search the ExoMol catalogue, download validated high-temperature cross-section grids ($\text{CO}_2$ UCL-4000, $\text{H}_2\text{O}$ POKAZATEL, $\text{CH}_4$ MM), and reopen cached `.sigma` products offline with local SHA-256 integrity checks.
* **Strict Real-Data Enforcement**: The forward model defaults to `cached_only` (strict ExoMol line lists). Species lacking cached data within the observation's wavenumber range are rejected with actionable guidance (`"need ~2500–3500 cm^-1"`) rather than silently substituted with synthetic band templates.
* **Transparent Badging**: Candidates are explicitly tagged in the UI as `[Real ExoMol]` or `[Synthetic Template]`.

### 4. Comparisons & Residual Diagnostics
* **Audited Passband Integration**: Automatically audits observation channel boundaries (`audit_observation_bin_semantics`). Distinguishes top-hat filter bandpasses from instrument point-spread FWHM. Integrates forward models over actual top-hat bins (`integrate_model_over_bins`) rather than applying artificial smoothing.
* **Statistical Residual Metrics**: Computes raw residuals ($r = y_{\text{obs}} - y_{\text{model}}$), RMS residual, de-meaned shape RMS, systematic baseline offset ($|\bar{r}|$), maximum absolute residual, total weighted quadratic ($q = \mathbf{r}^{\mathsf{T}} \mathbf{C}^{-1} \mathbf{r}$), and reduced chi-square:
  $$\chi_\nu^2 = \frac{q}{N}$$
* **Mathematical Noise Safeguards**: Detects near-singular noise covariance matrices using condition number threshold $\kappa > 10^{12}$ (`noise.ill_conditioned`). Flags asymmetric uncertainties ($>10\%$) and alerts when systematic offsets dominate spectral shape.
* **Attestation Integrity**: Prevents user-entered metadata overrides from conflicting with established source file facts.

### 5. Transit & Orbit Visualizer
* **2D Observer Sky View**: Real-time celestial projection showing the host star, impact parameter chord $b = \frac{a \cos i}{R_\star}$, and transiting exoplanet disc.
* **Limb-Darkened Geometric Light Curve**: Analytic calculation of the geometric transit profile with linear limb darkening:
  $$I(r) = 1 - u_1 \left(1 - \sqrt{1 - r^2}\right)$$
* **Blackbody Stellar Coloring**: Approximates the visual chromaticity of the host star from its effective temperature ($T_{\text{eff}} \in [1000, 40000]\ \text{K}$) using Tanner Helland's algorithm.
* **Interactive Scrubber & Preset Linking**: Real-time play/pause animation ($0.5\times \dots 4.0\times$), phase scrubber slider, and a one-click button to load system parameters directly into the Comparisons workspace.

### 6. Research Projects & Provenance
* **Offline Project Storage**: Organizes datasets into independent SQLite research projects.
* **Signed Array Snapshots**: Stores complete comparison records as canonical JSON envelopes (`ecas-comparison-record-v1`) with SHA-256 checksums binding input spectra, model parameters, alignment steps, and residual metrics.
* **Reproducibility Verification**: Verifies whether raw source files are present on disk or whether analysis reproduction operates from signed array snapshots.

### 7. Scientific References & Resources
* **Curated Resource Directory**: Fast-access reference library linking canonical software, archives, molecular databases, and literature citations.
* **Literature Benchmarks**: Preconfigured reference parameters for standard exoplanet benchmarks (WASP-39 b, HD 209458 b, HD 189733 b, K2-18 b, TRAPPIST-1 e).

### 8. Local Molecular Identification

Open **Comparisons → Local library: Identify Molecules**. Import a compatible laboratory observation in Spectral Data, add it to identification, and select molecules using the **IR** and **UV–Vis** checkbox groups. The real local library contains 18 IR datasets across 13 molecules and 22 UV–Vis datasets across 15 molecules; choose one explicit source/condition variant per molecule. Colours stay consistent between the plot and compact results table.

The absorption engine recovers v1's nonnegative optical-depth mixture fit, continuum terms, and same-weight **refitted drop-one** score `sqrt(max(chi²_without - chi²_full, 0))`. The historical default threshold is 3. Scores are conditional fit statistics, including an explicitly labelled residual-noise estimate when errors are absent; they are **not calibrated detection significance or evidence of atmospheric presence**.

UV–Vis cross-section-to-cross-section fitting is a separate exploratory measured-template adaptation that retains negative values. Cross-section/optical-depth mixing and planetary transit-depth inputs are blocked here. Phase conflicts, missing coverage and repeated coordinates produce explicit reasons rather than invented scores. Unknown conditions and temperature differences limit interpretation. Reference interpolation assumes continuous support; resolution and internal gaps require independent review.

Add multiple observations from the active project, filter by planet, and inspect independent results for each input. Duplicate raw products are reported without counting them as independent evidence. Export and reproduce checksum-bound input arrays, provenance, settings and results. No combined sigma across observations is calculated. See [methodology, workflow, and limits](docs/architecture/LABORATORY_IDENTIFICATION.md).

**Add observation files…** loads several inputs directly. Measured spectra remain visible before fitting and when a fit is blocked; the reason appears beside the graph. **Show selected reference spectra** displays source references separately by quantity and units. For planetary transmission observations such as WASP-39 b NIRSpec, **Open atmospheric comparison for checked inputs** transfers the observations to the physical-model tools in strict real-data mode. Atmospheric models still run one selected observation at a time and require suitable cached opacity coverage; laboratory reference selection alone cannot produce a planetary identification score.

---

## Scientific Principles & Boundaries

Scientific integrity is a non-negotiable requirement in ECAS:

1. **Residual Agreement $\ne$ Molecular Detection**: A low residual, reduced chi-square $\chi_\nu^2 \approx 1$, or favorable candidate ranking indicates numerical consistency with the specified model; it does **not** prove molecular detection, chemical abundance, or atmospheric presence. Detection claims require rigorous Bayesian model selection, nested sampling, and systematic noise characterization.
2. **Cross Sections $\ne$ Transit Depth**: Molecular cross sections ($\sigma$ in $\text{cm}^2/\text{molecule}$) describe microscopic absorption probability and cannot be rescaled into transit depth without radiative transfer.
3. **No Silent Synthetic Substitution**: When real data is selected, the application will never silently fall back to synthetic or illustrative templates.
4. **Transparent Data Provenance**: Imported and saved analyses preserve available source metadata, file checksums, user attestations, and recorded processing steps. Unknown conditions remain explicit; internal checksums do not authenticate external sources.

---

## Evidence Framework & Evidence Labels

To maintain clarity between established empirical facts, mathematical theorems, and engineering approximations, ECAS uses standardized evidence tags:

| Label | Evidence Category | Description / Typical Context |
|---|---|---|
| `[E1]` | **Direct Observation** | Raw telescope/archive data (e.g. JWST NIRSpec `.tbl` from NASA Exoplanet Archive). |
| `[E2]` | **Verified Benchmark** | Exact analytic solutions, mathematical theorems, or machine-precision tests (e.g. Lecavelier Rayleigh slope within $0.5\%$). |
| `[E3]` | **Peer-Reviewed Reference** | Published scientific literature, ExoMol line lists, HITRAN databases, or vetted bulk planet parameters. |
| `[E4]` | **Engineering Approximation** | Explicit simplifying assumptions (e.g. 1D isothermal atmosphere, hydrostatic equilibrium, top-hat bandpasses, uniform VMR). |
| `[E5]` | **Exploratory / Educational** | Illustrative models and geometric simulators (e.g. Transit & Orbit Visualizer, synthetic band templates). |

---

## Definition of Done

Any new capability or modification to ECAS must satisfy these non-negotiable criteria before being considered complete:

- [x] **Mathematical & Physical Validation**: Every forward model or numerical calculation must be accompanied by an independent analytical test or physical invariant check (e.g. dimensional consistency, scale-height proportionality, convergence with quadrature grid refinement).
- [x] **Zero Silent Fallbacks**: Ambiguous headers, incompatible units, un-cached species, or singular covariance matrices must fail visibly with descriptive scientific diagnostics rather than resorting to silent heuristics.
- [x] **Automated Regression Suite**: All tests must execute cleanly without warnings under `pytest -W error`.
- [x] **Provenance Completeness**: Analysis records must record complete input SHA-256 hashes, parameter vectors, transformation histories, and algorithm versions.
- [x] **Documentation Integrity**: Changes must be reflected in `PROJECT_STATE.md`, `DECISIONS.md`, and relevant architecture documents. Existing docstrings and scientific citations must be preserved.

---

## Architecture & Documentation Map

| Document | Purpose |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Operating guidelines and constraints for AI coding agents |
| [`docs/brains/PROJECT_STATE.md`](docs/brains/PROJECT_STATE.md) | Verified implementation status, test counts, and active baseline |
| [`docs/brains/DECISIONS.md`](docs/brains/DECISIONS.md) | Architectural and physical design decision records |
| [`docs/ecas v1 and beta comparison documents/10_29_26_ecas_beta_review_initial.md`](docs/ecas%20v1%20and%20beta%20comparison%20documents/10_29_26_ecas_beta_review_initial.md) | Comprehensive program review and 8-phase roadmap |
| [`docs/ecas v1 and beta comparison documents/ECAS_going_forward_considerations.md`](docs/ecas%20v1%20and%20beta%20comparison%20documents/ECAS_going_forward_considerations.md) | Long-term architectural, scientific, and UX consolidation strategy |
| [`docs/architecture/ARCHITECTURE.md`](docs/architecture/ARCHITECTURE.md) | System layering and subsystem responsibilities |
| [`docs/architecture/VALIDATION_STRATEGY.md`](docs/architecture/VALIDATION_STRATEGY.md) | Validation pyramid, benchmark registry, and tolerance rationales |
| [`docs/architecture/LABORATORY_IDENTIFICATION.md`](docs/architecture/LABORATORY_IDENTIFICATION.md) | Recovered v1 method, local library, independent observations, reproduction, and scientific limits |

---

## Getting Started

### 1. Prerequisites
- Python 3.10 to 3.14 (tested on Windows AMD64, Linux, and macOS).
- Git.

### 2. Clone and Setup Environment

```powershell
# Clone the repository
git clone https://github.com/brettadin/ECAS_BETA.git
cd ECAS_BETA

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On Linux / macOS:
# source .venv/bin/activate

# Install runtime dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt
```

### 3. Launch the Application

```powershell
python main.py
```

---

## Running the Test Suite

ECAS enforces strict automated testing with zero warnings:

```powershell
# Set headless platform for Qt UI tests
$env:QT_QPA_PLATFORM = "offscreen"

# Run full test suite with warning escalation
pytest -W error
```

To run offline tests exclusively (skipping live network health checks to NASA/ExoMol):
```powershell
pytest -W error -m "not live_network"
```

---

## Development Workflow & AI Agent Instructions

All contributors and AI agents working on ECAS must adhere to the instructions in [`AGENTS.md`](AGENTS.md):
1. **Never alter ExoMol case sensitivity**: Molecular identifiers in ExoMol are strictly case-sensitive (`H2O`, `CO2`, `CH4`, `SO2`).
2. **Never present numerical fits as detections**: Adhere to the scientific claim boundaries in Section 16 of the architecture review.
3. **Preserve data provenance**: Retain all raw file bytes, response headers, and SHA-256 hashes.
4. **Document decisions**: Record architectural decisions in `DECISIONS.md` and status changes in `PROJECT_STATE.md`.
