"""Dependency-injected WSGI adapter for local adventure authoring."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from http import HTTPStatus
from urllib.parse import parse_qs
from wsgiref.types import StartResponse, WSGIEnvironment

from adventure_graph.application.errors import EntityNotFoundError
from adventure_graph.interfaces.web.adventure_rendering import (
    render_adventure_edit,
    render_overview,
)
from adventure_graph.interfaces.web.archive_workspace import (
    archive_action_response,
    archive_catalog_response,
    archive_detail_response,
    archive_download_response,
    create_archive_response,
    export_active_response,
    import_archive_response,
)
from adventure_graph.interfaces.web.authoring_action_workspace import (
    AuthoringActionWorkspace,
)
from adventure_graph.interfaces.web.clue_rendering import (
    render_clue,
    render_clue_create,
    render_clue_edit,
)
from adventure_graph.interfaces.web.contracts import (
    ArchiveCommands,
    ArchiveQueries,
    AuthoringCommands,
    AuthoringQueries,
    PlayCapability,
    ReportCommands,
    ReportQueries,
)
from adventure_graph.interfaces.web.encounter_rendering import (
    render_encounter,
    render_encounter_create,
    render_encounter_edit,
    render_encounter_remove,
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
    report_internal_error,
    require_local_authority,
    require_safe_query_string,
    require_safe_request_path,
)
from adventure_graph.interfaces.web.http import (
    WebResponse as _WebResponse,
)
from adventure_graph.interfaces.web.http import (
    emit_response as _emit_response,
)
from adventure_graph.interfaces.web.http import (
    last_parameter as _last_parameter,
)
from adventure_graph.interfaces.web.page_rendering import render_error
from adventure_graph.interfaces.web.play_workspace import PlayWebWorkspace
from adventure_graph.interfaces.web.reference_rendering import (
    REFERENCE_KINDS,
    render_reference,
    render_reference_create,
    render_reference_edit,
    render_reference_library,
    render_reference_remove,
)
from adventure_graph.interfaces.web.report_workspace import (
    publish_reports_response,
    report_download_response,
    report_page_response,
)
from adventure_graph.interfaces.web.routing import (
    archive_action_route,
    archive_detail_route,
    archive_download_route,
    entity_edit_route,
    entity_remove_route,
    entity_route,
    normalize_play_return_target,
)
from adventure_graph.interfaces.web.revelation_rendering import (
    render_revelation,
    render_revelation_create,
    render_revelation_edit,
)
from adventure_graph.interfaces.web.scripts import load_app_js
from adventure_graph.interfaces.web.structure_rendering import render_structure
from adventure_graph.interfaces.web.styles import load_app_css
from adventure_graph.interfaces.web.view_models import (
    ClueCreateValues,
    EncounterCreateValues,
    PageNotice,
    ReferenceCreateValues,
    RevelationCreateValues,
)


@dataclass(frozen=True, slots=True)
class AuthoringWebApplication:
    """Serve application queries and revision-aware authoring forms as local HTML."""

    queries: AuthoringQueries
    commands: AuthoringCommands
    project_label: str
    play: PlayCapability | None = None
    report_queries: ReportQueries | None = None
    report_commands: ReportCommands | None = None
    archive_queries: ArchiveQueries | None = None
    archive_commands: ArchiveCommands | None = None
    csrf_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    _play_workspace: PlayWebWorkspace = field(init=False, repr=False)
    _authoring_actions: AuthoringActionWorkspace = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.csrf_token:
            raise ValueError("The web authoring application requires a CSRF token.")
        object.__setattr__(
            self,
            "_play_workspace",
            PlayWebWorkspace(self.play, self.project_label, self.csrf_token),
        )
        object.__setattr__(
            self,
            "_authoring_actions",
            AuthoringActionWorkspace(
                self.queries,
                self.commands,
                self.project_label,
                self.csrf_token,
            ),
        )

    def __call__(self, environ: WSGIEnvironment, start_response: StartResponse) -> list[bytes]:
        """Dispatch one WSGI request without importing an infrastructure adapter."""
        method = str(environ.get("REQUEST_METHOD", "GET")).upper()
        path = "/"
        query = ""
        try:
            require_local_authority(environ)
            path = require_safe_request_path(environ)
            query = require_safe_query_string(environ)
            if method in {"GET", "HEAD"}:
                response = self._dispatch_read(path, query)
            elif method == "POST":
                response = self._dispatch_write(path, environ)
            else:
                response = _WebResponse(
                    HTTPStatus.METHOD_NOT_ALLOWED,
                    render_error(
                        405,
                        "Method not allowed",
                        "The local authoring interface accepts GET, HEAD, and explicit POST forms.",
                        self.project_label,
                    ),
                    extra_headers=(("Allow", "GET, HEAD, POST"),),
                )
        except InvalidHostError as error:
            response = _WebResponse(
                HTTPStatus.MISDIRECTED_REQUEST,
                render_error(
                    421,
                    "Request host rejected",
                    str(error),
                    "Adventure Graph local interface",
                ),
            )
        except InvalidRequestTargetError as error:
            response = _WebResponse(
                HTTPStatus.BAD_REQUEST,
                render_error(
                    400,
                    "Request path rejected",
                    str(error),
                    "Adventure Graph local interface",
                ),
            )
        except InvalidQueryStringError as error:
            response = _WebResponse(
                HTTPStatus.BAD_REQUEST,
                render_error(
                    400,
                    "Query string rejected",
                    str(error),
                    "Adventure Graph local interface",
                ),
            )
        except CsrfValidationError as error:
            response = _WebResponse(
                HTTPStatus.FORBIDDEN,
                render_error(403, "Form token rejected", str(error), self.project_label),
            )
        except FormTooLargeError as error:
            response = _WebResponse(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                render_error(413, "Form too large", str(error), self.project_label),
            )
        except InvalidFormError as error:
            response = _WebResponse(
                HTTPStatus.BAD_REQUEST,
                render_error(400, "Invalid authoring form", str(error), self.project_label),
            )
        except EntityNotFoundError as error:
            response = _WebResponse(
                HTTPStatus.NOT_FOUND,
                render_error(404, "Page not found", str(error), self.project_label),
            )
        except (OSError, ValueError) as error:
            report_internal_error(environ, error)
            response = self._internal_error_response()
        except Exception as error:  # noqa: BLE001 -- contain unexpected adapter failures.
            report_internal_error(environ, error)
            response = self._internal_error_response()
        return _emit_response(start_response, response, method)

    def _dispatch_read(self, path: str, query: str) -> _WebResponse:
        response = self._asset_response(path)
        if response is not None:
            return response
        if path == "/healthz":
            response = _WebResponse(HTTPStatus.OK, "ok\n", "text/plain; charset=utf-8")
        elif path == "/":
            result = self.queries.get_overview()
            parameters = parse_qs(query, keep_blank_values=True)
            saved = _last_parameter(parameters, "saved")
            draft_id = _last_parameter(parameters, "draft") or result.adventure.id
            response = _WebResponse(
                HTTPStatus.OK,
                render_overview(
                    result,
                    self.project_label,
                    notice=(
                        PageNotice(
                            "success",
                            "Encounter removed",
                            (
                                "The encounter and only its explicitly confirmed subordinate "
                                "dependencies were removed."
                            ),
                        )
                        if _last_parameter(parameters, "encounter_removed")
                        else _saved_notice("Adventure", saved)
                    ),
                    clear_draft_key=(self._draft_key("adventure", draft_id) if saved else None),
                ),
            )
        elif path == "/adventure/edit":
            result = self.queries.get_overview()
            response = _WebResponse(
                HTTPStatus.OK,
                render_adventure_edit(
                    result,
                    self.project_label,
                    csrf_token=self.csrf_token,
                    draft_key=self._draft_key("adventure", result.adventure.id),
                ),
            )
        elif path == "/structure":
            response = _WebResponse(
                HTTPStatus.OK,
                render_structure(self.queries.get_structure(), self.project_label),
            )
        elif (play_response := self._play_workspace.read(path, query)) is not None:
            response = play_response
        elif (workspace_response := self._extended_workspace_read(path, query)) is not None:
            response = workspace_response
        elif path == "/references":
            parameters = parse_qs(query, keep_blank_values=True)
            kind_filter = _last_parameter(parameters, "kind")
            if kind_filter and kind_filter not in REFERENCE_KINDS:
                raise InvalidQueryStringError("The reference kind filter is unsupported.")
            response = _WebResponse(
                HTTPStatus.OK,
                render_reference_library(
                    self.queries.get_overview(),
                    self.project_label,
                    kind_filter=kind_filter,
                    notice=_reference_library_notice(parameters),
                ),
            )
        elif path == "/references/new":
            response = self._new_reference_response(query)
        elif path == "/encounters/new":
            response = self._new_encounter_response(query)
        elif path == "/clues/new":
            response = self._new_clue_response(query)
        elif path == "/revelations/new":
            response = self._new_revelation_response(query)
        else:
            response = self._page_response(path, query)
        return response

    def _extended_workspace_read(self, path: str, query: str) -> _WebResponse | None:
        if path.startswith("/reports"):
            return self._report_workspace_read(path, query)
        if path.startswith("/archives"):
            return self._archive_workspace_read(path, query)
        return None

    def _report_workspace_read(self, path: str, query: str) -> _WebResponse | None:
        if path not in {"/reports", "/reports/download"}:
            return None
        if self.report_queries is None:
            return self._workspace_unavailable_response("Reports unavailable")
        if path == "/reports/download":
            return report_download_response(self.report_queries, query)
        return report_page_response(
            self.report_queries,
            self.project_label,
            self.csrf_token,
            query,
        )

    def _archive_workspace_read(self, path: str, query: str) -> _WebResponse | None:
        archive_download_id = archive_download_route(path)
        archive_id = archive_detail_route(path)
        if path != "/archives" and archive_id is None and archive_download_id is None:
            return None
        if self.archive_queries is None or self.play is None:
            return self._workspace_unavailable_response("Archives unavailable")
        if archive_download_id is not None:
            return archive_download_response(self.archive_queries, archive_download_id)
        if archive_id is None:
            return archive_catalog_response(
                self.archive_queries,
                self.play.queries,
                self.project_label,
                self.csrf_token,
                query,
            )
        return archive_detail_response(
            self.archive_queries,
            self.play.queries,
            self.project_label,
            self.csrf_token,
            archive_id,
        )

    def _asset_response(self, path: str) -> _WebResponse | None:
        if path == "/assets/app.css":
            return _WebResponse(
                HTTPStatus.OK,
                load_app_css(),
                "text/css; charset=utf-8",
                "public, max-age=3600",
            )
        if path == "/assets/app.js":
            return _WebResponse(
                HTTPStatus.OK,
                load_app_js(),
                "text/javascript; charset=utf-8",
                "public, max-age=3600",
            )
        return None

    def _new_reference_response(self, query: str) -> _WebResponse:
        result = self.queries.get_overview()
        parameters = parse_qs(query, keep_blank_values=True)
        encounter_id = _last_parameter(parameters, "encounter")
        if encounter_id and encounter_id not in result.adventure.encounter_index():
            raise EntityNotFoundError(f"Unknown encounter {encounter_id!r}.")
        values = ReferenceCreateValues(
            expected_revision=result.revision.value,
            encounter_id=encounter_id,
            return_to=(
                normalize_play_return_target(_last_parameter(parameters, "return_to")) or ""
            ),
        )
        draft_id = f"new:{encounter_id}" if encounter_id else "new"
        return _WebResponse(
            HTTPStatus.OK,
            render_reference_create(
                result,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("reference", draft_id),
                values=values,
            ),
        )

    def _new_encounter_response(self, query: str) -> _WebResponse:
        result = self.queries.get_structure()
        parameters = parse_qs(query, keep_blank_values=True)
        return_to = normalize_play_return_target(_last_parameter(parameters, "return_to")) or ""
        values = EncounterCreateValues(
            start=not result.adventure.encounters,
            expected_revision=result.revision.value,
            return_to=return_to,
        )
        return _WebResponse(
            HTTPStatus.OK,
            render_encounter_create(
                result,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("encounter", "new"),
                values=values,
            ),
        )

    def _new_clue_response(self, query: str) -> _WebResponse:
        result = self.queries.get_structure()
        parameters = parse_qs(query, keep_blank_values=True)
        values = ClueCreateValues(
            source_encounter_id=_last_parameter(parameters, "source"),
            revelation_id=_last_parameter(parameters, "revelation"),
            expected_revision=result.revision.value,
            return_to=(
                normalize_play_return_target(_last_parameter(parameters, "return_to")) or ""
            ),
        )
        notice = (
            PageNotice(
                "success",
                "Revelation created",
                "Now write the lead that establishes the proposed connection.",
            )
            if _last_parameter(parameters, "created_revelation")
            else None
        )
        return _WebResponse(
            HTTPStatus.OK,
            render_clue_create(
                result,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("clue", "new"),
                values=values,
                notice=notice,
            ),
        )

    def _new_revelation_response(self, query: str) -> _WebResponse:
        result = self.queries.get_structure()
        parameters = parse_qs(query, keep_blank_values=True)
        values = RevelationCreateValues(
            unlocks_encounter_id=_last_parameter(parameters, "unlocks"),
            source_encounter_id=_last_parameter(parameters, "source"),
            expected_revision=result.revision.value,
            return_to=(
                normalize_play_return_target(_last_parameter(parameters, "return_to")) or ""
            ),
        )
        return _WebResponse(
            HTTPStatus.OK,
            render_revelation_create(
                result,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("revelation", "new"),
                values=values,
            ),
        )

    def _page_response(self, path: str, query: str) -> _WebResponse:
        remove_route = entity_remove_route(path)
        if remove_route is not None:
            kind, identifier = remove_route
            if kind == "encounter":
                body = render_encounter_remove(
                    self.queries.get_encounter(identifier),
                    self.project_label,
                    csrf_token=self.csrf_token,
                )
            elif kind == "reference":
                body = render_reference_remove(
                    self.queries.get_reference(identifier),
                    self.project_label,
                    csrf_token=self.csrf_token,
                )
            else:
                return _WebResponse(
                    HTTPStatus.NOT_FOUND,
                    render_error(
                        404,
                        "Page not found",
                        "This authored item does not have a browser removal workflow.",
                        self.project_label,
                    ),
                )
            return _WebResponse(HTTPStatus.OK, body)
        edit_route = entity_edit_route(path)
        if edit_route is not None:
            kind, identifier = edit_route
            if kind == "encounter":
                result = self.queries.get_encounter(identifier)
                body = render_encounter_edit(
                    result,
                    self.project_label,
                    csrf_token=self.csrf_token,
                    draft_key=self._draft_key("encounter", identifier),
                )
            elif kind == "reference":
                result = self.queries.get_reference(identifier)
                body = render_reference_edit(
                    result,
                    self.project_label,
                    csrf_token=self.csrf_token,
                    draft_key=self._draft_key("reference", identifier),
                )
            elif kind == "revelation":
                result = self.queries.get_revelation(identifier)
                body = render_revelation_edit(
                    result,
                    self.project_label,
                    csrf_token=self.csrf_token,
                    draft_key=self._draft_key("revelation", identifier),
                )
            else:
                result = self.queries.get_clue(identifier)
                body = render_clue_edit(
                    result,
                    self.project_label,
                    csrf_token=self.csrf_token,
                    draft_key=self._draft_key("clue", identifier),
                )
            return _WebResponse(HTTPStatus.OK, body)
        route = entity_route(path)
        if route is None:
            return _WebResponse(
                HTTPStatus.NOT_FOUND,
                render_error(
                    404,
                    "Page not found",
                    "No authoring route matches this address.",
                    self.project_label,
                ),
            )
        kind, identifier = route
        parameters = parse_qs(query, keep_blank_values=True)
        if kind == "encounter":
            created = _last_parameter(parameters, "created")
            saved = _last_parameter(parameters, "saved")
            notice = (
                PageNotice(
                    "success",
                    "Encounter created",
                    "The new encounter was committed and structural validation was recomputed.",
                )
                if created
                else None
            )
            clear_draft_key = self._draft_key("encounter", "new") if created else None
            if saved:
                notice = (
                    PageNotice(
                        "info",
                        "No changes to save",
                        "The encounter already matched the submitted values.",
                    )
                    if saved == "unchanged"
                    else PageNotice(
                        "success",
                        "Encounter saved",
                        "The authored file was committed at the current project revision.",
                    )
                )
                draft_id = _last_parameter(parameters, "draft") or identifier
                clear_draft_key = self._draft_key("encounter", draft_id)
            reference_action = _last_parameter(parameters, "reference")
            if reference_action == "linked":
                notice = PageNotice(
                    "success",
                    "Reference linked",
                    "The contextual link was appended in encounter-authored order.",
                )
            elif reference_action == "unlinked":
                notice = PageNotice(
                    "success",
                    "Reference unlinked",
                    "Only this encounter/reference pair was removed.",
                )
            body = render_encounter(
                self.queries.get_encounter(identifier),
                self.project_label,
                csrf_token=self.csrf_token,
                notice=notice,
                clear_draft_key=clear_draft_key,
            )
        elif kind == "revelation":
            created = _last_parameter(parameters, "created")
            saved = _last_parameter(parameters, "saved")
            notice = (
                PageNotice(
                    "success",
                    "Revelation created",
                    "The new revelation was committed at the current project revision.",
                )
                if created
                else _saved_notice("Revelation", saved)
            )
            body = render_revelation(
                self.queries.get_revelation(identifier),
                self.project_label,
                notice=notice,
                clear_draft_key=(
                    self._draft_key(
                        "revelation",
                        _last_parameter(parameters, "draft") or identifier,
                    )
                    if saved
                    else None
                ),
            )
        elif kind == "clue":
            created = _last_parameter(parameters, "created")
            saved = _last_parameter(parameters, "saved")
            notice = (
                PageNotice(
                    "success",
                    "Lead created",
                    "The new lead was committed and structural validation was recomputed.",
                )
                if created
                else _saved_notice("Lead", saved)
            )
            body = render_clue(
                self.queries.get_clue(identifier),
                self.project_label,
                notice=notice,
                clear_draft_key=(
                    self._draft_key(
                        "clue",
                        _last_parameter(parameters, "draft") or identifier,
                    )
                    if saved
                    else None
                ),
            )
        else:
            created = _last_parameter(parameters, "created")
            saved = _last_parameter(parameters, "saved")
            linked = _last_parameter(parameters, "linked")
            notice = (
                PageNotice(
                    "success",
                    "Reference created and linked",
                    "The reference and encounter link were committed atomically.",
                )
                if linked
                else PageNotice(
                    "success",
                    "Reference created",
                    "The new adventure reference was committed at the current project revision.",
                )
                if created
                else _saved_notice("Reference", saved)
            )
            body = render_reference(
                self.queries.get_reference(identifier),
                self.project_label,
                notice=notice,
                clear_draft_key=(
                    self._draft_key(
                        "reference",
                        _last_parameter(parameters, "draft") or identifier,
                    )
                    if saved or created or linked
                    else None
                ),
            )
        return _WebResponse(HTTPStatus.OK, body)

    def _dispatch_write(self, path: str, environ: WSGIEnvironment) -> _WebResponse:
        response: _WebResponse | None = None
        if path == "/reports/generate":
            response = (
                self._workspace_unavailable_response("Reports unavailable")
                if self.report_queries is None or self.report_commands is None
                else publish_reports_response(
                    self.report_queries,
                    self.report_commands,
                    self.project_label,
                    self.csrf_token,
                    environ,
                )
            )
        elif path == "/archives/create":
            response = (
                self._workspace_unavailable_response("Archives unavailable")
                if self.archive_queries is None
                or self.archive_commands is None
                or self.play is None
                else create_archive_response(
                    self.archive_queries,
                    self.play.queries,
                    self.archive_commands,
                    self.project_label,
                    self.csrf_token,
                    environ,
                )
            )
        elif path == "/archives/export-active":
            response = (
                self._workspace_unavailable_response("Archives unavailable")
                if self.archive_queries is None
                or self.archive_commands is None
                or self.play is None
                else export_active_response(
                    self.archive_queries,
                    self.play.queries,
                    self.archive_commands,
                    self.project_label,
                    self.csrf_token,
                    environ,
                )
            )
        elif path == "/archives/import":
            response = (
                self._workspace_unavailable_response("Archives unavailable")
                if self.archive_queries is None
                or self.archive_commands is None
                or self.play is None
                else import_archive_response(
                    self.archive_queries,
                    self.play.queries,
                    self.archive_commands,
                    self.project_label,
                    self.csrf_token,
                    environ,
                )
            )
        elif (archive_action := archive_action_route(path)) is not None:
            archive_id, action = archive_action
            response = (
                self._workspace_unavailable_response("Archives unavailable")
                if self.archive_queries is None
                or self.archive_commands is None
                or self.play is None
                else archive_action_response(
                    self.archive_queries,
                    self.play.queries,
                    self.archive_commands,
                    self.project_label,
                    self.csrf_token,
                    archive_id,
                    action,
                    environ,
                )
            )
        elif (play_response := self._play_workspace.write(path, environ)) is not None:
            response = play_response
        elif (authoring_response := self._authoring_actions.write(path, environ)) is not None:
            response = authoring_response
        if response is not None:
            return response
        return _WebResponse(
            HTTPStatus.METHOD_NOT_ALLOWED,
            render_error(
                405,
                "Method not allowed",
                "Only explicit authoring and workspace forms accept submitted changes.",
                self.project_label,
            ),
            extra_headers=(("Allow", "GET, HEAD"),),
        )

    def _internal_error_response(self) -> _WebResponse:
        return _WebResponse(
            HTTPStatus.INTERNAL_SERVER_ERROR,
            render_error(
                500,
                "Project could not be loaded",
                "Adventure Graph could not complete this request without exposing "
                "local project details.",
                self.project_label,
            ),
        )

    def _workspace_unavailable_response(self, heading: str) -> _WebResponse:
        return _WebResponse(
            HTTPStatus.NOT_FOUND,
            render_error(
                404,
                heading,
                "This workspace was not configured for the local interface.",
                self.project_label,
            ),
        )

    def _draft_key(self, kind: str, identifier: str) -> str:
        return self._authoring_actions.draft_key(kind, identifier)


def _reference_library_notice(parameters: dict[str, list[str]]) -> PageNotice | None:
    if _last_parameter(parameters, "removed"):
        return PageNotice(
            "success",
            "Reference removed",
            "The reference and only its explicitly confirmed encounter links were removed.",
        )
    return None


def _saved_notice(kind: str, saved: str) -> PageNotice | None:
    if not saved:
        return None
    if saved == "unchanged":
        return PageNotice(
            "info",
            "No changes to save",
            f"The {kind.lower()} already matched the submitted values.",
        )
    return PageNotice(
        "success",
        f"{kind} saved",
        "The authored file was committed at the current project revision.",
    )
