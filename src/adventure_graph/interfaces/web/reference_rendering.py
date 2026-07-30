"""HTML rendering for the adventure-owned reference library."""

from __future__ import annotations

from urllib.parse import quote, urlencode

from adventure_graph.application.encounter_authoring import EncounterDetailResult
from adventure_graph.application.project_browsing import AdventureOverviewResult
from adventure_graph.application.reference_authoring import ReferenceDetailResult
from adventure_graph.domain.adventure import Adventure, Reference, ReferenceKind
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
    escape_html,
    render_badges,
    render_empty_card,
    render_notice,
    render_page,
)
from adventure_graph.interfaces.web.view_models import (
    PageNotice,
    ReferenceCreateValues,
    ReferenceEditValues,
)

REFERENCE_KINDS: tuple[ReferenceKind, ...] = (
    "person",
    "place",
    "organization",
    "object",
    "other",
)


def render_reference_library(
    result: AdventureOverviewResult,
    project_label: str,
    *,
    kind_filter: str = "",
    notice: PageNotice | None = None,
) -> str:
    """Render one unified reference collection with kind-based views."""
    adventure = result.adventure
    selected = kind_filter if kind_filter in REFERENCE_KINDS else ""
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row">
        <div><p class="eyebrow">Adventure reference library</p><h1>References</h1></div>
        <a class="button primary" href="/references/new">Add reference</a>
      </div>
      <p class="lede">Maintain recurring people, places, organizations, objects, and other subjects without making them encounter graph units.</p>
      {_kind_filters(adventure, selected)}
      {_reference_groups(adventure, selected)}
    """
    return render_page(
        title=f"References — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="references",
        current_id=None,
        body=body,
        related_issues=tuple(
            issue
            for issue in result.validation_report.issues
            if issue.subject_id in adventure.reference_index()
        ),
        revision=result.revision.value,
    )


def render_reference(
    result: ReferenceDetailResult,
    project_label: str,
    *,
    notice: PageNotice | None = None,
    clear_draft_key: str | None = None,
) -> str:
    """Render one canonical reference with derived encounter backlinks."""
    adventure = result.adventure
    detail = result.detail
    reference = detail.reference
    reference_url = _reference_url(reference.id)
    aliases = (
        f'<p class="reference-aliases"><strong>Also known as:</strong> '
        f"{escape_html(', '.join(reference.aliases))}</p>"
        if reference.aliases
        else '<p class="muted-note">No alternate names.</p>'
    )
    backlinks = "".join(
        _backlink_card(backlink.encounter.id, backlink.encounter.title, backlink.context)
        for backlink in detail.backlinks
    ) or render_empty_card(
        "No encounters link this reference. The record remains valid as adventure-owned context."
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row">
        <div><p class="eyebrow">{escape_html(reference.kind.title())} reference</p><h1 class="editable-surface editable-heading" {edit_attributes(f"{reference_url}/edit#title", "reference title")}>{escape_html(reference.title)}</h1></div>
        <div class="button-row">
          <a class="button secondary" href="{reference_url}/remove">Remove reference</a>
          <a class="button primary" href="{reference_url}/edit">Edit reference</a>
        </div>
      </div>
      {render_badges((reference.kind.title(), *reference.tags))}
      {aliases}
      <section class="section">
        <div class="section-heading"><h2>Summary</h2><span>At-a-glance GM context</span></div>
        {editable_plain_text(reference.summary, f"{reference_url}/edit#summary", "reference summary", "No reference summary has been written.", class_name="lede")}
      </section>
      <section class="section">
        <div class="section-heading"><h2>Reference material</h2><span>Markdown</span></div>
        {editable_markdown(reference.content, f"{reference_url}/edit#content", "reference material", "No detailed reference material has been written.")}
      </section>
      <section class="section">
        <div class="section-heading"><h2>Encounter backlinks</h2><span>{len(detail.backlinks)} linked encounters</span></div>
        <div class="card-grid">{backlinks}</div>
      </section>
      {dependency_section(detail.dependency_preview, "reference")}
    """
    return render_page(
        title=f"{reference.title} — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="reference",
        current_id=reference.id,
        body=body,
        related_issues=detail.validation_issues,
        revision=result.revision.value,
        clear_draft_key=clear_draft_key,
    )


