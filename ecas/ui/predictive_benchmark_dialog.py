"""Interactive UI Dialog for Cross-Observation Predictive Benchmark.

Visualizes model predictions against independent validation observations,
marking the target absorption band and reference continuum intervals,
and displaying the statistical decision and plain-language interpretation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ecas.comparison.predictive_benchmark import (
    BandContrastDefinition,
    PredictiveBenchmarkResult,
    run_wasp39b_water_benchmark,
)


class PredictiveBenchmarkDialog(QDialog):
    """Dialog displaying cross-observation predictive benchmark results."""

    def __init__(self, result: PredictiveBenchmarkResult, parent: QWidget | None = None):
        super().__init__(parent)
        self.result = result
        self.setWindowTitle(f"Predictive Benchmark — {result.molecule_tested} in {result.target_planet}")
        self.resize(1050, 750)
        self.setStyleSheet("background-color: #0b0f19; color: #f1f5f9; font-family: 'Segoe UI', sans-serif;")

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # 1. Header Card with Outcome Badge
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #1e293b; border-radius: 8px; padding: 10px;")
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(10, 8, 10, 8)
        h_layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_label = QLabel(f"🔬 Cross-Observation Predictive Benchmark: {self.result.molecule_tested} in {self.result.target_planet}")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #38bdf8;")
        title_row.addWidget(title_label)
        title_row.addStretch()

        # Decision Badge
        badge = QLabel(f"  {self.result.outcome_decision}  ")
        badge.setFont(QFont("Segoe UI", 10, QFont.Bold))
        if "cannot distinguish" in self.result.outcome_decision.lower():
            badge.setStyleSheet("background-color: #b45309; color: #fef08a; border-radius: 4px; padding: 4px 8px;")
        elif "improved" in self.result.outcome_decision.lower():
            badge.setStyleSheet("background-color: #15803d; color: #bbf7d0; border-radius: 4px; padding: 4px 8px;")
        else:
            badge.setStyleSheet("background-color: #334155; color: #f1f5f9; border-radius: 4px; padding: 4px 8px;")
        title_row.addWidget(badge)
        h_layout.addLayout(title_row)

        # Independence & Visit Info Pill
        indep_row = QHBoxLayout()
        indep_pill = QLabel(
            f"✓ Separate Visits Confirmed: Fitting = {self.result.fitting_observation.instrument} ({self.result.fitting_observation.observing_visit}, {self.result.fitting_observation.observation_date}) | "
            f"Validation = {self.result.validation_observation.instrument} ({self.result.validation_observation.observing_visit}, {self.result.validation_observation.observation_date})"
        )
        indep_pill.setStyleSheet("color: #4ade80; font-size: 11px;")
        indep_row.addWidget(indep_pill)
        indep_row.addStretch()
        h_layout.addLayout(indep_row)

        layout.addWidget(header_card)

        # 2. Main Content Splitter (Left: Table & Summary, Right: Interactive Plot)
        splitter = QSplitter(Qt.Horizontal)

        # Left Column: Table & Plain Language Summary
        left_widget = QWidget()
        l_layout = QVBoxLayout(left_widget)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(10)

        # Comparison Table
        table_label = QLabel("Comparison Metrics (Band Contrast & Predictive Errors)")
        table_label.setStyleSheet("font-weight: bold; color: #94a3b8; font-size: 12px;")
        l_layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Metric",
            "Observed (PRISM)",
            "Model +H2O",
            "Baseline (No H2O)",
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #0f172a; alternate-background-color: #1e293b; color: #f1f5f9; gridline-color: #334155; }"
        )
        self.table.setAlternatingRowColors(True)
        self._populate_table()
        l_layout.addWidget(self.table, stretch=3)

        # Plain-Language Interpretation Text Box
        summary_label = QLabel("Plain-Language Interpretation & Decision")
        summary_label.setStyleSheet("font-weight: bold; color: #94a3b8; font-size: 12px;")
        l_layout.addWidget(summary_label)

        self.summary_edit = QTextEdit()
        self.summary_edit.setReadOnly(True)
        self.summary_edit.setStyleSheet(
            "QTextEdit { background-color: #1e293b; color: #e2e8f0; border: 1px solid #334155; border-radius: 6px; padding: 8px; font-size: 12px; line-height: 1.4; }"
        )
        self.summary_edit.setPlainText(self.result.plain_language_summary)
        l_layout.addWidget(self.summary_edit, stretch=2)

        splitter.addWidget(left_widget)

        # Right Column: Interactive Plot
        right_widget = QWidget()
        r_layout = QVBoxLayout(right_widget)
        r_layout.setContentsMargins(0, 0, 0, 0)
        r_layout.setSpacing(6)

        plot_title = QLabel(f"Validation Spectrum & Predictions ({self.result.validation_observation.instrument})")
        plot_title.setStyleSheet("font-weight: bold; color: #38bdf8; font-size: 12px;")
        r_layout.addWidget(plot_title)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#0f172a")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.25)
        self.plot_widget.setLabel("bottom", "Wavelength", units="µm")
        self.plot_widget.setLabel("left", "Transit Depth", units="%")
        self.plot_widget.addLegend(offset=(10, 10))

        self._render_plot()
        r_layout.addWidget(self.plot_widget)

        splitter.addWidget(right_widget)
        splitter.setSizes([450, 600])
        layout.addWidget(splitter, stretch=1)

        # 3. Bottom Action Bar
        bottom_bar = QHBoxLayout()
        export_manifest_btn = QPushButton("📄 Export Manifest (JSON)...")
        export_manifest_btn.setStyleSheet("background-color: #1e293b; color: #38bdf8; font-weight: bold; padding: 6px 12px; border: 1px solid #38bdf8; border-radius: 4px;")
        export_manifest_btn.clicked.connect(self._export_manifest)
        bottom_bar.addWidget(export_manifest_btn)

        export_md_btn = QPushButton("📝 Export Markdown Report...")
        export_md_btn.setStyleSheet("background-color: #1e293b; color: #e2e8f0; padding: 6px 12px; border: 1px solid #64748b; border-radius: 4px;")
        export_md_btn.clicked.connect(self._export_markdown)
        bottom_bar.addWidget(export_md_btn)

        bottom_bar.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background-color: #334155; color: white; padding: 6px 16px; border-radius: 4px;")
        close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(close_btn)

        layout.addLayout(bottom_bar)

    def _populate_table(self) -> None:
        rows_data = [
            (
                "Band Contrast (ppm)",
                f"{self.result.observed_contrast_ppm:+.1f} ± {self.result.observed_contrast_uncertainty_ppm:.1f}",
                f"{self.result.h2o_model.predicted_contrast_ppm:+.1f}",
                f"{self.result.baseline_model.predicted_contrast_ppm:+.1f}",
            ),
            (
                "Contrast Prediction Error (ppm)",
                "—",
                f"{self.result.h2o_model.contrast_error_ppm:.1f}",
                f"{self.result.baseline_model.contrast_error_ppm:.1f}",
            ),
            (
                "In-Band Depth (3.1-3.3 µm)",
                f"{self.result.observed_band_depth_percent:.5f}%",
                f"{self.result.h2o_model.predicted_band_depth_percent:.5f}%",
                f"{self.result.baseline_model.predicted_band_depth_percent:.5f}%",
            ),
            (
                "Continuum Ref Depth",
                f"{self.result.observed_continuum_depth_percent:.5f}%",
                f"{self.result.h2o_model.predicted_continuum_depth_percent:.5f}%",
                f"{self.result.baseline_model.predicted_continuum_depth_percent:.5f}%",
            ),
            (
                "Validation Visit Mean Offset",
                "—",
                f"{self.result.h2o_model.validation_mean_offset_ppm:+.1f} ppm",
                f"{self.result.baseline_model.validation_mean_offset_ppm:+.1f} ppm",
            ),
            (
                "Mean-Subtracted Shape RMS",
                "—",
                f"{self.result.h2o_model.validation_shape_rms_ppm:.1f} ppm",
                f"{self.result.baseline_model.validation_shape_rms_ppm:.1f} ppm",
            ),
            (
                "Training Fit RMS (G395H)",
                "—",
                f"{self.result.h2o_model.training_rms_ppm:.1f} ppm",
                f"{self.result.baseline_model.training_rms_ppm:.1f} ppm",
            ),
        ]

        self.table.setRowCount(len(rows_data))
        for r_idx, (m, o, h, b) in enumerate(rows_data):
            self.table.setItem(r_idx, 0, QTableWidgetItem(m))
            self.table.setItem(r_idx, 1, QTableWidgetItem(o))
            self.table.setItem(r_idx, 2, QTableWidgetItem(h))
            self.table.setItem(r_idx, 3, QTableWidgetItem(b))

            if r_idx == 0:
                for c in range(4):
                    item = self.table.item(r_idx, c)
                    item.setFont(QFont("Segoe UI", 9, QFont.Bold))
                    item.setForeground(QColor("#38bdf8"))

    def _render_plot(self) -> None:
        self.plot_widget.clear()

        # 1. Shaded Region for Band Interval
        b_lo, b_hi = self.result.band_definition.band_interval_um
        band_region = pg.LinearRegionItem(
            values=[b_lo, b_hi],
            brush=pg.mkBrush(249, 115, 22, 45),  # semi-transparent orange
            pen=pg.mkPen(color="#f97316", width=1.5, style=Qt.DashLine),
            movable=False,
        )
        self.plot_widget.addItem(band_region)

        # 2. Shaded Regions for Reference Intervals (Blue & Red)
        bl_lo, bl_hi = self.result.band_definition.blue_reference_interval_um
        blue_region = pg.LinearRegionItem(
            values=[bl_lo, bl_hi],
            brush=pg.mkBrush(56, 189, 248, 30),  # semi-transparent light blue
            pen=pg.mkPen(color="#38bdf8", width=1, style=Qt.DotLine),
            movable=False,
        )
        self.plot_widget.addItem(blue_region)

        rd_lo, rd_hi = self.result.band_definition.red_reference_interval_um
        red_region = pg.LinearRegionItem(
            values=[rd_lo, rd_hi],
            brush=pg.mkBrush(56, 189, 248, 30),
            pen=pg.mkPen(color="#38bdf8", width=1, style=Qt.DotLine),
            movable=False,
        )
        self.plot_widget.addItem(red_region)

        # Extract validation data points
        pts = self.result.validation_points
        if not pts:
            return

        x_vals = np.array([p["wavelength_um"] for p in pts], dtype=float)
        y_obs = np.array([p["observed_depth_percent"] for p in pts], dtype=float)
        u_obs = np.array([p["measurement_error_percent"] for p in pts], dtype=float)
        y_h2o = np.array([p["h2o_model_depth_percent"] for p in pts], dtype=float)
        y_base = np.array([p["baseline_depth_percent"] for p in pts], dtype=float)

        # 3. Model Curves
        # Sort by wavelength for smooth curve rendering
        sort_idx = np.argsort(x_vals)
        self.plot_widget.plot(
            x_vals[sort_idx],
            y_base[sort_idx],
            pen=pg.mkPen(color="#06b6d4", width=2, style=Qt.DashLine),
            name="Continuum Baseline (No H2O)",
        )
        self.plot_widget.plot(
            x_vals[sort_idx],
            y_h2o[sort_idx],
            pen=pg.mkPen(color="#f97316", width=2.5),
            name="Physical Model (+H2O)",
        )

        # 4. Observation Points & Error Bars
        if np.any(u_obs > 0):
            err_item = pg.ErrorBarItem(
                x=x_vals,
                y=y_obs,
                top=u_obs,
                bottom=u_obs,
                beam=0.005,
                pen=pg.mkPen(color="#94a3b8", width=1),
            )
            self.plot_widget.addItem(err_item)

        self.plot_widget.plot(
            x_vals,
            y_obs,
            pen=None,
            symbol="o",
            symbolSize=6,
            symbolBrush="#f1f5f9",
            symbolPen="#64748b",
            name=f"Validation Obs ({self.result.validation_observation.instrument})",
        )

    def _export_manifest(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Predictive Benchmark Manifest",
            "wasp39b_predictive_benchmark_manifest.json",
            "JSON Files (*.json)",
        )
        if path:
            Path(path).write_text(json.dumps(self.result.export_manifest(), indent=2), encoding="utf-8")
            QMessageBox.information(self, "Exported", f"Saved benchmark manifest to:\n{path}")

    def _export_markdown(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Predictive Benchmark Report",
            "wasp39b_predictive_benchmark_report.md",
            "Markdown Files (*.md)",
        )
        if path:
            Path(path).write_text(self.result.export_markdown_report(), encoding="utf-8")
            QMessageBox.information(self, "Exported", f"Saved benchmark Markdown report to:\n{path}")

