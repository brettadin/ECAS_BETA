"""Explicit, provenance-recorded alignment and unit transformations.

Nothing in this module runs implicitly inside assess() or evaluate_residuals().
Callers must invoke each transformation explicitly, preserving the immutable
original ComparisonInput alongside every TransformationStep, included index,
and excluded index. Observations are never upsampled, out-of-domain bins are
never extrapolated or silently clipped, and cross sections cannot be converted
into transit depth here.
"""
from collections.abc import Sequence
from dataclasses import dataclass, replace

import numpy as np

from .eligibility import ComparisonInput

_SIGNAL_FACTORS = {
    ('fraction', 'percent'): 100.0,
    ('percent', 'fraction'): 0.01,
    ('percent', 'percent'): 1.0,
    ('fraction', 'fraction'): 1.0,
    ('ppm', 'fraction'): 1e-6,
    ('ppm', 'percent'): 1e-4,
    ('fraction', 'ppm'): 1e6,
    ('percent', 'ppm'): 1e4,
    ('ppm', 'ppm'): 1.0,
}

_AXIS_FACTORS = {
    ('nanometers', 'microns'): 1e-3,
    ('nm', 'microns'): 1e-3,
    ('angstroms', 'microns'): 1e-4,
    ('angstrom', 'microns'): 1e-4,
    ('um', 'microns'): 1.0,
    ('microns', 'microns'): 1.0,
}


@dataclass(frozen=True)
class TransformationStep:
    operation: str
    parameters: tuple[tuple[str, object], ...]
    included_indices: tuple[int, ...]
    excluded_indices: tuple[int, ...]
    exclusion_reason: str | None = None


@dataclass(frozen=True)
class TransformedInput:
    original: ComparisonInput
    transformed: ComparisonInput
    steps: tuple[TransformationStep, ...]


def _unwrap(item: ComparisonInput | TransformedInput) -> tuple[ComparisonInput, ComparisonInput, tuple[TransformationStep, ...]]:
    if isinstance(item, TransformedInput):
        return item.original, item.transformed, item.steps
    if isinstance(item, ComparisonInput):
        return item, item, ()
    raise TypeError('Expected ComparisonInput or TransformedInput')


def convert_signal_unit(
    item: ComparisonInput | TransformedInput,
    target_unit: str,
) -> TransformedInput:
    """Explicitly scale transit-depth values, sigma, and covariance between fraction and percent."""
    original, current, prior_steps = _unwrap(item)
    key = (current.signal_unit, target_unit)
    if key not in _SIGNAL_FACTORS:
        raise ValueError(
            f'Unsupported signal unit conversion: {current.signal_unit!r} -> {target_unit!r}'
        )
    factor = _SIGNAL_FACTORS[key]
    values = np.asarray(current.values, dtype=float)
    if values.ndim != 1 or len(values) == 0 or not np.isfinite(values).all():
        raise ValueError('Signal conversion requires finite 1D values')

    with np.errstate(over='raise', invalid='raise'):
        scaled_values = tuple(float(v) for v in values * factor)
        scaled_sigma = None
        if current.sigma is not None:
            sigma = np.asarray(current.sigma, dtype=float)
            if sigma.shape != values.shape or not np.isfinite(sigma).all():
                raise ValueError('Signal conversion encountered invalid sigma array')
            scaled_sigma = tuple(float(v) for v in sigma * factor)
        scaled_cov = None
        if current.covariance is not None:
            cov = np.asarray(current.covariance, dtype=float)
            n = len(values)
            if cov.shape != (n, n) or not np.isfinite(cov).all():
                raise ValueError('Signal conversion encountered invalid covariance matrix')
            scaled_cov = tuple(
                tuple(float(v) for v in row) for row in (cov * (factor ** 2))
            )

    indices = tuple(range(len(values)))
    step = TransformationStep(
        operation='convert_signal_unit_v1',
        parameters=(
            ('from_unit', current.signal_unit),
            ('to_unit', target_unit),
            ('scale_factor', factor),
        ),
        included_indices=indices,
        excluded_indices=(),
    )
    updated = replace(
        current,
        signal_unit=target_unit,
        values=scaled_values,
        sigma=scaled_sigma,
        covariance=scaled_cov,
    )
    return TransformedInput(original=original, transformed=updated, steps=prior_steps + (step,))


