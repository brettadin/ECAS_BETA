# Public NASA archive captures — 2026-10-27

These are unchanged HTTP response bodies retrieved anonymously from the NASA
Exoplanet Archive's documented TAP service. Each has a separate provenance JSON
record with its exact query URL, UTC request/finish times, HTTP status, byte count,
SHA-256, limits and validation outcome. No credentials, cookies, redirects or
automatic retries were used. Both successful requests finished within 10 seconds
and remained below the 256 KiB cap. The initial restricted-session DNS failure is
recorded separately under `.venv/checks/nasa-live/`; it is not counted as a retrieval.

| Capture | Content | Limitations |
|---|---|---|
| planet-wasp39b.json | One catalog identity: WASP-39 b, host WASP-39, discovery method Transit | Not spectral measurements or an alias-resolution test |
| wasp39b-spectra-metadata.json | First 20 WASP-39 b spectral metadata records, ordered by bibcode/spec_path | TOP 20 reached: incomplete inventory; no measurement files downloaded |

The spectral metadata includes `2023Natur.614..670F`, Feinstein et al. 2023,
Transmission, NIRISS, 331 points, with `spec_path`:
`74/34/80/11/WASP_39_b_3.11466_5078_1.tbl`. This identifies a record from the same
paper and with the same row count as ECAS's bundled CSV. It does not establish
byte/value equality with that CSV, which was not replaced or reinterpreted.

According to NASA's documentation, only spectrum-level metadata columns are
available from this TAP table. Measurement files are separately downloaded through
the archive's spectral-file workflow. No guessed file URL or conversion from these
metadata into a SpectrumData object was attempted. The .tbl file format and units
must be inspected before implementing a parser or adapting an existing importer.

References and attribution:
- [NASA TAP documentation](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html)
- [Spectral data-column definitions](https://exoplanetarchive.ipac.caltech.edu/docs/atmospheres/atmospheres_columns.html)
- [NASA spectrum download workflow](https://exoplanetarchive.ipac.caltech.edu/docs/atmospheres/atmospheres_work.html)
- [Archive citation and DOI guidance](https://exoplanetarchive.ipac.caltech.edu/docs/doi.html)

Retain the source publication identifiers and cite the underlying publications and
archive appropriately when using these records. Hashes establish byte identity,
not independently authenticated historical provenance or scientific validity.
Tests read these frozen captures locally and do not contact NASA.

## Subsequently retrieved measurement product

`feinstein-2023.tbl` is the actual 184,828-byte NASA product (331 rows, 29 source
columns), SHA-256 `3140d259259c51e282cd075890cc878ab79c9bb859fae3b83ab5459756e9adc2`.
Its adjacent provenance JSON preserves the successful anonymous HTTP 200 retrieval
URL and UTC timestamps. Unlike the two JSON responses above, it contains measurements.

The URL was derived from NASA's public page and its own JavaScript URL construction,
not guessed: `applications/atmospheres/js/main.js` sets BaseURL from the page's
workspace; `tab1.js` appends `/data/` and SPEC_PATH. The generated workspace URL is
session-specific and must not be treated as a stable download API.
`download-path-evidence.json` retains source URLs/hashes for that derivation.
Remote scripts were inspected as text and never executed.

The table declares wavelength `microns`, transit depth `%`, and SPEC_TYPE
Transmission. It retains references, signed uncertainty columns, flags and URLs.
Its REFERENCE header says Feinstein et al. 2022; the separately captured catalog
metadata says Feinstein et al. 2023 / 2023Natur.614..670F. Both values are retained,
not silently reconciled. The source file is not modified.

An automated comparison verifies all 331 rows of all 23 fields represented in
the bundled CSV match this product's corresponding values. The .tbl additionally
has limit/provenance URL fields and explicit units; byte identity is not claimed.

## Subsequently verified online application workflow

The actual ECASWindow, rendered offscreen, searched NASA and downloaded the same
Feinstein table through the new Qt client on 2026-10-27 at 23:55 UTC. It then cleared
the displayed spectrum and reopened the validated cache entry without another
request. This was an automated application check, not human interactive approval.

- `nasa-ui-live-result.json`: request URLs, response sizes/hashes, start/finish
  timestamps and observed application results (28 transmission records, 331 rows,
  31 displayed columns, microns/% and offline reopening).
- `wasp39b-spectra-metadata-top50.json`: unchanged 11,355-byte metadata response,
  SHA-256 `310a2b671069ed7599326231df02b53e719677eaf33692d0543f2e8cbdf3d41d`.
  This later TOP 50 query differs from the earlier partial TOP 20 capture.
- `nasa-ui-cache-record.json`: the generated entry's registration/provenance,
  including the exact query and selected record. Original `metadata.json` was
  copied here under the descriptive TOP 50 filename; this directory is an evidence
  bundle, not itself a production cache entry.

The raw table hash matched `feinstein-2023.tbl` above, so no duplicate table copy is
needed here. The diagnostic cache path in the live report is project-local under
ignored `.venv/checks/`; ordinary application downloads use `data/NASA/cache/`.
Each live request was capped at 1 MiB/15 seconds, without authentication, cookies,
redirects or retries. The source URLs remain session-specific historical evidence.
