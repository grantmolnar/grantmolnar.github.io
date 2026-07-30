"""Opaque adventure identity and stable human-readable entity identifiers."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from uuid import RFC_4122, UUID, uuid4


def new_adventure_identifier() -> str:
    """Return one globally unique opaque identifier for a newly created adventure."""
    return str(uuid4())


def new_reference_identifier() -> str:
    """Return one canonical UUIDv4 identifier for a newly created reference."""
    return str(uuid4())


def is_canonical_uuid4(value: object) -> bool:
    """Return whether a value is canonical lower-case RFC 4122 UUIDv4 text."""
    if not isinstance(value, str):
        return False
    try:
        parsed = UUID(value)
    except ValueError:
        return False
    return parsed.version == 4 and parsed.variant == RFC_4122 and str(parsed) == value


def identifier_slug(title: str) -> str:
    """Normalize a title into the canonical lower-case hyphenated identifier form."""
    normalized = unicodedata.normalize("NFKD", title)
    ascii_title = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_title.lower()).strip("-")
    return slug or "item"


def unique_identifier(
    title: str,
    existing_identifiers: Iterable[str],
    *,
    current_identifier: str | None = None,
) -> str:
    """Return a title-derived identifier, adding a numeric suffix only when necessary."""
    existing = set(existing_identifiers)
    if current_identifier is not None:
        existing.discard(current_identifier)
    base = identifier_slug(title)
    if base not in existing:
        return base
    suffix = 2
    while f"{base}-{suffix}" in existing:
        suffix += 1
    return f"{base}-{suffix}"
