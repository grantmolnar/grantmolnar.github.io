"""Tests for structural and semantic play-journal validation."""

from __future__ import annotations

import pytest
from tests.support.adventures import complete_four_encounter_adventure

from adventure_graph.application.play_errors import PlayTrackingError
from adventure_graph.application.play_journal_validation import validate_journal_shape
from adventure_graph.application.play_projection import project_play_state
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    DiceGroupResult,
    DiceRollRecordedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    PlayEvent,
    PlayOperationVoidedEvent,
    ReferenceNoteRecordedEvent,
    RevelationEstablishedEvent,
    RevelationForeclosedEvent,
    RevelationReopenedEvent,
    SessionEndedEvent,
    SessionStartedEvent,
    VisitNoteRecordedEvent,
)
from adventure_graph.domain.play_state import PlayState


def test_projection_rejects_state_for_a_different_adventure() -> None:
    adventure = complete_four_encounter_adventure()

    with pytest.raises(PlayTrackingError, match="belongs to 'other'"):
        project_play_state(adventure, PlayState(adventure_id="other"))


def test_projection_rejects_noncontiguous_event_and_visit_numbers() -> None:
    adventure = complete_four_encounter_adventure()
    bad_event_sequence = PlayState(
        adventure_id=adventure.id,
        events=(
            EncounterVisitedEvent(
                sequence=2, visit_number=1, encounter_id="alpha", operation_number=1
            ),
        ),
    )
    bad_visit_sequence = PlayState(
        adventure_id=adventure.id,
        events=(
            EncounterVisitedEvent(
                sequence=1, visit_number=2, encounter_id="alpha", operation_number=1
            ),
        ),
    )

    with pytest.raises(PlayTrackingError, match="Event sequence must be contiguous"):
        project_play_state(adventure, bad_event_sequence)
    with pytest.raises(PlayTrackingError, match="Visit numbers must be contiguous"):
        project_play_state(adventure, bad_visit_sequence)


def test_projection_rejects_raw_visit_to_locked_encounter() -> None:
    adventure = complete_four_encounter_adventure()
    state = PlayState(
        adventure_id=adventure.id,
        events=(
            EncounterVisitedEvent(
                sequence=1, visit_number=1, encounter_id="beta", operation_number=1
            ),
        ),
    )

    with pytest.raises(PlayTrackingError, match="visits locked encounter 'beta'"):
        project_play_state(adventure, state)


def test_projection_rejects_a_duplicate_spotted_clue_in_raw_history() -> None:
    adventure = complete_four_encounter_adventure()
    state = PlayState(
        adventure_id=adventure.id,
        events=(
            EncounterVisitedEvent(1, 1, "alpha", 1),
            ClueSpottedEvent(2, "alpha-to-beta", 1, 2),
            ClueSpottedEvent(3, "alpha-to-beta", 1, 3),
        ),
    )

    with pytest.raises(PlayTrackingError, match="spotted more than once"):
        project_play_state(adventure, state)


def test_projection_rejects_raw_clue_at_wrong_visit() -> None:
    adventure = complete_four_encounter_adventure()
    state = PlayState(
        adventure_id=adventure.id,
        events=(
            EncounterVisitedEvent(
                sequence=1, visit_number=1, encounter_id="alpha", operation_number=1
            ),
            ClueSpottedEvent(
                sequence=2, clue_id="beta-to-alpha", visit_number=1, operation_number=2
            ),
        ),
    )

    with pytest.raises(PlayTrackingError, match="outside source encounter 'beta'"):
        project_play_state(adventure, state)


def test_projection_rejects_unspotted_establishment_basis() -> None:
    adventure = complete_four_encounter_adventure()
    state = PlayState(
        adventure_id=adventure.id,
        events=(
            RevelationEstablishedEvent(
                sequence=1,
                revelation_id="find-beta",
                operation_number=1,
                supporting_clue_ids=("alpha-to-beta",),
            ),
        ),
    )

    with pytest.raises(PlayTrackingError, match="cites unspotted lead"):
        project_play_state(adventure, state)


