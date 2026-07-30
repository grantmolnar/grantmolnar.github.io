"""Revision-aware application boundary for the live session workspace."""

from __future__ import annotations

from dataclasses import dataclass

from adventure_graph.application.dice import DiceRollResult
from adventure_graph.application.play_journal import (
    JournalOperationRecord,
    PlayJournalProject,
    PlayJournalSnapshot,
    journal_operation_records,
)
from adventure_graph.application.play_tracking import (
    add_visit_note,
    end_session,
    establish_revelation,
    foreclose_revelation,
    latest_active_operation_number,
    miss_clue,
    project_play_state,
    record_dice_roll,
    record_encounter_consequence,
    record_reference_note,
    record_visit,
    reopen_revelation,
    spot_clue,
    start_session,
    transition_visit,
    unlock_encounter,
)
from adventure_graph.application.project import ProjectRevision, RevisionConflictError
from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
    Encounter,
    Reference,
    Revelation,
)
from adventure_graph.domain.play_state import (
    EncounterConsequenceRecord,
    PlayProjection,
    PlayState,
    ReferenceNoteRecord,
    VisitRecord,
)
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import ValidationReport


@dataclass(frozen=True, slots=True)
class RunClueStatus:
    """One authored clue and its current discovery status."""

    clue: Clue
    revelation: Revelation
    spotted: bool
    spotted_visit_number: int | None
    missed_visit_numbers: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class RunRevelationStatus:
    """One authored revelation and its current play support."""

    revelation: Revelation
    destination_encounter: Encounter | None
    supporting_clues: tuple[Clue, ...]
    spotted_clues: tuple[Clue, ...]
    is_established: bool
    is_foreclosed: bool
    establishment_clue_ids: tuple[str, ...]
    establishment_note: str
    foreclosure_reason: str = ""


@dataclass(frozen=True, slots=True)
class RunReferenceBacklink:
    """One encounter-local use of a persistent authored reference."""

    encounter: Encounter
    context: str


@dataclass(frozen=True, slots=True)
class RunReferenceStatus:
    """One authored reference plus backlinks and chronological playthrough notes."""

    reference: Reference
    backlinks: tuple[RunReferenceBacklink, ...]
    notes: tuple[ReferenceNoteRecord, ...]


@dataclass(frozen=True, slots=True)
class RunEncounterOption:
    """One encounter available for a new visit in the current projection."""

    encounter: Encounter
    visit_count: int
    current: bool
    authored_from_current: bool
    unspotted_clues: tuple[Clue, ...]


@dataclass(frozen=True, slots=True)
class RunDashboardResult:
    """Current session state and legal authored options for the Recovery workspace."""

    adventure: Adventure
    validation_report: ValidationReport
    revision: ProjectRevision
    projection: PlayProjection
    current_visit: VisitRecord | None
    current_encounter: Encounter | None
    current_clues: tuple[RunClueStatus, ...]
    available_encounters: tuple[RunEncounterOption, ...]
    locked_encounters: tuple[Encounter, ...]
    revelation_statuses: tuple[RunRevelationStatus, ...]
    reference_statuses: tuple[RunReferenceStatus, ...]
    current_consequences: tuple[EncounterConsequenceRecord, ...]
    recent_operations: tuple[JournalOperationRecord, ...]
    total_operation_count: int
    latest_active_operation_number: int | None

    def reference_status_index(self) -> dict[str, RunReferenceStatus]:
        """Return authored references and derived backlinks keyed by stable identity."""
        return {item.reference.id: item for item in self.reference_statuses}


@dataclass(frozen=True, slots=True)
class RecordVisitCommand:
    """Request one atomic visit operation against an expected journal revision."""

    expected_revision: ProjectRevision
    encounter_id: str
    spotted_clue_ids: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    party_label: str = ""


@dataclass(frozen=True, slots=True)
class StartSessionCommand:
    """Request one explicit session start against an expected journal revision."""

    expected_revision: ProjectRevision
    title: str = ""
    played_on: str | None = None
    participants: tuple[str, ...] = ()
    attendance_note: str = ""
    opening_note: str = ""


@dataclass(frozen=True, slots=True)
class EndSessionCommand:
    """Request the end of the currently active explicit session."""

    expected_revision: ProjectRevision
    closing_note: str = ""


