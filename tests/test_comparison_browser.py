"""Offline input selection and scientific boundary regressions using real widgets."""
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from ecas.ui.main_window import ECASWindow
from ecas.ui import molecular_browser
from ecas.ingestion.exomol_product import ProductRequest, validate_product
from ecas.ingestion.exomol_product_network import RetrievedCrossSection
from ecas.ingestion.exomol_reference_cache import store_reference

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='session', autouse=True)
def app():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def window(tmp_path, app):
    widget = ECASWindow(projects_dir=tmp_path / 'projects', reference_cache_dir=tmp_path / 'cache')
    yield widget
    widget.close()


def cache_reference(window):
    request = ProductRequest(4000, 4010, 500, '1')
    raw = (ROOT / 'data/ExoMol/2026-10-28/CO2-12C-16O2-500K-4000-4010-dnu1.sigma').read_bytes()
    result = RetrievedCrossSection(request, raw, validate_product(raw, request))
    path = store_reference(window.reference_browser.cache_root / 'references', result)
    return path, result


def import_csv(window, tmp_path, name, signal):
    source = tmp_path / name
    source.write_text(f'wavelength,signal\n1,{signal}\n2,3\n', encoding='utf-8')
    window._import_csv_from_path(str(source))
    return window.current_spectrum


def test_independent_selection_preserves_original_values_and_main_display(window, tmp_path):
    browser = window.comparison_browser
    first = import_csv(window, tmp_path, 'first.csv', 2)
    browser.add_current_observation()
    second = import_csv(window, tmp_path, 'second.csv', 9)
    browser.add_current_observation()
    browser.observation_selector.setCurrentIndex(0)
    path, result = cache_reference(window)
    with patch.object(molecular_browser, 'PublicExomolCatalogueHttp') as catalogue, \
         patch.object(molecular_browser, 'PublicExomolProductHttp') as product:
        browser.refresh_references()
        assert browser.reference_selector.currentIndex() == -1  # explicit choice
        browser.reference_selector.setCurrentIndex(0)
        for page in (4, 3, 2, 4):
            window.navigation.setCurrentRow(page)
        catalogue.assert_not_called()
        product.assert_not_called()
    assert browser.current_observation == first and browser.current_observation is not first
    assert browser.current_reference == result
    assert browser.observation_table.item(0, 1).text() == '2.0'
    assert browser.reference_table.item(0, 0).text() == '4000.0'
    assert window.current_spectrum is second
    assert window.spectra_plot._current_spectrum is second
    assert window.reference_browser.current_reference is None
    assert 'Comparison blocked' in browser.compatibility.text()
    assert 'units are unknown' in browser.compatibility.text()
    assert 'physical model' in browser.compatibility.text()
    assert result.raw == (ROOT / 'data/ExoMol/2026-10-28/CO2-12C-16O2-500K-4000-4010-dnu1.sigma').read_bytes()


def test_snapshot_survives_source_removal_failed_import_and_no_current_input(window, tmp_path):
    browser = window.comparison_browser
    original = import_csv(window, tmp_path, 'original.csv', 2)
    browser.add_current_observation()
    original.source_file.unlink()
    with patch('ecas.ui.main_window.QMessageBox.warning'):
        window._import_csv_from_path(str(tmp_path / 'absent.csv'))
    browser.add_current_observation()
    assert browser.observation_selector.count() == 1
    assert browser.current_observation == original
    assert browser.observation_table.rowCount() == 2
    assert 'Previous selection retained' in browser.observation_status.text()


@pytest.mark.parametrize('damage', ['corrupt', 'delete'])
def test_invalidated_cache_clears_reference_and_prevents_stale_inspection(window, damage):
    browser = window.comparison_browser
    path, result = cache_reference(window)
    browser.refresh_references()
    browser.reference_selector.setCurrentIndex(0)
    assert browser.current_reference == result
    if damage == 'corrupt':
        path.write_text('{}', encoding='utf-8')
    else:
        path.unlink()
    browser._select_reference()  # re-read at use, not just at discovery
    assert browser.current_reference is None
    assert browser.reference_table.rowCount() == 0
    assert 'unavailable or invalid' in browser.reference_status.text()
    browser.refresh_references()
    assert browser.reference_selector.count() == 0
    assert ('1 invalid' if damage == 'corrupt' else '0 invalid') in browser.cache_status.text()
    assert browser.reference_status.toolTip() == ''


def test_refresh_preserves_independent_choices_and_reports_empty_cache(window, tmp_path):
    browser = window.comparison_browser
    browser.refresh_references()
    assert '0 cached references' in browser.cache_status.text()
    import_csv(window, tmp_path, 'generic.csv', 2)
    browser.add_current_observation()
    observation = browser.current_observation
    first, _ = cache_reference(window)
    browser.refresh_references()
    browser.reference_selector.setCurrentIndex(0)
    second, _ = cache_reference(window)
    browser.refresh_references()
    assert browser.reference_selector.count() == 2
    assert browser.reference_selector.currentData() == str(first)
    assert browser.current_observation is observation
    labels = [browser.reference_selector.itemText(i) for i in range(2)]
    assert len(set(labels)) == 2


def test_transmission_metadata_and_hash_are_preserved_without_claiming_eligibility(window):
    source = ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl'
    before = source.read_bytes()
    window._import_csv_from_path(str(source))
    browser = window.comparison_browser
    browser.add_current_observation()
    source_hash = window.current_spectrum_details.source_sha256
    assert source_hash in browser.observation_status.toolTip()
    assert source_hash[:32] + '\n' + source_hash[32:] in browser.observation_status.text()
    assert 'Transmission' in browser.observation_status.text()
    cache_reference(window)
    browser.refresh_references()
    browser.reference_selector.setCurrentIndex(0)
    assert 'cannot be compared directly without a physical model' in browser.compatibility.text()
    assert 'instrument response evidence' in browser.compatibility.text()
    assert browser.current_observation.rows == window.current_spectrum.rows
    assert source.read_bytes() == before
