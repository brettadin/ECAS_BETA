# ECAS UI Redesign and Scientific Workflow
## Master roadmap, methodology, resource guide, and long-term wishlist

**Project:** ECAS — Exoplanetary Characterization & Astrochemistry Suite  
**Purpose:** Independent UI/UX design and prototyping project intended for later integration into `ECAS_BETA`  
**Status:** Planning document; not an implementation specification or claim that proposed capabilities already exist  
**Prepared:** 28 October 2026

---

## 1. Executive direction

Treat this effort as a **parallel product-design and prototype track**, not as a large UI rewrite on the main development branch. Its deliverables should be portable: design principles, capability inventory, interaction maps, wireframes, visual references, a standalone prototype, integration notes, and acceptance criteria. The work should survive unrelated changes to `ECAS_BETA` and should be easy to reconcile with the repository later.

The target experience is a desktop scientific workspace for investigating exoplanets through spectroscopy. It should help the user move between finding targets and data, importing local files, inspecting spectra, managing projects and provenance, examining molecular reference spectra, and carrying out analyses—without presenting future or scientifically unsupported functions as operational.

### Recommended product principles

1. **Task-oriented workspaces:** give each major activity a clear home.
2. **Scratch-first exploration:** users can investigate data without creating a formal project, then promote useful assets and analysis state into a project.
3. **Projects as durable research records:** projects organize source assets, metadata, provenance, configuration, and reproducible results; they are not a prerequisite for every action.
4. **Scientific typing before visual mixing:** observations, model outputs, molecular line lists, cross sections, simulations, and derived products remain explicitly distinguished.
5. **Progressive disclosure:** concise rows and summaries first; detailed metadata, diagnostics, and technical settings on demand.
6. **Configurable but recoverable layouts:** users can resize, hide, dock, and restore panels without losing data or making core navigation inaccessible.
7. **Capability-aware controls:** disabled, unsupported, cached, running, failed, and successful states must be explicit and explained.
8. **Reuse services, not old UI assumptions:** preserve valid domain logic and tested calculations where practical; avoid tying new presentation code directly to a legacy widget.
9. **Incremental verification:** each slice has an objective, scope boundary, acceptance checklist, tests, and documentation update.
10. **Evidence-based status:** mark every feature Existing / Partially implemented / Proposed / Future / Unverified.

### What success looks like

A user can open ECAS, resume a project or begin a scratch investigation, locate or import data, understand what that data represents, inspect it in a readable plot, open metadata and provenance, select compatible analysis actions, see honest explanations when an operation is unsupported, save useful work, and reopen it later. The user can customize the workspace without accidentally deleting data or losing access to recovery controls.

This is a product vision, not a statement that the current application already provides all of these capabilities.

---

## 2. Scope, assumptions, and confidence labels

### In scope

- Navigation and workspace architecture.
- Information hierarchy and scientific language.
- Search and archive-result presentation.
- Local-file import and data inspection workflows.
- Projects, scratch sessions, data/reference registries, provenance.
- Molecular reference browsing and spectral inspection.
- Analysis and plotting workspaces, including a possible transit-analysis experience.
- Resizable/collapsible/dockable panels and saved layouts.
- Global versus workspace-specific settings.
- Loading, empty, unsupported, cached, error, cancellation, and recovery states.
- Visual design system, wireframes, interactive prototype, integration strategy, and verification plan.
- Reference research into existing astronomy and scientific tools.

### Not automatically in scope

- Building a full atmospheric retrieval engine.
- Claiming molecular detections from visual spectral overlap.
- Implementing every archive or provider in the first release.
- Replacing the persistence layer or rewriting all models before the UI architecture is understood.
- Recreating every capability from the original `ecas` repository without evaluating dependencies and scientific assumptions.
- Merging the side project into the main branch before it is stable and explicitly reviewed.

### Status vocabulary to use throughout

| Label | Meaning |
|---|---|
| **Existing — verified** | Seen in the current code or demonstrated with a reproducible test. |
| **Existing — reported** | Reported in project notes or implementation summaries but not independently rechecked here. |
| **Partial** | Some workflow exists, but important states, supported formats, metadata, or actions are missing. |
| **Proposed** | A design recommendation; not implemented. |
| **Future** | Intentionally deferred until prerequisites are met. |
| **Unverified / decision needed** | Evidence or a product decision is required before committing to it. |

Do not let wireframes or roadmap tables turn Proposed or Future items into apparent Existing functionality.

---

## 3. Known starting point and cautions

This section summarizes project context available when the report was prepared. It is not a fresh, exhaustive local code audit.

### 3.1 ECAS_BETA context available

The project context describes a Python desktop application using **PySide6 and PyQtGraph**, with SQLite-backed persistence and a `SpectrumData` model in the supplied project snapshot. The live repository must be inspected before depending on particular paths or APIs.

The recent project checkpoint describes work in areas including:
- CSV import and GUI dispatch, including a particular NASA archive CSV path rather than universal support for all CSV/TXT files.
- Project creation/selection, attaching and reopening data, and preservation of source bytes/provenance/integrity information.
- Indexed/selective loading and snapshot-consistent reads.
- NASA planet-name alias resolution and clearer empty/unsupported result messaging.
- Molecular reference catalogue browsing and a narrow ExoMol retrieval path.
- A reference cache that can reopen cached items offline.
- Research prototypes for comparison readiness, response/binning/uncertainty and robustness/null-calibration experiments.

The latest supplied checkpoint describes ExoMol retrieval as narrow: a CO₂ / `12C-16O2` mapping with a small 500 K, 4000–4010 cm⁻¹, 1 cm⁻¹-spacing preset. That is not general molecular retrieval, a complete atmospheric model, or a claim of direct comparability with observational transmission depth. The report must not broaden this capability in its mockups.

A previous project issue describes usability concerns such as repeated generic filenames (for example `source.tbl`), catalogue results that appear selectable but are not downloadable, a narrow default spectral interval, and some settings that require refresh. Treat these as reported issues to validate, not as a substitute for inspecting current code.

### 3.2 Original `ecas` repository as a behavioral reference

The separate repository `https://github.com/brettadin/ecas` contains an older `app/ui/transit_panel.py` and core modules reviewed in prior project discussion. The original transit panel is useful as a **behavioral reference**, not a drop-in implementation specification.

The reviewed behavior includes:
- A shared time control synchronizing the light-curve tracker, observer view, orbital view, and model flux.
- Play/pause, time scrubbing, playback speed, time/phase/model-flux readouts.
- A 3D view when the optional PyVista path is available, with a 2D projected-orbit fallback.
- Adjustable planet-size exaggeration and camera modes.
- A `Spectrum at t` view, distinct from an extracted transmission-depth spectrum.
- Tabs described in the earlier review for phase-folded data, spectrum at time, transmission depth, model residuals, noise diagnostics, and abundance profile.
- Loading local data, fetching TESS photometry/JWST spectra, and mock-data generation.

The old `timeseries.py` represents a `LightCurve` (time/flux/optional uncertainties) and a `SpectralTimeSeries` (time array, wavelength array, time-by-wavelength flux matrix), with helpers for relative spectra, transmission spectra, white-light curves, and noise diagnostics. Re-check these details against the live source before reuse. The old UI's circular-orbit approximation, model assumptions, and any visual exaggeration must be documented rather than presented as precision ephemeris or scale-accurate geometry.

### 3.3 Immediate architectural caution

Do not transplant the old panel wholesale. First determine:
- Which scientific calculations can be imported independently of the old UI.
- Whether ECAS_BETA already has equivalent or conflicting domain models.
- How time-series and spectral arrays should be represented and validated.
- Which optional dependencies are needed for 3D and what fallback is supported.
- How analysis state, projects, and session persistence currently work.
- Which outputs have scientifically defined units, uncertainty, and provenance.
- Whether the older code has tests and clear licenses/dependency constraints.

