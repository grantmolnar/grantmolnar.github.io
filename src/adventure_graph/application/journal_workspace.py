"""Snapshot-consistent composite query for the journal browser workspace."""

from __future__ import annotations

from dataclasses import dataclass

from adventure_graph.application.play_journal import (
    PlayJournalProject,
    PlayJournalStatusResult,
    build_play_journal_status,
)
from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.run_workspace import (
    RunDashboardResult,
    build_run_dashboard,
)


@dataclass(frozen=True, slots=True)
class JournalWorkspaceResult:
    """Journal history and run context derived from one project snapshot."""

    journal: PlayJournalStatusResult
    dashboard: RunDashboardResult

    def __post_init__(self) -> None:
        """Reject composite results assembled from different project snapshots."""
        if self.journal.revision != self.dashboard.revision:
            raise ValueError("Journal history and run dashboard revisions must match.")
        if self.journal.adventure != self.dashboard.adventure:
            raise ValueError("Journal history and run dashboard adventures must match.")

    @property
    def revision(self) -> ProjectRevision:
        """Return the single revision shared by both page projections."""
        return self.journal.revision


class GetJournalWorkspace:
    """Load once and build every projection required by the journal page."""

    def __init__(self, project: PlayJournalProject, *, recent_operation_limit: int = 8) -> None:
        if recent_operation_limit <= 0:
            raise ValueError("The recent-operation limit must be positive.")
        self._project = project
        self._recent_operation_limit = recent_operation_limit

    def execute(self) -> JournalWorkspaceResult:
        """Return journal history and run context from one immutable snapshot."""
        snapshot = self._project.load()
        return JournalWorkspaceResult(
            journal=build_play_journal_status(snapshot),
            dashboard=build_run_dashboard(
                snapshot,
                recent_operation_limit=self._recent_operation_limit,
            ),
        )
