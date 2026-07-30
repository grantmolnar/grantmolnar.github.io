"""Regression checks for the Bramblewick traditional whodunnit."""

from collections import Counter, defaultdict
from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents, render_play_summary
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.corpus_contracts import assert_rendered_documents_match
from tests.support.corpus_contracts import group_clues_by_revelation

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-last-bell-of-bramblewick")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"
EXAMPLE_PLAYTHROUGH_PATH = EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md"
EXAMPLE_PARTY_PATH = EXAMPLE_DIRECTORY / "PARTY-DESIGN.md"
EXAMPLE_QUICKSTART_PATH = EXAMPLE_DIRECTORY / "GM-QUICKSTART.md"


@pytest.fixture(scope="module")
def bramblewick_adventure() -> Adventure:
    """Load the completed whodunnit once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def bramblewick_state() -> PlayState:
    """Load the Lantern Measure showcase journal once per module."""
    return load_play_state(EXAMPLE_STATE_PATH)


def test_bramblewick_is_a_valid_eleven_encounter_whodunnit(
    bramblewick_adventure: Adventure,
) -> None:
    """Keep the completed mystery aligned with its structural contract."""
    report = validate_adventure(bramblewick_adventure)

    assert len(bramblewick_adventure.encounters) == 11
    assert len(bramblewick_adventure.revelations) == 26
    assert len(bramblewick_adventure.clues) == 123
    assert {
        encounter.id for encounter in bramblewick_adventure.encounters if not encounter.required
    } == {
        "moss-apothecary",
        "bramble-mill",
    }
    assert sum(revelation.required for revelation in bramblewick_adventure.revelations) == 17
    assert report.is_valid
    assert report.edge_connectivity == 3


def test_bramblewick_uses_functional_irregular_clue_density(
    bramblewick_adventure: Adventure,
) -> None:
    """Prevent later cleanup from flattening the mystery's clue distribution."""
    clue_counts = Counter(clue.source_encounter_id for clue in bramblewick_adventure.clues)

    assert min(clue_counts.values()) == 7
    assert max(clue_counts.values()) == 18
    assert len(set(clue_counts.values())) == 8
    assert clue_counts == {
        "hearth-hall-and-the-map-room": 18,
        "merrit-alder-s-burrow": 16,
        "the-copper-kettle-and-long-pantry": 15,
        "moss-apothecary": 11,
        "alder-orchard": 8,
        "bramble-mill": 8,
        "the-common-chest": 10,
        "chapel-of-the-open-door": 7,
        "bramblewick-school": 13,
        "the-north-hedge": 10,
        "the-first-bell-moot": 7,
    }


def test_bramblewick_uses_functional_irregular_encounter_connectivity(
    bramblewick_adventure: Adventure,
) -> None:
    """Keep focused scenes peripheral while preserving dense investigative hubs."""
    revelation_targets = {
        revelation.id: revelation.unlocks_encounter_id
        for revelation in bramblewick_adventure.revelations
    }
    edges = {
        tuple(sorted((clue.source_encounter_id, target)))
        for clue in bramblewick_adventure.clues
        if (target := revelation_targets[clue.revelation_id]) is not None
        and target != clue.source_encounter_id
    }
    degrees = Counter(vertex for edge in edges for vertex in edge)

    assert len(edges) == 31
    assert sorted(degrees.values()) == [3, 4, 4, 5, 5, 5, 6, 6, 7, 7, 10]
    assert degrees["the-first-bell-moot"] == 3
    assert degrees["hearth-hall-and-the-map-room"] == 10
    assert len(set(degrees.values())) == 6


def test_every_bramblewick_revelation_has_independent_support(
    bramblewick_adventure: Adventure,
) -> None:
    """Keep the three-clue and three-source floors intact."""
    clues_by_revelation = group_clues_by_revelation(bramblewick_adventure.clues)

    for revelation in bramblewick_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        assert len(clues) >= 3
        if revelation.required:
            assert len({clue.source_encounter_id for clue in clues}) >= 3


def test_required_conclusions_survive_loss_of_any_one_source_encounter(
    bramblewick_adventure: Adventure,
) -> None:
    """Keep every required conclusion usable after one clue-source loss."""
    source_encounters_by_revelation: defaultdict[str, set[str]] = defaultdict(set)
    for clue in bramblewick_adventure.clues:
        source_encounters_by_revelation[clue.revelation_id].add(clue.source_encounter_id)

    encounter_ids = {encounter.id for encounter in bramblewick_adventure.encounters}
    for revelation in bramblewick_adventure.revelations:
        if not revelation.required:
            continue
        sources = source_encounters_by_revelation[revelation.id]
        for lost_encounter_id in encounter_ids:
            assert len(sources - {lost_encounter_id}) >= 2

    assert len(source_encounters_by_revelation["orlo-vane-killed-merrit-alder"]) == 7


