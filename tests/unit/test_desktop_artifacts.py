"""Tests for downloaded native desktop artifact evidence."""

from __future__ import annotations

import json
import os
import stat
import zipfile
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from scripts.build_desktop import _write_deterministic_tar_gz, _write_deterministic_zip
from scripts.desktop_artifacts import (
    BUNDLE_ENTRY_LIMIT,
    BUNDLE_LIMIT_BYTES,
    BUNDLE_UNPACKED_LIMIT_BYTES,
    InventoryEntry,
    _reject_escaping_symlinks,
    sha256_file,
    verify_artifact_manifest,
    verify_artifact_set,
    write_artifact_manifest,
)
from scripts.desktop_build_environment import (
    build_requirements_sha256,
    expected_build_dependencies,
)

from tests.support.paths import PROJECT_ROOT


def _build_metadata(platform_tag: str) -> dict[str, Any]:
    return {
        "build_dependencies": expected_build_dependencies(platform_tag),
        "build_requirements_sha256": build_requirements_sha256(),
        "build_operating_system": "Test OS",
        "runner_image": "test-runner",
        "runner_image_version": "test-version",
    }


def _bundle(root: Path, platform_tag: str) -> Path:
    bundle = root / ("Adventure Graph.app" if platform_tag == "macos" else "Adventure Graph")
    executable = (
        bundle / "Contents" / "MacOS" / "Adventure Graph"
        if platform_tag == "macos"
        else bundle / "Adventure Graph.exe"
        if platform_tag == "windows"
        else bundle / "Adventure Graph"
    )
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"native launcher\n")
    executable.chmod(0o755)
    assets = bundle / ("Contents/Resources" if platform_tag == "macos" else "assets")
    assets.mkdir(parents=True)
    (assets / "app.txt").write_text("runtime asset\n", encoding="utf-8")
    return bundle


def _artifact_pair(
    root: Path,
    platform_tag: str,
    *,
    architecture: str = "x86_64",
    source_revision: str = "revision-123",
) -> tuple[Path, Path, Path]:
    platform_root = root / platform_tag
    platform_root.mkdir(parents=True)
    bundle = _bundle(platform_root, platform_tag)
    stem = f"Adventure-Graph-0.10.0-{platform_tag}-{architecture}"
    if platform_tag == "linux":
        artifact = platform_root / f"{stem}.tar.gz"
        _write_deterministic_tar_gz(bundle, artifact, archive_root=stem)
    else:
        artifact = platform_root / f"{stem}.zip"
        archive_root = "Adventure Graph.app" if platform_tag == "macos" else stem
        _write_deterministic_zip(bundle, artifact, archive_root=archive_root)
    manifest = write_artifact_manifest(
        artifact,
        bundle,
        version="0.10.0",
        platform_tag=platform_tag,
        architecture_tag=architecture,
        python_version="3.13.5",
        pyinstaller_version="6.21.0",
        source_revision=source_revision,
        **_build_metadata(platform_tag),
    )
    return bundle, artifact, manifest


def _update_archive_facts(manifest: Path, artifact: Path) -> None:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["artifact_bytes"] = artifact.stat().st_size
    data["artifact_sha256"] = sha256_file(artifact)
    manifest.write_text(f"{json.dumps(data, indent=2, sort_keys=True)}\n", encoding="utf-8")


@pytest.mark.parametrize("platform_tag", ["linux", "windows", "macos"])
def test_verifier_accepts_each_platform_archive(tmp_path: Path, platform_tag: str) -> None:
    _, artifact, manifest = _artifact_pair(tmp_path, platform_tag)

    evidence = verify_artifact_manifest(manifest, expected_source_revision="revision-123")

    assert evidence.platform == platform_tag
    assert evidence.artifact_path == artifact.resolve()


def test_verifier_requires_one_complete_native_platform_set(tmp_path: Path) -> None:
    for platform_tag in ("linux", "windows", "macos"):
        _artifact_pair(tmp_path, platform_tag)

    evidence = verify_artifact_set(
        tmp_path,
        required_platforms=("linux", "windows", "macos"),
        expected_source_revision="revision-123",
    )

    assert {item.platform for item in evidence} == {"linux", "windows", "macos"}


def test_verifier_rejects_multiple_artifacts_for_one_required_platform(tmp_path: Path) -> None:
    _artifact_pair(tmp_path / "one", "linux", architecture="x86_64")
    _artifact_pair(tmp_path / "two", "linux", architecture="arm64")

    with pytest.raises(ValueError, match="exactly one artifact"):
        verify_artifact_set(tmp_path, required_platforms=("linux",))


