# **Plan v19 — Final Corrections Applied for ACT-Ready** #

---

## Corrections Applied (v18 → v19)

### 1. Column Order Preservation Using Original Header List

```python
def _import_archive_schema_csv(
    file_path: Path,
    schema: dict[str, str]  # Must be exactly WASP-39 b or raise before this path
) -> SpectrumData:
    
    # ... existing validation for exact WASP-39 b schema raises immediately if not exact match ...
    
    path = Path(file_path).resolve()
    
    if not path.exists() or not path.is_file():
        raise SpectrumImportError(f"File does not exist: {path}")
    
    if path.suffix.lower() != ".csv":
        raise SpectrumImportError("Expected a .csv file.")
    
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames or any(
                fn is None or not fn.strip() for fn in reader.fieldnames
            ):
                raise SpectrumImportError("CSV contains an empty column name.")
            
            original_headers_list = reader.fieldnames  # Keep as list to preserve order
            
            # Reject duplicate headers BEFORE any set comparison
            if len(original_headers_list) != len(set(original_headers_list)):
                duplicates = [h for h in original_headers_list if original_headers_list.count(h) > 1]
                raise SpectrumImportError(
                    f"CSV contains duplicate column names: {', '.join(sorted(set(duplicates)))}"
                )
            
            # Now safe to validate against expected sources
            if set(original_headers_list) != EXPECTED_ARCHIVE_SOURCES:
                missing = EXPECTED_ARCHIVE_SOURCES - set(original_headers_list)
                extra = set(original_headers_list) - EXPECTED_ARCHIVE_SOURCES
                raise SpectrumImportError(
                    f"Archive CSV has unsupported headers. "
                    f"Missing: {sorted(missing)}, Extra: {sorted(extra)}"
                )
            
            # Headers validated and unique → parse rows using exact field names from original list
            parsed_rows: list[dict[str, CellValue]] = []
            
            for line_number, raw_row in enumerate(reader, start=2):
                if None in raw_row.values():
                    raise SpectrumImportError(
                        f"Line {line_number}: more values than header columns."
                    )
                
                parsed_row: dict[str, CellValue] = {}
                
                # Use original header names (already validated to match expected sources)
                for field_name in EXPECTED_ARCHIVE_SOURCES:  # Exact source name as key
                    raw_value = raw_row.get(field_name)
                    parsed_row[field_name] = _parse_archive_field(field_name, raw_value)
                
                parsed_rows.append(parsed_row)
            
            if not parsed_rows:
                raise SpectrumImportError("CSV contains no spectrum data rows.")
            
            # Construct final columns: preserve original header order + append canonical aliases
            # original_headers_list already validated to be exact 21-source names in correct order
            columns_tuple = tuple(original_headers_list + ["wavelength", "signal"])
            
            model_rows: list[dict[str, CellValue]] = []
            
            for parsed_row in parsed_rows:
                row_dict: dict[str, CellValue] = dict(parsed_row)
                row_dict["wavelength"] = parsed_row["centralwavelng"]
                row_dict["signal"] = parsed_row["pl_transdep"]
                
                if len(row_dict) != 23:
                    raise SpectrumImportError(
                        f"Row has {len(row_dict)} columns instead of 23."
                    )
                
                model_rows.append(row_dict)
            
            return SpectrumData(
                source_file=path,
                columns=columns_tuple,
                rows=tuple(model_rows),
                warnings=[],
            )
```

### 2. Parametrized Tests for Optional Signed-Numeric Values

Instead of testing each optional signed field separately, use parametrization to cover `nan`, `inf`, and `-inf` across representative fields:

```python
import pytest
from itertools import product

# Define all optional signed-numeric fields for parameterization
OPTIONAL_SIGNED_NUMERIC_FIELDS = [
    "pl_transdeperr1", "pl_transdeperr2",
    "pl_ratrorerr1", "pl_ratrorerr2",
    "pl_radjerr1", "pl_radjerr2",
    "pl_transmiderr1", "pl_transmiderr2",
    "st_raderr1", "st_raderr2"
]


@pytest.mark.parametrize("field_name,value", product(OPTIONAL_SIGNED_NUMERIC_FIELDS, 
                                                    [("nan", "nan"), ("inf", "inf"), ("-inf", "-inf")]))
def test_nonfinite_optional_signed_field(tmp_path, field_name: str, value: str):
    """Parametrized test: non-finite values in optional signed-numeric fields raise."""
    
    path = tmp_path / f"bad_{field_name}.csv"
    
    COMPLETE_HEADER = [
        "centralwavelng", "bandwidth", "pl_transdep", 
        "pl_transdeperr1","pl_transdeperr2","pl_transdep_authors",
        "pl_ratror","pl_ratrorerr1","pl_ratrorerr2","pl_ratror_authors",
        "pl_radj","pl_radjerr1","pl_radjerr2","pl_radj_authors",
        "pl_transmid","pl_transmiderr1","pl_transmiderr2",
        "st_rad","st_raderr1","st_raderr2","st_rad_authors"
    ]
    
    # Build row with valid values for all fields except the one being tested
    # Field order matches COMPLETE_HEADER indices: field_name is at index 3 + i (where i=0..9)
    header_to_idx = {name: i for i, name in enumerate(COMPLETE_HEADER)}
    target_idx = header_to_idx[field_name]
    
    row_values = ["0.63096", "0.00147", "2.1065"]  # First 3 fields valid
    other_fields = [COMPLETE_HEADER[i+3] for i in range(21) if COMPLETE_HEADER[i+3] != field_name]
    
    # Build row: first 3 fields, then fill remaining 18 positions (skipping target field)
    row = []
    for idx, header in enumerate(COMPLETE_HEADER):
        if header == "centralwavelng":
            row.append("0.63096")
        elif header == "bandwidth":
            row.append("0.00147")
        elif header == "pl_transdep":
            row.append("2.1065")
        elif header == field_name:
            row.append(value)  # This is nan, inf, or -inf
        else:
            if header in ["pl_transdep_authors", "pl_ratror_authors", 
                          "pl_radj_authors", "st_rad_authors"]:
                row.append("Calculated" if "pl_" in header or "st_" in header else "")
            elif header in ["pl_transmiderr1", "pl_transmiderr2"]:
                row.append("")  # optional numeric blank for simplicity
            else:
                # Fill with generic finite values
                row.append("0.0" if idx % 3 != 2 else f"{idx}")
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_HEADER)
        writer.writerow(row)
    
    WASP_39_B_SCHEMA = {
        "wavelength": "centralwavelng",
        "signal": "pl_transdep"
    }
    
    with pytest.raises(SpectrumImportError, match=f"'{field_name}' must be finite"):
        import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)


def test_valid_optional_signed_field(tmp_path):
    """Test: Valid finite values in optional signed-numeric fields succeed."""
    
    path = tmp_path / "valid.csv"
    
    COMPLETE_HEADER = [
        "centralwavelng", "bandwidth", "pl_transdep", 
        "pl_transdeperr1","pl_transdeperr2","pl_transdep_authors",
        "pl_ratror","pl_ratrorerr1","pl_ratrorerr2","pl_ratror_authors",
        "pl_radj","pl_radjerr1","pl_radjerr2","pl_radj_authors",
        "pl_transmid","pl_transmiderr1","pl_transmiderr2",
        "st_rad","st_raderr1","st_raderr2","st_rad_authors"
    ]
    
    # All finite values for signed-numeric fields
    row = [
        "0.63096",   # centralwavelng
        "0.00147",   # bandwidth
        "2.1065",    # pl_transdep
        "0.01396",   # pl_transdeperr1 finite
        "-0.01396",  # pl_transdeperr2 finite
        "Feinstein et al. 2022",
        "0.14514",   # pl_ratror
        "0.00048",   # pl_ratrorerr1 finite
        "-0.00048",  # pl_ratrorerr2 finite
        "Calculated",# pl_ratror_authors
        "1.2641",    # pl_radj
        "0.0328",    # pl_radjerr1 finite
        "-0.0328",   # pl_radjerr2 finite
        "Calculated",# pl_radj_authors
        "",          # pl_transmid (optional numeric blank → "" allowed for test)
        "0.05",      # pl_transmiderr1 finite
        "-0.05",     # pl_transmiderr2 finite
        "0.895",     # st_rad
        "0.023",     # st_raderr1 finite
        "-0.023",    # st_raderr2 finite
        "Faedi et al. 2011"   # st_rad_authors
    ]
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COMPLETE_HEADER)
        writer.writerow(row)
    
    WASP_39_B_SCHEMA = {
        "wavelength": "centralwavelng",
        "signal": "pl_transdep"
    }
    
    result = import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)
    assert result is not None
    assert len(result.columns) == 23
    
    # Verify all signed-numeric fields contain finite values
    for field in OPTIONAL_SIGNED_NUMERIC_FIELDS:
        val = result.rows[0][field]
        if isinstance(val, float):
            assert math.isfinite(val), f"Field {field} should be finite"
```

