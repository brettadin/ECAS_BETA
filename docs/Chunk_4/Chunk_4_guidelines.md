# ECAS Chunk 4 — Archive and Molecular Reference Integration: Initial Investigation



**Mode: PLAN ONLY. Do not implement, edit files, install packages, or modify project documents.**

## Context

Project: ECAS — Exoplanetary Characterization & Astrochemistry Suite.

Repository: https://github.com/brettadin/ECAS_BETA

Chunks 2 and 3 are complete. The current application has a `SpectrumData` model, CSV import, SQLite persistence, a PySide6 UI, and a PyQtGraph plotting widget.

Chunk 4 is defined in `docs/ECAS_development_plan.md` as Online Archive Integration.

Its stated goals include:
- Investigating suitable scientific archives and APIs.
- Implementing source-specific providers behind a common interface.
- Preserving identifiers, citations, retrieval details, and source metadata.
- Caching retrieved data for reproducible offline access.

Completion criterion: ECAS can retrieve and register a real archival dataset with traceable provenance.

**Important scientific context:** ECAS ultimately needs both astronomical observations and molecular reference spectra. These are distinct types of data from different sources and must not be treated as interchangeable.

Potential sources include:
- NASA Exoplanet Archive and MAST for exoplanet identities, observations, and astronomical spectral data products.
- NIST Chemistry WebBook for molecular reference spectra, including infrared and UV/Vis data where available.
- HITRAN for molecular spectroscopic transition data, especially infrared applications.

The first implementation should remain small and evidence-based. We are investigating which source or sources are most practical for an initial proof of concept, not authorizing a full multi-provider system.

## Task 1 — Inspect the actual project

Read the relevant portions of:
- `docs/ECAS_development_plan.md`
- `docs/ECAS.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/DATA_FLOW.md`
- `docs/architecture/DATA_MODELS.md`
- `docs/architecture/MODULE_RESPONSIBILITIES.md`
- `docs/architecture/VALIDATION_STRATEGY.md`
- `docs/brains/DECISIONS.md`
- `docs/brains/PROJECT_STATE.md`
- `ecas/models/spectrum.py`
- `ecas/ingestion/csv_importer.py`
- `ecas/persistence.py`
- `ecas/ui/main_window.py`
- `docs/Chunk_4/Chunk_4_guidelines.md` (THAT IS THIS MESSAGE.)
- `docs/Chunk_4/Chunk_4_plan_vX.md` (Where X is the version number. NO FILE WILL END WITH X. It will be a number, eg: 1, 2, 3, etc.) Each version should represent a meaningful revision, not every minor adjustment. Mark superseded plans clearly.
- `docs/Chunk_4/Chunk_4_implementation_log.md` Completed bursts, files changed, tests run, results, and unresolved issues. Should be used to update `docs/ECAS_development_plan.md` when this chunk is done. Record each completed burst, files changed, exact test commands and results, and unresolved issues. Distinguish tests actually run from tests merely proposed.
- `docs/Chunk_4/Chunk_4_decisions.md` Keep decisions and their rationale here while Chunk 4 is active. At completion, transfer relevant lasting decisions into `docs/brains/DECISIONS.md` rather than leaving conflicting copies.
- Existing tests and dependency/configuration files.

Inspect other files only when directly relevant.

Distinguish implemented behavior from proposed architecture. If documents conflict with the code or each other, report the conflict instead of silently choosing an interpretation.

Do not assume the current `SpectrumData` model can represent all required astronomical and molecular datasets. Examine its fields and identify limitations.

## Task 2 — Investigate astronomical data sources

Investigate the official documentation and actual data access options for:
- NASA Exoplanet Archive.
- MAST.

Determine whether each source can provide an actual relevant spectral data product, rather than only planet catalog metadata or publication records.

