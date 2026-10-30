# Laboratory identification checkpoint — 2026-10-29

Branch: `codex/laboratory-identification-checkpoint-20261029`.
Local implementation base: `e0ea472`. Library source: remote revision
`a84c9d3ccf5e5dd230716feb9e972b60e0c454d9`, verified against Git blob hashes.

Includes real-library discovery/import, recovered v1 optical-depth BVLS and
refitted drop-one scores, separate exploratory signed UV measured-template fits,
IR/UV selection, consistent colours, result tables, independent observation
identities, duplicate handling, metadata persistence and reproducible exports.

Verification: full offscreen suite with `pytest -W error`: 688 passed, 22 skipped,
zero failures/warnings. Skips: 21 opt-in network checks and unavailable directory
symlink creation. Subsequent project-identity follow-up: 26 affected tests passed.
Offscreen layout inspected; normal-desktop user acceptance remains outstanding.

Scores are conditional statistics, not calibrated molecular detections. Planetary
transit depth remains in the physical atmospheric workflow. See
`architecture/LABORATORY_IDENTIFICATION.md` for method and limitations.

The pre-existing blank-line edit to `HANDOFF_TO_OPENAI.md` is excluded.
GitHub master was already at the library revision above before publication;
this checkpoint is uploaded separately without rewriting or merging master.
