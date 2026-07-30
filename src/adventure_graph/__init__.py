"""Adventure Graph package metadata."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

__version__: str

__all__ = ["__version__"]


def __getattr__(name: str) -> str:
    """Return lazily computed module attributes."""
    if name == "__version__":
        try:
            return version("adventure-graph")
        except PackageNotFoundError:
            return "0.0.0+unknown"
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
