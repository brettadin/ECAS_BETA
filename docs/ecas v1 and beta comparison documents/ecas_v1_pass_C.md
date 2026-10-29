## 1. Molecular line physics and forward modeling

The core implementation is in `app/core/physics.py` and `app/core/engine.py`.

### Implemented calculations

- Pressure broadening: Lorentzian half-width varies with pressure and temperature using a reference-width power law.
- Thermal Doppler broadening: Gaussian width depends on line center, temperature, and molecular mass.
- Line shapes: Unit-area Lorentzian, Gaussian, and Voigt profiles are implemented. The Voigt profile uses SciPy's Faddeeva function.
- Mixture spectra: `SpectrumEngine` combines line profiles into per-gas optical-depth arrays and applies gas multipliers.
- Transmission: The engine calculates transmittance using Beer–Lambert attenuation, \\(T=e^{-\tau}\\).
- Performance: Line data are flattened into shared arrays; the engine builds a profile matrix and caches optical depth by spectral unit and atmospheric conditions.

### Scientific interpretation

These are recognizable spectroscopic modeling components, but the presence of physically motivated equations does not establish that the model reproduces laboratory or atmospheric spectra accurately.

The engine's molecular input files, line intensities, broadening parameters, scaling conventions, and temperature/pressure applicability determine its scientific validity. The built-in model should be understood as a configurable forward-modeling tool whose assumptions and input-data quality need to be considered when interpreting results.

One specific design choice deserves attention: the Gaussian option uses a quadrature combination of Doppler width and Lorentzian/envelope width. The code comments explain that this is intended to preserve visible broadening on the display grid. It is therefore a practical approximation, not a pure thermal Doppler profile.

## 2. Spectral fitting and molecular identification

### Fitting method

`app/core/fitting.py` uses bounded nonlinear least squares (`scipy.optimize.least_squares`, trust-region reflective method) to fit gas multipliers. The fit can include a continuum level or a linear continuum tilt and can restrict fitting to a specified wavenumber window.

The model is effectively:

\\[ T(\tilde{\nu}) = B(\tilde{\nu})\exp\left[-\sum_g m_g\tau_g(\tilde{\nu})\right] \\]

where \\(m_g\\) is the fitted multiplier for gas \\(g\\), \\(\tau_g\\) is that gas's modeled optical depth, and \\(B\\) is the fitted continuum term.

The fitting implementation also estimates residual noise when the observation has no supplied uncertainties. It returns fitted multipliers, residuals, reduced chi-squared, and estimated uncertainties.

### Finding C1 — Estimated fit uncertainties require correction or verification

Source-level numerical concern

In `app/core/fitting.py`, around lines 327–347, the optimizer initially runs with unit uncertainties when no observation uncertainties are supplied. The code subsequently estimates the residual noise scale, but calculates the covariance using:

```
cov = np.linalg.pinv(    sol.jac.T @ sol.jac    * (1.0 / np.square(sigma).mean() if est else 1.0))
```

Because the Jacobian in this case was calculated using unit weights, the usual local least-squares covariance approximation scales the inverse information matrix by the estimated residual variance, rather than dividing by that variance. The current expression appears to apply the inverse scaling.

Implication: when noise is estimated rather than supplied, the returned multiplier uncertainties may be mis-scaled. This is a source-inspection finding; I have not run a numerical reproduction or examined the relevant tests. It does not, by itself, establish that the fitted multiplier values are wrong.

Recommendation: verify the intended covariance formula against a controlled synthetic spectrum with known noise, then add a regression test before changing the implementation.

### Identification is not the same as confirmation

`app/core/identify.py` implements reference ranking, constrained component fitting, and feature attribution. `app/core/fitting.py` also provides anomaly detection and candidate matching.

These tools can help identify plausible explanations for observed features. Their outputs depend on the reference library, spectral coverage, preprocessing, and overlap between molecular bands. A highly ranked candidate is not, by ranking alone, a confirmed chemical detection.

