"""Journal-archive CLI commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from adventure_graph.application.archive_management import (
    ArchiveActiveJournal,
    ArchiveActiveJournalCommand,
    DeleteJournalArchive,
    DeleteJournalArchiveCommand,
    RestoreJournalArchive,
    RestoreJournalArchiveCommand,
)
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.journal_archive_store import load_journal_archive
from adventure_graph.infrastructure.local_journal_archives import LocalJournalArchiveProject


def handle_archive(args: argparse.Namespace) -> int:
    adventure_path = Path(args.adventure)
    state_path = Path(args.state)
    archive_directory = (
        Path(args.archive_dir) if args.archive_dir is not None else state_path.parent / "archives"
    )
    project = LocalJournalArchiveProject(adventure_path, state_path, archive_directory)
    snapshot = project.load()
    result = ArchiveActiveJournal(project).execute(
        ArchiveActiveJournalCommand(
            expected_revision=snapshot.revision,
            label=args.label,
            name=args.name or "",
        )
    )
    archive_path = archive_directory / f"{result.archive_id}.journal.json"
    print(
        f"Archived {result.event_count} event(s) as {result.archive_id} at {archive_path}; "
        f"reset {state_path}."
    )
    return 0


def handle_list_archives(args: argparse.Namespace) -> int:
    directory = Path(args.directory)
    if not directory.exists():
        raise FileNotFoundError(f"Archive directory does not exist: {directory}.")
    if not directory.is_dir():
        raise NotADirectoryError(f"Archive path is not a directory: {directory}.")
    paths = sorted(directory.glob("*.journal.json"))
    if not paths:
        print("No journal archives found.")
        return 0
    print(f"Journal archives ({len(paths)}):")
    for path in paths:
        archive = load_journal_archive(path)
        label = f" — {archive.label}" if archive.label else ""
        print(
            f"- {archive.archive_id}: {archive.adventure_snapshot.title}; "
            f"{archive.event_count} event(s); {archive.archived_at}{label}"
        )
    return 0


def handle_restore_archive(args: argparse.Namespace) -> int:
    adventure_path = Path(args.adventure)
    state_path = Path(args.state)
    archive_path = Path(args.archive)
    adventure = load_adventure(adventure_path)
    archive = load_journal_archive(archive_path)
    project = LocalJournalArchiveProject(adventure_path, state_path, archive_path.parent)
    snapshot = project.load()
    RestoreJournalArchive(project).execute(
        RestoreJournalArchiveCommand(archive.archive_id, snapshot.revision)
    )
    revision_note = (
        " The current adventure differs from the archived snapshot but remains compatible."
        if adventure != archive.adventure_snapshot
        else ""
    )
    print(
        f"Restored archive {archive.archive_id} to {state_path}; retained {archive_path}."
        f"{revision_note}"
    )
    return 0


def handle_delete_archive(args: argparse.Namespace) -> int:
    adventure_path = Path(args.adventure)
    state_path = Path(args.state)
    archive_path = Path(args.archive)
    archive = load_journal_archive(archive_path)
    confirmation = args.confirm
    if confirmation is None:
        try:
            confirmation = input(
                f"Type archive identifier {archive.archive_id!r} to permanently delete it: "
            )
        except EOFError as error:
            raise ValueError("Deletion confirmation was not provided.") from error
    project = LocalJournalArchiveProject(adventure_path, state_path, archive_path.parent)
    snapshot = project.load()
    DeleteJournalArchive(project).execute(
        DeleteJournalArchiveCommand(
            archive_id=archive.archive_id,
            confirmation=confirmation,
            expected_revision=snapshot.revision,
        )
    )
    print(f"Deleted journal archive {archive.archive_id} at {archive_path}.")
    return 0


__all__ = [
    "handle_archive",
    "handle_delete_archive",
    "handle_list_archives",
    "handle_restore_archive",
]
