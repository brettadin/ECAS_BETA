"""Independent scientific benchmarks and physical validation suite for forward_model.py.

Addresses Priority 2 (Forward-Model Scientific Validation) from the 29 October 2026
review recommendations (Categories A through H):
- Category A: Baseline continuum (zero-opacity limit and Lecavelier Rayleigh slope).
- Category B: Molecular-opacity contribution and band attribution.
- Category C: Abundance variation (monotonicity and logarithmic scale-height growth).
- Category D: Temperature variation (scale-height linearity and feature amplitude scaling).
- Category E: Gravity variation (scale-height inverse scaling and atmospheric compression).
- Category F: Cloud-boundary behavior (gray cloud-deck floor and feature muting).
- Category G: Wavelength-support boundaries (intersection and exclusion diagnostics).
- Category H: Numerical stability, layer convergence, parameter edge cases, and error rejection.
"""
import math
import numpy as np
import pytest

from ecas.comparison.forward_model import (
    AtmosphericModelProvenance,
    OpacitySourceSpec,
    validate_model_provenance,
)
from ecas.comparison.model_generator import (
    ENGINE_NAME,
    ENGINE_VERSION,
    MolecularComponentSpec,
    PlanetAtmospherePreset,
    build_illustrative_band_component,
    generate_isothermal_transmission_model,
    get_planet_preset,
    lecavelier_analytic_transit_depth,
)


# Helper: construct a synthetic Gaussian absorption band
def _make_gaussian_component(
    formula: str = "TestMol",
    vmr: float = 1e-3,
    center_um: float = 2.0,
    peak_cm2: float = 1e-20,
    width_um: float = 0.05,
    lam_min: float = 1.0,
    lam_max: float = 3.0,
    n_points: int = 51,
) -> MolecularComponentSpec:
    lam = np.linspace(lam_min, lam_max, n_points)
    sig = peak_cm2 * np.exp(-0.5 * ((lam - center_um) / width_um) ** 2)
    return MolecularComponentSpec(
        formula=formula,
        isotopologue=f"1{formula}",
        dataset="ScientificBenchmark",
        version="1.0",
        source_sha256="c" * 64,
        vmr=vmr,
        wavelengths_um=tuple(float(x) for x in lam),
        cross_sections_cm2=tuple(float(y) for y in sig),
    )


# ==============================================================================
# Category A: Baseline Continuum
# ==============================================================================

def test_category_a_zero_opacity_baseline_continuum():
    """Verify exact analytic geometric limit (Rp/Rstar)^2 when atmospheric opacity is zero."""
    preset = get_planet_preset("WASP-39 b")
    grid = np.linspace(1.0, 5.0, 25)

    # When cloud pressure equals reference pressure, z_base = 0 and r_base = Rp.
    # With haze_multiplier=0 and no molecular components, opacity is zero everywhere above r_base.
    model_frac = generate_isothermal_transmission_model(
        target_wavelengths_um=grid,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        reference_pressure_bar=0.01,
        cloud_pressure_bar=0.01,
        haze_multiplier=0.0,
        signal_unit="fraction",
    )
    expected_fraction = (preset.planet_radius_m / preset.stellar_radius_m) ** 2
    vals_frac = np.asarray(model_frac.comparison_input.values, dtype=float)
    assert np.allclose(vals_frac, expected_fraction, atol=1e-15, rtol=1e-15)

    # In percent units:
    model_pct = generate_isothermal_transmission_model(
        target_wavelengths_um=grid,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        reference_pressure_bar=0.01,
        cloud_pressure_bar=0.01,
        haze_multiplier=0.0,
        signal_unit="percent",
    )
    vals_pct = np.asarray(model_pct.comparison_input.values, dtype=float)
    assert np.allclose(vals_pct, expected_fraction * 100.0, atol=1e-13, rtol=1e-13)


