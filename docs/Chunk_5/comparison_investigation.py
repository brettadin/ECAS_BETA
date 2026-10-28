"""Offline Chunk 5 investigation, deliberately separate from application scoring.

Run with the project Python in an isolated environment; stdout is a JSON report.
Synthetic scores illustrate failure modes, not detection significance.
"""
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from ecas.ingestion.nasa_table import import_transmission_table


def candidate_scores(observed, model, sigma):
    """Same-grid toy diagnostic with explicitly independent, positive 1-sigma errors.

    No alignment, conversion, fitted parameters or physical modelling is inferred.
    The residual sum is not reduced chi-square or a detection probability.
    """
    if not observed or len(observed) != len(model) or len(sigma) != len(model):
        raise ValueError('Require equally sized nonempty arrays on an explicit common grid')
    if any(not math.isfinite(v) for values in (observed, model, sigma) for v in values):
        raise ValueError('Require finite values')
    if any(s <= 0 for s in sigma):
        raise ValueError('Require strictly positive known uncertainties')
    average_y, average_m = sum(observed) / len(observed), sum(model) / len(model)
    y = [v - average_y for v in observed]
    m = [v - average_m for v in model]
    norm = math.sqrt(sum(v*v for v in y) * sum(v*v for v in m))
    return {
        'weighted_residual_sum': sum(((v - p) / s)**2 for v, p, s in zip(observed, model, sigma)),
        'pearson_correlation': sum(v*p for v, p in zip(y, m)) / norm if norm else None,
    }


def synthetic_experiment():
    # Invented unit-labelled curves. Not astronomical observations or a molecule.
    x = [1 + i / 100 for i in range(101)]
    shape = [math.exp(-((v-1.5)/0.08)**2) for v in x]
    observed = [2 + 0.1*v for v in shape]  # fictional transit depth, percent
    sigma = [0.01] * len(x)  # explicitly fictional independent 1-sigma percentage points
    candidates = {
        'identical': observed,
        'offset_0.2_percentage_points': [v+0.2 for v in observed],
        'double_feature_amplitude': [2+0.2*v for v in shape],
        'shifted_feature': [2+0.1*math.exp(-((v-1.6)/0.08)**2) for v in x],
        'constant': [2.0] * len(x),
    }
    # A declared fraction -> percent conversion of both values and uncertainties.
    fraction = [v/100 for v in observed]
    fraction_sigma = [v/100 for v in sigma]
    return {
        'kind': 'synthetic_not_observed', 'samples': len(x),
        'axis': 'wavelength in microns; identical grid for every candidate',
        'signal': 'fictional transit depth in percent',
        'uncertainty_assumption': 'independent known 1-sigma; no fitted parameters',
        'scores': {name: candidate_scores(observed, values, sigma) for name, values in candidates.items()},
        'declared_unit_conversion': candidate_scores(observed, [v*100 for v in fraction], [v*100 for v in fraction_sigma]),
        'limitations': ['No noise distribution calibration, covariance, resolution matching or physical model',
                        'Correlation ignores additive offsets and positive scale changes',
                        'No score is a molecular detection or posterior probability'],
    }