---

## 4. Independence and integration strategy

### 4.1 Keep a parallel track

Create a separate Git branch or, preferably for sustained work, a separate worktree and a dedicated side-project directory/repository. Keep the main branch untouched. A possible naming convention is `ui-redesign-lab` or `research-workspace-prototype`; names are suggestions, not existing branches.

Use one of these arrangements:

**Option A — same repository, separate branch/worktree**
- Advantages: easier to compare current code, reuse tests, and eventually open a PR.
- Risks: frequent conflicts if the side branch edits the same UI files as active development.
- Use when the prototype is tightly coupled to current Qt components.

**Option B — separate prototype repository**
- Advantages: strongest isolation from friend/agent changes; can develop design assets and prototype independently.
- Risks: later porting requires an explicit integration adapter and may create duplicate code.
- Use when early work is mostly wireframes, fake data, and UX behavior.

**Recommended hybrid:** start with a separate design/prototype package or repository containing design documents, mock data, and a runnable shell; periodically compare the upstream repository; port reusable components only after their interfaces are clear.

### 4.2 Never integrate by copying a whole branch blindly

Use a small integration protocol:
1. Record the base commit and date of the side project.
2. Fetch latest mainline and inspect the current project-state/decision docs.
3. Review changed files and any new service/model interfaces.
4. Re-run the capability inventory for affected areas.
5. Rebase or merge only the isolated side branch/worktree when appropriate.
6. Resolve conflicts by preserving the current mainline's data and scientific logic unless a deliberate change is approved.
7. Run the focused test set, then broader tests.
8. Document integration decisions and any functionality deferred.
9. Open a reviewable PR or equivalent change set; do not merge solely because the prototype works locally.

### 4.3 Define a stable boundary between presentation and scientific logic

Aim for this dependency direction:

`UI widgets → application/workflow services → domain models and scientific functions → persistence/provider adapters`

Avoid:
- Plot widgets issuing raw SQL.
- UI callbacks embedding scientific formulas.
- Provider API response dictionaries becoming the long-term domain model.
- One widget owning network retrieval, parsing, caching, plotting, and persistence all at once.
- UI-only layout preferences being stored in a scientific result record.
- Project membership being conflated with source-file identity.
- A scratch session being treated as an unsaved project with no distinct lifecycle.

Use adapters where the existing code differs from the new interface. An adapter translates current model/service shapes into the new UI's stable view model; it should not silently change scientific meaning.

### 4.4 Versioned contracts and compatibility

For each boundary, write a short contract describing:
- Inputs and units.
- Output type and schema version.
- Required and optional metadata.
- Errors and unsupported cases.
- Provenance and source identity.
- Cancellation and progress behavior.
- Persistence behavior.
- Tests that define compatibility.

Prefer explicit versioned data-transfer objects for long-lived saved state. Do not serialize arbitrary widget internals as the only representation of scientific work. A Qt layout-state blob can be a convenience for layout restoration, but saved analysis configuration should remain separately inspectable and versioned.

---

## 5. Product architecture: workspaces and global shell

### 5.1 Proposed navigation

Use dedicated workspaces with shared services. A reasonable first draft:

1. **Home / Overview** — resume recent work and see task status; remove it if it duplicates navigation and has no useful independent purpose.
2. **Search** — search planets, targets, archive observations, and supported data products.
3. **Projects** — create, open, organize, inspect, and reopen durable research projects.
4. **Data** — import local files, validate schemas/units, preview, inspect, and register datasets.
5. **Molecular References** — browse catalogue entries, identify supported products, retrieve where supported, inspect and reopen cached references.
6. **Analysis** — plot, inspect, transform, compare where scientifically eligible, and run available diagnostics.
7. **Settings** — global preferences, network/provider configuration, cache management, diagnostics, and layout reset.

The exact order and names should be tested with wireframes. Avoid making a menu item for every small tool. A workspace should correspond to a recurring user goal, not merely to a code module.

### 5.2 Global shell

Persistent elements:
- ECAS identity and current workspace.
- Current context label: **Scratch session** or **Project: [name]**.
- Global navigation that remains accessible after panels are hidden.
- Background-task indicator with progress, cancel where safe, and meaningful failure details.
- Global settings.
- Layout/panel controls, including a clear restore-default-layout action.
- Status area for concise context such as selected data, active provider state, or validation warning.

Do not crowd the top bar with all analysis parameters. Put settings next to the task they affect, and place genuinely global preferences in Settings.

### 5.3 Home / Overview decision

Do not build a decorative dashboard just because desktop applications often have one. It earns its place only if it helps users resume work. A useful Home could show:
- Recent projects and scratch sessions.
- Recent datasets and molecular references.
- Current/failed/cancelled background tasks.
- Clear actions: Open Project, Start Scratch Analysis, Import Data, Search Target.
- Warnings requiring attention, such as a missing source file or stale cache.

If those are better represented in navigation or a task launcher, remove Overview or rename it **Home**. Decide this after a workflow map and low-fidelity prototype.

### 5.4 Scratch and project analysis contexts

The same analysis tools should support two contexts.

**Scratch analysis**
- Starts without requiring a project.
- Can receive data from Search, Data, or Molecular References.
- Supports temporary plot and inspection configurations.
- Should recover useful session state after a restart when feasible.
- Must clearly distinguish unsaved configuration from saved source data/results.
- Can promote selected assets, plot settings, and supported analysis outputs into an existing or new project.
- Discarding a scratch session must not delete registered source files or project data.

**Project analysis**
- Loads data and references attached to the selected project.
- Preserves provenance, selected inputs, analysis parameters, outputs, and supported plot settings.
- Can add data without forcing the user back to a different workspace.
- Must distinguish project assets from temporary items and external references.
- Reopening the project should recover enough context to reproduce or audit the result.

---

## 6. Core workflows to design before coding

Create a swimlane or step-by-step map for each workflow. For every step, identify the user action, UI response, data change, failure states, and next valid action.

### Workflow A — Find an exoplanet and its data
1. Enter a planet/host/alias or use filters.
2. Resolve aliases and show what entity was matched.
3. Present result identity and useful metadata, including source/archive and observation/instrument/publication where available.
4. Separate the planet record from its observation/product records.
5. For each result, show a clear availability status: metadata only, downloadable, locally cached, unsupported, or failed.
6. Allow opening details, viewing source information, and transferring a supported product to Data or Analysis.
7. Preserve archive/source links and query context.

Acceptance criteria:
- Alias matches are not silently conflated.
- Empty results are informative.
- Metadata-only records cannot masquerade as downloadable data.
- Long names and duplicate observations remain distinguishable.
- Network errors do not erase the query or existing results.

### Workflow B — Import a local spectral file
1. Choose a file or drop it into the Data workspace.
2. Detect likely format/encoding/schema without silently asserting correctness.
3. Show a preview and let the user confirm delimiters, headers, columns, units, and axis semantics when needed.
4. Validate numeric content, missing values, duplicates, ordering, wavelength/wavenumber/time axes, uncertainty columns, and likely unit issues.
5. Display warnings separately from blocking errors.
6. Register the dataset with original bytes or an appropriate immutable source reference, content hash, source path/name, import time, parser/version, user-confirmed mapping, and provenance.
7. Plot a preview and expose metadata.
8. Send the data to Scratch Analysis, or attach it to a selected project.

