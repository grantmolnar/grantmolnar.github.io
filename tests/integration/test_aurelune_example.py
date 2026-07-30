"""Regression checks for the Aurelune high-court political adventure."""

from collections import Counter
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
    assert_editorial_phrase_locks,
    assert_rendered_documents_match,
    assert_semantic_concepts,
    group_clues_by_revelation,
)

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/the-concord-of-aurelune")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"
EXAMPLE_PLAYTHROUGH_PATH = EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md"
EXAMPLE_PARTY_PATH = EXAMPLE_DIRECTORY / "PARTY-DESIGN.md"


@pytest.fixture(scope="module")
def aurelune_adventure() -> Adventure:
    """Load the completed political adventure once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def aurelune_state() -> PlayState:
    """Load the Grey Lantern demonstration journal once per module."""
    return load_play_state(EXAMPLE_STATE_PATH)


def test_aurelune_is_a_valid_fourteen_encounter_adventure(
    aurelune_adventure: Adventure,
) -> None:
    """Keep the completed court aligned with its structural contract."""
    report = validate_adventure(aurelune_adventure)

    assert len(aurelune_adventure.encounters) == 14
    assert len(aurelune_adventure.revelations) == 18
    assert len(aurelune_adventure.clues) == 111
    assert {
        encounter.id for encounter in aurelune_adventure.encounters if not encounter.required
    } == {
        "the-twilight-laurel-apartments",
        "the-ashen-bough-hearing",
        "the-masque-of-plain-faces",
        "the-chamber-of-the-fourfold-petition",
    }
    assert sum(revelation.required for revelation in aurelune_adventure.revelations) == 15
    assert report.is_valid
    assert report.edge_connectivity == 6


def test_aurelune_uses_intentionally_irregular_clue_density(
    aurelune_adventure: Adventure,
) -> None:
    """Prevent later cleanup from flattening functional clue density."""
    clue_counts = Counter(clue.source_encounter_id for clue in aurelune_adventure.clues)

    assert min(clue_counts.values()) == 6
    assert max(clue_counts.values()) == 10
    assert len(set(clue_counts.values())) == 5
    assert sum(clue_counts.values()) / len(aurelune_adventure.encounters) > 7
    assert clue_counts == {
        "the-argent-canopy": 9,
        "the-unfurling-branch": 7,
        "the-white-hart-gallery": 7,
        "the-noon-spear-court": 7,
        "the-red-rose-pavilion": 6,
        "the-golden-sheaf-exchange": 9,
        "the-amber-quill-archive": 10,
        "the-hall-of-first-frost": 7,
        "the-silent-fir-lodge": 8,
        "the-twilight-laurel-apartments": 8,
        "the-ashen-bough-hearing": 7,
        "the-masque-of-plain-faces": 8,
        "the-chamber-of-the-fourfold-petition": 9,
        "the-crown-conclave": 9,
    }


def test_every_aurelune_revelation_has_redundant_independent_sources(
    aurelune_adventure: Adventure,
) -> None:
    """Keep the three-clue rule as a floor rather than a location target."""
    clues_by_revelation = group_clues_by_revelation(aurelune_adventure.clues)

    for revelation in aurelune_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        assert len(clues) >= 3
        assert len({clue.source_encounter_id for clue in clues}) >= 3


def test_aurelune_second_look_adds_non_route_evidence_without_changing_traversal(
    aurelune_adventure: Adventure,
    aurelune_state: PlayState,
) -> None:
    """Keep the additive density repair independent of access and play history."""
    revelation_index = {item.id: item for item in aurelune_adventure.revelations}
    route_edges = {
        (clue.source_encounter_id, revelation_index[clue.revelation_id].unlocks_encounter_id)
        for clue in aurelune_adventure.clues
        if revelation_index[clue.revelation_id].unlocks_encounter_id is not None
    }
    added_ids = {
        "the-crown-expedition-needs-the-same-defenses",
        "ilyrion-asks-for-a-hand-not-a-title",
        "maelith-binds-the-bearer-rather-than-the-owner",
        "the-war-table-separates-redirection-from-field-command",
        "the-campaign-order-can-stand-beside-the-petition",
        "orelle-prices-each-associated-promise-separately",
        "a-liability-share-does-not-buy-command",
        "the-adverse-index-keeps-four-hands-apart",
        "the-certification-index-tests-count-and-season-separately",
        "thalan-precedent-requires-protection-before-compulsion",
        "the-watch-order-can-remain-an-associated-instrument",
        "the-border-watch-cannot-redirect-the-rescue",
        "eirals-docket-makes-parallel-bargains-governable",
        "one-recall-article-makes-the-security-package-operative",
        "the-seasonal-call-precedes-the-seal-count",
    }
    clues = {clue.id: clue for clue in aurelune_adventure.clues}
    projection = project_play_state(aurelune_adventure, aurelune_state)

    assert added_ids <= clues.keys()
    assert all(
        revelation_index[clues[clue_id].revelation_id].unlocks_encounter_id is None
        for clue_id in added_ids
    )
    assert not added_ids.intersection(projection.spotted_clue_ids)
    assert len(route_edges) == 72
    assert Counter(clue.revelation_id for clue in aurelune_adventure.clues) == {
        "house-ilyrion-can-seal-for-sovereign-partnership": 7,
        "house-maelith-can-seal-for-answerable-personal-surety": 6,
        "house-serathiel-can-seal-for-coherent-command-and-defense": 5,
        "house-vaudren-can-seal-after-public-satisfaction-or-neutral-credit": 5,
        "house-orelle-can-seal-for-bounded-and-assigned-liability": 5,
        "house-namaris-can-seal-for-exact-and-reviewable-language": 5,
        "house-thalan-can-seal-for-restrained-emergency-precedent": 5,
        "house-serevin-can-seal-for-a-defended-eastern-border": 5,
        "house-eiral-can-seal-for-a-governable-concord": 6,
        "the-ashen-bough-can-be-seated-before-the-conclave": 4,
        "public-declarations-can-bind-politically-without-becoming-seals": 5,
        "a-complete-petition-can-compel-certification": 5,
        "the-kings-counteroffer-can-be-defeated-without-persuading-him": 9,
        "the-concord-can-compel-joint-custody-without-transferring-ownership": 7,
        "seasonal-balance-is-separate-from-the-seven-seal-count": 6,
        "a-combined-security-package-can-protect-aurelune-during-the-loan": 7,
        "side-covenants-can-carry-compatible-house-bargains": 10,
        "orisons-agency-can-survive-custody-and-command-safeguards": 9,
    }


def test_aurelune_second_look_openings_form_one_court_progression(
    aurelune_adventure: Adventure,
) -> None:
    """Protect both player-facing introduction passes and their final restraint."""
    encounters = aurelune_adventure.encounter_index()
    expected_fragments = {
        "the-argent-canopy": "Mara lays Orison's black-frosted stone beneath the throne.",
        "the-unfurling-branch": "Silver shears close, but not on the pear branch.",
        "the-white-hart-gallery": "The empty family chair has already been moved beside Mara Venn.",
        "the-noon-spear-court": "Ysandre's spear-butt strikes the glass",
        "the-red-rose-pavilion": "stop at the same sour chord",
        "the-golden-sheaf-exchange": "waiting for a named account",
        "the-amber-quill-archive": "The next question belongs to your enemy.",
        "the-hall-of-first-frost": "The lines touch, separate, and touch again",
        "the-silent-fir-lodge": "Caldus Serevin does not greet you.",
        "the-twilight-laurel-apartments": "You may not pretend they are the same.",
        "the-ashen-bough-hearing": "claim tomorrow morning",
        "the-masque-of-plain-faces": "every promise abandoned here",
        "the-chamber-of-the-fourfold-petition": "Whose promise",
        "the-crown-conclave": "Theron calls Spring before counting any seal.",
    }

    assert set(expected_fragments) == set(encounters)
    assert len({encounter.opening_view for encounter in encounters.values()}) == 14
    for encounter_id, fragment in expected_fragments.items():
        opening = encounters[encounter_id].opening_view
        assert fragment in opening
        assert 61 <= len(opening.split()) <= 69


def test_aurelune_voice_i_trusts_the_court_and_preserves_the_source_contract(
    aurelune_adventure: Adventure,
    aurelune_state: PlayState,
) -> None:
    """Protect the source-level voice pass without freezing every sentence."""
    encounters = aurelune_adventure.encounter_index()
    body_text = "\n".join(encounter.content for encounter in aurelune_adventure.encounters)
    overview_words = sum(
        len(text.split())
        for text in (
            aurelune_adventure.synopsis,
            aurelune_adventure.premise,
            aurelune_adventure.explanation,
        )
    )

    semantic_contracts = {
        "the-argent-canopy": {
            "public preference is encoded in language": (
                ("public",),
                ("preference", "partiality"),
                ("noun", "wording", "language"),
            )
        },
        "the-unfurling-branch": {
            "acceptable revision requires public standing": (
                ("revision",),
                ("public life", "public standing", "public force"),
            )
        },
        "the-white-hart-gallery": {
            "personal affection begins but does not settle the bargain": (
                ("begins", "starts"),
                ("love", "affection"),
            )
        },
        "the-noon-spear-court": {
            "concurrent dangers must become commands": (
                ("simultaneous", "concurrent"),
                ("danger", "threat"),
                ("order", "command"),
            )
        },
        "the-red-rose-pavilion": {
            "court satisfaction is distinct from truth": (
                ("satisfaction",),
                ("court custom", "court procedure"),
                ("truth",),
            )
        },
        "the-golden-sheaf-exchange": {
            "each clause is priced by political category": (
                ("loss",),
                ("capital",),
                ("advantage",),
                ("disputed", "dispute"),
            )
        },
        "the-amber-quill-archive": {
            "delay exposes the king's limiting case": (
                ("time", "delay"),
                ("king", "crown"),
                ("limiting case", "limit"),
            )
        },
        "the-hall-of-first-frost": {
            "precedent can become continuing license against the Crown": (
                ("standing license", "continuing license", "precedent"),
                ("crown",),
                ("tomorrow", "future"),
            )
        },
        "the-silent-fir-lodge": {
            "recall must be operationally measurable": (
                ("recall",),
                ("measure", "measurable"),
            )
        },
        "the-twilight-laurel-apartments": {
            "the resulting arrangement remains governable": (
                ("govern", "governable", "governance"),
            )
        },
        "the-masque-of-plain-faces": {
            "fragmentary promises must coexist publicly": (
                ("fragment",),
                ("coexist", "stand together"),
                ("public",),
            )
        },
        "the-chamber-of-the-fourfold-petition": {
            "drafting choices remain linked": (
                ("draft",),
                ("linked", "interdependent"),
                ("choice", "clause"),
            )
        },
    }
    editorial_locks = {
        "the-ashen-bough-hearing": "gray branches kindle an ember-colored leaf",
        "the-crown-conclave": "The Conclave turns inconsistency into authorship.",
    }

    assert set(semantic_contracts) | set(editorial_locks) == set(encounters)
    for encounter_id, concepts in semantic_contracts.items():
        encounter = encounters[encounter_id]
        assert_semantic_concepts(f"{encounter.summary}\n{encounter.content}", concepts)
    for encounter_id, phrase in editorial_locks.items():
        encounter = encounters[encounter_id]
        assert_editorial_phrase_locks(f"{encounter.summary}\n{encounter.content}", (phrase,))
    assert all(len(encounter.summary.split()) <= 24 for encounter in encounters.values())

    assert "The party" not in body_text
    assert "The GM should" not in body_text
    assert overview_words == 330
    assert len(aurelune_adventure.encounters) == 14
    assert len(aurelune_adventure.revelations) == 18
    assert len(aurelune_adventure.clues) == 111
    assert len(aurelune_state.events) == 158


def test_aurelune_voice_ii_closes_source_and_cross_file_register(
    aurelune_adventure: Adventure,
    aurelune_state: PlayState,
) -> None:
    """Protect the final source cadence and completed cross-file record."""
    encounters = aurelune_adventure.encounter_index()

    assert (
        "Before the audience ends, plain questions establish"
        in encounters["the-argent-canopy"].content
    )
    assert (
        "Every custody change reopens Maelith's bargain"
        in encounters["the-white-hart-gallery"].content
    )
    assert "The exercise records whose authority" in encounters["the-noon-spear-court"].content
    assert "Mirelle prices these separately" in encounters["the-golden-sheaf-exchange"].content
    assert (
        "Judgment does not remove the losing claimant from court"
        in encounters["the-ashen-bough-hearing"].content
    )
    assert (
        "repeated traps merely teach the court to narrow its answers"
        in encounters["the-masque-of-plain-faces"].content
    )
    assert (
        "Use only the pressure that fits the coalition actually assembled"
        in encounters["the-crown-conclave"].content
    )
    assert (
        "There is no correct answer hidden in the exercise"
        not in encounters["the-noon-spear-court"].content
    )
    assert "The adventure should not erase" not in encounters["the-ashen-bough-hearing"].content

    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text()

    assert "The party" not in playthrough
    assert "the party's" not in playthrough
    assert "Seven seals compelled the Sunseed's release" in playthrough
    assert len(aurelune_adventure.encounters) == 14
    assert len(aurelune_adventure.revelations) == 18
    assert len(aurelune_adventure.clues) == 111
    assert len(aurelune_state.events) == 158


def test_aurelune_authoritative_source_is_independent_of_the_demonstration(
    aurelune_adventure: Adventure,
    aurelune_state: PlayState,
) -> None:
    """Keep fresh-play source primary and the named journal explicitly subordinate."""
    source_text = EXAMPLE_PATH.read_text(encoding="utf-8")
    party = EXAMPLE_PARTY_PATH.read_text(encoding="utf-8")
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")

    for sample_specific in (
        "Grey Lantern",
        "Nara Stoneglass",
        "Tamsin Rook",
        "Lethiel Greenglass",
        "Garran Vale",
    ):
        assert sample_specific not in source_text

    assert "Mara lays Orison's black-frosted stone" in source_text
    assert (
        "their identities, history, internal offices, and preferred coalition remain open"
        in source_text
    )
    assert "one road still remembers the way to the Pall's center" in source_text
    assert "This company is one worked example" in party
    assert "Demonstration status" in playthrough
    assert len(aurelune_adventure.encounters) == 14
    assert len(aurelune_adventure.revelations) == 18
    assert len(aurelune_adventure.clues) == 111
    assert len(aurelune_state.events) == 158


def test_aurelune_renders_complete_source_and_play_packet(
    aurelune_adventure: Adventure,
    aurelune_state: PlayState,
) -> None:
    """Keep the checked-in packet aligned with the source and journal."""
    report = validate_adventure(aurelune_adventure)
    documents = render_adventure_documents(aurelune_adventure, report, aurelune_state)

    assert set(documents) >= {
        "00-overview.md",
        "01-encounter-index.md",
        "02-clue-list.md",
        "03-revelation-list.md",
        "04-validation-report.md",
        "05-play-summary.md",
    }
    assert len([name for name in documents if name.startswith("encounters/")]) == 14
    assert "Result: PASS" in documents["04-validation-report.md"]
    assert "Corrections recorded: 1" in documents["05-play-summary.md"]

    assert_rendered_documents_match(
        documents, EXAMPLE_DIRECTORY / "generated"
    )


def test_checked_in_aurelune_journal_exercises_political_independence(
    aurelune_adventure: Adventure,
    aurelune_state: PlayState,
) -> None:
    """Keep the route, optional encounters, amendment, and royal concord stable."""
    projection = project_play_state(aurelune_adventure, aurelune_state)
    visited = tuple(visit.encounter_id for visit in projection.visits)
    progress = projection.revelation_progress_index()
    spotted = set(projection.spotted_clue_ids)

    assert len(aurelune_state.events) == 158
    assert len(aurelune_state.active_events) == 156
    assert visited == (
        "the-argent-canopy",
        "the-unfurling-branch",
        "the-white-hart-gallery",
        "the-red-rose-pavilion",
        "the-amber-quill-archive",
        "the-hall-of-first-frost",
        "the-silent-fir-lodge",
        "the-noon-spear-court",
        "the-golden-sheaf-exchange",
        "the-masque-of-plain-faces",
        "the-amber-quill-archive",
        "the-chamber-of-the-fourfold-petition",
        "the-hall-of-first-frost",
        "the-crown-conclave",
    )
    assert all(progress[item.id].is_established for item in aurelune_adventure.revelations)
    assert set(projection.available_encounter_ids) == {
        encounter.id for encounter in aurelune_adventure.encounters
    }
    assert len(spotted) == 74
    assert len(aurelune_adventure.clues) - len(spotted) == 37
    assert (
        not {
            clue.id
            for clue in aurelune_adventure.clues
            if clue.source_encounter_id
            in {"the-twilight-laurel-apartments", "the-ashen-bough-hearing"}
        }
        & spotted
    )
    assert len(projection.corrections) == 1
    assert projection.corrections[0].target_operation_number == 45
    assert any(
        consequence.encounter_id == "the-red-rose-pavilion"
        and "seal is released" in consequence.text
        for consequence in projection.consequences
    )
    assert any(
        consequence.encounter_id == "the-twilight-laurel-apartments"
        and "certifies the valid petition in office" in consequence.text
        for consequence in projection.consequences
    )
    assert any(
        consequence.encounter_id == "the-ashen-bough-hearing"
        and "remains vacant at departure" in consequence.text
        for consequence in projection.consequences
    )
    assert any(
        consequence.encounter_id == "the-crown-conclave"
        and "Certification precedes royal joinder" in consequence.text
        for consequence in projection.consequences
    )
    assert any(
        consequence.encounter_id == "the-crown-conclave"
        and "Sunseed leaves Aurelune" in consequence.text
        for consequence in projection.consequences
    )


def test_aurelune_playthrough_and_party_design_fix_the_same_outcome() -> None:
    """Keep the narrative, named party, and canonical journal mutually aligned."""
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")
    party = EXAMPLE_PARTY_PATH.read_text(encoding="utf-8")

    required_playthrough_text = [
        "Canopy -> Ilyrion -> Maelith -> Vaudren -> Namaris -> Thalan -> Serevin",
        "The delegation does not request an Ashen Bough hearing",
        "A route to a seal is not a seal",
        "The original operation remains visible and is voided by the correction",
        "There are seven seals with all four seasons represented",
        "The Sunseed enters the Crown Passage before the last safe departure",
    ]
    required_party_text = [
        "The Grey Lantern Delegation",
        "House Eiral's political seal and the Chamberlain's official certification remain separate",
        "House Ilyrion refuses the final petition",
        "Certification precedes royal joinder",
    ]

    assert all(text in playthrough for text in required_playthrough_text)
    assert all(text in party for text in required_party_text)

    summary = render_play_summary(
        load_adventure(EXAMPLE_PATH),
        load_play_state(EXAMPLE_STATE_PATH),
    )
    assert "Visits recorded: 14" in summary
    assert "Corrections recorded: 1" in summary
    assert "The final seven seals are Maelith" in summary
    assert "The Sunseed leaves Aurelune" in summary


def test_aurelune_second_look_closes_the_external_causal_chain(
    aurelune_adventure: Adventure,
    aurelune_state: PlayState,
) -> None:
    """Keep the Pall, standing, clocks, and royal fallback mutually coherent."""
    canopy = next(
        encounter
        for encounter in aurelune_adventure.encounters
        if encounter.id == "the-argent-canopy"
    )
    masque = next(
        encounter
        for encounter in aurelune_adventure.encounters
        if encounter.id == "the-masque-of-plain-faces"
    )
    conclave = next(
        encounter
        for encounter in aurelune_adventure.encounters
        if encounter.id == "the-crown-conclave"
    )
    counteroffer = next(
        revelation
        for revelation in aurelune_adventure.revelations
        if revelation.id == "the-kings-counteroffer-can-be-defeated-without-persuading-him"
    )
    short_term = next(
        clue
        for clue in aurelune_adventure.clues
        if clue.id == "the-six-day-offer-shifts-risk-onto-orison"
    )
    design = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text()

    assert "siege-work has continued without its makers" in canopy.content
    assert "paving stone from Orison's noon market" in canopy.content
    assert "Lantern Road compact" in canopy.content
    assert "loan term begins when the relic is uprooted" in canopy.content
    assert "ordered a six-day Crown expedition studied on the first morning" in masque.content
    assert "root-casket enters the Crown Passage before moonrise" in conclave.content
    assert "commissions a six-day Crown expedition at once" in counteroffer.description
    assert "restore two verified dawns" in short_term.description
    assert "The custody term begins when the Sunseed is uprooted" in design
    assert "The Sunseed enters the Crown Passage before the last safe departure" in playthrough
    assert len(aurelune_adventure.encounters) == 14
    assert len(aurelune_adventure.revelations) == 18
    assert len(aurelune_adventure.clues) == 111
    assert len(aurelune_state.events) == 158
    assert len(aurelune_state.active_events) == 156
