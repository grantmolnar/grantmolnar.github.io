"""Executable browser contracts for the multi-adventure catalog."""

from __future__ import annotations

from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.bootstrap import compose_workspace_web_application
from adventure_graph.infrastructure.adventure_store import save_adventure
from adventure_graph.infrastructure.local_adventure_workspace import LocalAdventureWorkspace
from adventure_graph.infrastructure.play_state_store import save_play_state
from adventure_graph.interfaces.web.styles import load_app_css
from adventure_graph.interfaces.web.workspace_app import WorkspaceWebApplication
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.web import request_wsgi

pytestmark = pytest.mark.browser


def _workspace_application(tmp_path: Path) -> WorkspaceWebApplication:
    for directory, title in (("alpha", "Alpha Adventure"), ("beta", "Beta Adventure")):
        project = tmp_path / directory
        project.mkdir()
        base = complete_four_encounter_adventure()
        adventure = base.__class__(
            id=directory,
            title=title,
            synopsis=f"Synopsis for {title}.",
            premise=base.premise,
            explanation=base.explanation,
            encounters=base.encounters,
            revelations=base.revelations,
            clues=base.clues,
            validation_policy=base.validation_policy,
        )
        save_adventure(project / "adventure.json", adventure)
        save_play_state(project / "play-state.json", new_play_state(adventure))
    workspace = LocalAdventureWorkspace(tmp_path)
    workspace.select_initial_adventure(tmp_path / "alpha" / "adventure.json")
    return compose_workspace_web_application(workspace)


def _workspace_html(tmp_path: Path, path: str) -> str:
    status, _, body = request_wsgi(_workspace_application(tmp_path), path)
    assert status == "200 OK"
    return body.replace(
        '<script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css">',
        f"<style>{load_app_css()}</style>",
    )


def _catalog_html(tmp_path: Path) -> str:
    return _workspace_html(tmp_path, "/adventures")


def _empty_workspace_html(tmp_path: Path) -> str:
    application = compose_workspace_web_application(LocalAdventureWorkspace(tmp_path))
    status, _, body = request_wsgi(application, "/adventures")
    assert status == "200 OK"
    return body.replace(
        '<script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css">',
        f"<style>{load_app_css()}</style>",
    )


@pytest.mark.parametrize("width", [1648, 900, 720, 390])
def test_catalog_filters_remain_inside_the_bounded_content_column(
    tmp_path: Path,
    page: Page,
    width: int,
) -> None:
    page.set_viewport_size({"width": width, "height": 900})
    page.set_content(_catalog_html(tmp_path))

    filters = page.locator(".catalog-filters")
    expect(filters).to_be_visible()
    filter_box = filters.bounding_box()
    assert filter_box is not None

    for control in filters.locator("input, select, button").all():
        control_box = control.bounding_box()
        assert control_box is not None
        assert control_box["x"] >= filter_box["x"] - 1
        assert control_box["x"] + control_box["width"] <= (
            filter_box["x"] + filter_box["width"] + 1
        )

    assert page.evaluate("document.documentElement.scrollWidth") == page.evaluate(
        "document.documentElement.clientWidth"
    )


@pytest.mark.parametrize("width", [900, 390])
def test_empty_catalog_sample_actions_remain_visible_and_bounded(
    tmp_path: Path,
    page: Page,
    width: int,
) -> None:
    page.set_viewport_size({"width": width, "height": 900})
    page.set_content(_empty_workspace_html(tmp_path))

    sample_form = page.locator('form[action="/adventures/sample"]')
    expect(sample_form).to_be_visible()
    expect(sample_form.locator('button[type="submit"]')).to_have_text("Add The Glass Saint sample")
    blank_adventure = page.locator(
        'a[href="/adventures/new"]',
        has_text="Create blank adventure",
    )
    expect(blank_adventure).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth") == page.evaluate(
        "document.documentElement.clientWidth"
    )


def test_catalog_exposes_distinct_adventure_and_playthrough_imports(
    tmp_path: Path,
    page: Page,
) -> None:
    page.set_content(_catalog_html(tmp_path))

    adventure_import = page.locator('a[href="/adventures/import"]')
    playthrough_import = page.locator('a[href="/adventures/playthroughs/import"]')
    expect(adventure_import).to_have_text("Import adventure")
    expect(playthrough_import).to_have_text("Import playthrough")
    expect(adventure_import).to_be_visible()
    expect(playthrough_import).to_be_visible()


@pytest.mark.parametrize(
    ("path", "width"),
    [
        ("/adventures/import", 900),
        ("/adventures/import", 390),
        ("/adventures/playthroughs/import", 900),
        ("/adventures/playthroughs/import", 390),
    ],
)
def test_transfer_import_forms_remain_bounded_and_have_one_clear_action(
    tmp_path: Path,
    page: Page,
    path: str,
    width: int,
) -> None:
    page.set_viewport_size({"width": width, "height": 900})
    page.set_content(_workspace_html(tmp_path, path))

    form = page.locator("form.transfer-import-form")
    expect(form).to_be_visible()
    expect(form.locator('input[type="file"]')).to_be_visible()
    expect(form.locator('button[type="submit"]')).to_have_count(1)
    expect(form.locator("small")).to_contain_text("up to 8 MiB")

    form_box = form.bounding_box()
    assert form_box is not None
    assert form_box["x"] >= -1
    assert form_box["x"] + form_box["width"] <= width + 1
    assert page.evaluate("document.documentElement.scrollWidth") == page.evaluate(
        "document.documentElement.clientWidth"
    )


@pytest.mark.parametrize("width", [900, 390])
def test_selected_adventure_import_form_remains_bounded(
    tmp_path: Path,
    page: Page,
    width: int,
) -> None:
    page.set_viewport_size({"width": width, "height": 900})
    page.set_content(_workspace_html(tmp_path, "/archives"))

    form = page.locator("form.archive-import-form")
    expect(form).to_be_visible()
    expect(form.locator('input[type="file"]')).to_be_visible()
    expect(form.locator('button[type="submit"]')).to_have_count(1)
    expect(form.locator("small")).to_contain_text("up to 8 MiB")

    form_box = form.bounding_box()
    assert form_box is not None
    assert form_box["x"] >= -1
    assert form_box["x"] + form_box["width"] <= width + 1
    assert page.evaluate("document.documentElement.scrollWidth") == page.evaluate(
        "document.documentElement.clientWidth"
    )
