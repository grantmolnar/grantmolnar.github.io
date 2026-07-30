"""Revision-aware local-file adapter for one active play journal."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from adventure_graph.application.play_journal import PlayJournalSnapshot
from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.application.project import ProjectRevision, RevisionConflictError
from adventure_graph.domain.play_state import PlayState
from adventure_graph.infrastructure.adventure_store import adventure_from_data
from adventure_graph.infrastructure.file_transactions import recover_pending_transactions
from adventure_graph.infrastructure.json_values import (
    decode_object_bytes,
    read_json_document_bytes,
)
from adventure_graph.infrastructure.local_path_safety import require_contained_file
from adventure_graph.infrastructure.play_state_store import play_state_from_data, save_play_state
from adventure_graph.infrastructure.revision_bytes import framed_sha256_hexdigest

_MISSING_STATE = b"<missing-play-state>"


@dataclass(frozen=True, slots=True)
class LocalPlayJournalProject:
    """Load and conditionally commit a sibling local play journal."""

    adventure_path: Path
    state_path: Path
    containment_root: Path | None = None

    def load(self) -> PlayJournalSnapshot:
        """Load the adventure, active journal, and revision from one byte snapshot."""
        adventure_payload, state_payload = self._read_payloads()
        adventure = adventure_from_data(decode_object_bytes(adventure_payload, self.adventure_path))
        state = (
            new_play_state(adventure)
            if state_payload == _MISSING_STATE
            else play_state_from_data(decode_object_bytes(state_payload, self.state_path))
        )
        return PlayJournalSnapshot(
            adventure=adventure,
            state=state,
            revision=_revision(
                self.adventure_path,
                adventure_payload,
                self.state_path,
                state_payload,
            ),
        )

    def commit_state(
        self,
        state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Commit only if neither adventure nor active journal changed after loading."""
        adventure_payload, state_payload = self._read_payloads()
        current_revision = _revision(
            self.adventure_path,
            adventure_payload,
            self.state_path,
            state_payload,
        )
        if current_revision != expected_revision:
            raise RevisionConflictError(
                "The adventure or play journal changed after this history was loaded; "
                "reload before correcting it."
            )
        save_play_state(self.state_path, state)
        committed_adventure, committed_state = self._read_payloads()
        return _revision(
            self.adventure_path,
            committed_adventure,
            self.state_path,
            committed_state,
        )

    def _read_payloads(self) -> tuple[bytes, bytes]:
        if self.containment_root is not None:
            require_contained_file(
                self.adventure_path,
                self.containment_root,
                label="Adventure source",
            )
            require_contained_file(
                self.state_path,
                self.containment_root,
                allow_missing=True,
                label="Active play journal",
            )
        recover_pending_transactions(
            (self.adventure_path, self.state_path),
            containment_root=self.containment_root,
        )
        adventure_payload = read_json_document_bytes(self.adventure_path, recover=False)
        state_payload = (
            read_json_document_bytes(self.state_path, recover=False)
            if self.state_path.exists()
            else _MISSING_STATE
        )
        return adventure_payload, state_payload


def _revision(
    adventure_path: Path,
    adventure_payload: bytes,
    state_path: Path,
    state_payload: bytes,
) -> ProjectRevision:
    sources = sorted(
        (
            (str(adventure_path.resolve()), adventure_payload),
            (str(state_path.resolve()), state_payload),
        ),
        key=lambda item: item[0],
    )
    return ProjectRevision(framed_sha256_hexdigest(sources))
