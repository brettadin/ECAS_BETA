# NASA transmission workflow — human review handoff

This review branch publishes the locally tested ECAS version based on
`6da2dccfe966b9b75dc118aba3d55e606319b579`. At publication preparation, GitHub master
was `5deb2673e3db3a626cb67040f09ac0bf48a38df4`, one newer commit containing CSV
import-manager/UI/test/documentation changes. Those changes have not been merged
into this branch. Review the tested implementation here before integrating the
overlapping changes; this is not a claim of merge readiness or final acceptance.

## What is implemented

- Exact planet-name NASA spectral metadata search in Spectral Data.
- Selection, anonymous bounded download and validation of supported transmission
  tables, with cancellation and explicit errors.
- Local raw-table/metadata cache with hashes, source URLs and offline reopening.
- Local CSV and supported NASA table import/display, preserving scientific units,
  signed uncertainties, nulls, source columns and metadata.
- Startup/import regression coverage, portable test fixtures and pinned local
  runtime/test dependency records. See the root README for setup and launch.

## Verification

Latest recorded full regression: **281 passed, 1 skipped** in 3.94 seconds on
Windows AMD64, Python 3.14.5, PySide6 6.12.0. The skip requires Windows directory
symlink privileges. Exact command/environment metadata and output are in
`../verification_20261027/network-reentrant-full-run.json` and `.log`.

Publication packaging check: **281 passed, 1 skipped** in 3.61 seconds from a
clean checkout of the staged Git index, using the existing installed environment
and sanitized offscreen test settings. Ten NASA JSON/table capture files matched
their original working-file bytes exactly in the index. Scoped .gitattributes
rules preserve raw capture bytes across checkout, including source-table spacing.
The staged-file credential-pattern scan found no matches (a heuristic check, not
an exhaustive guarantee). Evidence: ../verification_20261027/review-package.json
and .log. Only documentation/evidence additions followed this test.

The actual application was also exercised offscreen against NASA: 28 transmission
results for WASP-39 b, the selected 331-row/31-column Feinstein table, microns/%
units, then offline reopening without another request. Evidence and unchanged
public NASA fixtures are under `../../../data/NASA/2026-10-27/`.

Offscreen automated execution is distinct from human interactive acceptance and
does not establish scientific validity.

## Independent review status

All three interactive Argon reports were supplied by the user and assessed:

- Batch 1: fixed target-casing evidence mismatch. The network follow-up then
  reproduced a completion-reentrancy bug before fixing reply identity handling.
- Batch 2: added declared blank numeric-null support and type-case tolerance;
  expanded evidence-URL validation to reject empty duplicate/unknown parameters.
  Undeclared blanks remain errors. The app's generated lowercase format=json
  contract remains intentional; arbitrary external format variants are unsupported.
- Batch 3: no production defect confirmed. Added queued Qt failure and cached-load
  integration tests to check the actual handling. See [batch 3 triage](batch3-triage.md).
- Network details and before/after evidence: [follow-up triage](network-followup-triage.md).

**Targeted Argon re-review of revised code remains pending.** The review findings
and fixes are not a final independent approval. Historical parent-workspace paths
in development logs refer to local execution evidence; these review summaries and
the committed verification records provide the portable handoff.

## Human checks

1. Install the README's dependencies in a project environment, then launch main.py.
2. Import the bundled CSV after selecting WASP-39 b Archive; inspect 331 rows.
3. Import data/NASA/2026-10-27/feinstein-2023.tbl with either CSV schema selected;
   inspect 331 rows, 31 columns and explicit microns/% units.
4. Search NASA for lowercase `wasp-39 b`, select a supported transmission record,
   download it, then reopen from Cached spectra without another network request.
5. Check cancellation and visible errors; verify a failed download preserves the
   prior displayed spectrum, while a failed replacement import clears stale data.

The generated data/NASA/cache and local .venv are excluded from Git. No real
credentials, private project databases or coordinator runtime files are required
for this review.

Still outside this increment: cache-to-project-SQLite provenance integration,
other providers, generalized scientific formats, large-cache performance work,
scientific comparison validation and integration with the newer master commit.