def convert_axis_unit(
    item: ComparisonInput | TransformedInput,
    target_unit: str = 'microns',
) -> TransformedInput:
    """Explicitly convert positive wavelength coordinates (nm, angstroms) to microns."""
    original, current, prior_steps = _unwrap(item)
    key = (current.axis_unit, target_unit)
    if key not in _AXIS_FACTORS:
        raise ValueError(
            f'Unsupported axis unit conversion: {current.axis_unit!r} -> {target_unit!r}'
        )
    factor = _AXIS_FACTORS[key]
    coords = np.asarray(current.coordinates, dtype=float)
    if coords.ndim != 1 or len(coords) < 3 or not np.isfinite(coords).all() or np.any(coords <= 0):
        raise ValueError('Wavelength conversion requires at least 3 positive finite coordinates')
    if not np.all(np.diff(coords) > 0):
        raise ValueError('Wavelength conversion requires strictly increasing coordinates')

    with np.errstate(over='raise', invalid='raise'):
        scaled = coords * factor
    if not np.isfinite(scaled).all() or not np.all(np.diff(scaled) > 0):
        raise ValueError('Converted coordinates lost finiteness or strict ordering')

    indices = tuple(range(len(coords)))
    step = TransformationStep(
        operation='convert_axis_unit_v1',
        parameters=(
            ('from_unit', current.axis_unit),
            ('to_unit', target_unit),
            ('scale_factor', factor),
        ),
        included_indices=indices,
        excluded_indices=(),
    )
    updated = replace(
        current,
        axis_unit=target_unit,
        coordinates=tuple(float(v) for v in scaled),
    )
    return TransformedInput(original=original, transformed=updated, steps=prior_steps + (step,))


def convert_wavenumber_to_microns(
    item: ComparisonInput | TransformedInput,
    target_unit: str = 'microns',
) -> TransformedInput:
    """Explicitly convert strictly increasing wavenumbers (cm^-1) to strictly increasing microns.

    Because lambda(um) = 1e4 / nu(cm^-1) is monotonically decreasing, converting
    strictly increasing wavenumbers into strictly increasing wavelengths reverses
    the coordinate order and applies the exact reversal permutation P to values,
    sigma, and covariance (C' = P C P^T), preserving quadratic forms r^T C^-1 r.
    """
    original, current, prior_steps = _unwrap(item)
    if current.axis_unit not in ('cm^-1', 'cm-1', '1/cm') or target_unit != 'microns':
        raise ValueError(
            f'Unsupported wavenumber conversion: {current.axis_unit!r} -> {target_unit!r}'
        )
    coords = np.asarray(current.coordinates, dtype=float)
    values = np.asarray(current.values, dtype=float)
    n = len(coords)
    if coords.ndim != 1 or n < 3 or not np.isfinite(coords).all() or np.any(coords <= 0):
        raise ValueError('Wavenumber conversion requires at least 3 positive finite coordinates')
    if values.shape != coords.shape or not np.isfinite(values).all():
        raise ValueError('Wavenumber conversion requires finite 1D values matching coordinates')
    if not np.all(np.diff(coords) > 0):
        raise ValueError('Wavenumber conversion requires strictly increasing wavenumbers')

    perm = tuple(reversed(range(n)))
    with np.errstate(divide='raise', over='raise', invalid='raise'):
        wavelengths_um = (10000.0 / coords)[list(perm)]
    if not np.isfinite(wavelengths_um).all() or not np.all(np.diff(wavelengths_um) > 0):
        raise ValueError('Converted wavelengths lost finiteness or strict increasing ordering')

    reordered_values = tuple(float(v) for v in values[list(perm)])
    reordered_sigma = None
    if current.sigma is not None:
        sigma = np.asarray(current.sigma, dtype=float)
        if sigma.shape != coords.shape or not np.isfinite(sigma).all():
            raise ValueError('Wavenumber conversion encountered invalid sigma array')
        reordered_sigma = tuple(float(v) for v in sigma[list(perm)])

    reordered_cov = None
    if current.covariance is not None:
        cov = np.asarray(current.covariance, dtype=float)
        if cov.shape != (n, n) or not np.isfinite(cov).all():
            raise ValueError('Wavenumber conversion encountered invalid covariance matrix')
        perm_cov = cov[np.ix_(perm, perm)]
        reordered_cov = tuple(tuple(float(v) for v in row) for row in perm_cov)

    step = TransformationStep(
        operation='convert_wavenumber_to_microns_v1',
        parameters=(
            ('from_unit', current.axis_unit),
            ('to_unit', target_unit),
            ('formula', '10000.0 / wavenumber_cm_inv'),
            ('axis_order_reversed', True),
        ),
        included_indices=perm,
        excluded_indices=(),
    )
    updated = replace(
        current,
        axis_unit=target_unit,
        coordinates=tuple(float(v) for v in wavelengths_um),
        values=reordered_values,
        sigma=reordered_sigma,
        covariance=reordered_cov,
    )
    return TransformedInput(original=original, transformed=updated, steps=prior_steps + (step,))



