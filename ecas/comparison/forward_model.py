"""Explicit physical-assumption contract for forward-modelled transit spectra.

ECAS does not include a built-in radiative-transfer solver or abundance
retrieval engine, and it strictly forbids rescaling a raw molecular cross
section (cm^2/molecule) to masquerade as a transit-depth prediction. Any
externally generated or future forward-modelled transit spectrum must supply a
complete AtmosphericModelProvenance record before entering ComparisonInput as
role='forward_model'.
"""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
import re

import numpy as np

from .eligibility import ComparisonInput

_HEX64 = re.compile(r'^[0-9a-fA-F]{64}$')
MODEL_FILE_SCHEMA = 'ecas-forward-model-v1'
MAX_MODEL_BYTES = 4 * 1024 * 1024
_WAVELENGTH_UNITS = ('microns', 'nanometers', 'nm', 'angstroms')


class UnsupportedProjectionError(ValueError):
    """Raised when an unvalidated physical projection or abundance inference is requested."""


@dataclass(frozen=True)
class OpacitySourceSpec:
    formula: str
    isotopologue: str
    dataset: str
    version: str
    source_sha256: str


@dataclass(frozen=True)
class AtmosphericModelProvenance:
    engine_name: str
    engine_version: str
    temperature_pressure_profile: str
    abundance_convention: str
    species_parameters: tuple[tuple[str, float], ...]
    opacity_sources: tuple[OpacitySourceSpec, ...]
    gravity_m_s2: float
    reference_pressure_bar: float
    planet_radius_m: float
    stellar_radius_m: float
    continuum_and_clouds: str


