# ECAS — Development Plan Reconciliation and Autonomous Development Workflow

**Repository:** https://github.com/brettadin/ECAS_BETA  
**Project:** ECAS — Exoplanetary Characterization & Astrochemistry Suite  
**Initial mode:** PLAN  
**Scope:** Reconcile project documentation with the actual implementation, revise the development plan, and establish a safe workflow for autonomous development after planning and documentation are complete.

## Objective

Review the current project state and authoritative documentation. Establish what has genuinely been completed, what remains outstanding, and what needs to change in the development plan. See: `docs/ECAS_development_plan.md`

The revised plan must accurately represent the current state of Chunk 4 and establish a clear, evidence-based path into Chunks 5, 5.1, and 6.

After the necessary planning, documentation reconciliation, and verification are complete, the intended workflow is for the agent to **continue working through eligible development tasks without requiring a separate human approval for every routine step**.

This is a staged task:

1. **Planning and reconciliation:** Investigate the repository, prepare a reviewable plan, and identify required documentation changes. Do not edit files or implement features in this phase.
2. **Documentation and roadmap:** After the initial plan is approved, reconcile the relevant records and finalize the development roadmap.
3. **Autonomous development:** Once the documentation and roadmap are reconciled, use the established roadmap to plan, implement, test, review, and document subsequent eligible tasks in controlled increments, without stopping for routine approval between each step.

Autonomous execution does not mean unrestricted changes. Preserve scientific integrity, repository safety, explicit acceptance criteria, and clear stop conditions. The agent must not bypass a necessary human decision simply to keep working.

---

## 1. Establish the current state

Inspect the current branch, working-tree status, relevant commit history, authoritative project-state and decision records, and the development plan.

Locate the relevant chunk plans, implementation reports, review records, test evidence, handoffs, and decisions. Start with the authoritative documents and most recent relevant records; inspect additional files when needed to resolve specific questions.

Determine whether the current checkout includes the relevant recent work. Distinguish committed changes from local changes and identify discrepancies between the current code, documentation, and historical records.

Use the actual repository and available verification evidence to establish implementation status. Previous conversations and historical plans may provide context, but are not proof that something was implemented, tested, or accepted.

Reuse existing evidence and decisions wherever possible. Avoid redundant investigations, unnecessary rewrites, and duplicate documentation.

Do not overwrite, discard, or silently modify unrelated user changes. Before any implementation work, establish the branch and working-tree state and preserve a safe boundary around existing work.

## 2. Reconcile documentation and implementation status

Identify the specific documentation that requires correction or updating.

For each relevant task, distinguish between:

- Planned but not implemented.
- Partially implemented.
- Implemented but not fully tested.
- Tested but not manually verified where manual verification is required.
- Reviewed but not yet accepted.
- Verified and accepted.
- Deferred or blocked.

These states must not be treated as interchangeable.

Inspect Chunk 4 in particular, including the NASA transmission-spectrum retrieval workflow, caching and provenance, offline reopening, failure handling, outstanding interactive verification, independent review, and integration with newer development work.

Verify each relevant status against the current code, test evidence, review records, and acceptance criteria. Do not assume every item listed above remains outstanding; determine its actual status.

Update the development plan and authoritative project-state or decision records only where changes are justified. Preserve historical plans and evidence unless a specific correction is necessary. Do not rewrite completed historical plans merely to make them match the current roadmap.

Do not mark Chunk 4 complete or merge-ready unless its applicable acceptance criteria have been satisfied.

## 3. Revise the development plan

Locate the authoritative development plan and revise its relevant sections to reflect the following intended structure.

Preserve the existing document organization and terminology where practical. If the plan already contains relevant material, revise it in place rather than creating a competing version.

### Chunk 5 — Spectral Comparison Foundations and Method Selection

**Purpose:** Establish what makes spectra scientifically comparable and select an appropriate comparison method before implementing the production workflow.

The plan must cover:

