** This is the very first prompt I will hand to an AI to begin working on this project. This is just for the start of this project, and it doesnt need to be used for future agents. This is just to get the ball rolling. **


# ECAS UI Redesign — Master Project Prompt

## 1. Role and project context

You are my AI design and development partner for an independent UI/UX redesign of **ECAS — Exoplanetary Characterization & Astrochemistry Suite**.

Main repository: https://github.com/brettadin/ECAS_BETA

My local project ZIP represents the version currently on my PC. Treat the actual files in that project as the primary source for its current state. The repository may have advanced beyond older planning documents or previously discussed implementation stages.

I created `docs/Chunk_99_UI/` specifically for this UI redesign. It contains four brainstorming/review documents and two roadmap documents. Read and use those materials before proposing a direction.

This is a separate design and prototyping track. The main ECAS application may continue evolving while the redesign proceeds. The goal is to develop a coherent, well-reasoned UI that can eventually be integrated into the main application without unnecessarily disrupting existing functionality.

Do not assume that I will use Cline for this work. I may use another AI, another development environment, or a mixture of tools. Your instructions and plans must therefore be tool-agnostic unless I specify otherwise.

## 2. Mandatory working principles

- Work in small, controlled, reviewable stages.
- Investigate before proposing changes.
- Produce a concrete plan before implementation.
- Wait for my approval before beginning each substantive implementation stage.
- Prefer incremental changes over large rewrites.
- Preserve working functionality unless a change is explicitly approved and justified.
- Distinguish verified facts, documentation claims, assumptions, inferences, and proposals.
- Never claim that you inspected a file, ran a test, viewed a screen, or verified a feature unless you actually did so.
- Do not treat a successful automated test as proof that the GUI looks or behaves correctly.
- Do not silently resolve conflicting documentation by choosing whichever version seems most plausible. Identify the conflict and investigate the current code or authoritative project records.
- Do not assume that a feature described in a roadmap is already implemented.
- Do not assume that a feature is absent merely because it is not documented.
- Keep scientific correctness, data provenance, and capability boundaries central to UI decisions.
- Avoid speculative infrastructure, unnecessary dependencies, and premature abstraction.
- Do not expand the scope just because an idea might be useful in the future.
- Include many comments in the code to help future workers understand context of coding blocks. Whether human or AI. 

## 3. Start by reading the actual project materials

### A. Read the complete UI redesign folder

Start with the actual contents of:

`docs/Chunk_99_UI/`

Read all six documents:

- `brainstorming_review_p1.md`
- `brainstorming_review_p2.md`
- `brainstorming_review_p3.md`
- `brainstorming_review_p4.md`
- `ECAS_UI_Redesign_Master_Roadmap.md`
- `ECAS_UI_Redesign_Master_Roadmap.docx`

Verify the filenames against the directory listing rather than assuming they exist exactly as written. If a name differs, use the actual filename and report the discrepancy.

Read the four brainstorming documents in their intended order. Read both roadmap formats and determine whether they agree on important details. Treat the Markdown version as the convenient working reference, but do not assume the Word version is identical without checking.

Extract the original design goals, proposed workflows, outstanding questions, constraints, rejected or tentative ideas, and any decisions already made. Preserve distinctions between settled decisions and brainstorming.

### B. Read the current project documentation

Start with the repository's actual `README.md` and follow its links to the current project records.

At minimum, investigate these known paths if they exist:

- `docs/REVIEW_CHECKPOINT_20261028.md`
- `docs/brains/PROJECT_STATE.md`
- `docs/brains/DECISIONS.md`

Then identify and read the relevant current architecture, development checkpoint, implementation, verification, and handoff documents.

Review the current documentation for **all relevant work through the present project state, including Chunk 5 and Chunk 5.1**. Do not stop at Chunk 4 or treat an older handoff as the current status.

Use the repository's actual documentation structure to identify the authoritative records for completed work, current work, pending reviews, known limitations, and planned work. Do not invent document paths or expect me to provide unrelated conversation excerpts as repository files.

If a referenced file is missing, report that fact and continue using available sources. Do not substitute a similarly named file without explaining the substitution.

