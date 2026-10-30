"""Scientific tabular and FITS binary-table importers for ECAS Chunk 7.

Supports:
- Astropy Enhanced Character-Separated Values (.ecsv)
- Delimited scientific ASCII / TSV tables (.dat, .tsv, .txt, .asc)
- FITS 1D spectral binary tables (.fits, .fit, .fts; XTENSION = 'BINTABLE')

Distinguishes astronomical observations (e.g. Transmission transit depth) from
laboratory FTIR/UV-Vis measurements (wavenumber / absorbance or transmittance)
so laboratory reference spectra are never conflated with planetary transit depth.
"""
from __future__ import annotations

import csv
import io
import math
from pathlib import Path
import re
import struct

from ecas.ingestion.csv_importer import SpectrumImportError
from ecas.models.spectrum import CellValue, SpectrumData

MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_ROWS = 100_000
MAX_FITS_FILE_BYTES = 8 * 1024**3
MAX_FITS_HDUS = 128
MAX_FITS_HEADER_BLOCKS = 128
MAX_FITS_COLUMNS = 128
MAX_FITS_CELLS = 1_000_000

_CANONICAL_UNIT_MAP = {
    "um": "um",
    "micron": "um",
    "microns": "microns",
    "nm": "nm",
    "angstrom": "angstrom",
    "a": "angstrom",
    "cm-1": "cm^-1",
    "cm^-1": "cm^-1",
    "1/cm": "cm^-1",
    "ppm": "ppm",
    "%": "%",
    "percent": "percent",
    "dimensionless": "dimensionless",
    "absorbance": "absorbance",
    "transmittance": "transmittance",
    "cm^2/molecule": "cm^2/molecule",
    "cm2/molecule": "cm^2/molecule",
    "cm^2": "cm^2/molecule",
}


def _read_bounded_bytes(path: str | Path, *, expected_suffixes: tuple[str, ...]) -> tuple[Path, bytes]:
    target = Path(path)
    if not target.exists():
        raise SpectrumImportError(f"File does not exist: {target}")
    if not target.is_file() or target.is_symlink() or target.is_junction():
        raise SpectrumImportError(f"Path is not a regular file: {target}")
    suffix = target.suffix.lower()
    if suffix not in expected_suffixes:
        raise SpectrumImportError(
            f"Unsupported file extension {suffix!r}; expected one of {', '.join(expected_suffixes)}."
        )
    with target.open("rb") as stream:
        raw = stream.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise SpectrumImportError("Spectrum file exceeds 16 MiB limit.")
    if not raw:
        raise SpectrumImportError("Spectrum file is empty.")
    return target.resolve(), raw


def _normalize_unit(raw_unit: str | None) -> str | None:
    if raw_unit is None:
        return None
    cleaned = raw_unit.strip().strip("'\"")
    if not cleaned:
        return None
    return _CANONICAL_UNIT_MAP.get(cleaned.lower(), cleaned)