def test_verifier_rejects_unpaired_archive(tmp_path: Path) -> None:
    _, artifact, _ = _artifact_pair(tmp_path, "linux")
    unpaired = artifact.with_name("Adventure-Graph-0.10.0-linux-arm64.tar.gz")
    unpaired.write_bytes(artifact.read_bytes())

    with pytest.raises(ValueError, match="without adjacent verified manifests"):
        verify_artifact_set(tmp_path)


def test_verifier_rejects_missing_required_platform(tmp_path: Path) -> None:
    _artifact_pair(tmp_path, "linux")

    with pytest.raises(ValueError, match="missing required platforms"):
        verify_artifact_set(tmp_path, required_platforms=("linux", "windows"))


def test_verifier_rejects_mixed_source_revisions(tmp_path: Path) -> None:
    _artifact_pair(tmp_path, "linux", source_revision="old-revision")

    with pytest.raises(ValueError, match="does not match"):
        verify_artifact_set(tmp_path, expected_source_revision="accepted-revision")


def test_verifier_rejects_archive_tampering(tmp_path: Path) -> None:
    _, artifact, manifest = _artifact_pair(tmp_path, "windows")
    artifact.write_bytes(artifact.read_bytes() + b"tampered")

    with pytest.raises(ValueError, match="byte count"):
        verify_artifact_manifest(manifest)


def test_verifier_rejects_unsafe_archive_member_path(tmp_path: Path) -> None:
    _, artifact, manifest = _artifact_pair(tmp_path, "windows")
    with zipfile.ZipFile(artifact, "a") as archive:
        archive.writestr("Adventure-Graph-0.10.0-windows-x86_64/../escape.txt", b"bad")
    _update_archive_facts(manifest, artifact)

    with pytest.raises(ValueError, match="unsafe path"):
        verify_artifact_manifest(manifest)


def test_verifier_rejects_canonical_user_data_inside_archive(tmp_path: Path) -> None:
    bundle, artifact, _ = _artifact_pair(tmp_path, "windows")
    (bundle / "adventure.json").write_text("{}\n", encoding="utf-8")
    _write_deterministic_zip(
        bundle,
        artifact,
        archive_root="Adventure-Graph-0.10.0-windows-x86_64",
    )
    manifest = write_artifact_manifest(
        artifact,
        bundle,
        version="0.10.0",
        platform_tag="windows",
        architecture_tag="x86_64",
        python_version="3.13.5",
        pyinstaller_version="6.21.0",
        source_revision="revision-123",
        **_build_metadata("windows"),
    )

    with pytest.raises(ValueError, match="canonical user data"):
        verify_artifact_manifest(manifest)


def test_linux_tar_hardlinks_verify_as_regular_bundle_files(tmp_path: Path) -> None:
    bundle, artifact, _ = _artifact_pair(tmp_path, "linux")
    source = bundle / "assets" / "app.txt"
    linked = bundle / "assets" / "app-copy.txt"
    try:
        linked.hardlink_to(source)
    except OSError:
        pytest.skip("Hard links are unavailable in this environment")
    _write_deterministic_tar_gz(
        bundle,
        artifact,
        archive_root="Adventure-Graph-0.10.0-linux-x86_64",
    )
    manifest = write_artifact_manifest(
        artifact,
        bundle,
        version="0.10.0",
        platform_tag="linux",
        architecture_tag="x86_64",
        python_version="3.13.5",
        pyinstaller_version="6.21.0",
        source_revision="revision-123",
        **_build_metadata("linux"),
    )

    evidence = verify_artifact_manifest(manifest)

    assert evidence.platform == "linux"


def test_symlink_validation_resolves_chained_directory_link() -> None:
    entries = (
        InventoryEntry(
            "Contents/Frameworks/Python.framework/Python",
            "symlink",
            0o777,
            23,
            "Versions/Current/Python",
        ),
        InventoryEntry(
            "Contents/Frameworks/Python.framework/Versions/Current",
            "symlink",
            0o777,
            4,
            "3.13",
        ),
        InventoryEntry(
            "Contents/Frameworks/Python.framework/Versions/3.13/Python",
            "file",
            0o755,
            1,
            "0" * 64,
        ),
    )

    _reject_escaping_symlinks(entries)


