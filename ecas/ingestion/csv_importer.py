
"""Import and validate spectrum data from CSV files."""

import csv
import math
from pathlib import Path

from ecas.models.spectrum import CellValue, SpectrumData


# Generic CSV importer configuration.
REQUIRED_COLUMNS = {"wavelength", "signal"}
OPTIONAL_COLUMNS = {"uncertainty"}

COLUMN_ALIASES = {
    "wavelength": "wavelength",
    "lambda": "wavelength",
    "signal": "signal",
    "intensity": "signal",
    "uncertainty": "uncertainty",
    "error": "uncertainty",
}


# Supported archive schema. Keys are ECAS canonical names; values
# are the corresponding source column names from CSV.
WASP39B_SCHEMA = {
    "wavelength": "centralwavelng",
    "signal": "pl_trandep",
}

EXPECTED_ARCHIVE_SOURCES = (
    "centralwavelng",
    "bandwidth",
    "pl_trandep",
    "pl_trandeperr1",
    "pl_trandeperr2",
    "pl_trandep_authors",
    "pl_ratror",
    "pl_ratrorerr1",
    "pl_ratrorerr2",
    "pl_ratror_authors",
    "pl_radj",
    "pl_radjerr1",
    "pl_radjerr2",
    "pl_radj_authors",
    "pl_tranmid",
    "pl_tranmiderr1",
    "pl_tranmiderr2",
    "st_rad",
    "st_raderr1",
    "st_raderr2",
    "st_rad_authors",
)

REQUIRED_ARCHIVE_NUMERIC_FIELDS = {
    "centralwavelng",
    "pl_trandep",
}

OPTIONAL_ARCHIVE_NUMERIC_FIELDS = {
    "bandwidth",
    "pl_trandeperr1",
    "pl_trandeperr2",
    "pl_ratror",
    "pl_ratrorerr1",
    "pl_ratrorerr2",
    "pl_radj",
    "pl_radjerr1",
    "pl_radjerr2",
    "pl_tranmid",
    "pl_tranmiderr1",
    "pl_tranmiderr2",
    "st_rad",
    "st_raderr1",
    "st_raderr2",
}

ARCHIVE_METADATA_FIELDS = {
    "pl_trandep_authors",
    "pl_ratror_authors",
    "pl_radj_authors",
    "st_rad_authors",
}


class SpectrumImportError(ValueError):
    """Raised when a spectrum file cannot be imported or validated."""


def _validate_file(file_path: str | Path) -> Path:
    """Validate the input path and return its resolved form."""
    path = Path(file_path)

    if not path.exists():
        raise SpectrumImportError(f"File does not exist: {path}")

    if not path.is_file():
        raise SpectrumImportError(f"Path is not a file: {path}")

    if path.suffix.lower() != ".csv":
        raise SpectrumImportError("Expected a .csv file.")

    return path.resolve()


def _read_csv_headers(reader: csv.DictReader) -> tuple[str, ...]:
    """Validate raw headers and return normalized lowercase names."""
    if not reader.fieldnames:
        raise SpectrumImportError("CSV file is empty or has no header.")

    raw_headers = list(reader.fieldnames)

    if any(header is None or not header.strip() for header in raw_headers):
        raise SpectrumImportError("CSV contains an empty column name.")

    normalized = tuple(header.strip().lower() for header in raw_headers)

    if len(normalized) != len(set(normalized)):
        raise SpectrumImportError(
            "CSV contains duplicate column names after header normalization."
        )

    return normalized


def _parse_finite_float(
    raw_value: str | None,
    *,
    field_name: str,
    line_number: int,
    required: bool,
) -> float | None:
    """Parse a finite numeric value, allowing blanks only for optional fields."""
    if raw_value is None:
        if required:
            raise SpectrumImportError(
                f"Line {line_number}: required field '{field_name}' is missing."
            )
        return None

    stripped = raw_value.strip()

    if not stripped:
        if required:
            raise SpectrumImportError(
                f"Line {line_number}: required field '{field_name}' is blank."
            )
        return None

    try:
        value = float(stripped)
    except ValueError:
        raise SpectrumImportError(
            f"Line {line_number}: field '{field_name}' must be numeric."
        ) from None

    if not math.isfinite(value):
        raise SpectrumImportError(
            f"Line {line_number}: field '{field_name}' must be finite."
        )

    return value


