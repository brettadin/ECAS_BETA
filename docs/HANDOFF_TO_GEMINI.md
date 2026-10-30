# ECAS handoff to Gemini — 2026-10-29

## Start here and preserve working state

Repository: https://github.com/brettadin/ECAS_BETA
Workspace: `C:\AI-Projects\Bwett AI Project UwU\ECAS_BETA`.
Branch: `codex/laboratory-identification-checkpoint-20261029`.
Latest published commit: `31325c2` — Fix identification previews and stream large FITS spectra.
The push was verified against the remote branch. Remote commit `8b7b950` had
integrated master; our fixes were rebased onto it and pushed normally, without force.
Master itself was not changed by that push.

Read `AGENTS.md`, `clinerules.md`, `README.md`, `docs/brains/PROJECT_STATE.md`,
`docs/brains/DECISIONS.md`, and `docs/architecture/LABORATORY_IDENTIFICATION.md`.
Also inspect the recently integrated inventory/resource and FITS/HDF5 research
documents before planning further ingestion work. Treat research as context,
not proof of implemented functionality.

An existing user edit to `docs/HANDOFF_TO_OPENAI.md` remains uncommitted (a blank
line at EOF). Preserve it. This Gemini note is newly created after the push and
is not part of commit `31325c2`. Some historical headings in PROJECT_STATE still
say “uncommitted”; the implementation they describe is now published.
Do not commit or push additional work without user authorization.

## Scientific requirements

- Actual measured library data only. No fabricated spectra or silent synthetic fallback.
- Preserve ExoMol catalogue case: H2O, CO2, CH4, SO2.
- Cross sections in cm²/molecule cannot be subtracted from transit depth in percent.
  Atmospheric observations need an explicit radiative-transfer model.
- Fit agreement, rankings and conditional sigma scores do not prove molecular
  presence, abundance or calibrated detection significance.
- Preserve signed measurements, source identities, conditions and provenance.
- Run headless tests with warning escalation.

## Completed architecture and identification work

Earlier baseline `e0ea472` consolidated comparison eligibility, passband versus
FWHM handling, analytic forward-model checks, strict cached real-data mode,
covariance conditioning, provenance conflict guards, saved-result reproduction,
and the transit/orbit visualizer. Those features remain intact.

The new laboratory workflow is in:

- `ecas/identification/library.py`: real library discovery, uncompressed AFFN
  JCAMP-DX XYDATA/XYPOINTS and explicit UV CSV adapters, stable dataset IDs,
  hashes, source headers and curation metadata.
- `ecas/identification/engine.py`: recovered v1 absorption fit, separate signed
  UV cross-section adaptation, explicit blocked results and numerical records.
- `ecas/ui/identification_panel.py`: grouped molecule selection, explicit source
  variants, stable colours, independent observation batches, plots and table.
- `ecas/observations.py`: immutable input snapshots, project/record identities,
  duplicate-source handling and streaming source hashes.
- `ecas/identification_records.py`: checksum-bound batch export and reproduction.
- `ecas/ui/comparison_browser.py`: panel entry and atmospheric handoff.
- `ecas/ingestion/import_manager.py`, `tabular_formats.py`, `main_window.py`,
  `projects.py`, `persistence.py`, and `models/spectrum.py`: format dispatch,
  metadata retention, project identity and persistence integration.

SciPy 1.18.1 is pinned in requirements. Solver absence blocks explicitly.
Optional spectrum metadata is omitted when empty from legacy integrity payloads
so older project digests remain valid.

## Original v1 methodology: exact meaning

Inspected archive: `C:\Users\Blake\Downloads\ecas_v1.zip`, root `ecas-main/`.
SHA-256: `cbbf5800d0b84cc9e444ae43ab8bae2cb39aae9808cde879782caf6ccfc47f19`.
Its Git revision was not established.
Original `app/core/identify.py`: solver lines 138–142; decomposition 211–292;
drop-one refits 313–319; positive-amplitude/threshold interpretation 340–343.
Original UI default threshold is 3, adjustable 1–20.

Compatible absorption is fitted as natural optical depth:
`tau = -ln(T) = sum(a_i*k_i) + constant + tilt`, with nonnegative molecular
coefficients and unbounded continuum, using SciPy BVLS. Decadic absorbance is
converted with ln(10); percent transmittance is divided by 100.
At least 20 points must remain in the common reference coverage. Opaque points
are filtered with T cutoff 0.05, or max(0.05, 3*median(sigma_T)); log floor 0.02.
Supplied errors propagate as max(sigma_T/T, 1e-6). Otherwise an initial fit
estimates transmittance noise using max(1.4826*MAD(residual_T), 1e-6), then uses
that noise divided by T.