def test_projection_rejects_invalid_revelation_based_unlocks() -> None:
    adventure = complete_four_encounter_adventure()
    before_establishment = PlayState(
        adventure_id=adventure.id,
        events=(
            EncounterUnlockedEvent(
                sequence=1,
                encounter_id="beta",
                operation_number=1,
                source_revelation_id="find-beta",
            ),
        ),
    )
    wrong_target = PlayState(
        adventure_id=adventure.id,
        events=(
            RevelationEstablishedEvent(sequence=1, revelation_id="find-beta", operation_number=1),
            EncounterUnlockedEvent(
                sequence=2,
                encounter_id="gamma",
                operation_number=1,
                source_revelation_id="find-beta",
            ),
        ),
    )

    with pytest.raises(PlayTrackingError, match="unestablished revelation"):
        project_play_state(adventure, before_establishment)
    with pytest.raises(PlayTrackingError, match="does not unlock 'gamma'"):
        project_play_state(adventure, wrong_target)


def test_projection_rejects_manual_unlock_without_reason() -> None:
    adventure = complete_four_encounter_adventure()
    state = PlayState(
        adventure_id=adventure.id,
        events=(EncounterUnlockedEvent(sequence=1, encounter_id="beta", operation_number=1),),
    )

    with pytest.raises(PlayTrackingError, match="manual encounter unlock without a reason"):
        project_play_state(adventure, state)


def test_projection_rejects_correction_that_skips_a_later_active_operation() -> None:
    adventure = complete_four_encounter_adventure()
    state = PlayState(
        adventure_id=adventure.id,
        events=(
            EncounterVisitedEvent(1, 1, "alpha", 1),
            VisitNoteRecordedEvent(2, 1, "Keep this.", 2),
            PlayOperationVoidedEvent(3, 3, 1, "Invalid target."),
        ),
    )

    with pytest.raises(PlayTrackingError, match="latest active operation 2"):
        project_play_state(adventure, state)


def test_projection_rejects_die_results_outside_their_bounds() -> None:
    adventure = complete_four_encounter_adventure()
    state = PlayState(
        adventure_id=adventure.id,
        events=(
            DiceRollRecordedEvent(
                sequence=1,
                expression="1d6",
                terms=(DiceGroupResult(1, 6, (7,)),),
                total=7,
                operation_number=1,
            ),
        ),
    )

    with pytest.raises(PlayTrackingError, match="outside its die bounds"):
        project_play_state(adventure, state)


def test_projection_rejects_an_excessive_recorded_dice_label() -> None:
    adventure = complete_four_encounter_adventure()
    state = PlayState(
        adventure_id=adventure.id,
        events=(
            DiceRollRecordedEvent(
                sequence=1,
                expression="1d6",
                terms=(DiceGroupResult(1, 6, (4,)),),
                total=4,
                operation_number=1,
                label="x" * 161,
            ),
        ),
    )

    with pytest.raises(PlayTrackingError, match="label longer than 160"):
        project_play_state(adventure, state)



def _journal(*events: PlayEvent) -> PlayState:
    return PlayState(adventure_id="complete-four", events=events)


