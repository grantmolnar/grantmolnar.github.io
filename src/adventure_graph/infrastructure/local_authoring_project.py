"""Revision-aware local-file adapter for authored project workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from adventure_graph.application.project import (
    AuthoringSnapshot,
    ProjectRevision,
    RelatedPlayState,
    RevisionConflictError,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.infrastructure.adventure_store import adventure_from_data, save_adventure
from adventure_graph.infrastructure.authoring_store import save_authoring_bundle
from adventure_graph.infrastructure.file_transactions import recover_pending_transactions
from adventure_graph.infrastructure.json_values import (
    decode_object_bytes,
    read_json_document_bytes,
)
from adventure_graph.infrastructure.local_path_safety import require_contained_file
from adventure_graph.infrastructure.local_project_paths import local_project_paths
from adventure_graph.infrastructure.play_state_store import play_state_from_data
from adventure_graph.infrastructure.revision_bytes import framed_sha256_hexdigest


@dataclass(frozen=True, slots=True)
class LocalAuthoringProject:
    """Load and conditionally commit one adventure and its related local journals."""

    adventure_path: Path
    explicit_state_paths: tuple[Path, ...] | None = None
    containment_root: Path | None = None

    def __post_init__(self) -> None:
        if self.explicit_state_paths is None:
            return
        if len(set(self.explicit_state_paths)) != len(self.explicit_state_paths):
            raise ValueError("A related play-state path was supplied more than once.")

    def load(self) -> AuthoringSnapshot:
        """Load the adventure, related journals, and a revision from the same bytes."""
        state_paths, payloads = self._read_payloads()
        adventure = adventure_from_data(
            decode_object_bytes(payloads[self.adventure_path], self.adventure_path)
        )
        related_play_states = tuple(
            RelatedPlayState(
                source=str(path),
                state=play_state_from_data(decode_object_bytes(payloads[path], path)),
            )
            for path in state_paths
        )
        return AuthoringSnapshot(
            adventure=adventure,
            related_play_states=related_play_states,
            revision=_revision(payloads),
        )

    def commit_adventure(
        self,
        adventure: Adventure,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Commit only if no authored or related journal file changed since loading."""
        _, current_payloads = self._read_payloads()
        current_revision = _revision(current_payloads)
        if current_revision != expected_revision:
            raise RevisionConflictError(
                "The project changed after this encounter was loaded; reload before saving."
            )
        save_adventure(self.adventure_path, adventure)
        _, committed_payloads = self._read_payloads()
        return _revision(committed_payloads)

    def commit_authoring(
        self,
        adventure: Adventure,
        related_play_states: tuple[RelatedPlayState, ...],
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Commit an adventure and a complete set of rewritten related journals."""
        state_paths, current_payloads = self._read_payloads()
        current_revision = _revision(current_payloads)
        if current_revision != expected_revision:
            raise RevisionConflictError(
                "The project changed after this encounter was loaded; reload before saving."
            )
        supplied = {Path(related.source): related.state for related in related_play_states}
        if set(supplied) != set(state_paths):
            raise ValueError(
                "The rewritten journal set does not match the loaded project snapshot."
            )
        save_authoring_bundle(self.adventure_path, adventure, supplied)
        _, committed_payloads = self._read_payloads()
        return _revision(committed_payloads)

    def _read_payloads(self) -> tuple[tuple[Path, ...], dict[Path, bytes]]:
        state_paths = self._state_paths()
        paths = (self.adventure_path, *state_paths)
        if self.containment_root is not None:
            require_contained_file(
                self.adventure_path,
                self.containment_root,
                label="Adventure source",
            )
            for state_path in state_paths:
                require_contained_file(
                    state_path,
                    self.containment_root,
                    allow_missing=False,
                    label="Related play journal",
                )
        recover_pending_transactions(paths, containment_root=self.containment_root)
        return state_paths, {path: read_json_document_bytes(path, recover=False) for path in paths}

    def _state_paths(self) -> tuple[Path, ...]:
        if self.explicit_state_paths is not None:
            return self.explicit_state_paths
        companion = local_project_paths(self.adventure_path).play_state
        return (companion,) if companion.exists() else ()


def _revision(payloads: dict[Path, bytes]) -> ProjectRevision:
    sources = sorted((str(path.resolve()), content) for path, content in payloads.items())
    return ProjectRevision(framed_sha256_hexdigest(sources))
