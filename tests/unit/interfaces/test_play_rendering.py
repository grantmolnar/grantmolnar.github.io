"""Focused tests for Play-mode presentation behavior."""

from dataclasses import replace

from adventure_graph.application.play_tracking import (
    end_session,
    new_play_state,
    record_visit,
    start_session,
)
from adventure_graph.application.run_workspace import GetRunDashboard
from adventure_graph.interfaces.web.play_rendering import render_play
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.projects import read_only_play_project


def test_route_groups_do_not_merge_distinct_sessions_with_the_same_title() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Night Watch")
    state = record_visit(adventure, state, "alpha")
    state = end_session(state)
    state = start_session(state, title="Night Watch")
    state = record_visit(adventure, state, "alpha")
    project = read_only_play_project(state, adventure, revision="same-title-sessions")

    page = render_play(
        GetRunDashboard(project).execute(),
        "memory://adventure.json",
        csrf_token="known-token",
    )

    assert page.count('<section class="play-route-group">') == 2
    assert page.count("<h3>Night Watch</h3>") == 2


def test_current_visit_uses_six_page_scrolling_disclosure_sections() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Table night")
    state = record_visit(adventure, state, "alpha")
    project = read_only_play_project(state, adventure, revision="section-stack-workspace")

    page = render_play(
        GetRunDashboard(project).execute(),
        "memory://adventure.json",
        csrf_token="known-token",
    )

    assert page.count('class="play-encounter-section ') == 6
    assert page.count('data-disclosure-default="expanded"') >= 6
    assert page.count("data-play-encounter-section-scroll=") == 6
    headings = (
        "Opening description",
        "GM orientation",
        "Encounter material",
        "Linked references",
        "Leads at this encounter",
        "Encounter notes",
    )
    positions = [page.index(heading) for heading in headings]
    assert positions == sorted(positions)
    assert "data-play-reading-divider" not in page
    assert "data-play-panel-toggle" not in page
    assert page.count('role="region"') == 6
    assert page.count('tabindex="0"') == 6
    for key in ("opening", "orientation", "material", "references", "clues", "notes"):
        toggle_id = f"play-encounter-section-{key}-toggle"
        content_id = f"play-encounter-section-{key}-content"
        assert f'id="{toggle_id}"' in page
        assert f'aria-controls="{content_id}"' in page
        assert f'id="{content_id}"' in page
        assert f'aria-labelledby="{toggle_id}"' in page


def test_browsed_encounter_keeps_the_notes_section_without_inventing_a_visit() -> None:
    adventure = complete_four_encounter_adventure()
    project = read_only_play_project(
        new_play_state(adventure),
        adventure,
        revision="browse-only-section-stack",
    )

    page = render_play(
        GetRunDashboard(project).execute(),
        "memory://adventure.json",
        csrf_token="known-token",
    )

    assert page.count('class="play-encounter-section ') == 6
    assert "Encounter notes are visit-specific." in page
    assert "data-play-notebook" not in page
    assert 'action="/play/note"' not in page


def test_visit_notes_use_one_flexible_encounter_notebook() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(new_play_state(adventure), title="Table night")
    state = record_visit(adventure, state, "alpha")
    project = read_only_play_project(state, adventure, revision="note-modes")

    page = render_play(
        GetRunDashboard(project).execute(),
        "memory://adventure.json",
        csrf_token="known-token",
    )

    assert 'data-play-notebook data-play-visit-number="1"' in page
    assert (
        'class="play-notebook-status" role="status" aria-live="polite" aria-atomic="true"' in page
    )
    assert 'action="/play/note"' in page
    assert "Save note only" in page
    assert "changed circumstances, or likely consequences" in page
    assert "data-play-note-mode" not in page
    assert 'action="/play/consequence"' not in page
    assert "Earlier persistent notes" not in page


def test_title_only_adventure_renders_a_play_empty_state() -> None:
    adventure = replace(
        complete_four_encounter_adventure(),
        encounters=(),
        revelations=(),
        clues=(),
        references=(),
    )
    project = read_only_play_project(
        new_play_state(adventure),
        adventure,
        revision="empty-play-workspace",
    )

    page = render_play(
        GetRunDashboard(project).execute(),
        "memory://adventure.json",
        csrf_token="known-token",
    )

    assert "This adventure has no encounters yet." in page
    assert "Add an encounter before beginning play." in page
    assert 'href="/encounters/new?return_to=%2Fplay"' in page
    assert "data-play-focused-encounter-id" not in page
