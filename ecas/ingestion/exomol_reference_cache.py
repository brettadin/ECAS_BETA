"""Atomic reference envelopes retain raw bytes, exact settings and provenance."""
import base64
from dataclasses import asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import re
from pathlib import Path
import tempfile
from uuid import uuid4

from .exomol_product import CITATIONS, ProductRequest, validate_product
from .exomol_product_network import RetrievedCrossSection

MAX_CACHE_BYTES=2*1024*1024


def _root(root):
    root=Path(root)
    if root.is_symlink() or root.is_junction(): raise ValueError('Linked reference cache is unsupported')
    return root


def _context(context, request):
    if context is None: return
    if not isinstance(context,dict) or set(context)!={'formula','isotopologue','dataset','version','catalogue_sha256'}:
        raise ValueError('Invalid selected catalogue context')
    service=request.service
    if (context['formula'],context['isotopologue'],context['dataset'])!=(service.formula,service.isotopologue,service.dataset):
        raise ValueError('Selected catalogue identity differs from supported service')
    if not isinstance(context['version'],str) or not re.fullmatch('[0-9]{8}',context['version']):
        raise ValueError('Invalid catalogue version label')
    if not isinstance(context['catalogue_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',context['catalogue_sha256']):
        raise ValueError('Invalid catalogue source hash')


def store_reference(root, result, *, catalogue_context=None):
    # Recompute from raw bytes/settings; never trust a separately supplied parsed product.
    checked=validate_product(result.raw,result.request)
    if checked!=result.product: raise ValueError('Reference payload and parsed provenance disagree')
    _context(catalogue_context, result.request)
    envelope=dict(schema='ecas-exomol-reference-v1',request=asdict(result.request),
        provenance=asdict(checked.provenance),retrieved_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=checked.source_sha256,raw_base64=base64.b64encode(result.raw).decode('ascii'),
        catalogue_context=catalogue_context)
    unsigned=json.dumps(envelope,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    envelope['integrity_sha256']=sha256(unsigned).hexdigest()
    encoded=json.dumps(envelope,allow_nan=False).encode()
    if len(encoded)>MAX_CACHE_BYTES: raise ValueError('Reference cache record exceeds 2 MiB')
    root=_root(root); root.mkdir(parents=True,exist_ok=True)
    target=root/(uuid4().hex+'.json')
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=root,prefix='reference-',suffix='.tmp',delete=False) as stream:
            temporary=Path(stream.name); stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary,target)
    finally:
        if temporary is not None: temporary.unlink(missing_ok=True)
    return target


def load_reference(path):
    path=Path(path)
    _root(path.parent)
    if path.is_symlink() or path.is_junction(): raise ValueError('Linked reference record is unsupported')
    with path.open('rb') as stream: raw=stream.read(MAX_CACHE_BYTES+1)
    if len(raw)>MAX_CACHE_BYTES: raise ValueError('Reference cache record exceeds 2 MiB')
    try:
        envelope=json.loads(raw)
        required={'schema','request','provenance','retrieved_utc','source_sha256','raw_base64','integrity_sha256'}
        if set(envelope) not in (required,required|{'catalogue_context'}):
            raise ValueError('Unexpected reference envelope fields')
        unsigned={k:v for k,v in envelope.items() if k!='integrity_sha256'}
        if sha256(json.dumps(unsigned,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()!=envelope['integrity_sha256']:
            raise ValueError('Reference record integrity mismatch')
        if envelope['schema']!='ecas-exomol-reference-v1': raise ValueError('Unsupported reference record')
        stamp=datetime.fromisoformat(envelope['retrieved_utc'])
        if stamp.utcoffset() is None or stamp.utcoffset().total_seconds()!=0: raise ValueError('UTC timestamp required')
        request=ProductRequest(**envelope['request'])
        _context(envelope.get('catalogue_context'), request)
        source=base64.b64decode(envelope['raw_base64'],validate=True)
        product=validate_product(source,request)
        # JSON round-trip normalizes tuple citations to lists without altering values.
        expected=json.loads(json.dumps(asdict(product.provenance)))
        stored=envelope['provenance']
        if request.isotopologue=='12C-16O2' and isinstance(stored,dict) and stored.get('citations')==list(CITATIONS[:2]):
            # Early v1 records retained the method/dataset citations before the
            # general ExoMol citation was added. Preserve, rather than rewrite,
            # those valid historical metadata while validating every other field.
            expected['citations']=list(CITATIONS[:2])
            product=replace(product,provenance=replace(product.provenance,citations=CITATIONS[:2]))
        if expected!=stored or product.source_sha256!=envelope['source_sha256']:
            raise ValueError('Saved reference provenance differs from validated request')
        return RetrievedCrossSection(request,source,product)
    except (ValueError,TypeError,KeyError,RecursionError) as error:
        raise ValueError(f'Invalid reference cache: {error}') from error


def cached_references(root):
    root=_root(root)
    if not root.exists(): return [],0
    records=[]; invalid=0
    for path in sorted(root.glob('*.json')):
        try: records.append((path,load_reference(path)))
        except (OSError,ValueError): invalid+=1
    return records,invalid
