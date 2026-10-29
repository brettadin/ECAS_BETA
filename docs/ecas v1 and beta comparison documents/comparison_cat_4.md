# ECAS v1 and Beta Comparison — Category 4
## Data Ingestion, Persistence, Integrity, and Provenance

**Scope:** Compare how ECAS v1 and ECAS Beta ingest scientific data, preserve project state, manage source data and caches, verify integrity, and record provenance relevant to reproducibility.

**Evidence basis:** The supplied v1 and Beta source archives and the findings from the respective seven-pass reviews. No new application execution, persistence tests, or external-source verification was performed for this category.

---

## 1. Executive Assessment

ECAS v1 already provides project persistence, scientific-file ingestion, archive retrieval, and provenance information for supported workflows. Its native `.ecas` project format uses a ZIP archive containing `state.json` and `arrays.npz`. The application also documents preservation of downloaded spectral time-series data and archive provenance for relevant transit workflows.

Beta expands the data-management architecture substantially. It introduces SQLite-backed project management, structured project attachments, source metadata and hashes, integrity digests, and dedicated cache workflows for NASA archive products and ExoMol molecular-reference data. Its scientific tabular importer also supports ECSV, selected FITS binary tables, and several scientific delimited-text formats.

The key advancement is that Beta treats data identity, source metadata, and integrity checking more explicitly across its scientific workflows.

However, **data integrity is not the same as provenance completeness, and neither is equivalent to scientific validity.** A matching hash can establish that bytes have not changed relative to a recorded digest, but it does not authenticate the provider, establish calibration quality, or prove that a downstream analysis can be reproduced.

Beta provides a stronger foundation for managing scientific inputs, but its guarantees differ by data source and workflow. The evidence does not establish that every derived result, model configuration, or analysis decision can be reconstructed end to end.

## 2. Side-by-Side Data Management Matrix

| Area | ECAS v1 | ECAS Beta | Comparative assessment |
|---|---|---|---|
| Native project format | `.ecas` ZIP archive containing `state.json` and `arrays.npz`. | SQLite-backed project management with structured project data and attachments. | Beta adopts a more structured project-storage architecture; the two formats provide different persistence models. |
| Project lifecycle | Save and reopen project state through the native project format. | Create, select, attach, save, and reopen projects through dedicated project-management workflows. | Beta has a more explicit project lifecycle and attachment-management structure. |
| Spectral-file ingestion | Supports documented spectroscopy formats including CSV, TSV, delimited text, FITS tables, and JCAMP-DX. | Supports generic CSV, a schema-specific WASP-39b archive route, ECSV, scientific delimited text, and a restricted FITS binary-table path. | Both support multiple formats. Beta adds explicit scientific-tabular routes but does not guarantee universal format or schema compatibility. |
| Source identity | Archive provenance is documented for relevant workflows; provenance completeness varies by data path. | Comparison inputs and persisted records can include source identity, hashes, roles, units, and metadata. | Beta represents source identity more explicitly within comparison and persistence workflows. |
| Original-source preservation | V1 documents preservation of downloaded spectral time-series data for relevant transit workflows. A universal original-file preservation guarantee was not established. | Project persistence supports optional original source bytes, subject to a 16 MiB limit, alongside source metadata and hashes. | Beta provides an explicit bounded source-byte preservation mechanism; preservation is not universal for all inputs. |
| NASA archive cache | Caching and archive provenance are documented for supported workflows. | Stores raw source tables, SHA-256 hashes, metadata, product type, and row count; reload validates defined consistency conditions. | Beta's cache validation is more explicit in the reviewed implementation. |
| Molecular-reference cache | Uses configured gas data and reference workflows, including NIST JCAMP browsing. | ExoMol cache preserves raw bytes, retrieval settings, provenance, citations, retrieval timestamp, and source SHA; reload checks defined integrity properties. | Beta adds a more structured molecular-reference retrieval and cache workflow for supported products. |
| Integrity verification | The reviewed v1 evidence does not establish a uniform integrity-verification scheme across all project and cache data. | Project persistence uses integrity digests; source-specific caches validate hashes and metadata according to their implemented rules. | Beta provides more explicit integrity safeguards, but their scope is limited to the properties each mechanism actually checks. |
| Data provenance | Source and archive metadata exist, but the v1 review identifies limits to full provenance and reproducibility. | Provenance is represented more explicitly for project records, NASA data, and supported ExoMol products. | Beta improves provenance coverage and structure, but provenance completeness still differs between source types. |
| Cache lifecycle | Cache behavior exists for supported workflows, but a uniform lifecycle and validation policy was not established in the review. | Dedicated cache workflows and validation rules exist; bundled data and caches still require clear identity and lifecycle communication. | Beta has clearer source-specific cache behavior, while broader lifecycle consistency remains an area for documentation and verification. |
| Offline reuse | Native project persistence supports reopening saved work; full offline reproducibility depends on what was saved and what external resources are needed. | Cached NASA and ExoMol data and persisted project content support reuse, subject to cache availability and the stored data. | Beta provides more explicit cached-source reuse. Neither version is established as fully offline-reproducible across every workflow. |
| Scientific traceability | Provenance exists in supported workflows but does not establish complete reconstruction of every derived result. | More structured metadata, hashes, citations, and source records are available, but not every provenance guarantee is uniform. | Beta is better structured for traceability; end-to-end reconstruction remains unproven. |

