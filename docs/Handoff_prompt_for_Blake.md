# ECAS — Development Handoff and Agent Instructions

## 1. Project Identity

You are contributing to **ECAS — Exoplanetary Characterization & Astrochemistry Suite**, a scientific desktop application for working with exoplanetary spectra and related astrochemical data.

Repository: https://github.com/brettadin/ECAS_BETA

The repository will be available in your working environment as `ECAS_BETA/`. **Do not assume any particular absolute filesystem path.** Begin by locating the repository root and verifying the current Git branch and working-tree state.

Your task is to continue developing the actual application. Focus on useful code additions, correctness, integration, testing, and resolving implementation defects. Do not spend the entire session rewriting documentation or repeating investigations already completed.

## 2. How Development Is Expected to Work

Follow a controlled, incremental workflow.

**PLAN → REVIEW → ACT → VERIFY → DOCUMENT**

- **PLAN:** Inspect the relevant code and tests, identify existing behavior, dependencies, affected files, risks, and a small implementation scope.
- **REVIEW:** Present a concrete plan with acceptance criteria. Wait for explicit approval before implementing.
- **ACT:** Implement only the approved scope. Avoid unrelated refactoring and speculative feature additions.
- **VERIFY:** Run relevant tests, inspect the diff, and report actual results.
- **DOCUMENT:** Update the appropriate project records to reflect what was actually implemented, tested, deferred, or decided.

If the environment supports distinct planning and execution modes, use them accordingly. If it does not, maintain the same separation in your responses.

Work in small, independently reviewable increments. Prefer one coherent change at a time over a broad rewrite.

Do not claim that code, tests, documentation, or Git operations succeeded unless you have evidence that they did.

## 3. Start by Establishing the Actual Repository State

Before proposing changes:

1. Confirm the repository root.
2. Inspect `git status --short`, the current branch, and recent commits.
3. Identify staged, modified, untracked, and deleted files.
4. Read the current project instructions, especially `AGENTS.md` if present, and any applicable repository-specific agent instructions.
5. Locate and read the current versions of:
   - `docs/brains/PROJECT_STATE.md`
   - `docs/brains/DECISIONS.md`
   - `docs/ECAS.md`
   - Relevant architecture documentation under `docs/architecture/`
   - Relevant Chunk 4 planning and implementation records under `docs/Chunk_4/`
6. Inspect the current source code and tests before relying on any earlier description of their contents.
7. Check the current branch history and repository status before deciding what work remains.

The repository contents and current implementation are authoritative. Historical planning notes are useful context, but they do not override the actual code, tests, or later documented decisions.

**Preserve existing work.** Do not reset, overwrite, discard, or silently exclude pre-existing changes. If the working tree contains changes you did not make, identify them and account for them before acting.

Avoid spending excessive time exploring the entire repository. Follow the code paths relevant to the next task.

## 4. Current Development Context: Chunk 4

Recent work has focused on improving CSV spectrum ingestion and making the GUI support an explicit schema choice for a WASP-39 b archive CSV format.

The known intended behavior is:

- The spectral GUI offers a `Generic / Unknown` schema selection as the default.
- It also offers a `WASP-39 b Archive` selection.
- Generic selection uses no archive-specific schema.
- Archive selection explicitly passes the existing `WASP39B_SCHEMA` mapping.
- The archive mapping uses `centralwavelng` for wavelength and `pl_trandep` for signal.
- File-dialog cancellation should return without attempting an import.
- Archive-specific handling must not silently become filename-based auto-detection.
- Generic CSV import behavior should remain compatible with its existing contract.

Relevant code locations reported during previous work include:

- `ecas/ingestion/csv_importer.py`
- `ecas/ui/main_window.py`
- `ecas/visualization/spectra_plot.py`

Relevant test locations reported during previous work include:

- `tests/test_csv_importer.py`
- `tests/test_archive_csv_importer.py`
- `tests/test_main_window.py`

Verify all these paths and their actual contents before making assumptions. They are starting points, not a guarantee that the repository has not changed.

### Known outstanding work

Previous review identified the following issues that still require confirmation against the current repository:

