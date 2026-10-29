"""Project presentation preserves independently attributed saved facts."""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import pytest

from ecas.models.spectrum import SpectrumData
from ecas.projects import ProjectSpectrum, ProjectStore
from ecas.ingestion.import_manager import import_spectrum
from ecas.ui.project_labels import project_label


def record(attachment=None):
    spectrum = SpectrumData(Path('missing/source.tbl'),
        ({'wavelength': 2., 'signal': 1.}, {'wavelength': 3., 'signal': 2.}),
        ('wavelength', 'signal'), axis_unit='microns', signal_type='Transmission')
    return ProjectSpectrum(7, spectrum, attachment)


def test_archive_heading_keeps_conflicting_table_facts_and_does_not_read_files():
    item = record({'source_sha256': 'a' * 64, 'provenance': {
        'cache_record': {'metadata': {'pl_name': 'WASP-39 b', 'authors': 'Feinstein et al. 2023',
            'instrument': 'NIRISS', 'facility': 'JWST', 'bibcode': '2023Natur.614..670F',
            'minwavelng': .631, 'maxwavelng': 2.7965}},
        'table_metadata': (('PL_NAME', 'WASP-39 b'), ('REFERENCE', 'Feinstein et al. 2022'),
                           ('INSTRUMENT', 'Near Infrared Imager and Slitless Spectrograph'))}})
    original = deepcopy(item)
    with patch.object(Path, 'open', side_effect=AssertionError('Unexpected file access')):
        label, tooltip = project_label(item)
    assert '7: WASP-39 b — Feinstein et al. 2023' in label
    assert 'NIRISS | Transmission | 2 rows | source preserved' in label
    assert 'Archive publication: Feinstein et al. 2023' in tooltip
    assert 'Table publication: Feinstein et al. 2022' in tooltip
    assert 'neither was corrected' in tooltip
    assert 'Archive facility: JWST' in tooltip
    assert '2023Natur.614..670F' in tooltip
    assert 'Imported wavelength range: 2–3 (microns)' in tooltip
    assert 'a' * 64 in tooltip
    assert item == original


def test_local_table_uses_saved_header_without_claiming_archive_metadata():
    item = record({'provenance': {'table_metadata': (('PL_NAME', 'WASP-39 b'),
                   ('REFERENCE', 'Local paper 2022'), ('INSTRUMENT', 'NIRISS'))}})
    label, tooltip = project_label(item)
    assert 'WASP-39 b — Local paper 2022' in label and 'NIRISS' in label
    assert 'Table publication: Local paper 2022' in tooltip
    assert 'Archive publication' not in tooltip


@pytest.mark.parametrize('attachment', [None, {}, {'provenance': {}},
    {'provenance': {'table_metadata': None, 'cache_record': None}},
    {'provenance': {'cache_record': {'metadata': {'authors': None, 'instrument': 42}}}}])
def test_missing_descriptions_fall_back_to_filename(attachment):
    item = record(attachment)
    item = replace(item, spectrum=replace(item.spectrum, axis_unit=None, signal_type=None))
    label, tooltip = project_label(item)
    assert label.startswith('7: source.tbl\n2 rows | ')
    assert ('legacy: no source attachment' in label) == (attachment is None)
    assert 'unit not established' in tooltip
    assert 'Archive publication:' not in tooltip and 'Table publication:' not in tooltip


def test_tooltip_escapes_provider_markup_and_record_ids_distinguish_duplicates():
    item = record({'provenance': {'cache_record': {'metadata': {'authors': '<img src=x> & paper'}}}})
    label, tooltip = project_label(item)
    assert '<img src=x>' in label  # QListWidget item text is plain text.
    assert '&lt;img src=x&gt; &amp; paper' in tooltip and '<img src=x>' not in tooltip
    assert project_label(replace(item, record_id=8))[0] != label


def test_generic_csv_label_survives_offline_reopen_without_database_rewrite(tmp_path):
    source = tmp_path / 'observation.csv'
    source.write_bytes(b'wavelength,signal\n1,2\n2,3\n')
    spectrum = import_spectrum(source)
    store = ProjectStore(tmp_path / 'projects')
    store.create('research')
    store.attach('research', spectrum)
    database = store.root / 'research/data.sqlite'
    before = database.read_bytes()
    initial = project_label(store.spectra('research')[0])
    source.unlink()
    assert project_label(ProjectStore(store.root).spectra('research')[0]) == initial
    assert 'observation.csv' in initial[0] and 'unit not established' in initial[1]
    assert database.read_bytes() == before
