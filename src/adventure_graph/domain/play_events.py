"""Append-only actual-play event values and their closed kind vocabulary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias


@dataclass(frozen=True, slots=True)
class SessionStartedEvent:
    """Record the beginning and table metadata of one explicit play session."""

    sequence: int
    session_number: int
    operation_number: int
    title: str = ""
    played_on: str | None = None
    participants: tuple[str, ...] = ()
    attendance_note: str = ""
    opening_note: str = ""


@dataclass(frozen=True, slots=True)
class SessionEndedEvent:
    """Record the end of the currently active explicit play session."""

    sequence: int
    session_number: int
    operation_number: int
    closing_note: str = ""


@dataclass(frozen=True, slots=True)
class EncounterVisitedEvent:
    """Record that play entered one encounter as a numbered visit."""

    sequence: int
    visit_number: int
    encounter_id: str
    operation_number: int
    party_label: str = ""


@dataclass(frozen=True, slots=True)
class ClueSpottedEvent:
    """Record that a clue was first noticed during a specific visit."""

    sequence: int
    clue_id: str
    visit_number: int
    operation_number: int


@dataclass(frozen=True, slots=True)
class ClueMissedEvent:
    """Record one missed opportunity to discover a clue during one visit."""

    sequence: int
    clue_id: str
    visit_number: int
    operation_number: int


@dataclass(frozen=True, slots=True)
class RevelationEstablishedEvent:
    """Record that the players established a revelation explicitly."""

    sequence: int
    revelation_id: str
    operation_number: int
    supporting_clue_ids: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True, slots=True)
class RevelationForeclosedEvent:
    """Record a GM judgment that one revelation is no longer establishable."""

    sequence: int
    revelation_id: str
    reason: str
    operation_number: int


@dataclass(frozen=True, slots=True)
class RevelationReopenedEvent:
    """Record a later GM judgment reopening one foreclosed revelation."""

    sequence: int
    revelation_id: str
    reason: str
    operation_number: int


@dataclass(frozen=True, slots=True)
class DiceGroupResult:
    """Ordered results for one signed group of like-faced dice."""

    sign: int
    faces: int
    results: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class DiceModifierResult:
    """One signed integer modifier in a recorded dice expression."""

    value: int


DiceRollTerm: TypeAlias = DiceGroupResult | DiceModifierResult


@dataclass(frozen=True, slots=True)
class DiceRollRecordedEvent:
    """Record one deliberately retained dice result and its auditable terms."""

    sequence: int
    expression: str
    terms: tuple[DiceRollTerm, ...]
    total: int
    operation_number: int
    label: str = ""


@dataclass(frozen=True, slots=True)
class EncounterUnlockedEvent:
    """Record that an encounter became available through play or GM adjudication."""

    sequence: int
    encounter_id: str
    operation_number: int
    source_revelation_id: str | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class VisitNoteRecordedEvent:
    """Append a note to one visit without rewriting prior state."""

    sequence: int
    visit_number: int
    text: str
    operation_number: int


@dataclass(frozen=True, slots=True)
class ReferenceNoteRecordedEvent:
    """Append one playthrough note to a persistent authored reference."""

    sequence: int
    reference_id: str
    text: str
    operation_number: int


@dataclass(frozen=True, slots=True)
class EncounterConsequenceRecordedEvent:
    """Record a durable consequence affecting one authored encounter."""

    sequence: int
    encounter_id: str
    text: str
    operation_number: int


@dataclass(frozen=True, slots=True)
class PlayOperationVoidedEvent:
    """Record an honest correction that voids the latest active play operation."""

    sequence: int
    operation_number: int
    target_operation_number: int
    reason: str


PlayContentEvent: TypeAlias = (
    SessionStartedEvent
    | SessionEndedEvent
    | EncounterVisitedEvent
    | ClueSpottedEvent
    | ClueMissedEvent
    | RevelationEstablishedEvent
    | RevelationForeclosedEvent
    | RevelationReopenedEvent
    | DiceRollRecordedEvent
    | EncounterUnlockedEvent
    | VisitNoteRecordedEvent
    | ReferenceNoteRecordedEvent
    | EncounterConsequenceRecordedEvent
)

PlayEvent: TypeAlias = PlayContentEvent | PlayOperationVoidedEvent

PlayContentEventKind: TypeAlias = Literal[
    "session_started",
    "session_ended",
    "encounter_visited",
    "clue_spotted",
    "clue_missed",
    "revelation_established",
    "revelation_foreclosed",
    "revelation_reopened",
    "dice_roll_recorded",
    "encounter_unlocked",
    "visit_note_recorded",
    "reference_note_recorded",
    "encounter_consequence_recorded",
]
PlayEventKind: TypeAlias = PlayContentEventKind | Literal["operation_voided"]

PLAY_CONTENT_EVENT_KINDS: tuple[PlayContentEventKind, ...] = (
    "session_started",
    "session_ended",
    "encounter_visited",
    "clue_spotted",
    "clue_missed",
    "revelation_established",
    "revelation_foreclosed",
    "revelation_reopened",
    "dice_roll_recorded",
    "encounter_unlocked",
    "visit_note_recorded",
    "reference_note_recorded",
    "encounter_consequence_recorded",
)
PLAY_EVENT_KINDS: tuple[PlayEventKind, ...] = (
    "session_started",
    "session_ended",
    "encounter_visited",
    "clue_spotted",
    "clue_missed",
    "revelation_established",
    "revelation_foreclosed",
    "revelation_reopened",
    "dice_roll_recorded",
    "encounter_unlocked",
    "visit_note_recorded",
    "reference_note_recorded",
    "encounter_consequence_recorded",
    "operation_voided",
)
