"""Markdown document generation from authored and played adventure state."""

from __future__ import annotations

from collections import defaultdict
from typing import assert_never

from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
    Reference,
    Revelation,
)
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    DiceGroupResult,
    DiceModifierResult,
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
from adventure_graph.domain.play_state import (
    PlayProjection,
    PlayState,
    RevelationProgress,
)
from adventure_graph.domain.validation_models import (
    GraphConnectivityDiagnosis,
    GraphRepairSuggestion,
    ValidationReport,
)


def render_adventure_documents(
    adventure: Adventure,
    report: ValidationReport,
    state: PlayState | None = None,
) -> dict[str, str]:
    """Generate the core source-oriented, destination-oriented, and runtime documents."""
    documents = {
        "00-overview.md": _overview(adventure, report),
        "01-encounter-index.md": _encounter_index(adventure),
        "02-clue-list.md": _clue_list(adventure),
        "03-revelation-list.md": _revelation_list(adventure),
        "04-validation-report.md": _validation_report(report),
    }
    for encounter in adventure.encounters:
        documents[f"encounters/{encounter.id}.md"] = _encounter_document(adventure, encounter.id)
    if adventure.references:
        documents["references/index.md"] = _reference_index(adventure)
        for reference in adventure.references:
            documents[f"references/{reference.id}.md"] = _reference_document(
                adventure,
                reference,
            )
    if state is not None:
        documents["05-play-summary.md"] = render_play_summary(adventure, state)
    return documents


def render_play_summary(adventure: Adventure, state: PlayState) -> str:
    """Generate an event chronology and an explicit current-state dashboard."""
    projection = project_play_state(adventure, state)
    lines = [
        f"# Play Summary: {adventure.title}",
        "",
        f"Events recorded: {len(state.events)}  ",
        f"Active events: {len(state.active_events)}  ",
        f"Corrections recorded: {len(projection.corrections)}  ",
    ]
    if projection.sessions:
        lines.extend(
            [
                f"Explicit sessions: {len(projection.sessions)}  ",
                f"Active session: {projection.active_session_number or 'none'}  ",
            ]
        )
    lines.extend([f"Visits recorded: {len(projection.visits)}", ""])
    lines.extend(_event_timeline(adventure, state))
    lines.extend(_visit_log(adventure, projection))
    lines.extend(_current_state(adventure, projection))
    lines.extend(
        [
            "",
            f"Unique leads found: {len(projection.spotted_clue_ids)} / {len(adventure.clues)}",
            "",
        ]
    )
    return "\n".join(lines)


def _event_timeline(adventure: Adventure, state: PlayState) -> list[str]:
    lines = ["## Event Timeline", ""]
    if not state.events:
        return [*lines, "- No play events recorded.", ""]
    voided = state.voided_operation_numbers
    for event in state.events:
        lines.extend(_event_lines(adventure, event, event.operation_number in voided))
    return [*lines, ""]


