"""Immutable authoring operations and dependency analysis."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import assert_never

from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
    Encounter,
    Reference,
    ReferenceLink,
    Revelation,
)
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    DiceRollRecordedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    PlayEvent,
    PlayOperationVoidedEvent,
    ReferenceNoteRecordedEvent,
    RevelationEstablishedEvent,
    RevelationForeclosedEvent,
    RevelationReopenedEvent,
    SessionEndedEvent,
    SessionStartedEvent,
    VisitNoteRecordedEvent,
)
from adventure_graph.domain.play_state import PlayState


class AuthoringError(ValueError):
    """Raised when an authoring operation would make identifiers inconsistent."""


@dataclass(frozen=True, slots=True)
class EncounterDependencies:
    """Authored records that directly depend on one encounter identifier."""

    encounter_id: str
    source_clue_ids: tuple[str, ...]
    unlocking_revelation_ids: tuple[str, ...]
    linked_reference_ids: tuple[str, ...]

    @property
    def has_dependencies(self) -> bool:
        """Return whether removing the encounter would require dependent changes."""
        return bool(
            self.source_clue_ids or self.unlocking_revelation_ids or self.linked_reference_ids
        )


@dataclass(frozen=True, slots=True)
class RevelationDependencies:
    """Authored clues that directly depend on one revelation identifier."""

    revelation_id: str
    supporting_clue_ids: tuple[str, ...]

    @property
    def has_dependencies(self) -> bool:
        """Return whether removing the revelation would require dependent changes."""
        return bool(self.supporting_clue_ids)


@dataclass(frozen=True, slots=True)
class ClueDependencies:
    """Authored endpoint records referenced by one clue."""

    clue_id: str
    source_encounter_id: str
    revelation_id: str


@dataclass(frozen=True, slots=True)
class ReferenceDependency:
    """One encounter-owned link that depends on a reference record."""

    encounter_id: str
    context: str


@dataclass(frozen=True, slots=True)
class ReferenceDependencies:
    """Encounter links that directly depend on one reference identifier."""

    reference_id: str
    links: tuple[ReferenceDependency, ...]

    @property
    def has_dependencies(self) -> bool:
        """Return whether removing the reference would require unlinking encounters."""
        return bool(self.links)


def add_encounter(adventure: Adventure, encounter: Encounter) -> Adventure:
    """Append an encounter after enforcing identifier uniqueness."""
    if encounter.id in adventure.encounter_index():
        raise AuthoringError(f"Encounter {encounter.id!r} already exists.")
    return replace(adventure, encounters=(*adventure.encounters, encounter))


def add_reference(adventure: Adventure, reference: Reference) -> Adventure:
    """Append a reference after enforcing stable-identifier uniqueness."""
    if reference.id in adventure.reference_index():
        raise AuthoringError(f"Reference {reference.id!r} already exists.")
    return replace(adventure, references=(*adventure.references, reference))


def add_revelation(adventure: Adventure, revelation: Revelation) -> Adventure:
    """Append a revelation after validating its identifier and optional destination."""
    if revelation.id in adventure.revelation_index():
        raise AuthoringError(f"Revelation {revelation.id!r} already exists.")
    _require_revelation_destination(adventure, revelation)
    return replace(adventure, revelations=(*adventure.revelations, revelation))


def add_clue(adventure: Adventure, clue: Clue) -> Adventure:
    """Append a clue after validating its identifier, source, and revelation."""
    if clue.id in adventure.clue_index():
        raise AuthoringError(f"Lead {clue.id!r} already exists.")
    _require_clue_endpoints(adventure, clue)
    return replace(adventure, clues=(*adventure.clues, clue))


def update_encounter(adventure: Adventure, encounter: Encounter) -> Adventure:
    """Replace one encounter without changing its identifier or list position."""
    _require_encounter(adventure, encounter.id)
    return replace(
        adventure,
        encounters=tuple(
            encounter if current.id == encounter.id else current for current in adventure.encounters
        ),
    )


def update_reference(adventure: Adventure, reference: Reference) -> Adventure:
    """Replace one reference without changing its identity or authored position."""
    _require_reference(adventure, reference.id)
    return replace(
        adventure,
        references=tuple(
            reference if current.id == reference.id else current for current in adventure.references
        ),
    )


def link_reference(
    adventure: Adventure,
    encounter_id: str,
    link: ReferenceLink,
) -> Adventure:
    """Append one contextual reference link to an encounter."""
    encounter = _require_encounter(adventure, encounter_id)
    _require_reference(adventure, link.reference_id)
    if any(current.reference_id == link.reference_id for current in encounter.reference_links):
        raise AuthoringError(
            f"Encounter {encounter_id!r} already links reference {link.reference_id!r}."
        )
    return update_encounter(
        adventure,
        replace(encounter, reference_links=(*encounter.reference_links, link)),
    )


def unlink_reference(
    adventure: Adventure,
    encounter_id: str,
    reference_id: str,
) -> Adventure:
    """Remove one encounter/reference pair while preserving all other link order."""
    encounter = _require_encounter(adventure, encounter_id)
    if not any(link.reference_id == reference_id for link in encounter.reference_links):
        raise AuthoringError(
            f"Encounter {encounter_id!r} does not link reference {reference_id!r}."
        )
    return update_encounter(
        adventure,
        replace(
            encounter,
            reference_links=tuple(
                link for link in encounter.reference_links if link.reference_id != reference_id
            ),
        ),
    )


def update_revelation(adventure: Adventure, revelation: Revelation) -> Adventure:
    """Replace one revelation after validating its optional destination."""
    _require_revelation(adventure, revelation.id)
    _require_revelation_destination(adventure, revelation)
    return replace(
        adventure,
        revelations=tuple(
            revelation if current.id == revelation.id else current
            for current in adventure.revelations
        ),
    )


def update_clue(adventure: Adventure, clue: Clue) -> Adventure:
    """Replace one clue after validating its source and revelation endpoints."""
    _require_clue(adventure, clue.id)
    _require_clue_endpoints(adventure, clue)
    return replace(
        adventure,
        clues=tuple(clue if current.id == clue.id else current for current in adventure.clues),
    )


def rename_encounter(adventure: Adventure, old_id: str, new_id: str) -> Adventure:
    """Rename an encounter and update all authored references atomically in memory."""
    encounter = _require_encounter(adventure, old_id)
    _require_new_identifier(adventure.encounter_index(), "Encounter", old_id, new_id)
    renamed = replace(encounter, id=new_id)
    return replace(
        adventure,
        encounters=tuple(
            renamed if current.id == old_id else current for current in adventure.encounters
        ),
        revelations=tuple(
            replace(revelation, unlocks_encounter_id=new_id)
            if revelation.unlocks_encounter_id == old_id
            else revelation
            for revelation in adventure.revelations
        ),
        clues=tuple(
            (
                replace(clue, source_encounter_id=new_id)
                if clue.source_encounter_id == old_id
                else clue
            )
            for clue in adventure.clues
        ),
    )


def rename_revelation(adventure: Adventure, old_id: str, new_id: str) -> Adventure:
    """Rename a revelation and update all supporting clues atomically in memory."""
    revelation = _require_revelation(adventure, old_id)
    _require_new_identifier(adventure.revelation_index(), "Revelation", old_id, new_id)
    renamed = replace(revelation, id=new_id)
    return replace(
        adventure,
        revelations=tuple(
            renamed if current.id == old_id else current for current in adventure.revelations
        ),
        clues=tuple(
            replace(clue, revelation_id=new_id) if clue.revelation_id == old_id else clue
            for clue in adventure.clues
        ),
    )


def rename_clue(adventure: Adventure, old_id: str, new_id: str) -> Adventure:
    """Rename a clue without changing its source or supported revelation."""
    clue = _require_clue(adventure, old_id)
    _require_new_identifier(adventure.clue_index(), "Lead", old_id, new_id)
    renamed = replace(clue, id=new_id)
    return replace(
        adventure,
        clues=tuple(renamed if current.id == old_id else current for current in adventure.clues),
    )


def encounter_dependencies(adventure: Adventure, encounter_id: str) -> EncounterDependencies:
    """Return every authored record whose reference depends on one encounter."""
    encounter = _require_encounter(adventure, encounter_id)
    return EncounterDependencies(
        encounter_id=encounter_id,
        source_clue_ids=tuple(
            clue.id for clue in adventure.clues if clue.source_encounter_id == encounter_id
        ),
        unlocking_revelation_ids=tuple(
            revelation.id
            for revelation in adventure.revelations
            if revelation.unlocks_encounter_id == encounter_id
        ),
        linked_reference_ids=tuple(link.reference_id for link in encounter.reference_links),
    )


def reference_dependencies(adventure: Adventure, reference_id: str) -> ReferenceDependencies:
    """Return every encounter link that depends on one reference."""
    _require_reference(adventure, reference_id)
    return ReferenceDependencies(
        reference_id=reference_id,
        links=tuple(
            ReferenceDependency(encounter.id, link.context)
            for encounter in adventure.encounters
            for link in encounter.reference_links
            if link.reference_id == reference_id
        ),
    )


def revelation_dependencies(adventure: Adventure, revelation_id: str) -> RevelationDependencies:
    """Return every authored clue that supports one revelation."""
    _require_revelation(adventure, revelation_id)
    return RevelationDependencies(
        revelation_id=revelation_id,
        supporting_clue_ids=tuple(
            clue.id for clue in adventure.clues if clue.revelation_id == revelation_id
        ),
    )


def clue_dependencies(adventure: Adventure, clue_id: str) -> ClueDependencies:
    """Return the authored source and revelation endpoints of one clue."""
    clue = _require_clue(adventure, clue_id)
    return ClueDependencies(
        clue_id=clue_id,
        source_encounter_id=clue.source_encounter_id,
        revelation_id=clue.revelation_id,
    )


def remove_encounter(
    adventure: Adventure,
    encounter_id: str,
    *,
    cascade: bool = False,
) -> Adventure:
    """Remove an encounter, refusing dependent authored records unless cascade is explicit."""
    dependencies = encounter_dependencies(adventure, encounter_id)
    if dependencies.has_dependencies and not cascade:
        raise AuthoringError(_encounter_removal_refusal(dependencies))
    removed_clues: set[str] = set(dependencies.source_clue_ids) if cascade else set()
    return replace(
        adventure,
        encounters=tuple(
            encounter for encounter in adventure.encounters if encounter.id != encounter_id
        ),
        clues=tuple(clue for clue in adventure.clues if clue.id not in removed_clues),
        revelations=tuple(
            replace(revelation, unlocks_encounter_id=None)
            if cascade and revelation.unlocks_encounter_id == encounter_id
            else revelation
            for revelation in adventure.revelations
        ),
    )


def remove_reference(
    adventure: Adventure,
    reference_id: str,
    *,
    cascade: bool = False,
) -> Adventure:
    """Remove a reference, refusing encounter links unless cascade is explicit."""
    dependencies = reference_dependencies(adventure, reference_id)
    if dependencies.has_dependencies and not cascade:
        raise AuthoringError(_reference_removal_refusal(dependencies))
    encounters = adventure.encounters
    if cascade:
        encounters = tuple(
            replace(
                encounter,
                reference_links=tuple(
                    link for link in encounter.reference_links if link.reference_id != reference_id
                ),
            )
            for encounter in adventure.encounters
        )
    return replace(
        adventure,
        encounters=encounters,
        references=tuple(
            reference for reference in adventure.references if reference.id != reference_id
        ),
    )


def remove_revelation(
    adventure: Adventure,
    revelation_id: str,
    *,
    cascade: bool = False,
) -> Adventure:
    """Remove a revelation, refusing supporting clues unless cascade is explicit."""
    dependencies = revelation_dependencies(adventure, revelation_id)
    if dependencies.has_dependencies and not cascade:
        raise AuthoringError(_revelation_removal_refusal(dependencies))
    removed_clues: set[str] = set(dependencies.supporting_clue_ids) if cascade else set()
    return replace(
        adventure,
        revelations=tuple(
            revelation for revelation in adventure.revelations if revelation.id != revelation_id
        ),
        clues=tuple(clue for clue in adventure.clues if clue.id not in removed_clues),
    )


def remove_clue(adventure: Adventure, clue_id: str) -> Adventure:
    """Remove one clue after requiring that it exists."""
    _require_clue(adventure, clue_id)
    return replace(adventure, clues=tuple(clue for clue in adventure.clues if clue.id != clue_id))


def remap_play_state_identifiers(
    state: PlayState,
    *,
    adventure_id: str | None = None,
    encounter_ids: dict[str, str] | None = None,
    revelation_ids: dict[str, str] | None = None,
    clue_ids: dict[str, str] | None = None,
) -> PlayState:
    """Rewrite authored identifiers in every affected play-journal event."""
    encounter_map = encounter_ids or {}
    revelation_map = revelation_ids or {}
    clue_map = clue_ids or {}
    return replace(
        state,
        adventure_id=adventure_id if adventure_id is not None else state.adventure_id,
        events=tuple(
            _remap_event(event, encounter_map, revelation_map, clue_map) for event in state.events
        ),
    )


# Exhaustive event-algebra dispatch is clearer as one auditable function.
def _remap_event(
    event: PlayEvent,
    encounter_ids: dict[str, str],
    revelation_ids: dict[str, str],
    clue_ids: dict[str, str],
) -> PlayEvent:
    if isinstance(event, EncounterVisitedEvent):
        return replace(
            event,
            encounter_id=encounter_ids.get(event.encounter_id, event.encounter_id),
        )
    if isinstance(event, ClueSpottedEvent):
        return replace(event, clue_id=clue_ids.get(event.clue_id, event.clue_id))
    if isinstance(event, ClueMissedEvent):
        return replace(event, clue_id=clue_ids.get(event.clue_id, event.clue_id))
    if isinstance(event, RevelationEstablishedEvent):
        return replace(
            event,
            revelation_id=revelation_ids.get(event.revelation_id, event.revelation_id),
            supporting_clue_ids=tuple(
                clue_ids.get(clue_id, clue_id) for clue_id in event.supporting_clue_ids
            ),
        )
    if isinstance(event, EncounterUnlockedEvent):
        source_revelation_id = event.source_revelation_id
        if source_revelation_id is not None:
            source_revelation_id = revelation_ids.get(source_revelation_id, source_revelation_id)
        return replace(
            event,
            encounter_id=encounter_ids.get(event.encounter_id, event.encounter_id),
            source_revelation_id=source_revelation_id,
        )
    if isinstance(event, (RevelationForeclosedEvent, RevelationReopenedEvent)):
        return replace(
            event,
            revelation_id=revelation_ids.get(event.revelation_id, event.revelation_id),
        )
    if isinstance(event, EncounterConsequenceRecordedEvent):
        return replace(
            event,
            encounter_id=encounter_ids.get(event.encounter_id, event.encounter_id),
        )
    if isinstance(
        event,
        (
            SessionStartedEvent,
            SessionEndedEvent,
            DiceRollRecordedEvent,
            VisitNoteRecordedEvent,
            ReferenceNoteRecordedEvent,
            PlayOperationVoidedEvent,
        ),
    ):
        return event
    assert_never(event)


def _require_encounter(adventure: Adventure, encounter_id: str) -> Encounter:
    encounter = adventure.encounter_index().get(encounter_id)
    if encounter is None:
        raise AuthoringError(f"Unknown encounter {encounter_id!r}.")
    return encounter


def _require_reference(adventure: Adventure, reference_id: str) -> Reference:
    reference = adventure.reference_index().get(reference_id)
    if reference is None:
        raise AuthoringError(f"Unknown reference {reference_id!r}.")
    return reference


def _require_revelation(adventure: Adventure, revelation_id: str) -> Revelation:
    revelation = adventure.revelation_index().get(revelation_id)
    if revelation is None:
        raise AuthoringError(f"Unknown revelation {revelation_id!r}.")
    return revelation


def _require_clue(adventure: Adventure, clue_id: str) -> Clue:
    clue = adventure.clue_index().get(clue_id)
    if clue is None:
        raise AuthoringError(f"Unknown lead {clue_id!r}.")
    return clue


def _require_revelation_destination(adventure: Adventure, revelation: Revelation) -> None:
    if (
        revelation.unlocks_encounter_id is not None
        and revelation.unlocks_encounter_id not in adventure.encounter_index()
    ):
        raise AuthoringError(f"Unknown unlocked encounter {revelation.unlocks_encounter_id!r}.")


def _require_clue_endpoints(adventure: Adventure, clue: Clue) -> None:
    if clue.source_encounter_id not in adventure.encounter_index():
        raise AuthoringError(f"Unknown lead source encounter {clue.source_encounter_id!r}.")
    if clue.revelation_id not in adventure.revelation_index():
        raise AuthoringError(f"Unknown lead revelation {clue.revelation_id!r}.")


def _require_new_identifier(
    index: Mapping[str, object],
    kind: str,
    old_id: str,
    new_id: str,
) -> None:
    if not new_id:
        raise AuthoringError(f"{kind} identifier cannot be empty.")
    if old_id == new_id:
        raise AuthoringError(f"{kind} {old_id!r} already has that identifier.")
    if new_id in index:
        raise AuthoringError(f"{kind} {new_id!r} already exists.")


def _encounter_removal_refusal(dependencies: EncounterDependencies) -> str:
    details: list[str] = []
    if dependencies.source_clue_ids:
        details.append(
            "source leads: " + ", ".join(repr(item) for item in dependencies.source_clue_ids)
        )
    if dependencies.unlocking_revelation_ids:
        details.append(
            "unlocking revelations: "
            + ", ".join(repr(item) for item in dependencies.unlocking_revelation_ids)
        )
    if dependencies.linked_reference_ids:
        details.append(
            "reference links: "
            + ", ".join(repr(item) for item in dependencies.linked_reference_ids)
        )
    return (
        f"Cannot remove encounter {dependencies.encounter_id!r}; authored dependencies exist "
        f"({'; '.join(details)}). Retry with cascade=True to remove its source leads, clear "
        "revelations that unlock it, and discard its subordinate reference links."
    )


def _reference_removal_refusal(dependencies: ReferenceDependencies) -> str:
    encounters = ", ".join(repr(link.encounter_id) for link in dependencies.links)
    return (
        f"Cannot remove reference {dependencies.reference_id!r}; encounter links exist in: "
        f"{encounters}. Retry with cascade=True to unlink those encounters and remove the "
        "reference record."
    )


def _revelation_removal_refusal(dependencies: RevelationDependencies) -> str:
    clues = ", ".join(repr(item) for item in dependencies.supporting_clue_ids)
    return (
        f"Cannot remove revelation {dependencies.revelation_id!r}; supporting leads exist: "
        f"{clues}. Retry with cascade=True to remove those leads as well."
    )
