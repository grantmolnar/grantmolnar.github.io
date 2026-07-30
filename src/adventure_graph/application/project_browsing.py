"""Transport-neutral queries for browsing an authored adventure."""

from __future__ import annotations

from dataclasses import dataclass

from adventure_graph.application.dependency_previews import (
    DependencyPreview,
    preview_clue_dependencies,
    preview_revelation_dependencies,
)
from adventure_graph.application.errors import EntityNotFoundError
from adventure_graph.application.project import AuthoringProject, AuthoringSnapshot, ProjectRevision
from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
    Encounter,
    Revelation,
)
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import (
    ValidationIssue,
    ValidationReport,
)


@dataclass(frozen=True, slots=True)
class AdventureOverviewResult:
    """An authored adventure, its validation report, and the loaded revision."""

    adventure: Adventure
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class RevelationDetail:
    """One revelation together with its authored support and destination."""

    revelation: Revelation
    supporting_clues: tuple[Clue, ...]
    source_encounters: tuple[Encounter, ...]
    unlocks_encounter: Encounter | None
    validation_issues: tuple[ValidationIssue, ...]
    dependency_preview: DependencyPreview


@dataclass(frozen=True, slots=True)
class RevelationDetailResult:
    """Revelation detail, complete navigation data, and loaded project metadata."""

    adventure: Adventure
    detail: RevelationDetail
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class ClueDetail:
    """One clue together with its source, supported revelation, and destination."""

    clue: Clue
    source_encounter: Encounter
    revelation: Revelation
    destination_encounter: Encounter | None
    validation_issues: tuple[ValidationIssue, ...]
    dependency_preview: DependencyPreview


@dataclass(frozen=True, slots=True)
class ClueDetailResult:
    """Clue detail, complete navigation data, and loaded project metadata."""

    adventure: Adventure
    detail: ClueDetail
    revision: ProjectRevision
    validation_report: ValidationReport


class GetAdventureOverview:
    """Load one complete read-only adventure overview."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self) -> AdventureOverviewResult:
        """Return the authored adventure and its current structural validation."""
        snapshot = self._project.load()
        return AdventureOverviewResult(
            adventure=snapshot.adventure,
            revision=snapshot.revision,
            validation_report=validate_adventure(snapshot.adventure),
        )


class GetRevelationDetail:
    """Load one revelation-oriented read model."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, revelation_id: str) -> RevelationDetailResult:
        """Return one revelation and its supporting authored relationships."""
        snapshot = self._project.load()
        report = validate_adventure(snapshot.adventure)
        return RevelationDetailResult(
            adventure=snapshot.adventure,
            detail=_revelation_detail(snapshot, report, revelation_id),
            revision=snapshot.revision,
            validation_report=report,
        )


class GetClueDetail:
    """Load one clue-oriented read model."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, clue_id: str) -> ClueDetailResult:
        """Return one clue and its direct authored relationships."""
        snapshot = self._project.load()
        report = validate_adventure(snapshot.adventure)
        return ClueDetailResult(
            adventure=snapshot.adventure,
            detail=_clue_detail(snapshot, report, clue_id),
            revision=snapshot.revision,
            validation_report=report,
        )


def _revelation_detail(
    snapshot: AuthoringSnapshot,
    report: ValidationReport,
    revelation_id: str,
) -> RevelationDetail:
    adventure = snapshot.adventure
    revelation = adventure.revelation_index().get(revelation_id)
    if revelation is None:
        raise EntityNotFoundError(f"Unknown revelation {revelation_id!r}.")
    supporting_clues = tuple(
        clue for clue in adventure.clues if clue.revelation_id == revelation_id
    )
    source_ids = {clue.source_encounter_id for clue in supporting_clues}
    source_encounters = tuple(
        encounter for encounter in adventure.encounters if encounter.id in source_ids
    )
    unlocks_encounter = (
        adventure.encounter_index().get(revelation.unlocks_encounter_id)
        if revelation.unlocks_encounter_id is not None
        else None
    )
    related_ids = {revelation_id, *(clue.id for clue in supporting_clues)}
    validation_issues = tuple(issue for issue in report.issues if issue.subject_id in related_ids)
    return RevelationDetail(
        revelation=revelation,
        supporting_clues=supporting_clues,
        source_encounters=source_encounters,
        unlocks_encounter=unlocks_encounter,
        validation_issues=validation_issues,
        dependency_preview=preview_revelation_dependencies(snapshot, revelation_id),
    )


def _clue_detail(
    snapshot: AuthoringSnapshot,
    report: ValidationReport,
    clue_id: str,
) -> ClueDetail:
    adventure = snapshot.adventure
    clue = adventure.clue_index().get(clue_id)
    if clue is None:
        raise EntityNotFoundError(f"Unknown lead {clue_id!r}.")
    source_encounter = adventure.encounter_index()[clue.source_encounter_id]
    revelation = adventure.revelation_index()[clue.revelation_id]
    destination_encounter = (
        adventure.encounter_index().get(revelation.unlocks_encounter_id)
        if revelation.unlocks_encounter_id is not None
        else None
    )
    related_ids = {clue.id, source_encounter.id, revelation.id}
    validation_issues = tuple(issue for issue in report.issues if issue.subject_id in related_ids)
    return ClueDetail(
        clue=clue,
        source_encounter=source_encounter,
        revelation=revelation,
        destination_encounter=destination_encounter,
        validation_issues=validation_issues,
        dependency_preview=preview_clue_dependencies(snapshot, clue_id),
    )
