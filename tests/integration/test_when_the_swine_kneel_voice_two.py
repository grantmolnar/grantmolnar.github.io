"""Regression checks for the When the Swine Kneel Voice II pass."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.journal_archive_store import load_journal_archive
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.integration.swine_support import assert_historical_archive_structure
from tests.support.corpus_contracts import assert_rendered_documents_match

pytestmark = pytest.mark.corpus

EXAMPLE = Path("examples/when-the-swine-kneel")
SOURCE = EXAMPLE / "adventure.json"
STATE = EXAMPLE / "play-state.example.json"
ARCHIVE = EXAMPLE / "archives" / "synthetic-complete-playthrough.journal.json"


def test_swine_voice_two_has_a_three_field_source_finish() -> None:
    """Keep the final source edits narrow, concrete, and fresh-company neutral."""
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    revelation = next(
        item
        for item in raw["revelations"]
        if item["id"] == "the-hall-can-restrain-the-offices-destroying-the-evidence"
    )
    deep_bell = next(item for item in raw["encounters"] if item["id"] == "the-deep-bell")
    source_text = SOURCE.read_text(encoding="utf-8")

    assert "Three days before the Hall hearing" in raw["adventure"]["explanation"]
    assert "widen the inspection commission" in revelation["description"]
    for phrase in (
        "The Bell has no will and offers no terms",
        "No instrument below can show what all six lines are doing",
        "There is no fixed allotment of three cycles",
        "The last honest evidence may be a Rillcross herd",
        "Total failure is the moment the reports cease",
    ):
        assert phrase in deep_bell["content"]

    for obsolete in (
        "Three days before the adventure",
        "party\u2019s commission",
        "No monster is required",
        "binary keys",
        "negotiation with a machine",
        "Use the game's ordinary procedures",
        "trick answer",
        "one decisive roll",
        "one unlucky check",
    ):
        assert obsolete not in source_text

    for demonstrator in (
        "Ashlar Company",
        "Mara Venn",
        "Nell Harth",
        "Orris Cale",
        "Sera Dain",
    ):
        assert demonstrator not in source_text


def test_swine_voice_two_preserves_structure_and_both_play_states() -> None:
    """Keep the final voice finish from altering routes, evidence, or recorded play."""
    adventure = load_adventure(SOURCE)
    state = load_play_state(STATE)
    archive = load_journal_archive(ARCHIVE)
    projection = project_play_state(adventure, state)
    report = validate_adventure(adventure)
    source_raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    archive_raw = json.loads(ARCHIVE.read_text(encoding="utf-8"))

    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(adventure.encounters) == 7
    assert len(adventure.revelations) == 10
    assert len(adventure.clues) == 38
    assert len(state.events) == 96
    assert len(archive.play_state.events) == 74
    assert len(projection.visits) == 8
    assert len(projection.spotted_clue_ids) == 25
    assert len(set(adventure.clue_index()) - set(projection.spotted_clue_ids)) == 13
    assert all(item.is_established for item in projection.revelation_progress)
    assert_historical_archive_structure(archive_raw["adventure_snapshot"], source_raw)
    assert archive_raw["archive"]["event_count"] == 74


def test_swine_voice_two_closes_the_individual_sequence() -> None:
    """Keep the final audit, current packet, roadmap, and generated documents aligned."""
    company = (EXAMPLE / "PARTY-DESIGN.md").read_text(encoding="utf-8")
    playthrough = (EXAMPLE / "FULL-PLAYTHROUGH.md").read_text(encoding="utf-8")


    assert "# Demonstration Company: The Ashlar Company" in company

    assert "available node" not in playthrough

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
