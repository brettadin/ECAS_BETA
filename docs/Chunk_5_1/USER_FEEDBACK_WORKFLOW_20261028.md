# User-feedback workflow — 2026-10-28

The user approved this implementation order after a read-only reconciliation of
the primary user's feedback with the current code and roadmap. Work is local
after published review checkpoint `98abaec`; publication is a separate action.

## Approved order

1. **Implemented locally:** Make project spectra identifiable from saved metadata.
2. **Implemented locally:** Separate Molecular References from Comparisons, reusing
   the existing browser.
3. **Investigated:** Current 55 Cancri e search returns four transmission records;
   the earlier reported zero result was not reproduced. Returned/excluded counts
   are clearer; resolution/query/filtering behavior is unchanged.
4. **Implemented locally:** Verified water / POKAZATEL and methane / MM product
   mappings alongside CO2, each checked against its own form/product/conditions.
5. **Implemented locally, Argon zero findings:** independent observation/reference selection, separate inspection and
   compatibility explanations. Overlay/residual operations require suitable
   observables, units, grid/response evidence and applicable eligibility checks.
6. **Implemented locally, Argon zero findings:** Overview/Settings content based on the implemented research workflow.

For each increment: inspect, implement, run focused checks, check related behavior,
update the handoff, and group completed changes into manageable Argon batches.
No additional paid reviewer/agent is invoked. New code still needs independent
review and desktop acceptance. Scientific validation remains deferred.

## Step 6 continuation — workspace pages

The user accepted Argon's first six code reviews and authorized pipeline
continuation. Overview now supplies workflow shortcuts and page-entry summaries
of in-memory observation/reference/comparison state. Settings exposes configured
paths read-only and synchronizes the established session CSV choice with Spectral
Data. Both pages scroll at smaller sizes. Source/storage values and independent
selections remain unchanged. See `WORKSPACE_PAGES_IMPLEMENTATION.md`.
Focused: 121 passed, 5.82 s; full: 571 passed, 1 skipped, 11.15 s; exit 0.
Evidence: `verification_workspace_20261028/`; new review batch:
`review_workspace_20261028/07-workspace-pages.txt`. This increment still requires
review and normal-desktop acceptance. Scientific validation remains deferred.
Next: those acceptance checks and remaining Chunk 5.1 roadmap reconciliation.

Batch 7 subsequently returned zero findings for four explicitly listed files.
Report/scope disposition: `review_workspace_20261028/07-argon-report.json` and
`07-disposition.md`. Original manifest/prompt matched before receipt and remain
preserved. No source fix or test rerun was required. All seven feedback batches
have zero findings in their stated scopes. Remaining acceptance and production
boundaries are reconciled in `ACCEPTANCE_STATUS_20261028.md`; normal-desktop
acceptance remains open, scientific validation deferred.

## Continuation — five reports received and step 5 implemented

All five Argon reports supplied by the user have zero findings. Manifested source
hashes matched the working tree before continuation. Scopes, exact limitation
text and the correction to Batch 3's causal summary are in
`review_feedback_20261028/RECEIVED_REPORTS.md`. No corrective code was required.
This completes receipt of those five scoped reports, not desktop/scientific acceptance.

Step 5 now provides explicit session observation snapshots and independent cached
reference choices in Comparisons, separate read-only tables, cache validation and
conservative blocked comparison explanations. No overlay, residual or general
production eligibility service is enabled. Instructions, boundaries and test
evidence: `COMPARISON_SELECTION_IMPLEMENTATION.md`. Focused: 116 passed (3.97 s);
full: 566 passed, 1 skipped (8.03 s), exit 0. New review batch:
`review_selection_20261028/06-comparison-selection.txt`. Desktop acceptance remains
open and scientific validation deferred. Historical per-step notes follow.

Batch 6 subsequently returned zero findings. Its exact report and disposition are
in `review_selection_20261028/06-argon-report.json` and `06-disposition.md`.
All manifested files and the prompt matched before receipt. Cache damage is
detected on selection/refresh, not continuously despite the report's "immediately"
wording. No corrective code change or test rerun was required. All six feedback
batches have zero findings; desktop acceptance remains open. Next approved
implementation work: Overview/Settings content.

## Step 1 — Project spectrum identification

`ecas/ui/project_labels.py` is a presentation helper called by ProjectBrowser.
It uses already loaded ProjectSpectrum records and does not open source/cache
files or write the database. No schema migration or stored attachment change.

List heading: record ID, saved planet name and archive authors/publication when
available; fallback to the table's REFERENCE and then the source filename. The
second line shows available instrument/type plus row count and attachment status.
Generic and legacy records retain filename fallbacks, with no fabricated identity.
Record IDs distinguish attachments sharing the same publication/instrument.