Important: do not assume the user only has CSV files, only has two columns, or that all `.txt` files share a schema. FTIR and UV-Vis data can use different axis conventions and units. Do not silently convert or infer scientific meaning from file extensions alone.

Acceptance criteria:
- Original input is preserved or its preservation policy is explicit.
- Unknown units remain unknown until confirmed.
- Import errors identify the row/column/reason where practical.
- Large files do not freeze the UI.
- Reimporting the same file has a defined duplicate policy.
- A user can cancel before committing changes.

### Workflow C — Inspect a molecular reference
1. Search by molecule, isotopologue, provider, dataset, data type, and spectral region.
2. Explain the distinction between a catalogue entry and a retrievable product.
3. Show retrieval support before the user commits to a download.
4. For supported products, choose available conditions/range/resolution parameters with scientific defaults and clear units.
5. Display progress, cancel safely, and distinguish network, parser, validation, and cache errors.
6. Validate returned data and preserve provider/dataset/version/license/citation/parameters.
7. Plot the reference and its metadata.
8. Reopen cached data offline.
9. Send the reference to Analysis only with its scientific type and compatibility limitations intact.

Acceptance criteria:
- Unsupported products are not presented as retrievable.
- Cache status and source freshness are clear.
- Provider data and user-derived products are distinguishable.
- The UI does not label a reference cross section as a planetary transit spectrum.

### Workflow D — Quick scratch investigation
1. Start a scratch session.
2. Add one or more datasets/references.
3. Show the active items and their types/units.
4. Select a visualization or supported operation.
5. Inspect/adjust axes, range, labels, and display options.
6. Save/export a plot or result, or promote selected items/configuration into a project.
7. Recover after interruption or discard with a clear confirmation.

### Workflow E — Project-based investigation
1. Open/create a project.
2. Review assets, provenance, and prior results.
3. Add or retrieve data from within the project context.
4. Select analysis inputs and verify eligibility.
5. Run the analysis with visible progress and reproducible parameters.
6. Review plots, diagnostics, warnings, and results.
7. Save results with input identities, versions, parameters, software version, and date.
8. Reopen and audit the result.

### Workflow F — Customize and recover the workspace
1. Resize/collapse/move supported panels.
2. Hide and restore optional panels.
3. Adjust table columns and graph/table proportions.
4. Save preferences per workspace and optionally named layouts.
5. Restore a built-in layout at any time.
6. Upgrade to a new app version without silently losing all customizations.
7. Handle missing/renamed panels gracefully.

Acceptance criteria:
- Navigation and reset controls are always reachable.
- Layout changes do not delete data or change scientific results.
- Invalid saved layouts fall back to a safe default.
- Screen-size changes do not leave essential controls off-screen.
- Layout preferences are stored separately from project scientific state unless a project-specific layout is explicitly desired.

---

## 7. Workspace-by-workspace design specification

### 7.1 Search

**Primary purpose:** discover targets, observations, and products—not to become a full analysis screen.

Recommended layout:
- Search/filter bar across the top.
- Result table/list in the main area.
- Optional compact preview or details inspector.
- Details/provenance panel on selection.
- Explicit actions for Open Details, Inspect Product, Add to Scratch, Add to Project, or Download where supported.

Result rows should use meaningful identifiers rather than generic filenames. Include target, observation/product label, instrument, date, wavelength coverage, source/publication, and availability when those fields are available. Avoid filling the table with every technical field; use column chooser and inspector.

Status examples:
- `Metadata only`
- `Download supported`
- `Cached locally`
- `Unsupported product type`
- `Retrieval failed`
- `Needs unit/schema review`

Search result details should explain what the result actually represents. A planet catalogue entry, observation, extracted spectrum, archive file, and molecular database product are different entities.

### 7.2 Projects

**Primary purpose:** durable research organization and reproducibility.

Recommended structure:
- Project list with name, target(s), last modified, asset count, and status.
- Project workspace with tabs/sections such as Summary, Data & References, Analysis, Results, Provenance/History.
- Main content shows the selected section; an optional inspector shows metadata and valid actions.
- Project creation should not demand every future field. Allow partial creation and progressively add details.

Each project asset should show:
- Human-readable label.
- Entity type and scientific role.
- Original source/provider.
- Local identity/cache state.
- Key units/coverage.
- Added date and provenance.
- Valid operations and reasons unsupported actions are unavailable.

### 7.3 Data

**Primary purpose:** local ingestion, validation, data registration, and inspection.

Recommended layout:
- Import/registration actions and supported-format guidance.
- Dataset table with columns such as label, source file, type, axis/unit, coverage, rows/points, validation state, and project membership.
- Large spectral preview.
- Inspector with columns/units, parsing choices, validation messages, and provenance.
- Clear actions: Inspect, Re-import, Export, Send to Scratch, Attach to Project.

Do not confuse the original filename, internal storage name, user-facing label, and database identifier. Keep them separate.

Support a data-validation preview before final registration. A parser should report what it understood, not pretend that a syntactically valid table is scientifically interpretable.

### 7.4 Molecular References

**Primary purpose:** search and inspect molecular spectral resources and retrieve supported products.

Recommended layout:
- Catalogue/search results.
- Retrieval panel only when a selected entry supports retrieval.
- Main plot with pan/zoom, legend, units, range controls, and data cursor/inspection.
- Metadata inspector for molecule, isotopologue, provider, dataset, data type, conditions, units, range, resolution/grid, citation, licence, cache status, and retrieval settings.

For line lists, cross sections, opacity tables, or other provider-specific products, show the actual data type. Do not collapse all into a generic “spectrum” label.

### 7.5 Analysis

**Primary purpose:** interactive plotting and supported scientific operations.

Recommended default composition:
- Main plot area with most of the available width/height.
- Data/trace list to add, remove, show/hide, and reorder traces.
- Inspector for selected trace/axis/settings.
- Secondary diagnostics in tabs or dockable panels.
- Compact task toolbar for plotting, supported transformations, export, and result saving.
- Status/eligibility area explaining selected inputs and warnings.

Recommended plot capabilities, staged by maturity:
1. Single-spectrum inspection.
2. Multiple compatible traces with explicit units and legends.
3. Axis selection, range controls, log/linear scale where valid, labels, uncertainty display.
4. Data cursor and selected-point metadata.
5. Derived curves with clear input/output labels and reproducible parameters.
6. Residual/diagnostic plots when the corresponding analysis exists.
7. Linked views for time-series data.
8. Figure export and data export with provenance metadata.

**Scientific guardrail:** the UI must not enable a scientifically invalid comparison just because two arrays can be drawn. Before comparison, evaluate data type, axis semantics, units, uncertainty representation, calibration/response treatment, spectral range, and the operation's prerequisites. If eligibility is not established, permit side-by-side inspection if appropriate but label it as inspection, not a quantitative comparison.

### 7.6 Transit Analysis / time-series exploration

This is a potential future workspace inspired by the original `ecas` repository. It should be planned as a distinct analysis mode, not assumed to be a quick UI-only transplant.

Recommended composition:
- Large light-curve plot.
- Orbital/observer visualization with 2D fallback and optional 3D implementation.
- Shared playback strip: play/pause, time scrubber, speed, timestamp, orbital phase where defined, model flux/readout where applicable.
- Secondary views: spectrum at selected time, phase-folded curve, transmission-depth spectrum, model residuals, noise diagnostics, atmospheric profile/model diagnostics only when implemented.
- Data/provenance inspector.
- Model/observation distinction in legends and labels.

The shared clock should update all time-dependent views coherently. A spectrum extracted at a selected time is not the same object as a transmission spectrum derived from in-/out-of-transit data. The orbit display should disclose assumptions and any exaggerated scale. A simulated planet position is not an observed measurement.

