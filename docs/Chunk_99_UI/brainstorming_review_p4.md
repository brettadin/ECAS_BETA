** This is the forth document related to the brainstorming process for the UI redesign. This is to keep a record of ideas as I work. **
** This document marks the point where I was given the redesign master roadmap for use. **
** See `/docs/Chunk_99_UI/ECAS_UI_Redesign_Master_Roadmap.md` or `/docs/Chunk_99_UI/ECAS_UI_Redesign_Master_Roadmap.docx` **

# ECAS UI and Scientific Workflow Redesign — Master Roadmap

The recommended approach is to treat this as a separate, long-running design and prototyping project for ECAS — Exoplanetary Characterization & Astrochemistry Suite, with its own branch, documentation, visual designs, and verification process. It should be developed so that changes to `ECAS_BETA` by your friend, Cline, or other contributors do not routinely interrupt your work.

The goal is not simply to reskin the current desktop application. It is to plan a coherent scientific workspace that brings together observational data, local spectroscopy files, molecular reference spectra, research projects, interactive visualization, and eventually defensible atmospheric-analysis workflows.

There are three important boundaries for this project:

1. Design the intended experience before committing to a large implementation. We should map existing features, future requirements, scientific workflows, and unresolved decisions before changing the interface.
2. Keep the redesign independent of the main application until integration is justified. Reuse existing scientific logic where practical, but do not make the side project depend on a permanently frozen copy of the main branch.
3. Keep scientific capabilities and interface affordances honest. A button, plot, search result, or menu item must reflect what the underlying system can actually do. A catalogue result is not necessarily downloadable, a plot overlay is not automatically a valid scientific comparison, and a simulated spectrum is not an observation.

The report should serve as a durable reference that can be revisited over months. It separates the current known context from proposed designs, future possibilities, and items that still require verification.

## Report files

ECAS UI Redesign Master Roadmap — Word

Editable document for reading, annotating, and maintaining over time.

Download the Word report

ECAS UI Redesign Master Roadmap — Markdown

Plain-text version suitable for Git, a project documentation folder, and future revisions.

Download the Markdown report

The report covers the project architecture, current-state cautions, workspace layouts, scratch and project workflows, data import, molecular references, analysis and transit visualization, customizable layouts, scientific safeguards, verification, phased development, integration with ongoing mainline work, and a prioritized wishlist. It also includes external references to scientific software, astronomy archives, spectroscopy libraries, and Qt documentation.

## Recommended next step

Start with Phase 0 and Phase 1 in the report: establish the isolated workspace, then build the capability inventory from the current codebase. Do not begin a broad UI rewrite yet.

That inventory is the foundation for everything else. It will establish what the redesigned interface must preserve, what can be reused, what needs adaptation, and what is genuinely new. It will also make it much easier to incorporate your friend's future changes without having to restart the design project.

The report is a planning baseline, not a verified audit of every current repository file. The next stage should reconcile it against the latest code and documentation before turning its recommendations into implementation tasks.