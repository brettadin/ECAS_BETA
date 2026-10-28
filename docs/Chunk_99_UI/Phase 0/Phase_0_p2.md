** This was the continuation from the Initital planning response. it just looks over stuff, and i had to tell it i cant upload images to help it visualize the ui.. stupid limits... It was unable to do it itself, too. **

# ECAS UI side project — Phase 0 review

Phase 0 can now be considered complete for planning purposes, with one limitation: I have inspected the application structure and the available issue report, but I could not independently view the screenshots or launch the application in this environment.

I used your designated [`UI-Side-Project`](https://github.com/brettadin/ECAS_BETA/tree/UI-Side-Project?utm_source=chatgpt.com)[ branch](https://github.com/brettadin/ECAS_BETA/tree/UI-Side-Project?utm_source=chatgpt.com) as the source of truth for this review. I also reviewed the architecture documents, current project state, implementation records, and [GitHub Issue #2](https://github.com/brettadin/ECAS_BETA/issues/2?utm_source=chatgpt.com). I have not modified the repository or run tests.

## 1. Can I visualize the existing application?

I tried two routes.

- Run the application: The environment cannot clone the repository because external network access is unavailable. I therefore could not install its dependencies or launch the current branch.
- Inspect the screenshots in Issue #2: I retrieved the issue text, including its embedded image references, but could not load the actual images through the available tools.

The issue nevertheless provides useful descriptions of the existing interface and how it behaves. It confirms that the current UI includes project management, spectral-data inspection, and a molecular-reference catalogue, and identifies several usability concerns.

I can continue to inspect the source code and infer the layout structure, but I will distinguish those inferences from observations of a running application.

If we later need an actual visual reference, there is no need for you to upload images. We can use Cline on your computer to generate screenshots of the current application and save them in the repository or a local review folder. You can then share the resulting file contents or have Cline describe the screenshots in a structured report. That is a fallback, not a prerequisite for continuing the planning work.

## 2. Architecture review

I reviewed the architecture documents and the relevant UI implementation on your selected branch.

The most important distinction is that ECAS already has a working application foundation, but several of its intended scientific workflows remain incomplete. The redesign should improve the existing application rather than imply that planned scientific capabilities already exist.

### Current application structure

### ECAS desktop application

Python · PySide6 · Qt

Main window

Navigation, page layout, shared display state

Application services

Projects, ingestion, retrieval, persistence

Scientific visualization

PyQtGraph and tabular spectral inspection

Data storage

SQLite projects and separate source/reference caches

The main window is implemented in [`ecas/ui/main_window.py`](https://github.com/brettadin/ECAS_BETA/blob/UI-Side-Project/ecas/ui/main_window.py?utm_source=chatgpt.com). It uses a left-side navigation list and a stacked page container, with the selected page displayed on the right.

The existing styling is a dark Qt stylesheet with fixed-width navigation and shared widget styles. This gives us a clear starting point for a visual redesign without requiring a new UI framework.

### Existing navigation and capabilities

| Current page  | Verified status from source and records                                   | Implication for redesign                                                                          |
| ------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Overview      | Placeholder                                                               | Decide whether it should become a useful workspace landing page or be removed.                    |
| Projects      | Functional project creation, selection, spectrum attachment and reopening | Improve discoverability and how saved datasets are identified.                                    |
| Spectral Data | Local import, NASA retrieval/cache access, plot and data table            | Organize source selection, import controls, metadata and visualization more clearly.              |
| Comparisons   | Molecular-reference search and bounded reference retrieval                | Clarify that this currently focuses on reference discovery, not production scientific comparison. |
| Settings      | Placeholder                                                               | Do not design a large preferences system before its requirements are established.                 |

The source confirms the navigation labels, a 200-pixel fixed-width sidebar, and a 1200 × 800 initial window size with a 900 × 600 minimum. These are code-level facts, not measurements of how the interface looks on your screen.

## 3. What the architecture means for the redesign

The existing separation between UI, ingestion, scientific data, and persistence is worth preserving.

The main components include:

- `ecas/models/spectrum.py` — the `SpectrumData` model, which retains columns, rows, source location and import warnings without inventing missing scientific meaning.
- `ecas/ingestion/` — CSV and NASA ingestion, plus ExoMol catalogue and reference retrieval.
- `ecas/projects.py` and `ecas/persistence.py` — project operations and persistent records.
- `ecas/visualization/spectra_plot.py` — PyQtGraph visualization.
- `ecas/ui/` — the main window and the separate project, NASA and molecular-reference interfaces.

The architecture documents reinforce several important rules: UI components should not issue SQL directly, scientific algorithms should not live inside view code, and the interface must not infer missing units or present unsupported scientific conclusions.

These constraints do not prevent a substantial facelift. They tell us where to make changes safely.

For example, we can redesign the project browser, restructure the spectral-data page, introduce clearer metadata panels, and improve the visual hierarchy without rewriting the underlying scientific services.

## 4. Important findings from Issue #2

Your issue report helps establish real usability needs beyond the general goal of making the interface look better.

Projects need better dataset identification

The report describes multiple project attachments appearing as `source.tbl`. You also wanted author and instrument information to be easier to identify.

The data already retain source bytes and provenance. The likely UI solution is to expose useful metadata and distinguish records in the project list, rather than introduce another storage system.

Search results need clearer status information

Molecular records can be searchable without having a supported downloadable product. The interface should distinguish a catalogue match, a supported retrieval, an unavailable product and an actual retrieval failure.

Inspection and comparison are different tasks

Your report proposed viewing multiple spectra together, with distinct labels and colors, and separating this from molecular-reference retrieval. That is a useful design direction, but true scientific comparison must remain a distinct capability with explicit compatibility rules.

Overview and Settings need defined purposes

Both pages are currently placeholders. Their future roles should follow the user's workflow, not be filled with decorative cards or speculative controls.

Source: [Issue #2 — user verification notes](https://github.com/brettadin/ECAS_BETA/issues/2?utm_source=chatgpt.com).

## 5. Scientific and implementation boundaries

The redesign needs to preserve these distinctions.

- Observations and molecular references are different data types. Displaying them together must not imply that their quantities or units are directly comparable.
- A plotted overlay is not a validated scientific comparison. Any future comparison workspace needs explicit eligibility checks, labels, units, and warnings.
- Retrieval availability is limited. The current implementation record identifies one bounded ExoMol retrieval workflow: CO₂ / `12C-16O2` / UCL-4000. Other catalogue entries remain searchable, but are not all supported for retrieval.
- Scratch analysis and persistent projects should not be conflated. If we add a quick exploratory workspace, it needs a clear unsaved state and a deliberate way to preserve work in a project.
- Existing persistence should remain authoritative. UI improvements should build on the current project and cache mechanisms unless a demonstrated requirement justifies a change.

The last two points will matter when we plan the information architecture, since they affect what the user sees across pages and how work is resumed.

## 6. Phase 0 status

| Item                                                      | Final status                                             |
| --------------------------------------------------------- | -------------------------------------------------------- |
| Selected branch established as the review target          | Complete                                                 |
| Current UI architecture and navigation reviewed           | Complete                                                 |
| Relevant architecture and implementation records reviewed | Complete for initial planning                            |
| Existing functionality and key limitations mapped         | Complete for initial planning                            |
| Issue #2 usability observations reviewed                  | Complete                                                 |
| Test status                                               | Accepted as-is per your instruction; no rerun needed now |
| Running application and screenshots visually inspected    | Unavailable in this environment                          |

Phase 0: complete for planning purposes. The missing visual inspection is a documented limitation, not a reason to restart the audit. We should revisit the actual rendered interface before finalizing visual details or accepting a prototype.

## 7. Recommended next step: Phase 1

I recommend moving to a capability and user-workflow inventory, not implementation.

The next review should establish the major tasks ECAS needs to support and how the existing features fit together. In particular:

1. Find an exoplanet and discover available data.
2. Import or retrieve a spectrum and inspect its metadata and plot.
3. Create or reopen a project and organize its datasets.
4. Search for, retrieve and inspect molecular reference data.
5. Inspect multiple datasets together, while clearly distinguishing visual overlays from validated comparisons.
6. Preserve exploratory work and reopen previous work.
7. Understand unsupported actions, errors, progress and retrieval status.

For each workflow, we should record the existing entry point, relevant data and services, the user's likely pain points, the current limitations, and what the redesign must preserve.

The output should be a small, evidence-backed set of user journeys and requirements. Those will then inform the information architecture and low-fidelity wireframes.

No code changes, branches, prototypes, or detailed visual styling are needed yet.