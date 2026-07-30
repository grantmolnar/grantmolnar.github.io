"""Authored-graph mutation CLI commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from adventure_graph.application.authoring import (
    remove_clue,
    remove_revelation,
    revelation_dependencies,
)
from adventure_graph.application.encounter_authoring import (
    GetEncounterDetail,
    RemoveEncounter,
    RemoveEncounterCommand,
    UpdateEncounter,
    UpdateEncounterCommand,
)
from adventure_graph.application.project import AuthoringProject, AuthoringSnapshot
from adventure_graph.application.project_browsing import GetClueDetail, GetRevelationDetail
from adventure_graph.application.project_integrity import validate_related_play_states
from adventure_graph.application.reference_authoring import (
    CreateReference,
    CreateReferenceCommand,
    GetReferenceDetail,
    LinkReference,
    LinkReferenceCommand,
    RemoveReference,
    RemoveReferenceCommand,
    UnlinkReference,
    UnlinkReferenceCommand,
    UpdateReference,
    UpdateReferenceCommand,
)
from adventure_graph.application.structural_authoring import (
    CreateClue,
    CreateClueCommand,
    CreateEncounter,
    CreateEncounterCommand,
    CreateRevelation,
    CreateRevelationCommand,
    UpdateClue,
    UpdateClueCommand,
    UpdateRevelation,
    UpdateRevelationCommand,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.infrastructure.local_authoring_project import LocalAuthoringProject


def handle_add_encounter(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    snapshot = project.load()
    result = CreateEncounter(project).execute(
        CreateEncounterCommand(
            expected_revision=snapshot.revision,
            title=args.title,
            summary=args.summary,
            opening_view=args.opening_view,
            content=args.content,
            required=not args.optional,
            start=args.start,
            end=args.end,
            tags=tuple(args.tag),
        )
    )
    print(f"Added encounter {result.encounter.title}.")
    return 0


def handle_add_reference(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    snapshot = project.load()
    result = CreateReference(project).execute(
        CreateReferenceCommand(
            expected_revision=snapshot.revision,
            kind=args.kind,
            title=args.title,
            aliases=tuple(args.alias),
            summary=args.summary,
            content=args.content,
            tags=tuple(args.tag),
        )
    )
    print(f"Added reference {result.reference.title} ({result.reference.id}).")
    return 0


def handle_add_revelation(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    snapshot = project.load()
    result = CreateRevelation(project).execute(
        CreateRevelationCommand(
            expected_revision=snapshot.revision,
            title=args.title,
            description=args.description,
            unlocks_encounter_id=args.unlocks,
            required=not args.optional,
        )
    )
    print(f"Added revelation {result.revelation.title}.")
    return 0


def handle_add_clue(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    snapshot = project.load()
    result = CreateClue(project).execute(
        CreateClueCommand(
            expected_revision=snapshot.revision,
            title=args.title,
            source_encounter_id=args.source,
            revelation_id=args.revelation,
            description=args.description,
            discovery=args.discovery,
        )
    )
    print(f"Added lead {result.clue.title}.")
    return 0


def handle_edit_encounter(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    detail = GetEncounterDetail(project).execute(args.id)
    tags = () if args.clear_tags else tuple(args.tag) if args.tag is not None else None
    UpdateEncounter(project).execute(
        UpdateEncounterCommand(
            encounter_id=args.id,
            expected_revision=detail.revision,
            title=args.title,
            summary=args.summary,
            opening_view=args.opening_view,
            content=args.content,
            required=args.required,
            start=args.start,
            end=args.end,
            tags=tags,
        )
    )
    print(f"Updated encounter {args.id}.")
    return 0


def handle_edit_reference(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    detail = GetReferenceDetail(project).execute(args.id)
    before = detail.detail.reference
    aliases = (
        ()
        if args.clear_aliases
        else tuple(args.alias)
        if args.alias is not None
        else before.aliases
    )
    tags = () if args.clear_tags else tuple(args.tag) if args.tag is not None else before.tags
    result = UpdateReference(project).execute(
        UpdateReferenceCommand(
            reference_id=before.id,
            expected_revision=detail.revision,
            kind=args.kind if args.kind is not None else before.kind,
            title=args.title if args.title is not None else before.title,
            aliases=aliases,
            summary=args.summary if args.summary is not None else before.summary,
            content=args.content if args.content is not None else before.content,
            tags=tags,
        )
    )
    print(f"Updated reference {result.after.title} ({result.after.id}).")
    return 0


def handle_edit_revelation(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    detail = GetRevelationDetail(project).execute(args.id)
    before = detail.detail.revelation
    unlocks_encounter_id = before.unlocks_encounter_id
    if args.clear_unlocks:
        unlocks_encounter_id = None
    elif args.unlocks is not None:
        unlocks_encounter_id = args.unlocks
    result = UpdateRevelation(project).execute(
        UpdateRevelationCommand(
            revelation_id=before.id,
            expected_revision=detail.revision,
            title=args.title if args.title is not None else before.title,
            description=(args.description if args.description is not None else before.description),
            unlocks_encounter_id=unlocks_encounter_id,
            required=args.required if args.required is not None else before.required,
        )
    )
    print(f"Updated revelation {result.after.title}.")
    return 0


def handle_edit_clue(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    detail = GetClueDetail(project).execute(args.id)
    before = detail.detail.clue
    result = UpdateClue(project).execute(
        UpdateClueCommand(
            clue_id=before.id,
            expected_revision=detail.revision,
            title=args.title if args.title is not None else before.title,
            source_encounter_id=before.source_encounter_id,
            revelation_id=(
                args.revelation if args.revelation is not None else before.revelation_id
            ),
            description=args.description if args.description is not None else before.description,
            discovery=args.discovery if args.discovery is not None else before.discovery,
        )
    )
    print(f"Updated lead {result.after.title}.")
    return 0


def handle_move_clue(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    detail = GetClueDetail(project).execute(args.id)
    before = detail.detail.clue
    UpdateClue(project).execute(
        UpdateClueCommand(
            clue_id=before.id,
            expected_revision=detail.revision,
            title=before.title,
            source_encounter_id=args.source,
            revelation_id=before.revelation_id,
            description=before.description,
            discovery=before.discovery,
        )
    )
    print(f"Moved lead {before.id} to encounter {args.source}.")
    return 0


def handle_link_reference(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    snapshot = project.load()
    result = LinkReference(project).execute(
        LinkReferenceCommand(
            encounter_id=args.encounter,
            reference_id=args.reference,
            expected_revision=snapshot.revision,
            context=args.context,
        )
    )
    print(f"Linked reference {result.link.reference_id} to encounter {result.encounter.id}.")
    return 0


def handle_unlink_reference(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    snapshot = project.load()
    result = UnlinkReference(project).execute(
        UnlinkReferenceCommand(
            encounter_id=args.encounter,
            reference_id=args.reference,
            expected_revision=snapshot.revision,
        )
    )
    print(
        f"Unlinked reference {result.removed_link.reference_id} from encounter "
        f"{result.encounter.id}."
    )
    return 0


def handle_remove_encounter(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    snapshot = project.load()
    result = RemoveEncounter(project).execute(
        RemoveEncounterCommand(
            encounter_id=args.id,
            expected_revision=snapshot.revision,
            cascade=args.cascade,
        )
    )
    print(f"Removed encounter {args.id}.")
    if args.cascade:
        dependencies = result.dependencies
        print(
            f"Cascade removed {len(dependencies.source_clue_ids)} source lead(s), cleared "
            f"{len(dependencies.unlocking_revelation_ids)} revelation destination(s), and "
            f"discarded {len(dependencies.linked_reference_ids)} reference link(s)."
        )
    return 0


def handle_remove_reference(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    snapshot = project.load()
    result = RemoveReference(project).execute(
        RemoveReferenceCommand(
            reference_id=args.id,
            expected_revision=snapshot.revision,
            cascade=args.cascade,
        )
    )
    print(f"Removed reference {result.reference.title} ({result.reference.id}).")
    if args.cascade:
        print(f"Cascade removed {len(result.dependencies.links)} encounter link(s).")
    return 0


def handle_remove_revelation(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    snapshot = project.load()
    dependencies = revelation_dependencies(snapshot.adventure, args.id)
    updated = remove_revelation(snapshot.adventure, args.id, cascade=args.cascade)
    _commit_adventure(project, snapshot, updated)
    print(f"Removed revelation {args.id}.")
    if args.cascade:
        print(f"Cascade removed {len(dependencies.supporting_clue_ids)} supporting lead(s).")
    return 0


def handle_remove_clue(args: argparse.Namespace) -> int:
    project = _authoring_project(args)
    snapshot = project.load()
    updated = remove_clue(snapshot.adventure, args.id)
    _commit_adventure(project, snapshot, updated)
    print(f"Removed lead {args.id}.")
    return 0


def _commit_adventure(
    project: AuthoringProject,
    snapshot: AuthoringSnapshot,
    adventure: Adventure,
) -> None:
    validate_related_play_states(adventure, snapshot.related_play_states)
    project.commit_adventure(adventure, snapshot.revision)


def _authoring_project(args: argparse.Namespace) -> LocalAuthoringProject:
    state_arguments = getattr(args, "state", None)
    state_paths = None if state_arguments is None else tuple(Path(item) for item in state_arguments)
    return LocalAuthoringProject(Path(args.adventure), state_paths)


__all__ = [
    "handle_add_clue",
    "handle_add_encounter",
    "handle_add_reference",
    "handle_add_revelation",
    "handle_edit_clue",
    "handle_edit_encounter",
    "handle_edit_reference",
    "handle_edit_revelation",
    "handle_link_reference",
    "handle_move_clue",
    "handle_remove_clue",
    "handle_remove_encounter",
    "handle_remove_reference",
    "handle_remove_revelation",
    "handle_unlink_reference",
]
