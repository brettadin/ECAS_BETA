"""Candidate molecule screening and hypothesis generation engine.

Implements principled, instrument-aware candidate screening for planetary
transmission spectra and laboratory spectroscopy.

Follows the TauREx 'Marple' screening philosophy (Waldmann et al. 2015,
arXiv:1409.2312) while incorporating species-selection bias protections and
look-elsewhere effect disclosures (MacDonald & Batalha 2023, Welbanks et al. 2024,
arXiv:2506.12144).

Key scientific guarantees:
1. Physical modelling: Planetary transmission candidates are evaluated via 1D
   isothermal limb radiative transfer with real opacity cross sections, not raw
   cross-section comparisons against transit depth.
2. Fair domain comparison: Baseline and candidate models are evaluated on the
   EXACT same wavelength points and instrument passbands.
3. Transparent inventory: Species in catalogues whose cross-sections are not
   downloaded locally are categorized as 'unavailable_data', NEVER reported as
   evidence of absence.
4. Non-calibrated screening: Screening statistics (ΔRMS, Δχ²) are explicitly
   documented as hypothesis ranking metrics, NOT calibrated Bayesian posteriors
   or detection significance.
5. Multi-band consistency & degeneracies: Secondary bands and overlapping
   alternative candidates are systematically detected and reported.
"""
from __future__ import annotations

import base64
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
import json
import math
from pathlib import Path
from typing import Any, Literal

import numpy as np

from ecas.comparison.diagnostics import compute_residual_structure_diagnostics
from ecas.comparison.eligibility import ComparisonInput
from ecas.comparison.model_generator import (
    GeneratedForwardModel,
    MolecularComponentSpec,
    PlanetAtmospherePreset,
    component_from_cached_exomol,
    generate_isothermal_transmission_model,
    get_planet_preset,
)
from ecas.identification.library import LibraryCatalog, ReferenceDataset, discover_library
from ecas.ingestion.exomol_catalogue import parse_catalogue
from ecas.ingestion.exomol_reference_cache import cached_references

PoolStatus = Literal["searchable", "partial_coverage", "unavailable_data", "incompatible"]
ScreeningOutcome = Literal[
    "Strong Candidate",
    "Moderate Support",
    "Marginal / Weak",
    "No Improvement",
    "Inconclusive",
]

SCIENTIFIC_DISCLOSURES = (
    "Candidate screening evaluates hypothesis suitability on a fixed 1D isothermal "
    "limb-transmission model grid. It does NOT constitute a Bayesian retrieval, "
    "posterior evidence, or detection significance.",
    "Searching an extensive molecular catalogue inherently inflates the probability of "
    "accidental spectral alignments (look-elsewhere effect / species-selection bias; "
    "see MacDonald & Batalha 2023, Welbanks et al. 2024).",
    "Unmodelled physics (3D thermal gradients, non-gray photochemical hazes, stellar "
    "photospheric activity) can mimic or distort candidate molecular features.",
    "Categorization as 'unavailable_data' indicates the species is in the catalogue but "
    "its opacity is not in the local cache. It is NOT evidence that the molecule is absent.",
)


@dataclass(frozen=True)
class CandidatePoolEntry:
    """A molecular species considered for the candidate screening pool."""

    molecule_id: str
    formula: str
    isotopologue: str
    dataset: str | None
    status: PoolStatus
    status_reason: str
    wavelength_range_um: tuple[float, float] | None
    wavenumber_range_cm1: tuple[float, float] | None
    reference_temperature_k: float | None
    source_sha256: str | None
    source_type: str
    reference_record: Any = None


@dataclass(frozen=True)
class DistinguishingBand:
    """A wavelength band that can distinguish between two overlapping candidate species."""

    band_min_um: float
    band_max_um: float
    competing_molecule: str
    explanation: str


@dataclass(frozen=True)
class CandidateScreeningResult:
    """Quantitative screening metrics for a single candidate molecule."""

    molecule_id: str
    formula: str
    isotopologue: str
    dataset: str | None
    status: PoolStatus
    outcome: ScreeningOutcome
    outcome_reason: str
    tested_vmr: float
    evaluated_wavelength_range_um: tuple[float, float]
    evaluated_points_count: int
    total_observation_points: int
    coverage_fraction: float
    baseline_rms: float
    candidate_rms: float
    delta_rms: float  # cand_rms - base_rms (negative indicates improvement)
    rms_improvement_percent: float  # ((base - cand) / base) * 100
    baseline_chi2: float
    candidate_chi2: float
    delta_chi2: float  # base_chi2 - cand_chi2 (positive indicates improvement)
    reduced_chi2: float
    runs_test_z: float | None
    runs_test_interpretation: str
    multi_band_consistency: str
    competing_alternatives: tuple[str, ...]
    distinguishing_bands: tuple[DistinguishingBand, ...]
    supporting_regions_um: tuple[tuple[float, float], ...]
    candidate_model_curve: tuple[tuple[float, float], ...]  # (wavelength, transit_depth)
    baseline_model_curve: tuple[tuple[float, float], ...]
    source_sha256: str | None = None
    is_selected_for_followup: bool = False


@dataclass(frozen=True)
class JointCandidateResult:
    """Evaluation of a combined candidate pair (Candidate A + Candidate B)."""

    pair_name: str
    molecules: tuple[str, str]
    delta_chi2_vs_baseline: float
    additive_chi2_improvement: float  # improvement beyond best single candidate
    joint_rms: float
    outcome: str
    explanation: str


