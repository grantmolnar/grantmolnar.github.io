"""Property evidence for canonical adventure and journal persistence."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("hypothesis")

from hypothesis import given, settings
from tests.support.property_strategies import (
    JournalCase,
    authored_adventures,
    valid_journal_cases,
)

from adventure_graph.domain.adventure import Adventure
from adventure_graph.infrastructure.adventure_store import (
    adventure_data,
    adventure_from_data,
    load_adventure,
    save_adventure,
)
from adventure_graph.infrastructure.play_state_store import (
    load_play_state,
    play_state_data,
    play_state_from_data,
    save_play_state,
)

pytestmark = pytest.mark.property


@settings(max_examples=60, deadline=None, derandomize=True)
@given(adventure=authored_adventures())
def test_adventure_canonical_object_round_trip_is_idempotent(adventure: Adventure) -> None:
    """Canonical object encoding must preserve every owned field and authored order."""
    encoded = adventure_data(adventure)
    decoded = adventure_from_data(encoded)

    assert decoded == adventure
    assert adventure_data(decoded) == encoded


@settings(max_examples=35, deadline=None, derandomize=True)
@given(adventure=authored_adventures())
def test_adventure_file_round_trip_is_byte_stable(tmp_path: Path, adventure: Adventure) -> None:
    """Loading and resaving canonical adventure JSON must not create textual drift."""
    path = tmp_path / "adventure.json"
    save_adventure(path, adventure)
    first = path.read_bytes()

    save_adventure(path, load_adventure(path))

    assert path.read_bytes() == first


@settings(max_examples=60, deadline=None, derandomize=True)
@given(case=valid_journal_cases())
def test_play_state_canonical_object_round_trip_is_idempotent(case: JournalCase) -> None:
    """Every public-command journal must survive canonical object conversion exactly."""
    encoded = play_state_data(case.state)
    decoded = play_state_from_data(encoded)

    assert decoded == case.state
    assert play_state_data(decoded) == encoded


@settings(max_examples=35, deadline=None, derandomize=True)
@given(case=valid_journal_cases())
def test_play_state_file_round_trip_is_byte_stable(tmp_path: Path, case: JournalCase) -> None:
    """Loading and resaving canonical journal JSON must preserve exact bytes."""
    path = tmp_path / "play-state.json"
    save_play_state(path, case.state)
    first = path.read_bytes()

    save_play_state(path, load_play_state(path))

    assert path.read_bytes() == first