def _classify_columns_and_semantics(
    col_names: list[str],
    col_units: dict[str, str | None],
    header_meta: dict[str, str],
) -> tuple[str, str, str | None, str | None, str | None, str | None]:
    """Identify coordinate, signal, and uncertainty columns plus physical semantics.

    Returns (coord_col, signal_col, unc_col, axis_unit, signal_unit, signal_type).
    """
    lower_to_orig = {name.lower(): name for name in col_names}

    # Check whether this is a laboratory FTIR / UV-Vis / cross-section / emission spectrum
    is_lab_wavenumber = "wavenumber" in lower_to_orig or "nu" in lower_to_orig
    is_lab_absorbance = "absorbance" in lower_to_orig
    is_lab_transmittance = "transmittance" in lower_to_orig
    is_cross_section = "cross_section" in lower_to_orig or "sigma_cm2" in lower_to_orig
    is_emission_ref = "emission_intensity" in lower_to_orig or "line_flux" in lower_to_orig

    if is_lab_wavenumber and (is_lab_absorbance or is_lab_transmittance):
        coord_col = lower_to_orig.get("wavenumber") or lower_to_orig["nu"]
        signal_col = (
            lower_to_orig["absorbance"]
            if is_lab_absorbance
            else lower_to_orig["transmittance"]
        )
        unc_col = lower_to_orig.get("uncertainty") or lower_to_orig.get("error")
        axis_unit = _normalize_unit(col_units.get(coord_col)) or _normalize_unit(
            header_meta.get("axis_unit")
        ) or "cm^-1"
        default_sig_unit = "absorbance" if is_lab_absorbance else "transmittance"
        signal_unit = _normalize_unit(col_units.get(signal_col)) or _normalize_unit(
            header_meta.get("signal_unit")
        ) or default_sig_unit
        signal_type = (
            "Laboratory FTIR Absorbance"
            if is_lab_absorbance
            else "Laboratory FTIR Transmittance"
        )
        return coord_col, signal_col, unc_col, axis_unit, signal_unit, signal_type

    if not is_lab_wavenumber and (is_lab_absorbance or is_lab_transmittance):
        coord_col = None
        for candidate in ("wavelength", "wave", "lambda"):
            if candidate in lower_to_orig:
                coord_col = lower_to_orig[candidate]
                break
        if coord_col is not None:
            signal_col = (
                lower_to_orig["absorbance"]
                if is_lab_absorbance
                else lower_to_orig["transmittance"]
            )
            unc_col = lower_to_orig.get("uncertainty") or lower_to_orig.get("error")
            axis_unit = _normalize_unit(col_units.get(coord_col)) or _normalize_unit(
                header_meta.get("axis_unit")
            )
            default_sig_unit = "absorbance" if is_lab_absorbance else "transmittance"
            signal_unit = _normalize_unit(col_units.get(signal_col)) or _normalize_unit(
                header_meta.get("signal_unit")
            ) or default_sig_unit
            signal_type = (
                "Laboratory UV-Vis Absorbance"
                if is_lab_absorbance
                else "Laboratory UV-Vis Transmittance"
            )
            return coord_col, signal_col, unc_col, axis_unit, signal_unit, signal_type

    if is_cross_section:
        coord_col = None
        for candidate in ("wavelength", "wavenumber", "nu", "wave", "lambda"):
            if candidate in lower_to_orig:
                coord_col = lower_to_orig[candidate]
                break
        if coord_col is not None:
            signal_col = lower_to_orig.get("cross_section") or lower_to_orig["sigma_cm2"]
            unc_col = lower_to_orig.get("uncertainty") or lower_to_orig.get("error")
            default_axis = "cm^-1" if coord_col.lower() in ("wavenumber", "nu") else None
            axis_unit = _normalize_unit(col_units.get(coord_col)) or _normalize_unit(
                header_meta.get("axis_unit")
            ) or default_axis
            signal_unit = _normalize_unit(col_units.get(signal_col)) or _normalize_unit(
                header_meta.get("signal_unit")
            ) or "cm^2/molecule"
            signal_type = "Laboratory Cross Section"
            return coord_col, signal_col, unc_col, axis_unit, signal_unit, signal_type

    if is_emission_ref:
        coord_col = None
        for candidate in ("wavelength", "wavenumber", "nu", "wave", "lambda"):
            if candidate in lower_to_orig:
                coord_col = lower_to_orig[candidate]
                break
        if coord_col is not None:
            signal_col = lower_to_orig.get("emission_intensity") or lower_to_orig["line_flux"]
            unc_col = lower_to_orig.get("uncertainty") or lower_to_orig.get("error")
            axis_unit = _normalize_unit(col_units.get(coord_col)) or _normalize_unit(
                header_meta.get("axis_unit")
            )
            signal_unit = _normalize_unit(col_units.get(signal_col)) or _normalize_unit(
                header_meta.get("signal_unit")
            )
            signal_type = "Reference Emission Spectrum"
            return coord_col, signal_col, unc_col, axis_unit, signal_unit, signal_type

    coord_col = None
    for candidate in ("wavelength", "centralwavelng", "wave", "lambda", "wavenumber"):
        if candidate in lower_to_orig:
            coord_col = lower_to_orig[candidate]
            break

    signal_col = None
    for candidate in ("signal", "transit_depth", "pl_trandep", "depth", "flux", "intensity"):
        if candidate in lower_to_orig:
            signal_col = lower_to_orig[candidate]
            break

    if coord_col is None or signal_col is None:
        raise SpectrumImportError(
            "Tabular spectrum must provide recognizable coordinate ('wavelength' or 'wavenumber') "
            "and signal ('signal', 'transit_depth', 'absorbance', or 'transmittance') columns."
        )

    unc_col = None
    for candidate in ("uncertainty", "error", "sigma", "err", "pl_trandeperr1"):
        if candidate in lower_to_orig:
            unc_col = lower_to_orig[candidate]
            break

    axis_unit = _normalize_unit(col_units.get(coord_col)) or _normalize_unit(
        header_meta.get("axis_unit")
    )
    signal_unit = _normalize_unit(col_units.get(signal_col)) or _normalize_unit(
        header_meta.get("signal_unit")
    )
    raw_sig_type = (
        header_meta.get("signal_type")
        or header_meta.get("spec_type")
        or header_meta.get("observable")
    )
    if raw_sig_type:
        cleaned_type = raw_sig_type.strip().strip("'\"")
        if cleaned_type.lower() in ("transmission", "transit_depth"):
            signal_type = "Transmission"
        else:
            signal_type = cleaned_type
    elif signal_col.lower() in ("transit_depth", "pl_trandep"):
        signal_type = "Transmission"
    else:
        signal_type = None

    return coord_col, signal_col, unc_col, axis_unit, signal_unit, signal_type


