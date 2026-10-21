
"""Import and validate spectrum data from CSV files."""

import csv
import math
from pathlib import Path

from ecas.models.spectrum import CellValue, SpectrumData


REQUIRED_COLUMNS = {"wavelength", "signal"}
OPTIONAL_COLUMNS = {"uncertainty"}


class SpectrumImportError(ValueError):
    """Raised when a spectrum file cannot be imported or validated."""


def import_spectrum_csv(file_path: str | Path) -> SpectrumData:
    """
    Import a CSV spectrum and return a structured SpectrumData object.

    Required columns:
        wavelength: finite numeric spectral coordinates
        signal: finite numeric signal values

    Optional column:
        uncertainty: finite, non-negative numeric values when present.
        Blank uncertainty cells are preserved as None and reported as a warning.

    Additional columns are preserved as text. Units and signal meaning
    remain unknown unless established separately.
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

            # Normalize headers consistently while preserving their order.
            if any(
                header is None or not header.strip()
                for header in reader.fieldnames
            ):
                raise SpectrumImportError(
                    "CSV contains an empty column name."
                )

            columns = tuple(
                header.strip().lower() for header in reader.fieldnames
            )

            if len(columns) != len(set(columns)):
                raise SpectrumImportError(
                    "CSV contains duplicate column names."
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

                # Preserve every CSV column; validate scientific fields below.
                row = {
                    column: (
                        raw_row[original].strip()
                        if raw_row[original] is not None
                        else ""
                    )
                    for original, column in zip(reader.fieldnames, columns)
                }

                # Ignore fully blank rows rather than treating them as data.
                if all(value == "" for value in row.values()):
                    continue

                # Required coordinates and signals must be finite numbers.
                parsed: dict[str, CellValue] = dict(row)

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

                # Missing uncertainty is not zero uncertainty.
                # Keep it as None and report the limitation after parsing.
                if "uncertainty" in OPTIONAL_COLUMNS.intersection(columns):
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

    # Record a single summary warning instead of one warning per blank cell.
    warnings = ()
    if missing_uncertainty_count:
        warnings = (
            f"{missing_uncertainty_count} measurement row(s) have missing "
            "uncertainty values. Missing uncertainty is not zero uncertainty.",
        )

    return SpectrumData(
        source_file=path.resolve(),
        columns=columns,
        rows=tuple(rows),
        warnings=warnings,
    )
