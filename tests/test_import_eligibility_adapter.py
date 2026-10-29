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


def test_production_observation_and_reference_inputs_preserve_provenance_and_block_cross_sections():
    from ecas.comparison.eligibility import assess as prod_assess
    from ecas.comparison.inputs import observation_input, reference_input
    from ecas.ingestion.exomol_product import ProductRequest, validate_product
    from ecas.ingestion.exomol_product_network import RetrievedCrossSection

    details = import_transmission_table(ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl')
    obs = observation_input(details.spectrum, details.source_sha256)
    assert obs.comparison_input.source_sha256 == details.source_sha256
    assert obs.comparison_input.observable == 'transit_depth'
    assert obs.comparison_input.axis_unit == 'microns'
    assert obs.comparison_input.signal_unit == 'percent'
    assert obs.comparison_input.role is None
    assert obs.comparison_input.noise_kind is None
    assert dict(obs.raw_uncertainty_columns)['pl_trandeperr2'][0] < 0

    request = ProductRequest(4000, 4010, 500, '1')
    raw = (ROOT / 'data/ExoMol/2026-10-28/CO2-12C-16O2-500K-4000-4010-dnu1.sigma').read_bytes()
    product = validate_product(raw, request)
    ref = reference_input(RetrievedCrossSection(request, raw, product))
    assert ref.comparison_input == reference_input(product).comparison_input
    assert ref.comparison_input.source_id == product.provenance.source_url
    assert ref.comparison_input.source_sha256 == product.source_sha256
    assert ref.comparison_input.role == 'calculated_absorption_cross_section'
    assert ref.comparison_input.observable == 'absorption_cross_section'
    assert ref.comparison_input.axis_unit == 'cm^-1'
    assert ref.comparison_input.signal_unit == 'cm^2/molecule'
    assert ref.comparison_input.coordinates == tuple(p[0] for p in product.points)
    assert ref.comparison_input.values == tuple(p[1] for p in product.points)

    eligibility = prod_assess(obs.comparison_input, ref.comparison_input)
    assert eligibility.status == 'incompatible'
    assert 'right.role.requires_physical_model_or_supported_role' in eligibility.reasons
    assert 'right.observable.unsupported_in_v1' in eligibility.reasons
    assert 'pair.observable.mismatch_explicit_transformation_required' in eligibility.reasons
    assert 'pair.axis_unit.mismatch_explicit_transformation_required' in eligibility.reasons
    assert 'pair.signal_unit.mismatch_explicit_transformation_required' in eligibility.reasons
