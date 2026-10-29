# ECAS — Exoplanetary Characterization & Astrochemistry Suite

# Comprehensive Program Review and Development Recommendations

**Repository:** [https://github.com/brettadin/ECAS_BETA](https://github.com/brettadin/ECAS_BETA)\
**Review type:** Codebase assessment, scientific-validity review, functional assessment, testing review, and development recommendations\
**Review date:** 29 October 2026\
**Status:** Assessment of the supplied code snapshot and previously examined implementation paths; further verification required

---

## Table of Contents

1. Executive Summary
2. Scope and Limitations of This Review
3. Overall Assessment of ECAS
4. Existing Strengths Worth Preserving
5. Priority 1: Spectral Bins and Instrument Response
6. Priority 2: Forward-Model Scientific Validation
7. Priority 3: Molecular Reference Data and Synthetic Templates
8. Priority 4: Residuals, Uncertainties, and Statistical Interpretation
9. Priority 5: Comparison Eligibility and Metadata Integrity
10. Priority 6: Persistence, Provenance, and Reproducibility
11. Priority 7: Testing and Verification
12. Additional Code-Level Investigation Areas
13. Data Ingestion and File-Format Support
14. User Interface and Scientific Usability
15. Documentation and Project-State Consistency
16. Scientific Claims and Interpretation Boundaries
17. Recommended Development Roadmap
18. Additional Investigations to Conduct
19. Issues That Should Not Be Prioritized Yet
20. Suggested Acceptance Criteria for Future Work
21. Final Assessment

---

# 1. Executive Summary

ECAS has progressed beyond a basic spectral-data viewer. The current BETA codebase contains a developing scientific analysis workflow with spectral-data ingestion, molecular reference management, project persistence, atmospheric forward-model generation, spectral comparison, residual analysis, candidate evaluation, and saved comparisons that can be reopened.

The most significant architectural strength is that ECAS attempts to prevent invalid scientific comparisons rather than simply plotting two spectra together and returning a similarity score.

The comparison framework includes compatibility checks, explicit alignment behavior, unit and observable restrictions, wavelength-support limitations, warnings about model assumptions, and safeguards against treating numerical agreement as proof of molecular detection.

These are valuable foundations for an application intended to support exoplanetary atmospheric characterization.

However, three questions must remain distinct:

1. **Software functionality:** Does the application execute the intended workflow?
2. **Numerical correctness:** Are the implemented algorithms and calculations behaving correctly?
3. **Scientific validity:** Do the input data, physical assumptions, uncertainties, and processing methods justify the conclusions drawn from the results?

The available project history provides encouraging evidence for several functional workflows and reports a substantial automated-test suite. Nevertheless, the full suite has not been independently reproduced in the review environment, and the scientific validity of the forward model and comparison results requires further verification.

The most consequential issue identified in the reviewed code concerns the interpretation of spectral-bin widths and instrument-response metadata. Incorrect assumptions at this stage can affect the model values compared with observations and, consequently, the residuals and candidate rankings.

Other important priorities include independent physical validation of the forward model, clear separation of illustrative synthetic templates from physical molecular reference data, uncertainty and covariance validation, and stronger end-to-end provenance for saved comparisons.

**Overall recommendation:** Continue developing the existing architecture. Do not undertake a broad rewrite. Prioritize the correctness and scientific defensibility of existing functionality before adding more sophisticated analysis features.

## Principal Findings

| Area                     | Assessment                                                                         | Recommended action                                                   |
| ------------------------ | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Application workflow     | Meaningful functionality is present                                                | Preserve and continue testing existing workflows                     |
| Comparison safeguards    | Several thoughtful protections are implemented                                     | Preserve them and strengthen metadata provenance                     |
| Spectral-bin semantics   | A concrete ambiguity exists in the reviewed implementation                         | Investigate and resolve before relying on integrated-model residuals |
| Instrument response      | Matching wavelength coordinates can be conflated with response handling            | Separate coordinate evaluation from response application             |
| Forward model            | Physically motivated implementation with defined assumptions                       | Validate against independent benchmarks                              |
| Molecular references     | Distinguishes catalogue information, cached references, and illustrative templates | Strengthen provenance and visible status reporting                   |
| Residuals and statistics | Safeguards exist, but broader scientific validation is needed                      | Verify uncertainty, covariance, and interpretation                   |
| Saved comparisons        | Integrity checking and reopening are implemented                                   | Clarify reproducibility boundaries and preserve complete provenance  |
| Automated tests          | Meaningful workflow tests exist; one duplicate test definition was identified      | Fix test collection and establish a reproducible baseline            |
| Ingestion                | Strict validation exists for the supported NASA transmission-table path            | Expand format support deliberately and test real file variants       |
| UI and usability         | A functional workflow is present, but scientific complexity remains                | Improve clarity around assumptions, exclusions, and limitations      |
| Documentation            | Some project-state inconsistencies have been identified previously                 | Make focused corrections as implementation work proceeds             |

---

# 2. Scope and Limitations of This Review

This review is based on the supplied ECAS_BETA code snapshot, previously examined implementation paths, project instructions, and the functional and testing results discussed during the project.

It is a static review, not a complete line-by-line audit of every repository file.

The following implementation areas were examined in particular:

- `ecas/comparison/inputs.py`
- `ecas/comparison/eligibility.py`
- `ecas/comparison/alignment.py`
- `ecas/comparison/residuals.py`
- `ecas/comparison/candidates.py`
- `ecas/comparison/model_generator.py`
- `ecas/comparison/persistence.py`
- `ecas/ingestion/nasa_table.py`
- `ecas/projects.py`
- `ecas/ui/comparison_browser.py`
- `ecas/ui/molecular_browser.py`
- `tests/test_spectra_plot.py`
- Selected comparison and integration tests

The review also considered previously discussed project documentation, including the README, project-state material, decision records, architecture documents, and the ECAS development instructions.

### Important verification limitations

- The full test suite was not independently rerun because PySide6 was unavailable in the review environment.
- Historical test totals reported during the project are not treated as independently verified current results.
- The application was not independently exercised end to end in this review.
- Scientific benchmark agreement has not been established merely by inspecting the implementation.
- Additional defects may exist in files and execution paths that were not examined.
- Findings should be rechecked against the current GitHub revision before implementation begins.

A distinction is maintained throughout this document between:

- **Confirmed code issue:** directly supported by the inspected implementation.
- **Scientific or engineering risk:** a plausible concern that warrants investigation but has not been proven to be a defect.
- **Recommendation:** a proposed improvement that requires a decision and, where appropriate, a separate implementation task.

This distinction is important because not every recommendation implies that the existing code is wrong.

---

# 3. Overall Assessment of ECAS

ECAS has a credible foundation for incremental development as a scientific desktop application.

The existing work demonstrates an effort to move beyond basic data display toward a structured workflow in which observations, model outputs, molecular references, and comparison results have explicit roles.

The code also demonstrates awareness that scientific comparison is not simply a numerical subtraction operation. Different observables, units, coordinate frames, instrument responses, and measurement grids can make otherwise plausible-looking comparisons invalid.

That design direction should be retained.

The central remaining challenge is to demonstrate that the numerical results are scientifically defensible, not merely that the software executes the intended operations.

## 3.1 Functional maturity

The reviewed code supports substantial parts of the intended workflow:

- Importing supported spectral data.
- Managing molecular reference information.
- Generating forward models.
- Comparing compatible inputs.
- Computing residuals and candidate diagnostics.
- Saving comparison records.
- Reopening saved comparisons and recomputing diagnostics.

The project history also contains a WASP-39 b workflow test covering model generation, candidate evaluation, passband integration, residual generation, and persistence.

These are meaningful capabilities.

## 3.2 Numerical maturity

The comparison architecture includes validation and alignment components rather than relying entirely on UI-level operations.

This is a good foundation, but each scientific transformation still needs its own numerical tests. Passing a workflow test proves that a sequence of operations executes under the tested conditions; it does not establish that every operation matches the intended scientific method.

## 3.3 Scientific maturity

The forward model has an identifiable physical basis, but it also has limitations associated with its assumptions and available molecular opacity data.

The scientific maturity of ECAS therefore depends on:

- The correctness of wavelength and signal interpretation.
- The validity of instrument-response treatment.
- The suitability of molecular cross sections.
- The physical assumptions used by the forward model.
- The handling of uncertainties and correlated errors.
- The interpretation of residuals and candidate rankings.
- The traceability of the data and parameters used in an analysis.

These areas deserve more attention than simply adding more features.

## 3.4 Recommended development philosophy

The preferred approach is to strengthen the existing architecture incrementally.

Each development burst should have:

1. A clearly identified issue or question.
2. A defined scope.
3. A reviewable implementation plan.
4. Focused code changes.
5. Tests appropriate to the change.
6. Verification against expected behavior.
7. A documented result and any remaining limitations.

The project should avoid combining unrelated scientific changes, UI redesigns, refactoring, and documentation restructuring in one large implementation task.

---

# 4. Existing Strengths Worth Preserving

## 4.1 Structured comparison eligibility

**Relevant files:**

- `ecas/comparison/eligibility.py`
- `ecas/comparison/alignment.py`
- `ecas/comparison/residuals.py`
- `ecas/comparison/candidates.py`

The comparison engine checks whether inputs are compatible before allowing them to participate in a comparison.

The reviewed safeguards include checks involving:

- Observable type.
- Units.
- Coordinate frame.
- Response metadata.
- Measurement grids.
- Required provenance and source information.
- Certain uncertainty and covariance requirements.

The system also avoids some silent transformations and contains safeguards against interpreting numerical closeness as detection significance or abundance.

This is an important architectural strength.

### Recommendation

Preserve these checks as core invariants. Future UI shortcuts, import adapters, and analysis features should not bypass the eligibility system.

Where the system rejects a comparison, the user should receive an actionable explanation identifying the missing or incompatible information.

## 4.2 Explicit alignment behavior

The reviewed alignment workflow includes opt-in behavior and records excluded points when a model does not cover the required wavelength region.

This is preferable to silently extrapolating model values or presenting a partially supported comparison as complete.

### Recommendation

Continue to expose alignment and exclusion decisions to the user. Ensure the number of excluded points, their wavelength ranges, and the reasons for exclusion are visible and retained in saved results.

## 4.3 Physically motivated forward modelling

**File:** `ecas/comparison/model_generator.py`

The function `generate_isothermal_transmission_model()` implements a one-dimensional isothermal transmission-model calculation with hydrostatic structure and spherical-shell chord integration.

The reviewed implementation includes:

- Molecular cross-section contributions.
- Hydrogen-related Rayleigh scattering.
- A haze continuum.
- Cloud-deck or deep-boundary treatment.
- Opacity attribution.
- Wavelength-support restrictions.
- Provenance information.
- Model-content hashing.
- Warnings for certain assumptions and limitations.

The model also restricts unsupported wavelength extrapolation rather than assuming that unavailable molecular opacity data can be extended arbitrarily.

### Recommendation

Preserve the existing physical scope while improving independent validation. A more complicated model is not automatically better if its underlying assumptions and numerical behavior have not been established.

## 4.4 Molecular-reference distinctions

**File:** `ecas/ui/molecular_browser.py`

The reviewed molecular-reference workflow distinguishes catalogue entries from verified or downloaded reference products.

It also communicates that catalogue information alone may not establish a product's units, pressure treatment, temperature, or valid wavelength range.

This is essential because a catalogue listing is not equivalent to a usable molecular cross-section dataset.

### Recommendation

Maintain these distinctions in the UI and in saved model provenance. Do not allow catalogue availability to imply scientific readiness.

## 4.5 Saved-comparison integrity

**Files:**

- `ecas/comparison/persistence.py`
- `ecas/projects.py`
- `ecas/ui/comparison_browser.py`

The reviewed persistence path includes record validation, atomic writing, content-integrity checks, and a reopening workflow that recomputes comparison diagnostics from stored arrays.

This is a useful foundation for returning to previous analyses.

### Recommendation

Retain the existing persistence mechanism. Improve the completeness of its provenance and make clear what the reopening process does and does not reproduce.

## 4.6 Integration testing

The project history includes a WASP-39 b workflow test that reportedly verifies:

- Five eligible model candidates, including a full model and four leave-one-out models.
- A residual table containing 331 rows.
- Passband integration using the `integrate_tophat_bins_v1` operation.
- Saved-comparison round-trip behavior.

This is useful coverage of the connected software workflow.

### Recommendation

Keep this integration test as a regression test, but complement it with independent scientific benchmarks and tests using realistic input variations.

---

# 5. Priority 1: Spectral Bins and Instrument Response

**Priority: High — recommended first investigation**

## 5.1 Files involved

- `ecas/comparison/inputs.py`
- `ecas/ui/comparison_browser.py`
- `ecas/ingestion/nasa_table.py`

## 5.2 Finding: Width fields are interpreted using one convention

In `ecas/comparison/inputs.py`, the function `extract_observation_bin_edges()` searches for column names including:

- `bandwidth`
- `bin_width`
- `fwhm`

When it finds a suitable numeric column, it treats the value as a full width and calculates symmetric edges around the wavelength center:

\lambda\_{\mathrm{center}}-\frac{w}{2}\
]

