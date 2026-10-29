"""Tests for comparison record persistence, reproducibility checks, and forward-model contract."""
from dataclasses import replace
import json
from pathlib import Path

import pytest

from ecas.comparison.alignment import convert_signal_unit
from ecas.comparison.eligibility import ComparisonInput
from ecas.comparison.forward_model import (
    MODEL_FILE_SCHEMA,
    AtmosphericModelProvenance,
    OpacitySourceSpec,
    UnsupportedProjectionError,
    forward_model_input,
    load_forward_model_file,
    project_cross_section_to_transit_depth,
)
from ecas.comparison.inputs import observation_input, reference_input
from ecas.comparison.persistence import (
    build_comparison_record,
    load_comparison_record,
    reproduce_comparison_record,
)
from ecas.ingestion.exomol_product import ProductRequest, validate_product
from ecas.ingestion.exomol_product_network import RetrievedCrossSection
from ecas.ingestion.nasa_table import import_transmission_table
from ecas.persistence import PersistenceError
from ecas.projects import ProjectStore

ROOT = Path(__file__).resolve().parents[1]


def sample_model_provenance():
    return AtmosphericModelProvenance(
        engine_name='synthetic-rt-solver',
        engine_version='0.1.0-test',
        temperature_pressure_profile='isothermal 1100 K synthetic test profile',
        abundance_convention='volume_mixing_ratio',
        species_parameters=(('CO2', 1e-4), ('H2O', 1e-3)),
        opacity_sources=(
            OpacitySourceSpec(
                formula='CO2',
                isotopologue='12C-16O2',
                dataset='UCL-4000',
                version='20200601',
                source_sha256='c' * 64,
            ),
        ),
        gravity_m_s2=4.26,
        reference_pressure_bar=0.01,
        planet_radius_m=9.1e7,
        stellar_radius_m=6.26e8,
        continuum_and_clouds='H2-He Rayleigh + gray deck at 1 mbar (synthetic)',
    )


def test_forward_model_contract_enforces_provenance_and_blocks_adhoc_projection():
    prov = sample_model_provenance()
    model_inp = forward_model_input(
        source_id='synthetic-rt-curve',
        source_sha256='b' * 64,
        provenance=prov,
        axis_unit='microns',
        signal_unit='fraction',
        coordinate_frame='barycentric-synthetic',
        response_id='synthetic-tophat-v1',
        response_evidence='synthetic bin-integrated curve',
        coordinates=(1.0, 2.0, 3.0),
        values=(0.020, 0.021, 0.019),
    )
    assert model_inp.role == 'forward_model'
    assert model_inp.observable == 'transit_depth'
    assert model_inp.noise_kind == 'deterministic_model'

    # Missing or nonpositive physical parameters must be rejected
    with pytest.raises(ValueError, match='stellar_radius_m'):
        forward_model_input(
            source_id='bad',
            source_sha256='b' * 64,
            provenance=replace(prov, stellar_radius_m=0.0),
            axis_unit='microns',
            signal_unit='percent',
            coordinate_frame='barycentric-synthetic',
            response_id='synthetic-tophat-v1',
            response_evidence='synthetic',
            coordinates=(1.0, 2.0, 3.0),
            values=(2.0, 2.1, 1.9),
        )

    # Cross-section units must never enter forward_model_input
    with pytest.raises(ValueError, match='signal_unit'):
        forward_model_input(
            source_id='bad',
            source_sha256='b' * 64,
            provenance=prov,
            axis_unit='microns',
            signal_unit='cm^2/molecule',
            coordinate_frame='barycentric-synthetic',
            response_id='synthetic-tophat-v1',
            response_evidence='synthetic',
            coordinates=(1.0, 2.0, 3.0),
            values=(1e-24, 2e-24, 1e-24),
        )

    with pytest.raises(UnsupportedProjectionError):
        project_cross_section_to_transit_depth()


def test_eligible_transformed_comparison_persists_verifies_and_reproduces(tmp_path):
    projects_dir = tmp_path / 'projects'
    store = ProjectStore(projects_dir)
    store.create('wasp39-study')

    csv_file = tmp_path / 'obs.csv'
    csv_file.write_text('wavelength,signal\n1.0,2.0\n2.0,2.2\n3.0,1.9\n', encoding='utf-8')
    from ecas.ingestion.import_manager import import_spectrum
    store.attach('wasp39-study', import_spectrum(csv_file))

    obs = ComparisonInput(
        source_id='synthetic-obs',
        source_sha256='a' * 64,
        role='observation',
        observable='transit_depth',
        axis_unit='microns',
        signal_unit='percent',
        coordinate_frame='barycentric-synthetic',
        response_id='synthetic-tophat-v1',
        response_evidence='synthetic bins',
        coordinates=(1.0, 2.0, 3.0),
        values=(2.0, 2.2, 1.9),
        noise_kind='independent_gaussian_1sigma',
        noise_evidence='synthetic 1-sigma',
        sigma=(0.1, 0.1, 0.1),
    )
    prov = sample_model_provenance()
    model_frac = forward_model_input(
        source_id='synthetic-rt-curve',
        source_sha256='b' * 64,
        provenance=prov,
        axis_unit='microns',
        signal_unit='fraction',
        coordinate_frame='barycentric-synthetic',
        response_id='synthetic-tophat-v1',
        response_evidence='synthetic bins',
        coordinates=(1.0, 2.0, 3.0),
        values=(0.020, 0.021, 0.020),
    )
    transformed_model = convert_signal_unit(model_frac, 'percent')

    record = build_comparison_record(
        obs,
        transformed_model,
        weighted=True,
        cross_dataset_independent=True,
        right_provenance={'engine': prov.engine_name, 'version': prov.engine_version},
    )
    saved_path = store.save_comparison('wasp39-study', record)
    assert saved_path.is_file()

    # Coexistence with existing project spectra and project listing
    assert store.projects() == ['wasp39-study']
    assert len(store.spectra('wasp39-study')) == 1

    loaded_records, invalid = store.comparisons('wasp39-study')
    assert len(loaded_records) == 1 and invalid == 0
    _, loaded = loaded_records[0]
    assert loaded['right']['original_input']['signal_unit'] == 'fraction'
    assert loaded['right']['evaluated_input']['signal_unit'] == 'percent'
    assert loaded['right']['transformations'][0]['operation'] == 'convert_signal_unit_v1'

    repro = reproduce_comparison_record(loaded)
    assert repro.matches_saved_verdict is True
    assert repro.matches_saved_diagnostics is True
    assert repro.discrepancies == ()
    assert any('original source files' in lim for lim in repro.limitations)

    # Corrupting a saved record is detected on reload
    tampered = json.loads(saved_path.read_text(encoding='utf-8'))
    tampered['diagnostic']['rms_residual'] = 0.0
    bad_path = saved_path.parent / 'tampered.json'
    bad_path.write_text(json.dumps(tampered), encoding='utf-8')
    with pytest.raises(ValueError, match='integrity'):
        load_comparison_record(bad_path)
    valid_after, invalid_after = store.comparisons('wasp39-study')
    assert len(valid_after) == 1 and invalid_after == 1

    # Nonexistent or traversal project IDs are rejected
    with pytest.raises(PersistenceError):
        store.save_comparison('nonexistent-project', record)
    with pytest.raises(PersistenceError):
        store.save_comparison('../escape', record)


