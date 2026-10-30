
"""
ECAS main application window.

This module is responsible for the desktop interface: navigation, page layouts,
and presenting imported spectral data. The actual CSV parsing and validation
are handled by ecas.ingestion.csv_importer so that scientific data processing
does not become tied to the user interface.
"""

from pathlib import Path
from ecas.observations import hash_source_file


def _hash_file_if_present(path):
    target = Path(path)
    if not target.is_file() or target.is_symlink() or target.is_junction():
        return None
    return hash_source_file(target)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QColor

from PySide6.QtWidgets import (
    QApplication,
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
from ecas.ui.identification_panel import IdentificationPanel
from ecas.ui.images_workspace import ImagesWorkspacePage
from ecas.ui.runs_workspace import RunsReportsWorkspacePage
from ecas.ui.event_filters import IgnoreWheelUnlessFocusedFilter, apply_wheel_protection


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
            "Atmospheric Analysis",
            "Transit Visualizer",
            "Laboratory Identification",
            "Images",
            "Runs & Reports",
            "References & Resources",
            "Settings",
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
        self.current_project_record_id = None
        self.current_project_id = None
        self.project_store = ProjectStore(projects_dir if projects_dir is not None
                                          else Path(__file__).resolve().parents[2] / 'projects')
        self.project_browser = None
        self.reference_cache_dir = reference_cache_dir
        self.identification_panel_page = None
        self.images_workspace = None
        self.runs_workspace = None

        # Install wheel event protection on the application to prevent unintentional scrolling changes
        self._wheel_filter = IgnoreWheelUnlessFocusedFilter(self)
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self._wheel_filter)
        self.installEventFilter(self._wheel_filter)

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
        apply_wheel_protection(self)

    def _build_pages(self):
        """Create the pages and add them to the stacked page container."""
        # Keep the navigation and page order aligned.
        # Overview summarizes loaded state; Settings mirrors existing preferences.
        definitions = [
            ("ECAS workspace", "Scientific analysis workspace."),
            ("Projects", "Create and manage research projects."),
            ("", ""),
            ("Molecular References", "Search and manage molecular reference data."),
            ("Atmospheric Analysis", "Planetary transmission observations and physical models."),
            ("Transit Visualizer", "Educational geometric exoplanet transit and orbit simulation."),
            ("Laboratory Identification", "Fit compatible laboratory absorption measurements using real local IR or UV-Vis references."),
            ("Images", "Inspect 2D FITS astronomical image planes and surface brightness."),
            ("Runs & Reports", "Analysis job lifecycle, checkpoint resumption, and reproducible reporting."),
            ("References & Resources", "Scientific software, archives, molecular databases, and publications."),
            ("Settings", "Application preferences and data locations."),
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
                self.transit_page = TransitVisualizerPage(
                    on_apply_preset=self._on_transit_apply_to_comparisons,
                    parent=self,
                )
                self.transit_page.apply_to_comparisons_requested.connect(
                    self._on_transit_apply_to_comparisons
                )
                layout.addWidget(self.transit_page)
            elif index == 6:
                self.identification_panel_page = IdentificationPanel(
                    self._comparison_observation,
                    metadata_getter=self._comparison_metadata,
                    description_getter=self._comparison_description,
                    project_store=self.project_store,
                    active_project_getter=lambda: (self.project_browser.projects.currentText()
                                                   if self.project_browser is not None else None),
                    parent=self,
                )
                self.identification_panel_page.atmospheric_requested.connect(
                    self._on_identification_atmospheric_requested
                )
                layout.addWidget(self.identification_panel_page)
            elif index == 7:
                self.images_workspace = ImagesWorkspacePage(self)
                layout.addWidget(self.images_workspace)
            elif index == 8:
                self.runs_workspace = RunsReportsWorkspacePage(self)
                layout.addWidget(self.runs_workspace)
            elif index == 9:
                self.resources_browser = ResourcesBrowser(self)
                layout.addWidget(self.resources_browser)
            elif index == 10:
                self.settings_page = SettingsPage(self.spectrum_schema_selector, {
                    'Research projects': self.project_store.root,
                    'NASA cache': self.nasa_browser.cache_root,
                    'ExoMol catalogue cache': self.reference_browser.cache_root,
                    'ExoMol reference cache': self.reference_browser.cache_root / 'references',
                }, self)
                layout.addWidget(self.settings_page)
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
            if index in (0, 5, 8):
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

    def _comparison_metadata(self) -> dict[str, object]:
        """Return established header/archive metadata without rereading source files."""
        details = self.current_spectrum_details
        table = dict(details.metadata) if details is not None else {}
        attachment = self.current_project_attachment or {}
        archive = attachment.get('provenance', {}).get('cache_record', {}).get('metadata', {})
        if not isinstance(archive, dict):
            archive = {}

        def clean(value):
            return ' '.join(value.split()) if isinstance(value, str) else ''

        meta: dict[str, object] = dict(self.current_spectrum.metadata) if self.current_spectrum else {}
        if table:
            meta['source_table_metadata'] = dict(table)
        if archive:
            meta['archive_metadata'] = dict(archive)
        if self.current_project_record_id is not None:
            meta['project_record_id'] = str(self.current_project_record_id)
            meta['project_id'] = self.current_project_id
        for key in ('bibcode', 'spec_path'):
            if archive.get(key):
                meta[key] = str(archive[key])
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

        view_fits_button = QPushButton("Inspect 2D FITS Image...")
        view_fits_button.setToolTip("Open and visualize 2D astronomical image containers (e.g. JWST MIRI imaging products)")
        view_fits_button.clicked.connect(self._open_fits_image_dialog)

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
        layout.addWidget(view_fits_button, 0, Qt.AlignmentFlag.AlignLeft)
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
        self.current_project_record_id = None
        self.current_project_id = None
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
        self.current_project_record_id = None
        self.current_project_id = None
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

    def _handle_import_error(self, exc: SpectrumImportError, file_path: str | Path) -> None:
        """Handle spectrum import failure, offering 2D image inspection if the file is an astronomical image."""
        self._clear_spectrum_display()
        self.statusBar().showMessage("Import failed")

        resolved = Path(file_path)
        is_fits = resolved.suffix.lower() in (".fits", ".fit", ".fts")
        image_container = None
        if is_fits:
            from ecas.ingestion.fits_image import scan_fits_image

            image_container = scan_fits_image(resolved)

        if image_container is not None and image_container.planes:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("2D Astronomical Image Product")
            msg_box.setText(
                "<b>2D Astronomical Image Container Detected</b><br><br>"
                f"{exc}<br><br>"
                "Would you like to open the <b>2D FITS Image Viewer</b> to inspect its "
                "calibrated spatial brightness planes and pixel statistics?"
            )
            btn_inspect = msg_box.addButton("Inspect 2D Image", QMessageBox.AcceptRole)
            msg_box.addButton(QMessageBox.Close)
            msg_box.setDefaultButton(btn_inspect)
            msg_box.exec()

            if msg_box.clickedButton() == btn_inspect:
                self._open_fits_image_viewer(image_container)
            return

        QMessageBox.warning(
            self,
            "Spectrum Import Failed",
            str(exc) or "The spectrum could not be imported. No further error details were provided.",
        )

    def _open_fits_image_dialog(self) -> None:
        """Open a file dialog to choose and inspect a 2D FITS image."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Inspect 2D FITS Image",
            "",
            "FITS images (*.fits *.fit *.fts);;All files (*)",
        )
        if not file_name:
            return

        from ecas.ingestion.fits_image import scan_fits_image

        container = scan_fits_image(file_name)
        if container is None or not container.planes:
            QMessageBox.warning(
                self,
                "Not a 2D FITS Image",
                f"The selected file could not be recognized as a valid 2D FITS image container: {Path(file_name).name}",
            )
            return

        self._open_fits_image_viewer(container)

    def _open_fits_image_viewer(self, container_or_path) -> None:
        """Open the 2D FITS image viewer workspace or fallback dialog."""
        if hasattr(self, 'images_workspace') and self.images_workspace is not None:
            self.images_workspace.load_fits_image(container_or_path)
            self.navigate_to('images')
            return

        from ecas.ui.fits_image_viewer import FitsImageViewerDialog

        dialog = FitsImageViewerDialog(container_or_path, parent=self)
        dialog.exec()

    def _import_csv(self):
        """Open a file dialog and import a CSV spectrum."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Import Spectrum",
            "",
            "Spectrum files (*.csv *.tbl *.ecsv *.dat *.tsv *.txt *.asc *.fits *.fit *.fts *.jdx *.dx *.jcamp *.jcm);;"
            "CSV files (*.csv);;NASA IPAC tables (*.tbl);;"
            "Astropy ECSV / ASCII (*.ecsv *.dat *.tsv *.txt *.asc);;"
            "FITS binary tables (*.fits *.fit *.fts);;JCAMP-DX (*.jdx *.dx *.jcamp *.jcm);;All files (*)",
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
            self._handle_import_error(exc, file_name)
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
            self._handle_import_error(exc, path)
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

    def _on_identification_atmospheric_requested(self, context=None):
        """Navigate to Atmospheric Analysis when a transit observation is routed from Lab ID."""
        self.navigation.setCurrentRow(4)

    def navigate_to(self, name_or_alias: str) -> bool:
        """Navigate to a workspace by name, alias, or index."""
        aliases = {
            'overview': 0,
            'projects': 1,
            'spectral data': 2,
            'spectral': 2,
            'spectra': 2,
            'molecular references': 3,
            'molecular': 3,
            'references': 3,
            'atmospheric analysis': 4,
            'atmospheric': 4,
            'comparisons': 4,
            'comparison': 4,
            'transit visualizer': 5,
            'transit': 5,
            'laboratory identification': 6,
            'laboratory': 6,
            'identification': 6,
            'images': 7,
            'fits': 7,
            'fits images': 7,
            'runs & reports': 8,
            'runs': 8,
            'reports': 8,
            'jobs': 8,
            'references & resources': 9,
            'resources': 9,
            'settings': 10,
            'preferences': 10,
        }
        key = str(name_or_alias).strip().lower()
        if key in aliases:
            self.navigation.setCurrentRow(aliases[key])
            return True
        return False

    def show_workspace(self, name_or_index):
        """Convenience method to show a workspace by name, alias, or integer index."""
        if isinstance(name_or_index, int):
            if 0 <= name_or_index < self.navigation.count():
                self.navigation.setCurrentRow(name_or_index)
                return True
            return False
        return self.navigate_to(name_or_index)

    def closeEvent(self, event):
        if self.comparison_browser.identification_panel is not None:
            self.comparison_browser.identification_panel.shutdown()
        if hasattr(self, 'identification_panel_page') and self.identification_panel_page is not None:
            self.identification_panel_page.shutdown()
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
                self.current_project_record_id = record.record_id
                self.current_project_id = self.project_browser.projects.currentText()
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
