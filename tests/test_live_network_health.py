"""Opt-in live network health checks for catalogued archives and endpoints.

Skipped by default during routine offline/CI test runs so ECAS remains 100%
deterministic and offline-safe. Maintainers can run these checks on demand via:

    $env:ECAS_RUN_LIVE_NETWORK_TESTS='1'
    pytest -m live_network tests/test_live_network_health.py
"""
from __future__ import annotations

import os
import urllib.request

import pytest

from ecas.ingestion.exomol_catalogue import parse_catalogue
from ecas.resources.catalog import SCIENTIFIC_RESOURCES

LIVE_ENABLED = os.environ.get("ECAS_RUN_LIVE_NETWORK_TESTS") == "1"


def test_catalogued_urls_are_strictly_https_for_health_monitoring():
    """Offline sanity check ensuring every monitored catalog URL uses HTTPS."""
    assert len(SCIENTIFIC_RESOURCES) >= 17
    for entry in SCIENTIFIC_RESOURCES:
        assert entry.canonical_url.startswith("https://"), (
            f"Non-HTTPS URL in {entry.resource_id}: {entry.canonical_url}"
        )


@pytest.mark.live_network
@pytest.mark.skipif(
    not LIVE_ENABLED,
    reason="Opt-in live network check; set ECAS_RUN_LIVE_NETWORK_TESTS=1 to execute.",
)
@pytest.mark.parametrize("resource", SCIENTIFIC_RESOURCES, ids=lambda r: r.resource_id)
def test_live_scientific_resource_urls_respond(resource):
    req = urllib.request.Request(
        resource.canonical_url,
        headers={"User-Agent": "ECAS-HealthCheck/1.0 (+https://github.com/brettadin/ECAS_BETA)"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        assert 200 <= resp.status < 400


@pytest.mark.live_network
@pytest.mark.skipif(
    not LIVE_ENABLED,
    reason="Opt-in live network check; set ECAS_RUN_LIVE_NETWORK_TESTS=1 to execute.",
)
def test_live_nasa_exoplanet_archive_tap_atmospheres_schema():
    tap_url = (
        "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
        "query=select+top+1+pl_name,centralwavelng,pl_trandep+from+atmospheres"
        "+where+pl_name='WASP-39+b'&format=csv"
    )
    req = urllib.request.Request(
        tap_url,
        headers={"User-Agent": "ECAS-HealthCheck/1.0"},
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        body = resp.read(65536).decode("utf-8")
    assert "pl_name" in body
    assert "WASP-39 b" in body


@pytest.mark.live_network
@pytest.mark.skipif(
    not LIVE_ENABLED,
    reason="Opt-in live network check; set ECAS_RUN_LIVE_NETWORK_TESTS=1 to execute.",
)
def test_live_exomol_master_catalogue_parses():
    req = urllib.request.Request(
        "https://www.exomol.com/db/exomol.all",
        headers={"User-Agent": "ECAS-HealthCheck/1.0"},
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read(2 * 1024 * 1024)
    catalogue = parse_catalogue(raw)
    assert len(catalogue.entries) > 100
