
"""Import and validate spectrum data from CSV files."""

import csv
import math
from pathlib import Path

from ecas.models.spectrum import CellValue, SpectrumData


# ECAS uses these standard names internally after header normalization.
REQUIRED_COLUMNS = {"wavelength", "signal"}
OPTIONAL_COLUMNS = {"uncertainty"}

# Map recognized source-specific headers to ECAS's standard column names.
# Unrecognized headers are preserved using their cleaned lowercase names.
COLUMN_ALIASES = {
    "wavelength": "wavelength",
    "lambda": "wavelength",
    "signal": "signal",
    "intensity": "signal",
    "uncertainty": "uncertainty",
    "error": "uncertainty",
}


class SpectrumImportError(ValueError):
    """Raised when a spectrum file cannot be imported or validated."""


def import_spectrum_csv(file_path: str | Path) -> SpectrumData:
    """
    Import and validate a CSV spectrum into a SpectrumData object.

    Recognized aliases:
        lambda -> wavelength
        intensity -> signal
        error -> uncertainty

    Additional columns are preserved. Units and signal meaning remain
    unknown unless established separately.
    """
    path = Path(file_path)

    if not path.exists():
        raise SpectrumImportError(f"File does not exist: {path}")

    if not path.is_file():
        raise SpectrumImportError(f"Path is not a file: {path}")

    if path.suffix.lower() != ".csv":
        raise SpectrumImportError("Expected a .csv file.")

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                raise SpectrumImportError(
                    "CSV file is empty or has no header."
                )

            # Reject blank headers before attempting normalization.
            if any(
                header is None or not header.strip()
                for header in reader.fieldnames
            ):
                raise SpectrumImportError(
                    "CSV contains an empty column name."
                )

            # Clean headers, then translate recognized aliases to ECAS names.
            original_headers = reader.fieldnames
            columns = tuple(
                COLUMN_ALIASES.get(header.strip().lower(), header.strip().lower())
                for header in original_headers
            )

            # Two source headers must not silently collapse into one column.
            # For example, "lambda,wavelength" would be ambiguous.
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

                # Store all source values under the normalized column names.
                row = {
                    normalized: (
                        raw_row[original].strip()
                        if raw_row[original] is not None
                        else ""
                    )
                    for original, normalized in zip(original_headers, columns)
                }

                # Ignore fully blank rows.
                if all(value == "" for value in row.values()):
                    continue

                parsed: dict[str, CellValue] = dict(row)

                # Required wavelength and signal values must be finite numbers.
                for column in REQUIRED_COLUMNS:
                    try:
                        value = float(row[column])
                    except (TypeError, ValueError):
                        raise SpectrumImportError(
                            f"Line {line_number}: "
                            f"'{column}' must be numeric."
                        ) from None

                    if not math.isfinite(value):
                        raise SpectrumImportError(
                            f"Line {line_number}: "
                            f"'{column}' must be finite."
                        )

                    parsed[column] = value

                # Blank uncertainty values remain None, not zero.
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

                        if (
                            not math.isfinite(uncertainty)
                            or uncertainty < 0
                        ):
                            raise SpectrumImportError(
                                f"Line {line_number}: "
                                "'uncertainty' must be finite "
                                "and non-negative."
                            )

                        parsed["uncertainty"] = uncertainty

                rows.append(parsed)

    except UnicodeDecodeError as exc:
        raise SpectrumImportError(
            "CSV must be text encoded as UTF-8 or UTF-8 with BOM."
        ) from exc
    except OSError as exc:
        raise SpectrumImportError(
            f"Could not read file: {exc}"
        ) from exc

    if not rows:
        raise SpectrumImportError(
            "CSV contains no spectrum data rows."
        )

    # Summarize blank uncertainty cells without treating them as zero.
    warnings = ()
    if missing_uncertainty_count:
        warnings = (
            f"{missing_uncertainty_count} measurement row(s) have missing "
            "uncertainty values. Missing uncertainty is not zero uncertainty.",
        )

    # Report recognized aliases so the user can see how source headers
    # were interpreted. Do not infer physical units from column names.
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
        source_file=path.resolve(),
        columns=columns,
        rows=tuple(rows),
        warnings=warnings,
    )
