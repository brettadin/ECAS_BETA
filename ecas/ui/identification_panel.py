"""Local laboratory identification alongside the atmospheric comparison tools."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from hashlib import sha256
import json
import math
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QScrollArea,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from ecas.identification.engine import identify, result_to_record
from ecas.identification.library import discover_library
from ecas.observations import hash_source_file, independent_observations, observation_context, project_observation


def molecule_color(molecule):
    """Stable per-identity hue across modalities, selection orders and sessions."""
    hue = (int.from_bytes(sha256(molecule.encode('utf-8')).digest()[:4], 'big') * 137) % 360
    return QColor.fromHsv(hue, 160, 225).name()


def _label(text):
    label = QLabel(text)
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.PlainText)
    return label


class _FitWorker(QThread):
    ready = Signal(object)
    failed = Signal(str)
    progress = Signal(str)

    def __init__(self, contexts, references, threshold, parent):
        super().__init__(parent)
        self.contexts, self.references, self.threshold = contexts, references, threshold

    def run(self):
        try:
            results = []
            for index, context in enumerate(self.contexts, 1):
                if self.isInterruptionRequested():
                    return
                self.progress.emit(f'Analysing input {index}/{len(self.contexts)}: {context.label}')
                result = identify(context.spectrum, self.references,
                                  observation_metadata=context.metadata, threshold=self.threshold)
                results.append((context, result))
            self.ready.emit(results)
        except Exception as exc:
            self.failed.emit(f'Identification failed: {exc}')


class IdentificationPanel(QWidget):
    """Snapshot inputs; evaluate every selected observation independently."""

    atmospheric_requested = Signal(object)

    def __init__(self, observation_getter, *, metadata_getter=None, description_getter=None,
                 project_store=None, active_project_getter=None, library_root=None, parent=None):
        super().__init__(parent)
        self.observation_getter = observation_getter
        self.metadata_getter = metadata_getter
        self.description_getter = description_getter
        self.project_store = project_store
        self.active_project_getter = active_project_getter
        self.library_root = Path(library_root or Path(__file__).resolve().parents[2] / 'data/ECAS_Spectral_Library')
        self.contexts = []
        self.batch_results = []
        self._run_references = ()
        self._duplicates = ()
        self._worker = None
        self.molecule_checks = {}
        self.dataset_selectors = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 6)
        layout.addWidget(_label('Local molecular identification'))
        layout.addWidget(_label(
            'Fit compatible laboratory absorption measurements using real local IR or UV–Vis references. '
            'Sigma is a conditional drop-one fit score, not proof of molecular presence. '
            'For planetary transit depths, use the atmospheric model tools below.'))
        row = QHBoxLayout()
        self.import_button = QPushButton('Add observation files…')
        self.add_input_button = QPushButton('Add current input')
        self.project_button = QPushButton('Add active project observations')
        self.refresh_button = QPushButton('Refresh local library')
        for button in (self.import_button, self.add_input_button, self.project_button, self.refresh_button):
            row.addWidget(button)
        layout.addLayout(row)
        row = QHBoxLayout()
        row.addWidget(_label('Planet / input group'))
        self.planet_selector = QComboBox()
        self.planet_selector.addItem('All inputs', '')
        row.addWidget(self.planet_selector, 1)
        layout.addLayout(row)
        self.observations = QListWidget()
        self.observations.setMaximumHeight(110)
        layout.addWidget(self.observations)
        self.selection_status = _label('No observations added. Select one or more files, or add project observations.')
        layout.addWidget(self.selection_status)
        self.molecule_tabs = QTabWidget()
        self.molecule_tabs.setMaximumHeight(190)
        layout.addWidget(self.molecule_tabs)
        self.library_status = _label('')
        layout.addWidget(self.library_status)
        row = QHBoxLayout()
        self.identify_button = QPushButton('Identify Molecules')
        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(1., 20.)
        self.threshold.setValue(3.)
        self.threshold.setSuffix(' σ score')
        self.threshold.setToolTip('Original v1 default threshold: 3. This is not a calibrated detection significance.')
        row.addWidget(self.identify_button)
        row.addWidget(_label('Conditional score threshold'))
        row.addWidget(self.threshold)
        self.export_button = QPushButton('Export analysis record')
        self.export_button.setEnabled(False)
        row.addWidget(self.export_button)
        layout.addLayout(row)
        self.reproduce_button = QPushButton('Open and reproduce saved identification')
        layout.addWidget(self.reproduce_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.status = _label('Import an absorption observation in Spectral Data, add it here, then select references.')
        layout.addWidget(self.status)
        self.atmospheric_button = QPushButton('Open atmospheric comparison for checked inputs')
        self.atmospheric_button.setToolTip('Transfer observations with their identities and metadata. Choose real atmospheric opacities and review model settings there.')
        self.atmospheric_button.setVisible(False)
        layout.addWidget(self.atmospheric_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.plot_status = _label('Add an observation to preview its measured spectrum; no fit is needed.')
        layout.addWidget(self.plot_status)
        self.result_selector = QComboBox()
        self.result_selector.setToolTip('Inspect one independently evaluated observation at a time.')
        layout.addWidget(self.result_selector)
        self.plot = pg.PlotWidget()
        self.plot.setMinimumHeight(230)
        self.plot.addLegend()
        self.plot.setLabel('bottom', 'Wavenumber', units='cm⁻¹')
        layout.addWidget(self.plot)
        self.reference_toggle = QPushButton('Show selected reference spectra')
        layout.addWidget(self.reference_toggle, 0, Qt.AlignmentFlag.AlignLeft)
        self.reference_plots = QTabWidget()
        self.reference_plots.setMinimumHeight(230)
        self.reference_plots.hide()
        layout.addWidget(self.reference_plots)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(120)
        layout.addWidget(self.details)
        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels(['Observation', 'Molecule', 'Modality', 'Colour', 'Sigma', 'Status'])
        self.results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.results_table.setMinimumHeight(140)
        self.results_table.setMaximumHeight(230)
        layout.addWidget(self.results_table)
        self.add_input_button.clicked.connect(self.add_current_input)
        self.import_button.clicked.connect(self.import_files)
        self.project_button.clicked.connect(self.add_project_observations)
        self.refresh_button.clicked.connect(self.refresh_library)
        self.identify_button.clicked.connect(lambda: self.run_identification())
        self.export_button.clicked.connect(self.export_record)
        self.reproduce_button.clicked.connect(self.open_record)
        self.result_selector.currentIndexChanged.connect(self.show_result)
        self.planet_selector.currentIndexChanged.connect(self._filter_observations)
        self.observations.itemChanged.connect(self.invalidate_results)
        self.observations.currentRowChanged.connect(self._show_current_input)
        self.threshold.valueChanged.connect(self.invalidate_results)
        self.reference_toggle.clicked.connect(self._toggle_reference_plots)
        self.atmospheric_button.clicked.connect(lambda: self.atmospheric_requested.emit(self.selected_contexts()))
        self.refresh_library()

    def invalidate_results(self, *_):
        if self.batch_results:
            self.status.setText('Selection changed; run Identify Molecules to update the results.')
        self.batch_results = []
        self.results_table.setRowCount(0)
        self.result_selector.clear()
        self.plot.clear()
        self.details.clear()
        self.export_button.setEnabled(False)
        self._update_selection_status()
        self._show_current_input()
        if not self.reference_plots.isHidden():
            self._show_reference_plots()

    def selected_contexts(self):
        return [context for index, context in enumerate(self.contexts)
                if self.observations.item(index).checkState() == Qt.CheckState.Checked
                and not self.observations.item(index).isHidden()]

    @staticmethod
    def _is_transit(context):
        kind = (context.spectrum.signal_type or '').lower()
        return 'transit' in kind or kind == 'transmission'

    def _update_selection_status(self):
        selected = self.selected_contexts()
        self.selection_status.setText(
            f'{len(selected)} checked observation(s) in this group; {len(self.contexts)} loaded. '
            'All checked inputs run separately. Click a row to preview it.')
        self.atmospheric_button.setVisible(any(self._is_transit(c) for c in selected))

    @staticmethod
    def _plot_measurements(plot, spectrum, *, name, color):
        # Display source values in source units, even when fitting is ineligible.
        # Do not transform transit depth into a laboratory observable.
        pairs = [(float(row['wavelength']), float(row['signal'])) for row in spectrum.rows
                 if all(isinstance(row.get(key), (int, float)) and math.isfinite(row[key])
                        for key in ('wavelength', 'signal'))]
        if pairs:
            pairs.sort(key=lambda pair: pair[0])
            x, y = zip(*pairs)
            plot.plot(x, y, pen=pg.mkPen(color, width=1.5), name=name,
                      symbol='o' if len(pairs) == 1 else None, symbolSize=5)
        return len(pairs)

    def _show_current_input(self, *_):
        index = self.observations.currentRow()
        if index < 0 or self.observations.item(index).isHidden():
            index = next((i for i in range(len(self.contexts)) if not self.observations.item(i).isHidden()), -1)
        if index < 0:
            self.plot.clear()
            self.plot.setTitle('Observation preview')
            self.plot_status.setText('Add an observation to preview it. Selected references can be viewed separately below.')
            return
        context = self.contexts[index]
        if self.batch_results:
            result_index = next((i for i, (c, _) in enumerate(self.batch_results)
                                 if c.observation_id == context.observation_id), None)
            if result_index is not None:
                self.result_selector.setCurrentIndex(result_index)
                self.show_result(result_index)
                return
        self._preview_observation(context)

    def _preview_observation(self, context):
        self.plot.clear()
        spectrum = context.spectrum
        self.plot.setTitle('Measured input — preview, no fit')
        self.plot.setLabel('bottom', 'Spectral coordinate', units=spectrum.axis_unit or 'unknown')
        self.plot.setLabel('left', spectrum.signal_type or 'Signal', units=spectrum.signal_unit or 'unknown')
        count = self._plot_measurements(self.plot, spectrum, name='Measured input', color='#d8dee9')
        self.plot.enableAutoRange()
        message = f'{context.label}: {count} measured points shown in original units. '
        if self._is_transit(context):
            message += ('This is planetary transit depth, not laboratory transmittance. '
                        'Use atmospheric comparison for a physical model; a local-library sigma is unavailable.')
        else:
            message += 'Select compatible references and run Identify Molecules to calculate a fit.'
        self.plot_status.setText(message)
        self.details.setPlainText(f'Input: {context.observation_id}\nSource: {spectrum.source_file}\n'
                                  'Measured preview only; no fit or sigma is displayed.')

    def _toggle_reference_plots(self):
        visible = self.reference_plots.isHidden()
        self.reference_plots.setVisible(visible)
        self.reference_toggle.setText('Hide selected reference spectra' if visible else 'Show selected reference spectra')
        if visible:
            self._show_reference_plots()

    def _show_reference_plots(self):
        while self.reference_plots.count():
            widget = self.reference_plots.widget(0)
            self.reference_plots.removeTab(0)
            widget.deleteLater()
        grouped = defaultdict(list)
        for ref in self.selected_references():
            spectrum = ref.spectrum
            grouped[(ref.modality, spectrum.signal_type, spectrum.axis_unit, spectrum.signal_unit)].append(ref)
        for (modality, kind, axis, unit), refs in grouped.items():
            plot = pg.PlotWidget()
            plot.addLegend()
            plot.setTitle('Source reference measurements — no scaling or fit')
            plot.setLabel('bottom', 'Spectral coordinate', units=axis or 'unknown')
            plot.setLabel('left', kind or 'Signal', units=unit or 'unknown')
            for ref in refs:
                self._plot_measurements(plot, ref.spectrum, name=ref.molecule, color=molecule_color(ref.molecule))
            self.reference_plots.addTab(plot, f'{modality} / {unit} / {axis}')
        if not grouped:
            self.reference_plots.addTab(_label('Check one or more IR or UV–Vis molecules to preview the real reference measurements.'), 'No references selected')

    def refresh_library(self):
        selected = {key for key, check in self.molecule_checks.items() if check.isChecked()}
        previous = {key: widget.currentData() for key, widget in self.dataset_selectors.items()}
        self.invalidate_results()
        self.catalog = discover_library(self.library_root)
        self.molecule_tabs.clear()
        self.molecule_checks, self.dataset_selectors = {}, {}
        for modality in ('IR', 'UV-Vis'):
            page = QWidget()
            rows = QVBoxLayout(page)
            grouped = defaultdict(list)
            for dataset in self.catalog.datasets:
                if dataset.modality == modality:
                    grouped[dataset.molecule].append(dataset)
            for molecule, variants in sorted(grouped.items()):
                key = (modality, molecule)
                line = QHBoxLayout()
                check = QCheckBox(molecule)
                check.setStyleSheet(f'color: {molecule_color(molecule)}')
                check.setChecked(key in selected)
                selector = QComboBox()
                for ref in variants:
                    selector.addItem(ref.source_path.name, ref.dataset_id)
                if previous.get(key) is not None:
                    idx = selector.findData(previous[key])
                    if idx >= 0:
                        selector.setCurrentIndex(idx)
                self.molecule_checks[key] = check
                self.dataset_selectors[key] = selector
                line.addWidget(check)
                line.addWidget(selector, 1)
                rows.addLayout(line)
                check.toggled.connect(self.invalidate_results)
                selector.currentIndexChanged.connect(self.invalidate_results)
                selector.setToolTip('Choose one source/condition variant per molecule. No automatic merging.')
            rows.addStretch()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            self.molecule_tabs.addTab(scroll, f'{modality} molecules ({len(grouped)})')
        self.library_status.setText(f'{len(self.catalog.datasets)} real local reference datasets; '
                                    f'{len(self.catalog.issues)} discovery issue(s). Select a source variant explicitly.')
        self.library_status.setToolTip('\n'.join(self.catalog.issues) or str(self.library_root))
        if not self.reference_plots.isHidden():
            self._show_reference_plots()

    def _add_context(self, context):
        if any(old.observation_id == context.observation_id for old in self.contexts):
            return False
        self.contexts.append(context)
        item = QListWidgetItem(context.label)
        item.setData(Qt.ItemDataRole.UserRole, context.observation_id)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked)
        item.setToolTip(f'{context.spectrum.source_file}\nSHA-256: {context.source_sha256 or "unknown"}')
        self.observations.addItem(item)
        planets = {self.planet_selector.itemData(i) for i in range(self.planet_selector.count())}
        if context.planet and context.planet not in planets:
            self.planet_selector.addItem(context.planet, context.planet)
        self._filter_observations()
        self.observations.setCurrentItem(item)
        return True

    def import_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Add observation files', '',
            'Spectrum files (*.csv *.tbl *.ecsv *.dat *.tsv *.txt *.asc *.fits *.fit *.fts *.jdx *.dx *.jcamp *.jcm)')
        if paths:
            self.add_files(paths)

    def add_files(self, paths):
        from ecas.ingestion.import_manager import import_spectrum
        from ecas.ingestion.nasa_table import import_transmission_table
        self.invalidate_results()
        added, errors = 0, []
        for path in map(Path, paths):
            try:
                if path.suffix.lower() == '.tbl':
                    source = import_transmission_table(path)
                    spectrum, digest = source.spectrum, source.source_sha256
                    table = dict(source.metadata)
                    metadata = {'source_table_metadata': table, 'pl_name': table.get('PL_NAME', ''),
                                'instrument': table.get('INSTRUMENT', ''), 'reference': table.get('REFERENCE', '')}
                else:
                    digest = hash_source_file(path)
                    spectrum = import_spectrum(path)
                    metadata = {}
                    if hash_source_file(path) != digest:
                        raise ValueError('Source changed during import; try again')
                label = ' | '.join(str(metadata[key]) for key in ('pl_name', 'instrument', 'reference') if metadata.get(key))
                added += self._add_context(observation_context(spectrum, digest, metadata, label or path.name))
            except (OSError, ValueError) as exc:
                errors.append(f'{path.name}: {exc}')
        self.status.setText(f'Added {added} observation(s). {len(errors)} import failure(s). '
                            'Checked inputs will be analysed separately.' + ('\n' + '\n'.join(errors) if errors else ''))

    def add_current_input(self):
        spectrum, digest = self.observation_getter()
        if spectrum is None:
            self.status.setText('Import or open an input spectrum first.')
            return
        self.invalidate_results()
        metadata = self.metadata_getter() if self.metadata_getter else {}
        label = self.description_getter() if self.description_getter else None
        added = self._add_context(observation_context(spectrum, digest, metadata, label))
        self.status.setText('Input snapshot added.' if added else 'This input identity is already listed.')

    def add_project_observations(self):
        project = self.active_project_getter() if self.active_project_getter else ''
        if not self.project_store or not project:
            self.status.setText('Select an existing project in Projects first.')
            return
        try:
            records = self.project_store.spectra(project)
            self.invalidate_results()
            added = sum(self._add_context(project_observation(project, record)) for record in records)
            self.status.setText(f'Added {added} observations from {project}; individual record identities retained.')
        except Exception as exc:
            self.status.setText(f'Could not load project observations: {exc}')

    def _filter_observations(self, *_):
        planet = self.planet_selector.currentData()
        for index, context in enumerate(self.contexts):
            self.observations.item(index).setHidden(bool(planet and context.planet != planet))
        self.invalidate_results()

    def selected_references(self):
        ids = {self.dataset_selectors[key].currentData() for key, check in self.molecule_checks.items() if check.isChecked()}
        return tuple(ref for ref in self.catalog.datasets if ref.dataset_id in ids)

    def run_identification(self, *, synchronous=False):
        if self._worker is not None and self._worker.isRunning():
            return
        contexts = self.selected_contexts()
        references = self.selected_references()
        self.invalidate_results()
        if not contexts or not references:
            self.status.setText('Check at least one input and one IR or UV–Vis molecule.')
            return
        contexts, self._duplicates = independent_observations(contexts)
        self._run_references = references
        if synchronous:
            self._receive([(context, identify(context.spectrum, references,
                           observation_metadata=context.metadata, threshold=self.threshold.value())) for context in contexts])
            return
        self._worker = _FitWorker(contexts, references, self.threshold.value(), self)
        self._worker.ready.connect(self._receive)
        self._worker.failed.connect(self._failed)
        self._worker.progress.connect(self.status.setText)
        self._worker.finished.connect(lambda: self._set_busy(False))
        self._set_busy(True)
        self.status.setText(f'Fitting {len(contexts)} independent input(s)…')
        self._worker.start()

    def _set_busy(self, busy):
        for widget in (self.identify_button, self.import_button, self.add_input_button, self.project_button,
                       self.refresh_button, self.molecule_tabs, self.observations,
                       self.threshold, self.planet_selector, self.reproduce_button, self.atmospheric_button):
            widget.setEnabled(not busy)

    def _failed(self, message):
        self.invalidate_results()
        self.status.setText(message)

    def _receive(self, results):
        self.batch_results = results
        self.result_selector.blockSignals(True)
        self.result_selector.clear()
        self.results_table.setRowCount(0)
        for context, result in results:
            outcome = 'fit available' if result.x else 'not fitted'
            self.result_selector.addItem(f'{context.label} — {outcome}')
            for component in result.components:
                self._result_row(context, component.molecule, component.modality, component.sigma,
                                 component.reason or component.status, component.dataset_id)
        for context in self._duplicates:
            for ref in self._run_references:
                self._result_row(context, ref.molecule, ref.modality, None,
                                 'Duplicate source product; not evaluated as independent evidence', ref.dataset_id)
        self.result_selector.blockSignals(False)
        self.results_table.resizeColumnsToContents()
        self.export_button.setEnabled(bool(results))
        fitted = sum(c.status == 'evaluated' for _, result in results for c in result.components)
        self.status.setText(f'{len(results)} input(s) processed separately; {fitted} candidate fit(s); '
                            f'{len(self._duplicates)} duplicate product(s) excluded. '
                            'Scores are conditional fit statistics; see limitations below.')
        if not fitted:
            reasons = list(dict.fromkeys(c.reason for _, result in results for c in result.components if c.reason))
            self.status.setText(f'No compatible fit for {len(results)} input(s). ' + ' '.join(reasons))
        self.show_result(0)

    def _result_row(self, context, molecule, modality, sigma, status, dataset_id):
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        values = (context.label, molecule, modality, molecule_color(molecule),
                  'N/A' if sigma is None else f'{sigma:.3g}', status)
        for column, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setToolTip(f'Observation: {context.observation_id}\nReference: {dataset_id}\n{status}')
            if column in (1, 3):
                item.setForeground(QColor(molecule_color(molecule)))
            self.results_table.setItem(row, column, item)

    def show_result(self, index):
        self.plot.clear()
        if not 0 <= index < len(self.batch_results):
            return
        context, result = self.batch_results[index]
        cross_section = result.settings.get('fit_quantity') == 'cross_section'
        if result.x:
            self.plot.setTitle('Laboratory fit — ' + context.label)
            self.plot_status.setText(f'{context.label}: {len(result.x)} points in the fitted common window. '
                                     'Use the result selector to inspect each independently analysed input.')
            self.plot.setLabel('bottom', 'Wavenumber', units='cm⁻¹')
            self.plot.setLabel('left', 'Measured cross section' if cross_section else 'Optical depth',
                               units='cm²/molecule' if cross_section else 'dimensionless')
            self.plot.plot(result.x, result.observed, pen=pg.mkPen('#d8dee9', width=1), name='Input')
            self.plot.plot(result.x, result.model, pen=pg.mkPen('#ffffff', width=2), name='Joint model + continuum')
            by_id = {ref.dataset_id: ref for ref in self._run_references}
            for identity, curve in result.component_curves.items():
                ref = by_id[identity]
                self.plot.plot(result.x, curve, pen=pg.mkPen(molecule_color(ref.molecule), width=2),
                               name=f'{ref.molecule} ({ref.modality})')
            self.plot.enableAutoRange()
        else:
            self._preview_observation(context)
            reasons = list(dict.fromkeys(c.reason for c in result.components if c.reason))
            self.plot_status.setText(self.plot_status.text() + '\nNot fitted: ' + ' '.join(reasons))
        blocked = '\n'.join(f'{c.molecule} ({c.modality}): {c.reason}' for c in result.components if c.status == 'blocked')
        limitations = '\n'.join(result.warnings)
        noise = ('No fit performed' if not result.x else
                 'estimated from residuals' if result.sigma_estimated else 'supplied uncertainties')
        self.details.setPlainText(f'Input: {context.observation_id}\n'
                                  f'Noise: {noise}\n'
                                  f'{blocked}\n'
                                  f'{limitations}\nSettings: {json.dumps(result.settings, ensure_ascii=False)}')

    def analysis_record(self):
        """Full immutable inputs plus method results for offline audit/reproduction."""
        if not self.batch_results:
            raise ValueError('Run an analysis before exporting')
        payload = {'observations': [asdict(context) for context, _ in self.batch_results],
                   'references': [asdict(ref) for ref in self._run_references],
                   'results': [result_to_record(result) for _, result in self.batch_results],
                   'duplicates': [asdict(context) for context in self._duplicates]}
        # Round-trip Path and tuple values to the exact JSON representation being hashed.
        payload = json.loads(json.dumps(payload, default=str, allow_nan=False))
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        return {'schema': 'ecas-identification-batch-v1', 'payload': payload,
                'sha256': sha256(encoded).hexdigest()}

    def export_record(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Export identification analysis', 'identification.json', 'JSON (*.json)')
        if not path:
            return
        try:
            from ecas.identification_records import save_record
            save_record(path, self.analysis_record())
            self.status.setText(f'Exported inputs, provenance, settings and results: {path}')
        except (OSError, ValueError) as exc:
            self.status.setText(f'Export failed: {exc}')

    def open_record(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Reproduce identification', '', 'JSON (*.json)')
        if not path:
            return
        self.invalidate_results()
        try:
            from ecas.identification_records import load_record, reproduce_record, record_inputs
            record = load_record(path)
            results = reproduce_record(record)
            contexts, self._run_references, self._duplicates = record_inputs(record)
            self._receive(list(zip(contexts, results)))
            self.status.setText('Reproduced saved arrays and settings successfully. Original raw files were not re-ingested.')
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.status.setText(f'Reproduction failed: {exc}')

    def shutdown(self):
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.wait()
