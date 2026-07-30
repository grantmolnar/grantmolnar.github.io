"""Static architecture tests for dependency direction and unsafe hacks."""

from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.support.paths import (
    PACKAGE_NAME,
    PACKAGE_ROOT,
    PROJECT_ROOT,
    SRC_ROOT,
    iter_python_files,
)
from tests.support.python_ast import dotted_name, parse_module

pytestmark = pytest.mark.architecture

FORBIDDEN_LAYER_IMPORTS = {
    f"{PACKAGE_NAME}.domain": (
        f"{PACKAGE_NAME}.application",
        f"{PACKAGE_NAME}.infrastructure",
        f"{PACKAGE_NAME}.interfaces",
    ),
    f"{PACKAGE_NAME}.application": (
        f"{PACKAGE_NAME}.infrastructure",
        f"{PACKAGE_NAME}.interfaces",
    ),
    f"{PACKAGE_NAME}.infrastructure": (f"{PACKAGE_NAME}.interfaces",),
    f"{PACKAGE_NAME}.interfaces": (f"{PACKAGE_NAME}.infrastructure",),
}

FORBIDDEN_CALLS = {
    "os.system",
    "os.popen",
    "os.spawnl",
    "os.spawnle",
    "os.spawnlp",
    "os.spawnlpe",
    "os.spawnv",
    "os.spawnve",
    "os.spawnvp",
    "os.spawnvpe",
    "sys.path.append",
    "sys.path.insert",
}

SUBPROCESS_CALLS = {
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
}


