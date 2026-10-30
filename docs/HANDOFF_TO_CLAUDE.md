# ECAS UI Exploration & Architecture Hand-off for Claude

**Date:** 2026-10-30  
**Repository:** https://github.com/brettadin/ECAS_BETA  
**Local Workspace:** `c:\AI-Projects\Bwett AI Project UwU\ECAS_BETA`  
**Git Baseline:** Tag `checkpoint-20261030-pre-claude-ui` on branch `claude/ui-exploration` (branched from `master` at `5a41fd7`)  
**Test Suite Status:** **707 passed, 21 skipped (network health tests), 0 failures, 0 warnings (`pytest -W error`)**  

---

## 1. Welcome & Primary Mission

Welcome, Claude! Blake and Brett have invited you to explore, polish, and modernize the User Interface (UI/UX) of **ECAS** (Exoplanetary Characterization & Astrochemistry Suite). 

This hand-off document is your safety net. A local git checkpoint and dedicated branch (`claude/ui-exploration`) have been created so you can freely experiment, redesign, and polish the interface without any risk of losing project context, scientific invariants, or roadmap momentum.

---

## 2. Non-Negotiable Ground Rules & Scientific Invariants

When modifying UI components, styling, or workflows, you **must preserve** these verified scientific and operational constraints:

1. **Ask Before Pushing to GitHub**:  
   Blake has an absolute rule: **Never execute `git push` without Blake's explicit confirmation in chat.** Keep your commits local on your branch.
2. **Pure Real-Data Rule (Zero Synthetic Fallback)**:  
   In strict `cached_only` mode, the app must never silently substitute synthetic broadband templates when real data is requested. Un-cached molecules must be transparently disabled with informative tooltips.
3. **Cross-Section vs. Transit Depth Physical Guard**:  
   Raw laboratory absorption cross sections ($\text{cm}^2/\text{molecule}$) must **never** be directly subtracted from or compared to exoplanetary transit depths ($\%$) without an explicit radiative-transfer forward model. If a user selects both, the UI must explain the dimensional incompatibility and guide them to forward modeling or atmospheric handoff.
4. **ExoMol Catalogue Casing**:  
   ExoMol molecular searches are strictly case-sensitive (`H2O`, `CO2`, `CH4`, `SO2`). Do not normalize them to lowercase or uppercase.
5. **No Overclaiming Molecular Detection**:  
   Numerical residual agreement, low RMS, $\chi_\nu^2 \approx 1$, or candidate ranking does **not** constitute empirical proof of molecular detection or atmospheric abundance. All labels and status bars must honestly reflect "conditional fit improvement" or "numerical agreement", not "detection confirmed".
6. **Strict Test Passing with Zero Warnings**:  
   Always run test verification headless with warning escalation:
   ```powershell
   $env:QT_QPA_PLATFORM = "offscreen"
   .\.venv\Scripts\pytest -W error
   ```
   No deprecation warnings or test failures are tolerated.

---

## 3. UI Component Map

The application is built on **PySide6 (Qt for Python)** and **PyQtGraph** for fast, hardware-accelerated 2D spectral plots.

| View / Module | File Path | Purpose & Current State |
|---|---|---|
| **Main Window** | `ecas/ui/main_window.py` | Top-level sidebar navigation (`QListWidget`), dark theme palette, status bar, and central `QStackedWidget`. |
| **Overview** | `ecas/ui/overview_view.py` | Welcome dashboard, quick navigation shortcuts, session status summaries. |
| **Projects** | `ecas/ui/projects_view.py` | Project workspace management (SQLite-backed), saving/reopening sessions, metadata cards. |
| **Spectral Data** | `ecas/ui/data_view.py` | Primary data ingestion: NASA Exoplanet Archive queries, local CSV/ASCII/FITS import, dataset inspection. |
| **Molecular References** | `ecas/ui/reference_browser.py` | ExoMol catalogue search, cached cross-section downloads, reference plot & data table inspection. |
| **Comparisons** | `ecas/ui/comparison_browser.py` | Observation vs. reference comparison, 1D forward model generation, leave-one-out candidate ranking, residual diagnostics. |
| **Transit Visualizer** | `ecas/ui/transit_view.py` | Interactive 2D observer sky projection of exoplanetary transit, analytic limb-darkened light curve, scrub bar, playback timer, stellar presets. |
| **Identify (Laboratory)** | `ecas/ui/identification_panel.py` | Laboratory FTIR (`.jdx`) & UV-Vis (`.csv`) spectral decomposition, bounded non-negative optical depth fitting, measured preview, atmospheric handoff. |
| **Spectral Plots** | `ecas/visualization/spectra_plot.py` | Main observation plot widget (PyQtGraph) with pan/zoom, error bars, hover readouts. |
| **Reference Plots** | `ecas/visualization/reference_plot.py` | Molecular cross-section plot widget with wavenumber $\leftrightarrow$ wavelength toggle. |
| **Residual Plots** | `ecas/visualization/residuals_plot.py` | Difference and weighted-residual diagnostic plot widget. |

