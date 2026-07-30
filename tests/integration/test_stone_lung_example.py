"""Regression checks for the underdark siege example."""

from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents, render_play_summary
from adventure_graph.application.play_tracking import (
    establish_revelation,
    new_play_state,
    project_play_state,
    record_visit,
)
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

EXAMPLE_DIRECTORY = Path("examples/the-siege-of-the-stone-lung")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"
EXAMPLE_PLAYTHROUGH_PATH = EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md"


@pytest.fixture(scope="module")
def stone_lung_adventure() -> Adventure:
    """Load the authored siege example once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def stone_lung_state() -> PlayState:
    """Load the Basalt Hand showcase journal once per module."""
    return load_play_state(EXAMPLE_STATE_PATH)


def test_stone_lung_is_a_valid_eight_encounter_adventure(
    stone_lung_adventure: Adventure,
) -> None:
    """Keep the authored siege aligned with its structural contract."""
    report = validate_adventure(stone_lung_adventure)

    assert len(stone_lung_adventure.encounters) == 8
    assert len(stone_lung_adventure.revelations) == 12
    assert len(stone_lung_adventure.clues) == 46
    assert report.is_valid
    assert report.edge_connectivity == 3


def test_every_stone_lung_revelation_has_independent_sources(
    stone_lung_adventure: Adventure,
) -> None:
    """Keep the deliberately irregular matrix independently sourced."""
    clues_by_revelation = group_clues_by_revelation(stone_lung_adventure.clues)

    for revelation in stone_lung_adventure.revelations:
        clues = clues_by_revelation[revelation.id]
        assert 3 <= len(clues) <= 6
        assert len({clue.source_encounter_id for clue in clues}) == len(clues)

    assert {len(clues) for clues in clues_by_revelation.values()} == {3, 4, 5, 6}


def test_stone_lung_uses_the_intended_wheel_and_terminal_cap(
    stone_lung_adventure: Adventure,
) -> None:
    """Prevent clue revisions from silently changing the planned topology."""
    revelations = stone_lung_adventure.revelation_index()
    edges = {
        frozenset((clue.source_encounter_id, target_id))
        for clue in stone_lung_adventure.clues
        if (target_id := revelations[clue.revelation_id].unlocks_encounter_id) is not None
        and clue.source_encounter_id != target_id
    }

    assert edges == {
        frozenset(("the-lantern-court", "the-shattered-gate")),
        frozenset(("the-lantern-court", "the-cinder-foundry")),
        frozenset(("the-lantern-court", "the-pale-gardens")),
        frozenset(("the-lantern-court", "the-refuge-galleries")),
        frozenset(("the-lantern-court", "the-black-cisterns")),
        frozenset(("the-lantern-court", "the-countermine")),
        frozenset(("the-shattered-gate", "the-cinder-foundry")),
        frozenset(("the-cinder-foundry", "the-pale-gardens")),
        frozenset(("the-pale-gardens", "the-refuge-galleries")),
        frozenset(("the-refuge-galleries", "the-black-cisterns")),
        frozenset(("the-black-cisterns", "the-countermine")),
        frozenset(("the-countermine", "the-shattered-gate")),
        frozenset(("the-cinder-foundry", "the-stone-lung")),
        frozenset(("the-refuge-galleries", "the-stone-lung")),
        frozenset(("the-countermine", "the-stone-lung")),
    }


def test_stone_lung_renders_complete_source_packet(
    stone_lung_adventure: Adventure,
) -> None:
    """Keep the checked-in table packet aligned with the authored source."""
    report = validate_adventure(stone_lung_adventure)
    documents = render_adventure_documents(stone_lung_adventure, report)

    assert set(documents) >= {
        "00-overview.md",
        "01-encounter-index.md",
        "02-clue-list.md",
        "03-revelation-list.md",
        "04-validation-report.md",
    }
    assert len([name for name in documents if name.startswith("encounters/")]) == 8
    assert "Result: PASS" in documents["04-validation-report.md"]
    assert "Arriving before Heartstrike" in documents["encounters/the-stone-lung.md"]

    assert_rendered_documents_match(
        documents, EXAMPLE_DIRECTORY / "generated"
    )


def _run_route(
    adventure: Adventure, steps: tuple[tuple[str, str, tuple[str, ...]], ...]
) -> tuple[str, ...]:
    state = new_play_state(adventure)
    for operation, entity_id, clue_ids in steps:
        if operation == "visit":
            state = record_visit(adventure, state, entity_id, clue_ids)
        else:
            state = establish_revelation(adventure, state, entity_id, clue_ids)
    return tuple(visit.encounter_id for visit in project_play_state(adventure, state).visits)


@pytest.mark.parametrize(
    ("steps", "expected_visits"),
    [
        (
            (
                ("visit", "the-lantern-court", ("the-gates-double-red-flare",)),
                (
                    "establish",
                    "the-shattered-gate-can-still-buy-the-city-time",
                    ("the-gates-double-red-flare",),
                ),
                (
                    "visit",
                    "the-shattered-gate",
                    ("the-unexploded-tower-resonator",),
                ),
                (
                    "establish",
                    "the-cinder-foundry-can-counter-the-resonance-weapons",
                    ("the-unexploded-tower-resonator",),
                ),
                (
                    "visit",
                    "the-cinder-foundry",
                    ("the-counterweight-service-gantry",),
                ),
                (
                    "establish",
                    "three-routes-converge-on-the-stone-lung-and-heartstrike-charge",
                    ("the-counterweight-service-gantry",),
                ),
                ("visit", "the-stone-lung", ()),
            ),
            (
                "the-lantern-court",
                "the-shattered-gate",
                "the-cinder-foundry",
                "the-stone-lung",
            ),
        ),
        (
            (
                ("visit", "the-lantern-court", ("the-blue-garden-lantern",)),
                (
                    "establish",
                    "the-pale-gardens-can-map-and-clean-the-failing-air",
                    ("the-blue-garden-lantern",),
                ),
                (
                    "visit",
                    "the-pale-gardens",
                    ("deren-vasks-ration-cart-message",),
                ),
                (
                    "establish",
                    "the-refuge-galleries-hold-witnesses-and-an-old-service-route",
                    ("deren-vasks-ration-cart-message",),
                ),
                (
                    "visit",
                    "the-refuge-galleries",
                    ("the-memorial-maintenance-stair",),
                ),
                (
                    "establish",
                    "three-routes-converge-on-the-stone-lung-and-heartstrike-charge",
                    ("the-memorial-maintenance-stair",),
                ),
                ("visit", "the-stone-lung", ()),
            ),
            (
                "the-lantern-court",
                "the-pale-gardens",
                "the-refuge-galleries",
                "the-stone-lung",
            ),
        ),
        (
            (
                ("visit", "the-lantern-court", ("the-sealed-black-water-flask",)),
                (
                    "establish",
                    "the-black-cisterns-expose-the-false-conduit-map-and-black-breath",
                    ("the-sealed-black-water-flask",),
                ),
                (
                    "visit",
                    "the-black-cisterns",
                    ("the-lower-road-maintenance-grate",),
                ),
                (
                    "establish",
                    "the-countermine-reaches-the-enemys-true-line-of-effort",
                    ("the-lower-road-maintenance-grate",),
                ),
                (
                    "visit",
                    "the-countermine",
                    ("the-heartstrike-cable",),
                ),
                (
                    "establish",
                    "three-routes-converge-on-the-stone-lung-and-heartstrike-charge",
                    ("the-heartstrike-cable",),
                ),
                ("visit", "the-stone-lung", ()),
            ),
            (
                "the-lantern-court",
                "the-black-cisterns",
                "the-countermine",
                "the-stone-lung",
            ),
        ),
        (
            (
                ("visit", "the-lantern-court", ("the-gates-double-red-flare",)),
                (
                    "establish",
                    "the-shattered-gate-can-still-buy-the-city-time",
                    ("the-gates-double-red-flare",),
                ),
                (
                    "visit",
                    "the-shattered-gate",
                    ("the-scouts-lower-road-route",),
                ),
                (
                    "establish",
                    "the-countermine-reaches-the-enemys-true-line-of-effort",
                    ("the-scouts-lower-road-route",),
                ),
                (
                    "visit",
                    "the-countermine",
                    ("the-heartstrike-cable",),
                ),
                (
                    "establish",
                    "three-routes-converge-on-the-stone-lung-and-heartstrike-charge",
                    ("the-heartstrike-cable",),
                ),
                ("visit", "the-stone-lung", ()),
            ),
            (
                "the-lantern-court",
                "the-shattered-gate",
                "the-countermine",
                "the-stone-lung",
            ),
        ),
    ],
    ids=("wall-first", "civilians-first", "utilities-first", "counterattack-first"),
)
def test_priority_routes_reach_the_stone_lung(
    stone_lung_adventure: Adventure,
    steps: tuple[tuple[str, str, tuple[str, ...]], ...],
    expected_visits: tuple[str, ...],
) -> None:
    """Keep four plausible siege priorities playable through the runtime rules."""
    assert _run_route(stone_lung_adventure, steps) == expected_visits


def test_checked_in_stone_lung_journal_exercises_the_siege_runtime(
    stone_lung_adventure: Adventure,
    stone_lung_state: PlayState,
) -> None:
    """Keep the Basalt Hand route, correction, omissions, and resolution stable."""
    projection = project_play_state(stone_lung_adventure, stone_lung_state)
    visited = tuple(visit.encounter_id for visit in projection.visits)
    progress = projection.revelation_progress_index()
    spotted = set(projection.spotted_clue_ids)

    assert len(stone_lung_state.events) == 85
    assert visited == (
        "the-lantern-court",
        "the-shattered-gate",
        "the-cinder-foundry",
        "the-stone-lung",
        "the-pale-gardens",
        "the-refuge-galleries",
        "the-black-cisterns",
        "the-countermine",
        "the-lantern-court",
        "the-stone-lung",
    )
    assert all(
        progress[revelation.id].is_established for revelation in stone_lung_adventure.revelations
    )
    assert set(projection.available_encounter_ids) == {
        encounter.id for encounter in stone_lung_adventure.encounters
    }
    assert len(spotted) == 32
    assert {clue.id for clue in stone_lung_adventure.clues} - spotted == {
        "the-sealed-black-water-flask",
        "hammer-signals-beneath-the-court",
        "the-split-tower-brace-calculation",
        "the-scouts-lower-road-route",
        "the-rejected-joint-inspection-packet",
        "venns-authenticated-revocation",
        "meras-signed-production-board",
        "the-ventwrights-three-stage-litany",
        "the-public-refuge-hearing-record",
        "rusks-protected-truce-slate",
        "the-assault-relay-drum",
        "the-buried-lorn-control-ring",
        "the-bypassed-command-governor",
        "the-surviving-balance-marks",
    }
    assert len(projection.corrections) == 1
    assert projection.corrections[0].target_operation_number == 16
    assert any(
        consequence.encounter_id == "the-stone-lung"
        and "southern branch reopens" in consequence.text
        for consequence in projection.consequences
    )
    assert any(
        consequence.encounter_id == "the-shattered-gate" and "outer gate falls" in consequence.text
        for consequence in projection.consequences
    )


def test_stone_lung_generated_packet_includes_current_journal(
    stone_lung_adventure: Adventure,
    stone_lung_state: PlayState,
) -> None:
    """Keep every checked-in report byte-aligned with the source and journal."""
    report = validate_adventure(stone_lung_adventure)
    documents = render_adventure_documents(stone_lung_adventure, report, stone_lung_state)

    assert "05-play-summary.md" in documents
    assert "Corrections recorded: 1" in documents["05-play-summary.md"]
    assert "Visits recorded: 10" in documents["05-play-summary.md"]
    assert_rendered_documents_match(
        documents, EXAMPLE_DIRECTORY / "generated"
    )


def test_stone_lung_full_playthrough_narrates_the_fixed_decisions() -> None:
    """Keep the narrative aligned with the journal's major defensive choices."""
    playthrough = EXAMPLE_PLAYTHROUGH_PATH.read_text(encoding="utf-8")

    required_text = [
        (
            "Court -> Gate -> Foundry -> Lung -> Gardens -> Refuge -> Cisterns -> "
            "Countermine -> Court -> Lung"
        ),
        "The first Lung visit is reconnaissance",
        "The journal preserves both the overstated report and the correction",
        "Session Four: Seven lanterns",
        "Fourteen authored clues remain unseen",
    ]

    assert all(text in playthrough for text in required_text)
    summary = render_play_summary(
        load_adventure(EXAMPLE_PATH),
        load_play_state(EXAMPLE_STATE_PATH),
    )
    assert "Heartstrike is detuned" in summary
    assert "Corrections recorded: 1" in summary


