"""Runs & Reports workspace for ECAS.

Provides a dedicated workspace for managing analysis job lifecycles, monitoring
background tasks, cooperatively cancelling runs, resuming validated checkpoints,
and exporting human-readable reports and machine-readable analysis manifests.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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


class RunsReportsWorkspacePage(QWidget):
    """First-class workspace for monitoring analysis jobs and exporting reproducible reports."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.jobs: list[AnalysisJob] = []
        self._current_job_index = 0

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header Card
        header = QFrame()
        header.setStyleSheet(
            "background-color: #242933; border: 1px solid #3b4252; border-radius: 6px; padding: 8px;"
        )
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(8, 6, 8, 6)

        title = QLabel("<b>Runs & Reports — Analysis Lifecycle & Reproducible Reporting</b>")
        title.setStyleSheet("color: #88c0d0; font-size: 14pt; font-weight: 600;")
        h_layout.addWidget(title)

        desc = QLabel(
            "Monitor background atmospheric retrievals and forward modeling jobs, manage cooperative cancellations, "
            "resume computational checkpoints, and export tamper-evident scientific reports with cryptographic provenance.<br/>"
            "• <b>Human-Readable Report (Markdown / HTML):</b> Narrative summary of observation, readiness, parameters, and results for papers and lab records.<br/>"
            "• <b>Machine-Readable Manifest (JSON):</b> Cryptographically verifiable record containing raw input SHA-256 hashes, exact parameter definitions, and reproduction code."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #d8dee9; font-size: 10pt; line-height: 1.3;")
        h_layout.addWidget(desc)
        layout.addWidget(header)

        # Splitter: Jobs Table (top) + Report Preview & Controls (bottom)
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top: Jobs Table
        table_container = QWidget()
        t_layout = QVBoxLayout(table_container)
        t_layout.setContentsMargins(0, 0, 0, 0)
        t_layout.setSpacing(6)

        table_header = QHBoxLayout()
        table_header.addWidget(QLabel("<b>Analysis Jobs & Execution Queue:</b>"))
        self.refresh_btn = QPushButton("🔄 Refresh Queue")
        self.refresh_btn.clicked.connect(self._populate_jobs_table)
        table_header.addWidget(self.refresh_btn)
        table_header.addStretch(1)

        self.cancel_btn = QPushButton("🛑 Cancel Run")
        self.cancel_btn.setToolTip("Request cooperative cancellation of the selected active job.")
        self.cancel_btn.clicked.connect(self._cancel_selected_job)
        self.resume_btn = QPushButton("▶ Validate & Resume Checkpoint…")
        self.resume_btn.setToolTip("Validate cryptographic SHA-256 hashes and software environment to continue interrupted state.")
        self.resume_btn.clicked.connect(self._resume_selected_job)

        table_header.addWidget(self.cancel_btn)
        table_header.addWidget(self.resume_btn)
        t_layout.addLayout(table_header)

        self.jobs_table = QTableWidget(0, 7)
        self.jobs_table.setHorizontalHeaderLabels([
            "Job ID", "Name", "Type", "Target", "Status", "Progress", "Can Resume"
        ])
        self.jobs_table.horizontalHeader().setStretchLastSection(True)
        self.jobs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.jobs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.jobs_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.jobs_table.verticalHeader().setVisible(False)
        self.jobs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.jobs_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.jobs_table.itemSelectionChanged.connect(self._on_job_selection_changed)
        self.jobs_table.setStyleSheet("font-size: 11px;")
        t_layout.addWidget(self.jobs_table)

        splitter.addWidget(table_container)

        # Bottom: Report Preview & Export Controls
        preview_container = QWidget()
        p_layout = QVBoxLayout(preview_container)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.setSpacing(6)

        prev_header = QHBoxLayout()
        prev_header.addWidget(QLabel("<b>Reproducible Analysis Report Preview:</b>"))
        prev_header.addStretch(1)

        self.export_md_btn = QPushButton("📄 Export Report (Markdown)…")
        self.export_md_btn.setStyleSheet(
            "QPushButton { background-color: #5e81ac; color: white; font-weight: bold; padding: 5px 12px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #81a1c1; }"
        )
        self.export_md_btn.clicked.connect(self._export_markdown_report)

        self.export_html_btn = QPushButton("🌐 Export Report (HTML)…")
        self.export_html_btn.clicked.connect(self._export_html_report)

        self.export_json_btn = QPushButton("💾 Export Manifest (JSON)…")
        self.export_json_btn.clicked.connect(self._export_json_manifest)

        prev_header.addWidget(self.export_md_btn)
        prev_header.addWidget(self.export_html_btn)
        prev_header.addWidget(self.export_json_btn)
        p_layout.addLayout(prev_header)

        self.report_preview = QTextEdit()
        self.report_preview.setReadOnly(True)
        self.report_preview.setStyleSheet(
            "background-color: #1e222a; font-family: Consolas, monospace; font-size: 11px; padding: 6px;"
        )
        p_layout.addWidget(self.report_preview)

        splitter.addWidget(preview_container)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)

        self._populate_jobs_table()
        self._update_preview()

    def set_jobs(self, jobs: Sequence[AnalysisJob]) -> None:
        """Update jobs collection from the application coordinator."""
        self.jobs = list(jobs)
        self._populate_jobs_table()
        self._update_preview()

    def _populate_jobs_table(self) -> None:
        self.jobs_table.setRowCount(0)
        if not self.jobs:
            self.jobs_table.setRowCount(1)
            item = QTableWidgetItem("No analysis jobs have run in this session. Configure and run a model in Atmospheric Analysis.")
            item.setForeground(Qt.GlobalColor.gray)
            self.jobs_table.setItem(0, 1, item)
            self.cancel_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            return

        self.jobs_table.setRowCount(len(self.jobs))
        for r_idx, job in enumerate(self.jobs):
            id_item = QTableWidgetItem(job.job_id)
            name_item = QTableWidgetItem(job.name)
            type_item = QTableWidgetItem(job.job_type)
            target_item = QTableWidgetItem(job.target_name or "Unknown")
            status_item = QTableWidgetItem(job.status.name)
            prog_item = QTableWidgetItem(f"{job.progress_percent:.0f}% ({job.progress_message})")
            resume_item = QTableWidgetItem("Yes" if job.can_resume() else "No")

            if job.status == JobStatus.RUNNING:
                status_item.setForeground(Qt.GlobalColor.cyan)
            elif job.status == JobStatus.COMPLETED:
                status_item.setForeground(Qt.GlobalColor.green)
            elif job.status == JobStatus.FAILED:
                status_item.setForeground(Qt.GlobalColor.red)
            elif job.status == JobStatus.CANCELLED:
                status_item.setForeground(Qt.GlobalColor.yellow)

            self.jobs_table.setItem(r_idx, 0, id_item)
            self.jobs_table.setItem(r_idx, 1, name_item)
            self.jobs_table.setItem(r_idx, 2, type_item)
            self.jobs_table.setItem(r_idx, 3, target_item)
            self.jobs_table.setItem(r_idx, 4, status_item)
            self.jobs_table.setItem(r_idx, 5, prog_item)
            self.jobs_table.setItem(r_idx, 6, resume_item)

        if self._current_job_index < len(self.jobs):
            self.jobs_table.selectRow(self._current_job_index)

    def _on_job_selection_changed(self) -> None:
        selected_rows = self.jobs_table.selectionModel().selectedRows()
        if selected_rows:
            self._current_job_index = selected_rows[0].row()
            self._update_preview()

    def _selected_job(self) -> AnalysisJob | None:
        if 0 <= self._current_job_index < len(self.jobs):
            return self.jobs[self._current_job_index]
        return None

    def _update_preview(self) -> None:
        job = self._selected_job()
        if job is None:
            self.report_preview.setPlainText(
                "=== NO ACTIVE ANALYSIS JOB SELECTED ===\n\n"
                "To generate reports or analysis manifests:\n"
                "1. Switch to 'Atmospheric Analysis' in the left menu.\n"
                "2. Choose an observation and configure an atmospheric forward model.\n"
                "3. Click 'Run Atmospheric Model & Compare'.\n"
                "4. Return to 'Runs & Reports' to monitor progress, resume checkpoints, and export results.\n\n"
                "Report Types:\n"
                "• Markdown / HTML: Formatted for human reading, citations, and publication supplements.\n"
                "• JSON Manifest: Cryptographic manifest compliant with ecas-analysis-manifest-v1 for exact machine reproduction."
            )
            self.export_md_btn.setEnabled(False)
            self.export_html_btn.setEnabled(False)
            self.export_json_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.resume_btn.setEnabled(False)
            return

        self.cancel_btn.setEnabled(job.status in (JobStatus.QUEUED, JobStatus.RUNNING))
        self.resume_btn.setEnabled(job.can_resume())
        self.export_md_btn.setEnabled(True)
        self.export_html_btn.setEnabled(True)
        self.export_json_btn.setEnabled(True)

        report = generate_analysis_report(job, format="markdown")
        self.report_preview.setPlainText(report)

    def _cancel_selected_job(self) -> None:
        job = self._selected_job()
        if job:
            job.cancel()
            self._populate_jobs_table()
            self._update_preview()
            QMessageBox.information(self, "Cancellation Requested", f"Cooperative cancellation signaled for job {job.job_id}.")

    def _resume_selected_job(self) -> None:
        job = self._selected_job()
        if not job or not job.checkpoint_data:
            QMessageBox.warning(self, "Cannot Resume", "Selected job does not have valid checkpoint data to resume.")
            return

        resumable, reason = validate_checkpoint_resumability(
            job.checkpoint_data,
            current_input_sha256=job.checkpoint_data.get("input_sha256", ""),
            current_software_version=job.checkpoint_data.get("software_version", "1.0.0"),
            current_model_settings=job.checkpoint_data.get("model_settings", {}),
            current_parameter_bounds=job.checkpoint_data.get("parameter_bounds", {}),
        )
        if resumable:
            QMessageBox.information(self, "Checkpoint Valid", f"Checkpoint verified! Ready to resume: {reason}")
        else:
            QMessageBox.warning(self, "Resume Rejected", f"Checkpoint resumption rejected: {reason}")

    def _export_markdown_report(self) -> None:
        job = self._selected_job()
        if not job:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Analysis Report (Markdown)", f"ecas_report_{job.job_id}.md", "Markdown (*.md)")
        if path:
            report = generate_analysis_report(job, format="markdown")
            Path(path).write_text(report, encoding="utf-8")
            QMessageBox.information(self, "Export Complete", f"Report saved to:\n{path}")

    def _export_html_report(self) -> None:
        job = self._selected_job()
        if not job:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Analysis Report (HTML)", f"ecas_report_{job.job_id}.html", "HTML (*.html)")
        if path:
            report = generate_analysis_report(job, format="html")
            Path(path).write_text(report, encoding="utf-8")
            QMessageBox.information(self, "Export Complete", f"Report saved to:\n{path}")

    def _export_json_manifest(self) -> None:
        job = self._selected_job()
        if not job:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Machine-Readable Manifest (JSON)", f"ecas_manifest_{job.job_id}.json", "JSON (*.json)")
        if path:
            manifest = generate_analysis_manifest(job)
            Path(path).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            QMessageBox.information(self, "Export Complete", f"Manifest saved to:\n{path}")

