from dataclasses import replace
from pathlib import Path
import runpy

import pytest

from ecas.ingestion.import_manager import import_spectrum
from ecas.ingestion.nasa_table import import_transmission_table
from ecas.models.spectrum import SpectrumData

ROOT = Path(__file__).resolve().parents[1]
adapter = runpy.run_path(str(ROOT / 'docs/Chunk_5/import_eligibility_adapter.py'))
adapt, assess = adapter['adapt'], adapter['contract']['assess']


def test_captured_import_mapping_preserves_bytes_values_and_unknowns():
    # This checks adapter fidelity only; it is not real-data comparison validation.
    source = ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl'
    raw = source.read_bytes()
    details = import_transmission_table(source)
    original = details.spectrum
    result = adapt(original, details=details)
    item = result.comparison_input
    assert item.source_sha256 == details.source_sha256
    assert item.signal_unit == 'percent' and item.axis_unit == 'microns'
    assert item.observable == 'transit_depth'
    assert item.values == tuple(row['pl_trandep'] for row in original.rows)
    assert item.coordinates == tuple(row['centralwavelng'] for row in original.rows)
    assert result.original_row_indices == tuple(range(331))
    assert dict(result.raw_uncertainty_columns)['pl_trandeperr2'][0] < 0
    assert item.noise_kind is None and item.role is None and item.response_id is None
    assert assess(item, item).status == 'missing_requirements'
    assert source.read_bytes() == raw


def test_generic_csv_does_not_acquire_units_or_physical_identity(tmp_path):
    source = tmp_path / 'generic.csv'
    source.write_text('wavelength,signal,uncertainty\n1,2,0.1\n2,3,0.2\n3,4,0.1\n')
    result = adapt(import_spectrum(source))
    assert result.comparison_input.observable is None
    assert result.comparison_input.signal_unit is None
    assert result.comparison_input.source_sha256 is None
    assert dict(result.raw_uncertainty_columns)['uncertainty'] == (0.1, 0.2, 0.1)
    assert result.comparison_input.noise_kind is None


def test_declared_synthetic_metadata_allows_unweighted_not_weighted():
    spectrum = SpectrumData(Path('synthetic.csv'),
        ({'wavelength': 1., 'signal': 2.}, {'wavelength': 2., 'signal': 2.1},
         {'wavelength': 3., 'signal': 2.}), ('wavelength', 'signal'), 'microns', '%', 'Transmission')
    result = adapt(spectrum, source_sha256='a'*64, role='observation',
        coordinate_frame='invented-frame', response_id='invented-common-response', response_evidence='synthetic fixture')
    assert assess(result.comparison_input, result.comparison_input).status == 'eligible'
    assert assess(result.comparison_input, result.comparison_input, weighted=True).status != 'eligible'
    assert result.comparison_input.values == (2., 2.1, 2.)  # no percent/fraction scaling


@pytest.mark.parametrize('conflict', ['hash', 'spectrum'])
def test_mismatched_import_details_are_refused(conflict):
    details = import_transmission_table(ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl')
    with pytest.raises(ValueError):
        adapt(replace(details.spectrum, signal_unit='fraction') if conflict == 'spectrum' else details.spectrum,
              details=details, source_sha256='b'*64 if conflict == 'hash' else None)


def test_missing_values_and_source_order_are_not_silently_repaired():
    spectrum = SpectrumData(Path('synthetic.csv'),
        ({'wavelength': 3., 'signal': 2.}, {'wavelength': 1.}, {'wavelength': 2., 'signal': 4.}),
        ('wavelength', 'signal'))
    result = adapt(spectrum)
    assert result.comparison_input.coordinates == (3., 1., 2.)
    assert result.comparison_input.values == (2., None, 4.)
    assert result.original_row_indices == (0, 1, 2)
    assert assess(result.comparison_input, result.comparison_input).status == 'incompatible'
