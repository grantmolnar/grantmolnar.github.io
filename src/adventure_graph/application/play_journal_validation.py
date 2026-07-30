"""Structural validation for append-only play journals."""

from __future__ import annotations

from datetime import date
from typing import assert_never

from adventure_graph.application.dice import (
    MAX_LABEL_CHARACTERS,
    DiceExpressionError,
    DiceRollResult,
    validate_dice_roll,
)
from adventure_graph.application.play_errors import PlayTrackingError
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    DiceRollRecordedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    PlayContentEvent,
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


def validate_journal_shape(state: PlayState) -> None:
    """Reject journals whose raw or active event streams violate invariants."""
    _validate_raw_journal_shape(state)
    _validate_active_journal_shape(state.active_events)


def _validate_raw_journal_shape(state: PlayState) -> None:
    expected_operation_number = 1
    current_operation_number = 0
    operation_events: dict[int, list[PlayEvent]] = {}
    content_operation_numbers: list[int] = []
    voided_operation_numbers: set[int] = set()

    for expected_sequence, event in enumerate(state.events, start=1):
        if event.sequence != expected_sequence:
            raise PlayTrackingError(
                f"Event sequence must be contiguous; expected {expected_sequence}, "
                f"found {event.sequence}."
            )
        if event.operation_number <= 0:
            raise PlayTrackingError(
                f"Event {event.sequence} has invalid operation number {event.operation_number}."
            )
        if event.operation_number != current_operation_number:
            if event.operation_number != expected_operation_number:
                raise PlayTrackingError(
                    "Operation numbers must be contiguous; "
                    f"expected {expected_operation_number}, found {event.operation_number}."
                )
            current_operation_number = event.operation_number
            expected_operation_number += 1
            operation_events[current_operation_number] = []
        group = operation_events[current_operation_number]
        if isinstance(event, PlayOperationVoidedEvent):
            if group:
                raise PlayTrackingError(
                    f"Correction operation {event.operation_number} must contain only its "
                    "correction event."
                )
            _validate_correction_event(event, content_operation_numbers, voided_operation_numbers)
            voided_operation_numbers.add(event.target_operation_number)
        else:
            if group and isinstance(group[0], PlayOperationVoidedEvent):
                raise PlayTrackingError(
                    f"Correction operation {event.operation_number} must contain only its "
                    "correction event."
                )
            if not group:
                content_operation_numbers.append(event.operation_number)
        group.append(event)

    for operation_number, events in operation_events.items():
        if not isinstance(events[0], PlayOperationVoidedEvent):
            _validate_content_operation_shape(operation_number, events)


def _validate_correction_event(
    event: PlayOperationVoidedEvent,
    content_operation_numbers: list[int],
    voided_operation_numbers: set[int],
) -> None:
    if not event.reason.strip():
        raise PlayTrackingError(f"Correction event {event.sequence} requires a reason.")
    active_operation_numbers = [
        number for number in content_operation_numbers if number not in voided_operation_numbers
    ]
    if not active_operation_numbers:
        raise PlayTrackingError(
            f"Correction event {event.sequence} has no active operation to void."
        )
    latest_operation_number = active_operation_numbers[-1]
    if event.target_operation_number != latest_operation_number:
        raise PlayTrackingError(
            f"Correction event {event.sequence} must target latest active operation "
            f"{latest_operation_number}, not {event.target_operation_number}."
        )


def _validate_content_operation_shape(
    operation_number: int,
    events: list[PlayEvent],
) -> None:
    first = events[0]
    if len(events) == 1:
        return
    if isinstance(first, EncounterVisitedEvent):
        for event in events[1:]:
            if not isinstance(event, (ClueSpottedEvent, ClueMissedEvent, VisitNoteRecordedEvent)):
                raise PlayTrackingError(
                    f"Visit operation {operation_number} contains an unrelated event."
                )
            if event.visit_number != first.visit_number:
                raise PlayTrackingError(f"Visit operation {operation_number} mixes visit numbers.")
        return
    if _is_transition_operation(events):
        _validate_transition_operation_shape(operation_number, events)
        return
    raise PlayTrackingError(
        f"Operation {operation_number} contains multiple unrelated play events."
    )