def import_spectrum_csv(
    file_path: str | Path,
    archive_schema: dict[str, str] | None = None,
) -> SpectrumData:
    """
    Import a generic spectrum CSV or a supported archive CSV.

    With archive_schema=None, the existing generic CSV behavior is used.

    The supported WASP-39 b mapping is:
        wavelength <- centralwavelng
        signal     <- pl_transdep

    Archive source columns are retained in their original order.
    Canonical wavelength and signal columns are appended afterward.
    """
    path = _validate_file(file_path)

    if archive_schema is None:
        return _import_generic_csv(path)

    if archive_schema != WASP39B_SCHEMA:
        raise SpectrumImportError("Unsupported archive schema.")

    return _import_archive_csv(path, archive_schema)


def _import_archive_csv(
    file_path: Path,
    schema: dict[str, str],
) -> SpectrumData:
    """Import and validate the supported WASP-39 b archive CSV."""
    if schema != WASP39B_SCHEMA:
        raise SpectrumImportError("Unsupported archive schema.")

    try:
        with file_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            normalized_headers = _read_csv_headers(reader)

            if len(normalized_headers) != len(EXPECTED_ARCHIVE_SOURCES):
                raise SpectrumImportError(
                    "WASP-39 b archive requires exactly 21 source columns; "
                    f"found {len(normalized_headers)}."
                )

            expected_set = set(EXPECTED_ARCHIVE_SOURCES)
            actual_set = set(normalized_headers)

            if actual_set != expected_set:
                missing = sorted(expected_set - actual_set)
                extra = sorted(actual_set - expected_set)

                details = []
                if missing:
                    details.append(f"Missing columns: {missing}")
                if extra:
                    details.append(f"Unexpected columns: {extra}")

                raise SpectrumImportError(
                    "WASP-39 b archive CSV has unsupported headers. "
                    + " ".join(details)
                )

            # DictReader uses the original header names as dictionary keys.
            # Build a mapping only after raw header validation.
            raw_headers = list(reader.fieldnames or [])
            normalized_to_raw = {
                normalized: raw
                for raw, normalized in zip(raw_headers, normalized_headers)
            }

            source_columns = list(normalized_headers)
            canonical_columns = list(schema.keys())
            # Build a mapping from schema keys to their original column names, then create unified output columns
            source_to_canonical = {v: k for k, v in WASP39B_SCHEMA.items()}
            output_columns = ("wavelength",) + tuple(normalized_headers) + ("signal",)


            parsed_rows: list[dict[str, CellValue]] = []

            for line_number, raw_row in enumerate(reader, start=2):
                # DictReader stores surplus fields under the None key.
                if None in raw_row:
                    raise SpectrumImportError(
                        f"Line {line_number}: more values than header columns."
                    )

                # Missing cells are also malformed rows, including missing
                # optional values. An explicitly empty CSV cell is allowed
                # where the field's validation rules permit it.
                if any(
                    raw_row.get(raw_header) is None
                    for raw_header in raw_headers
                ):
                    raise SpectrumImportError(
                        f"Line {line_number}: fewer values than header columns."
                    )

                source_values: dict[str, CellValue] = {}

                # Parse every original field without changing source order.
                for field_name in source_columns:
                    raw_value = raw_row[normalized_to_raw[field_name]]

                    if field_name in REQUIRED_ARCHIVE_NUMERIC_FIELDS:
                        value = _parse_finite_float(
                            raw_value,
                            field_name=field_name,
                            line_number=line_number,
                            required=True,
                        )
                    elif field_name in OPTIONAL_ARCHIVE_NUMERIC_FIELDS:
                        value = _parse_finite_float(
                            raw_value,
                            field_name=field_name,
                            line_number=line_number,
                            required=False,
                        )
                    elif field_name in ARCHIVE_METADATA_FIELDS:
                        value = (raw_value or "").strip()
                    else:
                        # This should be unreachable after exact header
                        # validation, but protects against future schema edits.
                        raise SpectrumImportError(
                            f"Unsupported archive field: {field_name}"
                        )

                    source_values[field_name] = value

                # Retain all source columns and append canonical aliases.
                parsed_row: dict[str, CellValue] = dict(source_values)

                for canonical_name, source_name in schema.items():
                    parsed_row[canonical_name] = source_values[source_name]

                parsed_rows.append(parsed_row)

    except UnicodeDecodeError as exc:
        raise SpectrumImportError(
            "CSV must be text encoded as UTF-8 or UTF-8 with BOM."
        ) from exc
    except OSError as exc:
        raise SpectrumImportError(f"Could not read file: {exc}") from exc

    if not parsed_rows:
        raise SpectrumImportError(
            "WASP-39 b archive CSV contains no spectrum data rows."
        )

    return SpectrumData(
        source_file=file_path.resolve(),
        columns=output_columns,
        rows=tuple(parsed_rows),
    )


