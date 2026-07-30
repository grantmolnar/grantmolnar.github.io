"""Architecture checks for process dispatch and local adapter composition."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from adventure_graph.cli_execution import command_handlers
from tests.support.paths import PACKAGE_ROOT
from tests.support.python_ast import parse_module

pytestmark = pytest.mark.architecture


def _imported_modules(path: Path) -> set[str]:
    modules: set[str] = set()
    for encounter in ast.walk(parse_module(path)):
        if isinstance(encounter, ast.Import):
            modules.update(alias.name for alias in encounter.names)
        elif isinstance(encounter, ast.ImportFrom) and encounter.module is not None:
            modules.add(encounter.module)
    return modules


def test_bootstrap_remains_a_small_process_dispatcher() -> None:
    bootstrap = PACKAGE_ROOT / "bootstrap.py"

    assert len(bootstrap.read_text(encoding="utf-8").splitlines()) <= 80
    assert {
        "adventure_graph.cli_execution",
        "adventure_graph.web_composition",
    }.issubset(_imported_modules(bootstrap))


def test_cli_execution_does_not_depend_on_browser_composition() -> None:
    imports = _imported_modules(PACKAGE_ROOT / "cli_execution.py")

    assert "adventure_graph.web_composition" not in imports
    assert all(not module.startswith("adventure_graph.interfaces.web") for module in imports)


def test_web_composition_does_not_depend_on_cli_execution() -> None:
    imports = _imported_modules(PACKAGE_ROOT / "web_composition.py")

    assert "adventure_graph.cli_execution" not in imports
    assert "adventure_graph.interfaces.presentation" not in imports


def test_cli_command_registry_is_fresh_and_complete() -> None:
    first = command_handlers()
    second = command_handlers()

    assert first is not second
    assert set(first) == {
        "init",
        "archive",
        "start-session",
        "end-session",
        "list-archives",
        "restore-archive",
        "delete-archive",
        "validate",
        "list",
        "inspect",
        "add-encounter",
        "add-reference",
        "add-revelation",
        "add-clue",
        "edit-encounter",
        "edit-reference",
        "edit-revelation",
        "edit-clue",
        "move-clue",
        "link-reference",
        "unlink-reference",
        "remove-encounter",
        "remove-reference",
        "remove-revelation",
        "remove-clue",
        "render",
        "visit",
        "spot-clue",
        "miss-clue",
        "establish-revelation",
        "foreclose-revelation",
        "reopen-revelation",
        "unlock-encounter",
        "consequence",
        "note",
        "reference-note",
        "correct-latest",
        "summary",
    }


def test_play_feature_is_composed_as_one_complete_capability() -> None:
    composition = (PACKAGE_ROOT / "web_composition.py").read_text(encoding="utf-8")
    contracts = (PACKAGE_ROOT / "interfaces" / "web" / "contracts.py").read_text(encoding="utf-8")
    authoring_app = (PACKAGE_ROOT / "interfaces" / "web" / "app.py").read_text(encoding="utf-8")

    assert "play=PlayCapability(" in composition
    assert "class PlayCapability:" in contracts
    assert "queries: PlayQueries" in contracts
    assert "commands: PlayCommands" in contracts
    assert "class PlayLedgerQueries:" in contracts
    assert "ledgers=PlayLedgerQueries(" in composition
    assert "get_workspace=GetPlayLedgerWorkspace(projects.play).execute" in composition
    assert "get_journal_workspace=GetJournalWorkspace(projects.play).execute" in composition
    assert "get_ledgers: Callable[[PlayLedgerScope], PlayLedgersResult] | None" not in contracts
    assert "play: PlayCapability | None = None" in authoring_app
    assert "play_queries:" not in authoring_app
    assert "play_commands:" not in authoring_app


def test_workspace_settings_use_explicit_application_contracts() -> None:
    composition = (PACKAGE_ROOT / "web_composition.py").read_text(encoding="utf-8")
    contracts = (PACKAGE_ROOT / "interfaces" / "web" / "contracts.py").read_text(encoding="utf-8")
    workspace_app = (PACKAGE_ROOT / "interfaces" / "web" / "workspace_app.py").read_text(
        encoding="utf-8"
    )

    assert "get_adventure_overview=get_adventure_overview" in composition
    assert "update_adventure_validation_policy=update_adventure_validation_policy" in composition
    assert "get_adventure_overview: Callable[[str], AdventureOverviewResult]" in contracts
    assert "update_adventure_validation_policy: Callable[" in contracts
    assert ".queries.get_overview()" not in workspace_app
    assert ".commands.update_validation_policy(" not in workspace_app


def test_cli_structural_and_reference_authoring_uses_shared_application_commands() -> None:
    path = PACKAGE_ROOT / "cli_authoring_commands.py"
    module = parse_module(path)
    imports_by_module = {
        encounter.module: {alias.name for alias in encounter.names}
        for encounter in module.body
        if isinstance(encounter, ast.ImportFrom) and encounter.module is not None
    }
    text = path.read_text(encoding="utf-8")

    assert {
        "CreateClue",
        "CreateClueCommand",
        "CreateRevelation",
        "CreateRevelationCommand",
        "UpdateClue",
        "UpdateClueCommand",
        "UpdateRevelation",
        "UpdateRevelationCommand",
    }.issubset(imports_by_module["adventure_graph.application.structural_authoring"])
    assert {
        "CreateReference",
        "CreateReferenceCommand",
        "UpdateReference",
        "UpdateReferenceCommand",
        "LinkReference",
        "LinkReferenceCommand",
        "UnlinkReference",
        "UnlinkReferenceCommand",
        "RemoveReference",
        "RemoveReferenceCommand",
    }.issubset(imports_by_module["adventure_graph.application.reference_authoring"])
    assert imports_by_module["adventure_graph.application.authoring"].isdisjoint(
        {
            "add_clue",
            "add_revelation",
            "remap_play_state_identifiers",
            "rename_clue",
            "rename_revelation",
            "update_clue",
            "update_revelation",
        }
    )
    assert text.count("project = _authoring_project(args)") == 15
    assert "adventure_graph.infrastructure.adventure_store" not in imports_by_module
    assert "adventure_graph.infrastructure.local_project_paths" not in imports_by_module
    assert "adventure_graph.infrastructure.play_state_store" not in imports_by_module
    assert "project_play_state" not in text


def test_authoring_post_orchestration_is_separate_from_the_wsgi_shell() -> None:
    web_root = PACKAGE_ROOT / "interfaces" / "web"
    authoring_app = (web_root / "app.py").read_text(encoding="utf-8")
    action_workspace = (web_root / "authoring_action_workspace.py").read_text(encoding="utf-8")

    assert "AuthoringActionWorkspace" in authoring_app
    assert "self._authoring_actions.write(path, environ)" in authoring_app
    assert "parse_adventure_form" not in authoring_app
    assert "CreateClueCommand" not in authoring_app
    assert "class AuthoringActionWorkspace:" in action_workspace
    assert "def write(self, path: str, environ: WSGIEnvironment)" in action_workspace
    assert "parse_adventure_form" in action_workspace
    assert "CreateClueCommand" in action_workspace
    assert "archive_action_response" not in action_workspace
    assert "PlayWebWorkspace" not in action_workspace
