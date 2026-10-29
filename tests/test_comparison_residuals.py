"""Unit and scientific boundary tests for production residual diagnostics."""
from dataclasses import FrozenInstanceError, replace
import math
from pathlib import Path

import numpy as np
import pytest

from ecas.comparison.eligibility import VERSION, ComparisonInput
from ecas.comparison.inputs import observation_input, reference_input
from ecas.comparison.residuals import (
    IneligibleComparisonError,
    ResidualDiagnostic,
    evaluate_residuals,
)
from ecas.ingestion.exomol_product import ProductRequest, validate_product
from ecas.ingestion.exomol_product_network import RetrievedCrossSection
from ecas.ingestion.nasa_table import import_transmission_table

ROOT = Path(__file__).resolve().parents[1]


def synthetic_observation():
    return ComparisonInput(
        source_id='synthetic-observation',
        source_sha256='a' * 64,
        role='observation',
        observable='transit_depth',
        axis_unit='microns',
        signal_unit='percent',
        coordinate_frame='barycentric-synthetic',
        response_id='synthetic-tophat-v1',
        response_evidence='synthetic test response declaration',
        coordinates=(1.0, 2.0, 3.0, 4.0),
        values=(2.0, 2.3, 1.9, 2.2),
        noise_kind='independent_gaussian_1sigma',
        noise_evidence='synthetic independent 1-sigma errors',
        sigma=(0.1, 0.2, 0.1, 0.2),
    )


def synthetic_model():
    return replace(
        synthetic_observation(),
        source_id='synthetic-forward-model',
        source_sha256='b' * 64,
        role='forward_model',
        values=(2.0, 2.1, 2.1, 1.8),
        noise_kind='deterministic_model',
        noise_evidence='synthetic deterministic forward model',
        sigma=None,
    )


