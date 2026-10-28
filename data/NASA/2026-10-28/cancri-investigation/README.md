# 55 Cancri e investigation — 2026-10-28

Small public metadata captures, not downloaded spectra or scientific validation.
Original successful response bytes are unchanged. `capture-provenance.json`
records exact URLs, UTC timing, byte counts, SHA-256 and HTTP status. Captures use
anonymous HTTPS GETs, no credentials/cookies/proxy environment/redirects, a 1 MiB
response bound and request timeouts. No retry loop or product download.

- `long-name-aliases.json`: 55 Cancri e resolves to 55 Cnc e.
- `short-name-aliases.json`: 55 Cnc e resolves to 55 Cnc e.
- `canonical-spectra.json`: the application's exact spectra query for 55 Cnc e
  returns 23 records: four Transmission and 19 Eclipse. All pass the existing
  metadata parser; only Transmission records are supported for loading.
- `long-name-direct-spectra.json`: querying the spectra table directly with
  55 Cancri e returns an empty array. This demonstrates the need for alias lookup;
  it does not establish that the current application skips that lookup (it does not).
- `restricted-network-failure.json`: initial DNS failure, preserved separately.

The compact spelling 55Cancrie request timed out. Its provenance entry describes
failure; no response file exists for that request. Do not infer name rejection or
absence of spectra from the timeout. The inventory continuation reused the two
successful, hash-checked alias captures rather than requesting them again.

Provider: NASA Exoplanet Archive, https://exoplanetarchive.ipac.caltech.edu/ .
Alias protocol: https://exoplanetarchive.ipac.caltech.edu/docs/sysaliases.html .
Publication attribution, author, instrument and facility fields are retained in
the original inventory. This snapshot is dated evidence, not a promise that the
archive inventory will remain unchanged. `.gitattributes` preserves NASA JSON bytes.

The exact cause of the earlier user-reported zero result remains unestablished.
Current code, captured-response regression tests and an actual-window live search
all return four transmission results. See
`docs/Chunk_5_1/USER_FEEDBACK_WORKFLOW_20261028.md`, step 3.
