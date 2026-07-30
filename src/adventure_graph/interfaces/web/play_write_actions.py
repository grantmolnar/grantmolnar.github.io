"""Typed executors for committed Play mode form actions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Protocol, TypeVar
from wsgiref.types import WSGIEnvironment

from adventure_graph.application.project import RevisionConflictError
from adventure_graph.interfaces.web.contracts import PlayCommands
from adventure_graph.interfaces.web.form_parsing import CsrfValidationError
from adventure_graph.interfaces.web.play_forms import (
    parse_play_clue_form,
    parse_play_consequence_form,
    parse_play_dice_record_form,
    parse_play_end_session_form,
    parse_play_enter_form,
    parse_play_judgment_form,
    parse_play_note_form,
    parse_play_reference_note_form,
    parse_play_revelation_form,
    parse_play_start_session_form,
    parse_play_transition_form,
    parse_play_unlock_form,
)
from adventure_graph.interfaces.web.view_models import PlayFormValues


@dataclass(frozen=True, slots=True)
class CommittedPlayAction:
    """Redirect metadata produced by one successful committed Play action."""

    values: PlayFormValues
    action: str
    operation_number: int
    visit_number: int | None = None
    clear_draft_visit_number: int | None = None


class PlayActionConflictError(Exception):
    """Carry preserved form values with a revision conflict."""

    def __init__(self, values: PlayFormValues, error: RevisionConflictError) -> None:
        super().__init__(str(error))
        self.values = values
        self.error = error


class PlayActionRejectedError(Exception):
    """Carry preserved form values and a user-facing rejection heading."""

    def __init__(
        self,
        values: PlayFormValues,
        error: ValueError,
        heading: str = "Play operation was not recorded",
    ) -> None:
        super().__init__(str(error))
        self.values = values
        self.error = error
        self.heading = heading


class PlayActionExecutor(Protocol):
    """Execute one typed Play form and return its redirect metadata."""

    def __call__(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Parse, authorize, execute, and describe one committed action."""
        ...


_CommandT = TypeVar("_CommandT")
_ResultT = TypeVar("_ResultT")


