"""Independent input inspection, gated candidate comparison, and persistence."""
from copy import deepcopy
from dataclasses import dataclass, replace
import math

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ecas import persistence as project_persistence
from ecas.comparison.alignment import (
    TransformedInput,
    convert_axis_unit,
    convert_signal_unit,
    restrict_to_shared_coordinates,
)
from ecas.comparison.candidates import evaluate_candidates
from ecas.comparison.eligibility import ComparisonInput, assess, describe_reason
from ecas.comparison.forward_model import load_forward_model_file
from ecas.comparison.inputs import observation_input, reference_input
from ecas.comparison.persistence import (
    build_comparison_record,
    load_comparison_record,
    reproduce_comparison_record,
)
from ecas.comparison.residuals import evaluate_residuals
from ecas.ingestion.exomol_reference_cache import cached_references, load_reference
from ecas.visualization.reference_plot import ReferencePlot
from ecas.visualization.residual_plot import ResidualPlot
from ecas.visualization.spectra_plot import SpectraPlot


@dataclass(frozen=True)
class _CandidateEntry:
    label: str
    comparison_input: ComparisonInput
    provenance: dict


def _eval_input(item: ComparisonInput | TransformedInput) -> ComparisonInput:
    return item.transformed if isinstance(item, TransformedInput) else item


def _steps_summary(item: ComparisonInput | TransformedInput) -> str:
    if not isinstance(item, TransformedInput) or not item.steps:
        return ''
    parts = []
    for step in item.steps:
        if step.excluded_indices:
            parts.append(
                f'{step.operation} ({len(step.included_indices)} kept, '
                f'{len(step.excluded_indices)} excluded: {step.exclusion_reason})'
            )
        else:
            parts.append(step.operation)
    return ', '.join(parts)


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


def _strictly_increasing_1d(coords: tuple) -> bool:
    if len(coords) < 3:
        return False
    try:
        arr = np.asarray(coords, dtype=float)
    except (TypeError, ValueError):
        return False
    return bool(arr.ndim == 1 and np.isfinite(arr).all() and np.all(np.diff(arr) > 0))


