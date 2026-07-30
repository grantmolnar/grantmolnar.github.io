"""Tests for portable repository cleanup."""

from __future__ import annotations

from pathlib import Path

from scripts.clean_repository import clean_repository


def _write(path: Path, text: str = "generated\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_clean_repository_removes_nested_package_metadata_and_declared_artifacts(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "src" / "adventure_graph.egg-info" / "PKG-INFO")
    _write(tmp_path / "adventure_graph.egg-info" / "PKG-INFO")
    _write(tmp_path / "src" / "adventure_graph" / "__pycache__" / "module.pyc")
    _write(tmp_path / ".pytest_cache" / "state")
    _write(tmp_path / ".coverage.worker")
    _write(tmp_path / "coverage.xml")
    _write(tmp_path / "dist" / "artifact.whl")
    _write(tmp_path / "build" / "temporary.txt")
    _write(tmp_path / "src" / "adventure_graph" / "module.py", "source\n")
    _write(tmp_path / "notes.egg-info.txt", "source\n")

    removed = clean_repository(tmp_path)

    assert not (tmp_path / "src" / "adventure_graph.egg-info").exists()
    assert not (tmp_path / "adventure_graph.egg-info").exists()
    assert not (tmp_path / "src" / "adventure_graph" / "__pycache__").exists()
    assert not (tmp_path / ".pytest_cache").exists()
    assert not (tmp_path / ".coverage.worker").exists()
    assert not (tmp_path / "coverage.xml").exists()
    assert not (tmp_path / "dist").exists()
    assert not (tmp_path / "build").exists()
    assert (tmp_path / "src" / "adventure_graph" / "module.py").read_text(
        encoding="utf-8"
    ) == "source\n"
    assert (tmp_path / "notes.egg-info.txt").is_file()
    assert Path("src/adventure_graph.egg-info") in removed