\lambda\_{\mathrm{center}}+\frac{w}{2}\
]

The function documentation acknowledges that source tables can differ in their use of bandwidth terminology, but the implementation applies one interpretation.

This is a concrete ambiguity in the reviewed code.

A `bin_width` may define the full extent of a bin. A `bandwidth` field may have source-specific semantics. An `fwhm` value describes the width of a response function at half its maximum, but does not establish that the response function is a top-hat.

These concepts cannot safely be treated as interchangeable without evidence about the source format and the intended measurement.

## 5.3 Why this matters

The inferred edges are used to decide which model values contribute to each observational bin.

If the edges are wrong, the model can be integrated over the wrong wavelength intervals. That can change the model values, residuals, and candidate comparisons.

The eligibility engine may not detect this error because the inputs can appear internally consistent: both the observation and model may have valid wavelength coordinates, units, and response identifiers while the assumed response is physically inaccurate.

## 5.4 Finding: Passband integration relies on those inferred bins

In `ecas/ui/comparison_browser.py`, the reviewed workflow:

1. Checks whether bin integration is enabled.
2. Attempts to extract bin edges.
3. Generates a dense wavelength grid for model evaluation when integration is used.
4. Integrates model values over the inferred bins.
5. Associates the resulting model with response metadata.

The alignment path also calls `integrate_model_over_bins()` when appropriate.

