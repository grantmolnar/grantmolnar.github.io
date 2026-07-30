"""Tests for play-mode session and run workflows."""

from __future__ import annotations

from dataclasses import replace

from adventure_graph.application.play_errors import PlayTrackingError
from adventure_graph.application.play_tracking import (
    new_play_state,
    record_visit,
    start_session,
)
from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.run_workspace import GetRunDashboard
from adventure_graph.interfaces.web.play_rendering_support import present_play_error
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.web import (
    build_authoring_app,
    build_play_app,
    request_wsgi,
)


def test_play_error_presentation_removes_internal_operation_indexes() -> None:
    adventure = complete_four_encounter_adventure()

    message = present_play_error(
        PlayTrackingError("Transition operation 5 contains an unrelated encounter unlock."),
        adventure,
    )

    assert message == "The submitted visit update contains an unrelated encounter unlock."


def test_play_mode_runs_an_explicit_session_through_one_atomic_transition() -> None:
    adventure = complete_four_encounter_adventure()
    app, project = build_play_app(adventure, new_play_state(adventure))

    status, headers, _ = request_wsgi(
        app,
        "/play/session/start",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "focus_encounter_id": "",
            "title": "The eastern watch",
            "played_on": "2026-07-15",
            "participants": "Mara, Sera",
            "attendance_note": "Orin joined remotely.",
            "opening_note": "The party resumed at the city gate.",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == "/play?action=session-started&operation=1"

    status, _, body = request_wsgi(app, "/play", query="encounter=alpha")
    assert status == "200 OK"
    assert ">Start visit</button>" in body
    assert "Begin session first" not in body

    status, headers, _ = request_wsgi(
        app,
        "/play/enter",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-2",
            "focus_encounter_id": "alpha",
            "encounter_id": "alpha",
            "party_label": "Main party",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == "/play?action=visit&operation=2&encounter=alpha&visit=1"

    status, _, body = request_wsgi(app, "/play", query="encounter=alpha")
    assert status == "200 OK"
    assert "Encounter notes" in body
    assert "Save note only" in body
    assert "data-play-note-mode" not in body
    assert 'action="/play/consequence"' not in body
    assert "What remains true when the party returns?" not in body
    assert "changed circumstances, or likely consequences" in body
    assert 'data-play-notebook data-play-visit-number="1"' in body
    assert 'action="/play/clue/found"' in body
    assert 'action="/play/clue/missed"' in body
    assert 'action="/play/transition"' in body

    status, headers, _ = request_wsgi(
        app,
        "/play/transition",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-2",
            "focus_encounter_id": "alpha",
            "source_visit_number": "1",
            "note": "The party questioned the watch captain.",
            "spotted_clue_id": "alpha-to-beta",
            "missed_clue_id": "alpha-to-gamma",
            "established_revelation_id": "find-beta",
            "destination_encounter_id": "beta",
            "party_label": "Scouting pair",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == (
        "/play?action=transition&operation=3&encounter=beta&visit=2&clear_draft=1"
    )

    dashboard = GetRunDashboard(project).execute()
    transition_events = tuple(
        event for event in project.snapshot.state.events if event.operation_number == 3
    )
    assert len(transition_events) == 6
    assert dashboard.current_encounter is not None
    assert dashboard.current_encounter.id == "beta"
    assert dashboard.current_visit is not None
    assert dashboard.current_visit.party_label == "Scouting pair"
    assert dashboard.projection.visits[0].notes == ("The party questioned the watch captain.",)
    assert dashboard.projection.visits[0].spotted_clue_ids == ("alpha-to-beta",)
    assert dashboard.projection.visits[0].missed_clue_ids == ("alpha-to-gamma",)
    find_beta = next(
        item for item in dashboard.revelation_statuses if item.revelation.id == "find-beta"
    )
    assert find_beta.is_established
    assert dashboard.projection.consequences == ()

    status, headers, _ = request_wsgi(
        app,
        "/play/session/end",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-2",
            "focus_encounter_id": "beta",
            "closing_note": "The party made camp beneath the eastern wall.",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == ("/play?action=session-ended&operation=4&encounter=beta")
    session = GetRunDashboard(project).execute().projection.sessions[0]
    assert session.title == "The eastern watch"
    assert session.participants == ("Mara", "Sera")
    assert session.closing_note == "The party made camp beneath the eastern wall."


def test_play_mode_records_and_reverses_revelation_foreclosure() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Session one")
    state = record_visit(adventure, state, "alpha")
    app, project = build_play_app(adventure, state)

    status, _, body = request_wsgi(app, "/play", query="encounter=alpha")
    assert status == "200 OK"
    assert 'action="/play/revelation/foreclose"' in body

    status, headers, _ = request_wsgi(
        app,
        "/play/revelation/foreclose",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "focus_encounter_id": "alpha",
            "revelation_id": "find-beta",
            "reason": "The only guide has left the city.",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == ("/play?action=revelation-foreclosed&operation=3&encounter=alpha")

    status, _, body = request_wsgi(app, "/play", query="encounter=alpha")
    assert status == "200 OK"
    assert "Foreclosed" in body
    assert 'action="/play/revelation/reopen"' in body

    status, headers, _ = request_wsgi(
        app,
        "/play/revelation/reopen",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-2",
            "focus_encounter_id": "alpha",
            "revelation_id": "find-beta",
            "reason": "The guide returned with reinforcements.",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == ("/play?action=revelation-reopened&operation=4&encounter=alpha")
    status_item = next(
        item
        for item in GetRunDashboard(project).execute().revelation_statuses
        if item.revelation.id == "find-beta"
    )
    assert not status_item.is_foreclosed


def test_play_transition_establishes_multiple_already_supported_revelations_and_moves() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Session one")
    state = record_visit(
        adventure,
        state,
        "alpha",
        spotted_clue_ids=("alpha-to-beta", "alpha-to-gamma"),
    )
    app, project = build_play_app(adventure, state)

    status, headers, body = request_wsgi(
        app,
        "/play/transition",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "focus_encounter_id": "alpha",
            "source_visit_number": "1",
            "note": "",
            "established_revelation_id": ("find-beta", "find-gamma"),
            "destination_encounter_id": "beta",
            "party_label": "",
        },
    )

    assert status == "303 See Other"
    assert body == ""
    assert headers["Location"] == (
        "/play?action=transition&operation=3&encounter=beta&visit=2&clear_draft=1"
    )
    dashboard = GetRunDashboard(project).execute()
    assert dashboard.current_encounter is not None
    assert dashboard.current_encounter.id == "beta"
    assert dashboard.projection.available_encounter_ids == ("alpha", "beta", "gamma")


def test_play_transition_error_names_authored_material_instead_of_internal_ids() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Session one")
    state = record_visit(adventure, state, "alpha")
    app, project = build_play_app(adventure, state)
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/play/transition",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "focus_encounter_id": "alpha",
            "source_visit_number": "1",
            "note": "",
            "spotted_clue_id": "alpha-to-beta",
            "missed_clue_id": "alpha-to-beta",
            "destination_encounter_id": "",
            "party_label": "",
        },
    )

    assert status == "422 Unprocessable Content"
    notice = body.split('<section class="notice error"', 1)[1].split("</section>", 1)[0]
    assert "Visit update was not recorded" in notice
    assert "alpha points to beta" in notice
    assert "alpha-to-beta" not in notice
    assert project.snapshot == before


def test_play_transition_error_preserves_submitted_notebook_and_outcomes() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Session one")
    state = record_visit(adventure, state, "alpha")
    app, project = build_play_app(adventure, state)
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/play/transition",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "obsolete",
            "focus_encounter_id": "alpha",
            "source_visit_number": "1",
            "note": "Preserve this working account.",
            "spotted_clue_id": "alpha-to-beta",
            "missed_clue_id": "alpha-to-gamma",
            "established_revelation_id": "find-beta",
            "consequence": "Preserve this consequence.",
            "destination_encounter_id": "alpha",
            "party_label": "Main party",
        },
    )

    assert status == "409 Conflict"
    assert "Revision conflict" in body
    assert "Preserve this working account." in body
    assert "Preserve this consequence." not in body
    assert 'value="alpha-to-beta" checked data-play-outcome="found"' in body
    assert 'value="alpha-to-gamma" checked data-play-outcome="missed"' in body
    assert 'value="find-beta" checked' in body
    assert '<option value="">Stay here; save outcomes only</option>' in body
    assert '<option value="alpha"' not in body
    assert 'value="Main party"' in body
    assert project.snapshot == before


def test_play_action_rejects_invalid_csrf_without_echoing_submitted_text() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Session one")
    state = record_visit(adventure, state, "alpha")
    app, project = build_play_app(adventure, state)
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/play/note",
        method="POST",
        form={
            "csrf_token": "wrong-token",
            "expected_revision": "play-revision-2",
            "focus_encounter_id": "alpha",
            "visit_number": "1",
            "text": "Preserve this rejected notebook entry.",
        },
    )

    assert status == "403 Forbidden"
    assert "Form token rejected" in body
    assert "Preserve this rejected notebook entry." not in body
    assert project.snapshot == before


