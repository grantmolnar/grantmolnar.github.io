# ruff: noqa: RUF001 -- exact authored prose retains typographic punctuation.
"""Regression checks for the voice-complete Harrowgate dungeon crawl."""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.corpus_contracts import (
    assert_deprecated_editorial_phrases_absent,
    assert_rendered_documents_match,
    assert_semantic_concepts,
    group_clues_by_revelation,
)

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-bell-beneath-harrowgate")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"

HARROWGATE_REFERENCE_IDS = (
    "7d10d123-1d6b-4b7f-b09b-ac6d976a98f4",
    "70f54526-9ee3-4fbd-97e4-ba7b1393fdd6",
    "70dbadad-c4c0-459a-8df6-1bc5417bbb0d",
    "ddb3c840-1e11-4f47-b790-8dc67ec28dc7",
    "0e3023d6-2580-41fb-bd67-6bfe72480d77",
    "7450c8fa-6633-4b79-a24d-1f4b639ae2dc",
    "c776856e-eea8-4a35-b64d-789cf16a8086",
    "9c2e68e3-bf5b-4d1a-8388-2527775e95fa",
    "6bb941f4-f47d-44f5-9427-a2d03b8cb931",
    "eba87b8e-8c93-4624-bdde-f0fd3ae282bc",
    "b91c3329-612c-4320-98aa-37f7a40d81cc",
    "ca9adfa1-d0d7-465b-91c7-dcf0cdd67742",
    "b365284a-6604-45d3-9305-997ad660f7ad",
    "0ee5aa87-9379-4170-afd6-97de3c5badd6",
    "05588cfb-6f87-4072-a6e0-44523968d7c4",
    "8e4c88cb-067e-4701-9364-7c61e104a710",
    "eb5bc5a6-28dd-43db-a2f0-a4b5e13e6206",
    "2f1ca17b-5166-4598-be11-617cd4cdcaff",
    "adcf2968-b7f4-45fa-85e1-7da7118b404e",
    "4b3bdda6-6e52-4409-bfe7-fb9c7d53e0db",
    "05e3da93-ea8c-4cb4-a611-19a8c9612a4c",
    "eeae1101-1cb5-471f-92d8-eb27757ca095",
    "ca76d25a-8e6f-40e0-9cc5-96ab287f0bc1",
)


