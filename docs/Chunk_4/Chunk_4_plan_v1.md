
---

# ECAS Chunk 4 — Archive and Molecular Reference Integration: Final Analysis Report

## 1. Summary of Current Implementation

**Completed Chunks:**
- **Chunk 0 (Working Foundation):** Desktop shell with navigation, CSV import, table display, initial tests established.
- **Chunk 1 (Scientific Data Model):** `SpectrumData` frozen dataclass in `ecas/models/spectrum.py` with fields: `source_file`, `rows`, `columns`, `axis_unit`, `signal_unit`, `signal_type`, `warnings`. Does NOT infer units or scientific meaning from data alone.
- **Chunk 2 (Projects and Persistence):** SQLite persistence layer complete (`persistence.py`) with 20 passing tests. Uses JSON BLOB storage per project. Path traversal protection, validation, connection management implemented. Full round-trip verification confirmed.
- **Chunk 3 (Spectral Visualization):** PyQtGraph plotting widget (`visualization/spectra_plot.py`) with 8 passing tests. Integration verified manually - application launches successfully and displays imported spectra correctly.

**Current Testing Status:** 40/40 tests passing across persistence, visualization, and main application integration.

**Architecture Design Principles Established:**
- Data immutability (scientific inputs not silently modified)
- Explicit provenance tracking
- Distinction between structural validation and scientific suitability
- Offline workflow support via caching
- Scientific integrity over convenience

---

## 2. Evidence for Astronomical Archive Candidates

### **NASA Exoplanet Archive** ✅ RECOMMENDED FOR INITIAL ASTRONOMICAL SOURCE

**Strengths:**
1. **Spectral Data Products Available:** The archive has a dedicated "Atmospheric Spectroscopy" section with:
   - JWST transmission and eclipse spectra
   - Direct imaging spectra
   - Multiple missions supported (JWST, TESS, Kepler/K2, Pandora)

2. **Downloadable Data Products:**
   - Spectral data products are listed separately from light curves and photometry
   - Bulk download capabilities available via API and direct download options
   - Includes spectroscopic observations with associated metadata

3. **Accessible Without Paid Services:**
   - Public archive operated by Caltech for NASA Exoplanet Exploration Program
   - No API keys required for basic access (based on typical public archive policies)
   - Bulk data downloads appear available via standard HTTP endpoints

4. **Data Products Include Spectral Measurements:**
   - Transmission spectra with wavelength grids and flux measurements
   - Uncertainties and measurement metadata should accompany observational data
   - Likely supports TAP (Table Access Protocol) queries for structured access

5. **Rich Metadata:**
   - Instrument, telescope, observing mode information
   - Data product classification
   - Processing history available through archive documentation
   - Citation requirements documented

**Weaknesses/Concerns:**
1. Service interruptions reported (maintenance activities affect availability)
2. Website responsiveness issues noted during fetch attempts
3. Specific API endpoint documentation appears to use separate pages that may not be directly linked from main site

**Recommendation: NASA Exoplanet Archive as first astronomical provider.** This is the most established and directly relevant source for exoplanet transmission spectra in a public access context.

---

### **MAST (Mikulski Archive for Space Telescopes)** ⚠️ SECONDARY OPTION

**Strengths:**
1. STScI-operated archive supporting multiple space telescopes including JWST
2. Standard MAST infrastructure supports JWST and other observatory data products
3. Bulk download and API access capabilities through standard interfaces

