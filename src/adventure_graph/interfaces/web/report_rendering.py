"""HTML rendering for the generated-report workspace."""

from __future__ import annotations

from urllib.parse import urlencode

from adventure_graph.application.errors import EntityNotFoundError
from adventure_graph.application.reporting import ReportDocument, ReportPacketResult
from adventure_graph.interfaces.web.markdown import render_safe_markdown
from adventure_graph.interfaces.web.page_rendering import (
    current_page_attribute,
    escape_html,
    render_notice,
    render_page,
)
from adventure_graph.interfaces.web.view_models import PageNotice


def render_reports(
    result: ReportPacketResult,
    project_label: str,
    *,
    csrf_token: str,
    selected_name: str | None = None,
    notice: PageNotice | None = None,
) -> str:
    """Render a navigable, printable generated report packet."""
    selected = _selected_report(result, selected_name)
    links = "".join(
        f'<a class="report-link" href="/reports?{urlencode({"document": document.name})}" '
        f"{current_page_attribute(document.name == selected.name)}>"
        f"<span>{escape_html(document.title)}</span><code>{escape_html(document.name)}</code></a>"
        for document in result.documents
    )
    body = f"""
      {render_notice(notice)}
      <div class="page-heading-row report-heading">
        <div><p class="eyebrow">Adventure packet</p><h1>{escape_html(selected.title)}</h1></div>
        <div class="button-row no-print">
          <a class="button secondary" href="/play/ledgers?kind=narrative&amp;scope=playthrough">Open play history</a>
          <button class="button secondary" type="button" data-print-page>Print current report</button>
          <a class="button secondary" href="/reports/download?{urlencode({"document": selected.name})}">Download Markdown</a>
        </div>
      </div>
      <p class="lede">Printable reference documents for the authored adventure. This is not the chronological record of table play; use History for what happened so far.</p>
      <div class="report-layout">
        <nav class="report-toc no-print" aria-label="Generated packet documents">
          <h2>Choose a packet document</h2>{links}
          <form method="post" action="/reports/generate" class="compact-form">
            <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}">
            <input type="hidden" name="expected_revision" value="{escape_html(result.revision.value)}">
            <button class="button primary" type="submit">Write generated packet</button>
            <p>Destination: <code>{escape_html(result.output_label)}</code></p>
          </form>
        </nav>
        <article class="report-paper">
          <div class="report-file-meta"><code>{escape_html(selected.name)}</code><span>{len(selected.content.splitlines())} lines</span></div>
          <div class="prose report-prose">{render_safe_markdown(selected.content)}</div>
        </article>
      </div>
    """
    return render_page(
        title=f"Reports — {result.adventure.title}",
        project_label=project_label,
        adventure=result.adventure,
        report=result.validation_report,
        current_kind="reports",
        current_id=None,
        body=body,
        related_issues=result.validation_report.issues,
        revision=result.revision.value,
    )


def _selected_report(result: ReportPacketResult, selected_name: str | None) -> ReportDocument:
    index = result.document_index()
    if selected_name:
        selected = index.get(selected_name)
        if selected is None:
            raise EntityNotFoundError(f"Unknown generated report {selected_name!r}.")
        return selected
    return result.documents[0]
