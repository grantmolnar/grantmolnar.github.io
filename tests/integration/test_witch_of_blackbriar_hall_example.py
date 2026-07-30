"""Regression checks for the Blackbriar witch-hunt adventure."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

from adventure_graph.application.documents import (
    render_adventure_documents,
    render_play_summary,
)
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.adventure import Adventure, AdventureTags
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.journal_archive_store import load_journal_archive
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.corpus_contracts import (
    assert_rendered_documents_match,
    group_clues_by_revelation,
)

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-witch-of-blackbriar-hall")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"
EXAMPLE_ARCHIVE_PATH = (
    EXAMPLE_DIRECTORY / "archives" / "blackbriar-commission-demonstrated-playthrough.journal.json"
)


@pytest.fixture(scope="module")
def witch_adventure() -> Adventure:
    """Load the current Blackbriar source once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def witch_state() -> PlayState:
    """Load the completed Blackbriar demonstration journal once per module."""
    return load_play_state(EXAMPLE_STATE_PATH)


def test_blackbriar_foundation_preserves_the_villain_hunt_shape(
    witch_adventure: Adventure,
) -> None:
    """Protect the compact graph, explicit antagonist, and valid resilient structure."""
    report = validate_adventure(witch_adventure)

    assert len(witch_adventure.encounters) == 10
    assert len(witch_adventure.revelations) == 18
    assert len(witch_adventure.clues) == 95
    assert witch_adventure.tags.genres == ("Dark fantasy", "Horror", "Investigation")
    assert witch_adventure.tags.game_systems == ("System-agnostic",)
    assert witch_adventure.tags.settings == ("Original fantasy",)
    assert (
        witch_adventure.tags.party_size_min,
        witch_adventure.tags.party_size_max,
    ) == (4, 6)
    assert witch_adventure.tags.level_min is None
    assert witch_adventure.tags.level_max is None
    assert witch_adventure.tags.combat_intensity == "moderate"
    assert witch_adventure.tags.keywords == (
        "Villain hunt",
        "Occult pacts",
        "Captive rescue",
        "Community resistance",
        "Time pressure",
    )
    assert {encounter.id for encounter in witch_adventure.encounters if encounter.start} == {
        "saint-orra-gallows"
    }
    assert {encounter.id for encounter in witch_adventure.encounters if encounter.end} == {
        "underhall-of-the-hollow-feast"
    }
    assert all(encounter.required for encounter in witch_adventure.encounters)
    assert all(revelation.required for revelation in witch_adventure.revelations)
    assert report.is_valid
    assert report.edge_connectivity == 4
    assert not [issue for issue in report.issues if issue.severity == "error"]


def test_blackbriar_clue_distribution_is_deliberately_irregular(
    witch_adventure: Adventure,
) -> None:
    """Keep support tied to evidence density rather than a uniform clue count."""
    clues_by_revelation = group_clues_by_revelation(witch_adventure.clues)

    support_counts = sorted(
        len(clues_by_revelation[revelation.id]) for revelation in witch_adventure.revelations
    )
    assert support_counts == [
        3,
        3,
        3,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
        6,
        6,
        6,
        7,
        7,
        7,
        7,
        8,
    ]
    for revelation in witch_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        assert len({clue.source_encounter_id for clue in clues}) == len(clues)

    source_counts = Counter(clue.source_encounter_id for clue in witch_adventure.clues)
    assert min(source_counts.values()) == 7
    assert max(source_counts.values()) == 15
    assert len(set(source_counts.values())) >= 7


def test_blackbriar_keeps_judith_willing_and_central(
    witch_adventure: Adventure,
) -> None:
    """Prevent later drafts from softening the antagonist or hiding her offstage."""
    explanation = witch_adventure.explanation
    encounter_index = witch_adventure.encounter_index()

    assert "Judith Crowl is the witch" in explanation
    assert "She chose each bargain, renewed it when it weakened" in explanation
    assert "Keep Judith in the work" in explanation
    assert "a good son proves his innocence" in encounter_index["saint-orra-gallows"].opening_view
    assert "## The immediate wrong" in encounter_index["saint-orra-gallows"].content
    assert "## Judith's response" in encounter_index["saint-mercy-house"].content
    assert (
        "Judith can be killed while pacts remain"
        in encounter_index["underhall-of-the-hollow-feast"].content
    )