This is reasonable when the source's bin semantics and response assumptions are valid. It is not sufficient merely because a width column exists.

## 5.5 Recommendation

Investigate and resolve this issue before treating integrated-model residuals as scientifically reliable.

Recommended changes to consider:

1. **Separate bin width from response shape.** A bin interval does not necessarily describe the full instrument response.
2. **Use source-specific semantics.** Interpret fields according to verified source-format conventions.
3. **Do not treat FWHM as a top-hat width automatically.**
4. **Validate units.** A numeric width without a trustworthy unit should not be used to infer wavelength edges silently.
5. **Handle ambiguity explicitly.** If the correct interpretation cannot be established, leave the bins unresolved and explain the limitation.
6. **Preserve the no-extrapolation behavior.** Unsupported model regions should remain excluded rather than being invented.
7. **Record provenance.** Save the source field, interpretation, unit, response assumptions, and integration method.
8. **Add focused tests.** Cover differing width conventions, missing units, irregular bins, incomplete model coverage, and invalid width values.
9. **Validate against actual source files.** Do not rely exclusively on hand-built test fixtures.

## 5.6 Acceptance criteria

This issue should be considered resolved only when:

- Each supported width field has a defined and justified interpretation.
- The response model is distinguished from simple wavelength-bin boundaries.
- Unsupported or ambiguous inputs cannot silently receive unjustified passband treatment.
- The UI clearly communicates whether integration was performed and under what assumptions.
- The saved comparison records the actual integration method and its provenance.
- Tests verify both valid and ambiguous cases.

---

# 6. Priority 2: Forward-Model Scientific Validation

**Priority: High**

## 6.1 File involved

`ecas/comparison/model_generator.py`

The main reviewed function is `generate_isothermal_transmission_model()`.

## 6.2 Existing implementation

The model implements a physically motivated transmission calculation involving hydrostatic atmospheric structure, molecular opacity, continuum contributions, and spherical-shell chord integration.

The reviewed calculation includes the atmospheric scale-height relationship:

[\
H=\frac{kT}{\mu m_u g}\
]

where the temperature, mean molecular weight, and gravitational acceleration influence the vertical atmospheric structure.

Molecular cross sections contribute to the mixture opacity according to their assumed abundances. The implementation then uses atmospheric geometry and optical-depth calculations to estimate the effective transit depth.

The code also includes restrictions and warnings for unsupported wavelength regions and certain cross-section limitations.

These are substantive features. However, the physical assumptions need independent validation.

## 6.3 Important assumptions

The model's interpretation depends on assumptions including:

- An isothermal atmosphere.
- Hydrostatic structure.
- The selected gravitational acceleration and mean molecular weight.
- The atmospheric reference parameters.
- The molecular opacity data and their validity.
- The treatment of Rayleigh scattering and haze.
- The cloud-deck or deep-boundary treatment.
- The handling of pressure broadening.
- The stellar radius and transit-depth convention.
- The common wavelength support across required molecular cross sections.

These assumptions are not automatically defects. They define the model's scope. The important question is whether the results are correct and useful within that scope.

## 6.4 Existing limitations and warnings

The reviewed implementation warns about certain cases, including:

- Illustrative synthetic broadband molecular templates.
- Zero-pressure cross sections that neglect pressure-broadened wings.
- Significant differences between reference and model temperatures.

It also limits output to supported wavelength regions rather than extrapolating unavailable cross sections.

These warnings should be preserved.

## 6.5 Recommendation: Independent numerical benchmarks

Build a small scientific validation suite using expected behavior derived from analytical limiting cases, published results, or a trusted independent implementation.

Recommended benchmark categories:

### A. Baseline continuum

Construct a controlled case without molecular opacity contributions and verify that the resulting spectrum behaves as expected under the specified continuum assumptions.

### B. Molecular-opacity contribution

Introduce one known opacity contribution and verify that the model changes in the expected direction and approximate scale.

### C. Abundance variation

Vary the assumed abundance of a molecular species while holding other parameters fixed. Verify that the output responds consistently with the model's physical formulation.

### D. Temperature variation

Change atmospheric temperature and verify the expected effects on scale height and transmission features under controlled conditions.

### E. Gravity variation

Vary gravitational acceleration while holding other assumptions fixed. Verify the expected direction of the structural response.

### F. Cloud-boundary behavior

Test the influence of cloud-deck settings and verify that the model behaves consistently with the implemented boundary assumptions.

### G. Wavelength-support boundaries

Verify that unsupported regions are excluded correctly, that the model does not extrapolate silently, and that coverage diagnostics match the returned arrays.

### H. Numerical stability

Test extreme but valid parameter ranges, invalid parameters, non-finite inputs, and wavelength grids with boundary conditions relevant to the algorithm.

## 6.6 Recommendation: Document the validated scope

The model should have a clear description of:

- Its physical assumptions.
- The input parameters it requires.
- The opacity sources it supports.
- Known limitations.
- Validated parameter ranges, where established.
- The meaning and units of its output.
- Which claims its output can and cannot support.

Do not claim that the model is validated merely because the tests pass. The benchmark expectations must themselves be scientifically defensible.

---

# 7. Priority 3: Molecular Reference Data and Synthetic Templates

**Priority: High**

## 7.1 Files involved

- `ecas/ui/molecular_browser.py`
- `ecas/comparison/model_generator.py`
- Relevant reference-data cache and retrieval code

## 7.2 Finding: Automatic mode can use illustrative templates

The reviewed model-generation workflow can use cached ExoMol cross sections when available, but automatic opacity selection can fall back to illustrative synthetic broadband templates.

The implementation includes warnings that distinguish this behavior from the use of physical cross-section data.

This fallback can be useful for development and exploratory testing. The concern is that users may interpret the resulting model or comparison as evidence of actual atmospheric chemistry.

## 7.3 Why the distinction matters

A synthetic template can help test:

- Model-generation plumbing.
- Candidate selection.
- Plotting.
- Residual calculation.
- Persistence.
- UI behavior.

It does not establish that the template accurately represents a molecule's real absorption cross section under the relevant conditions.

Even a genuine molecular cross section must be appropriate for the model's temperature, pressure treatment, spectral range, and units.

## 7.4 Recommendation

