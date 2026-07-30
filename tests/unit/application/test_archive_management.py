"""Tests for transport-neutral journal archive management."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime

import pytest
from tests.support.adventures import complete_four_encounter_adventure

from adventure_graph.application.archive_management import (
    ArchiveActiveJournal,
    ArchiveActiveJournalCommand,
    DeleteJournalArchive,
    DeleteJournalArchiveCommand,
    ExportActiveJournal,
    ExportActiveJournalCommand,
    GetJournalArchiveDetail,
    ImportJournalArchive,
    ImportJournalArchiveCommand,
    JournalArchiveCatalogSnapshot,
    JournalArchiveSnapshot,
    ListJournalArchives,
    RestoreJournalArchive,
    RestoreJournalArchiveCommand,
    compare_adventures,
    create_archive_id,
)
from adventure_graph.application.play_tracking import (
    correct_latest_operation,
    new_play_state,
    record_visit,
)
from adventure_graph.application.project import (
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.domain.play_state import PlayState


@dataclass
class MemoryArchiveProject:
    """In-memory archive port for application tests."""

    snapshot: JournalArchiveCatalogSnapshot

    def load(self) -> JournalArchiveCatalogSnapshot:
        return self.snapshot

    def _check(self, expected: ProjectRevision) -> None:
        if expected != self.snapshot.revision:
            raise RevisionConflictError("stale")

    def create_and_reset(
        self,
        archive: JournalArchiveSnapshot,
        empty_state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        self._check(expected_revision)
        revision = ProjectRevision("revision-2")
        self.snapshot = replace(
            self.snapshot,
            active_state=empty_state,
            archives=(*self.snapshot.archives, archive),
            revision=revision,
        )
        return revision

    def restore(
        self,
        _archive_id: str,
        restored_state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        self._check(expected_revision)
        revision = ProjectRevision("revision-3")
        self.snapshot = replace(
            self.snapshot,
            active_state=restored_state,
            revision=revision,
        )
        return revision

    def delete(self, archive_id: str, expected_revision: ProjectRevision) -> ProjectRevision:
        self._check(expected_revision)
        revision = ProjectRevision("revision-4")
        self.snapshot = replace(
            self.snapshot,
            archives=tuple(a for a in self.snapshot.archives if a.archive_id != archive_id),
            revision=revision,
        )
        return revision

    def import_archive(
        self,
        archive: JournalArchiveSnapshot,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        self._check(expected_revision)
        revision = ProjectRevision("revision-5")
        self.snapshot = replace(
            self.snapshot,
            archives=(*self.snapshot.archives, archive),
            revision=revision,
        )
        return revision


def _project(*, active: bool = True) -> MemoryArchiveProject:
    adventure = complete_four_encounter_adventure()
    state = new_play_state(adventure)
    if active:
        state = record_visit(adventure, state, "alpha")
    return MemoryArchiveProject(
        JournalArchiveCatalogSnapshot(
            adventure, state, (), "play-state.json", ProjectRevision("revision-1")
        )
    )


def test_archive_active_journal_resets_state_and_catalog_lists_summary() -> None:
    project = _project()
    result = ArchiveActiveJournal(
        project,
        now=lambda: datetime(2026, 7, 13, 15, 30, tzinfo=UTC),
    ).execute(
        ArchiveActiveJournalCommand(
            expected_revision=ProjectRevision("revision-1"),
            label="Session One",
        )
    )

    assert result.archive_id == "20260713T153000Z-session-one"
    assert result.event_count == 1
    assert not project.snapshot.active_state.events
    catalog = ListJournalArchives(project).execute()
    assert catalog.archives[0].visit_count == 1
    assert catalog.archives[0].label == "Session One"


def test_archive_active_journal_rejects_case_insensitive_catalog_collision() -> None:
    project = _project()
    adventure = project.snapshot.adventure
    existing = JournalArchiveSnapshot(
        "Session-One",
        "",
        "2026-07-13T14:30:00Z",
        "play-state.json",
        adventure,
        record_visit(adventure, new_play_state(adventure), "alpha"),
    )
    project.snapshot = replace(project.snapshot, archives=(existing,))
    before = project.snapshot

    with pytest.raises(ValueError, match="unique without regard to case"):
        ArchiveActiveJournal(
            project,
            now=lambda: datetime(2026, 7, 13, 15, 30, tzinfo=UTC),
        ).execute(
            ArchiveActiveJournalCommand(
                expected_revision=project.snapshot.revision,
                name="session-one",
            )
        )

    assert project.snapshot == before


def test_archive_identifiers_are_bounded_and_derived_names_are_truncated() -> None:
    with pytest.raises(ValueError, match="80 characters"):
        create_archive_id("x" * 81, "", "Adventure", "2026-07-13T15:30:00Z")

    derived = create_archive_id(
        "",
        "A very long archive label " * 20,
        "Adventure",
        "2026-07-13T15:30:00Z",
    )

    assert len(derived) == 80
    assert derived.startswith("20260713T153000Z-")
    assert not derived.endswith("-")


def test_export_active_journal_builds_archive_without_mutating_project() -> None:
    project = _project()
    before = project.snapshot

    archive = ExportActiveJournal(
        project,
        now=lambda: datetime(2026, 7, 13, 15, 30, tzinfo=UTC),
    ).execute(
        ExportActiveJournalCommand(
            expected_revision=ProjectRevision("revision-1"),
            label="Session One",
            name="session-one",
        )
    )

    assert archive.archive_id == "session-one"
    assert archive.label == "Session One"
    assert archive.play_state == before.active_state
    assert archive.adventure_snapshot == before.adventure
    assert project.snapshot == before


def test_import_playthrough_preserves_archive_and_requires_matching_adventure() -> None:
    project = _project(active=False)
    adventure = project.snapshot.adventure
    archive = JournalArchiveSnapshot(
        "session-one",
        "Session One",
        "2026-07-13T15:30:00Z",
        "play-state.json",
        adventure,
        record_visit(adventure, new_play_state(adventure), "alpha"),
    )

    result = ImportJournalArchive(project).execute(
        ImportJournalArchiveCommand(archive, project.snapshot.revision)
    )

    assert result.archive_id == "session-one"
    assert project.snapshot.archives == (archive,)

    foreign_adventure = replace(adventure, id="different-adventure")
    foreign = replace(
        archive,
        archive_id="foreign",
        adventure_snapshot=foreign_adventure,
        play_state=record_visit(
            foreign_adventure,
            new_play_state(foreign_adventure),
            "alpha",
        ),
    )
    with pytest.raises(ValueError, match="different adventure"):
        ImportJournalArchive(project).execute(
            ImportJournalArchiveCommand(foreign, project.snapshot.revision)
        )


def test_import_playthrough_rejects_case_insensitive_archive_collision() -> None:
    project = _project(active=False)
    adventure = project.snapshot.adventure
    existing = JournalArchiveSnapshot(
        "Session-One",
        "",
        "2026-07-13T15:30:00Z",
        "play-state.json",
        adventure,
        record_visit(adventure, new_play_state(adventure), "alpha"),
    )
    project.snapshot = replace(project.snapshot, archives=(existing,))
    duplicate = replace(existing, archive_id="session-one")

    with pytest.raises(ValueError, match="already present"):
        ImportJournalArchive(project).execute(
            ImportJournalArchiveCommand(duplicate, project.snapshot.revision)
        )


def test_archive_catalog_counts_only_active_visits_after_correction() -> None:
    project = _project(active=False)
    adventure = project.snapshot.adventure
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    state = correct_latest_operation(adventure, state, "Recorded against the wrong encounter.")
    archive = JournalArchiveSnapshot(
        "corrected-archive",
        "Corrected session",
        "2026-07-13T15:30:00Z",
        "play-state.json",
        adventure,
        state,
    )
    project.snapshot = replace(project.snapshot, archives=(archive,))

    catalog = ListJournalArchives(project).execute()
    detail = GetJournalArchiveDetail(project).execute(archive.archive_id)

    assert catalog.archives[0].event_count == 2
    assert catalog.archives[0].correction_count == 1
    assert catalog.archives[0].visit_count == 0
    assert len(detail.archive.play_state.visits) == 0


def test_archive_detail_compares_snapshot_and_restore_retains_archive() -> None:
    project = _project()
    archive_result = ArchiveActiveJournal(
        project,
        now=lambda: datetime(2026, 7, 13, 15, 30, tzinfo=UTC),
    ).execute(ArchiveActiveJournalCommand(ProjectRevision("revision-1")))
    archive = project.snapshot.archives[0]
    project.snapshot = replace(
        project.snapshot,
        adventure=replace(project.snapshot.adventure, title="Revised title"),
    )

    detail = GetJournalArchiveDetail(project).execute(archive.archive_id)

    assert not detail.comparison.identical
    assert detail.comparison.compatible
    assert detail.comparison.title_changed
    assert detail.can_restore

    restored = RestoreJournalArchive(project).execute(
        RestoreJournalArchiveCommand(archive.archive_id, archive_result.revision)
    )
    assert restored.event_count == 1
    assert project.snapshot.active_state.events
    assert project.snapshot.archives == (archive,)
    retained_detail = GetJournalArchiveDetail(project).execute(archive.archive_id)
    assert retained_detail.archive.adventure_snapshot == archive.adventure_snapshot
    assert retained_detail.archive.play_state == archive.play_state


def test_restore_requires_empty_state_and_delete_requires_exact_confirmation() -> None:
    project = _project(active=False)
    adventure = project.snapshot.adventure
    archive = JournalArchiveSnapshot(
        "archive-one",
        "",
        "2026-07-13T15:30:00Z",
        "play-state.json",
        adventure,
        record_visit(adventure, new_play_state(adventure), "alpha"),
    )
    project.snapshot = replace(project.snapshot, archives=(archive,))

    with pytest.raises(ValueError, match="exactly match"):
        DeleteJournalArchive(project).execute(
            DeleteJournalArchiveCommand(
                archive.archive_id,
                "wrong",
                project.snapshot.revision,
            )
        )

    deleted = DeleteJournalArchive(project).execute(
        DeleteJournalArchiveCommand(
            archive.archive_id,
            archive.archive_id,
            project.snapshot.revision,
        )
    )
    assert deleted.archive_id == archive.archive_id


def test_restore_archive_refuses_to_overwrite_an_active_journal() -> None:
    project = _project(active=True)
    adventure = project.snapshot.adventure
    archive = JournalArchiveSnapshot(
        "archive-one",
        "",
        "2026-07-13T15:30:00Z",
        "play-state.json",
        adventure,
        record_visit(adventure, new_play_state(adventure), "alpha"),
    )
    project.snapshot = replace(project.snapshot, archives=(archive,))
    before = project.snapshot

    with pytest.raises(ValueError, match="active play journal is not empty"):
        RestoreJournalArchive(project).execute(
            RestoreJournalArchiveCommand(
                archive.archive_id,
                project.snapshot.revision,
            )
        )

    assert project.snapshot == before


def test_restore_archive_rejects_a_stale_revision_without_mutation() -> None:
    project = _project(active=False)
    adventure = project.snapshot.adventure
    archive = JournalArchiveSnapshot(
        "archive-one",
        "",
        "2026-07-13T15:30:00Z",
        "play-state.json",
        adventure,
        record_visit(adventure, new_play_state(adventure), "alpha"),
    )
    project.snapshot = replace(project.snapshot, archives=(archive,))
    before = project.snapshot

    with pytest.raises(RevisionConflictError, match="stale"):
        RestoreJournalArchive(project).execute(
            RestoreJournalArchiveCommand(
                archive.archive_id,
                ProjectRevision("obsolete"),
            )
        )

    assert project.snapshot == before


def test_restore_archive_rejects_an_unknown_identity_without_mutation() -> None:
    project = _project(active=False)
    before = project.snapshot

    with pytest.raises(ValueError, match="Unknown journal archive"):
        RestoreJournalArchive(project).execute(
            RestoreJournalArchiveCommand(
                "missing-archive",
                project.snapshot.revision,
            )
        )

    assert project.snapshot == before


def test_restore_archive_rejects_an_archive_from_another_adventure() -> None:
    project = _project(active=False)
    other_adventure = replace(project.snapshot.adventure, id="other-adventure")
    archive = JournalArchiveSnapshot(
        "foreign-archive",
        "",
        "2026-07-13T15:30:00Z",
        "play-state.json",
        other_adventure,
        new_play_state(other_adventure),
    )
    project.snapshot = replace(project.snapshot, archives=(archive,))
    before = project.snapshot

    with pytest.raises(ValueError, match="Play state belongs to"):
        RestoreJournalArchive(project).execute(
            RestoreJournalArchiveCommand(
                archive.archive_id,
                project.snapshot.revision,
            )
        )

    assert project.snapshot == before


def test_delete_archive_rejects_a_stale_revision_without_mutation() -> None:
    project = _project(active=False)
    adventure = project.snapshot.adventure
    archive = JournalArchiveSnapshot(
        "archive-one",
        "",
        "2026-07-13T15:30:00Z",
        "play-state.json",
        adventure,
        record_visit(adventure, new_play_state(adventure), "alpha"),
    )
    project.snapshot = replace(project.snapshot, archives=(archive,))
    before = project.snapshot

    with pytest.raises(RevisionConflictError, match="stale"):
        DeleteJournalArchive(project).execute(
            DeleteJournalArchiveCommand(
                archive.archive_id,
                archive.archive_id,
                ProjectRevision("obsolete"),
            )
        )

    assert project.snapshot == before


def test_delete_archive_rejects_an_archive_from_another_adventure() -> None:
    project = _project(active=False)
    other_adventure = replace(project.snapshot.adventure, id="other-adventure")
    archive = JournalArchiveSnapshot(
        "foreign-archive",
        "",
        "2026-07-13T15:30:00Z",
        "play-state.json",
        other_adventure,
        new_play_state(other_adventure),
    )
    project.snapshot = replace(project.snapshot, archives=(archive,))

    with pytest.raises(ValueError, match="different adventure"):
        DeleteJournalArchive(project).execute(
            DeleteJournalArchiveCommand(
                archive.archive_id,
                archive.archive_id,
                project.snapshot.revision,
            )
        )

    assert project.snapshot.archives == (archive,)


def test_compare_marks_removed_referenced_encounter_incompatible() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    current = replace(
        adventure,
        encounters=tuple(
            encounter for encounter in adventure.encounters if encounter.id != "alpha"
        ),
    )

    comparison = compare_adventures(current, adventure, state)

    assert not comparison.compatible
    assert comparison.encounters.removed_ids == ("alpha",)
