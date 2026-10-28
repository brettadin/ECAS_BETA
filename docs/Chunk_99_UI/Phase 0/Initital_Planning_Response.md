** This file is the response to Kickoff_prompt.md . It outlines the plans, does the review of the current codebase and whatnot **
** This is part of phase 0, and there will be at least one more document regarding phase 0 before we move on. But this is our starting point **

# ECAS UI Redesign — Initial Audit

Audit date: 28 October 2026 · Mode: Read-only · No implementation authorized

## 1. Executive summary

The redesign should be treated as an independent design and prototyping track for ECAS — Exoplanetary Characterization & Astrochemistry Suite, grounded in the application's actual capabilities rather than its long-term feature wishlist.

The supplied local project ZIP is available for inspection. I have confirmed that it contains the six requested UI redesign documents, including both roadmap formats, alongside the current project checkpoint and authoritative project-state and decision records.

The initial design materials establish several important principles:

- Organize the application around scientific tasks rather than accumulating unrelated controls in a crowded window.
- Give data, projects, molecular references, and analysis distinct but connected workflows.
- Keep metadata, source provenance, units, validation status, and scientific limitations visible where relevant.
- Design for future capabilities without implying that planned features already work.
- Develop and evaluate the redesign separately before integrating it into the evolving application.

The recommended direction is a task-oriented desktop workspace with persistent primary navigation, contextual details, and progressively configurable analysis layouts. This remains a design proposal until the current code, workflows, and roadmap documents have been fully reconciled.

### Evidence and scope boundaries

This audit distinguishes five evidence categories:

| Label      | Meaning                                                               |
| ---------- | --------------------------------------------------------------------- |
| Verified   | Directly inspected source, repository metadata, or executed behavior. |
| Documented | Recorded in project documentation but not independently demonstrated. |
| Inferred   | Reasoned conclusion from available evidence.                          |
| Proposed   | Recommendation for the redesign.                                      |
| Unknown    | Evidence is insufficient to establish the claim.                      |

The ZIP is a snapshot, not proof of the current local Git state. I will not claim that the application launches, that tests pass, or that the live repository matches the ZIP without independent evidence.

## 2. Source and documentation audit

### 2.1 UI redesign folder

Verified in ZIP

All six requested files exist under `docs/Chunk_99_UI/` in the supplied archive.

| File                                   | Role and findings                                                                                                                   |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `brainstorming_review_p1.md`           | Initial task-oriented workspace concept, plotting, metadata density, layout customization, and capability inventory.                |
| `brainstorming_review_p2.md`           | Refines workspace organization and establishes scratch investigations alongside persistent projects.                                |
| `brainstorming_review_p3.md`           | Specifies transit and molecular-spectrum visualization requirements; documents findings about the earlier ECAS implementation.      |
| `brainstorming_review_p4.md`           | Fourth brainstorming record; retained as a separate input to the design process.                                                    |
| `ECAS_UI_Redesign_Master_Roadmap.md`   | Detailed master roadmap covering workflows, architecture, design, scientific integrity, verification, resources, and future stages. |
| `ECAS_UI_Redesign_Master_Roadmap.docx` | Word-format version of the master roadmap.                                                                                          |

The four brainstorming documents have been inspected for their section structure and substantive opening material. The roadmap Markdown and Word documents have both been inspected for their structure and major content.

Roadmap comparison: Both versions contain the same 26 numbered major sections and agree on the major subjects, including scratch sessions, projects, scientific eligibility, transit analysis, integration, and phased implementation. The Markdown version is approximately 72,128 characters; the extracted Word paragraph text is approximately 67,698 characters.

This establishes broad structural agreement, not byte-for-byte or sentence-by-sentence equivalence. A complete semantic comparison of every paragraph remains a verification item.

### 2.2 Current project documentation

The following current project records were read or inspected.

| File                                                 | Role in the audit                                                |
| ---------------------------------------------------- | ---------------------------------------------------------------- |
| `README.md`                                          | Entry point and links to authoritative project records.          |
| `docs/REVIEW_CHECKPOINT_20261028.md`                 | Publication/review checkpoint and current verification summary.  |
| `docs/brains/PROJECT_STATE.md`                       | Current implementation status and outstanding work.              |
| `docs/brains/DECISIONS.md`                           | Approved technical decisions and their implementation scope.     |
| `docs/ECAS.md`                                       | Master scientific blueprint.                                     |
| `docs/ECAS_development_plan.md`                      | Development direction and chunk organization.                    |
| `docs/Chunk_5_1/PRODUCT_RETRIEVAL_IMPLEMENTATION.md` | Detailed molecular-reference retrieval behavior and limitations. |

