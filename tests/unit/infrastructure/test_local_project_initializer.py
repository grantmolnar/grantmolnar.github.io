"""Tests for local starter-project creation."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.support.adventures import complete_four_encounter_adventure

from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.local_project_initializer import LocalProjectInitializer
from adventure_graph.infrastructure.play_state_store import load_play_state


def test_local_project_initializer_creates_complete_canonical_project(tmp_path: Path) -> None:
    directory = tmp_path / "starter project"
    adventure = complete_four_encounter_adventure()

    LocalProjectInitializer(directory).create(adventure, new_play_state(adventure))

    assert load_adventure(directory / "adventure.json") == adventure
    assert load_play_state(directory / "play-state.json").adventure_id == adventure.id
    assert (directory / "generated").is_dir()
    assert (directory / "archives").is_dir()


def test_local_project_initializer_refuses_existing_canonical_files(tmp_path: Path) -> None:
    directory = tmp_path / "occupied"
    directory.mkdir()
    adventure_path = directory / "adventure.json"
    adventure_path.write_text("keep me", encoding="utf-8")
    adventure = complete_four_encounter_adventure()

    with pytest.raises(OSError, match=r"Refusing to overwrite adventure\.json"):
        LocalProjectInitializer(directory).create(adventure, new_play_state(adventure))

    assert adventure_path.read_text(encoding="utf-8") == "keep me"
    assert not (directory / "play-state.json").exists()
