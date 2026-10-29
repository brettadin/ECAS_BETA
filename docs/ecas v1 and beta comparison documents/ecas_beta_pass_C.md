## 1. Input representations and comparison eligibility

The comparison system uses a structured `ComparisonInput` record. It carries the source identifier and SHA-256, role, observable, axis and signal units, coordinate frame, response identifier and evidence, measurements, and optional uncertainty information.

This is important because the comparison code does not treat every pair of arrays as scientifically comparable.

### Eligibility requirements

The current eligibility implementation checks:

- A supported role: observation, forward model, or reference measurement.
- The supported observable: transit depth.
- Explicit wavelength and signal units.
- Coordinate-frame and response metadata.
- A valid source SHA-256.
- At least three finite measurements with strictly increasing coordinates.
- Exact coordinate alignment for the residual diagnostics.
- Explicit uncertainty evidence and a declared cross-dataset independence assumption for weighted diagnostics.

A missing requirement is reported separately from an incompatibility. An input with unknown metadata is not automatically treated as compatible.

Finding C1 — Explicit eligibility checks are a strong design feature. The code makes assumptions visible instead of silently inferring measurement meaning. However, it explicitly documents that evidence strings are caller attestations; they do not independently verify a source, instrument response, or physical accuracy.

## 2. Unit conversion and spectral alignment

The alignment module implements explicit transformations rather than implicitly modifying data during eligibility assessment.

| Transformation                | Implemented behavior                                     | Important boundary                                                             |
| ----------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Signal units                  | Converts transit depth between fraction and percent.     | Does not establish that the original signal actually represents transit depth. |
| Wavelength units              | Converts supported wavelength units to microns.          | Requires positive, finite, strictly increasing coordinates.                    |
| Wavenumber                    | Converts cm⁻¹ to microns and reverses the sample order.  | Reorders values, uncertainties, and covariance consistently.                   |
| Shared-coordinate restriction | Restricts inputs to supported common coordinates.        | Does not invent measurements outside coverage.                                 |
| Model-to-bin alignment        | Integrates a forward model over observational passbands. | Requires usable model coverage; no extrapolation outside the supported domain. |

The wavenumber conversion is particularly careful: it reverses the coordinate ordering and applies the corresponding permutation to the covariance matrix. This is necessary to preserve the mathematical meaning of weighted residuals after the coordinate order changes.

### Important distinction

A correct unit conversion is not the same as a correct physical interpretation. For example, converting a column from percent to fraction cannot establish whether the column is transit depth, normalized flux, or some other quantity.

Finding C2 — The transformation layer is explicit and auditable. The principal scientific question is whether the metadata supplied to these routines are accurate. That requires examining the ingestion and provenance path in Pass D.

## 3. Transmission forward model

The core implementation is in `ecas/comparison/model_generator.py`. It generates a one-dimensional, isothermal hydrostatic transmission spectrum using spherical-shell chord integration.

### Model structure

The implementation:

1. Validates the planetary and stellar parameters, temperature, gravity, reference pressure, mean molecular weight, wavelength grid, and molecular mixing ratios.
2. Establishes the shared wavelength coverage of the selected molecular components.
3. Calculates a hydrostatic scale height.
4. Defines an opaque lower boundary, with an optional gray cloud deck.
5. Combines molecular absorption cross sections with an H₂/He Rayleigh-like continuum.
6. Calculates slant optical depths along spherical-shell chords.
7. Integrates annular contributions to derive the modeled transit depth.
8. Records model parameters, opacity sources, source hashes, warnings, and a content-derived SHA-256.

The model explicitly excludes target wavelengths outside the shared coverage of its active molecular components rather than extrapolating their cross sections.

### Assumptions and limitations

The model is not a general-purpose atmospheric retrieval. It assumes:

- A one-dimensional, isothermal hydrostatic atmosphere.
- Uniform volume mixing ratios for the modeled species.
- A specified mean molecular weight and gravity.
- A simplified continuum and gray cloud treatment.
- Molecular cross sections that are already available on compatible wavelength grids.

The source also emits warnings for synthetic illustrative bands, zero-pressure Doppler cross sections, and large differences between reference and model temperatures.

Finding C3 — A substantial forward-model implementation exists, but its physical scope is restricted. Its outputs are conditional on supplied planetary parameters, molecular abundances, opacity data, and model assumptions. A generated spectrum is not an independently inferred atmosphere.

## 4. Molecular attribution and leave-one-out analysis

The model generator includes `generate_leave_one_out_models()` and `summarize_leave_one_out_attribution()`.

The code can compare a full model with models generated after removing one molecular component at a time. It also reports wavelength-dependent shares of the modeled opacity contributions.

These results can help identify which components influence a model under its chosen assumptions.

They should not be interpreted as proof that a molecule is present in an observation. A component's influence on a synthetic spectrum depends on the supplied abundance, opacity source, continuum, cloud settings, and other fixed parameters.

Finding C4 — Attribution is conditional model sensitivity, not molecular identification. The source's own caveats appropriately distinguish these concepts. The UI and exported records should preserve that distinction wherever attribution results are shown.

## 5. Residual diagnostics and candidate ranking

