# ECAS v1 and Beta Comparison — Category 2
## Functional Capabilities and Workflows

**Scope:** Compare the user-facing and scientific workflows available in ECAS v1 and ECAS Beta, distinguishing established functionality from partial implementations, restricted support, and capabilities that remain unverified.

**Evidence basis:** The supplied v1 and Beta source archives, their README and project-state documentation, and the findings from the respective seven-pass reviews. This is a source-based assessment; no new application execution or tests were performed for this category.

---

## 1. Executive Assessment

ECAS v1 already provides substantial spectroscopy and transit-analysis functionality. Its workflows include importing and inspecting spectra, identifying absorption features, fitting gas multipliers, retrieving astronomical observations, analyzing transit light curves, extracting wavelength-dependent transit depths, and optionally generating atmospheric forward spectra through petitRADTRANS.

ECAS Beta develops a different part of the overall research workflow. Its emphasis shifts toward structured scientific-data ingestion, NASA archive discovery and retrieval, molecular-reference catalogue search and selected product downloads, persistent project data, observation/reference selection, compatibility checks, comparison preparation, residual diagnostics, and a restricted transmission forward model.

The progression is therefore not simply from fewer features to more features. **V1 offers a broader integrated spectroscopy and transit-analysis experience, while Beta develops stronger data-management and comparison-preparation infrastructure.** The two versions have different strengths, and Beta's additional comparison-related code must not be mistaken for a complete, validated molecular-detection or atmospheric-retrieval workflow.

## 2. Side-by-Side Capability Matrix

| Capability | ECAS v1 | ECAS Beta | Assessment |
|---|---|---|---|
| Spectral-file ingestion | CSV, TSV, delimited text, FITS tables, and JCAMP-DX, with column/unit interpretation and correction through the import dialog. | Generic CSV support, a schema-specific WASP-39b archive route, scientific tabular formats including ECSV and selected FITS tables, and scientific delimited-text handling in the reviewed source. | Both support ingestion, but through different paths and restrictions. Beta's broader source-specific data infrastructure is an advancement; neither version should be assumed to accept every scientific file. |
| Spectral visualization | Spectroscopy and Identify workflows, absorption-feature inspection, and plotting. | Separate observation and reference inspection, native-unit plots, tables, and metadata displays. | Beta improves separation and traceability of observation/reference inspection; v1 retains its integrated spectroscopy workflow. |
| Molecular feature identification | Peak identification and matching against known bands; gas fitting against configured model spectra. | Reference catalogue discovery and product retrieval, but no established production molecular-detection result. | V1 provides direct feature-identification functionality. Beta improves access to molecular reference data but does not establish that a molecule has been detected in an observation. |
| Gas fitting | Fits gas multipliers and can fit continuum level/tilt against configured model coverage. | Comparison preparation and forward-model generation are present in source, but these do not establish an equivalent, general-purpose gas-fitting workflow. | V1 has a more explicit integrated fitting workflow. The methods and scientific meaning differ, so these features are not directly interchangeable. |
| Transit analysis | Planet lookup, TESS light-curve retrieval, JWST spectral time-series retrieval, transit analysis, synchronized visualization, and extraction of measured transit depths. | The reviewed Beta workflow centers on spectral observations and reference products. An equivalent integrated transit-analysis and time-series visualization workflow was not established by the Beta review. | V1 has the stronger documented integrated transit workflow. Beta should not be assumed to replace it. |
| Atmospheric forward modeling | Optional petitRADTRANS 3 clear-atmosphere forward spectrum and a conditional one-dimensional gas-abundance profile scan, with explicitly stated limitations. | A native one-dimensional isothermal hydrostatic transmission forward model, including molecular absorption, continuum contributions, optional gray clouds, and restricted sensitivity diagnostics; external-model adapter boundaries are also present. | Both include model-related functionality. Beta adds an in-package model implementation, but this does not establish that it is more physically complete or empirically more accurate than the optional v1 backend. |
| Astronomical archive access | TESS and JWST product search/download through MAST for supported workflows, with caching and archive provenance. | Dedicated NASA target resolution, archive discovery, supported transmission-table retrieval, cached source metadata, and integrity checks. | Beta has more explicit archive-data management and validation boundaries. The precise product coverage differs. |
| Molecular-reference access | Configured spectral models, gas data, and NIST IR/UV-Vis JCAMP reference browsing. | ExoMol catalogue search and bounded product retrieval for CO₂/UCL-4000, H₂O/POKAZATEL, and CH₄/MM in the reviewed state. | Beta provides a more explicit catalogue-to-product workflow and persistent reference cache. Supported retrieval is restricted to documented mappings. |
| Observation/reference comparison | A molecular-comparison workspace using a relative pseudo-transmittance, with known limitations and no absolute abundance result. | Observation/reference selection, compatibility eligibility, alignment, residual diagnostics, candidate handling, and forward-model comparison preparation are present in the reviewed source. | Beta advances the structure and explicit safeguards of comparison preparation. The completeness of the production workflow remains a separate question. |
| Uncertainty and residual diagnostics | Measured transit-depth uncertainties, optional inverse-variance channel binning, residual/χ² diagnostics for the optional model overlay, and a time-correlated-noise diagnostic. | Explicit uncertainty and independence assumptions for weighted diagnostics, response-aware alignment, residual summaries, and Cholesky-whitened weighted diagnostics where supported. | Beta makes more comparison assumptions explicit. Neither set of diagnostics alone establishes calibrated statistical evidence or a validated uncertainty model. |
| Project persistence | `.ecas` project archives preserve state and relevant arrays; v1 documents preservation of downloaded spectral time series and archive provenance. | SQLite-backed project management, attachments, source hashes, metadata, integrity digests, and source-specific cache validation. | Beta provides more structured project and source-integrity mechanisms. The exact guarantees differ by data source and workflow. |
| Reporting and export | CSV, Markdown report, and PNG export are documented. | Structured project/reference storage and inspection workflows are documented; equivalent parity across all v1 export and reporting features was not established in the Beta review. | V1 has explicitly documented reporting/export workflows. Beta's equivalent end-user coverage needs separate verification. |

