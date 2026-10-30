"""Lossless local reference discovery and explicit scientific format adapters.

JCAMP support intentionally covers uncompressed AFFN XYDATA/XYPOINTS only.
Original values (including negative cross sections and T > 1) are retained.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field, replace
import hashlib
import math
from pathlib import Path
import re

from ecas.models.spectrum import SpectrumData


@dataclass(frozen=True)
class ReferenceDataset:
    dataset_id: str
    molecule: str
    modality: str
    spectrum: SpectrumData
    metadata: dict = field(default_factory=dict)
    source_sha256: str = ""
    source_path: Path = Path()

    @property
    def ref_id(self):
        return self.dataset_id


@dataclass(frozen=True)
class LibraryCatalog:
    datasets: tuple[ReferenceDataset, ...]
    issues: tuple[str, ...] = ()


def _number(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Non-finite reference measurement")
    return value


def _jcamp(path: Path):
    tags, points = {}, []
    mode = None
    for line_no, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.split("$$", 1)[0].strip()
        if line.startswith("##"):
            key, separator, value = line[2:].partition("=")
            if not separator:
                raise ValueError(f"Malformed JCAMP header at line {line_no}")
            key = re.sub(r"[\s_-]", "", key).upper()
            tags[key] = value.strip()
            mode = key if key in ("XYDATA", "XYPOINTS") else None
            continue
        if not line or not mode:
            continue
        try:
            values = [_number(x) for x in re.split(r"[\s,;]+", line)]
        except ValueError as exc:
            raise ValueError(f"JCAMP compressed/non-AFFN values at line {line_no}; not supported") from exc
        xfactor = _number(tags.get("XFACTOR", "1"))
        if mode == "XYPOINTS":
            if len(values) % 2:
                raise ValueError("Unpaired JCAMP XYPOINTS coordinates")
            points.extend((values[i] * xfactor, values[i + 1]) for i in range(0, len(values), 2))
        else:
            if len(values) < 2:
                raise ValueError("JCAMP XYDATA row needs X and Y")
            dx = _number(tags.get("DELTAX", "0"))
            if not dx:
                dx = (_number(tags["LASTX"]) - _number(tags["FIRSTX"])) / (_number(tags["NPOINTS"]) - 1)
            points.extend((values[0] * xfactor + i * dx, y) for i, y in enumerate(values[1:]))
    if not points:
        raise ValueError("No supported JCAMP XY data")
    if "NPOINTS" in tags and len(points) != int(tags["NPOINTS"]):
        raise ValueError("JCAMP NPOINTS does not match decoded measurements")
    xu, yu = tags.get("XUNITS", "").upper(), tags.get("YUNITS", "").upper()
    if xu in ("1/CM", "CM-1", "WAVENUMBER"):
        axis = "cm^-1"
    elif xu in ("MICROMETERS", "MICROMETER", "MICRONS", "UM"):
        axis = "microns"
    elif xu in ("NANOMETERS", "NANOMETER", "NM"):
        axis = "nm"
    else:
        raise ValueError(f"Unsupported JCAMP XUNITS {xu!r}")
    if yu == "ABSORBANCE":
        kind, unit = "Laboratory Absorbance", "absorbance"
    elif yu in ("TRANSMITTANCE", "% TRANSMITTANCE", "PERCENT TRANSMITTANCE"):
        kind, unit = "Laboratory Transmittance", "%" if "%" in yu or "PERCENT" in yu else "fraction"
    else:
        raise ValueError(f"Unsupported JCAMP YUNITS {yu!r}; no quantity inferred")
    yfactor = _number(tags.get("YFACTOR", "1"))
    rows = tuple({"wavelength": x, "signal": y * yfactor} for x, y in points)
    spectrum = SpectrumData(path, rows, ("wavelength", "signal"), axis, unit, kind,
                            ("Laboratory reference; not a planetary transit-depth spectrum",))
    return spectrum, {"jcamp_headers": tags, "phase": tags.get("STATE", ""),
                      "title": tags.get("TITLE", ""), "cas": tags.get("CASREGISTRYNO", ""),
                      "origin": tags.get("ORIGIN", ""), "resolution": tags.get("RESOLUTION", ""),
                      "source_reference": tags.get("SOURCEREFERENCE", "")}


def _uv_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        expected = ("wavelength_nm", "absorption_cross_section_cm2_per_molecule")
        if not reader.fieldnames or tuple(reader.fieldnames) != expected:
            raise ValueError("Expected explicit wavelength_nm,absorption_cross_section_cm2_per_molecule columns")
        rows = tuple({expected[0]: _number(r[expected[0]]), expected[1]: _number(r[expected[1]]),
                      "wavelength": _number(r[expected[0]]), "signal": _number(r[expected[1]])} for r in reader)
    if not rows:
        raise ValueError("Empty UV–Vis CSV")
    warnings = ["Laboratory measured cross section; not a planetary transit-depth spectrum"]
    if any(r["signal"] < 0 for r in rows):
        warnings.append("Signed negative measured cross sections retained unchanged")
    return SpectrumData(path, rows, expected + ("wavelength", "signal"), "nm", "cm2/molecule",
                        "Laboratory Absorption Cross Section", tuple(warnings)), {}


def load_reference(path, modality=None, molecule=None) -> ReferenceDataset:
    path = Path(path).resolve()
    if path.suffix.lower() in (".jdx", ".dx", ".jcamp", ".jcm"):
        spectrum, metadata = _jcamp(path)
        modality = modality or "IR"
    elif path.suffix.lower() == ".csv":
        spectrum, metadata = _uv_csv(path)
        modality = modality or "UV-Vis"
    else:
        raise ValueError("Supported library formats: AFFN JCAMP-DX and explicit UV–Vis CSV")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    molecule = molecule or path.parent.name
    # Content and relative identity both matter: different source/condition variants remain separate.
    identity = hashlib.sha256((modality + "/" + molecule + "/" + path.name + "\n" + digest).encode()).hexdigest()
    library_root = next((p for p in path.parents if p.name == "ECAS_Spectral_Library"), None)
    if library_root:
        manifest = library_root / "Documentation" / ("IR/manifest.csv" if modality == "IR" else "UV-Vis/dataset_manifest.csv")
        if manifest.is_file():
            with manifest.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    name = row.get("filename") if modality == "IR" else Path(row.get("output_csv", "")).name
                    if name == path.name and (row.get("species") or row.get("molecule")) == molecule:
                        if row.get("sha256") and row["sha256"].lower() != digest:
                            raise ValueError("Reference bytes conflict with curation manifest SHA-256")
                        source_phase = str(metadata.get("phase", "")).lower()
                        curated_phase = str(row.get("phase", "")).lower()
                        source_phase_name = next((p for p in ("gas", "liquid", "solid") if re.search(r"\b" + p + r"\b", source_phase)), "")
                        if source_phase_name and curated_phase and source_phase_name != curated_phase:
                            raise ValueError("JCAMP STATE conflicts with curated phase; manual resolution required")
                        metadata["curation_manifest"] = dict(row)
                        for key in ("phase", "temperature_K", "source_database", "source_reference_hint", "download_url", "detail_url", "source_archive_path"):
                            if row.get(key):
                                metadata[key] = row[key]
                        raw_folder = library_root / "Raw_Sources" / ("IR" if modality == "IR" else "Uv-Vis") / molecule
                        raw_path = raw_folder / (row.get("filename") if modality == "IR" else row.get("original_filename", ""))
                        if raw_path.is_file():
                            metadata["raw_source_path"] = str(raw_path)
                            metadata["raw_source_sha256"] = hashlib.sha256(raw_path.read_bytes()).hexdigest()
                        break
    metadata.update({"modality": modality, "original_file": str(path), "source_sha256": digest})
    spectrum = replace(spectrum, metadata=tuple((str(k), str(v)) for k, v in metadata.items()))
    return ReferenceDataset(identity, molecule, modality, spectrum, metadata, digest, path)


def load_library_spectrum(path) -> SpectrumData:
    return load_reference(path).spectrum


def discover_library(root) -> LibraryCatalog:
    root = Path(root)
    ready = root / "Ready_For_ECAS"
    if not ready.is_dir():
        return LibraryCatalog((), (f"Prepared spectral library missing: {ready}",))
    datasets, issues = [], []
    for modality in ("IR", "UV-Vis"):
        # Current library uses Uv-Vis on disk; do not rename source directories.
        folder = ready / ("IR" if modality == "IR" else "Uv-Vis")
        if not folder.is_dir():
            issues.append(f"Missing {modality} directory: {folder}")
            continue
        for path in sorted(folder.rglob("*")):
            if path.suffix.lower() not in (".jdx", ".dx", ".jcamp", ".jcm", ".csv"):
                continue
            try:
                relative = path.relative_to(folder)
                molecule = relative.parts[0] if len(relative.parts) > 1 else path.stem.split("_")[0]
                datasets.append(load_reference(path, modality, molecule))
            except (OSError, ValueError, KeyError, ZeroDivisionError) as exc:
                issues.append(f"{path}: {exc}")
    return LibraryCatalog(tuple(datasets), tuple(issues))
