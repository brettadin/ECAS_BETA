"""Formal scientific test suite for pure real-data forward models and molecular references.

Enforces Priority 3 requirements from the architecture review:
1. Strict real ExoMol line lists / cross-section datasets from cache.
2. Real observational JWST transmission spectra (Alderson et al. 2022 NIRSpec G395H).
3. Complete provenance tracking distinguishing physical reference data from synthetic templates.
4. Passband integration and round-trip project persistence without synthetic fallback.
5. UI defaults to strict cached-only mode and blocks un-cached species.
"""

from hashlib import sha256
from pathlib import Path
from dataclasses import replace
import gc
import numpy as np
import pytest
from PySide6.QtWidgets import QApplication

from ecas.comparison.alignment import integrate_model_over_bins
from ecas.comparison.candidates import evaluate_candidates
from ecas.comparison.inputs import audit_observation_bin_semantics, observation_input
from ecas.comparison.model_generator import (
    ILLUSTRATIVE_DATASET_ID,
    component_from_cached_exomol,
    generate_isothermal_transmission_model,
    generate_leave_one_out_models,
    get_planet_preset,
)
from ecas.comparison.persistence import (
    build_comparison_record,
    load_comparison_record,
    reproduce_comparison_record,
)
from ecas.ingestion.exomol_reference_cache import load_reference
from ecas.ingestion.nasa_table import import_transmission_table
from ecas.projects import ProjectStore
from ecas.ui.main_window import ECASWindow

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def window(tmp_path, qapp):
    widget = ECASWindow(
        projects_dir=tmp_path / "projects",
        reference_cache_dir=ROOT / "data/ExoMol/cache",
    )
    yield widget
    widget.close()
    gc.collect()


def test_real_exomol_cached_dataset_integrity():
    """Verify the integrity, metadata, wavenumber coverage, and points of cached ExoMol H2O reference."""
    ref_file = ROOT / "data/ExoMol/cache/references/3228bc548ff442f882e074e1234f5577.json"
    assert ref_file.is_file(), f"Expected real ExoMol cache file at {ref_file}"

    ref_res = load_reference(ref_file)
    assert ref_res is not None
    prov = ref_res.product.provenance
    assert prov.molecule == "H2O"
    assert prov.dataset == "POKAZATEL"
    assert prov.isotopologue == "1H2-16O"
    assert ref_res.request.temperature == 500

    pts = ref_res.product.points
    assert len(pts) == 3611
    nu_vals = np.array([float(p[0]) for p in pts])
    sigma_vals = np.array([float(p[1]) for p in pts])

    # Wavenumber range 400 - 4010 cm^-1 corresponds to 2.4937 - 25.0 microns
    assert nu_vals[0] == pytest.approx(400.0)
    assert nu_vals[-1] == pytest.approx(4010.0)
    assert np.all(sigma_vals >= 0.0)
    assert np.max(sigma_vals) > 1e-19  # Distinct physical water absorption band

    # Create molecular component
    comp = component_from_cached_exomol(ref_res, vmr=1e-3)
    assert comp.formula == "H2O"
    assert comp.dataset == "POKAZATEL"
    assert comp.dataset != ILLUSTRATIVE_DATASET_ID
    assert comp.reference_temperature_k == 500.0
    assert comp.source_sha256 == ref_res.product.source_sha256


