# ECAS Architecture Specification — Draft 0.3

**Status:** For review  
**Implementation status:** No implementation authorized  
**File status:** This draft is a working specification; it does not authorize creating or modifying project files.

## 1. Purpose

ECAS is a Python desktop application for comparing exoplanet transmission spectra with molecular spectral references to support atmospheric characterization.

The application should retrieve and cache real exoplanet observations and molecular reference data, preserve their provenance, and compare selected molecular references against observations. A project is organized around one planet and can contain multiple observations, analyses, and comparisons.

ECAS must distinguish evidence of spectral correspondence from a confirmed molecular detection. Spectral overlap alone is not proof of a molecule's presence. Results should expose assumptions, uncertainty, data limitations, and the sources behind every input.

## 2. Confirmed decisions

| Topic | Decision |
|---|---|
| Application form | Native-style Python desktop window |
| Desktop UI framework | Recommend after reviewing dependencies and requirements; not selected yet |
| Launch method | One-click desktop shortcut or equivalent launcher |
| Persistence | SQLite for structured records, plus files for larger datasets and artifacts |
| Initial observation type | Exoplanet transmission spectra |
| Molecular references | Support measured/experimentally derived spectra and theoretical spectroscopic line lists, handled distinctly |
| First analysis method | Spectral comparison and candidate scoring |
| Validation | Use published detections and suitable non-detections or control cases |
| Validation thresholds | Derive from benchmark evidence, metric uncertainty, and intended use |
| Offline behavior | Saved projects and cached inputs must work offline; new downloads and refreshes generally require internet |
| Project organization | One project per planet, with multiple observations and analyses |
| Standalone packaging | Defer until the workflow stabilizes |
| UI design | Keep the first interface simple; refine detailed design later |
| Implementation authorization | No file creation/modification or code implementation until explicitly authorized |

## 3. Initial user workflow

The initial workflow should support the following sequence:

1. Select or find an exoplanet.
2. Review available transmission-spectrum observations and their metadata.
3. Retrieve an observation or open a previously cached one.
4. Select molecular references from the local library or retrieve them from supported sources.
5. Check whether the observation and reference data are suitable for comparison.
6. Run spectral comparison and calculate candidate scores.
7. Review plots, scores, limitations, and source information.
8. Compare results with relevant benchmarks where supported.
9. Save the analysis to the planet's project so it can be inspected or rerun later.

The interface should not hide failed checks, incompatible data, missing metadata, or important assumptions.

## 4. Proposed project structure

The following is a **proposed target structure**, not an instruction to create every listed file or folder. The architecture-planning phase should simplify or combine modules where doing so improves clarity and maintainability.

```text
ECAS/
├── docs/
│   ├── ECAS.md
│   ├── architecture/
│   │   ├── ARCHITECTURE.md
│   │   ├── DATA_FLOW.md
│   │   ├── MODULE_RESPONSIBILITIES.md
│   │   ├── DATA_MODELS.md
│   │   ├── VALIDATION_STRATEGY.md
	│ 	└── ARCHITECTURE_SPECIFICATION.md
│   └── brains/
│       ├── PROJECT_STATE.md
│       ├── DECISIONS.md
│       └── agents/
├── src/
│   └── ecas/
│       ├── __init__.py
│       ├── __main__.py
│       ├── app.py
│       ├── core/
│       │   ├── settings.py
│       │   ├── paths.py
│       │   ├── logging_config.py
│       │   └── exceptions.py
│       ├── data/
│       │   ├── sources.py
│       │   ├── ingestion.py
│       │   ├── validation.py
│       │   ├── cache.py
│       │   ├── metadata.py
│       │   └── storage.py
│       ├── molecules/
│       │   ├── models.py
│       │   ├── catalog.py
│       │   └── references.py
│       ├── exoplanets/
│       │   ├── models.py
│       │   ├── catalog.py
│       │   └── observations.py
│       ├── spectroscopy/
│       │   ├── models.py
│       │   ├── units.py
│       │   └── preprocessing.py
│       ├── analysis/
│       │   ├── models.py
│       │   ├── comparison.py
│       │   ├── scoring.py
│       │   └── results.py
│       ├── validation/
│       │   ├── benchmarks.py
│       │   ├── metrics.py
│       │   └── evaluation.py
│       ├── projects/
│       │   ├── models.py
│       │   ├── manager.py
│       │   └── serialization.py
│       ├── visualization/
│       │   ├── spectra.py
│       │   └── comparisons.py
│       ├── reporting/
│       │   └── citations.py
│       └── ui/
│           ├── app.py
│           ├── state.py
│           └── views/
│               ├── planet_view.py
│               ├── library_view.py
│               ├── analysis_view.py
│               └── project_view.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── validation/
│   └── fixtures/
├── data/
│   ├── cache/
│   ├── projects/
│   └── validation/
├── config/
├── logs/
├── scripts/
├── .gitignore
├── README.md
└── pyproject.toml
```

