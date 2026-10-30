"""Portable batch identification records: saved inputs, integrity and reproduction."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from ecas.identification.engine import identify, verify_record as verify_result
from ecas.identification.library import ReferenceDataset
from ecas.models.spectrum import SpectrumData
from ecas.observations import ObservationContext

SCHEMA = 'ecas-identification-batch-v1'
MAX_BYTES = 64 * 1024 * 1024


def _spectrum(data):
    return SpectrumData(Path(data['source_file']), tuple(data['rows']), tuple(data['columns']),
                        data.get('axis_unit'), data.get('signal_unit'), data.get('signal_type'),
                        tuple(data.get('warnings', ())), tuple(tuple(x) for x in data.get('metadata', ())))


def verify_record(record):
    try:
        payload = record['payload']
        encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        if record['schema'] != SCHEMA or sha256(encoded).hexdigest() != record['sha256']:
            raise ValueError('Identification record integrity check failed')
        if len(encoded) > MAX_BYTES or not payload['observations']:
            raise ValueError('Empty or oversized identification record')
        if len(payload['observations']) != len(payload['results']) or not all(verify_result(r) for r in payload['results']):
            raise ValueError('Identification result records are incomplete or changed')
        return record
    except (KeyError, TypeError, OverflowError) as exc:
        raise ValueError('Malformed identification record') from exc


def save_record(path, record):
    verify_record(record)
    encoded = json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8')
    if len(encoded) > MAX_BYTES:
        raise ValueError('Identification record exceeds 64 MiB')
    target = Path(path)
    if target.is_symlink() or target.is_junction():
        raise ValueError('Linked identification record targets are unsupported')
    target.write_bytes(encoded)


def load_record(path):
    with Path(path).open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('Identification record exceeds 64 MiB')
    try:
        return verify_record(json.loads(raw))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Invalid identification JSON') from exc


def reproduce_record(record):
    """Re-evaluate saved arrays without requiring original files; no raw-file claim."""
    payload = verify_record(record)['payload']
    refs = [ReferenceDataset(r['dataset_id'], r['molecule'], r['modality'], _spectrum(r['spectrum']),
                             r['metadata'], r['source_sha256'], Path(r['source_path']))
            for r in payload['references']]
    results = []
    for observation, saved in zip(payload['observations'], payload['results']):
        original = saved['payload']
        settings = original['settings']
        if settings['method'] != 'ecas-v1-drop-one-bvls-v1':
            raise ValueError('Unsupported identification method version')
        result = identify(_spectrum(observation['spectrum']), refs,
                          observation_metadata=observation['metadata'],
                          threshold=settings['threshold'], continuum=settings['continuum'])
        if len(result.components) != len(original['components']):
            raise ValueError('Reproduced component count differs')
        for actual, expected in zip(result.components, original['components']):
            if actual.dataset_id != expected['dataset_id'] or actual.status != expected['status']:
                raise ValueError('Reproduced candidate identity/status differs')
            for field in ('sigma', 'amplitude', 'uncertainty', 'delta_chi2'):
                a, b = getattr(actual, field), expected[field]
                if (a is None) != (b is None) or (a is not None and not np.isclose(a, b, rtol=1e-8, atol=1e-12)):
                    raise ValueError(f'Reproduced {field} differs')
        for field in ('x', 'observed', 'model', 'sigma_values'):
            actual = np.asarray(getattr(result, field))
            expected = np.asarray(original[field])
            if actual.shape != expected.shape or not np.allclose(actual, expected, rtol=1e-8, atol=1e-30):
                raise ValueError(f'Reproduced {field} differs')
        results.append(result)
    return tuple(results)


def record_inputs(record):
    payload = verify_record(record)['payload']
    refs = tuple(ReferenceDataset(r['dataset_id'], r['molecule'], r['modality'], _spectrum(r['spectrum']),
                                  r['metadata'], r['source_sha256'], Path(r['source_path']))
                 for r in payload['references'])
    def context(r):
        return ObservationContext(r['observation_id'], r['label'], _spectrum(r['spectrum']),
                                  r['source_sha256'], r['metadata'])
    return tuple(context(r) for r in payload['observations']), refs, tuple(context(r) for r in payload.get('duplicates', ()))
