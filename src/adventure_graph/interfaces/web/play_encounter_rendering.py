"""Focused encounter sections for the table-centered Play workspace."""

from __future__ import annotations

from collections.abc import Iterable
from urllib.parse import quote, urlencode

from adventure_graph.application.run_workspace import (
    RunDashboardResult,
    RunRevelationStatus,
)
from adventure_graph.domain.adventure import Clue, Encounter, Revelation
from adventure_graph.domain.play_state import ClueProgress, EncounterConsequenceRecord
from adventure_graph.interfaces.web.markdown import render_safe_markdown
from adventure_graph.interfaces.web.page_rendering import escape_html
from adventure_graph.interfaces.web.play_rendering_support import render_play_hidden_fields
from adventure_graph.interfaces.web.view_models import PlayFormValues


def render_focused_encounter_sections(
    encounter: Encounter,
    result: RunDashboardResult,
    csrf_token: str,
    values: PlayFormValues,
) -> str:
    """Render six ordinary, independently collapsible encounter-workspace sections."""
    clues = tuple(
        clue for clue in result.adventure.clues if clue.source_encounter_id == encounter.id
    )
    consequences = tuple(
        item for item in result.projection.consequences if item.encounter_id == encounter.id
    )
    outgoing = _outgoing_revelations(encounter, result)
    active_here = (
        result.projection.active_session_number is not None
        and result.current_encounter is not None
        and result.current_visit is not None
        and result.current_encounter.id == encounter.id
    )
    current_here = (
        result.current_encounter is not None and result.current_encounter.id == encounter.id
    )
    adventure_id = result.adventure.id

    opening = _encounter_section(
        adventure_id=adventure_id,
        key="opening",
        title="Opening description",
        context="Player-facing · read or paraphrase",
        content=f'<div class="play-prose-measure prose">{render_safe_markdown(encounter.opening_view)}</div>',
        section_id="encounter-opening",
        extra_class="play-opening-section",
    )
    orientation = _encounter_section(
        adventure_id=adventure_id,
        key="orientation",
        title="GM orientation",
        context="Encounter synopsis",
        content=f'<p class="play-encounter-summary play-prose-measure">{escape_html(encounter.summary)}</p>',
        section_id="encounter-orientation",
    )
    material = _encounter_section(
        adventure_id=adventure_id,
        key="material",
        title="Encounter material",
        context="GM reference",
        content=f'<div class="play-prose-measure prose">{render_safe_markdown(encounter.content)}</div>',
        section_id="encounter-material",
        extra_class="play-encounter-material-section",
    )
    references = _encounter_section(
        adventure_id=adventure_id,
        key="references",
        title="Linked references",
        context=_linked_reference_count(encounter, result),
        content=_linked_reference_content(encounter, result),
        section_id="encounter-references",
    )
    clue_content = _clue_content(
        clues,
        outgoing,
        result,
        encounter.id,
        csrf_token,
        values,
        active_here,
    )
    clues_panel = _encounter_section(
        adventure_id=adventure_id,
        key="clues",
        title="Leads at this encounter",
        context=_clue_context(clues, active_here),
        content=clue_content,
        section_id="focused-clues",
        extra_class="play-encounter-clues-section",
    )
    notes = _encounter_section(
        adventure_id=adventure_id,
        key="notes",
        title="Encounter notes",
        context=_notes_context(result, encounter.id),
        content=_visit_notebook_content(
            result,
            encounter.id,
            csrf_token,
            values,
            active_here,
            current_here,
            consequences,
        ),
        section_id="current-visit-notes",
        extra_class="play-encounter-notes-section",
    )
    return f"""
      <article class="play-encounter-reader">
        <div class="play-encounter-section-stack" data-play-encounter-sections>
          {opening}
          {orientation}
          {material}
          {references}
          {clues_panel}
          {notes}
        </div>
      </article>
    """


