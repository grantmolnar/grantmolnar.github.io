"""Play-mode retrieval tests for persistent adventure references."""

from __future__ import annotations

from dataclasses import replace
from urllib.parse import urlencode

from adventure_graph.application.play_tracking import (
    end_session,
    new_play_state,
    record_visit,
    start_session,
)
from adventure_graph.domain.adventure import Reference
from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    PLACE_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)
from tests.support.web import build_play_app, request_wsgi


def test_play_shows_ordered_links_and_selection_without_journal_writes() -> None:
    adventure = reference_library_adventure()
    app, project = build_play_app(adventure)
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/play",
        query=urlencode({"encounter": "beta", "reference": PERSON_REFERENCE_ID}),
    )

    assert status == "200 OK"
    assert "Browsing Beta; the current recorded visit remains Alpha." in body
    assert f'data-play-selected-reference-id="{PERSON_REFERENCE_ID}"' in body
    assert "data-play-selected-reference" in body
    assert "The hall&#x27;s observant housekeeper." in body
    assert "Cora protects the household before its owner." in body
    assert 'data-play-pin-kind="reference"' in body
    linked = body.split('id="encounter-references"', 1)[1].split("</section>", 1)[0]
    assert "Cora Pike" in linked
    assert "Cora may change allegiance after hearing the testimony." in linked
    assert project.snapshot == before


def test_play_preserves_encounter_authored_reference_order_and_context() -> None:
    adventure = reference_library_adventure()
    app, _ = build_play_app(adventure)

    status, _, body = request_wsgi(app, "/play", query="encounter=alpha")

    assert status == "200 OK"
    linked = body.split('id="encounter-references"', 1)[1].split("</section>", 1)[0]
    assert linked.index("Cora Pike") < linked.index("Blackbriar Hall")
    assert "Cora controls access to the first-floor rooms." in linked
    assert f"reference={PERSON_REFERENCE_ID}" in linked
    assert f"reference={PLACE_REFERENCE_ID}" in linked


def test_play_search_indexes_reference_names_prose_tags_and_link_context() -> None:
    app, _ = build_play_app(reference_library_adventure())

    status, _, body = request_wsgi(app, "/play", query="encounter=alpha")

    assert status == "200 OK"
    assert "Search encounters, leads, revelations, and references" in body
    assert "the housekeeper" in body
    assert "cora protects the household before its owner" in body
    assert "staff witness" in body
    assert "cora may change allegiance after hearing the testimony" in body
    assert f"reference%3D{PERSON_REFERENCE_ID}" not in body
    assert f"reference={PERSON_REFERENCE_ID}" in body


def test_unlinked_reference_is_reachable_from_search_selection_and_typed_pin_records() -> None:
    adventure = reference_library_adventure()
    unlinked = Reference(
        "77777777-7777-4777-8777-777777777777",
        "object",
        "The Quiet Key",
        aliases=("Key of Ash",),
        summary="A key not yet assigned to an encounter.",
        content="It opens a door the GM has not placed.",
        tags=("unplaced",),
    )
    adventure = replace(adventure, references=(*adventure.references, unlinked))
    app, project = build_play_app(adventure)
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/play",
        query=urlencode({"encounter": "alpha", "reference": unlinked.id}),
    )

    assert status == "200 OK"
    assert "The Quiet Key" in body
    assert "This reference is not linked to an encounter." in body
    assert f'data-play-kind="reference" data-play-id="{unlinked.id}"' in body
    assert f'data-play-pin-id="{unlinked.id}"' in body
    assert project.snapshot == before


def test_reference_light_play_has_a_small_explicit_empty_state() -> None:
    app, _ = build_play_app(complete_four_encounter_adventure())

    status, _, body = request_wsgi(app, "/play", query="encounter=alpha")

    assert status == "200 OK"
    assert "This adventure has no persistent references." in body
    assert '<div class="play-reference-records" hidden></div>' in body
    assert "data-play-selected-reference" not in body


def test_invalid_selected_reference_is_ignored_without_changing_encounter_focus() -> None:
    app, project = build_play_app(reference_library_adventure())
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/play",
        query="encounter=beta&reference=77777777-7777-4777-8777-777777777777",
    )

    assert status == "200 OK"
    assert "<h1>Beta</h1>" in body
    assert "data-play-selected-reference" not in body
    assert project.snapshot == before


