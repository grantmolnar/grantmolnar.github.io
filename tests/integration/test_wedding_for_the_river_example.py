# ruff: noqa: RUF001 -- exact authored titles retain typographic apostrophes.
"""Regression checks for the completed constructive river wedding."""

from __future__ import annotations

from collections import defaultdict
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
from tests.support.corpus_contracts import (
    assert_editorial_phrase_locks,
    assert_markdown_sections,
    assert_rendered_documents_match,
    group_clues_by_encounter,
    group_clues_by_revelation,
)

pytestmark = pytest.mark.corpus

EXAMPLE_DIRECTORY = Path("examples/a-wedding-for-the-river")
EXAMPLE_PATH = EXAMPLE_DIRECTORY / "adventure.json"
EXAMPLE_STATE_PATH = EXAMPLE_DIRECTORY / "play-state.example.json"
EXAMPLE_ARCHIVE_PATH = (
    EXAMPLE_DIRECTORY / "archives" / "four-open-hands-demonstrated-playthrough.journal.json"
)


@pytest.fixture(scope="module")
def wedding_adventure() -> Adventure:
    """Load the completed source once per module."""
    return load_adventure(EXAMPLE_PATH)


@pytest.fixture(scope="module")
def wedding_state() -> PlayState:
    """Load the Four Open Hands demonstration journal once per module."""
    return load_play_state(EXAMPLE_STATE_PATH)


@pytest.fixture(scope="module")
def archived_wedding_state() -> PlayState:
    """Load the exact archived demonstration once per module."""
    return load_journal_archive(EXAMPLE_ARCHIVE_PATH).play_state


def test_wedding_voice_pass_preserves_the_intended_constructive_social_shape(
    wedding_adventure: Adventure,
) -> None:
    """Protect the compact scale, single finale, and unusually dense resilience."""
    report = validate_adventure(wedding_adventure)

    assert len(wedding_adventure.encounters) == 9
    assert len(wedding_adventure.revelations) == 20
    assert len(wedding_adventure.clues) == 72
    assert {encounter.id for encounter in wedding_adventure.encounters if encounter.start} == {
        "house-of-open-measure"
    }
    assert {encounter.id for encounter in wedding_adventure.encounters if encounter.end} == {
        "wedding-between-the-banks"
    }
    assert all(encounter.required for encounter in wedding_adventure.encounters)
    assert all(revelation.required for revelation in wedding_adventure.revelations)
    assert report.is_valid
    assert report.edge_connectivity == 8
    assert not [issue for issue in report.issues if issue.severity == "error"]


def test_wedding_second_intro_pass_varies_cadence_and_oblique_evidence(
    wedding_adventure: Adventure,
) -> None:
    """Protect differentiated table openings without turning them into clue summaries."""
    encounters = wedding_adventure.encounter_index()
    openings = {encounter.id: encounter.opening_view for encounter in wedding_adventure.encounters}

    assert len(set(openings.values())) == 9
    assert all(len(opening.split()) >= 55 for opening in openings.values())
    assert "question that is not hers" in openings["house-of-open-measure"]
    assert "which of these does a wedding carry" in openings["vale-mill-and-hearth"]
    assert "The bell is old. The knot is new." in openings["house-beneath-the-willows"]
    assert "Fish first" in openings["market-of-seven-baskets"]
    assert "what each person may still decline" in openings["shrine-of-the-open-door"]
    assert "What, exactly, is meant to carry her?" in openings["reedwrights-yard"]
    assert "the wedding collides with itself" in openings["bridge-of-three-tunes"]
    assert "Neither woman reaches for it." in openings["flood-meadow-and-old-ford"]
    assert "gives either of them the first word" in openings["wedding-between-the-banks"]
    assert encounters["wedding-between-the-banks"].end


