"""Packaged stylesheet loading for the local authoring shell."""

from functools import lru_cache
from importlib.resources import files


@lru_cache(maxsize=1)
def load_app_css() -> str:
    """Load the packaged interface stylesheet once per process."""
    return (
        files("adventure_graph.interfaces.web.assets")
        .joinpath("app.css")
        .read_text(encoding="utf-8")
    )
