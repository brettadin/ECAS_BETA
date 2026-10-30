
"""Typed representation of an imported spectrum.

This model stores validated measurements, source information, and import
warnings. It does not guess physical units or scientific signal meaning.
"""

from dataclasses import dataclass
from pathlib import Path


# CSV cells can be numeric, text, or missing.
# None represents a missing value; it must never be treated as zero.
CellValue = float | str | None


@dataclass(frozen=True)
class SpectrumData:
    """Structured data returned after a spectrum file is imported."""

    # Original file location, retained for traceability.
    source_file: Path

    # Column names and validated rows, in their original column order.
    rows: tuple[dict[str, CellValue], ...]
    columns: tuple[str, ...]

    # None means the importer has not established this information.
    # These values must not be inferred from the data alone.
    axis_unit: str | None = None
    signal_unit: str | None = None
    signal_type: str | None = None

    # Non-fatal import limitations, such as missing uncertainty values.
    warnings: tuple[str, ...] = ()

    # Explicit source header/curation facts. Empty for legacy imports; never
    # inferred from the shape or magnitude of the measurements.
    metadata: tuple[tuple[str, str], ...] = ()

    @property
    def row_count(self) -> int:
        """Return the number of imported measurement rows."""
        return len(self.rows)