def test_blackbriar_preserves_three_distinct_pacts(
    witch_adventure: Adventure,
) -> None:
    """Keep shelter, burial, and naming violations materially separate."""
    revelation_index = witch_adventure.revelation_index()

    guest = revelation_index["the-guest-in-ash-pact-can-be-broken-at-the-burned-refuge"].description
    worm = revelation_index["the-worm-in-white-pact-can-be-broken-by-honest-burial"].description
    child = revelation_index[
        "the-child-behind-glass-pact-can-be-broken-by-returning-the-stolen-names"
    ].description

    assert "nineteen betrayed names" in guest
    assert "quicklime" in worm
    assert "unborrowed reflection" in child


def test_blackbriar_session_two_fixes_village_resistance_operations(
    witch_adventure: Adventure,
) -> None:
    """Protect the named village layer and bounded resistance procedures."""
    encounter_index = witch_adventure.encounter_index()
    gallows = encounter_index["saint-orra-gallows"].content
    croft = encounter_index["sedge-croft"].content

    assert "## The execution clock" in gallows
    assert "## The legal fault" in gallows
    assert "## Public result" in gallows
    assert "## Revoking Judith's welcome" in croft
    assert "## Making a refuge" in croft
    assert "Nell Sedge, Amey Fen, Jo Rusk" in croft

    ledger = (EXAMPLE_DIRECTORY / "BLACKBRIAR-VALE-LEDGER.md").read_text()
    resistance = (EXAMPLE_DIRECTORY / "PUBLIC-RESISTANCE-AND-RETALIATION.md").read_text()

    assert "sixty-three inhabited households" in ledger
    assert "## Mara's seven prosecution packets" in ledger
    assert "## Missing and taken people" in ledger
    assert "Judith is not omniscient" in resistance
    assert "## Household revocation procedure" in resistance
    assert "## Retaliation ladder" in resistance
    assert "does not turn the village into a single morale score" in resistance


def test_blackbriar_session_three_operationalizes_saint_mercy_house(
    witch_adventure: Adventure,
) -> None:
    """Protect the independent rescue, evidence, medical, and name-vessel procedures."""
    mercy = witch_adventure.encounter_index()["saint-mercy-house"].content

    assert "## The inspection clock" in mercy
    assert "## Name-vessel handling" in mercy
    assert "## Evacuation procedure" in mercy
    assert "## Sister Harl's decisions" in mercy
    assert "All seven silvered name vessels are still in the mirror dormitory" in mercy
    for captive in ("Nell Sedge", "Amey Fen", "Lark Merrow", "Sella Darr", "Eda Lorn"):
        assert captive in mercy
    assert "A disorderly rescue still saves people" in mercy

    operations = (EXAMPLE_DIRECTORY / "SAINT-MERCY-HOUSE-OPERATIONS.md").read_text()
    assert "## Name-vessel register" in operations
    assert "## Infirmary transfer register" in operations
    assert "## Evacuation routes" in operations
    assert "## Judith's public counterattack" in operations
    assert "does not return the name" in operations


def test_blackbriar_session_four_operationalizes_the_pact_sites(
    witch_adventure: Adventure,
) -> None:
    """Protect material severance, persistent partial work, and distinct patron rules."""
    encounter_index = witch_adventure.encounter_index()
    refuge = encounter_index["burned-refuge"].content
    pits = encounter_index["white-pits"].content
    chapel = encounter_index["chapel-of-the-free-witness"].content
    mere = encounter_index["moonless-mere"].content

    assert "## Opening the original doors" in refuge
    assert "## Restoring the names" in refuge
    assert "## Burning the false shelter ledger" in refuge
    assert "Orra Kelm, Sero Kelm, Hara Kelm, Lio Kelm" in refuge
    assert "Opening the doors frees the dead to speak" in refuge

    assert "## The founding thirty-one" in pits
    assert "## Preparing the extraction" in pits
    assert "## Honest burial or burning" in pits
    assert "Bera Pell, Oren Pell" in pits
    assert "all thirty-one founding dead" in pits

    assert "## Repairing the honest bell" in chapel
    assert "## The threshold procedure" in chapel
    assert "## The burial procedure" in chapel
    assert "## The naming procedure" in chapel
    assert "Do not replace the door" in chapel

    assert "## Testing an unborrowed reflection" in mere
    assert "## Returning a name to its owner" in mere
    assert "## Returning an absent or dead person's name" in mere
    assert "## Mirror navigation" in mere
    assert "A restored name stays restored" in mere

    operations = (EXAMPLE_DIRECTORY / "PACT-SITE-OPERATIONS.md").read_text()
    assert "Completed work persists" in operations
    assert "## The nineteen" in operations
    assert "## Founding thirty-one" in operations
    assert "## Current seven" in operations
    assert "# Judith's response record" in operations


