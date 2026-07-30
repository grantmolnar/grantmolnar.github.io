"""Low-level, bounded parsing primitives for local web forms."""

from __future__ import annotations

from dataclasses import dataclass
from email import policy
from email.parser import BytesParser
from string import hexdigits
from typing import BinaryIO, cast
from urllib.parse import parse_qs
from wsgiref.types import WSGIEnvironment

from adventure_graph.domain.adventure import (
    AdventureTags,
    CombatIntensity,
)

_MAX_FORM_BYTES = 2_000_000
_FORM_CONTENT_TYPE = "application/x-www-form-urlencoded"
_MULTIPART_CONTENT_TYPE = "multipart/form-data"
_MAX_MULTIPART_OVERHEAD_BYTES = 262_144
_MAX_MULTIPART_TEXT_BYTES = 65_536


class InvalidFormError(ValueError):
    """Raised when an authoring request cannot be parsed safely."""


class CsrfValidationError(ValueError):
    """Raised when a modifying request lacks the application form token."""


class FormTooLargeError(ValueError):
    """Raised when a submitted authoring form exceeds the bounded request size."""


@dataclass(frozen=True, slots=True)
class UploadedFile:
    """One bounded file part submitted by a local browser form."""

    filename: str
    content_type: str
    content: bytes


def parse_form_fields(
    environ: WSGIEnvironment,
    *,
    max_num_fields: int,
) -> dict[str, list[str]]:
    """Read and strictly parse one bounded URL-encoded request body."""
    content_type = str(environ.get("CONTENT_TYPE", "")).split(";", maxsplit=1)[0].strip().lower()
    if content_type != _FORM_CONTENT_TYPE:
        raise InvalidFormError("Expected an application/x-www-form-urlencoded form submission.")
    raw_length = str(environ.get("CONTENT_LENGTH", "")).strip()
    if not raw_length or any(character not in "0123456789" for character in raw_length):
        raise InvalidFormError("The form content length is invalid.")
    content_length = int(raw_length)
    if content_length > _MAX_FORM_BYTES:
        raise FormTooLargeError("Local web forms may not exceed 2,000,000 bytes.")
    input_value = environ.get("wsgi.input")
    if input_value is None or not callable(getattr(input_value, "read", None)):
        raise InvalidFormError("The submitted form body is unavailable.")
    input_stream = cast(BinaryIO, input_value)
    raw_body = input_stream.read(content_length)
    if len(raw_body) != content_length:
        raise InvalidFormError("The submitted form ended before its declared content length.")
    try:
        body = raw_body.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidFormError("The submitted form body is not valid UTF-8.") from error
    try:
        _require_valid_percent_encoding(body)
    except ValueError as error:
        raise InvalidFormError("The submitted form has a malformed percent escape.") from error
    try:
        return parse_qs(
            body,
            keep_blank_values=True,
            strict_parsing=True,
            max_num_fields=max_num_fields,
            encoding="utf-8",
            errors="strict",
        )
    except UnicodeDecodeError as error:
        raise InvalidFormError(
            "The submitted form contains invalid percent-encoded UTF-8."
        ) from error
    except ValueError as error:
        raise InvalidFormError("The submitted URL-encoded form is malformed.") from error


