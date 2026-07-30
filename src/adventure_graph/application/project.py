"""Shared application contracts for revision-aware authored projects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState


class RevisionConflictError(ValueError):
    """Raised when a modifying command was based on an obsolete project snapshot."""


@dataclass(frozen=True, slots=True)
class ProjectRevision:
    """Opaque revision token for one authored project snapshot."""

    value: str


@dataclass(frozen=True, slots=True)
class RelatedPlayState:
    """One play journal considered when validating an authored change."""

    source: str
    state: PlayState


@dataclass(frozen=True, slots=True)
class AuthoringSnapshot:
    """Adventure and related journals loaded at one project revision."""

    adventure: Adventure
    related_play_states: tuple[RelatedPlayState, ...]
    revision: ProjectRevision


class AuthoringProject(Protocol):
    """Application-facing port for loading and committing authored state."""

    def load(self) -> AuthoringSnapshot:
        """Load one internally consistent project snapshot."""
        ...

    def commit_adventure(
        self,
        adventure: Adventure,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Commit an adventure only when the project still has the expected revision."""
        ...

    def commit_authoring(
        self,
        adventure: Adventure,
        related_play_states: tuple[RelatedPlayState, ...],
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Commit an adventure and rewritten related journals at one expected revision."""
        ...
