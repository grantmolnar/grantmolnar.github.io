"""Property evidence for append-only journal projection invariants."""

from __future__ import annotations

from dataclasses import replace

import pytest

pytest.importorskip("hypothesis")

from hypothesis import given, settings
from tests.support.property_strategies import JournalCase, valid_journal_cases

from adventure_graph.application.play_tracking import (
    correct_latest_operation,
    latest_active_operation_number,
    project_play_state,
)
from adventure_graph.domain.play_state import PlayProjection

pytestmark = pytest.mark.property


@settings(max_examples=80, deadline=None, derandomize=True)
@given(case=valid_journal_cases())
def test_projection_is_deterministic_ordered_and_owned_by_the_authored_adventure(
    case: JournalCase,
) -> None:
    """Projection must be stable and contain only unique authored identifiers."""
    projection = project_play_state(case.adventure, case.state)

    assert project_play_state(case.adventure, case.state) == projection
    assert case.state.visits == projection.visits
    assert [event.sequence for event in case.state.events] == list(
        range(1, len(case.state.events) + 1)
    )
    assert [event.operation_number for event in case.state.events] == sorted(
        event.operation_number for event in case.state.events
    )
    assert len(projection.spotted_clue_ids) == len(set(projection.spotted_clue_ids))
    assert len(projection.available_encounter_ids) == len(set(projection.available_encounter_ids))
    assert set(projection.spotted_clue_ids) <= set(case.adventure.clue_index())
    assert set(projection.available_encounter_ids) <= set(case.adventure.encounter_index())


@settings(max_examples=80, deadline=None, derandomize=True)
@given(case=valid_journal_cases())
def test_voiding_latest_operation_restores_the_prior_derived_state(case: JournalCase) -> None:
    """An append-only correction must restore the state before the latest active operation."""
    latest = latest_active_operation_number(case.state)
    assert latest is not None
    prior = replace(
        case.state,
        events=tuple(event for event in case.state.events if event.operation_number != latest),
    )

    corrected = correct_latest_operation(case.adventure, case.state, "Property correction")

    assert corrected.active_events == prior.events
    corrected_projection = _stateful_projection(project_play_state(case.adventure, corrected))
    prior_projection = _stateful_projection(project_play_state(case.adventure, prior))
    assert corrected_projection == prior_projection


def _stateful_projection(projection: PlayProjection) -> tuple[object, ...]:
    return (
        projection.visits,
        projection.spotted_clue_ids,
        projection.revelation_progress,
        projection.available_encounter_ids,
        projection.unlocks,
        projection.consequences,
        projection.sessions,
        projection.active_session_number,
        projection.clue_progress,
        projection.encounter_progress,
    )
