"""Comparison of scientific assumptions across analysis configurations.

Manages, saves, and compares analysis configurations differing in key assumptions:
- Clear vs cloudy atmosphere (e.g. P_cloud=0.01 bar vs None/100 bar).
- Alternative supported opacity sources (e.g. line-by-line ExoMol vs synthetic templates).
- Selected molecular components (e.g. full chemistry vs drop-one species).
- Wavelength domain selections (e.g. full PRISM band vs 3.0–5.0 µm sub-band).
- Alternative noise treatments (unweighted vs 1-sigma Gaussian vs covariance).

Enforces scientific domain boundaries:
- Forbids ranking fits on different wavelength subsets as directly comparable scores.
- Declares that Bayesian evidence is not calculated unless an active nested-sampling
  or MCMC backend is installed and provides valid evidence integrals.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Sequence
from uuid import uuid4

import numpy as np

from ecas.comparison.eligibility import ComparisonInput
from ecas.models.spectrum import SpectrumData


DOMAIN_MISMATCH_WARNING = (
    "Configurations were evaluated on different data points or wavelength subsets. "
    "Residual RMS and Chi-squared statistics across differing data domains are NOT "
    "directly equivalent or rankable."
)

BAYESIAN_EVIDENCE_NOTICE = (
    "Bayesian evidence (marginal likelihood ln Z and Bayes factors) requires an active "
    "nested-sampling or MCMC atmospheric retrieval backend. In this forward-model configuration, "
    "comparisons report goodness-of-fit Δχ² and residual RMS conditioned on the specified parameters."
)


@dataclass(frozen=True)
class ScientificAssumptionVariant:
    """A single preserved analysis configuration and its evaluated results."""

    config_id: str
    name: str
    target_id: str
    atmosphere_structure: str  # 'cloudy', 'clear', 'hazy'
    cloud_pressure_bar: float | None
    opacity_source_kind: str  # 'real_exomol', 'synthetic_template', 'laboratory'
    included_species: tuple[str, ...]
    wavelength_range_um: tuple[float, float]
    data_point_count: int
    data_indices: tuple[int, ...]
    noise_treatment: str  # 'unweighted', 'independent_gaussian_1sigma', 'gaussian_covariance'
    model_predictions: tuple[float, ...]
    residuals: tuple[float, ...]
    rms_residual: float
    reduced_chi2: float | None
    provenance: dict[str, Any] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_id": self.config_id,
            "name": self.name,
            "target_id": self.target_id,
            "atmosphere_structure": self.atmosphere_structure,
            "cloud_pressure_bar": self.cloud_pressure_bar,
            "opacity_source_kind": self.opacity_source_kind,
            "included_species": list(self.included_species),
            "wavelength_range_um": list(self.wavelength_range_um),
            "data_point_count": self.data_point_count,
            "data_indices": list(self.data_indices),
            "noise_treatment": self.noise_treatment,
            "model_predictions": list(self.model_predictions),
            "residuals": list(self.residuals),
            "rms_residual": self.rms_residual,
            "reduced_chi2": self.reduced_chi2,
            "provenance": self.provenance,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True)
class AssumptionDelta:
    """Detailed differential comparison between two scientific assumption configurations."""

    variant_a_id: str
    variant_a_name: str
    variant_b_id: str
    variant_b_name: str
    data_domains_identical: bool
    domain_warning: str | None
    assumption_differences: tuple[str, ...]
    model_prediction_delta_rms: float
    max_model_prediction_delta: float
    delta_rms_residual: float  # RMS_b - RMS_a
    delta_reduced_chi2: float | None  # None if domains differ
    evidence_comparison_available: bool = False
    evidence_statement: str = BAYESIAN_EVIDENCE_NOTICE
    applicable_limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant_a_id": self.variant_a_id,
            "variant_a_name": self.variant_a_name,
            "variant_b_id": self.variant_b_id,
            "variant_b_name": self.variant_b_name,
            "data_domains_identical": self.data_domains_identical,
            "domain_warning": self.domain_warning,
            "assumption_differences": list(self.assumption_differences),
            "model_prediction_delta_rms": self.model_prediction_delta_rms,
            "max_model_prediction_delta": self.max_model_prediction_delta,
            "delta_rms_residual": self.delta_rms_residual,
            "delta_reduced_chi2": self.delta_reduced_chi2,
            "evidence_comparison_available": self.evidence_comparison_available,
            "evidence_statement": self.evidence_statement,
            "applicable_limitations": list(self.applicable_limitations),
        }


def compare_scientific_assumptions(
    variant_a: ScientificAssumptionVariant,
    variant_b: ScientificAssumptionVariant,
) -> AssumptionDelta:
    """Compare two scientific assumption configurations."""
    # 1. Identify differences in assumptions
    diffs: list[str] = []

    if variant_a.atmosphere_structure != variant_b.atmosphere_structure or variant_a.cloud_pressure_bar != variant_b.cloud_pressure_bar:
        diffs.append(
            f"Atmosphere Structure: {variant_a.atmosphere_structure} (Pcloud={variant_a.cloud_pressure_bar} bar) "
            f"vs {variant_b.atmosphere_structure} (Pcloud={variant_b.cloud_pressure_bar} bar)"
        )

    if variant_a.opacity_source_kind != variant_b.opacity_source_kind:
        diffs.append(f"Opacity Sources: {variant_a.opacity_source_kind} vs {variant_b.opacity_source_kind}")

    species_a = set(variant_a.included_species)
    species_b = set(variant_b.included_species)
    if species_a != species_b:
        dropped_in_b = species_a - species_b
        added_in_b = species_b - species_a
        notes = []
        if dropped_in_b:
            notes.append(f"omitted {', '.join(sorted(dropped_in_b))}")
        if added_in_b:
            notes.append(f"added {', '.join(sorted(added_in_b))}")
        diffs.append(f"Molecular Chemistry: {'; '.join(notes)}")

    if variant_a.wavelength_range_um != variant_b.wavelength_range_um:
        diffs.append(
            f"Wavelength Span: [{variant_a.wavelength_range_um[0]:.3g}, {variant_a.wavelength_range_um[1]:.3g}] µm "
            f"vs [{variant_b.wavelength_range_um[0]:.3g}, {variant_b.wavelength_range_um[1]:.3g}] µm"
        )

    if variant_a.noise_treatment != variant_b.noise_treatment:
        diffs.append(f"Noise Treatment: {variant_a.noise_treatment} vs {variant_b.noise_treatment}")

    if not diffs:
        diffs.append("No recorded assumption differences (identical configurations).")

    # 2. Check data domain identity
    same_count = variant_a.data_point_count == variant_b.data_point_count
    same_indices = variant_a.data_indices == variant_b.data_indices
    same_range = variant_a.wavelength_range_um == variant_b.wavelength_range_um
    domains_identical = same_count and same_indices and same_range

    domain_warn = None if domains_identical else DOMAIN_MISMATCH_WARNING

    # 3. Model prediction differences
    # Compute on the intersection of data indices or min length
    n_common = min(len(variant_a.model_predictions), len(variant_b.model_predictions))
    if n_common > 0:
        pred_a = np.asarray(variant_a.model_predictions[:n_common], dtype=float)
        pred_b = np.asarray(variant_b.model_predictions[:n_common], dtype=float)
        pred_diff = pred_b - pred_a
        max_delta_pred = float(np.max(np.abs(pred_diff)))
        rms_delta_pred = float(np.sqrt(np.mean(pred_diff ** 2)))
    else:
        max_delta_pred = 0.0
        rms_delta_pred = 0.0

    delta_rms = float(variant_b.rms_residual - variant_a.rms_residual)

    # Chi-squared comparison is ONLY valid if data domains are identical!
    if domains_identical and variant_a.reduced_chi2 is not None and variant_b.reduced_chi2 is not None:
        delta_chi2 = float(variant_b.reduced_chi2 - variant_a.reduced_chi2)
    else:
        delta_chi2 = None

    # Merge limitations
    all_limits = list(dict.fromkeys(variant_a.limitations + variant_b.limitations))

    return AssumptionDelta(
        variant_a_id=variant_a.config_id,
        variant_a_name=variant_a.name,
        variant_b_id=variant_b.config_id,
        variant_b_name=variant_b.name,
        data_domains_identical=domains_identical,
        domain_warning=domain_warn,
        assumption_differences=tuple(diffs),
        model_prediction_delta_rms=rms_delta_pred,
        max_model_prediction_delta=max_delta_pred,
        delta_rms_residual=delta_rms,
        delta_reduced_chi2=delta_chi2,
        evidence_comparison_available=False,
        evidence_statement=BAYESIAN_EVIDENCE_NOTICE,
        applicable_limitations=tuple(all_limits),
    )


class AssumptionsManager:
    """Manages preserved scientific assumption configurations for comparative evaluation."""

    def __init__(self):
        self._variants: dict[str, ScientificAssumptionVariant] = {}

    def add_variant(self, variant: ScientificAssumptionVariant) -> None:
        self._variants[variant.config_id] = variant

    def get_variant(self, config_id: str) -> ScientificAssumptionVariant | None:
        return self._variants.get(config_id)

    def list_variants(self) -> tuple[ScientificAssumptionVariant, ...]:
        return tuple(self._variants.values())

    def clear(self) -> None:
        self._variants.clear()