def _is_transition_operation(events: list[PlayEvent]) -> bool:
    allowed = (
        VisitNoteRecordedEvent,
        ClueSpottedEvent,
        ClueMissedEvent,
        RevelationEstablishedEvent,
        RevelationForeclosedEvent,
        RevelationReopenedEvent,
        EncounterUnlockedEvent,
        EncounterConsequenceRecordedEvent,
        EncounterVisitedEvent,
    )
    return all(isinstance(event, allowed) for event in events)


def _validate_transition_operation_shape(operation_number: int, events: list[PlayEvent]) -> None:
    phase = 0
    source_visit_number: int | None = None
    previous_revelation_id = ""
    for event in events:
        if isinstance(event, VisitNoteRecordedEvent):
            event_phase = 1
            source_visit_number = _transition_source_visit(
                operation_number, source_visit_number, event.visit_number
            )
        elif isinstance(event, (ClueSpottedEvent, ClueMissedEvent)):
            event_phase = 2
            source_visit_number = _transition_source_visit(
                operation_number, source_visit_number, event.visit_number
            )
        elif isinstance(event, RevelationEstablishedEvent):
            event_phase = 3
            previous_revelation_id = event.revelation_id
        elif isinstance(event, EncounterUnlockedEvent):
            event_phase = 3
            if not previous_revelation_id or event.source_revelation_id != previous_revelation_id:
                raise PlayTrackingError(
                    f"Transition operation {operation_number} contains an unrelated "
                    "encounter unlock."
                )
            previous_revelation_id = ""
        elif isinstance(event, (RevelationForeclosedEvent, RevelationReopenedEvent)):
            event_phase = 4
            previous_revelation_id = ""
        elif isinstance(event, EncounterConsequenceRecordedEvent):
            event_phase = 5
            previous_revelation_id = ""
        elif isinstance(event, EncounterVisitedEvent):
            event_phase = 6
            previous_revelation_id = ""
        else:
            raise PlayTrackingError(
                f"Transition operation {operation_number} contains an unrelated event."
            )
        if event_phase < phase:
            raise PlayTrackingError(
                f"Transition operation {operation_number} has events out of phase order."
            )
        if isinstance(event, EncounterVisitedEvent) and event is not events[-1]:
            raise PlayTrackingError(
                f"Transition operation {operation_number} must end with its destination visit."
            )
        phase = event_phase


def _transition_source_visit(operation_number: int, current: int | None, candidate: int) -> int:
    if current is not None and current != candidate:
        raise PlayTrackingError(f"Transition operation {operation_number} mixes source visits.")
    return candidate


