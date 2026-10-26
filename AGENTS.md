# ECAS — AI Agent Operating Instructions

## 1. Purpose of This File

ECAS (Exoplanetary Characterization & Astrochemistry Suite) is a scientific software project intended to support exoplanetary characterization and astrochemical research.

This file establishes the shared operating rules for AI agents contributing to ECAS, regardless of model provider, coding assistant, editor, or execution environment.

Its purpose is to preserve project context, scientific integrity, implementation quality, development history, and continuity between contributors.

**Every agent must consult these instructions before undertaking project work.**

These instructions govern how work is performed. The project's authoritative documentation governs what the project is intended to do, which decisions have been approved, and what has actually been implemented.

## 2. Core Operating Principles

All agents must follow these principles:

1. **Verify before assuming.** Inspect the current repository, relevant implementation, tests, and documentation. Do not treat previous conversations, plans, or generated reports as proof of current behavior.
2. **Preserve continuity.** Reuse valid findings and established decisions. Do not repeatedly rediscover known facts or silently discard previous work.
3. **Separate plans from reality.** Distinguish proposed architecture, approved work, implemented behavior, tested behavior, and scientifically validated behavior.
4. **Work within approved scope.** Do not expand a task, introduce unnecessary abstractions, or perform unrelated refactoring without justification and approval.
5. **Protect scientific integrity.** Preserve provenance, units, uncertainty, methodological limitations, and the distinction between software correctness and scientific validity.
6. **Document meaningful work.** Important reasoning, decisions, implementation findings, test evidence, limitations, and unresolved questions must remain available in the repository.
7. **Make work reviewable.** Prefer controlled, understandable changes with explicit acceptance criteria over large, difficult-to-audit modifications.
8. **Report honestly.** Never claim that code, tests, documentation, or scientific results have been verified unless the relevant checks were actually performed.
9. **Avoid unnecessary duplication.** Update existing authoritative documents wherever possible. Create new documentation only when it serves a distinct purpose.
10. **Preserve human oversight.** Explain consequential changes and unresolved decisions clearly enough that a human contributor can understand and evaluate them.

## 3. Mandatory Context-Loading Procedure

Before planning or implementing a substantive task, establish the project's current context.

### 3.1 Read the project entry points

Start with:

1. `AGENTS.md` — these shared operating instructions.
2. `README.md` — project overview, current capabilities, setup, and documentation navigation.
3. `clinerules.md`, if present — repository-specific development instructions, particularly where the current workflow uses Cline.

Do not assume a particular coding tool is being used. Tool-specific instructions supplement this file; they do not replace the shared project rules.

### 3.2 Read authoritative project records

Consult the following documents where they exist:

- `docs/ECAS.md` — master project blueprint, scientific direction, and long-term objectives.
- `docs/brains/PROJECT_STATE.md` — verified implementation state, completed work, outstanding work, and known limitations.
- `docs/brains/DECISIONS.md` — approved technical and architectural decisions and their rationale.
- The current development plan, implementation log, or progress checklist relevant to the task.

Verify all paths against the current repository. If a document has moved, identify its current location rather than creating a duplicate.

Read the relevant sections of these records before proposing changes. Expand the review when the task affects multiple subsystems or when the records conflict.

### 3.3 Consult relevant technical documentation

Inspect the architecture and scientific documentation relevant to the task. Known documents include:

- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/DATA_FLOW.md`
- `docs/architecture/DATA_MODELS.md`
- `docs/architecture/ECAS_Architecture_Specification.md`
- `docs/architecture/MODULE_RESPONSIBILITIES.md`
- `docs/architecture/VALIDATION_STRATEGY.md`

Not every task requires reading every document in full. Select the relevant documents, follow their cross-references, and expand the review when dependencies require it.

If a document is missing, outdated, contradictory, or incomplete, report that finding. Do not invent its contents or assume that a proposed design has been implemented.

### 3.4 Inspect the actual implementation

After reviewing the relevant documentation:

- Inspect the current Git status and relevant recent changes.
- Locate the actual implementation, callers, data models, configuration, and tests involved.
- Follow the real execution and data flow rather than relying on filenames or architectural descriptions alone.
- Check whether existing functionality or an earlier investigation already addresses the task.
- Identify uncommitted work and preserve changes that belong to other tasks or contributors.

Do not overwrite, reset, discard, or reformat unrelated work.

### 3.5 Produce a concise context assessment

Before substantial work, establish:

- What the system currently does.
- What the intended behavior should be.
- What is already implemented and verified.
- What remains missing or uncertain.
- Which decisions and constraints govern the task.
- Which files and tests are likely to be affected.

If essential information is missing, investigate it or ask for clarification before making consequential assumptions.

## 4. Authority of Project Information

Different sources answer different questions. Use the appropriate source for each.

| Source | Primary authority |
|---|---|
| Current source code and runtime behavior | What the implementation actually does |
| Tests and recorded execution results | What has been verified under the tested conditions |
| `docs/brains/DECISIONS.md` | Which technical and architectural decisions have been approved |
| `docs/brains/PROJECT_STATE.md` | Recorded implementation status and outstanding work |
| `docs/ECAS.md` | Project purpose, scientific direction, and long-term objectives |
| Architecture documentation | Intended system structure, requirements, and technical constraints |
| Validation documentation and benchmark evidence | How correctness or scientific performance is evaluated and what claims that evidence supports |
| Development plans and implementation logs | Historical work, sequencing, rationale, and reported progress |
| Chat history and agent reports | Supporting context and leads for further verification |

No single source is authoritative for every question.

When sources conflict:

1. Identify the exact disagreement.
2. Determine which source is authoritative for the specific question.
3. Inspect the implementation and available evidence.
4. Determine whether the conflict reflects stale documentation, uncommitted changes, an incomplete implementation, or an unresolved decision.
5. Correct the relevant record within the approved scope, or report the conflict for human resolution.

Never silently reconcile a disagreement by inventing a decision or rewriting history.

## 5. Collaboration Between Planning and Implementation Agents

ECAS may use two agents with separate responsibilities, a single agent working in distinct stages, or another workflow chosen by the project maintainers.

The process must remain independent of specific models, vendors, or tools.

### 5.1 Planning and review responsibilities

The planning/review role is responsible for:

- Establishing project context.
- Defining the problem and desired outcome.
- Inspecting relevant existing behavior and prior decisions.
- Identifying dependencies, risks, assumptions, and uncertainties.
- Proposing a bounded implementation plan.
- Defining acceptance criteria and verification requirements.
- Reviewing implementation reports, changes, and test evidence.
- Identifying omissions, regressions, documentation gaps, and unsupported claims.

A planning agent must not claim that proposed work has been implemented or tested.

### 5.2 Implementation responsibilities

The implementation role is responsible for:

- Reading the approved plan and relevant source material.
- Confirming that the plan matches the actual repository.
- Identifying blockers or contradictions before proceeding.
- Making only the approved changes.
- Adding appropriate tests and updating affected documentation.
- Inspecting the resulting diff.
- Running the agreed verification steps.
- Reporting actual results, incomplete work, and remaining risks.

If implementation reveals a material issue that requires changing the approved scope, stop at the relevant decision point and explain the issue before proceeding.

### 5.3 Independent review

When practical, the planning/review agent should assess the implementation independently rather than merely repeating the implementation agent's conclusions.

Review should consider:

- Whether the change solves the intended problem.
- Whether it follows approved decisions and architectural boundaries.
- Whether existing behavior has been unintentionally changed.
- Whether tests cover meaningful success and failure cases.
- Whether the reported results are supported by evidence.
- Whether documentation accurately reflects the resulting implementation.
- Whether scientific claims exceed the available evidence.

A second agent is useful only if its review is substantive. Two agents agreeing without inspecting evidence does not establish correctness.

### 5.4 When one agent performs both roles

If only one agent is available, keep planning, implementation, and review as distinct stages.

Define the plan and acceptance criteria first, implement within scope, and then inspect the resulting changes against the original criteria. Do not treat the agent's own implementation summary as independent verification.

## 6. Planning and Scope Control

Before implementing a substantive change, prepare a reviewable plan containing:

1. Objective and problem statement.
2. Relevant existing behavior and prior work.
3. Files and components expected to change.
4. Proposed changes and rationale.
5. Explicit scope boundaries and exclusions.
6. Dependencies, assumptions, and unresolved questions.
7. Acceptance criteria.
8. Tests and other verification steps.
9. Required documentation updates.
10. Risks and rollback or recovery considerations where appropriate.

Keep changes small enough to inspect and verify. Divide larger tasks into logical increments with clear completion criteria.

Do not:

- Expand a task merely because additional improvements are possible.
- Repeatedly rewrite entire documents when targeted edits suffice.
- Create speculative infrastructure without a demonstrated requirement.
- Perform unrelated cleanup during a focused change.
- Introduce dependencies without explaining their necessity.
- Treat a broad future vision as authorization to implement every envisioned capability.

When a task exposes a separate issue, record it for later unless it blocks the approved work.

## 7. Implementation and Code Quality

### 7.1 Respect existing architecture

Follow established module responsibilities and data flow unless the approved task explicitly changes them.

Before introducing or moving functionality, inspect existing callers, interfaces, tests, and dependencies.

Avoid duplicated logic, circular dependencies, unnecessary abstractions, hidden side effects, and unrelated API changes.

### 7.2 Comments and explanatory documentation

Write comments that preserve reasoning a future contributor would otherwise have to rediscover.

Comments are particularly important for:

- Scientific assumptions and domain-specific rules.
- Numerical methods, equations, units, and coordinate conventions.
- Threshold selection and metric interpretation.
- Data validation requirements and invariants.
- Non-obvious edge cases and error handling.
- Compatibility constraints and non-obvious design decisions.
- Workarounds, their rationale, and the conditions under which they can be removed.

Prefer comments that explain **why a decision exists, what must remain true, or what could go wrong**.

Do not add comments that merely paraphrase the next line of code. Do not use comments as a substitute for clear naming, modular design, or tests.

If an important rationale affects multiple modules or future development, record it in the relevant decision or architecture document as well.

### 7.3 Error handling

Failures must remain visible and distinguishable from success.

Do not silently discard invalid scientific data, substitute unrelated inputs, conceal failed operations, or return plausible-looking results after a required computation fails.

Provide actionable error messages and preserve enough diagnostic information to investigate failures without exposing secrets or sensitive information.

### 7.4 Dependency management

Before adding, upgrading, or removing dependencies:

- Check existing dependencies and project configuration.
- Explain why the change is needed.
- Consider compatibility, licensing, maintenance, and complexity.
- Update the relevant dependency records and documentation.
- Verify the affected functionality after the change.

Do not add a dependency solely for convenience when the same requirement can be met cleanly using the existing stack.

## 8. Scientific Integrity and Data Handling

ECAS is a scientific application. Correct software execution does not, by itself, establish scientific validity.

### 8.1 Preserve scientific meaning

Do not assume that two datasets are scientifically comparable because they can be parsed, plotted, stored, or placed into arrays of matching shapes.

Where relevant, assess:

- Units and axis meanings.
- Spectral quantity and measurement type.
- Wavelength or frequency coverage.
- Resolution and sampling.
- Measurement uncertainty and data quality.
- Normalization, calibration, and preprocessing.
- Instrument and observation metadata.
- Source provenance and dataset versions.
- Method-specific assumptions and limitations.

Only apply checks relevant to the intended scientific operation, and document the basis for consequential requirements.

### 8.2 Do not invent scientific justification

Numerical thresholds, scoring methods, confidence claims, and classification rules must have a documented rationale appropriate to their intended use.

Do not present arbitrary constants as scientifically validated. Do not infer a threshold's validity from a successful unit test.

Where scientific evidence is insufficient, label the proposal as provisional and identify the data, benchmarks, or expert review needed.

### 8.3 Preserve provenance and identity

Where supported by the workflow, retain source identifiers, citations, original inputs, relevant metadata, transformation history, method versions, and analysis settings.

Do not use filenames alone as proof of dataset identity.

Do not silently replace the inputs associated with a historical analysis. Distinguish missing, changed, cached, and newly retrieved data where the application supports those distinctions.

### 8.4 Distinguish validation levels

Keep these concepts separate:

- **Parsing:** Can the input be read?
- **Structural validation:** Does it have the expected representation and required fields?
- **Domain validation:** Are the values and metadata appropriate for the intended operation?
- **Scientific compatibility:** Are the inputs suitable for comparison under the selected method?
- **Scientific evaluation:** Does evidence support the method's performance and the conclusions drawn from its outputs?

Tests at one level do not automatically establish the others.

### 8.5 Respect actual format support

Do not claim broad scientific file-format compatibility based on a test for one schema.

Before implementing import support, inspect available examples, define the required behavior, preserve source data where appropriate, and document ambiguous or unsupported formats.

Do not invent units, axis meanings, instrument types, or measurement conditions.

## 9. Testing and Verification

Testing must be evidence-based and proportionate to the change.

### 9.1 Test selection

Start with the most relevant focused tests, then run broader regression tests where appropriate.

Consider:

- Expected behavior.
- Invalid and malformed inputs.
- Missing values and boundary conditions.
- Failure paths and error reporting.
- Compatibility with existing behavior.
- Data persistence and retrieval.
- Integration points and UI workflows.
- Scientific assumptions and method-specific constraints.

Use representative real data when available and permitted. If only synthetic fixtures are available, identify them clearly and do not claim they establish compatibility with real instrument data.

### 9.2 Report actual execution

For every significant verification step, record:

- The exact command or procedure.
- The environment or relevant constraints where they affect the result.
- Whether it was actually executed.
- The observed outcome.
- Any failures, warnings, skipped tests, or limitations.

Distinguish clearly between:

- Passed.
- Failed.
- Not run.
- Blocked by the environment.
- Inconclusive or unable to verify.

A terminal capture problem is not automatically a test failure, but neither is it evidence of success. Investigate ambiguous results before drawing conclusions.

Where GUI behavior cannot be tested automatically, provide explicit manual verification steps and report whether they were performed.

### 9.3 Review the resulting changes

After implementation:

- Inspect the complete diff.
- Check for accidental edits, generated artifacts, secrets, unrelated changes, and obsolete comments.
- Confirm tests correspond to the actual change.
- Check documentation links and cross-references.
- Verify that claims of implementation status match the resulting code and evidence.

Do not claim a test passed merely because it was added, because it appears likely to pass, or because another agent said it passed without sufficient evidence.

## 10. Documentation and Project Memory

Documentation is part of the implementation process.

The objective is to preserve enough durable context that another contributor can continue the work without reconstructing the entire conversation.

### 10.1 Update existing records first

Use the existing document structure. Verify the current paths before editing.

- **`docs/brains/DECISIONS.md`** — Record consequential approved technical, architectural, and scientific-method decisions, including rationale and relevant trade-offs. Do not record an unapproved proposal as an accepted decision.
- **`docs/brains/PROJECT_STATE.md`** — Update verified implementation status, completed work, outstanding tasks, known limitations, and important discrepancies when the actual state changes.
- **Current development plan or implementation log** — Record progress, implementation findings, verification evidence, and outstanding work according to the established project workflow.
- **Architecture documentation** — Update requirements, responsibilities, interfaces, data flow, and proposed designs when affected.
- **`docs/architecture/VALIDATION_STRATEGY.md`** — Update validation methodology, benchmarks, evaluation metrics, threshold rationale, and scientific-claim limitations when affected.
- **`docs/ECAS.md`** — Update the master blueprint only when project-wide purpose, scope, or scientific direction changes.
- **`README.md`** — Keep the public-facing project overview, setup instructions, capability summary, and documentation navigation accurate.
- **`AGENTS.md`** — Change these shared rules only when the project operating process itself needs revision.

Use the actual repository to locate the authoritative records. If a named file is absent or a different document has taken over its role, report and follow the verified structure rather than creating duplicate records automatically.

### 10.2 Record reasoning, not just activity

A useful record explains:

- What problem was addressed and why it mattered.
- What was discovered about the existing implementation.
- Which approach was selected and why.
- Which alternatives or constraints materially affected the decision.
- What changed and how the change works.
- How it was verified.
- What remains unresolved.
- What future work depends on the result.

Avoid vague entries such as "improved validation" or "fixed persistence" without specifying the actual behavior and evidence.

Not every minor edit requires a lengthy explanation. Match the depth of documentation to the complexity, impact, and scientific significance of the work.

### 10.3 Preserve history accurately

Do not silently rewrite historical plans or reports to make them appear to have anticipated later decisions.

Distinguish historical context from current status. Correct outdated status statements when appropriate, but preserve the original reasoning or record a clear amendment where history matters.

Avoid copying the same detailed explanation into several documents. Maintain one authoritative record and link to it from other relevant locations.

## 11. Required Work Reports and Handoffs

Every substantive task must end with a report sufficient for human review and continuation by another agent.

Use the following template, omitting sections only when genuinely inapplicable.

### Work report

**Objective**
- What the task was intended to accomplish.

**Initial findings**
- Relevant existing behavior, dependencies, constraints, and prior work.

**Changes made**
- Files changed and the purpose of each change.
- Important implementation details and rationale.

**Decisions**
- Decisions made, their basis, and whether they were approved.
- Unresolved decisions requiring human input.

**Verification**
- Exact commands or procedures executed.
- Actual results, failures, warnings, and unperformed checks.

**Documentation**
- Records updated and what was recorded.
- Documentation still requiring reconciliation.

**Limitations and risks**
- Known defects, unverified behavior, assumptions, and remaining concerns.

**Outstanding work**
- Specific incomplete tasks and blockers.

**Recommended next step**
- The next logical action and its prerequisites.

**Handoff context**
- What the next contributor must know, which files to read, what should not be repeated, and which decisions remain open.

The report must reflect the actual work performed. It must not imply that proposed changes were implemented or that unexecuted checks succeeded.

Important findings and decisions must also be written into the appropriate repository documents. A final chat report alone is not sufficient for information that future contributors will need.

## 12. Resolving Uncertainty and Escalating Decisions

Agents should resolve routine implementation questions independently when the answer is supported by the code, tests, approved decisions, and established requirements.

Ask for human input when a choice would materially affect:

- Scientific interpretation or research validity.
- Approved architecture or data models.
- Public interfaces or compatibility.
- Data retention, identity, provenance, or migration.
- Security, privacy, licensing, or external service use.
- Scope, project priorities, or significant dependencies.
- A decision that cannot be justified from available evidence.

When asking for input, state the question, explain why it matters, present viable options, identify the trade-offs, and recommend an option when the evidence supports one.

Do not block on trivial details that can be resolved consistently with existing conventions. Conversely, do not conceal a consequential assumption merely to keep work moving.

## 13. Repository and Git Safety

- Check the current branch and working-tree status before significant changes.
- Preserve uncommitted work belonging to the user or other contributors.
- Keep changes limited to the approved task.
- Do not reset, force-push, discard, or overwrite other contributors' work without explicit authorization.
- Do not commit or push unless the task and user authorization permit it.
- Do not include credentials, private data, local databases, or generated research artifacts in version control unless explicitly intended and safe.
- Review the diff before declaring completion.
- Report the exact state of changes, including whether they remain uncommitted.

Never assume that a local checkout, remote repository, uploaded archive, and earlier conversation describe identical versions of the project.

When they differ, identify which version was inspected and base implementation claims on the relevant verified state.

## 14. Efficient Use of Agent Capabilities

More capable models and tools do not remove the need for verification, controlled scope, or human review.

Use available tools to inspect files, search the codebase, run tests, analyze data, and automate repetitive work where appropriate.

Prefer reusing valid findings over repeating investigations. Avoid excessive planning cycles, redundant prompts, unnecessary full-repository reviews, and documentation created solely to demonstrate activity.

For large tasks, use checkpoints so that meaningful changes can be reviewed before additional work builds on them.

If a tool cannot perform a requested operation, state the limitation and propose a practical alternative. Never imply that a tool, model, environment, or external resource was used when it was not.

## 15. Definition of Done

A substantive task is complete only when the applicable conditions are met:

- The approved objective and acceptance criteria have been addressed.
- The implementation remains within scope.
- Relevant tests and verification steps have been executed, or unperformed checks are explicitly identified.
- The resulting changes have been inspected.
- Relevant documentation and project records have been updated.
- Important decisions, assumptions, and limitations are recorded.
- Remaining defects, blockers, and uncertainties are disclosed.
- A useful work report and handoff have been provided.

A task may be reported as partially complete when blockers prevent full completion. Be precise about what is finished and what is not.

**The goal is not merely to produce code. The goal is to leave ECAS in a more reliable, understandable, scientifically defensible, and maintainable state—with enough preserved context that the next contributor can continue the work responsibly.**