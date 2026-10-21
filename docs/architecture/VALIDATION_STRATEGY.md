# ECAS Validation Strategy

**Document status:** Draft for review  
**Project:** Exoplanet Characterization and Spectral Analysis (ECAS)  
**Related documents:** `ECAS.md`, `ARCHITECTURE.md`, `DATA_FLOW.md`, `MODULE_RESPONSIBILITIES.md`, `DATA_MODELS.md`  
**Implementation status:** This document does not authorize implementation.

---

## 1. Purpose

This document defines how ECAS will evaluate the scientific usefulness, reliability, and limitations of its spectral comparison methods.

The initial application will compare exoplanet transmission-spectrum observations with molecular reference data and produce candidate scores and supporting diagnostics. Validation must establish what those results mean, under which conditions they are useful, and what conclusions the available evidence does not support.

This document defines the validation framework. It does not select the first comparison algorithm, designate specific benchmark datasets, or establish numerical thresholds. Those choices require investigation of accessible scientific data and published evidence.

### 1.1 Primary objectives

The validation process must:

1. Identify suitable published detections, non-detections, and control cases.
2. Determine whether the selected method can distinguish relevant spectral correspondence from misleading matches.
3. Evaluate candidate ranking and scoring behavior against documented evidence.
4. assess the effects of data quality, uncertainty, spectral coverage, resolution, and reference selection.
5. Establish defensible decision thresholds only when sufficient evidence supports them.
6. Distinguish development and tuning from evaluation intended to estimate performance.
7. Record the limits of the conclusions supported by the evaluation.
8. Provide a repeatable procedure for evaluating future comparison methods.

### 1.2 Scope

The initial validation effort concerns **spectral comparison and candidate scoring**, not quantitative atmospheric abundance estimation or full atmospheric retrieval.

A successful benchmark evaluation does not automatically establish that ECAS can confirm atmospheric detections. Any detection-related interpretation must be justified by the evidence, method, and validation procedure actually used.

---

## 2. Governing Principles

### 2.1 Real scientific evidence

Scientific validation must be grounded in real, traceable observations and documented scientific conclusions.

Synthetic data may be used for specific software tests or controlled diagnostic experiments, provided they are clearly labeled. Synthetic data must not be represented as real astronomical observations or used as a substitute for independent scientific benchmark evidence.

### 2.2 Published conclusions are evidence, not infallible labels

Published detections and non-detections provide starting points for benchmark construction. They must not be treated as unquestionable ground truth without reviewing the original study, its methods, uncertainty, and subsequent context where relevant.

A publication may report tentative evidence, conflicting interpretations, or a result that depends on a particular dataset or analysis method. The benchmark record must preserve those distinctions.

### 2.3 Validation must match the intended claim

A method that ranks spectra by similarity is not necessarily capable of estimating detection probability or establishing atmospheric presence.

Validation claims must match the task evaluated:

- **Similarity:** Does the method quantify correspondence between the selected inputs?
- **Ranking:** Does the method rank supported candidates usefully against competing candidates?
- **Discrimination:** Can the method distinguish relevant benchmark cases from suitable non-detections or controls?
- **Calibration:** If a method outputs probabilities, do those probabilities agree with observed outcome frequencies under an appropriate evaluation?
- **Detection support:** Does the combined evidence justify a detection-related interpretation for the defined task?

These are different evaluation questions. Success at one does not establish success at the others.

### 2.4 Preserve uncertainty and limitations

Validation records must preserve known uncertainty, missing metadata, ambiguous scientific conclusions, and limitations affecting interpretation.

Unknown information must not be silently replaced with assumptions. Where uncertainty prevents a defensible evaluation, the case may be excluded from a particular metric while remaining documented in the benchmark inventory.

### 2.5 No arbitrary thresholds

Thresholds must not be selected merely because they produce attractive scores or reproduce a desired result.

Threshold selection must consider benchmark performance, uncertainty in the evaluation metrics, the consequences of false positives and false negatives, and the intended use of ECAS.

### 2.6 Reproducibility

