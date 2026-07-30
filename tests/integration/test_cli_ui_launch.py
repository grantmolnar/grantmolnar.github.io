"""Integration coverage for CLI local-UI launch target semantics."""

from __future__ import annotations

from pathlib import Path

import pytest

from adventure_graph.bootstrap import main
from adventure_graph.infrastructure.local_adventure_workspace import (
    LocalAdventureWorkspace,
)
from adventure_graph.interfaces.web.workspace_app import WorkspaceWebApplication


def test_cli_ui_accepts_a_project_directory_as_the_initial_selection(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project-directory-ui"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    captured: dict[str, object] = {}

    class RecordingWorkspace(LocalAdventureWorkspace):
        def select_initial_adventure(self, path: Path) -> None:
            captured["initial_selection"] = path
            super().select_initial_adventure(path)

    def open_workspace(root: Path) -> LocalAdventureWorkspace:
        captured["workspace_root"] = root
        return RecordingWorkspace(root)

    def fake_serve(
        app: object,
        *,
        host: str,
        port: int,
        open_browser: bool,
    ) -> None:
        assert isinstance(app, WorkspaceWebApplication)
        workspace = app.queries.get_workspace()
        assert workspace.selected_adventure is not None
        captured["selected_title"] = workspace.selected_adventure.title
        captured["host"] = host
        captured["port"] = port
        captured["open_browser"] = open_browser

    monkeypatch.setattr("adventure_graph.bootstrap.LocalAdventureWorkspace", open_workspace)
    monkeypatch.setattr("adventure_graph.bootstrap.serve_web_app", fake_serve)

    assert main(["ui", str(project), "--no-browser"]) == 0
    assert captured == {
        "workspace_root": project,
        "initial_selection": adventure_path,
        "selected_title": "The Glass Saint",
        "host": "127.0.0.1",
        "port": 8765,
        "open_browser": False,
    }


def test_cli_ui_preserves_a_nonexistent_workspace_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "new-workspace"
    captured: dict[str, object] = {}

    def open_workspace(root: Path) -> LocalAdventureWorkspace:
        captured["workspace_root"] = root
        return LocalAdventureWorkspace(root)

    monkeypatch.setattr("adventure_graph.bootstrap.LocalAdventureWorkspace", open_workspace)

    assert main(["ui", str(target), "--no-browser"]) == 2
    assert captured == {"workspace_root": target}
    assert f"Workspace does not exist: {target}" in capsys.readouterr().err
