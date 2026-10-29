"""Project attachment use cases; SQL stays in persistence and UI stays separate."""
import base64
from dataclasses import dataclass
from hashlib import sha256
import json
import sqlite3
from pathlib import Path

from ecas import persistence
from ecas.comparison.persistence import load_comparison_records, save_comparison_record
from ecas.ingestion.import_manager import import_spectrum
from ecas.ingestion.nasa_archive import read_cached
from ecas.ingestion.nasa_table import TransmissionTable, import_transmission_table
from ecas.models.spectrum import SpectrumData

MAX_SOURCE_BYTES = 16 * 1024 * 1024


def _source_bytes(source):
    with source.open('rb') as stream:
        raw = stream.read(MAX_SOURCE_BYTES + 1)
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError('Project source exceeds 16 MiB limit')
    return raw


def _payload(spectrum):
    return dict(source_file=str(spectrum.source_file), rows=spectrum.rows,
                columns=spectrum.columns, axis_unit=spectrum.axis_unit,
                signal_unit=spectrum.signal_unit, signal_type=spectrum.signal_type,
                warnings=spectrum.warnings)


def _digest(spectrum, attachment, *, source_file=None):
    payload = _payload(spectrum)
    if source_file is not None:
        payload['source_file'] = source_file
    return sha256(json.dumps(dict(spectrum=payload, attachment=attachment),
                             sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _verified(spectrum, attachment, *, source_file=None):
    if not isinstance(attachment, dict) or attachment.get('schema') != 'ecas-project-source-v1':
        raise ValueError('Unsupported project source record')
    unsigned = {key: value for key, value in attachment.items() if key != 'integrity_sha256'}
    if _digest(spectrum, unsigned, source_file=source_file) != attachment.get('integrity_sha256'):
        raise ValueError('Saved spectrum or provenance changed')
    raw = base64.b64decode(attachment['source_bytes'], validate=True)
    if len(raw) > MAX_SOURCE_BYTES or sha256(raw).hexdigest() != attachment['source_sha256']:
        raise ValueError('Saved source failed integrity validation')
    # v1 hashes include the original path spelling. Verify that exact persisted
    # spelling before adapting the envelope to this platform's Path rendering.
    # This keeps old databases valid and allows verified copies between projects.
    if source_file is not None and source_file != str(spectrum.source_file):
        return dict(unsigned, integrity_sha256=_digest(spectrum, unsigned))
    return attachment


@dataclass(frozen=True)
class ProjectSpectrum:
    record_id: int
    spectrum: SpectrumData
    attachment: dict | None

    @property
    def details(self):
        if self.attachment is None or 'table_metadata' not in self.attachment['provenance']:
            return None
        data = self.attachment['provenance']
        return TransmissionTable(self.spectrum, tuple(map(tuple, data['table_metadata'])),
                                 tuple(map(tuple, data['column_units'])), self.attachment['source_sha256'])

    @property
    def import_schema(self):
        return self.attachment['provenance'].get('import_schema') if self.attachment else None


class ProjectStore:
    def __init__(self, root):
        self.root = Path(root)
        if self.root.is_symlink() or self.root.is_junction():
            raise persistence.PersistenceError('Linked project roots are unsupported')

    def projects(self):
        return persistence.list_project_ids(self.root)

    def create(self, name):
        persistence.create_project(name, self.root)

    def attach(self, name, spectrum, schema=None, existing_attachment=None, *, expected_source_sha256=None):
        """Snapshot a validated local source, or copy a verified saved attachment.

        The original path remains origin metadata. Reopening uses saved values and
        source bytes, so neither the cache nor the original file is a dependency.
        """
        try:
            database = persistence._checked_project_database(name, self.root)
            if not database.is_file():
                raise ValueError('Create or select an existing project first')
            if existing_attachment is not None:
                attachment = _verified(spectrum, existing_attachment)
            else:
                source = spectrum.source_file
                raw = _source_bytes(source)
                if expected_source_sha256 is not None and sha256(raw).hexdigest() != expected_source_sha256:
                    raise ValueError('Source changed since import; reimport it before attaching')
                provenance = dict(original_path=str(source), import_schema=schema)
                if source.suffix.lower() == '.tbl':
                    details = import_transmission_table(source)
                    parsed = details.spectrum
                    if sha256(raw).hexdigest() != details.source_sha256:
                        raise ValueError('Source changed while attaching')
                    provenance.update(import_schema=None, table_metadata=details.metadata, column_units=details.column_units)
                    if source.name == 'source.tbl' and (source.parent / 'record.json').exists():
                        record, _ = read_cached(source.parent)
                        metadata = (source.parent / 'metadata.json').read_bytes()
                        if record['sha256'] != details.source_sha256 or sha256(metadata).hexdigest() != record['metadata_sha256']:
                            raise ValueError('Cache provenance changed while attaching')
                        provenance.update(cache_record=record, metadata_bytes=base64.b64encode(metadata).decode('ascii'))
                else:
                    parsed = import_spectrum(source, archive_schema=schema)
                    if _source_bytes(source) != raw:
                        raise ValueError('Source changed while attaching')
                if parsed != spectrum:
                    raise ValueError('Source no longer matches the displayed spectrum; reimport it first')
                attachment = dict(schema='ecas-project-source-v1', source_name=source.name,
                                  source_sha256=sha256(raw).hexdigest(), source_bytes=base64.b64encode(raw).decode('ascii'),
                                  provenance=provenance)
                attachment['integrity_sha256'] = _digest(spectrum, attachment)
            size = len(json.dumps(dict(_payload(spectrum), attachment=attachment), allow_nan=False).encode())
            if size > 64 * 1024 * 1024:
                raise ValueError('Project spectrum exceeds 64 MiB record limit')
            return persistence.save_spectrum_to_database(spectrum, name, self.root, attachment=attachment)
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            raise persistence.PersistenceError(f'Could not attach spectrum: {error}') from error

    def spectra(self, name):
        try:
            result = []
            for identifier, data in persistence.load_spectrum_records(name, self.root):
                spectrum = persistence._to_spectrums_dict(data)
                attachment = _verified(spectrum, data['attachment'], source_file=data['source_file']) if 'attachment' in data else None
                result.append(ProjectSpectrum(identifier, spectrum, attachment))
            return result
        except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
            raise persistence.PersistenceError(f'Could not validate project spectra: {error}') from error

    def save_comparison(self, name, record):
        """Persist a verified comparison record inside the project directory."""
        try:
            return save_comparison_record(name, self.root, record)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise persistence.PersistenceError(f'Could not save comparison record: {error}') from error

    def comparisons(self, name):
        """Return `(valid_records, invalid_count)` for saved comparison records in `name`."""
        try:
            return load_comparison_records(name, self.root)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise persistence.PersistenceError(f'Could not load comparison records: {error}') from error
