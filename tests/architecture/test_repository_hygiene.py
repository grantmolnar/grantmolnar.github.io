"""Repository-wide hygiene tests for portable, non-leaky baselines."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from tests.support.paths import PROJECT_ROOT

pytestmark = pytest.mark.architecture

_ALLOWED_ROOT_PYTHON_FILES = {"noxfile.py", "tasks.py"}
_TEXT_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
_IGNORED_PARTS = {
    ".git",
    ".hypothesis",
    ".import_linter_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "htmlcov",
    "mutants",
    "__pycache__",
}

_REQUIRED_GITIGNORE_PATTERNS = {
    "__pycache__/",
    "*.py[cod]",
    ".coverage",
    ".coverage.*",
    "coverage.xml",
    "htmlcov/",
    ".hypothesis/",
    ".import_linter_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    ".venv/",
    "node_modules/",
    ".mutmut-cache/",
    "mutants/",
    ".env",
    ".env.*",
    "!.env.example",
}

_FORBIDDEN_TEXT_PATTERNS = {
    "private key material": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "GitHub personal access token": re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    "AWS access key id": re.compile(r"AKIA[0-9A-Z]{16}"),
    "hard-coded Unix home path": re.compile(r"/home/[A-Za-z0-9_.-]+/"),
    "hard-coded Windows user path": re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\\\s]+\\\\"),
}


_RETIRED_ADVENTURE_WORKBENCH_EXACT_NAMES = {
    "BUILD-PLAN.md",
    "ENCOUNTER-CONSTRUCTION.md",
    "FINAL-BUILD-OUT-CONSISTENCY-AUDIT.md",
    "FINAL-CONSISTENCY-AUDIT.md",
    "PREMISE-AND-CAUSALITY-AUDIT.md",
    "REVELATION-PLAN.md",
    "ROUTE-STRUCTURE-AUDIT.md",
    "VOICE-AND-COHERENCE-AUDIT.md",
}
_RETIRED_ADVENTURE_WORKBENCH_PREFIXES = (
    "EXPANSION-SESSION-",
    "REFERENCE-DEFRAGMENTATION-",
    "SECOND-LOOK-",
)
_RETIRED_ADVENTURE_WORKBENCH_SUFFIXES = ("-STRESS-TEST.md",)
_RETIRED_ADVENTURE_WORKBENCH_DIRECTORIES = {"audits", "development"}


def _iter_repository_files() -> list[Path]:
    return sorted(
        path
        for path in PROJECT_ROOT.rglob("*")
        if path.is_file()
        and not any(part in _IGNORED_PARTS for part in path.relative_to(PROJECT_ROOT).parts)
    )


def test_completed_test_hardening_handoffs_are_not_packaged() -> None:
    stale_paths = [
        *PROJECT_ROOT.glob("ADVENTURE_GRAPH_TEST_HARDENING_SESSION_*_HANDOFF.md"),
        *(PROJECT_ROOT / "docs").glob("test-hardening-session-*.md"),
        *(PROJECT_ROOT / "docs").glob("adventure-reference-defragmentation-session-*-handoff.md"),
        *(PROJECT_ROOT / "docs").glob("adventure-reference-library-phase-*-handoff.md"),
        *(PROJECT_ROOT / "docs").glob("play-interface-panel-session-*-handoff.md"),
        PROJECT_ROOT / "docs" / "test-hardening-roadmap.md",
        PROJECT_ROOT / "docs" / "play-interface-panel-roadmap.md",
        PROJECT_ROOT / "docs" / "private-beta-platform-signoff-handoff.md",
        PROJECT_ROOT / "docs" / "reference-defragmentation-ui-integration-session-01-handoff.md",
    ]

    packaged_stale_paths = [path.relative_to(PROJECT_ROOT) for path in stale_paths if path.exists()]

    assert packaged_stale_paths == []


def test_bundled_adventures_do_not_retain_completed_workbench_artifacts() -> None:
    examples = PROJECT_ROOT / "examples"
    violations: list[Path] = []

    for path in sorted(examples.rglob("*")):
        relative_path = path.relative_to(PROJECT_ROOT)
        if path.is_dir() and path.name.casefold() in _RETIRED_ADVENTURE_WORKBENCH_DIRECTORIES:
            violations.append(relative_path)
            continue
        if not path.is_file():
            continue
        if (
            path.name in _RETIRED_ADVENTURE_WORKBENCH_EXACT_NAMES
            or path.name.startswith(_RETIRED_ADVENTURE_WORKBENCH_PREFIXES)
            or path.name.endswith(_RETIRED_ADVENTURE_WORKBENCH_SUFFIXES)
        ):
            violations.append(relative_path)

    assert violations == []


def test_root_python_files_are_deliberate_exceptions() -> None:
    unexpected_files = sorted(
        path.name
        for path in PROJECT_ROOT.glob("*.py")
        if path.name not in _ALLOWED_ROOT_PYTHON_FILES
    )

    assert unexpected_files == []


def test_repository_text_files_do_not_contain_common_secret_or_local_path_patterns() -> None:
    violations: list[str] = []

    for path in _iter_repository_files():
        if path.suffix not in _TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in _FORBIDDEN_TEXT_PATTERNS.items():
            if pattern.search(text):
                relative_path = path.relative_to(PROJECT_ROOT)
                violations.append(f"{relative_path}: {label}")

    assert violations == []


def test_gitignore_excludes_common_generated_and_local_artifacts() -> None:
    gitignore = PROJECT_ROOT / ".gitignore"
    patterns = {
        line.strip()
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }

    missing_patterns = _REQUIRED_GITIGNORE_PATTERNS.difference(patterns)

    assert missing_patterns == set()


def test_runtime_and_schema_contract_use_encounter_vocabulary_only() -> None:
    retired_term = re.compile(r"(?:\bnode(?:s)?\b|node_|_node)", re.IGNORECASE)
    help_renderer = Path("src/adventure_graph/interfaces/web/workspace_rendering.py")
    roots = (PROJECT_ROOT / "src" / "adventure_graph", PROJECT_ROOT / "schemas")
    violations: list[str] = []

    for root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            relative_path = path.relative_to(PROJECT_ROOT)
            if "node" in path.name.casefold():
                violations.append(f"{relative_path}: retired term in path")
                continue
            if path.suffix not in {".py", ".json", ".js", ".css"}:
                continue
            text = path.read_text(encoding="utf-8")
            for match in retired_term.finditer(text):
                names_external_method = (
                    relative_path == help_renderer
                    and match.group(0).casefold() == "node"
                    and text[match.end() : match.end() + 6].casefold() == "-based"
                )
                if not names_external_method:
                    violations.append(f"{relative_path}: retired term in content")
                    break

    assert violations == []


def test_beta_schema_versions_are_explicit() -> None:
    adventure_schema = json.loads(
        (PROJECT_ROOT / "schemas" / "adventure.schema.json").read_text(encoding="utf-8")
    )
    play_schema = json.loads(
        (PROJECT_ROOT / "schemas" / "play-state.schema.json").read_text(encoding="utf-8")
    )

    assert adventure_schema["properties"]["schema_version"]["const"] == 3
    assert play_schema["properties"]["schema_version"]["const"] == 6


def test_private_beta_packages_only_the_glass_saint_sample() -> None:
    resources = PROJECT_ROOT / "src" / "adventure_graph" / "resources"

    assert {path.name for path in resources.glob("*.adventure.json")} == {
        "the-glass-saint.adventure.json"
    }


def test_repository_example_matches_packaged_template() -> None:
    example = PROJECT_ROOT / "examples" / "the-glass-saint.adventure.json"
    template = (
        PROJECT_ROOT / "src" / "adventure_graph" / "resources" / "the-glass-saint.adventure.json"
    )

    assert example.read_bytes() == template.read_bytes()
