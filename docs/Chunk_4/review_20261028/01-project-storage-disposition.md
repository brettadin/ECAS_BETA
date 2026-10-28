# Batch 1 storage review disposition — 2026-10-28

Argon's supplied review covered persistence.py, projects.py, the spectrum model
and service tests. This records implementation triage; it is not independent
approval of the corrections. Original batch 01 and its manifest remain unchanged.

1. **Concurrent read, accepted and fixed.** The ID/length query and payload reads
   now share an explicit SQLite read transaction. This preserves one snapshot
   during concurrent deletion or replacement and retains the size check before
   transferring payloads into Python. A real second connection in WAL mode deletes
   and commits after the reader fetches IDs; the first read completes consistently,
   and the next read sees the deletion. Previously TypeError would be wrapped in
   PersistenceError, so the project load failed rather than leaking TypeError.
2. **Path portability, accepted with a compatible correction.** v1 hashes contain
   the original path spelling. Verification now uses the exact saved path text,
   before Path conversion can affect its spelling. After verification, an adapted
   in-memory attachment hash supports copying the record to another project on
   this platform. Original database bytes and provenance remain unchanged.
   Blindly switching to as_posix() would invalidate existing hashes. Tests simulate
   both Windows and POSIX path rendering; a second physical OS was not available.
3. **Injected connection commit, no behavior change.** DECISIONS.md's existing
   persistence contract explicitly commits each save regardless of connection
   ownership and excludes caller-managed bulk transactions. Removing commit
   silently would break that contract. Transaction composition remains a future
   API decision; injecting a connection does not imply deferred commits.
4. **Index load, accepted and fixed.** A read-only parameterized query uses
   ORDER BY id, LIMIT 1 and OFFSET to fetch and parse only the requested row.
   Negative/out-of-range/missing-project reads return None without creating files.
   A malformed unrelated record no longer prevents retrieving a valid record.
   OFFSET can still scan preceding entries inside SQLite; this removes eager
   Python loading, not all index-dependent database work.

The review's 64 MiB limitation needs correction: the existing length(CAST(data AS
BLOB)) query checks size before fetching the body into Python. The new transaction
keeps that size check and subsequent fetch in the same snapshot. The per-record
bound does not impose a total project memory limit.

Verification used the existing isolated, offline test driver:

- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py project-review-focused`
  — 39 passed, 1 skipped (0.85 s).
- `.venv/Scripts/python.exe -I -B .venv/checks/run_checks.py project-review-full`
  — 345 passed, 1 skipped (5.74 s).

The skip remains Windows directory-symlink privileges. Logs and exact commands
are in ../verification_20261028/project-review-*. No downloads, model calls,
credentials, commits or pushes. Argon follow-up and normal desktop human review
remain open. Follow-up source snapshot: 01-project-storage-follow-up.txt.

## Independent follow-up received — 2026-10-28

User supplied Argon's re-review of persistence.py, projects.py and
test_project_review_regressions.py: findings were empty. Argon confirmed snapshot
consistency, compatible v1 path integrity, selective index loading and retention
of the documented commit contract. Batch 1 correction review is complete for the
supplied snapshot. This does not constitute human desktop acceptance.

Argon noted that explicit BEGIN must precede any implicit transaction. The current
fresh read-only connection executes BEGIN before its SELECTs, so no preceding
transaction exists in this scope. If connection reuse or preceding writes are
introduced, revisit transaction ownership. No code change or test rerun was needed.
Latest overall executed suite remains 357 passed, one skipped. Batch 2/4 correction
reviews and human desktop acceptance remain pending.
