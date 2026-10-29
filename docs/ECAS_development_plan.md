ECAS development plan
The goal is to build ECAS in manageable chunks, with each chunk producing a working, testable result. We should avoid adding several interconnected systems at once, because that makes errors harder to isolate and leaves you with code that's difficult to understand.

Latest continuation (2026-10-28): user accepted the first six Argon code reviews
and authorized continuation. Feedback steps 5 (independent input inspection) and
6 (Overview/Settings content) are implemented locally. Overview provides workflow
shortcuts and loaded-state summaries; Settings exposes read-only configured paths
and the shared session CSV-schema preference. See
`docs/Chunk_5_1/WORKSPACE_PAGES_IMPLEMENTATION.md`. Latest suite: 571 passed,
1 skipped; focused: 121 passed. Batch 7 subsequently returned zero findings for
its four listed files; all seven feedback reviews now have zero findings in their
stated scopes. Remaining desktop acceptance and future scientific/production
boundaries are reconciled in `docs/Chunk_5_1/ACCEPTANCE_STATUS_20261028.md`.
Desktop acceptance remains open and scientific validation deferred. The following feedback
paragraphs and counts describe earlier checkpoints, not current acceptance.

Current user-approved feedback workflow (2026-10-28): identify project spectra,
separate reference browsing from comparison, investigate 55 Cancri e, expand
verified retrieval mappings, add compatible comparison selection/inspection, then
develop useful Overview/Settings. See
`docs/Chunk_5_1/USER_FEEDBACK_WORKFLOW_20261028.md`. Steps 1–2 are implemented locally:
metadata labels/fallbacks and source-attributed tooltips, no database migration;
dedicated Molecular References page and a separate explanatory Comparisons page.
Step 3 evidence: 55 Cancri e resolves to 55 Cnc e and returns four Transmission
plus 19 Eclipse records in captured and live app checks. Earlier zero results
were not reproduced; their cause remains unknown. Status now explains excluded
counts; resolution/query behavior is unchanged. Step 4 adds verified H2O / POKAZATEL
and CH4 / MM main-isotopologue products alongside CO2, with separate limits,
citations and cache identities. Actual-window small downloads/offline reopen passed.
Next: independent dataset selection and compatibility explanations.
Latest suite: 560 passed/1 skipped, exit 0. Published review baseline is `98abaec`
(538 passed/1 skipped); these increments still need review and desktop checks.

Historical integration baseline (2026-10-28): merged master `2de79c7` includes the NASA retrieval/cache workflow and the CSV import manager. The earlier `7a4061a` build passed 281 tests with one skip; that result does not validate the merge. Inspection reproduced a merged CSV GUI `NameError` because its dispatch method still calls the removed `import_spectrum_csv` import. This was repaired and re-tested in subsequent increments. Earlier counts and completion checklists below are dated historical evidence, not current full-suite results.
Local follow-up: CSV routing has since been repaired and alias resolution added.
Latest full local suite: 341 passed/1 skipped; see PROJECT_STATE and the Chunk 4 log.
These local changes are not yet committed, pushed or independently accepted.
Proposed development chunks

Chunk 0 — Working foundation
Complete

- ✓ Desktop shell, navigation, CSV import, table display, initial tests.

Goal: Maintain a working baseline before expanding functionality.




Chunk 1 — Scientific data model

Define what an ECAS spectrum is independently of the interface.
- ✓ Establish a consistent spectrum representation (frozen dataclass).
- ◐ Preserve source paths, column information, and metadata: path/columns retained in SpectrumData; units/signal-type remain None (uninferred per spec); no scientific metadata beyond CSV columns exists.
- ✗ Separate file-import validation from scientific suitability checks: importer validates structure and records warnings but performs no scientific suitability evaluation.
- ◐ Add tests for the model and its validation rules: test_csv_importer.py provides 8 functional tests covering required columns, missing values, invalid numbers; spectrum.py lacks direct type/unit assertions.

Completion criterion: Imported spectra become structured, validated objects rather than loosely organized dictionaries.




## Chunk 2 — Projects and persistence

**Status: Complete (core persistence verified)**  
**Deferred:** Comprehensive change-history/provenance tracking remains a future design decision.

Give datasets a durable home.

