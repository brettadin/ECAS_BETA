"""Verified external forward-model adapters and software evaluation matrix for ECAS Chunk 7.

Implements Approach C (External Forward-Model Adapters + Provenance Contract):
ECAS remains lightweight and license-clean (no bundled Fortran/CUDA binaries or
multi-gigabyte opacity tables) while accepting precomputed forward-model spectra
from established community packages (petitRADTRANS, POSEIDON, TauREx 3, PLATON,
Pyrat Bay) with complete AtmosphericModelProvenance and molecular-database
temperature-applicability checks.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

from ecas.comparison.forward_model import (
    MODEL_FILE_SCHEMA,
    AtmosphericModelProvenance,
    LoadedForwardModel,
    OpacitySourceSpec,
    load_forward_model_file,
    validate_model_provenance,
)
from ecas.resources.catalog import (
    ScientificResource,
    get_resource_by_id,
    validate_temperature_applicability,
)


@dataclass(frozen=True)
class ExternalModelingSoftwareSpec:
    """Structured technical evaluation of an established atmospheric modeling code."""

    software_id: str
    name: str
    resource_id: str
    observing_modes: tuple[str, ...]
    radiative_transfer_method: str
    opacity_treatment: str
    chemistry_modes: tuple[str, ...]
    cloud_haze_parametrizations: str
    retrieval_samplers: tuple[str, ...]
    typical_data_footprint: str
    license_spdx: str
    ecas_integration_role: str

    @property
    def catalog_resource(self) -> ScientificResource:
        res = get_resource_by_id(self.resource_id)
        if res is None:
            raise KeyError(f"Missing catalog resource for {self.resource_id!r}")
        return res


EXTERNAL_MODELING_SOFTWARE: tuple[ExternalModelingSoftwareSpec, ...] = (
    ExternalModelingSoftwareSpec(
        software_id="petitradtrans",
        name="petitRADTRANS",
        resource_id="software-petitradtrans",
        observing_modes=("Transmission", "Thermal emission / eclipse", "Direct imaging", "High-resolution CCF"),
        radiative_transfer_method="1D plane-parallel transmission chord integration and Feautrier/two-stream emission radiative transfer.",
        opacity_treatment="Correlated-k (low-res R=1000) and line-by-line (high-res R=10^6) HDF5 opacity tables from ExoMol, HITEMP, and HITRAN.",
        chemistry_modes=("Free abundance profiles", "Equilibrium chemistry (easychem / fastchem)", "Disequilibrium quench pressure"),
        cloud_haze_parametrizations="Power-law Rayleigh-like haze slope, gray cloud deck pressure, and Ackerman & Marley condensate Mie scattering.",
        retrieval_samplers=("PyMultiNest", "Ultranest", "emcee"),
        typical_data_footprint="~5–50+ GB of correlated-k / line-by-line HDF5 opacity grids.",
        license_spdx="MIT",
        ecas_integration_role="Primary external forward-model generator via adapt_external_forward_model() and ecas-forward-model-v1 JSON export.",
    ),
    ExternalModelingSoftwareSpec(
        software_id="poseidon",
        name="POSEIDON",
        resource_id="software-poseidon",
        observing_modes=("Transmission (1D/2D/3D)", "Thermal emission / secondary eclipse"),
        radiative_transfer_method="1D/2D/3D cylindrical coordinate ray-tracing across day-night and morning-evening terminator sectors.",
        opacity_treatment="Opacity sampling from precomputed high-resolution cross-section HDF5 databases (ExoMol, HITEMP, HITRAN).",
        chemistry_modes=("Free VMR (uniform or altitude/sector-dependent)", "Equilibrium chemistry grid interpolation"),
        cloud_haze_parametrizations="Patchy sector clouds, gray cloud deck, power-law aerosol hazes, and Mie scattering aerosols.",
        retrieval_samplers=("PyMultiNest (nested sampling)",),
        typical_data_footprint="~10–30 GB of precomputed HDF5 cross-section tables.",
        license_spdx="BSD-3-Clause",
        ecas_integration_role="External multidimensional transmission/emission forward-model source for JWST benchmark comparisons.",
    ),
    ExternalModelingSoftwareSpec(
        software_id="taurex3",
        name="TauREx 3",
        resource_id="software-taurex3",
        observing_modes=("Transmission", "Thermal emission", "Phase curves"),
        radiative_transfer_method="Plugin-based 1D layered plane-parallel optical depth integration.",
        opacity_treatment="ExoMol/HITRAN cross-section (.xsec / HDF5) or correlated-k (.ktables) tables.",
        chemistry_modes=("Constant/two-layer free VMR", "ACE / FastChem thermochemical equilibrium", "Custom plugin chemistry"),
        cloud_haze_parametrizations="Simple gray cloud deck, Lee et al. Mie scattering clouds, and power-law Rayleigh haze.",
        retrieval_samplers=("MultiNest", "UltraNest", "Nestle", "dynesty", "emcee"),
        typical_data_footprint="~1–20 GB depending on selected ExoMol .xsec / k-table resolution.",
        license_spdx="BSD-3-Clause",
        ecas_integration_role="Modular external forward-model and retrieval output source (wavenumber cm^-1 or wavelength um grids).",
    ),
    ExternalModelingSoftwareSpec(
        software_id="platon",
        name="PLATON",
        resource_id="software-platon",
        observing_modes=("Transmission", "Secondary eclipse / thermal emission"),
        radiative_transfer_method="Fast 1D hydrostatic plane-parallel radiative transfer with pre-tabulated opacity grids.",
        opacity_treatment="Pre-gridded wavelength-temperature-pressure absorption cross sections (R~1000 to R~10,000).",
        chemistry_modes=("Equilibrium chemistry (metallicity Z, C/O ratio)", "Free species abundances"),
        cloud_haze_parametrizations="Cloud-top pressure P_cloud, scattering slope alpha, scattering factor, and Mie condensates.",
        retrieval_samplers=("dynesty (dynamic nested sampling)", "emcee (Affine-invariant MCMC)"),
        typical_data_footprint="~1–4 GB of pre-gridded opacity tables.",
        license_spdx="MIT",
        ecas_integration_role="Lightweight external forward-model generator (native SI meters wavelength + (Rp/Rs)^2 transit depth).",
    ),
    ExternalModelingSoftwareSpec(
        software_id="pyratbay",
        name="Pyrat Bay",
        resource_id="software-pyratbay",
        observing_modes=("Transmission", "Thermal emission"),
        radiative_transfer_method="1D plane-parallel radiative transfer with line-by-line or opacity sampling.",
        opacity_treatment="Line-by-line processing of ExoMol/HITRAN/HITEMP line lists into cross-section tables.",
        chemistry_modes=("TEA thermochemical equilibrium", "Uniform free VMR profiles"),
        cloud_haze_parametrizations="Gray cloud deck and Lecavelier des Etangs Rayleigh scattering haze.",
        retrieval_samplers=("MC3 (MCMC / Snooker / DEMC)", "MultiNest"),
        typical_data_footprint="~2–25 GB depending on line-list compilation.",
        license_spdx="GPL-2.0-only",
        ecas_integration_role="External output file ingestion only; never linked or bundled in ECAS due to GPL-2.0 copyleft.",
    ),
)


@dataclass(frozen=True)
class AdaptedExternalModel:
    """Result of adapting an external forward model into ECAS's verified contract."""

    loaded_model: LoadedForwardModel
    software_spec: ExternalModelingSoftwareSpec
    representative_temperature_k: float
    applicability_warnings: tuple[str, ...]


