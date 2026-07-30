"""Shared path helpers for repository-wide tests."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "src"
PACKAGE_ROOT = SRC_ROOT / "adventure_graph"
PACKAGE_NAME = "adventure_graph"


def iter_python_files(root: Path) -> Iterator[Path]:
    """Yield non-hidden Python files below a root in stable order."""
    if not root.exists():
        return
    for path in sorted(root.rglob("*.py")):
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        yield path


def module_name_from_src_path(path: Path) -> str:
    """Return the importable module name for a file under src/."""
    relative_path = path.relative_to(SRC_ROOT)
    parts = list(relative_path.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)
