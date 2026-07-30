"""HTML rendering for encounter detail and editing."""

from __future__ import annotations

from urllib.parse import urlencode

from adventure_graph.application.encounter_authoring import EncounterDetailResult
from adventure_graph.application.structural_authoring import StructuralOverviewResult
from adventure_graph.interfaces.web.authoring_rendering_support import (
    dependency_section,
    edit_attributes,
    editable_markdown,
    editable_plain_text,
    editor_footer,
    editor_toolbar,
    form_hidden,
    revision_warning,
)
from adventure_graph.interfaces.web.page_rendering import (
    entity_url,
    escape_html,
    render_badges,
    render_clue_card,
    render_empty_card,
    render_encounter_card,
    render_notice,
    render_page,
)
from adventure_graph.interfaces.web.reference_rendering import render_encounter_reference_links
from adventure_graph.interfaces.web.view_models import (
    EncounterCreateValues,
    EncounterEditValues,
    PageNotice,
)


def render_encounter(
    result: EncounterDetailResult,
    project_label: str,
    *,
    csrf_token: str,
    notice: PageNotice | None = None,
    clear_draft_key: str | None = None,
) -> str:
    """Render one encounter and its authored relationships."""
    adventure = result.adventure
    detail = result.detail
    encounter = detail.encounter
    encounter_url = entity_url("encounter", encounter.id)
    encounter_edit_url = f"{encounter_url}/edit"
    badges = [
        "Necessary" if encounter.required else "Optional",
        *(("Start encounter",) if encounter.start else ()),
        *(("End encounter",) if encounter.end else ()),
        *encounter.tags,
    ]
    sourced = "".join(
        render_clue_card(clue, adventure, include_source=False) for clue in detail.sourced_clues
    ) or render_empty_card("No leads are sourced at this encounter.")
    incoming = "".join(
        render_clue_card(clue, adventure, include_source=True) for clue in detail.incoming_clues
    ) or render_empty_card("No authored leads point to this encounter.")
    destinations = "".join(
        render_encounter_card(item) for item in detail.destination_encounters
    ) or render_empty_card("This encounter does not presently point to another encounter.")
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row">
        <div><p class="eyebrow">Encounter</p><h1 class="editable-surface editable-heading" {edit_attributes(f"{encounter_edit_url}#title", "encounter title")}>{escape_html(encounter.title)}</h1></div>
        <div class="button-row">
          <a class="button secondary" href="/revelations/new?{urlencode({"unlocks": encounter.id})}">Add unlocking revelation</a>
          <a class="button secondary" href="/clues/new?{urlencode({"source": encounter.id})}">Add lead here</a>
          <a class="button secondary" href="{encounter_url}/remove">Remove encounter</a>
          <a class="button primary" href="{encounter_edit_url}">Edit encounter</a>
        </div>
      </div>
      <section class="section encounter-orientation-section">
        <div class="section-heading"><h2>GM orientation</h2><span>Encounter synopsis</span></div>
        {editable_plain_text(encounter.summary, f"{encounter_edit_url}#summary", "GM orientation", "No encounter synopsis has been written.", class_name="lede")}
      </section>
      {render_badges(badges)}
      <section class="section">
        <div class="section-heading"><h2>Opening description</h2><span>Player-facing · read or paraphrase</span></div>
        {editable_markdown(encounter.opening_view, f"{encounter_edit_url}#opening_view", "opening description", "No player-facing opening description has been written.")}
      </section>
      <section class="section">
        <div class="section-heading"><h2>Encounter material</h2><span>Markdown</span></div>
        {editable_markdown(encounter.content, f"{encounter_edit_url}#content", "encounter material", "No encounter material has been written.")}
      </section>
      {render_encounter_reference_links(result, csrf_token=csrf_token, include_controls=True)}
      <section class="section">
        <div class="section-heading"><h2>Leads at this encounter</h2><span>{len(detail.sourced_clues)} leads</span></div>
        <div class="card-grid">{sourced}</div>
      </section>
      <section class="section">
        <div class="section-heading"><h2>Destinations supported here</h2><span>{len(detail.destination_encounters)} encounters</span></div>
        <div class="card-grid">{destinations}</div>
      </section>
      <section class="section">
        <div class="section-heading"><h2>Incoming pathways</h2><span>{len(detail.incoming_clues)} leads</span></div>
        <div class="card-grid">{incoming}</div>
      </section>
      {dependency_section(detail.dependency_preview, "encounter")}
    """
    return render_page(
        title=f"{encounter.title} — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="encounter",
        current_id=encounter.id,
        body=body,
        related_issues=detail.validation_issues,
        revision=result.revision.value,
        clear_draft_key=clear_draft_key,
    )


def render_encounter_create(
    result: StructuralOverviewResult,
    project_label: str,
    *,
    csrf_token: str,
    draft_key: str,
    values: EncounterCreateValues | None = None,
    notice: PageNotice | None = None,
    server_values: bool = False,
) -> str:
    """Render an explicit-save form for one new encounter."""
    form = values or EncounterCreateValues(
        start=not result.adventure.encounters,
        expected_revision=result.revision.value,
    )
    required_checked = " checked" if form.required else ""
    start_checked = " checked" if form.start else ""
    end_checked = " checked" if form.end else ""
    revision_warning_html = revision_warning(form.expected_revision, result.revision.value)
    cancel_href = form.return_to or "/structure"
    return_field = (
        f'<input type="hidden" name="return_to" value="{escape_html(form.return_to)}">'
        if form.return_to
        else ""
    )
    heading = "Add an encounter during play" if form.return_to else "Add an encounter"
    eyebrow = "Play improvisation" if form.return_to else "New encounter"
    context = (
        '<p class="lede">Create authored material without changing the current visit or play history. '
        "After saving, the new encounter will be focused in the Table workspace.</p>"
        if form.return_to
        else ""
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading">
        <div><p class="eyebrow">{eyebrow}</p><h1>{heading}</h1></div>
        <a class="button secondary" href="{escape_html(cancel_href)}">{"Back to table" if form.return_to else "Cancel"}</a>
      </div>
      {context}
      <form class="editor-form" method="post" action="/encounters/new"
            data-authoring-form data-encounter-editor data-draft-key="{escape_html(draft_key)}"
            data-current-revision="{escape_html(result.revision.value)}"
            data-save-label="Create encounter" data-server-values="{"true" if server_values else "false"}" data-cancel-href="{escape_html(cancel_href)}">
        {form_hidden(csrf_token, form.expected_revision)}
        {return_field}
        {editor_toolbar("Authored encounter", "Create encounter")}
        {revision_warning_html}
        <div class="form-grid">
          <label class="field" for="title"><span>Title</span><input id="title" name="title" value="{escape_html(form.title)}" required data-draft-field></label>
          <label class="field" for="summary"><span>GM orientation <small>Encounter synopsis</small></span><textarea id="summary" name="summary" rows="4" data-draft-field>{escape_html(form.summary)}</textarea></label>
          <label class="field field-wide" for="opening_view"><span>Opening description <small>Player-facing Markdown</small></span><textarea id="opening_view" name="opening_view" rows="8" data-draft-field>{escape_html(form.opening_view)}</textarea></label>
          <label class="field field-wide" for="content"><span>Encounter material <small>Markdown</small></span><textarea class="content-editor" id="content" name="content" rows="26" data-draft-field>{escape_html(form.content)}</textarea></label>
          <label class="field field-wide" for="tags"><span>Tags <small>Comma-separated</small></span><input id="tags" name="tags" value="{escape_html(form.tags)}" data-draft-field></label>
          <fieldset class="field field-wide option-field"><legend>Necessity</legend>
            <label><input type="checkbox" name="required" value="1" data-draft-field{required_checked}> Necessary encounter</label>
            <small>Optional encounters still need at least one incoming lead, but they are exempt from configured incoming-lead minimums.</small>
          </fieldset>
          <fieldset class="field field-wide option-field"><legend>Encounter role</legend>
            <label><input type="checkbox" name="start" value="1" data-draft-field{start_checked}> Start encounter</label>
            <label><input type="checkbox" name="end" value="1" data-draft-field{end_checked}> End encounter</label>
          </fieldset>
        </div>
        {editor_footer(result.revision.value, "Create encounter")}
      </form>
    """
    return render_page(
        title=f"New encounter — {result.adventure.title}",
        project_label=project_label,
        adventure=result.adventure,
        report=result.validation_report,
        current_kind="structure",
        current_id=None,
        body=body,
        related_issues=(),
        revision=result.revision.value,
        editing=True,
    )