Each evaluation must identify the exact benchmark inputs, reference datasets, preparation operations, comparison method, configuration, software versions, and evaluation procedure used.

A change to a method or its preparation pipeline must be traceable to a new evaluation configuration.

---

## 3. Validation Questions

The following questions define the initial validation program. They do not require all answers to be available before the first implementation begins.

| Question | What must be established |
|---|---|
| Data suitability | Can the method accept the selected observation and reference without violating its scientific requirements? |
| Candidate correspondence | Does the method produce interpretable outputs when a candidate reference is compared with an observation? |
| Competing candidates | Can the method distinguish the intended candidate from plausible alternatives? |
| Negative cases | Does the method avoid treating suitable non-detections or controls as strong positive evidence? |
| Robustness | How sensitive are results to noise, coverage, resolution, processing, and reference choice? |
| Uncertainty | How do measurement uncertainty and incomplete metadata affect the outputs and their interpretation? |
| Reproducibility | Can the same recorded inputs and configuration reproduce or explain the reported result? |
| Generalization | Do results remain useful on evaluation cases that were not used to develop or tune the method? |
| Interpretation | Which conclusions are supported by the observed performance, and which remain unsupported? |

The first benchmark investigation should prioritize questions that can be answered using accessible, well-documented data.

---

## 4. Benchmark Case Design

ECAS should build a curated benchmark collection from published observations and their associated scientific context.

A benchmark case is an evaluation record with a documented purpose, source evidence, required data, and an explicitly defined expected interpretation. It may contain one or more observations, candidate references, and supporting records.

### 4.1 Benchmark categories

The initial benchmark inventory should consider the following categories.

**A. Published detection cases**

Cases in which a study reports evidence for a molecular species in an exoplanet atmosphere.

These cases test whether ECAS produces useful correspondence or candidate-ranking results under the conditions represented by the selected observations.

Inclusion does not mean ECAS is expected to reproduce the published conclusion automatically. Differences in data products, reference data, spectral coverage, and analysis methods may explain differences in outcome.

**B. Published non-detection cases**

Cases in which an appropriate study reports that a molecular species was not detected or that the available observations did not support a detection under the study's stated conditions.

These cases help assess whether the method produces misleadingly strong candidate results in situations where the published evidence does not support the same claim.

A non-detection is not proof that the molecule is absent. Its meaning depends on the observation, sensitivity, wavelength coverage, analysis assumptions, and strength of the published constraint.

**C. Negative or comparison controls**

Cases chosen to investigate misleading correspondence, background structure, or alternative explanations for a candidate match.

Potential controls may include plausible competing molecular references or observations that do not support the target interpretation. The suitability of each control must be scientifically justified; arbitrary unrelated spectra are not sufficient evidence of meaningful discrimination.

**D. Ambiguous or disputed cases**

Cases where the published evidence is tentative, conflicting, or dependent on interpretation.

These cases should initially be kept separate from the clearest evaluation cases. They may be useful for examining limitations and uncertainty but should not be assigned a definitive positive or negative label without justification.

**E. Technical and synthetic test cases**

Controlled inputs used to verify parsing, numerical behavior, known transformations, error handling, or specific algorithm properties.

These cases belong primarily to software and method diagnostics. Their results must be distinguished from evaluation on real astronomical benchmark observations.

### 4.2 Benchmark inclusion criteria

Each proposed scientific benchmark should be assessed against the following criteria:

- The source publication or authoritative scientific record is identifiable.
- The relevant scientific conclusion and its scope are documented.
- The underlying observation or a suitable documented data product is accessible.
- The data have sufficient metadata to understand their spectral quantity, units, coverage, and processing state, or the missing information is explicitly recorded.
- The relationship between the observation, target molecule, and selected reference can be evaluated.
- The case is relevant to the intended comparison task.
- The case does not require unsupported assumptions merely to make it usable.
- The case can be evaluated without violating applicable source access or usage restrictions.

A case that fails one criterion need not be discarded from all research. It may be retained as contextual evidence while excluded from a particular metric or benchmark subset.

### 4.3 Benchmark prioritization

