# Proposed comparison inputs and investigation results — 2026-10-28

Draft for review. Not a persistence schema, implemented validator, method selection
or production comparison feature. SpectrumData and the reviewed UI are unchanged.

## Verified archive context

The [NASA atmospheric column guide](https://exoplanetarchive.ipac.caltech.edu/docs/atmospheres/atmospheres_columns.html)
identifies centralwavelng and bandwidth in microns, pl_trandep as transit depth in
percent, and pl_trandeperr1/2 as upper/lower uncertainty. It does not define the
bandwidth's half/full-width convention, response function, covariance or uncertainty
confidence level. Keep those unknown; do not manufacture symmetric bin edges or
treat bandwidth as instrument resolving power. Error units are blank in this file's
headers; any future mapping to depth units must be explicit and source-supported.

The guide describes pl_trandeplim as calculated-versus-reference provenance,
not a generic detection limit flag. Some neighboring guide descriptions appear
misaligned. Do not generalize the word 'limit' into a censoring rule. The importer
currently supports only zero flags; this conservative existing restriction stays
unchanged until numeric flag mapping and calculation provenance are verified.

The [original NIRISS publication](https://www.nature.com/articles/s41586-022-05674-1)
was published 9 January 2023. Our file's REFERENCE string says Feinstein et al.
2022. Preserve both as separate facts; do not rewrite the capture to reconcile a
display year. Dataset/reduction identity requires the saved archive record and
publication context, not just matching author/year text.

## Actual captured spectrum audit

`comparison_investigation.py` runs the existing table importer on immutable captured
bytes, then reports descriptive statistics in
`verification_20261028/investigation-report.json`.

- 331 measurements; source SHA-256
  `3140d259259c51e282cd075890cc878ab79c9bb859fae3b83ab5459756e9adc2`.
- Central wavelengths: 0.63096–2.79649 microns; bandwidth: 0.00147–0.01288 microns.
- Transit depth: 2.03628–2.20857 percent.
- All retained upper uncertainties are positive and lower uncertainties negative;
  their magnitudes match in this product. Magnitudes range 0.00423–0.03465, with
  blank header unit strings. All five audited fields are populated; all flags zero.
- These observations do not establish Gaussianity, 1-sigma confidence, independent
  errors, valid instrument convolution, or a molecular interpretation.

## Proposed contract

Every comparison input should retain raw source identity/hash, dataset role
(observation, reference measurement, line list, opacity or forward model), observable,
axis kind/unit, signal unit, original row indices and metadata evidence. Unknown
values stay unknown. A plotting alias must not become a physical equivalence.

| Proposed component | Required semantics |
| --- | --- |
| Sampling | Explicit coordinates; optional documented bin edges/response; resolution and its source kept distinct from sample spacing |
| Uncertainty | Separate lower/upper magnitudes after documented sign conversion; source column names/signs retained; confidence convention and covariance availability stated |
| Physical conditions | For relevant references/models: temperature, pressure, geometry, isotopologue, abundance assumptions, opacity/model version and evidence; absent values are not defaults |
| Preprocessing | Ordered, versioned transformations with parameters, masks and retained indices; immutable raw input remains available |
| Operation | A named method/version, required metadata, coverage policy and assumptions; no generic 'compatible' flag |
| Output | Operation-specific eligibility/reasons, transformed-input identities and diagnostic limitations; no automatic molecular detection statement |

Outcomes: **inspection only**, **missing requirements**, **incompatible**, or
**eligible for the named operation**. Report all unmet requirements. For a future
weighted residual diagnostic require comparable observables/units, documented grid
and resolution handling, positive finite errors with established conventions and
a declared covariance model. Missing covariance is not proof of independence.
Asymmetric errors must not be averaged silently. A molecular cross section cannot
be compared as though it were measured transit depth; that requires a physical
forward model. No conversion or interpolation is performed by this draft.

## Executed synthetic experiment

The isolated experiment uses 101 invented same-grid points with a Gaussian-shaped
feature, explicit percentage units and fictional independent 1-sigma errors. No
real measurements are scored and no parameters are fitted. It contrasts a Pearson
correlation with sum((observation-model)/sigma)^2. This sum is not a probability or
reduced chi-square.

| Invented candidate | Correlation | Weighted residual sum |
| --- | ---: | ---: |
| Identical | 1.0 | 0 |
| Constant offset +0.2 percentage points | 1.0 | 40400 |
| Double feature amplitude | 1.0 | 1002.65 |
| Shift feature center by 0.1 micron | 0.324 | 1087.21 |
| Constant curve | Undefined | 1002.65 |

Explicit fraction-to-percent conversion of both values and uncertainty preserves
the identical result to floating-point tolerance. Unknown/nonpositive uncertainties
do not produce a weighted score. This provides a concrete counterexample to using
correlation alone as absolute agreement. It does not select a method or compare
real molecular candidates. Runtime/performance has not been benchmarked.

## Remaining investigation before method selection

Build and evaluate nonoverlapping/partial axes, irregular sampling, finite bin
response/resolution mismatch, asymmetric errors, correlated noise, blended features
and incompatible-observable fixtures. Define acceptable numerical tolerances and
false-match calibration for each candidate's claimed use. Investigate an explicit
forward-model-to-observation path and uncertainty likelihood, with primary-source
support. Verify flag mapping and bin/error conventions against original product
documentation. Provider selection/access terms and reference retrieval are Chunk
5.1 work. None is satisfied by the small executed same-grid experiment.

Follow-on: analytic response, partial-coverage, asymmetric-error, fixed-covariance
and blend counterexamples are now executed; see RESPONSE_AND_UNCERTAINTY_EXPERIMENT.md.
They remain synthetic, not product calibration or noise/false-match validation.
