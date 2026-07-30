"""Tests for workspace-level portable playthrough routing."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest
from tests.support.adventures import complete_four_encounter_adventure

from adventure_graph.application.archive_management import (
    JournalArchiveCatalogSnapshot,
    JournalArchiveSnapshot,
)
from adventure_graph.application.play_tracking import new_play_state, record_visit
from adventure_graph.application.project import ProjectRevision, RevisionConflictError
from adventure_graph.application.workspace_management import (
    AdventureCatalogEntry,
    WorkspaceRevision,
    WorkspaceRevisionConflictError,
    WorkspaceSettings,
    WorkspaceSnapshot,
)
from adventure_graph.application.workspace_transfer import (
    ImportWorkspacePlaythrough,
    ImportWorkspacePlaythroughCommand,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState


@dataclass
class MemoryWorkspace:
    """Read-only workspace port used to test transfer orchestration."""

    snapshot: WorkspaceSnapshot

    def load(self) -> WorkspaceSnapshot:
        return self.snapshot


@dataclass
class MemoryArchiveProject:
    """In-memory archive project retaining the active journal during imports."""

    snapshot: JournalArchiveCatalogSnapshot

    def load(self) -> JournalArchiveCatalogSnapshot:
        return self.snapshot

    def create_and_reset(
        self,
        _archive: JournalArchiveSnapshot,
        _empty_state: PlayState,
        _expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        raise AssertionError("Workspace import must not archive or reset the active journal.")

    def restore(
        self,
        _archive_id: str,
        _restored_state: PlayState,
        _expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        raise AssertionError("Workspace import must not restore the active journal.")

    def delete(
        self,
        _archive_id: str,
        _expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        raise AssertionError("Workspace import must not delete an archive.")

    def import_archive(
        self,
        archive: JournalArchiveSnapshot,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        if expected_revision != self.snapshot.revision:
            raise RevisionConflictError("stale")
        revision = ProjectRevision("project-revision-2")
        self.snapshot = replace(
            self.snapshot,
            archives=(*self.snapshot.archives, archive),
            revision=revision,
        )
        return revision


def _archive(adventure: Adventure) -> JournalArchiveSnapshot:
    return JournalArchiveSnapshot(
        archive_id="session-one",
        label="Session One",
        archived_at="2026-07-27T18:00:00Z",
        source_state_name="play-state.json",
        adventure_snapshot=adventure,
        play_state=record_visit(adventure, new_play_state(adventure), "alpha"),
    )


def _workspace(
    entries: tuple[AdventureCatalogEntry, ...],
    *,
    selected: str | None = "beta/adventure.json",
) -> MemoryWorkspace:
    return MemoryWorkspace(
        WorkspaceSnapshot(
            adventures=entries,
            settings=WorkspaceSettings(selected_adventure_key=selected),
            revision=WorkspaceRevision("workspace-revision-1"),
        )
    )


def _project(adventure: Adventure) -> MemoryArchiveProject:
    active_state = record_visit(adventure, new_play_state(adventure), "alpha")
    return MemoryArchiveProject(
        JournalArchiveCatalogSnapshot(
            adventure=adventure,
            active_state=active_state,
            archives=(),
            source_state_name="play-state.json",
            revision=ProjectRevision("project-revision-1"),
        )
    )


def test_workspace_import_routes_by_identity_without_changing_selection_or_active_state() -> None:
    adventure = complete_four_encounter_adventure()
    entries = (
        AdventureCatalogEntry(
            "alpha/adventure.json",
            "Matching Adventure",
            "",
            adventure_id=adventure.id,
        ),
        AdventureCatalogEntry(
            "beta/adventure.json",
            "Selected Adventure",
            "",
            adventure_id="other-adventure",
        ),
    )
    workspace = _workspace(entries)
    project = _project(adventure)
    active_state = project.snapshot.active_state
    opened_keys: list[str] = []

    def project_for_key(key: str) -> MemoryArchiveProject:
        opened_keys.append(key)
        return project

    result = ImportWorkspacePlaythrough(workspace, project_for_key).execute(
        ImportWorkspacePlaythroughCommand(
            _archive(adventure),
            WorkspaceRevision("workspace-revision-1"),
        )
    )

    assert opened_keys == ["alpha/adventure.json"]
    assert result.adventure == entries[0]
    assert result.archive_id == "session-one"
    assert result.event_count == 1
    assert result.project_revision == ProjectRevision("project-revision-2")
    assert project.snapshot.archives[0].archive_id == "session-one"
    assert project.snapshot.active_state == active_state
    assert workspace.snapshot.settings.selected_adventure_key == "beta/adventure.json"


def test_workspace_import_rejects_stale_catalog_before_opening_a_project() -> None:
    adventure = complete_four_encounter_adventure()
    workspace = _workspace(
        (
            AdventureCatalogEntry(
                "alpha/adventure.json",
                "Matching Adventure",
                "",
                adventure_id=adventure.id,
            ),
        )
    )

    with pytest.raises(WorkspaceRevisionConflictError, match="catalog changed"):
        ImportWorkspacePlaythrough(
            workspace,
            lambda _key: (_ for _ in ()).throw(AssertionError("project opened")),
        ).execute(
            ImportWorkspacePlaythroughCommand(
                _archive(adventure),
                WorkspaceRevision("stale-revision"),
            )
        )


def test_workspace_import_rejects_missing_identity_without_opening_a_project() -> None:
    adventure = complete_four_encounter_adventure()
    workspace = _workspace(
        (
            AdventureCatalogEntry(
                "beta/adventure.json",
                "Other Adventure",
                "",
                adventure_id="other-adventure",
            ),
        )
    )

    with pytest.raises(ValueError, match="Import the matching adventure first"):
        ImportWorkspacePlaythrough(
            workspace,
            lambda _key: (_ for _ in ()).throw(AssertionError("project opened")),
        ).execute(
            ImportWorkspacePlaythroughCommand(
                _archive(adventure),
                WorkspaceRevision("workspace-revision-1"),
            )
        )


def test_workspace_import_rejects_ambiguous_identity_without_opening_a_project() -> None:
    adventure = complete_four_encounter_adventure()
    entries = tuple(
        AdventureCatalogEntry(
            f"copy-{index}/adventure.json",
            f"Copy {index}",
            "",
            adventure_id=adventure.id,
        )
        for index in (1, 2)
    )
    workspace = _workspace(entries)

    with pytest.raises(ValueError, match="duplicate projects"):
        ImportWorkspacePlaythrough(
            workspace,
            lambda _key: (_ for _ in ()).throw(AssertionError("project opened")),
        ).execute(
            ImportWorkspacePlaythroughCommand(
                _archive(adventure),
                WorkspaceRevision("workspace-revision-1"),
            )
        )


def test_workspace_import_preserves_project_level_duplicate_checks() -> None:
    adventure = complete_four_encounter_adventure()
    archive = _archive(adventure)
    entry = AdventureCatalogEntry(
        "alpha/adventure.json",
        "Matching Adventure",
        "",
        adventure_id=adventure.id,
    )
    workspace = _workspace((entry,))
    project = _project(adventure)
    project.snapshot = replace(project.snapshot, archives=(archive,))

    with pytest.raises(ValueError, match="already present"):
        ImportWorkspacePlaythrough(workspace, lambda _key: project).execute(
            ImportWorkspacePlaythroughCommand(
                archive,
                WorkspaceRevision("workspace-revision-1"),
            )
        )

    assert project.snapshot.archives == (archive,)


def test_workspace_import_rechecks_identity_against_the_opened_project() -> None:
    archive_adventure = complete_four_encounter_adventure()
    entry = AdventureCatalogEntry(
        "alpha/adventure.json",
        "Catalog Entry",
        "",
        adventure_id=archive_adventure.id,
    )
    workspace = _workspace((entry,))
    different_adventure = replace(archive_adventure, id="different-adventure")
    project = _project(different_adventure)

    with pytest.raises(ValueError, match="different adventure"):
        ImportWorkspacePlaythrough(workspace, lambda _key: project).execute(
            ImportWorkspacePlaythroughCommand(
                _archive(archive_adventure),
                WorkspaceRevision("workspace-revision-1"),
            )
        )

    assert project.snapshot.archives == ()
