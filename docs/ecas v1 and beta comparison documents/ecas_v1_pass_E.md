# Pass E — UI and usability

Scope: Review how ECAS v1 presents its scientific workflows, communicates analysis state, handles user input and errors, and supports long-running operations.

This pass examines the archived source and documentation. It does not establish that the interface behaves correctly at runtime; that would require launching the application and testing its workflows.

## 1. Application layout and workflow separation

The main interface is implemented in `app/ui/main_window.py`, with the transit and 3D visualization workflow in `app/ui/transit_panel.py`.

The UI separates two major user activities:

- Spectroscopy: configuring molecular models, adjusting gas parameters, importing observations, fitting spectra, reviewing anomalies and candidates, and exporting results.
- Transit analysis: finding planetary data, loading light curves or spectral time series, analyzing transits, viewing orbital geometry, and extracting transmission spectra.

This separation gives each workflow a recognizable purpose while allowing transmission-spectrum results to feed into molecular comparison.

The application also provides project open/save functionality and export options, so analysis is not restricted to a single transient GUI session.

Assessment: the overall organization is appropriate for a scientific desktop application with multiple related workflows. The main usability question is whether users can reliably understand which data and assumptions are active as they move between those workflows.

## 2. Visual feedback and analysis state

The spectroscopy interface includes multiple plot tabs, gas controls, a residual plot, and a status area. The residual plot uses a standardized residual axis and displays threshold lines at \\(+3\sigma\\) and \\(-3\sigma\\).

The main window also maintains an activity log, which is read-only and capped at 500 blocks. It is hidden by default.

### Positive findings

- Residuals are visualized separately from the modeled spectrum, making model disagreement easier to inspect.
- Slider events are coalesced through a single-shot `QTimer`, avoiding a full refresh for every event in a rapid burst of slider changes.
- The interface can show an exploratory blackbody continuum fit and explicitly warns that molecular features and systematics are not modeled.
- The activity log provides a place for warnings and operational information without making the main workspace permanently crowded.

### Finding E1 — Important diagnostic information may not be visible by default

The activity log starts hidden. This is a reasonable layout choice, but it means users may not notice warnings unless they know where to look. The status bar is also used for transient messages.

Recommendation: ensure warnings that affect scientific interpretation remain visible or are explicitly acknowledged. Important import assumptions and failed analysis steps should not be communicated solely through a transient status message.

## 3. Import and error handling

The code contains user-facing warning paths for failures such as blackbody fitting errors and unsupported input requirements. Several core modules also raise domain-specific exceptions, including `TableError`, `FitError`, `TransitError`, and `ArchiveError`.

This is a good foundation for separating expected scientific-input problems from unexpected programming errors.

However, source-level exception handling alone does not establish that all failures are presented clearly. The important usability questions are whether users receive actionable explanations, whether failed operations leave the previous valid result intact, and whether partial results are distinguished from completed analyses.

### Finding E2 — Error messaging needs end-to-end verification

The reviewed source shows individual error-handling paths, but it does not establish consistent user-facing behavior across all import, network, fitting, and atmospheric-model operations.

Recommendation: during runtime testing, verify that each failure:

- Identifies the operation that failed.
- Explains the actionable cause when known.
- Preserves valid existing data.
- Avoids presenting stale results as though they came from the latest inputs.

This remains a verification requirement, not a confirmed defect.

## 4. Background operations and responsiveness

`app/ui/tasks.py` provides a reusable `run_async()` helper. It runs a callable in a worker thread, forwards success or failure signals, and keeps track of worker/thread pairs for cleanup. The transit panel uses worker threads for analysis.

The 3D viewport also degrades gracefully: if PyVista/PyVistaQt is unavailable, OpenGL is unavailable, or 3D has been disabled, the interface falls back to a 2D orbit visualization and provides an explanation.

### Finding E3 — Graceful 3D fallback is a clear usability strength

The application does not make the optional 3D renderer a prerequisite for using the transit workflow. This reduces installation and platform friction.

A remaining question is whether every worker operation handles cancellation, repeated submissions, window closure, and late-arriving results safely. The helper's existence is positive, but these lifecycle behaviors require execution tests.

## 5. Scientific communication and interpretation

The interface and documentation include several explicit caveats:

- Blackbody fitting is exploratory continuum fitting, not atmospheric characterization.
- Molecular candidate matches do not establish confirmed detections.
- Transit-depth conversion to pseudo-transmittance is a relative comparison technique.
- Abundance scans are conditional and are not posterior distributions.
- Correlated-noise diagnostics do not automatically correct uncertainties.

These caveats are especially important for a scientific application because visual polish and numerical output can otherwise make exploratory estimates appear more authoritative than they are.

### Finding E4 — Interpretation warnings should follow the result

The source and README document meaningful limits, but a caveat in the README may not be present when a user views a result or exports it.

Recommendation: keep the relevant caveat adjacent to the output it qualifies and carry it into exported reports where appropriate. For example, a single-gas abundance scan should identify fixed inputs and the conditional nature of its interval in the results view and report, not only in general documentation.

This is a design recommendation; I have not verified every result panel or export template in this pass.

## 6. Consolidated Pass E findings

| ID | Finding                                                                                           | Assessment                        |
| -- | ------------------------------------------------------------------------------------------------- | --------------------------------- |
| E1 | The activity log is hidden by default, potentially reducing warning visibility                    | Medium                            |
| E2 | Consistency of error handling across complete workflows remains unverified                        | Medium                            |
| E3 | The 2D fallback for unavailable 3D rendering improves accessibility and resilience                | Positive                          |
| E4 | Scientific caveats should be shown alongside outputs and retained in reports                      | High for scientific communication |
| E5 | Worker lifecycle and stale-result behavior need runtime testing                                   | Medium                            |
| E6 | Separate spectroscopy, identification, and transit workspaces provide clear functional separation | Positive                          |

## Pass E conclusion

ECAS v1 has several good UI foundations: distinct workflows, residual visualization, activity logging, debounced plot refreshes, background-task support, and graceful fallback from 3D to 2D. It also makes a genuine effort to distinguish exploratory outputs from validated scientific conclusions.

The principal usability risks are the visibility and persistence of warnings, consistent recovery from errors, and ensuring scientific caveats stay attached to the results they qualify.

Pass E is complete at the source-inspection level. No files have been modified, and no tests or interactive UI sessions have been run.

The next pass is Pass F — Testing, reliability, and maintainability. It will examine the test suite, dependency and packaging assumptions, failure handling, code organization, and what can actually be established about reliability without claiming tests have passed when they have not.