def _build_spectrum_from_parsed_rows(
    *,
    resolved_path: Path,
    col_names: list[str],
    raw_rows: list[dict[str, str | float | None]],
    coord_col: str,
    signal_col: str,
    unc_col: str | None,
    axis_unit: str | None,
    signal_unit: str | None,
    signal_type: str | None,
    metadata: dict[str, str] | None = None,
) -> SpectrumData:
    if not raw_rows:
        raise SpectrumImportError("Spectrum file contains no measurement rows.")
    if len(raw_rows) > MAX_ROWS:
        raise SpectrumImportError(f"Spectrum file exceeds {MAX_ROWS} row limit.")

    rows: list[dict[str, CellValue]] = []
    missing_uncertainty = 0
    for row_idx, raw_row in enumerate(raw_rows, start=1):
        parsed_row: dict[str, CellValue] = {}
        for col in col_names:
            val = raw_row.get(col)
            if val is None or (isinstance(val, str) and val.strip() in ("", "null", "nan", "NaN", "None")):
                parsed_row[col] = None
                continue
            if isinstance(val, (int, float)):
                fval = float(val)
                if not math.isfinite(fval):
                    raise SpectrumImportError(f"Non-finite numeric value in column {col!r} at row {row_idx}.")
                parsed_row[col] = fval
            else:
                text = str(val).strip()
                try:
                    fval = float(text)
                    if not math.isfinite(fval):
                        raise SpectrumImportError(f"Non-finite numeric value in column {col!r} at row {row_idx}.")
                    parsed_row[col] = fval
                except ValueError:
                    if col in (coord_col, signal_col, unc_col):
                        raise SpectrumImportError(
                            f"Invalid numeric value {text!r} in column {col!r} at row {row_idx}."
                        )
                    parsed_row[col] = text

        coord_val = parsed_row.get(coord_col)
        sig_val = parsed_row.get(signal_col)
        if not isinstance(coord_val, float) or not isinstance(sig_val, float):
            raise SpectrumImportError(
                f"Missing required coordinate or signal measurement at row {row_idx}."
            )
        parsed_row["wavelength"] = coord_val
        parsed_row["signal"] = sig_val
        if unc_col is not None:
            unc_val = parsed_row.get(unc_col)
            if unc_val is None:
                missing_uncertainty += 1
            elif isinstance(unc_val, float):
                if unc_val < 0.0:
                    raise SpectrumImportError(
                        f"Negative uncertainty value {unc_val} at row {row_idx}."
                    )
                parsed_row["uncertainty"] = unc_val

        rows.append(parsed_row)

    out_cols = list(col_names)
    for canonical in ("wavelength", "signal", "uncertainty"):
        if canonical not in out_cols and any(canonical in r for r in rows):
            out_cols.append(canonical)

    warnings: list[str] = []
    if unc_col is not None and missing_uncertainty > 0:
        warnings.append(f"{missing_uncertainty} row(s) have missing uncertainty values")
    if signal_type and signal_type.startswith("Laboratory"):
        warnings.append(
            f"Imported as {signal_type}; laboratory spectra are not planetary transit-depth observations"
        )
    elif signal_type == "Reference Emission Spectrum":
        warnings.append(
            f"Imported as {signal_type}; emission reference spectra are not planetary transit-depth observations"
        )

    return SpectrumData(
        source_file=resolved_path,
        rows=tuple(rows),
        columns=tuple(out_cols),
        axis_unit=axis_unit,
        signal_unit=signal_unit,
        signal_type=signal_type,
        warnings=tuple(warnings),
        metadata=tuple(sorted((str(k), str(v)) for k, v in (metadata or {}).items())),
    )


