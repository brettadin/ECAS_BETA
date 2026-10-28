"""Real offscreen project controls, import, persistence and reopen integration."""
import json
from pathlib import Path
import shutil
import sqlite3
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from ecas.ui.main_window import ECASWindow
from ecas.ingestion.nasa_archive import store_spectrum, spectrum_url, spectra_search

DATA = Path(__file__).resolve().parents[1] / 'data/NASA/2026-10-27'


@pytest.fixture(scope='module', autouse=True)
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


def create(window, name='research'):
    controls = window.project_browser
    controls.name.setText(name)
    controls.create_button.click()
    assert controls.projects.currentText() == name


def test_create_attach_reopen_csv_using_actual_controls(tmp_path):
    root = tmp_path / 'projects'
    source = tmp_path / 'data.csv'
    source.write_text('wavelength,signal\n1,2\n2,3\n', encoding='utf-8')
    window = ECASWindow(projects_dir=root)
    try:
        assert not root.exists()
        assert not window.project_browser.save_button.isEnabled()
        create(window)
        window._import_csv_from_path(str(source))
        original = window.current_spectrum
        window.project_browser.save_button.click()
        assert window.project_browser.spectra.count() == 1
        assert 'Added spectrum' in window.project_browser.status.text()
    finally:
        window.close()
    source.unlink()
    reopened = ECASWindow(projects_dir=root)
    try:
        assert reopened.project_browser.projects.currentText() == 'research'
        reopened.project_browser.spectra.setCurrentRow(0)
        with patch.object(reopened.nasa_browser.http, 'get', side_effect=AssertionError('Unexpected network')):
            reopened.project_browser.open_button.click()
        assert reopened.current_spectrum == original
        assert reopened.spectrum_table.rowCount() == 2
        assert reopened.navigation.currentRow() == 2
        assert reopened.current_project_attachment is not None
        create(reopened, 'copy')
        reopened.project_browser.save_button.click()
        assert reopened.project_browser.spectra.count() == 1
    finally:
        reopened.close()


@pytest.mark.parametrize('schema_index', [0, 1])
def test_cached_nasa_selection_attach_and_reopen_after_cache_removal(tmp_path, schema_index):
    root, cache = tmp_path / 'projects', tmp_path / 'cache'
    metadata = (DATA / 'wasp39b-spectra-metadata.json').read_bytes()
    chosen = next(row for row in json.loads(metadata) if row['bibcode'] == '2023Natur.614..670F')
    source = store_spectrum(cache, chosen, (DATA / 'feinstein-2023.tbl').read_bytes(),
        spectrum_url(b"FF_InitPage('x', '/workspace/TMP_test_123')", chosen),
        {'url': spectra_search('WASP-39 b'), 'raw': metadata})
    window = ECASWindow(projects_dir=root)
    try:
        create(window)
        window.spectrum_schema_selector.setCurrentIndex(schema_index)
        window.nasa_browser.cache_root = cache
        window.nasa_browser.show_cache()
        window.nasa_browser.results.setCurrentRow(0)
        window.nasa_browser.load_selected()
        window.project_browser.save_button.click()
        assert window.project_browser.spectra.count() == 1
    finally:
        window.close()
    assert cache.resolve().is_relative_to(tmp_path.resolve())
    shutil.rmtree(cache)
    reopened = ECASWindow(projects_dir=root)
    try:
        reopened.project_browser.spectra.setCurrentRow(0)
        with patch.object(reopened.nasa_browser.http, 'get', side_effect=AssertionError('Unexpected network')):
            reopened.project_browser.open_button.click()
        assert reopened.current_spectrum.row_count == 331
        assert reopened.current_spectrum.axis_unit == 'microns'
        assert reopened.current_spectrum_details.source_sha256
        assert reopened.spectrum_table.columnCount() == 31
        assert reopened.current_project_attachment['provenance']['cache_record']['metadata']['pl_name'] == 'WASP-39 b'
        assert reopened.current_project_attachment['provenance']['import_schema'] is None
        assert not source.exists()
        saved_item = reopened.project_browser.spectra.item(0)
        assert 'WASP-39 b — Feinstein et al. 2023' in saved_item.text()
        assert '331 rows | source preserved' in saved_item.text()
        assert 'Near Infrared Imager and Slitless Spectrograph' in saved_item.text()
        assert 'Table publication: Feinstein et al. 2022' in saved_item.toolTip()
        assert 'source.tbl' in saved_item.toolTip()
    finally:
        reopened.close()


def test_duplicate_project_and_changed_source_fail_without_losing_display(tmp_path):
    source = tmp_path / 'data.csv'
    source.write_text('wavelength,signal\n1,2\n', encoding='utf-8')
    window = ECASWindow(projects_dir=tmp_path / 'projects')
    try:
        create(window)
        controls = window.project_browser
        controls.name.setText('research')
        controls.create_button.click()
        assert 'failed' in controls.status.text()
        assert controls.projects.count() == 1
        window._import_csv_from_path(str(source))
        original = window.current_spectrum
        source.write_text('wavelength,signal\n1,999\n', encoding='utf-8')
        controls.save_button.click()
        assert 'no longer matches' in controls.status.text()
        assert window.current_spectrum is original
        assert controls.spectra.count() == 0
    finally:
        window.close()


