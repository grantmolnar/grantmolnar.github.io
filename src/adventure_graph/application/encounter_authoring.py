"""Reusable encounter-detail queries and revision-aware encounter authoring."""

from __future__ import annotations

from dataclasses import dataclass, replace

from adventure_graph.application.authoring import (
    EncounterDependencies,
    encounter_dependencies,
    remove_encounter,
    update_encounter,
)
from adventure_graph.application.dependency_previews import (
    DependencyPreview,
    preview_encounter_dependencies,
)
from adventure_graph.application.errors import (
    EntityNotFoundError,
    NoChangesRequestedError,
)
from adventure_graph.application.project import (
    AuthoringProject,
    AuthoringSnapshot,
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.application.project_integrity import validate_related_play_states
from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
    Encounter,
    Reference,
    Revelation,
)
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import (
    ValidationIssue,
    ValidationReport,
)


@dataclass(frozen=True, slots=True)
class EncounterReferenceDetail:
    """One encounter-local reference link and its resolved adventure record."""

    reference_id: str
    reference: Reference | None
    context: str


@dataclass(frozen=True, slots=True)
class EncounterDetail:
    """Transport-neutral read model for one authored encounter and its relationships."""

    encounter: Encounter
    sourced_clues: tuple[Clue, ...]
    supported_revelations: tuple[Revelation, ...]
    destination_encounters: tuple[Encounter, ...]
    unlocking_revelations: tuple[Revelation, ...]
    incoming_clues: tuple[Clue, ...]
    linked_references: tuple[EncounterReferenceDetail, ...]
    validation_issues: tuple[ValidationIssue, ...]
    dependency_preview: DependencyPreview


@dataclass(frozen=True, slots=True)
class EncounterDetailResult:
    """Encounter detail, complete navigation data, and loaded project metadata."""

    adventure: Adventure
    detail: EncounterDetail
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class UpdateEncounterCommand:
    """Requested encounter-field changes based on one known project revision."""

    encounter_id: str
    expected_revision: ProjectRevision
    title: str | None = None
    summary: str | None = None
    opening_view: str | None = None
    content: str | None = None
    required: bool | None = None
    start: bool | None = None
    end: bool | None = None
    tags: tuple[str, ...] | None = None


@dataclass(frozen=True, slots=True)
class RemoveEncounterCommand:
    """Requested dependency-aware encounter removal."""

    encounter_id: str
    expected_revision: ProjectRevision
    cascade: bool = False


@dataclass(frozen=True, slots=True)
class RemoveEncounterResult:
    """Committed encounter removal and its pre-commit dependency projection."""

    encounter: Encounter
    dependencies: EncounterDependencies
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class UpdateEncounterResult:
    """Committed encounter update and the resulting project state."""

    before: Encounter
    after: Encounter
    revision: ProjectRevision
    validation_report: ValidationReport


class GetEncounterDetail:
    """Load one encounter-oriented read model from an authored project."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, encounter_id: str) -> EncounterDetailResult:
        """Return one encounter detail at the currently loaded project revision."""
        snapshot = self._project.load()
        report = validate_adventure(snapshot.adventure)
        return EncounterDetailResult(
            adventure=snapshot.adventure,
            detail=_encounter_detail(snapshot, report, encounter_id),
            revision=snapshot.revision,
            validation_report=report,
        )


class UpdateEncounter:
    """Apply and commit one revision-aware encounter edit."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: UpdateEncounterCommand) -> UpdateEncounterResult:
        """Validate and commit the requested encounter changes."""
        snapshot = self._project.load()
        if snapshot.revision != command.expected_revision:
            raise RevisionConflictError(
                "The project changed after this encounter was loaded; reload before saving."
            )
        before = _known_encounter(snapshot.adventure, command.encounter_id)
        title = command.title if command.title is not None else before.title
        after = replace(
            before,
            title=title,
            summary=command.summary if command.summary is not None else before.summary,
            opening_view=(
                command.opening_view if command.opening_view is not None else before.opening_view
            ),
            content=command.content if command.content is not None else before.content,
            required=command.required if command.required is not None else before.required,
            start=command.start if command.start is not None else before.start,
            end=command.end if command.end is not None else before.end,
            tags=command.tags if command.tags is not None else before.tags,
        )
        if before == after:
            raise NoChangesRequestedError("No authoring changes were requested.")

        adventure = update_encounter(snapshot.adventure, after)
        validate_related_play_states(adventure, snapshot.related_play_states)
        report = validate_adventure(adventure)
        revision = self._project.commit_adventure(adventure, snapshot.revision)
        return UpdateEncounterResult(
            before=before,
            after=after,
            revision=revision,
            validation_report=report,
        )