def _encounter_section(
    *,
    adventure_id: str,
    key: str,
    title: str,
    context: str,
    content: str,
    section_id: str,
    extra_class: str = "",
) -> str:
    classes = " ".join(
        item
        for item in ("play-encounter-section", "ui-disclosure", "is-expanded", extra_class)
        if item
    )
    content_id = f"play-encounter-section-{key}-content"
    toggle_id = f"play-encounter-section-{key}-toggle"
    storage_key = f"adventure-graph:play:{adventure_id}:encounter-section:{key}"
    return f"""
      <section class="{escape_html(classes)}" id="{escape_html(section_id)}"
               data-ui-disclosure data-disclosure-default="expanded"
               data-disclosure-storage-key="{escape_html(storage_key)}">
        <header class="play-encounter-section-header">
          <h2>
            <button type="button" class="play-encounter-section-toggle"
                    id="{escape_html(toggle_id)}"
                    aria-controls="{escape_html(content_id)}" aria-expanded="true"
                    data-ui-disclosure-toggle>
              <span class="play-encounter-section-heading">
                <span class="play-encounter-section-title">{escape_html(title)}</span>
                <span class="play-encounter-section-context">{escape_html(context)}</span>
              </span>
              <span class="ui-disclosure-indicator" aria-hidden="true"></span>
            </button>
          </h2>
        </header>
        <div class="play-encounter-section-scroll" id="{escape_html(content_id)}"
             role="region" aria-labelledby="{escape_html(toggle_id)}" tabindex="0"
             data-ui-disclosure-content data-play-encounter-section-scroll="{escape_html(key)}">
          {content}
        </div>
      </section>
    """


def _linked_reference_count(encounter: Encounter, result: RunDashboardResult) -> str:
    if encounter.reference_links:
        return f"{len(encounter.reference_links)} linked"
    if result.adventure.references:
        return "None linked"
    return "Reference-light"


def _linked_reference_content(encounter: Encounter, result: RunDashboardResult) -> str:
    reference_index = result.reference_status_index()
    cards: list[str] = []
    for link in encounter.reference_links:
        reference = reference_index[link.reference_id].reference
        href = f"/play?{urlencode({'encounter': encounter.id, 'reference': reference.id})}"
        context = (
            f'<p class="play-reference-context">{escape_html(link.context)}</p>'
            if link.context
            else ""
        )
        cards.append(
            f"""
              <article class="play-linked-reference-card">
                <div>
                  <span>{escape_html(reference.kind)}</span>
                  <h3>{escape_html(reference.title)}</h3>
                  <p>{escape_html(reference.summary)}</p>
                  {context}
                </div>
                <a class="button secondary" href="{escape_html(href)}">Open full reference</a>
              </article>
            """
        )
    if cards:
        return f'<div class="play-linked-reference-list">{"".join(cards)}</div>'
    if result.adventure.references:
        return (
            '<p class="play-empty">No persistent reference is linked to this encounter. '
            "Use authored-material search to open an unlinked reference.</p>"
        )
    return '<p class="play-empty">This adventure has no persistent references.</p>'


def _clue_context(clues: tuple[Clue, ...], active_here: bool) -> str:
    mode = "Current visit controls" if active_here else "Browse-only"
    return f"{len(clues)} authored · {mode}"


def _clue_content(
    clues: tuple[Clue, ...],
    outgoing: tuple[RunRevelationStatus, ...],
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
    active_here: bool,
) -> str:
    if not clues:
        cards = '<p class="play-empty">No authored lead is located at this encounter.</p>'
    else:
        clue_progress = result.projection.clue_progress_index()
        revelation_index = result.adventure.revelation_index()
        cards = (
            '<div class="play-clue-list">'
            + "".join(
                _clue_card(
                    clue,
                    clue_progress[clue.id],
                    revelation_index[clue.revelation_id],
                    result,
                    focus_encounter_id,
                    csrf_token,
                    active_here,
                )
                for clue in clues
            )
            + "</div>"
        )
    return f"""
      <div class="play-clue-section-block">
        {cards}
      </div>
      {_outgoing_content(outgoing, result, focus_encounter_id, csrf_token, values)}
    """


def _clue_card(
    clue: Clue,
    progress: ClueProgress,
    revelation: Revelation,
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    active_here: bool,
) -> str:
    spotted_visit = progress.spotted_visit_number
    missed_visits = progress.missed_visit_numbers
    if spotted_visit is not None:
        status = f"Found on visit {spotted_visit}"
        status_class = "found"
    elif missed_visits:
        joined = ", ".join(str(value) for value in missed_visits)
        status = f"Missed on visit {joined}; still recoverable"
        status_class = "missed"
    else:
        status = "Unresolved"
        status_class = "unresolved"
    description = clue.description or "No expanded description."
    actions = ""
    current_visit = result.current_visit
    if active_here and spotted_visit is None and current_visit is not None:
        hidden = render_play_hidden_fields(
            csrf_token,
            result.revision.value,
            focus_encounter_id,
        )
        common = f"""{hidden}<input type="hidden" name="clue_id" value="{escape_html(clue.id)}"><input type="hidden" name="visit_number" value="{current_visit.visit_number}">"""
        missed_here = current_visit.visit_number in missed_visits
        miss_button = (
            '<span class="play-form-help">Already missed on this visit.</span>'
            if missed_here
            else f'<form method="post" action="/play/clue/missed">{common}<button class="button secondary" type="submit">Missed this visit</button></form>'
        )
        actions = f"""
        <div class="play-card-actions">
          <form method="post" action="/play/clue/found">{common}<button class="button primary" type="submit">Mark found</button></form>
          {miss_button}
        </div>
        """
    return f"""
      <article class="play-clue-card {status_class}" id="clue-{escape_html(clue.id)}">
        <header>
          <span>Lead</span><strong>{escape_html(status)}</strong>
        </header>
        <h3>{escape_html(clue.title)}</h3>
        <div class="play-clue-field">
          <h4>How it can be discovered</h4>
          <p>{escape_html(clue.discovery)}</p>
        </div>
        <div class="play-clue-field">
          <h4>What the lead establishes</h4>
          <p>{escape_html(description)}</p>
        </div>
        <footer><span>Supports</span><a href="#revelation-{quote(revelation.id, safe="")}">{escape_html(revelation.title)}</a></footer>
        {actions}
      </article>
    """


