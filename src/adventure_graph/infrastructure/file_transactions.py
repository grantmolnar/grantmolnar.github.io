"""Crash-recoverable coordinated replacement for canonical local files."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import Iterable, Mapping
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from adventure_graph.application.document_limits import (
    MAX_CANONICAL_JSON_BYTES as _MAX_TRANSACTION_ARTIFACT_BYTES,
)
from adventure_graph.infrastructure.local_path_safety import (
    UnsafeFilesystemLayoutError,
    require_contained_file,
    require_paths_within_root,
)

_TRANSACTION_VERSION = 1
_MARKER_PREFIX = ".adventure-graph-transaction-"
_MARKER_SUFFIX = ".json"
_ARTIFACT_SUFFIX = ".tmp"
_STAGING = "staging"
_PREPARED = "prepared"
_COMMITTED = "committed"
_MAX_TRANSACTION_MARKER_BYTES = 1_048_576
_MAX_TRANSACTION_ENTRIES = 256


class TransactionRecoveryError(OSError):
    """Raised when an interrupted coordinated write cannot be recovered safely."""


@dataclass(frozen=True, slots=True)
class _TransactionEntry:
    destination: Path
    staged: Path
    backup: Path | None


@dataclass(frozen=True, slots=True)
class _TransactionRecord:
    transaction_id: str
    state: str
    entries: tuple[_TransactionEntry, ...]
    marker_paths: tuple[Path, ...]


def coordinated_replace(payloads: Mapping[Path, bytes]) -> None:
    """Replace several destinations with crash-recoverable all-or-nothing semantics."""
    if len(payloads) < 2:
        raise ValueError("Coordinated replacement requires at least two destinations.")
    normalized = _normalized_payloads(payloads)
    recover_pending_transactions(normalized)
    originals = {path: path.read_bytes() if path.exists() else None for path in normalized}
    record = _new_record(tuple(normalized), originals)
    try:
        _write_markers(record)
        _stage_transaction(record, normalized, originals)
        prepared = _with_state(record, _PREPARED)
        _write_markers(prepared)
        _replace_destinations(prepared)
        _commit_markers(prepared)
    except BaseException:
        try:
            recover_pending_transactions(normalized)
        except BaseException as recovery_error:
            raise TransactionRecoveryError(
                "The coordinated write failed and automatic rollback could not complete. "
                "Leave the hidden Adventure Graph transaction files in place and retry the "
                "same project after correcting the filesystem problem."
            ) from recovery_error
        raise
    _cleanup_artifacts(record)


def replace_one(path: Path, content: bytes) -> None:
    """Atomically replace one file and request durable directory metadata."""
    destination = _normalized_path(path)
    recover_pending_transactions((destination,))
    ensure_directory(destination.parent)
    staged = destination.parent / (
        f"{_MARKER_PREFIX}{uuid.uuid4().hex}-single.new{_ARTIFACT_SUFFIX}"
    )
    try:
        _write_bytes_exclusive(staged, content)
        staged.replace(destination)
        _sync_directory(destination.parent)
    finally:
        _best_effort_unlink(staged)


def ensure_directory(path: Path) -> None:
    """Create one directory tree and sync each new parent entry where supported."""
    directory = _normalized_path(path)
    if directory.exists():
        if not directory.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {directory}.")
        return
    missing: list[Path] = []
    cursor = directory
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    if not cursor.is_dir():
        raise NotADirectoryError(f"Directory ancestor is not a directory: {cursor}.")
    for candidate in reversed(missing):
        candidate.mkdir()
        _sync_directory(candidate)
        _sync_directory(candidate.parent)


def remove_empty_directory(path: Path) -> None:
    """Remove one empty directory and request durable parent metadata."""
    directory = _normalized_path(path)
    directory.rmdir()
    _sync_directory(directory.parent)


def remove_one(path: Path) -> None:
    """Remove one file and request durable directory metadata."""
    destination = _normalized_path(path)
    recover_pending_transactions((destination,))
    if not destination.exists():
        raise FileNotFoundError(f"File does not exist: {destination}.")
    destination.unlink()
    _sync_directory(destination.parent)


def recover_pending_transactions(
    paths: Iterable[Path],
    *,
    containment_root: Path | None = None,
) -> None:
    """Recover interrupted transactions visible beside the supplied canonical paths."""
    directories = {_normalized_path(path).parent for path in paths}
    recover_pending_transactions_in_directories(directories, containment_root=containment_root)


def recover_pending_transactions_in_directories(
    directories: Iterable[Path],
    *,
    containment_root: Path | None = None,
) -> None:
    """Recover transaction markers and remove committed orphan artifacts."""
    normalized = tuple(sorted({_normalized_path(path) for path in directories}, key=str))
    markers: list[Path] = []
    for directory in normalized:
        if directory.is_dir():
            markers.extend(sorted(directory.glob(f"{_MARKER_PREFIX}*{_MARKER_SUFFIX}")))
    recovered_ids: set[str] = set()
    for marker in markers:
        transaction_id = _transaction_id_from_marker_name(marker)
        if transaction_id in recovered_ids or not marker.exists():
            continue
        _recover_transaction(marker, containment_root=containment_root)
        recovered_ids.add(transaction_id)
    for directory in normalized:
        _cleanup_orphan_artifacts(directory)


def _normalized_payloads(payloads: Mapping[Path, bytes]) -> dict[Path, bytes]:
    normalized: dict[Path, bytes] = {}
    for path, content in payloads.items():
        destination = _normalized_path(path)
        if destination in normalized:
            raise ValueError(f"Duplicate coordinated destination {destination}.")
        normalized[destination] = content
    return dict(sorted(normalized.items(), key=lambda item: str(item[0])))


def _normalized_path(path: Path) -> Path:
    return path.parent.resolve() / path.name


def _new_record(
    destinations: tuple[Path, ...],
    originals: Mapping[Path, bytes | None],
) -> _TransactionRecord:
    transaction_id = uuid.uuid4().hex
    entries = tuple(
        _TransactionEntry(
            destination=destination,
            staged=destination.parent
            / f"{_MARKER_PREFIX}{transaction_id}-{index:04d}.new{_ARTIFACT_SUFFIX}",
            backup=(
                destination.parent
                / f"{_MARKER_PREFIX}{transaction_id}-{index:04d}.old{_ARTIFACT_SUFFIX}"
                if originals[destination] is not None
                else None
            ),
        )
        for index, destination in enumerate(destinations)
    )
    marker_paths = tuple(
        directory / f"{_MARKER_PREFIX}{transaction_id}{_MARKER_SUFFIX}"
        for directory in sorted({entry.destination.parent for entry in entries}, key=str)
    )
    return _TransactionRecord(transaction_id, _STAGING, entries, marker_paths)


def _with_state(record: _TransactionRecord, state: str) -> _TransactionRecord:
    return _TransactionRecord(record.transaction_id, state, record.entries, record.marker_paths)


def _write_markers(record: _TransactionRecord) -> None:
    content = _record_bytes(record)
    for marker in record.marker_paths:
        ensure_directory(marker.parent)
        temporary = marker.parent / (
            f"{_MARKER_PREFIX}{record.transaction_id}-{uuid.uuid4().hex}.marker{_ARTIFACT_SUFFIX}"
        )
        try:
            _write_bytes_exclusive(temporary, content)
            temporary.replace(marker)
            _sync_directory(marker.parent)
        finally:
            _best_effort_unlink(temporary)


def _stage_transaction(
    record: _TransactionRecord,
    payloads: Mapping[Path, bytes],
    originals: Mapping[Path, bytes | None],
) -> None:
    for entry in record.entries:
        ensure_directory(entry.destination.parent)
        _write_bytes_exclusive(entry.staged, payloads[entry.destination])
        original = originals[entry.destination]
        if entry.backup is not None and original is not None:
            _write_bytes_exclusive(entry.backup, original)


def _replace_destinations(record: _TransactionRecord) -> None:
    for entry in record.entries:
        entry.staged.replace(entry.destination)
        _sync_directory(entry.destination.parent)


def _commit_markers(record: _TransactionRecord) -> None:
    committed = _with_state(record, _COMMITTED)
    try:
        _write_markers(committed)
    except BaseException:
        if _recover_if_commit_point_was_written(record):
            return
        raise
    try:
        _remove_markers(committed)
    except BaseException:  # noqa: BLE001 -- cleanup must survive process-level interruption.
        # Every destination and marker already crossed the commit point. Cleanup is retryable.
        recover_pending_transactions_in_directories(marker.parent for marker in record.marker_paths)


def _recover_if_commit_point_was_written(record: _TransactionRecord) -> bool:
    marker = next((path for path in record.marker_paths if path.exists()), None)
    if marker is None:
        return False
    records = _load_marker_family(marker)
    if _merged_record(records).state != _COMMITTED:
        return False
    _recover_transaction(marker)
    return True


def _cleanup_artifacts(record: _TransactionRecord) -> None:
    directories: set[Path] = set()
    for entry in record.entries:
        _best_effort_unlink(entry.staged)
        if entry.backup is not None:
            _best_effort_unlink(entry.backup)
        directories.add(entry.destination.parent)
    for marker in record.marker_paths:
        _best_effort_unlink(marker)
        directories.add(marker.parent)
    for directory in directories:
        if not directory.is_dir():
            continue
        with suppress(OSError):
            # The canonical commit is already complete. A later read retries artifact cleanup.
            _sync_directory(directory)


def _recover_transaction(
    marker: Path,
    *,
    containment_root: Path | None = None,
) -> None:
    records = _load_marker_family(marker, containment_root=containment_root)
    record = _merged_record(records)
    if record.state == _PREPARED:
        _rollback_prepared(record)
    _remove_markers(record)
    _cleanup_artifacts(record)


def _load_marker_family(
    marker: Path,
    *,
    containment_root: Path | None = None,
) -> tuple[_TransactionRecord, ...]:
    first = _read_record(marker, containment_root=containment_root)
    records = [
        _read_record(expected, containment_root=containment_root)
        for expected in first.marker_paths
        if expected.exists()
    ]
    if not records:
        raise TransactionRecoveryError(f"Transaction marker disappeared during recovery: {marker}.")
    return tuple(records)


def _merged_record(records: tuple[_TransactionRecord, ...]) -> _TransactionRecord:
    first = records[0]
    for record in records[1:]:
        if (
            record.transaction_id != first.transaction_id
            or record.entries != first.entries
            or record.marker_paths != first.marker_paths
        ):
            raise TransactionRecoveryError(
                f"Conflicting transaction markers for {first.transaction_id}."
            )
    states = {record.state for record in records}
    if _COMMITTED in states:
        state = _COMMITTED
    elif _STAGING in states:
        state = _STAGING
    else:
        state = _PREPARED
    return _with_state(first, state)


def _rollback_prepared(record: _TransactionRecord) -> None:
    directories: set[Path] = set()
    for index, entry in enumerate(record.entries):
        if entry.backup is None:
            entry.destination.unlink(missing_ok=True)
        else:
            if not entry.backup.exists():
                raise TransactionRecoveryError(f"Missing rollback backup for {entry.destination}.")
            restore = entry.destination.parent / (
                f"{_MARKER_PREFIX}{record.transaction_id}-{index:04d}.restore{_ARTIFACT_SUFFIX}"
            )
            try:
                _write_bytes_exclusive(restore, _read_transaction_artifact(entry.backup))
                restore.replace(entry.destination)
            finally:
                _best_effort_unlink(restore)
        directories.add(entry.destination.parent)
    for directory in directories:
        _sync_directory(directory)


def _read_transaction_artifact(path: Path) -> bytes:
    try:
        with path.open("rb") as stream:
            content = stream.read(_MAX_TRANSACTION_ARTIFACT_BYTES + 1)
    except OSError as error:
        raise TransactionRecoveryError(
            f"Cannot read transaction recovery artifact {path}."
        ) from error
    if len(content) > _MAX_TRANSACTION_ARTIFACT_BYTES:
        raise TransactionRecoveryError(f"Transaction recovery artifact is too large: {path}.")
    return content


def _remove_markers(record: _TransactionRecord) -> None:
    directories: set[Path] = set()
    for marker in record.marker_paths:
        marker.unlink(missing_ok=True)
        directories.add(marker.parent)
    for directory in directories:
        if directory.is_dir():
            _sync_directory(directory)


def _read_record(
    path: Path,
    *,
    containment_root: Path | None = None,
) -> _TransactionRecord:
    if path.is_symlink():
        raise TransactionRecoveryError(f"Transaction marker must not be a symlink: {path}.")
    try:
        with path.open("rb") as stream:
            content = stream.read(_MAX_TRANSACTION_MARKER_BYTES + 1)
        if len(content) > _MAX_TRANSACTION_MARKER_BYTES:
            raise TransactionRecoveryError(f"Transaction marker is too large: {path}.")
        raw: object = json.loads(content.decode("utf-8"))
    except TransactionRecoveryError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise TransactionRecoveryError(f"Cannot read transaction marker {path}.") from error
    if not isinstance(raw, dict):
        raise TransactionRecoveryError(f"Transaction marker must contain an object: {path}.")
    data = cast(dict[str, object], raw)
    if data.get("version") != _TRANSACTION_VERSION:
        raise TransactionRecoveryError(f"Unsupported transaction marker version in {path}.")
    transaction_id = data.get("transaction_id")
    state = data.get("state")
    entries_data = data.get("entries")
    marker_data = data.get("marker_paths")
    if (
        not isinstance(transaction_id, str)
        or _transaction_id_from_marker_name(path) != transaction_id
        or not isinstance(state, str)
        or state not in {_STAGING, _PREPARED, _COMMITTED}
        or not isinstance(entries_data, list)
        or not isinstance(marker_data, list)
    ):
        raise TransactionRecoveryError(f"Malformed transaction marker {path}.")
    entry_items = cast(list[object], entries_data)
    marker_items = cast(list[object], marker_data)
    if len(entry_items) > _MAX_TRANSACTION_ENTRIES or len(marker_items) > _MAX_TRANSACTION_ENTRIES:
        raise TransactionRecoveryError(f"Malformed transaction marker {path}.")
    entries = tuple(
        _entry_from_data(item, transaction_id, index) for index, item in enumerate(entry_items)
    )
    marker_paths = tuple(_marker_path_from_data(item, transaction_id) for item in marker_items)
    expected_markers = tuple(
        directory / f"{_MARKER_PREFIX}{transaction_id}{_MARKER_SUFFIX}"
        for directory in sorted({entry.destination.parent for entry in entries}, key=str)
    )
    if (
        not entries
        or len({entry.destination for entry in entries}) != len(entries)
        or marker_paths != expected_markers
        or path not in marker_paths
    ):
        raise TransactionRecoveryError(f"Transaction marker family is inconsistent in {path}.")
    if containment_root is not None:
        transaction_paths = (
            tuple(
                path
                for entry in entries
                for path in (entry.destination, entry.staged, entry.backup)
                if path is not None
            )
            + marker_paths
        )
        try:
            require_paths_within_root(
                transaction_paths,
                containment_root,
                label="Transaction marker",
            )
            for transaction_path in transaction_paths:
                require_contained_file(
                    transaction_path,
                    containment_root,
                    allow_missing=True,
                    label="Transaction path",
                )
        except UnsafeFilesystemLayoutError as error:
            raise TransactionRecoveryError(
                f"Transaction marker escaped its configured filesystem root: {path}."
            ) from error
    return _TransactionRecord(transaction_id, state, entries, marker_paths)


def _entry_from_data(
    data: object,
    transaction_id: str,
    index: int,
) -> _TransactionEntry:
    if not isinstance(data, dict):
        raise TransactionRecoveryError("Transaction entry must be an object.")
    entry_data = cast(dict[str, object], data)
    destination_value = entry_data.get("destination")
    staged_value = entry_data.get("staged")
    backup_value = entry_data.get("backup")
    if (
        not isinstance(destination_value, str)
        or not isinstance(staged_value, str)
        or (backup_value is not None and not isinstance(backup_value, str))
    ):
        raise TransactionRecoveryError("Malformed transaction entry paths.")
    destination = Path(destination_value)
    staged = Path(staged_value)
    backup = Path(backup_value) if isinstance(backup_value, str) else None
    expected_staged = destination.parent / (
        f"{_MARKER_PREFIX}{transaction_id}-{index:04d}.new{_ARTIFACT_SUFFIX}"
    )
    expected_backup = destination.parent / (
        f"{_MARKER_PREFIX}{transaction_id}-{index:04d}.old{_ARTIFACT_SUFFIX}"
    )
    if not destination.is_absolute() or staged != expected_staged:
        raise TransactionRecoveryError("Transaction entry escaped its destination directory.")
    if backup is not None and backup != expected_backup:
        raise TransactionRecoveryError("Transaction backup escaped its destination directory.")
    return _TransactionEntry(destination, staged, backup)


def _marker_path_from_data(data: object, transaction_id: str) -> Path:
    if not isinstance(data, str):
        raise TransactionRecoveryError("Malformed transaction marker path.")
    path = Path(data)
    if not path.is_absolute() or path.name != f"{_MARKER_PREFIX}{transaction_id}{_MARKER_SUFFIX}":
        raise TransactionRecoveryError("Transaction marker path is not canonical.")
    return path


def _record_bytes(record: _TransactionRecord) -> bytes:
    data = {
        "version": _TRANSACTION_VERSION,
        "transaction_id": record.transaction_id,
        "state": record.state,
        "entries": [
            {
                "destination": str(entry.destination),
                "staged": str(entry.staged),
                "backup": str(entry.backup) if entry.backup is not None else None,
            }
            for entry in record.entries
        ],
        "marker_paths": [str(path) for path in record.marker_paths],
    }
    return f"{json.dumps(data, indent=2, sort_keys=True)}\n".encode()


def _write_bytes_exclusive(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        _best_effort_unlink(path)
        raise


def _sync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _transaction_id_from_marker_name(path: Path) -> str:
    name = path.name
    if not name.startswith(_MARKER_PREFIX) or not name.endswith(_MARKER_SUFFIX):
        raise TransactionRecoveryError(f"Invalid transaction marker name: {path}.")
    transaction_id = name[len(_MARKER_PREFIX) : -len(_MARKER_SUFFIX)]
    try:
        uuid.UUID(hex=transaction_id)
    except ValueError as error:
        raise TransactionRecoveryError(f"Invalid transaction identifier in {path}.") from error
    return transaction_id


def _cleanup_orphan_artifacts(directory: Path) -> None:
    if not directory.is_dir():
        return
    changed = False
    for path in directory.iterdir():
        if not path.is_file() or not _is_transaction_artifact(path):
            continue
        try:
            path.unlink()
        except OSError:
            continue
        changed = True
    if changed:
        with suppress(OSError):
            _sync_directory(directory)


def _is_transaction_artifact(path: Path) -> bool:
    name = path.name
    return name.startswith(_MARKER_PREFIX) and name.endswith(_ARTIFACT_SUFFIX)


def _best_effort_unlink(path: Path) -> None:
    with suppress(OSError):
        path.unlink(missing_ok=True)