@dataclass(frozen=True, slots=True)
class PlayWriteActions:
    """Resolve committed Play routes to small command-specific executors."""

    commands: PlayCommands
    require_csrf: Callable[[str], None]

    def executor_for(self, path: str) -> PlayActionExecutor | None:
        """Return the executor owned by one exact Play action route."""
        executors: dict[str, PlayActionExecutor] = {
            "/play/session/start": self.start_session,
            "/play/session/end": self.end_session,
            "/play/enter": self.enter_encounter,
            "/play/clue/found": self.spot_clue,
            "/play/clue/missed": self.miss_clue,
            "/play/revelation/establish": self.establish_revelation,
            "/play/revelation/foreclose": self.foreclose_revelation,
            "/play/revelation/reopen": self.reopen_revelation,
            "/play/unlock": self.unlock_encounter,
            "/play/note": self.add_visit_note,
            "/play/reference/note": self.record_reference_note,
            "/play/consequence": self.record_consequence,
            "/play/dice/record": self.record_dice_roll,
            "/play/transition": self.transition_visit,
        }
        return executors.get(path)

    def _commit(
        self,
        values: PlayFormValues,
        command: _CommandT,
        token: str,
        execute: Callable[[_CommandT], _ResultT],
        *,
        rejected_heading: str = "Play operation was not recorded",
    ) -> _ResultT:
        try:
            self.require_csrf(token)
            return execute(command)
        except CsrfValidationError:
            raise
        except RevisionConflictError as error:
            raise PlayActionConflictError(values, error) from error
        except ValueError as error:
            raise PlayActionRejectedError(values, error, rejected_heading) from error

    def start_session(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Begin an explicit session."""
        values, command, token = parse_play_start_session_form(environ)
        result = self._commit(values, command, token, self.commands.start_session)
        return CommittedPlayAction(values, "session-started", result.operation_number)

    def end_session(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """End the active explicit session."""
        values, command, token = parse_play_end_session_form(environ)
        result = self._commit(values, command, token, self.commands.end_session)
        return CommittedPlayAction(values, "session-ended", result.operation_number)

    def enter_encounter(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Record a visit to one encounter."""
        values, command, token = parse_play_enter_form(environ)
        result = self._commit(values, command, token, self.commands.record_visit)
        return CommittedPlayAction(
            replace(values, focus_encounter_id=command.encounter_id),
            "visit",
            result.operation_number,
            visit_number=result.visit_number,
        )

    def spot_clue(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Record one clue discovery."""
        values, command, token = parse_play_clue_form(environ, missed=False)
        result = self._commit(values, command, token, self.commands.spot_clue)
        return CommittedPlayAction(values, "clue-found", result.operation_number)

    def miss_clue(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Record one missed clue opportunity."""
        values, command, token = parse_play_clue_form(environ, missed=True)
        result = self._commit(values, command, token, self.commands.miss_clue)
        return CommittedPlayAction(values, "clue-missed", result.operation_number)

    def establish_revelation(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Record one established revelation."""
        values, command, token = parse_play_revelation_form(environ)
        result = self._commit(values, command, token, self.commands.establish_revelation)
        return CommittedPlayAction(values, "revelation-established", result.operation_number)

    def foreclose_revelation(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Record one revelation foreclosure."""
        values, command, token = parse_play_judgment_form(environ)
        result = self._commit(values, command, token, self.commands.foreclose_revelation)
        return CommittedPlayAction(values, "revelation-foreclosed", result.operation_number)

    def reopen_revelation(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Reverse one active revelation foreclosure."""
        values, command, token = parse_play_judgment_form(environ)
        result = self._commit(values, command, token, self.commands.reopen_revelation)
        return CommittedPlayAction(values, "revelation-reopened", result.operation_number)

    def unlock_encounter(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Record one explicit encounter unlock."""
        values, command, token = parse_play_unlock_form(environ)
        result = self._commit(values, command, token, self.commands.unlock_encounter)
        return CommittedPlayAction(values, "encounter-unlocked", result.operation_number)

    def add_visit_note(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Append one note to an existing visit."""
        values, command, token = parse_play_note_form(environ)
        result = self._commit(values, command, token, self.commands.add_visit_note)
        return CommittedPlayAction(
            values,
            "note",
            result.operation_number,
            clear_draft_visit_number=command.visit_number,
        )

    def record_reference_note(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Append one note to a persistent authored reference."""
        values, command, token = parse_play_reference_note_form(environ)
        result = self._commit(values, command, token, self.commands.record_reference_note)
        return CommittedPlayAction(values, "reference-note", result.operation_number)

    def record_consequence(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Record one durable encounter consequence."""
        values, command, token = parse_play_consequence_form(environ)
        result = self._commit(values, command, token, self.commands.record_consequence)
        return CommittedPlayAction(values, "consequence", result.operation_number)

    def record_dice_roll(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Commit one previously rolled dice result."""
        values, command, token = parse_play_dice_record_form(environ)
        result = self._commit(values, command, token, self.commands.record_dice_roll)
        return CommittedPlayAction(values, "dice-recorded", result.operation_number)

    def transition_visit(self, environ: WSGIEnvironment) -> CommittedPlayAction:
        """Record current-visit outcomes and an optional destination visit atomically."""
        values, command, token = parse_play_transition_form(environ)
        result = self._commit(
            values,
            command,
            token,
            self.commands.transition_visit,
            rejected_heading="Visit update was not recorded",
        )
        if command.destination_encounter_id is not None:
            values = replace(values, focus_encounter_id=command.destination_encounter_id)
        return CommittedPlayAction(
            values,
            "transition",
            result.operation_number,
            visit_number=result.destination_visit_number,
            clear_draft_visit_number=command.source_visit_number,
        )
