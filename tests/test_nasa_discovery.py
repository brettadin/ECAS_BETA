"""Offline protocol checks: synthetic cases and dated public NASA captures."""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from ecas.ingestion.nasa_discovery import (
    DiscoveryError, MAX_RESPONSE_BYTES, parse_planet_search, planet_search,
)


@pytest.mark.parametrize("name", ["WASP-39 b", "Kepler-22 b", "O'Brien b", "x' OR '1'='1"])
def test_named_queries_are_encoded_literals(name):
    request = planet_search(name, limit=3)
    parts = urlsplit(request.url)
    assert parts.scheme == "https" and parts.netloc == "exoplanetarchive.ipac.caltech.edu"
    query = parse_qs(parts.query)
    assert query["format"] == ["json"]
    assert "select top 3 pl_name,hostname,discoverymethod from pscomppars" in query["query"][0]
    assert "lower('" + name.replace("'", "''") + "')" in query["query"][0]


@pytest.mark.parametrize("name", [None, "", "  ", "planet\nname", "x" * 257, 42])
def test_invalid_names_rejected(name):
    with pytest.raises(DiscoveryError):
        planet_search(name)


@pytest.mark.parametrize("limit", [0, -1, 101, True, 2.5, "20"])
def test_invalid_limits_rejected(limit):
    with pytest.raises(DiscoveryError):
        planet_search("WASP-39 b", limit=limit)


def encoded_row(**updates):
    row = {"pl_name": "WASP-39 b", "hostname": "Synthetic host", "discoverymethod": None}
    row.update(updates)
    return json.dumps([row]).encode()


def test_response_preserves_raw_bytes_and_unknown_metadata():
    raw = encoded_row()
    result = parse_planet_search(planet_search("wasp-39 b", limit=1), raw)
    assert result.planets[0].name == "WASP-39 b"
    assert result.planets[0].discovery_method is None
    assert result.raw_response == raw and result.response_sha256 == sha256(raw).hexdigest()
    assert result.possibly_truncated
    assert result.evidence_kind == "supplied_response_unverified"


def test_empty_matches_are_distinct_from_failure():
    result = parse_planet_search(planet_search("Unknown b"), b"[]")
    assert result.planets == () and not result.possibly_truncated


@pytest.mark.parametrize("raw", [b"", b"<html>Error</html>", b"{}", b"[null]", b"[{}]",
    b"[NaN]", b"\xff", b'[{"pl_name":"x","pl_name":"y"}]', b"[" * 2000,
    b"x" * (MAX_RESPONSE_BYTES + 1)])
def test_malformed_or_oversized_response_fails(raw):
    with pytest.raises(DiscoveryError):
        parse_planet_search(planet_search("WASP-39 b"), raw)


@pytest.mark.parametrize("updates", [{"hostname": 42}, {"hostname": ""},
    {"pl_name": "Other b"}, {"discoverymethod": True}, {"extra": "unsupported"}])
def test_invalid_record_is_not_a_no_match(updates):
    with pytest.raises(DiscoveryError):
        parse_planet_search(planet_search("WASP-39 b"), encoded_row(**updates))


def test_duplicates_and_count_overflow_rejected():
    raw = json.dumps(json.loads(encoded_row()) * 2).encode()
    for limit in (1, 20):
        with pytest.raises(DiscoveryError):
            parse_planet_search(planet_search("WASP-39 b", limit=limit), raw)


def test_changed_request_rejected():
    request = replace(planet_search("WASP-39 b"), url="https://example.invalid/")
    with pytest.raises(DiscoveryError):
        parse_planet_search(request, encoded_row())


CAPTURES = Path(__file__).resolve().parents[1] / "data" / "NASA" / "2026-10-27"


def test_captured_live_catalog_roundtrip_and_provenance():
    raw = (CAPTURES / "planet-wasp39b.json").read_bytes()
    provenance = json.loads((CAPTURES / "planet-wasp39b.provenance.json").read_text())
    request = planet_search("WASP-39 b")
    assert provenance["success"] is True and provenance["http_status"] == 200
    assert provenance["source_url"] == request.url
    assert provenance["bytes"] == len(raw)
    assert sha256(raw).hexdigest() == provenance["sha256"] == "f3c35ec462680ae10f185db0b8f9211a06b3cf1353a5ba72efc3146ee860598e"
    result = parse_planet_search(request, raw)
    assert len(result.planets) == 1
    assert result.planets[0].name == "WASP-39 b"
    assert result.planets[0].host_name == "WASP-39"
    assert result.planets[0].discovery_method == "Transit"
    assert result.possibly_truncated is False
    # Parsing retained bytes does not independently reauthenticate their origin.
    assert result.evidence_kind == "supplied_response_unverified"


def test_captured_spectral_metadata_identifies_bundled_paper_without_claiming_data():
    raw = (CAPTURES / "wasp39b-spectra-metadata.json").read_bytes()
    provenance = json.loads((CAPTURES / "wasp39b-spectra-metadata.provenance.json").read_text())
    assert sha256(raw).hexdigest() == provenance["sha256"] == "9a6e0052580ac88fabbc0477b3fc7edc75e9b10bf36f580778920c07ab266abd"
    assert provenance["bytes"] == len(raw)
    assert provenance["success"] is True and provenance["http_status"] == 200
    records = json.loads(raw)
    assert len(records) == provenance["record_count"] == 20
    assert provenance["possibly_truncated"] is True
    assert all(row["pl_name"] == "WASP-39 b" for row in records)
    matched = [row for row in records if row["bibcode"] == "2023Natur.614..670F"]
    assert len(matched) == 1
    assert matched[0]["authors"] == "Feinstein et al. 2023"
    assert matched[0]["num_datapoints"] == 331
    assert matched[0]["spec_type"] == "Transmission"
    assert matched[0]["spec_path"].endswith(".tbl")
    # This response identifies a file; it contains no per-wavelength measurements.
    assert "centralwavelng" not in matched[0] and "pl_trandep" not in matched[0]
