"""Build and verify portable Adventure Graph source snapshots."""

from __future__ import annotations

import argparse
import hashlib
import stat
import sys
import zipfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = "adventure-graph"
WINDOWS_LEGACY_PATH_LIMIT_CHARS = 259
SUPPORTED_EXTRACTION_PREFIX_CHARS = 120
MAX_ARCHIVE_MEMBER_PATH_CHARS = (
    WINDOWS_LEGACY_PATH_LIMIT_CHARS - SUPPORTED_EXTRACTION_PREFIX_CHARS - 1
)
MAX_REPOSITORY_RELATIVE_PATH_CHARS = MAX_ARCHIVE_MEMBER_PATH_CHARS - len(ARCHIVE_ROOT) - 1
_FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
_REQUIRED_MEMBERS = {
    "BETA-TERMS.md",
    "README.md",
    "pyproject.toml",
    "src/adventure_graph/__init__.py",
}
_EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".hypothesis",
    ".import_linter_cache",
    ".mutmut-cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "mutants",
    "node_modules",
}
_EXCLUDED_FILE_NAMES = {
    ".coverage",
    "coverage.xml",
}


@dataclass(frozen=True)
class TreeAudit:
    """Measured source-tree path facts for one snapshot candidate."""

    file_count: int
    longest_relative_path: str
    longest_relative_path_chars: int
    longest_member_path: str
    longest_member_path_chars: int


@dataclass(frozen=True)
class SnapshotEvidence:
    """Verified archive facts for one source snapshot."""

    archive: Path
    archive_sha256: str
    file_count: int
    longest_member_path: str
    longest_member_path_chars: int
    supported_extraction_prefix_chars: int


def _is_excluded(relative: Path) -> bool:
    parts = relative.parts
    if any(part in _EXCLUDED_DIRECTORY_NAMES for part in parts):
        return True
    if any(part.endswith(".egg-info") for part in parts):
        return True
    if relative.name in _EXCLUDED_FILE_NAMES:
        return True
    if relative.name.startswith(".coverage."):
        return True
    if relative.name == ".env" or (
        relative.name.startswith(".env.") and relative.name != ".env.example"
    ):
        return True
    return False


def snapshot_files(source_root: Path = PROJECT_ROOT) -> tuple[Path, ...]:
    """Return the regular files admitted to a source snapshot."""

    root = source_root.resolve()
    files: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if _is_excluded(relative):
            continue
        if path.is_symlink():
            raise ValueError(f"Source snapshot may not contain symbolic link {relative.as_posix()!r}.")
        if path.is_file():
            files.append(path)
    return tuple(sorted(files, key=lambda path: path.relative_to(root).as_posix()))


def audit_source_tree(source_root: Path = PROJECT_ROOT) -> TreeAudit:
    """Validate source paths against the portable archive budget."""

    root = source_root.resolve()
    files = snapshot_files(root)
    if not files:
        raise ValueError("Source snapshot candidate contains no files.")

    relative_paths = [path.relative_to(root).as_posix() for path in files]
    _reject_case_collisions(relative_paths, subject="source tree")
    longest_relative = max(relative_paths, key=lambda value: (len(value), value))
    longest_member = f"{ARCHIVE_ROOT}/{longest_relative}"

    if len(longest_relative) > MAX_REPOSITORY_RELATIVE_PATH_CHARS:
        raise ValueError(
            "Source path exceeds the portable repository-relative budget of "
            f"{MAX_REPOSITORY_RELATIVE_PATH_CHARS} characters: {longest_relative!r} "
            f"({len(longest_relative)} characters)."
        )
    if len(longest_member) > MAX_ARCHIVE_MEMBER_PATH_CHARS:
        raise ValueError(
            "Source archive member exceeds the portable member budget of "
            f"{MAX_ARCHIVE_MEMBER_PATH_CHARS} characters: {longest_member!r}."
        )

    return TreeAudit(
        file_count=len(files),
        longest_relative_path=longest_relative,
        longest_relative_path_chars=len(longest_relative),
        longest_member_path=longest_member,
        longest_member_path_chars=len(longest_member),
    )


def build_source_snapshot(
    output: Path,
    *,
    source_root: Path = PROJECT_ROOT,
) -> SnapshotEvidence:
    """Create a deterministic ZIP with a short, stable internal root."""

    root = source_root.resolve()
    audit_source_tree(root)
    files = snapshot_files(root)
    destination = output.resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.tmp")
    temporary.unlink(missing_ok=True)

    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            for path in files:
                relative = path.relative_to(root).as_posix()
                member = f"{ARCHIVE_ROOT}/{relative}"
                info = zipfile.ZipInfo(member, date_time=_FIXED_ZIP_TIMESTAMP)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                archive.writestr(info, path.read_bytes(), compresslevel=9)
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    return verify_source_snapshot(destination)


