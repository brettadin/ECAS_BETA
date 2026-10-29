This is planned to be a very extensive document.
I tasked the same AI chat to consider what we can do to bring all the best parts of both programs together, what can be improved on, what we can do to set up foundational stuff if we wanted to revise the program from the ground up. I asked for resources, guidelines, references, logic, reasoning / explinations of all material that may be needed.
The goal of this was to create an overarching plan of what still can be done and improved upon as we progress in the development, and potential next steps to take to either improve the beta, or build a new program from the ground up with a more refined approach.
<br>

Here is my exact message to the ai: 

Now for one last request
Lets say we wanted to improve either the beta version, or revise the entire program from the floor up

What would be the best approach? How do we pull all the good parts from each version?
Like, good ui design. 
v1 looked cleaner in some parts, and had fun elements like the identify tab and the transit modeling/animations. but its not the focus of the beta capabilities so we dont have that.
how do we make reliable documentation creation and updating as we work?
What tools should we work with to make the program work as we want to the best of its capabilities?
What sources/libraries/databases/reference programs should we consult to do this? 
Should we consider more languages, not just python? For any kind of functionality, without making it a mess.
How can we keep the user experience manageable and easy? without overloading them with variables and options, but with the ability to enable more fine tuning when they want it.
How do we bring these versions together, make them better, and still work toward building a even more comprehensive, scientifically sound, user friendly, powerful and reliable program?
Please suggest anything that should be considered for this overall task.
You can produce a very, very, very detailed output. Try to keep it in .md so ai agents can read it and use it.
Include reasoning for everything we cover, from the physics and chemistry, to the math and programing, and the UI design and logic. 
Please produce an extensive file to address this task now.
You can make it a .md file for download.


<br>


Below will be the response I recieved:

<br>
<br>


# ECAS --- Long-Term Product, Architecture, Scientific, and UX Strategy

**Project:** ECAS --- Exoplanetary Characterization & Astrochemistry
Suite\
**Purpose:** A strategic design brief for consolidating the strongest
ideas from ECAS v1 and ECAS Beta, improving the current product without
unnecessary rewrites, and establishing a disciplined path toward a
scientifically defensible, capable, maintainable desktop research
application.\
**Status:** Proposal for investigation and staged decision-making. This
document is not an approved implementation plan and does not assert that
proposed capabilities have been implemented or scientifically
validated.\
**Repository:** <https://github.com/brettadin/ECAS_BETA>\
**Prepared:** 2026-10-29

------------------------------------------------------------------------

## 1. Executive recommendation

### 1.1 The central recommendation

**Do not immediately rewrite ECAS from scratch, and do not simply merge
the two codebases file-by-file.** Treat v1 and Beta as two sources of
product knowledge. Preserve the useful scientific workflows and
user-experience ideas from v1, retain Beta's stronger structured
ingestion, project/provenance, archive access, comparison-preparation,
and testing foundations where verified, and move toward a clearly
defined architecture through small, reversible changes.

The best default strategy is a **capability-led consolidation**:

1.  Establish a verified inventory of what each version actually does.
2.  Decide which user jobs ECAS must support and which scientific claims
    it may legitimately make.
3.  Define a stable scientific data model and scientific-computation
    boundaries.
4.  Design the experience around common tasks, not around module names
    or every available parameter.
5.  Bring across selected v1 workflows as product capabilities---not as
    wholesale code imports.
6.  Keep Beta's sound foundations where they work; replace individual
    components only when evidence justifies it.
7.  Add scientific validation and provenance alongside features, rather
    than after them.
8.  Make documentation, testing, and release evidence part of each
    change.
9.  Defer language proliferation and broad plugin architectures until a
    concrete, measured need exists.

A full rewrite can be justified if a formal audit demonstrates that core
design choices make the required product materially unsafe,
unmaintainable, or impossible to evolve. It should not be justified
solely because the code feels untidy, because two versions differ, or
because a new architecture looks cleaner on paper.

### 1.2 What "combine the best of both" means

  -----------------------------------------------------------------------
  Area                                Direction
  ----------------------------------- -----------------------------------
  Beta architecture                   Retain its modular separation where
                                      boundaries are real and useful;
                                      simplify overgrown coordination
                                      points when evidence supports it.

  V1 user experience                  Revisit the cleaner visual
                                      hierarchy, approachable workflow,
                                      molecule-identification
                                      interaction, and engaging
                                      transit-model visualization.
                                      Reimplement only after defining
                                      what the science and UX should
                                      mean.

  V1 scientific workflows             Preserve valuable spectroscopy,
                                      feature-identification, fitting,
                                      and transit-analysis use cases
                                      where they meet explicit scientific
                                      requirements.

  Beta data and provenance            Build on structured projects,
                                      source identity, hashes, metadata,
                                      archive retrieval, and cache
                                      validation---but do not mistake
                                      integrity checks for source
                                      authenticity or scientific
                                      validation.

  Both versions                       Reassess numerical assumptions,
                                      error handling, usability, tests,
                                      documentation, accessibility,
                                      packaging, and scientific claims.

  Future capabilities                 Add them only when there is a
                                      defined user problem, a scientific
                                      specification, testable acceptance
                                      criteria, and an identified
                                      maintainer.
  -----------------------------------------------------------------------

### 1.3 The non-negotiable principle

ECAS should distinguish, visibly and in its data model, between:

-   a **real observation**;
-   a **processed or calibrated observation**;
-   a **laboratory measurement**;
-   a **theoretical molecular line list or cross-section**;
-   a **synthetic model spectrum**;
-   a **candidate molecular interpretation**;
-   a **diagnostic result**;
-   a **validated scientific conclusion**.

A spectrum that overlaps a molecular reference is not, by itself,
evidence sufficient to claim a detection. A model that produces a
plausible curve is not automatically a validated atmospheric model. An
imported file that parses successfully is not necessarily scientifically
interpretable.

------------------------------------------------------------------------

## 2. Scope, evidence, and how to use this document

This is a strategic proposal informed by the supplied ECAS project
instructions and the preceding v1/Beta comparative review. That review
identified several important patterns:

-   Beta has a more explicit modular structure and structured ingestion,
    project persistence, source metadata, archive/cache workflows,
    comparison eligibility/alignment, residual diagnostics, and a
    restricted native transmission forward model.
-   V1 contains useful integrated spectroscopy and transit-analysis
    workflows, including feature identification and fitting-related
    interactions, plus some more approachable or engaging interface
    ideas.
-   Beta documentation has discrepancies around the current maturity of
    comparison and atmospheric-modelling features.
-   Beta has historical test-count reports from different snapshots;
    those counts must remain tied to the exact code revision and command
    that produced them.
-   Some scientific and numerical concerns were identified for
    investigation but were not independently reproduced in the
    comparative review.
-   The review was based on source and documentation inspection, not a
    fresh run of either complete application or a reproduction of all
    test results.

Consequently:

1.  **Treat observations about existing versions as audit findings to
    re-verify against the current checkout.**
2.  Treat architecture, library, UX, and roadmap recommendations as
    proposals.
3.  Do not mark a feature complete because it appears in this document.
4.  Before changing the repository, have your Ai partner inspect the current
    working tree, tests, decisions, project state, and recent changes.
5.  Keep this document as a strategy reference. Do not duplicate all of
    it into `PROJECT_STATE.md`, the README, or chunk logs.

### 2.1 Evidence labels to use throughout the project

Adopt these labels in plans, reviews, and scientific documentation:

-   **Observed in source** --- a code path or declaration was inspected.
-   **Automated-tested** --- a named test passed on a recorded revision
    and environment.
-   **Manually verified** --- a defined interactive workflow was
    executed and recorded.
-   **Scientifically benchmarked** --- results were compared with an
    identified reference or analytic case using declared tolerances.
-   **Independently reviewed** --- a reviewer other than the implementer
    assessed the stated subject.
-   **Proposed** --- not yet implemented or verified.
-   **Unknown / unverified** --- evidence is insufficient.
-   **Known limitation** --- a boundary that is intentionally accepted
    and documented.

These labels prevent the common failure mode in which a plan, a test
report, and a scientific validation claim become conflated.

------------------------------------------------------------------------

## 3. Product vision: define the jobs ECAS should do

A comprehensive scientific tool should not be a collection of tabs that
expose every internal capability. It should help a researcher move
through a coherent set of tasks while preserving enough detail for
advanced work.

### 3.1 Proposed core user journeys

#### Journey A --- Bring in a spectrum and understand it

1.  Start a project or open an existing one.
2.  Import a supported file or retrieve a supported archive product.
3.  Review the detected axis, signal, units, uncertainty, source, and
    data type.
4.  Resolve ambiguous columns or metadata explicitly.
5.  Preview the data and inspect quality flags.
6.  Save the original source and normalized representation with
    provenance.
7.  See a clear statement of what ECAS inferred and what the user
    confirmed.

This journey should work for spectroscopy files from multiple
domains---including FTIR and UV-Vis where the actual format and metadata
are supported---without assuming every text or CSV file has the same
semantics.

#### Journey B --- Explore molecular candidates responsibly

1.  Select an observation and the spectral interval of interest.
2.  Choose a molecular reference source or browse available reference
    data.
3.  Confirm units, spectral domain, resolution, temperature, pressure,
    and data provenance as applicable.
4.  View observation and reference on compatible axes.
5.  Explore candidate overlaps and known degeneracies.
6.  Inspect assumptions, uncertainty, missing information, and
    alternative explanations.
7.  Save the candidate evaluation and its configuration.
8.  Export plots and a traceable report that labels the result as
    exploratory unless stronger validation exists.

The default language should be "candidate overlap," "consistent with,"
or "requires further testing," not "detected," unless the method and
evidence genuinely support a detection claim.

#### Journey C --- Analyze transit spectroscopy

1.  Select or import transit observations or transmission-spectrum
    products.
2.  Inspect target, instrument, observation epoch, reduction product,
    wavelength coverage, and uncertainty.
3.  Select a compatible model path: inspect, fit a constrained model, or
    run a more advanced inference workflow if implemented.
4.  See which parameters are fixed, fitted, derived, or assumed.
5.  Inspect the model, residuals, uncertainties, and diagnostic
    warnings.
6.  Compare alternate model assumptions or sources where appropriate.
7.  Save a reproducible analysis configuration and results.
8.  Export a report that distinguishes data, model assumptions, and
    inference.

#### Journey D --- Learn or demonstrate a physical process

This is where the engaging elements from v1 can remain valuable. A
transit animation or molecular-identification activity can make the
application approachable, but it must be explicitly educational or
illustrative unless it is linked to a validated numerical analysis.

Examples: - an animated planet crossing a star, with an adjustable
impact parameter and scale; - a "why this feature is ambiguous"
molecular comparison explorer; - a visual explanation of how spectral
resolution or binning affects a signal; - an atmospheric-layer
illustration connected to the assumptions of the selected model.

These should explain concepts without implying that an animation is a
direct rendering of the actual planet or a scientifically complete
simulation.

#### Journey E --- Reproduce prior work

1.  Open a saved project and analysis record.
2.  See the exact input identities and hashes, source URLs or
    identifiers, retrieval times, software version, and configuration.
3.  Re-run the analysis if the required data and dependencies are
    available.
4.  Compare new output with the saved result.
5.  Understand whether differences come from changed code, changed data,
    changed reference products, changed dependencies, or nondeterminism.

Reproducibility is a first-class user journey, not an export feature
added at the end.

### 3.2 Define user groups without fragmenting the application

