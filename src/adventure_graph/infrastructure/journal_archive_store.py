"""Versioned persistence for archived play journals."""

from __future__ import annotations

from pathlib import Path

from adventure_graph.application.archive_management import (
    JournalArchiveSnapshot as JournalArchive,
)
from adventure_graph.application.archive_management import (
    require_archive_id,
)
from adventure_graph.domain.play_state import PlayState
from adventure_graph.infrastructure.adventure_store import adventure_data, adventure_from_data
from adventure_graph.infrastructure.atomic_files import (
    remove_file,
    write_json_object,
    write_json_objects,
)
from adventure_graph.infrastructure.json_values import (
    JsonObject,
    UnsupportedFieldError,
    nonempty_string_value,
    object_value,
    positive_integer,
    read_object,
    reject_unknown_fields,
    rfc3339_datetime_value,
    string_value,
)
from adventure_graph.infrastructure.play_state_store import play_state_data, play_state_from_data

JOURNAL_ARCHIVE_SCHEMA_VERSION = 1

JOURNAL_ARCHIVE_ROOT_FIELDS = (
    "schema_version",
    "archive",
    "adventure_snapshot",
    "play_state",
)
JOURNAL_ARCHIVE_METADATA_FIELDS = (
    "id",
    "label",
    "archived_at",
    "source_state_name",
    "event_count",
)


def load_journal_archive(path: Path) -> JournalArchive:
    """Load and validate one canonically named versioned journal archive."""
    archive = journal_archive_from_data(read_object(path), source=path)
    require_canonical_archive_path(path, archive.archive_id)
    return archive


def journal_archive_from_data(
    data: JsonObject,
    *,
    source: str | Path = "journal archive document",
) -> JournalArchive:
    """Decode and validate one versioned journal archive object."""
    if data.get("schema_version") != JOURNAL_ARCHIVE_SCHEMA_VERSION:
        raise ValueError(
            "Only journal archive schema_version "
            f"{JOURNAL_ARCHIVE_SCHEMA_VERSION} is supported in {source}."
        )
    try:
        return _journal_archive_from_current_schema(data, source)
    except UnsupportedFieldError:
        raise
    except ValueError as error:
        raise ValueError(f"Malformed journal archive document in {source}: {error}") from error


def _journal_archive_from_current_schema(data: JsonObject, source: str | Path) -> JournalArchive:
    reject_unknown_fields(data, JOURNAL_ARCHIVE_ROOT_FIELDS, f"{source} root")
    metadata = object_value(data, "archive")
    reject_unknown_fields(metadata, JOURNAL_ARCHIVE_METADATA_FIELDS, f"{source} archive")
    adventure = adventure_from_data(
        object_value(data, "adventure_snapshot"), source=f"{source} adventure_snapshot"
    )
    state = play_state_from_data(object_value(data, "play_state"), source=f"{source} play_state")
    archive_id = string_value(metadata, "id")
    canonical_archive_filename(archive_id)
    archive = JournalArchive(
        archive_id=archive_id,
        label=string_value(metadata, "label", ""),
        archived_at=rfc3339_datetime_value(metadata, "archived_at"),
        source_state_name=nonempty_string_value(metadata, "source_state_name"),
        adventure_snapshot=adventure,
        play_state=state,
    )
    expected_event_count = positive_integer(metadata, "event_count")
    if expected_event_count != archive.event_count:
        raise ValueError(
            "Archive event_count does not match the embedded play journal: "
            f"expected {expected_event_count}, found {archive.event_count}."
        )
    if adventure.id != state.adventure_id:
        raise ValueError(
            "Archived adventure snapshot and play journal identify different adventures."
        )
    return archive


def canonical_archive_filename(archive_id: str) -> str:
    """Return the canonical filename for one valid archive identifier."""
    require_archive_id(archive_id)
    return f"{archive_id}.journal.json"


def require_canonical_archive_path(path: Path, archive_id: str) -> None:
    """Reject a journal archive whose filename disagrees with its embedded identity."""
    expected_name = canonical_archive_filename(archive_id)
    if path.name != expected_name:
        raise ValueError(
            f"Journal archive filename {path.name!r} does not match embedded identifier "
            f"{archive_id!r}; expected {expected_name!r}."
        )


def journal_archive_data(archive: JournalArchive) -> JsonObject:
    """Return the canonical JSON object for a journal archive."""
    canonical_archive_filename(archive.archive_id)
    metadata: JsonObject = {
        "id": archive.archive_id,
        "label": archive.label,
        "archived_at": archive.archived_at,
        "source_state_name": archive.source_state_name,
        "event_count": archive.event_count,
    }
    rfc3339_datetime_value(metadata, "archived_at")
    nonempty_string_value(metadata, "source_state_name")
    positive_integer(metadata, "event_count")
    return {
        "schema_version": JOURNAL_ARCHIVE_SCHEMA_VERSION,
        "archive": metadata,
        "adventure_snapshot": adventure_data(archive.adventure_snapshot),
        "play_state": play_state_data(archive.play_state),
    }


def save_archive_and_reset(
    archive_path: Path,
    archive: JournalArchive,
    state_path: Path,
    empty_state: PlayState,
) -> None:
    """Persist an archive and reset its active journal as one coordinated commit."""
    require_canonical_archive_path(archive_path, archive.archive_id)
    if archive_path.exists():
        raise FileExistsError(f"Archive already exists: {archive_path}.")
    write_json_objects(
        {
            archive_path: journal_archive_data(archive),
            state_path: play_state_data(empty_state),
        }
    )


def save_journal_archive(archive_path: Path, archive: JournalArchive) -> None:
    """Persist one immutable journal archive without changing the active journal."""
    require_canonical_archive_path(archive_path, archive.archive_id)
    if archive_path.exists():
        raise FileExistsError(f"Archive already exists: {archive_path}.")
    write_json_object(archive_path, journal_archive_data(archive))


def restore_journal_archive(
    archive_path: Path,
    state_path: Path,
    restored_state: PlayState,
) -> None:
    """Restore an archived journal while retaining the immutable archive."""
    if not archive_path.exists():
        raise FileNotFoundError(f"Archive does not exist: {archive_path}.")
    write_json_object(state_path, play_state_data(restored_state))


def delete_journal_archive(path: Path) -> None:
    """Delete one journal archive after confirmation has occurred upstream."""
    remove_file(path)
