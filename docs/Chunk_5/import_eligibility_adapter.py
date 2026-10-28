"""Research-only adapter: preserve imported facts without filling scientific gaps."""
from dataclasses import dataclass
from pathlib import Path
import runpy

contract = runpy.run_path(str(Path(__file__).with_name('eligibility_contract.py')))


@dataclass(frozen=True)
class AdaptedInput:
    comparison_input: object
    original_row_indices: tuple
    mappings: tuple
    unresolved: tuple
    raw_uncertainty_columns: tuple


def adapt(spectrum, *, details=None, source_sha256=None, role=None,
          coordinate_frame=None, response_id=None, response_evidence=None):
    """Copy canonical columns in original order; neither read files nor score data.

    Caller role/frame/response evidence is not authenticated. Known NASA import
    details must match this exact imported dataset. Error columns are preserved
    for audit, never promoted to a Gaussian likelihood or independence assumption.
    """
    mappings = [('source_id', 'SpectrumData.source_file'),
                ('coordinates', 'rows.wavelength, original order'),
                ('values', 'rows.signal, original order')]
    if details is not None:
        if details.spectrum != spectrum:
            raise ValueError('Import details do not match the supplied spectrum')
        if source_sha256 is not None and source_sha256 != details.source_sha256:
            raise ValueError('Supplied source hash conflicts with import details')
        source_sha256 = details.source_sha256
        mappings.append(('source_sha256', 'TransmissionTable.source_sha256'))
    elif source_sha256 is not None:
        mappings.append(('source_sha256', 'caller-supplied; not verified by adapter'))
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
    values = tuple(row.get('signal') for row in spectrum.rows)
    coordinates = tuple(row.get('wavelength') for row in spectrum.rows)
    errors = tuple((name, tuple(row.get(name) for row in spectrum.rows))
                   for name in ('uncertainty', 'pl_trandeperr1', 'pl_trandeperr2')
                   if name in spectrum.columns)
    unresolved = ['noise convention/confidence and covariance not inferred']
    for name, value in (('role', role), ('coordinate_frame', coordinate_frame),
                        ('response_id', response_id), ('response_evidence', response_evidence)):
        if value is None:
            unresolved.append(f'{name} not established')
        else:
            mappings.append((name, 'caller declaration; requires evidence review'))
    if observable is None:
        unresolved.append('observable not established by supported signal_type mapping')
    if not source_sha256:
        unresolved.append('raw source hash unavailable; no filesystem lookup performed')
    item = contract['ComparisonInput'](str(spectrum.source_file), source_sha256, role,
        observable, axis_unit, signal_unit, coordinate_frame, response_id,
        response_evidence, coordinates, values)
    return AdaptedInput(item, tuple(range(len(spectrum.rows))), tuple(mappings),
                        tuple(unresolved), errors)