def _outgoing_revelations(
    encounter: Encounter,
    result: RunDashboardResult,
) -> tuple[RunRevelationStatus, ...]:
    revelation_ids = {
        clue.revelation_id
        for clue in result.adventure.clues
        if clue.source_encounter_id == encounter.id
    }
    return tuple(
        status for status in result.revelation_statuses if status.revelation.id in revelation_ids
    )


def _outgoing_content(
    statuses: tuple[RunRevelationStatus, ...],
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
) -> str:
    if not statuses:
        content = (
            '<p class="play-empty">No authored revelation is supported from this encounter.</p>'
        )
    else:
        content = (
            '<div class="play-path-list">'
            + "".join(
                _path_card(status, result, focus_encounter_id, csrf_token, values)
                for status in statuses
            )
            + "</div>"
        )
    return f"""
      <section class="play-clue-paths" aria-labelledby="play-clue-paths-heading">
        <div class="play-section-heading">
          <h3 id="play-clue-paths-heading">Paths and conclusions</h3>
          <span>{len(statuses)} supported here</span>
        </div>
        {content}
      </section>
    """


def _path_card(
    status: RunRevelationStatus,
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
) -> str:
    if status.is_established:
        state = "Established"
    elif status.is_foreclosed:
        state = "Foreclosed"
    elif status.spotted_clues:
        state = "Supported"
    else:
        state = "Unsupported"
    destination = status.destination_encounter
    if destination is None:
        destination_html = "<span>Conclusion only</span>"
    else:
        available = destination.id in result.projection.available_encounter_ids
        destination_html = (
            f'<a href="/play?encounter={quote(destination.id, safe="")}">'
            f"{escape_html(destination.title)}</a>"
            f"<span>{'Available' if available else 'Locked'}</span>"
        )
    actions = _revelation_actions(status, result, focus_encounter_id, csrf_token, values)
    return f"""
      <article class="play-path-card" id="revelation-{escape_html(status.revelation.id)}">
        <span class="play-path-state">{escape_html(state)}</span>
        <h3>{escape_html(status.revelation.title)}</h3>
        <p>{escape_html(status.revelation.description)}</p>
        <footer>{destination_html}</footer>
        {actions}
      </article>
    """


def _revelation_actions(
    status: RunRevelationStatus,
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
) -> str:
    if result.projection.active_session_number is None or status.is_established:
        return ""
    selected = values.revelation_id == status.revelation.id
    hidden = render_play_hidden_fields(
        csrf_token,
        result.revision.value,
        focus_encounter_id,
    )
    if status.is_foreclosed:
        reason = values.judgment_reason if selected else ""
        return f"""
        <details class="play-card-control" {"open" if reason else ""}>
          <summary>Reopen revelation</summary>
          <form method="post" action="/play/revelation/reopen" class="play-compact-form">
            {hidden}<input type="hidden" name="revelation_id" value="{escape_html(status.revelation.id)}">
            <label>Reason <textarea name="reason" rows="2" required>{escape_html(reason)}</textarea></label>
            <button class="button primary" type="submit">Reopen</button>
          </form>
        </details>
        """
    selected_ids = (
        set(values.supporting_clue_ids) if selected else {clue.id for clue in status.spotted_clues}
    )
    clue_fields = (
        "".join(
            f'<label class="play-check-row"><input type="checkbox" name="supporting_clue_id" value="{escape_html(clue.id)}" {"checked" if clue.id in selected_ids else ""}><span>{escape_html(clue.title)}</span></label>'
            for clue in status.spotted_clues
        )
        or '<p class="play-form-help">No lead basis is required for explicit GM adjudication.</p>'
    )
    note = values.revelation_note if selected else ""
    reason = values.judgment_reason if selected else ""
    return f"""
      <div class="play-card-control-grid">
        <details class="play-card-control" {"open" if selected and not reason else ""}>
          <summary>Establish</summary>
          <form method="post" action="/play/revelation/establish" class="play-compact-form">
            {hidden}<input type="hidden" name="revelation_id" value="{escape_html(status.revelation.id)}">
            <fieldset><legend>Basis</legend>{clue_fields}</fieldset>
            <label>Note <textarea name="note" rows="2">{escape_html(note)}</textarea></label>
            <button class="button primary" type="submit">Establish revelation</button>
          </form>
        </details>
        <details class="play-card-control" {"open" if bool(reason) else ""}>
          <summary>Foreclose</summary>
          <form method="post" action="/play/revelation/foreclose" class="play-compact-form">
            {hidden}<input type="hidden" name="revelation_id" value="{escape_html(status.revelation.id)}">
            <label>Reason <textarea name="reason" rows="2" required>{escape_html(reason)}</textarea></label>
            <button class="button secondary" type="submit">Foreclose</button>
          </form>
        </details>
      </div>
    """


