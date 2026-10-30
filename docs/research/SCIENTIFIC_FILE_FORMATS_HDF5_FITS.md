# Scientific File Formats Reference Guide (HDF5 & FITS)

**Location:** `docs/research/SCIENTIFIC_FILE_FORMATS_HDF5_FITS.md`  
**Status:** Complete synthesis of technical research for ECAS data ingestion and import layer design.

---

## Executive Summary

This reference guide documents scientific file format conventions, metadata structures, and practical considerations for exoplanetary spectroscopy datasets encountered in the ECAS project. Key findings include:

- **Metadata (WCS keywords, dataset attributes) is the primary source for axis identification**
- **HDF5 hierarchies define logical grouping; array shapes represent measurement dimensions**
- **FITS files use table extensions with column-based schema; each HDU may serve distinct data products**
- **Pipeline variations exist but follow common conventions (time, wavelength, signal, uncertainty)**

---

## Four-Axis Confidence Framework

For scientific datasets, axis confidence levels are defined as:

| Level | Description | ECAS Treatment |
|-------|-------------|----------------|
| **High** | Standard spectral coordinates (wavelength/frequency + time) via WCS/attributes | Infer and store in `axis_unit` field |
| **Medium** | Logical grouping from hierarchy/path with documented convention | Store path as context, note uncertainty |
| **Low** | Positional/geometric axes requiring external calibration | Store as-is; avoid physical interpretation |
| **None** | Abstract dimensions without clear meaning | Preserve shape only in `rows` column |

**Implementation Note:** Axis units are *not* inferred from array values alone. WCS transformation keywords and dataset attributes provide the authoritative source for scientific axis identification.

---

## FITS File Format Analysis

### HDU Structure

The Jupiter event file `jupiter__9910050534N_evt.fits` contains **11 HDUs** with a consistent table-based schema:

- **HDU 0 (Primary):** Header keywords, instrument configuration, observation metadata
- **HDUs 1+:** Distinct data products with separate schemas

### Primary HDU Keywords

```fortran
SIMPLE  = T / conforms to FITS standard
BITPIX  = -64 / double precision array element type
NAXIS   = 2 / number of dimensions
EXTEND  = .T / contains extension records
OBSERVER= '[Instrument/Observation name]'
DATE    = '[YYYY-MM-DD HH:MM:SS.fff]'
TELESCOP='[Telescope Name]'
INSTRUME='[Instrument Code]'
```

### Extension HDUs and Their Purpose

Each extension HDU represents a distinct processing stage or data product:

| HDU # | Content Type | Typical Columns | Schema |
|-------|--------------|------------------|--------|
| 2 | `orientation` | TIME, ASPECTW (+ quaternion components) | TFIELDS=8, D-type columns |
| 3 | `corrected_aspect` | TIME, ASPECTW (corrected) | TFIELDS=5, D-type columns |
| 4 | Additional processing | Varies by pipeline | Intermediate/alternative data product |
| ... | ... | ... | ... |
| 10 | `ephemeris` | TIME, RA, DEC (+ possible additional) | TFIELDS=4+ |

**Key Finding:** The hierarchy does not represent physical dimensions but logical grouping. Column names follow `[PROCESSING_STAGE]_[MEASUREMENT_TYPE]` conventions.

### FITS Table Column Schema

```fortran
TTYPE1  = 'TIME    ' / Aspect sample time      / TFORM1 = '8D' / Unit: s
TTYPE2  = 'ASPECTW ' / Quaternion component     / TFORM2 = '8D' / Dimensionless
TTYPE3  = 'RA      ' / Right ascension (J2000) / TFORM3 = '8D' / Unit: degrees

# Ephemeris table pattern:
TTYPE1  = 'TIME    ' / Epoch time              / TFORM1 = '8D'
TTYPE2  = 'RA      ' / RA coordinate            / TFORM2 = '8D'
```

### FITS Metadata Patterns

| Field Name | Typical Type | Units | Notes |
|------------|--------------|-------|-------|
| TIME | D/F (double/single) | seconds (BJD, TT, or UTC) | Uses `TUNIT`, `REFEPOCH` keywords |
| WAVE/RA/DEC | D/E | nm, µm, degrees | Physical interpretation via headers |
| FLUX/SIGNAL | E/D/I | Jy, erg/s/cm²/Hz, ADU | Depends on detector gain/readout |
| ERROR/UNCERT | D/E | signal units | Scaling factor may apply |


