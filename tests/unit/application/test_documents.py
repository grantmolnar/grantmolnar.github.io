"""Tests for generated authoring and runtime documents."""

from __future__ import annotations

from dataclasses import replace

from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    PLACE_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)

from adventure_graph.application.documents import (
    render_adventure_documents,
    render_play_summary,
)
from adventure_graph.application.play_tracking import (
    end_session,
    establish_revelation,
    foreclose_revelation,
    miss_clue,
    new_play_state,
    record_encounter_consequence,
    record_reference_note,
    record_visit,
    reopen_revelation,
    start_session,
)
from adventure_graph.domain.adventure import Reference
from adventure_graph.domain.play_events import (
    DiceGroupResult,
    DiceModifierResult,
    DiceRollRecordedEvent,
)
from adventure_graph.domain.validation import validate_adventure


def test_generated_clue_and_revelation_lists_are_dual_views() -> None:
    adventure = complete_four_encounter_adventure()
    documents = render_adventure_documents(adventure, validate_adventure(adventure))

    clue_list = documents["02-clue-list.md"]
    revelation_list = documents["03-revelation-list.md"]
    assert "Alpha (`alpha`)" in clue_list
    assert "alpha points to beta" in clue_list
    assert "Find Beta (`find-beta`)" in revelation_list
    assert "alpha points to beta" in revelation_list
    assert "Alpha (`alpha`)" in revelation_list


def test_generated_packet_includes_stable_reference_index_sheets_and_context() -> None:
    adventure = reference_library_adventure()

    documents = render_adventure_documents(adventure, validate_adventure(adventure))

    assert "references/index.md" in documents
    assert f"references/{PERSON_REFERENCE_ID}.md" in documents
    assert f"references/{PLACE_REFERENCE_ID}.md" in documents
    index = documents["references/index.md"]
    assert index.index("## People") < index.index("## Places")
    assert f"[**Cora Pike**]({PERSON_REFERENCE_ID}.md)" in index
    assert "Aliases: The Housekeeper." in index
    sheet = documents[f"references/{PERSON_REFERENCE_ID}.md"]
    assert "## Encounter Backlinks" in sheet
    assert "[**Alpha**](../encounters/alpha.md)" in sheet
    assert "Cora controls access to the first-floor rooms." in sheet
    assert "[**Beta**](../encounters/beta.md)" in sheet
    encounter = documents["encounters/alpha.md"]
    assert encounter.index("[**Cora Pike**]") < encounter.index("[**Blackbriar Hall**]")
    assert "Cora controls access to the first-floor rooms." in encounter


def test_reference_sheet_names_remain_stable_under_title_edits() -> None:
    adventure = reference_library_adventure()
    renamed = replace(
        adventure,
        references=(
            replace(adventure.references[0], title="Cora Vale"),
            adventure.references[1],
        ),
    )

    before = render_adventure_documents(adventure, validate_adventure(adventure))
    after = render_adventure_documents(renamed, validate_adventure(renamed))

    stable_name = f"references/{PERSON_REFERENCE_ID}.md"
    assert stable_name in before
    assert stable_name in after
    assert "# Cora Vale" in after[stable_name]


def test_reference_index_groups_by_kind_and_preserves_authored_order_within_groups() -> None:
    adventure = reference_library_adventure()
    extra = (
        Reference(
            "33333333-3333-4333-8333-333333333333",
            "organization",
            "Saint Mercy House",
        ),
        Reference(
            "44444444-4444-4444-8444-444444444444",
            "object",
            "Aulonite Seal",
        ),
        Reference(
            "55555555-5555-4555-8555-555555555555",
            "person",
            "Aster Pike",
        ),
        Reference(
            "66666666-6666-4666-8666-666666666666",
            "other",
            "The Long Silence",
        ),
    )
    reordered = replace(adventure, references=(*adventure.references, *extra))

    index = render_adventure_documents(reordered, validate_adventure(reordered))[
        "references/index.md"
    ]

    assert index.index("## People") < index.index("## Places")
    assert index.index("## Places") < index.index("## Organizations")
    assert index.index("## Organizations") < index.index("## Objects")
    assert index.index("## Objects") < index.index("## Other")
    assert index.index("Cora Pike") < index.index("Aster Pike")


def test_reference_light_packet_omits_reference_directory() -> None:
    adventure = complete_four_encounter_adventure()

    documents = render_adventure_documents(adventure, validate_adventure(adventure))

    assert not any(name.startswith("references/") for name in documents)
    assert "## Linked References" not in documents["encounters/alpha.md"]


