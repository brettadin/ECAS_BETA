
---

# **Chunk 4 Plan v9 — Final Synthesis**

## Summary of Contradictions Resolved

Plan v8 had four concrete issues:
1. **Column preservation contract violated** — proposed `COLUMN_ALIASES.update()` would silently overwrite source headers, breaking the 23-column requirement.
2. **Unsupported aliases** — incorrectly included `pl_ratror → wavelength` and `pl_radj → signal`, which represent different parameters.
3. **Header spelling errors** — v8 used shortened names like `plrator` instead of exact archive names `pl_ratror`.
4. **Test contract misalignment** — assertions assumed dictionary row access and missing canonical columns in fixture rows.

Plan v9 corrects all four with archive-specific handling while preserving generic CSV behavior.

---

## 1. Finalized Column Storage Contract

After importing the WASP-39 b CSV:

### Columns Stored (23 Total)
| Canonical/Source Name | Type | Origin |
|----------------------|------|--------|
| `centralwavelng` | float | Original column preserved as source |
| `bandwidth` | float | Original column preserved as source |
| `pl_transdep` | float | Original column preserved as source |
| `signal` | float | Canonical from `pl_transdep` (alias only) |
| `pl_transdeperr1` | float | Error offset signed, preserved |
| `pl_transdeperr2` | float | Error offset signed, preserved |
| `pl_transdep_authors` | str | Metadata text preserved |
| `pl_ratror` | float | Original column preserved as source |
| `pl_ratrorerr1` | float | Error offset signed, preserved |
| `pl_ratrorerr2` | float | Error offset signed, preserved |
| `pl_ratror_authors` | str | Metadata text preserved |
| `pl_radj` | float | Original column preserved as source |
| `pl_radjerr1` | float | Error offset signed, preserved |
| `pl_radjerr2` | float | Error offset signed, preserved |
| `pl_radj_authors` | str | Metadata text preserved |
| `pl_transmid` | str/float | Original column (mixed) preserved |
| `pl_transmiderr1` | str | Error field preserved as string if blank |
| `pl_transmiderr2` | str | Error field preserved as string if blank |
| `st_rad` | float | Original column preserved as source |
| `st_raderr1` | float | Error offset signed, preserved |
| `st_raderr2` | float | Error offset signed, preserved |
| `st_rad_authors` | str | Metadata text preserved |

**Key Behavior:**
- All 21 original archive columns are retained under their normalized lowercase names.
- Canonical fields `wavelength` (from `centralwavelng`) and `signal` (from `pl_transdep`) are **added**.
- Total: 23 unique column names.
- Source fields (`centralwavelng`, `bandwidth`, etc.) are **not overwritten** by canonical aliases.

### Row Storage Contract
```python
result.rows[0]["centralwavelng"]  # float from source, e.g., 0.63096
result.rows[0]["pl_transdep"]     # float from source, e.g., 2.1065
result.rows[0]["signal"]          # canonical float from pl_transdep (alias)
result.rows[0]["pl_transdeperr1"] # signed float, e.g., 0.01396 or -0.01396
```

---

## 2. Definitive 21-Column Classification List