ECAS may serve: - a researcher who wants to inspect a file quickly; - a
spectroscopy user who understands units but not every atmospheric
parameter; - an experienced atmospheric modeller; - a student learning
how transit spectroscopy works; - a developer or method specialist
evaluating numerical details.

Do not create a separate application for every group. Use progressive
disclosure and clear modes: - **Explore** --- inspect, plot, compare,
and learn. - **Analyze** --- configure a defined workflow with
meaningful defaults. - **Advanced** --- expose additional parameters,
assumptions, and diagnostics. - **Developer / diagnostics** ---
technical details and support information, not the default researcher
experience.

The modes should alter how much detail is visible, not silently change
the underlying science.

------------------------------------------------------------------------

## 4. Consolidation strategy: improve Beta first, preserve the option to rewrite

### 4.1 Why a rewrite is risky

A rewrite can create a cleaner structure while losing: - edge-case
behavior embedded in existing workflows; - scientific assumptions that
were never documented; - useful file-format handling; - user interaction
patterns; - regression tests; - source provenance; - lessons from bugs
and failed implementations.

It can also make both applications unusable for a long period.
Scientific software is especially vulnerable because "the new plot looks
right" does not prove that the numerical output is equivalent.

### 4.2 Why a blind merge is also risky

V1 and Beta may represent different architectural assumptions, different
data models, and different levels of maturity. Copying entire modules
across versions can introduce duplicate models, incompatible units,
conflicting state ownership, and inconsistent persistence.

A module that appears self-contained may depend on: - undocumented
globals or UI state; - a particular array orientation; - a hidden unit
convention; - a specific model parameterization; - a database schema; -
assumptions about the meaning of missing values; - a particular
error-handling convention.

Therefore, port **capabilities and verified behavior**, not code volume.

### 4.3 Decision rule for each feature

For every useful feature found in either version, classify it:

1.  **Keep as-is** --- implementation is understood, tests are adequate,
    and design is compatible.
2.  **Keep but wrap** --- capability is useful but needs a stable
    interface or better separation.
3.  **Reimplement from specification** --- behavior is valuable but
    implementation is tightly coupled, poorly tested, or scientifically
    ambiguous.
4.  **Retire** --- redundant, unsafe, misleading, or no longer aligned
    with product goals.
5.  **Defer** --- potentially useful but not justified by current users
    or validation capacity.
6.  **Investigate** --- evidence is not sufficient to decide.

The decision record should include the reason, evidence, scientific
risks, UX impact, migration implications, and acceptance criteria.

### 4.4 Establish a capability inventory before restructuring

Create a table with one row per user-visible workflow, not just one row
per Python module.

Suggested columns:

-   Capability name
-   User job it supports
-   V1 status
-   Beta status
-   Current source locations
-   Scientific purpose
-   Inputs and outputs
-   Required metadata
-   Unit and coordinate conventions
-   Error behavior
-   Test coverage
-   Scientific benchmark status
-   UI quality and known friction
-   Data/provenance behavior
-   Dependencies
-   Decision: keep, wrap, reimplement, retire, defer, investigate
-   Acceptance criteria
-   Owner / next review

Do not infer status from filenames, README prose, or historical test
totals alone. Inspect callers, tests, current documentation, and actual
behavior.

### 4.5 Migration should be incremental and reversible

For each migrated workflow: 1. Write down the existing behavior and
intended behavior. 2. Identify representative input fixtures and
expected outputs. 3. Build or clarify a backend service boundary. 4.
Implement the service with tests independent of the UI. 5. Integrate it
into Beta behind a small, clear user workflow. 6. Compare results with
the old implementation where scientifically meaningful. 7. Record any
intended differences. 8. Run relevant regression tests and a manual
workflow check. 9. Update documentation and project status. 10. Remove
old code only after the replacement is verified and no callers remain.

A "strangler" approach---replacing one capability at a time while the
rest of the product remains operational---is generally safer than a
big-bang rewrite.

------------------------------------------------------------------------

## 5. Recommended target architecture

The architecture should be modular enough to support research growth but
not so abstract that each operation requires layers of indirection.

### 5.1 Proposed layers

``` text
┌─────────────────────────────────────────────────────────┐
│ Presentation layer                                      │
│ Workspace, workflow pages, plots, tables, dialogs       │
└──────────────────────────┬──────────────────────────────┘
                           │ user intent / view models
┌──────────────────────────▼──────────────────────────────┐
│ Application / use-case layer                             │
│ Import spectrum, retrieve product, compare, fit, export  │
│ Workflow validation, progress, cancellation, orchestration│
└───────────────┬────────────────────────────┬─────────────┘
                │                            │
┌───────────────▼────────────────┐  ┌────────▼─────────────┐
│ Scientific domain and methods  │  │ Data-access adapters │
│ Units, axes, spectra, models,  │  │ NASA, ExoMol, files, │
│ eligibility, diagnostics       │  │ project DB, caches   │
└───────────────┬────────────────┘  └────────┬─────────────┘
                │                            │
┌───────────────▼────────────────────────────▼─────────────┐
│ Shared contracts and persistence                         │
│ Data models, provenance, configuration, schema versions  │
└─────────────────────────────────────────────────────────┘
```

This is a conceptual boundary map, not a mandate to create one package
per box. A module should exist because it has a clear responsibility, a
stable contract, and a reason to change independently.

### 5.2 Scientific domain objects should not depend on the GUI

Core scientific objects and algorithms should not import Qt widgets,
mutate UI state, or require an active window.

For example, a comparison function should accept a validated input
object and configuration, return a result object with diagnostics, and
raise or return explicit domain errors. The UI decides how to display
the result.

Why: - numerical tests can run headlessly; - the same computation can
serve the GUI, command-line tooling, batch workflows, or a future API; -
UI changes cannot silently alter scientific calculations; - failures are
easier to isolate; - analysis becomes more reproducible.

### 5.3 Keep orchestration separate from numerical algorithms

A use case may: - validate the user's request; - fetch data; - report
progress; - invoke a scientific routine; - save inputs and results; -
translate failures into actionable messages.

The numerical routine should not perform all these jobs. It should focus
on its mathematical operation.

For example: - `RetrieveReferenceProduct` orchestrates provider requests
and caching. - `NormalizeSpectrum` performs a defined transformation. -
`AlignSpectra` converts compatible axes and resamples under declared
rules. - `ComputeResidualDiagnostics` computes explicitly defined
diagnostics. - `RunTransmissionForwardModel` evaluates a specified model
configuration. - `SaveAnalysisRecord` persists a result and its
provenance.

Names are illustrative. Inspect current code before adding or renaming
modules.

### 5.4 Use stable, typed contracts at boundaries

A boundary object should explicitly describe: - data identity and
provenance; - quantity and units; - coordinate axis and coordinate
frame; - data role and semantics; - uncertainty representation; -
quality flags and missing-data policy; - instrument/response metadata
where relevant; - software and schema versions.

Do not rely on generic dictionaries or positional tuples for important
scientific interfaces unless the schema is documented and validated.

Use typed models selectively. Pydantic can be useful at
file/API/configuration boundaries; dataclasses and explicit validation
may be sufficient for internal objects. Do not introduce multiple
competing validation frameworks without a clear reason.

### 5.5 Treat long-running work as a service, not a button callback

Archive retrieval, large cross-section loading, model generation,
fitting, and sensitivity analysis can be slow. The application layer
should provide: - progress events where meaningful; - cancellation; -
timeouts; - safe error propagation; - prevention of stale results
overwriting newer user choices; - a clear distinction between cancelled,
failed, partial, and successful runs.

A Cancel button that only changes the UI label is not real cancellation.
Cancellation behavior needs dedicated tests and manual verification.

### 5.6 Avoid premature microservices and plugin frameworks

ECAS is currently a desktop scientific application. A single
well-structured Python process is likely simpler and more reliable than
a distributed service architecture.

Use an adapter interface for genuinely variable external providers or
model engines. Do not create a general-purpose plugin framework until at
least two or three real implementations need the same extension
mechanism and the contract can be specified from actual requirements.

------------------------------------------------------------------------

## 6. Scientific data model and provenance

### 6.1 Represent scientific meaning, not just arrays

A spectrum should not be represented only as `x` and `y`. At minimum,
the normalized representation should identify:

-   coordinate values;
-   coordinate quantity and units (e.g. wavelength, wavenumber,
    frequency);
-   signal values;
-   signal quantity and units (e.g. flux density, transit depth,
    absorbance, transmittance);
-   uncertainty values and their meaning;
-   data role: observation, calibrated product, laboratory measurement,
    reference, model, residual, or derived result;
-   coordinate frame where relevant;
-   spectral domain and conventions;
-   source identity and provenance;
-   processing history;
-   quality masks or flags;
-   optional covariance or correlation information;
-   instrument and response metadata when available;
-   original source reference and immutable source bytes when feasible.

The data model should allow incomplete metadata without pretending it is
known. For example, a missing uncertainty is not the same as zero
uncertainty; an unknown unit is not dimensionless; an assumed wavelength
axis is not a verified wavelength axis.

### 6.2 Preserve both original and normalized data

Recommended conceptual model:

1.  **Raw source artifact** --- original bytes or a reference to a
    stable source artifact, plus hash and acquisition metadata.
2.  **Parsed representation** --- parsed columns and parser/version
    information.
3.  **Normalized scientific object** --- standardized units/semantics
    with explicit conversion history.
4.  **Derived result** --- transformation or analysis output linked to
    all parent inputs.
5.  **Analysis record** --- method version, parameters, assumptions,
    diagnostics, and output references.

Do not overwrite the original data when normalizing units, filtering
points, binning, or transforming coordinates.

### 6.3 Provenance must form a traceable chain

For each derived product, record as applicable: - parent data IDs and
content hashes; - provider or publication identifiers; - exact URL or
archive product identifier; - retrieval timestamp and relevant request
parameters; - parser and transformation version; - software version and
Git revision; - analysis method/version; - full configuration, including
defaults that affect the result; - dependency versions when
scientifically relevant; - warnings and assumptions; - output hashes; -
whether the result can be reproduced offline.

A SHA-256 hash establishes byte-level identity/integrity relative to a
known value. It does **not** prove that the data came from the claimed
provider, that the provider's data are correct, or that the scientific
interpretation is valid. Those are separate questions.

### 6.4 Version the project schema and migrations

If projects are persisted in SQLite or a project archive: - assign a
schema version; - make migrations explicit and testable; - retain a
backup or recoverable copy before migration; - validate migrated data; -
provide actionable errors for incompatible or corrupt projects; - test
opening older project fixtures; - never silently discard fields that are
not understood.

Store large arrays and raw artifacts in a format appropriate to their
size and access pattern. SQLite is suitable for metadata, relational
links, and moderate embedded payloads; it is not automatically the best
location for every large scientific array. Avoid optimizing this
prematurely: measure actual project sizes and access patterns first.

### 6.5 Distinguish provenance from reproducibility

A record can have excellent provenance but still be unreproducible if: -
an external service changes or removes the source product; - a
dependency is unavailable; - a proprietary or licensed reference dataset
cannot be redistributed; - a stochastic method is not seeded or its
random state is not recorded; - the original configuration is
incomplete; - a platform-specific numerical difference matters.

The UI should state whether a saved analysis is: - fully reproducible
from project-contained inputs; - reproducible if external sources remain
available; - reproducible only with a specified environment or optional
dependency; - not reproducible because required source data are missing.

------------------------------------------------------------------------

## 7. Scientific foundations: spectroscopy and molecular reference data

This section is a design and validation guide, not a complete
spectroscopy textbook. Detailed methods must be selected for each
supported measurement type and backed by domain literature.