---

## ✅ Confirmation: Plan v19 Ready for ACT

- **Column order preserved**: `original_headers_list` (validated as unique 21-source names) used to build columns_tuple.
- **Duplicate headers rejected**: Check `len(original_headers_list) != len(set(original_headers_list))` before set comparison.
- **Parametrized tests for optional signed-numeric fields**: Covers `nan`, `inf`, `-inf` across all 10 optional signed fields using `@pytest.mark.parametrize`.
- **All previous requirements preserved**: Schema validation, finite checks, required field rejection, optional blank handling, canonical alias addition, and exception type standardization unchanged.

**Plan v19 is final and ready for ACT mode execution.**

<br>
<br>
<br>
<br>
<br>

# **CHATGPT REVIEW** #

Not fully corrected yet. The column-order and duplicate-header fixes are correct, but the parametrized test has a defect that could make the tests fail for the wrong reason.

- Column order: Correct. It preserves the original header order and appends the two canonical columns.
- Duplicate headers: Correct. Duplicates are checked before converting headers to a set.
- Optional signed-numeric tests: Not correct as written. The `product()` call pairs each field with a two-element tuple such as `("nan", "nan")`, so `value` is a tuple rather than a string. The test then attempts to write that tuple as a CSV cell, which is not the intended test input.
- Test row construction: Also unnecessarily complicated and risks generating values that don't match the field classifications. Build a known-valid 21-field row and replace only the selected field with the non-finite value.

Since you asked to proceed with implementation, don't start another full planning cycle. Send Cline this ACT prompt with the correction included. It should use the repository's actual files and documentation as the authority.

# ECAS Chunk 4 — ACT: Implement NASA Archive CSV Support

**Mode: ACT. Implement the approved Chunk 4 scope now. Do not produce another plan or edit planning documents.**

## 1. Read the project context first

Inspect the current repository and read the relevant existing documentation before editing. Search for and read all relevant Chunk 4 planning and reference material, including the plans through v19, Chunk 4 guidelines, implementation log, decisions, project state, and any other documents governing ingestion, CSV imports, spectrum data, testing, or project conventions.

Planning documents are **reference only**. Do not edit, rename, delete, or regenerate any planning document. If two documents conflict, use the current code and established project decisions alongside the latest approved requirements to determine the implementation, and record any unresolved conflict in the appropriate non-plan documentation.

Inspect these implementation assets before changing code:

- `ecas/ingestion/csv_importer.py`
- Existing tests for CSV/spectrum importing and related validation
- The `SpectrumData` model and `CellValue` type definitions
- `data/WASP-39b/table_WASP-39-b-Feinstein-et-al.-2023.csv`
- Relevant `pyproject.toml`, test configuration, and documentation conventions

Use actual repository paths if any listed path differs. Do not assume proposed code snippets in historical plans are production-ready.

## 2. Implement the agreed behavior

Implement archive CSV support in `ecas/ingestion/csv_importer.py`, preserving existing generic CSV behavior.

### Schema selection

- `archive_schema=None` must continue to use the existing generic importer without behavior changes.
- Accept only the exact WASP-39 b mapping:
  - `wavelength` → `centralwavelng`
  - `signal` → `pl_transdep`
- Any unsupported, malformed, or extra-key supplied schema must raise `SpectrumImportError("Unsupported archive schema.")`. Never fall back to generic import for an unsupported supplied schema.
- Do not mutate or use global `COLUMN_ALIASES` for archive-specific header handling.

