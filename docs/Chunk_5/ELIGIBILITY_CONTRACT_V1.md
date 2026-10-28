# Eligibility contract v1 — 2026-10-28

Research implementation: eligibility_contract.py, not connected to application UI,
ingestion or persistence. No migration or change to SpectrumData. This increment
awaits independent review along with the robustness work and initial method decision.

Version `ecas-comparison-eligibility-v1` accepts two immutable ComparisonInput
envelopes. It returns an Eligibility containing version, requested operation,
source identities, status and every detected blocking reason. It does not compute
a score, edit inputs, authenticate evidence, or certify physical validity.

Operations are aligned_residual_v1 and weighted_residual_v1. Outcomes are eligible,
missing_requirements or incompatible, with incompatible taking precedence if both
missing and incompatible reasons occur. A blocked operation returns reasons, not
zero residuals. Missing metadata does not prohibit raw-data inspection in the app;
that existing workflow is unchanged and outside this assessor.

## Required caller declarations

- Source identifier and syntactically valid SHA-256. The caller must derive/check
  hashes; this offline assessor does not read the source file.
- Dataset role: observation, forward_model or reference_measurement. Raw line lists
  and cross sections require a physical-model step before this contract applies.
- V1 only supports transit_depth on microns, in percent or fraction. Units must
  already agree between inputs; it performs no implicit conversion. A future
  adapter must explicitly map archive `%` to the contract's `percent` and preserve
  that mapping as provenance, not infer unknown units.
- Coordinate frame, common response ID and nonempty response evidence. These are
  caller assertions that curves are already expressed at the same response, not
  physical checks against instrument documentation. Different response IDs block.
- At least three finite measurements, strictly increasing coordinates and exactly
  equal grids. Missing measurements, non-overlap and unaligned grids block. No
  sorting, masking, tolerance-based alignment, clipping or extrapolation occurs.

This intentionally narrow v1 avoids a general provider/unit/response framework.
Different observables can be supported later with explicit versioned requirements.
The API takes typed envelopes; it is not a parser for arbitrary JSON/dictionaries.

## Weighted mode

Requires explicit documented noise_kind and noise_evidence for both inputs:

| Noise kind | Required declaration |
| --- | --- |
| independent_gaussian_1sigma | Positive finite sigma per point; no conflicting covariance |
| gaussian_covariance | Finite symmetric positive-definite matrix; no conflicting sigma |
| deterministic_model | Only forward_model role, no error arrays, explicit evidence; contributes zero variance |

Combined covariance is C_left+C_right only with an explicit cross-dataset
independence declaration. Equal source hashes for two stochastic inputs cannot
be assumed independent. This conservative guard does not discover correlated
provenance between different hashes: the caller still has to establish independence.
Two deterministic inputs have zero combined covariance and cannot yield a weighted
diagnostic. No covariance estimation, jitter, pseudoinverse or asymmetric likelihood
is silently supplied. Unknown/asymmetric errors may permit unweighted residual
inspection while blocking weighted diagnostics. Nonfinite variance from overflow
is rejected. Missing/invalid noise information never implies zero variance.

## Verification and status

29 new cases cover valid unweighted/weighted paths, all missing metadata fields,
roles/observables/units/frame/response mismatches, non-overlap/invalid measurements,
sigma overflow/zero, singular/asymmetric covariance, missing evidence, shared-source
independence and deterministic-only pairs. The envelopes and caller values remain
unchanged. These are contract checks, not validation of caller-supplied science.

Focused command: `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk5-eligibility-focused`
— 100 passed, one skipped, 1.08 s. Full command with chunk5-eligibility-full:
418 passed, one skipped, 7.82 s; exit 0. Evidence: verification_eligibility_20261028.
Skip remains Windows directory-symlink privileges. No dependency or download added.

User confirmed manual review complete on 2026-10-28; no individual checklist
results were supplied or invented. Real-data validation remains deferred. This
confirmation does not imply independent review of newly written contract code.
Original recovery checkpoint and reviewed research snapshots remain unchanged.
Next: independent review, then a deliberate adapter from actual imported metadata
and reference-provider investigation; no automatic metadata defaults or legacy
database rewrites. No Git commit/push, paid reviewer invocation or real-data scoring.

## Source review received — 2026-10-28

Argon returned zero findings for eligibility_contract.py. Exact-grid equality was
noted as a limitation and is retained by design; floating-point differences block
until explicitly aligned. The supplied review did not list the test file or other
new increments. See review_20261028/04-eligibility-disposition.md. No code change or
test rerun; latest full suite remains 418 passed, one skipped.
