"""Tests for explicit unit conversions, shared-grid restriction, and top-hat bin integration."""
from dataclasses import replace
import math

import numpy as np
import pytest

from ecas.comparison.alignment import (
    convert_axis_unit,
    convert_signal_unit,
    integrate_model_over_bins,
    restrict_to_shared_coordinates,
)
from ecas.comparison.eligibility import ComparisonInput
from ecas.comparison.residuals import evaluate_residuals


def base_observation():
    return ComparisonInput(
        source_id='synthetic-obs',
        source_sha256='a' * 64,
        role='observation',
        observable='transit_depth',
        axis_unit='microns',
        signal_unit='percent',
        coordinate_frame='barycentric-synthetic',
        response_id='synthetic-tophat-v1',
        response_evidence='synthetic top-hat bins',
        coordinates=(1.0, 1.5, 2.0, 2.5),
        values=(2.0, 2.2, 2.1, 2.3),
        noise_kind='gaussian_covariance',
        noise_evidence='synthetic correlated covariance',
        covariance=(
            (0.04, 0.01, 0.00, 0.00),
            (0.01, 0.04, 0.01, 0.00),
            (0.00, 0.01, 0.04, 0.01),
            (0.00, 0.00, 0.01, 0.04),
        ),
    )


def test_signal_unit_conversion_scales_values_sigma_and_covariance_invariantly():
    obs_pct = base_observation()
    model_frac = ComparisonInput(
        source_id='synthetic-model-fraction',
        source_sha256='b' * 64,
        role='forward_model',
        observable='transit_depth',
        axis_unit='microns',
        signal_unit='fraction',
        coordinate_frame='barycentric-synthetic',
        response_id='synthetic-tophat-v1',
        response_evidence='synthetic top-hat bins',
        coordinates=(1.0, 1.5, 2.0, 2.5),
        values=(0.020, 0.021, 0.022, 0.021),
        noise_kind='deterministic_model',
        noise_evidence='synthetic deterministic model',
    )

    # Convert model fraction -> percent and compare
    model_to_pct = convert_signal_unit(model_frac, 'percent')
    assert model_to_pct.original == model_frac  # original untouched
    assert model_to_pct.steps[0].operation == 'convert_signal_unit_v1'
    diag_pct = evaluate_residuals(
        obs_pct, model_to_pct.transformed, weighted=True, cross_dataset_independent=True
    )

    # Convert observation percent -> fraction (scaling covariance by 1e-4) and compare
    obs_to_frac = convert_signal_unit(obs_pct, 'fraction')
    diag_frac = evaluate_residuals(
        obs_to_frac.transformed, model_frac, weighted=True, cross_dataset_independent=True
    )

    assert math.isclose(diag_pct.rms_residual, diag_frac.rms_residual * 100.0, rel_tol=1e-13)
    # Dimensionless weighted quadratic must be invariant under unit scaling!
    assert math.isclose(
        diag_pct.weighted_residual_quadratic,
        diag_frac.weighted_residual_quadratic,
        rel_tol=1e-13,
    )

    with pytest.raises(ValueError):
        convert_signal_unit(replace(obs_pct, signal_unit='cm^2/molecule'), 'percent')


def test_axis_unit_conversion_preserves_order_and_rejects_wavenumber():
    nm_model = ComparisonInput(
        source_id='synthetic-nm',
        source_sha256='c' * 64,
        role='forward_model',
        observable='transit_depth',
        axis_unit='nanometers',
        signal_unit='percent',
        coordinate_frame='barycentric-synthetic',
        response_id='synthetic-tophat-v1',
        response_evidence='synthetic top-hat bins',
        coordinates=(1000.0, 1500.0, 2000.0, 2500.0),
        values=(2.0, 2.2, 2.1, 2.3),
    )
    converted = convert_axis_unit(nm_model, 'microns')
    assert converted.original.axis_unit == 'nanometers'
    assert converted.transformed.axis_unit == 'microns'
    assert np.allclose(converted.transformed.coordinates, (1.0, 1.5, 2.0, 2.5))

    with pytest.raises(ValueError):
        convert_axis_unit(replace(nm_model, axis_unit='cm^-1'), 'microns')


