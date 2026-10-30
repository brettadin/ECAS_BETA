"""Interactive observation consistency and reduction pipeline comparison dialog.

Allows users to inspect consistency across multiple datasets for the same planet:
- Discovers alternative reductions of the same exposure (e.g. Eureka, FIREFLy, Tiberius, Tshirt, Feinstein).
- Enforces the scientific rule that alternative reductions are NOT independent evidence.
- Computes non-destructive systematic median offsets, residual RMS, and consistency chi-squared.
- Exposes downstream nuisance parameter specifications for joint fitting.
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

from ecas.comparison.consistency import (
    MultiObservationConsistencyReport,
    PairwiseConsistency,
    compare_observation_consistency,
)
from ecas.models.spectrum import SpectrumData
from ecas.observations import ObservationContext


class ObservationConsistencyDialog(QDialog):
    """Dialog for reviewing multi-dataset consistency and pipeline reduction differences."""

    def __init__(
        self,
        report: MultiObservationConsistencyReport,
        datasets: Sequence[SpectrumData | ObservationContext],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Observation Consistency — {report.target_name}")
        self.resize(1020, 720)

        self.report = report
        self.datasets = datasets
        self._current_pair_index = 0

        self._setup_ui()
        self._populate_datasets_table()
        self._populate_pair_selector()
        self._update_pair_display()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Header Card with Target & Clusters Notice
        header_card = QFrame()
        header_card.setStyleSheet("background-color: #242933; border: 1px solid #434c5e; border-radius: 4px; padding: 6px;")
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(8, 6, 8, 6)

        title_lbl = QLabel(f"<b>Target: {self.report.target_name}</b> ({len(self.report.datasets)} datasets evaluated)")
        title_lbl.setStyleSheet("color: #88c0d0; font-size: 12px;")
        h_layout.addWidget(title_lbl)

        if self.report.warnings:
            for w in self.report.warnings:
                w_lbl = QLabel(f"⚠️ {w}")
                w_lbl.setStyleSheet("color: #ebcb8b; font-weight: 500; font-size: 11px;")
                w_lbl.setWordWrap(True)
                h_layout.addWidget(w_lbl)
        main_layout.addWidget(header_card)

        # 2. Main Tabs: Overview vs Pairwise Deep Dive
        self.tabs = QTabWidget()

        # Tab 1: Dataset Overview Table
        tab_overview = QWidget()
        tab_over_layout = QVBoxLayout(tab_overview)
        tab_over_layout.setContentsMargins(4, 4, 4, 4)

        self.datasets_table = QTableWidget(0, 7)
        self.datasets_table.setHorizontalHeaderLabels([
            "ID", "Pipeline / Reduction", "Instrument / Mode", "Epoch", "Range (µm)", "Points", "Uncertainties"
        ])
        self.datasets_table.horizontalHeader().setStretchLastSection(True)
        self.datasets_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.datasets_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.datasets_table.verticalHeader().setVisible(False)
        self.datasets_table.setStyleSheet("font-size: 11px;")
        tab_over_layout.addWidget(self.datasets_table)
        self.tabs.addTab(tab_overview, "Dataset Inventory")

        # Tab 2: Pairwise Consistency Comparison
        tab_pair = QWidget()
        tab_pair_layout = QVBoxLayout(tab_pair)
        tab_pair_layout.setContentsMargins(4, 4, 4, 4)
        tab_pair_layout.setSpacing(6)

        # Selector Row
        pair_sel_row = QHBoxLayout()
        pair_sel_row.addWidget(QLabel("<b>Compare Pair:</b>"))
        self.pair_selector = QComboBox()
        self.pair_selector.currentIndexChanged.connect(self._on_pair_changed)
        pair_sel_row.addWidget(self.pair_selector, 1)

        self.rel_badge = QLabel("")
        self.rel_badge.setStyleSheet("font-weight: bold; padding: 4px 10px; border-radius: 3px; font-size: 11px;")
        pair_sel_row.addWidget(self.rel_badge)
        tab_pair_layout.addLayout(pair_sel_row)

        self.independence_banner = QLabel("")
        self.independence_banner.setWordWrap(True)
        self.independence_banner.setStyleSheet("color: #ebcb8b; font-size: 11px; padding: 2px 4px;")
        tab_pair_layout.addWidget(self.independence_banner)

        # Pairwise Splitter (Plots left, Metrics & Nuisance right)
        splitter = QSplitter(Qt.Horizontal)

        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.setSpacing(4)

        self.top_plot = pg.PlotWidget()
        self.top_plot.setTitle("Empirical Spectra Comparison")
        self.top_plot.setLabel("bottom", "Wavelength", units="µm")
        self.top_plot.setLabel("left", "Transit Depth", units="%")
        self.top_plot.addLegend(offset=(10, 10))
        self.top_plot.showGrid(x=True, y=True, alpha=0.3)
        plot_layout.addWidget(self.top_plot, 2)

        self.bot_plot = pg.PlotWidget()
        self.bot_plot.setTitle("Residual Difference (A - B)")
        self.bot_plot.setLabel("bottom", "Wavelength", units="µm")
        self.bot_plot.setLabel("left", "Difference (A - B)", units="%")
        self.bot_plot.addLegend(offset=(10, 10))
        self.bot_plot.showGrid(x=True, y=True, alpha=0.3)
        plot_layout.addWidget(self.bot_plot, 1)

        splitter.addWidget(plot_container)

        # Right side: Metric cards & Joint fitting nuisance recommendations
        metrics_panel = QFrame()
        metrics_panel.setStyleSheet("background-color: #1e222a; border-radius: 4px; padding: 8px;")
        m_layout = QVBoxLayout(metrics_panel)
        m_layout.setContentsMargins(8, 8, 8, 8)
        m_layout.setSpacing(6)

        m_layout.addWidget(QLabel("<b>Consistency Diagnostics:</b>"))
        self.metrics_label = QLabel("")
        self.metrics_label.setWordWrap(True)
        self.metrics_label.setStyleSheet("font-size: 11px; line-height: 1.4;")
        m_layout.addWidget(self.metrics_label)

        m_layout.addWidget(QLabel("<b>Downstream Joint-Fitting Nuisance Specification:</b>"))
        self.nuisance_label = QLabel("")
        self.nuisance_label.setWordWrap(True)
        self.nuisance_label.setStyleSheet("font-family: monospace; font-size: 10.5px; background-color: #242933; padding: 6px; border-radius: 3px;")
        m_layout.addWidget(self.nuisance_label)

        m_layout.addStretch(1)
        splitter.addWidget(metrics_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        tab_pair_layout.addWidget(splitter, 1)
        self.tabs.addTab(tab_pair, "Pairwise Comparison & Offsets")
        self.tabs.setCurrentIndex(1)  # Focus on pairwise

        main_layout.addWidget(self.tabs, 1)

        # Bottom row
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        main_layout.addLayout(btn_row)

    def _populate_datasets_table(self) -> None:
        ds = self.report.datasets
        self.datasets_table.setRowCount(len(ds))
        for row, d in enumerate(ds):
            self.datasets_table.setItem(row, 0, QTableWidgetItem(d.source_id))
            self.datasets_table.setItem(row, 1, QTableWidgetItem(d.pipeline_or_reduction))
            self.datasets_table.setItem(row, 2, QTableWidgetItem(f"{d.instrument} ({d.observing_mode})"))
            self.datasets_table.setItem(row, 3, QTableWidgetItem(d.epoch or "n/a"))
            self.datasets_table.setItem(row, 4, QTableWidgetItem(f"{d.wavelength_min_um:.3g} – {d.wavelength_max_um:.3g}"))
            self.datasets_table.setItem(row, 5, QTableWidgetItem(f"{d.point_count} (Δλ={d.median_resolution_delta_um:.4f})"))
            self.datasets_table.setItem(row, 6, QTableWidgetItem("Yes (1σ)" if d.has_uncertainties else "None"))

    def _populate_pair_selector(self) -> None:
        self.pair_selector.blockSignals(True)
        self.pair_selector.clear()
        for idx, p in enumerate(self.report.pairwise_comparisons):
            rel_str = f"[{p.relationship}]"
            self.pair_selector.addItem(f"{p.dataset_a_name} vs {p.dataset_b_name} {rel_str}", idx)
        self.pair_selector.blockSignals(False)

    def _on_pair_changed(self, index: int) -> None:
        if 0 <= index < len(self.report.pairwise_comparisons):
            self._current_pair_index = index
            self._update_pair_display()

    def _update_pair_display(self) -> None:
        if not self.report.pairwise_comparisons:
            return

        pair = self.report.pairwise_comparisons[self._current_pair_index]

        # Style relationship badge
        if pair.relationship == "DUPLICATE_FILE":
            self.rel_badge.setText("DUPLICATE FILE")
            self.rel_badge.setStyleSheet("background-color: #bf616a; color: white;")
        elif pair.relationship == "ALTERNATIVE_REDUCTION":
            self.rel_badge.setText("ALTERNATIVE REDUCTION (SAME EXPOSURE)")
            self.rel_badge.setStyleSheet("background-color: #d08770; color: white;")
        else:
            self.rel_badge.setText("INDEPENDENT OBSERVATIONS")
            self.rel_badge.setStyleSheet("background-color: #a3be8c; color: #2e3440;")

        self.independence_banner.setText(pair.independence_warning or "")

        # Format diagnostics text
        lines = [
            f"<b>Overlap Range:</b> {f'{pair.overlap_range_um[0]:.3g} – {pair.overlap_range_um[1]:.3g} µm' if pair.overlap_range_um else 'None'} ({pair.overlap_point_count} points)",
            f"<b>Resolution:</b> {pair.resolution_notes}",
        ]
        if pair.systematic_median_offset is not None:
            off_err_str = f" ± {pair.offset_uncertainty:.4f}" if pair.offset_uncertainty else ""
            lines.append(f"<b>Systematic Median Offset (A - B):</b> {pair.systematic_median_offset:+.4f}%{off_err_str}")
            lines.append(f"<b>Offset-Subtracted Residual RMS:</b> {pair.offset_subtracted_rms:.4f}%")
        if pair.reduced_chi2 is not None:
            lines.append(f"<b>Consistency χ² / dof:</b> {pair.consistency_chi2:.1f} (reduced χ_ν² = {pair.reduced_chi2:.2f})")
            if pair.max_discrepancy_sigma is not None:
                lines.append(f"<b>Peak Pointwise Discrepancy:</b> {pair.max_discrepancy_sigma:.2f} σ")
            if pair.discrepancy_locations_um:
                locs_str = ", ".join(f"{loc:.3g} µm" for loc in pair.discrepancy_locations_um[:6])
                lines.append(f"<b>Regions with >2.5σ Deviation:</b> {locs_str}")

        self.metrics_label.setText("<br>".join(lines))

        # Nuisance Spec
        if pair.nuisance_parameter_spec:
            spec = pair.nuisance_parameter_spec
            spec_text = (
                f"Parameter: {spec['parameter_name']}\n"
                f"Offset Value: {spec['estimated_value']:+.5g} {spec['unit']}\n"
                f"Recommended Joint-Fitting Prior: {spec['prior_recommendation']}\n"
                "Note: Floating offset required to account for instrument slit losses / detector shifts."
            )
            self.nuisance_label.setText(spec_text)
        else:
            self.nuisance_label.setText("No nuisance parameters required (no mutual overlap).")

        # 3. Update Plots
        item_a = self.datasets[pair.dataset_a_index]
        item_b = self.datasets[pair.dataset_b_index]

        from ecas.comparison.consistency import _get_dataset_arrays
        xa, ya, sa = _get_dataset_arrays(item_a)
        xb, yb, sb = _get_dataset_arrays(item_b)

        self.top_plot.clear()
        self.bot_plot.clear()

        self.top_plot.plot(xa, ya, pen=None, symbol="o", symbolSize=5, symbolBrush="#88c0d0", name=pair.dataset_a_name)
        self.top_plot.plot(xb, yb, pen=None, symbol="t", symbolSize=5, symbolBrush="#bf616a", name=pair.dataset_b_name)

        if pair.overlap_range_um is not None and pair.systematic_median_offset is not None:
            ov_mask = (xa >= pair.overlap_range_um[0]) & (xa <= pair.overlap_range_um[1])
            sub_xa = xa[ov_mask]
            sub_ya = ya[ov_mask]
            sub_yb = np.interp(sub_xa, xb, yb)
            diff = sub_ya - sub_yb

            self.bot_plot.plot(sub_xa, diff, pen=pg.mkPen("#d8dee9", width=1.5), symbol="o", symbolSize=4, name="Raw Difference (A - B)")
            self.bot_plot.addLine(y=pair.systematic_median_offset, pen=pg.mkPen("#ebcb8b", width=1.5, style=Qt.DashLine))
            self.bot_plot.addLine(y=0.0, pen=pg.mkPen("#4c566a"))

