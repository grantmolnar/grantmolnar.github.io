"""Tests for play-mode navigation and interaction surfaces."""

from __future__ import annotations

import json
from dataclasses import replace

from adventure_graph.application.play_tracking import (
    new_play_state,
    record_visit,
    start_session,
)
from adventure_graph.application.project import ProjectRevision
from adventure_graph.domain.play_events import (
    DiceGroupResult,
    DiceRollRecordedEvent,
)
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.web import (
    build_authoring_app,
    build_play_app,
    request_wsgi,
)


def test_journal_page_loads_one_snapshot_for_history_and_run_context() -> None:
    app, project = build_play_app()

    status, _, body = request_wsgi(app, "/journal")

    assert status == "200 OK"
    assert "Operation 1" in body
    assert project.load_count == 1


def test_journal_history_renders_and_corrects_latest_operation() -> None:
    app, project = build_play_app()

    status, _, body = request_wsgi(app, "/journal")
    assert status == "200 OK"
    assert "Operation 1" in body
    assert "3 events" in body
    assert "Correct operation 1" in body

    status, headers, _ = request_wsgi(
        app,
        "/journal/correct",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "reason": "The visit never occurred.",
        },
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/journal?corrected=1"
    assert project.snapshot.state.active_events == ()

    _, _, updated = request_wsgi(app, "/journal", query="corrected=1")
    assert "Operation corrected" in updated
    assert "Voided" in updated
    assert "Correction" in updated
    assert "The visit never occurred." in updated


def test_journal_correction_conflict_preserves_submitted_reason() -> None:
    app, project = build_play_app()
    project.snapshot = replace(project.snapshot, revision=ProjectRevision("external"))

    status, _, body = request_wsgi(
        app,
        "/journal/correct",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "reason": "Preserve this explanation.",
        },
    )

    assert status == "409 Conflict"
    assert "Revision conflict" in body
    assert "Preserve this explanation." in body
    assert len(project.snapshot.state.events) == 3
    assert project.load_count == 2


def test_author_rail_contains_only_author_workspaces() -> None:
    app, _ = build_play_app()

    status, _, body = request_wsgi(app, "/")

    assert status == "200 OK"
    left_rail = body.split('<aside class="left-rail"', 1)[1].split("</aside>", 1)[0]
    assert 'href="/structure"' in left_rail
    assert 'href="/reports"' in left_rail
    assert 'href="/play"' not in left_rail
    assert 'href="/journal"' not in left_rail
    assert 'href="/run"' not in left_rail
    assert 'href="/archives"' not in left_rail


def test_play_rails_keep_navigation_and_retrieval_on_the_left() -> None:
    app, _ = build_play_app()

    status, _, body = request_wsgi(app, "/play")

    assert status == "200 OK"
    left_rail = body.split('<aside class="play-route-rail"', 1)[1].split("</aside>", 1)[0]
    right_rail = body.split('<aside class="play-utility-rail"', 1)[1].split("</aside>", 1)[0]
    assert 'aria-label="Play navigation"' in left_rail
    assert "Find authored material" in left_rail
    assert "Chronological route" in left_rail
    assert "Find authored material" not in right_rail
    assert "Current visit actions" in right_rail
    assert "Dice tray" in right_rail
    assert right_rail.index("Dice tray") < right_rail.index("Current visit actions")