@dataclass(frozen=True, slots=True)
class RecordVisitResult:
    """Committed visit operation and resulting journal revision."""

    visit_number: int
    operation_number: int
    revision: ProjectRevision


@dataclass(frozen=True, slots=True)
class SpotClueCommand:
    """Request one clue-discovery operation against an expected journal revision."""

    expected_revision: ProjectRevision
    clue_id: str
    visit_number: int | None = None


@dataclass(frozen=True, slots=True)
class MissClueCommand:
    """Request one visit-specific missed clue opportunity."""

    expected_revision: ProjectRevision
    clue_id: str
    visit_number: int | None = None


@dataclass(frozen=True, slots=True)
class EstablishRevelationCommand:
    """Request one revelation-establishment operation."""

    expected_revision: ProjectRevision
    revelation_id: str
    supporting_clue_ids: tuple[str, ...] = ()
    note: str = ""


@dataclass(frozen=True, slots=True)
class RevelationJudgmentCommand:
    """Request one foreclosure or reopening judgment."""

    expected_revision: ProjectRevision
    revelation_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class UnlockEncounterCommand:
    """Request one explicit encounter-unlock operation."""

    expected_revision: ProjectRevision
    encounter_id: str
    reason: str


@dataclass(frozen=True, slots=True)
class AddVisitNoteCommand:
    """Request one append-only note for an existing visit."""

    expected_revision: ProjectRevision
    visit_number: int
    text: str


@dataclass(frozen=True, slots=True)
class RecordReferenceNoteCommand:
    """Request one append-only note for a persistent authored reference."""

    expected_revision: ProjectRevision
    reference_id: str
    text: str


@dataclass(frozen=True, slots=True)
class RecordEncounterConsequenceCommand:
    """Request one durable consequence for an authored encounter."""

    expected_revision: ProjectRevision
    encounter_id: str
    text: str


@dataclass(frozen=True, slots=True)
class RecordDiceRollCommand:
    """Request one canonical significant-roll operation."""

    expected_revision: ProjectRevision
    result: DiceRollResult
    label: str = ""


@dataclass(frozen=True, slots=True)
class TransitionVisitCommand:
    """Request one atomic transition from the current visit."""

    expected_revision: ProjectRevision
    source_visit_number: int
    notes: tuple[str, ...] = ()
    spotted_clue_ids: tuple[str, ...] = ()
    missed_clue_ids: tuple[str, ...] = ()
    established_revelation_ids: tuple[str, ...] = ()
    consequence_texts: tuple[str, ...] = ()
    destination_encounter_id: str | None = None
    destination_party_label: str = ""


@dataclass(frozen=True, slots=True)
class TransitionVisitResult:
    """Committed transition and optional destination visit."""

    operation_number: int
    destination_visit_number: int | None
    revision: ProjectRevision


@dataclass(frozen=True, slots=True)
class PlayOperationResult:
    """Committed single play operation and resulting journal revision."""

    operation_number: int
    revision: ProjectRevision


class GetRunDashboard:
    """Load the current play projection and authored session affordances."""

    def __init__(self, project: PlayJournalProject, *, recent_operation_limit: int = 8) -> None:
        if recent_operation_limit <= 0:
            raise ValueError("The recent-operation limit must be positive.")
        self._project = project
        self._recent_operation_limit = recent_operation_limit

    def execute(self) -> RunDashboardResult:
        """Return a validated transport-neutral session dashboard."""
        return build_run_dashboard(
            self._project.load(),
            recent_operation_limit=self._recent_operation_limit,
        )


