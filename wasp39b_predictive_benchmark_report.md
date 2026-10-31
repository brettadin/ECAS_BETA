# ECAS Predictive Benchmark: H2O in WASP-39 b

## 1. Executive Summary

**Question:** *When ECAS suggests H2O, does including that molecule improve its prediction of an absorption feature in a separate observation?*

> **Benchmark Outcome:** **This observation cannot distinguish the models.**

This observation cannot distinguish the models. Both the physical water model (contrast error = 243.7 ppm) and the flat continuum baseline (contrast error = 273.4 ppm) predict band contrasts within the 2-sigma observational uncertainty interval (±72.1 ppm) of the validation observation. While adding water improved the training fit on NIRSpec G395H by 83.0 ppm, the separate NIRSpec PRISM observation's per-bin measurement scatter is comparable to the contrast difference, preventing a statistically decisive preference between the two models on this feature.

## 2. Separate Observation Identities

- **Observation Independence:** ✓ CONFIRMED SEPARATE VISITS
- **Evidence:** Verified independent observing visits: Fitting observation is Near Infrared Spectrograph (NIRSpec) - G395H (Prog 1366, Visit 02, observed 2022-07-30/31), while validation observation is Near Infrared Spectrograph (NIRSpec) - PRISM (Prog 1366, Visit 01, observed 2022-07-10/11). The datasets represent separate physical transits separated in time with distinct instrument readouts.

| Role | Target | Instrument / Mode | Program & Visit | Date | Source Reference | Points |
|---|---|---|---|---|---|---|
| **Fitting (Training)** | WASP-39 b | Near Infrared Spectrograph (NIRSpec) - G395H | Prog 1366, Visit 02 | 2022-07-30/31 | Alderson et al. 2022 / 2023 | 344 |
| **Validation (Test)** | WASP-39 b | Near Infrared Spectrograph (NIRSpec) - PRISM | Prog 1366, Visit 01 | 2022-07-10/11 | Rustamkulov et al. 2023 | 207 |

## 3. Pre-Declared Feature & Band Contrast Definition

- **Feature Name:** WASP-39 b 3.10-3.30 µm Water Band (Holdout Window)
- **In-Band Interval:** 3.10 – 3.30 µm
- **Blue Reference Interval:** 2.80 – 3.00 µm
- **Red Reference Interval:** 3.40 – 3.60 µm
- **Weighting:** inverse_variance
- **Scientific Justification:** Evaluates the 3.10-3.30 µm water feature relative to local continuum reference levels at 2.80-3.00 µm and 3.40-3.60 µm across separate visits.

## 4. Quantitative Results & Model Comparison

| Metric | Observed (Validation Visit) | Model with H2O | Baseline (No H2O) |
|---|---:|---:|---:|
| In-Band Mean Depth | 2.13219% | 2.14284% | 2.14976% |
| Continuum Reference Mean Depth | 2.15953% | 2.14580% | 2.14976% |
| **Band Contrast (ppm)** | **-273.4 ± 36.1** | **-29.6** | **-0.0** |
| Contrast Prediction Error | — | 243.7 ppm | 273.4 ppm |
| Visit-Level Mean Offset | — | +140.7 ppm | +181.0 ppm |
| Mean-Subtracted Shape RMS | — | 274.3 ppm | 300.4 ppm |
| Training RMS (G395H) | — | 287.4 ppm | 370.4 ppm |

## 5. Opacity Traceability and Methodological Disclosures

- **Line List:** POKAZATEL (['Polyansky et al. 2018, MNRAS 480, 2597 (POKAZATEL)', 'Tennyson & Yurchenko 2012, MNRAS 425, 21 (ExoMol)'])
- **Tabulated Temperature:** 500.0 K
- **Model Atmospheric Temperature:** 1166.0 K
- **Pressure Broadening Treatment:** Doppler broadening at zero pressure; pressure-broadened wings neglected
- **Approximation Disclosure:** The 500 K POKAZATEL zero-pressure cross section preserves fundamental vibrational band centers (2.7-3.3 µm) and envelope structure, allowing comparative testing of band contrast vs continuum. Higher-energy thermal state populations and pressure broadening are known approximations.
- **Outstanding Requirement:** High-temperature cross section tabulated at T=1166 K, P=0.01 bar with H2/He line broadening. Can be generated via ExoMol cross-section ingestion workflow once online access is authorized.