def test_play_topbar_and_left_rail_have_distinct_responsibilities() -> None:
    app, _ = build_play_app()

    status, _, body = request_wsgi(app, "/play")

    assert status == "200 OK"
    topbar = body.split('<header class="topbar play-topbar">', 1)[1].split("</header>", 1)[0]
    left_rail = body.split('<aside class="play-route-rail"', 1)[1].split("</aside>", 1)[0]
    assert 'aria-label="Adventure context"' in topbar
    assert 'aria-label="Application"' in topbar
    assert ">Author</a>" in topbar
    assert ">Play</a>" in topbar
    assert ">Adventures</a>" in topbar
    assert ">Settings</a>" in topbar
    assert 'class="topbar-project" href="/play"' in topbar
    assert ">History</a>" not in topbar
    assert ">Trackers</a>" not in topbar
    assert ">Correct history</a>" not in topbar
    assert "Play workspaces" in left_rail
    assert "<span>Table</span>" in left_rail
    assert "<span>History</span>" in left_rail
    assert "<span>Trackers</span>" in left_rail
    assert "<span>Correct history</span>" in left_rail
    assert "<span>Recovery console</span>" in left_rail
    assert "<span>Archives</span>" in left_rail
    assert "Open Author mode" not in left_rail
    assert 'class="play-mobile-application-links"' in left_rail
    assert '<a href="/help">Help</a>' in left_rail


def test_recent_history_summary_does_not_duplicate_workspace_navigation() -> None:
    app, _ = build_play_app()

    status, _, body = request_wsgi(app, "/play")

    assert status == "200 OK"
    panel = body.split("<h2>What happened so far</h2>", 1)[1].split("</section>", 1)[0]
    assert "<a " not in panel
    assert "History and trackers remain in the persistent left navigation." not in panel


def test_clues_link_directly_to_the_revelations_they_support() -> None:
    app, _ = build_play_app()

    status, _, body = request_wsgi(app, "/play", query="encounter=alpha")

    assert status == "200 OK"
    assert '<a href="#revelation-find-beta">Find Beta</a>' in body
    assert 'id="revelation-find-beta"' in body


def test_active_visit_transition_exposes_authored_next_encounters() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Table night")
    state = record_visit(adventure, state, "alpha")
    app, _ = build_play_app(adventure, state)

    status, _, body = request_wsgi(app, "/play", query="encounter=alpha")

    assert status == "200 OK"
    assert '<details class="play-live-details play-transition-details" open>' in body
    assert "Save outcomes and choose the next encounter" in body
    assert '<option value="alpha"' not in body
    assert (
        'value="beta" data-encounter-title="Beta" data-requires-revelations="find-beta" disabled'
    ) in body
    assert 'data-play-transition-summary aria-live="polite" hidden' in body
    assert "This will record:" not in body
    assert "The encounter notebook is the visit record" not in body
    assert "Save outcomes without moving" in body
    assert "Split-party label" in body


def test_secondary_play_pages_preserve_the_same_navigation_and_context_rails() -> None:
    app, _ = build_play_app()
    pages = (
        ("/play/ledgers", "kind=narrative&scope=playthrough"),
        ("/play/ledgers", "kind=encounters&scope=playthrough"),
        ("/journal", ""),
        ("/run", ""),
    )

    for path, query in pages:
        status, _, body = request_wsgi(app, path, query=query)

        assert status == "200 OK"
        assert body.count('<aside class="play-route-rail"') == 1
        assert body.count('<aside class="play-utility-rail"') == 1
        left_rail = body.split('<aside class="play-route-rail"', 1)[1].split("</aside>", 1)[0]
        right_rail = body.split('<aside class="play-utility-rail"', 1)[1].split("</aside>", 1)[0]
        assert 'aria-label="Play navigation"' in left_rail
        assert "Find authored material" in left_rail
        assert 'href="/play"' in left_rail
        assert 'href="/journal"' in left_rail
        assert "Current visit actions" in right_rail
        assert "Dice tray" in right_rail
        assert "What happened so far" in right_rail
        assert "play-ledger-quick-links" not in right_rail
        assert "data-play-encounter-record" in body


