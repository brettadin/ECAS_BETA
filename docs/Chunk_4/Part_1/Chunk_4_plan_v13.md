# **Chunk 4 — Plan v13: Targeted Corrections Only** #

---

### ✅ Defect Resolution Summary

| Defect # | Description | Resolution in v13 |
|----------|-------------|-------------------|
| 1 | Missing immutable schema constant | Added `WASP_39_B_SCHEMA` module-level constant used consistently |
| 2 | Unclear archive vs generic path separation | Explicit `archive_schema=None` default; separate conditional block for archive mode |
| 3 | Schema validation leaks into generic path | Archive-specific parsing isolated; generic behavior unchanged when no schema provided |
| 4 | Broad prefix fallbacks allow malformed values | Replaced with explicit field classification dictionary |
| 5 | `pl_transmiderr1/err2` classified as metadata | Correctly parsed as numeric error fields (finite floats or None) |
| 6 | Incomplete fixture procedures | All fixtures use `csv.writer`; blank fields properly tested across multiple rows |
| 7 | Missing canonical collision tests | Added tests for `wavelength`/`signal` source header rejection |
| 8 | Unsupported schema silently treated as generic | Explicit rejection with `SpectrumImportError` if schema doesn't match exactly |

---

### 1. Schema Validation & Immutable Constant

**Plan v13 adds:**
```python
# Module-level immutable constant (after imports, before class definitions)
WASP_39_B_SCHEMA = {
    "wavelength": "centralwavelng",
    "signal": "pl_transdep",
}  # type: ignore[assignment]  # Type guard: dict[str, str], not source-header mapping
```

**Usage:**
- `archive_schema=None` → generic path unchanged.
- `archive_schema != WASP_39_B_SCHEMA` → raises `SpectrumImportError("Unsupported archive schema.")`.
- No silent fallback; explicit rejection required.

---

### 2. Generic Behavior Preservation (Unchanged)

**When `archive_schema=None`:**
- Header normalization uses only `COLUMN_ALIASES`.
- Uncertainty column validation unchanged.
- Blank uncertainty → `None` + warning preserved.
- No archive-specific field names (`pl_transdep`, etc.) affect behavior.
- Additional columns preserved in original order via alias dictionary or lowercase fallback.

**Key isolation mechanism:**
```python
def import_spectrum_csv(
    file_path: str | Path,
    archive_schema: dict[str, str] = None,  # Optional parameter; defaults to None
) -> SpectrumData:
    
    use_archive_mode = (
        archive_schema is not None 
        and archive_schema == WASP_39_B_SCHEMA
    )
    
    # Generic path uses COLUMN_ALIASES for all header normalization
    effective_columns_map = (
        archive_schema  # Only when exact match
        if use_archive_mode
        else COLUMN_ALIASES
    )
    
    # ... rest of generic logic unchanged ...
```

---

### 3. Archive Schema & Header Validation Rules

**Validation sequence (archive mode only):**

1. **Normalize headers independently** — Strip whitespace, lowercase, use `COLUMN_ALIASES` (not `archive_schema`).

2. **Reject duplicates** — Check `len(columns) != len(set(columns))`.

3. **Reject canonical collisions** — Reject if any source header normalizes to `"wavelength"` or `"signal"`.

4. **Require both sources** — Both `"centralwavelng"` and `"pl_transdep"` must exist in normalized columns.

5. **Preserve 21 source columns** — Append `("wavelength", "signal")` after the 21 source fields.

6. **Final tuple length** — Must be exactly 23 unique entries when archive mode is active.

---

### 4. Explicit Archive Field Classification

**Replaces broad prefix fallbacks with explicit dictionary:**

