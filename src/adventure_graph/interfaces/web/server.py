"""Loopback-only server lifecycle for local browser interfaces."""

from __future__ import annotations

import webbrowser
from threading import Thread
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server
from wsgiref.types import WSGIApplication

_ALLOWED_HOSTS = ("127.0.0.1", "localhost")


class QuietRequestHandler(WSGIRequestHandler):
    """Suppress default per-request stderr logging in the local authoring shell."""

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002 -- match the base override signature.
        """Discard routine local request logs."""
        del format, args


class LoopbackWebServer:
    """Own one bound loopback WSGI server and its optional background thread."""

    def __init__(
        self,
        app: WSGIApplication,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        _validate_bind_target(host, port)
        self._server: WSGIServer = make_server(
            host,
            port,
            app,
            handler_class=QuietRequestHandler,
        )
        self._thread: Thread | None = None
        self._closed = False

    @property
    def url(self) -> str:
        """Return the bound browser URL, including an operating-system-selected port."""
        return f"http://{self._server.server_address[0]}:{self._server.server_port}/"

    @property
    def is_running(self) -> bool:
        """Return whether the owned background server thread is alive."""
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        """Serve in one owned daemon thread."""
        if self._closed:
            raise RuntimeError("The local server has already been closed.")
        if self._thread is not None:
            raise RuntimeError("The local server has already been started.")
        self._thread = Thread(
            target=self._server.serve_forever,
            name="adventure-graph-loopback-server",
            daemon=True,
        )
        self._thread.start()

    def serve_forever(self) -> None:
        """Serve synchronously until interrupted or shut down elsewhere."""
        if self._closed:
            raise RuntimeError("The local server has already been closed.")
        if self._thread is not None:
            raise RuntimeError("The local server is already running in the background.")
        self._server.serve_forever()

    def shutdown(self) -> None:
        """Stop the owned server, join its thread, and release the bound socket."""
        if self._closed:
            return
        thread = self._thread
        if thread is not None and thread.is_alive():
            self._server.shutdown()
            thread.join(timeout=5)
            if thread.is_alive():
                raise RuntimeError("The local server did not stop cleanly.")
        self._server.server_close()
        self._closed = True

    def __enter__(self) -> LoopbackWebServer:
        """Return this server for scoped lifecycle ownership."""
        return self

    def __exit__(self, *_exc_info: object) -> None:
        """Release the server socket at scope exit."""
        self.shutdown()


def start_web_app(
    app: WSGIApplication,
    *,
    host: str = "127.0.0.1",
    port: int = 0,
) -> LoopbackWebServer:
    """Bind and start one background loopback server."""
    server = LoopbackWebServer(app, host=host, port=port)
    server.start()
    return server


def serve_web_app(
    app: WSGIApplication,
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    """Serve the application on loopback until interrupted."""
    with LoopbackWebServer(app, host=host, port=port) as server:
        print(f"Adventure Graph UI: {server.url}")
        print("Press Ctrl+C to stop the local server.")
        if open_browser:
            webbrowser.open(server.url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nAdventure Graph UI stopped.")


def _validate_bind_target(host: str, port: int) -> None:
    if host not in _ALLOWED_HOSTS:
        raise ValueError("The local UI may bind only to 127.0.0.1 or localhost.")
    if not 0 <= port <= 65535:
        raise ValueError("Port must be between 0 and 65535.")
