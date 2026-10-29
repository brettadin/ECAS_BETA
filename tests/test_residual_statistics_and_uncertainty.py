"""Formal statistical validation suite for residuals, uncertainties, covariance, and scientific interpretation boundaries.

Enforces Priority 4 requirements from the architecture review (Section 8):
1. Representation, conversion, and validation of uncertainty structures.
2. Distinction between variance, standard deviation, and covariance.
3. Dimension, shape, symmetry, and positive-definiteness enforcement.
4. Detection and rejection of singular or ill-conditioned covariance matrices (cond > 1e12).
5. Cross-dataset error independence attestations.
6. Mathematical correctness of Cholesky whitening and reduced chi-squared statistics.
7. Fair candidate ranking guards and preservation of exact ties.
8. Strict adherence to scientific claim boundaries (no detection/abundance claims).
"""

from dataclasses import replace
import math
import numpy as np
import pytest

from ecas.comparison.candidates import evaluate_candidates
from ecas.comparison.eligibility import ComparisonInput, assess, describe_reason
from ecas.comparison.residuals import (
    IneligibleComparisonError,
    _covariance_matrix,
    evaluate_residuals,
)


def make_obs(
    coords=(1.0, 2.0, 3.0, 4.0),
    vals=(2.1, 2.2, 2.0, 2.3),
    sigma=(0.05, 0.05, 0.05, 0.05),
    covariance=None,
    noise_kind="independent_gaussian_1sigma",
    axis_unit="microns",
    signal_unit="percent",
    source_id="test-obs",
    source_sha="1" * 64,
):
    return ComparisonInput(
        source_id=source_id,
        source_sha256=source_sha,
        role="observation",
        observable="transit_depth",
        axis_unit=axis_unit,
        signal_unit=signal_unit,
        coordinate_frame="barycentric",
        response_id="test-tophat-passband",
        response_evidence="top-hat passband",
        coordinates=coords,
        values=vals,
        noise_kind=noise_kind,
        noise_evidence="statistical test uncertainty declaration",
        sigma=sigma,
        covariance=covariance,
    )


def make_model(
    coords=(1.0, 2.0, 3.0, 4.0),
    vals=(2.0, 2.0, 2.0, 2.0),
    source_id="test-model",
    source_sha="2" * 64,
    signal_unit="percent",
    noise_kind="deterministic_model",
    sigma=None,
    covariance=None,
):
    return ComparisonInput(
        source_id=source_id,
        source_sha256=source_sha,
        role="forward_model",
        observable="transit_depth",
        axis_unit="microns",
        signal_unit=signal_unit,
        coordinate_frame="barycentric",
        response_id="test-tophat-passband",
        response_evidence="top-hat passband",
        coordinates=coords,
        values=vals,
        noise_kind=noise_kind,
        noise_evidence="forward model deterministic declaration",
        sigma=sigma,
        covariance=covariance,
    )


def test_uncertainty_representation_and_conversions():
    """Verify conversion of independent 1-sigma, deterministic models, and covariance matrices."""
    obs = make_obs(sigma=(0.1, 0.2, 0.3, 0.4))
    cov_diag = _covariance_matrix(obs, 4)
    expected_diag = np.diag([0.01, 0.04, 0.09, 0.16])
    assert np.allclose(cov_diag, expected_diag, rtol=0, atol=1e-15)

    model = make_model()
    cov_zero = _covariance_matrix(model, 4)
    assert cov_zero.shape == (4, 4)
    assert np.all(cov_zero == 0.0)

    dense_cov = (
        (0.04, 0.01, 0.00, 0.00),
        (0.01, 0.04, 0.01, 0.00),
        (0.00, 0.01, 0.04, 0.01),
        (0.00, 0.00, 0.01, 0.04),
    )
    obs_dense = make_obs(noise_kind="gaussian_covariance", sigma=None, covariance=dense_cov)
    cov_out = _covariance_matrix(obs_dense, 4)
    assert np.allclose(cov_out, dense_cov, rtol=0, atol=1e-15)