def build_run_dashboard(
    snapshot: PlayJournalSnapshot,
    *,
    recent_operation_limit: int = 8,
) -> RunDashboardResult:
    """Build the live-session dashboard from an already loaded snapshot."""
    if recent_operation_limit <= 0:
        raise ValueError("The recent-operation limit must be positive.")
    adventure = snapshot.adventure
    projection = project_play_state(adventure, snapshot.state)
    current_visit = projection.visits[-1] if projection.visits else None
    encounter_index = adventure.encounter_index()
    current_encounter = (
        None if current_visit is None else encounter_index[current_visit.encounter_id]
    )
    clue_visit_numbers = _clue_visit_numbers(projection)
    current_clues = _current_clues(
        adventure,
        projection,
        current_encounter,
        clue_visit_numbers,
    )
    route_target_ids = _route_target_ids(adventure, current_encounter)
    available_encounters = _available_encounter_options(
        adventure,
        projection,
        current_encounter,
        route_target_ids,
        clue_visit_numbers,
    )
    available_ids = set(projection.available_encounter_ids)
    operations = journal_operation_records(snapshot.state)
    return RunDashboardResult(
        adventure=adventure,
        validation_report=validate_adventure(adventure),
        revision=snapshot.revision,
        projection=projection,
        current_visit=current_visit,
        current_encounter=current_encounter,
        current_clues=current_clues,
        available_encounters=available_encounters,
        locked_encounters=tuple(
            encounter for encounter in adventure.encounters if encounter.id not in available_ids
        ),
        revelation_statuses=_revelation_statuses(adventure, projection),
        reference_statuses=_reference_statuses(adventure, projection),
        current_consequences=tuple(
            item
            for item in projection.consequences
            if current_encounter is not None and item.encounter_id == current_encounter.id
        ),
        recent_operations=operations[-recent_operation_limit:],
        total_operation_count=len(operations),
        latest_active_operation_number=latest_active_operation_number(snapshot.state),
    )


def _reference_statuses(
    adventure: Adventure,
    projection: PlayProjection,
) -> tuple[RunReferenceStatus, ...]:
    backlinks: dict[str, list[RunReferenceBacklink]] = {
        reference.id: [] for reference in adventure.references
    }
    for encounter in adventure.encounters:
        for link in encounter.reference_links:
            backlinks[link.reference_id].append(RunReferenceBacklink(encounter, link.context))
    notes: dict[str, list[ReferenceNoteRecord]] = {
        reference.id: [] for reference in adventure.references
    }
    for note in projection.reference_notes:
        notes[note.reference_id].append(note)
    return tuple(
        RunReferenceStatus(
            reference,
            tuple(backlinks[reference.id]),
            tuple(notes[reference.id]),
        )
        for reference in adventure.references
    )


class StartPlaySession:
    """Commit one revision-aware explicit session start."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: StartSessionCommand) -> PlayOperationResult:
        """Start the next contiguous session without stale overwrite."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = start_session(
            snapshot.state,
            title=command.title,
            played_on=command.played_on,
            participants=command.participants,
            attendance_note=command.attendance_note,
            opening_note=command.opening_note,
        )
        project_play_state(snapshot.adventure, updated)
        return _commit_operation(self._project, snapshot.revision, updated)


class EndPlaySession:
    """Commit one revision-aware explicit session end."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: EndSessionCommand) -> PlayOperationResult:
        """End the active session without stale overwrite."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = end_session(snapshot.state, command.closing_note)
        project_play_state(snapshot.adventure, updated)
        return _commit_operation(self._project, snapshot.revision, updated)


class RecordPlayVisit:
    """Commit one revision-aware atomic visit operation."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: RecordVisitCommand) -> RecordVisitResult:
        """Record a visit, its immediate clues, and notes without stale overwrite."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = record_visit(
            snapshot.adventure,
            snapshot.state,
            command.encounter_id,
            command.spotted_clue_ids,
            command.notes,
            command.party_label,
        )
        operation_number = updated.events[-1].operation_number
        visit_number = project_play_state(snapshot.adventure, updated).visits[-1].visit_number
        revision = self._project.commit_state(updated, snapshot.revision)
        return RecordVisitResult(visit_number, operation_number, revision)


class TransitionPlayVisit:
    """Commit one revision-aware compound transition operation."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: TransitionVisitCommand) -> TransitionVisitResult:
        """Commit the ordered transition without permitting partial journal writes."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        before_visit_count = len(project_play_state(snapshot.adventure, snapshot.state).visits)
        updated = transition_visit(
            snapshot.adventure,
            snapshot.state,
            command.source_visit_number,
            notes=command.notes,
            spotted_clue_ids=command.spotted_clue_ids,
            missed_clue_ids=command.missed_clue_ids,
            established_revelation_ids=command.established_revelation_ids,
            consequence_texts=command.consequence_texts,
            destination_encounter_id=command.destination_encounter_id,
            destination_party_label=command.destination_party_label,
        )
        projection = project_play_state(snapshot.adventure, updated)
        destination_visit_number = (
            projection.visits[-1].visit_number
            if len(projection.visits) > before_visit_count
            else None
        )
        operation_number = updated.events[-1].operation_number
        revision = self._project.commit_state(updated, snapshot.revision)
        return TransitionVisitResult(operation_number, destination_visit_number, revision)