# Keep report rendering exhaustive over the event algebra in one place.
def _event_lines(
    adventure: Adventure,
    event: PlayEvent,
    is_voided: bool,
) -> list[str]:
    encounter_index = adventure.encounter_index()
    clue_index = adventure.clue_index()
    revelation_index = adventure.revelation_index()
    suffix = " *(voided)*" if is_voided else ""
    if isinstance(event, PlayOperationVoidedEvent):
        return [
            (
                f"- **Event {event.sequence}: Operation corrected** — voided operation "
                f"{event.target_operation_number}; reason: {event.reason}"
            )
        ]
    if isinstance(event, SessionStartedEvent):
        details = [f"session {event.session_number}"]
        if event.title:
            details.append(event.title)
        if event.played_on:
            details.append(event.played_on)
        lines = [f"- **Event {event.sequence}: Session started** — {' — '.join(details)}.{suffix}"]
        if event.participants:
            lines.append(f"  Participants: {', '.join(event.participants)}")
        if event.attendance_note:
            lines.append(f"  Attendance: {event.attendance_note}")
        if event.opening_note:
            lines.append(f"  Opening note: {event.opening_note}")
        return lines
    if isinstance(event, SessionEndedEvent):
        lines = [
            f"- **Event {event.sequence}: Session ended** — session {event.session_number}.{suffix}"
        ]
        if event.closing_note:
            lines.append(f"  Closing note: {event.closing_note}")
        return lines
    if isinstance(event, EncounterVisitedEvent):
        party = f"; party: {event.party_label}" if event.party_label else ""
        return [
            (
                f"- **Event {event.sequence}: Visit {event.visit_number}** — entered "
                f"{encounter_index[event.encounter_id].title} "
                f"(`{event.encounter_id}`){party}.{suffix}"
            )
        ]
    if isinstance(event, ClueSpottedEvent):
        clue = clue_index[event.clue_id]
        return [
            (
                f"- **Event {event.sequence}: Lead found** — {clue.title} (`{clue.id}`) "
                f"during visit {event.visit_number}.{suffix}"
            )
        ]
    if isinstance(event, ClueMissedEvent):
        clue = clue_index[event.clue_id]
        return [
            (
                f"- **Event {event.sequence}: Lead missed** — {clue.title} (`{clue.id}`) "
                f"during visit {event.visit_number}.{suffix}"
            )
        ]
    if isinstance(event, RevelationEstablishedEvent):
        revelation = revelation_index[event.revelation_id]
        basis = _establishment_basis(event.supporting_clue_ids, clue_index)
        lines = [
            (
                f"- **Event {event.sequence}: Revelation established** — {revelation.title} "
                f"(`{revelation.id}`); basis: {basis}.{suffix}"
            )
        ]
        if event.note:
            lines.append(f"  Note: {event.note}")
        return lines
    if isinstance(event, RevelationForeclosedEvent):
        revelation = revelation_index[event.revelation_id]
        return [
            (
                f"- **Event {event.sequence}: Revelation foreclosed** — {revelation.title} "
                f"(`{revelation.id}`); reason: {event.reason}.{suffix}"
            )
        ]
    if isinstance(event, RevelationReopenedEvent):
        revelation = revelation_index[event.revelation_id]
        return [
            (
                f"- **Event {event.sequence}: Revelation reopened** — {revelation.title} "
                f"(`{revelation.id}`); reason: {event.reason}.{suffix}"
            )
        ]
    if isinstance(event, DiceRollRecordedEvent):
        label = f" — {event.label}" if event.label else ""
        terms = _recorded_roll_terms(event)
        return [
            (
                f"- **Event {event.sequence}: Dice roll recorded**{label} — "
                f"{event.expression} = {event.total}; results: {terms}.{suffix}"
            )
        ]
    if isinstance(event, EncounterUnlockedEvent):
        encounter = encounter_index[event.encounter_id]
        explanation = _unlock_explanation(event, revelation_index)
        return [
            (
                f"- **Event {event.sequence}: Encounter available** — {encounter.title} "
                f"(`{encounter.id}`), {explanation}.{suffix}"
            )
        ]
    if isinstance(event, VisitNoteRecordedEvent):
        return [
            f"- **Event {event.sequence}: Visit {event.visit_number} note** — {event.text}{suffix}"
        ]
    if isinstance(event, ReferenceNoteRecordedEvent):
        reference = adventure.reference_index()[event.reference_id]
        return [
            (
                f"- **Event {event.sequence}: Reference note** — "
                f"{reference.title} (`{reference.id}`): {event.text}{suffix}"
            )
        ]
    if isinstance(event, EncounterConsequenceRecordedEvent):
        return [
            (
                f"- **Event {event.sequence}: Encounter consequence** — "
                f"{encounter_index[event.encounter_id].title}: {event.text}{suffix}"
            )
        ]
    assert_never(event)


def _recorded_roll_terms(event: DiceRollRecordedEvent) -> str:
    rendered: list[str] = []
    for term in event.terms:
        if isinstance(term, DiceGroupResult):
            sign = "-" if term.sign < 0 else "+"
            values = ", ".join(str(result) for result in term.results)
            rendered.append(f"{sign}d{term.faces} [{values}]")
        elif isinstance(term, DiceModifierResult):
            rendered.append(f"{term.value:+d}")
        else:
            assert_never(term)
    return " ".join(rendered).lstrip("+")


