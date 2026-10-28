# Response and uncertainty investigation — 2026-10-28

Second offline experiment, not production comparison or method acceptance. All
response parameters, bin edges and errors are invented, not inferred from NASA.
Original v1 evidence remains under verification_20261028; new v2 evidence is under
verification_response_20261028. Application behavior and recovery archive unchanged.

## Results

| Controlled example | Result and implication |
| --- | --- |
| Irregular top-hat bins versus center samples | Residual sum 663.22 despite correlation 0.99868; matching bin averages give zero |
| Known Gaussian LSF omitted from model | Residual sum 43111.17; response matching matters, but this is not a real instrument calibration |
| Partial/no coverage | Only fully covered declared bins accepted; exclusions reported; no extrapolation or silent clipping |
| Two narrow features versus one broad feature | Dense-grid maximum difference 0.0482 becomes 1.36e-14 in a single coarse bin; shapes can lose distinguishability |
| Lower/upper errors 0.1/0.2 | Equal-distance models give penalties 1/0.25 on opposite sides; averaging errors would erase this distinction |
| Fixed correlation rho=0.8 | Ten common unit residuals change quadratic penalty 10 to 1.22; alternating residuals change 10 to 50; independence assumptions can bias either way |

Scores are not detection probabilities or reduced chi-square. Side-dependent
quadratics are illustrative penalties, not established asymmetric likelihoods.
Covariance examples are deterministic residual patterns, not random noise calibration.
No species labels, actual detector response, interpolation or molecular inference.

## Independent checks and primary sources

Simpson integration verifies analytical top-hat averaging and Gaussian convolution
at relative tolerance 1e-10. NumPy linear solves independently verify the covariance
expression on three residual patterns. NumPy was already installed; no dependency
was added. Tests reject invalid bins and unsupported/singular covariance parameters.

[SciPy's multivariate-normal documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.multivariate_normal.html)
includes a determinant normalization as well as the covariance quadratic. Our
fixed-covariance quadratic omits that normalization and cannot fit covariance or
rank full likelihoods across different covariance choices. SciPy was not invoked.

[petitRADTRANS's Data API](https://petitradtrans.readthedocs.io/en/latest/autoapi/petitRADTRANS/retrieval/data/index.html)
separately represents resolution, bin widths, model functions, uncertainty and
covariance. That informs investigation of an explicit response contract; it does
not select that library or establish valid defaults. Sources read 2026-10-28.

## Next

Investigate actual forward-model inputs and product provenance, characterize noise
and false matches, and verify product-specific response/error conventions. Overlay
plus residual inspection is a candidate; correlation alone cannot establish
agreement. No production method selected. Real wavelength-dependent LSFs, covariance
estimation, atmospheric modelling and retrieval remain unimplemented. Independent
review of this research and human desktop acceptance of Chunk 4 remain pending.