def test_wedding_clue_density_is_irregular_without_weakening_redundancy(
    wedding_adventure: Adventure,
) -> None:
    """Protect deliberate clue clusters while retaining three-source discovery floors."""
    clues_by_revelation = group_clues_by_revelation(wedding_adventure.clues)

    clue_counts = {
        revelation.id: len(clues_by_revelation[revelation.id])
        for revelation in wedding_adventure.revelations
    }
    source_counts = {
        revelation.id: len(
            {clue.source_encounter_id for clue in clues_by_revelation[revelation.id]}
        )
        for revelation in wedding_adventure.revelations
    }

    assert sorted(clue_counts.values()).count(3) == 9
    assert sorted(clue_counts.values()).count(4) == 10
    assert sorted(clue_counts.values()).count(5) == 1
    assert min(source_counts.values()) == 3
    assert clue_counts["gifts-need-declared-intentions-not-assumed-symbols"] == 5
    assert source_counts["gifts-need-declared-intentions-not-assumed-symbols"] == 5
    assert clue_counts["the-old-flood-was-a-failed-handoff-not-a-single-betrayal"] == 4
    assert source_counts["the-old-flood-was-a-failed-handoff-not-a-single-betrayal"] == 3


def test_wedding_encounter_density_and_destinations_are_deliberately_uneven(
    wedding_adventure: Adventure,
) -> None:
    """Keep rich scenes clue-dense without manufacturing a uniform graph matrix."""
    revelation_targets = {
        revelation.id: revelation.unlocks_encounter_id
        for revelation in wedding_adventure.revelations
    }
    clues_by_source = group_clues_by_encounter(wedding_adventure.clues)
    targets_by_source: defaultdict[str, set[str]] = defaultdict(set)
    for clue in wedding_adventure.clues:
        target = revelation_targets[clue.revelation_id]
        assert target is not None
        targets_by_source[clue.source_encounter_id].add(target)

    assert {encounter_id: len(clues) for encounter_id, clues in clues_by_source.items()} == {
        "bridge-of-three-tunes": 6,
        "flood-meadow-and-old-ford": 9,
        "house-beneath-the-willows": 7,
        "house-of-open-measure": 8,
        "market-of-seven-baskets": 11,
        "reedwrights-yard": 6,
        "shrine-of-the-open-door": 7,
        "vale-mill-and-hearth": 9,
        "wedding-between-the-banks": 9,
    }
    assert sorted(len(targets) for targets in targets_by_source.values()) == [
        6,
        6,
        6,
        6,
        6,
        7,
        7,
        8,
        8,
    ]
    assert all(
        encounter.id not in targets_by_source[encounter.id]
        for encounter in wedding_adventure.encounters
    )


