
import os
from unittest.mock import patch, sentinel

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from ecas.ui.main_window import ECASWindow
from ecas.ui import main_window


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication([])
    widget = ECASWindow()
    yield widget
    widget.close()


def test_schema_selector_defaults_to_generic(window):
    selector = window.spectrum_schema_selector
    assert [selector.itemText(i) for i in range(selector.count())] == [
        "Generic / Unknown", "WASP-39 b Archive"
    ]
    assert selector.currentIndex() == 0
    layout = selector.parentWidget().layout()
    import_button = next(button for button in selector.parentWidget().findChildren(
        main_window.QPushButton) if button.text() == "Import Spectrum")
    assert layout.indexOf(selector) < layout.indexOf(import_button)


@pytest.mark.parametrize('via_dialog', [False, True])
def test_empty_import_error_still_has_visible_explanation(window, tmp_path, via_dialog):
    path = str(tmp_path / 'synthetic.csv')
    with patch.object(window, '_read_spectrum_file', side_effect=main_window.SpectrumImportError()), \
         patch.object(main_window.QFileDialog, 'getOpenFileName', return_value=(path, '')), \
         patch.object(main_window.QMessageBox, 'warning') as warning:
        if via_dialog:
            window._import_csv()
        else:
            window._import_csv_from_path(path)
    warning.assert_called_once()
    assert 'No further error details were provided' in warning.call_args.args[2]
    assert window.current_spectrum is None
    assert window.statusBar().currentMessage() == 'Import failed'


@pytest.mark.parametrize("via_dialog", [False, True])
@pytest.mark.parametrize("schema_index", [0, 1])
def test_selected_schema_reaches_importer_and_display(window, tmp_path, via_dialog, schema_index):
    """Both entry points must use the importer's real keyword contract."""
    path = str(tmp_path / "synthetic.csv")
    window.spectrum_schema_selector.setCurrentIndex(schema_index)
    schema = main_window.WASP39B_SCHEMA if schema_index else None
    with patch.object(main_window, "import_spectrum", autospec=True,
                      return_value=sentinel.spectrum) as importer, \
         patch.object(window, "_display_spectrum") as display, \
         patch.object(main_window.QFileDialog, "getOpenFileName",
                      return_value=(path, "CSV files (*.csv)")):
        if via_dialog:
            window._import_csv()
        else:
            window._import_csv_from_path(path)
    importer.assert_called_once_with(path, archive_schema=schema)
    display.assert_called_once_with(sentinel.spectrum, schema=schema)


def test_cancelled_dialog_preserves_existing_display(window):
    window.spectrum_status.setText("Existing dataset")
    with patch.object(main_window.QFileDialog, "getOpenFileName",
                      return_value=("", "")), \
         patch.object(main_window, "import_spectrum", autospec=True) as importer, \
         patch.object(window, "_clear_spectrum_display") as clear, \
         patch.object(window, "_display_spectrum") as display:
        window._import_csv()
    importer.assert_not_called()
    clear.assert_not_called()
    display.assert_not_called()
    assert window.spectrum_status.text() == "Existing dataset"


@pytest.mark.parametrize("via_dialog", [False, True])
def test_bundled_archive_imports_into_table_and_plot_without_database(window, via_dialog):
    """Exercise the actual file importer and display, not mocked spectrum data."""
    from pathlib import Path
    path = str(Path(__file__).resolve().parents[1] / "data" / "WASP-39b" /
               "table_WASP-39-b-Feinstein-et-al.-2023.csv")
    window.spectrum_schema_selector.setCurrentIndex(1)
    with patch.object(main_window.QMessageBox, "warning") as warning, \
         patch.object(main_window.QFileDialog, "getOpenFileName", return_value=(path, "")):
        if via_dialog:
            window._import_csv()
        else:
            window._import_csv_from_path(path)
    warning.assert_not_called()
    spectrum = window.current_spectrum
    assert spectrum.row_count == 331
    assert window.spectrum_table.rowCount() == 331
    assert window.spectrum_table.columnCount() == 23
    assert window.spectra_plot._current_spectrum is spectrum
    assert spectrum.rows[0]["wavelength"] == spectrum.rows[0]["centralwavelng"]
    assert spectrum.rows[0]["signal"] == spectrum.rows[0]["pl_trandep"]
    assert "Imported 331 measurements" in window.statusBar().currentMessage()


def test_bundled_archive_requires_explicit_schema_in_generic_mode(window):
    from pathlib import Path
    path = Path(__file__).resolve().parents[1] / "data" / "WASP-39b" / "table_WASP-39-b-Feinstein-et-al.-2023.csv"
    with patch.object(main_window.QMessageBox, "warning") as warning:
        window._import_csv_from_path(str(path))
    warning.assert_called_once()
    assert window.current_spectrum is None
    assert window.spectrum_table.rowCount() == 0
    assert window.statusBar().currentMessage() == "Import failed"


