"""Tests for baseline quality-tool configuration."""

from __future__ import annotations

import tomllib
from typing import Any, cast

from tests.support.paths import PROJECT_ROOT

TomlTable = dict[str, Any]

_REQUIRED_DEV_DEPENDENCIES = {
    "bandit",
    "deptry",
    "docstring-format-checker",
    "hypothesis",
    "import-linter",
    "mutmut",
    "pyright",
    "pip-audit",
    "playwright",
    "pytest",
    "pytest-cov",
    "radon",
    "ruff",
    "vulture",
}

_REQUIRED_TOOL_SECTIONS = {
    "bandit",
    "coverage",
    "deptry",
    "dfc",
    "importlinter",
    "mutmut",
    "pyright",
    "pytest",
    "ruff",
}


def _pyproject() -> TomlTable:
    return tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _as_table(value: object) -> TomlTable:
    assert isinstance(value, dict)
    return cast(TomlTable, value)


def _table(parent: TomlTable, key: str) -> TomlTable:
    return _as_table(parent[key])


def test_required_dev_dependencies_are_declared() -> None:
    pyproject = _pyproject()
    project = _table(pyproject, "project")
    optional_dependencies = _table(project, "optional-dependencies")
    dev_dependencies = optional_dependencies["dev"]
    assert isinstance(dev_dependencies, list)
    declared = {
        str(item).split("[", maxsplit=1)[0].split(">", maxsplit=1)[0] for item in dev_dependencies
    }

    missing_dependencies = _REQUIRED_DEV_DEPENDENCIES.difference(declared)

    assert missing_dependencies == set()


def test_beta_metadata_matches_the_tested_distribution_contract() -> None:
    pyproject = _pyproject()
    project = _table(pyproject, "project")

    assert project["requires-python"] == ">=3.11,<3.14"
    assert project["license"] == "LicenseRef-Adventure-Graph-Beta"
    assert project["license-files"] == ["BETA-TERMS.md"]
    classifiers = project["classifiers"]
    assert isinstance(classifiers, list)
    assert "Development Status :: 4 - Beta" in classifiers
    assert "Programming Language :: Python :: 3.11" in classifiers
    assert "Programming Language :: Python :: 3.12" in classifiers
    assert "Programming Language :: Python :: 3.13" in classifiers

    terms = (PROJECT_ROOT / "BETA-TERMS.md").read_text(encoding="utf-8")
    assert "private beta evaluation" in terms
    assert "open-source license" in terms
    assert "These terms are not" in terms


def test_setuptools_owns_the_single_package_build_contract() -> None:
    pyproject = _pyproject()
    build_system = _table(pyproject, "build-system")
    tool = _table(pyproject, "tool")

    assert build_system["build-backend"] == "setuptools.build_meta"
    assert "setuptools" in tool
    assert "poetry" not in tool


def test_required_quality_tool_sections_are_configured() -> None:
    pyproject = _pyproject()
    tool = _table(pyproject, "tool")

    missing_sections = _REQUIRED_TOOL_SECTIONS.difference(tool)

    assert missing_sections == set()
    coverage = _table(tool, "coverage")
    report = _table(coverage, "report")
    assert report["fail_under"] == 90


def test_test_tiers_register_browser_corpus_and_property_contracts() -> None:
    pyproject = _pyproject()
    pytest_config = _table(_table(pyproject, "tool"), "pytest")
    markers = pytest_config["ini_options"]["markers"]

    assert isinstance(markers, list)
    assert any(str(marker).startswith("browser:") for marker in markers)
    assert any(str(marker).startswith("corpus:") for marker in markers)
    assert any(str(marker).startswith("property:") for marker in markers)


def test_pyright_runs_in_strict_mode() -> None:
    pyproject = _pyproject()
    pyright = _table(_table(pyproject, "tool"), "pyright")

    assert pyright["include"] == ["src"]
    assert pyright["typeCheckingMode"] == "strict"
    assert pyright["reportUnnecessaryIsInstance"] == "none"
    assert "src" in pyright["extraPaths"]


def test_import_linter_contract_enforces_clean_architecture_layers() -> None:
    pyproject = _pyproject()
    importlinter = _table(_table(pyproject, "tool"), "importlinter")
    contracts = cast(list[object], importlinter["contracts"])

    assert contracts
    contract = _as_table(contracts[0])
    layers: object = contract["layers"]

    assert importlinter["root_package"] == "adventure_graph"
    assert contract["id"] == "clean-architecture-layers"
    assert contract["type"] == "layers"
    assert layers == [
        "adventure_graph.interfaces | adventure_graph.infrastructure",
        "adventure_graph.application",
        "adventure_graph.domain",
    ]


def test_import_linter_forbids_interface_to_infrastructure_imports() -> None:
    pyproject = _pyproject()
    importlinter = _table(_table(pyproject, "tool"), "importlinter")
    contracts = cast(list[object], importlinter["contracts"])

    contract = _as_table(contracts[1])

    assert contract["id"] == "interfaces-independent-of-infrastructure"
    assert contract["type"] == "forbidden"
    assert contract["source_modules"] == ["adventure_graph.interfaces"]
    assert contract["forbidden_modules"] == ["adventure_graph.infrastructure"]


