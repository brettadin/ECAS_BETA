# Fitted-template prototype and false-match experiment — 2026-10-28

Research-only increment. template_investigation.py implements fitted comparisons
under known synthetic conditions. It is not connected to ECAS UI, persistence or
NASA ingestion. It does not compute atmospheric models, molecular presence,
abundances or Bayesian evidence. No library/provider selected for production.

## Executed numerical workflow

The invented template grid has 21 feature centers, 64 explicit bins over 1–2
microns, known Gaussian LSF sigma 0.02 micron and feature width 0.035 micron.
Analytic convolution and bin averaging use the preceding research harness.
Generalized least squares fits a constant plus a signed template amplitude, with
the same fixed covariance and data for every candidate. Amplitude is unconstrained:
negative features count in this two-sided experiment. It is not an abundance.

Cholesky whitening implements the specified positive-definite covariance. Fitted
baseline and feature amplitude are removed before calculating residual improvement
relative to a fitted constant-only null. An independent full-design least-squares
solve checks coefficients and residuals. Noiseless input recovers the known baseline,
amplitude and center. Degenerate templates, nonfinite inputs, incompatible shapes,
asymmetric and non-positive-definite covariance are rejected by the numerical API.
This array API assumes explicit common-grid/units; it is not a metadata validator.

The Monte Carlo uses known Gaussian AR(1) noise, rho=0.65 and sigma=0.01 percentage
points. Three separate seeded generators produce 2,000 calibration null draws,
2,000 held-out null draws and 500 injected draws. Calibration takes the higher
empirical 95th percentile; thresholds are frozen before evaluating holdout draws.
Baseline fitting and the complete grid search are repeated for every draw.

| Held-out procedure | Threshold | Exceedances |
| --- | ---: | ---: |
| One fixed template | 3.8239 | 78/2000 = 3.9% |
| Search 21 templates, incorrectly reuse fixed-template threshold | 3.8239 | 1221/2000 = 61.05% |
| Search 21 templates, use full-search null threshold | 9.0968 | 110/2000 = 5.5% |

Binomial standard errors are recorded in the JSON (about 0.51 percentage points
for the final row); they omit uncertainty from finite calibration samples. No
exact population error-rate guarantee or rare-tail significance is claimed.

For invented amplitude 0.06 at the center template, 489/500 injected runs exceed
the search threshold; 496/500 recover the exact grid center. These are separate
metrics: matching the center does not require exceeding a threshold. Median fitted
amplitude at the true center is 0.06040. Recovery at this favorable synthetic
amplitude does not validate weaker signals, unknown covariance or real molecules.

## Source context and physical-model requirements

[Gross and Vitells (2010)](https://arxiv.org/abs/1005.1891) distinguish a fixed-point
excess from searching across a range. Our independent Monte Carlo illustrates
that issue; it does not implement their asymptotic trial-factor method.

The [petitRADTRANS tutorial](https://petitradtrans.readthedocs.io/en/latest/content/notebooks/retrieval_basic.html)
generates transit radii from temperatures, composition, gravity, radius and a
reference pressure, then converts radii using stellar radius. Model and observation
units must match. This establishes a concrete distinction between a fitted feature
and atmospheric forward modelling; no tutorial parameters are adopted for WASP-39 b.
Sources read 2026-10-28; no datasets or dependencies downloaded.

Before evaluating actual forward models, require explicit parameter values/priors
and provenance for temperature-pressure structure, species/isotopologues and
opacity versions, abundance convention, gravity/radius/reference-pressure relation,
stellar radius, cloud/haze assumptions, model numerical grid and wavelength frame.
Record model output observable/units, convolution/bin response and all transformations.
Provider opacity validity, license/access and conditions need separate verification.
Do not obtain a physical model by rescaling an arbitrary molecular cross section.

## Limits and next step

Thresholds apply only to this exact covariance, null, fitted nuisance parameters,
template grid, masks and response. Changing search widths, additional molecules or
fitting constraints requires recalibration. No nuisance priors, covariance
estimation, wavelength-dependent LSF or model inadequacy was evaluated. No real
measurement or molecular reference was scored.

Next evaluate mismatched noise/continuum and out-of-grid features, then consolidate
method-selection evidence and a proposed limited implementation contract. The
research increments await the user's planned Argon batch review; do not count the
earlier application reviews as acceptance of this prototype. Chunk 4 desktop
acceptance remains open. All edits local; original recovery archive unchanged.

Reproducibility: verification_template_20261028/template-report.json stores seeds,
NumPy version, template/covariance hashes, arrays/settings, counts and limits.
Exact child command/environment keys are in template-run.json; full/focused test
logs and source fingerprints are alongside. This prototype and the earlier
comparison_investigation.py, both test files and their contract/results documents
form the next review scope.
