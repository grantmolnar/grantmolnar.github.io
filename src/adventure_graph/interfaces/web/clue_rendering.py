"""Render persisted ``Clue`` records as user-facing leads."""

from __future__ import annotations

from urllib.parse import urlencode

from adventure_graph.application.project_browsing import ClueDetailResult
from adventure_graph.application.structural_authoring import StructuralOverviewResult
from adventure_graph.interfaces.web.authoring_rendering_support import (
    dependency_section,
    edit_attributes,
    editable_plain_text,
    editor_footer,
    editor_toolbar,
    form_hidden,
    revision_warning,
    select_options,
)
from adventure_graph.interfaces.web.page_rendering import (
    entity_url,
    escape_html,
    render_badges,
    render_notice,
    render_page,
    render_pathway_step,
)
from adventure_graph.interfaces.web.view_models import (
    ClueCreateValues,
    ClueEditValues,
    PageNotice,
)


def render_clue_create(
    result: StructuralOverviewResult,
    project_label: str,
    *,
    csrf_token: str,
    draft_key: str,
    values: ClueCreateValues,
    notice: PageNotice | None = None,
    server_values: bool = False,
) -> str:
    """Render contextual clue creation against a known project revision."""
    adventure = result.adventure
    source_options = select_options(
        adventure.encounters, values.source_encounter_id, allow_empty=True
    )
    revelation_options = select_options(
        adventure.revelations,
        values.revelation_id,
        allow_empty=True,
    )
    cancel_href = values.return_to or "/structure"
    return_field = (
        f'<input type="hidden" name="return_to" value="{escape_html(values.return_to)}">'
        if values.return_to
        else ""
    )
    revelation_parameters = {"source": values.source_encounter_id}
    if values.return_to:
        revelation_parameters["return_to"] = values.return_to
    revelation_href = f"/revelations/new?{urlencode(revelation_parameters)}"
    context = (
        '<p class="lede">Add a lead to the focused encounter without changing the current visit or '
        "play history. Saving returns directly to the Table workspace.</p>"
        if values.return_to
        else ""
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading">
        <div><p class="eyebrow">{"Play improvisation" if values.return_to else "Structural authoring"}</p><h1>{"Add a lead during play" if values.return_to else "Add lead"}</h1></div>
        <a class="button secondary" href="{escape_html(cancel_href)}">{"Back to table" if values.return_to else "Cancel"}</a>
      </div>
      {context}
      <form class="editor-form" method="post" action="/clues/new" data-authoring-form
            data-draft-key="{escape_html(draft_key)}" data-current-revision="{escape_html(result.revision.value)}"
            data-save-label="Create lead" data-server-values="{"true" if server_values else "false"}" data-cancel-href="{escape_html(cancel_href)}">
        {form_hidden(csrf_token, values.expected_revision)}
        {return_field}
        {editor_toolbar("New authored lead", "Create lead")}
        {revision_warning(values.expected_revision, result.revision.value)}
        <div class="form-grid two-column-form">
          <label class="field" for="title"><span>Title</span><input id="title" name="title" value="{escape_html(values.title)}" data-draft-field></label>
          <label class="field" for="source_encounter_id"><span>Source encounter</span><select id="source_encounter_id" name="source_encounter_id" data-draft-field>{source_options}</select></label>
          <label class="field" for="revelation_id"><span>Supported revelation</span><select id="revelation_id" name="revelation_id" data-draft-field>{revelation_options}</select><small>Need a new conclusion? <a href="{escape_html(revelation_href)}">Create a revelation first</a>.</small></label>
          <label class="field" for="discovery"><span>Discovery mode</span><input id="discovery" name="discovery" value="{escape_html(values.discovery)}" data-draft-field></label>
          <label class="field field-wide" for="description"><span>Description</span><textarea id="description" name="description" rows="8" data-draft-field>{escape_html(values.description)}</textarea></label>
        </div>
        {editor_footer(result.revision.value, "Create lead")}
      </form>
    """
    return render_page(
        title=f"Add lead — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="clue-new",
        current_id=None,
        body=body,
        related_issues=(),
        revision=result.revision.value,
        editing=True,
    )


def render_clue_edit(
    result: ClueDetailResult,
    project_label: str,
    *,
    csrf_token: str,
    draft_key: str,
    values: ClueEditValues | None = None,
    notice: PageNotice | None = None,
    server_values: bool = False,
) -> str:
    """Render a revision-aware clue editor."""
    adventure = result.adventure
    clue = result.detail.clue
    form = values or ClueEditValues.from_result(result)
    source_options = select_options(
        adventure.encounters, form.source_encounter_id, allow_empty=False
    )
    revelation_options = select_options(
        adventure.revelations,
        form.revelation_id,
        allow_empty=False,
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading">
        <div><p class="eyebrow">Edit lead</p><h1>{escape_html(clue.title)}</h1></div>
        <a class="button secondary" href="{entity_url("clue", clue.id)}">Cancel</a>
      </div>
      <form class="editor-form" method="post" action="{entity_url("clue", clue.id)}/edit" data-authoring-form
            data-draft-key="{escape_html(draft_key)}" data-current-revision="{escape_html(result.revision.value)}"
            data-save-label="Save lead" data-server-values="{"true" if server_values else "false"}" data-cancel-href="{entity_url("clue", clue.id)}">
        {form_hidden(csrf_token, form.expected_revision)}
        {editor_toolbar("Authored lead", "Save lead")}
        {revision_warning(form.expected_revision, result.revision.value)}
        <div class="form-grid two-column-form">
          <label class="field" for="title"><span>Title</span><input id="title" name="title" value="{escape_html(form.title)}" data-draft-field></label>
          <label class="field" for="source_encounter_id"><span>Source encounter</span><select id="source_encounter_id" name="source_encounter_id" data-draft-field>{source_options}</select></label>
          <label class="field" for="revelation_id"><span>Supported revelation</span><select id="revelation_id" name="revelation_id" data-draft-field>{revelation_options}</select></label>
          <label class="field" for="discovery"><span>Discovery mode</span><input id="discovery" name="discovery" value="{escape_html(form.discovery)}" data-draft-field></label>
          <label class="field field-wide" for="description"><span>Description</span><textarea id="description" name="description" rows="8" data-draft-field>{escape_html(form.description)}</textarea></label>
        </div>
        {editor_footer(result.revision.value, "Save lead")}
      </form>
    """
    return render_page(
        title=f"Edit {clue.title} — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="clue",
        current_id=clue.id,
        body=body,
        related_issues=result.detail.validation_issues,
        revision=result.revision.value,
        editing=True,
    )


def render_clue(
    result: ClueDetailResult,
    project_label: str,
    *,
    notice: PageNotice | None = None,
    clear_draft_key: str | None = None,
) -> str:
    """Render one clue and its direct source-to-destination pathway."""
    adventure = result.adventure
    detail = result.detail
    clue = detail.clue
    clue_url = entity_url("clue", clue.id)
    clue_edit_url = f"{clue_url}/edit"
    destination = (
        render_pathway_step(
            "Destination",
            detail.destination_encounter.title,
            "encounter",
            detail.destination_encounter.id,
        )
        if detail.destination_encounter is not None
        else render_pathway_step("Conclusion", "No encounter unlock", None, None)
    )
    pathway = f"""
      <div class="pathway">
        {render_pathway_step("Source encounter", detail.source_encounter.title, "encounter", detail.source_encounter.id)}
        <div class="pathway-arrow" aria-hidden="true">→</div>
        {render_pathway_step("Revelation", detail.revelation.title, "revelation", detail.revelation.id)}
        <div class="pathway-arrow" aria-hidden="true">→</div>
        {destination}
      </div>
    """
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row">
        <div><p class="eyebrow">Lead</p><h1 class="editable-surface editable-heading" {edit_attributes(f"{clue_edit_url}#title", "lead title")}>{escape_html(clue.title)}</h1></div>
        <a class="button primary" href="{clue_edit_url}">Edit lead</a>
      </div>
      {editable_plain_text(clue.description, f"{clue_edit_url}#description", "lead description", "No expanded lead description has been written.", class_name="lede")}
      {render_badges((clue.discovery,))}
      <section class="section">
        <div class="section-heading"><h2>Authored pathway</h2><span>Source → conclusion → destination</span></div>
        {pathway}
      </section>
      {dependency_section(detail.dependency_preview, "lead")}
    """
    return render_page(
        title=f"{clue.title} — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="clue",
        current_id=clue.id,
        body=body,
        related_issues=detail.validation_issues,
        revision=result.revision.value,
        clear_draft_key=clear_draft_key,
    )