def test_blackbriar_session_five_operationalizes_hall_wood_and_feast(
    witch_adventure: Adventure,
) -> None:
    """Protect finite estate logistics, pact-state tactics, and parallel finale states."""
    encounter_index = witch_adventure.encounter_index()
    hall = encounter_index["blackbriar-hall"].content
    wood = encounter_index["crow-wood"].content
    underhall = encounter_index["underhall-of-the-hollow-feast"].content

    assert "## Hall response" in hall
    assert "## Areas" in hall
    assert "## Judith in her house" in hall
    assert "## Failure-forward outcomes" in hall
    assert "The living false shelter ledger" in hall
    assert "Corin Pike" in hall
    assert "Eda Lorn" in hall

    assert "## The marked-path rule" in wood
    assert "## The prisoner wagon" in wood
    assert "## Familiar messages" in wood
    assert "## Pursuit clock" in wood
    assert "Olla Pike" in wood
    assert "Thoughts do not travel by themselves" in wood

    assert "## The three feast components" in underhall
    assert "## Feast stages" in underhall
    assert "## Judith's capabilities by pact state" in underhall
    assert "## If Judith falls" in underhall
    assert "at least four controlled voices" in underhall
    assert "Neutralizing any two" in underhall
    assert "With two pacts severed, Judith is bodily mortal" in underhall

    operations = (EXAMPLE_DIRECTORY / "HALL-WOOD-AND-FEAST-OPERATIONS.md").read_text()
    assert "# Blackbriar Hall record" in operations
    assert "# Crow Wood record" in operations
    assert "# Judith's capability record" in operations
    assert "# Hollow Feast record" in operations
    assert "The common welcome remains while any two" in operations
    assert "Do not summarize the ending as a binary victory or defeat" in operations


def test_blackbriar_session_six_stress_tests_irregular_route_support(
    witch_adventure: Adventure,
) -> None:
    """Keep compact routes viable without making incomplete routes comprehensive."""
    clues_by_revelation = group_clues_by_revelation(witch_adventure.clues)

    routes = {
        "social": {
            "saint-orra-gallows",
            "sedge-croft",
            "saint-mercy-house",
            "chapel-of-the-free-witness",
            "blackbriar-hall",
            "underhall-of-the-hollow-feast",
        },
        "rescue-first": {
            "saint-orra-gallows",
            "sedge-croft",
            "saint-mercy-house",
            "crow-wood",
            "chapel-of-the-free-witness",
            "blackbriar-hall",
            "underhall-of-the-hollow-feast",
        },
        "pact-first": {
            "saint-orra-gallows",
            "sedge-croft",
            "chapel-of-the-free-witness",
            "burned-refuge",
            "white-pits",
            "moonless-mere",
            "blackbriar-hall",
            "underhall-of-the-hollow-feast",
        },
        "direct-assault": {
            "saint-orra-gallows",
            "blackbriar-hall",
            "underhall-of-the-hollow-feast",
        },
        "covert": {
            "saint-orra-gallows",
            "sedge-croft",
            "moonless-mere",
            "crow-wood",
            "blackbriar-hall",
            "underhall-of-the-hollow-feast",
        },
        "combat-heavy": {
            "saint-orra-gallows",
            "saint-mercy-house",
            "crow-wood",
            "blackbriar-hall",
            "underhall-of-the-hollow-feast",
        },
        "partial-information": {
            "saint-orra-gallows",
            "sedge-croft",
            "blackbriar-hall",
            "underhall-of-the-hollow-feast",
        },
    }

    support = {
        route_name: {
            revelation.id: sum(
                clue.source_encounter_id in route_encounters
                for clue in clues_by_revelation[revelation.id]
            )
            for revelation in witch_adventure.revelations
        }
        for route_name, route_encounters in routes.items()
    }

    assert min(support["social"].values()) == 2
    assert sum(count >= 3 for count in support["social"].values()) == 13
    assert min(support["rescue-first"].values()) == 2
    assert sum(count >= 3 for count in support["rescue-first"].values()) == 16
    assert min(support["pact-first"].values()) == 2
    assert sum(count >= 3 for count in support["pact-first"].values()) == 17

    direct_missing = {
        revelation_id for revelation_id, count in support["direct-assault"].items() if count == 0
    }
    assert direct_missing == {
        "the-white-pits-hold-the-plague-dead-judith-denied-burial",
    }
    assert sum(count == 1 for count in support["direct-assault"].values()) == 5
    assert sum(count >= 2 for count in support["covert"].values()) == 18
    assert sum(count >= 2 for count in support["combat-heavy"].values()) == 17
    assert not {
        revelation_id
        for revelation_id, count in support["partial-information"].items()
        if count == 0
    }


