"""Projection of append-only play journals into current table state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import assert_never

from adventure_graph.application.play_errors import PlayTrackingError
from adventure_graph.application.play_journal_validation import (
    validate_journal_shape,
    validate_recorded_roll,
)
from adventure_graph.domain.adventure import Adventure, Clue, Encounter, Reference, Revelation
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    DiceRollRecordedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    PlayContentEvent,
    PlayOperationVoidedEvent,
    ReferenceNoteRecordedEvent,
    RevelationEstablishedEvent,
    RevelationForeclosedEvent,
    RevelationReopenedEvent,
    SessionEndedEvent,
    SessionStartedEvent,
    VisitNoteRecordedEvent,
)
from adventure_graph.domain.play_state import (
    ClueProgress,
    EncounterConsequenceRecord,
    EncounterProgress,
    EncounterUnlockRecord,
    NarrativeRecord,
    PlayCorrectionRecord,
    PlayProjection,
    PlayState,
    ReferenceNoteRecord,
    RevelationProgress,
    SessionRecord,
    VisitRecord,
)


@dataclass(slots=True)
class _VisitBuilder:
    """Mutable projection state for one encounter visit."""

    encounter_id: str
    party_label: str
    spotted_clue_ids: list[str] = field(default_factory=list[str], init=False)
    missed_clue_ids: list[str] = field(default_factory=list[str])
    notes: list[str] = field(default_factory=list[str])

    def record(self, visit_number: int) -> VisitRecord:
        """Freeze the visit into the public projection value."""
        return VisitRecord(
            visit_number=visit_number,
            encounter_id=self.encounter_id,
            party_label=self.party_label,
            spotted_clue_ids=tuple(self.spotted_clue_ids),
            missed_clue_ids=tuple(self.missed_clue_ids),
            notes=tuple(self.notes),
        )


@dataclass(slots=True)
class _SessionBuilder:
    """Mutable projection state for one explicit play session."""

    start: SessionStartedEvent
    end: SessionEndedEvent | None = None
    operation_numbers: list[int] = field(default_factory=list[int])
    visit_numbers: list[int] = field(default_factory=list[int])

    def record(self) -> SessionRecord:
        """Freeze the session into the public projection value."""
        end = self.end
        return SessionRecord(
            session_number=self.start.session_number,
            start_sequence=self.start.sequence,
            start_operation_number=self.start.operation_number,
            title=self.start.title,
            played_on=self.start.played_on,
            participants=self.start.participants,
            attendance_note=self.start.attendance_note,
            opening_note=self.start.opening_note,
            end_sequence=None if end is None else end.sequence,
            end_operation_number=None if end is None else end.operation_number,
            closing_note="" if end is None else end.closing_note,
            operation_numbers=tuple(self.operation_numbers),
            visit_numbers=tuple(self.visit_numbers),
        )


@dataclass(slots=True)
class _PlayProjectionBuilder:
    """Own the mutable state and invariants of one journal projection."""

    adventure: Adventure
    encounter_index: dict[str, Encounter] = field(init=False)
    clue_index: dict[str, Clue] = field(init=False)
    revelation_index: dict[str, Revelation] = field(init=False)
    reference_index: dict[str, Reference] = field(init=False)
    available_encounter_ids: list[str] = field(init=False)
    available_encounters: set[str] = field(init=False)
    explicitly_unlocked: set[str] = field(default_factory=set[str], init=False)
    spotted_clue_ids: list[str] = field(default_factory=list[str], init=False)
    spotted_clues: set[str] = field(default_factory=set[str], init=False)
    spotted_events: dict[str, ClueSpottedEvent] = field(
        default_factory=dict[str, ClueSpottedEvent], init=False
    )
    missed_clues: dict[str, list[int]] = field(init=False)
    missed_by_visit: set[tuple[str, int]] = field(default_factory=set[tuple[str, int]], init=False)
    established_revelations: dict[str, RevelationEstablishedEvent] = field(
        default_factory=dict[str, RevelationEstablishedEvent], init=False
    )
    foreclosed_revelations: dict[str, RevelationForeclosedEvent] = field(
        default_factory=dict[str, RevelationForeclosedEvent], init=False
    )
    reopening_sequences: dict[str, list[int]] = field(init=False)
    visits: dict[int, _VisitBuilder] = field(default_factory=dict[int, _VisitBuilder], init=False)
    unlocks: list[EncounterUnlockRecord] = field(
        default_factory=list[EncounterUnlockRecord], init=False
    )
    consequences: list[EncounterConsequenceRecord] = field(
        default_factory=list[EncounterConsequenceRecord], init=False
    )
    reference_notes: list[ReferenceNoteRecord] = field(
        default_factory=list[ReferenceNoteRecord], init=False
    )
    narrative: list[NarrativeRecord] = field(default_factory=list[NarrativeRecord], init=False)
    sessions: dict[int, _SessionBuilder] = field(
        default_factory=dict[int, _SessionBuilder], init=False
    )
    active_session_number: int | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.encounter_index = self.adventure.encounter_index()
        self.clue_index = self.adventure.clue_index()
        self.revelation_index = self.adventure.revelation_index()
        self.reference_index = self.adventure.reference_index()
        self.available_encounter_ids = [
            encounter.id for encounter in self.adventure.encounters if encounter.start
        ]
        self.available_encounters = set(self.available_encounter_ids)
        self.missed_clues = {clue.id: [] for clue in self.adventure.clues}
        self.reopening_sequences = {revelation.id: [] for revelation in self.adventure.revelations}

    def apply(self, event: PlayContentEvent) -> None:
        """Validate and project one active content event."""
        if isinstance(event, SessionStartedEvent):
            self._start_session(event)
            return
        if isinstance(event, SessionEndedEvent):
            self._end_session(event)
            return

        self._record_active_operation(event.operation_number)
        if isinstance(event, EncounterVisitedEvent):
            self._visit_encounter(event)
        elif isinstance(event, ClueSpottedEvent):
            self._spot_clue(event)
        elif isinstance(event, ClueMissedEvent):
            self._miss_clue(event)
        elif isinstance(event, RevelationEstablishedEvent):
            self._establish_revelation(event)
        elif isinstance(event, RevelationForeclosedEvent):
            self._foreclose_revelation(event)
        elif isinstance(event, RevelationReopenedEvent):
            self._reopen_revelation(event)
        elif isinstance(event, EncounterUnlockedEvent):
            self._unlock_encounter(event)
        elif isinstance(event, VisitNoteRecordedEvent):
            self.visits[event.visit_number].notes.append(event.text)
        elif isinstance(event, DiceRollRecordedEvent):
            validate_recorded_roll(event)
        elif isinstance(event, ReferenceNoteRecordedEvent):
            self._record_reference_note(event)
        elif isinstance(event, EncounterConsequenceRecordedEvent):
            self._record_consequence(event)
        else:
            assert_never(event)
        self.narrative.append(_narrative_record(event, self.active_session_number))

    def build(self, state: PlayState) -> PlayProjection:
        """Freeze the accumulated state into the public projection."""
        visits = tuple(self.visits[number].record(number) for number in sorted(self.visits))
        encounter_visits: dict[str, list[int]] = {
            encounter.id: [] for encounter in self.adventure.encounters
        }
        for visit in visits:
            encounter_visits[visit.encounter_id].append(visit.visit_number)
        return PlayProjection(
            visits=visits,
            spotted_clue_ids=tuple(self.spotted_clue_ids),
            revelation_progress=tuple(
                self._revelation_progress(revelation.id)
                for revelation in self.adventure.revelations
            ),
            available_encounter_ids=tuple(self.available_encounter_ids),
            unlocks=tuple(self.unlocks),
            consequences=tuple(self.consequences),
            reference_notes=tuple(self.reference_notes),
            corrections=_correction_records(state),
            sessions=tuple(self.sessions[number].record() for number in sorted(self.sessions)),
            active_session_number=self.active_session_number,
            clue_progress=tuple(self._clue_progress(clue.id) for clue in self.adventure.clues),
            encounter_progress=tuple(
                EncounterProgress(
                    encounter_id=encounter.id,
                    available=encounter.id in self.available_encounters,
                    visit_numbers=tuple(encounter_visits[encounter.id]),
                )
                for encounter in self.adventure.encounters
            ),
            narrative=tuple(self.narrative),
        )

    def _start_session(self, event: SessionStartedEvent) -> None:
        self.active_session_number = event.session_number
        self.sessions[event.session_number] = _SessionBuilder(
            start=event,
            operation_numbers=[event.operation_number],
        )
        self.narrative.append(_narrative_record(event, self.active_session_number))

    def _end_session(self, event: SessionEndedEvent) -> None:
        builder = self.sessions[event.session_number]
        _append_unique(builder.operation_numbers, event.operation_number)
        builder.end = event
        self.narrative.append(_narrative_record(event, self.active_session_number))
        self.active_session_number = None

    def _record_active_operation(self, operation_number: int) -> None:
        if self.active_session_number is None:
            return
        _append_unique(
            self.sessions[self.active_session_number].operation_numbers,
            operation_number,
        )

    def _visit_encounter(self, event: EncounterVisitedEvent) -> None:
        if event.encounter_id not in self.encounter_index:
            raise PlayTrackingError(
                f"Unknown encounter {event.encounter_id!r} in event {event.sequence}."
            )
        if event.encounter_id not in self.available_encounters:
            raise PlayTrackingError(
                f"Event {event.sequence} visits locked encounter {event.encounter_id!r}."
            )
        self.visits[event.visit_number] = _VisitBuilder(
            encounter_id=event.encounter_id,
            party_label=event.party_label,
        )
        if self.active_session_number is not None:
            self.sessions[self.active_session_number].visit_numbers.append(event.visit_number)

    def _spot_clue(self, event: ClueSpottedEvent) -> None:
        clue = self._known_clue(event.clue_id, event.sequence)
        if event.clue_id in self.spotted_clues:
            raise PlayTrackingError(f"Lead {event.clue_id!r} is spotted more than once.")
        if self.visits[event.visit_number].encounter_id != clue.source_encounter_id:
            raise PlayTrackingError(
                f"Event {event.sequence} spots lead {event.clue_id!r} outside source encounter "
                f"{clue.source_encounter_id!r}."
            )
        self.spotted_clues.add(event.clue_id)
        self.spotted_clue_ids.append(event.clue_id)
        self.spotted_events[event.clue_id] = event
        self.visits[event.visit_number].spotted_clue_ids.append(event.clue_id)

    def _miss_clue(self, event: ClueMissedEvent) -> None:
        clue = self._known_clue(event.clue_id, event.sequence)
        if event.clue_id in self.spotted_clues:
            raise PlayTrackingError(
                f"Event {event.sequence} marks already-spotted lead {event.clue_id!r} missed."
            )
        if self.visits[event.visit_number].encounter_id != clue.source_encounter_id:
            raise PlayTrackingError(
                f"Event {event.sequence} misses lead {event.clue_id!r} outside source encounter "
                f"{clue.source_encounter_id!r}."
            )
        key = (event.clue_id, event.visit_number)
        if key in self.missed_by_visit:
            raise PlayTrackingError(
                f"Lead {event.clue_id!r} is missed more than once on visit {event.visit_number}."
            )
        self.missed_by_visit.add(key)
        self.missed_clues[event.clue_id].append(event.visit_number)
        self.visits[event.visit_number].missed_clue_ids.append(event.clue_id)

    def _establish_revelation(self, event: RevelationEstablishedEvent) -> None:
        if event.revelation_id not in self.revelation_index:
            raise PlayTrackingError(
                f"Unknown revelation {event.revelation_id!r} in event {event.sequence}."
            )
        if event.revelation_id in self.established_revelations:
            raise PlayTrackingError(
                f"Revelation {event.revelation_id!r} is established more than once."
            )
        if event.revelation_id in self.foreclosed_revelations:
            raise PlayTrackingError(
                f"Event {event.sequence} establishes foreclosed revelation {event.revelation_id!r}."
            )
        if len(set(event.supporting_clue_ids)) != len(event.supporting_clue_ids):
            raise PlayTrackingError(f"Event {event.sequence} repeats a supporting lead.")
        for clue_id in event.supporting_clue_ids:
            clue = self._known_clue(clue_id, event.sequence)
            if clue_id not in self.spotted_clues:
                raise PlayTrackingError(f"Event {event.sequence} cites unspotted lead {clue_id!r}.")
            if clue.revelation_id != event.revelation_id:
                raise PlayTrackingError(
                    f"Event {event.sequence} cites lead {clue_id!r} for the wrong revelation."
                )
        self.established_revelations[event.revelation_id] = event

    def _foreclose_revelation(self, event: RevelationForeclosedEvent) -> None:
        if event.revelation_id not in self.revelation_index:
            raise PlayTrackingError(
                f"Unknown revelation {event.revelation_id!r} in event {event.sequence}."
            )
        if event.revelation_id in self.established_revelations:
            raise PlayTrackingError(
                f"Event {event.sequence} forecloses established revelation {event.revelation_id!r}."
            )
        if event.revelation_id in self.foreclosed_revelations:
            raise PlayTrackingError(
                f"Revelation {event.revelation_id!r} is foreclosed more than once without "
                "reopening."
            )
        if not event.reason.strip():
            raise PlayTrackingError(f"Event {event.sequence} contains a blank foreclosure reason.")
        self.foreclosed_revelations[event.revelation_id] = event

    def _reopen_revelation(self, event: RevelationReopenedEvent) -> None:
        if event.revelation_id not in self.revelation_index:
            raise PlayTrackingError(
                f"Unknown revelation {event.revelation_id!r} in event {event.sequence}."
            )
        if event.revelation_id not in self.foreclosed_revelations:
            raise PlayTrackingError(
                f"Event {event.sequence} reopens revelation {event.revelation_id!r} "
                "without an active foreclosure."
            )
        if not event.reason.strip():
            raise PlayTrackingError(f"Event {event.sequence} contains a blank reopening reason.")
        del self.foreclosed_revelations[event.revelation_id]
        self.reopening_sequences[event.revelation_id].append(event.sequence)

    def _unlock_encounter(self, event: EncounterUnlockedEvent) -> None:
        if event.encounter_id not in self.encounter_index:
            raise PlayTrackingError(
                f"Unknown encounter {event.encounter_id!r} in event {event.sequence}."
            )
        if event.encounter_id in self.explicitly_unlocked:
            raise PlayTrackingError(f"Encounter {event.encounter_id!r} has multiple unlock events.")
        if event.source_revelation_id is None and not event.reason.strip():
            raise PlayTrackingError(
                f"Event {event.sequence} is a manual encounter unlock without a reason."
            )
        if event.source_revelation_id is not None:
            revelation = self.revelation_index.get(event.source_revelation_id)
            if revelation is None:
                raise PlayTrackingError(
                    f"Unknown revelation {event.source_revelation_id!r} in event {event.sequence}."
                )
            if event.source_revelation_id not in self.established_revelations:
                raise PlayTrackingError(
                    f"Event {event.sequence} unlocks an encounter from an unestablished revelation."
                )
            if revelation.unlocks_encounter_id != event.encounter_id:
                raise PlayTrackingError(
                    f"Revelation {event.source_revelation_id!r} does not unlock "
                    f"{event.encounter_id!r}."
                )
        self.explicitly_unlocked.add(event.encounter_id)
        if event.encounter_id not in self.available_encounters:
            self.available_encounters.add(event.encounter_id)
            self.available_encounter_ids.append(event.encounter_id)
        self.unlocks.append(
            EncounterUnlockRecord(
                sequence=event.sequence,
                encounter_id=event.encounter_id,
                source_revelation_id=event.source_revelation_id,
                reason=event.reason,
            )
        )

    def _record_reference_note(self, event: ReferenceNoteRecordedEvent) -> None:
        if event.reference_id not in self.reference_index:
            raise PlayTrackingError(
                f"Unknown reference {event.reference_id!r} in event {event.sequence}."
            )
        self.reference_notes.append(
            ReferenceNoteRecord(
                sequence=event.sequence,
                operation_number=event.operation_number,
                reference_id=event.reference_id,
                text=event.text,
                session_number=self.active_session_number,
            )
        )

    def _record_consequence(self, event: EncounterConsequenceRecordedEvent) -> None:
        if event.encounter_id not in self.encounter_index:
            raise PlayTrackingError(
                f"Unknown encounter {event.encounter_id!r} in event {event.sequence}."
            )
        self.consequences.append(
            EncounterConsequenceRecord(
                sequence=event.sequence,
                encounter_id=event.encounter_id,
                text=event.text,
            )
        )

    def _known_clue(self, clue_id: str, sequence: int) -> Clue:
        clue = self.clue_index.get(clue_id)
        if clue is None:
            raise PlayTrackingError(f"Unknown lead {clue_id!r} in event {sequence}.")
        return clue

    def _revelation_progress(self, revelation_id: str) -> RevelationProgress:
        established = self.established_revelations.get(revelation_id)
        foreclosed = self.foreclosed_revelations.get(revelation_id)
        return RevelationProgress(
            revelation_id=revelation_id,
            spotted_clue_ids=tuple(
                clue_id
                for clue_id in self.spotted_clue_ids
                if self.clue_index[clue_id].revelation_id == revelation_id
            ),
            established_sequence=None if established is None else established.sequence,
            establishment_clue_ids=() if established is None else established.supporting_clue_ids,
            establishment_note="" if established is None else established.note,
            foreclosure_sequence=None if foreclosed is None else foreclosed.sequence,
            foreclosure_reason="" if foreclosed is None else foreclosed.reason,
            reopening_sequences=tuple(self.reopening_sequences[revelation_id]),
        )

    def _clue_progress(self, clue_id: str) -> ClueProgress:
        spotted = self.spotted_events.get(clue_id)
        return ClueProgress(
            clue_id=clue_id,
            missed_visit_numbers=tuple(self.missed_clues[clue_id]),
            spotted_sequence=None if spotted is None else spotted.sequence,
            spotted_visit_number=None if spotted is None else spotted.visit_number,
        )


def project_play_state(adventure: Adventure, state: PlayState) -> PlayProjection:
    """Validate an event journal and derive its current playable state."""
    _require_matching_adventure(adventure, state)
    validate_journal_shape(state)
    builder = _PlayProjectionBuilder(adventure)
    for event in state.active_events:
        builder.apply(event)
    return builder.build(state)


def _correction_records(state: PlayState) -> tuple[PlayCorrectionRecord, ...]:
    return tuple(
        PlayCorrectionRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            target_operation_number=event.target_operation_number,
            reason=event.reason,
        )
        for event in state.events
        if isinstance(event, PlayOperationVoidedEvent)
    )


# Keep narrative conversion exhaustive over the event algebra.
def _narrative_record(event: PlayContentEvent, session_number: int | None) -> NarrativeRecord:
    if isinstance(event, SessionStartedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="session_started",
            text=event.opening_note,
        )
    if isinstance(event, SessionEndedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="session_ended",
            text=event.closing_note,
        )
    if isinstance(event, EncounterVisitedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="encounter_visited",
            visit_number=event.visit_number,
            encounter_id=event.encounter_id,
            text=event.party_label,
        )
    if isinstance(event, ClueSpottedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="clue_spotted",
            visit_number=event.visit_number,
            clue_id=event.clue_id,
        )
    if isinstance(event, ClueMissedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="clue_missed",
            visit_number=event.visit_number,
            clue_id=event.clue_id,
        )
    if isinstance(event, RevelationEstablishedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="revelation_established",
            revelation_id=event.revelation_id,
            text=event.note,
        )
    if isinstance(event, RevelationForeclosedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="revelation_foreclosed",
            revelation_id=event.revelation_id,
            text=event.reason,
        )
    if isinstance(event, RevelationReopenedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="revelation_reopened",
            revelation_id=event.revelation_id,
            text=event.reason,
        )
    if isinstance(event, DiceRollRecordedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="dice_roll_recorded",
            text=f"{event.label}: {event.expression} = {event.total}".strip(": "),
        )
    if isinstance(event, EncounterUnlockedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="encounter_unlocked",
            encounter_id=event.encounter_id,
            revelation_id=event.source_revelation_id or "",
            text=event.reason,
        )
    if isinstance(event, VisitNoteRecordedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="visit_note_recorded",
            visit_number=event.visit_number,
            text=event.text,
        )
    if isinstance(event, ReferenceNoteRecordedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="reference_note_recorded",
            reference_id=event.reference_id,
            text=event.text,
        )
    if isinstance(event, EncounterConsequenceRecordedEvent):
        return NarrativeRecord(
            sequence=event.sequence,
            operation_number=event.operation_number,
            session_number=session_number,
            kind="encounter_consequence_recorded",
            encounter_id=event.encounter_id,
            text=event.text,
        )
    assert_never(event)


def _append_unique(values: list[int], value: int) -> None:
    if not values or values[-1] != value:
        values.append(value)


def _require_matching_adventure(adventure: Adventure, state: PlayState) -> None:
    if state.adventure_id != adventure.id:
        raise PlayTrackingError(
            f"Play state belongs to {state.adventure_id!r}, not adventure {adventure.id!r}."
        )
