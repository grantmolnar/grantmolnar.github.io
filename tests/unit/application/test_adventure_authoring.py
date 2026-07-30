"""Tests for revision-aware adventure metadata editing."""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.projects import InMemoryAuthoringProject, authoring_project

from adventure_graph.application.adventure_authoring import (
    UpdateAdventure,
    UpdateAdventureCommand,
)
from adventure_graph.application.errors import NoChangesRequestedError
from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.application.project import (
    ProjectRevision,
    RelatedPlayState,
    RevisionConflictError,
)
from adventure_graph.domain.adventure import AdventureTags


def _project(*, with_journal: bool = False) -> InMemoryAuthoringProject:
    adventure = complete_four_encounter_adventure()
    related = (
        (RelatedPlayState("memory://play-state", new_play_state(adventure)),)
        if with_journal
        else ()
    )
    return authoring_project(adventure, related_play_states=related)


def test_update_adventure_edits_prose_and_preserves_immutable_identifier() -> None:
    project = _project(with_journal=True)

    result = UpdateAdventure(project).execute(
        UpdateAdventureCommand(
            expected_revision=ProjectRevision("revision-1"),
            title="The Complete Four",
            synopsis="A revised synopsis.",
            premise="A revised premise.",
            explanation="A revised explanation.",
        )
    )

    assert result.after.id == "complete-four"
    assert result.after.synopsis == "A revised synopsis."
    assert project.snapshot.related_play_states[0].state.adventure_id == "complete-four"
    assert result.revision == ProjectRevision("revision-2")


def test_update_adventure_preserves_existing_tags_when_legacy_caller_omits_them() -> None:
    project = _project()
    tags = AdventureTags(genres=("Investigation",), combat_intensity="light")
    project.snapshot = replace(
        project.snapshot,
        adventure=replace(project.snapshot.adventure, tags=tags),
    )

    result = UpdateAdventure(project).execute(
        UpdateAdventureCommand(
            expected_revision=ProjectRevision("revision-1"),
            title=project.snapshot.adventure.title,
            synopsis="A revised synopsis.",
            premise=project.snapshot.adventure.premise,
            explanation=project.snapshot.adventure.explanation,
        )
    )

    assert result.after.tags == tags


def test_update_adventure_refuses_stale_empty_and_noop_edits() -> None:
    project = _project()
    adventure = project.snapshot.adventure

    with pytest.raises(RevisionConflictError):
        UpdateAdventure(project).execute(
            UpdateAdventureCommand(
                expected_revision=ProjectRevision("revision-0"),
                title=adventure.title,
                synopsis=adventure.synopsis,
                premise=adventure.premise,
                explanation=adventure.explanation,
            )
        )
    with pytest.raises(ValueError, match="title must not be empty"):
        UpdateAdventure(project).execute(
            UpdateAdventureCommand(
                expected_revision=ProjectRevision("revision-1"),
                title="  ",
                synopsis=adventure.synopsis,
                premise=adventure.premise,
                explanation=adventure.explanation,
            )
        )
    with pytest.raises(NoChangesRequestedError, match="No authoring changes"):
        UpdateAdventure(project).execute(
            UpdateAdventureCommand(
                expected_revision=ProjectRevision("revision-1"),
                title=adventure.title,
                synopsis=adventure.synopsis,
                premise=adventure.premise,
                explanation=adventure.explanation,
            )
        )