def test_missing_and_nonfinite_uncertainty_guards():
    """Verify zero, negative, missing, and nonfinite uncertainties are strictly blocked."""
    model = make_model()

    # 1. Missing noise_kind
    no_kind = replace(make_obs(), noise_kind=None)
    elig = assess(no_kind, model, weighted=True, cross_dataset_independent=True)
    assert elig.status != "eligible"
    assert "left.noise_kind.missing" in elig.reasons

    # 2. Zero uncertainty (variance = 0 is non-invertible)
    zero_sigma = replace(make_obs(), sigma=(0.05, 0.0, 0.05, 0.05))
    elig = assess(zero_sigma, model, weighted=True, cross_dataset_independent=True)
    assert elig.status != "eligible"
    assert "left.noise.invalid" in elig.reasons

    # 3. Negative uncertainty (physically unphysical)
    neg_sigma = replace(make_obs(), sigma=(0.05, -0.01, 0.05, 0.05))
    elig = assess(neg_sigma, model, weighted=True, cross_dataset_independent=True)
    assert elig.status != "eligible"
    assert "left.noise.invalid" in elig.reasons

    # 4. Nonfinite uncertainty (inf, nan)
    inf_sigma = replace(make_obs(), sigma=(0.05, float("inf"), 0.05, 0.05))
    elig = assess(inf_sigma, model, weighted=True, cross_dataset_independent=True)
    assert elig.status != "eligible"
    assert "left.noise.invalid" in elig.reasons

    nan_sigma = replace(make_obs(), sigma=(0.05, float("nan"), 0.05, 0.05))
    elig = assess(nan_sigma, model, weighted=True, cross_dataset_independent=True)
    assert elig.status != "eligible"
    assert "left.noise.invalid" in elig.reasons


def test_uncertainty_dimension_and_shape_validation():
    """Verify incorrect uncertainty lengths or covariance dimensions are rejected."""
    model = make_model()

    # 1. sigma length != coordinates count
    short_sigma = replace(make_obs(), sigma=(0.05, 0.05, 0.05))
    elig = assess(short_sigma, model, weighted=True, cross_dataset_independent=True)
    assert elig.status != "eligible"
    assert "left.noise.invalid" in elig.reasons

    # 2. Covariance matrix shape not (N, N)
    rect_cov = ((0.04, 0.01), (0.01, 0.04), (0.0, 0.01), (0.0, 0.0))
    non_sq = replace(make_obs(), noise_kind="gaussian_covariance", sigma=None, covariance=rect_cov)
    elig = assess(non_sq, model, weighted=True, cross_dataset_independent=True)
    assert elig.status != "eligible"
    assert "left.noise.invalid" in elig.reasons


def test_incompatible_units_and_observables_boundaries():
    """Verify comparisons across mismatched units or observables are blocked without fallback scores."""
    # 1. Mismatched signal units (percent vs fraction)
    obs_pct = make_obs(signal_unit="percent")
    model_frac = make_model(signal_unit="fraction")
    elig = assess(obs_pct, model_frac)
    assert elig.status == "incompatible"
    assert "pair.signal_unit.mismatch_explicit_transformation_required" in elig.reasons

    # 2. Unsupported axis unit
    obs_nm = replace(obs_pct, axis_unit="nanometers")
    model_um = make_model(coords=(1.0, 2.0, 3.0, 4.0))
    elig = assess(obs_nm, model_um)
    assert elig.status == "incompatible"
    assert "left.axis_unit.explicit_conversion_required" in elig.reasons


