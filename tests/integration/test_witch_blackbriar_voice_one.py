"""Regression checks for the Blackbriar Hall Voice I pass."""

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


def test_blackbriar_voice_one_returns_action_to_the_vale() -> None:
    """Protect the authoritative prose pass and unchanged evidence/play layers."""
    witch_adventure = load_adventure(EXAMPLE_PATH)
    witch_state = load_play_state(EXAMPLE_STATE_PATH)

    revised_text = "\n".join(
        (
            witch_adventure.synopsis,
            witch_adventure.premise,
            witch_adventure.explanation,
            *(encounter.summary for encounter in witch_adventure.encounters),
            *(encounter.content for encounter in witch_adventure.encounters),
        )
    ).lower()
    for generic_actor in ("party", "players", "adventurer", "adventurers"):
        assert generic_actor not in revised_text

    assert (
        sum(len(encounter.opening_view.split()) for encounter in witch_adventure.encounters) == 784
    )
    assert (
        "Questions do not shorten the count"
        in witch_adventure.encounter_index()["saint-orra-gallows"].content
    )
    assert "A defended threshold becomes a safehouse only after five decisions" in (
        witch_adventure.encounter_index()["sedge-croft"].content
    )
    assert (
        "Careful questions consume table time"
        in witch_adventure.encounter_index()["saint-mercy-house"].content
    )
    assert (
        "which household a seizure will leave cold"
        in witch_adventure.encounter_index()["blackbriar-hall"].content
    )
    assert (
        "Give each name a person before the rite"
        in witch_adventure.encounter_index()["burned-refuge"].content
    )
    assert (
        "The tag states uncertainty honestly"
        in witch_adventure.encounter_index()["white-pits"].content
    )
    assert "The chapel cannot revoke every household's welcome" in (
        witch_adventure.encounter_index()["chapel-of-the-free-witness"].content
    )
    assert (
        "This distinguishes a secured vessel"
        in witch_adventure.encounter_index()["moonless-mere"].content
    )
    assert "The wood always converts movement into evidence" in (
        witch_adventure.encounter_index()["crow-wood"].content
    )
    assert "The chamber reflects every person, record, route, and obligation" in (
        witch_adventure.encounter_index()["underhall-of-the-hollow-feast"].content
    )

    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    assert "## Second-look Voice I" in design

    projection = project_play_state(witch_adventure, witch_state)
    report = validate_adventure(witch_adventure)
    assert report.is_valid
    assert report.edge_connectivity == 4
    assert len(witch_adventure.encounters) == 10
    assert len(witch_adventure.revelations) == 18
    assert len(witch_adventure.clues) == 95
    assert len(witch_state.events) == 200
    assert len(projection.spotted_clue_ids) == 72
    assert sum(len(item.missed_visit_numbers) for item in projection.clue_progress) == 11
