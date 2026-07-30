"""Tests for deterministic projection of valid play journals."""

from __future__ import annotations

import pytest
from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)

from adventure_graph.application.play_errors import PlayTrackingError
from adventure_graph.application.play_projection import project_play_state
from adventure_graph.application.play_tracking import (
    add_visit_note,
    correct_latest_operation,
    end_session,
    establish_revelation,
    foreclose_revelation,
    miss_clue,
    new_play_state,
    record_encounter_consequence,
    record_reference_note,
    record_visit,
    reopen_revelation,
    spot_clue,
    start_session,
    transition_visit,
    unlock_encounter,
)
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    DiceGroupResult,
    DiceModifierResult,
    DiceRollRecordedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    PlayOperationVoidedEvent,
    ReferenceNoteRecordedEvent,
    RevelationEstablishedEvent,
    RevelationForeclosedEvent,
    RevelationReopenedEvent,
    VisitNoteRecordedEvent,
)
from adventure_graph.domain.play_state import PlayState


def test_spotted_clue_does_not_establish_revelation_or_unlock_encounter() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta",),
    )

    projection = project_play_state(adventure, state)
    progress = projection.revelation_progress_index()["find-beta"]

    assert progress.spotted_clue_ids == ("alpha-to-beta",)
    assert not progress.is_established
    assert projection.available_encounter_ids == ("alpha",)
    with pytest.raises(PlayTrackingError, match="is locked"):
        record_visit(adventure, state, "beta")


def test_transition_commits_ordered_table_developments_as_one_correctable_operation() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Session one")
    state = record_visit(adventure, state, "alpha", party_label="Main party")

    transitioned = transition_visit(
        adventure,
        state,
        1,
        notes=("The party questioned the watch captain.",),
        spotted_clue_ids=("alpha-to-beta",),
        missed_clue_ids=("alpha-to-gamma",),
        established_revelation_ids=("find-beta",),
        consequence_texts=("The watch now trusts the party.",),
        destination_encounter_id="beta",
        destination_party_label="Scouting pair",
    )

    transition_events = transitioned.events[len(state.events) :]
    assert [type(event) for event in transition_events] == [
        VisitNoteRecordedEvent,
        ClueSpottedEvent,
        ClueMissedEvent,
        RevelationEstablishedEvent,
        EncounterUnlockedEvent,
        EncounterConsequenceRecordedEvent,
        EncounterVisitedEvent,
    ]
    assert {event.operation_number for event in transition_events} == {3}

    projection = project_play_state(adventure, transitioned)
    assert [visit.encounter_id for visit in projection.visits] == ["alpha", "beta"]
    assert projection.visits[0].notes == ("The party questioned the watch captain.",)
    assert projection.visits[0].spotted_clue_ids == ("alpha-to-beta",)
    assert projection.visits[0].missed_clue_ids == ("alpha-to-gamma",)
    assert projection.visits[1].party_label == "Scouting pair"
    assert projection.revelation_progress_index()["find-beta"].is_established
    assert projection.available_encounter_ids == ("alpha", "beta")

    corrected = correct_latest_operation(adventure, transitioned, "The party remained at Alpha.")
    corrected_projection = project_play_state(adventure, corrected)
    correction = corrected.events[-1]
    assert isinstance(correction, PlayOperationVoidedEvent)
    assert correction.target_operation_number == 3
    assert [visit.encounter_id for visit in corrected_projection.visits] == ["alpha"]
    assert corrected_projection.visits[0].notes == ()
    assert corrected_projection.visits[0].spotted_clue_ids == ()
    assert corrected_projection.visits[0].missed_clue_ids == ()
    assert not corrected_projection.revelation_progress_index()["find-beta"].is_established
    assert corrected_projection.available_encounter_ids == ("alpha",)
    assert corrected_projection.consequences == ()


