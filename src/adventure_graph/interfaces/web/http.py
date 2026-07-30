"""HTTP response and request-safety primitives for the local web adapter."""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from http import HTTPStatus
from string import hexdigits
from urllib.parse import unquote, unquote_to_bytes
from wsgiref.types import StartResponse, WSGIEnvironment

from adventure_graph.interfaces.web.form_parsing import CsrfValidationError

_LOCAL_AUTHORITY_PATTERN = r"(?:localhost|127\.0\.0\.1)(?::([0-9]{1,5}))?"
_ATTACHMENT_FILENAME_PATTERN = r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}"
_MAX_QUERY_STRING_LENGTH = 65_536
_MAX_QUERY_FIELDS = 100


class InvalidHostError(ValueError):
    """Raised when a request authority is outside the loopback trust boundary."""


class InvalidRequestTargetError(ValueError):
    """Raised when a request path is malformed or ambiguously encoded."""


class InvalidQueryStringError(ValueError):
    """Raised when a query string is oversized or ambiguously encoded."""


def require_local_authority(environ: WSGIEnvironment) -> None:
    """Require an explicit loopback Host authority and ignore proxy forwarding headers."""
    authority = str(environ.get("HTTP_HOST", "")).strip()
    if not authority:
        authority = str(environ.get("SERVER_NAME", "")).strip()
    match = re.fullmatch(_LOCAL_AUTHORITY_PATTERN, authority, re.IGNORECASE)
    if match is None:
        raise InvalidHostError("Use the loopback address printed when Adventure Graph started.")
    port = match.group(1)
    if port is not None and int(port) > 65535:
        raise InvalidHostError("Use the loopback address printed when Adventure Graph started.")


def require_safe_request_path(environ: WSGIEnvironment) -> str:
    """Return a normalized WSGI path after rejecting ambiguous request targets."""
    path = str(environ.get("PATH_INFO", "/"))
    if not path.startswith("/"):
        raise InvalidRequestTargetError("The request path must begin with '/'.")
    if "\\" in path or any(ord(character) < 32 or ord(character) == 127 for character in path):
        raise InvalidRequestTargetError("The request path contains a forbidden character.")
    for segment in path.split("/")[1:]:
        if not _has_valid_percent_encoding(segment):
            raise InvalidRequestTargetError("The request path contains a malformed percent escape.")
        try:
            decoded = unquote(segment, errors="strict")
        except UnicodeDecodeError as error:
            raise InvalidRequestTargetError(
                "The request path contains invalid percent-encoded text."
            ) from error
        if decoded in {".", ".."}:
            raise InvalidRequestTargetError("Dot segments are not accepted in local UI paths.")
        if "/" in decoded or "\\" in decoded:
            raise InvalidRequestTargetError(
                "Encoded path separators are not accepted in local UI paths."
            )
        if any(ord(character) < 32 or ord(character) == 127 for character in decoded):
            raise InvalidRequestTargetError("The request path contains a forbidden character.")
    return path


def require_safe_query_string(environ: WSGIEnvironment) -> str:
    """Return a bounded ASCII query string after strict percent-decoding validation."""
    query = str(environ.get("QUERY_STRING", ""))
    if len(query) > _MAX_QUERY_STRING_LENGTH:
        raise InvalidQueryStringError("The query string is too large for the local interface.")
    if any(ord(character) > 127 for character in query):
        raise InvalidQueryStringError("The query string must use percent-encoded UTF-8.")
    if any(ord(character) < 32 or ord(character) == 127 for character in query):
        raise InvalidQueryStringError("The query string contains a forbidden character.")
    if not _has_valid_percent_encoding(query):
        raise InvalidQueryStringError("The query string contains a malformed percent escape.")
    field_count = 0 if not query else query.count("&") + 1
    if field_count > _MAX_QUERY_FIELDS:
        raise InvalidQueryStringError("The query string contains too many fields.")
    try:
        unquote_to_bytes(query).decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise InvalidQueryStringError(
            "The query string contains invalid percent-encoded UTF-8."
        ) from error
    return query


def _has_valid_percent_encoding(value: str) -> bool:
    """Return whether every percent sign begins a complete hexadecimal escape."""
    index = 0
    while True:
        index = value.find("%", index)
        if index < 0:
            return True
        if index + 2 >= len(value) or any(
            character not in hexdigits for character in value[index + 1 : index + 3]
        ):
            return False
        index += 3


