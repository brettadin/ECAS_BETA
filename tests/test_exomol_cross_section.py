"""Synthetic only: no provider product downloaded or scientifically validated."""
from dataclasses import replace
from hashlib import sha256

import pytest

from ecas.ingestion.exomol_cross_section import (
    CrossSectionProvenance, LICENCE_URL, MAX_BYTES, ReferenceImportError, parse_cross_section,
)


def provenance():
    return CrossSectionProvenance('CO2', '12C-16O2', 'synthetic-not-provider-data',
        500., 0., 'doppler_only', 'https://www.exomol.com/synthetic-not-a-download.sigma',
        ('Synthetic fixture; not a real molecular spectrum',), LICENCE_URL)


def test_explicit_reference_representation_preserves_raw_identity_and_conditions():
    raw = b'1000 0\n1001 2e-21\n1002 3e-21\n'
    result = parse_cross_section(raw, provenance())
    assert result.points == ((1000., 0.), (1001., 2e-21), (1002., 3e-21))
    assert result.source_sha256 == sha256(raw).hexdigest()
    assert result.source_bytes == len(raw) and result.provenance == provenance()
    assert result.coordinate_kind == 'wavenumber'
    assert result.signal_unit == 'cm^2/molecule'
    assert result.product_kind == 'calculated_absorption_cross_section'
    assert not hasattr(result, 'spectrum')  # cannot silently enter transit-depth workflow


@pytest.mark.parametrize('raw', [b'1\n2\n', b'1 2 3\n2 3 4', b'-1 1\n1 2',
    b'1 -1\n2 2', b'1 nan\n2 2', b'1 2\n1 3', b'2 2\n1 3', b'1 2',
    b'abc 2\n2 3', b'1 inf\n2 3', b'\xff', b'', pytest.param(b' '* (MAX_BYTES+1), id='oversized')])
def test_unsupported_or_invalid_sources_rejected_without_guessing(raw):
    with pytest.raises(ReferenceImportError):
        parse_cross_section(raw, provenance())


@pytest.mark.parametrize('changes', [
    {'temperature_kelvin': None}, {'temperature_kelvin': 0}, {'temperature_kelvin': True},
    {'pressure_bar': 1.}, {'broadening': 'air'}, {'molecule': ''}, {'isotopologue': None},
    {'citations': ()}, {'licence_url': 'unknown'}, {'source_url': 'file:///tmp/reference'},
    {'source_url': 'https://name:secret@www.exomol.com/file'},
    {'source_url': 'https://www.exomol.com.evil.test/file'},
])
def test_required_conditions_and_provenance_are_not_defaulted(changes):
    with pytest.raises(ReferenceImportError):
        parse_cross_section(b'1000 1e-21\n1001 2e-21', replace(provenance(), **changes))


def test_point_limit_is_enforced():
    raw = ''.join(f'{i+1} 0\n' for i in range(10001)).encode()
    with pytest.raises(ReferenceImportError, match='point limit'):
        parse_cross_section(raw, provenance())


def test_zero_wavenumber_is_preserved_without_reciprocal_conversion():
    assert parse_cross_section(b'0 0\n1 1e-21', provenance()).points[0] == (0., 0.)
