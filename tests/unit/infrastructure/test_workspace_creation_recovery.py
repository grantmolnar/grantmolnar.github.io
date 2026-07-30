"""Recovery tests for interrupted multi-file workspace project creation."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.support.adventures import complete_four_encounter_adventure

import adventure_graph.infrastructure.local_adventure_workspace as workspace_module
from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.application.workspace_management import WorkspaceSettings
from adventure_graph.infrastructure.adventure_store import save_adventure
from adventure_graph.infrastructure.atomic_files import write_json_object
from adventure_graph.infrastructure.local_adventure_workspace import LocalAdventureWorkspace
from adventure_graph.infrastructure.play_state_store import save_play_state

_CREATION_FILE = ".adventure-graph-project-creation.json"


def test_workspace_load_discards_an_interrupted_uncommitted_project(tmp_path: Path) -> None:
    project = tmp_path / "unfinished"
    marker = project / _CREATION_FILE
    write_json_object(marker, {"schema_version": 1, "state": "creating"})

    snapshot = LocalAdventureWorkspace(tmp_path).load()

    assert snapshot.adventures == ()
    assert not project.exists()


def test_workspace_load_finishes_a_committed_project_after_process_termination(
    tmp_path: Path,
) -> None:
    project = tmp_path / "committed"
    adventure = complete_four_encounter_adventure()
    save_adventure(project / "adventure.json", adventure)
    save_play_state(project / "play-state.json", new_play_state(adventure))
    write_json_object(
        project / _CREATION_FILE,
        {"schema_version": 1, "state": "committed"},
    )

    snapshot = LocalAdventureWorkspace(tmp_path).load()

    assert [entry.title for entry in snapshot.adventures] == [adventure.title]
    assert (project / "generated").is_dir()
    assert (project / "archives").is_dir()
    assert not (project / _CREATION_FILE).exists()


def test_workspace_recovery_refuses_to_delete_unexpected_user_files(tmp_path: Path) -> None:
    project = tmp_path / "unfinished"
    write_json_object(
        project / _CREATION_FILE,
        {"schema_version": 1, "state": "creating"},
    )
    note = project / "keep-me.txt"
    note.write_text("user data", encoding="utf-8")

    with pytest.raises(ValueError, match=r"contains unexpected files: keep-me\.txt"):
        LocalAdventureWorkspace(tmp_path).load()

    assert note.read_text(encoding="utf-8") == "user data"
    assert (project / _CREATION_FILE).exists()


def test_create_project_removes_its_creation_directory_when_transaction_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace = LocalAdventureWorkspace(tmp_path)
    adventure = complete_four_encounter_adventure()
    snapshot = workspace.load()

    def fail_transaction(payloads: object) -> None:
        raise OSError("simulated coordinated write failure")

    monkeypatch.setattr(workspace_module, "write_json_objects", fail_transaction)

    with pytest.raises(OSError, match="coordinated write failure"):
        workspace.create_project(
            "failed-project",
            adventure,
            new_play_state(adventure),
            WorkspaceSettings("failed-project/adventure.json"),
            snapshot.revision,
        )

    assert not (tmp_path / "failed-project").exists()