def import_ecsv_spectrum(path: str | Path) -> SpectrumData:
    """Import an Astropy Enhanced Character-Separated Values (.ecsv) spectrum."""
    resolved, raw = _read_bounded_bytes(path, expected_suffixes=(".ecsv",))
    try:
        lines = raw.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        raise SpectrumImportError(f"ECSV file is not valid UTF-8: {exc}") from exc

    header_lines: list[str] = []
    data_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#") and not data_lines:
            header_lines.append(stripped[1:].strip())
        elif not stripped.startswith("#"):
            data_lines.append(line)

    if not header_lines or not header_lines[0].startswith("%ECSV"):
        raise SpectrumImportError("ECSV file must begin with a '# %ECSV' header line.")
    if not data_lines:
        raise SpectrumImportError("ECSV file contains no header or data rows.")

    delimiter = " "
    col_units: dict[str, str | None] = {}
    header_meta: dict[str, str] = {}
    current_col_name: str | None = None
    in_meta = False

    for hline in header_lines[1:]:
        if hline.startswith("delimiter:"):
            raw_delim = hline.partition(":")[2].strip().strip("'\"")
            if raw_delim in (",", " ", "\t", "|"):
                delimiter = raw_delim
        elif hline.startswith("meta:"):
            in_meta = True
            current_col_name = None
        elif hline.startswith("datatype:"):
            in_meta = False
            current_col_name = None
        elif hline.startswith("- {") or hline.startswith("-"):
            in_meta = False
            name_match = re.search(r"name:\s*([^\s,}]+)", hline)
            unit_match = re.search(r"unit:\s*([^\s,}]+)", hline)
            if name_match:
                current_col_name = name_match.group(1).strip("'\"")
                if unit_match:
                    col_units[current_col_name] = unit_match.group(1).strip("'\"")
        elif current_col_name and hline.startswith("unit:"):
            col_units[current_col_name] = hline.partition(":")[2].strip().strip("'\"")
        elif in_meta and ":" in hline:
            k, _, v = hline.partition(":")
            header_meta[k.strip().lower()] = v.strip().strip("'\"")

    if delimiter == " ":
        col_names = data_lines[0].split()
        raw_rows: list[dict[str, str | float | None]] = []
        for row_idx, dline in enumerate(data_lines[1:], start=2):
            tokens = dline.split()
            if len(tokens) != len(col_names):
                raise SpectrumImportError(
                    f"ECSV row {row_idx} has {len(tokens)} values; expected {len(col_names)}."
                )
            raw_rows.append(dict(zip(col_names, tokens)))
    else:
        reader = csv.reader(io.StringIO("\n".join(data_lines)), delimiter=delimiter)
        all_rows = list(reader)
        col_names = [c.strip() for c in all_rows[0]]
        raw_rows = []
        for row_idx, tokens in enumerate(all_rows[1:], start=2):
            if len(tokens) != len(col_names):
                raise SpectrumImportError(
                    f"ECSV row {row_idx} has {len(tokens)} values; expected {len(col_names)}."
                )
            raw_rows.append(dict(zip(col_names, [t.strip() for t in tokens])))

    if not col_names or len(set(c.lower() for c in col_names)) != len(col_names):
        raise SpectrumImportError("ECSV header has empty or duplicate column names.")

    coord_col, signal_col, unc_col, axis_unit, signal_unit, signal_type = (
        _classify_columns_and_semantics(col_names, col_units, header_meta)
    )
    return _build_spectrum_from_parsed_rows(
        resolved_path=resolved,
        col_names=col_names,
        raw_rows=raw_rows,
        coord_col=coord_col,
        signal_col=signal_col,
        unc_col=unc_col,
        axis_unit=axis_unit,
        signal_unit=signal_unit,
        signal_type=signal_type,
        metadata=header_meta,
    )


