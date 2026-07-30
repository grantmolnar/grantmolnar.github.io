"""Tests for the revision-aware play-journal application boundary."""

from __future__ import annotations

import pytest
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.projects import InMemoryPlayProject, play_project

from adventure_graph.application.play_journal import (
    CorrectLatestPlayOperation,
    CorrectLatestPlayOperationCommand,
    GetPlayJournalStatus,
)
from adventure_graph.application.play_tracking import (
    end_session,
    foreclose_revelation,
    miss_clue,
    new_play_state,
    record_visit,
    reopen_revelation,
    start_session,
)
from adventure_graph.application.project import (
    ProjectRevision,
    RevisionConflictError,
)


def _project() -> InMemoryPlayProject:
    adventure = complete_four_encounter_adventure()
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta",),
        ("Accidental operation.",),
    )
    return play_project(state, adventure)


def test_journal_status_groups_compound_events_into_one_active_operation() -> None:
    project = _project()

    result = GetPlayJournalStatus(project).execute()

    assert result.event_count == 3
    assert result.active_event_count == 3
    assert result.latest_active_operation_number == 1
    assert len(result.operations) == 1
    assert result.operations[0].active
    assert [event.kind for event in result.operations[0].events] == [
        "encounter_visited",
        "clue_spotted",
        "visit_note_recorded",
    ]


def test_journal_status_exposes_session_miss_and_judgment_metadata() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(
        new_play_state(adventure),
        title="The western breach",
        played_on="2026-07-18",
        participants=("Mara", "Sera"),
        attendance_note="Torren was absent.",
        opening_note="The party resumed beneath the aqueduct.",
    )
    state = record_visit(adventure, state, "alpha", party_label="Canal team")
    state = miss_clue(adventure, state, "alpha-to-beta", 1)
    state = foreclose_revelation(adventure, state, "find-beta", "The witness left the city.")
    state = reopen_revelation(adventure, state, "find-beta", "The witness returned under guard.")
    state = end_session(state, "The party withdrew before dusk.")
    project = play_project(state, adventure)

    result = GetPlayJournalStatus(project).execute()
    events = [event for operation in result.operations for event in operation.events]

    assert [event.kind for event in events] == [
        "session_started",
        "encounter_visited",
        "clue_missed",
        "revelation_foreclosed",
        "revelation_reopened",
        "session_ended",
    ]
    assert events[0].title == "The western breach"
    assert events[0].participants == ("Mara", "Sera")
    assert events[0].attendance_note == "Torren was absent."
    assert events[1].party_label == "Canal team"
    assert events[-1].text == "The party withdrew before dusk."


def test_correction_command_commits_audit_event_and_updates_status() -> None:
    project = _project()

    result = CorrectLatestPlayOperation(project).execute(
        CorrectLatestPlayOperationCommand(
            reason="The visit did not occur.",
            expected_revision=ProjectRevision("revision-1"),
        )
    )
    status = GetPlayJournalStatus(project).execute()

    assert result.target_operation_number == 1
    assert result.correction_sequence == 4
    assert result.revision == ProjectRevision("revision-2")
    assert status.active_event_count == 0
    assert status.correction_count == 1
    assert status.operations[0].active is False
    assert status.operations[1].is_correction


def test_correction_command_refuses_stale_revision_without_committing() -> None:
    project = _project()
    before = project.snapshot

    with pytest.raises(RevisionConflictError, match="stale journal revision"):
        CorrectLatestPlayOperation(project).execute(
            CorrectLatestPlayOperationCommand(
                reason="Wrong click.",
                expected_revision=ProjectRevision("obsolete"),
            )
        )

    assert project.snapshot == before
