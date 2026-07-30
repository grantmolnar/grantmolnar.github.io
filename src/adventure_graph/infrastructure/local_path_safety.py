"""Filesystem ownership checks for local beta workspace surfaces."""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import Literal, TypeAlias

_PathKind: TypeAlias = Literal["file", "directory"]


class UnsafeFilesystemLayoutError(ValueError):
    """Raised when a canonical local surface uses a symlink or escapes its owner root."""


def require_contained_file(
    path: Path,
    root: Path,
    *,
    allow_missing: bool = False,
    label: str = "Canonical file",
) -> Path:
    """Return one lexical absolute file path after containment and symlink checks."""
    return _require_contained_path(
        path,
        root,
        expected_kind="file",
        allow_missing=allow_missing,
        label=label,
    )


def require_contained_directory(
    path: Path,
    root: Path,
    *,
    allow_missing: bool = False,
    label: str = "Canonical directory",
) -> Path:
    """Return one lexical absolute directory path after containment and symlink checks."""
    return _require_contained_path(
        path,
        root,
        expected_kind="directory",
        allow_missing=allow_missing,
        label=label,
    )


def require_symlink_free_tree(path: Path, root: Path, *, label: str) -> Path:
    """Require an existing or absent owned directory tree to contain no symlinks."""
    owner = root.resolve(strict=True)
    directory = require_contained_directory(
        path,
        root,
        allow_missing=True,
        label=label,
    )
    if not directory.exists():
        return directory

    pending = [directory]
    while pending:
        current = pending.pop()
        for child in current.iterdir():
            mode = child.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise UnsafeFilesystemLayoutError(
                    f"{label} must not contain symlinks: {child.relative_to(owner)}."
                )
            if stat.S_ISDIR(mode):
                pending.append(child)
            elif not stat.S_ISREG(mode):
                raise UnsafeFilesystemLayoutError(
                    f"{label} contains an unsupported filesystem entry: {child.relative_to(owner)}."
                )
    return directory


def require_paths_within_root(paths: tuple[Path, ...], root: Path, *, label: str) -> None:
    """Require absolute transaction paths to remain lexically below one owner root."""
    owner = root.resolve(strict=True)
    for path in paths:
        candidate = _lexical_absolute(path)
        if candidate != owner and owner not in candidate.parents:
            raise UnsafeFilesystemLayoutError(f"{label} escaped its configured filesystem root.")


def _require_contained_path(
    path: Path,
    root: Path,
    *,
    expected_kind: _PathKind,
    allow_missing: bool,
    label: str,
) -> Path:
    owner = root.resolve(strict=True)
    if not owner.is_dir():
        raise NotADirectoryError(f"Filesystem owner root is not a directory: {owner}.")
    candidate = _lexical_absolute(path)
    if candidate != owner and owner not in candidate.parents:
        raise UnsafeFilesystemLayoutError(f"{label} escaped its configured filesystem root.")

    relative = candidate.relative_to(owner)
    cursor = owner
    for index, part in enumerate(relative.parts):
        cursor /= part
        try:
            mode = cursor.lstat().st_mode
        except FileNotFoundError:
            if allow_missing:
                return candidate
            raise FileNotFoundError(f"{label} does not exist: {candidate}.") from None
        if stat.S_ISLNK(mode):
            raise UnsafeFilesystemLayoutError(
                f"{label} must not use symlinks: {cursor.relative_to(owner)}."
            )
        is_target = index == len(relative.parts) - 1
        if not is_target and not stat.S_ISDIR(mode):
            raise UnsafeFilesystemLayoutError(
                f"{label} has a non-directory ancestor: {cursor.relative_to(owner)}."
            )
        if is_target:
            if expected_kind == "file" and not stat.S_ISREG(mode):
                raise UnsafeFilesystemLayoutError(f"{label} must be a regular file.")
            if expected_kind == "directory" and not stat.S_ISDIR(mode):
                raise UnsafeFilesystemLayoutError(f"{label} must be a directory.")
    return candidate


def _lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))  # noqa: PTH100 -- resolve() would traverse symlinks first.
