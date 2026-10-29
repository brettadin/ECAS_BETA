
"""
ECAS main application window.

This module is responsible for the desktop interface: navigation, page layouts,
and presenting imported spectral data. The actual CSV parsing and validation
are handled by ecas.ingestion.csv_importer so that scientific data processing
does not become tied to the user interface.
"""

from hashlib import sha256
from pathlib import Path


def _hash_file_if_present(path):
    target = Path(path)
    if not target.is_file() or target.is_symlink() or target.is_junction():
        return None
    with target.open('rb') as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    return sha256(raw).hexdigest() if len(raw) <= 16 * 1024 * 1024 else None
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QColor

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
    QComboBox,
    QScrollArea,
)

# Reuse the ingestion module rather than duplicating CSV validation here.
# SpectrumImportError represents an expected problem with the input file.
from ecas.ingestion.csv_importer import (
    SpectrumImportError,
    WASP39B_SCHEMA,
)
from ecas.ingestion.import_manager import import_spectrum

# The plotting widget receives normalized SpectrumData, not raw CSV files.
from ecas.visualization.spectra_plot import SpectraPlot
from ecas.ingestion.nasa_table import import_transmission_table
from ecas.ui.nasa_browser import NasaArchiveBrowser
from ecas.ui.project_browser import ProjectBrowser
from ecas.projects import ProjectStore
from ecas.ui.source_links import source_link
from ecas.ui.molecular_browser import MolecularReferenceBrowser
from ecas.ui.comparison_browser import ComparisonBrowser
from ecas.ui.workspace_pages import OverviewPage, SettingsPage
from ecas.ui.resources_browser import ResourcesBrowser
from ecas.ui.transit_view import TransitVisualizerPage
from ecas.ingestion.tabular_formats import import_tabular_spectrum


