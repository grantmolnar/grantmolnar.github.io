"""Canonical companion paths for one local adventure source."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_ADVENTURE_SUFFIX = ".adventure.json"


@dataclass(frozen=True, slots=True)
class LocalProjectPaths:
    """Filesystem surfaces associated with one authored adventure document."""

    adventure: Path
    play_state: Path
    generated: Path
    archives: Path


def local_project_paths(adventure_path: Path) -> LocalProjectPaths:
    """Return collision-free companion paths for a local adventure document.

    Canonical directory projects use ``adventure.json`` beside ``play-state.json``,
    ``generated/``, and ``archives/``. Standalone adventure documents namespace
    each companion surface from the source filename.
    """
    if adventure_path.name == "adventure.json":
        return LocalProjectPaths(
            adventure=adventure_path,
            play_state=adventure_path.with_name("play-state.json"),
            generated=adventure_path.parent / "generated",
            archives=adventure_path.parent / "archives",
        )

    name = adventure_path.name
    namespace = (
        name[: -len(_ADVENTURE_SUFFIX)] if name.endswith(_ADVENTURE_SUFFIX) else adventure_path.stem
    )
    return LocalProjectPaths(
        adventure=adventure_path,
        play_state=adventure_path.with_name(f"{namespace}.play-state.json"),
        generated=adventure_path.parent / f"{namespace}.generated",
        archives=adventure_path.parent / f"{namespace}.archives",
    )
