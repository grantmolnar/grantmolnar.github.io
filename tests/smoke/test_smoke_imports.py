"""Smoke tests for package imports and command-line entry points."""

from __future__ import annotations

import os
import pkgutil
import subprocess
import sys
from collections import defaultdict

import pytest

from tests.support.paths import (
    PACKAGE_NAME,
    PACKAGE_ROOT,
    PROJECT_ROOT,
    SRC_ROOT,
)

pytestmark = pytest.mark.smoke


def _python_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTEST_CURRENT_TEST", None)
    existing_python_path = env.get("PYTHONPATH")
    src_path = str(SRC_ROOT)
    env["PYTHONPATH"] = src_path
    if existing_python_path:
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{existing_python_path}"
    return env


def _run_python(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=PROJECT_ROOT,
        env=_python_env(),
        text=True,
        capture_output=True,
        check=False,
        timeout=20,
    )


def _discover_package_modules() -> list[str]:
    modules = [PACKAGE_NAME]
    modules.extend(
        module_info.name
        for module_info in pkgutil.walk_packages([str(PACKAGE_ROOT)], prefix=f"{PACKAGE_NAME}.")
    )
    return sorted(set(modules))


def _module_groups() -> list[tuple[str, tuple[str, ...]]]:
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for module_name in _discover_package_modules():
        segments = module_name.split(".")
        group = segments[1] if len(segments) > 1 else "package"
        groups[group].append(module_name)
    return [(name, tuple(modules)) for name, modules in sorted(groups.items())]


@pytest.mark.parametrize(("group_name", "module_names"), _module_groups())
def test_package_module_groups_import_cleanly(
    group_name: str,
    module_names: tuple[str, ...],
) -> None:
    script = (
        "import importlib; "
        f"modules = {module_names!r}; "
        "[importlib.import_module(name) for name in modules]"
    )
    result = _run_python(["-c", script])

    assert result.returncode == 0, f"{group_name}: {result.stderr}"
    assert result.stdout == ""
    assert result.stderr == ""


def test_module_entry_point_supports_help() -> None:
    result = _run_python(["-m", PACKAGE_NAME, "--help"])

    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout.lower()
    assert "lead-driven adventure graphs" in result.stdout
    assert "add-clue            Append a lead to an adventure." in result.stdout
    assert result.stderr == ""


def test_module_entry_point_reports_installed_or_source_version() -> None:
    result = _run_python(["-m", PACKAGE_NAME, "--version"])

    assert result.returncode == 0
    assert result.stdout.startswith("adventure-graph ")
