"""Regression checks for the moving ecological adventure."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents, render_play_summary
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.journal_archive_store import load_journal_archive
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.integration.forest_support import assert_historical_archive_structure
from tests.support.corpus_contracts import assert_rendered_documents_match
from tests.support.corpus_contracts import group_clues_by_revelation

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-forest-that-carries-dawn")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"
EXAMPLE_ARCHIVE_PATH = (
    EXAMPLE_DIRECTORY / "archives" / "saltward-four-demonstrated-playthrough.journal.json"
)


@pytest.fixture(scope="module")
def forest_adventure() -> Adventure:
    """Load the current drafted source once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def forest_state() -> PlayState:
    """Load the canonical demonstration journal for the Forest example."""
    return load_play_state(EXAMPLE_STATE_PATH)


@pytest.fixture(scope="module")
def archived_forest_state() -> PlayState:
    """Load the immutable historical archive journal for the Forest example."""
    return load_journal_archive(EXAMPLE_ARCHIVE_PATH).play_state


def test_forest_foundation_preserves_the_moving_ecological_shape(
    forest_adventure: Adventure,
) -> None:
    """Protect the compact graph, single dawn finale, and valid resilient structure."""
    report = validate_adventure(forest_adventure)

    assert len(forest_adventure.encounters) == 10
    assert len(forest_adventure.revelations) == 18
    assert len(forest_adventure.clues) == 94
    assert forest_adventure.tags.genres == (
        "Wilderness exploration",
        "Survival",
        "Ecological fantasy",
    )
    assert forest_adventure.tags.game_systems == ("System-agnostic",)
    assert forest_adventure.tags.settings == ("Original fantasy",)
    assert (
        forest_adventure.tags.party_size_min,
        forest_adventure.tags.party_size_max,
    ) == (4, 6)
    assert forest_adventure.tags.level_min is None
    assert forest_adventure.tags.level_max is None
    assert forest_adventure.tags.combat_intensity == "none"
    assert forest_adventure.tags.keywords == (
        "Migrating forest",
        "Rescue",
        "Ecology",
        "Route finding",
        "Time pressure",
    )
    assert {encounter.id for encounter in forest_adventure.encounters if encounter.start} == {
        "camp-under-new-leaves"
    }
    assert {encounter.id for encounter in forest_adventure.encounters if encounter.end} == {
        "glass-verge"
    }
    assert all(encounter.required for encounter in forest_adventure.encounters)
    assert all(revelation.required for revelation in forest_adventure.revelations)
    assert report.is_valid
    assert report.edge_connectivity == 5
    assert not [issue for issue in report.issues if issue.severity == "error"]


def test_forest_clue_distribution_is_deliberately_uneven(
    forest_adventure: Adventure,
) -> None:
    """Keep redundancy tied to evidence density rather than an exact three-clue template."""
    clues_by_revelation = group_clues_by_revelation(forest_adventure.clues)

    support_counts = sorted(
        len(clues_by_revelation[revelation.id]) for revelation in forest_adventure.revelations
    )
    assert support_counts == [
        3,
        3,
        4,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        6,
        6,
        6,
        6,
        6,
        7,
        7,
    ]
    for revelation in forest_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        assert len({clue.source_encounter_id for clue in clues}) == len(clues)

    source_counts = Counter(clue.source_encounter_id for clue in forest_adventure.clues)
    assert min(source_counts.values()) == 7
    assert max(source_counts.values()) == 11
    assert len(set(source_counts.values())) >= 5


