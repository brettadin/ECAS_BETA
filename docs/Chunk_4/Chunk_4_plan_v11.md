---

# **Chunk 4 Plan v11 — Internally Consistent Implementation**

## Summary of Defects Resolved in v11

Plan v11 addresses the review's identified defects:
1. ✅ **No global alias dictionary mutation** — Archive schema passed as parameter without modifying `COLUMN_ALIASES`.
2. ✅ **General import path unchanged** — Existing tests and behavior remain intact.
3. ✅ **Source headers normalized then canonical aliases appended** — Original order preserved; 23 unique columns in model.
4. ✅ **Collision detection without false positives** — Explicit validation of required source fields + duplicate checks.
5. ✅ **Fixture uses proper CSV construction** — Uses `csv.writer` context manager, not string splitting.
6. ✅ **All 21 normalized source names including metadata** — Full column list specified with exact order and counts.
7. ✅ **Model API compliance verified** — `SpectrumData(columns: tuple[str, ...], rows: tuple[dict])` structure respected.

---

## 1. Final Schema Selection and Storage Contract

### Optional Archive Schema Parameter (Signature Update)

```python
def import_spectrum_csv(
    file_path: str | Path,
    archive_schema: dict[str, str] = None,
) -> SpectrumData:
    """Import spectrum CSV with optional WASP-39 b schema.

    Args:
        file_path: Path to the CSV file.
        archive_schema: Optional dict of canonical_name -> source_column for
            WASP-39 b only. When provided:
            - All 21 source columns preserved in original order (normalized).
            - Canonical aliases "wavelength" and "signal" added after sources.
            - Total columns: exactly 23 unique.

    Behavior when archive_schema is None:
        - Generic alias mapping from COLUMN_ALIASES applies to all CSVs.
        - All additional columns preserved as lowercase strings.
        - No canonical aliases added unless they already exist in source.
        - Existing tests and behavior unchanged.
    """
```

### Schema Validation Rules
```python
# Inside import_spectrum_csv, after opening file:

WASP_39_B_SCHEMA = {
    "wavelength": "centralwavelng",
    "signal": "pl_transdep",
}

if archive_schema is not None and archive_schema != WASP_39_B_SCHEMA:
    raise SpectrumImportError(
        f"Unsupported archive schema. Only WASP-39 b schema supported: {WASP_39_B_SCHEMA}"
    )

# Validate both source fields exist in headers
if "centralwavelng".lower() not in reader.fieldnames:
    raise SpectrumImportError("Missing required source column: centralwavelng")
if "pl_transdep".lower() not in reader.fieldnames:
    raise SpectrumImportError("Missing required source column: pl_transdep")
```

---

## 2. Definitive Field Classifications (WASP-39 b Only)

| Exact Header Name | Normalized Form | Type | Validation Rules |
|------------------|-----------------|------|------------------|
| `centralwavelng` | `centralwavelng` | float | Required source; finite float required; blanks → None |
| `bandwidth` | `bandwidth` | float | Optional numeric field |
| `pl_transdep` | `pl_transdep` | float | Required source for signal canonical |
| `pl_transdeperr1` | `pl_transdeperr1` | float | Signed error offset; preserves negative values |
| `pl_transdeperr2` | `pl_transdeperr2` | float | Symmetric error bound |
| `pl_transdep_authors` | `pl_transdep_authors` | str | Citation metadata; blanks → "" |
| `pl_ratror` | `pl_ratror` | float | Optional numeric field (not wavelength substitute) |
| `pl_ratrorerr1` | `pl_ratrorerr1` | float | Signed error offset |
| `pl_ratrorerr2` | `pl_ratrorerr2` | float | Symmetric error bound |
| `pl_ratror_authors` | `pl_ratror_authors` | str | Citation metadata; blanks → "" |
| `pl_radj` | `pl_radj` | float | Optional numeric field (not signal substitute) |
| `pl_radjerr1` | `pl_radjerr1` | float | Signed error offset |
| `pl_radjerr2` | `pl_radjerr2` | float | Symmetric error bound |
| `pl_radj_authors` | `pl_radj_authors` | str | Citation metadata; blanks → "" |
| `pl_transmid` | `pl_transmid` | mixed | Optional numeric/text; blanks → None |
| `pl_transmiderr1` | `pl_transmiderr1` | str | Error field for mid; preserves blanks as "" |
| `pl_transmiderr2` | `pl_transmiderr2` | str | Error field for mid; preserves blanks as "" |
| `st_rad` | `st_rad` | float | Optional numeric field |
| `st_raderr1` | `st_raderr1` | float | Signed error offset |
| `st_raderr2` | `st_raderr2` | float | Symmetric error bound |
| `st_rad_authors` | `st_rad_authors` | str | Citation metadata; blanks → "" |