def test_play_mode_renders_navigation_without_recording_play() -> None:
    app, project = build_play_app()
    before = project.snapshot

    status, _, body = request_wsgi(app, "/play")

    assert status == "200 OK"
    assert "Chronological route" in body
    assert "Focused encounter" in body
    assert "The focused encounter is also the current recorded visit." in body
    assert "data-play-route-link" in body
    assert "data-play-pin-toggle" in body
    assert "data-play-search" in body
    assert 'href="/play" aria-current="page"' in body
    assert 'href="/play/ledgers?kind=narrative&scope=playthrough"' in body
    assert "<span>History</span>" in body
    assert 'href="/reports"' not in body
    assert "data-play-pin-panel hidden" in body
    assert "Pinned for reference" in body
    assert "Pinning never records a visit" in body
    assert "Encounter notes" in body
    assert "Open Run console" not in body
    assert "Recovery console" in body
    assert project.snapshot == before


def test_play_dice_roll_is_ephemeral_until_explicitly_recorded() -> None:
    app, project = build_play_app()
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/play/dice/roll",
        method="POST",
        form={
            "csrf_token": "known-token",
            "focus_encounter_id": "alpha",
            "expression": "2D6+3",
            "label": "Hold the gate",
        },
    )

    assert status == "200 OK"
    assert "Dice tray" in body
    assert 'data-expression="2d6 + 3"' in body
    assert "Hold the gate" in body
    assert "<strong>15</strong>" in body
    assert body.count("<span>6</span>") >= 2
    assert 'action="/play/dice/record"' in body
    assert "Insert in notebook" in body
    assert project.snapshot == before


def test_play_dice_roll_rejects_invalid_expression_without_touching_journal() -> None:
    app, project = build_play_app()
    before = project.snapshot

    status, _, body = request_wsgi(
        app,
        "/play/dice/roll",
        method="POST",
        form={
            "csrf_token": "known-token",
            "focus_encounter_id": "alpha",
            "expression": "1001d6",
            "label": "Too many dice",
        },
    )

    assert status == "422 Unprocessable Content"
    assert "Dice expression was not rolled" in body
    assert 'value="1001d6"' in body
    assert 'value="Too many dice"' in body
    assert project.snapshot == before


def test_play_dice_roll_records_the_exact_submitted_result_on_request() -> None:
    app, project = build_play_app()
    payload = json.dumps(
        {
            "expression": "2d6 + 3",
            "terms": [
                {"kind": "dice", "sign": 1, "faces": 6, "results": [6, 6]},
                {"kind": "modifier", "value": 3},
            ],
            "total": 15,
        },
        separators=(",", ":"),
    )

    status, headers, body = request_wsgi(
        app,
        "/play/dice/record",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "focus_encounter_id": "alpha",
            "label": "Hold the gate",
            "roll_payload": payload,
        },
    )

    assert status == "303 See Other"
    assert body == ""
    assert headers["Location"] == "/play?action=dice-recorded&operation=2&encounter=alpha"
    event = project.snapshot.state.events[-1]
    assert isinstance(event, DiceRollRecordedEvent)
    assert event.expression == "2d6 + 3"
    assert event.total == 15
    assert event.label == "Hold the gate"
    first_term = event.terms[0]
    assert isinstance(first_term, DiceGroupResult)
    assert first_term.results == (6, 6)


def test_play_dice_record_rejects_a_tampered_total() -> None:
    app, project = build_play_app()
    before = project.snapshot
    payload = json.dumps(
        {
            "expression": "1d6",
            "terms": [{"kind": "dice", "sign": 1, "faces": 6, "results": [6]}],
            "total": 5,
        },
        separators=(",", ":"),
    )

    status, _, body = request_wsgi(
        app,
        "/play/dice/record",
        method="POST",
        form={
            "csrf_token": "known-token",
            "expected_revision": "play-revision-1",
            "focus_encounter_id": "alpha",
            "label": "Changed in transit",
            "roll_payload": payload,
        },
    )

    assert status == "422 Unprocessable Content"
    assert "Play operation was not recorded" in body
    assert "does not match" in body
    assert project.snapshot == before


def test_play_mode_browses_locked_encounter_without_changing_current_visit() -> None:
    app, project = build_play_app()
    before = project.snapshot

    status, _, body = request_wsgi(app, "/play", query="encounter=omega")

    assert status == "200 OK"
    assert "<h1>Omega</h1>" in body
    assert "Browsing Omega; the current recorded visit remains Alpha." in body
    assert "No journal event was added." in body
    assert "<span>Locked</span>" in body
    assert 'data-encounter-id="omega" aria-pressed="false"' in body
    assert project.snapshot == before