## 5. Architectural responsibilities

These are conceptual responsibilities. Exact file boundaries and public interfaces remain open for review.

| Area | Responsibility |
|---|---|
| `core` | Shared settings, path handling, logging, and application-level exceptions |
| `data` | Source adapters, downloading, ingestion, metadata normalization, validation, caching, and storage coordination |
| `molecules` | Molecule identity and catalog records; discovery and handling of molecular reference datasets |
| `exoplanets` | Planet records, discovery, observation listings, and observation metadata |
| `spectroscopy` | Spectral data structures, units, comparability checks, and preprocessing |
| `analysis` | Comparison methods, scoring, analysis records, and result representation |
| `validation` | Benchmark definitions, evaluation metrics, and validation runs |
| `projects` | Planet-project lifecycle, persistence, and project serialization |
| `visualization` | Plot construction for spectra and comparisons |
| `reporting` | Source attribution and citation details for displayed and exported results |
| `ui` | Desktop views, user interaction, and presentation of application state |
| `tests` | Unit, integration, and benchmark/validation tests |

### Dependency rules

- The UI must not contain scientific analysis logic.
- Scientific calculations should be independently testable without launching the desktop interface.
- Source-specific logic should remain isolated in source adapters rather than spreading through the application.
- Analysis should be repeatable offline when all required inputs and reference data are cached.
- Storage and data retrieval should not silently alter the scientific meaning of an input.
- Visualization should display analysis outputs rather than independently recompute scientific conclusions.
- Module boundaries should be justified by clear responsibilities; avoid unnecessary abstraction and excessive numbers of tiny modules.

## 6. Molecular reference data

ECAS must support two distinct reference categories.

### 6.1 Measured or experimentally derived spectra

These datasets originate from measurements or experimentally derived spectral products. Preserve available information about:

- Source and citation.
- Measurement conditions, such as temperature, pressure, path length, and sample state where provided.
- Spectral axis and units.
- Signal type and units.
- Resolution and instrumental conditions, where available.
- Uncertainty, quality flags, and known limitations.
- Whether the data are raw, calibrated, normalized, or otherwise processed.

Do not assume that measurements taken under different conditions are directly interchangeable.

### 6.2 Theoretical spectroscopic line lists

Line lists describe transitions and associated spectroscopic parameters rather than necessarily providing a directly measured, continuous spectrum. Comparing them with an observation may require generating a modeled spectrum using line profiles and assumptions about conditions such as temperature, pressure, broadening, and resolution.

ECAS must preserve the distinction between:

- The original theoretical line list.
- The assumptions and parameters used to synthesize a spectrum.
- The resulting synthesized spectrum.
- Any subsequent processing applied before comparison.

A synthesized spectrum must never be labeled as a direct experimental measurement.

### 6.3 Candidate data sources

Potential sources to assess include HITRAN, ExoMol, the NIST Chemistry WebBook, the NASA Exoplanet Archive, and MAST. These are candidates for investigation, not a commitment to support every source in the first release. The initial provider list should follow the chosen benchmarks and their actual data requirements.

## 7. Spectral data and comparability

A spectral dataset should retain, where available:

- Wavelength or wavenumber coordinates, with units.
- Signal values, with an explicit description of what they represent and their units.
- Uncertainties, error estimates, and quality flags.
- Instrument and observation metadata.
- Source identifiers, version information, retrieval time, and provenance.
- Processing history and whether the data are original, processed, or synthesized.

