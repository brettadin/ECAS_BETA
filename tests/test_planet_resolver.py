"""Unit tests for exoplanet target normalization and fuzzy relevance ranking."""
import pytest

from ecas.ingestion.planet_resolver import (
    KNOWN_ATMOSPHERIC_TARGETS,
    collect_all_known_planets,
    fuzzy_match_targets,
    normalize_target_name,
    suggest_canonical_target,
)


def test_normalize_target_name():
    assert normalize_target_name("WASP-39 b") == "wasp39b"
    assert normalize_target_name("wasp 39b") == "wasp39b"
    assert normalize_target_name("WASP39b") == "wasp39b"
    assert normalize_target_name("  55 Cnc e  ") == "55cnce"
    assert normalize_target_name("TRAPPIST-1 e") == "trappist1e"
    assert normalize_target_name("HD_209458+b") == "hd209458b"
    assert normalize_target_name("") == ""
    assert normalize_target_name(None) == ""


def test_exact_normalized_match():
    assert suggest_canonical_target("wasp39b") == "WASP-39 b"
    assert suggest_canonical_target("WASP 39 b") == "WASP-39 b"
    assert suggest_canonical_target("55cnce") == "55 Cnc e"
    assert suggest_canonical_target("trappist1e") == "TRAPPIST-1 e"
    assert suggest_canonical_target("hd209458b") == "HD 209458 b"


def test_typo_fuzzy_match_wasp30b():
    # User types 'WASP30b' (typo with '0' instead of '9')
    matches = fuzzy_match_targets("WASP30b", top_n=3)
    assert len(matches) > 0
    top_target, score = matches[0]
    assert "WASP-" in top_target
    assert score > 0.80
    # Confirms WASP-39 b is among top candidate recommendations
    candidate_names = [target for target, _ in matches]
    assert "WASP-39 b" in candidate_names


def test_partial_query_without_planet_letter():
    # User types 'wasp 39' without the planet letter 'b'
    matches = fuzzy_match_targets("wasp 39", top_n=3)
    top_target, score = matches[0]
    assert top_target == "WASP-39 b"
    assert score > 0.90


def test_typo_trapist1e():
    # User types 'trapist1e' (single 'p' instead of 'pp')
    matches = fuzzy_match_targets("trapist1e", top_n=3)
    top_target, score = matches[0]
    assert top_target == "TRAPPIST-1 e"
    assert score > 0.90


def test_empty_or_whitespace_query():
    assert fuzzy_match_targets("") == []
    assert fuzzy_match_targets("   ") == []
    assert suggest_canonical_target("") is None


def test_collect_all_known_planets(tmp_path):
    planets = collect_all_known_planets(tmp_path)
    assert "WASP-39 b" in planets
    assert "TRAPPIST-1 e" in planets
    assert "55 Cnc e" in planets
    assert len(planets) >= len(KNOWN_ATMOSPHERIC_TARGETS)


def test_nasa_browser_suggestion_bar_on_typo(tmp_path):
    from unittest.mock import patch
    from PySide6.QtWidgets import QApplication
    from ecas.ui.nasa_browser import NasaArchiveBrowser

    app = QApplication.instance() or QApplication([])
    browser = NasaArchiveBrowser(cache_root=tmp_path)
    assert browser.target.completer() is not None
    assert "WASP-39 b" in browser.known_planets

    browser.target.setText("WASP30b")
    # Simulate a lookup failure on typo
    with patch.object(browser.http, "get", side_effect=ValueError("synthetic lookup failure")):
        browser.search()

    assert not browser.suggestion_bar.isHidden()
    assert "WASP-39 b" in browser.suggestion_label.text()
    assert "Search WASP-39 b" in browser.suggestion_button.text()

    # Clicking suggestion applies WASP-39 b
    browser.suggestion_button.click()
    assert browser.target.text() == "WASP-39 b"
    browser.close()
