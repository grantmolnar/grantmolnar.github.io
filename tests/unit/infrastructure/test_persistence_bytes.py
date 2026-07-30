"""Tests for byte-level persistence contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from adventure_graph.infrastructure.atomic_files import write_json_object, write_json_objects
from adventure_graph.infrastructure.json_values import (
    MAX_JSON_DOCUMENT_BYTES,
    MAX_JSON_NESTING_DEPTH,
    decode_object_bytes,
    read_object,
)
from adventure_graph.infrastructure.revision_bytes import framed_sha256_hexdigest


def test_framed_sha256_hexdigest_preserves_established_digest_vector() -> None:
    sources = (
        ("/workspace/adventure.json", b'{"a":1}'),
        ("/workspace/play-state.json", b"<missing-play-state>"),
    )

    assert framed_sha256_hexdigest(sources) == (
        "608fc0abdc3eff17edb915e5aa7ebd67ede8c7723cb8f907ea13f2da114c6679"
    )


def test_framed_sha256_hexdigest_respects_caller_order() -> None:
    sources = (("a", b""), ("bb", b"ccc"))

    assert framed_sha256_hexdigest(sources) == (
        "4d73b51763069c7f5e1648fd024af904f789e199be4f6a3a068d58abe4ea9c83"
    )
    assert framed_sha256_hexdigest(reversed(sources)) != framed_sha256_hexdigest(sources)


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b"\xff", "Expected UTF-8 JSON in example.json."),
        (b'{"broken":', "Invalid JSON in example.json:"),
        (b"[]", "Expected a JSON object in example.json."),
    ],
)
def test_decode_object_bytes_retains_source_context(content: bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        decode_object_bytes(content, "example.json")


def test_read_object_uses_the_same_source_aware_decoder(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_bytes(b'{"broken":')

    with pytest.raises(ValueError, match=f"Invalid JSON in {path}:"):
        read_object(path)


def test_decode_object_bytes_rejects_documents_above_the_size_limit() -> None:
    content = b'{"text":"' + (b"a" * MAX_JSON_DOCUMENT_BYTES) + b'"}'

    with pytest.raises(ValueError, match=r"exceeds the .*byte limit"):
        decode_object_bytes(content, "oversized.json")


def test_read_object_stops_after_the_json_size_limit(tmp_path: Path) -> None:
    path = tmp_path / "oversized.json"
    path.write_bytes(b" " * (MAX_JSON_DOCUMENT_BYTES + 1))

    with pytest.raises(ValueError, match=r"exceeds the .*byte limit"):
        read_object(path)


def test_writers_refuse_to_create_documents_the_reader_cannot_reopen(tmp_path: Path) -> None:
    destination = tmp_path / "oversized.json"

    with pytest.raises(ValueError, match=r"8,388,608 UTF-8 bytes"):
        write_json_object(destination, {"text": "x" * MAX_JSON_DOCUMENT_BYTES})

    assert not destination.exists()


def test_coordinated_writes_validate_every_encoded_document_before_mutation(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text('{"before": 1}\n', encoding="utf-8")
    second.write_text('{"before": 2}\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"8,388,608 UTF-8 bytes"):
        write_json_objects(
            {
                first: {"after": 1},
                second: {"text": "x" * MAX_JSON_DOCUMENT_BYTES},
            }
        )

    assert first.read_text(encoding="utf-8") == '{"before": 1}\n'
    assert second.read_text(encoding="utf-8") == '{"before": 2}\n'


def test_decode_object_bytes_rejects_excessive_nesting_but_ignores_string_brackets() -> None:
    nested = (
        b'{"value":'
        + (b"[" * MAX_JSON_NESTING_DEPTH)
        + b"0"
        + (b"]" * MAX_JSON_NESTING_DEPTH)
        + b"}"
    )

    with pytest.raises(ValueError, match="nesting limit"):
        decode_object_bytes(nested, "deep.json")

    assert decode_object_bytes(b'{"value":"[[[{{{\\""}', "strings.json") == {"value": '[[[{{{"'}