### Archive headers and columns

- Require exactly the 21 expected source fields established in the approved Chunk 4 requirements.
- Reject empty, missing, extra, duplicate, or conflicting headers with `SpectrumImportError`. Detect duplicate headers before converting them to a set or mapping.
- Preserve the CSV's original source-column order, then append canonical `wavelength` and `signal` columns. The result must have 23 columns.
- Parse and preserve every source field; do not map `pl_ratror` or `pl_radj` to canonical fields.
- Ensure parsed row dictionaries contain all 21 source fields plus `wavelength` and `signal`, with exactly 23 keys. Canonical values must equal `centralwavelng` and `pl_transdep`, respectively.

### Field parsing

Apply the previously approved field classifications:

- Required finite numeric fields: `centralwavelng`, `pl_transdep`.
- Optional numeric fields: blank becomes `None`.
- Optional signed-numeric error fields: preserve finite positive or negative values and signs; blank becomes `None`.
- Every nonblank numeric field must parse as a finite float. Reject malformed values, NaN, positive infinity, and negative infinity with `SpectrumImportError`, including optional signed-numeric fields.
- Required fields must raise `SpectrumImportError` when blank, whitespace-only, malformed, or non-finite.
- Author/metadata fields must be strings stripped of surrounding whitespace; blank becomes `""`.
- Do not infer units or reinterpret values.
- Use `SpectrumImportError` consistently for archive-mode validation and parsing failures.
- Do not introduce unrelated refactoring.

## 3. Implement complete, executable tests

Follow the repository's existing testing conventions. Use `csv.writer` and complete, correctly sized 21-column fixtures. Avoid pseudocode, ellipses, and tests that fail before reaching the behavior they are intended to test.

Include tests for:

- Valid archive import, all 21 preserved source columns, 23 total columns, canonical aliases, source order, metadata trimming, signed-value preservation, and optional blank numeric fields.
- Unsupported schemas: wrong mapping, missing key, extra key, and malformed schema type.
- Empty, missing, extra, duplicate, and conflicting headers.
- Required fields independently rejecting blank, whitespace-only, malformed, `nan`, `inf`, and `-inf` for both `centralwavelng` and `pl_transdep`.
- Optional signed-numeric fields rejecting `nan`, `inf`, and `-inf`.
- Malformed nonblank optional numeric values.
- Empty files/data rows and incorrect row widths, where consistent with existing importer conventions.
- Backward compatibility of generic imports when `archive_schema=None`, including existing generic-import tests.

**Important test-fixture correction:** Do not copy the faulty parametrization in Plan v19. Its `product()` expression passes a tuple as the test value rather than a string. Use something equivalent to `@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])`, combined with the field parameter if desired. Build one complete, known-valid row, replace only the target field, and assert that the import fails specifically for that field. Confirm every generated row has exactly 21 values.

Do not modify unrelated tests merely to make them pass. If an existing test exposes a genuine regression caused by this change, fix the regression within scope.

## 4. Update appropriate non-plan documentation

Inspect the repository's existing documentation conventions and update the relevant non-plan documents to record:

- The implemented archive schema and field mapping
- Header and numeric-validation behavior
- Tests and actual test results
- Any limitations, unresolved issues, or decisions that require follow-up

Use the existing Chunk 4 guidelines, implementation log, or other appropriate non-plan documents as applicable. Do not create redundant documents if an existing document is the right place. **Do not edit planning documents**, even to mark them complete.

Do not claim tests passed unless you actually ran them. Record any commands that could not be run and the reason.

## 5. Verification and final report

Run the focused new tests first, then relevant existing importer tests, then the broader test suite if practical.

After implementation, report:

1. Files created or changed, with a short reason for each.
2. Test commands actually executed and their pass/fail results.
3. Any unresolved failures, limitations, or decisions that need follow-up.
4. Confirmation that planning documents were left untouched.

If a concrete blocker prevents implementation or testing, do not silently change the design. Document the blocker in the appropriate non-plan document and explain it in the final report.

Proceed with implementation now.

When Cline finishes ACT, send me its implementation summary and test results. I'll review the actual changes and results rather than returning to another planning cycle.