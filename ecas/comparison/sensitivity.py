"""Parameter sensitivity and observational constraints analysis.

Evaluates "What can this observation constrain?" by computing forward-model
perturbations around a physical baseline across the observation's actual wavelength grid.
Supports:
- Temperature T (+/- 50 K)
- Reference planet radius Rp (+/- 0.02 R_J or +/- 2%)
- Molecular volume mixing ratios (+/- 0.5 dex)
- Cloud top pressure P_cloud (+/- 0.5 dex)
- Haze multiplier (+/- 50%)

Distinguishes local model sensitivity from posterior uncertainty or detection
significance. Relates spectral changes to empirical uncertainties (Delta / sigma)
when available without inventing noise when missing.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Sequence

import numpy as np

from ecas.comparison.alignment import integrate_model_over_bins
from ecas.comparison.eligibility import ComparisonInput
from ecas.comparison.inputs import audit_observation_bin_semantics, extract_observation_bin_edges
from ecas.comparison.model_generator import (
    MolecularComponentSpec,
    R_JUPITER_M,
    R_SUN_M,
    generate_isothermal_transmission_model,
    get_planet_preset,
)
from ecas.models.spectrum import SpectrumData


SCIENTIFIC_BOUNDARY_NOTICE = (
    "Local model sensitivity quantifies forward-model responses to parameter perturbations "
    "over the observed wavelength coverage. It is NOT a posterior probability distribution, "
    "retrieval constraint, parameter measurement, or molecular detection significance. "
    "Predictions are forward model simulations conditioned on the specified parameters."
)


@dataclass(frozen=True)
class SensitivityPerturbation:
    """Spectral change resulting from a single parameter perturbation."""

    parameter_name: str
    display_name: str
    unit: str
    baseline_value: float
    perturbed_value: float
    perturbation_delta: float
    perturbation_direction: str  # "+" or "-"
    perturbed_spectrum: tuple[float, ...]
    delta_spectrum: tuple[float, ...]  # perturbed - baseline
    max_abs_delta: float
    rms_delta: float
    relative_to_uncertainty: tuple[float, ...] | None  # delta / sigma
    max_significance_ratio: float | None
    has_weak_sensitivity: bool
    weak_sensitivity_explanation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ParameterDegeneracy:
    """Correlation between two parameter perturbation vectors across the observed grid."""

    param_a: str
    param_b: str
    correlation_coefficient: float
    is_degenerate: bool
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SensitivityAnalysisResult:
    """Comprehensive sensitivity analysis of forward model parameters against an observation."""

    target_id: str
    wavelengths_um: tuple[float, ...]
    baseline_parameters: dict[str, Any]
    baseline_spectrum: tuple[float, ...]
    uncertainties: tuple[float, ...] | None
    uncertainty_kind: str  # 'observational_1sigma' or 'unweighted'
    perturbations: tuple[SensitivityPerturbation, ...]
    degeneracies: tuple[ParameterDegeneracy, ...]
    warnings: tuple[str, ...]
    scientific_boundary_notice: str = SCIENTIFIC_BOUNDARY_NOTICE

    @property
    def weak_parameters(self) -> tuple[SensitivityPerturbation, ...]:
        return tuple(p for p in self.perturbations if p.has_weak_sensitivity)

    @property
    def degenerate_pairs(self) -> tuple[ParameterDegeneracy, ...]:
        return tuple(d for d in self.degeneracies if d.is_degenerate)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "wavelengths_um": list(self.wavelengths_um),
            "baseline_parameters": self.baseline_parameters,
            "baseline_spectrum": list(self.baseline_spectrum),
            "uncertainties": list(self.uncertainties) if self.uncertainties is not None else None,
            "uncertainty_kind": self.uncertainty_kind,
            "perturbations": [p.to_dict() for p in self.perturbations],
            "degeneracies": [d.to_dict() for d in self.degeneracies],
            "warnings": list(self.warnings),
            "scientific_boundary_notice": self.scientific_boundary_notice,
        }


def _compute_cosine_correlation(v1: np.ndarray, v2: np.ndarray) -> float:
    """Compute Pearson correlation coefficient between two delta spectra."""
    denom = (np.std(v1) * np.std(v2))
    if denom <= 1e-15:
        # Fall back to cosine similarity if flat
        norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)
        if norm_product <= 1e-15:
            return 0.0
        return float(np.dot(v1, v2) / norm_product)
    return float(np.corrcoef(v1, v2)[0, 1])


def compute_parameter_sensitivity(
    observation: SpectrumData | ComparisonInput,
    *,
    planet_preset_id: str = "wasp-39b",
    temperature_k: float | None = None,
    planet_radius_m: float | None = None,
    stellar_radius_m: float | None = None,
    gravity_m_s2: float | None = None,
    reference_pressure_bar: float = 0.01,
    cloud_pressure_bar: float | None = 0.01,
    haze_multiplier: float = 1.0,
    components: Sequence[MolecularComponentSpec] = (),
    delta_temp_k: float = 50.0,
    delta_radius_fraction: float = 0.02,
    delta_log_abundance_dex: float = 0.5,
    delta_log_cloud_dex: float = 0.5,
    source_sha256: str | None = None,
) -> SensitivityAnalysisResult:
    """Compute forward-model parameter sensitivity against an observation's wavelength grid.

    Calculates spectral perturbations and compares them to measurement uncertainties.
    Identifies parameter degeneracies where multiple parameters produce collinear spectral effects.
    """
    preset = get_planet_preset(planet_preset_id)
    t_base = float(temperature_k if temperature_k is not None else preset.temperature_k)
    rp_base = float(planet_radius_m if planet_radius_m is not None else preset.planet_radius_m)
    rstar_base = float(stellar_radius_m if stellar_radius_m is not None else preset.stellar_radius_m)
    g_base = float(gravity_m_s2 if gravity_m_s2 is not None else preset.gravity_m_s2)
    mu_base = float(preset.mean_molecular_weight_u)
    p_cloud_base = cloud_pressure_bar if cloud_pressure_bar is not None else preset.default_cloud_pressure_bar

    # Extract coordinates & uncertainties
    if isinstance(observation, SpectrumData):
        target_id = str(observation.source_file)
        lam_arr = np.array([float(r["wavelength"]) for r in observation.rows], dtype=float)
        # Check if uncertainties exist
        if "uncertainty" in observation.columns:
            try:
                sigma_arr = np.array([float(r["uncertainty"]) for r in observation.rows], dtype=float)
                if not np.isfinite(sigma_arr).all() or np.any(sigma_arr <= 0):
                    sigma_arr = None
            except Exception:
                sigma_arr = None
        else:
            sigma_arr = None
    elif isinstance(observation, ComparisonInput):
        target_id = str(observation.source_id)
        lam_arr = np.asarray(observation.coordinates, dtype=float)
        if observation.sigma is not None:
            sigma_arr = np.asarray(observation.sigma, dtype=float)
            if not np.isfinite(sigma_arr).all() or np.any(sigma_arr <= 0):
                sigma_arr = None
        else:
            sigma_arr = None
    else:
        raise TypeError(f"Unsupported observation type: {type(observation)!r}")

    if len(lam_arr) < 3 or not np.isfinite(lam_arr).all() or np.any(lam_arr <= 0):
        raise ValueError("Observation must contain >= 3 finite positive wavelength coordinates")

    # Sort strictly increasing
    order = np.argsort(lam_arr)
    target_wavelengths = lam_arr[order]
    uncertainty_vals = sigma_arr[order] if sigma_arr is not None else None
    uncertainty_kind = "observational_1sigma" if uncertainty_vals is not None else "unweighted"

    warnings_list: list[str] = []
    if uncertainty_vals is None:
        warnings_list.append(
            "Observation has no positive 1-sigma uncertainty column; perturbations are reported in raw transit depth units without noise weighting."
        )

    # 1. Compute Baseline Forward Model
    baseline_model = generate_isothermal_transmission_model(
        target_wavelengths_um=target_wavelengths,
        temperature_k=t_base,
        gravity_m_s2=g_base,
        planet_radius_m=rp_base,
        stellar_radius_m=rstar_base,
        reference_pressure_bar=reference_pressure_bar,
        mean_molecular_weight_u=mu_base,
        components=components,
        cloud_pressure_bar=p_cloud_base,
        haze_multiplier=haze_multiplier,
        signal_unit="percent",
    )
    y_baseline = np.asarray(baseline_model.comparison_input.values, dtype=float)

    # 2. Define Parameter Variations
    perturbations_spec: list[dict[str, Any]] = []

    # Temperature +/- delta_T
    t_plus = min(3000.0, t_base + delta_temp_k)
    t_minus = max(150.0, t_base - delta_temp_k)
    perturbations_spec.append({
        "param": "temperature_k",
        "display": "Temperature (T)",
        "unit": "K",
        "base": t_base,
        "perturbed": t_plus,
        "delta": t_plus - t_base,
        "dir": "+",
        "kwargs": {"temperature_k": t_plus},
    })
    perturbations_spec.append({
        "param": "temperature_k",
        "display": "Temperature (T)",
        "unit": "K",
        "base": t_base,
        "perturbed": t_minus,
        "delta": t_minus - t_base,
        "dir": "-",
        "kwargs": {"temperature_k": t_minus},
    })

    # Radius +/- delta_radius
    rp_plus = rp_base * (1.0 + delta_radius_fraction)
    rp_minus = rp_base * (1.0 - delta_radius_fraction)
    perturbations_spec.append({
        "param": "planet_radius_m",
        "display": "Planet Radius (Rp)",
        "unit": "R_J",
        "base": rp_base / R_JUPITER_M,
        "perturbed": rp_plus / R_JUPITER_M,
        "delta": (rp_plus - rp_base) / R_JUPITER_M,
        "dir": "+",
        "kwargs": {"planet_radius_m": rp_plus},
    })
    perturbations_spec.append({
        "param": "planet_radius_m",
        "display": "Planet Radius (Rp)",
        "unit": "R_J",
        "base": rp_base / R_JUPITER_M,
        "perturbed": rp_minus / R_JUPITER_M,
        "delta": (rp_minus - rp_base) / R_JUPITER_M,
        "dir": "-",
        "kwargs": {"planet_radius_m": rp_minus},
    })

    # Cloud pressure +/- delta_log_cloud_dex
    if p_cloud_base is not None and p_cloud_base > 0:
        factor_cloud = 10.0 ** delta_log_cloud_dex
        p_c_plus = min(100.0, p_cloud_base * factor_cloud)
        p_c_minus = max(1e-5, p_cloud_base / factor_cloud)
        perturbations_spec.append({
            "param": "cloud_pressure_bar",
            "display": "Cloud Deck Pressure (Pcloud)",
            "unit": "bar",
            "base": p_cloud_base,
            "perturbed": p_c_plus,
            "delta": p_c_plus - p_cloud_base,
            "dir": "+",
            "kwargs": {"cloud_pressure_bar": p_c_plus},
        })
        perturbations_spec.append({
            "param": "cloud_pressure_bar",
            "display": "Cloud Deck Pressure (Pcloud)",
            "unit": "bar",
            "base": p_cloud_base,
            "perturbed": p_c_minus,
            "delta": p_c_minus - p_cloud_base,
            "dir": "-",
            "kwargs": {"cloud_pressure_bar": p_c_minus},
        })

    # Molecular abundances for active components
    for comp in components:
        if comp.vmr > 0:
            factor_vmr = 10.0 ** delta_log_abundance_dex
            vmr_plus = min(0.5, comp.vmr * factor_vmr)
            vmr_minus = max(1e-8, comp.vmr / factor_vmr)

            # Build perturbed component list
            comps_plus = [
                MolecularComponentSpec(
                    formula=c.formula,
                    isotopologue=c.isotopologue,
                    dataset=c.dataset,
                    version=c.version,
                    source_sha256=c.source_sha256,
                    vmr=vmr_plus if c.formula == comp.formula else c.vmr,
                    wavelengths_um=c.wavelengths_um,
                    cross_sections_cm2=c.cross_sections_cm2,
                    reference_temperature_k=c.reference_temperature_k,
                    broadening_note=c.broadening_note,
                )
                for c in components
            ]
            comps_minus = [
                MolecularComponentSpec(
                    formula=c.formula,
                    isotopologue=c.isotopologue,
                    dataset=c.dataset,
                    version=c.version,
                    source_sha256=c.source_sha256,
                    vmr=vmr_minus if c.formula == comp.formula else c.vmr,
                    wavelengths_um=c.wavelengths_um,
                    cross_sections_cm2=c.cross_sections_cm2,
                    reference_temperature_k=c.reference_temperature_k,
                    broadening_note=c.broadening_note,
                )
                for c in components
            ]

            perturbations_spec.append({
                "param": f"vmr_{comp.formula}",
                "display": f"{comp.formula} Abundance (VMR)",
                "unit": "dex",
                "base": comp.vmr,
                "perturbed": vmr_plus,
                "delta": delta_log_abundance_dex,
                "dir": "+",
                "kwargs": {"components": comps_plus},
            })
            perturbations_spec.append({
                "param": f"vmr_{comp.formula}",
                "display": f"{comp.formula} Abundance (VMR)",
                "unit": "dex",
                "base": comp.vmr,
                "perturbed": vmr_minus,
                "delta": -delta_log_abundance_dex,
                "dir": "-",
                "kwargs": {"components": comps_minus},
            })

    # 3. Evaluate Perturbations
    evaluated_perturbations: list[SensitivityPerturbation] = []
    delta_vectors: dict[str, np.ndarray] = {}

    for spec_item in perturbations_spec:
        # Merge kwargs with baseline
        kw = {
            "target_wavelengths_um": target_wavelengths,
            "temperature_k": t_base,
            "gravity_m_s2": g_base,
            "planet_radius_m": rp_base,
            "stellar_radius_m": rstar_base,
            "reference_pressure_bar": reference_pressure_bar,
            "mean_molecular_weight_u": mu_base,
            "components": components,
            "cloud_pressure_bar": p_cloud_base,
            "haze_multiplier": haze_multiplier,
            "signal_unit": "percent",
        }
        kw.update(spec_item["kwargs"])

        model_pert = generate_isothermal_transmission_model(**kw)
        y_pert = np.asarray(model_pert.comparison_input.values, dtype=float)
        diff = y_pert - y_baseline

        key = f"{spec_item['param']}_{spec_item['dir']}"
        delta_vectors[key] = diff

        max_delta = float(np.max(np.abs(diff)))
        rms_delta = float(np.sqrt(np.mean(diff ** 2)))

        sig_ratio: tuple[float, ...] | None = None
        max_sig: float | None = None
        has_weak = False
        weak_exp: str | None = None

        if uncertainty_vals is not None:
            with np.errstate(divide="ignore", invalid="ignore"):
                ratios = np.abs(diff) / uncertainty_vals
                ratios = np.where(np.isfinite(ratios), ratios, 0.0)
                sig_ratio = tuple(float(v) for v in (diff / uncertainty_vals))
                max_sig = float(np.max(ratios))
            if max_sig < 0.10:
                has_weak = True
                weak_exp = (
                    f"Parameter perturbation changes model by at most {max_sig:.2f} sigma across the observed band; "
                    "current observational uncertainty exceeds parameter influence."
                )
        else:
            if max_delta < 1e-4:  # less than 1 ppm in percent units (0.0001%)
                has_weak = True
                weak_exp = f"Maximum model change is {max_delta*10000:.2f} ppm; negligible influence on spectrum."

        evaluated_perturbations.append(
            SensitivityPerturbation(
                parameter_name=spec_item["param"],
                display_name=spec_item["display"],
                unit=spec_item["unit"],
                baseline_value=float(spec_item["base"]),
                perturbed_value=float(spec_item["perturbed"]),
                perturbation_delta=float(spec_item["delta"]),
                perturbation_direction=spec_item["dir"],
                perturbed_spectrum=tuple(float(v) for v in y_pert),
                delta_spectrum=tuple(float(v) for v in diff),
                max_abs_delta=max_delta,
                rms_delta=rms_delta,
                relative_to_uncertainty=sig_ratio,
                max_significance_ratio=max_sig,
                has_weak_sensitivity=has_weak,
                weak_sensitivity_explanation=weak_exp,
            )
        )

    # 4. Check Parameter Degeneracies
    degeneracies: list[ParameterDegeneracy] = []
    # Compare distinct positive perturbation directions
    pos_keys = [k for k in delta_vectors if k.endswith("_+")]
    for i in range(len(pos_keys)):
        for j in range(i + 1, len(pos_keys)):
            k1, k2 = pos_keys[i], pos_keys[j]
            v1, v2 = delta_vectors[k1], delta_vectors[k2]
            corr = _compute_cosine_correlation(v1, v2)
            is_deg = abs(corr) >= 0.85
            p1_name = k1.replace("_+", "")
            p2_name = k2.replace("_+", "")

            if is_deg:
                exp = (
                    f"High correlation (r={corr:.2f}) between {p1_name} and {p2_name} spectral responses. "
                    "Perturbing one parameter mimics changes in the other over this wavelength coverage, "
                    "indicating potential observational degeneracy."
                )
            else:
                exp = f"Low to moderate correlation (r={corr:.2f}); parameter effects are distinguishable."

            degeneracies.append(
                ParameterDegeneracy(
                    param_a=p1_name,
                    param_b=p2_name,
                    correlation_coefficient=corr,
                    is_degenerate=is_deg,
                    explanation=exp,
                )
            )

    return SensitivityAnalysisResult(
        target_id=target_id,
        wavelengths_um=tuple(float(v) for v in target_wavelengths),
        baseline_parameters={
            "planet_preset_id": planet_preset_id,
            "temperature_k": t_base,
            "gravity_m_s2": g_base,
            "planet_radius_m": rp_base,
            "planet_radius_rj": rp_base / R_JUPITER_M,
            "stellar_radius_m": rstar_base,
            "reference_pressure_bar": reference_pressure_bar,
            "mean_molecular_weight_u": mu_base,
            "cloud_pressure_bar": p_cloud_base,
            "haze_multiplier": haze_multiplier,
            "components": [asdict(c) for c in components],
        },
        baseline_spectrum=tuple(float(v) for v in y_baseline),
        uncertainties=tuple(float(v) for v in uncertainty_vals) if uncertainty_vals is not None else None,
        uncertainty_kind=uncertainty_kind,
        perturbations=tuple(evaluated_perturbations),
        degeneracies=tuple(degeneracies),
        warnings=tuple(warnings_list),
        scientific_boundary_notice=SCIENTIFIC_BOUNDARY_NOTICE,
    )

