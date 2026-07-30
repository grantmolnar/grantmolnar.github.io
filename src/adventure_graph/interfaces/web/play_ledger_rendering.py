"""HTML rendering for operational Play-mode ledgers and recaps."""

from __future__ import annotations

from collections import Counter
from urllib.parse import urlencode

from adventure_graph.application.play_ledgers import (
    ClueLedgerEntry,
    EncounterLedgerEntry,
    NarrativeLedgerEntry,
    PlayLedgerKind,
    PlayLedgerScope,
    PlayLedgersResult,
    RevelationLedgerEntry,
)
from adventure_graph.application.run_workspace import RunDashboardResult
from adventure_graph.interfaces.web.page_rendering import escape_html
from adventure_graph.interfaces.web.play_rendering import render_play_workspace_page


def _ledger_titles() -> tuple[tuple[PlayLedgerKind, str], ...]:
    return (
        ("encounters", "Encounters"),
        ("clues", "Leads"),
        ("revelations", "Revelations"),
        ("narrative", "Narrative"),
        ("recap", "Player recap"),
    )


def render_play_ledgers(
    result: PlayLedgersResult,
    *,
    selected_kind: PlayLedgerKind,
    dashboard: RunDashboardResult,
    csrf_token: str,
) -> str:
    """Render one scoped operational ledger with stable Play navigation."""
    document = result.document_index()[selected_kind]
    body_class = "play-ledger-body player-safe" if selected_kind == "recap" else "play-ledger-body"
    current_kind = "history" if selected_kind in {"narrative", "recap"} else "trackers"
    workspace_label = "History" if current_kind == "history" else "Trackers"
    workspace_copy = (
        "A chronological record of what happened at the table."
        if selected_kind == "narrative"
        else (
            "A spoiler-safe recap suitable for sharing with players."
            if selected_kind == "recap"
            else "Current encounter, lead, and revelation status across the playthrough."
        )
    )
    body = f"""
      <div class="play-ledger-page" id="play-ledger-content">
        <div class="play-ledger-heading no-print">
          <div>
            <p class="eyebrow">{workspace_label}</p>
            <h1>{escape_html(document.title)}</h1>
            <p>{workspace_copy}</p>
          </div>
          <div class="button-row">
            <button class="button secondary" type="button" data-print-page>Print</button>
            <a class="button secondary" href="{_download_url(selected_kind, result)}">Download Markdown</a>
            <a class="button primary" href="/play">Return to Play</a>
          </div>
        </div>
        {_scope_switch(result, selected_kind)}
        {_ledger_tabs(result, selected_kind)}
        {_scope_warning(result)}
        {_summary_strip(result, selected_kind)}
        <section class="play-ledger-paper" aria-label="{escape_html(document.title)}">
          <header class="play-ledger-print-header">
            <p>{escape_html(result.adventure.title)}</p>
            <h1>{escape_html(document.title)}</h1>
            <span>{escape_html(result.scope_label)}</span>
          </header>
          {_ledger_content(result, selected_kind)}
        </section>
      </div>
    """
    return render_play_workspace_page(
        dashboard,
        csrf_token=csrf_token,
        title=f"{document.title} — {result.adventure.title}",
        current_kind=current_kind,
        body=body,
        body_class=body_class,
        player_safe=selected_kind == "recap",
    )


def _scope_switch(result: PlayLedgersResult, selected_kind: PlayLedgerKind) -> str:
    playthrough = _ledger_url(selected_kind, "playthrough")
    session = _ledger_url(selected_kind, "session")
    session_label = "Latest session"
    if result.selected_session is not None:
        session_label = (
            result.selected_session.title or f"Session {result.selected_session.session_number}"
        )
    session_control = (
        f'<a href="{session}" aria-current="page">{escape_html(session_label)}</a>'
        if result.is_session_scope
        else (
            f'<a href="{session}">{escape_html(session_label)}</a>'
            if result.available_session_count
            else '<span aria-disabled="true">No explicit sessions</span>'
        )
    )
    playthrough_current = ' aria-current="page"' if not result.is_session_scope else ""
    return f"""
      <nav class="play-ledger-scope no-print" aria-label="Ledger scope">
        <span>Scope</span>
        <a href="{playthrough}"{playthrough_current}>Whole playthrough</a>
        {session_control}
      </nav>
    """


def _ledger_tabs(result: PlayLedgersResult, selected_kind: PlayLedgerKind) -> str:
    links: list[str] = []
    for kind, title in _ledger_titles():
        current = ' aria-current="page"' if kind == selected_kind else ""
        links.append(
            f'<a href="{_ledger_url(kind, result.requested_scope)}"{current}>'
            f"{escape_html(title)}</a>"
        )
    return (
        '<nav class="play-ledger-tabs no-print" aria-label="Operational ledgers">'
        + "".join(links)
        + "</nav>"
    )


