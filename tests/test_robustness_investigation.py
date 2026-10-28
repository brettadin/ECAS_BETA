from pathlib import Path
import runpy

import pytest

study = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'docs/Chunk_5/robustness_investigation.py'))


@pytest.fixture(scope='module')
def result():
    return study['report']()


def test_calibration_is_not_transferred_between_noise_models(result):
    assert len(set(result['seeds'].values())) == 3
    correct = result['correct_noise_holdout']['fraction']
    assert 0.02 < correct < 0.09
    assert result['wrong_noise_holdout']['fraction'] > correct+0.1
    assert result['omitted_slope_holdout']['fraction'] > correct


def test_noiseless_grid_mismatch_is_visible_in_residuals(result):
    cases = result['feature_cases_noiseless']
    assert cases['on_grid']['best_residual_quadratic'] == pytest.approx(0, abs=1e-9)
    assert cases['on_grid']['fitted_amplitude'] == pytest.approx(0.06)
    assert cases['between_grid_centers']['best_residual_quadratic'] > 1
    assert cases['between_grid_centers']['absolute_center_error'] == pytest.approx(0.02)


def test_outside_grid_can_still_have_a_best_candidate(result):
    case = result['feature_cases_noiseless']['outside_search_grid']
    assert case['boundary_candidate']
    assert case['absolute_center_error'] >= 0.1
    assert case['best_improvement'] > 0
    assert case['best_residual_quadratic'] > 1