Relevant architecture files identified in the ZIP include:

- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/DATA_FLOW.md`
- `docs/architecture/DATA_MODELS.md`
- `docs/architecture/ECAS_Architecture_Specification.md`
- `docs/architecture/MODULE_RESPONSIBILITIES.md`
- `docs/architecture/VALIDATION_STRATEGY.md`

These are relevant to the redesign, but a complete, line-by-line review of all six architecture documents is still outstanding. I will not represent them as fully audited.

The current project records also identify additional implementation and review material under `docs/Chunk_4/`, `docs/Chunk_5/`, and `docs/Chunk_5_1/`. These records matter because the current implementation includes work beyond the earlier UI brainstorming assumptions.

### 2.3 Important discrepancy: ZIP versus GitHub

The UI redesign folder is present in the supplied ZIP. Attempts to retrieve its six files from the inspected GitHub `master` branch and `codex/roadmap-reconciliation-20261028` branch returned not found.

This is a verified discrepancy between the supplied archive and those inspected GitHub references. It does not establish whether the documents are uncommitted local files, belong to another revision, or were otherwise excluded from publication.

The supplied ZIP remains the primary source for these six design documents, as requested. I will not assume they are already tracked in the live repository or ask you to recreate them.

### 2.4 Authority and conflicts

The following hierarchy is appropriate for the redesign:

1. Actual source code and reproducible behavior establish current implementation.
2. `PROJECT_STATE.md`, current checkpoints, and relevant implementation records establish documented status and verification evidence.
3. `DECISIONS.md` establishes approved design constraints.
4. The master blueprint and architecture documents establish intended direction, subject to implementation status.
5. The UI brainstorming documents and roadmap supply design proposals, unresolved questions, and historical context.

The roadmap is not a production implementation specification. Its proposed workspaces, scratch-session model, configurable layouts, and future analysis tools must remain proposals until their requirements and integration implications are reviewed.

## 3. Current project baseline

Evidence source: supplied project ZIP, current project records, and selected files fetched from GitHub. No local checkout was available for direct Git or runtime inspection.

| Baseline item                            | Finding                                                                              |
| ---------------------------------------- | ------------------------------------------------------------------------------------ |
| Project                                  | ECAS — Exoplanetary Characterization & Astrochemistry Suite                          |
| Repository                               | [brettadin/ECAS_BETA](https://github.com/brettadin/ECAS_BETA?utm_source=chatgpt.com) |
| Supplied local snapshot                  | `/mnt/data/ecas beta zip.zip`                                                        |
| Language                                 | Python                                                                               |
| Desktop framework                        | PySide6 / Qt                                                                         |
| Plotting                                 | PyQtGraph                                                                            |
| Documented review branch                 | `codex/roadmap-reconciliation-20261028`                                              |
| Documented baseline commit               | `2de79c7e025b492c900cc34a067e2875b744d8ab`                                           |
| Current branch tip                       | Unknown from the evidence retrieved                                                  |
| Local working-tree state                 | Unknown                                                                              |
| Local uncommitted changes                | Unknown                                                                              |
| Python environment on your PC            | Not inspected                                                                        |
| Application launch in this session       | Not performed                                                                        |
| Current GUI visual inspection            | Not performed                                                                        |
| Automated tests executed in this session | None                                                                                 |

The checkpoint identifies `2de79c7` as the baseline after merging PR #1. It reports a later full test result of 538 passed, 1 skipped, and records a successful live Qt check for a single retrieved CO₂ reference product. These are documented historical results, not tests independently rerun during this audit.

The project records identify `python main.py` as a launch method and `python -m pytest -q -o pythonpath=.` as a full-suite command for the documented review environment.

The ZIP includes `app.py` and `main.py`. The inspected copies of these entry points both construct a `QApplication`, create `ECASWindow`, display it, and enter the Qt event loop. The main-window source is imported from `ecas.ui.main_window`.

Baseline conclusion: There is sufficient source and documentation evidence to assess the broad architecture and begin design requirements. There is not yet evidence of the current local branch tip, working-tree cleanliness, launch success, or present-day GUI appearance.

## 4. Current UI inventory

The following inventory is based on actual source inspection, not screenshots. Relevant source links refer to the inspected repository files.

### 4.1 Main application shell

[Hypervision Explorer | qtec docs](https://images.openai.com/static-rsc-4/nnnzl_5iKoSy-pphA2jY5awszQCRHhlx02ZGYv0XkPJk3a-ip1ljqMej7ZO7JeFKHyLijB-YbCSK3bEl0sfU-dxohkwX4U1z3kliX67t6JHVhmZCbUkjWWTCPCyI8WAKXnHeWUjt-Cz4ZAJ_5Mo3JgMAxLi8nFVeiGUszHYqLCg?purpose=inline)

Main window and navigation

`ecas/ui/main_window.py`

- A `QMainWindow` with a fixed-width left navigation list.
- A `QStackedWidget` switches between five pages.
- The window has a 1200 × 800 initial size and a 900 × 600 minimum size.
- A status bar reports basic application state.
- A dark Qt stylesheet controls typography, selection, tables, and buttons.

[Qt-Advanced-Docking-System | Advanced Docking System for Qt](https://images.openai.com/static-rsc-4/NzWeFGe8q7uF2-JsZuHELyt3ZCFcFQTkwliCVGDrv3QvKGhaLSgJw49B4KBAuO2M1Bbq7avkq8ycOBkWApZYieCdsc5SCSXQvIZ3vy-RsqorFRnP9rWnHjtD_lqJYyf-jGSsIiqjBrrNfE-nTLXXGjEXFrgkzIZIeTYMV5cdnlI?purpose=inline)

Spectral Data

`ecas/ui/main_window.py`, `ecas/visualization/spectra_plot.py`

- Local CSV import and a schema selector.
- NASA archive search/download and cached-spectrum access embedded in the page.
- A spectral plot above a read-only table.
- The current display is replaced when another spectrum is successfully loaded.
- The importer explicitly avoids inferring scientific units or signal meaning.

[Experiment data management | umIT](https://images.openai.com/static-rsc-4/yduOvrZjxujwrEndiq5d8Xn_DnsZPLb4pqI344TzWvHWu1pmJJHG00uqIQHtuELLPnkUpzHRy9nfzAL9dzJgWOrirHoyyGD1_tQ8KRUxTK6CTvKMgOca7vTn__HaD5jcgUe04banjsAsyz56NPqifufnuJynnRsF4OVAu46QdMU?purpose=inline)

Projects

`ecas/ui/project_browser.py`, `ecas/projects.py`, `ecas/persistence.py`

- Create and select projects.
- Add the currently displayed spectrum to a project.
- List saved spectra and reopen a selected record.
- Delegate persistence through application services rather than issuing SQL in the widget.

[Spectragryph - optical spectroscopy software: Manual](https://images.openai.com/static-rsc-4/uP24HxaY6mvVNOKkd_SF1j6C6ijor__vJCgjZHo7GAsFwJ7CyqQjA4AgqcZDL3dIoaQFRU5s-3ld-T1SjglreY3VYFjHpgHWoCNW4xfpoDfN24EedWZV1ES1tA1HPS--vHgn9OwidIMj18kwqEi4Jg4uw0JqZzjV4tRkHX50cFY?purpose=inline)

Comparisons

`ecas/ui/molecular_browser.py` and `ecas/ingestion/exomol_*`

- Molecular catalogue search and selection.
- Explicit catalogue refresh/cancel controls.
- Bounded retrieval for one supported CO₂ product configuration family.
- A separate reference-data display and offline cache reopening.
- No production observation/reference comparison or molecular-detection workflow.

The illustrations above are generic visual references, not screenshots of the current ECAS application. They are not evidence of current appearance or behavior.

### 4.2 Navigation and page implementation status

| Navigation entry | Source-established status                                                                                 |
| ---------------- | --------------------------------------------------------------------------------------------------------- |
| Overview         | Placeholder page with heading and description.                                                            |
| Projects         | Implemented project creation, selection, attachment, and reopening workflow.                              |
| Spectral Data    | Implemented local CSV and supported NASA-table import/display workflows.                                  |
| Comparisons      | Molecular reference catalogue and bounded product retrieval are integrated; production comparison is not. |
| Settings         | Placeholder page with heading and description.                                                            |

Verified design issue: the current navigation labels do not fully communicate the breadth and limits of their contents. For example, Comparisons currently hosts catalogue browsing and reference retrieval, while the actual scientific comparison workflow remains unimplemented.

This supports reconsidering the information architecture. It does not, by itself, establish that every proposed workspace should become a separate top-level navigation item.

### 4.3 Workflow tracing and architectural boundaries

The inspected source supports the following separation:

- `ecas/ui/main_window.py` coordinates page layout, import actions, and spectrum display.
- `ecas/ui/nasa_browser.py` provides NASA discovery, supported retrieval, and cache controls.
- `ecas/ui/project_browser.py` exposes project operations through a project service.
- `ecas/ui/molecular_browser.py` coordinates reference search and retrieval controls.
- `ecas/ingestion/` contains parsing, provider, cache, and network-related modules.
- `ecas/models/spectrum.py` defines the spectrum representation.
- `ecas/projects.py` and `ecas/persistence.py` handle project and persistence operations.
- `ecas/visualization/spectra_plot.py` supplies the plotting widget.

The current implementation therefore provides reusable domain and service behavior that a redesigned presentation layer should investigate reusing. It would be premature to assume that the UI can be replaced without changes to every workflow.

### 4.4 Supported observations versus unverified usability claims

Verified from source:

- The navigation is fixed-width rather than a fully configurable docking shell.
- The main page construction is based on a fixed page list.
- Overview and Settings are placeholders.
- Spectral Data combines import, archive access, plotting, and tabular inspection.
- Molecular-reference browsing is integrated into Comparisons.
- The plotting widget and table are both embedded in the Spectral Data page.

Not yet verified visually:

- Whether controls overflow at the minimum window size.
- Whether tables and plot labels remain legible at different display scales.
- Whether the current hierarchy feels crowded during actual use.
- Whether all progress, cancellation, and error states are visually understandable.
- Whether keyboard navigation and screen-reader behavior are adequate.
- Whether the UI remains usable with unusually long filenames, metadata, or large datasets.

These need actual GUI inspection and targeted acceptance tests. Source structure alone cannot settle them.

## 5. Capability and workflow matrix

The matrix combines source inspection with the current project records. “Implemented” refers to the documented or inspected scope, not necessarily every future workflow in that category.

| Workflow                          | Current status                                | Main constraints and redesign implications                                                                                                                                            |
| --------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Target discovery                  | Implemented, bounded                          | NASA name/alias resolution and transmission-record discovery exist. Show matched identity, source, availability, and empty results without conflating a target with its observations. |
| Local data import                 | Implemented, limited                          | Generic CSV and a specific WASP-39 b archive schema are supported. Do not imply universal astronomical CSV/TXT support or silently infer units.                                       |
| Data inspection and plotting      | Implemented, basic                            | Current plot and table display imported spectra. More advanced multi-dataset inspection requires explicit compatibility rules and design work.                                        |
| Project creation and selection    | Implemented                                   | The project browser exposes project creation, selection, and refresh. A richer project asset view is a design opportunity, not an established missing backend capability.             |
| Project attachment and reopening  | Implemented, documented                       | Saved spectrum records preserve source material and provenance within established limits. Preserve this behavior during any UI migration.                                             |
| Scratch investigation             | Not verified as implemented                   | The roadmap proposes analysis without mandatory project creation. Requirements for lifecycle, recovery, temporary state, and promotion into projects remain open.                     |
| Molecular catalogue search        | Implemented                                   | Offline catalogue search and explicit refresh exist. A catalogue record does not guarantee an available product or compatible spectrum.                                               |
| Molecular-reference retrieval     | Implemented, narrowly                         | One supported CO₂ / isotopologue / dataset workflow is documented. Broader provider-product mappings remain pending.                                                                  |
| Reference inspection              | Partially implemented                         | Reference values, metadata, provenance, and offline reopening are supported in the bounded workflow. A dedicated, richer reference-spectrum inspector remains a design candidate.     |
| Observation/reference pairing     | Pending                                       | Independent selection and explicit eligibility through the comparison rules remain outstanding.                                                                                       |
| Scientific comparison             | Research foundation only                      | Chunk 5 contains research prototypes and method decisions, not an integrated production comparison/scoring workflow.                                                                  |
| Transit analysis                  | Not implemented in the inspected ECAS_BETA UI | The earlier ECAS repository has a richer transit implementation; its behavior needs to be adapted rather than assumed compatible.                                                     |
| Settings and preferences          | Placeholder / not meaningfully developed      | Define actual user needs before introducing global settings, cache management, or saved layouts.                                                                                      |
| Layout customization and recovery | Limited / not verified                        | The current main window uses a fixed navigation and page structure. Start with predictable resizing, visibility controls, and restoration before considering advanced docking.        |

### 5.1 Scientific and data-integrity requirements

These are cross-cutting constraints, not optional polish.

- Distinguish observational measurements, molecular reference cross sections, simulations, and derived products.
- Keep source identity, provenance, units, and known conditions attached to displayed data.
- Treat spectral overlap as evidence for further investigation, not proof of molecular presence.
- Do not equate a molecular cross section with an observed transit-depth spectrum.
- Do not combine datasets into a comparison merely because both can be plotted.
- Explain unsupported operations and incomplete provider support before users commit to an action.
- Preserve original data and saved project behavior when introducing new presentation components.

### 5.2 Scratch sessions and persistent projects

Proposed model: support two related working contexts that share analysis tools.

Scratch investigation

Start quickly, import or select data, inspect plots, and experiment without requiring a persistent project. Make unsaved state and recovery behavior explicit. Allow selected work to be promoted into a project.

Persistent project

Organize datasets, references, analysis settings, provenance, and supported outputs into a durable research record that can be reopened and audited.

The important architectural distinction is between a scientific data asset and its membership in a working context. A scratch session should not silently become a second project database, duplicate source records, or delete source data when discarded.

Before implementation, establish what scratch state is saved, what is temporary, what can be promoted, and how provenance is preserved.

### 5.3 Configurable layouts

The roadmap's progressive approach is appropriate:

1. Resize panels and control plot/table proportions.
2. Show or hide optional areas.
3. Provide an obvious restore-default-layout action.
4. Consider docking and floating panels only if validated workflows require them.
5. Add named or workspace-specific layouts only when their persistence and migration costs are justified.

The current application uses ordinary Qt layouts and a stacked page container. A redesign can preserve that simplicity initially; it does not need to introduce a complex docking framework before usability requirements are established.

## 6. Transit-reference assessment

The original repository, [brettadin/ecas](https://github.com/brettadin/ecas?utm_source=chatgpt.com), is accessible. I inspected the actual source for its transit panel and key scientific modules.

### 6.1 Verified earlier-project behavior

| Earlier source            | Verified role                                                                                                                                         |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app/ui/transit_panel.py` | Transit-analysis UI, synchronized time controls, light-curve tracking, orbital views, and analysis controls.                                          |
| `app/core/timeseries.py`  | Time-by-wavelength spectral data, white-light curves, spectra at a selected time, transmission-spectrum extraction, and correlated-noise diagnostics. |
| `app/core/transit.py`     | Light-curve data and analysis, orbital positions, transit modelling, and derived transit-spectrum operations.                                         |
| `app/core/atmosphere.py`  | Optional atmospheric forward-modelling and abundance-scan functionality.                                                                              |

