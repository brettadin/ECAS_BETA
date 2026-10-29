"""Tamper-evident persistence and reproducibility checks for comparison records.

Stores comparison configurations, transformation steps, eligibility verdicts,
and residual diagnostics inside a validated project folder under
projects/<project_id>/comparisons/*.json without altering SQLite schemas.
Saving a record never implies unconditional reproducibility; explicit
reproducibility limitations are recorded and verified on reload.
"""
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version as pkg_version
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from uuid import uuid4

import numpy as np

from ecas import persistence as project_persistence
from .alignment import TransformationStep, TransformedInput
from .eligibility import VERSION, ComparisonInput, Eligibility, assess
from .residuals import ResidualDiagnostic, evaluate_residuals

SCHEMA = 'ecas-comparison-record-v1'
MAX_RECORD_BYTES = 8 * 1024 * 1024
_HEX64 = re.compile(r'^[0-9a-fA-F]{64}$')


@dataclass(frozen=True)
class ReproducibilityCheck:
    matches_saved_verdict: bool
    matches_saved_diagnostics: bool
    recomputed_eligibility: Eligibility
    recomputed_diagnostic: ResidualDiagnostic | None
    limitations: tuple[str, ...]
    discrepancies: tuple[str, ...]


def _unwrap_input(item: ComparisonInput | TransformedInput) -> tuple[ComparisonInput, ComparisonInput, tuple[TransformationStep, ...]]:
    if isinstance(item, TransformedInput):
        return item.original, item.transformed, item.steps
    if isinstance(item, ComparisonInput):
        return item, item, ()
    raise TypeError('Expected ComparisonInput or TransformedInput')


def _input_to_dict(item: ComparisonInput) -> dict:
    return asdict(item)


def _dict_to_input(data: dict) -> ComparisonInput:
    cov = data.get('covariance')
    sigma = data.get('sigma')
    return ComparisonInput(
        source_id=data['source_id'],
        source_sha256=data['source_sha256'],
        role=data.get('role'),
        observable=data.get('observable'),
        axis_unit=data.get('axis_unit'),
        signal_unit=data.get('signal_unit'),
        coordinate_frame=data.get('coordinate_frame'),
        response_id=data.get('response_id'),
        response_evidence=data.get('response_evidence'),
        coordinates=tuple(data['coordinates']),
        values=tuple(data['values']),
        noise_kind=data.get('noise_kind'),
        noise_evidence=data.get('noise_evidence'),
        sigma=tuple(sigma) if sigma is not None else None,
        covariance=tuple(tuple(row) for row in cov) if cov is not None else None,
    )


def _canonical_digest(unsigned_envelope: dict) -> str:
    encoded = json.dumps(
        unsigned_envelope, sort_keys=True, separators=(',', ':'), allow_nan=False
    ).encode('utf-8')
    return sha256(encoded).hexdigest()


