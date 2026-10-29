"""Physical 1D isothermal hydrostatic limb-transmission forward-model generator.

Implements exact spherical-shell slant-chord optical-depth integration for an
isothermal hydrostatic planetary atmosphere (Lecavelier des Etangs et al. 2008,
A&A 481, L83; Heng & Kitzmann 2017, MNRAS 470, 2972) with:
- Verified planet/star physical presets (WASP-39 b, K2-18 b, HD 209458 b) or
  custom planetary/stellar parameters,
- Real cached ExoMol cross sections (cm^2/molecule on cm^-1 -> microns) and
  imported laboratory UV-Vis / IR cross-section spectra,
- H2/He Rayleigh scattering continuum, haze power-law slope, and opaque gray
  cloud-top pressure cutoff P_cloud,
- Per-wavelength molecular optical-depth share attribution and leave-one-out
  (without-species) sensitivity models,
- Complete AtmosphericModelProvenance and SHA-256 verification compatible with
  ecas-comparison-eligibility-v1 and ecas-forward-model-v1.

Scientific integrity boundary:
- Never extrapolates molecular cross sections outside their covered wavelength domain.
- Explicitly records zero-pressure Doppler-broadening limitations when public
  ExoMol .sigma cross sections are used.
- Leave-one-out Delta-RMS and Delta-Q quantify sensitivity conditioned on the
  fixed forward model; they are never presented as marginalized Bayesian
  retrieval posteriors or standalone detection sigma claims.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math

import numpy as np

from .eligibility import ComparisonInput
from .forward_model import (
    AtmosphericModelProvenance,
    OpacitySourceSpec,
    forward_model_input,
    validate_model_provenance,
)

ENGINE_NAME = "ECAS-IsothermalLimbRT"
ENGINE_VERSION = "1.0.0"

# CODATA 2018 / IAU 2015 nominal SI constants
K_BOLTZMANN = 1.380649e-23        # J / K
ATOMIC_MASS_UNIT = 1.6605390666e-27  # kg
BAR_TO_PA = 1.0e5                 # Pa / bar
CM2_TO_M2 = 1.0e-4                # m^2 / cm^2
EULER_MASCHERONI = 0.5772156649015329

R_JUPITER_M = 7.1492e7            # IAU nominal equatorial Jupiter radius (m)
R_EARTH_M = 6.3781e6              # IAU nominal equatorial Earth radius (m)
R_SUN_M = 6.957e8                 # IAU nominal solar radius (m)

# H2 Rayleigh scattering reference cross section (Lecavelier des Etangs et al. 2008)
H2_RAYLEIGH_SIGMA0_CM2 = 5.31e-27
H2_RAYLEIGH_LAMBDA0_UM = 0.35

ILLUSTRATIVE_DATASET_ID = "ECAS-IllustrativeBandProfile-Synthetic"

# Literature-anchored rovibrational & UV-Vis electronic band centers:
# (center_um, peak_sigma_cm2, gaussian_width_um)
_ILLUSTRATIVE_BAND_LIBRARY: dict[str, tuple[str, tuple[tuple[float, float, float], ...]]] = {
    "H2O": (
        "1H2-16O",
        (
            (0.72, 1.5e-24, 0.015),
            (0.82, 4.0e-24, 0.018),
            (0.94, 2.5e-23, 0.025),
            (1.15, 8.0e-23, 0.035),
            (1.40, 6.0e-22, 0.055),
            (1.87, 1.2e-21, 0.075),
            (2.70, 5.0e-21, 0.140),
            (6.27, 4.0e-20, 0.350),
        ),
    ),
    "CO2": (
        "12C-16O2",
        (
            (1.43, 8.0e-24, 0.020),
            (1.60, 1.5e-23, 0.025),
            (2.01, 2.5e-22, 0.045),
            (2.77, 2.0e-21, 0.070),
            (4.30, 8.0e-19, 0.140),
            (15.0, 2.5e-19, 0.650),
        ),
    ),
    "CH4": (
        "12C-1H4",
        (
            (0.89, 1.2e-23, 0.020),
            (1.15, 4.5e-23, 0.030),
            (1.38, 1.5e-22, 0.040),
            (1.67, 4.5e-22, 0.055),
            (2.32, 2.2e-21, 0.085),
            (3.32, 3.5e-20, 0.130),
            (7.66, 1.8e-20, 0.280),
        ),
    ),
    "SO2": (
        "32S-16O2",
        (
            (0.29, 8.0e-19, 0.018),
            (4.05, 3.5e-20, 0.065),
            (7.35, 1.8e-19, 0.180),
            (8.60, 6.5e-20, 0.220),
        ),
    ),
    "CO": (
        "12C-16O",
        (
            (1.57, 6.0e-24, 0.025),
            (2.35, 3.5e-21, 0.065),
            (4.67, 6.5e-20, 0.130),
        ),
    ),
    "NO2": (
        "14N-16O2",
        (
            (0.40, 6.0e-19, 0.045),
            (3.44, 8.0e-21, 0.070),
            (6.20, 1.4e-19, 0.180),
        ),
    ),
    "Na": (
        "23Na",
        (
            (0.5893, 2.5e-16, 0.004),
        ),
    ),
    "K": (
        "39K",
        (
            (0.7682, 1.8e-16, 0.005),
        ),
    ),
}

ILLUSTRATIVE_SPECIES: tuple[str, ...] = tuple(_ILLUSTRATIVE_BAND_LIBRARY.keys())


@dataclass(frozen=True)
class PlanetAtmospherePreset:
    """Published planetary and stellar bulk parameters for forward-model initialization."""

    preset_id: str
    planet_name: str
    temperature_k: float
    gravity_m_s2: float
    planet_radius_m: float
    stellar_radius_m: float
    reference_pressure_bar: float
    mean_molecular_weight_u: float
    default_cloud_pressure_bar: float | None
    citation: str


PLANET_PRESETS: tuple[PlanetAtmospherePreset, ...] = (
    PlanetAtmospherePreset(
        preset_id="wasp-39b",
        planet_name="WASP-39 b",
        temperature_k=1166.0,
        gravity_m_s2=4.26,
        planet_radius_m=1.27 * R_JUPITER_M,
        stellar_radius_m=0.895 * R_SUN_M,
        reference_pressure_bar=0.01,
        mean_molecular_weight_u=2.33,
        default_cloud_pressure_bar=0.01,
        citation="Faedi et al. (2011); Feinstein et al. (2023, Nature 614, 670)",
    ),
    PlanetAtmospherePreset(
        preset_id="k2-18b",
        planet_name="K2-18 b",
        temperature_k=284.0,
        gravity_m_s2=12.43,
        planet_radius_m=2.61 * R_EARTH_M,
        stellar_radius_m=0.4445 * R_SUN_M,
        reference_pressure_bar=0.01,
        mean_molecular_weight_u=2.35,
        default_cloud_pressure_bar=0.05,
        citation="Benneke et al. (2019); Madhusudhan et al. (2023, ApJL 956, L13)",
    ),
    PlanetAtmospherePreset(
        preset_id="hd-209458b",
        planet_name="HD 209458 b",
        temperature_k=1450.0,
        gravity_m_s2=9.36,
        planet_radius_m=1.359 * R_JUPITER_M,
        stellar_radius_m=1.155 * R_SUN_M,
        reference_pressure_bar=0.01,
        mean_molecular_weight_u=2.33,
        default_cloud_pressure_bar=0.10,
        citation="Torres et al. (2008); Sing et al. (2016, Nature 529, 59)",
    ),
)


def get_planet_preset(preset_id_or_name: str) -> PlanetAtmospherePreset:
    from ecas.ingestion.planet_resolver import normalize_target_name

    needle = preset_id_or_name.strip().lower()
    norm_needle = normalize_target_name(preset_id_or_name)
    for preset in PLANET_PRESETS:
        if (
            preset.preset_id == needle
            or preset.planet_name.lower() == needle
            or normalize_target_name(preset.planet_name) == norm_needle
            or normalize_target_name(preset.preset_id) == norm_needle
        ):
            return preset
    raise KeyError(f"Unknown planet preset: {preset_id_or_name!r}")


@dataclass(frozen=True)
class MolecularComponentSpec:
    """Validated molecular cross-section curve on a strictly increasing micron grid."""

    formula: str
    isotopologue: str
    dataset: str
    version: str
    source_sha256: str
    vmr: float
    wavelengths_um: tuple[float, ...]
    cross_sections_cm2: tuple[float, ...]
    reference_temperature_k: float | None = None
    broadening_note: str = "Doppler-only zero-pressure cross section"


@dataclass(frozen=True)
class GeneratedForwardModel:
    """Output of the 1D isothermal hydrostatic limb-transmission solver."""

    comparison_input: ComparisonInput
    provenance: AtmosphericModelProvenance
    scale_height_m: float
    covered_wavelengths_um: tuple[float, ...]
    excluded_target_indices: tuple[int, ...]
    species_optical_depth_share: dict[str, tuple[float, ...]]
    dominant_absorber_by_wavelength: tuple[str, ...]
    warnings: tuple[str, ...]

    def to_provenance_dict(self) -> dict:
        return {
            "kind": "generated_isothermal_forward_model",
            "engine_name": ENGINE_NAME,
            "engine_version": ENGINE_VERSION,
            "scale_height_m": self.scale_height_m,
            "warnings": list(self.warnings),
            "atmospheric_model_provenance": asdict(self.provenance),
        }


@dataclass(frozen=True)
class SpeciesAttributionEntry:
    """Fixed-model leave-one-out attribution summary for one molecular component."""

    formula: str
    vmr: float
    max_opacity_share: float
    peak_wavelength_um: float
    full_rms: float
    without_species_rms: float
    delta_rms: float
    full_weighted_q: float | None = None
    without_species_weighted_q: float | None = None
    delta_weighted_q: float | None = None


def component_from_cached_exomol(result, vmr: float) -> MolecularComponentSpec:
    """Convert a cached ExoMol RetrievedCrossSection (cm^-1, cm^2/molecule) to microns."""
    if isinstance(vmr, bool) or not isinstance(vmr, (int, float)) or not math.isfinite(vmr) or vmr < 0.0 or vmr > 1.0:
        raise ValueError("Volume mixing ratio (vmr) must be a finite number in [0, 1]")
    product = getattr(result, "product", result)
    request = getattr(result, "request", None)
    temp_k = float(request.temperature) if request is not None else None

    pts = [(float(nu), float(sig)) for nu, sig in product.points if float(nu) > 0.0]
    if len(pts) < 3:
        raise ValueError("Cached ExoMol product requires at least 3 positive wavenumber points")
    nu_arr = np.array([p[0] for p in pts], dtype=float)
    sig_arr = np.array([p[1] for p in pts], dtype=float)
    lam_um = 10000.0 / nu_arr
    order = np.argsort(lam_um)
    lam_sorted = lam_um[order]
    sig_sorted = np.maximum(sig_arr[order], 0.0)
    if not np.all(np.diff(lam_sorted) > 0):
        raise ValueError("Converted ExoMol wavelengths are not strictly increasing")

    prov = product.provenance
    return MolecularComponentSpec(
        formula=prov.molecule,
        isotopologue=prov.isotopologue,
        dataset=prov.dataset,
        version="ExoMol-sigma",
        source_sha256=product.source_sha256,
        vmr=float(vmr),
        wavelengths_um=tuple(float(x) for x in lam_sorted),
        cross_sections_cm2=tuple(float(y) for y in sig_sorted),
        reference_temperature_k=temp_k,
        broadening_note="ExoMol zero-pressure Doppler-broadened cross section",
    )


def component_from_cross_section_spectrum(
    spectrum,
    *,
    source_sha256: str,
    formula: str,
    vmr: float,
    isotopologue: str = "natural",
    dataset: str = "laboratory_or_custom",
    version: str = "1.0",
    reference_temperature_k: float | None = None,
) -> MolecularComponentSpec:
    """Build a MolecularComponentSpec from an imported UV-Vis or IR cross-section SpectrumData."""
    if spectrum.signal_unit != "cm^2/molecule":
        raise ValueError(
            f"Cross-section component requires signal_unit 'cm^2/molecule', got {spectrum.signal_unit!r}"
        )
    if isinstance(vmr, bool) or not isinstance(vmr, (int, float)) or not math.isfinite(vmr) or vmr < 0.0 or vmr > 1.0:
        raise ValueError("Volume mixing ratio (vmr) must be a finite number in [0, 1]")

    coords = np.array([float(r["wavelength"]) for r in spectrum.rows], dtype=float)
    sigs = np.array([float(r["signal"]) for r in spectrum.rows], dtype=float)
    if len(coords) < 3 or np.any(coords <= 0) or np.any(sigs < 0):
        raise ValueError("Cross-section spectrum requires >= 3 positive coordinates and non-negative cross sections")

    unit = (spectrum.axis_unit or "").strip().lower()
    if unit in ("microns", "um", "micron"):
        lam_um = coords
    elif unit in ("nm", "nanometers"):
        lam_um = coords * 1e-3
    elif unit in ("angstrom", "angstroms"):
        lam_um = coords * 1e-4
    elif unit in ("cm^-1", "cm-1", "1/cm"):
        lam_um = 10000.0 / coords
    else:
        raise ValueError(f"Unsupported cross-section axis_unit: {spectrum.axis_unit!r}")

    order = np.argsort(lam_um)
    lam_sorted = lam_um[order]
    sig_sorted = sigs[order]
    if not np.all(np.diff(lam_sorted) > 0):
        raise ValueError("Cross-section wavelengths must be strictly distinct after sorting")

    return MolecularComponentSpec(
        formula=formula.strip(),
        isotopologue=isotopologue.strip(),
        dataset=dataset.strip(),
        version=version.strip(),
        source_sha256=source_sha256,
        vmr=float(vmr),
        wavelengths_um=tuple(float(x) for x in lam_sorted),
        cross_sections_cm2=tuple(float(y) for y in sig_sorted),
        reference_temperature_k=reference_temperature_k,
        broadening_note=f"Imported {spectrum.signal_type or 'cross-section'} spectrum",
    )


def build_illustrative_band_component(
    formula: str,
    vmr: float,
    *,
    wavelength_min_um: float = 0.25,
    wavelength_max_um: float = 18.0,
    n_grid_points: int = 1200,
) -> MolecularComponentSpec:
    """Construct a broadband synthetic band-envelope component for quick exploratory previews.

    Explicitly tagged with dataset=ILLUSTRATIVE_DATASET_ID so provenance and UI warnings
    always distinguish smooth band templates from line-by-line ExoMol/HITRAN cross sections.
    """
    key = formula.strip()
    if key not in _ILLUSTRATIVE_BAND_LIBRARY:
        raise KeyError(
            f"Unsupported illustrative species {formula!r}; choose from {', '.join(ILLUSTRATIVE_SPECIES)}"
        )
    if isinstance(vmr, bool) or not isinstance(vmr, (int, float)) or not math.isfinite(vmr) or vmr < 0.0 or vmr > 1.0:
        raise ValueError("Volume mixing ratio (vmr) must be a finite number in [0, 1]")
    if wavelength_min_um <= 0.0 or wavelength_max_um <= wavelength_min_um or n_grid_points < 10:
        raise ValueError("Invalid wavelength range or grid resolution for illustrative band component")

    isotopologue, bands = _ILLUSTRATIVE_BAND_LIBRARY[key]
    lam = np.linspace(float(wavelength_min_um), float(wavelength_max_um), int(n_grid_points))
    sigma = np.full_like(lam, 1.0e-30)
    for center_um, peak_cm2, width_um in bands:
        sigma = sigma + peak_cm2 * np.exp(-0.5 * ((lam - center_um) / width_um) ** 2)

    spec_payload = json.dumps(
        {
            "dataset": ILLUSTRATIVE_DATASET_ID,
            "formula": key,
            "isotopologue": isotopologue,
            "bands": bands,
            "range_um": [float(wavelength_min_um), float(wavelength_max_um), int(n_grid_points)],
        },
        sort_keys=True,
    ).encode("utf-8")
    digest = sha256(spec_payload).hexdigest()

    return MolecularComponentSpec(
        formula=key,
        isotopologue=isotopologue,
        dataset=ILLUSTRATIVE_DATASET_ID,
        version="1.0-template",
        source_sha256=digest,
        vmr=float(vmr),
        wavelengths_um=tuple(float(x) for x in lam),
        cross_sections_cm2=tuple(float(y) for y in sigma),
        reference_temperature_k=None,
        broadening_note="Synthetic broadband Gaussian band-center envelope (not a line-by-line opacity)",
    )


def lecavelier_analytic_transit_depth(
    *,
    wavelengths_um: Sequence[float],
    sigma_mix_cm2: Sequence[float],
    temperature_k: float,
    gravity_m_s2: float,
    planet_radius_m: float,
    stellar_radius_m: float,
    reference_pressure_bar: float,
    mean_molecular_weight_u: float,
) -> np.ndarray:
    """Analytical cloud-free optically thick transit depth (Lecavelier des Etangs et al. 2008; Heng & Kitzmann 2017).

    Used as a peer-reviewed mathematical verification benchmark for the numerical
    spherical-shell chord integrator in the optically thick regime (tau_eq >> 1).
    """
    scale_height = (K_BOLTZMANN * temperature_k) / (mean_molecular_weight_u * ATOMIC_MASS_UNIT * gravity_m_s2)
    n0 = (reference_pressure_bar * BAR_TO_PA) / (K_BOLTZMANN * temperature_k)
    sigma_m2 = np.asarray(sigma_mix_cm2, dtype=float) * CM2_TO_M2
    tau_eq = n0 * sigma_m2 * math.sqrt(2.0 * math.pi * planet_radius_m * scale_height)
    r_eff = planet_radius_m + scale_height * (EULER_MASCHERONI + np.log(np.maximum(tau_eq, 1e-300)))
    return (r_eff / stellar_radius_m) ** 2


def generate_isothermal_transmission_model(
    *,
    target_wavelengths_um: Sequence[float],
    temperature_k: float,
    gravity_m_s2: float,
    planet_radius_m: float,
    stellar_radius_m: float,
    reference_pressure_bar: float = 0.01,
    mean_molecular_weight_u: float = 2.33,
    components: Sequence[MolecularComponentSpec] = (),
    cloud_pressure_bar: float | None = 0.01,
    deep_boundary_pressure_bar: float = 10.0,
    haze_multiplier: float = 1.0,
    haze_slope: float = 4.0,
    signal_unit: str = "percent",
    coordinate_frame: str = "barycentric",
    response_id: str = "broadband_model_grid_v1",
    response_evidence: str = "Generated on caller wavelength grid",
    source_id: str | None = None,
    n_altitude_layers: int = 160,
) -> GeneratedForwardModel:
    """Compute a 1D isothermal hydrostatic transmission spectrum via spherical-shell chord quadrature."""
    for name, val in (
        ("temperature_k", temperature_k),
        ("gravity_m_s2", gravity_m_s2),
        ("planet_radius_m", planet_radius_m),
        ("stellar_radius_m", stellar_radius_m),
        ("reference_pressure_bar", reference_pressure_bar),
        ("mean_molecular_weight_u", mean_molecular_weight_u),
        ("deep_boundary_pressure_bar", deep_boundary_pressure_bar),
    ):
        if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or val <= 0.0:
            raise ValueError(f"{name} must be a finite positive number")
    if haze_multiplier < 0.0 or not math.isfinite(haze_multiplier):
        raise ValueError("haze_multiplier must be finite and non-negative")
    if signal_unit not in ("percent", "fraction"):
        raise ValueError(f"signal_unit must be 'percent' or 'fraction', got {signal_unit!r}")

    raw_grid = np.asarray(target_wavelengths_um, dtype=float)
    if raw_grid.ndim != 1 or len(raw_grid) < 3 or not np.isfinite(raw_grid).all() or np.any(raw_grid <= 0.0):
        raise ValueError("target_wavelengths_um requires >= 3 finite positive wavelengths")
    if not np.all(np.diff(raw_grid) > 0):
        raise ValueError("target_wavelengths_um must be strictly increasing")

    total_trace_vmr = sum(c.vmr for c in components)
    if total_trace_vmr > 1.0 + 1e-12:
        raise ValueError(f"Sum of species VMRs ({total_trace_vmr:.4g}) cannot exceed 1.0")
    bg_vmr = max(0.0, 1.0 - total_trace_vmr)

    # Determine non-extrapolated shared wavelength domain across all active molecular components
    low_bound = float(raw_grid[0])
    high_bound = float(raw_grid[-1])
    for comp in components:
        low_bound = max(low_bound, float(comp.wavelengths_um[0]))
        high_bound = min(high_bound, float(comp.wavelengths_um[-1]))

    covered_mask = (raw_grid >= low_bound) & (raw_grid <= high_bound)
    included_idx = tuple(int(i) for i in np.nonzero(covered_mask)[0])
    excluded_idx = tuple(int(i) for i in np.nonzero(~covered_mask)[0])
    if len(included_idx) < 3:
        raise ValueError(
            f"Active molecular cross sections cover fewer than 3 target wavelengths "
            f"(overlap [{low_bound:.4g}, {high_bound:.4g}] um vs target [{raw_grid[0]:.4g}, {raw_grid[-1]:.4g}] um). "
            "Download or select molecular cross sections covering the observation's wavelength range."
        )
    lam = raw_grid[list(included_idx)]

    scale_height = (K_BOLTZMANN * temperature_k) / (
        mean_molecular_weight_u * ATOMIC_MASS_UNIT * gravity_m_s2
    )
    if scale_height <= 0.0 or scale_height > 0.25 * planet_radius_m:
        raise ValueError(
            f"Unphysical hydrostatic scale height H={scale_height:.3e} m compared to Rp={planet_radius_m:.3e} m"
        )

    # Determine opaque base altitude (either grey cloud deck P_cloud or deep continuum boundary)
    effective_base_p = deep_boundary_pressure_bar
    if cloud_pressure_bar is not None:
        if not math.isfinite(cloud_pressure_bar) or cloud_pressure_bar <= 0.0:
            raise ValueError("cloud_pressure_bar must be positive when specified")
        effective_base_p = min(deep_boundary_pressure_bar, cloud_pressure_bar)

    # Continuum Rayleigh/haze extinction per particle (cm^2 -> m^2)
    sigma_rayleigh_cm2 = (
        bg_vmr
        * haze_multiplier
        * H2_RAYLEIGH_SIGMA0_CM2
        * ((H2_RAYLEIGH_LAMBDA0_UM / lam) ** haze_slope)
    )
    species_contrib_cm2: dict[str, np.ndarray] = {
        "H2/He_continuum": sigma_rayleigh_cm2.copy()
    }
    sigma_mix_cm2 = sigma_rayleigh_cm2.copy()

    warnings: list[str] = []
    opacity_specs: list[OpacitySourceSpec] = []
    species_params: list[tuple[str, float]] = [("H2_He_background", float(bg_vmr))]

    for comp in components:
        comp_lam = np.asarray(comp.wavelengths_um, dtype=float)
        comp_sig = np.asarray(comp.cross_sections_cm2, dtype=float)
        interp_sig_cm2 = np.interp(lam, comp_lam, comp_sig)
        weighted_sig = comp.vmr * interp_sig_cm2
        species_contrib_cm2[comp.formula] = (
            species_contrib_cm2.get(comp.formula, np.zeros_like(lam)) + weighted_sig
        )
        sigma_mix_cm2 = sigma_mix_cm2 + weighted_sig
        opacity_specs.append(
            OpacitySourceSpec(
                formula=comp.formula,
                isotopologue=comp.isotopologue,
                dataset=comp.dataset,
                version=comp.version,
                source_sha256=comp.source_sha256,
            )
        )
        species_params.append((comp.formula, float(comp.vmr)))
        if comp.dataset == ILLUSTRATIVE_DATASET_ID:
            warnings.append(
                f"{comp.formula} uses a synthetic broadband Gaussian band-center template "
                f"({ILLUSTRATIVE_DATASET_ID}); download real ExoMol/HITRAN cross sections "
                "for line-resolved quantitative opacity modeling."
            )
        elif "zero-pressure" in comp.broadening_note.lower():
            warnings.append(
                f"{comp.formula} ({comp.dataset}): uses zero-pressure Doppler cross sections; "
                "pressure-broadened line wings at P > 0.01 bar are neglected."
            )
        if comp.reference_temperature_k is not None and abs(comp.reference_temperature_k - temperature_k) > 150.0:
            warnings.append(
                f"{comp.formula} cross section was tabulated at {comp.reference_temperature_k:g} K "
                f"while model T={temperature_k:g} K (delta={abs(comp.reference_temperature_k - temperature_k):g} K)."
            )

    if not opacity_specs:
        # Continuum-only baseline model still records an explicit H2/He Rayleigh opacity spec
        continuum_hash = sha256(b"H2-Rayleigh-Lecavelier2008-5.31e-27cm2-0.35um").hexdigest()
        opacity_specs.append(
            OpacitySourceSpec(
                formula="H2",
                isotopologue="1H2",
                dataset="Lecavelier2008-Rayleigh",
                version="2008",
                source_sha256=continuum_hash,
            )
        )

    sigma_mix_m2 = sigma_mix_cm2 * CM2_TO_M2
    n0_ref = (reference_pressure_bar * BAR_TO_PA) / (K_BOLTZMANN * temperature_k)
    max_sigma_m2 = float(np.max(sigma_mix_m2)) if len(sigma_mix_m2) > 0 else 0.0
    tau_eq_max = n0_ref * max_sigma_m2 * math.sqrt(2.0 * math.pi * planet_radius_m * scale_height)
    optically_thin_top = scale_height * (math.log(max(tau_eq_max, 1.0)) + 10.0)

    z_base = scale_height * math.log(reference_pressure_bar / effective_base_p)
    z_top = max(z_base + 8.0 * scale_height, 18.0 * scale_height, optically_thin_top)
    r_base = planet_radius_m + z_base
    r_top = planet_radius_m + z_top
    if r_base <= 0.0:
        raise ValueError("Base radius r_base became non-positive; check reference/cloud pressures")

    # Spherical shell edges and midpoints
    r_edges = np.linspace(r_base, r_top, n_altitude_layers + 1)
    dr = np.diff(r_edges)
    r_mid = 0.5 * (r_edges[:-1] + r_edges[1:])
    z_mid = r_mid - planet_radius_m
    p_mid_pa = (reference_pressure_bar * BAR_TO_PA) * np.exp(-z_mid / scale_height)
    n_mid_m3 = p_mid_pa / (K_BOLTZMANN * temperature_k)

    # Exact spherical-shell geometric path lengths L[j, k] for impact parameter b_j = r_mid[j], shell k >= j
    b_sq = r_mid[:, None] ** 2
    r_outer_sq = r_edges[1:][None, :] ** 2
    r_inner_sq = r_edges[:-1][None, :] ** 2
    upper_mask = np.triu(np.ones((n_altitude_layers, n_altitude_layers), dtype=bool), k=0)
    chord_outer = np.sqrt(np.maximum(r_outer_sq - b_sq, 0.0))
    chord_inner = np.sqrt(np.maximum(r_inner_sq - b_sq, 0.0))
    chord_lengths = np.where(upper_mask, 2.0 * (chord_outer - chord_inner), 0.0)
    slant_column_m2 = chord_lengths @ n_mid_m3  # shape (n_altitude_layers,)
    tau_chord = np.outer(slant_column_m2, sigma_mix_m2)  # shape (n_layers, n_wavelengths)
    absorptance = -np.expm1(-tau_chord)  # accurate 1 - exp(-tau) even for tiny tau
    annulus_area = 2.0 * ((r_mid * dr)[:, None] * absorptance).sum(axis=0)
    r_eff_sq = (r_base ** 2) + annulus_area
    depth_fraction = r_eff_sq / (stellar_radius_m ** 2)
    out_values = depth_fraction * 100.0 if signal_unit == "percent" else depth_fraction

    # Per-wavelength optical-depth attribution share
    safe_denom = np.where(sigma_mix_cm2 > 0.0, sigma_mix_cm2, 1.0)
    share_map: dict[str, tuple[float, ...]] = {}
    ordered_names = list(species_contrib_cm2.keys())
    share_matrix = np.zeros((len(ordered_names), len(lam)), dtype=float)
    for idx_s, s_name in enumerate(ordered_names):
        s_share = np.where(sigma_mix_cm2 > 0.0, species_contrib_cm2[s_name] / safe_denom, 0.0)
        share_map[s_name] = tuple(float(v) for v in s_share)
        share_matrix[idx_s] = s_share
    dom_indices = np.argmax(share_matrix, axis=0)
    dominant = tuple(ordered_names[int(i)] for i in dom_indices)

    cloud_desc = (
        f"Opaque gray cloud deck at {cloud_pressure_bar:g} bar; "
        if cloud_pressure_bar is not None
        else f"Cloud-free down to {deep_boundary_pressure_bar:g} bar boundary; "
    )
    cloud_desc += f"H2 Rayleigh haze_multiplier={haze_multiplier:g}, slope={haze_slope:g}"

    provenance = AtmosphericModelProvenance(
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        temperature_pressure_profile=f"Isothermal hydrostatic T={temperature_k:g} K, mu={mean_molecular_weight_u:g} u",
        abundance_convention="uniform_volume_mixing_ratio",
        species_parameters=tuple(species_params),
        opacity_sources=tuple(opacity_specs),
        gravity_m_s2=float(gravity_m_s2),
        reference_pressure_bar=float(reference_pressure_bar),
        planet_radius_m=float(planet_radius_m),
        stellar_radius_m=float(stellar_radius_m),
        continuum_and_clouds=cloud_desc,
    )
    validate_model_provenance(provenance)

    # Deterministic content-addressed SHA-256 over provenance + coordinates + values
    canonical_payload = json.dumps(
        {
            "provenance": asdict(provenance),
            "coordinates": [float(x) for x in lam],
            "values": [float(y) for y in out_values],
            "signal_unit": signal_unit,
            "coordinate_frame": coordinate_frame,
            "response_id": response_id,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    model_sha256 = sha256(canonical_payload).hexdigest()

    species_tag = "+".join(c.formula for c in components) if components else "continuum-only"
    resolved_source_id = source_id or f"isothermal-{species_tag}-{temperature_k:g}K"

    comp_input = forward_model_input(
        source_id=resolved_source_id,
        source_sha256=model_sha256,
        provenance=provenance,
        axis_unit="microns",
        signal_unit=signal_unit,
        coordinate_frame=coordinate_frame,
        response_id=response_id,
        response_evidence=response_evidence,
        coordinates=tuple(float(x) for x in lam),
        values=tuple(float(y) for y in out_values),
    )

    # Deduplicate warnings while preserving order
    dedup_warnings = tuple(dict.fromkeys(warnings))
    return GeneratedForwardModel(
        comparison_input=comp_input,
        provenance=provenance,
        scale_height_m=float(scale_height),
        covered_wavelengths_um=tuple(float(x) for x in lam),
        excluded_target_indices=excluded_idx,
        species_optical_depth_share=share_map,
        dominant_absorber_by_wavelength=dominant,
        warnings=dedup_warnings,
    )


def generate_leave_one_out_models(
    *,
    target_wavelengths_um: Sequence[float],
    temperature_k: float,
    gravity_m_s2: float,
    planet_radius_m: float,
    stellar_radius_m: float,
    components: Sequence[MolecularComponentSpec],
    reference_pressure_bar: float = 0.01,
    mean_molecular_weight_u: float = 2.33,
    cloud_pressure_bar: float | None = 0.01,
    haze_multiplier: float = 1.0,
    haze_slope: float = 4.0,
    signal_unit: str = "percent",
    coordinate_frame: str = "barycentric",
    response_id: str = "broadband_model_grid_v1",
    response_evidence: str = "Generated on caller wavelength grid",
) -> tuple[GeneratedForwardModel, dict[str, GeneratedForwardModel]]:
    """Generate the full multi-molecule forward model and leave-one-out models per species.

    All leave-one-out models are evaluated on the exact shared wavelength grid of the
    full model so candidate comparisons satisfy identical coordinate support.
    """
    full_model = generate_isothermal_transmission_model(
        target_wavelengths_um=target_wavelengths_um,
        temperature_k=temperature_k,
        gravity_m_s2=gravity_m_s2,
        planet_radius_m=planet_radius_m,
        stellar_radius_m=stellar_radius_m,
        reference_pressure_bar=reference_pressure_bar,
        mean_molecular_weight_u=mean_molecular_weight_u,
        components=components,
        cloud_pressure_bar=cloud_pressure_bar,
        haze_multiplier=haze_multiplier,
        haze_slope=haze_slope,
        signal_unit=signal_unit,
        coordinate_frame=coordinate_frame,
        response_id=response_id,
        response_evidence=response_evidence,
    )
    shared_grid = full_model.covered_wavelengths_um
    leave_one_out: dict[str, GeneratedForwardModel] = {}
    seen_formulas: list[str] = []
    for comp in components:
        if comp.formula not in seen_formulas:
            seen_formulas.append(comp.formula)

    for omitted_formula in seen_formulas:
        remaining = [c for c in components if c.formula != omitted_formula]
        loo_model = generate_isothermal_transmission_model(
            target_wavelengths_um=shared_grid,
            temperature_k=temperature_k,
            gravity_m_s2=gravity_m_s2,
            planet_radius_m=planet_radius_m,
            stellar_radius_m=stellar_radius_m,
            reference_pressure_bar=reference_pressure_bar,
            mean_molecular_weight_u=mean_molecular_weight_u,
            components=remaining,
            cloud_pressure_bar=cloud_pressure_bar,
            haze_multiplier=haze_multiplier,
            haze_slope=haze_slope,
            signal_unit=signal_unit,
            coordinate_frame=coordinate_frame,
            response_id=response_id,
            response_evidence=response_evidence,
            source_id=f"{full_model.comparison_input.source_id}-without-{omitted_formula}",
        )
        leave_one_out[omitted_formula] = loo_model

    return full_model, leave_one_out


def summarize_leave_one_out_attribution(
    observation: ComparisonInput,
    full_model: GeneratedForwardModel,
    leave_one_out_models: dict[str, GeneratedForwardModel],
    *,
    weighted: bool = False,
    cross_dataset_independent: bool = False,
    aligned_full_input: ComparisonInput | None = None,
    aligned_loo_inputs: dict[str, ComparisonInput] | None = None,
) -> tuple[SpeciesAttributionEntry, ...]:
    """Quantify per-species leave-one-out residual change (Delta-RMS and Delta-Q).

    Positive delta_rms or delta_weighted_q indicates that removing the species
    worsens agreement with the observation under this fixed atmospheric parameter set.
    """
    from .residuals import evaluate_residuals

    eval_full = aligned_full_input if aligned_full_input is not None else full_model.comparison_input
    full_diag = evaluate_residuals(
        observation,
        eval_full,
        weighted=weighted,
        cross_dataset_independent=cross_dataset_independent,
    )
    vmr_by_species: dict[str, float] = {}
    for k, v in full_model.provenance.species_parameters:
        if k != "H2_He_background":
            vmr_by_species[k] = vmr_by_species.get(k, 0.0) + float(v)

    entries: list[SpeciesAttributionEntry] = []
    model_lam = np.asarray(full_model.covered_wavelengths_um, dtype=float)
    obs_min = float(observation.coordinates[0])
    obs_max = float(observation.coordinates[-1])
    in_band_mask = (model_lam >= obs_min) & (model_lam <= obs_max)

    for formula, loo_model in leave_one_out_models.items():
        eval_loo = (
            aligned_loo_inputs[formula]
            if aligned_loo_inputs is not None and formula in aligned_loo_inputs
            else loo_model.comparison_input
        )
        loo_diag = evaluate_residuals(
            observation,
            eval_loo,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
        )
        raw_shares = np.asarray(
            full_model.species_optical_depth_share.get(formula, np.zeros_like(model_lam)),
            dtype=float,
        )
        if len(raw_shares) == len(model_lam) and np.any(in_band_mask):
            band_lam = model_lam[in_band_mask]
            band_shares = raw_shares[in_band_mask]
            peak_idx = int(np.argmax(band_shares))
            max_share = float(band_shares[peak_idx])
            peak_lam = float(band_lam[peak_idx])
        elif len(raw_shares) > 0 and len(raw_shares) == len(model_lam):
            peak_idx = int(np.argmax(raw_shares))
            max_share = float(raw_shares[peak_idx])
            peak_lam = float(model_lam[peak_idx])
        else:
            max_share = 0.0
            peak_lam = 0.0

        dq = None
        if weighted and full_diag.weighted_residual_quadratic is not None and loo_diag.weighted_residual_quadratic is not None:
            dq = float(loo_diag.weighted_residual_quadratic - full_diag.weighted_residual_quadratic)

        entries.append(
            SpeciesAttributionEntry(
                formula=formula,
                vmr=vmr_by_species.get(formula, 0.0),
                max_opacity_share=max_share,
                peak_wavelength_um=peak_lam,
                full_rms=full_diag.rms_residual,
                without_species_rms=loo_diag.rms_residual,
                delta_rms=float(loo_diag.rms_residual - full_diag.rms_residual),
                full_weighted_q=full_diag.weighted_residual_quadratic,
                without_species_weighted_q=loo_diag.weighted_residual_quadratic,
                delta_weighted_q=dq,
            )
        )
    return tuple(entries)
