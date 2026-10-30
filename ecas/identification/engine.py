"""Conditional laboratory template fits recovered from ECAS v1 Identify.

The reported sqrt(delta chi-square) is a fit statistic, never a calibrated
molecular detection significance. Reference uncertainty/correlated noise are
not modelled. Planetary transit depth requires the separate radiative transfer
workflow. No pseudo-transmittance conversion is provided here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import sys
from importlib.metadata import PackageNotFoundError, version

import numpy as np

from ecas.models.spectrum import SpectrumData
from .library import ReferenceDataset


@dataclass(frozen=True)
class ComponentResult:
    dataset_id: str
    molecule: str
    modality: str
    sigma: float | None
    status: str
    reason: str = ""
    amplitude: float | None = None
    uncertainty: float | None = None
    delta_chi2: float | None = None


@dataclass(frozen=True)
class IdentificationResult:
    components: tuple[ComponentResult, ...]
    x: tuple[float, ...] = ()
    observed: tuple[float, ...] = ()
    model: tuple[float, ...] = ()
    component_curves: dict[str, tuple[float, ...]] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    settings: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    sigma_estimated: bool = True
    chi2: float | None = None
    reduced_chi2: float | None = None
    sigma_values: tuple[float, ...] = ()


def _kind(spectrum):
    value = (spectrum.signal_type or "").lower().replace("_", " ")
    if "transit" in value or value == "transmission":
        raise ValueError("Planetary transit depth requires a radiative-transfer model; laboratory identification is blocked")
    if "cross section" in value:
        if spectrum.signal_unit not in ("cm2/molecule", "cm^2/molecule", "cm2 molecule-1"):
            raise ValueError("Cross-section units must explicitly be cm²/molecule")
        return "cross_section"
    if "absorbance" in value:
        if spectrum.signal_unit not in ("absorbance", "dimensionless", "AU", "a.u."):
            raise ValueError("Absorbance units are missing or unsupported")
        return "absorbance"
    if "transmittance" in value:
        if spectrum.signal_unit not in ("fraction", "%", "percent", "dimensionless"):
            raise ValueError("Transmittance must explicitly declare fraction or percent units")
        return "transmittance"
    if "optical depth" in value and spectrum.signal_unit in ("dimensionless", "optical_depth", "1"):
        return "optical_depth"
    raise ValueError("Signal must explicitly describe laboratory absorbance, transmittance, optical depth or cross section")


def _arrays(spectrum):
    try:
        x = np.array([row["wavelength"] for row in spectrum.rows], dtype=float)
        y = np.array([row["signal"] for row in spectrum.rows], dtype=float)
    except (ValueError, KeyError, TypeError) as exc:
        raise ValueError("Missing numeric canonical wavelength/signal values") from exc
    if not x.size or not np.isfinite(x).all() or not np.isfinite(y).all() or np.any(x <= 0):
        raise ValueError("Coordinates must be positive and all measurements finite")
    unit = (spectrum.axis_unit or "").lower()
    if unit in ("cm^-1", "cm-1", "1/cm"):
        nu = x
    elif unit in ("microns", "micron", "um", "µm"):
        nu = 1e4 / x
    elif unit in ("nm", "nanometers", "nanometer"):
        nu = 1e7 / x
    else:
        raise ValueError("Explicit supported spectral coordinate units are required")
    order = np.argsort(nu, kind="stable")
    nu, y = nu[order], y[order]
    if np.any(np.diff(nu) <= 0):
        raise ValueError("Duplicate spectral coordinates require an explicit reduction; no averaging performed")
    sigma = None
    if "uncertainty" in spectrum.columns:
        try:
            sigma = np.array([row.get("uncertainty") for row in spectrum.rows], dtype=float)[order]
        except (ValueError, TypeError) as exc:
            raise ValueError("Unusable uncertainty values") from exc
        if not np.isfinite(sigma).all() or np.any(sigma <= 0):
            raise ValueError("Supplied uncertainties must be finite positive values for every point")
    return nu, y, sigma


def _phase(metadata):
    value = str(metadata.get("phase") or metadata.get("state") or "").lower()
    for phase in ("gas", "liquid", "solid"):
        if phase in value:
            return phase
    return ""


def _tau(y, kind, unit):
    if kind == "absorbance":
        return y * np.log(10.)
    if kind == "optical_depth":
        return y
    if kind == "transmittance":
        t = y / 100. if unit in ("%", "percent") else y
        if np.any(t <= 0):
            raise ValueError("Reference transmittance has nonpositive values; optical depth undefined")
        return -np.log(t)
    return y


def identify(observation: SpectrumData, references: list[ReferenceDataset], *,
             observation_metadata=None, threshold=3.0, continuum=True) -> IdentificationResult:
    """Fit every selected compatible reference jointly; retain explicit blocked rows.

