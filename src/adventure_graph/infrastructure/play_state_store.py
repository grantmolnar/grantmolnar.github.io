"""JSON persistence for canonical actual-play journals."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import assert_never, cast

from adventure_graph.domain.play_events import (
    PLAY_EVENT_KINDS,
    ClueMissedEvent,
    ClueSpottedEvent,
    DiceGroupResult,
    DiceModifierResult,
    DiceRollRecordedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    PlayEvent,
    PlayEventKind,
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
from adventure_graph.infrastructure.atomic_files import write_json_object
from adventure_graph.infrastructure.json_values import (
    JsonObject,
    UnsupportedFieldError,
    integer_at_least,
    nonempty_string_value,
    nullable_iso_date,
    nullable_nonempty_string,
    object_list,
    positive_integer,
    read_object,
    reject_unknown_fields,
    string_value,
    unique_nonempty_string_list,
)

PLAY_STATE_SCHEMA_VERSION = 6
MAX_PLAY_STATE_EVENTS = 10_000

PLAY_STATE_ROOT_FIELDS = ("schema_version", "adventure_id", "events")


def play_event_object_fields(event_type: PlayEventKind) -> tuple[str, ...]:
    """Return the closed persisted key set for one event kind."""
    match event_type:
        case "session_started":
            return (
                "sequence",
                "operation_number",
                "type",
                "session_number",
                "title",
                "played_on",
                "participants",
                "attendance_note",
                "opening_note",
            )
        case "session_ended":
            return "sequence", "operation_number", "type", "session_number", "closing_note"
        case "encounter_visited":
            return (
                "sequence",
                "operation_number",
                "type",
                "visit_number",
                "encounter_id",
                "party_label",
            )
        case "clue_spotted" | "clue_missed":
            return "sequence", "operation_number", "type", "clue_id", "visit_number"
        case "revelation_established":
            return (
                "sequence",
                "operation_number",
                "type",
                "revelation_id",
                "supporting_clue_ids",
                "note",
            )
        case "revelation_foreclosed" | "revelation_reopened":
            return "sequence", "operation_number", "type", "revelation_id", "reason"
        case "dice_roll_recorded":
            return (
                "sequence",
                "operation_number",
                "type",
                "expression",
                "label",
                "terms",
                "total",
            )
        case "encounter_unlocked":
            return (
                "sequence",
                "operation_number",
                "type",
                "encounter_id",
                "source_revelation_id",
                "reason",
            )
        case "visit_note_recorded":
            return "sequence", "operation_number", "type", "visit_number", "text"
        case "reference_note_recorded":
            return "sequence", "operation_number", "type", "reference_id", "text"
        case "encounter_consequence_recorded":
            return "sequence", "operation_number", "type", "encounter_id", "text"
        case "operation_voided":
            return (
                "sequence",
                "operation_number",
                "type",
                "target_operation_number",
                "reason",
            )
        case _:
            assert_never(event_type)


def dice_term_object_fields(kind: str) -> tuple[str, ...]:
    """Return the closed persisted key set for one recorded-dice term kind."""
    if kind == "dice":
        return "kind", "sign", "faces", "results"
    if kind == "modifier":
        return "kind", "value"
    raise ValueError(f"Unknown dice result term kind {kind!r}.")


def load_play_state(path: Path) -> PlayState:
    """Load one canonical play-state journal."""
    return play_state_from_data(read_object(path), source=path)


def play_state_from_data(
    data: JsonObject,
    *,
    source: str | Path = "play-state document",
) -> PlayState:
    """Decode one canonical play-state JSON object."""
    if data.get("schema_version") != PLAY_STATE_SCHEMA_VERSION:
        raise ValueError(
            f"Only play-state schema_version {PLAY_STATE_SCHEMA_VERSION} is supported in {source}."
        )
    try:
        return _play_state_from_current_schema(data, source)
    except UnsupportedFieldError:
        raise
    except ValueError as error:
        raise ValueError(f"Malformed play-state document in {source}: {error}") from error


def _play_state_from_current_schema(data: JsonObject, source: str | Path) -> PlayState:
    reject_unknown_fields(data, PLAY_STATE_ROOT_FIELDS, f"{source} root")
    events = object_list(data, "events")
    if len(events) > MAX_PLAY_STATE_EVENTS:
        raise ValueError(f"events exceeds the supported limit of {MAX_PLAY_STATE_EVENTS} entries.")
    return PlayState(
        adventure_id=nonempty_string_value(data, "adventure_id"),
        events=tuple(
            _play_event_v6(item, source, index) for index, item in enumerate(events, start=1)
        ),
    )


def save_play_state(path: Path, state: PlayState) -> None:
    """Persist the append-only play operation journal in canonical JSON."""
    write_json_object(path, play_state_data(state))


def play_state_data(state: PlayState) -> JsonObject:
    """Return the canonical JSON object for a play journal."""
    if not state.adventure_id:
        raise ValueError("adventure_id must be a nonempty string.")
    if len(state.events) > MAX_PLAY_STATE_EVENTS:
        raise ValueError(f"Play journals support at most {MAX_PLAY_STATE_EVENTS} persisted events.")
    encoded_events = [_play_event_data(event) for event in state.events]
    for index, event_data in enumerate(encoded_events, start=1):
        _play_event_v6(event_data, "play-state serialization", index)
    return {
        "schema_version": PLAY_STATE_SCHEMA_VERSION,
        "adventure_id": state.adventure_id,
        "events": encoded_events,
    }


# Canonical schema decoding uses one decoder per event shape. The typed key vocabulary and
# round-trip contract tests keep the dispatch table aligned with the domain event algebra.
def _decode_operation_voided(
    data: JsonObject, sequence: int, operation_number: int
) -> PlayOperationVoidedEvent:
    return PlayOperationVoidedEvent(
        sequence=sequence,
        operation_number=operation_number,
        target_operation_number=positive_integer(data, "target_operation_number"),
        reason=nonempty_string_value(data, "reason"),
    )


def _decode_session_started(
    data: JsonObject, sequence: int, operation_number: int
) -> SessionStartedEvent:
    return SessionStartedEvent(
        sequence=sequence,
        session_number=positive_integer(data, "session_number"),
        operation_number=operation_number,
        title=string_value(data, "title", ""),
        played_on=nullable_iso_date(data, "played_on"),
        participants=tuple(unique_nonempty_string_list(data, "participants", [])),
        attendance_note=string_value(data, "attendance_note", ""),
        opening_note=string_value(data, "opening_note", ""),
    )


def _decode_session_ended(
    data: JsonObject, sequence: int, operation_number: int
) -> SessionEndedEvent:
    return SessionEndedEvent(
        sequence=sequence,
        session_number=positive_integer(data, "session_number"),
        operation_number=operation_number,
        closing_note=string_value(data, "closing_note", ""),
    )


def _decode_encounter_visited(
    data: JsonObject, sequence: int, operation_number: int
) -> EncounterVisitedEvent:
    return EncounterVisitedEvent(
        sequence=sequence,
        visit_number=positive_integer(data, "visit_number"),
        encounter_id=nonempty_string_value(data, "encounter_id"),
        operation_number=operation_number,
        party_label=string_value(data, "party_label", ""),
    )


def _decode_clue_spotted(
    data: JsonObject, sequence: int, operation_number: int
) -> ClueSpottedEvent:
    return ClueSpottedEvent(
        sequence=sequence,
        clue_id=nonempty_string_value(data, "clue_id"),
        visit_number=positive_integer(data, "visit_number"),
        operation_number=operation_number,
    )


def _decode_clue_missed(data: JsonObject, sequence: int, operation_number: int) -> ClueMissedEvent:
    return ClueMissedEvent(
        sequence=sequence,
        clue_id=nonempty_string_value(data, "clue_id"),
        visit_number=positive_integer(data, "visit_number"),
        operation_number=operation_number,
    )


def _decode_revelation_established(
    data: JsonObject, sequence: int, operation_number: int
) -> RevelationEstablishedEvent:
    return RevelationEstablishedEvent(
        sequence=sequence,
        revelation_id=nonempty_string_value(data, "revelation_id"),
        operation_number=operation_number,
        supporting_clue_ids=tuple(unique_nonempty_string_list(data, "supporting_clue_ids", [])),
        note=string_value(data, "note", ""),
    )


def _decode_revelation_foreclosed(
    data: JsonObject, sequence: int, operation_number: int
) -> RevelationForeclosedEvent:
    return RevelationForeclosedEvent(
        sequence=sequence,
        revelation_id=nonempty_string_value(data, "revelation_id"),
        reason=nonempty_string_value(data, "reason"),
        operation_number=operation_number,
    )


def _decode_revelation_reopened(
    data: JsonObject, sequence: int, operation_number: int
) -> RevelationReopenedEvent:
    return RevelationReopenedEvent(
        sequence=sequence,
        revelation_id=nonempty_string_value(data, "revelation_id"),
        reason=nonempty_string_value(data, "reason"),
        operation_number=operation_number,
    )


def _decode_dice_roll_recorded(
    data: JsonObject, sequence: int, operation_number: int, context: str
) -> DiceRollRecordedEvent:
    term_data = object_list(data, "terms")
    if not term_data:
        raise ValueError("terms must contain at least one dice result term.")
    terms = tuple(
        _dice_term(item, f"{context}.terms[{index}]")
        for index, item in enumerate(term_data, start=1)
    )
    total = _signed_integer(data, "total")
    calculated_total = sum(
        term.sign * sum(term.results) if isinstance(term, DiceGroupResult) else term.value
        for term in terms
    )
    if total != calculated_total:
        raise ValueError(f"total must equal the recorded dice terms ({calculated_total}).")
    return DiceRollRecordedEvent(
        sequence=sequence,
        expression=nonempty_string_value(data, "expression"),
        label=string_value(data, "label", ""),
        terms=terms,
        total=total,
        operation_number=operation_number,
    )


def _decode_encounter_unlocked(
    data: JsonObject, sequence: int, operation_number: int
) -> EncounterUnlockedEvent:
    return EncounterUnlockedEvent(
        sequence=sequence,
        encounter_id=nonempty_string_value(data, "encounter_id"),
        operation_number=operation_number,
        source_revelation_id=nullable_nonempty_string(data, "source_revelation_id"),
        reason=string_value(data, "reason", ""),
    )


def _decode_visit_note_recorded(
    data: JsonObject, sequence: int, operation_number: int
) -> VisitNoteRecordedEvent:
    return VisitNoteRecordedEvent(
        sequence=sequence,
        visit_number=positive_integer(data, "visit_number"),
        text=nonempty_string_value(data, "text"),
        operation_number=operation_number,
    )


def _decode_reference_note_recorded(
    data: JsonObject, sequence: int, operation_number: int
) -> ReferenceNoteRecordedEvent:
    return ReferenceNoteRecordedEvent(
        sequence=sequence,
        reference_id=nonempty_string_value(data, "reference_id"),
        text=nonempty_string_value(data, "text"),
        operation_number=operation_number,
    )


def _decode_encounter_consequence_recorded(
    data: JsonObject, sequence: int, operation_number: int
) -> EncounterConsequenceRecordedEvent:
    return EncounterConsequenceRecordedEvent(
        sequence=sequence,
        encounter_id=nonempty_string_value(data, "encounter_id"),
        text=nonempty_string_value(data, "text"),
        operation_number=operation_number,
    )


def _play_event_v6_decoder(
    event_type: PlayEventKind,
    context: str,
) -> Callable[[JsonObject, int, int], PlayEvent]:
    match event_type:
        case "session_started":
            decoder = _decode_session_started
        case "session_ended":
            decoder = _decode_session_ended
        case "encounter_visited":
            decoder = _decode_encounter_visited
        case "clue_spotted":
            decoder = _decode_clue_spotted
        case "clue_missed":
            decoder = _decode_clue_missed
        case "revelation_established":
            decoder = _decode_revelation_established
        case "revelation_foreclosed":
            decoder = _decode_revelation_foreclosed
        case "revelation_reopened":
            decoder = _decode_revelation_reopened
        case "dice_roll_recorded":
            return lambda data, sequence, operation_number: _decode_dice_roll_recorded(
                data, sequence, operation_number, context
            )
        case "encounter_unlocked":
            decoder = _decode_encounter_unlocked
        case "visit_note_recorded":
            decoder = _decode_visit_note_recorded
        case "reference_note_recorded":
            decoder = _decode_reference_note_recorded
        case "encounter_consequence_recorded":
            decoder = _decode_encounter_consequence_recorded
        case "operation_voided":
            decoder = _decode_operation_voided
        case _:
            assert_never(event_type)
    return decoder


def _play_event_v6(data: JsonObject, source: str | Path, index: int) -> PlayEvent:
    raw_event_type = string_value(data, "type")
    if raw_event_type not in PLAY_EVENT_KINDS:
        raise ValueError(f"Unknown play event type {raw_event_type!r}.")
    event_type = raw_event_type
    context = f"{source} events[{index}] ({event_type})"
    reject_unknown_fields(data, play_event_object_fields(event_type), context)
    return _play_event_v6_decoder(event_type, context)(
        data,
        positive_integer(data, "sequence"),
        positive_integer(data, "operation_number"),
    )


# Keep canonical event encoding exhaustive and schema-adjacent.
def _play_event_data(event: PlayEvent) -> JsonObject:
    base: JsonObject = {
        "sequence": event.sequence,
        "operation_number": event.operation_number,
    }
    if isinstance(event, PlayOperationVoidedEvent):
        return {
            **base,
            "type": "operation_voided",
            "target_operation_number": event.target_operation_number,
            "reason": event.reason,
        }
    if isinstance(event, SessionStartedEvent):
        return {
            **base,
            "type": "session_started",
            "session_number": event.session_number,
            "title": event.title,
            "played_on": event.played_on,
            "participants": list(event.participants),
            "attendance_note": event.attendance_note,
            "opening_note": event.opening_note,
        }
    if isinstance(event, SessionEndedEvent):
        return {
            **base,
            "type": "session_ended",
            "session_number": event.session_number,
            "closing_note": event.closing_note,
        }
    if isinstance(event, EncounterVisitedEvent):
        return {
            **base,
            "type": "encounter_visited",
            "visit_number": event.visit_number,
            "encounter_id": event.encounter_id,
            "party_label": event.party_label,
        }
    if isinstance(event, ClueSpottedEvent):
        return {
            **base,
            "type": "clue_spotted",
            "clue_id": event.clue_id,
            "visit_number": event.visit_number,
        }
    if isinstance(event, ClueMissedEvent):
        return {
            **base,
            "type": "clue_missed",
            "clue_id": event.clue_id,
            "visit_number": event.visit_number,
        }
    if isinstance(event, RevelationEstablishedEvent):
        return {
            **base,
            "type": "revelation_established",
            "revelation_id": event.revelation_id,
            "supporting_clue_ids": list(event.supporting_clue_ids),
            "note": event.note,
        }
    if isinstance(event, RevelationForeclosedEvent):
        return {
            **base,
            "type": "revelation_foreclosed",
            "revelation_id": event.revelation_id,
            "reason": event.reason,
        }
    if isinstance(event, RevelationReopenedEvent):
        return {
            **base,
            "type": "revelation_reopened",
            "revelation_id": event.revelation_id,
            "reason": event.reason,
        }
    if isinstance(event, DiceRollRecordedEvent):
        return {
            **base,
            "type": "dice_roll_recorded",
            "expression": event.expression,
            "label": event.label,
            "terms": [_dice_term_data(term) for term in event.terms],
            "total": event.total,
        }
    if isinstance(event, EncounterUnlockedEvent):
        return {
            **base,
            "type": "encounter_unlocked",
            "encounter_id": event.encounter_id,
            "source_revelation_id": event.source_revelation_id,
            "reason": event.reason,
        }
    if isinstance(event, VisitNoteRecordedEvent):
        return {
            **base,
            "type": "visit_note_recorded",
            "visit_number": event.visit_number,
            "text": event.text,
        }
    if isinstance(event, ReferenceNoteRecordedEvent):
        return {
            **base,
            "type": "reference_note_recorded",
            "reference_id": event.reference_id,
            "text": event.text,
        }
    if isinstance(event, EncounterConsequenceRecordedEvent):
        return {
            **base,
            "type": "encounter_consequence_recorded",
            "encounter_id": event.encounter_id,
            "text": event.text,
        }
    assert_never(event)


def _dice_term(data: JsonObject, context: str) -> DiceGroupResult | DiceModifierResult:
    kind = string_value(data, "kind")
    reject_unknown_fields(data, dice_term_object_fields(kind), context)
    if kind == "dice":
        sign = _signed_integer(data, "sign")
        if sign not in (-1, 1):
            raise ValueError("sign must be -1 or 1 for a dice term.")
        raw_results: object = data.get("results")
        if not isinstance(raw_results, list):
            raise ValueError("results must be a list of positive integers.")
        result_items = cast(list[object], raw_results)
        if not all(
            isinstance(item, int) and not isinstance(item, bool) and item > 0
            for item in result_items
        ):
            raise ValueError("results must be a list of positive integers.")
        results = cast(list[int], result_items)
        if not results:
            raise ValueError("results must contain at least one die result.")
        faces = integer_at_least(data, "faces", 2)
        if any(result > faces for result in results):
            raise ValueError("dice results must not exceed the die's face count.")
        return DiceGroupResult(
            sign=sign,
            faces=faces,
            results=tuple(results),
        )
    if kind == "modifier":
        return DiceModifierResult(value=_signed_integer(data, "value"))
    raise AssertionError(f"Unhandled validated dice result term kind {kind!r}.")


def _dice_term_data(term: DiceGroupResult | DiceModifierResult) -> JsonObject:
    if isinstance(term, DiceGroupResult):
        return {
            "kind": "dice",
            "sign": term.sign,
            "faces": term.faces,
            "results": list(term.results),
        }
    if isinstance(term, DiceModifierResult):
        return {"kind": "modifier", "value": term.value}
    assert_never(term)


def _signed_integer(data: JsonObject, key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer.")
    return value