### 7.1 Define the signal before comparing it

Spectral axes can be expressed as wavelength, wavenumber, frequency, or
energy. Signal axes may represent flux, flux density, intensity,
absorbance, transmittance, reflectance, optical depth, or transit depth.

These are not interchangeable labels.

For example, absorbance is commonly defined as:

\[ A(`\lambda`{=tex}) = -`\log`{=tex}\_{10} T(`\lambda`{=tex}) \]

where (T) is transmittance under the relevant convention. A
percent-transmittance value must be converted to a fraction before
applying this definition. Reflectance is not transmittance. Flux density
per unit wavelength is not numerically interchangeable with flux density
per unit frequency without a Jacobian transformation.

The conversion between wavelength and wavenumber is:

\[ `\tilde{\nu}`{=tex} = `\frac{1}{\lambda}`{=tex} \]

when units are consistent; for wavelength in micrometres and wavenumber
in inverse centimetres, the numerical relation is
(`\tilde{\nu}`{=tex},\[`\mathrm{cm}`{=tex}\^{-1}\] = 10\^4 /
`\lambda`{=tex},\[`\mu`{=tex}`\mathrm{m}`{=tex}\]).

Because this transformation reverses axis order, every associated vector
and matrix---measurements, uncertainties, masks, covariance, response
arrays---must be reordered consistently. Unit conversion must be
performed on the full scientific object, not on the x-axis alone.

### 7.2 File parsing is not scientific interpretation

A CSV, TXT, DAT, ASC, ECSV, FITS, or instrument-exported file may
contain: - a header and metadata; - multiple tables; - decimal commas or
unusual delimiters; - comments and missing values; - wavelength in one
column and signal in another; - absorbance or transmittance; -
instrument-specific units; - a wavenumber axis; - a background/reference
measurement; - multiple spectra in one file.

A generic parser can identify numeric columns, but it cannot safely
infer every scientific meaning. Import UX should separate: 1. format
detection; 2. table/column selection; 3. unit and semantic confirmation;
4. data-quality validation; 5. normalized representation.

Where the format is ambiguous, ask the user rather than silently
guessing. Provide a preview and show exactly which interpretation will
be saved.

### 7.3 Reference spectra and line lists have conditions

Molecular spectra can depend on temperature, pressure, isotopic
composition, broadening assumptions, line-strength convention, partition
functions, and spectral range. A reference at one temperature or
pressure may not be directly comparable to an observation or model at
another.

Record: - provider and dataset version; - molecule/isotopologue
identifiers; - temperature and pressure conditions where relevant; -
units and spectral domain; - resolution or line-list nature; -
broadening and cross-section assumptions; - citation and license; - any
interpolation or transformation applied by ECAS.

Do not label a theoretical line list as a measured laboratory spectrum.
Do not label a synthetic cross-section as a direct observation.

### 7.4 Resolution and instrumental response matter

A high-resolution reference spectrum cannot always be overlaid directly
on a lower-resolution observation and interpreted by eye. Instrumental
line-spread functions, spectral response, binning, and wavelength
calibration can change the apparent profile.

A comparison workflow should make explicit whether it: - plots
native-resolution data only; - resamples one spectrum; - integrates into
bins; - convolves with a response kernel; - applies a wavelength offset
or calibration correction; - compares only coarse-band features.

Do not use a simple interpolation routine as a substitute for a
physically justified convolution when the instrument response is
relevant.

### 7.5 Overlap is not detection

Molecular bands often overlap with other species, clouds/hazes, stellar
contamination, instrumental effects, and reduction artifacts. A visual
match can generate a candidate, but stronger inference requires an
explicit statistical/modeling framework and appropriate alternative
hypotheses.

A responsible UI should show: - the candidate and reference source; -
spectral coverage and excluded regions; - compatible units and
resolution assumptions; - uncertainty treatment; - known degeneracies
and alternatives; - diagnostic output and its limits; - what additional
data or analysis would strengthen the claim.

Use calibrated language and never present a candidate score as a
detection probability unless it is mathematically and scientifically
calibrated as such.

### 7.6 FTIR and UV-Vis should be treated as important use cases

The user's existing research files may be FTIR-oriented or UV-Vis text
exports. ECAS should not claim universal support without representative
fixtures, but its ingestion architecture should not make arbitrary CSV
schema assumptions a permanent limitation.

Recommended work: - gather anonymized representative files from each
intended instrument/export workflow; - document their true formats and
semantics; - create small synthetic fixtures for edge cases; - create a
parser specification per supported format family; - retain original
bytes and parsing metadata; - test unit/axis interpretation and failure
messages; - explicitly identify formats not yet supported.

Do not build a custom parser for a format based only on its extension.
Inspect representative examples and authoritative format specifications.

------------------------------------------------------------------------

## 8. Scientific foundations: exoplanet transmission and transit modeling

### 8.1 Separate the physical forward model from inference

A **forward model** maps physical and nuisance parameters to a predicted
observable. An **inference method** compares predictions with data and
estimates which parameter values are supported.

These are different capabilities: - forward model: "What spectrum does
this parameter set predict under these assumptions?" - optimizer: "Which
parameter set minimizes this defined objective?" - posterior sampler:
"What parameter distribution follows from the likelihood, priors, and
data under this model?" - model comparison: "How do specified competing
models compare under a defined criterion?"

Implementing a forward model does not automatically implement retrieval,
uncertainty quantification, or detection significance.

### 8.2 Transmission spectra are physically layered problems

A simplified transmission model may include: - planetary radius and
gravity; - stellar radius; - atmospheric temperature structure; -
pressure/altitude grid; - mean molecular weight and composition; -
molecular absorption cross-sections or line-by-line opacity; -
collision-induced absorption and scattering where relevant; -
clouds/hazes; - reference pressure/radius convention; - instrument
spectral response; - observational uncertainties and covariance.

The transit depth is often approximated in a simple opaque-disk limit
by:

\[ D
`\approx `{=tex}`\left`{=tex}(`\frac{R_p}{R_*}`{=tex}`\right`{=tex})\^2
\]

but wavelength-dependent transmission involves an effective planetary
radius that varies with opacity and atmospheric structure. A simplified
isothermal, hydrostatic model can be useful for exploration, but its
assumptions must be stated and tested. It should not be presented as a
complete atmospheric retrieval engine.

### 8.3 Hydrostatic and isothermal assumptions

A common hydrostatic relation is:

\[ `\frac{dP}{dr}`{=tex} = -`\rho`{=tex}(r) g(r) \]

Under ideal-gas and constant-temperature approximations, pressure often
varies approximately exponentially with altitude over a limited range,
with scale height:

\[ H `\approx `{=tex}`\frac{k_B T}{\mu m_H g}`{=tex} \]

Here (T) is temperature, (`\mu `{=tex}m_H) is mean molecular mass under
the chosen convention, (g) is gravity, and (k_B) is Boltzmann's
constant. Units and definitions must be consistent.

These assumptions can be useful for a transparent educational or
exploratory model, but: - temperature may vary with altitude; - gravity
may vary with radius; - mean molecular weight depends on composition; -
clouds/hazes and refraction can alter the observable; - the reference
radius/pressure degeneracy matters; - stellar heterogeneity and
instrument systematics can affect observed spectra.

Expose such assumptions in the result metadata and report.

### 8.4 Opacity and cross-section handling

Cross-section tables require careful validation: - correct
molecule/isotopologue; - correct temperature and pressure dependence; -
wavelength/wavenumber units; - cross-section units; - finite,
nonnegative values where physically required; - valid grid ordering and
duplicates policy; - temperature interpolation policy; - extrapolation
policy; - provenance and source citation.

Never silently extrapolate beyond a reference grid unless a defined
method justifies it. A temperature mismatch warning should not imply
that a cross-section has been corrected. If temperature interpolation is
unsupported, say so and reject or explicitly mark the approximation.

### 8.5 Transit geometry and numerical integration

A transmission forward model may calculate slant optical depth along
chords through spherical atmospheric shells and then integrate over
impact parameter. Numerical design should address: - radial grid
resolution and convergence; - line-of-sight integration accuracy; -
interpolation of opacity; - numerical overflow/underflow in transmission
(e\^{-`\tau`{=tex}}); - boundary conditions and top-of-atmosphere
truncation; - conservation or limiting behavior in known cases; -
sensitivity to grid resolution.

A visually smooth curve is not proof of numerical convergence. Use
convergence tests: increase resolution and compare output against a
declared tolerance for representative cases.

### 8.6 Fitting and parameter inference

For least-squares or likelihood methods, document: - the
objective/likelihood equation; - treatment of measurement uncertainty; -
whether data points are assumed independent; - covariance handling; -
parameter bounds and priors; - parameter transformations; -
optimizer/sampler and convergence criteria; - initialization and random
seed where relevant; - failure modes; - posterior or parameter
uncertainty reporting.

A weighted least-squares expression such as

\[ `\chi`{=tex}\^2 = (`\mathbf{y}`{=tex}-`\mathbf{m}`{=tex})\^T
`\mathbf{C}`{=tex}\^{-1}(`\mathbf{y}`{=tex}-`\mathbf{m}`{=tex}) \]

is meaningful only when (`\mathbf{C}`{=tex}) represents the relevant
uncertainty/covariance structure and the assumptions behind the
statistic are appropriate. If the covariance is diagonal, state that
assumption. If the method assumes independent Gaussian errors, say so.

Do not describe an optimizer's best-fit parameters as a full posterior.
Do not call a leave-one-out sensitivity curve a molecular detection
test. Do not call a residual summary a calibrated significance measure
unless its null distribution and assumptions are justified.

### 8.7 Residuals and model adequacy

Residual plots and summary statistics are diagnostic tools. They can
expose structured mismatch but do not by themselves prove model
correctness or molecule presence.

For each diagnostic, specify: - equation and normalization; -
assumptions about uncertainty and correlation; - valid input
conditions; - interpretation; - what it does not measure; - whether its
reference distribution is calibrated.

A whitened residual calculation requires a valid covariance
representation and numerically stable factorization. Handle singular or
ill-conditioned covariance matrices explicitly; do not silently
substitute a diagonal approximation.

### 8.8 Model comparison and detections require stronger standards

If ECAS later supports claims about molecular evidence, define a
separate scientific specification for: - competing hypotheses/models; -
priors and nuisance parameters; - instrument and stellar systematics; -
correlated noise; - model misspecification; - model evidence or other
chosen statistic; - calibration and false-positive behavior; - benchmark
datasets and published comparison cases; - sensitivity to assumptions.

No single numerical score should be treated as universally valid across
all instruments and datasets. Independent scientific review should be
required before a feature is marketed as a detection or retrieval
capability.

------------------------------------------------------------------------

## 9. Validation strategy: what "scientifically sound" should mean

Scientific soundness is not a single test suite. It has multiple layers.

### 9.1 Validation pyramid

1.  **Static and contract checks** --- types, schemas, valid units,
    valid shapes, explicit error conditions.
2.  **Unit tests** --- individual transformations and algorithms.
3.  **Property/invariant tests** --- properties that should hold over
    many generated inputs.
4.  **Analytic tests** --- known mathematical cases with derivable
    answers.
5.  **Numerical convergence tests** --- results stable as
    grid/resolution/tolerance changes.
6.  **Regression tests** --- previously verified outputs remain within
    stated tolerances.
7.  **Reference/benchmark tests** --- compare with trusted datasets,
    literature examples, or independent implementations.
8.  **Integration tests** --- ingestion to persisted result across
    components.