1. **GUI schema-selector regression tests:** Automated tests for generic selection, archive selection, and file-dialog cancellation were reported as missing. Inspect the current suite and add focused tests if still absent.
2. **Full test-suite evidence:** A report claimed that 105 tests passed, but the captured command output and exit code were not available in that report. Run the relevant tests in the current environment and record the actual results.
3. **Manual integration test:** An untracked `test_spectra_schema.py` was reported as using `SpectraPlot.load_spectrum(..., schema=WASP39B_SCHEMA)`. Determine whether it is useful, reproducible, and should be integrated into the established test suite.
4. **CSV fixtures:** `generic_test.csv` and `wasp39b_test.csv` were reported as untracked files. Inspect their contents, provenance, intended purpose, and current Git status before deciding whether they should become maintained test fixtures.
5. **Generic alias removal:** The `"flux": "flux_error"` mapping was removed from `COLUMN_ALIASES`. Verify the current alias behavior and tests. Preserve only changes supported by the intended import contract; do not restore or remove aliases without examining their effects.
6. **Documentation changes:** Several architecture documents were reported to have substantial diffs. Do not assume these are correct or incorrect based on diff size alone. Review them when relevant, and do not let documentation cleanup displace higher-priority application work.
7. **Git handoff:** Check the actual latest commit and branch state. Do not assume the previous changes were committed or pushed. If the working tree is dirty, preserve and report existing work.

These items are a handoff checklist, not a mandate to fix everything in one session. Prioritize defects that affect application correctness, data integrity, or the ability to continue development safely.

## 5. Scientific Data Integrity Requirements

ECAS is a scientific application. Correctness and transparent handling of data are more important than making unsupported assumptions to achieve a successful import.

When adding or modifying ingestion and analysis functionality:

- Preserve original source information and provenance where the application supports it.
- Keep archive-specific schemas explicit and separate from generic parsing rules.
- Do not silently infer units, physical meaning, or metadata that are not present or supported by the input.
- Do not silently convert malformed or ambiguous scientific values into apparently valid measurements.
- Distinguish missing values, invalid values, unsupported formats, and valid zero-valued measurements.
- Make import failures and unsupported formats understandable to users.
- Keep wavelength, signal, uncertainty, and metadata semantics consistent with the actual code and documented schema.
- Avoid implying that support for one archive CSV layout means universal support for online archives, arbitrary CSV files, or TXT/FTIR/UV-Vis formats.
- Where a format is not supported, report the limitation and identify the smallest justified next step.

Any scientific transformation, schema expansion, or interpretation that changes the meaning of data should be explicitly justified, tested, and documented.

## 6. Implementation and Testing Standards

For every proposed code change:

1. Identify the affected modules and existing contracts.
2. Inspect relevant call sites and tests.
3. Prefer the smallest maintainable implementation that satisfies the requirement.
4. Follow the existing project style and dependencies.
5. Add or update automated tests for new behavior and regressions.
6. Test error paths and cancellation behavior where relevant.
7. Run focused tests first, then broader tests when practical.
8. Inspect the final diff for unintended changes.

Do not introduce a new abstraction, dependency, schema framework, or test framework when a small change using existing project patterns will suffice.

Do not weaken or delete tests simply to make a suite pass. If an existing test is invalid, explain why and replace it with a test that checks the intended behavior.

When tests cannot be run, report exactly why. Do not describe an unexecuted test as passing.

Record the exact commands and meaningful results, including exit codes when available. Distinguish between:

- Automated tests that were actually executed.
- Manual checks that were actually performed.
- Code paths inspected but not executed.
- Tests that could not run.
- Remaining unverified behavior.

## 7. Documentation and Project Memory

Documentation is part of the development process, but it must reflect the real implementation.

Use the existing documentation structure and conventions. Do not create competing project-state files or duplicate planning histories without a clear reason.

### `docs/brains/PROJECT_STATE.md`

Update when there is a meaningful change to the actual project state, such as:

- A feature being implemented and verified.
- A module or workflow becoming available.
- A known limitation being resolved or newly identified.
- A significant task being completed or deferred.

Keep it concise and factual. Distinguish verified implementation from planned functionality.

### `docs/brains/DECISIONS.md`

Record meaningful architectural or scientific design decisions, particularly those affecting:

- Data models and persistence.
- Schema design and ingestion behavior.
- Scientific data interpretation.
- Module boundaries and public interfaces.
- Backward compatibility or migration requirements.

Do not add a new decision entry for every minor code change. Record the decision and its rationale when it changes or clarifies an actual project convention.

