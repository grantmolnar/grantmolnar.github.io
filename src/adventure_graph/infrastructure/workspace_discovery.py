"""Canonical filesystem discovery policy for beta workspaces."""

from __future__ import annotations

from pathlib import Path

_ADVENTURE_FILE = "adventure.json"


def discover_workspace_adventure_sources(root: Path) -> tuple[Path, ...]:
    """Return canonical adventure sources owned directly by one workspace root.

    A workspace may be a project itself through ``root/adventure.json`` and may also
    contain visible direct child project directories. Discovery does not recurse,
    follow directory symlinks, or treat arbitrary ``*.adventure.json`` files as
    workspace projects.
    """
    resolved_root = root.resolve()
    candidates: list[Path] = []
    root_source = resolved_root / _ADVENTURE_FILE
    if _is_owned_regular_file(root_source, resolved_root):
        candidates.append(root_source.resolve())

    for child in sorted(resolved_root.iterdir(), key=lambda path: path.name.casefold()):
        if child.name.startswith(".") or child.is_symlink() or not child.is_dir():
            continue
        source = child / _ADVENTURE_FILE
        if _is_owned_regular_file(source, resolved_root):
            candidates.append(source.resolve())
    return tuple(candidates)


def _is_owned_regular_file(path: Path, root: Path) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    try:
        resolved = path.resolve(strict=True)
    except OSError:
        return False
    return resolved == root or root in resolved.parents