def _module_name_from_file(path: Path) -> str:
    relative_path = path.relative_to(SRC_ROOT)
    parts = list(relative_path.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _absolute_import_name(path: Path, encounter: ast.ImportFrom) -> str | None:
    if encounter.module is None and encounter.level == 0:
        return None
    if encounter.level == 0:
        return encounter.module

    current_module = _module_name_from_file(path)
    if path.name == "__init__.py":
        current_package = current_module
    else:
        current_package = current_module.rpartition(".")[0]
    package_parts = current_package.split(".") if current_package else []
    keep_count = len(package_parts) - encounter.level + 1
    if keep_count < 0:
        return encounter.module
    base = ".".join(package_parts[:keep_count])
    if encounter.module is None:
        return base
    return f"{base}.{encounter.module}" if base else encounter.module


def _iter_imports(path: Path) -> Iterator[str]:
    module = parse_module(path)
    for encounter in ast.walk(module):
        if isinstance(encounter, ast.Import):
            for alias in encounter.names:
                yield alias.name
        elif isinstance(encounter, ast.ImportFrom):
            import_name = _absolute_import_name(path, encounter)
            if import_name is not None:
                yield import_name


def _is_or_is_below(module_name: str, package_name: str) -> bool:
    return module_name == package_name or module_name.startswith(f"{package_name}.")


def _iter_calls(path: Path) -> Iterator[tuple[int, str]]:
    module = parse_module(path)
    for encounter in ast.walk(module):
        if isinstance(encounter, ast.Call):
            name = dotted_name(encounter.func)
            if name is not None:
                yield encounter.lineno, name


def _iter_subprocess_shell_calls(path: Path) -> Iterator[int]:
    module = parse_module(path)
    for encounter in ast.walk(module):
        if not isinstance(encounter, ast.Call):
            continue
        call_name = dotted_name(encounter.func)
        if call_name not in SUBPROCESS_CALLS:
            continue
        for keyword in encounter.keywords:
            if (
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
            ):
                yield encounter.lineno


def _iter_runtime_python_files() -> Iterator[Path]:
    yield from iter_python_files(PACKAGE_ROOT)


def test_clean_architecture_layers_are_present() -> None:
    expected_layers = {"domain", "application", "infrastructure", "interfaces"}
    actual_layers = {path.name for path in PACKAGE_ROOT.iterdir() if path.is_dir()}

    assert expected_layers.issubset(actual_layers)


def test_package_has_py_typed_marker() -> None:
    assert (PACKAGE_ROOT / "py.typed").is_file()


def test_internal_imports_follow_dependency_direction() -> None:
    violations: list[str] = []

    for path in iter_python_files(PACKAGE_ROOT):
        importer = _module_name_from_file(path)
        forbidden_imports = tuple(
            forbidden
            for layer, forbidden_group in FORBIDDEN_LAYER_IMPORTS.items()
            if _is_or_is_below(importer, layer)
            for forbidden in forbidden_group
        )
        for imported in _iter_imports(path):
            for forbidden in forbidden_imports:
                if _is_or_is_below(imported, forbidden):
                    relative_path = path.relative_to(PROJECT_ROOT)
                    violations.append(f"{relative_path}: {importer} imports {imported}")

    assert violations == []


def test_runtime_code_does_not_use_common_os_hacks() -> None:
    violations: list[str] = []

    for path in _iter_runtime_python_files():
        for line_number, call_name in _iter_calls(path):
            if call_name in FORBIDDEN_CALLS:
                relative_path = path.relative_to(PROJECT_ROOT)
                violations.append(f"{relative_path}:{line_number}: {call_name}")
        for line_number in _iter_subprocess_shell_calls(path):
            relative_path = path.relative_to(PROJECT_ROOT)
            violations.append(f"{relative_path}:{line_number}: subprocess call uses shell=True")

    assert violations == []


def test_ordinary_title_edits_cannot_rederive_or_remap_identifiers() -> None:
    adventure_update = (PACKAGE_ROOT / "application" / "adventure_authoring.py").read_text(
        encoding="utf-8"
    )
    encounter_update = (PACKAGE_ROOT / "application" / "encounter_authoring.py").read_text(
        encoding="utf-8"
    )
    structural_update = (PACKAGE_ROOT / "application" / "structural_authoring.py").read_text(
        encoding="utf-8"
    )
    workspace_creation = (PACKAGE_ROOT / "application" / "workspace_management.py").read_text(
        encoding="utf-8"
    )

    assert "identifier_slug" not in adventure_update
    assert "remap_play_state_identifiers" not in adventure_update
    assert "unique_identifier" not in encounter_update
    assert "rename_encounter" not in encounter_update
    assert "remap_play_state_identifiers" not in encounter_update
    assert "rename_clue" not in structural_update
    assert "rename_revelation" not in structural_update
    assert "remap_play_state_identifiers" not in structural_update
    assert "new_adventure_identifier" in workspace_creation


def test_runtime_code_does_not_classify_errors_by_message_text() -> None:
    forbidden_patterns = (
        ("unknown-prefix classification", 'str(error).startswith("Unknown "'),
        ("no-change equality classification", 'str(error) == "No '),
        ("no-change inequality classification", 'str(error) != "No '),
    )
    violations: list[str] = []

    for path in _iter_runtime_python_files():
        text = path.read_text(encoding="utf-8")
        for label, snippet in forbidden_patterns:
            if snippet in text:
                relative_path = path.relative_to(PROJECT_ROOT)
                violations.append(f"{relative_path}: {label}")

    assert violations == []


def test_workspace_shell_does_not_reconstruct_selected_adventure_responses() -> None:
    workspace_app = PACKAGE_ROOT / "interfaces" / "web" / "workspace_app.py"
    text = workspace_app.read_text(encoding="utf-8")

    assert "def _delegate(" not in text
    assert "captured_status" not in text
    assert "captured_headers" not in text
    assert "body.decode(" not in text


def test_authoring_shell_does_not_own_play_route_implementation() -> None:
    authoring_app = PACKAGE_ROOT / "interfaces" / "web" / "app.py"
    text = authoring_app.read_text(encoding="utf-8")

    assert "adventure_graph.interfaces.web.play_workspace" in text
    assert "adventure_graph.interfaces.web.play_forms" not in text
    assert "adventure_graph.interfaces.web.run_forms" not in text
    assert "adventure_graph.interfaces.web.play_ledger_workspace" not in text
    assert '"/play' not in text
    assert '"/run' not in text
    assert '"/journal' not in text
    assert "def _play_write(" not in text
    assert "def _run_write(" not in text
    assert "def _correct_latest_operation(" not in text


_LAYER_PACKAGE_INITIALIZERS = (
    PACKAGE_ROOT / "application" / "__init__.py",
    PACKAGE_ROOT / "domain" / "__init__.py",
    PACKAGE_ROOT / "infrastructure" / "__init__.py",
    PACKAGE_ROOT / "interfaces" / "__init__.py",
    PACKAGE_ROOT / "interfaces" / "web" / "__init__.py",
)


def test_layer_package_initializers_do_not_reexport_runtime_symbols() -> None:
    violations: list[str] = []

    for path in _LAYER_PACKAGE_INITIALIZERS:
        module = parse_module(path)
        for encounter in module.body:
            if isinstance(encounter, ast.Import | ast.ImportFrom):
                relative_path = path.relative_to(PROJECT_ROOT)
                violations.append(f"{relative_path}:{encounter.lineno}: package re-export")

    assert violations == []


def test_removed_compatibility_modules_do_not_return() -> None:
    removed_paths = (
        PACKAGE_ROOT / "domain" / "models.py",
        PACKAGE_ROOT / "interfaces" / "web" / "rendering.py",
    )

    assert [path for path in removed_paths if path.exists()] == []


def test_package_and_tests_import_defining_modules_directly() -> None:
    retired_facades = {
        f"{PACKAGE_NAME}.application",
        f"{PACKAGE_NAME}.domain",
        f"{PACKAGE_NAME}.domain.models",
        f"{PACKAGE_NAME}.infrastructure",
        f"{PACKAGE_NAME}.interfaces",
        f"{PACKAGE_NAME}.interfaces.web",
        f"{PACKAGE_NAME}.interfaces.web.rendering",
    }
    initializer_paths = set(_LAYER_PACKAGE_INITIALIZERS)
    violations: list[str] = []

    for root in (PACKAGE_ROOT, PROJECT_ROOT / "tests"):
        for path in iter_python_files(root):
            if path in initializer_paths:
                continue
            for imported in _iter_imports(path):
                if imported in retired_facades:
                    relative_path = path.relative_to(PROJECT_ROOT)
                    violations.append(f"{relative_path}: imports retired facade {imported}")

    assert violations == []


def test_play_write_dispatch_uses_command_specific_executors() -> None:
    workspace = PACKAGE_ROOT / "interfaces" / "web" / "play_workspace.py"
    actions = PACKAGE_ROOT / "interfaces" / "web" / "play_write_actions.py"
    workspace_text = workspace.read_text(encoding="utf-8")
    action_text = actions.read_text(encoding="utf-8")
    committed_routes = (
        "/play/session/start",
        "/play/session/end",
        "/play/enter",
        "/play/clue/found",
        "/play/clue/missed",
        "/play/revelation/establish",
        "/play/revelation/foreclose",
        "/play/revelation/reopen",
        "/play/unlock",
        "/play/note",
        "/play/consequence",
        "/play/dice/record",
        "/play/transition",
    )

    assert "PlayWriteActions" in workspace_text
    assert "PLR0912" not in workspace_text
    assert "PLR0915" not in workspace_text
    assert "render_play(" not in action_text
    for route in committed_routes:
        assert route not in workspace_text
        assert route in action_text


def test_web_shells_share_one_wsgi_response_emitter() -> None:
    authoring_app = PACKAGE_ROOT / "interfaces" / "web" / "app.py"
    workspace_app = PACKAGE_ROOT / "interfaces" / "web" / "workspace_app.py"
    http_primitives = PACKAGE_ROOT / "interfaces" / "web" / "http.py"

    authoring_text = authoring_app.read_text(encoding="utf-8")
    workspace_text = workspace_app.read_text(encoding="utf-8")
    http_text = http_primitives.read_text(encoding="utf-8")

    assert "def emit_response(" in http_text
    assert "def _respond(" not in authoring_text
    assert "def _respond(" not in workspace_text
    assert "emit_response" in authoring_text
    assert "emit_response" in workspace_text


def test_authoring_updates_share_conflict_noop_and_rejection_control_flow() -> None:
    web_root = PACKAGE_ROOT / "interfaces" / "web"
    authoring_app = (web_root / "app.py").read_text(encoding="utf-8")
    action_workspace = (web_root / "authoring_action_workspace.py").read_text(
        encoding="utf-8"
    )
    update_text = (web_root / "authoring_updates.py").read_text(encoding="utf-8")

    assert "execute_authoring_update" not in authoring_app
    assert "execute_authoring_update" in action_workspace
    assert "except NoChangesRequestedError" not in action_workspace
    assert "except NoChangesRequestedError" in update_text
    assert "except RevisionConflictError" in update_text