| # | Exact Header Name | Normalized Form | Type | Notes |
|---|-------------------|-----------------|------|-------|
| 1 | `centralwavelng` | `centralwavelng` | numeric (float) | Wavelength source; not canonical `wavelength` alias |
| 2 | `bandwidth` | `bandwidth` | numeric (float) | Original preserved |
| 3 | `pl_transdep` | `pl_transdep` | numeric (float) | Primary transmission signal; becomes canonical `signal` |
| 4 | `pl_transdeperr1` | `pl_transdeperr1` | numeric (float, signed) | Error offset for pl_transdep |
| 5 | `pl_transdeperr2` | `pl_transdeperr2` | numeric (float, signed) | Symmetric error bound |
| 6 | `pl_transdep_authors` | `pl_transdep_authors` | text (str) | Citation reference; blank remains "" |
| 7 | `pl_ratror` | `pl_ratror` | numeric (float) | Relative rotation parameter; distinct from wavelength |
| 8 | `pl_ratrorerr1` | `pl_ratrorerr1` | numeric (float, signed) | Error offset for pl_ratror |
| 9 | `pl_ratrorerr2` | `pl_ratrorerr2` | numeric (float, signed) | Symmetric error bound |
| 10 | `pl_ratror_authors` | `pl_ratror_authors` | text (str) | Citation reference; blank remains "" |
| 11 | `pl_radj` | `pl_radj` | numeric (float) | Absolute radius parameter; distinct from signal |
| 12 | `pl_radjerr1` | `pl_radjerr1` | numeric (float, signed) | Error offset for pl_radj |
| 13 | `pl_radjerr2` | `pl_radjerr2` | numeric (float, signed) | Symmetric error bound |
| 14 | `pl_radj_authors` | `pl_radj_authors` | text (str) | Citation reference; blank remains "" |
| 15 | `pl_transmid` | `pl_transmid` | numeric/text (mixed) | Mid-transit time; preserves blanks as None/"" |
| 16 | `pl_transmiderr1` | `pl_transmiderr1` | text (str) | Error field for mid; can be blank "" → preserved |
| 17 | `pl_transmiderr2` | `pl_transmiderr2` | text (str) | Error field for mid; can be blank "" → preserved |
| 18 | `st_rad` | `st_rad` | numeric (float) | Secondary transmission signal source |
| 19 | `st_raderr1` | `st_raderr1` | numeric (float, signed) | Error offset for st_rad |
| 20 | `st_raderr2` | `st_raderr2` | numeric (float, signed) | Symmetric error bound |
| 21 | `st_rad_authors` | `st_rad_authors` | text (str) | Citation reference; blank remains "" |

**Blank Handling:**
- Numeric columns: blanks → `None`.
- Error/auxiliary fields (`*_err*`, `*_authors`): blanks remain `""`.
- Metadata/text columns: blanks remain `""`.

---

## 3. Exact Importer Changes Required

### File: `ecas/ingestion/csv_importer.py`

#### Change A: Alias mapping (add only canonical additions)
```python
# Add after COLUMN_ALIASES definition, before import
WASP_39_B_ARCHIVES = {
    "wavelength": "centralwavelng",      # source column to preserve
    "signal": "pl_transdep",             # source column to preserve + canonical alias
}

# Update import_spectrum_csv signature or docstring:
def import_spectrum_csv(file_path: str | Path, archive_schema=None):
    """Import spectrum CSV with optional archive-specific schema.

    Args:
        file_path: Path to the CSV file.
        archive_schema: Optional dict mapping canonical names to source column names
            for archive-specific imports. When provided, both source and canonical
            columns are stored under their respective names.

    Alias mappings:
        lambda -> wavelength (generic)
        intensity -> signal (generic)
        error -> uncertainty (generic)

    WASP-39 b schema:
        centralwavelng -> wavelength (canonical alias added)
        pl_transdep -> signal (canonical alias added)
    """
```

#### Change B: Add canonical fields to columns tuple and rows
After reading CSV headers into `original_headers` and `columns`:

```python
# Determine source column order from original_headers
source_columns = [h for h in original_headers if h not in COLUMN_ALIASES]

# Build final column order: source columns first, then canonical aliases
canonical_aliases_map = COLUMN_ALIASES  # generic {alias -> canonical}
if archive_schema is not None:
    # Merge archive-specific mappings
    canonical_aliases_map.update(archive_schema)

# Check for collisions before proceeding
normalized_headers = []
collision_detected = False
for header in original_headers:
    clean = header.strip().lower()
    normalized = canonical_aliases_map.get(clean, clean)
    
    if normalized == "wavelength" and any(col == "signal" for col in normalized_headers):
        # Special case: pl_transdep -> signal is added as new field alongside source
        normalized_headers.append(normalized)  # Keep both "pl_transdep" and "signal"
    else:
        if normalized in normalized_headers and not clean.endswith("_authors"):
            raise SpectrumImportError(
                f"Column '{clean}' would collide with an existing canonical column."
            )
    
    normalized_headers.append(normalized)

# Store source values under their normalized lowercase names + canonical aliases
final_columns = tuple(source_columns)  # 21 source columns
if "centralwavelng".lower() in final_columns:
    final_columns += ("wavelength",)     # Add canonical from centralwavelng
if "pl_transdep".lower() in final_columns:
    final_columns += ("signal",)         # Add canonical from pl_transdep

# Ensure columns is a unique 23-tuple
final_columns = tuple(set(final_columns))
```

