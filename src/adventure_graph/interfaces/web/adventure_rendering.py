"""HTML rendering for adventure overview and metadata editing."""

from __future__ import annotations

from adventure_graph.application.project_browsing import AdventureOverviewResult
from adventure_graph.domain.adventure import AdventureTags
from adventure_graph.interfaces.web.authoring_rendering_support import (
    edit_attributes,
    editable_markdown,
    editable_plain_text,
    editor_footer,
    editor_toolbar,
    form_hidden,
    revision_warning,
)
from adventure_graph.interfaces.web.page_rendering import (
    escape_html,
    render_encounter_card,
    render_metrics,
    render_notice,
    render_page,
    render_revelation_card,
)
from adventure_graph.interfaces.web.view_models import AdventureEditValues, PageNotice


def render_overview(
    result: AdventureOverviewResult,
    project_label: str,
    *,
    notice: PageNotice | None = None,
    clear_draft_key: str | None = None,
) -> str:
    """Render the adventure overview page."""
    adventure = result.adventure
    connectivity = result.validation_report.edge_connectivity
    metrics = (
        (str(len(adventure.encounters)), "Encounters"),
        (str(len(adventure.revelations)), "Revelations"),
        (str(len(adventure.clues)), "Leads"),
        ("n/a" if connectivity is None else str(connectivity), "Structural resilience"),
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row">
        <div><p class="eyebrow">Adventure overview</p><h1 class="editable-surface editable-heading" {edit_attributes("/adventure/edit#title", "adventure title")}>{escape_html(adventure.title)}</h1></div>
        <div class="button-row"><a class="button primary" href="/play">Play adventure</a><a class="button secondary" href="/structure">Inspect structure</a><a class="button secondary" href="/adventure/edit">Edit adventure</a></div>
      </div>
      {editable_plain_text(adventure.synopsis, "/adventure/edit#synopsis", "adventure synopsis", "No synopsis has been written.", class_name="lede overview-synopsis")}
      {_adventure_tags(adventure.tags)}
      {render_metrics(metrics)}
      <section class="section">
        <div class="section-heading"><h2>Premise</h2><span>Situation and core problem</span></div>
        {editable_markdown(adventure.premise, "/adventure/edit#premise", "adventure premise", "No premise has been written.")}
      </section>
      <section class="section">
        <div class="section-heading"><h2>Explanation</h2><span>GM-facing reality</span></div>
        {editable_markdown(adventure.explanation, "/adventure/edit#explanation", "adventure explanation", "No explanation has been written.")}
      </section>
      <section class="section">
        <div class="section-heading"><h2>Encounters</h2><span>{len(adventure.encounters)} authored</span></div>
        <div class="card-grid">{"".join(render_encounter_card(encounter) for encounter in adventure.encounters)}</div>
      </section>
      <section class="section">
        <div class="section-heading"><h2>Revelations</h2><span>{len(adventure.revelations)} authored</span></div>
        <div class="card-grid">{"".join(render_revelation_card(revelation, adventure) for revelation in adventure.revelations)}</div>
      </section>
    """
    return render_page(
        title=adventure.title,
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="overview",
        current_id=None,
        body=body,
        related_issues=result.validation_report.issues,
        revision=result.revision.value,
        clear_draft_key=clear_draft_key,
    )


def render_adventure_edit(
    result: AdventureOverviewResult,
    project_label: str,
    *,
    csrf_token: str,
    draft_key: str,
    values: AdventureEditValues | None = None,
    notice: PageNotice | None = None,
    server_values: bool = False,
) -> str:
    """Render the adventure metadata editor."""
    adventure = result.adventure
    form = values or AdventureEditValues.from_result(result)
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading">
        <div><p class="eyebrow">Edit adventure</p><h1>{escape_html(adventure.title)}</h1></div>
        <a class="button secondary" href="/">Cancel</a>
      </div>
      <form class="editor-form" method="post" action="/adventure/edit" data-authoring-form
            data-draft-key="{escape_html(draft_key)}" data-current-revision="{escape_html(result.revision.value)}"
            data-save-label="Save adventure" data-server-values="{"true" if server_values else "false"}" data-cancel-href="/">
        {form_hidden(csrf_token, form.expected_revision)}
        {editor_toolbar("Adventure metadata", "Save adventure")}
        {revision_warning(form.expected_revision, result.revision.value)}
        <div class="form-grid">
          <label class="field" for="title"><span>Title</span><input id="title" name="title" value="{escape_html(form.title)}" data-draft-field></label>
          <label class="field field-wide" for="synopsis"><span>Synopsis <small>Concise overview</small></span><textarea id="synopsis" name="synopsis" rows="5" data-draft-field>{escape_html(form.synopsis)}</textarea></label>
          <label class="field field-wide" for="premise"><span>Premise <small>Player-facing setup and core problem</small></span><textarea id="premise" name="premise" rows="8" data-draft-field>{escape_html(form.premise)}</textarea></label>
          <label class="field field-wide" for="explanation"><span>Explanation <small>GM-facing reality</small></span><textarea id="explanation" name="explanation" rows="12" data-draft-field>{escape_html(form.explanation)}</textarea></label>
          {_adventure_tag_fields(form.tags or adventure.tags)}
        </div>
        {editor_footer(result.revision.value, "Save adventure")}
      </form>
    """
    return render_page(
        title=f"Edit {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="overview",
        current_id=None,
        body=body,
        related_issues=result.validation_report.issues,
        revision=result.revision.value,
        editing=True,
    )


def _adventure_tags(tags: AdventureTags) -> str:
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
            f'<span class="tag-chip">{escape_html(_tag_range(tags.party_size_min, tags.party_size_max, "players"))}</span>'
        )
    if tags.level_min is not None or tags.level_max is not None:
        chips.append(
            f'<span class="tag-chip">{escape_html(_tag_range(tags.level_min, tags.level_max, "level"))}</span>'
        )
    chips.extend(
        f'<span class="tag-chip subtle">{escape_html(value)}</span>' for value in tags.keywords
    )
    if not chips:
        return '<a class="adventure-tags-empty editable-surface" href="/adventure/edit#genres">Add discovery tags</a>'
    return f'<div class="adventure-tag-list overview-tags">{"".join(chips)}</div>'


