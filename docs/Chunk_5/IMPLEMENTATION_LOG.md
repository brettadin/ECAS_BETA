# Chunk 5 investigation log

## 2026-10-28 — source audit and initial candidate experiment

Created comparison_investigation.py as an offline research harness, outside the
application package. Audits the unchanged 331-row NASA capture and compares two
diagnostics on labelled synthetic same-grid curves. Preserves raw measurements,
schema, persistence and UI. Input-contract draft separates source facts, unknown
conventions and proposed eligibility requirements; no production method selected.

Read primary NASA column documentation and the original NIRISS publication through
web tools. Links and scoped conclusions are in COMPARISON_INPUT_CONTRACT_DRAFT.md;
access date 2026-10-28. Bandwidth edge/response convention, confidence/covariance and
numeric flag mappings remain unresolved. No new dataset or dependency downloaded.

Actual commands (existing project Python, isolated child environments):

- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk5-investigation-focused`
  — 46 passed, one skipped; 0.88 s, exit 0.
- `.venv/Scripts/python.exe -I -B .venv/checks/run_chunk5_report.py`
  — exit 0; emitted source audit plus synthetic experiment report. Exact child
  command and environment keys in verification_20261028/investigation-run.json.
- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk5-investigation-full`
  — 364 passed, one skipped; 7.25 s, exit 0.

Skip remains Windows directory-symlink privileges. Full/focused logs and command
metadata are copied into verification_20261028. Seven new test cases cover the
experiment's offset/amplitude counterexample, undefined constant correlation,
explicit unit conversion, invalid uncertainties and real-capture identity.
Tests support these limited conclusions, not physical validity of a method.

Next: broaden synthetic tests to sampling/response, asymmetric errors, covariance
and blends; obtain product-specific conventions and evaluate a physical-model
comparison path before method selection. Chunk 4 human desktop acceptance remains
open. This increment has not been independently reviewed. Original Argon reviews
cover the prior application snapshots. Recovery checkpoint remains untouched.
No new agent/model calls, credentials, Git commits or pushes.

## 2026-10-28 — response and uncertainty counterexamples

Extended the research harness, preserving application code and original v1 report.
Added analytic top-hat averages, normalized Gaussian LSF convolution, explicit
full-bin coverage selection, side-dependent error penalties and a fixed positive
equicorrelation quadratic. Added 15 test cases including independent integration
and linear-solve checks. Results/limitations: RESPONSE_AND_UNCERTAINTY_EXPERIMENT.md.
No real NASA measurements scored or altered; no production likelihood selected.

Final commands via existing isolated drivers:
`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk5-response-focused`
— 61 passed/one skipped, 1.01 s;
`.venv/Scripts/python.exe -I -B .venv/checks/run_chunk5_report.py` — exit 0;
`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk5-response-full`
— 379 passed/one skipped, 7.94 s, exit 0. Evidence copied to
verification_response_20261028. Skip remains Windows directory-symlink privileges.
Earlier intermediate runs were superseded by final Gaussian-LSF coverage.
No downloads, dependencies, credentials, paid reviews, commits or pushes.
Next: physical model input/provenance and noise/false-match investigation. Method
selection, independent research review and human desktop acceptance remain open.

## 2026-10-28 — fitted templates and held-out false-match calibration

Added template_investigation.py and test_template_investigation.py. GLS fits baseline
and signed feature amplitude using explicit synthetic response and fixed covariance.
Separate seeded calibration/holdout draws test one-template versus full-search
thresholds, plus injected-feature recovery. Results and physical-model input
requirements are in MODEL_COMPARISON_PROTOTYPE.md. No real spectra scored.

`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk5-template-focused`
— 68 passed/one skipped, 3.53 s;
`.venv/Scripts/python.exe -I -B .venv/checks/run_template_report.py` — exit 0;
`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk5-template-full`
— 386 passed/one skipped, 7.88 s, exit 0. Evidence in verification_template_20261028.
Existing symlink-privilege skip unchanged. Seven new cases include independent GLS,
noiseless recovery, invalid covariance, degenerate template and held-out calibration.
User plans Argon batch review later; this research remains unreviewed. Next: model/
noise misspecification and out-of-grid behavior before method-selection consolidation.
No app changes, paid reviewer calls, credentials, downloads, commits or pushes.

## 2026-10-28 — independent research Batch 1 received

User supplied Argon's review with zero findings for response/uncertainty code,
tests and supporting context. Recorded snapshot scope and synthetic/uniform-noise
limitations in review_20261028/01-response-and-uncertainty-disposition.md.
Batch 1 review complete; Batches 2/3 pending. No code changes or tests rerun.
Latest suite remains 386 passed/one skipped. Chunk 5 method acceptance and Chunk 4
human desktop acceptance remain open. No model call or Git publication.

## 2026-10-28 — independent research Batch 2 received

