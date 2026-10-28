from pathlib import Path

import pytest

from ecas.ingestion.exomol_catalogue import CatalogueError, parse_catalogue, search_catalogue

SOURCE = Path(__file__).resolve().parents[1] / 'data/ExoMol/2026-10-28/exomol.all'


@pytest.fixture(scope='module')
def catalogue():
    return parse_catalogue(SOURCE.read_bytes())


def test_real_metadata_capture_counts_and_identity(catalogue):
    assert catalogue.source_sha256 == '3bc26ed45c5483839ee7a17ce4b135bdd5b2230147b6c261e07102884ffe646c'
    assert catalogue.version == '20260605'
    assert len(catalogue.entries) == 250
    assert len({e.formula for e in catalogue.entries}) == 102
    assert len({(e.formula, e.isotopologue) for e in catalogue.entries}) == 242
    assert any('20221307' in warning for warning in catalogue.warnings)


def test_provider_name_formula_and_isotope_search(catalogue):
    water = search_catalogue(catalogue, '  WATER  ')
    assert water.formulas == ('H2O',) and water.total_matches == 5
    assert water.entries == search_catalogue(catalogue, 'H2O').entries
    one = search_catalogue(catalogue, '1H2-16O')
    assert one.total_matches == 1
    assert one.entries[0].dataset == 'POKAZATEL'
    assert one.entries[0].definition_url == 'https://www.exomol.com/db/H2O/1H2-16O/POKAZATEL/1H2-16O__POKAZATEL.def'


def test_ambiguous_provider_alias_is_not_silently_resolved(catalogue):
    assert set(search_catalogue(catalogue, 'Phosphine').formulas) == {'PF3', 'PH3'}


def test_multiple_datasets_for_one_isotope_stay_distinct(catalogue):
    result = search_catalogue(catalogue, '12C-16O')
    assert len({e.dataset for e in result.entries}) >= 2
    assert len({e.isotopologue for e in result.entries}) == 1
    assert any(e.version == '20221307' for e in catalogue.entries)


def test_formula_spelling_is_not_case_folded(catalogue):
    assert search_catalogue(catalogue, 'H2O').total_matches == 5
    assert search_catalogue(catalogue, 'h2o').total_matches == 0


def test_complete_miss_and_limit_have_distinct_states(catalogue):
    absent = search_catalogue(catalogue, 'synthetic-nonexistent-molecule')
    assert absent.total_matches == 0 and not absent.truncated
    limited = search_catalogue(catalogue, 'Water', limit=1)
    assert len(limited.entries) == 1 and limited.total_matches == 5 and limited.truncated


@pytest.mark.parametrize('query', ['', None, 'water\n', 'x'*257])
def test_invalid_search_input_rejected(catalogue, query):
    with pytest.raises(CatalogueError):
        search_catalogue(catalogue, query)


@pytest.mark.parametrize('limit', [0, 201, True])
def test_search_bounds(catalogue, limit):
    with pytest.raises(CatalogueError):
        search_catalogue(catalogue, 'Water', limit=limit)


@pytest.mark.parametrize('mutation', ['truncated', 'html', 'count', 'label', 'path', 'encoding', 'oversize', 'trailing'])
def test_malformed_catalogue_is_not_an_empty_search(mutation):
    raw = SOURCE.read_bytes()
    if mutation == 'truncated': raw = raw[:1000]
    elif mutation == 'html': raw = b'<html>temporarily unavailable</html>'
    elif mutation == 'count': raw = raw.replace(b' 250 ', b' 251 ', 1)
    elif mutation == 'label': raw = raw.replace(b'# Iso-slug', b'# Unsupported field', 1)
    elif mutation == 'path': raw = raw.replace(b'27Al-35Cl', b'../secret', 1)
    elif mutation == 'encoding': raw = b'\xff'
    elif mutation == 'oversize': raw = b'x'*1048577
    elif mutation == 'trailing': raw += b'extra # Unexpected\n'
    with pytest.raises(CatalogueError):
        parse_catalogue(raw)