Strengthen the distinction between illustrative and physical reference data throughout the application.

Recommended behavior:

- Label illustrative templates visibly in candidate lists and result summaries.
- Preserve their status in saved comparisons.
- Display the selected dataset's identity and relevant limitations.
- Warn when the reference temperature differs from the model temperature.
- Communicate when pressure broadening or other physical effects are not represented.
- Avoid describing illustrative-template results as molecular detections.
- Ensure switching between illustrative and physical data is visible to the user.

## 7.5 Reference-data provenance

The molecular browser already distinguishes catalogue information from downloaded reference products. That is a good starting point.

For each selected molecular reference, preserve the following information where available:

- Molecule and species identity.
- Source and dataset identifier.
- Dataset or release version.
- Download source or URL.
- File hash.
- Units.
- Wavelength or wavenumber range.
- Temperature.
- Pressure treatment.
- Spectral resolution or sampling information.
- Known assumptions or limitations.

Do not invent missing metadata. Unknown values should remain explicitly unknown.

## 7.6 Recommended acceptance criteria

- Catalogue entries are not represented as verified molecular products.
- Illustrative templates are visibly distinguished from physical reference data.
- Reference provenance is preserved through model generation and saved comparisons.
- Unsupported physical properties are not silently assumed.
- Tests verify that the correct reference type is used and that its status survives persistence.

---

# 8. Priority 4: Residuals, Uncertainties, and Statistical Interpretation

**Priority: High**

## 8.1 Files involved

- `ecas/comparison/residuals.py`
- `ecas/comparison/candidates.py`
- `ecas/comparison/eligibility.py`
- `ecas/comparison/alignment.py`
- Relevant UI code in `ecas/ui/comparison_browser.py`

## 8.2 Existing safeguards

The reviewed comparison framework includes safeguards related to uncertainty evidence, covariance, weighted ranking, and the distinction between numerical closeness and scientific detection.

This is a positive design choice.

However, I have not established a specific defect in the residual or covariance calculations from the reviewed material. This section describes an important validation requirement rather than a confirmed calculation error.

## 8.3 Scientific concern

Residuals are only as meaningful as the data-processing and uncertainty assumptions behind them.

Potential complications include:

- Incorrect uncertainty units.
- Uncertainties interpreted as standard deviations when they represent something else.
- Correlated errors between wavelength bins.
- Missing or incomplete covariance information.
- Zero or invalid uncertainty values.
- Singular or ill-conditioned covariance matrices.
- Comparisons over only part of the observation's wavelength range.
- Different instrumental response functions.
- Uncertainties that do not account for all relevant processing effects.

A low residual does not automatically imply that a model is scientifically correct. A ranking among candidates does not automatically identify a molecule. A numerical score does not automatically constitute a detection significance.

## 8.4 Recommendation

Trace the full uncertainty path from ingestion to the final candidate diagnostics.

Verify:

1. How uncertainty values are represented and converted.
2. Whether variance, standard deviation, and covariance are distinguished.
3. Whether covariance dimensions and wavelength ordering are validated.
4. Whether covariance units are consistent with the residuals.
5. How invalid, missing, singular, or ill-conditioned cases are handled.
6. Whether weighted methods require sufficient uncertainty evidence.
7. Whether the UI distinguishes descriptive residuals from statistically weighted results.
8. Whether excluded wavelength bins affect the interpretation of scores.

## 8.5 Statistical terminology

The UI should use terms that match the calculation performed.

For example, avoid using:

- "Detection significance" for a descriptive residual score.
- "Molecular abundance" for a candidate similarity score.
- "Confidence" without a defined statistical interpretation.
- "Best model" without explaining the criterion and assumptions.

Where a statistic has a formal definition, document the method and the conditions under which it is valid.

## 8.6 Recommended tests

- Missing uncertainty.
- Zero and non-finite uncertainty.
- Incorrect uncertainty dimensions.
- Incompatible units.
- Covariance matrices with incorrect shape.
- Singular and ill-conditioned covariance.
- Correlated versus independent measurement cases.
- Weighted and unweighted comparisons.
- Comparisons with partial wavelength coverage.

Expected behavior should be defined from the actual statistical method, not chosen merely to make the tests pass.

---

# 9. Priority 5: Comparison Eligibility and Metadata Integrity

**Priority: High to Medium**

## 9.1 Files involved

- `ecas/comparison/eligibility.py`
- `ecas/comparison/inputs.py`
- `ecas/ui/comparison_browser.py`
- `ecas/ingestion/nasa_table.py`

## 9.2 Existing behavior

The comparison engine requires important metadata, including source identity, role, observable, units, coordinate frame, response information, and provenance information.

The reviewed eligibility checks restrict supported observable types and evaluate compatibility before allowing a comparison.

This provides a valuable validation boundary.

## 9.3 Metadata attestation

The reviewed `observation_input()` adapter in `ecas/comparison/inputs.py` deliberately leaves several comparison-specific metadata fields unset. The UI can then allow the user to attest to information required for comparison.

This is reasonable when the importer cannot establish the relevant scientific context.

I did not establish that the current adapter silently overwrites already-populated response or frame metadata. The adapter examined does not currently populate those fields.

The narrower concern is future robustness: as more importers are added, conflicting metadata could be accepted unless the trust boundary is explicitly defined.

## 9.4 Recommendation

For each consequential metadata field, distinguish between:

- Source-provided information.
- Values derived by the application.
- Values supplied or attested to by the user.
- Values that remain unknown.

Record the provenance of those values in the saved comparison.

If an importer supplies a response identifier, coordinate frame, or other consequential field, the UI should detect conflicts rather than silently replacing the imported value.

Where the user changes a source-derived value, request confirmation and retain the original value and the reason for the change where practical.

## 9.5 Unit and observable validation

Review the supported combinations of:

- Wavelength-axis units.
- Signal units.
- Observable types.
- Coordinate frames.
- Measurement grids.
- Response metadata.

Ensure that conversions are explicit and dimensionally correct.

The application should not treat two measurements as equivalent merely because their numeric arrays have similar shapes or their axis values appear close.

## 9.6 Acceptance criteria

- Invalid combinations are rejected with useful explanations.
- Unknown metadata is not silently replaced with assumptions.
- User attestations are distinguishable from source facts.
- Conflicting metadata are detected when relevant fields are populated.
- Provenance survives persistence and reopening.
- Tests cover both valid and invalid combinations.

---

# 10. Priority 6: Persistence, Provenance, and Reproducibility

**Priority: High**

## 10.1 Files involved

- `ecas/comparison/persistence.py`
- `ecas/projects.py`
- `ecas/ui/comparison_browser.py`

Relevant UI methods include:

- `save_active_comparison()`
- `refresh_saved_comparisons()`
- `reproduce_selected_comparison()`

## 10.2 Existing implementation

The reviewed persistence workflow includes:

- Saved comparison records.
- Validation when loading records.
- Atomic-writing behavior.
- SHA-256 content-integrity checks.
- Recalculation of comparison diagnostics on reopening.
- UI support for selecting and reopening saved comparisons.

