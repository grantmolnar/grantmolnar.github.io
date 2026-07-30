"""Revision-aware application boundary for play-journal history and correction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeAlias, assert_never

from adventure_graph.application.play_tracking import (
    correct_latest_operation,
    latest_active_operation_number,
    project_play_state,
)
from adventure_graph.application.project import ProjectRevision
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
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
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import ValidationReport

JournalEventKind: TypeAlias = PlayEventKind


@dataclass(frozen=True, slots=True)
class PlayJournalSnapshot:
    """Adventure and journal loaded at one revision."""

    adventure: Adventure
    state: PlayState
    revision: ProjectRevision


class PlayJournalProject(Protocol):
    """Application-facing port for loading and committing one active journal."""

    def load(self) -> PlayJournalSnapshot:
        """Load one adventure/journal snapshot and its opaque revision."""
        ...

    def commit_state(
        self,
        state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Commit a journal only when its project revision remains current."""
        ...


@dataclass(frozen=True, slots=True)
class JournalEventRecord:
    """Transport-neutral fields for one raw journal event."""

    sequence: int
    operation_number: int
    kind: JournalEventKind
    active: bool
    session_number: int | None = None
    visit_number: int | None = None
    encounter_id: str = ""
    clue_id: str = ""
    revelation_id: str = ""
    reference_id: str = ""
    supporting_clue_ids: tuple[str, ...] = ()
    text: str = ""
    source_revelation_id: str = ""
    target_operation_number: int | None = None
    title: str = ""
    played_on: str | None = None
    participants: tuple[str, ...] = ()
    attendance_note: str = ""
    party_label: str = ""


@dataclass(frozen=True, slots=True)
class JournalOperationRecord:
    """One atomic play operation or correction in raw journal order."""

    operation_number: int
    active: bool
    is_correction: bool
    events: tuple[JournalEventRecord, ...]


@dataclass(frozen=True, slots=True)
class PlayJournalStatusResult:
    """History and current correction affordance for one active play journal."""

    adventure: Adventure
    validation_report: ValidationReport
    revision: ProjectRevision
    event_count: int
    active_event_count: int
    correction_count: int
    latest_active_operation_number: int | None
    operations: tuple[JournalOperationRecord, ...]


@dataclass(frozen=True, slots=True)
class CorrectLatestPlayOperationCommand:
    """Request one append-only correction against an expected journal revision."""

    reason: str
    expected_revision: ProjectRevision


@dataclass(frozen=True, slots=True)
class CorrectLatestPlayOperationResult:
    """Committed correction and resulting journal revision."""

    target_operation_number: int
    correction_sequence: int
    revision: ProjectRevision


class GetPlayJournalStatus:
    """Query raw operation history and the current projection through one port."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self) -> PlayJournalStatusResult:
        """Load and validate one journal before returning its operation history."""
        return build_play_journal_status(self._project.load())


def build_play_journal_status(snapshot: PlayJournalSnapshot) -> PlayJournalStatusResult:
    """Build journal history from an already loaded project snapshot."""
    projection = project_play_state(snapshot.adventure, snapshot.state)
    operations = journal_operation_records(snapshot.state)
    return PlayJournalStatusResult(
        adventure=snapshot.adventure,
        validation_report=validate_adventure(snapshot.adventure),
        revision=snapshot.revision,
        event_count=len(snapshot.state.events),
        active_event_count=len(snapshot.state.active_events),
        correction_count=len(projection.corrections),
        latest_active_operation_number=latest_active_operation_number(snapshot.state),
        operations=operations,
    )


def journal_operation_records(state: PlayState) -> tuple[JournalOperationRecord, ...]:
    """Return raw journal events grouped into atomic operation records."""
    voided = state.voided_operation_numbers
    grouped: dict[int, list[PlayEvent]] = {}
    for event in state.events:
        grouped.setdefault(event.operation_number, []).append(event)
    operations: list[JournalOperationRecord] = []
    for operation_number, events in grouped.items():
        is_correction = isinstance(events[0], PlayOperationVoidedEvent)
        active = not is_correction and operation_number not in voided
        operations.append(
            JournalOperationRecord(
                operation_number=operation_number,
                active=active,
                is_correction=is_correction,
                events=tuple(_event_record(event, active) for event in events),
            )
        )
    return tuple(operations)


class CorrectLatestPlayOperation:
    """Append one correction through a revision-aware journal port."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(
        self,
        command: CorrectLatestPlayOperationCommand,
    ) -> CorrectLatestPlayOperationResult:
        """Correct the latest active operation and commit without stale overwrite."""
        snapshot = self._project.load()
        updated = correct_latest_operation(snapshot.adventure, snapshot.state, command.reason)
        correction = updated.events[-1]
        if not isinstance(correction, PlayOperationVoidedEvent):
            raise RuntimeError("Journal correction did not append a correction event.")
        revision = self._project.commit_state(updated, command.expected_revision)
        return CorrectLatestPlayOperationResult(
            target_operation_number=correction.target_operation_number,
            correction_sequence=correction.sequence,
            revision=revision,
        )


# Keep journal read-model conversion exhaustive and directly auditable.
def _event_record(event: PlayEvent, active: bool) -> JournalEventRecord:
    if isinstance(event, SessionStartedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="session_started",
            session_number=event.session_number,
            title=event.title,
            played_on=event.played_on,
            participants=event.participants,
            attendance_note=event.attendance_note,
            text=event.opening_note,
        )
    elif isinstance(event, SessionEndedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="session_ended",
            session_number=event.session_number,
            text=event.closing_note,
        )
    elif isinstance(event, EncounterVisitedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="encounter_visited",
            visit_number=event.visit_number,
            encounter_id=event.encounter_id,
            party_label=event.party_label,
        )
    elif isinstance(event, ClueSpottedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="clue_spotted",
            visit_number=event.visit_number,
            clue_id=event.clue_id,
        )
    elif isinstance(event, ClueMissedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="clue_missed",
            visit_number=event.visit_number,
            clue_id=event.clue_id,
        )
    elif isinstance(event, RevelationEstablishedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="revelation_established",
            revelation_id=event.revelation_id,
            supporting_clue_ids=event.supporting_clue_ids,
            text=event.note,
        )
    elif isinstance(event, RevelationForeclosedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="revelation_foreclosed",
            revelation_id=event.revelation_id,
            text=event.reason,
        )
    elif isinstance(event, RevelationReopenedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="revelation_reopened",
            revelation_id=event.revelation_id,
            text=event.reason,
        )
    elif isinstance(event, DiceRollRecordedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="dice_roll_recorded",
            title=event.label,
            text=f"{event.expression} = {event.total}",
        )
    elif isinstance(event, EncounterUnlockedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="encounter_unlocked",
            encounter_id=event.encounter_id,
            source_revelation_id=event.source_revelation_id or "",
            text=event.reason,
        )
    elif isinstance(event, VisitNoteRecordedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="visit_note_recorded",
            visit_number=event.visit_number,
            text=event.text,
        )
    elif isinstance(event, ReferenceNoteRecordedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="reference_note_recorded",
            reference_id=event.reference_id,
            text=event.text,
        )
    elif isinstance(event, EncounterConsequenceRecordedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            active=active,
            kind="encounter_consequence_recorded",
            encounter_id=event.encounter_id,
            text=event.text,
        )
    elif isinstance(event, PlayOperationVoidedEvent):
        record = JournalEventRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            kind="operation_voided",
            active=False,
            target_operation_number=event.target_operation_number,
            text=event.reason,
        )
    else:
        assert_never(event)
    return record
