"""Reference-library queries and revision-aware authored lifecycle operations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from adventure_graph.application.authoring import (
    ReferenceDependencies,
    add_reference,
    link_reference,
    reference_dependencies,
    remove_reference,
    unlink_reference,
    update_reference,
)
from adventure_graph.application.dependency_previews import (
    DependencyPreview,
    preview_reference_dependencies,
)
from adventure_graph.application.errors import EntityNotFoundError, NoChangesRequestedError
from adventure_graph.application.project import (
    AuthoringProject,
    AuthoringSnapshot,
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.application.project_integrity import validate_related_play_states
from adventure_graph.domain.adventure import (
    Adventure,
    Encounter,
    Reference,
    ReferenceKind,
    ReferenceLink,
)
from adventure_graph.domain.identifiers import new_reference_identifier
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import ValidationIssue, ValidationReport


@dataclass(frozen=True, slots=True)
class ReferenceBacklink:
    """One encounter that links a reference, preserving encounter and link order."""

    encounter: Encounter
    context: str


@dataclass(frozen=True, slots=True)
class ReferenceDetail:
    """One reference together with derived backlinks and removal dependencies."""

    reference: Reference
    backlinks: tuple[ReferenceBacklink, ...]
    validation_issues: tuple[ValidationIssue, ...]
    dependency_preview: DependencyPreview


@dataclass(frozen=True, slots=True)
class ReferenceDetailResult:
    """Reference detail, navigation data, validation, and project revision."""

    adventure: Adventure
    detail: ReferenceDetail
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class CreateReferenceCommand:
    """Requested reference creation based on one known project revision."""

    expected_revision: ProjectRevision
    kind: ReferenceKind
    title: str
    aliases: tuple[str, ...] = ()
    summary: str = ""
    content: str = ""
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CreateReferenceResult:
    """Committed reference creation and resulting project state."""

    reference: Reference
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class CreateAndLinkReferenceCommand:
    """Requested atomic reference creation and encounter-local linking."""

    encounter_id: str
    expected_revision: ProjectRevision
    kind: ReferenceKind
    title: str
    aliases: tuple[str, ...] = ()
    summary: str = ""
    content: str = ""
    tags: tuple[str, ...] = ()
    context: str = ""


@dataclass(frozen=True, slots=True)
class CreateAndLinkReferenceResult:
    """Committed compound reference creation and encounter-local link."""

    reference: Reference
    encounter: Encounter
    link: ReferenceLink
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class UpdateReferenceCommand:
    """Requested reference changes based on one known project revision."""

    reference_id: str
    expected_revision: ProjectRevision
    kind: ReferenceKind
    title: str
    aliases: tuple[str, ...]
    summary: str
    content: str
    tags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class UpdateReferenceResult:
    """Committed reference update and resulting project state."""

    before: Reference
    after: Reference
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class LinkReferenceCommand:
    """Requested encounter-local reference link creation."""

    encounter_id: str
    reference_id: str
    expected_revision: ProjectRevision
    context: str = ""


@dataclass(frozen=True, slots=True)
class LinkReferenceResult:
    """Committed encounter-local reference link and resulting project state."""

    encounter: Encounter
    link: ReferenceLink
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class UnlinkReferenceCommand:
    """Requested removal of one encounter/reference pair."""

    encounter_id: str
    reference_id: str
    expected_revision: ProjectRevision


@dataclass(frozen=True, slots=True)
class UnlinkReferenceResult:
    """Committed encounter-local unlink and resulting project state."""

    encounter: Encounter
    removed_link: ReferenceLink
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class RemoveReferenceCommand:
    """Requested dependency-aware reference removal."""

    reference_id: str
    expected_revision: ProjectRevision
    cascade: bool = False


@dataclass(frozen=True, slots=True)
class RemoveReferenceResult:
    """Committed reference removal and its pre-commit dependency projection."""

    reference: Reference
    dependencies: ReferenceDependencies
    revision: ProjectRevision
    validation_report: ValidationReport


class GetReferenceDetail:
    """Load one reference-oriented read model from an authored project."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, reference_id: str) -> ReferenceDetailResult:
        """Return one reference with encounter-order backlinks and dependencies."""
        snapshot = self._project.load()
        report = validate_adventure(snapshot.adventure)
        return ReferenceDetailResult(
            adventure=snapshot.adventure,
            detail=_reference_detail(snapshot, report, reference_id),
            revision=snapshot.revision,
            validation_report=report,
        )


class CreateReference:
    """Create and commit one revision-aware reference record."""

    def __init__(
        self,
        project: AuthoringProject,
        identifier_factory: Callable[[], str] = new_reference_identifier,
    ) -> None:
        self._project = project
        self._identifier_factory = identifier_factory

    def execute(self, command: CreateReferenceCommand) -> CreateReferenceResult:
        """Generate identity once, append the reference, validate, and commit."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        reference = Reference(
            id=self._identifier_factory(),
            kind=command.kind,
            title=command.title.strip(),
            aliases=command.aliases,
            summary=command.summary,
            content=command.content,
            tags=command.tags,
        )
        adventure = add_reference(snapshot.adventure, reference)
        report, revision = _commit(self._project, snapshot, adventure)
        return CreateReferenceResult(reference, revision, report)


class CreateAndLinkReference:
    """Create one reference and its first encounter link in one commit."""

    def __init__(
        self,
        project: AuthoringProject,
        identifier_factory: Callable[[], str] = new_reference_identifier,
    ) -> None:
        self._project = project
        self._identifier_factory = identifier_factory

    def execute(
        self,
        command: CreateAndLinkReferenceCommand,
    ) -> CreateAndLinkReferenceResult:
        """Generate identity once and commit the record and link atomically."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        reference = Reference(
            id=self._identifier_factory(),
            kind=command.kind,
            title=command.title.strip(),
            aliases=command.aliases,
            summary=command.summary,
            content=command.content,
            tags=command.tags,
        )
        link = ReferenceLink(reference.id, command.context)
        adventure = add_reference(snapshot.adventure, reference)
        adventure = link_reference(adventure, command.encounter_id, link)
        report, revision = _commit(self._project, snapshot, adventure)
        return CreateAndLinkReferenceResult(
            reference=reference,
            encounter=adventure.encounter_index()[command.encounter_id],
            link=link,
            revision=revision,
            validation_report=report,
        )