def build_comparison_record(
    left: ComparisonInput | TransformedInput,
    right: ComparisonInput | TransformedInput,
    *,
    weighted: bool = False,
    cross_dataset_independent: bool = False,
    left_provenance: dict | None = None,
    right_provenance: dict | None = None,
    limitations: Sequence[str] = (),
) -> dict:
    """Create a signed comparison result envelope with explicit provenance and limits."""
    left_orig, left_eval, left_steps = _unwrap_input(left)
    right_orig, right_eval, right_steps = _unwrap_input(right)

    eligibility = assess(
        left_eval,
        right_eval,
        weighted=weighted,
        cross_dataset_independent=cross_dataset_independent,
    )
    diagnostic = None
    if eligibility.status == 'eligible':
        diagnostic = evaluate_residuals(
            left_eval,
            right_eval,
            weighted=weighted,
            cross_dataset_independent=cross_dataset_independent,
        )

    recorded_limits: list[str] = [
        'Saved comparison records preserve evaluated arrays, hashes, transformations, '
        'and method version; independent raw-file re-ingestion requires access to the '
        'original source files or saved project attachments.'
    ]
    for label, inp in (('left', left_orig), ('right', right_orig)):
        if not isinstance(inp.source_sha256, str) or not _HEX64.fullmatch(inp.source_sha256):
            recorded_limits.append(
                f'{label} input lacks a valid raw-source SHA-256; byte-level source '
                'identity cannot be verified.'
            )
    if eligibility.status == 'eligible':
        recorded_limits.append(
            'Numerical residual diagnostics do not establish model adequacy, statistical '
            'detection significance, molecular presence, or atmospheric abundance.'
        )
    for note in limitations:
        if isinstance(note, str) and note.strip() and note not in recorded_limits:
            recorded_limits.append(note)

    envelope = {
        'schema': SCHEMA,
        'method_version': VERSION,
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'settings': {
            'weighted': bool(weighted),
            'cross_dataset_independent': bool(cross_dataset_independent),
        },
        'software_environment': {
            'python': sys.version.split()[0],
            'numpy': pkg_version('numpy'),
        },
        'left': {
            'original_input': _input_to_dict(left_orig),
            'evaluated_input': _input_to_dict(left_eval),
            'transformations': [asdict(step) for step in left_steps],
            'provenance': left_provenance,
        },
        'right': {
            'original_input': _input_to_dict(right_orig),
            'evaluated_input': _input_to_dict(right_eval),
            'transformations': [asdict(step) for step in right_steps],
            'provenance': right_provenance,
        },
        'eligibility': asdict(eligibility),
        'diagnostic': asdict(diagnostic) if diagnostic is not None else None,
        'reproducibility_limitations': recorded_limits,
    }
    # Ensure strict JSON serializability and finite numbers before signing
    envelope['integrity_sha256'] = _canonical_digest(envelope)
    encoded = json.dumps(envelope, allow_nan=False).encode('utf-8')
    if len(encoded) > MAX_RECORD_BYTES:
        raise ValueError('Comparison record exceeds 8 MiB limit')
    return json.loads(encoded.decode('utf-8'))


def _comparisons_dir(project_id: str, projects_dir: Path) -> Path:
    root = Path(projects_dir)
    if root.is_symlink() or root.is_junction():
        raise project_persistence.PersistenceError('Linked project roots are unsupported')
    database = project_persistence._checked_project_database(project_id, root)
    if not database.is_file():
        raise project_persistence.DatabaseNotFoundError(
            f'Project {project_id!r} does not exist'
        )
    comp_dir = database.parent / 'comparisons'
    if comp_dir.exists() and (comp_dir.is_symlink() or comp_dir.is_junction()):
        raise project_persistence.PersistenceError('Linked comparisons directory is unsupported')
    return comp_dir


def verify_comparison_record(record: dict) -> dict:
    """Validate schema, required sections, and SHA-256 integrity signature."""
    if not isinstance(record, dict) or record.get('schema') != SCHEMA:
        raise ValueError('Unsupported comparison record schema')
    expected_sig = record.get('integrity_sha256')
    if not isinstance(expected_sig, str) or not _HEX64.fullmatch(expected_sig):
        raise ValueError('Missing or invalid comparison record integrity_sha256')
    unsigned = {k: v for k, v in record.items() if k != 'integrity_sha256'}
    if _canonical_digest(unsigned) != expected_sig.lower():
        raise ValueError('Comparison record failed integrity verification')
    for required in ('method_version', 'settings', 'left', 'right', 'eligibility', 'reproducibility_limitations'):
        if required not in unsigned:
            raise ValueError(f'Missing required comparison record field: {required}')
    # Reconstruct inputs to ensure structural validity
    _dict_to_input(unsigned['left']['original_input'])
    _dict_to_input(unsigned['left']['evaluated_input'])
    _dict_to_input(unsigned['right']['original_input'])
    _dict_to_input(unsigned['right']['evaluated_input'])
    return record


def save_comparison_record(project_id: str, projects_dir: Path, record: dict) -> Path:
    """Atomically persist a verified comparison record inside the project directory."""
    verify_comparison_record(record)
    encoded = json.dumps(record, allow_nan=False, indent=2).encode('utf-8')
    if len(encoded) > MAX_RECORD_BYTES:
        raise ValueError('Comparison record exceeds 8 MiB limit')

    comp_dir = _comparisons_dir(project_id, projects_dir)
    comp_dir.mkdir(parents=True, exist_ok=True)
    target = comp_dir / f'{uuid4().hex}.json'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=comp_dir, prefix='comparison-', suffix='.tmp', delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return target


