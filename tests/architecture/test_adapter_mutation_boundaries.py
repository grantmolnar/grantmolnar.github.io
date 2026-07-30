"""Static guardrails for canonical mutations at CLI and browser boundaries."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.support.paths import PACKAGE_ROOT, PROJECT_ROOT, iter_python_files
from tests.support.python_ast import parse_module

pytestmark = pytest.mark.architecture

_CANONICAL_WRITERS = {
    "adventure_graph.infrastructure.adventure_store": {"save_adventure"},
    "adventure_graph.infrastructure.atomic_files": {
        "remove_file",
        "write_json_object",
        "write_json_objects",
    },
    "adventure_graph.infrastructure.authoring_store": {"save_authoring_bundle"},
    "adventure_graph.infrastructure.journal_archive_store": {
        "delete_journal_archive",
        "restore_journal_archive",
        "save_archive_and_reset",
    },
    "adventure_graph.infrastructure.play_state_store": {"save_play_state"},
}


def _adapter_paths() -> tuple[Path, ...]:
    cli_paths = tuple(sorted(PACKAGE_ROOT.glob("cli_*_commands.py")))
    web_paths = tuple(iter_python_files(PACKAGE_ROOT / "interfaces" / "web"))
    return (*cli_paths, *web_paths)


def _dotted_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return None if parent is None else f"{parent}.{node.attr}"
    return None


def test_adapters_do_not_access_canonical_persistence_writers() -> None:
    """Keep ordinary adapter writes behind application commands and project ports."""
    violations: list[str] = []
    for path in _adapter_paths():
        module = parse_module(path)
        module_aliases: dict[str, str] = {}

        for encounter in ast.walk(module):
            if isinstance(encounter, ast.ImportFrom) and encounter.module is not None:
                forbidden_names = _CANONICAL_WRITERS.get(encounter.module, set())
                for alias in encounter.names:
                    if alias.name == "*" and forbidden_names:
                        relative_path = path.relative_to(PROJECT_ROOT)
                        violations.append(
                            f"{relative_path}:{encounter.lineno}: star-imports canonical writer "
                            f"module {encounter.module}"
                        )
                        continue
                    if alias.name not in forbidden_names:
                        continue
                    relative_path = path.relative_to(PROJECT_ROOT)
                    violations.append(
                        f"{relative_path}:{encounter.lineno}: imports canonical writer "
                        f"{encounter.module}.{alias.name}"
                    )
            elif isinstance(encounter, ast.Import):
                for alias in encounter.names:
                    if alias.name not in _CANONICAL_WRITERS:
                        continue
                    module_aliases[alias.asname or alias.name] = alias.name

        for encounter in ast.walk(module):
            if not isinstance(encounter, ast.Call):
                continue
            called_name = _dotted_name(encounter.func)
            if called_name is None:
                continue
            for local_name, imported_module in module_aliases.items():
                if called_name == local_name:
                    continue
                prefix = f"{local_name}."
                if not called_name.startswith(prefix):
                    continue
                called_member = called_name[len(prefix) :]
                if called_member not in _CANONICAL_WRITERS[imported_module]:
                    continue
                relative_path = path.relative_to(PROJECT_ROOT)
                violations.append(
                    f"{relative_path}:{encounter.lineno}: calls canonical writer "
                    f"{imported_module}.{called_member}"
                )

    assert violations == []
