# ECAS agent handoff — 2026-10-28

## 1. Current checkpoint and verification state

Repository: C:/AI-Projects/Bwett AI Project UwU/ECAS_BETA. Branch: codex/roadmap-reconciliation-20261028. Last observed published/local HEAD: 49e3b963b06e4a96dc626dd13178ab13f857bcd9. Remote: https://github.com/brettadin/ECAS_BETA.git. It was explicitly committed/pushed for external review; no merge or deployment occurred. Subsequent issue #4 changes remain local/uncommitted. This document records conversation-established state; no Git commands, tests, subprocesses or repository scan were run to create it.

Read AGENTS.md, clinerules.md, README.md, PROJECT_CHECKPOINT.md, docs/brains/PROJECT_STATE.md, docs/brains/DECISIONS.md and docs/ECAS_development_plan.md before new code. Preserve the working tree and the unrelated parent coordinator repository. Do not reset, change branches or overwrite local work.

### Reviewed Batches 1–8 checkpoint (published in 49e3b96)

All eight Argon code reviews completed with zero findings within their reported scopes. User accepted Batches 1–6; Batches 7–8 reviewed and passing. Batch 7 explicitly lists four reviewed files, not every context file in its prompt. Reports/dispositions are in docs/Chunk_5_1/review_feedback_20261028, review_selection_20261028, review_workspace_20261028 and review_desktop_20261028. Batches 1–5 have condensed receipts; later batches have supplied JSON. Preserve original prompts/manifests as historical snapshots. Git may normalize source line endings; numbered prompts and provider capture bytes have explicit preservation attributes. Reviewer-local citation markers are not independently resolvable sources.

The Batches 1–8 desktop checkpoint's last offline results were focused: 121 passed (5.54 s); full: 571 passed, 1 skipped (10.56 s), exit 0. Skip: Windows directory-symlink privilege. Exact commands from repository root:

- .venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_desktop_20261028/run_checks.py focused
- .venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_desktop_20261028/run_checks.py full
- Isolated normal-desktop launcher: .venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_desktop_20261028/launch.py

See that directory's RESULTS.md and saved logs/run JSON for exact environment keys, versions and limits. Launcher uses minimal environment and isolated projects/reference caches under .venv/checks/desktop-feedback, seeded from original public CO2/H2O/CH4 captures. NASA cache remains the application's default; do not operate on private research data. Automated runner uses QT_QPA_PLATFORM=offscreen, disabled pytest plugin autoload, temporary data and fixtures, with no live requests.

At that checkpoint, normal Windows agent checks verified readable Overview/Settings, original 331-row NASA table import/plot, independent water/methane reference inspection, shared CSV choice, restart reset, and corrected comparison headings/hash display at 1200 x 800. They did not verify project save/reopen through desktop UI, smaller-window layout, all tooltip/citation interactions or the later graphical Comparisons implementation. Screenshots were inspected in chat, not saved as a claimed image archive. Agent verification is not human acceptance.

### IMPORTANT: later issue #4 work is the actual current working state

Do not mistake the requested 121/571 baseline for the newest test totals. GitHub issue https://github.com/brettadin/ECAS_BETA/issues/4 reviews 49e3b96 and confirms core desktop workflow usability, with follow-ups and permission to continue. Item 5 confirmed path visibility, not an explicit human check of CSV sync/restart. See ISSUE_4_DESKTOP_FEEDBACK_20261028.md.

Local subsequent work:

- Batch 9: exact validated request/content/provenance/catalogue-context cache reuse; non-destructive grouping of existing identical files; richer session observation labels; immediate completion-display regressions. Different raw bytes or provenance remain distinct. No writer lock: simultaneous independent writers can still create equivalent files; reader groups them.
- Batch 10: native-unit reference plots in Molecular References and independent Plot/Data table tabs in Comparisons; explicit supported-download versus catalogue-only labels. No shared-axis scientific comparison.
- Batch 11: explicit scientific y-axis ticks (automatic SI prefixes disabled), compact sigma units, and manual Hide/Show request settings to enlarge reference inspection. Request controls are visible by default; collapsing does not alter parameters or cancel requests.

User states Batches 9–11 require no fixes per Argon. Record as reviewed on user confirmation; no individual JSON reports/file lists were supplied. Receipt: review_plot_desktop_20261028/09-11-user-confirmation.md. Preserve historical Batch 9/10/11 prompts; later source changes naturally differ from earlier hashes.

