"""Shared paths and snapshot helpers for Glass Saint integration tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

EXAMPLE_PATH = Path("examples/the-glass-saint.adventure.json")
DIRECTORY_ADVENTURE_PATH = Path("examples/the-glass-saint/adventure.json")
PUBLIC_LEDGER_PATH = Path("examples/the-glass-saint/PUBLIC-PRESSURE-AND-WITNESS-LEDGER.md")
RITUAL_SHEET_PATH = Path("examples/the-glass-saint/RITUAL-AND-BELL-OPERATING-SHEET.md")
MANOR_SHEET_PATH = Path("examples/the-glass-saint/VALE-MANOR-AND-AFTERMATH-OPERATING-SHEET.md")
ROUTE_SHEET_PATH = Path("examples/the-glass-saint/GM-ROUTE-AND-CONTINUITY-SHEET.md")
STATE_PATH = Path("examples/the-glass-saint/play-state.example.json")
ARCHIVE_PATH = Path(
    "examples/the-glass-saint/archives/counterseal-witnesses-demonstrated-playthrough.journal.json"
)
PARTY_PATH = Path("examples/the-glass-saint/PARTY-DESIGN.md")
PLAYTHROUGH_PATH = Path("examples/the-glass-saint/FULL-PLAYTHROUGH.md")
PLAY_SUMMARY_PATH = Path("examples/the-glass-saint/generated/05-play-summary.md")
RESOURCE_PATH = Path("src/adventure_graph/resources/the-glass-saint.adventure.json")


def without_references(adventure):
    """Project current authored data back to a reference-free current snapshot."""
    return replace(
        adventure,
        references=(),
        encounters=tuple(
            replace(encounter, reference_links=()) for encounter in adventure.encounters
        ),
    )


def assert_historical_archive_structure(snapshot, adventure) -> None:
    """Keep immutable snapshots structurally aligned after later prose passes."""
    current = without_references(adventure)
    assert replace(snapshot, encounters=()) == replace(current, encounters=())

    def strip_prose(encounter):
        return replace(encounter, opening_view="", content="")

    assert tuple(map(strip_prose, snapshot.encounters)) == tuple(
        map(strip_prose, current.encounters)
    )