**Canonical Aliases (Added After Source Columns):**
- `wavelength` → from `centralwavelng`
- `signal` → from `pl_transdep`

---

## 3. Collision Policy and Error Handling

### Allowed Collisions
| Scenario | Outcome |
|----------|---------|
| `wavelength` source column present (generic) without `centralwavelng` | Generic alias mapping applies; normal behavior. |
| Both `pl_transdep` and `signal` columns exist in CSV | **Raises error** — ambiguous source for signal. |
| Both `centralwavelng` and `wavelength` columns exist | **Raises error** — duplicate wavelength sources. |

### Forbidden Collisions
```python
# After normalizing headers, check for collisions:

seen_canonicals: dict[str, int] = {}  # normalized -> first index seen

for i, (original_header, normalized) in enumerate(zip(original_headers, columns)):
    if normalized in seen_canonicals:
        # Special case: signal canonical from pl_transdep is allowed with source
        if normalized == "signal" and original_header.lower() == "pl_transdep":
            pass  # Intentional duplicate detection for this pair only
        elif normalized == "wavelength" and original_header.lower() == "centralwavelng":
            pass  # Also intentional, as wavelength canonical follows source
        else:
            raise SpectrumImportError(
                f"Column collision detected: '{normalized}' already exists at index {seen_canonicals[normalized]}."
            )

    seen_canonicals[normalized] = i
```

---

## 4. Coherent Implementation Sequence

### Step A: File and Header Validation (Lines 1-86)
```python
path = Path(file_path)
archive_schema = archive_schema if archive_schema else {}  # Default to None-like empty dict

if path.exists() and path.is_file() and path.suffix.lower() == ".csv":
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        
        if not reader.fieldnames or any(h is None or not h.strip() for h in reader.fieldnames):
            raise SpectrumImportError(...)

        original_headers = list(reader.fieldnames)

        # Normalize headers (lowercase, strip whitespace)
        normalized_headers = tuple(
            archive_schema.get(h.strip().lower(), h.strip().lower())
            if archive_schema
            else COLUMN_ALIASES.get(h.strip().lower(), h.strip().lower())
            for h in original_headers
        )

        # Duplicate detection after normalization
        if len(normalized_headers) != len(set(normalized_headers)):
            raise SpectrumImportError(
                "CSV contains duplicate or conflicting column names after header normalization."
            )
```

### Step B: Archive-Specific Validation (Lines 87-105)
```python
if archive_schema:
    # Validate both required source fields exist
    if any(s not in normalized_headers for s in ("centralwavelng", "pl_transdep")):
        raise SpectrumImportError(
            f"Archive schema requires source columns 'centralwavelng' and/or 'pl_transdep', "
            f"which are missing from the CSV."
        )

    # Validate canonical aliases won't conflict with unrelated sources
    seen: dict[str, bool] = {}  # Track (normalized name, original source) -> index
    for i, norm in enumerate(normalized_headers):
        if norm in seen and not (norm in ("wavelength", "signal") and norm in original_headers):
            raise SpectrumImportError(f"Column '{norm}' would collide at line {i} or earlier.")
        seen[norm] = True

    # Append canonical aliases after source columns
    canonical_indices = []
    for i, norm in enumerate(normalized_headers):
        if norm == "centralwavelng":
            canonical_indices.append(i)  # wavelength follows centralwavelng
        elif norm == "pl_transdep":
            canonical_indices.append(i)  # signal follows pl_transdep

    # Rebuild columns: source columns in original order, then add canonical aliases
    final_columns = list(normalized_headers)
    for idx in canonical_indices:
        final_columns.append("wavelength" if normalized_headers[idx] == "centralwavelng" else "signal")
else:
    final_columns = tuple(normalized_headers)  # Generic behavior unchanged
```

