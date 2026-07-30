"""Command facade for explicit actual-play journals."""

from __future__ import annotations

from dataclasses import dataclass, field, replace

from adventure_graph.application.dice import (
    MAX_LABEL_CHARACTERS,
    DiceExpressionError,
    DiceRollResult,
    validate_dice_roll,
)
from adventure_graph.application.play_errors import PlayTrackingError
from adventure_graph.application.play_journal_validation import (
    session_state,
    validate_journal_shape,
    validate_played_on,
)
from adventure_graph.application.play_projection import project_play_state
from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
)
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
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
from adventure_graph.domain.play_state import (
    PlayProjection,
    PlayState,
    VisitRecord,
)

__all__ = [
    "PlayTrackingError",
    "add_visit_note",
    "correct_latest_operation",
    "end_session",
    "establish_revelation",
    "foreclose_revelation",
    "latest_active_operation_number",
    "miss_clue",
    "new_play_state",
    "project_play_state",
    "record_dice_roll",
    "record_encounter_consequence",
    "record_reference_note",
    "record_visit",
    "reopen_revelation",
    "spot_clue",
    "start_session",
    "transition_visit",
    "unlock_encounter",
]


def new_play_state(adventure: Adventure) -> PlayState:
    """Create an empty event journal for an adventure."""
    return PlayState(adventure_id=adventure.id)


@dataclass(slots=True)
class _PendingPlayOperation:
    """Assemble one validated atomic play operation before committing it."""

    adventure: Adventure
    original_state: PlayState
    operation_number: int = field(init=False)
    events: list[PlayEvent] = field(default_factory=list[PlayEvent], init=False)
    projection: PlayProjection = field(init=False)

    def __post_init__(self) -> None:
        self.projection = project_play_state(self.adventure, self.original_state)
        _require_content_operation_allowed(self.original_state)
        self.operation_number = _next_operation_number(self.original_state)

    @property
    def next_sequence(self) -> int:
        """Return the canonical sequence number for the next pending event."""
        return len(self.original_state.events) + len(self.events) + 1

    @property
    def state(self) -> PlayState:
        """Return the journal with all currently pending events applied."""
        return replace(
            self.original_state,
            events=(*self.original_state.events, *self.events),
        )

    def append(self, event: PlayEvent) -> None:
        """Append an event only when its atomic-operation metadata is canonical."""
        if event.sequence != self.next_sequence:
            raise RuntimeError("Pending play event has a noncanonical sequence number.")
        if event.operation_number != self.operation_number:
            raise RuntimeError("Pending play event has a mismatched operation number.")
        self.events.append(event)

    def refresh(self) -> PlayProjection:
        """Reproject pending events when a later validation depends on them."""
        self.projection = project_play_state(self.adventure, self.state)
        return self.projection

    def finish(self) -> PlayState:
        """Validate and return the completed atomic operation."""
        updated = self.state
        self.projection = project_play_state(self.adventure, updated)
        return updated


def start_session(
    state: PlayState,
    *,
    title: str = "",
    played_on: str | None = None,
    participants: tuple[str, ...] = (),
    attendance_note: str = "",
    opening_note: str = "",
) -> PlayState:
    """Append one explicit session boundary with optional table metadata."""
    validate_journal_shape(state)
    active_session, session_numbers = session_state(state)
    if active_session is not None:
        raise PlayTrackingError(f"Session {active_session} is already active.")
    clean_participants = tuple(item.strip() for item in participants)
    if any(not item for item in clean_participants):
        raise PlayTrackingError("Session participants cannot contain blank names.")
    if len(set(clean_participants)) != len(clean_participants):
        raise PlayTrackingError("Session participants cannot be listed twice.")
    validate_played_on(played_on)
    event = SessionStartedEvent(
        sequence=_next_sequence(state),
        session_number=len(session_numbers) + 1,
        operation_number=_next_operation_number(state),
        title=title.strip(),
        played_on=played_on,
        participants=clean_participants,
        attendance_note=attendance_note.strip(),
        opening_note=opening_note.strip(),
    )
    updated = _append(state, event)
    validate_journal_shape(updated)
    return updated


