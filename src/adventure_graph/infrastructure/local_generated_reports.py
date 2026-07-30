"""Local-file adapter for revision-aware generated report publication."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from adventure_graph.application.play_journal import PlayJournalSnapshot
from adventure_graph.application.project import ProjectRevision, RevisionConflictError
from adventure_graph.infrastructure.atomic_files import write_documents
from adventure_graph.infrastructure.local_path_safety import require_symlink_free_tree
from adventure_graph.infrastructure.local_play_journal import LocalPlayJournalProject


@dataclass(frozen=True, slots=True)
class LocalGeneratedReportProject:
    """Read report source state and publish disposable Markdown documents."""

    journal_project: LocalPlayJournalProject
    output_directory: Path

    @property
    def output_label(self) -> str:
        """Return the configured generated-document directory."""
        return str(self.output_directory)

    def load(self) -> PlayJournalSnapshot:
        """Load current adventure and journal state through the shared local adapter."""
        return self.journal_project.load()

    def publish(
        self,
        documents: Mapping[str, str],
        expected_revision: ProjectRevision,
    ) -> tuple[str, ...]:
        """Write reports only if source files remain at the expected revision."""
        current = self.journal_project.load()
        if current.revision != expected_revision:
            raise RevisionConflictError(
                "The adventure or play journal changed after these reports were loaded; "
                "reload before generating them."
            )
        if self.journal_project.containment_root is not None:
            require_symlink_free_tree(
                self.output_directory,
                self.journal_project.containment_root,
                label="Generated report directory",
            )
        write_documents(self.output_directory, documents)
        return tuple(sorted(documents))
