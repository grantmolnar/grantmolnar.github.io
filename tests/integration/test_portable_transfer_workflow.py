"""Browser integration coverage for portable adventure and playthrough transfer."""

from __future__ import annotations

from pathlib import Path

import pytest

from adventure_graph.application.document_limits import MAX_CANONICAL_JSON_BYTES
from adventure_graph.application.play_tracking import new_play_state, record_visit
from adventure_graph.bootstrap import compose_workspace_web_application
from adventure_graph.infrastructure.adventure_store import load_adventure, save_adventure
from adventure_graph.infrastructure.local_adventure_workspace import LocalAdventureWorkspace
from adventure_graph.infrastructure.local_journal_archives import LocalJournalArchiveProject
from adventure_graph.infrastructure.local_path_safety import UnsafeFilesystemLayoutError
from adventure_graph.infrastructure.play_state_store import load_play_state, save_play_state
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.web import request_wsgi


def _write_project(root: Path, directory: str, title: str) -> None:
    project = root / directory
    project.mkdir()
    base = complete_four_encounter_adventure()
    adventure = base.__class__(
        id=directory,
        title=title,
        synopsis=f"Synopsis for {title}.",
        premise=base.premise,
        explanation=base.explanation,
        encounters=base.encounters,
        revelations=base.revelations,
        clues=base.clues,
        validation_policy=base.validation_policy,
    )
    save_adventure(project / "adventure.json", adventure)
    save_play_state(project / "play-state.json", new_play_state(adventure))


