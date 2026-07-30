"""HTML rendering for the table-centered Play mode shell."""

from __future__ import annotations

import json
from urllib.parse import quote, urlencode

from adventure_graph.application.dice import DiceRollResult, format_dice_roll
from adventure_graph.application.run_workspace import (
    RunDashboardResult,
    RunReferenceStatus,
    RunRevelationStatus,
)
from adventure_graph.domain.adventure import Encounter
from adventure_graph.domain.play_events import (
    DiceGroupResult,
    DiceModifierResult,
)
from adventure_graph.domain.play_state import ReferenceNoteRecord, SessionRecord, VisitRecord
from adventure_graph.interfaces.web.markdown import render_safe_markdown
from adventure_graph.interfaces.web.page_rendering import (
    escape_html,
    render_notice,
    render_play_authored_search,
    render_play_context_topbar,
    render_play_encounter_records,
    render_play_navigation,
    render_play_pin_panel,
    render_play_recent_focus_panel,
    render_play_reference_records,
)
from adventure_graph.interfaces.web.play_encounter_rendering import (
    render_focused_encounter_sections,
)
from adventure_graph.interfaces.web.play_rendering_support import render_play_hidden_fields
from adventure_graph.interfaces.web.view_models import PageNotice, PlayFormValues


def render_play(
    result: RunDashboardResult,
    project_label: str,
    *,
    csrf_token: str,
    focus_encounter_id: str | None = None,
    selected_reference_id: str | None = None,
    notice: PageNotice | None = None,
    values: PlayFormValues | None = None,
    clear_draft_visit_number: int | None = None,
    show_session_review: bool = False,
    dice_roll: DiceRollResult | None = None,
) -> str:
    """Render a navigation-first Play mode without recording canonical state."""
    del project_label
    adventure = result.adventure
    if not adventure.encounters:
        return _render_empty_play(adventure.id, adventure.title, notice)
    focused = _resolve_focus(result, focus_encounter_id)
    selected_reference = result.reference_status_index().get(selected_reference_id or "")
    current = result.current_encounter
    submitted = values or PlayFormValues()
    clear_attribute = (
        ""
        if clear_draft_visit_number is None
        else f' data-play-clear-draft-visit="{clear_draft_visit_number}"'
    )
    selected_attribute = (
        ""
        if selected_reference is None
        else f' data-play-selected-reference-id="{escape_html(selected_reference.reference.id)}"'
    )
    body_attributes = (
        f' data-play-adventure-id="{escape_html(adventure.id)}"'
        f' data-play-focused-encounter-id="{escape_html(focused.id)}"'
        f"{selected_attribute}{clear_attribute}"
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>Play — {escape_html(adventure.title)}</title>
  <script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css">
</head>
<body class="play-body"{body_attributes}>
  <a class="skip-link" href="#play-encounter-reader">Skip to focused encounter</a>
  {render_play_topbar(adventure.title)}
  <div class="play-workspace" data-play-workspace>
    <aside class="play-route-rail" id="play-route-drawer"
           aria-label="Play navigation and authored material" data-play-drawer="route">
      <div class="play-rail-inner">
        {_play_left_rail(result, focused.id, csrf_token, submitted, "play")}
      </div>
    </aside>
    <main class="play-main" id="play-encounter-reader" tabindex="-1">
      <div class="play-main-inner">
        {render_notice(notice)}
        {_session_review_panel() if show_session_review else ""}
        {_focus_context(focused, current, result, csrf_token, submitted)}
        {_selected_reference_panel(selected_reference, result, focused.id, csrf_token, submitted)}
        {render_focused_encounter_sections(focused, result, csrf_token, submitted)}
      </div>
    </main>
    <aside class="play-utility-rail" id="play-utility-drawer"
           aria-label="Current context and play tools" data-play-drawer="utility">
      <div class="play-rail-inner">
        {_play_right_rail(result, focused.id, csrf_token, submitted, dice_roll)}
      </div>
    </aside>
  </div>
  <nav class="play-mobile-nav" aria-label="Play mode panels">
    <button type="button" data-play-drawer-toggle="route" aria-controls="play-route-drawer"
            aria-expanded="false">Navigate &amp; find</button>
    <a href="/play?encounter={quote(focused.id, safe="")}">Encounter</a>
    <button type="button" data-play-drawer-toggle="utility" aria-controls="play-utility-drawer"
            aria-expanded="false">
      Context &amp; tools
    </button>
  </nav>
  <div class="play-drawer-scrim" data-play-drawer-close aria-hidden="true" hidden></div>
  {render_play_encounter_records(adventure.encounters)}
  {render_play_reference_records(adventure.references, focused.id)}
</body></html>"""


def _render_empty_play(
    adventure_id: str,
    adventure_title: str,
    notice: PageNotice | None,
) -> str:
    """Render the valid pre-play state for an adventure without encounters."""
    add_encounter_href = escape_html(f"/encounters/new?{urlencode({'return_to': '/play'})}")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>Play — {escape_html(adventure_title)}</title>
  <script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css">
</head>
<body class="play-body" data-play-adventure-id="{escape_html(adventure_id)}">
  <a class="skip-link" href="#play-empty-state">Skip to Play mode status</a>
  {render_play_topbar(adventure_title)}
  <main class="play-empty-page" id="play-empty-state" tabindex="-1">
    <section class="play-empty-panel">
      {render_notice(notice)}
      <p class="eyebrow">Play mode</p>
      <h1>This adventure has no encounters yet.</h1>
      <p>Add an encounter before beginning play.</p>
      <div class="button-row">
        <a class="button primary" href="{add_encounter_href}">Add first encounter</a>
        <a class="button secondary" href="/">Return to Author mode</a>
      </div>
    </section>
  </main>
</body></html>"""


def render_play_topbar(adventure_title: str) -> str:
    return render_play_context_topbar(adventure_title)


def render_play_workspace_page(
    result: RunDashboardResult,
    *,
    csrf_token: str,
    title: str,
    current_kind: str,
    body: str,
    focus_encounter_id: str | None = None,
    values: PlayFormValues | None = None,
    body_class: str = "",
    player_safe: bool = False,
) -> str:
    """Render a secondary Play workspace inside the same persistent table chrome."""
    focused = _resolve_focus(result, focus_encounter_id)
    submitted = values or PlayFormValues()
    classes = " ".join(item for item in ("play-body", "play-secondary-body", body_class) if item)
    attributes = (
        f' data-play-adventure-id="{escape_html(result.adventure.id)}"'
        f' data-play-focused-encounter-id="{escape_html(focused.id)}"'
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark">
  <title>{escape_html(title)}</title>
  <script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css">
</head>
<body class="{escape_html(classes)}"{attributes}>
  <a class="skip-link" href="#play-secondary-content">Skip to workspace</a>
  {render_play_topbar(result.adventure.title)}
  <div class="play-workspace" data-play-workspace>
    <aside class="play-route-rail" id="play-route-drawer"
           aria-label="Play navigation and authored material" data-play-drawer="route">
      <div class="play-rail-inner">
        {_play_left_rail(result, focused.id, csrf_token, submitted, current_kind)}
      </div>
    </aside>
    <main class="play-main play-secondary-main" id="play-secondary-content" tabindex="-1">
      <div class="play-main-inner play-secondary-main-inner">{body}</div>
    </main>
    <aside class="play-utility-rail" id="play-utility-drawer"
           aria-label="Current context and play tools" data-play-drawer="utility">
      <div class="play-rail-inner">
        {
        _play_right_rail(
            result,
            focused.id,
            csrf_token,
            submitted,
            None,
            player_safe=player_safe,
        )
    }
      </div>
    </aside>
  </div>
  <nav class="play-mobile-nav" aria-label="Play mode panels">
    <button type="button" data-play-drawer-toggle="route" aria-controls="play-route-drawer"
            aria-expanded="false">Navigate &amp; find</button>
    <a href="/play?encounter={quote(focused.id, safe="")}">Encounter</a>
    <button type="button" data-play-drawer-toggle="utility" aria-controls="play-utility-drawer"
            aria-expanded="false">Context &amp; tools</button>
  </nav>
  <div class="play-drawer-scrim" data-play-drawer-close aria-hidden="true" hidden></div>
  {render_play_encounter_records(result.adventure.encounters)}
  {render_play_reference_records(result.adventure.references, focused.id)}
</body></html>"""


def _play_left_rail(
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
    current_kind: str,
) -> str:
    return f"""
      {render_play_navigation(current_kind)}
      {render_play_authored_search(result.adventure, focus_encounter_id)}
      {_session_card(result, focus_encounter_id, csrf_token, values)}
      {_route_rail(result, focus_encounter_id)}
    """


def _play_right_rail(
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
    dice_roll: DiceRollResult | None,
    *,
    player_safe: bool = False,
) -> str:
    if player_safe:
        return """
          <section class="play-utility-card">
            <div class="play-utility-heading"><h2>Player-safe view</h2><span>GM context hidden</span></div>
            <p>This rail intentionally omits authored secrets, private notes, missed leads, and adjudication controls.</p>
          </section>
        """
    return f"""
      {_current_scene_card(result)}
      {render_play_pin_panel()}
      {_dice_tray(result, focus_encounter_id, csrf_token, values, dice_roll)}
      {_live_play_panel(result, focus_encounter_id, csrf_token, values)}
      {_history_summary_panel(result)}
      {render_play_recent_focus_panel()}
      {_keyboard_panel()}
    """


def _resolve_focus(result: RunDashboardResult, requested_id: str | None) -> Encounter:
    encounter_index = result.adventure.encounter_index()
    if requested_id is not None and requested_id in encounter_index:
        return encounter_index[requested_id]
    if result.current_encounter is not None:
        return result.current_encounter
    start = next((encounter for encounter in result.adventure.encounters if encounter.start), None)
    return start or result.adventure.encounters[0]


def _session_card(
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
) -> str:
    active_number = result.projection.active_session_number
    hidden = render_play_hidden_fields(csrf_token, result.revision.value, focus_encounter_id)
    if active_number is None:
        title = "Between sessions"
        copy = "Browsing and pinning are available. Begin a session to record visits, leads, revelations, and encounter notes."
        controls = f"""
        <form method="post" action="/play/session/start" class="play-compact-form play-session-form">
          {hidden}
          <button class="button primary play-wide-button" type="submit">Begin session</button>
          <details class="play-session-controls" {"open" if values.session_title or values.session_opening_note else ""}>
            <summary>Add session details</summary>
            <label>Title <input name="title" value="{escape_html(values.session_title)}" placeholder="Optional"></label>
            <label>Date <input type="date" name="played_on" value="{escape_html(values.session_played_on)}"></label>
            <label>Participants <input name="participants" value="{escape_html(values.session_participants)}" placeholder="Comma-separated"></label>
            <label>Attendance note <textarea name="attendance_note" rows="2">{escape_html(values.session_attendance_note)}</textarea></label>
            <label>Opening note <textarea name="opening_note" rows="3">{escape_html(values.session_opening_note)}</textarea></label>
          </details>
        </form>
        """
        badge = "Between sessions"
    else:
        session = next(
            item for item in result.projection.sessions if item.session_number == active_number
        )
        title = session.title or f"Session {session.session_number}"
        copy_parts: list[str] = []
        if session.played_on:
            copy_parts.append(session.played_on)
        if session.participants:
            copy_parts.append(", ".join(session.participants))
        copy = " · ".join(copy_parts) or "Explicit session in progress."
        controls = f"""
        <form method="post" action="/play/session/end" class="play-compact-form play-session-form">
          {hidden}
          <button class="button secondary play-wide-button" type="submit">End session</button>
          <details class="play-session-controls" {"open" if values.session_closing_note else ""}>
            <summary>Add a closing note</summary>
            <label>Closing note <textarea name="closing_note" rows="3">{escape_html(values.session_closing_note)}</textarea></label>
            <p class="play-form-help">Commit any working notebook text first; local drafts remain in this browser after the session ends.</p>
          </details>
        </form>
        """
        badge = f"Session {session.session_number} active"
    return f"""
      <section class="play-session-card">
        <span class="play-status-badge">{escape_html(badge)}</span>
        <h2>{escape_html(title)}</h2>
        <p>{escape_html(copy)}</p>
        {controls}
      </section>
    """


def _route_rail(result: RunDashboardResult, focused_encounter_id: str) -> str:
    visits = result.projection.visits
    if not visits:
        return """
        <section class="play-route-section">
          <div class="play-rail-heading"><h2>Route</h2><span>0 visits</span></div>
          <p class="play-empty">No visit has been recorded. Begin a session above, choose an encounter, then use Start visit in the center panel. Browsing or pinning does not record play.</p>
        </section>
        """
    grouped = _group_visits_by_session(visits, result.projection.sessions)
    blocks = "".join(
        _route_group(label, group, result, focused_encounter_id) for label, group in grouped
    )
    return f"""
      <section class="play-route-section">
        <div class="play-rail-heading">
          <h2>Chronological route</h2><span>{len(visits)} visits</span>
        </div>
        <div class="play-route-list" data-play-route-list>{blocks}</div>
      </section>
    """


def _group_visits_by_session(
    visits: tuple[VisitRecord, ...], sessions: tuple[SessionRecord, ...]
) -> tuple[tuple[str, tuple[VisitRecord, ...]], ...]:
    session_by_visit = {
        visit_number: session for session in sessions for visit_number in session.visit_numbers
    }
    groups: list[tuple[int | None, str, list[VisitRecord]]] = []
    for visit in visits:
        session = session_by_visit.get(visit.visit_number)
        key = session.session_number if session is not None else None
        label = (
            "Earlier play"
            if session is None
            else session.title or f"Session {session.session_number}"
        )
        if not groups or groups[-1][0] != key:
            groups.append((key, label, []))
        groups[-1][2].append(visit)
    return tuple((label, tuple(group)) for _, label, group in groups)


def _route_group(
    label: str,
    visits: tuple[VisitRecord, ...],
    result: RunDashboardResult,
    focused_encounter_id: str,
) -> str:
    encounter_index = result.adventure.encounter_index()
    current_number = result.current_visit.visit_number if result.current_visit is not None else None
    links = "".join(
        _route_link(
            visit, encounter_index[visit.encounter_id], current_number, focused_encounter_id
        )
        for visit in visits
    )
    return f"""
      <section class="play-route-group">
        <h3>{escape_html(label)}</h3>
        <div>{links}</div>
      </section>
    """


def _route_link(
    visit: VisitRecord,
    encounter: Encounter,
    current_visit_number: int | None,
    focused_encounter_id: str,
) -> str:
    classes = ["play-route-link"]
    labels: list[str] = []
    if visit.visit_number == current_visit_number:
        classes.append("current")
        labels.append("Current")
    if visit.encounter_id == focused_encounter_id:
        classes.append("focused")
        labels.append("Focused")
    if visit.party_label:
        labels.append(visit.party_label)
    status = " · ".join(labels)
    status_html = f"<small>{escape_html(status)}</small>" if status else ""
    return f"""
      <a class="{" ".join(classes)}"
         href="/play?encounter={quote(encounter.id, safe="")}"
         data-play-route-link data-encounter-id="{escape_html(encounter.id)}">
        <span class="play-route-number">{visit.visit_number}</span>
        <span><strong>{escape_html(encounter.title)}</strong>{status_html}</span>
      </a>
    """


def _focus_context(
    focused: Encounter,
    current: Encounter | None,
    result: RunDashboardResult,
    csrf_token: str,
    values: PlayFormValues,
) -> str:
    encounter_progress = result.projection.encounter_progress_index()[focused.id]
    labels = ["Available" if encounter_progress.available else "Locked"]
    labels.append("Necessary" if focused.required else "Optional")
    if focused.start:
        labels.append("Start")
    if focused.end:
        labels.append("End")
    if encounter_progress.visit_count:
        suffix = "time" if encounter_progress.visit_count == 1 else "times"
        labels.append(f"Visited {encounter_progress.visit_count} {suffix}")
    if current is not None and current.id == focused.id:
        labels.append("Current visit")
    badges = "".join(f"<span>{escape_html(label)}</span>" for label in labels)
    if current is None:
        context = "No current visit has been recorded. This encounter is only being inspected."
    elif current.id == focused.id:
        context = "The focused encounter is also the current recorded visit."
    else:
        context = (
            f"Browsing {focused.title}; the current recorded visit remains {current.title}. "
            "No journal event was added."
        )
    active = result.projection.active_session_number is not None
    hidden = render_play_hidden_fields(csrf_token, result.revision.value, focused.id)
    if not active:
        canonical_action = (
            '<button class="button primary" type="button" disabled>Begin session first</button>'
        )
    elif current is not None and current.id == focused.id:
        canonical_action = (
            '<button class="button primary" type="button" disabled>Current visit</button>'
        )
    elif encounter_progress.available:
        party_label = values.enter_party_label if values.enter_encounter_id == focused.id else ""
        label = "Start another visit" if encounter_progress.visit_count else "Start visit"
        canonical_action = f"""
        <form method="post" action="/play/enter" class="play-inline-action">
          {hidden}<input type="hidden" name="encounter_id" value="{escape_html(focused.id)}">
          <label class="sr-only" for="enter-party-{escape_html(focused.id)}">Split-party label</label>
          <span class="play-form-help">Optional: identify the subgroup making this visit.</span>
          <input id="enter-party-{escape_html(focused.id)}" name="party_label"
                 value="{escape_html(party_label)}" placeholder="Split-party label">
          <button class="button primary" type="submit">{label}</button>
        </form>
        """
    else:
        reason = values.unlock_reason if values.unlock_encounter_id == focused.id else ""
        canonical_action = f"""
        <details class="play-inline-action" {"open" if reason else ""}>
          <summary class="button secondary">Unlock encounter</summary>
          <form method="post" action="/play/unlock" class="play-compact-form">
            {hidden}<input type="hidden" name="encounter_id" value="{escape_html(focused.id)}">
            <label>GM reason <textarea name="reason" rows="2" required>{escape_html(reason)}</textarea></label>
            <button class="button primary" type="submit">Unlock and keep focused</button>
          </form>
        </details>
        """
    authoring_actions = _play_authoring_actions(focused.id)
    return f"""
      <section class="play-focus-header">
        <div class="play-focus-copy">
          <p class="eyebrow">Focused encounter</p>
          <h1>{escape_html(focused.title)}</h1>
          <p class="play-focus-context">{escape_html(context)}</p>
          <div class="play-encounter-badges">{badges}</div>
        </div>
        <div class="play-focus-actions">
          <button class="button secondary" type="button" data-play-pin-toggle
                  data-play-pin-kind="encounter" data-play-pin-id="{escape_html(focused.id)}"
                  data-encounter-id="{escape_html(focused.id)}" aria-pressed="false">
            Pin encounter
          </button>
          {authoring_actions}
          {canonical_action}
        </div>
      </section>
    """


def _play_authoring_actions(encounter_id: str) -> str:
    """Render author-level improvisation links that return to the current table context."""
    return_to = f"/play?{urlencode({'encounter': encounter_id})}"
    encounter_href = escape_html(f"/encounters/new?{urlencode({'return_to': return_to})}")
    clue_href = escape_html(
        f"/clues/new?{urlencode({'source': encounter_id, 'return_to': return_to})}"
    )
    revelation_href = escape_html(
        f"/revelations/new?{urlencode({'source': encounter_id, 'return_to': return_to})}"
    )
    reference_href = escape_html(
        f"/references/new?{urlencode({'encounter': encounter_id, 'return_to': return_to})}"
    )
    return f"""
      <details class="play-authoring-menu">
        <summary class="button secondary">Add to adventure</summary>
        <div class="play-authoring-menu-panel">
          <a href="{clue_href}">Add lead here</a>
          <a href="{revelation_href}">Add revelation and lead here</a>
          <a href="{reference_href}">Add linked reference</a>
          <a href="{encounter_href}">Add encounter</a>
          <p>These create ordinary authored adventure entities. Play records only visits, outcomes, and notes; it does not create a separate runtime entity type.</p>
        </div>
      </details>
    """


def _selected_reference_panel(
    status: RunReferenceStatus | None,
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
) -> str:
    if status is None:
        return ""
    reference = status.reference
    aliases = ", ".join(escape_html(alias) for alias in reference.aliases) or "none"
    tags = ", ".join(escape_html(tag) for tag in reference.tags) or "none"
    backlinks = "".join(
        _reference_backlink_item(status, index) for index in range(len(status.backlinks))
    )
    backlink_content = (
        f'<ol class="play-reference-backlinks">{backlinks}</ol>'
        if backlinks
        else '<p class="play-empty">This reference is not linked to an encounter.</p>'
    )
    close_href = f"/play?{urlencode({'encounter': focus_encounter_id})}"
    return f"""
      <section class="play-selected-reference" data-play-selected-reference>
        <header class="play-selected-reference-header">
          <div>
            <p class="eyebrow">Selected {escape_html(reference.kind)}</p>
            <h2>{escape_html(reference.title)}</h2>
            <p>{escape_html(reference.summary)}</p>
          </div>
          <div class="play-selected-reference-actions">
            <button class="button secondary" type="button" data-play-pin-toggle
                    data-play-pin-kind="reference" data-play-pin-id="{escape_html(reference.id)}"
                    aria-pressed="false">Pin reference</button>
            <a class="button secondary" href="{escape_html(close_href)}">Close reference</a>
          </div>
        </header>
        <div class="play-selected-reference-grid">
          <div class="play-selected-reference-prose prose">
            {render_safe_markdown(reference.content)}
          </div>
          <aside class="play-selected-reference-meta">
            <dl>
              <div><dt>Aliases</dt><dd>{aliases}</dd></div>
              <div><dt>Tags</dt><dd>{tags}</dd></div>
            </dl>
            <h3>Encounter backlinks</h3>
            {backlink_content}
          </aside>
        </div>
        {_reference_notes(status, result, focus_encounter_id, csrf_token, values)}
      </section>
    """


def _reference_notes(
    status: RunReferenceStatus,
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
) -> str:
    reference = status.reference
    session_index = {session.session_number: session for session in result.projection.sessions}
    notes = "".join(
        _reference_note_item(
            note,
            session_index.get(note.session_number) if note.session_number is not None else None,
        )
        for note in status.notes
    )
    note_history = (
        f'<ol class="play-reference-note-list">{notes}</ol>'
        if notes
        else '<p class="play-empty">No playthrough notes have been recorded for this reference.</p>'
    )
    if result.projection.active_session_number is None:
        form = """
          <p class="play-empty">Begin a session in the left rail to add another chronological note.</p>
        """
    else:
        value = values.reference_note_text if values.selected_reference_id == reference.id else ""
        hidden = render_play_hidden_fields(csrf_token, result.revision.value, focus_encounter_id)
        field_id = f"reference-note-{reference.id}"
        form = f"""
          <form method="post" action="/play/reference/note"
                class="play-compact-form play-reference-note-form">
            {hidden}
            <input type="hidden" name="reference_id" value="{escape_html(reference.id)}">
            <label for="{escape_html(field_id)}">Add a playthrough note</label>
            <textarea id="{escape_html(field_id)}" name="text" rows="4" required
                      placeholder="Record what changed, what this person learned, or what the party now knows…">{escape_html(value)}</textarea>
            <p class="play-form-help">Saving appends a chronological play record associated with this reference. It does not alter the authored description above.</p>
            <button class="button primary" type="submit">Save reference note</button>
          </form>
        """
    return f"""
      <section class="play-reference-notes" aria-labelledby="reference-notes-heading">
        <div class="play-reference-notes-header">
          <div>
            <p class="eyebrow">Playthrough record</p>
            <h3 id="reference-notes-heading">Notes on {escape_html(reference.title)}</h3>
          </div>
          <span>{len(status.notes)} committed</span>
        </div>
        {note_history}
        {form}
      </section>
    """


def _reference_note_item(note: ReferenceNoteRecord, session: SessionRecord | None) -> str:
    session_label = (
        f"Session {note.session_number}"
        if note.session_number is not None
        else "Before explicit sessions"
    )
    if session is not None and session.title:
        session_label = f"{session_label}: {session.title}"
    return f"""
      <li class="play-reference-note">
        <span class="play-reference-note-meta">{escape_html(session_label)} · Event {note.sequence}</span>
        <p>{escape_html(note.text)}</p>
      </li>
    """


def _reference_backlink_item(status: RunReferenceStatus, index: int) -> str:
    reference = status.reference
    backlink = status.backlinks[index]
    href = f"/play?{urlencode({'encounter': backlink.encounter.id, 'reference': reference.id})}"
    context = f"<p>{escape_html(backlink.context)}</p>" if backlink.context else ""
    return f"""
      <li>
        <a href="{escape_html(href)}"><strong>{escape_html(backlink.encounter.title)}</strong></a>
        {context}
      </li>
    """


def _current_scene_card(result: RunDashboardResult) -> str:
    if result.current_encounter is None or result.current_visit is None:
        return """
        <section class="play-utility-card play-current-card">
          <span class="play-utility-kicker">Current visit</span>
          <h2>None recorded</h2>
          <p>Focus and pin freely. Begin a session in the left rail, then use Start visit in the center panel when table play begins.</p>
        </section>
        """
    encounter = result.current_encounter
    visit = result.current_visit
    party = f" · {visit.party_label}" if visit.party_label else ""
    return f"""
      <section class="play-utility-card play-current-card">
        <span class="play-utility-kicker">Current visit</span>
        <h2>{escape_html(encounter.title)}</h2>
        <p>Visit {visit.visit_number}{escape_html(party)}</p>
        <a href="/play?encounter={quote(encounter.id, safe="")}" data-play-current-link>
          Focus current scene
        </a>
      </section>
    """


def _live_play_panel(
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
) -> str:
    current_visit = result.current_visit
    current_encounter = result.current_encounter
    if current_visit is None or current_encounter is None:
        return """
        <section class="play-utility-card play-live-card">
          <span class="play-utility-kicker">Current visit actions</span>
          <h2>No current visit</h2>
          <p>Begin a session, then start a visit at an available encounter.</p>
        </section>
        """
    if result.projection.active_session_number is None:
        return """
        <section class="play-utility-card play-live-card">
          <span class="play-utility-kicker">Current visit actions</span>
          <h2>Between sessions</h2>
          <p>Begin a session in the left rail to resume recording this visit.</p>
        </section>
        """
    hidden = render_play_hidden_fields(csrf_token, result.revision.value, focus_encounter_id)
    clue_controls = _transition_clue_controls(result, values)
    revelation_controls = _transition_revelation_controls(result, values)
    destination_options = _transition_destination_options(result, values)
    return f"""
      <section class="play-utility-card play-live-card">
        <div class="play-utility-heading"><h2>Current visit actions</h2><span>Visit {current_visit.visit_number}</span></div>
        <details class="play-live-details play-transition-details" open>
          <summary>Save outcomes and choose the next encounter</summary>
          <form method="post" action="/play/transition" class="play-compact-form" data-play-transition-form>
            {hidden}<input type="hidden" name="source_visit_number" value="{current_visit.visit_number}">
            <input type="hidden" name="note" value="{escape_html(values.transition_note)}" data-play-transition-note>
            {clue_controls}
            {revelation_controls}
            <label>Next encounter
              <select name="destination_encounter_id" data-play-transition-destination><option value="">Stay here; save outcomes only</option>{destination_options}</select>
            </label>
            <label>Split-party label
              <input name="party_label" value="{escape_html(values.transition_party_label)}" placeholder="Optional subgroup name">
            </label>
            <p class="play-form-help">Use the split-party label only when a subgroup is acting separately. A destination unlocked by a revelation becomes selectable when that revelation is checked above.</p>
            <p class="play-transition-summary" data-play-transition-summary aria-live="polite" hidden></p>
            <button class="button primary play-wide-button" type="submit" data-play-transition-submit>Save outcomes without moving</button>
          </form>
        </details>
      </section>
    """


def _transition_clue_controls(result: RunDashboardResult, values: PlayFormValues) -> str:
    unresolved = tuple(item for item in result.current_clues if not item.spotted)
    if not unresolved:
        return '<p class="play-form-help">No unresolved lead remains at this encounter.</p>'
    found = set(values.transition_spotted_clue_ids)
    missed = set(values.transition_missed_clue_ids)
    rows = "".join(
        f"""
        <div class="play-transition-row">
          <span>{escape_html(item.clue.title)}</span>
          <label><input type="checkbox" name="spotted_clue_id" value="{escape_html(item.clue.id)}" {"checked" if item.clue.id in found else ""} data-play-outcome="found"> Found</label>
          <label><input type="checkbox" name="missed_clue_id" value="{escape_html(item.clue.id)}" {"checked" if item.clue.id in missed else ""} data-play-outcome="missed"> Missed</label>
        </div>
        """
        for item in unresolved
    )
    return f"<fieldset><legend>Lead outcomes</legend>{rows}</fieldset>"


def _transition_revelation_controls(result: RunDashboardResult, values: PlayFormValues) -> str:
    selected = set(values.transition_revelation_ids)
    current_revelation_ids = {item.revelation.id for item in result.current_clues}
    choices = tuple(
        item
        for item in result.revelation_statuses
        if item.revelation.id in current_revelation_ids
        and not item.is_established
        and not item.is_foreclosed
    )
    if not choices:
        return ""
    rows = "".join(
        f'<label class="play-check-row"><input type="checkbox" name="established_revelation_id" value="{escape_html(item.revelation.id)}" {"checked" if item.revelation.id in selected else ""}><span>{escape_html(item.revelation.title)}</span></label>'
        for item in choices
    )
    return f"<fieldset><legend>Establish supported revelations</legend>{rows}</fieldset>"


def _transition_destination_options(result: RunDashboardResult, values: PlayFormValues) -> str:
    current_id = result.current_encounter.id if result.current_encounter is not None else None
    available = {option.encounter.id: option for option in result.available_encounters}
    potential_unlocks: dict[str, list[RunRevelationStatus]] = {}
    current_source_ids = {clue.revelation.id for clue in result.current_clues}
    for status in result.revelation_statuses:
        destination = status.destination_encounter
        if (
            destination is not None
            and destination.id != current_id
            and status.revelation.id in current_source_ids
            and not status.is_foreclosed
        ):
            potential_unlocks.setdefault(destination.id, []).append(status)

    encounter_index = result.adventure.encounter_index()
    destination_ids = [
        option.encounter.id
        for option in result.available_encounters
        if option.encounter.id != current_id
    ]
    destination_ids.extend(
        encounter_id for encounter_id in potential_unlocks if encounter_id not in available
    )
    options: list[str] = []
    selected_revelations = set(values.transition_revelation_ids)
    for encounter_id in destination_ids:
        encounter = encounter_index[encounter_id]
        option = available.get(encounter_id)
        statuses = potential_unlocks.get(encounter_id, [])
        currently_available = option is not None
        requirement_ids = (
            ()
            if currently_available
            else tuple(status.revelation.id for status in statuses if not status.is_established)
        )
        requirement_titles = (
            ()
            if currently_available
            else tuple(status.revelation.title for status in statuses if not status.is_established)
        )
        enabled_by_submission = bool(selected_revelations.intersection(requirement_ids))
        disabled = not currently_available and not enabled_by_submission
        if currently_available:
            suffix = " · available"
            if option.visit_count:
                suffix = f" · revisit ({option.visit_count} prior)"
        else:
            suffix = " · establish " + " or ".join(requirement_titles)
        attrs = [
            f'value="{escape_html(encounter.id)}"',
            f'data-encounter-title="{escape_html(encounter.title)}"',
            f'data-requires-revelations="{escape_html(",".join(requirement_ids))}"',
        ]
        if values.transition_destination_encounter_id == encounter.id:
            attrs.append("selected")
        if disabled:
            attrs.append("disabled")
        options.append(
            f"<option {' '.join(attrs)}>{escape_html(encounter.title + suffix)}</option>"
        )
    if not options:
        return (
            '<option value="" disabled>No authored next encounter is currently available</option>'
        )
    return "".join(options)


def _dice_tray(
    result: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    values: PlayFormValues,
    roll: DiceRollResult | None,
) -> str:
    expression = values.dice_expression or "1d20"
    label = values.dice_label
    roll_result = (
        "" if roll is None else _dice_result(result, focus_encounter_id, csrf_token, label, roll)
    )
    return f"""
      <section class="play-utility-card play-dice-card">
        <div class="play-utility-heading"><h2>Dice tray</h2><span>Ephemeral by default</span></div>
        <form method="post" action="/play/dice/roll" class="play-compact-form" data-play-dice-form>
          <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}">
          <input type="hidden" name="focus_encounter_id" value="{escape_html(focus_encounter_id)}">
          <label>Expression
            <input name="expression" value="{escape_html(expression)}" maxlength="256"
                   autocomplete="off" spellcheck="false" data-play-dice-expression>
          </label>
          <label>Label
            <input name="label" value="{escape_html(label)}" maxlength="160"
                   placeholder="Optional: Hold the gate" data-play-dice-label>
          </label>
          <button class="button primary play-wide-button" type="submit">Roll</button>
        </form>
        {roll_result}
        <div class="play-dice-recents" data-play-dice-recents>
          <p class="play-empty">Recent expressions stay in this browser.</p>
        </div>
      </section>
    """


def _dice_result(
    dashboard: RunDashboardResult,
    focus_encounter_id: str,
    csrf_token: str,
    label: str,
    roll: DiceRollResult,
) -> str:
    terms = "".join(_dice_term(term) for term in roll.terms)
    notebook_text = format_dice_roll(roll, label=label)
    payload = _dice_payload(roll)
    can_record = (
        dashboard.projection.active_session_number is not None or not dashboard.projection.sessions
    )
    record_control = (
        f"""
        <form method="post" action="/play/dice/record" class="play-dice-record-form">
          {render_play_hidden_fields(csrf_token, dashboard.revision.value, focus_encounter_id)}
          <input type="hidden" name="label" value="{escape_html(label)}">
          <input type="hidden" name="roll_payload" value="{escape_html(payload)}">
          <button class="button secondary" type="submit">Record in journal</button>
        </form>
        """
        if can_record
        else '<span class="play-dice-record-disabled">Begin a session to record this roll.</span>'
    )
    label_html = f'<p class="play-dice-result-label">{escape_html(label)}</p>' if label else ""
    return f"""
        <article class="play-dice-result" data-play-dice-result
                 data-expression="{escape_html(roll.expression)}"
                 data-label="{escape_html(label)}"
                 data-notebook-text="{escape_html(notebook_text)}">
          {label_html}
          <div class="play-dice-equation"><span>{escape_html(roll.expression)}</span><strong>{roll.total}</strong></div>
          <div class="play-dice-terms">{terms}</div>
          <div class="play-dice-actions">
            <button class="button secondary" type="button" data-play-dice-insert>Insert in notebook</button>
            {record_control}
          </div>
          <p class="play-form-help">This result remains outside play history unless you record it.</p>
        </article>
    """


def _dice_term(term: DiceGroupResult | DiceModifierResult) -> str:
    if isinstance(term, DiceGroupResult):
        values = "".join(f"<span>{value}</span>" for value in term.results)
        subtotal = term.sign * sum(term.results)
        sign = "-" if term.sign < 0 else "+"
        return f"""
          <div class="play-dice-term">
            <small>{sign} {len(term.results)}d{term.faces}</small>
            <div class="play-dice-values">{values}</div>
            <strong>{subtotal:+d}</strong>
          </div>
        """
    return f"""
      <div class="play-dice-term play-dice-modifier">
        <small>Modifier</small><div class="play-dice-values"><span>{term.value:+d}</span></div>
        <strong>{term.value:+d}</strong>
      </div>
    """


def _dice_payload(roll: DiceRollResult) -> str:
    terms: list[dict[str, object]] = []
    for term in roll.terms:
        if isinstance(term, DiceGroupResult):
            terms.append(
                {
                    "kind": "dice",
                    "sign": term.sign,
                    "faces": term.faces,
                    "results": list(term.results),
                }
            )
        else:
            terms.append({"kind": "modifier", "value": term.value})
    return json.dumps(
        {"expression": roll.expression, "terms": terms, "total": roll.total},
        separators=(",", ":"),
    )


def _session_review_panel() -> str:
    return """
      <section class="play-session-review">
        <div>
          <p class="eyebrow">Session review</p>
          <h2>Review what changed before closing the table.</h2>
        </div>
        <div class="button-row">
          <a class="button secondary" href="/play/ledgers?kind=narrative&amp;scope=session">Narrative</a>
          <a class="button secondary" href="/play/ledgers?kind=clues&amp;scope=session">Leads</a>
          <a class="button secondary" href="/play/ledgers?kind=revelations&amp;scope=session">Revelations</a>
          <a class="button primary" href="/play/ledgers?kind=recap&amp;scope=session">Player recap</a>
        </div>
      </section>
    """


def _history_summary_panel(result: RunDashboardResult) -> str:
    """Render recent canonical developments without duplicating left-rail navigation."""
    records = result.projection.narrative[-6:]
    if not records:
        return """
          <section class="play-utility-card">
            <div class="play-utility-heading"><h2>What happened so far</h2><span>No history yet</span></div>
            <p>No table developments have been recorded.</p>
          </section>
        """
    encounter_index = result.adventure.encounter_index()
    clue_index = result.adventure.clue_index()
    revelation_index = result.adventure.revelation_index()
    reference_index = result.adventure.reference_index()
    labels = {
        "session_started": "Session began",
        "session_ended": "Session ended",
        "encounter_visited": "Entered encounter",
        "clue_spotted": "Lead found",
        "clue_missed": "Lead missed",
        "revelation_established": "Revelation established",
        "revelation_foreclosed": "Revelation foreclosed",
        "revelation_reopened": "Revelation reopened",
        "encounter_unlocked": "Encounter unlocked",
        "visit_note_recorded": "Encounter note",
        "reference_note_recorded": "Reference note",
        "encounter_consequence_recorded": "Encounter note",
        "dice_roll_recorded": "Recorded roll",
    }
    items: list[str] = []
    for record in records:
        subject = record.text
        if record.encounter_id:
            subject = encounter_index[record.encounter_id].title
        elif record.clue_id:
            subject = clue_index[record.clue_id].title
        elif record.revelation_id:
            subject = revelation_index[record.revelation_id].title
        elif record.reference_id:
            subject = reference_index[record.reference_id].title
        items.append(
            f"<li><span>{escape_html(labels.get(record.kind, record.kind))}</span>"
            f"<strong>{escape_html(subject or 'Recorded')}</strong></li>"
        )
    return f"""
      <section class="play-utility-card">
        <div class="play-utility-heading"><h2>What happened so far</h2><span>Latest {len(records)}</span></div>
        <ol class="play-activity-list">{"".join(items)}</ol>
      </section>
    """


def _keyboard_panel() -> str:
    return """
      <details class="play-utility-card play-shortcuts">
        <summary>Keyboard shortcuts</summary>
        <dl>
          <div><dt>/</dt><dd>Search</dd></div>
          <div><dt>P</dt><dd>Pin focused encounter</dd></div>
          <div><dt>G</dt><dd>Focus current visit</dd></div>
          <div><dt>[ / ]</dt><dd>Previous / next route visit</dd></div>
          <div><dt>Esc</dt><dd>Close drawer or clear search</dd></div>
        </dl>
      </details>
    """
