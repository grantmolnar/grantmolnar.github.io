"""Exhaustive persisted-string escaping evidence for the local web adapter."""

from __future__ import annotations

from dataclasses import replace
from html import escape

from adventure_graph.application.archive_management import (
    AdventureSnapshotComparison,
    ArchiveDetailResult,
    EntityComparison,
    JournalArchiveSnapshot,
)
from adventure_graph.application.dice import roll_dice
from adventure_graph.application.play_tracking import (
    add_visit_note,
    correct_latest_operation,
    end_session,
    establish_revelation,
    foreclose_revelation,
    miss_clue,
    new_play_state,
    record_dice_roll,
    record_encounter_consequence,
    record_reference_note,
    record_visit,
    reopen_revelation,
    start_session,
    unlock_encounter,
)
from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.run_workspace import GetRunDashboard
from adventure_graph.domain.adventure import Adventure, AdventureTags
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.interfaces.web.archive_rendering import render_archive_detail
from adventure_graph.interfaces.web.page_rendering import MetricLink, render_error, render_metrics
from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)
from tests.support.projects import read_only_play_project
from tests.support.web import build_play_app, request_wsgi


def _payload(name: str) -> str:
    return f'<img src=x onerror="{name}">'


def _hostile_adventure() -> Adventure:
    adventure = complete_four_encounter_adventure()
    encounters = tuple(
        replace(
            encounter,
            title=_payload("enc-title"),
            summary=_payload("enc-summary"),
            opening_view=_payload("enc-open"),
            content=_payload("enc-content"),
            tags=(_payload("enc-tag"),),
        )
        if encounter.id == "alpha"
        else encounter
        for encounter in adventure.encounters
    )
    revelations = tuple(
        replace(
            revelation,
            title=_payload("rev-title"),
            description=_payload("rev-desc"),
        )
        if revelation.id == "find-beta"
        else revelation
        for revelation in adventure.revelations
    )
    clues = tuple(
        replace(
            clue,
            title=_payload("clue-title"),
            description=_payload("clue-desc"),
            discovery=_payload("clue-disc"),
        )
        if clue.id == "alpha-to-beta"
        else clue
        for clue in adventure.clues
    )
    return replace(
        adventure,
        title=_payload("adv-title"),
        synopsis=_payload("synopsis"),
        premise=_payload("premise"),
        explanation=_payload("explanation"),
        encounters=encounters,
        revelations=revelations,
        clues=clues,
        tags=AdventureTags(
            genres=(_payload("genre"),),
            game_systems=(_payload("system"),),
            settings=(_payload("setting"),),
            keywords=(_payload("keyword"),),
        ),
    )


def _hostile_play_state(adventure: Adventure) -> PlayState:
    state = new_play_state(adventure)
    state = start_session(
        state,
        title=_payload("session-title"),
        played_on="2026-07-25",
        participants=(_payload("participant"),),
        attendance_note=_payload("attendance"),
        opening_note=_payload("opening-note"),
    )
    state = record_visit(
        adventure,
        state,
        "alpha",
        ("alpha-to-beta",),
        (_payload("visit-note"),),
        party_label=_payload("party"),
    )
    state = miss_clue(adventure, state, "alpha-to-gamma", 1)
    state = establish_revelation(
        adventure,
        state,
        "find-beta",
        ("alpha-to-beta",),
        _payload("establish-note"),
    )
    state = foreclose_revelation(adventure, state, "find-gamma", _payload("foreclose"))
    state = reopen_revelation(adventure, state, "find-gamma", _payload("reopen"))
    state = unlock_encounter(adventure, state, "gamma", _payload("unlock"))
    state = add_visit_note(state, 1, _payload("added-note"))
    state = record_encounter_consequence(
        adventure,
        state,
        "alpha",
        _payload("consequence"),
    )
    state = record_dice_roll(
        state,
        roll_dice("1d6", randbelow=lambda _bound: 0),
        _payload("dice-label"),
    )
    state = end_session(state, _payload("closing"))
    return correct_latest_operation(adventure, state, _payload("correction"))