def test_transition_can_establish_multiple_revelations_from_newly_spotted_clues() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Session one")
    state = record_visit(adventure, state, "alpha")

    transitioned = transition_visit(
        adventure,
        state,
        1,
        spotted_clue_ids=("alpha-to-beta", "alpha-to-gamma"),
        established_revelation_ids=("find-beta", "find-gamma"),
    )

    transition_events = transitioned.events[len(state.events) :]
    assert [type(event) for event in transition_events] == [
        ClueSpottedEvent,
        ClueSpottedEvent,
        RevelationEstablishedEvent,
        EncounterUnlockedEvent,
        RevelationEstablishedEvent,
        EncounterUnlockedEvent,
    ]
    assert {event.operation_number for event in transition_events} == {3}
    projection = project_play_state(adventure, transitioned)
    assert projection.available_encounter_ids == ("alpha", "beta", "gamma")
    assert projection.revelation_progress_index()["find-beta"].is_established
    assert projection.revelation_progress_index()["find-gamma"].is_established


def test_transition_can_establish_multiple_revelations_from_already_spotted_clues() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Session one")
    state = record_visit(
        adventure,
        state,
        "alpha",
        spotted_clue_ids=("alpha-to-beta", "alpha-to-gamma"),
    )

    transitioned = transition_visit(
        adventure,
        state,
        1,
        established_revelation_ids=("find-beta", "find-gamma"),
        destination_encounter_id="beta",
    )

    transition_events = transitioned.events[len(state.events) :]
    assert [type(event) for event in transition_events] == [
        RevelationEstablishedEvent,
        EncounterUnlockedEvent,
        RevelationEstablishedEvent,
        EncounterUnlockedEvent,
        EncounterVisitedEvent,
    ]
    assert {event.operation_number for event in transition_events} == {3}
    projection = project_play_state(adventure, transitioned)
    assert projection.visits[-1].encounter_id == "beta"
    assert projection.available_encounter_ids == ("alpha", "beta", "gamma")


def test_establishing_revelation_records_basis_and_unlocks_destination() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta",),
        ("The group copied the address.",),
    )
    state = establish_revelation(
        adventure,
        state,
        "find-beta",
        ("alpha-to-beta",),
        "They connected the address to Beta.",
    )
    state = record_visit(adventure, state, "beta", ("beta-to-omega",))
    state = add_visit_note(state, 1, "They later returned to the scene.")

    projection = project_play_state(adventure, state)
    progress = projection.revelation_progress_index()["find-beta"]

    assert [type(event) for event in state.events] == [
        EncounterVisitedEvent,
        ClueSpottedEvent,
        VisitNoteRecordedEvent,
        RevelationEstablishedEvent,
        EncounterUnlockedEvent,
        EncounterVisitedEvent,
        ClueSpottedEvent,
        VisitNoteRecordedEvent,
    ]
    assert progress.is_established
    assert progress.establishment_clue_ids == ("alpha-to-beta",)
    assert progress.establishment_note == "They connected the address to Beta."
    assert projection.available_encounter_ids == ("alpha", "beta")
    assert projection.visits[0].notes[-1] == "They later returned to the scene."


def test_revelation_can_be_established_without_recorded_clue_basis() -> None:
    adventure = complete_four_encounter_adventure()
    state = establish_revelation(
        adventure,
        new_play_state(adventure),
        "find-beta",
        note="The captive gave the location directly.",
    )

    progress = project_play_state(adventure, state).revelation_progress_index()["find-beta"]
    assert progress.is_established
    assert progress.establishment_clue_ids == ()
    assert "beta" in project_play_state(adventure, state).available_encounter_ids


def test_manual_unlock_and_encounter_consequence_are_explicit_events() -> None:
    adventure = complete_four_encounter_adventure()
    state = unlock_encounter(
        adventure,
        new_play_state(adventure),
        "gamma",
        "The ferryman carried the group there without a clue.",
    )
    state = record_visit(adventure, state, "gamma")
    state = record_encounter_consequence(
        adventure,
        state,
        "gamma",
        "The observatory roof collapsed during the escape.",
    )

    projection = project_play_state(adventure, state)
    assert isinstance(state.events[0], EncounterUnlockedEvent)
    assert isinstance(state.events[-1], EncounterConsequenceRecordedEvent)
    assert projection.available_encounter_ids == ("alpha", "gamma")
    assert projection.consequences[0].text.startswith("The observatory")


