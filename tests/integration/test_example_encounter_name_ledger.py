"""Regression contracts for the final example encounter-name deconfliction pass."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.corpus

LEDGER = Path("docs/example-encounter-name-ledger.md")
DISPOSITIONS = Path("docs/example-encounter-name-dispositions.json")
ADVENTURE_PATHS = tuple(sorted(Path("examples").glob("*/adventure.json")))
FUNCTION_WORDS = {
    "a",
    "an",
    "and",
    "at",
    "beneath",
    "between",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "under",
    "with",
}
TITLE_CHANGES = {
    ("A Wedding for the River", "shrine-of-the-open-door"): (
        "The Shrine of the Open Door",
        "The Doorless Shrine",
        "2b2465527a7d7994c86060c5c617013ead3c92752cbd556c815e2757f0ee0bde",
    ),
    ("The Siege of the Stone Lung", "the-black-cisterns"): (
        "The Black Cisterns",
        "The Cisterns of Black Breath",
        "c063ac67f949e450398e08740132d09541a3af708fa5f14cd57d53404512171d",
    ),
    ("When the Swine Kneel", "the-hall-of-petitions"): (
        "The Hall of Petitions",
        "The Hall of Condemnations",
        "a6bb800e34e986982ea240eb5e81e4331aebedf4d443f36d4f8afa7ddd0aac66",
    ),
    ("The Concord of Aurelune", "the-white-hart-gallery"): (
        "The White Hart Gallery",
        "The Gallery of Silver Kin",
        "808fab12f173d73f554f6464a0cda8abd829c49b2f5a094ce8f7c545f8c3215b",
    ),
}
FROZEN_PLAY_FILES = {
    Path("examples/a-wedding-for-the-river/play-state.example.json"): (
        "8a2085d588a2119dc32fccb120b698a4574651e6eaa27cfefdcdeed6cc0eb0c6"
    ),
    Path(
        "examples/a-wedding-for-the-river/archives/"
        "four-open-hands-demonstrated-playthrough.journal.json"
    ): "46cc45d6a92d0e919ddafb960150fa0da789963c730ac70dff2d55276ee26787",
    Path("examples/the-siege-of-the-stone-lung/play-state.example.json"): (
        "67c9b16c6b1d9322706ea4af91aa433e93ad5ad54723f3890dc3aefacd9a2268"
    ),
    Path("examples/when-the-swine-kneel/play-state.example.json"): (
        "4507a3cb7ed4312251e1d9a6cf3c107b8783969a2d906bbf4ce88004b2b06387"
    ),
    Path(
        "examples/when-the-swine-kneel/archives/"
        "synthetic-complete-playthrough.journal.json"
    ): "83f359ebd69a62649042237e2baebaa2e4486b39913c9d1bda5eae140bf3b4bf",
    Path("examples/the-concord-of-aurelune/play-state.example.json"): (
        "c5fbf17c07163b7ceeb3cea4f82ad58a30bb0415c61bdede77c0a3e45baa87f5"
    ),
}


def _load_sources() -> tuple[dict[str, Any], ...]:
    return tuple(json.loads(path.read_text(encoding="utf-8")) for path in ADVENTURE_PATHS)


def _source_rows() -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (
            source["adventure"]["title"],
            encounter["title"],
            encounter["id"],
        )
        for source in _load_sources()
        for encounter in source["encounters"]
    )


def _ledger_rows() -> tuple[tuple[str, str, str], ...]:
    rows: list[tuple[str, str, str]] = []
    in_complete_ledger = False
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if line == "## Complete final ledger":
            in_complete_ledger = True
            continue
        if not in_complete_ledger:
            continue
        match = re.fullmatch(r"\| (.+) \| (.+) \| `([^`]+)` \|", line)
        if match:
            rows.append(match.groups())
    return tuple(rows)


def _normalize_title(title: str) -> str:
    folded = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", folded.lower()).strip()


def _article_insensitive(title: str) -> str:
    tokens = _normalize_title(title).split()
    if tokens and tokens[0] in {"a", "an", "the"}:
        tokens = tokens[1:]
    return " ".join(tokens)


def _meaningful_tokens(title: str) -> set[str]:
    return set(_normalize_title(title).split()) - FUNCTION_WORDS


def _candidate_pairs(
    rows: tuple[tuple[str, str, str], ...], detector: dict[str, Any]
) -> set[frozenset[tuple[str, str]]]:
    candidates: set[frozenset[tuple[str, str]]] = set()
    for left, right in combinations(rows, 2):
        if left[0] == right[0]:
            continue
        sequence = SequenceMatcher(
            None,
            _normalize_title(left[1]),
            _normalize_title(right[1]),
        ).ratio()
        left_tokens = _meaningful_tokens(left[1])
        right_tokens = _meaningful_tokens(right[1])
        token_overlap = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
        if sequence >= detector["sequence_threshold"] or (
            sequence >= detector["combined_sequence_threshold"]
            and token_overlap >= detector["combined_token_overlap_threshold"]
        ):
            candidates.add(frozenset({(left[0], left[2]), (right[0], right[2])}))
    return candidates


def test_final_ledger_is_an_exact_source_rebuild() -> None:
    """Reject stale, missing, reordered, or invented title-ledger rows."""
    rows = _source_rows()
    ledger = LEDGER.read_text(encoding="utf-8")

    assert len(rows) == 138
    assert len({adventure for adventure, _, _ in rows}) == 13
    assert _ledger_rows() == rows
    assert "- Exact cross-adventure duplicates: **0**" in ledger
    assert "- Article-and-punctuation-insensitive duplicates: **0**" in ledger
    assert "- Accepted title-only deconflictions: **4**" in ledger
    assert "- Reviewed current near-match and practical-ambiguity candidates: **18**" in ledger
    assert "- Unresolved candidates: **0**" in ledger


def test_final_titles_have_no_exact_or_normalized_cross_adventure_duplicates() -> None:
    """Keep exact and article-insensitive collisions out of the final corpus."""
    exact: defaultdict[str, set[str]] = defaultdict(set)
    normalized: defaultdict[str, set[str]] = defaultdict(set)
    for adventure, title, _ in _source_rows():
        exact[title].add(adventure)
        normalized[_article_insensitive(title)].add(adventure)

    assert {title: adventures for title, adventures in exact.items() if len(adventures) > 1} == {}
    assert {
        title: adventures for title, adventures in normalized.items() if len(adventures) > 1
    } == {}


def test_every_automated_candidate_has_a_recorded_disposition() -> None:
    """Make the similarity detector a review queue rather than an unexplained warning."""
    dispositions = json.loads(DISPOSITIONS.read_text(encoding="utf-8"))
    detected = _candidate_pairs(_source_rows(), dispositions["detector"])
    recorded = {
        frozenset(
            {
                tuple(entry["encounter_a"]),
                tuple(entry["encounter_b"]),
            }
        )
        for entry in dispositions["retained_candidates"]
        if entry["category"] != "compatibility distinction"
    }

    assert detected == recorded
    for entry in dispositions["retained_candidates"]:
        assert entry["category"] in {
            "compatibility distinction",
            "deliberate motif",
            "harmless generic overlap",
        }
        assert entry["reason"].strip()


def test_accepted_changes_are_title_only_and_keep_stable_ids() -> None:
    """Prove each deconfliction is the documented text substitution and nothing else."""
    sources = {source["adventure"]["title"]: source for source in _load_sources()}
    dispositions = json.loads(DISPOSITIONS.read_text(encoding="utf-8"))
    documented = {
        (entry["adventure"], entry["encounter_id"]): (
            entry["previous_title"],
            entry["current_title"],
        )
        for entry in dispositions["accepted_title_changes"]
    }

    assert documented == {
        key: (previous, current)
        for key, (previous, current, _) in TITLE_CHANGES.items()
    }
    for (adventure, encounter_id), (previous, current, baseline_hash) in TITLE_CHANGES.items():
        source = sources[adventure]
        encounter = next(item for item in source["encounters"] if item["id"] == encounter_id)
        assert encounter["title"] == current

        path = next(
            path
            for path in ADVENTURE_PATHS
            if json.loads(path.read_text(encoding="utf-8"))["adventure"]["title"]
            == adventure
        )
        restored = path.read_text(encoding="utf-8").replace(current, previous)
        assert hashlib.sha256(restored.encode()).hexdigest() == baseline_hash


def test_play_states_and_historical_archives_remain_byte_identical() -> None:
    """Protect customer-style journals from a user-facing title clarification."""
    for path, expected_hash in FROZEN_PLAY_FILES.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash


def test_deep_bell_compatibility_ids_remain_distinct() -> None:
    """Preserve the historical ID boundary while keeping public titles unambiguous."""
    sources = {source["adventure"]["title"]: source for source in _load_sources()}
    harrowgate = next(
        encounter
        for encounter in sources["The Bell Beneath Harrowgate"]["encounters"]
        if encounter["id"] == "deep-bell"
    )
    swine = next(
        encounter
        for encounter in sources["When the Swine Kneel"]["encounters"]
        if encounter["id"] == "the-deep-bell"
    )

    assert harrowgate["title"] == "The Deep Bell"
    assert swine["title"] == "The Six-Line Bell"