def source_audit():
    details = import_transmission_table(ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl')
    rows = details.spectrum.rows
    fields = ('centralwavelng', 'bandwidth', 'pl_trandep', 'pl_trandeperr1', 'pl_trandeperr2')
    summaries = {}
    for name in fields:
        values = [row[name] for row in rows if row[name] is not None]
        summaries[name] = {'missing': len(rows)-len(values), 'min': min(values), 'max': max(values)}
    return {
        'source': 'data/NASA/2026-10-27/feinstein-2023.tbl',
        'sha256': details.source_sha256, 'rows': len(rows),
        'metadata': dict(details.metadata), 'units': dict(details.column_units),
        'fields': summaries,
        'upper_nonpositive': sum(row['pl_trandeperr1'] is not None and row['pl_trandeperr1'] <= 0 for row in rows),
        'lower_nonnegative': sum(row['pl_trandeperr2'] is not None and row['pl_trandeperr2'] >= 0 for row in rows),
        'unequal_error_magnitudes': sum(abs(row['pl_trandeperr1']) != abs(row['pl_trandeperr2']) for row in rows
                                      if row['pl_trandeperr1'] is not None and row['pl_trandeperr2'] is not None),
        'transit_depth_flags': sorted({row['pl_trandeplim'] for row in rows}),
        'interpretation': 'Descriptive audit only; no error confidence level, covariance or bin edges inferred',
    }


def gaussian_bin_average(left, right, center, width):
    """Analytic average of exp(-((x-center)/width)^2) over a declared top-hat bin."""
    if not all(math.isfinite(v) for v in (left, right, center, width)) or right <= left or width <= 0:
        raise ValueError('Require finite ordered bin edges and positive feature width')
    return width * math.sqrt(math.pi) / (2 * (right-left)) * (
        math.erf((right-center)/width) - math.erf((left-center)/width))


def gaussian_response(x, center, width, lsf_sigma):
    """Analytic normalized Gaussian LSF convolution of an invented Gaussian feature."""
    if not all(math.isfinite(v) for v in (x, center, width, lsf_sigma)) or width <= 0 or lsf_sigma < 0:
        raise ValueError('Require finite inputs, positive width and nonnegative LSF sigma')
    effective_width = math.sqrt(width**2 + 2*lsf_sigma**2)
    return width/effective_width * math.exp(-((x-center)/effective_width)**2)


def covered_bins(bins, model_domain):
    """Only fully covered declared bins qualify; no silent clipping/extrapolation."""
    start, stop = model_domain
    if not math.isfinite(start) or not math.isfinite(stop) or start >= stop:
        raise ValueError('Require a finite ordered model domain')
    accepted, excluded = [], []
    for index, (left, right) in enumerate(bins):
        if not math.isfinite(left) or not math.isfinite(right) or left >= right:
            raise ValueError('Require finite ordered bin edges')
        (accepted if start <= left and right <= stop else excluded).append(index)
    return {'accepted_indices': accepted, 'excluded_indices': excluded}


def asymmetric_penalty(observed, model, lower, upper):
    """Toy side-dependent quadratic penalty, NOT a justified asymmetric likelihood.

    Lower/upper are positive magnitudes on the observed value's interval; a model
    below that value uses lower. No normalization or probability is calculated.
    """
    if not observed or not all(len(values) == len(observed) for values in (model, lower, upper)):
        raise ValueError('Require equally sized nonempty arrays')
    if any(not math.isfinite(v) for values in (observed, model, lower, upper) for v in values):
        raise ValueError('Require finite values')
    if any(v <= 0 for values in (lower, upper) for v in values):
        raise ValueError('Require positive error magnitudes')
    return sum(((m-y) / (hi if m >= y else lo))**2
               for y, m, lo, hi in zip(observed, model, lower, upper))


def equicorrelated_penalty(residuals, sigma, rho):
    """r^T C^-1 r for C=sigma^2*((1-rho)*I+rho*11^T), 0<=rho<1.

    Fixed known covariance only; omits log determinant/normalization, and must
    not be used to fit rho or compare likelihoods across covariance choices.
    """
    if not residuals or not all(math.isfinite(v) for v in residuals):
        raise ValueError('Require nonempty finite residuals')
    if not math.isfinite(sigma) or sigma <= 0 or not math.isfinite(rho) or not 0 <= rho < 1:
        raise ValueError('Require positive sigma and 0 <= rho < 1')
    z = [v/sigma for v in residuals]
    n = len(z)
    # Decompose into mean and zero-mean components to avoid subtractive cancellation.
    mean = sum(z)/n
    return sum((v-mean)**2 for v in z)/(1-rho) + n*mean**2/(1+(n-1)*rho)


def response_experiment():
    # Irregular edges, analytic spectra and invented parameters, unrelated to NASA bandwidth.
    edges = [1.0, 1.31, 1.46, 1.54, 1.73, 2.0]
    bins = list(zip(edges, edges[1:]))
    centers = [(a+b)/2 for a, b in bins]
    truth = [2+0.1*gaussian_bin_average(a, b, 1.5, 0.04) for a, b in bins]
    center_samples = [2+0.1*math.exp(-((v-1.5)/0.04)**2) for v in centers]
    # Two narrow invented features versus one broader invented feature, before/after binning.
    dense = [1+i/1000 for i in range(1001)]
    blend = lambda x: 0.05*(math.exp(-((x-1.48)/0.01)**2)+math.exp(-((x-1.52)/0.01)**2))
    single = lambda x: 0.05*math.exp(-((x-1.5)/0.02)**2)
    blend_bin = 0.05*(gaussian_bin_average(1.4, 1.6, 1.48, 0.01)+gaussian_bin_average(1.4, 1.6, 1.52, 0.01))
    single_bin = 0.05*gaussian_bin_average(1.4, 1.6, 1.5, 0.02)
    return {
        'kind': 'synthetic_not_observed',
        'response_assumption': 'explicit top-hat bins, analytic Gaussian features; no real instrument LSF',
        'irregular_bin_edges_microns': edges,
        'bin_average_vs_point_sample': candidate_scores(truth, center_samples, [0.001]*len(truth)),
        'matching_bin_averages': candidate_scores(truth, truth, [0.001]*len(truth)),
        'gaussian_lsf': {
            'feature_width': 0.04, 'lsf_sigma': 0.03, 'units': 'microns',
            'unmatched_model': candidate_scores(
                [2+0.1*gaussian_response(x, 1.5, 0.04, 0.03) for x in dense],
                [2+0.1*math.exp(-((x-1.5)/0.04)**2) for x in dense], [0.001]*len(dense)),
            'caveat': 'Known invented constant Gaussian LSF; not the NASA instrument response'},
        'partial_coverage': covered_bins(bins, (1.3, 1.75)),
        'no_coverage': covered_bins(bins, (3, 4)),
        'blend': {'dense_max_absolute_difference': max(abs(blend(x)-single(x)) for x in dense),
                  'one_coarse_bin_absolute_difference': abs(blend_bin-single_bin),
                  'interpretation': 'Distinct shapes can be indistinguishable after coarse averaging; no species identities'},
        'asymmetric_errors': {'model_below': asymmetric_penalty([2], [1.9], [0.1], [0.2]),
                              'model_above': asymmetric_penalty([2], [2.1], [0.1], [0.2]),
                              'caveat': 'Illustrative penalty only; confidence convention does not determine likelihood'},
        'fixed_covariance': {
            'common_residual_diagonal': equicorrelated_penalty([1]*10, 1, 0),
            'common_residual_rho_0.8': equicorrelated_penalty([1]*10, 1, 0.8),
            'alternating_residual_diagonal': equicorrelated_penalty([1, -1]*5, 1, 0),
            'alternating_residual_rho_0.8': equicorrelated_penalty([1, -1]*5, 1, 0.8),
            'caveat': 'Fixed covariance counterexamples, not a noise simulation or likelihood ranking'},
    }


def report():
    return {'stage': 'chunk5-investigation-v2', 'source_audit': source_audit(),
            'synthetic_experiment': synthetic_experiment(), 'response_experiment': response_experiment()}


if __name__ == '__main__':
    print(json.dumps(report(), indent=2, allow_nan=False))