def end_session(state: PlayState, closing_note: str = "") -> PlayState:
    """Append the end boundary for the currently active explicit session."""
    validate_journal_shape(state)
    active_session, _ = session_state(state)
    if active_session is None:
        raise PlayTrackingError("No explicit session is active.")
    updated = _append(
        state,
        SessionEndedEvent(
            sequence=_next_sequence(state),
            session_number=active_session,
            operation_number=_next_operation_number(state),
            closing_note=closing_note.strip(),
        ),
    )
    validate_journal_shape(updated)
    return updated


def record_visit(
    adventure: Adventure,
    state: PlayState,
    encounter_id: str,
    spotted_clue_ids: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
    party_label: str = "",
) -> PlayState:
    """Append an encounter visit and optional clue/note events as one atomic operation."""
    operation = _PendingPlayOperation(adventure, state)
    _append_visit(
        operation,
        encounter_id,
        spotted_clue_ids=spotted_clue_ids,
        notes=notes,
        party_label=party_label,
    )
    return operation.finish()


def spot_clue(
    adventure: Adventure,
    state: PlayState,
    clue_id: str,
    visit_number: int | None = None,
) -> PlayState:
    """Append one first-discovery event for a clue at an authored source visit."""
    operation = _PendingPlayOperation(adventure, state)
    _append_spotted_clue(operation, clue_id, visit_number)
    return operation.finish()


def miss_clue(
    adventure: Adventure,
    state: PlayState,
    clue_id: str,
    visit_number: int | None = None,
) -> PlayState:
    """Append one visit-specific missed opportunity for an unresolved clue."""
    operation = _PendingPlayOperation(adventure, state)
    _append_missed_clue(operation, clue_id, visit_number)
    return operation.finish()


def establish_revelation(
    adventure: Adventure,
    state: PlayState,
    revelation_id: str,
    supporting_clue_ids: tuple[str, ...] = (),
    note: str = "",
) -> PlayState:
    """Establish a revelation explicitly and unlock its destination when applicable."""
    operation = _PendingPlayOperation(adventure, state)
    _append_established_revelation(
        operation,
        revelation_id,
        supporting_clue_ids,
        note,
    )
    return operation.finish()


def foreclose_revelation(
    adventure: Adventure,
    state: PlayState,
    revelation_id: str,
    reason: str,
) -> PlayState:
    """Append one explicit judgment foreclosing an unestablished revelation."""
    projection = project_play_state(adventure, state)
    _require_content_operation_allowed(state)
    if revelation_id not in adventure.revelation_index():
        raise PlayTrackingError(f"Unknown revelation {revelation_id!r}.")
    progress = projection.revelation_progress_index()[revelation_id]
    if progress.is_established:
        raise PlayTrackingError(f"Established revelation {revelation_id!r} cannot be foreclosed.")
    if progress.is_foreclosed:
        raise PlayTrackingError(f"Revelation {revelation_id!r} is already foreclosed.")
    clean_reason = reason.strip()
    if not clean_reason:
        raise PlayTrackingError("Revelation foreclosure requires a reason.")
    updated = _append(
        state,
        RevelationForeclosedEvent(
            sequence=_next_sequence(state),
            revelation_id=revelation_id,
            reason=clean_reason,
            operation_number=_next_operation_number(state),
        ),
    )
    project_play_state(adventure, updated)
    return updated


def reopen_revelation(
    adventure: Adventure,
    state: PlayState,
    revelation_id: str,
    reason: str,
) -> PlayState:
    """Append one explicit judgment reopening a currently foreclosed revelation."""
    projection = project_play_state(adventure, state)
    _require_content_operation_allowed(state)
    if revelation_id not in adventure.revelation_index():
        raise PlayTrackingError(f"Unknown revelation {revelation_id!r}.")
    progress = projection.revelation_progress_index()[revelation_id]
    if not progress.is_foreclosed:
        raise PlayTrackingError(f"Revelation {revelation_id!r} is not currently foreclosed.")
    clean_reason = reason.strip()
    if not clean_reason:
        raise PlayTrackingError("Revelation reopening requires a reason.")
    updated = _append(
        state,
        RevelationReopenedEvent(
            sequence=_next_sequence(state),
            revelation_id=revelation_id,
            reason=clean_reason,
            operation_number=_next_operation_number(state),
        ),
    )
    project_play_state(adventure, updated)
    return updated


