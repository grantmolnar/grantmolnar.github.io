"""Load adventure templates shipped with the runtime package."""

from __future__ import annotations

from importlib.resources import files

from adventure_graph.domain.adventure import Adventure
from adventure_graph.infrastructure.adventure_store import adventure_from_data
from adventure_graph.infrastructure.json_values import decode_object_bytes


def load_glass_saint_template() -> Adventure:
    """Return the packaged Glass Saint sample adventure."""
    source = files("adventure_graph.resources").joinpath("the-glass-saint.adventure.json")
    return adventure_from_data(
        decode_object_bytes(source.read_bytes(), "packaged Glass Saint sample"),
        source="packaged Glass Saint sample",
    )


__all__ = ["load_glass_saint_template"]
