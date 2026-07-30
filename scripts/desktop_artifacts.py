"""Create and verify Adventure Graph desktop artifact manifests."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tarfile
import zipfile
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

if __package__:
    from scripts.desktop_build_environment import (
        build_requirements_sha256 as current_build_requirements_sha256,
        validate_recorded_build_dependencies,
    )
else:
    from desktop_build_environment import (
        build_requirements_sha256 as current_build_requirements_sha256,
        validate_recorded_build_dependencies,
    )

BUNDLE_LIMIT_BYTES = 100 * 1024 * 1024
BUNDLE_UNPACKED_LIMIT_BYTES = 512 * 1024 * 1024
BUNDLE_ENTRY_LIMIT = 20_000
MANIFEST_SCHEMA_VERSION = 3
SUPPORTED_PLATFORMS = frozenset({"linux", "windows", "macos"})
FORBIDDEN_USER_DATA_NAMES = frozenset(
    {
        "adventure.json",
        "play-state.json",
        "workspace-settings.json",
        "launcher-settings.json",
    }
)


@dataclass(frozen=True, slots=True)
class InventoryEntry:
    """One regular file or symbolic link in a desktop bundle."""

    path: str
    kind: str
    mode: int
    size: int
    digest_or_target: str

    def canonical_line(self) -> bytes:
        """Return a stable inventory representation suitable for hashing."""
        data = {
            "digest_or_target": self.digest_or_target,
            "kind": self.kind,
            "mode": self.mode,
            "path": self.path,
            "size": self.size,
        }
        return (
            json.dumps(data, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"
        ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class ArtifactEvidence:
    """Verified facts about one archive and its adjacent manifest."""

    manifest_path: Path
    artifact_path: Path
    platform: str
    architecture: str
    source_revision: str
    build_operating_system: str
    runner_image: str
    runner_image_version: str


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bundle_inventory(bundle: Path) -> tuple[InventoryEntry, ...]:
    """Return the verifiable non-directory inventory of an unpacked bundle."""
    entries: list[InventoryEntry] = []
    for path in sorted(bundle.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(bundle).as_posix()
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if path.is_symlink():
            target = os.readlink(path)
            entries.append(
                InventoryEntry(
                    path=relative,
                    kind="symlink",
                    mode=mode,
                    size=len(target.encode("utf-8")),
                    digest_or_target=target,
                )
            )
        elif path.is_file():
            entries.append(
                InventoryEntry(
                    path=relative,
                    kind="file",
                    mode=mode,
                    size=metadata.st_size,
                    digest_or_target=sha256_file(path),
                )
            )
    return tuple(entries)


def inventory_sha256(entries: Iterable[InventoryEntry]) -> str:
    """Return a stable digest over sorted bundle inventory records."""
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item.path):
        digest.update(entry.canonical_line())
    return digest.hexdigest()


def write_artifact_manifest(
    artifact: Path,
    bundle: Path,
    *,
    version: str,
    platform_tag: str,
    architecture_tag: str,
    python_version: str,
    pyinstaller_version: str,
    source_revision: str,
    build_dependencies: Mapping[str, str],
    build_requirements_sha256: str,
    build_operating_system: str,
    runner_image: str,
    runner_image_version: str,
) -> Path:
    """Write the adjacent schema-versioned manifest for one built archive."""
    normalized_dependencies = validate_recorded_build_dependencies(
        build_dependencies, platform_tag
    )
    if pyinstaller_version != normalized_dependencies["pyinstaller"]:
        raise ValueError(
            "Desktop artifact PyInstaller version must match the checked-in build lock."
        )
    if build_requirements_sha256 != current_build_requirements_sha256():
        raise ValueError(
            "Desktop artifact requirements digest must match the checked-in build lock."
        )
    environment_fields = {
        "build_operating_system": build_operating_system,
        "runner_image": runner_image,
        "runner_image_version": runner_image_version,
    }
    for field, value in environment_fields.items():
        if not value.strip():
            raise ValueError(f"Desktop artifact {field} must be a non-empty string.")

    entries = bundle_inventory(bundle)
    regular_files = [entry for entry in entries if entry.kind == "file"]
    symlinks = [entry for entry in entries if entry.kind == "symlink"]
    bundle_bytes = sum(entry.size for entry in regular_files)
    if len(entries) > BUNDLE_ENTRY_LIMIT:
        raise RuntimeError(
            f"Desktop bundle contains {len(entries):,} entries; the limit is "
            f"{BUNDLE_ENTRY_LIMIT:,}."
        )
    if bundle_bytes > BUNDLE_UNPACKED_LIMIT_BYTES:
        raise RuntimeError(
            f"Desktop bundle contains {bundle_bytes:,} regular-file bytes; the limit is "
            f"{BUNDLE_UNPACKED_LIMIT_BYTES:,}."
        )
    data: dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "application": "Adventure Graph",
        "version": version,
        "platform": platform_tag,
        "architecture": architecture_tag,
        "python": python_version,
        "pyinstaller": pyinstaller_version,
        "source_revision": source_revision,
        "build_dependencies": normalized_dependencies,
        "build_requirements_sha256": build_requirements_sha256,
        "build_operating_system": build_operating_system,
        "runner_image": runner_image,
        "runner_image_version": runner_image_version,
        "artifact": artifact.name,
        "artifact_bytes": artifact.stat().st_size,
        "artifact_sha256": sha256_file(artifact),
        "bundle_regular_file_count": len(regular_files),
        "bundle_symlink_count": len(symlinks),
        "bundle_bytes": bundle_bytes,
        "bundle_entry_limit": BUNDLE_ENTRY_LIMIT,
        "bundle_unpacked_limit_bytes": BUNDLE_UNPACKED_LIMIT_BYTES,
        "bundle_inventory_sha256": inventory_sha256(entries),
        "compressed_limit_bytes": BUNDLE_LIMIT_BYTES,
    }
    destination = artifact.with_suffix(f"{artifact.suffix}.manifest.json")
    destination.write_text(f"{json.dumps(data, indent=2, sort_keys=True)}\n", encoding="utf-8")
    return destination


def verify_artifact_set(
    directory: Path,
    *,
    required_platforms: Sequence[str] = (),
    expected_source_revision: str | None = None,
) -> tuple[ArtifactEvidence, ...]:
    """Verify every adjacent archive/manifest pair in one evidence directory."""
    root = directory.expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Desktop artifact directory does not exist: {root}.")
    manifests = sorted(root.rglob("*.manifest.json"))
    if not manifests:
        raise ValueError(f"No desktop artifact manifests found under {root}.")
    evidence = tuple(
        verify_artifact_manifest(path, expected_source_revision=expected_source_revision)
        for path in manifests
    )

    identities = [(item.platform, item.architecture) for item in evidence]
    if len(set(identities)) != len(identities):
        raise ValueError("Desktop evidence contains duplicate platform/architecture artifacts.")

    present_platforms = {item.platform for item in evidence}
    required = set(required_platforms)
    unsupported = required.difference(SUPPORTED_PLATFORMS)
    if unsupported:
        raise ValueError(f"Unsupported required desktop platforms: {sorted(unsupported)}.")
    missing = required.difference(present_platforms)
    if missing:
        raise ValueError(f"Desktop evidence is missing required platforms: {sorted(missing)}.")
    if required:
        unexpected = present_platforms.difference(required)
        if unexpected:
            raise ValueError(
                f"Desktop evidence contains unexpected platforms: {sorted(unexpected)}."
            )
        repeated = sorted(
            platform_tag
            for platform_tag in required
            if sum(item.platform == platform_tag for item in evidence) != 1
        )
        if repeated:
            raise ValueError(
                "Desktop evidence must contain exactly one artifact for each required "
                f"platform; invalid platforms: {repeated}."
            )

    paired_artifacts = {item.artifact_path.resolve() for item in evidence}
    candidate_artifacts = {
        path.resolve()
        for path in root.rglob("*")
        if path.is_file() and (path.suffix == ".zip" or path.name.endswith(".tar.gz"))
    }
    unpaired = sorted(candidate_artifacts.difference(paired_artifacts))
    if unpaired:
        names = ", ".join(str(path.relative_to(root)) for path in unpaired)
        raise ValueError(f"Desktop archives without adjacent verified manifests: {names}.")
    return evidence


def verify_artifact_manifest(
    manifest_path: Path,
    *,
    expected_source_revision: str | None = None,
) -> ArtifactEvidence:
    """Verify one archive against its adjacent manifest and internal inventory."""
    manifest = _read_manifest(manifest_path)
    platform_tag = _required_string(manifest, "platform")
    if platform_tag not in SUPPORTED_PLATFORMS:
        raise ValueError(f"{manifest_path}: unsupported platform {platform_tag!r}.")
    architecture = _required_string(manifest, "architecture")
    source_revision = _required_string(manifest, "source_revision")
    recorded_dependencies = manifest.get("build_dependencies")
    if not isinstance(recorded_dependencies, dict):
        raise ValueError(f"{manifest_path}: build_dependencies must be an object.")
    normalized_dependencies = validate_recorded_build_dependencies(
        recorded_dependencies, platform_tag
    )
    pyinstaller_version = _required_string(manifest, "pyinstaller")
    if pyinstaller_version != normalized_dependencies["pyinstaller"]:
        raise ValueError(
            f"{manifest_path}: PyInstaller version does not match build_dependencies."
        )
    recorded_lock_sha256 = _required_sha256(manifest, "build_requirements_sha256")
    if recorded_lock_sha256 != current_build_requirements_sha256():
        raise ValueError(
            f"{manifest_path}: desktop build requirements digest does not match "
            "the checked-in lock."
        )
    build_operating_system = _required_string(manifest, "build_operating_system")
    runner_image = _required_string(manifest, "runner_image")
    runner_image_version = _required_string(manifest, "runner_image_version")
    if expected_source_revision is not None and source_revision != expected_source_revision:
        raise ValueError(
            f"{manifest_path}: source revision {source_revision!r} does not match "
            f"{expected_source_revision!r}."
        )

    artifact_name = _required_string(manifest, "artifact")
    if Path(artifact_name).name != artifact_name:
        raise ValueError(f"{manifest_path}: artifact must be a plain filename.")
    artifact = manifest_path.parent / artifact_name
    if not artifact.is_file():
        raise ValueError(f"{manifest_path}: adjacent artifact is missing: {artifact_name}.")

    version = _required_string(manifest, "version")
    expected_stem = f"Adventure-Graph-{version}-{platform_tag}-{architecture}"
    expected_name = (
        f"{expected_stem}.tar.gz" if platform_tag == "linux" else f"{expected_stem}.zip"
    )
    if artifact_name != expected_name:
        raise ValueError(
            f"{manifest_path}: artifact name {artifact_name!r} does not match {expected_name!r}."
        )

    artifact_bytes = _required_integer(manifest, "artifact_bytes")
    if artifact.stat().st_size != artifact_bytes:
        raise ValueError(f"{manifest_path}: artifact byte count does not match the archive.")
    compressed_limit = _required_integer(manifest, "compressed_limit_bytes")
    if compressed_limit != BUNDLE_LIMIT_BYTES or artifact_bytes > compressed_limit:
        raise ValueError(f"{manifest_path}: artifact violates the 100 MiB compressed ceiling.")
    if sha256_file(artifact) != _required_sha256(manifest, "artifact_sha256"):
        raise ValueError(f"{manifest_path}: artifact SHA-256 does not match the archive.")

    expected_root = "Adventure Graph.app" if platform_tag == "macos" else expected_stem
    entries = _read_archive_inventory(artifact, expected_root=expected_root)
    regular_files = [entry for entry in entries if entry.kind == "file"]
    symlinks = [entry for entry in entries if entry.kind == "symlink"]
    bundle_bytes = sum(entry.size for entry in regular_files)
    if len(entries) > BUNDLE_ENTRY_LIMIT:
        raise RuntimeError(
            f"Desktop bundle contains {len(entries):,} entries; the limit is "
            f"{BUNDLE_ENTRY_LIMIT:,}."
        )
    if bundle_bytes > BUNDLE_UNPACKED_LIMIT_BYTES:
        raise RuntimeError(
            f"Desktop bundle contains {bundle_bytes:,} regular-file bytes; the limit is "
            f"{BUNDLE_UNPACKED_LIMIT_BYTES:,}."
        )
    if len(regular_files) != _required_integer(manifest, "bundle_regular_file_count"):
        raise ValueError(f"{manifest_path}: regular-file count does not match the archive.")
    if len(symlinks) != _required_integer(manifest, "bundle_symlink_count"):
        raise ValueError(f"{manifest_path}: symbolic-link count does not match the archive.")
    bundle_bytes = sum(entry.size for entry in regular_files)
    if bundle_bytes != _required_integer(manifest, "bundle_bytes"):
        raise ValueError(f"{manifest_path}: unpacked regular-file bytes do not match the archive.")
    if _required_integer(manifest, "bundle_entry_limit") != BUNDLE_ENTRY_LIMIT:
        raise ValueError(f"{manifest_path}: unexpected bundle entry limit.")
    if len(entries) > BUNDLE_ENTRY_LIMIT:
        raise ValueError(f"{manifest_path}: bundle exceeds the entry limit.")
    if (
        _required_integer(manifest, "bundle_unpacked_limit_bytes")
        != BUNDLE_UNPACKED_LIMIT_BYTES
    ):
        raise ValueError(f"{manifest_path}: unexpected unpacked bundle limit.")
    if bundle_bytes > BUNDLE_UNPACKED_LIMIT_BYTES:
        raise ValueError(f"{manifest_path}: bundle exceeds the unpacked byte limit.")
    if inventory_sha256(entries) != _required_sha256(manifest, "bundle_inventory_sha256"):
        raise ValueError(f"{manifest_path}: bundle inventory digest does not match the archive.")

    _verify_required_executable(entries, platform_tag)
    return ArtifactEvidence(
        manifest_path=manifest_path.resolve(),
        artifact_path=artifact.resolve(),
        platform=platform_tag,
        architecture=architecture,
        source_revision=source_revision,
        build_operating_system=build_operating_system,
        runner_image=runner_image,
        runner_image_version=runner_image_version,
    )


def _read_manifest(path: Path) -> Mapping[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read desktop artifact manifest {path}: {error}") from error
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: desktop artifact manifest must be a JSON object.")
    expected_fields = {
        "schema_version",
        "application",
        "version",
        "platform",
        "architecture",
        "python",
        "pyinstaller",
        "source_revision",
        "build_dependencies",
        "build_requirements_sha256",
        "build_operating_system",
        "runner_image",
        "runner_image_version",
        "artifact",
        "artifact_bytes",
        "artifact_sha256",
        "bundle_regular_file_count",
        "bundle_symlink_count",
        "bundle_bytes",
        "bundle_inventory_sha256",
        "bundle_entry_limit",
        "bundle_unpacked_limit_bytes",
        "compressed_limit_bytes",
    }
    unknown = set(raw).difference(expected_fields)
    missing = expected_fields.difference(raw)
    if unknown or missing:
        raise ValueError(
            f"{path}: manifest fields differ; missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}."
        )
    if raw["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise ValueError(f"{path}: unsupported manifest schema_version {raw['schema_version']!r}.")
    if raw["application"] != "Adventure Graph":
        raise ValueError(f"{path}: unexpected application name.")
    _required_string(raw, "python")
    _required_string(raw, "pyinstaller")
    return raw


def _required_string(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Desktop artifact manifest field {key!r} must be a non-empty string.")
    return value


def _required_integer(data: Mapping[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"Desktop artifact manifest field {key!r} must be a non-negative integer.")
    return value


def _required_sha256(data: Mapping[str, Any], key: str) -> str:
    value = _required_string(data, key)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"Desktop artifact manifest field {key!r} must be lowercase SHA-256.")
    return value


def _read_archive_inventory(artifact: Path, *, expected_root: str) -> tuple[InventoryEntry, ...]:
    if artifact.suffix == ".zip":
        entries = _read_zip_inventory(artifact, expected_root=expected_root)
    elif artifact.name.endswith(".tar.gz"):
        entries = _read_tar_inventory(artifact, expected_root=expected_root)
    else:
        raise ValueError(f"Unsupported desktop archive format: {artifact.name}.")
    _reject_ambiguous_paths(entries)
    _reject_forbidden_user_data(entries)
    _reject_escaping_symlinks(entries)
    return entries


def _read_zip_inventory(artifact: Path, *, expected_root: str) -> tuple[InventoryEntry, ...]:
    entries: list[InventoryEntry] = []
    seen_root = False
    try:
        with zipfile.ZipFile(artifact) as archive:
            infos = archive.infolist()
            if len(infos) > BUNDLE_ENTRY_LIMIT * 2:
                raise ValueError(f"{artifact}: archive contains too many members.")
            logical_bytes = 0
            for info in infos:
                relative = _archive_relative_path(info.filename, expected_root)
                if relative is None:
                    seen_root = True
                    continue
                mode = (info.external_attr >> 16) & 0o777
                kind_bits = (info.external_attr >> 16) & 0o170000
                if info.is_dir() or kind_bits == stat.S_IFDIR:
                    continue
                if len(entries) >= BUNDLE_ENTRY_LIMIT:
                    raise ValueError(f"{artifact}: bundle exceeds the entry limit.")
                if kind_bits == stat.S_IFLNK:
                    if info.file_size > 4096:
                        raise ValueError(
                            f"{artifact}: symbolic link {info.filename!r} is too large."
                        )
                    payload = archive.read(info)
                    try:
                        target = payload.decode("utf-8")
                    except UnicodeDecodeError as error:
                        raise ValueError(
                            f"{artifact}: symbolic link {info.filename!r} is not UTF-8."
                        ) from error
                    entries.append(
                        InventoryEntry(relative, "symlink", mode, len(payload), target)
                    )
                else:
                    digest = hashlib.sha256()
                    size = 0
                    with archive.open(info) as source:
                        for chunk in iter(lambda: source.read(1024 * 1024), b""):
                            size += len(chunk)
                            logical_bytes += len(chunk)
                            if logical_bytes > BUNDLE_UNPACKED_LIMIT_BYTES:
                                raise ValueError(
                                    f"{artifact}: bundle exceeds the unpacked byte limit."
                                )
                            digest.update(chunk)
                    entries.append(
                        InventoryEntry(relative, "file", mode, size, digest.hexdigest())
                    )
    except (OSError, zipfile.BadZipFile) as error:
        raise ValueError(f"Could not inspect desktop ZIP {artifact}: {error}") from error
    if not seen_root:
        # ZIP writers are not required to include an explicit root directory entry; member
        # containment still proves the root exists logically.
        seen_root = bool(entries)
    if not seen_root:
        raise ValueError(f"{artifact}: archive contains no bundle entries.")
    return tuple(sorted(entries, key=lambda entry: entry.path))


def _read_tar_inventory(artifact: Path, *, expected_root: str) -> tuple[InventoryEntry, ...]:
    entries: list[InventoryEntry] = []
    seen_root = False
    try:
        with tarfile.open(artifact, mode="r:gz") as archive:
            members = archive.getmembers()
            if len(members) > BUNDLE_ENTRY_LIMIT * 2:
                raise ValueError(f"{artifact}: archive contains too many members.")
            logical_bytes = 0
            for member in members:
                relative = _archive_relative_path(member.name, expected_root)
                if relative is None:
                    seen_root = True
                    continue
                mode = member.mode & 0o777
                if member.isdir():
                    continue
                if len(entries) >= BUNDLE_ENTRY_LIMIT:
                    raise ValueError(f"{artifact}: bundle exceeds the entry limit.")
                if member.issym():
                    target = member.linkname
                    entries.append(
                        InventoryEntry(
                            relative,
                            "symlink",
                            mode,
                            len(target.encode("utf-8")),
                            target,
                        )
                    )
                elif member.isfile() or member.islnk():
                    if member.islnk():
                        _archive_relative_path(member.linkname, expected_root)
                    source = archive.extractfile(member)
                    if source is None:
                        raise ValueError(f"{artifact}: could not read {member.name!r}.")
                    digest = hashlib.sha256()
                    size = 0
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        size += len(chunk)
                        logical_bytes += len(chunk)
                        if logical_bytes > BUNDLE_UNPACKED_LIMIT_BYTES:
                            raise ValueError(
                                f"{artifact}: bundle exceeds the unpacked byte limit."
                            )
                        digest.update(chunk)
                    entries.append(
                        InventoryEntry(relative, "file", mode, size, digest.hexdigest())
                    )
                else:
                    raise ValueError(
                        f"{artifact}: unsupported archive member type {member.name!r}."
                    )
    except (OSError, tarfile.TarError) as error:
        raise ValueError(f"Could not inspect desktop tarball {artifact}: {error}") from error
    if not seen_root:
        seen_root = bool(entries)
    if not seen_root:
        raise ValueError(f"{artifact}: archive contains no bundle entries.")
    return tuple(sorted(entries, key=lambda entry: entry.path))


def _archive_relative_path(raw_name: str, expected_root: str) -> str | None:
    if "\\" in raw_name:
        raise ValueError(f"Desktop archive member uses a backslash path: {raw_name!r}.")
    path = PurePosixPath(raw_name.rstrip("/"))
    if path.is_absolute() or not path.parts:
        raise ValueError(f"Desktop archive member has an unsafe path: {raw_name!r}.")
    if path.parts[0] != expected_root:
        raise ValueError(
            f"Desktop archive member {raw_name!r} is outside expected root {expected_root!r}."
        )
    relative_parts = path.parts[1:]
    if not relative_parts:
        return None
    if any(part in {"", ".", ".."} for part in relative_parts):
        raise ValueError(f"Desktop archive member has an unsafe path: {raw_name!r}.")
    return PurePosixPath(*relative_parts).as_posix()


def _reject_ambiguous_paths(entries: Sequence[InventoryEntry]) -> None:
    exact: set[str] = set()
    folded: dict[str, str] = {}
    for entry in entries:
        if entry.path in exact:
            raise ValueError(f"Desktop archive contains duplicate member {entry.path!r}.")
        exact.add(entry.path)
        key = entry.path.casefold()
        existing = folded.get(key)
        if existing is not None and existing != entry.path:
            raise ValueError(
                f"Desktop archive contains case-colliding members {existing!r} and {entry.path!r}."
            )
        folded[key] = entry.path


def _reject_forbidden_user_data(entries: Sequence[InventoryEntry]) -> None:
    violations = [
        entry.path
        for entry in entries
        if PurePosixPath(entry.path).name.casefold() in FORBIDDEN_USER_DATA_NAMES
    ]
    if violations:
        raise ValueError(f"Desktop archive contains canonical user data: {', '.join(violations)}.")


def _reject_escaping_symlinks(entries: Sequence[InventoryEntry]) -> None:
    entries_by_path = {entry.path: entry for entry in entries}
    known_paths = set(entries_by_path)
    known_directories = {
        PurePosixPath(*PurePosixPath(path).parts[:index]).as_posix()
        for path in known_paths
        for index in range(1, len(PurePosixPath(path).parts))
    }
    for entry in entries:
        if entry.kind == "symlink":
            _resolve_archive_symlink(
                entry.path,
                entries_by_path=entries_by_path,
                known_paths=known_paths,
                known_directories=known_directories,
            )


def _resolve_archive_symlink(
    link_path: str,
    *,
    entries_by_path: Mapping[str, InventoryEntry],
    known_paths: set[str],
    known_directories: set[str],
) -> str:
    """Resolve one archive symlink, including symlinked path components."""
    link = entries_by_path[link_path]
    if link.kind != "symlink":
        raise ValueError(f"Desktop archive member {link_path!r} is not a symbolic link.")
    target = PurePosixPath(link.digest_or_target)
    if target.is_absolute():
        raise ValueError(
            f"Desktop archive symbolic link {link_path!r} has an absolute target."
        )
    initial_parts = (*PurePosixPath(link_path).parent.parts, *target.parts)
    resolved = _resolve_archive_path(
        initial_parts,
        source_link=link_path,
        entries_by_path=entries_by_path,
        active_links=(link_path,),
    )
    if resolved not in known_paths and resolved not in known_directories:
        raise ValueError(
            f"Desktop archive symbolic link {link_path!r} targets missing member {resolved!r}."
        )
    return resolved


def _resolve_archive_path(
    parts: Sequence[str],
    *,
    source_link: str,
    entries_by_path: Mapping[str, InventoryEntry],
    active_links: tuple[str, ...],
) -> str:
    """Resolve a root-relative archive path without allowing root escape or cycles."""
    pending = list(reversed(parts))
    resolved_parts: list[str] = []
    followed_links = list(active_links)
    while pending:
        part = pending.pop()
        if part in {"", "."}:
            continue
        if part == "..":
            if not resolved_parts:
                raise ValueError(
                    f"Desktop archive symbolic link {source_link!r} escapes the bundle root."
                )
            resolved_parts.pop()
            continue

        candidate_path = PurePosixPath(*resolved_parts, part).as_posix()
        candidate = entries_by_path.get(candidate_path)
        if candidate is None or candidate.kind != "symlink":
            resolved_parts.append(part)
            continue
        if candidate_path in followed_links:
            cycle = " -> ".join((*followed_links, candidate_path))
            raise ValueError(
                f"Desktop archive symbolic link {source_link!r} contains a cycle: "
                f"{cycle}."
            )
        target = PurePosixPath(candidate.digest_or_target)
        if target.is_absolute():
            raise ValueError(
                f"Desktop archive symbolic link {candidate_path!r} has an absolute target."
            )
        followed_links.append(candidate_path)
        pending.extend(reversed(target.parts))

    return PurePosixPath(*resolved_parts).as_posix() if resolved_parts else ""


def _verify_required_executable(entries: Sequence[InventoryEntry], platform_tag: str) -> None:
    executable = (
        "Contents/MacOS/Adventure Graph"
        if platform_tag == "macos"
        else "Adventure Graph.exe"
        if platform_tag == "windows"
        else "Adventure Graph"
    )
    matching = [entry for entry in entries if entry.path == executable]
    if len(matching) != 1 or matching[0].kind != "file":
        raise ValueError(f"Desktop archive is missing required executable {executable!r}.")
    if platform_tag != "windows" and not matching[0].mode & 0o111:
        raise ValueError(f"Desktop archive executable {executable!r} is not marked executable.")
