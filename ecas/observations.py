"""Independent observation identities shared by selection and batch analysis."""
from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path

from ecas.models.spectrum import SpectrumData


def hash_source_file(path):
    """Hash source bytes with bounded memory, including large FITS containers."""
    digest = sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class ObservationContext:
    observation_id: str
    label: str
    spectrum: SpectrumData
    source_sha256: str | None
    metadata: dict

    @property
    def planet(self):
        return self.metadata.get('pl_name') or self.metadata.get('PL_NAME') or ''


def observation_context(spectrum, source_sha256=None, metadata=None, label=None):
    facts = dict(spectrum.metadata)
    facts.update(deepcopy(metadata or {}))
    facts['source_sha256'] = source_sha256
    snapshot_hash = sha256(json.dumps(asdict(spectrum), default=str, sort_keys=True,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()
    identity = (f"project:{facts['project_id']}:{facts['project_record_id']}"
                if facts.get('project_id') and facts.get('project_record_id')
                else f"source:{source_sha256}" if source_sha256 else f"snapshot:{snapshot_hash}")
    return ObservationContext(identity, label or spectrum.source_file.name,
                              deepcopy(spectrum), source_sha256, facts)


def project_observation(project_id, record):
    attachment = record.attachment or {}
    provenance = attachment.get('provenance', {})
    table = dict(provenance.get('table_metadata', ()))
    archive = provenance.get('cache_record', {}).get('metadata', {})
    facts = dict(record.spectrum.metadata)
    # Keep both original descriptions, including differences in publication year.
    facts.update(source_table_metadata=table, archive_metadata=deepcopy(archive),
                 project_id=project_id, project_record_id=str(record.record_id))
    for target, archive_key, table_key in (
        ('pl_name', 'pl_name', 'PL_NAME'), ('reference', 'authors', 'REFERENCE'),
        ('instrument', 'instrument', 'INSTRUMENT'), ('facility', 'facility', 'FACILITY'),
        ('spec_type', 'spec_type', 'SPEC_TYPE')):
        if archive.get(archive_key) or table.get(table_key):
            facts[target] = archive.get(archive_key) or table.get(table_key)
    for key in ('bibcode', 'spec_path'):
        if archive.get(key):
            facts[key] = archive[key]
    label = ' | '.join(str(facts[k]) for k in ('pl_name', 'instrument', 'reference') if facts.get(k))
    label = f"{record.record_id}: {label or Path(record.spectrum.source_file).name}"
    return observation_context(record.spectrum, attachment.get('source_sha256'), facts, label)


def independent_observations(contexts):
    """Retain one evaluation per raw product while reporting duplicate identities."""
    unique, duplicates, seen = [], [], set()
    for item in contexts:
        key = item.source_sha256 or item.observation_id
        if key in seen:
            duplicates.append(item)
        else:
            seen.add(key)
            unique.append(item)
    return tuple(unique), tuple(duplicates)