def get_modeling_software_spec(software_id: str) -> ExternalModelingSoftwareSpec:
    normalized = software_id.strip().lower()
    for spec in EXTERNAL_MODELING_SOFTWARE:
        if spec.software_id == normalized or spec.name.lower() == normalized:
            return spec
    raise ValueError(
        f"Unsupported external modeling software {software_id!r}; supported: "
        f"{', '.join(s.software_id for s in EXTERNAL_MODELING_SOFTWARE)}"
    )


def export_external_forward_model(
    *,
    output_path: str | Path,
    software_id: str,
    engine_version: str,
    coordinates: tuple[float, ...] | list[float],
    values: tuple[float, ...] | list[float],
    input_axis_unit: str,
    input_signal_unit: str,
    representative_temperature_k: float,
    temperature_pressure_profile: str,
    abundance_convention: str,
    species_parameters: tuple[tuple[str, float], ...],
    opacity_sources: tuple[OpacitySourceSpec, ...],
    gravity_m_s2: float,
    reference_pressure_bar: float,
    planet_radius_m: float,
    stellar_radius_m: float,
    continuum_and_clouds: str,
    coordinate_frame: str | None = "barycentric",
    response_id: str | None = None,
    response_evidence: str | None = None,
    source_id: str | None = None,
) -> AdaptedExternalModel:
    """Validate and export an external model curve to an ecas-forward-model-v1 JSON file.

    Handles native coordinate/signal conventions from petitRADTRANS, PLATON,
    TauREx 3, POSEIDON, and Pyrat Bay:
    - input_axis_unit: 'microns', 'um', 'meters', 'm', 'cm', 'nm', 'angstroms', or 'cm^-1'
      (wavenumbers in cm^-1 and SI meters/cm are converted to strictly increasing 'microns'
      at export time so the resulting ecas-forward-model-v1 file satisfies native wavelength
      monotone ordering).
    - input_signal_unit: 'fraction', 'percent', or 'ppm'.
    - Validates opacity database temperature applicability against representative_temperature_k.
    """
    spec = get_modeling_software_spec(software_id)
    if not math.isfinite(representative_temperature_k) or representative_temperature_k <= 0:
        raise ValueError("representative_temperature_k must be a positive finite temperature in Kelvin")

    provenance = AtmosphericModelProvenance(
        engine_name=spec.name,
        engine_version=engine_version,
        temperature_pressure_profile=temperature_pressure_profile,
        abundance_convention=abundance_convention,
        species_parameters=species_parameters,
        opacity_sources=opacity_sources,
        gravity_m_s2=gravity_m_s2,
        reference_pressure_bar=reference_pressure_bar,
        planet_radius_m=planet_radius_m,
        stellar_radius_m=stellar_radius_m,
        continuum_and_clouds=continuum_and_clouds,
    )
    validate_model_provenance(provenance)

    # Check molecular database temperature applicability
    warnings: list[str] = []
    for op in opacity_sources:
        ds_upper = op.dataset.upper()
        for db_name in ("EXOMOL", "HITRAN", "HITEMP", "NIST ASD", "GEISA"):
            if db_name in ds_upper:
                is_ok, warn = validate_temperature_applicability(
                    db_name if db_name != "EXOMOL" else "ExoMol",
                    representative_temperature_k,
                )
                if not is_ok:
                    warnings.append(f"{op.formula} ({op.dataset}): {warn}")

    coords_arr = np.asarray(coordinates, dtype=float)
    vals_arr = np.asarray(values, dtype=float)
    if (
        coords_arr.ndim != 1
        or vals_arr.ndim != 1
        or len(coords_arr) < 3
        or len(coords_arr) != len(vals_arr)
        or not np.isfinite(coords_arr).all()
        or not np.isfinite(vals_arr).all()
        or np.any(coords_arr <= 0)
    ):
        raise ValueError("External model coordinates and values must be finite positive 1D arrays of length >= 3")

    unit_norm = input_axis_unit.strip().lower()
    if unit_norm in ("microns", "um", "micron"):
        out_coords = coords_arr
        out_axis_unit = "microns"
    elif unit_norm in ("m", "meter", "meters"):
        # PLATON outputs wavelength in SI meters
        out_coords = coords_arr * 1e6
        out_axis_unit = "microns"
    elif unit_norm == "cm":
        # petitRADTRANS cgs wavelength in cm
        out_coords = coords_arr * 1e4
        out_axis_unit = "microns"
    elif unit_norm in ("nm", "nanometers"):
        out_coords = coords_arr
        out_axis_unit = "nm"
    elif unit_norm in ("angstroms", "angstrom"):
        out_coords = coords_arr
        out_axis_unit = "angstroms"
    elif unit_norm in ("cm^-1", "cm-1", "1/cm"):
        # TauREx 3 / petitRADTRANS wavenumber grid -> invert to strictly increasing microns
        if not np.all(np.diff(coords_arr) > 0) and not np.all(np.diff(coords_arr) < 0):
            raise ValueError("External wavenumber grid must be strictly monotonic")
        wavelengths = 10000.0 / coords_arr
        order = np.argsort(wavelengths)
        out_coords = wavelengths[order]
        vals_arr = vals_arr[order]
        out_axis_unit = "microns"
    else:
        raise ValueError(f"Unsupported external model axis unit: {input_axis_unit!r}")

    if not np.all(np.diff(out_coords) > 0):
        raise ValueError("External model wavelength coordinates must be strictly increasing")

    sig_norm = input_signal_unit.strip().lower()
    if sig_norm == "fraction":
        out_vals = vals_arr
        out_sig_unit = "fraction"
    elif sig_norm in ("percent", "%"):
        out_vals = vals_arr
        out_sig_unit = "percent"
    elif sig_norm == "ppm":
        out_vals = vals_arr * 1e-6
        out_sig_unit = "fraction"
    else:
        raise ValueError(f"Unsupported external model signal unit: {input_signal_unit!r}")

    target_path = Path(output_path)
    payload = {
        "schema": MODEL_FILE_SCHEMA,
        "source_id": source_id or f"{spec.name}-{engine_version}-{target_path.stem}",
        "axis_unit": out_axis_unit,
        "signal_unit": out_sig_unit,
        "coordinate_frame": coordinate_frame,
        "response_id": response_id,
        "response_evidence": response_evidence,
        "coordinates": [float(x) for x in out_coords],
        "values": [float(y) for y in out_vals],
        "provenance": {
            "engine_name": provenance.engine_name,
            "engine_version": provenance.engine_version,
            "temperature_pressure_profile": provenance.temperature_pressure_profile,
            "abundance_convention": provenance.abundance_convention,
            "species_parameters": [[k, float(v)] for k, v in provenance.species_parameters],
            "opacity_sources": [asdict(op) for op in provenance.opacity_sources],
            "gravity_m_s2": float(provenance.gravity_m_s2),
            "reference_pressure_bar": float(provenance.reference_pressure_bar),
            "planet_radius_m": float(provenance.planet_radius_m),
            "stellar_radius_m": float(provenance.stellar_radius_m),
            "continuum_and_clouds": provenance.continuum_and_clouds,
        },
        "software_reference": {
            "resource_id": spec.resource_id,
            "canonical_url": spec.catalog_resource.canonical_url,
            "doi": spec.catalog_resource.doi,
            "citation": spec.catalog_resource.citation,
            "license_spdx": spec.license_spdx,
            "representative_temperature_k": float(representative_temperature_k),
            "applicability_warnings": warnings,
        },
    }
    raw_bytes = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
    target_path.write_bytes(raw_bytes)
    loaded = load_forward_model_file(target_path)
    return AdaptedExternalModel(
        loaded_model=loaded,
        software_spec=spec,
        representative_temperature_k=float(representative_temperature_k),
        applicability_warnings=tuple(warnings),
    )