Newest offline results: focused 126 passed (8.25 s); full 576 passed, 1 skipped (13.47 s), exit 0. Commands use .venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_plot_desktop_20261028/run_checks.py focused or full. No later code change or verification-only test rerun is claimed. The earlier prepublication suite also recorded 571 passed/1 skipped in verification_publication_20261028.

Latest normal-window check: verification_final_workflow_20261028/RESULTS.md. Two actual anonymous CO2/UCL-4000 requests at 500 K, 4000–4010 cm^-1, spacing 1 produced 11 points and updated the curve immediately without manual cache reopening. Cache count stayed four on repeat. First live record differed from preseeded context-free fixtures by catalogue context, intentionally retained. Original/live CO2 raw SHA-256: d323b5dd2f11c87a3cd6c0dc041fd625f00d56ec05cc2f2f2fb756cb01ea9fab. Safe public cache metadata is recorded alongside results; original retrieval timestamps do not represent every reuse.

New Comparisons desktop checks verified original observation microns/% and reference cm^-1/cm² per molecule on independent axes, metadata-derived labels, switching observation to Data table, and preservation across Molecular References navigation. The source table says Feinstein et al. 2022 while archive descriptions can say 2023; do not correct source descriptions. Historical manual-reopen symptom is NOT REPRODUCED on current build, not a claimed causal fix or proof the user was wrong. Reinvestigate with precise failing build/request/status if repeated. Test windows were closed.

## 2. Key modified and added files

Batches 1–8 production modules:

- ecas/ui/project_labels.py: metadata-based project headings, filename fallbacks and escaped, separately source-attributed tooltips.
- ecas/ui/project_browser.py: renders loaded project labels and retains existing project create/attach/reopen actions.
- ecas/ui/main_window.py: six-page coordination, independent observation/reference workspaces, Overview summaries and Settings wiring.
- ecas/ui/molecular_browser.py: catalogue search, explicit supported product requests, cache reopening and separate reference display.
- ecas/ui/nasa_browser.py: inventory/excluded-type/truncation/error explanations while preserving the alias-first query behavior.
- ecas/ui/comparison_browser.py: independent session snapshots/cache selections, separate inspection, cache revalidation and conservative blocking explanations.
- ecas/ui/workspace_pages.py: page-entry in-memory summaries/shortcuts and session CSV preference/read-only configured paths.
- ecas/ingestion/exomol_product.py: immutable CO2/UCL-4000, H2O/POKAZATEL, CH4/MM main-isotopologue service mappings, per-service limits, parser/request/provenance binding.
- ecas/ingestion/exomol_product_network.py: bounded same-origin GET/POST/GET protocol, anonymous CSRF/cookie handling, cancellation and callback lifecycle.
- ecas/ingestion/exomol_reference_cache.py: atomic integrity-bound product envelopes, exact request/catalogue provenance and backwards-compatible reopening.
- ecas/projects.py: existing project use cases/source attachments; dependency reviewed in Batch 1, not a new migration. Actual path is a module, NOT ecas/projects/.
- ecas/models/spectrum.py: existing SpectrumData representation preserving explicitly known units and unknowns; reviewed dependency.
- ecas/ingestion/nasa_aliases.py and nasa_archive.py: existing resolver/inventory services reviewed in Batch 3; do not claim this increment introduced their pipeline.
- ecas/ingestion/exomol_cross_section.py and exomol_catalogue.py: existing bounded cross-section/catalogue parsers reviewed as protocol dependencies.

Tests:

- tests/test_project_labels.py: metadata conflict/fallback/escaping/identity and read-only presentation checks.
- tests/test_projects_ui.py: saved project reopening, visible labels and source preservation integration.
- tests/test_main_window.py: navigation/index/state, import dispatch and explanatory workspace boundaries.
- tests/test_molecular_browser.py: catalogue/UI/network lifecycle and navigation/offline behavior.
- tests/test_nasa_aliases.py: canonical identity and 55 Cancri alias regression evidence.
- tests/test_nasa_online.py: inventory distinctions, supported types and bounded mocked network behavior.
- tests/test_exomol_product.py: service forms/results, request policy, bounds, cache/provenance and actual-widget completion integration.
- tests/test_comparison_browser.py: independent snapshots/choices, invalid-cache clearing, source fidelity and blocked scientific operations.
- tests/test_workspace_pages.py: shortcuts/state, shared CSV choice, read-only paths/no scans, session reset.

Later local changes extend main_window.py, comparison_browser.py, molecular_browser.py, exomol_reference_cache.py and the product/comparison tests. New ecas/visualization/reference_plot.py draws exact validated reference samples on linear native axes; existing spectra_plot.py supplies observation plotting and excludes invalid numeric pairs without editing original rows. Existing data tables retain all rows. Line segments join samples visually, not additional measurements.