def test_forest_separates_stable_discovery_from_moving_routes(
    forest_adventure: Adventure,
) -> None:
    """Protect the migration-stage model and the non-sovereign ecological premise."""
    explanation = forest_adventure.explanation
    encounter_index = forest_adventure.encounter_index()

    assert "The forest is not one mind" in explanation
    assert "Long Shade, Red Dusk, Root Night, and Glass Dawn" in explanation
    assert "Knowing a region exists does not guarantee a safe current route" in explanation
    assert "## Why the party is sent" in encounter_index["camp-under-new-leaves"].content
    assert "## The damaged soil route" in encounter_index["wagons-in-the-forked-roots"].content
    assert "## Testing a repair" in encounter_index["soilbearer-road"].content
    assert (
        "Display accumulated state rather than presenting a menu"
        in encounter_index["glass-verge"].content
    )


def test_forest_rain_seed_remains_a_constructive_convergence(
    forest_adventure: Adventure,
) -> None:
    """Keep the rain-seed dependent on six living relationships and a repair-created surplus."""
    revelation_index = forest_adventure.revelation_index()

    convergence = revelation_index[
        "a-viable-rain-seed-is-assembled-by-convergence-not-picked-from-one-tree"
    ]
    surplus = revelation_index[
        "the-forest-can-spare-one-mature-seed-if-the-broken-soil-route-is-restored"
    ]

    assert "living old soil" in convergence.description
    assert "captured dawn" in convergence.description
    assert "circulating rain" in convergence.description
    assert "blackgrass heat" in convergence.description
    assert "several maturing knots" in surplus.description
    assert "forest's own continuation" in surplus.description


def test_forest_generated_packet_matches_the_canonical_source(
    forest_adventure: Adventure,
) -> None:
    """Keep disposable rendered documents reproducible from the authored JSON."""
    report = validate_adventure(forest_adventure)
    rendered = render_adventure_documents(forest_adventure, report)

    assert_rendered_documents_match(
        rendered, EXAMPLE_DIRECTORY / "generated"
    )


def test_forest_session_two_fixes_the_exact_rescue_roster(
    forest_adventure: Adventure,
) -> None:
    """Protect the forty-two names and the opening knowledge/location distinction."""
    ledger = (EXAMPLE_DIRECTORY / "CARAVAN-AND-RESCUE-LEDGER.md").read_text()
    roster_rows = [
        line for line in ledger.splitlines() if line.startswith("| ") and line[2:4].isdigit()
    ]

    assert len(roster_rows) == 42
    assert len({row.split("|")[1].strip() for row in roster_rows}) == 42
    assert sum("| Camp | Present and able |" in row for row in roster_rows) == 27
    assert sum("| Camp | Present and injured |" in row for row in roster_rows) == 2
    assert sum("| Heard but unreached |" in row for row in roster_rows) == 4
    assert sum("| Believed with " in row for row in roster_rows) == 6
    assert sum("| Missing without location |" in row for row in roster_rows) == 3

    assert "Clove and Sedge" in ledger
    assert "Bell and Crook" in ledger
    assert "Moth and Reed" in ledger


def test_forest_session_two_makes_rescue_procedural_and_failure_forward(
    forest_adventure: Adventure,
) -> None:
    """Keep rescue, consent, property, and stage pressure concrete at the table."""
    encounter_index = forest_adventure.encounter_index()
    camp = encounter_index["camp-under-new-leaves"].content
    wagons = encounter_index["wagons-in-the-forked-roots"].content
    soil = encounter_index["soilbearer-road"].content
    ledger = (EXAMPLE_DIRECTORY / "CARAVAN-AND-RESCUE-LEDGER.md").read_text()

    assert "## Camp operating sequence" in camp
    assert "## Pocket pressures" in wagons
    assert "## Running a rescue operation" in wagons
    assert "A weak result should impose a consequence that follows from the method" in wagons
    assert (
        "Immediate life-saving necessity and speculative seed work are not the same authority"
        in soil
    )
    assert "## Emergency use of property" in ledger
    assert "## Reports and informed departure" in ledger

    for name in (
        "Orra Venn",
        "Hessa Clay",
        "Nahl Reed",
        "Pelen Marr",
        "Sio Tern",
        "Jun Alder",
    ):
        assert f"### {name}" in ledger


