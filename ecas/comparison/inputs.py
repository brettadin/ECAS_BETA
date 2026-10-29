"""Deliberate adapters from imported/cached ECAS data to eligibility inputs.

Port of the reviewed research adapter (docs/Chunk_5/import_eligibility_adapter.py),
extended to cached ExoMol products. Facts are copied from established import or
provenance fields only; nothing is converted, sorted, masked or inferred, and
unknown metadata stays unknown. No file is read and nothing is scored.
"""
from dataclasses import dataclass

from .eligibility import ComparisonInput


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

