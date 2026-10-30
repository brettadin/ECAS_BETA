"""Scientific 2D FITS image container scanner and array reader.

Provides bounded, streaming inspection and targeted plane extraction for 2D
astronomical imaging products (such as JWST MIRI imaging exposures), keeping
scientific arrays distinct from 1D sampled spectra.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import numpy as np

from ecas.ingestion.csv_importer import SpectrumImportError
from ecas.ingestion.tabular_formats import (
    MAX_FITS_FILE_BYTES,
    MAX_FITS_HDUS,
    _fits_integer,
    _parse_fits_header_block,
)


@dataclass(frozen=True)
class FitsImagePlane:
    """Descriptor for a 2D image plane inside a FITS container."""

    hdu_index: int
    extname: str
    dimensions: tuple[int, ...]  # (NAXIS1, NAXIS2, ...) -> (width, height)
    bitpix: int
    bunit: str
    bscale: float
    bzero: float
    data_offset: int
    data_bytes: int
    extver: int | None = None
    cards: dict[str, str] = field(default_factory=dict, repr=False)

    @property
    def width(self) -> int:
        """NAXIS1 (columns / horizontal dimension)."""
        return self.dimensions[0] if self.dimensions else 0

    @property
    def height(self) -> int:
        """NAXIS2 (rows / vertical dimension)."""
        return self.dimensions[1] if len(self.dimensions) > 1 else 0

    @property
    def display_label(self) -> str:
        """Human-readable selector label with dimensions and units."""
        unit_str = f" [{self.bunit}]" if self.bunit else ""
        dim_str = f"{self.width} x {self.height}"
        return f"{self.extname} ({dim_str}{unit_str})"


@dataclass(frozen=True)
class FitsImageContainer:
    """Metadata and inventory of image planes in a FITS file."""

    path: Path
    file_size: int
    target_name: str
    telescope: str
    instrument: str
    detector: str
    filter_name: str
    date_obs: str
    exposure_time_sec: float | None
    pipeline_stage: str
    primary_cards: dict[str, str] = field(default_factory=dict, repr=False)
    planes: list[FitsImagePlane] = field(default_factory=list)

    @property
    def default_plane(self) -> FitsImagePlane | None:
        """Return the science plane (SCI) if present, otherwise the first plane."""
        if not self.planes:
            return None
        for p in self.planes:
            if p.extname.upper() == "SCI":
                return p
        return self.planes[0]

    @property
    def product_summary(self) -> str:
        """Concise telescope, instrument, and filter description."""
        parts = [p for p in (self.telescope, self.instrument, self.filter_name) if p]
        return " ".join(parts) if parts else "FITS Image"


def scan_fits_image(path: str | Path) -> FitsImageContainer | None:
    """Scan a FITS file and return an image container descriptor, or None if not an image."""
    resolved = Path(path).resolve()
    if not resolved.is_file():
        return None

    try:
        size = resolved.stat().st_size
    except OSError:
        return None

    if size > MAX_FITS_FILE_BYTES:
        return None

    primary_cards: dict[str, str] = {}
    planes: list[FitsImagePlane] = []
    offset = 0
    hdu = 0

    try:
        with resolved.open("rb") as stream:
            while offset < size and hdu < MAX_FITS_HDUS:
                cards, data_start = _parse_fits_header_block(stream, offset)
                if hdu == 0:
                    primary_cards = cards

                xtension = cards.get("XTENSION", "").strip()
                naxis = _fits_integer(cards, "NAXIS", default="0")
                bitpix = _fits_integer(cards, "BITPIX", minimum=-64)

                # Compute data byte count
                data_bytes = 0
                dims: list[int] = []
                if naxis > 0:
                    mult = 1
                    for i in range(1, naxis + 1):
                        d = _fits_integer(cards, f"NAXIS{i}")
                        dims.append(d)
                        mult *= d
                    data_bytes = mult * (abs(bitpix) // 8)

                padded = (data_bytes + 2879) // 2880 * 2880
                next_offset = data_start + padded
                if next_offset > size:
                    break

                # Detect 2D image HDUs
                is_image_hdu = (
                    (xtension == "IMAGE" or (hdu == 0 and naxis >= 2))
                    and naxis >= 2
                    and len(dims) >= 2
                )

                if is_image_hdu:
                    extname = cards.get("EXTNAME", "PRIMARY" if hdu == 0 else f"HDU_{hdu}").strip()
                    bunit = cards.get("BUNIT", "").strip()
                    try:
                        bscale = float(cards.get("BSCALE", "1.0"))
                    except ValueError:
                        bscale = 1.0
                    try:
                        bzero = float(cards.get("BZERO", "0.0"))
                    except ValueError:
                        bzero = 0.0

                    extver = None
                    if "EXTVER" in cards:
                        try:
                            extver = int(cards["EXTVER"])
                        except ValueError:
                            extver = None

                    planes.append(
                        FitsImagePlane(
                            hdu_index=hdu,
                            extname=extname,
                            dimensions=tuple(dims),
                            bitpix=bitpix,
                            bunit=bunit,
                            bscale=bscale,
                            bzero=bzero,
                            data_offset=data_start,
                            data_bytes=data_bytes,
                            extver=extver,
                            cards=cards,
                        )
                    )

                offset = next_offset
                hdu += 1

    except (OSError, SpectrumImportError):
        return None

    if not planes:
        return None

    target = primary_cards.get("TARGNAME") or primary_cards.get("OBJECT") or ""
    telescope = primary_cards.get("TELESCOP", "").strip()
    instrument = primary_cards.get("INSTRUME", "").strip()
    detector = primary_cards.get("DETECTOR", "").strip()
    filter_name = primary_cards.get("FILTER", "").strip()
    date_obs = primary_cards.get("DATE-OBS", "").strip()

    exp_str = primary_cards.get("EFFEXPTM") or primary_cards.get("EXPTIME")
    exposure_time: float | None = None
    if exp_str:
        try:
            exposure_time = float(exp_str)
        except ValueError:
            exposure_time = None

    pipeline_stages = []
    for stage_kw in ("S_RAMP", "S_PHOTOM", "S_OUTLIR", "S_CAL"):
        if stage_kw in primary_cards:
            pipeline_stages.append(f"{stage_kw}={primary_cards[stage_kw].strip()}")
    pipeline_stage = "; ".join(pipeline_stages)

    return FitsImageContainer(
        path=resolved,
        file_size=size,
        target_name=target,
        telescope=telescope,
        instrument=instrument,
        detector=detector,
        filter_name=filter_name,
        date_obs=date_obs,
        exposure_time_sec=exposure_time,
        pipeline_stage=pipeline_stage,
        primary_cards=primary_cards,
        planes=planes,
    )


def read_fits_image_plane(path: str | Path, plane: FitsImagePlane) -> np.ndarray:
    """Read a specific 2D image plane from a FITS file into a NumPy float32 or int32 array.

    FITS NAXIS1 is columns (X, width) and NAXIS2 is rows (Y, height).
    The returned array has shape (NAXIS2, NAXIS1), matching standard C-order (row, col)
    indexing: array[y, x].
    """
    resolved = Path(path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"FITS file not found: {resolved}")

    # Determine dtype from BITPIX
    # Standard FITS BITPIX: 8 (uint8), 16 (int16), 32 (int32), 64 (int64), -32 (float32), -64 (float64)
    bitpix_dtype_map = {
        8: ">u1",
        16: ">i2",
        32: ">i4",
        64: ">i8",
        -32: ">f4",
        -64: ">f8",
    }
    raw_dtype_str = bitpix_dtype_map.get(plane.bitpix)
    if raw_dtype_str is None:
        raise ValueError(f"Unsupported FITS BITPIX: {plane.bitpix}")

    width = plane.width
    height = plane.height
    expected_bytes = width * height * (abs(plane.bitpix) // 8)

    with resolved.open("rb") as stream:
        stream.seek(plane.data_offset)
        raw_bytes = stream.read(expected_bytes)

    if len(raw_bytes) < expected_bytes:
        raise ValueError(f"Truncated FITS data for HDU {plane.hdu_index} ({plane.extname})")

    arr = np.frombuffer(raw_bytes, dtype=raw_dtype_str)
    arr = arr.reshape((height, width))

    # Apply scaling if present
    if plane.bscale != 1.0 or plane.bzero != 0.0:
        # Scale to float32 or float64
        arr = arr.astype(np.float32) * float(plane.bscale) + float(plane.bzero)
    elif plane.bitpix in (-32, -64):
        # Convert big-endian float to native float32
        arr = arr.astype(np.float32)
    elif plane.bitpix in (16, 32):
        # Preserve native int32
        arr = arr.astype(np.int32)

    return arr


def compute_plane_statistics(array: np.ndarray) -> dict[str, Any]:
    """Compute robust scientific summary statistics for a 2D image plane."""
    total = int(array.size)
    if total == 0:
        return {
            "total_pixels": 0,
            "nan_count": 0,
            "finite_min": 0.0,
            "finite_max": 0.0,
            "median": 0.0,
            "mean": 0.0,
            "std": 0.0,
            "p01": 0.0,
            "p99": 0.0,
        }

    is_float = np.issubdtype(array.dtype, np.floating)
    if is_float:
        finite_mask = np.isfinite(array)
        nan_count = int(total - np.count_nonzero(finite_mask))
        if nan_count == total:
            return {
                "total_pixels": total,
                "nan_count": nan_count,
                "finite_min": float("nan"),
                "finite_max": float("nan"),
                "median": float("nan"),
                "mean": float("nan"),
                "std": float("nan"),
                "p01": float("nan"),
                "p99": float("nan"),
            }
        finite_vals = array[finite_mask]
    else:
        nan_count = 0
        finite_vals = array.ravel()

    finite_min = float(np.min(finite_vals))
    finite_max = float(np.max(finite_vals))
    mean = float(np.mean(finite_vals))
    median = float(np.median(finite_vals))
    std = float(np.std(finite_vals))
    p01, p99 = [float(v) for v in np.percentile(finite_vals, [1.0, 99.0])]

    return {
        "total_pixels": total,
        "nan_count": nan_count,
        "finite_min": finite_min,
        "finite_max": finite_max,
        "median": median,
        "mean": mean,
        "std": std,
        "p01": p01,
        "p99": p99,
    }


def apply_display_stretch(
    array: np.ndarray,
    stretch_name: str,
    stats: dict[str, Any] | None = None,
) -> tuple[np.ndarray, float, float]:
    """Apply a visual display stretch to a copy of the array for UI rendering.

    Returns (display_array, vmin, vmax).
    The raw scientific array is never mutated.
    """
    if stats is None:
        stats = compute_plane_statistics(array)

    p01 = stats["p01"]
    p99 = stats["p99"]
    fmin = stats["finite_min"]
    fmax = stats["finite_max"]

    if np.isnan(p01) or np.isnan(p99) or p01 == p99:
        p01, p99 = (0.0, 1.0) if np.isnan(p01) else (p01, p01 + 1.0)
    if np.isnan(fmin) or np.isnan(fmax) or fmin == fmax:
        fmin, fmax = (0.0, 1.0) if np.isnan(fmin) else (fmin, fmin + 1.0)

    # Replace NaNs with p01 for clean visualization
    disp = np.nan_to_num(array, nan=p01, posinf=p99, neginf=p01)

    stretch = stretch_name.lower()
    if "percentile" in stretch:
        return disp, p01, p99
    if "minmax" in stretch or "min-max" in stretch:
        return disp, fmin, fmax

    # Shift so minimum is at 0
    shifted = np.clip(disp - p01, 0.0, None)
    denom = max(p99 - p01, 1e-12)
    norm = np.clip(shifted / denom, 0.0, 1.0)

    if "asinh" in stretch:
        # Astronomical asinh stretch: asinh(x / beta) / asinh(1 / beta)
        beta = 0.1
        transformed = np.arcsinh(norm / beta) / np.arcsinh(1.0 / beta)
        return transformed.astype(np.float32), 0.0, 1.0

    if "sqrt" in stretch:
        return np.sqrt(norm).astype(np.float32), 0.0, 1.0

    if "log" in stretch:
        # log10(1 + 100 * norm) / log10(101)
        transformed = np.log10(1.0 + 100.0 * norm) / np.log10(101.0)
        return transformed.astype(np.float32), 0.0, 1.0

    return disp, p01, p99
