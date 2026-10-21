
import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

from ecas.ui.main_window import ECASWindow


def test_main_window_has_expected_navigation():
    app = QApplication.instance() or QApplication([])

    window = ECASWindow()

    assert window.windowTitle().startswith("ECAS")
    assert window.navigation.count() == 5
    assert window.pages.count() == 5

    window.close()


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