User supplied Argon's fitted-template/calibration review with zero findings.
Recorded scope, known-covariance limitation and optional solver optimization in
review_20261028/02-template-fitting-and-calibration-disposition.md. Batch 2 review
complete; Batch 3 pending. No code changes or tests rerun; latest suite remains
386 passed/one skipped. No new dependency, paid review, download, commit or push.

## 2026-10-28 — independent research Batch 3 received

User supplied Argon's contract/scientific-claims review with zero findings.
Documentation and JSON evidence were judged consistent within the offline scope.
All three research batch reviews are complete for their snapshots. Disposition:
review_20261028/03-contract-and-scientific-claims-disposition.md. No code changes
or tests rerun; latest suite remains 386 passed/one skipped. Method selection,
model/noise misspecification, product conventions and human desktop acceptance
remain open. No new model call, download, commit or push.

## 2026-10-28 — robustness and initial method decision

User deferred real-data validation and allowed desktop acceptance to remain open.
Added robustness_investigation.py plus three tests. Existing reviewed research
helpers remain unchanged. Independent noise calibrations and held-out draws show
the consequences of wrong covariance/omitted continuum; noiseless midpoint and
outside-grid cases expose residual mismatch despite a best candidate.
Recorded a limited initial engineering method and acceptance boundaries in
INITIAL_METHOD_DECISION.md. No atmospheric engine, provider or production workflow
selected; metadata gates remain an implementation-design task. New increment awaits
independent review; previous three batch reviews still apply to their own snapshots.

Actual isolated commands:
`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk5-robustness-focused`
— 71 passed/one skipped, 1.05 s;
`.venv/Scripts/python.exe -I -B .venv/checks/run_robustness_report.py` — exit 0;
`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk5-robustness-full`
— 389 passed/one skipped, 7.48 s, exit 0. Evidence copied to
verification_robustness_20261028. Skip remains Windows directory-symlink privileges.
Read primary Ih/Kempton paper abstract and official pRT API; links in decision.
No new dependency, dataset download, real-data score, model call, credential access,
commit or push. Original recovery checkpoint preserved. Next: review this increment
then define metadata eligibility without rewriting legacy stored records.

## 2026-10-28 — versioned research eligibility contract

User confirmed manual review complete and authorized continuation. Added
eligibility_contract.py and 29 cases in test_comparison_eligibility.py, separate
from application code. Stable version/operation/status/reason outputs cover source,
observable, units, exact grid/frame/response declarations and optional noise gates.
No scoring, conversions, adapters or legacy migrations. See ELIGIBILITY_CONTRACT_V1.md.
Caller evidence is attestation, not automatically authenticated scientific evidence.

Isolated driver stages chunk5-eligibility-focused: 100 passed/one skipped, 1.08 s;
chunk5-eligibility-full: 418 passed/one skipped, 7.82 s, exit 0. Actual command:
`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py STAGE`. Evidence copied
to verification_eligibility_20261028. Existing symlink-privilege skip unchanged.
New increment plus robustness/method decision await independent review; prior
reviews retain their original scope. Real data remain deferred. No app changes,
downloads, dependencies, real credentials, model calls, commits or pushes.

## 2026-10-28 — eligibility source review received

User supplied Argon's source-only eligibility review with zero findings. Retained
exact-coordinate equality; recorded limitation and review scope in
review_20261028/04-eligibility-disposition.md. No corrections or test reruns; latest
suite remains 418 passed/one skipped. Robustness and initial method decision still
await independent review; manual confirmation complete, real data deferred.

## 2026-10-28 — imported-spectrum eligibility adapter

Added import_eligibility_adapter.py and six cases in test_import_eligibility_adapter.py.
Copies canonical values/indices without filtering or scaling, records explicit label
mappings, checks supplied table details/hash consistency, preserves raw errors and
leaves role/frame/response/noise gaps explicit. Generic CSV is not assigned missing
units or observational meaning. Details in IMPORT_ELIGIBILITY_ADAPTER.md.
This is adapter fidelity checking, not deferred real-data scientific validation.

Isolated driver command `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py STAGE`:
chunk5-adapter-focused — 106 passed/one skipped, 1.11 s;
chunk5-adapter-full — 424 passed/one skipped, 7.90 s, exit 0.
Evidence copied to verification_adapter_20261028. Symlink-privilege skip unchanged.
Existing reviewed source, application flows and recovery archive untouched. No
dependency/download/model call, credential read, commit or push. New adapter and
earlier unreviewed increments await independent review; next bounded phase is
reference-provider investigation once these comparison foundations are reviewed.

## 2026-10-28 — independent review completion confirmed

User stated "Independent review complete, please proceed". Record review completion
for the existing robustness/method/eligibility-test/adapter foundation checkpoint
based on that confirmation; do not invent itemized findings or extend it to later
code. Real-data validation remains deferred. Proceeded to Chunk 5.1 investigation.
