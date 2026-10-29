"""Deliberate adapters from imported/cached ECAS data to eligibility inputs.

Port of the reviewed research adapter (docs/Chunk_5/import_eligibility_adapter.py),
extended to cached ExoMol products. Facts are copied from established import or
provenance fields only; nothing is converted, sorted, masked or inferred, and
unknown metadata stays unknown. No file is read and nothing is scored.
"""
from dataclasses import dataclass
import math
import statistics

from .eligibility import ComparisonInput

_AXIS_UNIT_ALIASES = {
    'um': 'microns',
    'micron': 'microns',
    'microns': 'microns',
    'nm': 'nanometers',
    'nanometer': 'nanometers',
    'nanometers': 'nanometers',
    'a': 'angstroms',
    'angstrom': 'angstroms',
    'angstroms': 'angstroms',
    'cm-1': 'cm^-1',
    'cm^-1': 'cm^-1',
    '1/cm': 'cm^-1',
}

_TOPHAT_RESPONSE_NOTE = (
    'Resolved intervals define wavelength-bin boundaries for uniform top-hat boxcar '
    'averaging (integrate_tophat_bins_v1); they do not represent a non-uniform '
    'detector transmission curve or instrument line-spread function (LSF) convolution.'
)


@dataclass(frozen=True)
class AsymmetricUncertaintyAudit:
    has_asymmetric_columns: bool
    column_pair: tuple[str, str] | None
    envelope_sigma: tuple[float, ...] | None
    max_asymmetry_ratio: float
    exceeding_indices: tuple[int, ...]
    warning: str | None


@dataclass(frozen=True)
class ObservationBinAudit:
    has_resolved_bins: bool
    bin_edges: tuple[tuple[float, float], ...] | None
    source_columns: tuple[str, ...] | None
    convention: str
    axis_unit: str | None
    width_unit: str | None
    adjacent_spacing_to_width_median: float | None
    overlapping_pair_count: int
    response_shape_note: str | None
    warning: str | None


def audit_asymmetric_uncertainties(
    spectrum,
    *,
    asymmetry_threshold: float = 0.10,
) -> AsymmetricUncertaintyAudit:
    """Audit asymmetric upper/lower error columns without silently symmetrizing them.

    Computes per-bin asymmetry ratio ||sigma_+| - |sigma_-|| / max(|sigma_+|, |sigma_-|)
    and a conservative symmetric envelope max(|sigma_+|, |sigma_-|). Emits an explicit
    bias warning whenever any bin's asymmetry ratio exceeds asymmetry_threshold.
    """
    raw_cols = tuple(getattr(spectrum, 'columns', ()))
    col_map = {str(c).strip().lower(): str(c) for c in raw_cols}
    pair = None
    for up_col, lo_col in (
        ('pl_trandeperr1', 'pl_trandeperr2'),
        ('err_high', 'err_low'),
        ('err_plus', 'err_minus'),
        ('unc_upper', 'unc_lower'),
        ('unc_plus', 'unc_minus'),
        ('e_high', 'e_low'),
    ):
        if up_col in col_map and lo_col in col_map:
            pair = (col_map[up_col], col_map[lo_col])
            break
    if pair is None or not spectrum.rows:
        return AsymmetricUncertaintyAudit(
            has_asymmetric_columns=False,
            column_pair=None,
            envelope_sigma=None,
            max_asymmetry_ratio=0.0,
            exceeding_indices=(),
            warning=None,
        )

    up_name, lo_name = pair
    envelopes: list[float] = []
    exceeding: list[int] = []
    max_ratio = 0.0
    valid_all = True

    for idx, row in enumerate(spectrum.rows):
        u_raw = row.get(up_name)
        l_raw = row.get(lo_name)
        if (
            isinstance(u_raw, bool)
            or isinstance(l_raw, bool)
            or not isinstance(u_raw, (int, float))
            or not isinstance(l_raw, (int, float))
            or not math.isfinite(u_raw)
            or not math.isfinite(l_raw)
        ):
            valid_all = False
            break
        mag_u = abs(float(u_raw))
        mag_l = abs(float(l_raw))
        env = max(mag_u, mag_l)
        if env <= 0.0:
            valid_all = False
            break
        ratio = abs(mag_u - mag_l) / env
        if ratio > max_ratio:
            max_ratio = ratio
        if ratio > asymmetry_threshold:
            exceeding.append(idx)
        envelopes.append(env)

    if not valid_all:
        return AsymmetricUncertaintyAudit(
            has_asymmetric_columns=True,
            column_pair=pair,
            envelope_sigma=None,
            max_asymmetry_ratio=max_ratio,
            exceeding_indices=tuple(exceeding),
            warning=(
                f'Asymmetric uncertainty columns {pair[0]}/{pair[1]} contain missing or '
                'non-positive bounds and cannot form a complete 1-sigma envelope.'
            ),
        )

    warn = None
    if exceeding:
        warn = (
            f'{len(exceeding)} of {len(envelopes)} spectral bins exhibit >{asymmetry_threshold * 100:.0f}% '
            f'uncertainty asymmetry (max {max_ratio * 100:.1f}%) across {pair[0]}/{pair[1]}. '
            'Weighted diagnostics use a conservative symmetric envelope max(|+sigma|, |-sigma|); '
            'inspect unweighted residuals to check sensitivity to error asymmetry.'
        )
    return AsymmetricUncertaintyAudit(
        has_asymmetric_columns=True,
        column_pair=pair,
        envelope_sigma=tuple(envelopes),
        max_asymmetry_ratio=max_ratio,
        exceeding_indices=tuple(exceeding),
        warning=warn,
    )


