"""Tests for adventure-owned reference values and associations."""

from __future__ import annotations

from typing import Any, cast

import pytest
from tests.support.adventures import PERSON_REFERENCE_ID

from adventure_graph.domain.adventure import Reference, ReferenceLink


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"id": "not-a-uuid"}, "canonical UUIDv4"),
        ({"kind": "faction"}, "kind is unsupported"),
        ({"title": ""}, "nonempty trimmed"),
        ({"title": " Cora Pike"}, "nonempty trimmed"),
        ({"aliases": ("",)}, "aliases must be nonempty trimmed"),
        ({"aliases": ("Keeper", "keeper")}, "aliases must be unique"),
        ({"aliases": ("cora pike",)}, "must not duplicate the title"),
        ({"tags": (" witness",)}, "tags must be nonempty trimmed"),
        ({"tags": ("Staff", "staff")}, "tags must be unique"),
        ({"summary": 3}, "summary must be a string"),
        ({"content": []}, "content must be a string"),
    ],
)
def test_reference_rejects_malformed_values(changes: dict[str, Any], message: str) -> None:
    values: dict[str, Any] = {
        "id": PERSON_REFERENCE_ID,
        "kind": "person",
        "title": "Cora Pike",
    }
    values.update(changes)

    with pytest.raises(ValueError, match=message):
        Reference(**values)


def test_reference_link_accepts_blank_context_and_rejects_malformed_values() -> None:
    assert ReferenceLink(PERSON_REFERENCE_ID).context == ""

    with pytest.raises(ValueError, match="canonical UUIDv4"):
        ReferenceLink("cora-pike")
    with pytest.raises(ValueError, match="context must be a string"):
        ReferenceLink(PERSON_REFERENCE_ID, cast(Any, 4))
