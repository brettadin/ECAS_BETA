# Chunk 4 implementation log

## 2026-10-27 — Plan-history reconciliation and catalog-discovery protocol

Current authorization: user supplied the updated development handoff and directed
work to Chunk 4. Historical PLAN/ACT/commit/push prompts inside the plan files are
context, not present execution authority. No plan document was modified.

### Context and progression

Inspected the development plan's Chunk 4 scope, guidelines, Part 1 versions 1–19,
Part 2 versions 1–9, CSV bug notes, current records and implementation. Version
headings, relevant excerpts and later review corrections were compared rather than
treating a filename saying "final" as approval of every embedded code example.

- Early Part 1 plans proposed broad NASA/MAST and NIST/HITRAN retrieval. Retrieval
  verification and data-model concerns narrowed the initial work to the local
  WASP-39 b archive CSV. Changes to SpectrumData/provenance fields were deferred.
- Later Part 1 revisions converge on explicit schema selection, archive-isolated
  parsing, retained source fields, finite numeric checks, signed-offset preservation
  and honest fixtures. Some snippets still spell actual PL_TRANDEP/PL_TRANMID fields
  incorrectly as pl_transdep/pl_transmid. Do not copy those snippets into production.
- Part 2 progresses from filename guessing (v1) to explicit schema selection,
  correct widget lifetime, GUI coverage and collaboration handoff (v2–v9).
- Local import and GUI integration are implemented and tested. Online discovery,
  spectrum retrieval, provenance-aware caching and molecular-reference libraries
  are not. The existing column-order discrepancy is recorded in PROJECT_STATE.md;
  this increment does not alter importer behavior or resolve it by rewriting plans.

### Selected increment

Add NASA planet-catalog query construction and supplied-response validation as
a bounded first discovery step. This is NOT selection or validation of a spectral
retrieval endpoint. Planet identity metadata must not become SpectrumData or be
presented as a measured spectrum. No generalized provider framework was introduced.

- `ecas/ingestion/nasa_discovery.py`: case-insensitive exact-name queries against
  pscomppars, escaped SQL literals and URL encoding, 1–100 result bounds, strict
  256 KiB supplied-JSON validation, immutable identity records, retained raw bytes
  and SHA-256, null-preserving optional metadata and explicit unverified-origin
  labeling. A full result limit is marked possibly truncated. No network, file,
  credential, UI or database operations occur in this module.
- `tests/test_nasa_discovery.py`: 35 synthetic cases covering multiple targets,
  apostrophes/injection-like names, invalid names/limits, malformed/nonfinite JSON,
  duplicate keys/records, unexpected identities/types, bounds, no matches,
  request drift, exact byte/hash retention and unknown metadata.

Primary provider documentation checked on 2026-10-27:
- [NASA TAP service](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html)
- [Planetary catalog column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/API_PS_columns.html)

These establish the documented query protocol, table and metadata fields, not a
successful ECAS retrieval. pscomppars is a composite planet catalog, not a spectral
measurement product. Alias resolution, partial-name search and scientific use of
composite parameter values are outside this increment.

### Actual verification

Executed with the existing credential-free offscreen local test driver:

```text
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py nasa-discovery
35 passed in 0.18 s; exit 0
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk4-full
193 passed, 1 skipped in 2.85 s; exit 0
```

The skip remains directory-symlink creation unavailable. Logs, exact pytest command
arrays and JUnit XML are retained in .venv/checks with those stage names. Fixtures
are synthetic; no live catalog, spectrum, NIST, HITRAN or MAST retrieval was tested.
No additional dependencies, downloads, credentials, paid AI APIs, extra agents,
commits or pushes. Official documentation was read; no archive data was downloaded.

### Next steps and proposed live validation

Subject to the user's download approval: one exact-name public NASA TAP request
for WASP-39 b, selecting only pl_name, hostname and discoverymethod, TOP 20,
JSON output. Request is built by planet_search("WASP-39 b"). Use a 10-second timeout,
256 KiB response cap, no credentials, retries, alternate endpoints or redirects;
save raw response and request/hash/time record under the project-local
`.venv/checks/nasa-live/`. A rejected/failed response is evidence, never a successful
empty result. This validates catalog discovery only.

