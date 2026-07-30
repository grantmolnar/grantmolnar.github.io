"""Tests for the canonical beta workspace discovery policy."""

from __future__ import annotations

from pathlib import Path

import pytest

from adventure_graph.infrastructure.workspace_discovery import (
    discover_workspace_adventure_sources,
)


def _touch_project(directory: Path) -> Path:
    directory.mkdir(parents=True)
    source = directory / "adventure.json"
    source.write_text("{}", encoding="utf-8")
    return source.resolve()


def test_discovery_accepts_only_root_and_visible_direct_child_projects(tmp_path: Path) -> None:
    root_source = tmp_path / "adventure.json"
    root_source.write_text("{}", encoding="utf-8")
    child_source = _touch_project(tmp_path / "alpha")
    _touch_project(tmp_path / "collection" / "nested")
    _touch_project(tmp_path / ".hidden")
    (tmp_path / "standalone.adventure.json").write_text("{}", encoding="utf-8")

    assert discover_workspace_adventure_sources(tmp_path) == (
        root_source.resolve(),
        child_source,
    )


def test_discovery_does_not_follow_symlinked_project_directories(tmp_path: Path) -> None:
    external = tmp_path.parent / f"{tmp_path.name}-external"
    _touch_project(external)
    link = tmp_path / "linked"
    try:
        link.symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are not available on this platform.")

    assert discover_workspace_adventure_sources(tmp_path) == ()