def test_wedding_completed_source_fully_drafts_all_nine_encounters(
    wedding_adventure: Adventure,
) -> None:
    """Keep foundations, preparation, rehearsal, and finale table-usable."""
    encounters = wedding_adventure.encounter_index()

    for encounter_id, minimum_words in {
        "house-of-open-measure": 2700,
        "vale-mill-and-hearth": 2350,
        "house-beneath-the-willows": 2550,
        "market-of-seven-baskets": 3700,
        "shrine-of-the-open-door": 3000,
        "reedwrights-yard": 2900,
        "bridge-of-three-tunes": 2900,
        "flood-meadow-and-old-ford": 2750,
        "wedding-between-the-banks": 3000,
    }.items():
        assert len(encounters[encounter_id].content.split()) >= minimum_words

    house = encounters["house-of-open-measure"].content
    vale = encounters["vale-mill-and-hearth"].content
    river = encounters["house-beneath-the-willows"].content
    market = encounters["market-of-seven-baskets"].content
    shrine = encounters["shrine-of-the-open-door"].content
    yard = encounters["reedwrights-yard"].content
    bridge = encounters["bridge-of-three-tunes"].content

    assert_markdown_sections(
        house,
        (
            "## The private consent procedure",
            "### 3. Reciprocal paraphrase",
            "## Running the commission out of order",
            "## One-sided cooperation",
            "## The hospitality appendix",
        ),
    )
    assert_markdown_sections(
        vale,
        (
            "## Elsin Vale is not an inheritance token",
            "## The wheel, lease, and four kinds of authority",
            "## If the mill is skipped or reached late",
            "## Agnes’s seat and the guest register",
        ),
    )
    assert_markdown_sections(
        river,
        (
            "## Serein-at-Alderfall and exact adoption",
            "## Care, children, and claims of return",
            "## If the willow house is skipped or reached late",
            "## Deep-Reed’s basin chair",
        ),
    )
    assert_markdown_sections(
        market,
        (
            "## The seven baskets",
            "### Second basket: food and source",
            "### Sixth basket: gifts and declared intentions",
            "#### The public interval",
            "## Brin Quickwater and accountable comedy",
            "## If the market is skipped or reached late",
        ),
    )
    assert_markdown_sections(
        shrine,
        (
            "## The six ceremonial functions",
            "### 3. Names",
            "#### Image followed by plain speech",
            "## Ceremony orders",
            "## If the shrine is skipped or reached late",
        ),
    )
    assert_markdown_sections(
        yard,
        (
            "## The site survey",
            "## Wet and dry ground in one ceremony",
            "## The six-function plan",
            "## The threshold boat",
            "## If the yard is skipped or reached late",
        ),
    )
    assert_markdown_sections(
        bridge,
        (
            "## The three tunes",
            "## The six cues",
            "## Participation without compulsory dance",
            "## If the bridge is skipped or reached late",
        ),
    )
    flood = encounters["flood-meadow-and-old-ford"].content
    wedding = encounters["wedding-between-the-banks"].content
    assert_markdown_sections(
        flood,
        (
            "## The visible pressure board",
            "## Rehearsal pass one: the empty ceremony",
            "## Rehearsal pass four: the old flood handoff",
            "### Building the new handoff",
            "## If rehearsal is skipped, shortened, or divided",
        ),
    )
    assert_markdown_sections(
        wedding,
        (
            "### The last private repetition",
            "## The ceremony in six functions",
            "## The witnesses' record",
            "### Certification forms",
            "## Late discoveries and the smallest affected scope",
            "## Authority at the threshold",
        ),
    )
    assert_editorial_phrase_locks(
        house,
        (
            "one household in two dwellings",
            "Compelled speech, read thoughts",
        ),
    )
    assert_editorial_phrase_locks(
        river,
        ("The river household owes reciprocal duties",),
    )
    assert_editorial_phrase_locks(
        market,
        (
            "Pella sets twelve minutes and no more than four public entries",
            "The mill's grain account, Tomas's personal purse",
            "two flood-year market records",
        ),
    )
    assert_editorial_phrase_locks(
        vale,
        ("Mara's workshop inventory",),
    )
    assert_editorial_phrase_locks(
        shrine,
        ("Ansel's return-shelf register",),
    )
    assert_editorial_phrase_locks(
        bridge,
        ("Four and six meet every twelve pulses",),
    )
    assert_editorial_phrase_locks(
        flood,
        (
            "the protocol must still work when both are absent",
            "**mill gate received**",
        ),
    )
    assert_editorial_phrase_locks(
        wedding,
        (
            "**Marriage certified; river adoption deferred.**",
            "a fresh mud line may cross the planned aisle",
        ),
    )


def test_wedding_second_look_closes_the_opening_causal_chain(
    wedding_adventure: Adventure,
) -> None:
    """Keep the late discovery, witness office, and flood motive mutually intelligible."""
    house = wedding_adventure.encounter_index()["house-of-open-measure"].content
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()

    assert "Six weeks ago, each household lodged a sealed reading copy" in house
    assert "may not also serve as the independent field witness" in house
    assert "That was a shared evasion, not a trap" in house
    assert "One sentence appears to mend the same wound in opposite directions" in house
    assert "Tomas enters the house of Neris. Neris keeps the wheel." in playthrough
    assert "Each bears the other’s name before water and flame" in playthrough


def test_wedding_session_two_named_care_remains_without_default_custody(
    wedding_adventure: Adventure,
) -> None:
    """Protect the care affordance and its independent evidence."""
    revelation = wedding_adventure.revelation_index()[
        "care-follows-named-duties-not-household-claims"
    ]
    supporting = [clue for clue in wedding_adventure.clues if clue.revelation_id == revelation.id]

    assert revelation.unlocks_encounter_id == "house-beneath-the-willows"
    assert "default custody" in revelation.description
    assert {clue.source_encounter_id for clue in supporting} == {
        "house-of-open-measure",
        "market-of-seven-baskets",
        "vale-mill-and-hearth",
        "wedding-between-the-banks",
    }
    assert {clue.title for clue in supporting} == {
        "Mara’s named care instructions",
        "The lifting rota",
        "The two-ledger care compact",
        "The unclaimed care lines",
    }


