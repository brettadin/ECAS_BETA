"""Captured NASA alias responses and explicit malformed derivatives; no network."""
import json
from pathlib import Path

import pytest

from ecas.ingestion.nasa_aliases import alias_search, parse_aliases
from ecas.ingestion.nasa_archive import allowed_url, parse_spectra

DATA = Path(__file__).resolve().parents[1] / 'data/NASA/2026-10-28'


@pytest.mark.parametrize('label,name', [('long-name','55 Cancri e'), ('short-name','55 Cnc e')])
def test_captured_cancri_aliases_query_canonical_identity_and_preserve_inventory(label, name):
    capture = DATA / 'cancri-investigation'
    canonical = parse_aliases((capture / (label+'-aliases.json')).read_bytes(), name)
    assert canonical == '55 Cnc e'
    rows = parse_spectra((capture / 'canonical-spectra.json').read_bytes(), canonical)
    assert len(rows) == 23
    assert sum(row['spec_type']=='Transmission' for row in rows) == 4
    assert sum(row['spec_type']=='Eclipse' for row in rows) == 19
    # The spectroscopy table itself is exact-name; aliases must be resolved first.
    assert parse_spectra((capture / 'long-name-direct-spectra.json').read_bytes(), name) == []


@pytest.mark.parametrize('label,name,canonical,count', [
    ('wasp', 'WASP39b', 'WASP-39 b', 31),
    ('trappist', 'TRAPPIST-1e', 'TRAPPIST-1 e', 6),
    ('kepler', 'Kepler-452b', 'Kepler-452 b', 0),
    ('proxima', 'Proxima Centauri b', 'Proxima Cen b', 0),
])
def test_real_resolution_distinguishes_planet_identity_from_spectrum_availability(label, name, canonical, count):
    assert allowed_url(alias_search(name))
    assert parse_aliases((DATA / (label + '-aliases.json')).read_bytes(), name) == canonical
    assert len(parse_spectra((DATA / (label + '-spectra.json')).read_bytes(), canonical)) == count


@pytest.mark.parametrize('mutation', ['unresolved', 'host', 'ambiguous', 'wrong-request', 'wrong-identity'])
def test_no_silent_host_or_other_planet_selection(mutation):
    data = json.loads((DATA / 'wasp-aliases.json').read_bytes())
    planet = data['system']['objects']['planet_set']['planets']['WASP-39 b']
    if mutation == 'unresolved': data['manifest']['lookup_status'] = 'ERROR'
    elif mutation == 'host': planet.pop('requested_object')
    elif mutation == 'ambiguous':
        data['system']['objects']['planet_set']['planets']['other b'] = planet
    elif mutation == 'wrong-request': data['manifest']['requested_name'] = 'other b'
    else: data['manifest']['resolved_name'] = 'other b'
    with pytest.raises(ValueError): parse_aliases(json.dumps(data).encode(), 'WASP39b')


@pytest.mark.parametrize('raw', [b'', b'{}', b'[]', b'<html>error</html>', b'{"manifest":1,"manifest":2}', b'x' * 1048577])
def test_malformed_alias_response_is_an_error(raw):
    with pytest.raises(ValueError): parse_aliases(raw, 'WASP39b')