9.  **Manual workflow tests** --- real desktop interaction,
    cancellation, errors, and recovery.
10. **Scientific review** --- domain expert reviews equations,
    assumptions, interpretation, and limits.
11. **External validation** --- use on independent real datasets with
    documented criteria and limitations.

A feature can pass levels 1--4 and still fail scientific validation at
levels 7--11. Keep the levels separate in project status.

### 9.2 Test with synthetic data and real data

Synthetic fixtures are essential when representative files are
unavailable. They allow exact control of units, noise, edge cases, and
expected outcomes. However, synthetic data can accidentally encode the
same assumptions as the implementation, so it cannot be the only
validation source.

Use a mixture: - synthetic edge cases; - analytic test cases; -
published reference examples; - real but appropriately licensed or
publicly accessible datasets; - instrument-specific sample files where
possible; - independent implementation comparisons when feasible.

Record which classes of data have actually been tested. Never claim that
generic CSV tests validate FTIR, UV-Vis, JWST, or FITS workflows unless
those paths and their semantics were exercised.

### 9.3 Numerical tolerances must be justified

Avoid arbitrary `assert_allclose` tolerances chosen merely to make tests
pass. Explain: - expected floating-point error; - interpolation or
quadrature error; - physical or measurement precision; - allowed
regression tolerance; - whether the tolerance is absolute, relative, or
scale-dependent.

For ill-conditioned computations, use tests that expose the conditioning
and failure behavior. Include extreme-but-valid and invalid inputs.

### 9.4 Property-based and metamorphic tests

Useful properties include: - converting wavelength to wavenumber and
back recovers values within tolerance; - axis reversal also reverses all
associated arrays consistently; - unit conversions preserve physical
quantities; - reordering input rows followed by canonical sorting
produces the same normalized spectrum; - a zero-opacity limiting case
approaches the expected baseline; - an opaque atmosphere behaves
consistently with the model's defined limit; - increasing numerical
resolution converges within a tolerance; - serializing and reopening a
project preserves scientific values and provenance; - changing a source
artifact changes its content hash; - invalid or missing units are not
silently accepted as known units.

Hypothesis is one option for property-based testing in Python. Do not
add it until the team has identified high-value properties and can
maintain the resulting tests.

### 9.5 Benchmark registry

Create a small registry of trusted benchmark cases. Each record should
include: - benchmark name and citation; - input data or stable source
ID; - software/method version; - expected outputs or comparison
statistic; - tolerance and rationale; - known caveats; - reviewer and
review date; - test location.

Benchmark cases should be chosen by scientific capability. For example,
a transmission forward model should not be considered validated merely
because it agrees with a test fixture generated by itself.

### 9.6 Validation claims should be scoped

A useful statement is:

> "The wavelength conversion and axis-reversal behavior passed analytic
> and property tests for the declared unit pairs. The complete
> observational workflow has not yet been benchmarked against an
> independent instrument dataset."

This is more informative than "the science works."

------------------------------------------------------------------------

## 10. User experience: make complexity available without making it unavoidable

### 10.1 The primary UI rule

**Show the next decision the user needs to make---not every parameter
the program knows about.**

A scientific application can be powerful while keeping the default
workflow manageable. Complexity should be layered, contextual, and
reversible.

### 10.2 Proposed three-level interaction model

#### Level 1 --- Guided/default workflow

Expose: - the data or target being analyzed; - the operation; - a small
number of meaningful choices; - essential metadata confirmation; - a
clear preview; - warnings and a concise explanation of assumptions; -
Run, Cancel, Save, and Export actions as appropriate.

Use safe, explicit defaults. Do not silently invent critical metadata.

#### Level 2 --- Advanced settings

Expose: - resampling and binning method; - response convolution; -
uncertainty/covariance treatment; - model assumptions; - fit bounds and
priors; - numerical tolerances and grid resolution; - cache behavior and
source selection; - diagnostic options.

Each advanced control should explain what it changes and whether it
affects scientific interpretation.

#### Level 3 --- Expert / method configuration

Expose: - detailed physical parameterization; - alternative
algorithms; - custom model settings; - covariance structures; -
optimizer/sampler controls; - detailed numerical diagnostics; - explicit
overrides for otherwise blocking assumptions.

Overrides should record that the user supplied or changed the setting. A
warning should not be bypassable without recording the choice when the
warning concerns scientific validity.

### 10.3 Progressive disclosure must not hide critical assumptions

Good candidates for advanced panels: - performance tuning; - optional
visual styling; - detailed solver controls; - optional plot annotations.

Poor candidates for hidden panels: - units that determine the meaning of
data; - whether values are percent or fraction; - whether an axis is
wavelength or wavenumber; - whether a spectrum is observed or
synthetic; - whether uncertainty is absent or assumed; - whether the
result is exploratory or validated.

Critical assumptions should be visible in the workflow summary and
exported report even if their detailed controls are advanced.

### 10.4 Use workflow-oriented navigation

A practical navigation structure might be:

1.  **Home / Projects** --- resume work, open recent projects, start a
    task.
2.  **Data** --- import, retrieve, inspect, and manage source artifacts.
3.  **Explore** --- plots, spectral features, reference overlays,
    educational views.
4.  **Analyze** --- defined workflows such as transit-spectrum
    comparison, fitting, or diagnostics.
5.  **Models** --- configure and inspect supported forward models and
    inference methods.
6.  **Results** --- compare saved runs, review provenance, export
    reports.
7.  **Resources / Settings** --- citations, optional dependencies, cache
    and application preferences.

This is a conceptual model, not a demand to rename current pages
immediately. Test it with task-based prototypes before changing the
existing UI.

Avoid a tab per Python package or a page per internal class. Navigation
should mirror users' goals.

### 10.5 Visual hierarchy and consistency

V1's cleaner elements should be reviewed for: - spacing and alignment; -
hierarchy of headings and controls; - readable typography; - consistent
button placement; - restrained color use; - plot legibility; -
informative empty states; - consistent dialogs and warnings.

Define a small design system: - spacing scale; - typography scale; -
color tokens with accessible contrast; - control heights; - button
hierarchy; - table density; - plot line/marker conventions; -
status/warning/error styles; - keyboard focus and selection states.

The goal is not to copy v1's appearance wholesale. Preserve the visual
patterns that help users understand the workflow and reapply them
consistently.

### 10.6 Make plots a core scientific interface

Plots should provide: - labeled axes and units; - clear
data/model/reference distinction; - legends that do not obscure
important features; - error bars or uncertainty bands where
appropriate; - quality-mask/excluded-region visualization; - zoom, pan,
and reset; - hover inspection or cursor readout; - optional residual
panels; - reproducible export; - source/method context; - accessible
color and line-style distinctions.

Use color plus line style/markers so meaning does not depend on color
alone. Avoid using the same visual style for observed data, synthetic
model, reference line list, and residuals.

Do not overload plots with every annotation by default. Let users reveal
additional layers.

### 10.7 Preserve engaging features, but define their role

The v1 identification tab and transit animations may be valuable even if
they are not part of Beta's primary research workflow.

Recommended design: - retain an **Explore / Identify** experience as a
guided way to inspect candidate features; - present candidate matches as
hypotheses, not detections; - provide a "why this is a candidate"
explanation with source, units, and limitations; - retain a **Transit
Visualizer** as an educational or model-exploration view; - distinguish
illustrative animation from fitted or validated scientific output; -
allow a path from exploration to a saved analysis, carrying the selected
data and configuration forward.

Do not add animation solely because it looks engaging. It should teach a
concept, reveal a parameter's effect, or make a scientific workflow
easier to understand.

### 10.8 Accessibility and interaction quality

Include: - keyboard navigation; - visible focus; - logical tab order; -
readable contrast; - scalable layouts and text; - non-color status
indicators; - screen-reader labels where supported by the toolkit; -
clear error messages and recovery options; - no reliance on hover
alone; - predictable shortcuts and undo where practical.

Use a small set of real user tasks to evaluate UX. For example: - import
an FTIR text export and verify axis interpretation; - compare a transit
spectrum with a reference; - locate why a comparison is ineligible; -
cancel a slow archive request; - reopen a saved analysis and reproduce
its plot.

Measure task completion, error rate, time to recover from a mistake, and
user confidence---not just visual preference.

------------------------------------------------------------------------

## 11. Documentation as a reliable engineering process

Documentation should not depend on someone remembering to update it at
the end. It should be linked to task completion and verified alongside
code.

### 11.1 Establish a single source of truth for each kind of fact

Recommended responsibilities (adapt to the repository's actual existing
structure; do not create duplicates without need):

  -----------------------------------------------------------------------
  Document type                       Authoritative purpose
  ----------------------------------- -----------------------------------
  `README.md`                         What ECAS is, who it serves,
                                      current supported workflows,
                                      installation/launch, clear
                                      limitations

  `PROJECT_STATE.md`                  Current verified status, current
                                      blockers, latest verified
                                      test/validation status, next work

  `DECISIONS.md`                      Durable
                                      architectural/scientific/product
                                      decisions and reasons

  Architecture overview               Current modules, boundaries, data
                                      flow, entry points

  Data model documentation            Scientific object semantics, units,
                                      metadata, schema/version rules

  Validation strategy                 Test layers, benchmark policy,
                                      scientific-validation policy

  Feature specification               Intended behavior, equations,
                                      assumptions, limits, acceptance
                                      criteria for a substantial
                                      capability

  Chunk/task plan and implementation  Historical task scope, decisions,
  log                                 changes, verification output

  User guide                          How a user completes workflows and
                                      interprets outputs

  Release notes                       User-visible changes, migrations,
                                      compatibility and known limitations

  ADR (if adopted)                    Focused record for a significant
                                      architectural decision
  -----------------------------------------------------------------------

Avoid copying the same status paragraph into every file. Link to the
authoritative location instead.

### 11.2 Use a documentation change matrix

Every implementation task should answer:

-   Does behavior change? Update user-facing docs and relevant feature
    specification.
-   Does a scientific assumption or equation change? Update method
    specification and `DECISIONS.md` if durable.
-   Does module ownership or data flow change? Update architecture docs.
-   Does persistence/schema change? Update schema and migration docs.
-   Does validation status change? Update `PROJECT_STATE.md` and
    validation records.
-   Does the user's workflow change? Update user guide and
    screenshots/examples if useful.
-   Is this only a refactor with no behavior change? Update architecture
    docs only if the documented architecture changes.
-   Is the work incomplete? Record the blocker and do not mark the
    feature complete.

### 11.3 Add a definition of done

A task is not done merely because code was edited.

Suggested Definition of Done: - \[ \] Scope matches the approved plan. -
\[ \] No unrelated files or behavior changed without explanation. - \[
\] Relevant automated tests were run; actual command and result
recorded. - \[ \] Failure paths and important edge cases were tested. -
\[ \] Numerical behavior has appropriate
analytic/property/regression/benchmark tests. - \[ \] UI workflow was
manually checked where automation is insufficient. - \[ \] Inputs,
outputs, units, assumptions, and limitations are documented. - \[ \]
Provenance and persistence behavior are verified where relevant. - \[ \]
User-facing messages are actionable. - \[ \] Changed files and diff were
inspected. - \[ \] Applicable docs and project status were updated. - \[
\] Outstanding limitations are recorded. - \[ \] No claim exceeds the
evidence gathered.

A small documentation-only or trivial formatting task can use a
proportionate subset, but it should still report exactly what was
verified.

### 11.4 Keep machine-readable project status small and factual

