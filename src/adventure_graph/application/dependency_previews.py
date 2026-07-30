"""Transport-neutral dependency previews for authored structural operations."""

from __future__ import annotations

from dataclasses import dataclass

from adventure_graph.application.authoring import (
    clue_dependencies,
    encounter_dependencies,
    reference_dependencies,
    revelation_dependencies,
)
from adventure_graph.application.project import AuthoringSnapshot
from adventure_graph.domain.adventure import Reference
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    ReferenceNoteRecordedEvent,
    RevelationEstablishedEvent,
    RevelationForeclosedEvent,
    RevelationReopenedEvent,
)


@dataclass(frozen=True, slots=True)
class DependencyPreview:
    """Authored references and effects relevant to move and removal."""

    authored_references: tuple[str, ...]
    move_context: tuple[str, ...]
    removal_dependencies: tuple[str, ...]
    cascade_effects: tuple[str, ...]
    journal_references: tuple[str, ...]


def preview_encounter_dependencies(
    snapshot: AuthoringSnapshot,
    encounter_id: str,
) -> DependencyPreview:
    """Describe authored and journal references to one encounter."""
    dependencies = encounter_dependencies(snapshot.adventure, encounter_id)
    clue_index = snapshot.adventure.clue_index()
    revelation_index = snapshot.adventure.revelation_index()
    encounter = snapshot.adventure.encounter_index()[encounter_id]
    reference_index = snapshot.adventure.reference_index()
    reference_links = tuple(
        _encounter_reference_description(reference_index, link.reference_id, link.context)
        for link in encounter.reference_links
    )
    authored_references = (
        *(f"Lead: {clue_index[item].title}" for item in dependencies.source_clue_ids),
        *(
            f"Revelation: {revelation_index[item].title}"
            for item in dependencies.unlocking_revelation_ids
        ),
        *(f"Reference link: {description}" for description in reference_links),
    )
    cascade = (
        *(f"Remove lead: {clue_index[item].title}" for item in dependencies.source_clue_ids),
        *(
            f"Clear destination on revelation: {revelation_index[item].title}"
            for item in dependencies.unlocking_revelation_ids
        ),
        *(f"Discard reference link: {description}" for description in reference_links),
    )
    return DependencyPreview(
        authored_references=authored_references,
        move_context=(),
        removal_dependencies=authored_references,
        cascade_effects=cascade,
        journal_references=_journal_references(snapshot, "encounter", encounter_id),
    )


def preview_reference_dependencies(
    snapshot: AuthoringSnapshot,
    reference_id: str,
) -> DependencyPreview:
    """Describe encounter backlinks and removal effects for one reference."""
    dependencies = reference_dependencies(snapshot.adventure, reference_id)
    encounter_index = snapshot.adventure.encounter_index()
    references = tuple(
        _reference_backlink_description(
            encounter_index[link.encounter_id].title,
            link.encounter_id,
            link.context,
        )
        for link in dependencies.links
    )
    return DependencyPreview(
        authored_references=references,
        move_context=(),
        removal_dependencies=references,
        cascade_effects=tuple(f"Unlink from encounter: {item}" for item in references),
        journal_references=_journal_references(snapshot, "reference", reference_id),
    )


def preview_revelation_dependencies(
    snapshot: AuthoringSnapshot,
    revelation_id: str,
) -> DependencyPreview:
    """Describe authored and journal references to one revelation."""
    dependencies = revelation_dependencies(snapshot.adventure, revelation_id)
    clue_index = snapshot.adventure.clue_index()
    references = tuple(
        f"Lead: {clue_index[item].title}" for item in dependencies.supporting_clue_ids
    )
    return DependencyPreview(
        authored_references=references,
        move_context=(),
        removal_dependencies=references,
        cascade_effects=tuple(
            f"Remove lead: {clue_index[item].title}" for item in dependencies.supporting_clue_ids
        ),
        journal_references=_journal_references(snapshot, "revelation", revelation_id),
    )


def preview_clue_dependencies(snapshot: AuthoringSnapshot, clue_id: str) -> DependencyPreview:
    """Describe authored endpoints and journal references to one clue."""
    dependencies = clue_dependencies(snapshot.adventure, clue_id)
    encounter = snapshot.adventure.encounter_index()[dependencies.source_encounter_id]
    revelation = snapshot.adventure.revelation_index()[dependencies.revelation_id]
    return DependencyPreview(
        authored_references=(),
        move_context=(
            f"Source encounter: {encounter.title}",
            f"Revelation: {revelation.title}",
        ),
        removal_dependencies=(),
        cascade_effects=(),
        journal_references=_journal_references(snapshot, "clue", clue_id),
    )


def _encounter_reference_description(
    reference_index: dict[str, Reference],
    reference_id: str,
    context: str,
) -> str:
    reference = reference_index.get(reference_id)
    title = reference.title if reference is not None else reference_id
    base = f"{title} ({reference_id})"
    return f"{base} — {context}" if context else base


def _reference_backlink_description(
    encounter_title: str,
    encounter_id: str,
    context: str,
) -> str:
    base = f"{encounter_title} ({encounter_id})"
    return f"{base} — {context}" if context else base


def _journal_references(
    snapshot: AuthoringSnapshot,
    kind: str,
    identifier: str,
) -> tuple[str, ...]:
    references: list[str] = []
    for related in snapshot.related_play_states:
        sequences = tuple(
            event.sequence
            for event in related.state.events
            if _event_references(event, kind, identifier)
        )
        if sequences:
            joined = ", ".join(str(sequence) for sequence in sequences)
            references.append(f"{related.source} (event sequences {joined})")
    return tuple(references)


def _event_references(event: object, kind: str, identifier: str) -> bool:
    if kind == "encounter":
        return (
            isinstance(
                event,
                (
                    EncounterVisitedEvent,
                    EncounterUnlockedEvent,
                    EncounterConsequenceRecordedEvent,
                ),
            )
            and event.encounter_id == identifier
        )
    if kind == "reference":
        return isinstance(event, ReferenceNoteRecordedEvent) and event.reference_id == identifier
    if kind == "revelation":
        return (
            isinstance(
                event,
                (
                    RevelationEstablishedEvent,
                    RevelationForeclosedEvent,
                    RevelationReopenedEvent,
                ),
            )
            and event.revelation_id == identifier
        ) or (
            isinstance(event, EncounterUnlockedEvent) and event.source_revelation_id == identifier
        )
    return (
        isinstance(event, (ClueSpottedEvent, ClueMissedEvent)) and event.clue_id == identifier
    ) or (isinstance(event, RevelationEstablishedEvent) and identifier in event.supporting_clue_ids)