Stage it carefully:
- **T1:** plot a time/flux series with uncertainties and selected-time cursor.
- **T2:** linked time selection and spectral-at-time view for valid time-resolved spectra.
- **T3:** orbital visualization with explicit assumptions and fallback.
- **T4:** additional diagnostics only when their underlying calculations are validated.
- **T5:** model fitting/atmospheric interpretation only after scientific requirements, tests, and validation are agreed.

### 7.7 Settings

Separate **global settings** from **workspace controls**.

Global:
- Appearance/theme and font scaling.
- Layout defaults and reset.
- Data handling/import preferences.
- Network/provider timeouts and offline behavior.
- Cache location/size/clear policy.
- Logging/diagnostics.
- Export defaults.
- Optional dependency status.

Workspace-specific:
- Search filters and result columns.
- Import parser/column mappings.
- Retrieval range/conditions.
- Plot axes/units/trace display.
- Analysis parameters.

Each setting should identify scope, default, persistence, validation, and whether changing it affects existing saved results. A display preference must never silently alter source data or scientific calculations.

---

## 8. Visualization and data-density standards

### 8.1 Space allocation

Use the available space for the user's primary task:
- Search: results and selected-item details.
- Data: preview plot and validation.
- Molecular References: spectral plot and technical metadata.
- Analysis: plot first; tools and diagnostics secondary.
- Projects: asset organization and reproducible work state.
- Home: shortcuts and resumable activity, not decorative charts.

Prefer adjustable splitters and dockable panels over a rigid grid of tiny plots. Set sensible minimum sizes and offer one-click focus/maximize for the selected plot.

### 8.2 Table and result design

- Use concise labels and human-readable metadata.
- Provide sorting, filtering, column chooser, and horizontal scrolling.
- Use stable IDs internally; do not display opaque hashes as the main label.
- Preserve long filenames in the inspector or tooltip without forcing every row to be huge.
- For large datasets, consider model/view patterns, paging, or efficient rendering rather than creating a widget for every cell.
- Make hidden columns a display choice only; exports should use an explicit export configuration and not silently omit hidden scientific fields.
- Include empty/loading/error states.
- Distinguish a missing value from zero and from “not available from provider.”

### 8.3 Plot conventions

Every plot should make clear:
- What quantity is on each axis and its units.
- Whether values are observed, derived, simulated, or theoretical.
- Which trace belongs to which dataset/source.
- Whether uncertainty is shown and what it represents.
- Whether the axis is wavelength, wavenumber, frequency, time, phase, or another quantity.
- Any transformations, normalization, binning, smoothing, or response treatment applied.
- The data range and resolution/sampling when relevant.

Avoid silently swapping wavelength and wavenumber or converting units without clear labels. If conversions are supported, show the original unit and conversion details in metadata/history.

### 8.4 Responsive behavior

Design for:
- Normal desktop dimensions.
- Smaller laptop screens.
- High display scaling.
- Long metadata strings.
- Dense result tables.
- Multiple open panels.
- Floating/detached panels returning to the main window.
- No 3D rendering available.
- Fonts or symbols unavailable on the platform.

Use graceful degradation rather than clipping, overlapping, or hiding required controls.

---

## 9. Layout customization and persistence

A flexible UI needs a safe customization model; unrestricted docking alone is not enough.

### Stage 1 — Reliable resizing
- Use splitters for plot/table/inspector proportions.
- Set minimum sizes and avoid zero-width critical panels.
- Remember window geometry and workspace split proportions.
- Provide a restore-default-layout action.

### Stage 2 — Hide/show optional panels
- Add a Panels menu with visibility checkboxes.
- Ensure a hidden panel can always be reopened from persistent navigation.
- Prevent the user from hiding every recovery or navigation affordance.

### Stage 3 — Dock and float selected panels
Qt's `QMainWindow`/`QDockWidget` support dockable, movable, and floating panels, plus `saveState()`/`restoreState()` for restoring layout. This is a candidate implementation technique, not a requirement to make every widget freely dockable. Stable unique object names, versioned layout state, compatibility handling, and a safe default layout are important. See the official Qt documentation in the resource list.

### Stage 4 — Named layout presets
Examples:
- **Standard:** plot + inspector + trace list.
- **Plot Focus:** maximized plot with compact toolbar.
- **Data Review:** table + preview + validation inspector.
- **Transit:** light curve + orbital view + playback controls.
- **Reference Inspection:** plot + molecular metadata.

Presets are a wishlist until simpler layout persistence works reliably.

### Stage 5 — Workspace-specific preferences
Save layout per workspace so a table-heavy Data layout does not overwrite the Analysis layout. Consider named custom presets later.

### Persistence boundaries
Store separately:
1. **Application preferences:** theme, default layout, last window size.
2. **Workspace layout preferences:** panel visibility/positions, table columns.
3. **Scratch session state:** open items, selected traces, current range, temporary configuration.
4. **Project scientific state:** inputs, analysis parameters, outputs, provenance.
5. **Source data/cache:** immutable originals or explicitly versioned cached provider products.

Layout migration requirements:
- Use versioned keys/state.
- Ignore unknown panel IDs safely.
- Recover if a panel has been removed or renamed.
- Never allow malformed saved state to block startup.
- Provide reset without deleting projects or cached scientific data.
- Do not accept arbitrary untrusted layout-state blobs from external sources.

---

## 10. Data architecture concepts to keep distinct

The redesign should use clear concepts even if the current implementation does not yet separate them perfectly.

### 10.1 Source asset
A file or provider product as obtained, with source identity, bytes/hash or stable reference, timestamp/version, licence/citation, and original metadata.

### 10.2 Registered dataset
A source asset interpreted by a parser: columns, axes, units, uncertainties, masks, validation results, and a schema/parser version.

### 10.3 Derived product
A transformed or calculated object, such as a binned spectrum, white-light curve, transmission-depth spectrum, fitted curve, residual series, or exported plot data. It must link to input identities and parameters.

### 10.4 Project membership
A relationship associating assets/results with a project. It should not require duplicating source bytes unnecessarily or erase provenance.

### 10.5 Scratch session
Temporary working context, potentially autosaved. It should not be confused with a source dataset or a durable project.

### 10.6 Molecular reference
A theoretical or laboratory/provider resource with a data type such as line list, cross section, opacity product, or model spectrum. Store temperature, isotopologue, pressure/broadening assumptions, grid/range, provider/dataset version, and generation/retrieval parameters when applicable.

### 10.7 Analysis result
A versioned result with inputs, parameters, method/version, units, uncertainties, diagnostics, warnings, provenance, and reproducibility information.

These boundaries make it easier to adapt the UI if friends or agents change implementation details. The UI should depend on stable concepts and service contracts rather than private database column names.

---

## 11. Scientific integrity and eligibility model

Implement a shared **capability/eligibility description** for every data item and action. This is a key architectural requirement.

For each item, track or derive:
- Data type / scientific role.
- Axis semantics and units.
- Value semantics and units.
- Uncertainty availability/type.
- Provenance completeness.
- Source/cache state.
- Parser/validation status.
- Supported actions.
- Requirements for those actions.
- Reasons an action is unavailable.

An action should be described in terms such as:
- **Available:** prerequisites met.
- **Available with warnings:** operation is possible but a caveat must be acknowledged.
- **Inspection only:** display is supported but quantitative comparison is not.
- **Needs configuration:** user must select units/columns/range.
- **Unsupported:** the provider or calculation is not implemented.
- **Blocked:** validation or compatibility requirements fail.

