# Comparison readiness investigation — 2026-10-28

Status: initial investigation, not method selection or Chunk 5 acceptance.
This independent documentation work can proceed while Chunk 4 desktop acceptance
is pending. It does not change the reviewed application. Historical part_1 plans
are context; the reconciled development plan governs this increment.

## Actual inputs and gaps

Code inspected: ecas/models/spectrum.py, ingestion/csv_importer.py,
ingestion/nasa_table.py, projects.py and visualization/spectra_plot.py.
Real source inspected: data/NASA/2026-10-27/feinstein-2023.tbl and its headers.
The 331-row product has retained raw bytes and provenance; it is not interchangeable
with an arbitrary bundled CSV merely because both mention WASP-39 b.

| Requirement | Current evidence | Comparison implication |
| --- | --- | --- |
| Axis identity/units | NASA centralwavelng alias wavelength, explicit microns; CSV units may be absent | Missing units must block quantitative alignment; numeric similarity is insufficient |
| Signal identity/units | NASA pl_trandep alias signal, Transmission, explicit percent | Preserve observable type; a molecular cross section is not the same observable |
| Uncertainty | NASA signed pl_trandeperr1/2 retained as raw columns; generic CSV uncertainty may be missing or zero | No established unified uncertainty mapping or covariance contract; never replace missing errors with zero |
| Sampling | NASA bandwidth retained with micron units | Do not equate bandwidth with instrumental resolution or assume its edge convention without source verification |
| Instrument | NASA metadata identifies JWST/NIRISS | Instrument label alone does not establish line-spread function or resolving power |
| Provenance | Source hashes, metadata, project source snapshots | Reproducible input storage exists; preprocessing/model provenance is not implemented |
| Physical conditions | Generic SpectrumData has no temperature/pressure/abundance or geometry contract | Do not invent atmospheric conditions from the planet name |
| Covariance | No typed representation in SpectrumData | Independent-error scoring would require an explicit documented assumption and appropriate data |

SpectrumData preserves columns, rows, optional axis/signal units/type and warnings.
It has no formal dataset-role, resolution, bin-edge, uncertainty-convention or
covariance fields. NASA attachment metadata can preserve facts outside that model;
generic CSV and legacy database records must not silently acquire those facts.

## Primary-source evidence

The [petitRADTRANS retrieval tutorial](https://petitradtrans.readthedocs.io/en/latest/content/notebooks/retrieval_basic.html)
describes fitting generated spectra to observations using error bars or covariance
and a model function; its example includes physical parameters and priors. It also
documents instrument convolution via data_resolution. This supports investigating
forward-model comparison rather than treating a reference line list as a measured
transit-depth curve. It does not establish a library choice for ECAS.

[ExoMol's official data-type catalogue](https://www.exomol.com/data/data-types/)
distinguishes transition lists, absorption cross sections, pressure broadening and
temperature/pressure-dependent opacities. A provider and product type therefore
need separate decisions. Access/licensing, required species/conditions, product
availability and actual retrieval interfaces have not been evaluated here.

Sources accessed 2026-10-28 through read-only web tools. No reference datasets,
packages or dependencies were downloaded or installed.

## Candidate approaches to evaluate, not select yet

| Candidate | Bounded use worth testing | Unresolved issue before quantitative use |
| --- | --- | --- |
| Compatible-observable overlay | Inspect aligned curves and missing coverage | Units, common coverage, binning/resolution and explicit transformations |
| Residual/uncertainty-weighted comparison | Compare a specified model against data | Error conventions, covariance, nuisance parameters and model adequacy |
| Correlation | Investigate shape/shift sensitivity on controlled cases | Continuum treatment, sampling, resolution, noise and significance calibration |
| Peak/line proximity | Exploratory feature annotations | Blends and broadening; coincidence cannot establish molecular presence |
| Physical forward model plus retrieval | Long-term atmosphere characterization | Physical inputs, opacity data, priors, likelihood, validation and runtime |

This table is an ECAS investigation agenda, not evidence that the methods perform
well on the current spectrum. No benchmark or scientific result was produced.

## Proposed compatibility outcomes and validation cases

Distinguish inspection-only, eligible-for-a-specified-method, missing-metadata and
incompatible. Eligibility must name the operation, not imply scientific detection.
Do not infer missing units or normalize away physical meaning. Record every
conversion, mask, sorting/rebinning step, reference identity and parameter choice.

Before choosing a method, prepare explicitly synthetic fixtures covering identical
curves, percent versus fractional representations with declared conversion, shifted
and non-overlapping axes, different sampling/resolution, missing/asymmetric errors,
correlated noise, blended features and incompatible signal types. Evaluate recovery
of known transformations, residual calibration under stated assumptions, false
matches, missing-data behavior and provenance reproducibility. Keep real NASA
measurements untouched. These fixtures and evaluation thresholds are not yet built.

Next bounded task: verify the archive's published bandwidth/error conventions and
publication context; define a proposed comparison-input contract without changing
SpectrumData or existing persistence. Then build synthetic evaluation cases and
investigate candidate methods against them. Provider selection and production
comparison remain deferred. Human desktop acceptance of Chunk 4 stays separate.

## Follow-on increment

The initial source audit, metadata investigation, proposed input contract and
same-grid synthetic comparison experiment are now recorded in
`COMPARISON_INPUT_CONTRACT_DRAFT.md` with machine-readable evidence under
`verification_20261028/`. Several conventions remain unverified; the contract is
a draft and method selection is still open. The broader fixture agenda above
is only partly exercised, not complete. No production application behavior changed.
