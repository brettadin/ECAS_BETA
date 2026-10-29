# Pass D — Data ingestion, storage, and provenance

Scope: How ECAS v1 reads scientific files, interprets their contents, preserves measurements, manages downloaded data, and records the origins of scientific results.

This pass is based on source inspection. No files have been modified, and no import, download, or persistence tests have been executed.

## 1. Scientific file ingestion

The main implementation is in `app/core/tables.py`, with spectrum interpretation in `app/core/fitting.py` and light-curve handling in `app/core/transit.py`.

### Supported input formats

| Format                         | Source-level support                                                          | Important boundary                                             |
| ------------------------------ | ----------------------------------------------------------------------------- | -------------------------------------------------------------- |
| CSV and delimited text         | Commas, semicolons, tabs, and whitespace                                      | Automatic parsing may require column review                    |
| Text with metadata and headers | Comments, header lines, encoding detection, decimal commas, and `D` exponents | Ragged rows may be discarded                                   |
| FITS                           | Binary and ASCII tables via Astropy                                           | Table interpretation depends on available columns and metadata |
| JCAMP-DX                       | `XYDATA` and `XYPOINTS` with uncompressed AFFN data                           | Does not establish support for every JCAMP variant             |
| JWST `x1dints`                 | Dedicated spectral time-series loader                                         | Specific product structure is expected                         |
| Matrix CSV                     | First row holds wavelengths; first column holds times                         | The layout must match the expected convention                  |
| ORCA output                    | Dedicated parser in `app/core/parser.py`                                      | Separate from generic observation-table ingestion              |

This is a broader ingestion layer than CSV-only support. In particular, it offers a path for text-based laboratory measurements and a separate path for astronomical FITS data.

### Finding D1 — Broad file support does not guarantee correct scientific interpretation

`read_table()` converts supported files into numeric tables. `suggest_spectrum_columns()` and `build_observation()` subsequently infer which columns represent the independent variable, signal, and optional uncertainty.

This separation is useful, but automatic parsing and automatic scientific interpretation are different tasks. A file can parse successfully while its columns or units are interpreted incorrectly.

The import code records several assumptions in observation metadata, including selected columns, inferred units, signal interpretation, and import notes. That is a positive design feature.

Recommendation: retain these assumptions in the UI and exported reports, and ensure ambiguous or unsupported formats require user confirmation rather than silently proceeding.

## 2. Units and signal interpretation

### Wavelength and wavenumber

`app/core/fitting.py` detects whether the independent variable is likely wavelength or wavenumber, then converts supported input to ECAS's native representation. The conversion helpers are in `app/core/physics.py`.

The importer can use column names and header text as clues, with numerical values also informing automatic detection.

Risk: numerical ranges are not reliable unit identifiers on their own. Ambiguous columns or missing units can lead to a plausible-looking but physically incorrect spectrum.

### Absorbance, transmittance, optical depth, and normalized data

The `_convert_y()` function supports several signal modes:

- Transmittance: retained as supplied.
- Percent: divided by 100.
- Absorbance: converted using \\(T=10^{-A}\\).
- Optical depth: converted using \\(T=e^{-\tau}\\).
- Automatic normalization: divides the signal by its 95th-percentile value when the other modes are not selected.

Where supplied uncertainties are transformed alongside the signal, the implementation applies corresponding scaling or derivatives for these conversions.

### Finding D2 — Automatic normalization can remove absolute measurement information

When ECAS selects the normalization fallback, the original signal scale is discarded in favor of a continuum-relative representation. This is useful for some comparisons, but can remove information needed for quantitative work.

For example, an uncalibrated signal, a laboratory absorbance measurement, and a calibrated astronomical flux spectrum are not interchangeable simply because each can be normalized.

The code recognizes archive `FLAM` and `FNU` columns and labels them as emission flux rather than transmission data. That distinction should be preserved.

Recommendation: make the resolved interpretation explicit and inspectable for every imported dataset. Preserve the original values and units, or provide a clear record of the transformation, whenever quantitative interpretation may depend on them.

## 3. Data validation and cleaning

The ingestion modules perform several structural checks.

- `RawTable` records the numeric table, column names, source path, metadata text, and parsing notes.
- The text parser chooses the dominant row width and discards rows with different column counts, recording how many were skipped.
- `ObservedSpectrum` checks array dimensions and prepares the data for fitting.
- `SpectralTimeSeries` checks that the flux matrix matches the time and wavelength dimensions, filters invalid integrations and wavelength channels, and sorts the remaining data.
- `load_x1dints()` handles the expected JWST integration-table structures.

### Finding D3 — Silent row rejection needs careful visibility

Discarding ragged rows is a defensible way to recover some imperfect files, and the parser records the number of rejected rows. However, dropping data can also remove valid measurements if the input format has a more complex structure than expected.

Recommendation: ensure users can see parsing warnings and the number of rows retained or rejected. For high-stakes scientific analysis, retain access to the original file and make the cleaned dataset inspectable.

### Finding D4 — Structural validity is not scientific validity

A time series can satisfy its dimensional and minimum-sample requirements without having adequate signal-to-noise, reliable calibration, independent errors, or sufficient out-of-transit coverage.

Similarly, a numeric table can be structurally valid while containing the wrong units or measurement type.

These are separate validation layers. ECAS's existing checks establish some structural conditions, but should not be treated as a general certification that data are scientifically suitable for analysis.