def test_blackbriar_session_six_bounds_routes_judith_and_retaliation(
    witch_adventure: Adventure,
) -> None:
    """Protect late-state persistence, one-body Judith, and bounded response rules."""
    operating = (EXAMPLE_DIRECTORY / "GM-OPERATING-SHEET.md").read_text()
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    resistance = (EXAMPLE_DIRECTORY / "PUBLIC-RESISTANCE-AND-RETALIATION.md").read_text()
    encounter_index = witch_adventure.encounter_index()


    for heading in (
        "## Adventure-turn loop",
        "## Never collapse these six states",
        "## Judith location board",
        "## Channel limits",
        "## One-major-response rule",
        "## Initial route branches",
        "## Route quick reference",
        "## Irregular-clue rule",
        "## Split-company board",
        "## Late and skipped encounter rule",
        "## Direct-assault procedure",
        "## Finale setup",
        "## Failure-forward ladder",
    ):
        assert heading in operating

    assert "## Knowledge, access, readiness, and control are separate" in design
    assert "## Judith has one body" in design
    assert "## Direct assault remains a real route" in design
    assert "## Uneven support is allowed to produce uneven knowledge" in design
    assert "## Completed work persists through retaliation" in design
    assert "## Judith's physical location and response budget" in resistance
    assert "## Channel ledger" in resistance
    assert "## Response persistence" in resistance
    assert "A split company does not multiply this budget" in resistance

    expected_late_headings = {
        "saint-orra-gallows": "## Route branches from the green",
        "sedge-croft": "## If the croft is reached late",
        "saint-mercy-house": "## If the house is reached late or skipped",
        "blackbriar-hall": "## Early or direct assault",
        "burned-refuge": "## If the refuge is reached late",
        "white-pits": "## If the pits are reached late",
        "chapel-of-the-free-witness": "## If the chapel is reached late",
        "moonless-mere": "## If the mere is reached late",
        "crow-wood": "## If Crow Wood is skipped or reached late",
        "underhall-of-the-hollow-feast": "## Arriving with partial knowledge",
    }
    for encounter_id, heading in expected_late_headings.items():
        assert heading in encounter_index[encounter_id].content

    assert (
        "Saint Mercy House cannot be emptied offstage by one order"
        in encounter_index["saint-mercy-house"].content
    )
    assert "The founding thirty-one cannot be removed" in encounter_index["white-pits"].content
    assert (
        "The Underhall remains physically legible"
        in encounter_index["underhall-of-the-hollow-feast"].content
    )
    assert "Judith has one body and bounded information" in witch_adventure.explanation


def test_blackbriar_generated_packet_matches_the_canonical_source(
    witch_adventure: Adventure,
) -> None:
    """Keep disposable rendered documents reproducible from the authored JSON."""
    report = validate_adventure(witch_adventure)
    rendered = render_adventure_documents(witch_adventure, report)

    assert_rendered_documents_match(
        rendered, EXAMPLE_DIRECTORY / "generated"
    )