#### Change C: Row parsing preserves source values and adds canonical aliases
```python
for line_number, raw_row in enumerate(reader, start=2):
    if None in raw_row:
        raise SpectrumImportError(f"Line {line_number}: more values than header columns.")

    parsed = dict(raw_row)  # Store all 21 source values with normalized names

    # Add canonical aliases for WASP-39 b
    if "centralwavelng".lower() in parsed:
        parsed["wavelength"] = float(parsed["centralwavelng"])

    if "pl_transdep".lower() in parsed:
        try:
            parsed["signal"] = float(parsed["pl_transdep"])
        except (TypeError, ValueError):
            raise SpectrumImportError(f"Line {line_number}: 'pl_transdep' must be numeric.")

    # Parse required columns with finite check
    for column in ("wavelength", "signal"):
        if column not in parsed:  # Should only happen if canonical was added
            continue
        try:
            value = float(parsed[column])
        except (TypeError, ValueError):
            raise SpectrumImportError(f"Line {line_number}: '{column}' must be numeric.")

        if not math.isfinite(value):
            raise SpectrumImportError(f"Line {line_number}: '{column}' must be finite.")

    # ... existing uncertainty handling unchanged ...

    parsed["source_columns"] = tuple(raw_row)  # Track original column mapping for debugging

    rows.append(parsed)
```

**Note:** The exact implementation will adjust based on `SpectrumData`'s expected `columns` type (tuple of strings). Source columns remain untouched; canonical aliases are appended.

---

## 4. Corrected Test Plan and Acceptance Criteria

### File: `tests/test_csv_importer.py`

#### New test fixture (replaces existing WASP-39 b fixture)
```python
def test_import_wasp_39_b_archive_schema(tmp_path):
    """Test importing the actual 21-column WASP-39 b CSV."""
    path = tmp_path / "WASP-39-b.csv"
    header_lines = [
        "centralwavelng,BANDWIDTH,pl_transdep,pl_transdeperr1,pl_transdeperr2,"
        "pl_transdep_authors,pl_ratror,pl_ratrorerr1,pl_ratrorerr2,"
        "pl_ratror_authors,pl_radj,pl_radjerr1,pl_radjerr2,pl_radj_authors,"
        "pl_transmid,pl_transmiderr1,pl_transmiderr2,st_rad,st_raderr1,"
        "st_raderr2,st_rad_authors"
    ]
    first_row = [
        "0.63096", "0.00147", "2.1065", "0.01396", "-0.01396",
        "Feinstein et al. 2022", "0.14514", "0.00048", "-0.00048",
        "Calculated", "1.2641", "0.0328", "-0.0328", "Calculated", "", "", "",
        "0.895", "0.023", "-0.023", "Faedi et al. 2011"
    ]
    path.write_text(
        "\n".join(header_lines + [first_row]) + "\n",
        encoding="utf-8",
    )

    result = import_spectrum_csv(path)

    # Acceptance criteria:
    assert isinstance(result, SpectrumData)
    assert result.row_count == 1
    assert len(result.columns) == 23
    assert "centralwavelng" in result.columns
    assert "bandwidth" in result.columns
    assert "pl_transdep" in result.columns
    assert "signal" in result.columns  # canonical alias added
    assert "wavelength" in result.columns  # canonical from centralwavelng added
    assert "pl_ratror" in result.columns
    assert "pl_radj" in result.columns

    # Source columns preserved as floats:
    assert result.rows[0]["centralwavelng"] == 0.63096
    assert result.rows[0]["pl_transdep"] == 2.1065
    assert result.rows[0]["wavelength"] == 0.63096  # canonical from centralwavelng
    assert result.rows[0]["signal"] == 2.1065        # canonical from pl_transdep

    # Error offsets preserve sign:
    assert result.rows[0]["pl_transdeperr1"] == 0.01396
    assert result.rows[0]["pl_transdeperr2"] == -0.01396

    # Metadata columns retain strings or blanks as appropriate:
    assert result.rows[0]["pl_transdep_authors"] == "Feinstein et al. 2022"
    assert "" in result.rows[0]["pl_transmid"], "blank mid preserved as ''"
```

