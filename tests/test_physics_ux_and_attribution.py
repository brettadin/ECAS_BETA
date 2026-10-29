"""Verification of 1D limb-transmission RT physics, data-accuracy guards, and plug-and-chug UX."""
from __future__ import annotations

import gc
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from ecas.comparison.eligibility import ComparisonInput, assess
from ecas.comparison.forward_model import validate_model_provenance
from ecas.comparison.inputs import (
    audit_asymmetric_uncertainties,
    audit_observation_bin_semantics,
    extract_observation_bin_edges,
    observation_input,
)
from ecas.comparison.model_generator import (
    ILLUSTRATIVE_DATASET_ID,
    MolecularComponentSpec,
    build_illustrative_band_component,
    component_from_cross_section_spectrum,
    generate_isothermal_transmission_model,
    generate_leave_one_out_models,
    get_planet_preset,
    lecavelier_analytic_transit_depth,
    summarize_leave_one_out_attribution,
)
from ecas.comparison.residuals import evaluate_residuals
from ecas.ingestion.exomol_product import ProductRequest, validate_product
from ecas.ingestion.exomol_product_network import RetrievedCrossSection
from ecas.ingestion.exomol_reference_cache import store_reference
from ecas.ingestion.tabular_formats import import_tabular_spectrum
from ecas.ui.main_window import ECASWindow
from ecas.visualization.reference_plot import reference_display_points

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def window(tmp_path, qapp):
    widget = ECASWindow(
        projects_dir=tmp_path / "projects",
        reference_cache_dir=tmp_path / "cache",
    )
    yield widget
    widget.close()
    gc.collect()


def test_spherical_shell_chord_integrator_matches_lecavelier_analytic_formula():
    """Verify numerical spherical-shell quadrature against Lecavelier des Etangs (2008) / Heng & Kitzmann (2017)."""
    preset = get_planet_preset("WASP-39 b")
    lam = np.linspace(1.0, 5.0, 25)
    #Vary cross section across 4 orders of magnitude in the optically thick cloud-free regime
    log_sigma = np.linspace(-22.5, -18.5, len(lam))
    sigma_cm2 = 10.0 ** log_sigma

    comp = MolecularComponentSpec(
        formula="H2O",
        isotopologue="1H2-16O",
        dataset="AnalyticBenchmark",
        version="1.0",
        source_sha256="a" * 64,
        vmr=1.0,  # pure absorber so sigma_mix == sigma_cm2 with zero Rayleigh background
        wavelengths_um=tuple(float(x) for x in lam),
        cross_sections_cm2=tuple(float(s) for s in sigma_cm2),
    )
    model = generate_isothermal_transmission_model(
        target_wavelengths_um=lam,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        reference_pressure_bar=0.1,
        mean_molecular_weight_u=preset.mean_molecular_weight_u,
        components=(comp,),
        cloud_pressure_bar=None,
        deep_boundary_pressure_bar=100.0,
        haze_multiplier=0.0,
        signal_unit="fraction",
        n_altitude_layers=450,
    )
    analytic = lecavelier_analytic_transit_depth(
        wavelengths_um=lam,
        sigma_mix_cm2=sigma_cm2,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        reference_pressure_bar=0.1,
        mean_molecular_weight_u=preset.mean_molecular_weight_u,
    )
    numerical = np.asarray(model.comparison_input.values, dtype=float)
    # Spherical-shell quadrature includes exact H/Rp curvature corrections (~0.1-0.2%)
    rel_diff = np.abs(numerical - analytic) / analytic
    assert np.max(rel_diff) < 3.0e-3
    validate_model_provenance(model.provenance)


def test_forward_model_generator_never_extrapolates_and_records_warnings():
    preset = get_planet_preset("K2-18 b")
    narrow_comp = MolecularComponentSpec(
        formula="CH4",
        isotopologue="12C-1H4",
        dataset="MM",
        version="ExoMol",
        source_sha256="b" * 64,
        vmr=1e-2,
        wavelengths_um=(1.5, 2.0, 2.5, 3.0, 3.5),
        cross_sections_cm2=(1e-22, 5e-21, 2e-21, 8e-20, 1e-21),
        reference_temperature_k=500.0,
        broadening_note="ExoMol zero-pressure Doppler-broadened cross section",
    )
    target = (1.0, 1.6, 2.2, 2.8, 3.3, 4.5)
    generated = generate_isothermal_transmission_model(
        target_wavelengths_um=target,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(narrow_comp,),
    )
    # 1.0 um and 4.5 um lie outside [1.5, 3.5] um and must be excluded rather than extrapolated
    assert generated.covered_wavelengths_um == (1.6, 2.2, 2.8, 3.3)
    assert generated.excluded_target_indices == (0, 5)
    assert any("zero-pressure" in w for w in generated.warnings)
    assert any("500 K" in w for w in generated.warnings)