The initial shortlist should favor cases with:

1. Accessible and traceable observations.
2. Clear published conclusions and relevant citations.
3. Sufficient metadata for meaningful comparison.
4. Suitable molecular references.
5. A range of observation and reference characteristics relevant to the initial method.
6. Manageable data acquisition and preparation requirements.

The goal is a small, defensible initial benchmark set rather than a large collection of poorly characterized cases.

The actual cases and their supporting publications remain to be researched and selected.

---

## 5. Benchmark Records and Evidence

Every benchmark case must have a structured record. The final fields will be aligned with `DATA_MODELS.md`.

### 5.1 Required information

A benchmark record should include, where applicable:

- Stable benchmark identifier.
- Target planet and relevant aliases or catalog identifiers.
- Observation identifiers and source versions.
- Source archive, publication, and persistent identifiers such as a DOI where available.
- Target molecule or candidate set.
- Molecular reference identities and representation types.
- Published result and its original terminology.
- Evidence supporting the benchmark interpretation.
- Observation and reference limitations.
- Relevant wavelength coverage, resolution, uncertainty, and processing information.
- Intended benchmark role: development, tuning, evaluation, control, or diagnostic.
- Inclusion decision and rationale.
- Known ambiguity, disagreement, or missing information.
- Date and version of the benchmark record.

### 5.2 Evidence categories

ECAS should distinguish the following states rather than forcing every case into a simple positive/negative label:

- **Supported detection:** The cited evidence supports the stated detection claim within its documented scope.
- **Reported non-detection:** The cited study reports no supported detection under its stated conditions.
- **Ambiguous:** The evidence does not justify a confident binary interpretation for the intended evaluation.
- **Conflicting evidence:** Relevant sources reach materially different conclusions.
- **Insufficient information:** Available records do not permit a defensible interpretation.

These are proposed benchmark-evidence categories, not final application detection labels.

The original published wording and conclusion must remain available even if ECAS uses a simplified internal category for a particular evaluation.

### 5.3 Conflicting publications and revised results

When publications disagree or later analyses materially revise an earlier interpretation, ECAS must record the disagreement and relevant chronology.

A newer publication should not silently overwrite an earlier benchmark record. The benchmark curator must document which evidence is being used for a particular evaluation and why.

If the disagreement cannot be resolved adequately for the intended task, the case should be excluded from evaluations that require a clear reference outcome or analyzed separately.

---

## 6. Development, Tuning, and Evaluation Separation

Validation must reduce the risk of reporting overly optimistic performance because the same evidence was used to design and evaluate the method.

### 6.1 Distinct roles

Benchmark cases should be assigned explicit roles:

- **Development:** Used to understand the data, investigate algorithm behavior, and identify implementation requirements.
- **Tuning:** Used to select method settings, preprocessing choices, ranking rules, or decision thresholds.
- **Evaluation:** Reserved for assessing performance after relevant method choices have been fixed.
- **Diagnostic:** Used to investigate specific failure modes or technical behavior without necessarily contributing to a performance estimate.

A case may be used for more than one exploratory purpose, but that reuse must be recorded. Results from reused cases must not be presented as independent evaluation.

### 6.2 Preferred separation

Where the number and diversity of available cases permit, evaluation cases should be separated from development and tuning cases.

The separation strategy must consider dependencies between cases. For example, multiple observations of the same planet or closely related data products may not provide independent evidence if split across development and evaluation groups.

The final grouping strategy depends on the size and structure of the benchmark collection. A very small benchmark set may not support a reliable independent performance estimate; ECAS must state this limitation rather than imply otherwise.

### 6.3 Threshold selection

If a method requires a decision threshold, the threshold-selection procedure must be defined before reporting final evaluation performance.

Thresholds should be selected using development or tuning evidence, based on the intended task and the relative consequences of errors. Evaluation cases must not be repeatedly used to adjust the threshold and then reported as independent confirmation of its performance.

If a defensible threshold cannot be established from available evidence, ECAS should report continuous scores or rankings without assigning a validated binary decision.

