"""Workspace-level orchestration for portable playthrough transfer."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from adventure_graph.application.archive_management import (
    ImportJournalArchive,
    ImportJournalArchiveCommand,
    JournalArchiveProject,
    JournalArchiveSnapshot,
)
from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.workspace_management import (
    AdventureCatalogEntry,
    AdventureWorkspace,
    WorkspaceRevision,
    WorkspaceRevisionConflictError,
)


@dataclass(frozen=True, slots=True)
class ImportWorkspacePlaythroughCommand:
    """Import one portable playthrough by its embedded adventure identity."""

    archive: JournalArchiveSnapshot
    expected_revision: WorkspaceRevision


@dataclass(frozen=True, slots=True)
class ImportWorkspacePlaythroughResult:
    """Imported archive identity and the adventure catalog entry that received it."""

    adventure: AdventureCatalogEntry
    archive_id: str
    event_count: int
    project_revision: ProjectRevision


class ImportWorkspacePlaythrough:
    """Resolve and import a playthrough without changing workspace selection."""

    def __init__(
        self,
        workspace: AdventureWorkspace,
        archive_project_for_key: Callable[[str], JournalArchiveProject],
    ) -> None:
        self._workspace = workspace
        self._archive_project_for_key = archive_project_for_key

    def execute(
        self,
        command: ImportWorkspacePlaythroughCommand,
    ) -> ImportWorkspacePlaythroughResult:
        """Import into the unique project matching the archive's stable identity."""
        workspace_snapshot = self._workspace.load()
        if workspace_snapshot.revision != command.expected_revision:
            raise WorkspaceRevisionConflictError(
                "The adventure catalog changed after this page was loaded; reload before importing."
            )

        adventure_id = command.archive.adventure_snapshot.id
        matches = [
            entry for entry in workspace_snapshot.adventures if entry.adventure_id == adventure_id
        ]
        if not matches:
            raise ValueError(
                "No adventure in this workspace matches the adventure identity carried by this "
                "playthrough. Import the matching adventure first."
            )
        if len(matches) > 1:
            raise ValueError(
                "More than one adventure in this workspace has the identity carried by this "
                "playthrough. Remove or repair the duplicate projects before importing."
            )

        adventure = matches[0]
        project = self._archive_project_for_key(adventure.key)
        project_snapshot = project.load()
        mutation = ImportJournalArchive(project).execute(
            ImportJournalArchiveCommand(command.archive, project_snapshot.revision)
        )
        return ImportWorkspacePlaythroughResult(
            adventure=adventure,
            archive_id=mutation.archive_id,
            event_count=mutation.event_count,
            project_revision=mutation.revision,
        )
