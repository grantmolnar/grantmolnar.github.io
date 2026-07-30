"""Minimal composition root for the Adventure Graph command-line application."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from adventure_graph.cli_execution import command_handlers
from adventure_graph.infrastructure.local_adventure_workspace import LocalAdventureWorkspace
from adventure_graph.interfaces.cli import parse_args
from adventure_graph.interfaces.web.server import serve_web_app
from adventure_graph.web_composition import compose_workspace_web_application


def main(argv: Sequence[str] | None = None) -> int:
    """Parse and execute one CLI command."""
    return run(parse_args(argv))


def run(args: argparse.Namespace) -> int:
    """Execute one parsed CLI command and return a process status."""
    handlers = command_handlers()
    handlers["ui"] = _handle_ui
    try:
        handler = handlers.get(args.command)
        if handler is None:
            raise ValueError(f"Unknown command {args.command!r}.")
        return handler(args)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


def _handle_ui(args: argparse.Namespace) -> int:
    """Open one workspace or project in the local browser application."""
    target = Path(args.workspace)
    if target.is_file():
        workspace_root = target.parent
        selected_source = target
    else:
        workspace_root = target
        project_source = target / "adventure.json"
        selected_source = project_source if project_source.is_file() else None
    workspace = LocalAdventureWorkspace(workspace_root)
    if selected_source is not None:
        workspace.select_initial_adventure(selected_source)
    serve_web_app(
        compose_workspace_web_application(workspace),
        host=args.host,
        port=args.port,
        open_browser=not args.no_browser,
    )
    return 0


__all__ = ["compose_workspace_web_application", "main", "run"]