@dataclass
class CandidatePool:
    """Collection of candidate species partitioned into status categories."""

    observation_target: str
    observation_domain_um: tuple[float, float]
    observation_points_count: int
    observable: str
    searchable: list[CandidatePoolEntry] = field(default_factory=list)
    partial: list[CandidatePoolEntry] = field(default_factory=list)
    unavailable: list[CandidatePoolEntry] = field(default_factory=list)
    incompatible: list[CandidatePoolEntry] = field(default_factory=list)

    @property
    def all_entries(self) -> list[CandidatePoolEntry]:
        return self.searchable + self.partial + self.unavailable + self.incompatible

    def summary(self) -> dict[str, int]:
        return {
            "searchable": len(self.searchable),
            "partial_coverage": len(self.partial),
            "unavailable_data": len(self.unavailable),
            "incompatible": len(self.incompatible),
            "total_considered": len(self.all_entries),
        }

    def export_inventory(self) -> list[dict[str, Any]]:
        rows = []
        for e in self.all_entries:
            rows.append({
                "molecule_id": e.molecule_id,
                "formula": e.formula,
                "isotopologue": e.isotopologue,
                "dataset": e.dataset,
                "status": e.status,
                "status_reason": e.status_reason,
                "wavelength_range_um": e.wavelength_range_um,
                "reference_temperature_k": e.reference_temperature_k,
                "source_type": e.source_type,
            })
        return rows


@dataclass
class ScreeningReport:
    """Complete hypothesis generation and screening report."""

    target_id: str
    target_sha256: str | None
    observable: str
    mode: str
    planet_preset_id: str | None
    baseline_parameters: dict[str, Any]
    screening_config: dict[str, Any]
    pool: CandidatePool
    results: list[CandidateScreeningResult]
    joint_pairs: list[JointCandidateResult] = field(default_factory=list)
    unexplained_regions_um: list[tuple[float, float]] = field(default_factory=list)
    scientific_disclosures: tuple[str, ...] = SCIENTIFIC_DISCLOSURES

    def top_candidates(self, limit: int = 5) -> list[CandidateScreeningResult]:
        """Return top candidates ranked by delta_chi2 improvement on eligible points."""
        sorted_cands = sorted(
            [r for r in self.results if r.delta_chi2 > 0 and r.delta_rms < 0],
            key=lambda r: r.delta_chi2,
            reverse=True,
        )
        return sorted_cands[:limit]

    def export_manifest(self) -> dict[str, Any]:
        """Export comprehensive JSON reproducibility manifest."""
        return {
            "schema": "ecas-candidate-screening-v1",
            "target_id": self.target_id,
            "target_sha256": self.target_sha256,
            "observable": self.observable,
            "mode": self.mode,
            "planet_preset_id": self.planet_preset_id,
            "baseline_parameters": self.baseline_parameters,
            "screening_config": self.screening_config,
            "pool_summary": self.pool.summary(),
            "candidate_inventory": self.pool.export_inventory(),
            "candidates_evaluated_count": len(self.results),
            "screening_results": [
                {
                    "molecule_id": r.molecule_id,
                    "formula": r.formula,
                    "outcome": r.outcome,
                    "outcome_reason": r.outcome_reason,
                    "tested_vmr": r.tested_vmr,
                    "evaluated_wavelength_range_um": r.evaluated_wavelength_range_um,
                    "evaluated_points_count": r.evaluated_points_count,
                    "total_observation_points": r.total_observation_points,
                    "coverage_fraction": r.coverage_fraction,
                    "delta_rms": r.delta_rms,
                    "rms_improvement_percent": r.rms_improvement_percent,
                    "delta_chi2": r.delta_chi2,
                    "reduced_chi2": r.reduced_chi2,
                    "runs_test_z": r.runs_test_z,
                    "runs_test_interpretation": r.runs_test_interpretation,
                    "multi_band_consistency": r.multi_band_consistency,
                    "competing_alternatives": list(r.competing_alternatives),
                    "distinguishing_bands": [
                        {
                            "range_um": (b.band_min_um, b.band_max_um),
                            "competing": b.competing_molecule,
                            "explanation": b.explanation,
                        }
                        for b in r.distinguishing_bands
                    ],
                    "supporting_regions_um": list(r.supporting_regions_um),
                    "is_selected": r.is_selected_for_followup,
                }
                for r in self.results
            ],
            "joint_pairs": [asdict(p) for p in self.joint_pairs],
            "unexplained_regions_um": self.unexplained_regions_um,
            "scientific_disclosures": list(self.scientific_disclosures),
        }

    def export_markdown_report(self) -> str:
        """Export publication-quality Markdown screening report."""
        lines = [
            f"# ECAS Candidate Molecule Screening Report — {self.target_id}",
            "",
            f"- **Target / Observation:** {self.target_id}",
            f"- **Observable:** {self.observable} ({self.mode})",
            f"- **Atmospheric Preset:** {self.planet_preset_id or 'Custom'}",
            f"- **Wavelength Coverage:** {self.pool.observation_domain_um[0]:.3f} – {self.pool.observation_domain_um[1]:.3f} µm ({self.pool.observation_points_count} points)",
            "",
            "## 1. Candidate Pool Summary",
            "",
            f"A total of **{len(self.pool.all_entries)}** candidate molecular references were inspected:",
            f"- **Searchable candidates:** {len(self.pool.searchable)}",
            f"- **Partial coverage candidates:** {len(self.pool.partial)}",
            f"- **Unavailable reference data (not cached):** {len(self.pool.unavailable)}",
            f"- **Incompatible species:** {len(self.pool.incompatible)}",
            "",
            "> **Methodological Note:** Unavailable reference data indicates that the species is listed in the catalogue but its molecular cross section has not been downloaded into the local cache. It does NOT indicate the molecule is absent from the target atmosphere.",
            "",
            "## 2. Screening Suggestions & Results",
            "",
            "| Molecule | Outcome | ΔRMS (%) | Δχ² | Reduced χ² | Evaluated Coverage | Consistency / Alternatives |",
            "|---|---|---|---|---|---|---|",
        ]
        for r in self.results:
            cov_str = f"{r.evaluated_wavelength_range_um[0]:.2f}–{r.evaluated_wavelength_range_um[1]:.2f} µm ({r.evaluated_points_count} pts)"
            alt_summary = r.multi_band_consistency
            if r.competing_alternatives:
                alt_summary += f"; Alt: {', '.join(r.competing_alternatives[:2])}"
            lines.append(
                f"| **{r.formula}** ({r.molecule_id}) | {r.outcome} | {r.rms_improvement_percent:+.2f}% | {r.delta_chi2:+.1f} | {r.reduced_chi2:.2f} | {cov_str} | {alt_summary} |"
            )

        if self.joint_pairs:
            lines.extend([
                "",
                "## 3. Joint Multi-Candidate Combinations",
                "",
                "| Candidate Pair | Joint Δχ² | Additive Gain | Outcome | Explanation |",
                "|---|---|---|---|---|",
            ])
            for p in self.joint_pairs:
                lines.append(
                    f"| {p.pair_name} | {p.delta_chi2_vs_baseline:+.1f} | {p.additive_chi2_improvement:+.1f} | {p.outcome} | {p.explanation} |"
                )

        if self.unexplained_regions_um:
            lines.extend([
                "",
                "## 4. Unexplained Spectral Features",
                "",
                "The following spectral regions exhibit significant residuals (> 2σ) across all tested candidate models, indicating potential unmodeled absorbers, continuum slope variations, or instrumental systematics:",
            ])
            for reg in self.unexplained_regions_um:
                lines.append(f"- **{reg[0]:.3f} – {reg[1]:.3f} µm**")

        lines.extend([
            "",
            "## 5. Scientific Method & Limitations",
            "",
        ])
        for note in self.scientific_disclosures:
            lines.append(f"- {note}")

        return "\n".join(lines)


