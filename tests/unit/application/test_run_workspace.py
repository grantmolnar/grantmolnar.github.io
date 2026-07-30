"""Tests for the revision-aware live session application boundary."""

from __future__ import annotations

import pytest
from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)
from tests.support.projects import InMemoryPlayProject, play_project

from adventure_graph.application.dice import roll_dice
from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.application.project import (
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.application.run_workspace import (
    AddPlayVisitNote,
    AddVisitNoteCommand,
    EndPlaySession,
    EndSessionCommand,
    EstablishPlayRevelation,
    EstablishRevelationCommand,
    ForeclosePlayRevelation,
    GetRunDashboard,
    MissClueCommand,
    MissPlayClue,
    RecordDiceRollCommand,
    RecordEncounterConsequenceCommand,
    RecordPlayDiceRoll,
    RecordPlayEncounterConsequence,
    RecordPlayReferenceNote,
    RecordPlayVisit,
    RecordReferenceNoteCommand,
    RecordVisitCommand,
    ReopenPlayRevelation,
    RevelationJudgmentCommand,
    SpotClueCommand,
    SpotPlayClue,
    StartPlaySession,
    StartSessionCommand,
    TransitionPlayVisit,
    TransitionVisitCommand,
    UnlockEncounterCommand,
    UnlockPlayEncounter,
)
from adventure_graph.domain.play_events import DiceRollRecordedEvent


def _project() -> InMemoryPlayProject:
    adventure = complete_four_encounter_adventure()
    return play_project(new_play_state(adventure), adventure)


def test_empty_run_dashboard_exposes_entry_encounter_and_locked_encounters() -> None:
    project = _project()

    result = GetRunDashboard(project).execute()

    assert result.current_visit is None
    assert result.current_encounter is None
    assert [item.encounter.id for item in result.available_encounters] == ["alpha"]
    assert [encounter.id for encounter in result.locked_encounters] == ["beta", "gamma", "omega"]
    assert result.total_operation_count == 0
    assert result.latest_active_operation_number is None


def test_run_dashboard_exposes_reference_records_and_encounter_order_backlinks() -> None:
    adventure = reference_library_adventure()
    project = play_project(new_play_state(adventure), adventure)

    result = GetRunDashboard(project).execute()

    status = result.reference_status_index()[PERSON_REFERENCE_ID]
    assert status.reference.title == "Cora Pike"
    assert [item.encounter.id for item in status.backlinks] == ["alpha", "beta"]
    assert [item.context for item in status.backlinks] == [
        "Cora controls access to the first-floor rooms.",
        "Cora may change allegiance after hearing the testimony.",
    ]


def test_visit_dashboard_exposes_current_material_clues_and_recent_operation() -> None:
    project = _project()
    visit = RecordPlayVisit(project).execute(
        RecordVisitCommand(
            expected_revision=ProjectRevision("revision-1"),
            encounter_id="alpha",
            spotted_clue_ids=("alpha-to-beta",),
            notes=("The party inspected the eastern wall.",),
        )
    )

    result = GetRunDashboard(project).execute()

    assert visit.visit_number == 1
    assert visit.operation_number == 1
    assert result.current_encounter is not None
    assert result.current_encounter.id == "alpha"
    assert result.current_visit is not None
    assert result.current_visit.notes == ("The party inspected the eastern wall.",)
    assert {item.clue.id: item.spotted for item in result.current_clues}["alpha-to-beta"]
    assert result.available_encounters[0].encounter.id == "alpha"
    assert result.total_operation_count == 1
    assert result.recent_operations[0].operation_number == 1


def test_run_commands_commit_revelation_unlock_notes_consequences_and_clues() -> None:
    project = _project()
    visit = RecordPlayVisit(project).execute(
        RecordVisitCommand(
            expected_revision=ProjectRevision("revision-1"),
            encounter_id="alpha",
            spotted_clue_ids=("alpha-to-beta",),
        )
    )
    revelation = EstablishPlayRevelation(project).execute(
        EstablishRevelationCommand(
            expected_revision=visit.revision,
            revelation_id="find-beta",
            supporting_clue_ids=("alpha-to-beta",),
            note="The eastern wall marks the route.",
        )
    )
    second_visit = RecordPlayVisit(project).execute(
        RecordVisitCommand(
            expected_revision=revelation.revision,
            encounter_id="beta",
        )
    )
    clue = SpotPlayClue(project).execute(
        SpotClueCommand(
            expected_revision=second_visit.revision,
            clue_id="beta-to-gamma",
            visit_number=2,
        )
    )
    note = AddPlayVisitNote(project).execute(
        AddVisitNoteCommand(
            expected_revision=clue.revision,
            visit_number=2,
            text="The guards withdrew.",
        )
    )
    consequence = RecordPlayEncounterConsequence(project).execute(
        RecordEncounterConsequenceCommand(
            expected_revision=note.revision,
            encounter_id="beta",
            text="The western gate now stands open.",
        )
    )

    result = GetRunDashboard(project).execute()

    assert revelation.operation_number == 2
    assert second_visit.visit_number == 2
    assert clue.operation_number == 4
    assert note.operation_number == 5
    assert consequence.operation_number == 6
    assert {item.encounter.id for item in result.available_encounters} == {"alpha", "beta"}
    assert result.current_visit is not None
    assert result.current_visit.notes == ("The guards withdrew.",)
    assert [item.text for item in result.current_consequences] == [
        "The western gate now stands open."
    ]
    find_beta = next(
        item for item in result.revelation_statuses if item.revelation.id == "find-beta"
    )
    assert find_beta.is_established
    assert find_beta.establishment_clue_ids == ("alpha-to-beta",)


def test_significant_roll_records_the_generated_result_without_rerolling() -> None:
    project = _project()
    roll = roll_dice("2d6 + 3", randbelow=lambda bound: bound - 1)

    recorded = RecordPlayDiceRoll(project).execute(
        RecordDiceRollCommand(
            expected_revision=ProjectRevision("revision-1"),
            result=roll,
            label="Hold the gate",
        )
    )

    event = project.snapshot.state.events[-1]
    assert recorded.operation_number == 1
    assert isinstance(event, DiceRollRecordedEvent)
    assert event.expression == "2d6 + 3"
    assert event.total == 15
    assert event.label == "Hold the gate"


def test_manual_unlock_and_stale_revision_refusal() -> None:
    project = _project()

    result = UnlockPlayEncounter(project).execute(
        UnlockEncounterCommand(
            expected_revision=ProjectRevision("revision-1"),
            encounter_id="gamma",
            reason="The ferryman offers an alternate route.",
        )
    )

    assert result.operation_number == 1
    assert {
        item.encounter.id for item in GetRunDashboard(project).execute().available_encounters
    } == {
        "alpha",
        "gamma",
    }

    before = project.snapshot
    with pytest.raises(RevisionConflictError, match="session view was loaded"):
        RecordPlayVisit(project).execute(
            RecordVisitCommand(
                expected_revision=ProjectRevision("obsolete"),
                encounter_id="alpha",
            )
        )
    assert project.snapshot == before


def test_visit_note_rejects_a_stale_revision_without_committing() -> None:
    project = _project()
    visit = RecordPlayVisit(project).execute(
        RecordVisitCommand(
            expected_revision=ProjectRevision("revision-1"),
            encounter_id="alpha",
        )
    )
    before = project.snapshot

    with pytest.raises(RevisionConflictError, match="session view was loaded"):
        AddPlayVisitNote(project).execute(
            AddVisitNoteCommand(
                expected_revision=ProjectRevision("obsolete"),
                visit_number=visit.visit_number,
                text="This note was based on stale state.",
            )
        )

    assert project.snapshot == before


def test_run_dashboard_rejects_nonpositive_recent_operation_limit() -> None:
    with pytest.raises(ValueError, match="must be positive"):
        GetRunDashboard(_project(), recent_operation_limit=0)


def test_session_miss_and_revelation_judgment_services_share_revision_boundary() -> None:
    project = _project()
    started = StartPlaySession(project).execute(
        StartSessionCommand(
            expected_revision=ProjectRevision("revision-1"),
            title="Session one",
            participants=("Mara", "Sera"),
        )
    )
    visit = RecordPlayVisit(project).execute(
        RecordVisitCommand(
            expected_revision=started.revision,
            encounter_id="alpha",
            party_label="Main party",
        )
    )
    missed = MissPlayClue(project).execute(
        MissClueCommand(
            expected_revision=visit.revision,
            clue_id="alpha-to-beta",
            visit_number=1,
        )
    )
    foreclosed = ForeclosePlayRevelation(project).execute(
        RevelationJudgmentCommand(
            expected_revision=missed.revision,
            revelation_id="find-beta",
            reason="The witness fled.",
        )
    )
    reopened = ReopenPlayRevelation(project).execute(
        RevelationJudgmentCommand(
            expected_revision=foreclosed.revision,
            revelation_id="find-beta",
            reason="The witness returned.",
        )
    )
    ended = EndPlaySession(project).execute(
        EndSessionCommand(
            expected_revision=reopened.revision,
            closing_note="The party camped outside.",
        )
    )

    result = GetRunDashboard(project).execute()
    find_beta = next(
        item for item in result.revelation_statuses if item.revelation.id == "find-beta"
    )

    assert ended.operation_number == 6
    assert result.projection.active_session_number is None
    assert result.projection.sessions[0].closing_note == "The party camped outside."
    assert result.current_visit is not None
    assert result.current_visit.party_label == "Main party"
    assert result.current_clues[0].missed_visit_numbers == (1,)
    assert not find_beta.is_foreclosed


def test_transition_service_commits_once_and_returns_destination_visit() -> None:
    project = _project()
    started = StartPlaySession(project).execute(
        StartSessionCommand(ProjectRevision("revision-1"), title="Session one")
    )
    entered = RecordPlayVisit(project).execute(
        RecordVisitCommand(started.revision, encounter_id="alpha")
    )

    result = TransitionPlayVisit(project).execute(
        TransitionVisitCommand(
            expected_revision=entered.revision,
            source_visit_number=entered.visit_number,
            notes=("The party searched the eastern wall.",),
            spotted_clue_ids=("alpha-to-beta",),
            missed_clue_ids=("alpha-to-gamma",),
            established_revelation_ids=("find-beta",),
            consequence_texts=("The watch opens the eastern gate.",),
            destination_encounter_id="beta",
            destination_party_label="Main party",
        )
    )

    dashboard = GetRunDashboard(project).execute()
    assert result.operation_number == 3
    assert result.destination_visit_number == 2
    assert project.commit_count == 3
    assert dashboard.current_encounter is not None
    assert dashboard.current_encounter.id == "beta"
    assert dashboard.current_visit is not None
    assert dashboard.current_visit.party_label == "Main party"
    operation = next(item for item in dashboard.recent_operations if item.operation_number == 3)
    assert len(operation.events) == 7


def test_reference_note_service_commits_and_dashboard_groups_notes_by_identity() -> None:
    adventure = reference_library_adventure()
    project = play_project(new_play_state(adventure), adventure)

    committed = RecordPlayReferenceNote(project).execute(
        RecordReferenceNoteCommand(
            expected_revision=ProjectRevision("revision-1"),
            reference_id=PERSON_REFERENCE_ID,
            text="Cora moved the witnesses into the pantry.",
        )
    )
    dashboard = GetRunDashboard(project).execute()
    status = dashboard.reference_status_index()[PERSON_REFERENCE_ID]

    assert committed.operation_number == 1
    assert committed.revision == ProjectRevision("revision-2")
    assert [note.text for note in status.notes] == ["Cora moved the witnesses into the pantry."]
    assert status.notes[0].reference_id == PERSON_REFERENCE_ID


def test_reference_note_service_rejects_stale_revision_without_committing() -> None:
    adventure = reference_library_adventure()
    project = play_project(new_play_state(adventure), adventure)
    before = project.snapshot

    with pytest.raises(RevisionConflictError):
        RecordPlayReferenceNote(project).execute(
            RecordReferenceNoteCommand(
                expected_revision=ProjectRevision("obsolete"),
                reference_id=PERSON_REFERENCE_ID,
                text="Stale note",
            )
        )

    assert project.snapshot == before