def test_stone_lung_second_look_clue_density_is_irregular_and_terminal_aware(
    stone_lung_adventure: Adventure,
    stone_lung_state: PlayState,
) -> None:
    """Protect the forty-six-clue matrix and unchanged demonstration."""
    clues_by_revelation = group_clues_by_revelation(stone_lung_adventure.clues)
    clues_by_encounter = group_clues_by_encounter(stone_lung_adventure.clues)
    pairs: set[tuple[str, str]] = set()
    for clue in stone_lung_adventure.clues:
        pair = (clue.source_encounter_id, clue.revelation_id)
        assert pair not in pairs
        pairs.add(pair)

    assert len(stone_lung_adventure.clues) == 46
    assert {len(clues) for clues in clues_by_revelation.values()} == {3, 4, 5, 6}
    assert {encounter_id: len(clues) for encounter_id, clues in clues_by_encounter.items()} == {
        "the-lantern-court": 8,
        "the-shattered-gate": 5,
        "the-cinder-foundry": 7,
        "the-pale-gardens": 5,
        "the-refuge-galleries": 6,
        "the-black-cisterns": 5,
        "the-countermine": 6,
        "the-stone-lung": 4,
    }

    added_ids = {
        "the-rejected-joint-inspection-packet",
        "venns-authenticated-revocation",
        "meras-signed-production-board",
        "the-ventwrights-three-stage-litany",
        "the-public-refuge-hearing-record",
        "rusks-protected-truce-slate",
        "the-assault-relay-drum",
        "the-buried-lorn-control-ring",
        "the-bypassed-command-governor",
        "the-surviving-balance-marks",
    }
    assert added_ids <= {clue.id for clue in stone_lung_adventure.clues}
    assert all(
        stone_lung_adventure.revelation_index()[clue.revelation_id].unlocks_encounter_id is None
        for clue in stone_lung_adventure.clues
        if clue.source_encounter_id == "the-stone-lung"
    )

    projection = project_play_state(stone_lung_adventure, stone_lung_state)
    assert len(stone_lung_state.events) == 85
    assert len(projection.spotted_clue_ids) == 32
    assert len(stone_lung_adventure.clues) - len(projection.spotted_clue_ids) == 14
    assert all(item.is_established for item in projection.revelation_progress)


