"""Executable browser contracts for persistent-reference playthrough notes."""

from __future__ import annotations

from urllib.parse import urlencode

import pytest
from playwright.sync_api import Page, expect

from adventure_graph.application.play_tracking import (
    new_play_state,
    record_reference_note,
    start_session,
)
from adventure_graph.interfaces.web.styles import load_app_css
from tests.support.adventures import PERSON_REFERENCE_ID, reference_library_adventure
from tests.support.web import build_play_app, request_wsgi

pytestmark = pytest.mark.browser


def _reference_note_html() -> str:
    adventure = reference_library_adventure()
    state = start_session(new_play_state(adventure), title="Household audience")
    state = record_reference_note(
        adventure,
        state,
        PERSON_REFERENCE_ID,
        "Cora agreed to shelter the witnesses.",
    )
    app, _ = build_play_app(adventure, state)
    status, _, body = request_wsgi(
        app,
        "/play",
        query=urlencode({"encounter": "alpha", "reference": PERSON_REFERENCE_ID}),
    )
    assert status == "200 OK"
    return body.replace(
        '<script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css">',
        f"<style>{load_app_css()}</style>",
    )


@pytest.mark.parametrize("width", [900, 390])
def test_reference_note_panel_remains_bounded_and_preserves_authored_play_separation(
    page: Page,
    width: int,
) -> None:
    page.set_viewport_size({"width": width, "height": 1000})
    page.set_content(_reference_note_html())

    selected = page.locator("[data-play-selected-reference]")
    notes = selected.locator(".play-reference-notes")
    form = notes.locator("form.play-reference-note-form")

    expect(selected).to_be_visible()
    expect(selected).to_contain_text("Cora protects the household before its owner.")
    expect(notes).to_contain_text("Cora agreed to shelter the witnesses.")
    expect(notes).to_contain_text("Session 1: Household audience")
    expect(form.locator("textarea[name='text']")).to_be_visible()
    expect(form.locator("button[type='submit']")).to_have_text("Save reference note")
    expect(form).to_contain_text("It does not alter the authored description above.")

    panel_box = notes.bounding_box()
    assert panel_box is not None
    for control in form.locator("textarea, button").all():
        control_box = control.bounding_box()
        assert control_box is not None
        assert control_box["x"] >= panel_box["x"] - 1
        assert control_box["x"] + control_box["width"] <= (panel_box["x"] + panel_box["width"] + 1)

    assert page.evaluate("document.documentElement.scrollWidth") == page.evaluate(
        "document.documentElement.clientWidth"
    )
