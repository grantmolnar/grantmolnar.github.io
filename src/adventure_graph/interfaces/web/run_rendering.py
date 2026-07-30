"""HTML rendering for the live run workspace."""

from __future__ import annotations

from adventure_graph.application.run_workspace import (
    RunClueStatus,
    RunDashboardResult,
    RunEncounterOption,
    RunRevelationStatus,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.interfaces.web.journal_rendering import render_journal_operation
from adventure_graph.interfaces.web.markdown import render_safe_markdown
from adventure_graph.interfaces.web.page_rendering import (
    escape_html,
    render_badges,
    render_empty_card,
    render_metrics,
    render_notice,
)
from adventure_graph.interfaces.web.play_rendering import render_play_workspace_page
from adventure_graph.interfaces.web.view_models import PageNotice, RunFormValues


def render_run(
    result: RunDashboardResult,
    project_label: str,
    *,
    csrf_token: str,
    notice: PageNotice | None = None,
    values: RunFormValues | None = None,
) -> str:
    """Render the live session workspace from a transport-neutral dashboard."""
    del project_label
    submitted = values or RunFormValues()
    projection = result.projection
    current_title = (
        result.current_encounter.title if result.current_encounter is not None else "No visit yet"
    )
    established_count = sum(item.is_established for item in result.revelation_statuses)
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row">
        <div><p class="eyebrow">Recovery console</p><h1>{escape_html(current_title)}</h1></div>
        <div class="button-row"><a class="button primary" href="/play">Return to Play</a><a class="button secondary" href="/journal">Correct history</a></div>
      </div>
      <p class="lede">Use this console when an interrupted or unusual recording workflow cannot be completed in ordinary Play.</p>
      {render_metrics(((str(len(projection.visits)), "Visits"), (str(len(projection.spotted_clue_ids)), "Leads found"), (str(established_count), "Revelations established"), (str(len(result.available_encounters)), "Available encounters")))}
      {_run_current_encounter(result, csrf_token)}
      {_run_visit_options(result, csrf_token, submitted)}
      {_run_revelations(result, csrf_token, submitted)}
      {_run_notes_and_consequences(result, csrf_token, submitted)}
      {_run_unlocks(result, csrf_token, submitted)}
      {_run_recent_history(result, csrf_token, submitted)}
    """
    return render_play_workspace_page(
        result,
        csrf_token=csrf_token,
        title=f"Run — {result.adventure.title}",
        current_kind="run",
        body=body,
        body_class="run-body",
    )


def _run_current_encounter(result: RunDashboardResult, csrf_token: str) -> str:
    current_encounter = result.current_encounter
    current_visit = result.current_visit
    if current_encounter is None or current_visit is None:
        return """
        <section class="section run-empty-state">
          <div class="section-heading"><h2>Begin play</h2><span>No active visit</span></div>
          <p class="empty-copy">Choose an available start encounter below to record the first visit.</p>
        </section>
        """
    clue_cards = "".join(
        _run_current_clue(item, current_visit.visit_number, result.revision.value, csrf_token)
        for item in result.current_clues
    ) or render_empty_card("No authored leads are located at this encounter.")
    notes = "".join(f"<li>{escape_html(note)}</li>" for note in current_visit.notes)
    legacy_notes = "".join(
        f"<li>{escape_html(item.text)}</li>" for item in result.current_consequences
    )
    records = ""
    if notes or legacy_notes:
        records = f"""
        <div class="run-record-grid">
          <article><h3>Encounter notes</h3>{f"<ul>{notes}</ul>" if notes else '<p class="empty-copy">No notes yet.</p>'}</article>
          <article><h3>Earlier persistent notes</h3>{f"<ul>{legacy_notes}</ul>" if legacy_notes else '<p class="empty-copy">No legacy records.</p>'}</article>
        </div>
        """
    return f"""
      <section class="section current-visit">
        <div class="section-heading"><h2>Current visit</h2><span>Visit {current_visit.visit_number}</span></div>
        <p class="lede compact-lede">{escape_html(current_encounter.summary)}</p>
        <div class="prose run-prose">{render_safe_markdown(current_encounter.content)}</div>
        <div class="run-subsection"><h3>Discoverable leads</h3><div class="run-clue-grid">{clue_cards}</div></div>
        {records}
      </section>
    """


def _run_current_clue(
    status: RunClueStatus,
    visit_number: int,
    revision: str,
    csrf_token: str,
) -> str:
    clue = status.clue
    description = clue.description or "No expanded description."
    if status.spotted:
        action = (
            f'<span class="coverage-status ok">Found on visit {status.spotted_visit_number}</span>'
        )
        classes = "run-clue found"
    else:
        action = f"""
        <form method="post" action="/run/clue" class="inline-action-form">
          {_run_hidden_fields(csrf_token, revision)}
          <input type="hidden" name="clue_id" value="{escape_html(clue.id)}">
          <input type="hidden" name="visit_number" value="{visit_number}">
          <button class="button small primary" type="submit">Mark discovered</button>
        </form>
        """
        classes = "run-clue"
    return f"""
      <article class="{classes}">
        <span class="card-kicker">{escape_html(clue.discovery)}</span>
        <h4>{escape_html(clue.title)}</h4>
        <p>{escape_html(description)}</p>
        <div class="card-meta">Supports {escape_html(status.revelation.title)}</div>
        {action}
      </article>
    """


def _run_visit_options(
    result: RunDashboardResult,
    csrf_token: str,
    values: RunFormValues,
) -> str:
    ordered = sorted(
        result.available_encounters,
        key=lambda item: (
            not item.authored_from_current,
            item.current,
            item.encounter.title.casefold(),
        ),
    )
    cards = "".join(_run_visit_option(item, result, csrf_token, values) for item in ordered)
    return f"""
      <section class="section">
        <div class="section-heading"><h2>Start another visit</h2><span>Available encounters only</span></div>
        <div class="run-action-list">{cards or render_empty_card("No encounter is currently available.")}</div>
      </section>
    """


def _run_visit_option(
    option: RunEncounterOption,
    result: RunDashboardResult,
    csrf_token: str,
    values: RunFormValues,
) -> str:
    encounter = option.encounter
    selected = values.visit_encounter_id == encounter.id
    clue_ids: set[str] = set(values.visit_clue_ids) if selected else set()
    clues = "".join(
        f'<label><input type="checkbox" name="clue_id" value="{escape_html(clue.id)}" {"checked" if clue.id in clue_ids else ""}><span><strong>{escape_html(clue.title)}</strong><small>{escape_html(clue.discovery)}</small></span></label>'
        for clue in option.unspotted_clues
    )
    clue_field = (
        f'<fieldset class="check-list"><legend>Leads found immediately</legend>{clues}</fieldset>'
        if clues
        else '<p class="muted-note">No unresolved leads remain at this encounter.</p>'
    )
    labels: list[str] = []
    if option.authored_from_current:
        labels.append("Authored next step")
    if option.current:
        labels.append("Current encounter")
    if option.visit_count:
        labels.append(f"Visited {option.visit_count} times")
    note = values.visit_note if selected else ""
    button = "Start another visit" if option.visit_count else "Start visit"
    return f"""
      <details class="run-action-card" {"open" if selected or option.authored_from_current else ""}>
        <summary><span><strong>{escape_html(encounter.title)}</strong><small>{escape_html(encounter.summary)}</small></span>{render_badges(labels)}</summary>
        <form method="post" action="/run/visit" class="compact-form">
          {_run_hidden_fields(csrf_token, result.revision.value)}
          <input type="hidden" name="encounter_id" value="{escape_html(encounter.id)}">
          {clue_field}
          <label for="visit-note-{escape_html(encounter.id)}">Initial encounter note</label>
          <textarea id="visit-note-{escape_html(encounter.id)}" name="note" rows="3">{escape_html(note)}</textarea>
          <div class="form-actions"><button class="button primary" type="submit">{button}</button></div>
        </form>
      </details>
    """


def _run_revelations(
    result: RunDashboardResult,
    csrf_token: str,
    values: RunFormValues,
) -> str:
    pending = tuple(item for item in result.revelation_statuses if not item.is_established)
    established = tuple(item for item in result.revelation_statuses if item.is_established)
    pending_cards = "".join(
        _run_revelation_form(item, result.revision.value, csrf_token, values) for item in pending
    ) or render_empty_card("Every authored revelation has been established.")
    established_cards = "".join(
        _run_established_revelation(item, result.adventure) for item in established
    )
    established_block = (
        f'<div class="run-established-list">{established_cards}</div>'
        if established_cards
        else '<p class="empty-copy">No revelation has been established yet.</p>'
    )
    return f"""
      <section class="section">
        <div class="section-heading"><h2>Revelation progress</h2><span>{len(established)} established · {len(pending)} pending</span></div>
        <div class="run-action-list">{pending_cards}</div>
        <div class="run-subsection"><h3>Established conclusions</h3>{established_block}</div>
      </section>
    """


def _run_revelation_form(
    status: RunRevelationStatus,
    revision: str,
    csrf_token: str,
    values: RunFormValues,
) -> str:
    selected = values.revelation_id == status.revelation.id
    selected_ids = (
        set(values.supporting_clue_ids) if selected else {clue.id for clue in status.spotted_clues}
    )
    spotted = "".join(
        f'<label><input type="checkbox" name="supporting_clue_id" value="{escape_html(clue.id)}" {"checked" if clue.id in selected_ids else ""}><span><strong>{escape_html(clue.title)}</strong><small>{escape_html(clue.discovery)}</small></span></label>'
        for clue in status.spotted_clues
    )
    basis = (
        f'<fieldset class="check-list"><legend>Supporting leads</legend>{spotted}</fieldset>'
        if spotted
        else '<p class="muted-note">No supporting lead has been found. Establishment is still permitted as explicit GM adjudication.</p>'
    )
    destination = (
        f"Unlocks {status.destination_encounter.title}"
        if status.destination_encounter is not None
        else "Conclusion only"
    )
    note = values.revelation_note if selected else ""
    return f"""
      <details class="run-action-card" {"open" if selected or status.spotted_clues else ""}>
        <summary><span><strong>{escape_html(status.revelation.title)}</strong><small>{escape_html(status.revelation.description)}</small></span><span class="badge">{escape_html(destination)}</span></summary>
        <form method="post" action="/run/revelation" class="compact-form">
          {_run_hidden_fields(csrf_token, revision)}
          <input type="hidden" name="revelation_id" value="{escape_html(status.revelation.id)}">
          {basis}
          <label for="revelation-note-{escape_html(status.revelation.id)}">Establishment note</label>
          <textarea id="revelation-note-{escape_html(status.revelation.id)}" name="note" rows="3">{escape_html(note)}</textarea>
          <div class="form-actions"><button class="button primary" type="submit">Establish revelation</button></div>
        </form>
      </details>
    """


def _run_established_revelation(status: RunRevelationStatus, adventure: Adventure) -> str:
    clue_index = adventure.clue_index()
    basis = (
        ", ".join(
            clue_index[item].title for item in status.establishment_clue_ids if item in clue_index
        )
        or "GM adjudication"
    )
    note = f" · {status.establishment_note}" if status.establishment_note else ""
    return f"""
      <article class="run-established">
        <span class="coverage-status ok">Established</span>
        <h4>{escape_html(status.revelation.title)}</h4>
        <p>Basis: {escape_html(basis)}{escape_html(note)}</p>
      </article>
    """


def _run_notes_and_consequences(
    result: RunDashboardResult,
    csrf_token: str,
    values: RunFormValues,
) -> str:
    current_visit = result.current_visit
    if current_visit is None:
        return ""
    note_text = values.note_text if values.note_visit_number == current_visit.visit_number else ""
    return f"""
      <section class="section">
        <div class="section-heading"><h2>Record table developments</h2><span>One flexible note stream</span></div>
        <form method="post" action="/run/note" class="compact-form run-panel">
          {_run_hidden_fields(csrf_token, result.revision.value)}
          <input type="hidden" name="visit_number" value="{current_visit.visit_number}">
          <h3>Add an encounter note</h3>
          <label for="run-note">Record anything the GM wants to remember about visit {current_visit.visit_number}.</label>
          <textarea id="run-note" name="text" rows="7" required>{escape_html(note_text)}</textarea>
          <div class="form-actions"><button class="button primary" type="submit">Record note</button></div>
        </form>
      </section>
    """


def _run_unlocks(
    result: RunDashboardResult,
    csrf_token: str,
    values: RunFormValues,
) -> str:
    if not result.locked_encounters:
        return ""
    options = "".join(
        f'<option value="{escape_html(encounter.id)}" {"selected" if values.unlock_encounter_id == encounter.id else ""}>{escape_html(encounter.title)}</option>'
        for encounter in result.locked_encounters
    )
    return f"""
      <section class="section">
        <div class="section-heading"><h2>GM override</h2><span>Explicit manual unlock</span></div>
        <form method="post" action="/run/unlock" class="compact-form run-panel">
          {_run_hidden_fields(csrf_token, result.revision.value)}
          <label for="unlock-encounter">Locked encounter</label>
          <select id="unlock-encounter" name="encounter_id" required><option value="">Choose an encounter</option>{options}</select>
          <label for="unlock-reason">Why is it available now?</label>
          <textarea id="unlock-reason" name="reason" rows="3" required>{escape_html(values.unlock_reason)}</textarea>
          <div class="form-actions"><button class="button secondary" type="submit">Unlock encounter</button></div>
        </form>
      </section>
    """


def _run_recent_history(
    result: RunDashboardResult,
    csrf_token: str,
    values: RunFormValues,
) -> str:
    operations = "".join(
        render_journal_operation(operation, result.adventure)
        for operation in reversed(result.recent_operations)
    ) or render_empty_card("No play operations have been recorded.")
    latest = result.latest_active_operation_number
    correction = (
        f"""
        <form class="compact-form run-panel" method="post" action="/run/correct">
          {_run_hidden_fields(csrf_token, result.revision.value)}
          <label for="run-correction">Why is operation {latest} being corrected?</label>
          <textarea id="run-correction" name="reason" rows="3" required>{escape_html(values.correction_reason)}</textarea>
          <div class="form-actions"><button class="button danger" type="submit">Correct operation {latest}</button></div>
        </form>
        """
        if latest is not None
        else '<p class="empty-copy">No active operation remains to correct.</p>'
    )
    return f"""
      <section class="section">
        <div class="section-heading"><h2>Recent operations</h2><span>Showing {len(result.recent_operations)} of {result.total_operation_count}</span></div>
        <div class="journal-history">{operations}</div>
        <div class="run-subsection"><h3>Correct the latest active operation</h3>{correction}</div>
      </section>
    """


def _run_hidden_fields(csrf_token: str, revision: str) -> str:
    return f"""
      <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}">
      <input type="hidden" name="expected_revision" value="{escape_html(revision)}">
    """
