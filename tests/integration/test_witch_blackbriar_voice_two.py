"""Regression checks for the Blackbriar Hall Voice II completion pass."""

from __future__ import annotations

from pathlib import Path

import pytest

from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-witch-of-blackbriar-hall")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"


def test_blackbriar_voice_two_closes_the_packet_and_preserves_fresh_play() -> None:
    """Protect the final source finish, terminology, demonstration, and handoff."""
    adventure = load_adventure(EXAMPLE_PATH)
    state = load_play_state(EXAMPLE_STATE_PATH)
    encounters = adventure.encounter_index()
    clue = adventure.clue_index()["mirrors-repeat-conversations-from-marked-rooms"]

    source_prose = "\n".join(
        [
            adventure.synopsis,
            adventure.premise,
            adventure.explanation,
            *(encounter.summary for encounter in adventure.encounters),
            *(encounter.opening_view for encounter in adventure.encounters),
            *(encounter.content for encounter in adventure.encounters),
            *(revelation.title for revelation in adventure.revelations),
            *(revelation.description for revelation in adventure.revelations),
            *(item.description for item in adventure.clues),
            *(item.discovery for item in adventure.clues),
        ]
    )

    assert " party " not in f" {source_prose.lower()} "
    assert " adventurer" not in source_prose.lower()
    assert "player agency" not in source_prose.lower()
    assert "the GM invents" not in source_prose
    assert (
        "ordinary hospitality does not acquire a hidden cost after the fact"
        in encounters["saint-mercy-house"].content
    )
    assert "an accidental phrase never counts as acceptance" in encounters["moonless-mere"].content
    assert clue.discovery == (
        "Listen before the Glass Nurse turns toward the observer, or compare its echoes "
        "with household witnesses."
    )


    report = validate_adventure(adventure)
    projection = project_play_state(adventure, state)
    assert report.is_valid
    assert report.edge_connectivity == 4
    assert len(adventure.encounters) == 10
    assert len(adventure.revelations) == 18
    assert len(adventure.clues) == 95
    assert len(state.events) == 200
    assert len(projection.visits) == 10
    assert len(projection.spotted_clue_ids) == 72
    assert sum(len(item.missed_visit_numbers) for item in projection.clue_progress) == 11
    assert len(adventure.clues) - len(projection.spotted_clue_ids) == 23
