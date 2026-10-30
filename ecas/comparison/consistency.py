"""Multi-dataset observation consistency and reduction pipeline comparison.

Analyzes multiple spectral datasets of the same astronomical target (e.g. WASP-39 b):
- Detects duplicate products (identical SHA-256) and alternative reductions of the
  same exposure (e.g. Eureka, FIREFLy, Tiberius, Tshirt, Feinstein).
- Forbids counting alternative pipeline reductions as independent physical evidence.
- Evaluates overlap regions and spectral resolution compatibility.
- Computes non-destructive systematic median offsets and residual diagnostics without
  silently resampling, stitching, or averaging the underlying empirical measurements.
- Preserves nuisance parameter specifications for downstream joint fitting.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from pathlib import Path
import re
from typing import Any, Sequence

import numpy as np

from ecas.comparison.eligibility import ComparisonInput
from ecas.models.spectrum import SpectrumData
from ecas.observations import ObservationContext

_PIPELINE_KEYWORDS = {
    "eureka": "Eureka! Reduction Pipeline",
    "firefly": "FIREFLy Reduction Pipeline",
    "tiberius": "Tiberius Reduction Pipeline",
    "tshirt": "Tshirt Reduction Pipeline",
    "feinstein": "Feinstein et al. (2023) Nature reduction",
    "rustamkulov": "Rustamkulov et al. (2023) Nature reduction",
    "alderaan": "Alderaan Reduction Pipeline",
}


@dataclass(frozen=True)
class DatasetIdentity:
    """Complete provenance and spectral characteristics of an observation dataset."""

    dataset_index: int
    source_id: str
    source_path: str
    source_sha256: str
    target_name: str
    instrument: str
    observing_mode: str
    epoch: str | None
    pipeline_or_reduction: str
    citation: str | None
    axis_unit: str
    signal_unit: str
    point_count: int
    wavelength_min_um: float
    wavelength_max_um: float
    median_resolution_delta_um: float
    has_uncertainties: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PairwiseConsistency:
    """Consistency audit between two datasets of the same target."""

    dataset_a_index: int
    dataset_b_index: int
    dataset_a_name: str
    dataset_b_name: str
    relationship: str  # 'DUPLICATE_FILE', 'ALTERNATIVE_REDUCTION', 'INDEPENDENT_OBSERVATIONS'
    independence_warning: str | None
    overlap_range_um: tuple[float, float] | None
    overlap_point_count: int
    resolution_ratio: float  # delta_a / delta_b
    resolution_compatible: bool
    resolution_notes: str
    systematic_median_offset: float | None
    offset_uncertainty: float | None
    offset_subtracted_rms: float | None
    consistency_chi2: float | None
    reduced_chi2: float | None
    max_discrepancy_sigma: float | None
    discrepancy_locations_um: tuple[float, ...]
    transformations_recorded: tuple[str, ...]
    nuisance_parameter_spec: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MultiObservationConsistencyReport:
    """Comprehensive multi-dataset consistency report for a target."""

    target_name: str
    datasets: tuple[DatasetIdentity, ...]
    pairwise_comparisons: tuple[PairwiseConsistency, ...]
    alternative_reduction_clusters: tuple[tuple[int, ...], ...]
    has_duplicate_files: bool
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "datasets": [d.to_dict() for d in self.datasets],
            "pairwise_comparisons": [p.to_dict() for p in self.pairwise_comparisons],
            "alternative_reduction_clusters": [list(c) for c in self.alternative_reduction_clusters],
            "has_duplicate_files": self.has_duplicate_files,
            "warnings": list(self.warnings),
        }


def _extract_dataset_identity(index: int, item: SpectrumData | ObservationContext | ComparisonInput) -> DatasetIdentity:
    if isinstance(item, ObservationContext):
        spec = item.spectrum
        path_str = str(spec.source_file)
        name_str = item.label
        sha = item.source_sha256 or getattr(spec, "source_sha256", "unknown_hash")
        meta = dict(item.metadata)
    elif isinstance(item, SpectrumData):
        spec = item
        path_str = str(spec.source_file)
        name_str = spec.source_file.name
        sha = getattr(spec, "source_sha256", "unknown_hash")
        meta = dict(getattr(spec, "metadata", ()))
    elif isinstance(item, ComparisonInput):
        spec = None
        path_str = item.source_id
        name_str = Path(item.source_id).name if "/" in item.source_id or "\\" in item.source_id else item.source_id
        sha = item.source_sha256 or "unknown_hash"
        meta = {}
    else:
        raise TypeError(f"Unsupported dataset type: {type(item)!r}")

    # Extract coordinates
    if spec is not None:
        coords = np.array([float(r["wavelength"]) for r in spec.rows if r.get("wavelength") is not None], dtype=float)
        has_unc = "uncertainty" in spec.columns or "pl_trandeperr1" in spec.columns
        axis_u = spec.axis_unit or "unknown"
        sig_u = spec.signal_unit or "percent"
    else:
        coords = np.asarray(item.coordinates, dtype=float)
        has_unc = item.sigma is not None or item.covariance is not None
        axis_u = item.axis_unit or "unknown"
        sig_u = item.signal_unit or "percent"

    coords = np.sort(coords[np.isfinite(coords) & (coords > 0)])
    w_min = float(coords[0]) if len(coords) else 0.0
    w_max = float(coords[-1]) if len(coords) else 0.0
    med_res = float(np.median(np.diff(coords))) if len(coords) > 1 else 0.0

    # Pipeline detection from path or metadata
    pipeline_name = "Standard Pipeline"
    lower_path = path_str.lower()
    for kw, label in _PIPELINE_KEYWORDS.items():
        if kw in lower_path:
            pipeline_name = label
            break

    target = meta.get("pl_name") or meta.get("PL_NAME") or meta.get("target") or "Unknown Target"
    if "wasp-39" in lower_path or "w39" in lower_path:
        target = "WASP-39 b"

    inst = meta.get("instrument") or meta.get("INSTRUME") or ("JWST NIRSpec/PRISM" if "prism" in lower_path else "Unspecified Instrument")
    mode = meta.get("mode") or meta.get("OBSMODE") or ("PRISM" if "prism" in lower_path else "Spectroscopy")
    epoch = meta.get("epoch") or meta.get("DATE-OBS") or meta.get("observation_date")
    cit = meta.get("citation") or meta.get("PL_TRANDEP_AUTHORS")

    return DatasetIdentity(
        dataset_index=index,
        source_id=name_str,
        source_path=path_str,
        source_sha256=sha,
        target_name=str(target),
        instrument=str(inst),
        observing_mode=str(mode),
        epoch=str(epoch) if epoch else None,
        pipeline_or_reduction=pipeline_name,
        citation=str(cit) if cit else None,
        axis_unit=axis_u,
        signal_unit=sig_u,
        point_count=len(coords),
        wavelength_min_um=w_min,
        wavelength_max_um=w_max,
        median_resolution_delta_um=med_res,
        has_uncertainties=has_unc,
    )


def _get_dataset_arrays(item: SpectrumData | ObservationContext | ComparisonInput) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    if isinstance(item, ObservationContext):
        spec = item.spectrum
    elif isinstance(item, SpectrumData):
        spec = item
    else:
        x = np.asarray(item.coordinates, dtype=float)
        y = np.asarray(item.values, dtype=float)
        s = np.asarray(item.sigma, dtype=float) if item.sigma is not None else None
        order = np.argsort(x)
        return x[order], y[order], (s[order] if s is not None else None)

    rows = spec.rows
    x_l, y_l, s_l = [], [], []
    has_unc = "uncertainty" in spec.columns
    for r in rows:
        w = r.get("wavelength")
        v = r.get("signal")
        if w is not None and v is not None:
            try:
                wf = float(w)
                vf = float(v)
                if math.isfinite(wf) and math.isfinite(vf) and wf > 0:
                    x_l.append(wf)
                    y_l.append(vf)
                    if has_unc and r.get("uncertainty") is not None:
                        s_l.append(float(r["uncertainty"]))
            except (ValueError, TypeError):
                continue
    x = np.array(x_l, dtype=float)
    y = np.array(y_l, dtype=float)
    s = np.array(s_l, dtype=float) if len(s_l) == len(x_l) and len(s_l) > 0 else None
    order = np.argsort(x)
    return x[order], y[order], (s[order] if s is not None else None)


def compare_observation_consistency(
    datasets: Sequence[SpectrumData | ObservationContext | ComparisonInput],
    *,
    target_name: str | None = None,
) -> MultiObservationConsistencyReport:
    """Analyze multi-dataset consistency for a set of observations."""
    if len(datasets) < 2:
        raise ValueError("Multi-observation consistency comparison requires at least 2 datasets")

    identities = tuple(_extract_dataset_identity(i, item) for i, item in enumerate(datasets))
    resolved_target = target_name or identities[0].target_name

    pairwise_list: list[PairwiseConsistency] = []
    clusters: list[set[int]] = []
    warnings_list: list[str] = []
    has_duplicate = False

    for i in range(len(datasets)):
        for j in range(i + 1, len(datasets)):
            id_a, id_b = identities[i], identities[j]
            item_a, item_b = datasets[i], datasets[j]
            x_a, y_a, s_a = _get_dataset_arrays(item_a)
            x_b, y_b, s_b = _get_dataset_arrays(item_b)

            transforms: list[str] = []

            # 1. Classify Relationship
            if id_a.source_sha256 == id_b.source_sha256 and id_a.source_sha256 != "unknown_hash":
                rel = "DUPLICATE_FILE"
                has_duplicate = True
                warning = f"Datasets [{i}] and [{j}] share identical SHA-256 raw bytes; they are duplicate files."
            elif (
                (id_a.pipeline_or_reduction != "Standard Pipeline" and id_b.pipeline_or_reduction != "Standard Pipeline")
                or (id_a.instrument == id_b.instrument and id_a.instrument != "Unspecified Instrument" and id_a.observing_mode == id_b.observing_mode)
            ):
                rel = "ALTERNATIVE_REDUCTION"
                warning = (
                    f"Datasets [{i}] ({id_a.pipeline_or_reduction}) and [{j}] ({id_b.pipeline_or_reduction}) "
                    "are alternative reduction pipelines of the same exposure; they must NOT be combined as independent evidence."
                )
                # Group into cluster
                found_cluster = False
                for cl in clusters:
                    if i in cl or j in cl:
                        cl.add(i)
                        cl.add(j)
                        found_cluster = True
                        break
                if not found_cluster:
                    clusters.append({i, j})
            else:
                rel = "INDEPENDENT_OBSERVATIONS"
                warning = None

            # 2. Check Overlap
            ov_min = max(id_a.wavelength_min_um, id_b.wavelength_min_um)
            ov_max = min(id_a.wavelength_max_um, id_b.wavelength_max_um)

            if ov_max <= ov_min:
                pairwise_list.append(
                    PairwiseConsistency(
                        dataset_a_index=i,
                        dataset_b_index=j,
                        dataset_a_name=id_a.source_id,
                        dataset_b_name=id_b.source_id,
                        relationship=rel,
                        independence_warning=warning,
                        overlap_range_um=None,
                        overlap_point_count=0,
                        resolution_ratio=float(id_a.median_resolution_delta_um / max(id_b.median_resolution_delta_um, 1e-9)),
                        resolution_compatible=False,
                        resolution_notes="Disjoint wavelength coverage; no spectral overlap exists.",
                        systematic_median_offset=None,
                        offset_uncertainty=None,
                        offset_subtracted_rms=None,
                        consistency_chi2=None,
                        reduced_chi2=None,
                        max_discrepancy_sigma=None,
                        discrepancy_locations_um=(),
                        transformations_recorded=(),
                        nuisance_parameter_spec=None,
                    )
                )
                continue

            # 3. Resolution Compatibility
            r_ratio = float(id_a.median_resolution_delta_um / max(id_b.median_resolution_delta_um, 1e-9))
            res_comp = 0.5 <= r_ratio <= 2.0
            res_notes = (
                f"Resolution ratio Δλ_a / Δλ_b = {r_ratio:.2f} (~1.0); grid sampling is compatible."
                if res_comp
                else f"Resolution disparity (ratio = {r_ratio:.2f}); fine grid requires bin integration rather than direct sample comparison."
            )

            # 4. Non-Destructive Overlap Evaluation
            # We match points on a common overlap grid via linear interpolation of whichever dataset is smoother
            mask_a = (x_a >= ov_min) & (x_a <= ov_max)
            mask_b = (x_b >= ov_min) & (x_b <= ov_max)
            n_ov = min(int(np.count_nonzero(mask_a)), int(np.count_nonzero(mask_b)))

            if n_ov < 3:
                pairwise_list.append(
                    PairwiseConsistency(
                        dataset_a_index=i,
                        dataset_b_index=j,
                        dataset_a_name=id_a.source_id,
                        dataset_b_name=id_b.source_id,
                        relationship=rel,
                        independence_warning=warning,
                        overlap_range_um=(float(ov_min), float(ov_max)),
                        overlap_point_count=n_ov,
                        resolution_ratio=r_ratio,
                        resolution_compatible=False,
                        resolution_notes=f"Fewer than 3 overlapping samples in [{ov_min:.3g}, {ov_max:.3g}] µm; insufficient for consistency metrics.",
                        systematic_median_offset=None,
                        offset_uncertainty=None,
                        offset_subtracted_rms=None,
                        consistency_chi2=None,
                        reduced_chi2=None,
                        max_discrepancy_sigma=None,
                        discrepancy_locations_um=(),
                        transformations_recorded=(),
                        nuisance_parameter_spec=None,
                    )
                )
                continue

            # Evaluate differences at observation A's points within overlap
            sub_xa = x_a[mask_a]
            sub_ya = y_a[mask_a]
            sub_yb = np.interp(sub_xa, x_b, y_b)
            transforms.append(f"Interpolated dataset B onto {len(sub_xa)} points of dataset A for non-destructive offset estimation")

            diff = sub_ya - sub_yb
            med_offset = float(np.median(diff))
            centered_diff = diff - med_offset
            rms_diff = float(np.sqrt(np.mean(centered_diff ** 2)))

            # Uncertainty & Chi-squared consistency
            chi2: float | None = None
            red_chi2: float | None = None
            max_sig: float | None = None
            offset_err: float | None = None
            discrepant_locs: list[float] = []

            if s_a is not None and s_b is not None:
                sub_sa = s_a[mask_a]
                sub_sb = np.interp(sub_xa, x_b, s_b)
                comb_var = sub_sa ** 2 + sub_sb ** 2
                comb_sig = np.sqrt(comb_var)

                # Variance-weighted offset
                weights = 1.0 / np.maximum(comb_var, 1e-15)
                weighted_mean_offset = float(np.sum(diff * weights) / np.sum(weights))
                offset_err = float(1.0 / math.sqrt(np.sum(weights)))

                # Consistency chi2 using systematic offset
                pt_chi2 = (diff - med_offset) ** 2 / comb_var
                chi2 = float(np.sum(pt_chi2))
                dof = max(1, len(sub_xa) - 1)
                red_chi2 = float(chi2 / dof)

                sig_diff = np.abs(diff - med_offset) / comb_sig
                max_sig = float(np.max(sig_diff))

                # Identify regions with > 2.5 sigma discrepancies
                bad_idx = np.where(sig_diff > 2.5)[0]
                discrepant_locs = [float(sub_xa[bi]) for bi in bad_idx]
            else:
                offset_err = float(rms_diff / math.sqrt(len(sub_xa)))

            nuisance_spec = {
                "parameter_name": f"offset_{id_a.source_id}_vs_{id_b.source_id}",
                "estimated_value": med_offset,
                "uncertainty": offset_err,
                "unit": id_a.signal_unit,
                "prior_recommendation": f"Gaussian(mu={med_offset:.5g}, sigma={max(offset_err or 0.01, 0.01):.5g})",
            }

            pairwise_list.append(
                PairwiseConsistency(
                    dataset_a_index=i,
                    dataset_b_index=j,
                    dataset_a_name=id_a.source_id,
                    dataset_b_name=id_b.source_id,
                    relationship=rel,
                    independence_warning=warning,
                    overlap_range_um=(float(ov_min), float(ov_max)),
                    overlap_point_count=len(sub_xa),
                    resolution_ratio=r_ratio,
                    resolution_compatible=res_comp,
                    resolution_notes=res_notes,
                    systematic_median_offset=med_offset,
                    offset_uncertainty=offset_err,
                    offset_subtracted_rms=rms_diff,
                    consistency_chi2=chi2,
                    reduced_chi2=red_chi2,
                    max_discrepancy_sigma=max_sig,
                    discrepancy_locations_um=tuple(discrepant_locs),
                    transformations_recorded=tuple(transforms),
                    nuisance_parameter_spec=nuisance_spec,
                )
            )

    if clusters:
        warnings_list.append(
            f"Detected {len(clusters)} alternative reduction cluster(s) sharing raw exposures. "
            "Pipelines within each cluster represent alternative reductions, NOT independent data."
        )

    return MultiObservationConsistencyReport(
        target_name=resolved_target,
        datasets=identities,
        pairwise_comparisons=tuple(pairwise_list),
        alternative_reduction_clusters=tuple(tuple(sorted(cl)) for cl in clusters),
        has_duplicate_files=has_duplicate,
        warnings=tuple(warnings_list),
    )

