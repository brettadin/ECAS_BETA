"""Atomic single-snapshot catalogue cache; raw metadata stay provenance-bound."""
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

from .exomol_catalogue import CatalogueError, parse_catalogue

CATALOGUE_URL = 'https://www.exomol.com/db/exomol.all'
MAX_CACHE_BYTES = 2*1024*1024


@dataclass(frozen=True)
class CatalogueSnapshot:
    catalogue: object
    retrieved_utc: str


def _path(root):
    root = Path(root)
    path = root/'catalogue.json'
    if root.is_symlink() or root.is_junction() or path.is_symlink() or path.is_junction():
        raise CatalogueError('Linked catalogue cache paths are unsupported')
    return path


def store_catalogue(root, raw):
    catalogue = parse_catalogue(raw)
    stamp = datetime.now(timezone.utc).isoformat()
    envelope = dict(schema='ecas-exomol-catalogue-v1', source_url=CATALOGUE_URL,
        retrieved_utc=stamp, sha256=catalogue.source_sha256, raw_base64=base64.b64encode(raw).decode('ascii'))
    encoded = json.dumps(envelope, separators=(',', ':')).encode()
    if len(encoded)>MAX_CACHE_BYTES:
        raise CatalogueError('Catalogue cache exceeds 2 MiB')
    path = _path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='catalogue-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return CatalogueSnapshot(catalogue, stamp)


def load_catalogue(root):
    path = _path(root)
    if not path.exists():
        return None
    with path.open('rb') as stream:
        encoded = stream.read(MAX_CACHE_BYTES+1)
    if len(encoded)>MAX_CACHE_BYTES:
        raise CatalogueError('Catalogue cache exceeds 2 MiB')
    try:
        envelope = json.loads(encoded)
        if not isinstance(envelope, dict) or set(envelope) != {'schema', 'source_url', 'retrieved_utc', 'sha256', 'raw_base64'}:
            raise ValueError('fields')
        if envelope['schema'] != 'ecas-exomol-catalogue-v1' or envelope['source_url'] != CATALOGUE_URL:
            raise ValueError('source/schema')
        stamp = datetime.fromisoformat(envelope['retrieved_utc'])
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError('timestamp must include UTC offset')
        raw = base64.b64decode(envelope['raw_base64'], validate=True)
        catalogue = parse_catalogue(raw)
        if catalogue.source_sha256 != envelope['sha256']:
            raise ValueError('source hash mismatch')
        return CatalogueSnapshot(catalogue, envelope['retrieved_utc'])
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError) as error:
        raise CatalogueError(f'Invalid catalogue cache: {error}') from error