## 3. Functional Progression by Workflow

### 3.1 Importing and inspecting scientific data

**V1 baseline**

V1 supports several spectroscopy input formats and an import dialog that allows the user to review detected columns, wavelength/wavenumber units, and signal scaling. It also distinguishes transmission-like data from archive emission-flux data, with limitations on which analyses are permitted for each measurement type.

**Beta state**

Beta adds more explicit scientific-data structures and ingestion routes. Its scientific tabular importer supports ECSV, delimited scientific text, and a restricted FITS binary-table path. It also preserves information about source identity, units, observable type, coordinate frame, response metadata, and uncertainties where available.

The generic CSV route still requires recognizable wavelength and signal columns. The schema-specific archive importer requires its expected schema; arbitrary user-selected X/Y column mapping is not implemented.

**Assessment**

Beta's advancement is not universal file compatibility. It is stronger organization of the imported information and clearer boundaries for deciding whether data can be used in a later analysis.

The review does not establish that every FTIR, UV-Vis, or laboratory file can be imported directly. Compatibility depends on the file format, table structure, axis and signal representation, and available metadata.

### 3.2 Accessing astronomical observations

**V1 baseline**

V1 integrates planet lookup with MAST product retrieval for supported TESS photometry and JWST spectral time-series workflows. It supports transit analysis and, for suitable JWST spectral time series, extraction of wavelength-dependent transit depths. The documented extraction path has minimum-data requirements.

**Beta state**

Beta's NASA workflow emphasizes target resolution, archive discovery, supported transmission-table retrieval, cache validation, and source metadata. These are useful for bringing archive products into a controlled data-management workflow.

**Assessment**

Beta strengthens the infrastructure surrounding archive data. However, the reviewed evidence does not establish equivalent end-to-end parity with v1's transit light-curve analysis, synchronized transit visualization, and spectral time-series extraction.

These should be treated as distinct workflow capabilities rather than assuming one supersedes the other.

### 3.3 Accessing molecular references

**V1 baseline**