### 6.4 Changes after evaluation

If a method, threshold, reference set, or preparation procedure changes materially after evaluation, the change must be recorded.

Previous results remain part of the evaluation history. A revised method may require a new evaluation, and any reuse of previous benchmark cases must be disclosed.

---

## 7. Evaluation Metrics

The first comparison method has not been selected, so the final metrics must remain open. Metrics should be chosen only after the intended output and benchmark structure are understood.

Different metrics answer different questions and should not be treated as interchangeable.

### 7.1 Candidate-ranking metrics

If the intended output ranks candidate molecules, evaluation should determine whether the ranking places relevant supported candidates ahead of plausible alternatives.

Potential metrics to investigate include:

- Rank of a benchmark-supported candidate.
- Mean or median rank across eligible cases.
- Top-\(k\) retrieval performance, where a defined number of leading candidates is relevant.
- Pairwise ranking performance when benchmark cases support a defensible comparison.

These are candidate metrics for investigation, not approved requirements. Their suitability depends on how benchmark outcomes and competing candidates are defined.

### 7.2 Classification metrics

If the method eventually produces a validated binary classification for a clearly defined task, potential metrics include:

- **Sensitivity / recall:** Fraction of reference-positive cases classified as positive.
- **Specificity:** Fraction of reference-negative cases classified as negative.
- **Precision:** Fraction of predicted-positive cases that are reference-positive under the benchmark definition.
- **False-positive rate:** Fraction of reference-negative cases incorrectly classified as positive.
- **False-negative rate:** Fraction of reference-positive cases incorrectly classified as negative.
- **Balanced accuracy:** A summary that weights sensitivity and specificity equally.

These metrics require defensible case labels and an explicitly defined unit of evaluation. They must not be calculated by treating every reported non-detection as proof of molecular absence.

Precision and other prevalence-dependent metrics also depend on the composition of the benchmark collection. Results from a curated benchmark must not automatically be interpreted as real-world predictive performance.

### 7.3 Score discrimination

If the method returns continuous scores, ECAS should investigate whether the scores meaningfully distinguish relevant benchmark categories or candidate comparisons.

The selected evaluation must account for score direction and meaning. A larger value may represent a better match, a larger residual, or a different quantity depending on the method.

Raw scores from different comparison methods must not be pooled or compared as though they shared a common scale.

### 7.4 Calibration

Calibration evaluation is relevant only if the method produces probabilities or another output intended to represent a calibrated level of confidence.

A similarity score or arbitrary ranking value must not be called a probability.

If calibration is investigated, the procedure must evaluate whether reported probabilities agree with observed outcomes on suitable data, account for the limited size and representativeness of the benchmark, and disclose uncertainty. Calibration must not be claimed from a handful of cases without adequate supporting evidence.

### 7.5 Robustness and sensitivity

Where the benchmark supports it, evaluate how results change with:

- Measurement noise and reported uncertainty.
- Wavelength coverage and missing spectral regions.
- Spectral resolution and sampling.
- Reference dataset selection.
- Documented normalization or other preparation choices.
- Data-quality flags and masking.
- Observation selection or variation between observations of the same planet.
- Reasonable changes to method settings.

Robustness tests must distinguish scientifically justified variations from arbitrary manipulations. Any transformed or synthetic diagnostic input must be labeled as such.

### 7.6 Metric uncertainty

Metric values should not be presented without considering the amount and independence of supporting evidence.

Where appropriate and feasible, report confidence intervals or other defensible uncertainty summaries. The choice of procedure depends on the metric, sample size, and benchmark structure.

If the benchmark is too small to support a reliable uncertainty estimate, state that limitation explicitly. A numerical metric alone does not establish precise or generalizable performance.

---

## 8. Threshold Derivation and Decision Rules

Thresholds are method- and task-specific. ECAS must not define one universal score cutoff for all molecules, observations, or comparison methods.

### 8.1 Required considerations

A proposed threshold or decision rule must account for:

1. The meaning and direction of the method output.
2. Performance on development and tuning cases.
3. Evidence from suitable negative and control cases.
4. Uncertainty in the estimated performance.
5. The consequences of false-positive and false-negative interpretations.
6. The intended use and limitations of ECAS.
7. The quality, diversity, and representativeness of the benchmark.
8. Any relevant assumptions about reference data or preparation.

### 8.2 Decision outcomes

The initial result presentation should allow the method to report a score or ranking without forcing every candidate into a positive/negative category.

Where supported by the selected method and validation evidence, an evaluation may establish decision regions such as:

- A region meeting a documented criterion for further investigation.
- A region that does not meet that criterion.
- An indeterminate region where the evidence is insufficient.

These are conceptual possibilities, not preselected categories or thresholds. Their definitions must be justified by the method and benchmark evidence.

### 8.3 Limits of interpretation

Even a well-performing comparison method may only support a statement that a candidate's reference is comparatively consistent with the observed spectral data under specified assumptions.

It does not automatically establish that the molecule is present in the atmosphere, that alternative explanations have been excluded, or that a particular abundance has been measured.

Any stronger claim requires additional scientific evidence and a validation procedure appropriate to that claim.

---

## 9. Reference Data and Comparability Effects

Validation must evaluate the method together with the input conditions it requires. A method cannot be judged independently of its observations, reference data, and preparation pipeline.

### 9.1 Reference representation

ECAS must retain distinctions among:

- Measured or experimentally derived spectra.
- Theoretical spectroscopic line lists.
- Spectra synthesized from line lists or other model inputs.

These representations have different assumptions and limitations. Results obtained with one reference type must not automatically be generalized to another.

### 9.2 Physical and instrumental differences

For each benchmark, document relevant differences between the observation and the molecular reference, including coverage, units, resolution, sampling, physical conditions, and processing state where known.

If the comparison requires transformations, their assumptions and effects must be documented. Validation should investigate whether the selected preparation procedure introduces limitations or changes the interpretation of the result.

### 9.3 Incompatible or incomplete inputs

An observation-reference pair that fails the selected method's comparability requirements must not be scored as though it were a valid comparison.

If a benchmark cannot be evaluated because required information or transformations are unavailable, record the reason. Do not silently substitute a different observation, reference, or processing method.

---

## 10. Validation Procedure

The following sequence defines the intended validation workflow.

1. **Define the evaluation question.** Specify the behavior being tested and the scientific claim the evaluation is intended to support.
2. **Select candidate benchmark cases.** Identify published detections, non-detections, controls, or diagnostic cases relevant to that question.
3. **Review the evidence.** Verify the source records, scientific conclusions, data accessibility, metadata, and limitations.
4. **Assign benchmark roles.** Mark cases as development, tuning, evaluation, or diagnostic and document dependencies between cases.
5. **Acquire and register the inputs.** Preserve source identity, provenance, versions, and associated publications.
6. **Validate the data.** Check structural integrity and metadata before scientific use.
7. **Assess comparability.** Determine whether each observation-reference pair satisfies the selected method's requirements.
8. **Prepare inputs.** Apply only justified, documented transformations and preserve their history.
9. **Freeze the evaluation configuration.** Record the method, version, settings, preparation choices, benchmark subset, and metrics before evaluating reserved cases.
10. **Execute the method.** Preserve outputs, failures, diagnostics, and warnings.
11. **Calculate appropriate metrics.** Use only cases eligible for each metric and record exclusions and their reasons.
12. **Assess uncertainty and limitations.** Determine whether the benchmark supports the intended interpretation and how broadly the results can be generalized.
13. **Document conclusions.** Report observed performance, uncertainty, failure modes, limitations, and unsupported claims.
14. **Persist the validation record.** Save the exact inputs, method configuration, evaluation procedure, results, and relevant citations.

If a stage cannot be completed, ECAS must record the failure or limitation rather than present the evaluation as complete.

---

## 11. Failure Analysis

Validation must examine not only aggregate metrics but also cases where the method behaves unexpectedly.

Examples include:

- A supported candidate ranks poorly.
- A reported non-detection receives a strong candidate score.
- A plausible competing reference ranks above the intended candidate.
- A result changes substantially with small, justified preparation changes.
- Missing uncertainty or metadata prevents interpretation.
- Different observations of the same target produce materially different outcomes.
- The method fails on particular coverage or resolution conditions.
- A result depends on one reference dataset or a narrow spectral region.

Each significant failure should be recorded with the benchmark identity, method configuration, relevant diagnostics, plausible explanations, and whether the case changes the interpretation of the overall evaluation.

Failure analysis may motivate method changes. Once those changes are made, their evaluation must be distinguished from the original evaluation, especially when the same case influenced the change.

---

## 12. Validation Reporting

Each completed evaluation should produce a report that can be understood without reconstructing the process from informal notes.

### 12.1 Required report contents

The report should contain:

- Evaluation identifier and date.
- Purpose and scope.
- Comparison method, version, and configuration.
- Benchmark cases and their assigned roles.
- Sources, publications, and data versions.
- Reference datasets and representation types.
- Preparation operations and relevant assumptions.
- Inclusion and exclusion criteria.
- Metrics and their definitions.
- Results and uncertainty summaries where justified.
- Failures, ambiguous cases, and sensitivity findings.
- Limitations of the benchmark and evaluation procedure.
- Conclusions supported by the evidence.
- Conclusions that are not supported.
- Recommendations for additional investigation.

### 12.2 Reporting language

Reports must distinguish observed results from interpretations and recommendations.

Avoid statements such as "the method detects this molecule reliably" unless the benchmark design and evidence justify that specific claim.

Prefer scoped statements that identify the evaluated data, task, and limitations. For example, a result may support the conclusion that a method ranked a benchmark-supported candidate above selected alternatives in a defined evaluation set. That does not establish universal detection capability.

### 12.3 Versioning

Each validation report must identify the exact method and benchmark configuration it evaluates.

A revised benchmark, changed reference, modified preprocessing procedure, or updated comparison method may affect the conclusions. New evaluations must not silently replace historical reports.

---

## 13. Software Testing Versus Scientific Validation

ECAS must maintain a clear distinction between software correctness and scientific performance.

| Test category | Primary question | Example |
|---|---|---|
| Unit testing | Does an individual operation behave as specified? | A transformation converts units correctly. |
| Integration testing | Do application components exchange data correctly? | An imported spectrum passes through validation and registration. |
| Regression testing | Did a code change alter previously characterized behavior? | A known input produces an unexpected numerical change. |
| Scientific benchmark evaluation | Does the method behave usefully on documented scientific cases? | Candidate rankings are assessed against curated observations and controls. |
| Robustness evaluation | How sensitive is the result to relevant data conditions? | Results are compared across suitable coverage or resolution conditions. |

Passing software tests does not establish scientific validity. Passing a limited benchmark does not establish that every code path is correct.

Synthetic fixtures may support unit and integration tests. Their role and limitations must remain explicit.

---

## 14. Initial Work Plan

The next scientific work should proceed in this order:

### Phase A — Benchmark research

- Identify accessible publications and data products describing relevant exoplanet transmission-spectrum detections and non-detections.
- Identify potentially useful control cases.
- Record source accessibility, scientific conclusions, data availability, and major limitations.
- Produce a shortlist of cases rather than committing immediately to a large benchmark collection.

### Phase B — Data feasibility assessment

- Determine whether the shortlisted observations can be acquired or imported.
- Identify the available spectral quantities, units, coverage, resolution, uncertainty information, and processing state.
- Identify suitable molecular reference representations.
- Record gaps that would prevent meaningful comparison.

### Phase C — Method selection

- Compare candidate comparison approaches against the actual benchmark characteristics and intended task.
- Identify each method's input requirements, outputs, assumptions, computational dependencies, and limitations.
- Select the first method only after this assessment.

### Phase D — Evaluation design

- Select metrics that correspond to the chosen method and intended task.
- Define development, tuning, and evaluation roles for the available cases.
- Establish a defensible procedure for uncertainty estimation and threshold selection, if thresholds are justified.
- Record criteria before using reserved evaluation cases.