def _subset_input(
    item: ComparisonInput | TransformedInput,
    included: Sequence[int],
    operation: str,
    exclusion_reason: str,
    extra_params: tuple[tuple[str, object], ...] = (),
) -> TransformedInput:
    original, current, prior_steps = _unwrap(item)
    n = len(current.coordinates)
    inc_tuple = tuple(int(i) for i in included)
    inc_set = set(inc_tuple)
    exc_tuple = tuple(i for i in range(n) if i not in inc_set)
    if len(inc_tuple) < 3:
        raise ValueError('At least 3 shared points are required; subset refused')

    sub_coords = tuple(current.coordinates[i] for i in inc_tuple)
    sub_vals = tuple(current.values[i] for i in inc_tuple)
    sub_sigma = (
        tuple(current.sigma[i] for i in inc_tuple)
        if current.sigma is not None else None
    )
    sub_cov = None
    if current.covariance is not None:
        cov = np.asarray(current.covariance, dtype=float)
        if cov.shape != (n, n):
            raise ValueError('Covariance shape does not match coordinate count')
        sliced = cov[np.ix_(inc_tuple, inc_tuple)]
        sub_cov = tuple(tuple(float(v) for v in row) for row in sliced)

    step = TransformationStep(
        operation=operation,
        parameters=extra_params + (('original_count', n), ('retained_count', len(inc_tuple))),
        included_indices=inc_tuple,
        excluded_indices=exc_tuple,
        exclusion_reason=exclusion_reason if exc_tuple else None,
    )
    updated = replace(
        current,
        coordinates=sub_coords,
        values=sub_vals,
        sigma=sub_sigma,
        covariance=sub_cov,
    )
    return TransformedInput(original=original, transformed=updated, steps=prior_steps + (step,))


def subset_by_indices(
    item: ComparisonInput | TransformedInput,
    included_indices: Sequence[int],
    *,
    exclusion_reason: str = 'excluded_by_model_bin_coverage',
) -> TransformedInput:
    """Explicitly subset an input to retained coordinate indices with full provenance."""
    return _subset_input(
        item,
        included_indices,
        'subset_by_indices_v1',
        exclusion_reason,
    )


def restrict_to_shared_coordinates(
    left: ComparisonInput | TransformedInput,
    right: ComparisonInput | TransformedInput,
) -> tuple[TransformedInput, TransformedInput]:
    """Restrict two curves with matching axis units and frame to exact shared coordinates.

    No interpolation or tolerance matching is performed. Excluded indices on both
    inputs are explicitly recorded in TransformationStep.
    """
    _, cur_left, _ = _unwrap(left)
    _, cur_right, _ = _unwrap(right)
    if not cur_left.axis_unit or cur_left.axis_unit != cur_right.axis_unit:
        raise ValueError('Shared-coordinate restriction requires matching explicit axis_unit')
    if not cur_left.coordinate_frame or cur_left.coordinate_frame != cur_right.coordinate_frame:
        raise ValueError('Shared-coordinate restriction requires matching explicit coordinate_frame')

    x_left = np.asarray(cur_left.coordinates, dtype=float)
    x_right = np.asarray(cur_right.coordinates, dtype=float)
    if (
        x_left.ndim != 1 or x_right.ndim != 1
        or len(x_left) < 3 or len(x_right) < 3
        or not np.isfinite(x_left).all() or not np.isfinite(x_right).all()
        or not np.all(np.diff(x_left) > 0) or not np.all(np.diff(x_right) > 0)
    ):
        raise ValueError('Shared-coordinate restriction requires finite strictly increasing 1D grids')

    right_index_by_coord = {float(v): idx for idx, v in enumerate(x_right)}
    inc_left: list[int] = []
    inc_right: list[int] = []
    for idx_l, val in enumerate(x_left):
        key = float(val)
        if key in right_index_by_coord:
            inc_left.append(idx_l)
            inc_right.append(right_index_by_coord[key])

    if len(inc_left) < 3:
        raise ValueError(
            f'Insufficient exact coordinate overlap ({len(inc_left)} shared points; need >= 3)'
        )

    return (
        _subset_input(left, inc_left, 'restrict_to_shared_coordinates_v1', 'outside_shared_exact_grid'),
        _subset_input(right, inc_right, 'restrict_to_shared_coordinates_v1', 'outside_shared_exact_grid'),
    )


_trapezoid = getattr(np, 'trapezoid', getattr(np, 'trapz', None))


