"""Controlled laboratory observation metadata attestation and conflict detection.

Enforces scientific integrity for laboratory identification inputs:
1. Distinguishes source-provided information, user-attested values, and application facts.
2. Detects conflicts when user attestation contradicts populated source metadata.
3. Forbids silent inference: wavelength ranges or active UI tabs must never
   establish modality or physical units without explicit user attestation.
4. Preserves complete metadata provenance through persistence and verification.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Any

from ecas.models.spectrum import SpectrumData
from ecas.observations import ObservationContext


# Canonical modalities
SUPPORTED_MODALITIES = ("IR", "UV-Vis")

# Canonical spectral coordinate units
SUPPORTED_AXIS_UNITS = {
    "cm^-1": "wavenumber",
    "cm-1": "wavenumber",
    "1/cm": "wavenumber",
    "microns": "wavelength",
    "micron": "wavelength",
    "um": "wavelength",
    "μm": "wavelength",
    "nm": "wavelength",
    "nanometers": "wavelength",
    "nanometer": "wavelength",
}

# Canonical signal types
SUPPORTED_SIGNAL_TYPES = (
    "transmittance",
    "absorbance",
    "optical_depth",
    "cross_section",
)

# Canonical signal units per signal type
VALID_SIGNAL_UNITS = {
    "absorbance": ("absorbance", "dimensionless", "AU", "a.u.", "1"),
    "transmittance": ("%", "percent", "fraction", "dimensionless"),
    "optical_depth": ("dimensionless", "optical_depth", "1"),
    "cross_section": ("cm2/molecule", "cm^2/molecule", "cm2 molecule-1"),
}


@dataclass(frozen=True)
class AttestationAudit:
    """Audit of an observation context's physical metadata and attestation state."""

    is_complete: bool
    missing_fields: tuple[str, ...]
    source_facts: dict[str, Any]
    user_attested: dict[str, Any]
    effective_facts: dict[str, Any]
    warnings: tuple[str, ...]
    can_identify: bool

    @property
    def summary_message(self) -> str:
        """Concise status string for UI display."""
        if self.is_complete:
            mod = self.effective_facts.get("modality", "")
            axis = self.effective_facts.get("axis_unit", "")
            sig = self.effective_facts.get("signal_type", "")
            unit = self.effective_facts.get("signal_unit", "")
            unit_str = f" [{unit}]" if unit else ""
            return f"{mod} {sig}{unit_str} vs {axis} (Complete)"
        return f"Incomplete: missing {', '.join(self.missing_fields)}"


def audit_observation_attestation(context: ObservationContext) -> AttestationAudit:
    """Audit an observation context to verify whether all required identification facts exist."""
    spec = context.spectrum
    source_meta = dict(getattr(spec, "metadata", ()))
    ctx_meta = dict(context.metadata)

    # 1. Source-provided facts (from file header/table)
    # Check if this context has prior user_attested metadata
    prov = ctx_meta.get("metadata_provenance")
    if isinstance(prov, dict) and "source_provided" in prov:
        source_facts = dict(prov.get("source_provided", {}))
        user_attested = dict(prov.get("user_attested", {}))
    else:
        source_facts = {}
        user_attested = {}
        if spec.axis_unit:
            source_facts["axis_unit"] = spec.axis_unit
        if spec.signal_type:
            source_facts["signal_type"] = spec.signal_type
        if spec.signal_unit:
            source_facts["signal_unit"] = spec.signal_unit
        if source_meta.get("modality"):
            source_facts["modality"] = source_meta["modality"]
        elif ctx_meta.get("modality"):
            source_facts["modality"] = ctx_meta["modality"]

    # 2. Effective facts
    effective_modality = ctx_meta.get("modality") or source_meta.get("modality")
    effective_axis = spec.axis_unit
    effective_signal_type = spec.signal_type
    effective_signal_unit = spec.signal_unit

    effective_facts = {
        "modality": effective_modality,
        "axis_unit": effective_axis,
        "signal_type": effective_signal_type,
        "signal_unit": effective_signal_unit,
    }

    missing: list[str] = []
    warnings: list[str] = []

    # Validate modality
    if not effective_modality or effective_modality not in SUPPORTED_MODALITIES:
        missing.append("modality (IR or UV-Vis)")

    # Validate axis unit
    if not effective_axis or effective_axis.lower() not in SUPPORTED_AXIS_UNITS:
        missing.append("spectral coordinate unit (cm^-1, microns, or nm)")

    # Validate signal type
    normalized_sig_type = (effective_signal_type or "").lower().replace(" ", "_")
    matched_type = None
    for st in SUPPORTED_SIGNAL_TYPES:
        if st in normalized_sig_type:
            matched_type = st
            break

    if not matched_type:
        missing.append("signal observable (absorbance, transmittance, optical_depth, or cross_section)")

    # Validate signal unit
    if matched_type:
        valid_units = VALID_SIGNAL_UNITS[matched_type]
        if not effective_signal_unit or effective_signal_unit.lower() not in [u.lower() for u in valid_units]:
            missing.append(f"signal unit matching {matched_type} ({', '.join(valid_units)})")

    # Modality vs signal type compatibility
    if effective_modality == "IR" and matched_type == "cross_section":
        warnings.append("IR references require absorbance or transmittance, not cross section")

    is_complete = len(missing) == 0 and len(warnings) == 0
    can_identify = is_complete

    return AttestationAudit(
        is_complete=is_complete,
        missing_fields=tuple(missing),
        source_facts=source_facts,
        user_attested=user_attested,
        effective_facts=effective_facts,
        warnings=tuple(warnings),
        can_identify=can_identify,
    )