def test_wedding_session_three_adds_particular_hospitality(
    wedding_adventure: Adventure,
) -> None:
    """Protect named capacities against representative cultural assumptions."""
    revelation = wedding_adventure.revelation_index()[
        "hospitality-follows-named-capacities-not-representative-customs"
    ]
    supporting = [clue for clue in wedding_adventure.clues if clue.revelation_id == revelation.id]

    assert revelation.unlocks_encounter_id == "market-of-seven-baskets"
    assert "named guests and their choices" in revelation.description
    assert {clue.source_encounter_id for clue in supporting} == {
        "flood-meadow-and-old-ford",
        "house-of-open-measure",
        "vale-mill-and-hearth",
        "house-beneath-the-willows",
    }
    assert {clue.title for clue in supporting} == {
        "The basin moved after the elder",
        "The crossed-out household columns",
        "Agnes’s corrected seat",
        "Three incompatible river accommodations",
    }


def test_wedding_voice_pass_preserves_functional_ceremony_design(
    wedding_adventure: Adventure,
) -> None:
    """Protect movable functions, non-symmetrical names, and genuine musical leadership."""
    revelations = wedding_adventure.revelation_index()
    clues_by_revelation = group_clues_by_revelation(wedding_adventure.clues)

    six_functions = revelations["six-clear-functions-matter-more-than-copying-every-custom"]
    rhythms = revelations["two-rhythms-can-meet-without-one-becoming-background"]
    names = revelations["stable-records-can-preserve-changing-river-names"]

    assert "Consent, household standing, names, exchange, promises, and departure" in (
        six_functions.description
    )
    assert {clue.source_encounter_id for clue in clues_by_revelation[six_functions.id]} == {
        "flood-meadow-and-old-ford",
        "bridge-of-three-tunes",
        "reedwrights-yard",
    }
    assert "each household audibly leads" in rhythms.description
    assert {clue.source_encounter_id for clue in clues_by_revelation[rhythms.id]} == {
        "market-of-seven-baskets",
        "reedwrights-yard",
        "shrine-of-the-open-door",
        "wedding-between-the-banks",
    }
    assert "without replacing her current answered name" in names.description


def test_wedding_source_preserves_no_villain_and_revisable_consent(
    wedding_adventure: Adventure,
) -> None:
    """Prevent sabotage, compulsory marriage, or compulsory truth from entering."""
    combined = "\n".join(
        [
            wedding_adventure.synopsis,
            wedding_adventure.premise,
            wedding_adventure.explanation,
            *(encounter.content for encounter in wedding_adventure.encounters),
        ]
    )
    lowered = combined.lower()

    assert "no villain" in lowered
    assert "nobody forged the document" in lowered
    assert "the wedding may be postponed" in lowered
    assert "postponed by the couple" in lowered
    assert "not sabotage" in lowered
    assert "secret saboteur" not in lowered
    assert "jealous former lover" not in lowered
    assert "must marry" not in lowered
    assert "read thoughts" in lowered
    assert "answer the wrong question" in lowered