def test_forest_session_three_operationalizes_the_first_three_currents(
    forest_adventure: Adventure,
) -> None:
    """Keep soil, captured dawn, and circulating rain distinct and procedural."""
    encounter_index = forest_adventure.encounter_index()
    soil = encounter_index["soilbearer-road"].content
    lantern = encounter_index["lantern-canopy"].content
    rain = encounter_index["warm-rain-basins"].content
    sheet = (EXAMPLE_DIRECTORY / "ECOLOGY-OPERATING-SHEET.md").read_text()

    for heading in (
        "## The operating rule",
        "## Current states",
        "## The six currents",
        "## Observation procedure",
        "## Experiment procedure",
        "## Taking, borrowing, spending, and returning",
        "## Cross-current effects",
    ):
        assert heading in sheet

    for state in ("Absent", "Weak", "Working", "Strong"):
        assert f"| {state} |" in sheet

    assert "## Testing a repair" in soil
    assert "### Copper scent-rill" in soil
    assert "### Hand ferry and gate crew" in soil
    assert "## Fire preparation" in soil
    assert "## Results and later options" in soil

    assert "### Severed and living light" in lantern
    assert "### Rehang an intact cup" in lantern
    assert "### Build a wet pollen bridge" in lantern
    assert "## Damage and repair states" in lantern
    assert "Ordinary reflected light does not replace stored dawn" in lantern

    assert "### Measured drinking test" in rain
    assert "## Water for the caravan" in rain
    assert "## Recovery of Moth and Reed" in rain
    assert "### Copper circulation loop" in rain
    assert "### Capillary bypass" in rain
    assert "## Contamination and repair" in rain


def test_forest_session_three_tracks_persistent_cost_and_later_options(
    forest_adventure: Adventure,
) -> None:
    """Protect the distinction between borrowing, spending, fouling, and repair."""
    encounter_index = forest_adventure.encounter_index()
    source_text = "\n".join(
        encounter_index[encounter_id].content
        for encounter_id in ("soilbearer-road", "lantern-canopy", "warm-rain-basins")
    )
    migration = (EXAMPLE_DIRECTORY / "MIGRATION-LEDGER.md").read_text()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()

    assert "**Borrow:**" in (EXAMPLE_DIRECTORY / "ECOLOGY-OPERATING-SHEET.md").read_text()
    assert "**Spend:**" in (EXAMPLE_DIRECTORY / "ECOLOGY-OPERATING-SHEET.md").read_text()
    assert "**Foul:**" in (EXAMPLE_DIRECTORY / "ECOLOGY-OPERATING-SHEET.md").read_text()
    assert source_text.count("Persistent cost") >= 12
    assert source_text.count("Later option") >= 12
    assert "A strong current supplies one concrete redundancy" in migration
    assert (
        "Record ecological currents as **absent**, **weak**, **working**, or **strong**"
        in migration
    )
    assert "## Currents are relationships, not inventory" in design
    assert (
        "It cannot replace an absent soil, light, water, heat, memory, or pulse relationship"
        in design
    )


def test_forest_session_four_keeps_voice_memory_material_and_bounded(
    forest_adventure: Adventure,
) -> None:
    """Protect river-course selection without treating fungal echoes as whole persons."""
    encounter_index = forest_adventure.encounter_index()
    hollow = encounter_index["hollow-of-kept-voices"].content
    sheet = (EXAMPLE_DIRECTORY / "MEMORY-FIRE-AND-BREATH.md").read_text()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()

    for heading in (
        "## What the cords retain",
        "## Testing whether a voice is a person",
        "## Choosing a river course",
        "### Living braid",
        "### Wet transcription",
        "## Current states",
    ):
        assert heading in hollow

    for relation in ("Fall", "Storage", "Ground", "Overflow", "Interval"):
        assert f"| {relation} |" in hollow

    assert "the fragment cannot consent" in hollow
    assert "The copy does not itself supply the living memory current" in hollow
    assert "## Preserved voice is evidence, not surviving authority" in design
    assert "## Remembered river course" in sheet
    assert "Names and relationships drift. Measurements persist." in sheet