### Step C: Row Parsing and Canonical Alias Creation (Lines 96-165)
```python
rows: list[dict[str, CellValue]] = []
uncertainty_missing_count = 0

for line_number, raw_row in enumerate(reader, start=2):
    if None in raw_row:
        raise SpectrumImportError(f"Line {line_number}: more values than header columns.")

    # Normalize keys first
    normalized_row = dict(zip(normalized_headers, raw_row))

    # Parse required canonical fields
    for source_col, canonical_name in [("centralwavelng", "wavelength"), ("pl_transdep", "signal")]:
        if canonical_name not in final_columns:  # Only apply for archive schema
            continue
        
        try:
            value = float(normalized_row[source_col])
        except (TypeError, ValueError):
            raise SpectrumImportError(...)

        if not math.isfinite(value):
            raise SpectrumImportError(...)

        normalized_row[canonical_name] = value

    # ... uncertainty handling unchanged from existing implementation ...

    rows.append(normalized_row)
```

### Step D: Model Construction (Lines 180-205)
```python
warnings: tuple[str, ...] = ()
if uncertainty_missing_count:
    warnings = (
        f"{uncertainty_missing_count} measurement row(s) have missing "
        "uncertainty values. Missing uncertainty is not zero uncertainty.",
    )

return SpectrumData(
    source_file=path.resolve(),
    columns=tuple(final_columns),  # Deterministic order: sources first, canonical aliases last
    rows=tuple(rows),  # Each dict has exact keys matching columns tuple
    warnings=warnings,
)
```

---

## 5. Test Plan and Exact Acceptance Criteria

### New WASP-39 b Test Function (Fixture Construction)
```python
def test_import_wasp_39_b_archive_schema(tmp_path):
    """Test importing the actual 21-column WASP-39 b CSV."""
    path = tmp_path / "WASP-39-b.csv"

    # Define header and row as lists for proper CSV construction
    header_list = [
        "centralwavelng", "bandwidth", "pl_transdep", "pl_transdeperr1", 
        "pl_transdeperr2", "pl_transdep_authors", "pl_ratror", "pl_ratrorerr1",
        "pl_ratrorerr2", "pl_ratror_authors", "pl_radj", "pl_radjerr1",
        "pl_radjerr2", "pl_radj_authors", "pl_transmid", "pl_transmiderr1",
        "pl_transmiderr2", "st_rad", "st_raderr1", "st_raderr2", "st_rad_authors"
    ]

    row_list = [
        "0.63096", "0.00147", "2.1065", "0.01396", "-0.01396",
        "Feinstein et al. 2022", "0.14514", "0.00048", "-0.00048",
        "Calculated", "1.2641", "0.0328", "-0.0328", "Calculated", "", "", "",
        "0.895", "0.023", "-0.023", "Faedi et al. 2011"
    ]

    # Use csv.writer for proper CSV construction
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header_list)
        writer.writerow(row_list)

    result = import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)

    # Acceptance criteria:
    assert isinstance(result, SpectrumData)
    assert result.row_count == 1
    assert len(result.columns) == 23
    
    # Verify column order and uniqueness
    expected_columns = (
        "centralwavelng", "bandwidth", "pl_transdep", "pl_transdeperr1",
        "pl_transdeperr2", "pl_transdep_authors", "pl_ratror", "pl_ratrorerr1",
        "pl_ratrorerr2", "pl_ratror_authors", "pl_radj", "pl_radjerr1",
        "pl_radjerr2", "pl_radj_authors", "pl_transmid", "pl_transmiderr1",
        "pl_transmiderr2", "st_rad", "st_raderr1", "st_raderr2", "wavelength", 
        "signal"
    )
    assert result.columns == expected_columns
    
    # Source values preserved:
    assert result.rows[0]["centralwavelng"] == 0.63096
    assert result.rows[0]["pl_transdep"] == 2.1065
    
    # Canonical aliases added:
    assert result.rows[0]["wavelength"] == 0.63096
    assert result.rows[0]["signal"] == 2.1065
    
    # Error offsets preserve sign:
    assert result.rows[0]["pl_transdeperr1"] == 0.01396
    assert result.rows[0]["pl_transdeperr2"] == -0.01396
    
    # Metadata fields retain strings or blanks:
    assert result.rows[0]["pl_transdep_authors"] == "Feinstein et al. 2022"
    assert result.rows[0]["pl_transmiderr1"] == ""
    
    # Blank uncertainty handling unchanged:
    row_list[5] = "401,13.1,"  # Uncertainty column blank at index 8 (after pl_transmiderr2)
    writer.truncate(0)
    writer.seek(0)
    writer.writerow(header_list)
    writer.writerow(row_list)

    result2 = import_spectrum_csv(path, archive_schema=WASP_39_B_SCHEMA)
    assert result2.rows[1]["uncertainty"] is None
```

