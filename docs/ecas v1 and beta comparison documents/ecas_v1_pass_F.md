# Pass F — Testing, reliability, and maintainability

Scope: Assess the test suite, packaging and dependency configuration, reliability safeguards, and maintenance risks in ECAS v1.

The source archive includes a substantial set of tests, but their presence does not establish that they pass. This review has not executed the suite or launched the application.

## 1. Test-suite structure

The archive contains eight Python files under `tests/`, including the shared fixture configuration.

| Test module                | Main coverage                                                                                            |
| -------------------------- | -------------------------------------------------------------------------------------------------------- |
| `tests/test_ecas.py`       | Core engine, parser, configuration, fitting, transit analysis, UI workflows, persistence, and exports    |
| `tests/test_archives.py`   | Archive queries, caching, MAST searches, product downloads, and archive comparisons                      |
| `tests/test_atmosphere.py` | Atmospheric-model adapter, channel integration, abundance scans, and synthetic validation                |
| `tests/test_identify.py`   | Reference imports, source records, candidate ranking, decomposition, and attribution                     |
| `tests/test_timeseries.py` | Time-series loading, transit extraction, binning, uncertainty handling, and correlated-noise diagnostics |
| `tests/test_emission.py`   | Blackbody fitting and emission-flux interpretation                                                       |
| `tests/conftest.py`        | Shared test fixtures                                                                                     |
| `tests/check_internet.py`  | Network-check helper; not itself a `test_*.py` module                                                    |

The largest test module, `test_ecas.py`, contains tests spanning the engine and GUI. The remaining modules separate several scientific subsystems.

### Positive finding

The suite goes beyond basic smoke tests. Its test names indicate synthetic recovery tests, input-validation checks, archive-service fakes, project round trips, and regression checks for specific scientific behaviors.

Examples include:

- Recovering known gas multipliers from synthetic spectra.
- Checking line-profile normalization and limiting behavior.
- Testing transit-depth recovery with and without baseline drift.
- Verifying uncertainty propagation during spectral binning.
- Testing archive caching without repeated network access.
- Checking that an unmodeled molecule remains unexplained rather than being attributed to a decoy.
- Testing atmospheric abundance scans against injected mixing ratios.

These are appropriate testing strategies for a scientific application.

## 2. What the tests establish—and what they do not

The suite contains tests for important numerical and workflow properties. That is stronger evidence of intentional verification than relying on manual demonstrations alone.

However, the following remain unestablished:

- Whether the full suite passes in the intended environment.
- Whether optional dependencies are present in the environments where optional tests run.
- Whether network-dependent behavior works against live services.
- Whether synthetic recovery results generalize to real, instrument-processed observations.
- Whether uncertainty estimates have appropriate statistical coverage across relevant conditions.

In particular, the existence of a synthetic validation test for atmospheric abundance recovery does not establish that a real-world retrieval is calibrated. The injected model, noise assumptions, and tested parameter range matter.

## 3. Packaging and dependency reliability

The project metadata in `pyproject.toml` defines ECAS v1 as version `0.8.0`, requires Python 3.10 or later, and declares the main application dependencies:

- PyQt6
- PyQtGraph
- NumPy
- SciPy
- Astropy

Optional dependency groups cover 3D visualization, archive access, and testing. The atmospheric-model backend is handled separately through `requirements-atmosphere.txt`.

### Finding F1 — Dependency declarations need installation-level verification

The main project metadata and `requirements.txt` do not present precisely the same installation story. For example, PyVista/PyVistaQt appear in the requirements file as commented optional dependencies, while the project metadata treats 3D visualization as an optional extra. Astroquery is also represented in the archive-related dependency setup.

Multiple installation routes are not inherently wrong, but they can produce inconsistent environments if their roles are unclear.

Recommendation: establish one documented installation path for the base application, with explicit commands for optional capabilities and development tests. Verify that a clean installation of each supported configuration can import and launch the expected features.

### Finding F2 — Python-version compatibility is declared, not demonstrated

The metadata declares Python 3.10 or later. That does not prove every dependency combination or optional feature works across all those versions.

Recommendation: use the versions the project intends to support as an explicit test matrix, prioritizing the main environment and any optional backend that ECAS actively relies on.

