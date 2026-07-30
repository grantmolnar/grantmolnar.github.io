"""Integration tests for the multi-adventure browser workspace."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from shutil import rmtree
from uuid import UUID

import pytest

from adventure_graph import __version__
from adventure_graph.application.play_tracking import new_play_state, record_visit, start_session
from adventure_graph.bootstrap import compose_workspace_web_application
from adventure_graph.domain.adventure import AdventureTags
from adventure_graph.domain.validation_models import ValidationPolicy
from adventure_graph.infrastructure.adventure_store import (
    load_adventure,
    save_adventure,
)
from adventure_graph.infrastructure.local_adventure_workspace import (
    LocalAdventureWorkspace,
)
from adventure_graph.infrastructure.play_state_store import (
    load_play_state,
    save_play_state,
)
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.paths import PROJECT_ROOT
from tests.support.web import rendered_post_forms, request_wsgi


def _write_project(root: Path, directory: str, title: str) -> None:
    project = root / directory
    project.mkdir()
    adventure = complete_four_encounter_adventure()
    adventure = adventure.__class__(
        id=directory,
        title=title,
        synopsis=f"Synopsis for {title}.",
        premise=adventure.premise,
        explanation=adventure.explanation,
        encounters=adventure.encounters,
        revelations=adventure.revelations,
        clues=adventure.clues,
        validation_policy=adventure.validation_policy,
    )
    save_adventure(project / "adventure.json", adventure)
    save_play_state(project / "play-state.json", new_play_state(adventure))


def test_workspace_construction_does_not_persist_selection(tmp_path: Path) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    _write_project(tmp_path, "beta", "Beta Adventure")
    settings_path = tmp_path / ".adventure-graph" / "settings.json"

    workspace = LocalAdventureWorkspace(tmp_path)

    assert not settings_path.exists()
    workspace.select_initial_adventure(tmp_path / "beta" / "adventure.json")
    assert settings_path.is_file()
    assert workspace.load().settings.selected_adventure_key == "beta/adventure.json"


def test_workspace_without_prior_selection_opens_one_project_but_not_an_arbitrary_many(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, "beta", "Beta Adventure")
    single = LocalAdventureWorkspace(tmp_path).load()
    assert single.settings.selected_adventure_key == "beta/adventure.json"

    _write_project(tmp_path, "alpha", "Alpha Adventure")
    multiple_workspace = LocalAdventureWorkspace(tmp_path)
    multiple = multiple_workspace.load()
    assert multiple.settings.selected_adventure_key is None
    assert multiple.selected_adventure is None

    status, headers, _ = request_wsgi(
        compose_workspace_web_application(multiple_workspace),
        "/",
    )
    assert status == "303 See Other"
    assert headers["Location"] == "/adventures"


def test_workspace_with_a_malformed_project_opens_the_catalog_before_auto_selection(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    malformed = tmp_path / "damaged"
    malformed.mkdir()
    (malformed / "adventure.json").write_text("{not-json", encoding="utf-8")
    workspace = LocalAdventureWorkspace(tmp_path)

    snapshot = workspace.load()

    assert snapshot.settings.selected_adventure_key is None
    assert snapshot.selected_adventure is None
    assert tuple(entry.key for entry in snapshot.adventures) == ("alpha/adventure.json",)
    assert tuple(item.key for item in snapshot.diagnostics) == ("damaged/adventure.json",)

    status, headers, _ = request_wsgi(compose_workspace_web_application(workspace), "/")
    assert status == "303 See Other"
    assert headers["Location"] == "/adventures"


def test_workspace_does_not_silently_substitute_for_an_unavailable_selection(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    _write_project(tmp_path, "beta", "Beta Adventure")
    workspace = LocalAdventureWorkspace(tmp_path)
    workspace.select_initial_adventure(tmp_path / "beta" / "adventure.json")
    rmtree(tmp_path / "beta")

    snapshot = workspace.load()

    assert snapshot.settings.selected_adventure_key == "beta/adventure.json"
    assert snapshot.selected_adventure is None
    assert tuple(entry.key for entry in snapshot.adventures) == ("alpha/adventure.json",)

    app = compose_workspace_web_application(workspace)
    status, headers, _ = request_wsgi(app, "/")
    assert status == "303 See Other"
    assert headers["Location"] == "/adventures"

    status, _, body = request_wsgi(app, "/adventures")
    assert status == "200 OK"
    assert "Previously selected adventure unavailable" in body
    assert "did not substitute another project" in body
    assert "Current adventure" not in body


def test_workspace_creation_avoids_existing_nonproject_directory_case_collisions(
    tmp_path: Path,
) -> None:
    (tmp_path / "The-Ember-Road").mkdir()
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)
    snapshot = workspace.load()

    status, _, _ = request_wsgi(
        app,
        "/adventures/new",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": snapshot.revision.value,
            "title": "The Ember Road",
            "synopsis": "",
            "premise": "",
            "explanation": "",
            "opening_title": "",
            "opening_summary": "",
            "opening_view": "",
        },
    )

    assert status == "303 See Other"
    assert (tmp_path / "the-ember-road-2" / "adventure.json").is_file()
    assert workspace.load().settings.selected_adventure_key == ("the-ember-road-2/adventure.json")


def test_workspace_revision_changes_when_a_visible_name_is_reserved(
    tmp_path: Path,
) -> None:
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)
    stale_snapshot = workspace.load()
    (tmp_path / "reserved-after-render").mkdir()

    status, _, body = request_wsgi(
        app,
        "/adventures/new",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": stale_snapshot.revision.value,
            "title": "Another Adventure",
            "synopsis": "",
            "premise": "",
            "explanation": "",
            "opening_title": "",
            "opening_summary": "",
            "opening_view": "",
        },
    )

    assert status == "409 Conflict"
    assert "Workspace changed" in body
    assert not (tmp_path / "another-adventure").exists()


def test_workspace_catalog_switches_and_delegates_to_selected_adventure(tmp_path: Path) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    _write_project(tmp_path, "beta", "Beta Adventure")
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)
    snapshot = workspace.load()

    status, _, body = request_wsgi(app, "/adventures")
    assert status == "200 OK"
    assert "Alpha Adventure" in body
    assert "Beta Adventure" in body
    assert "Open adventure" in body
    assert "Import adventure" in body
    assert "Import playthrough" in body
    assert "Export adventure" in body
    assert "Playthroughs" in body
    assert "Encounters" in body
    assert "Revelations" in body
    assert "Leads" in body

    status, headers, _ = request_wsgi(
        app,
        "/adventures/select",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": snapshot.revision.value,
            "adventure_key": "beta/adventure.json",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == "/"

    status, _, body = request_wsgi(app, "/")
    assert status == "200 OK"
    assert "Beta Adventure" in body
    assert "Adventures" in body
    assert "Settings" in body


def test_workspace_catalog_opens_playthroughs_for_the_chosen_adventure(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    _write_project(tmp_path, "beta", "Beta Adventure")
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)
    snapshot = workspace.load()

    status, headers, _ = request_wsgi(
        app,
        "/adventures/playthroughs",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": snapshot.revision.value,
            "adventure_key": "beta/adventure.json",
        },
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/archives"
    assert workspace.load().settings.selected_adventure_key == "beta/adventure.json"

    status, _, body = request_wsgi(app, "/archives")
    assert status == "200 OK"
    assert "Beta Adventure" in body
    assert "Import for this adventure" in body
    assert "Current playthrough" in body


def test_delegated_head_uses_selected_adventure_response_semantics(tmp_path: Path) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    app = compose_workspace_web_application(LocalAdventureWorkspace(tmp_path))

    get_status, get_headers, get_body = request_wsgi(app, "/")
    head_status, head_headers, head_body = request_wsgi(app, "/", method="HEAD")

    assert head_status == get_status == "200 OK"
    assert head_headers == get_headers
    assert int(head_headers["Content-Length"]) == len(get_body.encode("utf-8"))
    assert head_body == ""
    assert head_headers["X-Frame-Options"] == "DENY"


def test_workspace_catalog_renders_and_filters_structured_adventure_tags(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    path = tmp_path / "alpha" / "adventure.json"
    adventure = load_adventure(path)
    save_adventure(
        path,
        replace(
            adventure,
            tags=AdventureTags(
                genres=("Investigation",),
                game_systems=("System-agnostic",),
                settings=("Original fantasy",),
                party_size_min=3,
                party_size_max=5,
                combat_intensity="light",
                keywords=("Museum",),
            ),
        ),
    )
    app = compose_workspace_web_application(LocalAdventureWorkspace(tmp_path))

    status, _, body = request_wsgi(app, "/adventures")

    assert status == "200 OK"
    assert "data-adventure-filter-genre" in body
    assert "data-adventure-filter-system" in body
    assert "data-adventure-filter-party" in body
    assert "data-adventure-filter-level" in body
    assert "data-adventure-filter-combat" in body
    assert 'data-genres="investigation"' in body
    assert 'data-party-min="3"' in body
    assert 'data-party-max="5"' in body
    assert "Light combat" in body
    assert "Museum" in body


def test_workspace_discovery_is_root_or_visible_direct_child_only(tmp_path: Path) -> None:
    root_adventure = complete_four_encounter_adventure()
    save_adventure(tmp_path / "adventure.json", root_adventure)
    _write_project(tmp_path, "alpha", "Alpha Adventure")

    nested = tmp_path / "collection"
    nested.mkdir()
    _write_project(nested, "nested", "Nested Adventure")
    save_adventure(tmp_path / "standalone.adventure.json", root_adventure)
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    save_adventure(hidden / "adventure.json", root_adventure)

    snapshot = LocalAdventureWorkspace(tmp_path).load()

    assert {entry.key for entry in snapshot.adventures} == {
        "adventure.json",
        "alpha/adventure.json",
    }


def test_examples_directory_exposes_bundled_drafted_roster() -> None:
    snapshot = LocalAdventureWorkspace(PROJECT_ROOT / "examples").load()

    assert {entry.title for entry in snapshot.adventures} == {
        "A Wedding for the River",
        "The Bell Beneath Harrowgate",
        "The Cauldron of Nine Silences",
        "The Concord of Aurelune",
        "The Forest That Carries Dawn",
        "The Glass Saint",
        "The Last Bell of Bramblewick",
        "The Mandate of Seven Reeds",
        "The March on Vossgard",
        "The Princess on the Salt Road",
        "The Siege of the Stone Lung",
        "The Witch of Blackbriar Hall",
        "When the Swine Kneel",
    }


def test_workspace_catalog_reports_malformed_canonical_projects(tmp_path: Path) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    broken = tmp_path / "broken"
    broken.mkdir()
    (broken / "adventure.json").write_text("{not json", encoding="utf-8")
    workspace = LocalAdventureWorkspace(tmp_path)

    snapshot = workspace.load()
    assert len(snapshot.diagnostics) == 1
    assert snapshot.diagnostics[0].key == "broken/adventure.json"
    assert "valid JSON" in snapshot.diagnostics[0].message

    status, _, body = request_wsgi(compose_workspace_web_application(workspace), "/adventures")
    assert status == "200 OK"
    assert "Some adventure projects need attention" in body
    assert "broken/adventure.json" in body
    assert "Repair or remove" in body


def test_explicit_malformed_or_standalone_selection_fails_actionably(tmp_path: Path) -> None:
    malformed = tmp_path / "broken"
    malformed.mkdir()
    malformed_source = malformed / "adventure.json"
    malformed_source.write_text("{not json", encoding="utf-8")

    with pytest.raises(ValueError, match=r"Cannot open selected adventure broken/adventure\.json"):
        LocalAdventureWorkspace(tmp_path).select_initial_adventure(malformed_source)

    standalone = tmp_path / "standalone.adventure.json"
    save_adventure(standalone, complete_four_encounter_adventure())
    with pytest.raises(ValueError, match="not a canonical workspace adventure"):
        LocalAdventureWorkspace(tmp_path).select_initial_adventure(standalone)


def test_workspace_creates_project_with_defaults_and_canonical_files(tmp_path: Path) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)
    snapshot = workspace.load()
    defaults = ValidationPolicy(
        minimum_clues_per_revelation=4,
        minimum_source_encounters_per_revelation=2,
        minimum_incoming_clues_per_encounter=2,
        minimum_incoming_source_encounters_per_encounter=2,
        minimum_outgoing_clues_per_encounter=1,
        minimum_distinct_encounter_targets_per_encounter=1,
        minimum_edge_connectivity=1,
        require_directed_reachability=False,
    )

    status, _, _ = request_wsgi(
        app,
        "/settings/defaults",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": snapshot.revision.value,
            "minimum_clues_per_revelation": "4",
            "minimum_source_encounters_per_revelation": "2",
            "minimum_incoming_clues_per_encounter": "2",
            "minimum_incoming_source_encounters_per_encounter": "2",
            "minimum_outgoing_clues_per_encounter": "1",
            "minimum_distinct_encounter_targets_per_encounter": "1",
            "minimum_edge_connectivity": "1",
        },
    )
    assert status == "303 See Other"
    snapshot = workspace.load()

    status, headers, _ = request_wsgi(
        app,
        "/adventures/new",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": snapshot.revision.value,
            "title": "The Ember Road",
            "synopsis": "A road under threat.",
            "premise": "Carry the ember home.",
            "explanation": "The road itself is awake.",
            "opening_title": "The Broken Milepost",
            "opening_summary": "The road forks where it should not.",
            "opening_view": "Ash falls from a clear sky.",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == "/adventures?created=1"

    adventure_path = tmp_path / "the-ember-road" / "adventure.json"
    state_path = tmp_path / "the-ember-road" / "play-state.json"
    assert adventure_path.is_file()
    assert state_path.is_file()
    assert (tmp_path / "the-ember-road" / "generated").is_dir()
    assert (tmp_path / "the-ember-road" / "archives").is_dir()
    adventure = load_adventure(adventure_path)
    assert UUID(adventure.id).version == 4
    assert adventure.validation_policy == defaults
    assert adventure.encounters[0].start
    assert load_play_state(state_path).adventure_id == adventure.id
    assert workspace.load().settings.selected_adventure_key == "the-ember-road/adventure.json"


def test_workspace_can_create_an_almost_blank_adventure(tmp_path: Path) -> None:
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)
    snapshot = workspace.load()

    status, _, body = request_wsgi(app, "/adventures/new")
    assert status == "200 OK"
    assert "Name the adventure, then add as much or as little detail as you need." in body
    assert "Only the adventure title is required" not in body
    assert "Empty prose and an omitted opening encounter" not in body
    assert "Create adventure <span>Ctrl/⌘ S</span>" not in body
    assert "Opening encounter (optional)" in body
    opening_title_control = body.split('name="opening_title"', maxsplit=1)[1].split(
        ">", maxsplit=1
    )[0]
    opening_summary_control = body.split('name="opening_summary"', maxsplit=1)[1].split(
        ">", maxsplit=1
    )[0]
    assert "required" not in opening_title_control
    assert "required" not in opening_summary_control

    status, headers, _ = request_wsgi(
        app,
        "/adventures/new",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": snapshot.revision.value,
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
    adventure_path = tmp_path / "the-unwritten-door" / "adventure.json"
    state_path = tmp_path / "the-unwritten-door" / "play-state.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    assert adventure.title == "The Unwritten Door"
    assert adventure.synopsis == ""
    assert adventure.premise == ""
    assert adventure.explanation == ""
    assert adventure.encounters == ()
    assert adventure.revelations == ()
    assert adventure.clues == ()
    assert state.adventure_id == adventure.id
    assert state.events == ()

    selected_key = workspace.load().settings.selected_adventure_key
    assert selected_key == "the-unwritten-door/adventure.json"
    selected_app = app.adventure_application(selected_key, app.csrf_token)
    revision = selected_app.queries.get_structure().revision.value
    status, _, create_body = request_wsgi(app, "/encounters/new")
    assert status == "200 OK"
    assert "Add an encounter" in create_body
    assert 'name="start" value="1" data-draft-field checked' in create_body

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
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == "/encounters/the-first-room?created=1"
    reloaded = load_adventure(adventure_path)
    assert tuple(item.id for item in reloaded.encounters) == ("the-first-room",)
    assert reloaded.encounters[0].start


def test_settings_page_updates_selected_adventure_without_rewriting_defaults(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)

    status, _, body = request_wsgi(app, "/settings")
    assert status == "200 OK"
    assert "Defaults for new adventures" in body
    assert "Alpha Adventure validator policy" in body

    adventure_path = tmp_path / "alpha" / "adventure.json"
    adventure_revision = (
        app.adventure_application("alpha/adventure.json", app.csrf_token)
        .queries.get_overview()
        .revision.value
    )
    status, headers, _ = request_wsgi(
        app,
        "/settings/adventure",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": adventure_revision,
            "minimum_clues_per_revelation": "2",
            "minimum_source_encounters_per_revelation": "2",
            "minimum_incoming_clues_per_encounter": "2",
            "minimum_incoming_source_encounters_per_encounter": "2",
            "minimum_outgoing_clues_per_encounter": "2",
            "minimum_distinct_encounter_targets_per_encounter": "2",
            "minimum_edge_connectivity": "2",
            "require_directed_reachability": "1",
        },
    )
    assert status == "303 See Other"
    assert headers["Location"] == "/settings?saved=adventure"
    assert load_adventure(adventure_path).validation_policy.minimum_clues_per_revelation == 2
    assert workspace.load().settings.validator_defaults == ValidationPolicy()


def test_help_page_is_available_without_a_selected_adventure(tmp_path: Path) -> None:
    app = compose_workspace_web_application(LocalAdventureWorkspace(tmp_path))

    status, headers, body = request_wsgi(app, "/help")
    head_status, head_headers, head_body = request_wsgi(app, "/help", method="HEAD")

    assert status == head_status == "200 OK"
    assert headers == head_headers
    assert head_body == ""
    assert "Prepare situations, not a fixed plot" in body
    assert "Encounters connected by information" in body
    assert "Build the possibilities" in body
    assert "Follow the table" in body
    assert "Beta feedback" in body
    assert f"Adventure Graph <code>{__version__}</code>" in body
    assert "private table notes" in body
    assert "not affiliated with, sponsored by, or endorsed by Justin Alexander" in body
    assert (
        'href="https://thealexandrian.net/wordpress/7949/roleplaying-games/'
        'node-based-scenario-design-part-1-the-plotted-approach"'
    ) in body
    assert 'href="https://thealexandrian.net/so-you-want-to-be-a-game-master"' in body
    assert body.count('target="_blank" rel="noopener noreferrer"') == 2
    assert '<a href="/help" aria-current="page">Help</a>' in body


def test_help_is_reachable_from_workspace_author_and_play_chrome(tmp_path: Path) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    app = compose_workspace_web_application(LocalAdventureWorkspace(tmp_path))

    for path in ("/adventures", "/", "/play"):
        status, _, body = request_wsgi(app, path)
        assert status == "200 OK", path
        assert '<a href="/help">Help</a>' in body, path


def test_workspace_shell_shares_appearance_and_new_adventure_draft_contract(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)

    _, _, catalog = request_wsgi(app, "/adventures")
    _, _, create = request_wsgi(app, "/adventures/new")

    assert "data-theme-toggle" in catalog
    assert '<meta name="color-scheme" content="light dark">' in catalog
    assert "data-authoring-form" in create
    assert 'data-draft-key="workspace:new-adventure"' in create
    assert 'id="opening_view" name="opening_view"' in create
    assert "Discard browser draft" in create


def test_created_adventure_catalog_clears_the_workspace_creation_draft(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)

    _, _, body = request_wsgi(app, "/adventures", query="created=1")

    assert 'data-clear-draft-key="workspace:new-adventure"' in body


def test_play_session_exports_latest_session_narrative_and_safe_recap(tmp_path: Path) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    workspace = LocalAdventureWorkspace(tmp_path)
    app = compose_workspace_web_application(workspace)
    delegate = app.adventure_application("alpha/adventure.json", app.csrf_token)

    def revision() -> str:
        assert delegate.play is not None
        return delegate.play.queries.get_run().revision.value

    status, _, _ = request_wsgi(
        app,
        "/play/session/start",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": revision(),
            "focus_encounter_id": "",
            "title": "The road east",
            "played_on": "2026-07-15",
            "participants": "Mara, Sera",
            "attendance_note": "",
            "opening_note": "The party resumed beneath the eastern gate.",
        },
    )
    assert status == "303 See Other"

    status, _, _ = request_wsgi(
        app,
        "/play/enter",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": revision(),
            "focus_encounter_id": "alpha",
            "encounter_id": "alpha",
            "party_label": "Main party",
        },
    )
    assert status == "303 See Other"

    status, _, _ = request_wsgi(
        app,
        "/play/transition",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": revision(),
            "focus_encounter_id": "alpha",
            "source_visit_number": "1",
            "note": "The party questioned the watch captain.",
            "spotted_clue_id": "alpha-to-beta",
            "missed_clue_id": "alpha-to-gamma",
            "established_revelation_id": "find-beta",
            "consequence": "The watch now trusts the party.",
            "destination_encounter_id": "beta",
            "party_label": "Scouting pair",
        },
    )
    assert status == "303 See Other"

    status, _, _ = request_wsgi(
        app,
        "/play/session/end",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": revision(),
            "focus_encounter_id": "beta",
            "closing_note": "The party camped beneath the eastern wall.",
        },
    )
    assert status == "303 See Other"

    status, headers, narrative = request_wsgi(
        app,
        "/play/ledgers/download",
        query="kind=narrative&scope=session",
    )
    assert status == "200 OK"
    assert headers["Content-Type"] == "text/markdown; charset=utf-8"
    assert headers["Content-Disposition"] == 'attachment; filename="session-01-narrative.md"'
    assert "The road east" in narrative
    assert "The party questioned the watch captain." in narrative
    assert "The watch now trusts the party." in narrative
    assert "The party camped beneath the eastern wall." in narrative

    status, _, recap = request_wsgi(
        app,
        "/play/ledgers/download",
        query="kind=recap&scope=session",
    )
    assert status == "200 OK"
    assert "Alpha" in recap
    assert "alpha points to beta" in recap
    assert "Find Beta" in recap
    assert "The watch now trusts the party." not in recap
    assert "alpha points to gamma" not in recap


def test_every_rendered_post_form_carries_the_shared_workspace_csrf_token(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    _write_project(tmp_path, "beta", "Beta Adventure")
    adventure_path = tmp_path / "alpha" / "adventure.json"
    adventure = load_adventure(adventure_path)
    save_play_state(
        tmp_path / "alpha" / "play-state.json",
        record_visit(
            adventure,
            start_session(new_play_state(adventure), title="Session one"),
            "alpha",
        ),
    )
    workspace = LocalAdventureWorkspace(tmp_path)
    workspace.select_initial_adventure(adventure_path)
    app = compose_workspace_web_application(workspace)
    pages = (
        "/adventures",
        "/adventures/new",
        "/adventures/playthroughs/import",
        "/settings",
        "/help",
        "/adventure/edit",
        "/encounters/alpha/edit",
        "/clues/new",
        "/clues/alpha-to-beta/edit",
        "/revelations/new",
        "/revelations/find-beta/edit",
        "/play",
        "/run",
        "/journal",
        "/reports",
        "/archives",
    )
    actions: set[str] = set()

    for page in pages:
        status, _, body = request_wsgi(app, page)
        assert status == "200 OK", page
        for form in rendered_post_forms(body):
            actions.add(form.action)
            assert form.csrf_tokens == (app.csrf_token,), (page, form)

    assert {
        "/adventures/select",
        "/adventures/playthroughs",
        "/adventures/new",
        "/adventures/playthroughs/import",
        "/settings/defaults",
        "/settings/adventure",
        "/adventure/edit",
        "/encounters/alpha/edit",
        "/clues/new",
        "/clues/alpha-to-beta/edit",
        "/revelations/new",
        "/revelations/find-beta/edit",
        "/play/session/end",
        "/play/note",
        "/play/dice/roll",
        "/run/visit",
        "/run/note",
        "/run/correct",
        "/journal/correct",
        "/reports/generate",
        "/archives/create",
    } <= actions


def test_workspace_report_archive_and_journal_mutations_reject_wrong_csrf_before_writes(
    tmp_path: Path,
) -> None:
    _write_project(tmp_path, "alpha", "Alpha Adventure")
    _write_project(tmp_path, "beta", "Beta Adventure")
    adventure_path = tmp_path / "alpha" / "adventure.json"
    adventure = load_adventure(adventure_path)
    save_play_state(
        tmp_path / "alpha" / "play-state.json",
        record_visit(adventure, new_play_state(adventure), "alpha"),
    )
    local_workspace = LocalAdventureWorkspace(tmp_path)
    local_workspace.select_initial_adventure(adventure_path)
    app = compose_workspace_web_application(local_workspace)
    workspace = app.queries.get_workspace()
    selected = workspace.selected_adventure
    assert selected is not None
    delegate = app.adventure_application(selected.key, app.csrf_token)
    revision = delegate.queries.get_overview().revision.value
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    requests = (
        (
            "/adventures/select",
            {
                "csrf_token": "wrong-token",
                "expected_revision": workspace.revision.value,
                "adventure_key": "beta/adventure.json",
            },
        ),
        (
            "/reports/generate",
            {
                "csrf_token": "wrong-token",
                "expected_revision": revision,
            },
        ),
        (
            "/archives/create",
            {
                "csrf_token": "wrong-token",
                "expected_revision": revision,
                "label": "Must not be archived",
                "name": "must-not-exist",
            },
        ),
        (
            "/journal/correct",
            {
                "csrf_token": "wrong-token",
                "expected_revision": revision,
                "reason": "Must not void the visit.",
            },
        ),
    )

    for path, form in requests:
        status, _, body = request_wsgi(app, path, "POST", form=form)
        assert status == "403 Forbidden", path
        assert "Form token rejected" in body

    after = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before