_RENDERING_SURFACES = {
    "overview": ("/", ""),
    "adventure-edit": ("/adventure/edit", ""),
    "encounter-detail": ("/encounters/alpha", ""),
    "encounter-edit": ("/encounters/alpha/edit", ""),
    "revelation-detail": ("/revelations/find-beta", ""),
    "revelation-edit": ("/revelations/find-beta/edit", ""),
    "clue-detail": ("/clues/alpha-to-beta", ""),
    "clue-edit": ("/clues/alpha-to-beta/edit", ""),
    "structure": ("/structure", ""),
    "play": ("/play", "encounter=alpha"),
    "run": ("/run", ""),
    "journal": ("/journal", ""),
    "encounter-ledger": (
        "/play/ledgers",
        "kind=encounters&scope=playthrough",
    ),
    "clue-ledger": ("/play/ledgers", "kind=clues&scope=playthrough"),
    "revelation-ledger": (
        "/play/ledgers",
        "kind=revelations&scope=playthrough",
    ),
    "narrative-ledger": (
        "/play/ledgers",
        "kind=narrative&scope=playthrough",
    ),
}

_ALL_SURFACES = frozenset(_RENDERING_SURFACES)
_PLAY_SURFACES = frozenset(
    {
        "play",
        "run",
        "journal",
        "encounter-ledger",
        "clue-ledger",
        "revelation-ledger",
        "narrative-ledger",
    }
)

_EXPECTED_SURFACES = {
    "adv-title": _ALL_SURFACES,
    "synopsis": frozenset({"overview", "adventure-edit"}),
    "premise": frozenset({"overview", "adventure-edit"}),
    "explanation": frozenset({"overview", "adventure-edit"}),
    "genre": frozenset({"overview", "adventure-edit"}),
    "system": frozenset({"overview", "adventure-edit"}),
    "setting": frozenset({"overview", "adventure-edit"}),
    "keyword": frozenset({"overview", "adventure-edit"}),
    "enc-title": _ALL_SURFACES,
    "enc-summary": frozenset(
        {
            "overview",
            "encounter-detail",
            "encounter-edit",
            *_PLAY_SURFACES,
        }
    ),
    "enc-open": frozenset({"encounter-detail", "encounter-edit", *_PLAY_SURFACES}),
    "enc-content": frozenset({"encounter-detail", "encounter-edit", *_PLAY_SURFACES}),
    "enc-tag": frozenset(
        {
            "overview",
            "encounter-detail",
            "encounter-edit",
            *_PLAY_SURFACES,
        }
    ),
    "rev-title": _ALL_SURFACES,
    "rev-desc": frozenset(
        {
            "overview",
            "revelation-detail",
            "revelation-edit",
            *_PLAY_SURFACES,
        }
    ),
    "clue-title": _ALL_SURFACES,
    "clue-desc": frozenset(
        {
            "encounter-detail",
            "revelation-detail",
            "clue-detail",
            "clue-edit",
            *_PLAY_SURFACES,
        }
    ),
    "clue-disc": frozenset(
        {
            "encounter-detail",
            "revelation-detail",
            "clue-detail",
            "clue-edit",
            *_PLAY_SURFACES,
        }
    ),
    "session-title": _PLAY_SURFACES,
    "participant": _PLAY_SURFACES,
    "attendance": frozenset({"journal"}),
    "opening-note": frozenset({"journal", "narrative-ledger"}),
    "party": _PLAY_SURFACES,
    "visit-note": frozenset({"play", "run", "journal", "narrative-ledger"}),
    "establish-note": frozenset({"run", "journal", "revelation-ledger", "narrative-ledger"}),
    "foreclose": frozenset({"run", "journal", "narrative-ledger"}),
    "reopen": frozenset({"run", "journal", "narrative-ledger"}),
    "unlock": frozenset({"run", "journal", "narrative-ledger"}),
    "added-note": _PLAY_SURFACES,
    "consequence": frozenset({"play", "run", "journal", "encounter-ledger", "narrative-ledger"}),
    "dice-label": _PLAY_SURFACES,
    "closing": frozenset({"run", "journal"}),
    "correction": frozenset({"run", "journal"}),
}


