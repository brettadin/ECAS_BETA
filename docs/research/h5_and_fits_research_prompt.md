# ACT TASK: Scientific File Format Investigation and Documentation — HDF5 and FITS

## Objective

Conduct the approved technical investigation into HDF5 and FITS scientific data formats and document the findings in a permanent ECAS research reference.

**Mode: ACT**

You are authorized to:
- Research official documentation and scientific standards.
- Inspect the existing ECAS repository and example data.
- Use Python and appropriate scientific libraries to inspect the actual files.
- Perform read-only experiments to understand file structures and metadata.
- Create one dedicated research documentation file containing your findings.

You are NOT authorized to:
- Implement HDF5 or FITS importers.
- Modify application source code.
- Modify existing tests.
- Change existing architecture or data models.
- Install unnecessary dependencies.
- Refactor existing functionality.
- Modify or reorganize the example scientific datasets.

## 1. Required learning before file inspection

Do not begin by simply attempting to load the example files.

First study the formats using authoritative documentation.

### HDF5 resources

- HDF Group documentation: https://docs.hdfgroup.org/hdf5/
- HDF5 User Guide: https://docs.hdfgroup.org/hdf5/latest/_u_g.html
- h5py documentation: https://docs.h5py.org/en/stable/

Understand:
- Files, groups, datasets, and attributes.
- Hierarchical organization.
- Multidimensional arrays.
- Metadata organization and inheritance.
- Dataset dimensions and data types.
- Coordinate arrays and scientific conventions.
- Compression, chunking, references, and links.
- Why different scientific applications can produce entirely different HDF5 schemas.

### FITS resources

- Official FITS standard: https://fits.gsfc.nasa.gov/fits_standard.html
- NASA FITS documentation: https://fits.gsfc.nasa.gov/
- Astropy FITS documentation: https://docs.astropy.org/en/stable/io/fits/
- Astropy WCS documentation: https://docs.astropy.org/en/stable/wcs/

Understand:
- FITS file structure.
- Primary and extension HDUs.
- Image HDUs and multidimensional arrays.
- Binary and ASCII tables.
- Headers and metadata keywords.
- FITS WCS and coordinate transformations.
- How pixel or array indices relate to physical coordinates.
- How spectral, spatial, and temporal axes are represented.

### Additional resources

- Astropy: https://docs.astropy.org/en/stable/
- Specutils: https://specutils.readthedocs.io/en/stable/
- ASDF: https://asdf.readthedocs.io/en/stable/

Investigate the relevance and limitations of these tools.

Record the documentation and standards actually consulted, with links.

Do not claim to have studied a resource unless it was actually accessed and examined.

## 2. Understand scientific interpretation

Investigate how software determines what the contents of a scientific file actually represent.

Separate:

**Structural discovery**
- Groups.
- Datasets.
- Arrays.
- Dimensions.
- HDUs.
- Tables.
- Headers.
- Attributes.
- Data types.

**Scientific interpretation**
- Wavelength.
- Frequency.
- Wavenumber.
- Time.
- Flux.
- Transit depth.
- Spatial coordinates.
- Detector coordinates.
- Spectral intensity.
- Uncertainties.
- Other physical quantities.

Explain why discovering a numerical array does not establish its scientific meaning.

## 3. Axis and coordinate identification

Investigate how axis meanings are established using:

- FITS WCS.
- FITS header keywords.
- HDF5 attributes.
- Dataset names and descriptions.
- Table column metadata.
- Associated coordinate arrays.
- Parent-group and file-level metadata.
- Instrument and processing pipeline conventions.
- Recognized scientific standards.

Do not infer physical meaning from array shape alone.

Investigate how coordinate information is associated with the correct measurement arrays, including when coordinates are stored separately or defined through transformations.

Explain how to handle:
- Missing metadata.
- Conflicting metadata.
- Incomplete WCS.
- Ambiguous units.
- Multiple coordinate systems.
- Unknown schemas.

Develop a confidence classification:

- Explicit.
- Strongly inferred.
- Tentative.
- Unknown.

Explain the evidence required for each classification.

## 4. Inspect actual ECAS example files

After learning the formats, inspect the real examples in the repository.

### FITS files

Location:

`ECAS_BETA/data/`

First inspect the directory and establish which FITS files are actually present.

For each relevant file, investigate:
- Origin and scientific purpose.
- HDU count and structure.
- HDU types.
- Header contents.
- Dimensions and data types.
- WCS definitions.
- Units.
- Coordinate systems.
- Scientific quantities represented.
- How its axes can be interpreted.

Do not assume that all files have the same structure.

### HDF5 files

Location:

`ECAS_BETA/data/wasp-39b/W39_PRISM_data/`

Verify the actual directory and filenames.

Inspect the available files, including where present:

- `Eureka_transit_spec.h5`
- `FIREFLy_transit_spec.h5`
- `Tiberius_transit_spec.h5`
- `Tshirt_transit_spec.h5`
- `Eureka_normalized_specphot.h5`
- `Tiberius_normalized_specphot.h5`
- `firefly_normalized_specphot.h5`
- `tshirt_normalized_specphot.h5`
- `best_fit_model.h5`
- `limb_asymmetry_spectrum.h5`

For each relevant product, establish:
- Internal group and dataset structure.
- Dataset shapes and data types.
- Attributes and metadata.
- Coordinate representations.
- Units.
- Uncertainties and quality information.
- Scientific meaning of the datasets.
- Relationship to the underlying observations.
- Differences between processing pipelines.