def _is_valid_positive_number(val: object) -> bool:
    return (
        not isinstance(val, bool)
        and isinstance(val, (int, float))
        and math.isfinite(val)
        and float(val) > 0.0
    )


def _count_adjacent_overlaps(
    centers: list[float],
    edges: list[tuple[float, float]],
) -> tuple[int, int]:
    overlaps = 0
    positive_steps = 0
    for idx in range(len(centers) - 1):
        if centers[idx + 1] > centers[idx]:
            positive_steps += 1
            span_cur = edges[idx][1] - edges[idx][0]
            span_nxt = edges[idx + 1][1] - edges[idx + 1][0]
            rounding_tol = max(1e-12, 0.05 * min(span_cur, span_nxt))
            if edges[idx][1] > edges[idx + 1][0] + rounding_tol:
                overlaps += 1
    return overlaps, positive_steps


def audit_observation_bin_semantics(
    spectrum,
    *,
    column_units: dict[str, str | None] | tuple[tuple[str, str | None], ...] | None = None,
    width_convention: str = 'auto',
    require_axis_unit: bool = False,
    axis_unit_override: str | None = None,
) -> ObservationBinAudit:
    """Audit observation spectral-bin columns, width conventions, units, and response semantics.

    Distinguishes:
    1. Explicit bin boundary pairs (e.g. bin_low/bin_high, wave_min/wave_max) -> 'explicit_bounds'
    2. Explicit full-width columns (bin_width, full_width) -> 'full_width' [c - w/2, c + w/2]
    3. Explicit half-width columns (bin_half_width, half_width) -> 'half_width' [c - w, c + w]
    4. Archive 'bandwidth' columns -> 'full_width' (or 'half_width' when selected), with
       adjacent-spacing ratio diagnostics to flag half-width contributor conventions.
    5. Instrument 'fwhm' columns -> 'rejected_response_fwhm' (never treated as top-hat edges).
    """
    if width_convention not in ('auto', 'full_width', 'half_width'):
        raise ValueError(f'Unsupported width_convention: {width_convention!r}')

    raw_cols = tuple(getattr(spectrum, 'columns', ()))
    col_map = {str(c).strip().lower(): str(c) for c in raw_cols}
    effective_axis_unit = (
        axis_unit_override
        if axis_unit_override is not None
        else getattr(spectrum, 'axis_unit', None)
    )
    if isinstance(effective_axis_unit, str):
        effective_axis_unit = effective_axis_unit.strip() or None

    raw_unit_source = column_units if column_units is not None else getattr(spectrum, 'column_units', None)
    unit_lookup: dict[str, str | None] | None = None
    if raw_unit_source is not None:
        if isinstance(raw_unit_source, dict):
            unit_lookup = {str(k).strip().lower(): v for k, v in raw_unit_source.items()}
        else:
            unit_lookup = {str(k).strip().lower(): v for k, v in raw_unit_source}

    bound_pair: tuple[str, str] | None = None
    for lo_k, hi_k in (
        ('bin_low', 'bin_high'),
        ('bin_min', 'bin_max'),
        ('wave_min', 'wave_max'),
        ('wavelength_min', 'wavelength_max'),
        ('lambda_min', 'lambda_max'),
        ('wavelng_min', 'wavelng_max'),
    ):
        if lo_k in col_map and hi_k in col_map:
            bound_pair = (col_map[lo_k], col_map[hi_k])
            break

    full_w_col = next((col_map[k] for k in ('bin_width', 'full_width') if k in col_map), None)
    half_w_col = next((col_map[k] for k in ('bin_half_width', 'half_width') if k in col_map), None)
    bandwidth_col = col_map.get('bandwidth')
    fwhm_col = col_map.get('fwhm')

    if bound_pair is not None:
        source_cols = bound_pair
        candidate_kind = 'explicit_bounds'
    elif full_w_col is not None:
        source_cols = (full_w_col,)
        candidate_kind = 'explicit_full_width'
    elif half_w_col is not None:
        source_cols = (half_w_col,)
        candidate_kind = 'explicit_half_width'
    elif bandwidth_col is not None:
        source_cols = (bandwidth_col,)
        candidate_kind = 'archive_bandwidth'
    elif fwhm_col is not None:
        w_unit = unit_lookup.get(fwhm_col.lower()) if unit_lookup is not None else None
        return ObservationBinAudit(
            has_resolved_bins=False,
            bin_edges=None,
            source_columns=(fwhm_col,),
            convention='rejected_response_fwhm',
            axis_unit=effective_axis_unit,
            width_unit=w_unit.strip() if isinstance(w_unit, str) and w_unit.strip() else None,
            adjacent_spacing_to_width_median=None,
            overlapping_pair_count=0,
            response_shape_note=(
                'FWHM describes the width of a peaked instrument line-spread function at half '
                'maximum, not uniform top-hat passband boundaries.'
            ),
            warning=(
                f'Column {fwhm_col!r} specifies instrument Full Width at Half Maximum (FWHM), '
                'which describes a peaked response profile rather than uniform top-hat bin edges; '
                'automatic top-hat bin integration is disabled.'
            ),
        )
    else:
        return ObservationBinAudit(
            has_resolved_bins=False,
            bin_edges=None,
            source_columns=None,
            convention='no_bin_columns',
            axis_unit=effective_axis_unit,
            width_unit=None,
            adjacent_spacing_to_width_median=None,
            overlapping_pair_count=0,
            response_shape_note=None,
            warning=None,
        )

    rows = getattr(spectrum, 'rows', ())
    if not rows:
        return ObservationBinAudit(
            has_resolved_bins=False,
            bin_edges=None,
            source_columns=source_cols,
            convention='unresolved_empty_rows',
            axis_unit=effective_axis_unit,
            width_unit=None,
            adjacent_spacing_to_width_median=None,
            overlapping_pair_count=0,
            response_shape_note=None,
            warning='Spectrum contains no measurement rows.',
        )

    resolved_width_unit: str | None = None
    if unit_lookup is not None:
        for sc in source_cols:
            if sc.lower() in unit_lookup:
                raw_u = unit_lookup[sc.lower()]
                clean_u = str(raw_u).strip() if raw_u is not None else ''
                if not clean_u and effective_axis_unit:
                    return ObservationBinAudit(
                        has_resolved_bins=False,
                        bin_edges=None,
                        source_columns=source_cols,
                        convention='unresolved_missing_width_unit',
                        axis_unit=effective_axis_unit,
                        width_unit=None,
                        adjacent_spacing_to_width_median=None,
                        overlapping_pair_count=0,
                        response_shape_note=None,
                        warning=(
                            f'Column {sc!r} has no declared unit in source table header while '
                            f'coordinate axis_unit is {effective_axis_unit!r}; passband edges '
                            'are not inferred from unitless width columns.'
                        ),
                    )
                if clean_u:
                    resolved_width_unit = clean_u
                    if effective_axis_unit:
                        norm_u = _AXIS_UNIT_ALIASES.get(clean_u.lower(), clean_u.lower())
                        norm_ax = _AXIS_UNIT_ALIASES.get(
                            effective_axis_unit.lower(), effective_axis_unit.lower()
                        )
                        if norm_u != norm_ax:
                            return ObservationBinAudit(
                                has_resolved_bins=False,
                                bin_edges=None,
                                source_columns=source_cols,
                                convention='unresolved_unit_mismatch',
                                axis_unit=effective_axis_unit,
                                width_unit=clean_u,
                                adjacent_spacing_to_width_median=None,
                                overlapping_pair_count=0,
                                response_shape_note=None,
                                warning=(
                                    f'Column {sc!r} unit {clean_u!r} conflicts with coordinate '
                                    f'axis_unit {effective_axis_unit!r}; automatic passband '
                                    'integration is blocked.'
                                ),
                            )

    if require_axis_unit and not effective_axis_unit:
        return ObservationBinAudit(
            has_resolved_bins=False,
            bin_edges=None,
            source_columns=source_cols,
            convention='unresolved_missing_axis_unit',
            axis_unit=None,
            width_unit=resolved_width_unit,
            adjacent_spacing_to_width_median=None,
            overlapping_pair_count=0,
            response_shape_note=None,
            warning=(
                f'Coordinate axis_unit is not established; numeric column(s) '
                f'{", ".join(source_cols)} cannot establish physical passband edges '
                'without a verified coordinate unit.'
            ),
        )

    wl_col = col_map.get('wavelength', col_map.get('centralwavelng', 'wavelength'))

    if candidate_kind == 'explicit_bounds':
        lo_col, hi_col = source_cols
        edges: list[tuple[float, float]] = []
        centers: list[float] = []
        for row in rows:
            c = row.get(wl_col)
            lo = row.get(lo_col)
            hi = row.get(hi_col)
            if not (
                _is_valid_positive_number(c)
                and _is_valid_positive_number(lo)
                and _is_valid_positive_number(hi)
            ):
                return ObservationBinAudit(
                    has_resolved_bins=False,
                    bin_edges=None,
                    source_columns=source_cols,
                    convention='unresolved_invalid_values',
                    axis_unit=effective_axis_unit,
                    width_unit=resolved_width_unit or effective_axis_unit,
                    adjacent_spacing_to_width_median=None,
                    overlapping_pair_count=0,
                    response_shape_note=None,
                    warning=f'Explicit bin bound columns {lo_col}/{hi_col} contain missing or non-positive values.',
                )
            cf, lof, hif = float(c), float(lo), float(hi)
            if hif <= lof or not (lof <= cf <= hif):
                return ObservationBinAudit(
                    has_resolved_bins=False,
                    bin_edges=None,
                    source_columns=source_cols,
                    convention='unresolved_invalid_values',
                    axis_unit=effective_axis_unit,
                    width_unit=resolved_width_unit or effective_axis_unit,
                    adjacent_spacing_to_width_median=None,
                    overlapping_pair_count=0,
                    response_shape_note=None,
                    warning=f'Explicit bin bounds [{lof}, {hif}] do not bracket center {cf}.',
                )
            centers.append(cf)
            edges.append((lof, hif))
        overlaps, _ = _count_adjacent_overlaps(centers, edges)
        warn = (
            f'{overlaps} adjacent bin pair(s) overlap in explicit bounds {lo_col}/{hi_col}.'
            if overlaps > 0 else None
        )
        return ObservationBinAudit(
            has_resolved_bins=True,
            bin_edges=tuple(edges),
            source_columns=source_cols,
            convention='explicit_bounds',
            axis_unit=effective_axis_unit,
            width_unit=resolved_width_unit or effective_axis_unit,
            adjacent_spacing_to_width_median=None,
            overlapping_pair_count=overlaps,
            response_shape_note=_TOPHAT_RESPONSE_NOTE,
            warning=warn,
        )

    bw_col = source_cols[0]
    if candidate_kind == 'explicit_full_width' and width_convention == 'half_width':
        return ObservationBinAudit(
            has_resolved_bins=False,
            bin_edges=None,
            source_columns=source_cols,
            convention='unresolved_conflicting_convention',
            axis_unit=effective_axis_unit,
            width_unit=resolved_width_unit or effective_axis_unit,
            adjacent_spacing_to_width_median=None,
            overlapping_pair_count=0,
            response_shape_note=None,
            warning=f'Column {bw_col!r} explicitly denotes full bin width and cannot be interpreted as half_width.',
        )
    if candidate_kind == 'explicit_half_width' and width_convention == 'full_width':
        return ObservationBinAudit(
            has_resolved_bins=False,
            bin_edges=None,
            source_columns=source_cols,
            convention='unresolved_conflicting_convention',
            axis_unit=effective_axis_unit,
            width_unit=resolved_width_unit or effective_axis_unit,
            adjacent_spacing_to_width_median=None,
            overlapping_pair_count=0,
            response_shape_note=None,
            warning=f'Column {bw_col!r} explicitly denotes bin half-width and cannot be interpreted as full_width.',
        )

    centers: list[float] = []
    widths: list[float] = []
    for row in rows:
        c = row.get(wl_col)
        bw = row.get(bw_col)
        if not (_is_valid_positive_number(c) and _is_valid_positive_number(bw)):
            return ObservationBinAudit(
                has_resolved_bins=False,
                bin_edges=None,
                source_columns=source_cols,
                convention='unresolved_invalid_values',
                axis_unit=effective_axis_unit,
                width_unit=resolved_width_unit or effective_axis_unit,
                adjacent_spacing_to_width_median=None,
                overlapping_pair_count=0,
                response_shape_note=None,
                warning=f'Column {bw_col!r} or coordinate {wl_col!r} contains missing or non-positive values.',
            )
        centers.append(float(c))
        widths.append(float(bw))

    ratios: list[float] = []
    for idx in range(len(centers) - 1):
        dc = centers[idx + 1] - centers[idx]
        mean_w = 0.5 * (widths[idx] + widths[idx + 1])
        if dc > 0.0 and mean_w > 0.0:
            ratios.append(dc / mean_w)
    med_ratio = float(statistics.median(ratios)) if ratios else None

    if candidate_kind == 'explicit_half_width' or (
        candidate_kind == 'archive_bandwidth' and width_convention == 'half_width'
    ):
        resolved_convention = 'half_width'
        half_scale = 1.0
    else:
        resolved_convention = 'full_width'
        half_scale = 0.5

    edges: list[tuple[float, float]] = []
    for cf, wf in zip(centers, widths):
        half = half_scale * wf
        left_edge = cf - half
        right_edge = cf + half
        if left_edge <= 0.0 or right_edge <= left_edge:
            return ObservationBinAudit(
                has_resolved_bins=False,
                bin_edges=None,
                source_columns=source_cols,
                convention='unresolved_invalid_values',
                axis_unit=effective_axis_unit,
                width_unit=resolved_width_unit or effective_axis_unit,
                adjacent_spacing_to_width_median=med_ratio,
                overlapping_pair_count=0,
                response_shape_note=None,
                warning=f'Computed bin edges [{left_edge}, {right_edge}] around {cf} are non-positive.',
            )
        edges.append((left_edge, right_edge))

    overlaps, pos_steps = _count_adjacent_overlaps(centers, edges)
    if candidate_kind == 'archive_bandwidth' and resolved_convention == 'half_width' and pos_steps > 0:
        full_edges = [(cf - 0.5 * wf, cf + 0.5 * wf) for cf, wf in zip(centers, widths)]
        full_overlaps, _ = _count_adjacent_overlaps(centers, full_edges)
        if overlaps > 0.25 * pos_steps and full_overlaps <= 0.05 * pos_steps:
            ratio_str = f'{med_ratio:.2f}' if med_ratio is not None else 'n/a'
            return ObservationBinAudit(
                has_resolved_bins=False,
                bin_edges=None,
                source_columns=source_cols,
                convention='unresolved_overlapping_bins',
                axis_unit=effective_axis_unit,
                width_unit=resolved_width_unit or effective_axis_unit,
                adjacent_spacing_to_width_median=med_ratio,
                overlapping_pair_count=overlaps,
                response_shape_note=None,
                warning=(
                    f'Interpreting {bw_col!r} as half-width [c - w, c + w] causes {overlaps} of '
                    f'{pos_steps} adjacent bins to overlap (median spacing/width = {ratio_str}); '
                    'source values appear to represent full widths.'
                ),
            )

    warnings_list: list[str] = []
    if (
        candidate_kind == 'archive_bandwidth'
        and resolved_convention == 'full_width'
        and med_ratio is not None
        and 1.75 <= med_ratio <= 2.25
    ):
        warnings_list.append(
            f'Column {bw_col!r} has median adjacent center spacing / bandwidth = {med_ratio:.2f} '
            '(~2.0), which is consistent with a contributor half-width (+/-dw) convention. '
            'Full-width top-hat edges [c - bw/2, c + bw/2] were applied; switch bin width '
            'convention to half_width [c - bw, c + bw] if the source table reports half-widths.'
        )
    if overlaps > 0:
        warnings_list.append(
            f'{overlaps} adjacent passband pair(s) overlap under {resolved_convention} '
            f'interpretation of {bw_col!r}.'
        )

    return ObservationBinAudit(
        has_resolved_bins=True,
        bin_edges=tuple(edges),
        source_columns=source_cols,
        convention=resolved_convention,
        axis_unit=effective_axis_unit,
        width_unit=resolved_width_unit or effective_axis_unit,
        adjacent_spacing_to_width_median=med_ratio,
        overlapping_pair_count=overlaps,
        response_shape_note=_TOPHAT_RESPONSE_NOTE,
        warning=' '.join(warnings_list) if warnings_list else None,
    )


