"""Snapshot-consistent composite query for the operational ledger page."""

from __future__ import annotations

from dataclasses import dataclass

from adventure_graph.application.play_journal import PlayJournalProject
from adventure_graph.application.play_ledgers import (
    PlayLedgerScope,
    PlayLedgersResult,
    build_play_ledgers,
)
from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.run_workspace import RunDashboardResult, build_run_dashboard


@dataclass(frozen=True, slots=True)
class PlayLedgerWorkspaceResult:
    """Operational ledgers and run context derived from one project snapshot."""

    ledgers: PlayLedgersResult
    dashboard: RunDashboardResult

    def __post_init__(self) -> None:
        """Reject composite results assembled from different project snapshots."""
        if self.ledgers.revision != self.dashboard.revision:
            raise ValueError("Play ledgers and run dashboard revisions must match.")
        if self.ledgers.adventure != self.dashboard.adventure:
            raise ValueError("Play ledgers and run dashboard adventures must match.")

    @property
    def revision(self) -> ProjectRevision:
        """Return the single revision shared by both page projections."""
        return self.ledgers.revision


class GetPlayLedgerWorkspace:
    """Load once and build every projection required by a ledger page."""

    def __init__(self, project: PlayJournalProject, *, recent_operation_limit: int = 8) -> None:
        if recent_operation_limit <= 0:
            raise ValueError("The recent-operation limit must be positive.")
        self._project = project
        self._recent_operation_limit = recent_operation_limit

    def execute(self, scope: PlayLedgerScope = "playthrough") -> PlayLedgerWorkspaceResult:
        """Return selected ledgers and run context from one immutable snapshot."""
        snapshot = self._project.load()
        return PlayLedgerWorkspaceResult(
            ledgers=build_play_ledgers(snapshot, scope),
            dashboard=build_run_dashboard(
                snapshot,
                recent_operation_limit=self._recent_operation_limit,
            ),
        )