def test_blackbriar_session_seven_journal_records_the_complete_demonstration(
    witch_adventure: Adventure,
    witch_state: PlayState,
) -> None:
    """Protect the named party, route, discoveries, misses, and durable outcomes."""
    projection = project_play_state(witch_adventure, witch_state)

    assert len(witch_state.events) == 200
    assert len(projection.sessions) == 4
    assert projection.active_session_number is None
    assert tuple(session.title for session in projection.sessions) == (
        "The Torch in Tomas's Hands",
        "The White House and the Red Road",
        "Three Debts Answered",
        "The Hollow Feast",
    )
    assert tuple(visit.encounter_id for visit in projection.visits) == (
        "saint-orra-gallows",
        "sedge-croft",
        "saint-mercy-house",
        "crow-wood",
        "blackbriar-hall",
        "chapel-of-the-free-witness",
        "burned-refuge",
        "white-pits",
        "moonless-mere",
        "underhall-of-the-hollow-feast",
    )
    assert len(projection.spotted_clue_ids) == 72
    assert sum(len(item.missed_visit_numbers) for item in projection.clue_progress) == 11
    assert all(item.is_established for item in projection.revelation_progress)
    assert len(projection.consequences) == 36
    assert not projection.corrections

    consequences = "\n".join(item.text for item in projection.consequences)
    assert "all seven current children and all seven current vessels" in consequences
    assert "The Guest in Ash pact is severed" in consequences
    assert "The Child Behind Glass pact is severed" in consequences
    assert "fully severing the Worm in White pact" in consequences
    assert "Judith Crowl dies after refusing surrender" in consequences
    assert "five active household claims" in consequences


def test_blackbriar_session_seven_archive_and_play_summary_are_reproducible(
    witch_adventure: Adventure,
    witch_state: PlayState,
) -> None:
    """Keep the pre-tag archive and generated play summary synchronized."""
    summary = render_play_summary(witch_adventure, witch_state)
    archived = load_journal_archive(EXAMPLE_ARCHIVE_PATH)

    assert summary == (EXAMPLE_DIRECTORY / "generated" / "05-play-summary.md").read_text()
    assert "Events recorded: 200" in summary
    assert "Explicit sessions: 4" in summary
    assert "Visits recorded: 10" in summary
    assert "Unique leads found: 72 / 95" in summary
    assert "The Blackbriar Commission" in summary
    assert archived.event_count == 200
    archived_encounters = archived.adventure_snapshot.encounter_index()
    current_without_references = replace(
        witch_adventure,
        tags=AdventureTags(),
        references=(),
        encounters=tuple(
            replace(
                encounter,
                content=archived_encounters[encounter.id].content,
                reference_links=(),
            )
            for encounter in witch_adventure.encounters
        ),
    )
    assert archived.adventure_snapshot == current_without_references
    assert archived.play_state == witch_state


def test_blackbriar_session_seven_completion_packet_is_consistent() -> None:
    """Protect the party, narrative, aftermath, audit, and completed build plan."""
    party = (EXAMPLE_DIRECTORY / "PARTY-DESIGN.md").read_text()
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()
    aftermath = (EXAMPLE_DIRECTORY / "AFTERMATH-AND-SURVIVING-CLAIMS.md").read_text()

    assert "# Demonstration Company: The Blackbriar Commission" in party
    for name in ("Sabren Holt", "Lysa Marrin", "Toma Brack", "Neris Kade"):
        assert f"## {name}" in party
    assert "# Full Playthrough: The Blackbriar Commission" in playthrough
    assert "## Session One: The Torch in Tomas's Hands" in playthrough
    assert "## Session Four: The Hollow Feast" in playthrough
    assert "She dies in the Underhall by her own refusal of capture" in playthrough
    assert "# Aftermath and Surviving Claims" in aftermath
    assert "## Seasonal states" in aftermath


def test_blackbriar_generated_packet_matches_source_and_completed_journal(
    witch_adventure: Adventure,
    witch_state: PlayState,
) -> None:
    """Keep all disposable documents reproducible after the demonstration."""
    report = validate_adventure(witch_adventure)
    rendered = render_adventure_documents(witch_adventure, report, witch_state)

    assert_rendered_documents_match(
        rendered, EXAMPLE_DIRECTORY / "generated"
    )