def test_symlink_validation_applies_parent_after_following_directory_link() -> None:
    entries = (
        InventoryEntry("source", "symlink", 0o777, 13, "alias/../file"),
        InventoryEntry("alias", "symlink", 0o777, 8, "real/dir"),
        InventoryEntry("real/dir/marker", "file", 0o644, 1, "0" * 64),
        InventoryEntry("real/file", "file", 0o644, 1, "1" * 64),
    )

    _reject_escaping_symlinks(entries)


def test_symlink_validation_rejects_escape_reached_through_chain() -> None:
    entries = (
        InventoryEntry(
            "Contents/Frameworks/Python.framework/Python",
            "symlink",
            0o777,
            23,
            "Versions/Current/Python",
        ),
        InventoryEntry(
            "Contents/Frameworks/Python.framework/Versions/Current",
            "symlink",
            0o777,
            22,
            "../../../../../outside",
        ),
    )

    with pytest.raises(ValueError, match="escapes the bundle root"):
        _reject_escaping_symlinks(entries)


def test_symlink_validation_rejects_missing_final_member() -> None:
    entries = (InventoryEntry("link", "symlink", 0o777, 7, "missing"),)

    with pytest.raises(ValueError, match="targets missing member"):
        _reject_escaping_symlinks(entries)


def test_macos_zip_preserves_host_symlink_mode_for_manifest_verification(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    platform_root = tmp_path / "macos"
    platform_root.mkdir()
    bundle = _bundle(platform_root, "macos")
    framework = bundle / "Contents" / "Frameworks" / "Python.framework"
    version = framework / "Versions" / "3.13"
    version.mkdir(parents=True)
    target = version / "Python"
    target.write_bytes(b"framework binary\n")
    link = framework / "Python"
    try:
        link.symlink_to("Versions/3.13/Python")
    except OSError:
        pytest.skip("Symbolic links are unavailable in this environment")

    original_lstat = Path.lstat

    def lstat_with_macos_symlink_mode(path: Path) -> os.stat_result:
        result = original_lstat(path)
        if path == link:
            values = list(result)
            values[0] = stat.S_IFLNK | 0o755
            return os.stat_result(values)
        return result

    monkeypatch.setattr(Path, "lstat", lstat_with_macos_symlink_mode)
    artifact = platform_root / "Adventure-Graph-0.10.0-macos-x86_64.zip"
    _write_deterministic_zip(bundle, artifact, archive_root="Adventure Graph.app")
    manifest = write_artifact_manifest(
        artifact,
        bundle,
        version="0.10.0",
        platform_tag="macos",
        architecture_tag="x86_64",
        python_version="3.13.5",
        pyinstaller_version="6.21.0",
        source_revision="revision-123",
        **_build_metadata("macos"),
    )

    evidence = verify_artifact_manifest(manifest)

    assert evidence.platform == "macos"


def test_verifier_accepts_macos_framework_symlink_chain(tmp_path: Path) -> None:
    platform_root = tmp_path / "macos"
    platform_root.mkdir()
    bundle = _bundle(platform_root, "macos")
    framework = bundle / "Contents" / "Frameworks" / "Python.framework"
    version = framework / "Versions" / "3.13"
    version.mkdir(parents=True)
    (version / "Python").write_bytes(b"framework binary\n")
    try:
        (framework / "Versions" / "Current").symlink_to("3.13", target_is_directory=True)
        (framework / "Python").symlink_to("Versions/Current/Python")
    except OSError:
        pytest.skip("Symbolic links are unavailable in this environment")

    artifact = platform_root / "Adventure-Graph-0.10.0-macos-x86_64.zip"
    _write_deterministic_zip(bundle, artifact, archive_root="Adventure Graph.app")
    manifest = write_artifact_manifest(
        artifact,
        bundle,
        version="0.10.0",
        platform_tag="macos",
        architecture_tag="x86_64",
        python_version="3.13.5",
        pyinstaller_version="6.21.0",
        source_revision="revision-123",
        **_build_metadata("macos"),
    )

    evidence = verify_artifact_manifest(manifest)

    assert evidence.platform == "macos"


def test_verifier_rejects_symbolic_link_cycle(tmp_path: Path) -> None:
    platform_root = tmp_path / "macos"
    platform_root.mkdir()
    bundle = _bundle(platform_root, "macos")
    links = bundle / "Contents" / "Frameworks"
    links.mkdir(parents=True, exist_ok=True)
    try:
        (links / "first").symlink_to("second")
        (links / "second").symlink_to("first")
    except OSError:
        pytest.skip("Symbolic links are unavailable in this environment")

    artifact = platform_root / "Adventure-Graph-0.10.0-macos-x86_64.zip"
    _write_deterministic_zip(bundle, artifact, archive_root="Adventure Graph.app")
    manifest = write_artifact_manifest(
        artifact,
        bundle,
        version="0.10.0",
        platform_tag="macos",
        architecture_tag="x86_64",
        python_version="3.13.5",
        pyinstaller_version="6.21.0",
        source_revision="revision-123",
        **_build_metadata("macos"),
    )

    with pytest.raises(ValueError, match="contains a cycle"):
        verify_artifact_manifest(manifest)


def test_verifier_rejects_symbolic_link_that_escapes_bundle(tmp_path: Path) -> None:
    bundle, artifact, _ = _artifact_pair(tmp_path, "linux")
    link = bundle / "escape"
    try:
        link.symlink_to("../../outside")
    except OSError:
        pytest.skip("Symbolic links are unavailable in this environment")
    _write_deterministic_tar_gz(
        bundle,
        artifact,
        archive_root="Adventure-Graph-0.10.0-linux-x86_64",
    )
    manifest = write_artifact_manifest(
        artifact,
        bundle,
        version="0.10.0",
        platform_tag="linux",
        architecture_tag="x86_64",
        python_version="3.13.5",
        pyinstaller_version="6.21.0",
        source_revision="revision-123",
        **_build_metadata("linux"),
    )

    with pytest.raises(ValueError, match="escapes the bundle root"):
        verify_artifact_manifest(manifest)


def test_verifier_rejects_case_colliding_archive_members(tmp_path: Path) -> None:
    _, artifact, manifest = _artifact_pair(tmp_path, "windows")
    root = "Adventure-Graph-0.10.0-windows-x86_64"
    with zipfile.ZipFile(artifact, "a") as archive:
        for name in ("Readme.txt", "README.txt"):
            info = zipfile.ZipInfo(f"{root}/{name}")
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, name.encode("utf-8"))
    _update_archive_facts(manifest, artifact)

    with pytest.raises(ValueError, match="case-colliding"):
        verify_artifact_manifest(manifest)