def test_pure_real_data_forward_model_generation_alderson_jwst():
    """Verify forward model generation on real JWST NIRSpec G395H data using real ExoMol cross sections."""
    tbl_path = ROOT / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
    assert tbl_path.is_file()

    tbl = import_transmission_table(tbl_path)
    assert tbl.spectrum.row_count == 344

    ref_file = ROOT / "data/ExoMol/cache/references/3228bc548ff442f882e074e1234f5577.json"
    ref_res = load_reference(ref_file)
    comp_h2o = component_from_cached_exomol(ref_res, vmr=1.2e-3)

    # Observation coordinates
    tbl_sha = sha256(tbl_path.read_bytes()).hexdigest()
    adapted_obs = observation_input(tbl.spectrum, source_sha256=tbl_sha)
    obs_coords = np.asarray(adapted_obs.comparison_input.coordinates, dtype=float)
    assert obs_coords[0] == pytest.approx(2.763, abs=0.01)
    assert obs_coords[-1] == pytest.approx(5.169, abs=0.01)

    # Confirm 100% of observation coordinates lie within the real POKAZATEL wavelength coverage (2.494 - 25.0 um)
    ref_pts = ref_res.product.points
    nu_arr = np.array([float(p[0]) for p in ref_pts])
    lam_um = 10000.0 / nu_arr
    c_min, c_max = float(np.min(lam_um)), float(np.max(lam_um))
    assert np.all((obs_coords >= c_min) & (obs_coords <= c_max))

    # Dense calculation grid
    dense_grid = np.linspace(obs_coords[0] - 0.01, obs_coords[-1] + 0.01, 1200)
    joint_grid = np.unique(np.concatenate((dense_grid, obs_coords)))

    preset = get_planet_preset("WASP-39 b")
    full_mod = generate_isothermal_transmission_model(
        target_wavelengths_um=joint_grid,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(comp_h2o,),
        cloud_pressure_bar=0.01,
        signal_unit="percent",
    )

    prov_dict = full_mod.to_provenance_dict()
    assert prov_dict["reference_type"] == "physical_reference_data"
    assert prov_dict["contains_synthetic_templates"] is False
    assert prov_dict["physical_opacity_sources"] == ["POKAZATEL"]

    # Verify passband integration
    bin_audit = audit_observation_bin_semantics(tbl.spectrum, column_units=tbl.column_units)
    assert bin_audit.has_resolved_bins is True
    assert bin_audit.bin_edges is not None

    integrated, inc_idx, exc_idx = integrate_model_over_bins(
        full_mod.comparison_input,
        obs_coords,
        bin_audit.bin_edges,
        response_id="jwst-nirspec-g395h-tophat",
        response_evidence="Alderson et al. 2022 bin widths",
    )
    assert len(inc_idx) == 344
    assert len(exc_idx) == 0
    assert len(integrated.transformed.coordinates) == 344
    assert np.all(np.isfinite(integrated.transformed.values))


def test_real_data_project_store_persistence_and_exact_reproducibility(tmp_path):
    """Verify that a comparison record using real NASA data and real ExoMol references persists and reproduces exactly."""
    tbl_path = ROOT / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
    tbl = import_transmission_table(tbl_path)
    tbl_sha = sha256(tbl_path.read_bytes()).hexdigest()
    adapted_obs = observation_input(tbl.spectrum, source_sha256=tbl_sha)
    bin_audit = audit_observation_bin_semantics(tbl.spectrum, column_units=tbl.column_units)

    obs_input = replace(
        adapted_obs.comparison_input,
        role="observation",
        observable="transit_depth",
        axis_unit="microns",
        signal_unit="percent",
        coordinate_frame="barycentric",
        response_id="nirspec-g395h-tophat-passband",
        response_evidence="Alderson et al. 2022 passband bounds",
        noise_kind="independent_gaussian_1sigma",
        noise_evidence="Imported asymmetric error envelope",
        sigma=tuple(max(float(r["pl_trandeperr1"]), float(r["pl_trandeperr2"])) for r in tbl.spectrum.rows),
    )
    obs_coords = np.asarray(obs_input.coordinates, dtype=float)

    ref_file = ROOT / "data/ExoMol/cache/references/3228bc548ff442f882e074e1234f5577.json"
    comp_h2o = component_from_cached_exomol(load_reference(ref_file), vmr=1e-3)
    preset = get_planet_preset("WASP-39 b")

    dense_grid = np.linspace(obs_coords[0] - 0.01, obs_coords[-1] + 0.01, 1000)
    joint_grid = np.unique(np.concatenate((dense_grid, obs_coords)))

    full_mod, loo_mods = generate_leave_one_out_models(
        target_wavelengths_um=joint_grid,
        temperature_k=preset.temperature_k,
        gravity_m_s2=preset.gravity_m_s2,
        planet_radius_m=preset.planet_radius_m,
        stellar_radius_m=preset.stellar_radius_m,
        components=(comp_h2o,),
        cloud_pressure_bar=0.01,
        signal_unit="percent",
    )

    integrated_full, _, _ = integrate_model_over_bins(
        full_mod.comparison_input,
        obs_coords,
        bin_audit.bin_edges,
        response_id="nirspec-g395h-tophat-passband",
        response_evidence="Alderson et al. 2022 passband bounds",
    )
    integrated_loo, _, _ = integrate_model_over_bins(
        loo_mods["H2O"].comparison_input,
        obs_coords,
        bin_audit.bin_edges,
        response_id="nirspec-g395h-tophat-passband",
        response_evidence="Alderson et al. 2022 passband bounds",
    )

    summary = evaluate_candidates(
        obs_input,
        (integrated_full.transformed, integrated_loo.transformed),
        weighted=False,
    )
    assert len(summary.eligible_indices) == 2

    # Save to ProjectStore
    store = ProjectStore(tmp_path / "projects")
    store.create("wasp39b-real-exomol")

    record = build_comparison_record(
        left=obs_input,
        right=integrated_full,
        left_provenance={"kind": "real_nasa_observation", "source": "Alderson et al. 2022 JWST NIRSpec G395H"},
        right_provenance=full_mod.to_provenance_dict(),
    )
    saved_path = store.save_comparison("wasp39b-real-exomol", record)
    assert saved_path.is_file()

    # Load and verify JSON structure
    loaded = load_comparison_record(saved_path)
    right_prov = loaded["right"]["provenance"]
    assert right_prov["reference_type"] == "physical_reference_data"
    assert right_prov["contains_synthetic_templates"] is False
    assert right_prov["atmospheric_model_provenance"]["opacity_sources"][0]["dataset"] == "POKAZATEL"

    # Reproduce
    repro = reproduce_comparison_record(loaded)
    assert repro.matches_saved_verdict is True
    assert repro.matches_saved_diagnostics is True
    assert repro.discrepancies == ()


