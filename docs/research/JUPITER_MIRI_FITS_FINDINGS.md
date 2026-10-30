# Jupiter MIRI FITS findings and ECAS handling proposal

Date: 2026-10-30. Status: inspected files; recommendations only, no application changes.

## Conclusion

Both supplied files can be read as JWST MIRI imaging products. ECAS should offer
an image inspection workflow for them. They cannot directly supply the
wavelength-dependent absorption or transit-depth measurements required by Identify.
The immediate importer failure is an unsupported continued header string; image
support remains a separate requirement after that parser issue is resolved.

## Exact inputs and verified metadata

Files are in `C:\Users\Blake\Downloads\`:

| Filename | Bytes | SCI dimensions (x × y) | SCI BUNIT |
|---|---:|---|---|
| jw01022017001_03101_00001_mirimage_rate.fits | 21,214,080 | 1032 × 1024 | DN/s |
| jw01022017001_03101_00001_mirimage_o017_crf.fits | 29,721,600 | 1032 × 1024 | MJy/sr |

SHA-256, respectively:

```text
1c66b5c4b1180b2db5dfeb621b49eef3bcdfc41828fed78895143a802b46dd09
f5a1af32177c7184229213a22c916b70abde4fb24fd12d36c9388f4ad2337bbc
```

Both primary headers declare TELESCOP=JWST, INSTRUME=MIRI, DETECTOR=MIRIMAGE,
EXP_TYPE=MIR_IMAGE, FILTER=F770W, DATAMODL=ImageModel, TARGNAME=JUPITER,
DATE-OBS=2022-07-03 and EFFEXPTM=30.525 seconds. They share the exposure identifier;
they are processing products of that exposure, not independent observations.

The rate file has a primary header followed by SCI, ERR, DQ, VAR_POISSON,
VAR_RNOISE and ASDF. The crf file adds AREA and VAR_FLAT. All image planes have
the same 1032 × 1024 dimensions. SCI and ERR are floating-point image arrays;
DQ is an integer bitmask. The ASDF BINTABLE contains serialized metadata and
does not provide wavelength/flux spectral rows.

The rate header records S_RAMP=COMPLETE. The crf header records
S_PHOTOM=COMPLETE and S_OUTLIR=SKIPPED. Therefore the crf suffix alone must not be
used to assert that outlier rejection actually ran on this particular product.
The calibrated image is the more appropriate starting point for surface-brightness
inspection, subject to its quality flags and calibration history.

## Reproduced ECAS failure

Both calls to `import_fits_bintable_spectrum` in
`ecas/ingestion/tabular_formats.py` fail with:

```text
FITS CONTINUE long strings are unsupported; explicit extraction required
```

The SCI header contains a continued S_REGION string. The current reader rejects
it before reaching a useful image-versus-spectrum diagnosis. A separate read-only
header scanner traversed all HDUs and established the inventories above, without
altering inputs or weakening the production parser. No numerical image statistics,
pixel-quality assessment, WCS validation or independent calibration validation
were performed. The files are about 20.2 and 28.3 MiB, distinct from the previously
reported approximately 84 MB `jupiter__9303301451N_evt.fits`, which remains a
different, unverified input.

## What these data support

Images permit inspecting Jupiter's spatial brightness distribution in the F770W
band, examining quality masks, and eventually measuring calibrated regional or
integrated band photometry. A single filter measures a response-weighted band;
it does not provide a resolved absorption spectrum. Averaging image columns or
labelling pixel position as wavelength would invent a spectral coordinate.

Several filters could support separately calibrated photometric measurements
and comparisons with physical models integrated through the actual filter
responses. They would still be broadband photometry rather than a reconstructed
high-resolution spectrum. Molecular inference would need an appropriate physical
model and uncertainty treatment, not the laboratory sigma calculation.

For wavelength-resolved analysis, seek actual spectroscopic products with
verified coordinates, observable and uncertainty metadata. JWST extracted
spectra and spectral cubes need their own mode-specific adapters; an x1d flux
spectrum is not automatically an exoplanet transit-depth spectrum.

## Recommended implementation sequence

1. Add an import inspection stage that classifies header/HDU content before
   selecting an adapter. Show instrument, target, filter, calibration state,
   units, image dimensions and available products. Explain which workflows apply.
2. Support standard FITS continued strings correctly, including escaped quotes
   and comment handling. Prefer a maintained FITS library such as Astropy for
   general image/header support, after dependency review; retain explicit limits
   and existing scientific checks. Do not ignore or truncate S_REGION silently.
3. Introduce an image data representation separate from SpectrumData: SCI, ERR,
   DQ, optional variance/area planes, WCS metadata, units and provenance. Keep
   metadata serialization/ASDF handling separate from tabular scientific values.
4. Add an image viewer with percentile/asinh display options, colour bar with
   units, pixel values, quality overlays and region selection. Display stretches
   must leave scientific arrays unchanged. Select extensions by identity rather
   than assuming all secondary HDU indices are fixed.
5. Implement photometry only after validating calibration and pixel-area semantics.
   For surface brightness I_i in MJy/sr and solid angle Omega_i in sr, an
   appropriately background-subtracted aperture flux is
   `F_nu[Jy] = 1e6 * sum(I_i * Omega_i)` over included pixels. Check whether AREA
   is a relative correction or absolute area and use the relevant reference area;
   do not treat raw AREA values as steradians without verification. Propagate ERR
   in matching units and include background, calibration and covariance terms
   where applicable. Record the mask and excluded fraction; do not silently
   replace bad pixels with zero. Jupiter is extended, so point-source aperture
   corrections must not be applied indiscriminately.
6. Preserve pipeline versions, calibration reference context, exposure identity,
   original hashes, WCS and extraction settings. Keep rate and crf related in the
   project model to prevent duplicate-evidence claims. Design large-source storage
   separately from the current 16 MiB raw project attachment envelope.

Initial acceptance should cover opening both exact inputs, correct dimensions
and units, long-string preservation, distinct imaging eligibility, bounded-memory
loading, quality-mask preservation, and an honest route back to spectral workflows.
Later photometry needs independent unit/area/error checks and real-data comparisons.
No molecular score should appear merely because an image opened successfully.

## Practical handling before ECAS image support exists

Use a FITS image viewer or an Astropy-based inspection session to open SCI and
review ERR/DQ together. Start with the calibrated crf product for brightness
inspection; retain rate for calibration comparison. If scientific reprocessing
is needed, use the official JWST pipeline with its appropriate calibration
references and provenance. Do not apply another photometric conversion to an
already calibrated MJy/sr SCI array. These are recommendations; no viewer,
dependency installation or pipeline processing was executed in this investigation.

## Authoritative references consulted

- [JWST science product layouts](https://jwst-pipeline.readthedocs.io/en/stable/jwst/data_products/science_products.html):
  rate, calibrated image planes and metadata structure.
- [JWST processing stages and crf products](https://jwst.readthedocs.io/en/latest/jwst/data_products/stages.html):
  interpretation of intermediate products; actual step status must be read from each file.
- [STScI stages of JWST processing](https://jwst-docs.stsci.edu/jwst-science-calibration-pipeline/stages-of-jwst-data-processing):
  detector count rates and calibrated imaging versus spectroscopy.
- [STScI MIRI photometric calibration and corrections](https://jwst-docs.stsci.edu/jwst-mid-infrared-instrument/miri-performance/miri-zero-magnitude-flux-densities-aperture-corrections-and-color-corrections):
  surface-brightness units, pixel area and source-dependent corrections.

Local measurements above come from the supplied file headers and streamed SHA-256
hashes. Architectural steps are proposed work, not implemented capabilities.