Consider a compact status record, either within the current
`PROJECT_STATE.md` or a structured file if automation becomes useful,
with: - current Git revision; - date and environment for latest test
run; - exact command; - passed/failed/skipped counts; - whether tests
were complete or focused; - scientific benchmark status; - manual
acceptance status; - known blockers; - next bounded task.

Do not manually synchronize multiple status files with slightly
different test totals. If a report refers to an earlier snapshot, keep
it historical and label it clearly.

### 11.5 Generate reference documentation where possible

Automate documentation that is mechanically derived: - public API
references from docstrings; - dependency inventories; - supported import
formats from a declared registry; - test and coverage reports; - schema
diagrams where generated from a source definition; - release notes from
curated changes when useful.

Do not try to auto-generate scientific explanations or project status
from code alone. Generated references still need review and should not
be treated as proof that a feature works.

### 11.6 Use CI to enforce cheap documentation checks

Potential checks: - Markdown links and formatting; - code examples that
can be tested; - spelling/terminology checks for official project
name; - docs build; - validation of JSON/YAML configuration; -
consistency checks for supported-format registries; - a check that
feature status labels follow an allowed vocabulary.

Keep checks useful. A fragile documentation pipeline that blocks all
work for cosmetic issues will be ignored or bypassed.

### 11.7 Make Agent's documentation obligations explicit

Every ACT prompt should specify: 1. which docs may need updating; 2.
which docs must not be rewritten unnecessarily; 3. what source is
authoritative; 4. which claims must be supported by test output; 5. how
unverified behavior must be described; 6. that the diff must be
inspected after edits; 7. that incomplete work must remain explicitly
incomplete.

Agents should not invent test counts, rewrite historic checkpoints as
current, or mark a feature complete because implementation code exists.

------------------------------------------------------------------------

## 12. Development tools and engineering workflow

### 12.1 Keep the core toolchain intentionally small

The following is a candidate toolset, not an instruction to add every
dependency at once.

  -------------------------------------------------------------------------
  Need                    Candidate                 Why / cautions
  ----------------------- ------------------------- -----------------------
  Language/runtime        Supported Python version  Best fit for existing
                                                    code and scientific
                                                    ecosystem; standardize
                                                    supported versions and
                                                    packaging.

  GUI                     Existing Qt binding and   Preserve working
                          PyQtGraph, unless a       desktop foundations;
                          deliberate migration is   avoid switching GUI
                          justified                 frameworks solely for
                                                    novelty.

  Tests                   pytest                    Mature testing model;
                                                    use focused tests and
                                                    explicit fixtures.

  Coverage                coverage.py / pytest-cov  Shows untested code
                                                    paths, but coverage
                                                    percentage is not
                                                    scientific correctness.

  Static typing           mypy or pyright, selected Helps clarify
                          deliberately              interfaces; avoid
                                                    running competing
                                                    strict configurations
                                                    without a plan.

  Lint/format             Ruff, optionally Black if Fast consistency
                          not covered by selected   checks; agree on one
                          Ruff settings             canonical formatter.

  Type/data validation    dataclasses plus explicit Prevents malformed
                          validation; Pydantic at   inputs crossing
                          boundaries if useful      important boundaries;
                                                    avoid redundant model
                                                    systems.

  Units                   Astropy units and/or      Dimensional correctness
                          Pint, after a focused     is critical; select one
                          comparison                primary quantity
                                                    strategy for each
                                                    domain and define
                                                    interop.

  Scientific arrays       NumPy, SciPy              Core numerical
                                                    foundations; pin and
                                                    test supported
                                                    versions.

  Astronomy               Astropy                   Standard astronomy
  formats/coordinates                               ecosystem for FITS,
                                                    units, time,
                                                    coordinates, and
                                                    related facilities.

  Spectral utilities      specutils where its       Potential support for
                          abstractions fit          spectral data and
                                                    operations; evaluate
                                                    its conventions against
                                                    ECAS's requirements.

  Plotting                PyQtGraph for interactive Avoid duplicating
                          desktop plots; Matplotlib plotting stacks without
                          for publication-quality   a defined role for
                          static output if needed   each.

  Property tests          Hypothesis, selectively   Useful for invariants
                                                    and edge cases; design
                                                    properties before
                                                    adding broad generated
                                                    tests.

  Database                SQLite for local project  Reliable local storage
                          metadata/relationships,   for many desktop
                          with explicit schema      workflows; don't put
                          migrations                all large arrays there
                                                    by default without
                                                    measuring.

  Configuration/schema    TOML/YAML/JSON only where Keep human-readable
                          appropriate;              configuration and
                          schema-validate persisted project schemas
                          formats                   versioned.

  Packaging               PyInstaller or another    A working source tree
                          chosen packager;          does not prove a
                          clean-build CI            packaged desktop build
                                                    works.

  Documentation           Markdown, Sphinx or       Start with clear
                          MkDocs if project size    Markdown; introduce a
                          warrants                  docs site when
                                                    navigation and API docs
                                                    justify it.

  Dependency locking      A chosen                  Reproducible
                          lockfile/workflow (uv,    environments matter;
                          pip-tools, Poetry, or     choose one tool and
                          another)                  document it.

  Git quality gates       GitHub Actions or         Run tests/lint/docs
                          existing CI provider      checks on supported
                                                    environments.

  Crash diagnostics       Structured logging with   Makes failures
                          privacy-conscious         diagnosable without
                          redaction                 exposing local paths or
                                                    sensitive research
                                                    data.
  -------------------------------------------------------------------------

Do not introduce every tool immediately. First inspect the existing
project configuration and choose the smallest coherent toolchain.

### 12.2 Suggested quality gates

For pull requests or each implementation burst: - formatting/lint; -
static type checks for agreed scope; - focused tests; - full fast test
suite where feasible; - docs/link checks; - diff review; -
dependency/security scan on a sensible schedule; - package smoke test
for release-relevant changes.

For release candidates: - complete supported test suite; - benchmark
suite; - clean install in a fresh environment; - packaged application
launch and workflow smoke tests; - data migration tests; - archive/cache
behavior tests; - cancellation and error-recovery tests; - manual
acceptance checklist; - release notes and known limitations.

### 12.3 Improve test evidence

For every meaningful test run, preserve: - Git revision; - Python
version and OS; - dependency lock/version summary; - exact command; -
start/end date; - exit code; - pass/fail/skip totals; - relevant output
or artifact; - whether network tests were enabled; - whether the run was
focused or full.

Avoid treating an old terminal transcript as proof of current behavior.
Avoid treating a test count alone as evidence of correctness.

### 12.4 Avoid giant ACT prompts

Use one bounded change per ACT phase. A prompt can be comprehensive
about requirements while still limiting implementation to a small scope.

Recommended loop: 1. Inspect the current state. 2. State the problem and
evidence. 3. Plan the smallest change. 4. Review and approve. 5.
Implement. 6. Test and inspect diff. 7. Update docs. 8. Accept or
request a specific correction. 9. Commit at a logical checkpoint.

Do not ask agents to simultaneously redesign the entire UI, rewrite the
data model, migrate the database, add multiple model engines, and update
every document. That is too many interacting failure modes.

------------------------------------------------------------------------

## 13. Programming languages: should ECAS add more than Python?

### 13.1 Default: keep Python as the primary language

Python is already the project language and has a strong ecosystem for
scientific computing, astronomy, data handling, testing, and desktop UI
integration. Adding another language has costs: - a second build and
dependency toolchain; - more complex debugging; - cross-language data
contracts; - additional packaging and distribution problems; - more
contributors required to understand the code; - more opportunities for
inconsistent scientific semantics.

A language should be added only when it solves a measured problem better
than a simpler Python solution.

### 13.2 When another language could be justified

  -----------------------------------------------------------------------
  Language / technology   Possible use            Decision threshold
  ----------------------- ----------------------- -----------------------
  C, C++, or Rust         A computational kernel  Profile first; identify
                          that is demonstrably    the bottleneck; compare
                          too slow in             vectorization,
                          Python/NumPy, or a      algorithmic
                          stable native library   improvements, and
                          with strong             existing native
                          performance/ safety     libraries before
                          benefits                writing a new kernel.

  Fortran                 Integrating or          Prefer reuse of
                          maintaining established validated routines over
                          scientific routines     rewriting them into a
                          where the Fortran       different language
                          implementation is       without a scientific
                          authoritative           equivalence study.

  JavaScript/TypeScript   A separate web UI or    Only if there is a
                          browser-based           defined web deployment
                          visualization product   need; do not create a
                                                  web front end merely
                                                  because it is
                                                  fashionable.

  SQL                     Database queries and    Already appropriate as
                          migrations              a data language, not a
                                                  reason to split the
                                                  main application.

  Julia                   Experimental research   Keep as a separate
                          algorithms or           prototype until its
                          performance-sensitive   value is proven;
                          numerical prototyping   integrating a second
                          in a team that can      runtime can be costly.
                          maintain Julia          

  Shell scripts           Build, release, and     Keep scripts short and
                          automation glue         portable; do not move
                                                  domain logic into
                                                  shell.
  -----------------------------------------------------------------------

### 13.3 Performance policy

Use this sequence: 1. Measure with representative data. 2. Identify
whether time is spent in Python loops, numerical libraries, I/O, network
waits, plotting, or database operations. 3. Improve algorithmic
complexity or vectorization. 4. Use appropriate NumPy/SciPy/library
implementations. 5. Cache only when cache invalidation and provenance
are defined. 6. Consider compiled kernels only if profiling still shows
a material bottleneck. 7. Add benchmarks and cross-platform packaging
tests for the compiled component.

Do not optimize based on intuition or tiny synthetic benchmarks.

### 13.4 Keep boundaries language-neutral if future expansion is plausible

Use documented arrays, units, schemas, and file/API contracts. If a
compiled engine becomes necessary, a narrow function interface or a
separately packaged command-line worker is often easier to maintain than
spreading a second language through the application.

Do not build language-neutral infrastructure now without a concrete
second-language use case.

------------------------------------------------------------------------

## 14. External scientific sources, databases, and reference programs

The following are candidate resources to evaluate. Their inclusion does
not imply endorsement of every product, compatibility with every ECAS
workflow, free redistribution, or verified integration. Before adopting
any source, check its current documentation, licensing, versioning,
coverage, units, API terms, citation requirements, and scientific
limitations.

### 14.1 Observational and exoplanet data

-   **NASA Exoplanet Archive** ---
    <https://exoplanetarchive.ipac.caltech.edu/>\
    A key source for exoplanet data and associated archive products. Use
    documented APIs and record exact table/product identifiers, query
    parameters, retrieval time, and citations. Do not assume all
    observations or reductions are available in one uniform schema.

-   **MAST (Mikulski Archive for Space Telescopes)** ---
    <https://mast.stsci.edu/>\
    Relevant for many space-telescope datasets, including JWST and HST
    holdings. Dataset selection, calibration level, data rights, and
    instrument-specific interpretation need to be explicit.

-   **ESA Gaia Archive** --- <https://gea.esac.esa.int/archive/>\
    Potentially useful for stellar context and related metadata; not a
    replacement for instrument-specific spectral archives.

-   **NASA/IPAC Infrared Science Archive (IRSA)** ---
    <https://irsa.ipac.caltech.edu/>\
    Relevant for infrared astronomical data and catalogs where the
    science case requires them.

-   **VizieR** --- <https://vizier.cds.unistra.fr/>\
    Useful for published catalogs and tables. Preserve the exact catalog
    identifier and bibliographic reference.

-   **SIMBAD** --- <https://simbad.cds.unistra.fr/simbad/>\
    Useful for object identification and cross-identification.
    Object-name resolution should preserve ambiguity and source
    identifiers rather than relying on a string alone.