def test_forest_session_four_separates_bounded_heat_from_runaway_fire(
    forest_adventure: Adventure,
) -> None:
    """Keep necessary fire procedural, dangerous, and distinct from excess flame."""
    burn = forest_adventure.encounter_index()["blackgrass-burn"].content
    sheet = (EXAMPLE_DIRECTORY / "MEMORY-FIRE-AND-BREATH.md").read_text()

    for heading in (
        "## Reading the front",
        "## The three burn segments",
        "### Wagon scar",
        "### Restored corridor",
        "### Crownward seam",
        "## Preparing a bounded corridor",
        "## Running the burn",
        "## Current and hazard states",
    ):
        assert heading in burn

    assert "Two independent margins" in burn
    assert "A runaway fire is not a strong current" in burn
    assert burn.count("Persistent cost") >= 6
    assert burn.count("Later option") >= 6
    assert "## Bounded blackgrass heat" in sheet
    assert "A runaway fire is tracked separately" in sheet


def test_forest_session_four_makes_root_breath_readable_and_unique(
    forest_adventure: Adventure,
) -> None:
    """Protect the Bearer as observable physiology with one nonrepeatable deep exhale."""
    chamber = forest_adventure.encounter_index()["root-breath-chamber"].content
    sheet = (EXAMPLE_DIRECTORY / "MEMORY-FIRE-AND-BREATH.md").read_text()
    migration = (EXAMPLE_DIRECTORY / "MIGRATION-LEDGER.md").read_text()

    for heading in (
        "## Four beats under load",
        "## Reading the cycle",
        "## Burden map",
        "## Correcting burdens",
        "## Preliminary breath",
        "## Limited redirection",
        "## The deep exhale",
        "## Root-pulse current states",
    ):
        assert heading in chamber

    for phase in (
        "Traction pulse",
        "Venting rise",
        "Long central exhale",
        "Inward draw and hardening",
    ):
        assert f"| {phase} |" in chamber

    for band in ("Western carry band", "Middle circulation band", "Crownward lift band"):
        assert f"| {band} |" in chamber

    assert "It cannot safely release a mature seed" in chamber
    assert "The long central exhale occurs once during Root Night" in chamber
    assert "The beat accommodates physiology. It neither speaks for the Bearer" in chamber
    assert "## Bearer's root pulse" in sheet
    assert "unique deep exhale" in migration


def test_forest_session_five_makes_crown_assembly_diagnostic_and_procedural(
    forest_adventure: Adventure,
) -> None:
    """Protect the six-current receiver logic and distinct knot states."""
    crown = forest_adventure.encounter_index()["crown-of-unfallen-rain"].content
    sheet = (EXAMPLE_DIRECTORY / "CROWN-VERGE-OPERATING-SHEET.md").read_text()

    for heading in (
        "## Reading an unfinished knot",
        "## Knot states",
        "## The crown sequence",
        "### 1. Descend and diagnose",
        "### 2. Choose a receiver",
        "### 3. Complete the living paths",
        "### 4. Close one crown circuit",
        "## Separating a seed",
        "### Clean physical separation",
        "### Ecologically defensible separation",
        "## Failure-forward consequences",
    ):
        assert heading in crown

    for state in (
        "Empty shell",
        "Stormglass knot",
        "Viable knot",
        "Mature knot",
        "Surplus crown",
    ):
        assert f"| {state} |" in crown

    for defect in (
        "Living old soil",
        "Captured dawn",
        "Circulating rain",
        "Remembered river course",
        "Bounded blackgrass heat",
        "Bearer root pulse",
    ):
        assert f"| {defect} |" in crown

    assert "A rain circuit is not working merely because the knot becomes wet" in crown
    assert "Do not demand six separate random successes" in crown
    assert "## One complete crown circuit" in sheet


