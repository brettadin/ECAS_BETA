"""Interactive comparison dialog for scientific assumptions and analysis variants.

Renders differential diagnostics across configurations differing in:
- Atmospheric structure (clear vs cloudy)
- Opacity sources (ExoMol vs synthetic)
- Molecular components (full chemistry vs drop-one)
- Wavelength trims
- Noise treatments

Enforces scientific fairness guards:
- Blocks direct chi-squared comparisons across non-identical data domains.
- Clearly states Bayesian evidence requirements.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ecas.comparison.assumptions import (
    BAYESIAN_EVIDENCE_NOTICE,
    DOMAIN_MISMATCH_WARNING,
    AssumptionDelta,
    ScientificAssumptionVariant,
    compare_scientific_assumptions,
)


class AssumptionsComparisonDialog(QDialog):
    """Dialog for comparing analysis configurations differing in scientific assumptions."""

    def __init__(
        self,
        variants: Sequence[ScientificAssumptionVariant],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Compare Scientific Assumptions — ECAS")
        self.resize(1000, 700)

        self.variants = list(variants)
        self._current_a_idx = 0
        self._current_b_idx = min(1, len(variants) - 1)

        self._setup_ui()
        self._populate_selectors()
        self._populate_inventory_table()
        self._update_comparison()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Header Banner
        banner = QFrame()
        banner.setStyleSheet("background-color: #242933; border: 1px solid #434c5e; border-radius: 4px; padding: 6px;")
        b_layout = QVBoxLayout(banner)
        b_layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel("<b>Comparative Evaluation of Scientific Modeling Assumptions</b>")
        title.setStyleSheet("color: #88c0d0; font-size: 12px;")
        desc = QLabel(
            "Compare forward models and fits evaluated under alternative hypotheses "
            "(cloudiness, opacities, chemical species, wavelength trims). "
            "Fits evaluated on different data domains cannot be directly compared by residual scores."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #d8dee9; font-size: 10.5px;")
        b_layout.addWidget(title)
        b_layout.addWidget(desc)
        main_layout.addWidget(banner)

        # 2. Selector row
        sel_card = QFrame()
        sel_card.setStyleSheet("background-color: #1e222a; border-radius: 4px; padding: 6px;")
        sel_layout = QHBoxLayout(sel_card)
        sel_layout.setContentsMargins(6, 4, 6, 4)

        sel_layout.addWidget(QLabel("<b>Baseline (A):</b>"))
        self.sel_a = QComboBox()
        self.sel_a.currentIndexChanged.connect(self._on_sel_a_changed)
        sel_layout.addWidget(self.sel_a, 1)

        sel_layout.addWidget(QLabel("<b>Alternative (B):</b>"))
        self.sel_b = QComboBox()
        self.sel_b.currentIndexChanged.connect(self._on_sel_b_changed)
        sel_layout.addWidget(self.sel_b, 1)

        self.domain_badge = QLabel("")
        self.domain_badge.setStyleSheet("font-weight: bold; padding: 4px 10px; border-radius: 3px; font-size: 11px;")
        sel_layout.addWidget(self.domain_badge)
        main_layout.addWidget(sel_card)

        # Domain warning banner
        self.domain_warning_label = QLabel("")
        self.domain_warning_label.setWordWrap(True)
        self.domain_warning_label.setStyleSheet("color: #ebcb8b; font-weight: 500; font-size: 11px; padding: 0 4px;")
        self.domain_warning_label.setVisible(False)
        main_layout.addWidget(self.domain_warning_label)

        # 3. Main Splitter: Differential Plots (left) + Differential Diagnostics (right)
        splitter = QSplitter(Qt.Horizontal)

        # Left: Plots
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(4)

        self.top_plot = pg.PlotWidget()
        self.top_plot.setTitle("Model Predictions: Baseline (A) vs Alternative (B)")
        self.top_plot.setLabel("bottom", "Wavelength", units="µm")
        self.top_plot.setLabel("left", "Transit Depth", units="%")
        self.top_plot.addLegend(offset=(10, 10))
        self.top_plot.showGrid(x=True, y=True, alpha=0.3)
        plot_layout.addWidget(self.top_plot, 2)

        self.bot_plot = pg.PlotWidget()
        self.bot_plot.setTitle("Prediction Differential (Model B - Model A)")
        self.bot_plot.setLabel("bottom", "Wavelength", units="µm")
        self.bot_plot.setLabel("left", "Δ Model (B - A)", units="%")
        self.bot_plot.addLegend(offset=(10, 10))
        self.bot_plot.showGrid(x=True, y=True, alpha=0.3)
        plot_layout.addWidget(self.bot_plot, 1)

        splitter.addWidget(plot_container)

        # Right: Tabs (Comparison Details vs Configuration Inventory)
        side_tabs = QTabWidget()

        # Tab 1: Comparison Details
        tab_details = QWidget()
        tab_det_layout = QVBoxLayout(tab_details)
        tab_det_layout.setContentsMargins(6, 6, 6, 6)

        tab_det_layout.addWidget(QLabel("<b>Scientific Assumption Changes:</b>"))
        self.diffs_label = QLabel("")
        self.diffs_label.setWordWrap(True)
        self.diffs_label.setStyleSheet("font-size: 11px; line-height: 1.4;")
        tab_det_layout.addWidget(self.diffs_label)

        tab_det_layout.addWidget(QLabel("<b>Differential Statistics:</b>"))
        self.stats_label = QLabel("")
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("font-size: 11px; line-height: 1.4;")
        tab_det_layout.addWidget(self.stats_label)

        tab_det_layout.addWidget(QLabel("<b>Evidence Notice:</b>"))
        ev_label = QLabel(BAYESIAN_EVIDENCE_NOTICE)
        ev_label.setWordWrap(True)
        ev_label.setStyleSheet("color: #d8dee9; font-size: 10px; font-style: italic;")
        tab_det_layout.addWidget(ev_label)

        tab_det_layout.addStretch(1)
        side_tabs.addTab(tab_details, "Differential Analysis")

        # Tab 2: Inventory
        self.inv_table = QTableWidget(0, 5)
        self.inv_table.setHorizontalHeaderLabels(["Name", "Atmosphere", "Opacities", "Points", "Residual RMS"])
        self.inv_table.horizontalHeader().setStretchLastSection(True)
        self.inv_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.inv_table.verticalHeader().setVisible(False)
        self.inv_table.setStyleSheet("font-size: 11px;")
        side_tabs.addTab(self.inv_table, f"Saved Configurations ({len(self.variants)})")

        splitter.addWidget(side_tabs)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter, 1)

        # Bottom row
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        main_layout.addLayout(btn_row)

    def _populate_selectors(self) -> None:
        self.sel_a.blockSignals(True)
        self.sel_b.blockSignals(True)
        self.sel_a.clear()
        self.sel_b.clear()

        for idx, v in enumerate(self.variants):
            self.sel_a.addItem(v.name, idx)
            self.sel_b.addItem(v.name, idx)

        self.sel_a.setCurrentIndex(self._current_a_idx)
        self.sel_b.setCurrentIndex(self._current_b_idx)
        self.sel_a.blockSignals(False)
        self.sel_b.blockSignals(False)

    def _populate_inventory_table(self) -> None:
        self.inv_table.setRowCount(len(self.variants))
        for row, v in enumerate(self.variants):
            self.inv_table.setItem(row, 0, QTableWidgetItem(v.name))
            p_cloud_str = f"P_c={v.cloud_pressure_bar} bar" if v.cloud_pressure_bar is not None else "Clear"
            self.inv_table.setItem(row, 1, QTableWidgetItem(f"{v.atmosphere_structure} ({p_cloud_str})"))
            self.inv_table.setItem(row, 2, QTableWidgetItem(f"{v.opacity_source_kind} ({', '.join(v.included_species)})"))
            self.inv_table.setItem(row, 3, QTableWidgetItem(str(v.data_point_count)))
            self.inv_table.setItem(row, 4, QTableWidgetItem(f"{v.rms_residual:.4f}%"))

    def _on_sel_a_changed(self, idx: int) -> None:
        if 0 <= idx < len(self.variants):
            self._current_a_idx = idx
            self._update_comparison()

    def _on_sel_b_changed(self, idx: int) -> None:
        if 0 <= idx < len(self.variants):
            self._current_b_idx = idx
            self._update_comparison()

    def _update_comparison(self) -> None:
        if not self.variants:
            return

        var_a = self.variants[self._current_a_idx]
        var_b = self.variants[self._current_b_idx]

        delta = compare_scientific_assumptions(var_a, var_b)

        # 1. Update Domain Status & Warning
        if delta.data_domains_identical:
            self.domain_badge.setText("IDENTICAL DATA DOMAIN")
            self.domain_badge.setStyleSheet("background-color: #2e7d32; color: white;")
            self.domain_warning_label.setVisible(False)
        else:
            self.domain_badge.setText("DIFFERENT WAVELENGTH SUBSETS")
            self.domain_badge.setStyleSheet("background-color: #d08770; color: white;")
            self.domain_warning_label.setText(f"⚠️ {delta.domain_warning}")
            self.domain_warning_label.setVisible(True)

        # 2. Update Differences Text
        diff_lines = [f"• {d}" for d in delta.assumption_differences]
        self.diffs_label.setText("<br>".join(diff_lines))

        # 3. Update Differential Stats Text
        stat_lines = [
            f"<b>Model Prediction Difference RMS:</b> {delta.model_prediction_delta_rms:.4f}%",
            f"<b>Max Model Prediction Difference:</b> {delta.max_model_prediction_delta:.4f}%",
            f"<b>Residual RMS Change (B - A):</b> {delta.delta_rms_residual:+.4f}%",
        ]
        if delta.delta_reduced_chi2 is not None:
            stat_lines.append(f"<b>Reduced χ_ν² Change (B - A):</b> {delta.delta_reduced_chi2:+.3f}")
        else:
            stat_lines.append("<b>Reduced χ_ν² Change:</b> <i>Unavailable (differing data domains)</i>")
        self.stats_label.setText("<br>".join(stat_lines))

        # 4. Update Plots
        n_pts = min(len(var_a.model_predictions), len(var_b.model_predictions))
        x = np.linspace(var_a.wavelength_range_um[0], var_a.wavelength_range_um[1], n_pts)
        ya = np.asarray(var_a.model_predictions[:n_pts], dtype=float)
        yb = np.asarray(var_b.model_predictions[:n_pts], dtype=float)
        ydiff = yb - ya

        self.top_plot.clear()
        self.bot_plot.clear()

        self.top_plot.plot(x, ya, pen=pg.mkPen("#81a1c1", width=2), name=f"Model A: {var_a.name}")
        self.top_plot.plot(x, yb, pen=pg.mkPen("#bf616a", width=2, style=Qt.DashLine), name=f"Model B: {var_b.name}")

        self.bot_plot.plot(x, ydiff, pen=pg.mkPen("#ebcb8b", width=1.5), name="Model Differential (B - A)")
        self.bot_plot.addLine(y=0.0, pen=pg.mkPen("#4c566a"))