- [x] Create the SQLite persistence layer for spectrum data.
- [x] Save imported spectra and preserve `source_file`, columns, units, `signal_type`, and warnings.
- [x] Reload saved spectra from the SQLite database.
- [x] Verify that all 7 `SpectrumData` fields survive the save/load round trip.
- [x] Preserve column order and `None` values.
- [x] Handle spectra without an uncertainty column.
- [x] Support saving and loading multiple spectra and loading by index.
- [x] Handle nonexistent projects and database-clearing operations.
- [x] Validate project IDs, including path traversal and symlink escape cases.
- [x] Verify persistence implementation: `python -m pytest tests/test_persistence.py -v` — **20 passed**.
- [x] Confirm the completion criterion: saved spectrum data can be reloaded intact, verified by `test_round_trip_preserves_all_fields`.
- [x] Verify the final Git working-tree status and commit contents, if not already completed.

**Data integrity and scope**
- The source file path is tracked through `source_file`.
- Import warnings are preserved in the stored JSON data.
- Original CSV files are not modified by the persistence layer.
- Comprehensive change-history/provenance tracking is not implemented and remains deferred unless explicitly required.

**Verification note**
- Persistence tests: **20 passed**.
- Full test suite: **40/40 passing**.
- Chunk 3 plotting verified; application launched with `test_spectrum` import and display working correctly.

**Completion criterion:** A saved project can be closed and reopened with its imported spectrum data intact. **Verified by the passing persistence round-trip test.**




Chunk 3 — Spectral visualization

Make imported data scientifically inspectable.
- **Goal:** Plot real imported measurements for visual inspection.
- **Completion criterion:** Users can inspect a real spectrum without changing its underlying data.

**Progress checklist**

Plotting component:
- [x] Create the PyQtGraph-based plotting widget.
- [x] Accept normalized `SpectrumData` rather than parsing CSV files in the plotting component.
- [x] Apply available axis and signal units from `SpectrumData`.
- [x] Filter missing, non-numeric, and non-finite coordinate pairs.
- [x] Reset visible and internal state after unsuccessful loads.
- [x] Verify plotted coordinates against the supplied measurements (automated tests confirm coordinate fidelity).
- [x] Verify source rows, columns, and metadata remain unchanged (frozen dataclass ensures immutability).

Application integration:
- [x] Display the plotting widget on the existing Spectral Data page.
- [x] Update the plot and data table together after a successful import.
- [x] Replace the previous plot when a new spectrum is imported.
- [x] Ensure rejected imports do not leave a misleading previous dataset visible.
- [x] Verify missing metadata is not presented as measured information (units displayed from `SpectrumData`, not invented).

Verification:
- [x] Run the targeted plotting tests and record the actual result (**all plotting tests passed**).
- [x] Run the full test suite and investigate failures (**40/40 passing overall**).
- [x] Manually verify plotting, table behavior, replacement, and rejected imports (application launched; `test_spectrum` imported and plotted correctly).

Dataset selection:
- [ ] Resolve whether selection among saved spectra is required in Chunk 3,
      given that the current import workflow replaces the displayed dataset.
      *Note:* Existing documentation does not explicitly resolve this. Defer to future work; no selection behavior implemented in current codebase.

Completion:
- [x] Confirm that users can inspect a real imported spectrum without changing
      its underlying data (manual verification via `test_spectrum` import and plot).
- [x] Record which behaviors were verified automatically and manually (automated tests + manual app launch/import/plot confirmation).

---



Chunk 4 — Online archive integration

**Latest acceptance update (2026-10-28):** All scoped Chunk 4 application Argon
batches/correction reviews have no unresolved confirmed findings. User has now
confirmed manual review complete. Record the manual gate complete based on that
confirmation, without invented checklist results. The historical reconciliation
status below predates these receipts. Deferred formats/providers remain outside
this supported transmission workflow; real-data scientific validation is deferred.

**Historical reconciled status (2026-10-28): implemented in part; acceptance open.**
NASA exact-name metadata search, supported transmission-table download, integrity-checked
sidecar cache, provenance and offline reopening exist. The review branch was merged
via `6c90ce5` and PR #1 (`2de79c7`); integration is done, verification of that merge
was pending at that merge. CSV dispatch has since been repaired locally and the
merged local workflow re-tested. Independent review reports
exist, but targeted acceptance of revised fixes is outstanding. Human use produced
feedback; it was not a complete manual acceptance pass.

