# Batch 3 links/layout review disposition — 2026-10-28

Argon reviewed source_links.py, main_window.py excerpts, nasa_browser.py layout
and source-link tests. No functional defect was established. This review confirms
that absolute HTTP(S) URLs pass source_link, resolving Batch 2's missing-context
claim that double validation prevents opening links.

The P3 suggestion to remove click-time URL validation is optional cleanup, not a
correctness fix. Retain the inexpensive check immediately before the external
browser action: it applies the allowed-scheme/credential policy to the current
cell value. No measured performance issue justifies removing it. No code changes
or new review batch are needed for Batch 3.

Clarifications: control characters are rejected, not stripped. urlsplit and the
allowlist checks are limited URL validation, not a guarantee that every malformed
URL is rejected. Do not rely on the operating system as a universal rejection
mechanism. A false return from QDesktopServices.openUrl is already reported.

Latest executed verification remains project-ui-review-focused (107 passed) and
project-ui-review-full (355 passed, one Windows directory-symlink privilege skip),
including actual table double-click opening, absolute citation preservation and
browser-launch failure tests. No tests rerun for this documentation-only triage.
No model calls, downloads, credentials, commits or pushes. Batch 4, independent
follow-up on Batch 1/2 corrections and human desktop acceptance remain pending.
