** This is the first document related to the brainstorming process for the UI redesign. This is to keep a record of ideas as I work. **


# ECAS UI strategy: from the current application to a flexible scientific workspace

The best approach is to design ECAS around the scientific tasks a user wants to perform, rather than giving every existing function its own crowded screen.

ECAS needs to support several different kinds of work:

- Finding exoplanets and locating observational data.
- Managing research projects and preserving data provenance.
- Finding, retrieving, and organizing molecular reference spectra.
- Inspecting and plotting spectral data.
- Eventually comparing observations against molecular references and investigating possible atmospheric constituents.
- Importing local data, exploring it, and making it available to projects without losing the original files or their metadata.

Those tasks overlap, but they do not all need the same interface. A search workflow benefits from compact results and filters. A spectral-analysis workflow needs plots, legends, data selection, and controls. A project-management workflow needs clear organization and provenance. A reference-retrieval workflow needs dataset details, physical conditions, download status, and cache information.

My recommendation is a task-oriented, modular interface with a consistent global structure, dedicated scientific workspaces, and user-configurable panels inside those workspaces. The design should be flexible enough to accommodate features that have not been implemented yet, without requiring a complete redesign every time a new function is added.

This should be an independent UI-design effort. It can produce a visual and interaction specification that another AI or developer can implement incrementally as the underlying functionality becomes available.

## 1. What the current application needs to accommodate

Based on the repository checkpoint and your Issue #2 report, this is the current functional picture. The distinction between implemented, partially supported, and planned matters: the UI should not present a future capability as though it already works.

Current capabilities and limitations described in the available repository documentation and your user-verification report.

| Area                          | Current state                                                                                          | Main UI requirement                                                     |
| ----------------------------- | ------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| Exoplanet search              | Improved NASA-based search and name resolution                                                         | Search, filter, inspect results, and show clear empty states            |
| Observational spectra         | Import/display workflow with existing spectrum graph                                                   | Plot data clearly and expose relevant metadata                          |
| Research projects             | Create, select, attach, reopen, and persist spectra                                                    | Identify datasets, show provenance, and manage project contents         |
| Molecular reference catalogue | Searchable molecular and isotopologue records                                                          | Compact search results with useful dataset metadata                     |
| Reference retrieval           | Verified initial CO₂ / UCL-4000 workflow and caching                                                   | Settings, progress, validation errors, provenance, and cache status     |
| Spectral comparison           | Research prototypes and eligibility/method groundwork, but no completed production comparison workflow | Design a dedicated workspace without pretending analysis already exists |
| Overview                      | Purpose not yet established                                                                            | Define its role after the main workflows are mapped                     |
| Settings                      | Not yet meaningfully developed as a global settings area                                               | Build only the settings that have real behavior                         |

This table should become the starting point of a UI capability inventory. Before designing screens, every existing function needs to be accounted for, including functions that are currently hidden behind buttons, dialogs, menus, or background services.

I would not begin by redesigning individual tabs in isolation. First, map the whole application.

## 2. Proposed application structure

I would organize ECAS into a persistent application shell, a set of scientific workspaces, and a contextual inspector.

## ECAS

Project: WASP-39 b

Search

Projects

Data

References

Analysis

Main workspace

Search results, project contents, reference catalogue, or analysis layout, depending on the selected workspace.

Context inspector

Details, metadata, selected-item actions, validation messages, and relevant settings.

Persistent status area: background tasks, import/retrieval status, and actionable errors

Conceptual layout only, not a representation of the current UI or a final visual design.

### A. Global application bar

Keep the top bar relatively small. It should contain things that are useful across most workspaces:

- ECAS identity and a way to return to the main workspace.
- Current project selector, where a project is relevant.
- Global settings.
- A small status indicator for background tasks.
- Possibly a universal search entry point later, if search across planets, datasets, molecules, and projects becomes practical.

Avoid putting every scientific action in this bar. A global toolbar that contains Import, Download, Plot, Fit, Compare, Export, Refresh, and Settings would become crowded and contextually confusing.

The primary action should change with the active workspace. For example, `Import data` makes sense in Data, while `Download reference` belongs in Molecular References.

### B. Primary navigation

I recommend five main workspaces as the long-term target:

