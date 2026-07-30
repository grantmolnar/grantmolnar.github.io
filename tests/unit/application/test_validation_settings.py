"""Tests for revision-aware validator-policy editing."""

from __future__ import annotations

import pytest
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.projects import authoring_project

from adventure_graph.application.errors import NoChangesRequestedError
from adventure_graph.application.project import (
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.application.validation_settings import (
    UpdateValidationPolicy,
    UpdateValidationPolicyCommand,
)
from adventure_graph.domain.validation_models import ValidationPolicy


def test_update_validation_policy_commits_and_revalidates() -> None:
    project = authoring_project()
    policy = ValidationPolicy(
        minimum_clues_per_revelation=2,
        minimum_source_encounters_per_revelation=2,
        minimum_outgoing_clues_per_encounter=1,
        minimum_distinct_encounter_targets_per_encounter=1,
        minimum_edge_connectivity=2,
        require_directed_reachability=False,
    )

    result = UpdateValidationPolicy(project).execute(
        UpdateValidationPolicyCommand(ProjectRevision("revision-1"), policy)
    )

    assert result.after.validation_policy == policy
    assert result.revision == ProjectRevision("revision-2")
    assert project.snapshot.adventure.validation_policy == policy


def test_update_validation_policy_rejects_stale_and_noop_requests() -> None:
    adventure = complete_four_encounter_adventure()
    project = authoring_project(adventure)
    command = UpdateValidationPolicy(project)

    with pytest.raises(RevisionConflictError):
        command.execute(
            UpdateValidationPolicyCommand(ProjectRevision("stale"), adventure.validation_policy)
        )
    with pytest.raises(NoChangesRequestedError, match="No validator setting changes"):
        command.execute(
            UpdateValidationPolicyCommand(
                ProjectRevision("revision-1"), adventure.validation_policy
            )
        )


def test_validation_policy_rejects_negative_minimums() -> None:
    with pytest.raises(ValueError, match="zero or greater"):
        ValidationPolicy(minimum_clues_per_revelation=-1)
