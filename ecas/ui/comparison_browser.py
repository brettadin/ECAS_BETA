"""Independent, offline input inspection; no scientific comparison operations."""
from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QSplitter,
)

from ecas.ingestion.exomol_reference_cache import cached_references, load_reference


def _label(text):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


def _table():
    table = QTableWidget()
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    return table


def _fill(table, columns, rows):
    table.clearContents()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            table.setItem(i, j, QTableWidgetItem('' if value is None else str(value)))
    table.resizeColumnsToContents()


class ComparisonBrowser(QWidget):
    """Session observation snapshots and revalidated cached ExoMol references.

    The input getter reads the window's already imported observation, never a
    source file. Each explicit addition copies its values so subsequent imports
    cannot change the selected input. Reference selection never creates a client.
    """

    def __init__(self, observation_getter, cache_root, parent=None):
        super().__init__(parent)
        self.observation_getter = observation_getter
        self.cache_root = cache_root
        self.current_observation = None
        self.current_reference = None
        layout = QVBoxLayout(self)
        title = _label('Comparisons')
        title.setObjectName('pageTitle')
        layout.addWidget(title)
        layout.addWidget(_label(
            'Select inputs independently and inspect their original values below. '
            'Observation choices last for this session; open saved observations in Projects '
            'and add them here. Download references in Molecular References, then refresh '
            'the cached choices. No overlay, residual, score or detection is produced.'))
        panels = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(panels, 1)
        for side in ('observation', 'reference'):
            panel = QWidget()
            box = QVBoxLayout(panel)
            box.addWidget(_label('Observation / input' if side == 'observation' else 'Cached molecular reference'))
            controls = QHBoxLayout()
            selector = QComboBox()
            selector.setMinimumContentsLength(12)
            selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
            button = QPushButton('Add current observation' if side == 'observation' else 'Refresh cached choices')
            controls.addWidget(selector, 1)
            controls.addWidget(button)
            box.addLayout(controls)
            status = _label('No input selected.')
            table = _table()
            box.addWidget(status)
            box.addWidget(table, 1)
            setattr(self, side + '_selector', selector)
            setattr(self, side + '_status', status)
            setattr(self, side + '_table', table)
            setattr(self, side + '_button', button)
            panels.addWidget(panel)
        self.cache_status = _label('Cached choices have not been refreshed.')
        self.compatibility = _label('Select an observation and a cached reference for inspection.')
        layout.addWidget(self.cache_status)
        layout.addWidget(self.compatibility)
        self.observation_button.clicked.connect(self.add_current_observation)
        self.reference_button.clicked.connect(self.refresh_references)
        self.observation_selector.currentIndexChanged.connect(self._select_observation)
        self.reference_selector.currentIndexChanged.connect(self._select_reference)

    def add_current_observation(self):
        spectrum, source_hash = self.observation_getter()
        if spectrum is None:
            self.observation_status.setText('Load an observation in Spectral Data or Projects first. Previous selection retained.')
            return
        snapshot = deepcopy(spectrum)
        self.observation_selector.addItem(
            f'{self.observation_selector.count() + 1}: {snapshot.source_file.name} | {snapshot.row_count} rows',
            (snapshot, source_hash))
        self.observation_selector.setCurrentIndex(self.observation_selector.count() - 1)

    def _select_observation(self, *_):
        selected = self.observation_selector.currentData()
        self.current_observation = selected[0] if selected else None
        if selected:
            spectrum, source_hash = selected
            # Keep the exact hash available in the tooltip; shorter lines prevent
            # a long unbroken identifier from crowding the split inspection pane.
            hash_display = ('\n'.join(source_hash[i:i + 32] for i in range(0, len(source_hash), 32))
                            if source_hash else 'not established')
            self.observation_status.setToolTip(
                f'Source: {spectrum.source_file}\nSource SHA-256: {source_hash or "not established"}')
            self.observation_status.setText(
                f'Source: {spectrum.source_file}\nObservable: {spectrum.signal_type or "unknown"}; '
                f'axis unit: {spectrum.axis_unit or "unknown"}; signal unit: {spectrum.signal_unit or "unknown"}. '
                f'Source SHA-256:\n{hash_display}\n'
                + ('Warnings: ' + '; '.join(spectrum.warnings) if spectrum.warnings else ''))
            _fill(self.observation_table, spectrum.columns,
                  [tuple(row[column] for column in spectrum.columns) for row in spectrum.rows])
        self._explain()

    def refresh_references(self):
        previous = self.reference_selector.currentData()
        self.reference_selector.blockSignals(True)
        self.reference_selector.clear()
        try:
            records, invalid = cached_references(self.cache_root / 'references')
            for path, result in records:
                request = result.request
                self.reference_selector.addItem(
                    f'{request.service.formula} / {request.service.isotopologue} / {request.service.dataset} | '
                    f'{request.temperature} K | {request.minimum}–{request.maximum} cm^-1 | '
                    f'{request.spacing} spacing | {path.stem}', str(path))
            index = self.reference_selector.findData(previous) if previous is not None else -1
            self.reference_selector.setCurrentIndex(index)
            self.cache_status.setText(f'{len(records)} cached references available; {invalid} invalid entries excluded. '
                                      'Uncached catalogue entries require a supported download in Molecular References.')
        except (OSError, ValueError) as error:
            self.cache_status.setText(f'Reference cache unavailable: {error}')
        finally:
            self.reference_selector.blockSignals(False)
        self._select_reference()

    def _select_reference(self, *_):
        self.current_reference = None
        _fill(self.reference_table, (), ())
        path = self.reference_selector.currentData()
        self.reference_status.setText('No cached reference selected.')
        self.reference_status.setToolTip('')
        if path is not None:
            try:
                result = load_reference(path)
                self.current_reference = result
                product, request = result.product, result.request
                provenance = product.provenance
                self.reference_status.setText(
                    f'{provenance.molecule} / {provenance.isotopologue} / {provenance.dataset}; '
                    f'{request.temperature} K; zero pressure; Doppler-only. Calculated absorption cross section.\n'
                    f'Source SHA-256: {product.source_sha256}\nSource: {provenance.source_url}')
                self.reference_status.setToolTip('\n'.join((*provenance.citations, provenance.licence_url)))
                _fill(self.reference_table, ('Wavenumber (cm^-1)', 'Cross section (cm^2/molecule)'), product.points)
            except (OSError, ValueError) as error:
                self.reference_status.setText(f'Cached reference unavailable or invalid: {error}')
        self._explain()

    def _explain(self):
        if self.current_observation is None or self.current_reference is None:
            self.compatibility.setText('Select an observation and a valid cached reference for inspection. '
                                       'Comparison operations remain unavailable.')
            return
        spectrum = self.current_observation
        reasons = [
            'Comparison blocked: this reference is a calculated absorption cross section in cm^2/molecule '
            'on wavenumber cm^-1, not a predicted transit-depth spectrum. '
            'Cross sections and transit depth cannot be compared directly without a physical model.'
        ]
        if not spectrum.signal_type or not spectrum.signal_unit or not spectrum.axis_unit:
            reasons.append('Observation observable or units are unknown; no meaning or conversion is inferred.')
        reasons.append('A physical model with documented conditions, compatible observables/units, '
                       'coordinate frame, grid alignment and instrument response evidence is required '
                       'before overlay or residual analysis. Uncertainty/noise evidence is required for '
                       'weighted diagnostics. Scientific comparison operations are not available yet.')
        self.compatibility.setText('\n'.join(reasons))
