"""Operational play ledgers and spoiler-safe recap projections."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias, assert_never

from adventure_graph.application.play_journal import PlayJournalProject, PlayJournalSnapshot
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.application.project import ProjectRevision
from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
    Encounter,
    Revelation,
)
from adventure_graph.domain.play_events import PlayContentEventKind
from adventure_graph.domain.play_state import (
    NarrativeRecord,
    PlayProjection,
    SessionRecord,
)
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import ValidationReport

PlayLedgerScope: TypeAlias = Literal["playthrough", "session"]
PlayLedgerKind: TypeAlias = Literal["encounters", "clues", "revelations", "narrative", "recap"]
ClueLedgerStatus: TypeAlias = Literal["found", "missed", "unresolved"]
RevelationLedgerStatus: TypeAlias = Literal["established", "foreclosed", "supported", "unsupported"]
EncounterLedgerStatus: TypeAlias = Literal["current", "visited", "available", "locked"]


@dataclass(frozen=True, slots=True)
class ClueLedgerEntry:
    """One authored clue enriched with scoped activity and current status."""

    clue: Clue
    source_encounter: Encounter
    revelation: Revelation
    status: ClueLedgerStatus
    spotted_visit_number: int | None
    missed_visit_numbers: tuple[int, ...]
    spotted_in_scope: bool
    missed_visit_numbers_in_scope: tuple[int, ...]
    source_visited_in_scope: bool


@dataclass(frozen=True, slots=True)
class RevelationLedgerEntry:
    """One authored revelation enriched with support and scoped activity."""

    revelation: Revelation
    destination_encounter: Encounter | None
    supporting_clues: tuple[Clue, ...]
    spotted_clues: tuple[Clue, ...]
    spotted_clues_in_scope: tuple[Clue, ...]
    status: RevelationLedgerStatus
    establishment_note: str
    foreclosure_reason: str
    changed_in_scope: bool


@dataclass(frozen=True, slots=True)
class EncounterLedgerEntry:
    """One authored encounter enriched with reachability and scoped history."""

    encounter: Encounter
    status: EncounterLedgerStatus
    visit_numbers: tuple[int, ...]
    visit_numbers_in_scope: tuple[int, ...]
    consequence_texts_in_scope: tuple[str, ...]
    unresolved_clue_count: int


@dataclass(frozen=True, slots=True)
class NarrativeLedgerEntry:
    """One human-readable, session-aware active-history item."""

    sequence: int
    operation_number: int
    session_number: int | None
    kind: PlayContentEventKind
    title: str
    detail: str
    visit_number: int | None = None
    encounter_id: str = ""
    clue_id: str = ""
    revelation_id: str = ""
    reference_id: str = ""


@dataclass(frozen=True, slots=True)
class PlayLedgerDocument:
    """One derived Markdown document available for download."""

    kind: PlayLedgerKind
    name: str
    title: str
    content: str


@dataclass(frozen=True, slots=True)
class PlayLedgersResult:
    """All operational ledgers derived from one journal revision and scope."""

    adventure: Adventure
    validation_report: ValidationReport
    revision: ProjectRevision
    requested_scope: PlayLedgerScope
    selected_session: SessionRecord | None
    available_session_count: int
    clues: tuple[ClueLedgerEntry, ...]
    revelations: tuple[RevelationLedgerEntry, ...]
    encounters: tuple[EncounterLedgerEntry, ...]
    narrative: tuple[NarrativeLedgerEntry, ...]
    player_recap: tuple[NarrativeLedgerEntry, ...]
    documents: tuple[PlayLedgerDocument, ...]

    @property
    def is_session_scope(self) -> bool:
        """Return whether an explicit session is selected for this result."""
        return self.requested_scope == "session" and self.selected_session is not None

    @property
    def scope_label(self) -> str:
        """Return a concise user-facing scope label."""
        if self.requested_scope == "session" and self.selected_session is None:
            return "No explicit session"
        if not self.is_session_scope:
            return "Whole playthrough"
        selected_session = self.selected_session
        if selected_session is None:
            raise ValueError("Session scope requires a selected session.")
        return selected_session.title or f"Session {selected_session.session_number}"

    def document_index(self) -> dict[PlayLedgerKind, PlayLedgerDocument]:
        """Return derived documents keyed by ledger kind."""
        return {document.kind: document for document in self.documents}


class GetPlayLedgers:
    """Load one journal and derive all operational ledgers without side effects."""

    def __init__(self, project: PlayJournalProject) -> None:
        self._project = project

    def execute(self, scope: PlayLedgerScope = "playthrough") -> PlayLedgersResult:
        """Return whole-playthrough or latest-session operational ledgers."""
        return build_play_ledgers(self._project.load(), scope)


def build_play_ledgers(
    snapshot: PlayJournalSnapshot,
    scope: PlayLedgerScope = "playthrough",
) -> PlayLedgersResult:
    """Build operational ledgers from an already loaded journal snapshot."""
    if scope not in {"playthrough", "session"}:
        raise ValueError(f"Unknown play-ledger scope {scope!r}.")
    projection = project_play_state(snapshot.adventure, snapshot.state)
    selected_session = (
        projection.sessions[-1] if scope == "session" and projection.sessions else None
    )
    scoped_visit_numbers = _scoped_visit_numbers(projection, scope, selected_session)
    scoped_narrative = _scoped_narrative(projection, scope, selected_session)
    clues = _clue_entries(snapshot.adventure, projection, scoped_visit_numbers, scope)
    revelations = _revelation_entries(
        snapshot.adventure,
        projection,
        scoped_visit_numbers,
        scoped_narrative,
        scope,
    )
    encounters = _encounter_entries(
        snapshot.adventure,
        projection,
        scoped_visit_numbers,
        scoped_narrative,
        scope,
    )
    narrative = tuple(
        _narrative_entry(snapshot.adventure, projection, record) for record in scoped_narrative
    )
    player_recap = tuple(
        _player_recap_entry(snapshot.adventure, projection, record)
        for record in scoped_narrative
        if _is_player_safe(record)
    )
    documents = _render_documents(
        snapshot.adventure,
        scope,
        selected_session,
        clues,
        revelations,
        encounters,
        narrative,
        player_recap,
    )
    return PlayLedgersResult(
        adventure=snapshot.adventure,
        validation_report=validate_adventure(snapshot.adventure),
        revision=snapshot.revision,
        requested_scope=scope,
        selected_session=selected_session,
        available_session_count=len(projection.sessions),
        clues=clues,
        revelations=revelations,
        encounters=encounters,
        narrative=narrative,
        player_recap=player_recap,
        documents=documents,
    )


def _scoped_visit_numbers(
    projection: PlayProjection,
    scope: PlayLedgerScope,
    selected_session: SessionRecord | None,
) -> frozenset[int]:
    if scope == "playthrough":
        return frozenset(visit.visit_number for visit in projection.visits)
    if selected_session is None:
        return frozenset()
    return frozenset(selected_session.visit_numbers)


def _scoped_narrative(
    projection: PlayProjection,
    scope: PlayLedgerScope,
    selected_session: SessionRecord | None,
) -> tuple[NarrativeRecord, ...]:
    if scope == "playthrough":
        return projection.narrative
    if selected_session is None:
        return ()
    return tuple(
        record
        for record in projection.narrative
        if record.session_number == selected_session.session_number
    )


def _clue_entries(
    adventure: Adventure,
    projection: PlayProjection,
    scoped_visit_numbers: frozenset[int],
    scope: PlayLedgerScope,
) -> tuple[ClueLedgerEntry, ...]:
    encounter_index = adventure.encounter_index()
    revelation_index = adventure.revelation_index()
    progress_index = projection.clue_progress_index()
    visit_index = {visit.visit_number: visit for visit in projection.visits}
    entries: list[ClueLedgerEntry] = []
    for clue in adventure.clues:
        progress = progress_index[clue.id]
        source_visited_in_scope = any(
            visit_index[number].encounter_id == clue.source_encounter_id
            for number in scoped_visit_numbers
        )
        missed_in_scope = tuple(
            number for number in progress.missed_visit_numbers if number in scoped_visit_numbers
        )
        spotted_in_scope = progress.spotted_visit_number in scoped_visit_numbers
        if scope == "session" and not (
            source_visited_in_scope or missed_in_scope or spotted_in_scope
        ):
            continue
        status: ClueLedgerStatus
        if progress.is_spotted:
            status = "found"
        elif progress.missed_visit_numbers:
            status = "missed"
        else:
            status = "unresolved"
        entries.append(
            ClueLedgerEntry(
                clue=clue,
                source_encounter=encounter_index[clue.source_encounter_id],
                revelation=revelation_index[clue.revelation_id],
                status=status,
                spotted_visit_number=progress.spotted_visit_number,
                missed_visit_numbers=progress.missed_visit_numbers,
                spotted_in_scope=spotted_in_scope,
                missed_visit_numbers_in_scope=missed_in_scope,
                source_visited_in_scope=source_visited_in_scope,
            )
        )
    return tuple(entries)


def _revelation_entries(
    adventure: Adventure,
    projection: PlayProjection,
    scoped_visit_numbers: frozenset[int],
    scoped_narrative: tuple[NarrativeRecord, ...],
    scope: PlayLedgerScope,
) -> tuple[RevelationLedgerEntry, ...]:
    encounter_index = adventure.encounter_index()
    clue_index = adventure.clue_index()
    clue_progress = projection.clue_progress_index()
    progress_index = projection.revelation_progress_index()
    changed_ids = {
        record.revelation_id
        for record in scoped_narrative
        if record.revelation_id
        and record.kind
        in {"revelation_established", "revelation_foreclosed", "revelation_reopened"}
    }
    entries: list[RevelationLedgerEntry] = []
    for revelation in adventure.revelations:
        supporting = tuple(clue for clue in adventure.clues if clue.revelation_id == revelation.id)
        spotted = tuple(
            clue_index[clue_id] for clue_id in progress_index[revelation.id].spotted_clue_ids
        )
        spotted_in_scope = tuple(
            clue
            for clue in spotted
            if clue_progress[clue.id].spotted_visit_number in scoped_visit_numbers
        )
        source_visited_in_scope = any(
            visit.visit_number in scoped_visit_numbers
            and any(clue.source_encounter_id == visit.encounter_id for clue in supporting)
            for visit in projection.visits
        )
        changed_in_scope = revelation.id in changed_ids
        if scope == "session" and not (
            source_visited_in_scope or spotted_in_scope or changed_in_scope
        ):
            continue
        progress = progress_index[revelation.id]
        status: RevelationLedgerStatus
        if progress.is_established:
            status = "established"
        elif progress.is_foreclosed:
            status = "foreclosed"
        elif progress.is_supported:
            status = "supported"
        else:
            status = "unsupported"
        entries.append(
            RevelationLedgerEntry(
                revelation=revelation,
                destination_encounter=(
                    None
                    if revelation.unlocks_encounter_id is None
                    else encounter_index[revelation.unlocks_encounter_id]
                ),
                supporting_clues=supporting,
                spotted_clues=spotted,
                spotted_clues_in_scope=spotted_in_scope,
                status=status,
                establishment_note=progress.establishment_note,
                foreclosure_reason=progress.foreclosure_reason,
                changed_in_scope=changed_in_scope,
            )
        )
    return tuple(entries)


def _encounter_entries(
    adventure: Adventure,
    projection: PlayProjection,
    scoped_visit_numbers: frozenset[int],
    scoped_narrative: tuple[NarrativeRecord, ...],
    scope: PlayLedgerScope,
) -> tuple[EncounterLedgerEntry, ...]:
    progress_index = projection.encounter_progress_index()
    clue_progress = projection.clue_progress_index()
    current_encounter_id = projection.visits[-1].encounter_id if projection.visits else None
    consequence_by_encounter: dict[str, list[str]] = {}
    for record in scoped_narrative:
        if record.kind == "encounter_consequence_recorded" and record.encounter_id:
            consequence_by_encounter.setdefault(record.encounter_id, []).append(record.text)
    entries: list[EncounterLedgerEntry] = []
    for encounter in adventure.encounters:
        progress = progress_index[encounter.id]
        scoped_visits = tuple(
            number for number in progress.visit_numbers if number in scoped_visit_numbers
        )
        if scope == "session" and not (scoped_visits or progress.available):
            continue
        if encounter.id == current_encounter_id:
            status: EncounterLedgerStatus = "current"
        elif progress.visit_numbers:
            status = "visited"
        elif progress.available:
            status = "available"
        else:
            status = "locked"
        unresolved_count = sum(
            1
            for clue in adventure.clues
            if clue.source_encounter_id == encounter.id and not clue_progress[clue.id].is_spotted
        )
        entries.append(
            EncounterLedgerEntry(
                encounter=encounter,
                status=status,
                visit_numbers=progress.visit_numbers,
                visit_numbers_in_scope=scoped_visits,
                consequence_texts_in_scope=tuple(consequence_by_encounter.get(encounter.id, [])),
                unresolved_clue_count=unresolved_count,
            )
        )
    return tuple(entries)


def _narrative_entry(
    adventure: Adventure,
    projection: PlayProjection,
    record: NarrativeRecord,
) -> NarrativeLedgerEntry:
    encounter_index = adventure.encounter_index()
    clue_index = adventure.clue_index()
    revelation_index = adventure.revelation_index()
    reference_index = adventure.reference_index()
    session_index = {session.session_number: session for session in projection.sessions}
    kind = record.kind
    title = kind.replace("_", " ").title()
    detail = record.text
    if kind == "session_started":
        session = (
            session_index[record.session_number] if record.session_number is not None else None
        )
        title = "Session begun"
        if session is not None:
            parts = [session.title or f"Session {session.session_number}"]
            if session.played_on:
                parts.append(session.played_on)
            if session.participants:
                parts.append(", ".join(session.participants))
            detail = " · ".join(parts)
            if session.opening_note:
                detail += f" — {session.opening_note}"
    elif kind == "session_ended":
        title = "Session ended"
    elif kind == "encounter_visited":
        encounter = encounter_index[record.encounter_id]
        title = f"Visit {record.visit_number}: {encounter.title}"
    elif kind == "clue_spotted":
        clue = clue_index[record.clue_id]
        title = f"Lead found: {clue.title}"
        detail = clue.description
    elif kind == "clue_missed":
        clue = clue_index[record.clue_id]
        title = f"Lead missed: {clue.title}"
        encounter_title = encounter_index[clue.source_encounter_id].title
        detail = f"Visit {record.visit_number} at {encounter_title}."
    elif kind == "revelation_established":
        revelation = revelation_index[record.revelation_id]
        title = f"Revelation established: {revelation.title}"
        detail = record.text or revelation.description
    elif kind == "revelation_foreclosed":
        revelation = revelation_index[record.revelation_id]
        title = f"Revelation foreclosed: {revelation.title}"
    elif kind == "revelation_reopened":
        revelation = revelation_index[record.revelation_id]
        title = f"Revelation reopened: {revelation.title}"
    elif kind == "dice_roll_recorded":
        title = "Recorded dice roll"
    elif kind == "encounter_unlocked":
        title = f"Encounter unlocked: {encounter_index[record.encounter_id].title}"
    elif kind == "visit_note_recorded":
        title = f"Visit {record.visit_number} note"
    elif kind == "reference_note_recorded":
        title = f"Note on {reference_index[record.reference_id].title}"
    elif kind == "encounter_consequence_recorded":
        title = f"Consequence at {encounter_index[record.encounter_id].title}"
    else:
        assert_never(kind)
    return NarrativeLedgerEntry(
        sequence=record.sequence,
        operation_number=record.operation_number,
        session_number=record.session_number,
        kind=kind,
        title=title,
        detail=detail,
        visit_number=record.visit_number,
        encounter_id=record.encounter_id,
        clue_id=record.clue_id,
        revelation_id=record.revelation_id,
        reference_id=record.reference_id,
    )


def _is_player_safe(record: NarrativeRecord) -> bool:
    return record.kind in {
        "session_started",
        "session_ended",
        "encounter_visited",
        "clue_spotted",
        "revelation_established",
    }


def _player_recap_entry(
    adventure: Adventure,
    projection: PlayProjection,
    record: NarrativeRecord,
) -> NarrativeLedgerEntry:
    entry = _narrative_entry(adventure, projection, record)
    if record.kind == "session_started":
        session = next(
            (item for item in projection.sessions if item.session_number == record.session_number),
            None,
        )
        detail_parts: list[str] = []
        if session is not None and session.played_on:
            detail_parts.append(session.played_on)
        if session is not None and session.participants:
            detail_parts.append(", ".join(session.participants))
        return NarrativeLedgerEntry(
            sequence=entry.sequence,
            operation_number=entry.operation_number,
            session_number=entry.session_number,
            kind=entry.kind,
            title=(
                session.title
                if session is not None and session.title
                else f"Session {record.session_number}"
            ),
            detail=" · ".join(detail_parts),
        )
    if record.kind == "session_ended":
        return NarrativeLedgerEntry(
            sequence=entry.sequence,
            operation_number=entry.operation_number,
            session_number=entry.session_number,
            kind=entry.kind,
            title="Session ended",
            detail="",
        )
    if record.kind == "encounter_visited":
        encounter = adventure.encounter_index()[record.encounter_id]
        return NarrativeLedgerEntry(
            sequence=entry.sequence,
            operation_number=entry.operation_number,
            session_number=entry.session_number,
            kind=entry.kind,
            title=encounter.title,
            detail=record.text,
            visit_number=record.visit_number,
            encounter_id=record.encounter_id,
        )
    if record.kind == "clue_spotted":
        clue = adventure.clue_index()[record.clue_id]
        return NarrativeLedgerEntry(
            sequence=entry.sequence,
            operation_number=entry.operation_number,
            session_number=entry.session_number,
            kind=entry.kind,
            title=clue.title,
            detail=clue.description,
            visit_number=record.visit_number,
            clue_id=record.clue_id,
        )
    if record.kind == "revelation_established":
        revelation = adventure.revelation_index()[record.revelation_id]
        return NarrativeLedgerEntry(
            sequence=entry.sequence,
            operation_number=entry.operation_number,
            session_number=entry.session_number,
            kind=entry.kind,
            title=revelation.title,
            detail=revelation.description,
            revelation_id=record.revelation_id,
        )
    raise ValueError(f"Narrative kind {record.kind!r} is not player-safe.")


def _render_documents(
    adventure: Adventure,
    scope: PlayLedgerScope,
    session: SessionRecord | None,
    clues: tuple[ClueLedgerEntry, ...],
    revelations: tuple[RevelationLedgerEntry, ...],
    encounters: tuple[EncounterLedgerEntry, ...],
    narrative: tuple[NarrativeLedgerEntry, ...],
    player_recap: tuple[NarrativeLedgerEntry, ...],
) -> tuple[PlayLedgerDocument, ...]:
    if scope == "playthrough":
        scope_slug = "playthrough"
        scope_title = "Whole playthrough"
    elif session is None:
        scope_slug = "session-unavailable"
        scope_title = "No explicit session"
    else:
        scope_slug = f"session-{session.session_number:02d}"
        scope_title = session.title or f"Session {session.session_number}"
    items: tuple[tuple[PlayLedgerKind, str, str], ...] = (
        (
            "encounters",
            "Encounter ledger",
            _render_encounter_markdown(adventure, scope_title, encounters),
        ),
        ("clues", "Lead ledger", _render_clue_markdown(adventure, scope_title, clues)),
        (
            "revelations",
            "Revelation ledger",
            _render_revelation_markdown(adventure, scope_title, revelations),
        ),
        (
            "narrative",
            "Narrative ledger",
            _render_narrative_markdown(adventure, scope_title, narrative, player_safe=False),
        ),
        (
            "recap",
            "Player-safe recap",
            _render_narrative_markdown(adventure, scope_title, player_recap, player_safe=True),
        ),
    )
    return tuple(
        PlayLedgerDocument(
            kind=kind,
            name=f"{scope_slug}-{kind}.md",
            title=title,
            content=content,
        )
        for kind, title, content in items
    )


def _document_heading(adventure: Adventure, title: str, scope_title: str) -> list[str]:
    return [f"# {title}: {adventure.title}", "", f"Scope: **{scope_title}**", ""]


def _render_encounter_markdown(
    adventure: Adventure, scope_title: str, entries: tuple[EncounterLedgerEntry, ...]
) -> str:
    lines = _document_heading(adventure, "Encounter Ledger", scope_title)
    if not entries:
        lines.append("No encounters are in this scope.")
    for entry in entries:
        lines.extend(
            [
                f"## {entry.encounter.title}",
                "",
                f"- Status: **{entry.status}**",
                f"- Visits in scope: {', '.join(map(str, entry.visit_numbers_in_scope)) or 'none'}",
                f"- Visits overall: {', '.join(map(str, entry.visit_numbers)) or 'none'}",
                f"- Unresolved leads here: {entry.unresolved_clue_count}",
            ]
        )
        if entry.consequence_texts_in_scope:
            lines.append("- Consequences in scope:")
            lines.extend(f"  - {text}" for text in entry.consequence_texts_in_scope)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_clue_markdown(
    adventure: Adventure, scope_title: str, entries: tuple[ClueLedgerEntry, ...]
) -> str:
    lines = _document_heading(adventure, "Lead Ledger", scope_title)
    if not entries:
        lines.append("No leads are in this scope.")
    for entry in entries:
        lines.extend(
            [
                f"## {entry.clue.title}",
                "",
                f"- Status: **{entry.status}**",
                f"- Source: {entry.source_encounter.title}",
                f"- Supports: {entry.revelation.title}",
                f"- Found on visit: {entry.spotted_visit_number or 'not found'}",
                f"- Missed on visits: {', '.join(map(str, entry.missed_visit_numbers)) or 'none'}",
            ]
        )
        if entry.clue.description:
            lines.extend(["", entry.clue.description])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _render_revelation_markdown(
    adventure: Adventure,
    scope_title: str,
    entries: tuple[RevelationLedgerEntry, ...],
) -> str:
    lines = _document_heading(adventure, "Revelation Ledger", scope_title)
    if not entries:
        lines.append("No revelations are in this scope.")
    for entry in entries:
        lines.extend(
            [
                f"## {entry.revelation.title}",
                "",
                f"- Status: **{entry.status}**",
                f"- Necessary: {'yes' if entry.revelation.required else 'no'}",
                "- Destination: "
                + (entry.destination_encounter.title if entry.destination_encounter else "none"),
                (
                    f"- Found support: {len(entry.spotted_clues)} of "
                    f"{len(entry.supporting_clues)} leads"
                ),
            ]
        )
        if entry.establishment_note:
            lines.append(f"- Establishment note: {entry.establishment_note}")
        if entry.foreclosure_reason:
            lines.append(f"- Foreclosure reason: {entry.foreclosure_reason}")
        lines.extend(["", entry.revelation.description, ""])
    return "\n".join(lines).rstrip() + "\n"


def _render_narrative_markdown(
    adventure: Adventure,
    scope_title: str,
    entries: tuple[NarrativeLedgerEntry, ...],
    *,
    player_safe: bool,
) -> str:
    title = "Player-Safe Recap" if player_safe else "Narrative Ledger"
    lines = _document_heading(adventure, title, scope_title)
    if player_safe:
        lines.extend(
            [
                (
                    "This recap contains only visited locations, discovered leads, and "
                    "established revelations."
                ),
                "",
            ]
        )
    if not entries:
        lines.append("No narrative events are in this scope.")
    for entry in entries:
        lines.append(f"- **{entry.title}**" + (f" — {entry.detail}" if entry.detail else ""))
    return "\n".join(lines).rstrip() + "\n"
