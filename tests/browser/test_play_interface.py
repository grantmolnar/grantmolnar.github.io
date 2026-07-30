"""Executable browser contracts for the table-centered Play interface."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from adventure_graph.application.play_tracking import new_play_state, record_visit, start_session
from adventure_graph.infrastructure.adventure_store import load_adventure, save_adventure
from adventure_graph.infrastructure.play_state_store import save_play_state
from adventure_graph.interfaces.web.server import LoopbackWebServer, start_web_app
from tests.support.adventures import reference_library_adventure
from tests.support.local_web import build_local_play_app

pytestmark = pytest.mark.browser


@pytest.fixture
def play_server(tmp_path: Path) -> Iterator[tuple[LoopbackWebServer, Path, Path]]:
    """Serve one real filesystem-backed Play workspace on an ephemeral loopback port."""
    adventure = reference_library_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    state = start_session(
        new_play_state(adventure),
        title="Browser regression session",
        participants=("GM",),
    )
    state = record_visit(adventure, state, "alpha")
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, state)
    server = start_web_app(build_local_play_app(adventure_path, state_path))
    try:
        yield server, adventure_path, state_path
    finally:
        server.shutdown()


def _play_url(server: LoopbackWebServer) -> str:
    return f"{server.url}play?encounter=alpha"


def test_six_encounter_sections_toggle_visible_content_and_persist_preferences(
    play_server: tuple[LoopbackWebServer, Path, Path],
    page: Page,
) -> None:
    server, _, _ = play_server
    page.goto(_play_url(server))

    sections = page.locator("[data-play-encounter-sections] > [data-ui-disclosure]")
    expect(sections).to_have_count(6)
    assert sections.locator("[data-ui-disclosure-toggle][aria-expanded='true']").count() == 6
    assert sections.locator("[data-ui-disclosure-content]:visible").count() == 6

    opening = page.locator("#encounter-opening")
    toggle = opening.locator("[data-ui-disclosure-toggle]")
    content = opening.locator("[data-ui-disclosure-content]")
    toggle.click()

    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(content).to_be_hidden()
    page.reload()
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(content).to_be_hidden()

    toggle.click()
    page.reload()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(content).to_be_visible()


def test_notebook_draft_survives_reload_without_entering_play_history(
    play_server: tuple[LoopbackWebServer, Path, Path],
    page: Page,
) -> None:
    server, _, state_path = play_server
    original_journal = state_path.read_bytes()
    page.goto(_play_url(server))

    notebook = page.locator("[data-play-notebook]")
    status = page.locator("[data-play-notebook-status]")
    notebook.fill("The steward promised access after moonrise.")

    expect(status).to_have_text("Draft kept in this browser")
    assert state_path.read_bytes() == original_journal

    page.reload()
    expect(notebook).to_have_value("The steward promised access after moonrise.")
    expect(status).to_have_text("Draft kept in this browser")
    assert state_path.read_bytes() == original_journal


def test_mobile_drawer_hides_inert_content_and_restores_trigger_focus(
    play_server: tuple[LoopbackWebServer, Path, Path],
    page: Page,
) -> None:
    server, _, _ = play_server
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(_play_url(server))

    toggle = page.locator('[data-play-drawer-toggle="route"]')
    drawer = page.locator('[data-play-drawer="route"]')
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(drawer).to_have_attribute("aria-hidden", "true")
    assert drawer.evaluate("element => element.inert") is True

    toggle.click()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(drawer).to_have_attribute("aria-hidden", "false")
    assert drawer.evaluate("element => element.inert") is False
    page.wait_for_function(
        "document.activeElement && "
        "document.activeElement.closest('[data-play-drawer=\"route\"]') !== null"
    )

    page.keyboard.press("Escape")
    expect(toggle).to_have_attribute("aria-expanded", "false")
    expect(toggle).to_be_focused()
    expect(drawer).to_have_attribute("aria-hidden", "true")
    assert drawer.evaluate("element => element.inert") is True

    page.set_viewport_size({"width": 1200, "height": 900})
    expect(drawer).not_to_have_attribute("aria-hidden", "true")
    assert drawer.evaluate("element => element.inert") is False


def test_dice_tray_precedes_visit_actions_and_keeps_ephemeral_rolls_browser_local(
    play_server: tuple[LoopbackWebServer, Path, Path],
    page: Page,
) -> None:
    server, _, state_path = play_server
    original_journal = state_path.read_bytes()
    page.goto(_play_url(server))

    utility_headings = page.locator(".play-utility-rail h2").all_text_contents()
    assert utility_headings.index("Dice tray") < utility_headings.index("Current visit actions")

    page.locator("[data-play-dice-expression]").fill("2d6 + 1")
    page.locator("[data-play-dice-label]").fill("Hold the gate")
    page.locator("[data-play-dice-form]").get_by_role("button", name="Roll").click()

    result = page.locator("[data-play-dice-result]")
    expect(result.locator(".play-dice-equation strong")).to_have_text("13")
    assert state_path.read_bytes() == original_journal

    result.get_by_role("button", name="Insert in notebook").click()
    notebook_value = page.locator("[data-play-notebook]").input_value()
    assert "Hold the gate — 2d6 + 1 = 13" in notebook_value
    assert state_path.read_bytes() == original_journal

    page.goto(_play_url(server))
    expect(page.locator("[data-play-dice-recents] button", has_text="2d6 + 1")).to_be_visible()
    assert state_path.read_bytes() == original_journal


def test_play_reference_authoring_returns_to_table_without_mutating_journal(
    play_server: tuple[LoopbackWebServer, Path, Path],
    page: Page,
) -> None:
    server, adventure_path, state_path = play_server
    original_journal = state_path.read_bytes()
    page.goto(_play_url(server))

    page.get_by_text("Add to adventure", exact=True).click()
    page.get_by_role("link", name="Add linked reference").click()
    expect(page.get_by_text("Play improvisation", exact=True)).to_be_visible()

    page.locator('select[name="kind"]').select_option("person")
    page.locator('input[name="title"]').fill("Mara Venn")
    page.locator('textarea[name="summary"]').fill("A witness improvised at the table.")
    page.locator('textarea[name="content"]').fill(
        "## Mara Venn\n\nMara keeps the midnight arrival ledger."
    )
    page.locator('textarea[name="context"]').fill("Mara controls access to the improvised route.")
    page.get_by_role("button", name="Create reference").first.click()

    expect(page.get_by_text("Reference added", exact=True)).to_be_visible()
    selected_reference = page.locator("#encounter-references").get_by_text("Mara Venn", exact=True)
    expect(selected_reference).to_be_visible()
    assert state_path.read_bytes() == original_journal
    authored = load_adventure(adventure_path)
    reference = next(item for item in authored.references if item.title == "Mara Venn")
    assert any(
        link.reference_id == reference.id
        for link in authored.encounter_index()["alpha"].reference_links
    )


def test_transition_summary_appears_only_for_an_unusually_broad_update(
    play_server: tuple[LoopbackWebServer, Path, Path],
    page: Page,
) -> None:
    server, _, state_path = play_server
    original_journal = state_path.read_bytes()
    page.goto(_play_url(server))

    form = page.locator("[data-play-transition-form]")
    summary = form.locator("[data-play-transition-summary]")
    destination = form.locator("[data-play-transition-destination]")
    expect(summary).to_be_hidden()

    form.get_by_label("Find Beta").check()
    destination.select_option("beta")
    expect(summary).to_be_hidden()

    form.get_by_label("Find Gamma").check()
    expect(summary).to_be_hidden()

    form.get_by_label("Find Omega").check()
    expect(summary).to_have_text("This will record: 3 revelations established and a move to Beta.")

    clue_rows = form.locator(".play-transition-row")
    clue_rows.nth(0).get_by_label("Found").check()
    clue_rows.nth(1).get_by_label("Found").check()
    clue_rows.nth(2).get_by_label("Missed").check()
    expect(summary).to_have_text(
        "This will record: 2 leads found, 1 lead missed, 3 revelations established, "
        "and a move to Beta."
    )
    assert state_path.read_bytes() == original_journal
