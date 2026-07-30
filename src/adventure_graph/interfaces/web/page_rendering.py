"""Shared HTML page shell and presentation primitives for the local web adapter."""

from __future__ import annotations

import html
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import quote, urlencode

from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
    Encounter,
    Reference,
    Revelation,
)
from adventure_graph.domain.validation_models import (
    ValidationIssue,
    ValidationReport,
)
from adventure_graph.interfaces.web.view_models import PageNotice


def render_error(status: int, heading: str, message: str, project_label: str) -> str:
    """Render a contained local-application error without exposing a traceback."""
    del project_label
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{status} — Adventure Graph</title><script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css"></head>
<body><header class="topbar"><a class="brand" href="/"><span class="brand-mark">AG</span><span class="brand-copy"><strong>Adventure Graph</strong><span>Local GM workspace</span></span></a><nav class="topbar-actions" aria-label="Workspace"><a href="/help">Help</a></nav>{render_theme_toggle()}</header>
<main class="error-page"><section class="error-panel"><p class="eyebrow">Error {status}</p><h1>{escape_html(heading)}</h1><p>{escape_html(message)}</p><p><a href="/">Return to the adventure overview</a></p></section></main></body></html>"""


def render_page(
    *,
    title: str,
    project_label: str,
    adventure: Adventure,
    report: ValidationReport,
    current_kind: str,
    current_id: str | None,
    body: str,
    related_issues: tuple[ValidationIssue, ...],
    revision: str,
    editing: bool = False,
    clear_draft_key: str | None = None,
    body_class: str = "",
) -> str:
    del project_label, revision
    status_label = "Structurally valid" if report.is_valid else "Needs attention"
    body_attributes: list[str] = []
    if body_class:
        body_attributes.append(f'class="{escape_html(body_class)}"')
    if clear_draft_key:
        body_attributes.append(f'data-clear-draft-key="{escape_html(clear_draft_key)}"')
    play_context = current_kind in {"run", "journal", "archives", "history", "trackers"}
    if current_kind == "run":
        mode = "Recording"
    elif play_context:
        mode = "Play"
    else:
        mode = "Editing" if editing else "Authoring"
    topbar = (
        render_play_context_topbar(adventure.title)
        if play_context
        else f"""
  <header class="topbar">
    <a class="brand" href="/"><span class="brand-mark">AG</span><span class="brand-copy"><strong>Adventure Graph</strong><span>Local authoring workspace</span></span></a>
    <nav class="context-switch" aria-label="Adventure context"><a href="/" {current_page_attribute(True)}>Author</a><a href="/play">Play</a></nav>
    <span class="mode-pill">{mode}</span>
    <nav class="topbar-actions" aria-label="Workspace"><a href="/adventures">Adventures</a><a href="/settings">Settings</a><a href="/help">Help</a></nav>
    {render_theme_toggle()}
    <a class="topbar-project" href="/" title="{escape_html(adventure.title)}"><span>Current adventure</span><strong>{escape_html(adventure.title)}</strong></a>
  </header>
        """
    )
    if play_context:
        body_attributes.append(f'data-play-adventure-id="{escape_html(adventure.id)}"')
        play_focus_id = adventure.encounters[0].id
        navigation = render_play_navigation(current_kind) + render_play_authored_search(
            adventure, play_focus_id
        )
        right_rail = (
            render_play_pin_panel()
            + render_play_recent_focus_panel()
            + _validation_summary(report, status_label)
            + _related_issues(related_issues, adventure)
        )
        trailing = render_play_encounter_records(
            adventure.encounters
        ) + render_play_reference_records(adventure.references, play_focus_id)
    else:
        navigation = _navigation(adventure, current_kind, current_id)
        right_rail = _validation_summary(report, status_label) + _related_issues(
            related_issues, adventure
        )
        trailing = ""
    body_attribute = f" {' '.join(body_attributes)}" if body_attributes else ""
    workspace_class = "workspace play-secondary-workspace" if play_context else "workspace"
    rail_label = "Play navigation and authored material" if play_context else "Adventure navigation"
    right_rail_label = "Play context" if play_context else "Project status"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light dark"><title>{escape_html(title)}</title>
  <script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css">
</head>
<body{body_attribute}>
  <a class="skip-link" href="#main-content">Skip to content</a>
  {topbar}
  <div class="{workspace_class}">
    <aside class="left-rail" aria-label="{rail_label}"><div class="rail-inner">{navigation}</div></aside>
    <main class="main" id="main-content"><div class="main-inner">{body}</div></main>
    <aside class="right-rail" aria-label="{right_rail_label}"><div class="rail-inner">
      {right_rail}
    </div></aside>
  </div>
  {trailing}
</body></html>"""


