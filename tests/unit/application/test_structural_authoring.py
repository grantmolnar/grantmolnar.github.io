"""Tests for structural read models and revision-aware creation commands."""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.projects import InMemoryAuthoringProject, authoring_project

from adventure_graph.application.play_tracking import (
    establish_revelation,
    foreclose_revelation,
    miss_clue,
    new_play_state,
    record_visit,
    reopen_revelation,
)
from adventure_graph.application.project import (
    ProjectRevision,
    RelatedPlayState,
    RevisionConflictError,
)
from adventure_graph.application.structural_authoring import (
    CreateClue,
    CreateClueCommand,
    CreateRevelation,
    CreateRevelationCommand,
    GetStructuralOverview,
    UpdateClue,
    UpdateClueCommand,
    UpdateRevelation,
    UpdateRevelationCommand,
)
from adventure_graph.domain.adventure import (
    Clue,
    Revelation,
)
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    EncounterUnlockedEvent,
    RevelationEstablishedEvent,
    RevelationForeclosedEvent,
    RevelationReopenedEvent,
)


def _project() -> InMemoryAuthoringProject:
    return authoring_project()


def test_structural_overview_synchronizes_coverage_edges_and_diagnosis() -> None:
    result = GetStructuralOverview(_project()).execute()

    assert result.revision == ProjectRevision("revision-1")
    assert len(result.coverage) == 4
    assert all(row.is_sufficient for row in result.coverage)
    assert tuple(row.revelation.id for row in result.coverage) == (
        "find-alpha",
        "find-beta",
        "find-gamma",
        "find-omega",
    )
    assert len(result.graph_edges) == 12
    edge = next(
        item
        for item in result.graph_edges
        if item.source_encounter.id == "alpha" and item.target_encounter.id == "beta"
    )
    assert tuple(clue.id for clue in edge.clues) == ("alpha-to-beta",)
    assert tuple(revelation.id for revelation in edge.revelations) == ("find-beta",)
    assert result.validation_report.edge_connectivity == 3


def test_structural_overview_reports_malformed_references_without_crashing() -> None:
    adventure = complete_four_encounter_adventure()
    malformed = replace(
        adventure,
        revelations=(
            *adventure.revelations,
            Revelation(
                id="missing-destination",
                title="Missing destination",
                description="The target is absent.",
                unlocks_encounter_id="nowhere",
            ),
        ),
        clues=(
            *adventure.clues,
            Clue(
                id="missing-source",
                title="Missing source",
                source_encounter_id="nowhere",
                revelation_id="find-beta",
            ),
            Clue(
                id="missing-revelation",
                title="Missing revelation",
                source_encounter_id="alpha",
                revelation_id="not-authored",
            ),
        ),
    )
    project = authoring_project(malformed)

    result = GetStructuralOverview(project).execute()

    assert not result.validation_report.is_valid
    assert {issue.code for issue in result.validation_report.issues} >= {
        "clue-source-missing",
        "clue-revelation-missing",
        "revelation-encounter-missing",
    }
    beta = next(row for row in result.coverage if row.revelation.id == "find-beta")
    assert "missing-source" not in {clue.id for clue in beta.supporting_clues}
    assert all(
        edge.source_encounter.id != "nowhere" and edge.target_encounter.id != "nowhere"
        for edge in result.graph_edges
    )


def test_create_clue_commits_and_recomputes_coverage() -> None:
    project = _project()

    result = CreateClue(project).execute(
        CreateClueCommand(
            expected_revision=ProjectRevision("revision-1"),
            title="A second sign points to Beta",
            source_encounter_id="alpha",
            revelation_id="find-beta",
            description="The mark repeats the route.",
            discovery="inspection",
        )
    )

    assert result.clue.discovery == "inspection"
    assert result.revision == ProjectRevision("revision-2")
    assert project.committed_adventure is not None
    assert project.committed_adventure.clue_index()["a-second-sign-points-to-beta"] == result.clue
    coverage = GetStructuralOverview(project).execute().coverage
    beta = next(row for row in coverage if row.revelation.id == "find-beta")
    assert len(beta.supporting_clues) == 4
    assert len(beta.source_encounters) == 3


def test_create_revelation_commits_optional_destination() -> None:
    project = _project()

    result = CreateRevelation(project).execute(
        CreateRevelationCommand(
            expected_revision=ProjectRevision("revision-1"),
            title="Learn the truth",
            description="The group understands the hidden pattern.",
            unlocks_encounter_id=None,
            required=False,
        )
    )

    assert not result.revelation.required
    assert result.revelation.unlocks_encounter_id is None
    assert result.revision == ProjectRevision("revision-2")
    assert project.committed_adventure is not None
    assert project.committed_adventure.revelation_index()["learn-the-truth"] == result.revelation
    assert result.validation_report.is_valid


