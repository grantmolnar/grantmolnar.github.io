"""HTTP coordination for the generated-report workspace."""

from __future__ import annotations

from http import HTTPStatus
from urllib.parse import parse_qs
from wsgiref.types import WSGIEnvironment

from adventure_graph.application.errors import EntityNotFoundError
from adventure_graph.application.project import (
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.application.reporting import PublishReportPacketCommand
from adventure_graph.interfaces.web.authoring_forms import parse_publish_report_form
from adventure_graph.interfaces.web.contracts import ReportCommands, ReportQueries
from adventure_graph.interfaces.web.http import (
    WebResponse,
    attachment_disposition,
    last_parameter,
    redirect,
    require_csrf,
)
from adventure_graph.interfaces.web.report_rendering import render_reports
from adventure_graph.interfaces.web.view_models import PageNotice


def report_page_response(
    queries: ReportQueries,
    project_label: str,
    csrf_token: str,
    query: str,
) -> WebResponse:
    """Render the selected live report and any publication notice."""
    parameters = parse_qs(query, keep_blank_values=True)
    notice = (
        PageNotice(
            "success",
            "Generated packet written",
            "The disposable Markdown packet was regenerated from current source state.",
        )
        if last_parameter(parameters, "generated")
        else None
    )
    return WebResponse(
        HTTPStatus.OK,
        render_reports(
            queries.get_packet(),
            project_label,
            csrf_token=csrf_token,
            selected_name=last_parameter(parameters, "document") or None,
            notice=notice,
        ),
    )


def report_download_response(queries: ReportQueries, query: str) -> WebResponse:
    """Return one generated Markdown document as an attachment."""
    parameters = parse_qs(query, keep_blank_values=True)
    name = last_parameter(parameters, "document")
    packet = queries.get_packet()
    document = packet.document_index().get(name)
    if document is None:
        raise EntityNotFoundError(f"Unknown generated report {name!r}.")
    filename = document.name.rsplit("/", 1)[-1]
    return WebResponse(
        HTTPStatus.OK,
        document.content,
        "text/markdown; charset=utf-8",
        "no-store",
        (attachment_disposition(filename),),
    )


def publish_reports_response(
    queries: ReportQueries,
    commands: ReportCommands,
    project_label: str,
    csrf_token: str,
    environ: WSGIEnvironment,
) -> WebResponse:
    """Publish the current report packet after revision and CSRF validation."""
    revision, token = parse_publish_report_form(environ)
    require_csrf(token, csrf_token)
    try:
        commands.publish_packet(PublishReportPacketCommand(ProjectRevision(revision)))
    except RevisionConflictError as error:
        return WebResponse(
            HTTPStatus.CONFLICT,
            render_reports(
                queries.get_packet(),
                project_label,
                csrf_token=csrf_token,
                notice=PageNotice("error", "Revision conflict", str(error)),
            ),
        )
    return redirect("/reports?generated=1")