def _unlock_explanation(
    event: EncounterUnlockedEvent,
    revelation_index: dict[str, Revelation],
) -> str:
    if event.source_revelation_id is None:
        return event.reason or "by explicit adjudication"
    source = revelation_index[event.source_revelation_id]
    return f"from {source.title} (`{source.id}`)"


def _visit_log(adventure: Adventure, projection: PlayProjection) -> list[str]:
    lines = ["## Visit Log", ""]
    if not projection.visits:
        return [*lines, "No visits recorded.", ""]
    encounter_index = adventure.encounter_index()
    clue_index = adventure.clue_index()
    revelation_index = adventure.revelation_index()
    progress_index = projection.revelation_progress_index()
    for visit in projection.visits:
        party = f" — {visit.party_label}" if visit.party_label else ""
        heading = f"### {visit.visit_number}. {encounter_index[visit.encounter_id].title}{party}"
        lines.extend([heading, ""])
        if visit.spotted_clue_ids:
            lines.append("Leads found:")
            lines.extend(
                _visit_clue_line(clue_id, clue_index, revelation_index, progress_index)
                for clue_id in visit.spotted_clue_ids
            )
        else:
            lines.append("Leads found: none recorded.")
        if visit.missed_clue_ids:
            lines.extend(["", "Leads missed during this visit:"])
            lines.extend(f"- **{clue_index[clue_id].title}**" for clue_id in visit.missed_clue_ids)
        if visit.notes:
            lines.extend(["", "Notes:"])
            lines.extend(f"- {note}" for note in visit.notes)
        lines.append("")
    return lines


def _visit_clue_line(
    clue_id: str,
    clue_index: dict[str, Clue],
    revelation_index: dict[str, Revelation],
    progress_index: dict[str, RevelationProgress],
) -> str:
    clue = clue_index[clue_id]
    progress = progress_index[clue.revelation_id]
    status = "established" if progress.is_established else "not yet established"
    return f"- **{clue.title}** → {revelation_index[clue.revelation_id].title} ({status})"


def _current_state(adventure: Adventure, projection: PlayProjection) -> list[str]:
    progress_index = projection.revelation_progress_index()
    visited_encounter_ids = {visit.encounter_id for visit in projection.visits}
    lines = ["## Current State", ""]
    lines.extend(_spotted_clues_section(adventure, projection))
    lines.extend(_supported_revelations_section(adventure, projection))
    if any(progress.is_foreclosed for progress in projection.revelation_progress):
        lines.extend(_foreclosed_revelations_section(adventure, projection))
    lines.extend(_established_revelations_section(adventure, projection))
    lines.extend(_available_encounters_section(adventure, projection, visited_encounter_ids))
    lines.extend(_locked_encounters_section(adventure, projection))
    lines.extend(_outstanding_revelations_section(adventure, progress_index))
    lines.extend(_consequences_section(adventure, projection))
    return lines


def _spotted_clues_section(adventure: Adventure, projection: PlayProjection) -> list[str]:
    lines = ["### Found Leads", ""]
    if not projection.spotted_clue_ids:
        return [*lines, "- None.", ""]
    clue_index = adventure.clue_index()
    revelation_index = adventure.revelation_index()
    lines.extend(
        f"- **{clue_index[clue_id].title}** (`{clue_id}`) — supports "
        f"{revelation_index[clue_index[clue_id].revelation_id].title}."
        for clue_id in projection.spotted_clue_ids
    )
    return [*lines, ""]


def _supported_revelations_section(adventure: Adventure, projection: PlayProjection) -> list[str]:
    lines = ["### Supported but Unconfirmed Revelations", ""]
    supported = [
        progress
        for progress in projection.revelation_progress
        if progress.is_supported and not progress.is_established and not progress.is_foreclosed
    ]
    if not supported:
        return [*lines, "- None.", ""]
    revelation_index = adventure.revelation_index()
    lines.extend(
        f"- **{revelation_index[progress.revelation_id].title}** "
        f"(`{progress.revelation_id}`) — {len(progress.spotted_clue_ids)} "
        "found supporting lead(s)."
        for progress in supported
    )
    return [*lines, ""]


