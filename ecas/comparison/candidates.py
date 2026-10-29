"""Multi-candidate comparison evaluation with explicit fair-ranking guards.

Evaluates one target ComparisonInput against one or more candidate inputs using
the same grid, observable, units, coordinate frame, and instrument response.
Blocked candidates are retained with full Eligibility reasons rather than
dropped silently. Numerical ordering is permitted only when all eligible
candidates share identical evaluation conditions (including identical combined
covariance in weighted mode), preserves exact ties, and never claims model
adequacy, statistical significance, molecular identification, or abundance.
"""
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .eligibility import VERSION, ComparisonInput, Eligibility, assess
from .residuals import ResidualDiagnostic, _covariance_matrix, evaluate_residuals

TIE_ATOL = 1e-12

LIMITATIONS_UNWEIGHTED = (
    'Numerical closeness on this diagnostic does not establish model adequacy, '
    'statistical detection significance, molecular presence, or atmospheric abundance.',
    'Candidate ordering applies only within the supplied candidate set and shared '
    'spectral support; unmodelled species or continuum effects can alter agreement.',
)

LIMITATIONS_WEIGHTED = LIMITATIONS_UNWEIGHTED + (
    'Fixed-covariance quadratic omits Gaussian log-determinant normalization and '
    'is not a calibrated p-value or Bayesian evidence.',
)


@dataclass(frozen=True)
class CandidateAssessment:
    candidate_index: int
    source_id: str
    source_sha256: str | None
    eligibility: Eligibility
    diagnostic: ResidualDiagnostic | None


@dataclass(frozen=True)
class CandidateComparisonSummary:
    version: str
    operation: str
    target_source_id: str
    target_source_sha256: str | None
    candidates: tuple[CandidateAssessment, ...]
    eligible_indices: tuple[int, ...]
    blocked_indices: tuple[int, ...]
    ranking_metric: str | None
    fair_ranking_permitted: bool
    ranking_block_reasons: tuple[str, ...]
    ordered_eligible_indices: tuple[int, ...]
    closest_candidate_indices: tuple[int, ...]
    limitations: tuple[str, ...]


def evaluate_candidates(
    target: ComparisonInput,
    candidates: Sequence[ComparisonInput],
    *,
    weighted: bool = False,
    cross_dataset_independent: bool = False,
) -> CandidateComparisonSummary:
    """Assess and evaluate multiple candidates against a single target input.

    Fair ranking requires at least one eligible candidate and, in weighted mode,
    identical combined covariance matrices across all eligible candidates so that
    omitted Gaussian log-determinant terms cannot bias candidate ordering.
    """
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)) or len(candidates) == 0:
        raise ValueError('Require a nonempty sequence of ComparisonInput candidates')

    operation = 'weighted_residual_v1' if weighted else 'aligned_residual_v1'
    assessments: list[CandidateAssessment] = []
    eligible_indices: list[int] = []
    blocked_indices: list[int] = []
    combined_covariances: list[np.ndarray] = []

    for idx, candidate in enumerate(candidates):
        eligibility = assess(
            target,
            candidate,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
        )
        diagnostic = None
        if eligibility.status == 'eligible':
            diagnostic = evaluate_residuals(
                target,
                candidate,
                weighted=weighted,
                cross_dataset_independent=cross_dataset_independent,
            )
            eligible_indices.append(idx)
            if weighted:
                n = diagnostic.sample_count
                combined_covariances.append(
                    _covariance_matrix(target, n) + _covariance_matrix(candidate, n)
                )
        else:
            blocked_indices.append(idx)

        assessments.append(
            CandidateAssessment(
                candidate_index=idx,
                source_id=candidate.source_id,
                source_sha256=candidate.source_sha256,
                eligibility=eligibility,
                diagnostic=diagnostic,
            )
        )

    ranking_block_reasons: list[str] = []
    if not eligible_indices:
        ranking_block_reasons.append('candidates.none_eligible')
    elif weighted and len(combined_covariances) > 1:
        first_cov = combined_covariances[0]
        if any(
            cov.shape != first_cov.shape or not np.allclose(cov, first_cov, rtol=1e-12, atol=0)
            for cov in combined_covariances[1:]
        ):
            ranking_block_reasons.append(
                'candidates.combined_covariance.differs_across_candidates'
            )

    fair_ranking = len(ranking_block_reasons) == 0
    metric_name = None
    ordered: tuple[int, ...] = ()
    closest: tuple[int, ...] = ()

    if fair_ranking:
        metric_name = 'weighted_residual_quadratic' if weighted else 'rms_residual'

        def _metric(i: int) -> float:
            diag = assessments[i].diagnostic
            assert diag is not None
            val = diag.weighted_residual_quadratic if weighted else diag.rms_residual
            assert val is not None
            return val

        sorted_indices = sorted(eligible_indices, key=lambda i: (_metric(i), i))
        ordered = tuple(sorted_indices)
        best_val = _metric(sorted_indices[0])
        closest = tuple(
            i for i in sorted_indices if abs(_metric(i) - best_val) <= TIE_ATOL
        )

    return CandidateComparisonSummary(
        version=VERSION,
        operation=operation,
        target_source_id=target.source_id,
        target_source_sha256=target.source_sha256,
        candidates=tuple(assessments),
        eligible_indices=tuple(eligible_indices),
        blocked_indices=tuple(blocked_indices),
        ranking_metric=metric_name,
        fair_ranking_permitted=fair_ranking,
        ranking_block_reasons=tuple(ranking_block_reasons),
        ordered_eligible_indices=ordered,
        closest_candidate_indices=closest,
        limitations=LIMITATIONS_WEIGHTED if weighted else LIMITATIONS_UNWEIGHTED,
    )

