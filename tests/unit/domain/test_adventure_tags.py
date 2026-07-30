"""Tests for structured adventure discovery tags."""

from __future__ import annotations

from typing import Any

import pytest

from adventure_graph.domain.adventure import AdventureTags


def test_adventure_tags_accept_open_ranges_and_structured_facets() -> None:
    tags = AdventureTags(
        genres=("Investigation",),
        game_systems=("System-agnostic",),
        party_size_min=3,
        combat_intensity="light",
        keywords=("Deadline",),
    )

    assert tags.party_size_min == 3
    assert tags.party_size_max is None
    assert tags.combat_intensity == "light"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"party_size_min": 5, "party_size_max": 3}, "minimum cannot exceed"),
        ({"level_min": 0}, "minimum must be positive"),
        ({"genres": ("Investigation", "investigation")}, "must be unique"),
        ({"keywords": (" Deadline",)}, "nonempty and trimmed"),
        ({"combat_intensity": "constant"}, "unsupported"),
    ],
)
def test_adventure_tags_reject_malformed_facets(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        AdventureTags(**kwargs)
