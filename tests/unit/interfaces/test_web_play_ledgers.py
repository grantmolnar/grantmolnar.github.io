"""Tests for play ledgers and session-review routes."""

from __future__ import annotations

from adventure_graph.application.play_tracking import (
    add_visit_note,
    end_session,
    establish_revelation,
    miss_clue,
    new_play_state,
    record_encounter_consequence,
    record_visit,
    spot_clue,
    start_session,
)
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.web import (
    build_play_app,
    request_wsgi,
)


def test_play_ledgers_render_scoped_views_and_download_player_safe_markdown() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(
        new_play_state(adventure),
        title="Ledger Night",
        played_on="2026-07-15",
    )
    state = record_visit(adventure, state, "alpha")
    state = spot_clue(adventure, state, "alpha-to-beta")
    state = miss_clue(adventure, state, "alpha-to-gamma")
    state = add_visit_note(state, 1, "Hidden notebook text.")
    state = record_encounter_consequence(adventure, state, "alpha", "Hidden consequence.")
    state = establish_revelation(
        adventure,
        state,
        "find-beta",
        ("alpha-to-beta",),
        "Hidden establishment note.",
    )
    state = end_session(state, "Hidden closing note.")
    app, project = build_play_app(adventure, state)
    before = project.snapshot

    status, _, clue_page = request_wsgi(
        app,
        "/play/ledgers",
        query="kind=clues&scope=session",
    )

    assert status == "200 OK"
    assert "Lead ledger" in clue_page
    assert "Ledger Night" in clue_page
    assert "alpha points to beta" in clue_page
    assert "alpha points to gamma" in clue_page
    assert "Download Markdown" in clue_page
    assert 'aria-label="Play navigation"' in clue_page
    assert "Return to Play" in clue_page
    assert 'aria-label="Adventure context"' in clue_page
    assert "Open Author mode" not in clue_page
    assert project.snapshot == before
    assert project.load_count == 1

    status, headers, recap = request_wsgi(
        app,
        "/play/ledgers/download",
        query="kind=recap&scope=session",
    )

    assert status == "200 OK"
    assert headers["Content-Type"] == "text/markdown; charset=utf-8"
    assert headers["Content-Disposition"] == 'attachment; filename="session-01-recap.md"'
    assert "alpha points to beta" in recap
    assert "Find Beta" in recap
    assert "Hidden" not in recap
    assert "alpha points to gamma" not in recap
    assert "missed" not in recap.lower()
    assert project.load_count == 2

    _, _, narrative = request_wsgi(
        app,
        "/play/ledgers",
        query="kind=narrative&scope=session",
    )
    assert "Hidden notebook text." in narrative
    assert "Hidden consequence." in narrative

    _, _, player_page = request_wsgi(
        app,
        "/play/ledgers",
        query="kind=recap&scope=session",
    )
    assert "Player-safe projection" in player_page
    assert "Leads" in player_page
    assert "discovered leads" in player_page
    assert "discovered clues" not in player_page
    assert "Hidden notebook text." not in player_page
    assert "Hidden consequence." not in player_page
    assert "Lead missed" not in player_page


def test_play_mode_session_end_notice_links_to_latest_session_review() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Review Session")
    state = record_visit(adventure, state, "alpha")
    state = end_session(state)
    app, _ = build_play_app(adventure, state)

    status, _, body = request_wsgi(
        app,
        "/play",
        query="action=session-ended&operation=3&encounter=alpha",
    )

    assert status == "200 OK"
    assert "Session review" in body
    assert 'href="/play/ledgers?kind=narrative&amp;scope=session"' in body
    assert 'href="/play/ledgers?kind=recap&amp;scope=session"' in body


def test_play_ledgers_reject_unknown_view_selection() -> None:
    app, _ = build_play_app()

    status, _, body = request_wsgi(app, "/play/ledgers", query="kind=secrets")

    assert status == "404 Not Found"
    assert "Unknown play-ledger kind" in body