def test_stone_lung_second_look_coherence_repairs_fresh_play_and_causality(
    stone_lung_adventure: Adventure,
    stone_lung_state: PlayState,
) -> None:
    """Keep the siege catalyst, bounded commission, and terminal timing coherent."""
    encounters = stone_lung_adventure.encounter_index()
    revelations = stone_lung_adventure.revelation_index()
    source_prose = "\n".join(
        [
            stone_lung_adventure.synopsis,
            stone_lung_adventure.premise,
            stone_lung_adventure.explanation,
            *(encounter.summary for encounter in stone_lung_adventure.encounters),
            *(encounter.opening_view for encounter in stone_lung_adventure.encounters),
            *(encounter.content for encounter in stone_lung_adventure.encounters),
            *(revelation.title for revelation in stone_lung_adventure.revelations),
            *(revelation.description for revelation in stone_lung_adventure.revelations),
            *(clue.description for clue in stone_lung_adventure.clues),
        ]
    )
    court = encounters["the-lantern-court"].content
    countermine = encounters["the-countermine"].content
    lung = encounters["the-stone-lung"].content

    for demonstrator in ("Maela Orin", "Orren Caul", "Siva Merrow", "Hadrik Sol"):
        assert demonstrator not in source_prose
    assert "Basalt Hand" not in source_prose
    assert "last reliable shaft collapsed six weeks ago" in stone_lung_adventure.explanation
    assert "demanded a joint inspection" in stone_lung_adventure.explanation
    assert "wartime technical command" in stone_lung_adventure.explanation
    assert "## The six-lantern commission" in court
    assert "local, foreign, or mixed" in court
    assert "Early reconnaissance at the Stone Lung does not by itself begin Heartstrike" in court
    assert "temporary operational compact" in court
    assert "valid-looking countermand" in countermine
    assert "two orders from different chains" in countermine
    assert "An early visit finds Bas still deploying the weapon" in lung
    assert "Shared retuning under truce" in lung
    assert "rupture its chimney and open the southern branch" in lung
    assert (
        revelations["three-routes-converge-on-the-stone-lung-and-heartstrike-charge"].title
        == "A secured approach reaches the Stone Lung"
    )
    assert len(stone_lung_adventure.encounters) == 8
    assert len(stone_lung_adventure.revelations) == 12
    assert len(stone_lung_adventure.clues) == 46
    assert len(stone_lung_state.events) == 85