def test_bramblewick_renders_complete_source_and_play_packet(
    bramblewick_adventure: Adventure,
    bramblewick_state: PlayState,
) -> None:
    """Keep the checked-in packet aligned with source and journal."""
    report = validate_adventure(bramblewick_adventure)
    documents = render_adventure_documents(
        bramblewick_adventure,
        report,
        bramblewick_state,
    )

    assert set(documents) >= {
        "00-overview.md",
        "01-encounter-index.md",
        "02-clue-list.md",
        "03-revelation-list.md",
        "04-validation-report.md",
        "05-play-summary.md",
    }
    assert len([name for name in documents if name.startswith("encounters/")]) == 11
    assert "Result: PASS" in documents["04-validation-report.md"]
    assert "Corrections recorded: 1" in documents["05-play-summary.md"]

    assert_rendered_documents_match(
        documents, EXAMPLE_DIRECTORY / "generated"
    )


def test_checked_in_journal_solves_the_case_without_exhausting_the_village(
    bramblewick_adventure: Adventure,
    bramblewick_state: PlayState,
) -> None:
    """Keep the route, omissions, correction, and final finding stable."""
    projection = project_play_state(bramblewick_adventure, bramblewick_state)
    visited = tuple(visit.encounter_id for visit in projection.visits)
    progress = projection.revelation_progress_index()
    spotted = set(projection.spotted_clue_ids)

    assert len(bramblewick_state.events) == 156
    assert len(bramblewick_state.active_events) == 154
    assert visited == (
        "hearth-hall-and-the-map-room",
        "alder-orchard",
        "merrit-alder-s-burrow",
        "the-common-chest",
        "chapel-of-the-open-door",
        "bramblewick-school",
        "the-copper-kettle-and-long-pantry",
        "the-north-hedge",
        "hearth-hall-and-the-map-room",
        "the-first-bell-moot",
    )
    assert all(
        progress[revelation.id].is_established
        for revelation in bramblewick_adventure.revelations
        if revelation.required
    )
    assert progress["a-brass-acorn-map-weight-was-the-weapon"].is_established
    assert progress[
        "bram-searched-merrits-papers-earlier-but-worked-in-the-orchard-during-the-murder"
    ].is_established
    assert progress[
        "mara-paid-for-silence-about-brandy-and-was-in-the-pantry-during-the-murder"
    ].is_established
    assert progress[
        "hester-spent-common-money-on-the-bridge-and-served-pie-during-the-murder"
    ].is_established
    assert not progress[
        "cora-confronted-merrit-before-supper-and-stopped-the-mill-during-the-murder"
    ].is_established
    assert not progress[
        "perrin-altered-dosage-records-but-the-medicine-did-not-kill-merrit"
    ].is_established
    assert set(projection.available_encounter_ids) == {
        encounter.id for encounter in bramblewick_adventure.encounters
    }
    assert len(spotted) == 84
    assert len(bramblewick_adventure.clues) - len(spotted) == 39

    unvisited_sources = {"moss-apothecary", "bramble-mill"}
    assert (
        not {
            clue.id
            for clue in bramblewick_adventure.clues
            if clue.source_encounter_id in unvisited_sources
        }
        & spotted
    )
    assert len(projection.corrections) == 1
    assert projection.corrections[0].target_operation_number == 13
    assert "earlier desk search" in projection.corrections[0].reason


