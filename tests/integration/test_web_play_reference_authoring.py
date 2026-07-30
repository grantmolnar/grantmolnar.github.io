"""Filesystem integration coverage for Play-safe reference authoring."""

from __future__ import annotations

from pathlib import Path

from adventure_graph.application.play_tracking import new_play_state, record_visit
from adventure_graph.infrastructure.adventure_store import load_adventure, save_adventure
from adventure_graph.infrastructure.local_authoring_project import LocalAuthoringProject
from adventure_graph.infrastructure.play_state_store import save_play_state
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.local_web import build_local_play_app
from tests.support.web import post_form, request_wsgi


def test_play_reference_authoring_links_record_without_changing_play_history(
    tmp_path: Path,
) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    state = record_visit(adventure, new_play_state(adventure), "alpha", ())
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, state)
    app = build_local_play_app(adventure_path, state_path)
    original_state = state_path.read_bytes()

    form_status, _, form_body = request_wsgi(
        app,
        "/references/new",
        query="encounter=alpha&return_to=%2Fplay%3Fencounter%3Dalpha",
    )

    assert form_status == "200 OK"
    assert "Play improvisation" in form_body
    assert 'name="encounter_id" value="alpha"' in form_body
    assert 'name="return_to" value="/play?encounter=alpha"' in form_body
    assert 'href="/play?encounter=alpha">Cancel</a>' in form_body

    revision = LocalAuthoringProject(adventure_path).load().revision.value
    status, headers, _ = post_form(
        app,
        "/references/new",
        {
            "csrf_token": "integration-token",
            "expected_revision": revision,
            "kind": "person",
            "title": "Mara Venn",
            "aliases": "The Bellkeeper",
            "summary": "A recurring witness improvised during play.",
            "content": "## Mara Venn\n\nMara keeps the midnight arrival ledger.",
            "tags": "witness, staff",
            "encounter_id": "alpha",
            "context": "Mara controls access to the improvised route.",
            "return_to": "/play?encounter=alpha",
        },
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/play?encounter=alpha&action=reference-authored"
    assert state_path.read_bytes() == original_state
    authored = load_adventure(adventure_path)
    mara = next(reference for reference in authored.references if reference.title == "Mara Venn")
    assert any(
        link.reference_id == mara.id for link in authored.encounter_index()["alpha"].reference_links
    )

    return_status, _, return_body = request_wsgi(
        app,
        "/play",
        query="encounter=alpha&action=reference-authored",
    )

    assert return_status == "200 OK"
    assert "Reference added" in return_body
    assert "current visit and play history did not change" in return_body
    assert "Mara Venn" in return_body
