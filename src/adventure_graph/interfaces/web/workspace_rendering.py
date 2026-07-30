"""HTML rendering for application-wide workspace pages."""

from __future__ import annotations

from urllib.parse import urlencode

from adventure_graph import __version__
from adventure_graph.application.project_browsing import AdventureOverviewResult
from adventure_graph.application.workspace_management import (
    AdventureCatalogEntry,
    WorkspaceProjectDiagnostic,
    WorkspaceSnapshot,
)
from adventure_graph.domain.adventure import AdventureTags
from adventure_graph.domain.validation_models import ValidationPolicy
from adventure_graph.interfaces.web.page_rendering import (
    escape_html,
    render_notice,
    render_theme_toggle,
)
from adventure_graph.interfaces.web.transfer_forms import MAX_PORTABLE_DOCUMENT_BYTES
from adventure_graph.interfaces.web.view_models import PageNotice


def render_adventure_catalog(
    snapshot: WorkspaceSnapshot,
    *,
    csrf_token: str,
    notice: PageNotice | None = None,
    clear_draft_key: str | None = None,
) -> str:
    """Render selectable and filterable adventures in the local workspace."""
    selected = snapshot.settings.selected_adventure_key
    cards = "".join(
        _adventure_card(
            entry,
            selected=entry.key == selected,
            csrf_token=csrf_token,
            revision=snapshot.revision.value,
        )
        for entry in snapshot.adventures
    ) or _empty_catalog_card(
        csrf_token=csrf_token,
        revision=snapshot.revision.value,
    )
    current_action = (
        '<a class="button secondary" href="/">Open current adventure</a>'
        if snapshot.selected_adventure is not None
        else ""
    )
    filters = _catalog_filters(snapshot.adventures) if snapshot.adventures else ""
    diagnostics = _workspace_diagnostics(snapshot.diagnostics)
    unavailable_selection_notice = _unavailable_selection_notice(snapshot)
    body = f"""
      {render_notice(notice)}
      {render_notice(unavailable_selection_notice)}
      <div class="page-heading-row"><div><p class="eyebrow">Adventure library</p><h1>Browse your adventures</h1><p class="lede">Filter by genre, game system, setting, group size, level, or combat intensity, then open the adventure you want to read or run.</p></div><div class="page-heading-actions">{current_action}<a class="button secondary" href="/adventures/import">Import adventure</a><a class="button secondary" href="/adventures/playthroughs/import">Import playthrough</a><a class="button primary" href="/adventures/new">New adventure</a></div></div>
      {diagnostics}
      <section class="section" data-adventure-catalog>{filters}<div class="section-heading"><h2>Adventures</h2><span data-adventure-filter-count aria-live="polite">{len(snapshot.adventures)} of {len(snapshot.adventures)} projects</span></div><div class="card-grid workspace-catalog">{cards}</div><p class="empty-copy catalog-filter-empty" data-adventure-filter-empty aria-live="polite" hidden>No adventures match these filters.</p></section>
    """
    return _workspace_page(
        "Adventures — Adventure Graph",
        body,
        clear_draft_key=clear_draft_key,
        current_page="adventures",
    )


def _sample_adventure_form(*, csrf_token: str, revision: str, button_class: str) -> str:
    return (
        '<form method="post" action="/adventures/sample">'
        f'<input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}">'
        f'<input type="hidden" name="expected_revision" value="{escape_html(revision)}">'
        f'<button class="{escape_html(button_class)}" type="submit">'
        "Add The Glass Saint sample</button></form>"
    )


def _empty_catalog_card(*, csrf_token: str, revision: str) -> str:
    sample_form = _sample_adventure_form(
        csrf_token=csrf_token,
        revision=revision,
        button_class="button primary",
    )
    return (
        '<article class="card empty-catalog-card"><div>'
        '<p class="eyebrow">First project</p>'
        "<h2>Begin with a sample or a blank adventure</h2>"
        "<p>The Glass Saint is the complete sample included with this beta. "
        "Adding it creates an editable copy with an empty playthrough.</p></div>"
        f'<div class="workspace-card-actions">{sample_form}'
        '<a class="button secondary" href="/adventures/new">Create blank adventure</a>'
        "</div></article>"
    )


