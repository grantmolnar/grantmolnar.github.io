"""WSGI shell for application-wide local workspace routes."""

from __future__ import annotations

import secrets
from collections.abc import Callable, Iterable
from contextlib import suppress
from dataclasses import dataclass, field
from http import HTTPStatus
from urllib.parse import parse_qs
from wsgiref.types import StartResponse, WSGIEnvironment

from adventure_graph.application.errors import NoChangesRequestedError, TransferStorageError
from adventure_graph.application.project import ProjectRevision, RevisionConflictError
from adventure_graph.application.validation_settings import UpdateValidationPolicyCommand
from adventure_graph.application.workspace_management import (
    CreateAdventureCommand,
    SelectAdventureCommand,
    UpdateValidatorDefaultsCommand,
    WorkspaceRevision,
    WorkspaceRevisionConflictError,
)
from adventure_graph.interfaces.web.contracts import (
    AdventureWebApplication,
    WorkspaceCommands,
    WorkspaceQueries,
)
from adventure_graph.interfaces.web.form_parsing import (
    CsrfValidationError,
    FormTooLargeError,
    InvalidFormError,
)
from adventure_graph.interfaces.web.http import (
    InvalidHostError,
    InvalidQueryStringError,
    InvalidRequestTargetError,
    WebResponse,
    attachment_disposition,
    emit_response,
    last_parameter,
    redirect,
    report_internal_error,
    require_csrf,
    require_local_authority,
    require_safe_query_string,
    require_safe_request_path,
)
from adventure_graph.interfaces.web.page_rendering import render_error
from adventure_graph.interfaces.web.scripts import load_app_js
from adventure_graph.interfaces.web.styles import load_app_css
from adventure_graph.interfaces.web.transfer_forms import parse_import_document_form
from adventure_graph.interfaces.web.view_models import PageNotice
from adventure_graph.interfaces.web.workspace_forms import (
    parse_adventure_create_form,
    parse_validation_policy_form,
    parse_workspace_revision_form,
    parse_workspace_selection_form,
)
from adventure_graph.interfaces.web.workspace_rendering import (
    render_adventure_catalog,
    render_adventure_create,
    render_adventure_import,
    render_help,
    render_playthrough_import,
    render_settings,
)