- **Spectral compatibility:** Define the conditions required for scientifically meaningful comparisons, including units, spectral axes, coverage, resolution, sampling, uncertainty, instrument characteristics, and relevant measurement conditions.
- **Representative test cases:** Identify realistic cases involving noisy, incomplete, overlapping, and incompatible spectra.
- **Candidate methods:** Investigate simple line matching and scientifically appropriate alternatives. Evaluate their assumptions, scientific validity, robustness, interpretability, limitations, and computational practicality.
- **Evaluation criteria:** Define how candidate methods will be assessed, including how uncertainty, spectral overlap, ambiguous matches, and false matches will be handled.
- **Comparison contract:** Define required inputs, validation behavior, outputs, provenance, and compatibility rules.
- **Method selection:** Document an evidence-based decision explaining why the selected method is appropriate for ECAS's supported data and intended scientific use.

Do not assume simple line matching is sufficient. Do not select a method merely because it is easy to implement. Equally, avoid unnecessary complexity if a simpler method adequately meets the requirements.

**Completion criterion:** A justified method selection supported by explicit constraints, representative test cases, evaluation criteria, and documented limitations. If the available evidence is insufficient, record the unresolved questions instead of forcing a decision.

This chunk is primarily investigation, evaluation, and specification. It does not require implementation of the production comparison workflow.

### Chunk 5.1 — Molecular Reference Spectra and Comparison Data Integration

**Purpose:** Establish the infrastructure for discovering, retrieving, caching, organizing, and selecting molecular reference spectra for use in ECAS.

The plan must cover the following areas.

**A. Provider and format investigation**

- Investigate suitable scientific reference-data providers and file formats.
- Evaluate NIST as a candidate, alongside relevant alternatives. Investigate JCAMP-DX and other appropriate formats without assuming any provider or format is automatically the best choice.
- Assess actual availability of molecular spectra, supported search mechanisms, downloadable data products, spectral coverage, units, resolution, metadata, access restrictions, and suitability for the intended scientific use.
- Select an appropriate initial provider and supported representation based on the findings.
- Determine which additional sources or formats should be deferred rather than expanding the initial implementation unnecessarily.

**B. In-application molecular search**

ECAS must eventually be able to search for molecular spectral data directly from within the application.

- Provide a search workflow that queries the selected provider from ECAS rather than requiring users to locate and download every spectrum manually outside the program.
- Support searching by molecule name and, where the provider supports it, chemical formula, molecular identifiers, or other relevant search fields.
- Display available datasets and useful metadata before retrieval, including molecular identity, source, spectral coverage, data type, units, and other metadata supported by the provider.
- Allow users to select an available dataset for retrieval and caching.
- Clearly communicate when a search fails, no results are available, a product cannot be retrieved, or the provider does not expose the required search or download capability.
- Investigate the provider's actual interfaces, access policies, and technical constraints before choosing an implementation approach. Do not assume that a website offers a suitable public API or automated download mechanism without verifying it.
- If NIST is not the most suitable initial source, document the evidence for selecting an alternative while preserving the requirement for in-application molecular search.

**C. Retrieval, caching, and provenance**

- Implement retrieval, parsing, local caching, integrity validation, provenance preservation, and offline reopening for the selected reference-data source.
- Investigate whether existing ECAS caching and persistence patterns can be reused. Do not assume that the exoplanet-data cache is suitable without examining its architecture and requirements.
- Preserve source identifiers, original data where feasible, retrieval details, units, metadata, and the transformations applied during parsing or processing.
- Distinguish measured reference spectra, theoretical line lists, simulated spectra, and processed data.
- Handle missing metadata, invalid products, interrupted retrievals, and cache-integrity failures explicitly.

**D. Molecular catalogue and comparison interface**

- Establish a searchable molecular catalogue linking molecular identities to available reference datasets and their metadata.
- Support multiple reference datasets for a molecule where applicable; do not treat datasets from different sources, conditions, or representations as interchangeable without justification.
- Integrate the catalogue and reference-data selection into the Comparisons tab.
- Allow users to select the observational or input dataset independently of the reference dataset or datasets.
- Allow users to select individual molecules or inspect all eligible molecular references currently available.
- Show which datasets are available, cached, uncached, unavailable, invalid, or incompatible as appropriate.
- Make it clear which molecular reference dataset is selected and which observational or input dataset it will be compared against.

**E. Verification**

Plan focused tests covering provider search, retrieval, parsing, caching, provenance, integrity validation, offline reopening, catalogue behavior, dataset selection, and error handling.

