"""Tests for transport-neutral read-only project queries."""

from __future__ import annotations

import pytest
from tests.support.projects import ReadOnlyAuthoringProject, read_only_authoring_project

from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.project_browsing import (
    GetAdventureOverview,
    GetClueDetail,
    GetRevelationDetail,
)


def _project() -> ReadOnlyAuthoringProject:
    return read_only_authoring_project()


def test_overview_returns_complete_adventure_and_validation() -> None:
    result = GetAdventureOverview(_project()).execute()

    assert result.adventure.id == "complete-four"
    assert len(result.adventure.encounters) == 4
    assert result.revision == ProjectRevision("revision-1")
    assert result.validation_report.is_valid
    assert result.validation_report.edge_connectivity == 3


def test_revelation_detail_combines_support_sources_and_destination() -> None:
    result = GetRevelationDetail(_project()).execute("find-beta")

    assert result.detail.revelation.title == "Find Beta"
    assert tuple(clue.id for clue in result.detail.supporting_clues) == (
        "alpha-to-beta",
        "gamma-to-beta",
        "omega-to-beta",
    )
    assert tuple(encounter.id for encounter in result.detail.source_encounters) == (
        "alpha",
        "gamma",
        "omega",
    )
    assert result.detail.unlocks_encounter is not None
    assert result.detail.unlocks_encounter.id == "beta"
    assert result.validation_report.is_valid
    assert result.detail.dependency_preview.authored_references == (
        "Lead: alpha points to beta",
        "Lead: gamma points to beta",
        "Lead: omega points to beta",
    )


def test_clue_detail_combines_source_revelation_and_destination() -> None:
    result = GetClueDetail(_project()).execute("alpha-to-beta")

    assert result.detail.source_encounter.id == "alpha"
    assert result.detail.revelation.id == "find-beta"
    assert result.detail.destination_encounter is not None
    assert result.detail.destination_encounter.id == "beta"
    assert result.validation_report.is_valid
    assert result.detail.dependency_preview.move_context == (
        "Source encounter: Alpha",
        "Revelation: Find Beta",
    )


def test_browsing_queries_report_unknown_identifiers() -> None:
    project = _project()

    for query, identifier, label in (
        (GetRevelationDetail(project).execute, "missing", "revelation"),
        (GetClueDetail(project).execute, "missing", "lead"),
    ):
        with pytest.raises(ValueError, match=rf"Unknown {label} 'missing'\."):
            query(identifier)