def test_category_a_rayleigh_scattering_slope_and_monotonicity():
    """Verify Lecavelier et al. (2008) Rayleigh slope d(R_eff)/d(ln lambda) = -4*H in optically thick regime."""
    preset = get_planet_preset("WASP-39 b")
    # Rayleigh cross section is optically thick in the NUV/optical
    grid_opt = np.linspace(0.35, 0.60, 30)

    model_rayleigh = generate_isothermal_transmission_model(
        target_wavelengths_um=grid_opt,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        reference_pressure_bar=1.0,
        cloud_pressure_bar=None,
        deep_boundary_pressure_bar=100.0,
        haze_multiplier=5.0,
        haze_slope=4.0,
        signal_unit="fraction",
        n_altitude_layers=400,
    )
    vals = np.asarray(model_rayleigh.comparison_input.values, dtype=float)

    # Invariant 1: Rayleigh scattering cross section falls as lambda^-4, so transit depth strictly decreases
    diffs = np.diff(vals)
    assert np.all(diffs < 0.0), "Rayleigh transmission spectrum must strictly decrease with wavelength"

    # Invariant 2: Lecavelier des Etangs et al. (2008) logarithmic slope d(R_eff)/d(ln lambda) = -alpha * H
    r_eff = preset.stellar_radius_m * np.sqrt(vals)
    ln_lam = np.log(grid_opt)
    poly = np.polyfit(ln_lam, r_eff, 1)
    measured_slope = poly[0]
    expected_slope = -4.0 * model_rayleigh.scale_height_m
    rel_err = abs(measured_slope - expected_slope) / abs(expected_slope)
    assert rel_err < 0.01, f"Rayleigh slope relative error {rel_err:.4f} exceeds 1%"


# ==============================================================================
# Category B: Molecular-Opacity Contribution
# ==============================================================================

def test_category_b_molecular_opacity_injection_and_attribution():
    """Verify that adding a known molecular band increases transit depth and dominates attribution at band peak."""
    preset = get_planet_preset("WASP-39 b")
    grid = np.linspace(1.0, 3.0, 51)

    # 1. Zero-haze baseline vs molecular addition
    m_base = generate_isothermal_transmission_model(
        target_wavelengths_um=grid,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        haze_multiplier=0.0,
        signal_unit="fraction",
    )

    # 2. Model with molecular band planted at 2.0 um
    comp = _make_gaussian_component(formula="H2O", vmr=1e-3, center_um=2.0, peak_cm2=1e-20)
    m_mol = generate_isothermal_transmission_model(
        target_wavelengths_um=grid,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        haze_multiplier=0.0,
        components=(comp,),
        signal_unit="fraction",
    )

    v_base = np.asarray(m_base.comparison_input.values, dtype=float)
    v_mol = np.asarray(m_mol.comparison_input.values, dtype=float)

    # Invariant 1: Opacity contribution must non-decrease transit depth everywhere
    assert np.all(v_mol >= v_base - 1e-15)

    # Invariant 2: Maximum excess depth occurs at the molecular band center (2.0 um, index 25)
    delta_v = v_mol - v_base
    peak_idx = int(np.argmax(delta_v))
    assert peak_idx == 25
    assert grid[peak_idx] == pytest.approx(2.0)
    # Significant transit feature amplitude (> 3000 ppm)
    assert delta_v[peak_idx] > 3.0e-3

    # Invariant 3: Species attribution share peaks at band center
    h2o_share = np.asarray(m_mol.species_optical_depth_share["H2O"])
    assert h2o_share[peak_idx] == pytest.approx(np.max(h2o_share))
    assert h2o_share[peak_idx] > 0.99  # H2O dominates completely at 2.0 um
    assert m_mol.dominant_absorber_by_wavelength[peak_idx] == "H2O"


# ==============================================================================
# Category C: Abundance Variation
# ==============================================================================