def import_ascii_spectrum(path: str | Path) -> SpectrumData:
    """Import a whitespace- or tab-delimited scientific ASCII spectrum (.dat, .tsv, .txt, .asc)."""
    resolved, raw = _read_bounded_bytes(
        path, expected_suffixes=(".dat", ".tsv", ".txt", ".asc")
    )
    try:
        lines = raw.decode("utf-8-sig").splitlines()
    except UnicodeDecodeError as exc:
        raise SpectrumImportError(f"ASCII spectrum file is not valid UTF-8: {exc}") from exc

    header_meta: dict[str, str] = {}
    comment_lines: list[str] = []
    body_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped[0] in ("#", "%") and not body_lines:
            comment_body = stripped[1:].strip()
            comment_lines.append(comment_body)
            if ":" in comment_body or "=" in comment_body:
                sep = ":" if ":" in comment_body else "="
                k, _, v = comment_body.partition(sep)
                header_meta[k.strip().lower()] = v.strip()
        elif stripped[0] not in ("#", "%"):
            body_lines.append(line)

    if not body_lines:
        raise SpectrumImportError("ASCII spectrum file contains no data rows.")

    def _split_line(text: str) -> list[str]:
        if "\t" in text:
            return [tok.strip() for tok in text.split("\t") if tok.strip() != ""]
        if "," in text:
            return [tok.strip() for tok in text.split(",")]
        return text.split()

    first_tokens = _split_line(body_lines[0])
    try:
        for tok in first_tokens:
            float(tok)
        first_is_numeric = True
    except ValueError:
        first_is_numeric = False

    if not first_is_numeric:
        col_names = first_tokens
        data_lines = body_lines[1:]
    elif comment_lines:
        last_comment_tokens = _split_line(comment_lines[-1])
        if len(last_comment_tokens) == len(first_tokens) and all(
            re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", tok) for tok in last_comment_tokens
        ):
            col_names = last_comment_tokens
            data_lines = body_lines
        else:
            raise SpectrumImportError(
                "ASCII spectrum file must include an explicit column header row."
            )
    else:
        raise SpectrumImportError(
            "ASCII spectrum file must include an explicit column header row."
        )

    if not col_names or len(set(c.lower() for c in col_names)) != len(col_names):
        raise SpectrumImportError("ASCII spectrum has empty or duplicate column names.")

    raw_rows: list[dict[str, str | float | None]] = []
    for row_idx, dline in enumerate(data_lines, start=1):
        tokens = _split_line(dline)
        if len(tokens) != len(col_names):
            raise SpectrumImportError(
                f"ASCII spectrum row {row_idx} has {len(tokens)} columns; expected {len(col_names)}."
            )
        raw_rows.append(dict(zip(col_names, tokens)))

    coord_col, signal_col, unc_col, axis_unit, signal_unit, signal_type = (
        _classify_columns_and_semantics(col_names, {}, header_meta)
    )
    return _build_spectrum_from_parsed_rows(
        resolved_path=resolved,
        col_names=col_names,
        raw_rows=raw_rows,
        coord_col=coord_col,
        signal_col=signal_col,
        unc_col=unc_col,
        axis_unit=axis_unit,
        signal_unit=signal_unit,
        signal_type=signal_type,
        metadata=header_meta,
    )


def _fits_card_value(text: str) -> str:
    """Split comments only outside quoted FITS strings; unescape doubled quotes."""
    text = text.strip()
    if not text.startswith("'"):
        return text.split("/", 1)[0].strip()
    value, index = [], 1
    while index < len(text):
        if text[index] == "'":
            if index + 1 < len(text) and text[index + 1] == "'":
                value.append("'"); index += 2
                continue
            if text[index + 1:].strip() and not text[index + 1:].lstrip().startswith("/"):
                raise SpectrumImportError("Unsupported FITS continued string/header value")
            parsed = "".join(value).strip()
            if parsed.endswith("&"):
                raise SpectrumImportError("FITS CONTINUE long strings are unsupported; explicit extraction required")
            return parsed
        value.append(text[index]); index += 1
    raise SpectrumImportError("Unterminated FITS header string")


