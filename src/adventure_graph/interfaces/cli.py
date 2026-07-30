"""Command-line argument definitions without infrastructure coupling."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from typing import Any, Protocol

from adventure_graph import __version__


class _SubparserFactory(Protocol):
    def add_parser(self, name: str, **_kwargs: Any) -> argparse.ArgumentParser:
        """Create and return one command parser."""
        ...


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse Adventure Graph command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="adventure-graph",
        description="Author, validate, render, and track lead-driven adventure graphs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_project_parsers(subparsers)
    _add_authoring_parsers(subparsers)
    _add_play_parsers(subparsers)
    return parser.parse_args(argv)


def _add_project_parsers(subparsers: _SubparserFactory) -> None:
    init_parser = subparsers.add_parser("init", help="Create an editable example project.")
    init_parser.add_argument("directory")

    ui_parser = subparsers.add_parser("ui", help="Open the local GM web interface.")
    ui_parser.add_argument(
        "workspace",
        help=(
            "Workspace directory to browse, project directory to open, or one canonical "
            "adventure.json to select initially."
        ),
    )
    ui_parser.add_argument("--host", choices=("127.0.0.1", "localhost"), default="127.0.0.1")
    ui_parser.add_argument("--port", type=int, default=8765)
    ui_parser.add_argument("--no-browser", action="store_true")

    validate_parser = subparsers.add_parser("validate", help="Validate an adventure source file.")
    validate_parser.add_argument("adventure")

    render_parser = subparsers.add_parser("render", help="Generate the core Markdown documents.")
    render_parser.add_argument("adventure")
    render_parser.add_argument("output")
    render_parser.add_argument("--state", default=None)

    summary_parser = subparsers.add_parser("summary", help="Generate a current play summary.")
    summary_parser.add_argument("adventure")
    summary_parser.add_argument("state")
    summary_parser.add_argument("--output", default=None)


def _add_authoring_parsers(subparsers: _SubparserFactory) -> None:
    _add_query_parsers(subparsers)
    _add_create_parsers(subparsers)
    _add_edit_parsers(subparsers)
    _add_reference_link_parsers(subparsers)
    _add_remove_parsers(subparsers)


def _add_query_parsers(subparsers: _SubparserFactory) -> None:
    list_parser = subparsers.add_parser(
        "list", help="List authored encounters, references, revelations, or leads."
    )
    list_parser.add_argument("adventure")
    list_parser.add_argument(
        "kind",
        nargs="?",
        choices=("all", "encounter", "reference", "revelation", "clue"),
        default="all",
        help="Authored kind to list; use the stable 'clue' selector for leads.",
    )

    inspect_parser = subparsers.add_parser(
        "inspect", help="Inspect one authored entity and its direct dependencies."
    )
    inspect_parser.add_argument("adventure")
    inspect_parser.add_argument(
        "kind",
        choices=("encounter", "reference", "revelation", "clue"),
        help="Authored kind to inspect; use the stable 'clue' selector for a lead.",
    )
    inspect_parser.add_argument("id")
    inspect_parser.add_argument(
        "--state",
        action="append",
        default=None,
        help=(
            "Related play-state file whose journal blockers should appear; repeat for "
            "multiple journals. When omitted, inspection reads authored data only."
        ),
    )


def _add_create_parsers(subparsers: _SubparserFactory) -> None:
    encounter_parser = subparsers.add_parser(
        "add-encounter", help="Append an encounter to an adventure."
    )
    encounter_parser.add_argument("adventure")
    encounter_parser.add_argument("title")
    encounter_parser.add_argument("--summary", default="")
    encounter_parser.add_argument("--opening-view", default="")
    encounter_parser.add_argument("--content", default="")
    encounter_parser.add_argument("--optional", action="store_true")
    encounter_parser.add_argument("--start", action="store_true")
    encounter_parser.add_argument("--end", action="store_true")
    encounter_parser.add_argument("--tag", action="append", default=[])

    reference_parser = subparsers.add_parser(
        "add-reference", help="Append an adventure-owned reference record."
    )
    reference_parser.add_argument("adventure")
    reference_parser.add_argument(
        "kind", choices=("person", "place", "organization", "object", "other")
    )
    reference_parser.add_argument("title")
    reference_parser.add_argument("--alias", action="append", default=[])
    reference_parser.add_argument("--summary", default="")
    reference_parser.add_argument("--content", default="")
    reference_parser.add_argument("--tag", action="append", default=[])
    _add_related_state_argument(reference_parser)

    revelation_parser = subparsers.add_parser(
        "add-revelation", help="Append a revelation to an adventure."
    )
    revelation_parser.add_argument("adventure")
    revelation_parser.add_argument("title")
    revelation_parser.add_argument("--description", default="")
    revelation_parser.add_argument("--unlocks", default=None)
    revelation_parser.add_argument("--optional", action="store_true")

    clue_parser = subparsers.add_parser("add-clue", help="Append a lead to an adventure.")
    clue_parser.add_argument("adventure")
    clue_parser.add_argument("title")
    clue_parser.add_argument("--source", required=True)
    clue_parser.add_argument("--revelation", required=True)
    clue_parser.add_argument("--description", default="")
    clue_parser.add_argument("--discovery", default="search")


def _add_edit_parsers(subparsers: _SubparserFactory) -> None:
    encounter_parser = subparsers.add_parser(
        "edit-encounter",
        help="Edit encounter fields while preserving its stable identifier.",
    )
    encounter_parser.add_argument("adventure")
    encounter_parser.add_argument("id")
    encounter_parser.add_argument("--title", default=None)
    encounter_parser.add_argument("--summary", default=None)
    encounter_parser.add_argument("--opening-view", default=None)
    encounter_parser.add_argument("--content", default=None)
    required_group = encounter_parser.add_mutually_exclusive_group()
    required_group.add_argument("--necessary", dest="required", action="store_true")
    required_group.add_argument("--optional", dest="required", action="store_false")
    start_group = encounter_parser.add_mutually_exclusive_group()
    start_group.add_argument("--start", dest="start", action="store_true")
    start_group.add_argument("--not-start", dest="start", action="store_false")
    end_group = encounter_parser.add_mutually_exclusive_group()
    end_group.add_argument("--end", dest="end", action="store_true")
    end_group.add_argument("--not-end", dest="end", action="store_false")
    tag_group = encounter_parser.add_mutually_exclusive_group()
    tag_group.add_argument("--tag", action="append", default=None)
    tag_group.add_argument("--clear-tags", action="store_true")
    encounter_parser.set_defaults(required=None, start=None, end=None)
    _add_related_state_argument(encounter_parser)

    reference_parser = subparsers.add_parser(
        "edit-reference",
        help="Edit a reference while preserving its stable UUID identity.",
    )
    reference_parser.add_argument("adventure")
    reference_parser.add_argument("id")
    reference_parser.add_argument(
        "--kind",
        choices=("person", "place", "organization", "object", "other"),
        default=None,
    )
    reference_parser.add_argument("--title", default=None)
    alias_group = reference_parser.add_mutually_exclusive_group()
    alias_group.add_argument("--alias", action="append", default=None)
    alias_group.add_argument("--clear-aliases", action="store_true")
    reference_parser.add_argument("--summary", default=None)
    reference_parser.add_argument("--content", default=None)
    tag_group = reference_parser.add_mutually_exclusive_group()
    tag_group.add_argument("--tag", action="append", default=None)
    tag_group.add_argument("--clear-tags", action="store_true")
    _add_related_state_argument(reference_parser)

    revelation_parser = subparsers.add_parser(
        "edit-revelation",
        help="Edit revelation fields while preserving its stable identifier.",
    )
    revelation_parser.add_argument("adventure")
    revelation_parser.add_argument("id")
    revelation_parser.add_argument("--title", default=None)
    revelation_parser.add_argument("--description", default=None)
    unlock_group = revelation_parser.add_mutually_exclusive_group()
    unlock_group.add_argument("--unlocks", default=None)
    unlock_group.add_argument("--clear-unlocks", action="store_true")
    required_group = revelation_parser.add_mutually_exclusive_group()
    required_group.add_argument("--required", dest="required", action="store_true")
    required_group.add_argument("--optional", dest="required", action="store_false")
    revelation_parser.set_defaults(required=None)
    _add_related_state_argument(revelation_parser)

    clue_parser = subparsers.add_parser(
        "edit-clue", help="Edit lead fields while preserving its stable identifier."
    )
    clue_parser.add_argument("adventure")
    clue_parser.add_argument("id")
    clue_parser.add_argument("--title", default=None)
    clue_parser.add_argument("--revelation", default=None)
    clue_parser.add_argument("--description", default=None)
    clue_parser.add_argument("--discovery", default=None)
    _add_related_state_argument(clue_parser)

    move_parser = subparsers.add_parser(
        "move-clue", help="Move a lead to a different source encounter."
    )
    move_parser.add_argument("adventure")
    move_parser.add_argument("id")
    move_parser.add_argument("source")
    _add_related_state_argument(move_parser)


def _add_reference_link_parsers(subparsers: _SubparserFactory) -> None:
    link_parser = subparsers.add_parser(
        "link-reference", help="Append one contextual reference link to an encounter."
    )
    link_parser.add_argument("adventure")
    link_parser.add_argument("encounter")
    link_parser.add_argument("reference")
    link_parser.add_argument("--context", default="")
    _add_related_state_argument(link_parser)

    unlink_parser = subparsers.add_parser(
        "unlink-reference", help="Remove one encounter/reference link."
    )
    unlink_parser.add_argument("adventure")
    unlink_parser.add_argument("encounter")
    unlink_parser.add_argument("reference")
    _add_related_state_argument(unlink_parser)


def _add_remove_parsers(subparsers: _SubparserFactory) -> None:
    encounter_parser = subparsers.add_parser(
        "remove-encounter", help="Remove an encounter with dependency-aware refusal by default."
    )
    encounter_parser.add_argument("adventure")
    encounter_parser.add_argument("id")
    encounter_parser.add_argument("--cascade", action="store_true")
    _add_related_state_argument(encounter_parser)

    reference_parser = subparsers.add_parser(
        "remove-reference", help="Remove a reference with dependency-aware refusal by default."
    )
    reference_parser.add_argument("adventure")
    reference_parser.add_argument("id")
    reference_parser.add_argument("--cascade", action="store_true")
    _add_related_state_argument(reference_parser)

    revelation_parser = subparsers.add_parser(
        "remove-revelation",
        help="Remove a revelation with dependency-aware refusal by default.",
    )
    revelation_parser.add_argument("adventure")
    revelation_parser.add_argument("id")
    revelation_parser.add_argument("--cascade", action="store_true")
    _add_related_state_argument(revelation_parser)

    clue_parser = subparsers.add_parser("remove-clue", help="Remove one authored lead.")
    clue_parser.add_argument("adventure")
    clue_parser.add_argument("id")
    _add_related_state_argument(clue_parser)


def _add_related_state_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--state",
        action="append",
        default=None,
        help=(
            "Related play-state file to validate or rewrite; repeat for multiple journals. "
            "When omitted, the canonical companion journal is used if present."
        ),
    )


def _add_play_parsers(subparsers: _SubparserFactory) -> None:
    _add_archive_parsers(subparsers)
    _add_session_parsers(subparsers)
    _add_visit_parsers(subparsers)
    _add_progress_parsers(subparsers)
    _add_annotation_parsers(subparsers)
    _add_correction_parser(subparsers)


def _add_session_parsers(subparsers: _SubparserFactory) -> None:
    start_parser = subparsers.add_parser(
        "start-session", help="Begin the next explicit play session."
    )
    start_parser.add_argument("adventure")
    start_parser.add_argument("state")
    start_parser.add_argument("--title", default="")
    start_parser.add_argument("--played-on", default=None)
    start_parser.add_argument("--participant", action="append", default=[])
    start_parser.add_argument("--attendance-note", default="")
    start_parser.add_argument("--opening-note", default="")

    end_parser = subparsers.add_parser(
        "end-session", help="End the currently active explicit play session."
    )
    end_parser.add_argument("adventure")
    end_parser.add_argument("state")
    end_parser.add_argument("--closing-note", default="")


def _add_archive_parsers(subparsers: _SubparserFactory) -> None:
    archive_parser = subparsers.add_parser(
        "archive", help="Archive the active play journal and replace it with an empty journal."
    )
    archive_parser.add_argument("adventure")
    archive_parser.add_argument("state")
    archive_parser.add_argument("--archive-dir", default=None)
    archive_parser.add_argument(
        "--name",
        default=None,
        help="portable archive identifier (up to 80 ASCII filename-safe characters)",
    )
    archive_parser.add_argument("--label", default="")

    list_parser = subparsers.add_parser(
        "list-archives", help="List journal archives in one directory."
    )
    list_parser.add_argument("directory")

    restore_archive_parser = subparsers.add_parser(
        "restore-archive",
        help="Restore one journal archive into an empty active journal without deleting it.",
    )
    restore_archive_parser.add_argument("adventure")
    restore_archive_parser.add_argument("state")
    restore_archive_parser.add_argument("archive")

    delete_parser = subparsers.add_parser(
        "delete-archive",
        help="Permanently delete one project journal archive after exact confirmation.",
    )
    delete_parser.add_argument("adventure")
    delete_parser.add_argument("state")
    delete_parser.add_argument("archive")
    delete_parser.add_argument(
        "--confirm",
        default=None,
        help="Exact archive identifier; when omitted, the command prompts for it.",
    )


def _add_visit_parsers(subparsers: _SubparserFactory) -> None:
    visit_parser = subparsers.add_parser(
        "visit", help="Record an encounter visit and optional lead/note events."
    )
    visit_parser.add_argument("adventure")
    visit_parser.add_argument("state")
    visit_parser.add_argument("encounter")
    visit_parser.add_argument(
        "--clue",
        action="append",
        default=[],
        metavar="LEAD_ID",
        help="Lead identifier; repeat for multiple leads found during this visit.",
    )
    visit_parser.add_argument("--note", action="append", default=[])
    visit_parser.add_argument("--party", default="")

    spot_parser = subparsers.add_parser("spot-clue", help="Record a lead first spotted in play.")
    spot_parser.add_argument("adventure")
    spot_parser.add_argument("state")
    spot_parser.add_argument("clue", metavar="lead")
    spot_parser.add_argument("--visit", type=int, default=None)

    miss_parser = subparsers.add_parser(
        "miss-clue", help="Record one missed lead opportunity during a visit."
    )
    miss_parser.add_argument("adventure")
    miss_parser.add_argument("state")
    miss_parser.add_argument("clue", metavar="lead")
    miss_parser.add_argument("--visit", type=int, default=None)


def _add_progress_parsers(subparsers: _SubparserFactory) -> None:
    establish_parser = subparsers.add_parser(
        "establish-revelation", help="Record that the players established a revelation."
    )
    establish_parser.add_argument("adventure")
    establish_parser.add_argument("state")
    establish_parser.add_argument("revelation")
    establish_parser.add_argument(
        "--clue",
        action="append",
        default=[],
        metavar="LEAD_ID",
        help="Supporting lead identifier; repeat for multiple leads.",
    )
    establish_parser.add_argument("--note", default="")

    foreclose_parser = subparsers.add_parser(
        "foreclose-revelation",
        help="Record that one revelation is no longer establishable.",
    )
    foreclose_parser.add_argument("adventure")
    foreclose_parser.add_argument("state")
    foreclose_parser.add_argument("revelation")
    foreclose_parser.add_argument("--reason", required=True)

    reopen_parser = subparsers.add_parser(
        "reopen-revelation",
        help="Reverse an active revelation foreclosure with a reason.",
    )
    reopen_parser.add_argument("adventure")
    reopen_parser.add_argument("state")
    reopen_parser.add_argument("revelation")
    reopen_parser.add_argument("--reason", required=True)

    unlock_parser = subparsers.add_parser(
        "unlock-encounter", help="Make an encounter available by explicit GM adjudication."
    )
    unlock_parser.add_argument("adventure")
    unlock_parser.add_argument("state")
    unlock_parser.add_argument("encounter")
    unlock_parser.add_argument("--reason", required=True)


def _add_correction_parser(subparsers: _SubparserFactory) -> None:
    parser = subparsers.add_parser(
        "correct-latest",
        help="Append a correction voiding the latest still-active play operation.",
    )
    parser.add_argument("adventure")
    parser.add_argument("state")
    parser.add_argument("--reason", required=True)


def _add_annotation_parsers(subparsers: _SubparserFactory) -> None:
    consequence_parser = subparsers.add_parser(
        "consequence", help="Record a lasting change affecting one encounter."
    )
    consequence_parser.add_argument("adventure")
    consequence_parser.add_argument("state")
    consequence_parser.add_argument("encounter")
    consequence_parser.add_argument("text")

    note_parser = subparsers.add_parser(
        "note", help="Append a revision-checked note to an existing visit."
    )
    note_parser.add_argument("adventure")
    note_parser.add_argument("state")
    note_parser.add_argument("visit", type=int)
    note_parser.add_argument("text")

    reference_note_parser = subparsers.add_parser(
        "reference-note",
        help="Append a chronological play note to a persistent authored reference.",
    )
    reference_note_parser.add_argument("adventure")
    reference_note_parser.add_argument("state")
    reference_note_parser.add_argument("reference")
    reference_note_parser.add_argument("text")
