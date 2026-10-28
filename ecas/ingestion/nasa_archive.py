"""NASA spectral discovery, session URL resolution and local cache records.

No network or UI code here. Cache registration is separate from project SQLite
persistence: a complete record is written last, after validating the raw table.
"""
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
import re
from urllib.parse import urlencode, urlsplit, parse_qs
from uuid import uuid4

from .nasa_discovery import ENDPOINT, planet_search, _unique_object, _invalid_constant
from .nasa_table import import_transmission_table

HOST = "https://exoplanetarchive.ipac.caltech.edu"
INTERFACE = HOST + "/cgi-bin/atmospheres/nph-firefly?atmospheres"
FIELDS = "pl_name,spec_type,bibcode,authors,num_datapoints,instrument,facility,minwavelng,maxwavelng,spec_path"
MAX_BYTES = 1048576


def valid_spec_path(value):
    return isinstance(value, str) and ".." not in value and bool(re.fullmatch(
        r"(?:[0-9]{2}/){4}[A-Za-z0-9_.+-]+\.tbl", value))


def spectra_search(name):
    name = planet_search(name).name  # Reuse target validation, never caller SQL.
    literal = name.replace("'", "''")
    query = (f"select top 50 {FIELDS} from spectra where lower(pl_name)=lower('{literal}') "
             "order by bibcode,spec_path")
    return ENDPOINT + "?" + urlencode({"query": query, "format": "json"})


def parse_spectra(raw, name):
    if type(raw) is not bytes or not raw or len(raw) > MAX_BYTES:
        raise ValueError("Invalid or oversized NASA metadata")
    name = planet_search(name).name
    try:
        rows = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=_invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ValueError("Invalid NASA metadata JSON") from error
    if not isinstance(rows, list) or len(rows) > 50:
        raise ValueError("Expected at most 50 NASA spectra records")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(FIELDS.split(",")):
            raise ValueError("Missing or unsupported NASA metadata fields")
        if row["pl_name"].__class__ is not str or row["pl_name"].casefold() != name.casefold():
            raise ValueError("NASA returned another target")
        if not valid_spec_path(row["spec_path"]) or row["spec_path"] in seen:
            raise ValueError("Invalid or duplicate NASA spectral path")
        seen.add(row["spec_path"])
        if row["spec_type"] not in ("Transmission", "Eclipse", "Direct Imaging"):
            raise ValueError("Unknown spectrum type")
        for field in ("bibcode", "authors", "instrument", "facility"):
            value = row[field]
            if value is not None and (not isinstance(value, str) or len(value) > 2048
                                      or any(ord(c) < 32 for c in value)):
                raise ValueError("Invalid NASA descriptive field")
        if type(row["num_datapoints"]) is not int or not 1 <= row["num_datapoints"] <= 10000:
            raise ValueError("Unsupported NASA point count")
        for field in ("minwavelng", "maxwavelng"):
            value = row[field]
            if value is not None and (type(value) not in (int, float)
                                      or not math.isfinite(value) or value < 0):
                raise ValueError("Invalid NASA wavelength bounds")
        if (row["minwavelng"] is not None and row["maxwavelng"] is not None
                and row["minwavelng"] > row["maxwavelng"]):
            raise ValueError("Reversed NASA wavelength bounds")
    return rows


