"""Fault-injection coverage for crash-recoverable canonical-file transactions."""

from __future__ import annotations

import errno
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from tests.support.adventures import complete_four_encounter_adventure

import adventure_graph.infrastructure.file_transactions as file_transactions  # noqa: PLR0402 -- tests patch module-owned private seams.
from adventure_graph.application.archive_management import JournalArchiveSnapshot
from adventure_graph.application.play_tracking import new_play_state, record_visit
from adventure_graph.infrastructure.adventure_store import save_adventure
from adventure_graph.infrastructure.atomic_files import write_json_objects
from adventure_graph.infrastructure.file_transactions import TransactionRecoveryError
from adventure_graph.infrastructure.journal_archive_store import save_archive_and_reset
from adventure_graph.infrastructure.json_values import read_object
from adventure_graph.infrastructure.local_authoring_project import LocalAuthoringProject
from adventure_graph.infrastructure.play_state_store import save_play_state


def test_coordinated_replace_rejects_destinations_that_normalize_to_one_path(
    tmp_path: Path,
) -> None:
    duplicate = tmp_path / "nested" / ".." / "canonical.json"
    canonical = tmp_path / "canonical.json"

    with pytest.raises(ValueError, match="Duplicate coordinated destination"):
        file_transactions.coordinated_replace({duplicate: b"first", canonical: b"second"})

    assert not canonical.exists()


def _assert_coordinated_write_cleans_staging_after_disk_or_permission_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_number: int,
) -> None:
    first, second = _existing_pair(tmp_path)
    original_first = first.read_bytes()
    original_second = second.read_bytes()
    real_write = file_transactions._write_bytes_exclusive
    new_write_count = 0

    def fail_during_staging(path: Path, content: bytes) -> None:
        nonlocal new_write_count
        if path.name.endswith(".new.tmp"):
            new_write_count += 1
            if new_write_count == 2:
                raise OSError(error_number, os.strerror(error_number))
        real_write(path, content)

    monkeypatch.setattr(file_transactions, "_write_bytes_exclusive", fail_during_staging)

    with pytest.raises(OSError, match=rf"\[Errno {error_number}\]") as error:
        write_json_objects({first: {"value": "new-first"}, second: {"value": "new-second"}})

    assert error.value.errno == error_number
    assert first.read_bytes() == original_first
    assert second.read_bytes() == original_second
    assert _transaction_artifacts(tmp_path) == []


@pytest.mark.parametrize("error_number", [errno.ENOSPC, errno.EACCES])
def test_coordinated_write_cleans_staging_after_disk_or_permission_failure_parameterized(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error_number: int,
) -> None:
    _assert_coordinated_write_cleans_staging_after_disk_or_permission_failure(
        tmp_path, monkeypatch, error_number
    )


def test_failure_before_staging_preserves_canonical_files_and_leaves_no_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second = _existing_pair(tmp_path)
    original_first = first.read_bytes()
    original_second = second.read_bytes()

    def fail_first_marker_write(path: Path, content: bytes) -> None:
        raise OSError(errno.EACCES, "simulated marker permission failure")

    monkeypatch.setattr(file_transactions, "_write_bytes_exclusive", fail_first_marker_write)

    with pytest.raises(OSError, match="marker permission failure"):
        write_json_objects({first: {"value": "new-first"}, second: {"value": "new-second"}})

    assert first.read_bytes() == original_first
    assert second.read_bytes() == original_second
    assert _transaction_artifacts(tmp_path) == []


