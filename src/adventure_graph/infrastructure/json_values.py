"""Strict helpers for reading versioned JSON documents."""

from __future__ import annotations

import json
import re
from collections.abc import Collection
from datetime import date, datetime
from pathlib import Path
from typing import Any, TypeAlias, cast

from adventure_graph.application.document_limits import (
    MAX_CANONICAL_JSON_BYTES as MAX_JSON_DOCUMENT_BYTES,
)
from adventure_graph.infrastructure.file_transactions import recover_pending_transactions

JsonObject: TypeAlias = dict[str, Any]

MAX_JSON_NESTING_DEPTH = 64


class UnsupportedFieldError(ValueError):
    """Raised when a current-schema document contains an unknown persisted field."""


def encode_object_bytes(data: JsonObject) -> bytes:
    """Encode one bounded canonical JSON object for persistence and downloads."""
    content = f"{json.dumps(data, indent=2, ensure_ascii=False)}\n".encode()
    if len(content) > MAX_JSON_DOCUMENT_BYTES:
        raise ValueError(
            f"Canonical JSON documents may not exceed {MAX_JSON_DOCUMENT_BYTES:,} UTF-8 bytes."
        )
    return content


def encode_object_text(data: JsonObject) -> str:
    """Encode one bounded canonical JSON object as UTF-8 text."""
    return encode_object_bytes(data).decode("utf-8")


def reject_unknown_fields(
    data: JsonObject,
    allowed_fields: Collection[str],
    context: str,
) -> None:
    """Reject fields that the current runtime cannot preserve canonically."""
    unknown_fields = sorted(field for field in data if field not in allowed_fields)
    if not unknown_fields:
        return
    field_word = "field" if len(unknown_fields) == 1 else "fields"
    rendered_fields = ", ".join(repr(field) for field in unknown_fields)
    raise UnsupportedFieldError(
        f"Unsupported {field_word} in {context}: {rendered_fields}. "
        "This file may have been written by a newer Adventure Graph release."
    )


def read_object(path: Path) -> JsonObject:
    """Read one JSON object after recovering any interrupted sibling transaction."""
    return decode_object_bytes(read_json_document_bytes(path), path)


def read_json_document_bytes(path: Path, *, recover: bool = True) -> bytes:
    """Read one bounded canonical JSON payload without unbounded allocation."""
    if recover:
        recover_pending_transactions((path,))
    with path.open("rb") as stream:
        content = stream.read(MAX_JSON_DOCUMENT_BYTES + 1)
    if len(content) > MAX_JSON_DOCUMENT_BYTES:
        raise ValueError(
            f"JSON document in {path} exceeds the {MAX_JSON_DOCUMENT_BYTES}-byte limit."
        )
    return content


def decode_object_bytes(content: bytes, source: str | Path) -> JsonObject:
    """Decode one bounded UTF-8 JSON object while preserving source context."""
    if len(content) > MAX_JSON_DOCUMENT_BYTES:
        raise ValueError(
            f"JSON document in {source} exceeds the {MAX_JSON_DOCUMENT_BYTES}-byte limit."
        )
    _reject_excessive_nesting(content, source)
    try:
        data: object = json.loads(content.decode("utf-8"))
    except UnicodeDecodeError as error:
        raise ValueError(f"Expected UTF-8 JSON in {source}.") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in {source}: {error.msg}.") from error
    except RecursionError as error:
        raise ValueError(
            f"JSON document in {source} exceeds the supported nesting depth."
        ) from error
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {source}.")
    return cast(JsonObject, data)


def _reject_excessive_nesting(content: bytes, source: str | Path) -> None:
    depth = 0
    in_string = False
    escaped = False
    for value in content:
        if in_string:
            if escaped:
                escaped = False
            elif value == 0x5C:
                escaped = True
            elif value == 0x22:
                in_string = False
            continue
        if value == 0x22:
            in_string = True
        elif value in (0x5B, 0x7B):
            depth += 1
            if depth > MAX_JSON_NESTING_DEPTH:
                raise ValueError(
                    f"JSON document in {source} exceeds the "
                    f"{MAX_JSON_NESTING_DEPTH}-level nesting limit."
                )
        elif value in (0x5D, 0x7D):
            depth -= 1