def test_accusation_is_ready_before_the_moot_and_not_created_by_confession(
    bramblewick_adventure: Adventure,
    bramblewick_state: PlayState,
) -> None:
    """Keep the final hearing demonstrative rather than revelation-dependent."""
    projection = project_play_state(bramblewick_adventure, bramblewick_state)
    progress = projection.revelation_progress_index()

    assert (
        progress["the-evidence-supports-a-coherent-first-bell-accusation"].established_sequence
        == 134
    )
    assert progress["orlo-vane-killed-merrit-alder"].established_sequence == 150
    assert progress[
        "the-evidence-supports-a-coherent-first-bell-accusation"
    ].establishment_clue_ids == (
        "the-chest-supplies-a-complete-motive-exhibit",
        "the-school-gathers-the-broken-alibi-the-chalk-and-the-fund",
        "the-route-can-be-proved-without-naming-a-footprint",
    )
    assert progress["orlo-vane-killed-merrit-alder"].establishment_clue_ids == (
        "only-orlo-owns-the-threatened-scheme",
        "orlo-selected-the-names-merrit-was-about-to-expose",
        "the-wash-basin-holds-blood-dilution-and-merrits-collar-lint",
        "orlo-revises-both-his-presence-and-his-entrance",
        "only-orlo-fits-the-whole-crossing",
        "the-whole-sequence-leaves-no-innocent-substitute",
    )
    assert "confession" not in progress["orlo-vane-killed-merrit-alder"].establishment_note.lower()
    assert any(
        consequence.encounter_id == "the-first-bell-moot"
        and "rather than confession" in consequence.text
        for consequence in projection.consequences
    )


def test_bramblewick_cold_read_packet_is_gm_ready() -> None:
    """Keep table control, chronology, and construction-history segregation explicit."""
    quickstart = EXAMPLE_QUICKSTART_PATH.read_text(encoding="utf-8")
    overview = (EXAMPLE_DIRECTORY / "generated" / "00-overview.md").read_text(encoding="utf-8")
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")
    journal = EXAMPLE_STATE_PATH.read_text(encoding="utf-8")

    required_quickstart_text = [
        "## Exact murder timeline",
        "## Suspect sheet",
        "## The six propositions of the accusation",
        "## When the investigation stalls",
        "## Running the two commonly unvisited encounters",
        "## First-Bell Moot thresholds",
        "The beneficiary box can remain sealed",
    ]
    required_overview_text = [
        "### Murder sequence",
        "**8:44 p.m.**",
        "### Suspects at a glance",
        "### When the investigation stalls",
        "### Privacy and collateral wrongdoing",
    ]

    assert all(item in quickstart for item in required_quickstart_text)
    assert all(item in overview for item in required_overview_text)
    assert "At 8:44, Orlo struck him" in playthrough
    assert "Orlo killed Merrit at 8:44" in journal
    assert "8:47" not in playthrough
    assert "8:47" not in journal


def test_playthrough_party_and_summary_fix_the_same_outcome() -> None:
    """Keep the narrative, party design, journal, and generated summary aligned."""
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")
    party = EXAMPLE_PARTY_PATH.read_text(encoding="utf-8")

    required_playthrough_text = [
        "Hall -> Orchard -> Burrow -> Chest -> Chapel -> School",
        "The company voids the overstatement rather than erasing it",
        "The ghost-hearth warrants are different",
        "the footprint is not unique",
        "The moot finds that Orlo Vane killed Merrit Alder",
        "Moss Apothecary and Bramble Mill",
        "84 spotted clues and 39 unseen clues",
    ]
    required_party_text = [
        "The Lantern Measure",
        "Bram's traces",
        "Hester's accounts",
        "The children",
        "The beneficiaries",
        "The acorn weight strengthens the account of the blow",
    ]

    assert all(text in playthrough for text in required_playthrough_text)
    assert all(text in party for text in required_party_text)

    summary = render_play_summary(
        load_adventure(EXAMPLE_PATH),
        load_play_state(EXAMPLE_STATE_PATH),
    )
    assert "Events recorded: 156" in summary
    assert "Active events: 154" in summary
    assert "Corrections recorded: 1" in summary
    assert "Visits recorded: 10" in summary
    assert "The moot found Orlo Vane responsible" in summary
    assert "Beneficiary identities remained sealed" in summary


