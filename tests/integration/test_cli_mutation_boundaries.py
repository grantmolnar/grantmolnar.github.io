"""Integration coverage for revision-aware CLI mutation boundaries."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.bootstrap import main
from adventure_graph.infrastructure.adventure_store import load_adventure, save_adventure
from adventure_graph.infrastructure.play_state_store import save_play_state


def _make_distinct_project(project: Path, adventure_id: str) -> tuple[Path, Path]:
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    state_path = project / "play-state.json"
    adventure = replace(load_adventure(adventure_path), id=adventure_id)
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, new_play_state(adventure))
    return adventure_path, state_path


def test_cli_note_rejects_a_wrong_adventure_journal_pairing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first_adventure, first_state = _make_distinct_project(
        tmp_path / "first-project", "first-adventure"
    )
    second_adventure, _second_state = _make_distinct_project(
        tmp_path / "second-project", "second-adventure"
    )
    assert main(["visit", str(first_adventure), str(first_state), "the-shattered-gallery"]) == 0
    before = first_state.read_bytes()

    assert (
        main(
            [
                "note",
                str(second_adventure),
                str(first_state),
                "1",
                "This must not be committed.",
            ]
        )
        == 2
    )

    assert first_state.read_bytes() == before
    assert "Play state belongs to" in capsys.readouterr().err


def test_cli_delete_archive_rejects_an_archive_from_another_adventure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    first_adventure, first_state = _make_distinct_project(
        tmp_path / "first-project", "first-adventure"
    )
    second_adventure, second_state = _make_distinct_project(
        tmp_path / "second-project", "second-adventure"
    )
    assert main(["visit", str(first_adventure), str(first_state), "the-shattered-gallery"]) == 0
    assert main(["archive", str(first_adventure), str(first_state), "--name", "foreign"]) == 0
    archive_path = tmp_path / "first-project" / "archives" / "foreign.journal.json"

    assert (
        main(
            [
                "delete-archive",
                str(second_adventure),
                str(second_state),
                str(archive_path),
                "--confirm",
                "foreign",
            ]
        )
        == 2
    )

    assert archive_path.exists()
    assert "belongs to a different adventure" in capsys.readouterr().err