The transit panel uses a shared time value to synchronize the light-curve tracker and planetary position views. It supports a PyVista 3D orbit view when available, with a 2D projected-orbit fallback. The inspected source also separates calculations from the presentation layer and uses worker-thread analysis to avoid blocking the UI.

The original project's README documents a workflow involving transit light curves, wavelength-resolved observations, transmission-spectrum extraction, and atmospheric analysis. These capabilities belong to the earlier implementation; their existence does not establish that they are integrated into ECAS_BETA.

### 6.2 Capability comparison

| Capability                                      | Earlier ECAS                                                      | ECAS_BETA                                             |
| ----------------------------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------- |
| Synchronized transit light curve and orbit      | Implemented in inspected source                                   | Not implemented in the inspected UI                   |
| Shared time tracker and playback                | Implemented in inspected source                                   | Not implemented in the inspected UI                   |
| Wavelength-resolved time series                 | Implemented in inspected core module                              | Not verified as implemented                           |
| Transmission-spectrum extraction                | Implemented in inspected core module                              | No production transit-extraction workflow established |
| Atmospheric forward modelling                   | Implemented as an optional earlier-project capability             | Not implemented as a production workflow              |
| Molecular-reference retrieval                   | Earlier-project behavior not fully assessed in this pass          | Bounded ExoMol workflow implemented                   |
| Production comparison and atmospheric inference | Earlier-project behavior has separate assumptions and limitations | Not implemented as an integrated production workflow  |

