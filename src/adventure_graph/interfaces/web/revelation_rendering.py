"""HTML rendering for revelation detail, creation, and editing."""

from __future__ import annotations

from urllib.parse import urlencode

from adventure_graph.application.project_browsing import RevelationDetailResult
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
    MetricLink,
    entity_url,
    escape_html,
    render_badges,
    render_clue_card,
    render_empty_card,
    render_metrics,
    render_notice,
    render_page,
)
from adventure_graph.interfaces.web.view_models import (
    PageNotice,
    RevelationCreateValues,
    RevelationEditValues,
)


def render_revelation_create(
    result: StructuralOverviewResult,
    project_label: str,
    *,
    csrf_token: str,
    draft_key: str,
    values: RevelationCreateValues,
    notice: PageNotice | None = None,
    server_values: bool = False,
) -> str:
    """Render contextual revelation creation against a known project revision."""
    adventure = result.adventure
    destination_options = select_options(
        adventure.encounters,
        values.unlocks_encounter_id,
        allow_empty=True,
        empty_label="No encounter unlock",
    )
    required_checked = " checked" if values.required else ""
    clue_parameters = {"source": values.source_encounter_id}
    if values.return_to:
        clue_parameters["return_to"] = values.return_to
    cancel_href = (
        f"/clues/new?{urlencode(clue_parameters)}"
        if values.source_encounter_id
        else values.return_to or "/structure"
    )
    return_field = (
        f'<input type="hidden" name="return_to" value="{escape_html(values.return_to)}">'
        if values.return_to
        else ""
    )
    context = (
        '<p class="lede">A lead must support a revelation. Create the conclusion now, then Adventure '
        "Graph will return to the lead form with this encounter and Play context preserved.</p>"
        if values.source_encounter_id
        else ""
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading">
        <div><p class="eyebrow">{"Play improvisation" if values.return_to else "Structural authoring"}</p><h1>Add revelation</h1></div>
        <a class="button secondary" href="{escape_html(cancel_href)}">{"Back to lead" if values.source_encounter_id else "Cancel"}</a>
      </div>
      {context}
      <form class="editor-form" method="post" action="/revelations/new" data-authoring-form
            data-draft-key="{escape_html(draft_key)}" data-current-revision="{escape_html(result.revision.value)}"
            data-save-label="Create revelation" data-server-values="{"true" if server_values else "false"}" data-cancel-href="{escape_html(cancel_href)}">
        {form_hidden(csrf_token, values.expected_revision)}
        <input type="hidden" name="source_encounter_id" value="{escape_html(values.source_encounter_id)}">
        {return_field}
        {editor_toolbar("New authored revelation", "Create revelation")}
        {revision_warning(values.expected_revision, result.revision.value)}
        <div class="form-grid two-column-form">
          <label class="field" for="title"><span>Title</span><input id="title" name="title" value="{escape_html(values.title)}" data-draft-field></label>
          <label class="field" for="unlocks_encounter_id"><span>Unlocks encounter</span><select id="unlocks_encounter_id" name="unlocks_encounter_id" data-draft-field>{destination_options}</select></label>
          <fieldset class="field option-field"><legend>Necessity</legend><label><input type="checkbox" name="required" value="1" data-draft-field{required_checked}> Necessary revelation</label><small>Optional revelations need at least one supporting lead, but are exempt from configured lead and source minimums.</small></fieldset>
          <label class="field field-wide" for="description"><span>Description</span><textarea id="description" name="description" rows="10" data-draft-field>{escape_html(values.description)}</textarea></label>
        </div>
        {editor_footer(result.revision.value, "Create revelation")}
      </form>
    """
    return render_page(
        title=f"Add revelation — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="revelation-new",
        current_id=None,
        body=body,
        related_issues=(),
        revision=result.revision.value,
        editing=True,
    )


def render_revelation_edit(
    result: RevelationDetailResult,
    project_label: str,
    *,
    csrf_token: str,
    draft_key: str,
    values: RevelationEditValues | None = None,
    notice: PageNotice | None = None,
    server_values: bool = False,
) -> str:
    """Render a revision-aware revelation editor."""
    adventure = result.adventure
    revelation = result.detail.revelation
    form = values or RevelationEditValues.from_result(result)
    destination_options = select_options(
        adventure.encounters,
        form.unlocks_encounter_id,
        allow_empty=True,
        empty_label="No encounter unlock",
    )
    required_checked = " checked" if form.required else ""
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading">
        <div><p class="eyebrow">Edit revelation</p><h1>{escape_html(revelation.title)}</h1></div>
        <a class="button secondary" href="{entity_url("revelation", revelation.id)}">Cancel</a>
      </div>
      <form class="editor-form" method="post" action="{entity_url("revelation", revelation.id)}/edit" data-authoring-form
            data-draft-key="{escape_html(draft_key)}" data-current-revision="{escape_html(result.revision.value)}"
            data-save-label="Save revelation" data-server-values="{"true" if server_values else "false"}" data-cancel-href="{entity_url("revelation", revelation.id)}">
        {form_hidden(csrf_token, form.expected_revision)}
        {editor_toolbar("Authored revelation", "Save revelation")}
        {revision_warning(form.expected_revision, result.revision.value)}
        <div class="form-grid two-column-form">
          <label class="field" for="title"><span>Title</span><input id="title" name="title" value="{escape_html(form.title)}" data-draft-field></label>
          <label class="field" for="unlocks_encounter_id"><span>Unlocks encounter</span><select id="unlocks_encounter_id" name="unlocks_encounter_id" data-draft-field>{destination_options}</select></label>
          <fieldset class="field option-field"><legend>Necessity</legend><label><input type="checkbox" name="required" value="1" data-draft-field{required_checked}> Necessary revelation</label><small>Optional revelations need at least one supporting lead, but are exempt from configured lead and source minimums.</small></fieldset>
          <label class="field field-wide" for="description"><span>Description</span><textarea id="description" name="description" rows="10" data-draft-field>{escape_html(form.description)}</textarea></label>
        </div>
        {editor_footer(result.revision.value, "Save revelation")}
      </form>
    """
    return render_page(
        title=f"Edit {revelation.title} — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="revelation",
        current_id=revelation.id,
        body=body,
        related_issues=result.detail.validation_issues,
        revision=result.revision.value,
        editing=True,
    )


def render_revelation(
    result: RevelationDetailResult,
    project_label: str,
    *,
    notice: PageNotice | None = None,
    clear_draft_key: str | None = None,
) -> str:
    """Render one revelation and its clue coverage."""
    adventure = result.adventure
    detail = result.detail
    revelation = detail.revelation
    revelation_url = entity_url("revelation", revelation.id)
    revelation_edit_url = f"{revelation_url}/edit"
    destination = (
        MetricLink(
            detail.unlocks_encounter.title,
            entity_url("encounter", detail.unlocks_encounter.id),
        )
        if detail.unlocks_encounter is not None
        else "No encounter unlock"
    )
    clues = "".join(
        render_clue_card(clue, adventure, include_source=True) for clue in detail.supporting_clues
    ) or render_empty_card("No leads currently support this revelation.")
    source_count = len({clue.source_encounter_id for clue in detail.supporting_clues})
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row">
        <div><p class="eyebrow">Revelation</p><h1 class="editable-surface editable-heading" {edit_attributes(f"{revelation_edit_url}#title", "revelation title")}>{escape_html(revelation.title)}</h1></div>
        <div class="button-row"><a class="button secondary" href="/clues/new?{urlencode({"revelation": revelation.id})}">Add supporting lead</a><a class="button primary" href="{revelation_edit_url}">Edit revelation</a></div>
      </div>
      {editable_plain_text(revelation.description, f"{revelation_edit_url}#description", "revelation description", "No revelation description has been written.", class_name="lede")}
      {render_badges(("Necessary" if revelation.required else "Optional",))}
      {render_metrics(((str(len(detail.supporting_clues)), "Supporting leads"), (str(source_count), "Distinct sources"), (destination, "Unlocks")))}
      <section class="section">
        <div class="section-heading"><h2>Supporting leads</h2><span>{len(detail.supporting_clues)} authored</span></div>
        <div class="card-grid">{clues}</div>
      </section>
      {dependency_section(detail.dependency_preview, "revelation")}
    """
    return render_page(
        title=f"{revelation.title} — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="revelation",
        current_id=revelation.id,
        body=body,
        related_issues=detail.validation_issues,
        revision=result.revision.value,
        clear_draft_key=clear_draft_key,
    )
