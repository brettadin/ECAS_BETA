"""Offline input selection and scientific boundary regressions using real widgets."""
import gc
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from ecas.ui.main_window import ECASWindow
from ecas.ui import molecular_browser
from ecas.ingestion.exomol_product import ProductRequest, validate_product
from ecas.ingestion.exomol_product_network import RetrievedCrossSection
from ecas.ingestion.exomol_reference_cache import store_reference

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='session', autouse=True)
def app():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def window(tmp_path, app):
    widget = ECASWindow(projects_dir=tmp_path / 'projects', reference_cache_dir=tmp_path / 'cache')
    yield widget
    widget.close()
    gc.collect()


def cache_reference(window, *, distinct=False):
    request = ProductRequest(4000, 4010, 500, '1')
    raw = (ROOT / 'data/ExoMol/2026-10-28/CO2-12C-16O2-500K-4000-4010-dnu1.sigma').read_bytes()
    if distinct:
        raw += b'\n'  # Distinct source bytes, same numeric values: must remain distinct.
    result = RetrievedCrossSection(request, raw, validate_product(raw, request))
    path = store_reference(window.reference_browser.cache_root / 'references', result)
    return path, result


def import_csv(window, tmp_path, name, signal):
    source = tmp_path / name
    source.write_text(f'wavelength,signal\n1,{signal}\n2,3\n', encoding='utf-8')
    window._import_csv_from_path(str(source))
    return window.current_spectrum


def test_independent_selection_preserves_original_values_and_main_display(window, tmp_path):
    browser = window.comparison_browser
    first = import_csv(window, tmp_path, 'first.csv', 2)
    browser.add_current_observation()
    second = import_csv(window, tmp_path, 'second.csv', 9)
    browser.add_current_observation()
    browser.observation_selector.setCurrentIndex(0)
    path, result = cache_reference(window)
    with patch.object(molecular_browser, 'PublicExomolCatalogueHttp') as catalogue, \
         patch.object(molecular_browser, 'PublicExomolProductHttp') as product:
        browser.refresh_references()
        assert browser.reference_selector.currentIndex() == -1  # explicit choice
        browser.reference_selector.setCurrentIndex(0)
        for page in (4, 3, 2, 4):
            window.navigation.setCurrentRow(page)
        catalogue.assert_not_called()
        product.assert_not_called()
    assert browser.current_observation == first and browser.current_observation is not first
    assert browser.current_reference == result
    assert browser.observation_table.item(0, 1).text() == '2.0'
    assert browser.reference_table.item(0, 0).text() == '4000.0'
    assert window.current_spectrum is second
    assert window.spectra_plot._current_spectrum is second
    assert window.reference_browser.current_reference is None
    assert 'Comparison blocked' in browser.compatibility.text()
    assert 'units are unknown' in browser.compatibility.text()
    assert 'physical model' in browser.compatibility.text()
    assert result.raw == (ROOT / 'data/ExoMol/2026-10-28/CO2-12C-16O2-500K-4000-4010-dnu1.sigma').read_bytes()


def test_snapshot_survives_source_removal_failed_import_and_no_current_input(window, tmp_path):
    browser = window.comparison_browser
    original = import_csv(window, tmp_path, 'original.csv', 2)
    browser.add_current_observation()
    original.source_file.unlink()
    with patch('ecas.ui.main_window.QMessageBox.warning'):
        window._import_csv_from_path(str(tmp_path / 'absent.csv'))
    browser.add_current_observation()
    assert browser.observation_selector.count() == 1
    assert browser.current_observation == original
    assert browser.observation_table.rowCount() == 2
    assert 'Previous selection retained' in browser.observation_status.text()