def test_blackbriar_session_eight_completes_the_voice_and_coherence_pass(
    witch_adventure: Adventure,
) -> None:
    """Protect the completed voice signatures, prose pass, and structural invariants."""
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()
    encounter_index = witch_adventure.encounter_index()
    revelation_index = witch_adventure.revelation_index()


    assert "each kindness has a receipt" in witch_adventure.synopsis
    assert "Her voice stays controlled and domestic" in witch_adventure.explanation
    assert "You call it coercion because I have named the payer" in (
        encounter_index["blackbriar-hall"].content
    )
    assert "At first light, Tomas places the unused torch" in playthrough

    assert (
        revelation_index["judith-crowl-is-the-witch-and-manufactured-the-prosecutions"].title
        == "Judith made the witches she condemned"
    )
    assert (
        revelation_index[
            "judith-spies-and-strikes-through-accepted-gifts-written-names-and-hearth-ash"
        ].title
        == "Judith's omniscience has carriers"
    )
    assert (
        revelation_index["the-hollow-feast-can-be-stopped-by-revoking-the-village-welcome"].title
        == "Break two feast components to end the common welcome"
    )


def test_blackbriar_second_look_coherence_repairs_causality_and_authority(
    witch_adventure: Adventure,
    witch_state: PlayState,
) -> None:
    """Keep the publication coherence repairs independent of demonstrated play."""
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    operating = (EXAMPLE_DIRECTORY / "GM-OPERATING-SHEET.md").read_text()
    ledger = (EXAMPLE_DIRECTORY / "BLACKBRIAR-VALE-LEDGER.md").read_text()
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()
    encounter_index = witch_adventure.encounter_index()
    revelation_index = witch_adventure.revelation_index()
    clue_index = witch_adventure.clue_index()


    gallows = encounter_index["saint-orra-gallows"]
    mercy = encounter_index["saint-mercy-house"].content
    underhall = encounter_index["underhall-of-the-hollow-feast"].content

    assert gallows.opening_view.startswith("First-light rain")
    assert "Ysra's original writ predates Mara's arrest" in gallows.content
    assert "two competing courier networks, not chance" in gallows.content
    assert "## The commission and later authority" in gallows.content
    assert "commits the feast clock" in gallows.content
    assert "Do not place her at Saint Mercy House and Blackbriar Hall at the same time" in (
        gallows.content
    )

    assert "Slow ownership is about to become public evidence" in witch_adventure.explanation
    assert "Forty-seven households display a blackthorn token" in witch_adventure.explanation
    assert "a vessel is not a voice" in witch_adventure.explanation
    assert "One company cannot personally complete ten large operations in sequence" in (
        witch_adventure.explanation
    )

    assert "vessels alone cannot form the captive choir" in mercy
    assert "at least four living, controlled children" in mercy
    assert "only doors with a surviving signature, token, stolen ash" in underhall
    assert "at least four controlled voices from living captives" in underhall
    assert "## Authority after the confrontation" in underhall

    feast = revelation_index["the-hollow-feast-will-be-completed-beneath-blackbriar-hall"]
    assert "at least two of the Mercy Book, token network" in feast.description
    assert "four-voice captive choir" in feast.description
    assert (
        "Join the accounts before they are read"
        in clue_index["the-locked-stair-marked-with-three-chairs"].description
    )
    assert (
        "advance Mara's burning to first light"
        in clue_index["order-to-strip-the-sedge-house"].description
    )

    assert "## Second-look causal chain" in design
    assert "## Commission authority" in operating
    assert "## Clock and delegated work" in operating
    assert "five have avoided both" in ledger
    assert "fewer than sixty-three active doors" in ledger
    assert "The session follows the commission at decisive handoffs" in playthrough

    assert len(witch_state.events) == 200
    assert len(witch_adventure.encounters) == 10
    assert len(witch_adventure.revelations) == 18
    assert len(witch_adventure.clues) == 95
    assert validate_adventure(witch_adventure).edge_connectivity == 4