def extract_observation_bin_edges(
    spectrum,
    *,
    column_units: dict[str, str | None] | tuple[tuple[str, str | None], ...] | None = None,
    width_convention: str = 'auto',
    require_axis_unit: bool = False,
    axis_unit_override: str | None = None,
) -> tuple[tuple[float, float], ...] | None:
    """Extract validated non-extrapolated passband edges when bin semantics are resolved.

    Delegates to audit_observation_bin_semantics(). Instrument 'fwhm' columns describe
    peaked line-spread profiles rather than top-hat passband boundaries and return None.
    """
    audit = audit_observation_bin_semantics(
        spectrum,
        column_units=column_units,
        width_convention=width_convention,
        require_axis_unit=require_axis_unit,
        axis_unit_override=axis_unit_override,
    )
    return audit.bin_edges


@dataclass(frozen=True)
class AdaptedInput:
    comparison_input: ComparisonInput
    original_row_indices: tuple
    mappings: tuple
    unresolved: tuple
    raw_uncertainty_columns: tuple


def observation_input(spectrum, source_sha256=None):
    """Copy canonical wavelength/signal columns in original order.

    The caller's hash must be the importer's raw-source hash for this exact
    spectrum; it is never recomputed from parsed values. Role, coordinate frame,
    response and noise are not established by an import and stay unknown. Error
    columns are preserved for audit, never promoted to a likelihood.
    """
    mappings = [('source_id', 'SpectrumData.source_file'),
                ('coordinates', 'rows.wavelength, original order'),
                ('values', 'rows.signal, original order')]
    if source_sha256:
        mappings.append(('source_sha256', 'importer raw-source hash supplied with the snapshot; not recomputed'))
    axis_unit = spectrum.axis_unit
    signal_unit = spectrum.signal_unit
    if signal_unit == '%':
        signal_unit = 'percent'
        mappings.append(('signal_unit', 'explicit label mapping % -> percent; values unchanged'))
    elif signal_unit is not None:
        mappings.append(('signal_unit', 'SpectrumData.signal_unit; no conversion'))
    observable = {'Transmission': 'transit_depth'}.get(spectrum.signal_type)
    if observable is not None:
        mappings.append(('observable', 'explicit SpectrumData.signal_type Transmission -> transit_depth'))
    if axis_unit is not None:
        mappings.append(('axis_unit', 'SpectrumData.axis_unit; no conversion'))
    errors = tuple((name, tuple(row.get(name) for row in spectrum.rows))
                   for name in ('uncertainty', 'pl_trandeperr1', 'pl_trandeperr2')
                   if name in spectrum.columns)
    unresolved = ['role, coordinate_frame, response_id and response_evidence not established',
                  'noise convention/confidence and covariance not inferred']
    if observable is None:
        unresolved.append('observable not established by supported signal_type mapping')
    if not source_sha256:
        unresolved.append('raw source hash unavailable; no filesystem lookup performed')
    item = ComparisonInput(str(spectrum.source_file), source_sha256 or None, None, observable,
        axis_unit, signal_unit, None, None, None,
        tuple(row.get('wavelength') for row in spectrum.rows),
        tuple(row.get('signal') for row in spectrum.rows))
    return AdaptedInput(item, tuple(range(len(spectrum.rows))), tuple(mappings),
                        tuple(unresolved), errors)


