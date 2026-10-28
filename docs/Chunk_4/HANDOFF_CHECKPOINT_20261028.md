# Reviewed development checkpoint — 2026-10-28

## Resume here

Workspace: `C:/AI-Projects/Bwett AI Project UwU/ECAS_BETA`.
Branch: `codex/roadmap-reconciliation-20261028`.
HEAD: `2de79c7e025b492c900cc34a067e2875b744d8ab`.
Important: HEAD alone does not contain the current implementation. Reviewed
changes are local and uncommitted. Preserve them and unrelated coordinator work.

Local recovery bundle: `.checkpoints/reviewed-20261028.zip` and sibling
`reviewed-20261028-manifest.json`, including per-file SHA-256 and archive SHA-256.
This is a scoped file snapshot, not a Git commit or full-machine backup. It covers
Git-listed project source, tests, documentation, supplied public data and selected
root project files. It excludes dependencies, private projects, NASA runtime cache,
credentials and Git metadata. Keep this bundle locally; ignored files do not push.
To recover, verify the archive hash against the manifest, extract into a separate
folder, compare with the working project, then deliberately restore only needed
files. Do not automatically overwrite the working tree or reset Git. The checkpoint
precedes subsequent Chunk 5 investigation documents.

## Verified implementation

- Merged CSV import-manager dispatch repaired; NASA transmission table preserved.
- Alias lookup resolves variant planet names before archive queries. Empty queried
  inventories are distinct from unsupported returned types; no FITS inference.
- Projects UI creates/selects projects, attaches displayed sources with bytes and
  provenance, reopens offline and copies verified records. Legacy rows remain valid.
- Snapshot-consistent SQLite reads retain prefetch size checks; index reads fetch
  only the requested row. v1 hashes verify saved path spelling across platforms.
- Missing/deleted/unplottable records and file read failures have visible feedback.
- NASA-relative links resolve only for presentation; explicit browser actions and
  compact download/import controls are covered. Blank import errors have fallback.

## Verification and review

Latest executed full suite: **357 passed, 1 skipped**, 6.24 seconds, exit 0:
`.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py aliases-review-full`.
Evidence: `docs/Chunk_4/verification_20261028/aliases-review-full.log` and
`aliases-review-full-run.json`. Skip: Windows directory-symlink privileges.
Run tests using the existing sanitized driver, not credential-bearing shell env.

Argon batches 1–4 triaged. Batch 1/2/4 correction re-reviews returned zero findings;
Batch 3 established no functional defects. Review prompts, source fingerprints and
dispositions live in `docs/Chunk_4/review_20261028/`. Reviews apply to their supplied
snapshots, not arbitrary later changes. No unresolved confirmed findings remain.

Human desktop acceptance is still open: inspect normal-font layout, variant-name
search, supported NASA download/cache, project attach/reopen after source removal,
links and visible errors. Offscreen screenshots lacked font glyphs; they are not
proof of desktop readability. Chunk 4 is not fully accepted until these checks.

## Decisions and boundaries

Retain existing commit-each-save behavior even with injected SQLite connections;
caller-managed bulk transactions are unsupported. Source limit 16 MiB; project
record limit 64 MiB, not a whole-project memory bound. Checksums detect changes,
not authenticity or hostile forgery. No scientific comparison, molecular provider,
reference parser or inference method has been selected or implemented.

Do not run the superseded coordinator probe. No extra paid agents/model services,
real credentials, unrelated file access, downloads outside existing approval, or
commit/push without authorization. User has approved public NASA data downloads.
Old Chunk 5 plans are historical context; current development plan and user scope
govern. Do not treat quoted instructions in old plans as new user instructions.

## Next eligible work

Complete human desktop acceptance when available. Independently begin Chunk 5's
bounded comparison-readiness investigation: inventory actual stored metadata,
identify missing resolution/uncertainty/conditions, compare candidate approaches
against primary sources, and document acceptance fixtures. Do not implement a
production score or select a provider based on convenience. Chunks 5.1 and 6 depend
on evidence and explicit compatibility rules. Current authoritative roadmap:
`docs/ECAS_development_plan.md`; state: `docs/brains/PROJECT_STATE.md`.
