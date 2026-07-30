"""HTTP coordination for operational Play-mode ledgers."""

from __future__ import annotations

from http import HTTPStatus
from urllib.parse import parse_qs

from adventure_graph.application.errors import EntityNotFoundError
from adventure_graph.application.play_ledgers import (
    PlayLedgerKind,
    PlayLedgerScope,
)
from adventure_graph.interfaces.web.contracts import PlayLedgerQueries, PlayQueries
from adventure_graph.interfaces.web.http import (
    WebResponse,
    attachment_disposition,
    last_parameter,
)
from adventure_graph.interfaces.web.play_ledger_rendering import render_play_ledgers

_ALLOWED_KINDS = ("encounters", "clues", "revelations", "narrative", "recap")
_ALLOWED_SCOPES = ("playthrough", "session")


def play_ledger_page_response(queries: PlayQueries, query: str, *, csrf_token: str) -> WebResponse:
    """Render one selected operational ledger."""
    kind, scope = _selection(query)
    workspace = _ledger_queries(queries).get_workspace(scope)
    return WebResponse(
        HTTPStatus.OK,
        render_play_ledgers(
            workspace.ledgers,
            selected_kind=kind,
            dashboard=workspace.dashboard,
            csrf_token=csrf_token,
        ),
    )


def play_ledger_download_response(queries: PlayQueries, query: str) -> WebResponse:
    """Return one derived operational ledger as a Markdown attachment."""
    kind, scope = _selection(query)
    result = _ledger_queries(queries).get_ledgers(scope)
    document = result.document_index()[kind]
    return WebResponse(
        HTTPStatus.OK,
        document.content,
        "text/markdown; charset=utf-8",
        "no-store",
        (attachment_disposition(document.name),),
    )


def _selection(query: str) -> tuple[PlayLedgerKind, PlayLedgerScope]:
    parameters = parse_qs(query, keep_blank_values=True)
    raw_kind = last_parameter(parameters, "kind") or "encounters"
    raw_scope = last_parameter(parameters, "scope") or "playthrough"
    if raw_kind not in _ALLOWED_KINDS:
        raise EntityNotFoundError(f"Unknown play-ledger kind {raw_kind!r}.")
    if raw_scope not in _ALLOWED_SCOPES:
        raise EntityNotFoundError(f"Unknown play-ledger scope {raw_scope!r}.")
    return raw_kind, raw_scope


def _ledger_queries(queries: PlayQueries) -> PlayLedgerQueries:
    if queries.ledgers is None:
        raise ValueError("Operational play ledgers were not configured for this interface.")
    return queries.ledgers
