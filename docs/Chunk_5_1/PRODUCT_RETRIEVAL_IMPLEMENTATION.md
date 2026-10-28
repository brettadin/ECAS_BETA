# Bounded CO2 reference retrieval — 2026-10-28

Historical CO2-only checkpoint. Later verified water/methane mappings and current
UI location are recorded in `USER_FEEDBACK_WORKFLOW_20261028.md`, step 4.

This increment supersedes the product-retrieval pending items in the earlier
provider, catalogue and browser notes. Chunk 5.1 remains in progress. New code
requires independent review and fresh human desktop acceptance; earlier approvals
apply to their earlier snapshots. Real-data scientific validation remains deferred.

## Implemented workflow

In Comparisons, search **CO2**, select **12C-16O2 / UCL-4000**, choose temperature,
wavenumber bounds and spacing, then **Download selected reference**. This is the
only verified service mapping; other catalogue records remain searchable but
retrieval is explicitly unsupported. Defaults (500 K, 4000–4010 cm^-1, spacing
1 cm^-1) are a small reference-product preset, not inferred planetary conditions.

The client retrieves the public form, submits its anonymous anti-forgery state
with the selected settings, then retrieves the matching two-column .sigma file.
The fixed [CO2 service](https://www.exomol.com/xsec/12C-16O2/) identifies UCL-4000,
zero pressure and Doppler-only broadening. The parser checks those descriptions,
form action/fields and exact returned product identity before accepting the data.
Service changes fail visibly rather than widening the supported protocol.

Supported requests require whole-number 100–4000 K temperatures and 0–20000 cm^-1
bounds, positive spacing with at most six decimals, and an exactly divisible
inclusive grid of 2–10000 points. These are application support limits, not a
claim that every allowed combination is empirically verified or scientifically
appropriate. Returned count and coordinates must match; coordinate comparison
allows 5e-7 cm^-1 for the provider's six-decimal output. Cross sections must be
finite/nonnegative and the axis strictly increasing.

Successful retrieval displays a read-only wavenumber/cross-section table and
stores an atomic, versioned cache envelope under ignored
`data/ExoMol/cache/references/`. **Open cached reference** reparses and validates
the saved original bytes without creating either ExoMol network client. The
reference remains separate from the currently loaded observational SpectrumData.
There is no conversion to transit depth, comparison score or molecular detection.

## Network, storage and provenance

- Dedicated Qt manager; only the fixed HTTPS form and exact matching product URL.
  No redirects, account credentials, email, proxy environment or authentication
  reuse. A fresh anonymous CSRF cookie is sent only to the form POST, never to the
  product GET. Tokens/cookies remain transient and are absent from caches/logs.
- Overall 30-second deadline; HTML pages at most 256 KiB, product at most 1 MiB,
  reads bounded to 64 KiB. Cancel, close, HTTP/auth/protocol/overflow failures reset
  state. Reply identity checks protect requests started by a previous callback.
- Cache envelopes at most 2 MiB: original bytes, source SHA-256, settings, explicit
  type/units/conditions, source URL, three provider/dataset citations, CC BY-SA 4.0
  URL, UTC retrieval time and a checksum binding the record. New records also
  retain selected catalogue identity/version/hash. Reopening checks and reparses
  these fields; direct linked roots/files are rejected. Checksums detect changes,
  not malicious forgery or independent scientific authenticity.
- Early v1 records lacking catalogue context or containing the earlier two
  citations remain readable without fabricating missing metadata or rewriting
  them. New records retain the complete citation set.
- Conflicting controls are disabled while busy; cancel/failure retains the previous
  reference. Unsupported selection, invalid settings/cache and request failure
  have visible explanations. Catalogue search/refresh remains independently usable.

## Executed verification

Final isolated driver commands:

```
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-product-focused
.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-product-full
```

Focused: **172 passed, 1 skipped**, 2.80 s; full: **538 passed, 1 skipped**, 7.20 s.
Both processes exited 0. Existing skip: unavailable Windows directory-symlink
privileges. Exact pytest invocations, runtime versions, environment-key names and
logs are in `verification_product_20261028/`; the checkout-local sanitized driver
is ignored. A fresh environment with declared dependencies can run
`python -m pytest -q -o pythonpath=.`; tests use captured fixtures/fakes, not live
downloads.

The 41 new cases cover captured form/result/data, request/grid bounds, altered
service descriptions/fields, wrong product links, cache integrity/provenance and
atomic failure, legacy cache compatibility, GET/POST/GET policy, timeout/cancel/
auth/redirect/overflow failures, reentrant callbacks, actual-window integration,
offline reopening and preservation of the previous reference/observation.

Initial focused assertions passed but Qt teardown exited 3221226505; that run is
preserved as failed evidence. Replacing a self-capturing combo-box signal lambda
with a bound method resolved the lifecycle issue. Final combined/full runs exited
cleanly. No failed run is counted as a passed milestone.

An approved live offscreen check used the actual window and Qt client to download,
validate/cache and reopen **11 points**, CO2 / 12C-16O2 / UCL-4000, 500 K,
4000–4010 cm^-1, spacing 1 cm^-1, zero pressure, Doppler-only. Raw SHA-256:
`d323b5dd2f11c87a3cd6c0dc041fd625f00d56ec05cc2f2f2fb756cb01ea9fab`.
The reopened reference was equal and neither network client was created offline.
The initial restricted-network DNS failure and approved successful retry are both
recorded. This live check preceded the additional catalogue-context field and
third citation; final offline tests cover those additions and legacy compatibility.

Public raw product, result-page bytes and provenance are in
`data/ExoMol/2026-10-28/`. The form fixture explicitly replaces its transient token
with synthetic text; its provenance distinguishes original and transformed hashes.
It must not be described as an unmodified form capture. No reusable token or
account state is published.

Offscreen layout inspection reduced the minimum window width to 986 pixels, but
the local rendering environment lacked normal font glyphs. It verifies geometry,
not readable desktop typography. Fresh human visual acceptance remains open.

## Remaining scope

Independent review of the Chunk 5.1 parser/catalogue/network/cache/UI work, normal
desktop acceptance, additional verified molecule/provider mappings, and explicit
observation/reference pairing through the eligibility contract remain open.
Cross sections cannot be compared directly with transmission depth without a
physical model. No atmospheric inference or new paid dependency/service is added.
