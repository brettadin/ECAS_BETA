"""Exoplanet target name normalization, relevance ranking, and fuzzy suggestion engine.

Provides typo-tolerant matching and auto-suggestions for exoplanetary atmospheric
spectroscopy targets without modifying underlying scientific database queries.
"""
from __future__ import annotations

import difflib
import json
from pathlib import Path
import re
from typing import Iterable


# Curated canonical exoplanets with published transmission spectroscopy / NASA archive records
KNOWN_ATMOSPHERIC_TARGETS: tuple[str, ...] = (
    # WASP Series
    "WASP-4 b",
    "WASP-6 b",
    "WASP-10 b",
    "WASP-12 b",
    "WASP-17 b",
    "WASP-18 b",
    "WASP-19 b",
    "WASP-29 b",
    "WASP-31 b",
    "WASP-33 b",
    "WASP-39 b",
    "WASP-43 b",
    "WASP-52 b",
    "WASP-67 b",
    "WASP-69 b",
    "WASP-74 b",
    "WASP-76 b",
    "WASP-77 A b",
    "WASP-79 b",
    "WASP-80 b",
    "WASP-96 b",
    "WASP-107 b",
    "WASP-121 b",
    "WASP-127 b",
    "WASP-166 b",
    # HD Series
    "HD 209458 b",
    "HD 189733 b",
    "HD 149026 b",
    "HD 97658 b",
    "HD 106315 b",
    "HD 106315 c",
    "HD 3167 b",
    "HD 3167 c",
    "HD 3167 d",
    "HD 219134 b",
    "HD 219134 c",
    # HAT Series
    "HAT-P-1 b",
    "HAT-P-2 b",
    "HAT-P-3 b",
    "HAT-P-7 b",
    "HAT-P-8 b",
    "HAT-P-11 b",
    "HAT-P-12 b",
    "HAT-P-14 b",
    "HAT-P-18 b",
    "HAT-P-26 b",
    "HAT-P-32 b",
    "HAT-P-38 b",
    "HAT-P-41 b",
    # K2 Series
    "K2-18 b",
    "K2-25 b",
    "K2-33 b",
    "K2-136 c",
    "K2-138 b",
    "K2-141 b",
    # GJ Series
    "GJ 1214 b",
    "GJ 436 b",
    "GJ 3470 b",
    "GJ 9827 b",
    "GJ 9827 d",
    "GJ 1132 b",
    "GJ 3053 b",
    "GJ 486 b",
    "GJ 367 b",
    # TRAPPIST-1 System
    "TRAPPIST-1 b",
    "TRAPPIST-1 c",
    "TRAPPIST-1 d",
    "TRAPPIST-1 e",
    "TRAPPIST-1 f",
    "TRAPPIST-1 g",
    "TRAPPIST-1 h",
    # Super-Earths / Rocky / Sub-Neptunes
    "55 Cnc e",
    "LHS 1140 b",
    "LHS 475 b",
    "L 98-59 b",
    "L 98-59 c",
    "L 98-59 d",
    "LTT 1445 A b",
    "LTT 9779 b",
    # TOI Series
    "TOI-270 c",
    "TOI-270 d",
    "TOI-700 d",
    "TOI-700 e",
    "TOI-849 b",
    "TOI-1231 b",
    "TOI-5675 b",
    "TOI-178 b",
    "TOI-2109 b",
    # Kepler Series
    "Kepler-16 b",
    "Kepler-51 b",
    "Kepler-51 d",
    "Kepler-138 c",
    "Kepler-138 d",
    "Kepler-186 f",
    "Kepler-1649 c",
    # KELT / MASCARA
    "KELT-9 b",
    "KELT-11 b",
    "KELT-20 b",
    "MASCARA-1 b",
    "MASCARA-2 b",
    "Proxima Cen b",
)


_KEYBOARD_NEIGHBORS: dict[str, str] = {
    "1": "2q",
    "2": "13qw",
    "3": "24we",
    "4": "35er",
    "5": "46rt",
    "6": "57ty",
    "7": "68yu",
    "8": "79ui",
    "9": "80io",
    "0": "9-op",
    "q": "12wa",
    "w": "23qeas",
    "e": "34wrsd",
    "r": "45etdf",
    "t": "56ryfg",
    "y": "67tugh",
    "u": "78yijh",
    "i": "89uokj",
    "o": "90iplk",
    "p": "0-[;lo",
    "a": "qwsz",
    "s": "weadzx",
    "d": "ersfxc",
    "f": "rtdgcv",
    "g": "tyfhvb",
    "h": "yugjbn",
    "j": "uihknm",
    "k": "iojlm",
    "l": "opk",
    "z": "asx",
    "x": "sdzc",
    "c": "dfxv",
    "v": "fgcb",
    "b": "ghvn",
    "n": "hjbm",
    "m": "jkn",
}

