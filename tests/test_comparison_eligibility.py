"""Contract tests for the research-only eligibility prototype."""
from dataclasses import replace
from pathlib import Path
import runpy

import pytest

contract = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'docs/Chunk_5/eligibility_contract.py'))
Input, assess = contract['ComparisonInput'], contract['assess']


def observation():
    return Input('synthetic-observation', 'a'*64, 'observation', 'transit_depth',
                 'microns', 'percent', 'synthetic-frame', 'synthetic-response-v1',
                 'explicit synthetic top-hat response, not NASA', (1., 2., 3.), (2., 2.1, 2.),
                 'independent_gaussian_1sigma', 'invented independent 1-sigma errors', (0.1, 0.1, 0.1))


def model():
    return replace(observation(), source_id='synthetic-model', source_sha256='b'*64,
                   role='forward_model', noise_kind='deterministic_model',
                   noise_evidence='invented deterministic curve', sigma=None)


def test_eligible_is_operation_specific_and_does_not_mutate_inputs():
    left, right = observation(), model()
    result = assess(left, right)
    assert result.status == 'eligible' and result.reasons == ()
    assert result.operation == 'aligned_residual_v1'
    assert left == observation() and right == model()
    assert assess(left, right, weighted=True).status == 'missing_requirements'
    assert assess(left, right, weighted=True, cross_dataset_independent=True).status == 'eligible'


@pytest.mark.parametrize('field', ['source_id', 'source_sha256', 'role', 'observable',
    'axis_unit', 'signal_unit', 'coordinate_frame', 'response_id', 'response_evidence'])
def test_missing_metadata_does_not_invent_compatibility(field):
    result = assess(replace(observation(), **{field: None}), model())
    assert result.status == 'missing_requirements'
    assert any(field in reason for reason in result.reasons)


@pytest.mark.parametrize('changes', [
    {'role': 'cross_section'}, {'observable': 'absorption_cross_section'},
    {'signal_unit': 'fraction'}, {'axis_unit': 'nanometers'},
    {'coordinate_frame': 'other-frame'}, {'response_id': 'other-response'},
    {'coordinates': (4., 5., 6.)}, {'coordinates': (1., 3., 2.)},
    {'values': (2., None, 2.)}, {'coordinates': (1., 2.)},
])
def test_incompatible_inputs_never_get_an_eligible_diagnostic(changes):
    assert assess(replace(observation(), **changes), model()).status == 'incompatible'


def test_returns_all_missing_reasons_and_explicit_no_overlap():
    result = assess(replace(observation(), source_id=None, response_evidence=None,
                            coordinates=(4., 5., 6.)), model())
    assert result.status == 'incompatible'
    assert 'left.source_id.missing' in result.reasons
    assert 'left.response_evidence.missing' in result.reasons
    assert 'pair.coverage.no_overlap' in result.reasons


@pytest.mark.parametrize('changes', [
    {'sigma': (0., 0.1, 0.1)}, {'sigma': (1e308, 0.1, 0.1)},
    {'noise_kind': 'asymmetric_intervals'}, {'noise_evidence': None},
    {'noise_kind': 'gaussian_covariance', 'sigma': None,
     'covariance': ((1., 2., 0.), (0., 1., 0.), (0., 0., 1.))},
    {'noise_kind': 'gaussian_covariance', 'sigma': None,
     'covariance': ((1., 1., 1.), (1., 1., 1.), (1., 1., 1.))},
])
def test_weighted_diagnostic_requires_usable_documented_errors(changes):
    left = replace(observation(), **changes)
    assert assess(left, model(), weighted=True, cross_dataset_independent=True).status != 'eligible'
    assert assess(left, model()).status == 'eligible'  # unweighted inspection does not infer errors


def test_valid_covariance_allowed_but_duplicate_observations_not_independent():
    left = replace(observation(), noise_kind='gaussian_covariance', sigma=None,
        covariance=((1., 0.2, 0.), (0.2, 1., 0.2), (0., 0.2, 1.)))
    assert assess(left, model(), weighted=True, cross_dataset_independent=True).status == 'eligible'
    result = assess(left, left, weighted=True, cross_dataset_independent=True)
    assert 'pair.same_source.cannot_assume_independence' in result.reasons


def test_two_deterministic_models_do_not_create_weighted_evidence():
    assert assess(model(), model(), weighted=True, cross_dataset_independent=True).status == 'incompatible'
