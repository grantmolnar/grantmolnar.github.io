"""Project initialization, inspection, validation, and document CLI commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from adventure_graph.application.documents import (
    render_adventure_documents,
    render_play_summary,
)
from adventure_graph.application.encounter_authoring import GetEncounterDetail
from adventure_graph.application.project_initialization import InitializeStarterProject
from adventure_graph.application.reference_authoring import GetReferenceDetail
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.atomic_files import write_documents
from adventure_graph.infrastructure.bundled_adventures import load_glass_saint_template
from adventure_graph.infrastructure.local_authoring_project import LocalAuthoringProject
from adventure_graph.infrastructure.local_project_initializer import LocalProjectInitializer
from adventure_graph.infrastructure.play_state_store import load_play_state
from adventure_graph.interfaces.presentation import (
    print_encounter_detail,
    print_entity_inspection,
    print_entity_list,
    print_reference_detail,
    print_validation_report,
)


def handle_init(args: argparse.Namespace) -> int:
    return _init(Path(args.directory))


def handle_validate(args: argparse.Namespace) -> int:
    report = validate_adventure(load_adventure(Path(args.adventure)))
    return print_validation_report(report)


def handle_list(args: argparse.Namespace) -> int:
    print_entity_list(load_adventure(Path(args.adventure)), args.kind)
    return 0


def handle_inspect(args: argparse.Namespace) -> int:
    if args.kind in {"encounter", "reference"}:
        state_paths = tuple(Path(item) for item in args.state) if args.state else ()
        project = LocalAuthoringProject(Path(args.adventure), state_paths)
        if args.kind == "encounter":
            print_encounter_detail(GetEncounterDetail(project).execute(args.id).detail)
        else:
            print_reference_detail(GetReferenceDetail(project).execute(args.id).detail)
    else:
        print_entity_inspection(load_adventure(Path(args.adventure)), args.kind, args.id)
    return 0


def handle_render(args: argparse.Namespace) -> int:
    state = load_play_state(Path(args.state)) if args.state else None
    adventure = load_adventure(Path(args.adventure))
    report = validate_adventure(adventure)
    write_documents(Path(args.output), render_adventure_documents(adventure, report, state))
    print(f"Wrote documents to {args.output}.")
    return 0 if report.is_valid else 1


def handle_summary(args: argparse.Namespace) -> int:
    adventure = load_adventure(Path(args.adventure))
    summary = render_play_summary(adventure, load_play_state(Path(args.state)))
    if args.output:
        Path(args.output).write_text(summary, encoding="utf-8")
    else:
        print(summary)
    return 0


def _init(directory: Path) -> int:
    starter = load_glass_saint_template()
    result = InitializeStarterProject(LocalProjectInitializer(directory), starter).execute()
    adventure_path = directory / "adventure.json"
    state_path = directory / "play-state.json"
    print(f"Created {adventure_path} and {state_path} with adventure id {result.adventure.id}.")
    return 0


__all__ = [
    "handle_init",
    "handle_inspect",
    "handle_list",
    "handle_render",
    "handle_summary",
    "handle_validate",
]
