# Agent desktop verification — 2026-10-28

Method: normal Windows Qt platform, 1200 × 800 client-area window (captured outer
window 1202 × 832), controlled with the computer-use skill's sky API. This is
agent verification, not a claim of human acceptance. Screenshots were displayed
and inspected in the continuation chat; no separate screenshot files are claimed.

`launch.py` starts ECAS with a minimal environment, isolated project/reference
roots under `.venv/checks/desktop-feedback`, and the existing captured CO2, H2O
and CH4 11-point products (500 K, 4000–4010 cm^-1, spacing 1). It validates these
raw bytes through the existing parser/cache before inspection. No fresh download
or current-provider availability check is implied. NASA's configured cache remains
the application's default path; no cache action/request was triggered there.
No research project was opened or changed. The test windows were closed afterward.

## Observed results

- Overview rendered readable text and all workflow shortcuts at this window size.
  Its observation shortcut opened Spectral Data. After inspection, Overview showed
  the 331-row observation and independent comparison selection while correctly
  reporting no reference loaded in the separate Molecular References display.
- Imported the original `data/NASA/2026-10-27/feinstein-2023.tbl` via the native
  file dialog: 331 rows, plot displayed with micron/% labels and numeric table.
  These labels are importer-provided; no new scientific interpretation was made.
- Comparisons accepted the observation snapshot and discovered three valid seeded
  references, zero invalid. Selected water/POKAZATEL in the first session and
  methane/MM after restart. The separate original-value tables and physical-model
  blocking explanation were visible. No comparison score or detection was produced.
- Settings paths were readable. Changing its CSV choice by keyboard to WASP-39 b
  Archive was reflected in Spectral Data; the existing observation plot and 331-row
  status remained intact after navigation. This did not reinterpret the .tbl file.
- After closing/relaunching, Overview showed zero session choices/no loaded data
  and Spectral Data showed Generic / Unknown. Re-import and cache reopening worked.

## Desktop issue corrected

Initial inspection exposed clipped reference column headings and crowded inline
observation hash text. `comparison_browser.py` now resizes table columns to their
contents. The observation hash is displayed in two 32-character lines; an exact,
unbroken hash and source path remain in a tooltip. Plain-text labels
are mouse-selectable. No source values, hashes, identities or stored bytes change.
The existing provenance regression checks both the exact tooltip hash and its
two-line display. Final desktop inspection of the methane reference showed both
complete headings and both observation hash lines. Observation tables still scroll
horizontally to expose their many source columns, as intended.

Commands and actual final results:

- `.venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_desktop_20261028/run_checks.py focused`
  — 121 passed, 5.54 s, exit 0.
- `.venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_desktop_20261028/run_checks.py full`
  — 571 passed, 1 skipped, 10.56 s, exit 0.

Exact commands/versions/environment keys are recorded alongside these results.
The skip remains Windows directory-symlink privileges. No new dependency, paid
reviewer, credential, scientific analysis, commit or push was used.

## Remaining acceptance

Human acceptance is still open. Long project-label/tooltips, project save/reopen
through the desktop UI, Molecular References-page offline reopening/citation
tooltips, and smaller-window scrolling were not checked in this desktop pass.
Existing automated coverage is not relabelled as manual verification. Provider
captures are historical 2026-10-28 protocol evidence, not live scientific validation.
Real-data scientific validation remains deferred. This readability patch needs its
own independent review; earlier Argon reports apply to their original snapshots.