def test_play_mode_invalid_focus_falls_back_to_current_visit() -> None:
    app, _ = build_play_app()

    status, _, body = request_wsgi(app, "/play", query="encounter=not-a-encounter")

    assert status == "200 OK"
    assert "<h1>Alpha</h1>" in body
    assert "The focused encounter is also the current recorded visit." in body


def test_play_mode_escapes_authored_values_and_sanitizes_markdown() -> None:
    adventure = complete_four_encounter_adventure()
    alpha = adventure.encounter_index()["alpha"]
    unsafe = replace(
        adventure,
        title='Complete Four <script>alert("title")</script>',
        encounters=tuple(
            replace(
                encounter,
                title='Alpha" onmouseover="alert(1)',
                opening_view='<script>alert("opening")</script> **safe emphasis**',
            )
            if encounter.id == alpha.id
            else encounter
            for encounter in adventure.encounters
        ),
    )
    state = record_visit(unsafe, new_play_state(unsafe), "alpha")
    app, _ = build_play_app(unsafe, state)

    status, _, body = request_wsgi(app, "/play")

    assert status == "200 OK"
    assert '<script>alert("title")</script>' not in body
    assert '<script>alert("opening")</script>' not in body
    assert "&lt;script&gt;alert(&quot;title&quot;)&lt;/script&gt;" in body
    assert 'data-title="Alpha&quot; onmouseover=&quot;alert(1)"' in body
    assert "<strong>safe emphasis</strong>" in body


def test_authored_prose_exposes_field_targeted_double_click_editing() -> None:
    app, _ = build_authoring_app()

    _, _, overview = request_wsgi(app, "/")
    _, _, encounter = request_wsgi(app, "/encounters/alpha")
    _, _, revelation = request_wsgi(app, "/revelations/find-beta")
    _, _, clue = request_wsgi(app, "/clues/alpha-to-beta")

    assert 'data-edit-href="/adventure/edit#title"' in overview
    assert 'data-edit-href="/adventure/edit#premise"' in overview
    assert 'data-edit-href="/encounters/alpha/edit#summary"' in encounter
    assert 'data-edit-href="/encounters/alpha/edit#opening_view"' in encounter
    assert 'data-edit-href="/revelations/find-beta/edit#description"' in revelation
    assert 'data-edit-href="/clues/alpha-to-beta/edit#description"' in clue
    assert 'title="Double-click or press Enter to edit"' in overview


def test_editors_expose_focus_cancel_and_draft_controls() -> None:
    app, _ = build_authoring_app()

    _, _, adventure = request_wsgi(app, "/adventure/edit")
    _, _, encounter = request_wsgi(app, "/encounters/alpha/edit")

    assert 'id="premise" name="premise"' in adventure
    assert 'data-cancel-href="/"' in adventure
    assert "Discard browser draft" in adventure
    assert 'id="opening_view" name="opening_view"' in encounter
    assert 'data-cancel-href="/encounters/alpha"' in encounter
    assert "Esc returns without discarding this browser draft" in encounter


def test_notebook_and_encounter_sections_have_independent_scroll_bounds() -> None:
    app, _ = build_authoring_app()

    _, _, css = request_wsgi(app, "/assets/app.css")

    assert ".play-encounter-section-scroll {" in css
    assert "max-height: min(56vh, 46rem);\n  overflow: auto;" in css
    assert ".play-encounter-notes-section .play-encounter-section-scroll" in css
    assert "min-height: 220px;\n  resize: vertical;" in css
    assert ".play-prose-measure { width: min(100%, 82ch); }" in css
    assert ".play-reading-workspace" not in css


