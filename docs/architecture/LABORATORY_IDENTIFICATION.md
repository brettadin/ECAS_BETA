# Local laboratory molecular identification

Implemented locally on 2026-10-29. This workflow is distinct from atmospheric
transit-depth comparison and fixed-parameter forward-model species attribution.

## User workflow

1. Import a laboratory observation in Spectral Data, or reopen one from Projects.
   Supported local reference schemas are uncompressed AFFN JCAMP-DX and the
   explicit wavelength_nm/absorption_cross_section_cm2_per_molecule CSV schema.
2. In Comparisons, open **Local library: Identify Molecules**.
3. The current input is added on first opening when available. Use **Add observation
   files…** to select several files directly, **Add current input**, or add observations
   from the active project. Check the inputs to analyse; the planet filter limits
   which checked inputs are included. The checked count and per-input progress make
   batch execution explicit; clicking an observation previews its source measurements.
4. Select molecule checkboxes in IR and/or UV–Vis. Choose one source/condition
   variant per selected molecule. Variants are not automatically merged. **Show
   selected reference spectra** previews source measurements, without fitting or
   normalization, in separate tabs for each modality, quantity and coordinate unit.
5. Run **Identify Molecules**. Every selected reference receives a result or an
   explicit blocked reason. Inspect individual observations using the result
   selector. The plot and table share stable molecular colours. Blocked results keep
   the input visible in its original units, with reasons immediately above the graph;
   a measured preview never represents a successful fit or fabricated sigma.
6. Export a checksum-bound JSON analysis record; **Open and reproduce saved
   identification** recomputes from saved input arrays and settings without
   requiring original files. This does not re-ingest or authenticate raw sources.

Planetary transit depths are blocked here. **Open atmospheric comparison for checked
inputs** transfers checked transit snapshots and metadata into the existing model
workspace, selects strict cached ExoMol mode, and leaves generation explicit. This
does not turn laboratory library files into atmospheric opacities. Laboratory batches
run all checked inputs independently; atmospheric generation still runs one chosen
observation at a time. A successful self-comparison of a
reference file checks numerical consistency, not independent identification.

### Feedback reproduction and FITS containers (2026-10-29)

The cached Rustamkulov WASP-39 b NIRSpec PRISM observation has 207 transit-depth
points (0.53146–5.34413 microns). The corrected panel displays all 207 before and
after a blocked laboratory fit. The available local H2O POKAZATEL 500 K opacity
overlaps only 122 points; 85 shorter-wavelength points are outside coverage. CO2
and CH4 atmospheric opacity are absent from that runtime cache. The atmospheric
path can produce a partial H2O model, with explicit temperature and line-profile
limitations; no full-band molecular identification or calibrated sigma is claimed.

FITS import now seeks through containers up to 8 GiB instead of applying the
16 MiB text-table limit to the entire file. It loads one unambiguous scalar numeric
spectral BINTABLE, with limits of 100,000 rows, 128 columns and 1,000,000 decoded
cells; container scans allow 128 HDUs and 128 header blocks per HDU. Scaling
(`TSCALn`, `TZEROn`), integer nulls and slash-containing units are preserved.
Image extensions can precede the spectrum. Image-only, event-list, vector and
multiple-spectral-table products need explicit extraction/selection and are not
silently interpreted as spectra. Source hashing also streams bytes.

Two 84 MiB structural FITS containers carrying unchanged, real-derived NASA
measurements test import and hashing; these are format engineering checks, not
new observations. The reported `jupiter__9303301451N_evt.fits` was not available
in the inspected repository branches or local data and has not been validated.
Project raw-source attachments still have the separate 16 MiB limit; large FITS
can be opened directly and analysed when compatible, but cannot yet be embedded
as raw project attachments. Generic laboratory files still require explicit
quantity, coordinate units and IR/UV–Vis modality metadata for fitting.

## Recovered original method

Source inspected: local `ecas_v1.zip`, archive root `ecas-main/`, SHA-256
`cbbf5800d0b84cc9e444ae43ab8bae2cb39aae9808cde879782caf6ccfc47f19`.
Its Git revision was not established. Relevant original members:

- `app/core/identify.py:138–142`: bounded SciPy BVLS solver.
- `app/core/identify.py:211–292`: mixture, continuum and noise model.
- `app/core/identify.py:313–319`: same-weight, refitted drop-one statistic.
- `app/core/identify.py:340–343`: positive amplitude and threshold test.
- `app/ui/identify_panel.py:184–193`: default threshold 3, range 1–20.

For compatible absorption measurements the engine fits natural optical depth:

`tau = -ln(T) = sum(a_i * k_i) + constant + tilt`, with `a_i >= 0` and
unconstrained continuum coefficients. Declared decadic absorbance becomes
`tau = A * ln(10)`. Percent transmittance is explicitly divided by 100. Source
values are preserved, including T > 1; no upper clipping or percentile
normalization is applied. Molecular reference columns are scaled for numerical
conditioning, then amplitudes/uncertainties are converted back to native basis
units. This scaling preserves the fitted objective and bounds.

At least 20 points must remain in the common reference endpoint window.
Transmittance below 0.05 is excluded; with supplied errors the cutoff is
`max(0.05, 3 * median(sigma_T))`. The logarithm floor is 0.02. Original values and
the exclusion count are retained in the record.

With supplied independent errors, `sigma_tau = max(sigma_T / T, 1e-6)`.
Otherwise an initial unweighted optical-depth fit produces transmittance
residuals `r_T`; the estimated noise is
`s_T = max(1.4826 * median(abs(r_T - median(r_T))), 1e-6)` and weights use
`sigma_tau = s_T / T`.