def test_category_c_abundance_scaling_monotonicity_and_scale_height_growth():
    """Verify strict monotonicity and logarithmic growth d(R_eff)/d(ln VMR) = H across orders of magnitude."""
    preset = get_planet_preset("WASP-39 b")
    grid = np.linspace(1.0, 3.0, 51)
    vmrs = [1e-5, 1e-4, 1e-3, 1e-2]

    models = [
        generate_isothermal_transmission_model(
            target_wavelengths_um=grid,
            temperature_k=preset.temperature_k,
            gravity_m_s2=preset.gravity_m_s2,
            planet_radius_m=preset.planet_radius_m,
            stellar_radius_m=preset.stellar_radius_m,
            reference_pressure_bar=0.1,
            cloud_pressure_bar=None,
            deep_boundary_pressure_bar=100.0,
            haze_multiplier=0.0,
            components=(_make_gaussian_component(vmr=v, center_um=2.0),),
            signal_unit="fraction",
            n_altitude_layers=350,
        )
        for v in vmrs
    ]

    center_idx = 25  # 2.0 um
    peak_depths = [m.comparison_input.values[center_idx] for m in models]

    # Invariant 1: Strict monotonicity with abundance at the absorption feature
    for i in range(len(peak_depths) - 1):
        assert peak_depths[i] < peak_depths[i + 1], f"VMR {vmrs[i]} -> {vmrs[i+1]} did not increase transit depth"

    # Invariant 2: Effective radius growth in optically thick regime d(R_eff)/d(ln xi) = H
    r_effs = [preset.stellar_radius_m * math.sqrt(d) for d in peak_depths]
    H_true = models[0].scale_height_m
    # Measure growth between 1e-4 and 1e-2
    delta_r = r_effs[3] - r_effs[1]
    delta_ln_vmr = math.log(vmrs[3] / vmrs[1])
    measured_H = delta_r / delta_ln_vmr
    rel_err = abs(measured_H - H_true) / H_true
    assert rel_err < 0.015, f"VMR scaling growth rate relative error {rel_err:.4f} exceeds 1.5%"


# ==============================================================================
# Category D: Temperature Variation
# ==============================================================================

def test_category_d_temperature_scaling_on_scale_height_and_feature_amplitude():
    """Verify scale height linearity H ~ T and direct scaling of transmission feature amplitudes."""
    preset = get_planet_preset("WASP-39 b")
    grid = np.linspace(1.0, 3.0, 51)
    comp = _make_gaussian_component(vmr=1e-3, center_um=2.0)
    temps = [400.0, 800.0, 1200.0, 1600.0]

    models = [
        generate_isothermal_transmission_model(
            target_wavelengths_um=grid,
            temperature_k=T,
            gravity_m_s2=preset.gravity_m_s2,
            planet_radius_m=preset.planet_radius_m,
            stellar_radius_m=preset.stellar_radius_m,
            reference_pressure_bar=0.1,
            cloud_pressure_bar=None,
            deep_boundary_pressure_bar=100.0,
            haze_multiplier=0.0,
            components=(comp,),
            signal_unit="fraction",
            n_altitude_layers=300,
        )
        for T in temps
    ]

    # Invariant 1: Scale height must be mathematically linear in T: H / T = constant
    h_over_t = [m.scale_height_m / T for m, T in zip(models, temps)]
    for val in h_over_t[1:]:
        assert val == pytest.approx(h_over_t[0], rel=1e-12)

    # Invariant 2: Feature amplitude (peak - wing) must increase monotonically with T
    amplitudes = [m.comparison_input.values[25] - m.comparison_input.values[0] for m in models]
    for i in range(len(amplitudes) - 1):
        assert amplitudes[i] < amplitudes[i + 1]

    # Invariant 3: Radial amplitude Delta R_eff scales approximately linearly with T
    delta_r = [
        preset.stellar_radius_m * (math.sqrt(m.comparison_input.values[25]) - math.sqrt(m.comparison_input.values[0]))
        for m in models
    ]
    ratio_t = delta_r[-1] / delta_r[0]
    expected_ratio = temps[-1] / temps[0]  # 1600 / 400 = 4.0
    assert abs(ratio_t - expected_ratio) / expected_ratio < 0.05


# ==============================================================================
# Category E: Gravity Variation
# ==============================================================================