def test_forest_session_five_separates_clean_release_from_demonstrated_surplus(
    forest_adventure: Adventure,
) -> None:
    """Keep technical separation and ecological justification as distinct claims."""
    crown = forest_adventure.encounter_index()["crown-of-unfallen-rain"].content
    sheet = (EXAMPLE_DIRECTORY / "CROWN-VERGE-OPERATING-SHEET.md").read_text()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()

    for requirement in (
        "the selected knot is mature",
        "its water has completed a return after the coat opened",
        "a wet cradle or equivalent support already bears its weight",
        "at least three independent deep-exhale cues have appeared",
        "the party draws the slack feeder ring free before the inward draw hardens it",
    ):
        assert requirement in crown

    assert "at least one other mature knot remains attached" in crown
    assert "A sole mature seed can still be taken cleanly" in sheet
    assert "Clean separation and justified taking are different claims" in design
    assert "A clean socket proves that the crown was not torn during removal" in design


def test_forest_session_five_runs_glass_dawn_through_routes_and_visible_signals(
    forest_adventure: Adventure,
) -> None:
    """Protect route capacities, parallel operations, and plural departure consent."""
    verge = forest_adventure.encounter_index()["glass-verge"].content
    sheet = (EXAMPLE_DIRECTORY / "CROWN-VERGE-OPERATING-SHEET.md").read_text()
    migration = (EXAMPLE_DIRECTORY / "MIGRATION-LEDGER.md").read_text()

    for heading in (
        "## Three roads before the salt closes",
        "## The dawn signals",
        "### First reflection",
        "### Deep exhale",
        "### Inward draw",
        "### Direct sun",
        "## Departure muster",
        "## Running the finale in parallel",
        "## Principal positions at the verge",
        "## Failure-forward departures",
        "## Final record",
    ):
        assert heading in verge

    for route in ("Broad salt shelf", "Wet middle ledge", "Crown service root"):
        assert f"| {route} |" in verge

    assert "Do not merge distinct choices into “the caravan decided.”" in sheet
    assert "The crown and verge should normally be active at the same time" in verge
    assert "Silence, absence, injury, youth, dependency, and admiration are not consent" in verge
    assert "## Root Night and Glass Dawn sequence" in migration


def test_forest_session_five_preserves_distinct_immediate_and_seasonal_outcomes(
    forest_adventure: Adventure,
) -> None:
    """Keep seed physiology, Merewash establishment, forest cost, and eastbound play explicit."""
    aftermath = (EXAMPLE_DIRECTORY / "AFTERMATH-AND-SEASONAL-STATES.md").read_text()

    for heading in (
        "## Immediate aftermath: the first day",
        "### West of the verge",
        "### A carried rain-seed",
        "### The forest east of the verge",
        "## Seed condition states",
        "### Mature surplus seed",
        "### Mature sole seed",
        "### Stormglass seed",
        "### Torn seed",
        "### No seed taken",
        "## Establishing a viable seed at Merewash",
        "## Seasonal development at Merewash",
        "### First seven days",
        "### First month",
        "### First wet season",
        "### First following dry season",
        "### Third year",
        "## Eastbound aftermath",
        "## Immediate outcome combinations",
        "## Final campaign record",
    ):
        assert heading in aftermath

    assert "It does not immediately end a six-year drought across the whole valley" in aftermath
    assert "A group that escaped without a seed still achieved a real rescue" in aftermath
    assert "People still aboard have not automatically died" not in aftermath
    assert "They are exposed and cut off, not automatically dead" in aftermath
    assert "Do not summarize these as “good,” “mixed,” or “bad.”" in aftermath


