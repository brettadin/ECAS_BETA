## 4. Scientific tabular ingestion: an important Beta capability

The newer `ecas/ingestion/tabular_formats.py` module expands import support beyond the generic CSV path discussed in Pass B.

It implements dispatch for:

- `.ecsv` — Astropy Enhanced Character-Separated Values.
- `.dat`, `.tsv`, `.txt`, `.asc` — scientific delimited text.
- `.fits`, `.fit`, `.fts` — supported FITS binary-table spectra.

The importer classifies coordinate and signal columns and attempts to preserve scientific semantics, including axis units, signal units, and whether the input represents transmission depth or a laboratory measurement such as absorbance or transmittance.

This directly matters for your existing research files: FTIR and UV-Vis data are not automatically excluded from ECAS just because they are not CSV. The new importer can handle certain tabular text formats, but compatibility depends on each file's structure, headers, units, and signal semantics. It does not establish universal support for every instrument export or laboratory format.

The implementation also has format-specific limitations: the FITS path supports a restricted binary-table structure rather than every possible FITS spectral representation.

Finding D1 — The import boundary is broader than the generic CSV importer suggests. Documentation and UI descriptions should distinguish the basic CSV importer from the newer scientific-tabular dispatcher. We should not claim a format is fully supported without matching its structure to the importer.

## 5. NASA source data and cache integrity

The NASA path is more than a download folder. The source separates network access, archive discovery, strict transmission-table parsing, and cache registration.

The inspected code shows these protections:

- Downloads and cached source tables have a 1 MiB limit.
- The parser requires a supported NASA transmission-table structure and explicit transmission metadata.
- Required columns and table-header alignment are checked.
- Numeric fields are checked for finite values.
- The cache stores the original table bytes and a SHA-256 digest.
- A separate record stores source URL, retrieval timestamp, and metadata evidence.
- Cache reopening verifies the source hash, metadata hash, source identity, product type, and expected row count.

The NASA cache writes the manifest last, treating it as a completion marker. Failed validation can leave an unregistered partial directory, but the cache reader does not treat that directory as a valid record merely because files exist.

Finding D2 — NASA caching has meaningful integrity and identity checks. This is stronger than a simple file-exists cache. It still does not independently authenticate NASA as the origin of every byte or validate the scientific calibration of a dataset. A hash proves consistency with the recorded digest, not scientific correctness.

The strict table parser is also deliberately not a general IPAC table reader. Unsupported layouts should fail explicitly rather than being silently reinterpreted.

## 6. ExoMol products, raw bytes, and provenance

The ExoMol workflow has a separate validation and caching path, with a more explicit product contract than the NASA cache.

`ecas/ingestion/exomol_cross_section.py` validates the supported two-column `.sigma` representation. It checks the source byte limit, provenance fields, required licensing metadata, positive temperature, zero pressure, Doppler-only conditions, URL origin, finite numerical values, non-negative cross sections, and strictly increasing wavenumbers.

The reference cache then retains:

- The raw source bytes, encoded in the cache envelope.
- The requested molecule/isotopologue and calculation settings.
- Parsed provenance and citations.
- Retrieval timestamp and source SHA-256.
- Optional catalogue context.
- An integrity digest over the serialized envelope.

On reload, the code recomputes the envelope digest, decodes the raw bytes, reruns product validation, and checks that the stored provenance and source digest match the validated product. Writes use a temporary file and atomic replacement.

This supports a useful separation between the original product, its validated parsed representation, and the conditions under which it was requested.

### Limitation: provenance is not authentication

The ExoMol parser explicitly notes that supplied metadata cannot prove the source URL actually supplied the bytes or independently authenticate the declared temperature and molecular identity.

The SHA-256 and integrity digest detect inconsistency or alteration relative to the recorded data. They are not digital signatures from the provider. Likewise, a stored retrieval timestamp is evidence recorded by ECAS, not independently verified proof of when the provider published the product.

Finding D3 — ExoMol reference caching preserves substantially more than a parsed spectrum. Raw bytes and settings are retained, and cache reload revalidates them. The remaining provenance boundary is explicit: internal consistency is stronger than unaudited metadata, but it is not external authentication.

## 7. Project persistence and attachment provenance

The lower-level persistence layer in `ecas/persistence.py` uses SQLite, storing `SpectrumData` records as JSON. Project-level operations in `ecas/projects.py` add attachment and provenance handling.

The project attachment path can retain:

- The spectrum payload.
- Original source bytes, subject to a 16 MiB source limit.
- A source SHA-256.
- The original source path and import-schema information.
- NASA table metadata and column units, where applicable.
- NASA cache-record evidence, including the associated metadata bytes.
- An integrity digest covering the saved spectrum and attachment envelope.