def parse_multipart_form(
    environ: WSGIEnvironment,
    *,
    max_num_fields: int,
    max_file_bytes: int,
) -> tuple[dict[str, list[str]], dict[str, list[UploadedFile]]]:
    """Read one bounded browser-generated multipart form with explicit file limits."""
    content_type = str(environ.get("CONTENT_TYPE", "")).strip()
    media_type = content_type.split(";", maxsplit=1)[0].strip().lower()
    if media_type != _MULTIPART_CONTENT_TYPE:
        raise InvalidFormError("Expected a multipart/form-data submission.")
    if any(ord(character) < 32 or ord(character) == 127 for character in content_type):
        raise InvalidFormError("The multipart content type is invalid.")
    try:
        encoded_content_type = content_type.encode("ascii")
    except UnicodeEncodeError as error:
        raise InvalidFormError("The multipart content type must use ASCII.") from error

    body = _read_request_body(
        environ,
        maximum_bytes=max_file_bytes + _MAX_MULTIPART_OVERHEAD_BYTES,
        oversized_message="Uploaded forms exceed the supported size limit.",
    )
    message = BytesParser(policy=policy.default).parsebytes(
        b"Content-Type: " + encoded_content_type + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
    )
    if not message.is_multipart():
        raise InvalidFormError("The multipart form boundary is missing or malformed.")

    fields: dict[str, list[str]] = {}
    files: dict[str, list[UploadedFile]] = {}
    part_count = 0
    for part in message.iter_parts():
        part_count += 1
        if part_count > max_num_fields:
            raise InvalidFormError("The submitted form contains too many fields.")
        if part.is_multipart() or part.get_content_disposition() != "form-data":
            raise InvalidFormError("The submitted multipart form contains an unsupported part.")
        name = part.get_param("name", header="content-disposition")
        if not isinstance(name, str) or not name:
            raise InvalidFormError("A multipart form field is missing its name.")
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            raise InvalidFormError("A multipart form field could not be decoded.")
        filename = part.get_filename()
        if filename is None:
            if len(payload) > _MAX_MULTIPART_TEXT_BYTES:
                raise FormTooLargeError("A multipart text field exceeds 65,536 bytes.")
            try:
                value = payload.decode("utf-8")
            except UnicodeDecodeError as error:
                raise InvalidFormError("A multipart text field is not valid UTF-8.") from error
            fields.setdefault(name, []).append(value)
            continue
        if not filename or any(
            ord(character) < 32 or ord(character) == 127 for character in filename
        ):
            raise InvalidFormError("The uploaded filename is invalid.")
        if len(payload) > max_file_bytes:
            raise FormTooLargeError(f"Uploaded files may not exceed {max_file_bytes:,} bytes.")
        files.setdefault(name, []).append(
            UploadedFile(
                filename=filename,
                content_type=part.get_content_type(),
                content=payload,
            )
        )
    return fields, files


def one_uploaded_file(
    files: dict[str, list[UploadedFile]],
    name: str,
) -> UploadedFile:
    """Return exactly one nonempty uploaded file for a required field."""
    values = files.get(name)
    if values is None:
        raise InvalidFormError(f"Required file field {name!r} is missing.")
    if len(values) != 1:
        raise InvalidFormError(f"File field {name!r} was submitted more than once.")
    uploaded = values[0]
    if not uploaded.content:
        raise InvalidFormError("Choose a nonempty JSON file to import.")
    return uploaded


def require_allowed_upload_fields(
    fields: dict[str, list[str]],
    files: dict[str, list[UploadedFile]],
    *,
    allowed_fields: set[str],
    allowed_files: set[str],
) -> None:
    """Reject text and file parts outside an explicit multipart form contract."""
    unknown_fields = set(fields) - allowed_fields
    if unknown_fields:
        raise InvalidFormError(f"Unexpected form field: {sorted(unknown_fields)[0]}.")
    unknown_files = set(files) - allowed_files
    if unknown_files:
        raise InvalidFormError(f"Unexpected file field: {sorted(unknown_files)[0]}.")


def _read_request_body(
    environ: WSGIEnvironment,
    *,
    maximum_bytes: int,
    oversized_message: str,
) -> bytes:
    raw_length = str(environ.get("CONTENT_LENGTH", "")).strip()
    if not raw_length or any(character not in "0123456789" for character in raw_length):
        raise InvalidFormError("The form content length is invalid.")
    content_length = int(raw_length)
    if content_length > maximum_bytes:
        raise FormTooLargeError(oversized_message)
    input_value = environ.get("wsgi.input")
    if input_value is None or not callable(getattr(input_value, "read", None)):
        raise InvalidFormError("The submitted form body is unavailable.")
    input_stream = cast(BinaryIO, input_value)
    raw_body = input_stream.read(content_length)
    if len(raw_body) != content_length:
        raise InvalidFormError("The submitted form ended before its declared content length.")
    return raw_body