```python
# Inside row parsing (archive mode only)
ARCHIVE_NUMERIC_FIELDS = [
    "centralwavelng", "bandwidth", "pl_transdep",
    "pl_transdeperr1", "pl_transdeperr2", "pl_ratror",
    "pl_ratrorerr1", "pl_ratrorerr2", "pl_radj",
    "pl_radjerr1", "pl_radjerr2", "pl_transmid",
    "pl_transmiderr1", "pl_transmiderr2", "st_rad",
    "st_raderr1", "st_raderr2",
]

ARCHIVE_METADATA_FIELDS = [
    "pl_transdep_authors", "pl_ratror_authors", 
    "pl_radj_authors", "st_rad_authors"
]

def _parse_archive_field(field_name: str, value: str) -> CellValue:
    """Parse archive-specific field with exact classification."""
    
    if field_name in ARCHIVE_NUMERIC_FIELDS:
        if value == "":
            return None  # Blank optional numeric → None
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise SpectrumImportError(f"Line X:'{field_name}' must be numeric.") from None
        if not math.isfinite(num):
            raise SpectrumImportError(f"Line X:'{field_name}' must be finite.") from None
        return num
    
    elif field_name in ARCHIVE_METADATA_FIELDS:
        # Metadata fields stay as strings; blank → ""
        return (value or "").strip() if value else ""
    
    elif field_name == "uncertainty":
        # Uncertainty handling (generic path only, archive has no uncertainty column)
        ...
```

**Special rules:**
- `centralwavelng` and `pl_transdep` **required**: must be populated finite floats; blank/malformed raises error.
- All signed error offsets (`*err1`, `*err2`) preserve original sign (negative allowed).
- `pl_transmid` numeric field: blanks → `None`, populated → finite float or text string (not reinterpreted).
- `pl_transmiderr1/err2`: now treated as numeric error fields; blanks → `None`, malformed → error.

---

### 5. Corrected Fixture Procedures (csv.writer Context Management)

**Exact fixture header (21 source columns):**
```python
HEADER_LIST = [
    "centralwavelng", "bandwidth", "pl_transdep", 
    "pl_transdeperr1", "pl_transdeperr2", "pl_transdep_authors",
    "pl_ratror", "pl_ratrorerr1", "pl_ratrorerr2", "pl_ratror_authors",
    "pl_radj", "pl_radjerr1", "pl_radjerr2", "pl_radj_authors",
    "pl_transmid", "pl_transmiderr1", "pl_transmiderr2",
    "st_rad", "st_raderr1", "st_raderr2", "st_rad_authors"
]
```

**Row 1: All fields populated except `pl_transmid` (blank → None)**
```python
ROW_1 = [
    "0.63096",      # centralwavelng
    "0.00147",      # bandwidth
    "2.1065",       # pl_transdep
    "0.01396",      # pl_transdeperr1 (+)
    "-0.01396",     # pl_transdeperr2 (-, preserves sign!)
    "Feinstein et al. 2022",  # pl_transdep_authors
    "0.14514",      # pl_ratror
    "0.00048",      # pl_ratrorerr1 (+)
    "-0.00048",     # pl_ratrorerr2 (-)
    "Calculated",   # pl_ratror_authors
    "1.2641",       # pl_radj
    "0.0328",       # pl_radjerr1 (+)
    "-0.0328",      # pl_radjerr2 (-)
    "Calculated",   # pl_radj_authors
    "",             # pl_transmid (blank → None)
    "",             # pl_transmiderr1 (blank → "")
    "",             # pl_transmiderr2 (blank → "")
    "0.895",        # st_rad
    "0.023",        # st_raderr1 (+)
    "-0.023",       # st_raderr2 (-)
    "Faedi et al. 2011"  # st_rad_authors
]
```

**Row 2: Blank `centralwavelng` (error), populated `pl_transmid` to test numeric parsing**
```python
ROW_2 = [
    "",             # centralwavelng → should trigger "must be numeric" error
    "0.00147",      # bandwidth
    "3.4500",       # pl_transdep
    "0.0150",       # pl_transdeperr1 (+)
    "-0.0150",      # pl_transdeperr2 (-, preserves sign!)
    "Example 2023", # pl_transdep_authors
    "",             # pl_ratror → None
    "",             # pl_ratrorerr1 → None
    "",             # pl_ratrorerr2 → None
    "",             # pl_ratror_authors → ""
    "1.5000",       # pl_radj
    "0.0400",       # pl_radjerr1 (+)
    "-0.0400",      # pl_radjerr2 (-)
    "Smith 2020",   # pl_radj_authors
    "3.5000",       # pl_transmid (numeric value)
    "",             # pl_transmiderr1 → ""
    "",             # pl_transmiderr2 → ""
    "0.9500",       # st_rad
    "0.030",        # st_raderr1 (+)
    "-0.030",       # st_raderr2 (-)
    "Jones 2018"    # st_rad_authors
]
```

