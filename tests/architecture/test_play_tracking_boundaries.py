"""Guard the command, validation, and projection seams for actual play."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from adventure_graph.application.play_errors import PlayTrackingError as ErrorDefinition
from adventure_graph.application.play_projection import (
    project_play_state as projection_implementation,
)
from adventure_graph.application.play_tracking import (
    PlayTrackingError,
    project_play_state,
)
from tests.support.paths import PACKAGE_ROOT

pytestmark = pytest.mark.architecture

_APPLICATION_ROOT = PACKAGE_ROOT / "application"


def _application_imports(path: Path) -> set[str]:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return {
        encounter.module
        for encounter in ast.walk(module)
        if isinstance(encounter, ast.ImportFrom)
        and encounter.module is not None
        and encounter.module.startswith("adventure_graph.application")
    }


def test_play_tracking_preserves_the_public_facade() -> None:
    assert project_play_state is projection_implementation
    assert PlayTrackingError is ErrorDefinition


def test_projection_and_validation_do_not_depend_on_command_facade() -> None:
    projection_imports = _application_imports(_APPLICATION_ROOT / "play_projection.py")
    validation_imports = _application_imports(_APPLICATION_ROOT / "play_journal_validation.py")

    assert "adventure_graph.application.play_tracking" not in projection_imports
    assert "adventure_graph.application.play_tracking" not in validation_imports
    assert "adventure_graph.application.play_projection" not in validation_imports


def _function_definition(path: Path, function_name: str) -> ast.FunctionDef:
    module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    owner_name, separator, method_name = function_name.partition(".")
    owner = module.body
    if separator:
        class_definition = next(
            (
                encounter
                for encounter in module.body
                if isinstance(encounter, ast.ClassDef) and encounter.name == owner_name
            ),
            None,
        )
        if class_definition is None:
            raise AssertionError(f"Missing class {owner_name!r} in {path}.")
        owner = class_definition.body
        function_name = method_name
    function = next(
        (
            encounter
            for encounter in owner
            if isinstance(encounter, ast.FunctionDef) and encounter.name == function_name
        ),
        None,
    )
    if function is None:
        raise AssertionError(f"Missing function {function_name!r} in {path}.")
    return function


@pytest.mark.parametrize(
    ("relative_path", "function_name"),
    [
        ("application/authoring.py", "_remap_event"),
        ("application/documents.py", "_event_lines"),
        ("application/documents.py", "_recorded_roll_terms"),
        ("application/play_journal.py", "_event_record"),
        ("application/play_journal_validation.py", "_validate_active_journal_shape"),
        ("application/play_projection.py", "_PlayProjectionBuilder.apply"),
        ("application/play_projection.py", "_narrative_record"),
        ("application/play_ledgers.py", "_narrative_entry"),
        ("infrastructure/play_state_store.py", "_play_event_v6_decoder"),
        ("infrastructure/play_state_store.py", "_play_event_data"),
        ("infrastructure/play_state_store.py", "_dice_term_data"),
        ("interfaces/web/journal_rendering.py", "_journal_event_text"),
    ],
)
def test_exhaustive_play_event_consumers_keep_static_never_guards(
    relative_path: str,
    function_name: str,
) -> None:
    """Prevent exhaustive event dispatches from regressing to silent fallthrough."""
    function = _function_definition(PACKAGE_ROOT / relative_path, function_name)
    assert any(
        isinstance(encounter, ast.Call)
        and isinstance(encounter.func, ast.Name)
        and encounter.func.id == "assert_never"
        for encounter in ast.walk(function)
    )


def test_play_projection_owns_mutation_in_one_private_builder() -> None:
    """Keep projection bookkeeping cohesive instead of restoring parallel local state."""
    path = PACKAGE_ROOT / "application" / "play_projection.py"
    text = path.read_text(encoding="utf-8")
    projection = _function_definition(path, "project_play_state")

    assert "class _PlayProjectionBuilder:" in text
    assert "class _VisitBuilder:" in text
    assert "PLR0912" not in ast.get_source_segment(text, projection)
    assert "PLR0915" not in ast.get_source_segment(text, projection)
    assigned_names = [
        target.id
        for encounter in ast.walk(projection)
        if isinstance(encounter, ast.Assign)
        for target in encounter.targets
        if isinstance(target, ast.Name)
    ]
    assert assigned_names == ["builder"]
    for retired_helper in (
        "def _project_visit(",
        "def _project_clue(",
        "def _project_missed_clue(",
        "def _project_revelation(",
        "def _project_foreclosure(",
        "def _project_reopening(",
        "def _project_unlock(",
    ):
        assert retired_helper not in text


def test_derived_event_records_use_the_shared_domain_kind_contract() -> None:
    """Prevent application read models from restoring independent string vocabularies."""
    play_state = (PACKAGE_ROOT / "domain" / "play_state.py").read_text(encoding="utf-8")
    journal = (PACKAGE_ROOT / "application" / "play_journal.py").read_text(encoding="utf-8")
    ledgers = (PACKAGE_ROOT / "application" / "play_ledgers.py").read_text(encoding="utf-8")

    assert "kind: PlayContentEventKind" in play_state
    assert "JournalEventKind: TypeAlias = PlayEventKind" in journal
    assert "kind: PlayContentEventKind" in ledgers


def test_compound_transition_assembles_one_operation_without_rebasing() -> None:
    """Keep atomic transition metadata final at event creation time."""
    path = _APPLICATION_ROOT / "play_tracking.py"
    text = path.read_text(encoding="utf-8")
    transition = _function_definition(path, "transition_visit")
    source = ast.get_source_segment(text, transition) or ""
    called_names = {
        encounter.func.id
        for encounter in ast.walk(transition)
        if isinstance(encounter, ast.Call) and isinstance(encounter.func, ast.Name)
    }

    assert "_PendingPlayOperation" in source
    assert "PLR0912" not in source
    assert "replace" not in called_names
    assert called_names.isdisjoint(
        {
            "add_visit_note",
            "establish_revelation",
            "miss_clue",
            "record_encounter_consequence",
            "record_visit",
            "spot_clue",
        }
    )
    assert "Pending play event has a mismatched operation number." in text
    assert "Pending play event has a noncanonical sequence number." in text
