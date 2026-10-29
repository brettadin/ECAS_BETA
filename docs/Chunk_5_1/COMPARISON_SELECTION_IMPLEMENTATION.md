# Comparison selection and separate inspection — 2026-10-28

Approved feedback step 5 is implemented as a bounded inspection workflow.
`ecas/ui/comparison_browser.py` replaces the Comparisons placeholder, while the
Molecular References page retains search/download controls and its displayed product.

1. Load a spectrum through Spectral Data or reopen one through Projects.
2. In Comparisons, click **Add current observation**. This copies imported values
   into a session choice, with original columns, missing values, units, warnings,
   source path and importer hash when available. Unknown metadata stays unknown.
   Multiple additions have distinct session numbers. Choices do not persist across
   application restart; projects remain the durable observation store.
3. Click **Refresh cached choices**, then explicitly choose a reference. All valid
   cached supported molecular products are offered independently of catalogue search
   and the reference displayed in Molecular References. Full cache IDs distinguish
   duplicate requests. Labels show isotope, dataset, temperature, range and spacing.
4. Inspect the separate read-only tables and source/condition metadata. Reference
   citations and licence are retained in the details tooltip. Neither selection
   changes the observation plot or reference browser. Page changes retain choices.

Discovery and selection use the existing cache validation service. Selection
rereads/revalidates the chosen record; refresh retains a still-valid selection by
its path. Invalid/missing records clear the reference table and reference state,
and block any pairing explanation. Empty cache, invalid counts, unavailable cache,
no current observation and uncached catalogue entries have explicit explanations.
Refresh is explicit; there is no startup scan, request or source-file read.
Cached bytes remain inspection snapshots until the next selection/refresh; the
page does not monitor external disk changes continuously.

Compatibility text is a conservative explanation for the currently supported
cross-section products, not a general eligibility engine. Every supported pairing
remains blocked for comparison: a calculated absorption cross section is not a
transit-depth prediction. Unknown observation metadata stays explicit. Physical
model/conditions, compatible observables/units, coordinate frame, grid alignment,
response evidence and applicable uncertainty requirements must be resolved before
analysis. The research eligibility contract/adapter remain outside production.
No coordinate/unit conversion, resampling, overlay, residual, score, detection,
physical-model default, persistent pairing or database migration is introduced.

## Verification

Commands (from repository root):

- `.venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_selection_20261028/run_checks.py focused`
  — **116 passed**, 3.97 s, exit 0.
- `.venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_selection_20261028/run_checks.py full`
  — **566 passed, 1 skipped**, 8.03 s, exit 0.

Exact commands, environment key names and dependency versions are saved beside
this runner. The skip remains the existing Windows directory-symlink privilege
case. Six new checks use real offscreen widgets, temporary projects/caches and the
existing captured CO2/NASA fixtures: independent selections/navigation; source
removal/failed import; corrupt cache; removed cache; refresh preservation/duplicate
identities; metadata/hash fidelity and blocked transit-depth pairing.

During development the initial focused run exposed a Qt test-lifetime crash;
retaining the QApplication fixture for the session resolved it. A focused failure
also exposed Qt lookup of Python Path objects losing the selected cache on refresh;
using string paths fixed it. The final focused and full runs above passed after
both corrections. No production networking or data schema was changed.

New code awaits independent review in `review_selection_20261028/` and fresh human
desktop acceptance. These checks do not establish scientific validity. Real-data
scientific validation remains deferred. No network download, paid service,
credential, commit or push was used. Next: review/desktop acceptance of this
increment, then Overview/Settings content based on the implemented workflow.
