"""Tests for explicit play commands and correction behavior."""

from __future__ import annotations

import pytest
from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)

from adventure_graph.application.dice import roll_dice
from adventure_graph.application.play_errors import PlayTrackingError
from adventure_graph.application.play_projection import project_play_state
from adventure_graph.application.play_tracking import (
    add_visit_note,
    correct_latest_operation,
    end_session,
    establish_revelation,
    latest_active_operation_number,
    new_play_state,
    record_dice_roll,
    record_encounter_consequence,
    record_reference_note,
    record_visit,
    spot_clue,
    start_session,
    unlock_encounter,
)
from adventure_graph.domain.play_events import (
    ClueSpottedEvent,
    PlayOperationVoidedEvent,
    ReferenceNoteRecordedEvent,
)


def test_spot_clue_defaults_to_latest_visit_to_its_source() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    state = record_visit(adventure, state, "alpha")
    state = spot_clue(adventure, state, "alpha-to-beta")

    clue_event = state.events[-1]
    assert isinstance(clue_event, ClueSpottedEvent)
    assert clue_event.visit_number == 2


def test_clue_must_be_spotted_at_its_authored_source() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")

    with pytest.raises(PlayTrackingError, match="Visit 1000 does not exist"):
        spot_clue(adventure, state, "alpha-to-beta", visit_number=1_000)

    with pytest.raises(PlayTrackingError, match="Visit 1 is to 'alpha'"):
        spot_clue(adventure, state, "beta-to-alpha", visit_number=1)


def test_clue_can_only_be_spotted_once() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta",),
    )

    with pytest.raises(PlayTrackingError, match="already spotted"):
        spot_clue(adventure, state, "alpha-to-beta")


def test_establishment_basis_must_be_spotted_and_support_the_revelation() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")

    with pytest.raises(PlayTrackingError, match="before it is spotted"):
        establish_revelation(adventure, state, "find-beta", ("alpha-to-beta",))

    state = spot_clue(adventure, state, "alpha-to-gamma")
    with pytest.raises(PlayTrackingError, match="supports 'find-gamma'"):
        establish_revelation(adventure, state, "find-beta", ("alpha-to-gamma",))


def test_mutation_commands_reject_redundant_or_blank_events() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")

    with pytest.raises(PlayTrackingError, match="already available"):
        unlock_encounter(adventure, state, "alpha", "Redundant.")
    with pytest.raises(PlayTrackingError, match="requires a reason"):
        unlock_encounter(adventure, state, "beta", "   ")
    with pytest.raises(PlayTrackingError, match="cannot be blank"):
        add_visit_note(state, 1, "   ")
    with pytest.raises(PlayTrackingError, match="cannot be blank"):
        record_encounter_consequence(adventure, state, "alpha", "   ")


def test_correction_voids_one_compound_visit_operation_without_rewriting_history() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta",),
        ("Accidental visit.",),
    )
    original_events = state.events

    corrected = correct_latest_operation(adventure, state, "The visit was recorded by mistake.")
    projection = project_play_state(adventure, corrected)

    assert corrected.events[:-1] == original_events
    assert isinstance(corrected.events[-1], PlayOperationVoidedEvent)
    assert corrected.events[-1].target_operation_number == 1
    assert corrected.voided_operation_numbers == frozenset({1})
    assert corrected.active_events == ()
    assert projection.visits == ()
    assert projection.spotted_clue_ids == ()
    assert projection.corrections[0].reason == "The visit was recorded by mistake."


def test_repeated_corrections_walk_back_active_operations_in_reverse_order() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    state = add_visit_note(state, 1, "First note.")
    state = add_visit_note(state, 1, "Second note.")

    state = correct_latest_operation(adventure, state, "Second note was accidental.")
    assert state.visits[0].notes == ("First note.",)
    assert latest_active_operation_number(state) == 2

    state = correct_latest_operation(adventure, state, "First note was accidental.")
    assert state.visits[0].notes == ()
    assert latest_active_operation_number(state) == 1


def test_correction_rejects_blank_reason_and_empty_journal() -> None:
    adventure = complete_four_encounter_adventure()
    empty = new_play_state(adventure)

    with pytest.raises(PlayTrackingError, match="requires a reason"):
        correct_latest_operation(adventure, empty, "  ")
    with pytest.raises(PlayTrackingError, match="no active operation"):
        correct_latest_operation(adventure, empty, "Nothing to undo.")


def test_session_boundaries_reject_overlap_bad_metadata_and_out_of_session_play() -> None:
    adventure = complete_four_encounter_adventure()
    state = new_play_state(adventure)

    with pytest.raises(PlayTrackingError, match="No explicit session is active"):
        end_session(state)
    with pytest.raises(PlayTrackingError, match="ISO calendar date"):
        start_session(state, played_on="18 July 2026")
    with pytest.raises(PlayTrackingError, match="listed twice"):
        start_session(state, participants=("Mara", "Mara"))

    state = start_session(state)
    with pytest.raises(PlayTrackingError, match="already active"):
        start_session(state)
    state = end_session(state)
    with pytest.raises(PlayTrackingError, match="start a new session"):
        record_visit(adventure, state, "alpha")


def test_recorded_dice_roll_rejects_an_excessive_label() -> None:
    adventure = complete_four_encounter_adventure()
    result = roll_dice("1d6", randbelow=lambda _bound: 0)

    with pytest.raises(PlayTrackingError, match="labels may not exceed 160"):
        record_dice_roll(new_play_state(adventure), result, "x" * 161)


def test_reference_notes_are_trimmed_and_require_a_known_reference() -> None:
    adventure = reference_library_adventure()
    state = new_play_state(adventure)

    state = record_reference_note(
        adventure,
        state,
        PERSON_REFERENCE_ID,
        "  Cora now trusts the party.  ",
    )

    event = state.events[-1]
    assert isinstance(event, ReferenceNoteRecordedEvent)
    assert event.reference_id == PERSON_REFERENCE_ID
    assert event.text == "Cora now trusts the party."
    with pytest.raises(PlayTrackingError, match="cannot be blank"):
        record_reference_note(adventure, state, PERSON_REFERENCE_ID, "   ")
    with pytest.raises(PlayTrackingError, match="Unknown reference"):
        record_reference_note(adventure, state, "missing-reference", "A note")


def test_reference_notes_obey_explicit_session_boundaries() -> None:
    adventure = reference_library_adventure()
    state = start_session(new_play_state(adventure), title="First session")
    state = end_session(state)

    with pytest.raises(PlayTrackingError, match="start a new session"):
        record_reference_note(adventure, state, PERSON_REFERENCE_ID, "Too late")