**Next bounded tasks, in order:**
Progress at this checkpoint: tasks 1–5 below are implemented/tested locally.
Project source attachments, link presentation and compact controls are now covered
by automated integration checks. Final human acceptance, normal-desktop layout
verification and targeted independent review remain outstanding; Chunk 4 is open.
1. Restore GUI CSV dispatch through the import manager while retaining the NASA
   table path. Verify generic/archive CSV, both GUI entry points, errors and .tbl
   imports; then run the merged full regression suite.
2. Investigate exact-name/zero-result behavior for the reported planet names.
   Separate unresolved names, absent archive products, unsupported spectrum types,
   truncated inventories and request errors. Do not assume FITS is the cause.
3. Add evidence-based name resolution with explicit ambiguity handling. Never
   silently substitute a different planet; retain canonical identifiers in provenance.
4. Connect selected imported/cached spectra to new or existing projects. Reuse the
   persistence service after defining how source identity, metadata and integrity
   records survive project reopening. Existing SpectrumData-only persistence does
   not establish full cache-provenance persistence or a working Projects UI.
5. Present NASA-relative source links as usable archive URLs while preserving raw
   source values. Limit the layout pass to button sizing/result spacing requested
   in review; broader styling remains deferred.

**Acceptance:** the repaired merged revision has recorded focused/full results;
the supported search/download/cache and project attach/reopen paths have explicit
success/failure checks; human feedback is dispositioned; required manual checks
and targeted independent review have evidence. Do not mark this chunk complete
solely because the PR was merged or a spectrum can be plotted.

**Deferred/open scope:** generalized FITS/IPAC support, additional observational
providers, a common provider interface and cache scaling
are not implemented. Investigate only as required by the next bounded task; do not
build a provider framework before a demonstrated need. Historical plans remain context.

Expand beyond local-file imports.
- Investigate appropriate scientific archives and available APIs.
- Implement source-specific providers behind a common interface.
- Preserve identifiers, citations, retrieval details, and source metadata.
- Cache retrieved data for reproducible offline access.
Completion criterion: ECAS can retrieve and register a real archival dataset with traceable provenance.




## Chunk 5 — Spectral Comparison Foundations and Method Selection

**2026-10-28 status:** Investigation started. Actual captured-source audit,
proposed input requirements and an isolated same-grid synthetic experiment are
recorded in `docs/Chunk_5/COMPARISON_INPUT_CONTRACT_DRAFT.md` and
`docs/Chunk_5/IMPLEMENTATION_LOG.md`. Broader sampling/noise/resolution evaluation
now includes synthetic response, fixed covariance and held-out template-search
calibration (see `docs/Chunk_5/MODEL_COMPARISON_PROTOTYPE.md`). Real product
conventions remain unresolved for empirical use. Noise/continuum mismatch and
off-grid synthetic tests now support a limited initial method decision in
`docs/Chunk_5/INITIAL_METHOD_DECISION.md`: compatible-observable overlay and residual
inspection. Decision and new robustness work await independent review; real-data
validation is explicitly deferred by the user. No production workflow or provider chosen;
The new research eligibility contract is implemented separately from application
code (see `docs/Chunk_5/ELIGIBILITY_CONTRACT_V1.md`); it awaits independent review.
User has confirmed manual review complete; real-data validation remains deferred.

Establish the scientific and technical foundations required for defensible spectral comparison. Do not assume that simple spectral-line matching is sufficient, and do not commit to a production comparison method before investigating the available evidence.

- **Define spectral comparability.** Establish the conditions under which spectra can be compared, including wavelength or wavenumber axes, units, spectral resolution, sampling, instrument characteristics, uncertainty, normalization, and relevant measurement conditions. Identify which differences can be corrected, which require explicit restrictions, and which make a comparison unsuitable.
- **Identify representative scientific test cases.** Establish realistic cases covering compatible spectra, differing resolutions or sampling, noisy or incomplete measurements, overlapping molecular features, and incompatible datasets. Use documented reference data where available and clearly identified synthetic fixtures where necessary.
- **Investigate candidate comparison methods.** Evaluate simple line matching alongside appropriate alternatives, such as reference-spectrum overlay, spectral correlation, peak-based comparison, and other scientifically justified methods. Assess their assumptions, sensitivity to noise and resolution, computational cost, interpretability, and suitability for the spectral data ECAS actually supports.
- **Define evaluation criteria.** Determine how candidate methods will be tested, what constitutes a meaningful comparison, how uncertainty and spectral overlap should be handled, and how false matches or ambiguous results will be communicated.
- **Select and document the initial method.** Choose the simplest method, or justified combination of methods, that meets the established scientific and technical requirements. Document its intended use, limitations, compatibility rules, and reasons for selection. If the evidence does not support a defensible selection, identify the unresolved questions rather than forcing a decision.
- **Establish the comparison contract.** Define the inputs, required metadata, validation outcomes, outputs, and provenance needed by the eventual comparison workflow.

