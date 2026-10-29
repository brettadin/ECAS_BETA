# Pass B — Functional capabilities and workflows

Scope: What ECAS v1 actually implements, how its main workflows connect, and where documented capabilities stop. This pass is based on the archived source and documentation; it does not establish that every workflow runs correctly in a live environment.

## 1. Spectroscopy workflow

Import spectra

`app/core/tables.py`, `app/core/fitting.py`

Imports support text-based tables and CSV/TSV, FITS tables, and JCAMP-DX. The importer can suggest columns, recognize wavelength units, and convert supported signal representations.

Model and fit

`app/core/engine.py`, `physics.py`, `fitting.py`

Builds modeled spectra, adjusts gas multipliers against observations, and supports baseline level and tilt fitting.

Identify features

`app/core/identify.py`, `library.py`

Finds absorption features, ranks reference spectra, and supports decomposition into candidate molecular components.

Export results

`app/core/export.py`

Exports modeled spectra, fits, anomalies, transmission-depth spectra, and Markdown reports.

### Important limitations

- The built-in simulated molecular bands cover approximately 400–4200 cm⁻¹ and represent fundamentals. A real spectrum outside that range needs overlapping reference/model coverage; the built-in model cannot identify every possible band.
- Molecular candidate matching and fitted gas multipliers are not automatically equivalent to a validated chemical identification or an absolute concentration measurement.
- NIST UV/Vis references can be imported as relative spectral shapes. Their shape alone does not establish concentration because measurement conditions such as solvent, path length, and concentration affect the spectrum.
- Archive flux data are treated as emission data when recognized as `FLAM` or `FNU`; normalizing flux does not turn it into a transmission spectrum.
- Blackbody continuum fitting estimates a color-temperature baseline with arbitrary scale. It does not determine luminosity, planetary radius, or atmospheric composition.

These limitations are explicitly described in the v1 README. They should be preserved when assessing the scientific meaning of results.

## 2. Transit and transmission-spectrum workflow

The transit workflow is implemented across `app/core/transit.py`, `app/core/timeseries.py`, and `app/ui/transit_panel.py`.

1. Find a planet and its observations. `archives.py` queries planetary data and searches MAST for relevant observations and downloadable products.
2. Load or analyze a light curve. `transit.py` provides transit modeling, detrending, period-search logic, fitting, and derived transit parameters.
3. Load wavelength-resolved time series. `timeseries.py` supports matrix CSV input and JWST `x1dints` FITS data, with validation of the time and wavelength dimensions.
4. Extract a transmission spectrum. The analysis derives wavelength-dependent transit depths and uncertainties, with optional adjacent-channel binning.
5. Compare against molecular references or a physical model. The extracted spectrum can be sent to the Identify workflow or compared with an optional `petitRADTRANS` forward model.

### Confirmed boundaries

- Broadband TESS photometry supports light-curve analysis, but cannot independently produce a wavelength-resolved transmission spectrum.
- The README explicitly says UV/Vis HST spectral extraction is not supported.
- Spectral time-series analysis requires at least 50 usable integrations and 8 wavelength channels.
- The molecular-comparison workflow converts measured transit depths into a continuum-relative pseudo-transmittance. It does not return validated absolute atmospheric abundances.
- The optional physical atmosphere model is a simplified clear, isothermal atmosphere with constant gas volume mixing ratios and an H₂/He background.
- The abundance scan varies one selected gas while holding the other atmospheric inputs fixed. Its output is explicitly exploratory, not a posterior distribution or calibrated abundance measurement.
- The correlated-noise tool is a diagnostic. It does not correct the reported transit-depth uncertainties or replace instrument/systematics modeling.

These are important scientific boundaries, not necessarily implementation defects. They prevent the existence of a feature from being mistaken for evidence that it produces a fully validated scientific result.

## 3. External data and reference libraries

ECAS v1 has several separate routes for obtaining scientific inputs:

| Component                      | Role                                                                                 |
| ------------------------------ | ------------------------------------------------------------------------------------ |
| `app/core/archives.py`         | Planet queries, MAST observation searches, product discovery, downloads, and caching |
| `app/core/molecule_sources.py` | Fetching or loading molecular data from supported sources                            |
| `app/core/library.py`          | Reference spectra, NIST JCAMP imports, and other molecular-reference handling        |
| `app/core/spectral_sources.py` | Spectral datasets and preparation of analysis inputs                                 |
| `app/core/sources.py`          | Citation records and provenance logging                                              |

The archive layer uses network requests and supports caching downloaded products. The documentation says previously downloaded products are reused from `~/.ecas/cache`.

The existence of these pathways is confirmed by the source. Successful operation still depends on external services, accessible products, compatible formats, and any required optional packages. I have not tested live network retrieval during this review.

## 4. Saving, restoring, and exporting work

The application exposes project save/open operations and several export formats through the main window.

The source establishes these capabilities:

- Save and restore `.ecas` project state.
- Export model spectra, fitting results, anomalies, and transmission-depth spectra as CSV.
- Generate a Markdown report.
- Export a PNG from the interface.

The workflow review has not yet established that every possible combination of datasets and analysis state survives a save/reopen cycle without loss. That belongs in the persistence and reliability review, including tests for round-trip consistency.

## 5. Test coverage visible in the archive

The archive includes tests for archives, atmospheric modeling, emission fitting, identification/reference libraries, and spectral time series. The inspected tests include synthetic-data checks for transit-depth extraction, uncertainty propagation during binning, correlated-noise diagnostics, reference-spectrum imports, and physical-model comparison.

That is evidence of targeted unit and integration-style test coverage in several scientific areas. It is not evidence that the whole application passes its test suite: I have not run the tests, and a source archive containing test files cannot establish their current pass status.

## 6. Pass B assessment

What is established

- ECAS v1 implements distinct spectroscopy and transit-analysis workflows.
- It supports several practical scientific file formats and multiple external data pathways.
- It includes molecular-reference matching, fitting, project persistence, reporting, and optional atmospheric forward modeling.
- The documentation makes several meaningful distinctions between exploratory analysis and scientifically calibrated results.

What remains unverified

- Whether each documented workflow functions end to end.
- Whether errors, missing data, and network failures are handled consistently.
- Whether scientific calculations and uncertainties are sufficiently validated for their intended uses.
- Whether project persistence and provenance remain complete across real workflows.
- Whether the test suite passes in a supported environment.

Pass B is complete at the source-inspection level. No files have been modified, and no tests have been run.

The next pass should focus on scientific and numerical implementation: the physical assumptions, fitting methods, transit calculations, uncertainty treatment, and limits of interpretation. That is where we can distinguish implemented calculations from claims that would require further scientific validation.