## 3. Detailed Comparison

### 3.1 Scientific-data ingestion

**V1 baseline**

V1 supports multiple spectroscopy input formats and interprets their scientific axes and signals within its import workflows. The reviewed implementation includes CSV, TSV, delimited text, FITS tables, and JCAMP-DX. Its import interface provides column and unit interpretation for supported data.

As with any scientific importer, successful parsing depends on the structure of the input. A file extension alone does not guarantee that ECAS can correctly identify its wavelength or wavenumber axis, signal representation, units, and observable type.

**Beta state**

Beta has several distinct ingestion paths:

- Generic CSV ingestion with recognizable wavelength and signal columns.
- A schema-specific WASP-39b archive importer.
- ECSV support.
- Scientific delimited-text support for formats such as `.dat`, `.tsv`, `.txt`, and `.asc`.
- A restricted FITS binary-table path.

The scientific tabular importer preserves relevant semantics and units and distinguishes laboratory from astronomical data in supported workflows.

Generic CSV import does not provide arbitrary user-selected X/Y column mapping. The schema-specific archive path depends on the expected table structure, and FITS support is restricted rather than universal.

**Assessment**

Beta expands and organizes scientific-tabular ingestion, especially for workflows with known schemas and explicit metadata. Its strongest advancement is not that it can ingest every laboratory or astronomical file, but that it has more explicit routes for particular data types and carries more scientific context into later stages.

The reviewed evidence does not establish universal direct import of FTIR or UV-Vis files. Compatibility must be assessed against the actual format, table layout, axis representation, signal units, and metadata available in each file.

### 3.2 Project persistence and lifecycle

**V1 baseline**

V1 saves project state in a native `.ecas` archive containing `state.json` and `arrays.npz`. This provides a defined mechanism for preserving application state and associated numerical arrays.

The v1 review nevertheless identified limitations in full provenance and reproducibility. The presence of a native project file does not guarantee that every external input, configuration, intermediate calculation, or derived result is included.

**Beta state**

Beta uses SQLite-backed project management. Its reviewed functionality supports project creation and selection, attachment management, saving, and reopening. Persistence includes structured spectrum data, project attachment payloads, optional original source bytes, source metadata, hashes, import-schema information, and an integrity digest.

Optional original-source preservation is bounded by a 16 MiB limit. Consequently, the reviewed implementation should not be described as preserving every original file without restriction.

**Assessment**

Beta has a more explicit persistence model for managing research inputs and their relationship to projects. Structured records and attachment handling are useful when projects contain observations, reference products, and derived analysis inputs from multiple sources.

The change in storage architecture is not, by itself, proof that all v1 project information can be migrated or that every Beta project contains all the information needed for exact reconstruction. Those are separate compatibility and reproducibility questions.

### 3.3 NASA archive data and cache integrity

**V1 baseline**

V1 supports MAST retrieval for its documented TESS and JWST workflows, with caching and archive provenance. The reviewed evidence does not establish a uniform hash-and-metadata validation scheme across every v1 cache or downloaded product.

**Beta state**

Beta's NASA cache stores:

- The raw source table.
- A SHA-256 hash.
- Source metadata and provenance.
- Product type.
- Row count.

On reload, the implementation checks the hash and defined metadata, source identity, product type, and row-count conditions.

These checks provide evidence that the cached content is internally consistent with its recorded metadata and expected identity.