### `docs/ECAS.md`

Treat this as the master project blueprint and documentation map. Update it when a substantial change alters the project's documented capabilities, direction, or document organization. Do not update it mechanically for every small bug fix.

### `docs/architecture/`

Update the relevant architecture document when a code change materially changes the documented architecture, data flow, module responsibilities, data models, or validation strategy.

Do not make large formatting-only rewrites as part of an unrelated implementation task. Keep architectural descriptions clear about the difference between:

- Current, verified behavior.
- Approved design decisions.
- Proposed future capabilities.
- Unresolved questions.

### `docs/Chunk_4/`

Maintain the existing Chunk 4 planning and implementation history. Confirm the active planning record before editing it. Append or update the correct record according to its existing convention; avoid creating a new version merely because an old record is inconvenient to edit.

For each meaningful implementation increment, document:

- Objective and scope.
- Actual files changed.
- Important implementation decisions.
- Tests executed and their results.
- Known limitations and follow-up work.
- Any deviation from the approved plan.

Do not retrospectively claim that a planned task was completed unless the implementation and verification support that claim.

### Documentation discipline

Documentation should be accurate, concise, and useful to the next developer. Avoid copying entire agent conversations into core architecture documents. Preserve detailed task history in the appropriate planning records and keep project-state documents readable.

## 8. Prioritization and Scope Control

Work in this order:

1. Protect existing changes and establish the current state.
2. Fix critical defects affecting application correctness or scientific data integrity.
3. Verify and test the current workflow.
4. Complete small, well-defined code additions that advance the application.
5. Update documentation relevant to those changes.
6. Record non-blocking improvements as follow-up tasks.

Do not block all development on cosmetic documentation cleanup, optional refactoring, or a full audit of every module.

If several issues are discovered, propose a short prioritized list and recommend the smallest useful next increment. Do not implement multiple independent features in one unreviewed burst.

When a task is substantially larger than expected, stop and present a revised plan rather than expanding scope silently.

## 9. Git and Collaboration Rules

This repository is shared with other developers.

- Inspect `git status` and the current branch before acting.
- Preserve changes made by other developers or agents.
- Do not force-push.
- Do not rewrite shared commit history.
- Do not commit generated files, local configuration, caches, virtual environments, or temporary test artifacts without an explicit project reason.
- Do not include unrelated modifications in a feature commit.
- Keep commits focused and use descriptive messages.
- Separate implementation and substantial documentation changes into different commits when practical.
- Do not stage or commit files unless the user has authorized that action.
- Do not push unless explicitly authorized.
- If a push is rejected, inspect the reason and coordinate before proceeding.

At the end of a task, report the working-tree state and any files that remain uncommitted. Never imply that work is on GitHub merely because it exists in a local checkout.

## 10. Required Response Format

For each development increment, provide a concise report with these sections:

### A. Assessment
What was inspected, what was found, and which facts were verified.

### B. Plan
The intended changes, exact file paths, acceptance criteria, and risks.

### C. Implementation
What changed and why. Identify any deviation from the approved plan.

### D. Verification
Exact commands executed, test counts/results, and any failures or limitations. Clearly distinguish automated tests from manual checks.

### E. Documentation
Which project documents were updated and why, or why no documentation update was necessary.

### F. Remaining Work
Known defects, missing tests, unsupported formats, deferred improvements, and the recommended next step.

### G. Git Status
Current branch, commit information where relevant, and modified/untracked files. State explicitly whether anything was committed or pushed.

Be direct and factual. Avoid inflated claims such as "fully functional," "production ready," or "all validated" unless the evidence justifies them.

## 11. First Task for This Agent

Do not begin by proposing a major new feature or rewriting all the documentation.

Start with a **brief repository-state and handoff assessment**:

1. Confirm the branch, working tree, recent commits, and whether the latest Chunk 4 work is present.
2. Read the applicable project instructions and current project-state/decision documents.
3. Inspect the current CSV ingestion and GUI schema-selection implementation.
4. Check the status of the existing tests and the outstanding items listed above.
5. Identify any critical correctness issues that should be fixed before extending the application.
6. Recommend the next one or two small, high-value code tasks.

Do not change files during this first assessment. Return the findings and wait for approval before implementation.

The objective is to continue building ECAS reliably, with controlled changes, verified behavior, scientific integrity, and documentation that accurately records the project's evolution.