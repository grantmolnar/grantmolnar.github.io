"""Regression checks for the Salt Road escort drafting sessions."""

import re
from collections import defaultdict
from pathlib import Path

import pytest

from adventure_graph.application.documents import (
    render_adventure_documents,
    render_play_summary,
)
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
from tests.support.corpus_contracts import assert_rendered_documents_match
from tests.support.corpus_contracts import group_clues_by_revelation

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-princess-on-the-salt-road")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"


@pytest.fixture(scope="module")
def salt_road_adventure() -> Adventure:
    """Load the escort source once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def salt_road_state() -> PlayState:
    """Load the canonical Narrow Shield journal once per module."""
    return load_play_state(STATE_PATH)


def test_salt_road_session_one_has_the_intended_braided_shape(
    salt_road_adventure: Adventure,
) -> None:
    """Protect the short route, principal roles, and normal resilience floor."""
    report = validate_adventure(salt_road_adventure)

    assert len(salt_road_adventure.encounters) == 9
    assert len(salt_road_adventure.revelations) == 20
    assert len(salt_road_adventure.clues) == 93
    assert {encounter.id for encounter in salt_road_adventure.encounters if encounter.start} == {
        "house-of-blue-lamps"
    }
    assert {encounter.id for encounter in salt_road_adventure.encounters if encounter.end} == {
        "myrine-harbor"
    }
    assert all(encounter.required for encounter in salt_road_adventure.encounters)
    assert report.is_valid
    assert report.edge_connectivity is not None
    assert report.edge_connectivity >= 3
    assert not [issue for issue in report.issues if issue.severity == "error"]


def test_every_salt_road_revelation_has_at_least_three_independent_sources(
    salt_road_adventure: Adventure,
) -> None:
    """Keep route and operational conclusions independently discoverable."""
    clues_by_revelation = group_clues_by_revelation(salt_road_adventure.clues)

    for revelation in salt_road_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        assert len(clues) >= 3
        assert len({clue.source_encounter_id for clue in clues}) >= 3


def test_salt_road_session_two_adds_irregular_clue_density(
    salt_road_adventure: Adventure,
) -> None:
    """Keep critical rendezvous conclusions richer than the minimum floor."""
    clues_by_revelation = group_clues_by_revelation(salt_road_adventure.clues)

    enriched = {
        "the-ash-knives-want-a-dead-heir",
        "the-bronze-seal-commands-outposts-and-reveals-the-true-route",
        "public-witnesses-protect-as-well-as-expose",
        "the-second-sunset-is-a-hard-political-deadline",
    }
    assert all(len(clues_by_revelation[revelation_id]) >= 4 for revelation_id in enriched)
    assert any(len(clues) == 3 for clues in clues_by_revelation.values())


def test_salt_road_session_two_fully_drafts_the_rendezvous(
    salt_road_adventure: Adventure,
) -> None:
    """Keep the first convergence encounter operational rather than merely sketched."""
    house = salt_road_adventure.encounter_index()["house-at-three-cypresses"]

    assert len(house.content.split()) >= 3000
    for heading in (
        "## Arrival by route",
        "## The tampered remount",
        "## Ianthe's counsel circle",
        "## Dorion's white-cloth offer",
        "## Naevan's leaf-sealed offer",
        "## Preparations and meaningful delay",
        "## Outcomes and failure forward",
    ):
        assert heading in house.content

    assert "Unfixed" in house.content
    assert "Named" in house.content
    assert "Closing" in house.content
    assert "Contact" in house.content


def test_salt_road_session_two_supporting_aid_is_present() -> None:
    """Keep the pursuit procedure and custody distinctions checked in."""
    pursuit = (EXAMPLE_DIRECTORY / "PURSUIT-AND-CUSTODY.md").read_text()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    ledger = (EXAMPLE_DIRECTORY / "ESCORT-LEDGER.md").read_text()

    assert "## The pursuit posture" in pursuit
    assert "## Custody ledger" in pursuit
    assert "## Dorion's usable truces" in pursuit
    assert "## Custody is not a single condition" in design
    assert "**Credible offer:** a thirty-day protector proclamation" in ledger
    assert "**Credible offer:** full extraction" in ledger


def test_salt_road_session_three_fully_drafts_both_middle_routes(
    salt_road_adventure: Adventure,
) -> None:
    """Keep bridge and channel play operational rather than descriptive."""
    encounters = salt_road_adventure.encounter_index()
    bridge = encounters["red-bridge"].content
    reeds = encounters["reed-villages"].content

    assert len(bridge.split()) >= 3000
    for heading in (
        "## The bridge precinct",
        "## Melas Orro and the bridge hearing",
        "## Dorion at the crossing",
        "## Ash Knives in the mechanism",
        "## Encounter frames",
        "## Outcomes and failure forward",
    ):
        assert heading in bridge

    assert len(reeds.split()) >= 3200
    for heading in (
        "## The channel network",
        "## Boats and capacity",
        "## The confiscation landing",
        "## The false loyalist boat",
        "## Route splitting procedure",
        "## Outcomes and failure forward",
    ):
        assert heading in reeds


def test_salt_road_session_three_enriches_middle_road_conclusions(
    salt_road_adventure: Adventure,
) -> None:
    """Keep infrastructure and route-splitting facts above the minimum floor."""
    clues_by_revelation = group_clues_by_revelation(salt_road_adventure.clues)

    enriched = {
        "the-red-bridge-controls-the-mounted-road-to-the-coast",
        "the-reed-villages-offer-a-covered-water-route",
        "the-pursuit-depends-on-remounts-and-beacon-signals",
        "road-communities-are-paying-for-royal-loyalty",
        "the-princess-and-seal-may-travel-separately",
        "armed-companies-cannot-simply-cross-the-white-stones",
    }
    assert all(len(clues_by_revelation[revelation_id]) >= 4 for revelation_id in enriched)


def test_salt_road_session_three_operating_aid_is_present() -> None:
    """Keep the coupled bridge, water, boat, and route-split procedures checked in."""
    operations = (EXAMPLE_DIRECTORY / "BRIDGE-AND-CHANNEL-OPERATIONS.md").read_text()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    ledger = (EXAMPLE_DIRECTORY / "ESCORT-LEDGER.md").read_text()

    assert "## Red Bridge resources" in operations
    assert "## Reed Village boat capacity" in operations
    assert "## Route split record" in operations
    assert "## Objective-driven encounter menu" in operations
    assert "## Infrastructure is shared consequence" in design
    assert "## Middle-road resource frame" in ledger


def test_salt_road_session_one_fully_drafts_the_departure_encounters(
    salt_road_adventure: Adventure,
) -> None:
    """Keep the escort compact and all three Aulon exits table-usable."""
    encounters = salt_road_adventure.encounter_index()

    for encounter_id, minimum_words in {
        "house-of-blue-lamps": 1000,
        "gate-of-horns": 500,
        "dry-aqueduct": 600,
        "cypress-gate": 550,
    }.items():
        assert len(encounters[encounter_id].content.split()) >= minimum_words

    assert "## Ianthe's compact" in encounters["house-of-blue-lamps"].content
    assert "## Three ways out" in encounters["house-of-blue-lamps"].content
    assert "## Protection problem" in encounters["gate-of-horns"].content
    assert "## Threats in confined ground" in encounters["dry-aqueduct"].content
    assert "## Protection without drawn steel" in encounters["cypress-gate"].content


def test_salt_road_preserves_principal_agency_and_public_conflict(
    salt_road_adventure: Adventure,
) -> None:
    """Prevent a bodyguard premise from degrading into passive-cargo play."""
    combined = "\n".join(
        [
            salt_road_adventure.synopsis,
            salt_road_adventure.premise,
            salt_road_adventure.explanation,
            *(encounter.content for encounter in salt_road_adventure.encounters),
        ]
    )

    assert "Do not make me safe by making me absent" in combined
    assert "the funeral rolls, sickroom tablets, and public notices agree" in combined
    assert "No hidden murderer waits behind the interregnum" not in combined
    assert "Only Ianthe\u2019s living, uncoerced speech" in combined
    assert "Ianthe is not cargo" not in combined
    assert "Myrine Harbor" in combined


def test_salt_road_renders_a_complete_packet(
    salt_road_adventure: Adventure,
) -> None:
    """Keep generated source documents aligned with the checked-in source."""
    report = validate_adventure(salt_road_adventure)
    documents = render_adventure_documents(salt_road_adventure, report)

    assert len([name for name in documents if name.startswith("encounters/")]) == 9
    assert "Result: PASS" in documents["04-validation-report.md"]
    assert "05-play-summary.md" not in documents
    assert_rendered_documents_match(
        documents, EXAMPLE_DIRECTORY / "generated"
    )


def test_salt_road_session_four_fully_drafts_the_final_approach(
    salt_road_adventure: Adventure,
) -> None:
    """Keep Beacon Hill and Myrine Harbor operational and independently resolved."""
    encounters = salt_road_adventure.encounter_index()
    beacon = encounters["beacon-hill"].content
    harbor = encounters["myrine-harbor"].content

    assert len(beacon.split()) >= 3800
    for heading in (
        "## The tower precinct",
        "## The signal lexicon",
        "## Three descents to Myrine",
        "## Dorion at the hill",
        "## Objective-driven encounter frames",
        "## Outcomes and failure forward",
    ):
        assert heading in beacon

    assert len(harbor.split()) >= 3900
    for heading in (
        "## Harbor geography",
        "## The three magistrates",
        "## The sanctuary procedure",
        "## Weapon handling and bodyguard access",
        "## Objective-driven finale frames",
        "## Mixed-success endings",
    ):
        assert heading in harbor


def test_salt_road_session_four_enriches_finale_conclusions(
    salt_road_adventure: Adventure,
) -> None:
    """Keep signal, sanctuary, deadline, and public-account facts richly sourced."""
    clues_by_revelation = group_clues_by_revelation(salt_road_adventure.clues)

    assert len(salt_road_adventure.clues) >= 76
    expected_counts = {
        "beacon-hill-controls-myrines-last-approach": 4,
        "myrine-sanctuary-begins-with-a-free-petition": 5,
        "armed-companies-cannot-simply-cross-the-white-stones": 5,
        "kallias-says-the-bodyguards-abducted-ianthe": 5,
        "the-second-sunset-is-a-hard-political-deadline": 6,
    }
    for revelation_id, expected in expected_counts.items():
        assert len(clues_by_revelation[revelation_id]) == expected


def test_salt_road_session_four_operating_aid_is_present() -> None:
    """Keep signal, descent, chain, sanctuary, and finale procedures checked in."""
    operations = (EXAMPLE_DIRECTORY / "BEACON-AND-HARBOR-OPERATIONS.md").read_text()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    ledger = (EXAMPLE_DIRECTORY / "ESCORT-LEDGER.md").read_text()

    assert "## Signal lexicon" in operations
    assert "## Three descents" in operations
    assert "## Sanctuary procedure" in operations
    assert "## Finale objective ledger" in operations
    assert "## The finale is distributed" in design
    assert "## Procedure creates tactical terrain" in design
    assert "## Final-approach resource frame" in ledger


def test_salt_road_session_five_discloses_both_middle_roads_from_every_exit(
    salt_road_adventure: Adventure,
) -> None:
    """Keep every city exit capable of supporting an informed direct continuation."""
    revelation_index = salt_road_adventure.revelation_index()
    unlocks_by_source: defaultdict[str, set[str]] = defaultdict(set)
    for clue in salt_road_adventure.clues:
        unlocked = revelation_index[clue.revelation_id].unlocks_encounter_id
        if unlocked is not None:
            unlocks_by_source[clue.source_encounter_id].add(unlocked)

    for departure in ("gate-of-horns", "dry-aqueduct", "cypress-gate"):
        assert {
            "house-at-three-cypresses",
            "red-bridge",
            "reed-villages",
        } <= unlocks_by_source[departure]


def test_salt_road_session_five_makes_bypasses_explicit(
    salt_road_adventure: Adventure,
) -> None:
    """Keep useful rendezvous and signal encounters from becoming mandatory tollbooths."""
    encounters = salt_road_adventure.encounter_index()
    expected_headings = {
        "house-of-blue-lamps": "## Keeping the route open",
        "gate-of-horns": "## Beyond the gate",
        "dry-aqueduct": "## Choosing beyond the olive cutting",
        "cypress-gate": "## Roads beyond the last lion",
        "house-at-three-cypresses": "## If the rendezvous is skipped or missed",
        "red-bridge": "## Arrival without the courier house",
        "reed-villages": "## Arrival without the courier house",
        "beacon-hill": "## Bypassing the hill",
        "myrine-harbor": "## Arrival without a beacon account",
    }
    for encounter_id, heading in expected_headings.items():
        assert heading in encounters[encounter_id].content


def test_salt_road_session_five_operating_and_stress_aids_are_present() -> None:
    """Keep route, clue, split-party, and principal-agency procedures checked in."""
    operating = (EXAMPLE_DIRECTORY / "GM-OPERATING-SHEET.md").read_text()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()

    for heading in (
        "## Start-of-encounter declaration",
        "## Scene operating loop",
        "## Physical route matrix",
        "## Divided-escort threat allocation",
        "## Ianthe's decision frame",
        "## Clue timing checklist",
    ):
        assert heading in operating


    assert "## The clue graph is not the road" in design
    assert "## Divided routes obey adversary knowledge" in design
    assert "## Ianthe's decisions are reasoned, not scripted" in design


def test_salt_road_session_five_has_the_audited_clue_total(
    salt_road_adventure: Adventure,
) -> None:
    """Protect the three forward route clues added by the route stress test."""
    assert len(salt_road_adventure.clues) == 93
    clue_ids = {clue.id for clue in salt_road_adventure.clues}
    assert {
        "gate-of-horns-the-red-bridge-controls-the-mounted-road-to-the-coast-1",
        "gate-of-horns-the-reed-villages-offer-a-covered-water-route-1",
        "dry-aqueduct-the-reed-villages-offer-a-covered-water-route-1",
    } <= clue_ids


def test_salt_road_session_six_adds_completion_material() -> None:
    """Keep the party, playthrough, aftermath, and final audit checked in."""
    party = (EXAMPLE_DIRECTORY / "PARTY-DESIGN.md").read_text()
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()
    aftermath = (EXAMPLE_DIRECTORY / "AFTERMATH-AND-SETTLEMENT.md").read_text()

    for name in ("Damon Keryx", "Phaedra Neris", "Thaleia Ormon", "Melia Varo"):
        assert name in party
    assert "The Narrow Shield" in party
    assert "House of Blue Lamps -> Dry Aqueduct -> House at Three Cypresses" in playthrough
    assert "Reed Villages / Red Bridge -> Beacon Hill -> Myrine Harbor" in playthrough
    assert "Melia and Thaleia sail with Ianthe" in playthrough
    assert "## Thirty-day political states" in aftermath
    assert "## Canonical demonstration aftermath" in aftermath


def test_salt_road_session_six_journal_demonstrates_the_divided_route(
    salt_road_adventure: Adventure,
    salt_road_state: PlayState,
) -> None:
    """Keep the canonical route, misses, sessions, and mixed outcome stable."""
    projection = project_play_state(salt_road_adventure, salt_road_state)

    assert len(salt_road_state.events) == 136
    assert len(salt_road_state.active_events) == 136
    assert tuple(visit.encounter_id for visit in projection.visits) == (
        "house-of-blue-lamps",
        "dry-aqueduct",
        "house-at-three-cypresses",
        "reed-villages",
        "red-bridge",
        "beacon-hill",
        "myrine-harbor",
    )
    assert tuple(visit.party_label for visit in projection.visits[3:5]) == (
        "Princess Ianthe, Damon, Melia, Mara, and the reed convoy",
        "Phaedra and Thaleia with the bronze seal",
    )
    assert len(projection.sessions) == 3
    assert projection.active_session_number is None
    assert {session.title for session in projection.sessions} == {
        "Under Stone, Under Oath",
        "Two Roads, One Principal",
        "Seven Stones and Three Judgments",
    }
    assert len(projection.spotted_clue_ids) == 50
    assert sum(len(item.missed_visit_numbers) for item in projection.clue_progress) == 6
    assert all(item.is_established for item in projection.revelation_progress)
    assert set(projection.available_encounter_ids) == {
        encounter.id for encounter in salt_road_adventure.encounters
    }
    assert len(projection.consequences) == 11

    consequences = "\n".join(item.text for item in projection.consequences)
    assert "Myrine takes the bronze seal into treaty custody" in consequences
    assert "Ianthe, Melia, and Thaleia sail on the Sea-Lark" in consequences
    assert "Damon and Phaedra remain free in Myrine" in consequences
    assert "crossing and Heron Sluice continue operating" in consequences


def test_salt_road_session_six_play_summary_matches_the_journal(
    salt_road_adventure: Adventure,
    salt_road_state: PlayState,
) -> None:
    """Keep the generated play summary reproducible from source and journal."""
    summary = render_play_summary(salt_road_adventure, salt_road_state)

    assert summary == (EXAMPLE_DIRECTORY / "generated" / "05-play-summary.md").read_text()
    assert "Events recorded: 136" in summary
    assert "Explicit sessions: 3" in summary
    assert "Visits recorded: 7" in summary
    assert "The Narrow Shield with Princess Ianthe" in summary
    assert "Myrine takes the bronze seal into treaty custody" in summary


def test_salt_road_session_six_renders_source_and_play_packet(
    salt_road_adventure: Adventure,
    salt_road_state: PlayState,
) -> None:
    """Keep all checked-in generated documents aligned after journal completion."""
    report = validate_adventure(salt_road_adventure)
    documents = render_adventure_documents(
        salt_road_adventure,
        report,
        salt_road_state,
    )

    assert "05-play-summary.md" in documents
    assert_rendered_documents_match(
        documents, EXAMPLE_DIRECTORY / "generated"
    )


def test_salt_road_session_seven_completes_voice_pass(
    salt_road_adventure: Adventure,
    salt_road_state: PlayState,
) -> None:
    """Keep the completed voice pass and its structural invariants checked in."""
    revelation_titles = {item.title for item in salt_road_adventure.revelations}

    assert "The Horn Road buys speed with witnesses" in revelation_titles
    assert "Sanctuary begins when Ianthe speaks for herself" in revelation_titles
    assert "Myrine admits a petitioner, not an armed company" in revelation_titles
    assert len(salt_road_adventure.encounters) == 9
    assert len(salt_road_adventure.revelations) == 20
    assert len(salt_road_adventure.clues) == 93
    assert len(salt_road_state.events) == 136


def test_salt_road_second_look_clue_density_broadens_campaign_evidence(
    salt_road_adventure: Adventure,
    salt_road_state: PlayState,
) -> None:
    """Protect the ninety-three-clue matrix and unchanged demonstration."""
    clues_by_revelation = group_clues_by_revelation(salt_road_adventure.clues)
    clues_by_encounter = group_clues_by_encounter(salt_road_adventure.clues)
    pairs: set[tuple[str, str]] = set()
    for clue in salt_road_adventure.clues:
        pair = (clue.source_encounter_id, clue.revelation_id)
        assert pair not in pairs
        pairs.add(pair)

    assert len(salt_road_adventure.clues) == 93
    assert {len(clues) for clues in clues_by_revelation.values()} == {3, 4, 5, 6}
    assert min(len(clues) for clues in clues_by_encounter.values()) == 5
    assert max(len(clues) for clues in clues_by_encounter.values()) == 13
    assert len(clues_by_encounter["red-bridge"]) == 13
    assert len(clues_by_encounter["beacon-hill"]) == 12
    assert len(clues_by_encounter["myrine-harbor"]) == 11

    added_ids = {
        "red-bridge-dorion-must-recover-ianthe-alive-1",
        "beacon-hill-dorion-must-recover-ianthe-alive-1",
        "myrine-harbor-dorion-must-recover-ianthe-alive-1",
        "beacon-hill-the-ash-knives-want-a-dead-heir-1",
        "myrine-harbor-the-ash-knives-want-a-dead-heir-1",
        "red-bridge-public-witnesses-protect-as-well-as-expose-1",
        "beacon-hill-public-witnesses-protect-as-well-as-expose-1",
        "cypress-gate-road-communities-are-paying-for-royal-loyalty-1",
        "myrine-harbor-road-communities-are-paying-for-royal-loyalty-1",
        "cypress-gate-ianthe-seeks-a-free-assembly-not-a-foreign-crown-1",
        "beacon-hill-ianthe-seeks-a-free-assembly-not-a-foreign-crown-1",
        "red-bridge-kallias-says-the-bodyguards-abducted-ianthe-1",
        "beacon-hill-the-princess-and-seal-may-travel-separately-1",
        "red-bridge-the-second-sunset-is-a-hard-political-deadline-1",
    }
    assert added_ids <= {clue.id for clue in salt_road_adventure.clues}

    projection = project_play_state(salt_road_adventure, salt_road_state)
    assert len(salt_road_state.events) == 136
    assert len(projection.spotted_clue_ids) == 50
    assert len(salt_road_adventure.clues) - len(projection.spotted_clue_ids) == 43
    assert all(item.is_established for item in projection.revelation_progress)


def test_salt_road_second_look_coherence_preserves_fresh_play(
    salt_road_adventure: Adventure,
    salt_road_state: PlayState,
) -> None:
    """Keep the authoritative escort independent from its named demonstration."""
    source_prose = "\n".join(
        [
            salt_road_adventure.synopsis,
            salt_road_adventure.premise,
            salt_road_adventure.explanation,
            *(encounter.summary for encounter in salt_road_adventure.encounters),
            *(encounter.opening_view for encounter in salt_road_adventure.encounters),
            *(encounter.content for encounter in salt_road_adventure.encounters),
            *(revelation.title for revelation in salt_road_adventure.revelations),
            *(revelation.description for revelation in salt_road_adventure.revelations),
            *(clue.description for clue in salt_road_adventure.clues),
        ]
    )
    operating_sheet = (EXAMPLE_DIRECTORY / "GM-OPERATING-SHEET.md").read_text()
    house = salt_road_adventure.encounter_index()["house-at-three-cypresses"].content
    gate = salt_road_adventure.encounter_index()["gate-of-horns"].content
    beacon = salt_road_adventure.encounter_index()["beacon-hill"].content

    assert "Narrow Shield" not in source_prose
    for demonstrator in (
        "Damon",
        "Phaedra Neris",
        "Thaleia",
        "Melia",
    ):
        assert demonstrator not in source_prose
    assert "four sworn bodyguards" not in source_prose
    assert "Sael" not in source_prose
    assert "Killing the herald or striking under white cloth" in house
    assert "armed retainers outside civic command" in gate
    assert "Ianthe\u2019s household escort as armed abductors" in beacon
    assert "## Fresh-escort composition" in operating_sheet
    assert "The Narrow Shield is an optional demonstration company" in operating_sheet
    assert len(salt_road_adventure.encounters) == 9
    assert len(salt_road_adventure.revelations) == 20
    assert len(salt_road_adventure.clues) == 93
    assert len(salt_road_state.events) == 136


def test_salt_road_encounter_introductions_two_form_a_paced_escort_sequence(
    salt_road_adventure: Adventure,
    salt_road_state: PlayState,
) -> None:
    """Protect the compressed openings, route discipline, and Voice I handoff."""
    encounters = salt_road_adventure.encounter_index()
    openings = [encounter.opening_view for encounter in salt_road_adventure.encounters]

    assert len(set(openings)) == 9
    assert sum(len(opening.split()) for opening in openings) == 689
    assert all(70 <= len(opening.split()) <= 84 for opening in openings)

    expected_phrases = {
        "house-of-blue-lamps": "the correct signal, known to too many hands",
        "gate-of-horns": "The wicket narrows around the next traveler",
        "dry-aqueduct": "the passage permits only one order of march",
        "cypress-gate": "Name the peace you ask us to spend.",
        "house-at-three-cypresses": "Every additional preparation costs distance from the pursuit.",
        "red-bridge": "waits for a signature.",
        "reed-villages": "not the whole cost of flight.",
        "beacon-hill": "Records and witnesses must make anyone believe the correction.",
        "myrine-harbor": "Who crosses with her?",
    }
    for encounter_id, phrase in expected_phrases.items():
        assert phrase in encounters[encounter_id].opening_view

    combined = "\n".join(openings)
    for demonstrator in ("Narrow Shield", "Damon", "Phaedra Neris", "Thaleia", "Melia"):
        assert demonstrator not in combined


    report = validate_adventure(salt_road_adventure)
    assert report.is_valid
    assert report.edge_connectivity == 4
    assert len(salt_road_state.events) == 136


def test_salt_road_voice_one_returns_protection_to_the_material_road(
    salt_road_adventure: Adventure,
    salt_road_state: PlayState,
) -> None:
    """Protect the source-level voice pass and its unchanged play surfaces."""
    bodies = "\n".join(encounter.content for encounter in salt_road_adventure.encounters)
    summaries = "\n".join(encounter.summary for encounter in salt_road_adventure.encounters)
    overview = "\n".join(
        (
            salt_road_adventure.synopsis,
            salt_road_adventure.premise,
            salt_road_adventure.explanation,
        )
    )

    for generic_actor in ("party", "players", "adventurers"):
        assert generic_actor not in bodies.lower()
    assert "party" not in summaries.lower()
    assert "player characters" not in overview.lower()
    assert (
        sum(len(encounter.content.split()) for encounter in salt_road_adventure.encounters) == 23463
    )
    assert (
        sum(len(encounter.summary.split()) for encounter in salt_road_adventure.encounters) == 215
    )
    assert (
        sum(len(encounter.opening_view.split()) for encounter in salt_road_adventure.encounters)
        == 689
    )

    source = EXAMPLE_PATH.read_text(encoding="utf-8")
    assert "Concealment buys distance while Kallias names what the unseen miles mean." in source
    assert "before Dorion\u2019s information becomes a road beneath his horses" in source
    assert "Myrine already acting on someone else’s nouns" in source
    assert "Each has its own lane, custodian, and failure point." in source


    assert len(salt_road_state.events) == 136


def test_salt_road_voice_two_reconciles_packet_and_closes_second_look(
    salt_road_adventure: Adventure,
    salt_road_state: PlayState,
) -> None:
    """Protect the final source finish, corpus reconciliation, and next handoff."""
    authored_prose = "\n".join(
        (
            salt_road_adventure.synopsis,
            salt_road_adventure.premise,
            salt_road_adventure.explanation,
            *(encounter.summary for encounter in salt_road_adventure.encounters),
            *(encounter.opening_view for encounter in salt_road_adventure.encounters),
            *(encounter.content for encounter in salt_road_adventure.encounters),
            *(revelation.title for revelation in salt_road_adventure.revelations),
            *(revelation.description for revelation in salt_road_adventure.revelations),
            *(clue.title for clue in salt_road_adventure.clues),
            *(clue.description for clue in salt_road_adventure.clues),
            *(clue.discovery for clue in salt_road_adventure.clues),
        )
    )
    authored_lower = authored_prose.lower()

    for generic_term in ("party", "players", "adventurers", "gm", "adventure"):
        assert not re.search(rf"\b{generic_term}\b", authored_lower)

    source = EXAMPLE_PATH.read_text(encoding="utf-8")
    for phrase in (
        "the funeral rolls, sickroom tablets, and public notices agree",
        "the moment at which her authority returns",
        "roads remain governed by distance, terrain, and control",
        "A decoy fails only when pursuers gain evidence",
        "Table discussion alone spends no bell",
        "The reeds hide an escort by spending a village",
    ):
        assert phrase in source

    assert (
        sum(len(encounter.content.split()) for encounter in salt_road_adventure.encounters) == 23463
    )
    assert (
        sum(len(encounter.opening_view.split()) for encounter in salt_road_adventure.encounters)
        == 689
    )
    assert {revelation.title for revelation in salt_road_adventure.revelations} >= {
        "The reeds hide an escort by spending a village"
    }


    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text(encoding="utf-8")
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text(encoding="utf-8")

    assert "## Second-look Voice I and II" in design
    assert not re.search(r"\bnodes?\b|\bthe party\b", playthrough, re.IGNORECASE)

    report = validate_adventure(salt_road_adventure)
    projection = project_play_state(salt_road_adventure, salt_road_state)
    assert len(salt_road_adventure.encounters) == 9
    assert len(salt_road_adventure.revelations) == 20
    assert len(salt_road_adventure.clues) == 93
    assert report.is_valid
    assert report.edge_connectivity == 4
    assert len(salt_road_state.events) == 136
    assert len(projection.spotted_clue_ids) == 50
    assert len(salt_road_adventure.clues) - len(projection.spotted_clue_ids) == 43
