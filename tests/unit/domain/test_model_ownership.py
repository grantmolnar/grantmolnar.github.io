"""Tests for direct domain-model ownership."""

from __future__ import annotations

import pytest

from adventure_graph.domain.adventure import (
    Adventure,
    AdventureTags,
    Clue,
    Encounter,
    Revelation,
)
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    DiceRollRecordedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    PlayOperationVoidedEvent,
    RevelationEstablishedEvent,
    RevelationForeclosedEvent,
    RevelationReopenedEvent,
    SessionEndedEvent,
    SessionStartedEvent,
    VisitNoteRecordedEvent,
)
from adventure_graph.domain.play_state import (
    ClueProgress,
    EncounterConsequenceRecord,
    EncounterProgress,
    EncounterUnlockRecord,
    NarrativeRecord,
    PlayCorrectionRecord,
    PlayProjection,
    PlayState,
    RevelationProgress,
    SessionRecord,
    VisitRecord,
)
from adventure_graph.domain.validation_models import (
    GraphConnectivityDiagnosis,
    GraphRepairSuggestion,
    ValidationIssue,
    ValidationPolicy,
    ValidationReport,
)

_OWNED_TYPES = (
    (Adventure, "adventure_graph.domain.adventure"),
    (AdventureTags, "adventure_graph.domain.adventure"),
    (Clue, "adventure_graph.domain.adventure"),
    (Encounter, "adventure_graph.domain.adventure"),
    (Revelation, "adventure_graph.domain.adventure"),
    (GraphConnectivityDiagnosis, "adventure_graph.domain.validation_models"),
    (GraphRepairSuggestion, "adventure_graph.domain.validation_models"),
    (ValidationIssue, "adventure_graph.domain.validation_models"),
    (ValidationPolicy, "adventure_graph.domain.validation_models"),
    (ValidationReport, "adventure_graph.domain.validation_models"),
    (ClueMissedEvent, "adventure_graph.domain.play_events"),
    (ClueSpottedEvent, "adventure_graph.domain.play_events"),
    (DiceRollRecordedEvent, "adventure_graph.domain.play_events"),
    (EncounterConsequenceRecordedEvent, "adventure_graph.domain.play_events"),
    (EncounterUnlockedEvent, "adventure_graph.domain.play_events"),
    (EncounterVisitedEvent, "adventure_graph.domain.play_events"),
    (PlayOperationVoidedEvent, "adventure_graph.domain.play_events"),
    (RevelationEstablishedEvent, "adventure_graph.domain.play_events"),
    (RevelationForeclosedEvent, "adventure_graph.domain.play_events"),
    (RevelationReopenedEvent, "adventure_graph.domain.play_events"),
    (SessionEndedEvent, "adventure_graph.domain.play_events"),
    (SessionStartedEvent, "adventure_graph.domain.play_events"),
    (VisitNoteRecordedEvent, "adventure_graph.domain.play_events"),
    (ClueProgress, "adventure_graph.domain.play_state"),
    (NarrativeRecord, "adventure_graph.domain.play_state"),
    (EncounterConsequenceRecord, "adventure_graph.domain.play_state"),
    (EncounterProgress, "adventure_graph.domain.play_state"),
    (EncounterUnlockRecord, "adventure_graph.domain.play_state"),
    (PlayCorrectionRecord, "adventure_graph.domain.play_state"),
    (PlayProjection, "adventure_graph.domain.play_state"),
    (PlayState, "adventure_graph.domain.play_state"),
    (RevelationProgress, "adventure_graph.domain.play_state"),
    (SessionRecord, "adventure_graph.domain.play_state"),
    (VisitRecord, "adventure_graph.domain.play_state"),
)


@pytest.mark.parametrize(("owned_type", "owner_module"), _OWNED_TYPES)
def test_domain_types_report_their_defining_module(
    owned_type: type[object],
    owner_module: str,
) -> None:
    assert owned_type.__module__ == owner_module
