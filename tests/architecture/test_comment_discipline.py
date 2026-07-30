"""Static guardrails for comments and local tool suppressions."""

from __future__ import annotations

import ast
import io
import re
import tokenize
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.support.paths import PROJECT_ROOT

pytestmark = pytest.mark.architecture

_PYTHON_ROOTS = (
    PROJECT_ROOT / "src",
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "scripts",
    PROJECT_ROOT / "packaging",
)
_SUPPRESSION_PREFIXES = (
    "# noqa:",
    "# ruff: noqa:",
    "# type: ignore",
    "# pyright:",
    "# nosec",
)
_WORK_ITEM_PATTERN = re.compile(r"\b(?:TODO|FIXME|HACK|XXX)\b", re.IGNORECASE)
_PROGRESS_SESSION_PATTERN = re.compile(r"\b(?:Expansion )?Session \d+\b")


def _python_comments() -> Iterator[tuple[Path, int, str]]:
    for root in _PYTHON_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            source = path.read_text(encoding="utf-8")
            tokens = tokenize.generate_tokens(io.StringIO(source).readline)
            for token in tokens:
                if token.type == tokenize.COMMENT:
                    yield path, token.start[0], token.string.strip()


def _python_docstrings() -> Iterator[tuple[Path, int, str]]:
    for root in _PYTHON_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            module = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(module):
                if not isinstance(
                    node,
                    ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
                ):
                    continue
                docstring = ast.get_docstring(node, clean=True)
                if docstring is not None:
                    yield path, getattr(node, "lineno", 1), docstring


def test_inline_tool_suppressions_explain_the_local_exception() -> None:
    violations: list[str] = []

    for path, line_number, comment in _python_comments():
        if not comment.startswith(_SUPPRESSION_PREFIXES):
            continue
        _, separator, rationale = comment.partition(" -- ")
        if not separator or not rationale.strip():
            relative_path = path.relative_to(PROJECT_ROOT)
            violations.append(f"{relative_path}:{line_number}: {comment}")

    assert violations == []


def test_python_comments_do_not_carry_untracked_work_items() -> None:
    violations: list[str] = []

    for path, line_number, comment in _python_comments():
        if _WORK_ITEM_PATTERN.search(comment):
            relative_path = path.relative_to(PROJECT_ROOT)
            violations.append(f"{relative_path}:{line_number}: {comment}")

    assert violations == []


def test_comments_and_docstrings_do_not_encode_progress_sessions() -> None:
    violations: list[str] = []

    for path, line_number, content in (*_python_comments(), *_python_docstrings()):
        if _PROGRESS_SESSION_PATTERN.search(content):
            relative_path = path.relative_to(PROJECT_ROOT)
            violations.append(f"{relative_path}:{line_number}: {content}")

    assert violations == []
