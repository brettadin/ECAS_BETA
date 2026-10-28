"""NASA planet-catalog discovery protocol; no network or filesystem operations.

Catalog identities are not spectra. A caller must separately authorize retrieval
and supply response bytes. Parsing does not authenticate their remote origin.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from urllib.parse import urlencode


ENDPOINT = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
MAX_RESPONSE_BYTES = 256 * 1024


class DiscoveryError(ValueError):
    """Invalid discovery input or unsupported response; never an empty success."""


@dataclass(frozen=True)
class PlanetSearch:
    name: str
    limit: int
    url: str


@dataclass(frozen=True)
class PlanetIdentity:
    name: str
    host_name: str | None
    discovery_method: str | None


@dataclass(frozen=True)
class DiscoveryResult:
    request: PlanetSearch
    planets: tuple[PlanetIdentity, ...]
    raw_response: bytes
    response_sha256: str
    possibly_truncated: bool
    evidence_kind: str = "supplied_response_unverified"


def _text(value, *, nullable=False):
    if value is None and nullable:
        return None
    if (not isinstance(value, str) or not value.strip() or len(value) > 256
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise DiscoveryError("Expected nonempty catalog text, or explicit null for optional fields")
    return value


def planet_search(name: str, *, limit: int = 20) -> PlanetSearch:
    """Build a case-insensitive exact-name query (not an alias resolver).

    No planet is hard-coded. Apostrophes are escaped as SQL string literals,
    then the complete query is URL-encoded; no caller-supplied SQL is accepted.
    """
    name = _text(name).strip()
    if type(limit) is not int or not 1 <= limit <= 100:
        raise DiscoveryError("Result limit must be an integer from 1 to 100")
    literal = name.replace("'", "''")
    query = (f"select top {limit} pl_name,hostname,discoverymethod from pscomppars "
             f"where lower(pl_name)=lower('{literal}') order by pl_name")
    url = ENDPOINT + "?" + urlencode({"query": query, "format": "json"})
    return PlanetSearch(name, limit, url)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DiscoveryError("Duplicate JSON field")
        result[key] = value
    return result


def _invalid_constant(value):
    raise DiscoveryError("Non-finite JSON constant is unsupported")


def parse_planet_search(request: PlanetSearch, raw: bytes) -> DiscoveryResult:
    """Validate bounded supplied JSON and retain its exact bytes/hash.

    An empty JSON array is a valid no-match response. HTTP errors, HTML, unknown
    fields, partial rows and overflow are failures, not 'no planets found'.
    """
    if type(request) is not PlanetSearch or request != planet_search(request.name, limit=request.limit):
        raise DiscoveryError("Search request changed or is unsupported")
    if type(raw) is not bytes or not raw or len(raw) > MAX_RESPONSE_BYTES:
        raise DiscoveryError("Response must contain 1 through 262144 bytes")
    try:
        rows = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=_invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise DiscoveryError("Invalid catalog JSON") from error
    if not isinstance(rows, list) or len(rows) > request.limit:
        raise DiscoveryError("Expected a bounded array of catalog records")
    planets = []
    names = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"pl_name", "hostname", "discoverymethod"}:
            raise DiscoveryError("Missing or unsupported catalog fields")
        name = _text(row["pl_name"])
        if name.casefold() != request.name.casefold() or name.casefold() in names:
            raise DiscoveryError("Unexpected or duplicate planet identity")
        names.add(name.casefold())
        planets.append(PlanetIdentity(name, _text(row["hostname"], nullable=True),
                                     _text(row["discoverymethod"], nullable=True)))
    return DiscoveryResult(request, tuple(planets), raw, sha256(raw).hexdigest(),
                           len(rows) == request.limit)
