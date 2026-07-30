"""Regression checks for the When the Swine Kneel introductions-I pass."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.integration.swine_support import assert_historical_archive_structure
from tests.support.corpus_contracts import assert_rendered_documents_match

pytestmark = pytest.mark.corpus

EXAMPLE = Path("examples/when-the-swine-kneel")
SOURCE = EXAMPLE / "adventure.json"
STATE = EXAMPLE / "play-state.example.json"
ARCHIVE = EXAMPLE / "archives" / "synthetic-complete-playthrough.journal.json"


def test_swine_encounter_introductions_one_are_live_first_arrivals() -> None:
    """Keep the first pass's active pressures through later compression."""
    adventure = load_adventure(SOURCE)
    encounters = adventure.encounter_index()
    openings = [encounter.opening_view for encounter in adventure.encounters]

    assert len(set(openings)) == 7
    expected_pressures = {
        "the-hall-of-petitions": "condemnation order",
        "southgate-stockyards": "cull crew",
        "the-college-of-civic-measure": "Water Office",
        "rillcross-farm-belt": "a child remains",
        "the-chapel-of-the-first-survey": "custody agreement",
        "the-nine-mile-pump-house": "A pump cavitates",
        "the-deep-bell": "the answers are already diverging",
    }
    for encounter_id, phrase in expected_pressures.items():
        assert phrase in encounters[encounter_id].opening_view

    combined = "\n".join(openings)
    for demonstrator in (
        "Ashlar Company",
        "Mara Venn",
        "Nell Harth",
        "Orris Cale",
        "Sera Dain",
    ):
        assert demonstrator not in combined


def test_swine_encounter_introductions_one_records_the_pass_contract() -> None:
    """Keep the audit, roadmap, source snapshot, and runtime baseline aligned."""
    adventure = load_adventure(SOURCE)
    state = load_play_state(STATE)
    projection = project_play_state(adventure, state)
    report = validate_adventure(adventure)
    archive_raw = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    source_raw = json.loads(SOURCE.read_text(encoding="utf-8"))


    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(adventure.encounters) == 7
    assert len(adventure.revelations) == 10
    assert len(adventure.clues) == 38
    assert len(state.events) == 96
    assert len(projection.spotted_clue_ids) == 25
    assert len(set(adventure.clue_index()) - set(projection.spotted_clue_ids)) == 13
    assert_historical_archive_structure(archive_raw["adventure_snapshot"], source_raw)
    assert archive_raw["archive"]["event_count"] == 74


def test_swine_introductions_packet_reproduces_exactly() -> None:
    """Keep all thirteen generated documents synchronized with the openings."""
    adventure = load_adventure(SOURCE)
    state = load_play_state(STATE)
    documents = render_adventure_documents(
        adventure,
        validate_adventure(adventure),
        state,
    )

    assert len(documents) == 35
    assert_rendered_documents_match(
        documents, EXAMPLE / "generated"
    )


def test_swine_encounter_introductions_two_form_a_varied_civic_sequence() -> None:
    """Protect the compressed openings and their distinct dramatic engines."""
    adventure = load_adventure(SOURCE)
    encounters = adventure.encounter_index()
    openings = [encounter.opening_view for encounter in adventure.encounters]

    assert len(set(openings)) == 7
    assert sum(len(opening.split()) for opening in openings) == 546
    assert all(70 <= len(opening.split()) <= 88 for opening in openings)

    expected_phrases = {
        "the-hall-of-petitions": "waits for a name beneath the finding",
        "southgate-stockyards": "the whole yard lowers faster than the gates can be moved",
        "the-college-of-civic-measure": "the final trace while its edge blackens",
        "rillcross-farm-belt": "passing it hand to hand toward the hole",
        "the-chapel-of-the-first-survey": "no one has signed it",
        "the-nine-mile-pump-house": "the river lifts beneath the floor",
        "the-deep-bell": "The first message reaches the chamber",
    }
    for encounter_id, phrase in expected_phrases.items():
        assert phrase in encounters[encounter_id].opening_view

    assert not any("“" in opening or "”" in opening for opening in openings)


def test_swine_encounter_introductions_two_preserve_fresh_play_and_route_state() -> None:
    """Keep the terminal arrival earned and the Ashlar route noncanonical."""
    adventure = load_adventure(SOURCE)
    combined = "\n".join(encounter.opening_view for encounter in adventure.encounters)
    deep_bell = adventure.encounter_index()["the-deep-bell"].opening_view

    for demonstrator in (
        "Ashlar Company",
        "Mara Venn",
        "Nell Harth",
        "Orris Cale",
        "Sera Dain",
    ):
        assert demonstrator not in combined

    for route_state in (
        "third-line pigs have left water",
        "Rillcross",
        "College needle",
        "answers are already diverging",
    ):
        assert route_state in deep_bell


def test_swine_encounter_introductions_two_records_voice_one_handoff() -> None:
    """Keep the audit, roadmap, README, and unchanged runtime baseline aligned."""
    adventure = load_adventure(SOURCE)
    state = load_play_state(STATE)
    projection = project_play_state(adventure, state)
    report = validate_adventure(adventure)


    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(adventure.encounters) == 7
    assert len(adventure.revelations) == 10
    assert len(adventure.clues) == 38
    assert len(state.events) == 96
    assert len(projection.spotted_clue_ids) == 25
    assert len(set(adventure.clue_index()) - set(projection.spotted_clue_ids)) == 13
