"""HTTP coordination for journal archive browsing and mutations."""

from __future__ import annotations

from http import HTTPStatus
from urllib.parse import parse_qs, urlencode
from wsgiref.types import WSGIEnvironment

from adventure_graph.application.archive_management import (
    ArchiveActiveJournalCommand,
    DeleteJournalArchiveCommand,
    ExportActiveJournalCommand,
    RestoreJournalArchiveCommand,
)
from adventure_graph.application.errors import TransferStorageError
from adventure_graph.application.project import (
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.interfaces.web.archive_rendering import (
    render_archive_catalog,
    render_archive_detail,
)
from adventure_graph.interfaces.web.authoring_forms import (
    parse_archive_action_form,
    parse_archive_create_form,
)
from adventure_graph.interfaces.web.contracts import ArchiveCommands, ArchiveQueries, PlayQueries
from adventure_graph.interfaces.web.form_parsing import FormTooLargeError, InvalidFormError
from adventure_graph.interfaces.web.http import (
    WebResponse,
    attachment_disposition,
    last_parameter,
    redirect,
    report_internal_error,
    require_csrf,
)
from adventure_graph.interfaces.web.page_rendering import render_error
from adventure_graph.interfaces.web.transfer_forms import parse_import_document_form
from adventure_graph.interfaces.web.view_models import PageNotice


def archive_catalog_response(
    queries: ArchiveQueries,
    play_queries: PlayQueries,
    project_label: str,
    csrf_token: str,
    query: str,
) -> WebResponse:
    """Render the archive catalog and any completed-action notice."""
    parameters = parse_qs(query, keep_blank_values=True)
    action = last_parameter(parameters, "action")
    identifier = last_parameter(parameters, "archive")
    notices = {
        "created": PageNotice(
            "success",
            "Journal archived",
            f"Archive {identifier} was created and the active journal was reset.",
        ),
        "restored": PageNotice(
            "success",
            "Archive restored",
            f"Archive {identifier} now supplies the active journal and remains in the catalog.",
        ),
        "deleted": PageNotice(
            "success",
            "Archive deleted",
            f"Archive {identifier} was permanently removed.",
        ),
        "imported": PageNotice(
            "success",
            "Playthrough imported",
            f"Archive {identifier} was added to this adventure.",
        ),
    }
    return WebResponse(
        HTTPStatus.OK,
        render_archive_catalog(
            queries.list_archives(),
            project_label,
            csrf_token=csrf_token,
            dashboard=play_queries.get_run(),
            notice=notices.get(action),
        ),
    )


def archive_detail_response(
    queries: ArchiveQueries,
    play_queries: PlayQueries,
    project_label: str,
    csrf_token: str,
    archive_id: str,
) -> WebResponse:
    """Render one immutable archive and its compatibility comparison."""
    return WebResponse(
        HTTPStatus.OK,
        render_archive_detail(
            queries.get_archive(archive_id),
            project_label,
            csrf_token=csrf_token,
            dashboard=play_queries.get_run(),
        ),
    )


def archive_download_response(queries: ArchiveQueries, archive_id: str) -> WebResponse:
    """Download one stored archive in its canonical portable representation."""
    document = queries.export_archive(archive_id)
    return WebResponse(
        HTTPStatus.OK,
        document.body,
        document.content_type,
        extra_headers=(attachment_disposition(document.filename),),
    )


def create_archive_response(
    queries: ArchiveQueries,
    play_queries: PlayQueries,
    commands: ArchiveCommands,
    project_label: str,
    csrf_token: str,
    environ: WSGIEnvironment,
) -> WebResponse:
    """Archive the active journal and reset it atomically."""
    values, token = parse_archive_create_form(environ)
    require_csrf(token, csrf_token)
    try:
        result = commands.create_archive(
            ArchiveActiveJournalCommand(
                expected_revision=ProjectRevision(values.expected_revision),
                label=values.label,
                name=values.name,
            )
        )
    except RevisionConflictError as error:
        return _catalog_error(
            queries,
            play_queries,
            project_label,
            csrf_token,
            error,
            HTTPStatus.CONFLICT,
            "Revision conflict",
        )
    except ValueError as error:
        return _catalog_error(
            queries,
            play_queries,
            project_label,
            csrf_token,
            error,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "Journal was not archived",
        )
    return redirect("/archives?" + urlencode({"action": "created", "archive": result.archive_id}))


def export_active_response(
    queries: ArchiveQueries,
    play_queries: PlayQueries,
    commands: ArchiveCommands,
    project_label: str,
    csrf_token: str,
    environ: WSGIEnvironment,
) -> WebResponse:
    """Download the current journal as a portable archive without resetting it."""
    values, token = parse_archive_create_form(environ)
    require_csrf(token, csrf_token)
    try:
        document = commands.export_active(
            ExportActiveJournalCommand(
                expected_revision=ProjectRevision(values.expected_revision),
                label=values.label,
                name=values.name,
            )
        )
    except RevisionConflictError as error:
        return _catalog_error(
            queries,
            play_queries,
            project_label,
            csrf_token,
            error,
            HTTPStatus.CONFLICT,
            "Revision conflict",
        )
    except ValueError as error:
        return _catalog_error(
            queries,
            play_queries,
            project_label,
            csrf_token,
            error,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "Playthrough was not exported",
        )
    return WebResponse(
        HTTPStatus.OK,
        document.body,
        document.content_type,
        extra_headers=(attachment_disposition(document.filename),),
    )


def import_archive_response(
    queries: ArchiveQueries,
    play_queries: PlayQueries,
    commands: ArchiveCommands,
    project_label: str,
    csrf_token: str,
    environ: WSGIEnvironment,
) -> WebResponse:
    """Validate and persist one uploaded portable playthrough archive."""
    try:
        values, token = parse_import_document_form(environ, file_field="archive_file")
    except FormTooLargeError as error:
        return _catalog_error(
            queries,
            play_queries,
            project_label,
            csrf_token,
            error,
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            "Playthrough file too large",
        )
    except InvalidFormError as error:
        return _catalog_error(
            queries,
            play_queries,
            project_label,
            csrf_token,
            error,
            HTTPStatus.BAD_REQUEST,
            "Playthrough upload could not be read",
        )
    require_csrf(token, csrf_token)
    try:
        result = commands.import_archive_document(
            values.content,
            ProjectRevision(values.expected_revision),
        )
    except RevisionConflictError as error:
        return _catalog_error(
            queries,
            play_queries,
            project_label,
            csrf_token,
            error,
            HTTPStatus.CONFLICT,
            "Revision conflict",
        )
    except TransferStorageError as error:
        report_internal_error(environ, error.__cause__ or error)
        return WebResponse(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            render_error(
                500,
                "Playthrough could not be saved",
                str(error),
                project_label,
            ),
        )
    except ValueError as error:
        return _catalog_error(
            queries,
            play_queries,
            project_label,
            csrf_token,
            error,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "Playthrough was not imported",
        )
    return redirect("/archives?" + urlencode({"action": "imported", "archive": result.archive_id}))


def archive_action_response(
    queries: ArchiveQueries,
    play_queries: PlayQueries,
    commands: ArchiveCommands,
    project_label: str,
    csrf_token: str,
    archive_id: str,
    action: str,
    environ: WSGIEnvironment,
) -> WebResponse:
    """Restore or permanently delete one archive after guarded form validation."""
    values, token = parse_archive_action_form(
        environ,
        include_confirmation=action == "delete",
    )
    confirmation = values.confirmation
    require_csrf(token, csrf_token)
    try:
        if action == "restore":
            result = commands.restore_archive(
                RestoreJournalArchiveCommand(
                    archive_id,
                    ProjectRevision(values.expected_revision),
                )
            )
        elif action == "delete":
            result = commands.delete_archive(
                DeleteJournalArchiveCommand(
                    archive_id,
                    confirmation,
                    ProjectRevision(values.expected_revision),
                )
            )
        else:
            raise InvalidFormError(f"Unknown archive action {action!r}.")
    except RevisionConflictError as error:
        return _detail_error(
            queries,
            play_queries,
            project_label,
            csrf_token,
            archive_id,
            confirmation,
            error,
            HTTPStatus.CONFLICT,
            "Revision conflict",
        )
    except ValueError as error:
        return _detail_error(
            queries,
            play_queries,
            project_label,
            csrf_token,
            archive_id,
            confirmation,
            error,
            HTTPStatus.UNPROCESSABLE_ENTITY,
            "Archive operation refused",
        )
    return redirect(
        "/archives?" + urlencode({"action": f"{action}d", "archive": result.archive_id})
    )


def _catalog_error(
    queries: ArchiveQueries,
    play_queries: PlayQueries,
    project_label: str,
    csrf_token: str,
    error: BaseException,
    status: HTTPStatus,
    heading: str,
) -> WebResponse:
    return WebResponse(
        status,
        render_archive_catalog(
            queries.list_archives(),
            project_label,
            csrf_token=csrf_token,
            dashboard=play_queries.get_run(),
            notice=PageNotice("error", heading, str(error)),
        ),
    )


def _detail_error(
    queries: ArchiveQueries,
    play_queries: PlayQueries,
    project_label: str,
    csrf_token: str,
    archive_id: str,
    confirmation: str,
    error: ValueError,
    status: HTTPStatus,
    heading: str,
) -> WebResponse:
    return WebResponse(
        status,
        render_archive_detail(
            queries.get_archive(archive_id),
            project_label,
            csrf_token=csrf_token,
            dashboard=play_queries.get_run(),
            notice=PageNotice("error", heading, str(error)),
            delete_confirmation=confirmation,
        ),
    )