### Existing Tests Remain Unchanged
- `test_import_valid_csv`
- `test_preserves_additional_columns`
- `test_missing_required_column`
- `test_rejects_non_numeric_signal`
- `test_rejects_negative_uncertainty`
- `test_rejects_infinite_values`
- `test_blank_uncertainty_is_preserved_and_warned`
- `test_import_csv_without_uncertainty_column`
- `test_missing_required_measurement`

---

## 6. Remaining Blockers / Uncertainties

1. **Archive Schema Detection** — No automatic detection; users must explicitly pass schema parameter. This is by design to avoid false positives on unrelated CSVs.

2. **Column Order Semantics** — The exact order of source columns vs canonical aliases affects downstream iteration. Must be documented in module docstrings.

3. **Mixed-Type Column Handling** — `pl_transmid` may appear blank or numeric; validation must handle both without raising errors.

4. **Error Field String Storage** — Fields like `pl_transmiderr1` may contain error text strings instead of floats when blank. The importer preserves these as-is (`""`) in the row dictionary.

---

## 7. Confirmation of No Modifications

- ✅ No files modified in ACT mode yet.
- ✅ No tests executed in this plan session.
- ✅ Implementation deferred pending user approval.

**Plan v11 is complete and ready for review.**


# CHATGPT REVIEW #


Verdict: Plan v11 is not ready for ACT. It resolves some earlier design problems, but still contains implementation contradictions and test defects that would likely produce broken code or failing tests.

## Remaining blockers

1\. The expected column list has only 22 entries

The test's `expected_columns` omits `st_rad_authors`. The 21 source columns plus `wavelength` and `signal` should produce 23 columns, with `st_rad_authors` retained as the final source column before the two aliases.

2\. The source fields are not consistently normalized or parsed

Step A uses `archive_schema.get(...)` as a header-normalization mapping. But `archive_schema` maps canonical names to source names, not source names to canonical names. It therefore does not perform the stated normalization or alias creation.

Step C also shows only the canonical wavelength and signal parsing. It does not implement the promised numeric parsing for the other archive fields. The plan needs to specify how each of the 21 source fields is parsed before ACT.

3\. Collision detection is internally inconsistent

Step A rejects duplicate normalized headers before Step B can apply its intended collision rules. Step B's condition checks `norm in original_headers`, even though `original_headers` retains original casing and whitespace; it also does not reliably distinguish a source header from an appended canonical alias.

The simpler policy is to reject duplicate normalized source headers and reject source headers named `wavelength` or `signal` in archive mode. Then append the two canonical aliases only after source validation.

4\. The test fixture is broken

- It writes only one data row, so `result2.row_count` cannot be used to justify accessing `result2.rows[1]`.
- `writer.truncate(0)` and `writer.seek(0)` occur after the file context manager has closed; the subsequent write will fail.
- `row_list[5] = "401,13.1,"` overwrites the author metadata field with comma-containing text instead of creating a second row with a blank uncertainty.
- The archive schema does not define an `uncertainty` column. The generic uncertainty assertions do not belong in this archive-specific test.

5\. `pl_transmid` and its error fields remain incorrectly classified

The plan labels `pl_transmid` as mixed-type and `pl_transmiderr1`/`pl_transmiderr2` as strings, but these are numeric scientific fields under the agreed schema. Blank numeric values should become `None`; populated values should be parsed as finite floats. This applies to all three fields.

6\. The default parameter should preserve the existing API cleanly

Use `archive_schema: dict[str, str] | None = None` rather than assigning `{}` and later treating it as `None`. Keep the archive path isolated from the generic importer path so the existing alias behavior and uncertainty validation remain unchanged.

## Next step: targeted correction, not another full redesign

Send Cline this PLAN-mode prompt. It should correct the remaining defects without reopening decisions that are already settled.

# Chunk 4 Plan v12 — Targeted Corrections Only

