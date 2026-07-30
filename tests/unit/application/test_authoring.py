"""Tests for immutable authoring operations and dependency analysis."""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    PLACE_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)

from adventure_graph.application.authoring import (
    AuthoringError,
    add_clue,
    add_encounter,
    add_reference,
    add_revelation,
    clue_dependencies,
    encounter_dependencies,
    link_reference,
    reference_dependencies,
    remap_play_state_identifiers,
    remove_clue,
    remove_encounter,
    remove_reference,
    remove_revelation,
    rename_clue,
    rename_encounter,
    rename_revelation,
    revelation_dependencies,
    unlink_reference,
    update_clue,
    update_encounter,
    update_reference,
    update_revelation,
)
from adventure_graph.domain.adventure import (
    Clue,
    Encounter,
    Reference,
    ReferenceLink,
    Revelation,
)
from adventure_graph.domain.play_events import (
    ClueSpottedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    RevelationEstablishedEvent,
    VisitNoteRecordedEvent,
)
from adventure_graph.domain.play_state import PlayState


def test_encounters_revelations_and_clues_can_be_appended_in_sequence() -> None:
    adventure = complete_four_encounter_adventure()
    adventure = add_encounter(adventure, Encounter("delta", "Delta", "A new encounter."))
    adventure = add_revelation(
        adventure,
        Revelation("find-delta", "Find Delta", "Delta can be located.", "delta"),
    )
    adventure = add_clue(
        adventure,
        Clue("alpha-to-delta", "A route to Delta", "alpha", "find-delta"),
    )

    assert adventure.encounters[-1].id == "delta"
    assert adventure.revelations[-1].id == "find-delta"
    assert adventure.clues[-1].id == "alpha-to-delta"


def test_add_encounter_rejects_an_existing_identifier() -> None:
    adventure = complete_four_encounter_adventure()

    with pytest.raises(AuthoringError, match="Encounter 'alpha' already exists"):
        add_encounter(adventure, Encounter("alpha", "Duplicate Alpha", "Duplicate."))


def test_clue_authoring_rejects_unknown_source_or_revelation() -> None:
    adventure = complete_four_encounter_adventure()

    with pytest.raises(AuthoringError, match="Unknown lead source"):
        add_clue(adventure, Clue("bad", "Bad", "missing", "find-beta"))

    with pytest.raises(AuthoringError, match="Unknown lead revelation"):
        add_clue(adventure, Clue("bad", "Bad", "alpha", "missing"))


def test_update_operations_preserve_order_and_validate_endpoints() -> None:
    adventure = complete_four_encounter_adventure()
    original_encounter_ids = tuple(encounter.id for encounter in adventure.encounters)
    original_revelation_ids = tuple(revelation.id for revelation in adventure.revelations)
    original_clue_ids = tuple(clue.id for clue in adventure.clues)

    adventure = update_encounter(
        adventure,
        replace(adventure.encounter_index()["alpha"], title="Alpha Revised", tags=("urban",)),
    )
    adventure = update_revelation(
        adventure,
        replace(
            adventure.revelation_index()["find-beta"],
            title="Locate Beta",
            unlocks_encounter_id="gamma",
        ),
    )
    adventure = update_clue(
        adventure,
        replace(
            adventure.clue_index()["alpha-to-beta"],
            source_encounter_id="omega",
            revelation_id="find-gamma",
        ),
    )

    assert tuple(encounter.id for encounter in adventure.encounters) == original_encounter_ids
    assert tuple(revelation.id for revelation in adventure.revelations) == original_revelation_ids
    assert tuple(clue.id for clue in adventure.clues) == original_clue_ids
    assert adventure.encounter_index()["alpha"].title == "Alpha Revised"
    assert adventure.revelation_index()["find-beta"].unlocks_encounter_id == "gamma"
    assert adventure.clue_index()["alpha-to-beta"].source_encounter_id == "omega"

    with pytest.raises(AuthoringError, match="Unknown unlocked encounter"):
        update_revelation(
            adventure,
            replace(adventure.revelation_index()["find-beta"], unlocks_encounter_id="missing"),
        )
    with pytest.raises(AuthoringError, match="Unknown lead source"):
        update_clue(
            adventure,
            replace(adventure.clue_index()["alpha-to-beta"], source_encounter_id="missing"),
        )