def test_leave_one_out_multi_molecule_attribution_identifies_planted_absorbers():
    preset = get_planet_preset("WASP-39 b")
    grid = np.linspace(0.8, 5.0, 120)
    h2o = build_illustrative_band_component("H2O", 1e-3, wavelength_min_um=0.6, wavelength_max_um=6.0)
    co2 = build_illustrative_band_component("CO2", 5e-4, wavelength_min_um=0.6, wavelength_max_um=6.0)
    no2 = build_illustrative_band_component("NO2", 5e-4, wavelength_min_um=0.6, wavelength_max_um=6.0)

    # Synthesize truth observation with H2O + CO2 ONLY (no NO2)
    truth = generate_isothermal_transmission_model(
        target_wavelengths_um=grid,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(h2o, co2),
        cloud_pressure_bar=0.01,
        response_id="synth-prism",
        response_evidence="synthetic benchmark",
    )
    sigma = tuple(0.004 for _ in grid)
    obs = ComparisonInput(
        source_id="synth-wasp39-obs",
        source_sha256="1" * 64,
        role="observation",
        observable="transit_depth",
        axis_unit="microns",
        signal_unit="percent",
        coordinate_frame="barycentric",
        response_id="synth-prism",
        response_evidence="synthetic benchmark",
        coordinates=truth.covered_wavelengths_um,
        values=truth.comparison_input.values,
        noise_kind="independent_gaussian_1sigma",
        noise_evidence="synthetic 40 ppm noise",
        sigma=sigma,
    )

    # Test leave-one-out on H2O + CO2 + spurious NO2
    full_3, loo_3 = generate_leave_one_out_models(
        target_wavelengths_um=grid,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(h2o, co2, no2),
        cloud_pressure_bar=0.01,
        response_id="synth-prism",
        response_evidence="synthetic benchmark",
    )
    entries = {
        e.formula: e
        for e in summarize_leave_one_out_attribution(
            obs, full_3, loo_3, weighted=True, cross_dataset_independent=True
        )
    }
    # Removing planted H2O or CO2 worsens residuals (positive delta_rms & delta_weighted_q)
    assert entries["H2O"].delta_rms > 0.0
    assert entries["CO2"].delta_rms > 0.0
    assert entries["CO2"].delta_weighted_q > 0.0
    # Removing spurious NO2 improves agreement with truth (negative delta_rms)
    assert entries["NO2"].delta_rms < 0.0
    assert any(ILLUSTRATIVE_DATASET_ID in w for w in full_3.warnings)


def test_uv_vis_cross_section_and_emission_reference_ingestion_and_modeling(tmp_path):
    # 1. UV-Vis laboratory cross-section ECSV (wavelength in nm, cross_section in cm^2/molecule)
    uv_ecsv = tmp_path / "no2_uv_vis.ecsv"
    uv_ecsv.write_text(
        "# %ECSV 1.0\n"
        "# ---\n"
        "# datatype:\n"
        "# - {name: wavelength, unit: nm, datatype: float64}\n"
        "# - {name: cross_section, unit: cm^2/molecule, datatype: float64}\n"
        "wavelength cross_section\n"
        "350.0 4.0e-19\n"
        "400.0 6.5e-19\n"
        "450.0 3.2e-19\n"
        "500.0 1.1e-19\n",
        encoding="utf-8",
    )
    uv_spec = import_tabular_spectrum(uv_ecsv)
    assert uv_spec.signal_type == "Laboratory Cross Section"
    assert uv_spec.axis_unit == "nm"
    assert uv_spec.signal_unit == "cm^2/molecule"

    uv_comp = component_from_cross_section_spectrum(
        uv_spec,
        source_sha256=sha256(uv_ecsv.read_bytes()).hexdigest(),
        formula="NO2",
        vmr=1e-5,
        dataset="Vandaele-UVVis",
    )
    preset = get_planet_preset("HD 209458 b")
    uv_model = generate_isothermal_transmission_model(
        target_wavelengths_um=(0.36, 0.40, 0.44, 0.48),
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(uv_comp,),
    )
    # Peak transit depth occurs at 0.40 um where NO2 UV-Vis cross section peaks
    vals = uv_model.comparison_input.values
    assert vals[1] == max(vals)

    # 2. H2 emission lamp reference spectrum must not be conflated with transit depth
    h2_em = tmp_path / "h2_emission.dat"
    h2_em.write_text(
        "# wavelength(nm) emission_intensity\n"
        "wavelength emission_intensity\n"
        "434.0 0.45\n"
        "486.1 0.85\n"
        "656.3 1.00\n",
        encoding="utf-8",
    )
    em_spec = import_tabular_spectrum(h2_em)
    assert em_spec.signal_type == "Reference Emission Spectrum"
    adapted_em = observation_input(em_spec, sha256(h2_em.read_bytes()).hexdigest())
    elig = assess(adapted_em.comparison_input, uv_model.comparison_input)
    assert elig.status != "eligible"