def load_comparison_record(path: str | Path) -> dict:
    """Load and integrity-verify a single saved comparison record."""
    target = Path(path)
    if target.is_symlink() or target.is_junction():
        raise ValueError('Linked comparison record file is unsupported')
    with target.open('rb') as stream:
        raw = stream.read(MAX_RECORD_BYTES + 1)
    if len(raw) > MAX_RECORD_BYTES:
        raise ValueError('Comparison record exceeds 8 MiB limit')
    data = json.loads(raw.decode('utf-8'))
    return verify_comparison_record(data)


def load_comparison_records(project_id: str, projects_dir: Path) -> tuple[list[tuple[Path, dict]], int]:
    """Return validated `(path, record)` pairs and count of invalid/corrupted files."""
    comp_dir = _comparisons_dir(project_id, projects_dir)
    if not comp_dir.exists():
        return [], 0
    valid: list[tuple[Path, dict]] = []
    invalid = 0
    for path in sorted(comp_dir.glob('*.json')):
        try:
            valid.append((path, load_comparison_record(path)))
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            invalid += 1
    return valid, invalid


def reproduce_comparison_record(record: dict, *, rtol: float = 1e-12, atol: float = 1e-12) -> ReproducibilityCheck:
    """Re-execute eligibility and residual diagnostics from a verified saved record."""
    verify_comparison_record(record)
    discrepancies: list[str] = []
    if record['method_version'] != VERSION:
        discrepancies.append(
            f'Saved method_version {record["method_version"]!r} differs from current {VERSION!r}'
        )

    left_eval = _dict_to_input(record['left']['evaluated_input'])
    right_eval = _dict_to_input(record['right']['evaluated_input'])
    weighted = bool(record['settings']['weighted'])
    independent = bool(record['settings']['cross_dataset_independent'])

    recomputed_elig = assess(
        left_eval, right_eval, weighted=weighted, cross_dataset_independent=independent
    )
    saved_elig = record['eligibility']
    verdict_ok = (
        recomputed_elig.operation == saved_elig['operation']
        and recomputed_elig.status == saved_elig['status']
        and list(recomputed_elig.reasons) == list(saved_elig['reasons'])
    )
    if not verdict_ok:
        discrepancies.append('Recomputed eligibility verdict or reasons differ from saved record')

    recomputed_diag = None
    diag_ok = True
    saved_diag = record.get('diagnostic')
    if recomputed_elig.status == 'eligible':
        recomputed_diag = evaluate_residuals(
            left_eval, right_eval, weighted=weighted, cross_dataset_independent=independent
        )
        if saved_diag is None:
            diag_ok = False
            discrepancies.append('Recomputed run is eligible, but saved diagnostic is None')
        else:
            if not np.allclose(recomputed_diag.residuals, saved_diag['residuals'], rtol=rtol, atol=atol):
                diag_ok = False
                discrepancies.append('Recomputed residual array differs beyond tolerance')
            if weighted:
                if saved_diag.get('weighted_residual_quadratic') is None or not np.isclose(
                    recomputed_diag.weighted_residual_quadratic,
                    saved_diag['weighted_residual_quadratic'],
                    rtol=rtol,
                    atol=atol,
                ):
                    diag_ok = False
                    discrepancies.append('Recomputed weighted quadratic differs beyond tolerance')
    elif saved_diag is not None:
        diag_ok = False
        discrepancies.append('Recomputed run is not eligible, but saved record contains a diagnostic')

    return ReproducibilityCheck(
        matches_saved_verdict=verdict_ok and (record['method_version'] == VERSION),
        matches_saved_diagnostics=diag_ok,
        recomputed_eligibility=recomputed_elig,
        recomputed_diagnostic=recomputed_diag,
        limitations=tuple(record['reproducibility_limitations']),
        discrepancies=tuple(discrepancies),
    )

