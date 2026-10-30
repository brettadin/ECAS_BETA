"""Real-library integration, identity preservation and honest blocked results.

Self-fits are round-trip engineering checks, not empirical identification proof.
No invented spectra or detection-success demonstrations are used here.
"""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication

from ecas.identification.library import load_reference
from ecas.identification_records import load_record, save_record, reproduce_record
from ecas.ingestion.import_manager import import_spectrum
from ecas.ingestion.nasa_table import import_transmission_table
from ecas.observations import observation_context, project_observation, independent_observations
from ecas.projects import ProjectStore
from ecas.ui.identification_panel import IdentificationPanel, molecule_color
from ecas.ui.main_window import ECASWindow

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / 'data/ECAS_Spectral_Library/Ready_For_ECAS'
IR = LIBRARY / 'IR/CO2/CO2_gas_IR_index0.jdx'
NASA = ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl'


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def panel(app):
    reference = load_reference(IR)
    widget = IdentificationPanel(lambda: (reference.spectrum, reference.source_sha256))
    yield widget
    widget.shutdown()
    widget.close()
    widget.deleteLater()
    app.processEvents()


def test_real_catalog_selection_colors_blocking_and_saved_reproduction(panel, tmp_path):
    assert len(panel.catalog.datasets) == 40
    assert len(panel.molecule_checks) == 28
    molecules = {r.molecule for r in panel.catalog.datasets}
    assert len({molecule_color(molecule) for molecule in molecules}) == len(molecules)
    panel.add_current_input()
    for key in [('IR', 'CO2'), ('IR', 'H2O'), ('UV-Vis', 'CH4')]:
        panel.molecule_checks[key].setChecked(True)
    panel.run_identification(synchronous=True)
    assert panel.results_table.rowCount() == 3
    result = panel.batch_results[0][1]
    evaluated = [c for c in result.components if c.status == 'evaluated']
    blocked = [c for c in result.components if c.status == 'blocked']
    assert evaluated and blocked
    assert all(c.sigma is None for c in blocked)
    by_molecule = {panel.results_table.item(i, 1).text(): i for i in range(3)}
    assert panel.results_table.item(by_molecule['CH4'], 4).text() == 'N/A'
    assert panel.results_table.item(by_molecule['CO2'], 3).text() == molecule_color('CO2')
    record = panel.analysis_record()
    path = tmp_path / 'analysis.json'
    save_record(path, record)
    restored = reproduce_record(load_record(path))
    assert restored[0].model == pytest.approx(result.model)
    damaged = deepcopy(record)
    damaged['payload']['observations'][0]['spectrum']['rows'][0]['signal'] += 1
    with pytest.raises(ValueError, match='integrity'):
        reproduce_record(damaged)
    panel.threshold.setValue(4.)
    assert not panel.batch_results and not panel.export_button.isEnabled()


def test_real_source_import_metadata_project_roundtrip_and_window_entry(app, tmp_path):
    window = ECASWindow(projects_dir=tmp_path / 'projects', reference_cache_dir=tmp_path / 'cache')
    try:
        window._import_csv_from_path(str(IR))
        spectrum = window.current_spectrum
        assert spectrum.signal_type == 'Laboratory Absorbance'
        assert dict(spectrum.metadata)['modality'] == 'IR'
        window.project_store.create('laboratory')
        identifier = window.project_store.attach('laboratory', spectrum)
        record = window.project_store.spectra('laboratory')[0]
        assert record.spectrum == spectrum and record.record_id == identifier
        context = project_observation('laboratory', record)
        assert context.observation_id == f'project:laboratory:{identifier}'
        window.project_browser.refresh('laboratory')
        window._open_project_spectrum(record)
        window.project_store.create('other')
        window.project_browser.refresh('other')
        assert window._comparison_metadata()['project_id'] == 'laboratory'
        panel = window.comparison_browser.open_identification()
        panel.add_current_input()
        assert panel.contexts[0].source_sha256 == record.attachment['source_sha256']
        assert panel.contexts[0].metadata['modality'] == 'IR'
    finally:
        window.close()


def test_real_signed_uv_import_and_project_metadata(app, tmp_path):
    source = next((LIBRARY / 'Uv-Vis/O2').glob('*650*'))
    spectrum = import_spectrum(source)
    original = tuple(row['signal'] for row in spectrum.rows)
    assert min(original) < 0
    store = ProjectStore(tmp_path / 'projects')
    store.create('uv')
    store.attach('uv', spectrum)
    reopened = store.spectra('uv')[0].spectrum
    assert reopened == spectrum
    assert tuple(row['signal'] for row in reopened.rows) == original
    assert dict(reopened.metadata)['modality'] == 'UV-Vis'


def test_planetary_project_batch_preserves_ids_and_duplicate_source_is_not_independent(panel, tmp_path):
    store = ProjectStore(tmp_path / 'projects')
    store.create('wasp39')
    spectrum = import_transmission_table(NASA).spectrum
    store.attach('wasp39', spectrum)
    store.attach('wasp39', spectrum)
    contexts = [project_observation('wasp39', record) for record in store.spectra('wasp39')]
    assert contexts[0].observation_id != contexts[1].observation_id
    assert contexts[0].planet == contexts[1].planet == 'WASP-39 b'
    assert contexts[0].metadata['source_table_metadata']['INSTRUMENT']
    unique, duplicates = independent_observations(contexts)
    assert len(unique) == len(duplicates) == 1
    panel.project_store = store
    panel.active_project_getter = lambda: 'wasp39'
    panel.add_project_observations()
    panel.molecule_checks[('IR', 'CO2')].setChecked(True)
    panel.run_identification(synchronous=True)
    assert len(panel.batch_results) == 1 and panel.results_table.rowCount() == 2
    assert panel.batch_results[0][1].components[0].sigma is None
    assert 'radiative' in panel.results_table.item(0, 5).text()
    assert 'Duplicate' in panel.results_table.item(1, 5).text()
    panel.planet_selector.setCurrentIndex(1)
    assert not panel.batch_results and not panel.export_button.isEnabled()


def test_worker_runs_real_fit_without_gui_thread_mutation(panel, app):
    panel.add_current_input()
    panel.molecule_checks[('IR', 'CO2')].setChecked(True)
    panel.run_identification()
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    panel._worker.finished.connect(loop.quit)
    timer.start(15000)
    loop.exec()
    timer.stop()
    app.processEvents()
    assert not panel._worker.isRunning()
    assert panel.batch_results and panel.identify_button.isEnabled()


def test_unhashed_changed_source_keeps_distinct_snapshot_identity():
    spectrum = load_reference(IR).spectrum
    rows = deepcopy(spectrum.rows)
    rows[0]['signal'] += 1  # Deliberate integrity-failure fixture, not a measured spectrum.
    changed = replace(spectrum, rows=rows)
    first, second = observation_context(spectrum), observation_context(changed)
    assert first.observation_id != second.observation_id
    assert first.source_sha256 is second.source_sha256 is None
