"""Integration checks for workspace guidance and the shared CSV preference."""
from pathlib import Path
from unittest.mock import patch, sentinel

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QScrollArea

from ecas.ui import main_window
from ecas.ui.main_window import ECASWindow
from ecas.ingestion.exomol_product import ProductRequest, validate_product
from ecas.ingestion.exomol_product_network import RetrievedCrossSection
from ecas.ingestion.exomol_reference_cache import store_reference


@pytest.fixture(scope='session', autouse=True)
def app():
    instance = QApplication.instance() or QApplication([])
    yield instance


@pytest.fixture
def window(tmp_path, app):
    widget = ECASWindow(projects_dir=tmp_path / 'projects', reference_cache_dir=tmp_path / 'cache')
    yield widget
    widget.close()


def test_overview_shortcuts_preserve_independent_loaded_inputs(window, tmp_path):
    source = tmp_path / 'observation.csv'
    source.write_text('wavelength,signal\n1,2\n2,3\n', encoding='utf-8')
    window._import_csv_from_path(str(source))
    observation = window.current_spectrum
    window.comparison_browser.add_current_observation()
    root = Path(__file__).resolve().parents[1]
    raw = (root / 'data/ExoMol/2026-10-28/CO2-12C-16O2-500K-4000-4010-dnu1.sigma').read_bytes()
    request = ProductRequest(4000, 4010, 500, '1')
    reference = RetrievedCrossSection(request, raw, validate_product(raw, request))
    window.reference_browser._show_reference(reference)
    store_reference(window.reference_browser.cache_root / 'references', reference)
    window.comparison_browser.refresh_references()
    window.comparison_browser.reference_selector.setCurrentIndex(0)
    snapshot = window.comparison_browser.current_observation
    source.unlink()
    for index, button in window.overview_page.shortcuts.items():
        window.navigation.setCurrentRow(index)
        window.navigation.setCurrentRow(0)
        button.click()
        assert window.navigation.currentRow() == index
        assert window.pages.currentIndex() == index
    window.navigation.setCurrentRow(0)
    summary = window.overview_page.status.text()
    assert 'observation.csv — 2 rows' in summary
    assert 'CO2 / UCL-4000; 500 K; 11 points' in summary
    assert '1 session observation choices; observation selected; reference selected' in summary
    assert window.current_spectrum is observation
    assert window.comparison_browser.current_observation is snapshot
    assert window.comparison_browser.current_reference == reference
    assert window.reference_browser.current_reference is reference
    assert window.reference_browser.http is None and window.reference_browser.product_http is None
    window._clear_spectrum_display()
    window.navigation.setCurrentRow(2)
    window.navigation.setCurrentRow(0)
    assert 'Current observation: none loaded' in window.overview_page.status.text()
    assert '1 session observation choices; observation selected' in window.overview_page.status.text()


@pytest.mark.parametrize('via_dialog', [False, True])
def test_settings_csv_choice_reaches_existing_import_dispatch(window, tmp_path, via_dialog):
    window.settings_page.csv_schema.setCurrentIndex(1)
    assert window.spectrum_schema_selector.currentIndex() == 1
    source = str(tmp_path / 'test.csv')
    with patch.object(main_window, 'import_spectrum', return_value=sentinel.spectrum) as importer, \
         patch.object(window, '_display_spectrum') as display, \
         patch.object(main_window.QFileDialog, 'getOpenFileName', return_value=(source, '')):
        if via_dialog:
            window._import_csv()
        else:
            window._import_csv_from_path(source)
    importer.assert_called_once_with(source, archive_schema=main_window.WASP39B_SCHEMA)
    display.assert_called_once_with(sentinel.spectrum, schema=main_window.WASP39B_SCHEMA)
    window.spectrum_schema_selector.setCurrentIndex(0)
    assert window.settings_page.csv_schema.currentIndex() == 0


def test_settings_paths_and_navigation_do_not_scan_or_write_data(window, tmp_path):
    files_before = sorted(tmp_path.rglob('*'))
    fields = window.settings_page.location_fields
    assert fields['Research projects'].text() == str(window.project_store.root.absolute())
    assert fields['NASA cache'].text() == str(window.nasa_browser.cache_root.absolute())
    assert fields['ExoMol catalogue cache'].text() == str(window.reference_browser.cache_root.absolute())
    assert fields['ExoMol reference cache'].text() == str((window.reference_browser.cache_root / 'references').absolute())
    assert all(field.isReadOnly() for field in fields.values())
    with patch.object(window.project_store, 'projects') as projects, \
         patch('ecas.ui.molecular_browser.cached_references') as cache, \
         patch('ecas.ui.comparison_browser.cached_references') as comparison_cache:
        window.navigation.setCurrentRow(5)
        window.navigation.setCurrentRow(0)
        projects.assert_not_called()
        cache.assert_not_called()
        comparison_cache.assert_not_called()
    assert sorted(tmp_path.rglob('*')) == files_before
    assert window.current_spectrum is None
    assert 'none loaded' in window.overview_page.status.text()
    assert window.overview_page.status.textFormat() == Qt.TextFormat.PlainText
    assert isinstance(window.pages.widget(0), QScrollArea)
    assert isinstance(window.pages.widget(5), QScrollArea)


def test_csv_preference_does_not_reinterpret_loaded_table_or_persist(window, tmp_path):
    root = Path(__file__).resolve().parents[1]
    window.settings_page.csv_schema.setCurrentIndex(1)
    window._import_csv_from_path(str(root / 'data/NASA/2026-10-27/feinstein-2023.tbl'))
    observation, details = window.current_spectrum, window.current_spectrum_details
    assert details is not None
    window.settings_page.csv_schema.setCurrentIndex(0)
    assert window.current_spectrum is observation and window.current_spectrum_details is details
    window.settings_page.csv_schema.setCurrentIndex(1)
    reopened = ECASWindow(projects_dir=tmp_path / 'projects', reference_cache_dir=tmp_path / 'cache')
    try:
        assert reopened.settings_page.csv_schema.currentIndex() == 0
        assert reopened.spectrum_schema_selector.currentIndex() == 0
    finally:
        reopened.close()