For each candidate, establish:
- What data products can be discovered and downloaded.
- Whether spectral measurements, uncertainties, units, and associated metadata are available.
- Whether the product is a transmission spectrum or another type of data that would require additional processing.
- Which identifiers, response/file formats, and metadata are supplied.
- API access requirements, relevant usage conditions, and reproducibility considerations.
- Whether a small retrieval can be demonstrated without paid services or unnecessary credentials.
- Whether the data can be represented faithfully by the existing model or require a distinct observation/data-product representation.

Recommend whether one of these sources should be the first astronomical provider. Do not assume that an available catalog entry is itself a usable spectrum.

## Task 3 — Investigate molecular reference sources: NIST and HITRAN

Investigate both sources before recommending which should be integrated first.

### A. NIST Chemistry WebBook

Determine:
- Which molecular species and spectral regions are actually represented in the relevant collections.
- Availability of IR and UV/Vis spectra, including the types of spectra and experimental conditions where documented.
- Whether data are available as numerical coordinates and intensities, downloadable files, structured responses, or only graphical displays for particular records.
- How to identify a compound reliably using the identifiers supplied by NIST.
- Whether the source supports a stable, documented programmatic interface. Do not assume that a web search page or an unofficial scraper constitutes an official API.
- What implementation would be required to retrieve one record responsibly and reproducibly.
- Attribution, citation, access, and usage conditions relevant to the intended implementation.

### B. HITRAN and its Python API

Determine:
- Which molecular species and wavelength/wavenumber regions are supported by the relevant HITRAN data products.
- Whether the source supplies line-by-line transition parameters rather than measured continuous spectra.
- How HITRAN data would be converted into a calculated spectrum, if needed, and what physical assumptions and parameters would be required.
- What units, line parameters, uncertainties or quality information, and molecular identifiers are available.
- API-key requirements, dependency requirements, request limits, and applicable data-use/citation conditions.
- Whether the available API can retrieve a small real dataset suitable for a reproducible proof of concept.

Do not assume that a HITRAN line list is equivalent to an experimentally measured FTIR spectrum. Explain the distinction and the consequences for future comparison workflows.

### C. Compare and recommend

Compare NIST and HITRAN on:
- Relevance to ECAS's intended molecular reference workflow.
- Infrared coverage and applicability to UV/Vis.
- Data accessibility and ease of programmatic retrieval.
- Numerical data availability and metadata quality.
- Authentication and setup burden.
- Scientific meaning of the data.
- Suitability for automated tests, caching, and provenance tracking.
- Implementation complexity and risk.

Recommend one initial molecular-reference source based on evidence.

If NIST is easier for a small proof of concept but does not offer a stable official programmatic interface for the required record, explain that trade-off. If HITRAN is more practical for a particular IR use case but requires an API key or line-shape calculations, explain that trade-off.

Do not select a source solely because it is easiest to download from. The source must suit the scientific purpose of the initial use case.

### D. Keep the data types distinct

The design must distinguish, at minimum:
- Astronomical observations, such as exoplanet transmission spectra.
- Experimentally measured molecular reference spectra.
- Theoretical or calculated molecular spectra.
- Molecular line lists containing transition parameters.

Do not force these categories into a single generic spectrum representation if doing so loses scientifically important meaning.

Identify the minimum metadata needed to distinguish them, including source identity, molecule or target identity, spectral coordinate and units, signal meaning and units, provenance, available uncertainty, and whether the data are measured or calculated.

Do not implement these models yet. Recommend the smallest scientifically defensible design for review.

## Task 4 — Recommend the first proof of concept

Recommend a bounded first implementation plan that covers the appropriate parts of Chunk 4.

Evaluate whether the first burst should focus on:
1. One astronomical archive provider.
2. One molecular-reference provider.
3. A narrowly scoped pair of providers, only if the repository architecture and evidence justify this without excessive complexity.

Do not automatically require both types of provider in the first implementation burst. Explain the dependencies and recommend the safest order.

