"""Interactive analysis job management and reproducible report export dialog.

Enables researchers to monitor background analysis jobs, cancel long-running
jobs cooperatively, resume validated checkpoints, and export comprehensive
Markdown/HTML reports and JSON reproducibility manifests.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from PySide6.QtCore import Qt
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

from ecas.analysis.jobs import (
    AnalysisJob,
    JobStatus,
    validate_checkpoint_resumability,
)
from ecas.analysis.reports import (
    generate_analysis_manifest,
    generate_analysis_report,
)


class JobManagerDialog(QDialog):
    """Dialog for inspecting jobs, resuming checkpoints, and exporting reports."""

    def __init__(
        self,
        jobs: Sequence[AnalysisJob],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Analysis Jobs & Reproducible Reporting — ECAS")
        self.resize(980, 680)

        self.jobs = list(jobs)
        self._current_job_index = 0

        self._setup_ui()
        self._populate_jobs_table()
        self._update_preview()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # Header card
        header = QFrame()
        header.setStyleSheet("background-color: #242933; border: 1px solid #434c5e; border-radius: 4px; padding: 6px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel("<b>Shared Analysis Job Lifecycle & Reproducible Reporting</b>")
        title.setStyleSheet("color: #88c0d0; font-size: 12px;")
        desc = QLabel(
            "Track background analysis jobs, manage cooperative cancellations and checkpointed resumptions, "
            "and generate tamper-evident scientific reports with cryptographic provenance and citations."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #d8dee9; font-size: 10.5px;")
        h_layout.addWidget(title)
        h_layout.addWidget(desc)
        main_layout.addWidget(header)

        # Splitter: Jobs Table (top) + Report Preview & Controls (bottom)
        splitter = QSplitter(Qt.Vertical)

        # Top: Jobs Table
        table_container = QWidget()
        t_layout = QVBoxLayout(table_container)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(4)

        t_layout.addWidget(QLabel("<b>Analysis Jobs:</b>"))
        self.jobs_table = QTableWidget(0, 7)
        self.jobs_table.setHorizontalHeaderLabels([
            "Job ID", "Name", "Type", "Target", "Status", "Progress", "Can Resume"
        ])
        self.jobs_table.horizontalHeader().setStretchLastSection(True)
        self.jobs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.jobs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.jobs_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.jobs_table.verticalHeader().setVisible(False)
        self.jobs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.jobs_table.setSelectionMode(QTableWidget.SingleSelection)
        self.jobs_table.itemSelectionChanged.connect(self._on_job_selection_changed)
        self.jobs_table.setStyleSheet("font-size: 11px;")
        t_layout.addWidget(self.jobs_table)

        # Job Actions Row
        job_btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel Job")
        self.cancel_btn.clicked.connect(self._cancel_selected_job)
        self.resume_btn = QPushButton("Validate & Resume Checkpoint...")
        self.resume_btn.clicked.connect(self._resume_selected_job)
        job_btn_row.addWidget(self.cancel_btn)
        job_btn_row.addWidget(self.resume_btn)
        job_btn_row.addStretch(1)
        t_layout.addLayout(job_btn_row)

        splitter.addWidget(table_container)

        # Bottom: Report Preview & Export Controls
        preview_container = QWidget()
        p_layout = QVBoxLayout(preview_container)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.setSpacing(4)

        prev_header = QHBoxLayout()
        prev_header.addWidget(QLabel("<b>Reproducible Analysis Report Preview:</b>"))
        prev_header.addStretch(1)

        self.export_md_btn = QPushButton("📄 Export Report (Markdown)...")
        self.export_md_btn.clicked.connect(self._export_markdown_report)
        self.export_html_btn = QPushButton("🌐 Export Report (HTML)...")
        self.export_html_btn.clicked.connect(self._export_html_report)
        self.export_json_btn = QPushButton("💾 Export Manifest (JSON)...")
        self.export_json_btn.clicked.connect(self._export_json_manifest)

        prev_header.addWidget(self.export_md_btn)
        prev_header.addWidget(self.export_html_btn)
        prev_header.addWidget(self.export_json_btn)
        p_layout.addLayout(prev_header)

        self.report_preview = QTextEdit()
        self.report_preview.setReadOnly(True)
        self.report_preview.setStyleSheet("background-color: #1e222a; font-family: monospace; font-size: 11px; padding: 6px;")
        p_layout.addWidget(self.report_preview)

        splitter.addWidget(preview_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter, 1)

        # Bottom Close Row
        close_row = QHBoxLayout()
        close_row.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_row.addWidget(close_btn)
        main_layout.addLayout(close_row)

    def _populate_jobs_table(self) -> None:
        self.jobs_table.setRowCount(len(self.jobs))
        for row, j in enumerate(self.jobs):
            self.jobs_table.setItem(row, 0, QTableWidgetItem(j.job_id[:12]))
            self.jobs_table.setItem(row, 1, QTableWidgetItem(j.name))
            self.jobs_table.setItem(row, 2, QTableWidgetItem(j.job_type))
            self.jobs_table.setItem(row, 3, QTableWidgetItem(j.target_id))

            status_item = QTableWidgetItem(j.status.value)
            if j.status == JobStatus.COMPLETED:
                status_item.setForeground(Qt.GlobalColor.green)
            elif j.status == JobStatus.RUNNING:
                status_item.setForeground(Qt.GlobalColor.cyan)
            elif j.status in (JobStatus.CANCELLED, JobStatus.FAILED):
                status_item.setForeground(Qt.GlobalColor.yellow)
            self.jobs_table.setItem(row, 4, status_item)

            self.jobs_table.setItem(row, 5, QTableWidgetItem(f"{j.progress_percent:.0f}% ({j.progress_message})"))
            self.jobs_table.setItem(row, 6, QTableWidgetItem("Yes" if j.can_resume else "No"))

        if self.jobs:
            self.jobs_table.selectRow(self._current_job_index)

    def _on_job_selection_changed(self) -> None:
        selected_rows = self.jobs_table.selectionModel().selectedRows()
        if selected_rows:
            self._current_job_index = selected_rows[0].row()
            self._update_preview()

    def _update_preview(self) -> None:
        if not self.jobs:
            self.report_preview.setPlainText("No jobs available.")
            return

        job = self.jobs[self._current_job_index]
        self.cancel_btn.setEnabled(job.status == JobStatus.RUNNING)
        self.resume_btn.setEnabled(job.can_resume)

        report_md = generate_analysis_report(job, format="markdown")
        self.report_preview.setPlainText(report_md)

    def _cancel_selected_job(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self._current_job_index]
        if job.status == JobStatus.RUNNING:
            job.status = JobStatus.CANCELLED
            job.progress_message = "Cancelled by user."
            self._populate_jobs_table()
            self._update_preview()

    def _resume_selected_job(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self._current_job_index]
        valid, msg = validate_checkpoint_resumability(job, job.input_hashes, job.config)
        if valid:
            QMessageBox.information(
                self,
                "Checkpoint Validated",
                f"Resumption Approved: {msg}\nJob can resume from last checkpoint.",
            )
        else:
            QMessageBox.warning(
                self,
                "Resumption Rejected",
                f"Cannot Resume Checkpoint: {msg}",
            )

    def _export_markdown_report(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self._current_job_index]
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Analysis Report (Markdown)", f"report_{job.job_id}.md", "Markdown (*.md);;All Files (*)"
        )
        if path:
            report_md = generate_analysis_report(job, format="markdown")
            Path(path).write_text(report_md, encoding="utf-8")
            QMessageBox.information(self, "Report Exported", f"Saved Markdown report to {path}")

    def _export_html_report(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self._current_job_index]
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Analysis Report (HTML)", f"report_{job.job_id}.html", "HTML (*.html);;All Files (*)"
        )
        if path:
            report_html = generate_analysis_report(job, format="html")
            Path(path).write_text(report_html, encoding="utf-8")
            QMessageBox.information(self, "Report Exported", f"Saved HTML report to {path}")

    def _export_json_manifest(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self._current_job_index]
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Analysis Manifest (JSON)", f"manifest_{job.job_id}.json", "JSON (*.json);;All Files (*)"
        )
        if path:
            manifest = generate_analysis_manifest(job)
            Path(path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            QMessageBox.information(self, "Manifest Exported", f"Saved JSON reproducibility manifest to {path}")