**Integration principle:** Treat every archive as a provider adapter
with explicit product types and metadata. A successful HTTP response is
not proof that the returned product is the intended scientific data.

### 14.2 Molecular spectroscopy and chemistry

-   **ExoMol** --- <https://exomol.com/>\
    Molecular line lists and related data for exoplanetary and other
    high-temperature atmospheres. Track molecule, isotopologue, dataset,
    version, citations, spectral coverage, and licensing/usage
    requirements.

-   **HITRAN** --- <https://hitran.org/>\
    A major molecular spectroscopic database. Confirm API/download
    conditions, supported parameters, temperature/pressure assumptions,
    and the appropriate citation.

-   **NIST Chemistry WebBook** ---
    <https://webbook.nist.gov/chemistry/>\
    Useful reference information for molecular and chemical data. Verify
    the particular data type and its conditions before using it as a
    quantitative reference.

-   **MPI-Mainz UV/VIS Spectral Atlas** ---
    <https://www.uv-vis-spectral-atlas-mainz.org/>\
    A relevant reference for gas-phase UV/visible absorption
    cross-sections. Check molecule-specific conditions, data source, and
    citation/usage terms.

-   **PNNL gas-phase infrared database** --- <https://www.pnl.gov/>\
    PNNL has published gas-phase infrared absorption data; locate and
    verify the authoritative dataset and current access route for the
    specific use case before integrating it. Do not hard-code a guessed
    endpoint.

-   **NIST Chemistry / spectral data and peer-reviewed literature**\
    Use primary publications and dataset-specific citations where a
    database is not the authoritative source for the exact conditions or
    interpretation.

**Important:** Different molecular databases may use different line
parameters, partition functions, broadening conventions, temperature
ranges, isotopologue coverage, and units. They should not be treated as
interchangeable. Store provider-specific provenance and normalize only
through explicit, tested transformations.

### 14.3 Astronomy and spectral Python ecosystem

-   **Astropy** --- <https://www.astropy.org/>\
    Foundational astronomy tools, including FITS, units, time,
    coordinates, and related standards. Prefer established
    implementations over reimplementing mature standards.

-   **specutils** --- <https://specutils.readthedocs.io/>\
    Spectral data structures and analysis utilities. Evaluate whether
    its abstractions match ECAS's needs and avoid creating two competing
    definitions of a spectrum without a conversion contract.

-   **NumPy** --- <https://numpy.org/doc/>\
    Array operations and numerical representation.

-   **SciPy** --- <https://docs.scipy.org/doc/scipy/>\
    Scientific algorithms, optimization, integration, interpolation,
    signal processing, and numerical linear algebra. Each algorithm
    still needs method-appropriate validation.

-   **xarray** --- <https://docs.xarray.dev/>\
    Worth evaluating if ECAS begins handling multidimensional datasets
    with named dimensions and coordinates. It may be unnecessary for the
    current one-dimensional workflow; do not add it merely for future
    possibilities.

-   **h5py / HDF5** --- <https://docs.h5py.org/>\
    Potential option for large arrays and structured scientific
    datasets. Choose only after measuring storage needs and considering
    portability and schema complexity.

-   **Pint** --- <https://pint.readthedocs.io/>\
    General-purpose units. Compare with Astropy units and choose a
    coherent strategy rather than mixing units systems without explicit
    conversion rules.

-   **Matplotlib** --- <https://matplotlib.org/stable/>\
    Useful for static scientific figures and publication-style output.
    It can coexist with PyQtGraph if the division of responsibility is
    clear.

### 14.4 Atmospheric modeling and retrieval programs

Evaluate these as reference implementations, optional adapters, or
independent benchmarks---not as automatic drop-in replacements:

-   **petitRADTRANS** --- <https://petitradtrans.readthedocs.io/>\
    Atmospheric radiative-transfer modeling. Verify the specific
    version, opacity inputs, model assumptions, and integration pathway.

-   **POSEIDON** --- <https://poseidon-retrievals.readthedocs.io/>\
    Exoplanet atmospheric retrieval tools. Useful for understanding
    retrieval workflows and possible comparisons; dependencies and
    methods must be checked for the chosen use case.

-   **TauREx** --- <https://taurex.readthedocs.io/>\
    Atmospheric retrieval and forward-modeling framework. Its
    assumptions, interfaces, supported data, and version-specific
    behavior need review.

-   **PLATON** --- <https://platon.readthedocs.io/>\
    Exoplanet transmission-spectrum modeling and retrieval-related
    functionality. Confirm scientific scope and version-specific
    assumptions.

-   **RADIS** --- <https://radis.readthedocs.io/>\
    Spectroscopic modeling and line-by-line tools, especially relevant
    to molecular spectra in appropriate regimes. It is not a universal
    substitute for exoplanet atmospheric retrieval.

-   **TauREx / POSEIDON / petitRADTRANS / PLATON and peer-reviewed
    methods papers**\
    Read the underlying papers and versioned documentation. Agreement
    between programs is useful evidence only when their input data,
    assumptions, parameter definitions, and numerical settings are made
    comparable. Shared data or assumptions can make agreement
    non-independent.

Do not implement all these engines at once. Choose one supported
workflow, define a narrow adapter contract, and validate one integration
end-to-end before considering another.

### 14.5 Scientific/statistical methods

-   **emcee** --- <https://emcee.readthedocs.io/>\
    Ensemble Markov chain Monte Carlo sampling. Appropriate only when
    the likelihood, priors, convergence assessment, and posterior
    diagnostics are specified.

-   **dynesty** --- <https://dynesty.readthedocs.io/>\
    Dynamic nested sampling. Useful for certain posterior and evidence
    calculations; not a guarantee that evidence is reliable without
    adequate sampling and validated likelihoods.

-   **ArviZ** --- <https://python.arviz.org/>\
    Diagnostics and visualization for Bayesian analyses. Use the
    diagnostics that match the inference method and explain their
    interpretation.

-   **JAX** --- <https://docs.jax.dev/>\
    Automatic differentiation and accelerated numerical computation;
    only consider if it materially helps a defined model and the team
    can manage its compilation, precision, and deployment implications.

These tools solve different problems. Do not choose a sampler before
defining the statistical model. A sophisticated inference engine cannot
rescue a physically incorrect forward model, invalid uncertainty
assumptions, or incomplete input provenance.

### 14.6 User-interface and engineering references

-   **Qt for Python / PySide6** --- <https://doc.qt.io/qtforpython-6/>\
    Official Qt for Python documentation. If Beta uses another Qt
    binding, do not migrate without comparing licensing, compatibility,
    packaging, and actual needs.

-   **PyQtGraph** --- <https://www.pyqtgraph.org/>\
    Interactive plotting suited to desktop scientific workflows. Confirm
    supported versions and export behavior.

-   **pytest** --- <https://docs.pytest.org/>\
    Test framework.

-   **Hypothesis** --- <https://hypothesis.readthedocs.io/>\
    Property-based testing.

-   **Ruff** --- <https://docs.astral.sh/ruff/>\
    Linting and formatting tooling.

-   **PyInstaller** --- <https://pyinstaller.org/>\
    Application packaging. Packaged builds need independent smoke
    testing; source-level tests alone do not validate a release bundle.

-   **Sphinx** --- <https://www.sphinx-doc.org/>\
    Documentation system, especially for API/reference docs.

-   **MkDocs** --- <https://www.mkdocs.org/>\
    Markdown-oriented documentation site option.

-   **GitHub Actions** --- <https://docs.github.com/actions>\
    CI automation if it fits the repository's current setup.

### 14.7 Standards and reproducibility resources

-   **FITS standard and Astropy FITS docs** --- use the authoritative
    standard and established libraries for FITS parsing.
-   **ECSV documentation** --- use Astropy's documented ECSV format and
    schema conventions.
-   **IVOA standards** --- <https://www.ivoa.net/> for astronomy
    interoperability standards where relevant.
-   **FAIR principles** --- <https://www.go-fair.org/fair-principles/>
    for findability, accessibility, interoperability, and reuse; apply
    them pragmatically rather than as a checklist detached from user
    needs.
-   **ASDF** --- <https://asdf.readthedocs.io/> may be worth evaluating
    for structured scientific data and metadata if a concrete use case
    arises.
-   **Zenodo** --- <https://zenodo.org/> can support versioned research
    software/data releases and DOI assignment, subject to licensing and
    release policy.
-   **CITATION.cff** --- a repository-level citation file can help
    others cite the software itself.

### 14.8 Source-adoption checklist

Before ECAS depends on a database, library, or external program,
record: - what capability it provides; - the exact supported
version(s); - license and redistribution terms; - source data license
and attribution requirements; - API or file-format stability; -
supported platforms; - data size and performance; - security and
maintenance activity; - numerical/scientific assumptions; - test
strategy; - fallback behavior if unavailable; - whether it is mandatory
or optional; - how users are told which version was used.

A source list is a starting point for investigation, not proof that
every item is appropriate for ECAS.

------------------------------------------------------------------------

## 15. Data ingestion strategy for broad scientific usability

### 15.1 Support a format through a specification, not an extension list

For every supported format family, define: - file structure; - required
and optional metadata; - axis/signal semantics; - units and conversion
rules; - missing/invalid values; - multi-spectrum handling; - error
reporting; - maximum practical file size; - source provenance; -
round-trip or normalization expectations; - representative fixtures and
test cases.

The extension alone is insufficient. A `.txt` file can contain almost
anything.

### 15.2 Use a two-stage import design

**Stage 1: Parse** - detect format; - read tables/headers/metadata; -
retain raw column names and original units; - report parse warnings; -
do not silently assign scientific meaning.

**Stage 2: Interpret** - let the user map columns to coordinate, signal,
uncertainty, mask, or metadata; - choose/confirm axis and signal
quantity; - confirm units and conversion; - preview the result; - save
the interpretation as a reusable import profile when appropriate.

This is more flexible than a single rigid CSV schema and safer than
guessing column semantics automatically.

### 15.3 Import profiles should be explicit and reviewable

A profile may store: - instrument/export name; - delimiter and header
rules; - column mapping; - unit defaults; - signal interpretation; -
known metadata fields; - parser version; - profile version.

On subsequent imports, show the profile that will be applied. If the
input differs materially, warn the user instead of silently reusing an
invalid mapping.

### 15.4 Preserve original units and conversions

The normalized object can use standard internal units, but it should
preserve: - original units; - normalized units; - conversion
formula/version; - any assumptions; - whether the conversion was
automatic or user-confirmed.

Do not silently convert percent transit depth to fraction or absorbance
to transmittance without recording the transformation and showing it in
the import summary.

### 15.5 Never conflate import success with quality approval

Use separate statuses: - parsed; - interpreted; - structurally valid; -
scientifically eligible for a particular analysis; - analyzed; -
benchmarked/validated.

A file can parse successfully but fail eligibility for a comparison
because it lacks required metadata or has incompatible units. That is a
good, explainable outcome---not an import bug.

------------------------------------------------------------------------

## 16. Comparison and alignment design

### 16.1 Define compatibility before computing

Before comparing two spectra, validate: - data roles; -
observable/quantity semantics; - units; - coordinate units and frame; -
coverage overlap; - resolution/response compatibility; - uncertainty
representation; - data quality masks; - duplicate or non-monotonic
coordinates; - provenance and source identity; - whether
interpolation/extrapolation is allowed.

Return a structured eligibility result with: - status; - blocking
errors; - warnings; - assumptions; - remediation suggestions.

