
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


class ECASWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ECAS — Exoplanetary Characterization & Astrochemistry Suite")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #20242b;
                color: #d8dee9;
                font-family: "Segoe UI";
                font-size: 10pt;
            }

            QListWidget {
                background-color: #181b21;
                border: none;
                padding: 8px;
                outline: none;
            }

            QListWidget::item {
                padding: 12px;
                border-radius: 4px;
            }

            QListWidget::item:selected {
                background-color: #394352;
                color: #ffffff;
            }

            QLabel#pageTitle {
                font-size: 20pt;
                font-weight: 600;
                color: #eceff4;
            }

            QLabel#subtitle {
                color: #9aa6b5;
                font-size: 10pt;
            }
        """)

        self.navigation = QListWidget()
        self.navigation.addItems([
            "Overview",
            "Projects",
            "Spectral Data",
            "Comparisons",
            "Settings",
        ])
        self.navigation.setFixedWidth(200)

        self.pages = QStackedWidget()

        page_definitions = [
            ("Overview", "ECAS workspace", "Scientific analysis workspace."),
            ("Projects", "Projects", "Create and manage research projects."),
            ("Spectral Data", "Spectral Data", "Import and inspect spectral datasets."),
            ("Comparisons", "Comparisons", "Configure and review spectral comparisons."),
            ("Settings", "Settings", "Application preferences and data locations."),
        ]

        for title, heading, description in page_definitions:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(32, 28, 32, 28)
            layout.setSpacing(12)

            heading_label = QLabel(heading)
            heading_label.setObjectName("pageTitle")

            description_label = QLabel(description)
            description_label.setObjectName("subtitle")
            description_label.setWordWrap(True)

            layout.addWidget(heading_label)
            layout.addWidget(description_label)
            layout.addStretch()

            self.pages.addWidget(page)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        content_layout.addWidget(self.pages)

        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        from PySide6.QtWidgets import QHBoxLayout

        horizontal_layout = QHBoxLayout()
        horizontal_layout.setContentsMargins(0, 0, 0, 0)
        horizontal_layout.setSpacing(0)
        horizontal_layout.addWidget(self.navigation)
        horizontal_layout.addWidget(content, 1)

        body_layout.addLayout(horizontal_layout)
        self.setCentralWidget(body)

        self.navigation.currentRowChanged.connect(
            self.pages.setCurrentIndex
        )
        self.navigation.setCurrentRow(0)

        self.statusBar().showMessage("Ready — no dataset loaded")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ECAS")

    window = ECASWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