Then implement the explicitly authorized network/application connection with
bounded requests, cancellation, provenance and a responsive UI. Actual spectrum
discovery/retrieval and registration still need their own concrete product contract
and live evidence. Investigate MAST and molecular sources separately; do not feed
line lists or calculated spectra into the observation importer or infer units.
Independent Argon review is still pending.

## 2026-10-27 — Authorized live NASA catalog and spectroscopy metadata capture

The user now authorizes gathering/downloading relevant publicly available NASA
data for ECAS. This supersedes the preceding requirement to ask again for each
NASA download. It does not authorize credentials, non-NASA downloads, paid AI
services, commits or publication. Requests here were anonymous and bounded.

### Results

1. The initial restricted execution could not resolve NASA's hostname; its failure
   provenance is retained locally. After normal network access was approved by the
   execution tool, the exact planned planet-name query returned HTTP 200 and 82
   bytes. Existing parser validation succeeded: one WASP-39 b identity, host WASP-39,
   discovery method Transit, no result-limit truncation. No credentials, cookies,
   redirects, proxy authentication or automatic retries were used.
2. Following official NASA TAP/spectroscopy documentation, fetched TOP 20 metadata
   records for WASP-39 b, sorted by bibcode/spec_path. HTTP 200, 7,288 bytes. This
   query reached its limit: it is a partial snapshot, not the complete inventory.
   It includes Feinstein et al. 2023 (2023Natur.614..670F), NIRISS, Transmission,
   331 points, spec_path 74/34/80/11/WASP_39_b_3.11466_5078_1.tbl.
3. The documented TAP table serves spectral metadata, not the measurement rows.
   NASA describes a separate spectral-file download workflow. No .tbl file was
   downloaded, no endpoint guessed and no metadata passed to SpectrumData.
   The same publication/point count does not establish equality with the bundled
   CSV; the original CSV was preserved.

Both successful calls used a 10-second outer deadline, an 8-second socket/read
budget, 256 KiB response cap and exclusive-create evidence files. Raw bodies and
UTC URL/status/size/hash provenance were copied byte-for-byte to the durable
project location `data/NASA/2026-10-27/`, with README and primary source references.
Catalog SHA-256: f3c35ec462680ae10f185db0b8f9211a06b3cf1353a5ba72efc3146ee860598e.
Spectral metadata SHA-256: 9a6e0052580ac88fabbc0477b3fc7edc75e9b10bf36f580778920c07ab266abd.

### Verification and next step

Added two deterministic captured-response tests covering exact body hashes,
provenance, actual catalog-parser compatibility, known spectral-record identity
and explicit metadata/truncation limits. These tests do not contact NASA.

Executed with the existing sanitized local test driver:

```text
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py nasa-live-captures
37 passed in 0.18 s; exit 0
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py nasa-live-full
195 passed, 1 skipped in 2.74 s; exit 0
```

The skip remains unavailable directory-symlink creation. No production network
caller/search UI is connected yet. Next: establish a documented direct spectral
file access path and inspect one actual .tbl product before adding format support;
then add bounded retrieval/registration with a responsive application flow. Preserve
dataset-specific bibliography, measurement types, units, uncertainty and hashes.
The broader NASA download authorization remains available for that work. NIST,
HITRAN and MAST integration and independent Argon review remain outstanding.

## 2026-10-27 — Real NASA measurement retrieval and application import

Continued under the user's public NASA download/development authorization. Retrieved
the actual Feinstein measurement product after deriving its URL from NASA's public
interface HTML and JavaScript, inspected as text only. main.js constructs BaseURL
from the page workspace; tab1.js appends /data/ and SPEC_PATH. No server utility
commands or downloaded scripts were executed. The generated URL is session-specific,
not a stable API template to hard-code into a production downloader.

### Retrieved product and source evidence

data/NASA/2026-10-27/feinstein-2023.tbl: HTTP 200, 184,828 bytes, SHA-256
3140d259259c51e282cd075890cc878ab79c9bb859fae3b83ab5459756e9adc2.
The raw file is unchanged; adjacent provenance records the URL, UTC timestamps,
status and hash. download-path-evidence.json records the interface source URLs and
hashes used to derive the download path. Requests were anonymous, capped at 1 MiB,
with 8-second socket limits and a 10-second outer deadline; no redirects/retries.