def test_category_e_gravity_scaling_on_scale_height_and_feature_compression():
    """Verify inverse gravity scaling H ~ 1/g and atmospheric compression muting transit features."""
    preset = get_planet_preset("WASP-39 b")
    grid = np.linspace(1.0, 3.0, 51)
    comp = _make_gaussian_component(vmr=1e-3, center_um=2.0)
    gravities = [2.5, 5.0, 10.0, 20.0]

    models = [
        generate_isothermal_transmission_model(
            target_wavelengths_um=grid,
            temperature_k=1000.0,
            gravity_m_s2=g,
            planet_radius_m=preset.planet_radius_m,
            stellar_radius_m=preset.stellar_radius_m,
            reference_pressure_bar=0.1,
            cloud_pressure_bar=None,
            deep_boundary_pressure_bar=100.0,
            haze_multiplier=0.0,
            components=(comp,),
            signal_unit="fraction",
            n_altitude_layers=300,
        )
        for g in gravities
    ]

    # Invariant 1: Scale height is strictly inverse to gravity: H * g = constant
    h_times_g = [m.scale_height_m * g for m, g in zip(models, gravities)]
    for val in h_times_g[1:]:
        assert val == pytest.approx(h_times_g[0], rel=1e-12)

    # Invariant 2: Higher gravity compresses the atmosphere, strictly reducing feature amplitude
    amplitudes = [m.comparison_input.values[25] - m.comparison_input.values[0] for m in models]
    for i in range(len(amplitudes) - 1):
        assert amplitudes[i] > amplitudes[i + 1]

    # Invariant 3: Doubling gravity approximately halves radial feature amplitude
    delta_r = [
        preset.stellar_radius_m * (math.sqrt(m.comparison_input.values[25]) - math.sqrt(m.comparison_input.values[0]))
        for m in models
    ]
    # g: 2.5 -> 5.0 (factor of 2)
    ratio_g = delta_r[0] / delta_r[1]
    assert abs(ratio_g - 2.0) / 2.0 < 0.05


# ==============================================================================
# Category F: Cloud-Boundary Behavior
# ==============================================================================

def test_category_f_cloud_deck_truncation_and_monotonicity():
    """Verify that opaque gray cloud decks raise the transit floor and mute spectral contrast."""
    preset = get_planet_preset("WASP-39 b")
    grid = np.linspace(1.0, 3.0, 51)
    comp = _make_gaussian_component(vmr=1e-3, center_um=2.0)
    p_clouds = [1e-4, 1e-2, 1.0, None]

    models = [
        generate_isothermal_transmission_model(
            target_wavelengths_um=grid,
            temperature_k=1000.0,
            gravity_m_s2=preset.gravity_m_s2,
            planet_radius_m=preset.planet_radius_m,
            stellar_radius_m=preset.stellar_radius_m,
            reference_pressure_bar=0.1,
            cloud_pressure_bar=pc,
            deep_boundary_pressure_bar=10.0,
            haze_multiplier=0.0,
            components=(comp,),
            signal_unit="fraction",
            n_altitude_layers=300,
        )
        for pc in p_clouds
    ]
    vals = [np.asarray(m.comparison_input.values, dtype=float) for m in models]

    # Invariant 1: Higher cloud deck (lower cloud pressure) raises baseline transit depth floor
    floors = [v[0] for v in vals]
    assert floors[0] > floors[1] > floors[2] > floors[3]

    # Invariant 2: Across all wavelengths, a higher cloud deck produces greater or equal transit depth
    # (subject only to numerical quadrature discretization <= 1 ppm)
    assert np.all(vals[0] >= vals[1] - 1e-6)
    assert np.all(vals[1] >= vals[2] - 1e-6)
    assert np.all(vals[2] >= vals[3] - 1e-6)

    # Invariant 3: High cloud mutes peak-to-floor contrast
    contrast_high_cloud = vals[0][25] - vals[0][0]
    contrast_cloud_free = vals[3][25] - vals[3][0]
    assert contrast_high_cloud < 0.5 * contrast_cloud_free


# ==============================================================================
# Category G: Wavelength-Support Boundaries
# ==============================================================================