def test_covariance_matrix_symmetry_and_positive_definiteness():
    """Verify asymmetric, singular, and negative-eigenvalue covariance matrices are rejected."""
    model = make_model()

    # 1. Asymmetric covariance matrix
    asym_cov = (
        (0.04, 0.02, 0.00, 0.00),
        (0.01, 0.04, 0.00, 0.00),  # 0.01 != 0.02
        (0.00, 0.00, 0.04, 0.00),
        (0.00, 0.00, 0.00, 0.04),
    )
    obs_asym = make_obs(noise_kind="gaussian_covariance", sigma=None, covariance=asym_cov)
    elig = assess(obs_asym, model, weighted=True, cross_dataset_independent=True)
    assert elig.status != "eligible"
    assert "left.noise.invalid" in elig.reasons

    # 2. Singular (rank-deficient) covariance matrix
    sing_cov = (
        (0.04, 0.04, 0.00, 0.00),
        (0.04, 0.04, 0.00, 0.00),  # Col 1 == Col 2 => rank deficient, det = 0
        (0.00, 0.00, 0.04, 0.00),
        (0.00, 0.00, 0.00, 0.04),
    )
    obs_sing = make_obs(noise_kind="gaussian_covariance", sigma=None, covariance=sing_cov)
    elig = assess(obs_sing, model, weighted=True, cross_dataset_independent=True)
    assert elig.status != "eligible"
    assert "left.noise.invalid" in elig.reasons


def test_ill_conditioned_covariance_matrix_rejection():
    """Verify ill-conditioned covariance matrices (condition number > 1e12) are blocked as numerically unstable."""
    model = make_model()

    # Condition number = 1.0 / 1e-13 = 1e13 > 1e12
    ill_cov = (
        (1.0, 0.0, 0.0, 0.0),
        (0.0, 1e-13, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 1.0),
    )
    obs_ill = make_obs(noise_kind="gaussian_covariance", sigma=None, covariance=ill_cov)
    elig = assess(obs_ill, model, weighted=True, cross_dataset_independent=True)
    assert elig.status == "incompatible"
    assert "left.noise.ill_conditioned" in elig.reasons
    desc = describe_reason("left.noise.ill_conditioned")
    assert "condition number exceeds 1e12" in desc

    # Combined covariance ill-conditioned
    obs_mod = replace(
        model,
        role="reference_measurement",
        noise_kind="gaussian_covariance",
        noise_evidence="reference covariance declaration",
        covariance=ill_cov,
    )
    elig_comb = assess(make_obs(), obs_mod, weighted=True, cross_dataset_independent=True)
    assert elig_comb.status == "incompatible"
    assert "right.noise.ill_conditioned" in elig_comb.reasons


def test_cross_dataset_independence_and_self_comparison_guards():
    """Verify cross-dataset error independence is strictly enforced in weighted mode."""
    obs = make_obs()
    model = make_model()

    # 1. Cross-dataset independence not declared
    elig = assess(obs, model, weighted=True, cross_dataset_independent=False)
    assert elig.status != "eligible"
    assert "pair.cross_dataset_independence.not_declared" in elig.reasons

    # 2. Comparing an observation to itself (identical sha256) cannot assume independence
    obs_stoch = replace(obs, source_id="obs-duplicate")
    elig_self = assess(obs, obs_stoch, weighted=True, cross_dataset_independent=True)
    assert elig_self.status == "incompatible"
    assert "pair.same_source.cannot_assume_independence" in elig_self.reasons


