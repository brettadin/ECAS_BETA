# Pass G — Documentation and intended behavior

Scope: Compare ECAS v1's documented goals, user-facing guidance, roadmap, and historical audit records against the source inspected in Passes A–F.

The archive contains a README, roadmap, blueprint, master construction prompt, changelog, and historical audit documents. These documents serve different purposes, so a historical issue should not automatically be treated as a current defect.

## 1. README versus implemented functionality

The README describes two primary workflows: spectroscopy and transit analysis. The source contains corresponding modules and supporting functionality.

| Documented capability                                   | Source-level assessment                              |
| ------------------------------------------------------- | ---------------------------------------------------- |
| Spectral modeling, gas controls, and fitting            | Implemented in the engine and fitting modules        |
| Import spectra from supported file formats              | Implemented, with format-specific limitations        |
| Residuals, anomalies, and molecular candidate matching  | Corresponding analysis functions exist               |
| Planet lookup and archive-product discovery             | Implemented in the archive layer                     |
| TESS light-curve analysis                               | Corresponding archive and transit functions exist    |
| JWST spectral time-series processing                    | Dedicated loader and analysis pathway exist          |
| Transmission-depth extraction                           | Implemented in `transit.py`                          |
| Optional `petitRADTRANS` comparison and abundance scans | Implemented in `atmosphere.py`                       |
| Project save/load and exports                           | Corresponding persistence and export functions exist |

The README also describes meaningful limitations: the molecular comparison workflow is not a calibrated abundance retrieval, the abundance scan is conditional, and correlated-noise diagnostics do not correct uncertainties automatically.

Assessment: the README broadly represents the architecture and major capabilities found in the source. The remaining issue is not a wholesale mismatch between documentation and code, but ensuring that descriptions of capabilities do not imply stronger scientific validation than the code supports.

## 2. Roadmap versus current implementation

`documentation/ROADMAP.md` records product goals, design principles, status, suggested next steps, and known issues. It emphasizes scientific integrity, provenance, reusable data, and avoiding unsupported conclusions.

The source already implements portions of these goals, including citation records, caching, project persistence, and external-data adapters.

However, a roadmap item can describe a goal without being an acceptance criterion for the current version. The existence of a feature does not necessarily mean it satisfies the full intended requirement.

Examples:

- Data provenance: source and citation infrastructure exists, but complete persistence of provenance through every project workflow is not established.
- Reusable datasets: caching exists, but cache reuse is not equivalent to verifying the identity and integrity of every external product.
- Scientific validation: synthetic tests and validation tools exist, but the evidence does not establish general real-world calibration.
- Transparent assumptions: several caveats are documented, but whether every relevant output displays and exports those caveats requires further verification.

These are gaps between the broader design principles and the assurances established by the current implementation.

## 3. Historical documentation that needs careful interpretation

The archive contains `Phase_0_Audit.md`, `Phase_0_audit_p2.md`, and numerous historical handoff notes. These provide development history, but they include statements that may predate later changes.

For example, the audit documents discuss older ORCA-based workflows, mock data in the gas registry, NIST HTTP 403 failures, and incomplete atmospheric-model integration. Later changelog entries describe fixes and additional implementations.

That creates a documentation-maintenance risk: historical audit statements should not be copied into a current status report without checking the present code and later verification records.

The changelog is more useful for tracing specific changes because its entries include implementation descriptions and claimed verification results. It records synthetic regression tests, reported full-suite results, and known limits. Those historical results are evidence of what was reported at the time, but they do not substitute for running the current archive's tests during this review.

### Finding G1 — Current status and historical findings need clearer separation

The archive contains both current-facing documentation and historical audit records, and older findings can appear inconsistent with later implementation.

Recommendation: label historical reports as snapshots, link each resolved issue to its fix and verification entry, and maintain a concise current-status section that distinguishes confirmed, resolved, partially resolved, and unverified issues.

## 4. Master construction prompt and project principles

`documentation/ECAS Master Construction Prompt.md` sets broader expectations for scientific integrity, data retrieval, analysis, persistence, testing, and documentation.

Its core principles align with the strongest findings from this review:

- Preserve distinctions between measured data, references, processed results, and predictions.
- Track sources and processing history.
- Avoid presenting possible molecular matches as confirmed detections.
- Validate analytical methods against known results where possible.
- Make assumptions and limitations transparent.
- Preserve working functionality unless there is a clear reason to change it.

These are project goals and development constraints, not proof that every requirement has already been met.

The most important documentation task is to turn those principles into verifiable acceptance criteria. For example, “preserve provenance” should specify what fields must survive a save/reopen cycle, while “validate retrieval” should identify the datasets, injected parameter regimes, recovery metrics, and coverage thresholds that constitute acceptable evidence.

## 5. Consolidated Pass G findings

| ID | Finding                                                                                              | Priority                                        |
| -- | ---------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| G1 | Historical audit findings can be confused with current status                                        | Medium                                          |
| G2 | README capability descriptions broadly match the inspected source                                    | Positive                                        |
| G3 | Roadmap goals around provenance and reproducibility exceed what has been established by inspection   | High                                            |
| G4 | Changelog verification claims provide useful history but have not been independently reproduced here | High before relying on them as current evidence |
| G5 | Broad scientific-integrity principles would benefit from explicit, testable acceptance criteria      | High                                            |

Pass G is complete at the source-inspection level. No files have been modified, and no tests have been run.

# Overall ECAS v1 review — A through G

## Summary

Architecture and capabilities

ECAS v1 is a modular scientific desktop application with substantive spectroscopy, molecular identification, transit, time-series, persistence, and optional atmospheric-model functionality.

Scientific reliability

Several methods have meaningful assumptions and documented limitations. The potential covariance-scaling issue in spectral fitting requires numerical verification before any change is made.

Data and provenance

File ingestion, caching, project persistence, and citation infrastructure exist, but complete reproducibility and provenance retention have not been established.

Verification

The codebase includes targeted tests and synthetic validation infrastructure. The current suite has not been run during this review, so no current pass status is claimed.

## Recommended issues to carry forward

These are the most consequential findings across the seven passes, ordered by the need to clarify or verify them rather than by implementation effort.

1. C1 — Verify the spectral-fit covariance calculation. Use controlled synthetic data with known noise to determine whether estimated uncertainties are scaled correctly.
2. D5 and D7 — Strengthen reproducibility and provenance. Establish what project files must preserve about configurations, input datasets, source identifiers, and processing choices.
3. C3 and C6 — Preserve uncertainty and retrieval limitations. Ensure transmission-spectrum uncertainties and conditional abundance-scan results are interpreted and reported appropriately.
4. D1 and D2 — Make import assumptions explicit. Users need to know how columns, units, signal types, and normalization have been interpreted.
5. F1, F3, and F5 — Establish a current verification baseline. Test the clean installation, full suite, and failure behavior in a documented environment.
6. G1 — Reconcile current documentation with historical reports. Keep the development history while clearly distinguishing current status from superseded findings.

These are review findings, not instructions to implement all changes immediately. In line with the project's controlled workflow, each actionable change should be planned, reviewed, and implemented in a small, testable unit.

## Review boundary

The v1 review is complete across Passes A–G at the source-inspection level. It has identified architecture, workflow, scientific, data-management, UI, testing, and documentation concerns. It has not established that ECAS v1 is scientifically validated, that the current test suite passes, or that any suspected defect has been reproduced.

The next stage is the separate ECAS Beta review, beginning with its architecture and structure. Findings should be kept distinct from v1 until the Beta review establishes which components, fixes, assumptions, and limitations were carried forward.