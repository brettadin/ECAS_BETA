"""Unit tests for reproducible scientific reporting and analysis manifests."""
import json
import pytest

from ecas.analysis.jobs import AnalysisJob
from ecas.analysis.reports import (
    REPORT_SCHEMA_VERSION,
    generate_analysis_manifest,
    generate_analysis_report,
)


class TestReproducibleReporting:
    def test_generate_analysis_manifest(self):
        job = AnalysisJob(
            job_id="wasp39b_run_01",
            name="WASP-39 b NIRSpec Atmospheric Model Analysis",
            job_type="forward_model_sweep",
            target_id="WASP-39 b",
            input_hashes={"wasp39b_feinstein.csv": "c" * 64},
            config={
                "planet_preset_id": "wasp-39b",
                "temperature_k": 1166.0,
                "citation": "Feinstein et al. (2023, Nature 614, 670)",
                "opacity_sources": [{"formula": "H2O", "dataset": "POKAZATEL", "source_sha256": "d" * 64}],
            },
            results={"completed": {"wasp39b_feinstein.csv": {"rms": 0.015}}},
        )

        manifest = generate_analysis_manifest(job)
        assert manifest["$schema"] == REPORT_SCHEMA_VERSION
        assert manifest["job_id"] == "wasp39b_run_01"
        assert len(manifest["input_products"]) == 1
        assert manifest["input_products"][0]["sha256"] == "c" * 64
        assert "Feinstein et al." in manifest["input_products"][0]["citation"]
        assert len(manifest["limitations"]) >= 3
        assert "python -m ecas.reproduce" in manifest["reproduction_command"]

        # Ensure JSON-serializable
        encoded = json.dumps(manifest)
        assert len(encoded) > 0

    def test_generate_markdown_report_contains_all_sections(self):
        job = AnalysisJob(
            job_id="job_report_01",
            name="Laboratory Identification Report",
            job_type="laboratory_fit",
            target_id="CO2 Gas Cell Sample",
            input_hashes={"co2_lab.jdx": "e" * 64},
            config={
                "engine": "ECAS-DropOneBVLS",
                "engine_version": "1.0",
                "threshold": 3.0,
            },
        )

        report_md = generate_analysis_report(job, format="markdown")
        assert "# ECAS Scientific Analysis Report" in report_md
        assert "## 1. Executive Summary" in report_md
        assert "## 2. Software & Computing Environment" in report_md
        assert "## 3. Input Products & Cryptographic Provenance" in report_md
        assert "## 4. Analysis Readiness Assessment" in report_md
        assert "## 5. Data Transformations & Exclusions" in report_md
        assert "## 6. Forward Model & Opacity Specifications" in report_md
        assert "## 7. Model Parameters & Noise Assumptions" in report_md
        assert "## 8. Statistical Fit Diagnostics" in report_md
        assert "## 9. Stated Scientific Limitations" in report_md
        assert "## 10. Instructions for Deterministic Reproduction" in report_md

    def test_generate_html_report(self):
        job = AnalysisJob(
            job_id="job_html_01",
            name="HTML Analysis Report",
            job_type="atmospheric_retrieval",
            target_id="WASP-39 b",
        )
        report_html = generate_analysis_report(job, format="html")
        assert "<!DOCTYPE html>" in report_html
        assert "<title>HTML Analysis Report</title>" in report_html