# Journal validation is one explicit state machine so invariants remain visible.
def _validate_active_journal_shape(
    events: tuple[PlayContentEvent, ...],
) -> None:
    visit_numbers: set[int] = set()
    spotted_clues: set[str] = set()
    missed_clues: set[tuple[str, int]] = set()
    established_revelations: set[str] = set()
    foreclosed_revelations: set[str] = set()
    unlocked_encounters: set[str] = set()
    expected_visit_number = 1
    expected_session_number = 1
    active_session_number: int | None = None
    explicit_session_seen = False
    for event in events:
        if isinstance(event, SessionStartedEvent):
            if active_session_number is not None:
                raise PlayTrackingError(
                    f"Session {event.session_number} starts while session "
                    f"{active_session_number} is active."
                )
            if event.session_number != expected_session_number:
                raise PlayTrackingError(
                    f"Session numbers must be contiguous; expected {expected_session_number}, "
                    f"found {event.session_number}."
                )
            _validate_session_start(event)
            active_session_number = event.session_number
            expected_session_number += 1
            explicit_session_seen = True
            continue
        if isinstance(event, SessionEndedEvent):
            if active_session_number is None:
                raise PlayTrackingError(
                    f"Session end event {event.sequence} has no active session."
                )
            if event.session_number != active_session_number:
                raise PlayTrackingError(
                    f"Session end event {event.sequence} names session {event.session_number}, "
                    f"not active session {active_session_number}."
                )
            active_session_number = None
            continue
        if explicit_session_seen and active_session_number is None:
            raise PlayTrackingError(
                f"Event {event.sequence} occurs outside an active explicit session."
            )
        if isinstance(event, EncounterVisitedEvent):
            expected_visit_number = _validate_visit_shape(
                event, visit_numbers, expected_visit_number
            )
        elif isinstance(event, ClueSpottedEvent):
            _validate_clue_shape(event, visit_numbers, spotted_clues)
        elif isinstance(event, ClueMissedEvent):
            _validate_missed_clue_shape(event, visit_numbers, spotted_clues, missed_clues)
        elif isinstance(event, RevelationEstablishedEvent):
            _validate_revelation_shape(event, established_revelations, foreclosed_revelations)
        elif isinstance(event, RevelationForeclosedEvent):
            _validate_foreclosure_shape(event, established_revelations, foreclosed_revelations)
        elif isinstance(event, RevelationReopenedEvent):
            _validate_reopening_shape(event, foreclosed_revelations)
        elif isinstance(event, DiceRollRecordedEvent):
            validate_recorded_roll(event)
        elif isinstance(event, EncounterUnlockedEvent):
            _validate_unlock_shape(event, unlocked_encounters)
        elif isinstance(event, VisitNoteRecordedEvent):
            _validate_visit_note_shape(event, visit_numbers)
        elif isinstance(event, ReferenceNoteRecordedEvent):
            _validate_reference_note_shape(event)
        elif isinstance(event, EncounterConsequenceRecordedEvent):
            _validate_consequence_shape(event)
        else:
            assert_never(event)


def _validate_session_start(event: SessionStartedEvent) -> None:
    validate_played_on(event.played_on)
    if any(not participant.strip() for participant in event.participants):
        raise PlayTrackingError(
            f"Session start event {event.sequence} contains a blank participant."
        )
    if len(set(event.participants)) != len(event.participants):
        raise PlayTrackingError(f"Session start event {event.sequence} repeats a participant.")


def _validate_visit_shape(
    event: EncounterVisitedEvent,
    visit_numbers: set[int],
    expected_visit_number: int,
) -> int:
    if event.visit_number != expected_visit_number:
        raise PlayTrackingError(
            f"Visit numbers must be contiguous; expected {expected_visit_number}, "
            f"found {event.visit_number}."
        )
    visit_numbers.add(event.visit_number)
    return expected_visit_number + 1


def _validate_clue_shape(
    event: ClueSpottedEvent,
    visit_numbers: set[int],
    spotted_clues: set[str],
) -> None:
    if event.visit_number not in visit_numbers:
        raise PlayTrackingError(
            f"Event {event.sequence} refers to nonexistent visit {event.visit_number}."
        )
    if event.clue_id in spotted_clues:
        raise PlayTrackingError(f"Lead {event.clue_id!r} is spotted more than once.")
    spotted_clues.add(event.clue_id)


def _validate_missed_clue_shape(
    event: ClueMissedEvent,
    visit_numbers: set[int],
    spotted_clues: set[str],
    missed_clues: set[tuple[str, int]],
) -> None:
    if event.visit_number not in visit_numbers:
        raise PlayTrackingError(
            f"Event {event.sequence} refers to nonexistent visit {event.visit_number}."
        )
    if event.clue_id in spotted_clues:
        raise PlayTrackingError(
            f"Lead {event.clue_id!r} cannot be marked missed after it is spotted."
        )
    key = (event.clue_id, event.visit_number)
    if key in missed_clues:
        raise PlayTrackingError(
            f"Lead {event.clue_id!r} is missed more than once on visit {event.visit_number}."
        )
    missed_clues.add(key)