class SpotPlayClue:
    """Commit one revision-aware clue discovery."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: SpotClueCommand) -> PlayOperationResult:
        """Record one clue at an authored source visit."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = spot_clue(
            snapshot.adventure,
            snapshot.state,
            command.clue_id,
            command.visit_number,
        )
        return _commit_operation(self._project, snapshot.revision, updated)


class MissPlayClue:
    """Commit one revision-aware missed clue opportunity."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: MissClueCommand) -> PlayOperationResult:
        """Record one miss at an authored source visit."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = miss_clue(
            snapshot.adventure,
            snapshot.state,
            command.clue_id,
            command.visit_number,
        )
        return _commit_operation(self._project, snapshot.revision, updated)


class EstablishPlayRevelation:
    """Commit one revision-aware revelation establishment."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: EstablishRevelationCommand) -> PlayOperationResult:
        """Establish a revelation and atomically unlock its destination when needed."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = establish_revelation(
            snapshot.adventure,
            snapshot.state,
            command.revelation_id,
            command.supporting_clue_ids,
            command.note,
        )
        return _commit_operation(self._project, snapshot.revision, updated)


class ForeclosePlayRevelation:
    """Commit one revision-aware revelation foreclosure."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: RevelationJudgmentCommand) -> PlayOperationResult:
        """Foreclose one unestablished revelation with an audit reason."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = foreclose_revelation(
            snapshot.adventure,
            snapshot.state,
            command.revelation_id,
            command.reason,
        )
        return _commit_operation(self._project, snapshot.revision, updated)


class ReopenPlayRevelation:
    """Commit one revision-aware revelation reopening."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: RevelationJudgmentCommand) -> PlayOperationResult:
        """Reopen one currently foreclosed revelation with an audit reason."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = reopen_revelation(
            snapshot.adventure,
            snapshot.state,
            command.revelation_id,
            command.reason,
        )
        return _commit_operation(self._project, snapshot.revision, updated)


class UnlockPlayEncounter:
    """Commit one revision-aware explicit encounter unlock."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: UnlockEncounterCommand) -> PlayOperationResult:
        """Unlock an encounter explicitly with an audit reason."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = unlock_encounter(
            snapshot.adventure,
            snapshot.state,
            command.encounter_id,
            command.reason,
        )
        return _commit_operation(self._project, snapshot.revision, updated)


class AddPlayVisitNote:
    """Commit one revision-aware note for an existing visit."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: AddVisitNoteCommand) -> PlayOperationResult:
        """Append one note without rewriting the visit operation."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        project_play_state(snapshot.adventure, snapshot.state)
        updated = add_visit_note(snapshot.state, command.visit_number, command.text)
        project_play_state(snapshot.adventure, updated)
        return _commit_operation(self._project, snapshot.revision, updated)


class RecordPlayReferenceNote:
    """Commit one revision-aware note for a persistent authored reference."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: RecordReferenceNoteCommand) -> PlayOperationResult:
        """Append one reference note without changing authored reference prose."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = record_reference_note(
            snapshot.adventure,
            snapshot.state,
            command.reference_id,
            command.text,
        )
        return _commit_operation(self._project, snapshot.revision, updated)


class RecordPlayEncounterConsequence:
    """Commit one revision-aware durable encounter consequence."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: RecordEncounterConsequenceCommand) -> PlayOperationResult:
        """Record how play changed one authored encounter."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = record_encounter_consequence(
            snapshot.adventure,
            snapshot.state,
            command.encounter_id,
            command.text,
        )
        return _commit_operation(self._project, snapshot.revision, updated)


class RecordPlayDiceRoll:
    """Commit one revision-aware significant dice result."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, command: RecordDiceRollCommand) -> PlayOperationResult:
        """Record one already-generated roll without rerolling it."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        updated = record_dice_roll(snapshot.state, command.result, command.label)
        project_play_state(snapshot.adventure, updated)
        return _commit_operation(self._project, snapshot.revision, updated)


