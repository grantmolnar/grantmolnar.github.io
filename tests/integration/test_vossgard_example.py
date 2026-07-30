"""Regression checks for the Shadowfell offensive campaign example."""

import re
from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents, render_play_summary
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.corpus_contracts import (
    assert_rendered_documents_match,
    group_clues_by_encounter,
    group_clues_by_revelation,
)

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-march-on-vossgard")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"
EXAMPLE_PLAYTHROUGH_PATH = EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md"

SECOND_LOOK_CLUE_IDS = {
    "taal-s-bridge-service-roster",
    "the-three-village-duty-roll",
    "the-reeves-refugee-road-tally",
    "morcant-s-recovery-cache-circuit",
    "voln-s-unfilled-tithe-convoy-board",
    "voln-s-stores-and-custody-ledger",
    "ren-s-canal-alarm-sequence",
    "ren-s-living-company-stand-down-roster",
    "the-recovery-tone-allotment-slate",
    "marr-s-canal-ward-roll",
    "drenn-s-gate-reinforcement-board",
    "the-freight-yard-receiving-marks",
    "voss-s-breakout-loading-table",
    "the-inner-keep-blood-service-table",
    "the-civil-continuity-docket",
}


@pytest.fixture(scope="module")
def vossgard_adventure() -> Adventure:
    """Load the authored campaign once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def vossgard_state() -> PlayState:
    """Load the Ash Warrant showcase journal once per module."""
    return load_play_state(EXAMPLE_STATE_PATH)


def test_vossgard_is_a_valid_eight_encounter_adventure(vossgard_adventure: Adventure) -> None:
    """Keep the offensive campaign aligned with its structural contract."""
    report = validate_adventure(vossgard_adventure)

    assert len(vossgard_adventure.encounters) == 8
    assert len(vossgard_adventure.revelations) == 12
    assert len(vossgard_adventure.clues) == 51
    assert report.is_valid
    assert report.edge_connectivity == 3


def test_vossgard_clue_density_is_irregular_and_independent(
    vossgard_adventure: Adventure,
) -> None:
    """Keep narrow conclusions focused and theater-wide systems broad."""
    clues_by_revelation = group_clues_by_revelation(vossgard_adventure.clues)
    clues_by_encounter = group_clues_by_encounter(vossgard_adventure.clues)

    revelation_counts = []
    for revelation in vossgard_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        revelation_counts.append(len(clues))
        assert len(clues) >= 3
        assert len({clue.source_encounter_id for clue in clues}) == len(clues)

    assert sorted(revelation_counts) == [3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 6, 8]
    assert {
        encounter.id: len(clues_by_encounter[encounter.id])
        for encounter in vossgard_adventure.encounters
    } == {
        "the-ashen-gate": 5,
        "the-iron-causeway": 6,
        "the-tithe-villages": 7,
        "the-thorn-barrows": 6,
        "the-red-abbey": 7,
        "the-black-bell-redoubt": 8,
        "the-drowned-sluice": 6,
        "vossgard": 6,
    }
    assert {clue.id for clue in vossgard_adventure.clues} >= SECOND_LOOK_CLUE_IDS


def test_vossgard_encounter_introductions_two_form_a_varied_offensive_sequence(
    vossgard_adventure: Adventure,
) -> None:
    """Protect the compressed openings, route discipline, and next stage."""
    encounters = vossgard_adventure.encounter_index()
    openings = [encounter.opening_view for encounter in vossgard_adventure.encounters]

    assert len(set(openings)) == 8
    assert sum(len(opening.split()) for opening in openings) == 580
    assert all(68 <= len(opening.split()) <= 81 for opening in openings)

    expected_phrases = {
        "the-ashen-gate": "Choose what reaches daylight first.",
        "the-iron-causeway": "The span is still whole; the surrender is not.",
        "the-tithe-villages": "the occupation\u2019s reputation",
        "the-thorn-barrows": "One horse returns without its rider.",
        "the-red-abbey": "Blood before baggage",
        "the-black-bell-redoubt": "It is weight descending toward the Warrant.",
        "the-drowned-sluice": "the chamber chooses a current",
        "vossgard": "take only the places earned for them",
    }
    for encounter_id, phrase in expected_phrases.items():
        assert phrase in encounters[encounter_id].opening_view


def test_vossgard_voice_one_returns_the_offensive_to_named_command(
    vossgard_adventure: Adventure,
) -> None:
    """Protect the source-level voice pass and its unchanged play surfaces."""
    bodies = "\n".join(encounter.content for encounter in vossgard_adventure.encounters)
    summaries = "\n".join(encounter.summary for encounter in vossgard_adventure.encounters)
    overview = "\n".join(
        (
            vossgard_adventure.synopsis,
            vossgard_adventure.premise,
            vossgard_adventure.explanation,
        )
    )

    assert "party" not in bodies.lower()
    assert "party" not in summaries.lower()
    assert "party" not in overview.lower()
    assert (
        sum(len(encounter.content.split()) for encounter in vossgard_adventure.encounters) == 9013
    )
    assert sum(len(encounter.summary.split()) for encounter in vossgard_adventure.encounters) == 111
    assert (
        sum(len(encounter.opening_view.split()) for encounter in vossgard_adventure.encounters)
        == 580
    )

    source = EXAMPLE_PATH.read_text(encoding="utf-8")
    assert "Settlement begins before the blood dries." in source
    assert "The Warrant reaches the redoubt between peals." in source
    assert "Allegiance follows roads, guards, receipts" in source
    assert "No fourth line can carry an organized remnant" in source


def test_vossgard_voice_two_finishes_the_packet_without_hidden_answer_reassurance(
    vossgard_adventure: Adventure,
) -> None:
    """Protect the final source finish, packet reconciliation, and next handoff."""
    source = EXAMPLE_PATH.read_text(encoding="utf-8")
    source_lower = source.lower()
    authored_prose = "\n".join(
        (
            vossgard_adventure.synopsis,
            vossgard_adventure.premise,
            vossgard_adventure.explanation,
            *(encounter.summary for encounter in vossgard_adventure.encounters),
            *(encounter.opening_view for encounter in vossgard_adventure.encounters),
            *(encounter.content for encounter in vossgard_adventure.encounters),
            *(revelation.title for revelation in vossgard_adventure.revelations),
            *(revelation.description for revelation in vossgard_adventure.revelations),
            *(clue.title for clue in vossgard_adventure.clues),
            *(clue.description for clue in vossgard_adventure.clues),
            *(clue.discovery for clue in vossgard_adventure.clues),
        )
    ).lower()

    assert not re.search(r"\bparty\b", authored_prose)
    for phrase in (
        "nothing important is concealed",
        "not a concealed third faction",
        "secret campaign information",
        "not a secret route",
        "secret route or hidden weakness",
        "not a hidden fourth route",
        "secretly possible",
        "undisclosed escape rule",
        "descriptive, not scores",
    ):
        assert phrase not in source_lower

    for phrase in (
        "The Ashen Gate's grey daylight prevents Voss",
        "Rusk plants the Warrant\u2019s blackened field plate",
        "It is weight descending toward the Warrant.",
        "the names below each flood mark",
        "turn a stand-down into an executable order",
        "that deployment fixes what the Compact can still intercept",
        "Use these outcomes to name the military and civil state",
    ):
        assert phrase in source

    assert (
        sum(len(encounter.content.split()) for encounter in vossgard_adventure.encounters) == 9013
    )
    assert (
        sum(len(encounter.opening_view.split()) for encounter in vossgard_adventure.encounters)
        == 580
    )


    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text(encoding="utf-8")
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")

    assert "## Second-look Voice I and II" in design
    assert "The victory rests on a battlefield" in playthrough


def test_vossgard_uses_the_planned_braided_offensive(vossgard_adventure: Adventure) -> None:
    """Prevent clue revisions from silently changing the campaign topology."""
    revelations = vossgard_adventure.revelation_index()
    edges = {
        frozenset((clue.source_encounter_id, target_id))
        for clue in vossgard_adventure.clues
        if (target_id := revelations[clue.revelation_id].unlocks_encounter_id) is not None
        and clue.source_encounter_id != target_id
    }

    assert len(edges) == 19
    assert {
        frozenset(("the-ashen-gate", "the-iron-causeway")),
        frozenset(("the-ashen-gate", "the-tithe-villages")),
        frozenset(("the-ashen-gate", "the-thorn-barrows")),
    } <= edges
    assert {
        frozenset(("the-red-abbey", "vossgard")),
        frozenset(("the-black-bell-redoubt", "vossgard")),
        frozenset(("the-drowned-sluice", "vossgard")),
    } <= edges


def test_vossgard_renders_complete_source_packet(vossgard_adventure: Adventure) -> None:
    """Keep the checked-in packet aligned with the authored source and journal."""
    report = validate_adventure(vossgard_adventure)
    state = load_play_state(EXAMPLE_STATE_PATH)
    documents = render_adventure_documents(vossgard_adventure, report, state)

    assert set(documents) >= {
        "00-overview.md",
        "01-encounter-index.md",
        "02-clue-list.md",
        "03-revelation-list.md",
        "04-validation-report.md",
        "05-play-summary.md",
    }
    assert len([name for name in documents if name.startswith("encounters/")]) == 8
    assert "Result: PASS" in documents["04-validation-report.md"]
    assert "Corrections recorded: 1" in documents["05-play-summary.md"]

    assert_rendered_documents_match(
        documents, EXAMPLE_DIRECTORY / "generated"
    )


def test_checked_in_vossgard_journal_exercises_campaign_consequences(
    vossgard_adventure: Adventure,
    vossgard_state: PlayState,
) -> None:
    """Keep the route, revisit, correction, bypass, and settlement stable."""
    projection = project_play_state(vossgard_adventure, vossgard_state)
    visited = tuple(visit.encounter_id for visit in projection.visits)
    progress = projection.revelation_progress_index()
    spotted = set(projection.spotted_clue_ids)

    assert len(vossgard_state.events) == 78
    assert visited == (
        "the-ashen-gate",
        "the-tithe-villages",
        "the-thorn-barrows",
        "the-black-bell-redoubt",
        "vossgard",
        "the-red-abbey",
        "vossgard",
    )
    assert all(
        progress[revelation.id].is_established for revelation in vossgard_adventure.revelations
    )
    assert set(projection.available_encounter_ids) == {
        encounter.id for encounter in vossgard_adventure.encounters
    }
    assert len(spotted) == 26
    assert {clue.id for clue in vossgard_adventure.clues} - spotted == (
        {
            clue.id
            for clue in vossgard_adventure.clues
            if clue.source_encounter_id in {"the-iron-causeway", "the-drowned-sluice"}
        }
        | SECOND_LOOK_CLUE_IDS
    )
    assert len(projection.corrections) == 1
    assert projection.corrections[0].target_operation_number == 14
    assert any(
        consequence.encounter_id == "the-iron-causeway"
        and "remains contained at the moment of victory" in consequence.text
        for consequence in projection.consequences
    )
    assert any(
        consequence.encounter_id == "the-drowned-sluice"
        and "bypassed Sluice exacts its cost" in consequence.text
        for consequence in projection.consequences
    )
    assert any(
        consequence.encounter_id == "vossgard" and "living garrison stands down" in consequence.text
        for consequence in projection.consequences
    )
    assert any(
        consequence.encounter_id == "vossgard"
        and "Holt commands the fortress overnight" in consequence.text
        for consequence in projection.consequences
    )


def test_vossgard_full_playthrough_narrates_the_fixed_decisions() -> None:
    """Keep the five-session account aligned with the event journal."""
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")

    required_text = [
        "Gate -> Villages -> Barrows -> Bell -> Vossgard -> Abbey -> Vossgard",
        "The first Vossgard operation will not attempt the inner keep",
        "The original report remains in the journal and is voided by a correction",
        "Session Five: The open exit",
        "Twenty-five authored clues remain unseen",
        "The canal has exacted the cost of being bypassed",
    ]

    assert all(text in playthrough for text in required_text)
    summary = render_play_summary(
        load_adventure(EXAMPLE_PATH),
        load_play_state(EXAMPLE_STATE_PATH),
    )
    assert "Visits recorded: 7" in summary
    assert "Corrections recorded: 1" in summary
    assert "Vossgard falls" in summary


def test_vossgard_coherence_protocol_is_explicit(vossgard_adventure: Adventure) -> None:
    """Keep the repaired authority, timing, and finale model in the source."""
    source = EXAMPLE_PATH.read_text(encoding="utf-8")
    gate = vossgard_adventure.encounter_index()["the-ashen-gate"].content
    fortress = vossgard_adventure.encounter_index()["vossgard"].content

    assert "Five lines wait beneath every field act" in gate
    assert "cannot grant permanent sovereignty" in gate
    assert "The opening council is turn zero" in gate
    assert "one surviving outer command for his primary" in gate
    assert "cannot reduce a position" in gate
    assert "Enforceable terms can split the living levies from the dead" in fortress
    assert "visible escape by mist, climbing, or a dominated mount" in fortress
    assert "### Broken flight" in fortress
    assert "`separate-living-levies`" not in source


def test_vossgard_source_remains_independent_of_demonstration_party() -> None:
    """Keep the named Ash Warrant subordinate to fresh-party play."""
    source = EXAMPLE_PATH.read_text(encoding="utf-8")

    assert all(
        name not in source for name in ("Lucan Vey", "Tala Marrick", "Sorin Halvek", "Maelin Rook")
    )
