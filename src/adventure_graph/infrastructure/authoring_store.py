"""Coordinated persistence for authored changes and related play journals."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from adventure_graph.infrastructure.adventure_store import adventure_data
from adventure_graph.infrastructure.atomic_files import write_json_objects
from adventure_graph.infrastructure.json_values import JsonObject
from adventure_graph.infrastructure.play_state_store import play_state_data


def save_authoring_bundle(
    adventure_path: Path,
    adventure: Adventure,
    play_states: Mapping[Path, PlayState],
) -> None:
    """Commit one adventure and related play-state rewrites as a coordinated update."""
    payloads: dict[Path, JsonObject] = {adventure_path: adventure_data(adventure)}
    for state_path, state in play_states.items():
        if state_path in payloads:
            raise ValueError(f"Duplicate authoring destination {state_path}.")
        payloads[state_path] = play_state_data(state)
    write_json_objects(payloads)