def test_forest_session_six_stress_tests_uneven_support_across_routes(
    forest_adventure: Adventure,
) -> None:
    """Keep nonlinear routes robust without forcing complete seed knowledge on rescue play."""
    clues_by_revelation = group_clues_by_revelation(forest_adventure.clues)

    compact_route = {
        "camp-under-new-leaves",
        "wagons-in-the-forked-roots",
        "soilbearer-road",
        "warm-rain-basins",
        "root-breath-chamber",
        "crown-of-unfallen-rain",
        "glass-verge",
    }
    compact_support = {
        revelation.id: sum(
            clue.source_encounter_id in compact_route for clue in clues_by_revelation[revelation.id]
        )
        for revelation in forest_adventure.revelations
    }

    assert min(compact_support.values()) == 2
    assert sum(count >= 3 for count in compact_support.values()) == 16
    assert {revelation_id for revelation_id, count in compact_support.items() if count == 2} == {
        "the-blackgrass-burn-is-moving-toward-the-old-scar",
        "the-rain-crown-forms-where-six-currents-meet",
    }

    rescue_route = {
        "camp-under-new-leaves",
        "wagons-in-the-forked-roots",
        "glass-verge",
    }
    rescue_support = {
        revelation.id: sum(
            clue.source_encounter_id in rescue_route for clue in clues_by_revelation[revelation.id]
        )
        for revelation in forest_adventure.revelations
    }
    assert {revelation_id for revelation_id, count in rescue_support.items() if count == 0} == {
        "the-rain-crown-forms-where-six-currents-meet",
        "the-warm-basins-circulate-rain-and-cannot-be-safely-drained",
    }
    assert sum(count == 1 for count in rescue_support.values()) == 6
    assert sum(count == 2 for count in rescue_support.values()) == 8
    assert sum(count >= 3 for count in rescue_support.values()) == 2


def test_forest_session_six_separates_access_knowledge_and_mobile_evidence(
    forest_adventure: Adventure,
) -> None:
    """Protect late access, source attribution, and missed-window limits."""
    sheet = (EXAMPLE_DIRECTORY / "GM-OPERATING-SHEET.md").read_text()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    migration = (EXAMPLE_DIRECTORY / "MIGRATION-LEDGER.md").read_text()

    for heading in (
        "## Migration-turn loop",
        "## Stage card",
        "## Physical access shorthand",
        "## Uneven-clue rule",
        "## Mobile evidence quick reference",
        "## Split-party board",
        "## Failure-forward ladder",
        "## Glass Dawn sequence",
    ):
        assert heading in sheet


    for encounter in forest_adventure.encounters:
        assert "## Late" in encounter.content

    assert (
        "The Bearer does not provide a second clean-separation exhale"
        in forest_adventure.encounter_index()["root-breath-chamber"].content
    )
    assert "## Discovery persists; access does not" in design
    assert "## Uneven support is allowed to produce uneven knowledge" in design
    assert "## Discovery, access, and mobile carriers" in migration
    assert "Use four access states beside each region" in migration


def test_forest_session_seven_uses_four_people_already_in_the_fixed_roster() -> None:
    """Prevent the demonstration party from silently increasing the caravan count."""
    party = (EXAMPLE_DIRECTORY / "PARTY-DESIGN.md").read_text()
    ledger = (EXAMPLE_DIRECTORY / "CARAVAN-AND-RESCUE-LEDGER.md").read_text()

    assert "# Party Design: The Saltward Four" in party
    for name in ("Ansel Roe", "Shai Moss", "Kesh Rill", "Len Orf"):
        assert f"## {name}" in party
        assert f"| {name} |" in ledger
    assert "This choice preserves the fixed forty-two-person opening count" in party


