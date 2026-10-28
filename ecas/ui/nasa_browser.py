"""User-initiated NASA transmission discovery/download and offline cache access."""
from pathlib import Path
from collections import Counter

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget

from ecas.ingestion.nasa_archive import (
    INTERFACE, spectra_search, parse_spectra, spectrum_url, cache_entries, read_cached, store_spectrum,
)
from ecas.ingestion.nasa_discovery import planet_search
from ecas.ingestion.nasa_network import PublicNasaHttp
from ecas.ingestion.nasa_aliases import alias_search, parse_aliases


class NasaArchiveBrowser(QWidget):
    spectrumReady = Signal(str)

    def __init__(self, parent=None, *, cache_root=None, http=None):
        super().__init__(parent)
        project = Path(__file__).resolve().parents[2]
        self.cache_root = Path(cache_root) if cache_root is not None else project / "data/NASA/cache"
        if cache_root is None and not self.cache_root.resolve().is_relative_to(project):
            raise ValueError("NASA cache must stay inside the project")
        self.http = http if http is not None else PublicNasaHttp(self)
        self.busy = False
        self.items = []
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.target = QLineEdit()
        self.target.setPlaceholderText("Planet name or alias, e.g. WASP39b")
        self.search_button = QPushButton("Search NASA")
        self.cache_button = QPushButton("Cached spectra")
        self.cancel_button = QPushButton("Cancel")
        controls.addWidget(self.target)
        for button in (self.search_button, self.cache_button, self.cancel_button):
            controls.addWidget(button)
        layout.addLayout(controls)
        self.status = QLabel("Search public NASA metadata; only supported transmission tables can be loaded.")
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.results = QListWidget()
        self.results.setObjectName('nasaResults')
        self.results.setStyleSheet('QListWidget#nasaResults::item { padding: 4px 6px; }')
        self.results.setSpacing(1)
        self.results.setMaximumHeight(130)
        layout.addWidget(self.results)
        self.load_button = QPushButton("Download selected spectrum")
        layout.addWidget(self.load_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.search_button.clicked.connect(self.search)
        self.cache_button.clicked.connect(self.show_cache)
        self.cancel_button.clicked.connect(self.cancel)
        self.load_button.clicked.connect(self.load_selected)
        self.results.currentRowChanged.connect(lambda _: self._buttons())
        self._buttons()

    def _buttons(self):
        self.search_button.setEnabled(not self.busy)
        self.cache_button.setEnabled(not self.busy)
        self.target.setEnabled(not self.busy)
        self.results.setEnabled(not self.busy)
        self.cancel_button.setEnabled(self.busy)
        self.load_button.setEnabled(not self.busy and 0 <= self.results.currentRow() < len(self.items))

    def _fail(self, error):
        self.busy = False
        self.status.setText(f"NASA operation stopped: {error}. Existing displayed data is unchanged.")
        self._buttons()

    def _request(self, url, handler):
        self.busy = True
        self._buttons()

        def completed(raw, error):
            if error:
                self._fail(error)
                return
            try:
                handler(raw)
            except Exception as failure:
                self._fail(failure)
        try:
            self.http.get(url, completed)
        except Exception as error:
            self._fail(error)

    def cancel(self):
        self.http.cancel()

    def search(self):
        if self.busy:
            return
        try:
            name = planet_search(self.target.text()).name
            lookup_url = alias_search(name)
        except ValueError as error:
            self._fail(error)
            return
        self.items = []
        self.results.clear()
        self.load_button.setText("Download selected spectrum")
        self.status.setText("Resolving the planet name with NASA…")

        def resolved(raw):
            canonical = parse_aliases(raw, name)
            self.status.setText(f"Resolved {name} as {canonical}; searching NASA spectra…")
            self._request(spectra_search(canonical), lambda body: receive(body, canonical))

        def receive(raw, canonical):
            url = spectra_search(canonical)
            rows = parse_spectra(raw, canonical)
            self.evidence = {"url": url, "raw": raw}
            self.items = [{"metadata": row} for row in rows if row["spec_type"] == "Transmission"]
            for item in self.items:
                row = item["metadata"]
                self.results.addItem(f"{row['pl_name']} | {row['authors']} | {row['instrument']} | {row['num_datapoints']} points")
            self.busy = False
            message = (f"{name} resolved as {canonical}: {len(self.items)} transmission records "
                       f"available to load out of {len(rows)} returned records.")
            excluded = Counter(row['spec_type'] for row in rows if row['spec_type'] != 'Transmission')
            if excluded:
                message += ' Excluded from loading: ' + ', '.join(
                    f'{kind} ({count})' for kind, count in sorted(excluded.items())) + '.'
            if len(rows) == 50:
                message += ' 50-record limit reached, results may be incomplete.'
            self.status.setText(message)
            if not rows:
                self.status.setText(f"{name} resolved as {canonical}. No spectra listed in NASA's queried spectroscopy table. Other archives were not searched.")
            elif not self.items:
                types = ', '.join(sorted({row['spec_type'] for row in rows}))
                self.status.setText(f"{canonical}: archive records exist ({types}), but no supported transmission records were returned.")
                if len(rows) == 50:
                    self.status.setText(self.status.text() + " 50-record limit reached; results may be incomplete.")
            self._buttons()
        self._request(lookup_url, resolved)

    def show_cache(self):
        if self.busy:
            return
        self.items = []
        self.results.clear()
        try:
            entries, invalid = cache_entries(self.cache_root)
            for record, source in entries:
                self.items.append({"cached": source.parent})
                row = record["metadata"]
                self.results.addItem(f"{row['pl_name']} | {row['authors']} | cached {record['retrieved_utc']}")
            self.load_button.setText("Load cached spectrum")
            self.status.setText(f"{len(entries)} verified cached spectra; {invalid} invalid or incomplete entries excluded.")
            self._buttons()
        except Exception as error:
            self._fail(error)

    def load_selected(self):
        index = self.results.currentRow()
        if self.busy or not 0 <= index < len(self.items):
            return
        item = self.items[index]
        if "cached" in item:
            try:
                _, source = read_cached(item["cached"])
                self.spectrumReady.emit(str(source))
                self.status.setText("Verified cached spectrum sent to display; no network request made.")
            except Exception as error:
                self._fail(error)
            return
        metadata = dict(item["metadata"])
        evidence = dict(self.evidence)
        self.status.setText("Resolving a fresh NASA download session…")

        def page_received(page):
            url = spectrum_url(page, metadata)
            self.status.setText("Downloading and validating selected spectrum…")

            def downloaded(raw):
                source = store_spectrum(self.cache_root, metadata, raw, url, evidence)
                self.busy = False
                self._buttons()
                self.spectrumReady.emit(str(source))
                self.status.setText("Validated and cached spectrum sent to display.")
            self._request(url, downloaded)
        self._request(INTERFACE, page_received)
