"""Tests for the snapshot-consistent journal workspace query."""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.projects import SequencedPlayProject

from adventure_graph.application.journal_workspace import (
    GetJournalWorkspace,
    JournalWorkspaceResult,
)
from adventure_graph.application.play_journal import (
    PlayJournalSnapshot,
    build_play_journal_status,
)
from adventure_graph.application.play_tracking import (
    new_play_state,
    record_visit,
)
from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.run_workspace import build_run_dashboard


def _snapshot(revision: str, *, with_visit: bool) -> PlayJournalSnapshot:
    adventure = complete_four_encounter_adventure()
    state = new_play_state(adventure)
    if with_visit:
        state = record_visit(adventure, state, "alpha")
    return PlayJournalSnapshot(adventure, state, ProjectRevision(revision))


def test_journal_workspace_builds_both_views_from_one_loaded_snapshot() -> None:
    project = SequencedPlayProject(
        (
            _snapshot("revision-1", with_visit=False),
            _snapshot("revision-2", with_visit=True),
        )
    )

    result = GetJournalWorkspace(project).execute()

    assert project.load_count == 1
    assert result.revision == ProjectRevision("revision-1")
    assert result.journal.revision == result.dashboard.revision
    assert result.journal.event_count == 0
    assert result.dashboard.current_visit is None


def test_journal_workspace_result_rejects_mixed_revisions() -> None:
    first = _snapshot("revision-1", with_visit=False)
    second = _snapshot("revision-2", with_visit=True)

    with pytest.raises(ValueError, match="revisions must match"):
        JournalWorkspaceResult(
            journal=build_play_journal_status(first),
            dashboard=build_run_dashboard(second),
        )


def test_journal_workspace_result_rejects_mixed_adventures() -> None:
    snapshot = _snapshot("revision-1", with_visit=False)
    changed = replace(snapshot, adventure=replace(snapshot.adventure, title="Changed title"))

    with pytest.raises(ValueError, match="adventures must match"):
        JournalWorkspaceResult(
            journal=build_play_journal_status(snapshot),
            dashboard=build_run_dashboard(changed),
        )


def test_journal_workspace_preserves_the_run_recent_operation_limit() -> None:
    snapshot = _snapshot("revision-1", with_visit=True)
    project = SequencedPlayProject((snapshot,))

    result = GetJournalWorkspace(project, recent_operation_limit=1).execute()

    assert len(result.dashboard.recent_operations) == 1
    assert result.dashboard.total_operation_count == 1


def test_journal_workspace_rejects_nonpositive_recent_operation_limit() -> None:
    project = SequencedPlayProject((_snapshot("revision-1", with_visit=False),))

    with pytest.raises(ValueError, match="must be positive"):
        GetJournalWorkspace(project, recent_operation_limit=0)