The product has 331 rows and 29 source columns, including signed errors, nulls,
limit flags and source URLs omitted from the older 21-column CSV representation.
It explicitly declares Transmission, microns and percent. Its REFERENCE says 2022;
the catalog publication says 2023. Both are retained, not silently reconciled.
Tests compare all 331 rows of every field represented by the bundled CSV and find
equal parsed values; byte equality is neither expected nor claimed.

### Implementation and acceptance

- Added ecas/ingestion/nasa_table.py: a deliberately strict four-header aligned
  IPAC transmission subset, based on the inspected NASA product and
  https://irsa.ipac.caltech.edu/applications/DDGEN/Doc/ipac_tbl.html . It preserves
  all source columns and units, metadata and source hash alongside SpectrumData.
  Limits: 1 MiB, 10,000 rows, header width 4,096 characters. Rejects ambiguous
  headers, unsupported types, malformed/misaligned or nonfinite numeric fields,
  missing coordinates/flags and nonzero transit-depth flags. It does not attempt
  generalized IPAC, eclipse/direct-imaging conversion or scientific validation.
- Main window Import Spectrum accepts CSV or NASA .tbl. Both existing import
  entry points route through the same file-format selection. CSV behavior/schema
  selection is preserved. Table metadata is retained in current_spectrum_details;
  replacement/failure clears it. No new database serialization contract is implied.
- Added real-product parser/integration tests and corrupted derivative negative
  cases. GUI tests verify both routes display 331 rows, 31 columns (29 source plus
  two canonical aliases), units and metadata; failed replacement clears stale data.
- Updated README and the NASA capture README with actual import instructions,
  download provenance and supported-format limits. Existing plan history untouched.

Executed with the existing sanitized offscreen test driver:

```text
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py nasa-table
28 passed in 0.92 s; exit 0
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py nasa-table-full
212 passed, 1 skipped in 2.95 s; exit 0
```

The skip remains unavailable directory-symlink creation. Logs and exact commands
are in .venv/checks. No extra dependencies, credentials, paid AI services, additional
agents, commits, pushes or external delivery. Prior uncommitted work preserved.

Remaining: online discovery UI and automatic in-app download/cache registration
are not connected. The completed application connection is local import/display
of the genuinely downloaded measurement file. A production retrieval flow must
refresh NASA's session-specific links, remain responsive, preserve provenance and
handle cancellation/errors explicitly. Independent Argon review remains pending
a route compatible with the user's billing and credential restrictions.

## 2026-10-27 — Online NASA search, download and offline cache increment

Continued the pending user-authorized NASA workflow after the real-format import
checkpoint. The bounded goal was an explicit exact-name search, selectable supported
transmission download with a fresh session, responsive network cancellation/errors,
and a provenance-preserving cache that can reopen without network access. Existing
CSV, SpectrumData and project SQLite contracts remain unchanged; generalized
providers and scientific analysis were outside this increment.

### Changes

- `ecas/ingestion/nasa_archive.py`: TOP 50 exact-name metadata query/parser, strict
  selected-record/path validation, fresh interface workspace resolution and local
  cache registration/revalidation. Retains original response bodies, source URLs,
  retrieval UTC time and SHA-256. Tables must match target/type/point count.
  Manifest written last; changed, malformed and partial entries are excluded.
- `ecas/ingestion/nasa_network.py`: Qt asynchronous client, only the needed HTTPS
  NASA host/path forms, 15-second overall request timer, 1 MiB body cap, cancellation
  and explicit HTTP/network/TLS failures. No credentials, proxy authentication,
  redirects, cookie load/save, automatic retries or startup network requests.
- `ecas/ui/nasa_browser.py` plus main-window connection: Search NASA, select and
  download, Cancel, Cached spectra and offline load in Spectral Data. Results only
  offer Transmission; a 50-record boundary warns of possible incompleteness.
- `.gitignore`: generated `data/NASA/cache/` excluded. README documents review
  steps and limits. Plan-history files were not edited; no new dependencies.

### Verification actually performed

Deterministic tests cover destination rejection, session-layout change, malformed
metadata, cache body/metadata/source changes, incomplete entries, target/count
mismatch, offline reopen, cancellation and malformed search. Qt client doubles
exercise success, redirect, oversized response, timeout, cancel, authentication,
HTTP server error and TLS failure. An initial focused run found a test-only PySide6
`rawHeader` argument mismatch; corrected from bytes to string, then 40 passed.
The subsequent full suite passed 240 with one skipped. Final self-review found
that a non-object cache manifest could abort listing valid neighboring entries;
added an explicit rejection and regression test before final verification:

```text
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py nasa-online-review
241 passed, 1 skipped in 3.48 s; exit 0
```

Python 3.14.5, pytest 9.2.0, PySide6 6.12.0, pyqtgraph 0.14.0, numpy 2.5.4.
The local driver uses a minimal credential-free environment, disables third-party
pytest plugin autoload, renders Qt offscreen, and bounds its child process to 120 s.
The exact pytest command/environment keys and output are preserved under
`verification_20261027/nasa-online-review-run.json` and `.log`. The one skipped
test requires Windows directory-symlink privileges; link rejection was separately
exercised with a test double, not represented as real privileged filesystem testing.

Executed `.venv/Scripts/python.exe -I -B .venv/checks/live_nasa_browser.py` through
a sanitized local subprocess (60-second outer deadline). Actual ECASWindow and
PublicNasaHttp, offscreen, performed three anonymous requests: metadata, a fresh
interface page, and the selected table. No substitute network client or manual
table injection was used. Results: 28 transmission records; Feinstein 2023 selected;
184,828-byte body with the previously recorded hash; 331 rows/31 columns displayed
with microns/%; after clearing the display, cached reopening restored it and did
not increase the request count. Completed at 23:55:52 UTC on 2026-10-27.
Durable raw metadata, registration and live report are under
`data/NASA/2026-10-27/`; the README there explains artifact names and hashes.

### Remaining limits and handoff

This is source-specific retrieval/cache/display, not generalized NASA/IPAC support
or scientific validation. An unrecognized source layout fails explicitly. Cache
registration is separate from project SQLite; completeness marking does not claim
crash-durable transactions or hostile-filesystem isolation. Local parsing/listing
is synchronous and large-cache responsiveness has not been established. Failed
downloads can leave excluded partial directories. Repeated downloads create new
entries; cache deduplication/retention is not implemented.

Human interactive review on the friend's host and independent Argon review remain
pending. Other providers and broader Chunk 4/analysis goals are not completed by
this increment. No real credentials, paid AI calls, extra agents, staging, commits,
pushes or external delivery were used. Prior uncommitted work was preserved.

## 2026-10-27 — User-authorized independent Argon review attempt

The user authorized Antigravity review and superseded the coordinator's historical
launch block, stating Antigravity manages billing with an automatic kill switch.
After an earlier 148-KB nested-JSON request timed out empty, implemented a separate
plain-text batch runner in the parent workspace's `argon_review_20261027/`.
No ECAS runtime code was changed in this review increment.

Five offline runner tests passed: empty SUCCESS versus explicit empty findings,
timeout overriding exit zero, known diagnostic defect acceptance, missing result/
invalid citation/tool activity, and missing coverage/duplicate JSON. The live
three-line diagnostic then succeeded: Argon identified the known indexing defect
at line 3, gave a failing example and proposed the correct index.

The actual NASA network/metadata review (21,534 characters with source line numbers
and hashes) nevertheless timed out after five minutes. Antigravity emitted SUCCESS
with an empty response and zero usage; the runner correctly recorded INCOMPLETE.
Cache and GUI batches were prepared but not invoked after that failure. No automatic
retry or model substitution. No independently reviewed ECAS findings or approval
were produced; neither the diagnostic nor the timeout approves ECAS code.

Evidence: parent `argon_review_20261027/RUNNER.md`, diagnostic-18eefc3e and
network-4e7e30ce. Existing ECAS result remains 241 passed/1 skipped; the application
suite was not rerun because only external review tooling and records changed.
Independent ECAS review and human interactive acceptance remain pending. No new
dependencies, commits, pushes, code delivery or real-credential inspection.
The user-managed billing controls were not independently certified.

## Batch 1 interactive Argon review received — 2026-10-27

User supplied the independent report; preserved verbatim in parent workspace
`argon_review_20261027/batch1-interactive-review.json`. Confirmed the target-casing
defect: lowercase query URLs disagreed with NASA's canonical metadata casing at
cache registration. Fixed comparison by decoding query parameters and comparing
the generated case-insensitive query, keeping exact endpoint/parameter structure.
Original evidence URLs remain unchanged and older canonical URLs remain valid.
Added a lowercase-search cache registration/reopen regression.