def render_play_context_topbar(adventure_title: str) -> str:
    """Render global mode and application navigation above Play workspaces."""
    return f"""
  <header class="topbar play-topbar">
    <a class="brand" href="/play">
      <span class="brand-mark">AG</span>
      <span class="brand-copy"><strong>Adventure Graph</strong><span>Local GM workspace</span></span>
    </a>
    <nav class="context-switch" aria-label="Adventure context">
      <a href="/">Author</a><a href="/play" aria-current="page">Play</a>
    </nav>
    <nav class="topbar-actions play-topbar-actions" aria-label="Application">
      <a href="/adventures">Adventures</a><a href="/settings">Settings</a><a href="/help">Help</a>
    </nav>
    {render_theme_toggle()}
    <a class="topbar-project" href="/play" title="{escape_html(adventure_title)}">
      <span>Current adventure</span><strong>{escape_html(adventure_title)}</strong>
    </a>
  </header>
    """


def render_theme_toggle() -> str:
    """Render the browser-local appearance control shared by every web shell."""
    return (
        '<button class="theme-toggle" type="button" data-theme-toggle '
        'aria-pressed="false" title="Switch to dark mode">'
        '<span class="theme-toggle-icon" aria-hidden="true">◐</span>'
        "<span data-theme-label>Dark mode</span></button>"
    )


def _navigation(adventure: Adventure, current_kind: str, current_id: str | None) -> str:
    return f"""
      <a class="project-home" href="/" {current_page_attribute(current_kind == "overview")}><span>Adventure</span><strong>{escape_html(adventure.title)}</strong></a>
      <a class="workspace-link" href="/structure" {current_page_attribute(current_kind == "structure")}><span>Structure</span><strong>Graph and coverage</strong></a>
      <a class="workspace-link" href="/references" {current_page_attribute(current_kind in {"references", "reference"})}><span>Reference library</span><strong>Recurring adventure subjects</strong></a>
      <a class="workspace-link" href="/reports" {current_page_attribute(current_kind == "reports")}><span>Adventure packet</span><strong>Authored reference documents</strong></a>
      <div class="nav-filter" data-navigation-filter-shell>
        <label for="adventure-navigation-filter">Find authored material</label>
        <input id="adventure-navigation-filter" type="search" placeholder="Filter titles" autocomplete="off" data-navigation-filter>
        <p class="nav-filter-status" data-navigation-filter-status aria-live="polite"></p>
      </div>
      {_nav_group("Encounters", "encounter", adventure.encounters, current_kind, current_id, add_url="/encounters/new")}
      {_nav_group("Revelations", "revelation", adventure.revelations, current_kind, current_id, add_url="/revelations/new")}
      {_nav_group("Leads", "clue", adventure.clues, current_kind, current_id, add_url="/clues/new")}
      {_nav_group("References", "reference", adventure.references, current_kind, current_id, add_url="/references/new")}
    """


def render_play_navigation(current_kind: str) -> str:
    """Render table-local workspaces without duplicating global top-bar links."""
    links = (
        ("play", "/play", "Table", "Encounter reference and notes"),
        (
            "history",
            "/play/ledgers?kind=narrative&scope=playthrough",
            "History",
            "What happened in chronological order",
        ),
        (
            "trackers",
            "/play/ledgers?kind=encounters&scope=playthrough",
            "Trackers",
            "Encounters, leads, and revelations",
        ),
        ("journal", "/journal", "Correct history", "Audit trail and corrections"),
        ("run", "/run", "Recovery console", "Exceptional recording and correction"),
        ("archives", "/archives", "Archives", "Transfer, snapshots, and restore"),
    )
    rendered = "".join(
        f'<a class="workspace-link" href="{href}" '
        f"{current_page_attribute(current_kind == key)}><span>{label}</span>"
        f"<strong>{description}</strong></a>"
        for key, href, label, description in links
    )
    return f"""
      <section class="play-workspace-switcher">
        <span class="play-rail-heading">Play workspaces</span>
        <nav class="play-workspace-navigation" aria-label="Play navigation">{rendered}</nav>
      </section>
      <nav class="play-mobile-application-links" aria-label="Application">
        <a href="/adventures">Adventures</a><a href="/settings">Settings</a><a href="/help">Help</a>
      </nav>
    """


