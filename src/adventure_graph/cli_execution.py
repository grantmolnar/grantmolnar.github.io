"""Registry for parsed Adventure Graph CLI commands."""

from __future__ import annotations

import argparse
from collections.abc import Callable

from adventure_graph.cli_archive_commands import (
    handle_archive,
    handle_delete_archive,
    handle_list_archives,
    handle_restore_archive,
)
from adventure_graph.cli_authoring_commands import (
    handle_add_clue,
    handle_add_encounter,
    handle_add_reference,
    handle_add_revelation,
    handle_edit_clue,
    handle_edit_encounter,
    handle_edit_reference,
    handle_edit_revelation,
    handle_link_reference,
    handle_move_clue,
    handle_remove_clue,
    handle_remove_encounter,
    handle_remove_reference,
    handle_remove_revelation,
    handle_unlink_reference,
)
from adventure_graph.cli_play_commands import (
    handle_consequence,
    handle_correct_latest,
    handle_end_session,
    handle_establish_revelation,
    handle_foreclose_revelation,
    handle_miss_clue,
    handle_note,
    handle_reference_note,
    handle_reopen_revelation,
    handle_spot_clue,
    handle_start_session,
    handle_unlock_encounter,
    handle_visit,
)
from adventure_graph.cli_project_commands import (
    handle_init,
    handle_inspect,
    handle_list,
    handle_render,
    handle_summary,
    handle_validate,
)


def command_handlers() -> dict[str, Callable[[argparse.Namespace], int]]:
    """Return a fresh registry of all non-browser CLI command handlers."""
    return {
        "init": handle_init,
        "archive": handle_archive,
        "start-session": handle_start_session,
        "end-session": handle_end_session,
        "list-archives": handle_list_archives,
        "restore-archive": handle_restore_archive,
        "delete-archive": handle_delete_archive,
        "validate": handle_validate,
        "list": handle_list,
        "inspect": handle_inspect,
        "add-encounter": handle_add_encounter,
        "add-reference": handle_add_reference,
        "add-revelation": handle_add_revelation,
        "add-clue": handle_add_clue,
        "edit-encounter": handle_edit_encounter,
        "edit-reference": handle_edit_reference,
        "edit-revelation": handle_edit_revelation,
        "edit-clue": handle_edit_clue,
        "move-clue": handle_move_clue,
        "link-reference": handle_link_reference,
        "unlink-reference": handle_unlink_reference,
        "remove-encounter": handle_remove_encounter,
        "remove-reference": handle_remove_reference,
        "remove-revelation": handle_remove_revelation,
        "remove-clue": handle_remove_clue,
        "render": handle_render,
        "visit": handle_visit,
        "spot-clue": handle_spot_clue,
        "miss-clue": handle_miss_clue,
        "establish-revelation": handle_establish_revelation,
        "foreclose-revelation": handle_foreclose_revelation,
        "reopen-revelation": handle_reopen_revelation,
        "unlock-encounter": handle_unlock_encounter,
        "consequence": handle_consequence,
        "note": handle_note,
        "reference-note": handle_reference_note,
        "correct-latest": handle_correct_latest,
        "summary": handle_summary,
    }


__all__ = ["command_handlers"]
