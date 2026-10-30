# ECAS Development Handoff — Spectral Identification Rework and UI Improvements

## Project

**ECAS — Exoplanetary Characterization & Astrochemistry Suite**

Repository:
https://github.com/brettadin/ECAS_BETA

You are working with two local AI development agents that collaborate and hand work between each other. Coordinate your investigation, planning, implementation and verification between both agents.

Unlike a conventional planning-only exercise, this task is intended to result in working software.

**You are authorised to investigate, plan, implement, test, and update documentation. Do not stop after producing a plan.**

Work incrementally, but keep progressing until the requested functionality is implemented and verified.

---

# 1. Background: Why ECAS has a local spectral library

ECAS is being developed as a tool for exoplanetary atmospheric characterization and astrochemistry.

An important part of the project has been building a local spectral library rather than relying on external websites or requiring users to locate and download spectra themselves.

The objectives are:

- Reliable local access to spectral datasets.
- Reproducible analysis using known datasets.
- Traceable scientific provenance.
- Support for both IR and UV–Vis spectroscopy.
- Broader molecular coverage over time.
- A fallback curation process for molecules or spectral regions not adequately covered by primary sources.
- A foundation for future atmospheric characterization and molecular identification workflows.

The application must use the actual spectral datasets included in the project.

**MOCK DATA IS STRICTLY PROHIBITED.**

Do not introduce fabricated spectra, synthetic reference datasets, placeholder molecular measurements, or simulated detection results to make the identification system appear functional.

If data is missing or unsuitable, report that limitation honestly.

---

# 2. First: Inspect the current project and its spectral data

The current spectral library is located at:

`data/ECAS_Spectral_Library/`

Inspect this directory and its contents before implementation.

Expected structure:

```text
data/ECAS_Spectral_Library/
├── Raw_Sources/
│   ├── IR/
│   └── Uv-Vis/
├── Ready_For_ECAS/
│   ├── IR/
│   └── Uv-Vis/
├── Documentation/
│   ├── IR/
│   └── UV-Vis/
└── README.txt
```

The current collection contains approximately:

- 18 IR JCAMP-DX files across 13 molecules.
- 22 original UV–Vis TXT files across 15 molecules.
- 22 prepared UV–Vis CSV files.

The prepared UV–Vis datasets use wavelength in nm and absorption cross-section in cm²/molecule.

The IR datasets retain their original JCAMP-DX metadata.

Important scientific distinctions:

- IR datasets may represent absorbance or transmittance.
- Sample phases and experimental conditions vary.
- The IR prepared files currently correspond to copies of the raw files.
- UV–Vis datasets have different wavelength ranges, temperatures and sampling densities.
- Some UV–Vis datasets contain negative cross-section values. These must not be silently removed or corrected.
- Not every molecule has both IR and UV–Vis coverage.

Read the library README and documentation to establish the exact current paths, formats and limitations.

Do not assume that every spectrum can be compared directly with every other spectrum.

---

# 3. Investigate the current Comparison tab

Inspect the existing ECAS comparison functionality in detail.

Determine:

- How spectra are currently imported and represented.
- How the Comparison tab obtains its data.
- How spectral datasets are selected.
- How comparisons are calculated.
- How results are presented.
- What currently works.
- What is incomplete or scientifically weak.
- Which existing components can be reused.

Do not discard working application infrastructure unnecessarily.

The goal is to improve the existing comparison functionality by introducing a substantially better molecular identification workflow.

---

# 4. Investigate ECAS v1 — use its Identify tab as the reference

