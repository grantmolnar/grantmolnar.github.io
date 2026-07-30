"""Tests for transport-neutral encounter queries and revision-aware updates."""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    PLACE_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)
from tests.support.projects import InMemoryAuthoringProject, authoring_project

from adventure_graph.application.encounter_authoring import (
    GetEncounterDetail,
    RemoveEncounter,
    RemoveEncounterCommand,
    UpdateEncounter,
    UpdateEncounterCommand,
)
from adventure_graph.application.errors import NoChangesRequestedError
from adventure_graph.application.play_tracking import (
    new_play_state,
    record_visit,
)
from adventure_graph.application.project import (
    ProjectRevision,
    RelatedPlayState,
    RevisionConflictError,
)
from adventure_graph.application.structural_authoring import (
    CreateEncounter,
    CreateEncounterCommand,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_events import EncounterVisitedEvent


def _project(
    adventure: Adventure | None = None,
    related_play_states: tuple[RelatedPlayState, ...] = (),
) -> InMemoryAuthoringProject:
    return authoring_project(adventure, related_play_states=related_play_states)


def test_create_encounter_commits_to_an_empty_adventure_shell() -> None:
    adventure = replace(
        complete_four_encounter_adventure(),
        encounters=(),
        revelations=(),
        clues=(),
    )
    project = _project(adventure)

    result = CreateEncounter(project).execute(
        CreateEncounterCommand(
            expected_revision=ProjectRevision("revision-1"),
            title="The First Threshold",
            summary="A place to begin.",
            start=True,
        )
    )

    assert result.encounter.id == "the-first-threshold"
    assert result.encounter.start
    assert result.revision == ProjectRevision("revision-2")
    assert project.committed_adventure is not None
    assert project.committed_adventure.encounters == (result.encounter,)


def test_create_encounter_rejects_empty_title_or_stale_revision() -> None:
    project = _project()

    with pytest.raises(ValueError, match="title must not be empty"):
        CreateEncounter(project).execute(
            CreateEncounterCommand(ProjectRevision("revision-1"), "   ")
        )
    with pytest.raises(RevisionConflictError, match="form was loaded"):
        CreateEncounter(project).execute(
            CreateEncounterCommand(ProjectRevision("stale"), "New Room")
        )

    assert project.committed_adventure is None


def test_encounter_detail_combines_authored_relationships_and_revision() -> None:
    project = _project()

    result = GetEncounterDetail(project).execute("beta")

    assert result.adventure.id == "complete-four"
    assert result.revision == ProjectRevision("revision-1")
    assert result.detail.encounter.id == "beta"
    assert tuple(clue.id for clue in result.detail.sourced_clues) == (
        "beta-to-alpha",
        "beta-to-gamma",
        "beta-to-omega",
    )
    assert tuple(revelation.id for revelation in result.detail.supported_revelations) == (
        "find-alpha",
        "find-gamma",
        "find-omega",
    )
    assert tuple(encounter.id for encounter in result.detail.destination_encounters) == (
        "alpha",
        "gamma",
        "omega",
    )
    assert tuple(revelation.id for revelation in result.detail.unlocking_revelations) == (
        "find-beta",
    )
    assert tuple(clue.id for clue in result.detail.incoming_clues) == (
        "alpha-to-beta",
        "gamma-to-beta",
        "omega-to-beta",
    )
    assert result.validation_report.is_valid
    assert "Lead: beta points to alpha" in result.detail.dependency_preview.authored_references
    assert "Revelation: Find Beta" in result.detail.dependency_preview.removal_dependencies
    assert "Remove lead: beta points to alpha" in result.detail.dependency_preview.cascade_effects


def test_update_encounter_commits_changed_fields_and_returns_new_revision() -> None:
    project = _project()

    result = UpdateEncounter(project).execute(
        UpdateEncounterCommand(
            encounter_id="alpha",
            expected_revision=ProjectRevision("revision-1"),
            title="Atrium",
            content="Long-form encounter material.",
            tags=("urban", "start"),
        )
    )

    assert result.before.title == "Alpha"
    assert result.after.title == "Atrium"
    assert result.after.content == "Long-form encounter material."
    assert result.after.tags == ("urban", "start")
    assert result.revision == ProjectRevision("revision-2")
    assert project.committed_adventure is not None
    assert result.after.id == "alpha"
    assert project.committed_adventure.encounter_index()["alpha"] == result.after


def test_update_encounter_refuses_stale_revision_before_mutation() -> None:
    project = _project()

    with pytest.raises(RevisionConflictError, match="changed after this encounter was loaded"):
        UpdateEncounter(project).execute(
            UpdateEncounterCommand(
                encounter_id="alpha",
                expected_revision=ProjectRevision("revision-0"),
                title="Stale edit",
            )
        )

    assert project.committed_adventure is None


def test_update_encounter_refuses_changes_that_invalidate_a_related_journal() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    project = _project(adventure, (RelatedPlayState("memory://play-state", state),))

    with pytest.raises(ValueError, match=r"memory://play-state.*visits locked encounter"):
        UpdateEncounter(project).execute(
            UpdateEncounterCommand(
                encounter_id="alpha",
                expected_revision=ProjectRevision("revision-1"),
                start=False,
            )
        )

    assert project.committed_adventure is None


def test_update_encounter_refuses_noop_edits() -> None:
    project = _project()

    with pytest.raises(NoChangesRequestedError, match="No authoring changes"):
        UpdateEncounter(project).execute(
            UpdateEncounterCommand(
                encounter_id="alpha",
                expected_revision=ProjectRevision("revision-1"),
                title="Alpha",
            )
        )


def test_title_change_preserves_encounter_and_journal_identifiers() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    project = _project(adventure, (RelatedPlayState("memory://play-state", state),))

    result = UpdateEncounter(project).execute(
        UpdateEncounterCommand(
            encounter_id="alpha",
            expected_revision=ProjectRevision("revision-1"),
            title="The Atrium",
        )
    )

    assert result.after.id == "alpha"
    related = project.snapshot.related_play_states[0]
    visit = related.state.events[0]
    assert isinstance(visit, EncounterVisitedEvent)
    assert visit.encounter_id == "alpha"
    assert project.snapshot.adventure.encounter_index()["alpha"].title == "The Atrium"


def test_encounter_detail_includes_ordered_reference_links_and_context() -> None:
    result = GetEncounterDetail(_project(reference_library_adventure())).execute("alpha")

    assert tuple(item.reference_id for item in result.detail.linked_references) == (
        PERSON_REFERENCE_ID,
        PLACE_REFERENCE_ID,
    )
    assert result.detail.linked_references[0].reference is not None
    assert result.detail.linked_references[0].reference.title == "Cora Pike"
    assert result.detail.linked_references[0].context == (
        "Cora controls access to the first-floor rooms."
    )
    assert any(
        "Reference link: Cora Pike" in item
        for item in result.detail.dependency_preview.removal_dependencies
    )


def test_encounter_edit_preserves_existing_reference_links() -> None:
    adventure = reference_library_adventure()
    before_links = adventure.encounter_index()["alpha"].reference_links
    project = _project(adventure)

    result = UpdateEncounter(project).execute(
        UpdateEncounterCommand(
            encounter_id="alpha",
            expected_revision=ProjectRevision("revision-1"),
            title="The Entry Hall",
        )
    )

    assert result.after.reference_links == before_links
    assert project.snapshot.adventure.encounter_index()["alpha"].reference_links == before_links


def test_remove_encounter_refuses_reference_links_then_retains_references_on_cascade() -> None:
    project = _project(reference_library_adventure())

    with pytest.raises(ValueError, match="reference links"):
        RemoveEncounter(project).execute(
            RemoveEncounterCommand(
                encounter_id="alpha",
                expected_revision=ProjectRevision("revision-1"),
            )
        )

    result = RemoveEncounter(project).execute(
        RemoveEncounterCommand(
            encounter_id="alpha",
            expected_revision=ProjectRevision("revision-1"),
            cascade=True,
        )
    )

    assert result.dependencies.linked_reference_ids == (
        PERSON_REFERENCE_ID,
        PLACE_REFERENCE_ID,
    )
    assert "alpha" not in project.snapshot.adventure.encounter_index()
    assert tuple(reference.id for reference in project.snapshot.adventure.references) == (
        PERSON_REFERENCE_ID,
        PLACE_REFERENCE_ID,
    )


def test_remove_encounter_remains_blocked_by_related_journal_after_cascade() -> None:
    adventure = reference_library_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    project = _project(adventure, (RelatedPlayState("memory://play-state", state),))

    with pytest.raises(ValueError, match=r"memory://play-state.*Unknown encounter"):
        RemoveEncounter(project).execute(
            RemoveEncounterCommand(
                encounter_id="alpha",
                expected_revision=ProjectRevision("revision-1"),
                cascade=True,
            )
        )

    assert project.committed_adventure is None