def object_value(data: JsonObject, key: str) -> JsonObject:
    """Return a required object member."""
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object.")
    return cast(JsonObject, value)


def object_list(data: JsonObject, key: str) -> list[JsonObject]:
    """Return a required list of object members."""
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list of objects.")
    items = cast(list[object], value)
    if not all(isinstance(item, dict) for item in items):
        raise ValueError(f"{key} must be a list of objects.")
    return cast(list[JsonObject], items)


def string_value(data: JsonObject, key: str, default: str | None = None) -> str:
    """Return a string member, optionally with a default."""
    value = data.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string.")
    return value


def nonempty_string_value(data: JsonObject, key: str) -> str:
    """Return a required string containing at least one character."""
    value = string_value(data, key)
    if not value:
        raise ValueError(f"{key} must be a nonempty string.")
    return value


def nullable_string(data: JsonObject, key: str) -> str | None:
    """Return a string or null member."""
    value = data.get(key)
    if value is not None and not isinstance(value, str):
        raise ValueError(f"{key} must be a string or null.")
    return value


def nullable_nonempty_string(data: JsonObject, key: str) -> str | None:
    """Return null or a string containing at least one character."""
    value = nullable_string(data, key)
    if value == "":
        raise ValueError(f"{key} must be a nonempty string or null.")
    return value


def nullable_iso_date(data: JsonObject, key: str) -> str | None:
    """Return null or one strict ISO 8601 calendar date."""
    value = nullable_nonempty_string(data, key)
    if value is None:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{key} must be a valid YYYY-MM-DD date or null.") from error
    if parsed.isoformat() != value:
        raise ValueError(f"{key} must be a valid YYYY-MM-DD date or null.")
    return value


def rfc3339_datetime_value(data: JsonObject, key: str) -> str:
    """Return one timezone-aware RFC 3339 date-time string."""
    value = nonempty_string_value(data, key)
    if (
        re.fullmatch(
            r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})",
            value,
        )
        is None
    ):
        raise ValueError(f"{key} must be a valid RFC 3339 date-time.")
    normalized = value[:-1] + "+00:00" if value[-1] in "Zz" else value
    normalized = normalized.replace("t", "T", 1)
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"{key} must be a valid RFC 3339 date-time.") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{key} must be a valid RFC 3339 date-time.")
    return value


def integer_value(data: JsonObject, key: str, default: int | None = None) -> int:
    """Return a non-negative integer member."""
    value = data.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{key} must be a non-negative integer.")
    return value


def integer_at_least(data: JsonObject, key: str, minimum: int) -> int:
    """Return an integer member no smaller than the requested minimum."""
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise ValueError(f"{key} must be an integer of at least {minimum}.")
    return value


def positive_integer(data: JsonObject, key: str) -> int:
    """Return a positive integer member."""
    return integer_at_least(data, key, 1)


def boolean_value(data: JsonObject, key: str, default: bool | None = None) -> bool:
    """Return a boolean member, optionally with a default."""
    value = data.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean.")
    return value


def string_list(
    data: JsonObject,
    key: str,
    default: list[str] | None = None,
) -> list[str]:
    """Return a list of strings, optionally with a default."""
    value = data.get(key, default)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list of strings.")
    items = cast(list[object], value)
    if not all(isinstance(item, str) for item in items):
        raise ValueError(f"{key} must be a list of strings.")
    return cast(list[str], items)


def unique_nonempty_string_list(
    data: JsonObject,
    key: str,
    default: list[str] | None = None,
) -> list[str]:
    """Return unique strings whose persisted values are each nonempty."""
    values = string_list(data, key, default)
    if any(not value for value in values):
        raise ValueError(f"{key} must contain only nonempty strings.")
    if len(set(values)) != len(values):
        raise ValueError(f"{key} must contain unique strings.")
    return values