## 4. Project storage and restoration

The project implementation is in `app/core/project.py`.

An `.ecas` file is a ZIP archive containing:

- `state.json` — project version, model conditions, gas multipliers, selected settings, notes, metadata, and dataset descriptions.
- `arrays.npz` — numerical arrays for observations, light curves, spectral time series, and transmission-depth spectra.

The loader checks the project version, reads both archive members, reconstructs the supported data objects, and raises `ProjectError` for several structural or compatibility problems.

This is an inspectable format and keeps the persisted numerical data separate from session settings.

### Finding D5 — The project does not preserve a complete reproducibility record

The saved state includes a `config_path`, but not a full snapshot of the configuration file or a verified fingerprint of the molecular line data used. The project structure also does not explicitly store a complete analysis history, such as every import decision, processing step, and fitting configuration used to produce each result.

The project module's description says that results are re-derived on load. That means reproducibility depends on the configuration and scientific inputs available when the project is reopened.

Implication: a project may preserve its observations and settings without guaranteeing bit-for-bit reproduction of earlier results on another machine or with changed scientific data.

Recommendation: consider recording the configuration contents or a versioned snapshot, scientific-data identifiers, software version, relevant processing parameters, and a structured record of the analysis steps. This would strengthen reproducibility without requiring every derived result to become a permanent authority.

## 5. External downloads and caching

`app/core/archives.py` provides NASA Exoplanet Archive and MAST lookup, product discovery, and download functions. It wraps several external-service failures in `ArchiveError` and checks expected product names for JWST spectral time-series downloads.

The archive layer also searches local directories for cached products, using product filenames and, where available, preferred path components to choose an existing file.

### Finding D6 — Cache reuse is not content verification

The cache lookup verifies that a matching file exists and is non-empty. It does not establish that the local file is byte-for-byte identical to the current archive product, nor does this lookup itself verify the file's checksum or completeness against a manifest.

A filename match can be convenient, but it is weaker than identity verification. A previously downloaded product may be replaced, incomplete, or associated with a different processing version.

Recommendation: where supported by the archive, retain product identifiers and checksums and validate them when reusing cached files. At minimum, preserve the source product URI, filename, retrieval time, and local path in project metadata.

This is a resilience and provenance concern; the inspected code does not prove that cache corruption has occurred.

## 6. Citation and provenance infrastructure

`app/core/sources.py` contains a source registry with source type, title, authors, year, DOI or URL, licensing notes, citation guidance, and a verification flag.

Its `CitationLog` records:

- The source key.
- A detail identifying the relevant dataset or target.
- Retrieval timestamp in UTC.
- The query or URL used.
- A row count, where applicable.

It can generate Markdown references and BibTeX entries. The registry also distinguishes mock data from actual measurements and records caveats for sources such as NIST and ExoMol.

This is a strong foundation for scientific attribution. The registry's `verified` flag is specifically about whether an identifier or citation was checked when the entry was written; it does not validate the scientific suitability of the data.

### Finding D7 — Citation infrastructure and project persistence are not fully connected

The citation log is capable of preserving useful provenance, but the `.ecas` project structure inspected in `project.py` does not explicitly serialize the `CitationLog` records as a first-class project field.

That creates a potential gap: a session may use the citation infrastructure, yet its saved project may not retain the complete list of sources actually used.

The source registry's existence alone does not establish that every external download, imported reference, or analysis result is automatically logged.

Recommendation: connect provenance records to imported datasets and saved projects. Each dataset should retain a stable source identity and retrieval details, while each analysis should record the relevant input datasets and processing settings.

## 7. Consolidated Pass D findings

| ID | Finding                                                                                              | Priority                        |
| -- | ---------------------------------------------------------------------------------------------------- | ------------------------------- |
| D1 | Automatic column and unit interpretation can be wrong even when parsing succeeds                     | High for reliability            |
| D2 | Automatic normalization can discard absolute measurement scale                                       | High for quantitative workflows |
| D3 | Ragged rows may be discarded during text parsing                                                     | Medium                          |
| D4 | Structural validation does not establish scientific data quality                                     | High for interpretation         |
| D5 | Saved projects do not guarantee reproduction against changed configurations or scientific inputs     | High for reproducibility        |
| D6 | Cache reuse is based on file matching and non-empty files, not comprehensive content verification    | Medium                          |
| D7 | Citation logging is implemented, but complete persistence and automatic coverage are not established | High for provenance             |

These findings describe different types of risk. D1–D4 concern data interpretation and suitability; D5 and D7 concern reproducibility and traceability; D6 concerns downloaded-data integrity.

## Pass D conclusion

ECAS v1 has a reasonably capable data-ingestion layer, support for both laboratory-style and astronomical formats, structured project storage, archive-download caching, and a dedicated citation registry.

Its main data-management weakness is not the absence of these components, but the gap between having the components and guaranteeing an auditable scientific workflow. In particular, project files do not appear to preserve all the information needed to reproduce every analysis independently, and automatic data interpretation requires visible assumptions and warnings.

No confirmed data-loss or cache-corruption incident has been established. The findings identify where the implementation should be tested or strengthened.

Pass D is complete at the source-inspection level. No files have been modified, and no tests have been run.

The next pass is Pass E — UI and usability: how the application presents analysis state, exposes import assumptions, handles errors and long-running tasks, and communicates the difference between exploratory results and scientifically interpretable outputs.