On reload, the project code verifies the attachment digest and, where source bytes are retained, checks the source hash. This helps detect changes to a saved spectrum or its recorded provenance.

### Important boundaries

1. A source path is not the same as a preserved source file. The path records where a source was found; retained bytes are what allow the original file content to be checked later.
2. Not every source has the same provenance envelope. Local CSV, NASA products, and ExoMol references carry different kinds of metadata. A single generic “provenance complete” claim would be too broad.
3. A valid hash is not a scientific validation result. It says that content matches the recorded digest.
4. A comparison record is not an unconditional reproducibility guarantee. The comparison persistence module records settings, transformations, eligibility verdicts, diagnostics, provenance, and limitations. Its reproducibility check compares recomputed results with saved results; it cannot guarantee that all external dependencies or scientific assumptions remain available and valid.

Finding D4 — Project persistence has a meaningful integrity layer, but provenance completeness depends on the import path. The code makes source preservation and verification explicit. Whether a particular saved project is sufficient to reproduce an analysis still depends on the contents of its attachments and comparison records.

## 8. Bundled data and cache lifecycle

The archive contains dated NASA and ExoMol datasets, provenance JSON files, catalogue/cache records, and sample products. This means the repository contains both application code and a snapshot of scientific resources.

That arrangement has practical benefits: some reference data can be inspected without a new network request, and bundled samples can support testing and development.

It also introduces lifecycle questions:

- Are bundled resources clearly distinguished from records retrieved by a user's own session?
- Are stale or invalid cache entries reported clearly rather than mistaken for usable references?
- Can a user identify which exact source bytes and settings were used for an earlier comparison?
- Are sample data and cache snapshots excluded from any claim that live network retrieval currently works?

The inspected NASA cache explicitly counts invalid entries separately from valid ones. The ExoMol cache validates individual records before reuse. These are useful mechanisms, although this pass does not establish that every UI path communicates all cache failures and provenance limitations clearly.

Finding D5 — Bundled datasets and caches need clear identity and lifecycle handling. This is a review concern rather than a confirmed defect. Pass E will assess how much of this information is visible to users; Pass F will examine corresponding test coverage.

## 9. Architecture documents versus current ingestion

The architecture documents correctly state that structural validity, scientific validity, and comparability are separate stages. They also distinguish implemented behavior from proposed workflows.

The current source now contains more than the initial CSV/SQLite baseline described in parts of those documents. In particular, scientific ASCII/ECSV/FITS import, source-specific NASA caching, ExoMol raw-product caching, project attachment integrity, and comparison-record persistence have evolved beyond the original baseline.

This does not mean the documents are useless or wholly incorrect. It means their status labels and descriptions must be checked against the current source rather than treated as a complete description of the latest implementation.

Finding D6 — The documented data-flow baseline needs reconciliation with current capabilities. The main concern is consistency between documentation, current code, and the records of later development—not evidence that the newer implementations are absent.

## 10. Pass D findings summary

| ID | Finding                                                                                                          | Classification                                           |
| -- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| D1 | Import support includes scientific ASCII, ECSV, and a restricted FITS binary-table path in addition to CSV.      | Confirmed capability; format limitations apply           |
| D2 | NASA caches validate source bytes, metadata evidence, table identity, product type, and row count.               | Confirmed integrity controls                             |
| D3 | ExoMol cache records preserve raw bytes, settings, provenance, and integrity digests, then revalidate on reload. | Confirmed integrity controls; no external authentication |
| D4 | Project persistence preserves spectrum payloads and attachment/source evidence, with hash verification.          | Confirmed capability; provenance varies by source        |
| D5 | Bundled data and cache lifecycle require clear user-facing identity and failure reporting.                       | Review concern; no defect confirmed                      |
| D6 | Architecture documents need reconciliation with the expanded current ingestion and persistence implementation.   | Documentation discrepancy                                |

No tests were run during this pass, and no files were changed.

## 11. Overall assessment

Beta's data layer is considerably more developed than a simple importer and local database. It has explicit format boundaries, source-specific parsing, cache integrity checks, raw-byte retention for supported reference products, project attachment verification, and persistent comparison records.

The remaining boundary is important: integrity, provenance, and reproducibility are related but distinct properties. A file can be intact but scientifically inappropriate; its source metadata can be internally consistent without being independently authenticated; and a saved comparison can be auditable without guaranteeing that every external dependency or physical assumption can be reconstructed.

The most useful next review is the user-facing side of those protections: whether the interface makes source identity, data limitations, errors, and scientific interpretation clear enough for a researcher to use the application safely.

I will wait for your discussion or approval before proceeding to Pass E — UI and usability.