def test_ci_workflow_runs_the_release_gates() -> None:
    workflow = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "permissions:" in text
    assert "contents: read" in text
    assert 'python -m pip install -e ".[dev]"' in text
    assert "make validate" in text
    assert "make dead-code complexity docstrings security" in text
    assert "python -m pip wheel --no-build-isolation --no-deps --wheel-dir dist ." in text
    assert "python scripts/beta_smoke.py --wheel-dir dist" in text
    assert "python -m playwright install --with-deps chromium" in text
    assert "make test-browser" in text
    validate_job = text.split("  validate:", 1)[1].split("  browser:", 1)[0]
    assert 'python-version: ["3.11", "3.12", "3.13"]' in validate_job
    assert "make validate" in validate_job
    package_job = text.split("  package:", 1)[1]
    assert 'python-version: ["3.11", "3.12", "3.13"]' in package_job
    assert "python-version: ${{ matrix.python-version }}" in package_job
    assert "ubuntu-latest" in package_job
    assert "windows-latest" in package_job
    assert "macos-latest" in package_job


def test_dependabot_tracks_python_and_github_actions_dependencies() -> None:
    dependabot = PROJECT_ROOT / ".github" / "dependabot.yml"
    text = dependabot.read_text(encoding="utf-8")

    assert 'package-ecosystem: "github-actions"' in text
    assert 'package-ecosystem: "pip"' in text
    assert 'interval: "weekly"' in text


def test_makefile_defaults_to_help_instead_of_mutating_the_environment() -> None:
    makefile = PROJECT_ROOT / "Makefile"
    text = makefile.read_text(encoding="utf-8")

    assert ".DEFAULT_GOAL := help" in text


def _makefile_targets() -> set[str]:
    makefile = PROJECT_ROOT / "Makefile"
    targets: set[str] = set()

    for line in makefile.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith(("\t", ".", "#")):
            continue
        name, separator, _recipe = line.partition(":")
        if separator and name and " " not in name and "=" not in name:
            targets.add(name)

    return targets


def test_makefile_exposes_primary_workflow_targets() -> None:
    targets = _makefile_targets()

    required_targets = {
        "install",
        "install-desktop-build",
        "quick",
        "schema-check",
        "validate",
        "validate-all",
        "ci",
        "test",
        "test-fast",
        "test-unit",
        "test-integration",
        "test-corpus",
        "test-browser",
        "test-architecture",
        "test-smoke",
        "format",
        "format-check",
        "typecheck",
        "imports",
        "security-deps",
        "mutation",
        "package",
        "desktop-package",
        "desktop-verify",
        "doctor",
    }

    assert required_targets.issubset(targets)


def test_makefile_avoids_synonym_targets() -> None:
    targets = _makefile_targets()
    synonym_targets = {
        "setup",
        "bootstrap",
        "fix",
        "format-fix",
        "strict",
        "quality",
        "audit",
        "check",
        "all",
        "release-check",
    }

    assert targets.isdisjoint(synonym_targets)


def test_makefile_enforces_coverage_and_extended_security_gates() -> None:
    text = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

    assert (
        "validate: metadata format-check typecheck schema-check test-property coverage "
        "deptry imports source-audit"
    ) in text
    assert "PYTEST_DETERMINISTIC_MARKERS := not browser and not property" in text
    assert "BROWSER_IGNORE_ARGS := --ignore=tests/browser" in text
    assert "PROPERTY_TEST_PATHS := $(shell find tests -type f -name 'test_*_properties.py'" in text
    assert 'test-property:\n\t$(PYTHON) -c "import hypothesis"' in text
    assert "$(PYTHON) -m pytest $(PROPERTY_TEST_PATHS) -m property" in text
    assert (
        'coverage:\n\t$(PYTHON) -m pytest $(PROPERTY_IGNORE_ARGS) $(BROWSER_IGNORE_ARGS) '
        '-m "$(PYTEST_COVERAGE_MARKERS)"'
    ) in text
    assert "validate-all: validate dead-code complexity docstrings security" in text
    assert "ci: validate-all package beta-smoke source-package" in text


def test_makefile_does_not_advertise_empty_test_tiers() -> None:
    targets = _makefile_targets()

    assert "test-external" not in targets
    assert "test-slow" not in targets


def test_desktop_workflow_builds_native_artifacts() -> None:
    workflow = PROJECT_ROOT / ".github" / "workflows" / "desktop.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "actions/checkout@v7" in text
    assert "actions/setup-python@v7" in text
    assert "actions/upload-artifact@v7" in text
    assert "actions/download-artifact@v8" in text
    assert 'python-version: "3.13"' in text
    assert "ubuntu-latest" in text
    assert "windows-latest" in text
    assert "macos-latest" in text
    assert "python -m pip install -r packaging/desktop-build-requirements.txt" in text
    assert "python -m pip install --no-build-isolation --no-deps -e ." in text
    assert "python -m pip check" in text
    assert "cache-dependency-path: packaging/desktop-build-requirements.txt" in text
    assert "python scripts/build_desktop.py --output-dir dist/desktop" in text
    assert "compression-level: 0" in text
    assert "merge-multiple: true" in text
    assert '- "src/**"' in text
    assert '- "scripts/desktop_build_environment.py"' in text
    assert '- "schemas/desktop-artifact-manifest.schema.json"' in text
    assert "--require-platforms linux windows macos" in text
    assert "--source-revision" in text