The distinction is particularly important for the built-in molecular model, whose limited spectral coverage and fundamental-band emphasis mean that unmodeled features can remain in the residuals.

## 3. Transit modeling and parameter inference

`app/core/transit.py` implements a transit geometry model, period search, parameter refinement, and physical-quantity calculations.

### Implemented methods

- A box least-squares (BLS) search supplies an initial period and transit estimate when the period is unknown.
- Bounded least squares refines transit parameters, including epoch, period, planet-to-star radius ratio, scaled orbital distance, and impact parameter.
- Single-transit analysis can hold the supplied period effectively fixed and use a stellar-parameter-based prior for the scaled orbital distance.
- The transit model calculates geometric overlap between the planetary and stellar discs and applies a quadratic limb-darkening prescription.
- A fitted linear baseline can be used for single-transit analysis.

### Finding C2 — Transit uncertainty estimates have explicit limits

The code estimates parameter covariance from the local least-squares Jacobian and scales it using the reduced chi-squared, with a lower scaling floor of one. This is a local approximation, not a complete posterior or a guarantee that parameter uncertainties account for all sources of error.

The code also documents a specific constraint: single-transit estimates of orbital geometry and radius ratio can be strongly correlated. When a stellar prior is used, those parameters are partly constrained by the stellar inputs rather than by transit shape alone.

Implication: reported parameter errors should be interpreted in the context of model assumptions, sampling, baseline treatment, and the available stellar information. The source alone does not establish statistical calibration across different data regimes.

## 4. Transmission-spectrum extraction

The function `extract_transmission_spectrum` holds the white-light transit geometry fixed and fits each wavelength channel to the corresponding transit-shape template. It normalizes each channel by an out-of-transit median and estimates wavelength-dependent transit depths.

If flux uncertainties are available, it uses inverse-variance weights and rescales the formal errors when the residual scatter is larger. Otherwise, it estimates uncertainty from residual scatter.

### Finding C3 — Some uncertainty sources are intentionally omitted

The function's docstring explicitly states that uncertainty in the estimated out-of-transit baseline and time-correlated noise are not modeled.

The subsequent `bin_depth_spectrum` function combines adjacent channels using inverse-variance weighting. That is appropriate under its weighting assumptions, but does not automatically account for correlations between channels or time-correlated systematics inherited from the original observations.

Implication: the extracted spectrum and its error bars are useful analysis products, but the uncertainties are not a comprehensive treatment of instrument systematics or correlated noise.

### Finding C4 — The molecular-identification bridge is deliberately heuristic

`depth_spectrum_to_observation` converts transit depths into a relative pseudo-transmittance by subtracting a low-percentile depth floor and scaling the excess absorption. Its docstring explicitly says the resulting gas multipliers represent relative abundances.

This conversion is not a physical inversion of transit depth into atmospheric composition. It is a bridge into the existing molecular comparison fitter.

Recommendation: keep this workflow clearly distinguished from the physical atmospheric forward-model comparison and from any future abundance-retrieval workflow.

## 5. Physical atmospheric modeling and abundance scans

`app/core/atmosphere.py` integrates the optional `petitRADTRANS` backend.

The source implements a forward model with the following assumptions:

- Isothermal temperature profile.
- Constant volume mixing ratios with altitude.
- Clear atmosphere with an H₂/He background.
- Hydrostatic transmission geometry.
- Correlated-k radiative transfer using the backend's default configuration.
- No instrumental line-spread convolution in the forward model.

It calculates wavelength-dependent transit depths from the modeled planetary radius and stellar radius. When comparing against measurements, `compare_model_to_depth_spectrum` integrates the model over inferred wavelength-channel edges rather than simply comparing the nearest model-grid point.

### Finding C5 — Channel integration is implemented, but channel boundaries are inferred

