"""Tests for local project revision snapshots and legacy fingerprints."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest
from tests.support.adventures import (
    complete_four_encounter_adventure,
    reference_library_adventure,
)

import adventure_graph.infrastructure.local_journal_archives as local_journal_archives  # noqa: PLR0402 -- tests patch module-owned private seams.
from adventure_graph.application.play_tracking import (
    new_play_state,
    record_visit,
)
from adventure_graph.application.project import ProjectRevision
from adventure_graph.infrastructure.adventure_store import save_adventure
from adventure_graph.infrastructure.journal_archive_store import (
    JournalArchive,
    save_archive_and_reset,
    save_journal_archive,
)
from adventure_graph.infrastructure.local_authoring_project import LocalAuthoringProject
from adventure_graph.infrastructure.local_journal_archives import (
    LocalJournalArchiveProject,
)
from adventure_graph.infrastructure.local_play_journal import LocalPlayJournalProject
from adventure_graph.infrastructure.play_state_store import save_play_state


def _legacy_revision(sources: list[tuple[str, bytes]]) -> ProjectRevision:
    digest = hashlib.sha256()
    for label, payload in sources:
        encoded_label = label.encode("utf-8")
        digest.update(len(encoded_label).to_bytes(8, "big"))
        digest.update(encoded_label)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return ProjectRevision(digest.hexdigest())


def test_local_authoring_project_preserves_legacy_revision_fingerprint(
    tmp_path: Path,
) -> None:
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    adventure = complete_four_encounter_adventure()
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, new_play_state(adventure))

    revision = LocalAuthoringProject(adventure_path).load().revision
    expected = _legacy_revision(
        sorted(
            [
                (str(adventure_path.resolve()), adventure_path.read_bytes()),
                (str(state_path.resolve()), state_path.read_bytes()),
            ]
        )
    )

    assert revision == expected


def test_local_play_journal_preserves_missing_state_revision_fingerprint(
    tmp_path: Path,
) -> None:
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, complete_four_encounter_adventure())

    revision = LocalPlayJournalProject(adventure_path, state_path).load().revision
    expected = _legacy_revision(
        sorted(
            [
                (str(adventure_path.resolve()), adventure_path.read_bytes()),
                (str(state_path.resolve()), b"<missing-play-state>"),
            ]
        )
    )

    assert revision == expected


def test_local_archive_project_preserves_missing_source_revision_fingerprint(
    tmp_path: Path,
) -> None:
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    archive_directory = tmp_path / "archives"
    save_adventure(adventure_path, complete_four_encounter_adventure())
    project = LocalJournalArchiveProject(adventure_path, state_path, archive_directory)

    missing_directory_revision = project.load().revision
    expected_missing = _legacy_revision(
        sorted(
            [
                (str(adventure_path.resolve()), adventure_path.read_bytes()),
                (str(state_path.resolve()), b"<missing-play-state>"),
                (
                    str(archive_directory.resolve()),
                    b"<missing-archive-directory>",
                ),
            ]
        )
    )
    archive_directory.mkdir()
    empty_directory_revision = project.load().revision
    expected_empty = _legacy_revision(
        sorted(
            [
                (str(adventure_path.resolve()), adventure_path.read_bytes()),
                (str(state_path.resolve()), b"<missing-play-state>"),
            ]
        )
    )

    assert missing_directory_revision == expected_missing
    assert empty_directory_revision == expected_empty
    assert empty_directory_revision != missing_directory_revision


def test_local_archive_load_reads_each_revision_source_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    archive_directory = tmp_path / "archives"
    archive_path = archive_directory / "first-run.journal.json"
    active = record_visit(adventure, new_play_state(adventure), "alpha")
    archive = JournalArchive(
        archive_id="first-run",
        label="First run",
        archived_at="2026-07-24T18:00:00Z",
        source_state_name=state_path.name,
        adventure_snapshot=adventure,
        play_state=active,
    )
    save_adventure(adventure_path, adventure)
    save_archive_and_reset(archive_path, archive, state_path, new_play_state(adventure))
    tracked = {path.resolve(): 0 for path in (adventure_path, state_path, archive_path)}
    original_read = local_journal_archives.read_json_document_bytes

    def read_tracked(path: Path, *, recover: bool = True) -> bytes:
        resolved = path.resolve()
        if resolved in tracked:
            tracked[resolved] += 1
            if tracked[resolved] > 1:
                raise AssertionError(f"Read revision source more than once: {resolved}")
        return original_read(path, recover=recover)

    monkeypatch.setattr(
        local_journal_archives,
        "read_json_document_bytes",
        read_tracked,
    )

    snapshot = LocalJournalArchiveProject(
        adventure_path,
        state_path,
        archive_directory,
    ).load()

    assert snapshot.archives == (archive,)
    assert set(tracked.values()) == {1}


def test_local_archive_project_rejects_renamed_duplicate_identity(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    archive_directory = tmp_path / "archives"
    archive_path = archive_directory / "first-run.journal.json"
    active = record_visit(adventure, new_play_state(adventure), "alpha")
    archive = JournalArchive(
        archive_id="first-run",
        label="First run",
        archived_at="2026-07-24T18:00:00Z",
        source_state_name=state_path.name,
        adventure_snapshot=adventure,
        play_state=active,
    )
    save_adventure(adventure_path, adventure)
    save_archive_and_reset(archive_path, archive, state_path, new_play_state(adventure))
    (archive_directory / "renamed-copy.journal.json").write_bytes(archive_path.read_bytes())

    with pytest.raises(ValueError, match="does not match embedded identifier"):
        LocalJournalArchiveProject(adventure_path, state_path, archive_directory).load()


def test_local_archive_project_rejects_case_insensitive_identity_collision(
    tmp_path: Path,
) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    archive_directory = tmp_path / "archives"
    active = record_visit(adventure, new_play_state(adventure), "alpha")
    first = JournalArchive(
        archive_id="First-Run",
        label="First run",
        archived_at="2026-07-24T18:00:00Z",
        source_state_name=state_path.name,
        adventure_snapshot=adventure,
        play_state=active,
    )
    second = replace(first, archive_id="first-run", label="Second copy")
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, new_play_state(adventure))
    save_journal_archive(archive_directory / "First-Run.journal.json", first)
    save_journal_archive(archive_directory / "first-run.journal.json", second)

    with pytest.raises(ValueError, match="unique without regard to case"):
        LocalJournalArchiveProject(adventure_path, state_path, archive_directory).load()


def test_reference_and_link_changes_use_the_ordinary_project_revision(tmp_path: Path) -> None:
    adventure_path = tmp_path / "adventure.json"
    adventure = reference_library_adventure()
    project = LocalAuthoringProject(adventure_path)
    save_adventure(adventure_path, adventure)
    initial_revision = project.load().revision

    changed_reference = replace(
        adventure.references[0],
        summary="Cora now openly supports the investigators.",
    )
    reference_changed = replace(
        adventure,
        references=(changed_reference, *adventure.references[1:]),
    )
    save_adventure(adventure_path, reference_changed)
    reference_revision = project.load().revision

    first_encounter = reference_changed.encounters[0]
    changed_link = replace(
        first_encounter.reference_links[0],
        context="Cora grants access after the testimony is authenticated.",
    )
    link_changed = replace(
        reference_changed,
        encounters=(
            replace(
                first_encounter,
                reference_links=(changed_link, *first_encounter.reference_links[1:]),
            ),
            *reference_changed.encounters[1:],
        ),
    )
    save_adventure(adventure_path, link_changed)
    link_revision = project.load().revision

    assert len({initial_revision, reference_revision, link_revision}) == 3