def unlock_encounter(
    adventure: Adventure,
    state: PlayState,
    encounter_id: str,
    reason: str,
) -> PlayState:
    """Make an encounter available explicitly when no authored revelation did so."""
    projection = project_play_state(adventure, state)
    _require_content_operation_allowed(state)
    if encounter_id not in adventure.encounter_index():
        raise PlayTrackingError(f"Unknown encounter {encounter_id!r}.")
    if encounter_id in projection.available_encounter_ids:
        raise PlayTrackingError(f"Encounter {encounter_id!r} is already available.")
    clean_reason = reason.strip()
    if not clean_reason:
        raise PlayTrackingError("An explicit encounter unlock requires a reason.")
    updated = _append(
        state,
        EncounterUnlockedEvent(
            sequence=_next_sequence(state),
            encounter_id=encounter_id,
            operation_number=_next_operation_number(state),
            reason=clean_reason,
        ),
    )
    project_play_state(adventure, updated)
    return updated


def add_visit_note(state: PlayState, visit_number: int, note: str) -> PlayState:
    """Append a note event referring to an existing visit."""
    validate_journal_shape(state)
    _require_content_operation_allowed(state)
    clean_note = note.strip()
    if not clean_note:
        raise PlayTrackingError("Encounter notes cannot be blank.")
    if visit_number not in {visit.visit_number for visit in state.visits}:
        raise PlayTrackingError(f"Visit sequence {visit_number} does not exist.")
    return _append(
        state,
        VisitNoteRecordedEvent(
            sequence=_next_sequence(state),
            visit_number=visit_number,
            text=clean_note,
            operation_number=_next_operation_number(state),
        ),
    )


def record_reference_note(
    adventure: Adventure,
    state: PlayState,
    reference_id: str,
    text: str,
) -> PlayState:
    """Append one playthrough note associated with a persistent reference."""
    operation = _PendingPlayOperation(adventure, state)
    if reference_id not in adventure.reference_index():
        raise PlayTrackingError(f"Unknown reference {reference_id!r}.")
    clean_text = text.strip()
    if not clean_text:
        raise PlayTrackingError("Reference notes cannot be blank.")
    operation.append(
        ReferenceNoteRecordedEvent(
            sequence=operation.next_sequence,
            reference_id=reference_id,
            text=clean_text,
            operation_number=operation.operation_number,
        )
    )
    return operation.finish()


def record_encounter_consequence(
    adventure: Adventure,
    state: PlayState,
    encounter_id: str,
    text: str,
) -> PlayState:
    """Append a durable note describing how play changed one encounter."""
    operation = _PendingPlayOperation(adventure, state)
    _append_encounter_consequence(operation, encounter_id, text)
    return operation.finish()


def record_dice_roll(state: PlayState, result: DiceRollResult, label: str = "") -> PlayState:
    """Append one deliberately retained and fully validated dice result."""
    validate_journal_shape(state)
    _require_content_operation_allowed(state)
    try:
        validate_dice_roll(result)
    except DiceExpressionError as error:
        raise PlayTrackingError(str(error)) from error
    clean_label = label.strip()
    if len(clean_label) > MAX_LABEL_CHARACTERS:
        raise PlayTrackingError(
            f"Dice-roll labels may not exceed {MAX_LABEL_CHARACTERS} characters."
        )
    updated = _append(
        state,
        DiceRollRecordedEvent(
            sequence=_next_sequence(state),
            expression=result.expression,
            terms=result.terms,
            total=result.total,
            operation_number=_next_operation_number(state),
            label=clean_label,
        ),
    )
    validate_journal_shape(updated)
    return updated