There is an older version of the application called `ecas_v1`. (https://github.com/brettadin/ecas)

It is included in the project history/archive.

Locate and inspect it.

The most important reference is the **Identify tab** in ECAS v1.

The previous identification implementation was significantly better than the current comparison tool.

Investigate its actual implementation, particularly:

- How molecular reference spectra were loaded.
- How observed and reference spectra were compared.
- How matching was calculated.
- How sigma confidence was calculated and interpreted.
- How detection confidence was displayed.
- How multiple molecular candidates were handled.
- How the user selected molecules.
- How results were presented.

Pay particular attention to the sigma-confidence methodology.

We want to bring the useful identification logic from ECAS v1 into the current ECAS application.

**Do not simply recreate the appearance of the old tab. Recover and reuse the underlying identification methodology wherever practical.**

Preserve the useful mathematics and confidence interpretation from v1 rather than inventing a new scoring system without justification.

If the original v1 sigma calculation depends on assumptions, normalization, uncertainty estimates or thresholds, document those assumptions.

Do not claim that a sigma value represents a statistically rigorous detection significance unless the underlying calculation supports that interpretation.

If the v1 implementation cannot be found, investigate the old project thoroughly before attempting to reconstruct it. Report any parts that cannot be recovered.

---

# 5. Implement the new molecular identification workflow

Integrate the improved identification functionality into the current ECAS application.

The objective is to allow a user to select molecules from the local spectral library and identify their potential presence in an observed spectrum.

The workflow should be straightforward.

## A. Molecule selection interface

Provide selectable molecule checkboxes.

For UI clarity, separate the available reference molecules into two groups:

**IR molecules**

**UV–Vis molecules**

Populate these choices from the actual local spectral library.

Do not hardcode molecules that do not have corresponding local reference data.

The user should be able to select multiple molecules.

The selected molecules become the reference candidates for identification.

Make it clear which modality is being used.

If the observed spectrum is IR, use compatible IR reference data.

If the observed spectrum is UV–Vis, use compatible UV–Vis reference data.

Do not compare incompatible spectral types or units.

## B. Identification action

Provide a clearly labelled action, such as:

`Identify Molecules`

When activated:

1. Retrieve the selected observed spectrum or spectra.
2. Retrieve the selected molecular reference datasets from the local library.
3. Apply the recovered ECAS v1 identification/comparison methodology.
4. Calculate the matching results and sigma confidence.
5. Display the potential molecular identifications.

The calculation must use actual spectral values.

Do not generate results from molecule names, predefined scores or mock detection data.

## C. Sigma confidence

Use the same kind of sigma-confidence calculation that made ECAS v1 more effective.

Investigate and reproduce the original methodology as closely as possible.

Preserve the useful features of the v1 calculation, including its interpretation and thresholds where they are supported by the original implementation.

The resulting sigma values should be associated with each molecular candidate.

Do not arbitrarily invent confidence thresholds.

If some datasets lack information required by the v1 calculation, establish a scientifically defensible handling strategy and clearly document the limitations.

## D. Molecular result visualization

Each selected molecule should receive a distinct, consistent colour.

Use those colours when displaying the comparison or identification results.

The user must be able to visually distinguish which molecular reference contributes to each result.

Avoid assigning colours that change unpredictably between calculations.

## E. Results table

At the bottom of the identification interface, add a compact results table.

At minimum, it should display:

| Molecule | Modality | Colour | Sigma |
|---|---|---|---|

The table should contain the selected molecules and their corresponding calculated results.

Use the same colour assigned to each molecule in the plot.

Display sigma values clearly.

Where a molecule cannot be evaluated because of missing or incompatible data, report that condition rather than inventing a result.

---

# 6. Multiple datasets from the same exoplanet

Investigate how ECAS currently represents observations and datasets associated with an exoplanet.

We need to consider a future workflow in which a user can:

- Select an exoplanet.
- Access multiple observational datasets associated with that same planet.
- Select one or more of those datasets.
- Run molecular identification against those datasets.
- Compare identification results between observations.

For example, a planet might have several observations from different instruments, observation dates, wavelength ranges or published studies.

We need to understand how this could work with the existing data model and UI.

Investigate:

- Whether the current database already supports multiple datasets per planet.
- How observations and spectra are associated with planetary records.
- Whether multiple spectra can be loaded into the identification workflow.
- Whether the v1 identification logic can operate on multiple observations.
- How results could be compared across separate observations.

Implement the necessary foundations where reasonably achievable without disrupting existing functionality.

Do not fabricate planetary observations or datasets.

If the existing application does not yet have sufficient real observational data to test this functionality, implement the appropriate architecture and report the limitation.

---

# 7. UI redesign — begin addressing the wider application

The current ECAS UI needs significant visual improvement.

It is functional in places, but the overall presentation is unattractive and inconsistent.

Do not let this derail the molecular identification work, but begin thinking about a coherent UI redesign.

Consider:

- More consistent spacing and alignment.
- Better visual hierarchy.
- Cleaner navigation.
- More modern tab layouts.
- Improved typography.
- Consistent colours and visual conventions.
- Better scientific plots and result tables.
- Reduced visual clutter.
- Better use of available screen space.
- More consistent controls across the application.

The identification interface should be implemented with this future redesign in mind.

Avoid creating an isolated interface that looks completely different from the rest of ECAS.

You may make sensible UI improvements as part of this task, but avoid a complete application-wide redesign until the identification functionality is working.

---

# 8. Scientific and implementation constraints

These requirements are mandatory.

### Real data only

Use the actual local IR and UV–Vis datasets.

Never use mock spectra or fabricated detection results.

### Preserve scientific meaning

Do not silently interchange:

- Absorbance.
- Transmittance.
- Absorption cross-sections.
- Molar absorptivity.
- Quantum yields.
- Gas-phase measurements.
- Liquid-phase measurements.

Use compatible quantities and units for comparisons.

### Preserve provenance

Reference datasets must retain their source identity and relevant experimental metadata.

### Handle incomplete coverage honestly

If a molecule has no suitable local reference dataset, it must not appear as a successful identification candidate.

### Preserve existing functionality

Do not break the current import, plotting, persistence, database or other application workflows.

### Reuse v1 intelligently

Recover the original sigma-confidence logic rather than inventing an unrelated replacement.

### Testing

Add or update tests for:

- Local spectral library discovery.
- Molecule selection.
- Correct modality filtering.
- Reference spectrum loading.
- Sigma calculations.
- Incompatible dataset handling.
- Missing data handling.
- Multiple molecular candidates.
- Colour consistency.
- Results table population.
- Multiple observations where implemented.

Tests must use real project datasets where appropriate, or small explicitly identified test fixtures derived from real source data. Do not use fabricated spectra to demonstrate scientific success.

---

# 9. Documentation

Update the relevant ECAS documentation after implementation.

Record:

- The identification methodology recovered from v1.
- The sigma calculation and assumptions.
- How local spectral reference data are discovered and loaded.
- How IR and UV–Vis candidates are separated.
- Data compatibility requirements.
- Missing molecule coverage.
- Limitations of the current identification workflow.
- How multiple observations per planet are handled or planned.
- Any remaining work required for the wider UI redesign.

Do not create unnecessary duplicate documentation.

Update the authoritative project documentation and decision records where implementation decisions warrant it.

---

# 10. Execution order

Work through the following sequence.

**Phase 1 — Investigation**

- Inspect current Comparison tab.
- Locate and inspect ECAS v1 Identify tab.
- Recover sigma-confidence calculation.
- Inspect current local spectral library.
- Inspect planetary observation/database relationships.

**Phase 2 — Identification implementation**

- Implement molecule selection grouped by IR and UV–Vis.
- Load actual local reference spectra.
- Integrate the v1 identification methodology.
- Implement sigma-confidence results.
- Add consistent molecule colours.
- Add the compact results table.

**Phase 3 — Multi-observation foundations**

- Establish how multiple datasets from the same planet can be selected.
- Integrate identification with multiple observations where the existing architecture supports it.
- Preserve individual observation identities and results.

**Phase 4 — Testing and verification**

- Test the complete workflow using the actual local library.
- Verify calculations and modality compatibility.
- Confirm that no mock data has entered the production workflow.
- Check for regressions in existing functionality.

**Phase 5 — Documentation and further development**

- Update authoritative documentation.
- Identify outstanding limitations.
- Once the requested functionality is working, continue with other worthwhile improvements in the existing project roadmap.

---

# 11. Collaboration between the two agents

Coordinate work to avoid duplication.

Suggested division:

**Agent 1 — Investigation and scientific methodology**
- Inspect ECAS v1.
- Recover the original sigma-confidence calculation.
- Inspect the current comparison implementation.
- Assess scientific compatibility of local datasets.
- Review the correctness of the new calculations.

**Agent 2 — Application implementation**
- Inspect the current application architecture.
- Implement the molecule selection UI.
- Integrate the identification engine.
- Implement plots, colours and result tables.
- Investigate multiple-observation integration.
- Add tests and documentation.

Both agents should communicate findings and review each other's work.

Do not allow the implementation agent to invent a replacement mathematical method while the other agent is still investigating v1.

---

# 12. Definition of done

The primary task is complete when:

1. The current ECAS application can discover its local IR and UV–Vis reference datasets.
2. Users can select multiple molecules using modality-grouped checkboxes.
3. The Identify action performs actual spectral comparisons.
4. The identification uses the recovered v1 sigma-confidence methodology.
5. Each molecule has a distinct, consistent colour.
6. A compact results table displays molecule, modality, colour and sigma.
7. Results are based on actual spectral measurements.
8. Incompatible or missing reference data are handled honestly.
9. Existing application functionality remains operational.
10. The implementation has been tested and documented.

Multiple-observation support should be implemented to the extent the current architecture allows, with any remaining limitations explicitly documented.

After these requirements are satisfied, continue with other useful improvements rather than stopping unnecessarily.

## Final instruction

This is an implementation task, not another prolonged planning exercise.

Investigate the existing code and v1 methodology, agree on the approach between both agents, implement the functionality, test it, and report the results.

Prioritize getting a scientifically defensible, working molecular identification tool into the current ECAS application.

We can refine thresholds, presentation and advanced functionality later. The immediate objective is to restore the stronger identification approach from ECAS v1 using the real local spectral library.

### last minute manual edit

make sure you update the readme and other documents and records as you go. if we get this new version of the identify thing in, the readme and other stuff will be out of date. so if you get bored, make sure all our documents are up to date and accurate. verify all your stuff by reading through the code before you claim something to be true in the documents. 