def _sample_adventure_card(*, csrf_token: str, revision: str) -> str:
    sample_form = _sample_adventure_form(
        csrf_token=csrf_token,
        revision=revision,
        button_class="button secondary",
    )
    return (
        '<section class="card sample-adventure-card"><div>'
        '<p class="eyebrow">Included sample</p><h2>The Glass Saint</h2>'
        "<p>Add a separate editable copy with a fresh identity and empty playthrough.</p>"
        f"</div>{sample_form}</section>"
    )


def _unavailable_selection_notice(snapshot: WorkspaceSnapshot) -> PageNotice | None:
    selected = snapshot.settings.selected_adventure_key
    if selected is None or snapshot.selected_adventure is not None:
        return None
    return PageNotice(
        "info",
        "Previously selected adventure unavailable",
        "Adventure Graph did not substitute another project. Repair the selected project "
        "or choose the adventure you intend to open.",
    )


def _workspace_diagnostics(
    diagnostics: tuple[WorkspaceProjectDiagnostic, ...],
) -> str:
    if not diagnostics:
        return ""
    items = "".join(
        f"<li><strong>{escape_html(item.key)}</strong><span>{escape_html(item.message)}</span></li>"
        for item in diagnostics
    )
    return (
        '<section class="notice error workspace-diagnostics" role="alert" aria-atomic="true">'
        "<strong>Some adventure projects need attention</strong>"
        "<p>Adventure Graph found project files that it could not open. "
        "Repair or remove each listed <code>adventure.json</code>, then reload the catalog.</p>"
        f"<ul>{items}</ul></section>"
    )


def render_adventure_create(
    snapshot: WorkspaceSnapshot,
    *,
    csrf_token: str,
    notice: PageNotice | None = None,
) -> str:
    """Render the guided new-adventure form."""
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading"><div><p class="eyebrow">New adventure</p><h1>Start a new adventure</h1><p class="lede">Name the adventure, then add as much or as little detail as you need. You can create the opening encounter now or later.</p></div><a class="button secondary" href="/adventures">Cancel</a></div>
      {_sample_adventure_card(csrf_token=csrf_token, revision=snapshot.revision.value)}
      <form class="editor-form" method="post" action="/adventures/new" data-authoring-form
            data-draft-key="workspace:new-adventure" data-current-revision="{escape_html(snapshot.revision.value)}"
            data-save-label="Create adventure" data-server-values="false" data-cancel-href="/adventures">
        <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}"><input type="hidden" name="expected_revision" value="{escape_html(snapshot.revision.value)}">
        <div class="editor-toolbar"><div><strong>Adventure foundation</strong><span data-draft-status>Unsaved changes are preserved in this browser.</span><div class="draft-actions"><button class="text-button" type="button" data-recover-draft hidden>Recover older draft</button><button class="text-button" type="button" data-discard-draft hidden>Discard browser draft</button></div></div><button class="button primary" type="submit">Create adventure</button></div>
        <div class="form-grid">
          {_text_field("title", "Adventure title", "", required=True)}
          {_textarea("synopsis", "Synopsis", "", 4)}
          {_textarea("premise", "Premise", "", 5)}
          {_textarea("explanation", "Explanation", "", 6)}
          {_adventure_tag_fields(AdventureTags())}
          <div class="form-subheading field-wide"><strong>Opening encounter (optional)</strong><span>Leave this section blank to create only the adventure shell.</span></div>
          {_text_field("opening_title", "Opening encounter title", "")}
          {_text_field("opening_summary", "Opening-encounter GM orientation", "")}
          {_textarea("opening_view", "Opening description (player-facing)", "", 7)}
        </div>
        <div class="editor-footer"><button class="button primary" type="submit">Create adventure</button></div>
      </form>
    """
    return _workspace_page("New adventure — Adventure Graph", body, current_page="adventures")


def render_adventure_import(
    snapshot: WorkspaceSnapshot,
    *,
    csrf_token: str,
    notice: PageNotice | None = None,
) -> str:
    """Render the canonical adventure-document import form."""
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading"><div><p class="eyebrow">Import adventure</p><h1>Import an adventure</h1><p class="lede">Choose an Adventure Graph adventure JSON file. The imported project keeps its adventure identity and starts with an empty play journal.</p></div><a class="button secondary" href="/adventures">Cancel</a></div>
      {
        _transfer_import_form(
            action="/adventures/import",
            csrf_token=csrf_token,
            revision=snapshot.revision.value,
            document_heading="Adventure document",
            document_explanation="Canonical schema-versioned JSON",
            field_label="Adventure JSON file",
            file_field="adventure_file",
            button_label="Import adventure",
        )
    }
    """
    return _workspace_page("Import adventure — Adventure Graph", body, current_page="adventures")


