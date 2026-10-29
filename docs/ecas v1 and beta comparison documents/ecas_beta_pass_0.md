# ECAS Beta review — Review plan

The Beta archive is available and passed its ZIP integrity check. It contains 720 entries, including application source, tests, architecture documentation, Chunk 4 planning and verification records, and dated NASA and ExoMol data snapshots.

I will use the same staged review method as v1, but tailor it to Beta's actual architecture and development history. The goal is to understand what changed from v1, what Beta currently implements, and whether the implementation, tests, and documentation agree.

## Review structure

## A

Architecture and application structure

Inspect the entry points, package layout, major subsystems, dependencies, and module boundaries. Establish how Beta differs structurally from v1.

First pass

## B

Functional capabilities and workflows

Trace the implemented user journeys: importing spectra, working with projects, discovering astronomical observations, browsing molecular references, comparing spectra, and accessing results.

## C

Scientific and numerical implementation

Review spectrum representation, units, comparison eligibility, alignment, molecular reference handling, scientific assumptions, and how results are interpreted.

## D

Data ingestion, storage, and provenance

Examine supported formats, NASA and ExoMol data pathways, cached resources, project persistence, source attribution, and whether data retain sufficient context for reproducibility.

## E

UI and usability

Assess import controls, project management, comparison workflows, molecular browsing, errors and warnings, feedback, and the clarity of scientific results.

## F

Testing, reliability, and maintainability

Inspect test coverage and recorded verification results, dependency assumptions, error handling, regressions, and maintainability risks. Clearly distinguish recorded results from tests independently run during this review.

## G

Documentation and intended behavior

Compare the README, project state, architecture documents, approved decisions, and Chunk 4 records against the implementation. Separate historical plans from current verified behavior.

## How each pass will work

For each pass, I will:

1. Inspect the relevant Beta source files and documentation.
2. Identify implemented behavior and its supporting evidence.
3. Record confirmed defects separately from potential risks and unanswered questions.
4. Explain the implications for ECAS's scientific purpose and future development.
5. Present the findings and pause for discussion before proceeding to the next pass.

At the end of Pass G, I will consolidate the findings into an overall Beta assessment and distinguish them from the v1 findings.

## Additional controls specific to Beta

Beta has a much larger documentation and data footprint than the v1 archive. Its ZIP contains extensive `docs/Chunk_4/` planning records, historical verification logs, and dated NASA and ExoMol resources. I will therefore apply four additional controls:

- Current source versus historical plans: a proposed feature or old issue will not be treated as current behavior without checking the implementation.
- Recorded versus independently verified tests: archived test logs will be treated as historical evidence, not as proof that the current code passes.
- Real data versus test fixtures: included astronomical and molecular data will not automatically be treated as scientifically validated reference material.
- Beta versus v1: changes will be described as improvements, regressions, or unresolved differences only where the evidence supports that classification.

The review is read-only. No implementation changes are authorized or planned as part of these passes.

## Pass A — Immediate scope

I will begin with:

- `app.py`, `main.py`, and any alternate or backup entry points.
- The `ecas/` package and its major subpackages.
- `requirements.txt`, `requirements-test.txt`, `pytest.ini`, and packaging/build configuration.
- `docs/architecture/` and `docs/brains/PROJECT_STATE.md`.
- Relevant architectural decisions in `docs/brains/DECISIONS.md`.

I will establish the actual application structure and startup path before tracing detailed workflows in Pass B.

Next step: Pass A, architecture and application structure.