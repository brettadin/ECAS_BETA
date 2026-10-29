# ECAS Beta Review — Pass B: Functional Capabilities and Workflows

Review basis: source code, README, project-state documentation, and test-file inventory in the supplied Beta archive. This remains a read-only review. I have not run the application or tests, and I will distinguish implementation evidence from historical verification claims.

The key question for this pass is not simply what ECAS contains, but which workflows are usable, which are constrained, and which are still planned or blocked.

## 1. Current application workflow

The source and documentation indicate that Beta has moved beyond a basic spectral viewer. It now contains distinct workflows for importing spectra, managing research projects, discovering NASA archive records, browsing molecular references, and preparing observation/reference comparisons.

1\. Import and inspect

Import supported CSV data, validate its structure, view the spectrum and inspect the imported data.

2\. Organize observations

Create projects, save spectra, reopen saved records and retain source-related metadata.

3A. NASA archive

Search for astronomical observations, inspect records, retrieve supported products and reopen cached data.

3B. Molecular references

Browse ExoMol catalogue records, retrieve selected supported cross sections, and inspect cached references.

4\. Prepare comparisons

Select observation and reference inputs, inspect their metadata and compatibility, and use the available comparison/model-preparation code where its requirements are met.

This is a conceptual workflow map, not a claim that every stage automatically feeds the next or that a scientific conclusion can be generated.

The critical limitation is at the final stage: data inspection and model-preparation features exist, but they do not by themselves establish that ECAS can identify molecules in an exoplanet atmosphere.

## 2. Local spectrum import and inspection

Relevant modules: `ecas/ingestion/csv_importer.py`, `ecas/ingestion/import_manager.py`, `ecas/models/spectrum.py`, `ecas/ui/main_window.py`, and `ecas/visualization/spectra_plot.py`.

The import workflow has two main paths:

- Generic CSV: expects recognizable wavelength and signal columns.
- WASP-39 b archive CSV: uses an explicit schema mapping `centralwavelng` to wavelength and `pl_trandep` to signal. The importer retains source columns and appends canonical columns.

The import manager rejects unsupported file extensions rather than silently treating them as CSV. The UI also exposes a session-level CSV schema choice.

### Limitations

- Arbitrary X/Y column selection is not implemented in the documented generic importer.
- The WASP-39 b importer is schema-specific, not universal support for NASA or other archive CSV files.
- The documented import manager does not provide general TXT-spectrum import support.
- Successful parsing does not establish correct scientific units, measurement type, calibration, or suitability for comparison.

Finding B1 — Import flexibility remains limited. This is an explicit limitation in the current project-state records, not merely a possibility inferred from the interface. For research files with nonstandard column names or text formats, import compatibility must be assessed individually.

The separate tabular-format and comparison-input modules provide additional representations and conversion capabilities. Their existence does not mean the basic CSV importer can accept every such representation directly.

## 3. Research projects and persistence

Relevant modules: `ecas/projects.py`, `ecas/persistence.py`, and `ecas/ui/project_browser.py`.

The project workflow supports:

- Creating and selecting projects.
- Attaching the currently displayed spectrum or a cached spectrum.
- Saving spectrum records and associated source information.
- Reopening saved records.
- Saving and listing comparison records through project-level operations.

The implementation includes source-byte hashing and verification helpers. The project-state document also describes versioned attachments and compatibility with older records that lack provenance.

Finding B2 — Project management is implemented, with bounded guarantees. The source supports a real project workflow rather than only a placeholder page. However, integrity checks do not establish that the original scientific data are authentic, that all external metadata are complete, or that a scientific analysis can be reproduced in every case.

The distinction matters: a saved record can be recoverable and internally consistent without containing all the information required to reproduce a scientific result.

## 4. NASA archive discovery and retrieval

Relevant modules: `ecas/ingestion/nasa_aliases.py`, `nasa_discovery.py`, `nasa_network.py`, `nasa_archive.py`, `nasa_table.py`, `planet_resolver.py`, and `ecas/ui/nasa_browser.py`.

The documented workflow supports astronomical target-name resolution, archive searching, inspection of available records, and retrieval of supported transmission-table products. Cached products can be reopened offline, and the code includes source metadata and validation paths.

The project-state records describe successful earlier checks for targets such as WASP-39 b and TRAPPIST-1 e, including returned record counts. Those are historical verification claims; I have not reproduced the network or desktop checks in this review.

### Limitations

- Archive search results depend on the provider's available inventory; an empty result does not prove that no observations exist anywhere.
- The documented NASA table path does not establish general FITS support.
- Support for one retrieved product does not establish support for all NASA product formats.
- Network retrieval and cached-file reopening are workflow capabilities, not scientific validation of the retrieved measurements.

Finding B3 — NASA support is source- and format-specific. Beta has a substantially more developed archive workflow than a manual-only import path, but it should not be described as a universal astronomical-data importer.

## 5. Molecular references and ExoMol

Relevant modules: `ecas/ingestion/exomol_catalogue.py`, `exomol_catalogue_cache.py`, `exomol_cross_section.py`, `exomol_product.py`, `exomol_product_network.py`, `exomol_reference_cache.py`, and `ecas/ui/molecular_browser.py`.

The molecular-reference workflow separates catalogue discovery from supported product retrieval.

Catalogue search

Search cached or bundled molecular catalogue metadata by name, formula, isotope or dataset identifier. A catalogue result is not proof that a compatible spectrum is available.

Supported reference retrieval

The documented supported datasets are CO₂ / UCL-4000, H₂O / POKAZATEL, and CH₄ / MM, each with bounded retrieval and calculation settings.

Inspection and caching

Display the calculated cross section separately, preserve reference provenance, and reopen validated cached data offline.