**Completion criterion:** A documented, evidence-based comparison-method selection supported by explicit compatibility rules, representative test cases, evaluation criteria, and known limitations. No production comparison workflow is required in this chunk.

## Chunk 5.1 — Molecular Reference Spectra and Comparison Data Integration

**Latest continuation (2026-10-28):** All five feedback Argon batches returned zero
findings; see `docs/Chunk_5_1/review_feedback_20261028/RECEIVED_REPORTS.md` for scope
and limitations. Independent session observation/cached-reference selection and
separate inspection now exist in Comparisons, with blocked comparison explanations.
See `docs/Chunk_5_1/COMPARISON_SELECTION_IMPLEMENTATION.md`. Full suite: 566 passed,
1 skipped. Selection work needs its own review and desktop acceptance; production
eligibility/analysis and real-data scientific validation remain outside this increment.
Following status paragraphs describe earlier checkpoints.

**2026-10-28 status:** User confirmed independent review of the existing Chunk 5
foundation complete and authorized progression. Real-data validation is deferred;
manual review is recorded complete. Initial provider comparison selects ExoMol
for anonymous discovery investigation, with a bounded two-column zero-pressure
.sigma parser implemented and synthetically tested. See
`docs/Chunk_5_1/PROVIDER_INVESTIGATION.md`. New provider/parser work awaits review;
actual product requests, catalogue search, cache and in-app integration are pending.

Follow-on: bounded catalogue parsing/local name/formula/isotope search is now
implemented against a real anonymous master-index capture. See
`docs/Chunk_5_1/CATALOGUE_IMPLEMENTATION.md`; catalogue refresh/cache, UI and spectral
product requests are still pending. Parser/catalogue work awaits independent review.

Next increment: Comparisons now hosts reference catalogue search, explicit bounded
Qt refresh/cancel and atomic validated cache/offline reopening. Live metadata
refresh passed; no molecular spectra downloaded. See
`docs/Chunk_5_1/REFERENCE_BROWSER_IMPLEMENTATION.md`. New UI/network/cache requires
review; actual spectral request/download mechanics remain the next task.

Latest increment: bounded CO2 / 12C-16O2 / UCL-4000 retrieval is connected to the
Comparisons browser, with explicit temperature/range/spacing, separate reference
table, atomic provenance cache and offline reopening. Actual Qt live download and
offline reopening succeeded for an 11-point reference product; full tests are
538 passed/1 skipped. See `docs/Chunk_5_1/PRODUCT_RETRIEVAL_IMPLEMENTATION.md`.
Earlier pending statements above describe successive checkpoints. New Chunk 5.1
code needs independent review and desktop acceptance. General product mappings,
explicit observation/reference pairing and eligibility integration remain pending;
Chunk 5.1 is not complete. Real-data scientific validation remains deferred.

Establish a reliable way to discover, retrieve, cache, organize, and select molecular reference spectra so they can be used alongside observational data in ECAS. The choice of data provider and file format must be investigated rather than assumed in advance.

- **Investigate reference-data sources and formats.** Evaluate suitable scientific databases and providers for molecular spectra, including NIST where appropriate. Investigate JCAMP-DX and other relevant formats, considering spectral coverage, units, resolution, molecular identifiers, metadata, licensing or access restrictions, download availability, and suitability for the intended comparison methods.
- **Select an initial source and supported data representation.** Choose a practical initial source based on evidence. Define how retrieved reference spectra will be parsed and represented internally while preserving the original source data, source identifiers, units, metadata, and provenance. Clearly distinguish measured reference spectra, theoretical line lists, simulated spectra, and processed products.
- **Search from inside ECAS.** Verify the chosen provider's actual search/download
  interface and access terms before implementation. Support molecule name and
  other provider-supported identifiers, show identity/coverage/type/units before
  selection, and distinguish no matches, search failure, unavailable products and
  unsupported retrieval. Manual downloads alone do not satisfy this requirement.