def test_visit_notes_are_append_only_events() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    before = state.events
    state = add_visit_note(state, 1, "A later annotation.")

    assert state.events[:-1] == before
    assert isinstance(state.events[-1], VisitNoteRecordedEvent)
    assert state.visits[0].notes == ("A later annotation.",)


def test_explicit_sessions_preserve_global_visit_order_and_party_labels() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    state = start_session(
        state,
        title="First explicit session",
        played_on="2026-07-18",
        participants=("Mara", "Sera"),
        opening_note="The party resumed at the gate.",
    )
    state = record_visit(adventure, state, "alpha", party_label="Mara and Sera")
    state = end_session(state, "They withdrew before dusk.")
    state = start_session(state, title="Return")
    state = record_visit(adventure, state, "alpha", party_label="Mara")

    projection = project_play_state(adventure, state)

    assert [visit.visit_number for visit in projection.visits] == [1, 2, 3]
    assert [visit.party_label for visit in projection.visits] == ["", "Mara and Sera", "Mara"]
    assert [session.session_number for session in projection.sessions] == [1, 2]
    assert projection.sessions[0].visit_numbers == (2,)
    assert projection.sessions[0].closing_note == "They withdrew before dusk."
    assert projection.sessions[1].is_active
    assert projection.sessions[1].visit_numbers == (3,)
    assert projection.active_session_number == 2
    assert [item.session_number for item in projection.narrative] == [None, 1, 1, 1, 2, 2]


def test_session_operation_numbers_list_each_compound_operation_once() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Compound operation")
    state = record_visit(
        adventure,
        state,
        "alpha",
        ("alpha-to-beta",),
        ("The party compared the two seals.",),
    )

    projection = project_play_state(adventure, state)

    assert projection.sessions[0].operation_numbers == (1, 2)
    assert [event.operation_number for event in state.events] == [1, 2, 2, 2]


def test_missed_clue_can_be_recovered_on_a_later_visit() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    state = miss_clue(adventure, state, "alpha-to-beta", 1)

    with pytest.raises(PlayTrackingError, match="already marked missed"):
        miss_clue(adventure, state, "alpha-to-beta", 1)

    state = record_visit(adventure, state, "alpha")
    state = spot_clue(adventure, state, "alpha-to-beta", 2)
    projection = project_play_state(adventure, state)
    clue = projection.clue_progress_index()["alpha-to-beta"]

    assert isinstance(state.events[1], ClueMissedEvent)
    assert clue.missed_visit_numbers == (1,)
    assert clue.spotted_visit_number == 2
    assert clue.is_spotted
    assert projection.visits[0].missed_clue_ids == ("alpha-to-beta",)
    assert projection.visits[1].spotted_clue_ids == ("alpha-to-beta",)
    with pytest.raises(PlayTrackingError, match="already spotted"):
        miss_clue(adventure, state, "alpha-to-beta", 2)


def test_revelation_foreclosure_and_reopening_preserve_derived_support() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta",),
    )
    state = foreclose_revelation(
        adventure,
        state,
        "find-beta",
        "The witness left the city.",
    )
    progress = project_play_state(adventure, state).revelation_progress_index()["find-beta"]

    assert isinstance(state.events[-1], RevelationForeclosedEvent)
    assert progress.is_supported
    assert progress.is_foreclosed
    with pytest.raises(PlayTrackingError, match="must be reopened"):
        establish_revelation(adventure, state, "find-beta", ("alpha-to-beta",))

    state = reopen_revelation(
        adventure,
        state,
        "find-beta",
        "The witness returned under guard.",
    )
    progress = project_play_state(adventure, state).revelation_progress_index()["find-beta"]

    assert isinstance(state.events[-1], RevelationReopenedEvent)
    assert progress.is_supported
    assert not progress.is_foreclosed
    assert progress.reopening_sequences == (4,)
    state = establish_revelation(adventure, state, "find-beta", ("alpha-to-beta",))
    with pytest.raises(PlayTrackingError, match="cannot be foreclosed"):
        foreclose_revelation(adventure, state, "find-beta", "Too late.")