def build_candidate_pool(
    observation: ComparisonInput,
    cache_root: Path | str,
    library_root: Path | str,
    *,
    exomol_catalogue_path: Path | str | None = None,
) -> CandidatePool:
    """Build and partition the candidate molecule pool based on actual reference availability.

    Categorizes every candidate into:
    - Searchable: local valid opacity covering observation domain (>= 3 points).
    - Partial: covers partial range (< 80% of points, but >= 3 points).
    - Unavailable: known catalog species whose cross sections are not cached locally.
    - Incompatible: observable, unit, or modality mismatch.
    """
    obs_coords = np.asarray(observation.coordinates, dtype=float)
    if len(obs_coords) == 0:
        obs_min, obs_max = 0.0, 0.0
    else:
        obs_min, obs_max = float(obs_coords[0]), float(obs_coords[-1])

    pool = CandidatePool(
        observation_target=observation.source_id,
        observation_domain_um=(obs_min, obs_max),
        observation_points_count=len(obs_coords),
        observable=observation.observable,
    )

    is_transmission = (
        observation.observable == "transit_depth"
        or (
            observation.axis_unit in ("um", "microns", "nm")
            and observation.signal_unit in ("percent", "fraction")
            and observation.observable not in ("absorbance", "transmittance", "optical_depth", "cross_section")
            and "lab" not in observation.source_id.lower()
        )
    )

    # 1. Inspect ExoMol Cached References
    cached_root_path = Path(cache_root) / "references" if not str(cache_root).endswith("references") else Path(cache_root)
    cached_records, _ = cached_references(cached_root_path)
    seen_exomol_formulas: set[str] = set()

    for path, ref in cached_records:
        prov = ref.product.provenance
        mol_formula = prov.molecule
        iso = prov.isotopologue
        dataset = prov.dataset
        seen_exomol_formulas.add(mol_formula)

        pts = [(float(nu), float(sig)) for nu, sig in ref.product.points if float(nu) > 0.0]
        if len(pts) < 3:
            pool.incompatible.append(
                CandidatePoolEntry(
                    molecule_id=f"{mol_formula} ({iso})",
                    formula=mol_formula,
                    isotopologue=iso,
                    dataset=dataset,
                    status="incompatible",
                    status_reason="Cached reference has < 3 valid positive wavenumber points.",
                    wavelength_range_um=None,
                    wavenumber_range_cm1=None,
                    reference_temperature_k=ref.request.temperature,
                    source_sha256=ref.product.source_sha256,
                    source_type="ExoMol cached reference",
                    reference_record=ref,
                )
            )
            continue

        nu_vals = [p[0] for p in pts]
        nu_min, nu_max = min(nu_vals), max(nu_vals)
        lam_min = 10000.0 / nu_max
        lam_max = 10000.0 / nu_min

        if not is_transmission:
            pool.incompatible.append(
                CandidatePoolEntry(
                    molecule_id=f"{mol_formula} ({iso})",
                    formula=mol_formula,
                    isotopologue=iso,
                    dataset=dataset,
                    status="incompatible",
                    status_reason=f"ExoMol cross section is designed for planetary transmission; incompatible with observable '{observation.observable}'.",
                    wavelength_range_um=(lam_min, lam_max),
                    wavenumber_range_cm1=(nu_min, nu_max),
                    reference_temperature_k=ref.request.temperature,
                    source_sha256=ref.product.source_sha256,
                    source_type="ExoMol cached reference",
                    reference_record=ref,
                )
            )
            continue

        # Check overlapping observation points
        overlap_mask = (obs_coords >= lam_min) & (obs_coords <= lam_max)
        overlap_count = int(np.sum(overlap_mask))

        if overlap_count < 3:
            pool.incompatible.append(
                CandidatePoolEntry(
                    molecule_id=f"{mol_formula} ({iso})",
                    formula=mol_formula,
                    isotopologue=iso,
                    dataset=dataset,
                    status="incompatible",
                    status_reason=f"Insufficient overlapping observation points ({overlap_count} pts < 3 required). Reference covers {lam_min:.2f}–{lam_max:.2f} µm.",
                    wavelength_range_um=(lam_min, lam_max),
                    wavenumber_range_cm1=(nu_min, nu_max),
                    reference_temperature_k=ref.request.temperature,
                    source_sha256=ref.product.source_sha256,
                    source_type="ExoMol cached reference",
                    reference_record=ref,
                )
            )
        elif overlap_count >= 0.8 * len(obs_coords):
            pool.searchable.append(
                CandidatePoolEntry(
                    molecule_id=f"{mol_formula} ({iso})",
                    formula=mol_formula,
                    isotopologue=iso,
                    dataset=dataset,
                    status="searchable",
                    status_reason=f"Valid ExoMol opacity covering {overlap_count}/{len(obs_coords)} points ({lam_min:.2f}–{lam_max:.2f} µm).",
                    wavelength_range_um=(lam_min, lam_max),
                    wavenumber_range_cm1=(nu_min, nu_max),
                    reference_temperature_k=ref.request.temperature,
                    source_sha256=ref.product.source_sha256,
                    source_type="ExoMol cached reference",
                    reference_record=ref,
                )
            )
        else:
            pool.partial.append(
                CandidatePoolEntry(
                    molecule_id=f"{mol_formula} ({iso})",
                    formula=mol_formula,
                    isotopologue=iso,
                    dataset=dataset,
                    status="partial_coverage",
                    status_reason=f"Partial coverage: covers {overlap_count}/{len(obs_coords)} points ({lam_min:.2f}–{lam_max:.2f} µm). Requires domain-restricted evaluation.",
                    wavelength_range_um=(lam_min, lam_max),
                    wavenumber_range_cm1=(nu_min, nu_max),
                    reference_temperature_k=ref.request.temperature,
                    source_sha256=ref.product.source_sha256,
                    source_type="ExoMol cached reference",
                    reference_record=ref,
                )
            )

    # 2. Inspect ExoMol Catalog for Uncached Known Species
    cat_file = Path(exomol_catalogue_path) if exomol_catalogue_path else Path(cache_root).parent / "cache/catalogue.json"
    if not cat_file.exists():
        cat_file = Path("data/ExoMol/cache/catalogue.json")

    if cat_file.exists():
        try:
            d = json.loads(cat_file.read_text("utf-8"))
            raw = base64.b64decode(d["raw_base64"])
            cat = parse_catalogue(raw)
            known_species = sorted({e.formula for e in cat.entries})
            for sp in known_species:
                if sp not in seen_exomol_formulas:
                    pool.unavailable.append(
                        CandidatePoolEntry(
                            molecule_id=sp,
                            formula=sp,
                            isotopologue=sp,
                            dataset=None,
                            status="unavailable_data",
                            status_reason="Catalog species recognized in ExoMol. Molecular cross-section is not downloaded in local cache. Reference data unavailable — NOT evidence of absence.",
                            wavelength_range_um=None,
                            wavenumber_range_cm1=None,
                            reference_temperature_k=None,
                            source_sha256=None,
                            source_type="ExoMol catalog (uncached)",
                            reference_record=None,
                        )
                    )
        except Exception:
            pass

    # 3. Inspect Laboratory Spectral Library
    lib_path = Path(library_root)
    if lib_path.exists():
        try:
            lib_cat = discover_library(lib_path)
            for ref_ds in lib_cat.datasets:
                mol = ref_ds.molecule
                modality = ref_ds.modality
                if is_transmission:
                    pool.incompatible.append(
                        CandidatePoolEntry(
                            molecule_id=f"Lab {mol} ({modality})",
                            formula=mol,
                            isotopologue=mol,
                            dataset=ref_ds.ref_id,
                            status="incompatible",
                            status_reason="Laboratory measurement (transmittance/absorbance) cannot be directly compared to planetary transit depth; physical ExoMol cross sections are required for atmospheric radiative transfer.",
                            wavelength_range_um=None,
                            wavenumber_range_cm1=None,
                            reference_temperature_k=None,
                            source_sha256=ref_ds.source_sha256,
                            source_type=f"ECAS Spectral Library ({modality})",
                            reference_record=ref_ds,
                        )
                    )
                else:
                    # For laboratory identification observations
                    pool.searchable.append(
                        CandidatePoolEntry(
                            molecule_id=f"Lab {mol} ({modality})",
                            formula=mol,
                            isotopologue=mol,
                            dataset=ref_ds.ref_id,
                            status="searchable",
                            status_reason=f"Compatible laboratory {modality} reference dataset.",
                            wavelength_range_um=None,
                            wavenumber_range_cm1=None,
                            reference_temperature_k=None,
                            source_sha256=ref_ds.source_sha256,
                            source_type=f"ECAS Spectral Library ({modality})",
                            reference_record=ref_ds,
                        )
                    )
        except Exception:
            pass

    return pool