def test_restrict_to_shared_coordinates_records_excluded_indices_and_slices_covariance():
    left = base_observation()  # coords: (1.0, 1.5, 2.0, 2.5)
    right = ComparisonInput(
        source_id='synthetic-partial-model',
        source_sha256='d' * 64,
        role='forward_model',
        observable='transit_depth',
        axis_unit='microns',
        signal_unit='percent',
        coordinate_frame='barycentric-synthetic',
        response_id='synthetic-tophat-v1',
        response_evidence='synthetic top-hat bins',
        coordinates=(0.8, 1.5, 2.0, 2.5, 3.0),
        values=(1.9, 2.1, 2.1, 2.0, 2.4),
        noise_kind='deterministic_model',
        noise_evidence='synthetic deterministic',
    )

    sub_left, sub_right = restrict_to_shared_coordinates(left, right)
    assert sub_left.steps[0].included_indices == (1, 2, 3)
    assert sub_left.steps[0].excluded_indices == (0,)
    assert sub_left.steps[0].exclusion_reason == 'outside_shared_exact_grid'
    assert sub_right.steps[0].included_indices == (1, 2, 3)
    assert sub_right.steps[0].excluded_indices == (0, 4)
    assert np.asarray(sub_left.transformed.covariance).shape == (3, 3)

    diag = evaluate_residuals(
        sub_left.transformed,
        sub_right.transformed,
        weighted=True,
        cross_dataset_independent=True,
    )
    assert diag.coordinates == (1.5, 2.0, 2.5)

    # Fewer than 3 shared points must be rejected
    too_few = replace(right, coordinates=(0.8, 1.5, 2.0, 3.1))
    with pytest.raises(ValueError, match='Insufficient exact coordinate overlap'):
        restrict_to_shared_coordinates(left, too_few)


def test_integrate_model_over_bins_matches_analytic_integral_and_blocks_observation_upsampling():
    # Dense linear-plus-tent model over [1.0, 3.0] microns: y(x) = 2.0 + 0.5 * x
    dense_x = tuple(1.0 + 0.05 * i for i in range(41))
    dense_y = tuple(2.0 + 0.5 * x for x in dense_x)
    dense_model = ComparisonInput(
        source_id='synthetic-dense-model',
        source_sha256='e' * 64,
        role='forward_model',
        observable='transit_depth',
        axis_unit='microns',
        signal_unit='percent',
        coordinate_frame='barycentric-synthetic',
        response_id='native-highres-grid',
        response_evidence='synthetic dense grid',
        coordinates=dense_x,
        values=dense_y,
        noise_kind='deterministic_model',
        noise_evidence='synthetic deterministic',
    )

    # Bin 0 is partially outside [1.0, 3.0] -> must be excluded, never extrapolated!
    bin_centers = (1.0, 1.5, 2.0, 2.5)
    bin_edges = ((0.9, 1.1), (1.3, 1.7), (1.8, 2.2), (2.3, 2.7))
    binned, inc, exc = integrate_model_over_bins(
        dense_model,
        bin_centers,
        bin_edges,
        response_id='synthetic-tophat-v1',
        response_evidence='declared top-hat bin edges',
    )
    assert inc == (1, 2, 3)
    assert exc == (0,)
    assert binned.steps[0].exclusion_reason == 'bin_not_fully_covered_by_model_domain'
    assert binned.transformed.coordinates == (1.5, 2.0, 2.5)
    # Analytic average of linear 2.0 + 0.5*x on symmetric bin around c is exact 2.0 + 0.5*c
    assert np.allclose(binned.transformed.values, (2.75, 3.0, 3.25), rtol=0, atol=1e-14)

    # Observations must never be upsampled or passed as models into bin integration
    with pytest.raises(ValueError, match='forward_model'):
        integrate_model_over_bins(
            base_observation(),
            bin_centers,
            bin_edges,
            response_id='synthetic-tophat-v1',
            response_evidence='invalid attempt',
        )