def test_category_g_wavelength_support_boundaries_and_exclusion_diagnostics():
    """Verify that unsupported wavelength regions are never extrapolated and excluded points are tracked."""
    preset = get_planet_preset("K2-18 b")
    # Target grid covers 0.5 to 5.0 um
    target = np.linspace(0.5, 5.0, 46)  # 0.1 um spacing

    # Component 1 covers 1.0 to 4.0 um
    comp1 = _make_gaussian_component(formula="MolA", lam_min=1.0, lam_max=4.0, n_points=31)
    # Component 2 covers 1.5 to 3.5 um
    comp2 = _make_gaussian_component(formula="MolB", lam_min=1.5, lam_max=3.5, n_points=21)

    model = generate_isothermal_transmission_model(
        target_wavelengths_um=target,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(comp1, comp2),
    )

    # The joint covered domain is the exact intersection: [1.5, 3.5] um
    assert min(model.covered_wavelengths_um) >= 1.5 - 1e-9
    assert max(model.covered_wavelengths_um) <= 3.5 + 1e-9

    # Check excluded indices
    for idx in model.excluded_target_indices:
        lam_val = target[idx]
        assert lam_val < 1.5 - 1e-9 or lam_val > 3.5 + 1e-9

    # Check that model coordinates match covered wavelengths exactly
    assert model.comparison_input.coordinates == model.covered_wavelengths_um

    # Non-overlapping components raise ValueError
    comp_far = _make_gaussian_component(formula="FarMol", lam_min=6.0, lam_max=8.0, n_points=21)
    with pytest.raises(ValueError, match="covers? fewer than 3 target wavelengths"):
        generate_isothermal_transmission_model(
            target_wavelengths_um=target,
            temperature_k=preset.temperature_k,
            gravity_m_s2=preset.gravity_m_s2,
            planet_radius_m=preset.planet_radius_m,
            stellar_radius_m=preset.stellar_radius_m,
            components=(comp1, comp_far),
        )


# ==============================================================================
# Category H: Numerical Stability, Layer Convergence, and Edge Cases
# ==============================================================================

def test_category_h_altitude_quadrature_layer_convergence():
    """Verify that spherical-shell chord quadrature converges smoothly as layer count increases."""
    preset = get_planet_preset("WASP-39 b")
    grid = np.linspace(1.0, 3.0, 21)
    comp = _make_gaussian_component(vmr=1e-3, center_um=2.0)

    models = [
        generate_isothermal_transmission_model(
            target_wavelengths_um=grid,
            temperature_k=preset.temperature_k,
            gravity_m_s2=preset.gravity_m_s2,
            planet_radius_m=preset.planet_radius_m,
            stellar_radius_m=preset.stellar_radius_m,
            components=(comp,),
            signal_unit="fraction",
            n_altitude_layers=n,
        )
        for n in (80, 160, 320, 480)
    ]
    vals = [np.asarray(m.comparison_input.values, dtype=float) for m in models]

    # Convergence from 160 to 320 layers < 0.05%
    rel_diff_160_320 = np.max(np.abs(vals[1] - vals[2]) / vals[2])
    assert rel_diff_160_320 < 5e-4, f"160->320 convergence {rel_diff_160_320:.6f} exceeds 5e-4"

    # Convergence from 320 to 480 layers < 0.02%
    rel_diff_320_480 = np.max(np.abs(vals[2] - vals[3]) / vals[3])
    assert rel_diff_320_480 < 2e-4, f"320->480 convergence {rel_diff_320_480:.6f} exceeds 2e-4"


