"""Small in-memory ports for application tests.

These doubles model optimistic concurrency and retain committed values, while keeping
individual tests focused on use-case behavior rather than persistence plumbing.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from adventure_graph.application.play_journal import PlayJournalSnapshot
from adventure_graph.application.project import (
    AuthoringSnapshot,
    ProjectRevision,
    RelatedPlayState,
    RevisionConflictError,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from tests.support.adventures import complete_four_encounter_adventure


@dataclass
class InMemoryAuthoringProject:
    """Mutable authoring port with optimistic concurrency."""

    snapshot: AuthoringSnapshot
    revision_prefix: str = "revision"
    commit_count: int = 0
    committed_adventure: Adventure | None = None

    def load(self) -> AuthoringSnapshot:
        """Return the current authoring snapshot."""
        return self.snapshot

    def commit_adventure(
        self,
        adventure: Adventure,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Commit an adventure only at the current revision."""
        self._require_current_revision(expected_revision)
        revision = self._next_revision()
        self.committed_adventure = adventure
        self.snapshot = replace(self.snapshot, adventure=adventure, revision=revision)
        return revision

    def commit_authoring(
        self,
        adventure: Adventure,
        related_play_states: tuple[RelatedPlayState, ...],
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Commit an adventure and remapped journals atomically."""
        self._require_current_revision(expected_revision)
        revision = self._next_revision()
        self.committed_adventure = adventure
        self.snapshot = replace(
            self.snapshot,
            adventure=adventure,
            related_play_states=related_play_states,
            revision=revision,
        )
        return revision

    def _require_current_revision(self, expected_revision: ProjectRevision) -> None:
        if expected_revision != self.snapshot.revision:
            raise RevisionConflictError("stale revision")

    def _next_revision(self) -> ProjectRevision:
        self.commit_count += 1
        return ProjectRevision(f"{self.revision_prefix}-{self.commit_count + 1}")


@dataclass
class ReadOnlyAuthoringProject:
    """Authoring query port that fails loudly if a query attempts a write."""

    snapshot: AuthoringSnapshot

    def load(self) -> AuthoringSnapshot:
        """Return the fixed authoring snapshot."""
        return self.snapshot

    def commit_adventure(
        self,
        adventure: Adventure,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Reject writes from read-only use cases."""
        raise AssertionError(f"unexpected commit of {adventure.id} at {expected_revision}")

    def commit_authoring(
        self,
        adventure: Adventure,
        related_play_states: tuple[RelatedPlayState, ...],
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Reject coordinated writes from read-only use cases."""
        del related_play_states
        raise AssertionError(f"unexpected commit of {adventure.id} at {expected_revision}")


@dataclass
class InMemoryPlayProject:
    """Mutable play-journal port with optimistic concurrency."""

    snapshot: PlayJournalSnapshot
    revision_prefix: str = "revision"
    fixed_commit_revision: ProjectRevision | None = None
    commit_count: int = 0
    load_count: int = 0

    def load(self) -> PlayJournalSnapshot:
        """Return the current play-journal snapshot and record the read."""
        self.load_count += 1
        return self.snapshot

    def commit_state(
        self,
        state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Commit play state only at the current revision."""
        if expected_revision != self.snapshot.revision:
            raise RevisionConflictError("stale journal revision")
        self.commit_count += 1
        revision = self.fixed_commit_revision or ProjectRevision(
            f"{self.revision_prefix}-{self.commit_count + 1}"
        )
        self.snapshot = replace(self.snapshot, state=state, revision=revision)
        return revision


@dataclass
class SequencedPlayProject:
    """Return configured play snapshots in order and reject writes."""

    snapshots: tuple[PlayJournalSnapshot, ...]
    load_count: int = 0

    def load(self) -> PlayJournalSnapshot:
        """Return the next configured snapshot, repeating the final value."""
        snapshot = self.snapshots[min(self.load_count, len(self.snapshots) - 1)]
        self.load_count += 1
        return snapshot

    def commit_state(
        self,
        state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Reject writes from this query-focused port double."""
        del state, expected_revision
        raise AssertionError("This play project is read-only.")


@dataclass(frozen=True)
class ReadOnlyPlayProject:
    """Play-journal query port that fails loudly if a query attempts a write."""

    snapshot: PlayJournalSnapshot

    def load(self) -> PlayJournalSnapshot:
        """Return the fixed play-journal snapshot."""
        return self.snapshot

    def commit_state(
        self,
        state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Reject writes from read-only use cases."""
        del state
        raise AssertionError(f"unexpected play-state commit at {expected_revision}")


def authoring_project(
    adventure: Adventure | None = None,
    *,
    related_play_states: tuple[RelatedPlayState, ...] = (),
    revision: str = "revision-1",
    revision_prefix: str = "revision",
) -> InMemoryAuthoringProject:
    """Build a writable authoring project with conventional test defaults."""
    return InMemoryAuthoringProject(
        AuthoringSnapshot(
            adventure=adventure or complete_four_encounter_adventure(),
            related_play_states=related_play_states,
            revision=ProjectRevision(revision),
        ),
        revision_prefix=revision_prefix,
    )


def read_only_authoring_project(
    adventure: Adventure | None = None,
    *,
    related_play_states: tuple[RelatedPlayState, ...] = (),
    revision: str = "revision-1",
) -> ReadOnlyAuthoringProject:
    """Build a read-only authoring project with conventional test defaults."""
    return ReadOnlyAuthoringProject(
        AuthoringSnapshot(
            adventure=adventure or complete_four_encounter_adventure(),
            related_play_states=related_play_states,
            revision=ProjectRevision(revision),
        )
    )


def play_project(
    state: PlayState,
    adventure: Adventure | None = None,
    *,
    revision: str = "revision-1",
    revision_prefix: str = "revision",
    fixed_commit_revision: str | None = None,
) -> InMemoryPlayProject:
    """Build a writable play-journal project around an explicit state."""
    resolved_adventure = adventure or complete_four_encounter_adventure()
    return InMemoryPlayProject(
        PlayJournalSnapshot(
            adventure=resolved_adventure,
            state=state,
            revision=ProjectRevision(revision),
        ),
        revision_prefix=revision_prefix,
        fixed_commit_revision=(
            ProjectRevision(fixed_commit_revision) if fixed_commit_revision is not None else None
        ),
    )


def read_only_play_project(
    state: PlayState,
    adventure: Adventure | None = None,
    *,
    revision: str = "revision-1",
) -> ReadOnlyPlayProject:
    """Build a read-only play-journal project around an explicit state."""
    resolved_adventure = adventure or complete_four_encounter_adventure()
    return ReadOnlyPlayProject(
        PlayJournalSnapshot(
            adventure=resolved_adventure,
            state=state,
            revision=ProjectRevision(revision),
        )
    )
