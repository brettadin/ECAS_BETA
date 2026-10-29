# Feedback acceptance reconciliation — 2026-10-28

Latest follow-through: `verification_final_workflow_20261028/RESULTS.md` records
successful live initial/repeated CO2 download-to-display and native-unit Comparisons
desktop inspection with preserved choices/view tabs. Historical display symptom is
not reproduced on the current local build. User confirms batches 9–11 require no
Argon fixes. Core supported workflow is ready for the bounded Chunk 6 entry task
in `CHUNK_6_ENTRY_SCOPE.md`; later human plot UX and smaller-window acceptance
remain open and no quantitative scientific operation is enabled.

Latest human review: issue #4 explicitly reviews `49e3b96`, confirms the main
desktop workflows and gives the go-ahead for continued development with known
issues. See `ISSUE_4_DESKTOP_FEEDBACK_20261028.md` for dispositions and next work.
The earlier open-checklist wording below is historical. Do not infer unreported
CSV synchronization/restart checks from the item-5 response about directories.
Human review is received with follow-ups; scientific validation remains deferred.

All six approved feedback implementation steps have a local disposition. All
eight Argon feedback batches returned zero findings in their stated scopes.
Reports are in review_feedback_20261028, review_selection_20261028 and
review_workspace_20261028, plus review_desktop_20261028 for the readability fix.
Receipt of a report is distinct from human desktop
acceptance or empirical scientific validation. No chunk completion is claimed.

| Workflow item | Current disposition |
| --- | --- |
| Project metadata labels and source-attributed tooltips | Implemented; Batch 1 zero findings. |
| Dedicated Molecular References and separate Comparisons pages | Implemented; Batch 2 zero findings. |
| 55 Cancri e investigation and clearer inventory status | Investigated; Batch 3 zero findings. Four Transmission and 19 Eclipse records captured. Historical zero-result cause remains unknown; alias-first pipeline was not newly introduced. |
| CO2, H2O and CH4 retrieval, provenance and cache identities | Implemented; Batches 4–5 zero findings. Prior live retrieval/offline evidence exists for bounded samples, not all settings. |
| Independent observation/reference selection and separate inspection | Implemented; Batch 6 zero findings. Session observation choices, validated cached references, explicit blocked comparison explanations. |
| Overview and Settings | Implemented; Batch 7 zero findings for its four listed files. Page-entry summaries; session CSV choice; read-only paths. |
| Comparison desktop readability correction | Implemented and visually rechecked; Batch 8 zero findings. Content-sized columns, selectable plain-text labels and two-line observation hash with exact tooltip. |

## Open normal-desktop acceptance

Agent desktop verification has since covered a bounded subset at 1200 × 800:
observation import/plot, comparison selection of captured water and methane,
Settings-to-Spectral Data schema synchronization, page-entry summary and session
reset after restart. A reference-header/hash readability issue was found, fixed,
and visually rechecked. See `verification_desktop_20261028/RESULTS.md` for exact
scope and remaining unperformed checks. This is not human acceptance; the
checklist below remains open. Batch 8 subsequently reviewed the patch with zero
findings; its report and hash verification are in review_desktop_20261028.

This is a proposed checklist, not a claim that the user has performed these checks.
Use the current local application and temporary research projects as appropriate:

1. Check readability/scrolling at a normal desktop window size, including long
   project labels, source-attributed tooltips and Overview/Settings paths.
2. Load or reopen an observation, inspect its plot/table, and confirm it remains
   intact when switching among all six pages and using Overview shortcuts.
3. Inspect/reopen an existing supported cached molecular product, checking the
   displayed molecule/isotope/dataset, conditions, units, citations and source hash.
4. In Comparisons, add observation choices and independently choose a cached
   reference. Check the separate original-value tables and blocked comparison
   explanation; switching selections must preserve the two original workspaces.
5. Change the CSV schema in Settings and Spectral Data; verify both selectors
   agree. Confirm existing loaded data stays unchanged and the choice resets to
   the generic default after restarting. Session comparison choices also reset;
   observations saved in Projects remain available for reopening.

Report actual outcomes before closing this acceptance item. Existing earlier
manual confirmations do not automatically accept these later screens. Repeating
live network downloads is not required simply to record this review receipt.

## Scientific and production boundaries

Current ExoMol products are calculated absorption cross sections, not transit-depth
predictions or detections. General production eligibility, unit/grid conversion,
response alignment, physical forward modelling, overlays/residuals, scoring and
persistent pairings remain unimplemented. The research contract/adapter remain
outside production. These are future scientific workflow tasks, not defects
reported by the seven reviews. Real-data scientific validation is deferred by the
user; no assumptions or declarations may be silently supplied to enable analysis.

Latest executed verification: focused 121 passed (5.82 s); full 571 passed,
1 skipped (11.15 s), exit 0. The skip is Windows directory-symlink privileges.
Evidence is preserved under verification_workspace_20261028. No rerun was needed
for receipt/reconciliation documentation alone. Working changes remain local and
uncommitted; no commit/push/merge/deployment is implied by review approval.
