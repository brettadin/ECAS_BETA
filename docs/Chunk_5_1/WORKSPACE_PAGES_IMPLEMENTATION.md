# Overview and Settings — 2026-10-28

Approved feedback step 6 is implemented locally in `ecas/ui/workspace_pages.py`
and connected through `ecas/ui/main_window.py`. The user accepted Argon's first
six code reviews and authorized pipeline continuation. This new increment needs
its own independent review; human normal-desktop acceptance remains open.

## Implemented behavior

Overview explains the implemented import/project/reference/inspection workflow,
provides navigation shortcuts and summarizes in-memory state whenever opened.
It shows the current observation filename/row count, the reference displayed in
Molecular References, and the number of session observation choices and selection
presence in Comparisons. These are distinct states, not an inventory of saved
projects or cached products. A summary is a page-entry snapshot, not a continuously
updating activity monitor. Labels use plain text, including source filenames.

Settings exposes the existing CSV schema choice, synchronized in both directions
with Spectral Data. Both CSV entry points use the same established selector.
Changing the setting applies to subsequent CSV imports; it does not reinterpret
loaded/saved values, affect .tbl dispatch or persist after closing the application.
The supported generic/archive choices and their default remain unchanged.

The page displays selectable read-only absolute paths for the actual configured
project root, NASA cache, ExoMol catalogue cache and ExoMol reference cache. It
uses existing service/browser attributes, including constructor overrides. It
does not scan, move, delete, create or change those locations. Text explains
storage roles, session-only comparison observations, public online actions,
offline reopening and cancellation. No new credential or network controls exist.

Both pages are scrollable at smaller window sizes. Navigation indices and all
existing long-lived workspaces remain unchanged. Shortcuts only navigate; they
do not initiate searches/imports/downloads, change selections or cancel requests.
No scientific analysis, production eligibility, persistent settings format,
storage migration, new dependency or source/cache mutation is introduced.

## Verification

- `.venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_workspace_20261028/run_checks.py focused`
  — **121 passed**, 5.82 s, exit 0.
- `.venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_workspace_20261028/run_checks.py full`
  — **571 passed, 1 skipped**, 11.15 s, exit 0.
- `git -c core.safecrlf=false diff --check` — exit 0.

Logs, exact subprocess commands, minimal environment key names and dependency
versions are in `verification_workspace_20261028/`. Existing skip: Windows
directory-symlink privileges. Five added integration cases verify navigation and
independent data preservation after source removal; both CSV dispatch entry
points; configured paths and no storage scanning/writing on page entry; .tbl
fidelity and session-only preference reset. They use real offscreen widgets,
temporary project/reference roots and existing captured fixtures. No live request,
paid service, credential, commit or push was used. Automated checks do not replace
normal-desktop inspection or establish scientific validity.

Review prompt and manifest: `review_workspace_20261028/07-workspace-pages.txt`
and `manifest.json`. Next: independent review and desktop acceptance of these
pages, then reconcile remaining Chunk 5.1 acceptance items against the roadmap.
Real-data scientific validation stays deferred; no chunk completion is claimed.