def render_play_authored_search(adventure: Adventure, focus_encounter_id: str) -> str:
    """Render one left-rail search over all authored adventure material."""
    entries: list[str] = []
    for encounter in adventure.encounters:
        search_text = " ".join(
            (
                encounter.title,
                encounter.summary,
                encounter.opening_view,
                encounter.content,
                *encounter.tags,
            )
        )
        entries.append(
            _play_search_entry(
                "Encounter", encounter.title, encounter.summary, encounter.id, search_text
            )
        )
    encounter_index = adventure.encounter_index()
    for clue in adventure.clues:
        source = encounter_index[clue.source_encounter_id]
        search_text = " ".join((clue.title, clue.description, clue.discovery, source.title))
        entries.append(
            _play_search_entry(
                "Lead",
                clue.title,
                f"At {source.title} · {clue.description or clue.discovery}",
                source.id,
                search_text,
                fragment=f"clue-{clue.id}",
            )
        )
    clue_sources: dict[str, str] = {}
    for clue in adventure.clues:
        clue_sources.setdefault(clue.revelation_id, clue.source_encounter_id)
    for revelation in adventure.revelations:
        target = revelation.unlocks_encounter_id or clue_sources.get(revelation.id)
        search_text = " ".join((revelation.title, revelation.description))
        entries.append(
            _play_search_entry(
                "Revelation",
                revelation.title,
                revelation.description,
                target,
                search_text,
                fallback_href=(
                    "/play/ledgers?kind=revelations&scope=playthrough"
                    f"#revelation-{quote(revelation.id, safe='')}"
                ),
            )
        )
    contexts: defaultdict[str, list[str]] = defaultdict(list)
    for encounter in adventure.encounters:
        for link in encounter.reference_links:
            if link.context:
                contexts[link.reference_id].append(link.context)
    for reference in adventure.references:
        search_text = " ".join(
            (
                reference.title,
                *reference.aliases,
                reference.summary,
                reference.content,
                *reference.tags,
                *contexts[reference.id],
            )
        )
        entries.append(
            _play_search_entry(
                reference.kind.title(),
                reference.title,
                reference.summary or "Persistent authored reference",
                focus_encounter_id,
                search_text,
                reference_id=reference.id,
            )
        )
    return f"""
      <section class="play-utility-card play-search-card play-left-search">
        <div class="play-utility-heading"><h2>Find authored material</h2><span>/</span></div>
        <label class="sr-only" for="play-search">Search encounters, leads, revelations, and references</label>
        <input id="play-search" type="search" autocomplete="off"
               placeholder="Search titles and prose" data-play-search>
        <p class="play-search-status" role="status" aria-live="polite" aria-atomic="true"
           data-play-search-status>Type to search the adventure.</p>
        <div class="play-search-results" aria-label="Authored material search results"
             data-play-search-results>{"".join(entries)}</div>
      </section>
    """


def _play_search_entry(
    kind: str,
    title: str,
    description: str,
    encounter_id: str | None,
    search_text: str,
    *,
    fragment: str = "",
    fallback_href: str = "",
    reference_id: str | None = None,
) -> str:
    suffix = f"#{quote(fragment, safe='')}" if fragment else ""
    if reference_id is not None and encounter_id is not None:
        href = f"/play?{urlencode({'encounter': encounter_id, 'reference': reference_id})}"
    else:
        href = (
            f"/play?encounter={quote(encounter_id, safe='')}{suffix}"
            if encounter_id is not None
            else fallback_href
        )
    return f"""
      <a href="{escape_html(href)}" class="play-search-result"
         data-play-search-entry data-search-text="{escape_html(search_text.casefold())}" hidden>
        <span>{escape_html(kind)}</span><strong>{escape_html(title)}</strong>
        <small>{escape_html(description)}</small>
      </a>
    """


