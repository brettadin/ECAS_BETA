"""Interactive parameter sensitivity and observational constraints dialog.

Allows users to inspect "What can this observation constrain?" by varying physical
forward-model parameters (T, Rp, Pcloud, molecular abundances) and observing predicted
spectral changes and significance relative to observational uncertainties.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ecas.comparison.sensitivity import (
    SCIENTIFIC_BOUNDARY_NOTICE,
    ParameterDegeneracy,
    SensitivityAnalysisResult,
    SensitivityPerturbation,
)


class ParameterSensitivityDialog(QDialog):
    """Interactive visual inspection of observational constraints and forward-model sensitivity."""

    def __init__(
        self,
        sensitivity_result: SensitivityAnalysisResult,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("What Can This Observation Constrain? — Parameter Sensitivity")
        self.resize(960, 680)

        self.res = sensitivity_result
        self._current_pert_index = 0

        self._setup_ui()
        self._populate_perturbation_selector()
        self._update_display()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Scientific Boundary Banner
        banner = QFrame()
        banner.setFrameShape(QFrame.StyledPanel)
        banner.setStyleSheet(
            "background-color: #242933; border: 1px solid #4c566a; border-radius: 4px; padding: 6px;"
        )
        b_layout = QVBoxLayout(banner)
        b_layout.setContentsMargins(8, 6, 8, 6)
        b_title = QLabel("<b>Forward-Model Observational Sensitivity & Constraint Analysis</b>")
        b_title.setStyleSheet("color: #88c0d0; font-size: 11.5px;")
        b_desc = QLabel(SCIENTIFIC_BOUNDARY_NOTICE)
        b_desc.setWordWrap(True)
        b_desc.setStyleSheet("color: #d8dee9; font-size: 10.5px;")
        b_layout.addWidget(b_title)
        b_layout.addWidget(b_desc)
        main_layout.addWidget(banner)

        # 2. Parameter Selector & Metric Summary Row
        ctrl_card = QFrame()
        ctrl_card.setStyleSheet("background-color: #1e222a; border-radius: 4px; padding: 6px;")
        ctrl_layout = QHBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(6, 4, 6, 4)

        ctrl_layout.addWidget(QLabel("<b>Parameter Variation:</b>"))
        self.pert_selector = QComboBox()
        self.pert_selector.currentIndexChanged.connect(self._on_perturbation_changed)
        ctrl_layout.addWidget(self.pert_selector, 1)

        self.summary_badge = QLabel("")
        self.summary_badge.setStyleSheet(
            "font-weight: bold; padding: 4px 10px; border-radius: 3px; font-size: 11px;"
        )
        ctrl_layout.addWidget(self.summary_badge)
        main_layout.addWidget(ctrl_card)

        # 3. Main Splitter: Plots (left) + Degeneracies & Diagnostic Tables (right)
        splitter = QSplitter(Qt.Horizontal)

        # Left: Plots
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(6)

        # Top Plot: Model predictions vs Observation
        self.top_plot = pg.PlotWidget()
        self.top_plot.setTitle("Transit Depth Model Predictions vs Observation")
        self.top_plot.setLabel("bottom", "Wavelength", units="µm")
        self.top_plot.setLabel("left", "Transit Depth", units="%")
        self.top_plot.addLegend(offset=(10, 10))
        self.top_plot.showGrid(x=True, y=True, alpha=0.3)
        plot_layout.addWidget(self.top_plot, 2)

        # Bottom Plot: Spectral Change Delta D or Delta D / sigma
        self.bot_plot = pg.PlotWidget()
        self.bot_plot.setTitle("Spectral Change (Perturbed - Baseline)")
        self.bot_plot.setLabel("bottom", "Wavelength", units="µm")
        self.bot_plot.setLabel("left", "Δ Depth", units="%")
        self.bot_plot.addLegend(offset=(10, 10))
        self.bot_plot.showGrid(x=True, y=True, alpha=0.3)
        plot_layout.addWidget(self.bot_plot, 1)

        splitter.addWidget(plot_container)

        # Right: Tabs for Degeneracies, Weak Parameters, and Technical Values
        side_tabs = QTabWidget()
        side_tabs.setMaximumWidth(420)

        # Tab 1: Degeneracies
        self.degen_table = QTableWidget(0, 3)
        self.degen_table.setHorizontalHeaderLabels(["Param A", "Param B", "Correlation (r)"])
        self.degen_table.horizontalHeader().setStretchLastSection(True)
        self.degen_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.degen_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.degen_table.verticalHeader().setVisible(False)
        self.degen_table.setStyleSheet("font-size: 11px;")
        side_tabs.addTab(self.degen_table, f"Degeneracies ({len(self.res.degenerate_pairs)})")

        # Tab 2: Parameter summary table
        self.param_table = QTableWidget(0, 4)
        self.param_table.setHorizontalHeaderLabels(["Parameter", "Δ Size", "Max Δ (%)", "Max Δ/σ"])
        self.param_table.horizontalHeader().setStretchLastSection(True)
        self.param_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.param_table.verticalHeader().setVisible(False)
        self.param_table.setStyleSheet("font-size: 11px;")
        side_tabs.addTab(self.param_table, "All Parameters")

        splitter.addWidget(side_tabs)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter, 1)

        # Bottom button row
        btn_row = QHBoxLayout()
        self.weak_warning_label = QLabel("")
        self.weak_warning_label.setStyleSheet("color: #ebcb8b; font-weight: 500;")
        btn_row.addWidget(self.weak_warning_label, 1)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        main_layout.addLayout(btn_row)

        self._populate_side_tabs()

    def _populate_perturbation_selector(self) -> None:
        self.pert_selector.blockSignals(True)
        self.pert_selector.clear()
        for idx, p in enumerate(self.res.perturbations):
            label = f"{p.display_name} ({p.perturbation_direction}{abs(p.perturbation_delta):g} {p.unit})"
            if p.has_weak_sensitivity:
                label += " [Weak]"
            self.pert_selector.addItem(label, idx)
        self.pert_selector.blockSignals(False)

    def _populate_side_tabs(self) -> None:
        # Populate Degeneracies Table
        degens = self.res.degeneracies
        self.degen_table.setRowCount(len(degens))
        for row, d in enumerate(degens):
            item_a = QTableWidgetItem(d.param_a)
            item_b = QTableWidgetItem(d.param_b)
            item_r = QTableWidgetItem(f"{d.correlation_coefficient:+.2f}")
            if d.is_degenerate:
                item_r.setForeground(Qt.GlobalColor.yellow)
                item_r.setToolTip(d.explanation)
            self.degen_table.setItem(row, 0, item_a)
            self.degen_table.setItem(row, 1, item_b)
            self.degen_table.setItem(row, 2, item_r)

        # Populate Parameter Summary Table
        self.param_table.setRowCount(len(self.res.perturbations))
        for row, p in enumerate(self.res.perturbations):
            name_item = QTableWidgetItem(f"{p.parameter_name} ({p.perturbation_direction})")
            size_item = QTableWidgetItem(f"{p.perturbation_delta:g} {p.unit}")
            delta_item = QTableWidgetItem(f"{p.max_abs_delta:.4f}")
            sig_text = f"{p.max_significance_ratio:.2f} σ" if p.max_significance_ratio is not None else "n/a"
            sig_item = QTableWidgetItem(sig_text)

            if p.has_weak_sensitivity:
                sig_item.setForeground(Qt.GlobalColor.gray)
                sig_item.setToolTip(p.weak_sensitivity_explanation or "Weak sensitivity")

            self.param_table.setItem(row, 0, name_item)
            self.param_table.setItem(row, 1, size_item)
            self.param_table.setItem(row, 2, delta_item)
            self.param_table.setItem(row, 3, sig_item)

    def _on_perturbation_changed(self, index: int) -> None:
        if index >= 0 and index < len(self.res.perturbations):
            self._current_pert_index = index
            self._update_display()

    def _update_display(self) -> None:
        if not self.res.perturbations:
            return

        pert = self.res.perturbations[self._current_pert_index]
        x = np.asarray(self.res.wavelengths_um, dtype=float)
        y_base = np.asarray(self.res.baseline_spectrum, dtype=float)
        y_pert = np.asarray(pert.perturbed_spectrum, dtype=float)
        delta = np.asarray(pert.delta_spectrum, dtype=float)

        # 1. Update Top Plot
        self.top_plot.clear()
        self.top_plot.plot(
            x, y_base,
            pen=pg.mkPen("#81a1c1", width=2.0),
            name="Baseline Model Prediction",
        )
        self.top_plot.plot(
            x, y_pert,
            pen=pg.mkPen("#bf616a", width=2.0, style=Qt.DashLine),
            name=f"Perturbed Model ({pert.display_name} {pert.perturbation_direction})",
        )

        # 2. Update Bottom Plot
        self.bot_plot.clear()
        if pert.relative_to_uncertainty is not None:
            rel = np.asarray(pert.relative_to_uncertainty, dtype=float)
            self.bot_plot.setLabel("left", "Δ Depth / σ", units="σ")
            self.bot_plot.setTitle(f"Perturbation Significance Relative to 1σ Uncertainty (Max = {pert.max_significance_ratio:.2f}σ)")
            self.bot_plot.plot(
                x, rel,
                pen=pg.mkPen("#ebcb8b", width=1.5),
                name="Δ / σ (Significance of Change)",
            )
            # Add horizontal 1-sigma reference lines
            self.bot_plot.addLine(y=1.0, pen=pg.mkPen("#4c566a", style=Qt.DotLine))
            self.bot_plot.addLine(y=-1.0, pen=pg.mkPen("#4c566a", style=Qt.DotLine))
            self.bot_plot.addLine(y=0.0, pen=pg.mkPen("#3b4252"))
        else:
            self.bot_plot.setLabel("left", "Δ Depth", units="%")
            self.bot_plot.setTitle(f"Unweighted Spectral Change (Max |Δ| = {pert.max_abs_delta:.4f}%)")
            self.bot_plot.plot(
                x, delta,
                pen=pg.mkPen("#88c0d0", width=1.5),
                name="Δ Depth (Perturbed - Baseline)",
            )
            self.bot_plot.addLine(y=0.0, pen=pg.mkPen("#3b4252"))

        # 3. Update Badge & Warning
        if pert.has_weak_sensitivity:
            self.summary_badge.setText("WEAK OBSERVATIONAL CONSTRAINT")
            self.summary_badge.setStyleSheet(
                "background-color: #434c5e; color: #eceff4; font-weight: bold; padding: 4px 10px; border-radius: 3px;"
            )
            self.weak_warning_label.setText(
                f"<b>Notice:</b> {pert.weak_sensitivity_explanation}"
            )
        else:
            sig_str = f"Max Effect: {pert.max_significance_ratio:.2f}σ" if pert.max_significance_ratio is not None else f"Max Δ: {pert.max_abs_delta:.4f}%"
            self.summary_badge.setText(f"OBSERVABLE RESPONSE ({sig_str})")
            self.summary_badge.setStyleSheet(
                "background-color: #2e7d32; color: #ffffff; font-weight: bold; padding: 4px 10px; border-radius: 3px;"
            )
            self.weak_warning_label.setText("")