class ECASWindow(QMainWindow):
    """Main ECAS window and coordinator for its interface."""

    def __init__(self, *, projects_dir=None, reference_cache_dir=None):
        """Initialize the window, navigation, pages, and status bar."""
        super().__init__()

        # Window identity and initial dimensions.
        # The minimum size prevents the interface from becoming too cramped.
        # Start the title with ECAS to identify the application consistently.
        self.setWindowTitle("ECAS — Exoplanetary Characterization & Astrochemistry Suite")
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
            "Molecular References",
            "Comparisons",
            "Settings",
            "References & Resources",
            "Transit Visualizer",
        ])
        self.navigation.setFixedWidth(200)

        # QStackedWidget holds multiple pages but displays only one at a time.
        # These attributes are initialized here so other methods can access
        # the spectral table, its status label, and the most recently imported
        # dataset.
        self.pages = QStackedWidget()
        # These widgets and the dataset reference are populated by the
        # Spectral Data page builder.
        self.spectrum_table = None
        self.spectrum_status = None
        self.spectra_plot = None
        self.current_spectrum = None
        self.current_spectrum_details = None
        self.current_spectrum_schema = None
        self.current_project_attachment = None
        self.current_source_sha256 = None
        self.project_store = ProjectStore(projects_dir if projects_dir is not None
                                          else Path(__file__).resolve().parents[2] / 'projects')
        self.project_browser = None
        self.reference_cache_dir = reference_cache_dir

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
        self.navigation.currentRowChanged.connect(self._refresh_workspace_summary)

        # Select the Overview page when ECAS first opens.
        self.navigation.setCurrentRow(0)

        # The status bar gives brief feedback about the current application
        # state, such as whether a dataset has been loaded successfully.
        self.statusBar().showMessage("Ready — no dataset loaded")

    def _build_pages(self):
        """Create the pages and add them to the stacked page container."""
        # Keep the navigation and page order aligned.
        # Overview summarizes loaded state; Settings mirrors existing preferences.
        definitions = [
            ("ECAS workspace", "Scientific analysis workspace."),
            ("Projects", "Create and manage research projects."),
            ("", ""),
            ("Molecular References", "Search and manage molecular reference data."),
            ("Comparisons", "Inspect independently selected inputs."),
            ("Settings", "Application preferences and data locations."),
            ("References & Resources", "Scientific software, archives, molecular databases, and publications."),
            ("Transit Visualizer", "Educational geometric exoplanet transit and orbit simulation."),
        ]

        for index, (heading, description) in enumerate(definitions):
            # Each page is a separate widget with its own vertical layout.
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(32, 28, 32, 28)
            layout.setSpacing(12)

            if index == 0:
                self.overview_page = OverviewPage(
                    self._workspace_summary, self.navigation.setCurrentRow, self)
                layout.addWidget(self.overview_page)
            elif index == 1:
                self.project_browser = ProjectBrowser(self.project_store, self)
                self.project_browser.saveRequested.connect(self._save_to_project)
                self.project_browser.spectrumReady.connect(self._open_project_spectrum)
                layout.addWidget(self.project_browser)
            elif index == 2:
                # Index 2 corresponds to "Spectral Data" in the navigation.
                # Its controls are created in a separate method to keep this
                # page-building loop easy to maintain.
                self._build_spectral_page(layout)
            elif index == 3:
                self.reference_browser = MolecularReferenceBrowser(self, cache_root=self.reference_cache_dir)
                layout.addWidget(self.reference_browser)
            elif index == 4:
                self.comparison_browser = ComparisonBrowser(
                    self._comparison_observation, self.reference_browser.cache_root, self,
                    description_getter=self._comparison_description,
                    metadata_getter=self._comparison_metadata,
                    project_store=self.project_store,
                    active_project_getter=lambda: self.project_browser.projects.currentText())
                layout.addWidget(self.comparison_browser)
            elif index == 5:
                self.settings_page = SettingsPage(self.spectrum_schema_selector, {
                    'Research projects': self.project_store.root,
                    'NASA cache': self.nasa_browser.cache_root,
                    'ExoMol catalogue cache': self.reference_browser.cache_root,
                    'ExoMol reference cache': self.reference_browser.cache_root / 'references',
                }, self)
                layout.addWidget(self.settings_page)
            elif index == 6:
                self.resources_browser = ResourcesBrowser(self)
                layout.addWidget(self.resources_browser)
            elif index == 7:
                self.transit_page = TransitVisualizerPage(
                    on_apply_preset=self._on_transit_apply_to_comparisons,
                    parent=self,
                )
                self.transit_page.apply_to_comparisons_requested.connect(
                    self._on_transit_apply_to_comparisons
                )
                layout.addWidget(self.transit_page)
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
            if index in (0, 5):
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setWidget(page)
                self.pages.addWidget(scroll)
            else:
                self.pages.addWidget(page)

    def _refresh_workspace_summary(self, index):
        if index == 0:
            self.overview_page.refresh()

    def _workspace_summary(self):
        """Summarize loaded state without opening files, caches or project databases."""
        spectrum = self.current_spectrum
        observation = (f'{spectrum.source_file.name} — {spectrum.row_count} rows'
                       if spectrum is not None else 'none loaded')
        reference = self.reference_browser.current_reference
        if reference is None:
            reference_text = 'none loaded'
        else:
            product = reference.product
            reference_text = (f'{product.provenance.molecule} / {product.provenance.dataset}; '
                              f'{reference.request.temperature} K; {len(product.points)} points')
        comparison = self.comparison_browser
        selected_observation = ('selected' if comparison.current_observation is not None else 'not selected')
        selected_reference = ('selected' if comparison.current_reference is not None else 'not selected')
        return (f'Current observation: {observation}\n'
                f'Molecular References display: {reference_text}\n'
                f'Comparisons: {comparison.observation_selector.count()} session observation choices; '
                f'observation {selected_observation}; reference {selected_reference}.\n'
                'This summary updates when Overview is opened; it is not a stored-data inventory.')

    def _on_transit_apply_to_comparisons(self, preset_id: str):
        """Navigate to Comparisons workspace and select the corresponding planetary atmosphere preset."""
        self.navigation.setCurrentRow(4)
        if hasattr(self, 'comparison_browser') and self.comparison_browser:
            idx = self.comparison_browser.gen_preset_selector.findData(preset_id)
            if idx >= 0:
                self.comparison_browser.gen_preset_selector.setCurrentIndex(idx)

    def _comparison_observation(self):
        """Return the loaded input without rereading files or asserting provenance."""
        source_hash = (self.current_spectrum_details.source_sha256
                       if self.current_spectrum_details is not None else self.current_source_sha256)
        return self.current_spectrum, source_hash

    def _comparison_description(self):
        """Use established source facts for session names, without source reads."""
        details = self.current_spectrum_details
        table = dict(details.metadata) if details is not None else {}
        attachment = self.current_project_attachment or {}
        archive = attachment.get('provenance', {}).get('cache_record', {}).get('metadata', {})
        if not isinstance(archive, dict):
            archive = {}
        def text(value):
            return ' '.join(value.split()) if isinstance(value, str) else ''
        planet = text(archive.get('pl_name')) or text(table.get('PL_NAME'))
        publication = text(archive.get('authors')) or text(table.get('REFERENCE'))
        instrument = text(archive.get('instrument')) or text(table.get('INSTRUMENT'))
        return ' — '.join(part for part in (
            planet, publication or self.current_spectrum.source_file.name, instrument) if part)

    def _comparison_metadata(self) -> dict[str, str]:
        """Return established header/archive metadata without rereading source files."""
        details = self.current_spectrum_details
        table = dict(details.metadata) if details is not None else {}
        attachment = self.current_project_attachment or {}
        archive = attachment.get('provenance', {}).get('cache_record', {}).get('metadata', {})
        if not isinstance(archive, dict):
            archive = {}

        def clean(value):
            return ' '.join(value.split()) if isinstance(value, str) else ''

        meta: dict[str, str] = {}
        planet = clean(archive.get('pl_name')) or clean(table.get('PL_NAME'))
        instrument = clean(archive.get('instrument')) or clean(table.get('INSTRUMENT'))
        facility = clean(archive.get('facility')) or clean(table.get('FACILITY'))
        reference = clean(archive.get('authors')) or clean(table.get('REFERENCE'))
        spec_type = clean(archive.get('spec_type')) or clean(table.get('SPEC_TYPE'))
        if planet:
            meta['pl_name'] = planet
        if instrument:
            meta['instrument'] = instrument
        if facility:
            meta['facility'] = facility
        if reference:
            meta['reference'] = reference
        if spec_type:
            meta['spec_type'] = spec_type
        if details is not None and getattr(details, 'column_units', None):
            meta['column_units'] = dict(details.column_units)
        return meta

    def _build_spectral_page(self, layout):
        """Create the controls used to import and inspect a spectrum."""
        title = QLabel("Spectral Data")
        title.setObjectName("pageTitle")

        # Be explicit about the current importer's scope: local CSV files.
        # The importer does not infer wavelength units or signal semantics.
        description = QLabel(
            "Import a local CSV spectrum for inspection. "
            "Values are displayed as imported; no units are inferred. "
            "For the bundled WASP-39 b example, choose WASP-39 b Archive "
            "before importing. Local CSV import does not require a database."
        )
        description.setObjectName("subtitle")
        description.setWordWrap(True)

        # Clicking this button invokes the import workflow below.
        import_button = QPushButton("Import Spectrum")
        import_button.clicked.connect(self._import_csv)

        # Schema selector for choosing how to interpret the CSV data.
        schema_label = QLabel("CSV schema:")
        schema_label.setObjectName("schemaLabel")

        self.spectrum_schema_selector = QComboBox()
        self.spectrum_schema_selector.addItems(["Generic / Unknown", "WASP-39 b Archive"])
        self.spectrum_schema_selector.setCurrentIndex(0)  # Default: Generic/Unknown

        # This label reports whether a dataset is loaded and, if so, its
        # filename and number of imported rows.
        self.spectrum_status = QLabel("No spectrum loaded.")
        self.spectrum_status.setWordWrap(True)

        # The table presents validated values for inspection.
        # Create the plot widget once and reuse it for subsequent imports.
        # Each successful load replaces the previous plotted dataset.
        self.spectra_plot = SpectraPlot()

        # The table presents validated values without permitting edits.
        self.spectrum_table = QTableWidget()
        self.spectrum_table.setAlternatingRowColors(True)
        self.spectrum_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.spectrum_table.setSortingEnabled(False)
        self.spectrum_table.itemDoubleClicked.connect(self._open_source_link)

        # Place the plot above the table so users can inspect the shape of
        # the spectrum and then examine its underlying imported measurements.
        layout.addWidget(title)
        layout.addWidget(description)
        self.nasa_browser = NasaArchiveBrowser(self)
        self.nasa_browser.spectrumReady.connect(self._import_csv_from_path)
        layout.addWidget(self.nasa_browser)
        # Schema selection must be visible before the import action; do not
        # silently infer scientific meaning from a filename or failed parse.
        layout.addWidget(schema_label)
        layout.addWidget(self.spectrum_schema_selector)
        layout.addWidget(import_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.spectrum_status)
        layout.addWidget(self.spectra_plot, 2)
        layout.addWidget(self.spectrum_table, 1)

    def _display_spectrum(self, spectrum, schema=None, *, nasa_source=False):
        """Display one normalized SpectrumData object in the plot and table.

        Args:
            spectrum: The SpectrumData object to display.
            schema: Optional schema dict for archive handling. Defaults to None (generic).
            nasa_source: Resolve NASA-relative source links for display only.
        """

        # Load the plot first. If the data cannot be plotted, do not leave
        # the table showing a dataset that the plot failed to display.
        if not self.spectra_plot.load_spectrum(spectrum, schema=schema):
            self._clear_spectrum_display()
            self.spectrum_status.setText(
                "The imported spectrum has no valid plottable measurements."
            )
            self.statusBar().showMessage("Spectrum could not be plotted")
            return

        rows = spectrum.rows
        columns = list(spectrum.columns)

        # Replace the previous table contents without modifying SpectrumData.
        self.spectrum_table.clearContents()
        self.spectrum_table.setRowCount(0)
        self.spectrum_table.setColumnCount(len(columns))
        self.spectrum_table.setHorizontalHeaderLabels(columns)
        self.spectrum_table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, column in enumerate(columns):
                # Missing values remain blank rather than being changed to zero.
                value = row[column]
                item = QTableWidgetItem(
                    "" if value is None else str(value)
                )
                if column.endswith('_url'):
                    link = source_link(value, nasa_source=nasa_source)
                    if link:
                        item.setText(link)
                        item.setData(Qt.ItemDataRole.UserRole, link)
                        item.setToolTip(f'Original source value: {value}\nDouble-click to open this source link.')
                        item.setForeground(QColor('#81a1c1'))
                        font = item.font()
                        font.setUnderline(True)
                        item.setFont(font)
                self.spectrum_table.setItem(
                    row_index, column_index, item
                )

        self.spectrum_table.resizeColumnsToContents()
        self.current_spectrum = spectrum
        self.current_spectrum_schema = schema
        self.current_project_attachment = None
        self.current_source_sha256 = None
        self.project_browser.set_spectrum_available(True)

        # Report the imported dataset and any warnings supplied by the importer.
        source_name = spectrum.source_file.name
        self.spectrum_status.setText(
            f"Loaded: {source_name} — {spectrum.row_count} rows"
        )

        status_message = (
            f"Imported {spectrum.row_count} measurements."
        )
        if spectrum.warnings:
            status_message += " " + ", ".join(spectrum.warnings)

        self.statusBar().showMessage(status_message)

    def _clear_spectrum_display(self):
        """Clear the table, plot, and dataset reference together."""

        # All three views must agree about whether a dataset is loaded.
        if self.spectra_plot is not None:
            self.spectra_plot.clear()

        if self.spectrum_table is not None:
            self.spectrum_table.clearContents()
            self.spectrum_table.setRowCount(0)
            self.spectrum_table.setColumnCount(0)

        self.current_spectrum = None
        self.current_spectrum_details = None
        self.current_spectrum_schema = None
        self.current_project_attachment = None
        self.current_source_sha256 = None
        if self.project_browser is not None:
            self.project_browser.set_spectrum_available(False)

        if self.spectrum_status is not None:
            self.spectrum_status.setText("No spectrum loaded.")


    def _selected_import_schema(self):
        """Return the schema selected in the import controls."""
        if self.spectrum_schema_selector.currentText() == "WASP-39 b Archive":
            return WASP39B_SCHEMA
        return None

    def _import_csv(self):
        """Open a file dialog and import a CSV spectrum."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Import Spectrum",
            "",
            "Spectrum files (*.csv *.tbl *.ecsv *.dat *.tsv *.fits *.fit *.fts);;"
            "CSV files (*.csv);;NASA IPAC tables (*.tbl);;"
            "Astropy ECSV / ASCII (*.ecsv *.dat *.tsv);;"
            "FITS binary tables (*.fits *.fit *.fts);;All files (*)",
        )

        # Cancelling the dialog does not count as a failed import.
        if not file_name:
            return

        # Map the schema selector text to the appropriate schema dict.
        selected_schema = (
            WASP39B_SCHEMA
            if self.spectrum_schema_selector.currentText() == "WASP-39 b Archive"
            else None
        )

        try:
            spectrum, details = self._read_spectrum_file(file_name, selected_schema)
        except SpectrumImportError as exc:
            # Remove the old display so it cannot be mistaken for the
            # spectrum the user just attempted to import.
            self._clear_spectrum_display()

            QMessageBox.warning(
                self,
                "Spectrum Import Failed",
                str(exc) or 'The spectrum could not be imported. No further error details were provided.',
            )
            self.statusBar().showMessage("Import failed")
            return

        self._display_spectrum(spectrum, schema=selected_schema, **({'nasa_source': True} if details is not None else {}))
        self.current_spectrum_details = details if self.current_spectrum is spectrum else None
        if self.current_spectrum is spectrum:
            self.current_source_sha256 = details.source_sha256 if details is not None else _hash_file_if_present(spectrum.source_file)

    def _import_csv_from_path(self, path: str):
        """Import a CSV from a specified path."""
        selected_schema = self._selected_import_schema()

        try:
            spectrum, details = self._read_spectrum_file(path, selected_schema)
        except SpectrumImportError as exc:
            # Remove the old display so it cannot be mistaken for the
            # spectrum the user just attempted to import.
            self._clear_spectrum_display()

            QMessageBox.warning(
                self,
                "Spectrum Import Failed",
                str(exc) or 'The spectrum could not be imported. No further error details were provided.',
            )
            self.statusBar().showMessage("Import failed")
            return

        self._display_spectrum(spectrum, schema=selected_schema, **({'nasa_source': True} if details is not None else {}))
        self.current_spectrum_details = details if self.current_spectrum is spectrum else None
        if self.current_spectrum is spectrum:
            self.current_source_sha256 = details.source_sha256 if details is not None else _hash_file_if_present(spectrum.source_file)

    def _read_spectrum_file(self, path, schema):
        if Path(path).suffix.lower() == ".tbl":
            details = import_transmission_table(path)
            return details.spectrum, details
        if Path(path).suffix.lower() in (".ecsv", ".dat", ".tsv", ".fits", ".fit", ".fts"):
            return import_tabular_spectrum(path), None
        return import_spectrum(path, archive_schema=schema), None

    def closeEvent(self, event):
        self.nasa_browser.cancel()
        self.reference_browser.shutdown()
        super().closeEvent(event)

    def _save_to_project(self, name):
        if self.current_spectrum is None:
            self.project_browser.fail('Load a spectrum in Spectral Data first')
            return
        try:
            identifier = self.project_store.attach(name, self.current_spectrum,
                self.current_spectrum_schema, self.current_project_attachment,
                expected_source_sha256=(self.current_spectrum_details.source_sha256
                                        if self.current_spectrum_details is not None else None))
            self.project_browser.reload()
            self.project_browser.status.setText(f'Added spectrum {identifier} to {name}; source bytes and provenance preserved.')
        except Exception as error:
            self.project_browser.fail(error)

    def _open_project_spectrum(self, record):
        try:
            self._display_spectrum(record.spectrum, schema=record.import_schema, nasa_source=record.details is not None)
            if self.current_spectrum is record.spectrum:
                self.current_spectrum_details = record.details
                self.current_project_attachment = record.attachment
                self.current_source_sha256 = (
                    record.details.source_sha256
                    if record.details is not None
                    else (record.attachment.get('source_sha256') if isinstance(record.attachment, dict) else None)
                )
                self.navigation.setCurrentRow(2)
            else:
                self.project_browser.fail('Spectrum could not be plotted: no valid plottable measurements.')
        except Exception as error:
            self._clear_spectrum_display()
            self.project_browser.fail(error)

    def _open_source_link(self, item):
        link = item.data(Qt.ItemDataRole.UserRole)
        if link and source_link(link):
            if not QDesktopServices.openUrl(QUrl(link)):
                self.statusBar().showMessage('Could not open the source link in a browser.')
