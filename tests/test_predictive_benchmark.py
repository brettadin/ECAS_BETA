"""Tests for reproducible cross-observation predictive benchmark."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
import numpy as np
from PySide6.QtWidgets import QApplication

from ecas.comparison.predictive_benchmark import (
    BandContrastDefinition,
    ModelEvaluationRecord,
    ObservationVisitSpec,
    PredictiveBenchmarkResult,
    calculate_band_contrast,
    run_wasp39b_water_benchmark,
    verify_observation_independence,
)
from ecas.ui.predictive_benchmark_dialog import PredictiveBenchmarkDialog

ROOT = Path(__file__).resolve().parents[1]
FIT_TBL = ROOT / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
VAL_TBL = ROOT / "data/NASA/cache/entry-174704980c13407d83953412906fd60c/source.tbl"
EXOMOL_REF = ROOT / "data/ExoMol/cache/references/3228bc548ff442f882e074e1234f5577.json"


@pytest.fixture(scope="session", autouse=True)
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


class TestObservationIndependence:
    def test_duplicate_file_rejection(self):
        spec_a = ObservationVisitSpec(
            target_id="WASP-39 b",
            source_file="obs_a.tbl",
            source_sha256="abc123" * 10,
            instrument="NIRSpec G395H",
            facility="JWST",
            program_id="1366",
            observing_visit="Visit 02",
            observation_date="2022-07-30",
            authors="Alderson et al. 2022",
            data_points_count=344,
            wavelength_range_um=(2.7, 5.2),
        )
        spec_dup = ObservationVisitSpec(
            target_id="WASP-39 b",
            source_file="obs_dup.tbl",
            source_sha256="abc123" * 10,  # identical hash
            instrument="NIRSpec G395H",
            facility="JWST",
            program_id="1366",
            observing_visit="Visit 02",
            observation_date="2022-07-30",
            authors="Alderson et al. 2022",
            data_points_count=344,
            wavelength_range_um=(2.7, 5.2),
        )

        is_indep, reason = verify_observation_independence(spec_a, spec_dup)
        assert not is_indep
        assert "Duplicate source file" in reason

    def test_shared_visit_rejection(self):
        spec_a = ObservationVisitSpec(
            target_id="WASP-39 b",
            source_file="reduction_a.tbl",
            source_sha256="111111" * 10,
            instrument="NIRSpec G395H",
            facility="JWST",
            program_id="1366",
            observing_visit="Visit 02",
            observation_date="2022-07-30",
            authors="Reduction A",
            data_points_count=344,
            wavelength_range_um=(2.7, 5.2),
        )
        spec_b = ObservationVisitSpec(
            target_id="WASP-39 b",
            source_file="reduction_b.tbl",
            source_sha256="222222" * 10,
            instrument="NIRSpec G395H",
            facility="JWST",
            program_id="1366",
            observing_visit="Visit 02",  # same visit
            observation_date="2022-07-30",
            authors="Reduction B",
            data_points_count=344,
            wavelength_range_um=(2.7, 5.2),
        )

        is_indep, reason = verify_observation_independence(spec_a, spec_b)
        assert not is_indep
        assert "Shared observing visit" in reason

    def test_distinct_visits_confirmed(self):
        spec_g395h = ObservationVisitSpec(
            target_id="WASP-39 b",
            source_file="alderson.tbl",
            source_sha256="aaaaaa" * 10,
            instrument="NIRSpec G395H",
            facility="JWST",
            program_id="1366",
            observing_visit="Visit 02",
            observation_date="2022-07-30",
            authors="Alderson et al. 2022",
            data_points_count=344,
            wavelength_range_um=(2.7, 5.2),
        )
        spec_prism = ObservationVisitSpec(
            target_id="WASP-39 b",
            source_file="rustamkulov.tbl",
            source_sha256="bbbbbb" * 10,
            instrument="NIRSpec PRISM",
            facility="JWST",
            program_id="1366",
            observing_visit="Visit 01",
            observation_date="2022-07-10",
            authors="Rustamkulov et al. 2023",
            data_points_count=207,
            wavelength_range_um=(0.5, 5.3),
        )

        is_indep, reason = verify_observation_independence(spec_g395h, spec_prism)
        assert is_indep
        assert "Verified independent observing visits" in reason


class TestUnitConversionAndBandContrast:
    def test_unit_conversion_percentage_to_ppm(self):
        """Verify that 1 percentage point corresponds exactly to 10,000 ppm."""
        band_def = BandContrastDefinition(
            name="Test Band",
            band_interval_um=(3.1, 3.3),
            blue_reference_interval_um=(2.8, 3.0),
            red_reference_interval_um=(3.4, 3.6),
        )

        lams = [2.9, 3.2, 3.5]
        # In-band is 2.2%, reference is 2.1%. Difference = 0.1% = 1,000 ppm
        depths = [2.10, 2.20, 2.10]
        uncs = [0.01, 0.01, 0.01]

        b_d, r_d, contrast_ppm, unc_ppm = calculate_band_contrast(lams, depths, uncs, band_def)

        assert pytest.approx(b_d, rel=1e-5) == 2.20
        assert pytest.approx(r_d, rel=1e-5) == 2.10
        assert pytest.approx(contrast_ppm, rel=1e-5) == 1000.0  # (2.2 - 2.1) * 10000 = 1000 ppm

    def test_bin_coverage_and_filtering(self):
        band_def = BandContrastDefinition(
            name="Test",
            band_interval_um=(3.1, 3.3),
            blue_reference_interval_um=(2.8, 3.0),
            red_reference_interval_um=(3.4, 3.6),
        )

        # Points only in the band, no reference points
        with pytest.raises(ValueError, match="reference intervals"):
            calculate_band_contrast([3.15, 3.25], [2.1, 2.1], [0.01, 0.01], band_def)

        # Points only in reference, no band points
        with pytest.raises(ValueError, match="band interval"):
            calculate_band_contrast([2.85, 3.45], [2.1, 2.1], [0.01, 0.01], band_def)


class TestStatisticalDecisionRule:
    def test_inconclusive_outcome_when_models_are_compatible(self):
        """When model difference is smaller than 2-sigma observation uncertainty, return inconclusive."""
        if not FIT_TBL.exists() or not VAL_TBL.exists() or not EXOMOL_REF.exists():
            pytest.skip("WASP-39 b cached tables or ExoMol reference not available")

        # The 3.1-3.3 um window has contrast difference < 2*sigma
        res = run_wasp39b_water_benchmark(FIT_TBL, VAL_TBL, EXOMOL_REF)

        assert res.outcome_decision == "This observation cannot distinguish the models."
        assert "cannot distinguish" in res.plain_language_summary.lower()
        assert abs(res.contrast_accuracy_improvement_ppm) <= (2.0 * res.observed_contrast_uncertainty_ppm)

    def test_decisive_outcome_when_contrast_exceeds_threshold(self):
        """When evaluated on the peak water band (2.76-3.0 um), water improves prediction decisively."""
        if not FIT_TBL.exists() or not VAL_TBL.exists() or not EXOMOL_REF.exists():
            pytest.skip("WASP-39 b cached tables or ExoMol reference not available")

        peak_band = BandContrastDefinition(
            name="2.76-3.00 µm Peak Water Band",
            band_interval_um=(2.76, 3.00),
            blue_reference_interval_um=(2.50, 2.70),
            red_reference_interval_um=(3.40, 3.80),
        )

        res = run_wasp39b_water_benchmark(FIT_TBL, VAL_TBL, EXOMOL_REF, band_definition=peak_band)

        assert res.outcome_decision == "Water model significantly improved feature prediction"
        assert res.contrast_accuracy_improvement_ppm > (2.0 * res.observed_contrast_uncertainty_ppm)


class TestBenchmarkExecutionAndUI:
    def test_end_to_end_wasp39b_water_benchmark(self, tmp_path):
        if not FIT_TBL.exists() or not VAL_TBL.exists() or not EXOMOL_REF.exists():
            pytest.skip("WASP-39 b cached tables or ExoMol reference not available")

        out_json = tmp_path / "manifest.json"
        res = run_wasp39b_water_benchmark(FIT_TBL, VAL_TBL, EXOMOL_REF, freeze_output_path=out_json)

        assert res.are_observations_independent
        assert res.target_planet == "WASP-39 b"
        assert res.molecule_tested == "H2O"
        assert len(res.validation_points) > 20
        assert res.h2o_model.training_rms_ppm < res.baseline_model.training_rms_ppm
        assert out_json.exists()

        # Check JSON manifest contents
        manifest = json.loads(out_json.read_text(encoding="utf-8"))
        assert manifest["schema"] == "ecas-predictive-benchmark-v1"
        assert manifest["are_observations_independent"]
        assert "observed_contrast" in manifest
        assert "models" in manifest
        assert "comparison" in manifest

        # Check Markdown export
        md = res.export_markdown_report()
        assert "# ECAS Predictive Benchmark: H2O in WASP-39 b" in md
        assert "Executive Summary" in md
        assert "Band Contrast" in md

    def test_predictive_benchmark_dialog_renders(self):
        if not FIT_TBL.exists() or not VAL_TBL.exists() or not EXOMOL_REF.exists():
            pytest.skip("WASP-39 b cached tables or ExoMol reference not available")

        res = run_wasp39b_water_benchmark(FIT_TBL, VAL_TBL, EXOMOL_REF)
        dlg = PredictiveBenchmarkDialog(res)

        assert dlg.table.rowCount() == 7
        assert dlg.table.columnCount() == 4
        assert len(dlg.summary_edit.toPlainText()) > 50

        # Verify linear region items exist in plot widget
        items = dlg.plot_widget.plotItem.items
        import pyqtgraph as pg
        regions = [it for it in items if isinstance(it, pg.LinearRegionItem)]
        assert len(regions) == 3, "Plot must display shaded band and reference regions"

        dlg.accept()