def test_weighted_whitening_quadratic_and_reduced_chi2_mathematics():
    """Verify numerical exactness of Cholesky whitening and reduced chi-squared statistic."""
    # Observations: values = (2.1, 2.2, 2.0, 2.3), sigma = (0.1, 0.1, 0.1, 0.1)
    # Model: values = (2.0, 2.0, 2.0, 2.0)
    # Residuals diff: (+0.1, +0.2, 0.0, +0.3)
    # Whitened residuals: diff / sigma = (+1.0, +2.0, 0.0, +3.0)
    # Weighted quadratic q = 1^2 + 2^2 + 0^2 + 3^2 = 14.0
    # Sample count N = 4 => reduced quadratic q / N = 14.0 / 4 = 3.5
    obs = make_obs(vals=(2.1, 2.2, 2.0, 2.3), sigma=(0.1, 0.1, 0.1, 0.1))
    model = make_model(vals=(2.0, 2.0, 2.0, 2.0))

    diag = evaluate_residuals(obs, model, weighted=True, cross_dataset_independent=True)
    assert diag.sample_count == 4
    assert np.allclose(diag.residuals, (0.1, 0.2, 0.0, 0.3), rtol=0, atol=1e-15)
    assert np.allclose(diag.whitened_residuals, (1.0, 2.0, 0.0, 3.0), rtol=0, atol=1e-14)
    assert math.isclose(diag.weighted_residual_quadratic, 14.0, rel_tol=0, abs_tol=1e-14)
    assert math.isclose(diag.reduced_weighted_quadratic, 3.5, rel_tol=0, abs_tol=1e-14)

    # Offset detection: mean residual = +0.15
    # Centered diff = (-0.05, +0.05, -0.15, +0.15)
    # De-meaned RMS = sqrt((0.0025 + 0.0025 + 0.0225 + 0.0225) / 4) = sqrt(0.0500 / 4) = sqrt(0.0125) approx 0.1118
    # |mean residual| = 0.15 > de-meaned RMS (0.1118) => offset_dominates_shape is True
    assert math.isclose(diag.mean_residual, 0.15, rel_tol=0, abs_tol=1e-15)
    assert math.isclose(diag.demeaned_rms_residual, math.sqrt(0.0125), rel_tol=1e-12, abs_tol=1e-15)
    assert diag.offset_dominates_shape is True


def test_candidate_ranking_covariance_fairness_and_scientific_claims():
    """Verify fair candidate ranking requires identical combined covariance and enforces claim boundaries."""
    obs = make_obs(vals=(2.1, 2.2, 2.0, 2.3), sigma=(0.1, 0.1, 0.1, 0.1))

    # Candidate 1: close model
    mod1 = make_model(vals=(2.1, 2.2, 2.0, 2.3), source_id="candidate-perfect")
    # Candidate 2: offset model
    mod2 = make_model(vals=(2.0, 2.0, 2.0, 2.0), source_id="candidate-offset")
    # Candidate 3: tied model with candidate 2 (same quadratic = 14.0)
    mod3 = make_model(vals=(2.2, 2.4, 2.0, 2.6), source_id="candidate-tied")

    summary = evaluate_candidates(
        obs,
        (mod1, mod2, mod3),
        weighted=True,
        cross_dataset_independent=True,
    )
    assert summary.fair_ranking_permitted is True
    assert summary.ordered_eligible_indices == (0, 1, 2)
    assert summary.closest_candidate_indices == (0,)

    # Test exact tie preservation between mod2 and mod3 alone
    tie_summary = evaluate_candidates(
        obs,
        (mod2, mod3),
        weighted=True,
        cross_dataset_independent=True,
    )
    assert tie_summary.fair_ranking_permitted is True
    assert len(tie_summary.closest_candidate_indices) == 2
    assert tie_summary.closest_candidate_indices == (0, 1)

    # When candidates have differing noise covariance (e.g. stochastically generated reference candidates),
    # fair ranking by quadratic is strictly blocked because omitted log-det terms would bias candidate ordering
    stoch_mod = replace(
        mod1,
        role="reference_measurement",
        noise_kind="independent_gaussian_1sigma",
        noise_evidence="candidate 1-sigma error",
        sigma=(0.02, 0.02, 0.02, 0.02),
    )
    diff_cov_summary = evaluate_candidates(
        obs,
        (mod1, stoch_mod),
        weighted=True,
        cross_dataset_independent=True,
    )
    assert diff_cov_summary.fair_ranking_permitted is False
    assert "candidates.combined_covariance.differs_across_candidates" in diff_cov_summary.ranking_block_reasons

    # Scientific limitations disclaimers are present
    for lim in summary.limitations:
        lim_lower = lim.lower()
        assert (
            "not establish model adequacy" in lim_lower
            or "candidate ordering applies only" in lim_lower
            or "omits gaussian log-determinant" in lim_lower
        )

