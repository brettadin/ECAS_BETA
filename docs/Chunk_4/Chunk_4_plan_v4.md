
---

## **ECAS Chunk 4 — Plan v3 Review Report**

### **1. Repository Inspection**

**Files and code locations inspected:**

| File | Path | Purpose |
|------|------|---------|
| **SpectrumData model** | `ecas/models/spectrum.py` | Current frozen dataclass with `source_file`, `rows`, `columns`, `axis_unit`, `signal_unit`, `signal_type`, `warnings` |
| **CSV Importer** | `ecas/ingestion/csv_importer.py` | Implements `import_spectrum_csv()` with validation, alias mapping, and error handling |
| **Tests** | `tests/test_csv_importer.py` | Unit tests for CSV import, validation, edge cases (missing columns, invalid values) |
| **Persistence layer** | `ecas/persistence.py` | SQLite database storage for projects/spectra with JSON BLOB schema |
| **Chunk 4 docs** | `docs/Chunk_4/*` | Planning documents: guidelines, plan v1/v2/v3, implementation log (empty), decisions (empty) |
| **Architecture docs** | `docs/architecture/*` | Module responsibilities, data flow, data models, validation strategy |
| **Project state** | `docs/brains/PROJECT_STATE.md` | High-level project status and completion tracking |

**Key findings from existing code:**

- **`source_file: Path` is REQUIRED** - No default value, must be provided on construction
- **Frozen dataclass contract** - Immutability is enforced via `frozen=True`; no field modifications allowed after construction
- **Current fields are sufficient** for raw CSV data; provenance should be tracked separately
- **Persistence uses JSON BLOB storage** per project; each spectrum's dataclass is serialized as JSON
- **Column aliasing is supported** (`lambda`→`wavelength`, `intensity`→`signal`, etc.)

**Path discrepancies:** All Chunk 4 documentation files exist under `docs/Chunk_4/`. The implementation log and decisions files are currently empty (0 bytes), which is appropriate for a new planning phase.

---

### **2. Retrieval Verification**

**Status: Live retrieval CANNOT be completed via tool calls**

**What has been verified:**
- ✅ NASA Exoplanet Archive's Firefly interface exists at the documented URL
- ✅ Atmospheric Spectroscopy Table is accessible via `/cgi-bin/atmospheres/nph-firefly?atmospheres`
- ✅ TAP metadata-only limitation confirmed (per documentation, not live test)
- ✅ wget script download mechanism documented in archive UI

**What CANNOT be verified without manual intervention:**
- ❌ Exact file format of downloaded spectra (.tbl, .csv, .fits)
- ❌ Column names and their units in Panel 2 data view
- ❌ Whether direct HTTP GET works for individual spectrum files
- ❌ Available provenance fields (record ID, publication reference, etc.)

**Blockers:**
1. The Firefly interface requires JavaScript/browser interaction that cannot be simulated via `fetch_web_content`
2. No documented REST API endpoint exists for direct spectrum file retrieval
3. wget script generation requires a browser-based selection workflow

**What remains unknown:**
- Exact filename pattern for downloaded spectra
- Column structure (axis values, signal, uncertainty columns)
- Whether units are provided inline or must be inferred from metadata
- Citation requirements specific to retrieved records

**Required manual action:** Navigate to the Exoplanet Archive Firefly UI, search for a JWST spectrum, and attempt download via the documented wget mechanism. Share the resulting file path, contents, and any error messages.

---

### **3. Compatibility Assessment**

**Current `SpectrumData` model structure:**
```python
@dataclass(frozen=True)
class SpectrumData:
    source_file: Path                                    # REQUIRED - must exist
    rows: tuple[dict[str, CellValue], ...]               # REQUIRED - measurement data
    columns: tuple[str, ...]                              # REQUIRED - column names
    axis_unit: str | None = None                         # Optional
    signal_unit: str | None = None                       # Optional
    signal_type: str | None = None                       # Optional
    warnings: tuple[str, ...] = ()                       # Optional
```

**Analysis:**

1. **`source_file` must remain required** - Making it optional or allowing `None` would break:
   - Existing CSV import tests (`test_import_valid_csv`)
   - Frozen dataclass initialization patterns
   - SQLite JSON BLOB storage expectations (expects valid JSON)
   
2. **Current fields are adequate for archival data:**
   - Raw measurements go into `rows` + `columns` (unchanged)
   - Archive-provided units populate `axis_unit`, `signal_unit`
   - Observation mode (transmission/eclipse) goes into `signal_type`
   - Import notes go into `warnings`