Full suite: 242 passed, 1 directory-symlink-privilege skip in 3.70 seconds, exit 0,
using `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py nasa-online-review`.
No live NASA or new Argon call was made. This fix has not been re-reviewed by Argon.

Remaining review triage: manager proxy mutation and unrelated authentication
challenges are conditional on injecting a shared manager. Production currently
constructs a dedicated manager; the supplied manager is used in tests. The claimed
reference leak is not established by this static report. Existing discovery and
destination-rejection tests outside the supplied excerpts qualify several claimed
coverage gaps. Proxy-authentication, streaming and reuse coverage still warrant
follow-up. Batch 1 is not marked fully resolved; batches 2/3 and human review remain
pending. Changes remain uncommitted.

## Batch 2 interactive Argon review received — 2026-10-27

Preserved the user-supplied report verbatim in parent workspace
`argon_review_20261027/batch2-interactive-review.json`. Assessed the four findings
against actual code, existing tests and the primary IPAC format definition.

1. Blank numeric cells: accepted in part. The parser rejected even a blank matching
   a blank column null marker; corrected that case. Rejecting a blank when the
   declared marker is the nonblank string null remains intentional. The standard
   requires exact null-marker matching, so Argon's suggestion to treat all blanks
   as missing would weaken scientific-data validation. Required coordinates/flags
   remain mandatory; empty text handling is unchanged. No demonstrated P1 failure
   of the captured NASA product was established by the static review.
2. Type casing: added case-insensitive handling for supported type labels as a
   narrow compatibility improvement. The standard leaves case policy to the
   application; this is not a claim that prior lowercase-only support was a
   universal IPAC violation. Original units, metadata and file hashes are preserved.
3. Uppercase format=JSON evidence: not adopted. Current and historical application
   queries emit lowercase json, and external arbitrary evidence URLs are not a
   supported import flow. No current application failure was demonstrated.
4. Coverage: added declared/undeclared blank and required-field tests, uppercase/
   mixed-case type tests comparing all real-product values, and direct URL tests
   for target casing (including Unicode), parameter order, duplicates, malformed
   queries, changed targets/endpoints and alternate format rejection. Existing
   cache tests in test_nasa_online.py were not missing from the repository.

The added URL cases found an actual gap: parse_qs discarded empty values, allowing
blank duplicate or unknown parameters to vanish before validation. Now retains
blank values and parses strictly; malformed input returns False. Existing original
evidence URLs and the prior target-casing fix continue working.

An initial focused run had one test-fixture error: changing a column's null header
to blank left other rows' old null tokens unchanged. Corrected the synthetic
fixture consistently; no relaxation of the parser was made to accommodate it.
Initial output is retained as argon-batch2-focused under .venv/checks.

Final full suite actually executed:
`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py argon-batch2-full`
265 passed, 1 skipped in 3.29 seconds; exit 0. The skip remains unavailable Windows
directory-symlink privileges. Durable log and command/environment metadata copied
to verification_20261027/argon-batch2-full.log and -run.json. Captured table SHA-256
remains 3140d259259c51e282cd075890cc878ab79c9bb859fae3b83ab5459756e9adc2.

No new model invocation, NASA data download, dependency, commit, push or delivery.
Batch 2 triage and code changes are locally verified, not independently approved
after revision. Batch 3 feedback, remaining batch 1 conditional-manager/coverage
work and human interactive review remain open. Older copied batch prompts are
historical snapshots and must not be presented as revised code.

## Batch 3 interactive Argon review assessed — 2026-10-27

Received the report directly in the user message. Inspected actual browser callback
handling, main-window metadata clearing, cache loading and the real SpectraPlot
implementation. Detailed finding-by-finding assessment is preserved in parent
`argon_review_20261027/batch3-triage.md` (a labeled summary, not a verbatim report).

No production defect was confirmed from these four findings. The callback wrapper
already catches handler exceptions when called asynchronously. Metadata already
clears before failed import returns. Synchronous startup exceptions already reset
busy state, as that finding's own explanation acknowledges. Cached .tbl loading
retains table metadata/units/hash and uses a validated local file; the sidecar
provenance remains on disk. A dedicated UI provenance view is a possible separate
enhancement, not demonstrated cache data loss.

Added five regression cases in test_nasa_online.py: queued Qt-event-loop interface
and table failures through the actual main window preserving the prior display;
synchronous HTTP startup failure restoring controls; and cached loading under
both CSV schemas preserving rows, units, metadata and hash without network calls,
then explicitly verifying all display/metadata state clears after a failed import.
The queued tests use fake HTTP delivery, not live NASA or arbitrary worker threads.

