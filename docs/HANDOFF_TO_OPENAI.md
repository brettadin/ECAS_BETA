# ECAS — Agent Hand-off and Development State Briefing

**Repository:** `https://github.com/brettadin/ECAS_BETA.git`  
**Active Branch:** `master`  
**Latest Checkpoint Commit:** `c053ae2`  
**Test Suite Status:** `672 passed, 21 skipped (live network tests), 0 failed, 0 warnings` under `pytest -W error`  
**Last Updated:** 2026-10-29

---

## 1. Executive Summary & Context

ECAS (**Exoplanetary Characterization & Astrochemistry Suite**) is a scientific desktop application built in Python (PySide6, PyQtGraph, SQLite, NumPy) for exoplanet transmission spectroscopy, atmospheric forward modeling, and molecular reference data analysis.

The repository is currently undergoing a phased consolidation combining:
1. **Beta's Mathematical & Physical Rigor**: True-to-nature 1D isothermal hydrostatic limb-transmission solver (`ECAS-IsothermalLimbRT`), spherical-shell optical depth quadrature, top-hat passband bin integration, multi-molecule leave-one-out sensitivity, covariance noise conditioning ($\kappa \le 10^{12}$), and reduced chi-square ($\chi_\nu^2$).
2. **v1's Cleaner UX & Visual Capabilities**: 2D observer-frame celestial sky projection, synchronized geometric transit light curve simulation with linear limb darkening, blackbody stellar coloring, and streamlined comparison workflows.

The authoritative project roadmap and guidelines are defined in:
* `docs/ecas v1 and beta comparison documents/10_29_26_ecas_beta_review_initial.md` (Initial 8-Phase Roadmap)
* `docs/ecas v1 and beta comparison documents/ECAS_going_forward_considerations.md` (Consolidation Strategy)
* `docs/brains/PROJECT_STATE.md` (Current verified implementation status)
* `docs/brains/DECISIONS.md` (Architectural and physical design decisions)
* `README.md` (Authoritative user documentation, Definition of Done, and Evidence Framework)

---

## 2. Completed Capabilities (Up to Commit `c053ae2`)

### Priorities 1–7 Consolidation
- **Priority 1 (Bin Semantics & Alignment)**: Disentangled instrument point-spread FWHM from top-hat bin edges in `ecas/comparison/inputs.py` (`audit_observation_bin_semantics`). Passband integration (`integrate_model_over_bins`) is explicitly separated from point-grid linear interpolation.
- **Priority 2 (Forward-Model Benchmarks)**: Parameter bounds defined in `ecas/comparison/model_generator.py` ($T \in [150, 3000]\ \text{K}$, $g \in [1, 100]\ \text{m/s}^2$, $H/R_p \le 0.25$, $P \in [10^{-6}, 10^2]\ \text{bar}$). Backed by 11 analytical benchmark tests in `tests/test_forward_model_physics.py` (Lecavelier analytic Rayleigh slope $\alpha=-4$ within $0.5\%$, $H \propto T/g$ linearity, VMR scaling, cloud floor, quadrature convergence).
- **Priority 3 (Pure Real-Data Enforcement)**: `cached_only` ExoMol opacity mode is default. Block non-overlapping species with specific wavenumber requirements (`need ~2500–3500 cm^-1`). Candidate badges distinguish `[Real ExoMol]` from `[Synthetic Template]`.
- **Priority 4 (Statistical Diagnostics)**: Added reduced chi-square $\chi_\nu^2 = q / N$ to `ResidualDiagnostic` in `ecas/comparison/residuals.py`. Added ill-conditioned covariance matrix check ($\kappa > 10^{12}$) in `ecas/comparison/eligibility.py` (`left.noise.ill_conditioned`).
- **Priority 5 (Attestation Integrity)**: Conflict detection in `ComparisonBrowser._build_attested_observation` prevents user overrides from contradicting source facts. Structured metadata into `source_provided`, `user_attested`, and `bin_derived`.
- **Priority 6 (Reproducibility & Persistence)**: Explicit raw file disk verification vs signed array snapshots in `reproduce_selected_comparison`.
- **Priority 7 (Testing Baseline)**: Zero-warning test suite execution (**672 passed, 21 skipped, 0 failed** in 31s).

### v1 Visual Recovery: Transit & Orbit Visualizer
- Implemented `TransitVisualizerPage` in `ecas/ui/transit_view.py`:
  - Observer-frame celestial sky projection (`SkyViewWidget`) with host star, transit chord $b = (a \cos i)/R_\star$, and moving planet disk.
  - Analytic geometric transit light curve with linear limb-darkening: $I(r) = 1 - u_1 (1 - \sqrt{1 - r^2})$.
  - Tanner Helland stellar blackbody temperature color approximation (`teff_to_hex`).
  - Real-time animation playback ($0.5\times \dots 4.0\times$), scrubbing slider, and 1-click `"Open in Comparisons Workspace"` linking.
  - Verified in `tests/test_transit_view.py` (8 passing tests).