@pytest.mark.parametrize('damage', ['corrupt', 'delete'])
def test_invalidated_cache_clears_reference_and_prevents_stale_inspection(window, damage):
    browser = window.comparison_browser
    path, result = cache_reference(window)
    browser.refresh_references()
    browser.reference_selector.setCurrentIndex(0)
    assert browser.current_reference == result
    if damage == 'corrupt':
        path.write_text('{}', encoding='utf-8')
    else:
        path.unlink()
    browser._select_reference()  # re-read at use, not just at discovery
    assert browser.current_reference is None
    assert browser.reference_table.rowCount() == 0
    assert browser.reference_plot.current_product is None
    assert browser.reference_plot.curve.getData()[0] is None
    assert 'unavailable or invalid' in browser.reference_status.text()
    browser.refresh_references()
    assert browser.reference_selector.count() == 0
    assert ('1 invalid' if damage == 'corrupt' else '0 invalid') in browser.cache_status.text()
    assert browser.reference_status.toolTip() == ''


def test_refresh_preserves_independent_choices_and_reports_empty_cache(window, tmp_path):
    browser = window.comparison_browser
    browser.refresh_references()
    assert '0 cached references' in browser.cache_status.text()
    import_csv(window, tmp_path, 'generic.csv', 2)
    browser.add_current_observation()
    observation = browser.current_observation
    first, _ = cache_reference(window)
    browser.refresh_references()
    browser.reference_selector.setCurrentIndex(0)
    second, _ = cache_reference(window, distinct=True)
    browser.refresh_references()
    assert browser.reference_selector.count() == 2
    assert browser.reference_selector.currentData() == str(first)
    assert browser.current_observation is observation
    labels = [browser.reference_selector.itemText(i) for i in range(2)]
    assert len(set(labels)) == 2


def test_transmission_metadata_and_hash_are_preserved_without_claiming_eligibility(window):
    source = ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl'
    before = source.read_bytes()
    window._import_csv_from_path(str(source))
    browser = window.comparison_browser
    browser.add_current_observation()
    source_hash = window.current_spectrum_details.source_sha256
    assert source_hash in browser.observation_status.toolTip()
    assert source_hash[:32] + '\n' + source_hash[32:] in browser.observation_status.text()
    assert 'Transmission' in browser.observation_status.text()
    assert browser.current_eligibility is None
    cache_reference(window)
    browser.refresh_references()
    browser.reference_selector.setCurrentIndex(0)
    assert browser.current_eligibility is not None
    assert browser.current_eligibility.version == 'ecas-comparison-eligibility-v1'
    assert browser.current_eligibility.operation == 'aligned_residual_v1'
    assert browser.current_eligibility.status == 'incompatible'
    assert 'right.role.requires_physical_model_or_supported_role' in browser.current_eligibility.reasons
    assert 'ecas-comparison-eligibility-v1 / aligned_residual_v1: incompatible' in browser.compatibility.text()
    assert 'cannot be compared directly without a physical model' in browser.compatibility.text()
    assert 'explicit physical model is needed first' in browser.compatibility.text()
    assert 'instrument response evidence' in browser.compatibility.text()
    assert 'right.role.requires_physical_model_or_supported_role' in browser.compatibility.toolTip()
    assert browser.current_observation.rows == window.current_spectrum.rows
    assert source.read_bytes() == before
    browser.reference_selector.setCurrentIndex(-1)
    assert browser.current_eligibility is None
    assert browser.compatibility.toolTip() == ''