1\. Search

Find exoplanets and available observational records. This is where the current exoplanet-search function belongs. Selecting a result should reveal its details and available actions, including adding eligible records to a project.

2\. Projects

Create and select projects, organize observations and references, inspect provenance, and reopen saved data. A project should act as the organizing context for research, not as a separate copy of every scientific tool.

3\. Data

Import local files, validate them, inspect columns and units, preview spectra, and manage reusable datasets. This is a natural home for the local-file workflow you anticipate.

4\. Molecular References

Search molecular records, inspect isotopologues and source information, download supported reference products, and manage cached references. This gives the current catalogue a clear, focused purpose.

5\. Analysis

Plot and compare selected datasets, inspect regions of interest, and eventually evaluate candidate molecular contributions. This is the future home for the broader comparison workflow—not a place to put every existing graph.

This is a proposed target, not a recommendation to create five new tabs immediately. Existing screens can be mapped into these roles gradually. If the current application uses a different number of navigation items, preserve the working functions and migrate them in controlled steps.

### C. Context inspector instead of permanent detail panels

A reusable inspector can reduce clutter across several workspaces.

When a user selects a planet, dataset, molecular reference, or project attachment, the inspector displays relevant details and actions. Its content changes with the selection.

For example:

- A planet: name, identifiers, stellar/planetary metadata, available records.
- An observational dataset: author, instrument, observable, wavelength range, units, source and import details.
- A molecular reference: species, isotopologue, dataset identity, spectral range, units, temperature, pressure/broadening assumptions, and source.
- A project attachment: where it came from, what is stored, validation status, and available actions.

Keep the initial inspector concise. More detailed provenance, raw metadata, and technical diagnostics can be expandable sections rather than permanently visible blocks.

## 3. Graphs: where they belong and how prominent they should be

Your point about having only one graph in the exoplanet-search area is important. Graphing should be a capability that appears wherever it supports a scientific task, not a feature confined to one screen.

However, different graphs have different jobs. ECAS should not reuse the same large spectrum graph indiscriminately.