def test_renames_rewrite_every_authored_reference() -> None:
    adventure = complete_four_encounter_adventure()

    adventure = rename_encounter(adventure, "beta", "bravo")
    assert "bravo" in adventure.encounter_index()
    assert "beta" not in adventure.encounter_index()
    assert adventure.revelation_index()["find-beta"].unlocks_encounter_id == "bravo"
    assert all(clue.source_encounter_id != "beta" for clue in adventure.clues)
    assert {
        clue.source_encounter_id for clue in adventure.clues if clue.id.startswith("beta-to-")
    } == {"bravo"}

    adventure = rename_revelation(adventure, "find-beta", "locate-bravo")
    assert "locate-bravo" in adventure.revelation_index()
    assert all(clue.revelation_id != "find-beta" for clue in adventure.clues)
    assert {clue.revelation_id for clue in adventure.clues if clue.id.endswith("-to-beta")} == {
        "locate-bravo"
    }

    adventure = rename_clue(adventure, "alpha-to-beta", "alpha-ledger")
    assert "alpha-ledger" in adventure.clue_index()
    assert "alpha-to-beta" not in adventure.clue_index()


def test_rename_rejects_missing_duplicate_empty_and_noop_identifiers() -> None:
    adventure = complete_four_encounter_adventure()

    with pytest.raises(AuthoringError, match="Unknown encounter"):
        rename_encounter(adventure, "missing", "new")
    with pytest.raises(AuthoringError, match="already exists"):
        rename_encounter(adventure, "alpha", "beta")
    with pytest.raises(AuthoringError, match="cannot be empty"):
        rename_revelation(adventure, "find-alpha", "")
    with pytest.raises(AuthoringError, match="already has that identifier"):
        rename_clue(adventure, "alpha-to-beta", "alpha-to-beta")


def test_dependency_queries_describe_authored_impact() -> None:
    adventure = complete_four_encounter_adventure()

    encounter_impact = encounter_dependencies(adventure, "beta")
    assert encounter_impact.source_clue_ids == ("beta-to-alpha", "beta-to-gamma", "beta-to-omega")
    assert encounter_impact.unlocking_revelation_ids == ("find-beta",)
    assert encounter_impact.has_dependencies

    revelation_impact = revelation_dependencies(adventure, "find-beta")
    assert revelation_impact.supporting_clue_ids == (
        "alpha-to-beta",
        "gamma-to-beta",
        "omega-to-beta",
    )
    assert revelation_impact.has_dependencies

    clue_impact = clue_dependencies(adventure, "alpha-to-beta")
    assert clue_impact.source_encounter_id == "alpha"
    assert clue_impact.revelation_id == "find-beta"


def test_removal_refuses_dependencies_and_cascade_is_explicit() -> None:
    adventure = complete_four_encounter_adventure()

    with pytest.raises(AuthoringError, match=r"source leads.*unlocking revelations"):
        remove_encounter(adventure, "beta")
    without_beta = remove_encounter(adventure, "beta", cascade=True)
    assert "beta" not in without_beta.encounter_index()
    assert all(clue.source_encounter_id != "beta" for clue in without_beta.clues)
    assert without_beta.revelation_index()["find-beta"].unlocks_encounter_id is None
    assert len(without_beta.clues) == len(adventure.clues) - 3

    with pytest.raises(AuthoringError, match="supporting leads exist"):
        remove_revelation(adventure, "find-beta")
    without_revelation = remove_revelation(adventure, "find-beta", cascade=True)
    assert "find-beta" not in without_revelation.revelation_index()
    assert all(clue.revelation_id != "find-beta" for clue in without_revelation.clues)
    assert len(without_revelation.clues) == len(adventure.clues) - 3

    without_clue = remove_clue(adventure, "alpha-to-beta")
    assert "alpha-to-beta" not in without_clue.clue_index()


def test_play_state_identifier_remap_updates_all_referencing_event_types() -> None:
    state = PlayState(
        adventure_id="complete-four",
        events=(
            EncounterVisitedEvent(1, 1, "alpha", 1),
            ClueSpottedEvent(2, "alpha-to-beta", 1, 2),
            RevelationEstablishedEvent(3, "find-beta", 3, ("alpha-to-beta",), "Basis"),
            EncounterUnlockedEvent(4, "beta", 3, "find-beta", ""),
            VisitNoteRecordedEvent(5, 1, "Note", 4),
            EncounterConsequenceRecordedEvent(6, "beta", "Changed", 5),
        ),
    )

    remapped = remap_play_state_identifiers(
        state,
        encounter_ids={"alpha": "atrium", "beta": "bravo"},
        revelation_ids={"find-beta": "locate-bravo"},
        clue_ids={"alpha-to-beta": "atrium-ledger"},
    )

    assert remapped.events == (
        EncounterVisitedEvent(1, 1, "atrium", 1),
        ClueSpottedEvent(2, "atrium-ledger", 1, 2),
        RevelationEstablishedEvent(3, "locate-bravo", 3, ("atrium-ledger",), "Basis"),
        EncounterUnlockedEvent(4, "bravo", 3, "locate-bravo", ""),
        VisitNoteRecordedEvent(5, 1, "Note", 4),
        EncounterConsequenceRecordedEvent(6, "bravo", "Changed", 5),
    )