Use real provider data where feasible, supplemented by documented fixtures for reproducible edge cases. Do not treat a successful download or file parse as independent scientific validation of the reference data.

**Completion criterion:** ECAS can search the selected initial provider from within the application, discover available molecular reference datasets, retrieve and cache selected spectra with traceable provenance, catalogue the available datasets by molecule, reopen cached spectra offline, and expose eligible reference and observational datasets for selection in the Comparisons tab.

This chunk establishes reference-data access and selection. It does not require the production comparison algorithm to be finalized or implemented, nor does it establish that any molecule is present in an observed atmosphere.

### Chunk 6 — Scientific Comparison, Interpretation, and Projections

**Purpose:** Implement the comparison workflow using the method selected in Chunk 5 and the reference-data infrastructure established in Chunk 5.1.

The plan must cover:

- **Dataset selection and validation:** Allow users to select eligible observational or input datasets and one or more molecular reference datasets. Validate compatibility before comparison.
- **Comparison execution:** Implement the selected method and its defined preprocessing, alignment, resolution handling, uncertainty treatment, and other required operations.
- **Multiple candidates:** Support comparison against individual molecules or multiple eligible reference datasets where the selected method permits.
- **Compatibility and failure explanations:** Explain why a comparison cannot proceed, which requirements are unmet, and what limitations affect the results.
- **Results and interpretation:** Present visualizations and derived comparison results appropriate to the selected method. Distinguish numerical agreement from scientific identification.
- **Projections and forward modelling:** Investigate and implement projections only where the required inputs, physical assumptions, and validation are established. Define the distinction between comparing an existing reference spectrum and predicting a spectrum under specified conditions.
- **Reproducibility:** Preserve input and reference dataset identities, source provenance, method version, preprocessing choices, relevant settings, and other information required to reproduce a result. Document limitations when original data or software versions cannot be recovered.
- **Scientific and technical verification:** Test known matches, ambiguous overlaps, incompatible inputs, changes in resolution or sampling, noise, incomplete data, missing metadata, and failure conditions.
- **Scientific reporting:** Clearly separate observed measurements, reference spectra, projected spectra, and derived comparison results. Do not present spectral overlap as proof of atmospheric composition or report unsupported abundance estimates.

**Completion criterion:** A user can select eligible datasets, run the documented comparison method, inspect and understand its results and limitations, and reproduce the analysis from preserved inputs and settings within the documented reproducibility limits. Any projections must be supported by explicitly defined and validated assumptions.

Do not expand these chunks into additional major chunks unless a concrete dependency or requirement demonstrates that the existing structure is insufficient.

## 4. Establish the correct sequence and dependencies

Evaluate the following intended sequence against the actual repository:

1. Finish outstanding Chunk 4 verification, review, and branch-integration requirements.
2. Update Chunk 4 documentation and acceptance status based on verified evidence.
3. Investigate and select the comparison method in Chunk 5.
4. Establish in-application molecular search, reference-data retrieval, caching, catalogue management, and Comparisons-tab selection in Chunk 5.1.
5. Implement the selected comparison workflow and scientifically justified projections in Chunk 6.

Confirm whether this ordering is appropriate given the current repository. If a dependency requires a different order, explain the reason and propose the smallest necessary adjustment.

Identify preliminary scientific or architectural questions that must be answered before implementation. Distinguish decisions that must be made during investigation from decisions that can safely remain open until evidence is available.

Do not prematurely design the entire future system or prescribe technologies before the investigation supports them.

## 5. Scientific and documentation requirements

Apply these principles throughout the plan and any documentation changes:

- Do not invent scientific data, sources, implementation results, test outcomes, or verification claims.
- Preserve source provenance and distinguish observations, measured reference spectra, theoretical line lists, simulated data, processed data, and projections.
- Do not assume spectra are comparable merely because they can be plotted together.
- Do not infer molecular presence from a spectral match alone.
- Do not assume that a provider, API, file format, or comparison method has been selected before the investigation establishes that decision.
- Keep deferred features explicitly deferred rather than silently absorbing them into the current scope.
- Preserve useful historical records and existing decisions unless evidence justifies revising them.
- Make unresolved questions and limitations explicit rather than silently making assumptions.
- Keep documentation changes focused on the approved scope.

## 6. Required PLAN-mode response

Before editing any files, provide a specific, reviewable plan containing:

1. **Files examined:** The authoritative development plan and relevant project-state, decision, chunk, review, and test records found.
2. **Current status:** What is complete, incomplete, unverified, deferred, or blocked, with supporting evidence.
3. **Documentation issues:** Exact file paths and sections requiring changes, with a brief explanation of each issue.
4. **Proposed edits:** Which files will change and what will change in each.
5. **Revised roadmap:** How Chunks 5, 5.1, and 6 will be represented, including dependencies and completion criteria.
6. **Outstanding decisions:** Missing evidence, unresolved scientific questions, provider capabilities that need investigation, and architectural dependencies.
7. **Verification plan:** How the resulting documentation will be checked for accuracy, consistency, and accidental changes.
8. **Autonomy readiness:** What capabilities, repository permissions, and execution conditions are needed for the agent to continue working after documentation reconciliation, and which of these are actually available in the current environment.
9. **Boundaries:** What will remain untouched or deferred.

Do not edit files or implement application functionality during PLAN mode. Do not claim that tests, reviews, or manual verification have been performed unless there is evidence that they actually have been.

Wait for approval before proceeding to ACT mode for the initial documentation reconciliation.

## 7. ACT-mode requirements for the initial reconciliation

Once the initial plan is approved:

- Make only the agreed documentation and development-plan changes.
- Read each target file before editing.
- Preserve historical records, unrelated work, and existing local changes.
- Base status updates on verified evidence.
- Inspect the complete diff for accuracy, consistency, accidental deletions, and unrelated modifications.
- Run appropriate documentation checks or repository validation commands where available.
- Report the exact files changed, substantive edits, verification performed and actual results, unresolved issues, and the next recommended task.

If investigation reveals that a proposed status update cannot be supported, leave the status unresolved and explain what evidence is missing. Do not manufacture certainty to complete the documentation.

If a separate implementation or review task is required to close an outstanding Chunk 4 item, document that requirement rather than performing unrelated work as part of the initial reconciliation.

Do not implement Chunks 5, 5.1, or 6 application functionality during this initial reconciliation task.

**Initial deliverable:** An accurate, internally consistent development plan and project record that reflects the actual state of ECAS, identifies remaining Chunk 4 requirements, and provides a practical, evidence-based roadmap for the next controlled development steps.

---

## 8. Autonomous development after planning and documentation are complete

After the initial reconciliation is completed and its documentation and roadmap have been verified, transition to the autonomous development workflow below. Do not treat this section as permission to skip the initial planning, reconciliation, or verification stages.

### 8.1 Transition conditions

Begin autonomous development only when all of the following are true:

- The authoritative development plan and project-state records are consistent with the repository evidence.
- The next eligible task and its dependencies are clear.
- Applicable acceptance criteria and verification requirements are documented.
- The agent has confirmed that it can access the required files, execute the necessary tools, and run the relevant tests.
- The current branch and working-tree state are understood, and existing work is protected.
- No unresolved human decision is a prerequisite for the next task.

If any condition is unmet, resolve it within the current authorized scope or stop and report the blocker. Do not pretend that a prerequisite has been satisfied.

### 8.2 Autonomous task loop

Once the transition conditions are satisfied, continue through the development roadmap without requiring a separate approval for each routine task.

For each task:

1. **Select the next task.** Use the authoritative roadmap, dependency order, and outstanding work. Prefer the smallest meaningful task that advances the next chunk.
2. **Inspect before acting.** Examine relevant code, tests, documentation, repository state, and existing decisions before proposing or making changes.
3. **Plan the task.** Define a bounded scope, expected behavior, acceptance criteria, likely risks, and verification steps. Record the plan in the appropriate existing project records when it materially affects future work.
4. **Implement the bounded task.** Make only changes required by that task. Preserve existing behavior unless a justified change is required by the approved roadmap.
5. **Verify.** Run relevant focused tests first, followed by broader tests or checks where appropriate. Execute the actual commands; do not infer success from a plan or from code inspection alone.
6. **Review the changes.** Inspect the complete diff, test coverage, error paths, compatibility, data integrity, provenance, documentation consistency, and unintended side effects.
7. **Resolve failures.** Diagnose and correct failures within the task's scope when the cause is understood and the fix is safe. Re-run affected checks after changes. Do not repeatedly retry without new evidence.
8. **Update project records.** Record actual implementation status, tests run and results, known limitations, decisions, deferred work, and any remaining acceptance requirements.
9. **Assess completion.** Mark the task complete only when its acceptance criteria are supported by evidence. Otherwise record it as partial, unverified, blocked, or deferred.
10. **Continue.** Select the next eligible task and repeat without waiting for routine human approval.