def test_corrections_reopen_session_and_restore_foreclosure_state() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Session one")
    state = foreclose_revelation(adventure, state, "find-beta", "The trail went cold.")
    state = reopen_revelation(adventure, state, "find-beta", "A new witness appeared.")

    state = correct_latest_operation(adventure, state, "The witness did not appear.")
    projection = project_play_state(adventure, state)
    assert projection.revelation_progress_index()["find-beta"].is_foreclosed

    state = correct_latest_operation(adventure, state, "The trail remains open after all.")
    projection = project_play_state(adventure, state)
    assert not projection.revelation_progress_index()["find-beta"].is_foreclosed

    state = end_session(state)
    state = correct_latest_operation(adventure, state, "The session is still underway.")
    assert project_play_state(adventure, state).active_session_number == 1


def test_recorded_dice_roll_projects_a_narrative_entry() -> None:
    adventure = complete_four_encounter_adventure()
    state = PlayState(
        adventure_id=adventure.id,
        events=(
            DiceRollRecordedEvent(
                sequence=1,
                expression="2d8 + 3",
                label="Hold the gate",
                terms=(DiceGroupResult(1, 8, (6, 3)), DiceModifierResult(3)),
                total=12,
                operation_number=1,
            ),
        ),
    )

    projection = project_play_state(adventure, state)

    assert projection.narrative[0].kind == "dice_roll_recorded"
    assert projection.narrative[0].text == "Hold the gate: 2d8 + 3 = 12"


def test_play_state_visit_view_matches_full_projection_for_supported_history() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta",),
        ("The group copied the address.",),
        party_label="Main party",
    )
    state = record_visit(adventure, state, "alpha", party_label="Scout")
    state = miss_clue(adventure, state, "alpha-to-gamma", 2)
    state = add_visit_note(state, 2, "The scout marked the sealed stair.")
    state = correct_latest_operation(adventure, state, "The note belonged to another visit.")

    assert state.visits == project_play_state(adventure, state).visits


def test_reference_notes_project_into_entity_history_and_chronology() -> None:
    adventure = reference_library_adventure()
    state = start_session(new_play_state(adventure), title="At the gate")
    state = record_reference_note(
        adventure,
        state,
        PERSON_REFERENCE_ID,
        "Cora agreed to hide the witnesses.",
    )

    projection = project_play_state(adventure, state)

    assert len(projection.reference_notes) == 1
    note = projection.reference_notes[0]
    assert note.reference_id == PERSON_REFERENCE_ID
    assert note.text == "Cora agreed to hide the witnesses."
    assert note.session_number == 1
    assert projection.narrative[-1].kind == "reference_note_recorded"
    assert projection.narrative[-1].reference_id == PERSON_REFERENCE_ID


def test_correcting_reference_note_removes_it_from_active_projection_only() -> None:
    adventure = reference_library_adventure()
    state = record_reference_note(
        adventure,
        new_play_state(adventure),
        PERSON_REFERENCE_ID,
        "This was attached to the wrong person.",
    )
    state = correct_latest_operation(adventure, state, "Wrong reference")

    projection = project_play_state(adventure, state)

    assert projection.reference_notes == ()
    assert all(record.kind != "reference_note_recorded" for record in projection.narrative)
    assert isinstance(state.events[0], ReferenceNoteRecordedEvent)
    assert isinstance(state.events[1], PlayOperationVoidedEvent)


def test_projection_rejects_reference_notes_for_missing_authored_identity() -> None:
    adventure = reference_library_adventure()
    state = PlayState(
        adventure.id,
        (ReferenceNoteRecordedEvent(1, "missing-reference", "A note", 1),),
    )

    with pytest.raises(PlayTrackingError, match="Unknown reference"):
        project_play_state(adventure, state)
