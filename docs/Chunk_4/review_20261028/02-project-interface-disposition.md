# Batch 2 interface review disposition — 2026-10-28

Argon's supplied review covered project_browser.py, main_window.py and project UI
tests. This is implementation triage, not independent acceptance of the fixes.
Original review packages and their manifests remain unchanged.

1. **Double-resolution blocks links: not reproduced; premise contradicted by
   helper.** source_link accepts absolute HTTP(S) URLs without credentials and
   returns them unchanged. The second call validates rather than expands that URL.
   Keep validation. Existing tests verify absolute citations and actual table
   double-click signals reaching the mocked QDesktopServices.openUrl with the
   resolved URL, including browser-launch failure reporting. The review did not
   have source_links.py; its stated assumption is false for this implementation.
2. **Unwrapped file I/O errors: conditional concern not present in supported
   importers.** Both CSV paths catch OSError and wrap SpectrumImportError;
   import_manager delegates to them. NASA table reads also wrap OSError.
   Eight new actual-window tests inject PermissionError/FileNotFoundError at
   Path.open for CSV/table and dialog/path entry points. All produce warnings and
   clear the display without leaking exceptions. No exception-contract change.
   This simulates read failures; it does not claim every Excel file is locked.
3. **Missing selected record: accepted and fixed.** Revalidation now looks up
   the stable record ID with a default and explicitly reports that the record no
   longer exists and the list should be refreshed. A real SQLite deletion between
   listing and opening verifies the error and preservation of the prior display.
4. **Unplottable record feedback: accepted and fixed.** If display returns without
   loading the selected record, the Projects status now reports no valid plottable
   measurements. A real legacy row containing only text exercises the actual plot
   rejection path: Projects stays selected, the error is visible there, stale
   spectrum/table/attachment state is cleared and Add is disabled.

Verification used the existing isolated offline driver:

- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py project-ui-review-focused`
  — 107 passed (3.40 s).
- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py project-ui-review-full`
  — 355 passed, 1 skipped (7.23 s).

The skip is the existing Windows directory-symlink privilege limitation.
Exact commands and logs: ../verification_20261028/project-ui-review-*.
Source changes: ecas/ui/project_browser.py, ecas/ui/main_window.py;
regressions: tests/test_projects_ui.py. No dependencies, downloads, credentials,
model calls, commits or pushes. Follow-up review and human desktop acceptance
remain open. Follow-up snapshot: 02-project-interface-follow-up.txt, including
the previously omitted source-link helper and importer exception context.

## Independent follow-up received — 2026-10-28

User supplied Argon's re-review of the interface, source-link helpers/tests and
importer context: findings were empty. Argon confirmed the missing-record and
unplottable-spectrum corrections and validated the absolute-link and wrapped-I/O
triage decisions. Batch 2 correction review is complete for the supplied snapshot.
Argon reported no limitations in that supplied context; this does not substitute
for normal-desktop human acceptance or establish guarantees beyond the review.
No code changes or test reruns were needed. Latest overall suite remains 357
passed, one skipped. Batch 4 correction review and human acceptance remain pending.
