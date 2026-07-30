"""Playwright fixtures for executable local-browser tests."""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import Browser, Page, Playwright, sync_playwright


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """Launch one headless Chromium process for the browser-test session."""
    with sync_playwright() as playwright:
        launched = _launch_chromium(playwright)
        try:
            yield launched
        finally:
            launched.close()


@pytest.fixture
def page(browser: Browser) -> Iterator[Page]:
    """Return one isolated browser page with fresh browser-local state."""
    context = browser.new_context(viewport={"width": 1440, "height": 1000})
    opened = context.new_page()
    try:
        yield opened
    finally:
        context.close()


def _launch_chromium(playwright: Playwright) -> Browser:
    override = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE")
    if override:
        return playwright.chromium.launch(headless=True, executable_path=override)

    system_chromium = shutil.which("chromium") or shutil.which("chromium-browser")
    if system_chromium:
        return playwright.chromium.launch(headless=True, executable_path=system_chromium)

    browser_path = Path(playwright.chromium.executable_path)
    if browser_path.exists():
        return playwright.chromium.launch(headless=True)

    pytest.fail(
        "Chromium is unavailable. Run `python -m playwright install chromium` or set "
        "PLAYWRIGHT_CHROMIUM_EXECUTABLE."
    )