The documented calculation is a zero-pressure, Doppler-only cross section with user-selected reference temperature and spectral range. Those settings do not represent inferred atmospheric conditions for a particular planet.

Finding B4 — Molecular-reference access is real but deliberately narrow. Catalogue discovery covers more entries than product retrieval. The three documented supported datasets should not be generalized into support for all ExoMol molecules or products.

A retrieved molecular cross section also cannot, on its own, establish molecular presence in an observed exoplanet atmosphere.

## 6. Comparisons and atmospheric model preparation

This is the most important functional area to assess carefully because the source code and documentation have evolved at different rates.

Relevant modules: `ecas/ui/comparison_browser.py`, `ecas/comparison/inputs.py`, `eligibility.py`, `alignment.py`, `model_adapters.py`, `model_generator.py`, `forward_model.py`, `candidates.py`, `residuals.py`, and `persistence.py`.

### What the source contains

- Independent observation and reference selections.
- Input metadata and eligibility checks.
- Explicit axis and signal-unit conversion routines.
- Restrictions on incompatible inputs and unsupported transformations.
- Top-hat integration of forward-model values into observational bins, without extrapolating outside model coverage.
- A 1D isothermal hydrostatic transmission-model generator.
- Leave-one-out multi-molecule sensitivity calculations.
- Residual diagnostics, comparison records, and methods to save and reproduce selected comparisons.

These are substantive implementations, not just proposed module names. However, the existence of these routines does not prove that every workflow is accessible, correctly integrated, or scientifically validated.

### Important scientific boundaries

The eligibility module explicitly distinguishes an eligible residual diagnostic from detection significance. Its weighted mode requires uncertainty evidence and an explicit declaration of cross-dataset independence; it checks covariance rather than estimating it.

The alignment code also makes some transformations explicit rather than silently changing data. For example, it restricts axis conversions to supported units and only permits top-hat bin integration on inputs identified as forward models.

These are sensible safeguards in the implementation. They do not establish that the physical model adequately represents a real exoplanet atmosphere, that the observational response is fully characterized, or that molecular attribution is reliable on real data.

### Finding B5 — Comparison capabilities are more advanced than the README describes

The README still describes Comparisons as an inspection-only workflow and says that analysis is not implemented. Meanwhile, the current source contains forward-model generation, model alignment, eligibility assessment, residual diagnostics, and related UI workflows.

The project-state document also records these more recent additions. This is a documentation-to-implementation discrepancy: the README needs to distinguish the current implemented model-preparation and diagnostic capabilities from the still-unestablished scientific conclusions.

I would not yet label the full comparison workflow scientifically complete. That requires closer review of the numerical methods and integration, which belongs in Pass C.

## 7. Other workspace and reference features

The source includes dedicated pages for Overview, Settings, Projects, NASA, Molecular References, Comparisons, and Resources.

- Overview and Settings: provide workflow shortcuts, a summary of current session state, read-only storage paths, and the session CSV-schema choice.
- Resources: provides a catalogue of scientific software, archives, molecular databases, and related resources.
- Plotting: spectrum, reference, and residual plots are implemented separately. The documentation describes independent axes for native-unit inspection; these plots should not be mistaken for a shared-scale scientific comparison.
- Source links and metadata: provide ways to inspect or open source information, but their presence alone does not guarantee complete provenance for every record.

These features make Beta more useful as a research workspace, even where the underlying scientific workflow remains incomplete.

## 8. Test inventory versus verified behavior

The archive contains a broad test suite covering imports, projects, persistence, NASA discovery and retrieval, ExoMol catalogue and product handling, comparison alignment and eligibility, plotting, UI workflows, and regressions.

The project-state document reports 622 passed and 22 skipped for a run dated October 29, 2026. That is a recorded result, not a result independently reproduced in this review.

For this pass, I have not executed tests or performed live network checks. I therefore cannot claim that the current archive passes that suite. Pass F will examine the test organization, coverage claims, historical run records, and reliability concerns in detail.

## 9. Pass B findings summary

| ID | Finding                                                                                                                                     | Status                                     |
| -- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| B1 | Generic CSV import remains constrained by recognizable columns; archive CSV support is schema-specific.                                     | Confirmed limitation                       |
| B2 | Project creation, attachment, persistence, and reopening are implemented, with bounded integrity/provenance guarantees.                     | Source-supported capability                |
| B3 | NASA discovery and retrieval support specific workflows and formats, not universal archive ingestion.                                       | Source-supported capability and limitation |
| B4 | ExoMol catalogue discovery is broader than the three documented supported product datasets.                                                 | Source-supported limitation                |
| B5 | Comparison/model-preparation code is more developed than the README's inspection-only description suggests.                                 | Confirmed documentation discrepancy        |
| B6 | The presence of model generation and diagnostics does not establish validated molecular detection or reliable atmospheric characterization. | Scientific-validation boundary             |
| B7 | The project reports extensive automated testing, but the current archive's suite has not been independently run here.                       | Verification status                        |

## 10. Discussion before Pass C

The main point to settle from this pass is the current status of the Comparisons workflow.

The source has advanced beyond simple visual inspection, but the README and some historical project-state entries still describe earlier stages. We should preserve that distinction rather than either understating the implementation or declaring the scientific analysis complete.

Pass C will examine the numerical and scientific implementation in more detail, especially:

- The transmission forward model and its assumptions.
- Unit conversions, spectral alignment, and bin integration.
- Eligibility rules and uncertainty handling.
- Leave-one-out molecular sensitivity and residual diagnostics.
- Whether the implementation's outputs support the interpretations the UI might encourage.

I will wait for your discussion or approval before proceeding to Pass C.