def test_stone_lung_encounter_introductions_one_records_live_siege_arrivals(
    stone_lung_adventure: Adventure,
    stone_lung_state: PlayState,
) -> None:
    """Keep the first-pass audit and unchanged structural baseline."""

    report = validate_adventure(stone_lung_adventure)
    projection = project_play_state(stone_lung_adventure, stone_lung_state)
    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(stone_lung_adventure.clues) == 46
    assert len(stone_lung_state.events) == 85
    assert len(projection.spotted_clue_ids) == 32


def test_stone_lung_encounter_introductions_two_form_a_varied_siege_sequence(
    stone_lung_adventure: Adventure,
    stone_lung_state: PlayState,
) -> None:
    """Protect the compressed openings, route discipline, and Voice I handoff."""
    encounters = stone_lung_adventure.encounter_index()
    openings = [encounter.opening_view for encounter in stone_lung_adventure.encounters]

    assert len(set(openings)) == 8
    assert sum(len(opening.split()) for opening in openings) == 667
    assert all(76 <= len(opening.split()) <= 88 for opening in openings)

    expected_phrases = {
        "the-lantern-court": "one token must turn toward help before the flames steady",
        "the-shattered-gate": "The tower answers both orders",
        "the-cinder-foundry": "\u2018Name the work,\u2019 Mera says",
        "the-pale-gardens": "One is poisoned. The other is starving.",
        "the-refuge-galleries": "the whole accusation leans downhill",
        "the-black-cisterns": "the worker misses the next beat",
        "the-countermine": "The next pulse travels under every raised weapon",
        "the-stone-lung": "The war reaches the Stone Lung before anyone does",
    }
    for encounter_id, phrase in expected_phrases.items():
        assert phrase in encounters[encounter_id].opening_view

    combined = "\n".join(openings)
    for demonstrator in (
        "Basalt Hand",
        "Maela Orin",
        "Orren Caul",
        "Siva Merrow",
        "Hadrik Sol",
    ):
        assert demonstrator not in combined


    report = validate_adventure(stone_lung_adventure)
    projection = project_play_state(stone_lung_adventure, stone_lung_state)
    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(stone_lung_adventure.clues) == 46
    assert len(stone_lung_state.events) == 85
    assert len(projection.spotted_clue_ids) == 32