def test_asymmetric_uncertainty_bias_guard_and_systematic_offset_diagnostics(window, tmp_path):
    skewed_tsv = tmp_path / "skewed_errors.tsv"
    skewed_tsv.write_text(
        "wavelength\tpl_trandep\tpl_trandeperr1\tpl_trandeperr2\n"
        "1.0\t2.10\t0.05\t-0.05\n"
        "2.0\t2.15\t0.10\t-0.05\n"  # 50% asymmetry -> triggers >10% guard
        "3.0\t2.12\t0.04\t-0.04\n",
        encoding="utf-8",
    )
    spec = import_tabular_spectrum(skewed_tsv)
    audit = audit_asymmetric_uncertainties(spec)
    assert audit.has_asymmetric_columns is True
    assert audit.exceeding_indices == (1,)
    assert audit.max_asymmetry_ratio == pytest.approx(0.5)
    assert audit.envelope_sigma == pytest.approx((0.05, 0.10, 0.04))
    assert audit.warning is not None and ">10%" in audit.warning

    # Systematic vertical baseline offset vs spectral shape RMS
    obs = ComparisonInput(
        source_id="inst-a",
        source_sha256="a" * 64,
        role="observation",
        observable="transit_depth",
        axis_unit="microns",
        signal_unit="percent",
        coordinate_frame="barycentric",
        response_id="prism",
        response_evidence="test",
        coordinates=(1.0, 2.0, 3.0, 4.0),
        values=(2.120, 2.151, 2.180, 2.139),
    )
    # Model matches spectral shape to ~0.001% (10 ppm) but is shifted by -0.020% (-200 ppm)
    mod = ComparisonInput(
        source_id="model-shifted",
        source_sha256="b" * 64,
        role="forward_model",
        observable="transit_depth",
        axis_unit="microns",
        signal_unit="percent",
        coordinate_frame="barycentric",
        response_id="prism",
        response_evidence="test",
        coordinates=(1.0, 2.0, 3.0, 4.0),
        values=(2.100, 2.130, 2.160, 2.120),
    )
    diag = window.comparison_browser.evaluate_inputs(obs, mod)
    assert diag is not None
    assert diag.offset_dominates_shape is True
    assert abs(diag.mean_residual) == pytest.approx(0.02, abs=1e-3)
    assert diag.demeaned_rms_residual < 0.002
    assert "Systematic-offset notice" in window.comparison_browser.diagnostic_summary.text()
    # Offset is never silently subtracted from raw residuals
    assert np.mean(diag.residuals) == pytest.approx(diag.mean_residual)