This is a useful foundation.

## 10.3 Important limitation

The reviewed reopening workflow recomputes diagnostics from stored arrays rather than re-ingesting the original source files or regenerating the original forward model.

The UI also indicates that raw source files are not re-ingested during this operation.

Consequently, the current workflow primarily supports reproduction of the saved comparison calculation. It does not independently regenerate the entire original analysis from its original sources and configuration.

This is a distinction, not necessarily a defect in the current persistence design.

## 10.4 Integrity versus scientific validity

A content hash can help detect whether the content covered by the hash has changed.

It does not prove that:

- The original source data were correct.
- The metadata were scientifically justified.
- The molecular reference data were appropriate.
- The model assumptions were valid.
- The original calculation was physically accurate.

Integrity checking and scientific validation serve different purposes.

## 10.5 Recommendation

Preserve the existing persistence system and improve the completeness of the saved analysis record.

Where available and practical, save:

### Source information

- Original source identifiers.
- Original file hashes.
- Source format and ingestion path.
- Relevant file metadata.
- Whether original files remain available.

### Reference information

- Molecular dataset identity and version.
- Reference-file hashes.
- Reference units and spectral coverage.
- Relevant temperature and pressure information.

### Model information

- Model parameters.
- Atmospheric assumptions.
- Selected opacity sources.
- Model algorithm version.
- Relevant software version.

### Processing information

- Unit conversions.
- Alignment operations.
- Passband-integration method.
- Response assumptions.
- Excluded points and reasons.
- Uncertainty and covariance treatment.

### Result information

- Candidate identities.
- Residual diagnostics.
- Warnings.
- Eligibility decisions.
- User attestations.
- Whether the record supports stored-result reproduction or full regeneration.

## 10.6 Schema versioning

Saved records may outlive the version of ECAS that created them.

Review whether comparison records have a clear schema version and whether older records are handled safely.

If migrations become necessary:

- Make them explicit.
- Preserve original data where appropriate.
- Test migration behavior.
- Reject unsupported records clearly rather than silently interpreting them under a new schema.

## 10.7 Acceptance criteria

A reopened comparison should clearly communicate:

- What was loaded.
- What was recomputed.
- Which source and model information is retained.
- Whether the original inputs are available.
- Whether the complete analysis can be regenerated.
- Which integrity checks were performed.

---

# 11. Priority 7: Testing and Verification

**Priority: High to Medium**

## 11.1 Confirmed test-definition issue

**File:** `tests/test_spectra_plot.py`

The reviewed file defines `test_axis_labels_set_correctly_with_units()` twice.

In Python, the later definition replaces the earlier binding under the same name. Consequently, only the later function is collected under that name.

This is a confirmed test-definition issue. It does not prove that the plotting implementation is defective.

### Recommendation

Rename the tests to reflect their separate cases, or consolidate them if they are redundant.

After the change, inspect the collected test list and verify that all intended cases are present.

## 11.2 Historical test results

The project history reports historical test results of 622 passed and 22 skipped.

These results are useful project context, but they have not been independently reproduced in the current review environment. PySide6 was unavailable when the test suite was examined.

The correct status is therefore **historically reported, not independently verified in this review**.

## 11.3 Testing strategy

The test suite should cover more than whether the UI can execute a workflow.

Four broad categories are important.

### A. Unit tests

Test individual numerical and data-handling functions:

- Unit conversions.
- Wavelength-grid validation.
- Bin-edge extraction.
- Model interpolation.
- Passband integration.
- Residual calculations.
- Covariance validation.
- Hashing and record validation.

### B. Integration tests

Test connected workflows:

- Importing a supported observation.
- Supplying required metadata.
- Generating a model.
- Aligning and comparing inputs.
- Computing residuals.
- Saving and reopening the result.

### C. Scientific benchmark tests

Test numerical behavior against independent expectations.

These should include physically justified benchmark values or tolerances rather than values selected solely from the current implementation.

### D. Robustness and failure tests

Test:

- Missing columns.
- Invalid units.
- Malformed values.
- Missing metadata.
- Unsupported wavelength coverage.
- Corrupted saved records.
- Failed reference retrieval.
- Invalid model parameters.
- Incomplete covariance information.
- Unsupported input formats.

## 11.4 Test collection and execution

For future verification, record:

- The Python version.
- Dependency versions.
- The exact test command.
- The number of collected, passed, failed, skipped, and deselected tests.
- Any environment-specific limitations.
- The final process exit code.
- Whether the run occurred against the current commit.

A terminal-capture problem should be distinguished from an actual test failure, but a test run should not be declared successful without reliable evidence of its result.

## 11.5 Acceptance criteria

- Duplicate test definitions are resolved.
- The intended tests are collected.
- The suite runs in the project's supported environment.
- The results are recorded accurately.
- Scientific benchmark tests are separate from ordinary software-path tests.
- Important failure paths are covered.

---

# 12. Additional Code-Level Investigation Areas

These are worthwhile investigations that were not established as confirmed defects in the reviewed code.

## 12.1 Partial wavelength coverage

**Relevant files:** comparison alignment, residual, and candidate-generation code.

The reviewed model restricts itself to supported wavelength regions, and the comparison engine can exclude unsupported points.

The remaining concern is whether users can easily understand how much of the observation is actually represented in the comparison.

### Recommendation

Display:

- Total observation bins.
- Bins included in the comparison.
- Bins excluded.
- Exclusion reasons.
- Wavelength range covered.
- Any relevant coverage limitations.

Preserve the same information in saved records.

A candidate score based on a subset of the observation should not be presented as though it necessarily describes the full spectrum.

## 12.2 Numerical stability

Review numerical behavior around:

- Very small or large parameter values.
- Non-finite inputs.
- Nearly duplicate wavelength coordinates.
- Invalid grid ordering.
- Narrow passbands.
- Boundaries of molecular cross-section coverage.
- Invalid covariance matrices.
- Floating-point tolerances.

### Recommendation

Add tests for realistic boundary cases and establish defensible tolerances. Avoid adding arbitrary clipping or fallback behavior without understanding its scientific implications.

## 12.3 Performance and responsiveness

Forward modelling, cross-section interpolation, passband integration, and candidate generation may become computationally expensive with larger data sets.

No specific performance defect was established in this review.

### Recommendation

Measure performance using representative data before introducing caching, vectorisation, background workers, or other optimisations.

If expensive work blocks the UI, consider a controlled background-execution design with explicit cancellation and error reporting.

## 12.4 Error handling

Review how the application handles:

- Corrupted input files.
- Missing required columns.
- Unsupported formats.
- Invalid model parameters.
- Failed reference downloads.
- Corrupted comparison records.
- Unavailable cached data.
- Unexpected numerical failures.

### Recommendation

Failures should produce actionable messages and leave the application in a consistent state.

Where an operation fails, the user should be able to tell whether any data were saved or modified.