def test_stone_lung_voice_one_returns_work_to_the_siege(
    stone_lung_adventure: Adventure,
    stone_lung_state: PlayState,
) -> None:
    """Protect the source-level voice pass and the unchanged adventure contract."""
    encounters = stone_lung_adventure.encounter_index()
    revised_source = "\n".join(
        [
            stone_lung_adventure.synopsis,
            stone_lung_adventure.premise,
            stone_lung_adventure.explanation,
            *(encounter.summary for encounter in stone_lung_adventure.encounters),
            *(encounter.content for encounter in stone_lung_adventure.encounters),
        ]
    )

    assert " party " not in f" {revised_source.lower()} "
    assert " adventurers " not in f" {revised_source.lower()} "
    assert (
        "the commission lets a verified fact cross the city"
        in encounters["the-lantern-court"].content.lower()
    )
    assert "The shell remembers vibration" in encounters["the-cinder-foundry"].content
    assert "Grief preserved a route" in encounters["the-refuge-galleries"].content
    assert (
        "The chamber concentrates the siege; it does not suspend it"
        in encounters["the-stone-lung"].content
    )


    report = validate_adventure(stone_lung_adventure)
    projection = project_play_state(stone_lung_adventure, stone_lung_state)
    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(stone_lung_adventure.clues) == 46
    assert len(stone_lung_state.events) == 85
    assert len(projection.spotted_clue_ids) == 32