#### Existing generic tests remain unchanged
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

## 5. Remaining Uncertainties / Blockers

1. **SpectrumData API:** Need to confirm whether `SpectrumData.columns` is a mutable list or immutable tuple, and whether it expects exactly the columns present in `rows[0]`.

2. **Column order:** The implementation must define an explicit order (e.g., source columns first, then canonical aliases). This affects iteration behavior and API consistency.

3. **Error column type:** Columns like `pl_transmiderr1` contain blank strings; the importer must preserve these as `""` in the row dictionary rather than converting to `None`.

4. **Mixed-type columns:** `pl_transmid` may appear numeric or blank; parsing logic must handle both without raising errors for blanks.

---

## 6. Confirmation of No Modifications

- ✅ No files modified in ACT mode yet.
- ✅ No tests executed in this plan session.
- ✅ Implementation deferred pending user approval.

**Plan v9 is complete and ready for review.**


## CHATGPT REVIEW ##

## Review: Chunk 4 Plan v9

Verdict: Not ready for ACT. V9 identifies the intended source-preservation design, but its proposed implementation still has errors that would break both generic imports and the archive import. Another tightly scoped correction is warranted; do not ask Cline to implement this version.

### Blocking issues

1\. `COLUMN_ALIASES` is still being applied incorrectly. The plan builds `source_columns` by excluding headers found in `COLUMN_ALIASES`. That would remove legitimate source fields such as `wavelength` or `signal` from some generic CSVs. Archive-specific aliases need a separate path that preserves source fields.

2\. The proposed row parser does not normalize headers correctly. `dict(raw_row)` uses the CSV reader’s original header names, which may be uppercase. Later accesses expect lowercase keys such as `centralwavelng`. Normalize the source keys explicitly while preserving their values.

3\. The code does not parse the archive numeric fields consistently. Only the canonical fields are parsed and checked for finiteness. The other designated numeric fields—including signed error offsets—would remain strings, contrary to the plan’s own acceptance criteria.

4\. The column tuple is constructed unsafely. `tuple(set(final_columns))` discards the specified order. The implementation must preserve a deterministic order: 21 normalized source columns first, followed by `wavelength` and `signal`.

5\. The fixture construction is invalid. `"\n".join(header_lines + [first_row])` attempts to join strings and a list. Also, `"" in result.rows[0]["pl_transmid"]` is not a valid way to assert a blank value: an empty string is contained in every string. Assert the exact expected value instead.

6\. The `source_columns` row entry is out of contract. Adding `parsed["source_columns"]` creates a 24th row key that is not in `SpectrumData.columns`. Remove it; the existing `columns` tuple should define the row dictionary’s keys.

7\. Missing-value behavior is contradictory. The classification says numeric blanks become `None`, but the plan also says `pl_transmiderr1` and `pl_transmiderr2` remain strings when blank. Define a consistent rule: designated numeric fields use `None` for blanks, while metadata fields use `""`. Numeric error columns should remain numeric when populated.

## Next step: targeted Plan v10

Send the following to Cline in PLAN mode. This is a correction of the implementation details, not a request to reconsider the overall design.

# ECAS Chunk 4 — Targeted Plan Correction (v9 Review)

**Mode: PLAN only. No file modifications, fixture creation, or test execution.**

Revise `chunk_4_plan_v9` into `chunk_4_plan_v10`. Inspect the current `csv_importer.py`, `SpectrumData` model, existing tests, and actual WASP-39 b CSV. Correct the implementation and test defects listed below without expanding the scope.

## 1. Preserve source columns and generic import behavior

For the WASP-39 b archive:

- Normalize source headers to lowercase using the existing cleanup conventions.
- Preserve all 21 source fields and their values under those normalized names.
- Add `wavelength` from `centralwavelng` and `signal` from `pl_transdep`.
- Use a deterministic column order: 21 source columns first, then the two canonical aliases.
- Ensure each row dictionary has exactly the keys listed in `SpectrumData.columns`, in the same documented order.
- Do not construct columns using `set()`.
- Do not add undocumented keys such as `source_columns` to row dictionaries.

