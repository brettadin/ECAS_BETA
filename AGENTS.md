The main change is to make GitHub a record of progress rather than a gate on progress. Agents should work locally, verify changes, and maintain project records without needing to commit or push after every increment. The user can push manually when ready.

Here is the revised `agents.md`, keeping the same foundations and roughly the same length.

# ECAS — AI Agent Instructions

## 1. Project Identity and Goals

**ECAS — Exoplanetary Characterization & Astrochemistry Suite**

Repository: [https://github.com/brettadin/ECAS_BETA](https://github.com/brettadin/ECAS_BETA)

ECAS is a Python scientific desktop application for exoplanetary spectroscopy and atmospheric characterization.

The goal is to build a functional, reliable, maintainable application that supports scientifically responsible analysis. Prioritize implementation, correctness, integration, and verified progress over excessive planning or documentation.

## 2. Autonomous Development

Agents are expected to make progress, not merely investigate and propose plans.

Unless explicitly restricted by the user or applicable instructions, agents may inspect and modify code, tests, configuration, dependencies, application functionality, architecture, project structure, and documentation.

Agents may make routine technical decisions, fix defects, add features, reorganize files when justified, and create or update chunk-specific records and folders.

Work in small, coherent increments. Investigate enough to understand the task, then implement, verify, document, and continue. Do not repeatedly restart planning or stop at a proposal when productive work can proceed.

Preserve useful existing work and avoid unnecessary rewrites, speculative changes, duplicate implementations, and unrelated cleanup.

## 3. Agent Roles and Collaboration

Planning, implementation, and review are complementary responsibilities. They may be performed by separate agents or combined when appropriate.

**Planning and review agents** identify priorities, establish objectives and acceptance criteria, review actual changes and verification evidence, maintain relevant progress records, and identify the next useful task.

**Implementation agents** inspect the repository, adapt plans to actual conditions, implement changes, add or update tests, document results, and address review feedback.

These roles do not restrict either agent to particular files. Both may edit code and relevant project records, correct inaccurate documentation, and identify additional improvements.

Agents should share findings, avoid duplicated effort, preserve each other's changes, and resolve disagreements using code, tests, documentation, and technical evidence. Seek human input when a consequential decision cannot reasonably be resolved from available evidence.

Routine implementation and review do not require approval at every intermediate step.

## 4. Project Context and Sources

Before starting, inspect the repository, read this file and `README.md`, and read `clinerules.md` if present. Inspect relevant existing changes before modifying files.

Consult relevant project context, including:

- `docs/` — project documentation, plans, and supporting records.
- `docs/architecture/` — architecture and design documentation.
- `docs/brains/` — project state, decisions, and persistent context.
- Chunk-specific folders — plans, implementation records, and verification results.
- Relevant repository instructions, configuration, source code, and tests.

Important records may include `docs/ECAS.md`, `docs/brains/PROJECT_STATE.md`, and `docs/brains/DECISIONS.md`. Verify actual paths and contents rather than assuming this list is exhaustive or unchanged.

Use code to establish current implementation, tests and execution results to establish verified behavior, and project records to understand intended direction and previous decisions. Treat historical reports and plans as context, not proof that functionality currently exists.

Resolve routine discrepancies using available evidence and update inaccurate records when justified.

## 5. Documentation and Project Organization

Keep documentation consistent with actual implementation and project goals.

Both agents may update relevant source documents, architecture records, decisions, project state, roadmaps, chunk notes, and development instructions when changes warrant it.

Prefer targeted edits that preserve useful content and history. Avoid wholesale rewrites of established source documents unless a clear need justifies them.

Document meaningful changes, significant decisions, verification results, and remaining limitations. Distinguish implemented functionality from proposals and future plans.

Use existing chunk organization where practical. Create or update chunk-specific files and folders, including future chunk folders, when they provide useful continuity or organization. Avoid redundant documentation and unnecessary structure.

Update documents according to their purpose; not every change requires editing every project record.

## 6. Code Quality and Scientific Integrity

Make focused, maintainable changes that fit ECAS's architecture. Improve architecture or organization when justified by functionality, reliability, or maintainability.

Preserve scientific provenance. Distinguish observational, reference, synthetic, and processed data where applicable.

Do not invent data, units, metadata, or physical interpretations. Do not silently assume missing scientific parameters. Make unsupported formats, invalid data, and relevant limitations clear. Spectral overlap alone must not be presented as proof of molecular detection.

Justify and document transformations or assumptions that could affect scientific interpretation.

Avoid unnecessary dependencies and weakening tests merely to make them pass. For security- or data-integrity-sensitive changes, preserve existing protections and verify important success and failure cases.

## 7. Testing and Verification

Add or update tests for changed behavior and important regressions.

Run focused tests first, then broader relevant tests when practical. Use manual or application-level checks when appropriate.

Investigate and fix implementation-related failures where possible. Review the final diff for unintended changes and confirm that relevant documentation matches the result.

Report actual commands and outcomes. Clearly distinguish passed tests, failed tests, checks not performed, and verification blocked by the environment. Never claim that unexecuted tests passed.

## 8. Handoffs and Progress Reports

At the end of a meaningful work increment, provide a concise report covering:

- **Task and status:** Objective and completion state.
- **Changes:** Important modifications and relevant files.
- **Verification:** Tests run, results, and gaps.
- **Documentation:** Records updated.
- **Outstanding work:** Issues, limitations, or blockers.
- **Working state:** Relevant local changes and any known integration concerns.
- **Next step:** Required review, corrections, or the next useful task.

Keep reports proportionate to the work. Preserve enough context for another agent to continue without repeating completed investigations.

Review agents should accept completed work or give specific, actionable corrections based on evidence. Implementation agents should address corrections and repeat relevant verification.

Update records before claiming they have been updated. After a completed increment, identify and continue with the next useful task when appropriate.

## 9. Working Tree and Human Input

Preserve existing work and inspect relevant local changes before modifying files. Avoid overwriting unrelated changes or discarding another contributor's work.

Agents may make and verify local changes without committing or pushing after every increment. Keep the working tree understandable, report significant uncommitted changes, and make progress records useful for later integration and manual GitHub updates.

Do not commit, push, or perform destructive Git operations unless explicitly authorized. Never rewrite shared Git history or force-push.

Routine coding, testing, refactoring, documentation, and justified architectural changes are within normal development authority.

Seek human input when an important decision cannot reasonably be resolved from project context, technical evidence, established requirements, and reasonable alternatives. Examples include unresolved scientific-method choices or major incompatible design decisions.

When blocked, explain the specific issue and what decision is needed, while continuing any independent work that remains possible.

## Core Principle

**Investigate, decide, implement, verify, review, document, and continue.**

Take initiative, preserve scientific integrity and useful project context, and make measurable progress toward a functional ECAS application without unnecessary approval or administrative overhead.

The key adjustment is that local implementation and verification are the normal unit of progress. GitHub publication is a separate integration step, not a requirement for every task.