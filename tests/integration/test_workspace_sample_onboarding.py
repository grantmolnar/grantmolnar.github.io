"""Integration coverage for the one packaged beta sample."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import UUID

from adventure_graph.bootstrap import compose_workspace_web_application
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.bundled_adventures import load_glass_saint_template
from adventure_graph.infrastructure.local_adventure_workspace import LocalAdventureWorkspace
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.web import request_wsgi


def test_empty_workspace_can_add_the_packaged_glass_saint_sample(tmp_path: Path) -> None:
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)
    snapshot = workspace.load()

    status, _, body = request_wsgi(app, "/adventures")

    assert status == "200 OK"
    assert "The Glass Saint is the complete sample included with this beta" in body
    assert 'action="/adventures/sample"' in body
    assert "Create blank adventure" in body

    status, headers, _ = request_wsgi(
        app,
        "/adventures/sample",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": snapshot.revision.value,
        },
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/adventures?sample=1"
    source = tmp_path / "the-glass-saint" / "adventure.json"
    state_source = tmp_path / "the-glass-saint" / "play-state.json"
    assert source.is_file()
    assert state_source.is_file()

    sample = load_adventure(source)
    template = load_glass_saint_template()
    assert sample.id != template.id
    assert UUID(sample.id).version == 4
    assert replace(sample, id=template.id) == template
    state = load_play_state(state_source)
    assert state.adventure_id == sample.id
    assert state.events == ()
    assert workspace.load().settings.selected_adventure_key == ("the-glass-saint/adventure.json")

    status, _, body = request_wsgi(app, "/adventures", query="sample=1")
    assert status == "200 OK"
    assert "Sample added" in body
    assert "separate editable project" in body


def test_packaged_sample_creation_refuses_a_stale_workspace_revision(tmp_path: Path) -> None:
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)
    stale_snapshot = workspace.load()
    (tmp_path / "reserved-after-render").mkdir()

    status, _, body = request_wsgi(
        app,
        "/adventures/sample",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": stale_snapshot.revision.value,
        },
    )

    assert status == "409 Conflict"
    assert "Workspace changed" in body
    assert not (tmp_path / "the-glass-saint").exists()
