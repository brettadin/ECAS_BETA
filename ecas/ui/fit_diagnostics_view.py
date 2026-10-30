"""Interactive fit and retrieval diagnostics dialog with progressive disclosure.

Renders statistical diagnostics (convergence, parameters at bounds, Wald-Wolfowitz runs,
lag-1 autocorrelation, reduced chi-squared, condition numbers) with plain-language
explanations, mathematical definitions, and formal retrieval backend contracts.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ecas.comparison.diagnostics import ComprehensiveFitDiagnostics


class FitDiagnosticsDialog(QDialog):
    """Dialog for comprehensive fit and retrieval diagnostics with progressive disclosure."""

    def __init__(
        self,
        diagnostics: ComprehensiveFitDiagnostics,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Fit Diagnostics — {diagnostics.fit_name}")
        self.resize(860, 640)

        self.diag = diagnostics
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Plain-Language Executive Summary
        summary_card = QFrame()
        summary_card.setStyleSheet("background-color: #242933; border: 1px solid #434c5e; border-radius: 4px; padding: 8px;")
        s_layout = QVBoxLayout(summary_card)
        s_layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel(f"<b>Statistical Fit Assessment: {self.diag.fit_name}</b>")
        title.setStyleSheet("color: #88c0d0; font-size: 12px;")
        desc = QLabel(self.diag.plain_language_summary)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #eceff4; font-size: 11px; line-height: 1.4;")
        s_layout.addWidget(title)
        s_layout.addWidget(desc)
        main_layout.addWidget(summary_card)

        # 2. Main Tabs
        tabs = QTabWidget()

        # Tab 1: Detailed Statistical Metrics
        tab_stats = QWidget()
        ts_layout = QVBoxLayout(tab_stats)
        ts_layout.setContentsMargins(4, 4, 4, 4)

        metrics_table = QTableWidget(0, 3)
        metrics_table.setHorizontalHeaderLabels(["Metric", "Value", "Scientific Interpretation"])
        metrics_table.horizontalHeader().setStretchLastSection(True)
        metrics_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        metrics_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        metrics_table.verticalHeader().setVisible(False)
        metrics_table.setStyleSheet("font-size: 11px;")

        rs = self.diag.residual_structure
        ss = self.diag.solver_status

        rows = [
            ("Solver Status", "Converged" if ss.converged else "Failed", ss.message),
            ("Parameters at Bounds", ", ".join(ss.parameters_at_bounds) if ss.parameters_at_bounds else "None", "Parameters clamped to optimization boundaries"),
            ("Uncertainty Basis", ss.uncertainty_basis, "Basis for residual weighting and chi-squared calculation"),
            ("Samples / Parameters (dof)", f"{rs.sample_count} / {rs.parameter_count} (dof={rs.degrees_of_freedom})", "Degrees of freedom available for model fit"),
            ("Raw Residual RMS", f"{rs.raw_rms:.5g}", "Root-mean-square of unweighted data-minus-model residuals"),
            ("Reduced χ_ν²", f"{rs.reduced_chi2:.2f}" if rs.reduced_chi2 is not None else "n/a", "Goodness of fit per degree of freedom (1.0 indicates consistency with 1σ errors)"),
            ("Wald-Wolfowitz Runs (Z)", f"R={rs.runs_count} (Z={rs.runs_z_score:.2f})" if rs.runs_z_score is not None else "n/a", rs.runs_interpretation),
            ("Lag-1 Autocorrelation (r_1)", f"{rs.lag1_autocorrelation:+.3f}", rs.autocorrelation_interpretation),
            ("Skewness / Excess Kurtosis", f"{rs.skewness:+.2f} / {rs.kurtosis:+.2f}", "Higher moments of standardized residuals (0/0 for Gaussian noise)"),
            ("Condition Number κ(C)", f"{rs.condition_number:.2e}" if rs.condition_number is not None else "n/a", "Ill-conditioned if κ > 1e12 (numerically unstable covariance)"),
        ]

        metrics_table.setRowCount(len(rows))
        for r_idx, (m, v, interp) in enumerate(rows):
            item_m = QTableWidgetItem(m)
            item_v = QTableWidgetItem(v)
            item_i = QTableWidgetItem(interp)
            if "Alert" in interp or "Failed" in v or "clustering" in interp.lower():
                item_v.setForeground(Qt.GlobalColor.yellow)
            metrics_table.setItem(r_idx, 0, item_m)
            metrics_table.setItem(r_idx, 1, item_v)
            metrics_table.setItem(r_idx, 2, item_i)

        ts_layout.addWidget(metrics_table)
        tabs.addTab(tab_stats, "Statistical Metrics")

        # Tab 2: Progressive Disclosure Mathematics
        tab_math = QWidget()
        tm_layout = QVBoxLayout(tab_math)
        tm_layout.setContentsMargins(6, 6, 6, 6)

        math_text = QTextEdit()
        math_text.setReadOnly(True)
        math_text.setStyleSheet("background-color: #1e222a; font-family: monospace; font-size: 11px; padding: 6px;")

        lines = ["=== MATHEMATICAL DEFINITIONS & DIAGNOSTIC FORMULAS ===\n"]
        for name, formula in self.diag.progressive_disclosure_math.items():
            lines.append(f"■ {name}:")
            lines.append(f"  {formula}\n")
        math_text.setPlainText("\n".join(lines))
        tm_layout.addWidget(math_text)
        tabs.addTab(tab_math, "Mathematical Formulas")

        # Tab 3: Retrieval Backend Interface & Scientific Boundaries
        tab_ret = QWidget()
        tr_layout = QVBoxLayout(tab_ret)
        tr_layout.setContentsMargins(6, 6, 6, 6)

        ret_text = QTextEdit()
        ret_text.setReadOnly(True)
        ret_text.setStyleSheet("background-color: #1e222a; font-family: monospace; font-size: 11px; padding: 6px;")

        contract = self.diag.retrieval_backend_contract
        r_lines = [
            f"=== RETRIEVAL BACKEND STATUS: {self.diag.retrieval_backend_status} ===\n",
            f"CRITICAL BOUNDARY NOTICE:\n{contract.get('boundary_warning', '')}\n",
            "Required AtmosphericRetrievalBackend Protocol Methods:",
        ]
        for meth in contract.get("required_backend_methods", ()):
            r_lines.append(f"  • {meth}")
        r_lines.append("\nRequired Posterior Sampling Outputs:")
        for diag in contract.get("required_posterior_diagnostics", ()):
            r_lines.append(f"  • {diag}")

        ret_text.setPlainText("\n".join(r_lines))
        tr_layout.addWidget(ret_text)
        tabs.addTab(tab_ret, "Posterior Retrieval Contract")

        main_layout.addWidget(tabs, 1)

        # Bottom row
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        main_layout.addLayout(btn_row)

