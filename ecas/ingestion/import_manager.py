
"""Coordinate spectrum imports across supported file formats."""

from pathlib import Path

from ecas.ingestion.csv_importer import (
    SpectrumImportError,
    import_spectrum_csv,
)
from ecas.models.spectrum import SpectrumData


def import_spectrum(
    file_path: str | Path,
    *,
    archive_schema: dict[str, str] | None = None,
) -> SpectrumData:
    """Import a spectrum using the parser for its supported file format.

    CSV is the only supported format in this initial implementation.
    Format-specific parsing and validation remain in csv_importer.
    """
    path = Path(file_path)

    if path.suffix.lower() != ".csv":
        raise SpectrumImportError(
            f"Unsupported file format '{path.suffix or '(no extension)'}'. "
            "Currently, only CSV files are supported."
        )

    return import_spectrum_csv(
        path,
        archive_schema=archive_schema,
    )
