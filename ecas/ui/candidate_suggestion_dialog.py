"""Interactive candidate molecule suggestion and hypothesis screening dialog.

Allows users to load an exoplanet observation or laboratory spectrum and discover
which candidate molecules deserve further investigation, without having to choose
molecules in advance.

Adheres strictly to the TauREx 'Marple' screening philosophy (Waldmann et al. 2015)
and incorporates species-selection bias protections and look-elsewhere disclosures
(MacDonald & Batalha 2023, Welbanks et al. 2024).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ecas.comparison.candidate_screener import (
    CandidatePool,
    CandidatePoolEntry,
    CandidateScreeningResult,
    ScreeningReport,
    build_candidate_pool,
    screen_candidates,
)
from ecas.comparison.eligibility import ComparisonInput

# Distinct, stable molecule colors
MOLECULE_COLORS = {
    "H2O": "#38bdf8",  # Sky blue
    "CO2": "#f97316",  # Bright orange
    "CH4": "#a855f7",  # Purple
    "CO": "#eab308",   # Amber / gold
    "NH3": "#10b981",  # Emerald
    "SO2": "#ef4444",  # Red
    "H2S": "#ec4899",  # Pink
    "HCN": "#06b6d4",  # Cyan
    "TiO": "#f43f5e",  # Rose
    "VO": "#8b5cf6",   # Violet
    "C2H2": "#e2e8f0", # Slate light
    "C2H4": "#94a3b8", # Slate
}


class CandidateSuggestionDialog(QDialog):
    """Dialog for suggesting candidate molecules from real reference libraries."""

    candidates_applied = Signal(list)  # Emits list of selected formula strings

    def __init__(
        self,
        report: ScreeningReport,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.report = report
        self.pool = report.pool
        self._current_result_index = 0

        self.setWindowTitle(f"Candidate Molecule Suggestions — {report.target_id}")
        self.resize(1080, 740)
        self.setMinimumSize(880, 580)

        self._setup_ui()
        self._populate_pool_table()
        self._populate_results_table()
        if self.report.results:
            self._select_result_row(0)

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Header Banner & Guidance
        header_card = QFrame()
        header_card.setFrameShape(QFrame.StyledPanel)
        header_card.setStyleSheet("QFrame { background-color: #1e293b; border-radius: 6px; padding: 10px; }")
        h_layout = QVBoxLayout(header_card)
        h_layout.setContentsMargins(8, 8, 8, 8)
        h_layout.setSpacing(4)

        title_label = QLabel("💡 Candidate Molecule Screening & Hypothesis Generation")
        title_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #38bdf8;")
        h_layout.addWidget(title_label)

        sub_label = QLabel(
            "Screen available molecular reference libraries against this observation using instrument-aware "
            "physical radiative transfer (or empirical laboratory fitting). "
            "Suggestions are candidate hypotheses for detailed modelling, not calibrated Bayesian posteriors."
        )
        sub_label.setWordWrap(True)
        sub_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        h_layout.addWidget(sub_label)

        # Badge summary
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)

        obs_badge = QLabel(f"<b>Target:</b> {self.report.target_id}")
        obs_badge.setStyleSheet("background: #0f172a; padding: 3px 8px; border-radius: 4px; color: #f1f5f9; font-size: 11px;")
        badges_layout.addWidget(obs_badge)

        cov_badge = QLabel(
            f"<b>Coverage:</b> {self.pool.observation_domain_um[0]:.2f}–{self.pool.observation_domain_um[1]:.2f} µm "
            f"({self.pool.observation_points_count} pts)"
        )
        cov_badge.setStyleSheet("background: #0f172a; padding: 3px 8px; border-radius: 4px; color: #f1f5f9; font-size: 11px;")
        badges_layout.addWidget(cov_badge)

        mode_badge = QLabel(f"<b>Mode:</b> {self.report.mode.replace('_', ' ').title()}")
        mode_badge.setStyleSheet("background: #0f172a; padding: 3px 8px; border-radius: 4px; color: #a7f3d0; font-size: 11px;")
        badges_layout.addWidget(mode_badge)

        if self.report.planet_preset_id:
            preset_badge = QLabel(f"<b>Preset:</b> {self.report.planet_preset_id}")
            preset_badge.setStyleSheet("background: #0f172a; padding: 3px 8px; border-radius: 4px; color: #fde047; font-size: 11px;")
            badges_layout.addWidget(preset_badge)

        badges_layout.addStretch()
        h_layout.addLayout(badges_layout)
        main_layout.addWidget(header_card)

        # 2. Main Tabbed Workspaces
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabWidget::pane { border: 1px solid #334155; border-radius: 4px; } "
            "QTabBar::tab { background: #0f172a; color: #94a3b8; padding: 8px 16px; margin-right: 2px; } "
            "QTabBar::tab:selected { background: #1e293b; color: #38bdf8; font-weight: bold; border-top: 2px solid #38bdf8; }"
        )

        # Tab 1: Screening Suggestions & Results
        self.results_tab = self._create_results_tab()
        self.tabs.addTab(self.results_tab, f"🎯 Suggested Candidates ({len(self.report.results)})")

        # Tab 2: Candidate Pool & Reference Availability
        self.pool_tab = self._create_pool_tab()
        self.tabs.addTab(self.pool_tab, f"📚 Reference Library Pool ({len(self.pool.all_entries)})")

        # Tab 3: Combinations & Unexplained Features
        self.joint_tab = self._create_joint_tab()
        self.tabs.addTab(self.joint_tab, "🔬 Alternatives & Multi-Absorbers")

        main_layout.addWidget(self.tabs, stretch=1)

        # 3. Bottom Action Bar
        bottom_bar = QHBoxLayout()
        bottom_bar.setSpacing(10)

        self.apply_btn = QPushButton("➡ Apply Selected Candidates to Atmospheric Model")
        self.apply_btn.setStyleSheet(
            "QPushButton { background-color: #0284c7; color: white; font-weight: bold; padding: 8px 18px; border-radius: 5px; } "
            "QPushButton:hover { background-color: #0369a1; }"
        )
        self.apply_btn.clicked.connect(self._apply_selected_candidates)
        bottom_bar.addWidget(self.apply_btn)

        self.export_btn = QPushButton("📄 Export Screening Manifest...")
        self.export_btn.setStyleSheet("padding: 8px 14px; border-radius: 5px;")
        self.export_btn.clicked.connect(self._export_manifest)
        bottom_bar.addWidget(self.export_btn)

        bottom_bar.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("padding: 8px 16px; border-radius: 5px;")
        close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(close_btn)

        main_layout.addLayout(bottom_bar)

    def _create_results_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        if self.report.uncertainty_notice:
            banner = QLabel(f"⚠️ <b>Methodological Notice:</b> {self.report.uncertainty_notice}")
            banner.setWordWrap(True)
            banner.setStyleSheet("background-color: #451a03; color: #fde047; border: 1px solid #b45309; padding: 6px 10px; border-radius: 4px; font-size: 11px;")
            layout.addWidget(banner)

        splitter = QSplitter(Qt.Horizontal)

        # Left Panel: Results Table
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        # Filter row
        filter_row = QHBoxLayout()
        filter_label = QLabel("Filter:")
        filter_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        filter_row.addWidget(filter_label)

        self.results_filter_combo = QComboBox()
        self.results_filter_combo.addItems([
            "All Evaluated Candidates",
            "Promising Only (Δχ² > 0)",
            "Strong Candidates Only",
        ])
        self.results_filter_combo.currentIndexChanged.connect(self._filter_results_table)
        filter_row.addWidget(self.results_filter_combo)
        filter_row.addStretch()
        left_layout.addLayout(filter_row)

        self.results_table = QTableWidget()
        self.results_table.setColumnCount(8)
        self.results_table.setHorizontalHeaderLabels([
            "Follow-up",
            "Molecule",
            "Outcome",
            "ΔRMS (%)",
            "Δχ²",
            "Reduced χ²",
            "Coverage (µm)",
            "Consistency / Alternatives",
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SingleSelection)
        self.results_table.setStyleSheet("QTableWidget { background: #0f172a; alternate-background-color: #1e293b; color: #f1f5f9; }")
        self.results_table.setAlternatingRowColors(True)
        self.results_table.cellClicked.connect(self._on_result_cell_clicked)
        left_layout.addWidget(self.results_table)

        splitter.addWidget(left_panel)

        # Right Panel: Interactive Plot & Details
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        # Plot Widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#0f172a")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.25)
        self.plot_widget.setLabel("bottom", "Wavelength", units="µm")
        self.plot_widget.setLabel("left", "Transit Depth", units="%" if self.report.mode == "planetary_transmission" else "")
        self.plot_widget.addLegend(offset=(10, 10))
        right_layout.addWidget(self.plot_widget, stretch=3)

        # Detail Inspection Card
        detail_card = QFrame()
        detail_card.setFrameShape(QFrame.StyledPanel)
        detail_card.setStyleSheet("QFrame { background-color: #1e293b; border-radius: 6px; padding: 6px; }")
        d_layout = QVBoxLayout(detail_card)
        d_layout.setContentsMargins(8, 8, 8, 8)
        d_layout.setSpacing(4)

        self.detail_title = QLabel("Candidate Details")
        self.detail_title.setStyleSheet("font-weight: bold; color: #38bdf8; font-size: 13px;")
        d_layout.addWidget(self.detail_title)

        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        self.detail_text.setStyleSheet("QTextEdit { background: #0f172a; color: #e2e8f0; font-size: 11px; border: none; }")
        self.detail_text.setMaximumHeight(140)
        d_layout.addWidget(self.detail_text)

        right_layout.addWidget(detail_card, stretch=2)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 5)
        layout.addWidget(splitter)

        return widget

    def _create_pool_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Filter bar
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        f_label = QLabel("Filter Category:")
        f_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        filter_row.addWidget(f_label)

        self.pool_category_combo = QComboBox()
        self.pool_category_combo.addItems([
            f"All Considered Species ({len(self.pool.all_entries)})",
            f"Searchable Candidates ({len(self.pool.searchable)})",
            f"Partial Coverage Candidates ({len(self.pool.partial)})",
            f"Unavailable Reference Data ({len(self.pool.unavailable)})",
            f"Incompatible Species ({len(self.pool.incompatible)})",
        ])
        self.pool_category_combo.currentIndexChanged.connect(self._filter_pool_table)
        filter_row.addWidget(self.pool_category_combo)

        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: #94a3b8; font-size: 11px; margin-left: 10px;")
        filter_row.addWidget(search_label)

        self.pool_search_edit = QLineEdit()
        self.pool_search_edit.setPlaceholderText("Filter by formula or name (e.g. CO2, CH4, H2O)...")
        self.pool_search_edit.textChanged.connect(self._filter_pool_table)
        filter_row.addWidget(self.pool_search_edit)

        export_pool_btn = QPushButton("💾 Export Pool Inventory (JSON)...")
        export_pool_btn.clicked.connect(self._export_pool_inventory)
        filter_row.addWidget(export_pool_btn)

        layout.addLayout(filter_row)

        # Footnote warning
        note_card = QFrame()
        note_card.setStyleSheet("QFrame { background-color: #0f172a; border-left: 3px solid #38bdf8; padding: 6px; }")
        n_layout = QVBoxLayout(note_card)
        n_layout.setContentsMargins(6, 4, 6, 4)
        note_text = QLabel(
            "<b>Scientific Inventory Notice:</b> 'Unavailable Reference Data' indicates the molecule is present in the "
            "ExoMol master catalogue, but its cross-section has not been downloaded into the local cache. "
            "It is <b>NOT</b> evidence that the molecule is absent from the observed atmosphere."
        )
        note_text.setWordWrap(True)
        note_text.setStyleSheet("color: #94a3b8; font-size: 11px;")
        n_layout.addWidget(note_text)
        layout.addWidget(note_card)

        self.pool_table = QTableWidget()
        self.pool_table.setColumnCount(5)
        self.pool_table.setHorizontalHeaderLabels([
            "Molecule / Formula",
            "Status",
            "Wavelength Range",
            "Reference Source",
            "Availability / Exclusion Reason",
        ])
        self.pool_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.pool_table.horizontalHeader().setStretchLastSection(True)
        self.pool_table.setStyleSheet("QTableWidget { background: #0f172a; alternate-background-color: #1e293b; color: #f1f5f9; }")
        self.pool_table.setAlternatingRowColors(True)
        layout.addWidget(self.pool_table)

        return widget

    def _create_joint_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 1. Joint Candidate Pairs
        pair_box = QGroupBox("Joint Multi-Candidate Pairs (Evaluated for Additive Improvement)")
        pair_box.setStyleSheet("QGroupBox { font-weight: bold; color: #38bdf8; }")
        p_layout = QVBoxLayout(pair_box)

        self.pair_table = QTableWidget()
        self.pair_table.setColumnCount(5)
        self.pair_table.setHorizontalHeaderLabels([
            "Candidate Pair",
            "Joint Δχ²",
            "Additive Gain (Δχ²)",
            "Joint RMS",
            "Outcome & Physical Interpretation",
        ])
        self.pair_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.pair_table.horizontalHeader().setStretchLastSection(True)
        self.pair_table.setStyleSheet("QTableWidget { background: #0f172a; color: #f1f5f9; }")

        if self.report.joint_pairs:
            self.pair_table.setRowCount(len(self.report.joint_pairs))
            for i, p in enumerate(self.report.joint_pairs):
                self.pair_table.setItem(i, 0, QTableWidgetItem(p.pair_name))
                self.pair_table.setItem(i, 1, QTableWidgetItem(f"{p.delta_chi2_vs_baseline:+.1f}"))
                self.pair_table.setItem(i, 2, QTableWidgetItem(f"{p.additive_chi2_improvement:+.1f}"))
                self.pair_table.setItem(i, 3, QTableWidgetItem(f"{p.joint_rms:.5f}"))
                self.pair_table.setItem(i, 4, QTableWidgetItem(f"{p.outcome}: {p.explanation}"))
        else:
            self.pair_table.setRowCount(1)
            self.pair_table.setItem(0, 0, QTableWidgetItem("None evaluated"))
            self.pair_table.setItem(0, 4, QTableWidgetItem("At least two single candidates with positive Δχ² are required to test joint combinations."))

        p_layout.addWidget(self.pair_table)
        layout.addWidget(pair_box)

        # 2. Unexplained Spectral Features
        unexp_box = QGroupBox("Unexplained Spectral Features (> 2σ Residuals Across Top Models)")
        unexp_box.setStyleSheet("QGroupBox { font-weight: bold; color: #f97316; }")
        u_layout = QVBoxLayout(unexp_box)

        unexp_text = QTextEdit()
        unexp_text.setReadOnly(True)
        unexp_text.setStyleSheet("QTextEdit { background: #0f172a; color: #e2e8f0; font-size: 11px; }")

        if self.report.unexplained_regions_um:
            msg = "The following wavelength intervals exhibit significant residual deviations (> 2.2σ) across all evaluated candidate models:\n\n"
            for reg in self.report.unexplained_regions_um:
                msg += f"• {reg[0]:.3f} – {reg[1]:.3f} µm: Residual excess suggests unmodelled trace species, photochemical haze absorption, or instrumental systematic.\n"
        else:
            msg = "No persistent high-significance (> 2.2σ) unmodelled features detected across the evaluated candidates on this wavelength domain."
        unexp_text.setPlainText(msg)
        u_layout.addWidget(unexp_text)
        layout.addWidget(unexp_box)

        return widget

    def _populate_results_table(self) -> None:
        self.results_table.setRowCount(0)
        for i, r in enumerate(self.report.results):
            self.results_table.insertRow(i)

            # Checkbox item
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            check_item.setCheckState(Qt.Checked if r.is_selected_for_followup else Qt.Unchecked)
            self.results_table.setItem(i, 0, check_item)

            # Molecule
            mol_item = QTableWidgetItem(f"{r.formula} ({r.molecule_id})")
            mol_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.results_table.setItem(i, 1, mol_item)

            # Outcome badge
            outcome_item = QTableWidgetItem(r.outcome)
            if r.outcome == "Strong Candidate":
                outcome_item.setForeground(QColor("#4ade80"))  # green
            elif r.outcome == "Moderate Support":
                outcome_item.setForeground(QColor("#a3e635"))  # lime
            elif r.outcome == "Marginal / Weak":
                outcome_item.setForeground(QColor("#facc15"))  # yellow
            else:
                outcome_item.setForeground(QColor("#94a3b8"))  # gray
            self.results_table.setItem(i, 2, outcome_item)

            # Delta RMS
            rms_item = QTableWidgetItem(f"{r.rms_improvement_percent:+.2f}%")
            self.results_table.setItem(i, 3, rms_item)

            # Delta Chi2
            chi2_item = QTableWidgetItem(f"{r.delta_chi2:+.1f}")
            self.results_table.setItem(i, 4, chi2_item)

            # Reduced Chi2
            red_item = QTableWidgetItem(f"{r.reduced_chi2:.2f}")
            self.results_table.setItem(i, 5, red_item)

            # Coverage
            cov_item = QTableWidgetItem(
                f"{r.evaluated_wavelength_range_um[0]:.2f}–{r.evaluated_wavelength_range_um[1]:.2f} ({r.evaluated_points_count} pts)"
            )
            self.results_table.setItem(i, 6, cov_item)

            # Consistency / Alternatives
            alt_summary = r.multi_band_consistency
            if r.competing_alternatives:
                alt_summary += f"; Alt: {', '.join(r.competing_alternatives)}"
            self.results_table.setItem(i, 7, QTableWidgetItem(alt_summary))

    def _filter_results_table(self) -> None:
        mode = self.results_filter_combo.currentText()
        for i in range(self.results_table.rowCount()):
            outcome_text = self.results_table.item(i, 2).text()
            if mode == "All Evaluated Candidates":
                self.results_table.setRowHidden(i, False)
            elif mode == "Promising Only (Δχ² > 0)":
                self.results_table.setRowHidden(i, outcome_text in ("No Improvement", "Inconclusive"))
            elif mode == "Strong Candidates Only":
                self.results_table.setRowHidden(i, outcome_text != "Strong Candidate")

    def _on_result_cell_clicked(self, row: int, col: int) -> None:
        if col == 0:
            # Checkbox toggled
            item = self.results_table.item(row, col)
            is_checked = (item.checkState() == Qt.Checked)
            if 0 <= row < len(self.report.results):
                # Update underlying result selection state
                r = self.report.results[row]
                object.__setattr__(r, "is_selected_for_followup", is_checked)
        self._select_result_row(row)

    def _select_result_row(self, row: int) -> None:
        if not (0 <= row < len(self.report.results)):
            return
        self._current_result_index = row
        r = self.report.results[row]

        # Update Detail Card
        self.detail_title.setText(f"Candidate Evaluation: {r.formula} ({r.molecule_id})")
        z_str = f"{r.runs_test_z:.2f}" if r.runs_test_z is not None else "N/A"
        details = (
            f"<b>Screening Outcome:</b> {r.outcome}<br>"
            f"<b>Basis:</b> {r.outcome_reason}<br>"
            f"<b>Evaluated Coverage:</b> {r.evaluated_wavelength_range_um[0]:.3f} – {r.evaluated_wavelength_range_um[1]:.3f} µm "
            f"({r.evaluated_points_count}/{r.total_observation_points} points, {r.coverage_fraction*100:.1f}% of spectrum)<br>"
            f"<b>Metrics:</b> ΔRMS = {r.delta_rms:+.5g} ({r.rms_improvement_percent:+.2f}%), Δχ² = {r.delta_chi2:+.1f}, Reduced χ² = {r.reduced_chi2:.2f}<br>"
            f"<b>Residual Structure (Runs Test):</b> Z = {z_str}; {r.runs_test_interpretation}<br>"
            f"<b>Multi-Band Consistency:</b> {r.multi_band_consistency}<br>"
        )
        if r.competing_alternatives:
            details += f"<b>Competing Alternatives:</b> {', '.join(r.competing_alternatives)}<br>"
        if r.distinguishing_bands:
            details += "<b>Distinguishing Bands:</b><br>"
            for db in r.distinguishing_bands:
                details += f"  • {db.band_min_um:.2f}–{db.band_max_um:.2f} µm: {db.explanation}<br>"

        self.detail_text.setHtml(details)

        # Update Plot
        self._plot_candidate_fit(r)

    def _plot_candidate_fit(self, r: CandidateScreeningResult) -> None:
        self.plot_widget.clear()
        self.plot_widget.addLegend(offset=(10, 10))

        obs_coords = np.asarray(self.report.pool.observation_domain_um)

        # Plot 1: Baseline model
        if r.baseline_model_curve:
            base_x = np.array([pt[0] for pt in r.baseline_model_curve])
            base_y = np.array([pt[1] for pt in r.baseline_model_curve])
            self.plot_widget.plot(
                base_x,
                base_y,
                pen=pg.mkPen(color="#06b6d4", width=2, style=Qt.DashLine),
                name="Continuum Baseline",
            )

        # Plot 2: Candidate Model
        if r.candidate_model_curve:
            cand_x = np.array([pt[0] for pt in r.candidate_model_curve])
            cand_y = np.array([pt[1] for pt in r.candidate_model_curve])
            c_color = MOLECULE_COLORS.get(r.formula, "#f97316")
            self.plot_widget.plot(
                cand_x,
                cand_y,
                pen=pg.mkPen(color=c_color, width=2.5),
                name=f"Candidate Model ({r.formula})",
            )

        # Plot 3: Observation Points and Error Bars
        if r.observed_curve:
            obs_x = np.array([pt[0] for pt in r.observed_curve], dtype=float)
            obs_y = np.array([pt[1] for pt in r.observed_curve], dtype=float)
            obs_err = np.array([pt[2] for pt in r.observed_curve], dtype=float)

            # Error bars
            if np.any(obs_err > 0):
                err_item = pg.ErrorBarItem(
                    x=obs_x,
                    y=obs_y,
                    top=obs_err,
                    bottom=obs_err,
                    beam=0.005,
                    pen=pg.mkPen(color="#94a3b8", width=1),
                )
                self.plot_widget.addItem(err_item)

            self.plot_widget.plot(
                obs_x,
                obs_y,
                pen=None,
                symbol="o",
                symbolSize=5,
                symbolBrush="#f1f5f9",
                symbolPen="#64748b",
                name=f"Observation ({self.report.target_id})",
            )

    def _populate_pool_table(self) -> None:
        self.pool_table.setRowCount(0)
        for i, entry in enumerate(self.pool.all_entries):
            self.pool_table.insertRow(i)

            # Molecule
            mol_item = QTableWidgetItem(entry.molecule_id)
            mol_item.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.pool_table.setItem(i, 0, mol_item)

            # Status
            status_item = QTableWidgetItem(entry.status.replace("_", " ").title())
            if entry.status == "searchable":
                status_item.setForeground(QColor("#4ade80"))
            elif entry.status == "partial_coverage":
                status_item.setForeground(QColor("#facc15"))
            elif entry.status == "unavailable_data":
                status_item.setForeground(QColor("#38bdf8"))
            else:
                status_item.setForeground(QColor("#94a3b8"))
            self.pool_table.setItem(i, 1, status_item)

            # Wavelength Range
            if entry.wavelength_range_um:
                w_str = f"{entry.wavelength_range_um[0]:.2f} – {entry.wavelength_range_um[1]:.2f} µm"
            else:
                w_str = "Unavailable in cache"
            self.pool_table.setItem(i, 2, QTableWidgetItem(w_str))

            # Reference source
            self.pool_table.setItem(i, 3, QTableWidgetItem(entry.source_type))

            # Reason
            self.pool_table.setItem(i, 4, QTableWidgetItem(entry.status_reason))

    def _filter_pool_table(self) -> None:
        cat_mode = self.pool_category_combo.currentText()
        query = self.pool_search_edit.text().strip().lower()

        for i in range(self.pool_table.rowCount()):
            mol_text = self.pool_table.item(i, 0).text().lower()
            status_text = self.pool_table.item(i, 1).text().lower()

            matches_cat = True
            if "searchable" in cat_mode.lower():
                matches_cat = ("searchable" in status_text)
            elif "partial" in cat_mode.lower():
                matches_cat = ("partial" in status_text)
            elif "unavailable" in cat_mode.lower():
                matches_cat = ("unavailable" in status_text)
            elif "incompatible" in cat_mode.lower():
                matches_cat = ("incompatible" in status_text)

            matches_query = (not query) or (query in mol_text)
            self.pool_table.setRowHidden(i, not (matches_cat and matches_query))

    def _apply_selected_candidates(self) -> None:
        """Transfer selected candidate molecules to the parent Atmospheric Analysis workspace."""
        selected_species: list[str] = []
        for i in range(self.results_table.rowCount()):
            if self.results_table.item(i, 0).checkState() == Qt.Checked:
                r = self.report.results[i]
                if r.formula not in selected_species:
                    selected_species.append(r.formula)

        if not selected_species:
            QMessageBox.information(
                self,
                "No Candidates Selected",
                "Please check at least one candidate molecule in the 'Follow-up' column to apply.",
            )
            return

        self.candidates_applied.emit(selected_species)
        QMessageBox.information(
            self,
            "Candidates Applied",
            f"Successfully applied candidate species: {', '.join(selected_species)} to Atmospheric Model configuration.\n\n"
            "You can now adjust mixing ratios, cloud decks, or run forward modelling in Step 3.",
        )
        self.accept()

    def _export_manifest(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Candidate Screening Manifest",
            f"screening_manifest_{self.report.target_id.replace(' ', '_')}.json",
            "JSON Manifest (*.json);;Markdown Report (*.md)",
        )
        if not path:
            return

        try:
            p = Path(path)
            if p.suffix.lower() == ".md":
                md_content = self.report.export_markdown_report()
                p.write_text(md_content, encoding="utf-8")
            else:
                data = self.report.export_manifest()
                p.write_text(json.dumps(data, indent=2), encoding="utf-8")
            QMessageBox.information(self, "Export Complete", f"Screening manifest exported to:\n{p}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save manifest: {e}")

    def _export_pool_inventory(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Reference Library Pool Inventory",
            f"candidate_pool_inventory_{self.report.target_id.replace(' ', '_')}.json",
            "JSON File (*.json)",
        )
        if not path:
            return

        try:
            inv = self.pool.export_inventory()
            Path(path).write_text(json.dumps(inv, indent=2), encoding="utf-8")
            QMessageBox.information(self, "Export Complete", f"Pool inventory exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save pool inventory: {e}")