def test_unweighted_aligned_residuals_preserve_sign_units_and_provenance():
    left = synthetic_observation()
    right = synthetic_model()
    result = evaluate_residuals(left, right)

    assert isinstance(result, ResidualDiagnostic)
    assert result.version == VERSION == 'ecas-comparison-eligibility-v1'
    assert result.operation == 'aligned_residual_v1'
    assert result.eligibility.status == 'eligible'
    assert result.source_ids == ('synthetic-observation', 'synthetic-forward-model')
    assert result.source_sha256s == ('a' * 64, 'b' * 64)
    assert result.observable == 'transit_depth'
    assert result.axis_unit == 'microns'
    assert result.signal_unit == 'percent'
    assert result.coordinate_frame == 'barycentric-synthetic'
    assert result.response_id == 'synthetic-tophat-v1'
    assert result.residual_convention == 'left_minus_right'
    assert result.coordinates == (1.0, 2.0, 3.0, 4.0)
    assert result.left_values == (2.0, 2.3, 1.9, 2.2)
    assert result.right_values == (2.0, 2.1, 2.1, 1.8)
    assert result.sample_count == 4

    # Expected: (0.0, +0.2, -0.2, +0.4)
    expected = (0.0, 0.2, -0.2, 0.4)
    assert np.allclose(result.residuals, expected, rtol=0, atol=1e-15)
    assert math.isclose(result.mean_residual, 0.1, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(result.mean_abs_residual, 0.2, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(result.rms_residual, math.sqrt(0.24 / 4.0), rel_tol=0, abs_tol=1e-15)
    assert math.isclose(result.max_abs_residual, 0.4, rel_tol=0, abs_tol=1e-15)
    assert result.whitened_residuals is None
    assert result.weighted_residual_quadratic is None

    with pytest.raises(FrozenInstanceError):
        result.mean_residual = 0.0


def test_identical_inputs_yield_exact_zero_unweighted_residuals():
    left = synthetic_observation()
    right = replace(synthetic_model(), values=left.values)
    result = evaluate_residuals(left, right)
    assert result.residuals == (0.0, 0.0, 0.0, 0.0)
    assert result.mean_residual == 0.0
    assert result.mean_abs_residual == 0.0
    assert result.rms_residual == 0.0
    assert result.max_abs_residual == 0.0


def test_weighted_residuals_with_independent_and_correlated_covariance():
    left = synthetic_observation()
    right = synthetic_model()
    result = evaluate_residuals(left, right, weighted=True, cross_dataset_independent=True)

    assert result.operation == 'weighted_residual_v1'
    # Residuals: (0.0, 0.2, -0.2, 0.4), sigma: (0.1, 0.2, 0.1, 0.2)
    # Whitened: (0.0, 1.0, -2.0, 2.0), quadratic: 0 + 1 + 4 + 4 = 9.0
    assert np.allclose(result.whitened_residuals, (0.0, 1.0, -2.0, 2.0), rtol=0, atol=1e-14)
    assert math.isclose(result.weighted_residual_quadratic, 9.0, rel_tol=0, abs_tol=1e-14)

    # Full positive-definite covariance on left + independent Gaussian on right
    cov_left = (
        (0.04, 0.01, 0.00, 0.00),
        (0.01, 0.04, 0.01, 0.00),
        (0.00, 0.01, 0.04, 0.01),
        (0.00, 0.00, 0.01, 0.04),
    )
    corr_left = replace(
        left,
        noise_kind='gaussian_covariance',
        sigma=None,
        covariance=cov_left,
    )
    stoch_right = replace(
        right,
        role='reference_measurement',
        noise_kind='independent_gaussian_1sigma',
        noise_evidence='synthetic reference 1-sigma errors',
        sigma=(0.1, 0.1, 0.1, 0.1),
    )
    corr_result = evaluate_residuals(
        corr_left, stoch_right, weighted=True, cross_dataset_independent=True
    )
    combined = np.asarray(cov_left) + np.diag([0.01, 0.01, 0.01, 0.01])
    diff = np.asarray(left.values) - np.asarray(right.values)
    expected_q = float(diff @ np.linalg.solve(combined, diff))
    assert math.isclose(corr_result.weighted_residual_quadratic, expected_q, rel_tol=1e-13, abs_tol=1e-15)
    assert math.isclose(
        sum(w * w for w in corr_result.whitened_residuals),
        expected_q,
        rel_tol=1e-13,
        abs_tol=1e-15,
    )


@pytest.mark.parametrize(
    'modifier,kwargs,expected_reason',
    [
        (lambda l, r: (l, r), {'weighted': True, 'cross_dataset_independent': False},
         'pair.cross_dataset_independence.not_declared'),
        (lambda l, r: (replace(l, role=None), r), {}, 'left.role.missing'),
        (lambda l, r: (replace(l, axis_unit='nanometers'), r), {},
         'left.axis_unit.explicit_conversion_required'),
        (lambda l, r: (replace(l, coordinates=(1.0, 2.0, 3.0, 5.0)), r), {},
         'pair.coordinates.not_exactly_aligned'),
        (lambda l, r: (l, replace(r, noise_kind='gaussian_covariance',
                                  covariance=((1., 1., 1., 1.),) * 4)),
         {'weighted': True, 'cross_dataset_independent': True},
         'right.noise.invalid'),
    ],
)
def test_ineligible_inputs_raise_structured_error_without_computing_scores(
    modifier, kwargs, expected_reason
):
    left, right = modifier(synthetic_observation(), synthetic_model())
    with pytest.raises(IneligibleComparisonError) as exc_info:
        evaluate_residuals(left, right, **kwargs)
    assert expected_reason in exc_info.value.eligibility.reasons
    assert expected_reason in str(exc_info.value)


def test_captured_nasa_and_exomol_cross_section_are_blocked_by_residual_service():
    details = import_transmission_table(ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl')
    obs = observation_input(details.spectrum, details.source_sha256)

    request = ProductRequest(4000, 4010, 500, '1')
    raw = (ROOT / 'data/ExoMol/2026-10-28/CO2-12C-16O2-500K-4000-4010-dnu1.sigma').read_bytes()
    ref = reference_input(RetrievedCrossSection(request, raw, validate_product(raw, request)))

    with pytest.raises(IneligibleComparisonError) as exc_info:
        evaluate_residuals(obs.comparison_input, ref.comparison_input)
    eligibility = exc_info.value.eligibility
    assert eligibility.status == 'incompatible'
    assert 'right.role.requires_physical_model_or_supported_role' in eligibility.reasons
    assert 'right.observable.unsupported_in_v1' in eligibility.reasons

