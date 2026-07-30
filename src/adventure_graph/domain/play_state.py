"""Append-only play state and derived projection values."""

from __future__ import annotations

from dataclasses import dataclass

from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    EncounterVisitedEvent,
    PlayContentEvent,
    PlayContentEventKind,
    PlayEvent,
    PlayOperationVoidedEvent,
    VisitNoteRecordedEvent,
)


@dataclass(frozen=True, slots=True)
class VisitRecord:
    """Derived chronological view of one numbered encounter visit during play."""

    visit_number: int
    encounter_id: str
    party_label: str = ""
    spotted_clue_ids: tuple[str, ...] = ()
    missed_clue_ids: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SessionRecord:
    """Derived metadata and operation range for one explicit play session."""

    session_number: int
    start_sequence: int
    start_operation_number: int
    title: str = ""
    played_on: str | None = None
    participants: tuple[str, ...] = ()
    attendance_note: str = ""
    opening_note: str = ""
    end_sequence: int | None = None
    end_operation_number: int | None = None
    closing_note: str = ""
    operation_numbers: tuple[int, ...] = ()
    visit_numbers: tuple[int, ...] = ()

    @property
    def is_active(self) -> bool:
        """Return whether this explicit session has no active end event."""
        return self.end_sequence is None


@dataclass(frozen=True, slots=True)
class ClueProgress:
    """Derived current discovery state and missed opportunities for one clue."""

    clue_id: str
    missed_visit_numbers: tuple[int, ...] = ()
    spotted_sequence: int | None = None
    spotted_visit_number: int | None = None

    @property
    def is_spotted(self) -> bool:
        """Return whether the clue has been discovered in active history."""
        return self.spotted_sequence is not None


@dataclass(frozen=True, slots=True)
class RevelationProgress:
    """Derived support and establishment status for one revelation."""

    revelation_id: str
    spotted_clue_ids: tuple[str, ...] = ()
    established_sequence: int | None = None
    establishment_clue_ids: tuple[str, ...] = ()
    establishment_note: str = ""
    foreclosure_sequence: int | None = None
    foreclosure_reason: str = ""
    reopening_sequences: tuple[int, ...] = ()

    @property
    def is_supported(self) -> bool:
        """Return whether at least one authored supporting clue has been spotted."""
        return bool(self.spotted_clue_ids)

    @property
    def is_established(self) -> bool:
        """Return whether play explicitly established this revelation."""
        return self.established_sequence is not None

    @property
    def is_foreclosed(self) -> bool:
        """Return whether the latest active judgment currently forecloses it."""
        return self.foreclosure_sequence is not None


@dataclass(frozen=True, slots=True)
class EncounterProgress:
    """Derived availability and visit chronology for one authored encounter."""

    encounter_id: str
    available: bool
    visit_numbers: tuple[int, ...] = ()

    @property
    def visit_count(self) -> int:
        """Return the number of active visits to this encounter."""
        return len(self.visit_numbers)


@dataclass(frozen=True, slots=True)
class NarrativeRecord:
    """One session-aware current-history item for narrative and ledger views."""

    sequence: int
    operation_number: int
    kind: PlayContentEventKind
    session_number: int | None = None
    visit_number: int | None = None
    encounter_id: str = ""
    clue_id: str = ""
    revelation_id: str = ""
    reference_id: str = ""
    text: str = ""


@dataclass(frozen=True, slots=True)
class EncounterUnlockRecord:
    """Derived record of one explicit encounter-availability event."""

    sequence: int
    encounter_id: str
    source_revelation_id: str | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ReferenceNoteRecord:
    """Derived chronological note associated with one persistent reference."""

    sequence: int
    operation_number: int
    reference_id: str
    text: str
    session_number: int | None = None


@dataclass(frozen=True, slots=True)
class EncounterConsequenceRecord:
    """Derived record of one encounter consequence."""

    sequence: int
    encounter_id: str
    text: str


@dataclass(frozen=True, slots=True)
class PlayCorrectionRecord:
    """Derived audit record for one voided play operation."""

    sequence: int
    operation_number: int
    target_operation_number: int
    reason: str