def _notes_context(result: RunDashboardResult, encounter_id: str) -> str:
    if result.current_visit is None or result.current_encounter is None:
        return "No current visit"
    if result.current_encounter.id != encounter_id:
        return f"Current visit is {result.current_encounter.title}"
    return f"Visit {result.current_visit.visit_number}"


def _visit_notebook_content(
    result: RunDashboardResult,
    encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
    active_here: bool,
    current_here: bool,
    consequences: tuple[EncounterConsequenceRecord, ...],
) -> str:
    legacy = _consequence_content(consequences)
    if not current_here or result.current_visit is None:
        return f"""
          <p class="play-empty">Encounter notes are visit-specific. Start a visit here, or focus the current scene, before writing canonical notes.</p>
          {legacy}
        """
    visit = result.current_visit
    committed = "".join(f"<li>{escape_html(note)}</li>" for note in visit.notes)
    committed_html = (
        f'<ol class="play-committed-notes">{committed}</ol>'
        if committed
        else '<p class="play-empty">No note has yet been committed for this visit.</p>'
    )
    if not active_here:
        return f"""
          <p class="play-empty">Begin a session in the left rail to continue recording this visit.</p>
          <details class="play-committed-notes-shell">
            <summary>Committed notes for this visit</summary>
            {committed_html}
          </details>
          {legacy}
        """
    notebook_value = ""
    submitted = False
    if values.note_visit_number == visit.visit_number:
        notebook_value = values.note_text
        submitted = True
    elif values.transition_source_visit_number == visit.visit_number:
        notebook_value = values.transition_note
        submitted = True
    hidden = render_play_hidden_fields(csrf_token, result.revision.value, encounter_id)
    return f"""
      <p class="play-section-intro">Record anything the GM wants to remember about this visit: decisions, reactions, unresolved questions, changed circumstances, or likely consequences.</p>
      <form method="post" action="/play/note" class="play-compact-form play-notebook-form" data-play-notebook-form>
        {hidden}<input type="hidden" name="visit_number" value="{visit.visit_number}">
        <label class="sr-only" for="play-notebook">Working notes for visit {visit.visit_number}</label>
        <textarea id="play-notebook" name="text" rows="8" required
                  data-play-notebook data-play-visit-number="{visit.visit_number}"
                  data-play-submitted="{"1" if submitted else "0"}"
                  placeholder="Record decisions, reactions, unanswered questions, and what changed…">{escape_html(notebook_value)}</textarea>
        <div class="play-notebook-status" role="status" aria-live="polite" aria-atomic="true"
             data-play-notebook-status>Draft not yet saved in history</div>
        <p class="play-form-help">Save this note by itself, or use Current visit actions to save it with lead outcomes and a move.</p>
        <button class="button primary" type="submit">Save note only</button>
      </form>
      <details class="play-committed-notes-shell">
        <summary>Committed notes for this visit</summary>
        {committed_html}
      </details>
      {legacy}
    """


def _consequence_content(consequences: Iterable[EncounterConsequenceRecord]) -> str:
    values = tuple(consequences)
    if not values:
        return ""
    content = (
        '<ol class="play-consequence-list">'
        + "".join(f"<li>{escape_html(item.text)}</li>" for item in values)
        + "</ol>"
    )
    return f"""
      <section class="play-legacy-notes">
        <div class="play-section-heading">
          <h3>Earlier persistent notes</h3><span>{len(values)} legacy records</span>
        </div>
        <p class="play-section-intro">These records came from an earlier version of Play mode. New persistent developments can be written directly into encounter notes.</p>
        {content}
      </section>
    """