The original implementation uses PyQt6 and PyVista, whereas the inspected ECAS_BETA interface uses PySide6 and PyQtGraph. This is a concrete compatibility difference.

### 6.3 What should be preserved or redesigned

Worth considering for redesign:

- One authoritative observation-position state shared by synchronized views.
- Linked light-curve and orbital displays.
- Explicit time and wavelength information.
- A clear distinction between broadband transit measurements and wavelength-dependent transit depths.
- Separation of scientific calculations from plotting and playback controls.
- Optional 3D rendering with a usable fallback.

Do not transplant wholesale:

- Qt widgets without checking binding compatibility.
- The old repository's data models or persistence assumptions.
- Scientific formulas or model assumptions without checking their validity and intended scope.
- Optional visualization dependencies without evaluating their cost and fallback behavior.
- UI actions that imply unsupported comparison or molecular-detection capabilities in ECAS_BETA.

The earlier project is a verified behavioral reference. The full dependency and calculation audit, including optional-dependency behavior, detailed scientific assumptions, and existing tests for every transit capability, remains incomplete.

## 7. Proposed information architecture

Recommendation: use a persistent application shell with task-oriented workspaces and a contextual inspector. The exact workspace order and whether Home deserves its own page should be decided after workflow mapping and low-fidelity wireframes.

