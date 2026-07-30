"""Revision-aware editing for an adventure's validator policy."""

from __future__ import annotations

from dataclasses import dataclass, replace

from adventure_graph.application.errors import NoChangesRequestedError
from adventure_graph.application.project import (
    AuthoringProject,
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import (
    ValidationPolicy,
    ValidationReport,
)


@dataclass(frozen=True, slots=True)
class UpdateValidationPolicyCommand:
    """Requested validator thresholds based on one known project revision."""

    expected_revision: ProjectRevision
    policy: ValidationPolicy


@dataclass(frozen=True, slots=True)
class UpdateValidationPolicyResult:
    """Committed validator-policy update and resulting validation report."""

    before: Adventure
    after: Adventure
    revision: ProjectRevision
    validation_report: ValidationReport


class UpdateValidationPolicy:
    """Replace one adventure's validator policy through the authoring project seam."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: UpdateValidationPolicyCommand) -> UpdateValidationPolicyResult:
        """Commit the policy only when the submitted revision is current."""
        snapshot = self._project.load()
        if snapshot.revision != command.expected_revision:
            raise RevisionConflictError(
                "The project changed after these validator settings were loaded; "
                "reload before saving."
            )
        before = snapshot.adventure
        after = replace(before, validation_policy=command.policy)
        if after == before:
            raise NoChangesRequestedError("No validator setting changes were requested.")
        report = validate_adventure(after)
        revision = self._project.commit_adventure(after, snapshot.revision)
        return UpdateValidationPolicyResult(before, after, revision, report)
