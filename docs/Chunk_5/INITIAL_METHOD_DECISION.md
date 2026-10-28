# Initial comparison method decision — 2026-10-28

Status: initial engineering method selected for future implementation, pending
independent review of this decision and robustness increment. Not a scientific
validation, release acceptance or claim that comparison is connected to the app.
User explicitly deferred real-data validation and left desktop acceptance open.
Those remain visible follow-up work, not prerequisites to this synthetic study.

## Selected initial scope

Use an **observable-compatible overlay with explicit response matching and residual
inspection**. Where errors and covariance conventions are established, optionally
report the residual quadratic for that fixed, documented noise model. A full
Gaussian likelihood must include its normalization if covariance choices vary.
Do not display a generic molecular match percentage or detection confidence.

The first implementation should compare supplied curves as given. No automatic
amplitude, baseline, shift or continuum fitting by default. If fitting is later
enabled, the fitted parameters, constraints and null/alternative must be explicit,
and raw curves must remain accessible. Research GLS fits are a tested numerical
candidate for that optional step, not the default scientific interpretation.

Raw data inspection may proceed when metadata are incomplete, with unknowns shown.
Quantitative comparison must stop at unmet requirements rather than filling missing
physical facts. Molecular line lists/cross sections require a physical model to
produce a comparable transit-depth observable. Reference catalogue membership and
visual feature overlap do not establish molecular presence.

## Rationale and alternatives

| Candidate | Evidence from the executed studies | Decision |
| --- | --- | --- |
| Overlay and residual inspection | Preserves absolute deviations, coverage and response effects | Initial diagnostic method, subject to compatibility requirements |
| Pearson correlation alone | Offset/amplitude errors can retain correlation 1; binned mismatch can retain 0.9987 | Not an agreement/detection score |
| Peak/line proximity | Distinct synthetic profiles become indistinguishable in a coarse bin | Exploratory annotations only; no molecular decision |
| Fixed-covariance GLS | Independent solve checks coefficients; injected synthetic feature recovered | Optional future fitted diagnostic; no general detection claim |
| Search-threshold calibration | Single-template threshold fails for grid search; wrong noise/continuum invalidates calibration | Research-only probabilities until entire intended procedure is validated |
| Physical atmospheric retrieval | Requires additional model inputs, opacity/provenance and likelihood decisions | Long-term direction; no engine or production retrieval chosen |

This selects the simplest interpretable initial diagnostic, not a replacement for
model-based atmospheric characterization. No model library/provider is selected.

## Comparison contract for implementation

Inputs must identify role, source/hash, observable, coordinate kind/frame and units,
signal units, sampling/bin/response convention and instrument/resolution evidence.
Any physical model/reference additionally records conditions, parameters, opacity
version and transformations. Retain original indices and immutable source values.

1. Validate observable and unit compatibility. Unit conversion must be explicit and
   applied consistently to values and errors. Missing units never imply equality.
2. Define common support and response. No extrapolation or silent clipping. List
   excluded indices; report no-overlap as incompatible, not a zero residual score.
   Match model response/bin averages to the observations, rather than upsampling
   observations to manufacture resolution. Unknown response blocks quantitative use.
3. Preserve uncertainty signs/conventions before documented conversion to positive
   magnitudes. Missing/zero errors do not become positive weights. Asymmetric errors
   remain explicit until an appropriate statistical model is chosen. Covariance
   absence is not evidence of independence; a declared assumption must be labelled
   and validated for any probabilistic use.
4. Produce overlay plus residual values and provenance first. Weighted diagnostics
   additionally require compatible positive finite errors and a specified positive-
   definite covariance. No implicit diagonal covariance or pseudoinverse fallback.
5. Report unmet requirements, assumptions, exclusions and model adequacy concerns.
   Separate a ranked best candidate from adequacy and from significance. Boundary
   hits and structured residuals are warnings, not definitive rejection rules.

Outcomes: inspection-only, missing requirements, incompatible, or eligible for a
named diagnostic/version. Outputs retain input hashes, transformations/parameters,
included/excluded indices, residuals and reasons. No production schema/API changes
are made by this decision; COMPARISON_INPUT_CONTRACT_DRAFT.md remains supporting
detail and unknown product conventions remain unknown.

## Robustness evidence added in this increment

`robustness_investigation.py` reuses the previously reviewed numerical prototype
unchanged. Three separate fixed seeds generate 2,000 draws per noise case. Each
noise model has its own 95th-percentile full-search calibration; holdout data are
generated with known correlated Gaussian noise. The misspecified fit assumes
diagonal noise. The slope example deliberately violates the fitted constant null.

| Case | Search threshold exceedance on holdout |
| --- | --- |
| Correct covariance and constant continuum | 105/2000 (5.25%) |
| Incorrect independent-noise assumption | 1476/2000 (73.8%) |
| Correct covariance, omitted continuum slope | 803/2000 (40.15%) |

These are conditional synthetic results, not observed mission false-positive rates.
An omitted-slope exceedance is evidence of an inadequate null, not detection of a
feature. Monte Carlo standard errors omit finite-calibration uncertainty.

Noiseless midpoint feature 1.52 microns is assigned grid center 1.5 and leaves
residual quadratic 7.64; exact-grid truth leaves numerical zero. Truth centered
outside the searched range at 0.99 produces a boundary candidate 1.1, negative
fitted amplitude and residual quadratic 14.97. A best index always exists, even
when the grid fails to describe the data. No empirical boundary classifier is
claimed. Evidence: verification_robustness_20261028/robustness-report.json.

## Evaluation criteria and outstanding validation

Analytic response functions have independent numerical-integration checks at 1e-10
relative tolerance; GLS coefficients/residuals are checked against an independent
design-matrix solve. Tests require visible partial/no coverage, invalid covariance
and degenerate-template failures. Same-grid and explicit unit conversion preserve
zero residual to floating-point tolerance. Calibration tests use broad finite-sample
sanity bounds, not a guaranteed 5% population error rate. Strong injected-feature
recovery is verified only for the specified synthetic conditions.

Future integration must exercise unknown units, incompatible observable roles,
non-overlap, missing/asymmetric errors, response mismatch and preserved provenance
through actual selection/display. The current array experiment does not implement
these metadata gates. For future probabilistic claims, recalibrate the full search,
fitting, masking and reference selection procedure, assess model misspecification,
and validate on suitable observational products. Real data remain deferred by user
instruction. No cutoff from this study may be used as a production detection rule.

## Scientific context

[Ih and Kempton (2021)](https://arxiv.org/abs/2106.12358) studied synthetic retrievals
and found that correlated noise can improve apparent fit while worsening accuracy.
This supports explicitly examining noise assumptions; our diagnostic experiment
does not reproduce their retrieval study or its quantitative results.

[petitRADTRANS's Data API](https://petitradtrans.readthedocs.io/en/latest/autoapi/petitRADTRANS/retrieval/data/index.html)
separates model functions, resolution/bin information, uncertainties and covariance.
That is supporting design context, not library selection. Primary sources accessed
2026-10-28. Earlier source links and broader method comparisons are retained in the
readiness, contract and prototype documents.

## Acceptance and next step

The investigation now documents an initial bounded method, compatibility rules,
synthetic cases, evaluation criteria and known limits. The new robustness work and
method decision require independent review before marking this increment accepted.
Previously reviewed snapshots remain intact. Desktop acceptance remains open;
real-data validation is a future activity. Next implementation-design task: turn
these metadata requirements into a versioned eligibility contract without changing
legacy stored spectra, then investigate reference providers under Chunk 5.1. A
production workflow belongs to Chunk 6 and depends on suitable reference/model data.
