
"""
ECAS main application window.

This module is responsible for the desktop interface: navigation, page layouts,
and presenting imported spectral data. The actual CSV parsing and validation
are handled by ecas.ingestion.csv_importer so that scientific data processing
does not become tied to the user interface.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Reuse the ingestion module rather than duplicating CSV validation here.
# SpectrumImportError represents an expected problem with the input file.
from ecas.ingestion.csv_importer import (
    SpectrumImportError,
    import_spectrum_csv,
)


class ECASWindow(QMainWindow):
    """Main ECAS window and coordinator for its interface."""

    def __init__(self):
        """Initialize the window, navigation, pages, and status bar."""
        super().__init__()

        # Window identity and initial dimensions.
        # The minimum size prevents the interface from becoming too cramped.
        self.setWindowTitle(
            "Exoplanetary Characterization & Astrochemistry Suite (ECAS)"
        )
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        # Qt stylesheets use CSS-like rules to control the appearance of widgets.
        # Object-specific rules, such as QLabel#pageTitle, apply only to widgets
        # assigned the matching object name below.
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

            QPushButton {
                background-color: #394352;
                border: 1px solid #4c596b;
                border-radius: 4px;
                padding: 9px 14px;
            }

            QPushButton:hover {
                background-color: #46556a;
            }

            QTableWidget {
                background-color: #181b21;
                alternate-background-color: #222832;
                gridline-color: #394352;
                border: 1px solid #394352;
            }

            QHeaderView::section {
                background-color: #2b323d;
                padding: 7px;
                border: none;
            }
        """)

        # The navigation list acts as the menu on the left side of the window.
        # Its row order must match the page order in self.pages below.
        self.navigation = QListWidget()
        self.navigation.addItems([
            "Overview",
            "Projects",
            "Spectral Data",
            "Comparisons",
            "Settings",
        ])
        self.navigation.setFixedWidth(200)

        # QStackedWidget holds multiple pages but displays only one at a time.
        # These attributes are initialized here so other methods can access
        # the spectral table, its status label, and the most recently imported
        # dataset.
        self.pages = QStackedWidget()
        self.spectrum_table = None
        self.spectrum_status = None
        self.current_spectrum = None

        # Build each page before assembling the overall window layout.
        self._build_pages()

        # The horizontal layout places navigation on the left and the selected
        # page on the right. The stretch factor of 1 lets the page area expand.
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self.navigation)
        body_layout.addWidget(self.pages, 1)

        self.setCentralWidget(body)

        # Connect navigation changes to page changes.
        # For example, selecting row 2 displays page index 2: Spectral Data.
        self.navigation.currentRowChanged.connect(
            self.pages.setCurrentIndex
        )

        # Select the Overview page when ECAS first opens.
        self.navigation.setCurrentRow(0)

        # The status bar gives brief feedback about the current application
        # state, such as whether a dataset has been loaded successfully.
        self.statusBar().showMessage("Ready — no dataset loaded")

    def _build_pages(self):
        """Create the pages and add them to the stacked page container."""
        # Keep the navigation and page order aligned.
        # Spectral Data receives a dedicated layout; the other pages are
        # placeholders until their functionality is implemented.
        definitions = [
            ("ECAS workspace", "Scientific analysis workspace."),
            ("Projects", "Create and manage research projects."),
            ("", ""),
            ("Comparisons", "Configure and review spectral comparisons."),
            ("Settings", "Application preferences and data locations."),
        ]

        for index, (heading, description) in enumerate(definitions):
            # Each page is a separate widget with its own vertical layout.
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(32, 28, 32, 28)
            layout.setSpacing(12)

            if index == 2:
                # Index 2 corresponds to "Spectral Data" in the navigation.
                # Its controls are created in a separate method to keep this
                # page-building loop easy to maintain.
                self._build_spectral_page(layout)
            else:
                # The remaining pages currently contain headings and
                # descriptions only; they are not fully implemented yet.
                title = QLabel(heading)
                title.setObjectName("pageTitle")

                subtitle = QLabel(description)
                subtitle.setObjectName("subtitle")
                subtitle.setWordWrap(True)

                layout.addWidget(title)
                layout.addWidget(subtitle)
                layout.addStretch()

            # Adding pages in this order is what links their indices to the
            # matching rows in the navigation list.
            self.pages.addWidget(page)

    def _build_spectral_page(self, layout):
        """Create the controls used to import and inspect a spectrum."""
        title = QLabel("Spectral Data")
        title.setObjectName("pageTitle")

        # Be explicit about the current importer's scope: local CSV files.
        # The importer does not infer wavelength units or signal semantics.
        description = QLabel(
            "Import a local CSV spectrum for inspection. "
            "Values are displayed as imported; no units are inferred."
        )
        description.setObjectName("subtitle")
        description.setWordWrap(True)

        # Clicking this button invokes the import workflow below.
        import_button = QPushButton("Import CSV")
        import_button.clicked.connect(self._import_csv)

        # This label reports whether a dataset is loaded and, if so, its
        # filename and number of imported rows.
        self.spectrum_status = QLabel("No spectrum loaded.")
        self.spectrum_status.setWordWrap(True)

        # The table presents validated values for inspection.
        # Editing is disabled so users cannot accidentally alter the displayed
        # data and mistake those edits for changes to the source file.
        self.spectrum_table = QTableWidget()
        self.spectrum_table.setAlternatingRowColors(True)
        self.spectrum_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.spectrum_table.setSortingEnabled(False)

        # Add controls to the page in visual order.
        # The table receives the remaining vertical space (stretch factor 1).
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(import_button, 0)
        layout.addWidget(self.spectrum_status)
        layout.addWidget(self.spectrum_table, 1)


    def _import_csv(self):
        """Import a CSV spectrum and display its validated measurements.

        Opens a file dialog via QFileDialog.getOpenFileName(). For testing,
        use the private _import_csv_from_path() method instead.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Import Spectrum CSV",
            "",
            "CSV files (*.csv);;All files (*)",
        )

        if not file_name:
            return

        try:
            spectrum = import_spectrum_csv(file_name)
        except SpectrumImportError as exc:
            QMessageBox.warning(
                self,
                "Spectrum Import Failed",
                str(exc),
            )
            self.statusBar().showMessage("Import failed")
            return

        # SpectrumData uses attributes instead of dictionary keys.
        rows = spectrum.rows
        columns = list(spectrum.columns)

        self.spectrum_table.setRowCount(0)
        self.spectrum_table.setColumnCount(len(columns))
        self.spectrum_table.setHorizontalHeaderLabels(columns)
        self.spectrum_table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, column in enumerate(columns):
                # Display missing values as blank cells without changing stored data.
                value = row[column]
                item = QTableWidgetItem("" if value is None else str(value))
                self.spectrum_table.setItem(
                    row_index, column_index, item
                )

        self.spectrum_table.resizeColumnsToContents()
        self.current_spectrum = spectrum

        source_name = spectrum.source_file.name
        self.spectrum_status.setText(
            f"Loaded: {source_name} — {spectrum.row_count} rows"
        )
        status_message = (
            f"Imported {spectrum.row_count} measurements. "
            + (", ".join(spectrum.warnings) if spectrum.warnings else "")
        )
        self.statusBar().showMessage(status_message)

    def _import_csv_from_path(self, path: str):
        """Import a CSV from a specific path for testing purposes."""
        try:
            spectrum = import_spectrum_csv(path)
        except SpectrumImportError as exc:
            QMessageBox.warning(
                self,
                "Spectrum Import Failed",
                str(exc),
            )
            self.statusBar().showMessage("Import failed")
            return

        # SpectrumData uses attributes instead of dictionary keys.
        rows = spectrum.rows
        columns = list(spectrum.columns)

        self.spectrum_table.setRowCount(0)
        self.spectrum_table.setColumnCount(len(columns))
        self.spectrum_table.setHorizontalHeaderLabels(columns)
        self.spectrum_table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, column in enumerate(columns):
                # Display missing values as blank cells without changing stored data.
                value = row[column]
                item = QTableWidgetItem("" if value is None else str(value))
                self.spectrum_table.setItem(
                    row_index, column_index, item
                )

        self.spectrum_table.resizeColumnsToContents()
        self.current_spectrum = spectrum

        source_name = spectrum.source_file.name
        self.spectrum_status.setText(
            f"Loaded: {source_name} — {spectrum.row_count} rows"
        )
        status_message = (
            f"Imported {spectrum.row_count} measurements. "
            + (", ".join(spectrum.warnings) if spectrum.warnings else "")
        )
        self.statusBar().showMessage(status_message)