- **Implement retrieval and caching.** Provide a controlled workflow for searching available molecular reference data, retrieving selected products, caching them locally, validating cached data, and reopening cached spectra without requiring another network request. Follow established ECAS patterns where appropriate, without assuming that the existing exoplanet-data cache can be reused unchanged.
- **Create a molecular reference catalogue.** Maintain a searchable catalogue linking molecular identities to available reference datasets and their associated spectra. Record relevant identifiers, source, spectral range, data type, units, retrieval status, and other metadata supported by the provider. A molecule may have multiple reference spectra, sources, conditions, or representations; do not treat these as interchangeable.
- **Connect reference spectra to the comparison interface.** Make cached and otherwise eligible reference datasets discoverable in the Comparisons tab. Allow the user to select the observational or input dataset and independently select the reference dataset or datasets to compare against it.
- **Support molecule selection.** Allow users to select individual molecules or inspect all eligible molecular references currently available. Show which reference datasets are available for each selection, and distinguish unavailable, uncached, incompatible, and successfully loaded data.
- **Preserve scientific provenance.** Retain the source and identity of every selected reference dataset. Do not infer molecular presence from catalogue membership, a spectral overlap, or a successful retrieval.
- **Validate the reference-data workflow.** Test searching, retrieval, parsing, caching, integrity checks, offline reopening, dataset selection, error handling, and the handling of missing or ambiguous metadata. Use real provider data where feasible and documented fixtures for reproducible edge cases.

**Scope boundary:** This chunk establishes molecular reference-data access, storage, organization, and selection. It does not establish that a particular molecule is present in an exoplanet atmosphere, nor does it require a finalized scientific comparison or atmospheric projection method.

**Completion criterion:** From within the application, ECAS can search the selected initial provider, discover and retrieve molecular reference spectra, cache and reopen them with traceable provenance, catalogue the available datasets by molecule, and expose eligible reference and observational datasets for independent selection in the Comparisons tab. Known format, access and compatibility limitations are documented. ExoMol two-column cross sections are the initial bounded implementation; NIST and JCAMP-DX remain unimplemented candidates for broader support.

## Chunk 6 — Scientific Comparison, Interpretation, and Projections

Entry update (2026-10-28): the supported Chunk 5.1 acquisition/selection/graphical
inspection workflow is implemented and reviewed per the user's batches 9–11
confirmation. Targeted live/desktop checks now cover initial/repeat CO2 completion
and the new independent Comparisons plots. See
`docs/Chunk_5_1/verification_final_workflow_20261028/RESULTS.md`. Later human plot
UX/smaller-window acceptance remains open; scientific validation is deferred.
The next bounded task is production eligibility integration as specified in
`docs/Chunk_5_1/CHUNK_6_ENTRY_SCOPE.md`; quantitative analysis remains unimplemented.

Chunk 6 implementation (local, 2026-10-28): User confirmed human desktop UI review
complete and functional. Stages 6.1–6.7 are implemented and verified:
- Eligibility & adapters (`ecas/comparison/eligibility.py`, `ecas/comparison/inputs.py`).
- Explicit unit/grid/bin-response alignment (`ecas/comparison/alignment.py`).
- Unweighted & Cholesky-weighted residual diagnostics (`ecas/comparison/residuals.py`).
- Multi-candidate evaluation with covariance parity and tie preservation (`ecas/comparison/candidates.py`).
- Aligned overlay & residual visualization and interactive candidate/persistence UI (`ecas/visualization/residual_plot.py`, `ecas/ui/comparison_browser.py`, `ecas/ui/main_window.py`).
- Tamper-evident project comparison persistence and reproducibility verification (`ecas/comparison/persistence.py`, `ecas/projects.py`).
- Forward-model provenance contract, `ecas-forward-model-v1` JSON loader, and ad-hoc cross-section projection block (`ecas/comparison/forward_model.py`).
- Five-perspective methodology deliverable (`docs/SCIENTIFIC_COMPARISON_AND_INTERPRETATION.md`) and progress log (`docs/Chunk_6/IMPLEMENTATION_LOG.md`).
Latest verification: 58 focused UI/persistence passed (7.72 s); 603 passed, 1 skipped full offscreen (14.41 s), exit 0. Raw cross sections remain blocked against transit depth pending an explicit radiative-transfer forward model; empirical mission forward-model validation remains deferred.

