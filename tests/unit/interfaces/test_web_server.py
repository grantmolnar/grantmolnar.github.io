"""Tests for loopback-only web server hosting."""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from typing import Any
from wsgiref.types import WSGIApplication

import pytest

import adventure_graph.interfaces.web.server as web_server


@dataclass
class FakeServer:
    """Scoped server that terminates immediately through KeyboardInterrupt."""

    app: WSGIApplication
    host: str
    port: int
    url: str = "http://localhost:43210/"
    entered: bool = False
    served: bool = False
    stopped: bool = False

    def __enter__(self) -> FakeServer:
        self.entered = True
        return self

    def __exit__(self, *args: object) -> None:
        del args
        self.stopped = True

    def serve_forever(self) -> None:
        self.served = True
        raise KeyboardInterrupt


def _app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
    del environ
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"ready"]


def test_server_refuses_non_loopback_hosts_and_invalid_ports() -> None:
    with pytest.raises(ValueError, match="bind only"):
        web_server.serve_web_app(_app, host="0.0.0.0", open_browser=False)
    with pytest.raises(ValueError, match="between 0 and 65535"):
        web_server.serve_web_app(_app, port=70000, open_browser=False)


def test_server_announces_opens_and_stops_cleanly(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    created: list[FakeServer] = []
    opened: list[str] = []

    def fake_server(app: WSGIApplication, *, host: str, port: int) -> FakeServer:
        server = FakeServer(app, host, port)
        created.append(server)
        return server

    monkeypatch.setattr(web_server, "LoopbackWebServer", fake_server)
    monkeypatch.setattr(web_server.webbrowser, "open", opened.append)

    web_server.serve_web_app(_app, host="localhost", port=0)

    assert len(created) == 1
    assert created[0].host == "localhost"
    assert created[0].port == 0
    assert created[0].entered
    assert created[0].served
    assert created[0].stopped
    assert opened == ["http://localhost:43210/"]
    output = capsys.readouterr().out
    assert "Adventure Graph UI: http://localhost:43210/" in output
    assert "Adventure Graph UI stopped." in output


def test_background_server_owns_an_available_port_and_stops() -> None:
    server = web_server.start_web_app(_app)
    try:
        assert server.is_running
        with urllib.request.urlopen(server.url, timeout=2) as response:
            assert response.status == 200
            assert response.read() == b"ready"
    finally:
        server.shutdown()

    assert not server.is_running
    server.shutdown()