def test_wavenumber_wavelength_toggle_in_molecular_and_comparison_browsers(window):
    raw = (ROOT / "data/ExoMol/2026-10-28/CO2-12C-16O2-500K-4000-4010-dnu1.sigma").read_bytes()
    req = ProductRequest(4000, 4010, 500, "1")
    result = RetrievedCrossSection(req, raw, validate_product(raw, req))
    store_reference(window.reference_browser.cache_root / "references", result)

    # 1. MolecularReferenceBrowser default is Wavenumber (cm^-1), toggle converts to increasing microns
    mol_browser = window.reference_browser
    mol_browser._reload_references()
    mol_browser.cached.setCurrentIndex(0)
    mol_browser.open_cached_reference()
    assert mol_browser.reference_plot.axis_mode == "wavenumber"
    assert mol_browser.reference_table.horizontalHeaderItem(0).text() == "Wavenumber (cm^-1)"
    assert mol_browser.reference_table.item(0, 0).text() == "4000.0"

    mol_browser.axis_toggle_button.click()
    assert mol_browser.reference_plot.axis_mode == "microns"
    assert mol_browser.reference_plot.plot_widget.getAxis("bottom").labelText == "Wavelength (microns)"
    assert mol_browser.reference_table.horizontalHeaderItem(0).text() == "Wavelength (microns)"
    first_um = float(mol_browser.reference_table.item(0, 0).text())
    last_um = float(mol_browser.reference_table.item(mol_browser.reference_table.rowCount() - 1, 0).text())
    assert first_um == pytest.approx(10000.0 / 4010.0)
    assert last_um == pytest.approx(10000.0 / 4000.0)
    assert first_um < last_um

    # Toggle back restores exact native cm^-1
    mol_browser.axis_toggle_button.click()
    assert mol_browser.reference_plot.axis_mode == "wavenumber"
    assert mol_browser.reference_table.item(0, 0).text() == "4000.0"

    # 2. ComparisonBrowser reference toggle works identically while preserving raw product bytes
    comp_browser = window.comparison_browser
    comp_browser.refresh_references()
    comp_browser.reference_selector.setCurrentIndex(0)
    assert comp_browser.reference_table.item(0, 0).text() == "4000.0"
    comp_browser.reference_axis_toggle.click()
    assert comp_browser.reference_plot.axis_mode == "microns"
    assert float(comp_browser.reference_table.item(0, 0).text()) == pytest.approx(10000.0 / 4010.0)
    assert comp_browser.current_reference.raw == raw


def test_ppm_and_wavenumber_alignment_controls_in_comparison_browser(window, tmp_path):
    from test_comparison_browser import _write_forward_model_json

    # Observation in wavenumber (cm^-1) and transit depth in ppm
    obs_wn_ppm = tmp_path / "obs_wn_ppm.csv"
    obs_wn_ppm.write_text(
        "wavelength,signal,uncertainty\n"
        "2500.0,21000.0,150.0\n"  # 4.0 um, 2.10%
        "4000.0,21500.0,150.0\n"  # 2.5 um, 2.15%
        "5000.0,21200.0,150.0\n", # 2.0 um, 2.12%
        encoding="utf-8",
    )
    window._import_csv_from_path(str(obs_wn_ppm))
    browser = window.comparison_browser
    browser.add_current_observation()

    model_path = _write_forward_model_json(
        tmp_path / "model_um_pct.json",
        source_id="model-um-percent",
        axis_unit="microns",
        signal_unit="percent",
        coordinates=[2.0, 2.5, 4.0],
        values=[2.12, 2.14, 2.10],
    )
    browser.load_forward_model_from_path(str(model_path))

    browser.obs_role_selector.setCurrentIndex(browser.obs_role_selector.findData("observation"))
    browser.obs_observable_selector.setCurrentIndex(browser.obs_observable_selector.findData("transit_depth"))
    browser.obs_axis_unit_selector.setCurrentIndex(browser.obs_axis_unit_selector.findData("cm^-1"))
    browser.obs_signal_unit_selector.setCurrentIndex(browser.obs_signal_unit_selector.findData("ppm"))
    browser.obs_frame_input.setText("barycentric")
    browser.obs_response_id_input.setText("nirspec-prism-v1")
    browser.obs_response_evidence_input.setText("JWST synthetic top-hat bin response")
    browser.align_checkbox.setChecked(True)

    summary = browser.run_interactive_candidates()
    assert summary is not None
    assert summary.eligible_indices == (0,)
    assert not browser.diagnostic_panel.isHidden()
    assert browser.current_diagnostic.coordinates == pytest.approx((2.0, 2.5, 4.0))
    assert browser.current_diagnostic.left_values == pytest.approx((2.12, 2.15, 2.10))


def test_one_click_plug_and_chug_generate_auto_align_and_compare_on_wasp39b_tbl(window):
    """End-to-end verification of zero-manual-typing forward-model generation & passband integration."""
    window.project_browser.name.setText("wasp39-plug-and-chug")
    window.project_browser.create_button.click()

    tbl_path = ROOT / "data/NASA/2026-10-27/feinstein-2023.tbl"
    window._import_csv_from_path(str(tbl_path))
    assert extract_observation_bin_edges(window.current_spectrum) is not None

    browser = window.comparison_browser
    browser.add_current_observation()
    assert browser.current_observation_metadata.get("pl_name") == "WASP-39 b"

    # Auto mode allows fallback to templates for species without cached line lists in this band
    browser.gen_source_selector.setCurrentIndex(browser.gen_source_selector.findData('auto'))
    summary = browser.generate_and_compare_forward_model()
    assert summary is not None
    # Full model + 4 leave-one-out models (H2O, CO2, CH4, SO2) = 5 eligible candidates
    assert len(summary.eligible_indices) == 5
    assert summary.blocked_indices == ()
    assert not browser.diagnostic_panel.isHidden()
    assert browser.residual_table.rowCount() == 331
    assert "integrate_tophat_bins_v1" in browser.compatibility.text()
    assert "Leave-one-out species attribution" in browser.compatibility.text()
    assert len(browser.last_attribution_entries) == 4

    # Save to active project and verify round-trip reproduction from signed JSON
    saved = browser.save_active_comparison()
    assert saved is not None and saved.is_file()
    check = browser.reproduce_selected_comparison()
    assert check is not None
    assert check.matches_saved_verdict is True
    assert check.matches_saved_diagnostics is True