The residual module calculates point-by-point differences and descriptive summaries, including mean residual, mean absolute residual, RMS residual, maximum absolute residual, demeaned RMS, and an offset-dominance flag.

Weighted diagnostics additionally calculate Cholesky-whitened residuals and the quadratic

\\[ Q = r^\mathsf{T}(C\_\mathrm{left}+C\_\mathrm{right})^{-1}r \\]

where \\(r\\) is the residual vector and the covariance matrices must be explicitly supplied or otherwise declared under the supported noise model.

The implementation does not estimate missing covariance, fit a baseline, or calculate detection significance. Its documentation explicitly warns that the quadratic omits Gaussian log-determinant normalization and is not a calibrated p-value or Bayesian evidence.

Candidate ranking applies further safeguards:

- Ineligible candidates remain visible with reasons for exclusion.
- Ranking is blocked if no candidate is eligible.
- Weighted ranking is blocked if eligible candidates have differing combined covariance matrices.
- Exact ties are retained within the configured numerical tolerance.
- The output includes limitations and does not claim molecular identification or abundance.

Finding C5 — The ranking design explicitly limits what its scores mean. It supports relative numerical comparison among eligible candidates under shared conditions, not a claim that the best-ranked candidate is the correct atmospheric composition.

## 6. External model adapters and provenance

The external-model adapter module defines a common input path for precomputed spectra from established atmospheric modeling software, including petitRADTRANS, POSEIDON, TauREx 3, PLATON, and Pyrat Bay.

The adapter code uses a versioned model-file schema and a structured `AtmosphericModelProvenance` contract. Its stated role is to accept externally generated model spectra without bundling the full modeling engines or their large opacity databases.

This is an architectural choice, not proof that all five external packages have been installed, executed, or independently validated in ECAS. A technical evaluation entry for a package should not be mistaken for a tested integration with that package.

Finding C6 — The external-model pathway is a defined integration boundary. Pass D should check whether source hashes, opacity metadata, temperature applicability, and imported model provenance are preserved accurately through that boundary.

## 7. Potential numerical validation gaps

The source inspection identified several input-validation areas worth recording. These are potential defects based on code inspection, not experimentally reproduced failures.

- C7 — Imported cross-section finiteness. `component_from_cross_section_spectrum()` checks the number of points, positivity of coordinates, non-negativity of cross sections, and coordinate ordering. Its visible checks do not explicitly reject all non-finite coordinate and cross-section values before constructing the component. A NaN can evade ordinary comparisons such as `value < 0`. The cached ExoMol conversion similarly does not visibly reject every non-finite cross-section value before model generation.
- C8 — Forward-model parameter validation. `generate_isothermal_transmission_model()` explicitly validates many physical parameters, but `haze_slope` and `n_altitude_layers` are not included in the same initial validation block. The consequences depend on the supplied values and downstream numerical operations; this should be checked with targeted tests before classifying it as a confirmed runtime defect.
- C9 — Cross-section temperature compatibility. The generator warns when the reference temperature differs substantially from the model temperature. A warning does not adjust the cross section to the requested temperature. Users must not interpret the output as temperature-consistent merely because the calculation completed.

These issues are narrower than a general claim that the model is unreliable. They identify specific boundaries where validation or interpretation deserves further attention.

## 8. Pass C findings summary

| ID | Finding                                                                                                   | Classification                                           |
| -- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| C1 | Eligibility checks require explicit metadata and distinguish missing requirements from incompatibilities. | Confirmed design feature                                 |
| C2 | Unit conversion and spectral alignment are explicit, with uncertainty and covariance transformations.     | Confirmed implementation                                 |
| C3 | A spherical-shell transmission model exists, with restricted physical assumptions.                        | Confirmed implementation and limitation                  |
| C4 | Leave-one-out attribution measures sensitivity within the chosen model, not molecular detection.          | Confirmed interpretation boundary                        |
| C5 | Residual diagnostics and ranking include safeguards against unsupported statistical claims.               | Confirmed design feature                                 |
| C6 | External model adapters define a provenance-aware integration path.                                       | Confirmed code structure; live integrations not verified |
| C7 | Imported cross-section paths may allow non-finite values through initial validation.                      | Potential defect; requires reproduction                  |
| C8 | Some forward-model parameters lack explicit validation in the initial checks.                             | Potential defect; requires targeted tests                |
| C9 | Temperature mismatch warnings do not correct cross sections for temperature.                              | Confirmed limitation                                     |

No numerical tests were run during this pass. I have not established whether C7 or C8 produces a downstream failure, incorrect finite output, or an error that is caught elsewhere.

## 9. Overall assessment of Pass C

Beta contains a meaningful numerical framework: explicit eligibility gates, auditable unit conversions, model-to-observation bin integration, a physically motivated transmission solver, residual diagnostics, conditional molecular attribution, and provenance-aware external-model adapters.

The principal boundary is that numerical rigor in individual operations does not, by itself, validate the complete scientific inference. Model assumptions, input metadata, observational response, uncertainty treatment, opacity validity, and interpretation must all be appropriate for the intended analysis.

The most actionable technical follow-up is to create targeted regression tests for the potential non-finite input and parameter-validation gaps before considering any code changes. No changes should be made during this review.

I will wait for your discussion or approval before proceeding to Pass D — Data ingestion, storage, caching, and provenance.