def _nonempty_str(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_model_provenance(provenance: AtmosphericModelProvenance) -> AtmosphericModelProvenance:
    """Verify that all required physical radiative-transfer assumptions are explicit."""
    if not isinstance(provenance, AtmosphericModelProvenance):
        raise ValueError('Require an AtmosphericModelProvenance instance')
    for field_name in (
        'engine_name',
        'engine_version',
        'temperature_pressure_profile',
        'abundance_convention',
        'continuum_and_clouds',
    ):
        if not _nonempty_str(getattr(provenance, field_name)):
            raise ValueError(f'Missing required model provenance field: {field_name}')

    for numeric_name in (
        'gravity_m_s2',
        'reference_pressure_bar',
        'planet_radius_m',
        'stellar_radius_m',
    ):
        val = getattr(provenance, numeric_name)
        if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or val <= 0:
            raise ValueError(f'Model {numeric_name} must be a finite positive number')

    if not provenance.opacity_sources:
        raise ValueError('Forward model requires at least one documented OpacitySourceSpec')
    for src in provenance.opacity_sources:
        if not isinstance(src, OpacitySourceSpec):
            raise ValueError('Each opacity_sources item must be an OpacitySourceSpec')
        for attr in ('formula', 'isotopologue', 'dataset', 'version'):
            if not _nonempty_str(getattr(src, attr)):
                raise ValueError(f'OpacitySourceSpec.{attr} must be a non-empty string')
        if not isinstance(src.source_sha256, str) or not _HEX64.fullmatch(src.source_sha256):
            raise ValueError('OpacitySourceSpec.source_sha256 must be a 64-hex SHA-256 digest')

    if not provenance.species_parameters:
        raise ValueError('Forward model requires explicit input species_parameters')
    for entry in provenance.species_parameters:
        if (
            not isinstance(entry, tuple)
            or len(entry) != 2
            or not _nonempty_str(entry[0])
            or isinstance(entry[1], bool)
            or not isinstance(entry[1], (int, float))
            or not math.isfinite(entry[1])
            or entry[1] < 0
        ):
            raise ValueError('Each species_parameters entry must be (species_name, nonnegative_value)')

    return provenance


@dataclass(frozen=True)
class LoadedForwardModel:
    comparison_input: ComparisonInput
    provenance: AtmosphericModelProvenance
    source_path: Path
    raw_sha256: str

    def to_provenance_dict(self) -> dict:
        return {
            'kind': 'forward_model_file',
            'schema': MODEL_FILE_SCHEMA,
            'source_path': str(self.source_path),
            'raw_sha256': self.raw_sha256,
            'atmospheric_model_provenance': asdict(self.provenance),
        }


def forward_model_input(
    *,
    source_id: str,
    source_sha256: str,
    provenance: AtmosphericModelProvenance,
    axis_unit: str,
    signal_unit: str,
    coordinate_frame: str | None,
    response_id: str | None,
    response_evidence: str | None,
    coordinates: tuple[float, ...],
    values: tuple[float, ...],
    allow_convertible_axis_units: bool = False,
) -> ComparisonInput:
    """Wrap a precomputed radiative-transfer transit-depth curve with verified provenance."""
    validate_model_provenance(provenance)
    if signal_unit not in ('percent', 'fraction'):
        raise ValueError(
            f'Forward-model transit depth requires signal_unit percent or fraction, got {signal_unit!r}'
        )
    allowed_axes = _WAVELENGTH_UNITS if allow_convertible_axis_units else ('microns',)
    if axis_unit not in allowed_axes:
        raise ValueError(
            f'Forward-model transit depth requires axis_unit in {allowed_axes}, got {axis_unit!r}'
        )
    coords = np.asarray(coordinates, dtype=float)
    vals = np.asarray(values, dtype=float)
    if (
        coords.ndim != 1 or vals.ndim != 1 or len(coords) < 3 or len(coords) != len(vals)
        or not np.isfinite(coords).all() or not np.isfinite(vals).all()
        or not np.all(np.diff(coords) > 0)
    ):
        raise ValueError('Forward-model curve requires >= 3 finite strictly increasing coordinates')

    return ComparisonInput(
        source_id=source_id,
        source_sha256=source_sha256,
        role='forward_model',
        observable='transit_depth',
        axis_unit=axis_unit,
        signal_unit=signal_unit,
        coordinate_frame=coordinate_frame,
        response_id=response_id,
        response_evidence=response_evidence,
        coordinates=tuple(float(v) for v in coords),
        values=tuple(float(v) for v in vals),
        noise_kind='deterministic_model',
        noise_evidence=(
            f'Deterministic radiative-transfer output from {provenance.engine_name} '
            f'{provenance.engine_version}'
        ),
        sigma=None,
        covariance=None,
    )


def _optional_str(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f'{field_name} must be a string or null')
    stripped = value.strip()
    return stripped if stripped else None


def _numeric_tuple(seq: object, field_name: str) -> tuple[float, ...]:
    if not isinstance(seq, (list, tuple)):
        raise ValueError(f'{field_name} must be a sequence of numbers')
    out: list[float] = []
    for item in seq:
        if isinstance(item, bool) or not isinstance(item, (int, float)) or not math.isfinite(item):
            raise ValueError(f'{field_name} must contain only finite numbers')
        out.append(float(item))
    return tuple(out)


def _parse_species_parameters(raw_species: object) -> tuple[tuple[str, float], ...]:
    if isinstance(raw_species, dict):
        pairs = list(raw_species.items())
    elif isinstance(raw_species, list):
        pairs = raw_species
    else:
        raise ValueError('provenance.species_parameters must be a mapping or list of [species, value] pairs')
    parsed: list[tuple[str, float]] = []
    for entry in pairs:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise ValueError('Each species_parameters entry must be a [species, value] pair')
        name, val = entry
        if isinstance(val, bool) or not isinstance(val, (int, float)):
            raise ValueError('Each species_parameters value must be a number')
        parsed.append((name, float(val)))
    return tuple(parsed)


def load_forward_model_file(path: str | Path) -> LoadedForwardModel:
    """Load, hash, and provenance-verify a local ecas-forward-model-v1 JSON file.

    Coordinates and units are preserved in their declared native wavelength/signal
    units without implicit conversion; source_sha256 is bound directly to the raw
    file bytes on disk.
    """
    target = Path(path)
    if target.is_symlink() or target.is_junction():
        raise ValueError('Linked forward-model file is unsupported')
    with target.open('rb') as stream:
        raw = stream.read(MAX_MODEL_BYTES + 1)
    if len(raw) > MAX_MODEL_BYTES:
        raise ValueError('Forward-model file exceeds 4 MiB limit')
    raw_sha256 = sha256(raw).hexdigest()

    data = json.loads(raw.decode('utf-8'))
    if not isinstance(data, dict) or data.get('schema') != MODEL_FILE_SCHEMA:
        raise ValueError(f'Unsupported forward-model schema; expected {MODEL_FILE_SCHEMA!r}')

    prov_raw = data.get('provenance')
    if not isinstance(prov_raw, dict):
        raise ValueError('Forward-model file requires a provenance object')

    opacities_raw = prov_raw.get('opacity_sources')
    if not isinstance(opacities_raw, list) or not opacities_raw:
        raise ValueError('provenance.opacity_sources must be a non-empty list')
    opacity_specs: list[OpacitySourceSpec] = []
    for item in opacities_raw:
        if not isinstance(item, dict):
            raise ValueError('Each opacity_sources item must be an object')
        opacity_specs.append(
            OpacitySourceSpec(
                formula=item.get('formula'),
                isotopologue=item.get('isotopologue'),
                dataset=item.get('dataset'),
                version=item.get('version'),
                source_sha256=item.get('source_sha256'),
            )
        )

    provenance = AtmosphericModelProvenance(
        engine_name=prov_raw.get('engine_name'),
        engine_version=prov_raw.get('engine_version'),
        temperature_pressure_profile=prov_raw.get('temperature_pressure_profile'),
        abundance_convention=prov_raw.get('abundance_convention'),
        species_parameters=_parse_species_parameters(prov_raw.get('species_parameters')),
        opacity_sources=tuple(opacity_specs),
        gravity_m_s2=prov_raw.get('gravity_m_s2'),
        reference_pressure_bar=prov_raw.get('reference_pressure_bar'),
        planet_radius_m=prov_raw.get('planet_radius_m'),
        stellar_radius_m=prov_raw.get('stellar_radius_m'),
        continuum_and_clouds=prov_raw.get('continuum_and_clouds'),
    )
    validate_model_provenance(provenance)

    raw_source_id = _optional_str(data.get('source_id'), 'source_id')
    source_id = raw_source_id if raw_source_id is not None else target.name
    axis_unit = data.get('axis_unit')
    signal_unit = data.get('signal_unit')
    if not isinstance(axis_unit, str) or not isinstance(signal_unit, str):
        raise ValueError('Forward-model axis_unit and signal_unit must be strings')

    comp_input = forward_model_input(
        source_id=source_id,
        source_sha256=raw_sha256,
        provenance=provenance,
        axis_unit=axis_unit,
        signal_unit=signal_unit,
        coordinate_frame=_optional_str(data.get('coordinate_frame'), 'coordinate_frame'),
        response_id=_optional_str(data.get('response_id'), 'response_id'),
        response_evidence=_optional_str(data.get('response_evidence'), 'response_evidence'),
        coordinates=_numeric_tuple(data.get('coordinates'), 'coordinates'),
        values=_numeric_tuple(data.get('values'), 'values'),
        allow_convertible_axis_units=True,
    )
    return LoadedForwardModel(
        comparison_input=comp_input,
        provenance=provenance,
        source_path=target,
        raw_sha256=raw_sha256,
    )


def project_cross_section_to_transit_depth(*_args, **_kwargs):
    """Explicitly block ad-hoc cross-section rescaling or unvalidated projection."""
    raise UnsupportedProjectionError(
        'Direct cross-section-to-transit-depth projection and atmospheric abundance '
        'retrieval are deferred: an explicit, validated radiative-transfer solver '
        '(with T-P structure, gravity, reference pressure, planet/stellar radii, '
        'multi-species opacities, continuum/clouds, and instrument response) is required.'
    )

