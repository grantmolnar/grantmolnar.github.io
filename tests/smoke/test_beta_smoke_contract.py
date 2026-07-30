"""Regression tests for the installed-wheel workflow command contract."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest
from scripts.beta_smoke import (
    AUDIT_COPY_PROJECT_NAME,
    AUDIT_COPY_WORKSPACE_NAME,
    AUDIT_PROJECT_NAME,
    AUDIT_RENAMED_PROJECT_NAME,
    AUDIT_SAMPLE_WORKSPACE_NAME,
    AUDIT_SECOND_PROJECT_NAME,
    AUDIT_WORKSPACE_NAME,
    _form_fields,
    _verify_wheel_contract,
    authoring_command_arguments,
    play_command_arguments,
)

from adventure_graph.interfaces.cli import parse_args

pytestmark = pytest.mark.smoke


@pytest.mark.parametrize(
    "arguments",
    [
        *authoring_command_arguments(Path("workspace/project/adventure.json")),
        *play_command_arguments(
            Path("workspace/project/adventure.json"),
            Path("workspace/project/play-state.json"),
        ),
    ],
)
def test_beta_smoke_workflow_commands_match_the_installed_cli_contract(
    arguments: tuple[str, ...],
) -> None:
    parsed = parse_args(arguments)

    assert parsed.command == arguments[0]


def test_beta_smoke_note_command_carries_adventure_and_state_context() -> None:
    commands = play_command_arguments(
        Path("workspace/project/adventure.json"),
        Path("workspace/project/play-state.json"),
    )
    note = next(arguments for arguments in commands if arguments[0] == "note")

    assert note[:5] == (
        "note",
        "workspace/project/adventure.json",
        "workspace/project/play-state.json",
        "1",
        "The curator keeps an authenticated copy.",
    )


def test_beta_browser_form_parser_preserves_submitted_browser_values() -> None:
    page = """
    <form method="post" action="/audit">
      <input type="hidden" name="csrf_token" value="token&amp;value">
      <input type="text" name="title" value="Current title">
      <input type="checkbox" name="required" value="1" checked>
      <input type="checkbox" name="start" value="1">
      <textarea name="content">Line one &amp; line two</textarea>
      <select name="mode">
        <option value="draft">Draft</option>
        <option value="final" selected>Final</option>
      </select>
    </form>
    """

    assert _form_fields(page, "/audit") == {
        "csrf_token": "token&value",
        "title": "Current title",
        "required": "1",
        "content": "Line one & line two",
        "mode": "final",
    }


def test_beta_browser_form_parser_requires_one_exact_action() -> None:
    page = '<form action="/audit"></form><form action="/audit"></form>'

    with pytest.raises(RuntimeError, match="Expected one browser form"):
        _form_fields(page, "/audit")


def test_beta_smoke_paths_cover_spaces_and_non_ascii_names() -> None:
    names = (
        AUDIT_WORKSPACE_NAME,
        AUDIT_PROJECT_NAME,
        AUDIT_SECOND_PROJECT_NAME,
        AUDIT_SAMPLE_WORKSPACE_NAME,
        AUDIT_COPY_WORKSPACE_NAME,
        AUDIT_COPY_PROJECT_NAME,
        AUDIT_RENAMED_PROJECT_NAME,
    )

    assert all(" " in name for name in names)
    assert all(any(ord(character) > 127 for character in name) for name in names)


def _minimal_wheel(path: Path, *, extra_files: dict[str, bytes] | None = None) -> Path:
    files = {
        "adventure_graph/py.typed": b"",
        "adventure_graph/desktop.py": b"",
        "adventure_graph/infrastructure/desktop_settings.py": b"",
        "adventure_graph/resources/the-glass-saint.adventure.json": b"{}",
        "adventure_graph/interfaces/web/assets/app.css": b"",
        "adventure_graph/interfaces/web/assets/app.js": b"",
        "adventure_graph-0.10.0.dist-info/METADATA": (
            b"Metadata-Version: 2.4\n"
            b"Name: adventure-graph\n"
            b"Version: 0.10.0\n"
            b"Requires-Python: >=3.11,<3.14\n"
            b"License-Expression: LicenseRef-Adventure-Graph-Beta\n\n"
        ),
        "adventure_graph-0.10.0.dist-info/licenses/BETA-TERMS.md": (
            b"Copyright (c) 2026 Grant Molnar. All rights reserved.\n"
            b"Adventure Graph 0.10.0 is provided for private beta evaluation.\n"
        ),
    }
    files.update(extra_files or {})
    with ZipFile(path, "w") as archive:
        for name, payload in files.items():
            archive.writestr(name, payload)
    return path


def test_beta_wheel_contract_rejects_development_payload(tmp_path: Path) -> None:
    wheel = _minimal_wheel(
        tmp_path / "adventure_graph-0.10.0-py3-none-any.whl",
        extra_files={"adventure_graph/tests/test_hidden.py": b"pass\n"},
    )

    with pytest.raises(RuntimeError, match="development-only payload"):
        _verify_wheel_contract(wheel)


def test_beta_wheel_contract_rejects_additional_adventure_resources(tmp_path: Path) -> None:
    wheel = _minimal_wheel(
        tmp_path / "adventure_graph-0.10.0-py3-none-any.whl",
        extra_files={"adventure_graph/resources/unpolished.adventure.json": b"{}"},
    )

    with pytest.raises(RuntimeError, match="unexpected tester-facing adventure resource set"):
        _verify_wheel_contract(wheel)


def test_beta_wheel_contract_requires_runtime_assets(tmp_path: Path) -> None:
    wheel = _minimal_wheel(tmp_path / "adventure_graph-0.10.0-py3-none-any.whl")
    with ZipFile(wheel, "r") as source:
        retained = {
            name: source.read(name)
            for name in source.namelist()
            if name != "adventure_graph/interfaces/web/assets/app.js"
        }
    with ZipFile(wheel, "w") as destination:
        for name, payload in retained.items():
            destination.writestr(name, payload)

    with pytest.raises(RuntimeError, match="missing required runtime payload"):
        _verify_wheel_contract(wheel)