def test_archive_reset_removes_new_archive_when_active_state_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adventure = complete_four_encounter_adventure()
    active_state = record_visit(adventure, new_play_state(adventure), "alpha")
    state_path = tmp_path / "play-state.json"
    archive_path = tmp_path / "archives" / "first-run.journal.json"
    save_play_state(state_path, active_state)
    original_state = state_path.read_bytes()
    archive = JournalArchiveSnapshot(
        archive_id="first-run",
        label="First run",
        archived_at="2026-07-24T18:00:00Z",
        source_state_name=state_path.name,
        adventure_snapshot=adventure,
        play_state=active_state,
    )
    real_replace = Path.replace
    failed = False

    def fail_state_replacement(source: Path, target: str | Path) -> Path:
        nonlocal failed
        if source.name.endswith(".new.tmp") and Path(target) == state_path and not failed:
            failed = True
            raise OSError(errno.ENOSPC, "simulated archive reset failure")
        return real_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_state_replacement)

    with pytest.raises(OSError, match="archive reset failure"):
        save_archive_and_reset(archive_path, archive, state_path, new_play_state(adventure))

    assert not archive_path.exists()
    assert state_path.read_bytes() == original_state
    assert _transaction_artifacts(tmp_path) == []


def test_coordinated_write_rolls_back_cross_device_replacement_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second = _existing_pair(tmp_path)
    original_first = first.read_bytes()
    original_second = second.read_bytes()
    real_replace = Path.replace
    failed = False

    def fail_cross_device(source: Path, target: str | Path) -> Path:
        nonlocal failed
        if source.name.endswith(".new.tmp") and Path(target) == second and not failed:
            failed = True
            raise OSError(errno.EXDEV, "simulated cross-device replacement")
        return real_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_cross_device)

    with pytest.raises(OSError, match="simulated cross-device replacement") as error:
        write_json_objects({first: {"value": "new-first"}, second: {"value": "new-second"}})

    assert error.value.errno == errno.EXDEV
    assert first.read_bytes() == original_first
    assert second.read_bytes() == original_second
    assert _transaction_artifacts(tmp_path) == []


def test_directory_sync_failure_before_commit_rolls_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second = _existing_pair(tmp_path)
    original_first = first.read_bytes()
    original_second = second.read_bytes()
    real_sync = file_transactions._sync_directory
    failed = False

    def fail_after_first_destination(directory: Path) -> None:
        nonlocal failed
        if (
            not failed
            and first.exists()
            and b"new-first" in first.read_bytes()
            and b"old-second" in second.read_bytes()
        ):
            failed = True
            raise OSError(errno.EIO, "simulated directory sync failure")
        real_sync(directory)

    monkeypatch.setattr(file_transactions, "_sync_directory", fail_after_first_destination)

    with pytest.raises(OSError, match="directory sync failure"):
        write_json_objects({first: {"value": "new-first"}, second: {"value": "new-second"}})

    assert first.read_bytes() == original_first
    assert second.read_bytes() == original_second
    assert _transaction_artifacts(tmp_path) == []


def test_failed_rollback_remains_recoverable_on_the_next_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second = _existing_pair(tmp_path)
    original_first = first.read_bytes()
    original_second = second.read_bytes()
    real_replace = Path.replace
    forward_failed = False
    rollback_failed = False

    def fail_forward_and_first_rollback(source: Path, target: str | Path) -> Path:
        nonlocal forward_failed, rollback_failed
        destination = Path(target)
        if source.name.endswith(".new.tmp") and destination == second and not forward_failed:
            forward_failed = True
            raise OSError(errno.ENOSPC, "simulated forward failure")
        if source.name.endswith(".restore.tmp") and destination == first and not rollback_failed:
            rollback_failed = True
            raise OSError(errno.EACCES, "simulated rollback failure")
        return real_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_forward_and_first_rollback)

    with pytest.raises(TransactionRecoveryError, match="automatic rollback could not complete"):
        write_json_objects({first: {"value": "new-first"}, second: {"value": "new-second"}})

    assert _transaction_markers(tmp_path)
    monkeypatch.setattr(Path, "replace", real_replace)

    assert read_object(first) == {"value": "old-first"}
    assert first.read_bytes() == original_first
    assert second.read_bytes() == original_second
    assert _transaction_artifacts(tmp_path) == []