def render_reference_create(
    result: AdventureOverviewResult,
    project_label: str,
    *,
    csrf_token: str,
    draft_key: str,
    values: ReferenceCreateValues | None = None,
    notice: PageNotice | None = None,
    server_values: bool = False,
) -> str:
    """Render standalone or contextual atomic reference creation."""
    form = values or ReferenceCreateValues(expected_revision=result.revision.value)
    encounter = result.adventure.encounter_index().get(form.encounter_id)
    contextual = encounter is not None
    default_cancel_href = (
        f"/encounters/{quote(encounter.id, safe='')}" if encounter is not None else "/references"
    )
    cancel_href = form.return_to or default_cancel_href
    heading = (
        f"Create and link a reference for {escape_html(encounter.title)}"
        if encounter is not None
        else "Add a reference"
    )
    if encounter is not None:
        context_fields = f"""
          <input type="hidden" name="encounter_id" value="{escape_html(encounter.id)}">
          <label class="field field-wide" for="context"><span>Encounter relevance <small>Local to {escape_html(encounter.title)}</small></span><textarea id="context" name="context" rows="4" data-draft-field>{escape_html(form.context)}</textarea></label>
        """
    else:
        context_fields = """
          <input type="hidden" name="encounter_id" value="">
          <input type="hidden" name="context" value="">
        """
    return_field = f'<input type="hidden" name="return_to" value="{escape_html(form.return_to)}">'
    eyebrow = (
        "Play improvisation"
        if form.return_to
        else "Contextual reference"
        if contextual
        else "New reference"
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading">
        <div><p class="eyebrow">{eyebrow}</p><h1>{heading}</h1></div>
        <a class="button secondary" href="{escape_html(cancel_href)}">Cancel</a>
      </div>
      <form class="editor-form" method="post" action="/references/new" data-authoring-form
            data-draft-key="{escape_html(draft_key)}" data-current-revision="{escape_html(result.revision.value)}"
            data-save-label="Create reference" data-server-values="{"true" if server_values else "false"}"
            data-cancel-href="{escape_html(cancel_href)}">
        {form_hidden(csrf_token, form.expected_revision)}
        {return_field}
        {editor_toolbar("Adventure reference", "Create reference")}
        {revision_warning(form.expected_revision, result.revision.value)}
        <div class="form-grid">
          {_reference_fields(form)}
          {context_fields}
        </div>
        {editor_footer(result.revision.value, "Create reference")}
      </form>
    """
    return render_page(
        title=f"New reference — {result.adventure.title}",
        project_label=project_label,
        adventure=result.adventure,
        report=result.validation_report,
        current_kind="references",
        current_id=None,
        body=body,
        related_issues=(),
        revision=result.revision.value,
        editing=True,
    )


def render_reference_edit(
    result: ReferenceDetailResult,
    project_label: str,
    *,
    csrf_token: str,
    draft_key: str,
    values: ReferenceEditValues | None = None,
    notice: PageNotice | None = None,
    server_values: bool = False,
) -> str:
    """Render one reference editor without exposing stable identity as editable."""
    reference = result.detail.reference
    form = values or ReferenceEditValues.from_result(result)
    reference_url = _reference_url(reference.id)
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row editor-heading">
        <div><p class="eyebrow">Edit reference</p><h1>{escape_html(reference.title)}</h1></div>
        <a class="button secondary" href="{reference_url}">Cancel</a>
      </div>
      <p class="form-help">Stable identity: <code>{escape_html(reference.id)}</code>. Titles and aliases may change without breaking encounter links.</p>
      <form class="editor-form" method="post" action="{reference_url}/edit" data-authoring-form
            data-draft-key="{escape_html(draft_key)}" data-current-revision="{escape_html(result.revision.value)}"
            data-save-label="Save reference" data-server-values="{"true" if server_values else "false"}"
            data-cancel-href="{reference_url}">
        {form_hidden(csrf_token, form.expected_revision)}
        {editor_toolbar("Adventure reference", "Save reference")}
        {revision_warning(form.expected_revision, result.revision.value)}
        <div class="form-grid">{_reference_fields(form)}</div>
        {editor_footer(result.revision.value, "Save reference")}
      </form>
      {_linked_reference_summary(result)}
    """
    return render_page(
        title=f"Edit {reference.title} — {result.adventure.title}",
        project_label=project_label,
        adventure=result.adventure,
        report=result.validation_report,
        current_kind="reference",
        current_id=reference.id,
        body=body,
        related_issues=result.detail.validation_issues,
        revision=result.revision.value,
        editing=True,
    )


def render_reference_remove(
    result: ReferenceDetailResult,
    project_label: str,
    *,
    csrf_token: str,
    notice: PageNotice | None = None,
) -> str:
    """Render exact dependency effects before removing one reference."""
    reference = result.detail.reference
    preview = result.detail.dependency_preview
    has_authored_dependencies = bool(preview.removal_dependencies)
    has_journal_references = bool(preview.journal_references)
    cascade = (
        '<label class="confirmation-check"><input type="checkbox" name="cascade" value="1" required> '
        "I understand that every listed encounter link will be removed with this reference.</label>"
        if has_authored_dependencies
        else ""
    )
    if has_journal_references:
        action = (
            '<section class="notice error"><strong>Removal blocked by play history.</strong>'
            "<p>This stable reference identity is used by the listed playthrough notes. "
            "Correct or replace that play history before removing the authored reference.</p>"
            "</section>"
        )
    else:
        action = f"""
          <form method="post" action="{_reference_url(reference.id)}/remove">
            {form_hidden(csrf_token, result.revision.value)}
            {cascade}
            <button class="button danger" type="submit">Remove reference</button>
          </form>
        """
    dependency_copy = (
        "This reference has authored links and requires an explicit cascade."
        if has_authored_dependencies
        else "This reference has no authored links and may be removed directly."
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row">
        <div><p class="eyebrow">Remove reference</p><h1>{escape_html(reference.title)}</h1></div>
        <a class="button secondary" href="{_reference_url(reference.id)}">Cancel</a>
      </div>
      {dependency_section(preview, "reference")}
      <section class="section danger-zone">
        <div class="section-heading"><h2>Permanent authored change</h2><span>Reference identity cannot be recovered automatically</span></div>
        <p>{dependency_copy}</p>
        {action}
      </section>
    """
    return render_page(
        title=f"Remove {reference.title} — {result.adventure.title}",
        project_label=project_label,
        adventure=result.adventure,
        report=result.validation_report,
        current_kind="reference",
        current_id=reference.id,
        body=body,
        related_issues=result.detail.validation_issues,
        revision=result.revision.value,
    )


def render_encounter_reference_links(
    result: EncounterDetailResult,
    *,
    csrf_token: str | None,
    include_controls: bool,
) -> str:
    """Render ordered linked references for encounter detail and edit views."""
    detail = result.detail
    adventure = result.adventure
    cards: list[str] = []
    for linked in detail.linked_references:
        reference = linked.reference
        if reference is None:
            cards.append(
                f'<article class="card issue error"><h3>Missing reference</h3><p>{escape_html(linked.reference_id)}</p></article>'
            )
            continue
        controls = ""
        if include_controls and csrf_token is not None:
            controls = f"""
              <form method="post" action="/encounters/{quote(detail.encounter.id, safe="")}/references/unlink" class="inline-form">
                {form_hidden(csrf_token, result.revision.value)}
                <input type="hidden" name="reference_id" value="{escape_html(reference.id)}">
                <button class="text-button" type="submit">Unlink</button>
              </form>
            """
        cards.append(
            f"""
              <article class="card reference-link-card">
                <p class="eyebrow">{escape_html(reference.kind.title())}</p>
                <h3><a href="{_reference_url(reference.id)}">{escape_html(reference.title)}</a></h3>
                <p>{escape_html(linked.context) if linked.context else '<span class="muted-note">No encounter-specific context.</span>'}</p>
                {controls}
              </article>
            """
        )
    linked_ids = {item.reference_id for item in detail.linked_references}
    available = tuple(
        reference for reference in adventure.references if reference.id not in linked_ids
    )
    controls = ""
    if include_controls and csrf_token is not None:
        options = "".join(
            f'<option value="{escape_html(reference.id)}">{escape_html(reference.title)} — {escape_html(reference.kind)}</option>'
            for reference in available
        )
        existing_form = (
            f"""
              <form class="compact-authoring-form" method="post" action="/encounters/{quote(detail.encounter.id, safe="")}/references/link">
                {form_hidden(csrf_token, result.revision.value)}
                <label class="field" for="reference_id"><span>Existing reference</span><select id="reference_id" name="reference_id" required><option value="">Select…</option>{options}</select></label>
                <label class="field" for="reference_context"><span>Encounter relevance</span><textarea id="reference_context" name="context" rows="3"></textarea></label>
                <button class="button secondary" type="submit">Link reference</button>
              </form>
            """
            if available
            else '<p class="muted-note">Every existing reference is already linked here.</p>'
        )
        create_query = urlencode({"encounter": detail.encounter.id})
        controls = f"""
          <div class="reference-link-actions">
            {existing_form}
            <a class="button secondary" href="/references/new?{create_query}">Create and link new reference</a>
          </div>
        """
    content = "".join(cards) or render_empty_card(
        "No references are linked to this encounter. Link only recurring subjects that deserve canonical adventure context."
    )
    return f"""
      <section class="section encounter-reference-section">
        <div class="section-heading"><h2>Linked references</h2><span>{len(detail.linked_references)} in authored order</span></div>
        <div class="card-grid">{content}</div>
        {controls}
      </section>
    """


def _reference_fields(form: ReferenceCreateValues | ReferenceEditValues) -> str:
    options = "".join(
        f'<option value="{kind}"{" selected" if form.kind == kind else ""}>{kind.title()}</option>'
        for kind in REFERENCE_KINDS
    )
    return f"""
      <label class="field" for="kind"><span>Kind</span><select id="kind" name="kind" data-draft-field>{options}</select></label>
      <label class="field" for="title"><span>Title</span><input id="title" name="title" value="{escape_html(form.title)}" required data-draft-field></label>
      <label class="field field-wide" for="aliases"><span>Aliases <small>Comma-separated alternate names</small></span><input id="aliases" name="aliases" value="{escape_html(form.aliases)}" data-draft-field></label>
      <label class="field field-wide" for="summary"><span>Summary <small>At-a-glance GM context</small></span><textarea id="summary" name="summary" rows="5" data-draft-field>{escape_html(form.summary)}</textarea></label>
      <label class="field field-wide" for="content"><span>Reference material <small>Markdown</small></span><textarea class="content-editor" id="content" name="content" rows="22" data-draft-field>{escape_html(form.content)}</textarea></label>
      <label class="field field-wide" for="tags"><span>Tags <small>Comma-separated authored-search labels</small></span><input id="tags" name="tags" value="{escape_html(form.tags)}" data-draft-field></label>
    """


def _kind_filters(adventure: Adventure, selected: str) -> str:
    counts = {
        kind: sum(reference.kind == kind for reference in adventure.references)
        for kind in REFERENCE_KINDS
    }
    links = [
        f'<a class="button {"primary" if not selected else "secondary"}" href="/references">All <span>{len(adventure.references)}</span></a>'
    ]
    links.extend(
        f'<a class="button {"primary" if selected == kind else "secondary"}" href="/references?{urlencode({"kind": kind})}">{kind.title()} <span>{counts[kind]}</span></a>'
        for kind in REFERENCE_KINDS
    )
    return f'<nav class="filter-row" aria-label="Reference kind">{"".join(links)}</nav>'


def _reference_groups(adventure: Adventure, selected: str) -> str:
    if not adventure.references:
        return """
          <section class="section reference-empty-state">
            <div class="section-heading"><h2>No reference records</h2><span>Reference-light adventures are valid</span></div>
            <p>Create a reference only when a person, place, organization, object, or other subject recurs across encounters or needs canonical adventure context.</p>
            <a class="button primary" href="/references/new">Add the first reference</a>
          </section>
        """
    kinds = (selected,) if selected else REFERENCE_KINDS
    groups: list[str] = []
    backlinks = {
        reference.id: sum(
            link.reference_id == reference.id
            for encounter in adventure.encounters
            for link in encounter.reference_links
        )
        for reference in adventure.references
    }
    for kind in kinds:
        references = tuple(
            reference for reference in adventure.references if reference.kind == kind
        )
        if not references:
            groups.append(
                f"""
                  <section class="section">
                    <div class="section-heading"><h2>{escape_html(kind.title())}</h2><span>0 authored</span></div>
                    {render_empty_card(f"No {kind} references. This filter does not imply that one is required.")}
                  </section>
                """
            )
            continue
        cards = "".join(
            _reference_card(reference, backlinks[reference.id]) for reference in references
        )
        groups.append(
            f"""
              <section class="section">
                <div class="section-heading"><h2>{escape_html(kind.title())}</h2><span>{len(references)} authored</span></div>
                <div class="card-grid">{cards}</div>
              </section>
            """
        )
    return "".join(groups)


def _reference_card(reference: Reference, backlink_count: int) -> str:
    aliases = (
        f'<p class="muted-note">Aliases: {escape_html(", ".join(reference.aliases))}</p>'
        if reference.aliases
        else ""
    )
    tags = "".join(
        f'<span class="tag-chip subtle">{escape_html(tag)}</span>' for tag in reference.tags
    )
    return f"""
      <article class="card reference-card">
        <p class="eyebrow">{escape_html(reference.kind.title())}</p>
        <h3><a href="{_reference_url(reference.id)}">{escape_html(reference.title)}</a></h3>
        <p>{escape_html(reference.summary) if reference.summary else '<span class="muted-note">No summary.</span>'}</p>
        {aliases}
        <div class="tag-list">{tags}</div>
        <p class="card-meta">{backlink_count} linked encounter{"s" if backlink_count != 1 else ""}</p>
      </article>
    """


def _backlink_card(encounter_id: str, title: str, context: str) -> str:
    return f"""
      <article class="card">
        <p class="eyebrow">Encounter backlink</p>
        <h3><a href="/encounters/{quote(encounter_id, safe="")}">{escape_html(title)}</a></h3>
        <p>{escape_html(context) if context else '<span class="muted-note">No encounter-specific context.</span>'}</p>
      </article>
    """


def _linked_reference_summary(result: ReferenceDetailResult) -> str:
    backlinks = "".join(
        _backlink_card(backlink.encounter.id, backlink.encounter.title, backlink.context)
        for backlink in result.detail.backlinks
    ) or render_empty_card("No encounters currently link this reference.")
    return f"""
      <section class="section">
        <div class="section-heading"><h2>Links preserved while editing</h2><span>{len(result.detail.backlinks)} backlinks</span></div>
        <div class="card-grid">{backlinks}</div>
      </section>
    """


def _reference_url(reference_id: str) -> str:
    return f"/references/{quote(reference_id, safe='')}"