**Fixture construction with csv.writer:**
```python
def test_import_wasp_39_b_archive_schema(tmp_path):
    path = tmp_path / "WASP-39-b.csv"
    
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER_LIST)
        writer.writerow(ROW_1)  # Valid row for positive test
```

**Note:** Additional error tests should use text file writes (not CSV writer) to simulate malformed inputs like blank required fields or non-numeric values.

---

### 6. Required Test Coverage Matrix

| Test Case | Expected Outcome | Key Assertion |
|-----------|------------------|---------------|
| Exact 23-column order & uniqueness | Success | `result.columns == EXPECTED_COLUMNS_WASP_39_B` |
| Row keys match final columns exactly | Success | `set(row.keys()) == set(result.columns)` |
| Canonical aliases equal source values | Success | `row["wavelength"] == row["centralwavelng"]` |
| Numeric parsing (finite floats) | Success | All numeric fields parsed correctly |
| Signed errors preserved | Success | `-0.01396` stored as negative, not absolute |
| Blank optional numeric → None | Success | `row["pl_transmid"] is None` |
| Blank author fields → "" | Success | `row["pl_transdep_authors"] == "Feinstein et al."` |
| Missing `centralwavelng` header | Error | `SpectrumImportError("Missing required columns: centralwavelng")` |
| Missing `pl_transdep` header | Error | Same error message pattern |
| Blank required `centralwavelng` in data row | Error | `"centralwavelng" must be numeric"` |
| Malformed optional numeric values | Error | Field-specific error message |
| Duplicate normalized source headers | Error | `SpectrumImportError("duplicate or conflicting column names")` |
| Source header named `wavelength`/`signal` | Error | `SpectrumImportError("canonical-name collision")` |
| Unsupported archive schema mapping | Error | `SpectrumImportError("Unsupported archive schema.")` |

---

### 7. Final Expected Tuple (23 Unique Entries)

```python
EXPECTED_COLUMNS_WASP_39_B = (
    "centralwavelng",           # 1 (required source, canonical)
    "bandwidth",                 # 2
    "pl_transdep",              # 3 (required source, canonical)
    "pl_transdeperr1",          # 4
    "pl_transdeperr2",          # 5
    "pl_transdep_authors",      # 6
    "pl_ratror",                # 7
    "pl_ratrorerr1",            # 8
    "pl_ratrorerr2",            # 9
    "pl_ratror_authors",        # 10
    "pl_radj",                  # 11
    "pl_radjerr1",              # 12
    "pl_radjerr2",              # 13
    "pl_radj_authors",          # 14
    "pl_transmid",              # 15
    "pl_transmiderr1",          # 16 (numeric error field)
    "pl_transmiderr2",          # 17 (numeric error field)
    "st_rad",                   # 18
    "st_raderr1",               # 19
    "st_raderr2",               # 20
    "st_rad_authors",           # 21
    "wavelength",               # 22 (canonical alias from centralwavelng)
    "signal",                   # 23 (canonical alias from pl_transdep)
)

assert len(EXPECTED_COLUMNS_WASP_39_B) == 23
assert len(set(EXPECTED_COLUMNS_WASP_39_B)) == 23
```

---

### 8. Explanation: How Generic Behavior Remains Unchanged

- **Default parameter**: `archive_schema=None` → generic path unchanged.
- **Header normalization**: Always uses `COLUMN_ALIASES` (unless archive mode enabled).
- **Uncertainty validation**: Only active when `"uncertainty"` column exists in source headers; archive schema has no uncertainty column, so this never triggers in archive mode.
- **Warnings**: Same pattern (`missing_uncertainty_count`) and messages apply to generic path only.
- **No leakage**: Archive-specific dictionaries (`ARCHIVE_NUMERIC_FIELDS`, etc.) scoped inside conditional block; not imported or referenced by generic tests.

---

### ✅ Confirmation: No Files Modified, No Tests Run

- **Files modified**: None (Plan mode only).
- **Tests executed**: None.
- **Implementation deferred** pending user approval to enter ACT mode.

**Plan v13 is complete and ready for review.**

<br>
<br>
<br>
<br>
<br>

# CHATGPT REVIEW #

