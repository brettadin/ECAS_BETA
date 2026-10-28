"""Reference catalogue search, verified product retrieval and offline reopening."""
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QSplitter, QFormLayout, QSpinBox, QDoubleSpinBox,
    QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView)

from ecas.ingestion.exomol_catalogue import MAX_BYTES, parse_catalogue, search_catalogue
from ecas.ingestion.exomol_catalogue_cache import load_catalogue, store_catalogue
from ecas.ingestion.exomol_network import PublicExomolCatalogueHttp
from ecas.ingestion.exomol_product import ProductRequest, SERVICES, supported_entry
from ecas.ingestion.exomol_product_network import PublicExomolProductHttp
from ecas.ingestion.exomol_reference_cache import cached_references, load_reference, store_reference


class MolecularReferenceBrowser(QWidget):
    def __init__(self, parent=None, *, cache_root=None, bundled_path=None, http=None, product_http=None):
        super().__init__(parent)
        root = Path(__file__).resolve().parents[2]
        self.cache_root = Path(cache_root) if cache_root is not None else root/'data/ExoMol/cache'
        self.bundled_path = Path(bundled_path) if bundled_path is not None else root/'data/ExoMol/2026-10-28/exomol.all'
        # Offline browsing needs no network manager. Construct it only when the
        # user explicitly refreshes, then retain it for subsequent refreshes.
        self.http = http
        self.product_http=product_http
        self.current_reference=None
        self.operation=None
        self.catalogue, self.entries = None, []
        self.busy, self.closing = False, False
        layout = QVBoxLayout(self)
        title = QLabel('Molecular reference catalogue')
        title.setWordWrap(True)
        title.setObjectName('pageTitle')
        layout.addWidget(title)
        explanation = QLabel('Search ExoMol molecule names, formulae, isotopologues or dataset names. Catalogue entries do not establish spectral availability or molecular presence.')
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        self.source = QLabel()
        self.source.setWordWrap(True)
        self.source.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.source)
        controls = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText('For example: Water, H2O, 1H2-16O or POKAZATEL')
        self.search_button = QPushButton('Search catalogue')
        controls.addWidget(self.query, 1)
        controls.addWidget(self.search_button)
        layout.addLayout(controls)
        refresh_controls = QHBoxLayout()
        self.refresh_button = QPushButton('Refresh from ExoMol')
        self.cancel_button = QPushButton('Cancel request')
        refresh_controls.addWidget(self.refresh_button)
        refresh_controls.addWidget(self.cancel_button)
        refresh_controls.addStretch()
        layout.addLayout(refresh_controls)
        self.status = QLabel('')
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        self.results = QListWidget()
        self.results.setObjectName('molecularResults')
        self.results.setStyleSheet('QListWidget#molecularResults::item { padding: 4px 6px; }')
        panels=QSplitter(Qt.Orientation.Horizontal)
        catalogue_panel=QWidget(); catalogue_layout=QVBoxLayout(catalogue_panel)
        catalogue_layout.setContentsMargins(0,0,8,0)
        catalogue_layout.addWidget(self.results,1)
        self.details = QLabel('Select an entry to inspect its identity. Comparison scoring is not available yet.')
        self.details.setTextFormat(Qt.TextFormat.PlainText)
        self.details.setWordWrap(True)
        catalogue_layout.addWidget(self.details)
        panels.addWidget(catalogue_panel)
        reference_panel=QWidget(); reference_layout=QVBoxLayout(reference_panel)
        reference_layout.setContentsMargins(8,0,0,0)
        conditions=QLabel('Supported retrieval: CO2 / UCL-4000, H2O / POKAZATEL, CH4 / MM (main isotopologues only). Calculated cross sections, zero pressure, Doppler-only broadening. Settings describe a reference product, not the planet atmosphere.')
        conditions.setWordWrap(True); reference_layout.addWidget(conditions)
        form=QFormLayout()
        self.temperature=QSpinBox(); self.temperature.setRange(100,5000); self.temperature.setValue(500)
        self.minimum=QSpinBox(); self.minimum.setRange(0,41200); self.minimum.setValue(4000)
        self.maximum=QSpinBox(); self.maximum.setRange(0,41200); self.maximum.setValue(4010)
        self.spacing=QDoubleSpinBox(); self.spacing.setDecimals(6); self.spacing.setRange(0.000001,41200); self.spacing.setValue(1)
        form.addRow('Temperature (K)',self.temperature)
        form.addRow('Minimum (cm^-1)',self.minimum); form.addRow('Maximum (cm^-1)',self.maximum)
        form.addRow('Spacing (cm^-1)',self.spacing)
        reference_layout.addLayout(form)
        self.download_button=QPushButton('Download selected reference')
        reference_layout.addWidget(self.download_button,0,Qt.AlignmentFlag.AlignLeft)
        cache_controls=QHBoxLayout()
        self.cached=QComboBox(); self.load_reference_button=QPushButton('Open cached reference')
        self.cached.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.cached.setMinimumContentsLength(10)
        cache_controls.addWidget(self.cached,1); cache_controls.addWidget(self.load_reference_button)
        reference_layout.addLayout(cache_controls)
        self.reference_status=QLabel('No reference loaded.')
        self.reference_status.setTextFormat(Qt.TextFormat.PlainText); self.reference_status.setWordWrap(True)
        reference_layout.addWidget(self.reference_status)
        self.reference_table=QTableWidget()
        self.reference_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        reference_layout.addWidget(self.reference_table,1)
        panels.addWidget(reference_panel); panels.setSizes([500,500])
        layout.addWidget(panels,1)
        self.query.returnPressed.connect(self.search)
        self.search_button.clicked.connect(self.search)
        self.refresh_button.clicked.connect(self.refresh)
        self.cancel_button.clicked.connect(self.cancel)
        self.results.currentRowChanged.connect(self.show_selected)
        self.download_button.clicked.connect(self.download_selected)
        self.load_reference_button.clicked.connect(self.open_cached_reference)
        self.cached.currentIndexChanged.connect(self._buttons)
        self._reload_references()
        self._load_initial()

    def _buttons(self):
        self.search_button.setEnabled(not self.busy and self.catalogue is not None)
        self.query.setEnabled(not self.busy)
        self.refresh_button.setEnabled(not self.busy)
        self.results.setEnabled(not self.busy)
        self.cancel_button.setEnabled(self.busy)
        selected=self.results.currentRow()
        self.download_button.setEnabled(not self.busy and 0<=selected<len(self.entries) and supported_entry(self.entries[selected]))
        self.load_reference_button.setEnabled(not self.busy and self.cached.currentIndex()>=0)
        self.cached.setEnabled(not self.busy)
        for control in (self.temperature,self.minimum,self.maximum,self.spacing): control.setEnabled(not self.busy)

    def _load_initial(self):
        warning = ''
        try:
            cached = load_catalogue(self.cache_root)
            if cached is not None:
                self.catalogue = cached.catalogue
                self.source.setText(f'Cached ExoMol index {self.catalogue.version}; retrieved {cached.retrieved_utc}. Search works offline.')
        except Exception as error:
            warning = f'Cached catalogue could not be loaded: {error}. '
        if self.catalogue is None:
            try:
                with self.bundled_path.open('rb') as stream:
                    self.catalogue = parse_catalogue(stream.read(MAX_BYTES+1))
                self.source.setText(f'Bundled ExoMol snapshot captured 2026-10-28; index {self.catalogue.version}. Refresh to check for updates.')
            except Exception as error:
                self.source.setText('No catalogue loaded.')
                warning += f'Bundled catalogue could not be loaded: {error}. '
        self.status.setText(warning or 'Enter a molecule name or provider identifier.')
        self._buttons()

    def search(self):
        if self.busy or self.catalogue is None:
            return
        self.entries = []
        self.results.clear()
        self.show_selected(-1)
        try:
            result = search_catalogue(self.catalogue, self.query.text())
            self.entries = list(result.entries)
            for entry in self.entries:
                self.results.addItem(f'{entry.formula} | {entry.isotopologue} | {entry.dataset} | {entry.version}')
            message = f'{result.total_matches} catalogue entries across {len(result.formulas)} molecules.'
            if not result.total_matches:
                message = 'No matches in this catalogue snapshot. This is not evidence that the molecule or its spectra do not exist.'
            if len(result.formulas)>1:
                message += ' Ambiguous identity: verify the formula and isotopologue.'
            if result.truncated:
                message += ' Showing the first 50; refine your search.'
            if self.catalogue.warnings:
                message += ' Provider version-label warnings are retained; no dates were corrected.'
            self.status.setText(message)
        except Exception as error:
            self.status.setText(f'Catalogue search failed: {error}')

    def show_selected(self, index):
        if not 0<=index<len(self.entries):
            self.details.setText('Select an entry to inspect its identity. Comparison scoring is not available yet.')
            self._buttons()
            return
        entry = self.entries[index]
        self.details.setText(f'Formula: {entry.formula}\nProvider names: {", ".join(entry.names) or "Not supplied"}\n'
            f'Isotopologue: {entry.isotope_formula} ({entry.isotopologue})\nInChIKey: {entry.inchi_key}\n'
            f'Dataset: {entry.dataset}; provider version label: {entry.version}\n'
            'Product type, spectral range, units, temperature and pressure: not established by this index.\n'+
            (f'Verified service: calculated {entry.formula} cross sections; zero pressure/Doppler-only. '
             f'Limits: 100–{SERVICES[entry.isotopologue].maximum_temperature} K, '
             f'0–{SERVICES[entry.isotopologue].maximum_wavenumber} cm^-1; exact grid of 2–10000 points.'
             if supported_entry(entry) else 'Retrieval for this catalogue record is not verified/supported yet.')+
            '\nCross sections cannot be compared directly with transit depth. Comparison scoring is not available yet.')
        self._buttons()

    def refresh(self):
        if self.busy:
            return
        self.busy = True
        self.operation='catalogue'
        self.status.setText('Refreshing the ExoMol catalogue…')
        self._buttons()

        def received(raw, error):
            if self.closing:
                return
            self.busy = False
            self.operation=None
            try:
                if error:
                    raise ValueError(error)
                snapshot = store_catalogue(self.cache_root, raw)
                self.catalogue = snapshot.catalogue
                self.source.setText(f'Cached ExoMol index {self.catalogue.version}; retrieved {snapshot.retrieved_utc}. Search works offline.')
                self.entries = []
                self.results.clear()
                self.show_selected(-1)
                if self.query.text().strip():
                    self.search()
                else:
                    self.status.setText('Catalogue refreshed and saved for offline search.')
            except Exception as failure:
                self.status.setText(f'Catalogue refresh stopped: {failure}. Previous catalogue unchanged.')
            self._buttons()
        try:
            if self.http is None:
                self.http = PublicExomolCatalogueHttp(self)
            self.http.get(received)
        except Exception as error:
            received(None, str(error) or 'Could not start catalogue refresh')

    def shutdown(self):
        self.closing = True
        if self.http is not None and hasattr(self.http, 'shutdown'):
            self.http.shutdown()
        else:
            self.cancel()
        if self.product_http is not None:
            if hasattr(self.product_http,'shutdown'): self.product_http.shutdown()
            else: self.product_http.cancel()

    def cancel(self):
        if self.operation=='reference' and self.product_http is not None:
            self.product_http.cancel()
        elif self.http is not None:
            self.http.cancel()

    def _reload_references(self, selected=None):
        self.cached.blockSignals(True)
        self.cached.clear()
        try:
            records,invalid=cached_references(self.cache_root/'references')
            for path,result in records:
                request=result.request
                self.cached.addItem(f'{request.service.formula} / {request.service.dataset} | {request.temperature} K | '
                                    f'{request.minimum}–{request.maximum} cm^-1 | spacing {request.spacing}',str(path))
                if selected is not None and path==selected: self.cached.setCurrentIndex(self.cached.count()-1)
            self.reference_status.setText(f'{len(records)} cached references; {invalid} invalid entries excluded.')
        except Exception as error: self.reference_status.setText(f'Reference cache unavailable: {error}')
        finally: self.cached.blockSignals(False)

    def _show_reference(self, result):
        product=result.product
        self.reference_table.setRowCount(len(product.points)); self.reference_table.setColumnCount(2)
        self.reference_table.setHorizontalHeaderLabels(['Wavenumber (cm^-1)','Cross section (cm^2/molecule)'])
        for row,point in enumerate(product.points):
            for column,value in enumerate(point): self.reference_table.setItem(row,column,QTableWidgetItem(str(value)))
        self.reference_table.resizeColumnsToContents()
        self.current_reference=result
        self.reference_status.setText(f'Calculated {product.provenance.molecule} cross section: {len(product.points)} points; {result.request.temperature} K; zero pressure; Doppler-only. '
            f'{product.provenance.dataset}. Source hash: {product.source_sha256[:12]}… CC BY-SA 4.0; references retained in cache.')
        self.reference_status.setToolTip(f'Raw SHA-256: {product.source_sha256}\nSource: {product.provenance.source_url}\n'+
                                        '\n'.join(product.provenance.citations))

    def download_selected(self):
        if self.busy: return
        index=self.results.currentRow()
        if not 0<=index<len(self.entries) or not supported_entry(self.entries[index]):
            self.status.setText('Select a supported CO2 / UCL-4000, H2O / POKAZATEL or CH4 / MM main-isotopologue record.')
            return
        entry=self.entries[index]
        try:
            request=ProductRequest(self.minimum.value(),self.maximum.value(),self.temperature.value(),
                                   format(self.spacing.value(),'.6f'),entry.isotopologue)
        except Exception as error:
            self.status.setText(f'Reference settings invalid: {error}'); return
        catalogue_context=dict(formula=entry.formula,isotopologue=entry.isotopologue,dataset=entry.dataset,
                               version=entry.version,catalogue_sha256=self.catalogue.source_sha256)
        self.busy=True; self.operation='reference'; self._buttons()
        self.status.setText('Starting reference request…')
        def received(result,error):
            if self.closing: return
            self.busy=False; self.operation=None
            try:
                if error: raise ValueError(error)
                if result.request!=request: raise ValueError('Downloaded reference settings differ from the selected request')
                path=store_reference(self.cache_root/'references',result,catalogue_context=catalogue_context)
                self._reload_references(path)
                self._show_reference(result)
                self.status.setText('Reference downloaded, validated and saved for offline reopening. No molecular detection or comparison was performed.')
            except Exception as failure:
                self.status.setText(f'Reference request stopped: {failure}. Previous displayed reference unchanged.')
            self._buttons()
        try:
            if self.product_http is None:
                self.product_http=PublicExomolProductHttp(self)
                self.product_http.phaseChanged.connect(self._reference_phase)
            self.product_http.download(entry,request,received)
        except Exception as error: received(None,str(error) or 'Could not start reference request')

    def _reference_phase(self, message):
        if not self.closing and self.operation=='reference': self.status.setText(message)

    def open_cached_reference(self):
        if self.busy or self.cached.currentIndex()<0: return
        try:
            result=load_reference(self.cached.currentData())
            self._show_reference(result)
            self.status.setText('Cached reference revalidated and reopened without a network request.')
        except Exception as error:
            self.status.setText(f'Could not open cached reference: {error}. Previous displayed reference unchanged.')
        self._buttons()