def transition_visit(
    adventure: Adventure,
    state: PlayState,
    source_visit_number: int,
    *,
    notes: tuple[str, ...] = (),
    spotted_clue_ids: tuple[str, ...] = (),
    missed_clue_ids: tuple[str, ...] = (),
    established_revelation_ids: tuple[str, ...] = (),
    consequence_texts: tuple[str, ...] = (),
    destination_encounter_id: str | None = None,
    destination_party_label: str = "",
) -> PlayState:
    """Commit one ordered encounter transition as a single correctable operation."""
    operation = _PendingPlayOperation(adventure, state)
    current_visit = _validate_transition_request(
        operation.projection,
        source_visit_number,
        spotted_clue_ids,
        missed_clue_ids,
        established_revelation_ids,
    )

    for note in notes:
        if note.strip():
            _append_visit_note(operation, source_visit_number, note)
    for clue_id in spotted_clue_ids:
        _append_spotted_clue(operation, clue_id, source_visit_number)
    if spotted_clue_ids:
        operation.refresh()
    for clue_id in missed_clue_ids:
        _append_missed_clue(operation, clue_id, source_visit_number)
    for revelation_id in established_revelation_ids:
        supporting_clue_ids = operation.projection.revelation_progress_index()[
            revelation_id
        ].spotted_clue_ids
        _append_established_revelation(
            operation,
            revelation_id,
            supporting_clue_ids,
            "",
        )
        operation.refresh()
    for text in consequence_texts:
        if text.strip():
            _append_encounter_consequence(
                operation,
                current_visit.encounter_id,
                text,
            )
    if destination_encounter_id:
        _append_visit(
            operation,
            destination_encounter_id,
            party_label=destination_party_label,
        )

    if not operation.events:
        raise PlayTrackingError("A transition must record at least one table development.")
    return operation.finish()


def correct_latest_operation(
    adventure: Adventure,
    state: PlayState,
    reason: str,
) -> PlayState:
    """Append a correction that voids the latest still-active play operation."""
    project_play_state(adventure, state)
    clean_reason = reason.strip()
    if not clean_reason:
        raise PlayTrackingError("A journal correction requires a reason.")
    active_operation_numbers = tuple(
        dict.fromkeys(event.operation_number for event in state.active_events)
    )
    if not active_operation_numbers:
        raise PlayTrackingError("The play journal has no active operation to correct.")
    updated = _append(
        state,
        PlayOperationVoidedEvent(
            sequence=_next_sequence(state),
            operation_number=_next_operation_number(state),
            target_operation_number=active_operation_numbers[-1],
            reason=clean_reason,
        ),
    )
    project_play_state(adventure, updated)
    return updated


def latest_active_operation_number(state: PlayState) -> int | None:
    """Return the latest active play operation without validating authored references."""
    operation_numbers = tuple(
        dict.fromkeys(event.operation_number for event in state.active_events)
    )
    return operation_numbers[-1] if operation_numbers else None


def _append_visit(
    operation: _PendingPlayOperation,
    encounter_id: str,
    *,
    spotted_clue_ids: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
    party_label: str = "",
) -> None:
    projection = operation.projection
    encounter_index = operation.adventure.encounter_index()
    clue_index = operation.adventure.clue_index()
    if encounter_id not in encounter_index:
        raise PlayTrackingError(f"Unknown encounter {encounter_id!r}.")
    if encounter_id not in projection.available_encounter_ids:
        raise PlayTrackingError(
            f"Encounter {encounter_id!r} is locked. Establish its revelation or unlock it "
            "explicitly first."
        )
    if len(set(spotted_clue_ids)) != len(spotted_clue_ids):
        raise PlayTrackingError("A lead cannot be listed twice in one visit.")

    already_spotted = set(projection.spotted_clue_ids)
    for clue_id in spotted_clue_ids:
        clue = clue_index.get(clue_id)
        if clue is None:
            raise PlayTrackingError(f"Unknown lead {clue_id!r}.")
        if clue.source_encounter_id != encounter_id:
            raise PlayTrackingError(
                f"Lead {clue_id!r} belongs to encounter {clue.source_encounter_id!r}, "
                f"not {encounter_id!r}."
            )
        if clue_id in already_spotted:
            raise PlayTrackingError(f"Lead {clue_id!r} was already spotted on an earlier visit.")

    visit_number = len(projection.visits) + 1
    operation.append(
        EncounterVisitedEvent(
            sequence=operation.next_sequence,
            visit_number=visit_number,
            encounter_id=encounter_id,
            operation_number=operation.operation_number,
            party_label=party_label.strip(),
        )
    )
    for clue_id in spotted_clue_ids:
        operation.append(
            ClueSpottedEvent(
                sequence=operation.next_sequence,
                clue_id=clue_id,
                visit_number=visit_number,
                operation_number=operation.operation_number,
            )
        )
    for note in (item.strip() for item in notes):
        if note:
            operation.append(
                VisitNoteRecordedEvent(
                    sequence=operation.next_sequence,
                    visit_number=visit_number,
                    text=note,
                    operation_number=operation.operation_number,
                )
            )


