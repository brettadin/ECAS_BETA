"""Numerical and held-out checks for the research-only fitting prototype."""
from pathlib import Path
import runpy

import numpy as np
import pytest

study = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'docs/Chunk_5/template_investigation.py'))


def test_gls_matches_independent_full_design_lstsq():
    models = np.array([[0, 1], [1, 0.5], [0.5, 0], [0.1, 0.1]])
    observations = np.array([[2, 2.3, 2.1, 2.05], [3, 2, 2.4, 2.2]])
    covariance = 0.04*0.3**np.abs(np.arange(4)[:, None]-np.arange(4))
    actual = study['fit_templates'](observations, models, covariance)
    chol = np.linalg.cholesky(covariance)
    for candidate in range(2):
        design = np.column_stack([np.ones(4), models[:, candidate]])
        for row, observation in enumerate(observations):
            expected = np.linalg.lstsq(np.linalg.solve(chol, design), np.linalg.solve(chol, observation), rcond=None)[0]
            residual = np.linalg.solve(chol, observation-design@expected)
            assert actual['baselines'][row, candidate] == pytest.approx(expected[0])
            assert actual['amplitudes'][row, candidate] == pytest.approx(expected[1])
            assert actual['null_quadratic'][row]-actual['improvement'][row, candidate] == pytest.approx(residual@residual)


def test_noiseless_known_feature_recovers_baseline_amplitude_and_center():
    _, _, models = study['template_grid']()
    fit = study['fit_templates']((2+0.06*models[:, 10])[None, :], models, np.eye(64)*0.01**2)
    assert fit['best_index'][0] == 10
    assert fit['baselines'][0, 10] == pytest.approx(2)
    assert fit['amplitudes'][0, 10] == pytest.approx(0.06)
    assert fit['null_quadratic'][0]-fit['improvement'][0, 10] == pytest.approx(0, abs=1e-10)


@pytest.mark.parametrize('covariance', [np.ones((4, 4)), np.diag([1, 1, 1, -1]),
    np.array([[1, 0.1, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])])
def test_invalid_covariance_rejected(covariance):
    with pytest.raises(ValueError):
        study['fit_templates']([[1, 2, 3, 4]], [[0], [1], [0], [0]], covariance)


def test_degenerate_template_is_not_a_false_feature():
    with pytest.raises(ValueError, match='degenerate'):
        study['fit_templates']([[1, 2, 3, 4]], np.ones((4, 1)), np.eye(4))


def test_search_threshold_is_calibrated_on_separate_null_draws():
    result = study['report']()
    assert len(set(result['seeds'].values())) == 3
    assert result['scan_threshold'] > result['fixed_template_threshold']
    local = result['holdout_scan_using_local_threshold']['fraction']
    scan = result['holdout_scan_using_scan_threshold']['fraction']
    assert local > scan+0.1
    assert 0.02 < scan < 0.09  # broad finite-simulation sanity bound, not exact 5% claim
    assert result['injected_exact_center_recovery']['fraction'] > 0.8
    assert result['injected_amplitude_median_at_true_center'] == pytest.approx(0.06, abs=0.005)