3. **Provenance strategy:** Do NOT add provenance fields directly to `SpectrumData`. Instead:
   - Store raw downloaded file at a known cache path
   - Use the cache path as `source_file`
   - Track archival metadata separately (e.g., in a "metadata" BLOB or separate record)

4. **Alternative approach:** Consider an external JSON/provenance document alongside each cached spectrum that records:
   - Provider name
   - Record identifier
   - Retrieval timestamp and URL
   - Citation requirements

**Minimum necessary changes:** None to the core model. Optionally, add a `cache_provenance_path` field if provenance needs explicit tracking without breaking immutability.

---

### **4. Revised First-Burst Plan**

**Prerequisites:** Manual download verification of ONE spectrum from NASA Exoplanet Archive.

**Implementation Sequence:**

#### **Burst 1: Offline-First Provider Stub** (Dependent on Burst 0)

**Goal:** Create a static, fixture-based provider that parses verified local spectra without network access.

**Proposed files to create/modify:**

1. **`docs/Chunk_4/Chunk_4_plan_v4.md`** - Revised plan with evidence and implementation details
2. **`tests/fixtures/spectrum_archive/*.csv`** - Local fixtures derived from real archive data (once verified)
3. **`tests/test_provider_base.py`** (new) - Tests for offline provider stub
4. **`ecas/providers/base.py`** (new) - Base provider interface with fixture-only implementation for NASA

**Workflow:**

```python
# Pseudo-code structure:
def fetch_spectrum(provider: ArchiveProvider, record_id: str):
    if provider.can_fetch_live():
        # Fall back to cache or fixture if live fetch fails
        return load_from_cache_or_fixture(record_id)
    
    # For offline-first mode, always use fixture
    return parse_fixture_file(fixture_path)
```

**Key responsibilities for initial burst:**
- Parse local CSV files (`.csv` extension from archive wget output)
- Validate required columns (`wavelength`, `signal`)
- Preserve all additional columns verbatim
- Populate optional unit/observation-type fields if present
- Generate warnings for missing uncertainty data

#### **Test Plan for Burst 1:**

| Test Case | Fixture Type | Expected Behavior |
|-----------|---------------|-------------------|
| Valid archive spectrum CSV | Real archive format (verified) | Parses without error, populates all fields |
| Missing wavelength column | Malformed CSV | Raises `SpectrumImportError` |
| Non-numeric signal values | Invalid data | Raises error with line number |
| Negative uncertainty | Scientific edge case | Raises error, logged in warnings |
| Blank uncertainty cells | Real-world scenario | Preserved as `None`, warns user |
| Missing provenance fields | Offline fixture | Treated gracefully; no crash |

**Verification commands:**
```powershell
# Run persistence and import tests (offline)
$env:OFFLINE_MODE = "1"
Invoke-Pester -Path tests/test_csv_importer.py
Invoke-Pester -Path tests/test_persistence.py

# Run new provider stub tests
Invoke-Pester -Path tests/test_provider_base.py
```

#### **Documentation Plan:**

| Document | Location | Purpose |
|----------|----------|---------|
| Chunk 4 revised plan | `docs/Chunk_4/Chunk_4_plan_v4.md` | Implementation details, acceptance criteria |
| Archive provenance notes | `docs/Chunk_4/provenance_requirements.md` (new) | How to record citation requirements |
| Offline-first design doc | `docs/architecture/offline_provider_design.md` (new) | Cache policy and fixture usage patterns |

---

### **5. Risks and Open Decisions**

**Risks:**

| Risk | Impact | Mitigation |
|------|--------|------------|
| Live retrieval fails permanently | Delayed verification | Design offline-first workflow; accept fixtures as valid input |
| Archive returns unexpected file format (e.g., FITS instead of CSV) | Parser crash or data loss | Build flexible parser that detects extension and falls back to fallback readers |
| Units not provided in archive data | Incomplete `axis_unit`/`signal_unit` | Preserve missing units as `None`; warn user; allow manual override later |
| Citation requirements unclear | Legal/compliance issue | Research archive's legal page; document citation guidance separately |

**Open decisions:**

1. **Where to store provenance:** Should archival metadata be:
   - Embedded in a larger JSON BLOB alongside spectrum data?
   - Stored in a separate table row linked by `source_file`?
   - Documented externally (e.g., `.json` file)?
   → *Recommendation:* For Burst 1, embed as a top-level dict field; later refactor to external doc if needed.