def _commit_operation(
    project: PlayJournalProject,
    revision: ProjectRevision,
    updated_state: PlayState,
) -> PlayOperationResult:
    operation_number = updated_state.events[-1].operation_number
    committed_revision = project.commit_state(updated_state, revision)
    return PlayOperationResult(operation_number, committed_revision)


def _require_revision(current: ProjectRevision, expected: ProjectRevision) -> None:
    if current != expected:
        raise RevisionConflictError(
            "The adventure or play journal changed after this session view was loaded; "
            "reload before recording another operation."
        )


def _clue_visit_numbers(projection: PlayProjection) -> dict[str, int]:
    return {
        clue_id: visit.visit_number
        for visit in projection.visits
        for clue_id in visit.spotted_clue_ids
    }


def _current_clues(
    adventure: Adventure,
    projection: PlayProjection,
    current_encounter: Encounter | None,
    clue_visit_numbers: dict[str, int],
) -> tuple[RunClueStatus, ...]:
    if current_encounter is None:
        return ()
    revelation_index = adventure.revelation_index()
    clue_progress = {progress.clue_id: progress for progress in projection.clue_progress}
    return tuple(
        RunClueStatus(
            clue=clue,
            revelation=revelation_index[clue.revelation_id],
            spotted=clue.id in clue_visit_numbers,
            spotted_visit_number=clue_visit_numbers.get(clue.id),
            missed_visit_numbers=clue_progress[clue.id].missed_visit_numbers,
        )
        for clue in adventure.clues
        if clue.source_encounter_id == current_encounter.id
        and clue.revelation_id in revelation_index
    )


def _route_target_ids(adventure: Adventure, current_encounter: Encounter | None) -> set[str]:
    if current_encounter is None:
        return set()
    revelation_index = adventure.revelation_index()
    return {
        target_id
        for clue in adventure.clues
        if clue.source_encounter_id == current_encounter.id
        and (revelation := revelation_index.get(clue.revelation_id)) is not None
        and (target_id := revelation.unlocks_encounter_id) is not None
    }


def _available_encounter_options(
    adventure: Adventure,
    projection: PlayProjection,
    current_encounter: Encounter | None,
    route_target_ids: set[str],
    clue_visit_numbers: dict[str, int],
) -> tuple[RunEncounterOption, ...]:
    available_ids = set(projection.available_encounter_ids)
    visit_counts: dict[str, int] = {}
    for visit in projection.visits:
        visit_counts[visit.encounter_id] = visit_counts.get(visit.encounter_id, 0) + 1
    clues_by_encounter: dict[str, list[Clue]] = {}
    for clue in adventure.clues:
        if clue.id not in clue_visit_numbers:
            clues_by_encounter.setdefault(clue.source_encounter_id, []).append(clue)
    return tuple(
        RunEncounterOption(
            encounter=encounter,
            visit_count=visit_counts.get(encounter.id, 0),
            current=current_encounter is not None and encounter.id == current_encounter.id,
            authored_from_current=encounter.id in route_target_ids,
            unspotted_clues=tuple(clues_by_encounter.get(encounter.id, ())),
        )
        for encounter in adventure.encounters
        if encounter.id in available_ids
    )


def _revelation_statuses(
    adventure: Adventure,
    projection: PlayProjection,
) -> tuple[RunRevelationStatus, ...]:
    encounter_index = adventure.encounter_index()
    progress_index = projection.revelation_progress_index()
    rows: list[RunRevelationStatus] = []
    for revelation in adventure.revelations:
        progress = progress_index[revelation.id]
        supporting_clues = tuple(
            clue for clue in adventure.clues if clue.revelation_id == revelation.id
        )
        spotted_ids = set(progress.spotted_clue_ids)
        rows.append(
            RunRevelationStatus(
                revelation=revelation,
                destination_encounter=(
                    encounter_index.get(revelation.unlocks_encounter_id)
                    if revelation.unlocks_encounter_id is not None
                    else None
                ),
                supporting_clues=supporting_clues,
                spotted_clues=tuple(clue for clue in supporting_clues if clue.id in spotted_ids),
                is_established=progress.is_established,
                is_foreclosed=progress.is_foreclosed,
                establishment_clue_ids=progress.establishment_clue_ids,
                establishment_note=progress.establishment_note,
                foreclosure_reason=progress.foreclosure_reason,
            )
        )
    return tuple(rows)