def matching_search_url(url, name):
    """Compare the generated query semantically while preserving original evidence.

    NASA returns canonical target casing even for case-insensitive searches.
    Decode query parameters before comparing so Unicode/percent encoding works;
    keep the endpoint and parameter structure exact, including duplicate rejection.
    """
    if not isinstance(url, str):
        return False
    try:
        actual, expected = urlsplit(url), urlsplit(spectra_search(name))
        # Keep empty values so blank duplicates/unknown parameters cannot vanish
        # during validation. Reject malformed query components explicitly.
        params = parse_qs(actual.query, keep_blank_values=True, strict_parsing=True)
        wanted = parse_qs(expected.query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return False
    if actual._replace(query="") != expected._replace(query=""):
        return False
    return (set(params) == set(wanted) and params.get('format') == wanted['format']
            and len(params.get('query', [])) == 1
            and params['query'][0].casefold() == wanted['query'][0].casefold())


def spectrum_url(page, record):
    """Follow NASA's inspected BaseURL + /data/ + SPEC_PATH construction.

    Workspace comes from the current page, not a stale saved session. No remote
    scripts are executed. If NASA changes this supported layout, stop explicitly.
    """
    if record["spec_type"] != "Transmission" or not valid_spec_path(record["spec_path"]):
        raise ValueError("Only supported transmission records can be downloaded")
    if type(page) is not bytes or len(page) > MAX_BYTES:
        raise ValueError("Invalid NASA interface page")
    text = page.decode("utf-8")
    matches = re.findall(r"FF_InitPage\s*\(\s*'[^']*'\s*,\s*'(/workspace/TMP_[A-Za-z0-9_]+)'", text)
    if len(matches) != 1:
        raise ValueError("NASA session layout changed; cannot resolve download safely")
    return HOST + matches[0] + "/atmospheres/tab1/data/" + record["spec_path"]


def allowed_url(url):
    parts = urlsplit(url)
    return (parts.scheme == "https" and parts.netloc == "exoplanetarchive.ipac.caltech.edu"
            and not parts.fragment and (parts.path == "/TAP/sync"
            or parts.path == "/cgi-bin/atmospheres/nph-firefly"
            or bool(re.fullmatch(r"/workspace/TMP_[A-Za-z0-9_]+/atmospheres/tab1/data/(?:[0-9]{2}/){4}[A-Za-z0-9_.+-]+\.tbl", parts.path))
            and ".." not in parts.path))


def _ordinary(path):
    if path.is_symlink() or path.is_junction():
        raise ValueError("Cache links are unsupported")


def read_cached(folder):
    folder = Path(folder)
    _ordinary(folder)
    source, manifest = folder / "source.tbl", folder / "record.json"
    _ordinary(source)
    _ordinary(manifest)
    if manifest.stat().st_size > 32768 or source.stat().st_size > MAX_BYTES:
        raise ValueError("Oversized cache record")
    record = json.loads(manifest.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    if not isinstance(record, dict):
        raise ValueError("Invalid cache manifest")
    raw = source.read_bytes()
    if record.get("schema") != "ecas-nasa-spectrum-cache-v1" or record.get("sha256") != sha256(raw).hexdigest():
        raise ValueError("Incomplete or changed cached spectrum")
    metadata = parse_spectra(json.dumps([record["metadata"]]).encode(), record["metadata"]["pl_name"])[0]
    metadata_file = folder / "metadata.json"
    _ordinary(metadata_file)
    if metadata_file.stat().st_size > MAX_BYTES:
        raise ValueError("Oversized cache metadata")
    evidence = metadata_file.read_bytes()
    if (sha256(evidence).hexdigest() != record["metadata_sha256"]
            or not matching_search_url(record["metadata_source_url"], metadata["pl_name"])
            or metadata not in parse_spectra(evidence, metadata["pl_name"])):
        raise ValueError("Cached metadata changed or no longer identifies the spectrum")
    if not allowed_url(record["source_url"]) or not record["source_url"].endswith(metadata["spec_path"]):
        raise ValueError("Cache source URL mismatch")
    parsed = import_transmission_table(source)
    if (metadata["spec_type"] != "Transmission"
            or dict(parsed.metadata)["PL_NAME"].casefold() != metadata["pl_name"].casefold()
            or parsed.spectrum.row_count != metadata["num_datapoints"]):
        raise ValueError("Cached table identity/count mismatch")
    return record, source


def cache_entries(root):
    root = Path(root)
    _ordinary(root)
    entries, invalid = [], 0
    if root.exists():
        for folder in root.glob("entry-*"):
            try:
                record, source = read_cached(folder)
                entries.append((record, source))
            except (ValueError, OSError, KeyError, TypeError, RecursionError):
                invalid += 1
    return entries, invalid


def store_spectrum(root, metadata, raw, url, evidence):
    if type(raw) is not bytes or not raw or len(raw) > MAX_BYTES:
        raise ValueError("Empty or oversized spectrum")
    metadata = parse_spectra(json.dumps([metadata]).encode(), metadata["pl_name"])[0]
    if (not matching_search_url(evidence["url"], metadata["pl_name"])
            or metadata not in parse_spectra(evidence["raw"], metadata["pl_name"])):
        raise ValueError("Metadata evidence does not identify the selected spectrum")
    if not allowed_url(url) or not url.endswith(metadata["spec_path"]):
        raise ValueError("Download URL does not match the selected spectrum")
    root = Path(root)
    _ordinary(root)
    root.mkdir(parents=True, exist_ok=True)
    folder = root / ("entry-" + uuid4().hex)
    folder.mkdir()  # Failed validation leaves an unregistered partial entry.
    source = folder / "source.tbl"
    with source.open("xb") as stream:
        stream.write(raw)
    parsed = import_transmission_table(source)
    if (metadata["spec_type"] != "Transmission"
            or dict(parsed.metadata)["PL_NAME"].casefold() != metadata["pl_name"].casefold()
            or parsed.spectrum.row_count != metadata["num_datapoints"]):
        raise ValueError("Downloaded table does not match the selected NASA record")
    record = dict(schema="ecas-nasa-spectrum-cache-v1", metadata=metadata, source_url=url,
        retrieved_utc=datetime.now(timezone.utc).isoformat(), sha256=sha256(raw).hexdigest(),
        metadata_source_url=evidence["url"], metadata_sha256=sha256(evidence["raw"]).hexdigest())
    with (folder / "metadata.json").open("xb") as stream:
        stream.write(evidence["raw"])
    with (folder / "record.json").open("x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)  # Completeness marker written last.
    return read_cached(folder)[1]
