"""Interface-owned values shared by web request parsing and HTML rendering."""

from __future__ import annotations

from dataclasses import dataclass

from adventure_graph.application.encounter_authoring import EncounterDetailResult
from adventure_graph.application.project_browsing import (
    AdventureOverviewResult,
    ClueDetailResult,
    RevelationDetailResult,
)
from adventure_graph.application.reference_authoring import ReferenceDetailResult
from adventure_graph.domain.adventure import AdventureTags


@dataclass(frozen=True, slots=True)
class AdventureEditValues:
    """Values displayed in the adventure metadata editor."""

    title: str
    synopsis: str
    premise: str
    explanation: str
    tags: AdventureTags | None
    expected_revision: str

    @classmethod
    def from_result(cls, result: AdventureOverviewResult) -> AdventureEditValues:
        """Build editor values from the current adventure overview."""
        adventure = result.adventure
        return cls(
            title=adventure.title,
            synopsis=adventure.synopsis,
            premise=adventure.premise,
            explanation=adventure.explanation,
            tags=adventure.tags,
            expected_revision=result.revision.value,
        )


@dataclass(frozen=True, slots=True)
class EncounterCreateValues:
    """Values displayed in the encounter creation form."""

    title: str = ""
    summary: str = ""
    opening_view: str = ""
    content: str = ""
    tags: str = ""
    required: bool = True
    start: bool = False
    end: bool = False
    expected_revision: str = ""
    return_to: str = ""


@dataclass(frozen=True, slots=True)
class EncounterEditValues:
    """Values displayed in the encounter editor."""

    title: str
    summary: str
    opening_view: str
    content: str
    tags: str
    required: bool
    start: bool
    end: bool
    expected_revision: str
    return_to: str = ""

    @classmethod
    def from_result(cls, result: EncounterDetailResult) -> EncounterEditValues:
        """Build editor values from the currently loaded encounter detail."""
        encounter = result.detail.encounter
        return cls(
            title=encounter.title,
            summary=encounter.summary,
            opening_view=encounter.opening_view,
            content=encounter.content,
            tags=", ".join(encounter.tags),
            required=encounter.required,
            start=encounter.start,
            end=encounter.end,
            expected_revision=result.revision.value,
        )


@dataclass(frozen=True, slots=True)
class ClueEditValues:
    """Values displayed in the clue editor."""

    title: str
    source_encounter_id: str
    revelation_id: str
    description: str
    discovery: str
    expected_revision: str

    @classmethod
    def from_result(cls, result: ClueDetailResult) -> ClueEditValues:
        """Build editor values from the current clue detail."""
        clue = result.detail.clue
        return cls(
            title=clue.title,
            source_encounter_id=clue.source_encounter_id,
            revelation_id=clue.revelation_id,
            description=clue.description,
            discovery=clue.discovery,
            expected_revision=result.revision.value,
        )


@dataclass(frozen=True, slots=True)
class RevelationEditValues:
    """Values displayed in the revelation editor."""

    title: str
    description: str
    unlocks_encounter_id: str
    required: bool
    expected_revision: str

    @classmethod
    def from_result(cls, result: RevelationDetailResult) -> RevelationEditValues:
        """Build editor values from the current revelation detail."""
        revelation = result.detail.revelation
        return cls(
            title=revelation.title,
            description=revelation.description,
            unlocks_encounter_id=revelation.unlocks_encounter_id or "",
            required=revelation.required,
            expected_revision=result.revision.value,
        )


@dataclass(frozen=True, slots=True)
class ClueCreateValues:
    """Values displayed in the clue creation form."""

    title: str = ""
    source_encounter_id: str = ""
    revelation_id: str = ""
    description: str = ""
    discovery: str = "search"
    expected_revision: str = ""
    return_to: str = ""


@dataclass(frozen=True, slots=True)
class RevelationCreateValues:
    """Values displayed in the revelation creation form."""

    title: str = ""
    description: str = ""
    unlocks_encounter_id: str = ""
    required: bool = True
    source_encounter_id: str = ""
    expected_revision: str = ""
    return_to: str = ""


@dataclass(frozen=True, slots=True)
class ReferenceCreateValues:
    """Values displayed in reference creation and create-and-link forms."""

    kind: str = "person"
    title: str = ""
    aliases: str = ""
    summary: str = ""
    content: str = ""
    tags: str = ""
    expected_revision: str = ""
    encounter_id: str = ""
    context: str = ""
    return_to: str = ""


@dataclass(frozen=True, slots=True)
class ReferenceEditValues:
    """Values displayed in the reference editor."""

    kind: str
    title: str
    aliases: str
    summary: str
    content: str
    tags: str
    expected_revision: str

    @classmethod
    def from_result(cls, result: ReferenceDetailResult) -> ReferenceEditValues:
        """Build editor values from the current reference detail."""
        reference = result.detail.reference
        return cls(
            kind=reference.kind,
            title=reference.title,
            aliases=", ".join(reference.aliases),
            summary=reference.summary,
            content=reference.content,
            tags=", ".join(reference.tags),
            expected_revision=result.revision.value,
        )


@dataclass(frozen=True, slots=True)
class RunFormValues:
    """Values preserved after a rejected session operation."""

    visit_encounter_id: str = ""
    visit_clue_ids: tuple[str, ...] = ()
    visit_note: str = ""
    clue_id: str = ""
    clue_visit_number: int | None = None
    revelation_id: str = ""
    supporting_clue_ids: tuple[str, ...] = ()
    revelation_note: str = ""
    unlock_encounter_id: str = ""
    unlock_reason: str = ""
    note_visit_number: int | None = None
    note_text: str = ""
    consequence_encounter_id: str = ""
    consequence_text: str = ""
    correction_reason: str = ""


@dataclass(frozen=True, slots=True)
class PlayFormValues:
    """Values preserved after a rejected Play mode operation."""

    focus_encounter_id: str = ""
    selected_reference_id: str = ""
    reference_note_text: str = ""
    session_title: str = ""
    session_played_on: str = ""
    session_participants: str = ""
    session_attendance_note: str = ""
    session_opening_note: str = ""
    session_closing_note: str = ""
    enter_encounter_id: str = ""
    enter_party_label: str = ""
    clue_id: str = ""
    revelation_id: str = ""
    supporting_clue_ids: tuple[str, ...] = ()
    revelation_note: str = ""
    judgment_reason: str = ""
    unlock_encounter_id: str = ""
    unlock_reason: str = ""
    note_visit_number: int | None = None
    note_text: str = ""
    consequence_encounter_id: str = ""
    consequence_text: str = ""
    transition_source_visit_number: int | None = None
    transition_note: str = ""
    transition_spotted_clue_ids: tuple[str, ...] = ()
    transition_missed_clue_ids: tuple[str, ...] = ()
    transition_revelation_ids: tuple[str, ...] = ()
    transition_consequence: str = ""
    transition_destination_encounter_id: str = ""
    transition_party_label: str = ""
    dice_expression: str = ""
    dice_label: str = ""


@dataclass(frozen=True, slots=True)
class PageNotice:
    """One interface-level status message for the current response."""

    level: str
    heading: str
    message: str