def render_playthrough_import(
    snapshot: WorkspaceSnapshot,
    *,
    csrf_token: str,
    notice: PageNotice | None = None,
) -> str:
    """Render workspace-level playthrough import with identity-based routing."""
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading"><div><p class="eyebrow">Import playthrough</p><h1>Import a playthrough</h1><p class="lede">Choose an Adventure Graph playthrough JSON file. Its embedded adventure identity determines which project receives the immutable archive.</p></div><a class="button secondary" href="/adventures">Cancel</a></div>
      {
        _transfer_import_form(
            action="/adventures/playthroughs/import",
            csrf_token=csrf_token,
            revision=snapshot.revision.value,
            document_heading="Playthrough archive",
            document_explanation=(
                "The selected adventure and every active journal remain unchanged."
            ),
            field_label="Playthrough JSON file",
            file_field="archive_file",
            button_label="Import playthrough",
        )
    }
    """
    return _workspace_page("Import playthrough — Adventure Graph", body, current_page="adventures")


def _transfer_import_form(
    *,
    action: str,
    csrf_token: str,
    revision: str,
    document_heading: str,
    document_explanation: str,
    field_label: str,
    file_field: str,
    button_label: str,
) -> str:
    size_mib = MAX_PORTABLE_DOCUMENT_BYTES // (1024 * 1024)
    help_id = f"{file_field}-help"
    return f"""
      <form class="editor-form transfer-import-form" method="post"
            action="{escape_html(action)}" enctype="multipart/form-data">
        <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}">
        <input type="hidden" name="expected_revision" value="{escape_html(revision)}">
        <div class="editor-toolbar"><div><strong>{escape_html(document_heading)}</strong><span>{escape_html(document_explanation)}</span></div></div>
        <div class="form-grid"><label class="field field-wide"><span>{escape_html(field_label)}</span><input type="file" name="{escape_html(file_field)}" accept="application/json,.json" aria-describedby="{escape_html(help_id)}" required><small id="{escape_html(help_id)}">Choose one canonical JSON document up to {size_mib} MiB.</small></label></div>
        <div class="editor-footer"><button class="button primary" type="submit">{escape_html(button_label)}</button></div>
      </form>
    """


def render_settings(
    snapshot: WorkspaceSnapshot,
    current: AdventureOverviewResult | None,
    *,
    csrf_token: str,
    notice: PageNotice | None = None,
) -> str:
    """Render workspace defaults and the selected adventure's effective policy."""
    defaults = _policy_form(
        snapshot.settings.validator_defaults,
        action="/settings/defaults",
        revision=snapshot.revision.value,
        csrf_token=csrf_token,
        heading="Defaults for new adventures",
        explanation="These values seed future projects. Existing adventures are not rewritten.",
        button="Save defaults",
    )
    current_form = (
        _policy_form(
            current.adventure.validation_policy,
            action="/settings/adventure",
            revision=current.revision.value,
            csrf_token=csrf_token,
            heading=f"{current.adventure.title} validator policy",
            explanation="These thresholds are persisted inside the selected adventure.",
            button="Save adventure policy",
        )
        if current is not None
        else '<section class="notice info"><strong>No adventure selected</strong><p>Create or select an adventure to edit its effective validator policy.</p></section>'
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row"><div><p class="eyebrow">Settings</p><h1>Validator policy</h1><p class="lede">Set the structural checks used for new adventures and, when one is selected, adjust that adventure separately.</p></div><a class="button secondary" href="/adventures">Adventures</a></div>
      <div class="settings-stack">{defaults}{current_form}</div>
    """
    return _workspace_page("Settings — Adventure Graph", body, current_page="settings")


def render_help() -> str:
    """Render conceptual and workflow guidance available without a selected adventure."""
    version = escape_html(__version__)
    body = f"""
      <div class="page-heading-row help-heading">
        <div>
          <p class="eyebrow">Help and introduction</p>
          <h1>Prepare situations, not a fixed plot</h1>
          <p class="lede">Adventure Graph helps a GM organize an adventure as connected encounters. Players can follow the leads that interest them, while the GM can see which routes remain available and where important information may need reinforcement.</p>
        </div>
      </div>
      <section class="help-grid" aria-label="Adventure Graph concepts">
        <article class="card help-card help-card-wide">
          <p class="eyebrow">The basic model</p>
          <h2>Encounters connected by information</h2>
          <p>An <strong>encounter</strong> is a place, scene, person, event, or other situation the party can engage with. A <strong>lead</strong> is something discoverable there. A <strong>revelation</strong> is the conclusion or actionable information that one or more leads support.</p>
          <p>The graph is a preparation aid, not a script. It helps you offer meaningful choices, notice fragile routes, and adapt when the players surprise you.</p>
        </article>
        <article class="card help-card">
          <p class="eyebrow">Author</p>
          <h2>Build the possibilities</h2>
          <ol class="help-steps">
            <li><span>1</span><div><strong>Create encounters.</strong><p>Describe the situations the players may reach.</p></div></li>
            <li><span>2</span><div><strong>Name revelations.</strong><p>State what the players may learn or unlock.</p></div></li>
            <li><span>3</span><div><strong>Place leads.</strong><p>Connect encounters to revelations through concrete discoveries.</p></div></li>
          </ol>
        </article>
        <article class="card help-card">
          <p class="eyebrow">Play</p>
          <h2>Follow the table</h2>
          <ol class="help-steps">
            <li><span>1</span><div><strong>Focus the current encounter.</strong><p>Keep its description, leads, and context in view.</p></div></li>
            <li><span>2</span><div><strong>Record what changed.</strong><p>Save notes and outcomes without forcing a transition.</p></div></li>
            <li><span>3</span><div><strong>Improvise when needed.</strong><p>Add an off-script encounter or lead, then return to the table.</p></div></li>
          </ol>
        </article>
        <article class="card help-card help-card-wide">
          <p class="eyebrow">Beta feedback</p>
          <h2>Identify the build</h2>
          <p>When reporting a problem, include <strong>Adventure Graph <code>{version}</code></strong>, your operating system, the workflow you used, and the exact steps that produced the result.</p>
          <p>Adventure and playthrough files may contain private table notes. Share only the smallest relevant file after removing those notes, and keep an untouched copy whenever a write, import, archive, or migration is in question.</p>
        </article>
      </section>
      <section class="section help-reference-section">
        <div class="section-heading"><div><p class="eyebrow">Further reading</p><h2>Justin Alexander and node-based design</h2></div></div>
        <div class="card help-reference-card">
          <p>The approach used here was introduced to this project through Justin Alexander's practical writing on node-based scenario design. We are grateful for advice that has helped many GMs prepare flexible situations and respond to player choice.</p>
          <div class="help-resource-links">
            <a class="button secondary" href="https://thealexandrian.net/wordpress/7949/roleplaying-games/node-based-scenario-design-part-1-the-plotted-approach" target="_blank" rel="noopener noreferrer">Read the Node-Based Scenario Design sequence</a>
            <a class="button secondary" href="https://thealexandrian.net/so-you-want-to-be-a-game-master" target="_blank" rel="noopener noreferrer">Explore <em>So You Want to Be a Game Master</em></a>
          </div>
          <p class="help-disclaimer"><strong>Independent project.</strong> Adventure Graph is not affiliated with, sponsored by, or endorsed by Justin Alexander, The Alexandrian, or the book's publishers. This is our own small effort to make adventure preparation and table play easier.</p>
        </div>
      </section>
    """
    return _workspace_page("Help — Adventure Graph", body, current_page="help")


def _adventure_card(
    entry: AdventureCatalogEntry,
    *,
    selected: bool,
    csrf_token: str,
    revision: str,
) -> str:
    status = '<span class="badge green">Current adventure</span>' if selected else ""
    health = _catalog_health_badge(entry)
    open_action = (
        '<a class="button primary" href="/">Open adventure</a>'
        if selected
        else _workspace_selection_form(
            entry,
            csrf_token=csrf_token,
            revision=revision,
            action="/adventures/select",
            label="Open adventure",
            button_class="primary",
        )
    )
    playthrough_action = (
        '<a class="button secondary" href="/archives">Playthroughs</a>'
        if selected
        else _workspace_selection_form(
            entry,
            csrf_token=csrf_token,
            revision=revision,
            action="/adventures/playthroughs",
            label="Playthroughs",
            button_class="secondary",
        )
    )
    synopsis_copy = escape_html(entry.synopsis) if entry.synopsis else "No synopsis yet."
    badges = (
        f'<div class="workspace-card-badges">{status}{health}</div>' if status or health else ""
    )
    tags = entry.tags
    search_values = (
        entry.title,
        entry.synopsis,
        *tags.genres,
        *tags.game_systems,
        *tags.settings,
        *tags.keywords,
    )
    search = " ".join(search_values).casefold()
    facets = _catalog_tag_summary(tags)
    export_url = "/adventures/export?" + urlencode({"key": entry.key})
    return f'''<article class="card workspace-card" data-adventure-card data-search="{escape_html(search)}" data-genres="{escape_html(_facet_value(tags.genres))}" data-systems="{escape_html(_facet_value(tags.game_systems))}" data-settings="{escape_html(_facet_value(tags.settings))}" data-party-min="{_optional_number(tags.party_size_min)}" data-party-max="{_optional_number(tags.party_size_max)}" data-level-min="{_optional_number(tags.level_min)}" data-level-max="{_optional_number(tags.level_max)}" data-combat="{escape_html(tags.combat_intensity or "")}"><div>{badges}<h3>{escape_html(entry.title)}</h3>{facets}<p class="workspace-card-synopsis">{synopsis_copy}</p><dl class="workspace-card-metrics"><div><dt>Encounters</dt><dd>{entry.encounter_count}</dd></div><div><dt>Revelations</dt><dd>{entry.revelation_count}</dd></div><div><dt>Leads</dt><dd>{entry.clue_count}</dd></div></dl></div><div class="workspace-card-actions"><a class="button secondary" href="{escape_html(export_url)}">Export adventure</a>{playthrough_action}{open_action}</div></article>'''


def _workspace_selection_form(
    entry: AdventureCatalogEntry,
    *,
    csrf_token: str,
    revision: str,
    action: str,
    label: str,
    button_class: str,
) -> str:
    """Render a revision-aware workspace selection action for one adventure."""
    return f'''<form method="post" action="{escape_html(action)}"><input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}"><input type="hidden" name="expected_revision" value="{escape_html(revision)}"><input type="hidden" name="adventure_key" value="{escape_html(entry.key)}"><button class="button {escape_html(button_class)}" type="submit">{escape_html(label)}</button></form>'''


def _catalog_filters(entries: tuple[AdventureCatalogEntry, ...]) -> str:
    genres = sorted({tag for entry in entries for tag in entry.tags.genres}, key=str.casefold)
    systems = sorted(
        {tag for entry in entries for tag in entry.tags.game_systems}, key=str.casefold
    )
    settings = sorted({tag for entry in entries for tag in entry.tags.settings}, key=str.casefold)
    return f"""
      <div class="catalog-filters" aria-label="Filter adventures">
        <label class="field catalog-search"><span>Search</span><input type="search" data-adventure-filter-search placeholder="Title, synopsis, or tag"></label>
        {_filter_select("Genre", "genre", genres)}
        {_filter_select("Game system", "system", systems)}
        {_filter_select("Setting", "setting", settings)}
        <label class="field"><span>Group size</span><input type="number" min="1" step="1" data-adventure-filter-party placeholder="Any"></label>
        <label class="field"><span>Level</span><input type="number" min="1" step="1" data-adventure-filter-level placeholder="Any"></label>
        <label class="field"><span>Combat</span><select data-adventure-filter-combat><option value="">Any</option><option value="none">None</option><option value="light">Light</option><option value="moderate">Moderate</option><option value="heavy">Heavy</option></select></label>
        <div class="catalog-filter-footer">
          <p class="catalog-filter-note">Group size and level match only adventures with a stated range.</p>
          <button class="button secondary catalog-filter-clear" type="button" data-adventure-filter-clear>Clear filters</button>
        </div>
      </div>
    """


def _filter_select(label: str, name: str, values: list[str]) -> str:
    options = "".join(
        f'<option value="{escape_html(value.casefold())}">{escape_html(value)}</option>'
        for value in values
    )
    return f'<label class="field"><span>{escape_html(label)}</span><select data-adventure-filter-{name}><option value="">Any</option>{options}</select></label>'


def _catalog_tag_summary(tags: AdventureTags) -> str:
    chips = [
        f'<span class="tag-chip">{escape_html(value)}</span>'
        for value in (*tags.genres, *tags.game_systems, *tags.settings)
    ]
    if tags.combat_intensity:
        chips.append(
            f'<span class="tag-chip">{escape_html(tags.combat_intensity.title())} combat</span>'
        )
    if tags.party_size_min is not None or tags.party_size_max is not None:
        chips.append(
            f'<span class="tag-chip">{escape_html(_range_label(tags.party_size_min, tags.party_size_max, "players"))}</span>'
        )
    if tags.level_min is not None or tags.level_max is not None:
        chips.append(
            f'<span class="tag-chip">{escape_html(_range_label(tags.level_min, tags.level_max, "level"))}</span>'
        )
    chips.extend(
        f'<span class="tag-chip subtle">{escape_html(value)}</span>' for value in tags.keywords
    )
    if not chips:
        return '<p class="muted-note adventure-tags-empty">No discovery tags yet.</p>'
    return f'<div class="adventure-tag-list">{"".join(chips)}</div>'


def _range_label(minimum: int | None, maximum: int | None, noun: str) -> str:
    if minimum is not None and maximum is not None:
        value = str(minimum) if minimum == maximum else f"{minimum}-{maximum}"
    elif minimum is not None:
        value = f"{minimum}+"
    else:
        value = f"up to {maximum}"
    return f"{value} {noun}"


def _facet_value(values: tuple[str, ...]) -> str:
    return "|".join(value.casefold() for value in values)


def _optional_number(value: int | None) -> str:
    return "" if value is None else str(value)


def _adventure_tag_fields(tags: AdventureTags) -> str:
    combat_options = (
        ("", "Unspecified"),
        ("none", "None"),
        ("light", "Light"),
        ("moderate", "Moderate"),
        ("heavy", "Heavy"),
    )
    options = "".join(
        f'<option value="{value}" {"selected" if tags.combat_intensity == value or (not value and tags.combat_intensity is None) else ""}>{label}</option>'
        for value, label in combat_options
    )
    return f'''
      <div class="form-subheading field-wide"><strong>Discovery tags</strong><span>Structured facets support filtering; keywords remain open-ended.</span></div>
      {_text_field("genres", "Genres (comma-separated)", ", ".join(tags.genres))}
      {_text_field("game_systems", "Game systems (comma-separated)", ", ".join(tags.game_systems))}
      {_text_field("settings", "Settings (comma-separated)", ", ".join(tags.settings))}
      <label class="field" for="combat_intensity"><span>Combat intensity</span><select id="combat_intensity" name="combat_intensity" data-draft-field>{options}</select></label>
      {_number_field_optional("party_size_min", "Minimum group size", tags.party_size_min)}
      {_number_field_optional("party_size_max", "Maximum group size", tags.party_size_max)}
      {_number_field_optional("level_min", "Minimum level", tags.level_min)}
      {_number_field_optional("level_max", "Maximum level", tags.level_max)}
      <label class="field field-wide" for="keywords"><span>Other tags <small>Comma-separated themes, structures, and play styles</small></span><input id="keywords" type="text" name="keywords" value="{escape_html(", ".join(tags.keywords))}" data-draft-field></label>
    '''


def _catalog_health_badge(entry: AdventureCatalogEntry) -> str:
    if entry.error_count:
        label = "validation error" if entry.error_count == 1 else "validation errors"
        return f'<span class="badge red">{entry.error_count} {label}</span>'
    if entry.warning_count:
        label = "warning" if entry.warning_count == 1 else "warnings"
        return f'<span class="badge amber">{entry.warning_count} {label}</span>'
    return '<span class="badge green">No validation findings</span>'


def _policy_form(
    policy: ValidationPolicy,
    *,
    action: str,
    revision: str,
    csrf_token: str,
    heading: str,
    explanation: str,
    button: str,
) -> str:
    return f"""
      <form class="editor-form settings-form" method="post" action="{action}">
        <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}"><input type="hidden" name="expected_revision" value="{escape_html(revision)}">
        <div class="editor-toolbar"><div><strong>{escape_html(heading)}</strong><span>{escape_html(explanation)}</span></div></div>
        <div class="form-grid settings-grid">
          {_number_field("minimum_clues_per_revelation", "Leads per necessary revelation", policy.minimum_clues_per_revelation)}
          {_number_field("minimum_source_encounters_per_revelation", "Source encounters per necessary revelation", policy.minimum_source_encounters_per_revelation)}
          {_number_field("minimum_incoming_clues_per_encounter", "Leads pointing to a necessary encounter", policy.minimum_incoming_clues_per_encounter)}
          {_number_field("minimum_incoming_source_encounters_per_encounter", "Source encounters leading to a necessary encounter", policy.minimum_incoming_source_encounters_per_encounter)}
          {_number_field("minimum_outgoing_clues_per_encounter", "Outgoing leads per encounter", policy.minimum_outgoing_clues_per_encounter)}
          {_number_field("minimum_distinct_encounter_targets_per_encounter", "Distinct destinations per encounter", policy.minimum_distinct_encounter_targets_per_encounter)}
          {_number_field("minimum_edge_connectivity", "Minimum necessary-encounter edge connectivity", policy.minimum_edge_connectivity)}
          <label class="checkbox-card"><input type="checkbox" name="require_directed_reachability" value="1" {"checked" if policy.require_directed_reachability else ""}><span><strong>Require directed reachability</strong><small>Necessary encounters must be reachable from a start; unreachable optional encounters are warnings.</small></span></label>
        </div>
        <div class="editor-footer"><span class="muted-note">Use zero to disable a numeric threshold deliberately.</span><button class="button primary" type="submit">{escape_html(button)}</button></div>
      </form>
    """


def _text_field(name: str, label: str, value: str, *, required: bool = False) -> str:
    required_attribute = " required" if required else ""
    return f'<label class="field" for="{name}"><span>{escape_html(label)}</span><input id="{name}" type="text" name="{name}" value="{escape_html(value)}" data-draft-field{required_attribute}></label>'


def _number_field(name: str, label: str, value: int) -> str:
    return f'<label class="field"><span>{escape_html(label)}</span><input type="number" min="0" step="1" name="{name}" value="{value}" required></label>'


def _number_field_optional(name: str, label: str, value: int | None) -> str:
    rendered = "" if value is None else str(value)
    return f'<label class="field" for="{name}"><span>{escape_html(label)}</span><input id="{name}" type="number" min="1" step="1" name="{name}" value="{rendered}" data-draft-field></label>'


def _textarea(name: str, label: str, value: str, rows: int) -> str:
    return f'<label class="field" for="{name}"><span>{escape_html(label)}</span><textarea id="{name}" name="{name}" rows="{rows}" data-draft-field>{escape_html(value)}</textarea></label>'


def _workspace_page(
    title: str,
    body: str,
    *,
    clear_draft_key: str | None = None,
    current_page: str | None = None,
) -> str:
    body_attribute = (
        f' data-clear-draft-key="{escape_html(clear_draft_key)}"' if clear_draft_key else ""
    )
    navigation = "".join(
        _workspace_topbar_link(key, href, label, current_page)
        for key, href, label in (
            ("adventures", "/adventures", "Adventures"),
            ("settings", "/settings", "Settings"),
            ("help", "/help", "Help"),
        )
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light dark"><title>{escape_html(title)}</title><script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css"></head>
<body{body_attribute}><a class="skip-link" href="#main-content">Skip to content</a><header class="topbar"><a class="brand" href="/"><span class="brand-mark">AG</span><span class="brand-copy"><strong>Adventure Graph</strong><span>Local GM workspace</span></span></a><nav class="topbar-actions" aria-label="Workspace">{navigation}</nav>{render_theme_toggle()}</header><main class="workspace-page" id="main-content"><div class="workspace-page-inner">{body}</div></main></body></html>"""


def _workspace_topbar_link(
    key: str,
    href: str,
    label: str,
    current_page: str | None,
) -> str:
    """Render one application-wide workspace destination."""
    current = ' aria-current="page"' if current_page == key else ""
    return f'<a href="{href}"{current}>{label}</a>'
