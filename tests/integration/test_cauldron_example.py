# ruff: noqa: RUF001 -- exact authored prose retains typographic punctuation.
"""Regression checks for the completed and voice-audited cauldron heist."""

from __future__ import annotations

from collections import Counter, defaultdict
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
    assert_deprecated_editorial_phrases_absent,
    assert_editorial_phrase_locks,
    assert_rendered_documents_match,
    assert_semantic_concepts,
    group_clues_by_revelation,
)

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-cauldron-of-nine-silences")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"


@pytest.fixture(scope="module")
def cauldron_adventure() -> Adventure:
    """Load the heist source once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def cauldron_state() -> PlayState:
    """Load the canonical Unsworn Hand journal once per module."""
    return load_play_state(STATE_PATH)


def test_cauldron_session_seven_has_the_intended_short_heist_shape(
    cauldron_adventure: Adventure,
) -> None:
    """Protect the compact scale, roles, optional solar, and resilience floor."""
    report = validate_adventure(cauldron_adventure)

    assert len(cauldron_adventure.encounters) == 10
    assert len(cauldron_adventure.revelations) == 41
    assert len(cauldron_adventure.clues) == 150
    assert {encounter.id for encounter in cauldron_adventure.encounters if encounter.start} == {
        "crooked-magpie"
    }
    assert {encounter.id for encounter in cauldron_adventure.encounters if encounter.end} == {
        "reed-weir"
    }
    assert {
        encounter.id for encounter in cauldron_adventure.encounters if not encounter.required
    } == {"widows-solar"}
    assert {item.id for item in cauldron_adventure.revelations if not item.required} == {
        "the-widows-solar-holds-the-founders-seal",
        "the-green-larks-enter-at-the-third-bell",
        "the-great-muster-apparatus-can-be-delayed-by-mismatched-components",
    }
    assert report.is_valid
    assert report.edge_connectivity is not None
    assert report.edge_connectivity >= 3
    assert not [issue for issue in report.issues if issue.severity == "error"]
    titles = {item.title for item in cauldron_adventure.revelations}
    assert "Wax admits paper; a witness admits a person" in titles
    assert "The stair records words, not hearts" in titles
    assert "The Nine Hearths claim a circuit, not a throne" in titles


def test_every_cauldron_revelation_has_independent_support(
    cauldron_adventure: Adventure,
) -> None:
    """Keep all conclusions discoverable from at least three regions."""
    clues_by_revelation = group_clues_by_revelation(cauldron_adventure.clues)

    for revelation in cauldron_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        assert len(clues) >= 3
        assert len({clue.source_encounter_id for clue in clues}) == len(clues)


def test_cauldron_second_look_makes_clue_density_irregular_without_changing_routes(
    cauldron_adventure: Adventure,
) -> None:
    """Protect the additive non-route rebalance and its exact support profile."""
    support = Counter(clue.revelation_id for clue in cauldron_adventure.clues)
    source_counts: defaultdict[str, set[str]] = defaultdict(set)
    for clue in cauldron_adventure.clues:
        source_counts[clue.revelation_id].add(clue.source_encounter_id)

    assert Counter(support.values()) == Counter({4: 20, 3: 18, 5: 2, 6: 1})
    assert Counter(len(items) for items in source_counts.values()) == Counter(
        {4: 20, 3: 18, 5: 2, 6: 1}
    )

    encounter_counts = Counter(clue.source_encounter_id for clue in cauldron_adventure.clues)
    assert min(encounter_counts.values()) == 9
    assert max(encounter_counts.values()) == 22

    added_ids = {clue.id for clue in cauldron_adventure.clues if "second-look" in clue.id}
    assert len(added_ids) == 18
    assert all(
        cauldron_adventure.revelation_index()[clue.revelation_id].unlocks_encounter_id is None
        for clue in cauldron_adventure.clues
        if clue.id in added_ids
    )


def test_cauldron_second_look_openings_form_a_table_ready_heist_sequence(
    cauldron_adventure: Adventure,
) -> None:
    """Protect both introduction passes without turning openings into solutions."""
    encounters = cauldron_adventure.encounter_index()

    expected_fragments = {
        "crooked-magpie": "The rain reaches the ring before Gwyne Marr does.",
        "white-hart-court": "Mael rehearses Branoc’s command before Branoc has spoken.",
        "smoke-kitchens": "Three hundred plates. Nine copper combs",
        "rookwalk": "The brass-ringed rook screams at the lantern, not at you.",
        "chapel-last-word": "“Last,” says the darkness beneath the font.",
        "widows-solar": "One candle serves two unfinished plans",
        "barrow-stair": "It is already taking down your words.",
        "house-borrowed-voices": "the keep begins obeying them.",
        "cauldron-vault": "The fifth bell has not sounded. The cauldron is ready anyway.",
        "reed-weir": "The tide has begun taking the road back.",
    }

    assert set(expected_fragments) == set(encounters)
    assert len({encounter.opening_view for encounter in encounters.values()}) == 10
    for encounter_id, fragment in expected_fragments.items():
        opening = encounters[encounter_id].opening_view
        assert fragment in opening
        assert 55 <= len(opening.split()) <= 65


def test_cauldron_second_look_voice_i_trusts_material_procedure(
    cauldron_adventure: Adventure,
) -> None:
    """Protect the source-level voice pass without changing the heist structure."""
    encounters = cauldron_adventure.encounter_index()

    assert cauldron_adventure.synopsis.startswith(
        "After Red Fen killed or scattered a third of the vale's field command"
    )
    assert cauldron_adventure.premise.endswith("before law hardens and the dead are diminished.")
    assert "Their claim is rival custody, not a second commission." in (
        cauldron_adventure.explanation
    )

    expected_summaries = {
        "crooked-magpie": "A ruined tide-road tavern offers Branoc's ring",
        "white-hart-court": "Mael turns hospitality, memorial rolls",
        "smoke-kitchens": "Soot, tallies, serving bells",
        "rookwalk": "Broken chains and message rooks",
        "chapel-last-word": "Caddoc's chapel can authenticate Branoc",
        "widows-solar": "Aderyn holds founder authority",
        "barrow-stair": "Three stone mouths record",
        "house-borrowed-voices": "Twelve accurate answers without remembered purposes",
        "cauldron-vault": "The target is a rite, a six-mark load",
        "reed-weir": "The tide road forces vessel, anchor, testimony",
    }
    for encounter_id, phrase in expected_summaries.items():
        assert encounters[encounter_id].summary.startswith(phrase)

    semantic_contracts = {
        "crooked-magpie": {
            "the heist follows a bounded lawful offer": (
                ("heist",),
                ("bounded", "limited"),
                ("lawful offer", "lawful bargain"),
            )
        },
        "white-hart-court": {
            "silence is not treated as freely available": (
                ("silent", "silence"),
                ("free", "freely"),
            )
        },
        "smoke-kitchens": {
            "intrusion must assume a working role": (
                ("intrusion", "intruder"),
                ("job", "work", "role"),
            )
        },
        "rookwalk": {
            "the route extracts an explicit price": (
                ("rookwalk",),
                ("buying", "price", "cost"),
            )
        },
        "chapel-last-word": {
            "Caddoc names defense without seeking absolution": (
                ("defense",),
                ("absolution", "forgiveness"),
            )
        },
        "barrow-stair": {
            "the stair is tracked through posture": (
                ("stair",),
                ("posture", "stance"),
            )
        },
        "house-borrowed-voices": {
            "the shutters externalize changing state": (
                ("shutter",),
                ("moving", "move"),
            )
        },
        "cauldron-vault": {
            "infiltration becomes responsibility at the target": (
                ("infiltration",),
                ("responsibility", "custody"),
            )
        },
        "reed-weir": {
            "the exit procedure asks four questions": (
                ("four",),
                ("ask", "question"),
            )
        },
    }
    for encounter_id, concepts in semantic_contracts.items():
        assert_semantic_concepts(encounters[encounter_id].content, concepts)
    assert_editorial_phrase_locks(
        encounters["widows-solar"].content,
        ("The Solar buys what flight alone cannot",),
    )

    combined_bodies = "\n".join(encounter.content for encounter in cauldron_adventure.encounters)
    assert_deprecated_editorial_phrases_absent(
        combined_bodies,
        (
            "The timing rests on three facts, all of which the crew should understand",
            "The House should behave like an adversarial planning scene",
            "The stair supports more than one correct solution",
            "This is a sound outcome for a crew unable to move the target",
            "Use **burden marks** as planning language, not a universal encumbrance rule",
        ),
    )


def test_cauldron_second_look_voice_ii_reconciles_live_records(
    cauldron_adventure: Adventure,
) -> None:
    """Protect the final source cadence and completed cross-file record."""
    encounters = cauldron_adventure.encounter_index()

    assert "End planning when the crew commits" in encounters["crooked-magpie"].content
    assert "A failed witness seats the crew" in encounters["white-hart-court"].content
    assert "A fall sends someone onto the sloped gatehouse roof" in encounters["rookwalk"].content
    assert "The Solar buys what flight alone cannot" in encounters["widows-solar"].content
    assert "consent does not make the loss neutral" in encounters["cauldron-vault"].content
    assert "The route favors witnessed seizure" in encounters["reed-weir"].content
    assert "This is a strong partial victory" not in encounters["reed-weir"].content


def test_cauldron_session_seven_fully_drafts_the_opening_underkeep_and_vault(
    cauldron_adventure: Adventure,
) -> None:
    """Keep the planning, premise hinges, and underkeep regions table-usable."""
    encounters = cauldron_adventure.encounter_index()

    for encounter_id, minimum_words in {
        "crooked-magpie": 1400,
        "white-hart-court": 1000,
        "smoke-kitchens": 750,
        "rookwalk": 550,
        "chapel-last-word": 1100,
        "widows-solar": 800,
        "barrow-stair": 1800,
        "house-borrowed-voices": 3000,
        "cauldron-vault": 5000,
        "reed-weir": 3400,
    }.items():
        assert len(encounters[encounter_id].content.split()) >= minimum_words

    assert "## Why tonight" in encounters["crooked-magpie"].content
    assert "## The second-bell declaration" in encounters["white-hart-court"].content
    assert "### The serving bells" in encounters["smoke-kitchens"].content
    assert "**The lifting tower.**" in encounters["rookwalk"].content
    assert "## The Full Asking" in encounters["chapel-last-word"].content
    assert "## Aderyn's position" in encounters["widows-solar"].content
    assert "## The Landing of Name" in encounters["barrow-stair"].content
    assert "## The Landing of Asking" in encounters["barrow-stair"].content
    assert "## The Landing of Keeping" in encounters["barrow-stair"].content
    assert "## The twelve borrowed answers" in encounters["house-borrowed-voices"].content
    assert "## Recovered reasons and release" in encounters["house-borrowed-voices"].content
    assert "## The command table" in encounters["house-borrowed-voices"].content
    assert "## The nine bands" in encounters["cauldron-vault"].content
    assert "## Conducting the Full Asking" in encounters["cauldron-vault"].content
    assert "## Branoc's answer" in encounters["cauldron-vault"].content
    assert "## The one-night respite" in encounters["cauldron-vault"].content
    assert "## Principal resolutions" in encounters["cauldron-vault"].content
    assert "## Restoration after loss" in encounters["cauldron-vault"].content
    assert "## The tide in four states" in encounters["reed-weir"].content
    assert "## The Nine Hearth claim" in encounters["reed-weir"].content
    assert "## Pursuit as four objectives" in encounters["reed-weir"].content
    assert "## Other exits" in encounters["reed-weir"].content
    assert "## Failure that preserves consequence" in encounters["reed-weir"].content
    assert "## Immediate aftermath before dawn" in encounters["reed-weir"].content


def test_cauldron_session_seven_preserves_the_rebuilt_causal_premise(
    cauldron_adventure: Adventure,
) -> None:
    """Prevent the discarded return premise or a prior Branoc summoning from returning."""
    combined = "\n".join(
        [
            cauldron_adventure.synopsis,
            cauldron_adventure.premise,
            cauldron_adventure.explanation,
            *(encounter.content for encounter in cauldron_adventure.encounters),
            *(f"{item.title}: {item.description}" for item in cauldron_adventure.revelations),
            *(clue.description for clue in cauldron_adventure.clues),
        ]
    )
    lowered = combined.lower()

    assert "branoc has never been summoned" in lowered
    assert "first full asking" in lowered
    assert "great muster" in lowered
    assert "gate compact" in lowered
    assert "what command did you give edric taran at the western gate" in lowered
    assert "house of borrowed voices" in lowered
    assert "olan" not in lowered
    assert "living memory" not in lowered
    assert "house of returned men" not in lowered
    assert "mass return" not in lowered
    assert "completed duty" not in lowered


def test_cauldron_second_look_repairs_the_full_causal_chain(
    cauldron_adventure: Adventure,
) -> None:
    """Keep Red Fen, the failed inspection, renewal, Muster, and Larks causally joined."""
    encounters = cauldron_adventure.encounter_index()
    combined = "\n".join(
        [
            cauldron_adventure.synopsis,
            cauldron_adventure.premise,
            cauldron_adventure.explanation,
            encounters["crooked-magpie"].content,
            encounters["white-hart-court"].content,
            encounters["chapel-last-word"].content,
            encounters["rookwalk"].content,
        ]
    )

    assert "Red Fen" in combined
    assert "underpinning" in combined
    assert "three witnesses" in combined
    assert "sole emergency custody" in combined
    assert "memorial rolls" in combined
    assert "one chained war register" in combined
    assert "notified Mere House" in combined
    assert "sent the Green Larks" in combined
    assert "Branoc has never been summoned" in combined


def test_cauldron_session_seven_keeps_the_underkeep_operational(
    cauldron_adventure: Adventure,
) -> None:
    """Protect the declaration model, twelve voices, and command-network weaknesses."""
    encounters = cauldron_adventure.encounter_index()
    revelations = cauldron_adventure.revelation_index()
    underkeep_text = "\n".join(
        [encounters["barrow-stair"].content, encounters["house-borrowed-voices"].content]
    )

    for name in (
        "Captain Alwen Reed",
        "Queen Mairwen Hearth-Giver",
        "Tegid Far-Step",
        "Abbess Morwen of Nine Lamps",
        "Iwan Stonehand",
        "Rhian Gorse-Eye",
        "Prince Owain Ash-Spear",
        "Nesta Vale-Hand",
        "Seneschal Madoc Three Keys",
        "Elidyr Snow-Warden",
        "Seren Bell-Bearer",
        "Bledri Rowan-Fire",
    ):
        assert name in underkeep_text

    assert "The stair reads declarations, not hearts" in encounters["barrow-stair"].content
    assert "A formally complete lie may therefore pass" not in encounters["barrow-stair"].content
    assert (
        "These are not twelve summoned persons" not in encounters["house-borrowed-voices"].content
    )
    assert (
        "The masks do not contain twelve dead people" in encounters["house-borrowed-voices"].content
    )
    assert (
        "Dunwarren's guards are trained to act immediately when two voices agree"
        in encounters["house-borrowed-voices"].content
    )
    assert "the-barrow-stair-records-declarations-rather-than-reading-hearts" in revelations
    assert "the-borrowed-voices-can-be-divided-by-conflicting-priorities" in revelations
    assert "a-recovered-reason-can-silence-a-borrowed-command" in revelations
    assert "the-house-sends-orders-through-swappable-command-lines" in revelations


def test_cauldron_session_seven_makes_target_costs_and_resolutions_explicit(
    cauldron_adventure: Adventure,
) -> None:
    """Protect the nine faculties, reversible interval, testimony, and mixed truth."""
    encounters = cauldron_adventure.encounter_index()
    revelations = cauldron_adventure.revelation_index()
    vault = encounters["cauldron-vault"].content

    for band in (
        "Band of the Face",
        "Band of the Road",
        "Band of the Measure",
        "Band of the Hearth",
        "Band of the Hand",
        "Band of the Season",
        "Band of the Bar",
        "Band of the Reply",
        "Band of Rest",
    ):
        assert band in vault

    assert "Raised to the arrest" in vault
    assert "The silence is not lost merely because the bell sounded" in vault
    assert "His trials used hair-fine name needles" in vault
    assert "all nine silences remain present for Branoc" in vault
    assert "Four iron custody dogs" in vault
    assert "The proper rite therefore uses accumulated power without consuming it" in vault
    assert "black water-script" in vault
    assert "A fort is a vessel; the realm is those it shelters" in vault
    assert "Branoc died before he could know which portions Edric obeyed" in vault

    for revelation_id in (
        "each-band-preserves-one-faculty-of-a-whole-dead-person",
        "an-opened-band-can-be-arrested-before-its-silence-is-spent",
        "four-custody-dogs-release-the-cradle-without-opening-a-band",
        "a-proper-full-asking-returns-the-nine-silences-at-voluntary-departure",
        "the-vault-can-preserve-exact-testimony-before-opposed-witnesses",
        "the-great-muster-apparatus-can-be-delayed-by-mismatched-components",
        "a-spent-silence-requires-communal-restoration-not-metal-repair",
        "the-old-compact-allows-a-one-night-respite-under-three-authorities",
    ):
        assert revelation_id in revelations

    exact_command = (
        "Bar the great leaves against the riders. Keep the wicket and the river stair "
        "until the outer ward is within."
    )
    assert exact_command in vault
    assert not any(exact_command in clue.description for clue in cauldron_adventure.clues)


def test_cauldron_session_seven_makes_extraction_and_partial_success_operational(
    cauldron_adventure: Adventure,
) -> None:
    """Protect rival custody, load, bounded pursuit, and testimony survival."""
    encounters = cauldron_adventure.encounter_index()
    revelations = cauldron_adventure.revelation_index()
    weir = encounters["reed-weir"].content

    assert "Mother Eluned of the Mere House" in weir
    assert "six marks" in weir
    assert "nine marks" in weir
    assert "Possession does not replace the recorded keeper" in weir
    assert "hold the route, take the bearers living, preserve the water" in weir
    assert "One authenticated leaf with two witnesses stays the dawn renewal until noon" in weir

    for objective in ("Vessel", "Anchor", "Testimony", "Keeper"):
        assert objective in weir

    for revelation_id in (
        "the-nine-hearth-trust-claims-the-cauldron-as-a-communal-circuit",
        "the-weir-punt-cannot-carry-the-cauldron-and-every-claimant",
        "physical-possession-does-not-replace-the-recorded-keeper",
        "vanes-recovery-order-preserves-the-vessel-and-takes-bearers-alive",
        "one-authenticated-witness-leaf-can-stay-the-dawn-oath",
        "three-extraction-routes-trade-secrecy-disguise-and-public-proof",
    ):
        assert revelation_id in revelations


def test_cauldron_maintained_records_and_packet_are_present() -> None:
    """Keep the maintained table aids, party, and playthrough with the source."""
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    ledger = (EXAMPLE_DIRECTORY / "HEIST-LEDGER.md").read_text()
    underkeep = (EXAMPLE_DIRECTORY / "UNDERKEEP-OPERATIONS.md").read_text()
    vault = (EXAMPLE_DIRECTORY / "VAULT-OPERATIONS.md").read_text()
    extraction = (EXAMPLE_DIRECTORY / "EXTRACTION-AND-AFTERMATH.md").read_text()
    party = (EXAMPLE_DIRECTORY / "PARTY-DESIGN.md").read_text()
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()
    operating = (EXAMPLE_DIRECTORY / "GM-OPERATING-SHEET.md").read_text()

    assert "## Causal spine" in design
    assert "## Why theft rather than sabotage" in design
    assert "## Demonstration decisions" in design
    assert "## Why now" in ledger
    assert "## Full Asking requirements" in ledger
    assert "## Canonical demonstration state" in ledger
    assert "## Barrow Stair quick reference" in underkeep
    assert "## The twelve retained answers" in underkeep
    assert "## Sample alarm sequences" in underkeep
    assert "## The nine bands" in vault
    assert "## Full Asking checklist" in vault
    assert "## Branoc's exact command" in vault
    assert "## Night of Hearing" in vault
    assert "## Resolution matrix" in vault
    assert "## Tide states" in extraction
    assert "## The Nine Hearth Trust" in extraction
    assert "## Pursuer priorities" in extraction
    assert "## Failure-forward outcomes" in extraction
    assert "## Immediate end states" in extraction
    for name in ("Rhoswen Pell", "Brother Aneirin Cade", "Huw Rill", "Gareth Bryn", "Sian Mere"):
        assert name in party
        assert name in playthrough
    assert "## Bell clock" in operating
    assert "## Failure-forward sequence" in operating


def test_cauldron_voice_decisions_are_present() -> None:
    """Keep the maintained voice standard and invariant record with the example."""

    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    assert "## Voice decisions" in design


def test_cauldron_session_seven_canonical_playthrough_projects_cleanly(
    cauldron_adventure: Adventure,
    cauldron_state: PlayState,
) -> None:
    """Protect the complete Unsworn Hand route, journal scale, and divided ending."""
    projection = project_play_state(cauldron_adventure, cauldron_state)

    assert len(cauldron_state.events) == 149
    assert [visit.encounter_id for visit in projection.visits] == [
        "crooked-magpie",
        "white-hart-court",
        "smoke-kitchens",
        "rookwalk",
        "chapel-last-word",
        "widows-solar",
        "barrow-stair",
        "house-borrowed-voices",
        "cauldron-vault",
        "reed-weir",
    ]
    assert len(projection.sessions) == 3
    assert projection.active_session_number is None
    assert len(projection.spotted_clue_ids) == 41
    assert sum(len(item.missed_visit_numbers) for item in projection.clue_progress) == 8
    assert all(item.is_established for item in projection.revelation_progress)
    assert {session.title for session in projection.sessions} == {
        "Masks, Ash, and the Old Chapel",
        "The Three Declarations and the Borrowed Council",
        "The King\u2019s Answer and the Carrying Road",
    }
    consequences = "\n".join(item.text for item in projection.consequences)
    assert "temporary keeper to Mere House" in consequences
    assert "Branoc\u2019s complete answer survives in three leaves" in consequences
    assert "cauldron and ring reach temporary Mere House custody" in consequences
    assert "living defense" in consequences


def test_cauldron_session_six_play_summary_matches_the_canonical_journal(
    cauldron_adventure: Adventure,
    cauldron_state: PlayState,
) -> None:
    """Keep the generated play summary reproducible from source and journal."""
    expected = render_play_summary(cauldron_adventure, cauldron_state)
    actual = (EXAMPLE_DIRECTORY / "generated" / "05-play-summary.md").read_text()

    assert actual == expected
    assert "The Unsworn Hand" in actual
    assert "The King\u2019s Answer and the Carrying Road" in actual
    assert "Reed Weir" in actual


def test_cauldron_checked_in_packet_matches_the_source(
    cauldron_adventure: Adventure,
) -> None:
    """Keep generated GM documents reproducible during staged drafting."""
    report = validate_adventure(cauldron_adventure)
    documents = render_adventure_documents(cauldron_adventure, report)

    assert "Result: PASS" in documents["04-validation-report.md"]
    assert len([name for name in documents if name.startswith("encounters/")]) == 10
    assert_rendered_documents_match(
        documents, EXAMPLE_DIRECTORY / "generated"
    )