def test_bramblewick_second_look_coherence_is_reconciled(
    bramblewick_adventure: Adventure,
    bramblewick_state: PlayState,
) -> None:
    """Lock the repaired causality, authority, identities, and unchanged structure."""
    encounters = {encounter.id: encounter for encounter in bramblewick_adventure.encounters}
    clues = {clue.id: clue for clue in bramblewick_adventure.clues}
    explanation = bramblewick_adventure.explanation
    quickstart = EXAMPLE_QUICKSTART_PATH.read_text(encoding="utf-8")
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")

    assert "screened clerk's passage" in explanation
    assert "tears out the two comparison leaves" in explanation
    assert "feeds the stolen leaves" in explanation
    assert "Merrit's signed invitation appoints the newcomers as outside witnesses" in explanation
    assert "sealed correction, repayment over time" in explanation
    assert "strikes him with the nearest brass acorn map weight" in explanation
    assert "## Temporary authority" in quickstart
    assert "screened clerk's passage" in playthrough
    assert "washed and burned the leaves at the school" in playthrough

    assert "without crossing the public floor" in encounters["hearth-hall-and-the-map-room"].content
    assert (
        "The inner covered turn reaches the clerk's passage"
        in encounters["the-copper-kettle-and-long-pantry"].content
    )
    assert "Nothing legible survives" in encounters["bramblewick-school"].content
    assert "Nim arrives with the second key and rain on his shoulders" in encounters[
        "the-common-chest"
    ].content
    assert (
        "The evidence must carry the action requested" in encounters["the-first-bell-moot"].content
    )

    assert (
        "pulled closed from outside but not latched after departure"
        in clues["no-forced-entry-and-an-unlatched-garden-door"].description
    )
    assert (
        "could reach the map room without force or crossing the public hall"
        in clues["the-authorized-key-register-names-orlo"].description
    )


    assert len(bramblewick_adventure.encounters) == 11
    assert len(bramblewick_adventure.revelations) == 26
    assert len(bramblewick_adventure.clues) == 123
    assert len(bramblewick_state.events) == 156
    assert len(bramblewick_state.active_events) == 154


def test_bramblewick_second_look_clue_density_is_reconciled(
    bramblewick_adventure: Adventure,
    bramblewick_state: PlayState,
) -> None:
    """Lock the selective additions, optional-suspect breadth, and unchanged route."""
    clues = {clue.id: clue for clue in bramblewick_adventure.clues}
    clues_by_revelation = group_clues_by_revelation(bramblewick_adventure.clues)

    expected_additions = {
        "merrit-planned-to-take-the-school-fund-from-orlos-control": (
            "merrit-alder-s-burrow",
            "orlo-vane-killed-merrit-alder",
        ),
        "the-tested-bottle-excludes-maras-kitchen-as-the-murder-method": (
            "moss-apothecary",
            "mara-paid-for-silence-about-brandy-and-was-in-the-pantry-during-the-murder",
        ),
        "fresh-school-ash-matches-the-missing-audit-leaves": (
            "bramblewick-school",
            "orlo-vane-killed-merrit-alder",
        ),
        "the-hedge-traces-separate-bram-from-the-killers-crossing": (
            "the-north-hedge",
            "bram-searched-merrits-papers-earlier-but-worked-in-the-orchard-during-the-murder",
        ),
        "perrins-dose-and-sickroom-sequence-survive-public-testing": (
            "the-first-bell-moot",
            "perrin-altered-dosage-records-but-the-medicine-did-not-kill-merrit",
        ),
    }
    for clue_id, (source_encounter_id, revelation_id) in expected_additions.items():
        assert clues[clue_id].source_encounter_id == source_encounter_id
        assert clues[clue_id].revelation_id == revelation_id

    for revelation_id in (
        "bram-searched-merrits-papers-earlier-but-worked-in-the-orchard-during-the-murder",
        "mara-paid-for-silence-about-brandy-and-was-in-the-pantry-during-the-murder",
        "perrin-altered-dosage-records-but-the-medicine-did-not-kill-merrit",
    ):
        assert len({clue.source_encounter_id for clue in clues_by_revelation[revelation_id]}) == 3

    final_clues = clues_by_revelation["orlo-vane-killed-merrit-alder"]
    assert len(final_clues) == 9
    assert len({clue.source_encounter_id for clue in final_clues}) == 7

    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")

    assert "84 spotted clues and 39 unseen clues" in playthrough

    projection = project_play_state(bramblewick_adventure, bramblewick_state)
    assert len(bramblewick_state.events) == 156
    assert len(projection.spotted_clue_ids) == 84
    assert not expected_additions.keys() & set(projection.spotted_clue_ids)


