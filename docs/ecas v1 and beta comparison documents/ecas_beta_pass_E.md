# ECAS Beta Review — Pass E: UI and Usability

Review basis: the supplied Beta archive, focusing on `ecas/ui/`, visualization modules, workflow integration, and the related project-state and architecture documentation.

This is a read-only source review. I have not launched the desktop application, performed interactive usability tests, or modified any files. I will distinguish observable UI implementation from behavior that would require runtime testing.

## 1. Overall interface structure

Beta uses a multi-page desktop workspace rather than placing all functionality in one spectroscopy window.

The principal areas include:

- Overview
- Settings
- Projects
- NASA archive browsing
- Molecular reference browsing
- Comparisons
- Resources

The main window coordinates these pages and the underlying ingestion, persistence, visualization, and comparison subsystems. This is a substantial expansion from a single-window spectroscopy workflow.

ECAS main window

Application navigation and session coordination

Research workspace

Overview, settings, projects and saved data

Scientific resources

NASA records, molecular catalogue and reference products

Comparison workspace

Input selection, eligibility, model preparation and residual diagnostics

Visualization

Spectrum, reference and residual plotting components

Logical UI organization based on source modules; this is not a screenshot or a claim that every page has been exercised at runtime.

Finding E1 — The interface is organized around distinct research workflows. This structure should make the application easier to extend than a monolithic window, but it also raises integration questions: do selections, source details, errors, and saved state remain consistent when users move between pages?

That question cannot be settled from the package structure alone.

## 2. Comparison interface: capability and discoverability

The most complex UI component is `ecas/ui/comparison_browser.py`, at over 2,000 lines. It includes:

- Separate observation and molecular-reference selectors.
- Native-unit plots and data tables.
- Expandable source-information panels.
- A collapsible comparison and candidate-tools panel.
- Quick Setup for metadata and alignment.
- Eligibility and compatibility feedback.
- A summary card and technical-details/provenance views.
- Candidate staging and forward-model handling.
- Residual diagnostics and attribution-related displays.

This is more than a passive browser. The UI exposes substantive comparison-related operations, although the actual operations remain subject to eligibility restrictions and scientific limitations documented in Pass C.

### Usability strengths

The implementation deliberately separates routine inspection from advanced controls. Source metadata and technical diagnostics can be expanded when needed, while a summary area is available for a more readable view.

The interface also explains several easy-to-misunderstand behaviors: observation choices last only for the session, reference choices need refreshing, selection alone does not produce a valid comparison, and plots use independent axes unless a supported alignment workflow is performed.

### Usability risks

Finding E2 — The comparison interface has high conceptual complexity. Its extensive controls require users to understand observable type, units, coordinate frame, response metadata, uncertainty assumptions, model inputs, and alignment. Tooltips and technical panels help, but source inspection cannot establish that the intended workflow is easy to follow for a new user.

Finding E3 — Important controls are hidden behind expandable panels. Hiding advanced controls can reduce clutter, but it can also make available capabilities hard to discover. This is a usability concern, not proof that the controls are defective.

A runtime usability test should determine whether a first-time user can select inputs, recognize incompatibilities, understand the displayed diagnostics, and avoid treating a staged candidate as a detection.

## 3. A significant documentation inconsistency in the workspace

The Overview page (`ecas/ui/workspace_pages.py`) currently tells users:

> “Comparison calculations and atmospheric modelling are not available.”

It also says that successful reference retrieval does not establish scientific compatibility.

The latter warning is consistent with the implementation. The first statement is broader than the current code: the comparison browser contains eligibility, alignment, model-generation, candidate, and diagnostic workflows.

The README has a related discrepancy, as noted in Pass B.

Finding E4 — The Overview page understates the capabilities exposed elsewhere in the application. This is a confirmed inconsistency between user-facing guidance and the current UI/source implementation. It could lead users to miss existing features or misunderstand the application's actual development state.

The correction should not simply claim that atmospheric characterization is complete. The text needs to distinguish implemented comparison and model-preparation operations from a validated end-to-end scientific retrieval or molecular-detection workflow.

## 4. NASA browser: network feedback and safe selection

The NASA browser (`ecas/ui/nasa_browser.py`) has several explicit usability safeguards:

- It displays guidance that only supported transmission tables can be loaded.
- It provides target-name suggestions when a search fails to match a known target.
- It disables conflicting controls while a request is pending.
- It includes a cancellation control.
- It reports failed operations and states that previously displayed data remain unchanged.
- It separates search results, cached choices, and loading the selected spectrum.

These choices make the distinction between discovering a record and loading a supported product more explicit.

Finding E5 — NASA request-state handling is visible in the implementation. The browser tracks busy state and updates controls around requests. Whether cancellation always stops the underlying network operation, whether the UI remains responsive during slow requests, and whether stale results can overwrite newer selections require runtime testing.

## 5. Molecular-reference browser

The molecular browser (`ecas/ui/molecular_browser.py`) provides a search field with examples of valid queries, a status area, and catalogue/product controls. It is designed around the distinction between finding catalogue entries and retrieving supported cross sections.

This separation is scientifically important: a catalogue match is not equivalent to a downloadable compatible product, and a cross section is not a planetary transit-depth prediction.

