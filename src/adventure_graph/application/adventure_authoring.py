"""Revision-aware editing for adventure-level authored metadata."""

from __future__ import annotations

from dataclasses import dataclass, replace

from adventure_graph.application.errors import NoChangesRequestedError
from adventure_graph.application.project import (
    AuthoringProject,
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.application.project_integrity import validate_related_play_states
from adventure_graph.domain.adventure import (
    Adventure,
    AdventureTags,
)
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import ValidationReport


@dataclass(frozen=True, slots=True)
class UpdateAdventureCommand:
    """Requested adventure-metadata changes based on one known project revision."""

    expected_revision: ProjectRevision
    title: str
    synopsis: str
    premise: str
    explanation: str
    tags: AdventureTags | None = None


@dataclass(frozen=True, slots=True)
class UpdateAdventureResult:
    """Committed adventure-metadata update and resulting project state."""

    before: Adventure
    after: Adventure
    revision: ProjectRevision
    validation_report: ValidationReport


class UpdateAdventure:
    """Apply and commit one revision-aware adventure metadata edit."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: UpdateAdventureCommand) -> UpdateAdventureResult:
        """Commit metadata while preserving the adventure's immutable identifier."""
        snapshot = self._project.load()
        if snapshot.revision != command.expected_revision:
            raise RevisionConflictError(
                "The project changed after this adventure was loaded; reload before saving."
            )
        before = snapshot.adventure
        title = command.title.strip()
        if not title:
            raise ValueError("Adventure title must not be empty.")
        after = replace(
            before,
            title=title,
            synopsis=command.synopsis,
            premise=command.premise,
            explanation=command.explanation,
            tags=before.tags if command.tags is None else command.tags,
        )
        if after == before:
            raise NoChangesRequestedError("No authoring changes were requested.")

        validate_related_play_states(after, snapshot.related_play_states)
        report = validate_adventure(after)
        revision = self._project.commit_adventure(after, snapshot.revision)
        return UpdateAdventureResult(before, after, revision, report)