def test_recovery_removes_destination_that_did_not_exist_before_transaction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = tmp_path / "created.json"
    existing = tmp_path / "existing.json"
    existing.write_text('{"value":"old"}\n', encoding="utf-8")
    original_existing = existing.read_bytes()
    real_replace = Path.replace
    failed = False

    def fail_second_destination(source: Path, target: str | Path) -> Path:
        nonlocal failed
        if source.name.endswith(".new.tmp") and Path(target) == existing and not failed:
            failed = True
            raise OSError(errno.EIO, "simulated replacement failure")
        return real_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_second_destination)

    with pytest.raises(OSError, match="replacement failure"):
        write_json_objects({created: {"created": True}, existing: {"value": "new"}})

    assert not created.exists()
    assert existing.read_bytes() == original_existing
    assert _transaction_artifacts(tmp_path) == []


@pytest.mark.parametrize(
    ("phase", "expected_first"),
    [
        ("staging", "old-first"),
        ("replacement", "old-first"),
        ("before-commit", "old-first"),
        ("commit-marker", "new-first"),
        ("after-commit", "new-first"),
    ],
)
def test_process_termination_recovers_at_the_transaction_commit_boundary(
    tmp_path: Path,
    phase: str,
    expected_first: str,
) -> None:
    first, second = _existing_pair(tmp_path)
    result = _run_crashing_writer(tmp_path, phase)

    assert (
        result.returncode
        == {
            "staging": 71,
            "replacement": 72,
            "before-commit": 73,
            "commit-marker": 74,
            "after-commit": 75,
        }[phase]
    )
    assert read_object(first) == {"value": expected_first}
    expected_second = "new-second" if phase in {"commit-marker", "after-commit"} else "old-second"
    assert read_object(second) == {"value": expected_second}
    assert _transaction_artifacts(tmp_path) == []


def test_revision_snapshot_recovers_interrupted_bundle_before_reading_bytes(
    tmp_path: Path,
) -> None:
    adventure = complete_four_encounter_adventure()
    state = new_play_state(adventure)
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, state)
    script = r"""
import os
import sys
from dataclasses import replace
from pathlib import Path
from adventure_graph.infrastructure.adventure_store import adventure_data, load_adventure
from adventure_graph.infrastructure.atomic_files import write_json_objects
from adventure_graph.infrastructure.play_state_store import load_play_state, play_state_data

adventure_path = Path(sys.argv[1])
state_path = Path(sys.argv[2])
adventure = replace(load_adventure(adventure_path), title="Interrupted title")
state = load_play_state(state_path)
real_replace = Path.replace
crashed = False
def crash_after_first_destination(source, target):
    global crashed
    result = real_replace(source, target)
    if source.name.endswith(".new.tmp") and not crashed:
        crashed = True
        os._exit(77)
    return result
Path.replace = crash_after_first_destination
write_json_objects(
    {adventure_path: adventure_data(adventure), state_path: play_state_data(state)}
)
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).parents[3] / "src")

    result = subprocess.run(
        [sys.executable, "-c", script, str(adventure_path), str(state_path)],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        timeout=20,
    )
    snapshot = LocalAuthoringProject(adventure_path, (state_path,)).load()

    assert result.returncode == 77
    assert snapshot.adventure == adventure
    assert snapshot.related_play_states[0].state == state
    assert _transaction_artifacts(tmp_path) == []


def test_single_file_crash_before_replace_preserves_content_and_cleans_staging(
    tmp_path: Path,
) -> None:
    path = tmp_path / "single.json"
    path.write_text('{"value":"old"}\n', encoding="utf-8")
    script = r"""
import os
import sys
from pathlib import Path
import adventure_graph.infrastructure.file_transactions as transactions
from adventure_graph.infrastructure.atomic_files import write_json_object

path = Path(sys.argv[1])
real_write = transactions._write_bytes_exclusive
def crash_after_staging(staged, content):
    real_write(staged, content)
    if staged.name.endswith("-single.new.tmp"):
        os._exit(76)
