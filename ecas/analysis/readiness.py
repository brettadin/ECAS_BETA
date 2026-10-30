"""Unified scientific analysis readiness engine for ECAS.

Evaluates operational readiness before running scientific analyses across three
distinct operations:
1. 'view': Inspecting a 1D spectral curve.
2. 'laboratory_fit': Fitting reference cross sections or optical depths to laboratory spectra.
3. 'atmospheric_retrieval': Forward modeling or atmospheric retrieval against transmission spectra.

Reuses existing scientific contracts (eligibility, attestation audit, bin semantics)
without establishing a competing rule system. Emits three canonical outcomes:
- READY: Operation is valid without major methodological caveats.
- READY_WITH_LIMITATIONS: Operation can run, but explicit physical or observational limitations apply.
- BLOCKED: Critical requirements are missing or incompatible, preventing execution.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import math
from pathlib import Path
import re
from typing import Any, Sequence

import numpy as np

from ecas.comparison.eligibility import ComparisonInput, assess, describe_reason
from ecas.comparison.inputs import audit_asymmetric_uncertainties, audit_observation_bin_semantics
from ecas.identification.attestation import AttestationAudit, audit_observation_attestation
from ecas.models.spectrum import SpectrumData
from ecas.observations import ObservationContext

_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


class ReadinessStatus(str, Enum):
    """Canonical analysis readiness outcomes."""

    READY = "Ready"
    READY_WITH_LIMITATIONS = "Ready with stated limitations"
    BLOCKED = "Blocked until a specific issue is resolved"


@dataclass(frozen=True)
class ReadinessIssue:
    """An individual scientific readiness finding with consequence and actionable remedy."""

    code: str
    category: str  # 'missing', 'incompatible', 'limitation'
    title: str
    consequence: str
    action: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ReadinessReport:
    """Complete evaluation of readiness for a specified scientific operation."""

    operation: str
    status: ReadinessStatus
    target_id: str
    issues: tuple[ReadinessIssue, ...]
    user_attestations: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)

    @property
    def is_blocked(self) -> bool:
        return self.status == ReadinessStatus.BLOCKED

    @property
    def has_limitations(self) -> bool:
        return self.status == ReadinessStatus.READY_WITH_LIMITATIONS

    @property
    def is_ready(self) -> bool:
        return self.status == ReadinessStatus.READY

    @property
    def missing_issues(self) -> tuple[ReadinessIssue, ...]:
        return tuple(i for i in self.issues if i.category == "missing")

    @property
    def incompatible_issues(self) -> tuple[ReadinessIssue, ...]:
        return tuple(i for i in self.issues if i.category == "incompatible")

    @property
    def limitation_issues(self) -> tuple[ReadinessIssue, ...]:
        return tuple(i for i in self.issues if i.category == "limitation")

    def summary_lines(self) -> list[str]:
        lines = [f"Analysis Readiness: {self.status.value} ({self.operation})"]
        for issue in self.issues:
            prefix = "[BLOCKED]" if issue.category in ("missing", "incompatible") else "[NOTE]"
            lines.append(f"  {prefix} {issue.title}: {issue.consequence} -> Action: {issue.action}")
        return lines

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "status": self.status.value,
            "target_id": self.target_id,
            "issues": [i.to_dict() for i in self.issues],
            "user_attestations": self.user_attestations,
            "provenance": self.provenance,
        }


def _extract_spectrum_and_context(
    target: SpectrumData | ObservationContext | ComparisonInput,
) -> tuple[SpectrumData | None, ObservationContext | None, ComparisonInput | None]:
    if isinstance(target, ObservationContext):
        return target.spectrum, target, None
    if isinstance(target, SpectrumData):
        return target, None, None
    if isinstance(target, ComparisonInput):
        return None, None, target
    raise TypeError(f"Unsupported target type for readiness evaluation: {type(target)!r}")


def evaluate_readiness(
    operation: str,
    target: SpectrumData | ObservationContext | ComparisonInput,
    *,
    references: Sequence[Any] | None = None,
    forward_model_config: dict[str, Any] | None = None,
    planet_preset: Any | None = None,
    source_sha256: str | None = None,
) -> ReadinessReport:
    """Evaluate analysis readiness for a specific operation.

    Parameters
    ----------
    operation : str
        One of 'view', 'laboratory_fit', or 'atmospheric_retrieval'.
    target : SpectrumData | ObservationContext | ComparisonInput
        Input observation or comparison dataset.
    references : Sequence[Any] | None
        List of ReferenceDataset objects (for laboratory_fit).
    forward_model_config : dict | None
        Atmospheric forward model settings (for atmospheric_retrieval).
    planet_preset : Any | None
        Planetary parameters (for atmospheric_retrieval).
    source_sha256 : str | None
        Established SHA-256 hash of the raw input file.
    """
    op = operation.strip().lower()
    spec, ctx, comp_inp = _extract_spectrum_and_context(target)
    target_id = (
        str(ctx.label if ctx else spec.source_file if spec else comp_inp.source_id)
        if (ctx or spec or comp_inp)
        else "unknown_target"
    )

    issues: list[ReadinessIssue] = []
    user_attestations: dict[str, Any] = {}
    provenance: dict[str, Any] = {
        "operation": op,
        "target_id": target_id,
    }

    if ctx is not None:
        ctx_meta = dict(ctx.metadata)
        prov = ctx_meta.get("metadata_provenance")
        if isinstance(prov, dict):
            user_attestations = dict(prov.get("user_attested", {}))
        provenance["context_metadata"] = ctx_meta

    # -------------------------------------------------------------------------
    # 1. Base Spectral Sampling & Numeric Integrity (All Operations)
    # -------------------------------------------------------------------------
    x_coords: np.ndarray | None = None
    y_vals: np.ndarray | None = None
    sigma_vals: np.ndarray | None = None

    if spec is not None:
        if not spec.rows:
            issues.append(
                ReadinessIssue(
                    code="spectrum.empty",
                    category="incompatible",
                    title="Observation Contains No Data Rows",
                    consequence="Spectrum contains zero rows; no points can be displayed or analyzed.",
                    action="Select a populated data file with numeric measurements.",
                )
            )
        else:
            try:
                x_raw = [r.get("wavelength") for r in spec.rows]
                y_raw = [r.get("signal") for r in spec.rows]
                x_coords = np.array(x_raw, dtype=float)
                y_vals = np.array(y_raw, dtype=float)
            except (ValueError, TypeError, KeyError):
                issues.append(
                    ReadinessIssue(
                        code="spectrum.non_numeric",
                        category="incompatible",
                        title="Non-Numeric Coordinates or Signals",
                        consequence="File contains non-numeric entries in coordinate or signal columns.",
                        action="Inspect the source file header or ensure tabular data parses cleanly.",
                    )
                )

            if x_coords is not None and y_vals is not None:
                if not np.isfinite(x_coords).all() or not np.isfinite(y_vals).all():
                    issues.append(
                        ReadinessIssue(
                            code="spectrum.non_finite_values",
                            category="incompatible",
                            title="Non-Finite (NaN or Inf) Values Present",
                            consequence="Data array contains NaN or Inf values; numerical calculations are invalid.",
                            action="Filter or clean non-finite rows in the source file.",
                        )
                    )
                if np.any(x_coords <= 0.0):
                    issues.append(
                        ReadinessIssue(
                            code="spectrum.non_positive_coordinates",
                            category="incompatible",
                            title="Non-Positive Spectral Coordinates",
                            consequence="Wavelength/wavenumber contains zero or negative values; physical units invalid.",
                            action="Verify the spectral coordinate axis and remove invalid non-positive entries.",
                        )
                    )
                if len(x_coords) < 3:
                    issues.append(
                        ReadinessIssue(
                            code="spectrum.insufficient_samples",
                            category="incompatible",
                            title="Fewer Than 3 Data Samples",
                            consequence="Analysis requires at least 3 spectral points to establish support.",
                            action="Provide a spectrum with adequate spectral coverage.",
                        )
                    )

                # Check duplicate coordinates
                order = np.argsort(x_coords)
                sorted_x = x_coords[order]
                diffs = np.diff(sorted_x)
                if np.any(diffs <= 0):
                    issues.append(
                        ReadinessIssue(
                            code="spectrum.duplicate_coordinates",
                            category="incompatible",
                            title="Duplicate or Non-Monotonic Spectral Coordinates",
                            consequence="Multiple measurements share identical coordinates; ECAS does not perform unverified averaging.",
                            action="Provide an explicitly binned or reduced spectrum with strictly distinct coordinates.",
                        )
                    )

        # Source hash verification
        resolved_hash = source_sha256 or getattr(spec, "source_sha256", None)
        if not resolved_hash or not isinstance(resolved_hash, str) or not _HEX64.fullmatch(resolved_hash):
            issues.append(
                ReadinessIssue(
                    code="provenance.source_hash_missing",
                    category="limitation",
                    title="Source SHA-256 Hash Not Established",
                    consequence="Byte-level source identity cannot be verified against the original disk file.",
                    action="Ensure the spectrum was imported through the project workspace or attach the source file.",
                )
            )
        else:
            provenance["source_sha256"] = resolved_hash

    elif comp_inp is not None:
        try:
            x_coords = np.asarray(comp_inp.coordinates, dtype=float)
            y_vals = np.asarray(comp_inp.values, dtype=float)
            if len(x_coords) < 3 or not np.isfinite(x_coords).all() or not np.isfinite(y_vals).all():
                issues.append(
                    ReadinessIssue(
                        code="comparison_input.invalid_arrays",
                        category="incompatible",
                        title="Invalid Comparison Input Arrays",
                        consequence="Coordinates or signals are non-finite or contain fewer than 3 samples.",
                        action="Verify that the comparison input was generated from valid numeric data.",
                    )
                )
        except Exception:
            issues.append(
                ReadinessIssue(
                    code="comparison_input.malformed",
                    category="incompatible",
                    title="Malformed Comparison Input",
                    consequence="Could not read comparison input coordinate arrays.",
                    action="Check the structure of the ComparisonInput object.",
                )
            )

    # -------------------------------------------------------------------------
    # 2. Operation-Specific Readiness
    # -------------------------------------------------------------------------

    if op in ("view", "spectrum_view"):
        _evaluate_view_readiness(spec, ctx, comp_inp, issues)

    elif op in ("laboratory_fit", "identify"):
        _evaluate_laboratory_fit_readiness(
            spec, ctx, comp_inp, x_coords, y_vals, references, issues, user_attestations
        )

    elif op in ("atmospheric_retrieval", "forward_model", "comparison"):
        _evaluate_atmospheric_readiness(
            spec, ctx, comp_inp, x_coords, y_vals, forward_model_config, planet_preset, issues
        )

    else:
        issues.append(
            ReadinessIssue(
                code="operation.unsupported",
                category="incompatible",
                title=f"Unsupported Operation: {operation!r}",
                consequence=f"ECAS does not recognize the requested operation '{operation}'.",
                action="Choose from 'view', 'laboratory_fit', or 'atmospheric_retrieval'.",
            )
        )

    # -------------------------------------------------------------------------
    # 3. Determine Overall Status
    # -------------------------------------------------------------------------
    has_incompatible = any(i.category == "incompatible" for i in issues)
    has_missing = any(i.category == "missing" for i in issues)
    has_limitation = any(i.category == "limitation" for i in issues)

    if has_incompatible or has_missing:
        status = ReadinessStatus.BLOCKED
    elif has_limitation:
        status = ReadinessStatus.READY_WITH_LIMITATIONS
    else:
        status = ReadinessStatus.READY

    return ReadinessReport(
        operation=operation,
        status=status,
        target_id=target_id,
        issues=tuple(issues),
        user_attestations=user_attestations,
        provenance=provenance,
    )


# =============================================================================
# Helper Evaluators
# =============================================================================


def _evaluate_view_readiness(
    spec: SpectrumData | None,
    ctx: ObservationContext | None,
    comp_inp: ComparisonInput | None,
    issues: list[ReadinessIssue],
) -> None:
    axis_unit = spec.axis_unit if spec else comp_inp.axis_unit if comp_inp else None
    signal_unit = spec.signal_unit if spec else comp_inp.signal_unit if comp_inp else None

    if not axis_unit:
        issues.append(
            ReadinessIssue(
                code="view.axis_unit_missing",
                category="limitation",
                title="Coordinate Axis Unit Missing",
                consequence="Plot axis will display unitless coordinates.",
                action="Attest or declare the coordinate axis unit (e.g. microns, nm, cm^-1).",
            )
        )
    if not signal_unit:
        issues.append(
            ReadinessIssue(
                code="view.signal_unit_missing",
                category="limitation",
                title="Signal Unit Missing",
                consequence="Plot signal axis will display arbitrary unitless values.",
                action="Attest or declare the signal unit (e.g. percent, AU, cm^2/molecule).",
            )
        )


def _evaluate_laboratory_fit_readiness(
    spec: SpectrumData | None,
    ctx: ObservationContext | None,
    comp_inp: ComparisonInput | None,
    x_coords: np.ndarray | None,
    y_vals: np.ndarray | None,
    references: Sequence[Any] | None,
    issues: list[ReadinessIssue],
    user_attestations: dict[str, Any],
) -> None:
    if spec is None:
        issues.append(
            ReadinessIssue(
                code="lab.requires_spectrum_data",
                category="incompatible",
                title="Laboratory Fitting Requires SpectrumData",
                consequence="Cannot evaluate laboratory fit on raw ComparisonInput without SpectrumData model.",
                action="Import observation through the laboratory identification workflow.",
            )
        )
        return

    sig_type = (spec.signal_type or "").lower().replace("_", " ")
    if "transit" in sig_type or sig_type == "transmission":
        issues.append(
            ReadinessIssue(
                code="lab.transit_depth_blocked",
                category="incompatible",
                title="Planetary Transit Depth Submitted to Laboratory Fitting",
                consequence="Planetary transit depth requires a physical radiative transfer model; direct subtraction or BVLS against cross sections is unphysical.",
                action="Switch to the Atmospheric Comparison / Forward Model workflow.",
            )
        )
        return

    # Attestation Audit check
    if ctx is not None:
        audit = audit_observation_attestation(ctx)
        if not audit.is_complete:
            for field in audit.missing_fields:
                field_clean = re.sub(r"[^a-zA-Z0-9_]", "_", field).strip("_").lower()
                # e.g. "modality__ir_or_uv_vis_" -> "modality"
                field_key = field_clean.split("_")[0] if "_" in field_clean else field_clean
                issues.append(
                    ReadinessIssue(
                        code=f"lab.metadata.{field_key}_missing",
                        category="missing",
                        title=f"Missing Required Attestation: {field}",
                        consequence=f"Laboratory identification requires explicit '{field}'; ECAS will not infer it from numerical ranges.",
                        action=f"Open the Attestation dialog and attest '{field}'.",
                    )
                )
        for warn in audit.warnings:
            issues.append(
                ReadinessIssue(
                    code="lab.attestation_warning",
                    category="limitation",
                    title="Attestation Limitation",
                    consequence=warn,
                    action="Review attestation metadata for consistency.",
                )
            )

    # Check signal units
    if "cross section" in sig_type:
        if spec.signal_unit not in ("cm2/molecule", "cm^2/molecule", "cm2 molecule-1"):
            issues.append(
                ReadinessIssue(
                    code="lab.cross_section_unit_invalid",
                    category="incompatible",
                    title="Cross Section Units Must Be cm^2/molecule",
                    consequence=f"Found signal unit {spec.signal_unit!r}; cross-section fits require cm^2/molecule.",
                    action="Convert or attest the signal unit as cm^2/molecule.",
                )
            )
    elif "absorbance" in sig_type:
        if spec.signal_unit not in ("absorbance", "dimensionless", "AU", "a.u.", "1"):
            issues.append(
                ReadinessIssue(
                    code="lab.absorbance_unit_invalid",
                    category="incompatible",
                    title="Absorbance Units Unsupported",
                    consequence=f"Found signal unit {spec.signal_unit!r}; absorbance requires AU or dimensionless.",
                    action="Attest absorbance units as AU or dimensionless.",
                )
            )
    elif "transmittance" in sig_type:
        if spec.signal_unit not in ("fraction", "%", "percent", "dimensionless"):
            issues.append(
                ReadinessIssue(
                    code="lab.transmittance_unit_invalid",
                    category="incompatible",
                    title="Transmittance Units Unsupported",
                    consequence=f"Found signal unit {spec.signal_unit!r}; transmittance requires percent or fraction.",
                    action="Attest transmittance unit as percent or fraction.",
                )
            )

    # Uncertainty availability
    if "uncertainty" not in spec.columns:
        issues.append(
            ReadinessIssue(
                code="lab.uncertainties_unweighted",
                category="limitation",
                title="Observation Lacks Uncertainty Column",
                consequence="Fitting will proceed with estimated residual variance; Delta-chi^2 is uncalibrated.",
                action="Provide measurement uncertainties if available in the source file.",
            )
        )
    else:
        unc_audit = audit_asymmetric_uncertainties(spec)
        if unc_audit.has_asymmetric_columns and unc_audit.warning:
            issues.append(
                ReadinessIssue(
                    code="lab.asymmetric_uncertainty",
                    category="limitation",
                    title="Asymmetric Uncertainties Detected",
                    consequence=unc_audit.warning,
                    action="Review asymmetric upper/lower error bounds.",
                )
            )

    # References validation
    if references is None or len(references) == 0:
        issues.append(
            ReadinessIssue(
                code="lab.references_missing",
                category="missing",
                title="No Reference Datasets Selected",
                consequence="Cannot run identification without candidate reference spectra.",
                action="Select one or more laboratory reference spectra from the library.",
            )
        )
    else:
        # Check overlap with references
        if x_coords is not None and len(x_coords) >= 3:
            unit = (spec.axis_unit or "").lower()
            if unit in ("cm^-1", "cm-1", "1/cm"):
                nu = x_coords
            elif unit in ("microns", "micron", "um", "µm"):
                nu = 1e4 / x_coords
            elif unit in ("nm", "nanometers", "nanometer"):
                nu = 1e7 / x_coords
            else:
                nu = None

            if nu is not None:
                nu_min, nu_max = float(np.min(nu)), float(np.max(nu))
                overlap_count = 0
                for ref in references:
                    ref_spec = getattr(ref, "spectrum", None)
                    if ref_spec and ref_spec.rows:
                        ref_x = [float(r.get("wavelength")) for r in ref_spec.rows if r.get("wavelength")]
                        if ref_x:
                            ref_min, ref_max = min(ref_x), max(ref_x)
                            # Check overlap in wavenumber
                            ov_pts = np.count_nonzero((nu >= ref_min) & (nu <= ref_max))
                            if ov_pts >= 20:
                                overlap_count += 1
                if overlap_count == 0:
                    issues.append(
                        ReadinessIssue(
                            code="lab.no_overlapping_references",
                            category="incompatible",
                            title="No References Overlap Common Spectral Range",
                            consequence="Selected references have fewer than 20 overlapping points with the observation.",
                            action="Select references covering the observation's wavenumber range.",
                        )
                    )


def _evaluate_atmospheric_readiness(
    spec: SpectrumData | None,
    ctx: ObservationContext | None,
    comp_inp: ComparisonInput | None,
    x_coords: np.ndarray | None,
    y_vals: np.ndarray | None,
    forward_model_config: dict[str, Any] | None,
    planet_preset: Any | None,
    issues: list[ReadinessIssue],
) -> None:
    observable = (
        comp_inp.observable
        if comp_inp
        else (
            {"Transmission": "transit_depth"}.get(spec.signal_type)
            if spec and spec.signal_type
            else None
        )
    )
    if observable != "transit_depth":
        issues.append(
            ReadinessIssue(
                code="atmos.observable_unsupported",
                category="incompatible",
                title="Observable Must Be Planetary Transit Depth",
                consequence=f"Found observable {observable!r}; atmospheric forward modeling requires transit depth.",
                action="Import a transmission spectroscopy observation or select transit_depth.",
            )
        )

    axis_unit = comp_inp.axis_unit if comp_inp else spec.axis_unit if spec else None
    if axis_unit != "microns":
        issues.append(
            ReadinessIssue(
                code="atmos.axis_unit_not_microns",
                category="incompatible",
                title="Wavelength Axis Unit Must Be Microns",
                consequence=f"Found coordinate axis unit {axis_unit!r}; radiative transfer requires microns.",
                action="Convert coordinate axis to microns via explicit transformation.",
            )
        )

    signal_unit = comp_inp.signal_unit if comp_inp else spec.signal_unit if spec else None
    if signal_unit == "%":
        signal_unit = "percent"
    if signal_unit not in ("percent", "fraction"):
        issues.append(
            ReadinessIssue(
                code="atmos.signal_unit_unsupported",
                category="incompatible",
                title="Signal Unit Must Be Percent or Fraction",
                consequence=f"Found signal unit {signal_unit!r}; transit depth must be expressed in percent or fraction.",
                action="Convert transit depth values to percent or fraction.",
            )
        )

    # Check bin semantics
    if spec is not None:
        bin_audit = audit_observation_bin_semantics(spec)
        if bin_audit.has_resolved_bins:
            if bin_audit.warning:
                issues.append(
                    ReadinessIssue(
                        code="atmos.bin_warning",
                        category="limitation",
                        title="Passband Bin Boundaries Resolved with Warnings",
                        consequence=bin_audit.warning,
                        action="Inspect bin width column conventions.",
                    )
                )
        else:
            if bin_audit.convention == "rejected_response_fwhm":
                issues.append(
                    ReadinessIssue(
                        code="atmos.fwhm_response_profile",
                        category="limitation",
                        title="Instrument FWHM Not Treated as Top-Hat Bins",
                        consequence="FWHM describes a peaked response profile; top-hat integration is bypassed.",
                        action="Model evaluations will be performed at bin center wavelengths.",
                    )
                )

    # Check planetary and stellar parameters
    if planet_preset is None and forward_model_config is None:
        issues.append(
            ReadinessIssue(
                code="atmos.planet_preset_missing",
                category="missing",
                title="No Planetary Preset or Bulk Parameters Configured",
                consequence="Radiative transfer cannot compute atmospheric scale height H = kT / (mu * g) without Rp, R*, T, and g.",
                action="Select a planetary preset (e.g. WASP-39 b) or provide stellar and planetary bulk parameters.",
            )
        )
    elif planet_preset is not None:
        # Check scale height sanity
        t = getattr(planet_preset, "temperature_k", None)
        g = getattr(planet_preset, "gravity_m_s2", None)
        rp = getattr(planet_preset, "planet_radius_m", None)
        rstar = getattr(planet_preset, "stellar_radius_m", None)
        mu = getattr(planet_preset, "mean_molecular_weight_u", 2.3)

        if not all(isinstance(v, (int, float)) and v > 0 for v in (t, g, rp, rstar, mu)):
            issues.append(
                ReadinessIssue(
                    code="atmos.preset_parameters_invalid",
                    category="incompatible",
                    title="Planetary Preset Parameters Non-Positive or Invalid",
                    consequence="T, g, Rp, R*, or mu are non-positive.",
                    action="Check planetary preset definition.",
                )
            )
        else:
            k_b = 1.380649e-23
            m_u = 1.6605390666e-27
            h = (k_b * t) / (mu * m_u * g)
            if h > 0.25 * rp:
                issues.append(
                    ReadinessIssue(
                        code="atmos.scale_height_unphysical",
                        category="incompatible",
                        title=f"Unphysical Hydrostatic Scale Height (H/Rp = {h/rp:.2f} > 0.25)",
                        consequence="Atmosphere would undergo catastrophic hydrodynamic escape; hydrostatic model invalid.",
                        action="Verify temperature, gravity, and mean molecular weight.",
                    )
                )

    # Check forward model opacity sources and physical limitations
    if forward_model_config is not None:
        sources = forward_model_config.get("opacity_sources", ())
        has_synthetic = any(
            isinstance(s, dict) and s.get("dataset") == "ECAS-IllustrativeBandProfile-Synthetic"
            for s in sources
        )
        if has_synthetic:
            issues.append(
                ReadinessIssue(
                    code="atmos.synthetic_templates_used",
                    category="limitation",
                    title="Synthetic Illustrative Band Profiles Used",
                    consequence="Model uses Gaussian band-envelope approximations rather than line-by-line cross sections.",
                    action="Download ExoMol cross sections for line-resolved opacity calculations.",
                )
            )

        # Inherent 1D isothermal limitation
        issues.append(
            ReadinessIssue(
                code="atmos.isothermal_1d_limitation",
                category="limitation",
                title="1D Isothermal Hydrostatic Assumption",
                consequence="Forward model assumes uniform temperature and mixing ratios; vertical temperature gradients and 3D terminator effects are neglected.",
                action="Review physical results with awareness of the 1D isothermal scope.",
            )
        )
        # Doppler zero-pressure broadening limitation
        issues.append(
            ReadinessIssue(
                code="atmos.zero_pressure_broadening_limitation",
                category="limitation",
                title="Zero-Pressure Doppler Cross Sections",
                consequence="ExoMol public cross sections neglect pressure-broadened collisional wings at P > 0.01 bar.",
                action="Account for pressure broadening at deep atmospheric pressures.",
            )
        )