def test_play_mobile_drawers_and_dynamic_statuses_expose_accessible_relationships() -> None:
    app, _ = build_play_app()

    status, _, body = request_wsgi(app, "/play")

    assert status == "200 OK"
    assert 'id="play-route-drawer"' in body
    assert 'id="play-utility-drawer"' in body
    assert 'data-play-drawer-toggle="route" aria-controls="play-route-drawer"' in body
    assert 'data-play-drawer-toggle="utility" aria-controls="play-utility-drawer"' in body
    assert 'data-play-drawer-close aria-hidden="true" hidden' in body
    assert 'class="play-search-status" role="status" aria-live="polite" aria-atomic="true"' in body


def test_play_interaction_assets_cover_motion_scroll_drawer_and_print_contracts() -> None:
    app, _ = build_play_app()

    _, _, css = request_wsgi(app, "/assets/app.css")
    _, _, javascript = request_wsgi(app, "/assets/app.js")

    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "scrollbar-gutter: stable;" in css
    assert "overscroll-behavior: contain" not in css
    assert ".play-encounter-section-scroll:focus-visible" in css
    assert "max-height: none !important;" in css
    assert ".play-clue-list, .play-path-list, .play-linked-reference-list" in css
    assert 'const mobileDrawerMedia = window.matchMedia("(max-width: 1000px)")' in javascript
    assert "drawer.inert = mobile && !open;" in javascript
    assert 'drawer.setAttribute("aria-hidden", String(!open));' in javascript
    assert "firstDrawerControl(drawer)?.focus" in javascript
    assert "buttonToRestore.focus" in javascript
    assert "button, a[href], summary" in javascript


def test_appearance_and_interaction_assets_are_available_on_every_page() -> None:
    app, _ = build_authoring_app()

    _, _, overview = request_wsgi(app, "/")
    _, _, css = request_wsgi(app, "/assets/app.css")
    _, _, javascript = request_wsgi(app, "/assets/app.js")

    assert "data-theme-toggle" in overview
    assert '<meta name="color-scheme" content="light dark">' in overview
    assert ':root[data-theme="dark"]' in css
    assert ".editable-surface" in css
    assert ".play-dice-result" in css
    assert ".play-encounter-section-stack" in css
    assert ".play-encounter-section-scroll" in css
    assert ".overview-synopsis" in css
    assert ".play-secondary-body .play-main" in css
    assert ".play-main { min-width: 0; overflow: visible;" in css
    assert "width: min(1420px, calc(100% - 36px));" in css
    assert 'const THEME_KEY = "adventure-graph:appearance"' in javascript
    assert "data-play-encounter-section-scroll" in javascript
    assert "reading-layout" not in javascript
    assert "initializePlaySharedChrome" in javascript
    assert "pinPanel.hidden = pins.length === 0" in javascript
    assert "data-play-transition-destination" in javascript
    assert "data-play-transition-submit" in javascript
    assert "data-play-transition-summary" in javascript
    assert "const manyRevelations = revelationCount >= 3;" in javascript
    assert "const largeUpdate = recordedOutcomeCount >= 5;" in javascript
    assert (
        "const bundledMove = Boolean(destination.value) && recordedOutcomeCount >= 3;" in javascript
    )
    assert "This will record:" in javascript
    assert 'pluralized(foundCount, "lead", "leads")' in javascript
    assert 'pluralized(missedCount, "lead", "leads")' in javascript
    assert 'pluralized(foundCount, "clue", "clues")' not in javascript
    assert 'pluralized(missedCount, "clue", "clues")' not in javascript
    assert ".play-transition-summary" in css
    assert "Save visit and move" in javascript
    assert "referenceRatio" not in javascript
    assert "scroll-return" in javascript
    assert "preserveScrollActions" in javascript
    assert 'divider.addEventListener("pointerdown"' not in javascript
    assert 'surface.addEventListener("dblclick"' in javascript
    assert "window.location.hash.slice(1)" in javascript
    assert "data-discard-draft" in javascript
    assert 'event.key.toLowerCase() === "s"' in javascript
