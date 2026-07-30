"""Focused tests for extracted authoring POST orchestration."""

from __future__ import annotations

from typing import cast

from adventure_graph.interfaces.web.authoring_action_workspace import (
    AuthoringActionWorkspace,
)
from adventure_graph.interfaces.web.contracts import AuthoringCommands, AuthoringQueries
from tests.support.web import build_wsgi_environ


def _workspace(project_label: str = "memory://adventure.json") -> AuthoringActionWorkspace:
    return AuthoringActionWorkspace(
        queries=cast(AuthoringQueries, object()),
        commands=cast(AuthoringCommands, object()),
        project_label=project_label,
        csrf_token="known-token",
    )


def test_authoring_action_workspace_declines_unrelated_post_routes() -> None:
    workspace = _workspace()

    assert workspace.write("/reports/generate", build_wsgi_environ("/")) is None
    assert workspace.write("/play/visit", build_wsgi_environ("/")) is None
    assert workspace.write("/not-a-route", build_wsgi_environ("/")) is None


def test_authoring_action_workspace_owns_stable_browser_draft_keys() -> None:
    first = _workspace("memory://adventure.json")
    second = _workspace("memory://adventure.json")
    other = _workspace("memory://other-adventure.json")

    assert first.draft_key("encounter", "alpha") == second.draft_key("encounter", "alpha")
    assert first.draft_key("encounter", "alpha").endswith(":encounter:alpha")
    assert first.draft_key("encounter", "alpha") != other.draft_key("encounter", "alpha")
