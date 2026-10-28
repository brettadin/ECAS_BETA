# ExoMol catalogue and local search — 2026-10-28

Implemented ecas/ingestion/exomol_catalogue.py, with real-metadata regression tests
in tests/test_exomol_catalogue.py. This is catalogue functionality, not in-app GUI
search, a runtime HTTP client/cache, product retrieval or scientific validation.

Captured the public master index in data/ExoMol/2026-10-28 with original bytes,
source/hash/timestamp provenance, attribution and licence. Retrieval was a bounded
anonymous GET (1 MiB/15-second socket timeout; isolated helper process timeout 35 s),
after an approved network retry following initial DNS restriction. No spectral
product generation/download, paid API, credentials or package installs.

## Verified catalogue structure and behavior

[Provider documentation](https://www.exomol.com/data/) links the master index and
specifies definition-file paths. The actual [master index](https://www.exomol.com/db/exomol.all)
has annotated field records, molecule-name blocks, distinct isotope identities and
dataset/version pairs. Multiple datasets can share one isotope. Local/global
unique-isotope and dataset counts are validated separately. An initial parser
assumption treating isotope count as dataset-row count failed on CO; the code was
corrected after inspecting the original file, not by weakening the totals checks.
Initial failure log is retained in verification_catalogue_20261028.

Limits: 1 MiB, 20,000 lines, 1,000 molecules, 10,000 datasets and bounded field/name
counts. Unsupported field labels, truncation, unsafe path identifiers, duplicate
dataset identities, malformed counts and inconsistent totals fail visibly. Raw
hash is retained. Eight-digit versions remain provider labels: invalid calendar
dates are warned about and preserved, never silently reformatted.

Search is exact over provider names, dataset name, formula, isotope identity and
InChI key. Names/datasets/keys ignore case; chemical formula and isotope spelling
retain case significance. Spaces normalize only for name matching, not molecular
composition. No guessed common names, fuzzy formula correction or selection of a
single result from an ambiguous alias. Results report all matched formulae, total
matches and whether a bounded result list is truncated. Search errors are exceptions,
not empty-success results. Definition URLs follow the documented pattern with
escaped path components; individual definition URLs are not fetched/validated here.

| Query on captured index | Observed result |
| --- | --- |
| Water / H2O | Same five dataset records, one molecule |
| CO2 | 13 datasets across multiple isotope identities |
| 12C-16O | Two datasets for one isotopologue |
| Phosphine | PF3 and PH3; provider alias ambiguity retained |
| Explicit nonexistent test identity | Zero matches, no truncation |

The index does not contain spectral arrays or establish product coverage, units,
temperature/pressure or reference comparability. No line list or cross section is
loaded as transit depth, and no molecular presence is inferred from a search hit.
Primary pages inspected 2026-10-28; immutable capture may lag the provider's site.

## Verification

21 new cases cover real capture/hash/counts, provider-supported name/formula/isotope
search, multiple datasets per isotope, ambiguous names, missing matches, truncation,
bounds and invalid sources. The catalogue is parsed offline in tests; no test uses
network or downloads. Captured metadata is real; malformed derivatives are synthetic.

Commands via existing isolated driver:
`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-catalogue-focused`
— 88 passed/one skipped, 0.91 s;
`.venv/Scripts/python.exe -I -B .venv/checks/audit_exomol_catalogue.py`
— exit 0, emitted parsed counts and searches;
`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-catalogue-full`
— 473 passed/one skipped, 6.25 s, exit 0.
Evidence/command metadata/source fingerprints: verification_catalogue_20261028.
Existing skip remains Windows directory-symlink privileges. Full previous scientific
prototype and application suites remain passing.

Next: connect catalogue search to a clearly labelled reference browser and implement
bounded catalogue refresh/cache lifecycle. Verify service request/download mechanics
before enabling any product button; unverified availability must remain explicit.
Parser/provider decision and this catalogue increment await independent review.
No existing app screen or NASA network trust boundary changed. Recovery archive
and prior reviewed snapshots remain intact. Changes local, uncommitted and unpushed.
