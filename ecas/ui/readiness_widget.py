"""Reusable scientific analysis readiness UI widget for ECAS.

Renders visible, actionable readiness summaries for spectral operations:
- READY (green)
- READY_WITH_LIMITATIONS (amber)
- BLOCKED (crimson)

Provides progressive disclosure of missing metadata, incompatible parameters,
and physical model limitations with explicit actionable guidance.
"""
from __future__ import annotations

from typing import cast
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ecas.analysis.readiness import ReadinessIssue, ReadinessReport, ReadinessStatus


class ReadinessBannerWidget(QFrame):
    """Visible banner displaying analysis readiness and actionable issue list."""

    action_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self._current_report: ReadinessReport | None = None
        self._expanded = False

        self._setup_ui()
        self.setVisible(False)

    def _setup_ui(self) -> None:
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(10, 8, 10, 8)
        self._main_layout.setSpacing(6)

        # Header row
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)

        self.status_badge = QLabel("READY")
        self.status_badge.setStyleSheet(
            "font-weight: bold; padding: 3px 8px; border-radius: 3px; font-size: 11px;"
        )
        header_row.addWidget(self.status_badge)

        self.summary_label = QLabel("Readiness assessment")
        self.summary_label.setStyleSheet("font-weight: 500; font-size: 12px;")
        header_row.addWidget(self.summary_label, 1)

        self.toggle_details_btn = QPushButton("View Details (0)")
        self.toggle_details_btn.setStyleSheet(
            "padding: 3px 10px; font-size: 11px; background-color: #31363b; border: 1px solid #4f5b66; border-radius: 3px;"
        )
        self.toggle_details_btn.clicked.connect(self._toggle_expanded)
        header_row.addWidget(self.toggle_details_btn)

        self._main_layout.addLayout(header_row)

        # Issues details table (expandable)
        self.details_table = QTableWidget(0, 4)
        self.details_table.setHorizontalHeaderLabels(["Type", "Issue", "Scientific Consequence", "Action"])
        self.details_table.horizontalHeader().setStretchLastSection(True)
        self.details_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.details_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.details_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.details_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.details_table.setStyleSheet(
            "QTableWidget { background-color: #1e2124; border: 1px solid #3e444c; border-radius: 3px; font-size: 11px; } "
            "QHeaderView::section { background-color: #2b3036; padding: 4px; font-weight: bold; border: none; }"
        )
        self.details_table.setMaximumHeight(160)
        self.details_table.setVisible(False)
        self._main_layout.addWidget(self.details_table)

    def set_report(self, report: ReadinessReport | None) -> None:
        """Update widget with a new analysis readiness report."""
        self._current_report = report
        if report is None:
            self.setVisible(False)
            return

        self.setVisible(True)
        status = report.status
        issue_count = len(report.issues)

        # Style by outcome
        if status == ReadinessStatus.READY:
            self.setStyleSheet(
                "ReadinessBannerWidget { background-color: #18281b; border: 1px solid #2e7d32; border-radius: 4px; }"
            )
            self.status_badge.setText("READY")
            self.status_badge.setStyleSheet(
                "background-color: #2e7d32; color: #ffffff; font-weight: bold; padding: 3px 8px; border-radius: 3px; font-size: 11px;"
            )
            self.summary_label.setText(
                f"<b>Ready for {report.operation}:</b> All requirements verified without blocking issues."
            )
        elif status == ReadinessStatus.READY_WITH_LIMITATIONS:
            self.setStyleSheet(
                "ReadinessBannerWidget { background-color: #2e2614; border: 1px solid #f57f17; border-radius: 4px; }"
            )
            self.status_badge.setText("READY WITH LIMITATIONS")
            self.status_badge.setStyleSheet(
                "background-color: #f57f17; color: #ffffff; font-weight: bold; padding: 3px 8px; border-radius: 3px; font-size: 11px;"
            )
            self.summary_label.setText(
                f"<b>Ready with stated limitations ({report.operation}):</b> {len(report.limitation_issues)} observational or physical limitation(s) apply."
            )
        else:  # BLOCKED
            self.setStyleSheet(
                "ReadinessBannerWidget { background-color: #2e1818; border: 1px solid #c62828; border-radius: 4px; }"
            )
            self.status_badge.setText("BLOCKED")
            self.status_badge.setStyleSheet(
                "background-color: #c62828; color: #ffffff; font-weight: bold; padding: 3px 8px; border-radius: 3px; font-size: 11px;"
            )
            missing_count = len(report.missing_issues)
            incompat_count = len(report.incompatible_issues)
            reasons = []
            if missing_count:
                reasons.append(f"{missing_count} missing requirement(s)")
            if incompat_count:
                reasons.append(f"{incompat_count} incompatible setting(s)")
            self.summary_label.setText(
                f"<b>Blocked ({report.operation}):</b> Action required before analysis ({', '.join(reasons)})."
            )

        self.toggle_details_btn.setText(f"View Issues & Details ({issue_count})" if not self._expanded else f"Hide Details ({issue_count})")
        self._populate_issues_table(report.issues)

    def _populate_issues_table(self, issues: tuple[ReadinessIssue, ...]) -> None:
        self.details_table.setRowCount(len(issues))
        for row, issue in enumerate(issues):
            cat_item = QTableWidgetItem(issue.category.upper())
            if issue.category in ("missing", "incompatible"):
                cat_item.setForeground(Qt.GlobalColor.red)
            else:
                cat_item.setForeground(Qt.GlobalColor.yellow)

            title_item = QTableWidgetItem(issue.title)
            cons_item = QTableWidgetItem(issue.consequence)
            act_item = QTableWidgetItem(issue.action)

            self.details_table.setItem(row, 0, cat_item)
            self.details_table.setItem(row, 1, title_item)
            self.details_table.setItem(row, 2, cons_item)
            self.details_table.setItem(row, 3, act_item)

    def _toggle_expanded(self) -> None:
        self._expanded = not self._expanded
        self.details_table.setVisible(self._expanded)
        count = len(self._current_report.issues) if self._current_report else 0
        self.toggle_details_btn.setText(f"Hide Details ({count})" if self._expanded else f"View Issues & Details ({count})")