def _require_valid_percent_encoding(body: str) -> None:
    """Reject incomplete or non-hexadecimal URL percent escapes."""
    index = 0
    while True:
        index = body.find("%", index)
        if index < 0:
            return
        if index + 2 >= len(body) or any(
            character not in hexdigits for character in body[index + 1 : index + 3]
        ):
            raise ValueError("Malformed percent escape in submitted form data.")
        index += 3


def require_allowed_fields(fields: dict[str, list[str]], allowed: set[str]) -> None:
    """Reject fields outside an explicit form contract."""
    unknown = set(fields) - allowed
    if unknown:
        raise InvalidFormError(f"Unexpected form field: {sorted(unknown)[0]}.")


def one_form_value(fields: dict[str, list[str]], name: str) -> str:
    """Return exactly one submitted value for a required field."""
    values = fields.get(name)
    if values is None:
        raise InvalidFormError(f"Required form field {name!r} is missing.")
    if len(values) != 1:
        raise InvalidFormError(f"Form field {name!r} was submitted more than once.")
    return values[0]


def many_form_values(fields: dict[str, list[str]], name: str) -> tuple[str, ...]:
    """Return zero or more nonempty submitted values in their original order."""
    values = fields.get(name, [])
    if any(not value for value in values):
        raise InvalidFormError(f"Form field {name!r} contains an empty value.")
    return tuple(values)


def checkbox_value(fields: dict[str, list[str]], name: str) -> bool:
    """Parse the adapter's single canonical checkbox representation."""
    values = fields.get(name, [])
    if len(values) > 1 or any(value != "1" for value in values):
        raise InvalidFormError(f"Checkbox field {name!r} is invalid.")
    return bool(values)


def require_revision_value(value: str) -> None:
    """Require the opaque revision token carried by every modifying form."""
    if not value:
        raise InvalidFormError("The expected project revision is missing.")


def required_positive_int(value: str, name: str) -> int:
    """Parse a required positive integer field."""
    parsed = optional_positive_int(value, name)
    if parsed is None:
        raise InvalidFormError(f"Form field {name!r} is required.")
    return parsed


def optional_positive_int(value: str, name: str) -> int | None:
    """Parse an optional positive integer field."""
    if not value:
        return None
    try:
        parsed = int(value)
    except ValueError as error:
        raise InvalidFormError(f"Form field {name!r} must be a positive integer.") from error
    if parsed <= 0:
        raise InvalidFormError(f"Form field {name!r} must be a positive integer.")
    return parsed


def parse_tags(value: str) -> tuple[str, ...]:
    """Normalize and case-insensitively deduplicate comma-separated tags."""
    tags: list[str] = []
    seen: set[str] = set()
    for item in value.split(","):
        tag = item.strip()
        folded = tag.casefold()
        if tag and folded not in seen:
            tags.append(tag)
            seen.add(folded)
    return tuple(tags)


def adventure_tags_from_values(values: dict[str, str]) -> AdventureTags:
    """Build validated structured adventure tags from form values."""
    combat_value = values["combat_intensity"].strip() or None
    if combat_value not in {None, "none", "light", "moderate", "heavy"}:
        raise InvalidFormError("Combat intensity must be none, light, moderate, or heavy.")
    combat = cast(CombatIntensity | None, combat_value)
    try:
        return AdventureTags(
            genres=parse_tags(values["genres"]),
            game_systems=parse_tags(values["game_systems"]),
            settings=parse_tags(values["settings"]),
            party_size_min=optional_positive_int(values["party_size_min"], "party_size_min"),
            party_size_max=optional_positive_int(values["party_size_max"], "party_size_max"),
            level_min=optional_positive_int(values["level_min"], "level_min"),
            level_max=optional_positive_int(values["level_max"], "level_max"),
            combat_intensity=combat,
            keywords=parse_tags(values["keywords"]),
        )
    except ValueError as error:
        raise InvalidFormError(str(error)) from error
