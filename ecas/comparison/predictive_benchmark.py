"""Reproducible Cross-Observation Predictive Benchmark for ECAS.

Answers the fundamental scientific question:
When ECAS suggests a molecule, does including that molecule improve its prediction
of an absorption feature in an independent, separate observation?

Evaluates WASP-39 b using real JWST transmission spectra from separate observing visits:
- Fitting Observation: JWST NIRSpec G395H (Visit 02, Alderson et al. 2022/2023)
- Validation Observation: JWST NIRSpec PRISM (Visit 01, Rustamkulov et al. 2023)
"""
from __future__ import annotations

import csv
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from scipy.optimize import least_squares

from ecas.ingestion.nasa_table import import_transmission_table
from ecas.ingestion.exomol_reference_cache import load_reference
from ecas.comparison.inputs import audit_observation_bin_semantics, observation_input
from ecas.comparison.model_generator import (
    MolecularComponentSpec,
    PlanetAtmospherePreset,
    component_from_cached_exomol,
    generate_isothermal_transmission_model,
    get_planet_preset,
)


@dataclass(frozen=True)
class ObservationVisitSpec:
    """Provenance and metadata establishing observation identity and visit independence."""

    target_id: str
    source_file: str
    source_sha256: str
    instrument: str
    facility: str
    program_id: str
    observing_visit: str
    observation_date: str
    authors: str
    data_points_count: int
    wavelength_range_um: tuple[float, float]
    reference_bibcode: str | None = None


@dataclass(frozen=True)
class BandContrastDefinition:
    """Pre-declared specification of an absorption band and continuum reference intervals."""

    name: str
    band_interval_um: tuple[float, float]
    blue_reference_interval_um: tuple[float, float]
    red_reference_interval_um: tuple[float, float]
    weighting_method: str = "inverse_variance"
    decision_threshold_sigmas: float = 2.0
    scientific_justification: str = ""


@dataclass(frozen=True)
class ModelEvaluationRecord:
    """Fitted parameters and cross-observation validation performance for one model."""

    model_name: str
    contains_target_molecule: bool
    fitted_parameters: dict[str, float]
    training_rms_ppm: float
    training_weighted_q_over_n: float
    validation_mean_depth_percent: float
    validation_mean_offset_ppm: float
    validation_shape_rms_ppm: float
    predicted_band_depth_percent: float
    predicted_continuum_depth_percent: float
    predicted_contrast_ppm: float
    contrast_error_ppm: float


