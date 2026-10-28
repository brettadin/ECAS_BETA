"""Synthetic template fitting and held-out null calibration; no application integration.

This is a numerical prototype, not atmospheric forward modelling or molecular
detection. Invented feature templates have no species identity.
"""
from hashlib import sha256
import json
from pathlib import Path
import runpy

import numpy as np

response = runpy.run_path(str(Path(__file__).with_name('comparison_investigation.py')))


def fit_templates(observations, templates, covariance):
    """GLS fits baseline + signed amplitude for each fixed template.

    observations: (draws, bins); templates: (bins, candidates); covariance:
    (bins, bins), known and fixed, positive definite. Candidates use the same data,
    units and covariance. Returns null improvement, NOT a detection significance.
    """
    y, models, cov = (np.asarray(v, dtype=float) for v in (observations, templates, covariance))
    if y.ndim != 2 or models.ndim != 2 or cov.ndim != 2:
        raise ValueError('Require observations and templates matrices and square covariance')
    draws, bins = y.shape
    if not draws or bins < 3 or models.shape[0] != bins or not models.shape[1] or cov.shape != (bins, bins):
        raise ValueError('Incompatible or empty input dimensions')
    if not all(np.isfinite(v).all() for v in (y, models, cov)):
        raise ValueError('Require finite inputs')
    if not np.allclose(cov, cov.T, rtol=1e-12, atol=0):
        raise ValueError('Covariance must be symmetric')
    try:
        chol = np.linalg.cholesky(cov)
    except np.linalg.LinAlgError as error:
        raise ValueError('Covariance must be positive definite') from error
    white_y = np.linalg.solve(chol, y.T).T
    white_models = np.linalg.solve(chol, models)
    white_one = np.linalg.solve(chol, np.ones(bins))
    one_norm = white_one @ white_one
    base_null = white_y @ white_one / one_norm
    residual_y = white_y - base_null[:, None]*white_one
    model_mean = white_one @ white_models / one_norm
    residual_models = white_models - white_one[:, None]*model_mean
    model_norm = np.sum(residual_models**2, axis=0)
    if np.any(model_norm <= np.finfo(float).eps*np.sum(white_models**2, axis=0)):
        raise ValueError('Template is degenerate with fitted constant baseline')
    projection = residual_y @ residual_models
    amplitudes = projection / model_norm
    improvement = projection**2 / model_norm
    null_q = np.sum(residual_y**2, axis=1)
    return {'improvement': improvement, 'amplitudes': amplitudes,
            'baselines': base_null[:, None]-amplitudes*model_mean,
            'null_quadratic': null_q, 'best_index': np.argmax(improvement, axis=1)}


def template_grid():
    edges = np.linspace(1, 2, 65)
    centers = np.linspace(1.1, 1.9, 21)
    width, lsf_sigma = 0.035, 0.02
    effective_width = np.sqrt(width**2+2*lsf_sigma**2)
    models = np.array([[width/effective_width*response['gaussian_bin_average'](
        float(left), float(right), float(center), float(effective_width))
        for center in centers] for left, right in zip(edges[:-1], edges[1:])])
    return edges, centers, models


def rate_summary(mask):
    count, trials = int(np.count_nonzero(mask)), int(len(mask))
    fraction = count/trials
    return {'count': count, 'trials': trials, 'fraction': fraction,
            'binomial_standard_error': float(np.sqrt(fraction*(1-fraction)/trials))}


def report():
    edges, centers, models = template_grid()
    bins, candidates = models.shape
    sigma, rho = 0.01, 0.65
    covariance = sigma**2*rho**np.abs(np.arange(bins)[:, None]-np.arange(bins))
    chol = np.linalg.cholesky(covariance)
    seeds = {'calibration': 20261028, 'holdout_null': 20261029, 'injected': 20261030}

    def noise(seed, count):
        return np.random.default_rng(seed).normal(size=(count, bins)) @ chol.T

    calibration = fit_templates(2+noise(seeds['calibration'], 2000), models, covariance)
    local_index = candidates//2
    local_threshold = float(np.quantile(calibration['improvement'][:, local_index], 0.95, method='higher'))
    scan_threshold = float(np.quantile(calibration['improvement'].max(axis=1), 0.95, method='higher'))
    holdout = fit_templates(2+noise(seeds['holdout_null'], 2000), models, covariance)
    injected = fit_templates(2+0.06*models[:, local_index]+noise(seeds['injected'], 500), models, covariance)
    best_injected = injected['best_index']
    return {
        'stage': 'chunk5-template-v1', 'kind': 'synthetic_not_observed', 'numpy_version': np.__version__,
        'seeds': seeds, 'axis_unit': 'microns', 'signal_unit': 'fictional transit-depth percent',
        'bin_edges': edges.tolist(), 'template_centers': centers.tolist(),
        'feature_width': 0.035, 'lsf_sigma': 0.02, 'noise_sigma': sigma, 'noise_ar1_rho': rho,
        'template_sha256': sha256(models.tobytes()).hexdigest(),
        'covariance_sha256': sha256(covariance.tobytes()).hexdigest(),
        'null_model': 'fitted constant', 'alternative': 'fitted constant + signed amplitude times fixed template',
        'calibration_trials': 2000, 'quantile': 0.95, 'quantile_method': 'higher',
        'fixed_template_index': local_index, 'fixed_template_threshold': local_threshold,
        'scan_threshold': scan_threshold,
        'holdout_fixed_template': rate_summary(holdout['improvement'][:, local_index] > local_threshold),
        'holdout_scan_using_local_threshold': rate_summary(holdout['improvement'].max(axis=1) > local_threshold),
        'holdout_scan_using_scan_threshold': rate_summary(holdout['improvement'].max(axis=1) > scan_threshold),
        'injected_scan_threshold_exceedance': rate_summary(injected['improvement'].max(axis=1) > scan_threshold),
        'injected_exact_center_recovery': rate_summary(best_injected == local_index),
        'injected_amplitude_median_at_true_center': float(np.median(injected['amplitudes'][:, local_index])),
        'limitations': ['Fixed known Gaussian AR(1) covariance and invented response',
                        'Thresholds valid only for this exact null, fitting procedure and search grid',
                        'No atmospheric parameters, physical species, Bayesian evidence or real data scoring',
                        'Finite calibration and holdout samples; no tail significance extrapolation'],
    }


if __name__ == '__main__':
    print(json.dumps(report(), indent=2, allow_nan=False))
