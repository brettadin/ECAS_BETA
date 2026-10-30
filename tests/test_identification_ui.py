"""Real-library integration, identity preservation and honest blocked results.

Self-fits are round-trip engineering checks, not empirical identification proof.
No invented spectra or detection-success demonstrations are used here.
"""
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QTimer, Qt
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


def test_blocked_transit_retains_measured_plot_and_actionable_reason(panel):
    panel.add_files([NASA])
    assert len(panel.plot.listDataItems()) == 1
    assert not panel.atmospheric_button.isHidden()
    panel.molecule_checks[('IR', 'CO2')].setChecked(True)
    panel.molecule_checks[('UV-Vis', 'CO2')].setChecked(True)
    panel.run_identification(synchronous=True)
    spectrum = panel.contexts[0].spectrum
    curve, = panel.plot.listDataItems()
    x, y = curve.getData()
    assert x == pytest.approx([r['wavelength'] for r in spectrum.rows])
    assert y == pytest.approx([r['signal'] for r in spectrum.rows])
    assert 'No compatible fit' in panel.status.text()
    assert 'radiative-transfer' in panel.plot_status.text()
    assert 'planetary transit depth' in panel.plot_status.text()
    assert panel.plot.getAxis('bottom').labelUnits == 'microns'
    assert panel.plot.getAxis('left').labelUnits == '%'
    assert all(panel.results_table.item(i, 4).text() == 'N/A' for i in range(2))


def test_reference_preview_preserves_source_values_and_separates_quantities(panel):
    for key in [('IR', 'CO2'), ('IR', 'CH4'), ('UV-Vis', 'O2')]:
        panel.molecule_checks[key].setChecked(True)
    absorbance = next(r for r in panel.catalog.datasets if r.molecule == 'CO2'
                      and r.spectrum.signal_type == 'Laboratory Absorbance')
    co2_selector = panel.dataset_selectors[('IR', 'CO2')]
    co2_selector.setCurrentIndex(co2_selector.findData(absorbance.dataset_id))
    transmittance = next(r for r in panel.catalog.datasets if r.molecule == 'CH4'
                        and r.spectrum.signal_type == 'Laboratory Transmittance')
    ch4_selector = panel.dataset_selectors[('IR', 'CH4')]
    ch4_selector.setCurrentIndex(ch4_selector.findData(transmittance.dataset_id))
    selector = panel.dataset_selectors[('UV-Vis', 'O2')]
    selector.setCurrentIndex(next(i for i in range(selector.count()) if '650' in selector.itemText(i)))
    panel.reference_toggle.click()
    assert panel.reference_plots.count() == 3  # IR absorbance, IR T, UV cross section
    refs = {r.molecule: r for r in panel.selected_references()}
    for index in range(panel.reference_plots.count()):
        plot = panel.reference_plots.widget(index)
        for curve in plot.listDataItems():
            reference = refs[curve.name()]
            expected = sorted((r['wavelength'], r['signal']) for r in reference.spectrum.rows)
            x, y = curve.getData()
            assert x == pytest.approx([r[0] for r in expected])
            assert y == pytest.approx([r[1] for r in expected])
            assert plot.getAxis('left').labelUnits == reference.spectrum.signal_unit
            if reference.molecule == 'O2':
                assert min(y) < 0
    assert not panel.batch_results  # Preview is never represented as a fit.


def test_two_real_nontransit_inputs_run_and_plot_independently(panel, app, tmp_path):
    uv = next((LIBRARY / 'Uv-Vis/C2H2').glob('*.csv'))
    panel.add_files([IR, uv, tmp_path / 'missing.fits'])
    assert len(panel.contexts) == 2
    assert '1 import failure' in panel.status.text()
    assert '2 checked observation' in panel.selection_status.text()
    panel.molecule_checks[('IR', 'CO2')].setChecked(True)
    panel.molecule_checks[('UV-Vis', 'C2H2')].setChecked(True)
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
    assert len(panel.batch_results) == 2
    assert panel.results_table.rowCount() == 4
    assert '2 input(s) processed separately' in panel.status.text()
    for index, (context, result) in enumerate(panel.batch_results):
        panel.result_selector.setCurrentIndex(index)
        assert any(c.status == 'evaluated' for c in result.components)
        assert len(panel.plot.listDataItems()) == 3
        plotted = panel.plot.listDataItems()[0]
        assert plotted.getData()[0] == pytest.approx(result.x)
        assert plotted.getData()[1] == pytest.approx(result.observed)
        assert context.label in panel.plot_status.text()
    # Changing the checked set invalidates scores but retains a measured preview.
    panel.observations.item(1).setCheckState(Qt.CheckState.Unchecked)
    assert not panel.batch_results and len(panel.plot.listDataItems()) == 1
    assert '1 checked observation' in panel.selection_status.text()


def test_atmospheric_handoff_preserves_multiple_snapshots_and_real_mode(app, tmp_path):
    window = ECASWindow(projects_dir=tmp_path / 'projects', reference_cache_dir=tmp_path / 'cache')
    try:
        panel = window.comparison_browser.open_identification()
        # Two independent record identities, even when a project attaches the same raw product.
        spectrum = import_transmission_table(NASA).spectrum
        for record_id in ('first', 'second'):
            panel._add_context(observation_context(spectrum, metadata={
                'project_id': 'wasp39', 'project_record_id': record_id,
                'pl_name': 'WASP-39 b', 'instrument': 'NIRISS', 'reference': 'Feinstein et al. 2023'}))
        browser = window.comparison_browser
        browser.gen_source_selector.setCurrentIndex(browser.gen_source_selector.findData('templates_only'))
        panel.atmospheric_button.click()
        assert browser.observation_selector.count() == 2
        assert browser.gen_source_selector.currentData() == 'cached_only'
        assert browser.current_observation == spectrum
        assert browser.current_observation_metadata['project_record_id'] == 'first'
        assert browser._observation_metadata_list[1]['project_record_id'] == 'second'
        assert not browser.candidate_entries  # No model or fabricated score was auto-generated.
        assert not browser.workflow_panel.isHidden()
        assert 'Run each observation separately' in browser.candidate_status.text()
        browser.open_identification()
        panel.atmospheric_button.click()
        assert browser.observation_selector.count() == 2  # Reopening does not duplicate inputs.
    finally:
        window.close()