def test_cached_exomol_cross_section_powers_strict_cached_only_generator(window, tmp_path):
    # Create and validate a broad cached CO2 ExoMol cross-section product (2500-5000 cm^-1 => 2.0-4.0 um)
    lines = [f"{nu:.6f} {1.0e-20 if 3500 <= nu <= 3700 else 1.0e-23:.6e}" for nu in range(2500, 5001, 50)]
    raw = ("\n".join(lines) + "\n").encode("ascii")
    req = ProductRequest(2500, 5000, 1100, "50", "12C-16O2")
    result = RetrievedCrossSection(req, raw, validate_product(raw, req))
    store_reference(window.reference_browser.cache_root / "references", result)

    obs_csv = tmp_path / "ir_obs.csv"
    obs_csv.write_text(
        "wavelength,signal,uncertainty\n"
        "2.2,2.10,0.02\n"
        "2.8,2.18,0.02\n"
        "3.3,2.11,0.02\n"
        "3.8,2.10,0.02\n",
        encoding="utf-8",
    )
    window._import_csv_from_path(str(obs_csv))
    browser = window.comparison_browser
    browser.add_current_observation()

    for formula, cb in browser.gen_species_checks.items():
        cb.setChecked(formula == "CO2")
    browser.gen_source_selector.setCurrentIndex(
        browser.gen_source_selector.findData("cached_only")
    )
    summary = browser.generate_and_compare_forward_model()
    assert summary is not None
    assert len(summary.eligible_indices) == 2  # full + leave-one-out without CO2
    full_prov = browser.candidate_entries[0].provenance["atmospheric_model_provenance"]
    assert full_prov["opacity_sources"][0]["dataset"] == "UCL-4000"
    assert full_prov["opacity_sources"][0]["source_sha256"] == result.product.source_sha256


def test_asymmetric_case_insensitivity_and_display_points_edge_cases(tmp_path):
    # Case-insensitive column matching for asymmetric errors and bandwidth
    tsv = tmp_path / "case_insensitive.tsv"
    tsv.write_text(
        "WAVELENGTH\tDEPTH\tPL_TRANDEPERR1\tPL_TRANDEPERR2\tBANDWIDTH\n"
        "1.5\t2.00\t0.08\t-0.04\t0.2\n"
        "2.5\t2.05\t0.06\t-0.03\t0.2\n"
        "3.5\t2.02\t0.07\t-0.07\t0.2\n",
        encoding="utf-8",
    )
    spec = import_tabular_spectrum(tsv)
    audit = audit_asymmetric_uncertainties(spec)
    assert audit.has_asymmetric_columns is True
    assert audit.column_pair == ("PL_TRANDEPERR1", "PL_TRANDEPERR2")
    assert audit.envelope_sigma == pytest.approx((0.08, 0.06, 0.07))
    assert audit.warning is not None and ">10%" in audit.warning

    edges = extract_observation_bin_edges(spec)
    assert edges is not None
    assert len(edges) == 3
    assert edges[0] == pytest.approx((1.4, 1.6))

    # Alternate astronomical error column pairs
    tsv2 = tmp_path / "alt_err.tsv"
    tsv2.write_text(
        "wavelength\tsignal\terr_plus\terr_minus\n"
        "1.0\t2.0\t0.05\t-0.05\n"
        "2.0\t2.1\t0.05\t-0.05\n"
        "3.0\t2.2\t0.05\t-0.05\n",
        encoding="utf-8",
    )
    spec2 = import_tabular_spectrum(tsv2)
    audit2 = audit_asymmetric_uncertainties(spec2)
    assert audit2.has_asymmetric_columns is True
    assert audit2.column_pair == ("err_plus", "err_minus")
    assert audit2.warning is None

    # reference_display_points defensive guards
    label_wn, pts_wn = reference_display_points(None, 'wavenumber')
    assert label_wn == 'Wavenumber (cm^-1)' and pts_wn == ()
    label_um, pts_um = reference_display_points(None, 'microns')
    assert label_um == 'Wavelength (microns)' and pts_um == ()
    with pytest.raises(ValueError, match="Unsupported reference axis_mode"):
        reference_display_points(None, 'invalid_mode')

    # Identical curves offset diagnostic: ensure offset_dominates_shape is False
    inp1 = ComparisonInput(
        source_id="model-a",
        source_sha256="c" * 64,
        role="forward_model",
        observable="transit_depth",
        axis_unit="microns",
        signal_unit="percent",
        coordinate_frame="barycentric",
        response_id="passband",
        response_evidence="test",
        coordinates=(1.0, 2.0, 3.0),
        values=(2.0, 2.1, 2.2),
    )
    inp2 = ComparisonInput(
        source_id="model-b",
        source_sha256="d" * 64,
        role="forward_model",
        observable="transit_depth",
        axis_unit="microns",
        signal_unit="percent",
        coordinate_frame="barycentric",
        response_id="passband",
        response_evidence="test",
        coordinates=(1.0, 2.0, 3.0),
        values=(2.0, 2.1, 2.2),
    )
    diag_identical = evaluate_residuals(inp1, inp2)
    assert diag_identical.offset_dominates_shape is False
    assert diag_identical.rms_residual == 0.0