Do not assume similarly named files have identical schemas.

Do not merely print array shapes. Explain what the structures mean and identify the evidence supporting that interpretation.

If a file's scientific meaning cannot be established, explicitly document the uncertainty.

## 5. Investigate the data producers

For the WASP-39 b files, research the relevant pipeline documentation:

- Eureka!
- FIREFLy
- Tiberius
- tshirt
- JWST data-product documentation.

Establish how these tools organize their scientific products and whether they use different HDF5 conventions.

For FITS files, identify the originating instruments, archives, and processing software where possible.

Consult producer documentation where necessary to understand the actual data structures.

## 6. Evaluate Python libraries

Investigate the responsibilities and limitations of:

### HDF5
- `h5py`

### FITS
- `astropy.io.fits`
- `astropy.wcs`

### Scientific interpretation
- `astropy.units`
- `astropy.coordinates`
- `astropy.time`
- `specutils`

Include other libraries only where they offer a demonstrated benefit.

Clearly distinguish:
1. Opening files.
2. Discovering structures.
3. Extracting measurements.
4. Interpreting metadata.
5. Establishing scientific meaning.
6. Preparing data for analysis.

Do not assume one library automatically handles every stage.

## 7. Assess relevance to ECAS

Inspect the current application and documentation.

Pay attention to:
- Existing data models.
- Existing ingestion architecture.
- CSV support.
- Visualization.
- Metadata and provenance.
- Validation and error handling.

Use the actual current implementation rather than assuming historical documentation is accurate.

Explain how the knowledge gained could inform future ECAS support.

Consider:
- Separate format-specific readers.
- A shared scientific data representation.
- Structural discovery separated from interpretation.
- Preservation of multidimensional data.
- Metadata and provenance retention.
- GUI presentation of discovered datasets and coordinates.
- User confirmation of ambiguous axis assignments.

These are investigation topics, not approved implementation tasks.

Do not modify the existing architecture.

## 8. Create the permanent research reference

Create:

`docs/research/SCIENTIFIC_FILE_FORMATS_HDF5_FITS.md`

If `docs/research/` does not exist, create that directory.

This document must be sufficiently detailed to serve as a future technical reference for ECAS development.

It should contain:

1. HDF5 fundamentals and internal organization.
2. FITS fundamentals and internal organization.
3. Differences between the formats.
4. Scientific metadata and schema conventions.
5. FITS headers and WCS.
6. HDF5 attributes and coordinate representations.
7. Axis and coordinate identification.
8. Scientific interpretation and confidence.
9. Findings from the actual ECAS FITS examples.
10. Findings from the actual WASP-39 b HDF5 examples.
11. Pipeline-specific differences.
12. Recommended Python libraries and their responsibilities.
13. Scientific data integrity and provenance requirements.
14. Implications for future ECAS architecture.
15. Known limitations and unresolved questions.
16. Recommended future implementation stages.
17. References and official documentation.

### Documentation quality requirements

The document must teach a future developer how to approach these formats, not merely summarize this investigation.

Include:
- Clear explanations.
- Relevant technical terminology.
- Examples of actual structures discovered.
- Representative metadata and header examples from the inspected files.
- Explanation of how physical coordinates are established.
- Practical guidance on inspecting unfamiliar files.
- Common pitfalls and incorrect assumptions.
- Links to the relevant official documentation.

Where useful, include small illustrative Python snippets demonstrating read-only inspection with `h5py` and Astropy.

Do not include fabricated output or present illustrative examples as actual file contents.

Clearly distinguish general format behavior from pipeline-specific findings.

## 9. Make the document useful for future development

The new reference must explicitly establish the following principle:

**ECAS must understand a scientific file's structure and metadata before assigning scientific meaning to its contents.**

Future developers and AI coding agents should be able to use this document when:
- Adding scientific file-format support.
- Investigating unfamiliar datasets.
- Developing importers.
- Determining axis meanings.
- Interpreting coordinate systems.
- Handling scientific units.
- Preserving uncertainties and provenance.

Include a short section titled:

`Guidance for Future ECAS Development`

This section should explain when developers should consult the reference and which principles must be followed.

Do not add speculative implementation details or imply that future capabilities already exist.

## 10. Final verification and report

After completing the investigation:

- Inspect the new Markdown file.
- Verify that all referenced paths and links are accurate.
- Confirm that actual file findings are supported by inspection.
- Confirm that no application source code, tests, or existing documentation were unintentionally changed.
- Review the Git diff and report all changes.

Report:

1. Resources studied.
2. HDF5 findings.
3. FITS findings.
4. Actual ECAS file inspection results.
5. Axis and metadata interpretation findings.
6. Pipeline-specific findings.
7. Recommended libraries.
8. Important limitations and unresolved questions.
9. Location of the new research document.
10. Exact files changed.
11. Confirmation that no implementation was performed.

Do not claim that all example files were successfully interpreted if some could not be understood.

Do not install dependencies merely to complete the investigation without first checking what is already available. If a dependency is unavailable, report the limitation.

## Final boundaries

This task authorizes research, read-only inspection, and creation of the single dedicated research reference.

It does not authorize:
- Importer implementation.
- Application changes.
- Test changes.
- Data-model changes.
- GUI changes.
- Existing documentation rewrites.
- Dependency additions.
- Dataset modifications.

Complete the investigation and documentation, then stop for review.