@pytest.mark.parametrize(
    ("state", "message"),
    (
        pytest.param(
            _journal(EncounterVisitedEvent(1, 1, "alpha", 0)),
            "invalid operation number 0",
            id="nonpositive-operation",
        ),
        pytest.param(
            _journal(EncounterVisitedEvent(1, 1, "alpha", 2)),
            "Operation numbers must be contiguous",
            id="noncontiguous-operation",
        ),
        pytest.param(
            _journal(PlayOperationVoidedEvent(1, 1, 1, "Nothing to void.")),
            "has no active operation to void",
            id="correction-without-active-operation",
        ),
        pytest.param(
            _journal(
                EncounterVisitedEvent(1, 1, "alpha", 1),
                PlayOperationVoidedEvent(2, 2, 1, "   "),
            ),
            "requires a reason",
            id="blank-correction-reason",
        ),
        pytest.param(
            _journal(
                EncounterVisitedEvent(1, 1, "alpha", 1),
                PlayOperationVoidedEvent(2, 2, 1, "Undo."),
                VisitNoteRecordedEvent(3, 1, "Wrongly grouped.", 2),
            ),
            "Correction operation 2 must contain only",
            id="content-after-correction-in-operation",
        ),
        pytest.param(
            _journal(
                EncounterVisitedEvent(1, 1, "alpha", 1),
                VisitNoteRecordedEvent(2, 1, "Wrongly grouped.", 2),
                PlayOperationVoidedEvent(3, 2, 1, "Undo."),
            ),
            "Correction operation 2 must contain only",
            id="correction-after-content-in-operation",
        ),
        pytest.param(
            _journal(
                EncounterVisitedEvent(1, 1, "alpha", 1),
                RevelationEstablishedEvent(2, "find-beta", 1),
            ),
            "Visit operation 1 contains an unrelated event",
            id="visit-operation-unrelated-event",
        ),
        pytest.param(
            _journal(
                EncounterVisitedEvent(1, 1, "alpha", 1),
                ClueSpottedEvent(2, "alpha-to-beta", 2, 1),
            ),
            "Visit operation 1 mixes visit numbers",
            id="visit-operation-mixed-visits",
        ),
        pytest.param(
            _journal(
                SessionStartedEvent(1, 1, 1),
                SessionEndedEvent(2, 1, 1),
            ),
            "multiple unrelated play events",
            id="unrelated-multi-event-operation",
        ),
        pytest.param(
            _journal(
                RevelationEstablishedEvent(1, "find-beta", 1),
                EncounterUnlockedEvent(2, "beta", 1, source_revelation_id="find-gamma"),
            ),
            "contains an unrelated encounter unlock",
            id="transition-unrelated-unlock",
        ),
        pytest.param(
            _journal(
                ClueSpottedEvent(1, "alpha-to-beta", 1, 1),
                VisitNoteRecordedEvent(2, 1, "Out of order.", 1),
            ),
            "events out of phase order",
            id="transition-phase-order",
        ),
        pytest.param(
            _journal(
                RevelationEstablishedEvent(1, "find-beta", 1),
                EncounterVisitedEvent(2, 1, "beta", 1),
                EncounterConsequenceRecordedEvent(3, "alpha", "Too late.", 1),
            ),
            "must end with its destination visit",
            id="transition-destination-not-last",
        ),
        pytest.param(
            _journal(
                VisitNoteRecordedEvent(1, 1, "Source one.", 1),
                ClueSpottedEvent(2, "alpha-to-beta", 2, 1),
            ),
            "mixes source visits",
            id="transition-mixed-source-visits",
        ),
    ),
)
def test_raw_journal_shape_rejects_malformed_operation_groups(
    state: PlayState,
    message: str,
) -> None:
    with pytest.raises(PlayTrackingError, match=message):
        validate_journal_shape(state)