### C. Inspect the actual application

After reviewing the documentation, inspect the source code to establish the real state of the application.

Determine:

- The application entry point and startup sequence.
- The UI framework, plotting framework, and relevant dependencies.
- The current window structure, navigation, panels, dialogs, tables, plots, and layout behavior.
- The relationship between UI components, domain logic, services, data models, persistence, and external providers.
- The current import and data-validation workflows.
- The current project creation, selection, attachment, saving, reopening, and provenance workflows.
- The molecular-reference catalogue and the scope of supported retrieval.
- Current analysis and plotting capabilities.
- Existing UI tests, service tests, integration tests, and documented manual acceptance procedures.
- Known limitations and outstanding defects relevant to the redesign.

Trace important UI workflows into their underlying code where practical. A visible control does not establish that the corresponding workflow is fully implemented.

Do not conduct an indiscriminate audit of every source file. Prioritize code that establishes the current architecture, existing capabilities, and integration constraints for the redesign.

## 4. Establish a trustworthy baseline

Before recommending implementation work, record the baseline that you can actually verify:

- Repository location and project version.
- Current branch and commit, if accessible.
- Working-tree state, if accessible.
- Application entry point and startup method.
- Dependency and environment information relevant to running the application.
- Relevant test suites and documented test commands.
- Whether the application can be launched in the available environment.
- Whether the current UI can be inspected visually.
- Any access limitations preventing verification.

The supplied ZIP is a snapshot of local project files. Do not infer from the ZIP alone that a particular change is committed, that the live working tree is clean, or that the local environment works.

If you cannot inspect Git state, launch the application, or run tests, say so explicitly. Continue with the evidence that is available.

## 5. Design objective

Develop a modern, coherent, scientifically reliable interface for ECAS that improves usability and supports the project's actual and planned scientific workflows.

The UI redesign should consider, where justified by the current capabilities and roadmap:

- A clear application information architecture and navigation system.
- Search and target discovery.
- Data import, validation, inspection, and provenance.
- Scratch or temporary investigations alongside durable project-based work.
- Molecular-reference discovery, retrieval, caching, and metadata inspection.
- Analysis workspaces with useful plot, table, trace, and metadata layouts.
- Reusable analysis and visualization tools.
- Configurable panels and workspaces without making the interface difficult to recover.
- Clear distinction between observations, simulations, reference data, derived products, and model outputs.
- Accessible typography, contrast, status indicators, and interaction states.
- Useful error messages, progress feedback, and recovery paths.
- Future growth without designing as though all potential features already exist.

These are areas to investigate and design, not a requirement to implement every item. Prioritize based on the actual code, established project goals, user workflows, scientific validity, and implementation cost.

### Scratch work and projects

Evaluate whether ECAS should support both:

1. A temporary investigation that can be started quickly without requiring a full project setup.
2. A persistent project that retains selected data, settings, analysis outputs, and provenance.

If this model is adopted, determine how a scratch investigation could be promoted into a project without losing relevant work or creating ambiguous copies of scientific data.

Do not introduce a second persistence system or duplicate domain models without first assessing the existing architecture.

### Configurable layouts

Evaluate progressive levels of customization, beginning with simple and reliable behavior such as resizing panels, showing or hiding secondary areas, and restoring defaults.

More advanced docking, floating panels, saved presets, and workspace-specific layouts should be justified by actual workflows and the capabilities of the current UI framework.

Layout customization must not compromise essential navigation, data integrity, reproducibility, or the user's ability to recover a usable interface.

### Scientific reliability

The UI must accurately communicate what the application can and cannot do.

For example:

- Do not imply that a reference spectrum is an observed planetary spectrum.
- Do not conflate molecular cross sections with observed transit depth.
- Do not present two datasets as scientifically comparable merely because both can be plotted.
- Do not silently infer unknown units or incompatible axis conventions.
- Distinguish raw data, normalized data, simulated data, derived products, and model results.
- Show meaningful metadata, provenance, limitations, and units where relevant.
- Make unsupported or incomplete capabilities visible rather than presenting misleading controls.

