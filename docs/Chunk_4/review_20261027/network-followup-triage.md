# Network follow-up: confirmed defect reproduced and fixed

The user pasted Argon's follow-up identifying reentrant completion corruption at
nasa_network.py's old line 59, plus conditional shared-manager behavior. This is
a summary of that report and resulting verification, not a verbatim copy.

Added a sequence-manager test double that creates a separate tracked reply per
request. Its abort completion can be immediate or deferred. On overflow discovered
by the final completion drain, the failure callback starts another request.
Before the fix, both completion timings failed: the second callback ran prematurely
with an empty successful body. Other direct-cancel and readyRead overflow cases
passed; the bug is not evidence that every cancellation necessarily corrupts state.
Initial focused run: 2 failed, 52 passed. Evidence saved before changing source.

Fix: bind readyRead/finished callbacks to their originating reply. Ignore callbacks
for an inactive reply, and check identity again after the final drain, which can
reenter completion and start a new request. Clear the stored callback before
invoking it. Stale signals can no longer drain or finish the subsequent request.
Post-fix focused run: 54 passed. Final full run includes additional coverage below.

Manager contract: production remains a dedicated, parent-owned manager. Injected
managers are explicitly exclusive-use dependencies and intentionally configured
NoProxy; shared application managers are unsupported. This follows Argon's offered
documentation alternative, rather than claiming shared-manager support. Replaced
manager authentication lambdas with bound receiver methods and filter server-auth
challenges by active reply identity. Proxy authentication still cancels the active
request on this exclusive manager. A permanent leak was not independently proven;
no generalized lifetime/garbage-collection guarantee is asserted by these changes.

Added deterministic tests for immediate/deferred abort completion, overflow during
streaming/final drain, cancellation callback chaining, successful callback chaining,
late old signals, unrelated authentication, active-request rejection, invalid URL
rejection, proxy authentication, and chunked exact-limit/one-byte-overflow bodies.
Tests use Qt QObject signals/test replies, not live NASA or a claim about every
native QNetworkReply implementation's abort timing. Production-window creation and
existing queued GUI integration regressions are included in the full suite.

Executed through the existing sanitized offscreen driver:

```
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py network-reentrant-before
2 failed, 52 passed in 1.29 s; exit 1 (expected reproduction)
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py network-reentrant-after
54 passed in 1.08 s; exit 0
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py network-reentrant-full
281 passed, 1 skipped in 3.94 s; exit 0
```

Logs and exact command/environment records preserved under ECAS
docs/Chunk_4/verification_20261027/network-reentrant-*. The skip is unavailable
Windows directory-symlink privileges. No new model call, data download, dependency,
credential inspection, commit, push or delivery. The fix awaits targeted Argon
re-review; human interactive acceptance and the earlier revised-code re-review
remain pending. Prior uncommitted work was preserved.
