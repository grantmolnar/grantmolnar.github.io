"""Tests for collision-free local project companion paths."""

from pathlib import Path

from adventure_graph.infrastructure.local_project_paths import local_project_paths


def test_canonical_directory_project_uses_unprefixed_companions(tmp_path: Path) -> None:
    paths = local_project_paths(tmp_path / "ember-road" / "adventure.json")

    assert paths.play_state == tmp_path / "ember-road" / "play-state.json"
    assert paths.generated == tmp_path / "ember-road" / "generated"
    assert paths.archives == tmp_path / "ember-road" / "archives"


def test_standalone_adventure_namespaces_every_companion_surface(tmp_path: Path) -> None:
    paths = local_project_paths(tmp_path / "the-glass-saint.adventure.json")

    assert paths.play_state == tmp_path / "the-glass-saint.play-state.json"
    assert paths.generated == tmp_path / "the-glass-saint.generated"
    assert paths.archives == tmp_path / "the-glass-saint.archives"


def test_nonstandard_source_name_uses_its_stem_as_namespace(tmp_path: Path) -> None:
    paths = local_project_paths(tmp_path / "campaign.json")

    assert paths.play_state == tmp_path / "campaign.play-state.json"
    assert paths.generated == tmp_path / "campaign.generated"
    assert paths.archives == tmp_path / "campaign.archives"