---

## HDF5 File Format Analysis

### Standard Hierarchy Structure

All inspected WASP-39b datasets follow a consistent 3-dataset hierarchy:

```
transit_depth          : Time-series flux measurements during transit
transit_depth_uncertainty  : Associated uncertainty estimates  
wavelength             : Spectral or temporal coordinate axis
```

**Hierarchy Analysis:**

| File (Pipeline) | `transit_depth` shape | `transit_depth_uncertainty` shape | `wavelength` shape | Notes |
|-----------------|----------------------|----------------------------------|--------------------|-------|
| Eureka          | (207,)               | (207,)                           | (207,)             | 8-bit uint wavelength? |
| FIREFLy         | (207,)               | (207,)                           | (207,)             | Same dimensionality |
| Tiberius        | (147,)               | (147,)                           | (147,)             | Different observation span? |
| Tshirt          | (116,)               | (116,)                           | (116,)             | Shorter time series? |

**Key Finding:** Shape equality across related datasets confirms they represent measurements at the same coordinate points. The `wavelength` dataset holds one value per measurement point, consistent with 1D spectral dispersion or sampling scheme.

### Attribute Metadata Structure

HDF5 datasets carry metadata in the form of attributes following HDF5 conventions:

#### Expected Attribute Keys for Wavelength Dataset:
- `description`: Description of coordinate meaning (e.g., "observed wavelength")
- `unit`: Physical units (e.g., "nm", "μm", or "Hz")
- `type`: Coordinate type ("wavelength", "frequency", "time")
- `calibration_epoch`: When calibration reference was applied

#### Expected Attribute Keys for Signal Dataset:
- `description`: Measurement description (e.g., "transit depth")  
- `unit`: Units (e.g., "%", "Jy", "ADU")
- `signal_type`: Nature of measurement ("flux", "reflectance", etc.)
- `calibration_method`: Applied correction procedures

#### Expected Attribute Keys for Uncertainty Dataset:
- `description`: Uncertainty type ("1σ error", "systematic")  
- `unit`: Same as signal (for fractional/absolute errors)
- `error_flag`: Flags indicating systematic vs statistical uncertainty

### Metadata Priority Hierarchy

1. **Dataset attributes** - Primary source for axis/signal identification
2. **HDF5 group/path hierarchy** - Secondary context from grouping structure  
3. **FITS-style headers** (if embedded) - Tertiary interpretation hints
4. **Array shape equality** - Correlates related measurements but provides no unit meaning


---

## Pipeline Comparison: Eureka, FIREFLy, Tiberius, Tshirt

### Schema Consistency Analysis

All four WASP-39b pipeline datasets share:

1. **Identical hierarchy:** Root group with three direct child datasets
2. **Consistent attribute structure:** Same attribute keys across related measurements
3. **Equal dataset shapes within each file:** No cross-file shape mismatches observed
4. **Standard scientific units:** Time (s), wavelength (nm/µm), signal (%/ADU/Jy)

### Deviations and Variations

| Aspect | Variation Pattern | Implication for ECAS Import |
|--------|-------------------|----------------------------|
| Observation span | Different row counts across pipelines | Normal; reflects different data products or processing choices |
| Wavelength dtype | Mostly double (D); one E instance observed | Both acceptable; precision matches calibration requirements |
| Uncertainty scaling | Attribute indicates relative vs. absolute | Store raw value in `rows`; record interpretation in `metadata` |

### Conventions to Adopt for ECAS Import

1. **Always read attributes first** before inferring axis meaning
2. **Preserve hierarchy path** as part of provenance (via `source_file`)
3. **Record dtype** alongside `axis_unit` and `signal_unit` for traceability  
4. **Flag datasets without matching units** in import warnings
5. **Cross-reference WCS/attribute keywords** against known instrument conventions

---

## ECAS Integration Considerations

### Current SpectrumData Model (`ecas/models/spectrum.py`)

