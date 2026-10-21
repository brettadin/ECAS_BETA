ECAS development plan
The goal is to build ECAS in manageable chunks, with each chunk producing a working, testable result. We should avoid adding several interconnected systems at once, because that makes errors harder to isolate and leaves you with code that's difficult to understand.

The current application already has a desktop shell, a CSV importer, a spectral-data table, and six passing tests. We'll build on those rather than start over.
Proposed development chunks

Chunk 0 — Working foundation
Complete

Desktop shell, navigation, CSV import, table display, initial tests.

Goal: Maintain a working baseline before expanding functionality.




Chunk 1 — Scientific data model

Define what an ECAS spectrum is independently of the interface.
- ✓ Establish a consistent spectrum representation.
- ✓/x Preserve source paths, column information, and metadata.
- x Separate file-import validation from scientific suitability checks.
- ✓/x Add tests for the model and its validation rules.
Completion criterion: Imported spectra become structured, validated objects rather than loosely organized dictionaries.




Chunk 2 — Projects and persistence

Give datasets a durable home.
- Create and open projects.
- Save imported spectra and associated metadata.
- Reopen a project after closing ECAS.
- Track data sources and changes without silently overwriting originals.
Completion criterion: A saved project can be closed and reopened with its imported data intact.




Chunk 3 — Spectral visualization

Make imported data scientifically inspectable.
- Plot real imported measurements.
- Label axes and units only when known.
- Support basic inspection and dataset selection.
- Clearly distinguish missing metadata from measured values.
Completion criterion: Users can inspect a real spectrum without changing its underlying data.




Chunk 4 — Online archive integration

Expand beyond local-file imports.
- Investigate appropriate scientific archives and available APIs.
- Implement source-specific providers behind a common interface.
- Preserve identifiers, citations, retrieval details, and source metadata.
- Cache retrieved data for reproducible offline access.
Completion criterion: ECAS can retrieve and register a real archival dataset with traceable provenance.




Chunk 5 — Comparison-method investigation

Choose the first comparison method based on evidence, not assumption.
- Define what makes spectra comparable.
- Identify representative scientific test cases and evaluation criteria.
- Investigate candidate methods and their limitations.
- Select and document a method before implementing the production comparison workflow.
Completion criterion: A justified method selection with explicit constraints and tests.




Chunk 6 — Comparison workflow

Connect data, validation, and the selected scientific method.
- Compare eligible spectra using the selected method.
- Explain compatibility failures and method limitations.
- Preserve settings and inputs needed to reproduce a result.
- Present results without implying unsupported abundance or composition estimates.
Completion criterion: A comparison can be reproduced from saved inputs and settings.




Chunk 7 — Integration and reliability

Make the assembled application dependable.
- Test failure recovery and malformed inputs.
- Verify project persistence and offline behavior.
- Test the full workflow from import to comparison.
- Improve error reporting and documentation.
Completion criterion: The complete workflow operates reliably without fabricated production data.



How we'll handle each chunk
Each chunk should follow the same process:
1. Define the goal. Specify exactly what the chunk will and won't do.
2. Inspect the current files. Check the relevant code and architecture documents before making changes.
3. Agree on the design. Identify the files to add or modify and explain their responsibilities.
4. Implement incrementally. Provide commented code, with a manageable number of changes at a time.
5. Test the result. Run automated tests and manually verify the relevant application behavior.
6. Close the chunk. Record what works, what remains incomplete, and what the next chunk depends on.
We should avoid speculative features, large rewrites, and unnecessary abstraction. Architecture should support the planned application without requiring every future feature to be built immediately.