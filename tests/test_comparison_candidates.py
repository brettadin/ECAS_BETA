"""Tests for multi-candidate comparison, fair-ranking guards, and tie preservation."""
from dataclasses import replace
from pathlib import Path

import pytest

from ecas.comparison.candidates import evaluate_candidates
from ecas.comparison.eligibility import ComparisonInput
from ecas.comparison.inputs import reference_input
from ecas.ingestion.exomol_product import ProductRequest, validate_product
from ecas.ingestion.exomol_product_network import RetrievedCrossSection

ROOT = Path(__file__).resolve().parents[1]


def synthetic_target():
    return ComparisonInput(
        source_id='synthetic-target',
        source_sha256='a' * 64,
        role='observation',
        observable='transit_depth',
        axis_unit='microns',
        signal_unit='percent',
        coordinate_frame='barycentric-synthetic',
        response_id='synthetic-tophat-v1',
        response_evidence='synthetic test response declaration',
        coordinates=(1.0, 2.0, 3.0, 4.0),
        values=(2.0, 2.2, 2.0, 2.1),
        noise_kind='independent_gaussian_1sigma',
        noise_evidence='synthetic independent 1-sigma errors',
        sigma=(0.1, 0.1, 0.1, 0.1),
    )


def synthetic_candidate(name: str, sha_char: str, values: tuple[float, ...]):
    return replace(
        synthetic_target(),
        source_id=name,
        source_sha256=sha_char * 64,
        role='forward_model',
        values=values,
        noise_kind='deterministic_model',
        noise_evidence='synthetic deterministic model',
        sigma=None,
    )


def test_mixed_eligible_and_blocked_candidates_preserve_reasons_and_order():
    target = synthetic_target()
    cand_far = synthetic_candidate('model-far', 'b', (2.0, 2.5, 2.0, 2.5))
    cand_close = synthetic_candidate('model-close', 'c', (2.0, 2.21, 2.0, 2.09))

    request = ProductRequest(4000, 4010, 500, '1')
    raw = (ROOT / 'data/ExoMol/2026-10-28/CO2-12C-16O2-500K-4000-4010-dnu1.sigma').read_bytes()
    raw_cross_section = reference_input(
        RetrievedCrossSection(request, raw, validate_product(raw, request))
    ).comparison_input

    summary = evaluate_candidates(target, (cand_far, raw_cross_section, cand_close))

    assert summary.eligible_indices == (0, 2)
    assert summary.blocked_indices == (1,)
    assert summary.fair_ranking_permitted is True
    assert summary.ranking_metric == 'rms_residual'
    assert summary.ordered_eligible_indices == (2, 0)
    assert summary.closest_candidate_indices == (2,)
    assert summary.candidates[1].diagnostic is None
    assert 'right.role.requires_physical_model_or_supported_role' in summary.candidates[1].eligibility.reasons
    assert any('not establish model adequacy' in text for text in summary.limitations)


def test_overlapping_tied_candidates_preserve_ambiguity():
    target = synthetic_target()
    # Opposite-sign residuals of identical magnitude produce identical RMS and Q
    cand_plus = synthetic_candidate('species-alpha-synthetic', 'b', (2.0, 2.3, 2.0, 2.1))
    cand_minus = synthetic_candidate('species-beta-synthetic', 'c', (2.0, 2.1, 2.0, 2.1))

    unweighted = evaluate_candidates(target, (cand_plus, cand_minus))
    assert unweighted.fair_ranking_permitted is True
    assert unweighted.closest_candidate_indices == (0, 1)

    weighted = evaluate_candidates(
        target, (cand_plus, cand_minus), weighted=True, cross_dataset_independent=True
    )
    assert weighted.fair_ranking_permitted is True
    assert weighted.ranking_metric == 'weighted_residual_quadratic'
    assert weighted.closest_candidate_indices == (0, 1)
    assert any('log-determinant normalization' in text for text in weighted.limitations)


def test_weighted_candidates_with_different_noise_covariances_block_unfair_ranking():
    target = synthetic_target()
    deterministic = synthetic_candidate('deterministic-candidate', 'b', (2.0, 2.5, 2.0, 2.5))
    noisy_ref = replace(
        deterministic,
        source_id='noisy-reference-measurement',
        source_sha256='d' * 64,
        role='reference_measurement',
        noise_kind='independent_gaussian_1sigma',
        noise_evidence='synthetic noisy reference',
        sigma=(1.0, 1.0, 1.0, 1.0),  # Larger variance shrinks raw Q artificially
    )

    summary = evaluate_candidates(
        target, (deterministic, noisy_ref), weighted=True, cross_dataset_independent=True
    )
    # Individual diagnostics remain inspectable, but cross-candidate ranking is refused
    assert summary.eligible_indices == (0, 1)
    assert summary.candidates[0].diagnostic is not None
    assert summary.candidates[1].diagnostic is not None
    assert summary.fair_ranking_permitted is False
    assert 'candidates.combined_covariance.differs_across_candidates' in summary.ranking_block_reasons
    assert summary.ordered_eligible_indices == ()
    assert summary.closest_candidate_indices == ()
    assert summary.ranking_metric is None


def test_all_blocked_candidates_and_invalid_sequence_handling():
    target = synthetic_target()
    unaligned = replace(
        synthetic_candidate('unaligned', 'b', (2.0, 2.2, 2.0, 2.1)),
        coordinates=(1.0, 2.0, 3.0, 4.5),
    )
    summary = evaluate_candidates(target, (unaligned,))
    assert summary.eligible_indices == ()
    assert summary.blocked_indices == (0,)
    assert summary.fair_ranking_permitted is False
    assert summary.ranking_block_reasons == ('candidates.none_eligible',)
    assert summary.ordered_eligible_indices == ()
    assert summary.closest_candidate_indices == ()

    with pytest.raises(ValueError):
        evaluate_candidates(target, ())
    with pytest.raises(ValueError):
        evaluate_candidates(target, 'not-a-sequence-of-inputs')

