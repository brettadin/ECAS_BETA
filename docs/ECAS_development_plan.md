ECAS development plan
The goal is to build ECAS in manageable chunks, with each chunk producing a working, testable result. We should avoid adding several interconnected systems at once, because that makes errors harder to isolate and leaves you with code that's difficult to understand.

The current application already has a desktop shell, a CSV importer, a spectral-data table, and six passing tests. We'll build on those rather than start over.
Proposed development chunks

Chunk 0 — Working foundation
Complete

- ✓ Desktop shell, navigation, CSV import, table display, initial tests.

Goal: Maintain a working baseline before expanding functionality.




Chunk 1 — Scientific data model

Define what an ECAS spectrum is independently of the interface.
- ✓ Establish a consistent spectrum representation (frozen dataclass).
- ◐ Preserve source paths, column information, and metadata: path/columns retained in SpectrumData; units/signal-type remain None (uninferred per spec); no scientific metadata beyond CSV columns exists.
- ✗ Separate file-import validation from scientific suitability checks: importer validates structure and records warnings but performs no scientific suitability evaluation.
- ◐ Add tests for the model and its validation rules: test_csv_importer.py provides 8 functional tests covering required columns, missing values, invalid numbers; spectrum.py lacks direct type/unit assertions.

Completion criterion: Imported spectra become structured, validated objects rather than loosely organized dictionaries.




## Chunk 2 — Projects and persistence

**Status: Complete (core persistence verified)**  
**Deferred:** Comprehensive change-history/provenance tracking remains a future design decision.

Give datasets a durable home.

- [x] Create the SQLite persistence layer for spectrum data.
- [x] Save imported spectra and preserve `source_file`, columns, units, `signal_type`, and warnings.
- [x] Reload saved spectra from the SQLite database.
- [x] Verify that all 7 `SpectrumData` fields survive the save/load round trip.
- [x] Preserve column order and `None` values.
- [x] Handle spectra without an uncertainty column.
- [x] Support saving and loading multiple spectra and loading by index.
- [x] Handle nonexistent projects and database-clearing operations.
- [x] Validate project IDs, including path traversal and symlink escape cases.
- [x] Verify persistence implementation: `python -m pytest tests/test_persistence.py -v` — **20 passed**.
- [x] Confirm the completion criterion: saved spectrum data can be reloaded intact, verified by `test_round_trip_preserves_all_fields`.
- [x] Verify the final Git working-tree status and commit contents, if not already completed.

**Data integrity and scope**
- The source file path is tracked through `source_file`.
- Import warnings are preserved in the stored JSON data.
- Original CSV files are not modified by the persistence layer.
- Comprehensive change-history/provenance tracking is not implemented and remains deferred unless explicitly required.

**Verification note**
- Persistence tests: **20 passed**.
- Full test suite: **30 passed, 1 failed**.
- The remaining failure is `test_main_window_has_expected_navigation`, which expects the window title to start with `ECAS`. The current title starts with `Exoplanetary Characterization`. Track this separately from Chunk 2; it does not invalidate the passing persistence tests.

**Completion criterion:** A saved project can be closed and reopened with its imported spectrum data intact. **Verified by the passing persistence round-trip test.**




Chunk 3 — Spectral visualization

Make imported data scientifically inspectable.
- **Goal:** Plot real imported measurements for visual inspection.
- **Completion criterion:** Users can inspect a real spectrum without changing its underlying data.

**Progress checklist**

Plotting component:
- [x] Create the PyQtGraph-based plotting widget.
- [x] Accept normalized `SpectrumData` rather than parsing CSV files in the plotting component.
- [ ] Apply available axis and signal units from `SpectrumData`.
- [ ] Filter missing, non-numeric, and non-finite coordinate pairs.
- [ ] Reset visible and internal state after unsuccessful loads.
- [ ] Verify plotted coordinates against the supplied measurements.
- [ ] Verify source rows, columns, and metadata remain unchanged.

Application integration:
- [ ] Display the plotting widget on the existing Spectral Data page.
- [ ] Update the plot and data table together after a successful import.
- [ ] Replace the previous plot when a new spectrum is imported.
- [ ] Ensure rejected imports do not leave a misleading previous dataset visible.
- [ ] Verify missing metadata is not presented as measured information.

Verification:
- [ ] Run the targeted plotting tests and record the actual result.
- [ ] Run the full test suite and investigate failures.
- [ ] Manually verify plotting, table behavior, replacement, and rejected imports.

Dataset selection:
- [ ] Resolve whether selection among saved spectra is required in Chunk 3,
      given that the current import workflow replaces the displayed dataset.
- [ ] Implement and test the agreed selection behavior if it is required.

Completion:
- [ ] Confirm that users can inspect a real imported spectrum without changing
      its underlying data.
- [ ] Record which behaviors were verified automatically and manually.

---



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