Evidence/docs: original public fixtures under data/ExoMol/2026-10-28/additional-products and data/NASA/2026-10-28/cancri-investigation; all Chunk_5_1 review/verification directories; ISSUE_4_FIRST_FIXES.md, ISSUE_4_NATIVE_PLOTS.md, ACCEPTANCE_STATUS_20261028.md and CHUNK_6_ENTRY_SCOPE.md. README, roadmap and brain records contain dated historical checkpoints; prefer newest notes plus actual code/evidence.

## 3. Non-negotiable scientific and engineering guardrails

- Never directly compare/overlay/subtract/score raw ExoMol absorption cross sections (cm²/molecule on cm^-1) against transit-depth observations without an explicit physical atmospheric model. Independent graphical inspection is allowed and must retain distinct units/axes. No molecular detection/abundance confidence from overlap or successful retrieval.
- Never infer missing units, observable/signal type, uncertainties, covariance, coordinate frame, response or planetary conditions. Unknown stays unknown. No implicit unit conversion, sorting, interpolation, normalization or noise assumptions to make inputs pass eligibility.
- Preserve original bytes, source metadata, citations and integrity. No destructive SQLite migrations, silent saved-spectrum rewrites or cache envelope migrations. Historical v1 CO2 two-citation records remain readable; missing isotopologue means original CO2 service only, never an arbitrary new default.
- Reopen offline by default. Only explicit authorized anonymous service actions contact public endpoints. Maintain origin/URL allowlists, bounded sizes/deadlines, manual redirect and cookie policies, ephemeral same-form CSRF used only for the single POST, no state forwarded to product GETs, and cancellation/reentrancy/shutdown safety.
- Offscreen automated tests have zero live network calls. Live checks are separately authorized/documented and do not establish scientific validity or all provider conditions. Use existing captures; do not fabricate unavailable data.
- Keep exact verified service limits; other catalogue entries do not automatically support downloading. No slug-derived arbitrary URLs. Reference defaults are product settings, not inferred planetary parameters.
- Preserve old cache records; grouping choices is not deleting duplicates. Exact-content reuse retains original retrieval timestamps. Different raw hashes/catalogue provenance/citations remain separate.
- No credentials, additional paid agents/model services or superseded coordinator probe. Preserve archives and parent repository. Relevant anonymous NASA/reference access is authorized; ask for out-of-scope access/downloads.
- Do not commit/push subsequent local changes without explicit user authorization. Earlier authorization published 49e3b96 only. No merge/deployment approval follows from code review. Runtime caches, private projects, dependencies and recovery bundles remain ignored/local. An unrelated untracked %SystemDrive% directory has been observed; do not publish/delete it automatically.

## 4. Immediate next steps and closure

1. Reconcile Chunk 5.1 closure against docs/ECAS_development_plan.md and ACCEPTANCE_STATUS_20261028.md. Core supported implementation and review are in place; latest graphical/live agent evidence is recorded. Do not silently mark every historical checklist item complete.
2. Remaining acceptance: human confirmation of the later plot UX and smaller-window readability; do not relabel agent screenshots as human acceptance. Earlier user issue #4 confirms core published desktop workflows, not all subsequent changes. Project save/reopen need not be falsely claimed repeated in the final plot pass.
3. Treat manual-reopen symptom as non-reproduced with live/offline evidence, retain the historical report, request precise reproduction only if it recurs. No speculative refresh hack.
4. Preserve this local checkpoint. Inspect actual Git status and relevant instructions before edits; no suites/subprocesses/broad scans were run during this handoff turn at the user's request. That restriction is for this turn, not a permanent project rule.
5. Only after explicit closure reconciliation, begin the bounded Chunk 6 entry task in CHUNK_6_ENTRY_SCOPE.md: deliberate production eligibility service/adapters, versioned truthful reasons and UI wiring. Read the reviewed research eligibility_contract.py, import_eligibility_adapter.py and INITIAL_METHOD_DECISION.md under docs/Chunk_5 first. Do not import research scripts as accidental production services. No quantitative residual/overlay or forward-model assumptions in the first integration.
6. Use declared synthetic compatible cases for service tests and original captures for fidelity; real-data scientific validation remains deferred. Carry forward response/grid/uncertainty/source-evidence requirements. Persisted comparison configurations, weighted diagnostics and a validated forward-model source are later bounded tasks.

No source code was changed for this handoff. Latest known verification remains 576 passed, 1 skipped; requested historical baseline remains 121 focused / 571 full. This distinction is intentional and essential for resuming at the actual state.