Do not return a single opaque boolean when the user needs to understand
why a comparison cannot proceed.

### 16.2 Make alignment a scientific operation with a record

Alignment may involve: - unit conversion; - coordinate reversal; -
interpolation; - bin integration; - convolution; - masks; - covariance
propagation.

Record which operations were applied, with their parameters and limits.
Never extrapolate silently. If covariance exists, transformations must
propagate it consistently or explicitly state why the diagnostic does
not support it.

### 16.3 Distinguish native overlay, aligned comparison, and model fit

These should be separate modes in the UI:

-   **Native overlay:** show each spectrum on its own compatible axis
    without pretending samples are directly paired.
-   **Aligned comparison:** transform/resample under explicit rules to a
    common coordinate/binning scheme.
-   **Model fit:** evaluate a defined model against data under an
    explicit objective/likelihood.

The display should state which mode is active. A shared x-axis alone
does not mean the samples are physically comparable.

------------------------------------------------------------------------

## 17. Project persistence and analysis records

### 17.1 Treat a project as a research workspace, not just a file container

A project should conceptually link: - target/object metadata; -
observations and reference products; - raw source artifacts; -
normalized spectra; - analysis configurations; - derived results; -
notes and citations; - software/method versions; - validation state.

Do not force every source into one identical metadata schema. Use a
stable common core plus typed source-specific metadata, with validation
and versioning.

### 17.2 Save immutable analysis runs

An analysis run should have an identifier and preserve: - input IDs and
hashes; - configuration and effective defaults; - method version; -
software revision; - dependency versions as needed; - warnings; -
outputs and output hashes; - completion/failure/cancellation status; -
timestamps.

If a user edits settings, create a new configuration/run record rather
than silently mutating the historic analysis record. Provide "duplicate
settings and rerun" as an explicit workflow.

### 17.3 Protect against corruption and partial writes

Test: - process interruption during save; - disk full / permission
errors; - corrupt database or artifact; - failed migrations; - missing
external source files; - hash mismatch; - concurrent or repeated save
attempts; - recovery and user messaging.

Use transactions and atomic file replacement where appropriate. Make
backup/recovery behavior explicit. Do not imply that a digest alone
guarantees full project integrity.

### 17.4 Export a self-describing research package

Potential export: - report in Markdown/PDF/HTML; - machine-readable
configuration; - derived numerical tables; - plot images/vector
output; - provenance manifest; - citation list; - software/version
metadata; - optional raw inputs subject to size/license/privacy
constraints.

The report should clearly distinguish data, transformations, model
assumptions, results, warnings, and scientific validation status.

------------------------------------------------------------------------

## 18. Architecture choices for future model engines

### 18.1 Use adapters only where they reduce real coupling

If ECAS supports an external engine, define a minimal contract: -
capability declaration; - input model/configuration; - required data and
opacity format; - output schema; - units and conventions; -
warnings/errors; - engine/version metadata; - cancellation/progress
behavior; - license and installation status.

The adapter should not pretend all engines have identical physics or
parameters. Keep engine-specific settings in a namespaced configuration,
and map only parameters with genuinely equivalent definitions.

### 18.2 Avoid false equivalence between model engines

Different engines can differ in: - opacity sources; - line lists and
cross-sections; - pressure/temperature grids; - cloud and haze
prescriptions; - radiative-transfer methods; - geometry; - priors and
likelihoods; - treatment of systematics; - parameterization and
reference radius; - interpolation and numerical approximations.

If ECAS offers a common interface, the result must still record the
actual engine and assumptions. A common button must not imply scientific
equivalence.

### 18.3 Optional dependencies should degrade gracefully

For each optional engine: - detect whether it is installed; - display
version and availability; - explain how to install it; - explain
licensing and resource requirements; - disable only the related
capability when absent; - keep the core application usable; - test both
installed and missing-dependency states.

Avoid importing a heavyweight optional engine at application startup if
it can be loaded when the feature is requested.

------------------------------------------------------------------------

## 19. Release engineering and operational reliability

### 19.1 Source execution and packaged application are different products

The program must be tested as users will run it: - fresh environment; -
clean installation; - packaged executable; - paths with spaces and
non-ASCII characters; - no network; - slow or unavailable network; -
missing optional packages; - read-only locations and permission
failures; - first launch and existing user data; - upgrade from a prior
project schema.

### 19.2 Define supported platforms deliberately

Do not claim support for an OS just because it imports successfully on a
developer's machine. Choose a realistic supported matrix, e.g. one
primary desktop OS initially and others when tested.

Record: - Python/runtime version; - OS/version; - architecture; - GUI
binding; - package manager; - supported build artifacts; - known
limitations.

### 19.3 Logging and diagnostics

Use structured logs for: - import failures; - provider requests and
responses (without secrets); - cache hits/misses and validation
failures; - model execution and timing; - project persistence errors; -
cancellation; - unhandled exceptions.

Avoid logging raw user data, tokens, credentials, or sensitive local
paths unnecessarily. Provide a way to copy a sanitized diagnostic report
for bug reports.

### 19.4 Network behavior

External archive features should support: - timeouts; - bounded retries
with backoff; - rate-limit awareness; - cancellation; - cache status; -
stale-cache disclosure; - provider error messages; - no-network
behavior; - reproducible record of what was retrieved.

Do not retry every error indefinitely. A bad query, authentication
error, unsupported product, or schema change may need a clear user
action rather than repeated requests.

------------------------------------------------------------------------

## 20. Security, licensing, and research integrity

Even a local desktop scientific tool needs basic security discipline: -
validate imported files and avoid unsafe deserialization; - limit file
size and handle malformed archives; - do not execute content from
scientific data files; - avoid storing secrets in project files or
logs; - use HTTPS and provider-supported authentication; - validate
external model/configuration inputs; - keep dependencies updated; -
record licenses and attribution; - respect database download terms and
redistribution restrictions; - distinguish user-supplied and externally
retrieved content.

Scientific integrity also includes: - no fabricated data; - no
fabricated citations; - no overstated feature maturity; - no hidden data
transformations; - no claim that automated tests establish empirical
validity; - no unrecorded manual override of critical scientific
assumptions.

------------------------------------------------------------------------

## 21. Prioritized roadmap

The roadmap should be gated by evidence and should not be interpreted as
authorization to implement all items. Each phase needs a small plan and
review.

### Phase 0 --- Establish a trustworthy baseline

**Objective:** Know exactly what is in the current repository and what
is already verified.

Tasks: 1. Inspect current branch, working tree, recent commits, and
repository instructions. 2. Identify authoritative project-state,
decision, architecture, validation, and task-log documents. 3. Reconcile
current README/Overview claims with actual behavior. 4. Inventory
user-visible capabilities from both v1 and Beta. 5. Identify duplicate
entry points and package/build inconsistencies. 6. Record actual test
and benchmark status by revision. 7. Establish the initial list of
scientific and UX risks.

Exit criteria: - capability inventory exists; - every maturity claim has
an evidence label; - conflicting docs are listed and assigned an
authoritative resolution; - no implementation refactor has begun merely
because the audit found complexity.

### Phase 1 --- Define the product and scientific contracts

**Objective:** Specify the key workflows and data semantics before large
changes.

Tasks: 1. Define the core user journeys. 2. Define spectrum/data-role
semantics and unit conventions. 3. Define provenance and analysis-run
requirements. 4. Specify comparison eligibility and alignment behavior.
5. Write method specifications for the first supported scientific
workflow. 6. Define UI progressive-disclosure rules and a small design
system. 7. Choose the minimum coherent toolchain.

Exit criteria: - data contracts have examples; - critical assumptions
and failure conditions are explicit; - workflow acceptance criteria are
testable; - proposed features are not mislabeled as implemented.

### Phase 2 --- Stabilize the core data and reliability layer

**Objective:** Make imports, units, persistence, and provenance
trustworthy.

Tasks: 1. Improve import interpretation without hard-coding one CSV
schema. 2. Add representative FTIR/UV-Vis fixtures where available;
otherwise state limitations and use carefully documented synthetic
fixtures. 3. Add schema versioning/migrations where needed. 4. Verify
source hashes, cache metadata, and project integrity behavior. 5. Test
corruption, partial writes, missing files, and recovery. 6. Add reusable
unit/axis conversion tests. 7. Add structured provenance and immutable
analysis-run records.

Exit criteria: - supported import formats are documented by semantics,
not extension alone; - invalid/ambiguous metadata are surfaced; -
persistence and migrations are tested; - derived results retain
traceable inputs.

### Phase 3 --- Build one complete scientific workflow end-to-end

**Objective:** Prove the architecture on a bounded, meaningful use case.

Choose one workflow based on user priority---for example, import a
supported spectrum, inspect units/metadata, align with a compatible
reference, calculate defined diagnostics, save the result, and export a
report.

Tasks: 1. Specify equations, assumptions, valid inputs, and failure
modes. 2. Implement/test scientific services independently of the GUI.
3. Add a simple guided UI. 4. Add analytic and property tests. 5. Add a
published or independent benchmark where feasible. 6. Add project
persistence and report provenance. 7. Perform a manual desktop
acceptance run.

Exit criteria: - the workflow is understandable to the user; - results
are reproducible within declared limits; - scientific status is stated
accurately; - failures are actionable; - documentation matches behavior.

### Phase 4 --- Recover selected v1 UX and workflows

**Objective:** Bring back useful functionality without destabilizing
Beta.

Candidate order: 1. Improve visual hierarchy and common plotting
behavior. 2. Add a guided Identify/Explore workflow with explicit
candidate limitations. 3. Add a Transit Visualizer with clear
educational/model status. 4. Port or reimplement selected v1 fitting or
transit-analysis capabilities only after method specifications and
benchmarks exist. 5. Connect exploratory views to saved project records.

Do not port all of v1 at once. Prioritize features based on user value,
scientific importance, and verification cost.

### Phase 5 --- Expand scientific capability deliberately

Possible work: - broader format-specific import support; - additional
archive adapters; - more molecular reference sources; -
instrument-response handling; - improved uncertainty/covariance
support; - advanced forward models; - retrieval/inference methods; -
model comparison; - batch workflows.

For each addition, require a method specification, source/version
provenance, tests, a benchmark plan, UI design, and maintenance owner.

### Phase 6 --- Operational hardening and release

Tasks: - supported-platform matrix; - fresh-environment installation; -
packaged app testing; - migration and upgrade testing; - performance
benchmarks on representative data; - dependency/license audit; - release
notes and user guide; - final validation summary with known limitations.

### Why this order?

It minimizes the risk of building a polished interface around unstable
scientific semantics, or an elaborate modeling engine on top of
unreliable imports and provenance. It also allows ECAS to deliver useful
capability after each phase rather than waiting for a complete rewrite.

------------------------------------------------------------------------

## 22. Decision framework: improve, replace, or rewrite?

For every major component, score the following qualitatively:

-   scientific correctness and clarity;
-   testability;
-   maintainability;
-   UX value;
-   integration cost;
-   migration risk;
-   performance;
-   packaging implications;
-   documentation quality;
-   availability of independent benchmarks.

Prefer **incremental improvement** when: - the component's purpose is
clear; - its core behavior is sound; - defects are bounded; - tests can
be added; - the interface can be stabilized.

Prefer **replacement of one component** when: - the implementation is
tightly coupled; - the algorithm or data model is poorly specified; -
existing tests cannot establish correctness; - a well-supported
alternative exists; - the replacement can be validated independently.