def test_play_mode_requires_a_configured_journal() -> None:
    app, _ = build_authoring_app()

    status, _, body = request_wsgi(app, "/play")

    assert status == "404 Not Found"
    assert "Play mode unavailable" in body


def test_run_workspace_renders_current_visit_actions_and_recent_history() -> None:
    app, _ = build_play_app()

    status, _, body = request_wsgi(app, "/run")

    assert status == "200 OK"
    assert "Recovery console" in body
    assert "Advanced recording" not in body
    assert "Current visit" in body
    assert "Alpha" in body
    assert "Discoverable leads" in body
    assert 'action="/run/clue"' in body
    assert 'action="/run/revelation"' in body
    assert 'action="/run/note"' in body
    assert 'action="/run/consequence"' not in body
    assert 'action="/run/correct"' in body
    assert "Operation 1" in body
    assert 'href="/play" aria-current="page"' in body
    assert "Return to Play" in body


def test_run_workspace_records_clue_revelation_visit_note_and_consequence() -> None:
    app, project = build_play_app()

    clue_status, clue_headers, _ = request_wsgi(
        app,
        "/run/clue",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "clue_id": "alpha-to-gamma",
            "visit_number": "1",
        },
    )
    assert clue_status == "303 See Other"
    assert clue_headers["Location"] == "/run?action=clue&operation=2"

    revelation_status, revelation_headers, _ = request_wsgi(
        app,
        "/run/revelation",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-2",
            "revelation_id": "find-beta",
            "supporting_clue_id": "alpha-to-beta",
            "note": "The first trail is enough.",
        },
    )
    assert revelation_status == "303 See Other"
    assert revelation_headers["Location"] == "/run?action=revelation&operation=3"

    visit_status, visit_headers, _ = request_wsgi(
        app,
        "/run/visit",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-2",
            "encounter_id": "beta",
            "clue_id": "beta-to-gamma",
            "note": "The party enters under guard.",
        },
    )
    assert visit_status == "303 See Other"
    assert visit_headers["Location"] == "/run?action=visit&operation=4&visit=2"

    note_status, note_headers, _ = request_wsgi(
        app,
        "/run/note",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-2",
            "visit_number": "2",
            "text": "The guards stand down.",
        },
    )
    assert note_status == "303 See Other"
    assert note_headers["Location"] == "/run?action=note&operation=5"

    consequence_status, consequence_headers, _ = request_wsgi(
        app,
        "/run/consequence",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-2",
            "encounter_id": "beta",
            "text": "The western gate remains open.",
        },
    )
    assert consequence_status == "303 See Other"
    assert consequence_headers["Location"] == "/run?action=consequence&operation=6"

    assert len(project.snapshot.state.events) == 11
    _, _, body = request_wsgi(app, "/run", query="action=consequence&operation=6")
    assert "Legacy persistent note recorded" in body
    assert "The guards stand down." in body
    assert "The western gate remains open." in body
    assert "Find Beta" in body
    assert "Established" in body