**Assessment**

Beta improves the explicitness of NASA-cache integrity checks. This helps detect certain forms of corruption, accidental modification, or mismatch between a cached payload and its recorded metadata.

The limits matter. A SHA-256 hash verifies equality against a reference digest; it does not establish who supplied the data. If the original content and its recorded digest were both incorrect, matching them would not make the source scientifically trustworthy. Nor does metadata consistency establish that an observation was calibrated correctly.

The defensible claim is that Beta adds defined cache-integrity safeguards—not that its NASA cache independently authenticates scientific data.

### 3.4 ExoMol reference-data preservation

**V1 baseline**

V1 provides configured gas-reference workflows and NIST JCAMP reference browsing. Its reviewed data-management structure does not establish an equivalent ExoMol catalogue-to-product cache workflow with the same explicit metadata and integrity checks as Beta.

**Beta state**

Beta separates molecular-reference catalogue discovery from supported product retrieval. For implemented ExoMol products, its cache preserves raw bytes, retrieval settings, provenance, citations, retrieval timestamps, and source SHA values. Reloading performs checks against the stored metadata and content.

The reviewed product support is bounded to documented mappings, including CO₂/UCL-4000, H₂O/POKAZATEL, and CH₄/MM. Catalogue discovery is broader than the set of products that can be retrieved through the implemented workflows.

**Assessment**

This is one of Beta's clearer data-management advances. It provides a more structured path from reference discovery to selected product retrieval, persistence, and subsequent reuse.

The saved retrieval settings and citations are useful for traceability. However, recorded settings do not independently prove that the provider used those settings exactly as declared, and an internally consistent cache does not establish that a molecular reference is appropriate for the observation or atmospheric conditions under study.

### 3.5 Provenance and source identity

Provenance answers questions such as:

- Where did this observation or reference come from?
- Which product and source record were retrieved?
- What bytes and metadata were retained?
- Which units, schema, or import route were applied?
- Which model or processing settings produced a derived result?
- Can another researcher reconstruct the steps taken?

V1 provides provenance for relevant archive workflows and persists project state, but its review identifies limitations in the completeness of provenance across the application.

Beta represents provenance more explicitly through source identities, hashes, metadata, import-schema information, cache records, and citations for supported reference products. Its comparison inputs also carry source-related fields that help define the origin and role of data used in a calculation.

The remaining question is coverage. A source hash and import schema are valuable, but they do not automatically record every transformation, manual decision, model version, parameter choice, uncertainty assumption, and output associated with a scientific conclusion.

**Assessment:** Beta improves the structure and breadth of provenance information. The reviews do not establish a universal, end-to-end provenance record for every analysis workflow.

### 3.6 Integrity versus authenticity versus reproducibility

These concepts must remain distinct in the final evaluation.

| Property | What it establishes | What it does not establish |
|---|---|---|
| Integrity | A payload matches a recorded digest or defined consistency checks. | That the original data were correct or came from an authentic provider. |
| Source identity | The application records which source or product a dataset is associated with. | That the source metadata are independently authenticated. |
| Provenance | Recorded information about origin, retrieval, processing, or configuration. | That all necessary steps and parameters have been recorded. |
| Reproducibility | A documented workflow can be repeated with suitable inputs and conditions. | That a reproducible result is scientifically correct. |
| Scientific validity | Evidence supports the physical and statistical interpretation of the result. | It cannot be established by file integrity checks alone. |

Beta makes progress primarily in the first three areas. The degree of reproducibility depends on the completeness of saved inputs and workflow settings, and scientific validity requires separate evidence.

### 3.7 Cache lifecycle and offline use

Beta's source-specific caches make reuse more explicit. Cached NASA tables and supported ExoMol products can be checked against stored integrity information and reopened according to their implemented workflows.

There are still important boundaries:

- A cache can only support offline reuse if the required data are present.
- A cache can be internally consistent without being scientifically current or suitable.
- Bundled data, downloaded caches, project attachments, and generated outputs have different origins and lifecycle requirements.
- The reviewed evidence does not establish that every workflow is fully reproducible offline.
- A cache's stored metadata should not be assumed to cover every downstream transformation or analysis setting.

The v1 project archive likewise supports saved-state reuse, but the complete availability of external inputs and provenance needed for every workflow was not established.

**Assessment:** Beta improves controlled reuse of selected data sources. A comprehensive offline-reproducibility guarantee has not been established for either version.

