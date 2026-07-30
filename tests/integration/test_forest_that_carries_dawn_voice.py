"""Regression checks for the Forest second-look voice passes."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.journal_archive_store import load_journal_archive
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.integration.forest_support import assert_historical_archive_structure

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-forest-that-carries-dawn")


def test_forest_voice_i_trusts_material_processes_without_changing_play() -> None:
    """Protect the source-level voice pass and its fresh-play invariants."""
    adventure = load_adventure(EXAMPLE_DIRECTORY / "adventure.json")
    state = load_play_state(EXAMPLE_DIRECTORY / "play-state.example.json")
    archive = load_journal_archive(
        EXAMPLE_DIRECTORY / "archives" / "saltward-four-demonstrated-playthrough.journal.json"
    )
    encounters = adventure.encounter_index()

    measured_source = "\n".join(
        (
            adventure.synopsis,
            adventure.premise,
            adventure.explanation,
            *(encounter.summary for encounter in adventure.encounters),
            *(encounter.content for encounter in adventure.encounters),
        )
    )
    assert len(re.findall(r"\bthe party\b", measured_source, re.IGNORECASE)) == 15
    assert "The Bearer bears, cools, strains, vents, and exhales" in adventure.explanation
    assert (
        "Authority for seed work comes from named volunteers"
        in encounters["camp-under-new-leaves"].content
    )
    assert (
        "Before committing material, answer five questions" in encounters["soilbearer-road"].content
    )
    assert "The flowers thank, accuse, and authorize no one" in encounters["lantern-canopy"].content
    assert (
        "Name the proposal by what happens to the water" in encounters["warm-rain-basins"].content
    )
    assert "preserved subject" in encounters["hollow-of-kept-voices"].content
    assert "Let failure follow the method" in encounters["blackgrass-burn"].content
    assert "Physiology grants no permission" in encounters["root-breath-chamber"].content
    assert "Keep the crown an honest receiver" in encounters["crown-of-unfallen-rain"].content
    assert "Keep distinct people from disappearing inside" in encounters["glass-verge"].content


    assert sum(len(encounter.opening_view.split()) for encounter in adventure.encounters) == 620
    assert len(adventure.encounters) == 10
    assert len(adventure.revelations) == 18
    assert len(adventure.clues) == 94
    assert_historical_archive_structure(archive.adventure_snapshot, adventure)
    assert archive.play_state == state
    assert len(state.events) == 196
    for sample_name in ("Ansel Roe", "Shai Moss", "Kesh Rill", "Len Orf", "Saltward Four"):
        assert sample_name not in measured_source


def test_forest_voice_ii_reconciles_the_complete_packet() -> None:
    """Protect the final cadence pass, current records, and subordinate demonstration."""
    adventure = load_adventure(EXAMPLE_DIRECTORY / "adventure.json")
    state = load_play_state(EXAMPLE_DIRECTORY / "play-state.example.json")
    archive = load_journal_archive(
        EXAMPLE_DIRECTORY / "archives" / "saltward-four-demonstrated-playthrough.journal.json"
    )
    encounters = adventure.encounter_index()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()

    assert "Advance the stage when the forest moves" in encounters["camp-under-new-leaves"].content
    assert (
        "Drawn gradually through the connected spillway" in encounters["warm-rain-basins"].content
    )
    assert "A mistaken choice alters the course" in encounters["hollow-of-kept-voices"].content
    assert (
        "Record the changed state without grading the choice"
        in encounters["blackgrass-burn"].content
    )
    assert "The beat accommodates physiology" in encounters["root-breath-chamber"].content
    assert "absent paths stay absent" in encounters["crown-of-unfallen-rain"].content
    assert (
        "That proves surplus, not permission; the Glass Waste remains unmeasured."
        in encounters["crown-of-unfallen-rain"].content
    )
    assert (
        "People still aboard enter a hotter, faster migration" in encounters["glass-verge"].content
    )
    assert "Show it before heavy departure closes" in encounters["glass-verge"].content
    assert "the GM has counted enough rolls" not in encounters["camp-under-new-leaves"].content
    assert "for the sake of a climax" not in encounters["crown-of-unfallen-rain"].content

    assert "stable encounter-and-clue structure" in design
    assert "State leaving the node" not in playthrough
    assert "The party" not in playthrough
    assert "the party's" not in playthrough
    assert "Their identities and specialties belong to this demonstration only" in playthrough

    assert len(adventure.encounters) == 10
    assert len(adventure.revelations) == 18
    assert len(adventure.clues) == 94
    assert sum(len(encounter.opening_view.split()) for encounter in adventure.encounters) == 620
    assert_historical_archive_structure(archive.adventure_snapshot, adventure)
    assert archive.play_state == state
    assert len(state.events) == 196


def test_forest_second_look_openings_form_one_ecological_progression() -> None:
    """Protect both introduction passes without turning living paths into answers."""
    adventure = load_adventure(EXAMPLE_DIRECTORY / "adventure.json")
    state = load_play_state(EXAMPLE_DIRECTORY / "play-state.example.json")
    expected_fragments = (
        "Hessa Clay calls thirteen names",
        "The road is no road until the beetles arrive.",
        "he answers with the depth of a well",
        "blue flame leaps sideways into spilled spice",
        "A wagon bell stops midway through a swing.",
        "Each name answers west, east, or not yet.",
    )
    openings = [encounter.opening_view for encounter in adventure.encounters]
    assert len(openings) == len(set(openings)) == 10
    combined_openings = "\n".join(openings)
    assert all(fragment in combined_openings for fragment in expected_fragments)
    assert all(59 <= len(opening.split()) <= 65 for opening in openings)
    assert sum(len(opening.split()) for opening in openings) == 620

    assert len(state.events) == 196