def test_blocked_cross_section_comparison_record_preserves_reasons_without_diagnostics(tmp_path):
    details = import_transmission_table(ROOT / 'data/NASA/2026-10-27/feinstein-2023.tbl')
    obs = observation_input(details.spectrum, details.source_sha256)
    request = ProductRequest(4000, 4010, 500, '1')
    raw = (ROOT / 'data/ExoMol/2026-10-28/CO2-12C-16O2-500K-4000-4010-dnu1.sigma').read_bytes()
    ref = reference_input(RetrievedCrossSection(request, raw, validate_product(raw, request)))

    record = build_comparison_record(obs.comparison_input, ref.comparison_input)
    assert record['eligibility']['status'] == 'incompatible'
    assert record['diagnostic'] is None
    repro = reproduce_comparison_record(record)
    assert repro.matches_saved_verdict is True
    assert repro.matches_saved_diagnostics is True
    assert repro.recomputed_diagnostic is None


def test_load_forward_model_file_binds_raw_sha256_and_validates_schema_and_units(tmp_path):
    from hashlib import sha256

    payload = {
        'schema': MODEL_FILE_SCHEMA,
        'source_id': 'wasp39-co2-nm-model',
        'axis_unit': 'nanometers',
        'signal_unit': 'fraction',
        'coordinate_frame': 'barycentric',
        'response_id': None,
        'response_evidence': None,
        'coordinates': [1000.0, 2000.0, 3000.0],
        'values': [0.020, 0.021, 0.019],
        'provenance': {
            'engine_name': 'synthetic-rt-solver',
            'engine_version': '0.1.0-test',
            'temperature_pressure_profile': 'isothermal 1100 K',
            'abundance_convention': 'volume_mixing_ratio',
            'species_parameters': {'CO2': 1e-4, 'H2O': 1e-3},
            'opacity_sources': [
                {
                    'formula': 'CO2',
                    'isotopologue': '12C-16O2',
                    'dataset': 'UCL-4000',
                    'version': '20200601',
                    'source_sha256': 'd' * 64,
                }
            ],
            'gravity_m_s2': 4.26,
            'reference_pressure_bar': 0.01,
            'planet_radius_m': 9.1e7,
            'stellar_radius_m': 6.26e8,
            'continuum_and_clouds': 'H2-He Rayleigh + gray deck at 1 mbar',
        },
    }
    model_path = tmp_path / 'model.json'
    model_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    expected_sha = sha256(model_path.read_bytes()).hexdigest()

    loaded = load_forward_model_file(model_path)
    assert loaded.raw_sha256 == expected_sha
    assert loaded.comparison_input.source_sha256 == expected_sha
    # Native units and unestablished response stay untouched on load
    assert loaded.comparison_input.axis_unit == 'nanometers'
    assert loaded.comparison_input.coordinates == (1000.0, 2000.0, 3000.0)
    assert loaded.comparison_input.response_id is None

    # Reject wrong schema
    bad_schema = tmp_path / 'bad_schema.json'
    bad_schema.write_text(json.dumps({**payload, 'schema': 'wrong'}), encoding='utf-8')
    with pytest.raises(ValueError, match='schema'):
        load_forward_model_file(bad_schema)

    # Reject wavenumber / cross-section masquerading as forward model
    bad_axis = tmp_path / 'bad_axis.json'
    bad_axis.write_text(json.dumps({**payload, 'axis_unit': 'cm^-1'}), encoding='utf-8')
    with pytest.raises(ValueError, match='axis_unit'):
        load_forward_model_file(bad_axis)

    # Reject boolean values masquerading as numbers
    bad_bool = tmp_path / 'bad_bool.json'
    bad_bool.write_text(json.dumps({**payload, 'values': [True, 0.02, 0.019]}), encoding='utf-8')
    with pytest.raises(ValueError, match='finite numbers'):
        load_forward_model_file(bad_bool)