def _validate_revelation_shape(
    event: RevelationEstablishedEvent,
    established_revelations: set[str],
    foreclosed_revelations: set[str],
) -> None:
    if event.revelation_id in established_revelations:
        raise PlayTrackingError(
            f"Revelation {event.revelation_id!r} is established more than once."
        )
    if event.revelation_id in foreclosed_revelations:
        raise PlayTrackingError(
            f"Foreclosed revelation {event.revelation_id!r} cannot be established."
        )
    established_revelations.add(event.revelation_id)


def _validate_foreclosure_shape(
    event: RevelationForeclosedEvent,
    established_revelations: set[str],
    foreclosed_revelations: set[str],
) -> None:
    if not event.reason.strip():
        raise PlayTrackingError(f"Event {event.sequence} contains a blank foreclosure reason.")
    if event.revelation_id in established_revelations:
        raise PlayTrackingError(
            f"Established revelation {event.revelation_id!r} cannot be foreclosed."
        )
    if event.revelation_id in foreclosed_revelations:
        raise PlayTrackingError(f"Revelation {event.revelation_id!r} is already foreclosed.")
    foreclosed_revelations.add(event.revelation_id)


def _validate_reopening_shape(
    event: RevelationReopenedEvent,
    foreclosed_revelations: set[str],
) -> None:
    if not event.reason.strip():
        raise PlayTrackingError(f"Event {event.sequence} contains a blank reopening reason.")
    if event.revelation_id not in foreclosed_revelations:
        raise PlayTrackingError(f"Revelation {event.revelation_id!r} is not foreclosed.")
    foreclosed_revelations.remove(event.revelation_id)


def _validate_unlock_shape(event: EncounterUnlockedEvent, unlocked_encounters: set[str]) -> None:
    if event.encounter_id in unlocked_encounters:
        raise PlayTrackingError(f"Encounter {event.encounter_id!r} has multiple unlock events.")
    unlocked_encounters.add(event.encounter_id)


def _validate_visit_note_shape(
    event: VisitNoteRecordedEvent,
    visit_numbers: set[int],
) -> None:
    if event.visit_number not in visit_numbers:
        raise PlayTrackingError(
            f"Event {event.sequence} refers to nonexistent visit {event.visit_number}."
        )
    if not event.text.strip():
        raise PlayTrackingError(f"Event {event.sequence} contains a blank encounter note.")


def _validate_reference_note_shape(event: ReferenceNoteRecordedEvent) -> None:
    if not event.reference_id.strip():
        raise PlayTrackingError(f"Event {event.sequence} contains a blank reference identifier.")
    if not event.text.strip():
        raise PlayTrackingError(f"Event {event.sequence} contains a blank reference note.")


def _validate_consequence_shape(event: EncounterConsequenceRecordedEvent) -> None:
    if not event.text.strip():
        raise PlayTrackingError(f"Event {event.sequence} contains a blank consequence.")


def validate_recorded_roll(event: DiceRollRecordedEvent) -> None:
    """Reject a persisted dice event whose expression, terms, or label is invalid."""
    try:
        validate_dice_roll(DiceRollResult(event.expression, event.terms, event.total))
    except DiceExpressionError as error:
        raise PlayTrackingError(f"Event {event.sequence}: {error}") from error
    if len(event.label) > MAX_LABEL_CHARACTERS:
        raise PlayTrackingError(
            f"Event {event.sequence} has a dice-roll label longer than "
            f"{MAX_LABEL_CHARACTERS} characters."
        )


def validate_played_on(played_on: str | None) -> None:
    """Reject a nonempty session date that is not an ISO calendar date."""
    if played_on is None:
        return
    try:
        date.fromisoformat(played_on)
    except ValueError as error:
        raise PlayTrackingError("Session played_on must be an ISO calendar date.") from error


def session_state(state: PlayState) -> tuple[int | None, tuple[int, ...]]:
    """Return the active session and all started session numbers."""
    active_session: int | None = None
    session_numbers: list[int] = []
    for event in state.active_events:
        if isinstance(event, SessionStartedEvent):
            active_session = event.session_number
            session_numbers.append(event.session_number)
        elif isinstance(event, SessionEndedEvent):
            active_session = None
    return active_session, tuple(session_numbers)
