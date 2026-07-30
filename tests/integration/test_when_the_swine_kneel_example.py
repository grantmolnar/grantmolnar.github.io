"""Regression checks for the long-form seven-encounter example."""

from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents, render_play_summary
from adventure_graph.application.play_tracking import (
    establish_revelation,
    new_play_state,
    project_play_state,
    record_visit,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.journal_archive_store import load_journal_archive
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.corpus_contracts import group_clues_by_revelation

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/when-the-swine-kneel")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"
EXAMPLE_PLAYTHROUGH_PATH = EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md"
EXAMPLE_ARCHIVE_PATH = (
    EXAMPLE_DIRECTORY / "archives" / "synthetic-complete-playthrough.journal.json"
)


@pytest.fixture(scope="module")
def swine_adventure() -> Adventure:
    """Load the final seven-encounter example once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def swine_state() -> PlayState:
    """Load the named-company demonstration journal once per module."""
    return load_play_state(EXAMPLE_STATE_PATH)


@pytest.fixture(scope="module")
def archived_swine_state() -> PlayState:
    """Load the archived synthetic playthrough once per module."""
    return load_journal_archive(EXAMPLE_ARCHIVE_PATH).play_state


def test_when_the_swine_kneel_is_a_valid_seven_encounter_adventure(
    swine_adventure: Adventure,
) -> None:
    """Keep the authored example aligned with its declared structural contract."""
    report = validate_adventure(swine_adventure)

    assert len(swine_adventure.encounters) == 7
    assert len(swine_adventure.revelations) == 10
    assert len(swine_adventure.clues) == 38
    assert report.is_valid
    assert report.edge_connectivity == 3


def test_swine_revelations_keep_independent_and_irregular_support(
    swine_adventure: Adventure,
) -> None:
    """Protect minimum redundancy without restoring the exact three-clue template."""
    clues_by_revelation = group_clues_by_revelation(swine_adventure.clues)

    support_counts = []
    for revelation in swine_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        support_counts.append(len(clues))
        assert len(clues) >= 3
        assert len({clue.source_encounter_id for clue in clues}) == len(clues)

    assert sorted(support_counts) == [3, 3, 3, 3, 3, 3, 3, 5, 6, 6]


def test_swine_example_renders_all_core_documents(
    swine_adventure: Adventure,
    swine_state: PlayState,
) -> None:
    """Ensure the example exercises source and runtime document generation."""
    report = validate_adventure(swine_adventure)
    documents = render_adventure_documents(swine_adventure, report, swine_state)

    assert set(documents) >= {
        "00-overview.md",
        "01-encounter-index.md",
        "02-clue-list.md",
        "03-revelation-list.md",
        "04-validation-report.md",
        "05-play-summary.md",
    }
    assert len([name for name in documents if name.startswith("encounters/")]) == 7
    assert "Result: PASS" in documents["04-validation-report.md"]
    stockyards_sheet = documents["encounters/southgate-stockyards.md"]
    assert "**Discovery:** Inspect the scale" in stockyards_sheet
    assert "**Supports:**" in stockyards_sheet
    assert "unlocks `the-chapel-of-the-first-survey`" in stockyards_sheet


def _run_route(
    adventure: Adventure, steps: tuple[tuple[str, str, tuple[str, ...]], ...]
) -> tuple[str, ...]:
    state = new_play_state(adventure)
    for operation, entity_id, clue_ids in steps:
        if operation == "visit":
            state = record_visit(adventure, state, entity_id, clue_ids)
        else:
            state = establish_revelation(adventure, state, entity_id, clue_ids)
    return tuple(visit.encounter_id for visit in project_play_state(adventure, state).visits)


@pytest.mark.parametrize(
    ("steps", "expected_visits"),
    [
        (
            (
                ("visit", "the-hall-of-petitions", ("the-rillcross-petition-bundle",)),
                (
                    "establish",
                    "rillcross-reveals-the-warnings-full-geography",
                    ("the-rillcross-petition-bundle",),
                ),
                ("visit", "rillcross-farm-belt", ("the-outer-pressure-vent",)),
                (
                    "establish",
                    "the-deep-bell-lies-beneath-veyr",
                    ("the-outer-pressure-vent",),
                ),
                ("visit", "the-deep-bell", ()),
            ),
            ("the-hall-of-petitions", "rillcross-farm-belt", "the-deep-bell"),
        ),
        (
            (
                (
                    "visit",
                    "the-hall-of-petitions",
                    ("southgate-condemnation-docket",),
                ),
                (
                    "establish",
                    "the-southgate-stockyards-carry-the-warning-inside-veyr",
                    ("southgate-condemnation-docket",),
                ),
                (
                    "visit",
                    "southgate-stockyards",
                    ("the-obsolete-survey-marker-socket",),
                ),
                (
                    "establish",
                    "the-chapel-of-the-first-survey-keeps-the-lost-doctrine",
                    ("the-obsolete-survey-marker-socket",),
                ),
                (
                    "visit",
                    "the-chapel-of-the-first-survey",
                    ("the-surveyors-stair-to-the-tuning-crown",),
                ),
                (
                    "establish",
                    "the-deep-bell-lies-beneath-veyr",
                    ("the-surveyors-stair-to-the-tuning-crown",),
                ),
                ("visit", "the-deep-bell", ()),
            ),
            (
                "the-hall-of-petitions",
                "southgate-stockyards",
                "the-chapel-of-the-first-survey",
                "the-deep-bell",
            ),
        ),
        (
            (
                ("visit", "the-hall-of-petitions", ("college-jurisdiction-over-civic-resonance",)),
                (
                    "establish",
                    "the-college-of-civic-measure-can-test-the-buried-pulse",
                    ("college-jurisdiction-over-civic-resonance",),
                ),
                (
                    "visit",
                    "the-college-of-civic-measure",
                    ("pulse-to-pump-phase-correlation",),
                ),
                (
                    "establish",
                    "the-nine-mile-pump-house-is-driving-the-crisis",
                    ("pulse-to-pump-phase-correlation",),
                ),
                (
                    "visit",
                    "the-nine-mile-pump-house",
                    ("the-hydraulic-service-conduit",),
                ),
                (
                    "establish",
                    "the-deep-bell-lies-beneath-veyr",
                    ("the-hydraulic-service-conduit",),
                ),
                ("visit", "the-deep-bell", ()),
            ),
            (
                "the-hall-of-petitions",
                "the-college-of-civic-measure",
                "the-nine-mile-pump-house",
                "the-deep-bell",
            ),
        ),
    ],
)
def test_three_independent_route_families_reach_the_deep_bell(
    swine_adventure: Adventure,
    steps: tuple[tuple[str, str, tuple[str, ...]], ...],
    expected_visits: tuple[str, ...],
) -> None:
    """Protect the three field, historical, and technical approaches to the finale."""
    assert _run_route(swine_adventure, steps) == expected_visits


def test_checked_in_swine_journal_is_a_complete_named_party_playthrough(
    swine_adventure: Adventure,
    swine_state: PlayState,
) -> None:
    """Keep the Ashlar Company route, omissions, and resolution stable."""
    projection = project_play_state(swine_adventure, swine_state)
    visited = tuple(visit.encounter_id for visit in projection.visits)
    progress = projection.revelation_progress_index()
    spotted = set(projection.spotted_clue_ids)

    assert len(swine_state.events) == 96
    assert visited == (
        "the-hall-of-petitions",
        "southgate-stockyards",
        "rillcross-farm-belt",
        "the-college-of-civic-measure",
        "the-hall-of-petitions",
        "the-chapel-of-the-first-survey",
        "the-nine-mile-pump-house",
        "the-deep-bell",
    )
    assert all(progress[revelation.id].is_established for revelation in swine_adventure.revelations)
    assert set(projection.available_encounter_ids) == {
        encounter.id for encounter in swine_adventure.encounters
    }
    assert len(spotted) == 25
    assert {clue.id for clue in swine_adventure.clues} - spotted == {
        "southgate-amplitude-map",
        "nine-mile-maintenance-traffic",
        "plan-of-the-southgate-sounding-station",
        "the-seized-college-recorder",
        "rillcross-pressure-ledger",
        "dasts-filed-convocation-load-schedule",
        "dasts-preemptive-cull-circular",
        "the-six-line-isolation-drill",
        "the-surveyors-livestock-observation-table",
        "the-confiscated-farm-signal-board",
        "the-surface-reports-answer-the-bell",
        "the-fresh-overdrive-scars",
        "the-three-independent-control-paths",
    }
    assert any(
        consequence.encounter_id == "the-deep-bell"
        and "Five sounding lines were retuned" in consequence.text
        for consequence in projection.consequences
    )


def test_swine_full_playthrough_narrates_the_fixed_decisions() -> None:
    """Keep the human-readable playthrough aligned with the journal's major choices."""
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")

    required_text = [
        "Hall -> Southgate -> Rillcross -> College -> Hall -> Chapel -> Pump House -> Deep Bell",
        "Dast remains an adviser under guard",
        "Five-line retuning",
        "Thirteen clues remain unseen",
        "Session Four: Five lines answer",
    ]

    assert all(text in playthrough for text in required_text)


def test_archived_swine_journal_is_consistent_and_complete(
    swine_adventure: Adventure,
    archived_swine_state: PlayState,
) -> None:
    """Keep the archived full investigation useful as a runtime example."""
    projection = project_play_state(swine_adventure, archived_swine_state)
    visited = tuple(visit.encounter_id for visit in projection.visits)
    progress = projection.revelation_progress_index()

    assert visited == (
        "the-hall-of-petitions",
        "southgate-stockyards",
        "the-college-of-civic-measure",
        "the-hall-of-petitions",
        "rillcross-farm-belt",
        "the-chapel-of-the-first-survey",
        "the-nine-mile-pump-house",
        "the-deep-bell",
    )
    assert all(
        progress[revelation.id].is_established
        for revelation in swine_adventure.revelations
        if revelation.required
    )
    assert not progress["the-hall-can-restrain-the-offices-destroying-the-evidence"].is_established
    assert progress["the-hall-can-restrain-the-offices-destroying-the-evidence"].is_supported
    assert set(projection.available_encounter_ids) == {
        encounter.id for encounter in swine_adventure.encounters
    }
    assert len(projection.consequences) >= 5
    summary = render_play_summary(swine_adventure, archived_swine_state)
    assert "Supported but Unconfirmed Revelations" in summary
    assert "The Hall can restrain the offices destroying the evidence" in summary
    assert "Five sounding lines were retuned" in summary
