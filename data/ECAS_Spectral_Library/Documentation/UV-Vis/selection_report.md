# ECAS UV–Vis Spectral Collection — First-Pass Selection Report

## 1. Purpose and source

This document describes the first-pass UV–Vis spectral collection selected for ECAS.

**Source:** MPI-Mainz UV/VIS Spectral Atlas, 2013-06-24 archive snapshot.

The collection is a curated selection from that archive. It is not a complete representation of all available measurements, nor does it claim complete spectral coverage for every ECAS target molecule.

The original selected source files are retained in the project.

## 2. Current directory structure

Original selected source files:

`Raw_Sources/Uv-Vis/<molecule>/*.txt`

Prepared numerical datasets:

`Ready_For_ECAS/Uv-Vis/<molecule>/*.csv`

Dataset manifest:

`Documentation/UV-Vis/dataset_manifest.csv`

Candidate inventory:

`Documentation/UV-Vis/candidate_inventory.csv`

Validation summary:

`Documentation/UV-Vis/validation_summary.txt`

The candidate inventory records source archive candidates, including records that were not selected. It is not an inventory of files currently stored in the prepared collection.

## 3. Current collection inventory

- Original TXT files: 22
- Prepared CSV files: 22
- Molecules represented: 15
- Source archive: MPI-Mainz UV/VIS Spectral Atlas, 2013-06-24 snapshot

Molecules represented:

C2H2, CH4, CO, CO2, H2CO, H2O, H2S, N2O, NH3, NO, NO2, O2, O3, PH3 and SO2.

Target molecules without a selected UV–Vis dataset in this archive snapshot:

- HCN
- C2H4

The absence of a selected dataset does not establish that no relevant spectral information exists elsewhere.

## 4. Selected datasets

### H2O — Water
- H2O_JPL-2010(2011)_298K_121-198nm(rec).txt
- 121–198 nm
- 98 points
- 298 K

### CO2 — Carbon dioxide
- CO2_HuestisBerkowitz(2010)_300K_0.1254-201.6nm(evaluation).txt
- 0.1254–201.6 nm
- 25,016 points
- 300 K
- CO2_Shemansky(1972)_298K_169.57-300.00nm.txt
- 169.57–300 nm
- 297 points
- 298 K

### CO — Carbon monoxide
- CO_Cook(1965)_295K_60.00-100.25nm.txt
- 60–100.25 nm
- 268 points
- 295 K

### CH4 — Methane
- CH4_Ditchburn(1955)_298K_27.8-151.3nm.txt
- 27.8–151.3 nm
- 73 points
- 298 K
- CH4_Kameta(2002)_298K_52-125nm.txt
- 52.054–124.629 nm
- 3,077 points
- 298 K

### NH3 — Ammonia
- NH3_Cheng(2006)_298K_140-230nm(0.02nm).txt
- 140–230 nm
- 4,501 points
- 298 K

### O2 — Oxygen
- O2_Bogumil(2003)_293K_235-389nm.txt
- 235.0718–389.0553 nm
- 1,374 points
- 293 K
- O2_Bogumil(2003)_293K_650-799.6nm.txt
- 649.999–799.6729 nm
- 717 points
- 293 K

### O3 — Ozone
- O3_Bogumil(2003)_293K_230-1070nm.txt
- 229.9956–1070.2802 nm
- 4,244 points
- 293 K

### SO2 — Sulfur dioxide
- SO2_ManattLane(1993)_293K_106.1-403.7nm.txt
- 106.1–403.7 nm
- 2,977 points
- 293 K
- SO2_VandaeleHermansFally(2009)_298K_227.275-416.658nm.txt
- 227.275–416.658 nm
- 39,999 points
- 298 K

### H2S — Hydrogen sulfide
- H2S_WuChen(1998)_295K_160-260nm.txt
- 159.465–259.46 nm
- 20,000 points
- 295 K

### N2O — Nitrous oxide
- N2O_JPL-2010(2011)_298K_160-240nm(rec).txt
- 160–240 nm
- 71 points
- 298 K
- N2O_Zelikoff(1953)_298K_108-208nm.txt
- 108.2–208 nm
- 223 points
- 298 K