Keep each task small enough that its changes and verification can be understood independently. Do not combine an entire chunk into one large, difficult-to-review change merely to reduce pauses.

### 8.3 PLAN and ACT behavior during autonomous work

Use the PLAN and ACT behavior according to the capabilities of the installed environment.

- Use planning before each meaningful implementation task, but do not require the user to manually relay and approve every routine plan.
- After checking that the task falls within the established roadmap and autonomy boundaries, proceed to implementation where the environment permits.
- If the tool requires a mode switch or confirmation that cannot be performed autonomously, report that limitation clearly. Do not claim to have continued automatically when the environment has paused.
- Do not reinterpret the original PLAN-mode restriction as a permanent prohibition on implementation. It applies to the initial reconciliation phase; subsequent implementation is authorized only under this autonomous-development section and its safeguards.

### 8.4 Scope and decision authority

The agent may independently perform routine, reversible development work that is supported by the roadmap, established decisions, and documented acceptance criteria, including:

- Inspecting and modifying application code and tests within the active task's scope.
- Implementing planned features in dependency order.
- Fixing defects directly related to the active task.
- Updating relevant documentation and project-state records to reflect verified changes.
- Refactoring narrowly where necessary for the task, provided existing behavior is preserved and tests support the change.
- Running available tests, static checks, and other relevant validation.
- Investigating candidate providers, formats, and methods as specified in the roadmap, then documenting evidence and recommendations.

The agent must not silently make consequential decisions that lack adequate evidence. It must stop for human input when progress depends on decisions such as:

- Choosing between scientifically consequential methods when evidence does not resolve the choice.
- Introducing assumptions that materially change scientific interpretation or claims.
- Accepting an unresolved provenance, licensing, privacy, security, or data-integrity risk.
- Removing or destructively migrating user data, rewriting unrelated history, or overwriting unrelated user work.
- Changing the approved project scope or introducing a substantial new dependency or architecture without justification under the roadmap.
- Merging to a protected branch, publishing a release, deploying, spending money, or taking another externally consequential action without explicit authorization.
- Accepting a feature whose scientific validity or required verification remains unresolved.

When a decision can safely be deferred, document it and continue with independent work rather than stopping the entire workflow unnecessarily.

### 8.5 Repository safety and change management

- Preserve existing user changes. Never discard work simply to obtain a clean working tree.
- Use the repository's established branch conventions. Keep autonomous changes isolated from unrelated work.
- Do not use destructive commands or broad rewrites without a clear, task-specific justification.
- Do not commit, push, merge, publish, or deploy unless the repository's existing workflow explicitly authorizes that action and the required safety conditions are met. If uncertain, do not perform the external action.
- Never embed secrets, tokens, credentials, or private user data in source code, logs, tests, or documentation.
- Do not weaken tests, remove validation, suppress errors, or change acceptance criteria merely to make a task pass.
- Do not silently modify unrelated files. If an unrelated issue is discovered, record it for later unless it blocks the current task or creates an immediate risk.
- Keep changes incremental and inspectable. Avoid large batches of unrelated modifications.

### 8.6 Scientific integrity and evidence requirements

These requirements apply to every autonomous task, not only the original planning phase.

- Do not fabricate data, source references, provider capabilities, test results, review outcomes, or scientific conclusions.
- Preserve provenance and distinguish observed measurements, measured reference spectra, theoretical line lists, simulated spectra, processed data, and projections.
- Do not assume that two spectra are scientifically comparable merely because they can be displayed together.
- Do not treat spectral similarity or overlap as proof of molecular presence, atmospheric composition, or abundance.
- Do not implement forward modelling or projections without defined inputs, explicit assumptions, and a defensible validation strategy.
- Do not describe fixtures, synthetic test data, or internally consistent cached files as independent scientific validation.
- Distinguish code-level correctness, successful data retrieval, software verification, scientific validation, and human acceptance.
- If scientific evidence is inadequate, document the uncertainty and continue only with work that does not depend on the unresolved claim.

