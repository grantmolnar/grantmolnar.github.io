"""Remove generated local artifacts without touching authored source."""

from __future__ import annotations

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

_ROOT_NAMES = (
    ".pytest_cache",
    ".ruff_cache",
    ".hypothesis",
    ".import_linter_cache",
    ".mutmut-cache",
    "mutants",
    "htmlcov",
    "coverage.xml",
    ".coverage",
    "dist",
    "build",
)
_ROOT_GLOBS = (".coverage.*",)
_RECURSIVE_DIRECTORY_NAMES = ("__pycache__",)
_RECURSIVE_DIRECTORY_GLOBS = ("*.egg-info",)


def clean_repository(root: Path = PROJECT_ROOT) -> tuple[Path, ...]:
    """Remove the repository's declared generated artifacts and return their paths."""
    root = root.resolve()
    candidates: set[Path] = {root / name for name in _ROOT_NAMES}
    for pattern in _ROOT_GLOBS:
        candidates.update(root.glob(pattern))
    for name in _RECURSIVE_DIRECTORY_NAMES:
        candidates.update(path for path in root.rglob(name) if path.is_dir())
    for pattern in _RECURSIVE_DIRECTORY_GLOBS:
        candidates.update(root.rglob(pattern))

    removed: list[Path] = []
    for path in sorted(candidates, key=lambda item: len(item.parts), reverse=True):
        if not path.exists() and not path.is_symlink():
            continue
        if path.is_symlink() or path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        removed.append(path.relative_to(root))
    return tuple(sorted(removed, key=lambda item: item.as_posix()))


def main() -> int:
    """Clean the current Adventure Graph source tree."""
    removed = clean_repository()
    print(f"Removed {len(removed)} generated artifact path(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