### ECAS application shell

Current context · Project or scratch session · Background tasks · Settings · Layout recovery

Search

Targets, archive records, source identity, availability.

Projects

Persistent research, attachments, provenance, reopening.

Data

Import, validate, preview, inspect, organize.

Molecular References

Catalogue, retrieval support, product metadata, cache.

Analysis

Spectral inspection, eligible overlays, diagnostics, and future validated analysis tools.

#### Contextual inspector

Selected item · Metadata · Units · Provenance · Validation · Supported actions

Proposed structure. It does not represent the current application or authorize creation of these workspaces.

### Purpose and design constraints

- Search: make it easy to locate targets and distinguish planets from observation/product records. Preserve query context and source links.
- Projects: provide a clear view of saved assets and their provenance, with actions that preserve existing project behavior.
- Data: make import validation and scientific interpretation explicit. Do not assume every file has the same schema or that its units are known.
- Molecular References: separate catalogue discovery from actual product retrieval and show supported configurations, source conditions, and cache status.
- Analysis: organize plotting and supported operations around selected data, with explicit eligibility checks and scientifically meaningful axes.
- Settings: expose only real preferences and controls. Keep contextual scientific parameters near the workflow they affect.
- Contextual inspector: display details for a selected item without forcing every workspace to maintain a large permanent metadata panel.