def render_encounter_edit(
    result: EncounterDetailResult,
    project_label: str,
    *,
    csrf_token: str,
    draft_key: str,
    values: EncounterEditValues | None = None,
    notice: PageNotice | None = None,
    server_values: bool = False,
) -> str:
    """Render an explicit-save encounter editor with revision and draft metadata."""
    adventure = result.adventure
    encounter = result.detail.encounter
    form = values or EncounterEditValues.from_result(result)
    required_checked = " checked" if form.required else ""
    start_checked = " checked" if form.start else ""
    end_checked = " checked" if form.end else ""
    revision_warning_html = revision_warning(form.expected_revision, result.revision.value)
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading">
        <div><p class="eyebrow">Edit encounter</p><h1>{escape_html(encounter.title)}</h1></div>
        <a class="button secondary" href="{entity_url("encounter", encounter.id)}">Cancel</a>
      </div>
      {render_encounter_reference_links(result, csrf_token=None, include_controls=False)}
      <form class="editor-form" method="post" action="{entity_url("encounter", encounter.id)}/edit"
            data-authoring-form data-encounter-editor data-draft-key="{escape_html(draft_key)}"
            data-current-revision="{escape_html(result.revision.value)}"
            data-save-label="Save encounter" data-server-values="{"true" if server_values else "false"}" data-cancel-href="{entity_url("encounter", encounter.id)}">
        {form_hidden(csrf_token, form.expected_revision)}
        {editor_toolbar("Authored encounter", "Save encounter")}
        {revision_warning_html}
        <div class="form-grid">
          <label class="field" for="title"><span>Title</span><input id="title" name="title" value="{escape_html(form.title)}" data-draft-field></label>
          <label class="field" for="summary"><span>GM orientation <small>Encounter synopsis</small></span><textarea id="summary" name="summary" rows="4" data-draft-field>{escape_html(form.summary)}</textarea></label>
          <label class="field field-wide" for="opening_view"><span>Opening description <small>Player-facing Markdown</small></span><textarea id="opening_view" name="opening_view" rows="8" data-draft-field>{escape_html(form.opening_view)}</textarea></label>
          <label class="field field-wide" for="content"><span>Encounter material <small>Markdown</small></span><textarea class="content-editor" id="content" name="content" rows="26" data-draft-field>{escape_html(form.content)}</textarea></label>
          <label class="field field-wide" for="tags"><span>Tags <small>Comma-separated</small></span><input id="tags" name="tags" value="{escape_html(form.tags)}" data-draft-field></label>
          <fieldset class="field field-wide option-field"><legend>Necessity</legend>
            <label><input type="checkbox" name="required" value="1" data-draft-field{required_checked}> Necessary encounter</label>
            <small>Optional encounters still need at least one incoming lead, but they are exempt from configured incoming-lead minimums.</small>
          </fieldset>
          <fieldset class="field field-wide option-field"><legend>Encounter role</legend>
            <label><input type="checkbox" name="start" value="1" data-draft-field{start_checked}> Start encounter</label>
            <label><input type="checkbox" name="end" value="1" data-draft-field{end_checked}> End encounter</label>
          </fieldset>
        </div>
        {editor_footer(result.revision.value, "Save encounter")}
      </form>
    """
    return render_page(
        title=f"Edit {encounter.title} — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="encounter",
        current_id=encounter.id,
        body=body,
        related_issues=result.detail.validation_issues,
        revision=result.revision.value,
        editing=True,
    )


def render_encounter_remove(
    result: EncounterDetailResult,
    project_label: str,
    *,
    csrf_token: str,
    notice: PageNotice | None = None,
) -> str:
    """Render encounter dependency effects and explicit cascade confirmation."""
    encounter = result.detail.encounter
    preview = result.detail.dependency_preview
    has_authored_dependencies = bool(preview.removal_dependencies)
    has_journal_references = bool(preview.journal_references)
    cascade = (
        '<label class="confirmation-check"><input type="checkbox" name="cascade" value="1" required> '
        "I understand that the listed leads and reference links will be removed, and revelation "
        "destinations will be cleared.</label>"
        if has_authored_dependencies
        else ""
    )
    if has_journal_references:
        action = (
            '<section class="notice error"><strong>Removal blocked by play history.</strong>'
            "<p>Resolve or archive the listed journal references before removing this encounter.</p>"
            "</section>"
        )
    else:
        action = f"""
          <form method="post" action="{entity_url("encounter", encounter.id)}/remove">
            {form_hidden(csrf_token, result.revision.value)}
            {cascade}
            <button class="button danger" type="submit">Remove encounter</button>
          </form>
        """
    dependency_copy = (
        "This encounter has authored dependencies and requires an explicit cascade."
        if has_authored_dependencies
        else "This encounter has no authored dependencies and may be removed directly."
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row">
        <div><p class="eyebrow">Remove encounter</p><h1>{escape_html(encounter.title)}</h1></div>
        <a class="button secondary" href="{entity_url("encounter", encounter.id)}">Cancel</a>
      </div>
      {dependency_section(preview, "encounter")}
      <section class="section danger-zone">
        <div class="section-heading"><h2>Permanent structural change</h2><span>Reference records themselves are retained</span></div>
        <p>{dependency_copy}</p>
        {action}
      </section>
    """
    return render_page(
        title=f"Remove {encounter.title} — {result.adventure.title}",
        project_label=project_label,
        adventure=result.adventure,
        report=result.validation_report,
        current_kind="encounter",
        current_id=encounter.id,
        body=body,
        related_issues=result.detail.validation_issues,
        revision=result.revision.value,
    )