Examples:
- A catalogue entry with no implemented download route: searchable metadata, not a downloadable spectrum.
- A molecular cross section: inspectable as a reference product, not automatically equivalent to a planet's observed transit depth.
- A local text file with unknown axis units: previewable, but quantitative comparison remains blocked until semantics are established.
- A simulated model spectrum: can be displayed as a model, not labelled as an observation.
- Two arrays with equal lengths but different axis values: not automatically aligned or comparable.

Do not build a single universal “Compare” button until the supported comparison modes and prerequisites are defined.

---

## 12. Feature inventory and traceability system

Before detailed implementation, build four working documents.

### A. Capability inventory
For every current or proposed feature record:
- Name and user goal.
- Current status label.
- Entry point in the UI.
- Underlying service/model/provider.
- Input/output and units.
- Supported formats/products.
- Persistence/cache behavior.
- Progress/cancel/error behavior.
- Known limitations.
- Tests/evidence.
- Owner/next action.

### B. Workspace map
A page/route map with navigation, parent/child screens, entry/exit paths, and context rules.

### C. Interaction-state matrix
For each feature, document states such as:
- Empty.
- Loading.
- Valid selection.
- Invalid input.
- Running.
- Cancellation requested/cancelled.
- Success.
- Partial success.
- Network failure.
- Parser failure.
- Cached/offline.
- Unsupported.
- Stale data.
- Recovery/default state.

### D. Requirement-to-test traceability matrix
Each requirement should map to:
- Design artifact/wireframe.
- Relevant widget/service/model.
- Test or manual verification.
- Documentation.
- Acceptance status.

This prevents visually polished prototypes from omitting small but critical functions such as refresh, cancellation, retry, offline cache behavior, export, or error explanations.

---

## 13. Recommended visual and interaction system

Build a compact design system before polishing individual screens.

### 13.1 Foundations
- Typography scale with legible defaults and platform scaling.
- Spacing scale.
- Color tokens for background/surface/border/text/selection/warning/error/success.
- Light and dark themes if both are planned.
- Contrast and non-color indicators for statuses.
- Icon style and button hierarchy.
- Consistent focus, hover, disabled, busy, and error states.

### 13.2 Components to design once
- Workspace navigation.
- Search/filter bar.
- Results table and column chooser.
- Dataset/reference list row.
- Metadata inspector.
- Plot toolbar.
- Trace/legend list.
- Empty/loading/error panel.
- Task/progress indicator.
- Warning/eligibility banner.
- Provenance/citation view.
- Import mapping dialog.
- Confirmation dialog for destructive actions.
- Layout/panel menu.
- Export dialog.
- Reusable unit/range editor.

### 13.3 Interaction rules
- A primary button performs one clear action.
- Do not use a disabled button without explaining why.
- Preserve inputs when a request fails.
- Ask for confirmation before discarding meaningful work or deleting cached data.
- Separate “remove from view” from “delete asset.”
- Avoid modal dialogs for routine non-destructive settings.
- Show background activity and offer cancellation where safe.
- Use tooltips for secondary help, not to hide essential scientific meaning.
- Keyboard focus and shortcuts should be predictable.
- Never rely on color alone to communicate validation state.

---

## 14. Roadmap in controlled phases

Treat the phases as gated work packages, not calendar promises. Each phase ends with a review and explicit decision to continue, revise, or stop.

### Phase 0 — Establish the side project and evidence baseline
**Goal:** make the work independent and auditable.

Tasks:
- Choose branch/worktree or separate prototype repository.
- Record base commit, date, Python/Qt versions, and dependencies.
- Read current project-state, decisions, architecture, and repository-specific instructions.
- Create a change log and a place for screenshots/wireframes.
- Capture current screenshots of each important existing workflow.
- Label claims as verified/reported/proposed/unverified.
- Avoid implementation changes in mainline.

Deliverables:
- Side-project README.
- Baseline snapshot and dependency list.
- Initial risk register.
- Initial feature inventory.

Gate: user can explain where the prototype lives, what commit it was based on, and how it stays separate from main development.

### Phase 1 — Audit current capabilities and user journeys
**Goal:** know what exists before designing replacements.

Tasks:
- Inspect every workspace and menu/action.
- Trace each visible control to code/service/test.
- List every supported import format and its actual schema assumptions.
- Trace provider search, download, cache, refresh, and offline paths.
- Trace project persistence and source provenance.
- Inventory plots and their scientific inputs/outputs.
- Recheck the original transit panel separately.
- Record duplicate/redundant screens and controls.
- Gather screenshots and note friction points.

Deliverables:
- Capability inventory.
- Current navigation map.
- Current workflow diagrams.
- Evidence list for each major feature.
- “Do not break” list.

Gate: no major existing workflow is omitted from the redesign plan, and unsupported behavior is explicitly listed.

### Phase 2 — Requirements and product decisions
**Goal:** turn wishlist ideas into testable requirements.

Tasks:
- Prioritize primary user personas/tasks (at minimum, researcher importing own data, researcher searching archive data, researcher inspecting molecular references).
- Decide Scratch vs Project lifecycle.
- Decide the purpose of Home/Overview.
- Define the first supported data types and scientific compatibility rules.
- Define which operations must be available offline.
- Decide what must autosave and what requires explicit save.
- Define core accessibility/resizing constraints.
- Separate MVP from future wishlist.

Deliverables:
- Product requirements brief.
- Decision log.
- Requirements-to-test matrix.
- Explicit deferred-feature list.

Gate: each proposed first-release feature has a user goal, status, prerequisites, and acceptance criteria.

### Phase 3 — Information architecture and low-fidelity wireframes
**Goal:** test workflow structure without getting distracted by colors.

Tasks:
- Draw global shell and navigation.
- Wireframe Search, Projects, Data, Molecular References, Analysis, Settings, and optional Home.
- Wireframe empty/loading/error/success/unsupported states.
- Draw the scratch-to-project promotion flow.
- Draw import preview and validation.
- Draw molecular retrieval and cache reopening.
- Draw Analysis with plot focus, trace list, and inspector.
- Draw Transit Analysis as a separate advanced workflow.
- Test layout alternatives for dense tables and plots.

Deliverables:
- Workspace map.
- Low-fidelity wireframes.
- Clickable or annotated flow.
- Usability questions to resolve.

Gate: users can explain how to complete the core tasks without needing the visual design to carry the workflow.

### Phase 4 — Visual design system and interaction patterns
**Goal:** establish consistent look and behavior.

Tasks:
- Choose typography, spacing, status colors, icon treatment, and theme rules.
- Design core components.
- Define panel resize/hide/dock behavior.
- Define table density and metadata inspector rules.
- Define plot conventions and scientific labels.
- Define keyboard and accessibility behavior.
- Design confirmation, warning, and failure patterns.

Deliverables:
- Design tokens/style guide.
- Component catalogue.
- Interaction-state patterns.
- Example polished screens.

Gate: common controls behave consistently across workspaces.

### Phase 5 — Standalone interactive prototype
**Goal:** demonstrate flows before integrating into ECAS_BETA.

Tasks:
- Use synthetic, clearly labelled sample data.
- Simulate search results with capability states.
- Demonstrate import validation without writing to production storage.
- Demonstrate molecular reference support/unsupported/cached states.
- Demonstrate scratch/project context switching.
- Demonstrate plot and trace controls.
- Demonstrate panel resize/hide/reset and saved layout.
- Simulate long-running tasks and errors.
- Keep adapters/mock data separated from domain logic.

Deliverables:
- Runnable prototype.
- Prototype README and known limitations.
- Task walkthroughs.
- Feedback log.

Gate: core workflows can be exercised end-to-end; prototype does not claim real provider or scientific computation where only mock behavior exists.