def test_manifest_records_verifiable_inventory_and_limits(tmp_path: Path) -> None:
    _, artifact, manifest = _artifact_pair(tmp_path, "linux")
    data = json.loads(manifest.read_text(encoding="utf-8"))

    assert data["schema_version"] == 3
    assert data["artifact"] == artifact.name
    assert data["build_dependencies"] == expected_build_dependencies("linux")
    assert data["build_requirements_sha256"] == build_requirements_sha256()
    assert data["build_operating_system"] == "Test OS"
    assert data["runner_image"] == "test-runner"
    assert data["runner_image_version"] == "test-version"
    assert data["compressed_limit_bytes"] == BUNDLE_LIMIT_BYTES
    assert data["bundle_entry_limit"] == BUNDLE_ENTRY_LIMIT
    assert data["bundle_unpacked_limit_bytes"] == BUNDLE_UNPACKED_LIMIT_BYTES
    assert data["bundle_regular_file_count"] == 2
    assert data["bundle_symlink_count"] == 0
    assert len(data["bundle_inventory_sha256"]) == 64


def test_verifier_rejects_build_dependency_drift(tmp_path: Path) -> None:
    _, _, manifest = _artifact_pair(tmp_path, "linux")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["build_dependencies"]["pyinstaller"] = "6.20.0"
    manifest.write_text(f"{json.dumps(data, indent=2, sort_keys=True)}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="do not match the checked-in lock"):
        verify_artifact_manifest(manifest)


def test_verifier_rejects_requirements_lock_drift(tmp_path: Path) -> None:
    _, _, manifest = _artifact_pair(tmp_path, "linux")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["build_requirements_sha256"] = "0" * 64
    manifest.write_text(f"{json.dumps(data, indent=2, sort_keys=True)}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="requirements digest"):
        verify_artifact_manifest(manifest)


def test_verifier_rejects_duplicate_pyinstaller_version(tmp_path: Path) -> None:
    _, _, manifest = _artifact_pair(tmp_path, "linux")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["pyinstaller"] = "6.20.0"
    manifest.write_text(f"{json.dumps(data, indent=2, sort_keys=True)}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="PyInstaller version"):
        verify_artifact_manifest(manifest)


def test_generated_manifest_matches_published_schema(tmp_path: Path) -> None:
    _, _, manifest = _artifact_pair(tmp_path, "linux")
    schema = json.loads(
        (PROJECT_ROOT / "schemas" / "desktop-artifact-manifest.schema.json").read_text(
            encoding="utf-8"
        )
    )
    data = json.loads(manifest.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(data)