def test_bramblewick_encounter_introductions_two_are_varied_and_synchronized(
    bramblewick_adventure: Adventure,
    bramblewick_state: PlayState,
) -> None:
    """Protect the compressed sequence, distinct engines, and next-stage handoff."""
    encounters = bramblewick_adventure.encounter_index()
    openings = [encounter.opening_view for encounter in bramblewick_adventure.encounters]

    assert len(set(openings)) == 11
    assert all(64 <= len(opening.split()) <= 75 for opening in openings)
    assert sum(len(opening.split()) for opening in openings) == 754
    assert all("?" not in opening for opening in openings)

    expected_phrases = {
        "hearth-hall-and-the-map-room": "before Bramblewick chooses one",
        "merrit-alder-s-burrow": "keeps one hand on its door",
        "the-copper-kettle-and-long-pantry": "covers the locked cellar latch",
        "moss-apothecary": "the body, the bottle, or your questions",
        "alder-orchard": "Nutmeg strains toward the lower gate",
        "bramble-mill": "Question me while you lift",
        "the-common-chest": "preservation public even when names must remain private",
        "chapel-of-the-open-door": "names as names, not entries",
        "bramblewick-school": "We have not been asked yet",
        "the-north-hedge": "sequence—not destination",
        "the-first-bell-moot": "what the evidence can bear",
    }
    for encounter_id, phrase in expected_phrases.items():
        assert phrase in encounters[encounter_id].opening_view


    documents = render_adventure_documents(
        bramblewick_adventure,
        validate_adventure(bramblewick_adventure),
        bramblewick_state,
    )
    for encounter in bramblewick_adventure.encounters:
        assert encounter.opening_view in documents[f"encounters/{encounter.id}.md"]

    assert len(bramblewick_adventure.encounters) == 11
    assert len(bramblewick_adventure.revelations) == 26
    assert len(bramblewick_adventure.clues) == 123
    assert validate_adventure(bramblewick_adventure).edge_connectivity == 3
    assert len(bramblewick_state.events) == 156
    assert len(bramblewick_state.active_events) == 154


def test_bramblewick_voice_one_is_compressed_and_structurally_stable(
    bramblewick_adventure: Adventure,
    bramblewick_state: PlayState,
) -> None:
    """Protect the source-level voice pass, its compression record, and next handoff."""


    measured_source = "\n".join(
        (
            bramblewick_adventure.synopsis,
            bramblewick_adventure.premise,
            bramblewick_adventure.explanation,
            *(encounter.summary for encounter in bramblewick_adventure.encounters),
            *(encounter.content for encounter in bramblewick_adventure.encounters),
        )
    )
    assert "the party" not in measured_source.lower()
    assert "Each explanation carries one object and drops the rest" in (
        bramblewick_adventure.encounter_index()["the-first-bell-moot"].content
    )
    assert "Orlo concedes one object at a time and changes the sentence around it" in (
        bramblewick_adventure.encounter_index()["bramblewick-school"].content
    )


    report = validate_adventure(bramblewick_adventure)
    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(bramblewick_adventure.encounters) == 11
    assert len(bramblewick_adventure.revelations) == 26
    assert len(bramblewick_adventure.clues) == 123
    assert len(bramblewick_state.events) == 156
    assert len(bramblewick_state.active_events) == 154


def test_bramblewick_voice_two_closes_the_second_look(
    bramblewick_adventure: Adventure,
    bramblewick_state: PlayState,
) -> None:
    """Protect the final source finish, packet reconciliation, and corpus handoff."""
    quickstart = EXAMPLE_QUICKSTART_PATH.read_text(encoding="utf-8")
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")
    party = EXAMPLE_PARTY_PATH.read_text(encoding="utf-8")


    assert "complete encounter sheets" in quickstart
    assert "## When the investigation stalls" in quickstart
    assert "## Running the two commonly unvisited encounters" in quickstart
    assert "nineteen belong to the unvisited Moss Apothecary and Bramble Mill" in playthrough
    assert "twenty are alternative discoveries" in playthrough

    encounters = bramblewick_adventure.encounter_index()
    assert "newcomers as outside witnesses" in bramblewick_adventure.explanation
    assert "returns the next choice to the table" in bramblewick_adventure.explanation
    assert "public act of numbering bundles" not in encounters["the-common-chest"].content
    assert "Nim numbers each removed bundle aloud while Hester writes" in encounters[
        "the-common-chest"
    ].content
    assert "after hearing the proposition" in encounters["chapel-of-the-open-door"].content
    assert "The morning record may reveal or seal" in encounters["the-first-bell-moot"].content

    source_text = EXAMPLE_PATH.read_text(encoding="utf-8")
    for demonstration_name in (
        "Elian Marr",
        "Pella Reedbank",
        "Sable Quoin",
        "Fen Harrow",
        "Lantern Measure",
    ):
        assert demonstration_name not in source_text


    report = validate_adventure(bramblewick_adventure)
    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(bramblewick_adventure.encounters) == 11
    assert len(bramblewick_adventure.revelations) == 26
    assert len(bramblewick_adventure.clues) == 123
    assert len(bramblewick_state.events) == 156
    assert len(bramblewick_state.active_events) == 154
