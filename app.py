
import sys

from PySide6.QtWidgets import QApplication

from ecas.ui.main_window import ECASWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ECAS")

    window = ECASWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