class RemoveEncounter:
    """Remove one encounter with authored and journal dependency safeguards."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: RemoveEncounterCommand) -> RemoveEncounterResult:
        """Refuse dependencies by default and commit an explicit cascade atomically."""
        snapshot = self._project.load()
        if snapshot.revision != command.expected_revision:
            raise RevisionConflictError(
                "The project changed after this encounter was loaded; reload before saving."
            )
        before = _known_encounter(snapshot.adventure, command.encounter_id)
        dependencies = encounter_dependencies(snapshot.adventure, command.encounter_id)
        adventure = remove_encounter(
            snapshot.adventure,
            command.encounter_id,
            cascade=command.cascade,
        )
        validate_related_play_states(adventure, snapshot.related_play_states)
        report = validate_adventure(adventure)
        revision = self._project.commit_adventure(adventure, snapshot.revision)
        return RemoveEncounterResult(before, dependencies, revision, report)


def _encounter_detail(
    snapshot: AuthoringSnapshot,
    report: ValidationReport,
    encounter_id: str,
) -> EncounterDetail:
    adventure = snapshot.adventure
    encounter = _known_encounter(adventure, encounter_id)
    sourced_clues = tuple(
        clue for clue in adventure.clues if clue.source_encounter_id == encounter_id
    )
    supported_ids = {clue.revelation_id for clue in sourced_clues}
    supported_revelations = tuple(
        revelation for revelation in adventure.revelations if revelation.id in supported_ids
    )
    destination_ids = {
        revelation.unlocks_encounter_id
        for revelation in supported_revelations
        if revelation.unlocks_encounter_id is not None
    }
    destination_encounters = tuple(
        encounter for encounter in adventure.encounters if encounter.id in destination_ids
    )
    unlocking_revelations = tuple(
        revelation
        for revelation in adventure.revelations
        if revelation.unlocks_encounter_id == encounter_id
    )
    unlocking_ids = {revelation.id for revelation in unlocking_revelations}
    incoming_clues = tuple(clue for clue in adventure.clues if clue.revelation_id in unlocking_ids)
    reference_index = adventure.reference_index()
    linked_references = tuple(
        EncounterReferenceDetail(
            reference_id=link.reference_id,
            reference=reference_index.get(link.reference_id),
            context=link.context,
        )
        for link in encounter.reference_links
    )
    related_subject_ids = {
        encounter_id,
        *(clue.id for clue in sourced_clues),
        *(revelation.id for revelation in unlocking_revelations),
        *(link.reference_id for link in encounter.reference_links),
    }
    validation_issues = tuple(
        issue for issue in report.issues if issue.subject_id in related_subject_ids
    )
    return EncounterDetail(
        encounter=encounter,
        sourced_clues=sourced_clues,
        supported_revelations=supported_revelations,
        destination_encounters=destination_encounters,
        unlocking_revelations=unlocking_revelations,
        incoming_clues=incoming_clues,
        linked_references=linked_references,
        validation_issues=validation_issues,
        dependency_preview=preview_encounter_dependencies(snapshot, encounter_id),
    )


def _known_encounter(adventure: Adventure, encounter_id: str) -> Encounter:
    encounter = adventure.encounter_index().get(encounter_id)
    if encounter is None:
        raise EntityNotFoundError(f"Unknown encounter {encounter_id!r}.")
    return encounter