Treat these as constraints to validate against the existing scientific implementation, not assumptions that every listed distinction already has a corresponding feature.

## 6. Investigate the existing transit-analysis UI as a reference

The earlier ECAS repository may contain transit-related UI and visualization work that could inform the redesign.

If the earlier repository or its relevant source files are accessible, inspect the actual implementation before drawing conclusions. Use the original repository as a behavioral reference, not as an automatic source of code to copy.

Investigate, where present:

- Light-curve visualization and controls.
- Shared time selection or synchronized playback.
- Observer and orbital visualizations.
- Spectrum-at-time behavior.
- Phase-folded data.
- Transmission-depth calculations and display.
- Residual and noise diagnostics.
- Model-versus-observation distinctions.
- Optional visualization dependencies and fallback behavior.
- Relevant data models and scientific transformations.

Compare these capabilities with the current ECAS_BETA implementation and roadmap.

For every relevant capability, identify whether it is:

- Implemented in the earlier project.
- Implemented in the current project.
- Partially implemented.
- Planned but not implemented.
- Not verified.

Explain what behavior is worth preserving, what needs redesigning, what depends on scientific or architectural changes, and what should not be transplanted.

Do not copy the earlier UI wholesale or assume its underlying models and services are compatible with the current architecture.

If the earlier repository is unavailable, state that limitation and defer conclusions requiring source inspection.

## 7. Architecture and integration strategy

The redesign must be developed independently enough to permit exploration without destabilizing the main application.

Recommend an isolation strategy appropriate to the repository and available tools. Consider a separate branch or worktree, a standalone prototype, or another controlled approach. Explain the trade-offs rather than automatically choosing the most elaborate option.

Before implementation, identify:

- Which existing services and domain models can be reused.
- Which UI elements can be redesigned without changing scientific logic.
- Which changes would require service or model modifications.
- Which interfaces should remain stable during parallel development.
- Which assumptions may be invalidated by ongoing mainline changes.
- How changes will be reconciled with the current application.
- How to avoid duplicated logic, divergent data models, and a prototype that cannot be integrated.
- How to keep unrelated development changes out of the redesign.

Prefer mock data and adapters for early prototypes when they allow meaningful interaction design without requiring changes to production behavior. Clearly mark simulated functionality so it cannot be mistaken for a working scientific feature.

Do not create a scaffold, alter the repository, create branches, or begin implementation during the initial audit.

## 8. Required initial audit deliverable

After the investigation, produce a structured report with the following sections.

### 1. Executive summary

Summarize the current UI, the main opportunities for improvement, the key constraints, and the recommended design direction.

### 2. Source and documentation audit

List the files actually read, their roles, and any important conflicts or gaps.

Distinguish current authoritative documentation from historical or superseded records.

Do not list files as read unless you actually read them.

### 3. Current project baseline

Report the verified repository, version, branch, commit, working-tree, environment, launch, and testing information that was accessible.

Mark unavailable or unverified items clearly.

### 4. Current UI inventory

Describe the actual windows, navigation, panels, tables, plots, dialogs, and workflows. Map important UI elements to their underlying implementation where practical.

Identify usability problems only when supported by source inspection, visual inspection, tests, documentation, or clearly labeled hypotheses.

### 5. Capability and workflow matrix

For each relevant workflow, record:

- Current implementation status.
- Supporting source files or documentation.
- Existing limitations.
- Scientific or data-integrity constraints.
- Potential UI improvements.
- Dependencies and risks.
- Verification still required.

Include target discovery, data import and validation, project workflows, scratch work, molecular references, analysis, saving and reopening, and layout recovery where relevant.

### 6. Transit-reference assessment

Summarize the verified behavior of the earlier transit UI, its relevance to the current application, the differences between the two implementations, and the components or behaviors worth considering for redesign.

Explicitly identify anything that could not be verified.

### 7. Proposed information architecture

Recommend a navigation structure and workspace organization grounded in actual requirements.

Explain the purpose of each proposed area and which capabilities belong there. Identify unresolved decisions instead of presenting tentative ideas as settled.

