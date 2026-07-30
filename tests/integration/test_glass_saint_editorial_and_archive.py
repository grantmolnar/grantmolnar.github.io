"""Editorial and demonstrated-play regression checks for The Glass Saint."""

from __future__ import annotations

from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents, render_play_summary
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.journal_archive_store import load_journal_archive
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.integration.glass_saint_support import (
    ARCHIVE_PATH,
    DIRECTORY_ADVENTURE_PATH,
    EXAMPLE_PATH,
    MANOR_SHEET_PATH,
    PARTY_PATH,
    PLAY_SUMMARY_PATH,
    PLAYTHROUGH_PATH,
    PUBLIC_LEDGER_PATH,
    RESOURCE_PATH,
    STATE_PATH,
    assert_historical_archive_structure,
)

pytestmark = pytest.mark.corpus


def test_glass_saint_encounter_introductions_two_are_varied_route_open_and_synchronized() -> None:
    """Protect the compressed sequence, differentiated engines, and current mirrors."""
    adventure = load_adventure(EXAMPLE_PATH)
    encounters = adventure.encounter_index()
    openings = [encounter.opening_view for encounter in adventure.encounters]

    assert len(set(openings)) == 9
    assert all(55 <= len(opening.split()) <= 72 for opening in openings)
    assert sum(len(opening.split()) for opening in openings) == 571
    expected_phrases = {
        "the-shattered-gallery": "before anyone can close the room",
        "the-procession-court": "disappears into traffic",
        "the-archive-vault": "custody log waits for its first name",
        "the-trustees-chamber": "either order to become the city\u2019s answer",
        "the-west-infirmary": "No family has signed away",
        "the-house-of-petitions": "keep every sheet moving",
        "the-bell-chapel": "Every rope answers",
        "the-grand-belfry": "hauling every command toward bronze",
        "vale-manor": "every pane returns a different face",
    }
    for encounter_id, phrase in expected_phrases.items():
        assert phrase in encounters[encounter_id].opening_view
    belfry_opening = encounters["the-grand-belfry"].opening_view
    for current_name in ("Mela Fen", "Rian Voss", "Karel Venn"):
        assert current_name in belfry_opening
    for retired_name in ("Mela Venn", "Rian Holt", "Karel Dune"):
        assert retired_name not in belfry_opening


    archive = load_journal_archive(ARCHIVE_PATH)
    assert_historical_archive_structure(archive.adventure_snapshot, adventure)
    assert EXAMPLE_PATH.read_bytes() == RESOURCE_PATH.read_bytes()
    assert EXAMPLE_PATH.read_bytes() == DIRECTORY_ADVENTURE_PATH.read_bytes()

    documents = render_adventure_documents(adventure, validate_adventure(adventure))
    for encounter in adventure.encounters:
        assert encounter.opening_view in documents[f"encounters/{encounter.id}.md"]


def test_glass_saint_voice_one_compresses_source_without_reopening_structure() -> None:
    """Protect the source-level voice pass, unchanged authored objects, and next stage."""
    adventure = load_adventure(EXAMPLE_PATH)
    archive = load_journal_archive(ARCHIVE_PATH)

    overview_words = sum(
        len(text.split()) for text in (adventure.synopsis, adventure.premise, adventure.explanation)
    )
    summary_words = sum(len(encounter.summary.split()) for encounter in adventure.encounters)
    opening_words = sum(len(encounter.opening_view.split()) for encounter in adventure.encounters)
    content_words = sum(len(encounter.content.split()) for encounter in adventure.encounters)
    revelation_words = sum(len(item.description.split()) for item in adventure.revelations)
    clue_words = sum(len(item.description.split()) for item in adventure.clues)

    assert (
        overview_words,
        summary_words,
        opening_words,
        content_words,
        revelation_words,
        clue_words,
    ) == (1461, 186, 571, 5958, 360, 1234)
    assert len(adventure.encounters) == 9
    assert len(adventure.revelations) == 16
    assert len(adventure.clues) == 69
    assert validate_adventure(adventure).edge_connectivity == 5
    assert_historical_archive_structure(archive.adventure_snapshot, adventure)
    assert len(archive.play_state.events) == 116


    assert EXAMPLE_PATH.read_bytes() == RESOURCE_PATH.read_bytes()
    assert EXAMPLE_PATH.read_bytes() == DIRECTORY_ADVENTURE_PATH.read_bytes()

    documents = render_adventure_documents(adventure, validate_adventure(adventure))
    assert "The investigation contests who may make a fact public" in documents["00-overview.md"]
    assert (
        "Sort the scene into three evidence chains"
        in documents["encounters/the-shattered-gallery.md"]
    )
    assert (
        "A sounded note cannot be unsounded; every later note remains contestable"
        in documents["encounters/the-grand-belfry.md"]
    )


