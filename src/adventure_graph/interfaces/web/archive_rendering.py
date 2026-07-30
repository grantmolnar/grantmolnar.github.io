"""HTML rendering for the journal-archive workspace."""

from __future__ import annotations

from urllib.parse import quote

from adventure_graph.application.archive_management import (
    MAX_ARCHIVE_ID_LENGTH,
    ArchiveCatalogResult,
    ArchiveDetailResult,
    EntityComparison,
)
from adventure_graph.application.run_workspace import RunDashboardResult
from adventure_graph.interfaces.web.page_rendering import (
    escape_html,
    render_empty_card,
    render_metrics,
    render_notice,
)
from adventure_graph.interfaces.web.play_rendering import render_play_workspace_page
from adventure_graph.interfaces.web.transfer_forms import MAX_PORTABLE_DOCUMENT_BYTES
from adventure_graph.interfaces.web.view_models import PageNotice


def render_archive_catalog(
    result: ArchiveCatalogResult,
    project_label: str,
    *,
    csrf_token: str,
    dashboard: RunDashboardResult,
    notice: PageNotice | None = None,
) -> str:
    """Render archive creation controls and the immutable archive catalog."""
    del project_label
    size_mib = MAX_PORTABLE_DOCUMENT_BYTES // (1024 * 1024)
    cards = "".join(
        f'<a class="archive-card" href="/archives/{quote(archive.archive_id, safe="")}">'
        f'<span class="card-kicker">{escape_html(archive.archived_at)}</span>'
        f"<h3>{escape_html(archive.label or archive.archive_id)}</h3>"
        f"<p>{archive.event_count} events · {archive.visit_count} visits · "
        f"{archive.correction_count} corrections</p>"
        f"<code>{escape_html(archive.archive_id)}</code></a>"
        for archive in result.archives
    ) or render_empty_card("No journal archives have been created yet.")
    archive_form = (
        f"""
        <form method="post" action="/archives/create" class="archive-create-form">
          <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}">
          <input type="hidden" name="expected_revision" value="{escape_html(result.revision.value)}">
          <label class="field"><span>Archive label</span><input type="text" name="label" placeholder="Session 4 — The Deep Bell"></label>
          <label class="field"><span>Optional archive identifier</span><input type="text" name="name" placeholder="deep-bell-finale" maxlength="{MAX_ARCHIVE_ID_LENGTH}" aria-describedby="archive-identifier-help"><small id="archive-identifier-help">Up to {MAX_ARCHIVE_ID_LENGTH} letters, digits, periods, underscores, or hyphens, beginning with a letter or digit. Leave blank to derive one from the timestamp and label.</small></label>
          <div class="page-heading-actions"><button class="button secondary" type="submit" formaction="/archives/export-active">Export current playthrough</button><button class="button primary" type="submit">Archive and reset journal</button></div>
        </form>
        """
        if result.active_event_count
        else (
            '<p class="muted-note">The active journal is empty. Record play before '
            "exporting or archiving it.</p>"
        )
    )
    active_explanation = (
        "Export it, or archive it and begin a fresh journal"
        if result.active_event_count
        else "No play has been recorded yet"
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row"><div><p class="eyebrow">Archive workspace</p><h1>Journal archives</h1></div></div>
      <p class="lede">Saved copies of play history kept with the version of the adventure used at the time.</p>
      {render_metrics(((str(result.active_event_count), "Current journal entries"), (str(len(result.archives)), "Archives")))}
      <section class="section no-print"><div class="section-heading"><h2>Current playthrough</h2><span>{active_explanation}</span></div>{archive_form}</section>
      <section class="section no-print"><div class="section-heading"><h2>Import for this adventure</h2><span>Add a portable playthrough to {escape_html(result.adventure.title)}</span></div>
        <form method="post" action="/archives/import" enctype="multipart/form-data" class="archive-create-form archive-import-form">
          <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}"><input type="hidden" name="expected_revision" value="{escape_html(result.revision.value)}">
          <label class="field"><span>Playthrough JSON file</span><input type="file" name="archive_file" accept="application/json,.json" aria-describedby="selected-playthrough-import-help" required><small id="selected-playthrough-import-help">Choose one canonical JSON document up to {size_mib} MiB. Its adventure identity must match this adventure.</small></label>
          <button class="button primary" type="submit">Import for this adventure</button>
        </form>
      </section>
      <section class="section"><div class="section-heading"><h2>Archive catalog</h2><span>{len(result.archives)} stored</span></div><div class="archive-grid">{cards}</div></section>
    """
    return render_play_workspace_page(
        dashboard,
        csrf_token=csrf_token,
        title=f"Archives — {result.adventure.title}",
        current_kind="archives",
        body=body,
        body_class="archives-body",
    )


def render_archive_detail(
    result: ArchiveDetailResult,
    project_label: str,
    *,
    csrf_token: str,
    dashboard: RunDashboardResult,
    notice: PageNotice | None = None,
    delete_confirmation: str = "",
) -> str:
    """Render one archive, its authored comparison, and guarded mutations."""
    del project_label
    archive = result.archive
    comparison = result.comparison
    compatibility_class = "success" if comparison.compatible else "error"
    restore_disabled = "" if result.can_restore else " disabled"
    restore_help = (
        "This archive can replace the empty active journal while remaining preserved here."
        if result.can_restore
        else (
            "Archive the active journal before restoring this one."
            if result.active_event_count
            else comparison.compatibility_message
        )
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row"><div><p class="eyebrow">Journal archive</p><h1>{escape_html(archive.label or archive.archive_id)}</h1></div><div class="page-heading-actions no-print"><a class="button secondary" href="/archives/{quote(archive.archive_id, safe="")}/download">Export playthrough</a><a class="button secondary" href="/archives">Back to archives</a></div></div>
      <p class="identifier">{escape_html(archive.archive_id)}</p>
      {render_metrics(((str(archive.event_count), "Events"), (str(len(archive.play_state.visits)), "Visits"), (archive.archived_at, "Archived")))}
      <div class="notice {compatibility_class}"><strong>{"Compatible" if comparison.compatible else "Incompatible"} with current adventure</strong><p>{escape_html(comparison.compatibility_message)}</p></div>
      <section class="section"><div class="section-heading"><h2>Adventure snapshot comparison</h2><span>{"Identical" if comparison.identical else "Changed since archive"}</span></div>
        <div class="comparison-grid">
          {_comparison_card("Encounters", comparison.encounters)}
          {_comparison_card("Revelations", comparison.revelations)}
          {_comparison_card("Leads", comparison.clues)}
          <div class="card"><span class="card-kicker">Adventure prose</span><h3>Top-level changes</h3><p>Title: {_yes_no(comparison.title_changed)} · Synopsis: {_yes_no(comparison.synopsis_changed)} · Premise: {_yes_no(comparison.premise_changed)} · Explanation: {_yes_no(comparison.explanation_changed)} · Tags: {_yes_no(comparison.tags_changed)}</p></div>
        </div>
      </section>
      <section class="section no-print"><div class="section-heading"><h2>Restore archive</h2><span>Archive retained</span></div>
        <p class="muted-note">{escape_html(restore_help)}</p>
        <form method="post" action="/archives/{quote(archive.archive_id, safe="")}/restore" class="compact-form">
          <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}"><input type="hidden" name="expected_revision" value="{escape_html(result.revision.value)}">
          <button class="button primary" type="submit"{restore_disabled}>Restore into active journal</button>
        </form>
      </section>
      <section class="section danger-zone no-print"><div class="section-heading"><h2>Delete archive permanently</h2><span>Cannot be undone</span></div>
        <form method="post" action="/archives/{quote(archive.archive_id, safe="")}/delete" class="compact-form">
          <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}"><input type="hidden" name="expected_revision" value="{escape_html(result.revision.value)}">
          <label class="field"><span>Type <code>{escape_html(archive.archive_id)}</code> to confirm</span><input type="text" name="confirmation" value="{escape_html(delete_confirmation)}" autocomplete="off"></label>
          <button class="button danger" type="submit">Delete archive permanently</button>
        </form>
      </section>
    """
    return render_play_workspace_page(
        dashboard,
        csrf_token=csrf_token,
        title=f"{archive.label or archive.archive_id} — Archives",
        current_kind="archives",
        body=body,
        body_class="archives-body",
    )


def _comparison_card(heading: str, comparison: EntityComparison) -> str:
    rows = (
        ("Added", comparison.added_ids),
        ("Removed", comparison.removed_ids),
        ("Changed", comparison.changed_ids),
    )
    details = "".join(
        f'<div class="comparison-row"><strong>{label}</strong><span>{escape_html(", ".join(values) or "none")}</span></div>'
        for label, values in rows
    )
    return f'<div class="card"><span class="card-kicker">Authored entities</span><h3>{heading}</h3>{details}</div>'


def _yes_no(value: bool) -> str:
    return "changed" if value else "unchanged"