@pytest.mark.parametrize("via_dialog", [False, True])
def test_downloaded_nasa_table_displays_source_units_and_metadata(window, via_dialog):
    from pathlib import Path
    path = str(Path(__file__).resolve().parents[1] / "data/NASA/2026-10-27/feinstein-2023.tbl")
    with patch.object(main_window.QMessageBox, "warning") as warning, \
         patch.object(main_window.QFileDialog, "getOpenFileName", return_value=(path, "")):
        if via_dialog:
            window._import_csv()
        else:
            window._import_csv_from_path(path)
    warning.assert_not_called()
    assert window.current_spectrum.row_count == 331
    assert window.spectrum_table.columnCount() == 31
    assert window.current_spectrum.axis_unit == "microns"
    assert window.current_spectrum.signal_unit == "%"
    assert dict(window.current_spectrum_details.metadata)["PL_NAME"] == "WASP-39 b"
    with patch.object(main_window.QMessageBox, "warning"):
        window._import_csv_from_path(str(Path(path).with_name("missing.tbl")))
    assert window.current_spectrum is None
    assert window.current_spectrum_details is None


def test_main_window_has_expected_navigation():
    app = QApplication.instance() or QApplication([])

    window = ECASWindow()

    assert window.windowTitle().startswith("ECAS")
    assert [window.navigation.item(i).text() for i in range(window.navigation.count())] == [
        'Overview', 'Projects', 'Spectral Data', 'Molecular References', 'Comparisons', 'Settings']
    assert window.pages.count() == window.navigation.count()
    for index in range(window.navigation.count()):
        window.navigation.setCurrentRow(index)
        assert window.pages.currentIndex() == index

    window.close()


def test_comparisons_explains_pending_work_and_has_no_reference_controls(window):
    window.navigation.setCurrentRow(4)
    page = window.pages.currentWidget()
    descriptions = ' '.join(label.text() for label in page.findChildren(main_window.QLabel))
    assert 'Select inputs independently' in descriptions
    assert 'No overlay, residual, score or detection is produced' in descriptions
    assert not page.findChildren(main_window.MolecularReferenceBrowser)
    assert window.pages.widget(3).isAncestorOf(window.reference_browser)
    assert window.reference_browser.http is None and window.reference_browser.product_http is None


@pytest.mark.parametrize('via_dialog', [False, True])
def test_generic_csv_uses_manager_and_displays_real_values(window, tmp_path, via_dialog):
    source = tmp_path / 'generic.csv'
    source.write_text('wavelength,signal\n1.0,2.0\n2.0,3.0\n', encoding='utf-8')
    with patch.object(main_window.QMessageBox, 'warning') as warning, \
         patch.object(main_window.QFileDialog, 'getOpenFileName', return_value=(str(source), '')):
        if via_dialog:
            window._import_csv()
        else:
            window._import_csv_from_path(str(source))
    warning.assert_not_called()
    assert window.current_spectrum.rows[0] == {'wavelength': 1.0, 'signal': 2.0}
    assert window.spectrum_table.rowCount() == 2
    assert window.spectra_plot._current_spectrum is window.current_spectrum
    assert window.current_spectrum_details is None


@pytest.mark.parametrize('via_dialog', [False, True])
def test_manager_format_rejection_clears_previous_table_metadata(window, tmp_path, via_dialog):
    from pathlib import Path
    window._import_csv_from_path(str(Path(__file__).resolve().parents[1] /
                                    'data/NASA/2026-10-27/feinstein-2023.tbl'))
    assert window.current_spectrum_details is not None
    source = tmp_path / 'unsupported.txt'
    source.write_text('wavelength,signal\n1.0,2.0\n', encoding='utf-8')
    with patch.object(main_window.QMessageBox, 'warning') as warning, \
         patch.object(main_window.QFileDialog, 'getOpenFileName', return_value=(str(source), '')):
        if via_dialog:
            window._import_csv()
        else:
            window._import_csv_from_path(str(source))
    warning.assert_called_once()
    assert 'only CSV files are supported' in warning.call_args.args[2]
    assert window.current_spectrum is None and window.current_spectrum_details is None
    assert window.spectrum_table.rowCount() == 0
    assert window.spectra_plot._current_spectrum is None


def test_import_csv_displays_warnings_in_status_bar(tmp_path):
    """Test that warnings from spectrum import are shown in status bar."""
    app = QApplication.instance() or QApplication([])
    window = ECASWindow()

    # Create a CSV with missing uncertainty values (generates a warning)
    csv_path = tmp_path / "with_warnings.csv"
    csv_path.write_text(
        "wavelength,signal,uncertainty\n"
        "400,12.5,0.2\n"
        "401,13.1,\n"  # missing uncertainty
        "402,14.0,0.3\n",
        encoding="utf-8",
    )

    window._import_csv_from_path(str(csv_path))

    # Give event loop time for Qt signals to process before asserting
    QApplication.processEvents()

    # Import succeeded - spectrum_status should show loaded info
    assert "Loaded:" in window.spectrum_status.text()

    # Status bar should include the warning about missing uncertainty
    status_text = window.statusBar().currentMessage()
    assert "Imported 3 measurements" in status_text
    assert "missing uncertainty values" in status_text

    window.close()