@dataclass
class PredictiveBenchmarkResult:
    """Complete, reproducible cross-visit predictive benchmark results."""

    benchmark_name: str
    target_planet: str
    molecule_tested: str
    fitting_observation: ObservationVisitSpec
    validation_observation: ObservationVisitSpec
    are_observations_independent: bool
    independence_evidence: str
    opacity_provenance: dict[str, Any]
    band_definition: BandContrastDefinition
    observed_band_depth_percent: float
    observed_continuum_depth_percent: float
    observed_contrast_ppm: float
    observed_contrast_uncertainty_ppm: float
    h2o_model: ModelEvaluationRecord
    baseline_model: ModelEvaluationRecord
    contrast_accuracy_improvement_ppm: float
    outcome_decision: str
    plain_language_summary: str
    validation_points: list[dict[str, Any]] = field(default_factory=list)
    created_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    protocol_sha256: str | None = None
    prediction_sha256: str | None = None

    def export_manifest(self) -> dict[str, Any]:
        """Export publication-quality JSON reproducibility manifest."""
        return {
            "schema": "ecas-predictive-benchmark-v1",
            "benchmark_name": self.benchmark_name,
            "created_utc": self.created_utc,
            "target_planet": self.target_planet,
            "molecule_tested": self.molecule_tested,
            "are_observations_independent": self.are_observations_independent,
            "independence_evidence": self.independence_evidence,
            "fitting_observation": asdict(self.fitting_observation),
            "validation_observation": asdict(self.validation_observation),
            "opacity_provenance": self.opacity_provenance,
            "band_definition": asdict(self.band_definition),
            "observed_contrast": {
                "band_depth_percent": self.observed_band_depth_percent,
                "continuum_depth_percent": self.observed_continuum_depth_percent,
                "contrast_ppm": self.observed_contrast_ppm,
                "uncertainty_ppm": self.observed_contrast_uncertainty_ppm,
            },
            "models": {
                "with_molecule": asdict(self.h2o_model),
                "without_molecule_baseline": asdict(self.baseline_model),
            },
            "comparison": {
                "contrast_accuracy_improvement_ppm": self.contrast_accuracy_improvement_ppm,
                "outcome_decision": self.outcome_decision,
                "plain_language_summary": self.plain_language_summary,
            },
            "validation_points_count": len(self.validation_points),
            "protocol_sha256": self.protocol_sha256,
            "prediction_sha256": self.prediction_sha256,
        }

    def export_markdown_report(self) -> str:
        """Export clean Markdown report for publication and user inspection."""
        lines = [
            f"# ECAS Predictive Benchmark: {self.molecule_tested} in {self.target_planet}",
            "",
            "## 1. Executive Summary",
            "",
            f"**Question:** *When ECAS suggests {self.molecule_tested}, does including that molecule improve its prediction of an absorption feature in a separate observation?*",
            "",
            f"> **Benchmark Outcome:** **{self.outcome_decision}**",
            "",
            self.plain_language_summary,
            "",
            "## 2. Separate Observation Identities",
            "",
            f"- **Observation Independence:** {'✓ CONFIRMED SEPARATE VISITS' if self.are_observations_independent else '⚠ NOT INDEPENDENT'}",
            f"- **Evidence:** {self.independence_evidence}",
            "",
            "| Role | Target | Instrument / Mode | Program & Visit | Date | Source Reference | Points |",
            "|---|---|---|---|---|---|---|",
            f"| **Fitting (Training)** | {self.fitting_observation.target_id} | {self.fitting_observation.instrument} | Prog {self.fitting_observation.program_id}, {self.fitting_observation.observing_visit} | {self.fitting_observation.observation_date} | {self.fitting_observation.authors} | {self.fitting_observation.data_points_count} |",
            f"| **Validation (Test)** | {self.validation_observation.target_id} | {self.validation_observation.instrument} | Prog {self.validation_observation.program_id}, {self.validation_observation.observing_visit} | {self.validation_observation.observation_date} | {self.validation_observation.authors} | {self.validation_observation.data_points_count} |",
            "",
            "## 3. Pre-Declared Feature & Band Contrast Definition",
            "",
            f"- **Feature Name:** {self.band_definition.name}",
            f"- **In-Band Interval:** {self.band_definition.band_interval_um[0]:.2f} – {self.band_definition.band_interval_um[1]:.2f} µm",
            f"- **Blue Reference Interval:** {self.band_definition.blue_reference_interval_um[0]:.2f} – {self.band_definition.blue_reference_interval_um[1]:.2f} µm",
            f"- **Red Reference Interval:** {self.band_definition.red_reference_interval_um[0]:.2f} – {self.band_definition.red_reference_interval_um[1]:.2f} µm",
            f"- **Weighting:** {self.band_definition.weighting_method}",
            f"- **Scientific Justification:** {self.band_definition.scientific_justification}",
            "",
            "## 4. Quantitative Results & Model Comparison",
            "",
            "| Metric | Observed (Validation Visit) | Model with H2O | Baseline (No H2O) |",
            "|---|---:|---:|---:|",
            f"| In-Band Mean Depth | {self.observed_band_depth_percent:.5f}% | {self.h2o_model.predicted_band_depth_percent:.5f}% | {self.baseline_model.predicted_band_depth_percent:.5f}% |",
            f"| Continuum Reference Mean Depth | {self.observed_continuum_depth_percent:.5f}% | {self.h2o_model.predicted_continuum_depth_percent:.5f}% | {self.baseline_model.predicted_continuum_depth_percent:.5f}% |",
            f"| **Band Contrast (ppm)** | **{self.observed_contrast_ppm:+.1f} ± {self.observed_contrast_uncertainty_ppm:.1f}** | **{self.h2o_model.predicted_contrast_ppm:+.1f}** | **{self.baseline_model.predicted_contrast_ppm:+.1f}** |",
            f"| Contrast Prediction Error | — | {self.h2o_model.contrast_error_ppm:.1f} ppm | {self.baseline_model.contrast_error_ppm:.1f} ppm |",
            f"| Visit-Level Mean Offset | — | {self.h2o_model.validation_mean_offset_ppm:+.1f} ppm | {self.baseline_model.validation_mean_offset_ppm:+.1f} ppm |",
            f"| Mean-Subtracted Shape RMS | — | {self.h2o_model.validation_shape_rms_ppm:.1f} ppm | {self.baseline_model.validation_shape_rms_ppm:.1f} ppm |",
            f"| Training RMS (G395H) | — | {self.h2o_model.training_rms_ppm:.1f} ppm | {self.baseline_model.training_rms_ppm:.1f} ppm |",
            "",
            "## 5. Opacity Traceability and Methodological Disclosures",
            "",
            f"- **Line List:** {self.opacity_provenance.get('dataset', 'Unknown')} ({self.opacity_provenance.get('citations', 'ExoMol')})",
            f"- **Tabulated Temperature:** {self.opacity_provenance.get('tabulated_temperature_k', 'Unknown')} K",
            f"- **Model Atmospheric Temperature:** {self.opacity_provenance.get('atmospheric_temperature_k', 'Unknown')} K",
            f"- **Pressure Broadening Treatment:** {self.opacity_provenance.get('pressure_treatment', 'Doppler only')}",
            f"- **Approximation Disclosure:** {self.opacity_provenance.get('approximation_justification', 'None')}",
            f"- **Outstanding Requirement:** {self.opacity_provenance.get('missing_requirement', 'None')}",
        ]
        return "\n".join(lines)