[JWST finds a heavy atmosphere on a mini-Neptune orbiting a hot Jupiter - AOL](https://images.openai.com/static-rsc-4/Wjon8RwBEHqORGrTTHBcOhPE250A4va9l6x8SX_CrNd4WycUW9DdgnMDoHsTPvejZj77pv7yBhtGVfVgBzicjItg3zBK0HDOTPP3e-gpy_m6B_Yq5S_eV1Tr8xUPyVCKYE-7VYuRf5F2IHCc_ySlw9WuHZCnZzqZRmnu7iLeR4w?purpose=inline)

Search — small preview or optional plot

A selected observational record can have a small spectrum preview where the source provides usable spectral data. Search itself should prioritize finding records, not become a full analysis screen.

Full plotting should be one click away.

[R-branch and P-branch of CO — ExoJAX 2.5.0 documentation](https://images.openai.com/static-rsc-4/rip10Zvb_CpJ1EGrmor0M32xl6fI8albUJnfPR4aotGNu3UjpW3SZnr0N7Yc9k_DxYAUbtqXnizrn1SGZI3W9k04dVzXPUEu5uqstgVL578DPouuQjDSMGuWQLRKRjAbsT-TG9DWLFcO3LeTj1UY0rT2wsq4wFBZ_118P7zEQP0?purpose=inline)

Molecular References — reference spectrum preview

Give the selected molecular reference a clear preview and summary statistics, with dataset conditions and units visible. A reference table can be available alongside it, but should not overwhelm the plot by default.

[Using plot_multiple to plot several datasets on the same figure — SpectroChemPy v0.8.2.dev37 0.8.2.dev37 documentation](https://images.openai.com/static-rsc-4/faytdFItrbMZ97KQWA3KhTLEbV1A04Seatui3o2owvPuYaH3SFr4hqvxOdMm3WtXGdAsCatbi7-OhbWAP-7ofrF45JTh6yMt4AV3AX_3I92DlIfQncbk6yXiusYnigUn24F0oq3LPu1RXyMGRtAL83t1TQcxs-8hAdeJxQsByvE?purpose=inline)

Data — inspect an imported spectrum

Provide a large plot for the selected dataset, with axis selection, units, range controls, and a compact metadata summary. This is useful even before any comparison functionality exists.

[A long-duration gamma-ray burst of dynamical origin from the nucleus of an ancient galaxy | Nature Astronomy](https://images.openai.com/static-rsc-4/7F-u9eLIIURi7wvBQhMBMYJSQoXQL8_Zn9Fyg_6m91-VN1CwaMMZP8_Chv8ymMax2TWy1-ZBHGQwdkelB4i71EHteWHZR_a2bMFhOiPmOmhSsrW87xDK9eYePku6Px_oVTixwHaIYA_YrOOr6MdBdzl1Qx-N0_f2xoOeL0818yM?purpose=inline)

Analysis — primary plotting workspace

This should receive the greatest emphasis on graphing. It needs a large plot, a dataset/trace list, clear legends, selection controls, and eventually optional residual or diagnostic plots where a validated analysis method supports them.

### What should be plotted?

| Location             | Appropriate visual focus                                                                             |
| -------------------- | ---------------------------------------------------------------------------------------------------- |
| Search               | Optional selected-record preview; discovery results remain primary                                   |
| Projects             | Small thumbnails or a preview of the selected project spectrum; not a permanent multi-plot dashboard |
| Data                 | A large, interactive plot for inspecting one dataset at a time                                       |
| Molecular References | A reference-spectrum plot and its relevant conditions                                                |
| Analysis             | Multiple selected traces, comparisons, and supported diagnostics                                     |
| Overview             | Small status summaries or recent-project information; avoid duplicating the analysis screen          |

A future Analysis workspace should support multiple traces with stable, distinct labels and colors. It should also allow a user to hide or show individual traces without deleting the underlying data.

### Avoid misleading comparisons

A visually appealing overlay can still be scientifically wrong. ECAS must distinguish data such as transit depth, flux, absorbance, and molecular cross section, and make units and axis meanings explicit.

For example, a calculated molecular cross section is not directly interchangeable with an observed transmission spectrum. A plot may be useful for inspection, but any scientifically meaningful comparison must be governed by appropriate compatibility rules and, where necessary, a physical model.

The UI should clearly distinguish:

- Inspection: viewing the data as supplied.
- Overlay: displaying compatible axes or explicitly normalized traces together.
- Analysis: applying a defined method with documented assumptions.

Those should not be presented as interchangeable actions.

## 4. How much information should the UI show?

The default should be the minimum information needed to make the next decision, with deeper detail available on demand.

That means different display rules for search results, molecular records, datasets, and numerical tables.

### Search results: concise rows, detailed inspector

A search result should help answer three questions:

1. Is this the item I am looking for?
2. Is it relevant to my current task?
3. What can I do with it?

For exoplanets, a compact row might show:

- Planet name and alternate identifier, where useful.
- Host star.
- One or two key discovery or physical properties when available and relevant.
- Number or type of available observational records.
- A clear indication when no matching records are found.

For molecular references, a row might show:

- Molecule and isotopologue.
- Dataset or calculation identifier.
- Spectral coverage.
- Product type and units, when established.
- Retrieval availability.

Avoid putting long descriptions, raw metadata, citation blocks, or every available field directly into each row. Put those in the inspector.

### Molecular information: concise by default, complete on demand

The current catalogue can produce multiple records for the same molecular formula. That is a good reason to separate species identity from dataset identity.

A useful design would have:

- A compact list of records.
- A detail inspector for the selected record.
- Expandable source and technical metadata.
- A clearly enabled or disabled retrieval action.
- A short, specific explanation when retrieval is unsupported.

Do not hide scientifically essential metadata merely to make the interface cleaner. The default summary should still make it clear what is being retrieved and under which conditions.

### Tables: small by default, configurable when needed

Numerical spectra can contain thousands of points and several metadata fields. A table should not automatically attempt to show every column at full width.

I recommend:

- A compact default set of scientifically useful columns.
- A column chooser.
- Column sorting and filtering where meaningful.
- Horizontal scrolling for wide tables.
- Row virtualization or pagination for large datasets.
- A separate way to inspect a single row in full.
- Copy/export options that preserve the selected data and its units.

The full underlying dataset must remain intact even when columns are hidden from view.

A useful distinction is that display preferences must never silently change the data used for analysis or export. Hiding a column is not the same as removing it from a dataset.

### Metadata should be progressive, not missing

Use three levels of information:

1. Summary: identity, a few relevant properties, availability and status.
2. Details: units, instrument, publication, source, physical conditions and other fields relevant to the selected item.
3. Technical details: full metadata, validation results, provenance, cache information and diagnostic messages.

This pattern works across all the major workspaces and avoids making each feature invent its own disclosure system.

## 5. Should users be able to resize, rearrange, and customize panels?

Yes—but I would introduce customization in stages rather than starting with a completely free-form interface.

A scientific application benefits from customization because different users have different needs. Someone inspecting one spectrum might want a large graph and a small metadata panel. Someone debugging a dataset might want the data table and metadata side by side. Someone comparing many traces might need more room for the legend and trace list.

The challenge is providing that flexibility without making ECAS difficult to use or maintain.

### Recommended customization levels

Level 1 — Basic preferences

Let users change table columns, sort order, panel visibility, plot settings, and a few useful display options. Save preferences automatically.

This should come first because it is relatively simple and helps immediately.

Level 2 — Resizable and collapsible panels

Allow users to drag splitters between supported panels, collapse sidebars, and adjust the balance between plots and tables.

Save those sizes per workspace so a large Analysis layout does not force Search to look the same way.

Level 3 — Saved layouts and movable panels

Let users rearrange approved panels within specific workspaces, save named layouts, and restore defaults. A user could maintain a `Spectrum inspection` layout and a `Comparison` layout without rebuilding either each time.

### Why not unrestricted drag-and-drop everywhere?

Completely free-form UI placement creates real maintenance costs:

- Panels can become too small to use.
- Essential controls can become hidden.
- Different window sizes can produce broken layouts.
- Future UI changes may invalidate saved arrangements.
- Developers must test many more possible configurations.

I would therefore allow rearrangement within defined workspace layouts, not arbitrary placement of any control anywhere in the application.

For example, the Analysis workspace might have a plot, trace list, data table, and inspector that can be rearranged within supported boundaries. The application’s main navigation and critical status indicators would remain fixed.

### What should be saved?

Save interface preferences separately from scientific project data.

| User preference                   | Recommended scope                           |
| --------------------------------- | ------------------------------------------- |
| Window size and position          | Application                                 |
| Selected workspace                | Application, optionally restored at startup |
| Panel sizes and visibility        | Per workspace                               |
| Table column visibility and order | Per table or workspace                      |
| Plot appearance and axis defaults | Per workspace or plot type                  |
| Named layouts                     | Per user                                    |
| Current project and its data      | Project state, not merely UI preferences    |

If a user saves a layout and ECAS later removes or renames a panel, the application should ignore the obsolete layout entry and restore a usable default rather than failing to open the workspace.

A `Reset layout` action is essential.

## 6. Should there be global toolbars and a Settings area?

Yes, but they should have clearly separated responsibilities.

### Global controls versus contextual controls

| Global application controls    | Workspace-specific controls              |
| ------------------------------ | ---------------------------------------- |
| Application settings           | Search filters                           |
| Theme and display preferences  | Dataset import options                   |
| Layout and reset preferences   | Molecular retrieval parameters           |
| General background-task status | Plot axes and trace visibility           |
| Application-level diagnostics  | Analysis method and eligibility controls |

A universal toolbar should not become a dumping ground for every operation.

Use a small global bar, contextual action bars within workspaces, and menus for infrequent or advanced actions.

### Settings should be organized by purpose

I would eventually use a Settings dialog or dedicated settings view with a few categories:

- Appearance and layout: theme, font/display options where supported, panel behavior, saved layouts.
- Data handling: import defaults, supported formats, cache location and retention controls where appropriate.
- Scientific display: default axis behavior, unit display, and plotting preferences.
- Network and retrieval: relevant timeouts, provider behavior, and cache controls where those are genuinely configurable.
- Diagnostics: application version, environment information, and relevant logs for troubleshooting.

Do not add settings that have no implementation behind them. In particular, avoid presenting a UI control that appears to change scientific behavior when the underlying service ignores it.

Every setting should have a defined owner, a persisted value if applicable, and a clear effect on the application.

## 7. Where should local data import go?

I would make Data the dedicated home for importing, validating, and inspecting local files.

That gives the workflow a natural order:

1\. Import

Select local files and identify their formats.

2\. Validate and preview

Inspect columns, units, axes, missing values, and format compatibility. Ask for user mapping only when necessary.

3\. Register the dataset

Preserve the original bytes and record provenance, validation information, and any parsed representation.

4\. Inspect and plot

Preview the dataset, select usable columns, and check whether the data is suitable for a particular scientific task.

5\. Add to a project

Attach the registered dataset to the current project without losing its source identity or provenance.

This is a proposed workflow, not a claim that every stage exists today.

### Import support must be scientifically aware

You have already noted that some of your previous research data is FTIR-oriented, while UV-Vis data may arrive in text files rather than standardized CSVs. That means ECAS should not assume that all useful data is a CSV with the same two columns.

The importer should distinguish at least:

- File format and encoding.
- Data columns and their roles.
- Wavelength versus wavenumber axes.
- Axis and signal units.
- Observable type, where known.
- Instrument and experimental conditions, where supplied.
- Whether the data can be plotted, compared, or only stored pending further interpretation.

An import should not silently reinterpret an unknown axis or signal. When ECAS cannot determine what a column means, it should ask the user or retain it as unknown.

### How caching should work

Caching needs a deliberate data lifecycle.

- Original source: preserve the uploaded bytes and their identity.
- Parsed representation: store a validated representation for efficient reopening, with a link to the original.
- Metadata and provenance: record where the data came from, how it was imported, and which transformations have been applied.
- Derived data: record the parent dataset and processing method so that derived data is traceable.
- Project membership: link the dataset to projects instead of unnecessarily duplicating the source every time it is attached.

The exact storage model should reuse ECAS’s existing project and persistence services wherever possible. The UI design must not assume that a new cache database or a new project storage system is required.

A useful principle is: the data registry owns dataset identity; projects organize research around datasets; workspaces display and operate on them.

That separation makes it much easier to add a new import format or a new scientific workspace later.

## 8. How to design for features that do not exist yet

This is the most important requirement if you intend to work on the UI independently while other development continues.

The interface should be designed around stable concepts and contracts, not the exact set of buttons currently implemented.

For example, a future local-data importer should be able to register a dataset that the project system can reference and the Analysis workspace can display. The importer should not need to know how every graph is drawn. Similarly, adding another molecular-data provider should not require rebuilding the whole Molecular References screen.

### Use a shared dataset concept

At a conceptual level, ECAS needs to distinguish these objects:

| Object                 | Purpose                                                    |
| ---------------------- | ---------------------------------------------------------- |
| Planet                 | Identifies the astronomical target                         |
| Observational dataset  | Holds an observed spectrum and its source information      |
| Molecular reference    | Holds a reference product and its scientific conditions    |
| Project                | Groups related research assets and records                 |
| Derived dataset        | Represents a transformed or processed dataset with lineage |
| Analysis configuration | Records selected inputs and analysis settings              |
| Analysis result        | Holds output and its method, parameters, and provenance    |

These are conceptual distinctions, not instructions to create six new database tables. The existing code may already represent some of them, or use different names. The implementation should be inspected before any model changes are proposed.

The UI should be able to show an object's identity, status, metadata, available actions, and relationships to other objects without knowing all the details of its underlying provider.

### Use capability-aware actions

Not every dataset supports every operation.

For example:

- A catalogue entry might be searchable but not downloadable.
- A local file might be storable and plottable but not scientifically comparable yet.
- A molecular reference might be downloadable and viewable but not eligible for a particular comparison method.
- An analysis result might be viewable but not reproducible if a required source or dependency is unavailable.

The UI should reflect these capabilities. A button should be enabled only when the action is supported and its prerequisites are satisfied. Otherwise, explain what is missing.

This is much better than building screens that assume every item supports every operation and then discovering that half the controls do nothing.

### Define the UI contract for each feature

Every new capability should answer the same questions before its UI is finalized:

1. What object does the feature consume?
2. What object or result does it produce?
3. What information must be displayed?
4. What operations are supported?
5. What prerequisites or eligibility conditions apply?
6. What errors and progress states can occur?
7. What is cached or persisted?
8. How can a user tell whether the operation succeeded?
9. How does the feature connect to a project?
10. What happens when the underlying capability is unavailable?

That contract becomes the bridge between UI work and future backend implementation.

## 9. How to ensure nothing gets forgotten

I recommend maintaining four linked documents as part of the UI effort.

### A. UI capability inventory

List every existing and planned function, where it lives, and its implementation status.

Include small things, not just the obvious features: export, refresh, cancellation, empty states, source links, cache reopening, validation messages, and error recovery.

### B. Workspace and navigation map

For every workspace, record:

- Its purpose.
- The primary task users perform there.
- Its primary data objects.
- The main graph or table, if any.
- Its contextual controls.
- Its inspector content.
- Where its actions lead next.
- Which other workspaces it depends on.

### C. Interaction and state matrix

For every major action, define the expected behavior across the full lifecycle.

| State                      | Example: molecular reference retrieval                                  |
| -------------------------- | ----------------------------------------------------------------------- |
| Idle                       | Dataset selected; retrieval action available if supported               |
| Invalid selection/settings | Explain the exact issue and how to correct it                           |
| Running                    | Show progress and offer cancellation where supported                    |
| Success                    | Show validated data and its metadata                                    |
| Failure                    | Explain the failure without destroying the previous valid reference     |
| Cached                     | Allow reopening the saved reference                                     |
| Unsupported                | Explain that the catalogue record exists but retrieval is not available |

The same matrix should cover imports, project operations, and future analysis tasks.

### D. Traceability matrix

Link every requirement to its implementation and tests.

| Requirement               | UI location             | Backend dependency                  | Verification                                      |
| ------------------------- | ----------------------- | ----------------------------------- | ------------------------------------------------- |
| Identify project spectra  | Projects                | Dataset provenance and metadata     | Multiple attachments remain distinguishable       |
| Import local data         | Data                    | Import and persistence services     | Supported formats validate and reopen correctly   |
| Preview a reference       | Molecular References    | Reference data and parser           | Plot matches validated source data                |
| Compare selected datasets | Analysis                | Eligibility and comparison services | Compatible inputs are handled correctly           |
| Save a custom layout      | Workspace layout system | Preference persistence              | Layout restores and recovers from obsolete panels |

The table is an example of the structure to maintain, not a claim that these tasks are all implemented.

This matrix should be updated whenever a feature is added, changed, deferred, or removed. It is the best defense against designing a beautiful UI that forgets existing functionality.

### Add a visual acceptance checklist

For each workspace, verify at least:

- The normal window size and a smaller window size.
- Empty, loading, successful, and error states.
- Long names and large metadata values.
- Large result lists and large numerical tables.
- Keyboard navigation and accessible control labels.
- A consistent way to return, cancel, or reset.
- Persistence across restart where applicable.
- Correct behavior when a feature is unsupported.
- No loss of data when the user changes display preferences.

This is as important as checking whether the screen looks good in a static mockup.

## 10. The independent UI-design workflow I would follow

The work should proceed in phases, with clear deliverables and review gates. That lets you make progress in your free time without blocking ongoing feature development.

## 1

Phase 1 — Inventory and architecture

Start here

Map the current screens, controls, actions, data dependencies, and existing behaviors. Compare them with Issue #2 and the project’s documented future direction.

Deliverable: capability inventory, navigation map, and list of unresolved design decisions.

## 2

Phase 2 — Low-fidelity wireframes

Sketch the main application shell and each workspace before selecting detailed styling. Establish where search results, tables, graphs, inspectors, and toolbars belong.

Deliverable: a coherent wireframe set covering both current features and planned workflows.

## 3

Phase 3 — Visual system and interaction patterns

Define typography, spacing, panel borders, buttons, selection states, table behavior, plot legends, notifications, dialogs, and progressive disclosure.

Deliverable: reusable design rules and representative high-fidelity screens.

## 4

Phase 4 — Interaction prototype

Test the important workflows with representative data: searching for a planet, attaching a spectrum to a project, importing a local file, retrieving a reference, and preparing a future comparison.

Deliverable: an interactive prototype that demonstrates transitions and states, not just attractive screenshots.

## 5

Phase 5 — Implementation mapping

For each visual component, identify the existing Qt widget, service, data model, or future dependency it needs. Separate cosmetic changes from changes to application behavior.

Deliverable: a component map, dependency list, and small implementation tasks that can be handed to whichever AI or developer you choose.

## 6

Phase 6 — Incremental integration and regression testing

Implement one workspace or shared component at a time. Test the existing behavior before and after each change, then update the capability and traceability inventories.

Deliverable: a UI that evolves without breaking search, persistence, retrieval, or scientific correctness.

### Important boundary between design and implementation

An AI-generated UI mockup is useful for exploring layout, but it cannot establish that the application will behave correctly. It may invent controls, omit states, or imply capabilities that the backend does not provide.

Every proposed control should therefore be classified as one of:

- Existing: connects to a verified capability.
- Needs adaptation: uses existing functionality through a new interface.
- Future: requires backend or scientific-method development.
- Design decision pending: needs agreement before implementation.

This classification allows the visual design to include future functionality without accidentally promising that it already works.

## 11. What I would prioritize first

I would not attempt to design every screen in detail at once. The following order provides a stable foundation and minimizes rework.

| Priority | Work                                              | Reason                                                                 |
| -------- | ------------------------------------------------- | ---------------------------------------------------------------------- |
| 1        | Inventory current functionality and dependencies  | Prevents existing capabilities from disappearing during redesign       |
| 2        | Define global navigation and workspace boundaries | Establishes where future features belong                               |
| 3        | Design the Data and Projects workflows            | They provide the foundation for organizing and reusing scientific data |
| 4        | Design the Analysis workspace                     | Resolves the graphing and comparison questions in Issue #2             |
| 5        | Refine Search and Molecular References            | Makes discovery, metadata, and retrieval easier to use                 |
| 6        | Define global settings and layout preferences     | Adds customization after the workspace structure is stable             |
| 7        | Implement and validate reusable components        | Allows the UI to evolve without rebuilding every screen                |

There is one important dependency: the Analysis workspace should be designed early enough to influence the overall architecture, but its actual scientific functionality should only be implemented when the underlying methods and data contracts support it.

## 12. Decisions worth settling before visual design

These are the choices that will have the greatest impact on the final layout.

Initial design preferences. These are not implementation commitments; you can leave the defaults or change any selection.

1\. Main navigation

Dedicated workspaces

Separate Search, Projects, Data, References, and Analysis.

Fewer broad sections

Combine related functions into fewer screens with internal subpanels.

2\. Graphing and comparison

Dedicated Analysis workspace

Give multi-spectrum plotting and comparison its own main area.

Analysis inside Projects

Make each project the primary place for plotting and analysis.

3\. UI customization

Staged customization

Start with columns and panel sizes, then add saved layouts.

Advanced layouts early

Prioritize draggable panels and named layouts from the beginning.

4\. Local data

Dedicated Data workspace

Import, validate, and inspect datasets before attaching them to projects.

Import through Projects

Make local import primarily an action inside each project.

5\. Overview

Research summary

Show the current project, available data, recent activity, and pending tasks.

Launch dashboard

Use it primarily to navigate into the application's main functions.

Defer it

Leave Overview minimal until the major workflows are established.

Continue with these preferences

## Final recommendation

Treat the UI as a separate design workstream with a documented interface contract, not as a cosmetic layer to be applied after development finishes.

The immediate goal is to produce a coherent design system and a complete map of how users move from discovery, to data management, to inspection, to analysis. That design should be grounded in the existing ECAS implementation while explicitly accounting for planned capabilities.

The most consequential decisions are:

- Make Analysis a first-class workspace with appropriate graphing and data inspection.
- Give local data import and project organization clear, complementary roles.
- Keep search results and metadata concise by default, with deeper detail available on demand.
- Offer meaningful customization without allowing arbitrary layouts to break the application.
- Make every new UI feature traceable to a real capability, a planned dependency, and a verification test.

Once those foundations are agreed upon, individual screens can be designed and implemented independently, with much less risk of having to redesign the entire application as ECAS grows.