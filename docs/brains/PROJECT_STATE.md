# ECAS - Project State Document

**Last Updated:** 2026-10-30
**Version:** 1.0 (Beta)

**Unified baseline and UI exploration checkpoint for Claude — 2026-10-30 (local checkpoint):**
Unified remote master commit 5a41fd7 (merging PR #8: laboratory identification library, FITS streaming, Identify UI panel) with verified Priorities 1–7 forward modeling, transit visualizer, and human-testing UI bug fixes (Issues 1–4). Full test suite: 707 passed, 21 skipped (opt-in network health tests), 0 failures, 0 warnings (pytest -W error). Created local checkpoint tag checkpoint-20261030-pre-claude-ui and local branch claude/ui-exploration for Claude to explore UI refinements without endangering master or project context. Captured Jupiter MIRI imaging findings in docs/research/JUPITER_MIRI_FITS_FINDINGS.md and authored comprehensive handoff in docs/HANDOFF_TO_CLAUDE.md. No push to GitHub.

**Brett feedback fixes — 2026-10-29 (local, uncommitted):**
Reproduced the blank Identify plot with the actual cached Rustamkulov WASP-39 b
NIRSpec PRISM transmission dataset. Laboratory eligibility correctly blocks
planetary transit depth, but the UI previously discarded the plotted input.
`identification_panel.py` now displays source measurements before fitting and on
blocked results, explains failures beside the graph, previews references in
separate quantity/unit tabs, imports several files directly, and displays checked
counts and per-input progress. Opening the panel snapshots the current input.
`comparison_browser.py` transfers checked transit snapshots and metadata into
strict cached-only atmospheric comparison without generating models implicitly.
Laboratory batches run independently; atmospheric generation remains one chosen
observation at a time. A real IR + signed UV two-input worker regression passes.

`tabular_formats.py` streams/scans FITS containers up to 8 GiB, seeking past
images/unrelated tables and decoding one unambiguous scalar spectral BINTABLE.
Decoded limits: 100,000 rows, 128 columns, 1,000,000 cells; scans limited to 128
HDUs and 128 header blocks per HDU. Scaling/null values and quoted units are
handled explicitly. Unsupported event/image/vector products receive extraction
diagnostics. Source hashing in `observations.py`/`main_window.py` also streams.
Project raw attachments retain their separate 16 MiB limit. Tests import two
84 MiB structural image containers containing unchanged NASA-derived spectral
rows using less than 8 MiB traced memory; these are format checks, not invented
spectral observations. Brett's `jupiter__9303301451N_evt.fits` was not present in
the inspected ECAS_BETA branches, original ECAS main, or local data/Downloads;
its actual content and compatibility remain unverified pending a resolvable file.

Verification: focused identification/comparison UI **23 passed**; agent FITS
checks **21 passed**. Full `QT_QPA_PLATFORM=offscreen` regression with warning
escalation: **706 passed, 22 skipped, 0 failed, 0 warnings** (41.56 s), using
`.venv/Scripts/python.exe -I -B -m pytest -W error -p no:cacheprovider
-o pythonpath=. -q -rs --tb=short --basetemp=.venv/checks/feedback-full`.
Final identification/FITS checks after the input-label refinement: **24 passed**
(4.86 s). Scoped `git diff --check` passed, excluding the pre-existing handoff edit.
Skips are 21 opt-in live network checks and unavailable directory-symlink creation.
Offscreen visual inspection confirms the Rustamkulov 207-point measured curve
remains visible. Actual atmospheric handoff/generation produces two H2O/without-H2O
candidates on 122 shared points; 85 short-wavelength points lack cached opacity.
Only H2O POKAZATEL 500 K is locally available; its temperature mismatch with the
1166 K preset and line-profile limitations remain. No full-band identification,
calibrated detection sigma, or verification of the unavailable Jupiter file is
claimed. Existing user changes to `docs/HANDOFF_TO_OPENAI.md` are untouched.

**Local laboratory identification implemented — 2026-10-29 (uncommitted):**
Added `ecas/identification/` (real-library discovery, AFFN JCAMP / explicit UV–Vis
CSV loading, v1 BVLS optical-depth mixture and same-weight refitted drop-one
statistic), `ecas/ui/identification_panel.py` (IR/UV–Vis checkboxes, explicit
dataset variants, stable colours, plots and compact results), `ecas/observations.py`
(project/record identities and duplicate-product handling), and
`ecas/identification_records.py` (batch export and snapshot reproduction).
Comparisons exposes the new panel on explicit entry; atmospheric comparison,
dimension guards and strict cached ExoMol behavior remain separate.

Imported the real library from pinned GitHub revision
`a84c9d3ccf5e5dd230716feb9e972b60e0c454d9`: 88 files checked against Git blob IDs.
All raw/prepared numerical files are unchanged. Corrected 22 UV–Vis manifest
paths and IR inventory documentation links. Discovery yields 40 datasets with
zero discovery issues (18 IR / 22 UV–Vis). Six UV–Vis CSV datasets contain negative
measurements, preserved unchanged. The PH3 repeated wavelength remains visible
but blocks interpolation pending an explicit reduction. Source experimental
metadata survives imports and project storage without changing empty-metadata
legacy integrity digests. Added SciPy 1.18.1 to project requirements/environment.

Verification: initial focused engine/library checks 10 passed; final cross-review
checks 11 passed after a disjoint-coverage regression. UI/import/integration
selection: 20 passed. Full headless regression with warning escalation:
**688 passed, 22 skipped, 0 failed, 0 warnings** (latest full run 29.88 s). Skips: 21 opt-in live
network checks and one unavailable directory-symlink check. Command:
`.venv/Scripts/python.exe -I -B -m pytest -W error -p no:cacheprovider
-o pythonpath=. -q -rs --tb=short --basetemp=.venv/checks/identification-release-check`
with `QT_QPA_PLATFORM=offscreen`. An earlier restricted run failed creating test
temporary folders; explicit workspace basetemp resolved that environment issue.
Old format-rejection tests now use genuinely unsupported `.bin` instead of the
newly supported `.txt`; their rejection/clearing assertions remain.

Both agents reviewed the integration. Corrected stale results after planet-filter
changes, unhashed snapshot identity collisions, and empty-domain noise calculation.
Final identity follow-up preserves an open spectrum's original project ID even
when the project selector changes; the 26 affected UI/window tests passed (5.84 s).
Solver/Python/NumPy versions are recorded in new analysis settings.
Offscreen application layout rendered and visually inspected with explicitly
loaded Windows Segoe UI font (the offscreen plugin initially exposed no system
fonts). This is not normal-desktop user acceptance or empirical identification
validation. Known limits: conditional uncalibrated scores, independent observations
only, exploratory signed cross-section mode, no cross-section/optical-depth mixing,
no direct planetary-depth fitting, unknown conditions and temperature mismatch
warnings, assumed continuous interpolation support and unmodelled instrument
response/reference uncertainty. Full methodology and source references:
`docs/architecture/LABORATORY_IDENTIFICATION.md`.

No commits/pushes. The pre-existing trailing blank-line change in
`docs/HANDOFF_TO_OPENAI.md` was preserved. Next meaningful acceptance: inspect the
workflow with an independently acquired compatible laboratory observation and
normal desktop UI; calibrated atmospheric inference and wider UI redesign remain
separate work.

**Consolidation of Priorities 1–7 and Transit & Orbit Visualizer published to GitHub — 2026-10-29 (`4b4d1c0`):** Completed consolidation of beta core with v1 visual capabilities following `10_29_26_ecas_beta_review_initial.md` and `ECAS_going_forward_considerations.md`. Implemented: (1) `audit_observation_bin_semantics()` in `ecas/comparison/inputs.py` disentangling FWHM from top-hat bin edges and passband integration separated from grid interpolation in `ecas/comparison/alignment.py`; (2) forward-model parameter bounds in `ecas/comparison/model_generator.py` and 11 benchmark tests in `tests/test_forward_model_physics.py` (analytic Rayleigh slope within 0.5%, $H \propto T/g$, VMR scaling, cloud floor, quadrature convergence); (3) `cached_only` ExoMol opacity mode as default, blocking non-overlapping species with specific wavenumber requirements, with transparent candidate badges `[Real ExoMol]` vs `[Synthetic Template]`; (4) reduced chi-square $\chi_\nu^2 = q / N$ in `ecas/comparison/residuals.py` and ill-conditioned covariance check $\kappa > 10^{12}$ in `ecas/comparison/eligibility.py`; (5) attestation conflict detection and structured provenance (`source_provided`, `user_attested`, `bin_derived`); (6) raw file disk verification vs signed snapshots in `reproduce_selected_comparison`; and (7) interactive `TransitVisualizerPage` in `ecas/ui/transit_view.py` with limb darkening, observer sky view, blackbody star coloring, scrubbing controls, and Comparisons preset linking. Suite: **672 passed, 21 skipped, 0 failed, 0 warnings** in 23.66s (`pytest -W error`).

**Post-review physics, data-accuracy & UI polish published to GitHub — 2026-10-29 (`5d55d08`):** Added 1D isothermal hydrostatic limb-transmission forward-model generator & leave-one-out multi-molecule sensitivity (`ecas/comparison/model_generator.py`), UV-Vis cross-section & emission-reference classification (`ecas/ingestion/tabular_formats.py`), top-hat passband bin integration, asymmetric uncertainty (>10%) bias guard (`ecas/comparison/inputs.py`), systematic baseline offset diagnostics (`ecas/comparison/residuals.py`), 1-click wavenumber/wavelength display toggles (`ecas/visualization/reference_plot.py`, `ecas/ui/molecular_browser.py`, `ecas/ui/comparison_browser.py`), metadata Quick Setup & `Generate, Auto-Align & Compare` workflow, opt-in `@pytest.mark.live_network` health checks (`tests/test_live_network_health.py`, `tests/test_physics_ux_and_attribution.py`), plot minimum height squish protection across `SpectraPlot`, `ReferencePlot`, and `ResidualPlot` with internal `QScrollArea`, clean 1-line `comparisonSummaryCard` with collapsible technical panel, and collapsible `Show information` toggles for observation and reference source metadata. Suite: 622 passed, 22 skipped in 16.29s (`pytest -W error`).

**Chunk 7 published for review — 2026-10-29 (`b3e3ad0`):** Stages 7.1–7.6 (`ecas/resources/catalog.py`, `ecas/ui/resources_browser.py`, `ecas/ingestion/tabular_formats.py`, `convert_wavenumber_to_microns` in `ecas/comparison/alignment.py`, `ecas/comparison/model_adapters.py`, `docs/Chunk_7/RESEARCH_AND_MODELING_FOUNDATION.md`, `docs/Chunk_7/IMPLEMENTATION_LOG.md`, and `tests/test_chunk7_resources_and_modeling.py`) were verified (`610 passed, 1 skipped`, exit 0) and pushed to `codex/roadmap-reconciliation-20261028`. Removed 0-byte `ecas/ui/main_window_temp.py`.

**Chunk 6 completed — 2026-10-28:** User confirmed Chunk 6 complete and authorized pending work instructions for Chunk 7. Stages 6.1—6.7 are fully implemented, verified, and published on GitHub (`codex/roadmap-reconciliation-20261028` at commit `9a8150d`). Full offscreen test suite: 603 passed, 1 skipped (14.41 s), exit 0. Raw cross sections remain strictly blocked against transit depth without an explicit radiative-transfer model; empirical validation and abundance retrieval remain deferred. Current position: Chunk 6 complete; ready for Chunk 7 (Integration and reliability).

**Latest workflow verification:** Live normal-window CO2 download and repeat both
updated the display without cached reopening; record count remained four on repeat.
New Comparisons plots, native units, metadata label and view/selection preservation
passed desktop checks at 1200 × 800. See
`docs/Chunk_5_1/verification_final_workflow_20261028/RESULTS.md`.
Historical display symptom remains non-reproduced, not a claimed causal fix.
Supported Chunk 5.1 implementation/review is in place; later human plot UX and
smaller-window acceptance remain open. Next bounded production work is defined in
`docs/Chunk_5_1/CHUNK_6_ENTRY_SCOPE.md`: eligibility integration, not quantitative
analysis or invented physical modelling. Latest suite still 576 passed/1 skipped.

**Review update — 2026-10-28:** User confirms batches 9–11 require no fixes per
Argon. Treat these increments as reviewed on that confirmation, without invented
JSON/file-scope details. See `docs/Chunk_5_1/review_plot_desktop_20261028/09-11-user-confirmation.md`.
Current roadmap position: late Chunk 5.1, reference integration and visual input
inspection implemented; acceptance reconciliation remains before declaring the
chunk closed. Chunk 6 scientific comparison is not implemented. Latest full
suite remains 576 passed, 1 skipped; no receipt-only test rerun.

**Native plot desktop correction (local):** Normal Windows inspection revealed
that automatic magnitude multipliers could be crowded on short reference plots.
Reference y-axis ticks now show explicit scientific notation with compact native
units. Molecular References has a manual Hide/Show request settings control to
give plots/tables more space without changing values. Cached CO2 plot/table was
visually checked at 1200 × 800; smaller sizes/new Comparisons desktop inspection
remain open. See `docs/Chunk_5_1/verification_plot_desktop_20261028/RESULTS.md`.
Final tests: 126 focused passes; 576 passed/1 skipped full. New review batch 11
is pending, alongside reports for batches 9/10. No publication or scientific claim.

**Issue #4 native plots (local):** Molecular References and both Comparisons panes
now offer Plot/Data table tabs, sharing inspection space. Reference samples plot
on original wavenumber/cross-section axes; observations retain imported units or
unknown labels. Axes remain independent and physical-model comparison blocking
remains. Catalogue results explicitly mark supported download versus unverified
retrieval. See `docs/Chunk_5_1/ISSUE_4_NATIVE_PLOTS.md`. New code is not published
or independently reviewed; normal-desktop plot acceptance remains pending.

**Issue #4 first fixes (local):** exact validated reference products/context are
reused on repeated saves; preexisting duplicates are grouped in choices without
deleting files. Distinct records carry hash/record suffixes. Comparison observation
choices now capture available saved/table publication and instrument descriptions
with filename fallbacks. Offline initial/repeated download completion redraws
successfully without manual reopening; the reported live symptom is not reproduced
and remains open. See `docs/Chunk_5_1/ISSUE_4_FIRST_FIXES.md` and its verification
folder. New work needs review/desktop confirmation; scientific validation deferred.

**Human desktop feedback received — issue #4, 2026-10-28:** User reviewed published
build `49e3b96`, confirmed core desktop workflows and authorized further development
with known follow-ups. See `docs/Chunk_5_1/ISSUE_4_DESKTOP_FEEDBACK_20261028.md`.
Confirmed code-level concerns: duplicate cache choices on repeated downloads and
filename-only comparison labels. Manual reopen reportedly needed after download
is not yet reproduced; the success callback already invokes display refresh.
Unsupported catalogue mappings remain a deliberate limitation. Native-unit plots
and an improved graphical inspection layout are requested future work; raw cross
sections remain incompatible with transit depth without a physical model.
Human review is received with follow-ups, not blanket checklist completion;
item 5 did not explicitly confirm CSV sync/restart behavior. Scientific validation
remains deferred. This receipt/triage is local documentation only.

**Authorized publication — 2026-10-28:** The user requested commit/push of the
reviewed feedback update for external review. See `docs/REVIEW_FEEDBACK_20261028.md`
for scope, evidence and remaining acceptance. Earlier local/uncommitted statements
below describe previous checkpoints; use actual Git state for current publication.
No merge/deployment or scientific-validation completion is authorized or claimed.

**Latest desktop follow-up — 2026-10-28:** Agent checked the normal Windows app
using original public captures and isolated projects/reference caches. Confirmed
331-row NASA import/plot, independent water/methane inspection, shared CSV choice
and restart reset. Fixed clipped comparison reference headings and made the exact
observation hash easier to inspect/copy. See
`docs/Chunk_5_1/verification_desktop_20261028/RESULTS.md`. Latest focused/full:
121 passed (5.54 s); 571 passed, 1 skipped (10.56 s), both exit 0. Batch 8 returned
zero findings for all four listed files, verified against its saved manifest before
receipt. See `docs/Chunk_5_1/review_desktop_20261028/08-disposition.md`. All eight
feedback review batches have zero findings within scope. No receipt-only test
rerun was needed. Human acceptance and unperformed desktop checks remain
open. Scientific validation remains deferred. No scientific input was fabricated.

**Latest workspace increment — 2026-10-28:** Following the user's acceptance of
Argon's six reviews and authorization to continue, Overview now provides workflow
shortcuts and page-entry summaries of loaded state. Settings shows configured
read-only data paths and mirrors the existing session CSV-schema choice. See
`docs/Chunk_5_1/WORKSPACE_PAGES_IMPLEMENTATION.md`. No production comparison or
new persistent preferences. Batch 7 returned zero findings for its four listed
files; all manifested files and the prompt matched before receipt. See
`docs/Chunk_5_1/review_workspace_20261028/07-disposition.md`. All seven feedback
batches have zero findings in their stated scopes. Latest full suite: **571 passed,
1 skipped**, 11.15 s; focused: 121 passed, 5.82 s; both exit 0. No receipt-only
test rerun. Remaining items/checklist are reconciled in
`docs/Chunk_5_1/ACCEPTANCE_STATUS_20261028.md`. Normal-desktop acceptance remains
open and scientific validation deferred; no chunk completion is claimed.
Older continuation and checkpoint paragraphs below retain historical states.

**Latest continuation — 2026-10-28:** All five user-supplied Argon feedback batches
have zero findings; their manifested source hashes matched before continuation.
Scopes, limitations and the Batch 3 causal-wording correction are recorded in
`docs/Chunk_5_1/review_feedback_20261028/RECEIVED_REPORTS.md`.
Comparisons now supports independent session observation snapshots and validated
cached-reference choices, separate tables and explicit blocked comparison reasons.
No production eligibility engine or scientific analysis is enabled. See
`docs/Chunk_5_1/COMPARISON_SELECTION_IMPLEMENTATION.md`. Batch 6 has since returned
zero findings for the selection snapshot; all seven files and its prompt matched
the review manifest before receipt. See
`docs/Chunk_5_1/review_selection_20261028/06-disposition.md`.
All six batches have zero reported findings. Desktop acceptance remains open;
next approved implementation work is Overview/Settings content.
Latest suite: **566 passed, 1 skipped**, 8.03 s, exit 0; focused: 116 passed, 3.97 s.
The checkpoint paragraphs below retain earlier implementation/review states.
Real-data scientific validation remains deferred; all changes remain local.

**Local user-feedback increments:** Approved workflow and steps 1–4 progress:
`docs/Chunk_5_1/USER_FEEDBACK_WORKFLOW_20261028.md`. Projects now shows saved
planet/publication/instrument labels with filename fallbacks and separately
attributed metadata in tooltips. No saved data/schema changes. Latest local suite:
560 passed, 1 skipped (8.39 s), exit 0. Molecular References now has its own page;
Comparisons is a separate explanatory placeholder. Navigation retains observations,
reference selections and active requests. New work awaits review/desktop acceptance;
it is not included in the published checkpoint below. 55 Cancri e resolves to
55 Cnc e and returns four Transmission plus 19 Eclipse records in captured and
actual-window live checks. The earlier zero-result report was not reproduced;
its historical cause remains unknown. Search now explains returned/excluded
counts; alias/query behavior is unchanged. Verified retrieval now also supports
H2O / 1H2-16O / POKAZATEL and CH4 / 12C-1H4 / MM, with distinct limits/citations
and identity-bound caches. Actual-window download/offline reopen passed for each
small sample; original CO2 caches remain readable. Other mappings remain unsupported.
Next: independent observation/reference selection and compatibility explanations.

**Published review checkpoint:** `docs/REVIEW_CHECKPOINT_20261028.md` describes the
publication snapshot and local recovery bundle at `98abaec`. Its full verification:
538 passed, 1 skipped; new Chunk 5.1 work still needs review.

**Earlier recovery checkpoint:** `docs/Chunk_4/HANDOFF_CHECKPOINT_20261028.md` describes
the reviewed baseline. Local ignored `.checkpoints/reviewed-20261028.zip` contains
199 hash-verified files with a sibling manifest; it precedes Chunk 5 investigation.
It is a file snapshot, not a commit or backup of private project databases.

**Current phase: Chunk 5.1.** User confirmed independent review complete and
authorized continuation on 2026-10-28. Existing Chunk 5 design/prototype checkpoint
is recorded reviewed on that confirmation, without invented report details.
Provider comparison and initial ExoMol two-column zero-pressure cross-section parser
are in `docs/Chunk_5_1/PROVIDER_INVESTIGATION.md`. Catalogue parsing and offline
name/formula/isotope/dataset search use an anonymous 189391-byte public capture.
Molecular References hosts catalogue search, explicit refresh/cancel and atomic cache.
Bounded CO2 / 12C-16O2 / UCL-4000 product retrieval, separate reference table,
provenance cache and offline reopening are now implemented. Actual Qt download
and offline reopening passed an approved live check: 11 calculated points, 500 K,
4000–4010 cm^-1, zero pressure, Doppler-only. Other catalogue entries remain
unsupported for retrieval except the water/methane additions described above. See
`docs/Chunk_5_1/USER_FEEDBACK_WORKFLOW_20261028.md` for current product support;
`PRODUCT_RETRIEVAL_IMPLEMENTATION.md` records the earlier CO2-only checkpoint.
New parser/catalogue/UI/cache/network work awaits independent review and fresh
desktop visual acceptance; earlier confirmation is not extended to later screens.
Explicit observation/reference pairing and production comparison remain pending.
Real-data scientific validation stays deferred; successful retrieval establishes
workflow behavior, not atmospheric validity or molecular presence.

**Chunk 5 foundation:** Source audit, draft comparison-input requirements and
same-grid and response/uncertainty experiments are implemented outside application code.
See `docs/Chunk_5/COMPARISON_INPUT_CONTRACT_DRAFT.md` and `IMPLEMENTATION_LOG.md` in
that folder. A limited initial method is now documented in
`docs/Chunk_5/INITIAL_METHOD_DECISION.md`: compatible-observable overlay plus explicit
response handling and residual inspection; weighted diagnostics only with established
error/covariance conventions. No production comparison integration; initial ExoMol
reference access is separate and described above.
Noise/continuum mismatch and off-grid behavior have synthetic evidence. User's
independent-review completion includes the existing research import adapter
(`docs/Chunk_5/IMPORT_ELIGIBILITY_ADAPTER.md`). It
preserves imported values/unknowns and explicitly records metadata label mappings;
no existing application path has been switched to the contract.
The source-reviewed prototype is documented in `docs/Chunk_5/ELIGIBILITY_CONTRACT_V1.md`. It is
outside the application and does not change existing import, storage or UI behavior.
Research-only fitted templates and separate calibration/holdout null trials are now
implemented; see `docs/Chunk_5/MODEL_COMPARISON_PROTOTYPE.md`. Physical modelling
itself remains unimplemented; empirical validation and general provider/product
support remain open, following the bounded ExoMol implementation above.
Analytic binning/LSF, asymmetric-error and fixed-covariance examples are recorded in
`docs/Chunk_5/RESPONSE_AND_UNCERTAINTY_EXPERIMENT.md`. This increment awaits independent
review at that earlier checkpoint; user subsequently confirmed completion. User confirmed manual
review complete on 2026-10-28; the manual acceptance gate is recorded complete on
that confirmation, without inventing per-test desktop results. User explicitly
deferred real-data validation; it is not an immediate gate to
this research, and no empirical validity is claimed.

**Chunk 5 review:** Argon Batch 1 response/uncertainty and Batch 2 fitted-template
reviews returned zero findings for their supplied snapshots. Batch 3 contract/claims
review also returned zero findings. All three research batch reviews are complete
for their supplied snapshots. Subsequent foundation review completion is recorded on user confirmation;
real-data validation remains deferred. Review scope does not include app/NASA/SQLite
integration validation.
Covariance estimation is not implemented.
Eligibility source-only review also returned zero findings; exact grid equality
remains deliberate v1 policy. That review did not include the tests or the later
robustness/method-decision work; the later user review-completion confirmation is recorded above.
Synthetic response and fixed noise examples are not empirical instrument/noise validation. No code corrections
or test reruns were needed for those receipts; no production comparison is accepted.

**Current reconciliation baseline:** GitHub master `2de79c7` merged PR #1 after
integration commit `6c90ce5`. The local work branch is
`codex/roadmap-reconciliation-20261028`, based on that merged master. Integration
is no longer outstanding. Inspection plus an in-memory method diagnostic found
CSV GUI dispatch referencing an unimported `import_spectrum_csv` symbol at that merge.
The CSV route is now repaired locally through the import manager, preserving NASA
.tbl import. Fresh verification: 289 passed/1 skipped after this repair, then
341 passed/1 skipped after project attachment, integrity and link/layout work (5.50 s),
then 345 passed/1 skipped after Argon batch 1 storage corrections (5.74 s).
Reviewed application baseline: 357 passed/1 skipped after batch 4 (6.24 s).
Latest with Chunk 5.1 product retrieval/cache/UI tests: 538 passed/1 skipped (7.20 s),
exit 0. Logs and exact commands: docs/Chunk_5_1/verification_product_20261028/.
All four original Argon batches are triaged. Batch 4's P1/P2 entries explicitly
describe non-defects; the P3 fallback is fixed in both import entry points.
See docs/Chunk_4/review_20261028/04-aliases-csv-disposition.md.
Argon batch 3 found no functional links/layout defect; optional removal of
click-time URL validation was declined. See review_20261028/03-links-layout-disposition.md
under docs/Chunk_4. Argon Batch 1, Batch 2 and Batch 4 correction re-reviews returned
no findings and are complete for their supplied snapshots. All four original
batches and necessary correction reviews are recorded; no confirmed review defects
remain unresolved. User-confirmed manual review is now complete. These re-review
receipts required no code changes or test reruns.
Missing-record and unplottable-project feedback are fixed. Absolute-link validation
and importer file-error wrapping were verified; their reported defects were not
present. Triage: `docs/Chunk_4/review_20261028/02-project-interface-disposition.md`.
Read snapshots, portable v1 hash verification and selective index loading are fixed;
the documented injected-connection commit contract is retained. See
`docs/Chunk_4/review_20261028/01-project-storage-disposition.md` for triage and follow-up.
User authorized checkpoint, commit and push for GitHub review on 2026-10-28.
The publication uses the current review branch; no merge into master is authorized.
The 281/1-skipped records below apply to `7a4061a`, not to the merged revision.

**Name resolution:** NASA alias lookup now precedes spectral metadata search.
The actual offscreen application resolved WASP39b to WASP-39 b (28 transmission
records), TRAPPIST-1e to TRAPPIST-1 e (6), Kepler-452b to Kepler-452 b (empty
queried inventory), and Proxima Centauri b to Proxima Cen b (empty queried
inventory). Unknown, ambiguous and inconsistent identities are errors. Captures
are under data/NASA/2026-10-28. This does not implement FITS support.

Human-review feedback has been received: exact-name/zero-result search behavior,
missing project attachment UI, relative NASA source links and minor layout issues.
Disposition and acceptance tasks are in the development plan's Chunk 4 section.
Manual acceptance is recorded complete on user confirmation; targeted Argon correction reviews are complete.
Projects now supports create/select, attach displayed/cached spectra and reopen
saved records with source bytes/provenance, even after original/cache removal.
Legacy rows remain readable without fabricated provenance. Database tables are
unchanged; new records optionally extend their JSON with a versioned attachment.
Integrity checks and source limits are covered by tests; no hostile-storage or
scientific-authenticity guarantee is implied. Comparisons now hosts the bounded
molecular reference browser described above.
NASA-relative links are expanded only for display and opened by explicit action.
Buttons/search-result spacing received the requested limited layout pass; normal
offscreen typography could not be verified because screenshots lacked glyphs.
The later user manual-review confirmation is recorded above; no screenshot results are invented.
A limited initial diagnostic method is documented and its earlier review completion
is recorded above. ExoMol reference access is implemented within the stated limits;
no atmospheric engine or production comparison is implemented.

**Historical checkpoint records follow:** their counts, integration notes and
acceptance statements describe their own revisions/dates.

**Latest local verification:** 281 passed, 1 skipped on 2026-10-27. See
`../Chunk_4/Chunk_4_implementation_log.md` for the latest online NASA/cache increment.
Earlier counts are historical reports. Independent Argon review remains pending.

**Interactive review follow-up:** all three batch reports have been received.
Batch 1's target-casing fix and batch 2's parser/URL fixes are implemented. Batch 3
claims were not substantiated by inspection and five added offscreen regression
cases, including queued Qt failures and cached loading under either CSV schema.
The network follow-up then reproduced and fixed completion reentrancy that could
prematurely complete a chained request. Reply-specific signal handling and an
explicit exclusive-use manager contract are now tested. The full suite passes
281/1 skipped. Triage is preserved in the Chunk 4 log and parent
argon_review_20261027/*-triage.md. Targeted independent re-review of revised code
and human interactive acceptance remain pending.

**Review update (2026-10-27):** the user-authorized Antigravity diagnostic passed,
but the first actual ECAS review batch timed out empty after five minutes and was
rejected as incomplete. Remaining batches were not launched. See the Chunk 4 log
and parent `argon_review_20261027/RUNNER.md`; there is no Argon approval of ECAS yet.

**Current Chunk 4 capability:** exact-name NASA spectral search, asynchronous
anonymous download of supported transmission tables, validated local cache
registration and offline reopening are connected to Spectral Data. The actual
offscreen application retrieved the 331-row WASP-39 b example and reopened it
without further requests. Cache manifests preserve raw metadata/table hashes and
source URLs; they do not extend project SQLite serialization. Human interactive
review, general format support, other providers and scientific validation remain
open. Earlier dated entries below describe the state at their own checkpoints.

---

## Repository Structure

```
ECAS_BETA/
├── ecas/
│   ├── __init__.py
│   ├── models/
│   │   ├── spectrum.py         # SpectrumData model (frozen dataclass)
│   │   └── __init__.py
│   ├── persistence.py          # SQLite storage layer (COMPLETE)
│   ├── visualization/           # Spectral visualization component
│   │   └── spectra_plot.py      # PyQtGraph spectrum plot widget
│   └── ...
├── docs/
│   └── brains/
│       ├── DECISIONS.md        # Design decisions
│       └── PROJECT_STATE.md    # This file
├── tests/                      # Test directory (complete test coverage for persistence and visualization)
│   ├── test_persistence.py     # Persistence tests (20 passing tests)
│   └── test_spectra_plot.py    # Visualization tests (8 passing tests)
├── README.md
└── ...
```
---

### CSV Import Manager and GUI Integration
10-27-2026
**Status: Implemented and verified by automated tests; manual GUI verification partially completed.**

- Added `ecas/ingestion/import_manager.py` as a format-selection entry point for spectrum imports.
- The import manager currently supports CSV files and delegates CSV parsing and validation to `ecas/ingestion/csv_importer.py`.
- Unsupported extensions, including files without an extension, are rejected with a clear `SpectrumImportError`.
- Updated `ecas/ui/main_window.py` to route CSV imports through the import manager while preserving the existing generic and WASP-39 b archive schema selection.
- Added `tests/test_import_manager.py` covering unsupported formats, extensionless files, generic CSV imports, and forwarding of the WASP-39 b archive schema.

**Automated verification:** The full test suite passed: `150 passed in 3.25s`.

**Manual GUI verification:**
- The WASP-39 b archive CSV imported successfully when `WASP-39 b Archive` was selected.
- The GUI displayed all 331 rows and plotted `centralwavelng` on the X-axis and `pl_trandep` on the Y-axis.
- `wasp39b_test.csv` also imported successfully using the archive schema.
- Other CSV files may fail if they do not match the selected import schema or contain recognizable generic measurement columns.

**Current limitations:**
- The archive importer requires its expected 21-column source schema.
- Generic CSV imports still require recognizable wavelength and signal columns; arbitrary column mapping is not implemented.
- Text-based spectrum imports are not implemented.
- Successful import of the tested archive dataset does not establish compatibility with all archive CSV variants.

**Deferred work:** Plan and implement user-selectable X/Y column mapping for generic CSV imports. Consider text-based import support in a separate, later increment.

---

## Component Status

### ✅ persistence.py - COMPLETE (Chunk 2)

**Functions Implemented:**
| Function | Description | Status |
|----------|-------------|--------|
| `validate_project_id()` | Sanitizes project ID, prevents path traversal | ✅ |
| `get_project_database()` | Gets path to project's SQLite DB | ✅ |
| `_get_connection()` | Opens/creates SQLite connection | ✅ |
| `_initialize_schema()` | Creates spectra table if needed | ✅ |
| `_to_spectrums_dict()` | Deserializes dict back to SpectrumData | ✅ |
| `save_spectrum_to_database()` | Saves spectrum to project DB | ✅ |
| `load_spectra_from_database()` | Loads all spectra for project | ✅ |
| `load_spectrum_by_index()` | Loads specific spectrum by index | ✅ |
| `clear_project_database()` | Empties project's spectra table | ✅ |
| `count_spectra()` | Counts spectra in project DB | ✅ |

**Storage Format:**
- Each spectrum stored as JSON in TEXT column (via SQLite BLOB/TEXT)
- JSON structure:
  ```json
  {
    "source_file": "/path/to/file",
    "rows": [[1.2, 2.3], [3.4, 4.5]],
    "columns": ["frequency", "intensity"],
    "axis_unit": "Hz",
    "signal_unit": "arbitrary units",
    "signal_type": "NMR",
    "warnings": []
  }
  }
  ```

### ✅ models/spectrum.py - COMPLETE (Chunk 1)

**Class:** `SpectrumData`  
**Attributes:**
- `source_file`: Path to original spectrum file
- `rows`: Tuple of tuples (spectral data matrix, frozen at creation)
- `columns`: Tuple of column names
- `axis_unit`: X-axis unit (e.g., "Hz", may be None)
- `signal_unit`: Y-axis unit (e.g., "arbitrary units", may be None)
- `signal_type`: Signal type (e.g., "NMR", may be None)
- `warnings`: Empty tuple or tuple of warning messages from import

### ✅ visualization/spectra_plot.py - COMPLETE (Chunk 3)

**Location:** `ecas/visualization/spectra_plot.py`

**Role:**
- Receives normalized `SpectrumData`.
- Uses PyQtGraph to display spectral coordinates.
- Is intended to replace the previous plotted dataset when a new one loads.

**Verification results:**
- Automated tests: All plotting tests passed (`tests/test_spectra_plot.py`).
- Full application test suite: **40/40 passing**.
- Manual verification: Application launched successfully; `test_spectrum` imported and displayed with correct plotting.

Current limitation: The generic CSV importer and the explicitly supported WASP-39b archive schema cover the currently implemented CSV paths. Other custom-formatted CSV schemas and research files in TXT or other formats are not necessarily supported. Broader import flexibility and unit selection remain future work. 10-23-2026

**Future work (unchanged):** 
- Additional archive ingestion and online reference-spectrum retrieval (Chunk 4; remaining scope) (10-23-26)
- Spectrum comparison workflow and scientific analysis features (Chunks 5-7)

### ✅ models/spectrum.py - COMPLETE (Chunk 1)

---

### ✅ ingestion/csv_importer.py — ARCHIVE CSV SUPPORT IMPLEMENTED (Chunk 4, current scope)

**Location:** `ecas/ingestion/csv_importer.py`

**Implemented capability:**
- Supports the explicitly configured WASP-39b archive CSV schema.
- Maps `centralwavelng` to canonical `wavelength`.
- Maps `pl_trandep` to canonical `signal`.
- Retains the original source columns and appends the two canonical columns.
- Preserves existing generic CSV import behavior when no archive schema is supplied.
- Rejects unsupported explicitly supplied archive schemas rather than silently using the generic importer.

**Real-data verification:**
- Source: `data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`
- Imported rows: 331
- Imported columns: 23 (21 source columns plus 2 canonical columns)

**Automated verification reported:**
- Archive importer tests: 105 passed.
- Full test suite: 145 passed.

These results reflect the reported test run for the current implementation. Rerun tests after subsequent code changes.

**Scope limitation:** This is support for one identified archive schema, not universal archive CSV compatibility. General online archive retrieval, additional archive schemas, TXT import, and broader unit-handling behavior are not established by this implementation.

---


## Known Issues / TODOs

### Persistence (Chunk 2):
- Comprehensive change-history/provenance tracking remains a future design decision.

### Visualization (Chunk 3) - Completed
- ✅ All automated plotting tests passed.
- ✅ Application launched and `test_spectrum` imported/plotting verified manually.
- ⏳ Dataset-selection behavior deferred per project plan; not implemented in current codebase.

### Testing:
- Full test suite: **40/40 passing** (user-reported result as of 2026-10-22).
---

## Testing Summary

**Latest reported full test suite:** 145 passed.

- Archive CSV importer: 105 tests passed (`tests/test_archive_csv_importer.py`).
- The full suite includes the existing persistence and visualization tests, as well as the new archive importer tests.

**Test Environment:**
- Python interpreter: Python 3.14.0
- Pytest version: pytest-9.1.1

These results describe the reported run and should be refreshed after subsequent code changes.

(10-23-2026)

---

## Next Steps

1. Complete and verify the persistence layer (Chunk 2) — **done**.
2. Complete the plotting component and integrate it into the main window (Chunk 3) — **verified and complete**.
3. Run targeted and full automated tests — **passed (40/40)**.
4. Continue to later chunks only after the current completion criteria are met.

Future work includes:
- Dataset-selection behavior for multiple saved spectra (deferred).
- Online reference-spectrum retrieval from archives (Chunk 4).
- Spectrum comparison workflow and scientific analysis features (Chunks 5-7).

---

## Verification Note

**Automated vs. Manual Verification:**
- Automated tests verify core functionality independently of the GUI.
- Manual verification requires running ECAS and inspecting the plot widget in action; this is separate from automated test results and will be documented once performed.

## Local regression preparation — 2026-10-27

Status: PARTIAL; runtime verification awaits approved dependency downloads.
Baseline: clean master at 6da2dccfe966b9b75dc118aba3d55e606319b579.
The QComboBox import and archive_schema keyword repairs are already present;
no application/scientific behavior was changed in this increment.

- tests/test_main_window.py: added six regression cases for selector labels/default,
  generic/archive schema forwarding through both import routes, and cancellation
  preserving the existing display. Importer mocks use the actual signature.
- test_spectra_schema.py: replaced import-time QApplication creation, hard-coded
  developer paths and print-only success claims with two portable parameterized
  assertions over explicitly synthetic coordinates. Both archive source columns
  and normalized canonical columns must plot unchanged coordinates; missing units
  remain unknown. Existing archive importer tests cover CSV ingestion separately.
- Syntax compilation of both changed modules via Python 3.14.5 with -I -S -B:
  PASS. git diff --check: PASS (line-ending notice only).
- Attempted: python -I -B -m pytest -p no:cacheprovider
  tests/test_main_window.py test_spectra_schema.py -q.
  BLOCKED: No module named pytest. Installed-module discovery also found PySide6
  and pyqtgraph absent. No runtime test pass or manual GUI verification is claimed.
- No downloads, credential use, paid API calls, Argon/other agent launches, commits
  or pushes. Changes remain uncommitted. Independent Argon review is outstanding.

Next: obtain user approval to download the required test/GUI packages into a
project-local environment, run the focused tests and relevant full regression,
then review the final changes. Do not run downloads implicitly. Historical test
counts elsewhere in this document remain reports, not results of this increment.

## Approved local dependency installation and regression verification — 2026-10-27

The user explicitly authorized the required downloads. This continuation resolves
the missing-dependency blocker recorded above. The scoped regression increment is
implemented and locally tested; independent Argon review and delivery are pending.
No application code, scientific interpretation, data values or units were changed.

### Environment and installation

- Project-local `.venv`, already excluded by `.gitignore`; no global packages changed.
- Python 3.14.5 (64-bit AMD64), pytest 9.2.0, PySide6 6.12.0,
  pyqtgraph 0.14.0 and numpy 2.5.4. Transitive package versions and download hashes
  are recorded locally in `.venv/checks/install-report.json`.
- Created using the existing Python executable with `-I -B -m venv .venv`.
  Restricted initialization first failed in ensurepip; the same approved setup
  then succeeded with the execution tool's additional system-access permission.
- Installed using `.venv/Scripts/python.exe -I -B -m pip --isolated
  --disable-pip-version-check --no-input --keyring-provider disabled install
  --index-url https://pypi.org/simple --only-binary=:all: --no-cache-dir
  --report .venv/checks/install-report.json pytest PySide6 pyqtgraph`.
- Dependency installation and test subprocesses received an explicit minimal
  environment, without inherited credentials. Qt ran offscreen; test temp/profile
  paths were inside `.venv/checks`. Plugin auto-loading and pytest cache writes
  were disabled. The initial focused invocation omitted PATH, causing two PySide6
  collection errors; supplying only the local Scripts and Windows System32 paths
  fixed this test-environment issue without an application change.

### Additional regression repair

The first full run reported 152 passed, 1 failed, 1 skipped. The failure was the
existing `tests/test_csv_manual_import.py` expectation that `centralwavelng` was
removed. That contradicted both the importer and the documented provenance rule.
The repaired test requires all 21 source columns in their relative source order,
both canonical aliases, two complete rows and exact alias/source value equality.
It does not change the importer's current output order. The existing real-data
archive test continues to verify that full output order and the 331-row fixture.

### Actual verification

All pytest commands used the local interpreter with `-I -B -m pytest`,
`-p no:cacheprovider -o pythonpath=.`, a fresh project-local `--basetemp`,
`QT_QPA_PLATFORM=offscreen` and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.

| Selection | Result | Exit |
|---|---|---|
| `tests/test_main_window.py test_spectra_schema.py -q` | 10 passed, 3.09 s | 0 |
| Initial full discovery (`-q`) | 152 passed, 1 failed, 1 skipped, 1.42 s | 1 |
| `tests/test_csv_manual_import.py -q` after assertion repair | 1 passed, 0.15 s | 0 |
| Final full discovery (`-q`) | 153 passed, 1 skipped, 1.26 s | 0 |

The skip is `TestProjectIdValidation.test_rejects_symlink_that_escapes_projects_directory`:
directory symlink creation is unavailable. This is not a verified access-denial
result. Manual interactive GUI verification and independent Argon review were not
performed. Software tests do not establish scientific validity.

Exact command arrays, exit codes, environment key names, logs and JUnit XML are
retained locally in `.venv/checks/` (`focused-fixedenv`, `full`, `archive-corrected`,
`full-final` artifacts). The local runner simply sanitizes the environment and
executes those pytest selections; it does not launch an AI service.

### Review and continuity

- Changes: `tests/test_main_window.py`, `test_spectra_schema.py`,
  `tests/test_csv_manual_import.py`, and this record. All remain uncommitted;
  no staging, pushes, real credential use, paid APIs or additional agents.
- Existing archive column-order discrepancy remains: the decision record/docstring
  describes appending both canonical aliases after the original source fields;
  current code and its real-data test put `wavelength` first and `signal` last.
  This increment preserves that current behavior. Reconcile the intended public
  ordering before changing it; the provenance requirement itself is satisfied by
  retaining the original source columns and values.
- Next: review the exact final changes with Argon through an explicitly approved
  route compatible with the user's no-additional-billing/no-real-credential rules,
  or obtain its review manually. Do not claim independent review from these local
  results or enable the custom agent launcher to obtain it implicitly.

## Launch and bundled archive import investigation — 2026-10-27

Reported problem: main.py did not launch on the friend's machine, and manually
importing the bundled archive file failed; incomplete database integration was
suspected. The attached screenshot is historical context, not a fresh failure.

### Verified findings

- Current main.py and app.py both construct and show the ECAS window and enter
  the Qt event loop in the installed project environment. New subprocess smoke
  tests run each real entry point offscreen from another working directory and
  instrument only event-loop exit with a timer. This is automated startup
  verification, not an interactive desktop/double-click test on the friend's host.
  The original launch failure is not reproduced; its traceback/environment remain
  unknown. No unsupported causal fix to main.py is claimed.
- Real local-file imports through both the file-dialog route and path helper
  display all 331 rows and 23 columns when WASP-39 b Archive is selected.
  Generic mode rejects the file. Neither route uses database retrieval. The
  existing archive importer already handles the bundled uppercase source headers.
- The schema selector was below the plot/table, making it easy to miss before
  importing. It is now above Import CSV, with an explicit explanation for the
  bundled example and the absence of any database requirement. Generic remains
  the default; no schema guessing or scientific interpretation was introduced.

### Changes and verification

- ecas/ui/main_window.py: moved schema controls before import and clarified help.
- tests/test_main_window.py: real bundled-file integration tests for both import
  routes, a generic-mode rejection test, and selector-before-button verification.
- tests/test_entry_points.py: two bounded offscreen entry-point smoke tests.
- requirements.txt / requirements-test.txt: recorded the versions already
  installed and verified in this local environment; no additional package types
  or new downloads were needed for this increment.
- README.md: concrete environment/launch/test commands and the exact example-file
  import steps. No activation script or database setup is required to import it.
- Before UI/doc changes, local focused startup/import tests: 13 passed in 2.26 s,
  exit 0. Final full suite: 158 passed, 1 skipped in 2.82 s, exit 0.
  The same directory-symlink-privilege skip remains unverified.
- Executed via .venv/Scripts/python.exe -I -B .venv/checks/run_checks.py
  launch-import-baseline and launch-import-final, respectively. The local driver
  preserves the sanitized offscreen environment from the preceding increment.
  Exact pytest commands, logs and XML are in the corresponding .venv/checks files.

Existing uncommitted regressions were preserved. No data files, importer behavior,
database integration, canonical column ordering, credentials or billing settings
were changed. Nothing staged, committed, pushed or sent; no additional AI agent
was invoked. Independent Argon review is outstanding.

Next: if the friend still cannot launch using the documented environment command,
obtain the full terminal traceback, Python version and exact launch method before
changing startup logic. Manual interactive verification on his host remains open.

## Chunk 4 discovery-protocol increment — 2026-10-27

Added bounded NASA exact planet-name query construction and strict validation of
supplied catalog-response bytes, with synthetic tests. No network caller or search
screen is connected yet, and no archive data was downloaded. This is catalog
identity metadata, not spectral retrieval or scientific validation. SpectrumData,
CSV and persistence behavior remain unchanged. Focused: 35 passed; full: 193 passed,
1 directory-symlink-privilege skip. Historical plans were preserved. See the Chunk 4
implementation log and decisions file for chronology, limitations and the next
download-approval-dependent check. Independent Argon review remains pending.

## Live NASA validation — 2026-10-27

User-authorized public NASA retrieval succeeded: one WASP-39 b catalog identity
validated by the existing parser, plus a partial TOP 20 spectral-metadata snapshot.
Raw responses, exact query URLs, UTC times, HTTP status and hashes are preserved
under data/NASA/2026-10-27. The metadata identifies the Feinstein et al. 2023 NIRISS
331-point record, but its measurement file was not downloaded or equated with the
bundled CSV. The Chunk 4 implementation log and data README contain the evidence
and limitations. Full regression: 195 passed, 1 symlink-privilege skip; exit 0.
No credentials, extra AI agents, commits or pushes. Online search/measurement
retrieval is not yet connected to the application. Public NASA download approval
continues; the other existing scope/billing/credential restrictions remain active.

## NASA measurement import — 2026-10-27

Retrieved the actual 331-row NASA transmission .tbl, with unchanged raw product,
provenance and download-path derivation evidence under data/NASA/2026-10-27.
Added strict NASA transmission IPAC parsing and Import Spectrum support in the
existing GUI. It displays explicitly supplied microns/percent and retains all 29
source columns plus canonical aliases, signed errors, flags, source URLs and file
metadata. CSV import behavior is unchanged. Full regression: 212 passed, one
symlink-privilege skip. Details and limits are in the Chunk 4 implementation log.
Online search and automatic in-app downloading/cache registration are still open;
Argon review is pending. No credentials, extra agents, commits or pushes.
