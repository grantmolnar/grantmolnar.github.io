"""Tests for the exact native desktop build toolchain contract."""

from __future__ import annotations

import hashlib
import importlib.metadata
from pathlib import Path

import pytest
import scripts.desktop_build_environment as build_environment
from scripts.desktop_build_environment import (
    DESKTOP_BUILD_REQUIREMENTS,
    build_requirements_sha256,
    expected_build_dependencies,
    require_build_environment,
    validate_recorded_build_dependencies,
)


def test_expected_dependencies_are_platform_specific() -> None:
    common = {
        "altgraph": "0.17.5",
        "packaging": "26.1",
        "pyinstaller": "6.21.0",
        "pyinstaller-hooks-contrib": "2026.6",
        "setuptools": "83.0.0",
    }

    assert expected_build_dependencies("linux") == common
    assert expected_build_dependencies("macos") == {**common, "macholib": "1.16.4"}
    assert expected_build_dependencies("windows") == {
        **common,
        "pefile": "2024.8.26",
        "pywin32-ctypes": "0.2.3",
    }


def test_unsupported_build_platform_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported desktop build platform"):
        expected_build_dependencies("amiga")


def test_build_lock_rejects_non_exact_requirements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = tmp_path / "requirements.txt"
    lock.write_text("pyinstaller>=6.21\n", encoding="utf-8")
    monkeypatch.setattr(build_environment, "DESKTOP_BUILD_REQUIREMENTS", lock)

    with pytest.raises(ValueError, match="exact distribution pin"):
        expected_build_dependencies("linux")


def test_build_lock_rejects_duplicate_requirements(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = tmp_path / "requirements.txt"
    lock.write_text("pyinstaller==6.21.0\npyinstaller==6.21.0\n", encoding="utf-8")
    monkeypatch.setattr(build_environment, "DESKTOP_BUILD_REQUIREMENTS", lock)

    with pytest.raises(ValueError, match="Duplicate desktop build requirement"):
        expected_build_dependencies("linux")


def test_matching_build_environment_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = expected_build_dependencies("linux")
    monkeypatch.setattr(importlib.metadata, "version", expected.__getitem__)

    assert require_build_environment("linux") == expected


def test_missing_and_mismatched_build_environment_has_actionable_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def installed_version(distribution: str) -> str:
        if distribution == "altgraph":
            raise importlib.metadata.PackageNotFoundError(distribution)
        if distribution == "pyinstaller":
            return "6.20.0"
        return expected_build_dependencies("linux")[distribution]

    monkeypatch.setattr(importlib.metadata, "version", installed_version)

    with pytest.raises(RuntimeError, match="make install-desktop-build") as error:
        require_build_environment("linux")

    assert "missing: altgraph" in str(error.value)
    assert "pyinstaller==6.20.0" in str(error.value)


def test_recorded_dependency_map_must_match_the_lock() -> None:
    recorded = expected_build_dependencies("linux")
    recorded["pyinstaller"] = "6.20.0"

    with pytest.raises(ValueError, match="do not match the checked-in lock"):
        validate_recorded_build_dependencies(recorded, "linux")


def test_requirements_digest_tracks_the_checked_in_file() -> None:
    normalized = DESKTOP_BUILD_REQUIREMENTS.read_text(encoding="utf-8").encode("utf-8")
    expected = hashlib.sha256(normalized).hexdigest()

    assert build_requirements_sha256() == expected


def test_requirements_digest_normalizes_platform_line_endings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lock = tmp_path / "requirements.txt"
    lock.write_bytes(b"pyinstaller==6.21.0\r\nsetuptools==83.0.0\r\n")
    monkeypatch.setattr(build_environment, "DESKTOP_BUILD_REQUIREMENTS", lock)
    expected = hashlib.sha256(
        b"pyinstaller==6.21.0\nsetuptools==83.0.0\n"
    ).hexdigest()

    assert build_requirements_sha256() == expected
