"""Focused tests for workspace-owned routing and selected-adventure delegation."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from typing import cast
from urllib.parse import urlencode

from adventure_graph.application.errors import TransferStorageError
from adventure_graph.application.project import RevisionConflictError
from adventure_graph.application.project_browsing import AdventureOverviewResult
from adventure_graph.application.workspace_management import (
    AdventureCatalogEntry,
    WorkspaceRevision,
    WorkspaceSettings,
    WorkspaceSnapshot,
)
from adventure_graph.interfaces.web.contracts import (
    DownloadDocument,
    WorkspaceCommands,
    WorkspaceQueries,
)
from adventure_graph.interfaces.web.workspace_app import WorkspaceWebApplication
from tests.support.web import (
    CapturedWSGIResponse,
    WSGIRequestEnvironment,
    WSGIStartResponse,
    build_wsgi_environ,
    request_wsgi,
)


@dataclass
class _DelegatedBody:
    chunks: tuple[bytes, ...]
    iterated: bool = False
    closed: bool = False

    def __iter__(self) -> Iterator[bytes]:
        self.iterated = True
        yield from self.chunks

    def close(self) -> None:
        self.closed = True


@dataclass
class _DelegatedApplication:
    body: _DelegatedBody
    response_headers: list[tuple[str, str]]
    received_environ: WSGIRequestEnvironment | None = None

    def __call__(
        self,
        environ: WSGIRequestEnvironment,
        start_response: WSGIStartResponse,
    ) -> Iterable[bytes]:
        self.received_environ = environ
        start_response("206 Partial Content", self.response_headers)
        return self.body


def _workspace_snapshot() -> WorkspaceSnapshot:
    entry = AdventureCatalogEntry("alpha/adventure.json", "Alpha", "Selected adventure.")
    return WorkspaceSnapshot(
        adventures=(entry,),
        settings=WorkspaceSettings(selected_adventure_key=entry.key),
        revision=WorkspaceRevision("workspace-revision"),
    )


def test_selected_adventure_response_is_passed_through_without_buffering() -> None:
    delegated_body = _DelegatedBody((b"\xffbinary", b"\x00tail"))
    delegated_headers = [
        ("Content-Type", "application/octet-stream"),
        ("Content-Length", "12"),
        ("Cache-Control", "private"),
        ("Content-Security-Policy", "sandbox"),
        ("X-Delegated", "unchanged"),
    ]
    delegated = _DelegatedApplication(delegated_body, delegated_headers)
    snapshot = _workspace_snapshot()
    workspace_loads = 0

    def get_workspace() -> WorkspaceSnapshot:
        nonlocal workspace_loads
        workspace_loads += 1
        return snapshot

    application = WorkspaceWebApplication(
        queries=WorkspaceQueries(
            get_workspace=get_workspace,
            get_adventure_overview=lambda _key: cast(AdventureOverviewResult, object()),
            export_adventure=lambda _key: cast(DownloadDocument, object()),
        ),
        commands=cast(WorkspaceCommands, object()),
        adventure_application=lambda _key, _token: delegated,
        workspace_label="Test workspace",
        csrf_token="test-token",
    )
    environ = build_wsgi_environ("/binary", query="kind=raw")
    captured = CapturedWSGIResponse()

    response = application(environ, cast(WSGIStartResponse, captured.start_response))

    assert response is delegated_body
    assert not delegated_body.iterated
    assert delegated.received_environ is environ
    assert workspace_loads == 1
    assert captured.status == "206 Partial Content"
    assert captured.headers == delegated_headers
    assert list(response) == [b"\xffbinary", b"\x00tail"]
    delegated_body.close()
    assert delegated_body.closed


def test_workspace_rejects_non_loopback_host_before_loading_catalog() -> None:
    loads = 0

    def get_workspace() -> WorkspaceSnapshot:
        nonlocal loads
        loads += 1
        return _workspace_snapshot()

    application = WorkspaceWebApplication(
        queries=WorkspaceQueries(
            get_workspace=get_workspace,
            get_adventure_overview=lambda _key: cast(AdventureOverviewResult, object()),
            export_adventure=lambda _key: cast(DownloadDocument, object()),
        ),
        commands=cast(WorkspaceCommands, object()),
        adventure_application=lambda _key, _token: cast(_DelegatedApplication, object()),
        workspace_label="Test workspace",
        csrf_token="test-token",
    )
    environ = build_wsgi_environ("/adventures", host_authority="attacker.example")
    captured = CapturedWSGIResponse()

    body = b"".join(application(environ, cast(WSGIStartResponse, captured.start_response)))

    assert captured.status == "421 Misdirected Request"
    assert b"Request host rejected" in body
    assert b"Test workspace" not in body
    assert loads == 0


def test_workspace_rejects_malformed_query_before_loading_catalog() -> None:
    loads = 0

    def get_workspace() -> WorkspaceSnapshot:
        nonlocal loads
        loads += 1
        return _workspace_snapshot()

    application = WorkspaceWebApplication(
        queries=WorkspaceQueries(
            get_workspace=get_workspace,
            get_adventure_overview=lambda _key: cast(AdventureOverviewResult, object()),
            export_adventure=lambda _key: cast(DownloadDocument, object()),
        ),
        commands=cast(WorkspaceCommands, object()),
        adventure_application=lambda _key, _token: cast(_DelegatedApplication, object()),
        workspace_label="/Users/grant/private/workspace",
        csrf_token="test-token",
    )

    status, _, body = request_wsgi(application, "/adventures", query="saved=%ZZ")

    assert status == "400 Bad Request"
    assert "Query string rejected" in body
    assert "/Users/grant/private/workspace" not in body
    assert loads == 0


def test_workspace_contains_internal_catalog_failures_without_disclosing_paths() -> None:
    def get_workspace() -> WorkspaceSnapshot:
        raise OSError("cannot read /Users/grant/private/workspace/settings.json")

    application = WorkspaceWebApplication(
        queries=WorkspaceQueries(
            get_workspace=get_workspace,
            get_adventure_overview=lambda _key: cast(AdventureOverviewResult, object()),
            export_adventure=lambda _key: cast(DownloadDocument, object()),
        ),
        commands=cast(WorkspaceCommands, object()),
        adventure_application=lambda _key, _token: cast(_DelegatedApplication, object()),
        workspace_label="/Users/grant/private/workspace",
        csrf_token="test-token",
    )

    status, _, body = request_wsgi(application, "/adventures")

    assert status == "500 Internal Server Error"
    assert "Workspace could not be loaded" in body
    assert "/Users/grant/private" not in body
    assert "OSError" not in body


def test_sample_storage_failure_is_logged_and_rendered_without_local_paths() -> None:
    snapshot = _workspace_snapshot()

    def create_sample_adventure(_revision: WorkspaceRevision) -> object:
        try:
            raise OSError("cannot write /Users/grant/private/workspace/the-glass-saint")
        except OSError as cause:
            raise TransferStorageError(
                "Adventure Graph could not save the sample adventure. Check workspace "
                "permissions and available disk space, then retry."
            ) from cause

    application = WorkspaceWebApplication(
        queries=WorkspaceQueries(
            get_workspace=lambda: snapshot,
            get_adventure_overview=lambda _key: cast(AdventureOverviewResult, object()),
            export_adventure=lambda _key: cast(DownloadDocument, object()),
        ),
        commands=cast(
            WorkspaceCommands,
            SimpleNamespace(create_sample_adventure=create_sample_adventure),
        ),
        adventure_application=lambda _key, _token: cast(_DelegatedApplication, object()),
        workspace_label="/Users/grant/private/workspace",
        csrf_token="test-token",
    )
    encoded = urlencode(
        {
            "csrf_token": "test-token",
            "expected_revision": snapshot.revision.value,
        }
    ).encode("utf-8")
    environ = build_wsgi_environ(
        "/adventures/sample",
        method="POST",
        body=encoded,
        content_type="application/x-www-form-urlencoded",
    )
    captured = CapturedWSGIResponse()

    body = b"".join(application(environ, captured.start_response)).decode("utf-8")

    assert captured.status == "500 Internal Server Error"
    assert "Workspace could not be updated" in body
    assert "Check workspace permissions" in body
    assert "/Users/grant/private" not in body
    stream = environ["wsgi.errors"]
    assert hasattr(stream, "getvalue")
    assert b"OSError" in stream.getvalue()
    assert b"/Users/grant/private/workspace/the-glass-saint" in stream.getvalue()


def test_catalog_playthrough_import_reports_project_revision_conflict_as_http_409() -> None:
    snapshot = _workspace_snapshot()

    def import_playthrough_document(
        _content: bytes,
        _revision: WorkspaceRevision,
    ) -> object:
        raise RevisionConflictError("The archive catalog changed; reload before importing.")

    commands = cast(
        WorkspaceCommands,
        SimpleNamespace(import_playthrough_document=import_playthrough_document),
    )
    application = WorkspaceWebApplication(
        queries=WorkspaceQueries(
            get_workspace=lambda: snapshot,
            get_adventure_overview=lambda _key: cast(AdventureOverviewResult, object()),
            export_adventure=lambda _key: cast(DownloadDocument, object()),
        ),
        commands=commands,
        adventure_application=lambda _key, _token: cast(_DelegatedApplication, object()),
        workspace_label="Test workspace",
        csrf_token="test-token",
    )

    status, _, body = request_wsgi(
        application,
        "/adventures/playthroughs/import",
        "POST",
        form={
            "csrf_token": "test-token",
            "expected_revision": snapshot.revision.value,
        },
        files={
            "archive_file": (
                "session-one.journal.json",
                b"{}",
                "application/json",
            )
        },
    )

    assert status == "409 Conflict"
    assert "Adventure or archive catalog changed" in body
    assert "archive catalog changed" in body
    assert 'action="/adventures/playthroughs/import"' in body
    assert 'role="alert"' in body


def test_catalog_playthrough_import_contains_storage_failures_without_disclosing_paths() -> None:
    snapshot = _workspace_snapshot()

    def import_playthrough_document(
        _content: bytes,
        _revision: WorkspaceRevision,
    ) -> object:
        try:
            raise OSError("cannot write /Users/grant/private/workspace/archives/run.json")
        except OSError as cause:
            raise TransferStorageError(
                "Adventure Graph could not save the imported playthrough. Check workspace "
                "permissions and available disk space, then retry."
            ) from cause

    commands = cast(
        WorkspaceCommands,
        SimpleNamespace(import_playthrough_document=import_playthrough_document),
    )
    application = WorkspaceWebApplication(
        queries=WorkspaceQueries(
            get_workspace=lambda: snapshot,
            get_adventure_overview=lambda _key: cast(AdventureOverviewResult, object()),
            export_adventure=lambda _key: cast(DownloadDocument, object()),
        ),
        commands=commands,
        adventure_application=lambda _key, _token: cast(_DelegatedApplication, object()),
        workspace_label="/Users/grant/private/workspace",
        csrf_token="test-token",
    )

    status, _, body = request_wsgi(
        application,
        "/adventures/playthroughs/import",
        "POST",
        form={
            "csrf_token": "test-token",
            "expected_revision": snapshot.revision.value,
        },
        files={
            "archive_file": (
                "session-one.journal.json",
                b"{}",
                "application/json",
            )
        },
    )

    assert status == "500 Internal Server Error"
    assert "Playthrough could not be saved" in body
    assert "Check workspace permissions" in body
    assert "/Users/grant/private" not in body
    assert "OSError" not in body


def test_catalog_playthrough_import_re_renders_malformed_upload_form() -> None:
    snapshot = _workspace_snapshot()
    commands = cast(WorkspaceCommands, SimpleNamespace())
    application = WorkspaceWebApplication(
        queries=WorkspaceQueries(
            get_workspace=lambda: snapshot,
            get_adventure_overview=lambda _key: cast(AdventureOverviewResult, object()),
            export_adventure=lambda _key: cast(DownloadDocument, object()),
        ),
        commands=commands,
        adventure_application=lambda _key, _token: cast(_DelegatedApplication, object()),
        workspace_label="Test workspace",
        csrf_token="test-token",
    )

    status, _, body = request_wsgi(
        application,
        "/adventures/playthroughs/import",
        "POST",
        form={
            "csrf_token": "test-token",
            "expected_revision": snapshot.revision.value,
        },
        files={"archive_file": ("empty.json", b"", "application/json")},
    )

    assert status == "400 Bad Request"
    assert "Playthrough upload could not be read" in body
    assert "Choose a nonempty JSON file" in body
    assert 'action="/adventures/playthroughs/import"' in body
    assert 'value="workspace-revision"' in body
