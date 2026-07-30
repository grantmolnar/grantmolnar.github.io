"""Adversarial tests for the bounded URL-encoded form request parser."""

from __future__ import annotations

from io import BytesIO

import pytest

from adventure_graph.interfaces.web.form_parsing import (
    FormTooLargeError,
    InvalidFormError,
    one_uploaded_file,
    parse_form_fields,
    parse_multipart_form,
)
from tests.support.web import WSGIRequestEnvironment, build_wsgi_environ


def _environment(body: bytes, **changes: object) -> WSGIRequestEnvironment:
    environ = build_wsgi_environ(
        "/submit",
        method="POST",
        body=body,
        content_type="application/x-www-form-urlencoded; charset=UTF-8",
    )
    environ.update(changes)
    return environ


def test_form_parser_accepts_canonical_utf8_percent_encoding() -> None:
    fields = parse_form_fields(_environment(b"name=caf%C3%A9&empty="), max_num_fields=2)

    assert fields == {"name": ["caf\N{LATIN SMALL LETTER E WITH ACUTE}"], "empty": [""]}


@pytest.mark.parametrize("content_length", ["", "-1", "+1", "1.0", "one", "\uff11\uff12"])
def test_form_parser_rejects_noncanonical_content_lengths(content_length: str) -> None:
    with pytest.raises(InvalidFormError, match="content length is invalid"):
        parse_form_fields(
            _environment(b"a=1", CONTENT_LENGTH=content_length),
            max_num_fields=1,
        )


def test_form_parser_rejects_oversize_body_before_reading_input() -> None:
    class UnreadableBody:
        def read(self, size: int) -> bytes:
            raise AssertionError(f"body should not have been read: {size}")

    with pytest.raises(FormTooLargeError, match="2,000,000 bytes"):
        parse_form_fields(
            _environment(
                b"",
                CONTENT_LENGTH="2000001",
                **{"wsgi.input": UnreadableBody()},
            ),
            max_num_fields=1,
        )


def test_form_parser_rejects_missing_or_truncated_body_streams() -> None:
    with pytest.raises(InvalidFormError, match="body is unavailable"):
        parse_form_fields(
            _environment(b"a=1", **{"wsgi.input": None}),
            max_num_fields=1,
        )
    with pytest.raises(InvalidFormError, match="ended before"):
        parse_form_fields(
            _environment(
                b"a=1",
                CONTENT_LENGTH="10",
                **{"wsgi.input": BytesIO(b"a=1")},
            ),
            max_num_fields=1,
        )


def test_form_parser_rejects_raw_invalid_utf8() -> None:
    with pytest.raises(InvalidFormError, match="body is not valid UTF-8"):
        parse_form_fields(_environment(b"a=\xff"), max_num_fields=1)


def test_form_parser_rejects_invalid_percent_encoded_utf8() -> None:
    with pytest.raises(InvalidFormError, match="invalid percent-encoded UTF-8"):
        parse_form_fields(_environment(b"a=%C3%28"), max_num_fields=1)


@pytest.mark.parametrize("body", [b"a=%ZZ", b"a=%"])
def test_form_parser_rejects_malformed_percent_escapes(body: bytes) -> None:
    with pytest.raises(InvalidFormError, match="malformed percent escape"):
        parse_form_fields(_environment(body), max_num_fields=1)


def test_form_parser_rejects_malformed_fields_and_field_count_abuse() -> None:
    with pytest.raises(InvalidFormError, match="URL-encoded form is malformed"):
        parse_form_fields(_environment(b"a=1&broken"), max_num_fields=2)
    with pytest.raises(InvalidFormError, match="URL-encoded form is malformed"):
        parse_form_fields(_environment(b"a=1&b=2"), max_num_fields=1)


def _multipart_environment(
    *,
    fields: tuple[tuple[str, str], ...] = (),
    files: tuple[tuple[str, str, bytes], ...] = (),
    boundary: str = "adventure-graph-boundary",
) -> WSGIRequestEnvironment:
    chunks: list[bytes] = []
    for name, value in fields:
        chunks.extend(
            (
                f"--{boundary}\r\n".encode("ascii"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("ascii"),
                value.encode("utf-8"),
                b"\r\n",
            )
        )
    for name, filename, content in files:
        chunks.extend(
            (
                f"--{boundary}\r\n".encode("ascii"),
                (
                    f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                ).encode("ascii"),
                b"Content-Type: application/json\r\n\r\n",
                content,
                b"\r\n",
            )
        )
    chunks.append(f"--{boundary}--\r\n".encode("ascii"))
    return build_wsgi_environ(
        "/upload",
        method="POST",
        body=b"".join(chunks),
        content_type=f"multipart/form-data; boundary={boundary}",
    )


def test_multipart_parser_accepts_utf8_text_and_one_json_file() -> None:
    fields, files = parse_multipart_form(
        _multipart_environment(
            fields=(("csrf_token", "caf\N{LATIN SMALL LETTER E WITH ACUTE}"),),
            files=(("document", "adventure.json", b'{"schema_version": 3}'),),
        ),
        max_num_fields=2,
        max_file_bytes=100,
    )

    assert fields == {"csrf_token": ["caf\N{LATIN SMALL LETTER E WITH ACUTE}"]}
    uploaded = one_uploaded_file(files, "document")
    assert uploaded.filename == "adventure.json"
    assert uploaded.content_type == "application/json"
    assert uploaded.content == b'{"schema_version": 3}'


def test_multipart_parser_rejects_file_above_explicit_limit() -> None:
    with pytest.raises(FormTooLargeError, match="may not exceed 4 bytes"):
        parse_multipart_form(
            _multipart_environment(files=(("document", "adventure.json", b"12345"),)),
            max_num_fields=1,
            max_file_bytes=4,
        )


def test_multipart_parser_rejects_missing_boundary() -> None:
    environ = build_wsgi_environ(
        "/upload",
        method="POST",
        body=b"not-a-multipart-body",
        content_type="multipart/form-data",
    )

    with pytest.raises(InvalidFormError, match="boundary is missing or malformed"):
        parse_multipart_form(environ, max_num_fields=1, max_file_bytes=100)


def test_multipart_parser_rejects_part_count_abuse() -> None:
    with pytest.raises(InvalidFormError, match="too many fields"):
        parse_multipart_form(
            _multipart_environment(fields=(("one", "1"), ("two", "2"))),
            max_num_fields=1,
            max_file_bytes=100,
        )