class UpdateReference:
    """Edit and commit one reference without changing identity or order."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: UpdateReferenceCommand) -> UpdateReferenceResult:
        """Apply complete reference fields at one expected project revision."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        before = _known_reference(snapshot.adventure, command.reference_id)
        after = replace(
            before,
            kind=command.kind,
            title=command.title.strip(),
            aliases=command.aliases,
            summary=command.summary,
            content=command.content,
            tags=command.tags,
        )
        if after == before:
            raise NoChangesRequestedError("No authoring changes were requested.")
        adventure = update_reference(snapshot.adventure, after)
        report, revision = _commit(self._project, snapshot, adventure)
        return UpdateReferenceResult(before, after, revision, report)


class LinkReference:
    """Append one contextual reference link through the canonical mutation path."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: LinkReferenceCommand) -> LinkReferenceResult:
        """Link one known reference to one known encounter at the expected revision."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        link = ReferenceLink(command.reference_id, command.context)
        adventure = link_reference(snapshot.adventure, command.encounter_id, link)
        report, revision = _commit(self._project, snapshot, adventure)
        encounter = adventure.encounter_index()[command.encounter_id]
        return LinkReferenceResult(encounter, link, revision, report)


class UnlinkReference:
    """Remove one encounter/reference pair through the canonical mutation path."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: UnlinkReferenceCommand) -> UnlinkReferenceResult:
        """Unlink a pair while preserving all remaining encounter-local order."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        encounter = snapshot.adventure.encounter_index().get(command.encounter_id)
        if encounter is None:
            raise EntityNotFoundError(f"Unknown encounter {command.encounter_id!r}.")
        removed_link = next(
            (
                link
                for link in encounter.reference_links
                if link.reference_id == command.reference_id
            ),
            None,
        )
        if removed_link is None:
            raise EntityNotFoundError(
                f"Encounter {command.encounter_id!r} does not link reference "
                f"{command.reference_id!r}."
            )
        adventure = unlink_reference(
            snapshot.adventure,
            command.encounter_id,
            command.reference_id,
        )
        report, revision = _commit(self._project, snapshot, adventure)
        return UnlinkReferenceResult(
            encounter=adventure.encounter_index()[command.encounter_id],
            removed_link=removed_link,
            revision=revision,
            validation_report=report,
        )


class RemoveReference:
    """Remove one reference with explicit cascade for encounter-owned links."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: RemoveReferenceCommand) -> RemoveReferenceResult:
        """Refuse linked removal by default and atomically cascade when requested."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        reference = _known_reference(snapshot.adventure, command.reference_id)
        dependencies = reference_dependencies(snapshot.adventure, command.reference_id)
        adventure = remove_reference(
            snapshot.adventure,
            command.reference_id,
            cascade=command.cascade,
        )
        report, revision = _commit(self._project, snapshot, adventure)
        return RemoveReferenceResult(reference, dependencies, revision, report)


def _reference_detail(
    snapshot: AuthoringSnapshot,
    report: ValidationReport,
    reference_id: str,
) -> ReferenceDetail:
    adventure = snapshot.adventure
    reference = _known_reference(adventure, reference_id)
    backlinks = tuple(
        ReferenceBacklink(encounter, link.context)
        for encounter in adventure.encounters
        for link in encounter.reference_links
        if link.reference_id == reference_id
    )
    related_encounter_ids = {backlink.encounter.id for backlink in backlinks}
    validation_issues = tuple(
        issue
        for issue in report.issues
        if issue.subject_id == reference_id
        or (issue.subject_id in related_encounter_ids and reference_id in issue.message)
    )
    return ReferenceDetail(
        reference=reference,
        backlinks=backlinks,
        validation_issues=validation_issues,
        dependency_preview=preview_reference_dependencies(snapshot, reference_id),
    )


def _known_reference(adventure: Adventure, reference_id: str) -> Reference:
    reference = adventure.reference_index().get(reference_id)
    if reference is None:
        raise EntityNotFoundError(f"Unknown reference {reference_id!r}.")
    return reference


def _require_revision(current: ProjectRevision, expected: ProjectRevision) -> None:
    if current != expected:
        raise RevisionConflictError(
            "The project changed after this reference operation was loaded; reload before saving."
        )


def _commit(
    project: AuthoringProject,
    snapshot: AuthoringSnapshot,
    adventure: Adventure,
) -> tuple[ValidationReport, ProjectRevision]:
    validate_related_play_states(adventure, snapshot.related_play_states)
    report = validate_adventure(adventure)
    revision = project.commit_adventure(adventure, snapshot.revision)
    return report, revision