### C2H2 — Acetylene
- C2H2_Vattulainen(1997)_292K_195-300nm(2bar).txt
- 195–300 nm
- 211 points
- 292 K
- C2H2_Wu(1989)_155K_153-210nm.txt
- 153.204–210 nm
- 9,467 points
- 155 K

### PH3 — Phosphine
- PH3_Halmann(1963)_296K_185-218nm.txt
- 185–218 nm
- 25 points
- 296 K

### NO — Nitric oxide
- NO_Watanabe(1967)_298K_110-135nm.txt
- 110.06–134.51 nm
- 258 points
- 298 K
- NO_Watanabe(1967)_298K_58-110nm.txt
- 58.43–109.95 nm
- 573 points
- 298 K

### NO2 — Nitrogen dioxide
- NO2_Bogumil(2003)_293K_230-930nm.txt
- 229.9432–930.1105 nm
- 3,729 points
- 293 K

### H2CO — Formaldehyde
- CH2O_JPL-2010(2011)_298K_226-375nm(rec,1nm).txt
- 226–375 nm
- 150 points
- 298 K

The dataset manifest remains the authoritative file-level record for the selected datasets and their local prepared-file mappings.

## 5. Data representation

The prepared CSV datasets contain:

- Wavelength in nm
- Absorption cross-section in cm²/molecule

The numerical values were transferred from the two-column atlas source files without smoothing, interpolation, normalization or resampling.

Original TXT files are retained so that prepared data can be traced back to their source representations.

## 6. Selection considerations and limitations

1. The source is a 2013 archive snapshot, not the current online atlas.
2. The atlas contains measurements with different wavelength ranges, sampling densities, temperatures and experimental conditions.
3. A filename wavelength range does not establish uniform sampling or guarantee that every intermediate wavelength is represented.
4. Multiple datasets for one molecule may represent distinct spectral regions, temperatures, resolutions or experimental conditions. They must not be merged blindly.
5. The CO2 evaluation dataset and the separate Shemansky dataset remain separate.
6. The PH3 dataset contains only 25 points and should be treated as limited coverage rather than a high-resolution reference spectrum.
7. The O2 visible-band dataset contains negative reported cross-section values. These values have been retained.
8. Negative values are also present in some NH3, SO2, C2H2 and NO2 datasets. The validation summary records their counts.
9. HCN had one sparse/max-style candidate record but no selected continuous spectrum.
10. No matching C2H4/ethylene cross-section file was found in this archive snapshot.
11. Numerical parsing, structural validation and CSV conversion do not establish measurement uncertainty, scientific suitability, completeness or licensing permissions.

## 7. Fallback curation

Where the primary selected collection does not provide suitable data for a molecule or spectral region, additional sources may be investigated.

Fallback data must be clearly distinguished from the primary collection and must retain:

- Original source and publication or database attribution
- Molecular identity
- Physical measurand and data type
- Units
- Sample phase
- Temperature and pressure, where available
- Spectral coverage and resolution or sampling information
- Known limitations and suitability caveats

Different physical quantities must not be treated as interchangeable merely to fill a coverage gap. For example, absorption cross-sections, molar absorptivity, absorbance, transmittance and quantum yields represent different quantities or data types.

Likewise, gas-phase and condensed-phase measurements must remain distinguishable.

The current UV–Vis collection contains the selected primary datasets described in this report. No separate fallback UV–Vis collection is identified in the current directory structure.

## 8. Validation

The current prepared CSV validation results are recorded in:

`Documentation/UV-Vis/validation_summary.txt`

The current report records 22 datasets with successful row-count checks and non-decreasing wavelength values. Negative cross-section values are reported rather than silently corrected.

These checks establish basic structural consistency only. They do not certify scientific accuracy or suitability.

## 9. Related documentation

- `dataset_manifest.csv` — selected dataset provenance, source details and local file mapping.
- `candidate_inventory.csv` — historical source archive candidate records.
- `validation_summary.txt` — prepared CSV structural validation.
- `../IR/validation_inventory.csv` — current IR file inventory.
- `../IR/validation_summary.txt` — current IR inventory summary.