Tooltips expose original filename/path, separately attributed archive/table planet,
publication, instrument, facility and type, archive bibcode, imported coordinate
range/unit and source hash when established. The range describes the loaded
numeric wavelength coordinates, not assumed units for archive min/max fields.
Unknown units remain explicit. Tooltip text is escaped before Qt rich-text formatting.

The real fixture's archive citation is Feinstein et al. 2023 and its table header
says Feinstein et al. 2022. The heading prefers the archive listing; the tooltip
retains both and explains that differing descriptions were not corrected. No
publication-year inference, source rewriting or integrity-hash update occurs.

## Verification

Executed with the existing isolated, minimal-environment test driver:

- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py project-labels-focused`
  — **84 passed, 1 skipped**, 3.82 s, exit 0.
- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py project-labels-full`
  — **547 passed, 1 skipped**, 9.40 s, exit 0.

Exact pytest commands, versions and logs are in
`verification_labels_20261028/`. Existing skip: Windows directory-symlink privileges.
Nine new cases cover saved archive/table facts, conflicts, missing/malformed optional
descriptions, legacy/generic fallbacks, escaped text, distinct IDs, no source reads,
and byte-identical database preservation through label generation/offline reopening.
The existing real-window cached-NASA test additionally checks the displayed label
and tooltip after original cache removal under both CSV dropdown settings.
Tests use temporary project data and recorded fixtures, with no live requests.

Fresh normal-desktop inspection and independent review of this change remain open.
No new desktop screenshot or acceptance is claimed.

## Step 2 — Separate reference browsing and comparison

The navigation now has Overview, Projects, Spectral Data, Molecular References,
Comparisons and Settings. The existing MolecularReferenceBrowser remains one
long-lived widget on its own page. Projects and Spectral Data keep their indices
and behavior. Comparisons is an explanatory placeholder, with no selection,
overlay, compatibility engine, scoring or detection claim. Its text explains that
calculated cross sections cannot be compared directly with transit depth without
a physical model. Existing source/parser/cache protocols are unchanged.

Actual-window tests verify all navigation items map to their pages, that reference
controls appear only on Molecular References, and that search query/results/
selection and the loaded observation survive navigation. The download integration
test switches to Comparisons during a pending request, completes it without an
automatic page change, returns to the reference table, and checks the reference
survives further page changes. Existing cancellation, shutdown, offline cache and
project reopening tests remain in the suite.

Executed isolated driver commands:

- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-product-focused`
  — **173 passed, 1 skipped**, 2.95 s, exit 0.
- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-product-full`
  — **548 passed, 1 skipped**, 8.42 s, exit 0.

Evidence for this navigation increment is preserved separately in
`verification_navigation_20261028/`; earlier product and label evidence is retained.
The skip remains Windows directory-symlink privileges. No live request, download,
new dependency, paid review service, commit or push was used for this increment.
Independent Argon batch review and human desktop inspection remain pending.
Next task: investigate 55 Cancri e before modifying NASA resolution/query behavior.

## Step 3 — 55 Cancri e evidence and search explanation

Anonymous public captures under `data/NASA/2026-10-28/cancri-investigation/` establish:

- Both 55 Cancri e and 55 Cnc e uniquely resolve to canonical 55 Cnc e through
  the existing strict resolver, without relaxing host/planet identity checks.
- The existing spectra query returns 23 valid metadata records, four Transmission
  and 19 Eclipse. The 50-record cap is not reached. The existing parser accepts
  all 23 and the browser correctly offers only the four Transmission records.
- A direct exact-name spectroscopy query using 55 Cancri e returns zero records.
  The current browser already resolves the name before querying; this alternate
  query is evidence of table naming semantics, not a reproduced application bug.
- One compact-name alias request timed out. No conclusion about that spelling's
  validity follows. A restricted-network DNS failure is also preserved.

The actual current ECAS window/Qt client successfully searched 55 Cancri e and
offered four records. Its raw metadata hash matches the original capture:
`407a7b9afdcd7097b2ad7f0a0e626b6fe72961cf1e0fb38415d09f455fb37a21`.
`verification_cancri_20261028/live-search.json` records UTC times, status and counts.
This was an offscreen metadata-only check, not a product-download, scientific or
normal-desktop acceptance check. No paid service or real credential was used.

The earlier user's zero-result report is **not reproduced**, and its historical
cause remains unknown without the exact input/build/error context. The issue page
could not be fetched through the web tool; the supplied feedback document remains
the issue description used here. Do not claim the original report is disproven
or that a name-resolution defect was fixed. Eclipse loading remains unsupported;
there is no evidence that FITS caused this discrepancy.

`ecas/ui/nasa_browser.py` now reports supported transmission count, total returned
count, and excluded types/counts. For this capture: four loadable out of 23;
Eclipse (19) excluded. Empty-inventory, no-supported-record and truncation states
retain their existing explanations. No alias/query/metadata/cache policy changed.