@dataclass(frozen=True, slots=True)
class WorkspaceWebApplication:
    """Serve a persistent shell around dynamically selected adventure applications."""

    queries: WorkspaceQueries
    commands: WorkspaceCommands
    adventure_application: Callable[[str, str], AdventureWebApplication]
    workspace_label: str
    csrf_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))

    def __post_init__(self) -> None:
        if not self.csrf_token:
            raise ValueError("The workspace web application requires a CSRF token.")

    def __call__(
        self,
        environ: WSGIEnvironment,
        start_response: StartResponse,
    ) -> Iterable[bytes]:
        """Dispatch workspace routes or delegate directly to the selected adventure."""
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = "/"
        query = ""
        try:
            require_local_authority(environ)
            path = require_safe_request_path(environ)
            query = require_safe_query_string(environ)
            if method in {"GET", "HEAD"}:
                response = self._dispatch_read(path, query)
                if response is None:
                    selected = self.queries.get_workspace().selected_adventure
                    if selected is not None:
                        application = self.adventure_application(selected.key, self.csrf_token)
                        return application(environ, start_response)
                    response = redirect("/adventures")
            elif method == "POST":
                response = self._dispatch_write(path, environ)
                if response is None:
                    selected = self.queries.get_workspace().selected_adventure
                    if selected is None:
                        raise InvalidFormError(
                            "Select or create an adventure before using the authoring workspace."
                        )
                    application = self.adventure_application(selected.key, self.csrf_token)
                    return application(environ, start_response)
            else:
                response = WebResponse(
                    HTTPStatus.METHOD_NOT_ALLOWED,
                    render_error(
                        405,
                        "Method not allowed",
                        "The local workspace accepts GET, HEAD, and explicit POST forms.",
                        self.workspace_label,
                    ),
                    extra_headers=(("Allow", "GET, HEAD, POST"),),
                )
        except InvalidHostError as error:
            response = WebResponse(
                HTTPStatus.MISDIRECTED_REQUEST,
                render_error(
                    421,
                    "Request host rejected",
                    str(error),
                    "Adventure Graph local interface",
                ),
            )
        except InvalidRequestTargetError as error:
            response = WebResponse(
                HTTPStatus.BAD_REQUEST,
                render_error(
                    400,
                    "Request path rejected",
                    str(error),
                    "Adventure Graph local interface",
                ),
            )
        except InvalidQueryStringError as error:
            response = WebResponse(
                HTTPStatus.BAD_REQUEST,
                render_error(
                    400,
                    "Query string rejected",
                    str(error),
                    "Adventure Graph local interface",
                ),
            )
        except CsrfValidationError as error:
            response = self._error(HTTPStatus.FORBIDDEN, "Form token rejected", error)
        except FormTooLargeError as error:
            response = self._error(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "Form too large", error)
        except InvalidFormError as error:
            response = self._error(HTTPStatus.BAD_REQUEST, "Invalid workspace form", error)
        except (WorkspaceRevisionConflictError, RevisionConflictError) as error:
            response = self._error(HTTPStatus.CONFLICT, "Workspace changed", error)
        except TransferStorageError as error:
            report_internal_error(environ, error.__cause__ or error)
            response = self._error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Workspace could not be updated",
                error,
            )
        except (OSError, ValueError) as error:
            report_internal_error(environ, error)
            response = self._internal_error_response()
        except Exception as error:  # noqa: BLE001 -- contain unexpected adapter failures.
            report_internal_error(environ, error)
            response = self._internal_error_response()
        return emit_response(start_response, response, method)

    def _dispatch_read(self, path: str, query: str) -> WebResponse | None:
        if path == "/assets/app.css":
            return WebResponse(
                HTTPStatus.OK,
                load_app_css(),
                "text/css; charset=utf-8",
                "public, max-age=3600",
            )
        if path == "/assets/app.js":
            return WebResponse(
                HTTPStatus.OK,
                load_app_js(),
                "text/javascript; charset=utf-8",
                "public, max-age=3600",
            )
        if path == "/healthz":
            return WebResponse(HTTPStatus.OK, "ok\n", "text/plain; charset=utf-8")
        if path == "/help":
            return WebResponse(HTTPStatus.OK, render_help())
        if path == "/adventures":
            snapshot = self.queries.get_workspace()
            parameters = parse_qs(query, keep_blank_values=True)
            notice = None
            if last_parameter(parameters, "created"):
                notice = PageNotice(
                    "success",
                    "Adventure created",
                    "The new adventure is selected and ready for authoring.",
                )
            elif last_parameter(parameters, "sample"):
                notice = PageNotice(
                    "success",
                    "Sample added",
                    "The Glass Saint is selected as a separate editable project.",
                )
            elif last_parameter(parameters, "selected"):
                notice = PageNotice(
                    "success",
                    "Adventure selected",
                    "The GM workspace now points to the chosen adventure.",
                )
            elif last_parameter(parameters, "imported"):
                notice = PageNotice(
                    "success",
                    "Adventure imported",
                    "The imported adventure is selected and ready to use.",
                )
            elif last_parameter(parameters, "playthrough-imported"):
                notice = PageNotice(
                    "success",
                    "Playthrough imported",
                    "Adventure Graph matched the playthrough to its adventure without changing "
                    "the selected adventure or active journal.",
                )
            return WebResponse(
                HTTPStatus.OK,
                render_adventure_catalog(
                    snapshot,
                    csrf_token=self.csrf_token,
                    notice=notice,
                    clear_draft_key=(
                        "workspace:new-adventure" if last_parameter(parameters, "created") else None
                    ),
                ),
            )
        if path == "/adventures/new":
            snapshot = self.queries.get_workspace()
            return WebResponse(
                HTTPStatus.OK,
                render_adventure_create(snapshot, csrf_token=self.csrf_token),
            )
        if path == "/adventures/import":
            snapshot = self.queries.get_workspace()
            return WebResponse(
                HTTPStatus.OK,
                render_adventure_import(snapshot, csrf_token=self.csrf_token),
            )
        if path == "/adventures/playthroughs/import":
            snapshot = self.queries.get_workspace()
            return WebResponse(
                HTTPStatus.OK,
                render_playthrough_import(snapshot, csrf_token=self.csrf_token),
            )
        if path == "/adventures/export":
            parameters = parse_qs(query, keep_blank_values=True)
            if set(parameters) != {"key"} or len(parameters["key"]) != 1:
                raise InvalidQueryStringError("Choose exactly one adventure to export.")
            key = parameters["key"][0]
            snapshot = self.queries.get_workspace()
            if key not in {entry.key for entry in snapshot.adventures}:
                return self._error(
                    HTTPStatus.NOT_FOUND,
                    "Adventure not found",
                    ValueError("The selected adventure is no longer available in this workspace."),
                )
            document = self.queries.export_adventure(key)
            return WebResponse(
                HTTPStatus.OK,
                document.body,
                document.content_type,
                extra_headers=(attachment_disposition(document.filename),),
            )
        if path == "/settings":
            snapshot = self.queries.get_workspace()
            parameters = parse_qs(query, keep_blank_values=True)
            selected = snapshot.selected_adventure
            current = (
                self.queries.get_adventure_overview(selected.key) if selected is not None else None
            )
            saved = last_parameter(parameters, "saved")
            notice = (
                PageNotice(
                    "success",
                    "Settings saved",
                    (
                        "Workspace defaults now apply to adventures created later."
                        if saved == "defaults"
                        else "The selected adventure's validator policy was updated."
                    ),
                )
                if saved in {"defaults", "adventure"}
                else None
            )
            return WebResponse(
                HTTPStatus.OK,
                render_settings(snapshot, current, csrf_token=self.csrf_token, notice=notice),
            )
        return None

    def _dispatch_write(self, path: str, environ: WSGIEnvironment) -> WebResponse | None:
        if path in {"/adventures/select", "/adventures/playthroughs"}:
            values, token = parse_workspace_selection_form(environ)
            require_csrf(token, self.csrf_token)
            self.commands.select_adventure(
                SelectAdventureCommand(
                    values.adventure_key,
                    WorkspaceRevision(values.expected_revision),
                )
            )
            return redirect("/archives" if path == "/adventures/playthroughs" else "/")
        if path == "/adventures/sample":
            revision, token = parse_workspace_revision_form(environ)
            require_csrf(token, self.csrf_token)
            self.commands.create_sample_adventure(WorkspaceRevision(revision))
            return redirect("/adventures?sample=1")
        if path == "/adventures/new":
            values, token = parse_adventure_create_form(environ)
            require_csrf(token, self.csrf_token)
            self.commands.create_adventure(
                CreateAdventureCommand(
                    title=values.title,
                    synopsis=values.synopsis,
                    premise=values.premise,
                    explanation=values.explanation,
                    tags=values.tags,
                    opening_title=values.opening_title,
                    opening_summary=values.opening_summary,
                    opening_view=values.opening_view,
                    expected_revision=WorkspaceRevision(values.expected_revision),
                )
            )
            return redirect("/adventures?created=1")
        if path == "/adventures/import":
            return self._import_adventure(environ)
        if path == "/adventures/playthroughs/import":
            return self._import_playthrough(environ)
        if path == "/settings/defaults":
            policy, revision, token = parse_validation_policy_form(environ)
            require_csrf(token, self.csrf_token)
            with suppress(NoChangesRequestedError):
                self.commands.update_validator_defaults(
                    UpdateValidatorDefaultsCommand(policy, WorkspaceRevision(revision))
                )
            return redirect("/settings?saved=defaults")
        if path == "/settings/adventure":
            selected = self.queries.get_workspace().selected_adventure
            if selected is None:
                raise InvalidFormError("Select an adventure before editing its validator policy.")
            policy, revision, token = parse_validation_policy_form(environ)
            require_csrf(token, self.csrf_token)
            with suppress(NoChangesRequestedError):
                self.commands.update_adventure_validation_policy(
                    selected.key,
                    UpdateValidationPolicyCommand(ProjectRevision(revision), policy),
                )
            return redirect("/settings?saved=adventure")
        return None

    def _import_adventure(self, environ: WSGIEnvironment) -> WebResponse:
        try:
            values, token = parse_import_document_form(
                environ,
                file_field="adventure_file",
            )
        except FormTooLargeError as error:
            return self._adventure_import_error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "Adventure file too large",
                error,
            )
        except InvalidFormError as error:
            return self._adventure_import_error(
                HTTPStatus.BAD_REQUEST,
                "Adventure upload could not be read",
                error,
            )
        require_csrf(token, self.csrf_token)
        try:
            self.commands.import_adventure_document(
                values.content,
                WorkspaceRevision(values.expected_revision),
            )
        except WorkspaceRevisionConflictError as error:
            return self._adventure_import_error(
                HTTPStatus.CONFLICT,
                "Adventure catalog changed",
                error,
            )
        except TransferStorageError as error:
            report_internal_error(environ, error.__cause__ or error)
            return self._adventure_import_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Adventure could not be saved",
                error,
            )
        except ValueError as error:
            return self._adventure_import_error(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Adventure was not imported",
                error,
            )
        return redirect("/adventures?imported=1")

    def _import_playthrough(self, environ: WSGIEnvironment) -> WebResponse:
        try:
            values, token = parse_import_document_form(
                environ,
                file_field="archive_file",
            )
        except FormTooLargeError as error:
            return self._playthrough_import_error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "Playthrough file too large",
                error,
            )
        except InvalidFormError as error:
            return self._playthrough_import_error(
                HTTPStatus.BAD_REQUEST,
                "Playthrough upload could not be read",
                error,
            )
        require_csrf(token, self.csrf_token)
        try:
            self.commands.import_playthrough_document(
                values.content,
                WorkspaceRevision(values.expected_revision),
            )
        except (WorkspaceRevisionConflictError, RevisionConflictError) as error:
            return self._playthrough_import_error(
                HTTPStatus.CONFLICT,
                "Adventure or archive catalog changed",
                error,
            )
        except TransferStorageError as error:
            report_internal_error(environ, error.__cause__ or error)
            return self._playthrough_import_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                "Playthrough could not be saved",
                error,
            )
        except ValueError as error:
            return self._playthrough_import_error(
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Playthrough was not imported",
                error,
            )
        return redirect("/adventures?playthrough-imported=1")

    def _adventure_import_error(
        self,
        status: HTTPStatus,
        heading: str,
        error: BaseException,
    ) -> WebResponse:
        return WebResponse(
            status,
            render_adventure_import(
                self.queries.get_workspace(),
                csrf_token=self.csrf_token,
                notice=PageNotice("error", heading, str(error)),
            ),
        )

    def _playthrough_import_error(
        self,
        status: HTTPStatus,
        heading: str,
        error: BaseException,
    ) -> WebResponse:
        return WebResponse(
            status,
            render_playthrough_import(
                self.queries.get_workspace(),
                csrf_token=self.csrf_token,
                notice=PageNotice("error", heading, str(error)),
            ),
        )

    def _internal_error_response(self) -> WebResponse:
        return WebResponse(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            render_error(
                500,
                "Workspace could not be loaded",
                "Adventure Graph could not complete this request without exposing "
                "local workspace details.",
                self.workspace_label,
            ),
        )

    def _error(self, status: HTTPStatus, heading: str, error: BaseException) -> WebResponse:
        return WebResponse(
            status,
            render_error(status.value, heading, str(error), self.workspace_label),
        )
