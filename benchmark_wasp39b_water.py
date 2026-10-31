#!/usr/bin/env python3
"""Standalone Reproducible Benchmark Runner: WASP-39 b Cross-Observation Water Prediction.

Executes the predictive benchmark comparing JWST NIRSpec G395H (Visit 02) training
against JWST NIRSpec PRISM (Visit 01) validation, answering:
"When ECAS suggests water, does including water improve its prediction of an
absorption feature in a separate observation?"

Usage:
    python benchmark_wasp39b_water.py
"""
import json
from pathlib import Path
import sys

# Ensure repository root is on sys.path
REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))

from ecas.comparison.predictive_benchmark import run_wasp39b_water_benchmark, BandContrastDefinition

def main():
    print("=" * 80)
    print("ECAS PREDICTIVE BENCHMARK: WATER IN WASP-39 b")
    print("=" * 80)

    f_fit = REPO / "data/NASA/cache/entry-d39db942be204812b8d322bb17f554d8/source.tbl"
    f_val = REPO / "data/NASA/cache/entry-174704980c13407d83953412906fd60c/source.tbl"
    ref_p = REPO / "data/ExoMol/cache/references/3228bc548ff442f882e074e1234f5577.json"

    print(f"1. Fitting observation:   {f_fit.name} (NIRSpec G395H, Visit 02, Alderson et al.)")
    print(f"2. Validation observation:{f_val.name} (NIRSpec PRISM, Visit 01, Rustamkulov et al.)")
    print(f"3. Opacity line list:     {ref_p.name} (ExoMol POKAZATEL 1H2-16O)")
    print()

    # Pre-declared band interval (the 3.1-3.3 um window from Brett & Blake's earlier experiment)
    band_def = BandContrastDefinition(
        name="WASP-39 b 3.10-3.30 µm Water Band (Holdout Window)",
        band_interval_um=(3.10, 3.30),
        blue_reference_interval_um=(2.80, 3.00),
        red_reference_interval_um=(3.40, 3.60),
        weighting_method="inverse_variance",
        decision_threshold_sigmas=2.0,
        scientific_justification=(
            "Evaluates the 3.10-3.30 µm water feature relative to local continuum reference levels "
            "at 2.80-3.00 µm and 3.40-3.60 µm across separate visits."
        ),
    )

    out_manifest = REPO / "wasp39b_predictive_benchmark_manifest.json"
    result = run_wasp39b_water_benchmark(
        fitting_table_path=f_fit,
        validation_table_path=f_val,
        opacity_reference_path=ref_p,
        band_definition=band_def,
        freeze_output_path=out_manifest,
    )

    print("OBSERVATION INDEPENDENCE:")
    print(f"   Separate Visits: {'YES (Confirmed)' if result.are_observations_independent else 'NO'}")
    print(f"   Details: {result.independence_evidence}")
    print()

    print("QUANTITATIVE RESULTS:")
    print(f"   Observed Band Contrast (PRISM):  {result.observed_contrast_ppm:+.1f} ± {result.observed_contrast_uncertainty_ppm:.1f} ppm")
    print(f"   Model with H2O Predicted:       {result.h2o_model.predicted_contrast_ppm:+.1f} ppm (error: {result.h2o_model.contrast_error_ppm:.1f} ppm)")
    print(f"   Baseline (No H2O) Predicted:     {result.baseline_model.predicted_contrast_ppm:+.1f} ppm (error: {result.baseline_model.contrast_error_ppm:.1f} ppm)")
    print(f"   Contrast Improvement by H2O:    {result.contrast_accuracy_improvement_ppm:+.1f} ppm")
    print(f"   2-Sigma Decision Threshold:      ±{2.0 * result.observed_contrast_uncertainty_ppm:.1f} ppm")
    print()

    print(f"DECISION OUTCOME: >>> {result.outcome_decision} <<<")
    print()
    print("PLAIN-LANGUAGE SCIENTIFIC SUMMARY:")
    print(result.plain_language_summary)
    print()

    # Save Markdown report
    out_md = REPO / "wasp39b_predictive_benchmark_report.md"
    out_md.write_text(result.export_markdown_report(), encoding="utf-8")
    print(f"Artifacts exported:")
    print(f"   - JSON Manifest: {out_manifest}")
    print(f"   - Markdown Report: {out_md}")

    # Generate headless plot via PyQtGraph
    try:
        import os
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        import pyqtgraph as pg
        import pyqtgraph.exporters
        import numpy as np

        app = QApplication.instance() or QApplication([])

        pw = pg.PlotWidget()
        pw.resize(1100, 650)
        pw.setBackground("#0f172a")
        pw.showGrid(x=True, y=True, alpha=0.25)
        pw.setLabel("bottom", "Wavelength", units="µm")
        pw.setLabel("left", "Transit Depth", units="%")
        pw.addLegend(offset=(15, 15))

        # Shaded regions
        b_reg = pg.LinearRegionItem(values=[3.10, 3.30], brush=pg.mkBrush(249, 115, 22, 50), pen=pg.mkPen("#f97316", width=1.5, style=Qt.DashLine), movable=False)
        pw.addItem(b_reg)
        bl_reg = pg.LinearRegionItem(values=[2.80, 3.00], brush=pg.mkBrush(56, 189, 248, 30), pen=pg.mkPen("#38bdf8", width=1, style=Qt.DotLine), movable=False)
        pw.addItem(bl_reg)
        rd_reg = pg.LinearRegionItem(values=[3.40, 3.60], brush=pg.mkBrush(56, 189, 248, 30), pen=pg.mkPen("#38bdf8", width=1, style=Qt.DotLine), movable=False)
        pw.addItem(rd_reg)

        pts = result.validation_points
        x_vals = np.array([p["wavelength_um"] for p in pts], dtype=float)
        y_obs = np.array([p["observed_depth_percent"] for p in pts], dtype=float)
        u_obs = np.array([p["measurement_error_percent"] for p in pts], dtype=float)
        y_h2o = np.array([p["h2o_model_depth_percent"] for p in pts], dtype=float)
        y_base = np.array([p["baseline_depth_percent"] for p in pts], dtype=float)

        s_idx = np.argsort(x_vals)
        pw.plot(x_vals[s_idx], y_base[s_idx], pen=pg.mkPen("#06b6d4", width=2, style=Qt.DashLine), name="Continuum Baseline (No H2O)")
        pw.plot(x_vals[s_idx], y_h2o[s_idx], pen=pg.mkPen("#f97316", width=2.5), name="Physical Model (+H2O)")

        if np.any(u_obs > 0):
            err_item = pg.ErrorBarItem(x=x_vals, y=y_obs, top=u_obs, bottom=u_obs, beam=0.005, pen=pg.mkPen("#94a3b8", width=1))
            pw.addItem(err_item)

        pw.plot(x_vals, y_obs, pen=None, symbol="o", symbolSize=6, symbolBrush="#f1f5f9", symbolPen="#64748b", name=f"Validation Obs ({result.validation_observation.instrument})")

        out_png = REPO / "wasp39b_predictive_benchmark_plot.png"
        exporter = pg.exporters.ImageExporter(pw.plotItem)
        exporter.parameters()["width"] = 1100
        exporter.export(str(out_png))
        print(f"   - Benchmark Chart: {out_png}")
    except Exception as e:
        print(f"Notice: PyQtGraph plot export failed ({e}).")

    print("=" * 80)
    print("BENCHMARK EXECUTION COMPLETED SUCCESSFULLY.")
    print("=" * 80)

if __name__ == "__main__":
    main()
