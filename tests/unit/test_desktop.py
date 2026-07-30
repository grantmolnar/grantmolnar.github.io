"""Tests for desktop launcher lifecycle ownership."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from wsgiref.types import WSGIApplication

import pytest

from adventure_graph import desktop
from adventure_graph.desktop import DesktopSession, _read_when_ready, _run_smoke_test, main
from adventure_graph.infrastructure.desktop_settings import DesktopLauncherSettings


@dataclass
class MemorySettingsStore:
    settings: DesktopLauncherSettings = field(default_factory=DesktopLauncherSettings)
    saved: list[DesktopLauncherSettings] = field(default_factory=list)

    def load(self) -> DesktopLauncherSettings:
        return self.settings

    def save(self, settings: DesktopLauncherSettings) -> None:
        self.settings = settings
        self.saved.append(settings)


@dataclass
class FakeServer:
    url: str
    stopped: bool = False

    def shutdown(self) -> None:
        self.stopped = True


def test_session_remembers_reopens_and_replaces_one_owned_workspace(tmp_path: Path) -> None:
    first_workspace = tmp_path / "first"
    second_workspace = tmp_path / "second"
    first_workspace.mkdir()
    second_workspace.mkdir()
    settings = MemorySettingsStore()
    servers: list[FakeServer] = []
    opened: list[str] = []

    def server_factory(_app: WSGIApplication) -> FakeServer:
        server = FakeServer(f"http://127.0.0.1:{41000 + len(servers)}/")
        servers.append(server)
        return server

    session = DesktopSession(
        settings_store=settings,
        server_factory=server_factory,
        browser_open=opened.append,
    )

    first_url = session.open_workspace(first_workspace)
    session.open_browser()
    second_url = session.open_workspace(second_workspace, open_browser=False)

    assert first_url == "http://127.0.0.1:41000/"
    assert second_url == "http://127.0.0.1:41001/"
    assert servers[0].stopped
    assert not servers[1].stopped
    assert opened == [first_url, first_url]
    assert settings.saved == [
        DesktopLauncherSettings(first_workspace.resolve()),
        DesktopLauncherSettings(second_workspace.resolve()),
    ]
    assert session.remembered_workspace() == second_workspace.resolve()

    session.close()
    assert servers[1].stopped
    assert session.url is None


def test_browser_failure_keeps_the_owned_server_available_for_retry(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    server = FakeServer("http://127.0.0.1:41000/")
    session = DesktopSession(
        settings_store=MemorySettingsStore(),
        server_factory=lambda _app: server,
        browser_open=lambda _url: False,
    )

    with pytest.raises(RuntimeError, match="default browser"):
        session.open_workspace(workspace)

    assert session.url == server.url
    assert not server.stopped
    session.close()


def test_session_rejects_missing_or_non_directory_workspaces(tmp_path: Path) -> None:
    session = DesktopSession(settings_store=MemorySettingsStore())

    with pytest.raises(FileNotFoundError, match="does not exist"):
        session.open_workspace(tmp_path / "missing", open_browser=False)

    file_path = tmp_path / "not-a-workspace"
    file_path.write_text("x")
    with pytest.raises(ValueError, match="must be a directory"):
        session.open_workspace(file_path, open_browser=False)


def test_remembered_workspace_ignores_a_path_that_no_longer_exists(tmp_path: Path) -> None:
    missing = tmp_path / "moved"
    session = DesktopSession(settings_store=MemorySettingsStore(DesktopLauncherSettings(missing)))

    assert session.remembered_workspace() is None


def test_headless_desktop_smoke_serves_an_empty_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    assert _run_smoke_test(workspace) == 0


def test_headless_desktop_smoke_returns_failure_without_a_window(
    tmp_path: Path,
) -> None:
    assert main(["--smoke-test", str(tmp_path / "missing")]) == 1


@dataclass
class FailingSettingsStore(MemorySettingsStore):
    def save(self, _settings: DesktopLauncherSettings) -> None:
        raise OSError("simulated settings failure")


def test_settings_failure_closes_the_new_server_and_clears_session_state(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    server = FakeServer("http://127.0.0.1:41000/")
    session = DesktopSession(
        settings_store=FailingSettingsStore(),
        server_factory=lambda _app: server,
        browser_open=lambda _url: True,
    )

    with pytest.raises(OSError, match="settings failure"):
        session.open_workspace(workspace)

    assert server.stopped
    assert session.workspace is None
    assert session.url is None


def test_open_browser_requires_an_owned_workspace() -> None:
    session = DesktopSession(settings_store=MemorySettingsStore())

    with pytest.raises(RuntimeError, match="Choose a workspace"):
        session.open_browser()


def test_main_forwards_graphical_workspace_and_browser_preference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    calls: list[tuple[Path | None, bool]] = []

    def run_window(candidate: Path | None, *, open_browser: bool) -> int:
        calls.append((candidate, open_browser))
        return 7

    monkeypatch.setattr(desktop, "_run_window", run_window)

    assert main([str(workspace), "--no-browser"]) == 7
    assert calls == [(workspace, False)]


def test_headless_smoke_rejects_an_unexpected_page_and_still_closes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setattr(desktop, "_read_when_ready", lambda _url: b"not the application")

    with pytest.raises(RuntimeError, match="unexpected page"):
        _run_smoke_test(workspace)


def test_read_when_ready_retries_a_transient_url_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    class Response:
        status = 200

        def __enter__(self) -> Response:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b"Adventure Graph"

    def urlopen(_url: str, *, timeout: int) -> Response:
        nonlocal calls
        calls += 1
        assert timeout == 1
        if calls == 1:
            raise desktop.urllib.error.URLError("not ready")
        return Response()

    monkeypatch.setattr(desktop.urllib.request, "urlopen", urlopen)
    monkeypatch.setattr(desktop.time, "sleep", lambda _seconds: None)

    assert _read_when_ready("http://127.0.0.1:41000/") == b"Adventure Graph"
    assert calls == 2


def test_read_when_ready_rejects_non_success_and_reports_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BadResponse:
        status = 503

        def __enter__(self) -> BadResponse:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

    monkeypatch.setattr(desktop.urllib.request, "urlopen", lambda *_args, **_kwargs: BadResponse())
    with pytest.raises(RuntimeError, match="HTTP 503"):
        _read_when_ready("http://127.0.0.1:41000/")

    moments = iter((0.0, 0.0, 6.0))
    monkeypatch.setattr(desktop.time, "monotonic", lambda: next(moments))
    monkeypatch.setattr(desktop.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        desktop.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            desktop.urllib.error.URLError("still unavailable")
        ),
    )
    with pytest.raises(RuntimeError, match="did not become ready") as raised:
        _read_when_ready("http://127.0.0.1:41000/")
    assert isinstance(raised.value.__cause__, desktop.urllib.error.URLError)
