"""Packaged browser-script loading for the local authoring shell."""

from functools import lru_cache
from importlib.resources import files


@lru_cache(maxsize=1)
def load_app_js() -> str:
    """Load the packaged interface script once per process."""
    return (
        files("adventure_graph.interfaces.web.assets")
        .joinpath("app.js")
        .read_text(encoding="utf-8")
    )