def _parse_fits_header_block(stream, offset: int) -> tuple[dict[str, str], int]:
    """Read bounded 2880-byte blocks; never load image arrays or the whole file."""
    cards: dict[str, str] = {}
    stream.seek(offset)
    for _ in range(MAX_FITS_HEADER_BLOCKS):
        block = stream.read(2880)
        if len(block) != 2880:
            raise SpectrumImportError("Malformed/truncated FITS header: missing END card or 2880-byte block")
        for i in range(0, 2880, 80):
            try:
                card = block[i : i + 80].decode("ascii")
            except UnicodeDecodeError as exc:
                raise SpectrumImportError("Non-ASCII FITS header") from exc
            keyword = card[:8].strip()
            if keyword == "END":
                return cards, stream.tell()
            if not keyword or card[8:10] != "= ":
                continue
            if keyword in cards:
                raise SpectrumImportError(f"Duplicate FITS header keyword {keyword}")
            cards[keyword] = _fits_card_value(card[10:])
    raise SpectrumImportError(f"FITS header exceeds {MAX_FITS_HEADER_BLOCKS} blocks")


def _fits_integer(cards, key, *, default=None, minimum=0, maximum=None):
    try:
        text = cards.get(key, default)
        if not re.fullmatch(r"[+-]?\d+", str(text)):
            raise ValueError()
        value = int(text)
        if value < minimum or (maximum is not None and value > maximum):
            raise ValueError()
        return value
    except (ValueError, TypeError) as exc:
        raise SpectrumImportError(f"Invalid/unsupported FITS {key}: {cards.get(key)!r}") from exc


