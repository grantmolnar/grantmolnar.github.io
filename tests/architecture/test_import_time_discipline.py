"""Static guardrails that keep package imports free of runtime behavior."""

from __future__ import annotations

import ast

import pytest

from tests.support.paths import PACKAGE_ROOT, PROJECT_ROOT, iter_python_files
from tests.support.python_ast import parse_module

pytestmark = pytest.mark.architecture

_ALLOWED_TOP_LEVEL_CALLS = {
    "cast",
    "dataclass",
    "field",
    "final",
    "overload",
    "TypeVar",
}


def _is_docstring(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def _is_type_checking_guard(statement: ast.stmt) -> bool:
    if not isinstance(statement, ast.If):
        return False
    test = statement.test
    return isinstance(test, ast.Name) and test.id == "TYPE_CHECKING"


def _is_main_guard(statement: ast.stmt) -> bool:
    if not isinstance(statement, ast.If):
        return False
    test = statement.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "__name__"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Eq)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value == "__main__"
    )


def _call_name(encounter: ast.AST) -> str | None:
    if isinstance(encounter, ast.Name):
        return encounter.id
    if isinstance(encounter, ast.Attribute):
        return encounter.attr
    return None


def _is_type_expression(encounter: ast.AST) -> bool:
    if isinstance(encounter, ast.Name | ast.Attribute):
        return True
    if isinstance(encounter, ast.Subscript):
        return _is_type_expression(encounter.value) and _is_type_expression(encounter.slice)
    if isinstance(encounter, ast.BinOp) and isinstance(encounter.op, ast.BitOr):
        return _is_type_expression(encounter.left) and _is_type_expression(encounter.right)
    if isinstance(encounter, ast.Tuple):
        return all(_is_type_expression(element) for element in encounter.elts)
    if isinstance(encounter, ast.Constant):
        return encounter.value is None or isinstance(encounter.value, str)
    return False


def _is_simple_constant_assignment(statement: ast.stmt) -> bool:
    if not isinstance(statement, ast.Assign | ast.AnnAssign):
        return False
    value = statement.value
    is_type_alias = (
        isinstance(statement, ast.AnnAssign)
        and isinstance(statement.annotation, ast.Name)
        and statement.annotation.id == "TypeAlias"
        and value is not None
        and _is_type_expression(value)
    )
    is_literal_collection = isinstance(value, ast.Tuple | ast.List | ast.Set) and all(
        isinstance(element, ast.Constant) for element in value.elts
    )
    is_allowed_call = isinstance(value, ast.Call) and (
        _call_name(value.func) in _ALLOWED_TOP_LEVEL_CALLS
    )
    return (
        is_type_alias
        or value is None
        or isinstance(value, ast.Constant)
        or is_literal_collection
        or is_allowed_call
    )


def _is_allowed_top_level_statement(statement: ast.stmt) -> bool:
    return (
        isinstance(
            statement,
            ast.Import | ast.ImportFrom | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        )
        or _is_docstring(statement)
        or _is_type_checking_guard(statement)
        or _is_main_guard(statement)
        or _is_simple_constant_assignment(statement)
    )


def test_package_modules_do_not_execute_runtime_work_at_import_time() -> None:
    violations: list[str] = []

    for path in iter_python_files(PACKAGE_ROOT):
        module = parse_module(path)
        for statement in module.body:
            if _is_allowed_top_level_statement(statement):
                continue
            relative_path = path.relative_to(PROJECT_ROOT)
            violations.append(
                f"{relative_path}:{statement.lineno}: top-level {type(statement).__name__}"
            )

    assert violations == []
