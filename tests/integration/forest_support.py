"""Shared historical-snapshot helpers for the Forest corpus tests."""

from __future__ import annotations

from dataclasses import replace

from adventure_graph.domain.adventure import Adventure, AdventureTags

VOICE_III_ENCOUNTER_IDS = (
    "camp-under-new-leaves",
    "hollow-of-kept-voices",
    "root-breath-chamber",
    "crown-of-unfallen-rain",
    "glass-verge",
)


def without_references(adventure: Adventure) -> Adventure:
    """Project current authored data back to its reference-free source shape."""
    return replace(
        adventure,
        references=(),
        encounters=tuple(
            replace(encounter, reference_links=()) for encounter in adventure.encounters
        ),
    )


def assert_historical_archive_structure(snapshot: Adventure, adventure: Adventure) -> None:
    """Keep the immutable archive aligned outside the five Voice III bodies."""
    current = replace(without_references(adventure), tags=AdventureTags())
    assert replace(snapshot, encounters=()) == replace(current, encounters=())

    def strip_content(encounter):
        return replace(encounter, content="")

    assert tuple(map(strip_content, snapshot.encounters)) == tuple(
        map(strip_content, current.encounters)
    )
    assert tuple(
        current_encounter.id
        for historical_encounter, current_encounter in zip(
            snapshot.encounters, current.encounters, strict=True
        )
        if historical_encounter.content != current_encounter.content
    ) == VOICE_III_ENCOUNTER_IDS
