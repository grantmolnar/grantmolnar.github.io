"""Final cross-file regression checks for The Mandate of Seven Reeds."""

from pathlib import Path

import pytest

from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-mandate-of-seven-reeds")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"
EXAMPLE_PLAYTHROUGH_PATH = EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md"


def test_seven_reeds_voice_two_reconciles_the_complete_corpus() -> None:
    """Protect the final source finish, fresh-play boundary, and roadmap handoff."""
    adventure = load_adventure(EXAMPLE_PATH)
    state = load_play_state(EXAMPLE_STATE_PATH)
    encounters = {encounter.id: encounter for encounter in adventure.encounters}
    report = validate_adventure(adventure)
    throne = encounters["hall-of-the-chrysanthemum-throne"].content

    assert "The Emperor names the commissioners **Witnesses of the Broken Dike**" in throne
    assert "Each commissioner was in Reedwater when the dike failed" in throne
    assert "addresses the adventurers" not in throne
    assert "The player characters were in Reedwater" not in throne

    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text()
    assert "the party" not in playthrough.lower()
    assert "These five Witnesses choose the costly northern channel" in playthrough
    assert "The Witnesses prepare paired acts of submission and field orders" in playthrough
    assert "this demonstrated government" in playthrough


    projection = project_play_state(adventure, state)
    assert len(adventure.encounters) == 15
    assert len(adventure.revelations) == 44
    assert len(adventure.clues) == 221
    assert report.is_valid
    assert report.edge_connectivity == 4
    assert len(state.events) == 288
    assert len(projection.spotted_clue_ids) == 142
    assert len(adventure.clues) - len(projection.spotted_clue_ids) == 79