### Phase E — Validation and revision

- Run the defined evaluation.
- Analyze errors, ambiguity, and sensitivity.
- Document what the evidence supports and what remains unresolved.
- Revise the method or scope if the results do not support the intended use.

These phases define the planned research sequence. They do not authorize implementation or establish that any phase has already been completed.

---

## 15. Open Decisions

The following decisions remain unresolved:

1. Which published detections, non-detections, and controls should form the initial benchmark shortlist?
2. Which observations and associated data products are accessible and suitable?
3. Which molecular reference sources and representation types are suitable for the initial cases?
4. What is the first comparison method, based on the benchmark evidence?
5. Which metrics are appropriate for that method's actual outputs?
6. How should benchmark cases be grouped to reduce dependence between development and evaluation?
7. Does the available evidence support any decision threshold?
8. What uncertainty estimation procedures are justified by the benchmark size and structure?
9. How should ambiguous or conflicting publications be represented in each evaluation?
10. What robustness tests are feasible and scientifically meaningful for the initial release?
11. What minimum evidence is required before ECAS can use stronger detection-related language?
12. How should validation reports and benchmark versions be stored in the finalized data model?

These decisions should be resolved through the benchmark research and method-selection process rather than through arbitrary defaults.

---

## 16. Acceptance Criteria

The validation strategy is ready to guide implementation planning when:

- [ ] Benchmark inclusion criteria are defined.
- [ ] Published detections, non-detections, controls, and ambiguous cases are distinguished appropriately.
- [ ] Every benchmark case retains traceable evidence and provenance.
- [ ] Development, tuning, and evaluation roles are recorded.
- [ ] Metrics are tied to an explicitly defined evaluation question.
- [ ] Thresholds are not assumed before supporting evidence is available.
- [ ] Uncertainty and benchmark limitations are addressed in reporting.
- [ ] Failures and excluded cases remain documented.
- [ ] Method-specific score meanings are preserved.
- [ ] Scientific validation is distinct from software testing.
- [ ] The report format captures inputs, method settings, outcomes, limitations, and citations.
- [ ] The strategy remains compatible with the architecture and data-model documents.

Completion of this document does not mean that ECAS has been scientifically validated. Validation is an empirical process that can only be completed after appropriate data, methods, and evaluation procedures have been selected and examined.

---

## 17. Relationship to Other Documents

This document defines how ECAS evaluates the scientific performance and limitations of its comparison methods.

It should be used alongside:

- `ECAS.md` — project purpose and governing scientific principles.
- `ARCHITECTURE.md` — system structure and scientific component boundaries.
- `DATA_FLOW.md` — acquisition, validation, preparation, comparison, and persistence workflows.
- `MODULE_RESPONSIBILITIES.md` — module ownership and scientific validation interfaces.
- `DATA_MODELS.md` — benchmark, analysis, result, provenance, and validation record concepts.
- `DECISIONS.md` — approved decisions and their rationale.
- `PROJECT_STATE.md` — verified project status and outstanding work.

## 18. Related Documents
ECAS.md — defines the scientific goals and initial scope.

ARCHITECTURE.md — defines the comparison and validation components.

DATA_FLOW.md — describes how observations and references reach comparison.

DATA_MODELS.md — defines how analyses, benchmark cases, and validation results are represented.

MODULE_RESPONSIBILITIES.md — defines ownership of comparison, scoring, and validation responsibilities.

IMPLEMENTATION_PLAN.md — schedules benchmark research and method selection before the first comparison method is finalized.

If a conflict arises between documents, identify and review it rather than resolving it through an unrecorded assumption.

---

**Draft conclusion:** ECAS should evaluate comparison methods using curated, traceable scientific benchmark cases and metrics matched to the task being evaluated. Published detections, non-detections, and controls provide complementary evidence, but none should be reduced to simplistic ground-truth labels without examining its scientific context. Performance claims and decision thresholds must be supported by the benchmark evidence, with uncertainty and limitations made explicit. This document defines the intended strategy; it does not establish empirical performance or authorize implementation.