@pytest.mark.parametrize(
    ("state", "message"),
    (
        pytest.param(
            _journal(SessionStartedEvent(1, 1, 1), SessionStartedEvent(2, 2, 2)),
            "starts while session 1 is active",
            id="nested-session",
        ),
        pytest.param(
            _journal(SessionStartedEvent(1, 2, 1)),
            "Session numbers must be contiguous",
            id="noncontiguous-session",
        ),
        pytest.param(
            _journal(SessionStartedEvent(1, 1, 1, played_on="2026-02-30")),
            "must be an ISO calendar date",
            id="invalid-session-date",
        ),
        pytest.param(
            _journal(SessionStartedEvent(1, 1, 1, participants=("Rhea", " "))),
            "contains a blank participant",
            id="blank-participant",
        ),
        pytest.param(
            _journal(SessionStartedEvent(1, 1, 1, participants=("Rhea", "Rhea"))),
            "repeats a participant",
            id="repeated-participant",
        ),
        pytest.param(
            _journal(SessionEndedEvent(1, 1, 1)),
            "has no active session",
            id="end-without-session",
        ),
        pytest.param(
            _journal(SessionStartedEvent(1, 1, 1), SessionEndedEvent(2, 2, 2)),
            "not active session 1",
            id="end-wrong-session",
        ),
        pytest.param(
            _journal(
                SessionStartedEvent(1, 1, 1),
                SessionEndedEvent(2, 1, 2),
                EncounterConsequenceRecordedEvent(3, "alpha", "Afterward.", 3),
            ),
            "occurs outside an active explicit session",
            id="content-between-explicit-sessions",
        ),
        pytest.param(
            _journal(ClueSpottedEvent(1, "alpha-to-beta", 1, 1)),
            "refers to nonexistent visit 1",
            id="spotted-lead-without-visit",
        ),
        pytest.param(
            _journal(
                EncounterVisitedEvent(1, 1, "alpha", 1),
                ClueSpottedEvent(2, "alpha-to-beta", 1, 2),
                ClueMissedEvent(3, "alpha-to-beta", 1, 3),
            ),
            "cannot be marked missed after it is spotted",
            id="missed-after-spotted",
        ),
        pytest.param(
            _journal(
                EncounterVisitedEvent(1, 1, "alpha", 1),
                ClueMissedEvent(2, "alpha-to-beta", 1, 2),
                ClueMissedEvent(3, "alpha-to-beta", 1, 3),
            ),
            "is missed more than once",
            id="duplicate-miss-on-visit",
        ),
        pytest.param(
            _journal(
                RevelationEstablishedEvent(1, "find-beta", 1),
                RevelationEstablishedEvent(2, "find-beta", 2),
            ),
            "is established more than once",
            id="duplicate-establishment",
        ),
        pytest.param(
            _journal(
                RevelationForeclosedEvent(1, "find-beta", "Lost.", 1),
                RevelationEstablishedEvent(2, "find-beta", 2),
            ),
            "cannot be established",
            id="establish-foreclosed-revelation",
        ),
        pytest.param(
            _journal(RevelationForeclosedEvent(1, "find-beta", "   ", 1)),
            "blank foreclosure reason",
            id="blank-foreclosure-reason",
        ),
        pytest.param(
            _journal(
                RevelationEstablishedEvent(1, "find-beta", 1),
                RevelationForeclosedEvent(2, "find-beta", "Lost.", 2),
            ),
            "cannot be foreclosed",
            id="foreclose-established-revelation",
        ),
        pytest.param(
            _journal(
                RevelationForeclosedEvent(1, "find-beta", "Lost.", 1),
                RevelationForeclosedEvent(2, "find-beta", "Still lost.", 2),
            ),
            "is already foreclosed",
            id="duplicate-foreclosure",
        ),
        pytest.param(
            _journal(
                RevelationForeclosedEvent(1, "find-beta", "Lost.", 1),
                RevelationReopenedEvent(2, "find-beta", "   ", 2),
            ),
            "blank reopening reason",
            id="blank-reopening-reason",
        ),
        pytest.param(
            _journal(RevelationReopenedEvent(1, "find-beta", "Found again.", 1)),
            "is not foreclosed",
            id="reopen-active-revelation",
        ),
        pytest.param(
            _journal(
                EncounterUnlockedEvent(1, "beta", 1, reason="GM ruling."),
                EncounterUnlockedEvent(2, "beta", 2, reason="Again."),
            ),
            "has multiple unlock events",
            id="duplicate-unlock",
        ),
        pytest.param(
            _journal(VisitNoteRecordedEvent(1, 1, "Missing visit.", 1)),
            "refers to nonexistent visit 1",
            id="note-without-visit",
        ),
        pytest.param(
            _journal(
                EncounterVisitedEvent(1, 1, "alpha", 1),
                VisitNoteRecordedEvent(2, 1, "   ", 2),
            ),
            "blank encounter note",
            id="blank-visit-note",
        ),
        pytest.param(
            _journal(ReferenceNoteRecordedEvent(1, " ", "Useful.", 1)),
            "blank reference identifier",
            id="blank-reference-id",
        ),
        pytest.param(
            _journal(ReferenceNoteRecordedEvent(1, "person-one", " ", 1)),
            "blank reference note",
            id="blank-reference-note",
        ),
        pytest.param(
            _journal(EncounterConsequenceRecordedEvent(1, "alpha", " ", 1)),
            "blank consequence",
            id="blank-consequence",
        ),
    ),
)
def test_active_journal_shape_rejects_invalid_state_transitions(
    state: PlayState,
    message: str,
) -> None:
    with pytest.raises(PlayTrackingError, match=message):
        validate_journal_shape(state)