def test_run_workspace_manual_unlock_and_correction() -> None:
    app, project = build_play_app()

    unlock_status, unlock_headers, _ = request_wsgi(
        app,
        "/run/unlock",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "encounter_id": "gamma",
            "reason": "A ferryman reveals a side channel.",
        },
    )
    assert unlock_status == "303 See Other"
    assert unlock_headers["Location"] == "/run?action=unlock&operation=2"

    correction_status, correction_headers, _ = request_wsgi(
        app,
        "/run/correct",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-2",
            "reason": "The ferryman had not arrived yet.",
        },
    )
    assert correction_status == "303 See Other"
    assert correction_headers["Location"] == "/run?action=corrected&operation=2"
    assert project.snapshot.state.voided_operation_numbers == frozenset({2})


def test_run_workspace_conflict_preserves_submitted_long_text() -> None:
    app, project = build_play_app()
    project.snapshot = replace(project.snapshot, revision=ProjectRevision("external"))

    status, _, body = request_wsgi(
        app,
        "/run/consequence",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "encounter_id": "alpha",
            "text": "Preserve this durable consequence.",
        },
    )

    assert status == "409 Conflict"
    assert "Revision conflict" in body
    assert "Preserve this durable consequence." not in body
    assert len(project.snapshot.state.events) == 3


def test_run_action_rejects_invalid_csrf_as_forbidden_without_mutation() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    app, project = build_play_app(adventure, state)
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/run/note",
        method="POST",
        form={
            "csrf_token": "wrong-token",
            "expected_revision": "play-revision-1",
            "visit_number": "1",
            "text": "Do not record this note.",
        },
    )

    assert status == "403 Forbidden"
    assert "Form token rejected" in body
    assert "Do not record this note." not in body
    assert project.snapshot == before
