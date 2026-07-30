"""Tests for portable source-snapshot packaging."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest
from scripts.source_snapshot import (
    ARCHIVE_ROOT,
    MAX_ARCHIVE_MEMBER_PATH_CHARS,
    MAX_REPOSITORY_RELATIVE_PATH_CHARS,
    SUPPORTED_EXTRACTION_PREFIX_CHARS,
    WINDOWS_LEGACY_PATH_LIMIT_CHARS,
    audit_source_tree,
    build_source_snapshot,
    verify_source_snapshot,
)

from tests.support.paths import PROJECT_ROOT


def _minimal_source(root: Path) -> Path:
    files = {
        "BETA-TERMS.md": "terms\n",
        "README.md": "readme\n",
        "pyproject.toml": "[project]\nname='test'\n",
        "src/adventure_graph/__init__.py": "\n",
        "docs/guide.md": "guide\n",
    }
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_repository_fits_declared_source_snapshot_path_budget() -> None:
    audit = audit_source_tree(PROJECT_ROOT)

    assert audit.longest_relative_path_chars <= MAX_REPOSITORY_RELATIVE_PATH_CHARS
    assert audit.longest_member_path_chars <= MAX_ARCHIVE_MEMBER_PATH_CHARS
    assert audit.file_count > 800


def test_builder_uses_short_stable_root_and_is_deterministic(tmp_path: Path) -> None:
    source = _minimal_source(tmp_path / "source")
    first = tmp_path / "first-long-human-readable-session-name.zip"
    second = tmp_path / "second-long-human-readable-session-name.zip"

    first_evidence = build_source_snapshot(first, source_root=source)
    second_evidence = build_source_snapshot(second, source_root=source)

    assert _sha256(first) == _sha256(second)
    assert first_evidence.archive_sha256 == second_evidence.archive_sha256
    with zipfile.ZipFile(first) as archive:
        names = archive.namelist()
    assert names
    assert all(name.startswith(f"{ARCHIVE_ROOT}/") for name in names)
    assert not any("first-long-human-readable-session-name" in name for name in names)


def test_snapshot_extracts_with_declared_destination_prefix_budget(tmp_path: Path) -> None:
    source = _minimal_source(tmp_path / "source")
    archive_path = tmp_path / "snapshot.zip"
    evidence = build_source_snapshot(archive_path, source_root=source)
    destination = tmp_path / (
        "x" * max(1, SUPPORTED_EXTRACTION_PREFIX_CHARS - len(str(tmp_path)) - 1)
    )
    destination.mkdir()

    assert len(str(destination)) <= SUPPORTED_EXTRACTION_PREFIX_CHARS
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(destination)
    extracted = destination / ARCHIVE_ROOT / "README.md"

    assert extracted.read_text(encoding="utf-8") == "readme\n"
    assert len(str(destination)) + 1 + evidence.longest_member_path_chars <= (
        WINDOWS_LEGACY_PATH_LIMIT_CHARS
    )


def test_verifier_rejects_old_descriptive_internal_root(tmp_path: Path) -> None:
    archive_path = tmp_path / "old.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(
            "adventure-graph-0.10.0-aurelune-reference-defragmentation-session-04/README.md",
            "readme\n",
        )

    with pytest.raises(ValueError, match="outside the required root"):
        verify_source_snapshot(archive_path)


def test_verifier_rejects_member_beyond_path_budget(tmp_path: Path) -> None:
    archive_path = tmp_path / "long.zip"
    member = f"{ARCHIVE_ROOT}/{'x' * MAX_ARCHIVE_MEMBER_PATH_CHARS}.txt"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(member, "too long\n")

    with pytest.raises(ValueError, match="exceeds"):
        verify_source_snapshot(archive_path)


def test_verifier_rejects_unsafe_or_case_colliding_members(tmp_path: Path) -> None:
    unsafe = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(unsafe, "w") as archive:
        archive.writestr(f"{ARCHIVE_ROOT}/../escape.txt", "bad\n")
    with pytest.raises(ValueError, match="unsafe path"):
        verify_source_snapshot(unsafe)

    collision = tmp_path / "collision.zip"
    with zipfile.ZipFile(collision, "w") as archive:
        archive.writestr(f"{ARCHIVE_ROOT}/README.md", "one\n")
        archive.writestr(f"{ARCHIVE_ROOT}/readme.md", "two\n")
    with pytest.raises(ValueError, match="Case-colliding"):
        verify_source_snapshot(collision)


def test_builder_excludes_local_generated_and_secret_files(tmp_path: Path) -> None:
    source = _minimal_source(tmp_path / "source")
    (source / ".env").write_text("SECRET=value\n", encoding="utf-8")
    (source / ".env.example").write_text("SECRET=\n", encoding="utf-8")
    (source / "dist").mkdir()
    (source / "dist" / "old.zip").write_bytes(b"old")
    (source / ".pytest_cache").mkdir()
    (source / ".pytest_cache" / "state").write_text("cache\n", encoding="utf-8")
    (source / ".coverage.worker").write_bytes(b"coverage")
    archive_path = tmp_path / "snapshot.zip"

    build_source_snapshot(archive_path, source_root=source)

    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
    assert f"{ARCHIVE_ROOT}/.env" not in names
    assert f"{ARCHIVE_ROOT}/dist/old.zip" not in names
    assert f"{ARCHIVE_ROOT}/.pytest_cache/state" not in names
    assert f"{ARCHIVE_ROOT}/.coverage.worker" not in names
    assert f"{ARCHIVE_ROOT}/.env.example" in names
