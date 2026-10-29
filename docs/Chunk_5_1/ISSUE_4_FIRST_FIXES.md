# Issue #4 — first fixes

Local increment after published `49e3b96`; independent review and targeted user
desktop confirmation remain pending. No commit/push is performed by this increment.

## Cache choices

store_reference now reuses a fully validated existing record only when the exact
request, parsed provenance, raw-source SHA-256 and catalogue context all agree.
The original record bytes and original retrieval timestamp remain unchanged.
Different source bytes (even numerically equivalent), conditions, citations or
catalogue contexts remain distinct. This is reuse of a saved product, not an
audit log of every retrieval attempt. Corrupt entries are not reused.

cached_references groups existing exact duplicates for presentation without
deleting/rewriting any original files. Invalid-entry counts still count invalid
files, not hidden duplicates. Deterministic path ordering chooses a representative.
Distinct records with otherwise similar labels now include short source-hash and
record-ID suffixes in Molecular References. Comparisons already carries record IDs.
No cache migration or schema change. There is no cross-process writer lock;
simultaneous independent writers can still create equivalent files, which the
reader groups. The normal single-window sequential download path reuses its record.

## Observation labels

Comparison additions capture a metadata-derived description at the same time as
the existing deep-copied values. Available saved archive descriptions take priority
over table descriptions; table REFERENCE/PL_NAME/INSTRUMENT are used when available,
and a missing publication falls back to the filename. Source descriptions are not
corrected or inferred. Unique session numbers remain, and later imports cannot
change earlier choice labels. No source file read, stored-data rewrite or scientific
meaning is added. Full conflict-attribution tooltips remain a future enhancement.

## Download display report

Not reproduced with the offline actual-widget completion sequence. A new check
explicitly empties displayed table cells before both the first and repeated
successful download, completes the callback, then verifies redraw/current product
and the selected cached identity without clicking Open cached reference. This
passes. Existing navigation-during-request checks remain. No speculative display
fix was introduced; the user-reported live symptom remains open pending targeted
reproduction with the selected request/status/display identity. No live request
was performed for this increment.

## Verification and remaining work

Runner: `.venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_issue4_20261028/run_checks.py focused`
— 124 passed, 5.48 s, exit 0 before the final cache-label suffix addition.
Final full run (`run_checks.py full`): **574 passed, 1 skipped**, 9.19 s, exit 0.
Exact commands/versions are recorded beside this runner; the skip remains Windows
directory-symlink privileges.
Three new cases cover immutable repeated-write reuse, legacy-duplicate grouping
with preserved files and distinct context, immediate repeated-download redraw,
and stable metadata-derived session labels (one case combines the cache assertions).
Existing distinct-choice fixture now deliberately uses different raw bytes;
atomic failure coverage requests a genuinely new context instead of a reused record.

Next: independent review, targeted desktop check, then clarify supported-product
discovery and add native-unit reference plots/readable graphical inspection.
Shared transit-depth/cross-section overlays remain blocked without a physical model.
Scientific validation remains deferred. Unrelated runtime/parent files are preserved.
