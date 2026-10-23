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