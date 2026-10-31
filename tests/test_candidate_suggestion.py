"""Tests for candidate molecule suggestion and hypothesis screening workflow."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ecas.comparison.candidate_screener import (
    CandidatePool,
    CandidatePoolEntry,
    CandidateScreeningResult,
    ScreeningReport,
    build_candidate_pool,
    screen_candidates,
)
from ecas.comparison.inputs import observation_input
from ecas.identification.library import discover_library, load_library_spectrum
from ecas.ingestion.nasa_table import import_transmission_table
from ecas.ui.candidate_suggestion_dialog import CandidateSuggestionDialog
from ecas.ui.main_window import ECASWindow
from ecas.ui.identification_panel import IdentificationPanel

ROOT = Path(__file__).resolve().parents[1]
EXOMOL_CACHE = ROOT / "data/ExoMol/cache"
SPECTRAL_LIB = ROOT / "data/ECAS_Spectral_Library"
FEINSTEIN_TBL = ROOT / "data/NASA/2026-10-27/feinstein-2023.tbl"


@pytest.fixture(scope="session", autouse=True)
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


@pytest.fixture
def wasp39_comp():
    if not FEINSTEIN_TBL.exists():
        pytest.skip("feinstein-2023.tbl not available")
    spec = import_transmission_table(FEINSTEIN_TBL).spectrum
    adapted = observation_input(spec, "a" * 64)
    return adapted.comparison_input


class TestCandidatePool:
    def test_pool_construction_and_inventory(self, wasp39_comp):
        pool = build_candidate_pool(wasp39_comp, EXOMOL_CACHE, SPECTRAL_LIB)
        summary = pool.summary()

        assert summary["total_considered"] > 100
        assert summary["unavailable_data"] >= 90
        assert summary["incompatible"] >= 10

        # Check unavailable data items have explicit non-absence disclosure
        unavail = pool.unavailable[0]
        assert "NOT evidence of absence" in unavail.status_reason
        assert unavail.status == "unavailable_data"
        assert unavail.wavelength_range_um is None

        # Check laboratory references are marked incompatible for planetary transmission
        lab_incompat = [e for e in pool.incompatible if "Lab" in e.molecule_id]
        assert len(lab_incompat) > 0
        assert "cannot be directly compared to planetary transit depth" in lab_incompat[0].status_reason

        # Check export inventory structure
        inv = pool.export_inventory()
        assert len(inv) == len(pool.all_entries)
        assert "molecule_id" in inv[0]
        assert "status" in inv[0]
        assert "status_reason" in inv[0]


class TestScreeningEngine:
    def test_planetary_transmission_screening(self, wasp39_comp):
        pool = build_candidate_pool(wasp39_comp, EXOMOL_CACHE, SPECTRAL_LIB)
        report = screen_candidates(wasp39_comp, pool, planet_preset_id="wasp-39b")

        assert report.target_id == wasp39_comp.source_id
        assert report.mode == "planetary_transmission"
        assert len(report.results) >= 1

        for r in report.results:
            assert r.evaluated_points_count >= 3
            assert r.evaluated_wavelength_range_um[0] < r.evaluated_wavelength_range_um[1]
            assert isinstance(r.delta_chi2, float)
            assert isinstance(r.delta_rms, float)
            assert isinstance(r.rms_improvement_percent, float)
            assert len(r.candidate_model_curve) == r.evaluated_points_count
            assert len(r.baseline_model_curve) == r.evaluated_points_count
            assert r.outcome in ("Strong Candidate", "Moderate Support", "Marginal / Weak", "No Improvement", "Inconclusive")
            assert len(r.outcome_reason) > 0
            assert len(r.multi_band_consistency) > 0

    def test_laboratory_identification_screening(self):
        if not SPECTRAL_LIB.exists():
            pytest.skip("ECAS_Spectral_Library not available")
        lib = discover_library(SPECTRAL_LIB)
        first_ds = lib.datasets[0]  # C2H2
        spec = load_library_spectrum(first_ds.source_path)
        comp = observation_input(spec, "b" * 64).comparison_input

        pool = build_candidate_pool(comp, EXOMOL_CACHE, SPECTRAL_LIB)
        assert len(pool.searchable) > 10

        report = screen_candidates(comp, pool)
        assert report.mode == "laboratory_identification"
        assert len(report.results) > 10

        top = report.top_candidates(limit=5)
        assert len(top) >= 1
        # Ground truth C2H2 must be detected as Strong Candidate
        c2h2_results = [r for r in top if "C2H2" in r.formula]
        assert len(c2h2_results) >= 1
        assert c2h2_results[0].outcome == "Strong Candidate"
        assert c2h2_results[0].delta_chi2 > 1000.0


class TestCandidateSuggestionUI:
    def test_dialog_tabs_and_filtering(self, wasp39_comp):
        pool = build_candidate_pool(wasp39_comp, EXOMOL_CACHE, SPECTRAL_LIB)
        report = screen_candidates(wasp39_comp, pool, planet_preset_id="wasp-39b")

        dlg = CandidateSuggestionDialog(report)
        assert dlg.tabs.count() == 3
        assert dlg.results_table.rowCount() == len(report.results)
        assert dlg.pool_table.rowCount() == len(pool.all_entries)

        # Test pool table filtering
        dlg.pool_category_combo.setCurrentIndex(1)  # Searchable
        dlg._filter_pool_table()

        # Test search text filtering
        dlg.pool_search_edit.setText("H2O")
        dlg._filter_pool_table()

        # Test results filtering
        dlg.results_filter_combo.setCurrentIndex(0)  # All
        dlg._filter_results_table()

        # Test selection of candidate row updates plot and details
        if dlg.results_table.rowCount() > 0:
            dlg._select_result_row(0)
            assert len(dlg.detail_text.toPlainText()) > 10

        dlg.accept()

    def test_apply_candidates_to_atmospheric_model(self, tmp_path, wasp39_comp):
        win = ECASWindow(projects_dir=tmp_path / "projects", reference_cache_dir=EXOMOL_CACHE)
        win._import_csv_from_path(str(FEINSTEIN_TBL))
        win.comparison_browser.add_current_observation()

        dlg = win.comparison_browser.open_candidate_suggestions(exec_dialog=False)
        assert dlg is not None

        # Test applying candidates: selecting CO2 must NOT check CO
        win.comparison_browser.apply_suggested_candidates(["CO2"])
        assert win.comparison_browser.workflow_tabs.currentIndex() == 2  # Step 3
        assert win.comparison_browser.gen_species_checks["CO2"].isChecked()
        if "CO" in win.comparison_browser.gen_species_checks:
            assert not win.comparison_browser.gen_species_checks["CO"].isChecked(), "CO must not be selected when only CO2 is chosen!"

        win.close()

    def test_dialog_plot_displays_true_observation_values(self, wasp39_comp):
        pool = build_candidate_pool(wasp39_comp, EXOMOL_CACHE, SPECTRAL_LIB)
        report = screen_candidates(wasp39_comp, pool, planet_preset_id="wasp-39b")
        dlg = CandidateSuggestionDialog(report)

        if len(report.results) > 0:
            dlg._select_result_row(0)
            res = report.results[0]
            assert len(res.observed_curve) > 0

            # Find observation plot item in plot widget
            plot_items = dlg.plot_widget.plotItem.items
            obs_plots = [item for item in plot_items if hasattr(item, "name") and item.name() and "Observation" in item.name()]
            assert len(obs_plots) == 1
            plotted_x, plotted_y = obs_plots[0].getData()

            # Plotted values must match input observation values, not candidate model curve
            expected_x = np.array([pt[0] for pt in res.observed_curve])
            expected_y = np.array([pt[1] for pt in res.observed_curve])
            np.testing.assert_allclose(plotted_x, expected_x)
            np.testing.assert_allclose(plotted_y, expected_y)

            # Plotted observation must differ from model curve
            model_y = np.array([pt[1] for pt in res.candidate_model_curve])
            assert not np.allclose(plotted_y, model_y), "Plotted observation points must not be identical to model values!"

        dlg.accept()

    def test_k2_18b_preset_resolution(self, tmp_path, wasp39_comp):
        win = ECASWindow(projects_dir=tmp_path / "projects", reference_cache_dir=EXOMOL_CACHE)
        win._import_csv_from_path(str(FEINSTEIN_TBL))
        win.comparison_browser.add_current_observation()

        # Set preset selector to K2-18 b
        k2_idx = win.comparison_browser.gen_preset_selector.findData("k2-18b")
        if k2_idx >= 0:
            win.comparison_browser.gen_preset_selector.setCurrentIndex(k2_idx)
            dlg = win.comparison_browser.open_candidate_suggestions(exec_dialog=False)
            assert dlg is not None
            assert dlg.report.planet_preset_id == "k2-18b"
            assert dlg.report.baseline_parameters["temperature_k"] < 400.0  # K2-18 b is temperate

        win.close()

    def test_uv_vis_laboratory_spectrum_screening(self):
        """UV-Vis laboratory spectra in nm must screen against laboratory references without 0 results."""
        from ecas.comparison.eligibility import ComparisonInput
        # Create a laboratory UV-Vis spectrum in nm
        uv_coords = tuple(float(x) for x in np.linspace(200.0, 800.0, 50))
        uv_vals = tuple(float(y) for y in (0.1 + 0.8 * np.exp(-((np.linspace(200.0, 800.0, 50) - 350.0) / 40.0) ** 2)))
        comp = ComparisonInput(
            source_id="uvvis_sample.csv",
            source_sha256="c" * 64,
            role="observation",
            observable="absorbance",
            axis_unit="nm",
            signal_unit="fraction",
            coordinate_frame=None,
            response_id=None,
            response_evidence=None,
            coordinates=uv_coords,
            values=uv_vals,
        )

        pool = build_candidate_pool(comp, EXOMOL_CACHE, SPECTRAL_LIB)
        # Must not be flagged as transmission, so lab references must be searchable
        assert len(pool.searchable) > 0, "Laboratory references must be searchable for UV-Vis laboratory data"
        report = screen_candidates(comp, pool)
        assert report.mode == "laboratory_identification"
        assert len(report.results) > 0

    def test_uncalibrated_uncertainty_notice(self, wasp39_comp):
        from dataclasses import replace
        # Observation without sigma
        comp_no_sig = replace(wasp39_comp, sigma=None)
        pool = build_candidate_pool(comp_no_sig, EXOMOL_CACHE, SPECTRAL_LIB)
        report = screen_candidates(comp_no_sig, pool, planet_preset_id="wasp-39b")

        assert not report.has_calibrated_uncertainties
        assert report.uncertainty_notice is not None
        assert "calibrated" in report.uncertainty_notice.lower()

        manifest = report.export_manifest()
        assert not manifest["has_calibrated_uncertainties"]
        assert manifest["uncertainty_notice"] == report.uncertainty_notice

    def test_laboratory_transit_guard(self):
        id_panel = IdentificationPanel(SPECTRAL_LIB)
        id_panel.add_files([str(FEINSTEIN_TBL)])

        # Guard must prevent transit spectrum from being screened as lab data
        dlg = id_panel.open_candidate_suggestions(exec_dialog=False)
        assert dlg is None
        assert not id_panel.transit_guidance_card.isHidden()

        id_panel.shutdown()


class TestReproducibilityAndManifest:
    def test_manifest_export_and_report(self, wasp39_comp):
        pool = build_candidate_pool(wasp39_comp, EXOMOL_CACHE, SPECTRAL_LIB)
        report = screen_candidates(wasp39_comp, pool, planet_preset_id="wasp-39b")

        # JSON manifest
        manifest = report.export_manifest()
        assert manifest["schema"] == "ecas-candidate-screening-v1"
        assert manifest["target_id"] == wasp39_comp.source_id
        assert manifest["mode"] == "planetary_transmission"
        assert "pool_summary" in manifest
        assert "screening_results" in manifest
        assert "scientific_disclosures" in manifest

        # Check JSON serialization round-trip
        serialized = json.dumps(manifest)
        deserialized = json.loads(serialized)
        assert deserialized["schema"] == manifest["schema"]

        # Markdown report
        md = report.export_markdown_report()
        assert "# ECAS Candidate Molecule Screening Report" in md
        assert "Candidate Pool Summary" in md
        assert "Scientific Method & Limitations" in md