def _foreclosed_revelations_section(
    adventure: Adventure,
    projection: PlayProjection,
) -> list[str]:
    lines = ["### Foreclosed Revelations", ""]
    foreclosed = [progress for progress in projection.revelation_progress if progress.is_foreclosed]
    if not foreclosed:
        return [*lines, "- None.", ""]
    revelation_index = adventure.revelation_index()
    for progress in foreclosed:
        revelation = revelation_index[progress.revelation_id]
        support = f"{len(progress.spotted_clue_ids)} found supporting lead(s)"
        lines.append(
            f"- **{revelation.title}** (`{revelation.id}`) — {support}; "
            f"reason: {progress.foreclosure_reason}."
        )
    return [*lines, ""]


def _established_revelations_section(adventure: Adventure, projection: PlayProjection) -> list[str]:
    lines = ["### Established Revelations", ""]
    established = [
        progress for progress in projection.revelation_progress if progress.is_established
    ]
    if not established:
        return [*lines, "- None.", ""]
    clue_index = adventure.clue_index()
    revelation_index = adventure.revelation_index()
    for progress in sorted(established, key=lambda item: item.established_sequence or 0):
        revelation = revelation_index[progress.revelation_id]
        basis = _establishment_basis(progress.establishment_clue_ids, clue_index)
        lines.append(
            f"- **{revelation.title}** (`{revelation.id}`) — event "
            f"{progress.established_sequence}; basis: {basis}."
        )
        if progress.establishment_note:
            lines.append(f"  Note: {progress.establishment_note}")
    return [*lines, ""]


def _available_encounters_section(
    adventure: Adventure,
    projection: PlayProjection,
    visited_encounter_ids: set[str],
) -> list[str]:
    lines = ["### Available Encounters", ""]
    if not projection.available_encounter_ids:
        return [*lines, "- None.", ""]
    encounter_index = adventure.encounter_index()
    for encounter_id in projection.available_encounter_ids:
        encounter = encounter_index[encounter_id]
        status = "visited" if encounter_id in visited_encounter_ids else "unvisited"
        entry = "; start encounter" if encounter.start else ""
        lines.append(f"- **{encounter.title}** (`{encounter.id}`) — {status}{entry}.")
    return [*lines, ""]


def _locked_encounters_section(adventure: Adventure, projection: PlayProjection) -> list[str]:
    lines = ["### Locked Encounters", ""]
    locked_encounters = [
        encounter
        for encounter in adventure.encounters
        if encounter.id not in projection.available_encounter_ids
    ]
    if not locked_encounters:
        return [*lines, "- None.", ""]
    lines.extend(f"- **{encounter.title}** (`{encounter.id}`)" for encounter in locked_encounters)
    return [*lines, ""]


def _outstanding_revelations_section(
    adventure: Adventure,
    progress_index: dict[str, RevelationProgress],
) -> list[str]:
    lines = ["### Outstanding Necessary Revelations", ""]
    outstanding = [
        revelation
        for revelation in adventure.revelations
        if revelation.required and not progress_index[revelation.id].is_established
    ]
    if not outstanding:
        return [*lines, "- None.", ""]
    lines.extend(f"- **{revelation.title}** (`{revelation.id}`)" for revelation in outstanding)
    return [*lines, ""]


def _consequences_section(adventure: Adventure, projection: PlayProjection) -> list[str]:
    lines = ["### Encounter Consequences", ""]
    if not projection.consequences:
        return [*lines, "- None.", ""]
    encounter_index = adventure.encounter_index()
    lines.extend(
        f"- Event {consequence.sequence}, **{encounter_index[consequence.encounter_id].title}**: "
        f"{consequence.text}"
        for consequence in projection.consequences
    )
    return [*lines, ""]


def _establishment_basis(clue_ids: tuple[str, ...], clue_index: dict[str, Clue]) -> str:
    if not clue_ids:
        return "no lead basis recorded"
    return ", ".join(f"{clue_index[clue_id].title} (`{clue_id}`)" for clue_id in clue_ids)