## 4. Reliability safeguards and failure modes

Several modules have useful defensive behavior:

- Domain-specific exceptions distinguish expected errors in imports, fitting, archives, and transit analysis.
- Configuration validation checks required values and data-file availability.
- Atmospheric-model code validates mixing ratios, wavelength coverage, and uncertainty inputs.
- Time-series code checks dimensions and rejects incompatible wavelength grids.
- Archive functions wrap external-service failures and use a local cache.
- The GUI has a 2D fallback when 3D rendering is unavailable.
- Project loading checks the archive's structure and supported version.

These safeguards reduce the chance of some invalid inputs reaching numerical calculations unchecked.

### Finding F3 — Failure handling is distributed across multiple layers

The scientific modules, archive adapters, task helpers, and GUI each have their own error-handling logic. That is a reasonable separation of responsibility, but it creates a need to verify how errors propagate between layers.

For example, a failed download should not leave a partially populated dataset that appears valid; a failed fit should not display a result from an earlier dataset as though it came from the current one.

The source inspection does not establish that either failure occurs. It identifies behaviors worth exercising through integration tests.

## 5. Maintainability and code organization

The implementation has clear conceptual module boundaries, a dedicated test directory, project metadata, optional dependencies, and separate modules for many scientific concerns.

There are also some maintenance considerations:

- `tests/test_ecas.py` is large and covers numerous unrelated workflows. This can make test failures harder to locate and increase the cost of changing shared fixtures.
- Some workflows have their own threading and state-management logic in addition to the reusable task helper.
- The ZIP archive contains compiled Python caches and tooling or patch artifacts. Their presence is not a functional defect, but generated files and historical artifacts should be reviewed for repository hygiene.
- External data formats and services may change independently of ECAS, so archive adapters need tests that do not depend entirely on current live service responses.

### Finding F4 — Large cross-workflow test module creates a maintenance risk

The core test module's size is not itself a defect. However, grouping parser, physics, UI, transit, persistence, and project workflows in one file can make targeted debugging and ownership less clear.

Recommendation: consider reorganizing tests by subsystem when touching them for substantive work. Avoid a large test-only refactor solely for aesthetic reasons; keep the focus on improving failure diagnosis and isolating regressions.

## 6. Consolidated Pass F findings

| ID | Finding                                                                                           | Priority                                  |
| -- | ------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| F1 | Dependency installation routes need consistent, clean-environment verification                    | Medium                                    |
| F2 | Declared Python compatibility has not been demonstrated across versions                           | Medium                                    |
| F3 | Cross-layer error propagation and stale-result prevention need integration testing                | High for reliability                      |
| F4 | The large cross-workflow test module increases maintenance cost                                   | Low–medium                                |
| F5 | Test coverage includes meaningful synthetic and regression cases, but execution status is unknown | High to resolve before claiming readiness |
| F6 | Generated caches and tooling artifacts warrant repository-hygiene review                          | Low                                       |

## 7. Pass F conclusion

ECAS v1 has a meaningful test foundation. Its tests cover several core numerical algorithms, input-validation boundaries, archive behavior, project persistence, and integrated GUI workflows. The application also contains safeguards for invalid data, optional dependencies, and external-service failures.

The main limitation is verification status: no test results have been obtained in this review. It would be incorrect to describe the application as passing its tests, fully reliable, or ready for scientific use based on test names and source inspection alone.

The most useful next actions, if this were an active v1 stabilization effort, would be:

1. Run the complete suite in a clean, documented environment.
2. Investigate the possible covariance-scaling issue identified in Pass C.
3. Exercise failure propagation across imports, downloads, fitting, and asynchronous UI tasks.
4. Verify installation of the base application and optional capabilities.
5. Review repository hygiene when making related changes, rather than treating it as a priority functional defect.

No files have been modified, and no tests have been run.

Pass F is complete at the source-inspection level.

The remaining pass in this review sequence is Pass G — Documentation and intended behavior. It will compare the README and project documentation with the implementation, distinguish implemented capabilities from planned or aspirational ones, and consolidate the findings from Passes A–F into an overall assessment of ECAS v1 before beginning the separate Beta review.