def test_category_h_physical_parameter_validation_and_rejection():
    """Verify that unphysical or malformed input parameters are rejected with explicit ValueErrors."""
    preset = get_planet_preset("WASP-39 b")
    valid_grid = (1.0, 2.0, 3.0)

    # 1. Negative or zero temperatures
    for bad_T in (0.0, -100.0, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="temperature_k must be a finite positive number"):
            generate_isothermal_transmission_model(
                target_wavelengths_um=valid_grid,
                temperature_k=bad_T,
                gravity_m_s2=preset.gravity_m_s2,
                planet_radius_m=preset.planet_radius_m,
                stellar_radius_m=preset.stellar_radius_m,
            )

    # 2. Negative or zero gravity
    for bad_g in (0.0, -9.8, float("nan")):
        with pytest.raises(ValueError, match="gravity_m_s2 must be a finite positive number"):
            generate_isothermal_transmission_model(
                target_wavelengths_um=valid_grid,
                temperature_k=preset.temperature_k,
                gravity_m_s2=bad_g,
                planet_radius_m=preset.planet_radius_m,
                stellar_radius_m=preset.stellar_radius_m,
            )

    # 3. Sum of species VMRs exceeding 1.0
    c1 = _make_gaussian_component(formula="M1", vmr=0.7)
    c2 = _make_gaussian_component(formula="M2", vmr=0.4)
    with pytest.raises(ValueError, match="Sum of species VMRs .* cannot exceed 1.0"):
        generate_isothermal_transmission_model(
            target_wavelengths_um=valid_grid,
            temperature_k=preset.temperature_k,
            gravity_m_s2=preset.gravity_m_s2,
            planet_radius_m=preset.planet_radius_m,
            stellar_radius_m=preset.stellar_radius_m,
            components=(c1, c2),
        )

    # 4. Unphysical escaping scale height H > 0.25 Rp
    with pytest.raises(ValueError, match="Unphysical hydrostatic scale height"):
        generate_isothermal_transmission_model(
            target_wavelengths_um=valid_grid,
            temperature_k=15000.0,
            gravity_m_s2=0.1,
            planet_radius_m=preset.planet_radius_m,
            stellar_radius_m=preset.stellar_radius_m,
        )

    # 5. Invalid wavelength coordinate inputs
    with pytest.raises(ValueError, match="requires >= 3 finite positive wavelengths"):
        generate_isothermal_transmission_model(
            target_wavelengths_um=(1.0, 2.0),  # only 2 points
            temperature_k=preset.temperature_k,
            gravity_m_s2=preset.gravity_m_s2,
            planet_radius_m=preset.planet_radius_m,
            stellar_radius_m=preset.stellar_radius_m,
        )

    with pytest.raises(ValueError, match="must be strictly increasing"):
        generate_isothermal_transmission_model(
            target_wavelengths_um=(1.0, 3.0, 2.0),  # non-monotonic
            temperature_k=preset.temperature_k,
            gravity_m_s2=preset.gravity_m_s2,
            planet_radius_m=preset.planet_radius_m,
            stellar_radius_m=preset.stellar_radius_m,
        )


def test_category_h_extreme_valid_parameter_regimes():
    """Verify solver execution in extreme astrophysical regimes without numerical instability."""
    preset = get_planet_preset("WASP-39 b")
    grid = np.linspace(1.0, 3.0, 21)

    # Regime 1: Ultra-hot Jupiter (T = 2800 K)
    m_hot = generate_isothermal_transmission_model(
        target_wavelengths_um=grid,
        temperature_k=2800.0,
        gravity_m_s2=15.0,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(_make_gaussian_component(vmr=1e-4),),
    )
    assert np.all(np.isfinite(m_hot.comparison_input.values))
    assert np.all(np.asarray(m_hot.comparison_input.values) > 0.0)

    # Regime 2: Cold giant / temperate sub-Neptune (T = 180 K)
    m_cold = generate_isothermal_transmission_model(
        target_wavelengths_um=grid,
        temperature_k=180.0,
        gravity_m_s2=10.0,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(_make_gaussian_component(vmr=1e-4),),
    )
    assert np.all(np.isfinite(m_cold.comparison_input.values))
    assert np.all(np.asarray(m_cold.comparison_input.values) > 0.0)

    # Regime 3: Trace abundance (VMR = 1e-10)
    m_trace = generate_isothermal_transmission_model(
        target_wavelengths_um=grid,
        temperature_k=1000.0,
        gravity_m_s2=10.0,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(_make_gaussian_component(vmr=1e-10),),
    )
    assert np.all(np.isfinite(m_trace.comparison_input.values))

    # Regime 4: High abundance (VMR = 0.95)
    m_heavy = generate_isothermal_transmission_model(
        target_wavelengths_um=grid,
        temperature_k=1000.0,
        gravity_m_s2=10.0,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(_make_gaussian_component(vmr=0.95),),
    )
    assert np.all(np.isfinite(m_heavy.comparison_input.values))
    assert validate_model_provenance(m_heavy.provenance) is not None
