"""Integration coverage for Play mode before an adventure has encounters."""

from pathlib import Path

from adventure_graph.bootstrap import compose_workspace_web_application
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.local_adventure_workspace import LocalAdventureWorkspace
from tests.support.web import request_wsgi


def test_title_only_adventure_can_enter_play_and_add_its_first_encounter(
    tmp_path: Path,
) -> None:
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)

    status, headers, _ = request_wsgi(
        app,
        "/adventures/new",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": workspace.load().revision.value,
            "title": "The Unwritten Door",
            "synopsis": "",
            "premise": "",
            "explanation": "",
            "opening_title": "",
            "opening_summary": "",
            "opening_view": "",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == "/adventures?created=1"

    selected_key = workspace.load().settings.selected_adventure_key
    assert selected_key == "the-unwritten-door/adventure.json"
    adventure_path = tmp_path / "the-unwritten-door" / "adventure.json"
    assert load_adventure(adventure_path).encounters == ()

    status, _, body = request_wsgi(app, "/play")
    assert status == "200 OK"
    assert "This adventure has no encounters yet." in body
    assert "Add an encounter before beginning play." in body
    assert 'href="/encounters/new?return_to=%2Fplay"' in body
    assert ">Add first encounter</a>" in body
    assert 'href="/">Return to Author mode</a>' in body
    assert "Workspace could not be loaded" not in body

    selected_app = app.adventure_application(selected_key, app.csrf_token)
    revision = selected_app.queries.get_structure().revision.value
    status, _, form_body = request_wsgi(
        app,
        "/encounters/new",
        query="return_to=%2Fplay",
    )
    assert status == "200 OK"
    assert "Add an encounter during play" in form_body
    assert 'name="return_to" value="/play"' in form_body
    assert 'name="start" value="1" data-draft-field checked' in form_body

    status, headers, _ = request_wsgi(
        app,
        "/encounters/new",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": revision,
            "title": "The First Room",
            "summary": "",
            "opening_view": "",
            "content": "",
            "tags": "",
            "required": "1",
            "start": "1",
            "return_to": "/play",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == (
        "/play?encounter=the-first-room&action=encounter-authored"
    )

    status, _, body = request_wsgi(
        app,
        "/play",
        query="encounter=the-first-room&action=encounter-authored",
    )
    assert status == "200 OK"
    assert "The First Room" in body
    assert "This adventure has no encounters yet." not in body
    assert tuple(item.id for item in load_adventure(adventure_path).encounters) == (
        "the-first-room",
    )