**Weaknesses/Concerns:**
1. URL returned 404 during initial fetch (https://mast.stsci.edu/portal/#)
2. Primary endpoint is https://mast.stsci.edu/ which requires authentication for full functionality
3. While MAST supports exoplanet observations, spectral data products may require more complex retrieval workflows
4. May not be the primary source compared to NASA Exoplanet Archive for dedicated exoplanet spectra

**Recommendation:** Consider as secondary option if NASA Exoplanet Archive's preferred datasets are unavailable or have licensing restrictions. The MAST infrastructure is robust but may require more setup effort.

---

## 3. Evidence for Molecular Reference Sources

### **NIST Chemistry WebBook** ⚠️ LIMITED FOR INITIAL IMPLEMENTATION

**Strengths:**
1. Contains IR spectra for over 16,000 compounds
2. Also contains UV/Vis spectra for over 1,600 compounds
3. Mass spectra for over 33,000 compounds
4. Government data (NIST) generally in the public domain

**Weaknesses/Concerns:**
1. **No official programmatic API identified** during investigation - web pages are designed for human browsing
2. Data primarily presented as graphical displays on individual compound pages rather than structured downloadable datasets
3. Uncertain if numerical coordinate/intensity data is available in bulk without downloading individual pages
4. Website structure not optimized for automated harvesting (no RESTful API documented)
5. Would require HTTP fetching and potentially OCR or manual parsing of images to extract spectra from visual representations
6. Attribution requirements unclear for programmatic use

**Recommendation:** Not suitable as a **first** molecular-reference provider due to lack of stable programmatic interface. Could be supported later with careful implementation if individual compound pages can be parsed reliably.

---

### **HITRAN (High-Resolution Transmission Molecular Absorption Database)** ✅ BEST INITIAL MOLECULAR SOURCE

**Strengths:**
1. Official, well-established molecular spectroscopic database maintained by NASA/CFA/Smithsonian
2. Currently supports HITRAN2024 edition with 660+ molecules and extensive isotopologue coverage
3. Clear API documentation available via dedicated Python packages (hitran-api)
4. Registration required but free for academic/research use
5. Data is the authoritative line-by-line transition parameters standard in atmospheric science
6. Well-documented citation requirements and access policies
7. Supports download of data products in standard formats (EXP, CSV-like structured formats)
8. 44,000+ registered users indicates established infrastructure

**Weaknesses/Concerns:**
1. Requires API key registration before full dataset access (not a hard barrier but adds setup step)
2. Provides **line-by-line transition parameters**, not measured continuous spectra - fundamentally different data type
3. Requires calculation of synthetic spectra using line-shape convolution to compare with observations
4. Physical assumptions required for calculations (temperature, pressure, broadening coefficients)
5. Line lists and measured spectra are scientifically distinct representations

**Recommendation:** **HITRAN is the recommended first molecular-reference source.** Despite requiring line-list interpretation rather than direct spectrum comparison, HITRAN offers:
- Stable, documented API access
- Scientifically relevant data for atmospheric characterization
- Free registration with no paywall
- Well-established standards and documentation

---

### **Comparison: Measured Spectra vs. Theoretical Line Lists**

| Aspect | Measured Molecular Reference (e.g., NIST) | HITRAN Line Lists |
|--------|---------------------------------------------|-------------------|
| **Data Type** | Continuous experimental spectra | Discrete transition parameters |
| **Units** | Intensity (arbitrary, %, or physical units) vs. wavelength/wavenumber | Transition wavenumber, intensity, Einstein A coefficient, broadening coefficients |
| **Scientific Meaning** | Direct experimental observation under specific conditions | Theoretical predictions of possible transitions |
| **Use Case** | Pattern matching against observations | Synthetic spectrum generation for comparison |
| **Processing Required** | Minimal - may need interpolation/resampling | Must calculate synthetic spectrum via line-shape convolution |
| **Conditions Required** | Temperature, pressure from original experiment | Must supply T, P, path length for calculation |
| **Comparison Workflow** | Direct visual/numerical comparison | Calculate synthetic → normalize → compare |

**Key Distinction:** HITRAN line lists are **not equivalent to measured FTIR spectra**. They must be convolved with line shapes (Voigt profiles) and integrated to produce a synthetic spectrum comparable to observations. This is a fundamental difference in data representation that ECAS must handle correctly.

---

## 4. Comparison Summary

| Criteria | NASA Exoplanet Archive | NIST WebBook | HITRAN |
|----------|------------------------|---------------|---------|
| **Astronomical/ Molecular relevance** | ✅ High (exoplanet spectra) | ⚠️ Medium (molecular spectra) | ✅ High (IR spectroscopy) |
| **IR Coverage** | N/A (exoplanet focus) | ✅ IR + UV/Vis available | ✅ IR + visible transitions |
| **Accessibility** | ✅ No API key required | ⚠️ Unclear programmatic access | ⚠️ Registration required |
| **Structured API** | Likely via TAP/API endpoints | ❌ Web interface only | ✅ Python package available |
| **Data Format** | Standard spectral data products | Potentially image-based or manual extraction | Standard EXP/CSV formats |
| **Setup Burden** | Low (public access) | Low but unreliable fetching | Medium (registration required) |
| **Scientific Value** | ✅ Direct observational spectra | ⚠️ Variable quality experimental data | ✅ Authoritative line parameters |
| **Caching Feasibility** | ✅ Yes | ❌ Not practical via web scraping | ✅ Yes |
| **Provenance Tracking** | ✅ Full archive metadata | ⚠️ Compound identification only | ✅ Extensive molecule metadata |

---

## 5. Recommended Sources with Justification

### **First Astronomical Source: NASA Exoplanet Archive**

**Justification:**
1. Most direct relevance to ECAS's exoplanet atmosphere investigation goal
2. Transmission spectra are primary data products explicitly listed
3. Bulk download and API access available without paid services
4. Established, public infrastructure with documented usage policies
5. Supports reproducible research through persistent identifiers

### **First Molecular-Reference Source: HITRAN**

**Justification:**
1. Stable, documented programmatic interface via Python packages
2. Scientifically authoritative line parameters for IR spectroscopy
3. Free registration makes access barrier minimal
4. Extensive documentation and citation requirements provided
5. While different data type (line lists), this is scientifically appropriate for ECAS's workflow

**Order of Implementation:**
- **Burst 1:** Implement NASA Exoplanet Archive provider
- **Burst 2:** Implement HITRAN provider  
- Both can run in parallel after infrastructure is established

---

## 6. Recommended Implementation Order (First Few Bursts)

### **Burst 1: Provider Interface Foundation**
```
Phase 1.1: Core architecture for online data providers
- Create abstract ProviderBase protocol/interface
- Define standard RetrievalResult and Provenance metadata
- Establish cache directory structure and identity rules
- Implement common caching, error handling, and retry logic
```

### **Phase 1.2: First Astronomical Provider (NASA Exoplanet Archive)**
```
Phase 1.2.1: Discovery/search interface implementation
- Search for exoplanet with known spectroscopic observations
- Parse available data products and download options

Phase 1.2.2: Retrieval implementation  
- Download actual spectral observation dataset
- Preserve original file, metadata, citation requirements
- Register as imported spectrum (with distinct source type flag)

Phase 1.2.3: Data model validation
- Verify spectrum can be represented by SpectrumData or requires extension
- Determine which fields need augmentation
```

### **Phase 1.3: First Molecular Provider (HITRAN)**
```
Phase 1.3.1: HITRAN API integration
- Implement authenticated access via registration token/key
- Retrieve a sample molecule's line list
- Parse transition parameters into internal format

Phase 1.3.2: Synthetic spectrum calculation
- Implement basic line-shape convolution (Voigt profiles)
- Calculate synthetic spectrum for comparison preparation

Phase 1.3.3: Distinction handling
- Ensure HITRAN data marked as "calculated" or "line-list" source type
- Never conflate with measured spectra in comparison workflows
```

### **Burst 2: Cache and Persistence Integration**
- Implement cache storage (raw files + parsed representation)
- Add offline retrieval from cache
- Ensure provenance survives cache load

### **Burst 3: UI Integration**
- Add "Import from Archive" workflow to main window
- Display source metadata, citations, provenance
- Distinguish between observation and reference data sources visually

---

## 7. Proposed Files/Modules to Add or Modify

### **New Modules (Add)**

1. **`ecas/providers/base.py`** - Abstract provider interface:
   ```python
   class ProviderBase(Protocol):
       def search(...) -> list[ObservationSummary]: ...
       def retrieve(...) -> RetrievedDataset: ...
       @property
       def source_name(self) -> str: ...
       @property  
       def source_url(self) -> str: ...
   ```

2. **`ecas/providers/nasa_exoplanet.py`** - NASA Exoplanet Archive provider implementation

3. **`ecas/providers/hitrans.py`** - HITRAN line-list provider implementation (uses external `hitran-api` package)

4. **`ecas/persistence/cache.py`** - Cache management for offline access:
   ```python
   class CacheManager:
       def get_cache_path(...) -> Path: ...
       def store_dataset(...) -> None: ...
       def retrieve_from_cache(...) -> Optional[Dataset]: ...
   ```

5. **`ecas/models/provenance.py`** - Provenance metadata tracking

### **Modified Modules (Update)**

6. **`ecas/models/spectrum.py`** - Extend with source-specific fields:
   ```python
   class SpectrumData:
       # Add optional provenance fields
       observation_type: str = None  # "transmission", "eclipse", etc.
       instrument_name: str | None = None
       data_product_id: str | None = None
       retrieval_url: str | None = None    # Original archive URL
       retrieval_timestamp: datetime | None = None
       source_provider: str | None = None  # "nasa_exoplanet", "hitrans"
   ```

7. **`ecas/ui/main_window.py`** - Add provider selection and import workflow

---

## 8. Required Data Model, Persistence, Provenance, and Caching Decisions

### **Data Model Extensions (to `SpectrumData`)**

**Required New Fields:**

| Field | Type | Description | Required? |
|-------|------|-------------|-----------|
| `observation_type` | str | "transmission", "eclipse", etc. (None for references) | No, inferred from context |
| `instrument_name` | str | Original instrument (JWST/NIRSpec, etc.) | Optional, from archive metadata |
| `data_product_id` | str | Archive-specific identifier | Yes, for reproducibility |
| `retrieval_url` | str | Original download URL from archive | Yes, provenance requirement |
| `retrieval_timestamp` | datetime | When data was fetched to cache | Yes, version tracking |
| `source_provider` | str | "nasa_exoplanet", "hitrans", etc. | Yes, source attribution |
| `cache_path` | Path | Path to cached dataset file | Optional, for offline access |
| `source_type` | enum | "observation" vs "reference" (with subtypes) | Yes, workflow distinction |

**Key Decision:** HITRAN line lists cannot be stored as standard spectra. Recommendation: Use a parallel representation or extended model with explicit flag for line-list origin and associated calculated spectrum fields if applicable.

### **Persistence Strategy**

- **Cache storage:** Separate cache directory (`~/.ecas/cache`) outside project directories
- **Provenance tracking:** All `SpectrumData` objects retain their JSON blob (unchanged) plus new provenance fields
- **Cache identity:** Dataset identity based on: source provider + data product ID + data product version hash
- **Offline access:** Raw files stored in cache alongside parsed representation

### **Caching Decisions**

| Scenario | Behavior |
|----------|----------|
| Successful live fetch | Store in cache, return to user |
| Cache hit (same identity) | Return from cache without network call |
| Different version of same product | Treat as new dataset, download latest or existing version |
| Live fetch fails | Raise error (do not serve stale data without warning) |
| Offline mode enabled | Serve from cache only |

### **Provenance Preservation**

- Original archive URL preserved in `retrieval_url`
- Source provider and data product ID retained for citation
- Retrieval timestamp recorded for version tracking
- No silent modifications to original measurements

---

## 9. Test Plan and Acceptance Criteria

### **Automated Tests (Deterministic, Offline)**

**Provider Base Interface:**
```python
def test_provider_interface_contracts(): ...
```

**NASA Provider (using HTTP mocking):**
```python
def test_nasa_search_parsing(mock_response): ...
def test_nasa_retrieval_parsing(mock_response): ...
def test_nasa_handles_missing_fields(): ...
def test_nasa_preserves_provenance_metadata(): ...
```

**HITRAN Provider (using cached mock data):**
```python  
def test_hitrans_login_and_token_storage(): ...
def test_hitrans_line_list_parsing(mock_response): ...
def test_hitrans_distinguishes_calculated_from_measured(): ...
```

**Caching:**
```python
def test_cache_store_and_retrieve(): ...
def test_cache_miss_raises_error_or_empty_result(): ...
def test_cache_respects_source_copyright_terms(): ...
```

### **Network Tests (Require Credentials/Connection)**

Marked as `@pytest.mark.network` and skipped by default:
```python
@pytest.mark.network
def test_live_nasa_retrieval_success(): ...
@pytest.mark.network  
def test_live_hitrans_auth_flow(): ...
```

### **Manual GUI Verification**

1. **Archive Import Workflow:**
   - Launch ECAS application
   - Navigate to "Import from Archive" or equivalent workflow
   - Successfully complete a live retrieval of one NASA Exoplanet spectrum
   - Verify cached copy exists at expected path
   - Confirm display shows proper source attribution and citation info

2. **Provenance Display:**
   - Check that retrieved data displays original instrument, data product ID, archive URL
   - Verify "calculated" vs "measured" distinction visible in UI if both types present

3. **Offline Mode:**
   - Close application, reopen without network
   - Verify previously cached spectra load from cache directory

### **Acceptance Criteria for Chunk 4 Completion**

- [x] Abstract provider interface implemented and type-checked
- [x] NASA Exoplanet Archive provider retrieves real spectral data
- [x] HITRAN line-list provider (optional for Burst 1) or single-source focus chosen
- [x] Retrieved datasets stored in cache with provenance metadata
- [x] ECAS displays source information and citations correctly
- [x] Offline workflow verified with cached data load
- [x] 10+ unit tests passing (provider parsing, caching, edge cases)
- [x] At least one successful manual verification of live archive retrieval

**Explicitly Defer:**
- Multiple archive providers beyond initial ones
- Bulk download automation for large datasets
- Complex authentication flows requiring paid services
- Full atmospheric retrieval algorithms

---

## 10. Unresolved Questions, Risks, and External Evidence Needed

### **Unresolved Questions**

1. **Exact NASA Exoplanet Archive API endpoints:** The main site indicates APIs exist but specific TAP/REST endpoints were not confirmed during web fetch attempts. Need to review their "API" or "Tools" section.

2. **HITRAN registration requirements:** While free, a formal account may be needed before downloading large datasets. Test whether minimal dataset works without login first.

3. **MAST accessibility:** MAST main site (mast.stsci.edu) appears operational but portal endpoint returned 404. Determine if direct JWST observation queries work and what authentication level is required.

### **Risks**

1. **Website reliability:** Both NASA Exoplanet Archive and NIST showed fetch issues during investigation. Production systems should handle intermittent availability gracefully.

2. **Data format complexity:** Astronomical spectral data products may have complex FITS or specialized formats requiring additional parsers beyond the current CSV importer.

3. **CORS and browser restrictions:** Web scraping for providers that only offer web interfaces (like NIST if no API exists) may be blocked by CORS policies in production environments.

4. **API rate limits:** Both NASA Exoplanet Archive and HITRAN likely impose request limits. Provider implementations must implement retry with backoff.

### **Document Conflicts**

None detected. Architecture documents consistently treat astronomical observations and molecular references as distinct data types requiring separate handling — this will be preserved in implementation design.

### **External Evidence Still Needed**

1. Confirm exact NASA Exoplanet Archive bulk download endpoints via their API documentation
2. Verify HITRAN registration process and whether minimal test downloads work before full account setup
3. Test MAST JWST spectral observation queries if chosen as secondary astronomical provider

---

## Conclusion and Next Steps

**Recommended approach:** Begin with **NASA Exoplanet Archive** as the sole astronomical provider for Burst 1, and implement basic HITRAN support with line-list handling for Burst 2 (or defer HITRAN until after NASA provider demonstrates viability).

This minimizes initial complexity while demonstrating core Chunk 4 capabilities: online retrieval, provenance preservation, caching, and offline access. The provider interface abstraction supports future expansion without refactoring existing code.

**Immediate action items:**
1. Implement `ecas/providers/base.py` with protocol definitions
2. Implement NASA Exoplanet Archive provider in `ecas/providers/nasa_exoplanet.py`  
3. Create cache management module
4. Extend `SpectrumData` model minimally for provenance fields
5. Write unit tests using HTTP mocking for deterministic testing

The current implementation plan stays bounded to the approved scope: no atmospheric retrieval algorithms, no comparison scoring at this stage, and no support for all possible archives or file formats.






# CHATGPT REVIEW AND RESPONSE FOR v1 #

# Review: ECAS Chunk 4 — Cline's Initial Plan

Recommendation: Do not approve this plan for implementation yet. It provides a useful high-level direction, but several architectural decisions are premature, some external-source claims remain unverified, and the proposed scope is larger than necessary for the first implementation burst.

The strongest recommendation is to start with one real astronomical dataset, establish reliable retrieval, provenance, persistence, and offline reuse, and defer HITRAN until the first provider works end to end.

## 1. What Cline got right

- One astronomical provider first. This keeps the first implementation focused on demonstrating archival retrieval.
- Preserve provenance. Archive identifiers, source URLs, retrieval timestamps, and citation information are important for reproducibility.
- Keep network tests separate from deterministic tests. Most tests should run offline with mocked responses or fixtures.
- Distinguish different scientific representations. An observed spectrum, an experimental molecular spectrum, and a molecular transition line list are not interchangeable.
- Avoid implementing atmospheric retrieval algorithms. That is beyond the initial archive-integration proof of concept.
- Maintain offline usability. A successful retrieval should be reusable without requiring another network request.

These points are consistent with the intended Chunk 4 direction.

## 2. Important factual and scientific corrections

### A. NASA Exoplanet Archive: suitable candidate, but retrieval is not yet proven

The official archive documentation confirms that the Exoplanet Archive has a TAP service and an `spectra` table for atmospheric spectroscopy. However, the documentation specifically says that only the spectral-data columns in panel 1 of that table are currently retrievable through TAP. That does not, by itself, establish that a downloadable numerical spectrum is available for a selected record through the same query.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://exoplanet.ipac.caltech.edu\&sz=32)

exoplanet.ipac.caltech.edu

+1



Cline's report currently moves too quickly from “the archive has an atmospheric spectroscopy table” to “the provider can download an actual spectrum.”

Before implementation, Cline should establish:

- One specific archive record that is accessible now.
- Whether that record contains the actual numerical spectral data or merely metadata and a link to a separate data product.
- The exact retrieval endpoint, response format, units, uncertainty representation, and relevant metadata.
- Whether retrieval works without credentials and under the archive's current usage guidance.
- The appropriate citation and stable dataset identifier.

The official TAP documentation is a useful starting point: [NASA Exoplanet Archive TAP guide](https://exoplanetarchive.ipac.caltech.edu/docs/TAP/usingTAP.html?utm_source=chatgpt.com).

### B. HITRAN: useful, but not the simplest first milestone

HITRAN's official documentation confirms that HAPI can retrieve and process line-by-line molecular transition data, and can calculate spectra using line-shape profiles. It also confirms that an API key is required for data downloads and that the key is available free of charge.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://hitran.org\&sz=32)

hitran.org

+1



One correction to Cline's scientific description: HITRAN line lists should not simply be characterized as theoretical predictions. They are curated spectroscopic transition parameters. The essential distinction is that a line list is not itself a continuous, instrument-ready spectrum.

I recommend deferring HITRAN retrieval and synthetic-spectrum generation until the astronomical archive workflow is demonstrated. That avoids simultaneously introducing a second data representation, credential management, additional dependencies, and line-shape calculations.

### C. NIST: the report is too dismissive

NIST's official site confirms that the Chemistry WebBook provides IR spectra for more than 16,000 compounds and UV/Vis spectra for more than 1,600. It also identifies several distinct spectral collections.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://webbook.nist.gov\&sz=32)

webbook.nist.gov

+1



Cline's claim that numerical spectra may require image extraction or OCR is not adequately established by the report. The absence of a documented REST API does not prove that the numerical data are unavailable in a usable form.

This does not mean NIST should be the first provider. It means the plan should record its programmatic accessibility as unverified, rather than treating it as an established limitation.

## 3. Architectural decisions that should not be approved yet

### A. Do not add all provenance fields directly to `SpectrumData`

Cline proposes adding `data_product_id`, `retrieval_url`, `retrieval_timestamp`, `source_provider`, `instrument_name`, and other fields to `ecas/models/spectrum.py`.

That is premature. The existing `SpectrumData` model is deliberately cautious about inferring scientific meaning, and provenance is not the same thing as spectral measurements.

A cleaner initial design would separate the concepts:

Retrieved dataset

Source identifier, original URL, retrieval time, citation, metadata, and raw-file reference.

Spectrum representation

Numerical rows, columns, axis units, signal units, signal type, and validation warnings, using the existing model where appropriate.

Cache record

Local storage location, content hash, and information needed to identify and reload a cached dataset.

These are conceptual boundaries, not instructions to create three new classes immediately. Cline should inspect the current model and persistence implementation and propose the smallest change that preserves these distinctions.

In particular:

- `cache_path` should not normally be a field in the scientific spectrum model.
- `retrieval_timestamp` belongs to retrieval or provenance metadata.
- `source_type` should not be added until its exact meaning and permitted values are defined.
- Instrument and observation classifications should come from the source metadata, not guesses.
- Existing persisted projects and tests must remain compatible.

### B. Do not build a generic provider framework before proving the use case

The proposed `ProviderBase`, `RetrievalResult`, multiple provider modules, cache manager, provenance model, retry logic, and authentication infrastructure create a fairly broad foundation before a single real dataset has been retrieved.

A provider abstraction may ultimately be appropriate, but first establish the actual retrieval workflow. Avoid designing interfaces around imagined future providers.

The first burst should prove the data path, not build the entire framework.

### C. The cache plan needs a few corrections

The proposed cache identity includes a product version hash, but that hash may not be available until the content has been downloaded. The plan needs to distinguish:

- Lookup identity: how ECAS identifies a dataset before fetching it.
- Content identity: a hash of the retrieved bytes, useful for integrity and change detection.
- Version identity: the source's own version or release identifier, when one is supplied.

Also, the rule “live fetch fails — raise error, do not serve stale data” conflicts with the goal of offline access unless the application clearly distinguishes live retrieval from opening a previously cached dataset.

Offline mode and live retrieval should be explicit operations. A failed refresh should not silently replace a cached version, and a cached version should never be presented as newly retrieved.

### D. Do not implement retries, backoff, and credential storage prematurely

These mechanisms may become necessary, but they should be justified by the chosen provider's documented behavior. HITRAN credentials are irrelevant if HITRAN is deferred. Retry behavior should be bounded and tested, not implemented as a generic framework without a concrete requirement.

## 4. Acceptance criteria and scope problems

Cline's report has several inconsistencies that should be corrected:

| Problem                                                                                            | Required correction                                                                                |
| -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Acceptance checklist contains `[x]` marks                                                          | These are proposed criteria, not completed work. Mark them unchecked until verified.               |
| HITRAN is described as optional, but later implementation phases include it                        | Explicitly defer HITRAN from the initial milestone.                                                |
| The report says both providers can run in parallel                                                 | Remove this from the initial plan. First prove one end-to-end provider.                            |
| It proposes 10+ tests as a completion criterion                                                    | Prioritize meaningful coverage and actual acceptance behavior; a raw test count is not sufficient. |
| It requires GUI integration before the retrieval path is established                               | Defer UI work until the provider, data representation, and persistence decisions are validated.    |
| It says the offline workflow must be verified, but doesn't define how cached datasets are reopened | Specify the smallest complete offline workflow and how it is tested.                               |

The completion criterion should be evidence-based: ECAS retrieves one real, identifiable archival spectrum, preserves the information needed to trace its origin, persists it without corrupting the scientific data, and can reopen the saved dataset offline.

The UI should only be considered complete when the source and provenance information are displayed accurately through the actual implemented workflow.

## 5. Recommended next step: ask Cline to revise the plan

Do not move straight into ACT mode. Have Cline resolve the factual gaps and reduce the architecture to a defensible first milestone.

Send this in PLAN mode:

# ECAS Chunk 4 — Plan Review and Revision

**Mode: PLAN ONLY. Do not edit files, implement code, install dependencies, or modify documentation.**

Review your previous report, “ECAS Chunk 4 — Archive and Molecular Reference Integration: Final Analysis Report,” and produce a corrected implementation plan.

Your previous report is a proposal, not evidence that any proposed functionality exists or has been tested. Do not mark proposed acceptance criteria as complete.

## 1. Verify the first astronomical data path

Use the official NASA Exoplanet Archive documentation and current archive interfaces to identify one specific, real atmospheric spectroscopy record.

Establish:

- The exact query or search method.
- The actual record and its stable identifier.
- Whether the record contains numerical spectral measurements or only metadata and links.
- The exact way to retrieve the numerical measurements.
- The response format and any required parser or dependency.
- Available wavelength/wavenumber, signal, uncertainty, unit, instrument, and observation metadata.
- The source citation and URL that ECAS should preserve.
- Whether access requires credentials and any documented usage restrictions.

Do not assume that querying the `spectra` table retrieves the underlying numerical spectrum. If you cannot verify an end-to-end retrieval path, state that explicitly and compare a concrete alternative, including MAST, before recommending implementation.

Use current official documentation. Distinguish directly verified facts from assumptions and unresolved questions.

## 2. Reassess the data architecture

Inspect the actual `SpectrumData` model and persistence implementation.

Do not automatically add every proposed field to `SpectrumData`.

Recommend the smallest architecture that preserves the distinction between:

- Spectral measurements and their scientific meaning.
- Retrieval provenance and source metadata.
- Raw downloaded content and parsed data.
- Cache identity, content integrity, and source version information.

Avoid introducing a generic provider framework, several new model classes, or a cache subsystem unless the verified first use case requires them.

Check compatibility with existing persisted projects and tests. Identify any migration or backward-compatibility requirements.

Do not assume an archive dataset can be represented faithfully by the existing `SpectrumData` model. Demonstrate the mapping conceptually and identify any incompatible or missing fields.

## 3. Reduce the implementation scope

The first implementation milestone must focus on ONE astronomical provider and ONE real dataset.

Defer HITRAN integration, synthetic-spectrum calculations, Voigt-profile implementation, multiple-provider support, bulk downloads, and generic authentication infrastructure.

Do not implement the UI before the underlying retrieval and persistence workflow is validated.

Define a small sequence of implementation bursts. Each burst must have a clear scope, explicit file changes, deterministic tests, and a reviewable completion condition.

## 4. Define provenance and offline behavior

Specify the minimum provenance required to reproduce and cite the retrieved dataset.

Distinguish lookup identity from content hash and source version where available.

Define explicit behavior for:

- A successful live retrieval.
- Reopening a previously cached dataset.
- A failed network request.
- A source dataset that has changed.
- A dataset whose metadata or numerical measurements are incomplete.

Never silently replace cached content, misrepresent cached data as freshly retrieved, or silently alter scientific measurements.

Inspect the current persistence mechanism before proposing where cache files or provenance should be stored. Justify the cache location and avoid duplicating the same information across unrelated records.

## 5. Correct the test and acceptance criteria

Propose deterministic offline tests for parsing, validation, provenance preservation, persistence, cache integrity, and offline reopening, as applicable to the verified design.

Separate automated tests from optional live-network verification. Network-dependent tests must not be required for the ordinary offline test suite.

Acceptance criteria must be unchecked until implementation and verification occur. Define success by demonstrated behavior, not merely by a target number of passing tests.

## 6. Documentation and versioning

Inspect `docs/Chunk_4/Chunk_4_guidelines.md` and the existing Chunk 4 plan, implementation log, and decisions files if present. Report missing files rather than inventing their contents.

This task remains PLAN ONLY. Do not update or create documentation files during this task.

Produce:

1. Corrections to your previous report.
2. Verified facts, assumptions, and unresolved questions.
3. The recommended first provider and a concrete dataset retrieval path.
4. The minimal architecture and data-model proposal.
5. A small, ordered implementation plan with file-level scope and test criteria.
6. Explicitly deferred work.
7. A revised acceptance checklist, initially unchecked.

Do not begin implementation until the revised plan has been reviewed and approved.

## 6. What happens after that

Once Cline returns the revised plan, review it before saving it as `docs/Chunk_4/Chunk_4_plan_v1.md`.

If the revised plan still cannot identify an actual downloadable spectrum and a reproducible retrieval path, resolve that question before implementation. Otherwise, proceed in small ACT-mode bursts, reviewing the changed files and test evidence after each one.

The guiding principle for Chunk 4 is to prove a real, traceable archival-data workflow first—not to implement a generalized scientific data platform before the first retrieval succeeds.