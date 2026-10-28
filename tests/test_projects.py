"""Project sources/provenance survive loss of original files and cached entries."""
import base64
import json
from pathlib import Path
import shutil
import sqlite3
from unittest.mock import patch

import pytest

from ecas.ingestion.import_manager import import_spectrum
from ecas.ingestion.nasa_archive import store_spectrum, spectrum_url, spectra_search
from ecas.ingestion.nasa_table import import_transmission_table
from ecas.persistence import PersistenceError, save_spectrum_to_database
from ecas.projects import ProjectStore

DATA = Path(__file__).resolve().parents[1] / 'data/NASA/2026-10-27'


def csv_source(tmp_path):
    path = tmp_path / 'spectrum.csv'
    path.write_bytes(b'wavelength,signal\n1,2\n2,3\n')
    return path, import_spectrum(path)


def test_empty_read_has_no_filesystem_side_effect_and_creation_is_exclusive(tmp_path):
    root = tmp_path / 'projects'
    store = ProjectStore(root)
    assert store.projects() == [] and store.spectra('missing') == []
    assert not root.exists()
    store.create('planet_b')
    assert store.projects() == ['planet_b']
    assert store.spectra('planet_b') == []
    with pytest.raises(PersistenceError): store.create('planet_b')


@pytest.mark.parametrize('name', ['', '../outside', 'x/y', 'x\\y', None, 42])
def test_invalid_project_names_rejected(tmp_path, name):
    with pytest.raises(PersistenceError): ProjectStore(tmp_path).create(name)


def test_csv_attachment_reopens_without_original_and_copies_to_another_project(tmp_path):
    source, spectrum = csv_source(tmp_path)
    raw = source.read_bytes()
    store = ProjectStore(tmp_path / 'projects')
    store.create('first')
    identifier = store.attach('first', spectrum)
    source.unlink()
    reopened = ProjectStore(store.root).spectra('first')[0]
    assert reopened.record_id == identifier and reopened.spectrum == spectrum
    assert base64.b64decode(reopened.attachment['source_bytes']) == raw
    assert reopened.details is None
    store.create('second')
    store.attach('second', reopened.spectrum, existing_attachment=reopened.attachment)
    assert store.spectra('second')[0].attachment == reopened.attachment


def test_cached_nasa_provenance_survives_cache_deletion(tmp_path):
    metadata = (DATA / 'wasp39b-spectra-metadata.json').read_bytes()
    chosen = next(row for row in json.loads(metadata) if row['bibcode'] == '2023Natur.614..670F')
    raw = (DATA / 'feinstein-2023.tbl').read_bytes()
    url = spectrum_url(b"FF_InitPage('x', '/workspace/TMP_test_123')", chosen)
    cache = tmp_path / 'cache'
    source = store_spectrum(cache, chosen, raw, url, {'url': spectra_search('WASP-39 b'), 'raw': metadata})
    spectrum = import_transmission_table(source).spectrum
    store = ProjectStore(tmp_path / 'projects')
    store.create('research')
    store.attach('research', spectrum)
    assert cache.resolve().is_relative_to(tmp_path.resolve())
    shutil.rmtree(cache)  # Checked, test-owned temporary fixture only.
    item = ProjectStore(store.root).spectra('research')[0]
    assert item.spectrum == spectrum and item.details.source_sha256
    assert item.details.spectrum.axis_unit == 'microns'
    provenance = item.attachment['provenance']
    assert provenance['cache_record']['source_url'] == url
    assert base64.b64decode(provenance['metadata_bytes']) == metadata
    assert base64.b64decode(item.attachment['source_bytes']) == raw


@pytest.mark.parametrize('target', ['spectrum', 'source', 'provenance'])
def test_changed_saved_data_is_visible_failure(tmp_path, target):
    _, spectrum = csv_source(tmp_path)
    store = ProjectStore(tmp_path / 'projects')
    store.create('research')
    store.attach('research', spectrum)
    with sqlite3.connect(store.root / 'research/data.sqlite') as conn:
        data = json.loads(conn.execute('SELECT data FROM spectra').fetchone()[0])
        if target == 'spectrum': data['rows'][0]['signal'] = 999
        elif target == 'source': data['attachment']['source_bytes'] = 'changed'
        else: data['attachment']['provenance']['original_path'] = 'changed'
        conn.execute('UPDATE spectra SET data = ?', (json.dumps(data),))
    with pytest.raises(PersistenceError): store.spectra('research')


def test_changed_original_is_not_registered_and_legacy_rows_remain_readable(tmp_path):
    source, spectrum = csv_source(tmp_path)
    store = ProjectStore(tmp_path / 'projects')
    store.create('research')
    source.write_text('wavelength,signal\n1,999\n', encoding='utf-8')
    with pytest.raises(PersistenceError): store.attach('research', spectrum)
    assert store.spectra('research') == []
    save_spectrum_to_database(spectrum, 'research', store.root)
    legacy = store.spectra('research')[0]
    assert legacy.spectrum == spectrum and legacy.attachment is None


def test_failed_database_insert_does_not_register_partial_attachment(tmp_path):
    _, spectrum = csv_source(tmp_path)
    store = ProjectStore(tmp_path / 'projects')
    store.create('research')
    with sqlite3.connect(store.root / 'research/data.sqlite') as conn:
        conn.execute("CREATE TRIGGER fail_insert BEFORE INSERT ON spectra BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END")
    with pytest.raises(PersistenceError): store.attach('research', spectrum)
    assert store.spectra('research') == []


def test_linked_project_root_rejected(tmp_path):
    with patch.object(Path, 'is_symlink', return_value=True):
        with pytest.raises(PersistenceError): ProjectStore(tmp_path)


def test_multiple_attachments_keep_stable_ids_and_size_failure_adds_no_record(tmp_path):
    source, first = csv_source(tmp_path)
    store = ProjectStore(tmp_path / 'projects')
    store.create('research')
    one = store.attach('research', first)
    second_path = tmp_path / 'second.csv'
    second_path.write_text('wavelength,signal\n3,4\n', encoding='utf-8')
    second = import_spectrum(second_path)
    two = store.attach('research', second)
    assert one != two
    assert [(r.record_id, r.spectrum) for r in store.spectra('research')] == [(one, first), (two, second)]
    with patch('ecas.projects.MAX_SOURCE_BYTES', 8):
        with pytest.raises(PersistenceError): store.attach('research', first)
    assert [r.record_id for r in store.spectra('research')] == [one, two]