@dataclass(frozen=True, slots=True)
class PlayProjection:
    """Validated current-state projection derived from an append-only event journal."""

    visits: tuple[VisitRecord, ...]
    spotted_clue_ids: tuple[str, ...]
    revelation_progress: tuple[RevelationProgress, ...]
    available_encounter_ids: tuple[str, ...]
    unlocks: tuple[EncounterUnlockRecord, ...]
    consequences: tuple[EncounterConsequenceRecord, ...]
    reference_notes: tuple[ReferenceNoteRecord, ...]
    corrections: tuple[PlayCorrectionRecord, ...]
    sessions: tuple[SessionRecord, ...] = ()
    active_session_number: int | None = None
    clue_progress: tuple[ClueProgress, ...] = ()
    encounter_progress: tuple[EncounterProgress, ...] = ()
    narrative: tuple[NarrativeRecord, ...] = ()

    def revelation_progress_index(self) -> dict[str, RevelationProgress]:
        """Return revelation progress keyed by authored identifier."""
        return {progress.revelation_id: progress for progress in self.revelation_progress}

    def clue_progress_index(self) -> dict[str, ClueProgress]:
        """Return clue progress keyed by authored identifier."""
        return {progress.clue_id: progress for progress in self.clue_progress}

    def encounter_progress_index(self) -> dict[str, EncounterProgress]:
        """Return encounter progress keyed by authored identifier."""
        return {progress.encounter_id: progress for progress in self.encounter_progress}


def project_visit_records(active_events: tuple[PlayContentEvent, ...]) -> tuple[VisitRecord, ...]:
    """Project the visit-centric subset of active play history."""
    visit_events: dict[int, EncounterVisitedEvent] = {}
    spotted_clue_ids: dict[int, list[str]] = {}
    missed_clue_ids: dict[int, list[str]] = {}
    notes: dict[int, list[str]] = {}
    for event in active_events:
        if isinstance(event, EncounterVisitedEvent):
            visit_events[event.visit_number] = event
            spotted_clue_ids.setdefault(event.visit_number, [])
            missed_clue_ids.setdefault(event.visit_number, [])
            notes.setdefault(event.visit_number, [])
        elif isinstance(event, ClueSpottedEvent):
            spotted_clue_ids.setdefault(event.visit_number, []).append(event.clue_id)
        elif isinstance(event, ClueMissedEvent):
            missed_clue_ids.setdefault(event.visit_number, []).append(event.clue_id)
        elif isinstance(event, VisitNoteRecordedEvent):
            notes.setdefault(event.visit_number, []).append(event.text)
    return tuple(
        VisitRecord(
            visit_number=visit_number,
            encounter_id=visit_events[visit_number].encounter_id,
            party_label=visit_events[visit_number].party_label,
            spotted_clue_ids=tuple(spotted_clue_ids.get(visit_number, [])),
            missed_clue_ids=tuple(missed_clue_ids.get(visit_number, [])),
            notes=tuple(notes.get(visit_number, [])),
        )
        for visit_number in sorted(visit_events)
    )


@dataclass(frozen=True, slots=True)
class PlayState:
    """Append-only journal of explicit actual-play events."""

    adventure_id: str
    events: tuple[PlayEvent, ...] = ()

    @property
    def voided_operation_numbers(self) -> frozenset[int]:
        """Return operation numbers voided by append-only correction events."""
        return frozenset(
            event.target_operation_number
            for event in self.events
            if isinstance(event, PlayOperationVoidedEvent)
        )

    @property
    def active_events(self) -> tuple[PlayContentEvent, ...]:
        """Return non-correction events whose operations remain active."""
        voided = self.voided_operation_numbers
        return tuple(
            event
            for event in self.events
            if not isinstance(event, PlayOperationVoidedEvent)
            and event.operation_number not in voided
        )

    @property
    def visits(self) -> tuple[VisitRecord, ...]:
        """Return the active visit log projected from visit, clue, and note events."""
        return project_visit_records(self.active_events)