def _append_spotted_clue(
    operation: _PendingPlayOperation,
    clue_id: str,
    visit_number: int | None,
) -> None:
    projection = operation.projection
    clue = operation.adventure.clue_index().get(clue_id)
    if clue is None:
        raise PlayTrackingError(f"Unknown lead {clue_id!r}.")
    if clue_id in projection.spotted_clue_ids:
        raise PlayTrackingError(f"Lead {clue_id!r} was already spotted.")
    selected_visit = _select_source_visit(projection, clue, visit_number)
    operation.append(
        ClueSpottedEvent(
            sequence=operation.next_sequence,
            clue_id=clue_id,
            visit_number=selected_visit,
            operation_number=operation.operation_number,
        )
    )


def _append_missed_clue(
    operation: _PendingPlayOperation,
    clue_id: str,
    visit_number: int | None,
) -> None:
    projection = operation.projection
    clue = operation.adventure.clue_index().get(clue_id)
    if clue is None:
        raise PlayTrackingError(f"Unknown lead {clue_id!r}.")
    if clue_id in projection.spotted_clue_ids:
        raise PlayTrackingError(f"Lead {clue_id!r} is already spotted and cannot be missed later.")
    selected_visit = _select_source_visit(projection, clue, visit_number)
    progress = projection.clue_progress_index()[clue_id]
    if selected_visit in progress.missed_visit_numbers:
        raise PlayTrackingError(
            f"Lead {clue_id!r} is already marked missed on visit {selected_visit}."
        )
    operation.append(
        ClueMissedEvent(
            sequence=operation.next_sequence,
            clue_id=clue_id,
            visit_number=selected_visit,
            operation_number=operation.operation_number,
        )
    )


def _append_established_revelation(
    operation: _PendingPlayOperation,
    revelation_id: str,
    supporting_clue_ids: tuple[str, ...],
    note: str,
) -> None:
    projection = operation.projection
    revelation = operation.adventure.revelation_index().get(revelation_id)
    if revelation is None:
        raise PlayTrackingError(f"Unknown revelation {revelation_id!r}.")
    progress = projection.revelation_progress_index()[revelation_id]
    if progress.is_established:
        raise PlayTrackingError(f"Revelation {revelation_id!r} is already established.")
    if progress.is_foreclosed:
        raise PlayTrackingError(
            f"Revelation {revelation_id!r} is foreclosed and must be reopened first."
        )
    if len(set(supporting_clue_ids)) != len(supporting_clue_ids):
        raise PlayTrackingError("A supporting lead cannot be listed twice.")

    spotted = set(projection.spotted_clue_ids)
    clue_index = operation.adventure.clue_index()
    for clue_id in supporting_clue_ids:
        clue = clue_index.get(clue_id)
        if clue is None:
            raise PlayTrackingError(f"Unknown lead {clue_id!r}.")
        if clue_id not in spotted:
            raise PlayTrackingError(
                f"Lead {clue_id!r} cannot establish a revelation before it is spotted."
            )
        if clue.revelation_id != revelation_id:
            raise PlayTrackingError(
                f"Lead {clue_id!r} supports {clue.revelation_id!r}, not {revelation_id!r}."
            )

    operation.append(
        RevelationEstablishedEvent(
            sequence=operation.next_sequence,
            revelation_id=revelation_id,
            operation_number=operation.operation_number,
            supporting_clue_ids=supporting_clue_ids,
            note=note.strip(),
        )
    )
    if (
        revelation.unlocks_encounter_id is not None
        and revelation.unlocks_encounter_id not in projection.available_encounter_ids
    ):
        operation.append(
            EncounterUnlockedEvent(
                sequence=operation.next_sequence,
                encounter_id=revelation.unlocks_encounter_id,
                operation_number=operation.operation_number,
                source_revelation_id=revelation_id,
            )
        )


