"""Shared Python-AST helpers for static architecture tests."""

from __future__ import annotations

import ast
from pathlib import Path


def parse_module(path: Path) -> ast.Module:
    """Parse one UTF-8 Python module with useful filename context."""
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def dotted_name(encounter: ast.AST) -> str | None:
    """Return a dotted identifier for simple name and attribute expressions."""
    if isinstance(encounter, ast.Name):
        return encounter.id
    if isinstance(encounter, ast.Attribute):
        parent = dotted_name(encounter.value)
        return f"{parent}.{encounter.attr}" if parent else encounter.attr
    return None