The eventual Chunk 4 workflow should be able to retrieve and register real data with traceable provenance. Where practical, the longer-term workflow should support:
- Finding a relevant astronomical observation.
- Finding a molecular reference dataset for a selected species.
- Preserving the original source data and metadata.
- Recording retrieval details and citations.
- Validating and registering data without silently changing scientific meaning.
- Caching data for repeat and offline access, subject to source terms.

For the initial proof of concept, specify:
- One actual source and one real, identifiable dataset or record.
- Exact retrieval and parsing scope.
- What data and metadata will be preserved.
- What constitutes successful registration.
- What is explicitly deferred.

Do not use fabricated data as evidence of successful retrieval. Test fixtures may be used for deterministic unit tests, but at least one documented manual or integration verification must establish that a real source record was retrieved successfully.

## Task 5 — Propose a minimal provider architecture

Recommend the smallest abstraction that isolates provider-specific API behavior from ECAS's internal data model.

Identify:
- Proposed modules and their responsibilities.
- The provider interface and first concrete provider.
- Whether astronomical and molecular-reference retrieval should use separate interfaces or share only a small amount of infrastructure.
- Where network access, parsing, structural validation, scientific suitability checks, and registration belong.
- How source identity, record identifiers, citations, retrieval timestamp, source URL, data version, units, uncertainties, and other available metadata would be preserved.
- How original downloaded artifacts relate to normalized data and existing SQLite persistence.
- How caching should work, including cache identity, repeat retrieval, failed requests, and offline reuse.

Do not build a generalized plugin framework or implement multiple providers before the first provider demonstrates a need for it.

Do not add an API key or other secret to source control. If credentials are needed, recommend a safe local configuration method and ensure tests can run without live credentials.

Do not force new data into the existing `SpectrumData` model if its fields cannot faithfully represent it. Identify required model or persistence changes and justify each one.

## Task 6 — Define testing and acceptance criteria

Propose tests for:
- Parsing provider responses using captured or local fixtures.
- Missing, malformed, and unexpected source data.
- Network failures, rate limits, unavailable records, and authentication failures where applicable.
- Provenance and scientific metadata preservation.
- Distinguishing measured spectra from calculated spectra and line lists.
- Unit and coordinate interpretation without invented values.
- Persistence and repeat access from cache.
- Regression against existing import, persistence, UI, and plotting behavior.

Separate:
- Deterministic automated tests.
- Tests requiring network access or credentials.
- Manual GUI verification.

Avoid tests that depend on an unstable live API when a fixture-based test can verify the same parsing behavior. Do not claim that fixture-based tests alone prove live retrieval works.

## Task 7 — Keep the work bounded

This is planning only. Do not modify files, install packages, or run implementation steps.

Do not start later chunks involving spectral comparison algorithms, molecular scoring, atmospheric abundance estimates, or full atmospheric retrieval.

Do not expand this task into support for every archive, every molecule, every spectral region, or every file format.

Do not assume IR and UV/Vis data can share identical processing or comparison logic merely because both can be plotted.

Avoid unnecessary abstraction, unrelated refactoring, and speculative features. If a decision cannot be supported by available evidence, state what evidence is missing.

## Required response

Return:

1. A concise summary of the current implementation relevant to Chunk 4.
2. Evidence for and against each astronomical archive candidate.
3. Evidence for and against NIST and HITRAN for molecular-reference retrieval.
4. A comparison of measured molecular spectra versus theoretical line lists and calculated spectra.
5. Your recommended first astronomical source and first molecular-reference source, with justification.
6. A recommended order for the first few implementation bursts, beginning with only the first burst.
7. Proposed files/modules to add or modify, and why.
8. Required data-model, persistence, provenance, and caching decisions.
9. A test plan and explicit acceptance criteria.
10. Unresolved questions, risks, document conflicts, and external evidence still needed.

Do not write or edit project documents yet. We will review your plan before authorizing any implementation.