def test_forest_session_seven_demonstrates_the_complete_moving_route(
    forest_adventure: Adventure,
    forest_state: PlayState,
    archived_forest_state: PlayState,
) -> None:
    """Keep sessions, visits, uneven discovery, and the demonstrated ending aligned."""
    projection = project_play_state(forest_adventure, forest_state)

    assert archived_forest_state == forest_state
    assert len(forest_state.events) == 196
    assert len(projection.sessions) == 4
    assert projection.active_session_number is None
    assert tuple(session.title for session in projection.sessions) == (
        "Thirteen Names Beyond the Roots",
        "Water That Climbs",
        "One Long Breath",
        "The Last Salt",
    )
    assert tuple(visit.encounter_id for visit in projection.visits) == (
        "camp-under-new-leaves",
        "wagons-in-the-forked-roots",
        "soilbearer-road",
        "lantern-canopy",
        "warm-rain-basins",
        "hollow-of-kept-voices",
        "blackgrass-burn",
        "root-breath-chamber",
        "crown-of-unfallen-rain",
        "glass-verge",
    )
    assert len(projection.spotted_clue_ids) == 74
    assert sum(len(item.missed_visit_numbers) for item in projection.clue_progress) == 15
    assert all(item.is_established for item in projection.revelation_progress)
    assert len(projection.consequences) == 36
    assert not projection.corrections

    consequences = "\n".join(item.text for item in projection.consequences)
    assert "All forty-two people are accounted for: forty westbound, two eastbound" in consequences
    assert "One mature surplus seed separates with a smooth living socket" in consequences
    assert "one mature knot attached, one viable knot" in consequences
    assert "Runaway fire" not in consequences or "no runaway fire" in consequences.lower()


def test_forest_session_seven_play_summary_and_archive_are_reproducible(
    forest_adventure: Adventure,
    forest_state: PlayState,
) -> None:
    """Keep the generated summary and pre-tag archive synchronized with source and journal."""
    summary = render_play_summary(forest_adventure, forest_state)
    archived = load_journal_archive(EXAMPLE_ARCHIVE_PATH)

    assert summary == (EXAMPLE_DIRECTORY / "generated" / "05-play-summary.md").read_text()
    assert "Events recorded: 196" in summary
    assert "Explicit sessions: 4" in summary
    assert "Visits recorded: 10" in summary
    assert "Unique leads found: 74 / 94" in summary
    assert "The Saltward Four" in summary
    assert archived.event_count == 196
    assert_historical_archive_structure(archived.adventure_snapshot, forest_adventure)
    assert archived.play_state == forest_state


def test_forest_session_seven_completion_packet_is_present_and_consistent() -> None:
    """Protect the playthrough, demonstrated aftermath, audit, and pending voice disposition."""
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()
    aftermath = (EXAMPLE_DIRECTORY / "AFTERMATH-AND-SEASONAL-STATES.md").read_text()

    assert "# Full Playthrough: The Saltward Four" in playthrough
    assert "## Session One: Thirteen Names Beyond the Roots" in playthrough
    assert "## Session Four: The Last Salt" in playthrough
    assert "Forty people reach the western White Salt alive" in playthrough
    assert "Sio Tern and Jun Alder continue east" in playthrough
    assert "## Demonstrated outcome: the Saltward Four" in aftermath


def test_forest_session_eight_completes_the_voice_and_coherence_pass(
    forest_adventure: Adventure,
    forest_state: PlayState,
) -> None:
    """Protect the final prose pass without allowing structural or journal drift."""
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()

    assert "## Governing voice standard" in design
    for phrase in (
        "Soilbearers **carry** old ground",
        "Lantern flowers **lend** dawn",
        "Warm basins **send and receive** water",
        "Fungal cords **keep measures**",
        "The Bearer **bears, cools, strains, vents, and exhales**",
    ):
        assert phrase in design

    assert "This is one demonstrated night through *The Forest That Carries Dawn*" in playthrough
    assert "Glass Dawn reveals the shape already made" in playthrough

    encounter_index = forest_adventure.encounter_index()
    assert (
        "Bring me news while it is still true"
        in encounter_index["camp-under-new-leaves"].opening_view
    )
    assert "Severed dawn has no road" in {clue.title for clue in forest_adventure.clues}
    assert (
        forest_adventure.revelation_index()[
            "a-viable-rain-seed-is-assembled-by-convergence-not-picked-from-one-tree"
        ].title
        == "A rain-seed is made where six paths meet"
    )
    assert "None of these responses is consent" in forest_adventure.explanation

    projection = project_play_state(forest_adventure, forest_state)
    assert len(forest_state.events) == 196
    assert len(projection.spotted_clue_ids) == 74
    assert sum(len(item.missed_visit_numbers) for item in projection.clue_progress) == 15
    assert len(projection.consequences) == 36