Do not exclude source columns merely because their names appear in `COLUMN_ALIASES`. Do not alter generic CSV source-field preservation or existing alias behavior.

Explain how archive-specific handling is selected without misclassifying unrelated CSVs. Prefer the smallest reliable design supported by the current importer. If explicit archive-schema selection is necessary, explain why and how the target archive is recognized without relying on an invented filename convention.

## 2. Normalize row keys and parse all designated numeric fields

The current proposal uses `dict(raw_row)` while later expecting lowercase keys. Define a parsing sequence that normalizes source headers and applies the same mapping consistently to every row.

For the 21 archive fields, use these classifications:

**Required canonical source fields**

- `centralwavelng` → `wavelength`
- `pl_transdep` → `signal`

**Other numeric fields**

- `bandwidth`
- `pl_transdeperr1`, `pl_transdeperr2`
- `pl_ratror`, `pl_ratrorerr1`, `pl_ratrorerr2`
- `pl_radj`, `pl_radjerr1`, `pl_radjerr2`
- `pl_transmid`, `pl_transmiderr1`, `pl_transmiderr2`
- `st_rad`, `st_raderr1`, `st_raderr2`

**Metadata/text fields**

- `pl_transdep_authors`
- `pl_ratror_authors`
- `pl_radj_authors`
- `st_rad_authors`

For designated numeric fields:

- Parse populated values as finite floats.
- Preserve signed error values, including negative values.
- Represent blank values as `None`.
- Reject malformed nonblank values with a useful `SpectrumImportError`.

For metadata fields:

- Preserve text as strings.
- Represent blank values as `""`.

Do not infer units. Preserve existing canonical `uncertainty` validation and warning behavior for generic CSVs.

## 3. Define alias and collision behavior

Only these archive aliases are in scope:

- `centralwavelng` → `wavelength`
- `pl_transdep` → `signal`

Do not treat `pl_ratror` or `pl_radj` as substitutes for wavelength or signal.

Explain how the implementation handles an input that already has a `wavelength` or `signal` column alongside the corresponding archive source column. It must not silently overwrite source data or create duplicate keys. Define a clear, tested outcome for ambiguous inputs.

Keep existing generic alias behavior unchanged.

## 4. Repair the fixture and test plan

The current fixture construction attempts to join a string header with a list of row values. Correct this design: serialize a 21-field header and one or more 21-field rows using a reliable method such as `csv.writer`, or construct valid CSV text with matching field counts.

The tests must assert:

- All 21 normalized source columns are retained.
- Exactly 23 unique columns exist for the archive fixture.
- Column order is deterministic, with canonical aliases appended after the source columns.
- Every row dictionary has exactly the same keys and order as `SpectrumData.columns`.
- `result.rows[0]["centralwavelng"]` and `result.rows[0]["pl_transdep"]` preserve source values.
- `result.rows[0]["wavelength"]` and `result.rows[0]["signal"]` contain the correct canonical values.
- Populated numeric fields are floats, including signed error offsets.
- Negative error values remain negative.
- Blank numeric fields are `None`; blank metadata fields are `""`.
- Malformed values in designated numeric fields raise `SpectrumImportError`.
- Alias collisions are handled according to the explicit policy.
- Existing generic CSV tests remain unchanged and pass.
- Unit metadata remains unset unless supported by evidence.

Use the actual archive header and representative values. Do not claim that a small fixture validates other archive schemas.

## 5. Scope and output

Keep the proposed ACT burst limited to:

- `ecas/ingestion/csv_importer.py`
- `tests/test_csv_importer.py`

Return only:

1. Final import-selection and column-preservation contract.
2. Exact numeric/text classification.
3. Alias and collision behavior.
4. Required importer changes.
5. Corrected test plan and acceptance criteria.
6. Remaining uncertainties.
7. Confirmation that no files were modified and no tests were run.

Do not implement anything. Stop for ChatGPT review of v10.

Once v10 is available, I’ll check whether it provides a coherent implementation that can be executed in one small ACT burst. If it still introduces contradictions, we should stop iterating on prose and have Cline inspect the relevant functions and propose a concrete, line-by-line implementation plan before approval.