def test_open_revalidates_database_and_refuses_changed_record(tmp_path):
    source = tmp_path / 'data.csv'
    source.write_text('wavelength,signal\n1,2\n', encoding='utf-8')
    window = ECASWindow(projects_dir=tmp_path / 'projects')
    try:
        create(window)
        window._import_csv_from_path(str(source))
        original = window.current_spectrum
        controls = window.project_browser
        controls.save_button.click()
        controls.spectra.setCurrentRow(0)
        with sqlite3.connect(tmp_path / 'projects/research/data.sqlite') as conn:
            data = json.loads(conn.execute('SELECT data FROM spectra').fetchone()[0])
            data['axis_unit'] = 'changed'
            conn.execute('UPDATE spectra SET data = ?', (json.dumps(data),))
        controls.open_button.click()
        assert 'changed' in controls.status.text()
        assert window.current_spectrum is original
    finally:
        window.close()


def test_project_refresh_error_is_visible_and_clears_stale_selection(tmp_path):
    window = ECASWindow(projects_dir=tmp_path / 'projects')
    try:
        create(window)
        controls = window.project_browser
        with patch.object(controls.store, 'projects', side_effect=OSError('synthetic read failure')):
            controls.refresh_button.click()
        assert 'synthetic read failure' in controls.status.text()
        assert controls.projects.count() == 0 and controls.spectra.count() == 0
        assert not controls.open_button.isEnabled() and not controls.save_button.isEnabled()
    finally:
        window.close()


def test_changed_table_header_provenance_cannot_replace_imported_source_silently(tmp_path):
    source = tmp_path / 'source.tbl'
    source.write_bytes((DATA / 'feinstein-2023.tbl').read_bytes())
    window = ECASWindow(projects_dir=tmp_path / 'projects')
    try:
        create(window)
        window._import_csv_from_path(str(source))
        spectrum, details = window.current_spectrum, window.current_spectrum_details
        raw = source.read_bytes()
        changed = raw.replace(b'Feinstein et al. 2022', b'Changed et al. 2026', 1)
        assert changed != raw
        source.write_bytes(changed)
        window.project_browser.save_button.click()
        assert 'Source changed since import' in window.project_browser.status.text()
        assert window.project_browser.spectra.count() == 0
        assert window.current_spectrum is spectrum and window.current_spectrum_details is details
    finally:
        window.close()


def test_deleted_selected_record_reports_actionable_error(tmp_path):
    source = tmp_path / 'data.csv'
    source.write_text('wavelength,signal\n1,2\n', encoding='utf-8')
    window = ECASWindow(projects_dir=tmp_path / 'projects')
    try:
        create(window)
        window._import_csv_from_path(str(source))
        original = window.current_spectrum
        controls = window.project_browser
        controls.save_button.click()
        controls.spectra.setCurrentRow(0)
        with sqlite3.connect(tmp_path / 'projects/research/data.sqlite') as conn:
            conn.execute('DELETE FROM spectra')
        controls.open_button.click()
        assert 'Record no longer exists' in controls.status.text()
        assert 'refresh' in controls.status.text()
        assert window.current_spectrum is original
    finally:
        window.close()


def test_unplottable_saved_record_reports_failure_on_projects_panel(tmp_path):
    from ecas.models.spectrum import SpectrumData
    from ecas.persistence import save_spectrum_to_database

    window = ECASWindow(projects_dir=tmp_path / 'projects')
    try:
        create(window)
        # Legacy rows may legitimately lack numeric plottable measurements.
        spectrum = SpectrumData(tmp_path / 'legacy.csv', ({'label': 'example'},), ('label',))
        save_spectrum_to_database(spectrum, 'research', window.project_store.root)
        controls = window.project_browser
        controls.reload()
        controls.spectra.setCurrentRow(0)
        window.navigation.setCurrentRow(1)
        controls.open_button.click()
        assert 'could not be plotted' in controls.status.text()
        assert window.navigation.currentRow() == 1
        assert window.current_spectrum is None and window.current_project_attachment is None
        assert not controls.save_button.isEnabled()
        assert window.spectrum_table.rowCount() == 0
    finally:
        window.close()


@pytest.mark.parametrize('suffix', ['.csv', '.tbl'])
@pytest.mark.parametrize('error', [PermissionError('synthetic file locked'), FileNotFoundError('synthetic file removed')])
@pytest.mark.parametrize('route', ['dialog', 'path'])
def test_import_file_access_errors_are_wrapped_and_reported(tmp_path, suffix, error, route):
    source = tmp_path / ('data' + suffix)
    source.write_bytes(b'wavelength,signal\n1,2\n')
    window = ECASWindow(projects_dir=tmp_path / 'projects')
    try:
        with patch('pathlib.Path.open', side_effect=error), \
             patch('ecas.ui.main_window.QFileDialog.getOpenFileName', return_value=(str(source), '')), \
             patch('ecas.ui.main_window.QMessageBox.warning') as warning:
            if route == 'dialog':
                window._import_csv()
            else:
                window._import_csv_from_path(str(source))
        warning.assert_called_once()
        assert str(error) in warning.call_args.args[2]
        assert window.statusBar().currentMessage() == 'Import failed'
        assert window.current_spectrum is None
    finally:
        window.close()
