# *CHATGPT PROMPT* #
<br>
<br>

## Review verdict: Approved with one condition

The corrected plan resolves the selector lifecycle problem. The schema selector will persist in the spectral page, and `_import_csv()` will read its current selection when importing a file.

The implementation scope is appropriately narrow:

- `ecas/ui/main_window.py`: Add the persistent schema selector and pass the selected schema to the importer.
- Tests: Verify that both GUI selections pass the correct argument, if feasible with the existing test infrastructure.
- Documentation: Record actual implementation and verification results after completion.
- `ecas/ingestion/csv_importer.py`: No changes unless implementation reveals a specific defect.

One condition: Cline must inspect the existing layout and GUI test infrastructure before editing. The proposed test snippets are illustrative, not complete tests; the mocked import result and file-dialog interaction must match the actual application.

## Next step: ACT mode

Send Cline the following prompt.

## ACT — Chunk 4, Part 2: Implement GUI CSV Schema Selection

**Mode: ACT. Implement only the approved scope below.**

### Objective

Fix the GUI import workflow so users can explicitly select either Generic/Unknown CSV handling or the WASP-39 b Archive schema, using the existing importer API.

### 1. Inspect before editing

Read the current implementations of:

- `ecas/ui/main_window.py`
- `ecas/ingestion/csv_importer.py`
- Relevant existing GUI and archive-importer tests
- The confirmed active Chunk 4 Part 2 plan and relevant authoritative documentation

Verify the existing widget layout, import-button wiring, test conventions, and documentation paths. Preserve unrelated local changes.

### 2. Implement the GUI change

In `_build_spectral_page()`:

- Add a descriptive `CSV schema:` label and a persistent `QComboBox` alongside the existing CSV import controls.
- Store the selector as `self.spectrum_schema_selector`.
- Add `Generic / Unknown` and `WASP-39 b Archive` options, with Generic/Unknown selected by default.
- Use the existing layout structure correctly; do not assume fixed widget indices.

In `_import_csv()`:

- Preserve the existing file-dialog cancellation behavior.
- Immediately before calling `import_spectrum_csv()`, read the selector's current index.
- Map index 0 to `archive_schema=None`.
- Map index 1 to `archive_schema=WASP39B_SCHEMA`.
- Import `WASP39B_SCHEMA` from the existing importer module.
- Keep existing error handling, import-result handling, and unrelated UI behavior unchanged.

Do not add `ARCHIVE_SCHEMA_OPTIONS`, filename detection, redundant state variables, or unnecessary signal handlers. Do not modify importer behavior unless a demonstrated defect blocks this integration; report such a blocker before expanding scope.

### 3. Tests and verification

Add a focused GUI regression test if compatible with the existing test infrastructure. Mock the file dialog and importer as appropriate, and verify that:

- Generic/Unknown passes `archive_schema=None`.
- WASP-39 b Archive passes `archive_schema=WASP39B_SCHEMA`.
- Cancelling the file dialog does not invoke the importer.

Use the actual existing test directories and conventions; do not assume `tests/gui_tests/` exists.

Run:

1. The new or updated GUI test.
2. The existing archive CSV importer tests.
3. Relevant main-window tests.
4. The broader test suite if the focused tests pass and execution is practical.

Use the repository's actual test command and environment. Report the exact commands and results. Do not claim tests passed unless they were executed successfully.

If automated GUI testing is genuinely impractical, explain why and provide explicit manual verification steps instead of adding a nonfunctional test.

### 4. Documentation

After implementation and verification:

- Update the confirmed active Chunk 4 Part 2 planning record with actual changes, tests, results, and any limitations.
- Update `docs/brains/PROJECT_STATE.md` only as warranted by the verified change.
- Update `docs/brains/DECISIONS.md` only if a new architectural decision was made.
- Preserve historical Part 1 plans and avoid duplicate planning records.

Do not document unverified results as completed.

### 5. Final report

Report:

- Files changed and the purpose of each change.
- Exact schema-selection behavior.
- Tests executed, commands, and actual results.
- Any manual checks still required.
- Documentation updated.
- Any unresolved issues.

Inspect the final diff for unintended changes. Stop when this scope is complete; do not begin another Chunk 4 task.

Once Cline returns its implementation report, send it here for review before we move to the next task.

<br>
<br>
<br>


# *CLINE RESPONSE* #

<br>
<br>

