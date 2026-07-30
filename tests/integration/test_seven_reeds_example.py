"""Regression checks for the Seven Reeds Imperial-court adventure."""

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
from tests.support.corpus_contracts import group_clues_by_revelation

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-mandate-of-seven-reeds")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"
EXAMPLE_PLAYTHROUGH_PATH = EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md"


@pytest.fixture(scope="module")
def seven_reeds_adventure() -> Adventure:
    """Load the developing political adventure once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def seven_reeds_state() -> PlayState:
    """Load the canonical Witnesses of the Broken Dike journal once."""
    return load_play_state(EXAMPLE_STATE_PATH)


def test_seven_reeds_session_seven_has_a_valid_court_structure(
    seven_reeds_adventure: Adventure,
) -> None:
    """Protect the completed source scale, necessity model, and resilience floor."""
    report = validate_adventure(seven_reeds_adventure)

    assert len(seven_reeds_adventure.encounters) == 15
    assert len(seven_reeds_adventure.revelations) == 44
    assert len(seven_reeds_adventure.clues) == 221
    assert {
        encounter.id for encounter in seven_reeds_adventure.encounters if not encounter.required
    } == {"evening-of-the-chrysanthemum-moon"}
    assert {item.id for item in seven_reeds_adventure.revelations if not item.required} == {
        "a-controlled-fallback-proposal-is-leverage-not-disloyalty",
        "the-moon-viewing-can-turn-private-bargains-into-public-obligations",
    }
    assert report.is_valid
    assert report.edge_connectivity == 4


def test_every_seven_reeds_revelation_has_independent_support(
    seven_reeds_adventure: Adventure,
) -> None:
    """Keep political conclusions discoverable through independent court routes."""
    clues_by_revelation = group_clues_by_revelation(seven_reeds_adventure.clues)

    for revelation in seven_reeds_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        assert len(clues) >= 3
        assert len({clue.source_encounter_id for clue in clues}) >= 3


def test_seven_reeds_session_two_completes_the_grain_and_sword_settlement(
    seven_reeds_adventure: Adventure,
) -> None:
    """Preserve the paired Harvest-Sword institutions and internal clan factions."""
    encounters = {encounter.id: encounter for encounter in seven_reeds_adventure.encounters}
    revelation_ids = {item.id for item in seven_reeds_adventure.revelations}

    crane = encounters["pavilion-of-first-rain"].content
    lion = encounters["hall-of-red-standards"].content

    assert len(crane.split()) >= 1_200
    assert len(lion.split()) >= 1_500
    assert "Daidoji Yorishige" in crane
    assert "Asahina Chiharu" in crane
    assert "Matsu Kiyoka" in lion
    assert "Ikoma Noritada" in lion
    assert "Seed rice" in crane
    assert "Demobilization as an ordered campaign" in lion
    assert {
        "a-written-supply-covenant-can-separate-readiness-from-control-of-granaries",
        "demobilization-must-be-a-sequence-of-obedience-and-replacement",
        "public-credit-can-settle-political-debt-without-granting-jurisdiction",
    } <= revelation_ids

    settlement = (EXAMPLE_DIRECTORY / "GRAIN-AND-SWORD-SETTLEMENT.md").read_text()
    assert "## Harvest clause matrix" in settlement
    assert "## Sword clause matrix" in settlement
    assert "## The demobilization sequence" in settlement
    assert "### Package A: Paired Imperial commissions" in settlement
    assert "### Package D: Emergency command, narrow Harvest" in settlement


def test_seven_reeds_session_three_completes_the_shrines_judgment_accounts_triangle(
    seven_reeds_adventure: Adventure,
) -> None:
    """Preserve the completed Phoenix-Dragon-Scorpion political subsystem."""
    encounters = {encounter.id: encounter for encounter in seven_reeds_adventure.encounters}
    revelation_ids = {item.id for item in seven_reeds_adventure.revelations}

    phoenix = encounters["shrine-of-listening-water"].content
    dragon = encounters["stone-and-moss-court"].content
    scorpion = encounters["theater-of-a-thousand-sleeves"].content

    assert len(phoenix.split()) >= 1_500
    assert len(dragon.split()) >= 1_400
    assert len(scorpion.split()) >= 1_500
    assert "Shiba Koremori" in phoenix
    assert "Asako Chise" in phoenix
    assert "Mirumoto Daizen" in dragon
    assert "Togashi Sorin" in dragon
    assert "Shosuro Mirei" in scorpion
    assert "Soshi Kureha" in scorpion
    assert "Four kinds of sacred claim" in phoenix
    assert "Recusal as a chain, not an absence" in dragon
    assert "The six powers hidden inside inspection" in scorpion
    assert {
        "sacred-consultation-needs-a-speaker-a-procedure-and-a-remedy",
        "recusal-without-substitute-jurisdiction-is-a-hidden-veto",
        "inspection-must-separate-access-preservation-reporting-and-sanction",
        "secrecy-may-protect-witnesses-but-not-final-authority-forever",
    } <= revelation_ids

    settlement = (EXAMPLE_DIRECTORY / "SHRINES-JUDGMENT-AND-ACCOUNTS.md").read_text()
    assert "## Shrines clause matrix" in settlement
    assert "## Judgment clause matrix" in settlement
    assert "## Accounts clause matrix" in settlement
    assert "## The sacred-consultation sequence" in settlement
    assert "## The recusal-and-appeal sequence" in settlement
    assert "## The inspection-and-secrecy sequence" in settlement
    assert "### Package D: Emergency reconstruction with retrospective teeth" in settlement


def test_seven_reeds_session_four_completes_roads_waters_and_burdens(
    seven_reeds_adventure: Adventure,
) -> None:
    """Preserve the completed Unicorn-Crab-Reedwater political subsystem."""
    encounters = {encounter.id: encounter for encounter in seven_reeds_adventure.encounters}
    revelation_ids = {item.id for item in seven_reeds_adventure.revelations}

    unicorn = encounters["courtyard-of-bells"].content
    crab = encounters["hall-of-joined-timbers"].content
    witnesses = encounters["guesthouse-of-the-bent-reed"].content

    assert len(unicorn.split()) >= 1_800
    assert len(crab.split()) >= 2_100
    assert len(witnesses.split()) >= 2_200
    assert "Shinjo Boroldai" in unicorn
    assert "Iuchi Nergui" in unicorn
    assert "Hida Chihaya" in crab
    assert "Yasuki Kameyo" in crab
    assert "Natsugawa Kenta" in witnesses
    assert "The requisition chain" in unicorn
    assert "One burden ledger" in crab
    assert "Standing that survives the audience" in witnesses
    assert {
        "requisition-must-create-a-valued-debt-before-it-consumes-the-next-season",
        "labor-levies-must-be-counted-across-offices-before-any-office-commands-another-day",
        "an-engineering-plan-is-a-political-allocation-of-risk-land-and-time",
        "emergency-works-must-name-who-may-sacrifice-a-district-and-who-must-answer-for-it",
        "provincial-standing-must-survive-drafting-into-implementation-and-review",
    } <= revelation_ids

    settlement = (EXAMPLE_DIRECTORY / "ROADS-WATERS-AND-BURDENS.md").read_text()
    assert "## Roads clause matrix" in settlement
    assert "## Waters clause matrix" in settlement
    assert "## The household burden ledger" in settlement
    assert "## The three levels of emergency authority" in settlement
    assert "## Provincial standing clause matrix" in settlement
    assert "### Package A: Imperial spine, clan execution" in settlement
    assert "### Package D: Distributed corridors and basins" in settlement


def test_seven_reeds_session_five_completes_public_obligation_and_stress_tests(
    seven_reeds_adventure: Adventure,
) -> None:
    """Preserve the completed moon-viewing procedures and route resilience audit."""
    encounters = {encounter.id: encounter for encounter in seven_reeds_adventure.encounters}
    revelations = {item.id: item for item in seven_reeds_adventure.revelations}

    moon = encounters["evening-of-the-chrysanthemum-moon"].content
    assert len(moon.split()) >= 3_000
    assert "Prepare no more than three public obligations" in moon
    assert "Four public obligations that must survive the garden" in moon
    assert "White keys beneath red standards" in moon
    assert "The road beside the new water" in moon
    assert "The mask before the open ledger" in moon
    assert "The empty cushion of succession" in moon
    assert "five forms" in moon.lower()
    assert "Skipping the evening remains valid" in moon

    session_five_ids = {
        "a-witnessed-concession-needs-scope-as-carefully-as-a-law",
        "a-gift-must-name-whether-it-repays-honors-transfers-custody-or-undertakes-duty",
        "seating-can-make-a-coalition-visible-without-making-it-permanent",
        "a-graceful-refusal-must-leave-a-lawful-path-open",
        "public-thanks-should-close-an-emergency-claim-not-renew-it",
        "every-public-bargain-must-name-the-third-parties-it-burdens",
    }
    assert session_five_ids <= revelations.keys()
    assert all(revelations[item_id].required for item_id in session_five_ids)

    clues_by_revelation = group_clues_by_revelation(seven_reeds_adventure.clues)
    for item_id in session_five_ids:
        clues = clues_by_revelation[item_id]
        assert len(clues) >= 5
        required_sources = {
            clue.source_encounter_id
            for clue in clues
            if encounters[clue.source_encounter_id].required
        }
        assert len(required_sources) >= 4

    aid = (EXAMPLE_DIRECTORY / "MOON-VIEWING-AND-PUBLIC-OBLIGATION.md").read_text()
    assert "## Ceremonial instrument matrix" in aid
    assert "## Ceremonial docket" in aid
    assert "## Public obligation ledger" in aid
    assert "## Refusal ladder" in aid
    assert "## Cross-clan bargain dependency matrix" in aid
    assert "## Skipping the event" in aid


    unlock_revelation_by_encounter = {
        item.unlocks_encounter_id: item.id
        for item in seven_reeds_adventure.revelations
        if item.unlocks_encounter_id is not None
    }
    clue_sources_by_revelation: defaultdict[str, set[str]] = defaultdict(set)
    for clue in seven_reeds_adventure.clues:
        clue_sources_by_revelation[clue.revelation_id].add(clue.source_encounter_id)

    routes = [
        [
            "hall-of-the-chrysanthemum-throne",
            "ministry-of-divided-ink",
            "garden-of-white-gravel",
            "hall-of-open-roads",
            "pavilion-of-first-rain",
            "hall-of-red-standards",
            "shrine-of-listening-water",
            "stone-and-moss-court",
            "theater-of-a-thousand-sleeves",
            "courtyard-of-bells",
            "hall-of-joined-timbers",
            "guesthouse-of-the-bent-reed",
            "chamber-of-seven-reeds",
            "the-second-audience",
        ],
        [
            "hall-of-the-chrysanthemum-throne",
            "pavilion-of-first-rain",
            "hall-of-red-standards",
            "garden-of-white-gravel",
            "ministry-of-divided-ink",
            "hall-of-open-roads",
            "hall-of-joined-timbers",
            "shrine-of-listening-water",
            "courtyard-of-bells",
            "guesthouse-of-the-bent-reed",
            "stone-and-moss-court",
            "theater-of-a-thousand-sleeves",
            "chamber-of-seven-reeds",
            "the-second-audience",
        ],
        [
            "hall-of-the-chrysanthemum-throne",
            "hall-of-open-roads",
            "courtyard-of-bells",
            "guesthouse-of-the-bent-reed",
            "hall-of-joined-timbers",
            "shrine-of-listening-water",
            "stone-and-moss-court",
            "ministry-of-divided-ink",
            "theater-of-a-thousand-sleeves",
            "garden-of-white-gravel",
            "pavilion-of-first-rain",
            "hall-of-red-standards",
            "chamber-of-seven-reeds",
            "the-second-audience",
        ],
        [
            "hall-of-the-chrysanthemum-throne",
            "ministry-of-divided-ink",
            "stone-and-moss-court",
            "theater-of-a-thousand-sleeves",
            "shrine-of-listening-water",
            "garden-of-white-gravel",
            "hall-of-open-roads",
            "pavilion-of-first-rain",
            "hall-of-red-standards",
            "courtyard-of-bells",
            "hall-of-joined-timbers",
            "guesthouse-of-the-bent-reed",
            "chamber-of-seven-reeds",
            "the-second-audience",
        ],
    ]
    for route in routes:
        assert "evening-of-the-chrysanthemum-moon" not in route
        visited = {route[0]}
        for encounter_id in route[1:]:
            revelation_id = unlock_revelation_by_encounter[encounter_id]
            assert clue_sources_by_revelation[revelation_id] & visited
            visited.add(encounter_id)


def test_seven_reeds_checked_in_packet_matches_source_and_journal(
    seven_reeds_adventure: Adventure,
    seven_reeds_state: PlayState,
) -> None:
    """Keep the completed packet synchronized and free of authoring placeholders."""
    report = validate_adventure(seven_reeds_adventure)
    documents = render_adventure_documents(
        seven_reeds_adventure,
        report,
        seven_reeds_state,
    )

    assert set(documents) >= {
        "00-overview.md",
        "01-encounter-index.md",
        "02-clue-list.md",
        "03-revelation-list.md",
        "04-validation-report.md",
        "05-play-summary.md",
    }
    assert len([name for name in documents if name.startswith("encounters/")]) == 15
    assert len(documents) == 40
    assert "Result: PASS" in documents["04-validation-report.md"]
    assert "Explicit sessions: 7" in documents["05-play-summary.md"]
    assert "Corrections recorded: 1" in documents["05-play-summary.md"]

    for content in documents.values():
        assert "full session-" not in content.lower()
    assert_rendered_documents_match(documents, EXAMPLE_DIRECTORY / "generated")


def test_seven_reeds_session_six_completes_drafting_and_imperial_judgment(
    seven_reeds_adventure: Adventure,
) -> None:
    """Preserve complete clauses, submissions, amendments, and durable outcomes."""
    encounters = {encounter.id: encounter for encounter in seven_reeds_adventure.encounters}
    revelations = {item.id: item for item in seven_reeds_adventure.revelations}

    chamber = encounters["chamber-of-seven-reeds"].content
    audience = encounters["the-second-audience"].content

    assert len(chamber.split()) >= 3_000
    assert len(audience.split()) >= 3_000
    assert "Five documents, one chain of provincial command" in chamber
    assert "The ten-part clause test" in chamber
    assert "Drafting in six passes" in chamber
    assert "Amendment discipline" in chamber
    assert "Two executable provincial governments" in chamber
    assert "Preparing acts of submission" in chamber
    assert "first forty days" in chamber.lower()
    assert "Order before dispatch" in audience
    assert "The Emperor's questions" in audience
    assert "The acts of submission" in audience
    assert "Amendment from the throne" in audience
    assert "Six durable outcomes" in audience
    assert "The Imperial Spine" in audience
    assert "The Narrow Imperial Peace" in audience

    session_six_ids = {
        "a-clause-is-not-complete-until-authority-burden-remedy-and-record-travel-together",
        "a-material-amendment-reopens-every-dependent-promise",
        "submission-must-transfer-command-custody-and-records-not-only-symbols",
        "adoption-needs-first-day-orders-resources-and-petition-routes",
        "imperial-judgment-tests-dangerous-combinations-and-failure-paths-not-endorsement-counts",
        "a-review-without-power-to-renew-narrow-replace-or-remedy-is-only-ceremony",
    }
    assert session_six_ids <= revelations.keys()
    assert all(revelations[item_id].required for item_id in session_six_ids)

    clues_by_revelation = group_clues_by_revelation(seven_reeds_adventure.clues)
    for item_id in session_six_ids:
        clues = clues_by_revelation[item_id]
        assert len(clues) >= 5
        assert len({clue.source_encounter_id for clue in clues}) == len(clues)

    aid = (EXAMPLE_DIRECTORY / "DRAFTING-AND-IMPERIAL-JUDGMENT.md").read_text()
    assert "## The settlement stack" in aid
    assert "## Universal clause matrix" in aid
    assert "## Reed-by-Reed drafting matrix" in aid
    assert "## Amendment classification" in aid
    assert "## Primary and fallback comparison" in aid
    assert "## Submission register" in aid
    assert "## Imperial question sequence" in aid
    assert "## First-forty-days implementation sheet" in aid
    assert "## Six outcome architectures" in aid
    assert "## Final consistency audit" in aid


def test_seven_reeds_session_seven_demonstrates_a_complete_political_run(
    seven_reeds_adventure: Adventure,
    seven_reeds_state: PlayState,
) -> None:
    """Preserve the named demonstration, fixed route, journal surfaces, and chosen outcome."""
    projection = project_play_state(seven_reeds_adventure, seven_reeds_state)
    visited = tuple(visit.encounter_id for visit in projection.visits)
    progress = projection.revelation_progress_index()

    assert visited == (
        "hall-of-the-chrysanthemum-throne",
        "hall-of-open-roads",
        "courtyard-of-bells",
        "guesthouse-of-the-bent-reed",
        "pavilion-of-first-rain",
        "hall-of-red-standards",
        "shrine-of-listening-water",
        "hall-of-joined-timbers",
        "garden-of-white-gravel",
        "ministry-of-divided-ink",
        "theater-of-a-thousand-sleeves",
        "stone-and-moss-court",
        "evening-of-the-chrysanthemum-moon",
        "chamber-of-seven-reeds",
        "the-second-audience",
    )
    assert len(seven_reeds_state.events) == 288
    assert len(seven_reeds_state.active_events) == 286
    assert len(projection.sessions) == 7
    assert [session.title for session in projection.sessions] == [
        "The Bare Mat",
        "The Court Outside the Court",
        "White Keys and Red Standards",
        "The Price of the Dike",
        "Masks, Ledgers, and the Judge Who Leaves",
        "Moonlight and Ink",
        "The Broad Sheet",
    ]
    assert all(not session.is_active for session in projection.sessions)
    assert len(projection.spotted_clue_ids) == 142
    assert len([item for item in projection.clue_progress if item.missed_visit_numbers]) == 10
    assert len(seven_reeds_adventure.clues) - len(projection.spotted_clue_ids) == 79
    assert all(progress[item.id].is_established for item in seven_reeds_adventure.revelations)
    assert set(projection.available_encounter_ids) == {
        encounter.id for encounter in seven_reeds_adventure.encounters
    }
    assert len(projection.consequences) == 15
    assert len(projection.corrections) == 1
    assert projection.corrections[0].target_operation_number == 95
    assert progress["a-controlled-fallback-proposal-is-leverage-not-disloyalty"].reopening_sequences
    assert any(
        consequence.encounter_id == "chamber-of-seven-reeds"
        and "Hundred-Day Brace" in consequence.text
        and "phase-two burden review" in consequence.text
        for consequence in projection.consequences
    )
    assert any(
        consequence.encounter_id == "the-second-audience"
        and "adopted with named amendments" in consequence.text
        for consequence in projection.consequences
    )


def test_seven_reeds_party_playthrough_and_audit_align_with_the_journal(
    seven_reeds_adventure: Adventure,
    seven_reeds_state: PlayState,
) -> None:
    """Keep the completion documents aligned with the executable event record."""
    party = (EXAMPLE_DIRECTORY / "PARTY-DESIGN.md").read_text()
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text()

    for name in (
        "Doji Kiyoe",
        "Akodo Naritomo",
        "Kitsuki Sadae",
        "Kaiu Masami",
        "Ide Qulan",
    ):
        assert name in party
        assert name in playthrough

    required_text = [
        "Throne -> Miya -> Unicorn -> Witnesses -> Crane -> Lion -> Phoenix -> Crab",
        "Reedwater Succession under the Hundred-Day Brace",
        "The current fallback has been politically foreclosed",
        "The GM reopens the fallback conclusion",
        "The mistaken operation is voided rather than silently rewritten",
        "No holder shall make its own failure",
        "The Emperor adopts the primary with the transition amendment",
    ]
    assert all(text in playthrough for text in required_text)

    summary = render_play_summary(seven_reeds_adventure, seven_reeds_state)
    assert "Explicit sessions: 7" in summary
    assert "Visits recorded: 15" in summary
    assert "Unique leads found: 142 / 221" in summary
    assert "### Established Revelations" in summary
    assert "### Outstanding Necessary Revelations\n\n- None." in summary
    assert "Corrections recorded: 1" in summary


def test_seven_reeds_session_eight_completes_voice_without_structural_drift(
    seven_reeds_adventure: Adventure,
    seven_reeds_state: PlayState,
) -> None:
    """Preserve the final voice standard and the proven political structure."""
    encounters = {encounter.id: encounter for encounter in seven_reeds_adventure.encounters}
    revelations = {item.id: item for item in seven_reeds_adventure.revelations}

    assert len(encounters) == 15
    assert len(revelations) == 44
    assert len(seven_reeds_adventure.clues) == 221
    assert len(seven_reeds_state.events) == 288
    assert all(encounter.summary.strip() for encounter in encounters.values())
    assert all(encounter.opening_view.strip() for encounter in encounters.values())
    assert len({encounter.opening_view for encounter in encounters.values()}) == 15

    assert (
        "seven water-darkened tablets"
        in encounters["hall-of-the-chrysanthemum-throne"].opening_view.lower()
    )
    assert "one flawless ceremonial beam" in encounters["hall-of-joined-timbers"].opening_view
    assert "orders leave the palace ahead of the weather" in (
        EXAMPLE_PLAYTHROUGH_PATH.read_text().lower()
    )
    assert (
        revelations["a-material-amendment-reopens-every-dependent-promise"].title
        == "A material amendment reopens its promises"
    )
    assert (
        revelations[
            "imperial-judgment-tests-dangerous-combinations-and-failure-paths-not-endorsement-counts"
        ].title
        == "The Emperor tests failure, not applause"
    )


def test_seven_reeds_second_look_repairs_commission_and_field_transfer(
    seven_reeds_adventure: Adventure,
    seven_reeds_state: PlayState,
) -> None:
    """Keep the publication coherence repairs independent of the demonstration."""
    encounters = {encounter.id: encounter for encounter in seven_reeds_adventure.encounters}
    clues = {clue.id: clue for clue in seven_reeds_adventure.clues}
    source_text = EXAMPLE_PATH.read_text()

    assert len(seven_reeds_adventure.encounters) == 15
    assert len(seven_reeds_adventure.revelations) == 44
    assert len(seven_reeds_adventure.clues) == 221
    assert len(seven_reeds_state.events) == 288

    throne = encounters["hall-of-the-chrysanthemum-throne"].content
    roads = encounters["hall-of-open-roads"].content
    garden = encounters["garden-of-white-gravel"].content
    audience = encounters["the-second-audience"].content

    assert "seal-bearing chief clerks" in throne
    assert "narrow commissions" in throne
    assert "grants no command in Reedwater" in throne
    assert "What the commission can and cannot command" in throne
    assert "The two-copy transition ledger" in roads
    assert "Submission at distance" in garden
    assert "court instrument and a field counterpart" in audience
    assert (
        "receiving field officer"
        in clues["the-effective-hour-in-the-submission-register"].description
    )

    for name in (
        "Doji Kiyoe",
        "Akodo Naritomo",
        "Kitsuki Sadae",
        "Kaiu Masami",
        "Ide Qulan",
    ):
        assert name not in source_text


def test_seven_reeds_second_look_adds_irregular_operational_density(
    seven_reeds_adventure: Adventure,
    seven_reeds_state: PlayState,
) -> None:
    """Keep the additive density repair uneven, route-safe, and journal-independent."""
    clues_by_revelation = group_clues_by_revelation(seven_reeds_adventure.clues)
    clues_by_encounter = Counter(
        clue.source_encounter_id for clue in seven_reeds_adventure.clues
    )

    assert Counter(len(clues) for clues in clues_by_revelation.values()) == {
        3: 2,
        4: 11,
        5: 22,
        6: 3,
        7: 5,
        8: 1,
    }
    assert sorted(clues_by_encounter.values()) == [
        6,
        8,
        10,
        12,
        12,
        13,
        13,
        16,
        16,
        17,
        18,
        19,
        20,
        20,
        21,
    ]

    added_ids = {
        "kentas-two-names-beneath-each-reed",
        "the-two-surrenders-announced-as-one-peace",
        "the-shrine-clause-with-four-visible-debts",
        "masashiges-clause-read-against-the-work-yard",
        "the-emperors-question-in-the-bare-margin",
        "kazetadas-inventory-of-powers-that-do-not-fit-in-a-box",
        "the-reedwater-copy-that-waits-for-acknowledgment",
        "the-first-patrol-order-after-the-standard-lowers",
        "the-first-granary-release-after-the-keys-change-hands",
        "shuns-correction-tree-for-one-changed-date",
        "the-garrison-term-that-reopens-rice-and-relief",
        "the-village-that-performs-the-courts-sacred-compromise",
        "the-villages-beneath-the-declining-roster",
        "the-seed-fields-on-the-water-design",
        "the-road-days-lost-to-each-line-of-water",
        "the-reedwater-receipt-entered-beside-the-imperial-seal",
        "harunoris-review-that-can-change-the-order",
        "the-road-clearance-that-proves-a-garrison-has-left",
    }
    clue_ids = {clue.id for clue in seven_reeds_adventure.clues}
    projection = project_play_state(seven_reeds_adventure, seven_reeds_state)
    report = validate_adventure(seven_reeds_adventure)

    assert added_ids <= clue_ids
    assert added_ids.isdisjoint(projection.spotted_clue_ids)
    assert report.is_valid
    assert report.edge_connectivity == 4


def test_seven_reeds_encounter_introductions_two_form_a_court_progression(
    seven_reeds_adventure: Adventure,
    seven_reeds_state: PlayState,
) -> None:
    """Protect the compressed sequence, distinct engines, and Voice I handoff."""
    encounters = {encounter.id: encounter for encounter in seven_reeds_adventure.encounters}
    openings = [encounter.opening_view for encounter in seven_reeds_adventure.encounters]

    assert len(encounters) == 15
    assert len(set(openings)) == 15
    assert sum(len(opening.split()) for opening in openings) == 990
    assert all(62 <= len(opening.split()) <= 69 for opening in openings)

    expected_phrases = {
        "hall-of-the-chrysanthemum-throne": "which present power must yield",
        "ministry-of-divided-ink": "The fourth scribe has nothing to write.",
        "garden-of-white-gravel": "The contradiction must travel farther than the ceremony",
        "hall-of-open-roads": "The road has begun editing the court.",
        "pavilion-of-first-rain": "the hunger moves with it",
        "hall-of-red-standards": "protection can change hands",
        "shrine-of-listening-water": "a remedy for being overruled",
        "stone-and-moss-court": "Dusk will not recuse itself.",
        "theater-of-a-thousand-sleeves": "have not yet agreed on an entrance",
        "courtyard-of-bells": "no wheel has received lawful priority",
        "hall-of-joined-timbers": "The river tests the arithmetic, not the seal.",
        "guesthouse-of-the-bent-reed": "whether or not the court has finished listening",
        "evening-of-the-chrysanthemum-moon": "beautiful enough to become dangerous",
        "chamber-of-seven-reeds": "Both complete proposals have just become drafts again.",
        "the-second-audience": "which order leaves before the court disperses",
    }
    for encounter_id, phrase in expected_phrases.items():
        assert phrase in encounters[encounter_id].opening_view

    report = validate_adventure(seven_reeds_adventure)
    projection = project_play_state(seven_reeds_adventure, seven_reeds_state)
    assert report.is_valid
    assert report.edge_connectivity == 4
    assert len(seven_reeds_adventure.clues) == 221
    assert len(seven_reeds_state.events) == 288
    assert len(projection.spotted_clue_ids) == 142


def test_seven_reeds_voice_one_restores_named_court_agency(
    seven_reeds_adventure: Adventure,
    seven_reeds_state: PlayState,
) -> None:
    """Protect the source-level voice pass and its structural boundaries."""
    encounters = {encounter.id: encounter for encounter in seven_reeds_adventure.encounters}
    report = validate_adventure(seven_reeds_adventure)
    measured_source = "\n".join(
        [
            seven_reeds_adventure.synopsis,
            seven_reeds_adventure.premise,
            seven_reeds_adventure.explanation,
        ]
        + [
            text
            for encounter in seven_reeds_adventure.encounters
            for text in (encounter.summary, encounter.content)
        ]
    )

    assert "the party" not in measured_source.lower()
    assert "The Emperor names the adventurers Witnesses of the Broken Dike" in (
        seven_reeds_adventure.synopsis
    )
    assert "inconveniently cross-cutting" in seven_reeds_adventure.premise
    assert "The Witnesses recommend and draft; the Throne adopts." in (
        seven_reeds_adventure.explanation
    )
    assert all(encounter.summary.strip() for encounter in encounters.values())
    assert sum(len(encounter.opening_view.split()) for encounter in encounters.values()) == 990
    assert "Kazetada cuts each Reed" in encounters["ministry-of-divided-ink"].summary
    assert "Shun sends every elegant clause across a broken bridge" in (
        encounters["hall-of-open-roads"].summary
    )
    assert "Masashige demands authority equal to the work" in (
        encounters["hall-of-joined-timbers"].summary
    )
    assert "The Imperial Spine strongly restores Imperial authorship" in (
        encounters["the-second-audience"].content
    )

    assert len(seven_reeds_adventure.encounters) == 15
    assert len(seven_reeds_adventure.revelations) == 44
    assert len(seven_reeds_adventure.clues) == 221
    assert len(seven_reeds_state.events) == 288
    assert report.is_valid
    assert report.edge_connectivity == 4