---

## 4. High-Impact UI Improvements Claude Can Tackle

Here are specific areas where your UI/UX design can make ECAS shine:

### A. Progressive Disclosure in Comparisons & Diagnostics
* **Problem**: The Comparisons tab computes rich diagnostic information (reduced $\chi_\nu^2$, condition number $\kappa$, baseline offset, covariance status, leave-one-out $\Delta\text{RMS}$), but exposing all technical details at once can overwhelm users.
* **Goal**: Implement collapsible technical disclosure tiers. The default view should show a clean, elegant **Summary Card** (Candidate name, $\chi_\nu^2$, primary molecule sensitivity), with an expandable **"🔬 Technical Diagnostics"** accordion revealing covariance health, degrees of freedom, and quadrature convergence.

### B. Absorption Band Reference Indicators on `spectra_plot.py`
* **Problem**: When examining a transmission spectrum (e.g. WASP-39 b from 0.5 to 5.5 $\mu\text{m}$), researchers have to mentally remember where molecular absorption peaks are located.
* **Goal**: Add a toggleable **"Molecular Absorption Bands"** overlay on the main spectrum plot. When checked (or selected via a dropdown for $\text{H}_2\text{O}$, $\text{CO}_2$, $\text{CH}_4$, $\text{SO}_2$):
  - Draw subtle, semi-transparent vertical bands or top-axis tick markers denoting canonical absorption bands (e.g., $\text{H}_2\text{O}$ at $1.4, 1.9, 2.7\ \mu\text{m}$; $\text{CO}_2$ at $4.3\ \mu\text{m}$; $\text{CH}_4$ at $2.3, 3.3\ \mu\text{m}$; $\text{SO}_2$ at $4.05\ \mu\text{m}$).
  - Ensure lines are styled with `cosmetic=True` so they render cleanly without cluttering the data points.

### C. 2D FITS Image Inspection (Jupiter JWST MIRI)
* **Context**: Brett provided JWST MIRI F770W imaging FITS files of Jupiter (`rate.fits` and `crf.fits`). See `docs/research/JUPITER_MIRI_FITS_FINDINGS.md`.
* **Goal**: When a user loads a 2D FITS image rather than a 1D tabular spectrum:
  - Instead of failing or trying to plot an image as a spectrum, offer a clean **Image Inspection Dialog / View** using `pg.ImageView` or `pg.ImageItem` with colormaps (e.g. `inferno` or `viridis`), asinh/log intensity stretching, and spatial pixel coordinate readouts.

### D. Consistent Theming, Typography & Button Feedback
* **Style Details**:
  - The application uses a modern dark astrophotography palette: Background `#12151c`, Panels `#1a1f2c`, Accent `#3b82f6` (blue), Success `#10b981` (emerald), Warning `#f59e0b` (amber), Danger `#ef4444` (ruby).
  - Ensure all spinboxes, combo boxes, and buttons have consistent hover and focus rings.
  - Review font scaling and ensure high-DPI scaling doesn't truncate labels on 1080p, 1440p, or 4K displays.

---

## 5. How to Launch and Test

To test the application locally on Windows:
```powershell
cd "c:\AI-Projects\Bwett AI Project UwU\ECAS_BETA"

# Run the GUI
.\.venv\Scripts\python.exe main.py

# Run the test suite (headless, zero warnings)
$env:QT_QPA_PLATFORM = "offscreen"
.\.venv\Scripts\pytest -W error
```

---

## 6. Current Long-Term Roadmap Context

For context on what the rest of the team (Blake, Brett, Astra/Codex, Gemini) is working on:
1. **WASP-39 b Benchmark Replication**: Incorporating high-temperature (1000–1200 K) ExoMol opacities covering the full NIRSpec PRISM band ($1872–18800\ \text{cm}^{-1}$) to reproduce literature publication benchmarks.
2. **Large-Source Project Persistence**: Migrating from base64-in-JSON storage to external immutable streaming file caches with SHA-256 digests for large FITS files.
3. **Controlled Attestation UI**: Allowing users to explicitly specify missing physical units or observational metadata for third-party laboratory files without altering raw source data.

Have fun polishing the UI! If you have any questions, consult `README.md`, `docs/brains/PROJECT_STATE.md`, or `docs/brains/DECISIONS.md`.