## 12.5 Data and algorithm versioning

As the code evolves, the meaning of a saved comparison may depend on the version of the model generator, alignment algorithm, or persistence schema.

### Recommendation

Record algorithm and schema versions where appropriate. Ensure older saved records are not silently interpreted as though they were created using current algorithms.

## 12.6 Internal API boundaries

The current architecture separates ingestion, comparison logic, persistence, and UI responsibilities across several modules.

### Recommendation

Preserve these boundaries where they are working. Scientific rules should remain testable outside the UI wherever practical, and UI behavior should not become the sole enforcement mechanism for comparison validity.

This is a design principle to verify during future implementation, not a claim that the current architecture consistently violates it.

---

# 13. Data Ingestion and File-Format Support

## 13.1 Current supported path

**File:** `ecas/ingestion/nasa_table.py`

The reviewed NASA transmission-table importer validates relevant metadata, including transmission-spectrum type and planet identification, checks expected columns and data types, handles null or invalid values, and records source-file hashes.

This is a useful strict-import strategy for a known format.

## 13.2 Limitations

A strict importer does not automatically provide broad support for the many formats used in spectroscopy and exoplanet science.

Potential sources include:

- NASA archive tables.
- Other archive products.
- Instrument-specific spectra.
- Research CSV files.
- FTIR data.
- UV-Vis exports.
- Text-based numerical data.
- Files with metadata stored in headers.
- Files with wavelength, wavenumber, frequency, or other axes.

The project history also establishes that the available local research data are not all NASA-style transmission tables. Some are FTIR-oriented CSV files, while other UV-Vis data may be stored as text files.

That means the existing import restrictions may limit practical use with the available research data.

## 13.3 Recommendation

Expand ingestion incrementally rather than accepting arbitrary tabular files under a single ambiguous interpretation.

A sensible approach is:

1. Preserve the existing strict NASA transmission-table importer.
2. Establish a generic numerical-spectrum importer for clearly defined input structures.
3. Add support for FTIR exports where their conventions can be documented and tested.
4. Add UV-Vis text-file support based on representative real examples.
5. Keep source-specific parsing separate from shared validation and spectrum representation.

A generic importer should not automatically assume that a two-column file is a transit-depth spectrum. It should identify the numerical columns and request the scientific metadata needed to interpret them.

## 13.4 Missing or ambiguous metadata

When units, observable type, or coordinate frame are missing, the application should not silently invent them.

Instead, it should:

- Import what can be safely identified.
- Preserve the raw source information.
- Flag unresolved fields.
- Request user input where necessary.
- Restrict incompatible comparisons until required metadata are established.

## 13.5 Acceptance criteria

- Existing supported formats continue to work.
- New formats have explicit parsing rules and representative fixtures.
- Units and observables are not inferred from file extensions alone.
- Missing metadata are surfaced to the user.
- Malformed files fail safely.
- Source hashes and provenance remain available.
- Each importer has tests for valid, invalid, and ambiguous input.

---

# 14. User Interface and Scientific Usability

## 14.1 General assessment

The application contains a meaningful workflow for importing observations, generating models, evaluating comparisons, and reopening saved results.

The project history also records that the WASP-39 b workflow worked more extensively than initially expected, including saved-comparison reopening.

The central UI challenge is not simply making the interface more attractive. It is ensuring that the scientific meaning of each operation is understandable.

## 14.2 Make model provenance visible

The distinction between physical molecular cross sections and illustrative templates should be visible where the user selects candidates and reviews results.

A warning that appears only during model generation may be missed when a user later reopens or exports a comparison.

### Recommendation

Display the relevant model type, opacity source, assumptions, and warnings in the candidate summary and saved-comparison view.

## 14.3 Explain alignment and integration

The user should be able to determine whether the application:

- Evaluated the model on observation coordinates.
- Interpolated the model.
- Integrated over spectral bins.
- Applied an explicit response function.
- Excluded unsupported bins.

These operations should not be described with interchangeable labels.

### Recommendation

Use precise operation names and provide concise explanations of the transformations actually performed.

## 14.4 Clarify eligibility failures

When a comparison is rejected, the UI should identify the specific incompatibility and explain how it might be resolved.

For example, missing response information should be distinguished from a response mismatch, and missing units should be distinguished from incompatible units.

### Recommendation

Provide actionable diagnostics without automatically bypassing the underlying scientific restrictions.

## 14.5 Make exclusions visible

If a comparison uses only part of an observation, the UI should display the coverage and exclusion information prominently enough that users do not mistake a partial comparison for a complete one.

## 14.6 Preserve useful exploratory workflows

Exploratory synthetic templates, manually supplied metadata, and saved comparisons can all be useful.

The goal should not be to remove these capabilities indiscriminately. The goal should be to label them correctly, preserve their provenance, and prevent exploratory outputs from being mistaken for stronger scientific evidence.

---

# 15. Documentation and Project-State Consistency

Documentation is an acknowledged area of ongoing work in ECAS. The project history also records that documentation inconsistencies have already been raised as GitHub issues.

The recommendation is therefore to make focused corrections when they are needed to support implementation or prevent misunderstanding, rather than initiating another broad documentation-cleanup project.

## 15.1 README and project-state discrepancy

**Files to check:**

- `README.md`
- `docs/brains/PROJECT_STATE.md`
- `docs/brains/DECISIONS.md`
- `docs/ECAS.md`

Previously examined material contained a potential discrepancy: the README described some comparison or analysis functionality as not implemented, while newer project-state information and current code described forward-model and comparison-related capabilities.

This discrepancy needs contextual verification. It may reflect outdated documentation or a distinction between basic comparison and more advanced scientific analysis.

### Recommendation

Establish one consistent description of:

- Implemented capabilities.
- Partially implemented capabilities.
- Planned capabilities.
- Known limitations.
- Features that are exploratory rather than scientifically validated.

Do not simply replace old claims without checking what they meant.

## 15.2 Architecture documents

Relevant documents include:

- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/DATA_FLOW.md`
- `docs/architecture/DATA_MODELS.md`
- `docs/architecture/MODULE_RESPONSIBILITIES.md`
- `docs/architecture/VALIDATION_STRATEGY.md`
- `docs/architecture/ECAS_Architecture_Specification.md`

Some architecture documents may describe intended or provisional designs rather than the actual implementation.

This is acceptable if their status is clear.

### Recommendation

When reviewing a feature, compare the relevant architecture document with the implementation. Correct discrepancies that affect decisions, data handling, validation, or expected behavior.

Avoid rewriting every architecture document simply to make them uniform.

## 15.3 Scientific assumptions should be documented near their implementation

The spectral-bin interpretation issue illustrates why scientific assumptions need to be recorded where they are applied.

A general statement elsewhere in the documentation is not enough if the code makes a consequential assumption about a particular data field.

### Recommendation

Document important assumptions in:

- The relevant implementation or function documentation.
- The model or processing provenance.
- The UI where the assumption affects a result.
- The project decision record when it establishes a lasting design choice.

## 15.4 Decision records and historical plans

The project instructions identify current project-state and decision material as important sources of truth. The project history also discusses multiple locations for Chunk 4 planning material.

Multiple competing documents can cause future work to follow an outdated plan.

### Recommendation

Before creating or reorganising planning documents, establish which current plan and decision record are authoritative.

Preserve historical documents, and do not rewrite them to make them appear to describe the current implementation.

## 15.5 Documentation acceptance criteria

Documentation updates should:

- Reflect actual code behavior.
- Distinguish implementation from plans.
- Preserve historical decisions.
- Avoid claiming scientific validation that has not occurred.
- Identify unresolved assumptions.
- Point to the relevant implementation and tests where practical.

---

# 16. Scientific Claims and Interpretation Boundaries

ECAS should clearly distinguish exploratory analysis from scientifically supported inference.

This is especially important because the application can produce numerical results and visualizations that appear authoritative even when the inputs or assumptions remain uncertain.

| Capability                    | What it can support                                                | What it does not establish by itself                                     |
| ----------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------ |
| Spectral overlay              | Visual comparison on compatible coordinates                        | Equivalent physical measurements or instrumental responses               |
| Residual calculation          | Numerical differences between compatible inputs                    | Molecular detection or reliable abundance                                |
| Candidate ranking             | Relative ranking under the selected method and assumptions         | Unique molecular identification                                          |
| Synthetic-template comparison | Exploration and testing of spectral patterns                       | Physical confirmation that the molecule is present                       |
| Forward modelling             | Predictions under stated model assumptions                         | That the assumptions accurately describe the observed planet             |
| Leave-one-out analysis        | Sensitivity to removing a component under the chosen configuration | Detection significance or a formal abundance constraint                  |
| Passband integration          | Model averaging under a specified integration assumption           | Correct instrument-response treatment unless the assumption is justified |
| Saved-comparison reopening    | Recalculation of diagnostics from stored data                      | Full independent regeneration from original sources                      |
| Eligibility checks            | Detection of specified incompatibilities                           | Correctness of metadata supplied by a source or user                     |

## 16.1 Avoid overclaiming

The UI and saved results should not imply that:

- A low residual proves a model is physically correct.
- A close molecular template establishes a detection.
- A candidate score is a molecular abundance.
- A leave-one-out result establishes statistical significance.
- A content hash proves scientific correctness.
- A successful test proves empirical validity.

## 16.2 Preserve exploratory analysis

Exploratory workflows are still useful. They can help users inspect data, understand model behavior, investigate possible spectral features, and test hypotheses.

The objective is to communicate the evidence level accurately, not to prevent users from exploring.

---

# 17. Recommended Development Roadmap

The following sequence is recommended based on the reviewed code and risks. It is a proposal for prioritization, not a claim that these tasks have already been approved or implemented.

## Phase 1 — Resolve spectral-bin and response semantics

**Priority: Highest**

### Scope

- Verify the supported source formats and their width-field conventions.
- Review `extract_observation_bin_edges()`.
- Review the model-generation and alignment paths in `comparison_browser.py`.
- Distinguish coordinate matching from response application and bin integration.
- Verify how response IDs and evidence are assigned.
- Add tests for ambiguous and valid input conventions.

### Completion condition

The application must not silently infer an unjustified passband or instrument-response interpretation. The processing operation and its limitations must be visible and recorded.

## Phase 2 — Establish independent forward-model benchmarks

**Priority: High**

### Scope

- Define benchmark cases with defensible expected behavior.
- Verify the baseline continuum.
- Test molecular-opacity contributions.
- Test controlled temperature and gravity variations.
- Test cloud-boundary behavior.
- Test wavelength-support restrictions.
- Test numerical stability within the intended operating range.

### Completion condition

The model's numerical behavior has been checked against independent scientific expectations, and its validated scope and limitations are documented.

## Phase 3 — Strengthen molecular reference provenance

**Priority: High**

### Scope

- Trace reference identity and metadata from catalogue or download through model generation.
- Confirm how temperature, pressure treatment, units, and wavelength coverage are handled.
- Verify the separation between illustrative templates and physical reference data.
- Preserve warnings and reference identities in saved comparisons.

### Completion condition

A user can determine which molecular reference was used, what is known about it, and which limitations apply to the result.

## Phase 4 — Review uncertainty and residual calculations

**Priority: High**

### Scope

- Trace uncertainty handling through ingestion and comparison.
- Verify covariance requirements and numerical behavior.
- Review the meaning of candidate scores.
- Test missing, invalid, and correlated uncertainty cases.
- Confirm that partial coverage is reflected in diagnostics.

### Completion condition

The application clearly distinguishes descriptive residuals from statistical methods and does not imply conclusions unsupported by the implemented calculation.

## Phase 5 — Improve saved-comparison reproducibility

**Priority: High**

### Scope

- Review stored comparison fields and schema versioning.
- Record source and reference hashes where available.
- Preserve model parameters and processing settings.
- Preserve exclusions, warnings, and attestations.
- Distinguish stored-result reproduction from end-to-end regeneration.

### Completion condition

Users can identify the provenance and reproducibility limits of each saved comparison.

## Phase 6 — Repair the test-definition issue and establish a verified baseline

**Priority: Medium to High**

### Scope

- Rename or consolidate duplicate test definitions in `tests/test_spectra_plot.py`.
- Confirm intended test collection.
- Run the suite in the supported environment.
- Record the test results and environment.
- Add focused tests for the highest-risk code paths.

### Completion condition

The current test baseline is reproducible and relevant tests are demonstrably collected and executed.

## Phase 7 — Improve ingestion support based on real data

**Priority: Medium**

### Scope

- Preserve the existing NASA transmission-table importer.
- Identify the actual formats required by available research data.
- Add generic numerical-spectrum support where appropriate.
- Add FTIR and UV-Vis parsing based on representative real files.
- Maintain strict scientific metadata validation.

### Completion condition

Each supported format has explicit parsing and interpretation rules, and ambiguous data cannot silently enter an incompatible comparison.

## Phase 8 — Focused documentation and UI corrections

**Priority: Medium**

### Scope

- Correct confirmed discrepancies in current documentation.
- Make model and reference provenance visible.
- Clarify response processing and exclusions.
- Improve eligibility failure messages.
- Ensure saved-comparison labels accurately describe reproduction behavior.

### Completion condition

The UI and authoritative documentation accurately describe implemented behavior, scientific assumptions, and known limitations.

---

# 18. Additional Investigations to Conduct

The following investigations would provide valuable evidence before larger development decisions are made.

## Investigation A — Trace a real observation from source to residual

**Recommended first investigation.**

Choose one real supported observation and trace it through:

1. Source file and metadata.
2. Ingestion.
3. Unit interpretation.
4. Bin-edge extraction.
5. Model generation.
6. Response handling.
7. Eligibility assessment.
8. Alignment and integration.
9. Residual calculation.
10. Candidate diagnostics.
11. Saved-comparison creation.
12. Reopening and reproduction.

### Objective

Identify exactly where source information is preserved, inferred, replaced, or lost, and verify whether the passband and response concerns affect the actual workflow.

## Investigation B — Audit one complete WASP-39 b result

Take a successful comparison and determine the exact meaning of its candidate scores, residuals, exclusions, and warnings.

Questions to answer:

- Which data were used?
- Which molecular references were selected?
- Were any illustrative templates used?
- Which wavelengths were excluded?
- Was passband integration applied?
- What uncertainty information was used?
- What do the candidate scores mathematically represent?
- Which conclusions are supported by the implemented method?
- Which conclusions remain exploratory?

### Objective

Establish whether the result presentation accurately reflects the strength and limitations of the underlying calculation.

## Investigation C — Reproduce the test suite

Run the current test suite in the project's supported local environment.

Record the environment, command, collected tests, results, skips, and exit status.

### Objective

Establish a verified software baseline before further implementation.

## Investigation D — Audit ingestion against real file variants

Use representative files from the actual supported archives and local research data.

Test missing metadata, unusual column names, inconsistent units, missing columns, and valid variations in file layout.

### Objective

Determine the practical boundaries of the current ingestion system and identify the most useful next format to support.

## Investigation E — Review persistence across software changes

Inspect how saved comparison records behave when required fields are missing, schema versions differ, or referenced data are no longer available.

### Objective

Ensure saved comparisons remain interpretable and fail safely when the current application cannot reproduce or validate an older record.

---

# 19. Issues That Should Not Be Prioritized Yet

The following activities may be worthwhile later but are not the most urgent responses to the findings in this review.

## 19.1 Replacing the comparison architecture

The existing eligibility and comparison structure contains useful safeguards. No evidence reviewed here justifies a wholesale replacement.

## 19.2 Rewriting the forward model before benchmarking it

The first step should be to establish which aspects of the current model are correct, where its limitations lie, and what improvements are scientifically necessary.

## 19.3 Adding sophisticated retrieval and detection-significance features

More advanced inference should follow validation of the input interpretation, forward model, uncertainty treatment, and existing diagnostics.

## 19.4 Expanding the molecular catalogue solely to increase coverage

More reference entries do not automatically mean more scientifically usable data. Reference provenance, units, conditions, and validity are more important than catalogue size alone.

## 19.5 Optimizing performance without profiling

Measure actual runtime and responsiveness before introducing major caching or concurrency changes.

## 19.6 Broad documentation restructuring

Documentation issues already have attention in the project. Focused corrections tied to actual implementation decisions are more useful than a large, unrelated cleanup.

## 19.7 Adding automatic assumptions to simplify the UI

A simpler workflow is not necessarily a better scientific workflow if it hides uncertainty about units, response functions, or observables.

Automation should be used where the application has enough evidence to make a justified decision. Otherwise, the ambiguity should remain visible.

---

# 20. Suggested Acceptance Criteria for Future Work

These criteria are intended to support controlled development and review.

They should be adapted to each implementation task rather than treated as a requirement to complete everything at once.

## 20.1 Code changes

- The task has a defined scope.
- The relevant implementation paths have been inspected.
- Existing behavior and constraints are understood.
- Changes remain limited to the approved scope.
- Existing safeguards are preserved.
- New behavior is covered by focused tests.
- Unrelated code and documentation are not changed unnecessarily.

## 20.2 Scientific behavior

- Units and observables are explicit.
- Relevant response and binning assumptions are justified.
- Unsupported wavelength regions are handled transparently.
- Physical assumptions are documented.
- Numerical results are tested against defensible expectations.
- Warnings accurately represent the limitations of the method.
- The UI does not overstate the scientific meaning of a score.

## 20.3 Data and provenance

- Source information is preserved where available.
- User-supplied metadata are distinguishable from source metadata.
- Molecular references have traceable identities.
- Processing settings are retained in saved comparisons.
- Hashes are described as integrity checks rather than proof of scientific correctness.
- Reproduction limitations are clearly communicated.

## 20.4 Tests and verification

- Intended tests are collected.
- Relevant tests pass in the supported environment.
- Failures are investigated rather than dismissed.
- Scientific benchmark tests are separate from workflow tests.
- Important edge cases and invalid inputs are covered.
- The test result and environment are recorded accurately.

## 20.5 Documentation

- Current implementation status is accurate.
- Planned behavior is not presented as implemented.
- Scientific limitations are stated clearly.
- Decisions that affect future implementation are recorded.
- Historical records are preserved appropriately.
- Documentation changes remain within the approved task scope.

---

# 21. Final Assessment

ECAS has a credible technical foundation for incremental development as an exoplanetary spectral-analysis application.

The strongest aspects of the current BETA are its structured comparison framework, explicit compatibility checks, physically motivated forward-model implementation, distinction between molecular catalogue entries and reference products, and saved-comparison workflow.

These are meaningful achievements and should be preserved.

The most important outstanding issue is whether the data-processing assumptions and physical calculations are sufficiently justified for the scientific interpretations the application invites users to make.

The spectral-bin and instrument-response ambiguity is the clearest concrete example. If the application infers the wrong bin boundaries or assigns response semantics that do not reflect the processing performed, the resulting residuals may be numerically consistent but scientifically misleading.

The forward model also needs independent numerical validation. Existing warnings and restrictions are valuable, but they do not substitute for benchmark comparisons. Similarly, candidate rankings and residual diagnostics require a clear relationship to the actual uncertainty information and assumptions.

The persistence workflow is a good foundation, but users need to know whether a reopened comparison reproduces stored calculations or regenerates the entire analysis from original sources.

Finally, the automated tests should be strengthened around these scientific and data-handling concerns, and the duplicate test definition in `tests/test_spectra_plot.py` should be corrected.

## Recommended next actions

In order of importance:

1. **Investigate spectral-bin semantics and instrument-response handling.**
2. **Trace one real observation through the entire comparison pipeline.**
3. **Establish independent benchmarks for the current forward model.**
4. **Verify the uncertainty and residual-calculation assumptions.**
5. **Strengthen provenance and reproducibility for saved comparisons.**
6. **Fix the duplicate test definition and reproduce the current test baseline.**
7. **Improve ingestion support based on representative real research files.**
8. **Make focused UI and documentation corrections tied to confirmed behavior.**

This is not a recommendation to stop development, discard the current implementation, or undertake a broad rewrite.

It is a recommendation to shift some effort from adding functionality toward demonstrating that the existing functionality behaves correctly and that its outputs mean what the application says they mean.

The most productive next step is to trace a real observation through the current pipeline, starting with its source metadata and ending with the saved residual result. That investigation should establish whether the highest-priority concerns affect the actual workflow and provide a concrete basis for the next small, controlled implementation task.

**Overall conclusion:** ECAS has progressed into a substantive scientific software project. Its next stage should focus on verification, scientific defensibility, and traceability, building on the existing architecture rather than replacing it.

---

*End of review.*