def _tag_range(minimum: int | None, maximum: int | None, noun: str) -> str:
    if minimum is not None and maximum is not None:
        value = str(minimum) if minimum == maximum else f"{minimum}-{maximum}"
    elif minimum is not None:
        value = f"{minimum}+"
    else:
        value = f"up to {maximum}"
    return f"{value} {noun}"


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
      <div class="form-subheading field-wide"><strong>Discovery tags</strong><span>Structured facets support library filtering; keywords remain open-ended.</span></div>
      <label class="field" for="genres"><span>Genres <small>Comma-separated</small></span><input id="genres" name="genres" value="{escape_html(", ".join(tags.genres))}" data-draft-field></label>
      <label class="field" for="game_systems"><span>Game systems <small>Comma-separated</small></span><input id="game_systems" name="game_systems" value="{escape_html(", ".join(tags.game_systems))}" data-draft-field></label>
      <label class="field" for="settings"><span>Settings <small>Comma-separated</small></span><input id="settings" name="settings" value="{escape_html(", ".join(tags.settings))}" data-draft-field></label>
      <label class="field" for="combat_intensity"><span>Combat intensity</span><select id="combat_intensity" name="combat_intensity" data-draft-field>{options}</select></label>
      {_optional_number_field("party_size_min", "Minimum group size", tags.party_size_min)}
      {_optional_number_field("party_size_max", "Maximum group size", tags.party_size_max)}
      {_optional_number_field("level_min", "Minimum level", tags.level_min)}
      {_optional_number_field("level_max", "Maximum level", tags.level_max)}
      <label class="field field-wide" for="keywords"><span>Other tags <small>Comma-separated themes, structures, and play styles</small></span><input id="keywords" name="keywords" value="{escape_html(", ".join(tags.keywords))}" data-draft-field></label>
    '''


def _optional_number_field(name: str, label: str, value: int | None) -> str:
    rendered = "" if value is None else str(value)
    return f'<label class="field" for="{name}"><span>{escape_html(label)}</span><input id="{name}" type="number" min="1" step="1" name="{name}" value="{rendered}" data-draft-field></label>'
