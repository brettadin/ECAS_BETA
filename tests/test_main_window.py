
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