Consider a **full rewrite** only if: - a repository-wide audit shows
that core abstractions fundamentally block the required workflows; -
repeated local replacements would cost more and carry more risk than a
controlled rewrite; - the intended behavior and scientific contracts are
already specified; - regression/benchmark fixtures exist; - there is a
migration plan for projects and saved results; - a staged coexistence
strategy exists; - the project can tolerate the temporary loss of
feature parity.

A rewrite should start with one thin vertical slice that imports real
data, validates semantics, runs a tested calculation, saves provenance,
and presents the result. If this slice is not convincingly better, do
not scale it into a full rewrite.

------------------------------------------------------------------------

## 23. How Agents should collaborate on this program

The current project workflow---Agent 1 plans/reviews, Agent 2 inspects and
implements in small bursts---is appropriate if it remains
evidence-based.

### 23.1 Recommended loop

1.  **State the user problem.** One bounded issue, not "make ECAS
    better."
2.  **Gather evidence.** Agent 2 inspects current source, tests, docs,
    callers, and recent changes.
3.  **Propose a plan.** PLAN mode only; include files, behavior, risks,
    tests, and documentation.
4.  **Review critically.** Check scientific semantics, architecture,
    unnecessary complexity, migration risk, and acceptance criteria.
5.  **Approve a narrow change.** Explicitly state what is in and out of
    scope.
6.  **Implement.** ACT mode; preserve unrelated behavior.
7.  **Verify.** Run focused tests, relevant broader tests, manual
    checks, and inspect the diff.
8.  **Document.** Update only the authoritative documents affected.
9.  **Record status.** Distinguish implemented, tested, manually
    verified, benchmarked, and scientifically reviewed.
10. **Commit at a logical checkpoint.** Keep changes reviewable and
    reversible.

### 23.2 Standard ACT prompt requirements

Each ACT prompt should state: - objective; - verified current state; -
exact scope; - constraints and decisions to preserve; - acceptance
criteria; - tests/commands; - manual checks; - required documentation
changes; - files not to touch; - reporting format; - how to describe
incomplete work.

Do not let agent turn a focused task into an architectural refactor. If
it discovers a separate issue, have it report and defer it unless it
blocks the task.

### 23.3 Avoid circular review

If two substantive review/correction cycles fail to resolve the same
issue: - stop repeating similar prompts; - isolate the unresolved
requirement; - request specific evidence or a minimal reproduction; -
decide whether the plan, implementation, environment, or requirement is
at fault; - switch tactics, simplify, or implement the bounded change
directly when appropriate.

### 23.4 Keep plans and implementation logs useful

A plan is a proposal, not a status record. An implementation log is
historical evidence, not the current source of truth. A project-state
document should summarize current verified state and link to detailed
records.

Do not continuously rewrite old plans to match the present. Preserve
history and add corrections or follow-up records.

------------------------------------------------------------------------

## 24. Specific risks and mitigations

  -----------------------------------------------------------------------
  Risk                    Why it matters          Mitigation
  ----------------------- ----------------------- -----------------------
  Full rewrite too early  Loses tested behavior   Capability inventory
                          and creates a long      and vertical-slice
                          feature gap             proof first

  Blind merge             Combines incompatible   Port behavior under
                          data models and         explicit contracts
                          assumptions             

  UI complexity           Users are overwhelmed   Guided defaults,
                          by scientific           progressive disclosure,
                          parameters              contextual explanations

  Hidden scientific       Results appear more     Explicit method specs,
  assumptions             authoritative than      warnings, provenance,
                          warranted               report language

  Incorrect unit handling Produces plausible but  Quantity-aware data
                          wrong results           model and analytic
                                                  conversion tests

  Overclaiming molecular  Scientific              Separate exploratory
  detection               misinterpretation       matching from
                                                  calibrated inference

  Test-count confusion    Historical reports      Record revision,
                          mistaken for current    command, environment,
                          verification            and output

  Documentation drift     Users and agents follow Documentation change
                          false instructions      matrix and CI checks

  Optional dependency     Feature breaks startup  Lazy loading,
  failure                 or packaging            capability checks,
                                                  missing-dependency
                                                  tests

  Archive/API changes     Retrieval fails or      Versioned adapters,
                          silently changes data   schema validation,
                                                  cached raw artifacts

  Overly broad format     Generic CSV test        Representative fixtures
  claims                  mistaken for            and format-specific
                          FTIR/UV-Vis support     specifications

  Model-engine            Maintenance and         One adapter at a time
  proliferation           scientific semantics    with clear capability
                          fragment                contract

  Premature               Build/debug burden      Profile first; keep
  multi-language code     exceeds benefit         Python default

  Fancy visualization     Animation looks like    Label illustrative vs
  overstates science      validated physics       computed vs fitted
                                                  output

  Over-abstracted         More indirection than   Add abstractions only
  architecture            benefit                 for demonstrated
                                                  variation

  Inadequate real-data    Synthetic tests miss    Independent and
  benchmarks              scientific errors       published benchmarks
                                                  where feasible

  Unclear licensing       Data or dependency      Record source and
                          redistribution is       dependency licenses
                          impermissible           before packaging

  Poor failure recovery   Users lose work or      Transactional saves,
                          cannot diagnose errors  backups, structured
                                                  logs, actionable errors
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 25. Immediate next steps

Do not begin with a large implementation prompt. The most useful next
action is a **read-only consolidation assessment** against the current
repository.

### Step 1 --- Have Agents inventory the current state

Ask it to: - inspect current branch and working tree without editing; -
read `agent.md` and authoritative project docs; - map actual entry
points, modules, tests, dependencies, and build configuration; -
identify current implementations of v1-derived or Beta capabilities; -
find contradictions between README, Overview, project state,
architecture docs, and actual code; - inventory import, project
persistence, archive/reference retrieval, comparison, transit modeling,
feature identification, and visualization workflows; - identify existing
tests and benchmark fixtures; - separate confirmed facts from
inferences; - produce a concise capability matrix and risk list; - make
no code or documentation edits.

### Step 2 --- Review and approve the baseline

Do not ask agent to propose a full rewrite yet. First resolve: - which
workflows must be retained; - which capabilities are actually working; -
which scientific methods are intended to be research-grade versus
exploratory; - which UI elements are highest value; - what
representative data can be used for validation; - what evidence is
missing.

### Step 3 --- Choose one vertical slice

Choose a high-value workflow that is small enough to verify from import
through scientific result, persistence, and export. Define its
scientific method and UX acceptance criteria first.

### Step 4 --- Establish documentation and validation gates

Adopt the definition of done, evidence labels, documentation change
matrix, and test-run record. Update existing authoritative documents
rather than multiplying project-state files.

### Step 5 --- Iterate

After the vertical slice is proven, select the next capability based on
user value, scientific risk, and implementation cost.

------------------------------------------------------------------------

## 26. Ready-to-paste Agent prompt: read-only consolidation assessment

Use this prompt in agent **PLAN mode**. It is deliberately limited to
investigation; it does not authorize code edits or a rewrite.

> **Mode: PLAN only --- read-only repository assessment. Do not edit or
> create files. Do not run commands that modify the working tree.**
>
> **Objective:** Produce an evidence-based consolidation assessment for
> ECAS --- Exoplanetary Characterization & Astrochemistry Suite,
> comparing the current Beta checkout with the known useful workflows
> and UX ideas from v1. We need to decide how to preserve the best of
> both versions without committing prematurely to a full rewrite.
>
> **First inspect:** the current Git branch and working-tree status,
> `agents.md`, `README.md`, `docs/brains/PROJECT_STATE.md`,
> `docs/brains/DECISIONS.md`, architecture documentation, validation
> strategy, current task/chunk records, tests, dependency/packaging
> configuration, and recent relevant commits. Verify actual paths; do
> not assume historical paths remain valid.
>
> **Inventory these capability areas:** 1. Application entry points,
> startup, main-window orchestration, packaging, and dependencies. 2. UI
> structure, visual consistency, empty/error/loading states, plotting,
> accessibility, and workflow complexity. 3. Spectrum import: CSV,
> delimited text, ECSV, FITS, and any instrument-specific formats
> actually supported. 4. FTIR/UV-Vis suitability: distinguish actual
> tested format support from generic text parsing; do not claim support
> without evidence. 5. Project persistence, schema/versioning, raw data
> retention, provenance, hashes, caches, and migration behavior. 6.
> NASA/archive data retrieval and molecular-reference sources, including
> product scope, metadata, and failure/cancellation handling. 7.
> V1-style feature identification, spectroscopy fitting, transit
> analysis, transit visualization/animation, and related capabilities:
> identify current equivalents, absent capabilities, and potential
> reuse/reimplementation candidates. 8. Comparison eligibility,
> axis/unit conversion, alignment/binning, uncertainty/covariance,
> residual diagnostics, and scientific limitations. 9. Transmission
> forward modeling, any inference/retrieval functionality, and external
> model-engine adapters. 10. Tests, analytic cases, property tests,
> benchmarks, manual acceptance, packaged-build verification, and
> current evidence status. 11. Documentation consistency, especially
> README, Overview, PROJECT_STATE, architecture summaries, DECISIONS,
> and validation/checkpoint records.
>
> **For each finding:** cite exact file paths and relevant
> symbols/tests. Label it as (a) observed in source, (b) covered by an
> existing test, (c) reported in documentation but not independently
> verified, (d) inference, or (e) unknown. Do not treat the existence of
> a function as proof of scientific validity or a user-ready workflow.
> Do not treat historic test counts as current unless the exact revision
> and run evidence are established.
>
> **Deliverables in the response only; do not write files:** - A
> capability matrix with V1 value, current Beta status, evidence,
> scientific risk, UX value, and recommendation: keep / wrap /
> reimplement / retire / defer / investigate. - A proposed minimal
> target architecture based on actual code, not a generic rewrite. - The
> 10 highest-value issues ranked by user impact, scientific risk, and
> implementation risk. - A short list of architecture and scientific
> decisions that must be settled before major implementation. - One
> recommended first vertical slice with acceptance criteria and tests. -
> A documentation update policy that uses existing authoritative files
> and avoids duplicate status documents. - Explicit unresolved questions
> and what evidence would resolve each.
>
> **Constraints:** Do not implement anything. Do not propose a full
> rewrite as the default. Do not add languages, frameworks, model
> engines, or dependencies without a concrete need. Prefer preserving
> sound existing behavior and replacing bounded components. Do not claim
> scientific validation without independent benchmarks or review. Keep
> the assessment focused and evidence-linked.
>
> End with a recommendation: improve Beta incrementally, replace
> specific components, or consider a rewrite---and explain what evidence
> supports that choice.

------------------------------------------------------------------------

## 27. Final recommendation

The long-term goal should not be "the largest possible feature set." It
should be **a coherent research environment where each capability has a
defined scientific meaning, a manageable workflow, traceable inputs,
tested numerical behavior, and an honest statement of limitations**.

The most promising direction is to use Beta as the likely integration
base while treating v1 as a source of valuable workflows and interaction
ideas. This is a provisional strategy, not a verdict that every part of
Beta is better. Reconfirm it through the read-only assessment.

Preserve v1's approachable experience where it improves comprehension.
Preserve Beta's structured data and provenance work where it is sound.
Reimplement tightly coupled or scientifically ambiguous components from
explicit specifications. Keep Python as the default. Add external
databases and model engines selectively. Use independent benchmarks and
scientific review for claims that affect interpretation. Make
documentation and verification part of every task.

**Build one complete, validated workflow at a time.** A smaller workflow
that is transparent, reproducible, and trustworthy is a stronger
foundation for a comprehensive scientific suite than a broad collection
of partially connected features.