def test_wedding_completion_materials_and_rendering_are_present(
    wedding_adventure: Adventure,
) -> None:
    """Keep plans, principles, ledgers, rehearsal aid, and packet synchronized."""
    design_notes = (EXAMPLE_DIRECTORY / "DESIGN-NOTES.md").read_text()
    ledger = (EXAMPLE_DIRECTORY / "WEDDING-LEDGER.md").read_text()
    terms = (EXAMPLE_DIRECTORY / "TERMS-OF-BELONGING.md").read_text()
    hospitality = (EXAMPLE_DIRECTORY / "HOSPITALITY-LEDGER.md").read_text()
    ceremony = (EXAMPLE_DIRECTORY / "CEREMONY-LEDGER.md").read_text()
    rehearsal = (EXAMPLE_DIRECTORY / "REHEARSAL-AND-WITNESS-RECORD.md").read_text()
    operating = (EXAMPLE_DIRECTORY / "GM-OPERATING-SHEET.md").read_text()

    assert "## Hospitality is particular and consent-bearing" in design_notes
    assert "## Grievances need scope, stewardship, and an ending" in design_notes
    assert "## Ceremony functions must be observable and movable" in design_notes
    assert "## Names and vows need not become symmetrical" in design_notes
    assert "## Movement and music do not manufacture assent" in design_notes
    assert "## Pressure must be public and negotiable" in design_notes
    assert "## Rehearsal is new consent evidence" in design_notes
    assert "## The old flood should improve a handoff, not consume grief" in design_notes
    assert "## Certification is scoped observation" in design_notes
    assert "## Calendar, clue flow, authority, and ceremony state are separate" in design_notes
    assert "## Authority is bounded and named" in design_notes
    assert "## Split parties preserve location and acceptance" in design_notes
    assert "## Late discoveries reopen the smallest scope" in design_notes
    assert "## Necessary encounters are not compulsory scenes" in design_notes
    assert "## Governing voice standard" in design_notes
    assert "## Terms of belonging" in ledger
    assert "## Hospitality decisions" in ledger
    assert "## The central live disagreement" in terms
    assert "## Private consent sequence" in terms
    assert "## The seven baskets" in hospitality
    assert "## Bounded grievance procedure" in hospitality
    assert "## Six-function worksheet" in ceremony
    assert "## Site matrix" in ceremony
    assert "## Procession and music score" in ceremony
    assert "## Minimum Session 4 result" in ceremony
    assert "## Demonstrated ceremony decisions" in ledger
    assert "## Rehearsal and wedding decisions" in ledger
    assert "## Route and agency decisions" in ledger
    assert "## Live adjudication" in ledger
    assert "## Session 5 handoff" in ceremony
    assert "## Rehearsal pressure board" in rehearsal
    assert "## Four rehearsal passes" in rehearsal
    assert "## New warning handoff" in rehearsal
    assert "## Witness folio" in rehearsal
    assert "### Certification scope" in rehearsal
    assert "## No-rehearsal fallback" in rehearsal
    assert "## Late-discovery triage" in rehearsal
    assert "## Never collapse these four structures" in operating
    assert "## Split-party procedure" in operating
    assert "## Skipped-encounter fallbacks" in operating
    assert "## Late-discovery triage" in operating

    documents = render_adventure_documents(wedding_adventure, validate_adventure(wedding_adventure))
    expected_documents = {
        "00-overview.md",
        "01-encounter-index.md",
        "02-clue-list.md",
        "03-revelation-list.md",
        "04-validation-report.md",
        "encounters/bridge-of-three-tunes.md",
        "encounters/flood-meadow-and-old-ford.md",
        "encounters/house-beneath-the-willows.md",
        "encounters/house-of-open-measure.md",
        "encounters/market-of-seven-baskets.md",
        "encounters/reedwrights-yard.md",
        "encounters/shrine-of-the-open-door.md",
        "encounters/vale-mill-and-hearth.md",
        "encounters/wedding-between-the-banks.md",
        "references/index.md",
    }
    expected_documents.update(
        f"references/{reference.id}.md" for reference in wedding_adventure.references
    )
    assert set(documents) == expected_documents

    assert tuple(reference.title for reference in wedding_adventure.references) == (
        "Tomas Vale",
        "Neris Reed-in-Rain",
        "Mera Quill",
        "Agnes Vale",
        "Serein-at-Alderfall",
        "Mara Vale",
        "Orren Underbridge",
        "Rain-at-Noon",
        "The House of Open Measure",
        "Vale Mill and Hearth",
        "The House Beneath the Willows",
    )
    reference_index = documents["references/index.md"]
    for reference in wedding_adventure.references:
        assert reference.title in reference_index
        assert f"references/{reference.id}.md" in documents

    assert (
        "## Two doors, one record"
        in documents["references/6f8bbb6f-b719-491e-80b0-b276fc770d08.md"]
    )
    assert (
        "## Wheel, hearth, and lease"
        in documents["references/7110bb5a-b845-4e64-a43b-2536a05069c4.md"]
    )
    assert (
        "## Beneath the willows" in documents["references/d635958c-fcff-4993-a528-e05f6f4fc0d5.md"]
    )