def _scope_warning(result: PlayLedgersResult) -> str:
    if result.requested_scope != "session" or result.selected_session is not None:
        return ""
    return """
      <aside class="play-ledger-warning">
        <strong>No explicit session is available.</strong>
        <p>The session scope is empty. Use the whole-playthrough scope for unsegmented legacy history.</p>
      </aside>
    """


def _summary_strip(result: PlayLedgersResult, selected_kind: PlayLedgerKind) -> str:
    if selected_kind == "encounters":
        counts = Counter(entry.status for entry in result.encounters)
        values = (
            ("Current", counts["current"]),
            ("Visited", counts["visited"]),
            ("Available", counts["available"]),
            ("Locked", counts["locked"]),
        )
    elif selected_kind == "clues":
        counts = Counter(entry.status for entry in result.clues)
        values = (
            ("Found", counts["found"]),
            ("Missed but open", counts["missed"]),
            ("Unresolved", counts["unresolved"]),
            ("In scope", len(result.clues)),
        )
    elif selected_kind == "revelations":
        counts = Counter(entry.status for entry in result.revelations)
        values = (
            ("Established", counts["established"]),
            ("Supported", counts["supported"]),
            ("Unsupported", counts["unsupported"]),
            ("Foreclosed", counts["foreclosed"]),
        )
    elif selected_kind == "narrative":
        values = (
            ("Events", len(result.narrative)),
            (
                "Sessions",
                len({item.session_number for item in result.narrative if item.session_number}),
            ),
            ("Visits", sum(item.kind == "encounter_visited" for item in result.narrative)),
            ("Discoveries", sum(item.kind == "clue_spotted" for item in result.narrative)),
        )
    else:
        values = (
            ("Safe events", len(result.player_recap)),
            ("Visits", sum(item.kind == "encounter_visited" for item in result.player_recap)),
            ("Leads", sum(item.kind == "clue_spotted" for item in result.player_recap)),
            (
                "Revelations",
                sum(item.kind == "revelation_established" for item in result.player_recap),
            ),
        )
    cards = "".join(
        f"<div><strong>{value}</strong><span>{escape_html(label)}</span></div>"
        for label, value in values
    )
    return f'<section class="play-ledger-summary no-print">{cards}</section>'


def _ledger_content(result: PlayLedgersResult, kind: PlayLedgerKind) -> str:
    if kind == "encounters":
        return _encounter_ledger(result.encounters)
    if kind == "clues":
        return _clue_ledger(result.clues, result.requested_scope)
    if kind == "revelations":
        return _revelation_ledger(result.revelations)
    if kind == "narrative":
        return _narrative_ledger(result.narrative, player_safe=False)
    return _narrative_ledger(result.player_recap, player_safe=True)


def _encounter_ledger(entries: tuple[EncounterLedgerEntry, ...]) -> str:
    if not entries:
        return _empty("No encounters are in this scope.")
    cards = "".join(
        f"""
        <article class="play-ledger-card status-{escape_html(entry.status)}">
          <header><span>{escape_html(entry.status)}</span><strong>{"Necessary" if entry.encounter.required else "Optional"}</strong></header>
          <h2>{escape_html(entry.encounter.title)}</h2>
          <p>{escape_html(entry.encounter.summary)}</p>
          <dl>
            <div><dt>Visits in scope</dt><dd>{_numbers(entry.visit_numbers_in_scope)}</dd></div>
            <div><dt>Visits overall</dt><dd>{_numbers(entry.visit_numbers)}</dd></div>
            <div><dt>Unresolved leads</dt><dd>{entry.unresolved_clue_count}</dd></div>
          </dl>
          {_consequences(entry.consequence_texts_in_scope)}
          <a class="no-print" href="/play?{urlencode({"encounter": entry.encounter.id})}">Focus in Play</a>
        </article>
        """
        for entry in entries
    )
    return f'<div class="play-ledger-grid">{cards}</div>'


def _clue_ledger(entries: tuple[ClueLedgerEntry, ...], scope: PlayLedgerScope) -> str:
    if not entries:
        return _empty("No leads are in this scope.")
    rows = "".join(
        f"""
        <article class="play-ledger-card status-{escape_html(entry.status)}">
          <header><span>{escape_html(entry.status)}</span><strong>{escape_html(entry.clue.discovery)}</strong></header>
          <h2>{escape_html(entry.clue.title)}</h2>
          <p>{escape_html(entry.clue.description or "No expanded description.")}</p>
          <dl>
            <div><dt>Source</dt><dd>{escape_html(entry.source_encounter.title)}</dd></div>
            <div><dt>Supports</dt><dd><a href="{_ledger_url("revelations", scope)}#revelation-{escape_html(entry.revelation.id)}">{escape_html(entry.revelation.title)}</a></dd></div>
            <div><dt>Found</dt><dd>{"Visit " + str(entry.spotted_visit_number) if entry.spotted_visit_number else "Not found"}</dd></div>
            <div><dt>Missed</dt><dd>{_numbers(entry.missed_visit_numbers)}</dd></div>
          </dl>
          {_scope_activity(entry)}
          <a class="no-print" href="/play?{urlencode({"encounter": entry.source_encounter.id})}#clue-{escape_html(entry.clue.id)}">Open source encounter</a>
        </article>
        """
        for entry in entries
    )
    return f'<div class="play-ledger-grid">{rows}</div>'