def _find_distinguishing_bands(
    cand_spec: MolecularComponentSpec,
    other_specs: Sequence[MolecularComponentSpec],
    coverage_um: tuple[float, float],
) -> list[DistinguishingBand]:
    """Identify spectral regions where a candidate's opacity diverges from competing species."""
    dist_bands: list[DistinguishingBand] = []
    w_cand = np.array(cand_spec.wavelengths_um, dtype=float)
    x_cand = np.array(cand_spec.cross_sections_cm2, dtype=float)
    cand_max = np.max(x_cand) if len(x_cand) > 0 and np.max(x_cand) > 0 else 1.0
    cand_norm = x_cand / cand_max

    for other in other_specs:
        if other.formula == cand_spec.formula:
            continue
        w_oth = np.array(other.wavelengths_um, dtype=float)
        x_oth = np.array(other.cross_sections_cm2, dtype=float)
        oth_max = np.max(x_oth) if len(x_oth) > 0 and np.max(x_oth) > 0 else 1.0

        # Check overlapping range
        low = max(coverage_um[0], float(w_cand[0]), float(w_oth[0]))
        high = min(coverage_um[1], float(w_cand[-1]), float(w_oth[-1]))
        if high <= low:
            continue

        grid = np.linspace(low, high, 120)
        c_interp = np.interp(grid, w_cand, cand_norm)
        o_interp = np.interp(grid, w_oth, x_oth / oth_max)

        # Region where candidate has significant absorption and other does not
        diff = c_interp - o_interp
        divergent_idx = np.where(diff > 0.35)[0]
        if len(divergent_idx) >= 4:
            b_min = float(grid[divergent_idx[0]])
            b_max = float(grid[divergent_idx[-1]])
            dist_bands.append(
                DistinguishingBand(
                    band_min_um=b_min,
                    band_max_um=b_max,
                    competing_molecule=other.formula,
                    explanation=(
                        f"{cand_spec.formula} displays prominent absorption ({b_min:.2f}–{b_max:.2f} µm) "
                        f"where {other.formula} has minimal cross-section."
                    ),
                )
            )

    return dist_bands