### 8. Visual and interaction design direction

Describe the proposed design language, layout principles, data density, responsive behavior within the desktop application, interaction patterns, accessibility considerations, and layout-customization strategy.

Avoid committing to detailed visual styling before the core workflows and information architecture are sufficiently understood.

### 9. Architecture and isolation recommendation

Explain how to develop and evaluate the redesign separately, preserve compatibility with the evolving main application, and integrate it incrementally.

Identify likely integration boundaries and any questions that must be resolved first.

### 10. Prioritized roadmap

Propose small, reviewable stages. For each stage, specify:

- Objective.
- Scope.
- Dependencies.
- Expected deliverables.
- Acceptance criteria.
- Verification method.
- Risks and out-of-scope work.

Separate discovery, requirements, wireframes, visual design, prototype, integration investigation, production implementation, and validation.

Do not schedule every wishlist item as committed work.

### 11. Open questions and decisions

List only questions that materially affect the next steps. Explain which can be deferred and which require my decision.

### 12. Recommended next action

Recommend **one specific next work item** that provides useful progress with limited risk. Explain its scope, deliverable, and completion criteria.

Do not begin that work until I review and approve the audit.

## 9. Research and evidence standards

Use the project itself as the primary source for current implementation facts.

Use external research selectively when it can answer a concrete question about UI architecture, scientific workflows, visualization, accessibility, or relevant astronomy resources.

Prefer official documentation and primary sources. Community discussions may help identify practical issues, but distinguish those observations from verified facts.

Keep external research focused during the initial audit. Do not spend time producing an enormous catalogue of libraries or features before the requirements and architecture are understood.

When presenting findings, distinguish:

- **Verified:** directly established by source code, executed tests, inspected UI, or other concrete evidence.
- **Documented:** stated in project documentation but not independently verified.
- **Inferred:** a reasoned conclusion from available evidence.
- **Proposed:** a recommendation for future work.
- **Unknown:** insufficient evidence.

Cite relevant repository paths, test names, source references, or external sources so findings can be checked.

## 10. Implementation protocol after the audit

Once I approve a proposed work item, use this sequence:

1. Confirm the exact scope and acceptance criteria.
2. Inspect the specific files and dependencies affected.
3. Present a concise implementation plan and identify risks.
4. Wait for approval if the plan changes scope or introduces consequential design decisions.
5. Implement only the approved work.
6. Review the complete diff for correctness, unintended changes, and scope creep.
7. Run relevant tests and checks where possible.
8. Inspect the actual GUI when the change affects visible behavior, if the environment permits.
9. Report what changed, what was tested, what was not tested, known limitations, and any follow-up work.
10. Update appropriate project documentation only when that documentation change is within the approved scope.

Keep each implementation slice small enough that it can be understood, reviewed, and reverted independently.

If a dependency, architecture change, or unexpected defect substantially expands the scope, stop and report the issue before proceeding.

## 11. Definition of success

The redesign should eventually produce:

- A coherent information architecture based on real scientific workflows.
- A consistent, accessible, and maintainable visual system.
- Clear data, project, and analysis workflows.
- Accurate representation of scientific capabilities and limitations.
- Useful inspection, plotting, and metadata experiences.
- A practical approach to temporary investigations and persistent projects, if justified.
- Configurable layouts that remain recoverable and predictable.
- A standalone prototype that demonstrates meaningful workflows without pretending to be production software.
- An integration plan aligned with the current application architecture.
- Incremental production changes supported by appropriate automated and manual verification.
- Documentation that accurately reflects the implemented state.

The objective is not to build the largest possible feature set. It is to create the most useful and scientifically trustworthy interface that can be integrated and maintained alongside the evolving ECAS project.

## 12. Your first response

Begin with the read-only audit.

First, inspect `docs/Chunk_99_UI/` and the current project's linked documentation. Then establish the baseline and inspect the relevant source code.

Do not modify files, create branches, scaffold a prototype, or implement anything.

Return the complete initial audit described above, with evidence and explicit uncertainty labels. End with one recommended next work item and its acceptance criteria.

Wait for my review before proceeding.