Four captured-response regression cases cover both spellings in the parser and
actual browser controls, assert the canonical query, four selectable Transmission
records, preserved evidence and explicit excluded counts. No product is downloaded.

Executed isolated driver commands:

- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py aliases-focused`
  — **102 passed**, 2.25 s, exit 0.
- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py aliases-full`
  — **552 passed, 1 skipped**, 7.69 s, exit 0.

Logs/runtime metadata and source fingerprints: `verification_cancri_20261028/`.
The skip remains Windows directory-symlink privileges. New feedback increments
remain local for later Argon review; no commit/push. Next: investigate additional
useful molecular products and add mappings only after verifying their protocols,
units, conditions and provenance. Earlier step counts describe their own snapshots.

## Step 4 — Additional verified reference products

The existing provider supports two additional useful mappings; no provider switch
or external package is needed. Verified public service pages identify:

| Formula | Isotopologue | Dataset | Wavenumber bounds (cm^-1) | Temperature (K) |
| --- | --- | --- | --- | --- |
| CO2 | 12C-16O2 | UCL-4000 | 0–20000 | 100–4000 |
| H2O | 1H2-16O | POKAZATEL | 0–41200 | 100–5000 |
| CH4 | 12C-1H4 | MM | 0–12000 | 100–2000 |

All supported products remain calculated absorption cross sections, zero pressure,
Doppler-only, wavenumber cm^-1 and signal cm^2/molecule. Application requests still
require whole-number temperature/bounds and an exact inclusive grid of 2–10000
points with positive spacing of at most six decimals. These bounds come from the
specific provider forms; successful small samples do not empirically validate all
settings or establish atmospheric suitability. Default reference settings remain
500 K, 4000–4010 cm^-1, spacing 1 cm^-1, not inferred planetary conditions.

`exomol_product.py` now contains an immutable service registry. A mapping binds
formula/isotope/dataset, fixed endpoint, exact dataset-description phrase, reported
limits and citations. The form parser checks each mapping's description, units,
zero-pressure/Doppler conditions, limits, POST action and fields before submission.
The client also checks that catalogue selection and request identity agree, uses
the matching Referer, and accepts only the exact same-origin result URL. Deadline,
size bounds, fresh anonymous CSRF handling and cancellation/reentrancy remain.

Request/cache identity includes isotopologue. Missing identity on original v1 CO2
records defaults only to the original CO2 service; legacy two-citation support
also applies only to CO2. The new reader preserves historical records without
rewriting them. Selected catalogue context is bound to the request's identity,
and saved provenance is checked against the service-specific request. New records
are not promised readable by older builds lacking the new request field/mappings.

Molecular References enables Download only for the exact supported records.
Details show selected-service limits. Shared controls cover the supported union;
invalid settings for a particular service fail before network activity, preserving
the previous reference. Selection changes do not silently clamp temperature/range.
Cache choices and displayed reference labels now use the actual formula/dataset,
including spacing in cache labels. Unsupported isotopes/datasets remain explicit.

Approved anonymous form/POST/product captures succeeded for water and methane:
11 points each, 500 K, 4000–4010 cm^-1, spacing 1 cm^-1. Original product/result
bytes, transformed form fixtures and provenance are in
`data/ExoMol/2026-10-28/additional-products/`. Form tokens were replaced by synthetic
text before publishing; no account, email or reusable cookie/token is retained.
Attribution includes the shared method/ExoMol papers and the specific POKAZATEL
(Polyansky et al. 2018) or MM (Yurchenko et al. 2024) paper. The methane page's
inline year says 2023 while its full bibliography says 2024; the original page is
preserved and citation metadata uses the full reference, without rewriting it.

Actual ECAS window/Qt retrieval and offline reopening passed separately for each
mapping. The existing observation stayed identical; reopened values equalled the
downloaded product; neither ExoMol client was created offline. Source hashes match
the separate original captures. Evidence: `verification_additional_20261028/`.
These are offscreen protocol/workflow checks, not desktop or scientific acceptance.

Eight added cases cover captured per-service forms/results/grids/hashes, actual Qt
client request URLs and cookie/Referer policy using fake replies, cache/provenance
identity binding, unsupported datasets/mixed selections, changed provider limits,
per-service request bounds, legacy CO2 identity omission, UI failure preservation
and offline reopening without network clients. Final runs:

- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-product-focused`
  — **181 passed, 1 skipped**, 2.99 s, exit 0.
- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py reference-product-full`
  — **560 passed, 1 skipped**, 8.39 s, exit 0.

The skip remains Windows directory-symlink privileges. New code is local for the
later Argon batch review; no commit/push or paid reviewer was invoked. Human
desktop review remains open. Next: independent observation/reference selection,
separate inspection and compatibility explanations; production analysis remains
unimplemented and cross sections cannot be used as transit-depth predictions.
