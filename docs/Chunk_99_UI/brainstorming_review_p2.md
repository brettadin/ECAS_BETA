** This is the second document related to the brainstorming process for the UI redesign. This is to keep a record of ideas as I work. **



These answers suggest that ECAS should be designed around two complementary ways of working: structured research inside projects, and flexible exploration outside them. The interface should support both without forcing users to commit to a project or sacrifice organization.

## 1. Refined workspace architecture

I would keep dedicated workspaces as the main navigation, but make them work together rather than operate as isolated screens.

Global application shell

Current workspace · Active project or scratch session · Background tasks · Settings · Layout controls

Search

Discover exoplanets, inspect records, find available data.

Projects

Manage research collections, datasets, and provenance.

Data

Import, validate, inspect, and organize local files.

Molecular References

Find, retrieve, cache, and inspect reference spectra.

Analysis

Plot, compare, and eventually run supported analysis methods.

Overview / Home

A useful entry point, not a duplicate of another workspace.

Proposed target structure, not a claim that all these workspaces already exist or have complete functionality.

## 2. Analysis should support both projects and quick exploration

I agree that it should be possible to investigate something without creating a project. A project should represent organized, continuing work—not be the admission ticket to use ECAS.

I recommend two analysis contexts sharing the same tools.

[Spectragryph - optical spectroscopy software: Screenshots](https://images.openai.com/static-rsc-4/W6uWgN2rkTwygYl8CPPGEljkZOzDa8t7Ky7VDMlAcP0yKTJVN7Y-CE8sVwTZn3qNm_n8N-vPDU1KoEaURjrxbSQ7_l1pMUdbx-xGkBMAYBJCWDjLFqhv-v2iJuD7iZWH2ulnfkEk0rfbsyU87k9Y6oogNAfnNFCu5POuRaWhqZ0?purpose=inline)

Scratch analysis

An ephemeral working session for quick investigations, temporary datasets, and looking at unrelated spectra together.

- Open data from Search, Data, or Molecular References.
- Inspect and plot without creating a project.
- Combine unrelated items for visual inspection when their data types and units permit it.
- Save or export useful results, or promote selected work into a project.

[Interface Overview — Raman Spectroscopy Analysis Application 1.0.0 documentation](https://images.openai.com/static-rsc-4/JfI19V7Cx-fq9K4Vh6mSbT08XIZM4aPcyovExDaf1ofnwolKeD6875Oa0ejjnmMiWhs3H4PFXzU_cAl_hXgmIXQoauLUP_RDccthYBHr5EeDYfKQs7yNcpG0pdXPqqddGcm-c__LrlISHArcb62pNK5QVtAymswTITR77J-mbCs?purpose=inline)

Project analysis

The same analytical tools, operating in the context of a selected project.

- Access that project's attached datasets and references.
- Keep relevant selections, analysis settings, and saved results associated with the project where supported.
- Reopen work with its provenance and configuration intact.
- Add further data without leaving the analysis workflow.

The distinction should be where the work belongs, not which tools are available.

For example, you could find an exoplanet, open an observational spectrum, retrieve a molecular reference, and inspect them in a scratch session. If the investigation becomes worth pursuing, you could save the relevant datasets and supported analysis artifacts into an existing project—or create a new one at that point.

There is an important scientific constraint: letting two items appear in the same plot does not mean they can be meaningfully compared. ECAS must check units, data types, axis semantics, and analysis eligibility. In particular, a molecular cross section should not be treated as directly equivalent to an observed transmission spectrum.

### How scratch work should behave

I would make scratch sessions persistent enough to be useful, but distinct from formal projects.

- Autosave the session state where feasible: open items, plot configuration, visible traces, and relevant settings.
- Clearly distinguish session state from saved scientific results and source data.
- Let users promote selected items into a project rather than forcing them to save everything.
- Provide a clear way to discard a scratch session, with confirmation when unsaved work or data could be lost.
- Avoid duplicating the original files merely because they are opened in a scratch session.

This needs an implementation review before deciding exactly what gets persisted. The existing data and project services should be reused where possible.

## 3. Layout customization: flexible, but recoverable

Your preference for a mix of guided defaults and substantial customization suggests a constrained, recoverable layout system.

Resize and rearrange

Resizable panels, collapsible sidebars, movable panels, adjustable table columns, and configurable plot-to-data proportions.

Save preferences

Remember workspace layouts, column visibility, panel sizes, and plot display preferences independently of scientific project data.

Built-in recovery

Restore default layout, reset one workspace, recover hidden panels, and prevent essential controls from becoming permanently inaccessible.

Named layouts

Eventually save presets such as “Spectrum inspection,” “Metadata review,” and “Comparison.”

I would not restrict users to a handful of fixed layouts. However, I would avoid completely unconstrained window placement initially. Panels should remain inside defined workspace regions, and core navigation and recovery controls should always remain accessible.

A useful additional safeguard is to distinguish between hiding an element and removing a capability. Hiding a metadata panel must never delete metadata; hiding a table column must never remove the underlying data or exclude it from an export.

## 4. The Data workspace should feed both scratch sessions and projects

Your answer to question four points toward a useful shared data workflow.

Import or discover data

Local FTIR CSV · UV-Vis TXT · Exoplanet observations · Molecular references

Validate and register

Inspect columns, units, axes, missing values, file format, source, and provenance.

Scratch session

Explore without project commitment.

Existing or new project

Organize data for continuing work.

This model also avoids assuming every input is a simple two-column CSV. Different instruments and file formats may require different parsers, and unknown units or axis meanings must be exposed for review rather than silently guessed.

The underlying data registry, project membership, and scratch-session state should be separate concepts. That gives ECAS a path to adding more import formats and scientific data sources without redesigning the entire application every time.

## 5. What should Overview become?

I would defer the final name until we inspect what the existing screen actually does. A screen should earn its place by solving a distinct problem.

My provisional recommendation is Home or Research Overview, with a narrow purpose:

- Resume recent projects and scratch sessions.
- Show recent datasets and references.
- Surface active downloads, imports, and other background tasks.
- Provide shortcuts to common actions such as importing data or starting an investigation.
- Report meaningful data or retrieval status without duplicating full analysis plots.

It should not become a dashboard full of decorative charts, duplicate search results, or statistics that don't help you decide what to do next.

If the current Overview has no useful independent role, repurposing or removing it from the main navigation is better than preserving it simply because it exists.

## 6. How to make sure nothing gets missed

Before implementation, I would add three explicit design deliverables to the UI workstream:

1. Capability inventory: every existing feature, including less visible functions such as caching, refresh, cancellation, persistence, error handling, export, and provenance.
2. Workspace and interaction map: where every feature lives, how users reach it, and how they move data between workspaces, scratch sessions, and projects.
3. Verification matrix: every user-facing capability mapped to its backend dependency, expected states, and a test or acceptance check.

Every proposed UI element should be classified as one of four things: already supported, requiring adaptation, a future capability, or an unresolved design decision. That distinction is especially important for Analysis, where the interface must not imply that research prototypes are production-ready scientific methods.

The work should then proceed from the shared application shell and interaction patterns to workspace wireframes, followed by detailed workflow designs and incremental implementation. That keeps visual design from accidentally driving unnecessary backend changes.

The key architectural decision is now clearer: ECAS needs shared scientific tools that can operate in a scratch session or in a project context, with a common data-management layer and a customizable but recoverable interface. This supports quick exploration today while leaving room for more sophisticated analysis workflows later.