def test_stone_lung_voice_two_closes_the_packet_and_preserves_fresh_play(
    stone_lung_adventure: Adventure,
    stone_lung_state: PlayState,
) -> None:
    """Protect the final source finish, cross-file terminology, and next handoff."""
    encounters = stone_lung_adventure.encounter_index()
    clue = stone_lung_adventure.clue_index()["the-spore-tracer-sequence"]
    source_prose = "\n".join(
        [
            stone_lung_adventure.synopsis,
            stone_lung_adventure.premise,
            stone_lung_adventure.explanation,
            *(encounter.summary for encounter in stone_lung_adventure.encounters),
            *(encounter.opening_view for encounter in stone_lung_adventure.encounters),
            *(encounter.content for encounter in stone_lung_adventure.encounters),
            *(revelation.title for revelation in stone_lung_adventure.revelations),
            *(revelation.description for revelation in stone_lung_adventure.revelations),
            *(item.description for item in stone_lung_adventure.clues),
        ]
    )

    assert " party " not in f" {source_prose.lower()} "
    assert " adventurer" not in source_prose.lower()
    assert "The source assumes" not in source_prose
    assert "beyond the current node" not in source_prose
    assert (
        "The chamber concentrates the siege; it does not suspend it"
        in encounters["the-stone-lung"].content
    )
    assert (
        "End when the pressure crisis and the battle reach a position"
        in encounters["the-stone-lung"].content
    )
    assert clue.description == (
        "Different spores move on compression, draw, and release. Garden crews can "
        "mark the black-breath front and confirm when the southern valves may "
        "advance safely."
    )


    report = validate_adventure(stone_lung_adventure)
    projection = project_play_state(stone_lung_adventure, stone_lung_state)
    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(stone_lung_adventure.encounters) == 8
    assert len(stone_lung_adventure.revelations) == 12
    assert len(stone_lung_adventure.clues) == 46
    assert len(stone_lung_state.events) == 85
    assert len(projection.visits) == 10
    assert len(projection.spotted_clue_ids) == 32
    assert len(stone_lung_adventure.clues) - len(projection.spotted_clue_ids) == 14