def test_reference_operations_preserve_authored_order_and_link_order() -> None:
    adventure = complete_four_encounter_adventure()
    first = Reference(PERSON_REFERENCE_ID, "person", "Cora Pike")
    second = Reference(PLACE_REFERENCE_ID, "place", "Blackbriar Hall")

    adventure = add_reference(adventure, first)
    adventure = add_reference(adventure, second)
    adventure = update_reference(adventure, replace(first, title="Cora Pike Revised"))
    adventure = link_reference(
        adventure,
        "alpha",
        ReferenceLink(PERSON_REFERENCE_ID, "Cora controls access."),
    )
    adventure = link_reference(adventure, "alpha", ReferenceLink(PLACE_REFERENCE_ID))

    assert tuple(reference.id for reference in adventure.references) == (
        PERSON_REFERENCE_ID,
        PLACE_REFERENCE_ID,
    )
    assert tuple(
        link.reference_id for link in adventure.encounter_index()["alpha"].reference_links
    ) == (PERSON_REFERENCE_ID, PLACE_REFERENCE_ID)
    assert adventure.reference_index()[PERSON_REFERENCE_ID].title == "Cora Pike Revised"

    adventure = unlink_reference(adventure, "alpha", PERSON_REFERENCE_ID)
    assert adventure.encounter_index()["alpha"].reference_links == (
        ReferenceLink(PLACE_REFERENCE_ID),
    )


def test_reference_linking_fails_closed_for_unknown_duplicate_and_missing_pairs() -> None:
    adventure = reference_library_adventure()

    with pytest.raises(AuthoringError, match="Unknown reference"):
        link_reference(
            adventure,
            "gamma",
            ReferenceLink("4e66fa28-aac8-4b77-a840-a0ae6ad2a4cb"),
        )
    with pytest.raises(AuthoringError, match="already links reference"):
        link_reference(adventure, "alpha", ReferenceLink(PERSON_REFERENCE_ID))
    with pytest.raises(AuthoringError, match="does not link reference"):
        unlink_reference(adventure, "gamma", PERSON_REFERENCE_ID)


def test_reference_dependencies_and_removal_are_explicit_and_bounded() -> None:
    adventure = reference_library_adventure()

    dependencies = reference_dependencies(adventure, PERSON_REFERENCE_ID)
    assert tuple(link.encounter_id for link in dependencies.links) == ("alpha", "beta")
    assert dependencies.links[0].context == "Cora controls access to the first-floor rooms."

    with pytest.raises(AuthoringError, match="encounter links exist"):
        remove_reference(adventure, PERSON_REFERENCE_ID)
    removed = remove_reference(adventure, PERSON_REFERENCE_ID, cascade=True)

    assert PERSON_REFERENCE_ID not in removed.reference_index()
    assert PLACE_REFERENCE_ID in removed.reference_index()
    assert all(
        link.reference_id != PERSON_REFERENCE_ID
        for encounter in removed.encounters
        for link in encounter.reference_links
    )
    assert tuple(encounter.id for encounter in removed.encounters) == (
        "alpha",
        "beta",
        "gamma",
        "omega",
    )


def test_encounter_removal_treats_reference_links_as_subordinate_dependencies() -> None:
    adventure = reference_library_adventure()
    dependencies = encounter_dependencies(adventure, "alpha")

    assert dependencies.linked_reference_ids == (PERSON_REFERENCE_ID, PLACE_REFERENCE_ID)
    with pytest.raises(AuthoringError, match="reference links"):
        remove_encounter(adventure, "alpha")

    removed = remove_encounter(adventure, "alpha", cascade=True)
    assert "alpha" not in removed.encounter_index()
    assert tuple(reference.id for reference in removed.references) == (
        PERSON_REFERENCE_ID,
        PLACE_REFERENCE_ID,
    )
