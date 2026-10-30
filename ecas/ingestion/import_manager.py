
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

    Legacy CSV behavior remains unchanged. Explicit laboratory CSV and JCAMP
    schemas are dispatched to the local-library adapter; other scientific
    tables use the existing tabular parsers.
    """
    path = Path(file_path)

    suffix = path.suffix.lower()
    if suffix in (".jdx", ".dx", ".jcamp", ".jcm"):
        from ecas.identification.library import load_library_spectrum
        try:
            return load_library_spectrum(path)
        except (OSError, ValueError) as exc:
            raise SpectrumImportError(str(exc)) from exc
    if suffix in (".ecsv", ".dat", ".tsv", ".txt", ".asc", ".fits", ".fit", ".fts"):
        from ecas.ingestion.tabular_formats import import_tabular_spectrum
        return import_tabular_spectrum(path)
    if suffix == ".csv" and archive_schema is None:
        # Recognize an explicit physical schema, never numeric-range guessing.
        import csv
        try:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                headers = next(csv.reader(stream), [])
            if headers == ["wavelength_nm", "absorption_cross_section_cm2_per_molecule"]:
                from ecas.identification.library import load_library_spectrum
                return load_library_spectrum(path)
        except (OSError, ValueError) as exc:
            raise SpectrumImportError(str(exc)) from exc
    if suffix != ".csv":
        raise SpectrumImportError(
            f"Unsupported file format '{path.suffix or '(no extension)'}'. "
            "Use CSV, supported scientific tables, or uncompressed JCAMP-DX."
        )

    return import_spectrum_csv(
        path,
        archive_schema=archive_schema,
    )
