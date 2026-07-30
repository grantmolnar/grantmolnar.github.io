"""Regression checks for the When the Swine Kneel coherence pass."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from tests.integration.swine_support import assert_historical_archive_structure

pytestmark = pytest.mark.corpus

EXAMPLE = Path("examples/when-the-swine-kneel")
SOURCE = EXAMPLE / "adventure.json"
ARCHIVE = EXAMPLE / "archives" / "synthetic-complete-playthrough.journal.json"


def test_swine_coherence_contract_preserves_structure_and_repairs_causality() -> None:
    """Protect the recent catalyst, divided knowledge, bounded authority, and finale rule."""
    adventure = load_adventure(SOURCE)
    report = validate_adventure(adventure)
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    source_text = SOURCE.read_text(encoding="utf-8")

    assert len(adventure.encounters) == 7
    assert len(adventure.revelations) == 10
    assert len(adventure.clues) == 38
    assert report.is_valid
    assert report.edge_connectivity == 3

    assert "Three days before the Hall hearing" in raw["adventure"]["explanation"]
    assert "uninterrupted high-load operation" in raw["adventure"]["explanation"]
    assert (
        "did not possess the surveyors' lost six-line doctrine" in raw["adventure"]["explanation"]
    )
    assert "post a civic bond or name a recognized sponsor" in source_text
    assert "It does not interrupt water service" in source_text
    assert "Six sounding lines run from its chamber" in source_text
    assert "Every line must be heard; every line need not survive" in source_text
    assert "No instrument below can show what all six lines are doing" in source_text
    assert "Ashlar Company" not in source_text


def test_swine_coherence_packet_and_roadmap_are_synchronized() -> None:
    """Keep the source snapshot, audit, current route, and next stage aligned."""
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    archive = json.loads(ARCHIVE.read_text(encoding="utf-8"))

    assert_historical_archive_structure(archive["adventure_snapshot"], source)
    assert archive["archive"]["event_count"] == 74
    assert len(archive["play_state"]["events"]) == 74
