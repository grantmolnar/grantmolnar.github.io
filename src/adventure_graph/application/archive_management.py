"""Revision-aware journal archive catalog and mutation use cases."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

from adventure_graph.application.errors import EntityNotFoundError
from adventure_graph.application.play_tracking import new_play_state, project_play_state
from adventure_graph.application.project import ProjectRevision, RevisionConflictError
from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
    Encounter,
    Revelation,
)
from adventure_graph.domain.play_events import PlayOperationVoidedEvent
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import ValidationReport

MAX_ARCHIVE_ID_LENGTH = 80
_ARCHIVE_ID_PATTERN = r"[A-Za-z0-9][A-Za-z0-9._-]*"


@dataclass(frozen=True, slots=True)
class JournalArchiveSnapshot:
    """One immutable journal archive and its authored snapshot."""

    archive_id: str
    label: str
    archived_at: str
    source_state_name: str
    adventure_snapshot: Adventure
    play_state: PlayState

    @property
    def event_count(self) -> int:
        """Return the number of raw events stored in this archive."""
        return len(self.play_state.events)


@dataclass(frozen=True, slots=True)
class JournalArchiveCatalogSnapshot:
    """Current project and archive directory loaded at one revision."""

    adventure: Adventure
    active_state: PlayState
    archives: tuple[JournalArchiveSnapshot, ...]
    source_state_name: str
    revision: ProjectRevision


class JournalArchiveProject(Protocol):
    """Application-facing port for one active journal and its archives."""

    def load(self) -> JournalArchiveCatalogSnapshot:
        """Load current state, all archives, and one aggregate revision."""
        ...

    def create_and_reset(
        self,
        archive: JournalArchiveSnapshot,
        empty_state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Create one archive and reset the active journal atomically."""
        ...

    def restore(
        self,
        archive_id: str,
        restored_state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Restore one archive without modifying the immutable archive."""
        ...

    def delete(
        self,
        archive_id: str,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Permanently remove one archive at the expected revision."""
        ...

    def import_archive(
        self,
        archive: JournalArchiveSnapshot,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Persist one validated external archive at the expected revision."""
        ...


@dataclass(frozen=True, slots=True)
class ArchiveSummary:
    """Compact archive information for catalog presentation."""

    archive_id: str
    label: str
    archived_at: str
    adventure_title: str
    event_count: int
    visit_count: int
    correction_count: int


@dataclass(frozen=True, slots=True)
class EntityComparison:
    """Identifier-level comparison for one authored entity kind."""

    added_ids: tuple[str, ...]
    removed_ids: tuple[str, ...]
    changed_ids: tuple[str, ...]

    @property
    def is_identical(self) -> bool:
        """Return whether this entity collection is unchanged."""
        return not (self.added_ids or self.removed_ids or self.changed_ids)


@dataclass(frozen=True, slots=True)
class AdventureSnapshotComparison:
    """Comparison between an archived adventure snapshot and current authorship."""

    identical: bool
    compatible: bool
    compatibility_message: str
    title_changed: bool
    synopsis_changed: bool
    premise_changed: bool
    explanation_changed: bool
    tags_changed: bool
    encounters: EntityComparison
    revelations: EntityComparison
    clues: EntityComparison


@dataclass(frozen=True, slots=True)
class ArchiveCatalogResult:
    """Archive catalog plus active-journal status and source revision."""

    adventure: Adventure
    validation_report: ValidationReport
    revision: ProjectRevision
    active_event_count: int
    archives: tuple[ArchiveSummary, ...]


@dataclass(frozen=True, slots=True)
class ArchiveDetailResult:
    """One archive, its comparison, and current restore eligibility."""

    adventure: Adventure
    validation_report: ValidationReport
    archive: JournalArchiveSnapshot
    revision: ProjectRevision
    active_event_count: int
    comparison: AdventureSnapshotComparison

    @property
    def can_restore(self) -> bool:
        """Return whether restore is currently safe and compatible."""
        return self.active_event_count == 0 and self.comparison.compatible


@dataclass(frozen=True, slots=True)
class ArchiveActiveJournalCommand:
    """Archive the active journal and replace it with an empty journal."""

    expected_revision: ProjectRevision
    label: str = ""
    name: str = ""


@dataclass(frozen=True, slots=True)
class RestoreJournalArchiveCommand:
    """Restore one archive into an empty active journal."""

    archive_id: str
    expected_revision: ProjectRevision


@dataclass(frozen=True, slots=True)
class DeleteJournalArchiveCommand:
    """Permanently delete one archive after exact identifier confirmation."""

    archive_id: str
    confirmation: str
    expected_revision: ProjectRevision


@dataclass(frozen=True, slots=True)
class ExportActiveJournalCommand:
    """Export the active journal as a portable archive without resetting it."""

    expected_revision: ProjectRevision
    label: str = ""
    name: str = ""


@dataclass(frozen=True, slots=True)
class ImportJournalArchiveCommand:
    """Import one portable journal archive into the current adventure."""

    archive: JournalArchiveSnapshot
    expected_revision: ProjectRevision


@dataclass(frozen=True, slots=True)
class ArchiveMutationResult:
    """Committed archive mutation and resulting revision."""

    archive_id: str
    event_count: int
    revision: ProjectRevision


class ListJournalArchives:
    """Query the archive catalog without exposing filesystem paths."""

    def __init__(self, project: JournalArchiveProject) -> None:
        self._project = project

    def execute(self) -> ArchiveCatalogResult:
        """Return current journal status and archive summaries."""
        snapshot = self._project.load()
        return ArchiveCatalogResult(
            adventure=snapshot.adventure,
            validation_report=validate_adventure(snapshot.adventure),
            revision=snapshot.revision,
            active_event_count=len(snapshot.active_state.events),
            archives=tuple(_archive_summary(archive) for archive in snapshot.archives),
        )


class GetJournalArchiveDetail:
    """Query one archive and compare its authored snapshot with the current project."""

    def __init__(self, project: JournalArchiveProject) -> None:
        self._project = project

    def execute(self, archive_id: str) -> ArchiveDetailResult:
        """Return one archive detail or reject an unknown identifier."""
        snapshot = self._project.load()
        archive = _archive_by_id(snapshot.archives, archive_id)
        return ArchiveDetailResult(
            adventure=snapshot.adventure,
            validation_report=validate_adventure(snapshot.adventure),
            archive=archive,
            revision=snapshot.revision,
            active_event_count=len(snapshot.active_state.events),
            comparison=compare_adventures(
                snapshot.adventure,
                archive.adventure_snapshot,
                archive.play_state,
            ),
        )


class ArchiveActiveJournal:
    """Create an immutable archive and atomically reset the active journal."""

    def __init__(
        self,
        project: JournalArchiveProject,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._project = project
        self._now = now or (lambda: datetime.now(UTC))

    def execute(self, command: ArchiveActiveJournalCommand) -> ArchiveMutationResult:
        """Validate, archive, and reset one non-empty active journal."""
        snapshot = self._project.load()
        project_play_state(snapshot.adventure, snapshot.active_state)
        if not snapshot.active_state.events:
            raise ValueError("Refusing to archive an empty play journal.")
        archived_at = self._now().astimezone(UTC).isoformat().replace("+00:00", "Z")
        archive_id = create_archive_id(
            command.name,
            command.label,
            snapshot.adventure.title,
            archived_at,
        )
        _require_available_archive_id(snapshot.archives, archive_id)
        archive = JournalArchiveSnapshot(
            archive_id=archive_id,
            label=command.label.strip(),
            archived_at=archived_at,
            source_state_name=snapshot.source_state_name,
            adventure_snapshot=snapshot.adventure,
            play_state=snapshot.active_state,
        )
        revision = self._project.create_and_reset(
            archive,
            new_play_state(snapshot.adventure),
            command.expected_revision,
        )
        return ArchiveMutationResult(archive_id, archive.event_count, revision)


class RestoreJournalArchive:
    """Restore one compatible archive into an empty active journal."""

    def __init__(self, project: JournalArchiveProject) -> None:
        self._project = project

    def execute(self, command: RestoreJournalArchiveCommand) -> ArchiveMutationResult:
        """Validate restore preconditions and retain the selected archive."""
        snapshot = self._project.load()
        project_play_state(snapshot.adventure, snapshot.active_state)
        if snapshot.active_state.events:
            raise ValueError(
                "The active play journal is not empty. Archive it before restoring another journal."
            )
        archive = _archive_by_id(snapshot.archives, command.archive_id)
        project_play_state(snapshot.adventure, archive.play_state)
        revision = self._project.restore(
            archive.archive_id,
            archive.play_state,
            command.expected_revision,
        )
        return ArchiveMutationResult(archive.archive_id, archive.event_count, revision)


class DeleteJournalArchive:
    """Permanently delete one archive after exact confirmation."""

    def __init__(self, project: JournalArchiveProject) -> None:
        self._project = project

    def execute(self, command: DeleteJournalArchiveCommand) -> ArchiveMutationResult:
        """Require an exact identifier and delete at the expected revision."""
        snapshot = self._project.load()
        project_play_state(snapshot.adventure, snapshot.active_state)
        archive = _archive_by_id(snapshot.archives, command.archive_id)
        project_play_state(archive.adventure_snapshot, archive.play_state)
        if archive.adventure_snapshot.id != snapshot.adventure.id:
            raise ValueError("The selected journal archive belongs to a different adventure.")
        if command.confirmation != archive.archive_id:
            raise ValueError(
                f"Deletion refused: confirmation must exactly match {archive.archive_id!r}."
            )
        revision = self._project.delete(archive.archive_id, command.expected_revision)
        return ArchiveMutationResult(archive.archive_id, archive.event_count, revision)


class ExportActiveJournal:
    """Build a portable archive from the active journal without mutating the project."""

    def __init__(
        self,
        project: JournalArchiveProject,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._project = project
        self._now = now or (lambda: datetime.now(UTC))

    def execute(self, command: ExportActiveJournalCommand) -> JournalArchiveSnapshot:
        """Return one validated export snapshot at the requested project revision."""
        snapshot = self._project.load()
        _require_project_revision(snapshot, command.expected_revision)
        project_play_state(snapshot.adventure, snapshot.active_state)
        if not snapshot.active_state.events:
            raise ValueError("Refusing to export an empty play journal.")
        exported_at = self._now().astimezone(UTC).isoformat().replace("+00:00", "Z")
        archive_id = create_archive_id(
            command.name,
            command.label,
            snapshot.adventure.title,
            exported_at,
        )
        return JournalArchiveSnapshot(
            archive_id=archive_id,
            label=command.label.strip(),
            archived_at=exported_at,
            source_state_name=snapshot.source_state_name,
            adventure_snapshot=snapshot.adventure,
            play_state=snapshot.active_state,
        )


class ImportJournalArchive:
    """Validate and persist one portable playthrough archive."""

    def __init__(self, project: JournalArchiveProject) -> None:
        self._project = project

    def execute(self, command: ImportJournalArchiveCommand) -> ArchiveMutationResult:
        """Import one archive that belongs to the current adventure identity."""
        snapshot = self._project.load()
        _require_project_revision(snapshot, command.expected_revision)
        archive = command.archive
        project_play_state(archive.adventure_snapshot, archive.play_state)
        if archive.adventure_snapshot.id != snapshot.adventure.id:
            raise ValueError(
                "This playthrough belongs to a different adventure and cannot be imported here."
            )
        _require_available_archive_id(snapshot.archives, archive.archive_id)
        revision = self._project.import_archive(archive, command.expected_revision)
        return ArchiveMutationResult(archive.archive_id, archive.event_count, revision)


def compare_adventures(
    current: Adventure,
    archived: Adventure,
    archived_state: PlayState,
) -> AdventureSnapshotComparison:
    """Compare authored snapshots and assess journal compatibility."""
    try:
        project_play_state(current, archived_state)
    except ValueError as error:
        compatible = False
        compatibility_message = str(error)
    else:
        compatible = True
        compatibility_message = (
            "The archived journal remains compatible with the current adventure."
            if current != archived
            else "The archived and current adventures are identical."
        )
    return AdventureSnapshotComparison(
        identical=current == archived,
        compatible=compatible,
        compatibility_message=compatibility_message,
        title_changed=current.title != archived.title,
        synopsis_changed=current.synopsis != archived.synopsis,
        premise_changed=current.premise != archived.premise,
        explanation_changed=current.explanation != archived.explanation,
        tags_changed=current.tags != archived.tags,
        encounters=_compare_entities(current.encounters, archived.encounters),
        revelations=_compare_entities(current.revelations, archived.revelations),
        clues=_compare_entities(current.clues, archived.clues),
    )


def _require_project_revision(
    snapshot: JournalArchiveCatalogSnapshot,
    expected_revision: ProjectRevision,
) -> None:
    if snapshot.revision != expected_revision:
        raise RevisionConflictError(
            "The adventure, active journal, or archive catalog changed after this page loaded; "
            "reload before modifying archives."
        )


def create_archive_id(name: str, label: str, adventure_title: str, archived_at: str) -> str:
    """Create a validated explicit identifier or a timestamped derived identifier."""
    explicit = name.strip()
    if explicit:
        return require_archive_id(explicit)
    timestamp = archived_at.replace("-", "").replace(":", "").replace(".", "")
    timestamp = timestamp.removesuffix("Z") + "Z"
    slug_source = label.strip() or adventure_title
    slug = re.sub(r"[^a-z0-9]+", "-", slug_source.lower()).strip("-")
    if slug:
        available_slug_characters = MAX_ARCHIVE_ID_LENGTH - len(timestamp) - 1
        slug = slug[:available_slug_characters].rstrip("-")
    return require_archive_id(f"{timestamp}-{slug}" if slug else timestamp)


def require_archive_id(archive_id: str) -> str:
    """Return one portable archive identifier or reject it with a bounded diagnostic."""
    if re.fullmatch(_ARCHIVE_ID_PATTERN, archive_id) is None:
        raise ValueError(
            "Archive identifiers must contain only letters, digits, periods, "
            "underscores, or hyphens and must begin with a letter or digit."
        )
    if len(archive_id) > MAX_ARCHIVE_ID_LENGTH:
        raise ValueError(f"Archive identifiers may not exceed {MAX_ARCHIVE_ID_LENGTH} characters.")
    return archive_id


def validate_archive_identity_set(archives: Sequence[JournalArchiveSnapshot]) -> None:
    """Reject an archive catalog that is ambiguous on case-insensitive filesystems."""
    identities: dict[str, str] = {}
    for archive in archives:
        archive_id = require_archive_id(archive.archive_id)
        folded = archive_id.casefold()
        prior = identities.get(folded)
        if prior is not None:
            raise ValueError(
                "Journal archive identifiers must be unique without regard to case; "
                f"{archive_id!r} conflicts with {prior!r}."
            )
        identities[folded] = archive_id


def _require_available_archive_id(
    archives: Sequence[JournalArchiveSnapshot],
    archive_id: str,
) -> None:
    validate_archive_identity_set(archives)
    require_archive_id(archive_id)
    existing = next(
        (
            archive.archive_id
            for archive in archives
            if archive.archive_id.casefold() == archive_id.casefold()
        ),
        None,
    )
    if existing is not None:
        raise ValueError(
            f"Archive {archive_id!r} is already present as {existing!r}; "
            "archive identifiers must be unique without regard to case."
        )


def _archive_summary(archive: JournalArchiveSnapshot) -> ArchiveSummary:
    visits = len(archive.play_state.visits)
    corrections = sum(
        isinstance(event, PlayOperationVoidedEvent) for event in archive.play_state.events
    )
    return ArchiveSummary(
        archive_id=archive.archive_id,
        label=archive.label,
        archived_at=archive.archived_at,
        adventure_title=archive.adventure_snapshot.title,
        event_count=archive.event_count,
        visit_count=visits,
        correction_count=corrections,
    )


def _archive_by_id(
    archives: tuple[JournalArchiveSnapshot, ...],
    archive_id: str,
) -> JournalArchiveSnapshot:
    for archive in archives:
        if archive.archive_id == archive_id:
            return archive
    raise EntityNotFoundError(f"Unknown journal archive {archive_id!r}.")


def _compare_entities(
    current: Sequence[Encounter | Revelation | Clue],
    archived: Sequence[Encounter | Revelation | Clue],
) -> EntityComparison:
    current_by_id = {str(item.id): item for item in current}
    archived_by_id = {str(item.id): item for item in archived}
    current_ids = set(current_by_id)
    archived_ids = set(archived_by_id)
    common_ids = current_ids & archived_ids
    return EntityComparison(
        added_ids=tuple(sorted(current_ids - archived_ids)),
        removed_ids=tuple(sorted(archived_ids - current_ids)),
        changed_ids=tuple(
            sorted(
                identifier
                for identifier in common_ids
                if current_by_id[identifier] != archived_by_id[identifier]
            )
        ),
    )