### Phase 8 Documentation & UI Bug Fixes
- **Documentation**: Synchronized `README.md`, `PROJECT_STATE.md`, and `DECISIONS.md`. Embedded the formal **Definition of Done** and **Evidence Labels** (`[E1]` to `[E5]`).
- **UI Bug Fix 1 (Issue 1)**: Added 1-click `⚡ Generate Forward Model & Compare` button to summary card when a raw cross section ($\text{cm}^2/\text{molecule}$) is selected, clarifying that cross sections require radiative transfer before comparison against transit depth ($\%$).
- **UI Bug Fix 2 (Issue 2)**: Added dedicated `−` and `+` step buttons next to all Transit Visualizer spinboxes, widened the control panel, and set `cosmetic=True` on sky view pens to prevent strokes from scaling to stellar radii in data units.
- **UI Bug Fix 3 (Issue 3)**: Clarified that real downloadable ExoMol line lists are strictly **$\text{H}_2\text{O}$, $\text{CO}_2$, and $\text{CH}_4$**. In `cached_only` mode, synthetic-only template species ($\text{SO}_2$, $\text{CO}$, $\text{NO}_2$, $\text{Na}$, $\text{K}$) are automatically unchecked and disabled with helpful tooltips.
- **UI Bug Fix 4 (Issue 4)**: Fixed forward-model candidate display so generating a model always selects and plots Candidate `[0]` (the Full Model with the user's molecules), preventing auto-selection of the leave-one-out flat continuum baseline (`without-molecule`). Added clear plot titles and auto-scrolling to the diagnostic view.

---

## 3. Non-Negotiable Scientific & Engineering Rules

Any agent continuing work on this codebase must adhere to these invariants:
1. **Case-Sensitivity in ExoMol**: Never alter case-sensitive searching in the ExoMol catalogue (`H2O`, `CO2`, `CH4`, `SO2`).
2. **Never Overclaim Detection**: Numerical residual agreement, low RMS, $\chi_\nu^2 \approx 1$, or candidate ranking does **not** constitute proof of molecular detection or atmospheric abundance. Never generate text claiming a molecule has been "detected" or "confirmed" without Bayesian model selection and systematic noise analysis.
3. **Pure Real-Data Rule**: Never silently substitute synthetic band templates when real reference data (`cached_only`) is requested. If real data is missing, fail visibly with specific wavenumber requirements.
4. **Physical Dimension Guard**: Raw molecular cross sections ($\text{cm}^2/\text{molecule}$) must never be directly subtracted from or rescaled into planetary transit depths ($\%$) without an explicit radiative-transfer model.
5. **Testing Standard**: Run all tests offscreen with warning escalation:
   ```powershell
   $env:QT_QPA_PLATFORM = "offscreen"
   pytest -W error
   ```
   Do not commit code that produces warnings or failures.
6. **Documentation Continuity**: Record architectural decisions in `docs/brains/DECISIONS.md` and status changes in `docs/brains/PROJECT_STATE.md`.

---

## 4. Pending Tasks for Next Session

1. **Awaiting User Input**: The user (Blake & Brett) will provide updated instructions and current accurate databases.
2. **Phase 7: Real-World Ingestion & Laboratory Data Workflows**:
   - Ingest and validate real laboratory FTIR / UV-Vis spectrophotometer tables (e.g. from NIST or HITRAN) using `ecas/ingestion/tabular_formats.py`.
   - Ensure laboratory absorbance/transmittance spectra display cleanly without entering transmission transit-depth comparisons.
3. **v1 UX Recovery (Sections 10 & 14)**:
   - Progressive disclosure: 3-tier view modes (Guided vs Advanced vs Expert) in Comparisons to reduce visual complexity for newcomers while preserving full parameter control for researchers.
   - Molecule vibrational absorption band indicators on spectra plots (marking diagnostic reference bands like $4.3\ \mu\text{m}$ $\text{CO}_2$, $1.4/1.9/2.7\ \mu\text{m}$ $\text{H}_2\text{O}$) without asserting detections.
4. **Deep-Dive Audits (Section 18)**:
   - Investigation A: End-to-end trace of a real observation from raw NASA archive table to an exported self-contained reproducible research package (`.json`).
   - Investigation B: Literature benchmark reproduction against published JWST WASP-39 b transmission spectra (NIRSpec PRISM / G395H).