ECAS must not treat transmission depth, normalized transit spectra, flux, absorbance, molecular cross-sections, and other spectral quantities as interchangeable. Before comparison, the application should check axis units, signal meaning, spectral coverage, resolution, normalization, uncertainty availability, and other relevant compatibility conditions.

Any resampling, normalization, smoothing, resolution matching, or other preprocessing must be explicit and recorded. Preserve the original input separately from derived data.

## 8. Conceptual data models

The following are proposed concepts, not final class definitions or database schemas:

- **Planet:** stable identity and relevant catalog metadata.
- **Project:** one planet's workspace, containing observations, analyses, and project-specific notes or settings.
- **Observation:** an observed transmission spectrum plus metadata, source references, and data-quality information.
- **Molecule:** stable molecular identity and useful identifiers.
- **ReferenceDataset:** a measured spectrum or theoretical line list, with its category, provenance, conditions, version, and limitations.
- **AnalysisRun:** inputs, method, configuration, software version, processing steps, and execution metadata for a comparison.
- **CandidateResult:** a candidate molecule's score, supporting evidence, uncertainty or limitations, and links to the relevant inputs.
- **BenchmarkCase:** a documented validation case based on a published detection, non-detection, or suitable control.
- **ValidationRun:** benchmark set, evaluation method, metric results, and the configuration used.

The detailed architecture phase should establish relationships, identity rules, and minimum required fields before implementation.

## 9. Projects, persistence, and provenance

Use SQLite for structured application records and files for larger datasets or artifacts. Exact schemas and migration tooling remain unresolved.

A project is organized around one planet and may contain multiple observations and analysis runs. Shared molecular references should live in a central cache/library rather than being redundantly copied into every project. Projects should record which specific cached reference versions and observation versions were used.

For each analysis, retain enough information to understand and reproduce its result, including as applicable:

- Exact input observation and reference dataset identifiers and versions.
- Source links and citation metadata.
- Preprocessing steps and parameters.
- Comparison method and scoring configuration.
- Relevant assumptions and compatibility checks.
- Application/software version.
- Output metrics, candidate results, warnings, and limitations.

Refreshing a dataset must not silently change the inputs associated with a previous analysis. A previous result should remain traceable to the exact data and settings that produced it.

## 10. Offline behavior

The following operations should work without an internet connection when the necessary inputs are already saved:

- Open and browse existing planet projects.
- Inspect saved observations, plots, analysis results, and citations.
- Rerun analyses using cached observations, references, and settings.
- Compare against locally available molecular references.
- Run validation against locally cached benchmark data.

Searching for new observations, downloading new references, and refreshing remote data generally require internet access. The UI should make unavailable online actions clear rather than failing silently.

## 11. Analysis and scientific interpretation

The first analysis capability is spectral comparison with candidate scoring. The exact comparison method remains undecided pending review of realistic observations, resolution, noise, spectral coverage, and reference data.

The application should communicate levels of evidence distinctly. A spectral match or high score is a candidate result, not automatically a confirmed detection or quantitative abundance estimate. Scores should not be described as probabilities unless they are calibrated and validated for that interpretation.

The architecture should support future methods without requiring the first release to implement full atmospheric retrieval, abundance estimation, or advanced uncertainty analysis. Those are deferred capabilities.

## 12. Validation strategy

Validation should use published detections and suitable non-detections or control cases. The initial benchmark shortlist should prioritize cases with accessible data, documented scientific conclusions, and enough metadata to support a defensible comparison.

Thresholds should not be selected arbitrarily. Derive them from benchmark performance, uncertainty in evaluation metrics, the consequences of false positives and false negatives, and the intended scope of the application. Report limitations and avoid implying broader validation than the evidence supports.

The detailed validation plan should define:

- Benchmark inclusion criteria and citations.
- Separation between development/tuning cases and evaluation cases where feasible.
- Metrics appropriate to the intended candidate-scoring task.
- Treatment of incomplete, ambiguous, or conflicting published evidence.
- How non-detections and controls are used.
- What conclusions the benchmark results do and do not support.

## 13. Desktop UI and dependencies

The UI framework has not been selected. The architecture-planning phase should compare suitable candidates based on:

- Native-style Windows desktop experience.
- Compatibility with the scientific Python stack and plotting.
- Maintainability, community support, and licensing.
- Accessibility and practical layout options.
- Packaging prospects, without treating packaging as a current deliverable.
- Ability to keep UI state and presentation separate from scientific calculations.
- Dependency size and complexity.

The recommendation should be evidence-based and include trade-offs. Do not install frameworks, create prototypes, or begin UI implementation during the review phase.

## 14. Remaining unresolved decisions

### Resolve during detailed architecture planning

1. **Initial benchmark targets and publications.** Identify a shortlist of documented detections, non-detections, and controls that can realistically be accessed and evaluated.
2. **First comparison and scoring method.** Choose a method based on the characteristics and limitations of the available benchmark data and references.
3. **Initial data providers and formats.** Survey the selected benchmark observations and determine the minimum set of providers and file formats required for the first workflow.
4. **Minimum reproducibility record.** Define the inputs, versions, settings, processing history, and outputs that must be retained for every analysis.
5. **Expected data volume and performance.** Estimate the scale of initial datasets and define practical expectations for loading, plotting, caching, and analysis.
6. **Desktop UI framework.** Compare candidates and recommend one after reviewing the dependency and workflow requirements.

### Defer until the workflow is better established

- Final database schema and migration strategy.
- Detailed cache refresh, invalidation, and retention policy.
- Final graph styling and detailed UI design.
- Standalone packaging and installer decisions.
- Full atmospheric retrieval and quantitative abundance estimation.
- Advanced uncertainty methods beyond what the initial benchmarked comparison requires.

## 15. Agent workflow and documentation rules

Agents working on ECAS must:

1. Read `docs/ECAS.md`, relevant architecture documents, `docs/brains/PROJECT_STATE.md`, and `docs/brains/DECISIONS.md` when those files exist.
2. Inspect the actual workspace before assuming that files, modules, tests, or infrastructure exist.
3. Distinguish clearly between proposals, completed changes, and results that have been verified.
4. Respect established module ownership and dependency boundaries. Avoid creating duplicate infrastructure.
5. Identify conflicts with approved decisions and propose a resolution before making changes outside their assigned scope.
6. Maintain a unique agent log under `docs/brains/agents/`, using a unique identifier and the actual date. Do not fabricate dates or overwrite another agent's history.
7. Record the assignment, context inspected, findings, actual changes, rationale, test evidence, unresolved issues, and handoff.
8. Update `PROJECT_STATE.md` only with verified current facts. Agent logs are historical records and do not override approved decisions.
9. Preserve scientific provenance, reproducibility, and uncertainty information in any data-related work.
10. Stop and request review when work exceeds its authorization or requires a material architectural decision.

### Documentation hierarchy

- `docs/ECAS.md` defines the project's purpose and governing principles.
- Approved architecture documents and recorded decisions govern design choices.
- `docs/brains/PROJECT_STATE.md` records the verified current state.
- `docs/brains/DECISIONS.md` records approved decisions and their rationale.
- Individual agent logs preserve task history and evidence; they do not independently change project requirements.

## 16. Next planning deliverable

The next planning phase should produce a reviewed architecture package containing:

- `ARCHITECTURE.md` — system boundaries and major design decisions.
- `DATA_FLOW.md` — flow from source retrieval through caching, preprocessing, comparison, validation, and project persistence.
- `MODULE_RESPONSIBILITIES.md` — module ownership, dependencies, and interfaces.
- `DATA_MODELS.md` — conceptual entities, relationships, and minimum data requirements.
- `VALIDATION_STRATEGY.md` — benchmark criteria, shortlist, evaluation metrics, and limits of interpretation.
- A desktop UI framework recommendation with evidence and trade-offs.
- A shortlist of benchmark targets/publications.
- A list of initially supported data providers and formats.

This phase is for inspection and planning only. It must not create or modify project files, install dependencies, or implement code unless the user explicitly authorizes those actions.

## 17. Governing principle

ECAS should prioritize **traceable scientific evidence, provenance, reproducibility, modularity, and transparent uncertainty** over apparent certainty or unnecessary architectural complexity.

The remaining central task is to establish the first benchmark and comparison method. Those decisions will determine what the initial data models and interfaces actually need to support, avoiding an architecture that looks complete but is built around the wrong scientific workflow.
