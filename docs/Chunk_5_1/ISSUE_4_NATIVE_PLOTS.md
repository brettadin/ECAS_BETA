# Issue #4 — native-unit graphical inspection

Local follow-on to ISSUE_4_FIRST_FIXES.md; both increments need independent
review and targeted desktop confirmation. Nothing has been committed/pushed.

Molecular References now displays a native-coordinate reference plot after download
or cached reopening. Plot and Data table tabs share the same inspection area.
Catalogue results explicitly label supported download mappings versus catalogue-only
entries with unverified retrieval. The Download tooltip explains the exact three
supported mappings and that an unsupported request is not evidence of absent data.
No new provider mapping, network protocol or catalogue omission was introduced.

Comparisons has separate observation/reference Plot and Data table tabs. The
observation uses the existing SpectraPlot on canonical imported columns, preserving
unknown unit labels and its existing exclusion of invalid numeric coordinate pairs.
The reference uses a new ReferencePlot on the exact validated wavenumber/cross-section
samples, linear axes, with no unit conversion, resampling, normalization or log floor.
Straight segments connect samples for visual inspection, not additional measurements.
Zero-valued reference samples remain zero. All original rows remain in Data table.

The two plots have independent axes, scales and physical meanings. Introductory
text states that their horizontal positions do not identify matching wavelengths.
Raw cross sections and transit depth are not overlaid; the physical-model block
and no-score/no-detection boundary remain. Reference invalidation clears both plot
and table. Failed replacement downloads retain the existing reference as before.
Navigation preserves view-tab choices and independent data selection. No stored
data, hash, schema or project attachment is modified by plotting.

## Verification

Commands: `.venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_plots_20261028/run_checks.py focused`
and the same command with `full`. Exact logs, subprocess commands, environment
key names and versions are saved beside the runner.
Results: **126 passed**, 6.95 s focused; **576 passed, 1 skipped**, 10.91 s full;
both exit 0. Existing skip: Windows directory-symlink privileges. Two new cases
cover availability labels and independently retained native plots/units/view tabs.
Existing repeated-download and corrupt/deleted-cache cases now check the plot
data and clearing as well. Tests use actual offscreen widgets and original captures;
no live service call or empirical scientific comparison is claimed.

Normal Windows visual acceptance of these new plots is still pending; the earlier
desktop screenshots predate them. In particular, inspect readability at smaller
window sizes and long metadata labels. No claim of a completed UX acceptance pass.
The manual-reopen download symptom is still not reproduced by offline callbacks.
Scientific validation remains deferred. Next: independent review and desktop
confirmation, then investigate any reproducible live completion issue.