### Home / Overview remains an open decision

The existing Overview page is a placeholder. A useful Home page might help users resume projects and scratch investigations or recover failed tasks. If it merely duplicates navigation, it should not be retained just because a typical desktop application has a dashboard.

Resolve this with a wireframe and a concrete user-task comparison, not by assuming that Overview must stay or disappear.

## 8. Visual and interaction design direction

The current source establishes a dark stylesheet and a conventional fixed sidebar. The redesign should first establish the information hierarchy and workflow requirements, then refine the visual styling.

### Proposed design principles

- Readable scientific data: give plots and data tables adequate space; allow secondary metadata to collapse.
- Progressive disclosure: concise result summaries first, with detailed metadata and diagnostics available on demand.
- Contextual actions: show actions relevant to the active workspace and selected item.
- Consistent status language: distinguish loading, cached, unsupported, failed, cancelled, and successful states.
- Recoverable customization: provide a visible path back to a usable default layout.
- Accessible interaction: maintain legible text, sufficient contrast, keyboard navigation, clear focus states, and error messages that explain the next action.
- Honest plotting: use explicit units, legends, source labels, and axis conventions. Never make incompatible datasets look scientifically comparable through styling alone.

### Plot and table interaction

The existing spectrum plot and read-only table provide a foundation for a richer inspection experience. A redesigned analysis workspace could consider:

- Plot/table resizing and visibility controls.
- Explicit axis and unit labels.
- Data-source and trace selection.
- Selected-point metadata.
- Clear distinctions between original and derived data.
- Linked views for time-series analysis when the underlying data supports them.
- Export actions that preserve meaningful metadata and provenance.

These are design candidates, not a commitment to implement all of them. Each should be tied to a real user task and the capabilities of the relevant scientific model.

### What should not be decided yet

The evidence does not yet justify committing to a detailed color palette, typography system, universal search, unrestricted docking, multiple plot engines, or a comprehensive design component library. Those choices should follow the workflow audit and wireframes.

## 9. Architecture and isolation recommendation

### 9.1 Recommended starting strategy

Proposed: begin with a standalone design and prototype workspace, using mock data and thin adapters where necessary. Do not scaffold it or modify the application during this audit.

