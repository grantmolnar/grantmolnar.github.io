"""Local filesystem adapter for one fresh starter project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from adventure_graph.application.project_initialization import ProjectInitializer
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from adventure_graph.infrastructure.adventure_store import adventure_data
from adventure_graph.infrastructure.atomic_files import create_directory, write_json_objects
from adventure_graph.infrastructure.file_transactions import (
    recover_pending_transactions_in_directories,
)
from adventure_graph.infrastructure.play_state_store import play_state_data


@dataclass(frozen=True, slots=True)
class LocalProjectInitializer(ProjectInitializer):
    """Create one complete local project without partially publishing canonical JSON."""

    directory: Path

    def create(self, adventure: Adventure, play_state: PlayState) -> None:
        """Create canonical files together and prepare their auxiliary directories."""
        create_directory(self.directory)
        recover_pending_transactions_in_directories((self.directory,))

        adventure_path = self.directory / "adventure.json"
        state_path = self.directory / "play-state.json"
        occupied = tuple(
            path.name for path in (adventure_path, state_path) if path.exists() or path.is_symlink()
        )
        if occupied:
            names = " or ".join(occupied)
            raise OSError(f"Refusing to overwrite {names}.")

        create_directory(self.directory / "generated")
        create_directory(self.directory / "archives")
        write_json_objects(
            {
                adventure_path: adventure_data(adventure),
                state_path: play_state_data(play_state),
            }
        )
