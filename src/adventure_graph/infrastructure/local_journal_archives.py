"""Local-file adapter for revision-aware journal archive management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from adventure_graph.application.archive_management import (
    JournalArchiveCatalogSnapshot,
    JournalArchiveSnapshot,
    validate_archive_identity_set,
)
from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.application.project import ProjectRevision, RevisionConflictError
from adventure_graph.domain.play_state import PlayState
from adventure_graph.infrastructure.adventure_store import adventure_from_data
from adventure_graph.infrastructure.file_transactions import (
    recover_pending_transactions_in_directories,
)
from adventure_graph.infrastructure.journal_archive_store import (
    canonical_archive_filename,
    delete_journal_archive,
    journal_archive_from_data,
    require_canonical_archive_path,
    restore_journal_archive,
    save_archive_and_reset,
    save_journal_archive,
)
from adventure_graph.infrastructure.json_values import (
    decode_object_bytes,
    read_json_document_bytes,
)
from adventure_graph.infrastructure.local_path_safety import (
    require_contained_directory,
    require_contained_file,
    require_symlink_free_tree,
)
from adventure_graph.infrastructure.play_state_store import play_state_from_data
from adventure_graph.infrastructure.revision_bytes import framed_sha256_hexdigest

_MISSING_STATE = b"<missing-play-state>"
_MISSING_DIRECTORY = b"<missing-archive-directory>"


@dataclass(frozen=True, slots=True)
class _ArchivePayloadSnapshot:
    adventure_payload: bytes
    active_state_payload: bytes
    archive_payloads: tuple[tuple[Path, bytes], ...]
    archive_directory_exists: bool


@dataclass(frozen=True, slots=True)
class LocalJournalArchiveProject:
    """Manage one active local journal and its sibling archive directory."""

    adventure_path: Path
    state_path: Path
    archive_directory: Path
    containment_root: Path | None = None

    def load(self) -> JournalArchiveCatalogSnapshot:
        """Load current source state, all archives, and one same-byte revision."""
        payloads = self._read_payloads()
        adventure = adventure_from_data(
            decode_object_bytes(payloads.adventure_payload, self.adventure_path)
        )
        active_state = (
            new_play_state(adventure)
            if payloads.active_state_payload == _MISSING_STATE
            else play_state_from_data(
                decode_object_bytes(payloads.active_state_payload, self.state_path)
            )
        )
        archives = tuple(
            self._decode_archive(path, payload) for path, payload in payloads.archive_payloads
        )
        validate_archive_identity_set(archives)
        return JournalArchiveCatalogSnapshot(
            adventure=adventure,
            active_state=active_state,
            archives=archives,
            source_state_name=self.state_path.name,
            revision=self._revision(payloads),
        )

    def create_and_reset(
        self,
        archive: JournalArchiveSnapshot,
        empty_state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Create an archive and reset the active journal after a revision check."""
        self._require_revision(expected_revision)
        path = self.archive_directory / canonical_archive_filename(archive.archive_id)
        save_archive_and_reset(path, archive, self.state_path, empty_state)
        return self._revision(self._read_payloads())

    def restore(
        self,
        archive_id: str,
        restored_state: PlayState,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Restore one archive without modifying it after a revision check."""
        payloads = self._require_revision(expected_revision)
        path = self._path_for_id(archive_id, payloads.archive_payloads)
        restore_journal_archive(path, self.state_path, restored_state)
        return self._revision(self._read_payloads())

    def delete(self, archive_id: str, expected_revision: ProjectRevision) -> ProjectRevision:
        """Permanently remove one archive after a revision check."""
        payloads = self._require_revision(expected_revision)
        delete_journal_archive(self._path_for_id(archive_id, payloads.archive_payloads))
        return self._revision(self._read_payloads())

    def import_archive(
        self,
        archive: JournalArchiveSnapshot,
        expected_revision: ProjectRevision,
    ) -> ProjectRevision:
        """Persist one validated external archive after a revision check."""
        self._require_revision(expected_revision)
        path = self.archive_directory / canonical_archive_filename(archive.archive_id)
        if self.containment_root is not None:
            require_contained_file(
                path,
                self.containment_root,
                allow_missing=True,
                label="Imported journal archive",
            )
        save_journal_archive(path, archive)
        return self._revision(self._read_payloads())

    def _require_revision(
        self,
        expected_revision: ProjectRevision,
    ) -> _ArchivePayloadSnapshot:
        payloads = self._read_payloads()
        if self._revision(payloads) != expected_revision:
            raise RevisionConflictError(
                "The adventure, active journal, or archive catalog changed after this page loaded; "
                "reload before modifying archives."
            )
        return payloads

    def _read_payloads(self) -> _ArchivePayloadSnapshot:
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
            require_contained_directory(
                self.archive_directory,
                self.containment_root,
                allow_missing=True,
                label="Journal archive directory",
            )
            require_symlink_free_tree(
                self.archive_directory,
                self.containment_root,
                label="Journal archive directory",
            )
        recover_pending_transactions_in_directories(
            (self.adventure_path.parent, self.state_path.parent, self.archive_directory),
            containment_root=self.containment_root,
        )
        archive_directory_exists = self.archive_directory.exists()
        archive_paths = (
            tuple(sorted(self.archive_directory.glob("*.journal.json")))
            if archive_directory_exists
            else ()
        )
        return _ArchivePayloadSnapshot(
            adventure_payload=read_json_document_bytes(self.adventure_path, recover=False),
            active_state_payload=(
                read_json_document_bytes(self.state_path, recover=False)
                if self.state_path.exists()
                else _MISSING_STATE
            ),
            archive_payloads=tuple(
                (path, read_json_document_bytes(path, recover=False)) for path in archive_paths
            ),
            archive_directory_exists=archive_directory_exists,
        )

    @staticmethod
    def _path_for_id(
        archive_id: str,
        archive_payloads: tuple[tuple[Path, bytes], ...],
    ) -> Path:
        for path, payload in archive_payloads:
            archive = LocalJournalArchiveProject._decode_archive(path, payload)
            if archive.archive_id == archive_id:
                return path
        raise ValueError(f"Unknown journal archive {archive_id!r}.")

    @staticmethod
    def _decode_archive(path: Path, payload: bytes) -> JournalArchiveSnapshot:
        archive = journal_archive_from_data(decode_object_bytes(payload, path), source=path)
        require_canonical_archive_path(path, archive.archive_id)
        return archive

    def _revision(self, payloads: _ArchivePayloadSnapshot) -> ProjectRevision:
        sources: list[tuple[str, bytes]] = [
            (str(self.adventure_path.resolve()), payloads.adventure_payload),
            (str(self.state_path.resolve()), payloads.active_state_payload),
        ]
        if payloads.archive_directory_exists:
            sources.extend(
                (str(path.resolve()), payload) for path, payload in payloads.archive_payloads
            )
        else:
            sources.append((str(self.archive_directory.resolve()), _MISSING_DIRECTORY))
        return ProjectRevision(framed_sha256_hexdigest(sorted(sources)))
