"""End-to-end WSGI request-boundary regressions for the local-only web adapter."""

from __future__ import annotations

from dataclasses import replace
from typing import Never

from tests.support.web import build_authoring_app, request_wsgi


def test_authoring_app_rejects_dns_rebinding_host_before_dispatch() -> None:
    app, project = build_authoring_app()

    status, _, body = request_wsgi(app, "/", host_authority="attacker.example")

    assert status == "421 Misdirected Request"
    assert "Request host rejected" in body
    assert "memory://adventure.json" not in body
    assert project.commit_count == 0


def test_authoring_app_ignores_forwarded_host_without_a_supported_proxy_boundary() -> None:
    app, _ = build_authoring_app()

    status, _, body = request_wsgi(
        app,
        "/",
        host_authority="127.0.0.1:8765",
        extra_environ={"HTTP_X_FORWARDED_HOST": "attacker.example"},
    )

    assert status == "200 OK"
    assert "Complete Four" in body


def test_authoring_app_rejects_noncanonical_request_paths() -> None:
    app, _ = build_authoring_app()

    status, _, body = request_wsgi(app, "/encounters/../alpha")

    assert status == "400 Bad Request"
    assert "Request path rejected" in body


def test_authoring_app_rejects_malformed_or_oversized_query_before_dispatch() -> None:
    app, project = build_authoring_app()

    malformed_status, _, malformed_body = request_wsgi(app, "/", query="saved=%ZZ")
    oversized_status, _, oversized_body = request_wsgi(
        app,
        "/",
        query="x=" + ("a" * 65_536),
    )

    assert malformed_status == oversized_status == "400 Bad Request"
    assert "Query string rejected" in malformed_body
    assert "Query string rejected" in oversized_body
    assert "memory://adventure.json" not in malformed_body + oversized_body
    assert project.commit_count == 0


def test_authoring_app_contains_internal_failures_without_disclosing_local_paths() -> None:
    app, _ = build_authoring_app()

    def broken_overview() -> Never:
        raise FileNotFoundError("/Users/grant/private/adventure.json")

    app = replace(app, queries=replace(app.queries, get_overview=broken_overview))

    status, _, body = request_wsgi(app, "/")

    assert status == "500 Internal Server Error"
    assert "Project could not be loaded" in body
    assert "/Users/grant/private/adventure.json" not in body
    assert "FileNotFoundError" not in body