transactions._write_bytes_exclusive = crash_after_staging
write_json_object(path, {"value": "new"})
"""
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).parents[3] / "src")

    result = subprocess.run(
        [sys.executable, "-c", script, str(path)],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        timeout=20,
    )

    assert result.returncode == 76
    assert read_object(path) == {"value": "old"}
    assert _transaction_artifacts(tmp_path) == []


def test_malformed_transaction_marker_fails_closed_without_touching_canonical_data(
    tmp_path: Path,
) -> None:
    first, second = _existing_pair(tmp_path)
    original_first = first.read_bytes()
    original_second = second.read_bytes()
    marker = tmp_path / ".adventure-graph-transaction-00000000000000000000000000000000.json"
    marker.write_text("not-json", encoding="utf-8")

    with pytest.raises(TransactionRecoveryError, match="Cannot read transaction marker"):
        read_object(first)

    assert first.read_bytes() == original_first
    assert second.read_bytes() == original_second
    assert marker.exists()


def _existing_pair(root: Path) -> tuple[Path, Path]:
    first = root / "first.json"
    second = root / "nested" / "second.json"
    second.parent.mkdir()
    first.write_text('{"value":"old-first"}\n', encoding="utf-8")
    second.write_text('{"value":"old-second"}\n', encoding="utf-8")
    return first, second


def _run_crashing_writer(root: Path, phase: str) -> subprocess.CompletedProcess[str]:
    script = r"""
import os
import sys
from pathlib import Path
import adventure_graph.infrastructure.file_transactions as file_transactions
from adventure_graph.application.archive_management import JournalArchiveSnapshot
from adventure_graph.application.play_tracking import new_play_state, record_visit
from adventure_graph.infrastructure.adventure_store import save_adventure
from adventure_graph.infrastructure.atomic_files import write_json_object, write_json_objects
from adventure_graph.infrastructure.journal_archive_store import save_archive_and_reset
from adventure_graph.infrastructure.local_authoring_project import LocalAuthoringProject
from adventure_graph.infrastructure.play_state_store import save_play_state

root = Path(sys.argv[1])
phase = sys.argv[2]
first = root / "first.json"
second = root / "nested" / "second.json"

if phase == "staging":
    real_write = file_transactions._write_bytes_exclusive
    crashed = False
    def crash_during_staging(path, content):
        global crashed
        real_write(path, content)
        if path.name.endswith(".new.tmp") and not crashed:
            crashed = True
            os._exit(71)
    file_transactions._write_bytes_exclusive = crash_during_staging
elif phase == "replacement":
    real_replace = Path.replace
    crashed = False
    def crash_after_first_replace(source, target):
        global crashed
        result = real_replace(source, target)
        if source.name.endswith(".new.tmp") and not crashed:
            crashed = True
            os._exit(72)
        return result
    Path.replace = crash_after_first_replace
elif phase == "before-commit":
    def crash_before_commit_marker(record):
        os._exit(73)
    file_transactions._commit_markers = crash_before_commit_marker
elif phase == "commit-marker":
    import uuid
    real_write_markers = file_transactions._write_markers
    def crash_after_one_commit_marker(record):
        if record.state != "committed":
            return real_write_markers(record)
        marker = record.marker_paths[0]
        temporary = marker.parent / (
            f".adventure-graph-transaction-{record.transaction_id}-"
            f"{uuid.uuid4().hex}.marker.tmp"
        )
        file_transactions._write_bytes_exclusive(
            temporary, file_transactions._record_bytes(record)
        )
        temporary.replace(marker)
        file_transactions._sync_directory(marker.parent)
        os._exit(74)
    file_transactions._write_markers = crash_after_one_commit_marker
elif phase == "after-commit":
    def crash_before_cleanup(record):
        os._exit(75)
    file_transactions._cleanup_artifacts = crash_before_cleanup