def test_priority1_spectral_bin_semantics_fwhm_rejection_and_real_nasa_tables(tmp_path):
    """Verify Priority 1 spectral-bin semantics: FWHM rejection, explicit bounds, unit checks, and real NASA tables."""
    from ecas.ingestion.nasa_table import import_transmission_table

    # 1. FWHM must NEVER be treated as uniform top-hat passband edges
    fwhm_tsv = tmp_path / "fwhm_spectrum.tsv"
    fwhm_tsv.write_text(
        "# axis_unit: microns\n"
        "# signal_unit: %\n"
        "# signal_type: Transmission\n"
        "wavelength\tsignal\tfwhm\n"
        "1.0\t2.10\t0.05\n"
        "2.0\t2.15\t0.05\n"
        "3.0\t2.12\t0.05\n",
        encoding="utf-8",
    )
    fwhm_spec = import_tabular_spectrum(fwhm_tsv)
    assert extract_observation_bin_edges(fwhm_spec) is None
    fwhm_audit = audit_observation_bin_semantics(fwhm_spec, require_axis_unit=True)
    assert fwhm_audit.has_resolved_bins is False
    assert fwhm_audit.bin_edges is None
    assert fwhm_audit.convention == "rejected_response_fwhm"
    assert fwhm_audit.source_columns == ("fwhm",)
    assert fwhm_audit.warning is not None and "Full Width at Half Maximum" in fwhm_audit.warning

    # 2. Explicit lower/upper bin bounds (including asymmetric intervals around center)
    bounds_tsv = tmp_path / "explicit_bounds.tsv"
    bounds_tsv.write_text(
        "# axis_unit: microns\n"
        "wavelength\tsignal\tbin_low\tbin_high\n"
        "1.00\t2.10\t0.92\t1.05\n"
        "2.00\t2.15\t1.88\t2.14\n"
        "3.00\t2.12\t2.90\t3.10\n",
        encoding="utf-8",
    )
    bounds_spec = import_tabular_spectrum(bounds_tsv)
    bounds_audit = audit_observation_bin_semantics(bounds_spec, require_axis_unit=True)
    assert bounds_audit.has_resolved_bins is True
    assert bounds_audit.convention == "explicit_bounds"
    assert bounds_audit.source_columns == ("bin_low", "bin_high")
    assert bounds_audit.bin_edges[0] == pytest.approx((0.92, 1.05))
    assert bounds_audit.bin_edges[1] == pytest.approx((1.88, 2.14))
    assert bounds_audit.bin_edges[2] == pytest.approx((2.90, 3.10))

    # 3. Explicit bin_width vs bin_half_width and conflicting convention guards
    bw_tsv = tmp_path / "explicit_bin_width.tsv"
    bw_tsv.write_text(
        "# axis_unit: microns\n"
        "wavelength\tsignal\tbin_width\n"
        "1.0\t2.10\t0.20\n"
        "2.0\t2.15\t0.20\n"
        "3.0\t2.12\t0.20\n",
        encoding="utf-8",
    )
    bw_spec = import_tabular_spectrum(bw_tsv)
    bw_audit = audit_observation_bin_semantics(bw_spec, require_axis_unit=True)
    assert bw_audit.has_resolved_bins is True
    assert bw_audit.convention == "full_width"
    assert bw_audit.bin_edges[0] == pytest.approx((0.90, 1.10))
    bw_conflict = audit_observation_bin_semantics(
        bw_spec, width_convention="half_width", require_axis_unit=True
    )
    assert bw_conflict.has_resolved_bins is False
    assert bw_conflict.convention == "unresolved_conflicting_convention"

    hw_tsv = tmp_path / "explicit_half_width.tsv"
    hw_tsv.write_text(
        "# axis_unit: microns\n"
        "wavelength\tsignal\tbin_half_width\n"
        "1.0\t2.10\t0.10\n"
        "2.0\t2.15\t0.10\n"
        "3.0\t2.12\t0.10\n",
        encoding="utf-8",
    )
    hw_spec = import_tabular_spectrum(hw_tsv)
    hw_audit = audit_observation_bin_semantics(hw_spec, require_axis_unit=True)
    assert hw_audit.has_resolved_bins is True
    assert hw_audit.convention == "half_width"
    assert hw_audit.bin_edges[0] == pytest.approx((0.90, 1.10))

    # 4. Unit validation: missing axis_unit (when required) and mismatched column_units
    no_unit_tsv = tmp_path / "no_unit.tsv"
    no_unit_tsv.write_text(
        "wavelength\tsignal\tbandwidth\n"
        "1.0\t2.10\t0.10\n"
        "2.0\t2.15\t0.10\n"
        "3.0\t2.12\t0.10\n",
        encoding="utf-8",
    )
    no_unit_spec = import_tabular_spectrum(no_unit_tsv)
    no_unit_audit = audit_observation_bin_semantics(no_unit_spec, require_axis_unit=True)
    assert no_unit_audit.has_resolved_bins is False
    assert no_unit_audit.convention == "unresolved_missing_axis_unit"

    mismatch_audit = audit_observation_bin_semantics(
        bw_spec,
        column_units={"wavelength": "microns", "bin_width": "nm"},
        require_axis_unit=True,
    )
    assert mismatch_audit.has_resolved_bins is False
    assert mismatch_audit.convention == "unresolved_unit_mismatch"
    assert "conflicts with coordinate axis_unit" in mismatch_audit.warning

    unitless_width_audit = audit_observation_bin_semantics(
        bw_spec,
        column_units={"wavelength": "microns", "bin_width": ""},
        require_axis_unit=True,
    )
    assert unitless_width_audit.has_resolved_bins is False
    assert unitless_width_audit.convention == "unresolved_missing_width_unit"

    # 5. Real NASA Exoplanet Archive tables: Feinstein 2022 (NIRISS) vs Alderson 2022 (G395H) vs Rustamkulov 2023 (PRISM)
    feinstein = import_transmission_table(ROOT / "data/NASA/2026-10-27/feinstein-2023.tbl")
    fein_auto = audit_observation_bin_semantics(
        feinstein.spectrum, column_units=feinstein.column_units, require_axis_unit=True
    )
    assert fein_auto.has_resolved_bins is True
    assert fein_auto.convention == "full_width"
    assert fein_auto.adjacent_spacing_to_width_median == pytest.approx(2.0, abs=0.05)
    assert fein_auto.warning is not None and "half-width" in fein_auto.warning
    fein_half = audit_observation_bin_semantics(
        feinstein.spectrum,
        column_units=feinstein.column_units,
        width_convention="half_width",
        require_axis_unit=True,
    )
    assert fein_half.has_resolved_bins is True
    assert fein_half.convention == "half_width"
    assert fein_half.overlapping_pair_count == 7

    alderson = import_transmission_table(
        ROOT / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
    )
    ald_auto = audit_observation_bin_semantics(
        alderson.spectrum, column_units=alderson.column_units, require_axis_unit=True
    )
    assert ald_auto.has_resolved_bins is True
    assert ald_auto.convention == "full_width"
    assert ald_auto.adjacent_spacing_to_width_median == pytest.approx(1.0, abs=0.05)
    assert "half-width" not in (ald_auto.warning or "")
    assert ald_auto.overlapping_pair_count == 2
    # Doubling Alderson's full-width bandwidth under half_width causes massive overlap and must be rejected
    ald_half = audit_observation_bin_semantics(
        alderson.spectrum,
        column_units=alderson.column_units,
        width_convention="half_width",
        require_axis_unit=True,
    )
    assert ald_half.has_resolved_bins is False
    assert ald_half.convention == "unresolved_overlapping_bins"

    rustamkulov = import_transmission_table(
        ROOT / "data/NASA/cache/entry-174704980c13407d83953412906fd60c/source.tbl"
    )
    rust_audit = audit_observation_bin_semantics(
        rustamkulov.spectrum, column_units=rustamkulov.column_units, require_axis_unit=True
    )
    assert rust_audit.has_resolved_bins is False
    assert rust_audit.convention == "unresolved_invalid_values"