def render_play_pin_panel() -> str:
    """Render the browser-local pin shelf, hidden until it contains a bookmark."""
    return """
      <section class="play-utility-card" data-play-pin-panel hidden>
        <div class="play-utility-heading">
          <h2>Pinned for reference</h2><span data-play-pin-count>0</span>
        </div>
        <p>Bookmarks stored in this browser. Pinning never records a visit.</p>
        <div class="play-pin-list" data-play-pin-list></div>
      </section>
    """


def render_play_recent_focus_panel() -> str:
    """Render browser-local encounter shortcuts in the contextual rail."""
    return """
      <section class="play-utility-card" data-play-recent-panel hidden>
        <div class="play-utility-heading"><h2>Recent focus</h2><span>Browser-local</span></div>
        <div class="play-recent-list" data-play-recent-list></div>
      </section>
    """


def render_play_encounter_records(encounters: tuple[Encounter, ...]) -> str:
    """Expose authored encounter labels to browser-local Play utilities."""
    records = "".join(
        f'<span data-play-item-record data-play-kind="encounter" data-play-id="{escape_html(encounter.id)}" '
        f'data-play-encounter-record data-encounter-id="{escape_html(encounter.id)}" '
        f'data-title="{escape_html(encounter.title)}" data-summary="{escape_html(encounter.summary)}" '
        f'data-href="/play?encounter={quote(encounter.id, safe="")}"></span>'
        for encounter in encounters
    )
    return f'<div class="play-encounter-records" hidden>{records}</div>'


def render_play_reference_records(
    references: tuple[Reference, ...],
    focus_encounter_id: str,
) -> str:
    """Expose authored references to browser-local typed pins without persisting state."""
    records = "".join(
        f'<span data-play-item-record data-play-kind="reference" data-play-id="{escape_html(reference.id)}" '
        f'data-title="{escape_html(reference.title)}" data-summary="{escape_html(reference.summary)}" '
        f'data-href="/play?{escape_html(urlencode({"encounter": focus_encounter_id, "reference": reference.id}))}"></span>'
        for reference in references
    )
    return f'<div class="play-reference-records" hidden>{records}</div>'


def _nav_group(
    heading: str,
    kind: str,
    entities: Iterable[Encounter | Revelation | Clue | Reference],
    current_kind: str,
    current_id: str | None,
    *,
    add_url: str | None = None,
) -> str:
    values = tuple(entities)
    links = "".join(
        f'<a class="entity-link" href="{entity_url(kind, entity.id)}" data-navigation-item data-navigation-title="{escape_html(_navigation_search_text(entity))}" {current_page_attribute(current_kind == kind and current_id == entity.id)}><span class="title">{escape_html(entity.title)}</span></a>'
        for entity in values
    )
    add = f'<a class="nav-add" href="{add_url}">Add</a>' if add_url else ""
    disclosure_id = f"author-navigation-{kind}"
    return f"""<section class="nav-group ui-disclosure" data-navigation-group data-ui-disclosure
      data-disclosure-default="collapsed"
      data-disclosure-storage-key="adventure-graph:author-navigation:{kind}">
      <div class="nav-heading ui-disclosure-header">
        <button class="nav-disclosure-toggle ui-disclosure-toggle" type="button"
                aria-controls="{disclosure_id}" aria-expanded="false" data-ui-disclosure-toggle>
          <span class="nav-heading-title">{heading}</span>
          <span class="nav-heading-count">{len(values)}</span>
          <span class="ui-disclosure-indicator" aria-hidden="true"></span>
        </button>
        {add}
      </div>
      <div class="entity-list ui-disclosure-content" id="{disclosure_id}"
           data-ui-disclosure-content hidden>
        {links}
        <p class="nav-group-empty" data-navigation-group-empty hidden>No matching {heading.lower()}.</p>
      </div>
    </section>"""


def _navigation_search_text(entity: Encounter | Revelation | Clue | Reference) -> str:
    if isinstance(entity, Reference):
        return " ".join(
            (entity.title, *entity.aliases, entity.summary, entity.content, *entity.tags)
        ).casefold()
    return entity.title.casefold()