def test_comparison_label_uses_table_facts_and_retains_session_identity(window, tmp_path):
    window._import_csv_from_path(str(ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl'))
    browser = window.comparison_browser
    browser.add_current_observation()
    label = browser.observation_selector.itemText(0)
    metadata = dict(window.current_spectrum_details.metadata)
    assert metadata['REFERENCE'] in label
    assert label.startswith('1: ')
    original = browser.current_observation
    import_csv(window, tmp_path, 'generic.csv', 5)
    browser.add_current_observation()
    assert browser.observation_selector.itemText(0) == label
    assert 'generic.csv' in browser.observation_selector.itemText(1)
    browser.observation_selector.setCurrentIndex(0)
    assert browser.current_observation is original


def test_separate_native_plots_preserve_original_values_and_navigation(window, tmp_path):
    observation = import_csv(window, tmp_path, 'unknown-units.csv', 2)
    browser = window.comparison_browser
    browser.add_current_observation()
    _, reference = cache_reference(window)
    browser.refresh_references()
    browser.reference_selector.setCurrentIndex(0)
    x, y = browser.reference_plot.curve.getData()
    assert list(zip(x, y)) == list(reference.product.points)
    assert browser.observation_plot._current_spectrum == observation
    assert browser.observation_plot._axis_unit_label is None
    assert browser.observation_plot._signal_unit_label is None
    assert browser.reference_plot.plot_widget.getAxis('bottom').labelText == 'Wavenumber (cm^-1)'
    axis = browser.reference_plot.plot_widget.getAxis('left')
    assert axis.labelText == 'σ (cm²/molecule)'
    assert not axis.autoSIPrefix
    assert 'e-' in axis.tickStrings([1e-24], 1, 1e-24)[0]
    browser.observation_views.setCurrentIndex(1)
    browser.reference_views.setCurrentIndex(1)
    for page in (0, 2, 3, 4):
        window.navigation.setCurrentRow(page)
    assert browser.observation_views.currentIndex() == browser.reference_views.currentIndex() == 1
    assert browser.current_observation == observation
    assert browser.current_reference == reference
    assert window.reference_browser.current_reference is None
    assert 'Comparison blocked' in browser.compatibility.text()
    assert browser.diagnostic_panel.isHidden()


def test_eligible_inputs_render_overlay_and_residuals_and_clear_on_blocked_selection(window, tmp_path):
    from dataclasses import replace
    from ecas.comparison.eligibility import ComparisonInput

    browser = window.comparison_browser
    assert browser.diagnostic_panel.isHidden()
    assert browser.residual_plot is None

    left = ComparisonInput(
        source_id='synthetic-obs',
        source_sha256='a' * 64,
        role='observation',
        observable='transit_depth',
        axis_unit='microns',
        signal_unit='percent',
        coordinate_frame='synthetic-frame',
        response_id='synthetic-response-v1',
        response_evidence='synthetic declaration',
        coordinates=(1.0, 2.0, 3.0),
        values=(2.0, 2.3, 1.9),
        noise_kind='independent_gaussian_1sigma',
        noise_evidence='synthetic 1-sigma',
        sigma=(0.1, 0.1, 0.1),
    )
    right = replace(
        left,
        source_id='synthetic-model',
        source_sha256='b' * 64,
        role='forward_model',
        values=(2.0, 2.1, 2.0),
        noise_kind='deterministic_model',
        noise_evidence='synthetic deterministic',
        sigma=None,
    )

    diag = browser.evaluate_inputs(
        left, right, weighted=True, cross_dataset_independent=True
    )
    assert diag is not None
    assert not browser.diagnostic_panel.isHidden()
    assert browser.residual_plot is not None
    assert not browser.residual_plot.overlay_widget.getAxis('left').autoSIPrefix
    assert not browser.residual_plot.residual_widget.getAxis('left').autoSIPrefix
    rx, ry = browser.residual_plot.residual_curve.getData()
    assert list(rx) == [1.0, 2.0, 3.0]
    assert pytest.approx(list(ry), abs=1e-12) == [0.0, 0.2, -0.1]
    assert browser.residual_table.rowCount() == 3
    assert browser.residual_table.columnCount() == 5  # includes Whitened residual
    assert 'weighted quadratic' in browser.diagnostic_summary.text()
    assert 'not establish molecular presence or abundance' in browser.compatibility.text()

    # Selecting an incompatible raw reference must immediately clear stale residuals
    import_csv(window, tmp_path, 'obs.csv', 2)
    browser.add_current_observation()
    cache_reference(window)
    browser.refresh_references()
    browser.reference_selector.setCurrentIndex(0)
    assert browser.current_diagnostic is None
    assert browser.diagnostic_panel.isHidden()
    assert browser.residual_table.rowCount() == 0
    assert browser.residual_plot.residual_curve.getData()[0] is None


def test_multi_candidate_ui_evaluation_preserves_ties_and_covariance_guards(window):
    from dataclasses import replace
    from ecas.comparison.eligibility import ComparisonInput

    browser = window.comparison_browser
    target = ComparisonInput(
        source_id='synthetic-obs',
        source_sha256='a' * 64,
        role='observation',
        observable='transit_depth',
        axis_unit='microns',
        signal_unit='percent',
        coordinate_frame='synthetic-frame',
        response_id='synthetic-response-v1',
        response_evidence='synthetic declaration',
        coordinates=(1.0, 2.0, 3.0),
        values=(2.0, 2.2, 2.0),
        noise_kind='independent_gaussian_1sigma',
        noise_evidence='synthetic 1-sigma',
        sigma=(0.1, 0.1, 0.1),
    )
    cand_a = replace(
        target,
        source_id='cand-alpha',
        source_sha256='b' * 64,
        role='forward_model',
        values=(2.0, 2.3, 2.0),
        noise_kind='deterministic_model',
        noise_evidence='synthetic deterministic',
        sigma=None,
    )
    cand_b = replace(cand_a, source_id='cand-beta', source_sha256='c' * 64, values=(2.0, 2.1, 2.0))

    summary = browser.evaluate_candidate_inputs(target, (cand_a, cand_b))
    assert summary.closest_candidate_indices == (0, 1)
    assert 'cand-alpha, cand-beta' in browser.compatibility.text()
    assert 'tied closest candidates; ambiguity preserved' in browser.compatibility.text()
    assert not browser.diagnostic_panel.isHidden()

    noisy_b = replace(
        cand_b,
        role='reference_measurement',
        noise_kind='independent_gaussian_1sigma',
        noise_evidence='synthetic noisy reference',
        sigma=(0.5, 0.5, 0.5),
    )
    unfair = browser.evaluate_candidate_inputs(
        target, (cand_a, noisy_b), weighted=True, cross_dataset_independent=True
    )
    assert unfair.fair_ranking_permitted is False
    assert 'Fair ranking blocked across eligible candidates' in browser.compatibility.text()


def _write_forward_model_json(path: Path, *, source_id: str, axis_unit: str, signal_unit: str, coordinates: list[float], values: list[float]) -> Path:
    import json
    from ecas.comparison.forward_model import MODEL_FILE_SCHEMA

    payload = {
        'schema': MODEL_FILE_SCHEMA,
        'source_id': source_id,
        'axis_unit': axis_unit,
        'signal_unit': signal_unit,
        'coordinate_frame': 'barycentric',
        'response_id': 'nirspec-prism-v1',
        'response_evidence': 'JWST synthetic top-hat bin response',
        'coordinates': coordinates,
        'values': values,
        'provenance': {
            'engine_name': 'synthetic-rt-solver',
            'engine_version': '0.1.0-test',
            'temperature_pressure_profile': 'isothermal 1100 K',
            'abundance_convention': 'volume_mixing_ratio',
            'species_parameters': [['CO2', 1e-4], ['H2O', 1e-3]],
            'opacity_sources': [
                {
                    'formula': 'CO2',
                    'isotopologue': '12C-16O2',
                    'dataset': 'UCL-4000',
                    'version': '20200601',
                    'source_sha256': 'c' * 64,
                }
            ],
            'gravity_m_s2': 4.26,
            'reference_pressure_bar': 0.01,
            'planet_radius_m': 9.1e7,
            'stellar_radius_m': 6.26e8,
            'continuum_and_clouds': 'H2-He Rayleigh + gray deck at 1 mbar',
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return path


def test_interactive_gui_forward_model_alignment_candidate_switching_and_project_persistence(window, tmp_path):
    import json
    from ecas.ui import comparison_browser as cb_module

    # 1. Create and select an active project via ProjectBrowser
    window.project_browser.name.setText('wasp39-gui-study')
    window.project_browser.create_button.click()
    assert window.project_browser.projects.currentText() == 'wasp39-gui-study'

    # 2. Import an observation CSV with an extra point (0.5 um) outside model coverage
    obs_csv = tmp_path / 'wasp39_obs.csv'
    obs_csv.write_text(
        'wavelength,signal,uncertainty\n'
        '0.5,1.8,0.1\n'
        '1.0,2.0,0.1\n'
        '2.0,2.2,0.1\n'
        '3.0,1.9,0.1\n',
        encoding='utf-8',
    )
    window._import_csv_from_path(str(obs_csv))
    browser = window.comparison_browser
    browser.observation_button.click()

    # Cache and select an ExoMol reference so we can stage it alongside forward models
    cache_reference(window)
    browser.reference_button.click()
    browser.reference_selector.setCurrentIndex(0)

    # 3. Open the collapsible candidate & comparison workflow tools
    assert browser.workflow_panel.isHidden()
    browser.workflow_toggle_button.click()
    assert not browser.workflow_panel.isHidden()

    model_a_path = _write_forward_model_json(
        tmp_path / 'model_a_nm_frac.json',
        source_id='model-co2-h2o-nm',
        axis_unit='nanometers',
        signal_unit='fraction',
        coordinates=[1000.0, 2000.0, 3000.0, 4000.0],
        values=[0.020, 0.021, 0.019, 0.020],
    )
    model_b_path = _write_forward_model_json(
        tmp_path / 'model_b_um_pct.json',
        source_id='model-h2o-only-um',
        axis_unit='microns',
        signal_unit='percent',
        coordinates=[1.0, 2.0, 3.0],
        values=[2.0, 2.5, 1.9],
    )

    with patch.object(cb_module.QFileDialog, 'getOpenFileName', return_value=(str(model_a_path), '')):
        browser.load_model_button.click()
    browser.load_forward_model_from_path(str(model_b_path))
    browser.add_reference_candidate_button.click()
    assert len(browser.candidate_entries) == 3

    # 4. Without caller attestations, all 3 candidates must be blocked
    browser.run_candidates_button.click()
    assert browser.current_candidate_summary.eligible_indices == ()
    assert len(browser.current_candidate_summary.blocked_indices) == 3
    assert browser.diagnostic_panel.isHidden()

    # 5. Supply explicit caller attestations, still WITHOUT opt-in alignment
    browser.obs_role_selector.setCurrentIndex(browser.obs_role_selector.findData('observation'))
    browser.obs_observable_selector.setCurrentIndex(browser.obs_observable_selector.findData('transit_depth'))
    browser.obs_axis_unit_selector.setCurrentIndex(browser.obs_axis_unit_selector.findData('microns'))
    browser.obs_signal_unit_selector.setCurrentIndex(browser.obs_signal_unit_selector.findData('percent'))
    browser.obs_frame_input.setText('barycentric')
    browser.obs_response_id_input.setText('nirspec-prism-v1')
    browser.obs_response_evidence_input.setText('JWST synthetic top-hat bin response')
    browser.obs_noise_selector.setCurrentIndex(browser.obs_noise_selector.findData('independent_gaussian_1sigma'))
    browser.obs_noise_evidence_input.setText('Published 1-sigma uncorrelated photon noise')
    browser.weighted_checkbox.setChecked(True)
    browser.independent_checkbox.setChecked(True)

    browser.run_candidates_button.click()
    assert browser.current_candidate_summary.eligible_indices == ()
    assert browser.diagnostic_panel.isHidden()

    # 6. Enable explicit opt-in unit & shared-grid alignment and re-evaluate
    browser.align_checkbox.setChecked(True)
    browser.run_candidates_button.click()
    summary = browser.current_candidate_summary
    assert summary.eligible_indices == (0, 1)
    assert summary.blocked_indices == (2,)
    assert summary.ordered_eligible_indices == (0, 1)
    assert summary.closest_candidate_indices == (0,)
    assert not browser.diagnostic_panel.isHidden()
    assert browser.residual_table.rowCount() == 3  # shared 1.0, 2.0, 3.0 um points only
    assert '1 excluded: outside_shared_exact_grid' in browser.compatibility.text()

    # 7. Inspect blocked ExoMol cross-section candidate -> plot clears immediately
    browser.candidate_selector.setCurrentIndex(2)
    assert browser.diagnostic_panel.isHidden()
    assert browser.current_diagnostic is None
    assert browser.current_eligibility.status == 'incompatible'
    assert 'right.role.requires_physical_model_or_supported_role' in browser.current_eligibility.reasons

    # Switch back to Candidate 0 -> eligible overlay & residuals reappear
    browser.candidate_selector.setCurrentIndex(0)
    assert not browser.diagnostic_panel.isHidden()
    assert browser.current_eligibility.status == 'eligible'

    # 8. Save comparison to active project and verify signed JSON envelope
    browser.save_comparison_button.click()
    assert 'Saved comparison' in browser.persistence_status.text()
    saved_path = Path(browser.saved_comparisons_selector.currentData())
    assert saved_path.is_file()
    saved_json = json.loads(saved_path.read_text(encoding='utf-8'))
    assert saved_json['left']['provenance']['caller_attestations']['axis_unit'] == 'microns'
    assert saved_json['left']['transformations'][0]['excluded_indices'] == [0]
    right_ops = [step['operation'] for step in saved_json['right']['transformations']]
    assert right_ops == [
        'convert_axis_unit_v1',
        'convert_signal_unit_v1',
        'restrict_to_shared_coordinates_v1',
    ]

    # 9. Clear session candidates/diagnostics, then verify & reopen saved comparison
    browser.clear_candidates_button.click()
    assert browser.diagnostic_panel.isHidden()
    browser.reproduce_saved_button.click()
    assert 'verdict matched, diagnostics matched' in browser.persistence_status.text()
    assert 'raw source files were not re-ingested' in browser.persistence_status.text()
    assert not browser.diagnostic_panel.isHidden()
    assert browser.residual_table.rowCount() == 3


def test_conflicting_caller_attestation_against_imported_metadata_is_rejected(window, tmp_path):
    window._import_csv_from_path(str(ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl'))
    browser = window.comparison_browser
    browser.add_current_observation()
    model_path = _write_forward_model_json(
        tmp_path / 'model.json',
        source_id='model-um',
        axis_unit='microns',
        signal_unit='percent',
        coordinates=[1.0, 2.0, 3.0],
        values=[2.0, 2.1, 1.9],
    )
    browser.load_forward_model_from_path(str(model_path))
    # feinstein-2023.tbl already establishes axis_unit == 'microns'; attesting 'nanometers' must fail
    browser.obs_axis_unit_selector.setCurrentIndex(browser.obs_axis_unit_selector.findData('nanometers'))
    browser.run_candidates_button.click()
    assert 'conflicts with imported metadata' in browser.compatibility.text()
    assert browser.diagnostic_panel.isHidden()


def test_comparison_browser_clean_ui_and_plot_minimum_heights(window, tmp_path):
    browser = window.comparison_browser
    # Verify scroll area wrapping and plot minimum heights prevent collapsing
    assert browser.scroll_area is not None
    assert browser.scroll_area.widgetResizable()
    assert browser.observation_plot.minimumHeight() >= 180
    assert browser.reference_plot.minimumHeight() >= 180

    # Summary card is present and has clean status
    assert not browser.summary_card.isHidden()
    assert 'Select an observation' in browser.clean_status_label.text()
    assert browser.technical_panel.isHidden()

    # Toggle technical panel visibility
    browser.technical_toggle_button.click()
    assert not browser.technical_panel.isHidden()
    assert browser.technical_toggle_button.text() == 'Hide Technical Details'
    browser.technical_toggle_button.click()
    assert browser.technical_panel.isHidden()
    assert browser.technical_toggle_button.text() == 'Show Technical Details & Provenance'

    # Load valid observation and forward model to test clean metrics display
    window._import_csv_from_path(str(ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl'))
    browser.add_current_observation()
    model_path = _write_forward_model_json(
        tmp_path / 'clean_test_model.json',
        source_id='clean-test-model',
        axis_unit='microns',
        signal_unit='percent',
        coordinates=[2.0, 3.0, 4.0],
        values=[2.1, 2.2, 2.0],
    )
    browser.load_forward_model_from_path(str(model_path))
    browser.auto_fill_observation_metadata()
    browser.run_candidates_button.click()

    # Verify clean summary reflects candidate evaluation
    assert not browser.diagnostic_panel.isHidden()
    assert 'RMS =' in browser.clean_metrics_label.text()
    assert 'Shape RMS =' in browser.clean_metrics_label.text()
    assert 'Multi-candidate' in browser.clean_status_label.text() or 'eligible' in browser.clean_status_label.text().lower()

    # Verify residual plot minimum height and technical tab content
    assert browser.residual_plot.minimumHeight() >= 280
    assert 'RMS =' in browser.technical_text_tab.toPlainText()