Implement the comparison workflow using the method selected in Chunk 5 and the molecular reference-data functionality established in Chunk 5.1. Develop projections only to the extent justified by the available scientific inputs and validated assumptions.

- **Connect datasets and validation.** Allow users to select an observational or input spectrum and one or more eligible reference datasets or molecules. Validate compatibility before comparison and explain which requirements are unmet when a comparison cannot proceed.
- **Implement the selected comparison method.** Apply the documented method and its defined preprocessing, alignment, resolution handling, uncertainty treatment, and other required operations. Keep the implementation consistent with the method-selection record; investigate and document any necessary deviation before expanding the method.
- **Support multiple candidates.** Where the method permits, compare a selected spectrum against individual molecules or multiple available references. Allow users to inspect results for individual candidates and compare their relative agreement without implying that the best numerical match is necessarily the correct scientific explanation.
- **Develop projections in a staged manner.** Determine which projections are scientifically supportable from the available data and comparison method. Potential outputs may include aligned reference overlays, expected spectral features, comparison scores, or other method-justified visualizations. Any forward modelling, combined-spectrum projection, or atmospheric interpretation requiring additional physical assumptions must have those assumptions explicitly defined and validated before implementation.
- **Explain results and limitations.** Present the data used, method applied, compatibility checks, relevant uncertainty, and known limitations. Distinguish observed measurements from reference data, modelled or projected spectra, and derived comparison results. Make ambiguous matches and unsupported conclusions explicit.
- **Preserve reproducibility.** Save or otherwise persist the identities and versions of the input and reference datasets, source provenance, relevant preprocessing and comparison settings, method version, and other parameters required to reproduce a result. Where necessary source data or software versions are no longer available, identify the limitation rather than claiming exact reproducibility.
- **Verify scientific and technical behavior.** Test known matches, ambiguous overlaps, incompatible datasets, altered resolution or sampling, noisy or incomplete inputs, missing metadata, and failure conditions. Include checks that prevent comparison scores or visual overlap from being presented as unsupported abundance estimates or proof of atmospheric composition.

**Completion criterion:** A user can select eligible observational and molecular reference datasets, run the selected comparison method, understand compatibility failures and methodological limitations, inspect the resulting comparison or justified projection, and reproduce the analysis from preserved inputs and settings within the documented reproducibility limits. No abundance or composition estimate is presented unless a separately justified and validated method supports it.




Chunk 7 — Integration and reliability

Make the assembled application dependable.
- Test failure recovery and malformed inputs.
- Verify project persistence and offline behavior.
- Test the full workflow from import to comparison.
- Improve error reporting and documentation.
Completion criterion: The complete workflow operates reliably without fabricated production data.



How we'll handle each chunk
Approved reconciliation sequence: finish the applicable Chunk 4 repair, verification
and acceptance work; establish comparison constraints/method evidence in Chunk 5;
implement reference access/selection in Chunk 5.1; then implement the selected
comparison workflow in Chunk 6. Limited provider feasibility research may inform
Chunk 5 without prematurely building Chunk 5.1. A lab spectrum or line list is not
automatically comparable to an observed transmission spectrum.

After the approved documentation reconciliation is verified, routine local tasks
may proceed autonomously: inspect, bound the task and acceptance criteria, implement,
test, review, record actual results, then select the next eligible task. Continue
independent work when a separate task is blocked. Pause for unresolved consequential
scientific choices, data migrations, missing access, paid services or other existing
user restrictions. No routine commit/push is required or newly authorized. Human
acceptance and independent review remain distinct from self-review and passing tests.

Each chunk should follow the same process:
1. Define the goal. Specify exactly what the chunk will and won't do.
2. Inspect the current files. Check the relevant code and architecture documents before making changes.
3. Agree on the design. Identify the files to add or modify and explain their responsibilities.
4. Implement incrementally. Provide commented code, with a manageable number of changes at a time.
5. Test the result. Run automated tests and manually verify the relevant application behavior.
6. Close the chunk. Record what works, what remains incomplete, and what the next chunk depends on.
We should avoid speculative features, large rewrites, and unnecessary abstraction. Architecture should support the planned application without requiring every future feature to be built immediately.