def test_glass_saint_voice_passes_reconcile_packet_and_reference_library() -> None:
    """Protect the final source finish and bounded post-reference voice repair."""
    adventure = load_adventure(EXAMPLE_PATH)
    archive = load_journal_archive(ARCHIVE_PATH)
    encounters = adventure.encounter_index()

    overview_words = sum(
        len(text.split()) for text in (adventure.synopsis, adventure.premise, adventure.explanation)
    )
    summary_words = sum(len(encounter.summary.split()) for encounter in adventure.encounters)
    opening_words = sum(len(encounter.opening_view.split()) for encounter in adventure.encounters)
    content_words = sum(len(encounter.content.split()) for encounter in adventure.encounters)
    revelation_words = sum(len(item.description.split()) for item in adventure.revelations)
    clue_words = sum(len(item.description.split()) for item in adventure.clues)
    assert (
        overview_words,
        summary_words,
        opening_words,
        content_words,
        revelation_words,
        clue_words,
    ) == (1461, 186, 571, 5958, 360, 1234)

    assert "a disputed civic voice assembled by the living" in adventure.explanation
    assert (
        "publication requires someone present to choose and carry a packet" in adventure.explanation
    )
    assert (
        "Caldra will not turn a working hospice into the city\u2019s warehouse"
        in encounters["the-archive-vault"].content
    )
    assert "Names on a page create no promise" in encounters["the-west-infirmary"].content
    assert "each surviving part keeps its listed use" in encounters["the-bell-chapel"].content
    assert (
        "Move Edrin only when pages, witnesses, custody, or altered glass make his next position untenable"
        in encounters["vale-manor"].content
    )
    assert "The body speaks only from the recorded streams" in encounters["vale-manor"].content
    assert "**What survives decides the ending.**" in encounters["vale-manor"].content
    auth_rule = "authenticated House copies under a named custodian"
    mouth_rule = "fails without either a Vale inside or a hand closing the inner line"
    assert auth_rule in encounters["the-trustees-chamber"].content
    assert auth_rule in PUBLIC_LEDGER_PATH.read_text()
    assert mouth_rule in adventure.explanation
    assert mouth_rule in encounters["vale-manor"].content
    assert mouth_rule in MANOR_SHEET_PATH.read_text()


    assert_historical_archive_structure(archive.adventure_snapshot, adventure)
    assert len(archive.play_state.events) == 116
    assert EXAMPLE_PATH.read_bytes() == RESOURCE_PATH.read_bytes()
    assert EXAMPLE_PATH.read_bytes() == DIRECTORY_ADVENTURE_PATH.read_bytes()

    references = adventure.reference_index()
    assert "Before she opens another drawer" in encounters["the-archive-vault"].content
    assert "The evidence remains in use" in encounters["the-west-infirmary"].content
    assert (
        "Four caucuses crowd Nessa Quill\u2019s copy tables"
        in encounters["the-house-of-petitions"].content
    )
    assert "The crew is split across the tower" in encounters["the-grand-belfry"].content
    assert (
        "## Four tables, one ledger" in references["baf4dcd9-9f96-4099-8bab-a487cc3e93f1"].content
    )
    assert "## Care before testimony" in references["af698a7e-01e3-4e9b-b5cb-3ccf7830d7a2"].content
    assert (
        "## Six doors to one circle" in references["2496cf62-c44a-4a52-b1dd-8ed40244f0e5"].content
    )
    assert "## What bronze remembers" in references["adf71e90-d724-486a-94e8-7d4e630bf82e"].content
    documents = render_adventure_documents(adventure, validate_adventure(adventure))
    assert "a disputed civic voice assembled by the living" in documents["00-overview.md"]
    assert "**What survives decides the ending.**" in documents["encounters/vale-manor.md"]


def test_glass_saint_fresh_play_archive_is_exact_and_does_not_define_source() -> None:
    """Keep the failed-warrant demonstration reproducible, bounded, and subordinate."""
    adventure = load_adventure(EXAMPLE_PATH)
    state = load_play_state(STATE_PATH)
    archive = load_journal_archive(ARCHIVE_PATH)
    projection = project_play_state(adventure, state)

    assert archive.play_state == state
    assert_historical_archive_structure(archive.adventure_snapshot, adventure)
    assert len(state.events) == 116
    assert len(state.active_events) == 116
    assert tuple(session.title for session in projection.sessions) == (
        "What the Glass Threw Out",
        "A Warrant Refused",
        "The Saint Who Could Not Answer",
    )
    assert projection.active_session_number is None
    assert tuple(visit.encounter_id for visit in projection.visits) == (
        "the-shattered-gallery",
        "the-procession-court",
        "the-archive-vault",
        "the-trustees-chamber",
        "the-house-of-petitions",
        "the-grand-belfry",
        "vale-manor",
    )
    assert len(projection.spotted_clue_ids) == 37
    assert sum(len(item.missed_visit_numbers) for item in projection.clue_progress) == 5
    assert all(item.is_established for item in projection.revelation_progress)
    assert len(projection.consequences) == 15
    assert not projection.corrections

    summary = render_play_summary(adventure, state)
    assert summary == PLAY_SUMMARY_PATH.read_text()
    assert "Events recorded: 116" in summary
    assert "Explicit sessions: 3" in summary
    assert "Visits recorded: 7" in summary
    assert "Unique leads found: 37 / 69" in summary

    party = PARTY_PATH.read_text()
    playthrough = PLAYTHROUGH_PATH.read_text()
    for name in ("Aven Rook", "Mira Thane", "Pell Orison", "Lysa Ord"):
        assert name in party
        assert name not in EXAMPLE_PATH.read_text()
    assert "The Counterseal Witnesses" in playthrough
    assert "West Infirmary" in playthrough
    assert "Bell Chapel" in playthrough
    assert "No living voice was taken." in playthrough
