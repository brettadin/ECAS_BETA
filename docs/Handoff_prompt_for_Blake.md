# ECAS — Development Handoff

## 1. First-Session Checklist

- [ ] Read `agents.md`, `README.md.
- [ ] Inspect the current repository, working tree, and existing local changes.
- [ ] Review the project state, decisions, development plan, and relevant chunk records.
- [ ] Check relevant documentation under `docs/`, `docs/architecture/`, and `docs/brains/`.
- [ ] Compare documented progress with the actual code and available test results.
- [ ] Identify the current priorities and next useful development task.
- [ ] Begin work, updating relevant code, tests, and documentation as needed.

Verify actual file paths and repository state rather than assuming previous reports remain current. Preserve existing changes and avoid repeating investigations that reliable evidence has already resolved.

## 2. Project Identity

**ECAS — Exoplanetary Characterization & Astrochemistry Suite**

Repository: https://github.com/brettadin/ECAS_BETA

ECAS is a Python scientific desktop application for exoplanetary spectroscopy and atmospheric characterization. The goal is to develop a functional, reliable, maintainable application that supports scientifically responsible analysis.

`agents.md` defines the standing instructions, permissions, and development principles. This handoff provides project context and continuity.

## 3. Development Workflow

Work in small, coherent increments that deliver useful progress.

1. Establish the task, current implementation, and relevant constraints.
2. Choose a practical approach based on the codebase and project decisions.
3. Implement the necessary code, tests, configuration, or documentation changes.
4. Run relevant tests and checks; investigate failures where possible.
5. Review the changes and update relevant project records.
6. Identify remaining work and continue to the next useful task.

Use planning when it helps clarify requirements or reduce risk. Do not remain in planning when the task is sufficiently understood and implementation can proceed.

Both agents may modify code, functionality, architecture, tests, and relevant project records. Make reasonable technical decisions independently, preserve useful existing work, and seek human input only for consequential decisions that cannot reasonably be resolved from available evidence.

## 4. Project Context and Documentation

Use the current roadmap, project-state records, decisions, architecture documents, and chunk-specific records to establish progress and priorities.

Important records may include:

- `docs/ECAS_development_plan.md`
- `docs/ECAS.md`
- `docs/brains/PROJECT_STATE.md`
- `docs/brains/DECISIONS.md`
- Current development plans and chunk documentation.

Verify paths and inspect relevant source code and tests. Code establishes what is implemented; test results establish what has been verified. Plans and previous reports provide context but are not proof of current functionality.

Update relevant documentation when implementation changes affect documented behavior, architecture, decisions, capabilities, or project status. Prefer targeted edits that preserve established content and history. Create or update chunk-specific records when useful, avoiding redundant documentation.

## 5. Scientific and Technical Standards

- Preserve data provenance and distinguish observational, reference, synthetic, and processed data where applicable.
- Never invent scientific data, units, metadata, or physical interpretations.
- Make unsupported formats, invalid inputs, assumptions, and limitations clear.
- Do not treat spectral overlap alone as proof of molecular detection.
- Justify transformations or assumptions that affect scientific interpretation.
- Add or update tests for changed behavior and important regressions.
- Report actual verification results, including failures and checks not performed.

Favor maintainable solutions that fit the existing architecture. Improve the architecture when justified by functionality, reliability, or maintainability.

## 6. Working State and Integration

Progress may accumulate through local changes over multiple increments. Commits and pushes are not required after every task.

Preserve existing work, inspect relevant local modifications before editing, and avoid overwriting unrelated changes. Keep significant uncommitted work and integration concerns clear in progress records.

Do not commit, push, force-push, rewrite shared Git history, or perform destructive Git operations unless explicitly authorized. Repository publication can be handled separately.

## 7. Progress Report and Continuity

At the end of each meaningful increment, report:

- **Task and status:** Complete, partial, or blocked.
- **Changes:** Important modifications and relevant files.
- **Verification:** Commands executed, actual results, and checks not performed.
- **Documentation:** Records updated.
- **Outstanding work:** Defects, limitations, or unresolved issues.
- **Working state:** Relevant local changes and integration concerns.
- **Next step:** The next useful task.

Keep reports factual and proportionate. Review actual implementation and evidence, address identified defects, and repeat relevant verification.

Maintain continuity by recording verified progress, remaining work, and updated priorities. At the start of future sessions, re-establish the current state rather than blindly following old recommendations.

**Core principle:** Make steady, verifiable progress toward a functional ECAS application while maintaining scientific integrity, accurate documentation, and continuity across development sessions.