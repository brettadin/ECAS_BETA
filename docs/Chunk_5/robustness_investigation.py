"""Synthetic noise/model misspecification checks; reviewed fitting code stays unchanged."""
import json
from pathlib import Path
import runpy

import numpy as np

study = runpy.run_path(str(Path(__file__).with_name('template_investigation.py')))


def report():
    edges, centers, models = study['template_grid']()
    bins = len(edges)-1
    x = (edges[:-1]+edges[1:])/2
    covariance = 0.01**2 * 0.65**np.abs(np.arange(bins)[:, None]-np.arange(bins))
    diagonal = np.eye(bins)*0.01**2
    chol = np.linalg.cholesky(covariance)
    seeds = {'correct_calibration': 20261101, 'diagonal_calibration': 20261102,
             'holdout': 20261103}
    fit = study['fit_templates']
    count = 2000

    def draws(seed, factor):
        return np.random.default_rng(seed).normal(size=(count, bins)) @ factor.T

    correct_null = 2+draws(seeds['correct_calibration'], chol)
    diagonal_null = 2+draws(seeds['diagonal_calibration'], np.linalg.cholesky(diagonal))
    holdout = 2+draws(seeds['holdout'], chol)
    correct_threshold = float(np.quantile(fit(correct_null, models, covariance)['improvement'].max(axis=1), 0.95, method='higher'))
    diagonal_threshold = float(np.quantile(fit(diagonal_null, models, diagonal)['improvement'].max(axis=1), 0.95, method='higher'))
    correct = fit(holdout, models, covariance)
    wrong_noise = fit(holdout, models, diagonal)
    # The truth has no template feature. The alternative can absorb part of an
    # omitted continuum slope; report as model inadequacy, not a false molecule.
    slope = 0.04*(x-1.5)
    omitted_slope = fit(holdout+slope, models, covariance)
    feature_cases = {}
    for label, center in [('on_grid', 1.5), ('between_grid_centers', 1.52), ('outside_search_grid', 0.99)]:
        width, lsf_sigma = 0.035, 0.02
        effective = float(np.sqrt(width**2+2*lsf_sigma**2))
        truth = 2+0.06*width/effective*np.array([
            study['response']['gaussian_bin_average'](float(a), float(b), center, effective)
            for a, b in zip(edges[:-1], edges[1:])])
        fitted = fit(truth[None, :], models, covariance)
        index = int(fitted['best_index'][0])
        feature_cases[label] = {'true_center': center, 'selected_center': float(centers[index]),
            'boundary_candidate': index in (0, len(centers)-1),
            'absolute_center_error': abs(float(centers[index])-center),
            'best_residual_quadratic': float(max(0, fitted['null_quadratic'][0]-fitted['improvement'][0, index])),
            'best_improvement': float(fitted['improvement'][0, index]),
            'injected_amplitude': 0.06, 'fitted_amplitude': float(fitted['amplitudes'][0, index])}
    return {'stage': 'chunk5-robustness-v1', 'kind': 'synthetic_not_observed',
        'seeds': seeds, 'trials_per_noise_case': count, 'numpy_version': np.__version__,
        'settings': {'true_ar1_rho': 0.65, 'sigma': 0.01, 'assumed_wrong_rho': 0,
                     'continuum_slope_percent_per_micron': 0.04, 'calibration_quantile': 0.95,
                     'quantile_method': 'higher'},
        'correct_threshold': correct_threshold, 'diagonal_threshold': diagonal_threshold,
        'correct_noise_holdout': study['rate_summary'](correct['improvement'].max(axis=1)>correct_threshold),
        'wrong_noise_holdout': study['rate_summary'](wrong_noise['improvement'].max(axis=1)>diagonal_threshold),
        'omitted_slope_holdout': study['rate_summary'](omitted_slope['improvement'].max(axis=1)>correct_threshold),
        'feature_cases_noiseless': feature_cases,
        'limitations': ['No covariance or continuum estimated from data',
                        'Omitted slope is a deliberately misspecified null, not a valid false-positive calibration',
                        'Boundary hit is a warning heuristic, not proof of absent template coverage',
                        'No real data or physical species; thresholds not transferable']}


if __name__ == '__main__':
    print(json.dumps(report(), indent=2, allow_nan=False))