def attest_observation_context(
    context: ObservationContext,
    *,
    modality: str | None = None,
    axis_unit: str | None = None,
    signal_type: str | None = None,
    signal_unit: str | None = None,
    notes: str | None = None,
) -> ObservationContext:
    """Explicitly attest missing physical facts for an observation context.

    Source facts take precedence; caller attestation cannot contradict established
    source metadata.
    """
    spec = context.spectrum
    source_meta = dict(getattr(spec, "metadata", ()))
    ctx_meta = dict(context.metadata)

    # Determine original source facts (before any user attestation)
    prov = ctx_meta.get("metadata_provenance")
    if isinstance(prov, dict) and "source_provided" in prov:
        src_provided = dict(prov["source_provided"])
        prior_attested = dict(prov.get("user_attested", {}))
    else:
        src_provided = {}
        prior_attested = {}
        if spec.axis_unit:
            src_provided["axis_unit"] = spec.axis_unit
        if spec.signal_type:
            src_provided["signal_type"] = spec.signal_type
        if spec.signal_unit:
            src_provided["signal_unit"] = spec.signal_unit
        if source_meta.get("modality"):
            src_provided["modality"] = source_meta["modality"]
        elif ctx_meta.get("modality"):
            src_provided["modality"] = ctx_meta["modality"]

    new_attested = dict(prior_attested)

    # 1. Modality conflict check
    source_mod = src_provided.get("modality")
    if modality is not None:
        if modality not in SUPPORTED_MODALITIES:
            raise ValueError(
                f"Attested modality must explicitly be one of {SUPPORTED_MODALITIES}, got {modality!r}"
            )
        if source_mod and source_mod.lower() != modality.lower():
            raise ValueError(
                f"Attested modality {modality!r} conflicts with imported metadata {source_mod!r}"
            )
        new_attested["modality"] = modality
        effective_modality = modality
    else:
        effective_modality = new_attested.get("modality") or source_mod

    # 2. Axis unit conflict check
    source_axis = src_provided.get("axis_unit")
    if axis_unit is not None:
        if axis_unit.lower() not in SUPPORTED_AXIS_UNITS:
            raise ValueError(
                f"Attested axis unit {axis_unit!r} is not a supported spectral coordinate unit "
                f"({', '.join(sorted(set(SUPPORTED_AXIS_UNITS.keys())))})"
            )
        if source_axis and source_axis.lower() != axis_unit.lower():
            raise ValueError(
                f"Attested axis unit {axis_unit!r} conflicts with imported metadata {source_axis!r}"
            )
        new_attested["axis_unit"] = axis_unit
        effective_axis = axis_unit
    else:
        effective_axis = new_attested.get("axis_unit") or source_axis

    # 3. Signal type conflict check
    source_sig_type = src_provided.get("signal_type")
    if signal_type is not None:
        normalized_st = signal_type.lower().replace(" ", "_")
        matched = next((st for st in SUPPORTED_SIGNAL_TYPES if st in normalized_st), None)
        if not matched:
            raise ValueError(
                f"Attested signal type {signal_type!r} is not supported. "
                f"Must describe {', '.join(SUPPORTED_SIGNAL_TYPES)}"
            )
        if source_sig_type and matched not in source_sig_type.lower().replace(" ", "_"):
            raise ValueError(
                f"Attested signal type {signal_type!r} conflicts with imported metadata {source_sig_type!r}"
            )
        new_attested["signal_type"] = signal_type
        effective_signal_type = signal_type
        effective_matched_type = matched
    else:
        effective_signal_type = new_attested.get("signal_type") or source_sig_type
        normalized_st = (effective_signal_type or "").lower().replace(" ", "_")
        effective_matched_type = next((st for st in SUPPORTED_SIGNAL_TYPES if st in normalized_st), None)

    # 4. Signal unit conflict check
    source_sig_unit = src_provided.get("signal_unit")
    if signal_unit is not None:
        if source_sig_unit and source_sig_unit.lower() != signal_unit.lower():
            raise ValueError(
                f"Attested signal unit {signal_unit!r} conflicts with imported metadata {source_sig_unit!r}"
            )
        new_attested["signal_unit"] = signal_unit
        effective_signal_unit = signal_unit
    else:
        effective_signal_unit = new_attested.get("signal_unit") or source_sig_unit

    # 5. Scientific consistency check between signal type and unit
    if effective_matched_type and effective_signal_unit:
        valid_units = VALID_SIGNAL_UNITS[effective_matched_type]
        if effective_signal_unit.lower() not in [u.lower() for u in valid_units]:
            raise ValueError(
                f"Signal unit {effective_signal_unit!r} is invalid for signal type {effective_matched_type!r}; "
                f"must be one of: {', '.join(valid_units)}"
            )

    # 6. Scientific consistency check between modality and signal type
    if effective_modality == "IR" and effective_matched_type == "cross_section":
        raise ValueError("IR laboratory identification requires absorbance or transmittance, not cross section")

    if notes is not None:
        new_attested["notes"] = notes.strip()

    # Build updated metadata
    updated_metadata = deepcopy(ctx_meta)
    if effective_modality:
        updated_metadata["modality"] = effective_modality

    updated_metadata["metadata_provenance"] = {
        "source_provided": src_provided,
        "user_attested": new_attested,
        "attestation_notes": notes.strip() if notes else prior_attested.get("notes", ""),
    }

    # Build updated SpectrumData
    updated_spectrum = replace(
        spec,
        axis_unit=effective_axis,
        signal_type=effective_signal_type,
        signal_unit=effective_signal_unit,
    )

    return ObservationContext(
        observation_id=context.observation_id,
        label=context.label,
        spectrum=updated_spectrum,
        source_sha256=context.source_sha256,
        metadata=updated_metadata,
    )

