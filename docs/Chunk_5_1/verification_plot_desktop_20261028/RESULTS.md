# Native plot desktop follow-up — 2026-10-28

Agent inspection used the normal Windows Qt platform and the existing isolated
desktop launcher (`verification_desktop_20261028/launch.py`), not the user's
project/reference storage. Public CO2/H2O/CH4 captures from 2026-10-28 seed the
isolated reference cache. No new provider request was made. Windows were closed
afterward. Screenshots were displayed/inspected in chat; no image archive claimed.

## Evidence and correction

At the normal 1200 × 800 client size (1202 × 832 outer screenshot), cached CO2
reopening displayed the original 11-point curve over 4000–4010 cm^-1. The first
render used automatic axis scaling: ticks appeared around 0–1, while a long
vertical label crowded the multiplier annotation. The plotting library's local
AxisItem source confirms that automatic multipliers can be appended to the label.
This is a readability/scientific-communication risk, not changed numerical data.

ReferencePlot now disables automatic SI prefixes on its vertical axis and labels
it `σ (cm²/molecule)`. Tick values explicitly show the magnitude, e.g. `1e-24`
and `5e-25`, without requiring a separate multiplier to be readable. The stored
sample coordinates, linear axes, zero values and reference cache remain unchanged.
The same ReferencePlot is used in both reference inspection workspaces.

Request settings consumed much of the reference pane's height. A manual
Hide/Show request settings button now collapses conditions, parameter controls
and the Download action as a group. They are visible by default. Cached reopening,
reference status and Plot/Data table tabs remain visible when settings are hidden.
No automatic collapse, parameter reset or request cancellation is introduced.

After restarting with these changes, CO2 cache reopening worked with settings
hidden; the larger curve, explicit scientific tick values, compact unit label and
native wavenumber axis were readable. Switching to Data table showed the original
numbers (for example 4000 with 7.193624117e-25). Collapse/expand preservation of
the product and all four request values is also checked in the widget regression.

## Verification

Commands from repository root:

- `.venv/Scripts/python.exe -I -B docs/Chunk_5_1/verification_plot_desktop_20261028/run_checks.py focused`
  — **126 passed**, 8.25 s, exit 0.
- Same command with `full` — **576 passed, 1 skipped**, 13.47 s, exit 0.

The skip remains Windows directory-symlink privileges. Logs, exact subprocess
commands and versions are saved alongside this report. The native-plot test now
checks scientific tick strings and the disabled automatic prefix setting.

This desktop pass did not reload an observation into the new Comparisons plots,
exercise live download completion, check project save/reopen or verify smaller
window sizes. A resize drag did not change the captured dimensions, so no smaller
size acceptance is claimed. Comparisons data fidelity/state/clearing remain
covered by the preceding offscreen tests, not relabelled as desktop observations.
Human acceptance and scientific validation remain separate; the latter is deferred.

New correction needs independent review (batch 11). Batches 9/10 are earlier local
snapshots, also awaiting supplied reviewer reports. Original prompts/manifests are
preserved. No commit, push, new dependency, paid reviewer or scientific conversion.
