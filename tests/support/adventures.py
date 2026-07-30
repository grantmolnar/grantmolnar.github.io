"""Reusable authored adventures for tests."""

from __future__ import annotations

from dataclasses import replace

from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
    Encounter,
    Reference,
    ReferenceLink,
    Revelation,
)


def complete_four_encounter_adventure() -> Adventure:
    """Return a K4 clue graph satisfying all default validation rules."""
    encounter_ids = ("alpha", "beta", "gamma", "omega")
    encounters = tuple(
        Encounter(
            id=encounter_id,
            title=encounter_id.title(),
            summary=f"Summary for {encounter_id}.",
            start=encounter_id == "alpha",
            end=encounter_id == "omega",
        )
        for encounter_id in encounter_ids
    )
    revelations = tuple(
        Revelation(
            id=f"find-{encounter_id}",
            title=f"Find {encounter_id.title()}",
            description=f"The group can locate {encounter_id}.",
            unlocks_encounter_id=encounter_id,
            required=encounter_id != "alpha",
        )
        for encounter_id in encounter_ids
    )
    clues = tuple(
        Clue(
            id=f"{source}-to-{target}",
            title=f"{source} points to {target}",
            source_encounter_id=source,
            revelation_id=f"find-{target}",
        )
        for source in encounter_ids
        for target in encounter_ids
        if source != target
    )
    return Adventure(
        id="complete-four",
        title="Complete Four",
        synopsis="Four encounters form a complete clue graph.",
        premise="Investigate four connected encounters.",
        explanation="Every encounter points to every other encounter.",
        encounters=encounters,
        revelations=revelations,
        clues=clues,
    )


PERSON_REFERENCE_ID = "8e2bd3ba-20fb-456c-9c73-cb9bab481e26"
PLACE_REFERENCE_ID = "62e43f7e-b9d2-4e6b-a4db-483a42c8b73a"


def reference_library_adventure() -> Adventure:
    """Return a valid graph with representative references and contextual links."""
    adventure = complete_four_encounter_adventure()
    references = (
        Reference(
            id=PERSON_REFERENCE_ID,
            kind="person",
            title="Cora Pike",
            aliases=("The Housekeeper",),
            summary="The hall's observant housekeeper.",
            content="## Cora Pike\n\nCora protects the household before its owner.",
            tags=("staff", "witness"),
        ),
        Reference(
            id=PLACE_REFERENCE_ID,
            kind="place",
            title="Blackbriar Hall",
            summary="A decaying estate whose rooms host several encounters.",
            tags=("estate",),
        ),
    )
    encounters = (
        replace(
            adventure.encounters[0],
            reference_links=(
                ReferenceLink(
                    PERSON_REFERENCE_ID,
                    "Cora controls access to the first-floor rooms.",
                ),
                ReferenceLink(PLACE_REFERENCE_ID),
            ),
        ),
        replace(
            adventure.encounters[1],
            reference_links=(
                ReferenceLink(
                    PERSON_REFERENCE_ID,
                    "Cora may change allegiance after hearing the testimony.",
                ),
            ),
        ),
        *adventure.encounters[2:],
    )
    return replace(adventure, encounters=encounters, references=references)