def test_blackbriar_second_look_clue_density_adds_fresh_play_alternatives(
    witch_adventure: Adventure,
    witch_state: PlayState,
) -> None:
    """Keep the expanded matrix route-safe and independent of the demonstration."""
    clue_index = witch_adventure.clue_index()
    projection = project_play_state(witch_adventure, witch_state)


    expected_new_clues = {
        "the-three-chairs-answer-different-unfinished-duties",
        "copied-doors-answer-only-to-surviving-carriers",
        "restored-refuge-names-expose-the-ash-route",
        "the-mere-needs-an-index-before-it-shows-a-room",
        "audas-last-correction-names-door-roll-and-hearth",
        "caldus-suppressed-burial-form-has-three-required-lines",
        "judiths-disposal-manual-marks-three-failures-in-red",
        "the-glasswork-ledger-records-what-cold-breaking-steals",
        "a-returned-name-loosens-the-bay-before-the-vessel-breaks",
        "two-refused-debts-leave-the-witch-in-her-own-wounds",
        "the-midnight-transfer-order-separates-book-carriers-and-voices",
        "the-wrong-sky-fork-ignores-an-unmarked-traveler",
    }
    assert expected_new_clues <= clue_index.keys()
    assert all(clue_index[clue_id].revelation_id for clue_id in expected_new_clues)
    assert all(
        witch_adventure.revelation_index()[clue_index[clue_id].revelation_id].unlocks_encounter_id
        is None
        for clue_id in expected_new_clues
    )

    unseen = (
        set(clue_index)
        - set(projection.spotted_clue_ids)
        - {item.clue_id for item in projection.clue_progress if item.missed_visit_numbers}
    )
    assert unseen == expected_new_clues
    assert len(witch_adventure.clues) == 95
    assert len(projection.spotted_clue_ids) == 72
    assert sum(len(item.missed_visit_numbers) for item in projection.clue_progress) == 11
    assert validate_adventure(witch_adventure).edge_connectivity == 4


def test_blackbriar_encounter_introductions_one_records_live_pressure_baseline(
    witch_adventure: Adventure,
    witch_state: PlayState,
) -> None:
    """Keep the first-pass audit and unchanged structural baseline."""

    report = validate_adventure(witch_adventure)
    projection = project_play_state(witch_adventure, witch_state)
    assert report.is_valid
    assert report.edge_connectivity == 4
    assert len(witch_adventure.encounters) == 10
    assert len(witch_adventure.revelations) == 18
    assert len(witch_adventure.clues) == 95
    assert len(witch_state.events) == 200
    assert len(projection.spotted_clue_ids) == 72


def test_blackbriar_encounter_introductions_two_form_a_varied_villain_hunt(
    witch_adventure: Adventure,
    witch_state: PlayState,
) -> None:
    """Protect the compressed sequence, route discipline, and Voice I handoff."""
    encounters = witch_adventure.encounter_index()
    openings = [encounter.opening_view for encounter in witch_adventure.encounters]

    assert len(set(openings)) == 10
    assert sum(len(opening.split()) for opening in openings) == 784
    assert all(68 <= len(opening.split()) <= 90 for opening in openings)

    expected_phrases = {
        "saint-orra-gallows": "Captain Cleft says, “Three.”",
        "sedge-croft": "the cellar latch lifts once",
        "saint-mercy-house": "crates lined with red cord strike the floor",
        "blackbriar-hall": "sends Corin toward the undercroft",
        "burned-refuge": "The outer bar sinks deeper",
        "white-pits": "The barrel tips.",
        "chapel-of-the-free-witness": "One carries a fitted door",
        "moonless-mere": "for another person's name",
        "crow-wood": "A child's borrowed voice gives the wrong turn",
        "underhall-of-the-hollow-feast": "asks who has entered her home",
    }
    for encounter_id, phrase in expected_phrases.items():
        assert phrase in encounters[encounter_id].opening_view

    combined = "\n".join(openings)
    for demonstrator in (
        "Blackbriar Commission",
        "Sabren Holt",
        "Lysa Marrin",
        "Toma Brack",
        "Neris Kade",
    ):
        assert demonstrator not in combined


    report = validate_adventure(witch_adventure)
    projection = project_play_state(witch_adventure, witch_state)
    assert report.is_valid
    assert report.edge_connectivity == 4
    assert len(witch_adventure.encounters) == 10
    assert len(witch_adventure.revelations) == 18
    assert len(witch_adventure.clues) == 95
    assert len(witch_state.events) == 200
    assert len(projection.spotted_clue_ids) == 72