def _revelation_ledger(entries: tuple[RevelationLedgerEntry, ...]) -> str:
    if not entries:
        return _empty("No revelations are in this scope.")
    cards = "".join(
        f"""
        <article id="revelation-{escape_html(entry.revelation.id)}" class="play-ledger-card status-{escape_html(entry.status)}">
          <header><span>{escape_html(entry.status)}</span><strong>{"Necessary" if entry.revelation.required else "Optional"}</strong></header>
          <h2>{escape_html(entry.revelation.title)}</h2>
          <p>{escape_html(entry.revelation.description)}</p>
          <dl>
            <div><dt>Found support</dt><dd>{len(entry.spotted_clues)} of {len(entry.supporting_clues)}</dd></div>
            <div><dt>Found this scope</dt><dd>{len(entry.spotted_clues_in_scope)}</dd></div>
            <div><dt>Destination</dt><dd>{escape_html(entry.destination_encounter.title if entry.destination_encounter else "Conclusion only")}</dd></div>
          </dl>
          {_judgment_notes(entry)}
        </article>
        """
        for entry in entries
    )
    return f'<div class="play-ledger-grid">{cards}</div>'


def _narrative_ledger(entries: tuple[NarrativeLedgerEntry, ...], *, player_safe: bool) -> str:
    if not entries:
        return _empty("No narrative events are in this scope.")
    preamble = (
        """
        <aside class="player-safe-banner">
          <strong>Player-safe projection</strong>
          <p>This view contains only visited locations, discovered leads, and established revelations. GM notes, misses, hidden judgments, unlocks, consequences, and rolls are absent by construction.</p>
        </aside>
        """
        if player_safe
        else ""
    )
    items = "".join(
        f"""
        <li class="narrative-{escape_html(entry.kind)}">
          <span>{_narrative_marker(entry)}</span>
          <div><h2>{escape_html(entry.title)}</h2>{f"<p>{escape_html(entry.detail)}</p>" if entry.detail else ""}</div>
        </li>
        """
        for entry in entries
    )
    return f'{preamble}<ol class="play-narrative-list">{items}</ol>'


def _scope_activity(entry: ClueLedgerEntry) -> str:
    messages: list[str] = []
    if entry.spotted_in_scope:
        messages.append("Found in this scope")
    if entry.missed_visit_numbers_in_scope:
        messages.append(
            f"Missed on visit {_numbers(entry.missed_visit_numbers_in_scope)} in this scope"
        )
    if entry.source_visited_in_scope and not messages:
        messages.append("Source visited in this scope; lead remains unresolved")
    if not messages:
        return ""
    return (
        '<p class="play-ledger-activity">'
        + " · ".join(escape_html(item) for item in messages)
        + "</p>"
    )


def _judgment_notes(entry: RevelationLedgerEntry) -> str:
    notes: list[str] = []
    if entry.establishment_note:
        notes.append(f"Established: {entry.establishment_note}")
    if entry.foreclosure_reason:
        notes.append(f"Foreclosed: {entry.foreclosure_reason}")
    if not notes:
        return ""
    return (
        '<ul class="play-ledger-notes">'
        + "".join(f"<li>{escape_html(note)}</li>" for note in notes)
        + "</ul>"
    )


def _consequences(values: tuple[str, ...]) -> str:
    if not values:
        return ""
    return (
        '<div class="play-ledger-consequences"><strong>Consequences in scope</strong><ul>'
        + "".join(f"<li>{escape_html(value)}</li>" for value in values)
        + "</ul></div>"
    )


def _narrative_marker(entry: NarrativeLedgerEntry) -> str:
    if entry.visit_number is not None:
        return f"Visit {entry.visit_number}"
    if entry.session_number is not None:
        return f"Session {entry.session_number}"
    return f"Event {entry.sequence}"


def _numbers(values: tuple[int, ...]) -> str:
    return ", ".join(str(value) for value in values) or "None"


def _empty(message: str) -> str:
    return f'<p class="play-ledger-empty">{escape_html(message)}</p>'


def _ledger_url(kind: PlayLedgerKind, scope: str) -> str:
    return "/play/ledgers?" + urlencode({"kind": kind, "scope": scope})


def _download_url(kind: PlayLedgerKind, result: PlayLedgersResult) -> str:
    return "/play/ledgers/download?" + urlencode({"kind": kind, "scope": result.requested_scope})