class ComparisonBrowser(QWidget):
    """Session observation snapshots, gated candidate comparison, and project records.

    The input getter reads the window's already imported observation, never a
    source file. Each explicit addition copies its values so subsequent imports
    cannot change the selected input. Reference selection never creates a client,
    and project persistence is accessed only on explicit user actions.
    """

    def __init__(
        self,
        observation_getter,
        cache_root,
        parent=None,
        *,
        description_getter=None,
        project_store=None,
        active_project_getter=None,
    ):
        super().__init__(parent)
        self.observation_getter = observation_getter
        self.description_getter = description_getter
        self.cache_root = cache_root
        self.project_store = project_store
        self.active_project_getter = active_project_getter
        self.current_observation = None
        self.current_observation_hash = None
        self.current_reference = None
        self.current_eligibility = None
        self.current_diagnostic = None
        self.current_candidate_summary = None
        self.residual_plot = None
        self.candidate_entries: list[_CandidateEntry] = []
        self._evaluated_candidate_records: list[dict] = []
        self._active_record_context: dict | None = None

        layout = QVBoxLayout(self)
        title = _label('Comparisons')
        title.setObjectName('pageTitle')
        layout.addWidget(title)
        layout.addWidget(_label(
            'Select inputs independently and inspect their original values below. '
            'Observation choices last for this session; open saved observations in Projects '
            'and add them here. Download references in Molecular References, then refresh '
            'the cached choices. No overlay, residual, score or detection is produced '
            'merely by selecting inputs; eligible overlays and residuals require compatible '
            'observables or validated forward-model curves. '
            'Plots use independent axes and original units; their horizontal positions do not indicate matching wavelengths.'
        ))
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
            plot = SpectraPlot() if side == 'observation' else ReferencePlot()
            views = QTabWidget()
            views.addTab(plot, 'Plot (native units)')
            views.addTab(table, 'Data table')
            box.addWidget(status)
            box.addWidget(views, 1)
            setattr(self, side + '_selector', selector)
            setattr(self, side + '_status', status)
            setattr(self, side + '_table', table)
            setattr(self, side + '_button', button)
            setattr(self, side + '_plot', plot)
            setattr(self, side + '_views', views)
            panels.addWidget(panel)

        self.cache_status = _label('Cached choices have not been refreshed.')
        layout.addWidget(self.cache_status)

        tools_bar = QHBoxLayout()
        self.workflow_toggle_button = QPushButton('Show comparison & candidate tools')
        self.candidate_status = _label('0 candidate curves staged.')
        tools_bar.addWidget(self.workflow_toggle_button)
        tools_bar.addWidget(self.candidate_status, 1)
        layout.addLayout(tools_bar)

        self.workflow_panel = QWidget()
        self._build_workflow_panel(self.workflow_panel)
        self.workflow_panel.setVisible(False)
        layout.addWidget(self.workflow_panel)

        self.compatibility = _label('Select an observation and a cached reference for inspection.')
        self.diagnostic_panel = QWidget()
        diagnostic_box = QVBoxLayout(self.diagnostic_panel)
        diagnostic_box.setContentsMargins(0, 0, 0, 0)
        self.diagnostic_summary = _label('')
        self.diagnostic_views = QTabWidget()
        self.residual_table = _table()
        self.diagnostic_views.addTab(self.residual_table, 'Residual table')
        diagnostic_box.addWidget(self.diagnostic_summary)
        diagnostic_box.addWidget(self.diagnostic_views, 1)
        self.diagnostic_panel.setVisible(False)
        layout.addWidget(self.compatibility)
        layout.addWidget(self.diagnostic_panel, 1)

        self.observation_button.clicked.connect(self.add_current_observation)
        self.reference_button.clicked.connect(self.refresh_references)
        self.observation_selector.currentIndexChanged.connect(self._select_observation)
        self.reference_selector.currentIndexChanged.connect(self._select_reference)
        self.workflow_toggle_button.clicked.connect(self._toggle_workflow_panel)

    def _build_workflow_panel(self, container: QWidget):
        box = QVBoxLayout(container)
        box.setContentsMargins(0, 4, 0, 4)
        box.setSpacing(6)
        box.addWidget(_label(
            'Caller observation attestations (optional; used only when raw import omits a field — '
            'never overrides conflicting imported metadata):'
        ))

        attest_row1 = QHBoxLayout()
        self.obs_role_selector = QComboBox()
        for text, data in (
            ('Role: (not attested)', None),
            ('Role: observation', 'observation'),
            ('Role: reference_measurement', 'reference_measurement'),
        ):
            self.obs_role_selector.addItem(text, data)

        self.obs_observable_selector = QComboBox()
        for text, data in (
            ('Observable: (from import / unknown)', None),
            ('Observable: transit_depth', 'transit_depth'),
        ):
            self.obs_observable_selector.addItem(text, data)

        self.obs_axis_unit_selector = QComboBox()
        for text, data in (
            ('Axis unit: (from import / unknown)', None),
            ('Axis unit: microns', 'microns'),
            ('Axis unit: nanometers', 'nanometers'),
            ('Axis unit: angstroms', 'angstroms'),
        ):
            self.obs_axis_unit_selector.addItem(text, data)

        self.obs_signal_unit_selector = QComboBox()
        for text, data in (
            ('Signal unit: (from import / unknown)', None),
            ('Signal unit: percent', 'percent'),
            ('Signal unit: fraction', 'fraction'),
        ):
            self.obs_signal_unit_selector.addItem(text, data)

        for widget in (
            self.obs_role_selector,
            self.obs_observable_selector,
            self.obs_axis_unit_selector,
            self.obs_signal_unit_selector,
        ):
            attest_row1.addWidget(widget)
        box.addLayout(attest_row1)

        attest_row2 = QHBoxLayout()
        self.obs_frame_input = QLineEdit()
        self.obs_frame_input.setPlaceholderText('Coordinate frame (e.g. barycentric)')
        self.obs_response_id_input = QLineEdit()
        self.obs_response_id_input.setPlaceholderText('Instrument response ID')
        self.obs_response_evidence_input = QLineEdit()
        self.obs_response_evidence_input.setPlaceholderText('Response evidence / citation')
        self.obs_noise_selector = QComboBox()
        for text, data in (
            ('Noise: (not attested)', None),
            ('Noise: 1-sigma uncorrelated (imported uncertainty)', 'independent_gaussian_1sigma'),
        ):
            self.obs_noise_selector.addItem(text, data)
        self.obs_noise_evidence_input = QLineEdit()
        self.obs_noise_evidence_input.setPlaceholderText('Noise evidence (if weighted)')
        for widget in (
            self.obs_frame_input,
            self.obs_response_id_input,
            self.obs_response_evidence_input,
            self.obs_noise_selector,
            self.obs_noise_evidence_input,
        ):
            attest_row2.addWidget(widget)
        box.addLayout(attest_row2)

        options_row = QHBoxLayout()
        self.align_checkbox = QCheckBox(
            'Opt-in explicit unit & exact shared-grid alignment (no interpolation or upsampling)'
        )
        self.weighted_checkbox = QCheckBox('Weighted residual diagnostics')
        self.independent_checkbox = QCheckBox('Attest cross-dataset error independence')
        options_row.addWidget(self.align_checkbox)
        options_row.addWidget(self.weighted_checkbox)
        options_row.addWidget(self.independent_checkbox)
        options_row.addStretch(1)
        box.addLayout(options_row)

        cand_row = QHBoxLayout()
        self.load_model_button = QPushButton('Load forward-model JSON...')
        self.add_reference_candidate_button = QPushButton('Stage selected cached reference')
        self.clear_candidates_button = QPushButton('Clear staged candidates')
        self.run_candidates_button = QPushButton('Evaluate observation vs. candidates')
        self.candidate_selector = QComboBox()
        self.candidate_selector.setMinimumContentsLength(18)
        self.candidate_selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        cand_row.addWidget(self.load_model_button)
        cand_row.addWidget(self.add_reference_candidate_button)
        cand_row.addWidget(self.clear_candidates_button)
        cand_row.addWidget(self.run_candidates_button)
        cand_row.addWidget(self.candidate_selector, 1)
        box.addLayout(cand_row)

        persist_row = QHBoxLayout()
        self.save_comparison_button = QPushButton('Save comparison to active project')
        self.refresh_saved_comparisons_button = QPushButton('Refresh project comparisons')
        self.saved_comparisons_selector = QComboBox()
        self.saved_comparisons_selector.setMinimumContentsLength(18)
        self.saved_comparisons_selector.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
        )
        self.reproduce_saved_button = QPushButton('Verify & reopen saved comparison')
        persist_row.addWidget(self.save_comparison_button)
        persist_row.addWidget(self.refresh_saved_comparisons_button)
        persist_row.addWidget(self.saved_comparisons_selector, 1)
        persist_row.addWidget(self.reproduce_saved_button)
        box.addLayout(persist_row)

        self.persistence_status = _label('Project comparison records have not been loaded.')
        box.addWidget(self.persistence_status)

        self.load_model_button.clicked.connect(self.load_forward_model)
        self.add_reference_candidate_button.clicked.connect(self.stage_selected_reference_candidate)
        self.clear_candidates_button.clicked.connect(self.clear_staged_candidates)
        self.run_candidates_button.clicked.connect(self.run_interactive_candidates)
        self.candidate_selector.currentIndexChanged.connect(self._on_candidate_selector_changed)
        self.save_comparison_button.clicked.connect(self.save_active_comparison)
        self.refresh_saved_comparisons_button.clicked.connect(self.refresh_saved_comparisons)
        self.reproduce_saved_button.clicked.connect(self.reproduce_selected_comparison)

    def _toggle_workflow_panel(self):
        visible = not self.workflow_panel.isVisible()
        self.workflow_panel.setVisible(visible)
        self.workflow_toggle_button.setText(
            'Hide comparison & candidate tools' if visible else 'Show comparison & candidate tools'
        )

    def _active_project_name(self) -> str:
        if self.active_project_getter is None:
            return ''
        name = self.active_project_getter()
        return name.strip() if isinstance(name, str) else ''

    def _sync_staged_candidate_selector(self):
        self.candidate_selector.blockSignals(True)
        try:
            self.candidate_selector.clear()
            for idx, entry in enumerate(self.candidate_entries):
                self.candidate_selector.addItem(f'[{idx}] {entry.label} (staged)', idx)
        finally:
            self.candidate_selector.blockSignals(False)
        self.candidate_status.setText(f'{len(self.candidate_entries)} candidate curves staged.')

    def load_forward_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            'Load Forward-Model Transit Spectrum (ecas-forward-model-v1)',
            '',
            'JSON files (*.json);;All files (*)',
        )
        if not path:
            return None
        return self.load_forward_model_from_path(path)

    def load_forward_model_from_path(self, path):
        try:
            loaded = load_forward_model_file(path)
        except (OSError, ValueError, TypeError) as error:
            self.candidate_status.setText(f'Forward-model load rejected: {error}')
            return None
        inp = loaded.comparison_input
        prov = loaded.provenance
        label = (
            f'{inp.source_id} ({prov.engine_name} {prov.engine_version}, '
            f'{len(inp.coordinates)} pts, {inp.axis_unit}, {inp.signal_unit})'
        )
        entry = _CandidateEntry(
            label=label,
            comparison_input=inp,
            provenance=loaded.to_provenance_dict(),
        )
        self.candidate_entries.append(entry)
        self.current_candidate_summary = None
        self._evaluated_candidate_records = []
        self._sync_staged_candidate_selector()
        self.candidate_status.setText(
            f'Loaded forward model {inp.source_id} ({len(self.candidate_entries)} staged).'
        )
        return loaded

    def stage_selected_reference_candidate(self):
        if self.current_reference is None:
            self.candidate_status.setText('Select a valid cached molecular reference first.')
            return None
        adapted = reference_input(self.current_reference)
        product = self.current_reference.product
        request = self.current_reference.request
        prov = product.provenance
        label = (
            f'{prov.molecule}/{prov.dataset} {request.temperature}K '
            f'(cross section, {product.coordinate_unit})'
        )
        entry = _CandidateEntry(
            label=label,
            comparison_input=adapted.comparison_input,
            provenance={
                'kind': 'cached_exomol_reference',
                'molecule': prov.molecule,
                'isotopologue': prov.isotopologue,
                'dataset': prov.dataset,
                'temperature_k': request.temperature,
                'source_url': prov.source_url,
                'source_sha256': product.source_sha256,
            },
        )
        self.candidate_entries.append(entry)
        self.current_candidate_summary = None
        self._evaluated_candidate_records = []
        self._sync_staged_candidate_selector()
        self.candidate_status.setText(
            f'Staged cached reference {prov.molecule}/{prov.dataset} '
            f'({len(self.candidate_entries)} staged).'
        )
        return entry

    def clear_staged_candidates(self):
        self.candidate_entries.clear()
        self._evaluated_candidate_records.clear()
        self.current_candidate_summary = None
        self._sync_staged_candidate_selector()
        self._explain()

    def _build_attested_observation(self) -> tuple[ComparisonInput, dict, list[str]]:
        if self.current_observation is None:
            raise ValueError('Select an observation in Comparisons first')
        spectrum = self.current_observation
        adapted = observation_input(spectrum, self.current_observation_hash)
        base = adapted.comparison_input
        attestations: dict[str, object] = {}

        role = base.role
        ui_role = self.obs_role_selector.currentData()
        if ui_role is not None:
            role = ui_role
            attestations['role'] = ui_role

        resolved = {
            'observable': base.observable,
            'axis_unit': base.axis_unit,
            'signal_unit': base.signal_unit,
        }
        for field_name, selector in (
            ('observable', self.obs_observable_selector),
            ('axis_unit', self.obs_axis_unit_selector),
            ('signal_unit', self.obs_signal_unit_selector),
        ):
            ui_val = selector.currentData()
            if ui_val is not None:
                imp_val = resolved[field_name]
                if imp_val is not None and imp_val != ui_val:
                    raise ValueError(
                        f'Caller attestation for {field_name} ({ui_val!r}) conflicts '
                        f'with imported metadata ({imp_val!r})'
                    )
                if imp_val is None:
                    resolved[field_name] = ui_val
                    attestations[field_name] = ui_val

        frame = base.coordinate_frame
        ui_frame = self.obs_frame_input.text().strip()
        if ui_frame:
            frame = ui_frame
            attestations['coordinate_frame'] = ui_frame

        resp_id = base.response_id
        ui_resp_id = self.obs_response_id_input.text().strip()
        if ui_resp_id:
            resp_id = ui_resp_id
            attestations['response_id'] = ui_resp_id

        resp_ev = base.response_evidence
        ui_resp_ev = self.obs_response_evidence_input.text().strip()
        if ui_resp_ev:
            resp_ev = ui_resp_ev
            attestations['response_evidence'] = ui_resp_ev

        noise_kind = base.noise_kind
        noise_ev = base.noise_evidence
        sigma = base.sigma
        ui_noise_kind = self.obs_noise_selector.currentData()
        ui_noise_ev = self.obs_noise_evidence_input.text().strip()
        if ui_noise_kind == 'independent_gaussian_1sigma':
            unc_map = dict(adapted.raw_uncertainty_columns)
            raw_unc = unc_map.get('uncertainty')
            if raw_unc is None or len(raw_unc) != len(base.values):
                raise ValueError(
                    'Cannot attest 1-sigma uncertainty: imported observation has no uncertainty column'
                )
            parsed_sigma: list[float] = []
            for val in raw_unc:
                if (
                    isinstance(val, bool)
                    or not isinstance(val, (int, float))
                    or not math.isfinite(val)
                    or val <= 0
                ):
                    raise ValueError(
                        'Cannot attest 1-sigma uncertainty: imported uncertainty column contains non-positive or missing values'
                    )
                parsed_sigma.append(float(val))
            sigma = tuple(parsed_sigma)
            noise_kind = ui_noise_kind
            attestations['noise_kind'] = ui_noise_kind
            if ui_noise_ev:
                noise_ev = ui_noise_ev
                attestations['noise_evidence'] = ui_noise_ev

        updated = replace(
            base,
            role=role,
            observable=resolved['observable'],
            axis_unit=resolved['axis_unit'],
            signal_unit=resolved['signal_unit'],
            coordinate_frame=frame,
            response_id=resp_id,
            response_evidence=resp_ev,
            noise_kind=noise_kind,
            noise_evidence=noise_ev,
            sigma=sigma,
        )
        provenance = {
            'kind': 'imported_observation_snapshot',
            'source_file': str(spectrum.source_file),
            'source_sha256': self.current_observation_hash,
            'importer_mappings': [list(item) for item in adapted.mappings],
            'caller_attestations': attestations,
        }
        notes: list[str] = []
        if attestations:
            notes.append(
                'Caller-supplied UI metadata attestations were applied for fields not '
                f'established by raw import: {", ".join(sorted(attestations))}.'
            )
        return updated, provenance, notes

    def _align_inputs_for_candidates(
        self,
        left_input: ComparisonInput,
        candidate_inputs: list[ComparisonInput],
    ) -> tuple[ComparisonInput | TransformedInput, list[ComparisonInput | TransformedInput], list[str]]:
        if not self.align_checkbox.isChecked():
            return left_input, list(candidate_inputs), []

        notes: list[str] = []
        left_item: ComparisonInput | TransformedInput = left_input
        if left_input.observable == 'transit_depth' and left_input.axis_unit in ('nanometers', 'nm', 'angstroms'):
            left_item = convert_axis_unit(left_item, 'microns')
        left_cur = _eval_input(left_item)

        stage1: list[ComparisonInput | TransformedInput] = []
        for cand in candidate_inputs:
            c_item: ComparisonInput | TransformedInput = cand
            if cand.observable == 'transit_depth':
                if cand.axis_unit in ('nanometers', 'nm', 'angstroms'):
                    c_item = convert_axis_unit(c_item, 'microns')
                c_cur = _eval_input(c_item)
                if (
                    left_cur.signal_unit in ('percent', 'fraction')
                    and c_cur.signal_unit in ('percent', 'fraction')
                    and c_cur.signal_unit != left_cur.signal_unit
                ):
                    c_item = convert_signal_unit(c_item, left_cur.signal_unit)
            stage1.append(c_item)

        if (
            left_cur.observable == 'transit_depth'
            and left_cur.axis_unit == 'microns'
            and left_cur.coordinate_frame
            and _strictly_increasing_1d(left_cur.coordinates)
        ):
            left_coord_set = set(left_cur.coordinates)
            alignable_indices: list[int] = []
            for idx, c_item in enumerate(stage1):
                c_cur = _eval_input(c_item)
                if (
                    c_cur.observable == 'transit_depth'
                    and c_cur.axis_unit == left_cur.axis_unit
                    and c_cur.coordinate_frame == left_cur.coordinate_frame
                    and _strictly_increasing_1d(c_cur.coordinates)
                    and len(left_coord_set & set(c_cur.coordinates)) >= 3
                ):
                    alignable_indices.append(idx)

            if alignable_indices:
                common_set = set(left_cur.coordinates)
                for idx in alignable_indices:
                    common_set &= set(_eval_input(stage1[idx]).coordinates)
                if len(common_set) >= 3:
                    common_sorted = tuple(x for x in left_cur.coordinates if x in common_set)
                    if common_sorted != left_cur.coordinates:
                        anchor = replace(
                            left_cur,
                            coordinates=common_sorted,
                            values=tuple(0.0 for _ in common_sorted),
                            sigma=None,
                            covariance=None,
                        )
                        left_item, _ = restrict_to_shared_coordinates(left_item, anchor)
                        left_cur = _eval_input(left_item)
                    for idx in alignable_indices:
                        if _eval_input(stage1[idx]).coordinates != left_cur.coordinates:
                            _, stage1[idx] = restrict_to_shared_coordinates(left_item, stage1[idx])
                elif len(alignable_indices) > 1:
                    notes.append(
                        'Multiple candidates share fewer than 3 common exact coordinates; '
                        'shared-grid subsetting was skipped to preserve target support.'
                    )

        return left_item, stage1, notes

    def run_interactive_candidates(self):
        if self.current_observation is None:
            self.compatibility.setText(
                'Select and add an observation snapshot before evaluating candidates.'
            )
            return None
        if not self.candidate_entries:
            self.compatibility.setText(
                'Load at least one forward-model JSON or stage a cached reference candidate first.'
            )
            return None
        try:
            left_base, left_prov, notes = self._build_attested_observation()
            left_item, right_items, align_notes = self._align_inputs_for_candidates(
                left_base, [e.comparison_input for e in self.candidate_entries]
            )
        except ValueError as error:
            self._clear_diagnostic()
            self.current_eligibility = None
            self.current_candidate_summary = None
            self.compatibility.setText(f'Candidate preparation blocked: {error}')
            return None

        all_notes = tuple(notes + align_notes)
        weighted = self.weighted_checkbox.isChecked()
        independent = self.independent_checkbox.isChecked()
        if independent and weighted:
            all_notes = all_notes + (
                'Caller attested cross-dataset error independence via UI.',
            )
        return self._evaluate_and_display_candidates(
            left_item=left_item,
            right_items=right_items,
            left_provenance=left_prov,
            right_provenances=[e.provenance for e in self.candidate_entries],
            candidate_labels=[e.label for e in self.candidate_entries],
            weighted=weighted,
            cross_dataset_independent=independent,
            limitations=all_notes,
        )

    def add_current_observation(self):
        spectrum, source_hash = self.observation_getter()
        if spectrum is None:
            self.observation_status.setText('Load an observation in Spectral Data or Projects first. Previous selection retained.')
            return
        snapshot = deepcopy(spectrum)
        description = self.description_getter() if self.description_getter else snapshot.source_file.name
        self.observation_selector.addItem(
            f'{self.observation_selector.count() + 1}: {description} | {snapshot.row_count} rows',
            (snapshot, source_hash))
        self.observation_selector.setCurrentIndex(self.observation_selector.count() - 1)

    def _select_observation(self, *_):
        selected = self.observation_selector.currentData()
        self.current_observation = selected[0] if selected else None
        self.current_observation_hash = selected[1] if selected else None
        if selected:
            spectrum, source_hash = selected
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
            if not self.observation_plot.load_spectrum(spectrum):
                self.observation_status.setText(self.observation_status.text() +
                    '\nNo valid coordinate pairs for plotting; original values remain in Data table.')
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
        self.reference_plot.clear()
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
                self.reference_plot.load_product(product)
            except (OSError, ValueError) as error:
                self.reference_status.setText(f'Cached reference unavailable or invalid: {error}')
        self._explain()

    def _clear_diagnostic(self):
        self.current_diagnostic = None
        if self.residual_plot is not None:
            self.residual_plot.clear()
        _fill(self.residual_table, (), ())
        self.diagnostic_summary.setText('')
        self.diagnostic_panel.setVisible(False)

    def _display_diagnostic(self, diagnostic):
        self.current_diagnostic = diagnostic
        if self.residual_plot is None:
            self.residual_plot = ResidualPlot(self.diagnostic_views)
            self.diagnostic_views.insertTab(0, self.residual_plot, 'Aligned overlay & residuals')
            self.diagnostic_views.setCurrentIndex(0)
        self.residual_plot.load_diagnostic(diagnostic)
        columns = [
            f'Wavelength ({diagnostic.axis_unit})',
            f'Left ({diagnostic.signal_unit})',
            f'Right ({diagnostic.signal_unit})',
            f'Residual left - right ({diagnostic.signal_unit})',
        ]
        if diagnostic.whitened_residuals is not None:
            columns.append('Whitened residual')
            rows = list(zip(
                diagnostic.coordinates,
                diagnostic.left_values,
                diagnostic.right_values,
                diagnostic.residuals,
                diagnostic.whitened_residuals,
            ))
        else:
            rows = list(zip(
                diagnostic.coordinates,
                diagnostic.left_values,
                diagnostic.right_values,
                diagnostic.residuals,
            ))
        _fill(self.residual_table, columns, rows)
        quadratic_note = (
            f'; weighted quadratic r^T C^-1 r = {diagnostic.weighted_residual_quadratic:.6g} '
            '(fixed covariance, omits log-det normalization)'
            if diagnostic.weighted_residual_quadratic is not None else ''
        )
        self.diagnostic_summary.setText(
            f'Diagnostic {diagnostic.operation} ({diagnostic.residual_convention}, '
            f'{diagnostic.sample_count} samples, {diagnostic.signal_unit}): '
            f'RMS = {diagnostic.rms_residual:.6g}, mean = {diagnostic.mean_residual:.6g}, '
            f'max |r| = {diagnostic.max_abs_residual:.6g}{quadratic_note}. '
            'Numerical residual agreement only; not model adequacy, statistical significance, '
            'molecular identification, or atmospheric abundance.'
        )
        self.diagnostic_panel.setVisible(True)

    def evaluate_inputs(
        self,
        left_input,
        right_input,
        *,
        weighted=False,
        cross_dataset_independent=False,
        left_label='observation',
        right_label='reference',
    ):
        """Assess two ComparisonInput objects and render residuals only if eligible."""
        self.current_candidate_summary = None
        self._evaluated_candidate_records = []
        self._clear_diagnostic()
        left_eval = _eval_input(left_input)
        right_eval = _eval_input(right_input)
        self._active_record_context = {
            'left_item': left_input,
            'right_item': right_input,
            'left_provenance': None,
            'right_provenance': None,
            'weighted': weighted,
            'cross_dataset_independent': cross_dataset_independent,
            'limitations': (),
        }
        eligibility = assess(
            left_eval,
            right_eval,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
        )
        self.current_eligibility = eligibility
        self.compatibility.setToolTip('\n'.join((
            f'{eligibility.version} ({eligibility.operation}): {eligibility.status}',
            *eligibility.reasons,
        )))
        if eligibility.status != 'eligible':
            reasons = [
                f'Comparison blocked ({eligibility.version} / {eligibility.operation}: {eligibility.status}).'
            ]
            if eligibility.reasons:
                reasons.append(
                    'Unmet eligibility checks: '
                    + '; '.join(describe_reason(code, left_label, right_label) for code in eligibility.reasons)
                    + '.'
                )
            self.compatibility.setText('\n'.join(reasons))
            return None
        diagnostic = evaluate_residuals(
            left_eval,
            right_eval,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
        )
        self._display_diagnostic(diagnostic)
        self.compatibility.setText(
            f'Comparison eligible ({eligibility.version} / {eligibility.operation}: {eligibility.status}). '
            'Aligned overlay and left-minus-right residuals are displayed below. '
            'Numerical agreement does not establish molecular presence or abundance.'
        )
        return diagnostic

    def _candidate_summary_header(self, summary) -> str:
        if summary.eligible_indices:
            if summary.fair_ranking_permitted:
                closest_ids = ', '.join(
                    summary.candidates[i].source_id for i in summary.closest_candidate_indices
                )
                tie_note = (
                    ' (tied closest candidates; ambiguity preserved)'
                    if len(summary.closest_candidate_indices) > 1 else ''
                )
                ranking_text = f'Closest by {summary.ranking_metric}: {closest_ids}{tie_note}.'
            else:
                ranking_text = (
                    'Fair ranking blocked across eligible candidates: '
                    + ', '.join(summary.ranking_block_reasons) + '.'
                )
            return (
                f'Multi-candidate {summary.operation}: {len(summary.eligible_indices)} eligible, '
                f'{len(summary.blocked_indices)} blocked. {ranking_text} '
                + ' '.join(summary.limitations)
            )
        return (
            f'Multi-candidate {summary.operation}: 0 eligible, '
            f'{len(summary.blocked_indices)} blocked ({", ".join(summary.ranking_block_reasons)}). '
            'No overlay, residual, or candidate ranking is produced.'
        )

    def _render_candidate_selection(self, idx: int):
        summary = self.current_candidate_summary
        if summary is None or not (0 <= idx < len(summary.candidates)):
            return
        cand = summary.candidates[idx]
        self.current_eligibility = cand.eligibility
        rec_ctx = self._evaluated_candidate_records[idx]
        self._active_record_context = rec_ctx
        header = self._candidate_summary_header(summary)
        left_steps = _steps_summary(rec_ctx['left_item'])
        right_steps = _steps_summary(rec_ctx['right_item'])
        transform_parts = []
        if left_steps:
            transform_parts.append(f'observation transforms: {left_steps}')
        if right_steps:
            transform_parts.append(f'candidate transforms: {right_steps}')
        transform_note = f' [{" | ".join(transform_parts)}]' if transform_parts else ''

        if cand.eligibility.status == 'eligible' and cand.diagnostic is not None:
            self._display_diagnostic(cand.diagnostic)
            detail = (
                f'Inspecting candidate [{idx}] {cand.source_id}: eligible{transform_note}.'
            )
        else:
            self._clear_diagnostic()
            unmet = '; '.join(
                describe_reason(code, 'observation', f'candidate {cand.source_id}')
                for code in cand.eligibility.reasons
            )
            detail = (
                f'Inspecting candidate [{idx}] {cand.source_id}: '
                f'{cand.eligibility.status}{transform_note} — Unmet checks: {unmet}.'
            )
        self.compatibility.setText(f'{header}\n{detail}')
        self.compatibility.setToolTip('\n'.join((
            f'{summary.version} ({summary.operation})',
            *(
                f'[{c.candidate_index}] {c.source_id}: {c.eligibility.status}'
                + (f' ({", ".join(c.eligibility.reasons)})' if c.eligibility.reasons else '')
                for c in summary.candidates
            ),
        )))

    def _on_candidate_selector_changed(self, idx: int):
        if self.current_candidate_summary is None:
            return
        self._render_candidate_selection(idx)

    def _evaluate_and_display_candidates(
        self,
        *,
        left_item: ComparisonInput | TransformedInput,
        right_items: list[ComparisonInput | TransformedInput],
        left_provenance: dict | None,
        right_provenances: list[dict | None],
        candidate_labels: list[str],
        weighted: bool,
        cross_dataset_independent: bool,
        limitations: tuple[str, ...],
    ):
        self._clear_diagnostic()
        left_eval = _eval_input(left_item)
        right_evals = [_eval_input(item) for item in right_items]
        summary = evaluate_candidates(
            left_eval,
            right_evals,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
        )
        self.current_candidate_summary = summary
        self._evaluated_candidate_records = [
            {
                'left_item': left_item,
                'right_item': r_item,
                'left_provenance': left_provenance,
                'right_provenance': r_prov,
                'weighted': weighted,
                'cross_dataset_independent': cross_dataset_independent,
                'limitations': limitations,
            }
            for r_item, r_prov in zip(right_items, right_provenances)
        ]
        if summary.eligible_indices:
            display_idx = (
                summary.ordered_eligible_indices[0]
                if summary.ordered_eligible_indices
                else summary.eligible_indices[0]
            )
        else:
            display_idx = 0

        self.candidate_selector.blockSignals(True)
        try:
            self.candidate_selector.clear()
            for idx, (cand, label) in enumerate(zip(summary.candidates, candidate_labels)):
                self.candidate_selector.addItem(
                    f'[{idx}] {label} ({cand.eligibility.status})', idx
                )
            self.candidate_selector.setCurrentIndex(display_idx)
        finally:
            self.candidate_selector.blockSignals(False)

        self._render_candidate_selection(display_idx)
        return summary

    def evaluate_candidate_inputs(
        self,
        target_input,
        candidate_inputs,
        *,
        weighted=False,
        cross_dataset_independent=False,
    ):
        """Evaluate multiple candidates against one target with fair-ranking guards."""
        items = list(candidate_inputs)
        labels = [_eval_input(item).source_id for item in items]
        return self._evaluate_and_display_candidates(
            left_item=target_input,
            right_items=items,
            left_provenance=None,
            right_provenances=[None for _ in items],
            candidate_labels=labels,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
            limitations=(),
        )

    def save_active_comparison(self):
        if self.project_store is None:
            self.persistence_status.setText('Project persistence is unavailable in this view.')
            return None
        project_name = self._active_project_name()
        if not project_name:
            self.persistence_status.setText('Select or create an active project in Projects first.')
            return None
        if self._active_record_context is None:
            self.persistence_status.setText(
                'Evaluate candidates or select both an observation and reference before saving.'
            )
            return None
        ctx = self._active_record_context
        try:
            record = build_comparison_record(
                ctx['left_item'],
                ctx['right_item'],
                weighted=ctx['weighted'],
                cross_dataset_independent=ctx['cross_dataset_independent'],
                left_provenance=ctx['left_provenance'],
                right_provenance=ctx['right_provenance'],
                limitations=ctx['limitations'],
            )
            saved_path = self.project_store.save_comparison(project_name, record)
        except (project_persistence.PersistenceError, ValueError, TypeError) as error:
            self.persistence_status.setText(f'Could not save comparison record: {error}')
            return None
        self.refresh_saved_comparisons(selected_path=str(saved_path))
        self.persistence_status.setText(
            f'Saved comparison {saved_path.name} to project {project_name} '
            f'(status: {record["eligibility"]["status"]}, '
            f'integrity SHA-256: {record["integrity_sha256"][:16]}…).'
        )
        self.persistence_status.setToolTip(
            '\n'.join((
                f'File: {saved_path}',
                f'Integrity SHA-256: {record["integrity_sha256"]}',
                *record['reproducibility_limitations'],
            ))
        )
        return saved_path

    def refresh_saved_comparisons(self, *_args, selected_path: str | None = None):
        if self.project_store is None:
            self.persistence_status.setText('Project persistence is unavailable in this view.')
            return []
        project_name = self._active_project_name()
        if not project_name:
            self.persistence_status.setText('Select or create an active project in Projects first.')
            return []
        previous = selected_path or self.saved_comparisons_selector.currentData()
        self.saved_comparisons_selector.blockSignals(True)
        self.saved_comparisons_selector.clear()
        try:
            records, invalid = self.project_store.comparisons(project_name)
            for path, rec in records:
                elig = rec['eligibility']
                right_id = rec['right']['evaluated_input']['source_id']
                self.saved_comparisons_selector.addItem(
                    f'{path.stem[:12]} | {elig["operation"]}: {elig["status"]} | {right_id}',
                    str(path),
                )
            idx = self.saved_comparisons_selector.findData(previous) if previous else -1
            if idx >= 0:
                self.saved_comparisons_selector.setCurrentIndex(idx)
            elif records:
                self.saved_comparisons_selector.setCurrentIndex(0)
            self.persistence_status.setText(
                f'Project {project_name}: {len(records)} verified comparison records; '
                f'{invalid} invalid/corrupted files excluded.'
            )
            return records
        except project_persistence.PersistenceError as error:
            self.persistence_status.setText(f'Could not load project comparisons: {error}')
            return []
        finally:
            self.saved_comparisons_selector.blockSignals(False)

    def reproduce_selected_comparison(self):
        path = self.saved_comparisons_selector.currentData()
        if not path:
            self.persistence_status.setText('Refresh and select a saved comparison record first.')
            return None
        try:
            record = load_comparison_record(path)
            check = reproduce_comparison_record(record)
        except (OSError, ValueError, KeyError, TypeError) as error:
            self._clear_diagnostic()
            self.current_eligibility = None
            self.persistence_status.setText(f'Saved comparison verification failed: {error}')
            self.persistence_status.setToolTip('')
            return None

        self.current_candidate_summary = None
        self.current_eligibility = check.recomputed_eligibility
        if check.recomputed_diagnostic is not None:
            self._display_diagnostic(check.recomputed_diagnostic)
        else:
            self._clear_diagnostic()

        verdict_flag = 'matched' if check.matches_saved_verdict else 'MISMATCH'
        diag_flag = 'matched' if check.matches_saved_diagnostics else 'MISMATCH'
        discrepancy_text = (
            f' Discrepancies: {"; ".join(check.discrepancies)}.'
            if check.discrepancies else ''
        )
        self.persistence_status.setText(
            f'Verified & reproduced {record["right"]["evaluated_input"]["source_id"]}: '
            f'verdict {verdict_flag}, diagnostics {diag_flag}.{discrepancy_text} '
            'Re-evaluated from signed record arrays; raw source files were not re-ingested.'
        )
        self.persistence_status.setToolTip('\n'.join((
            f'Method: {record["method_version"]}',
            f'Integrity SHA-256: {record["integrity_sha256"]}',
            *check.discrepancies,
            *check.limitations,
        )))
        elig = check.recomputed_eligibility
        if elig.status == 'eligible':
            self.compatibility.setText(
                f'Reopened saved comparison ({elig.version} / {elig.operation}: {elig.status}). '
                'Recomputed overlay and left-minus-right residuals are displayed below. '
                'Numerical agreement does not establish molecular presence or abundance.'
            )
        else:
            unmet = '; '.join(describe_reason(c, 'left', 'right') for c in elig.reasons)
            self.compatibility.setText(
                f'Reopened saved comparison ({elig.version} / {elig.operation}: {elig.status}). '
                f'Unmet eligibility checks: {unmet}.'
            )
        return check

    def _explain(self):
        self.current_eligibility = None
        self.current_candidate_summary = None
        self._evaluated_candidate_records = []
        self._active_record_context = None
        if self.candidate_entries:
            self._sync_staged_candidate_selector()
        self._clear_diagnostic()
        if self.current_observation is None or self.current_reference is None:
            self.compatibility.setText('Select an observation and a valid cached reference for inspection. '
                                       'Comparison operations remain unavailable.')
            self.compatibility.setToolTip('')
            return
        spectrum = self.current_observation
        left = observation_input(spectrum, self.current_observation_hash)
        right = reference_input(self.current_reference)
        self._active_record_context = {
            'left_item': left.comparison_input,
            'right_item': right.comparison_input,
            'left_provenance': {
                'kind': 'imported_observation_snapshot',
                'source_file': str(spectrum.source_file),
                'source_sha256': self.current_observation_hash,
            },
            'right_provenance': {
                'kind': 'cached_exomol_reference',
                'source_url': self.current_reference.product.provenance.source_url,
                'source_sha256': self.current_reference.product.source_sha256,
            },
            'weighted': False,
            'cross_dataset_independent': False,
            'limitations': (),
        }
        eligibility = assess(left.comparison_input, right.comparison_input)
        self.current_eligibility = eligibility
        reasons = [
            f'Comparison blocked ({eligibility.version} / {eligibility.operation}: {eligibility.status}): '
            'this reference is a calculated absorption cross section in cm^2/molecule '
            'on wavenumber cm^-1, not a predicted transit-depth spectrum. '
            'Cross sections and transit depth cannot be compared directly without a physical model.'
        ]
        if not spectrum.signal_type or not spectrum.signal_unit or not spectrum.axis_unit:
            reasons.append('Observation observable or units are unknown; no meaning or conversion is inferred.')
        if eligibility.reasons:
            reasons.append('Unmet eligibility checks: ' +
                           '; '.join(describe_reason(code, 'observation', 'reference') for code in eligibility.reasons) + '.')
        reasons.append('A physical model with documented conditions, compatible observables/units, '
                       'coordinate frame, grid alignment and instrument response evidence is required '
                       'before overlay or residual analysis. Uncertainty/noise evidence is required for '
                       'weighted diagnostics. Load a validated forward-model curve in the candidate tools '
                       'above to evaluate eligible transit-depth predictions.')
        self.compatibility.setText('\n'.join(reasons))
        self.compatibility.setToolTip('\n'.join((
            f'{eligibility.version} ({eligibility.operation}): {eligibility.status}',
            *eligibility.reasons,
        )))