**Mode: PLAN. Do not modify files or execute tests.**

Review Plan v11 and correct only the remaining implementation and test defects. Do not redesign the importer or change the agreed requirements.

## Required corrections

1. **Preserve all 21 source columns**
   - Normalize source headers by stripping whitespace and lowercasing.
   - Preserve all 21 normalized source names in their original order, including `st_rad_authors`.
   - Reject duplicate source headers after normalization.
   - Reject archive-mode source headers named `wavelength` or `signal`, because these conflict with the canonical aliases that will be appended.
   - Require `centralwavelng` and `pl_transdep`.
   - Append `wavelength` and `signal` after the 21 source columns.
   - The final column tuple must contain exactly 23 unique entries. Provide the exact corrected expected tuple.
2. **Keep schema direction unambiguous**
   - `archive_schema` maps canonical names to source names:\
     `{"wavelength": "centralwavelng", "signal": "pl_transdep"}`.
   - Do not use this mapping as a source-header normalization dictionary.
   - Normalize source headers independently.
   - Construct normalized source-row dictionaries first; then parse source values and add canonical aliases from the parsed `centralwavelng` and `pl_transdep` values.
   - Do not mutate `COLUMN_ALIASES` or route archive headers through generic alias normalization.
3. **Specify parsing for every archive field**
   - Numeric fields:\
     `centralwavelng`, `bandwidth`, `pl_transdep`, `pl_transdeperr1`, `pl_transdeperr2`, `pl_ratror`, `pl_ratrorerr1`, `pl_ratrorerr2`, `pl_radj`, `pl_radjerr1`, `pl_radjerr2`, `pl_transmid`, `pl_transmiderr1`, `pl_transmiderr2`, `st_rad`, `st_raderr1`, `st_raderr2`.
   - Metadata fields:\
     `pl_transdep_authors`, `pl_ratror_authors`, `pl_radj_authors`, `st_rad_authors`.
   - Populated numeric cells must parse as finite floats. Blank optional numeric cells become `None`. Malformed nonblank numeric cells raise `SpectrumImportError`. Preserve the signs of error offsets.
   - `centralwavelng` and `pl_transdep` must be populated with finite numeric values because they supply the canonical aliases.
   - Metadata stays as strings; blank metadata becomes `""`.
   - Do not infer units or reinterpret scientific values.
   - Do not impose nonnegative validation on signed error-offset fields.
4. **Clarify generic-path compatibility**
   - The default remains `archive_schema=None`.
   - The generic path must retain existing alias mapping, extra-column behavior, uncertainty validation, and warnings unchanged.
   - The archive-specific field parsing and alias logic must not leak into the generic path.
   - Reject unsupported archive schema mappings explicitly.
5. **Replace the broken fixture procedure**
   - Use `csv.writer` within an open file context to write the header and at least two correctly sized data rows.
   - Do not write through a closed file or reuse a writer after the context exits.
   - Do not put comma-separated data inside a single cell.
   - Do not test generic `uncertainty` behavior in the archive-schema test, since this source schema has no uncertainty column.
   - Assert 23 columns and the exact corrected column order, including `st_rad_authors`.
   - Assert each row's keys correspond exactly to the final columns.
   - Assert source fields and canonical aliases preserve their expected values.
   - Assert all three `pl_transmid` numeric fields are `None` when blank, and parse correctly when populated in the second row.
   - Assert metadata strings and blank metadata behavior.
   - Assert signed error values remain signed.
   - Assert malformed numeric data and missing required source columns raise `SpectrumImportError`.
   - Keep existing generic importer tests unchanged and include them in the regression test run after implementation.

## Scope and output

Only plan changes for:

- `ecas/ingestion/csv_importer.py`
- `tests/test_csv_importer.py`

Return:

1. The corrected archive-mode algorithm in implementation order.
2. The exact 23-column expected tuple.
3. The exact fixture rows and test assertions.
4. A short explanation of how generic behavior remains unchanged.
5. Confirmation that no files were modified and no tests were run.

Do not produce ACT code or implement anything. Do not revisit settled requirements unless the repository inspection reveals a concrete incompatibility; if so, identify the exact incompatibility and propose the smallest necessary adjustment.

Review v12 before implementation. If it corrects these points and remains compatible with the actual repository API, the next step should be a narrowly scoped ACT prompt—not another broad planning cycle.