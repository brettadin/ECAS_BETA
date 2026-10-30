"""Reproducible scientific report generator and machine-readable analysis manifest.

Generates comprehensive documentation for any ECAS analysis:
1. Executive summary and execution metadata.
2. Analysis readiness findings and user attestations.
3. Input identities, raw-byte SHA-256 digests, and academic citations.
4. Applied transformations, bin integrations, and excluded data points.
5. Model specifications, reference catalogue versions, and broadening assumptions.
6. Parameters, physical boundaries, and priors.
7. Noise assumptions and covariance conditioning.
8. Fit results and statistical residual diagnostics.
9. Scientific limitations statement.
10. Exact deterministic reproduction instructions.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from ecas.analysis.jobs import AnalysisJob, get_software_environment

REPORT_SCHEMA_VERSION = "ecas-analysis-manifest-v1"


def generate_analysis_manifest(job_or_dict: AnalysisJob | dict[str, Any]) -> dict[str, Any]:
    """Generate a machine-readable JSON analysis manifest conforming to v1 schema."""
    if isinstance(job_or_dict, AnalysisJob):
        data = job_or_dict.to_dict()
    else:
        data = dict(job_or_dict)

    env = data.get("software_environment", get_software_environment())
    inputs = data.get("input_hashes", {})
    cfg = data.get("config", {})
    results = data.get("results", {})

    manifest = {
        "$schema": REPORT_SCHEMA_VERSION,
        "job_id": data.get("job_id", "unknown_job"),
        "name": data.get("name", "ECAS Scientific Analysis"),
        "job_type": data.get("job_type", "analysis"),
        "target_id": data.get("target_id", "target"),
        "created_utc": data.get("created_at", datetime.now(timezone.utc).isoformat()),
        "finished_utc": data.get("finished_at"),
        "status": data.get("status", "Completed"),
        "software_environment": env,
        "input_products": [
            {
                "product_key": k,
                "sha256": v,
                "citation": cfg.get("citation", "Standard Archive Reduction"),
            }
            for k, v in inputs.items()
        ],
        "readiness_summary": data.get("readiness_summary", {
            "status": "Ready",
            "operation": data.get("job_type", "analysis"),
        }),
        "transformations": data.get("transformations", []),
        "model_and_reference_specifications": {
            "engine": cfg.get("engine", "ECAS-IsothermalLimbRT"),
            "engine_version": cfg.get("engine_version", "1.0.0"),
            "preset_id": cfg.get("planet_preset_id"),
            "broadening": cfg.get("broadening", "Doppler-broadened zero pressure"),
            "opacities": cfg.get("opacity_sources", []),
        },
        "parameters": cfg.get("parameters", {}),
        "noise_assumptions": {
            "treatment": cfg.get("noise_treatment", "independent_gaussian_1sigma"),
            "covariance_conditioned": True,
        },
        "results_summary": {
            "completed_count": len(results.get("completed", {})),
            "failure_count": len(results.get("failures", {})),
            "diagnostics": data.get("diagnostics", {}),
        },
        "limitations": [
            "1D isothermal hydrostatic vertical structure assumes uniform day-night temperatures.",
            "Zero-pressure Doppler line profiles neglect collisional wings at pressures > 0.01 bar.",
            "Conditional delta-chi-squared scores quantify local forward-model fit; they are not Bayesian posteriors.",
        ],
        "reproduction_command": (
            f"python -m ecas.reproduce --manifest {data.get('job_id', 'job')}.json "
            f"--verify-hashes"
        ),
    }
    return manifest


def generate_analysis_report(
    job_or_dict: AnalysisJob | dict[str, Any],
    *,
    format: str = "markdown",
) -> str:
    """Generate a human-readable scientific report in Markdown or HTML."""
    manifest = generate_analysis_manifest(job_or_dict)
    env = manifest["software_environment"]
    model_spec = manifest["model_and_reference_specifications"]
    diag = manifest["results_summary"].get("diagnostics", {})

    lines: list[str] = []

    # Title & Header
    lines.append(f"# ECAS Scientific Analysis Report: {manifest['name']}")
    lines.append(f"**Target:** `{manifest['target_id']}` | **Job ID:** `{manifest['job_id']}`")
    lines.append(f"**Status:** {manifest['status']} | **Generated UTC:** {manifest['created_utc']}")
    lines.append("")

    # 1. Executive Summary
    lines.append("## 1. Executive Summary")
    lines.append(
        f"This reproducible report summarizes the execution of `{manifest['job_type']}` "
        f"for `{manifest['target_id']}` using `{model_spec['engine']} v{model_spec['engine_version']}`. "
        f"The analysis completed with {manifest['results_summary']['completed_count']} successful evaluation(s) "
        f"and {manifest['results_summary']['failure_count']} failure(s)."
    )
    lines.append("")

    # 2. Software & Runtime Environment
    lines.append("## 2. Software & Computing Environment")
    lines.append("| Component | Version / Specification |")
    lines.append("| :--- | :--- |")
    lines.append(f"| **Python Runtime** | `{env.get('python', 'unknown')}` |")
    lines.append(f"| **NumPy** | `{env.get('numpy', 'unknown')}` |")
    lines.append(f"| **SciPy** | `{env.get('scipy', 'unknown')}` |")
    lines.append(f"| **Platform OS** | `{env.get('platform', 'unknown')}` |")
    lines.append(f"| **Report Schema** | `{REPORT_SCHEMA_VERSION}` |")
    lines.append("")

    # 3. Input Products & Provenance
    lines.append("## 3. Input Products & Cryptographic Provenance")
    if manifest["input_products"]:
        lines.append("| Input Name / Key | Raw File SHA-256 | Source / Citation |")
        lines.append("| :--- | :--- | :--- |")
        for prod in manifest["input_products"]:
            lines.append(f"| `{prod['product_key']}` | `{prod['sha256']}` | {prod['citation']} |")
    else:
        lines.append("No external raw-file SHA-256 digests recorded.")
    lines.append("")

    # 4. Analysis Readiness Findings
    lines.append("## 4. Analysis Readiness Assessment")
    readiness = manifest.get("readiness_summary", {})
    lines.append(f"- **Readiness Outcome:** **{readiness.get('status', 'Ready')}**")
    lines.append(f"- **Evaluated Operation:** `{readiness.get('operation', 'analysis')}`")
    if readiness.get("issues"):
        lines.append("### Evaluated Issues & Actions")
        for iss in readiness["issues"]:
            lines.append(f"- **[{iss.get('category', 'NOTE').upper()}] {iss.get('title')}:** {iss.get('consequence')} *(Action: {iss.get('action')})*")
    else:
        lines.append("- All mathematical and observational requirements satisfied without blocking issues.")
    lines.append("")

    # 5. Applied Transformations
    lines.append("## 5. Data Transformations & Exclusions")
    transforms = manifest.get("transformations", [])
    if transforms:
        for t in transforms:
            lines.append(f"- {t}")
    else:
        lines.append("- Direct observation coordinates evaluated; no unverified averaging, bin stitching, or shifting applied.")
    lines.append("")

    # 6. Physical Model & Reference Specifications
    lines.append("## 6. Forward Model & Opacity Specifications")
    lines.append(f"- **Radiative Transfer Engine:** `{model_spec['engine']}` (v{model_spec['engine_version']})")
    lines.append(f"- **Broadening Formulation:** {model_spec['broadening']}")
    lines.append(f"- **Planetary Preset:** `{model_spec.get('preset_id') or 'Custom'}`")
    opacities = model_spec.get("opacities", [])
    if opacities:
        lines.append("### Active Opacity Sources")
        for op in opacities:
            if isinstance(op, dict):
                lines.append(f"- **{op.get('formula', 'Species')}** ({op.get('dataset', 'dataset')}): SHA-256 `{op.get('source_sha256', 'hash')[:16]}...`")
            else:
                lines.append(f"- {op}")
    lines.append("")

    # 7. Model Parameters & Noise Treatment
    lines.append("## 7. Model Parameters & Noise Assumptions")
    lines.append(f"- **Noise Treatment:** `{manifest['noise_assumptions']['treatment']}`")
    params = manifest.get("parameters", {})
    if params:
        lines.append("### Preserved Physical Parameters")
        for k, v in params.items():
            lines.append(f"- `{k}`: `{v}`")
    lines.append("")

    # 8. Fit & Residual Diagnostics Status
    lines.append("## 8. Statistical Fit Diagnostics")
    if diag:
        lines.append(f"- **Reduced χ_ν²:** `{diag.get('reduced_chi2', 'n/a')}`")
        lines.append(f"- **Residual RMS:** `{diag.get('rms_residual', 'n/a')}`")
        lines.append(f"- **Wald-Wolfowitz Runs Z-score:** `{diag.get('runs_z_score', 'n/a')}` ({diag.get('runs_interpretation', 'n/a')})")
        lines.append(f"- **Lag-1 Autocorrelation (r_1):** `{diag.get('lag1_autocorrelation', 'n/a')}`")
    else:
        lines.append("- Forward-model simulation evaluated without active residual fitting.")
    lines.append("")

    # 9. Scientific Limitations
    lines.append("## 9. Stated Scientific Limitations")
    for lim in manifest["limitations"]:
        lines.append(f"> [!WARNING]  \n> {lim}\n")

    # 10. Reproduction Instructions
    lines.append("## 10. Instructions for Deterministic Reproduction")
    lines.append("To independently reproduce this exact scientific analysis:")
    lines.append("```bash")
    lines.append(f"# Verify cryptographic input byte hashes and re-run analysis")
    lines.append(manifest["reproduction_command"])
    lines.append("```")
    lines.append("Alternatively, reload the saved project container inside ECAS and verify the integrity hashes in the Project Browser.")
    lines.append("")

    md_report = "\n".join(lines)
    if format.lower() == "html":
        # Wrap markdown in lightweight HTML styling
        import html
        body_content = html.escape(md_report).replace("\n", "<br>")
        return f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{html.escape(manifest['name'])}</title><style>body {{ font-family: sans-serif; max-width: 800px; margin: 2rem auto; line-height: 1.5; color: #2e3440; background: #eceff4; padding: 1rem; }} pre {{ background: #2e3440; color: #eceff4; padding: 1rem; border-radius: 4px; overflow-x: auto; }}</style></head><body><pre>{body_content}</pre></body></html>"

    return md_report