### Phase 6 — Architecture mapping and integration spike
**Goal:** determine what can be reused and what must change.

Tasks:
- Map each prototype component to current Qt widgets, services, models, and persistence.
- Compare old transit logic with current domain models.
- Identify reusable calculations and test coverage.
- Identify API adapters required for friend/agent changes.
- Define versioned DTOs and persistence boundaries.
- Make one narrow vertical integration spike, preferably a low-risk workspace or reusable plot/inspector.
- Add tests around the adapter.

Deliverables:
- Integration map.
- Architecture decision record.
- Dependency and risk report.
- Demonstrated vertical slice.

Gate: integration is based on real code and tests, not assumptions from mockups.

### Phase 7 — Incremental production integration
**Goal:** integrate one coherent slice at a time.

Suggested order:
1. Global shell/navigation and layout recovery.
2. Reusable table, inspector, and status components.
3. Data workspace and import preview.
4. Project asset list and context switching.
5. Search result capability/metadata improvements.
6. Molecular reference inspector and retrieval-state clarity.
7. Core Analysis plot/trace workflow.
8. Saved layout preferences and scratch-session recovery.
9. Advanced linked time-series/transit experience.
10. Additional diagnostics and analysis tools only when validated.

For each slice:
- PLAN-only repository investigation.
- Review plan and verify scope.
- ACT only the approved slice.
- Inspect diff.
- Run focused tests and relevant regression suite.
- Test normal GUI behavior, not only offscreen tests.
- Update authoritative documentation and feature status.
- Record unresolved limitations.

Gate: no next slice until acceptance criteria and regression checks pass.

### Phase 8 — Scientific validation, usability, and hardening
**Goal:** validate correctness and practical usability.

Tasks:
- Test known sample datasets with documented expected behavior.
- Test unit and axis compatibility.
- Test missing/invalid data and uncertain provenance.
- Test cache freshness/offline recovery.
- Test large files and responsive behavior.
- Test long names, multiple projects, and many traces.
- Test layout restoration after a panel is renamed/removed.
- Test keyboard-only workflows and scaling.
- Run user walkthroughs against core scenarios.
- Verify plot exports and result metadata.

Deliverables:
- Test report.
- Known limitations.
- Usability issues ranked by severity.
- Release-readiness checklist.

Gate: no claim of scientific validity without an appropriate method and evidence; no claim of UI completeness while essential states remain unhandled.

### Phase 9 — Integration release and maintenance
**Goal:** make the redesigned UI maintainable amid ongoing mainline development.

Tasks:
- Compare side-project base with latest mainline.
- Port in small PRs.
- Document compatibility shims and removal plans.
- Run regression tests on the integration branch.
- Review new upstream features for fit with the capability inventory.
- Keep design documents updated when product decisions change.
- Remove temporary duplicate code only after equivalence is verified.

Deliverables:
- Reviewable PR series.
- Updated project state/decisions.
- Migration and rollback notes.
- Post-integration issue list.

---

## 15. Suggested chunking and work-item template

Use chunks small enough to plan, implement, and verify independently. A chunk should not simultaneously redesign navigation, replace the data model, add a provider, and rewrite analysis logic.

Suggested first chunks:
- **UI-00:** establish isolated side project and baseline.
- **UI-01:** current feature inventory and evidence map.
- **UI-02:** core user journeys and state matrix.
- **UI-03:** global navigation and workspace map.
- **UI-04:** low-fidelity Data and Projects wireframes.
- **UI-05:** Search and Molecular References wireframes.
- **UI-06:** Analysis and Transit Analysis wireframes.
- **UI-07:** visual system and reusable components.
- **UI-08:** standalone prototype shell and navigation.
- **UI-09:** import/validation prototype flow.
- **UI-10:** project/scratch context and promotion.
- **UI-11:** molecular reference capability states.
- **UI-12:** plotting and inspector prototype.
- **UI-13:** customizable layouts and recovery.
- **UI-14:** integration architecture spike.
- **UI-15+:** small production integration slices.

For every work item record:
- ID/title.
- Objective.
- Status and priority.
- Dependencies.
- In-scope files/components.
- Explicit out-of-scope items.
- Existing evidence to inspect.
- Acceptance criteria.
- Verification steps.
- Documentation to update.
- Risks/unknowns.
- Outcome and follow-up.

### Example prompt/workflow shape for future Cline use

**PLAN prompt:** inspect current repository and relevant docs; identify actual files/services/tests; compare them with the approved work item; propose the smallest viable change; list risks, unknowns, acceptance criteria, and tests; do not edit files.

**Review:** check for scope creep, duplicated models, scientific assumptions, unsupported formats, persistence impact, and missing states.

**ACT prompt:** implement only the approved plan; preserve unrelated changes; run the exact tests; report commands and actual outputs; inspect the diff; update only relevant docs; stop on blockers rather than inventing behavior.

Because the side project is intended to remain independent, explicitly instruct agents to preserve uncommitted work and not reset, force-push, or merge mainline changes without authorization.

---

## 16. Verification strategy

### 16.1 Layers of verification
1. **Static review:** imports, type/schema consistency, dependency direction.
2. **Unit tests:** parsers, model mapping, eligibility rules, layout settings serialization.
3. **Service tests:** search/retrieval/cache/persistence adapters with mocked network boundaries.
4. **UI tests:** state transitions, buttons, panel recovery, validation messaging.
5. **Integration tests:** project persistence and source/result linkage.
6. **Manual GUI checks:** normal desktop rendering, resize behavior, fonts, docking, plotting interaction.
7. **Scientific checks:** known input/output examples, units, uncertainty propagation, compatibility constraints.
8. **Usability checks:** task completion, discoverability, error recovery.

Offscreen UI tests are useful but do not replace normal GUI inspection, especially for fonts, native docking, graphics rendering, and platform scaling.

### 16.2 Essential regression scenarios
- Start with no data or project.
- Import a valid file.
- Import malformed/ambiguous text.
- Import FTIR-style wavenumber data and UV-Vis-style wavelength data without assuming they are interchangeable.
- Open a project and inspect an attached dataset.
- Start scratch analysis and promote an item to a project.
- Search an unsupported molecular entry.
- Retrieve a supported reference, then reopen it offline.
- Cancel a long-running operation.
- Recover after a provider failure.
- Hide all optional panels and restore defaults.
- Reopen after changing workspace layout.
- Load long names and a large result set.
- Remove a panel in a new version and load old saved layout.
- Export plot and data with correct labels/units/provenance.
- Confirm that display-only preferences do not mutate underlying data or results.

### 16.3 Evidence discipline
For each check, record command, environment, test count/result, and known limitations. Distinguish:
- Test not run.
- Test blocked by environment.
- Test failed.
- Test passed.
- Manually inspected.
- Reported by another agent but not independently verified.

---

## 17. Risks and mitigations

| Risk | Why it matters | Mitigation |
|---|---|---|
| Upstream changes collide with redesign | Friend/agent work may change files or interfaces | Isolated branch/worktree, small integration slices, adapter contracts |
| Duplicate domain models | Causes incompatible data representations | Audit current models first; reuse/adapt through explicit adapters |
| UI overpromises capability | Misleads users about download/analysis support | Capability inventory and explicit status model |
| Scientific types are conflated | Can produce invalid comparisons | Typed inputs, units, provenance, eligibility checks |
| Too much customization | Users can lose critical controls or layouts | Guardrails, reset, persistent navigation, staged docking |
| Project and scratch states blur | Data loss or unclear persistence | Separate lifecycle and storage contracts |
| Large datasets freeze UI | Poor experience and possible app hangs | Efficient model/view, background tasks, progressive loading |
| Cache becomes stale or opaque | Reproducibility suffers | Provenance, version/freshness status, explicit offline behavior |
| Prototype diverges from production | Later integration becomes expensive | Periodic API review and one narrow integration spike |
| Overbuilding before validating workflows | Wasted implementation | Wireframes, task walkthroughs, gated phases |
| Test success is overstated | False confidence | Capture actual commands/output and GUI checks |
| Old transit code is transplanted uncritically | Hidden assumptions/dependency issues | Separate scientific audit and test-backed reuse |
| Layout restore breaks after upgrades | Users lose workspace access | Versioned state, unknown-panel handling, safe default |
| External data formats are overgeneralized | Misinterpreted units/axes | Preview, explicit mappings, schema-specific parsers |