For each positive component, remove it and refit all remaining molecules and
continuum with the unchanged full-fit weights. The score is
`sqrt(max(chi2_without_refitted - chi2_full, 0))`. This is conditional fit
improvement, not a calibrated detection probability. The historical reduced
chi-square denominator is max(N-count_nonzero(coefficients), 1).

UV cross-section-to-cross-section fitting is a separate exploratory signed
measured-template fit. It preserves negative values and uses a unit-scaled MAD
floor, recorded as an adaptation. Cross-section/optical-depth mixing is blocked.
We did not port v1 pseudo-transmittance conversion of transit depth, reference
negative clipping, unsupported-region zero fill, or mock reference merging.
See the methodology document for full equations, assumptions and limitations.

## Actual local library

`data/ECAS_Spectral_Library/` contains Raw_Sources, Ready_For_ECAS and Documentation.
Imported from pinned upstream revision `a84c9d3ccf5e5dd230716feb9e972b60e0c454d9`;
88 files were checked against Git blob IDs. Numerical source files are unchanged.
Discovery yields 40 reference datasets with zero discovery issues:

- 18 IR datasets / 13 molecules: 5 absorbance, 13 transmittance; gas/liquid
  conditions vary. NO uses micrometers; other IR sources use inverse centimeters.
- 22 UV CSVs / 15 molecules, wavelength_nm and
  absorption_cross_section_cm2_per_molecule. Six datasets contain negative values,
  retained unchanged. PH3 has a duplicate coordinate and blocks pending an
  explicit reduction policy.

Corrected 22 UV manifest paths and IR documentation inventory links.
`.gitattributes` preserves raw/prepared scientific source bytes across checkout
alongside pre-existing source-preservation rules.
Known phase conflicts block; missing conditions and temperature differences warn.
Interpolation assumes continuous support inside common endpoints. Internal gaps,
instrument resolution and reference uncertainties are not yet modelled.
Some IR references contain nonpositive T and are explicitly rejected.
Selecting many UV references can leave fewer than 20 common points and block
the joint fit; do not silently fabricate or zero-fill missing coverage.

## Brett feedback and fixes in latest checkpoint

Brett selected WASP-39 b, Rustamkulov et al., NIRSpec PRISM transmission data;
Identify remained blank. The engine correctly rejected planetary transit depth
for laboratory fitting, but the UI only plotted successful fit arrays.

The panel now retains a measured-input preview before fitting and after blocked
results, with original units and visible reasons. Selected references can be
previewed separately by modality, quantity and coordinate units. Previewing never
creates a fit or sigma. Multiple files can be added directly; checked counts,
per-input worker progress and independent result selection make batching clear.
Opening Identify initially snapshots the currently loaded spectrum.

An atmospheric action transfers checked transit snapshots with their identities
and metadata to the existing physical-model workspace, sets strict cached ExoMol
mode, and requires explicit generation. Laboratory reference curves are not
transferred as opacities. Laboratory batches process all checked observations;
atmospheric generation still processes one selected observation at a time.
Repeated handoff does not duplicate already transferred identities.

The exact cached Rustamkulov product has 207 points from 0.53146–5.34413 microns.
Two local cache entries are the same raw product and must not count as independent
evidence. SHA-256: `135d6f22f6cf04f6d5a757d8570fbb50a0b2a0ef9f1f347dbaabef6a18e863e7`.
Its measured preview now retains all 207 points. Runtime opacity cache contains
only H2O POKAZATEL at 500 K; the broader 400–4010 cm^-1 product covers 122 points.
85 shorter-wavelength observations lack opacity coverage. Actual handoff/model
generation yielded full-H2O and without-H2O candidates on that shared subset.
The 1166 K atmosphere versus 500 K opacity mismatch and line-profile limitations
remain explicit. CO2/CH4 opacity are not available locally. Full PRISM center
coverage would require roughly 1871–18816 cm^-1; channel bandwidths are missing.

## Large FITS changes and unresolved Jupiter file