Plan v13 is not approved for ACT yet. It resolves several previous issues, but four concrete inconsistencies remain. These are narrow corrections; no need to restart planning.

## Remaining blockers

| Priority | Issue                                                                                                                                                                                                                                                                                                        | Required correction                                                                                                                                                      |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Critical | The second fixture row deliberately contains blank `centralwavelng`. The plan says every accepted row must have finite values for both required canonical source fields. The positive test currently writes only row 1, but the proposed fixture description still treats row 2 as part of the same dataset. | Keep valid rows exclusively in the positive fixture. Create a separate negative-test fixture containing a blank `centralwavelng` value.                                  |
| Critical | `pl_transmid` has contradictory parsing rules. The field-classification function says all numeric fields must be finite floats or `None`, but a special rule permits text values.                                                                                                                            | Treat `pl_transmid` as numeric, consistent with the stated archive requirements. Blank becomes `None`; malformed nonblank values raise `SpectrumImportError`.            |
| High     | Blank numeric detection is too narrow. The proposed parser checks `value == ""`, so whitespace-only fields may be treated as malformed instead of blank.                                                                                                                                                     | Strip field values before blank checks and numeric conversion. Preserve author fields as trimmed strings.                                                                |
| High     | The schema constant is not actually immutable. A normal dictionary remains mutable; `type: ignore[assignment]` does not make it immutable.                                                                                                                                                                   | Use an immutable representation, or explicitly establish and document an immutable mapping. Ensure the public schema argument can still be compared reliably against it. |

One additional implementation detail: the plan must ensure that canonical aliases are derived from the validated parsed values of `centralwavelng` and `pl_transdep`, and that every returned row contains exactly the 23 declared columns.

## Send Cline this final targeted correction

## Chunk 4 — Plan v14 Final Targeted Corrections

**Mode: PLAN only. Do not modify files or run tests.**

Revise Plan v13 only to resolve the four remaining defects and confirm row construction. Do not restart analysis or expand scope.

### 1. Separate valid and invalid fixtures

- The positive archive-import fixture must contain only rows with finite numeric `centralwavelng` and `pl_transdep`.
- Move the row with blank `centralwavelng` into a separate negative-test fixture.
- Add separate negative tests for blank and malformed `centralwavelng`, and for blank and malformed `pl_transdep`.
- Test missing required source headers independently from invalid required data values.

### 2. Make `pl_transmid` classification consistent

- Treat `pl_transmid` as a numeric archive field.
- Blank or whitespace-only values become `None`.
- Populated values must parse as finite floats.
- Malformed nonblank values raise `SpectrumImportError`.
- Remove any conflicting rule that permits arbitrary text for `pl_transmid`.

### 3. Normalize blank and numeric values

- Strip surrounding whitespace before checking whether a numeric field is blank and before converting it to a float.
- Blank optional numeric fields become `None`.
- Nonblank malformed or non-finite numeric fields raise `SpectrumImportError`.
- Preserve negative error offsets without taking absolute values.
- Author metadata remains strings, with surrounding whitespace removed and blank values represented as `""`.

### 4. Correct schema immutability

- Replace the mutable module-level schema dictionary with an immutable representation, such as `MappingProxyType`, if compatible with the function's public API.
- Alternatively, use an immutable tuple-based internal constant and construct or compare the supported mapping explicitly.
- Keep the accepted schema mapping and its canonical-to-source meaning unchanged:
  - `wavelength` → `centralwavelng`
  - `signal` → `pl_transdep`
- `archive_schema=None` must retain generic behavior.
- Any supplied unsupported schema must raise `SpectrumImportError`.
- Do not modify global `COLUMN_ALIASES`.

### 5. Confirm row construction

- Validate required source values before creating canonical aliases.
- Populate `wavelength` from the validated parsed `centralwavelng` value and `signal` from the validated parsed `pl_transdep` value.
- Ensure every successful archive row has exactly the same keys as the 23-column output tuple.
- Preserve all 21 normalized source fields in their original order, then append `wavelength` and `signal`.

### Response requirements

Return the revised plan and a concise defect-resolution summary only. Do not modify files, run tests, or enter ACT mode. Do not revisit previously resolved items or propose unrelated improvements.

Once you have Plan v14, share it for review. If these corrections are addressed without new contradictions, we can approve ACT without another broad planning cycle.