@dataclass(frozen=True, slots=True)
class WebResponse:
    """Complete WSGI response value before byte encoding."""

    status: HTTPStatus
    body: str
    content_type: str = "text/html; charset=utf-8"
    cache_control: str = "no-store"
    extra_headers: tuple[tuple[str, str], ...] = ()


def security_headers() -> tuple[tuple[str, str], ...]:
    """Return the fixed browser-security headers applied to every response."""
    return (
        (
            "Content-Security-Policy",
            (
                "default-src 'self'; style-src 'self'; script-src 'self'; "
                "img-src 'self' data:; connect-src 'none'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
            ),
        ),
        ("Cross-Origin-Opener-Policy", "same-origin"),
        ("Cross-Origin-Resource-Policy", "same-origin"),
        ("Permissions-Policy", "camera=(), geolocation=(), microphone=(), payment=(), usb=()"),
        ("Referrer-Policy", "no-referrer"),
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("X-Permitted-Cross-Domain-Policies", "none"),
    )


def emit_response(
    start_response: StartResponse,
    response: WebResponse,
    method: str,
) -> list[bytes]:
    """Encode and emit one complete response through the WSGI start callback."""
    encoded = response.body.encode("utf-8")
    headers = [
        ("Content-Type", response.content_type),
        ("Content-Length", str(len(encoded))),
        ("Cache-Control", response.cache_control),
        *security_headers(),
        *response.extra_headers,
    ]
    _require_safe_response_headers(headers)
    start_response(f"{response.status.value} {response.status.phrase}", headers)
    return [] if method == "HEAD" else [encoded]


def _require_safe_response_headers(headers: list[tuple[str, str]]) -> None:
    """Reject response headers containing controls before they reach the WSGI server."""
    for name, value in headers:
        if not name or any(
            not (character.isascii() and (character.isalnum() or character in "!#$%&'*+-.^_`|~"))
            for character in name
        ):
            raise ValueError("Response header names must use HTTP token characters.")
        if any(
            ord(character) < 32 or ord(character) == 127 or ord(character) > 255
            for character in value
        ):
            raise ValueError("Response header values must not contain control characters.")


def report_internal_error(environ: WSGIEnvironment, error: BaseException) -> None:
    """Write one local diagnostic while keeping implementation details out of HTTP responses."""
    stream = environ.get("wsgi.errors")
    write = getattr(stream, "write", None)
    if not callable(write):
        return
    message = f"Adventure Graph request failure: {type(error).__name__}: {error}\n"
    try:
        write(message)
    except TypeError:
        write(message.encode("utf-8", errors="replace"))


def require_csrf(submitted_token: str, expected_token: str) -> None:
    """Reject a form whose CSRF token does not match the application token."""
    if not secrets.compare_digest(submitted_token, expected_token):
        raise CsrfValidationError("Reload the editor and submit the form again.")


def last_parameter(parameters: dict[str, list[str]], name: str) -> str:
    """Return the last submitted query parameter value, or an empty string."""
    values = parameters.get(name, [])
    return values[-1] if values else ""


def attachment_disposition(filename: str) -> tuple[str, str]:
    """Return a conservative attachment header for one trusted local filename."""
    if filename in {".", ".."} or re.fullmatch(_ATTACHMENT_FILENAME_PATTERN, filename) is None:
        raise ValueError("Attachment filenames must be simple ASCII basenames.")
    return "Content-Disposition", f'attachment; filename="{filename}"'


def redirect(location: str) -> WebResponse:
    """Return a See Other response to a local application path."""
    if not location.startswith("/") or location.startswith("//"):
        raise ValueError("Redirects must remain within the local application.")
    if not _has_valid_percent_encoding(location):
        raise ValueError("Redirect targets must use valid percent escapes.")
    try:
        decoded = unquote(location, errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError("Redirect targets must use valid UTF-8.") from error
    if decoded.startswith("//") or "\\" in decoded:
        raise ValueError("Redirects must remain within the local application.")
    if any(ord(character) < 32 or ord(character) == 127 for character in decoded):
        raise ValueError("Redirect targets must not contain control characters.")
    return WebResponse(
        HTTPStatus.SEE_OTHER,
        "",
        extra_headers=(("Location", location),),
    )