def test_every_persisted_authored_and_journal_string_is_escaped_at_its_html_sinks() -> None:
    adventure = _hostile_adventure()
    app, _ = build_play_app(adventure, _hostile_play_state(adventure))

    pages: dict[str, str] = {}
    for name, (path, query) in _RENDERING_SURFACES.items():
        status, _, body = request_wsgi(app, path, query=query)
        assert status == "200 OK", name
        pages[name] = body

    for field_name, expected_surfaces in _EXPECTED_SURFACES.items():
        raw = _payload(field_name)
        escaped = escape(raw, quote=True)
        for surface_name, body in pages.items():
            assert raw not in body, (field_name, surface_name)
        for surface_name in expected_surfaces:
            assert escaped in pages[surface_name], (field_name, surface_name)


def test_error_rendering_preserves_authored_clue_words_verbatim() -> None:
    rendered = render_error(404, "Missing authored record", "The Clue Club is missing.", "Project")

    assert "The Clue Club is missing." in rendered
    assert "The Lead Club is missing." not in rendered


def test_metric_values_are_text_unless_the_caller_supplies_a_structured_link() -> None:
    raw = _payload("metric")
    href = '/encounters/alpha?next="beta"&mode=detail'

    rendered = render_metrics(
        (
            (raw, raw),
            (MetricLink(raw, href), "Destination"),
        )
    )

    assert raw not in rendered
    assert rendered.count(escape(raw, quote=True)) == 3
    assert f'<a href="{escape(href, quote=True)}">{escape(raw, quote=True)}</a>' in rendered


def test_archive_timestamp_uses_the_escaped_metric_value_contract() -> None:
    raw = _payload("archived-at")
    adventure = complete_four_encounter_adventure()
    state = new_play_state(adventure)
    unchanged = EntityComparison((), (), ())
    comparison = AdventureSnapshotComparison(
        identical=True,
        compatible=True,
        compatibility_message="Compatible.",
        title_changed=False,
        synopsis_changed=False,
        premise_changed=False,
        explanation_changed=False,
        tags_changed=False,
        encounters=unchanged,
        revelations=unchanged,
        clues=unchanged,
    )
    archive = JournalArchiveSnapshot(
        archive_id="archive-1",
        label="Archive",
        archived_at=raw,
        source_state_name="play-state.json",
        adventure_snapshot=adventure,
        play_state=state,
    )
    result = ArchiveDetailResult(
        adventure=adventure,
        validation_report=validate_adventure(adventure),
        archive=archive,
        revision=ProjectRevision("archive-revision"),
        active_event_count=0,
        comparison=comparison,
    )
    dashboard = GetRunDashboard(
        read_only_play_project(state, adventure, revision="archive-revision")
    ).execute()

    rendered = render_archive_detail(
        result,
        "memory://adventure.json",
        csrf_token="known-token",
        dashboard=dashboard,
    )

    assert raw not in rendered
    assert escape(raw, quote=True) in rendered


def test_reference_note_is_escaped_in_entity_journal_and_narrative_surfaces() -> None:
    adventure = reference_library_adventure()
    state = start_session(new_play_state(adventure), title="Reference review")
    state = record_reference_note(
        adventure,
        state,
        PERSON_REFERENCE_ID,
        _payload("reference-note"),
    )
    app, _ = build_play_app(adventure, state)
    surfaces = (
        ("/play", f"encounter=alpha&reference={PERSON_REFERENCE_ID}"),
        ("/journal", ""),
        ("/play/ledgers", "kind=narrative&scope=playthrough"),
    )

    raw = _payload("reference-note")
    escaped = escape(raw, quote=True)
    for path, query in surfaces:
        status, _, body = request_wsgi(app, path, query=query)
        assert status == "200 OK"
        assert raw not in body
        assert escaped in body
