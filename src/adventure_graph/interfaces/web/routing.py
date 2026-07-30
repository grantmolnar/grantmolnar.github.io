"""Path and identifier helpers for the local web adapter."""

from __future__ import annotations

import re
from string import hexdigits
from urllib.parse import parse_qs, quote, unquote, urlencode, urlsplit

_ENTITY_COLLECTIONS = ("encounters", "revelations", "clues", "references")
_ARCHIVE_ACTIONS = ("restore", "delete")
_ENTITY_IDENTIFIER_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"
_PLAY_AUTHORING_ACTIONS = {"encounter-authored", "clue-authored", "reference-authored"}


def entity_route(path: str) -> tuple[str, str] | None:
    """Return the entity kind and decoded identifier represented by a detail path."""
    segments = path.strip("/").split("/")
    if len(segments) != 2 or segments[1] == "new":
        return None
    identifier = _decoded_identifier(segments[1])
    if identifier is None:
        return None
    try:
        collection_index = _ENTITY_COLLECTIONS.index(segments[0])
    except ValueError:
        return None
    return ("encounter", "revelation", "clue", "reference")[collection_index], identifier


def entity_edit_route(path: str) -> tuple[str, str] | None:
    """Return the entity kind and identifier represented by an edit path."""
    segments = path.strip("/").split("/")
    if len(segments) != 3 or segments[2] != "edit":
        return None
    identifier = _decoded_identifier(segments[1])
    if identifier is None:
        return None
    try:
        collection_index = _ENTITY_COLLECTIONS.index(segments[0])
    except ValueError:
        return None
    return ("encounter", "revelation", "clue", "reference")[collection_index], identifier


def entity_remove_route(path: str) -> tuple[str, str] | None:
    """Return one entity kind and identifier represented by a removal path."""
    segments = path.strip("/").split("/")
    if len(segments) != 3 or segments[2] != "remove":
        return None
    identifier = _decoded_identifier(segments[1])
    if identifier is None:
        return None
    try:
        collection_index = _ENTITY_COLLECTIONS.index(segments[0])
    except ValueError:
        return None
    return ("encounter", "revelation", "clue", "reference")[collection_index], identifier


def encounter_reference_action_route(path: str) -> tuple[str, str] | None:
    """Return encounter identity and link action for a contextual reference route."""
    segments = path.strip("/").split("/")
    if (
        len(segments) != 4
        or segments[0] != "encounters"
        or segments[2] != "references"
        or segments[3] not in {"link", "unlink"}
    ):
        return None
    identifier = _decoded_identifier(segments[1])
    return None if identifier is None else (identifier, segments[3])


def encounter_edit_route(path: str) -> str | None:
    """Return the decoded encounter identifier represented by an edit path."""
    route = entity_edit_route(path)
    return route[1] if route is not None and route[0] == "encounter" else None


def archive_detail_route(path: str) -> str | None:
    """Return the decoded archive identifier represented by a detail path."""
    segments = path.strip("/").split("/")
    if len(segments) != 2 or segments[0] != "archives":
        return None
    return _decoded_identifier(segments[1])


def archive_action_route(path: str) -> tuple[str, str] | None:
    """Return the decoded archive identifier and supported action represented by a path."""
    segments = path.strip("/").split("/")
    if len(segments) != 3 or segments[0] != "archives" or segments[2] not in _ARCHIVE_ACTIONS:
        return None
    identifier = _decoded_identifier(segments[1])
    return None if identifier is None else (identifier, segments[2])


def archive_download_route(path: str) -> str | None:
    """Return the decoded archive identifier represented by a download path."""
    segments = path.strip("/").split("/")
    if len(segments) != 3 or segments[0] != "archives" or segments[2] != "download":
        return None
    return _decoded_identifier(segments[1])


def normalize_play_return_target(value: str) -> str | None:
    """Return one canonical Play-table target or reject an untrusted return value."""
    if not value or len(value) > 2_048 or not _has_valid_percent_encoding(value):
        return None
    if "\\" in value or any(ord(character) < 32 or ord(character) == 127 for character in value):
        return None
    target = urlsplit(value)
    if target.scheme or target.netloc or target.fragment or target.path != "/play":
        return None
    if not target.query:
        return "/play"
    try:
        parameters = parse_qs(
            target.query,
            keep_blank_values=True,
            strict_parsing=True,
            max_num_fields=1,
            encoding="utf-8",
            errors="strict",
        )
    except (UnicodeDecodeError, ValueError):
        return None
    if set(parameters) != {"encounter"}:
        return None
    encounters = parameters["encounter"]
    if len(encounters) != 1 or re.fullmatch(_ENTITY_IDENTIFIER_PATTERN, encounters[0]) is None:
        return None
    return f"/play?{urlencode({'encounter': encounters[0]})}"


def play_authoring_return_location(
    return_to: str,
    *,
    action: str,
    focus_encounter_id: str | None = None,
) -> str:
    """Add a bounded authoring notice and optional focus to one Play return target."""
    normalized = normalize_play_return_target(return_to)
    if normalized is None:
        raise ValueError("The authoring return target is invalid.")
    if action not in _PLAY_AUTHORING_ACTIONS:
        raise ValueError("The authoring return action is invalid.")
    parameters = parse_qs(urlsplit(normalized).query, keep_blank_values=True)
    if focus_encounter_id is not None:
        if re.fullmatch(_ENTITY_IDENTIFIER_PATTERN, focus_encounter_id) is None:
            raise ValueError("The focused encounter identifier is invalid.")
        parameters["encounter"] = [focus_encounter_id]
    parameters["action"] = [action]
    flattened_parameters = {name: values[-1] for name, values in parameters.items()}
    return f"/play?{urlencode(flattened_parameters)}"


def quote_identifier(identifier: str) -> str:
    """Encode one identifier for use as a complete URL path segment."""
    return quote(identifier, safe="")


def _decoded_identifier(segment: str) -> str | None:
    """Decode one identifier while rejecting separator and dot-segment ambiguity."""
    if not segment or not _has_valid_percent_encoding(segment):
        return None
    try:
        decoded = unquote(segment, errors="strict")
    except UnicodeDecodeError:
        return None
    if decoded in {"", ".", ".."}:
        return None
    if "/" in decoded or "\\" in decoded:
        return None
    if any(ord(character) < 32 or ord(character) == 127 for character in decoded):
        return None
    return decoded


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