def test_play_reference_output_escapes_authored_values_and_sanitizes_markdown() -> None:
    adventure = reference_library_adventure()
    malicious = Reference(
        "88888888-8888-4888-8888-888888888888",
        "other",
        "<script>alert(1)</script>",
        aliases=("<alias>",),
        summary='<img src=x onerror="alert(2)">',
        content="[unsafe](javascript:alert(3))\n\n**Safe emphasis**",
        tags=("<tag>",),
    )
    adventure = replace(adventure, references=(*adventure.references, malicious))
    app, project = build_play_app(adventure)
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/play",
        query=urlencode({"encounter": "alpha", "reference": malicious.id}),
    )

    assert status == "200 OK"
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body
    assert "<img src=x" not in body
    selected = body.split("data-play-selected-reference>", 1)[1].split("</section>", 1)[0]
    assert 'href="javascript:' not in selected
    assert "[unsafe](javascript:alert(3))" in selected
    assert "<strong>Safe emphasis</strong>" in body
    assert "&lt;alias&gt;" in body
    assert "&lt;tag&gt;" in body
    assert project.snapshot == before


def test_play_pin_script_migrates_legacy_encounter_ids_to_typed_bounded_records() -> None:
    app, _ = build_play_app(reference_library_adventure())

    status, _, script = request_wsgi(app, "/assets/app.js")

    assert status == "200 OK"
    assert 'pin = { kind: "encounter", id: value };' in script
    assert 'value.kind === "reference"' in script
    assert ".filter((pin) => itemRecords.has(`${pin.kind}:${pin.id}`))" in script
    assert ".slice(0, 16)" in script
    assert "JSON.stringify(pins)" in script
    assert "readStoredArray(recentKey)" in script


def test_play_reference_panel_appends_notes_and_keeps_them_in_chronological_views() -> None:
    adventure = reference_library_adventure()
    state = start_session(new_play_state(adventure), title="Household audience")
    state = record_visit(adventure, state, "alpha")
    app, project = build_play_app(adventure, state)

    get_status, _, get_body = request_wsgi(
        app,
        "/play",
        query=urlencode({"encounter": "alpha", "reference": PERSON_REFERENCE_ID}),
    )

    assert get_status == "200 OK"
    assert 'action="/play/reference/note"' in get_body
    assert 'name="reference_id"' in get_body
    assert "It does not alter the authored description above." in get_body

    status, headers, body = request_wsgi(
        app,
        "/play/reference/note",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "focus_encounter_id": "alpha",
            "reference_id": PERSON_REFERENCE_ID,
            "text": "Cora agreed to shelter the witnesses.",
        },
    )

    assert status == "303 See Other"
    assert body == ""
    assert "action=reference-note" in headers["Location"]
    assert f"reference={PERSON_REFERENCE_ID}" in headers["Location"]
    assert project.snapshot.state.events[-1].reference_id == PERSON_REFERENCE_ID

    _, _, updated = request_wsgi(
        app,
        "/play",
        query=urlencode(
            {
                "action": "reference-note",
                "operation": "3",
                "encounter": "alpha",
                "reference": PERSON_REFERENCE_ID,
            }
        ),
    )
    assert "Reference note committed" in updated
    assert "Cora agreed to shelter the witnesses." in updated
    assert "Session 1: Household audience" in updated

    _, _, journal = request_wsgi(app, "/journal")
    assert "Note on Cora Pike: Cora agreed to shelter the witnesses." in journal

    _, _, narrative = request_wsgi(
        app,
        "/play/ledgers",
        query="kind=narrative&scope=playthrough",
    )
    assert "Note on Cora Pike" in narrative
    assert "Cora agreed to shelter the witnesses." in narrative

    _, _, recap = request_wsgi(
        app,
        "/play/ledgers",
        query="kind=recap&scope=playthrough",
    )
    assert "Cora agreed to shelter the witnesses." not in recap


def test_rejected_reference_note_preserves_selection_and_submitted_text() -> None:
    adventure = reference_library_adventure()
    state = start_session(new_play_state(adventure), title="Household audience")
    app, project = build_play_app(adventure, state)
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/play/reference/note",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "obsolete",
            "focus_encounter_id": "beta",
            "reference_id": PERSON_REFERENCE_ID,
            "text": "Preserve this reference note.",
        },
    )

    assert status == "409 Conflict"
    assert "Revision conflict" in body
    assert "Preserve this reference note." in body
    assert f'data-play-selected-reference-id="{PERSON_REFERENCE_ID}"' in body
    assert "<h1>Beta</h1>" in body
    assert project.snapshot == before


def test_reference_note_form_is_read_only_between_explicit_sessions() -> None:
    adventure = reference_library_adventure()
    state = start_session(new_play_state(adventure), title="First session")
    state = end_session(state)
    app, _ = build_play_app(adventure, state)

    status, _, body = request_wsgi(
        app,
        "/play",
        query=urlencode({"encounter": "alpha", "reference": PERSON_REFERENCE_ID}),
    )

    assert status == "200 OK"
    assert 'action="/play/reference/note"' not in body
    assert "Begin a session in the left rail to add another chronological note." in body