def _validation_summary(report: ValidationReport, status_label: str) -> str:
    error_count = sum(issue.severity == "error" for issue in report.issues)
    warning_count = sum(issue.severity == "warning" for issue in report.issues)
    connectivity = "n/a" if report.edge_connectivity is None else str(report.edge_connectivity)
    error_class = " error" if not report.is_valid else ""
    return f'<section class="rail-card"><h2>Project status</h2><div class="status-line"><span class="status-dot{error_class}"></span>{escape_html(status_label)}</div><div class="stat-list"><div class="stat-row"><span>Errors</span><strong>{error_count}</strong></div><div class="stat-row"><span>Warnings</span><strong>{warning_count}</strong></div><div class="stat-row"><span>Structural resilience</span><strong>{connectivity}</strong></div></div></section>'


def _related_issues(issues: tuple[ValidationIssue, ...], adventure: Adventure) -> str:
    content = (
        '<p class="muted-note">No validation findings are attached to this view.</p>'
        if not issues
        else f'<div class="issue-list">{"".join(render_issue(issue, adventure) for issue in issues)}</div>'
    )
    return f'<section class="rail-card"><h2>Related validation</h2>{content}</section>'


def render_notice(notice: PageNotice | None) -> str:
    if notice is None:
        return ""
    role = "alert" if notice.level == "error" else "status"
    heading = notice.heading
    message = notice.message
    return (
        f'<section class="notice {escape_html(notice.level)}" role="{role}" '
        'aria-atomic="true">'
        f"<strong>{escape_html(heading)}</strong>"
        f"<p>{escape_html(message)}</p></section>"
    )


def render_issue(issue: ValidationIssue, adventure: Adventure | None = None) -> str:
    """Render a validation issue in GM-facing language without exposing diagnostic codes."""
    message = humanize_authored_identifiers(issue.message, adventure)
    repair_text = humanize_authored_identifiers(issue.repair, adventure)
    repair = f'<p class="repair">{escape_html(repair_text)}</p>' if repair_text else ""
    heading = _issue_heading(issue.code)
    severity = "Warning" if issue.severity == "warning" else "Error"
    return f'<article class="issue {escape_html(issue.severity)}"><span class="issue-severity">{severity}</span><strong>{escape_html(heading)}</strong><p>{escape_html(message)}</p>{repair}</article>'


def _issue_heading(code: str) -> str:
    headings = {
        "clue-source-missing": "Lead source is missing",
        "clue-revelation-missing": "Lead revelation is missing",
        "revelation-encounter-missing": "Revelation destination is missing",
        "optional-revelation-unclued": "Optional revelation has no leads",
        "revelation-insufficient-clues": "Revelation needs more leads",
        "revelation-insufficient-sources": "Revelation needs more independent sources",
        "optional-encounter-unclued": "Optional encounter has no leads pointing to it",
        "encounter-insufficient-incoming-clues": "Encounter needs more leads pointing to it",
        "encounter-insufficient-incoming-sources": "Encounter needs more independent approaches",
        "encounter-insufficient-outgoing-clues": "Encounter needs more leads pointing onward",
        "encounter-insufficient-targets": "Encounter needs more distinct destinations",
        "encounter-unreachable": "Necessary encounter is unreachable",
        "optional-encounter-unreachable": "Optional encounter is unreachable",
        "graph-edge-connectivity-impossible": "Configured structural resilience is impossible",
        "graph-edge-connectivity-low": "Structural resilience is below the configured minimum",
        "adventure-premise-empty": "Premise is empty",
        "adventure-explanation-empty": "Explanation is empty",
        "start-encounter-missing": "Start encounter is missing",
        "multiple-start-encounters": "Adventure has multiple start encounters",
        "multiple-end-encounters": "Adventure has multiple end encounters",
        "duplicate-encounter-id": "Encounter titles produce duplicate identities",
        "duplicate-revelation-id": "Revelation titles produce duplicate identities",
        "duplicate-clue-id": "Lead titles produce duplicate identities",
    }
    return headings.get(code, code.replace("-", " ").capitalize())