write_json_objects({first: {"value": "new-first"}, second: {"value": "new-second"}})
"""
    environment = os.environ.copy()
    source_root = Path(__file__).parents[3] / "src"
    environment["PYTHONPATH"] = str(source_root)
    return subprocess.run(
        [sys.executable, "-c", script, str(root), phase],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
        timeout=20,
    )


def _transaction_markers(root: Path) -> list[Path]:
    return sorted(root.rglob(".adventure-graph-transaction-*.json"))


def _transaction_artifacts(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob(".*")
        if path.is_file()
        and (
            "adventure-graph-transaction" in path.name
            or path.name.endswith((".new.tmp", ".old.tmp", ".restore.tmp"))
        )
    )


def test_mixed_transaction_markers_treat_any_committed_marker_as_the_commit_point(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "canonical.json"
    entry = file_transactions._TransactionEntry(
        destination=destination,
        staged=tmp_path / ".adventure-graph-transaction-id-0000.new.tmp",
        backup=tmp_path / ".adventure-graph-transaction-id-0000.old.tmp",
    )
    marker = tmp_path / ".adventure-graph-transaction-id.json"
    staging = file_transactions._TransactionRecord("id", "staging", (entry,), (marker,))
    committed = file_transactions._TransactionRecord("id", "committed", (entry,), (marker,))

    merged = file_transactions._merged_record((staging, committed))

    assert merged.state == "committed"


def test_transaction_artifact_accepts_the_exact_resource_limit(tmp_path: Path) -> None:
    artifact = tmp_path / "maximum.old.tmp"
    artifact.write_bytes(b"x" * file_transactions._MAX_TRANSACTION_ARTIFACT_BYTES)

    content = file_transactions._read_transaction_artifact(artifact)

    assert len(content) == file_transactions._MAX_TRANSACTION_ARTIFACT_BYTES


def test_transaction_marker_accepts_the_exact_resource_limit(tmp_path: Path) -> None:
    destination = tmp_path / "canonical.json"
    record = file_transactions._new_record((destination,), {destination: None})
    marker = record.marker_paths[0]
    encoded = file_transactions._record_bytes(record)
    marker.write_bytes(
        encoded + b" " * (file_transactions._MAX_TRANSACTION_MARKER_BYTES - len(encoded))
    )

    loaded = file_transactions._read_record(marker)

    assert loaded == record
    assert marker.stat().st_size == file_transactions._MAX_TRANSACTION_MARKER_BYTES


def test_contained_recovery_rejects_a_transaction_family_that_escapes_its_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    external = tmp_path / "external"
    root.mkdir()
    external.mkdir()
    inside_destination = root / "inside.json"
    outside_destination = external / "outside.json"
    inside_destination.write_text('{"value":"inside"}\n', encoding="utf-8")
    outside_destination.write_text('{"value":"outside"}\n', encoding="utf-8")
    original_inside = inside_destination.read_bytes()
    original_outside = outside_destination.read_bytes()
    transaction_id = "0123456789abcdef0123456789abcdef"
    marker_name = f".adventure-graph-transaction-{transaction_id}.json"
    marker_paths = tuple(directory / marker_name for directory in sorted((root, external), key=str))
    entries = []
    for index, destination in enumerate((inside_destination, outside_destination)):
        entries.append(
            {
                "destination": str(destination),
                "staged": str(
                    destination.parent
                    / (f".adventure-graph-transaction-{transaction_id}-{index:04d}.new.tmp")
                ),
                "backup": None,
            }
        )
    marker = root / marker_name
    marker.write_text(
        json.dumps(
            {
                "version": 1,
                "transaction_id": transaction_id,
                "state": "prepared",
                "entries": entries,
                "marker_paths": [str(path) for path in marker_paths],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(TransactionRecoveryError, match="escaped its configured filesystem root"):
        file_transactions.recover_pending_transactions_in_directories(
            (root,), containment_root=root
        )

    assert inside_destination.read_bytes() == original_inside
    assert outside_destination.read_bytes() == original_outside
    assert marker.exists()


def test_recovery_rejects_symlinked_transaction_markers(tmp_path: Path) -> None:
    transaction_id = "fedcba9876543210fedcba9876543210"
    marker = tmp_path / f".adventure-graph-transaction-{transaction_id}.json"
    external = tmp_path.parent / f"{tmp_path.name}-marker.json"
    external.write_text("{}", encoding="utf-8")
    try:
        marker.symlink_to(external)
    except OSError:
        pytest.skip("Filesystem symlinks are not available on this platform.")

    with pytest.raises(TransactionRecoveryError, match="must not be a symlink"):
        file_transactions.recover_pending_transactions_in_directories((tmp_path,))


def test_recovery_rejects_oversized_transaction_markers(tmp_path: Path) -> None:
    transaction_id = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    marker = tmp_path / f".adventure-graph-transaction-{transaction_id}.json"
    marker.write_bytes(b" " * (file_transactions._MAX_TRANSACTION_MARKER_BYTES + 1))

    with pytest.raises(TransactionRecoveryError, match="marker is too large"):
        file_transactions.recover_pending_transactions_in_directories((tmp_path,))


def test_contained_recovery_rejects_symlinked_transaction_artifacts(tmp_path: Path) -> None:
    destination = tmp_path / "canonical.json"
    destination.write_text('{"value":"canonical"}\n', encoding="utf-8")
    original_destination = destination.read_bytes()
    external = tmp_path.parent / f"{tmp_path.name}-backup.json"
    external.write_text('{"value":"external"}\n', encoding="utf-8")
    original_external = external.read_bytes()
    transaction_id = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    prefix = f".adventure-graph-transaction-{transaction_id}"
    marker = tmp_path / f"{prefix}.json"
    staged = tmp_path / f"{prefix}-0000.new.tmp"
    backup = tmp_path / f"{prefix}-0000.old.tmp"
    try:
        backup.symlink_to(external)
    except OSError:
        pytest.skip("Filesystem symlinks are not available on this platform.")
    marker.write_text(
        json.dumps(
            {
                "version": 1,
                "transaction_id": transaction_id,
                "state": "prepared",
                "entries": [
                    {
                        "destination": str(destination),
                        "staged": str(staged),
                        "backup": str(backup),
                    }
                ],
                "marker_paths": [str(marker)],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(TransactionRecoveryError, match="configured filesystem root"):
        file_transactions.recover_pending_transactions_in_directories(
            (tmp_path,), containment_root=tmp_path
        )

    assert destination.read_bytes() == original_destination
    assert external.read_bytes() == original_external
    assert marker.exists()


def test_recovery_rejects_oversized_transaction_backups(tmp_path: Path) -> None:
    destination = tmp_path / "canonical.json"
    destination.write_text('{"value":"canonical"}\n', encoding="utf-8")
    original_destination = destination.read_bytes()
    transaction_id = "cccccccccccccccccccccccccccccccc"
    prefix = f".adventure-graph-transaction-{transaction_id}"
    marker = tmp_path / f"{prefix}.json"
    staged = tmp_path / f"{prefix}-0000.new.tmp"
    backup = tmp_path / f"{prefix}-0000.old.tmp"
    backup.write_bytes(b"x" * (file_transactions._MAX_TRANSACTION_ARTIFACT_BYTES + 1))
    marker.write_text(
        json.dumps(
            {
                "version": 1,
                "transaction_id": transaction_id,
                "state": "prepared",
                "entries": [
                    {
                        "destination": str(destination),
                        "staged": str(staged),
                        "backup": str(backup),
                    }
                ],
                "marker_paths": [str(marker)],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(TransactionRecoveryError, match="artifact is too large"):
        file_transactions.recover_pending_transactions_in_directories((tmp_path,))

    assert destination.read_bytes() == original_destination
    assert marker.exists()
    assert backup.exists()
