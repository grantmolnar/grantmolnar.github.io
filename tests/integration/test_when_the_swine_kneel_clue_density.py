"""Regression checks for the When the Swine Kneel clue-density pass."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.journal_archive_store import load_journal_archive
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.integration.swine_support import assert_historical_archive_structure
from tests.support.corpus_contracts import group_clues_by_revelation

pytestmark = pytest.mark.corpus

EXAMPLE = Path("examples/when-the-swine-kneel")
SOURCE = EXAMPLE / "adventure.json"
STATE = EXAMPLE / "play-state.example.json"
ARCHIVE = EXAMPLE / "archives" / "synthetic-complete-playthrough.journal.json"

ADDED_CLUE_IDS = {
    "dasts-filed-convocation-load-schedule",
    "dasts-preemptive-cull-circular",
    "the-six-line-isolation-drill",
    "the-surveyors-livestock-observation-table",
    "the-confiscated-farm-signal-board",
    "the-surface-reports-answer-the-bell",
    "the-fresh-overdrive-scars",
    "the-three-independent-control-paths",
}


def test_swine_clue_density_is_irregular_independent_and_route_safe() -> None:
    """Protect the additive thirty-eight-clue matrix and unchanged topology."""
    adventure = load_adventure(SOURCE)
    report = validate_adventure(adventure)
    clues_by_revelation = group_clues_by_revelation(adventure.clues)
    clues_by_encounter: Counter[str] = Counter()
    pairs: set[tuple[str, str]] = set()

    for clue in adventure.clues:
        pair = (clue.source_encounter_id, clue.revelation_id)
        assert pair not in pairs
        pairs.add(pair)
        clues_by_encounter[clue.source_encounter_id] += 1

    assert len(adventure.clues) == 38
    assert Counter(len(clues) for clues in clues_by_revelation.values()) == {
        3: 7,
        5: 1,
        6: 2,
    }
    assert clues_by_encounter == {
        "the-hall-of-petitions": 4,
        "southgate-stockyards": 5,
        "the-college-of-civic-measure": 6,
        "rillcross-farm-belt": 7,
        "the-chapel-of-the-first-survey": 6,
        "the-nine-mile-pump-house": 7,
        "the-deep-bell": 3,
    }
    assert report.is_valid
    assert report.edge_connectivity == 3

    clue_index = adventure.clue_index()
    revelation_index = adventure.revelation_index()
    assert clue_index.keys() >= ADDED_CLUE_IDS
    assert all(
        revelation_index[clue_index[clue_id].revelation_id].unlocks_encounter_id is None
        for clue_id in ADDED_CLUE_IDS
    )


def test_swine_clue_density_additions_remain_unseen_by_the_demonstration() -> None:
    """Keep new evidence independent of the byte-stable Ashlar route."""
    adventure = load_adventure(SOURCE)
    state = load_play_state(STATE)
    projection = project_play_state(adventure, state)
    unseen = set(adventure.clue_index()) - set(projection.spotted_clue_ids)

    assert len(state.events) == 96
    assert len(projection.spotted_clue_ids) == 25
    assert len(unseen) == 13
    assert unseen >= ADDED_CLUE_IDS
    assert all(item.is_established for item in projection.revelation_progress)


def test_swine_clue_density_packet_archive_and_roadmap_are_synchronized() -> None:
    """Keep the audit, source snapshot, demonstration, and next stage aligned."""
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    archive_raw = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    archive = load_journal_archive(ARCHIVE)


    assert_historical_archive_structure(archive_raw["adventure_snapshot"], source)
    assert archive_raw["archive"]["event_count"] == 74
    assert len(archive.play_state.events) == 74