V1 supports configured gas reference spectra and NIST JCAMP reference browsing for IR and UV/Vis. Its feature-identification and fitting workflows can use those references within their supported spectral ranges and measurement assumptions.

**Beta state**

Beta adds a dedicated molecular-reference catalogue workflow, including catalogue search, explicit refresh and cancellation, selected product downloads, cached cross sections, provenance, and offline reopening.

The reviewed Beta implementation supports a bounded set of ExoMol products:

- CO₂ — UCL-4000
- H₂O — POKAZATEL
- CH₄ — MM

Catalogue discovery is broader than supported product retrieval. Finding a molecule in the catalogue does not mean ECAS can download every associated dataset or establish that a retrieved reference is compatible with a given observation.

**Assessment**

This is a meaningful Beta advancement in reference-data acquisition and management. It expands the foundations needed for reproducible comparison without, by itself, delivering molecular detection.

### 3.4 Comparing observations and references

**V1 baseline**

V1 has a molecular-comparison workflow, but its README explicitly describes the comparison as using a relative pseudo-transmittance and states that it does not return atmospheric abundances. Its comparison results therefore require careful interpretation.

**Beta state**

Beta introduces a more structured comparison-preparation pipeline. The reviewed source includes:

- Observation and reference selection.
- Eligibility checks for supported measurement types and metadata.
- Wavelength/wavenumber alignment and unit conversion.
- Explicit handling of selected transit-depth representations.
- Response-aware bin integration without extrapolation.
- Residual diagnostics and conditional weighted diagnostics.
- Candidate handling and leave-one-out model sensitivity.
- A restricted transmission forward-model generator.

However, the Beta README describes Comparisons as supporting inspection and selection while stating that analysis is not implemented. Project-state documentation also contains historical checkpoints that describe production comparison as outstanding. The reviewed source contains comparison-related calculations, but their presence does not resolve the status of a complete, accepted production workflow.

**Assessment**

Beta has more explicit comparison infrastructure and scientific safeguards. The strongest supported conclusion is that it advances comparison preparation and restricted model-based analysis.

It would be inaccurate either to say that Beta has no comparison-related calculations or to claim that it provides a fully validated production comparison, retrieval, or molecular-detection system.

### 3.5 Atmospheric modeling and interpretation

**V1 baseline**

V1 documents an optional petitRADTRANS-based clear-atmosphere transmission model and a conditional one-dimensional gas-abundance scan. It explicitly states that the scan does not marginalize over other parameters, and that the model does not include instrument line-spread convolution or correlated-noise likelihoods.

**Beta state**

Beta includes a native one-dimensional isothermal hydrostatic transmission forward model with molecular absorption, an H₂/He background, optional gray-cloud treatment, and leave-one-out sensitivity diagnostics. Its external-model adapter structures also define an import/provenance boundary for several other modeling packages, but live integration with those packages was not established by the review.

Beta's residual diagnostics can summarize differences between observations and models. Weighted diagnostics require explicit assumptions about uncertainties and independence. They are not, by themselves, calibrated p-values, Bayesian evidence, or proof of molecular detection.

**Assessment**

Beta broadens the available model-preparation infrastructure. The available evidence does not support a blanket claim that its model is more scientifically complete or more accurate than v1's optional backend. The models have different implementations and assumptions, and neither version's reviewed capabilities establish end-to-end empirical validation.

### 3.6 Persistence and reproducibility

**V1 baseline**

V1 supports native `.ecas` project save/open behavior and documents preservation of downloaded wavelength-by-time data and archive provenance for its relevant transit workflow.

**Beta state**

Beta uses SQLite-backed project management and structured storage for observations, attachments, source metadata, hashes, and integrity checks. Its NASA and ExoMol caches preserve source-specific provenance and verify defined integrity conditions when data are reopened.

**Assessment**

Beta provides a stronger and more explicit foundation for organizing research inputs and preserving data identity. However, integrity checks do not authenticate a scientific provider or validate the calibration and physical meaning of a dataset. Reproducibility also depends on recording the methods, assumptions, settings, and derived results for each analysis.