def test_priority1_ui_passband_vs_point_grid_and_saved_provenance(window, tmp_path):
    """Verify UI separates coordinate matching from passband integration and persists full bin provenance."""
    import json

    window.project_browser.name.setText("priority1-bin-provenance")
    window.project_browser.create_button.click()

    # 1. Importing a spectrum with FWHM disables passband integration, assigns point-grid response, and warns
    fwhm_tsv = tmp_path / "inst_fwhm.tsv"
    fwhm_tsv.write_text(
        "# axis_unit: microns\n"
        "# signal_unit: %\n"
        "# signal_type: Transmission\n"
        "wavelength\tpl_trandep\tpl_trandeperr1\tpl_trandeperr2\tfwhm\n"
        "1.2\t2.10\t0.02\t-0.02\t0.04\n"
        "2.0\t2.14\t0.02\t-0.02\t0.04\n"
        "2.8\t2.12\t0.02\t-0.02\t0.04\n"
        "3.6\t2.16\t0.02\t-0.02\t0.04\n",
        encoding="utf-8",
    )
    window._import_csv_from_path(str(fwhm_tsv))
    browser = window.comparison_browser
    browser.add_current_observation()
    browser.auto_fill_observation_metadata()
    assert browser.bin_integrate_checkbox.isChecked() is False
    assert browser.obs_response_id_input.text().endswith("-point-grid")
    assert "Full Width at Half Maximum" in browser.candidate_status.text()

    summary_fwhm = browser.generate_and_compare_forward_model()
    assert summary_fwhm is not None
    assert "integrate_tophat_bins_v1" not in browser.compatibility.text()
    assert "Full Width at Half Maximum" in browser.compatibility.text()
    saved_fwhm_path = browser.save_active_comparison()
    saved_fwhm = json.loads(saved_fwhm_path.read_text(encoding="utf-8"))
    assert saved_fwhm["left"]["provenance"]["bin_semantics"]["convention"] == "rejected_response_fwhm"
    assert saved_fwhm["left"]["provenance"]["bin_semantics"]["has_resolved_bins"] is False

    # 2. Importing Feinstein 2023 .tbl records bin_semantics and transformation step provenance
    tbl_path = ROOT / "data/NASA/2026-10-27/feinstein-2023.tbl"
    window._import_csv_from_path(str(tbl_path))
    browser.add_current_observation()
    browser.obs_response_id_input.clear()
    browser.obs_response_evidence_input.clear()
    browser.auto_fill_observation_metadata()
    assert browser.bin_integrate_checkbox.isChecked() is True
    assert browser.obs_response_id_input.text().endswith("-tophat-passband")

    summary_tbl = browser.generate_and_compare_forward_model()
    assert summary_tbl is not None
    saved_tbl_path = browser.save_active_comparison()
    saved_tbl = json.loads(saved_tbl_path.read_text(encoding="utf-8"))
    bin_sem = saved_tbl["left"]["provenance"]["bin_semantics"]
    assert bin_sem["has_resolved_bins"] is True
    assert bin_sem["source_columns"] == ["bandwidth"]
    assert bin_sem["convention"] == "full_width"
    assert bin_sem["width_unit"] == "microns"
    assert bin_sem["adjacent_spacing_to_width_median"] == pytest.approx(2.0, abs=0.05)
    assert "uniform top-hat boxcar" in bin_sem["response_shape_note"]

    right_steps = saved_tbl["right"]["transformations"]
    tophat_step = next(s for s in right_steps if s["operation"] == "integrate_tophat_bins_v1")
    step_params = dict(tophat_step["parameters"])
    assert step_params["response_shape"] == "uniform_tophat_boxcar"
    assert step_params["bin_source_columns"] == ["bandwidth"]
    assert step_params["bin_width_convention"] == "full_width"