# Major exoplanets with extensive published transmission spectroscopy in NASA archives
BENCHMARK_TRANSMISSION_TARGETS: frozenset[str] = frozenset({
    "WASP-39 b",
    "HD 209458 b",
    "HD 189733 b",
    "K2-18 b",
    "TRAPPIST-1 e",
    "55 Cnc e",
    "WASP-43 b",
    "WASP-17 b",
    "WASP-76 b",
    "GJ 1214 b",
    "HAT-P-11 b",
    "HAT-P-26 b",
})


def normalize_target_name(name: str) -> str:
    """Strip whitespace, punctuation, hyphens, and casing for fuzzy matching.

    Examples:
        'WASP-39 b' -> 'wasp39b'
        'wasp 39b'  -> 'wasp39b'
        '55 Cnc e'  -> '55cnce'
    """
    if not isinstance(name, str):
        return ""
    return re.sub(r"[\s\-_.\+]+", "", name).lower()


def fuzzy_match_targets(
    query: str,
    candidates: Iterable[str] | None = None,
    *,
    top_n: int = 5,
    cutoff: float = 0.5,
) -> list[tuple[str, float]]:
    """Rank target candidates by relevance and string similarity.

    Args:
        query: User input query (e.g., 'WASP30b', 'wasp 39', 'trapist 1e').
        candidates: Iterable of canonical target names. Defaults to KNOWN_ATMOSPHERIC_TARGETS.
        top_n: Maximum number of ranked suggestions to return.
        cutoff: Minimum similarity threshold (0.0 to 1.0).

    Returns:
        List of (canonical_name, similarity_score) sorted descending by score.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    norm_query = normalize_target_name(clean_query)
    if not norm_query:
        return []

    target_pool = candidates if candidates is not None else KNOWN_ATMOSPHERIC_TARGETS
    scored: list[tuple[str, float]] = []

    for target in target_pool:
        norm_target = normalize_target_name(target)
        if norm_query == norm_target:
            score = 1.0
        elif norm_query in norm_target:
            # Substring match (e.g. user typed 'wasp39' matching 'wasp39b')
            base = difflib.SequenceMatcher(None, norm_query, norm_target).ratio()
            score = max(base, 0.92)
        elif norm_target in norm_query:
            base = difflib.SequenceMatcher(None, norm_query, norm_target).ratio()
            score = max(base, 0.88)
        else:
            base_ratio = difflib.SequenceMatcher(None, norm_query, norm_target).ratio()
            score = base_ratio

            # Keyboard typo tolerance bonus for single-character neighbor slips (e.g. '0' for '9' in WASP30b vs WASP39b)
            if len(norm_query) == len(norm_target):
                diffs = [(c1, c2) for c1, c2 in zip(norm_query, norm_target) if c1 != c2]
                if len(diffs) == 1:
                    c1, c2 = diffs[0]
                    if c1 in _KEYBOARD_NEIGHBORS.get(c2, "") or c2 in _KEYBOARD_NEIGHBORS.get(c1, ""):
                        score = min(0.96, score + 0.08)

        # Prioritize major benchmark exoplanets when scores are close
        if target in BENCHMARK_TRANSMISSION_TARGETS and score < 1.0:
            score = min(0.99, score + 0.02)

        if score >= cutoff:
            scored.append((target, score))

    scored.sort(key=lambda item: (item[1], -len(item[0])), reverse=True)
    return scored[:top_n]


def suggest_canonical_target(
    query: str,
    candidates: Iterable[str] | None = None,
    *,
    min_confidence: float = 0.70,
) -> str | None:
    """Resolve an input string to a single canonical target if confident.

    Returns:
        Canonical name string if an exact normalized match or confident match exists, else None.
    """
    matches = fuzzy_match_targets(query, candidates, top_n=1, cutoff=min_confidence)
    if matches:
        return matches[0][0]
    return None


def collect_all_known_planets(cache_root: Path | None = None) -> tuple[str, ...]:
    """Return deduplicated list of canonical planet names from curated targets and local cache."""
    planets = list(KNOWN_ATMOSPHERIC_TARGETS)

    if cache_root is not None and isinstance(cache_root, Path) and cache_root.is_dir():
        for entry_dir in cache_root.glob("entry-*"):
            meta_file = entry_dir / "metadata.json"
            if meta_file.is_file():
                try:
                    meta = json.loads(meta_file.read_text(encoding="utf-8"))
                    name = None
                    if isinstance(meta, dict):
                        name = meta.get("pl_name")
                    elif isinstance(meta, list) and meta and isinstance(meta[0], dict):
                        name = meta[0].get("pl_name")
                    if name and isinstance(name, str) and name not in planets:
                        planets.append(name)
                except Exception:
                    pass

    return tuple(sorted(dict.fromkeys(planets), key=lambda x: (x.split()[0], x)))
