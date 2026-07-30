"""Tests for shared WSGI response emission."""

from __future__ import annotations

from http import HTTPStatus
from typing import cast

import pytest

from adventure_graph.interfaces.web.http import (
    InvalidHostError,
    InvalidQueryStringError,
    InvalidRequestTargetError,
    WebResponse,
    attachment_disposition,
    emit_response,
    redirect,
    report_internal_error,
    require_local_authority,
    require_safe_query_string,
    require_safe_request_path,
    security_headers,
)
from tests.support.web import (
    CapturedWSGIResponse,
    WSGIStartResponse,
    build_wsgi_environ,
)


def test_emit_response_preserves_header_order_and_encodes_body_once() -> None:
    captured = CapturedWSGIResponse()
    response = WebResponse(
        HTTPStatus.CREATED,
        "café",
        "text/plain; charset=utf-8",
        "private",
        (("Location", "/created"), ("X-Trace", "one")),
    )

    body = emit_response(
        cast(WSGIStartResponse, captured.start_response),
        response,
        "POST",
    )

    assert captured.status == "201 Created"
    assert captured.headers == [
        ("Content-Type", "text/plain; charset=utf-8"),
        ("Content-Length", str(len("café".encode()))),
        ("Cache-Control", "private"),
        *security_headers(),
        ("Location", "/created"),
        ("X-Trace", "one"),
    ]
    assert body == ["café".encode()]


def test_emit_response_keeps_head_metadata_but_suppresses_body() -> None:
    captured = CapturedWSGIResponse()
    response = WebResponse(HTTPStatus.OK, "body")

    body = emit_response(
        cast(WSGIStartResponse, captured.start_response),
        response,
        "HEAD",
    )

    assert body == []
    assert ("Content-Length", "4") in captured.headers


def test_local_authority_accepts_only_loopback_hostnames_and_ports() -> None:
    require_local_authority(build_wsgi_environ("/", host_authority="localhost"))
    require_local_authority(build_wsgi_environ("/", host_authority="LOCALHOST:8765"))
    require_local_authority(build_wsgi_environ("/", host_authority="127.0.0.1:1"))


@pytest.mark.parametrize(
    "authority",
    [
        "example.test",
        "127.0.0.2",
        "localhost.example.test",
        "localhost@evil.test",
        "localhost:65536",
        "localhost, evil.test",
        "[::1]:8765",
    ],
)
def test_local_authority_rejects_noncanonical_or_non_loopback_hosts(authority: str) -> None:
    with pytest.raises(InvalidHostError, match="loopback address"):
        require_local_authority(build_wsgi_environ("/", host_authority=authority))


def test_safe_request_path_rejects_backslashes_controls_and_dot_segments() -> None:
    for path in (
        "encounters/alpha",
        "/encounters/../alpha",
        "/encounters/%2E%2E/alpha",
        "/encounters/alpha%2Fbeta",
        "/encounters/alpha%ZZbeta",
        "/encounters\\alpha",
        "/bad\x00",
    ):
        with pytest.raises(InvalidRequestTargetError):
            require_safe_request_path(build_wsgi_environ(path))


def test_security_headers_isolate_the_local_browser_context() -> None:
    headers = dict(security_headers())

    assert headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert headers["Permissions-Policy"] == (
        "camera=(), geolocation=(), microphone=(), payment=(), usb=()"
    )
    assert headers["X-Permitted-Cross-Domain-Policies"] == "none"


def test_safe_query_string_accepts_bounded_percent_encoded_utf8() -> None:
    environ = build_wsgi_environ(
        "/play",
        query="encounter=alpha&note=caf%C3%A9",
    )

    assert require_safe_query_string(environ) == "encounter=alpha&note=caf%C3%A9"


def test_safe_query_string_accepts_the_exact_field_limit() -> None:
    query = "&".join(f"field{index}=1" for index in range(100))

    assert require_safe_query_string(build_wsgi_environ("/", query=query)) == query


@pytest.mark.parametrize(
    "query",
    [
        "note=%ZZ",
        "note=%FF",
        "note=café",
        "note=bad\x00value",
        "&".join(f"field{index}=1" for index in range(101)),
        "x=" + ("a" * 65_536),
    ],
)
def test_safe_query_string_rejects_ambiguous_or_oversized_values(query: str) -> None:
    with pytest.raises(InvalidQueryStringError):
        require_safe_query_string(build_wsgi_environ("/", query=query))


def test_attachment_disposition_accepts_only_simple_ascii_basenames() -> None:
    assert attachment_disposition("session-01-recap.md") == (
        "Content-Disposition",
        'attachment; filename="session-01-recap.md"',
    )

    for filename in ("../secret.md", "bad\r\nX-Evil: yes.md", "résumé.md", ""):
        with pytest.raises(ValueError, match="simple ASCII basenames"):
            attachment_disposition(filename)


def test_redirect_refuses_external_or_control_character_targets() -> None:
    assert dict(redirect("/play?notice=1").extra_headers)["Location"] == "/play?notice=1"

    for location in (
        "https://example.test",
        "//example.test",
        "/%2Fexample.test",
        "/\\example.test",
        "/%5Cexample.test",
        "/play%ZZ",
        "/play\r\nX-Evil: yes",
    ):
        with pytest.raises(ValueError, match="Redirect"):
            redirect(location)


def test_internal_error_report_keeps_diagnostic_on_local_wsgi_error_stream() -> None:
    environ = build_wsgi_environ("/")

    report_internal_error(
        environ,
        FileNotFoundError("/Users/grant/private/adventure.json"),
    )

    stream = environ["wsgi.errors"]
    assert hasattr(stream, "getvalue")
    diagnostic = stream.getvalue()
    assert b"FileNotFoundError" in diagnostic
    assert b"/Users/grant/private/adventure.json" in diagnostic


def test_emit_response_rejects_control_characters_in_extra_headers() -> None:
    captured = CapturedWSGIResponse()
    response = WebResponse(
        HTTPStatus.OK,
        "body",
        extra_headers=(("X-Test", "safe\r\nX-Evil: yes"),),
    )

    with pytest.raises(ValueError, match="control characters"):
        emit_response(
            cast(WSGIStartResponse, captured.start_response),
            response,
            "GET",
        )