Brett reported an approximately 84 MB FITS file blocked by the old 16 MiB reader
limit: `jupiter__9303301451N_evt.fits`. He said it was uploaded under data on GitHub.
Repeated checks of all four available ECAS_BETA branches, original ECAS main,
release attachments and local workspace/Downloads did not locate it at the time.
Do not claim that this exact file has been inspected or is compatible. Recheck
the current remote state and obtain a resolvable path/link if still absent.
Its filename alone does not establish instrument or scientific content.

`tabular_formats.py` now scans FITS using bounded header/row reads and seeks:

- Containers up to 8 GiB; 128 HDUs; 128 header blocks per HDU.
- One unambiguous scalar spectral BINTABLE; 100,000 rows, 128 columns,
  1,000,000 decoded cells; numeric D/E/J/K/I/B formats.
- Seeks past primary/images and unrelated extensions. Applies TSCAL/TZERO,
  integer TNULL, and preserves quoted units containing slashes.
- Rejects unsupported vector/variable-length tables, ambiguous spectral tables,
  image-only files and event lists with explicit extraction guidance.
- Streaming hashes avoid whole-file buffering and the previous >16 MiB missing hash.

Two 84 MiB structural image containers containing unchanged real-derived NASA
spectral rows imported with under 8 MiB traced memory. These are engineering
fixtures, not fabricated observational evidence. Raw project attachments still
have a separate 16 MiB limit; opening a large FITS does not yet allow embedding
its raw bytes into a project. Text-table limits also remain separate.

## Verification and practical limits

Full offscreen suite: **706 passed, 22 skipped, zero failures/warnings** in 41.56 s.
Skips: 21 opt-in network checks and one unavailable directory-symlink check.
Final identification/FITS focused suite after the input-label refinement:
**24 passed** in 4.86 s. Earlier focused UI/comparison suite: 23 passed.
Full suite preceded the final input-label-only refinement and subsequent clean
rebase onto remote documentation/inventory work; it was not rerun after rebase.

PowerShell verification command:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
.venv/Scripts/python.exe -I -B -m pytest -W error -p no:cacheprovider -o pythonpath=. -q -rs --tb=short --basetemp=.venv/checks/gemini-verification
```

Relevant tests: `test_identification_engine.py`, `test_identification_ui.py`,
`test_spectral_library.py`, `test_fits_streaming.py`, `test_real_data_workflow.py`,
and existing comparison/import/persistence tests. Real-library self-fits test
numerical consistency only. A mixed IR/UV two-input worker test verifies separate
results and plots. Offscreen rendering visually confirmed the Rustamkulov preview;
this is not full interactive desktop acceptance or independent scientific validation.

## Recommended next steps, in order

1. Locate and inspect the actual Jupiter FITS headers/HDU inventory. If it is an
   event list, identify instrument calibration, extraction and response requirements
   before proposing an adapter. Do not force events into wavelength/flux rows.
2. Have Brett exercise the published branch: Rustamkulov preview, visible blocked
   reason, atmospheric handoff, real IR and UV observations, and multiple checked
   inputs. Capture actual usability problems and distinguish expected eligibility
   blocks from defects. Verify on the final integrated checkout as appropriate.
3. Design large-source project persistence deliberately: external immutable source
   files/streamed copying plus hashes and portable provenance, rather than simply
   inflating the current base64-in-JSON envelope. Preserve legacy integrity checks.
4. Add a controlled, explicit attestation UI for generic lab spectra missing IR/UV
   modality or other required facts. Source facts must take precedence; wavelength
   shape or the selected molecule tab must not silently establish semantics.
5. Improve common-coverage diagnostics before fitting. Show overlap/usable-point
   counts and help users narrow incompatible candidates without changing the
   joint-fit methodology or presenting incomparable scores as equivalent.
6. Obtain appropriate real atmospheric opacities and coverage for the actual JWST
   target, including temperature and line-profile suitability; then pursue published
   WASP-39 benchmark replication. The local laboratory library alone is insufficient.
7. Extend atmospheric multi-observation execution with independent models/results,
   instrument/passband provenance and duplicate handling. Do not combine sigma
   automatically. Existing laboratory batching is not atmospheric batch retrieval.
8. Consider per-input unexpected-exception isolation in the worker: its current
   outer exception handler can discard a whole batch on an unexpected exception.
   Normal scientific incompatibilities already return blocked results. Any change
   must preserve honest failure records and successful observation identities.

Continue focused implementation and verification within authorized scope. Keep
the README, methodology, state and decisions accurate, and distinguish planned
features from implemented behavior and software tests from scientific evidence.