The status text is word-wrapped and displayed as plain text, reducing the risk of metadata being interpreted as rich text. However, the source review cannot establish whether all failure modes explain the next step clearly or whether catalogue and product states are sufficiently distinguishable during actual use.

Finding E6 — The molecular browser reflects the underlying catalogue-versus-product distinction, but its full interaction flow remains unverified.

## 6. Project browser and saved-state feedback

The project browser (`ecas/ui/project_browser.py`) explains how to create or select a project, save the displayed spectrum, and reopen a saved record offline.

It also:

- Disables the save action when no spectrum or project is available.
- Disables opening a record when nothing is selected.
- Displays saved-spectrum counts and storage location.
- Uses labels and tooltips to provide additional record information.
- Revalidates that a selected record still exists before opening it.
- Displays errors from failed project operations.

These behaviors reduce accidental actions and help users understand the current project state.

Finding E7 — Project actions have useful state and error feedback. The remaining usability question is whether the displayed source/provenance details are enough for a researcher to distinguish similarly named records and understand what is preserved offline. That should be checked with realistic project records.

## 7. Spectrum plotting and data inspection

The spectrum plot component (`ecas/visualization/spectra_plot.py`) clears the previous plot before loading a new dataset. If the new dataset lacks the required columns or contains no valid coordinate pairs, the component clears its state rather than leaving the previous spectrum visible.

It also filters out missing, non-numeric, NaN, and infinite coordinate pairs before plotting. Units are taken from explicitly supplied metadata, rather than inferred solely for axis labels.

The comparison browser separately offers native-unit plots and data tables. The reference plot can display molecular data in its native wavenumber representation or in wavelength units through an explicit toggle.

Finding E8 — The plotting layer has useful stale-display and invalid-point safeguards. These behaviors are source-supported, but they do not prove that every invalid input produces an informative explanation in the full application or that axis labels always communicate enough scientific context.

## 8. Cross-workflow usability concerns

Three broader issues emerge from the UI review.

### A. Session state versus saved state

The Settings and Overview pages explicitly state that observation choices in Comparisons last only for the current session. Projects preserve saved observations and their available provenance, while NASA and ExoMol caches support offline reopening.

That distinction is important but introduces a potential workflow trap: a user can prepare comparison inputs and then lose those selections on application exit if they have not saved the underlying records.

### B. Metadata attestations can be mistaken for verified facts

Quick Setup can populate missing comparison metadata from imported information or defaults. The comparison code records caller-supplied attestations for fields not established by the raw import.

This is preferable to silently hiding assumptions, but the interface needs to make clear that filling a field does not verify it. In particular, assigning a role, observable, coordinate frame, or response identifier must not be interpreted as independent confirmation of the data's scientific meaning.

### C. Technical detail versus accessible interpretation

Beta has both summary displays and technical reports, which is a useful design. The risk is that a concise summary can appear more definitive than the underlying eligibility checks, assumptions, or diagnostic limitations warrant.

A researcher should be able to determine, without digging through source code:

- What data were compared.
- Which transformations were applied.
- Why the inputs were considered eligible.
- Which assumptions were supplied rather than verified.
- What the diagnostic measures—and what it does not measure.

The comparison browser appears designed to expose much of this information. Whether it communicates all of it effectively requires an interactive test with realistic inputs.

## 9. Pass E findings summary

| ID | Finding                                                                                                                                  | Classification                                                    |
| -- | ---------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| E1 | The application has distinct research-workflow pages coordinated by the main window.                                                     | Confirmed structure                                               |
| E2 | The comparison interface has substantial scientific and configuration complexity.                                                        | Usability risk                                                    |
| E3 | Some advanced capabilities and diagnostics are hidden behind expandable panels.                                                          | Discoverability risk                                              |
| E4 | The Overview page says comparisons and atmospheric modelling are unavailable despite implemented comparison/model-preparation workflows. | Confirmed documentation/UI inconsistency                          |
| E5 | NASA search includes busy-state controls, cancellation, target suggestions, and failure feedback.                                        | Source-supported safeguards; runtime behavior unverified          |
| E6 | The molecular browser separates catalogue discovery from supported product retrieval.                                                    | Source-supported design; full interaction unverified              |
| E7 | The project browser provides state-aware controls, record details, and error feedback.                                                   | Source-supported safeguards                                       |
| E8 | The plotting component clears stale plots and filters invalid coordinate pairs.                                                          | Source-supported safeguards                                       |
| E9 | Session-only comparison selections and caller-supplied metadata require clear communication.                                             | Confirmed workflow boundaries; usability effectiveness unverified |

No application launch or interactive usability test was performed, and no files were modified.

## 10. Overall assessment

Beta has a more complete and deliberate interface than a basic spectral viewer. Its project management, archive browsers, molecular-reference browser, comparison workspace, expandable diagnostics, and explicit status feedback are meaningful capabilities.

The clearest actionable issue from this pass is the stale Overview guidance. Beyond that, the largest concern is whether the complexity of the comparison workflow is manageable for researchers who may not be familiar with all the metadata, units, eligibility rules, and model assumptions.

The next pass should assess whether the existing tests and reliability controls adequately protect these workflows, including invalid input, request cancellation, persistence failures, stale state, and regression risks.

I will wait for your discussion or approval before proceeding to Pass F — Testing, reliability, and maintainability.