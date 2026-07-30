"""Static tests that keep the test suite explicit and maintainable."""

from __future__ import annotations

import ast
import tomllib

import pytest

from tests.support.paths import PROJECT_ROOT, iter_python_files
from tests.support.python_ast import dotted_name, parse_module

pytestmark = pytest.mark.architecture

TEST_ROOT = PROJECT_ROOT / "tests"


def _decorator_name(decorator: ast.expr) -> str | None:
    if isinstance(decorator, ast.Call):
        return dotted_name(decorator.func)
    return dotted_name(decorator)


def _call_has_reason(call: ast.Call) -> bool:
    return any(
        keyword.arg == "reason"
        and isinstance(keyword.value, ast.Constant)
        and isinstance(keyword.value.value, str)
        and keyword.value.value.strip()
        for keyword in call.keywords
    )


def test_skip_and_xfail_markers_explain_their_reason() -> None:
    violations: list[str] = []

    for path in iter_python_files(TEST_ROOT):
        module = parse_module(path)
        for encounter in ast.walk(module):
            if not isinstance(encounter, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                continue
            for decorator in encounter.decorator_list:
                name = _decorator_name(decorator)
                if name not in {"pytest.mark.skip", "pytest.mark.xfail"}:
                    continue
                if isinstance(decorator, ast.Call) and _call_has_reason(decorator):
                    continue
                relative_path = path.relative_to(PROJECT_ROOT)
                violations.append(f"{relative_path}:{encounter.lineno}: {name} lacks reason=...")

    assert violations == []


def test_tests_do_not_use_focused_or_manual_debugging_markers() -> None:
    forbidden_markers = {"pytest.mark.only", "pytest.mark.focus", "pytest.mark.wip"}
    violations: list[str] = []

    for path in iter_python_files(TEST_ROOT):
        module = parse_module(path)
        for encounter in ast.walk(module):
            if not isinstance(encounter, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                continue
            for decorator in encounter.decorator_list:
                name = _decorator_name(decorator)
                if name in forbidden_markers:
                    relative_path = path.relative_to(PROJECT_ROOT)
                    violations.append(f"{relative_path}:{encounter.lineno}: {name}")

    assert violations == []


MAX_TEST_MODULE_LINES = 900
WSGI_HARNESS = TEST_ROOT / "support" / "web.py"


def test_test_modules_stay_small_enough_to_review_as_one_unit() -> None:
    """Keep test modules below the point where unrelated behaviors hide together."""
    violations: list[str] = []
    for path in iter_python_files(TEST_ROOT):
        if not path.name.startswith("test_"):
            continue
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_TEST_MODULE_LINES:
            violations.append(f"{path.relative_to(PROJECT_ROOT)}: {line_count} lines")

    assert violations == []


def test_wsgi_request_plumbing_is_centralized_in_the_test_harness() -> None:
    """Prevent interface tests from growing bespoke copies of the WSGI transport setup."""
    violations: list[str] = []

    for path in iter_python_files(TEST_ROOT):
        if path == WSGI_HARNESS:
            continue
        module = parse_module(path)
        for encounter in ast.walk(module):
            if isinstance(encounter, ast.ImportFrom) and encounter.module == "wsgiref.types":
                imported_names = {alias.name for alias in encounter.names}
                if "WSGIEnvironment" in imported_names or "StartResponse" in imported_names:
                    violations.append(str(path.relative_to(PROJECT_ROOT)))
                    break

    assert violations == []


APPLICATION_TEST_ROOT = TEST_ROOT / "unit" / "application"
SPECIALIZED_LOCAL_PORT_TESTS = {
    APPLICATION_TEST_ROOT / "test_archive_management.py",
    APPLICATION_TEST_ROOT / "test_workspace_management.py",
}


def test_general_application_port_doubles_live_in_test_support() -> None:
    """Keep reusable authoring and play ports out of individual feature modules."""
    violations: list[str] = []

    for path in iter_python_files(APPLICATION_TEST_ROOT):
        if path in SPECIALIZED_LOCAL_PORT_TESTS:
            continue
        module = parse_module(path)
        for encounter in module.body:
            if not isinstance(encounter, ast.ClassDef):
                continue
            method_names = {
                item.name for item in encounter.body if isinstance(item, ast.FunctionDef)
            }
            defines_application_port = "load" in method_names and any(
                name.startswith("commit_") for name in method_names
            )
            if defines_application_port:
                violations.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{encounter.lineno}: {encounter.name}"
                )

    assert violations == []


def test_property_tests_use_feature_local_property_module_names() -> None:
    """Keep optional collection out of deterministic loops without a parallel test tree."""
    violations: list[str] = []
    for path in iter_python_files(TEST_ROOT):
        if not path.name.startswith("test_"):
            continue
        module = parse_module(path)
        has_property_marker = any(
            isinstance(encounter, ast.Attribute)
            and dotted_name(encounter) == "pytest.mark.property"
            for encounter in ast.walk(module)
        )
        is_property_module = path.name.startswith("test_") and path.name.endswith("_properties.py")
        if has_property_marker != is_property_module:
            violations.append(str(path.relative_to(PROJECT_ROOT)))

    assert violations == []


def test_registered_custom_markers_are_exercised() -> None:
    """Reject marker tiers that are advertised but select no tests."""
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    marker_entries = pyproject["tool"]["pytest"]["ini_options"]["markers"]
    registered = {str(entry).split(":", maxsplit=1)[0] for entry in marker_entries}

    exercised: set[str] = set()
    for path in iter_python_files(TEST_ROOT):
        module = parse_module(path)
        for encounter in ast.walk(module):
            if not isinstance(encounter, ast.Attribute):
                continue
            name = dotted_name(encounter)
            if name is not None and name.startswith("pytest.mark."):
                exercised.add(name.rsplit(".", maxsplit=1)[-1])

    assert registered.difference(exercised) == set()