def screen_candidates(
    observation: ComparisonInput,
    pool: CandidatePool,
    *,
    planet_preset_id: str | None = "wasp-39b",
    screening_vmr: float = 1e-5,
    custom_planet_params: dict[str, Any] | None = None,
) -> ScreeningReport:
    """Screen candidate molecules against the observation using instrument-aware physical modelling."""
    obs_coords = np.asarray(observation.coordinates, dtype=float)
    obs_vals = np.asarray(observation.values, dtype=float)
    obs_unc = np.asarray(observation.sigma, dtype=float) if observation.sigma else np.ones_like(obs_vals) * 0.01
    is_transmission = (
        observation.observable == "transit_depth"
        or (
            observation.axis_unit in ("um", "microns", "nm")
            and observation.signal_unit in ("percent", "fraction")
            and observation.observable not in ("absorbance", "transmittance", "optical_depth", "cross_section")
            and "lab" not in observation.source_id.lower()
        )
    )

    # Resolve planetary parameters
    if planet_preset_id:
        preset = get_planet_preset(planet_preset_id)
        temp_k = float(preset.temperature_k)
        gravity = float(preset.gravity_m_s2)
        r_planet = float(preset.planet_radius_m)
        r_star = float(preset.stellar_radius_m)
        p_ref = float(preset.reference_pressure_bar)
        mu = float(preset.mean_molecular_weight_u)
        p_cloud = float(preset.default_cloud_pressure_bar) if preset.default_cloud_pressure_bar else 0.01
    else:
        cfg = custom_planet_params or {}
        temp_k = float(cfg.get("temperature_k", 1100.0))
        gravity = float(cfg.get("gravity_m_s2", 4.1))
        r_planet = float(cfg.get("planet_radius_m", 9.1e7))
        r_star = float(cfg.get("stellar_radius_m", 6.5e8))
        p_ref = float(cfg.get("reference_pressure_bar", 0.01))
        mu = float(cfg.get("mean_molecular_weight_u", 2.33))
        p_cloud = float(cfg.get("cloud_pressure_bar", 0.01))

    base_params = {
        "temperature_k": temp_k,
        "gravity_m_s2": gravity,
        "planet_radius_m": r_planet,
        "stellar_radius_m": r_star,
        "reference_pressure_bar": p_ref,
        "mean_molecular_weight_u": mu,
        "cloud_pressure_bar": p_cloud,
    }

    screening_config = {
        "screening_vmr": screening_vmr,
        "nuisance_refit": "vertical_baseline_offset",
        "instrument_integration": "shared_passband_grid",
    }

    candidates_to_evaluate = pool.searchable + pool.partial
    results: list[CandidateScreeningResult] = []

    if not is_transmission:
        from ecas.identification.engine import _arrays
        for entry in candidates_to_evaluate:
            ref_ds = entry.reference_record
            if ref_ds is None or not hasattr(ref_ds, "spectrum"):
                continue
            try:
                ref_x, ref_y, _ = _arrays(ref_ds.spectrum)
            except Exception:
                continue

            low = max(float(obs_coords[0]), float(ref_x[0]))
            high = min(float(obs_coords[-1]), float(ref_x[-1]))
            sub_mask = (obs_coords >= low) & (obs_coords <= high)
            sub_coords = obs_coords[sub_mask]
            sub_vals = obs_vals[sub_mask]
            sub_unc = obs_unc[sub_mask]
            if len(sub_coords) < 3:
                continue

            ref_interp = np.interp(sub_coords, ref_x, ref_y)
            A = np.column_stack([ref_interp, np.ones_like(ref_interp)])
            coeff, _, _, _ = np.linalg.lstsq(A, sub_vals, rcond=None)
            cand_fit = A @ coeff
            base_fit = np.full_like(sub_vals, np.mean(sub_vals))

            res_base = sub_vals - base_fit
            res_cand = sub_vals - cand_fit

            rms_base = float(np.sqrt(np.mean(res_base ** 2)))
            rms_cand = float(np.sqrt(np.mean(res_cand ** 2)))
            delta_rms = rms_cand - rms_base
            rms_pct = ((rms_base - rms_cand) / rms_base) * 100.0 if rms_base > 0 else 0.0

            chi2_base = float(np.sum((res_base / sub_unc) ** 2))
            chi2_cand = float(np.sum((res_cand / sub_unc) ** 2))
            delta_chi2 = chi2_base - chi2_cand
            dof = max(1, len(sub_coords) - 2)
            red_chi2 = chi2_cand / dof

            res_struct = compute_residual_structure_diagnostics(res_cand, uncertainties=sub_unc)
            runs_z = res_struct.runs_z_score
            runs_interp = res_struct.runs_interpretation

            if delta_chi2 > 8.0 and delta_rms < 0:
                outcome = "Strong Candidate"
                reason = f"Strong empirical match (Δχ² = +{delta_chi2:.1f}, RMS improved by {rms_pct:.1f}%)."
            elif delta_chi2 > 2.5 and delta_rms < 0:
                outcome = "Moderate Support"
                reason = f"Moderate empirical match (Δχ² = +{delta_chi2:.1f}, RMS improved by {rms_pct:.1f}%)."
            elif delta_chi2 > 0.0:
                outcome = "Marginal / Weak"
                reason = f"Marginal agreement (Δχ² = +{delta_chi2:.1f})."
            else:
                outcome = "No Improvement"
                reason = f"No improvement over flat baseline (Δχ² = {delta_chi2:.1f} <= 0)."

            cand_curve = tuple(zip([float(c) for c in sub_coords], [float(y) for y in cand_fit]))
            base_curve = tuple(zip([float(c) for c in sub_coords], [float(y) for y in base_fit]))

            results.append(
                CandidateScreeningResult(
                    molecule_id=entry.molecule_id,
                    formula=entry.formula,
                    isotopologue=entry.isotopologue,
                    dataset=entry.dataset,
                    status=entry.status,
                    outcome=outcome,
                    outcome_reason=reason,
                    tested_vmr=1.0,
                    evaluated_wavelength_range_um=(low, high),
                    evaluated_points_count=len(sub_coords),
                    total_observation_points=len(obs_coords),
                    coverage_fraction=len(sub_coords) / len(obs_coords),
                    baseline_rms=rms_base,
                    candidate_rms=rms_cand,
                    delta_rms=delta_rms,
                    rms_improvement_percent=rms_pct,
                    baseline_chi2=chi2_base,
                    candidate_chi2=chi2_cand,
                    delta_chi2=delta_chi2,
                    reduced_chi2=red_chi2,
                    runs_test_z=runs_z,
                    runs_test_interpretation=runs_interp,
                    multi_band_consistency="Empirical laboratory reference comparison on overlapping domain.",
                    competing_alternatives=(),
                    distinguishing_bands=(),
                    supporting_regions_um=((low, high),),
                    candidate_model_curve=cand_curve,
                    baseline_model_curve=base_curve,
                    source_sha256=entry.source_sha256,
                    is_selected_for_followup=(outcome in ("Strong Candidate", "Moderate Support")),
                )
            )

        return ScreeningReport(
            target_id=observation.source_id,
            target_sha256=observation.source_sha256,
            observable=observation.observable,
            mode="laboratory_identification",
            planet_preset_id=None,
            baseline_parameters={},
            screening_config={"method": "linear_regression_empirical"},
            pool=pool,
            results=results,
            joint_pairs=[],
            unexplained_regions_um=[],
        )

    prepared_specs: list[MolecularComponentSpec] = []
    cached_cands_map: dict[str, tuple[CandidatePoolEntry, MolecularComponentSpec]] = {}

    for entry in candidates_to_evaluate:
        if entry.reference_record is not None:
            try:
                spec = component_from_cached_exomol(entry.reference_record, vmr=screening_vmr)
                prepared_specs.append(spec)
                cached_cands_map[entry.molecule_id] = (entry, spec)
            except Exception:
                continue

    # Evaluate each candidate on its exact covered wavelength domain
    for entry, cand_spec in cached_cands_map.values():
        cand_lams = np.array(cand_spec.wavelengths_um, dtype=float)
        domain_min = max(float(obs_coords[0]), float(cand_lams[0]))
        domain_max = min(float(obs_coords[-1]), float(cand_lams[-1]))

        domain_mask = (obs_coords >= domain_min) & (obs_coords <= domain_max)
        sub_coords = obs_coords[domain_mask]
        sub_vals = obs_vals[domain_mask]
        sub_unc = obs_unc[domain_mask]

        if len(sub_coords) < 3:
            continue

        # 1. Baseline Model on this EXACT subdomain
        base_model = generate_isothermal_transmission_model(
            target_wavelengths_um=sub_coords,
            components=[],
            **base_params,
        )
        base_y = np.array(base_model.comparison_input.values, dtype=float)

        # 2. Candidate Model on this EXACT subdomain
        cand_model = generate_isothermal_transmission_model(
            target_wavelengths_um=sub_coords,
            components=[cand_spec],
            **base_params,
        )
        cand_y = np.array(cand_model.comparison_input.values, dtype=float)

        # 3. Refit nuisance parameter: vertical baseline offset Δ(Rp/R*)^2
        offset_base = float(np.mean(sub_vals - base_y))
        offset_cand = float(np.mean(sub_vals - cand_y))
        base_fit = base_y + offset_base
        cand_fit = cand_y + offset_cand

        # 4. Residuals and statistics
        res_base = sub_vals - base_fit
        res_cand = sub_vals - cand_fit

        rms_base = float(np.sqrt(np.mean(res_base ** 2)))
        rms_cand = float(np.sqrt(np.mean(res_cand ** 2)))
        delta_rms = rms_cand - rms_base
        rms_pct = ((rms_base - rms_cand) / rms_base) * 100.0 if rms_base > 0 else 0.0

        chi2_base = float(np.sum((res_base / sub_unc) ** 2))
        chi2_cand = float(np.sum((res_cand / sub_unc) ** 2))
        delta_chi2 = chi2_base - chi2_cand

        dof = max(1, len(sub_coords) - 2)
        red_chi2 = chi2_cand / dof

        # Runs test on candidate residuals
        res_struct = compute_residual_structure_diagnostics(res_cand, uncertainties=sub_unc)
        runs_z = res_struct.runs_z_score
        runs_interp = res_struct.runs_interpretation

        # 5. Multi-band consistency
        # Check where candidate absorbs strongest
        x_pts = np.interp(sub_coords, cand_lams, cand_spec.cross_sections_cm2)
        peak_idx = int(np.argmax(x_pts))
        peak_lam = float(sub_coords[peak_idx])
        supporting_regs: list[tuple[float, float]] = []

        # Find points where candidate model reduces individual residual magnitude
        improved_mask = np.abs(res_cand) < np.abs(res_base)
        if np.any(improved_mask):
            imp_coords = sub_coords[improved_mask]
            supporting_regs.append((float(imp_coords[0]), float(imp_coords[-1])))

        # Assess secondary bands
        x_sorted_peaks = np.argsort(x_pts)[::-1]
        secondary_bands: list[float] = []
        for p in x_sorted_peaks:
            lam_p = float(sub_coords[p])
            if abs(lam_p - peak_lam) > 0.4 and x_pts[p] > 0.15 * x_pts[peak_idx]:
                secondary_bands.append(lam_p)
                break

        if len(secondary_bands) > 0:
            sec_lam = secondary_bands[0]
            consistency_msg = (
                f"Multi-band structure evaluated: primary absorption near {peak_lam:.2f} µm "
                f"and secondary band near {sec_lam:.2f} µm both examined on observation grid."
            )
        else:
            consistency_msg = f"Single primary absorption feature near {peak_lam:.2f} µm within coverage."

        # 6. Competing alternatives & distinguishing bands
        dist_bands = _find_distinguishing_bands(
            cand_spec,
            prepared_specs,
            (domain_min, domain_max),
        )
        competing = tuple(sorted({b.competing_molecule for b in dist_bands}))

        # 7. Determine screening outcome
        if delta_chi2 > 8.0 and delta_rms < 0:
            outcome: ScreeningOutcome = "Strong Candidate"
            reason = (
                f"Significant fit improvement (Δχ² = +{delta_chi2:.1f}, RMS improved by {rms_pct:.1f}%); "
                f"explains prominent observed transit-depth excess near {peak_lam:.2f} µm."
            )
        elif delta_chi2 > 2.5 and delta_rms < 0:
            outcome = "Moderate Support"
            reason = f"Moderate fit improvement (Δχ² = +{delta_chi2:.1f}, RMS improved by {rms_pct:.1f}%)."
        elif delta_chi2 > 0.0:
            outcome = "Marginal / Weak"
            reason = f"Marginal fit improvement (Δχ² = +{delta_chi2:.1f}); within baseline uncertainty."
        else:
            outcome = "No Improvement"
            reason = f"Model with {cand_spec.formula} does not improve over baseline (Δχ² = {delta_chi2:.1f} <= 0)."

        # Model curves for visualization
        cand_curve = tuple(zip([float(c) for c in sub_coords], [float(y) for y in cand_fit]))
        base_curve = tuple(zip([float(c) for c in sub_coords], [float(y) for y in base_fit]))

        results.append(
            CandidateScreeningResult(
                molecule_id=entry.molecule_id,
                formula=entry.formula,
                isotopologue=entry.isotopologue,
                dataset=entry.dataset,
                status=entry.status,
                outcome=outcome,
                outcome_reason=reason,
                tested_vmr=screening_vmr,
                evaluated_wavelength_range_um=(domain_min, domain_max),
                evaluated_points_count=len(sub_coords),
                total_observation_points=len(obs_coords),
                coverage_fraction=len(sub_coords) / len(obs_coords),
                baseline_rms=rms_base,
                candidate_rms=rms_cand,
                delta_rms=delta_rms,
                rms_improvement_percent=rms_pct,
                baseline_chi2=chi2_base,
                candidate_chi2=chi2_cand,
                delta_chi2=delta_chi2,
                reduced_chi2=red_chi2,
                runs_test_z=runs_z,
                runs_test_interpretation=runs_interp,
                multi_band_consistency=consistency_msg,
                competing_alternatives=competing,
                distinguishing_bands=tuple(dist_bands),
                supporting_regions_um=tuple(supporting_regs),
                candidate_model_curve=cand_curve,
                baseline_model_curve=base_curve,
                source_sha256=entry.source_sha256,
                is_selected_for_followup=(outcome in ("Strong Candidate", "Moderate Support")),
            )
        )

    # 8. Evaluate joint multi-candidate combinations (Pairs of top candidates)
    joint_pairs: list[JointCandidateResult] = []
    top_cands = [r for r in results if r.delta_chi2 > 0]
    if len(top_cands) >= 2:
        cand_a = top_cands[0]
        cand_b = top_cands[1]
        spec_a = cached_cands_map[cand_a.molecule_id][1]
        spec_b = cached_cands_map[cand_b.molecule_id][1]

        # Shared domain across A and B
        low_ab = max(cand_a.evaluated_wavelength_range_um[0], cand_b.evaluated_wavelength_range_um[0])
        high_ab = min(cand_a.evaluated_wavelength_range_um[1], cand_b.evaluated_wavelength_range_um[1])
        mask_ab = (obs_coords >= low_ab) & (obs_coords <= high_ab)
        if np.sum(mask_ab) >= 3:
            coords_ab = obs_coords[mask_ab]
            vals_ab = obs_vals[mask_ab]
            unc_ab = obs_unc[mask_ab]

            base_ab = generate_isothermal_transmission_model(
                target_wavelengths_um=coords_ab,
                components=[],
                **base_params,
            )
            joint_model = generate_isothermal_transmission_model(
                target_wavelengths_um=coords_ab,
                components=[spec_a, spec_b],
                **base_params,
            )
            base_fit_ab = np.array(base_ab.comparison_input.values, dtype=float) + float(np.mean(vals_ab - np.array(base_ab.comparison_input.values)))
            joint_fit_ab = np.array(joint_model.comparison_input.values, dtype=float) + float(np.mean(vals_ab - np.array(joint_model.comparison_input.values)))

            chi2_base_ab = float(np.sum(((vals_ab - base_fit_ab) / unc_ab) ** 2))
            chi2_joint_ab = float(np.sum(((vals_ab - joint_fit_ab) / unc_ab) ** 2))
            d_chi2_joint = chi2_base_ab - chi2_joint_ab
            additive_gain = d_chi2_joint - max(cand_a.delta_chi2, cand_b.delta_chi2)

            joint_rms = float(np.sqrt(np.mean((vals_ab - joint_fit_ab) ** 2)))
            pair_label = f"{cand_a.formula} + {cand_b.formula}"

            if additive_gain > 5.0:
                p_outcome = "Additive Improvement"
                p_expl = f"Combining {cand_a.formula} and {cand_b.formula} improves fit significantly beyond either single absorber (additive Δχ² = +{additive_gain:.1f})."
            elif additive_gain > 0.0:
                p_outcome = "Marginal Additive Support"
                p_expl = f"Combining {cand_a.formula} and {cand_b.formula} yields slight additive improvement (Δχ² = +{additive_gain:.1f})."
            else:
                p_outcome = "Redundant / Degenerate"
                p_expl = f"No significant additive gain from combining {cand_a.formula} and {cand_b.formula}; features may be degenerate or overlapping."

            joint_pairs.append(
                JointCandidateResult(
                    pair_name=pair_label,
                    molecules=(cand_a.formula, cand_b.formula),
                    delta_chi2_vs_baseline=d_chi2_joint,
                    additive_chi2_improvement=additive_gain,
                    joint_rms=joint_rms,
                    outcome=p_outcome,
                    explanation=p_expl,
                )
            )

    # 9. Identify unexplained spectral regions (> 2 sigma residuals across top models)
    unexplained_regions: list[tuple[float, float]] = []
    if results:
        best_cand = max(results, key=lambda r: r.delta_chi2)
        # Check regions where residuals exceed 2.2 sigma
        sub_mask = (obs_coords >= best_cand.evaluated_wavelength_range_um[0]) & (obs_coords <= best_cand.evaluated_wavelength_range_um[1])
        c_sub = obs_coords[sub_mask]
        v_sub = obs_vals[sub_mask]
        u_sub = obs_unc[sub_mask]
        mod_y = np.array([pt[1] for pt in best_cand.candidate_model_curve])
        if len(mod_y) == len(v_sub):
            res_sig = np.abs(v_sub - mod_y) / u_sub
            bad_idx = np.where(res_sig > 2.2)[0]
            if len(bad_idx) > 0:
                unexplained_regions.append((float(c_sub[bad_idx[0]]), float(c_sub[bad_idx[-1]])))

    return ScreeningReport(
        target_id=observation.source_id,
        target_sha256=observation.source_sha256,
        observable=observation.observable,
        mode="planetary_transmission" if is_transmission else "laboratory_identification",
        planet_preset_id=planet_preset_id,
        baseline_parameters=base_params,
        screening_config=screening_config,
        pool=pool,
        results=results,
        joint_pairs=joint_pairs,
        unexplained_regions_um=unexplained_regions,
    )