The roadmap's hybrid approach is appropriate, but the least complicated option should be selected based on the first prototype's actual needs.

| Option                                     | Advantages                                                                                   | Risks                                                                          |
| ------------------------------------------ | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Separate branch or worktree in ECAS_BETA   | Easy access to current source, services, and tests; straightforward later integration.       | Conflicts with ongoing development and accidental changes to production files. |
| Separate prototype directory or repository | Stronger isolation; easy to explore workflows using mock data.                               | Can duplicate domain concepts or drift away from the current application.      |
| Hybrid approach                            | Start isolated, periodically compare current source, and integrate only reviewed components. | Requires explicit adapter contracts and periodic reconciliation.               |

My recommendation is to start with an isolated prototype and mock data, then run a small integration investigation before choosing the production implementation strategy.

A prototype should clearly identify simulated actions and data. It must not make mock downloads, comparisons, or scientific results appear real.

### 9.2 Integration boundaries

The inspected code suggests the following existing components are candidates for reuse:

- `ecas/models/spectrum.py` — spectrum representation.
- `ecas/ingestion/import_manager.py` — import coordination.
- `ecas/ingestion/nasa_*` — NASA discovery, supported data retrieval, and caching.
- `ecas/ingestion/exomol_*` — molecular catalogue, bounded retrieval, and reference caching.
- `ecas/projects.py` and `ecas/persistence.py` — project operations and persistence.
- `ecas/visualization/spectra_plot.py` — current plotting widget.

These should be treated as candidate integration boundaries, not an unconditional reuse commitment. Their public interfaces, lifecycle assumptions, and UI coupling need to be reviewed before integration.

The presentation layer should not become responsible for scientific calculations, raw database operations, provider protocols, or the meaning of source metadata.

### 9.3 Integration risks

1. Parallel development: the current application may change while the prototype is being designed. Recheck the current project state before each integration task.
2. Data-model divergence: scratch sessions, registered datasets, project attachments, molecular references, and analysis results should not become competing representations of the same scientific asset.
3. Qt binding compatibility: the earlier transit project uses PyQt6; the current application uses PySide6. Existing widgets cannot be assumed to be directly reusable.
4. Persistence and provenance: redesigning the interface must not bypass existing source-retention, integrity, or project-reopening behavior.
5. Capability drift: a polished prototype must not imply that planned scientific functionality already exists.

No branch, worktree, prototype scaffold, or source changes have been created.

## 10. Prioritized roadmap

The roadmap below retains the spirit of the supplied master roadmap while prioritizing evidence, low-risk deliverables, and explicit approval gates.

Phase 0 — Establish the evidence baseline

Current audit

Verify the supplied documents, current source, relevant architecture, implementation status, and integration constraints.

Deliverable: evidence-backed audit, discrepancies, and unresolved questions.

Phase 1 — Capability inventory and user journeys

Complete the architecture review and map the critical workflows, including import, projects, references, scratch work, and analysis.

Deliverable: traceable capability matrix and workflow diagrams.

Phase 2 — Requirements and decisions

Resolve the workspace model, scratch lifecycle, Home decision, minimum metadata requirements, and first-stage layout customization.

Deliverable: approved requirements and documented design decisions.

Phase 3 — Information architecture and wireframes

Map navigation, major screens, contextual inspectors, data flows, and error/recovery states.

Deliverable: low-fidelity wireframes and annotated interaction flows.

Phase 4 — Visual and interaction design

Establish typography, contrast, component patterns, plot/table conventions, and accessible interaction states.

Deliverable: design system and representative high-fidelity screens.

Phase 5 — Standalone interactive prototype

Demonstrate a small set of representative workflows with clearly identified mock data and simulated operations.

Deliverable: runnable or otherwise inspectable prototype, documented limitations, and interaction acceptance checks.

Phase 6 — Integration investigation

Verify adapter boundaries, Qt compatibility, persistence behavior, test coverage, and current mainline differences.

Deliverable: integration plan with explicit technical risks and acceptance criteria.

Phase 7 — Incremental production implementation

Implement only approved, integration-ready slices, preserving working functionality.

Deliverable: small reviewable changes, tests, GUI acceptance evidence, and targeted documentation updates.

Phases 8–9 — Validation and release

Validate usability, scientific claims, accessibility, persistence, regression behavior, and integration completeness.

Deliverable: acceptance evidence, known limitations, and an accurate release record.