def test_browser_adventure_export_import_round_trip_preserves_identity(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    _write_project(source_root, "alpha", "Alpha Adventure")
    source_adventure = load_adventure(source_root / "alpha" / "adventure.json")
    source_app = compose_workspace_web_application(LocalAdventureWorkspace(source_root))

    status, headers, exported = request_wsgi(
        source_app,
        "/adventures/export",
        query="key=alpha%2Fadventure.json",
    )

    assert status == "200 OK"
    assert headers["Content-Type"] == "application/json; charset=utf-8"
    assert headers["Content-Disposition"] == (
        'attachment; filename="alpha-adventure.adventure.json"'
    )

    target_workspace = LocalAdventureWorkspace(target_root)
    target_app = compose_workspace_web_application(target_workspace)
    target_revision = target_workspace.load().revision.value
    status, headers, _ = request_wsgi(
        target_app,
        "/adventures/import",
        "POST",
        form={
            "csrf_token": target_app.csrf_token,
            "expected_revision": target_revision,
        },
        files={
            "adventure_file": (
                "alpha-adventure.adventure.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/adventures?imported=1"
    imported_path = target_root / "alpha-adventure" / "adventure.json"
    assert load_adventure(imported_path) == source_adventure
    imported_state = load_play_state(target_root / "alpha-adventure" / "play-state.json")
    assert imported_state.adventure_id == source_adventure.id
    assert imported_state.events == ()
    assert target_workspace.load().settings.selected_adventure_key == (
        "alpha-adventure/adventure.json"
    )

    duplicate_revision = target_workspace.load().revision.value
    status, _, body = request_wsgi(
        target_app,
        "/adventures/import",
        "POST",
        form={
            "csrf_token": target_app.csrf_token,
            "expected_revision": duplicate_revision,
        },
        files={
            "adventure_file": (
                "duplicate.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )
    assert status == "422 Unprocessable Content"
    assert "Adventure was not imported" in body
    assert "already present" in body


def test_browser_adventure_export_bounds_the_portable_filename(tmp_path: Path) -> None:
    _write_project(tmp_path, "alpha", "A" * 200)
    app = compose_workspace_web_application(LocalAdventureWorkspace(tmp_path))

    status, headers, _ = request_wsgi(
        app,
        "/adventures/export",
        query="key=alpha%2Fadventure.json",
    )

    assert status == "200 OK"
    assert headers["Content-Disposition"] == (f'attachment; filename="{"a" * 80}.adventure.json"')


def test_browser_playthrough_export_import_and_redownload(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    _write_project(source_root, "alpha", "Alpha Adventure")
    source_adventure_path = source_root / "alpha" / "adventure.json"
    source_adventure = load_adventure(source_adventure_path)
    source_state_path = source_root / "alpha" / "play-state.json"
    source_state = record_visit(source_adventure, new_play_state(source_adventure), "alpha")
    save_play_state(source_state_path, source_state)
    source_workspace = LocalAdventureWorkspace(source_root)
    source_app = compose_workspace_web_application(source_workspace)
    source_selected = source_workspace.load().selected_adventure
    assert source_selected is not None
    source_delegate = source_app.adventure_application(
        source_selected.key,
        source_app.csrf_token,
    )
    assert source_delegate.archive_queries is not None
    source_revision = source_delegate.archive_queries.list_archives().revision.value

    status, headers, exported = request_wsgi(
        source_app,
        "/archives/export-active",
        "POST",
        form={
            "csrf_token": source_app.csrf_token,
            "expected_revision": source_revision,
            "label": "Session One",
            "name": "session-one",
        },
    )

    assert status == "200 OK"
    assert headers["Content-Disposition"] == ('attachment; filename="session-one.journal.json"')
    assert load_play_state(source_state_path) == source_state
    assert not (source_root / "alpha" / "archives" / "session-one.journal.json").exists()

    target_project = target_root / "fixed-adventure"
    target_project.mkdir()
    save_adventure(target_project / "adventure.json", source_adventure)
    save_play_state(target_project / "play-state.json", new_play_state(source_adventure))
    target_workspace = LocalAdventureWorkspace(target_root)
    target_app = compose_workspace_web_application(target_workspace)
    target_selected = target_workspace.load().selected_adventure
    assert target_selected is not None
    target_delegate = target_app.adventure_application(
        target_selected.key,
        target_app.csrf_token,
    )
    assert target_delegate.archive_queries is not None
    target_revision = target_delegate.archive_queries.list_archives().revision.value

    status, headers, _ = request_wsgi(
        target_app,
        "/archives/import",
        "POST",
        form={
            "csrf_token": target_app.csrf_token,
            "expected_revision": target_revision,
        },
        files={
            "archive_file": (
                "session-one.journal.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/archives?action=imported&archive=session-one"
    archive_path = target_project / "archives" / "session-one.journal.json"
    assert archive_path.is_file()
    assert load_play_state(target_project / "play-state.json").events == ()

    status, headers, downloaded = request_wsgi(
        target_app,
        "/archives/session-one/download",
    )
    assert status == "200 OK"
    assert headers["Content-Disposition"] == ('attachment; filename="session-one.journal.json"')
    assert downloaded == archive_path.read_text(encoding="utf-8")

    refreshed_delegate = target_app.adventure_application(
        target_selected.key,
        target_app.csrf_token,
    )
    assert refreshed_delegate.archive_queries is not None
    duplicate_revision = refreshed_delegate.archive_queries.list_archives().revision.value
    status, _, body = request_wsgi(
        target_app,
        "/archives/import",
        "POST",
        form={
            "csrf_token": target_app.csrf_token,
            "expected_revision": duplicate_revision,
        },
        files={
            "archive_file": (
                "session-one.journal.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )
    assert status == "422 Unprocessable Content"
    assert "Playthrough was not imported" in body
    assert "already present" in body


def test_browser_rejects_playthrough_for_different_adventure_identity(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    _write_project(source_root, "alpha", "Shared Title")
    _write_project(target_root, "beta", "Shared Title")

    source_adventure = load_adventure(source_root / "alpha" / "adventure.json")
    source_state = record_visit(source_adventure, new_play_state(source_adventure), "alpha")
    save_play_state(source_root / "alpha" / "play-state.json", source_state)
    source_workspace = LocalAdventureWorkspace(source_root)
    source_app = compose_workspace_web_application(source_workspace)
    source_selected = source_workspace.load().selected_adventure
    assert source_selected is not None
    source_delegate = source_app.adventure_application(
        source_selected.key,
        source_app.csrf_token,
    )
    assert source_delegate.archive_queries is not None
    source_revision = source_delegate.archive_queries.list_archives().revision.value
    status, _, exported = request_wsgi(
        source_app,
        "/archives/export-active",
        "POST",
        form={
            "csrf_token": source_app.csrf_token,
            "expected_revision": source_revision,
            "label": "Foreign run",
            "name": "foreign-run",
        },
    )
    assert status == "200 OK"

    target_workspace = LocalAdventureWorkspace(target_root)
    target_app = compose_workspace_web_application(target_workspace)
    target_selected = target_workspace.load().selected_adventure
    assert target_selected is not None
    target_delegate = target_app.adventure_application(
        target_selected.key,
        target_app.csrf_token,
    )
    assert target_delegate.archive_queries is not None
    target_revision = target_delegate.archive_queries.list_archives().revision.value

    status, _, body = request_wsgi(
        target_app,
        "/archives/import",
        "POST",
        form={
            "csrf_token": target_app.csrf_token,
            "expected_revision": target_revision,
        },
        files={
            "archive_file": (
                "foreign-run.journal.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )

    assert status == "422 Unprocessable Content"
    assert "Playthrough was not imported" in body
    assert "different adventure" in body
    assert not tuple((target_root / "beta" / "archives").glob("*.journal.json"))


def _exported_playthrough(root: Path, directory: str = "alpha") -> str:
    adventure_path = root / directory / "adventure.json"
    adventure = load_adventure(adventure_path)
    state_path = root / directory / "play-state.json"
    save_play_state(
        state_path,
        record_visit(adventure, new_play_state(adventure), "alpha"),
    )
    workspace = LocalAdventureWorkspace(root)
    workspace.select_initial_adventure(adventure_path)
    app = compose_workspace_web_application(workspace)
    selected = workspace.load().selected_adventure
    assert selected is not None
    delegate = app.adventure_application(selected.key, app.csrf_token)
    assert delegate.archive_queries is not None
    revision = delegate.archive_queries.list_archives().revision.value
    status, _, exported = request_wsgi(
        app,
        "/archives/export-active",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": revision,
            "label": "Session One",
            "name": "session-one",
        },
    )
    assert status == "200 OK"
    return exported


def test_catalog_imports_playthrough_into_matching_unselected_adventure(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    _write_project(source_root, "alpha", "Alpha Adventure")
    exported = _exported_playthrough(source_root)
    source_adventure = load_adventure(source_root / "alpha" / "adventure.json")

    matching_project = target_root / "renamed-copy"
    matching_project.mkdir()
    save_adventure(matching_project / "adventure.json", source_adventure)
    matching_active = record_visit(
        source_adventure,
        new_play_state(source_adventure),
        "alpha",
        notes=("Keep this active journal.",),
    )
    save_play_state(matching_project / "play-state.json", matching_active)
    _write_project(target_root, "beta", "Selected Adventure")
    beta_state_path = target_root / "beta" / "play-state.json"
    beta_state = load_play_state(beta_state_path)

    workspace = LocalAdventureWorkspace(target_root)
    workspace.select_initial_adventure(target_root / "beta" / "adventure.json")
    app = compose_workspace_web_application(workspace)
    revision = workspace.load().revision.value

    status, headers, _ = request_wsgi(
        app,
        "/adventures/playthroughs/import",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": revision,
        },
        files={
            "archive_file": (
                "session-one.journal.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/adventures?playthrough-imported=1"
    assert (matching_project / "archives" / "session-one.journal.json").is_file()
    assert load_play_state(matching_project / "play-state.json") == matching_active
    assert load_play_state(beta_state_path) == beta_state
    assert workspace.load().settings.selected_adventure_key == "beta/adventure.json"

    status, _, body = request_wsgi(app, "/adventures", query="playthrough-imported=1")
    assert status == "200 OK"
    assert "Playthrough imported" in body
    assert "without changing the selected adventure or active journal" in body

    status, _, body = request_wsgi(
        app,
        "/adventures/playthroughs/import",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": workspace.load().revision.value,
        },
        files={
            "archive_file": (
                "session-one.journal.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )
    assert status == "422 Unprocessable Content"
    assert "Playthrough was not imported" in body
    assert "already present" in body


def test_catalog_playthrough_import_rejects_missing_adventure_without_side_effects(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    _write_project(source_root, "alpha", "Alpha Adventure")
    exported = _exported_playthrough(source_root)
    _write_project(target_root, "beta", "Other Adventure")

    workspace = LocalAdventureWorkspace(target_root)
    app = compose_workspace_web_application(workspace)
    before = workspace.load()
    state_path = target_root / "beta" / "play-state.json"
    state_before = load_play_state(state_path)

    status, _, body = request_wsgi(
        app,
        "/adventures/playthroughs/import",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": before.revision.value,
        },
        files={
            "archive_file": (
                "session-one.journal.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )

    assert status == "422 Unprocessable Content"
    assert "Import the matching adventure first" in body
    assert workspace.load().settings == before.settings
    assert load_play_state(state_path) == state_before
    assert not (target_root / "beta" / "archives").exists()


def test_catalog_playthrough_import_rejects_ambiguous_adventure_identity(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    _write_project(source_root, "alpha", "Alpha Adventure")
    exported = _exported_playthrough(source_root)
    adventure = load_adventure(source_root / "alpha" / "adventure.json")

    for directory in ("copy-one", "copy-two"):
        project = target_root / directory
        project.mkdir()
        save_adventure(project / "adventure.json", adventure)
        save_play_state(project / "play-state.json", new_play_state(adventure))

    workspace = LocalAdventureWorkspace(target_root)
    workspace.select_initial_adventure(target_root / "copy-one" / "adventure.json")
    app = compose_workspace_web_application(workspace)
    before = workspace.load()

    status, _, body = request_wsgi(
        app,
        "/adventures/playthroughs/import",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": before.revision.value,
        },
        files={
            "archive_file": (
                "session-one.journal.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )

    assert status == "422 Unprocessable Content"
    assert "duplicate projects" in body
    assert workspace.load().settings == before.settings
    assert not tuple(target_root.glob("copy-*/archives/*.journal.json"))


def test_catalog_playthrough_import_rejects_stale_workspace_revision(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    _write_project(source_root, "alpha", "Alpha Adventure")
    exported = _exported_playthrough(source_root)
    source_adventure = load_adventure(source_root / "alpha" / "adventure.json")

    matching = target_root / "matching"
    matching.mkdir()
    save_adventure(matching / "adventure.json", source_adventure)
    save_play_state(matching / "play-state.json", new_play_state(source_adventure))
    _write_project(target_root, "beta", "Beta Adventure")

    workspace = LocalAdventureWorkspace(target_root)
    app = compose_workspace_web_application(workspace)
    stale_revision = workspace.load().revision.value
    workspace.select_initial_adventure(target_root / "beta" / "adventure.json")

    status, _, body = request_wsgi(
        app,
        "/adventures/playthroughs/import",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": stale_revision,
        },
        files={
            "archive_file": (
                "session-one.journal.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )

    assert status == "409 Conflict"
    assert "Adventure or archive catalog changed" in body
    assert 'action="/adventures/playthroughs/import"' in body
    assert not (matching / "archives").exists()


def test_catalog_import_forms_recover_from_malformed_and_oversize_documents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    _write_project(root, "alpha", "Alpha Adventure")
    workspace = LocalAdventureWorkspace(root)
    app = compose_workspace_web_application(workspace)

    status, _, body = request_wsgi(
        app,
        "/adventures/import",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": workspace.load().revision.value,
        },
        files={
            "adventure_file": (
                "broken.adventure.json",
                b"{",
                "application/json",
            )
        },
    )

    assert status == "422 Unprocessable Content"
    assert "Adventure was not imported" in body
    assert 'action="/adventures/import"' in body
    assert 'role="alert"' in body

    oversized_content = b"x" * (MAX_CANONICAL_JSON_BYTES + 1)
    status, _, body = request_wsgi(
        app,
        "/adventures/playthroughs/import",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": workspace.load().revision.value,
        },
        files={
            "archive_file": (
                "large.journal.json",
                oversized_content,
                "application/json",
            )
        },
    )

    assert status == "413 Content Too Large"
    assert "Playthrough file too large" in body
    assert f"may not exceed {MAX_CANONICAL_JSON_BYTES:,} bytes" in body
    assert 'action="/adventures/playthroughs/import"' in body


def test_selected_archive_workspace_explains_empty_export_and_recovers_upload_errors(
    tmp_path: Path,
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    _write_project(root, "alpha", "Alpha Adventure")
    workspace = LocalAdventureWorkspace(root)
    app = compose_workspace_web_application(workspace)

    status, _, body = request_wsgi(app, "/archives")

    assert status == "200 OK"
    assert "The active journal is empty" in body
    assert "Record play before exporting or archiving it" in body
    assert "Export current playthrough" not in body
    assert "Import for this adventure" in body
    assert "Its adventure identity must match this adventure" in body

    selected = workspace.load().selected_adventure
    assert selected is not None
    delegate = app.adventure_application(selected.key, app.csrf_token)
    assert delegate.archive_queries is not None
    revision = delegate.archive_queries.list_archives().revision.value
    status, _, body = request_wsgi(
        app,
        "/archives/import",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": revision,
        },
        files={"archive_file": ("empty.json", b"", "application/json")},
    )

    assert status == "400 Bad Request"
    assert "Playthrough upload could not be read" in body
    assert "Choose a nonempty JSON file" in body
    assert 'action="/archives/import"' in body
    assert 'role="alert"' in body


@pytest.mark.parametrize(
    ("failure", "expected_message"),
    [
        (
            OSError("cannot write /Users/grant/private/workspace/archives/session-one.json"),
            "Check workspace permissions and available disk space",
        ),
        (
            UnsafeFilesystemLayoutError("unsafe symlink /Users/grant/private/workspace/archives"),
            "Remove symlinks or unsupported entries",
        ),
    ],
)
def test_catalog_playthrough_import_contains_local_storage_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: BaseException,
    expected_message: str,
) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    _write_project(source_root, "alpha", "Alpha Adventure")
    exported = _exported_playthrough(source_root)
    source_adventure = load_adventure(source_root / "alpha" / "adventure.json")

    target_project = target_root / "matching"
    target_project.mkdir()
    save_adventure(target_project / "adventure.json", source_adventure)
    save_play_state(target_project / "play-state.json", new_play_state(source_adventure))
    workspace = LocalAdventureWorkspace(target_root)
    app = compose_workspace_web_application(workspace)

    def fail_to_save(*_args: object, **_kwargs: object) -> None:
        raise failure

    monkeypatch.setattr(LocalJournalArchiveProject, "import_archive", fail_to_save)
    status, _, body = request_wsgi(
        app,
        "/adventures/playthroughs/import",
        "POST",
        form={
            "csrf_token": app.csrf_token,
            "expected_revision": workspace.load().revision.value,
        },
        files={
            "archive_file": (
                "session-one.journal.json",
                exported.encode("utf-8"),
                "application/json",
            )
        },
    )

    assert status == "500 Internal Server Error"
    assert "Playthrough could not be saved" in body
    assert expected_message in body
    assert "/Users/grant/private" not in body
    assert not (target_project / "archives" / "session-one.journal.json").exists()