## 4. Important Limitations and Non-Equivalences

The following distinctions should be retained in any overall assessment:

1. **Feature identification is not molecular detection.** Identifying a spectral feature or matching it to a reference is not sufficient to establish the presence of a molecule in an exoplanet atmosphere.

2. **A forward model is not a retrieval system.** Generating a spectrum under specified atmospheric assumptions does not establish that the model has inferred the atmosphere's actual composition.

3. **Comparison preparation is not a complete scientific comparison workflow.** Selection, eligibility, alignment, and residual calculations are important capabilities, but production status and scientific acceptance must be established separately.

4. **Archive access is not universal product support.** Both versions have constraints on product types, formats, and analysis paths. Beta's ExoMol catalogue is broader than its implemented download mappings.

5. **Successful parsing is not scientific compatibility.** Units, observable type, calibration, spectral coverage, instrument response, uncertainties, and covariance conventions can affect whether two datasets can be compared meaningfully.

6. **Persistence and hashes are not scientific validation.** They help preserve and verify defined data-integrity properties, not establish empirical accuracy.

7. **A larger codebase does not guarantee greater practical capability.** Beta's new subsystems must be assessed by the workflows users can actually complete, not merely by the existence of modules or functions.

## 5. Category 2 Findings

| Classification | Finding |
|---|---|
| Improved | Structured comparison preparation, explicit compatibility checks, source-aware data handling, and molecular-reference cache workflows. |
| Expanded | NASA archive management, ExoMol catalogue/product access, structured persistence, and restricted native forward modeling. |
| Retained strength from v1 | Integrated spectroscopy, feature identification, configured gas fitting, transit analysis, and optional petitRADTRANS modeling. |
| Restricted or incomplete in Beta | General CSV column mapping, broad molecular-reference product retrieval, and a complete accepted production comparison/retrieval workflow. |
| Not established | Full parity with v1's integrated transit workflow, universal scientific-file support, general external-model integration, and empirical scientific validation. |
| Confirmed regression | None established by the reviewed evidence. A missing or unverified equivalent workflow is not automatically a regression. |

## 6. Category 2 Verdict

**Assessment: Beta expands the research-data and comparison-preparation workflow, but does not demonstrably supersede every integrated scientific workflow in v1.**

Beta's principal functional advances are its structured source-data workflows, reference catalogue and product handling, comparison eligibility and alignment infrastructure, richer provenance, and restricted forward-model generation. These make it better equipped for controlled development of reproducible observation/reference comparison.

V1 nevertheless has established documented workflows that should not be overlooked, particularly its integrated spectroscopy, molecular feature-identification and fitting tools, transit light-curve analysis, spectral time-series extraction, and optional petitRADTRANS modeling.

The most defensible overall interpretation is that Beta advances ECAS toward a more structured research platform, while the completeness, acceptance, and scientific validity of its newer comparison workflows remain separate questions. The evidence does not establish that Beta is a drop-in replacement for every v1 capability.

**Confidence:** Moderate for the high-level capability differences, based on the supplied source snapshots and existing reviews. Lower for direct workflow parity and runtime behavior because no fresh interactive tests were performed for this category.

---

## Review Sources and Audit Trail

The comparison is part of the review-document collection under:

`docs/ecas v1 and beta comparison documents/`

Relevant source records:

- `ecas_v1_pass_0.md` — initial v1 review planning.
- `ecas_v1_pass_A.md` through `ecas_v1_pass_G.md` — v1 review evidence.
- `ecas_beta_pass_0.md` — initial Beta review planning.
- `ecas_beta_pass_A.md` through `ecas_beta_pass_G.md` — Beta review evidence.
- `10_29_26_ecas_beta_review_initial.md` — earlier comprehensive Beta review, conducted before the structured seven-pass review.
- `comparison_cat_1.md` — architecture and application structure comparison.
- `comparison_cat_2.md` — this document.

The original reviews and the earlier comprehensive Beta review are separate evidence records. Conflicting descriptions of implementation status should be investigated rather than silently reconciled. The final synthesis should distinguish source observations, documentation claims, historical status records, and capabilities not independently verified.