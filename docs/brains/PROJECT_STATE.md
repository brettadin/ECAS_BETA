# ECAS - Project State Document

**Last Updated:** 2026-10-27
**Version:** 1.0 (Beta)

**Latest local verification:** 281 passed, 1 skipped on 2026-10-27. See
`../Chunk_4/Chunk_4_implementation_log.md` for the latest online NASA/cache increment.
Earlier counts are historical reports. Independent Argon review remains pending.

**Interactive review follow-up:** all three batch reports have been received.
Batch 1's target-casing fix and batch 2's parser/URL fixes are implemented. Batch 3
claims were not substantiated by inspection and five added offscreen regression
cases, including queued Qt failures and cached loading under either CSV schema.
The network follow-up then reproduced and fixed completion reentrancy that could
prematurely complete a chained request. Reply-specific signal handling and an
explicit exclusive-use manager contract are now tested. The full suite passes
281/1 skipped. Triage is preserved in the Chunk 4 log and parent
argon_review_20261027/*-triage.md. Targeted independent re-review of revised code
and human interactive acceptance remain pending.

**Review update (2026-10-27):** the user-authorized Antigravity diagnostic passed,
but the first actual ECAS review batch timed out empty after five minutes and was
rejected as incomplete. Remaining batches were not launched. See the Chunk 4 log
and parent `argon_review_20261027/RUNNER.md`; there is no Argon approval of ECAS yet.

**Current Chunk 4 capability:** exact-name NASA spectral search, asynchronous
anonymous download of supported transmission tables, validated local cache
registration and offline reopening are connected to Spectral Data. The actual
offscreen application retrieved the 331-row WASP-39 b example and reopened it
without further requests. Cache manifests preserve raw metadata/table hashes and
source URLs; they do not extend project SQLite serialization. Human interactive
review, general format support, other providers and scientific validation remain
open. Earlier dated entries below describe the state at their own checkpoints.

---

## Repository Structure

```
ECAS_BETA/
├── ecas/
│   ├── __init__.py
│   ├── models/
│   │   ├── spectrum.py         # SpectrumData model (frozen dataclass)
│   │   └── __init__.py
│   ├── persistence.py          # SQLite storage layer (COMPLETE)
│   ├── visualization/           # Spectral visualization component
│   │   └── spectra_plot.py      # PyQtGraph spectrum plot widget
│   └── ...
├── docs/
│   └── brains/
│       ├── DECISIONS.md        # Design decisions
│       └── PROJECT_STATE.md    # This file
├── tests/                      # Test directory (complete test coverage for persistence and visualization)
│   ├── test_persistence.py     # Persistence tests (20 passing tests)
│   └── test_spectra_plot.py    # Visualization tests (8 passing tests)
├── README.md
└── ...
```

---

## Component Status

### ✅ persistence.py - COMPLETE (Chunk 2)

**Functions Implemented:**
| Function | Description | Status |
|----------|-------------|--------|
| `validate_project_id()` | Sanitizes project ID, prevents path traversal | ✅ |
| `get_project_database()` | Gets path to project's SQLite DB | ✅ |
| `_get_connection()` | Opens/creates SQLite connection | ✅ |
| `_initialize_schema()` | Creates spectra table if needed | ✅ |
| `_to_spectrums_dict()` | Deserializes dict back to SpectrumData | ✅ |
| `save_spectrum_to_database()` | Saves spectrum to project DB | ✅ |
| `load_spectra_from_database()` | Loads all spectra for project | ✅ |
| `load_spectrum_by_index()` | Loads specific spectrum by index | ✅ |
| `clear_project_database()` | Empties project's spectra table | ✅ |
| `count_spectra()` | Counts spectra in project DB | ✅ |

**Storage Format:**
- Each spectrum stored as JSON in TEXT column (via SQLite BLOB/TEXT)
- JSON structure:
  ```json
  {
    "source_file": "/path/to/file",
    "rows": [[1.2, 2.3], [3.4, 4.5]],
    "columns": ["frequency", "intensity"],
    "axis_unit": "Hz",
    "signal_unit": "arbitrary units",
    "signal_type": "NMR",
    "warnings": []
  }
  }
  ```

### ✅ models/spectrum.py - COMPLETE (Chunk 1)

**Class:** `SpectrumData`  
**Attributes:**
- `source_file`: Path to original spectrum file
- `rows`: Tuple of tuples (spectral data matrix, frozen at creation)
- `columns`: Tuple of column names
- `axis_unit`: X-axis unit (e.g., "Hz", may be None)
- `signal_unit`: Y-axis unit (e.g., "arbitrary units", may be None)
- `signal_type`: Signal type (e.g., "NMR", may be None)
- `warnings`: Empty tuple or tuple of warning messages from import

### ✅ visualization/spectra_plot.py - COMPLETE (Chunk 3)

**Location:** `ecas/visualization/spectra_plot.py`

**Role:**
- Receives normalized `SpectrumData`.
- Uses PyQtGraph to display spectral coordinates.
- Is intended to replace the previous plotted dataset when a new one loads.

**Verification results:**
- Automated tests: All plotting tests passed (`tests/test_spectra_plot.py`).
- Full application test suite: **40/40 passing**.
- Manual verification: Application launched successfully; `test_spectrum` imported and displayed with correct plotting.

Current limitation: The generic CSV importer and the explicitly supported WASP-39b archive schema cover the currently implemented CSV paths. Other custom-formatted CSV schemas and research files in TXT or other formats are not necessarily supported. Broader import flexibility and unit selection remain future work. 10-23-2026

**Future work (unchanged):** 
- Additional archive ingestion and online reference-spectrum retrieval (Chunk 4; remaining scope) (10-23-26)
- Spectrum comparison workflow and scientific analysis features (Chunks 5-7)

### ✅ models/spectrum.py - COMPLETE (Chunk 1)

---

### ✅ ingestion/csv_importer.py — ARCHIVE CSV SUPPORT IMPLEMENTED (Chunk 4, current scope)

**Location:** `ecas/ingestion/csv_importer.py`

**Implemented capability:**
- Supports the explicitly configured WASP-39b archive CSV schema.
- Maps `centralwavelng` to canonical `wavelength`.
- Maps `pl_trandep` to canonical `signal`.
- Retains the original source columns and appends the two canonical columns.
- Preserves existing generic CSV import behavior when no archive schema is supplied.
- Rejects unsupported explicitly supplied archive schemas rather than silently using the generic importer.

**Real-data verification:**
- Source: `data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`
- Imported rows: 331
- Imported columns: 23 (21 source columns plus 2 canonical columns)

**Automated verification reported:**
- Archive importer tests: 105 passed.
- Full test suite: 145 passed.

These results reflect the reported test run for the current implementation. Rerun tests after subsequent code changes.

**Scope limitation:** This is support for one identified archive schema, not universal archive CSV compatibility. General online archive retrieval, additional archive schemas, TXT import, and broader unit-handling behavior are not established by this implementation.

---


## Known Issues / TODOs

### Persistence (Chunk 2):
- Comprehensive change-history/provenance tracking remains a future design decision.

### Visualization (Chunk 3) - Completed
- ✅ All automated plotting tests passed.
- ✅ Application launched and `test_spectrum` imported/plotting verified manually.
- ⏳ Dataset-selection behavior deferred per project plan; not implemented in current codebase.

### Testing:
- Full test suite: **40/40 passing** (user-reported result as of 2026-10-22).
---

## Testing Summary

**Latest reported full test suite:** 145 passed.

- Archive CSV importer: 105 tests passed (`tests/test_archive_csv_importer.py`).
- The full suite includes the existing persistence and visualization tests, as well as the new archive importer tests.

**Test Environment:**
- Python interpreter: Python 3.14.0
- Pytest version: pytest-9.1.1

These results describe the reported run and should be refreshed after subsequent code changes.

(10-23-2026)

---

## Next Steps

1. Complete and verify the persistence layer (Chunk 2) — **done**.
2. Complete the plotting component and integrate it into the main window (Chunk 3) — **verified and complete**.
3. Run targeted and full automated tests — **passed (40/40)**.
4. Continue to later chunks only after the current completion criteria are met.

Future work includes:
- Dataset-selection behavior for multiple saved spectra (deferred).
- Online reference-spectrum retrieval from archives (Chunk 4).
- Spectrum comparison workflow and scientific analysis features (Chunks 5-7).

---

## Verification Note

**Automated vs. Manual Verification:**
- Automated tests verify core functionality independently of the GUI.
- Manual verification requires running ECAS and inspecting the plot widget in action; this is separate from automated test results and will be documented once performed.

## Local regression preparation — 2026-10-27

Status: PARTIAL; runtime verification awaits approved dependency downloads.
Baseline: clean master at 6da2dccfe966b9b75dc118aba3d55e606319b579.
The QComboBox import and archive_schema keyword repairs are already present;
no application/scientific behavior was changed in this increment.

- tests/test_main_window.py: added six regression cases for selector labels/default,
  generic/archive schema forwarding through both import routes, and cancellation
  preserving the existing display. Importer mocks use the actual signature.
- test_spectra_schema.py: replaced import-time QApplication creation, hard-coded
  developer paths and print-only success claims with two portable parameterized
  assertions over explicitly synthetic coordinates. Both archive source columns
  and normalized canonical columns must plot unchanged coordinates; missing units
  remain unknown. Existing archive importer tests cover CSV ingestion separately.
- Syntax compilation of both changed modules via Python 3.14.5 with -I -S -B:
  PASS. git diff --check: PASS (line-ending notice only).
- Attempted: python -I -B -m pytest -p no:cacheprovider
  tests/test_main_window.py test_spectra_schema.py -q.
  BLOCKED: No module named pytest. Installed-module discovery also found PySide6
  and pyqtgraph absent. No runtime test pass or manual GUI verification is claimed.
- No downloads, credential use, paid API calls, Argon/other agent launches, commits
  or pushes. Changes remain uncommitted. Independent Argon review is outstanding.

Next: obtain user approval to download the required test/GUI packages into a
project-local environment, run the focused tests and relevant full regression,
then review the final changes. Do not run downloads implicitly. Historical test
counts elsewhere in this document remain reports, not results of this increment.

## Approved local dependency installation and regression verification — 2026-10-27

The user explicitly authorized the required downloads. This continuation resolves
the missing-dependency blocker recorded above. The scoped regression increment is
implemented and locally tested; independent Argon review and delivery are pending.
No application code, scientific interpretation, data values or units were changed.

### Environment and installation

- Project-local `.venv`, already excluded by `.gitignore`; no global packages changed.
- Python 3.14.5 (64-bit AMD64), pytest 9.2.0, PySide6 6.12.0,
  pyqtgraph 0.14.0 and numpy 2.5.4. Transitive package versions and download hashes
  are recorded locally in `.venv/checks/install-report.json`.
- Created using the existing Python executable with `-I -B -m venv .venv`.
  Restricted initialization first failed in ensurepip; the same approved setup
  then succeeded with the execution tool's additional system-access permission.
- Installed using `.venv/Scripts/python.exe -I -B -m pip --isolated
  --disable-pip-version-check --no-input --keyring-provider disabled install
  --index-url https://pypi.org/simple --only-binary=:all: --no-cache-dir
  --report .venv/checks/install-report.json pytest PySide6 pyqtgraph`.
- Dependency installation and test subprocesses received an explicit minimal
  environment, without inherited credentials. Qt ran offscreen; test temp/profile
  paths were inside `.venv/checks`. Plugin auto-loading and pytest cache writes
  were disabled. The initial focused invocation omitted PATH, causing two PySide6
  collection errors; supplying only the local Scripts and Windows System32 paths
  fixed this test-environment issue without an application change.

### Additional regression repair

The first full run reported 152 passed, 1 failed, 1 skipped. The failure was the
existing `tests/test_csv_manual_import.py` expectation that `centralwavelng` was
removed. That contradicted both the importer and the documented provenance rule.
The repaired test requires all 21 source columns in their relative source order,
both canonical aliases, two complete rows and exact alias/source value equality.
It does not change the importer's current output order. The existing real-data
archive test continues to verify that full output order and the 331-row fixture.

### Actual verification

All pytest commands used the local interpreter with `-I -B -m pytest`,
`-p no:cacheprovider -o pythonpath=.`, a fresh project-local `--basetemp`,
`QT_QPA_PLATFORM=offscreen` and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.

| Selection | Result | Exit |
|---|---|---|
| `tests/test_main_window.py test_spectra_schema.py -q` | 10 passed, 3.09 s | 0 |
| Initial full discovery (`-q`) | 152 passed, 1 failed, 1 skipped, 1.42 s | 1 |
| `tests/test_csv_manual_import.py -q` after assertion repair | 1 passed, 0.15 s | 0 |
| Final full discovery (`-q`) | 153 passed, 1 skipped, 1.26 s | 0 |

The skip is `TestProjectIdValidation.test_rejects_symlink_that_escapes_projects_directory`:
directory symlink creation is unavailable. This is not a verified access-denial
result. Manual interactive GUI verification and independent Argon review were not
performed. Software tests do not establish scientific validity.

Exact command arrays, exit codes, environment key names, logs and JUnit XML are
retained locally in `.venv/checks/` (`focused-fixedenv`, `full`, `archive-corrected`,
`full-final` artifacts). The local runner simply sanitizes the environment and
executes those pytest selections; it does not launch an AI service.

### Review and continuity

- Changes: `tests/test_main_window.py`, `test_spectra_schema.py`,
  `tests/test_csv_manual_import.py`, and this record. All remain uncommitted;
  no staging, pushes, real credential use, paid APIs or additional agents.
- Existing archive column-order discrepancy remains: the decision record/docstring
  describes appending both canonical aliases after the original source fields;
  current code and its real-data test put `wavelength` first and `signal` last.
  This increment preserves that current behavior. Reconcile the intended public
  ordering before changing it; the provenance requirement itself is satisfied by
  retaining the original source columns and values.
- Next: review the exact final changes with Argon through an explicitly approved
  route compatible with the user's no-additional-billing/no-real-credential rules,
  or obtain its review manually. Do not claim independent review from these local
  results or enable the custom agent launcher to obtain it implicitly.

## Launch and bundled archive import investigation — 2026-10-27

Reported problem: main.py did not launch on the friend's machine, and manually
importing the bundled archive file failed; incomplete database integration was
suspected. The attached screenshot is historical context, not a fresh failure.

### Verified findings

- Current main.py and app.py both construct and show the ECAS window and enter
  the Qt event loop in the installed project environment. New subprocess smoke
  tests run each real entry point offscreen from another working directory and
  instrument only event-loop exit with a timer. This is automated startup
  verification, not an interactive desktop/double-click test on the friend's host.
  The original launch failure is not reproduced; its traceback/environment remain
  unknown. No unsupported causal fix to main.py is claimed.
- Real local-file imports through both the file-dialog route and path helper
  display all 331 rows and 23 columns when WASP-39 b Archive is selected.
  Generic mode rejects the file. Neither route uses database retrieval. The
  existing archive importer already handles the bundled uppercase source headers.
- The schema selector was below the plot/table, making it easy to miss before
  importing. It is now above Import CSV, with an explicit explanation for the
  bundled example and the absence of any database requirement. Generic remains
  the default; no schema guessing or scientific interpretation was introduced.

### Changes and verification

- ecas/ui/main_window.py: moved schema controls before import and clarified help.
- tests/test_main_window.py: real bundled-file integration tests for both import
  routes, a generic-mode rejection test, and selector-before-button verification.
- tests/test_entry_points.py: two bounded offscreen entry-point smoke tests.
- requirements.txt / requirements-test.txt: recorded the versions already
  installed and verified in this local environment; no additional package types
  or new downloads were needed for this increment.
- README.md: concrete environment/launch/test commands and the exact example-file
  import steps. No activation script or database setup is required to import it.
- Before UI/doc changes, local focused startup/import tests: 13 passed in 2.26 s,
  exit 0. Final full suite: 158 passed, 1 skipped in 2.82 s, exit 0.
  The same directory-symlink-privilege skip remains unverified.
- Executed via .venv/Scripts/python.exe -I -B .venv/checks/run_checks.py
  launch-import-baseline and launch-import-final, respectively. The local driver
  preserves the sanitized offscreen environment from the preceding increment.
  Exact pytest commands, logs and XML are in the corresponding .venv/checks files.

Existing uncommitted regressions were preserved. No data files, importer behavior,
database integration, canonical column ordering, credentials or billing settings
were changed. Nothing staged, committed, pushed or sent; no additional AI agent
was invoked. Independent Argon review is outstanding.

Next: if the friend still cannot launch using the documented environment command,
obtain the full terminal traceback, Python version and exact launch method before
changing startup logic. Manual interactive verification on his host remains open.

## Chunk 4 discovery-protocol increment — 2026-10-27

Added bounded NASA exact planet-name query construction and strict validation of
supplied catalog-response bytes, with synthetic tests. No network caller or search
screen is connected yet, and no archive data was downloaded. This is catalog
identity metadata, not spectral retrieval or scientific validation. SpectrumData,
CSV and persistence behavior remain unchanged. Focused: 35 passed; full: 193 passed,
1 directory-symlink-privilege skip. Historical plans were preserved. See the Chunk 4
implementation log and decisions file for chronology, limitations and the next
download-approval-dependent check. Independent Argon review remains pending.

## Live NASA validation — 2026-10-27

User-authorized public NASA retrieval succeeded: one WASP-39 b catalog identity
validated by the existing parser, plus a partial TOP 20 spectral-metadata snapshot.
Raw responses, exact query URLs, UTC times, HTTP status and hashes are preserved
under data/NASA/2026-10-27. The metadata identifies the Feinstein et al. 2023 NIRISS
331-point record, but its measurement file was not downloaded or equated with the
bundled CSV. The Chunk 4 implementation log and data README contain the evidence
and limitations. Full regression: 195 passed, 1 symlink-privilege skip; exit 0.
No credentials, extra AI agents, commits or pushes. Online search/measurement
retrieval is not yet connected to the application. Public NASA download approval
continues; the other existing scope/billing/credential restrictions remain active.

## NASA measurement import — 2026-10-27

Retrieved the actual 331-row NASA transmission .tbl, with unchanged raw product,
provenance and download-path derivation evidence under data/NASA/2026-10-27.
Added strict NASA transmission IPAC parsing and Import Spectrum support in the
existing GUI. It displays explicitly supplied microns/percent and retains all 29
source columns plus canonical aliases, signed errors, flags, source URLs and file
metadata. CSV import behavior is unchanged. Full regression: 212 passed, one
symlink-privilege skip. Details and limits are in the Chunk 4 implementation log.
Online search and automatic in-app downloading/cache registration are still open;
Argon review is pending. No credentials, extra agents, commits or pushes.