## 4. Important Limitations and Non-Equivalences

The following distinctions should be retained in the overall assessment:

1. **File support is not universal compatibility.** Both versions support defined formats and workflows, with restrictions on schema, metadata, and scientific interpretation.

2. **A parsed table is not necessarily a scientifically interpretable dataset.** Units, axis direction, observable type, calibration, and response information may still be incomplete or ambiguous.

3. **A stored project is not necessarily a complete research record.** Exact reconstruction may require original inputs, transformation settings, model versions, intermediate data, and analysis parameters.

4. **A hash is not source authentication.** Integrity checks compare content with recorded values; they do not independently establish the provider's identity or the scientific quality of the content.

5. **Provenance completeness varies by source.** The existence of a structured cache or project schema does not mean all data paths preserve the same level of detail.

6. **Catalogue discovery is not complete product retrieval.** Beta's ExoMol discovery capabilities exceed its documented product mappings.

7. **Persistence is not scientific validation.** Correctly saved and reopened data can still be inappropriate for a particular calculation or contain calibration errors.

8. **More structured storage does not prove migration parity.** The reviewed evidence does not establish that every v1 project can be migrated into Beta without loss or that every Beta project captures all v1 workflow state.

## 5. Category 4 Findings

| Classification | Finding |
|---|---|
| Improved | Structured project management, explicit source identity and metadata, integrity digests, and source-specific cache validation. |
| Expanded | Scientific-tabular ingestion routes, bounded preservation of original source bytes, and ExoMol product retrieval with provenance. |
| Retained from v1 | Native project persistence, multiple spectroscopy formats, archive retrieval, and source provenance for supported workflows. |
| Unresolved | Complete provenance coverage, cache lifecycle consistency, offline reproducibility across all workflows, and migration compatibility. |
| Important boundary | Integrity and provenance mechanisms do not authenticate the source or validate the scientific meaning of the data. |
| Confirmed data-management regression | None established by the reviewed evidence. |
| Not established | Universal scientific-file support, complete end-to-end provenance, unrestricted original-file preservation, or universal reproducibility. |

## 6. Category 4 Verdict

**Assessment: Beta provides a more explicit and structured data-management foundation, particularly for source identity, project attachments, cache integrity, and molecular-reference provenance.**

V1 already supports native project persistence, multiple spectroscopy formats, and provenance for supported astronomical archive workflows. Beta's advances lie in making these responsibilities more explicit and extending them into a broader collection of data-management paths.

The most consequential improvement is not simply the change from ZIP-based project storage to SQLite. It is the combination of structured project records, bounded source preservation, source-specific cache validation, and richer metadata across observations and molecular references.

The main remaining gap is completeness. The reviews do not establish that every source, transformation, model configuration, and derived result is recorded well enough for exact end-to-end reconstruction. Integrity checks also cannot substitute for source authentication, calibration assessment, or empirical scientific validation.

The defensible conclusion is that Beta is better structured for traceable scientific-data management, while full reproducibility and scientific validity remain separate requirements.

**Confidence:** Moderate for the documented architectural and data-management differences. Lower for claims about complete provenance coverage, migration parity, and end-to-end offline reproducibility, which were not independently tested in this category.

---

## Review Sources and Audit Trail

Review-document directory:

`docs/ecas v1 and beta comparison documents/`

Relevant records:

- `ecas_v1_pass_0.md` — initial v1 review planning.
- `ecas_v1_pass_A.md` through `ecas_v1_pass_G.md` — v1 review evidence, including ingestion, persistence, and provenance findings.
- `ecas_beta_pass_0.md` — initial Beta review planning.
- `ecas_beta_pass_A.md` through `ecas_beta_pass_G.md` — Beta review evidence, including scientific-tabular ingestion, SQLite project persistence, NASA cache validation, and ExoMol provenance.
- `10_29_26_ecas_beta_review_initial.md` — earlier comprehensive Beta review, retained as a separate historical assessment.
- `comparison_cat_1.md` — architecture and application structure comparison.
- `comparison_cat_2.md` — functional capabilities and workflows comparison.
- `comparison_cat_3.md` — scientific and numerical implementation comparison.
- `comparison_cat_4.md` — this document.

Source-derived observations, documented claims, inferred implications, and unverified guarantees remain distinct. No new tests or source changes were performed for this category.