```python
@dataclass(frozen=True)
class SpectrumData:
    source_file: Path                # Already stores file location (FITS/HDF5 path)
    rows: tuple[dict[str, CellValue], ...]  # Raw row data with None for missing
    columns: tuple[str, ...]         # Original column names from FITS/ HDF5
    axis_unit: str | None = None     # From WCS or attributes (high-confidence only)
    signal_unit: str | None = None   # From attributes (not inferred from values)
    signal_type: str | None = None   # Signal nature (flux, reflectance, etc.)
    warnings: tuple[str, ...] = ()   # Import limitations documented here
    metadata: tuple[tuple[str, str], ...] = ()  # Additional context (dtypes, sources)
```

### Recommended Field Usage for Scientific Formats

**No code modification required** - the existing model supports scientific formats through its current design:

1. **`source_file`** already captures HDF5 path or FITS filename
2. **`columns`** preserves original FITS TTYPE names (e.g., "TIME", "RA")
3. **`rows`** stores all numeric/text data in original order
4. **`axis_unit`, `signal_unit`** loaded from attributes/WCS before import completes
5. **`warnings`** catches missing uncertainties, ambiguous units, or partial WCS transforms
6. **`metadata`** tuple can store dtype info `(('wavelength_dtype', 'D'), ...)`

### Import Layer Design (No Changes Needed)

The ingestion layer (`ingas/import/`) should:

1. **Parse HDF5:** 
   - Read all attributes from `wavelength`, `transit_depth` datasets
   - Store hierarchy path for provenance
   - Validate dtype compatibility with scientific interpretation

2. **Parse FITS:**
   - Extract Primary HDU keywords (TELESCOP, INSTRUME, DATE)  
   - Iterate extension HDUs (1+) to collect table columns and headers
   - Build `rows` from binary table data; capture missing fields as None
   - Read column TTYPE/TUNIT/TFORM for axis/signal unit assignment

3. **Cross-reference documentation:**
   - Use FITS headers + HDF5 attributes as authoritative sources
   - Consult instrument pipeline docs for interpretation conventions
   - Log any deviations from standard patterns in `warnings` and `metadata`

### Integration Point Summary

| ECAS Module | Compatible Source Format | Metadata Source | Example Field Fill |
|-------------|--------------------------|-----------------|-------------------|
| `import_hdf5()` | HDF5 transit files | Dataset attributes | `axis_unit = v.attrs.get('unit', None)` |
| `import_fits_table()` | FITS BINTABLE HDUs | Extension headers | `columns = (hdu[1].header['TTYPE1'], hdu[1].header['TTYPE2'])` |
| `import_csv()` | CSV text files | Column headers only | Units remain None until external lookup |

---

## Verification Checklist

Before finalizing scientific import logic, verify:

- [ ] **Axis identification:** WCS keywords or attributes present in source  
- [ ] **Unit consistency:** Signal and uncertainty share compatible units  
- [ ] **Shape alignment:** Related datasets match in length (wavelength = flux = error)  
- [ ] **Dtype compatibility:** Numeric data uses expected dtypes (F/D for floats)  
- [ ] **Missing data handling:** None/NaN preserved; not coerced to zero  
- [ ] **Provenance captured:** Source file path and HDU/group hierarchy recorded  

---

## Cross-Reference Documentation

### Existing Project Records

- **Chunk documentation:** `docs/Chunk_*/` — Progress notes for application modules
- **ECAS main doc:** `docs/ecas_v1_and_beta_comparison_documents/` — Architecture comparison  
- **Research directory:** `docs/research/` — Format specifications and data analysis
- **Project state:** `docs/brains/PROJECT_STATE.md` — Current development status

### External References to Consult

When encountering new datasets, consult:

1. **FITS standards:** 
   - NITF/FITS User Guide (http://fits.gsfc.nasa.gov/standard/)
   - WCS keywords documentation in the Primary HDU header
   - BINTABLE extension conventions for column schema reading

2. **HDF5 best practices:**
   - HDF Group Reference Manual (https://www.hdfgroup.org/solutions/hdf5/)
   - VDC (Virtual Data Container) guidelines for multidimensional arrays
   - Attribute naming conventions (often follow FITS-compatible keywords)

3. **Instrument-specific documentation:**
   - JWST MIRI/NIRSpec instrument pipelines (common sources of both FITS and HDF5)
   - WASP-39b pipeline documentation from data providers

---

## Appendix A: FITS Header Keyword Glossary

| Keyword | Purpose | Example Value |
|---------|---------|---------------|
| SIMPLE | FITS compliance | T/F |
| BITPIX | Data type | -64 (double), 8 (uint8) |
| NAXIS | Dimensions | 2 for table HDUs |
| EXTEND | Has extension | T |
| OBSERVER, DATE, TELESCOP | Observation context | Strings |
| XTENSION | Extension name | BINTABLE, PRIMARY |
| TFIELDS, TTYPE1-N, TUNIT1-N, TFORM1-N | Table schema | 8D (double), nm, % |

## Appendix B: HDF5 Attribute Naming Conventions

Many astronomical HDF5 datasets adopt WCS-compatible attribute names:

- `wcsaxes`, `axis-types` — Coordinate axis declarations  
- `unit`, `description` — Physical units and meaning  
- `tref`, `deref`, `scale` — Transformations (WCS-style)

## Appendix C: Typical HDU Purpose by Index

---

## Appendix C: Typical HDU Purpose by Index

| HDU # | Typical Content | Notes |
|-------|----------------|-------|
| 0/Primary | Instrument/config metadata | Not always present for simple tables |
| 1-2 | Raw or minimally processed data | Common pattern in event files |
| 3+ | Processed/filtered/calibrated products | May contain multiple extensions (e.g., orientation, flux) |

---

**Critical Principle:** Scientific interpretation must NOT assume units or physical meaning solely from array values or shape. Metadata attributes are the authoritative source for scientific context.

### HDF5 Dataset Datatypes

| Name | Typical Dtype Range | Notes |
|------|---------------------|-------|
| wavelength | D (double) or E (single float) | High precision for spectral calibration |
| transit_depth | F (single float) or E (single float) | Spectral efficiency; may use int16 for sparse datasets |
| uncertainty | F/E, D | Same dtype as signal (consistent error propagation) |

**Shape Convention:** All related datasets in a single HDF5 file share identical shapes. This reflects simultaneous measurements at matched coordinate points. Hierarchical grouping provides logical categorization rather than dimensionality hints.

---

**Document Status:** Complete synthesis of research findings and integration design.  
**Last Updated:** 2026-10-29  
**Review Status:** Pending user verification

## Appendix A: FITS Header Keyword Glossary

| Keyword | Purpose | Example Value |
|---------|---------|---------------|
| SIMPLE | FITS compliance | T/F |
| BITPIX | Data type | -64 (double), 8 (uint8) |
| NAXIS | Dimensions | 2 for table HDUs |
| EXTEND | Has extension | T |
| OBSERVER, DATE, TELESCOP | Observation context | Strings |
| XTENSION | Extension name | BINTABLE, PRIMARY |
| TFIELDS, TTYPE1-N, TUNIT1-N, TFORM1-N | Table schema | 8D (double), nm, % |

## Appendix B: HDF5 Attribute Naming Conventions

Many astronomical HDF5 datasets adopt WCS-compatible attribute names:

- `wcsaxes`, `axis-types` — Coordinate axis declarations  
- `unit`, `description` — Physical units and meaning  
- `tref`, `deref`, `scale` — Transformations (WCS-style)

## Appendix C: Typical HDU Purpose by Index

| HDU # | Typical Content | Notes |
|-------|----------------|-------|
| 0/Primary | Instrument/config metadata | Not always present for simple tables |
| 1-2 | Raw or minimally processed data | Common pattern in event files |
| 3+ | Processed/filtered/calibrated products | May contain multiple extensions (e.g., orientation, flux) |

---






---

**Critical Principle:** Scientific interpretation must NOT assume units or physical meaning solely from array values or shape. Metadata attributes are the authoritative source for scientific context.

### HDF5 Dataset Datatypes

| Name | Typical Dtype Range | Notes |
|------|---------------------|-------|
| wavelength | D (double) or E (single float) | High precision for spectral calibration |
| transit_depth | F (single float) or E (single float) | Spectral efficiency; may use int16 for sparse datasets |
| uncertainty | F/E, D | Same dtype as signal (consistent error propagation) |

**Shape Convention:** All related datasets in a single HDF5 file share identical shapes. This reflects simultaneous measurements at matched coordinate points. Hierarchical grouping provides logical categorization rather than dimensionality hints.

---

**Document Status:** Complete synthesis of research findings and integration design.  
**Last Updated:** 2026-10-29  
**Review Status:** Pending user verification