def test_play_summary_separates_spotted_support_from_established_revelations() -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta", "alpha-to-gamma"),
    )
    state = establish_revelation(
        adventure,
        state,
        "find-beta",
        ("alpha-to-beta",),
        "The address was decisive.",
    )
    state = record_encounter_consequence(
        adventure,
        state,
        "alpha",
        "The witness fled after questioning.",
    )

    summary = render_play_summary(adventure, state)

    assert "Supported but Unconfirmed Revelations" in summary
    assert "Find Gamma" in summary
    assert "Established Revelations" in summary
    assert "Find Beta" in summary
    assert "The address was decisive." in summary
    assert "Encounter Consequences" in summary
    assert "The witness fled after questioning." in summary
    assert "Unique leads found: 2 / 12" in summary


def test_empty_play_summary_lists_entry_encounter_as_available() -> None:
    adventure = complete_four_encounter_adventure()

    summary = render_play_summary(adventure, new_play_state(adventure))

    assert "No play events recorded" in summary
    assert "**Alpha** (`alpha`) — unvisited; start encounter" in summary
    assert "**Beta** (`beta`)" in summary


def test_play_summary_renders_schema_v6_session_and_judgment_events() -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(
        new_play_state(adventure),
        title="The western breach",
        participants=("Mara", "Sera"),
        opening_note="The party resumed beneath the aqueduct.",
    )
    state = record_visit(adventure, state, "alpha", party_label="Canal team")
    state = miss_clue(adventure, state, "alpha-to-beta", 1)
    state = foreclose_revelation(adventure, state, "find-beta", "The witness left the city.")
    state = reopen_revelation(adventure, state, "find-beta", "The witness returned under guard.")
    state = replace(
        state,
        events=(
            *state.events,
            DiceRollRecordedEvent(
                sequence=len(state.events) + 1,
                expression="2d8 + 3",
                terms=(DiceGroupResult(1, 8, (6, 3)), DiceModifierResult(3)),
                total=12,
                operation_number=state.events[-1].operation_number + 1,
                label="Hold the gate",
            ),
        ),
    )
    state = end_session(state, "The party withdrew before dusk.")

    summary = render_play_summary(adventure, state)

    assert "Explicit sessions: 1" in summary
    assert "Session started" in summary
    assert "Canal team" in summary
    assert "Lead missed" in summary
    assert "Revelation foreclosed" in summary
    assert "Revelation reopened" in summary
    assert "Dice roll recorded" in summary
    assert "Hold the gate" in summary
    assert "Session ended" in summary
    assert "Leads missed during this visit" in summary


def test_play_summary_renders_reference_notes_with_stable_identity() -> None:
    adventure = reference_library_adventure()
    state = record_reference_note(
        adventure,
        new_play_state(adventure),
        PERSON_REFERENCE_ID,
        "Cora now trusts the party with the west stair key.",
    )

    summary = render_play_summary(adventure, state)

    assert "Reference note" in summary
    assert "Cora Pike" in summary
    assert PERSON_REFERENCE_ID in summary
    assert "Cora now trusts the party with the west stair key." in summary


def test_validation_document_renders_cut_witness_repairs_and_issue_repairs() -> None:
    adventure = complete_four_encounter_adventure()
    retained = {
        "alpha-to-beta",
        "beta-to-alpha",
        "beta-to-gamma",
        "gamma-to-beta",
        "gamma-to-omega",
        "omega-to-gamma",
    }
    sparse = replace(
        adventure,
        clues=tuple(clue for clue in adventure.clues if clue.id in retained),
        validation_policy=replace(
            adventure.validation_policy,
            minimum_clues_per_revelation=0,
            minimum_source_encounters_per_revelation=0,
            minimum_outgoing_clues_per_encounter=0,
            minimum_distinct_encounter_targets_per_encounter=0,
        ),
    )

    document = render_adventure_documents(sparse, validate_adventure(sparse))[
        "04-validation-report.md"
    ]

    assert "## Minimum-Cut Witness" in document
    assert "**Partition A:** `alpha`" in document
    assert "**Cut edges:** `alpha`—`beta`" in document
    assert "## Structural Repair Candidates" in document
    assert "`alpha` supporting `find-gamma`" in document
    assert "**Repair:** Add at least 2 distinct cross-partition" in document