The comparison routine infers channel edges from adjacent wavelength centers using midpoints and extrapolated outer edges. This is a reasonable approximation for suitable channel grids, but it does not use instrument-supplied channel boundaries.

Implication: the comparison may not represent the actual instrumental response or throughput-weighted channel averages, especially for irregular channels or instruments with nontrivial spectral response.

The code correctly checks model wavelength coverage against the inferred channel edges and rejects measurements without usable uncertainties.

### Finding C6 — The abundance scan is conditional, not a complete retrieval

`scan_single_gas_abundance` evaluates a grid of volume mixing ratios for one selected gas while keeping the other atmospheric inputs fixed. It fits a constant transit-depth offset and reports the best grid value and any established \\(\Delta\chi^2=1\\) bounds.

The implementation explicitly warns about scan-boundary solutions and missing bounds. It also documents that the interval does not account for correlated noise, instrumental response, model inadequacy, or uncertainty in other inputs.

These are appropriate limitations to disclose. The resulting interval should not be presented as a general-purpose confidence interval for the true atmospheric abundance.

## 6. Synthetic validation infrastructure

`app/core/retrieval_validation.py` provides functions to generate synthetic transmission-depth observations and summarize profile-scan recovery across injected abundances and random seeds.

The synthetic generator supports optional instrument-response weighting, line-spread smoothing, and correlated Gaussian noise. The validation summary tracks absolute log-abundance bias, interval coverage, bounded intervals, and boundary-limited fits.

This is a useful foundation for quantitative validation.

However, the existence of validation infrastructure is not evidence that the method has passed validation. The implementation's docstrings specifically describe simplifying assumptions, including independent Gaussian noise as the default and no automatic emulation of instrument throughput, line-spread functions, or correlated systematics.

The next evidence needed is executed validation output, including recovery bias and interval coverage across representative signal-to-noise ratios and parameter regimes. The actual `petitRADTRANS` backend should be used for any claim about the performance of that backend.

## 7. Consolidated Pass C findings

| ID | Finding                                                                                                | Priority for follow-up                            |
| -- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------- |
| C1 | Possible incorrect covariance scaling when spectral-fit noise is estimated                             | High — verify numerically                         |
| C2 | Transit parameter errors rely on local covariance approximations and assumed model structure           | Medium — validate against synthetic cases         |
| C3 | Transmission-spectrum errors omit baseline uncertainty and time-correlated noise                       | Medium — document and validate limits             |
| C4 | Transit-depth-to-pseudo-transmittance conversion is heuristic                                          | High for interpretation; preserve the distinction |
| C5 | Atmospheric model comparison infers channel boundaries instead of using instrument-supplied boundaries | Medium — assess against intended datasets         |
| C6 | Single-gas abundance scans are conditional and can be boundary-limited                                 | High for interpretation; validation required      |
| C7 | Synthetic validation tools exist, but their presence does not establish successful validation          | High before making retrieval-performance claims   |

These priorities reflect scientific reliability and interpretation, not necessarily implementation order.

## Pass C conclusion

ECAS v1 contains substantive numerical and scientific functionality: molecular line-profile calculations, nonlinear spectral fitting, reference-spectrum decomposition, transit fitting, transmission-spectrum extraction, and an optional physical atmospheric model.

The main distinction is between implementing a scientific calculation and demonstrating that its outputs are accurate and its uncertainties calibrated. The code already acknowledges several limitations, especially for abundance scans and transmission-spectrum uncertainty. Those limitations should remain explicit in future development.

The most actionable source-level concern is C1, the possible covariance scaling error in spectral fitting when uncertainties are estimated from residuals. It warrants a focused numerical check before any correction is made.

Pass C is complete at the source-inspection level. No files have been modified, no tests have been run, and none of these findings has been experimentally reproduced in this review.

The next pass is Pass D — Data ingestion, storage, and provenance: supported file formats, unit and column interpretation, data validation, project round-tripping, external-data caching, and whether scientific results retain sufficient source and processing metadata.