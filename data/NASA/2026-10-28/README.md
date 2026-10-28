# NASA name-resolution and spectral-inventory evidence — 2026-10-28

Anonymous bounded metadata retrievals under the user's NASA authorization.
Original response bytes are unchanged. provenance.json records alias URLs,
HTTP statuses, times, sizes and hashes; inventory-provenance.json records the
canonical-name TAP queries. Each response was capped at 1 MiB with an 8-second
request timeout, without proxies, authentication, redirects or retries.

| Input | Resolved planet | Returned inventory |
|---|---|---|
| WASP39b | WASP-39 b | 31 records: 28 transmission, 3 eclipse |
| TRAPPIST-1e | TRAPPIST-1 e | 6 transmission records |
| Kepler-452b | Kepler-452 b | Empty array |
| Proxima Centauri b | Proxima Cen b | Empty array |

These are snapshots of this archive's queried spectroscopy table, not claims
about all observations elsewhere, scientific suitability or detections. No
measurement/FITS file was retrieved in this investigation. Whole-system alias
responses are retained; only one explicitly requested planet consistent with
the manifest is eligible for automatic selection. Host-only or ambiguous
responses must not silently select another listed planet.

Primary documentation: https://exoplanetarchive.ipac.caltech.edu/docs/sysaliases.html
and https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html . Actual
offscreen application results are preserved in the project under
docs/Chunk_4/verification_20261028/live-search-result.json.
