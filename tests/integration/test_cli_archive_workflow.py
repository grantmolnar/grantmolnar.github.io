"""Integration coverage for the journal-archive CLI lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest

from adventure_graph.bootstrap import main
from adventure_graph.infrastructure.play_state_store import load_play_state


def test_cli_archives_lists_and_restores_a_play_journal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "journal-lifecycle"
    assert main(["init", str(project)]) == 0
    adventure = project / "adventure.json"
    state = project / "play-state.json"
    archives = project / "archives"
    assert main(["visit", str(adventure), str(state), "the-shattered-gallery"]) == 0
    before = load_play_state(state)

    assert (
        main(
            [
                "archive",
                str(adventure),
                str(state),
                "--name",
                "gallery-opening",
                "--label",
                "Gallery opening",
            ]
        )
        == 0
    )
    archive_path = archives / "gallery-opening.journal.json"
    assert archive_path.is_file()
    assert load_play_state(state).events == ()
    assert main(["list-archives", str(archives)]) == 0
    archive_payload = archive_path.read_bytes()

    assert main(["restore-archive", str(adventure), str(state), str(archive_path)]) == 0

    assert load_play_state(state) == before
    assert archive_path.read_bytes() == archive_payload
    output = capsys.readouterr().out
    assert "Archived 1 event(s) as gallery-opening" in output
    assert "Journal archives (1):" in output
    assert "Gallery opening" in output
    assert "Restored archive gallery-opening" in output
    assert "retained" in output


def test_cli_restore_archive_refuses_to_overwrite_nonempty_active_journal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "occupied-journal"
    assert main(["init", str(project)]) == 0
    adventure = project / "adventure.json"
    state = project / "play-state.json"
    assert main(["visit", str(adventure), str(state), "the-shattered-gallery"]) == 0
    assert main(["archive", str(adventure), str(state), "--name", "first"]) == 0
    archive_path = project / "archives" / "first.journal.json"
    assert main(["visit", str(adventure), str(state), "the-shattered-gallery"]) == 0
    active_before = state.read_bytes()

    assert main(["restore-archive", str(adventure), str(state), str(archive_path)]) == 2

    assert state.read_bytes() == active_before
    assert archive_path.exists()
    assert "active play journal is not empty" in capsys.readouterr().err


def test_cli_delete_archive_requires_exact_identifier_confirmation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "archive-deletion"
    assert main(["init", str(project)]) == 0
    adventure = project / "adventure.json"
    state = project / "play-state.json"
    assert main(["visit", str(adventure), str(state), "the-shattered-gallery"]) == 0
    assert main(["archive", str(adventure), str(state), "--name", "disposable"]) == 0
    archive_path = project / "archives" / "disposable.journal.json"

    assert (
        main(
            [
                "delete-archive",
                str(adventure),
                str(state),
                str(archive_path),
                "--confirm",
                "DELETE",
            ]
        )
        == 2
    )
    assert archive_path.exists()
    assert (
        main(
            [
                "delete-archive",
                str(adventure),
                str(state),
                str(archive_path),
                "--confirm",
                "disposable",
            ]
        )
        == 0
    )
    assert not archive_path.exists()

    captured = capsys.readouterr()
    assert "confirmation must exactly match 'disposable'" in captured.err
    assert "Deleted journal archive disposable" in captured.out


def test_cli_refuses_to_archive_an_empty_journal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "empty-archive"
    assert main(["init", str(project)]) == 0

    assert (
        main(
            [
                "archive",
                str(project / "adventure.json"),
                str(project / "play-state.json"),
                "--name",
                "empty",
            ]
        )
        == 2
    )
    assert "Refusing to archive an empty play journal" in capsys.readouterr().err


def test_cli_rejects_a_renamed_archive_with_ambiguous_identity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "renamed-archive"
    assert main(["init", str(project)]) == 0
    adventure = project / "adventure.json"
    state = project / "play-state.json"
    archives = project / "archives"
    assert main(["visit", str(adventure), str(state), "the-shattered-gallery"]) == 0
    assert main(["archive", str(adventure), str(state), "--name", "canonical"]) == 0
    canonical = archives / "canonical.journal.json"
    renamed = archives / "renamed-copy.journal.json"
    renamed.write_bytes(canonical.read_bytes())

    assert main(["list-archives", str(archives)]) == 2
    assert main(["restore-archive", str(adventure), str(state), str(renamed)]) == 2

    captured = capsys.readouterr()
    assert "does not match embedded identifier" in captured.err
    assert canonical.is_file()
    assert renamed.is_file()


def test_cli_list_archives_rejects_a_file_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    archive_file = tmp_path / "not-a-directory.journal.json"
    archive_file.write_text("{}", encoding="utf-8")

    assert main(["list-archives", str(archive_file)]) == 2

    assert "Archive path is not a directory" in capsys.readouterr().err