def test_create_clue_refuses_stale_revision() -> None:
    project = _project()
    command = CreateClueCommand(
        expected_revision=ProjectRevision("revision-0"),
        title="Stale clue",
        source_encounter_id="alpha",
        revelation_id="find-beta",
    )

    with pytest.raises(RevisionConflictError, match="changed after this authoring form"):
        CreateClue(project).execute(command)

    assert project.committed_adventure is None


def test_create_revelation_refuses_stale_revision() -> None:
    project = _project()
    command = CreateRevelationCommand(
        expected_revision=ProjectRevision("revision-0"),
        title="Stale revelation",
        description="Stale.",
    )

    with pytest.raises(RevisionConflictError, match="changed after this authoring form"):
        CreateRevelation(project).execute(command)

    assert project.committed_adventure is None


def test_update_clue_preserves_identifier_and_related_journal_references() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    state = miss_clue(adventure, state, "alpha-to-beta", 1)
    state = record_visit(
        adventure,
        state,
        "alpha",
        ("alpha-to-beta",),
    )
    state = establish_revelation(adventure, state, "find-beta", ("alpha-to-beta",))
    project = authoring_project(
        adventure,
        related_play_states=(RelatedPlayState("memory://play-state", state),),
    )

    result = UpdateClue(project).execute(
        UpdateClueCommand(
            clue_id="alpha-to-beta",
            expected_revision=ProjectRevision("revision-1"),
            title="The atrium points to Beta",
            source_encounter_id="alpha",
            revelation_id="find-beta",
            description="A revised sign.",
            discovery="conversation",
        )
    )

    assert result.after.id == "alpha-to-beta"
    assert result.after.source_encounter_id == "alpha"
    assert project.snapshot.adventure.clue_index()[result.after.id] == result.after
    events = project.snapshot.related_play_states[0].state.events
    missed = next(event for event in events if isinstance(event, ClueMissedEvent))
    spotted = next(event for event in events if isinstance(event, ClueSpottedEvent))
    established = next(event for event in events if isinstance(event, RevelationEstablishedEvent))
    assert missed.clue_id == result.after.id
    assert spotted.clue_id == result.after.id
    assert established.supporting_clue_ids == (result.after.id,)


def test_update_revelation_preserves_identifier_and_related_journal_references() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta",),
    )
    state = foreclose_revelation(adventure, state, "find-beta", "The trail went cold.")
    state = reopen_revelation(adventure, state, "find-beta", "A witness returned.")
    state = establish_revelation(adventure, state, "find-beta", ("alpha-to-beta",))
    project = authoring_project(
        adventure,
        related_play_states=(RelatedPlayState("memory://play-state", state),),
    )

    result = UpdateRevelation(project).execute(
        UpdateRevelationCommand(
            revelation_id="find-beta",
            expected_revision=ProjectRevision("revision-1"),
            title="Locate Beta",
            description="The route to Beta is understood.",
            unlocks_encounter_id="beta",
            required=False,
        )
    )

    assert result.after.id == "find-beta"
    assert not result.after.required
    assert all(
        clue.revelation_id == "find-beta"
        for clue in project.snapshot.adventure.clues
        if clue.id.endswith("to-beta")
    )
    events = project.snapshot.related_play_states[0].state.events
    foreclosed = next(event for event in events if isinstance(event, RevelationForeclosedEvent))
    reopened = next(event for event in events if isinstance(event, RevelationReopenedEvent))
    established = next(event for event in events if isinstance(event, RevelationEstablishedEvent))
    unlocked = next(event for event in events if isinstance(event, EncounterUnlockedEvent))
    assert foreclosed.revelation_id == "find-beta"
    assert reopened.revelation_id == "find-beta"
    assert established.revelation_id == "find-beta"
    assert unlocked.source_revelation_id == "find-beta"


def test_update_structural_entities_refuses_stale_revisions() -> None:
    project = _project()

    with pytest.raises(RevisionConflictError):
        UpdateClue(project).execute(
            UpdateClueCommand(
                clue_id="alpha-to-beta",
                expected_revision=ProjectRevision("revision-0"),
                title="Stale clue",
                source_encounter_id="alpha",
                revelation_id="find-beta",
            )
        )
    with pytest.raises(RevisionConflictError):
        UpdateRevelation(project).execute(
            UpdateRevelationCommand(
                revelation_id="find-beta",
                expected_revision=ProjectRevision("revision-0"),
                title="Stale revelation",
                description="Stale.",
            )
        )