def _append_visit_note(
    operation: _PendingPlayOperation,
    visit_number: int,
    note: str,
) -> None:
    clean_note = note.strip()
    if not clean_note:
        raise PlayTrackingError("Encounter notes cannot be blank.")
    if visit_number not in {visit.visit_number for visit in operation.projection.visits}:
        raise PlayTrackingError(f"Visit sequence {visit_number} does not exist.")
    operation.append(
        VisitNoteRecordedEvent(
            sequence=operation.next_sequence,
            visit_number=visit_number,
            text=clean_note,
            operation_number=operation.operation_number,
        )
    )


def _append_encounter_consequence(
    operation: _PendingPlayOperation,
    encounter_id: str,
    text: str,
) -> None:
    if encounter_id not in operation.adventure.encounter_index():
        raise PlayTrackingError(f"Unknown encounter {encounter_id!r}.")
    clean_text = text.strip()
    if not clean_text:
        raise PlayTrackingError("Encounter consequences cannot be blank.")
    operation.append(
        EncounterConsequenceRecordedEvent(
            sequence=operation.next_sequence,
            encounter_id=encounter_id,
            text=clean_text,
            operation_number=operation.operation_number,
        )
    )


def _validate_transition_request(
    projection: PlayProjection,
    source_visit_number: int,
    spotted_clue_ids: tuple[str, ...],
    missed_clue_ids: tuple[str, ...],
    established_revelation_ids: tuple[str, ...],
) -> VisitRecord:
    if not projection.visits:
        raise PlayTrackingError("A transition requires an existing current visit.")
    current_visit = projection.visits[-1]
    if source_visit_number != current_visit.visit_number:
        raise PlayTrackingError(
            f"Transition source visit must be current visit {current_visit.visit_number}, "
            f"not {source_visit_number}."
        )
    if len(set(spotted_clue_ids)) != len(spotted_clue_ids):
        raise PlayTrackingError("A lead cannot be found twice in one transition.")
    if len(set(missed_clue_ids)) != len(missed_clue_ids):
        raise PlayTrackingError("A lead cannot be missed twice in one transition.")
    overlap = set(spotted_clue_ids) & set(missed_clue_ids)
    if overlap:
        clue_id = sorted(overlap)[0]
        raise PlayTrackingError(
            f"Lead {clue_id!r} cannot be both found and missed in one transition."
        )
    if len(set(established_revelation_ids)) != len(established_revelation_ids):
        raise PlayTrackingError("A revelation cannot be established twice in one transition.")
    return current_visit


def _select_source_visit(
    projection: PlayProjection,
    clue: Clue,
    visit_number: int | None,
) -> int:
    selected_visit = visit_number
    if selected_visit is None:
        selected_visit = next(
            (
                visit.visit_number
                for visit in reversed(projection.visits)
                if visit.encounter_id == clue.source_encounter_id
            ),
            None,
        )
    visit_index = {visit.visit_number: visit for visit in projection.visits}
    if selected_visit is None:
        raise PlayTrackingError(
            f"Lead {clue.id!r} cannot be recorded before visiting source encounter "
            f"{clue.source_encounter_id!r}."
        )
    visit = visit_index.get(selected_visit)
    if visit is None:
        raise PlayTrackingError(f"Visit {selected_visit} does not exist.")
    if visit.encounter_id != clue.source_encounter_id:
        raise PlayTrackingError(
            f"Visit {selected_visit} is to {visit.encounter_id!r}; lead {clue.id!r} belongs to "
            f"{clue.source_encounter_id!r}."
        )
    return selected_visit


def _require_content_operation_allowed(state: PlayState) -> None:
    active_session, session_numbers = session_state(state)
    if session_numbers and active_session is None:
        raise PlayTrackingError(
            "Explicit sessions have begun; start a new session before recording more play."
        )


def _next_sequence(state: PlayState, pending: list[PlayEvent] | None = None) -> int:
    return len(state.events) + len(pending or ()) + 1


def _next_operation_number(state: PlayState) -> int:
    return state.events[-1].operation_number + 1 if state.events else 1


def _append(state: PlayState, event: PlayEvent) -> PlayState:
    return replace(state, events=(*state.events, event))
