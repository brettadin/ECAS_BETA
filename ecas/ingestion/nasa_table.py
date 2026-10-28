"""Strict four-header, column-aligned NASA transmission-table import.

Not a general IPAC reader: unsupported layouts/types fail explicitly. Original
files, source columns, metadata, units and limits are retained, not rewritten.
"""
from dataclasses import dataclass
from hashlib import sha256
import math
from pathlib import Path

from ecas.ingestion.csv_importer import SpectrumImportError
from ecas.models.spectrum import SpectrumData


@dataclass(frozen=True)
class TransmissionTable:
    spectrum: SpectrumData
    metadata: tuple[tuple[str, str], ...]
    column_units: tuple[tuple[str, str], ...]
    source_sha256: str


def import_transmission_table(path):
    path = Path(path)
    try:
        with path.open("rb") as stream:
            raw = stream.read(1048577)
        if len(raw) > 1048576:
            raise SpectrumImportError("NASA table exceeds 1 MiB")
        lines = raw.decode("utf-8-sig").splitlines()
    except (OSError, UnicodeError, ValueError) as error:
        raise SpectrumImportError(f"Cannot read NASA table: {error}") from error
    metadata = {}
    headers = []
    data = []
    for line in lines:
        if not line.strip():
            continue
        if line.startswith("\\") and not headers:
            key, sep, value = line[1:].partition("=")
            if sep:
                key = key.strip()
                if not key or key in metadata:
                    raise SpectrumImportError("Duplicate or empty NASA metadata key")
                metadata[key] = value.strip()
        elif line.startswith("|") and not data:
            headers.append(line)
        else:
            data.append(line)
    if metadata.get("SPEC_TYPE") != "Transmission" or not metadata.get("PL_NAME"):
        raise SpectrumImportError("Only explicitly identified NASA Transmission tables are supported")
    if len(headers) != 4 or not data or len(data) > 10000:
        raise SpectrumImportError("Expected four NASA table headers and measurement rows")
    bars = [i for i, c in enumerate(headers[0]) if c == "|"]
    if len(bars) < 4 or bars[0] != 0 or bars[-1] > 4096 or any(
            [i for i, c in enumerate(h) if c == "|"] != bars for h in headers):
        raise SpectrumImportError("Misaligned NASA table headers")
    cells = lambda line: [line[a+1:b].strip() for a, b in zip(bars, bars[1:])]
    names = [name.lower() for name in cells(headers[0])]
    types, units, nulls = [cells(h) for h in headers[1:]]
    types = [typ.lower() for typ in types]
    if any(not name for name in names) or len(set(names)) != len(names):
        raise SpectrumImportError("Duplicate or empty NASA column")
    required = {"centralwavelng", "pl_trandep", "pl_trandeplim"}
    if not required <= set(names) or {"wavelength", "signal"} & set(names):
        raise SpectrumImportError("Missing or conflicting transmission columns")
    numeric = {"double", "real", "float", "long", "int", "integer"}
    if any(t not in numeric | {"char"} for t in types):
        raise SpectrumImportError("Unsupported NASA column type")
    if any(types[names.index(n)] not in numeric for n in required):
        raise SpectrumImportError("Transmission coordinates and flags must be numeric")
    rows = []
    for line in data:
        if len(line) < bars[-1] or line[bars[-1]+1:].strip() or any(
                i < len(line) and not line[i].isspace() for i in bars):
            raise SpectrumImportError("Misaligned NASA measurement row")
        row = {}
        for name, typ, null, value in zip(names, types, nulls, cells(line)):
            # Match the declared marker exactly. A blank numeric null marker is
            # meaningful; undeclared blanks must not conceal malformed numbers.
            # Preserve empty text cells when no explicit text marker is supplied.
            if value == null and (null or typ in numeric):
                parsed = None
            elif typ == "char":
                parsed = value
            else:
                try:
                    parsed = int(value) if typ in {"long", "int", "integer"} else float(value)
                    if not math.isfinite(parsed):
                        raise ValueError("non-finite")
                except (ValueError, OverflowError) as error:
                    raise SpectrumImportError(f"Invalid numeric NASA field: {name}") from error
            row[name] = parsed
        if any(row[n] is None for n in required):
            raise SpectrumImportError("Missing required transmission measurement")
        if row["pl_trandeplim"] != 0:
            raise SpectrumImportError("Nonzero transit-depth flags are not supported for plotting")
        row.update(wavelength=row["centralwavelng"], signal=row["pl_trandep"])
        rows.append(row)
    unit_map = dict(zip(names, units))
    spectrum = SpectrumData(source_file=path.resolve(), rows=tuple(rows),
        columns=tuple(names) + ("wavelength", "signal"),
        axis_unit=unit_map["centralwavelng"] or None,
        signal_unit=unit_map["pl_trandep"] or None, signal_type="Transmission")
    return TransmissionTable(spectrum, tuple(metadata.items()), tuple(unit_map.items()),
                             sha256(raw).hexdigest())
