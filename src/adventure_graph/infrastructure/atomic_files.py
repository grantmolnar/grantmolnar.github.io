"""Atomic local-file writes for JSON and generated documents."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from adventure_graph.infrastructure.file_transactions import (
    coordinated_replace,
    ensure_directory,
    remove_empty_directory,
    remove_one,
    replace_one,
)
from adventure_graph.infrastructure.json_values import JsonObject, encode_object_bytes


def write_json_object(path: Path, data: JsonObject) -> None:
    """Write one JSON document through an atomic same-directory replacement."""
    replace_one(path, _encoded_json(data))


def write_json_objects(payloads: Mapping[Path, JsonObject]) -> None:
    """Commit one or several JSON documents through the durable replacement path."""
    if not payloads:
        return
    encoded = {path: _encoded_json(data) for path, data in payloads.items()}
    if len(encoded) == 1:
        path, content = next(iter(encoded.items()))
        replace_one(path, content)
        return
    coordinated_replace(encoded)


def remove_file(path: Path) -> None:
    """Remove one existing file durably where the platform supports directory sync."""
    remove_one(path)


def create_directory(path: Path) -> None:
    """Create one durable directory tree for canonical project structure."""
    ensure_directory(path)


def remove_directory(path: Path) -> None:
    """Remove one empty canonical project directory durably where supported."""
    remove_empty_directory(path)


def write_documents(root: Path, documents: Mapping[str, str]) -> None:
    """Write a generated document bundle below one root directory."""
    for relative_name, content in documents.items():
        destination = root / relative_name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def _encoded_json(data: JsonObject) -> bytes:
    return encode_object_bytes(data)