All evaluated candidates use the same intersection of endpoint coverage.
Linear interpolation assumes continuous support between adjacent samples;
internal gaps and resolution compatibility are not established from endpoints
and must be reviewed independently. Returned arrays are fit quantity vs cm^-1:
natural optical depth for absorption, signed cross section for measured-template
UV comparison. Neither quantity is planetary transit depth.
"""
    source_metadata = dict(getattr(observation, "metadata", ()))
    metadata = dict(source_metadata)
    metadata.update(observation_metadata or {})
    warnings = ["Conditional sqrt(Δχ²) fit statistic; no calibrated detection significance or abundance is claimed",
                "Reference uncertainty, correlated noise, instrumental convolution and temperature structure are not modelled"]
    settings = {"method": "ecas-v1-drop-one-bvls-v1", "threshold": threshold, "continuum": continuum,
                "axis_unit": "cm^-1", "noise": "pending", "transforms": []}
    try:
        scipy_version = version('scipy')
    except PackageNotFoundError:
        scipy_version = 'unavailable'
    settings['software_environment'] = {'python': sys.version.split()[0],
                                        'numpy': np.__version__, 'scipy': scipy_version}
    def snapshot(s):
        return {"source_file": str(s.source_file), "rows": s.rows, "columns": s.columns,
                "axis_unit": s.axis_unit, "signal_unit": s.signal_unit, "signal_type": s.signal_type,
                "warnings": s.warnings, "metadata": getattr(s, "metadata", ())}
    provenance = {"observation_file": str(observation.source_file), "observation_metadata": metadata,
                  "observation_snapshot": snapshot(observation),
                  "references": [{"dataset_id": r.dataset_id, "sha256": r.source_sha256,
                                  "path": str(r.source_path), "metadata": r.metadata,
                                  "molecule": r.molecule, "modality": r.modality,
                                  "spectrum_snapshot": snapshot(r.spectrum)} for r in references]}
    blocked = {}
    def finish(reason):
        return IdentificationResult(tuple(ComponentResult(r.dataset_id, r.molecule, r.modality, None,
                                   "blocked", blocked.get(r.dataset_id, reason)) for r in references),
                                   warnings=tuple(warnings), settings=settings, provenance=provenance)
    for key in ("modality", "phase", "temperature_K"):
        if source_metadata.get(key) and observation_metadata and observation_metadata.get(key) and str(source_metadata[key]).lower() != str(observation_metadata[key]).lower():
            return finish(f"Observation metadata conflict: source-provided {key} cannot be overridden")
        if source_metadata.get(key):
            metadata[key] = source_metadata[key]
    try:
        from scipy.optimize import lsq_linear
    except ImportError as exc:
        return finish(f"Identification solver unavailable: {exc}")
    if not math.isfinite(threshold) or threshold < 0:
        return finish("Threshold must be finite and nonnegative")
    try:
        obs_kind = _kind(observation)
        nu, values, supplied_sigma = _arrays(observation)
    except ValueError as exc:
        return finish(str(exc))
    modality = metadata.get("modality")
    if modality not in ("IR", "UV-Vis"):
        return finish("Observation modality must explicitly be IR or UV-Vis")
    obs_phase = _phase(metadata)
    if not obs_phase:
        warnings.append("Observation phase is unknown; phase compatibility is not established")
    warnings.append("Reference sampling is linearly interpolated on the common endpoint window; internal gaps and instrument response require independent review")
    obs_temperature = metadata.get("temperature_K")
    if obs_kind == "cross_section":
        warnings.append("Exploratory signed measured-template cross-section fit; no physical opacity or column-density interpretation")
    settings["fit_quantity"] = "cross_section" if obs_kind == "cross_section" else "optical_depth"
    eligible = []
    for ref in references:
        try:
            if ref.modality != modality:
                raise ValueError("Reference modality differs from observation")
            phase = _phase(ref.metadata)
            if phase and obs_phase and phase != obs_phase:
                raise ValueError(f"Phase mismatch: observation {obs_phase}, reference {phase}")
            if not phase:
                warnings.append(f"{ref.molecule}: reference phase unknown")
            temperature = ref.metadata.get("temperature_K")
            if not obs_temperature or not temperature:
                warnings.append(f"{ref.molecule}: temperature compatibility is not established")
            elif str(obs_temperature) != str(temperature):
                warnings.append(f"{ref.molecule}: reference temperature {temperature} K differs from observation {obs_temperature} K; fit is exploratory")
            rk = _kind(ref.spectrum)
            if (rk == "cross_section") != (obs_kind == "cross_section"):
                # Cross sections can be bases of optical depth only with explicit
                # established gas conditions; this bounded release does not assume them.
                raise ValueError("Reference and observation quantities need an explicit physical adapter; cross-section/optical-depth mixing blocked")
            xn, y, _ = _arrays(ref.spectrum)
            k = _tau(y, rk, ref.spectrum.signal_unit)
            if np.count_nonzero((nu >= xn[0]) & (nu <= xn[-1])) < 20:
                raise ValueError("Fewer than 20 observation points overlap reference coverage")
            eligible.append((ref, xn, k))
            if str(ref.source_path.resolve()) == str(Path(observation.source_file).resolve()):
                warnings.append(f"{ref.molecule}: observation and reference use the same source file; self-comparison tests numerical consistency only")
        except ValueError as exc:
            blocked[ref.dataset_id] = str(exc)
    if not eligible:
        return finish("No compatible reference datasets")
    mask = (nu >= max(x[1][0] for x in eligible)) & (nu <= min(x[1][-1] for x in eligible))
    if np.count_nonzero(mask) < 20:
        return finish("Fewer than 20 observation points in the selected references' common coverage")
    nu, values = nu[mask], values[mask]
    sigma = None if supplied_sigma is None else supplied_sigma[mask]
    if obs_kind == "cross_section":
        target = values
    else:
        if obs_kind == "transmittance":
            t = values / 100. if observation.signal_unit in ("%", "percent") else values.copy()
            sig_t = None if sigma is None else sigma / (100. if observation.signal_unit in ("%", "percent") else 1.)
        else:
            tau = _tau(values, obs_kind, observation.signal_unit)
            if np.any(np.abs(tau) > 700):
                return finish("Optical depth outside safe exponential range; no clipping or substitution performed")
            t = np.exp(-tau)
            sig_t = None if sigma is None else sigma * t * (np.log(10.) if obs_kind == "absorbance" else 1.)
        cut = .05 if sig_t is None else max(.05, 3 * float(np.median(sig_t)))
        keep = t >= cut
        settings["transforms"].append({"step": "v1 optical-depth transform", "opaque_cut_T": cut,
                                       "excluded_points": int((~keep).sum())})
        nu, t = nu[keep], t[keep]
        sig_t = None if sig_t is None else sig_t[keep]
        target = -np.log(np.clip(t, .02, None))
        sigma = None if sig_t is None else np.maximum(sig_t / t, 1e-6)
    if nu.size < 20:
        return finish("Fewer than 20 usable points in the selected references' common coverage after opacity filtering")
    K = np.column_stack([np.interp(nu, xn, k) for _, xn, k in eligible])
    positive = np.max(K, axis=0) > 0
    for i in np.flatnonzero(~positive):
        blocked[eligible[i][0].dataset_id] = "Reference has no positive spectral support in the common window"
    eligible = [r for i, r in enumerate(eligible) if positive[i]]
    K = K[:, positive]
    if not eligible:
        return finish("No reference has positive spectral support in the common window")
    u = 2 * (nu - nu[0]) / max(float(nu[-1] - nu[0]), 1e-9) - 1
    C = np.column_stack((np.ones_like(u), u)) if continuum else np.zeros((nu.size, 0))
    raw = np.column_stack((K, C))
    scales = np.linalg.norm(raw, axis=0)
    scales[scales == 0] = 1
    design = raw / scales
    nr = K.shape[1]
    lower = np.r_[np.zeros(nr), np.full(C.shape[1], -np.inf)]
    cols = np.arange(raw.shape[1])
    def solve(weights, selected=cols):
        A, b = design[:, selected] / weights[:, None], target / weights
        if not selected.size:
            return np.zeros(raw.shape[1]), float(b @ b)
        sol = lsq_linear(A, b, bounds=(lower[selected], np.inf), method="bvls")
        if not sol.success:
            raise ValueError(f"Bounded fit did not converge: {sol.message}")
        x = np.zeros(raw.shape[1]); x[selected] = sol.x
        resid = A @ sol.x - b
        return x, float(resid @ resid)
    try:
        estimated = sigma is None
        if estimated:
            x0, _ = solve(np.ones_like(target))
            resid = values - design @ x0 if obs_kind == "cross_section" else t - np.exp(-(design @ x0))
            # Original v1 floor has transmittance units. Cross-section fitting
            # requires a unit-scaled floor; recorded as a modality adaptation.
            floor = 1e-6 if obs_kind != "cross_section" else max(float(np.max(np.abs(values))) * 1e-6, np.finfo(float).tiny)
            noise = max(1.4826 * float(np.median(np.abs(resid - np.median(resid)))), floor)
            sigma = np.full(target.size, noise) if obs_kind == "cross_section" else noise / t
            settings["transforms"].append({"step": "signed-cross-section residual MAD adaptation" if obs_kind == "cross_section" else "v1 transmittance residual MAD",
                                           "noise_floor": floor, "estimated_noise": noise})
        x, chi2 = solve(sigma)
    except (ValueError, np.linalg.LinAlgError) as exc:
        return finish(f"Numerical fit failed: {exc}")
    settings.update({"noise": ("signed_cross_section_residual_MAD_estimated" if obs_kind == "cross_section" else "v1_residual_MAD_estimated") if estimated else "supplied_diagonal_uncertainty",
                     "column_scales": scales.tolist(), "common_points": int(nu.size)})
    if estimated:
        warnings.append("Noise estimated from fitted residual MAD; displayed sigma is an estimated-noise statistic")
    coeff = x / scales
    active = np.flatnonzero(x[:nr] > 0)
    actcols = np.r_[active, np.arange(nr, raw.shape[1])]
    A = design / sigma[:, None]
    try:
        cov = np.linalg.pinv(A[:, actcols].T @ A[:, actcols])
    except np.linalg.LinAlgError as exc:
        return finish(f"Covariance calculation failed: {exc}")
    uncertainties = np.zeros(nr)
    uncertainties[active] = np.sqrt(np.clip(np.diag(cov)[:len(active)], 0, None)) / scales[active]
    for i in range(nr):
        if i not in active:
            uncertainties[i] = 1 / np.linalg.norm(A[:, i]) / scales[i]
    normalized = A[:, :nr] / np.linalg.norm(A[:, :nr], axis=0)
    similarity = normalized.T @ normalized
    for i in range(nr):
        for j in range(i + 1, nr):
            if similarity[i, j] > .8:
                warnings.append(f"{eligible[i][0].molecule} / {eligible[j][0].molecule}: overlapping template shapes ({similarity[i,j]:.2f}); amplitudes may be degenerate")
    evaluated, curves = {}, {}
    for i, (ref, _, _) in enumerate(eligible):
        delta = 0.
        if x[i] > 0:
            try:
                _, without = solve(sigma, cols[cols != i])
            except (ValueError, np.linalg.LinAlgError) as exc:
                return finish(f"Drop-one refit failed: {exc}")
            delta = max(without - chi2, 0.)
        significance = float(np.sqrt(delta))
        evaluated[ref.dataset_id] = ComponentResult(ref.dataset_id, ref.molecule, ref.modality, significance,
            "evaluated", "Above conditional fit threshold" if x[i] > 0 and significance >= threshold else "Below conditional fit threshold",
            float(coeff[i]), float(uncertainties[i]), delta)
        curves[ref.dataset_id] = tuple(float(v) for v in K[:, i] * coeff[i])
    components = tuple(evaluated[r.dataset_id] if r.dataset_id in evaluated else ComponentResult(
        r.dataset_id, r.molecule, r.modality, None, "blocked", blocked.get(r.dataset_id, "Unavailable")) for r in references)
    return IdentificationResult(components, tuple(nu.tolist()), tuple(target.tolist()), tuple((raw @ coeff).tolist()),
        curves, tuple(warnings), settings, provenance, estimated, chi2,
        chi2 / max(nu.size - np.count_nonzero(x), 1), tuple(sigma.tolist()))


def result_to_record(result: IdentificationResult) -> dict:
    """JSON-ready integrity envelope binding arrays, inputs, settings and results."""
    from dataclasses import asdict
    payload = asdict(result)
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {"schema": "ecas-laboratory-identification-v1", "payload": payload,
            "sha256": hashlib.sha256(serialized.encode()).hexdigest()}


def verify_record(record: dict) -> bool:
    try:
        encoded = json.dumps(record["payload"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        return record["schema"] == "ecas-laboratory-identification-v1" and hashlib.sha256(encoded).hexdigest() == record["sha256"]
    except (KeyError, TypeError, ValueError):
        return False


def reproduce_record(record: dict) -> IdentificationResult:
    """Recompute from integrity-checked array snapshots, without requiring source files.

    Integrity is an internal checksum, not a source authenticity signature or
    evidence of scientific validation. Current installed solver/version is used.
    """
    if not verify_record(record):
        raise ValueError("Identification record integrity/schema check failed")
    payload = record["payload"]
    def restore(snapshot):
        return SpectrumData(Path(snapshot["source_file"]), tuple(snapshot["rows"]), tuple(snapshot["columns"]),
            snapshot["axis_unit"], snapshot["signal_unit"], snapshot["signal_type"],
            tuple(snapshot["warnings"]), tuple(tuple(v) for v in snapshot.get("metadata", ())))
    provenance = payload["provenance"]
    refs = [ReferenceDataset(r["dataset_id"], r["molecule"], r["modality"], restore(r["spectrum_snapshot"]),
                             r["metadata"], r["sha256"], Path(r["path"])) for r in provenance["references"]]
    return identify(restore(provenance["observation_snapshot"]), refs,
                    observation_metadata=provenance["observation_metadata"],
                    threshold=payload["settings"]["threshold"], continuum=payload["settings"]["continuum"])
