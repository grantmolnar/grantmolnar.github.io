"""Adversarial filesystem tests for browser-owned local project surfaces."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.support.adventures import complete_four_encounter_adventure

from adventure_graph.infrastructure.adventure_store import save_adventure
from adventure_graph.infrastructure.local_adventure_workspace import LocalAdventureWorkspace
from adventure_graph.infrastructure.local_path_safety import (
    UnsafeFilesystemLayoutError,
    require_symlink_free_tree,
)
from adventure_graph.web_composition import LocalWebProjects


def _symlink_or_skip(link: Path, target: Path, *, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except OSError:
        pytest.skip("Filesystem symlinks are not available on this platform.")


def _project_source(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    project.mkdir()
    source = project / "adventure.json"
    save_adventure(source, complete_four_encounter_adventure())
    return source


def test_symlink_free_tree_rejects_a_symlink_below_nested_directories(tmp_path: Path) -> None:
    owned = tmp_path / "owned"
    nested = owned / "first" / "second"
    nested.mkdir(parents=True)
    external = tmp_path / "external"
    external.mkdir()
    _symlink_or_skip(nested / "borrowed", external, directory=True)

    with pytest.raises(UnsafeFilesystemLayoutError, match="must not contain symlinks"):
        require_symlink_free_tree(owned, tmp_path, label="Owned tree")


def test_workspace_rejects_a_symlinked_settings_directory(tmp_path: Path) -> None:
    external = tmp_path.parent / f"{tmp_path.name}-settings"
    external.mkdir()
    _symlink_or_skip(tmp_path / ".adventure-graph", external, directory=True)

    with pytest.raises(UnsafeFilesystemLayoutError, match=r"settings directory.*symlinks"):
        LocalAdventureWorkspace(tmp_path).load()


def test_browser_project_rejects_a_symlinked_active_journal(tmp_path: Path) -> None:
    source = _project_source(tmp_path)
    external_state = tmp_path / "external-play-state.json"
    external_state.write_text("{}", encoding="utf-8")
    _symlink_or_skip(source.with_name("play-state.json"), external_state)

    with pytest.raises(UnsafeFilesystemLayoutError, match=r"Active play journal.*symlinks"):
        LocalWebProjects.open(source)


def test_browser_project_rejects_nested_symlinks_in_generated_reports(tmp_path: Path) -> None:
    source = _project_source(tmp_path)
    generated = source.parent / "generated"
    generated.mkdir()
    external = tmp_path / "external-generated"
    external.mkdir()
    _symlink_or_skip(generated / "encounters", external, directory=True)

    with pytest.raises(UnsafeFilesystemLayoutError, match="Generated report directory"):
        LocalWebProjects.open(source)


def test_browser_project_rejects_symlinked_archive_entries(tmp_path: Path) -> None:
    source = _project_source(tmp_path)
    archives = source.parent / "archives"
    archives.mkdir()
    external = tmp_path / "external-archive.json"
    external.write_text("{}", encoding="utf-8")
    _symlink_or_skip(archives / "borrowed.journal.json", external)

    with pytest.raises(UnsafeFilesystemLayoutError, match="Journal archive directory"):
        LocalWebProjects.open(source)
