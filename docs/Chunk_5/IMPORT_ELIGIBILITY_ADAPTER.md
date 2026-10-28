# Import-to-eligibility adapter — 2026-10-28

Research prototype: import_eligibility_adapter.py, outside the application package.
No app wiring, comparison scores, database migration or source-file lookup occurs.
This prepares typed contract inputs while preserving unknown scientific facts.

`adapt` takes SpectrumData and optional matching TransmissionTable details. It
copies canonical wavelength/signal columns in original row order, preserves missing
cells, returns original indices, and records explicit metadata mappings. It does
not sort, mask, interpolate, scale values or infer meaning from a filename.

| Imported fact | Adapter behavior |
| --- | --- |
| Source path | Retained as source identity, not reopened |
| Matching table details | Preserve importer source hash; reject conflicting hash or spectrum |
| No source hash | Leave unknown; never hash parsed values as though they were raw bytes |
| Explicit Transmission signal_type | Record mapping to transit_depth |
| `%` signal unit | Record label mapping to percent; measurements unchanged |
| Other/missing units | Preserve as supplied; eligibility checks support/compatibility |
| Error columns | Preserve signed values for audit; do not infer confidence, Gaussianity or independence |
| Role/frame/response | Leave unknown unless caller supplies declarations; mark their provenance as caller assertions |

Matching import details bind to the supplied imported spectrum snapshot, not the
current contents of a file on disk. Caller-supplied hashes/declarations are not
authenticated by this prototype. Reading a file later requires separate validation.
The adapter does not automatically restore comparison metadata from project source
attachments; that remains a separate integration task. Raw source rows/columns and
unknown observable types remain available in original SpectrumData.

Six new cases exercise captured-product import fidelity, generic CSV unknowns,
declared synthetic metadata, conflicting hash/details and unmodified missing/
unsorted measurements. The NASA fixture is checked only for adapter fidelity and
unchanged bytes; no real-data scientific comparison is performed. Generic CSV
uncertainty does not become an established 1-sigma independent noise model.

Focused: `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py chunk5-adapter-focused`
— 106 passed, one skipped, 1.11 s. Full, stage chunk5-adapter-full: 424 passed, one
skipped, 7.90 s; exit 0. Evidence: verification_adapter_20261028. Existing skip is
Windows directory-symlink privileges. No dependency/download/model call or commit.

Independent review remains open for this adapter, eligibility test coverage and
the preceding robustness/method decision. Previously reviewed eligibility source
and research helpers are unchanged. Manual review is recorded complete; real-data
validation remains deferred. Next: review these bounded increments, then investigate
reference-provider identity, data conditions and format/access constraints before
choosing an initial source for Chunk 5.1. No automatic defaults or legacy rewrite.