def _overview(adventure: Adventure, report: ValidationReport) -> str:
    status = "PASS" if report.is_valid else "FAIL"
    connectivity = "n/a" if report.edge_connectivity is None else str(report.edge_connectivity)
    return "\n".join(
        [
            f"# {adventure.title}",
            "",
            f"**Adventure ID:** `{adventure.id}`  ",
            f"**Validation:** {status}  ",
            f"**Necessary-encounter edge connectivity:** {connectivity}",
            *_tag_metadata_lines(adventure),
            "",
            "## Synopsis",
            "",
            adventure.synopsis,
            "",
            "## Premise",
            "",
            adventure.premise,
            "",
            "## Explanation",
            "",
            adventure.explanation,
            "",
        ]
    )


def _tag_metadata_lines(adventure: Adventure) -> list[str]:
    tags = adventure.tags
    lines: list[str] = []
    if tags.genres:
        lines.append(f"**Genres:** {', '.join(tags.genres)}  ")
    if tags.game_systems:
        lines.append(f"**Game systems:** {', '.join(tags.game_systems)}  ")
    if tags.settings:
        lines.append(f"**Settings:** {', '.join(tags.settings)}  ")
    if tags.party_size_min is not None or tags.party_size_max is not None:
        group_size = _metadata_range(tags.party_size_min, tags.party_size_max)
        lines.append(f"**Recommended group size:** {group_size}  ")
    if tags.level_min is not None or tags.level_max is not None:
        lines.append(f"**Recommended level:** {_metadata_range(tags.level_min, tags.level_max)}  ")
    if tags.combat_intensity:
        lines.append(f"**Combat intensity:** {tags.combat_intensity.title()}  ")
    if tags.keywords:
        lines.append(f"**Other tags:** {', '.join(tags.keywords)}  ")
    return lines


def _metadata_range(minimum: int | None, maximum: int | None) -> str:
    if minimum is not None and maximum is not None:
        return str(minimum) if minimum == maximum else f"{minimum}-{maximum}"
    if minimum is not None:
        return f"{minimum}+"
    return f"up to {maximum}"


def _encounter_index(adventure: Adventure) -> str:
    lines = [f"# Encounter Index: {adventure.title}", ""]
    for encounter in adventure.encounters:
        roles = ["necessary" if encounter.required else "optional"]
        roles.extend(
            role
            for role, enabled in (("start", encounter.start), ("end", encounter.end))
            if enabled
        )
        role_text = ", ".join(roles)
        lines.extend(
            [
                f"## {encounter.title} (`{encounter.id}`)",
                "",
                f"**Role:** {role_text}",
                "",
                encounter.summary,
                "",
            ]
        )
    return "\n".join(lines)


def _clue_list(adventure: Adventure) -> str:
    revelation_index = adventure.revelation_index()
    clues_by_source: defaultdict[str, list[Clue]] = defaultdict(list)
    for clue in adventure.clues:
        clues_by_source[clue.source_encounter_id].append(clue)

    lines = [
        f"# Lead List: {adventure.title}",
        "",
        "Organized by source encounter (outgoing view).",
        "",
    ]
    for encounter in adventure.encounters:
        lines.extend([f"## {encounter.title} (`{encounter.id}`)", ""])
        clues = sorted(clues_by_source[encounter.id], key=lambda clue: clue.id)
        if not clues:
            lines.extend(["- No leads.", ""])
            continue
        for clue in clues:
            revelation = revelation_index[clue.revelation_id]
            target = (
                f"; unlocks `{revelation.unlocks_encounter_id}`"
                if revelation.unlocks_encounter_id is not None
                else ""
            )
            lines.append(
                f"- **{clue.title}** (`{clue.id}`) → {revelation.title} "
                f"(`{revelation.id}`){target}. Discovery: {clue.discovery}"
            )
            if clue.description:
                lines.append(f"  {clue.description}")
        lines.append("")
    return "\n".join(lines)


