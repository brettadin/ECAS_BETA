from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ecas.ui.source_links import source_link
from ecas.ui.main_window import ECASWindow


@pytest.mark.parametrize('value', [None, 42, 'file:///C:/private', 'javascript:alert(1)',
                                  '//example.org/file', 'https://name:secret@example.org/',
                                  'https://[invalid', 'https://example.org/\npath'])
def test_unsupported_or_credentialed_links_not_openable(value):
    assert source_link(value, nasa_source=True) is None


def test_relative_links_require_nasa_context_and_preserve_absolute_citations():
    relative = '/docs/atmospheres/atmospheres_calc.html'
    assert source_link(relative) is None
    assert source_link(relative, nasa_source=True) == 'https://exoplanetarchive.ipac.caltech.edu' + relative
    absolute = 'https://ui.adsabs.harvard.edu/abs/example/abstract'
    assert source_link(absolute) == absolute


def test_actual_table_links_are_presentation_only_and_open_on_explicit_action(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = ECASWindow(projects_dir=tmp_path / 'projects')
    try:
        source = Path(__file__).resolve().parents[1] / 'data/NASA/2026-10-27/feinstein-2023.tbl'
        with patch('ecas.ui.main_window.QDesktopServices.openUrl') as opened:
            window._import_csv_from_path(str(source))
            opened.assert_not_called()
            spectrum = window.current_spectrum
            raw = spectrum.rows[0]['pl_ratror_url']
            item = window.spectrum_table.item(0, spectrum.columns.index('pl_ratror_url'))
            assert item.text() == 'https://exoplanetarchive.ipac.caltech.edu' + raw
            assert raw in item.toolTip()
            assert item.data(Qt.ItemDataRole.UserRole) == item.text()
            window.spectrum_table.itemDoubleClicked.emit(item)
            opened.assert_called_once()
            assert opened.call_args.args[0].toString() == item.text()
            assert spectrum.rows[0]['pl_ratror_url'] == raw
        with patch('ecas.ui.main_window.QDesktopServices.openUrl', return_value=False):
            window._open_source_link(item)
        assert 'Could not open' in window.statusBar().currentMessage()
    finally:
        window.close()
