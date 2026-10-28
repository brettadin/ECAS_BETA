# Batch 3 interactive feedback — assessed against code and runtime tests

This is a summary/triage of the report pasted directly by the user, not a verbatim
copy or an independent Argon approval of subsequent changes. Review scope:
nasa_browser.py, selected main_window.py methods, test_main_window.py and selected
test_nasa_online.py functions.

1. **P1, nasa_browser.py:159, uncaught asynchronous page exception — not
   substantiated.** `_request` passes `completed` to HTTP. When HTTP invokes it,
   `completed` executes `handler(raw)` inside its own try/except. That still applies
   when invoked later; it does not depend on the initial `get` call's stack.
   Added Qt-event-loop queued tests for both changed interface HTML and invalid
   downloaded table bytes, through the actual ECASWindow. Both failures restored
   controls, reported the error, left no accepted cache entry and preserved the
   prior spectrum, metadata, table and plot. HTTP delivery was a test double;
   no live NASA request or arbitrary worker-thread callback was tested.
2. **P2, main_window.py:349, stale metadata after clearing — contradicted by
   existing assignment.** `_clear_spectrum_display` already sets
   current_spectrum_details to None before the import handler returns. Added cache
   integration tests explicitly check metadata/plot/table clearing on a subsequent
   failed import. No redundant assignment or rewrite was necessary.
3. **P2, nasa_browser.py:111, controls disabled after synchronous get failure —
   not a defect, as the review explanation itself states.** Added a direct
   throwing-get test confirming enabled controls, cleared busy state and error text.
4. **P3, cache load silently discards provenance/schema context — not established
   as current data loss or wrong schema.** The cache manifest remains on disk;
   read_cached validates it before emitting a .tbl path. Main-window dispatch
   reparses that table and retains its metadata/hash/units in
   current_spectrum_details. Added actual-window cached-load tests with both CSV
   schema choices; all 331 rows, 31 columns, units, metadata and matching source
   hash remained available without HTTP calls. Inspection of the real plot helper
   also resolves the report's missing plotting context for this input.

The sidecar catalog record is not attached to the current SpectrumData or shown
in a dedicated provenance view. That is a known possible UI enhancement, not
evidence that the cache deleted it. No public signal/schema expansion was made.
The browser's message accurately says the spectrum was sent to display, rather
than claiming a consumer's display operation succeeded.

Executed in the existing sanitized offscreen test environment:

```
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py argon-batch3-focused
61 passed in 1.43 s
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py argon-batch3-full
270 passed, 1 skipped in 3.58 s
```

Both exit codes zero. Skip: unavailable Windows directory-symlink privileges.
Five new regression cases; no ECAS production code changes in this increment.
Durable execution logs and command/environment metadata are in the ECAS
docs/Chunk_4/verification_20261027 directory. No extra model invocation, NASA
download, credentials, dependency changes, commit, push or delivery.

All three interactive batch reports have now been received. Batch 3 has no
confirmed blocking finding after these checks; this assessment is Codex's triage,
not Argon's acceptance. Batch 1/2 revised code still needs targeted independent
re-review, batch 1 shared-manager/lifecycle follow-up remains open, and human
interactive acceptance remains pending.
