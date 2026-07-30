"""Tests for fresh project initialization from a packaged starter."""

from __future__ import annotations

from dataclasses import dataclass

from tests.support.adventures import complete_four_encounter_adventure

from adventure_graph.application.project_initialization import InitializeStarterProject
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState


@dataclass
class RecordingProjectInitializer:
    """Capture one application-level project creation request."""

    created: tuple[Adventure, PlayState] | None = None

    def create(self, adventure: Adventure, play_state: PlayState) -> None:
        self.created = adventure, play_state


def test_starter_initialization_assigns_fresh_identity_and_matching_journal() -> None:
    starter = complete_four_encounter_adventure()
    project = RecordingProjectInitializer()

    result = InitializeStarterProject(
        project,
        starter,
        adventure_id_factory=lambda: "11111111-2222-4333-8444-555555555555",
    ).execute()

    assert result.adventure.id == "11111111-2222-4333-8444-555555555555"
    assert result.adventure.title == starter.title
    assert result.adventure.encounters == starter.encounters
    assert result.play_state.adventure_id == result.adventure.id
    assert result.play_state.events == ()
    assert project.created == (result.adventure, result.play_state)
    assert starter.id != result.adventure.id