---

## 18. Prioritized wishlist

### Tier 0 — Foundation / must decide before broad implementation
- Capability inventory with evidence.
- Global navigation and workspace map.
- Scratch vs Project lifecycle.
- Clear separation of source assets, registered datasets, derived products, project membership, and analysis results.
- Scientific type/units/provenance and eligibility rules.
- Error/unsupported/cached/running state patterns.
- Side-project branch/worktree and integration protocol.
- Restore-default-layout and protection from data loss.

### Tier 1 — First practical UX improvements
- Human-readable data labels and metadata inspector.
- Import preview and explicit column/unit mapping.
- Search result availability/capability indicators.
- Better table density, column chooser, sorting/filtering.
- Large plot area with trace list and axis controls.
- Clear molecular reference metadata and retrieval support state.
- Cache status and offline reopening visibility.
- Scratch analysis that can promote work into projects.
- Workspace-specific saved preferences.
- Consistent empty/loading/error/unsupported states.

### Tier 2 — Workflow and visualization improvements
- Dockable/floating panels with reliable recovery.
- Named layout presets.
- Reusable plot/inspector components.
- Data validation diagnostics and import history.
- Plot/data export with provenance.
- Linked views for time-resolved data.
- Project activity/history and reproducibility summary.
- User-friendly provider/source links and citation display.
- Search result filters by instrument, date, range, source, product type.

### Tier 3 — Advanced scientific workflow
- Transit/time-series workspace with synchronized light curve and orbital view.
- Spectrum-at-selected-time view for supported time-resolved spectra.
- Phase-folded, residual, and noise diagnostics when validated.
- Comparison readiness report explaining compatible/incompatible inputs.
- Explicit instrument response, binning, uncertainty, and normalization workflow.
- Reproducible derived-product graph/lineage.
- More molecular providers and product types after each adapter is independently validated.
- Atmospheric forward models or retrieval integrations only after scope and scientific validation.

### Tier 4 — Longer-term ideas
- User-configurable workspace presets and perhaps shareable layout descriptions.
- Plugin/provider extension points.
- Batch processing and queued tasks.
- Multi-observation/instrument comparison workspace.
- Reproducible analysis reports with source citations and parameter summaries.
- Advanced atmospheric model integration (for example, adapter-based access to established libraries) without duplicating their science unnecessarily.
- Optional scripting/notebook export for power users.

A wishlist item is not a commitment. Promote items only when there is a user need, a defined scientific method, a realistic dependency plan, and testable acceptance criteria.

---

## 19. External programs and design references

These projects are useful for learning from established workflows. They are **references, not templates to copy wholesale**, and their capabilities should not be attributed to ECAS.

### 19.1 ExoCTK — Exoplanet Characterization Tool Kit
- Website/docs: https://exoctk.readthedocs.io/
- GitHub: https://github.com/exoctk/exoctk
- Useful for: modular exoplanet characterization tools, transit light-curve fitting, limb-darkening and visibility/contamination tools, instrument/planning workflows.
- Study: how each tool explains inputs, output plots, downloads, and limitations.
- Do not assume its components are drop-in libraries for ECAS; inspect licenses, dependencies, and interface contracts first.

### 19.2 PandExo
- Docs: https://natashabatalha.github.io/PandExo/
- Useful for: planning/simulating JWST and HST exoplanet observations; understanding instrument-specific configuration and outputs.
- Study: parameter grouping, instrument constraints, output dictionaries, and explicit simulation context.
- It is an observation simulator, not a replacement for a generic observational-data browser or atmospheric retrieval workflow.

### 19.3 TauREx 3
- Docs: https://ucl-exoplanets.github.io/taurex3/
- Practical examples: https://ucl-exoplanets.github.io/taurex3/user/practical_examples/index.html
- Useful for: modular atmospheric forward modelling and Bayesian retrieval; examples of configurable scientific components and explicit inputs.
- Study: separation of forward model, chemistry, temperature, opacity, observations, binning, fitting, and output.
- Treat a future integration as a defined adapter and dependency decision, not an immediate requirement.

### 19.4 petitRADTRANS
- Docs: https://petitradtrans.readthedocs.io/
- Retrieval tutorial: https://petitradtrans.readthedocs.io/en/latest/content/notebooks/retrieval_basic.html
- Useful for: atmospheric radiative-transfer and retrieval concepts, model inputs, fitting and scientific interpretation.
- Study: how a model run differs from an observation and how retrieval results are described.
- Do not present its availability as proof that ECAS currently implements atmospheric retrieval.

### 19.5 ExoMol
- Main site: https://exomol.com/
- Data browser: https://exomol.com/data/
- Useful for: molecular line-list discovery, isotopologues, dataset definitions, and provider data products.
- Study the distinction among molecule, isotopologue, dataset, line list, cross section, and other data products. Preserve provider metadata and citations.
- Catalogue presence does not guarantee that ECAS has implemented retrieval for that product.

### 19.6 NASA Exoplanet Archive
- Overview: https://exoplanet.ipac.caltech.edu/docs/intro.html
- API guidance: https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html
- Useful for: planet/host records, literature-linked metadata, archive tables, and query design.
- Study how target identity is separated from data products and how source references are surfaced.
- Keep API/query limitations and archive update behavior explicit.

### 19.7 MAST / JWST archive
- JWST data access: https://archive.stsci.edu/missions-and-data/jwst
- Useful for: observing products and their stages (raw, detector-corrected, calibrated, combined), observation search, instrument/program metadata.
- Study the product hierarchy and file naming. An archive observation, calibrated file, extracted spectrum, and publication table are not interchangeable entities.

### 19.8 Specutils / Astropy
- Specutils: https://specutils.readthedocs.io/en/stable/
- Astropy: https://docs.astropy.org/
- Useful for: spectral data containers, units, uncertainty, spectral regions, resampling, fitting, and FITS/time-series handling.
- Study the unit-aware approach and explicit spectral-axis compatibility. Evaluate whether these abstractions fit ECAS's current models before adding another canonical representation.

### 19.9 Jdaviz / Specviz
- Jdaviz: https://jdaviz.readthedocs.io/
- Useful for: astronomy-oriented visualization workflows, spectrum inspection, linked analysis tools, and inspector-style interfaces.
- Study how plot interactions expose selected points, metadata, tools, and analysis state.

### 19.10 TOPCAT
- Website: https://www.star.bris.ac.uk/~mbt/topcat/
- Useful for: dense astronomical tables, filtering, column selection, cross-matching, and data exploration.
- Study its table-first efficiency and powerful but discoverable controls. ECAS may want a more guided experience, but table-density problems are worth learning from.

### 19.11 Qt for Python / PySide6
- `QMainWindow`: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMainWindow.html
- `QDockWidget`: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QDockWidget.html
- Useful for: window composition, toolbars, status bars, docking, floating panels, and save/restore of layout state.
- Study `saveState()`/`restoreState()`, unique object names, versioning, and recovery. Use saved Qt layout state only for compatible locally generated state; keep scientific analysis state separately versioned and inspectable.

