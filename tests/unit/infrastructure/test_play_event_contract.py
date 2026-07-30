"""Contracts aligning the play-event algebra, persistence, and derived kind vocabularies."""

from __future__ import annotations

from typing import get_args

import pytest
from tests.support.adventures import PERSON_REFERENCE_ID, reference_library_adventure

from adventure_graph.application.play_journal import JournalEventKind, journal_operation_records
from adventure_graph.application.play_projection import project_play_state
from adventure_graph.domain.play_events import (
    PLAY_CONTENT_EVENT_KINDS,
    PLAY_EVENT_KINDS,
    ClueMissedEvent,
    ClueSpottedEvent,
    DiceGroupResult,
    DiceModifierResult,
    DiceRollRecordedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    PlayContentEvent,
    PlayContentEventKind,
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
from adventure_graph.infrastructure.play_state_store import (
    MAX_PLAY_STATE_EVENTS,
    play_state_data,
    play_state_from_data,
)


def _representative_events() -> tuple[PlayEvent, ...]:
    return (
        SessionStartedEvent(
            sequence=1,
            session_number=1,
            operation_number=1,
            title="Opening",
            played_on="2026-07-24",
            participants=("Ari", "Bryn"),
            attendance_note="All present",
            opening_note="At the gate",
        ),
        SessionEndedEvent(
            sequence=2,
            session_number=1,
            operation_number=2,
            closing_note="At rest",
        ),
        EncounterVisitedEvent(
            sequence=3,
            visit_number=1,
            encounter_id="start",
            operation_number=3,
            party_label="The Lantern Company",
        ),
        ClueSpottedEvent(
            sequence=4,
            clue_id="clue-a",
            visit_number=1,
            operation_number=4,
        ),
        ClueMissedEvent(
            sequence=5,
            clue_id="clue-b",
            visit_number=1,
            operation_number=5,
        ),
        RevelationEstablishedEvent(
            sequence=6,
            revelation_id="truth",
            operation_number=6,
            supporting_clue_ids=("clue-a",),
            note="Confirmed",
        ),
        RevelationForeclosedEvent(
            sequence=7,
            revelation_id="lost-truth",
            reason="The witness departed",
            operation_number=7,
        ),
        RevelationReopenedEvent(
            sequence=8,
            revelation_id="lost-truth",
            reason="The witness returned",
            operation_number=8,
        ),
        DiceRollRecordedEvent(
            sequence=9,
            expression="2d6+1",
            terms=(DiceGroupResult(sign=1, faces=6, results=(2, 5)), DiceModifierResult(1)),
            total=8,
            operation_number=9,
            label="Search",
        ),
        EncounterUnlockedEvent(
            sequence=10,
            encounter_id="vault",
            operation_number=10,
            source_revelation_id="truth",
            reason="The seal yields",
        ),
        VisitNoteRecordedEvent(
            sequence=11,
            visit_number=1,
            text="The gate remains watched.",
            operation_number=11,
        ),
        ReferenceNoteRecordedEvent(
            sequence=12,
            reference_id=PERSON_REFERENCE_ID,
            text="Cora now trusts the party.",
            operation_number=12,
        ),
        EncounterConsequenceRecordedEvent(
            sequence=13,
            encounter_id="start",
            text="The ward is broken.",
            operation_number=13,
        ),
        PlayOperationVoidedEvent(
            sequence=14,
            operation_number=14,
            target_operation_number=13,
            reason="Recorded against the wrong encounter.",
        ),
    )


def test_event_union_kind_vocabulary_and_canonical_codec_remain_aligned() -> None:
    """Require every domain event class and canonical kind to round-trip exactly once."""
    events = _representative_events()
    state = PlayState(adventure_id="contract", events=events)
    data = play_state_data(state)
    encoded_events = data["events"]
    assert isinstance(encoded_events, list)
    encoded_kinds = tuple(item["type"] for item in encoded_events if isinstance(item, dict))

    assert {type(event) for event in events} == set(get_args(PlayEvent))
    assert tuple(get_args(PlayContentEventKind)) == PLAY_CONTENT_EVENT_KINDS
    assert encoded_kinds == PLAY_EVENT_KINDS
    assert play_state_from_data(data) == state


def test_journal_records_use_the_shared_event_kind_vocabulary() -> None:
    """Keep the raw journal read model on the same closed kind contract as persistence."""
    state = PlayState(adventure_id="contract", events=_representative_events())
    record_kinds: tuple[JournalEventKind, ...] = tuple(
        event.kind for operation in journal_operation_records(state) for event in operation.events
    )
    assert record_kinds == PLAY_EVENT_KINDS


def test_narrative_projection_uses_every_content_event_kind() -> None:
    """Keep active narrative kinds aligned with the content-event algebra."""
    adventure = reference_library_adventure()
    events: tuple[PlayContentEvent, ...] = (
        SessionStartedEvent(1, 1, 1),
        EncounterVisitedEvent(2, 1, "alpha", 2),
        ClueMissedEvent(3, "alpha-to-gamma", 1, 3),
        ClueSpottedEvent(4, "alpha-to-beta", 1, 4),
        RevelationEstablishedEvent(5, "find-beta", 5, ("alpha-to-beta",)),
        RevelationForeclosedEvent(6, "find-gamma", "Unavailable", 6),
        RevelationReopenedEvent(7, "find-gamma", "Available again", 7),
        DiceRollRecordedEvent(
            8,
            "1d6",
            (DiceGroupResult(sign=1, faces=6, results=(4,)),),
            4,
            8,
        ),
        EncounterUnlockedEvent(9, "beta", 9, source_revelation_id="find-beta"),
        VisitNoteRecordedEvent(10, 1, "A note", 10),
        ReferenceNoteRecordedEvent(11, PERSON_REFERENCE_ID, "Cora relented", 11),
        EncounterConsequenceRecordedEvent(12, "alpha", "A consequence", 12),
        SessionEndedEvent(13, 1, 13),
    )
    projection = project_play_state(adventure, PlayState(adventure.id, events))
    narrative_kinds = tuple(record.kind for record in projection.narrative)
    assert len(narrative_kinds) == len(PLAY_CONTENT_EVENT_KINDS)
    assert set(narrative_kinds) == set(PLAY_CONTENT_EVENT_KINDS)


def test_canonical_decoder_remains_fail_closed_for_unknown_event_kinds() -> None:
    """Reject persisted event kinds outside the shared closed vocabulary."""
    with pytest.raises(ValueError, match="Unknown play event type 'future_event'"):
        play_state_from_data(
            {
                "schema_version": 6,
                "adventure_id": "contract",
                "events": [
                    {
                        "sequence": 1,
                        "operation_number": 1,
                        "type": "future_event",
                    }
                ],
            }
        )


def test_play_state_decoder_rejects_excessive_event_counts_before_event_decoding() -> None:
    with pytest.raises(ValueError, match="events exceeds the supported limit"):
        play_state_from_data(
            {
                "schema_version": 6,
                "adventure_id": "contract",
                "events": [{}] * (MAX_PLAY_STATE_EVENTS + 1),
            }
        )


def test_play_state_encoder_rejects_excessive_event_counts() -> None:
    event = EncounterVisitedEvent(1, 1, "start", 1)
    state = PlayState("contract", (event,) * (MAX_PLAY_STATE_EVENTS + 1))

    with pytest.raises(ValueError, match=r"at most .* persisted events"):
        play_state_data(state)
