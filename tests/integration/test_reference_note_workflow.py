"""Filesystem integration coverage for persistent-reference playthrough notes."""

from __future__ import annotations

from pathlib import Path

from adventure_graph.application.play_tracking import new_play_state, start_session
from adventure_graph.domain.play_events import ReferenceNoteRecordedEvent
from adventure_graph.infrastructure.adventure_store import save_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state, save_play_state
from adventure_graph.web_composition import LocalWebProjects, compose_adventure_web_application
from tests.support.adventures import PERSON_REFERENCE_ID, reference_library_adventure
from tests.support.web import post_form, request_wsgi


def test_reference_note_commits_through_production_web_composition(tmp_path: Path) -> None:
    adventure = reference_library_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, adventure)
    save_play_state(
        state_path,
        start_session(new_play_state(adventure), title="Household audience"),
    )
    (tmp_path / "generated").mkdir()
    (tmp_path / "archives").mkdir()
    projects = LocalWebProjects.open(adventure_path)
    app = compose_adventure_web_application(projects, csrf_token="integration-token")

    status, headers, body = post_form(
        app,
        "/play/reference/note",
        {
            "csrf_token": "integration-token",
            "expected_revision": projects.play.load().revision.value,
            "focus_encounter_id": "alpha",
            "reference_id": PERSON_REFERENCE_ID,
            "text": "Cora agreed to shelter the witnesses.",
        },
    )

    assert status == "303 See Other"
    assert body == ""
    assert "action=reference-note" in headers["Location"]
    assert f"reference={PERSON_REFERENCE_ID}" in headers["Location"]
    event = load_play_state(state_path).events[-1]
    assert isinstance(event, ReferenceNoteRecordedEvent)
    assert event.reference_id == PERSON_REFERENCE_ID
    assert event.text == "Cora agreed to shelter the witnesses."

    view_status, _, view = request_wsgi(
        app,
        "/play",
        query=f"encounter=alpha&reference={PERSON_REFERENCE_ID}",
    )
    assert view_status == "200 OK"
    assert "Cora agreed to shelter the witnesses." in view
    assert "Session 1: Household audience" in view