### Phase acceptance criteria

| Phase | Completion criteria                                                                                         |
| ----- | ----------------------------------------------------------------------------------------------------------- |
| 0     | Current source and authoritative records are sufficiently reconciled to support requirements work.          |
| 1     | Each critical workflow has an implementation status, source references, limitations, and verification gaps. |
| 2     | Consequential design decisions have explicit approval; deferred questions are recorded.                     |
| 3     | Wireframes cover primary and failure/recovery states and trace back to approved requirements.               |
| 4     | Visual patterns are consistent, accessible, and demonstrated on representative screens.                     |
| 5     | The prototype demonstrates meaningful workflows without misrepresenting simulated functionality.            |
| 6     | Integration boundaries, compatibility issues, and verification methods are documented.                      |
| 7     | Each approved slice passes proportionate tests and GUI acceptance where applicable.                         |
| 8     | Scientific integrity, regression behavior, usability, and limitations are assessed with evidence.           |
| 9     | The integrated application and documentation agree on the actual shipped state.                             |

The roadmap's more advanced features—unrestricted docking, saved layout presets, broader provider support, and advanced scientific analyses—remain conditional. They should be scheduled only after the earlier requirements establish their value.

## 11. Open questions and decisions

The master roadmap contains many useful questions. Only a subset needs to be resolved early.

| Question                                                        | Priority                               | Recommendation                                                                                                |
| --------------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Should scratch work exist alongside persistent projects?        | High                                   | Retain as a core design question. It affects navigation, persistence, and data lifecycle.                     |
| Should Home be a dedicated workspace?                           | Medium                                 | Decide after workflow mapping and wireframes.                                                                 |
| Should the prototype live in a separate repository or worktree? | High before prototype creation         | Prefer an isolated prototype initially; choose the exact location when the first prototype scope is approved. |
| Which local file formats are first-class?                       | High before detailed import design     | Base this on actual supported workflows and validation requirements, not file extensions alone.               |
| What makes two datasets eligible for a comparison?              | High before analysis UI implementation | Use the existing research contract and method decisions; do not invent compatibility rules in the UI.         |
| Which transit capabilities should be recovered?                 | Medium to high                         | Inspect the earlier implementation and compare its assumptions with current domain models before deciding.    |
| How much layout customization is necessary?                     | Medium                                 | Begin with resizing, visibility controls, and reliable restoration.                                           |
| Which visual styling should be adopted?                         | Deferred                               | Establish information architecture and wireframes first.                                                      |

Two additional findings affect the audit itself:

- The UI redesign documents exist in the supplied ZIP but were not found on the inspected GitHub branches.
- The current local Git state, full visual appearance, and full architecture-document review remain unverified.

These should be resolved or explicitly carried forward before detailed integration planning.

## 12. Recommended next action

Complete Phase 1: the capability and workflow audit against the supplied ZIP and the current ECAS_BETA source.

This is the highest-value next item because it turns the broad redesign vision into an evidence-backed specification without committing to a visual design, creating infrastructure, or changing application behavior.

### Scope

- Finish reviewing the six architecture documents and relevant current development records, including the Chunk 5 and Chunk 5.1 implementation and review material.
- Trace the current main-window workflow into its import, project, molecular-reference, persistence, and plotting dependencies.
- Identify the existing tests and manual acceptance evidence relevant to each workflow.
- Complete the earlier-transit capability comparison, including the remaining scientific assumptions and optional dependencies.
- Document the current status of scratch work, project persistence, analysis eligibility, and layout recovery.
- Record source references, known limitations, and unresolved questions in one reviewable matrix.

### Acceptance criteria

1. Every critical workflow in the capability matrix has a source-backed implementation status.
2. Implemented, partially implemented, planned, and unverified features are explicitly distinguished.
3. The major data flows and likely integration boundaries are mapped.
4. The earlier transit implementation is compared with ECAS_BETA without assuming code compatibility.
5. Relevant tests and manual acceptance procedures are identified, with existing evidence distinguished from checks that still need to be run.
6. The audit identifies the minimum set of decisions required before wireframes begin.
7. No files are modified, no branches or prototype scaffolds are created, and no tests or GUI behavior are claimed to have been verified unless actually checked.

Completion gate: review and approve the capability matrix and the unresolved decisions before beginning requirements refinement or wireframing.

This completes the initial audit report to the extent supported by the evidence currently available. The remaining gaps are explicitly identified rather than treated as completed work. No implementation has begun.