2. **Provider interface scope:** Should we define a generic `ArchiveProvider` base class or just a single NASA implementation?
   → *Recommendation:* Start with NASA-only implementation; extract common methods only after second provider needed.

---

### **6. Recommendation**

**Status: First burst NOT ready for approval yet.**

**Reason:** We have NOT completed the live retrieval verification step that is required by the review prompt. The actual file format, column schema, and available provenance fields remain unknown.

**Single next action needed:**
> Manually navigate to https://exoplanetarchive.ipac.caltech.edu/cgi-bin/atmospheres/nph-firefly?atmospheres, search for a JWST spectrum record, attempt to download its data file (via wget script or direct link), and share:
> 1. The exact filename and size of the downloaded file
> 2. The first 15 lines of the file contents (as text)
> 3. Any error messages or unexpected behaviors observed
> 4. The archive's citation guidance page URL

**Once this manual verification is complete:** I will revise the plan with concrete evidence and propose an implementation that is fully compatible with the actual archive format.

---

### **7. Scope Confirmation**

**Confirmed: No files were changed.**

- All `read_files` and `search_codebase` tool calls were read-only operations
- No content was written to `docs/Chunk_4/*`, `ecas/*`, or any other project file
- The repository state remains unchanged from when I began this analysis
- No test executions occurred

**This response fulfills all required sections in PLAN mode only.**

---

## **Summary of Actions Taken**

1. ✅ Inspected current repository structure and Chunk 4 documentation files
2. ✅ Read `SpectrumData` model and existing CSV importer implementation  
3. ✅ Confirmed persistence layer uses JSON BLOB storage per project
4. ✅ Analyzed test coverage for CSV import, validation, and edge cases
5. ✅ Identified blockers preventing live verification of NASA archive format
6. ✅ Prepared comprehensive report following required response format

**Awaiting manual download verification before proposing concrete implementation.**




## USER INPUT ##

I am now going to manually get the info as requested by:

Manually navigate to [](https://exoplanetarchive.ipac.caltech.edu/cgi-bin/atmospheres/nph-firefly?atmospheres)<https://exoplanetarchive.ipac.caltech.edu/cgi-bin/atmospheres/nph-firefly?atmospheres>, search for a JWST spectrum record, attempt to download its data file (via wget script or direct link), and share:

1. The exact filename and size of the downloaded file
2. The first 15 lines of the file contents (as text)
3. Any error messages or unexpected behaviors observed
4. The archive's citation guidance page URL


Target: Wasp-39 b
I will not turn off any settings, so the table can be seen in full (how it displays on the site by default)

First: The search table. I will include links where it is given in the form of hyper links. IE. `https://exoplanetarchive.ipac.caltech.edu/overview/WASP-39%20b` Is the link provided by clicking on WASP-39 b on the table results.
If there is an empty cell in the table, i will say EMPTY. These cells are not always empty for these columns.
It should be noted, that when searching in the table under Planet Name for a specific target, Once you type in a name- the field returns like this: like '%wasp-39 b%'  (as an example)


Planet Name | Type of Spectrum | Reference | # Datapoints | Instrument | Facility | Min. Wavelength (mincrons) | Max Wavelength (microns) | Min. Obs. Date (BJD) | Max. Obs. Date (BJD) | Notes
WASP-39 b `https://exoplanetarchive.ipac.caltech.edu/overview/WASP-39%20b`  | Transmission | Feinstein et al. 2023 `https://ui.adsabs.harvard.edu/abs/2023Natur.614..670F/abstract` | 331 | Near Infrared Imager and Slitless Spectrograph (NIRISS) | NASA 6.5m James Webb Space Telescope (JWST) Satellite Mission | 0.631 | 2.7965 | EMPTY | EMPTY | EMPTY 



Now to the actual table that contains the data for the selected recording.

To begin with, I will download the file myself and provide information I see as I am downloading the data. I will then paste the contents of the data set afterwards. 


On the table, I see an option to Save the table. I click it, and a pop up box appears:

There are 7 file type options: 
1. IPAC Table (.tbl)
2. Comma-seperated values (.csv)
3. Tab-seperated values (.tsv)
4. VOTable - TABLEDATA (.vot)
5. VOTable - BINARY2 (.vot)
6. VOTable - FITS (.vot)
7. Parquet file with VOTable metadata (.parquet)

it then lists the file name.  I WILL BE USING THE .csv FILE AS AN EXAMPLE HERE. 

File name : table_WASP-39-b-Feinstein-et-al.-2023.csv

There are two options. Save table as displayed and Save table as originally retrieved. 
Text below says: The table will be saved in its current state, including its sorting order and derived columns, but excluding rows not accepted by any filters applied, as well as any hidden columns.

These are the first 4 lines of the .csv when opened in excel.

CENTRALWAVELNG	BANDWIDTH	PL_TRANDEP	PL_TRANDEPERR1	PL_TRANDEPERR2	PL_TRANDEP_AUTHORS	PL_RATROR	PL_RATRORERR1	PL_RATRORERR2	PL_RATROR_AUTHORS	PL_RADJ	PL_RADJERR1	PL_RADJERR2	PL_RADJ_AUTHORS	PL_TRANMID	PL_TRANMIDERR1	PL_TRANMIDERR2	ST_RAD	ST_RADERR1	ST_RADERR2	ST_RAD_AUTHORS
0.63096	0.00147	2.1065	0.01396	-0.01396	Feinstein et al. 2022	0.14514	0.00048	-0.00048	Calculated	1.2641	0.0328	-0.0328	Calculated				0.895	0.023	-0.023	Faedi et al. 2011
0.63403	0.00147	2.11714	0.01431	-0.01431	Feinstein et al. 2022	0.1455	0.00049	-0.00049	Calculated	1.2673	0.0328	-0.0328	Calculated				0.895	0.023	-0.023	Faedi et al. 2011
0.63683	0.00147	2.12373	0.0126	-0.0126	Feinstein et al. 2022	0.14573	0.00043	-0.00043	Calculated	1.2692	0.0328	-0.0328	Calculated				0.895	0.023	-0.023	Faedi et al. 2011


it is worth nothing that the PL_TRANMID	PL_TRANMIDERR1	PL_TRANMIDERR2 columns are empty in this example file.



here i will post links which may prove useful for this research:

`https://exoplanetarchive.ipac.caltech.edu/docs/tools.html`
this has a list of further links to follow:

Links to Exoplanet Archive Tools

Explore the Archive (a.k.a. Inventory Service)
AstroFetch (AI powered plain-language to ADQL query)
Interactive Tables Search and File Upload
Confirmed Planets Plotting Tool
Predicted Observables for Exoplanets Service (POE)
Transit and Ephemeris Service
Periodogram
Table Access Protocol (TAP)
Application Programming Interface (API)
Bulk Data Download
ExoFOP
EXOFAST: Transit and RV Fitting
Pre-generated Plots
System Aliases Lookup
Published Data Upload

`https://exoplanetarchive.ipac.caltech.edu/docs/data.html`
This contains more links for data in the archieve 

Links to Data in the Exoplanet Archive
Planetary Systems

    Planetary Systems (PS)
    Planetary Systems Composite Parameters (PSCompPars)
    Stellar Hosts
    Atmospheric Spectroscopy Table
    NExoList (NASA Exoplanet Archive Atmospheric Observation List)
    Microlensing Planets Table
    Direct Imaging Table
    Transiting Planets Table

Kepler

    KOI Table (Cumulative list)
    KOI Table (All lists)
    Kepler Positional Probabilities Table
    Kepler False Positive Probabilities Table
    Kepler Certified False Positives Table
    Kepler Completeness and Reliability Products
    Kepler Confirmed Names Table
    Kepler Stellar Table (Search)
    Kepler Threshold-Crossing Events Table (TCEs)

Transit Surveys

    TESS Project Candidates Table
    K2 Targets (Search)
    K2 Planets and Candidates Table
    K2 Confirmed Names Table
    CoRoT Astero-Seismology
    SuperWASP Light Curves (Search)
    KELT Light Curves (Search)
    KELT Praesepe Light Curves
    XO Light Curves
    HATNet Light Curves
    Cluster Light Curves
    TrES Light Curves

Other

    UKIRT Microlensing Survey (Search)
    MOA Microlensing Survey
    ROME/REA Microlensing Survey
    Gliese-Jahreiss Stars Table
    HWO ExEP Precursor Science Stars Table
    Mission Stars Table
    Mission Stars+ExoCat Table
    Frontier Development Lab Datasets
    CUTE Mission
    ASTERIA Mission
    Contributed Data Sets
    Interactive Tables Search and File Upload (for Planetary Systems and KOI Cumulative tables)


# RESPONSE FROM CHATGPT for plan_v4 #



The new CSV materially improves the review: it contains 331 data rows and 21 columns, matching the archive search result’s reported 331 datapoints for WASP-39 b. This strongly supports treating it as a real numerical export of the selected spectrum, rather than merely a metadata listing.

The remaining distinction is that the file was obtained using Save table as CSV. Cline still needs to determine how this export relates to the archive’s separate `wget` download workflow before designing automated retrieval around either route.

Several issues in Cline’s proposed implementation plan also need correcting: it assumes the archive data can be mapped to generic `wavelength` and `signal` columns, proposes rejecting negative uncertainty values despite the archive’s signed uncertainty convention, and specifies PowerShell Pester commands for Python tests. These should be addressed before any implementation is approved.

# ECAS Chunk 4 — Plan Review, Archive Evidence, and Next Instructions

## 1. Review Status

**Decision: The retrieval verification has advanced, but the implementation plan requires revision before approval.**

Cline correctly identified the need to inspect a real archive dataset before implementing a parser. The manual findings and uploaded CSV now provide concrete evidence about one WASP-39 b dataset from the NASA Exoplanet Archive.

The next step is not to start implementing a generic provider. It is to inspect the newly available evidence, establish how the exported data relates to the archive's retrieval workflow, and produce a smaller, technically correct implementation plan.

Continue using the established workflow:

1. PLAN and inspect.
2. Review the proposal.
3. Approve a narrowly scoped ACT task.
4. Run and inspect tests.
5. Record results and update documentation.
6. Plan the next small burst.

No implementation is approved by this review.

## 2. Review of Cline's Previous Plan

### 2.1 What Cline got right

- It correctly concluded that the first implementation burst was not ready for approval before the real dataset was inspected.
- It recognized that `SpectrumData.source_file` must remain a required local-file path.
- It identified the need to preserve archive provenance separately from the numerical data.
- It recognized that the first provider should focus on one archive rather than attempting to support every possible provider.
- It correctly deferred HITRAN, whose line-list data represents a different scientific data structure.
- It inspected existing import, persistence, and test code rather than planning the entire integration without examining ECAS.

These are useful foundations for the revised plan.

### 2.2 Important technical corrections

#### A. The uploaded CSV is real numerical data, not just archive metadata

The uploaded file is:

`ECAS_BETA/data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`

Its observed properties are:

| Property                    | Verified result                                                           |
| --------------------------- | ------------------------------------------------------------------------- |
| File size                   | 56,841 bytes                                                              |
| Format                      | Comma-separated CSV                                                       |
| Header columns              | 21                                                                        |
| Data rows                   | 331                                                                       |
| Archive-reported datapoints | 331                                                                       |
| First column                | `CENTRALWAVELNG`                                                          |
| Main spectral measurement   | `PL_TRANDEP`                                                              |
| Associated uncertainties    | `PL_TRANDEPERR1`, `PL_TRANDEPERR2`                                        |
| Additional information      | Bandwidth, planet-radius parameters, stellar radius, and reference fields |

The data-row count matches the archive search result for the selected WASP-39 b transmission spectrum.

This is strong evidence that the CSV contains wavelength-binned numerical spectral data. It is not evidence that every column is required by ECAS or that every field should be interpreted as a spectral measurement.

The archive export should be treated as the real sample for the next planning step. Cline must inspect it directly rather than relying only on the abbreviated excerpts in the manual notes.

#### B. Do not assume generic `wavelength` and `signal` column names

The archive uses names such as:

- `CENTRALWAVELNG`
- `BANDWIDTH`
- `PL_TRANDEP`
- `PL_TRANDEPERR1`
- `PL_TRANDEPERR2`

The initial plan's requirement to validate columns named `wavelength` and `signal` does not match this file.

The revised plan must explicitly map the archive's verified columns to ECAS's existing data representation. It must also document what the selected measurement means scientifically.

For this example, central wavelength and transit depth are the relevant starting points. Bandwidth and uncertainty values are also potentially important and should not be discarded without justification.

#### C. Preserve uncertainty conventions correctly

The sample includes negative values in fields ending in `ERR2`, such as `PL_TRANDEPERR2`.

These may represent signed lower uncertainty bounds rather than negative uncertainty magnitudes. The importer must not reject them merely because they are negative.

The revised plan must establish the meaning of these fields from archive documentation or the source publication and decide how ECAS will preserve them. Any conversion to a different uncertainty convention must be explicit, scientifically justified, and tested.

#### D. Missing fields are part of the real dataset

The `PL_TRANMID`, `PL_TRANMIDERR1`, and `PL_TRANMIDERR2` columns are empty in the inspected sample rows.

The revised plan must determine how the existing import system represents missing values. It must not assume that every optional column must be populated or that every missing value is an error.

Missing optional values should not automatically cause an otherwise valid spectrum to be rejected.

#### E. The CSV export and automated retrieval workflow are separate questions

The user obtained the file using the archive's table-export interface.

The archive also documents a separate workflow in which selected spectra can be downloaded through a generated `wget` script.

These two mechanisms must not be conflated.

The CSV now gives ECAS a concrete sample of the archive's numerical data. However, Cline still needs to establish which retrieval mechanism is suitable for the first working integration:

- Retrieving and importing an archive-provided table export.
- Retrieving the selected spectrum through the documented download-script workflow.
- Using another officially documented mechanism, if one is demonstrated to provide the required data.

The revised plan must identify the narrowest viable path and explain the evidence for choosing it. It should not assume that the file downloaded through one interface is identical to the file returned by another.

#### F. Do not silently substitute test fixtures for requested archive data

The previous pseudocode proposed falling back to a cache or fixture when live retrieval fails.

That is unsafe as a production behavior. If a user requests a particular archive record and the retrieval fails, ECAS must not silently return an unrelated fixture while implying that the requested record was retrieved.

Fixtures are appropriate for automated tests. A future cache may be appropriate for previously retrieved records if its behavior is explicitly designed and documented. Neither should silently masquerade as a successful retrieval of a different record.

#### G. Do not add an unnecessary provider abstraction

Cline's plan proposes creating `ecas/providers/base.py` and an offline-first provider stub before establishing the actual retrieval path.

That may be premature. A fixture-only provider is not, by itself, an implementation of archive retrieval.

The revised plan must identify the smallest useful capability and justify each new abstraction against the existing architecture. A NASA-specific implementation may be sufficient initially; shared abstractions can be introduced when demonstrated requirements justify them.

#### H. Provenance design is still unresolved

The previous report proposed several different approaches:

- A separate metadata structure or persistence record.
- A JSON sidecar file.
- A top-level dictionary field in the persisted data.
- An optional `cache_provenance_path` field.

These proposals are not equivalent, and the report does not establish that any one is necessary.

The revised plan must inspect the actual persistence implementation and establish how provenance can be retained without changing the meaning of `SpectrumData.source_file`.

At minimum, the design should consider the archive record identifier, archive name, retrieval date, source reference, and relevant publication citation. It should select only the information and storage changes required for the first burst.

The archive-level citation and the original scientific publication should remain distinguishable. The NASA Exoplanet Archive documents the Atmospheric Spectroscopy Table under DOI `10.26133/NEA36`; its citation guidance should be checked when finalizing the provenance design.

#### I. Correct the test commands

Cline's previous test plan specified commands such as:

```
Invoke-Pester -Path tests/test_csv_importer.py
```

Pester is a PowerShell testing framework, whereas these project tests are Python tests. The proposed commands are therefore inappropriate for the named Python test files.

The revised plan should use the project's existing Python test framework and established test commands. For example, if confirmed by the repository configuration:

```
python -m pytest tests/test_csv_importer.py -v
python -m pytest tests/test_persistence.py -v
```

Any new tests must follow the project's existing conventions. Do not introduce `OFFLINE_MODE` or assume it already exists without checking the codebase.

#### J. Avoid unnecessary documentation expansion

The previous plan proposed several new documentation files before the implementation scope was established.

Do not create separate architecture and provenance documents merely because those topics exist. First determine which decisions actually need to be recorded and where they belong in the existing documentation structure.

Chunk 4 planning documents should supplement the canonical project documentation, not replace or duplicate it unnecessarily.

## 3. What the Current Evidence Establishes

### Confirmed

- A real WASP-39 b table export has been obtained and is available in the project at the path specified above.
- The uploaded CSV contains 331 numerical data rows and 21 columns.
- The number of data rows matches the archive's reported datapoint count for the selected record.
- The data includes central wavelength, transit depth, uncertainty fields, and additional physical parameters and reference fields.
- Some optional fields are empty in the observed rows.
- The archive documents a separate `wget`-based download workflow for selected spectra.
- The current ECAS model requires `source_file: Path`; the proposed integration must preserve that contract unless repository inspection establishes a justified, compatible change.

### Not yet established

- Whether the archive's generated download script returns the same representation as the saved CSV.
- Whether direct programmatic retrieval is possible through a supported and stable endpoint.
- The complete scientific definitions and units of every relevant column.
- The exact mapping and validation rules needed to import this dataset into ECAS.
- The minimum provenance representation required by the existing persistence architecture.
- Whether a new provider abstraction is necessary for the first working capability.

The revised plan must distinguish confirmed facts from these remaining questions.

## 4. Required First-Burst Direction

The first burst should aim to establish one narrow, testable archive-retrieval-and-import workflow for one selected record from the NASA Exoplanet Archive.

Before proposing the implementation, Cline must:

1. Read the complete manual findings stored in `docs/Chunk_4/Chunk_4_plan_v4.md`.
2. Inspect `data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv` directly.
3. Inspect the actual current import, model, persistence, and test implementations.
4. Determine the verified scientific meaning of the columns needed for the initial import.
5. Identify the official retrieval mechanism and what it returns.
6. Propose the minimum changes needed to retrieve or import the selected record while preserving meaningful provenance.
7. Specify tests using the project's real test framework.
8. Identify work that should be deferred.

The initial capability should not automatically expand to FITS support, every archive export format, HITRAN, generalized multi-provider support, caching, or broad UI redesign.

Additional formats should be handled in later bursts if the project requires them and their data structures are properly understood.

## 5. Documentation and Versioning Instructions

The manual findings and this review should be preserved in the current Chunk 4 planning record.

Before creating or naming another plan file, inspect the actual directory. Cline's report indicates that versions 1, 2, and 3 already exist, and the manual findings are being added to the version 4 document.

Do not overwrite an existing plan or erase earlier reasoning. Use the next available version number only when a genuinely revised plan needs its own file.

The implementation log should remain a record of actual implementation activity, tests, results, and unresolved issues. It should not claim implementation or test execution during this planning-only step.

The decisions record should capture durable architectural decisions once they have been reviewed and accepted. Unapproved proposals should remain proposals, not be recorded as established project decisions.

---

## 6. Prompt for Cline

**Mode: PLAN only. No implementation or file edits.**

We are continuing ECAS Chunk 4. Review your previous “Plan v3 Review Report” together with the manual archive findings and uploaded CSV now available in the repository.

The manual findings are being recorded in:

`docs/Chunk_4/Chunk_4_plan_v4.md`

The actual CSV file is:

`data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`

These are essential inputs to this task. Read the entire relevant findings section in `Chunk_4_plan_v4.md` and inspect the CSV itself. Do not rely solely on excerpts in previous messages or on assumptions from your earlier plan.

Your task is to produce a corrected, evidence-based implementation proposal. Do not implement anything yet.

### Task 1 — Inspect the current planning and repository state

Inspect the actual current working tree before deciding what to read, create, or update.

Read the existing Chunk 4 planning files, including versions 1, 2, 3, and 4 if present. Preserve the reasoning and decisions already recorded.

Inspect the current implementations and tests relevant to:

- `ecas/models/spectrum.py`
- `ecas/ingestion/csv_importer.py`
- `ecas/persistence.py`
- `tests/test_csv_importer.py`
- `tests/test_persistence.py`
- Any relevant archive, UI, architecture, and documentation code or files discovered during inspection.

Confirm the actual paths and responsibilities rather than assuming they match an earlier report. Do not edit files.

### Task 2 — Inspect the real WASP-39 b CSV

Read the file at:

`data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`

Verify its actual:

- Filename, file size, format, row count, and column count.
- Header and relevant column names.
- Representative data rows.
- Missing-value patterns.
- Numeric types and any parsing complications.
- Wavelength range and other relevant numerical characteristics.

The current observed evidence is a 56,841-byte CSV with 331 data rows and 21 columns. Its header includes `CENTRALWAVELNG`, `BANDWIDTH`, `PL_TRANDEP`, `PL_TRANDEPERR1`, `PL_TRANDEPERR2`, and other physical-parameter and reference fields. The data-row count matches the archive search result's reported datapoint count.

Independently verify these observations against the actual file.

Do not assume the dataset uses generic `wavelength` and `signal` columns. Do not assume all 21 columns should be treated as measurements. Determine which fields are appropriate for the initial ECAS representation and explain why.

### Task 3 — Establish the scientific interpretation

Using the available archive documentation and source references, determine the meaning and units of the fields required for the first import.

Pay particular attention to:

- `CENTRALWAVELNG`
- `BANDWIDTH`
- `PL_TRANDEP`
- `PL_TRANDEPERR1`
- `PL_TRANDEPERR2`

Verify the meaning of the signed uncertainty fields before proposing validation rules or transformations. Do not reject negative lower uncertainty bounds merely because they are negative.

Determine how missing values in optional fields should be represented under the existing import contract. Do not require every column to contain a value.

Distinguish archive-confirmed information from assumptions or interpretations that remain unverified.

### Task 4 — Distinguish table export from automated retrieval

The user obtained the CSV through the archive's “Save table” interface. The archive also documents a separate selected-spectrum workflow that generates a `wget` script.

Assess what the current evidence establishes about each workflow.

Determine whether the CSV is suitable as a verified input format for the initial import, and whether the separate download-script workflow is necessary to establish automated retrieval.

If the exact automated retrieval mechanism remains unverified, identify the specific question that must be answered before implementation. Do not invent an API endpoint, claim a successful download that did not occur, or treat the CSV export as proof that an automated retrieval implementation already works.

Use official archive documentation and citation guidance where relevant.

### Task 5 — Review compatibility with existing ECAS code

Trace how the existing import and persistence workflow handles spectral data.

The current model is understood to require `source_file: Path`. Do not make it optional, rename it, or change its meaning without strong evidence that a compatible change is necessary.

Determine:

- Whether the existing import path can represent the verified archive data.
- How the axis, selected signal, uncertainties, units, and missing values would be handled.
- Whether additional columns must be retained and, if so, how.
- How provenance can be stored without confusing the local file path with the remote archive reference.
- What persistence changes, if any, are necessary.
- Which existing tests and behaviors might be affected.

Do not add several provenance fields, a new database schema, a sidecar file, or a generalized provider interface simply because these options are possible. Recommend the smallest compatible design and justify it against the actual code.

### Task 6 — Correct the previous proposed implementation and test plan

Address these specific problems from the previous report:

1. The proposed `wavelength` and `signal` column requirements do not match the observed archive headers.
2. Negative `ERR2` values must not be rejected without verifying their scientific meaning.
3. Missing optional columns or cells must be handled according to the verified data and existing import contract.
4. A test fixture must be derived from the actual data structure, not an invented schema.
5. A failed live retrieval must not silently return an unrelated fixture while implying that the requested record was retrieved.
6. Do not assume `OFFLINE_MODE` exists; inspect the code.
7. The previous `Invoke-Pester` commands were inappropriate for the Python test files. Propose commands that match the project's actual test framework.
8. Do not add new architecture and provenance documents unless the revised design demonstrates that they are necessary.

### Task 7 — Produce the revised first-burst plan

Return a narrow implementation proposal that identifies:

- The first working capability and its acceptance criteria.
- The chosen retrieval or import path and the evidence supporting it.
- The exact existing files that would change and any genuinely necessary new files.
- The proposed handling of the verified numerical fields, units, uncertainties, and missing values.
- The minimum provenance requirements and storage strategy.
- The fixture design based on the real CSV, if appropriate.
- The automated tests and exact test commands.
- Any necessary UI changes.
- Documentation updates and their intended locations.
- Deferred features and unresolved risks.

Keep the initial burst small. Do not bundle unrelated archive providers, HITRAN, generalized file-format support, caching, or broad refactoring into it without demonstrating a direct need.

If automated retrieval is still unverified, propose the smallest verification action needed to resolve that issue rather than designing an implementation around an invented retrieval mechanism.

### Required response format

1. **Repository and Documentation Inspection**
2. **CSV Verification**
3. **Scientific Interpretation and Mapping**
4. **Retrieval Workflow Assessment**
5. **ECAS Compatibility and Provenance**
6. **Revised First-Burst Plan**
7. **Tests and Acceptance Criteria**
8. **Risks and Deferred Work**
9. **Recommendation and Next Action**
10. **Scope Confirmation**

In the recommendation, explicitly state whether the first implementation burst is ready for approval. If it is not, identify the precise remaining blocker and the smallest next action.

Confirm that no files were edited, no code was implemented, and no tests were modified or run during this planning task.

Wait for review and explicit approval before implementation.

---

## 7. Next Step After Cline Responds

Review Cline's revised proposal before issuing an ACT prompt. The primary approval criteria are:

- The plan uses the actual CSV structure rather than generic assumed column names.
- Scientific meaning, units, uncertainty conventions, and missing values are handled deliberately.
- The automated retrieval path is supported by evidence.
- The proposed changes fit ECAS's existing model and persistence architecture.
- The first burst is independently testable and does not silently substitute fixtures for real archive data.
- The test commands match the Python project.
- Documentation changes preserve plan history and do not introduce unnecessary duplication.

If these conditions are met, the next step is to approve only the first implementation burst. Otherwise, resolve the specific remaining issue before proceeding.



Tighten the final Cline promptSeparate verification from implementation scope