def test_wedding_completed_adventure_demonstrates_the_complete_social_route(
    wedding_adventure: Adventure,
    wedding_state: PlayState,
    archived_wedding_state: PlayState,
) -> None:
    """Keep the named party, append-only correction, and mixed certification aligned."""
    projection = project_play_state(wedding_adventure, wedding_state)

    assert archived_wedding_state == wedding_state
    assert len(wedding_state.events) == 140
    assert len(projection.sessions) == 3
    assert projection.active_session_number is None
    assert tuple(session.title for session in projection.sessions) == (
        "The Same Words, Two Marriages",
        "Seven Baskets, Six Functions",
        "The Joining Light",
    )
    assert tuple(visit.encounter_id for visit in projection.visits) == (
        "house-of-open-measure",
        "vale-mill-and-hearth",
        "house-beneath-the-willows",
        "house-of-open-measure",
        "market-of-seven-baskets",
        "shrine-of-the-open-door",
        "reedwrights-yard",
        "bridge-of-three-tunes",
        "flood-meadow-and-old-ford",
        "wedding-between-the-banks",
    )
    assert tuple(visit.party_label for visit in projection.visits[1:3]) == (
        "Adel and Sella with Tomas and the Vale household",
        "Kest and Oren with Neris and the river household",
    )
    assert len(projection.spotted_clue_ids) == 59
    assert sum(len(item.missed_visit_numbers) for item in projection.clue_progress) == 1
    assert all(item.is_established for item in projection.revelation_progress)
    assert len(projection.corrections) == 1
    assert len(projection.consequences) == 11

    consequences = "\n".join(item.text for item in projection.consequences)
    assert "Marriage is certified with stated boundaries" in consequences
    assert "two household descriptions" in consequences
    assert "three-signal warning protocol" in consequences
    assert "empty abstention token" in consequences


def test_wedding_completed_play_summary_and_packet_are_reproducible(
    wedding_adventure: Adventure,
    wedding_state: PlayState,
) -> None:
    """Keep the generated packet synchronized with source and demonstrated journal."""
    report = validate_adventure(wedding_adventure)
    documents = render_adventure_documents(wedding_adventure, report, wedding_state)
    summary = render_play_summary(wedding_adventure, wedding_state)

    assert summary == (EXAMPLE_DIRECTORY / "generated" / "05-play-summary.md").read_text()
    assert "Events recorded: 140" in summary
    assert "Explicit sessions: 3" in summary
    assert "Visits recorded: 10" in summary
    assert "Unique leads found: 59 / 72" in summary
    assert "Corrections recorded: 1" in summary
    assert "The Four Open Hands" in summary

    assert "05-play-summary.md" in documents
    assert_rendered_documents_match(
        documents, EXAMPLE_DIRECTORY / "generated"
    )


def test_wedding_voice_and_completion_packet_is_present() -> None:
    """Protect the party, demonstration, aftermath, and completed voice packet."""
    party = (EXAMPLE_DIRECTORY / "PARTY-DESIGN.md").read_text()
    playthrough = (EXAMPLE_DIRECTORY / "FULL-PLAYTHROUGH.md").read_text()
    aftermath = (EXAMPLE_DIRECTORY / "AFTERMATH-AND-SEASONAL-STATES.md").read_text()
    quickstart = (EXAMPLE_DIRECTORY / "WITNESS-QUICKSTART.md").read_text()

    assert "# Party Design: The Four Open Hands" in party
    assert "## Adel Berren" in party
    assert "## Kest Larch" in party
    assert "## Sella Broth" in party
    assert "## Oren Chalk" in party
    assert "# Full Playthrough: The Four Open Hands" in playthrough
    assert "## Session One: The Same Words, Two Marriages" in playthrough
    assert "## Session Three: The Joining Light" in playthrough
    assert "marriage certified with stated boundaries" in playthrough
    assert "## Seasonal tests of the demonstrated marriage" in aftermath
    assert "### First flood warning" in aftermath
    assert "## Alternate certification states" in aftermath
    assert "## Split-party report" in quickstart
    assert "## Final witness scopes" in quickstart
