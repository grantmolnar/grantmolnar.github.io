"""Tests for deterministic native desktop artifact assembly."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest
from scripts.build_desktop import (
    _archive_bundle,
    _reject_canonical_user_data,
    _validated_output_dir,
    _write_deterministic_tar_gz,
    _write_deterministic_zip,
)


def _sample_bundle(root: Path) -> Path:
    bundle = root / "Adventure Graph"
    assets = bundle / "assets"
    assets.mkdir(parents=True)
    executable = bundle / "Adventure Graph"
    executable.write_bytes(b"native launcher\n")
    executable.chmod(0o755)
    (assets / "app.txt").write_text("runtime asset\n", encoding="utf-8")
    return bundle


def test_normalized_tar_gz_is_reproducible(tmp_path: Path) -> None:
    bundle = _sample_bundle(tmp_path)
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"

    _write_deterministic_tar_gz(bundle, first, archive_root="Adventure-Graph-test")
    _write_deterministic_tar_gz(bundle, second, archive_root="Adventure-Graph-test")

    assert first.read_bytes() == second.read_bytes()


def test_normalized_zip_is_reproducible_and_preserves_executable_mode(
    tmp_path: Path,
) -> None:
    bundle = _sample_bundle(tmp_path)
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"

    _write_deterministic_zip(bundle, first, archive_root="Adventure-Graph-test")
    _write_deterministic_zip(bundle, second, archive_root="Adventure-Graph-test")

    assert first.read_bytes() == second.read_bytes()
    with ZipFile(first) as archive:
        info = archive.getinfo("Adventure-Graph-test/Adventure Graph")
    assert (info.external_attr >> 16) & 0o111


def test_macos_archive_preserves_app_bundle_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = tmp_path / "Adventure Graph.app"
    executable = bundle / "Contents" / "MacOS" / "Adventure Graph"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"native launcher\n")
    executable.chmod(0o755)
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setattr("scripts.build_desktop.sys.platform", "darwin")

    artifact = _archive_bundle(bundle, output, "0.10.0")

    with ZipFile(artifact) as archive:
        names = archive.namelist()
    assert "Adventure Graph.app/Contents/MacOS/Adventure Graph" in names


def test_bundle_rejects_canonical_user_data(tmp_path: Path) -> None:
    bundle = _sample_bundle(tmp_path)
    (bundle / "adventure.json").write_text("{}\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="canonical user data"):
        _reject_canonical_user_data(bundle)


def test_output_directory_must_remain_under_project_dist(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="must stay inside"):
        _validated_output_dir(tmp_path / "unsafe-output")