def humanize_authored_identifiers(text: str, adventure: Adventure | None) -> str:
    """Replace serialized authored identifiers with their display titles."""
    if adventure is None or not text:
        return text
    entities = (*adventure.encounters, *adventure.revelations, *adventure.clues)
    for entity in sorted(entities, key=lambda item: len(item.id), reverse=True):
        text = text.replace(repr(entity.id), repr(entity.title))
        text = text.replace(f"`{entity.id}`", f"`{entity.title}`")
    return text


@dataclass(frozen=True, slots=True)
class MetricLink:
    """One explicitly structured link permitted inside a metric value."""

    text: str
    href: str


def render_metrics(items: Iterable[tuple[str | MetricLink, str]]) -> str:
    """Render metric values as escaped text unless a link is explicitly structured."""
    cards = "".join(
        f'<div class="metric"><strong>{_render_metric_value(value)}</strong>'
        f"<span>{escape_html(label)}</span></div>"
        for value, label in items
    )
    return f'<div class="metrics">{cards}</div>'


def _render_metric_value(value: str | MetricLink) -> str:
    if isinstance(value, MetricLink):
        return f'<a href="{escape_html(value.href)}">{escape_html(value.text)}</a>'
    return escape_html(value)


def render_badges(labels: Iterable[str]) -> str:
    values = tuple(label for label in labels if label)
    if not values:
        return ""
    badges = "".join(f'<span class="badge">{escape_html(label)}</span>' for label in values)
    return f'<div class="badges">{badges}</div>'


def render_encounter_card(encounter: Encounter) -> str:
    tags = ", ".join(encounter.tags) if encounter.tags else "No tags"
    position = "Entry" if encounter.start else "Terminal" if encounter.end else "Encounter"
    role = f"{position} · {'Necessary' if encounter.required else 'Optional'}"
    return f'<a class="card" href="{entity_url("encounter", encounter.id)}"><span class="card-kicker">{role}</span><h3>{escape_html(encounter.title)}</h3><p>{escape_html(encounter.summary)}</p><div class="card-meta">{escape_html(tags)}</div></a>'


def render_revelation_card(revelation: Revelation, adventure: Adventure) -> str:
    destination = (
        adventure.encounter_index()[revelation.unlocks_encounter_id].title
        if revelation.unlocks_encounter_id is not None
        else "Conclusion only"
    )
    role = "Necessary" if revelation.required else "Optional"
    return f'<a class="card" href="{entity_url("revelation", revelation.id)}"><span class="card-kicker">{role}</span><h3>{escape_html(revelation.title)}</h3><p>{escape_html(revelation.description)}</p><div class="card-meta">Unlocks: {escape_html(destination)}</div></a>'


def render_clue_card(clue: Clue, adventure: Adventure, *, include_source: bool) -> str:
    revelation = adventure.revelation_index()[clue.revelation_id]
    source = adventure.encounter_index()[clue.source_encounter_id]
    meta = f"From {source.title} · " if include_source else ""
    meta += f"Supports {revelation.title}"
    description = escape_html(clue.description) if clue.description else "No expanded description."
    return f'<a class="relationship-card" href="{entity_url("clue", clue.id)}"><span class="card-kicker">{escape_html(clue.discovery)}</span><h3>{escape_html(clue.title)}</h3><p>{description}</p><div class="card-meta">{escape_html(meta)}</div></a>'


def render_empty_card(message: str) -> str:
    return f'<div class="card"><p class="empty-copy">{escape_html(message)}</p></div>'


def render_pathway_step(label: str, title: str, kind: str | None, identifier: str | None) -> str:
    content = (
        f'<a href="{entity_url(kind, identifier)}">{escape_html(title)}</a>'
        if kind is not None and identifier is not None
        else f"<strong>{escape_html(title)}</strong>"
    )
    return f'<div class="pathway-step"><span>{escape_html(label)}</span>{content}</div>'


def entity_url(kind: str, identifier: str) -> str:
    plural = {
        "encounter": "encounters",
        "revelation": "revelations",
        "clue": "clues",
        "reference": "references",
    }[kind]
    return f"/{plural}/{quote(identifier, safe='')}"


def current_page_attribute(current: bool) -> str:
    return 'aria-current="page"' if current else ""


def escape_html(value: object) -> str:
    return html.escape(str(value), quote=True)