### 19.12 PyQtGraph
- Documentation: https://pyqtgraph.readthedocs.io/
- Useful for: interactive scientific plots in Qt, high-frequency updates, data cursors, linked axes, and large-array visualization.
- Study the current installed version and API before designing plot components around particular features.

### How to use these references efficiently
Do not attempt to study every project completely. For each one, capture:
1. What user task it supports.
2. What its UI does particularly well.
3. Which metadata and assumptions it exposes.
4. What ECAS should learn from it.
5. What ECAS should not copy.
6. Relevant licensing/dependency considerations.
7. A screenshot or small annotated sketch, if useful.

---

## 20. Research reading order

Recommended sequence:
1. **Qt layout and persistence docs** — informs realistic layout customization.
2. **NASA Exoplanet Archive and MAST** — informs target/product/result identity and provenance.
3. **ExoMol data browser** — informs molecular catalogue/product semantics.
4. **Specutils/Astropy** — informs units, axes, uncertainties, and data models.
5. **ExoCTK and PandExo** — informs task-specific exoplanet workflows and instrument planning.
6. **Jdaviz/Specviz and TOPCAT** — informs scientific inspection and table interaction.
7. **TauREx and petitRADTRANS** — informs later atmospheric-model integration, not early UI scaffolding.

Keep a source notes file with date accessed, relevant page, observation, design implication, and confidence. Official documentation should be preferred for API and capability claims; papers should be consulted for scientific method and citations.

---

## 21. Open decisions to settle deliberately

These are not all required immediately. Track them in a decision log.

1. Is the prototype in a separate repository or a same-repo worktree?
2. Is Home useful enough to keep, or should navigation land directly in the last workspace?
3. Which workspace is the default launch destination?
4. What exact state is autosaved for Scratch, and when is explicit save required?
5. Can a scratch session contain any registered dataset, or only a selected subset?
6. What is the minimum metadata required to register a scientific dataset?
7. How are wavelength, wavenumber, frequency, time, and phase represented?
8. What uncertainty formats are supported?
9. What does “compatible for comparison” mean for each supported analysis method?
10. Should all plots use PyQtGraph initially, or are there validated reasons for other renderers?
11. Is 3D orbit visualization a core requirement or optional plugin?
12. Which local file formats are first-class, and which are user-mapped text tables?
13. How should duplicate files be detected and displayed?
14. What is the cache eviction/refresh policy?
15. Which user settings are global, workspace-specific, or project-specific?
16. How should saved layout state migrate when widgets change?
17. What exports are required first: image, CSV, FITS, configuration, or report?
18. What scientific checks are required before enabling a new comparison operation?
19. Which parts of the old transit panel are worth reusing after code audit?
20. Which advanced analyses are explicitly deferred?

Do not block the whole project on every decision. Mark the decisions needed for the current phase and leave the rest open.

---

## 22. First 10 practical actions

This is the recommended immediate sequence.

1. **Create the isolated side-project location.** Record base commit, branch/worktree, Python/Qt versions, and how to run it.
2. **Read the current ECAS_BETA project instructions, project state, decisions, architecture, and latest checkpoint.** Reconcile them with the supplied ZIP/repository before relying on paths.
3. **Capture a current screenshot set** of every major existing workflow and record the exact steps needed to reach each one.
4. **Build the capability inventory.** Every visible action should map to current behavior, a service/model, a test/evidence source, and a status label.
5. **Draw the current navigation map** and identify dead ends, duplicate screens, and hidden controls.
6. **Write the six workflow maps** in Section 6, starting with local import and project reopen.
7. **Create the interaction-state matrix** for import, search, retrieval/cache, plotting, and layout restore.
8. **Produce low-fidelity wireframes** for Data, Projects, Search, Molecular References, and Analysis before choosing colors.
9. **Review the original transit implementation separately** and make a reuse/replace/defer table for its calculations, data structures, 3D view, fallback, and time synchronization.
10. **Build a small clickable or runnable prototype** with mock data and explicit capability states. Do not integrate it into mainline until the workflows and boundaries are accepted.

### Do not do yet
- Do not rewrite all current UI files.
- Do not port the original transit panel wholesale.
- Do not implement every provider or file format.
- Do not add retrieval/atmospheric-analysis features just to fill out a screen.
- Do not make arbitrary panels movable before reset/recovery works.
- Do not infer unknown units from the plot shape.
- Do not merge the prototype into mainline because a mock workflow looks good.

---

## 23. Definition of done for the design stage

The design stage is ready to transition into implementation when:
- Every major current feature is inventoried with evidence and status.
- Primary user journeys are mapped, including failure and recovery paths.
- Scratch and project contexts have clear lifecycle rules.
- The data/reference/result concepts and scientific eligibility boundaries are documented.
- Every workspace has low-fidelity wireframes and at least the important empty/loading/error/unsupported states.
- The visual system and reusable components are specified.
- Layout customization has a staged plan and recovery behavior.
- The prototype demonstrates core flows using clearly labelled mock data.
- Each proposed production feature maps to an existing service, a needed adapter, or an explicitly deferred dependency.
- Integration and regression checks are defined.
- Open questions are recorded rather than silently assumed.

## 24. Definition of done for each implementation slice

A slice is complete only when:
- The scope matches the approved plan.
- The code is integrated through the intended architecture boundary.
- Existing behavior has not regressed.
- Relevant tests ran and actual outputs were recorded.
- Manual GUI checks were completed where visual behavior matters.
- Data units, scientific types, provenance, and unsupported cases remain explicit.
- The diff was inspected for unrelated changes.
- Relevant docs and status records were updated.
- Known limitations and next steps are stated.
- No claim exceeds the available evidence.

---

## 25. Resource links (quick index)

### ECAS
- ECAS_BETA: https://github.com/brettadin/ECAS_BETA
- Original ECAS reference repository: https://github.com/brettadin/ecas
- ECAS_BETA Issue #2 (reported UI/data-discovery concerns): https://github.com/brettadin/ECAS_BETA/issues/2

### UI / plotting
- PySide6 QMainWindow: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMainWindow.html
- PySide6 QDockWidget: https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QDockWidget.html
- PyQtGraph: https://pyqtgraph.readthedocs.io/

### Astronomy data and spectroscopy
- NASA Exoplanet Archive overview: https://exoplanet.ipac.caltech.edu/docs/intro.html
- NASA Exoplanet Archive API: https://exoplanetarchive.ipac.caltech.edu/docs/program_interfaces.html
- MAST JWST: https://archive.stsci.edu/missions-and-data/jwst
- ExoMol: https://exomol.com/
- ExoMol data browser: https://exomol.com/data/
- Astropy: https://docs.astropy.org/
- Specutils: https://specutils.readthedocs.io/en/stable/
- Jdaviz: https://jdaviz.readthedocs.io/

### Exoplanet tools / models
- ExoCTK: https://exoctk.readthedocs.io/
- ExoCTK source: https://github.com/exoctk/exoctk
- PandExo: https://natashabatalha.github.io/PandExo/
- TauREx 3: https://ucl-exoplanets.github.io/taurex3/
- petitRADTRANS: https://petitradtrans.readthedocs.io/
- TOPCAT: https://www.star.bris.ac.uk/~mbt/topcat/

---

## 26. Closing project rule

**Build the evidence map first, the workflow design second, the prototype third, and the production integration last.** Keep the side project isolated, the scientific meaning explicit, the layout recoverable, and each change small enough to verify. That is the most reliable way to make substantial progress without becoming blocked by concurrent development or accidentally turning an aspirational design into claims about the current application.
