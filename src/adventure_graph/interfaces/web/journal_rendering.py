"""HTML rendering for append-only journal history."""

from __future__ import annotations

from typing import assert_never

from adventure_graph.application.play_journal import (
    JournalEventRecord,
    JournalOperationRecord,
    PlayJournalStatusResult,
)
from adventure_graph.application.run_workspace import RunDashboardResult
from adventure_graph.domain.adventure import Adventure
from adventure_graph.interfaces.web.page_rendering import (
    escape_html,
    render_empty_card,
    render_metrics,
    render_notice,
)
from adventure_graph.interfaces.web.play_rendering import render_play_workspace_page
from adventure_graph.interfaces.web.view_models import PageNotice


def render_journal(
    result: PlayJournalStatusResult,
    project_label: str,
    *,
    csrf_token: str,
    dashboard: RunDashboardResult,
    notice: PageNotice | None = None,
    correction_reason: str = "",
) -> str:
    """Render append-only journal history and the narrow correction form."""
    del project_label
    latest = result.latest_active_operation_number
    correction_form = (
        f"""
        <form class="editor-form compact-form" method="post" action="/journal/correct">
          <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}">
          <input type="hidden" name="expected_revision" value="{escape_html(result.revision.value)}">
          <label for="correction-reason">Why is operation {latest} being corrected?</label>
          <textarea id="correction-reason" name="reason" rows="3" required>{escape_html(correction_reason)}</textarea>
          <div class="form-actions"><button class="button danger" type="submit">Correct operation {latest}</button></div>
        </form>
        """
        if latest is not None
        else '<p class="empty-copy">No active operation remains to correct.</p>'
    )
    operations = (
        "".join(
            render_journal_operation(operation, result.adventure)
            for operation in reversed(result.operations)
        )
        if result.operations
        else render_empty_card("No play operations have been recorded.")
    )
    body = f"""
      <div class="page-heading-row">
        <div><p class="eyebrow">Audit trail</p><h1>Correct history</h1></div>
        <div class="button-row"><a class="button primary" href="/play/ledgers?kind=narrative&amp;scope=playthrough">Read chronological history</a></div>
      </div>
      <p class="lede">Review and correct recorded actions here. For a readable account of what happened, open History.</p>
      {render_notice(notice)}
      {render_metrics(((str(result.event_count), "Recorded events"), (str(result.active_event_count), "Active records"), (str(len(result.operations)), "Recorded actions"), (str(result.correction_count), "Corrections")))}
      <section class="section">
        <div class="section-heading"><h2>Correct latest operation</h2><span>Latest active action only</span></div>
        {correction_form}
      </section>
      <section class="section">
        <div class="section-heading"><h2>Operation history</h2><span>Newest first</span></div>
        <div class="journal-history">{operations}</div>
      </section>
    """
    return render_play_workspace_page(
        dashboard,
        csrf_token=csrf_token,
        title=f"Play history — {result.adventure.title}",
        current_kind="journal",
        body=body,
        body_class="journal-body",
    )


def render_journal_operation(operation: JournalOperationRecord, adventure: Adventure) -> str:
    if operation.is_correction:
        status = "Correction"
        status_class = "correction"
    elif operation.active:
        status = "Active"
        status_class = "active"
    else:
        status = "Voided"
        status_class = "voided"
    event_count = len(operation.events)
    event_label = "event" if event_count == 1 else "events"
    events = "".join(
        f'<li><span class="event-sequence">Event {event.sequence}</span>{escape_html(_journal_event_text(event, adventure))}</li>'
        for event in operation.events
    )
    return (
        f'<article class="journal-operation {status_class}"><header><div>'
        f'<span class="card-kicker">Operation {operation.operation_number}</span>'
        f'<h3>{status}</h3></div><span class="badge">{event_count} {event_label}</span>'
        f"</header><ol>{events}</ol></article>"
    )


# Keep journal presentation exhaustive over its transport-neutral read model.
def _journal_event_text(event: JournalEventRecord, adventure: Adventure) -> str:
    encounter_index = adventure.encounter_index()
    clue_index = adventure.clue_index()
    revelation_index = adventure.revelation_index()
    reference_index = adventure.reference_index()
    kind = event.kind
    if kind == "session_started":
        title = f": {event.title}" if event.title else ""
        played_on = f" on {event.played_on}" if event.played_on else ""
        participants = (
            f" Participants: {', '.join(event.participants)}." if event.participants else ""
        )
        attendance = f" Attendance: {event.attendance_note}" if event.attendance_note else ""
        note = f" Opening note: {event.text}" if event.text else ""
        text = (
            f"Started session {event.session_number}{title}{played_on}."
            f"{participants}{attendance}{note}"
        )
    elif kind == "session_ended":
        note = f" Closing note: {event.text}" if event.text else ""
        text = f"Ended session {event.session_number}.{note}"
    elif kind == "encounter_visited":
        encounter = encounter_index.get(event.encounter_id)
        title = "an unavailable encounter" if encounter is None else encounter.title
        party = f" ({event.party_label})" if event.party_label else ""
        text = f"Visit {event.visit_number}: entered {title}{party}."
    elif kind == "clue_spotted":
        clue = clue_index.get(event.clue_id)
        title = "an unavailable lead" if clue is None else clue.title
        text = f"Spotted {title} during visit {event.visit_number}."
    elif kind == "clue_missed":
        clue = clue_index.get(event.clue_id)
        title = "an unavailable lead" if clue is None else clue.title
        text = f"Missed {title} during visit {event.visit_number}."
    elif kind == "revelation_established":
        revelation = revelation_index.get(event.revelation_id)
        title = "an unavailable revelation" if revelation is None else revelation.title
        basis = (
            ", ".join(
                clue_index[item].title for item in event.supporting_clue_ids if item in clue_index
            )
            or "GM adjudication"
        )
        note = f" Note: {event.text}" if event.text else ""
        text = f"Established {title}; basis: {basis}.{note}"
    elif kind == "revelation_foreclosed":
        revelation = revelation_index.get(event.revelation_id)
        title = "an unavailable revelation" if revelation is None else revelation.title
        text = f"Foreclosed {title}: {event.text}"
    elif kind == "revelation_reopened":
        revelation = revelation_index.get(event.revelation_id)
        title = "an unavailable revelation" if revelation is None else revelation.title
        text = f"Reopened {title}: {event.text}"
    elif kind == "dice_roll_recorded":
        label = f"{event.title}: " if event.title else ""
        text = f"Recorded roll {label}{event.text}."
    elif kind == "encounter_unlocked":
        encounter = encounter_index.get(event.encounter_id)
        title = "an unavailable encounter" if encounter is None else encounter.title
        source_revelation = revelation_index.get(event.source_revelation_id or "")
        source = (
            f" from revelation {source_revelation.title}"
            if source_revelation is not None
            else f": {event.text}"
        )
        text = f"Made {title} available{source}."
    elif kind == "visit_note_recorded":
        text = f"Visit {event.visit_number} note: {event.text}"
    elif kind == "reference_note_recorded":
        reference = reference_index.get(event.reference_id)
        title = "an unavailable reference" if reference is None else reference.title
        text = f"Note on {title}: {event.text}"
    elif kind == "encounter_consequence_recorded":
        encounter = encounter_index.get(event.encounter_id)
        title = "an unavailable encounter" if encounter is None else encounter.title
        text = f"Consequence at {title}: {event.text}"
    elif kind == "operation_voided":
        text = f"Voided operation {event.target_operation_number}: {event.text}"
    else:
        assert_never(kind)
    return text
