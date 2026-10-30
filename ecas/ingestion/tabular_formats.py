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


def _parse_fits_header_block(raw: bytes, offset: int) -> tuple[dict[str, str], int]:
    """Parse one 2880-byte aligned FITS header unit starting at offset."""
    cards: dict[str, str] = {}
    pos = offset
    while pos + 2880 <= len(raw):
        block = raw[pos : pos + 2880]
        pos += 2880
        for i in range(0, 2880, 80):
            card = block[i : i + 80].decode("ascii", errors="replace")
            keyword = card[:8].strip()
            if keyword == "END":
                return cards, pos
            if not keyword or card[8:10] != "= ":
                continue
            val_part = card[10:].split("/")[0].strip()
            if val_part.startswith("'") and "'" in val_part[1:]:
                val_part = val_part[1 : val_part.index("'", 1)].strip()
            cards[keyword] = val_part
    raise SpectrumImportError("Malformed FITS header: missing END card or misaligned 2880-byte block.")


def import_fits_bintable_spectrum(path: str | Path) -> SpectrumData:
    """Import a 1D spectral binary table from a FITS (.fits, .fit, .fts) file."""
    resolved, raw = _read_bounded_bytes(
        path, expected_suffixes=(".fits", ".fit", ".fts")
    )
    if len(raw) % 2880 != 0:
        raise SpectrumImportError("Invalid FITS file: byte length is not a multiple of 2880.")

    primary_cards, pos = _parse_fits_header_block(raw, 0)
    if primary_cards.get("SIMPLE") != "T":
        raise SpectrumImportError("Invalid FITS primary header: SIMPLE = T required.")

    # Skip primary data array if present
    naxis = int(primary_cards.get("NAXIS", "0"))
    if naxis > 0:
        bitpix = abs(int(primary_cards.get("BITPIX", "8")))
        n_elems = 1
        for ax in range(1, naxis + 1):
            n_elems *= int(primary_cards.get(f"NAXIS{ax}", "0"))
        n_bytes = (n_elems * bitpix) // 8
        padded = ((n_bytes + 2879) // 2880) * 2880
        pos += padded

    if pos >= len(raw):
        raise SpectrumImportError("FITS file contains no BINTABLE spectral extension.")

    ext_cards, pos = _parse_fits_header_block(raw, pos)
    if ext_cards.get("XTENSION") != "BINTABLE":
        raise SpectrumImportError(
            f"Unsupported FITS extension {ext_cards.get('XTENSION')!r}; expected 'BINTABLE'."
        )

    row_byte_len = int(ext_cards.get("NAXIS1", "0"))
    n_rows = int(ext_cards.get("NAXIS2", "0"))
    tfields = int(ext_cards.get("TFIELDS", "0"))
    if row_byte_len <= 0 or n_rows <= 0 or tfields <= 0:
        raise SpectrumImportError("FITS BINTABLE has zero rows or columns.")
    if n_rows > MAX_ROWS:
        raise SpectrumImportError(f"FITS BINTABLE exceeds {MAX_ROWS} row limit.")
    if pos + row_byte_len * n_rows > len(raw):
        raise SpectrumImportError("FITS BINTABLE data block is truncated.")

    col_names: list[str] = []
    col_units: dict[str, str | None] = {}
    fmt_parts = [">"]
    for idx in range(1, tfields + 1):
        ttype = ext_cards.get(f"TTYPE{idx}", f"col{idx}").strip()
        tform = ext_cards.get(f"TFORM{idx}", "").strip().upper()
        tunit = ext_cards.get(f"TUNIT{idx}")
        col_names.append(ttype)
        col_units[ttype] = tunit
        if tform in ("D", "1D"):
            fmt_parts.append("d")
        elif tform in ("E", "1E"):
            fmt_parts.append("f")
        elif tform in ("J", "1J"):
            fmt_parts.append("i")
        elif tform in ("K", "1K"):
            fmt_parts.append("q")
        else:
            raise SpectrumImportError(
                f"Unsupported FITS BINTABLE column format {tform!r} for column {ttype!r}; "
                "only scalar numeric columns (1D, 1E, 1J, 1K) are supported."
            )

    struct_fmt = "".join(fmt_parts)
    if struct.calcsize(struct_fmt) != row_byte_len:
        raise SpectrumImportError("FITS BINTABLE NAXIS1 does not match column TFORM byte width.")

    raw_rows: list[dict[str, str | float | None]] = []
    for r_idx in range(n_rows):
        row_bytes = raw[pos + r_idx * row_byte_len : pos + (r_idx + 1) * row_byte_len]
        unpacked = struct.unpack(struct_fmt, row_bytes)
        raw_rows.append(
            {col_names[c_idx]: float(unpacked[c_idx]) for c_idx in range(tfields)}
        )

    header_meta = {
        "signal_type": ext_cards.get("SPEC_TYP") or primary_cards.get("SPEC_TYP") or "",
        "pl_name": ext_cards.get("OBJECT") or primary_cards.get("OBJECT") or "",
    }
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