def _import_generic_csv(file_path: Path) -> SpectrumData:
    """Import a generic spectrum CSV using the existing ECAS conventions."""
    path = file_path.resolve()

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            original_headers = list(reader.fieldnames or [])

            if not original_headers:
                raise SpectrumImportError(
                    "CSV file is empty or has no header."
                )

            if any(
                header is None or not header.strip()
                for header in original_headers
            ):
                raise SpectrumImportError(
                    "CSV contains an empty column name."
                )

            columns = tuple(
                COLUMN_ALIASES.get(
                    header.strip().lower(),
                    header.strip().lower(),
                )
                for header in original_headers
            )

            if len(columns) != len(set(columns)):
                raise SpectrumImportError(
                    "CSV contains duplicate or conflicting column names "
                    "after header normalization."
                )

            missing = REQUIRED_COLUMNS - set(columns)
            if missing:
                raise SpectrumImportError(
                    "Missing required columns: " + ", ".join(sorted(missing))
                )

            rows: list[dict[str, CellValue]] = []
            missing_uncertainty_count = 0

            for line_number, raw_row in enumerate(reader, start=2):
                if None in raw_row:
                    raise SpectrumImportError(
                        f"Line {line_number}: more values than header columns."
                    )

                row: dict[str, str] = {}

                for original, normalized in zip(original_headers, columns):
                    value = raw_row.get(original)
                    row[normalized] = value.strip() if value is not None else ""

                # Ignore fully blank rows, matching previous generic behavior.
                if all(value == "" for value in row.values()):
                    continue

                parsed: dict[str, CellValue] = dict(row)

                for column in REQUIRED_COLUMNS:
                    try:
                        value = float(row[column])
                    except (TypeError, ValueError):
                        raise SpectrumImportError(
                            f"Line {line_number}: '{column}' must be numeric."
                        ) from None

                    if not math.isfinite(value):
                        raise SpectrumImportError(
                            f"Line {line_number}: '{column}' must be finite."
                        )

                    parsed[column] = value

                if "uncertainty" in columns:
                    uncertainty_text = row["uncertainty"]

                    if uncertainty_text == "":
                        parsed["uncertainty"] = None
                        missing_uncertainty_count += 1
                    else:
                        try:
                            uncertainty = float(uncertainty_text)
                        except (TypeError, ValueError):
                            raise SpectrumImportError(
                                f"Line {line_number}: "
                                "'uncertainty' must be numeric or blank."
                            ) from None

                        if not math.isfinite(uncertainty) or uncertainty < 0:
                            raise SpectrumImportError(
                                f"Line {line_number}: "
                                "'uncertainty' must be finite and non-negative."
                            )

                        parsed["uncertainty"] = uncertainty

                rows.append(parsed)

    except UnicodeDecodeError as exc:
        raise SpectrumImportError(
            "CSV must be text encoded as UTF-8 or UTF-8 with BOM."
        ) from exc
    except OSError as exc:
        raise SpectrumImportError(f"Could not read file: {exc}") from exc

    if not rows:
        raise SpectrumImportError("CSV contains no spectrum data rows.")

    warnings: tuple[str, ...] = ()

    if missing_uncertainty_count:
        warnings += (
            f"{missing_uncertainty_count} measurement row(s) have missing "
            "uncertainty values. Missing uncertainty is not zero uncertainty.",
        )

    applied_aliases = [
        f"{original} -> {normalized}"
        for original, normalized in zip(original_headers, columns)
        if original.strip().lower() != normalized
    ]

    if applied_aliases:
        warnings += (
            "Recognized CSV header aliases: " + ", ".join(applied_aliases) + ".",
        )

    return SpectrumData(
        source_file=path,
        columns=columns,
        rows=tuple(rows),
        warnings=warnings,
    )