### 8.7 Testing and acceptance gates

For every task:

- Identify which tests and checks are applicable before implementation.
- Run the most relevant focused tests after changes.
- Run broader regression tests at appropriate milestones and before declaring a chunk complete.
- Add or update tests for new behavior, failure paths, and relevant regressions.
- Report actual command outcomes, including failures and skipped tests.
- Never claim that a test passed if it was not executed or if the result is ambiguous.
- Treat manual verification as outstanding until it is actually performed or the acceptance criteria are formally revised with justification.
- Treat independent review as outstanding until the review evidence exists.
- Do not mark a chunk complete or merge-ready until its documented acceptance criteria have been satisfied.

If a test or verification step cannot be run because of environment limitations, record exactly what could not be verified, why, and what remains necessary. Continue with independent tasks only when doing so will not conceal or compound the unverified issue.

### 8.8 Failure, uncertainty, and stop conditions

Stop the affected task and report a clear blocker when:

- Required evidence is unavailable and the missing information materially affects correctness.
- A scientific or architectural decision cannot be made responsibly from available evidence.
- A change risks damaging user work, corrupting data, or compromising repository integrity.
- Required permissions or tools are unavailable.
- A failure persists after a reasonable, evidence-driven diagnostic attempt.
- The only apparent path forward would violate the scope, safety boundaries, or acceptance criteria.

When blocked:

1. Record the exact blocker and supporting evidence.
2. Identify what has and has not been completed.
3. State the minimum decision, access, or verification needed to proceed.
4. Continue other independent, authorized tasks where safe and useful.
5. Do not repeatedly retry the same failed operation without a meaningful change in diagnosis or approach.

Do not stop the entire development roadmap because one independent task is blocked. Equally, do not bypass a blocker when downstream work depends on its resolution.

### 8.9 Persistent progress and handoffs

Maintain the existing authoritative project records rather than inventing a parallel tracking system.

As appropriate to the repository's conventions, record:

- Current chunk and task.
- Implementation status and acceptance status separately.
- Files and major components changed.
- Tests and checks executed, with actual results.
- Manual verification and independent review status.
- Decisions made and evidence supporting them.
- Outstanding uncertainties, risks, and blockers.
- Deferred work and its dependencies.
- The next eligible task and the conditions for starting it.

Update records at meaningful milestones and before ending a session. Do not repeatedly rewrite the entire roadmap after every small change.

The records must allow a future agent session to resume from the actual repository state without relying on conversational memory or assuming that an earlier task finished successfully.

### 8.10 Autonomous continuation and session limits

Continue working through eligible tasks in the established dependency order for as long as the execution environment permits.

Do not stop merely because one task has been completed, if the next task is clear, authorized, and safe to begin.

However:

- Do not claim to operate in the background or continue after the execution environment has ended unless the installed agent system explicitly supports that behavior.
- Do not assume that a prompt can override tool permission prompts, execution limits, session limits, or unavailable capabilities.
- If the environment pauses for a required confirmation, explain the precise intervention needed rather than implying that work is continuing.
- If nearing an execution or context limit, prioritize preserving the actual state, verification results, and next action so work can resume safely.

At the end of an autonomous run, provide a concise but complete report of work completed, actual verification results, unresolved issues, current acceptance status, and the next eligible task.

### 8.11 Definition of autonomous progress

Autonomous progress means the agent can move from one bounded, authorized task to the next, using documented dependencies and acceptance criteria, without routine human approval at every step.

It does **not** mean that the agent should:

- Declare success without evidence.
- Skip review or testing.
- Resolve unsupported scientific questions by guessing.
- Ignore blockers or tool limitations.
- Make irreversible or externally consequential changes without authorization.
- Mark partially completed or unverified work as complete.

The objective is sustained, incremental development with traceable decisions and verification—not unrestricted changes or artificial completion.

**Final objective:** Reconcile ECAS's current state and roadmap first, then progress autonomously through the eligible work in Chunks 4, 5, 5.1, and 6, and any justified follow-on tasks, while preserving scientific integrity, repository safety, accurate documentation, and verifiable acceptance criteria.
