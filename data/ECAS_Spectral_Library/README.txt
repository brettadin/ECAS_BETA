ECAS SPECTRAL LIBRARY
=====================

OVERVIEW

The ECAS Spectral Library contains curated infrared (IR) and ultraviolet-visible (UV-Vis) spectral datasets for molecules relevant to exoplanetary atmospheric characterization and astrochemistry.

The collection is a first-pass working library. It is not a complete spectral reference database, and file availability does not imply complete wavelength coverage or universal scientific suitability.

DIRECTORY STRUCTURE

Raw_Sources/
    IR/
        Original JCAMP-DX infrared spectra.
    Uv-Vis/
        Original TXT files selected from the MPI-Mainz UV/VIS Spectral Atlas.

Ready_For_ECAS/
    IR/
        Current IR files corresponding to the raw source files.
    Uv-Vis/
        Prepared CSV representations of the selected UV-Vis source files.

Documentation/
    IR/
        Historical acquisition manifest and current inventory/validation records.
    UV-Vis/
        Source candidate inventory, selected dataset manifest, selection report and validation summary.

CURRENT COLLECTION

IR:
    18 JCAMP-DX files across 13 molecules.

UV-Vis:
    22 original TXT files and 22 prepared CSV files across 15 molecules.

IR molecule coverage:
    C2H2, C2H4, CH4, CO, CO2, H2CO, H2O, H2S, N2O, NH3, NO, O3, SO2.

UV-Vis molecule coverage:
    C2H2, CH4, CO, CO2, H2CO, H2O, H2S, N2O, NH3, NO, NO2, O2, O3, PH3, SO2.

COMBINED COVERAGE

Present in both modalities:
    C2H2, CH4, CO, CO2, H2CO, H2O, H2S, N2O, NH3, NO, O3, SO2.

IR only:
    C2H4.

UV-Vis only:
    NO2, O2, PH3.

Currently absent from both:
    HCN.

SCIENTIFIC CONSIDERATIONS

IR:
    The IR files retain their individual JCAMP-DX metadata. Signal type, phase, source, resolution and experimental conditions vary. The collection includes both absorbance and transmittance data, and both gas-phase and liquid-phase samples. For example, the H2O collection contains one gas-phase spectrum and one liquid-phase spectrum.

    The current Ready_For_ECAS/IR files are byte-for-byte copies of their corresponding Raw_Sources/IR files. They have not undergone a separate conversion or normalization process.

UV-Vis:
    The prepared CSV datasets contain wavelength values in nm and absorption cross-sections in cm²/molecule. Individual datasets differ in wavelength coverage, temperature, sampling density and source publication.

    Some source datasets contain negative cross-section values. These have been retained rather than silently clipped or corrected.

    The CSV conversion process does not establish scientific suitability, completeness or measurement accuracy.

DATA PROVENANCE AND FALLBACK CURATION

Original source files are retained wherever possible. Source attribution, measurement conditions, units and known limitations should accompany any dataset used in scientific analysis.

Where primary collection data are unavailable or unsuitable, fallback sources may be considered. Fallback data must remain distinguishable from primary curated data. Their provenance, physical measurand, units, phase, experimental conditions and limitations must be recorded.

Different physical quantities or sample phases must not be silently treated as interchangeable.

No separate fallback-data directory is currently identified in this library structure.

DOCUMENTATION GUIDE

IR:
    Documentation/IR/manifest.csv
        Historical NIST acquisition records.
    Documentation/IR/validation_inventory.csv
        Current file-level IR inventory.
    Documentation/IR/validation_summary.txt
        Current IR collection summary and validation status.

UV-Vis:
    Documentation/UV-Vis/candidate_inventory.csv
        Historical source archive candidate records.
    Documentation/UV-Vis/dataset_manifest.csv
        Selected dataset provenance and local file mapping.
    Documentation/UV-Vis/selection_report.md
        Selection rationale, coverage and limitations.
    Documentation/UV-Vis/validation_summary.txt
        Prepared CSV structural validation results.

The historical acquisition and candidate inventories describe source searches, not the number of files currently stored in the prepared library.