For each positive fitted molecular amplitude, remove its column and **refit all
remaining molecular and continuum columns using the unchanged full-fit weights**:

`score_i = sqrt(max(chi2_without_i_refitted - chi2_full, 0))`.

The original positive-amplitude / score >= 3 default is retained as a conditional
fit threshold. Zero-amplitude evaluated components have score zero; unavailable
components have no score, never an invented zero. Amplitude uncertainties use the
active-set weighted normal-matrix pseudoinverse without reduced-chi-square
rescaling. Reduced chi-square uses the historical
`max(N - count_nonzero(fitted_coefficients), 1)` denominator. Weighted shape cosine
similarity > 0.8 generates a degeneracy warning. The old optional independent
candidate-screening function is not exposed in this implementation.

**Sigma is not a calibrated detection significance or a probability of molecular
presence.** Neither estimated noise nor supplied errors establish calibration
under correlated noise, reference uncertainty, nonnegative-boundary effects,
candidate selection or physical-model mismatch. No abundance claim is made.

## Separate UV–Vis measured-template mode

Signed cross-section observations can be fitted against signed cross-section
references with the same BVLS mixture / refitted drop-one objective. They are not
converted to transmittance or physical opacity. This exploratory adaptation
retains negative ordinates; amplitudes describe measured-template scaling.

Supplied uncertainties stay in cross-section units. Without supplied errors,
the residual MAD is computed directly in cross-section space with floor
`max(max(abs(observed_cross_section)) * 1e-6, smallest_positive_normal_float)`.
This replaces the transmittance-unit v1 floor and is recorded separately in
settings. It must not be described as the unchanged v1 noise model.

Cross-section/optical-depth mixing is blocked pending an explicit physical
adapter. Molar absorptivity and quantum yields are not accepted as cross-sections.

## Library, provenance and metadata

The real library was imported from ECAS_BETA revision
`a84c9d3ccf5e5dd230716feb9e972b60e0c454d9`; all 88 downloaded file contents were
verified against pinned Git blob IDs before writing. Raw and prepared numerical
files remain unchanged. Local corrections add `Uv-Vis/` to 22 manifest paths and
fix inventory links from `.csv` to the actual `.md` file.

Discovery reads `data/ECAS_Spectral_Library/Ready_For_ECAS/IR` and `Uv-Vis`:
18 IR datasets / 13 molecules and 22 UV–Vis datasets / 15 molecules. The IR
prepared files are raw copies, not separately normalized products. Six UV–Vis
CSV datasets contain signed negative measurements. PH3 has a repeated wavelength
and is discoverable but blocked from interpolation until an explicit reduction
policy is chosen. NO IR uses micrometres, unlike most IR files' wavenumbers.

Dataset IDs bind modality, molecule, filename and content hash, independently of
installation directory. Different phase/temperature/source variants remain
separate. JCAMP headers, curation records, source hashes, original units, phase,
conditions and available attribution are retained. Declared IR manifest hashes
and phase conflicts are checked. `SpectrumData.metadata` preserves source facts
through imports and project persistence; empty legacy metadata does not change
existing project integrity digests.

Known phase mismatches are blocked. Unknown conditions and differing reference
temperatures generate explicit warnings and permit only exploratory template fitting. Optional caller
metadata cannot override conflicting source-provided modality, phase or
temperature. Header values must establish units and quantity; no numerical-range
unit guessing is provided. Generic tabular observations can declare `modality`
and conditions in their supported header metadata.

## Multiple observations and reproducibility

Observations retain project/record ID, raw hash where known, source path, planet,
publication and instrument descriptions. Source-table and archive metadata are
separately attributed. Inputs are copied into independent session snapshots.
An unhashed input gets a content-derived **snapshot** identity, never a fabricated
raw-source hash. Identical raw products are reported as duplicates instead of
being counted as independent evidence. Results remain separate per observation;
there is no joint likelihood or combined sigma calculation.

Batch records (`ecas-identification-batch-v1`) contain input/reference snapshots,
metadata, dataset identities, exclusions/settings, solver results and checksums.
Individual results use `ecas-laboratory-identification-v1`. Checksums establish
internal consistency, not external source authenticity. Replay compares candidate
identity/status, scores, amplitudes, uncertainties and evaluated arrays. Software
versions are recorded; replay uses the installed implementation.

## Limits and verification scope

- Reference samples are linearly interpolated on the common endpoint interval.
  Continuous support is an explicit assumption; internal gaps, resolution and
  instrument-response equivalence are not independently certified. A warning is
  shown. Selecting disjoint windows can leave no evaluable joint fit.
- Unknown pressure/temperature/resolution and reference measurement uncertainty
  limit physical interpretation. No temperature extrapolation model is added.
- JCAMP support is limited to uncompressed AFFN XYDATA/XYPOINTS; unsupported
  compressed forms fail visibly.
- Fits run in a worker thread. Closing waits for a current solver call; there is
  no within-solver cancellation or combined atmospheric retrieval.
- The broader application redesign remains future work. This interface follows
  the existing Comparisons styling and uses collapsible entry and compact tables.
- Tests use actual project files and explicitly identified real-data-derived
  numerical/integrity fixtures. Reference self-fits are algebraic checks, not
  empirical validation, detection calibration, or proof of atmospheric presence.

Implementation: `ecas/identification/`, `ecas/observations.py`,
`ecas/ui/identification_panel.py`, `ecas/identification_records.py`.
Verification results are recorded in `docs/brains/PROJECT_STATE.md`.
