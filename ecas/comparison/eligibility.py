"""Production eligibility service for already-aligned curves (contract v1).

Deliberate port of the reviewed research contract in docs/Chunk_5/eligibility_contract.py;
the research script is not imported. Evidence strings are caller attestations, not
verification of a remote source or physical accuracy. No interpolation, conversion,
error inference or scoring: this service only reports whether a named diagnostic
could be considered and why it cannot.
"""
from dataclasses import dataclass
import re

import numpy as np

VERSION = 'ecas-comparison-eligibility-v1'


@dataclass(frozen=True)
class ComparisonInput:
    source_id: str
    source_sha256: str
    role: str | None
    observable: str | None
    axis_unit: str | None
    signal_unit: str | None
    coordinate_frame: str | None
    response_id: str | None
    response_evidence: str | None
    coordinates: tuple
    values: tuple
    noise_kind: str | None = None
    noise_evidence: str | None = None
    sigma: tuple | None = None
    covariance: tuple | None = None


@dataclass(frozen=True)
class Eligibility:
    version: str
    operation: str
    status: str
    reasons: tuple[str, ...]
    source_ids: tuple[str, str]


def assess(left, right, *, weighted=False, cross_dataset_independent=False):
    """Assess only same-grid residual diagnostics, never detection significance.

    Weighted mode uses combined uncertainty C_left+C_right, requiring an explicit
    cross-dataset independence declaration. Deterministic models require explicit
    evidence and contribute zero variance. Covariance is checked, not estimated.
    Returns all detected reasons; blocked results never become score zero.
    """
    missing, incompatible = [], []
    arrays, covariances = [], []

    def nonempty(value):
        return isinstance(value, str) and bool(value.strip())

    for label, item in (('left', left), ('right', right)):
        for field in ('source_id', 'role', 'observable', 'axis_unit', 'signal_unit',
                      'coordinate_frame', 'response_id', 'response_evidence'):
            if not nonempty(getattr(item, field)):
                missing.append(f'{label}.{field}.missing')
        if not isinstance(item.source_sha256, str) or not re.fullmatch('[0-9a-fA-F]{64}', item.source_sha256):
            missing.append(f'{label}.source_sha256.missing_or_invalid')
        if nonempty(item.role) and item.role not in ('observation', 'forward_model', 'reference_measurement'):
            incompatible.append(f'{label}.role.requires_physical_model_or_supported_role')
        if nonempty(item.observable) and item.observable != 'transit_depth':
            incompatible.append(f'{label}.observable.unsupported_in_v1')
        if nonempty(item.axis_unit) and item.axis_unit != 'microns':
            incompatible.append(f'{label}.axis_unit.explicit_conversion_required')
        if nonempty(item.signal_unit) and item.signal_unit not in ('percent', 'fraction'):
            incompatible.append(f'{label}.signal_unit.unsupported_in_v1')
        try:
            x, y = np.asarray(item.coordinates, dtype=float), np.asarray(item.values, dtype=float)
            if x.ndim != 1 or y.ndim != 1 or len(x) < 3 or len(x) != len(y):
                raise ValueError('shape')
            if not np.isfinite(x).all() or not np.isfinite(y).all() or not np.all(np.diff(x) > 0):
                raise ValueError('values')
            arrays.append((x, y))
        except (TypeError, ValueError):
            arrays.append(None)
            incompatible.append(f'{label}.measurements.invalid_or_incomplete')
        if not weighted:
            continue
        if not nonempty(item.noise_evidence):
            missing.append(f'{label}.noise_evidence.missing')
        covariance = None
        n = len(arrays[-1][0]) if arrays[-1] is not None else 0
        try:
            if item.noise_kind == 'deterministic_model':
                if item.role != 'forward_model' or item.sigma is not None or item.covariance is not None:
                    raise ValueError('deterministic declaration')
                covariance = np.zeros((n, n))
            elif item.noise_kind == 'independent_gaussian_1sigma':
                if item.sigma is None or item.covariance is not None:
                    raise ValueError('explicit sigma required, no conflicting covariance')
                sigma = np.asarray(item.sigma, dtype=float)
                if sigma.shape != (n,) or not np.isfinite(sigma).all() or np.any(sigma <= 0):
                    raise ValueError('sigma')
                with np.errstate(over='raise', invalid='raise'):
                    covariance = np.diag(sigma**2)
            elif item.noise_kind == 'gaussian_covariance':
                if item.covariance is None or item.sigma is not None:
                    raise ValueError('explicit covariance required, no conflicting sigma')
                covariance = np.asarray(item.covariance, dtype=float)
                if covariance.shape != (n, n) or not np.isfinite(covariance).all():
                    raise ValueError('covariance shape/values')
                if not np.allclose(covariance, covariance.T, rtol=1e-12, atol=0):
                    raise ValueError('covariance symmetry')
                np.linalg.cholesky(covariance)
                if n > 0 and float(np.linalg.cond(covariance)) > 1e12:
                    raise ValueError('ill_conditioned')
            elif item.noise_kind is None:
                missing.append(f'{label}.noise_kind.missing')
            else:
                incompatible.append(f'{label}.noise_kind.unsupported_or_asymmetric')
        except (TypeError, ValueError, FloatingPointError, np.linalg.LinAlgError) as err:
            covariance = None
            if str(err) == 'ill_conditioned':
                incompatible.append(f'{label}.noise.ill_conditioned')
            else:
                incompatible.append(f'{label}.noise.invalid')
        covariances.append(covariance)

    for field in ('observable', 'axis_unit', 'signal_unit', 'coordinate_frame', 'response_id'):
        if nonempty(getattr(left, field)) and nonempty(getattr(right, field)) and getattr(left, field) != getattr(right, field):
            incompatible.append(f'pair.{field}.mismatch_explicit_transformation_required')
    if all(array is not None for array in arrays):
        x_left, x_right = arrays[0][0], arrays[1][0]
        if not np.array_equal(x_left, x_right):
            incompatible.append('pair.coordinates.not_exactly_aligned')
        if max(x_left[0], x_right[0]) > min(x_left[-1], x_right[-1]):
            incompatible.append('pair.coverage.no_overlap')
    if weighted:
        if not cross_dataset_independent:
            missing.append('pair.cross_dataset_independence.not_declared')
        if left.source_sha256 == right.source_sha256 and left.noise_kind != 'deterministic_model' and right.noise_kind != 'deterministic_model':
            incompatible.append('pair.same_source.cannot_assume_independence')
        if len(covariances) == 2 and all(c is not None for c in covariances) and covariances[0].shape == covariances[1].shape:
            try:
                with np.errstate(over='raise', invalid='raise'):
                    combined = covariances[0]+covariances[1]
                if not np.isfinite(combined).all():
                    raise ValueError('nonfinite covariance')
                if n > 0 and float(np.linalg.cond(combined)) > 1e12:
                    incompatible.append('pair.combined_covariance.ill_conditioned')
                else:
                    np.linalg.cholesky(combined)
            except (ValueError, FloatingPointError, np.linalg.LinAlgError):
                incompatible.append('pair.combined_covariance.not_positive_definite')
    status = 'incompatible' if incompatible else 'missing_requirements' if missing else 'eligible'
    return Eligibility(VERSION, 'weighted_residual_v1' if weighted else 'aligned_residual_v1',
                       status, tuple(missing+incompatible), (left.source_id, right.source_id))