def reference_input(result):
    """Describe a validated cached ExoMol product exactly as its provenance states.

    A calculated absorption cross section on wavenumber is not a comparable
    transit-depth observable: its role and observable are recorded truthfully so
    the contract blocks it pending an explicit physical model. Units come from
    the validated product; the raw-byte hash is the product's source hash.
    """
    product = getattr(result, 'product', result)
    mappings = (('source_id', 'ExoMol product provenance source_url'),
                ('source_sha256', 'MolecularCrossSection.source_sha256 (raw product bytes)'),
                ('role', f'product_kind {product.product_kind}; not a supported comparison role'),
                ('observable', f'product_kind {product.product_kind} -> absorption_cross_section'),
                ('axis_unit', f'coordinate_unit ({product.coordinate_kind}); no conversion'),
                ('signal_unit', 'MolecularCrossSection.signal_unit; no conversion'),
                ('coordinates', 'points[0], original order'),
                ('values', 'points[1], original order'))
    unresolved = ('coordinate_frame, response_id and response_evidence not established',
                  'no noise or uncertainty is supplied by the product')
    item = ComparisonInput(product.provenance.source_url, product.source_sha256,
        product.product_kind, 'absorption_cross_section', product.coordinate_unit,
        product.signal_unit, None, None, None,
        tuple(point[0] for point in product.points), tuple(point[1] for point in product.points))
    return AdaptedInput(item, tuple(range(len(product.points))), mappings, unresolved, ())
