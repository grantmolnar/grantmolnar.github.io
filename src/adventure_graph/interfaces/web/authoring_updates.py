"""Shared control flow for revision-aware authoring updates."""

from __future__ import annotations

from collections.abc import Callable
from http import HTTPStatus
from typing import TypeVar

from adventure_graph.application.errors import NoChangesRequestedError
from adventure_graph.application.project import RevisionConflictError
from adventure_graph.interfaces.web.http import WebResponse, redirect

_CommandT = TypeVar("_CommandT")
_ResultT = TypeVar("_ResultT")


def execute_authoring_update(
    command: _CommandT,
    execute: Callable[[_CommandT], _ResultT],
    *,
    unchanged_location: str,
    render_error: Callable[[ValueError, HTTPStatus, str], WebResponse],
    rejected_heading: str,
) -> _ResultT | WebResponse:
    """Execute one update with the common conflict, no-op, and rejection contract."""
    try:
        return execute(command)
    except RevisionConflictError as error:
        return render_error(error, HTTPStatus.CONFLICT, "Revision conflict")
    except NoChangesRequestedError:
        return redirect(unchanged_location)
    except ValueError as error:
        return render_error(error, HTTPStatus.UNPROCESSABLE_ENTITY, rejected_heading)
