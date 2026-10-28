# Reference browser, catalogue refresh and cache — 2026-10-28

## Implemented behavior

The Comparisons tab now contains Molecular reference catalogue search. Startup
loads a validated cached index if present, otherwise the bundled dated snapshot.
It creates no ExoMol network manager or request until Refresh from ExoMol is clicked.
Search names, formulae, isotope identifiers, dataset names and InChI keys offline.
Results show formula/isotopologue/dataset/version; selected details retain provider
names and identity. Ambiguous aliases and truncated/no-match states are explicit.
Product type, range, units and temperature/pressure remain unestablished by the
master index. No spectrum download, observational-data selection or scoring exists
on this screen yet. Do not interpret catalogue membership as spectral availability.

Dedicated PublicExomolCatalogueHttp requests only the fixed HTTPS master-index URL.
It has an overall 15-second timer, 1 MiB raw limit, bounded reads, manual redirects,
no cookies/authentication reuse, dedicated NoProxy manager and cancellation. Auth
requests fail. Injected test managers must be exclusive-use dependencies. NASA's
client and URL policy were not widened; a small provider-specific client keeps
that earlier trust boundary intact. Active-reply identity checks prevent old
signals/overflow cancellation from corrupting a chained request. Shutdown prevents
reuse, stops/cancels work and disconnects manager authentication handlers.

Catalogue cache: ignored data/ExoMol/cache/catalogue.json, one versioned JSON envelope
containing raw metadata bytes in base64, raw SHA-256, exact source URL and UTC
retrieval timestamp. It is bounded to 2 MiB when read; raw content is re-parsed and
hash/source/schema/timestamp checked on reopen. A temporary sibling file plus
os.replace registers a complete snapshot atomically. Failed validation/write keeps
the previous snapshot. Direct linked cache roots/files are rejected. Hashes detect
changes, not hostile forgery or scientific authenticity. Invalid cache is reported
and the bundled snapshot is used; it is not silently treated as a fresh download.

The UI disables conflicting actions while refreshing, supports cancel, preserves
the previous catalogue/results on failure and ignores late callbacks after close.
Reopening cached metadata needs no network and does not create the network manager.
Import/display/project values are unaffected. Application constructor optionally
accepts reference_cache_dir for isolated testing.

## Verification

24 new cases exercise UI controls, ambiguity, selection, refresh/cancel/start/disk
failures, atomic old-cache preservation and temp-file cleanup, corrupt/missing
cache, actual-window integration, real Qt-manager lifecycle, fixed-origin anonymous
request policy, deadline/auth/proxy/HTTP/redirect failures, overflow/chained requests
with synchronous and delayed abort signals, shutdown and stale-callback rejection.

Initial focused assertions passed but process exited with native Qt shutdown error
3221226505. This was a failed run, not accepted evidence. Isolated network/UI runs
passed; repeated real-window tests exposed the interaction with eagerly constructed
unused managers. Lazy ExoMol manager creation plus explicit shutdown was added.
The session-lived QApplication fixture avoids recreating it between modules; tests
close their own widgets and do not globally delete other modules' Qt objects.
New repeated real-manager refresh/close tests and final combined/full runs exit 0.
The initial failure/exit metadata is preserved in verification_browser_20261028.

Final isolated driver commands:

- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-browser-focused`
  — 131 passed, one skipped; 2.55 s, exit 0.
- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-browser-full`
  — 497 passed, one skipped; 8.69 s, exit 0.

Skip remains unavailable Windows directory-symlink privileges. During test
development one rawHeader assertion used bytes instead of Qt's required str; fixed
before the final clean runs. No failed run is counted as a passing milestone.

Live offscreen check:
`.venv/Scripts/python.exe -I -B .venv/checks/verify_reference_ui_live.py`.
Restricted-network attempt reported Host not found and preserved the previous
snapshot. An approved anonymous network retry succeeded using the actual window,
Qt client and cache: raw SHA-256
`3bc26ed45c5483839ee7a17ce4b135bdd5b2230147b6c261e07102884ffe646c`, five Water entries.
A new window reopened the saved test cache, found the same entries and had no
ExoMol network client. Live-success/failure JSONs preserve actual UTC times and
isolated ignored cache paths. This validates metadata workflow, not spectroscopy.

## Limits and next step

New screen, cache/client and catalogue/parser increments await independent review.
Earlier user manual acceptance and independent-review confirmation concern prior
work; this new screen has only automated/offscreen verification, not fresh human
desktop visual acceptance. Real-data scientific validation remains deferred.
No molecular spectrum was retrieved or generated; only public catalogue metadata.
No new package, real credential, paid reviewer, Git commit or push. Recovery archive
and original raw catalogue capture remain unchanged.

Next verify ExoMol product-request fields and anonymous response/download mechanics,
retain explicit temperature/pressure/grid parameters, and add bounded spectral
retrieval/cache. Never enable product retrieval based solely on a master-index hit.
Catalogue refresh has no automatic retry, expiry or downgrade policy; the UI shows
snapshot/version/retrieval context, so search results must not be advertised as
current or complete provider inventory without checking freshness.