def _revelation_list(adventure: Adventure) -> str:
    encounter_index = adventure.encounter_index()
    clues_by_revelation: defaultdict[str, list[Clue]] = defaultdict(list)
    for clue in adventure.clues:
        clues_by_revelation[clue.revelation_id].append(clue)

    lines = [
        f"# Revelation List: {adventure.title}",
        "",
        "Organized by destination conclusion (incoming view).",
        "",
    ]
    for revelation in adventure.revelations:
        required = "necessary" if revelation.required else "optional"
        lines.extend([f"## {revelation.title} (`{revelation.id}`)", "", f"**Status:** {required}"])
        if revelation.unlocks_encounter_id is not None:
            lines.append(f"**Unlocks encounter:** `{revelation.unlocks_encounter_id}`")
        lines.extend(["", revelation.description, "", "Supporting leads:"])
        clues = sorted(clues_by_revelation[revelation.id], key=lambda clue: clue.id)
        if clues:
            for clue in clues:
                source_title = encounter_index[clue.source_encounter_id].title
                lines.append(
                    f"- **{clue.title}** (`{clue.id}`) — {source_title} "
                    f"(`{clue.source_encounter_id}`)"
                )
        else:
            lines.append("- None.")
        lines.append("")
    return "\n".join(lines)


def _encounter_document(adventure: Adventure, encounter_id: str) -> str:
    encounter = adventure.encounter_index()[encounter_id]
    revelation_index = adventure.revelation_index()
    clue_sections: list[str] = []
    for clue in adventure.clues:
        if clue.source_encounter_id != encounter_id:
            continue
        revelation = revelation_index[clue.revelation_id]
        destination = (
            f"; unlocks `{revelation.unlocks_encounter_id}`"
            if revelation.unlocks_encounter_id is not None
            else ""
        )
        clue_sections.extend(
            [
                f"### {clue.title} (`{clue.id}`)",
                "",
                f"**Supports:** {revelation.title} (`{revelation.id}`){destination}  ",
                f"**Discovery:** {clue.discovery}",
                "",
                clue.description or "No lead description supplied.",
                "",
            ]
        )
    if not clue_sections:
        clue_sections.extend(["No leads.", ""])
    roles = ["necessary" if encounter.required else "optional"]
    roles.extend(
        role for role, enabled in (("start", encounter.start), ("end", encounter.end)) if enabled
    )
    role_text = ", ".join(roles)
    tag_text = ", ".join(encounter.tags) or "none"
    reference_section = _encounter_reference_document_section(adventure, encounter_id)
    return "\n".join(
        [
            f"# {encounter.title}",
            "",
            f"**Role:** {role_text}  ",
            f"**Tags:** {tag_text}",
            "",
            encounter.summary,
            "",
            "## Opening View",
            "",
            encounter.opening_view or "No opening view supplied.",
            "",
            "## Encounter Material",
            "",
            encounter.content or "No encounter material supplied.",
            "",
            *reference_section,
            "## Leads Here",
            "",
            *clue_sections,
        ]
    )


def _reference_index(adventure: Adventure) -> str:
    lines = [f"# Reference Index: {adventure.title}", ""]
    headings = (
        ("person", "People"),
        ("place", "Places"),
        ("organization", "Organizations"),
        ("object", "Objects"),
        ("other", "Other"),
    )
    for kind, heading in headings:
        references = tuple(item for item in adventure.references if item.kind == kind)
        if not references:
            continue
        lines.extend([f"## {heading}", ""])
        for reference in references:
            aliases = f" Aliases: {', '.join(reference.aliases)}." if reference.aliases else ""
            summary = reference.summary or "No summary supplied."
            lines.append(f"- [**{reference.title}**]({reference.id}.md) — {summary}{aliases}")
        lines.append("")
    return "\n".join(lines)


def _reference_document(adventure: Adventure, reference: Reference) -> str:
    aliases = ", ".join(reference.aliases) or "none"
    tags = ", ".join(reference.tags) or "none"
    backlinks: list[str] = []
    for encounter in adventure.encounters:
        link = next(
            (item for item in encounter.reference_links if item.reference_id == reference.id),
            None,
        )
        if link is None:
            continue
        backlinks.append(
            f"- [**{encounter.title}**](../encounters/{encounter.id}.md)"
            + (f" — {link.context}" if link.context else "")
        )
    if not backlinks:
        backlinks.append("- No encounter backlinks.")
    return "\n".join(
        [
            f"# {reference.title}",
            "",
            f"**Reference ID:** `{reference.id}`  ",
            f"**Kind:** {reference.kind.title()}  ",
            f"**Aliases:** {aliases}  ",
            f"**Tags:** {tags}",
            "",
            "## Summary",
            "",
            reference.summary or "No summary supplied.",
            "",
            "## Reference Material",
            "",
            reference.content or "No detailed reference material supplied.",
            "",
            "## Encounter Backlinks",
            "",
            *backlinks,
            "",
        ]
    )


