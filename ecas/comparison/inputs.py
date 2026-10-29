"""Deliberate adapters from imported/cached ECAS data to eligibility inputs.

Port of the reviewed research adapter (docs/Chunk_5/import_eligibility_adapter.py),
extended to cached ExoMol products. Facts are copied from established import or
provenance fields only; nothing is converted, sorted, masked or inferred, and
unknown metadata stays unknown. No file is read and nothing is scored.
"""
from dataclasses import dataclass
import math

from .eligibility import ComparisonInput


@dataclass(frozen=True)
class AsymmetricUncertaintyAudit:
    has_asymmetric_columns: bool
    column_pair: tuple[str, str] | None
    envelope_sigma: tuple[float, ...] | None
    max_asymmetry_ratio: float
    exceeding_indices: tuple[int, ...]
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


def extract_observation_bin_edges(spectrum) -> tuple[tuple[float, float], ...] | None:
    """Extract explicit non-extrapolated passband edges [center - bw/2, center + bw/2].

    Note: NASA Exoplanet Archive tables vary on whether 'bandwidth' denotes full width
    or half-width depending on contributor, though positive finite width always defines
    a symmetric passband interval around centralwavelng. Here we use [c - bw/2, c + bw/2]
    when every row provides finite positive wavelength and bandwidth.
    """
    raw_cols = tuple(getattr(spectrum, 'columns', ()))
    col_map = {str(c).strip().lower(): str(c) for c in raw_cols}
    bw_col = None
    for cand in ('bandwidth', 'bin_width', 'fwhm'):
        if cand in col_map:
            bw_col = col_map[cand]
            break
    if bw_col is None or not spectrum.rows:
        return None
    wl_col = col_map.get('wavelength', 'wavelength')
    edges: list[tuple[float, float]] = []
    for row in spectrum.rows:
        c = row.get(wl_col)
        bw = row.get(bw_col)
        if (
            isinstance(c, bool)
            or isinstance(bw, bool)
            or not isinstance(c, (int, float))
            or not isinstance(bw, (int, float))
            or not math.isfinite(c)
            or not math.isfinite(bw)
            or bw <= 0.0
        ):
            return None
        half = 0.5 * float(bw)
        left_edge = float(c) - half
        right_edge = float(c) + half
        if left_edge <= 0.0 or right_edge <= left_edge:
            return None
        edges.append((left_edge, right_edge))
    return tuple(edges)


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

