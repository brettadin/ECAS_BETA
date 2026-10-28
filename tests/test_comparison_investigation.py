"""Check conclusions of the isolated experiment, not a production comparison API."""
from pathlib import Path
import runpy

import pytest

study = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'docs/Chunk_5/comparison_investigation.py'))


def test_correlation_cannot_distinguish_offset_or_feature_scale():
    scores = study['synthetic_experiment']()['scores']
    assert scores['identical']['weighted_residual_sum'] == 0
    for name in ('offset_0.2_percentage_points', 'double_feature_amplitude'):
        assert scores[name]['pearson_correlation'] == pytest.approx(1)
        assert scores[name]['weighted_residual_sum'] > 100
    assert scores['constant']['pearson_correlation'] is None
    assert scores['shifted_feature']['pearson_correlation'] < 0.9


def test_explicit_unit_conversion_preserves_residuals():
    scores = study['synthetic_experiment']()['declared_unit_conversion']
    assert scores['weighted_residual_sum'] == pytest.approx(0, abs=1e-20)
    assert scores['pearson_correlation'] == pytest.approx(1)


@pytest.mark.parametrize('sigma', [[0, 1], [-1, 1], [None, 1], [float('nan'), 1]])
def test_unknown_or_nonpositive_errors_do_not_yield_a_score(sigma):
    with pytest.raises((TypeError, ValueError)):
        study['candidate_scores']([1, 2], [1, 2], sigma)


def test_real_fixture_audit_identifies_unchanged_capture():
    audit = study['source_audit']()
    assert audit['sha256'] == '3140d259259c51e282cd075890cc878ab79c9bb859fae3b83ab5459756e9adc2'
    assert audit['rows'] == 331
    assert audit['units']['centralwavelng'] == 'microns'
    assert audit['units']['pl_trandep'] == '%'


def test_analytic_bin_average_matches_independent_numerical_integration():
    import math
    # Simpson integration independently checks the erf-based analytical formula.
    left, right, center, width, count = 1.31, 1.54, 1.5, 0.04, 10000
    step = (right-left)/count
    f = lambda x: math.exp(-((x-center)/width)**2)
    integral = step/3*(f(left)+f(right)+sum((4 if i % 2 else 2)*f(left+i*step) for i in range(1, count)))
    assert study['gaussian_bin_average'](left, right, center, width) == pytest.approx(integral/(right-left), rel=1e-10)


def test_sampling_and_blending_counterexamples_are_not_absolute_agreement():
    result = study['response_experiment']()
    assert result['matching_bin_averages']['weighted_residual_sum'] == 0
    assert result['bin_average_vs_point_sample']['weighted_residual_sum'] > 100
    assert result['blend']['dense_max_absolute_difference'] > 0.02
    assert result['blend']['one_coarse_bin_absolute_difference'] < 1e-10


def test_partial_bins_are_excluded_without_silent_clipping():
    result = study['response_experiment']()
    assert result['partial_coverage'] == {'accepted_indices': [1, 2, 3], 'excluded_indices': [0, 4]}
    assert result['no_coverage'] == {'accepted_indices': [], 'excluded_indices': [0, 1, 2, 3, 4]}


@pytest.mark.parametrize('bins,domain', [([(2, 1)], (0, 3)), ([(1, 2)], (3, 0)),
                                       ([(1, float('nan'))], (0, 3))])
def test_invalid_coverage_inputs_rejected(bins, domain):
    with pytest.raises(ValueError):
        study['covered_bins'](bins, domain)


def test_asymmetric_magnitudes_use_the_declared_side_not_silent_averaging():
    result = study['response_experiment']()['asymmetric_errors']
    assert result['model_below'] == pytest.approx(1)
    assert result['model_above'] == pytest.approx(0.25)
    with pytest.raises(ValueError):
        study['asymmetric_penalty']([2], [1.9], [-0.1], [0.2])


@pytest.mark.parametrize('residuals', [[1]*10, [1, -1]*5, [0.2, -0.7, 0.8]])
def test_covariance_expression_matches_independent_linear_solve(residuals):
    import numpy as np
    sigma, rho = 0.4, 0.8
    n = len(residuals)
    covariance = sigma**2*((1-rho)*np.eye(n)+rho*np.ones((n, n)))
    vector = np.array(residuals)
    expected = vector @ np.linalg.solve(covariance, vector)
    assert study['equicorrelated_penalty'](residuals, sigma, rho) == pytest.approx(expected)


def test_ignoring_correlation_can_bias_penalty_in_either_direction():
    result = study['response_experiment']()['fixed_covariance']
    assert result['common_residual_rho_0.8'] < result['common_residual_diagonal']
    assert result['alternating_residual_rho_0.8'] > result['alternating_residual_diagonal']


@pytest.mark.parametrize('rho', [-0.1, 1, float('nan')])
def test_unsupported_or_singular_covariance_rejected(rho):
    with pytest.raises(ValueError):
        study['equicorrelated_penalty']([1, 2], 1, rho)


def test_gaussian_lsf_matches_independent_convolution_integral():
    import math
    x, center, width, sigma = 1.51, 1.5, 0.04, 0.03
    count, left, right = 10000, 1.0, 2.0
    step = (right-left)/count
    f = lambda t: math.exp(-((t-center)/width)**2)*math.exp(-0.5*((x-t)/sigma)**2)/(sigma*math.sqrt(2*math.pi))
    integral = step/3*(f(left)+f(right)+sum((4 if i % 2 else 2)*f(left+i*step) for i in range(1, count)))
    assert study['gaussian_response'](x, center, width, sigma) == pytest.approx(integral, rel=1e-10)
    assert study['gaussian_response'](center, center, width, 0) == 1
    assert study['response_experiment']()['gaussian_lsf']['unmatched_model']['weighted_residual_sum'] > 100