def _encounter_reference_document_section(
    adventure: Adventure,
    encounter_id: str,
) -> list[str]:
    encounter = adventure.encounter_index()[encounter_id]
    if not encounter.reference_links:
        return []
    reference_index = adventure.reference_index()
    lines = ["## Linked References", ""]
    for link in encounter.reference_links:
        reference = reference_index[link.reference_id]
        lines.append(
            f"- [**{reference.title}**](../references/{reference.id}.md)"
            + (f" — {link.context}" if link.context else "")
        )
    return [*lines, ""]


def _validation_report(report: ValidationReport) -> str:
    """Render validation findings and the exact graph-cut witness."""
    lines = ["# Validation Report", "", f"Result: {'PASS' if report.is_valid else 'FAIL'}", ""]
    connectivity = "n/a" if report.edge_connectivity is None else str(report.edge_connectivity)
    lines.extend([f"Computed necessary-encounter edge connectivity: {connectivity}", ""])
    if report.connectivity_diagnosis is not None:
        lines.extend(_connectivity_diagnosis_lines(report.connectivity_diagnosis))
    if not report.issues:
        lines.extend(["## Findings", "", "No issues found.", ""])
        return "\n".join(lines)
    lines.extend(["## Findings", ""])
    for issue in report.issues:
        subject = f" (`{issue.subject_id}`)" if issue.subject_id else ""
        lines.append(f"- **{issue.severity.upper()} {issue.code}**{subject}: {issue.message}")
        if issue.repair:
            lines.append(f"  **Repair:** {issue.repair}")
    lines.append("")
    return "\n".join(lines)


def _connectivity_diagnosis_lines(diagnosis: GraphConnectivityDiagnosis) -> list[str]:
    lines = [
        "## Minimum-Cut Witness",
        "",
        f"**Configured minimum connectivity:** {diagnosis.required_edge_connectivity}  ",
        f"**Partition A:** {_encounter_id_list(diagnosis.side_a)}  ",
        f"**Partition B:** {_encounter_id_list(diagnosis.side_b)}  ",
        f"**Cut edges:** {_cut_edge_list(diagnosis.cut_edges)}",
        "",
    ]
    if diagnosis.additional_connections_needed <= 0:
        return lines
    lines.extend(
        [
            "## Structural Repair Candidates",
            "",
            (
                f"This witnessed cut needs at least {diagnosis.additional_connections_needed} "
                "additional distinct encounter-to-encounter connection(s). Revalidate after "
                "editing because another cut may then become limiting."
            ),
            "",
        ]
    )
    if not diagnosis.repair_suggestions:
        lines.extend(
            [
                (
                    "- No unused cross-partition encounter pair remains. Add encounters or lower "
                    "the policy threshold."
                ),
                "",
            ]
        )
        return lines
    lines.extend(_repair_suggestion_line(item) for item in diagnosis.repair_suggestions)
    lines.append("")
    return lines


def _repair_suggestion_line(suggestion: GraphRepairSuggestion) -> str:
    if suggestion.revelation_id is None:
        return (
            f"- Add a lead at `{suggestion.source_encounter_id}` that supports a new revelation "
            f"unlocking `{suggestion.target_encounter_id}`."
        )
    return (
        f"- Add a lead at `{suggestion.source_encounter_id}` supporting "
        f"`{suggestion.revelation_id}` to connect it to `{suggestion.target_encounter_id}`."
    )


def _encounter_id_list(encounter_ids: tuple[str, ...]) -> str:
    return ", ".join(f"`{encounter_id}`" for encounter_id in encounter_ids)


def _cut_edge_list(edges: tuple[tuple[str, str], ...]) -> str:
    if not edges:
        return "none (the graph is already disconnected)"
    return ", ".join(f"`{source}`—`{target}`" for source, target in edges)
