"""Play-mode rendering coverage across the bundled full-size journals."""

from __future__ import annotations

from pathlib import Path

import pytest

from adventure_graph.application.run_workspace import GetRunDashboard
from adventure_graph.infrastructure.local_play_journal import LocalPlayJournalProject
from adventure_graph.interfaces.web.play_rendering import render_play

pytestmark = pytest.mark.corpus

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
JOURNAL_PATHS = tuple(sorted(EXAMPLES.glob("*/play-state.example.json")))


@pytest.mark.parametrize("state_path", JOURNAL_PATHS, ids=lambda path: path.parent.name)
def test_bundled_journal_renders_in_play_mode_without_mutation(state_path: Path) -> None:
    adventure_path = state_path.parent / "adventure.json"
    before = state_path.read_bytes()

    dashboard = GetRunDashboard(LocalPlayJournalProject(adventure_path, state_path)).execute()
    page = render_play(dashboard, str(adventure_path), csrf_token="known-token")

    assert f"<title>Play — {dashboard.adventure.title}</title>" in page
    assert "Chronological route" in page
    assert "Find authored material" in page
    assert page.count("data-play-route-link") == len(dashboard.projection.visits)
    assert page.count("data-play-search-entry") == (
        len(dashboard.adventure.encounters)
        + len(dashboard.adventure.clues)
        + len(dashboard.adventure.revelations)
        + len(dashboard.adventure.references)
    )
    assert state_path.read_bytes() == before
