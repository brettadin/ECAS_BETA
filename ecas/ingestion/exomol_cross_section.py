"""Narrow parser for ExoMol two-column, zero-pressure .sigma products.

No network, cache or automatic conversion. Metadata are caller-supplied provenance,
not authenticated by numerical parsing. Single-column grids require a separate
documented representation and are deliberately unsupported.
"""
from dataclasses import dataclass
from hashlib import sha256
import math
from urllib.parse import urlsplit

MAX_BYTES = 1024 * 1024
MAX_POINTS = 10000
LICENCE_URL = 'https://creativecommons.org/licenses/by-sa/4.0/'


class ReferenceImportError(ValueError):
    """Invalid reference product or incomplete supported-product provenance."""


@dataclass(frozen=True)
class CrossSectionProvenance:
    molecule: str
    isotopologue: str
    dataset: str
    temperature_kelvin: float
    pressure_bar: float
    broadening: str
    source_url: str
    citations: tuple[str, ...]
    licence_url: str


@dataclass(frozen=True)
class MolecularCrossSection:
    provenance: CrossSectionProvenance
    points: tuple[tuple[float, float], ...]
    source_sha256: str
    source_bytes: int
    representation: str = 'exomol-two-column-sigma-v1'
    product_kind: str = 'calculated_absorption_cross_section'
    coordinate_kind: str = 'wavenumber'
    coordinate_unit: str = 'cm^-1'
    signal_unit: str = 'cm^2/molecule'


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 2048 and not any(ord(c) < 32 or ord(c) == 127 for c in value)


def parse_cross_section(raw: bytes, provenance: CrossSectionProvenance) -> MolecularCrossSection:
    """Preserve ascending wavenumbers and cross sections, with no resampling.

    Requires explicit product conditions and attribution. It cannot verify the
    supplied temperature/identity or that bytes came from the given source URL.
    Raw bytes must be retained by a future cache alongside this parsed product.
    """
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES:
        raise ReferenceImportError('Require nonempty source bytes within the 1 MiB limit')
    if not isinstance(provenance, CrossSectionProvenance):
        raise ReferenceImportError('Require typed cross-section provenance')
    if not all(_text(v) for v in (provenance.molecule, provenance.isotopologue, provenance.dataset)):
        raise ReferenceImportError('Require molecule, isotopologue and dataset identifiers')
    if not isinstance(provenance.citations, tuple) or not provenance.citations or not all(_text(v) for v in provenance.citations):
        raise ReferenceImportError('Require nonempty citation tuple')
    if provenance.licence_url != LICENCE_URL:
        raise ReferenceImportError('Require the documented ExoMol CC BY-SA 4.0 licence URL')
    try:
        temperature, pressure = provenance.temperature_kelvin, provenance.pressure_bar
        if isinstance(temperature, bool) or isinstance(pressure, bool) or not math.isfinite(temperature) or not math.isfinite(pressure):
            raise ValueError('conditions')
        if temperature <= 0 or pressure != 0 or provenance.broadening != 'doppler_only':
            raise ValueError('conditions')
    except (TypeError, ValueError):
        raise ReferenceImportError('Require positive temperature and explicit zero pressure/Doppler-only conditions') from None
    try:
        url = urlsplit(provenance.source_url)
        if (not _text(provenance.source_url) or url.scheme != 'https' or
            url.hostname not in ('exomol.com', 'www.exomol.com') or url.port not in (None, 443) or
            url.username is not None or url.password is not None or url.fragment):
            raise ValueError('origin')
    except (TypeError, ValueError, AttributeError):
        raise ReferenceImportError('Require an anonymous HTTPS ExoMol source URL') from None
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeError as error:
        raise ReferenceImportError('Require UTF-8 numerical text') from error
    points = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 2:
            raise ReferenceImportError(f'Line {line_number}: require exactly two numerical columns')
        try:
            coordinate, value = map(float, fields)
        except ValueError as error:
            raise ReferenceImportError(f'Line {line_number}: invalid numerical field') from error
        if not math.isfinite(coordinate) or not math.isfinite(value) or coordinate < 0 or value < 0:
            raise ReferenceImportError(f'Line {line_number}: require nonnegative finite wavenumber and cross section')
        if points and coordinate <= points[-1][0]:
            raise ReferenceImportError(f'Line {line_number}: wavenumbers must be strictly increasing')
        points.append((coordinate, value))
        if len(points) > MAX_POINTS:
            raise ReferenceImportError('Cross section exceeds the 10000-point limit')
    if len(points) < 2:
        raise ReferenceImportError('Require at least two cross-section points')
    return MolecularCrossSection(provenance, tuple(points), sha256(raw).hexdigest(), len(raw))