Actually executed with the existing sanitized offscreen driver:
`argon-batch3-focused`: 61 passed in 1.43 s; exit 0.
`argon-batch3-full`: 270 passed, 1 skipped in 3.58 s; exit 0.
Exact commands are `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py STAGE`.
Durable logs/run metadata copied to verification_20261027/argon-batch3-*. The skip
remains Windows symlink privileges. No runtime code change, external model call,
data download, dependency change, commit, push or external delivery in this increment.

All three reports are received; this is evidence-based triage, not a clean Argon
approval. Batch 1/2 fixes await targeted independent re-review, batch 1 conditional
shared-manager/lifecycle follow-up remains open, and human acceptance is pending.

## Batch 1 network follow-up — reproduced and fixed

User supplied Argon's reentrancy finding and conditional shared-manager assessment.
Added a separate-reply sequence-manager regression with immediate/deferred abort
completion. Both final-drain overflow cases failed before the fix: a callback
started a new request, then the old completion handled the new reply and invoked
its callback prematurely with an empty successful response. Direct cancellation
and streaming overflow did not fail in these initial scenarios.

Bound reply signals to their original reply, reject inactive-reply callbacks, and
recheck identity after draining because it can abort/reenter completion. Clear the
stored callback before invoking it. Documented injected managers as exclusive-use
dependencies, matching production's dedicated-manager policy; they intentionally
receive NoProxy configuration and are not a shared-manager API. Authentication
uses bound methods and filters server challenges by active reply identity.

Added coverage for chained failure/success callbacks, immediate/deferred abort,
stale old reply signals, proxy authentication, unrelated server authentication,
request reuse/active rejection, invalid destinations, and multi-event bodies at
exact size limit/one byte beyond it. Uses Qt-signal test doubles; does not assert
that all native abort paths have a particular timing. Existing actual-window
integration tests also pass. No speculative memory-leak fix is claimed as proven.

Executed via `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py STAGE`:
network-reentrant-before: 2 failed, 52 passed in 1.29 s, exit 1 (reproduction).
network-reentrant-after: 54 passed in 1.08 s, exit 0.
network-reentrant-full: 281 passed, 1 skipped in 3.94 s, exit 0.
Durable logs/run metadata are in verification_20261027/network-reentrant-*.
Skip remains Windows symlink privileges. Detailed report assessment is in parent
argon_review_20261027/network-followup-triage.md. Targeted independent re-review
of revised code and human interactive acceptance remain pending. No new external
model call, download, dependency, credentials, commit, push or delivery.

## GitHub human-review publication preparation — 2026-10-27

The user now explicitly authorizes publishing the current ECAS version to GitHub
for human review. This supersedes the earlier no-commit/no-push restriction for
this publication only; it does not authorize merging master or claiming final
Argon acceptance. Prepared branch codex/nasa-transmission-review-20261027 from
the tested base 6da2dcc. GitHub master had advanced one commit to 5deb267; its
overlapping CSV/import-manager changes were fetched and inspected but not merged
into the tested version. The branch handoff explicitly discloses that integration
is still needed. Parent coordinator changes are excluded from this publication.

Added portable review summaries and HUMAN_REVIEW.md under review_20261027, linked
from the README. Targeted independent re-review and human acceptance remain open.
Public NASA captures are included as required offline test inputs; generated
cache, .venv, credentials and local project databases are excluded.

Staging exposed Git newline conversion of raw captures. Added scoped .gitattributes
and re-added only the NASA capture directory with the byte-preserving attributes.
Verified all ten staged NASA JSON/table bodies match original bytes; source-table
whitespace and captured diagnostic formatting are intentionally preserved.
Credential-pattern scan of the staged files found no matches; it is a heuristic.

Exported the staged index to a fresh checkout inside ignored .venv/checks and ran
its full suite with the existing Python environment, isolated profile/temp paths,
third-party pytest plugin autoload disabled and offscreen Qt: 281 passed, 1 skipped
in 3.61 seconds, exit 0. This check validates the staged package rather than relying
on ignored working files. Exact command, capture hashes and output are in
verification_20261027/review-package.json and .log. Only review documentation and
evidence additions followed this check. No new dependencies or model calls.