def verify_source_snapshot(
    archive_path: Path,
    *,
    extraction_prefix_chars: int = SUPPORTED_EXTRACTION_PREFIX_CHARS,
) -> SnapshotEvidence:
    """Verify archive safety, identity, and the declared Windows path budget."""

    if extraction_prefix_chars < 0:
        raise ValueError("Extraction-prefix length must be nonnegative.")
    archive_path = archive_path.resolve()
    names: list[str] = []
    file_count = 0

    try:
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            if not infos:
                raise ValueError(f"Source snapshot {archive_path} is empty.")
            bad_member = archive.testzip()
            if bad_member is not None:
                raise ValueError(f"Source snapshot has a failed CRC member: {bad_member!r}.")

            for info in infos:
                if info.flag_bits & 0x1:
                    raise ValueError(f"Encrypted source member is not allowed: {info.filename!r}.")
                if info.is_dir():
                    raise ValueError(
                        f"Source snapshot contains unnecessary directory member {info.filename!r}."
                    )
                _validate_member_path(info.filename, extraction_prefix_chars=extraction_prefix_chars)
                unix_mode = info.external_attr >> 16
                if stat.S_IFMT(unix_mode) == stat.S_IFLNK:
                    raise ValueError(
                        f"Source snapshot may not contain symbolic link {info.filename!r}."
                    )
                names.append(info.filename)
                file_count += 1
    except (OSError, zipfile.BadZipFile) as error:
        raise ValueError(f"Could not inspect source snapshot {archive_path}: {error}") from error

    _reject_case_collisions(names, subject="source snapshot")
    relative_members = {name.removeprefix(f"{ARCHIVE_ROOT}/") for name in names}
    missing = sorted(_REQUIRED_MEMBERS.difference(relative_members))
    if missing:
        raise ValueError(f"Source snapshot is missing required members: {', '.join(missing)}.")

    longest_member = max(names, key=lambda value: (len(value), value))
    return SnapshotEvidence(
        archive=archive_path,
        archive_sha256=_sha256_file(archive_path),
        file_count=file_count,
        longest_member_path=longest_member,
        longest_member_path_chars=len(longest_member),
        supported_extraction_prefix_chars=extraction_prefix_chars,
    )


def _validate_member_path(raw_name: str, *, extraction_prefix_chars: int) -> None:
    if "\\" in raw_name:
        raise ValueError(f"Source snapshot member uses a backslash path: {raw_name!r}.")
    path = PurePosixPath(raw_name)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"Source snapshot member has an unsafe path: {raw_name!r}.")
    if path.parts[0] != ARCHIVE_ROOT or len(path.parts) == 1:
        raise ValueError(
            f"Source snapshot member {raw_name!r} is outside the required root "
            f"{ARCHIVE_ROOT!r}."
        )
    if len(raw_name) > MAX_ARCHIVE_MEMBER_PATH_CHARS:
        raise ValueError(
            f"Source snapshot member exceeds {MAX_ARCHIVE_MEMBER_PATH_CHARS} characters: "
            f"{raw_name!r} ({len(raw_name)} characters)."
        )
    extracted_chars = extraction_prefix_chars + 1 + len(raw_name)
    if extracted_chars > WINDOWS_LEGACY_PATH_LIMIT_CHARS:
        raise ValueError(
            "Source snapshot member exceeds the declared extracted-path budget: "
            f"{raw_name!r} would require {extracted_chars} characters with a "
            f"{extraction_prefix_chars}-character destination prefix."
        )


def _reject_case_collisions(paths: Iterable[str], *, subject: str) -> None:
    exact: set[str] = set()
    folded: dict[str, str] = {}
    for path in paths:
        if path in exact:
            raise ValueError(f"Duplicate member in {subject}: {path!r}.")
        exact.add(path)
        key = path.casefold()
        existing = folded.get(key)
        if existing is not None:
            raise ValueError(f"Case-colliding paths in {subject}: {existing!r} and {path!r}.")
        folded[key] = path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _print_tree_audit(audit: TreeAudit) -> None:
    print(f"Source files: {audit.file_count}")
    print(
        "Longest repository-relative path: "
        f"{audit.longest_relative_path_chars}/{MAX_REPOSITORY_RELATIVE_PATH_CHARS} "
        f"({audit.longest_relative_path})"
    )
    print(
        "Longest archive member: "
        f"{audit.longest_member_path_chars}/{MAX_ARCHIVE_MEMBER_PATH_CHARS} "
        f"({audit.longest_member_path})"
    )
    print(
        "Supported extraction destination prefix: "
        f"{SUPPORTED_EXTRACTION_PREFIX_CHARS} characters"
    )


def _print_evidence(evidence: SnapshotEvidence) -> None:
    print(f"Verified source snapshot: {evidence.archive}")
    print(f"Files: {evidence.file_count}")
    print(f"SHA-256: {evidence.archive_sha256}")
    print(
        "Longest archive member: "
        f"{evidence.longest_member_path_chars}/{MAX_ARCHIVE_MEMBER_PATH_CHARS} "
        f"({evidence.longest_member_path})"
    )
    print(
        "Supported extraction destination prefix: "
        f"{evidence.supported_extraction_prefix_chars} characters"
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="Audit the current source tree path budget.")
    audit.add_argument("--source-root", type=Path, default=PROJECT_ROOT)

    build = subparsers.add_parser("build", help="Build and verify a portable source snapshot.")
    build.add_argument("output", type=Path)
    build.add_argument("--source-root", type=Path, default=PROJECT_ROOT)

    verify = subparsers.add_parser("verify", help="Verify a portable source snapshot.")
    verify.add_argument("archive", type=Path)
    verify.add_argument(
        "--extraction-prefix-chars",
        type=int,
        default=SUPPORTED_EXTRACTION_PREFIX_CHARS,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the source-snapshot command-line interface."""

    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "audit":
            _print_tree_audit(audit_source_tree(arguments.source_root))
        elif arguments.command == "build":
            _print_evidence(
                build_source_snapshot(arguments.output, source_root=arguments.source_root)
            )
        else:
            _print_evidence(
                verify_source_snapshot(
                    arguments.archive,
                    extraction_prefix_chars=arguments.extraction_prefix_chars,
                )
            )
    except ValueError as error:
        print(f"Source snapshot error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