def test_forest_second_look_reconciles_fresh_play_and_later_authority(
    forest_adventure: Adventure,
    forest_state: PlayState,
) -> None:
    """Keep roster arithmetic, record provenance, and the work muster coherent."""
    camp = forest_adventure.encounter_index()["camp-under-new-leaves"].content
    lantern = forest_adventure.encounter_index()["lantern-canopy"].content
    chamber = forest_adventure.encounter_index()["root-breath-chamber"].content
    ledger = (EXAMPLE_DIRECTORY / "CARAVAN-AND-RESCUE-LEDGER.md").read_text()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()

    assert "one group among its forty-two named travelers" in forest_adventure.premise
    assert "occupy or replace an equal number of present-and-able roster entries" in camp
    for sample_name in ("Ansel Roe", "Shai Moss", "Kesh Rill", "Len Orf", "Saltward Four"):
        assert sample_name not in camp
    assert "## Renewing the commission" in camp
    assert "work muster rather than a binding vote" in camp
    assert "Name one route recorder" in camp
    assert "Name one property recorder" in camp
    assert "Ansel Roe" not in camp
    assert "Len Orf" not in camp
    assert "Shai Moss" not in lantern
    assert "The route recorder" in chamber
    assert "## Fresh-play party setup" in ledger
    assert "## Fresh-party roster rule" in design
    assert "## Why the old records are present" in design
    assert "## The commission can widen without becoming command" in design
    assert len(forest_adventure.encounters) == 10
    assert len(forest_adventure.revelations) == 18
    assert len(forest_adventure.clues) == 94
    assert len(forest_state.events) == 196


def test_forest_second_look_preserves_irregular_density_while_recording_local_tests(
    forest_adventure: Adventure,
    forest_state: PlayState,
) -> None:
    """Protect the five local additions without flattening the ecological matrix."""
    clue_index = forest_adventure.clue_index()
    encounter_index = forest_adventure.encounter_index()

    expected = {
        "oil-gives-the-fire-another-road": (
            "wagons-in-the-forked-roots",
            "blackgrass-fire-opens-the-seed-coat-and-renews-the-migration-corridor",
        ),
        "returned-water-holds-the-boundary": (
            "blackgrass-burn",
            "the-warm-basins-circulate-rain-and-cannot-be-safely-drained",
        ),
        "the-basin-answers-the-cloud": (
            "crown-of-unfallen-rain",
            "the-warm-basins-circulate-rain-and-cannot-be-safely-drained",
        ),
        "mirror-light-does-not-wake-a-dark-knot": (
            "glass-verge",
            "lantern-flowers-lend-captured-dawn-to-the-rain-seed",
        ),
        "one-cloud-leaves-one-cloud-travels": (
            "glass-verge",
            "the-forest-can-spare-one-mature-seed-if-the-broken-soil-route-is-restored",
        ),
    }
    assert set(expected) <= set(clue_index)
    for clue_id, (source_id, revelation_id) in expected.items():
        clue = clue_index[clue_id]
        assert clue.source_encounter_id == source_id
        assert clue.revelation_id == revelation_id

    assert "spice-oil stripe" in encounter_index["wagons-in-the-forked-roots"].content
    assert "steams dry" in encounter_index["blackgrass-burn"].content
    assert "remains dark in the glare" in encounter_index["glass-verge"].content
    assert len(forest_state.events) == 196