def _fits_hdu_size(cards, *, primary=False):
    bitpix = _fits_integer(cards, "BITPIX", minimum=-64)
    if bitpix not in (8, 16, 32, 64, -32, -64):
        raise SpectrumImportError("Unsupported FITS BITPIX")
    naxis = _fits_integer(cards, "NAXIS", maximum=999)
    if cards.get("GROUPS") == "T":
        raise SpectrumImportError("FITS random groups are unsupported")
    elements = 0 if naxis == 0 else 1
    for axis in range(1, naxis + 1):
        elements *= _fits_integer(cards, f"NAXIS{axis}")
        if elements > MAX_FITS_FILE_BYTES:
            raise SpectrumImportError("FITS dimensions exceed supported container bounds")
    pcount = _fits_integer(cards, "PCOUNT", default="0" if primary else None)
    gcount = _fits_integer(cards, "GCOUNT", default="1" if primary else None, minimum=1)
    size = abs(bitpix) // 8 * gcount * (elements + pcount)
    if size > MAX_FITS_FILE_BYTES:
        raise SpectrumImportError("FITS declared data size exceeds 8 GiB limit")
    return ((size + 2879) // 2880) * 2880


def _fits_table_descriptor(cards, primary):
    """Validate one supported table without decoding any rows yet."""
    if cards.get("BITPIX") != "8" or cards.get("NAXIS") != "2" or cards.get("GCOUNT") != "1":
        raise SpectrumImportError("FITS BINTABLE requires BITPIX=8, NAXIS=2 and GCOUNT=1")
    width = _fits_integer(cards, "NAXIS1", minimum=1)
    count = _fits_integer(cards, "NAXIS2", minimum=1, maximum=MAX_ROWS)
    fields = _fits_integer(cards, "TFIELDS", minimum=1, maximum=MAX_FITS_COLUMNS)
    if count * fields > MAX_FITS_CELLS:
        raise SpectrumImportError(f"FITS decoded table exceeds {MAX_FITS_CELLS} cell limit")
    names = [cards.get(f"TTYPE{i}", f"col{i}").strip() for i in range(1, fields + 1)]
    if any(not name for name in names) or len({name.casefold() for name in names}) != fields:
        raise SpectrumImportError("FITS table has empty or duplicate column names")
    units = {name: cards.get(f"TUNIT{i}") for i, name in enumerate(names, 1)}
    meta = {"signal_type": cards.get("SPEC_TYP") or primary.get("SPEC_TYP") or "",
            "pl_name": cards.get("OBJECT") or primary.get("OBJECT") or "",
            "fits_extname": cards.get("EXTNAME", ""),
            "fits_numeric_conversion": "physical=TSCALn*stored+TZEROn; integer TNULLn retained as missing"}
    for key in ("MODALITY", "PHASE", "TEMP_K"):
        if cards.get(key) or primary.get(key):
            meta[{"MODALITY": "modality", "PHASE": "phase", "TEMP_K": "temperature_K"}[key]] = cards.get(key) or primary[key]
    semantics = _classify_columns_and_semantics(names, units, meta)
    formats, scales, zeros, nulls = [], [], [], []
    supported = {"D": "d", "E": "f", "J": "i", "K": "q", "I": "h", "B": "B"}
    for i, name in enumerate(names, 1):
        form = cards.get(f"TFORM{i}", "").upper().strip()
        match = re.fullmatch(r"1?([DEJKIB])", form)
        if not match:
            raise SpectrumImportError(f"Unsupported FITS column {name!r} format {form!r}; only scalar numeric D/E/J/K/I/B are supported, not vectors or variable-length arrays")
        formats.append(supported[match[1]])
        try:
            scale = float(cards.get(f"TSCAL{i}", "1").replace("D", "E"))
            zero = float(cards.get(f"TZERO{i}", "0").replace("D", "E"))
            if not math.isfinite(scale) or not math.isfinite(zero):
                raise ValueError()
        except ValueError as exc:
            raise SpectrumImportError("Non-finite/invalid FITS TSCAL/TZERO") from exc
        null = cards.get(f"TNULL{i}")
        if null is not None and match[1] in ("D", "E"):
            raise SpectrumImportError("TNULL is only supported on integer FITS columns")
        nulls.append(_fits_integer(cards, f"TNULL{i}", minimum=-(2**63)) if null is not None else None)
        scales.append(scale); zeros.append(zero)
    unpacker = struct.Struct(">" + "".join(formats))
    if unpacker.size != width:
        raise SpectrumImportError("FITS BINTABLE NAXIS1 does not match scalar TFORM byte widths")
    meta["fits_column_scaling"] = repr(tuple(zip(names, scales, zeros, nulls)))
    return names, meta, semantics, unpacker, scales, zeros, nulls, count


def import_fits_bintable_spectrum(path: str | Path) -> SpectrumData:
    """Stream one unambiguous scalar spectral BINTABLE from a FITS container.

    Image and unrelated table HDUs are skipped by validated offsets. Container
    size is bounded at 8 GiB; decoded spectra at 100,000 rows, 128 columns and
    1,000,000 cells. Vector/variable-length spectra and image-only FITS need a
    separate scientifically explicit extraction workflow.
    """
    target = Path(path)
    if (not target.is_file() or target.is_symlink() or target.is_junction()
            or target.suffix.lower() not in ('.fits', '.fit', '.fts')):
        raise SpectrumImportError('FITS import requires a regular .fits/.fit/.fts file')
    size = target.stat().st_size
    if not size or size > MAX_FITS_FILE_BYTES:
        raise SpectrumImportError('FITS container must be nonempty and at most 8 GiB')
    if size % 2880:
        raise SpectrumImportError('Invalid FITS file: byte length is not a multiple of 2880')
    resolved = target.resolve()
    candidates, issues, offset, hdu = [], [], 0, 0
    try:
        with resolved.open('rb') as stream:
            primary = {}
            while offset < size:
                if hdu >= MAX_FITS_HDUS:
                    raise SpectrumImportError(f'FITS exceeds {MAX_FITS_HDUS} HDU limit')
                cards, data_start = _parse_fits_header_block(stream, offset)
                if hdu == 0:
                    primary = cards
                    if primary.get('SIMPLE') != 'T':
                        raise SpectrumImportError('Invalid FITS primary header: SIMPLE = T required')
                elif not cards.get('XTENSION'):
                    raise SpectrumImportError('FITS extension missing XTENSION')
                padded = _fits_hdu_size(cards, primary=hdu == 0)
                next_offset = data_start + padded
                if next_offset > size:
                    raise SpectrumImportError(f'FITS HDU {hdu} data block is truncated')
                if cards.get('XTENSION') == 'BINTABLE':
                    # Classify by header before parsing formats: unrelated archive
                    # tables may use strings/vectors and are safely skipped.
                    fields = _fits_integer(cards, 'TFIELDS', minimum=1, maximum=999)
                    names = [cards.get(f'TTYPE{i}', f'col{i}').strip() for i in range(1, fields + 1)]
                    units = {name: cards.get(f'TUNIT{i}') for i, name in enumerate(names, 1)}
                    meta = {'signal_type': cards.get('SPEC_TYP') or primary.get('SPEC_TYP') or ''}
                    try:
                        _classify_columns_and_semantics(names, units, meta)
                    except SpectrumImportError as exc:
                        event_names = {name.upper() for name in names}
                        is_event = (cards.get('EXTNAME', '').upper() in ('EVENTS', 'EVENT')
                                    or ('TIME' in event_names and bool(event_names & {'DETX', 'DETY', 'PHA', 'PI'})))
                        issues.append(f'HDU {hdu}: event-list data require instrument calibration and spectral extraction; individual events are not a sampled spectrum'
                                      if is_event else f'HDU {hdu}: {exc}')
                    else:
                        descriptor = _fits_table_descriptor(cards, primary)
                        candidates.append((data_start, hdu, descriptor))
                offset, hdu = next_offset, hdu + 1
            if len(candidates) > 1:
                raise SpectrumImportError('Ambiguous FITS: multiple spectral BINTABLE extensions; extract/select one explicit spectrum first')
            if not candidates:
                detail = '; '.join(issues[:3])
                raise SpectrumImportError('FITS contains no supported scalar spectral BINTABLE; image-only/vector products require extraction. ' + detail)
            data_start, selected_hdu, descriptor = candidates[0]
            names, meta, semantics, unpacker, scales, zeros, nulls, count = descriptor
            meta['fits_hdu_index'] = str(selected_hdu)
            stream.seek(data_start)
            raw_rows = []
            for _ in range(count):
                row_bytes = stream.read(unpacker.size)
                if len(row_bytes) != unpacker.size:
                    raise SpectrumImportError('FITS BINTABLE data block changed or truncated during import')
                values = unpacker.unpack(row_bytes)
                row = {}
                for i, value in enumerate(values):
                    if nulls[i] is not None and value == nulls[i]:
                        row[names[i]] = None
                    else:
                        # Reject loss of integer information rather than silently
                        # rounding it into SpectrumData's floating representation.
                        if isinstance(value, int) and abs(value) > 2**53:
                            raise SpectrumImportError('FITS integer exceeds exact float64 range; explicit precision-preserving extraction required')
                        row[names[i]] = value * scales[i] + zeros[i]
                raw_rows.append(row)
    except (OSError, OverflowError, struct.error) as exc:
        raise SpectrumImportError(f'Cannot read FITS spectrum: {exc}') from exc
    coord, signal, uncertainty, axis_unit, signal_unit, signal_type = semantics
    return _build_spectrum_from_parsed_rows(
        resolved_path=resolved, col_names=names, raw_rows=raw_rows,
        coord_col=coord, signal_col=signal, unc_col=uncertainty,
        axis_unit=axis_unit, signal_unit=signal_unit, signal_type=signal_type,
        metadata=meta,
    )


def import_tabular_spectrum(path: str | Path) -> SpectrumData:
    """Dispatch scientific tabular or FITS binary-table spectra by file suffix."""
    suffix = Path(path).suffix.lower()
    if suffix == ".ecsv":
        return import_ecsv_spectrum(path)
    if suffix in (".dat", ".tsv", ".txt", ".asc"):
        return import_ascii_spectrum(path)
    if suffix in (".fits", ".fit", ".fts"):
        return import_fits_bintable_spectrum(path)
    raise SpectrumImportError(f"Unsupported tabular spectrum format: {suffix!r}")

