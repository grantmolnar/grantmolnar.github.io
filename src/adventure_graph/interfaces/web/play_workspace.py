"""Cohesive browser routes for live play, run controls, journals, and ledgers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from http import HTTPStatus
from urllib.parse import parse_qs, urlencode
from wsgiref.types import WSGIEnvironment

from adventure_graph.application.dice import DiceExpressionError
from adventure_graph.application.play_journal import CorrectLatestPlayOperationCommand
from adventure_graph.application.project import (
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.interfaces.web.contracts import PlayCapability
from adventure_graph.interfaces.web.form_parsing import CsrfValidationError
from adventure_graph.interfaces.web.http import WebResponse, last_parameter, redirect, require_csrf
from adventure_graph.interfaces.web.journal_rendering import render_journal
from adventure_graph.interfaces.web.page_rendering import render_error
from adventure_graph.interfaces.web.play_forms import parse_play_dice_roll_form
from adventure_graph.interfaces.web.play_ledger_workspace import (
    play_ledger_download_response,
    play_ledger_page_response,
)
from adventure_graph.interfaces.web.play_rendering import render_play
from adventure_graph.interfaces.web.play_rendering_support import present_play_error
from adventure_graph.interfaces.web.play_write_actions import (
    PlayActionConflictError,
    PlayActionRejectedError,
    PlayWriteActions,
)
from adventure_graph.interfaces.web.run_forms import (
    parse_correction_form,
    parse_run_clue_form,
    parse_run_consequence_form,
    parse_run_note_form,
    parse_run_revelation_form,
    parse_run_unlock_form,
    parse_run_visit_form,
)
from adventure_graph.interfaces.web.run_rendering import render_run
from adventure_graph.interfaces.web.view_models import PageNotice, PlayFormValues, RunFormValues


@dataclass(frozen=True, slots=True)
class PlayWebWorkspace:
    """Own every browser route backed by the optional play capability."""

    capability: PlayCapability | None
    project_label: str
    csrf_token: str

    def read(self, path: str, query: str) -> WebResponse | None:
        """Serve one play-family GET/HEAD route or decline unrelated paths."""
        if path == "/play":
            return self._play_page(query)
        if path == "/run":
            return self._run_page(query)
        if path == "/journal":
            return self._journal_page(query)
        if path in {"/play/ledgers", "/play/ledgers/download"}:
            return self._ledger_page(path, query)
        return None

    def write(self, path: str, environ: WSGIEnvironment) -> WebResponse | None:
        """Serve one play-family POST route or decline unrelated paths."""
        if path.startswith("/play/"):
            if self.capability is None:
                return self._unavailable("Play mode unavailable")
            return self._play_write(path, environ)
        if path.startswith("/run/"):
            if self.capability is None:
                return self._unavailable("Recovery console unavailable")
            return self._run_write(path, environ)
        if path == "/journal/correct":
            if self.capability is None:
                return self._unavailable("Journal unavailable")
            return self._correct_latest_operation(environ)
        return None

    def _play_page(self, query: str) -> WebResponse:
        if self.capability is None:
            return self._unavailable("Play mode unavailable")
        parameters = parse_qs(query, keep_blank_values=True)
        return WebResponse(
            HTTPStatus.OK,
            render_play(
                self.capability.queries.get_run(),
                self.project_label,
                csrf_token=self.csrf_token,
                focus_encounter_id=last_parameter(parameters, "encounter"),
                selected_reference_id=last_parameter(parameters, "reference"),
                notice=_play_notice(parameters),
                clear_draft_visit_number=_optional_query_int(parameters, "clear_draft"),
                show_session_review=(last_parameter(parameters, "action") == "session-ended"),
            ),
        )

    def _run_page(self, query: str) -> WebResponse:
        if self.capability is None:
            return self._unavailable("Recovery console unavailable")
        parameters = parse_qs(query, keep_blank_values=True)
        return WebResponse(
            HTTPStatus.OK,
            render_run(
                self.capability.queries.get_run(),
                self.project_label,
                csrf_token=self.csrf_token,
                notice=_run_notice(parameters),
            ),
        )

    def _journal_page(self, query: str) -> WebResponse:
        if self.capability is None:
            return self._unavailable("Journal unavailable")
        parameters = parse_qs(query, keep_blank_values=True)
        corrected = last_parameter(parameters, "corrected")
        notice = (
            PageNotice(
                "success",
                "Operation corrected",
                f"Operation {corrected} is now void; the audit event remains in history.",
            )
            if corrected
            else None
        )
        workspace = self.capability.queries.get_journal_workspace()
        return WebResponse(
            HTTPStatus.OK,
            render_journal(
                workspace.journal,
                self.project_label,
                csrf_token=self.csrf_token,
                dashboard=workspace.dashboard,
                notice=notice,
            ),
        )

    def _ledger_page(self, path: str, query: str) -> WebResponse:
        if self.capability is None or self.capability.queries.ledgers is None:
            return self._workspace_unavailable("Play ledgers unavailable")
        if path == "/play/ledgers/download":
            return play_ledger_download_response(self.capability.queries, query)
        return play_ledger_page_response(
            self.capability.queries,
            query,
            csrf_token=self.csrf_token,
        )

    def _play_write(
        self,
        path: str,
        environ: WSGIEnvironment,
    ) -> WebResponse:
        capability = self._configured_capability()
        if path == "/play/dice/roll":
            return self._play_dice_roll(environ)
        executor = PlayWriteActions(capability.commands, self._require_csrf).executor_for(path)
        if executor is None:
            return self._method_not_allowed("No Play mode action matches this submitted form.")
        try:
            outcome = executor(environ)
        except CsrfValidationError:
            raise
        except PlayActionConflictError as failure:
            return self._play_error(
                failure.values,
                failure.error,
                HTTPStatus.CONFLICT,
                "Revision conflict",
            )
        except PlayActionRejectedError as failure:
            return self._play_error(
                failure.values,
                failure.error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                failure.heading,
            )
        except ValueError as error:
            return self._play_error(
                PlayFormValues(),
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Play operation was not recorded",
            )
        parameters = {
            "action": outcome.action,
            "operation": str(outcome.operation_number),
        }
        if outcome.values.focus_encounter_id:
            parameters["encounter"] = outcome.values.focus_encounter_id
        if outcome.values.selected_reference_id:
            parameters["reference"] = outcome.values.selected_reference_id
        if outcome.visit_number is not None:
            parameters["visit"] = str(outcome.visit_number)
        if outcome.clear_draft_visit_number is not None:
            parameters["clear_draft"] = str(outcome.clear_draft_visit_number)
        return redirect(f"/play?{urlencode(parameters)}")

    def _play_dice_roll(self, environ: WSGIEnvironment) -> WebResponse:
        capability = self._configured_capability()
        values, command, token = parse_play_dice_roll_form(environ)
        self._require_csrf(token)
        try:
            result = capability.commands.roll_dice(command)
        except DiceExpressionError as error:
            return self._play_error(
                values,
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Dice expression was not rolled",
            )
        return WebResponse(
            HTTPStatus.OK,
            render_play(
                capability.queries.get_run(),
                self.project_label,
                csrf_token=self.csrf_token,
                focus_encounter_id=values.focus_encounter_id or None,
                values=replace(values, dice_expression=result.expression),
                dice_roll=result,
            ),
        )

    def _play_error(
        self,
        values: PlayFormValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        capability = self._configured_capability()
        dashboard = capability.queries.get_run()
        message = present_play_error(error, dashboard.adventure)
        return WebResponse(
            status,
            render_play(
                dashboard,
                self.project_label,
                csrf_token=self.csrf_token,
                focus_encounter_id=values.focus_encounter_id or None,
                selected_reference_id=values.selected_reference_id or None,
                notice=PageNotice(
                    "error",
                    heading,
                    f"{message} Submitted text was preserved, and any browser-local "
                    "notebook draft was left unchanged.",
                ),
                values=values,
            ),
        )

    def _run_write(self, path: str, environ: WSGIEnvironment) -> WebResponse:
        capability = self._configured_capability()
        values = RunFormValues()
        try:
            if path == "/run/visit":
                values, command, token = parse_run_visit_form(environ)
                self._require_csrf(token)
                result = capability.commands.record_visit(command)
                location = (
                    f"/run?action=visit&operation={result.operation_number}"
                    f"&visit={result.visit_number}"
                )
            elif path == "/run/clue":
                values, command, token = parse_run_clue_form(environ)
                self._require_csrf(token)
                result = capability.commands.spot_clue(command)
                location = f"/run?action=clue&operation={result.operation_number}"
            elif path == "/run/revelation":
                values, command, token = parse_run_revelation_form(environ)
                self._require_csrf(token)
                result = capability.commands.establish_revelation(command)
                location = f"/run?action=revelation&operation={result.operation_number}"
            elif path == "/run/unlock":
                values, command, token = parse_run_unlock_form(environ)
                self._require_csrf(token)
                result = capability.commands.unlock_encounter(command)
                location = f"/run?action=unlock&operation={result.operation_number}"
            elif path == "/run/note":
                values, command, token = parse_run_note_form(environ)
                self._require_csrf(token)
                result = capability.commands.add_visit_note(command)
                location = f"/run?action=note&operation={result.operation_number}"
            elif path == "/run/consequence":
                values, command, token = parse_run_consequence_form(environ)
                self._require_csrf(token)
                result = capability.commands.record_consequence(command)
                location = f"/run?action=consequence&operation={result.operation_number}"
            elif path == "/run/correct":
                reason, revision, token = parse_correction_form(environ)
                values = RunFormValues(correction_reason=reason)
                self._require_csrf(token)
                result = capability.commands.correct_latest(
                    CorrectLatestPlayOperationCommand(
                        reason=reason,
                        expected_revision=ProjectRevision(revision),
                    )
                )
                location = f"/run?action=corrected&operation={result.target_operation_number}"
            else:
                return self._method_not_allowed(
                    "No Recovery-console action matches this submitted form."
                )
        except CsrfValidationError:
            raise
        except RevisionConflictError as error:
            return self._run_error(values, error, HTTPStatus.CONFLICT, "Revision conflict")
        except ValueError as error:
            return self._run_error(
                values,
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Operation was not recorded",
            )
        return redirect(location)

    def _run_error(
        self,
        values: RunFormValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        capability = self._configured_capability()
        return WebResponse(
            status,
            render_run(
                capability.queries.get_run(),
                self.project_label,
                csrf_token=self.csrf_token,
                notice=PageNotice("error", heading, str(error)),
                values=values,
            ),
        )

    def _correct_latest_operation(self, environ: WSGIEnvironment) -> WebResponse:
        capability = self._configured_capability()
        reason, revision, submitted_token = parse_correction_form(environ)
        self._require_csrf(submitted_token)
        try:
            result = capability.commands.correct_latest(
                CorrectLatestPlayOperationCommand(
                    reason=reason,
                    expected_revision=ProjectRevision(revision),
                )
            )
        except RevisionConflictError as error:
            return self._journal_error(
                error,
                HTTPStatus.CONFLICT,
                "Revision conflict",
                reason,
            )
        except ValueError as error:
            return self._journal_error(
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Operation was not corrected",
                reason,
            )
        return redirect(f"/journal?corrected={result.target_operation_number}")

    def _journal_error(
        self,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
        correction_reason: str,
    ) -> WebResponse:
        workspace = self._configured_capability().queries.get_journal_workspace()
        return WebResponse(
            status,
            render_journal(
                workspace.journal,
                self.project_label,
                csrf_token=self.csrf_token,
                dashboard=workspace.dashboard,
                notice=PageNotice("error", heading, str(error)),
                correction_reason=correction_reason,
            ),
        )

    def _configured_capability(self) -> PlayCapability:
        if self.capability is None:
            raise RuntimeError("Play workspace was used without a configured capability.")
        return self.capability

    def _require_csrf(self, submitted_token: str) -> None:
        require_csrf(submitted_token, self.csrf_token)

    def _unavailable(self, heading: str) -> WebResponse:
        return WebResponse(
            HTTPStatus.NOT_FOUND,
            render_error(
                404,
                heading,
                "No play journal was configured for this interface.",
                self.project_label,
            ),
        )

    def _workspace_unavailable(self, heading: str) -> WebResponse:
        return WebResponse(
            HTTPStatus.NOT_FOUND,
            render_error(
                404,
                heading,
                "This workspace was not configured for the local interface.",
                self.project_label,
            ),
        )

    def _method_not_allowed(self, detail: str) -> WebResponse:
        return WebResponse(
            HTTPStatus.METHOD_NOT_ALLOWED,
            render_error(405, "Method not allowed", detail, self.project_label),
            extra_headers=(("Allow", "GET, HEAD"),),
        )


def _play_notice(parameters: dict[str, list[str]]) -> PageNotice | None:
    action = last_parameter(parameters, "action")
    operation = last_parameter(parameters, "operation")
    visit = last_parameter(parameters, "visit")
    notices = {
        "session-started": ("Session begun", f"Session history began as operation {operation}."),
        "session-ended": (
            "Session ended",
            f"The closing boundary was committed as operation {operation}.",
        ),
        "visit": ("Encounter entered", f"Visit {visit} was committed as operation {operation}."),
        "clue-found": ("Lead found", f"The discovery was committed as operation {operation}."),
        "clue-missed": (
            "Lead missed",
            f"The missed opportunity was committed as operation {operation}.",
        ),
        "revelation-established": (
            "Revelation established",
            f"The conclusion was committed as operation {operation}.",
        ),
        "revelation-foreclosed": (
            "Revelation foreclosed",
            f"The judgment was committed as operation {operation}.",
        ),
        "revelation-reopened": (
            "Revelation reopened",
            f"The revised judgment was committed as operation {operation}.",
        ),
        "encounter-unlocked": (
            "Encounter unlocked",
            f"The GM override was committed as operation {operation}.",
        ),
        "note": ("Encounter note committed", f"The note was committed as operation {operation}."),
        "reference-note": (
            "Reference note committed",
            f"The chronological reference note was committed as operation {operation}.",
        ),
        "consequence": (
            "Legacy persistent note recorded",
            f"The legacy persistent note was committed as operation {operation}.",
        ),
        "transition": (
            "Transition committed",
            f"The complete transition was committed as operation {operation}.",
        ),
        "dice-recorded": (
            "Dice roll recorded",
            f"The retained result was committed as operation {operation}.",
        ),
        "encounter-authored": (
            "Encounter added",
            (
                "The new encounter is focused for review. "
                "The current visit and play history did not change."
            ),
        ),
        "clue-authored": (
            "Lead added",
            (
                "The new lead is available at this encounter. "
                "The current visit and play history did not change."
            ),
        ),
        "reference-authored": (
            "Reference added",
            (
                "The new reference is linked to this encounter. "
                "The current visit and play history did not change."
            ),
        ),
    }
    selected = notices.get(action)
    return None if selected is None else PageNotice("success", selected[0], selected[1])


def _optional_query_int(parameters: dict[str, list[str]], name: str) -> int | None:
    value = last_parameter(parameters, name)
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _run_notice(parameters: dict[str, list[str]]) -> PageNotice | None:
    action = last_parameter(parameters, "action")
    operation = last_parameter(parameters, "operation")
    visit = last_parameter(parameters, "visit")
    notices = {
        "visit": ("Visit recorded", f"Visit {visit} was committed as operation {operation}."),
        "clue": ("Lead discovered", f"The lead discovery was committed as operation {operation}."),
        "revelation": (
            "Revelation established",
            f"The conclusion and any automatic unlock were committed as operation {operation}.",
        ),
        "unlock": (
            "Encounter unlocked",
            f"The explicit unlock was committed as operation {operation}.",
        ),
        "note": ("Encounter note recorded", f"The note was committed as operation {operation}."),
        "consequence": (
            "Legacy persistent note recorded",
            f"The legacy persistent note was committed as operation {operation}.",
        ),
        "corrected": (
            "Operation corrected",
            f"Operation {operation} is now void; its audit history remains visible.",
        ),
    }
    selected = notices.get(action)
    return None if selected is None else PageNotice("success", selected[0], selected[1])