def test_ui_strict_cached_only_mode_with_real_alderson_spectrum(window):
    """Verify ComparisonBrowser in cached_only mode checks real overlapping molecules and tags candidates."""
    tbl_path = ROOT / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
    window._import_csv_from_path(str(tbl_path))

    browser = window.comparison_browser
    browser.add_current_observation()

    # Verify default is cached_only
    assert browser.gen_source_selector.currentData() == "cached_only"

    # Auto-fill triggers _sync_cached_species_checks
    browser.auto_fill_observation_metadata()

    # H2O is the only cached species overlapping 2.76 - 5.17 um in the local cache
    assert browser.gen_species_checks["H2O"].isChecked() is True
    assert browser.gen_species_checks["CO2"].isChecked() is False
    assert browser.gen_species_checks["CH4"].isChecked() is False
    assert browser.gen_species_checks["SO2"].isChecked() is False

    summary = browser.generate_and_compare_forward_model()
    assert summary is not None

    # Staged candidate should have [Real ExoMol] prefix
    assert len(browser.candidate_entries) >= 1
    assert browser.candidate_entries[0].label.startswith("[Real ExoMol]")
    assert "[Synthetic Template]" not in browser.candidate_entries[0].label

    # Provenance dictionary of the generated candidate has contains_synthetic_templates == False
    cand_prov = browser.candidate_entries[0].provenance
    assert cand_prov.get("reference_type") == "physical_reference_data"
    assert cand_prov.get("contains_synthetic_templates") is False


def test_ui_strict_cached_only_rejection_when_uncached_species_requested(window):
    """Verify cached_only mode refuses to run and reports error when an uncached species is checked."""
    tbl_path = ROOT / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
    window._import_csv_from_path(str(tbl_path))

    browser = window.comparison_browser
    browser.add_current_observation()
    browser.auto_fill_observation_metadata()

    # Explicitly check an un-cached species (e.g. CO2) in cached_only mode
    browser.gen_source_selector.setCurrentIndex(
        browser.gen_source_selector.findData("cached_only")
    )
    browser.gen_species_checks["CO2"].setChecked(True)

    res = browser.generate_and_compare_forward_model()
    # In cached_only mode, CO2 has no cached reference, so it should be rejected with an actionable error
    assert res is None
    compat_text = browser.compatibility.text()
    assert "Strict cached ExoMol mode blocked" in compat_text
    assert "CO2" in compat_text