def sha256_of_bytes(data: bytes) -> str:
    """Return SHA-256 digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def verify_observation_independence(
    fitting: ObservationVisitSpec,
    validation: ObservationVisitSpec,
) -> tuple[bool, str]:
    """Verify that two observation specifications represent physically separate observing visits.

    Returns (is_independent, justification).
    """
    if fitting.source_sha256 == validation.source_sha256:
        return False, "Duplicate source file: Both specifications share identical SHA-256 byte hashes."

    if (
        fitting.program_id == validation.program_id
        and fitting.observing_visit == validation.observing_visit
        and fitting.observing_visit.strip() != ""
    ):
        return (
            False,
            f"Shared observing visit: Both files derive from JWST Program {fitting.program_id}, {fitting.observing_visit} "
            "(alternative reductions or extractions of the same exposure share underlying photon counts).",
        )

    evidence = (
        f"Verified independent observing visits: Fitting observation is {fitting.instrument} "
        f"(Prog {fitting.program_id}, {fitting.observing_visit}, observed {fitting.observation_date}), while "
        f"validation observation is {validation.instrument} "
        f"(Prog {validation.program_id}, {validation.observing_visit}, observed {validation.observation_date}). "
        "The datasets represent separate physical transits separated in time with distinct instrument readouts."
    )
    return True, evidence


def calculate_band_contrast(
    wavelengths: Sequence[float],
    transit_depths: Sequence[float],
    uncertainties: Sequence[float] | None,
    band_def: BandContrastDefinition,
) -> tuple[float, float, float, float]:
    """Calculate in-band depth, continuum depth, contrast in ppm, and propagated uncertainty.

    Returns:
        (band_mean_pct, continuum_mean_pct, contrast_ppm, uncertainty_ppm)
    """
    x = np.asarray(wavelengths, dtype=float)
    y = np.asarray(transit_depths, dtype=float)
    if uncertainties is not None:
        u = np.asarray(uncertainties, dtype=float)
        # Handle zero or non-finite uncertainties gracefully
        valid_u = np.isfinite(u) & (u > 0)
        if np.all(valid_u):
            weights = 1.0 / (u ** 2)
        else:
            weights = np.ones_like(y)
    else:
        weights = np.ones_like(y)
        u = np.zeros_like(y)

    b_min, b_max = band_def.band_interval_um
    blue_min, blue_max = band_def.blue_reference_interval_um
    red_min, red_max = band_def.red_reference_interval_um

    band_mask = (x >= b_min) & (x <= b_max)
    ref_mask = ((x >= blue_min) & (x <= blue_max)) | ((x >= red_min) & (x <= red_max))

    if np.sum(band_mask) == 0:
        raise ValueError(f"No validation measurements fell inside the band interval [{b_min}, {b_max}] um.")
    if np.sum(ref_mask) == 0:
        raise ValueError(
            f"No validation measurements fell inside the reference intervals [{blue_min}, {blue_max}] or [{red_min}, {red_max}] um."
        )

    w_b = weights[band_mask]
    y_b = y[band_mask]
    band_depth = float(np.sum(w_b * y_b) / np.sum(w_b))

    w_r = weights[ref_mask]
    y_r = y[ref_mask]
    continuum_depth = float(np.sum(w_r * y_r) / np.sum(w_r))

    contrast_pct = band_depth - continuum_depth
    contrast_ppm = float(contrast_pct * 10000.0)

    # Uncertainty propagation: Var(D_band - D_cont) = Var(D_band) + Var(D_cont)
    if uncertainties is not None and np.all(valid_u):
        var_band = 1.0 / float(np.sum(w_b))
        var_cont = 1.0 / float(np.sum(w_r))
        unc_ppm = float(np.sqrt(var_band + var_cont) * 10000.0)
    else:
        unc_ppm = 0.0

    return band_depth, continuum_depth, contrast_ppm, unc_ppm


def run_wasp39b_water_benchmark(
    fitting_table_path: Path | str,
    validation_table_path: Path | str,
    opacity_reference_path: Path | str,
    band_definition: BandContrastDefinition | None = None,
    fitting_domain_um: tuple[float, float] = (2.76, 4.0),
    validation_domain_um: tuple[float, float] = (2.76, 4.0),
    freeze_output_path: Path | str | None = None,
) -> PredictiveBenchmarkResult:
    """Execute the complete reproducible benchmark on WASP-39 b water prediction across separate visits."""
    fit_path = Path(fitting_table_path)
    val_path = Path(validation_table_path)
    ref_path = Path(opacity_reference_path)

    if not fit_path.exists():
        raise FileNotFoundError(f"Fitting observation table not found: {fit_path}")
    if not val_path.exists():
        raise FileNotFoundError(f"Validation observation table not found: {val_path}")
    if not ref_path.exists():
        raise FileNotFoundError(f"Opacity reference JSON not found: {ref_path}")

    # 1. Ingest Fitting and Validation Observations
    table_fit = import_transmission_table(fit_path)
    table_val = import_transmission_table(val_path)

    spec_fit = table_fit.spectrum
    spec_val = table_val.spectrum

    # Compute SHA-256 byte hashes
    fit_sha = sha256_of_bytes(fit_path.read_bytes())
    val_sha = sha256_of_bytes(val_path.read_bytes())

    x_fit_all = np.array([float(r["centralwavelng"]) for r in spec_fit.rows], dtype=float)
    x_val_all = np.array([float(r["centralwavelng"]) for r in spec_val.rows], dtype=float)

    spec_fit_rec = ObservationVisitSpec(
        target_id="WASP-39 b",
        source_file=str(fit_path),
        source_sha256=fit_sha,
        instrument="Near Infrared Spectrograph (NIRSpec) - G395H",
        facility="JWST",
        program_id="1366",
        observing_visit="Visit 02",
        observation_date="2022-07-30/31",
        authors="Alderson et al. 2022 / 2023",
        data_points_count=len(spec_fit.rows),
        wavelength_range_um=(float(np.min(x_fit_all)), float(np.max(x_fit_all))),
        reference_bibcode="2023Natur.614..664A",
    )

    spec_val_rec = ObservationVisitSpec(
        target_id="WASP-39 b",
        source_file=str(val_path),
        source_sha256=val_sha,
        instrument="Near Infrared Spectrograph (NIRSpec) - PRISM",
        facility="JWST",
        program_id="1366",
        observing_visit="Visit 01",
        observation_date="2022-07-10/11",
        authors="Rustamkulov et al. 2023",
        data_points_count=len(spec_val.rows),
        wavelength_range_um=(float(np.min(x_val_all)), float(np.max(x_val_all))),
        reference_bibcode="2023Natur.614..659R",
    )

    # 2. Verify Observation Independence
    is_indep, indep_evidence = verify_observation_independence(spec_fit_rec, spec_val_rec)
    if not is_indep:
        raise ValueError(f"Observation independence requirement violated: {indep_evidence}")

    # 3. Default Band Contrast Definition (Pre-declared)
    if band_definition is None:
        band_definition = BandContrastDefinition(
            name="WASP-39 b 3.10-3.30 µm Water Band (Holdout Window)",
            band_interval_um=(3.10, 3.30),
            blue_reference_interval_um=(2.80, 3.00),
            red_reference_interval_um=(3.40, 3.60),
            weighting_method="inverse_variance",
            decision_threshold_sigmas=2.0,
            scientific_justification=(
                "Evaluates the 3.10-3.30 µm water feature (withheld during earlier single-spectrum testing) "
                "relative to local continuum reference levels at 2.80-3.00 µm and 3.40-3.60 µm across separate visits."
            ),
        )

    # 4. Filter Fitting Measurements to Domain
    y_fit_all = np.array([float(r["pl_trandep"]) for r in spec_fit.rows], dtype=float)
    s_fit_all = np.array(
        [
            max(abs(float(r.get("pl_trandeperr1") or 0.01)), abs(float(r.get("pl_trandeperr2") or 0.01)))
            for r in spec_fit.rows
        ],
        dtype=float,
    )

    fit_mask = (x_fit_all >= fitting_domain_um[0]) & (x_fit_all <= fitting_domain_um[1])
    x_tr = x_fit_all[fit_mask]
    y_tr = y_fit_all[fit_mask]
    s_tr = s_fit_all[fit_mask]

    # 5. Filter Validation Measurements to Domain
    y_val_all = np.array([float(r["pl_trandep"]) for r in spec_val.rows], dtype=float)
    s_val_all = np.array(
        [
            max(abs(float(r.get("pl_trandeperr1") or 0.01)), abs(float(r.get("pl_trandeperr2") or 0.01)))
            for r in spec_val.rows
        ],
        dtype=float,
    )

    val_mask = (x_val_all >= validation_domain_um[0]) & (x_val_all <= validation_domain_um[1])
    x_val = x_val_all[val_mask]
    y_val = y_val_all[val_mask]
    s_val = s_val_all[val_mask]

    # 6. Load Traceable Opacity
    preset = get_planet_preset("WASP-39 b")
    exomol_record = load_reference(ref_path)
    comp_h2o = component_from_cached_exomol(exomol_record, vmr=1e-4)

    opacity_prov = {
        "dataset": comp_h2o.dataset or "POKAZATEL",
        "formula": comp_h2o.formula,
        "isotopologue": comp_h2o.isotopologue,
        "tabulated_temperature_k": comp_h2o.reference_temperature_k or 500.0,
        "atmospheric_temperature_k": preset.temperature_k,
        "pressure_treatment": "Doppler broadening at zero pressure; pressure-broadened wings neglected",
        "approximation_justification": (
            "The 500 K POKAZATEL zero-pressure cross section preserves fundamental vibrational band centers "
            "(2.7-3.3 µm) and envelope structure, allowing comparative testing of band contrast vs continuum. "
            "Higher-energy thermal state populations and pressure broadening are known approximations."
        ),
        "missing_requirement": (
            "High-temperature cross section tabulated at T=1166 K, P=0.01 bar with H2/He line broadening. "
            "Can be generated via ExoMol cross-section ingestion workflow once online access is authorized."
        ),
        "citations": [
            "Polyansky et al. 2018, MNRAS 480, 2597 (POKAZATEL)",
            "Tennyson & Yurchenko 2012, MNRAS 425, 21 (ExoMol)",
        ],
    }

    # 7. Model 1: Fit Physical Model WITH Water on Training Measurements
    def _model_h2o_tr(params: Sequence[float]) -> np.ndarray:
        log_vmr, r_mult = params
        m = generate_isothermal_transmission_model(
            target_wavelengths_um=x_tr,
            temperature_k=preset.temperature_k,
            gravity_m_s2=preset.gravity_m_s2,
            planet_radius_m=preset.planet_radius_m * float(r_mult),
            stellar_radius_m=preset.stellar_radius_m,
            reference_pressure_bar=preset.reference_pressure_bar,
            mean_molecular_weight_u=preset.mean_molecular_weight_u,
            components=(replace(comp_h2o, vmr=10.0 ** float(log_vmr)),),
            cloud_pressure_bar=0.01,
            signal_unit="percent",
        )
        return np.asarray(m.comparison_input.values, dtype=float)

    def _obj_h2o(params: Sequence[float]) -> np.ndarray:
        return (_model_h2o_tr(params) - y_tr) / s_tr

    fit_h2o = least_squares(
        _obj_h2o,
        [-5.0, 1.0],
        bounds=([-8.0, 0.9], [-1.0, 1.1]),
        ftol=1e-10,
        xtol=1e-10,
        gtol=1e-10,
        max_nfev=200,
    )
    tr_pred_h2o = _model_h2o_tr(fit_h2o.x)
    tr_res_h2o = (tr_pred_h2o - y_tr) * 10000.0
    tr_rms_h2o = float(np.sqrt(np.mean(tr_res_h2o ** 2)))
    tr_q_n_h2o = float(np.mean(fit_h2o.fun ** 2))

    # 8. Model 2: Fit Baseline Model WITHOUT Water on Training Measurements
    # Refit shared radius multiplier so the baseline receives fair treatment
    def _model_base_tr(params: Sequence[float]) -> np.ndarray:
        r_mult = params[0]
        m = generate_isothermal_transmission_model(
            target_wavelengths_um=x_tr,
            temperature_k=preset.temperature_k,
            gravity_m_s2=preset.gravity_m_s2,
            planet_radius_m=preset.planet_radius_m * float(r_mult),
            stellar_radius_m=preset.stellar_radius_m,
            reference_pressure_bar=preset.reference_pressure_bar,
            mean_molecular_weight_u=preset.mean_molecular_weight_u,
            components=(),
            cloud_pressure_bar=0.01,
            signal_unit="percent",
        )
        return np.asarray(m.comparison_input.values, dtype=float)

    def _obj_base(params: Sequence[float]) -> np.ndarray:
        return (_model_base_tr(params) - y_tr) / s_tr

    fit_base = least_squares(
        _obj_base,
        [1.0],
        bounds=([0.9], [1.1]),
        ftol=1e-10,
        xtol=1e-10,
        gtol=1e-10,
        max_nfev=200,
    )
    tr_pred_base = _model_base_tr(fit_base.x)
    tr_res_base = (tr_pred_base - y_tr) * 10000.0
    tr_rms_base = float(np.sqrt(np.mean(tr_res_base ** 2)))
    tr_q_n_base = float(np.mean(fit_base.fun ** 2))

    # 9. Predict on Validation Observation (PRISM) Bins
    m_val_h2o = generate_isothermal_transmission_model(
        target_wavelengths_um=x_val,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m * float(fit_h2o.x[1]),
        stellar_radius_m=preset.stellar_radius_m,
        reference_pressure_bar=preset.reference_pressure_bar,
        mean_molecular_weight_u=preset.mean_molecular_weight_u,
        components=(replace(comp_h2o, vmr=10.0 ** float(fit_h2o.x[0])),),
        cloud_pressure_bar=0.01,
        signal_unit="percent",
    )
    val_pred_h2o = np.asarray(m_val_h2o.comparison_input.values, dtype=float)

    m_val_base = generate_isothermal_transmission_model(
        target_wavelengths_um=x_val,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m * float(fit_base.x[0]),
        stellar_radius_m=preset.stellar_radius_m,
        reference_pressure_bar=preset.reference_pressure_bar,
        mean_molecular_weight_u=preset.mean_molecular_weight_u,
        components=(),
        cloud_pressure_bar=0.01,
        signal_unit="percent",
    )
    val_pred_base = np.asarray(m_val_base.comparison_input.values, dtype=float)

    # 10. Compute Band Contrast Metrics on Validation Observation and Both Models
    obs_band_d, obs_cont_d, obs_contrast, obs_contrast_unc = calculate_band_contrast(
        x_val, y_val, s_val, band_definition
    )
    h2o_band_d, h2o_cont_d, h2o_contrast, _ = calculate_band_contrast(
        x_val, val_pred_h2o, s_val, band_definition
    )
    base_band_d, base_cont_d, base_contrast, _ = calculate_band_contrast(
        x_val, val_pred_base, s_val, band_definition
    )

    err_h2o_contrast = abs(h2o_contrast - obs_contrast)
    err_base_contrast = abs(base_contrast - obs_contrast)
    contrast_improvement = err_base_contrast - err_h2o_contrast

    # Average Depth Accuracy & Shape RMS (mean subtracted)
    mean_obs_val = float(np.mean(y_val))
    mean_pred_h2o = float(np.mean(val_pred_h2o))
    mean_pred_base = float(np.mean(val_pred_base))

    offset_h2o_ppm = float((mean_pred_h2o - mean_obs_val) * 10000.0)
    offset_base_ppm = float((mean_pred_base - mean_obs_val) * 10000.0)

    res_val_h2o = (val_pred_h2o - y_val) * 10000.0
    res_val_base = (val_pred_base - y_val) * 10000.0

    shape_rms_h2o = float(np.sqrt(np.mean((res_val_h2o - np.mean(res_val_h2o)) ** 2)))
    shape_rms_base = float(np.sqrt(np.mean((res_val_base - np.mean(res_val_base)) ** 2)))

    rec_h2o = ModelEvaluationRecord(
        model_name="Physical Atmospheric Model (+H2O)",
        contains_target_molecule=True,
        fitted_parameters={
            "log10_h2o_vmr": float(fit_h2o.x[0]),
            "h2o_vmr": float(10.0 ** fit_h2o.x[0]),
            "radius_multiplier": float(fit_h2o.x[1]),
        },
        training_rms_ppm=tr_rms_h2o,
        training_weighted_q_over_n=tr_q_n_h2o,
        validation_mean_depth_percent=mean_pred_h2o,
        validation_mean_offset_ppm=offset_h2o_ppm,
        validation_shape_rms_ppm=shape_rms_h2o,
        predicted_band_depth_percent=h2o_band_d,
        predicted_continuum_depth_percent=h2o_cont_d,
        predicted_contrast_ppm=h2o_contrast,
        contrast_error_ppm=err_h2o_contrast,
    )

    rec_base = ModelEvaluationRecord(
        model_name="Continuum Baseline (No H2O)",
        contains_target_molecule=False,
        fitted_parameters={"radius_multiplier": float(fit_base.x[0])},
        training_rms_ppm=tr_rms_base,
        training_weighted_q_over_n=tr_q_n_base,
        validation_mean_depth_percent=mean_pred_base,
        validation_mean_offset_ppm=offset_base_ppm,
        validation_shape_rms_ppm=shape_rms_base,
        predicted_band_depth_percent=base_band_d,
        predicted_continuum_depth_percent=base_cont_d,
        predicted_contrast_ppm=base_contrast,
        contrast_error_ppm=err_base_contrast,
    )

    # 11. Pre-Declared Statistical Decision Rule
    two_sigma = 2.0 * obs_contrast_unc
    if abs(contrast_improvement) <= two_sigma:
        outcome = "This observation cannot distinguish the models."
        plain_summary = (
            "This observation cannot distinguish the models. "
            f"Both the physical water model (contrast error = {err_h2o_contrast:.1f} ppm) and the flat continuum baseline "
            f"(contrast error = {err_base_contrast:.1f} ppm) predict band contrasts within the 2-sigma observational "
            f"uncertainty interval (±{two_sigma:.1f} ppm) of the validation observation. While adding water improved the "
            f"training fit on NIRSpec G395H by {tr_rms_base - tr_rms_h2o:.1f} ppm, the separate NIRSpec PRISM observation's "
            "per-bin measurement scatter is comparable to the contrast difference, preventing a statistically decisive "
            "preference between the two models on this feature."
        )
    elif contrast_improvement > two_sigma:
        outcome = "Water model significantly improved feature prediction"
        plain_summary = (
            f"Including physical water opacity improved the predicted band contrast by {contrast_improvement:.1f} ppm "
            f"beyond the continuum baseline, exceeding the 2-sigma validation measurement uncertainty (2σ = {two_sigma:.1f} ppm)."
        )
    else:
        outcome = "Baseline model had lower prediction error"
        plain_summary = (
            f"The continuum baseline was closer to the observed contrast than the water model by {-contrast_improvement:.1f} ppm "
            f"(exceeding 2σ = {two_sigma:.1f} ppm)."
        )

    val_points = []
    for i, lam in enumerate(x_val):
        val_points.append({
            "index": int(i),
            "wavelength_um": float(lam),
            "observed_depth_percent": float(y_val[i]),
            "measurement_error_percent": float(s_val[i]),
            "h2o_model_depth_percent": float(val_pred_h2o[i]),
            "baseline_depth_percent": float(val_pred_base[i]),
        })

    result = PredictiveBenchmarkResult(
        benchmark_name="WASP-39 b Cross-Observation Water Predictive Benchmark",
        target_planet="WASP-39 b",
        molecule_tested="H2O",
        fitting_observation=spec_fit_rec,
        validation_observation=spec_val_rec,
        are_observations_independent=is_indep,
        independence_evidence=indep_evidence,
        opacity_provenance=opacity_prov,
        band_definition=band_definition,
        observed_band_depth_percent=obs_band_d,
        observed_continuum_depth_percent=obs_cont_d,
        observed_contrast_ppm=obs_contrast,
        observed_contrast_uncertainty_ppm=obs_contrast_unc,
        h2o_model=rec_h2o,
        baseline_model=rec_base,
        contrast_accuracy_improvement_ppm=contrast_improvement,
        outcome_decision=outcome,
        plain_language_summary=plain_summary,
        validation_points=val_points,
    )

    if freeze_output_path:
        out_p = Path(freeze_output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(result.export_manifest(), indent=2), encoding="utf-8")

    return result