def _trapezoid_bin_average(x_grid: np.ndarray, y_grid: np.ndarray, left_edge: float, right_edge: float) -> float:
    """Exact piecewise-linear average over [left_edge, right_edge] within x_grid domain."""
    y_left = float(np.interp(left_edge, x_grid, y_grid))
    y_right = float(np.interp(right_edge, x_grid, y_grid))
    interior_mask = (x_grid > left_edge) & (x_grid < right_edge)
    xs = np.concatenate(([left_edge], x_grid[interior_mask], [right_edge]))
    ys = np.concatenate(([y_left], y_grid[interior_mask], [y_right]))
    area = float(_trapezoid(ys, xs))
    return area / (right_edge - left_edge)


def integrate_model_over_bins(
    model_input: ComparisonInput | TransformedInput,
    bin_centers: Sequence[float],
    bin_edges: Sequence[tuple[float, float]],
    *,
    response_id: str,
    response_evidence: str,
) -> tuple[TransformedInput, tuple[int, ...], tuple[int, ...]]:
    """Average a dense forward_model over declared top-hat bins without extrapolation.

    Observations are never upsampled; only role == 'forward_model' is accepted.
    Bins partially or wholly outside [x_model[0], x_model[-1]] are never clipped
    or extrapolated—their indices are returned as excluded_bin_indices so the
    caller can subset the observation explicitly with full provenance.
    """
    original, current, prior_steps = _unwrap(model_input)
    if current.role != 'forward_model':
        raise ValueError('Top-hat bin integration is permitted only for forward_model inputs')
    if current.noise_kind not in (None, 'deterministic_model'):
        raise ValueError('Top-hat bin integration requires deterministic or unstated model noise')
    if not isinstance(response_id, str) or not response_id.strip():
        raise ValueError('Explicit non-empty response_id is required')
    if not isinstance(response_evidence, str) or not response_evidence.strip():
        raise ValueError('Explicit non-empty response_evidence is required')

    centers = np.asarray(bin_centers, dtype=float)
    if centers.ndim != 1 or len(centers) < 3 or len(bin_edges) != len(centers):
        raise ValueError('Require at least 3 bin centers with matching bin_edges length')
    if not np.isfinite(centers).all() or not np.all(np.diff(centers) > 0):
        raise ValueError('Bin centers must be finite and strictly increasing')

    x_m = np.asarray(current.coordinates, dtype=float)
    y_m = np.asarray(current.values, dtype=float)
    if (
        x_m.ndim != 1 or y_m.ndim != 1 or len(x_m) < 3 or len(x_m) != len(y_m)
        or not np.isfinite(x_m).all() or not np.isfinite(y_m).all()
        or not np.all(np.diff(x_m) > 0)
    ):
        raise ValueError('Model coordinates and values must be finite 1D arrays with strictly increasing grid')

    domain_start, domain_stop = float(x_m[0]), float(x_m[-1])
    included_bins: list[int] = []
    excluded_bins: list[int] = []
    averaged_coords: list[float] = []
    averaged_values: list[float] = []

    for idx, (edge_pair, center) in enumerate(zip(bin_edges, centers)):
        if len(edge_pair) != 2:
            raise ValueError('Each bin edge entry must be a (left, right) pair')
        a, b = float(edge_pair[0]), float(edge_pair[1])
        if not (np.isfinite(a) and np.isfinite(b)) or b <= a or not (a <= float(center) <= b):
            raise ValueError(f'Invalid bin edges {(a, b)} for center {float(center)}')
        if domain_start <= a and b <= domain_stop:
            included_bins.append(idx)
            averaged_coords.append(float(center))
            averaged_values.append(_trapezoid_bin_average(x_m, y_m, a, b))
        else:
            excluded_bins.append(idx)

    if len(included_bins) < 3:
        raise ValueError(
            f'Insufficient fully covered bins ({len(included_bins)} covered; need >= 3)'
        )

    step = TransformationStep(
        operation='integrate_tophat_bins_v1',
        parameters=(
            ('response_id', response_id),
            ('response_evidence', response_evidence),
            ('model_domain', (domain_start, domain_stop)),
            ('total_bins', len(centers)),
            ('covered_bins', len(included_bins)),
        ),
        included_indices=tuple(included_bins),
        excluded_indices=tuple(excluded_bins),
        exclusion_reason='bin_not_fully_covered_by_model_domain' if excluded_bins else None,
    )
    updated = replace(
        current,
        response_id=response_id,
        response_evidence=response_evidence,
        coordinates=tuple(averaged_coords),
        values=tuple(averaged_values),
    )
    return (
        TransformedInput(original=original, transformed=updated, steps=prior_steps + (step,)),
        tuple(included_bins),
        tuple(excluded_bins),
    )

