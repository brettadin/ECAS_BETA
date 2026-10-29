"""Production same-grid residual diagnostics for eligible comparison inputs.

No interpolation, unit conversion, baseline fitting, covariance estimation or
molecular detection significance is computed here. Every call re-runs the
eligibility gate first; blocked inputs raise IneligibleComparisonError and never
produce zero residuals or fallback scores.
"""
from dataclasses import dataclass

import numpy as np

from .eligibility import VERSION, Eligibility, assess


class IneligibleComparisonError(ValueError):
    """Raised when residual evaluation is requested for non-eligible inputs."""

    def __init__(self, eligibility: Eligibility):
        self.eligibility = eligibility
        reasons = ', '.join(eligibility.reasons) if eligibility.reasons else 'no reasons recorded'
        super().__init__(
            f'Comparison not eligible for {eligibility.operation} '
            f'({eligibility.status}): {reasons}'
        )


@dataclass(frozen=True)
class ResidualDiagnostic:
    version: str
    operation: str
    eligibility: Eligibility
    source_ids: tuple[str, str]
    source_sha256s: tuple[str, str]
    observable: str
    axis_unit: str
    signal_unit: str
    coordinate_frame: str
    response_id: str
    residual_convention: str
    coordinates: tuple[float, ...]
    left_values: tuple[float, ...]
    right_values: tuple[float, ...]
    residuals: tuple[float, ...]
    sample_count: int
    mean_residual: float
    mean_abs_residual: float
    rms_residual: float
    max_abs_residual: float
    whitened_residuals: tuple[float, ...] | None = None
    weighted_residual_quadratic: float | None = None
    demeaned_rms_residual: float = 0.0
    offset_dominates_shape: bool = False


def _covariance_matrix(item, n: int) -> np.ndarray:
    if item.noise_kind == 'deterministic_model':
        return np.zeros((n, n), dtype=float)
    if item.noise_kind == 'independent_gaussian_1sigma':
        sigma = np.asarray(item.sigma, dtype=float)
        with np.errstate(over='raise', invalid='raise'):
            return np.diag(sigma ** 2)
    if item.noise_kind == 'gaussian_covariance':
        return np.asarray(item.covariance, dtype=float)
    raise ValueError(f'Unsupported noise_kind: {item.noise_kind!r}')


def evaluate_residuals(
    left,
    right,
    *,
    weighted: bool = False,
    cross_dataset_independent: bool = False,
) -> ResidualDiagnostic:
    """Compute point-by-point residuals (left minus right) for eligible inputs only.

    Unweighted mode ('aligned_residual_v1') computes raw residuals and descriptive
    summaries in the shared signal unit. Weighted mode ('weighted_residual_v1')
    additionally computes Cholesky-whitened residuals L^-1 r and the fixed-covariance
    quadratic r^T (C_left + C_right)^-1 r. The quadratic omits log-determinant
    normalization and is not a calibrated detection significance or abundance metric.
    """
    eligibility = assess(
        left,
        right,
        weighted=weighted,
        cross_dataset_independent=cross_dataset_independent,
    )
    if eligibility.status != 'eligible':
        raise IneligibleComparisonError(eligibility)

    x = np.asarray(left.coordinates, dtype=float)
    y_left = np.asarray(left.values, dtype=float)
    y_right = np.asarray(right.values, dtype=float)
    with np.errstate(over='raise', invalid='raise'):
        diff = y_left - y_right
        abs_diff = np.abs(diff)
        mean_res = float(np.mean(diff))
        mean_abs_res = float(np.mean(abs_diff))
        rms_res = float(np.sqrt(np.mean(diff ** 2)))
        max_abs_res = float(np.max(abs_diff))
        centered = diff - mean_res
        demeaned_rms = float(np.sqrt(np.mean(centered ** 2)))
        offset_dominates = bool(abs(mean_res) > demeaned_rms and rms_res > 1e-12 and abs(mean_res) > 1e-12)

    whitened_tuple = None
    quadratic = None
    if weighted:
        n = len(x)
        with np.errstate(over='raise', invalid='raise'):
            combined = _covariance_matrix(left, n) + _covariance_matrix(right, n)
            chol = np.linalg.cholesky(combined)
            whitened = np.linalg.solve(chol, diff)
            quadratic = float(whitened @ whitened)
        if not np.isfinite(whitened).all() or not np.isfinite(quadratic):
            raise ValueError('Nonfinite weighted residual result')
        whitened_tuple = tuple(float(v) for v in whitened)

    return ResidualDiagnostic(
        version=VERSION,
        operation=eligibility.operation,
        eligibility=eligibility,
        source_ids=(left.source_id, right.source_id),
        source_sha256s=(left.source_sha256, right.source_sha256),
        observable=left.observable,
        axis_unit=left.axis_unit,
        signal_unit=left.signal_unit,
        coordinate_frame=left.coordinate_frame,
        response_id=left.response_id,
        residual_convention='left_minus_right',
        coordinates=tuple(float(v) for v in x),
        left_values=tuple(float(v) for v in y_left),
        right_values=tuple(float(v) for v in y_right),
        residuals=tuple(float(v) for v in diff),
        sample_count=len(x),
        mean_residual=mean_res,
        mean_abs_residual=mean_abs_res,
        rms_residual=rms_res,
        max_abs_residual=max_abs_res,
        whitened_residuals=whitened_tuple,
        weighted_residual_quadratic=quadratic,
        demeaned_rms_residual=demeaned_rms,
        offset_dominates_shape=offset_dominates,
    )