@pytest.fixture(scope="module")
def harrowgate_adventure() -> Adventure:
    """Load the completed dungeon once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def harrowgate_state() -> PlayState:
    """Load the canonical demonstrated journal once per module."""
    return load_play_state(STATE_PATH)


def test_harrowgate_voice_pass_preserves_the_reactive_dungeon_structure(
    harrowgate_adventure: Adventure,
) -> None:
    """Protect scale, deliberate openings, optional depths, and resilience floor."""
    report = validate_adventure(harrowgate_adventure)

    assert len(harrowgate_adventure.encounters) == 18
    assert len(harrowgate_adventure.revelations) == 50
    assert len(harrowgate_adventure.clues) == 222
    assert len(harrowgate_adventure.references) == 23
    assert (
        sum(len(encounter.reference_links) for encounter in harrowgate_adventure.encounters) == 160
    )
    assert {encounter.id for encounter in harrowgate_adventure.encounters if encounter.start} == {
        "cracked-chapterhouse",
        "quarry-cleft",
    }
    assert {encounter.id for encounter in harrowgate_adventure.encounters if encounter.end} == {
        "deep-bell",
        "mouth-below",
    }
    assert {
        encounter.id for encounter in harrowgate_adventure.encounters if not encounter.required
    } == {
        "kings-narrow-grave",
        "menagerie-of-quiet-beasts",
        "mouth-below",
    }
    assert {item.id for item in harrowgate_adventure.revelations if not item.required} == {
        "the-quiet-menagerie-opens-behind-the-quarry-cages",
        "the-kings-narrow-grave-lies-behind-the-chained-genealogy",
        "the-mouth-below-opens-beneath-the-last-sounding-chamber",
        "quiet-beasts-require-an-appetite-a-boundary-and-a-return",
        "every-quiet-beast-removes-one-excess-and-creates-another-risk",
        "the-three-genealogies-divide-custody-maintenance-and-release",
        "the-royal-treasury-is-also-the-bells-maintenance-trust",
        "a-mouth-settlement-needs-an-offering-a-boundary-and-a-return",
    }
    assert report.is_valid
    assert report.edge_connectivity == 3
    assert {issue.code for issue in report.issues} == {
        "multiple-end-encounters",
        "multiple-start-encounters",
    }
    assert all(issue.severity == "warning" for issue in report.issues)
    chain_scriptorium = harrowgate_adventure.encounter_index()["chain-scriptorium"].content
    assert (
        "Queen Avarra's limited surrender permitted her Crown to stabilize the fault"
        in chain_scriptorium
    )
    assert (
        "the Golden Branch traces blood custody through House Vey and collateral lines"
        in chain_scriptorium
    )
    assert "the Burden Chain traces operating standing" in chain_scriptorium
    assert "the Ash Witness preserves Avarra's surrender limits" in chain_scriptorium
    assert "lawfully repurposed" not in chain_scriptorium
    assert "public line ending in House Vey" not in chain_scriptorium
    pell = next(
        reference
        for reference in harrowgate_adventure.references
        if reference.title == "Engineer Pell Varo"
    )
    assert "## Repairs he can answer for" in pell.content
    assert "## Repairs she can answer for" not in pell.content
    voice_counts = {
        "chain-scriptorium": 759,
        "reliquary-under-water": 2_367,
        "feast-of-empty-chairs": 2_956,
        "counterweight-wells": 2_649,
        "kings-narrow-grave": 2_885,
        "deep-bell": 2_725,
    }
    encounters = harrowgate_adventure.encounter_index()
    assert {
        encounter_id: len(encounters[encounter_id].content.split()) for encounter_id in voice_counts
    } == voice_counts
    assert (
        sum(len(encounter.content.split()) for encounter in harrowgate_adventure.encounters)
        == 37_261
    )


def test_every_necessary_harrowgate_revelation_has_required_region_support(
    harrowgate_adventure: Adventure,
) -> None:
    """Keep required progress independent of optional depths."""
    clues_by_revelation = group_clues_by_revelation(harrowgate_adventure.clues)

    required_encounters = {
        encounter.id for encounter in harrowgate_adventure.encounters if encounter.required
    }
    for revelation in harrowgate_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        assert len(clues) in {4, 5, 6, 7}
        assert len({clue.source_encounter_id for clue in clues}) == len(clues)
        if revelation.required:
            required_sources = {
                clue.source_encounter_id
                for clue in clues
                if clue.source_encounter_id in required_encounters
            }
            assert len(required_sources) >= 3


def test_harrowgate_second_look_uses_irregular_fictional_clue_clusters(
    harrowgate_adventure: Adventure,
) -> None:
    """Protect the density pass without turning optional depths into required keys."""
    clues_by_revelation = group_clues_by_revelation(harrowgate_adventure.clues)
    clues_by_source = Counter(
        clue.source_encounter_id for clue in harrowgate_adventure.clues
    )

    assert Counter(len(items) for items in clues_by_revelation.values()) == Counter(
        {4: 36, 5: 9, 6: 2, 7: 3}
    )
    assert clues_by_source == Counter(
        {
            "cracked-chapterhouse": 8,
            "quarry-cleft": 11,
            "hall-of-bent-knees": 11,
            "ropeworks-of-three-burdens": 16,
            "chain-scriptorium": 23,
            "lantern-cistern": 12,
            "reliquary-under-water": 16,
            "salt-barracks": 14,
            "garden-of-teeth": 17,
            "feast-of-empty-chairs": 17,
            "inverted-chapel": 15,
            "menagerie-of-quiet-beasts": 6,
            "counterweight-wells": 11,
            "kings-narrow-grave": 10,
            "choir-of-iron-tongues": 12,
            "black-rain-cistern": 10,
            "deep-bell": 8,
            "mouth-below": 5,
        }
    )

    added_ids = {
        "hall-petition-without-ending-clause",
        "hall-order-without-an-address",
        "ropeworks-three-drum-transfer-scar",
        "ropeworks-crown-drum-displaced-load-countermark",
        "scriptorium-six-closure-writs",
        "scriptorium-condemned-venting-order",
        "lantern-four-bough-phase-pattern",
        "reliquary-four-breath-manifold-cuts",
        "feast-empty-chair-for-the-burden",
        "chapel-ring-of-six-dispositions",
        "choir-refusal-rejects-unassigned-release",
        "black-rain-consequence-ledger",
        "bell-frame-exhaust-bruises",
        "bell-four-receivers-beneath-the-clapper",
        "bell-second-acceptance-collar",
        "mouth-returned-pressure-knot",
        "mouth-three-answers-to-avarras-cadence",
        "mouth-crown-cadence-carrying-weight",
    }
    assert added_ids <= {clue.id for clue in harrowgate_adventure.clues}

    route_revelations = {
        revelation.id
        for revelation in harrowgate_adventure.revelations
        if revelation.unlocks_encounter_id is not None
    }
    assert not any(
        clue.id in added_ids and clue.revelation_id in route_revelations
        for clue in harrowgate_adventure.clues
    )


def test_harrowgate_fully_drafts_every_dungeon_region(
    harrowgate_adventure: Adventure,
) -> None:
    """Preserve every completed region through the optional depths and lower machinery."""
    encounters = {encounter.id: encounter for encounter in harrowgate_adventure.encounters}

    completed = {
        "cracked-chapterhouse": 900,
        "quarry-cleft": 500,
        "hall-of-bent-knees": 700,
        "ropeworks-of-three-burdens": 800,
        "chain-scriptorium": 700,
        "lantern-cistern": 1_800,
        "reliquary-under-water": 2_000,
        "salt-barracks": 2_400,
        "garden-of-teeth": 2_600,
        "feast-of-empty-chairs": 2_700,
        "inverted-chapel": 3_000,
        "menagerie-of-quiet-beasts": 2_500,
        "counterweight-wells": 2_500,
        "kings-narrow-grave": 2_700,
        "choir-of-iron-tongues": 2_000,
        "black-rain-cistern": 1_800,
        "deep-bell": 2_700,
        "mouth-below": 2_000,
    }
    for encounter_id, minimum_words in completed.items():
        assert len(encounters[encounter_id].content.split()) >= minimum_words
        assert "construction boundary" not in encounters[encounter_id].content.lower()

    assert "The fourth-toll clock" in encounters["cracked-chapterhouse"].content
    assert "The lamp hunter" in encounters["quarry-cleft"].content
    assert "The petition scale" in encounters["hall-of-bent-knees"].content
    assert "The three drums" in encounters["ropeworks-of-three-burdens"].content
    assert "The chained genealogy" in encounters["chain-scriptorium"].content
    assert "The four lamp boughs" in encounters["lantern-cistern"].content
    assert "The six copper saints" in encounters["reliquary-under-water"].content
    assert "The three positions" in encounters["salt-barracks"].content
    assert "The three filter beds" in encounters["garden-of-teeth"].content
    assert "The four household positions" in encounters["feast-of-empty-chairs"].content
    assert "The five chapel states" in encounters["inverted-chapel"].content
    assert "The four principal beasts" in encounters["menagerie-of-quiet-beasts"].content
    assert "The three wells" in encounters["counterweight-wells"].content
    assert "The three genealogies" in encounters["kings-narrow-grave"].content
    assert "The command galleries" in encounters["choir-of-iron-tongues"].content
    assert "The four routes of strain" in encounters["black-rain-cistern"].content
    assert "The four phases of a toll" in encounters["deep-bell"].content
    assert "The grammar of settlement" in encounters["mouth-below"].content


def test_harrowgate_second_look_closes_the_opening_causal_chain(
    harrowgate_adventure: Adventure,
) -> None:
    """Keep the public commission, chain cut, and toll clock causally joined."""
    encounters = harrowgate_adventure.encounter_index()
    chapterhouse = encounters["cracked-chapterhouse"].content
    ropeworks = encounters["ropeworks-of-three-burdens"].content
    reliquary = encounters["reliquary-under-water"].content
    grave = encounters["kings-narrow-grave"].content
    revelation = harrowgate_adventure.revelation_index()[
        "the-ember-company-cut-the-queens-chain-and-split-itself"
    ]

    assert "The first toll cracked chimneys and was blamed on quarry settling" in chapterhouse
    assert "Until the dying porter's testimony, Harrowgate knew the Bell had failed" in chapterhouse
    assert "Treat midnight as Tarrow's best projection, not a stopwatch" in chapterhouse
    assert "a Vey recovery trust funded the Ember Company's survey" in chapterhouse
    assert "The earlier survivor then gave Warden Marr the copied order" in chapterhouse
    assert "A player character may be that survivor" in chapterhouse
    assert "Chief Factor Halren Coss's deputy" in chapterhouse

    assert "His copy called the outer chain a release restraint" in ropeworks
    assert "unload the Crown Drum" in ropeworks
    assert "set the Water Drum forward" in ropeworks
    assert "arrest the Memory Drum" in ropeworks
    assert "Captain Maelin Rook saw live strain on all three drums" in ropeworks

    assert "Lady Vey's conditional survey-and-recovery contract" in reliquary
    assert "Councilor Samet Rhun's debt rider" in reliquary
    assert "Lady Vey's recovery trust is the expedition's lawful sponsor" in grave
    assert "Lady Vey did not authorize the chain cut" in grave
    assert "abridged extraction schedule" in revelation.description
    assert "concealed possession rider" in revelation.description


def test_harrowgate_second_look_openings_are_table_ready_and_clue_aware(
    harrowgate_adventure: Adventure,
) -> None:
    """Protect the two-pass introduction sequence without turning openings into solutions."""
    encounters = harrowgate_adventure.encounter_index()

    assert all(50 <= len(encounter.opening_view.split()) <= 70 for encounter in encounters.values())
    assert len({encounter.opening_view for encounter in encounters.values()}) == 18

    expected_phrases = {
        "cracked-chapterhouse": "The dust rises before the Bell sounds",
        "quarry-cleft": "enough remains for a rescuer and not enough for a hurried pursuit",
        "hall-of-bent-knees": "The ceiling makes you bow before the petitioners do",
        "ropeworks-of-three-burdens": "A drum moves. A hand’s breadth only. It is enough.",
        "chain-scriptorium": "Odran watches the stopped link rather than the speaker",
        "lantern-cistern": "Tell me you brought rope before you tell me you brought fire",
        "reliquary-under-water": "Replace what you take",
        "salt-barracks": "One tap comes from beneath the empty command chair",
        "garden-of-teeth": "says your names one heartbeat too early",
        "feast-of-empty-chairs": "if your name did not come home",
        "inverted-chapel": "Her hand settles on the release lever",
        "menagerie-of-quiet-beasts": "Every creature still knows where its line lies",
        "counterweight-wells": "Nothing has fallen. That is the trouble.",
        "kings-narrow-grave": "The coffin asks again",
        "choir-of-iron-tongues": "The unfinished command waits for its next word",
        "black-rain-cistern": "Every gutter is already somebody’s address",
        "deep-bell": "There is no floor to receive what comes next",
        "mouth-below": "an answer you may already have given",
    }
    for encounter_id, phrase in expected_phrases.items():
        assert phrase in encounters[encounter_id].opening_view


def test_harrowgate_second_look_voice_i_trusts_material_consequences(
    harrowgate_adventure: Adventure,
) -> None:
    """Protect the source-level voice pass without changing authored structure."""
    encounters = harrowgate_adventure.encounter_index()

    assert harrowgate_adventure.synopsis.startswith(
        "Three nights running, the Deep Bell has sounded beneath Harrowgate"
    )
    assert harrowgate_adventure.premise.endswith(
        "decide which burdens Harrowgate will carry in public."
    )
    assert "No ending restores safety and justice together" in harrowgate_adventure.explanation

    expected_summaries = {
        "cracked-chapterhouse": "Harrowgate argues beneath rising dust",
        "ropeworks-of-three-burdens": "Three burden drums turn the upper house",
        "feast-of-empty-chairs": "The Low Choir feeds its living and absent",
        "deep-bell": "Four moving approaches converge on the Bell",
        "mouth-below": "A listening fault learns repeated exchanges",
    }
    for encounter_id, opening in expected_summaries.items():
        assert encounters[encounter_id].summary.startswith(opening)

    semantic_contracts = {
        "cracked-chapterhouse": {
            "burdens crossing the floor become public": (
                ("carried", "burden"),
                ("floor",),
                ("public",),
            )
        },
        "chain-scriptorium": {
            "removing records changes future proof": (
                ("plate", "record"),
                ("removed", "removal"),
                ("proved", "proof"),
            )
        },
        "lantern-cistern": {
            "light has both recipient and payer": (
                ("light",),
                ("recipient", "receives"),
                ("payer", "pays", "cost"),
            )
        },
        "garden-of-teeth": {
            "the Garden prices consequences in household-days": (
                ("garden",),
                ("household-day", "household day"),
            )
        },
        "inverted-chapel": {
            "procedure makes consent limits and remedy legible": (
                ("consent",),
                ("limit",),
                ("remedy",),
                ("legible", "visible"),
            )
        },
        "counterweight-wells": {
            "proposals pay a physical cost": (
                ("proposed answer", "proposal"),
                ("physical", "material"),
                ("bill", "cost"),
            )
        },
        "choir-of-iron-tongues": {
            "commands retain source address and limit": (
                ("source",),
                ("address",),
                ("limit",),
            )
        },
        "black-rain-cistern": {
            "displaced water is not treated as gone": (
                ("gone", "disappeared"),
                ("never", "not"),
            )
        },
        "deep-bell": {
            "bearers and casualties remain nameable": (
                ("bearer",),
                ("casualt",),
                ("named", "nameable"),
            )
        },
        "mouth-below": {
            "the bargain is made visible": (
                ("bargain",),
                ("visible", "legible"),
            )
        },
    }
    for encounter_id, concepts in semantic_contracts.items():
        assert_semantic_concepts(encounters[encounter_id].content, concepts)

    combined_bodies = "\n".join(encounter.content for encounter in harrowgate_adventure.encounters)
    assert_deprecated_editorial_phrases_absent(
        combined_bodies,
        (
            "The party should leave knowing",
            "The point is to reveal",
            "The crawl is not built around concealing",
            "A good resolution states four things plainly",
            "The Mouth does not debate propositions",
        ),
    )


def test_harrowgate_second_look_voice_ii_reconciles_live_documents(
    harrowgate_adventure: Adventure,
) -> None:
    """Protect final cadence and completed cross-file terminology."""
    encounters = harrowgate_adventure.encounter_index()

    assert (
        "change the state of a cistern or flooded room"
        in encounters["cracked-chapterhouse"].content
    )
    assert (
        "Name the receiving cost before the final release"
        in encounters["counterweight-wells"].content
    )
    assert "It grants no throne" in encounters["kings-narrow-grave"].content
    assert "The shape is only the form" in encounters["mouth-below"].content

    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()

    assert "They fought for stations, not a cleared room" in playthrough
    assert "They broke the command cascade by making command smaller" in playthrough


def test_harrowgate_voice_pass_completion_materials_are_present() -> None:
    """Keep the completed voice pass, demonstration, aids, and audits synchronized."""
    design_notes = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    party = (EXAMPLE_DIRECTORY / "PARTY-DESIGN.md").read_text()
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()

    assert "## Session 7 operating decisions" in design_notes

    assert "# Party Design: The Open Chain" in party
    for name in (
        "Dema Harl",
        "Sister Calve Norn",
        "Ilyra Vey",
        "Torren Pike",
        "Miren Glass",
    ):
        assert name in party
    assert "## Productive fault lines" in party
    assert "## Demonstrated arc" in party

    for title in (
        "Two Ways Down",
        "Water That Remembers",
        "The Salt Muster",
        "The Hanging Judgment",
        "Gold Is Weight",
        "The Routes of Strain",
        "A Bell That Does Not Sound",
    ):
        assert title in playthrough
    assert "## Demonstrated end state" in playthrough
    assert "The result was deliberately noncanonical" not in playthrough
    assert "It is not a canonical solution" in playthrough


def test_harrowgate_whole_dungeon_aids_cover_pressure_extraction_and_finale() -> None:
    """Preserve the new table-facing procedures without fixing system mechanics."""
    pressure = (EXAMPLE_DIRECTORY / "PRESSURE-AND-ENCOUNTERS.md").read_text()
    extraction = (EXAMPLE_DIRECTORY / "EXTRACTION-AND-CAMP.md").read_text()
    quick = (EXAMPLE_DIRECTORY / "GM-OPERATING-SHEET.md").read_text()

    for heading in (
        "## When pressure advances",
        "## The four pressure questions",
        "## General pressure event table",
        "## Reaction posture",
        "## Encounter objectives",
        "## Using skipped optional regions",
    ):
        assert heading in pressure
    assert "damage" not in pressure.lower() or "system" in pressure.lower()

    for heading in (
        "## The extraction questions",
        "## Broad load classes",
        "## Rescue priority ledger",
        "## Extraction routes",
        "## Safe camps",
        "## Reward without system-specific prices",
    ):
        assert heading in extraction

    for heading in (
        "## Starting truths",
        "## Route unlock spine",
        "## Likely combat-capable scenes",
        "## Core operating maxims",
        "## Finale readiness checklist",
        "## End-state questions",
    ):
        assert heading in quick


def test_harrowgate_canonical_journal_demonstrates_reactive_play(
    harrowgate_adventure: Adventure,
    harrowgate_state: PlayState,
) -> None:
    """Protect the seven-session route, revisits, correction, and optional choices."""
    projection = project_play_state(harrowgate_adventure, harrowgate_state)

    assert len(harrowgate_state.events) == 366
    assert len(harrowgate_state.active_events) == 364
    assert len(projection.sessions) == 7
    assert projection.active_session_number is None
    assert len(projection.visits) == 25
    assert len(projection.corrections) == 1
    assert len(projection.spotted_clue_ids) == 175
    assert len(projection.consequences) == 25
    assert sum(item.is_established for item in projection.revelation_progress) == 50
    assert len(projection.available_encounter_ids) == 18

    assert [session.title for session in projection.sessions] == [
        "Two Ways Down",
        "Water That Remembers",
        "The Salt Muster",
        "The Hanging Judgment",
        "Gold Is Weight",
        "The Routes of Strain",
        "A Bell That Does Not Sound",
    ]
    assert all(not session.is_active for session in projection.sessions)

    visit_counts = Counter(visit.encounter_id for visit in projection.visits)
    assert visit_counts["kings-narrow-grave"] == 1
    assert visit_counts["menagerie-of-quiet-beasts"] == 0
    assert visit_counts["mouth-below"] == 0
    assert visit_counts["deep-bell"] == 1
    assert sum(count > 1 for count in visit_counts.values()) == 9

    visited = set(visit_counts)
    spotted = set(projection.spotted_clue_ids)
    assert all(
        clue.source_encounter_id in visited
        for clue in harrowgate_adventure.clues
        if clue.id in spotted
    )
    assert sum(bool(item.missed_visit_numbers) for item in projection.clue_progress) == 11
    assert len(harrowgate_adventure.clues) - len(spotted) == 47

    consequence_texts = {item.text for item in projection.consequences}
    assert (
        "The Funerary Well remains braced and physically active while automatic Low Choir "
        "memory intake is severed; no Well was dropped."
    ) in consequence_texts
    assert (
        "The Funerary Well was dropped, permanently sacrificing lower memory access."
        not in consequence_texts
    )
    assert (
        "The Crown is free; the Bell is silenced without destruction; the Funerary draw is "
        "closed; distributed civic maintenance begins."
    ) in consequence_texts


def test_harrowgate_checked_in_packet_matches_source_and_journal(
    harrowgate_adventure: Adventure,
    harrowgate_state: PlayState,
) -> None:
    """Keep the completed packet synchronized and free of construction placeholders."""
    report = validate_adventure(harrowgate_adventure)
    documents = render_adventure_documents(
        harrowgate_adventure,
        report,
        harrowgate_state,
    )

    assert set(documents) >= {
        "00-overview.md",
        "01-encounter-index.md",
        "02-clue-list.md",
        "03-revelation-list.md",
        "04-validation-report.md",
        "05-play-summary.md",
    }
    assert len([name for name in documents if name.startswith("encounters/")]) == 18
    assert len(documents) == 48
    assert "Result: PASS" in documents["04-validation-report.md"]
    assert "multiple-start-encounters" in documents["04-validation-report.md"]
    assert "multiple-end-encounters" in documents["04-validation-report.md"]
    assert "Explicit sessions: 7" in documents["05-play-summary.md"]
    assert "Visits recorded: 25" in documents["05-play-summary.md"]
    assert "Unique leads found: 175 / 222" in documents["05-play-summary.md"]
    assert "references/index.md" in documents
    assert {f"references/{reference_id}.md" for reference_id in HARROWGATE_REFERENCE_IDS} <= set(
        documents
    )

    assert_rendered_documents_match(
        documents, EXAMPLE_DIRECTORY / "generated"
    )


def test_harrowgate_finale_operating_revelations_retain_independent_region_support(
    harrowgate_adventure: Adventure,
) -> None:
    """Protect the independent evidence needed to operate the final chambers."""
    ids = {
        "iron-tongue-commands-need-a-source-an-address-and-a-limit",
        "memory-restoration-needs-an-identified-memory-a-recipient-and-recognition",
        "avarras-will-survives-as-measure-refusal-and-witness",
        "black-rain-pressure-can-be-routed-delayed-or-divided-but-not-erased",
        "safe-quarry-venting-needs-open-mouths-prepared-roots-and-staged-release",
        "the-deep-bell-moves-through-breath-load-crown-descent-and-sounding",
        "freeing-the-crown-requires-transferring-or-spending-its-load",
        "a-mouth-settlement-needs-an-offering-a-boundary-and-a-return",
    }
    sources: defaultdict[str, set[str]] = defaultdict(set)
    counts: defaultdict[str, int] = defaultdict(int)
    for clue in harrowgate_adventure.clues:
        if clue.revelation_id in ids:
            counts[clue.revelation_id] += 1
            sources[clue.revelation_id].add(clue.source_encounter_id)

    expected_support = {
        "iron-tongue-commands-need-a-source-an-address-and-a-limit": 5,
        "memory-restoration-needs-an-identified-memory-a-recipient-and-recognition": 4,
        "avarras-will-survives-as-measure-refusal-and-witness": 5,
        "black-rain-pressure-can-be-routed-delayed-or-divided-but-not-erased": 7,
        "safe-quarry-venting-needs-open-mouths-prepared-roots-and-staged-release": 5,
        "the-deep-bell-moves-through-breath-load-crown-descent-and-sounding": 6,
        "freeing-the-crown-requires-transferring-or-spending-its-load": 7,
        "a-mouth-settlement-needs-an-offering-a-boundary-and-a-return": 4,
    }

    assert set(counts) == ids
    assert dict(counts) == expected_support
    assert {key: len(value) for key, value in sources.items()} == expected_support
