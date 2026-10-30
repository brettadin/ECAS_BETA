# ECAS UV–Vis collection — first-pass extraction

Source: MPI-Mainz UV/VIS Spectral Atlas archive supplied in this conversation (`uv-vis-spectral-atlas-2013-06-24.zip`).
This is a curated first-pass extraction, not a claim that the atlas provides complete spectra for all ECAS species.

## Output

- `Ready_For_ECAS/<molecule>/*.csv`: selected numerical datasets.
- `Raw_Sources/MPI_Mainz_selected_originals/<molecule>/*.txt`: unchanged originals for selected datasets.
- `Documentation/dataset_manifest.csv`: selected dataset metadata and output mapping.
- `Documentation/candidate_inventory.csv`: all matched source files for the 17 targets, including unselected records.

CSV columns are wavelength in nm and absorption cross-section in cm²/molecule. Values are copied from the two-column atlas files without smoothing, interpolation, normalization or resampling.

## Coverage summary

- Selected datasets: 22
- Molecules with at least one selected dataset: 15 of 17 (C2H2, CH4, CO, CO2, H2CO, H2O, H2S, N2O, NH3, NO, NO2, O2, O3, PH3, SO2)
- No selected continuous dataset in this archive: HCN, C2H4

### H2O — Water
- Candidate source files matched: 59; selected: 1.
- `H2O_JPL-2010(2011)_298K_121-198nm(rec).txt` — 121.0000–198.0000 nm; 98 points; 298 K.

### CO2 — Carbon dioxide
- Candidate source files matched: 48; selected: 2.
- `CO2_HuestisBerkowitz(2010)_300K_0.1254-201.6nm(evaluation).txt` — 0.1254–201.6000 nm; 25016 points; 300 K.
- `CO2_Shemansky(1972)_298K_169.57-300.00nm.txt` — 169.5700–300.0000 nm; 297 points; 298 K.

### CO — Carbon monoxide
- Candidate source files matched: 42; selected: 1.
- `CO_Cook(1965)_295K_60.00-100.25nm.txt` — 60.0000–100.2500 nm; 268 points; 295 K.

### CH4 — Methane
- Candidate source files matched: 27; selected: 2.
- `CH4_Ditchburn(1955)_298K_27.8-151.3nm.txt` — 27.8000–151.3000 nm; 73 points; 298 K.
- `CH4_Kameta(2002)_298K_52-125nm.txt` — 52.0540–124.6290 nm; 3077 points; 298 K.

### NH3 — Ammonia
- Candidate source files matched: 33; selected: 1.
- `NH3_Cheng(2006)_298K_140-230nm(0.02nm).txt` — 140.0000–230.0000 nm; 4501 points; 298 K.

### O2 — Oxygen
- Candidate source files matched: 164; selected: 2.
- `O2_Bogumil(2003)_293K_235-389nm.txt` — 235.0718–389.0553 nm; 1374 points; 293 K.
- `O2_Bogumil(2003)_293K_650-799.6nm.txt` — 649.9990–799.6729 nm; 717 points; 293 K.

### O3 — Ozone
- Candidate source files matched: 210; selected: 1.
- `O3_Bogumil(2003)_293K_230-1070nm.txt` — 229.9956–1070.2802 nm; 4244 points; 293 K.

### SO2 — Sulfur dioxide
- Candidate source files matched: 99; selected: 2.
- `SO2_ManattLane(1993)_293K_106.1-403.7nm.txt` — 106.1000–403.7000 nm; 2977 points; 293 K.
- `SO2_VandaeleHermansFally(2009)_298K_227.275-416.658nm.txt` — 227.2750–416.6580 nm; 39999 points; 298 K.

### H2S — Hydrogen sulfide
- Candidate source files matched: 15; selected: 1.
- `H2S_WuChen(1998)_295K_160-260nm.txt` — 159.4650–259.4600 nm; 20000 points; 295 K.

### HCN — Hydrogen cyanide
- Candidate source files matched: 1; selected: 0.
- Only a sparse/max-style record was found; not promoted to Ready_For_ECAS as a continuous spectrum.

### N2O — Nitrous oxide
- Candidate source files matched: 72; selected: 2.
- `N2O_JPL-2010(2011)_298K_160-240nm(rec).txt` — 160.0000–240.0000 nm; 71 points; 298 K.
- `N2O_Zelikoff(1953)_298K_108-208nm.txt` — 108.2000–208.0000 nm; 223 points; 298 K.

### C2H2 — Acetylene
- Candidate source files matched: 26; selected: 2.
- `C2H2_Vattulainen(1997)_292K_195-300nm(2bar).txt` — 195.0000–300.0000 nm; 211 points; 292 K.
- `C2H2_Wu(1989)_155K_153-210nm.txt` — 153.2040–210.0000 nm; 9467 points; 155 K.

### C2H4 — Ethylene
- Candidate source files matched: 0; selected: 0.
- No matching C2H4/ethylene cross-section files found in this archive snapshot.

### PH3 — Phosphine
- Candidate source files matched: 3; selected: 1.
- `PH3_Halmann(1963)_296K_185-218nm.txt` — 185.0000–218.0000 nm; 25 points; 296 K.

### NO — Nitric oxide
- Candidate source files matched: 13; selected: 2.
- `NO_Watanabe(1967)_298K_110-135nm.txt` — 110.0600–134.5100 nm; 258 points; 298 K.
- `NO_Watanabe(1967)_298K_58-110nm.txt` — 58.4300–109.9500 nm; 573 points; 298 K.

### NO2 — Nitrogen dioxide
- Candidate source files matched: 203; selected: 1.
- `NO2_Bogumil(2003)_293K_230-930nm.txt` — 229.9432–930.1105 nm; 3729 points; 293 K.

### H2CO — Formaldehyde
- Candidate source files matched: 81; selected: 1.
- `CH2O_JPL-2010(2011)_298K_226-375nm(rec,1nm).txt` — 226.0000–375.0000 nm; 150 points; 298 K.

## Important limitations and interpretation

1. This archive is a 2013 snapshot. It is not the current online atlas.
2. The atlas contains many narrow-window measurements. A wavelength range in a filename is not proof of continuous, uniformly sampled coverage; the manifest reports observed numeric endpoints and point counts.
3. Some target species have only limited UV coverage in this snapshot. This extraction does not invent missing wavelength regions.
4. CO2 includes an evaluation dataset and a separate literature dataset. They are retained separately and are not concatenated.
5. CH4, O2, SO2, N2O, C2H2 and NO have multiple selected measurements because they represent distinct regions, temperatures, resolutions or experimental conditions. They must not be merged blindly.
6. The PH3 record is sparse (25 points) and should be treated as limited coverage, not a high-resolution reference spectrum.
7. The O2 visible-band file contains small negative reported values. These are preserved exactly rather than clipped; assess before using in physical calculations.
8. Candidate inventory matching is based on exact leading species formula tokens, with CH2O used as the formaldehyde alias. It excludes quantum-yield files.
9. Numerical parsing and CSV conversion do not establish scientific suitability, measurement uncertainty, licensing permissions or completeness. Source publications and original files should be retained.
10. Files marked not selected may still be useful later; the candidate inventory preserves their identities and basic inspection results.
