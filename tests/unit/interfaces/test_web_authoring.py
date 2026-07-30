"""Tests for the dependency-injected local authoring WSGI adapter."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Never

from adventure_graph.application.errors import EntityNotFoundError
from adventure_graph.application.project import ProjectRevision
from adventure_graph.domain.adventure import Adventure
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.web import (
    adventure_form,
    build_authoring_app,
    build_play_app,
    encounter_form,
    existing_clue_form,
    existing_revelation_form,
    new_clue_form,
    new_encounter_form,
    new_revelation_form,
    request_wsgi,
    visible_page_text,
)


def test_external_nomenclature_uses_encounters_and_leads_while_preserving_clue_routes() -> None:
    adventure = replace(
        complete_four_encounter_adventure(),
        synopsis="A complete information graph.",
        premise="Investigate four connected encounters.",
        explanation="Every encounter points to every other encounter.",
    )
    authoring_app, _ = build_authoring_app(adventure)
    play_app, _ = build_play_app(adventure)
    pages = (
        (authoring_app, "/", ""),
        (authoring_app, "/structure", ""),
        (authoring_app, "/encounters/alpha", ""),
        (authoring_app, "/encounters/alpha/edit", ""),
        (authoring_app, "/encounters/new", ""),
        (authoring_app, "/revelations/find-beta", ""),
        (authoring_app, "/clues/alpha-to-beta", ""),
        (play_app, "/play", ""),
        (play_app, "/run", ""),
        (play_app, "/journal", ""),
        (play_app, "/play/ledgers", "kind=encounters&scope=playthrough"),
        (play_app, "/play/ledgers", "kind=clues&scope=playthrough"),
        (play_app, "/play/ledgers", "kind=revelations&scope=playthrough"),
        (play_app, "/play/ledgers", "kind=narrative&scope=playthrough"),
    )

    visible_pages: list[str] = []
    for app, path, query in pages:
        status, _, body = request_wsgi(app, path, query=query)
        assert status == "200 OK"
        visible_pages.append(visible_page_text(body))

    combined = " ".join(visible_pages)
    assert re.search(r"\bnodes?\b", combined, re.IGNORECASE) is None
    assert "Encounters" in combined
    assert "Leads" in combined
    assert re.search(r"\bClues?\b", combined) is None


def test_overview_renders_navigation_metrics_and_security_headers() -> None:
    app, _ = build_authoring_app()

    status, headers, body = request_wsgi(app, "/")

    assert status == "200 OK"
    assert headers["Content-Type"] == "text/html; charset=utf-8"
    assert "default-src 'self'" in headers["Content-Security-Policy"]
    assert "script-src 'self'" in headers["Content-Security-Policy"]
    assert "form-action 'self'" in headers["Content-Security-Policy"]
    assert "Complete Four" in body
    assert "Adventure overview" in body
    assert 'class="lede overview-synopsis editable-surface"' in body
    assert ">Play adventure</a>" in body
    assert ">Inspect structure</a>" in body
    assert ">Edit adventure</a>" in body
    assert "data-navigation-filter" in body
    assert 'placeholder="Filter titles"' in body
    assert body.count('data-disclosure-default="collapsed"') == 4
    assert body.count("data-ui-disclosure-toggle") == 4
    assert body.count("data-ui-disclosure-content hidden") == 4
    for kind in ("encounter", "revelation", "clue", "reference"):
        assert f'data-disclosure-storage-key="adventure-graph:author-navigation:{kind}"' in body
    assert "memory://adventure.json" not in body
    assert "Loaded revision" not in body
    assert "Save protection" not in body
    assert ">4</strong><span>Encounters" in body
    assert 'href="/encounters/alpha"' in body
    assert 'href="/revelations/find-beta"' in body
    assert 'href="/clues/alpha-to-beta"' in body
    assert 'class="marker"' not in body
    assert '<p class="identifier">' not in body


def test_encounter_revelation_and_clue_pages_render_relationships() -> None:
    app, _ = build_authoring_app()

    encounter_status, _, encounter_body = request_wsgi(app, "/encounters/beta")
    revelation_status, _, revelation_body = request_wsgi(app, "/revelations/find-beta")
    clue_status, _, clue_body = request_wsgi(app, "/clues/alpha-to-beta")

    assert encounter_status == revelation_status == clue_status == "200 OK"
    assert "Leads at this encounter" in encounter_body
    assert "Incoming pathways" in encounter_body
    assert "Necessary" in encounter_body
    assert 'href="/encounters/beta/edit"' in encounter_body
    assert "Supporting leads" in revelation_body
    assert "Necessary" in revelation_body
    assert "Distinct sources" in revelation_body
    assert "Authored pathway" in clue_body
    assert "Source encounter" in clue_body
    assert "Revelation" in clue_body
    assert "Destination" in clue_body


def test_adventure_revelation_and_clue_editors_are_gm_facing() -> None:
    app, _ = build_authoring_app()

    adventure_status, _, adventure_body = request_wsgi(app, "/adventure/edit")
    revelation_status, _, revelation_body = request_wsgi(app, "/revelations/find-beta/edit")
    clue_status, _, clue_body = request_wsgi(app, "/clues/alpha-to-beta/edit")

    assert adventure_status == revelation_status == clue_status == "200 OK"
    assert 'action="/adventure/edit"' in adventure_body
    assert 'name="premise"' in adventure_body
    assert 'name="explanation"' in adventure_body
    assert 'name="genres"' in adventure_body
    assert 'name="game_systems"' in adventure_body
    assert 'name="combat_intensity"' in adventure_body
    assert 'action="/revelations/find-beta/edit"' in revelation_body
    assert '<option value="beta" selected>Beta</option>' in revelation_body
    assert "Necessary revelation" in revelation_body
    assert 'action="/clues/alpha-to-beta/edit"' in clue_body
    assert '<option value="alpha" selected>Alpha</option>' in clue_body
    assert '<option value="find-beta" selected>Find Beta</option>' in clue_body
    assert '<p class="identifier">' not in revelation_body + clue_body


def test_adventure_revelation_and_clue_title_edits_preserve_ids_and_redirect() -> None:
    adventure_app, adventure_project = build_authoring_app()
    adventure_status, adventure_headers, _ = request_wsgi(
        adventure_app,
        "/adventure/edit",
        "POST",
        form=adventure_form(title="The Complete Four"),
    )

    assert adventure_status == "303 See Other"
    assert adventure_headers["Location"] == "/?saved=1&draft=complete-four"
    assert adventure_project.snapshot.adventure.id == "complete-four"

    revelation_app, revelation_project = build_authoring_app()
    revelation_status, revelation_headers, _ = request_wsgi(
        revelation_app,
        "/revelations/find-beta/edit",
        "POST",
        form=existing_revelation_form(title="Locate Beta"),
    )

    assert revelation_status == "303 See Other"
    assert revelation_headers["Location"] == ("/revelations/find-beta?saved=1&draft=find-beta")
    assert all(
        clue.revelation_id == "find-beta"
        for clue in revelation_project.snapshot.adventure.clues
        if clue.title.endswith("to beta")
    )

    clue_app, clue_project = build_authoring_app()
    clue_status, clue_headers, _ = request_wsgi(
        clue_app,
        "/clues/alpha-to-beta/edit",
        "POST",
        form=existing_clue_form(title="The first path to Beta"),
    )

    assert clue_status == "303 See Other"
    assert clue_headers["Location"] == ("/clues/alpha-to-beta?saved=1&draft=alpha-to-beta")
    assert clue_project.snapshot.adventure.clue_index()["alpha-to-beta"].title == (
        "The first path to Beta"
    )


def test_encounter_editor_exposes_revision_csrf_and_browser_draft_contract() -> None:
    app, _ = build_authoring_app()

    status, _, body = request_wsgi(app, "/encounters/alpha/edit")

    assert status == "200 OK"
    assert 'method="post" action="/encounters/alpha/edit"' in body
    assert 'name="csrf_token" value="known-token"' in body
    assert 'name="expected_revision" value="revision-1"' in body
    assert 'data-encounter-editor data-draft-key="adventure-graph:draft:' in body
    assert 'data-current-revision="revision-1"' in body
    assert 'name="opening_view"' in body
    assert 'name="content"' in body
    assert "Necessary encounter" in body
    assert ">Summary for alpha.</textarea>" in body
    assert "Ctrl/⌘ S" in body
    assert "Protected save" not in body
    assert ">Save encounter</button>" in body
    assert ">Save encounter <span>" not in body
    assert "Loaded revision" not in body
    assert "memory://adventure.json" not in body


def test_encounter_editor_commits_then_redirects_and_clears_browser_draft() -> None:
    app, project = build_authoring_app()

    status, headers, body = request_wsgi(
        app,
        "/encounters/alpha/edit",
        "POST",
        form=encounter_form(
            title="Atrium",
            summary="A revised threshold.",
            content="## Arrival\n\nLong-form encounter material.",
            tags="urban, threshold",
        ),
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/encounters/alpha?saved=1&draft=alpha"
    assert body == ""
    assert project.commit_count == 1
    encounter = project.snapshot.adventure.encounter_index()["alpha"]
    assert encounter.title == "Atrium"
    assert encounter.summary == "A revised threshold."
    assert encounter.content == "## Arrival\n\nLong-form encounter material."
    assert encounter.tags == ("urban", "threshold")
    assert encounter.start
    assert not encounter.end

    get_status, _, get_body = request_wsgi(app, "/encounters/alpha", query="saved=1")
    assert get_status == "200 OK"
    assert "Encounter saved" in get_body
    assert "Atrium" in get_body
    assert 'data-clear-draft-key="adventure-graph:draft:' in get_body


def test_encounter_editor_can_mark_a_encounter_optional() -> None:
    app, project = build_authoring_app()
    form = encounter_form()
    form.pop("required")

    status, headers, _ = request_wsgi(
        app,
        "/encounters/alpha/edit",
        "POST",
        form=form,
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/encounters/alpha?saved=1&draft=alpha"
    assert not project.snapshot.adventure.encounter_index()["alpha"].required


def test_revelation_creation_can_mark_a_revelation_optional() -> None:
    app, project = build_authoring_app()
    form = new_revelation_form()
    form.pop("required")

    status, _, _ = request_wsgi(app, "/revelations/new", "POST", form=form)

    assert status == "303 See Other"
    assert not project.snapshot.adventure.revelation_index()["find-the-hidden-vault"].required


def test_revision_conflict_preserves_submitted_values_without_committing() -> None:
    app, project = build_authoring_app()
    project.snapshot = replace(project.snapshot, revision=ProjectRevision("revision-2"))

    status, _, body = request_wsgi(
        app,
        "/encounters/alpha/edit",
        "POST",
        form=encounter_form(title="My unsaved & conflicted title"),
    )

    assert status == "409 Conflict"
    assert project.commit_count == 0
    assert "Revision conflict" in body
    assert "My unsaved &amp; conflicted title" in body
    assert 'name="expected_revision" value="revision-1"' in body
    assert 'data-current-revision="revision-2"' in body
    assert 'data-server-values="true"' in body
    assert "browser draft" in body


def test_encounter_editor_does_not_invent_nonempty_domain_rules() -> None:
    app, project = build_authoring_app()

    status, headers, _ = request_wsgi(
        app,
        "/encounters/alpha/edit",
        "POST",
        form=encounter_form(title="", summary=""),
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/encounters/alpha?saved=1&draft=alpha"
    encounter = project.snapshot.adventure.encounter_index()["alpha"]
    assert encounter.title == ""
    assert encounter.summary == ""


def test_encounter_editor_refuses_missing_or_invalid_csrf_token() -> None:
    app, project = build_authoring_app()

    status, _, body = request_wsgi(
        app,
        "/encounters/alpha/edit",
        "POST",
        form=encounter_form(csrf_token="wrong-token"),
    )

    assert status == "403 Forbidden"
    assert "Form token rejected" in body
    assert project.commit_count == 0


def test_adventure_editor_rejects_partial_tag_metadata() -> None:
    app, project = build_authoring_app()

    status, _, body = request_wsgi(
        app,
        "/adventure/edit",
        "POST",
        form=adventure_form(genres="Investigation"),
    )

    assert status == "400 Bad Request"
    assert "Adventure tag fields must be submitted together" in body
    assert project.commit_count == 0


def test_encounter_editor_rejects_malformed_forms_and_non_form_media_types() -> None:
    app, project = build_authoring_app()
    missing = encounter_form()
    del missing["title"]

    missing_status, _, missing_body = request_wsgi(
        app,
        "/encounters/alpha/edit",
        "POST",
        form=missing,
    )
    media_status, _, media_body = request_wsgi(
        app,
        "/encounters/alpha/edit",
        "POST",
        form=encounter_form(),
        content_type="application/json",
    )

    assert missing_status == "400 Bad Request"
    assert "Required form field" in missing_body
    assert media_status == "400 Bad Request"
    assert "application/x-www-form-urlencoded" in media_body
    assert project.commit_count == 0


def test_noop_save_redirects_without_writing() -> None:
    app, project = build_authoring_app()

    status, headers, _ = request_wsgi(
        app,
        "/encounters/alpha/edit",
        "POST",
        form=encounter_form(),
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/encounters/alpha?saved=unchanged"
    assert project.commit_count == 0


def test_validation_findings_use_gm_facing_headings_without_diagnostic_codes() -> None:
    adventure = replace(complete_four_encounter_adventure(), premise="")
    app, _ = build_authoring_app(adventure)

    status, _, body = request_wsgi(app, "/")

    assert status == "200 OK"
    assert "Premise is empty" in body
    assert "adventure-premise-empty" not in body
    assert '<span class="issue-severity">Warning</span>' in body


def test_authored_html_is_escaped_before_rendering() -> None:
    adventure = complete_four_encounter_adventure()
    hostile = Adventure(
        id=adventure.id,
        title='<script>alert("title")</script>',
        synopsis=adventure.synopsis,
        premise=adventure.premise,
        explanation='<img src=x onerror="alert(1)"> **safe emphasis**',
        encounters=adventure.encounters,
        revelations=adventure.revelations,
        clues=adventure.clues,
        validation_policy=adventure.validation_policy,
    )
    app, _ = build_authoring_app(hostile)

    _, _, body = request_wsgi(app, "/")

    assert "<script>alert" not in body
    assert "<img" not in body
    assert "&lt;script&gt;" in body
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in body
    assert "<strong>safe emphasis</strong>" in body


def test_not_found_status_depends_on_type_not_message_prefix() -> None:
    app, _ = build_authoring_app()

    def missing_encounter(encounter_id: str) -> Never:
        del encounter_id
        raise EntityNotFoundError("The requested encounter is absent.")

    app = replace(app, queries=replace(app.queries, get_encounter=missing_encounter))

    status, _, body = request_wsgi(app, "/encounters/missing")

    assert status == "404 Not Found"
    assert "The requested encounter is absent" in body


def test_value_error_prose_cannot_accidentally_select_not_found_status() -> None:
    app, _ = build_authoring_app()

    def broken_encounter_query(encounter_id: str) -> Never:
        del encounter_id
        raise ValueError("Unknown-looking project failure.")

    app = replace(app, queries=replace(app.queries, get_encounter=broken_encounter_query))

    status, _, body = request_wsgi(app, "/encounters/missing")

    assert status == "500 Internal Server Error"
    assert "Project could not be loaded" in body


def test_unknown_routes_entities_and_methods_are_contained() -> None:
    app, _ = build_authoring_app()

    route_status, _, route_body = request_wsgi(app, "/missing")
    workspace_status, _, workspace_body = request_wsgi(app, "/archives/missing/path")
    entity_status, _, entity_body = request_wsgi(app, "/encounters/missing")
    method_status, method_headers, method_body = request_wsgi(app, "/", "DELETE")
    post_status, post_headers, post_body = request_wsgi(app, "/encounters/alpha", "POST", form={})

    assert route_status == "404 Not Found"
    assert "No authoring route matches" in route_body
    assert workspace_status == "404 Not Found"
    assert "No authoring route matches" in workspace_body
    assert entity_status == "404 Not Found"
    assert "Unknown encounter" in entity_body
    assert method_status == "405 Method Not Allowed"
    assert method_headers["Allow"] == "GET, HEAD, POST"
    assert "explicit POST forms" in method_body
    assert post_status == "405 Method Not Allowed"
    assert post_headers["Allow"] == "GET, HEAD"
    assert "explicit authoring and workspace forms" in post_body


def test_css_script_health_and_head_requests_have_expected_bodies() -> None:
    app, _ = build_authoring_app()

    css_status, css_headers, css_body = request_wsgi(app, "/assets/app.css")
    js_status, js_headers, js_body = request_wsgi(app, "/assets/app.js")
    health_status, _, health_body = request_wsgi(app, "/healthz")
    head_status, head_headers, head_body = request_wsgi(app, "/", "HEAD")

    assert css_status == "200 OK"
    assert css_headers["Content-Type"] == "text/css; charset=utf-8"
    assert ".editor-form" in css_body
    assert js_status == "200 OK"
    assert js_headers["Content-Type"] == "text/javascript; charset=utf-8"
    assert "localStorage" in js_body
    assert "requestSubmit" in js_body
    assert "Browser draft storage is unavailable" in js_body
    assert "initializeEncounterGraphs" in js_body
    assert "initializeNavigationFilter" in js_body
    assert "data-navigation-filter" in js_body
    assert "data-graph-encounter-link" in js_body
    assert "dice-recents" in js_body
    assert "data-play-dice-insert" in js_body
    assert "@media (max-width: 1180px)" in css_body
    assert ".topbar-project { display: none; }" in css_body
    assert health_status == "200 OK"
    assert health_body == "ok\n"
    assert head_status == "200 OK"
    assert int(head_headers["Content-Length"]) > 0
    assert head_body == ""


def test_structure_workspace_renders_graph_coverage_and_repair_actions() -> None:
    app, _ = build_authoring_app()

    status, _, body = request_wsgi(app, "/structure")

    assert status == "200 OK"
    assert "Structure workspace" in body
    assert 'class="encounter-graph"' in body
    assert "data-graph-viewport" in body
    assert 'data-graph-zoom="in"' in body
    assert "data-graph-reset" in body
    assert "<rect " in body
    assert "<tspan " in body
    assert 'class="graph-edge' in body
    assert ' d="M ' in body
    assert '<line class="graph-edge' not in body
    assert 'href="/encounters/alpha"' in body
    assert "Revelation coverage" in body
    assert "Minimum-cut witness: 3 / 3" in body
    assert "find-beta" in body
    assert 'href="/clues/new?revelation=find-beta"' in body
    assert 'aria-current="page"' in body


def test_encounter_creation_form_and_post_commit_new_encounter() -> None:
    app, project = build_authoring_app()

    status, _, body = request_wsgi(app, "/encounters/new")
    assert status == "200 OK"
    assert 'method="post" action="/encounters/new"' in body
    assert 'name="title"' in body
    assert 'name="start"' in body
    assert 'data-draft-key="adventure-graph:draft:' in body
    assert 'encounter:new"' in body

    status, headers, response_body = request_wsgi(
        app, "/encounters/new", "POST", form=new_encounter_form()
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/encounters/the-fifth-chamber?created=1"
    assert response_body == ""
    assert project.snapshot.adventure.encounter_index()["the-fifth-chamber"].title == (
        "The Fifth Chamber"
    )

    detail_status, _, detail_body = request_wsgi(
        app, "/encounters/the-fifth-chamber", query="created=1"
    )
    assert detail_status == "200 OK"
    assert "Encounter created" in detail_body


def test_encounter_creation_preserves_rejected_values() -> None:
    app, project = build_authoring_app()

    status, _, body = request_wsgi(
        app,
        "/encounters/new",
        "POST",
        form=new_encounter_form(title=""),
    )

    assert status == "422 Unprocessable Content"
    assert "Encounter was not created" in body
    assert "Encounter title must not be empty" in body
    assert "A newly authored place." in body
    assert 'data-server-values="true"' in body
    assert project.committed_adventure is None


def test_contextual_creation_forms_preselect_relationship_endpoints() -> None:
    app, _ = build_authoring_app()

    clue_status, _, clue_body = request_wsgi(
        app,
        "/clues/new",
        query="source=alpha&revelation=find-beta",
    )
    revelation_status, _, revelation_body = request_wsgi(
        app,
        "/revelations/new",
        query="unlocks=omega&source=alpha",
    )

    assert clue_status == revelation_status == "200 OK"
    assert 'method="post" action="/clues/new"' in clue_body
    assert '<option value="alpha" selected>' in clue_body
    assert '<option value="find-beta" selected>' in clue_body
    assert 'name="expected_revision" value="revision-1"' in clue_body
    assert 'method="post" action="/revelations/new"' in revelation_body
    assert '<option value="omega" selected>' in revelation_body
    assert 'name="source_encounter_id" value="alpha"' in revelation_body


def test_clue_creation_commits_redirects_and_updates_structural_read_model() -> None:
    app, project = build_authoring_app()

    status, headers, body = request_wsgi(app, "/clues/new", "POST", form=new_clue_form())

    assert status == "303 See Other"
    assert headers["Location"] == "/clues/another-path-to-beta?created=1"
    assert body == ""
    assert project.commit_count == 1
    clue = project.snapshot.adventure.clue_index()["another-path-to-beta"]
    assert clue.source_encounter_id == "alpha"
    assert clue.revelation_id == "find-beta"
    assert clue.discovery == "inspection"

    detail_status, _, detail_body = request_wsgi(
        app,
        "/clues/another-path-to-beta",
        query="created=1",
    )
    structure_status, _, structure_body = request_wsgi(app, "/structure")
    assert detail_status == structure_status == "200 OK"
    assert "Lead created" in detail_body
    assert "Another path to Beta" in detail_body
    assert "deficit 0" in structure_body


def test_creation_conflict_and_domain_error_preserve_submitted_values() -> None:
    app, project = build_authoring_app()
    project.snapshot = replace(project.snapshot, revision=ProjectRevision("revision-2"))

    conflict_status, _, conflict_body = request_wsgi(
        app,
        "/clues/new",
        "POST",
        form=new_clue_form(title="Unsaved & stale clue"),
    )

    assert conflict_status == "409 Conflict"
    assert project.commit_count == 0
    assert "Revision conflict" in conflict_body
    assert "Unsaved &amp; stale clue" in conflict_body
    assert 'data-server-values="true"' in conflict_body

    fresh_app, fresh_project = build_authoring_app()
    error_status, _, error_body = request_wsgi(
        fresh_app,
        "/clues/new",
        "POST",
        form=new_clue_form(source_encounter_id="missing"),
    )
    assert error_status == "422 Unprocessable Content"
    assert fresh_project.commit_count == 0
    assert "Lead was not created" in error_body
    assert "Unknown lead source" in error_body


def test_contextual_revelation_creation_chains_into_clue_creation() -> None:
    app, project = build_authoring_app()

    status, headers, body = request_wsgi(
        app,
        "/revelations/new",
        "POST",
        form=new_revelation_form(),
    )

    assert status == "303 See Other"
    assert body == ""
    assert headers["Location"] == (
        "/clues/new?source=alpha&revelation=find-the-hidden-vault&created_revelation=1"
    )
    revelation = project.snapshot.adventure.revelation_index()["find-the-hidden-vault"]
    assert revelation.unlocks_encounter_id == "omega"
    assert revelation.required

    next_status, _, next_body = request_wsgi(
        app,
        "/clues/new",
        query="source=alpha&revelation=find-the-hidden-vault&created_revelation=1",
    )
    assert next_status == "200 OK"
    assert "Revelation created" in next_body
    assert '<option value="find-the-hidden-vault" selected>' in next_body


def test_entity_pages_include_read_only_dependency_previews() -> None:
    app, _ = build_authoring_app()

    encounter_status, _, encounter_body = request_wsgi(app, "/encounters/beta")
    revelation_status, _, revelation_body = request_wsgi(app, "/revelations/find-beta")
    clue_status, _, clue_body = request_wsgi(app, "/clues/alpha-to-beta")

    assert encounter_status == revelation_status == clue_status == "200 OK"
    assert "Dependency preview" in encounter_body
    assert "Remove lead: beta points to alpha" in encounter_body
    assert "Lead: alpha points to beta" in revelation_body
    assert "Source encounter: Alpha" in clue_body
    assert "Review what this lead is connected to before moving or removing it." in clue_body


def test_create_forms_reject_untrusted_play_return_targets() -> None:
    app, project = build_authoring_app()
    form = new_encounter_form()
    form["return_to"] = "https://example.com/play"

    status, _, body = request_wsgi(app, "/encounters/new", "POST", form=form)

    assert status == "400 Bad Request"
    assert "authoring return target is invalid" in body
    assert project.commit_count == 0
