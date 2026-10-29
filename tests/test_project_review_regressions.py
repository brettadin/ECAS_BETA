"""Storage review regressions: snapshots, selective reads and portable v1 hashes."""
from contextlib import closing
from dataclasses import replace
import json
from pathlib import PurePosixPath, PureWindowsPath
import sqlite3
from unittest.mock import patch

import pytest

from ecas import persistence
from ecas.ingestion.import_manager import import_spectrum
from ecas.projects import ProjectStore, _digest


def csv_source(tmp_path):
    source = tmp_path / 'spectrum.csv'
    source.write_bytes(b'wavelength,signal\n1,2\n2,3\n')
    return source, import_spectrum(source)


def test_record_reads_keep_snapshot_during_concurrent_delete(tmp_path):
    _, spectrum = csv_source(tmp_path)
    store = ProjectStore(tmp_path / 'projects')
    store.create('research')
    identifier = store.attach('research', spectrum)
    connect = sqlite3.connect
    writer = connect(store.root / 'research/data.sqlite')
    writer.execute('PRAGMA journal_mode=WAL')

    class Cursor:
        def __init__(self, cursor): self.cursor = cursor
        def fetchall(self):
            rows = self.cursor.fetchall()
            writer.execute('DELETE FROM spectra WHERE id = ?', (identifier,))
            writer.commit()
            return rows

    class Reader:
        def __init__(self, *args, **kwargs): self.conn = connect(*args, **kwargs)
        def execute(self, sql, args=()):
            cursor = self.conn.execute(sql, args)
            return Cursor(cursor) if sql.startswith('SELECT id, length') else cursor
        def close(self): self.conn.close()

    try:
        with patch('ecas.persistence.sqlite3.connect', Reader):
            loaded = store.spectra('research')
        assert [item.record_id for item in loaded] == [identifier]
        assert loaded[0].spectrum == spectrum
        assert store.spectra('research') == []
    finally:
        writer.close()


def test_index_read_only_parses_selected_row_and_keeps_id_order(tmp_path):
    _, spectrum = csv_source(tmp_path)
    root = tmp_path / 'projects'
    persistence.save_spectrum_to_database(spectrum, 'research', root)
    persistence.save_spectrum_to_database(spectrum, 'research', root)
    database = root / 'research/data.sqlite'
    with closing(sqlite3.connect(database)) as conn:
        with conn:
            conn.execute("UPDATE spectra SET data = 'invalid JSON' WHERE id = 1")
    # An unrelated malformed row must not be fetched or parsed.
    assert persistence.load_spectrum_by_index('research', root, 1) == spectrum
    assert persistence.load_spectrum_by_index('research', root, 2) is None
    assert persistence.load_spectrum_by_index('research', root, -1) is None
    assert persistence.load_spectrum_by_index('missing', root, 0) is None
    assert not (root / 'missing').exists()


@pytest.mark.parametrize(('saved_path', 'destination_path'), [
    ('/observations/planet.csv', PureWindowsPath),
    (r'C:\observations\planet.csv', PurePosixPath),
])
def test_v1_path_spelling_verified_before_platform_conversion_and_copy(tmp_path, saved_path, destination_path):
    _, spectrum = csv_source(tmp_path)
    store = ProjectStore(tmp_path / 'projects')
    store.create('first')
    store.create('second')
    store.attach('first', spectrum)
    database = store.root / 'first/data.sqlite'
    with closing(sqlite3.connect(database)) as conn:
        with conn:
            data = json.loads(conn.execute('SELECT data FROM spectra').fetchone()[0])
            data['source_file'] = saved_path
            unsigned = {k: v for k, v in data['attachment'].items() if k != 'integrity_sha256'}
            data['attachment']['integrity_sha256'] = _digest(spectrum, unsigned, source_file=saved_path)
            conn.execute('UPDATE spectra SET data = ?', (json.dumps(data),))
    convert = persistence._to_spectrums_dict

    def on_destination(data):
        return replace(convert(data), source_file=destination_path(data['source_file']))

    with patch('ecas.persistence._to_spectrums_dict', on_destination):
        loaded = store.spectra('first')[0]
        store.attach('second', loaded.spectrum, existing_attachment=loaded.attachment)
        copied = store.spectra('second')[0]
    assert copied.spectrum == loaded.spectrum
    assert copied.attachment == loaded.attachment
    # Adapting the in-memory envelope must not rewrite the original database.
    with closing(sqlite3.connect(database)) as conn:
        assert json.loads(conn.execute('SELECT data FROM spectra').fetchone()[0]) == data