_MEANING = {
    ('source_sha256', 'missing_or_invalid'): 'raw source SHA-256 is not established or is invalid',
    ('role', 'requires_physical_model_or_supported_role'):
        'role is not a supported comparison role; an explicit physical model is needed first',
    ('observable', 'unsupported_in_v1'): 'observable is not supported by v1 (transit_depth only)',
    ('axis_unit', 'explicit_conversion_required'): 'axis unit is not microns; v1 performs no conversion',
    ('signal_unit', 'unsupported_in_v1'): 'signal unit is not percent or fraction; v1 performs no conversion',
    ('measurements', 'invalid_or_incomplete'):
        'measurements need at least three finite, strictly increasing coordinates with matching values',
    ('noise_evidence', 'missing'): 'noise evidence is not established',
    ('noise_kind', 'missing'): 'noise kind is not established',
    ('noise_kind', 'unsupported_or_asymmetric'): 'noise kind is unsupported or asymmetric',
    ('noise', 'invalid'): 'noise declaration is invalid',
    ('noise', 'ill_conditioned'): 'covariance matrix is ill-conditioned (condition number exceeds 1e12; numerically unstable)',
}
_PAIR_MEANING = {
    ('coordinates', 'not_exactly_aligned'):
        'coordinates differ as supplied (no unit conversion), which is not meaningful while axis units differ',
    ('coverage', 'no_overlap'):
        'coordinate ranges do not overlap as supplied (no unit conversion), which is not meaningful while axis units differ',
    ('cross_dataset_independence', 'not_declared'): 'cross-dataset independence is not declared',
    ('same_source', 'cannot_assume_independence'): 'both inputs share one source; independence cannot be assumed',
    ('combined_covariance', 'not_positive_definite'): 'combined covariance is not positive definite',
    ('combined_covariance', 'ill_conditioned'): 'combined covariance matrix is ill-conditioned (condition number exceeds 1e12; numerically unstable)',
}


def describe_reason(code, left='left input', right='right input'):
    """Plain-language meaning of a machine-readable reason; unknown codes pass through."""
    parts = code.split('.', 2)
    if len(parts) != 3:
        return code
    side, field, kind = parts
    if side == 'pair':
        if (field, kind) in _PAIR_MEANING:
            return f'{left} / {right}: {_PAIR_MEANING[(field, kind)]}'
        if kind == 'mismatch_explicit_transformation_required':
            return f'{left} / {right}: {field.replace("_", " ")} differs; an explicit transformation is required'
        return code
    subject = {'left': left, 'right': right}.get(side)
    if subject is None:
        return code
    if kind == 'missing' and (field, kind) not in _MEANING:
        return f'{subject}: {field.replace("_", " ")} is not established; ECAS does not infer it'
    text = _MEANING.get((field, kind))
    return f'{subject}: {text}' if text else code
