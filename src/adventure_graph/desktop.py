"""Thin desktop launcher around the existing loopback browser application."""

from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request
import webbrowser
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol
from wsgiref.types import WSGIApplication

from adventure_graph.infrastructure.desktop_settings import (
    DesktopLauncherSettings,
    LocalDesktopSettingsStore,
)
from adventure_graph.infrastructure.local_adventure_workspace import LocalAdventureWorkspace
from adventure_graph.interfaces.web.server import LoopbackWebServer, start_web_app
from adventure_graph.web_composition import compose_workspace_web_application

_BROWSER_TIMEOUT_SECONDS = 5.0


class _SettingsStore(Protocol):
    def load(self) -> DesktopLauncherSettings:
        """Load launcher settings."""
        ...

    def save(self, settings: DesktopLauncherSettings) -> None:
        """Persist launcher settings."""
        ...


class _OwnedServer(Protocol):
    @property
    def url(self) -> str:
        """Return the local application URL."""
        ...

    def shutdown(self) -> None:
        """Stop and release the server."""
        ...


class DesktopSession:
    """Own the selected workspace, its loopback server, and browser reopening."""

    def __init__(
        self,
        *,
        settings_store: _SettingsStore | None = None,
        server_factory: Callable[[WSGIApplication], _OwnedServer] | None = None,
        browser_open: Callable[[str], object] = webbrowser.open,
    ) -> None:
        self._settings_store = settings_store or LocalDesktopSettingsStore()
        self._server_factory = server_factory or _start_workspace_server
        self._browser_open = browser_open
        self._server: _OwnedServer | None = None
        self._workspace: Path | None = None

    @property
    def workspace(self) -> Path | None:
        """Return the currently served workspace root."""
        return self._workspace

    @property
    def url(self) -> str | None:
        """Return the current browser URL, if a workspace is running."""
        return None if self._server is None else self._server.url

    def remembered_workspace(self) -> Path | None:
        """Return the last existing workspace selected by this user."""
        workspace = self._settings_store.load().workspace
        if workspace is None or not workspace.is_dir():
            return None
        return workspace.resolve()

    def open_workspace(
        self,
        workspace: Path,
        *,
        remember: bool = True,
        open_browser: bool = True,
    ) -> str:
        """Replace the owned server with one serving the requested workspace."""
        resolved = workspace.expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(f"Workspace does not exist: {resolved}.")
        if not resolved.is_dir():
            raise ValueError(f"Workspace must be a directory: {resolved}.")

        self.close()
        app = compose_workspace_web_application(LocalAdventureWorkspace(resolved))
        server = self._server_factory(app)
        self._server = server
        self._workspace = resolved
        try:
            if remember:
                self._settings_store.save(DesktopLauncherSettings(resolved))
        except Exception:
            self.close()
            raise
        if open_browser:
            self.open_browser()
        return server.url

    def open_browser(self) -> None:
        """Open another browser tab for the currently running workspace."""
        if self._server is None:
            raise RuntimeError("Choose a workspace before opening Adventure Graph.")
        opened = self._browser_open(self._server.url)
        if opened is False:
            raise RuntimeError("The default browser could not be opened.")

    def close(self) -> None:
        """Stop the owned server, if any."""
        server = self._server
        self._server = None
        self._workspace = None
        if server is not None:
            server.shutdown()


def main(argv: Sequence[str] | None = None) -> int:
    """Run the graphical launcher or its packaged headless smoke mode."""
    args = _parse_args(argv)
    if args.smoke_test is not None:
        try:
            return _run_smoke_test(args.smoke_test)
        except (OSError, RuntimeError, ValueError):
            return 1
    return _run_window(args.workspace, open_browser=not args.no_browser)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="adventure-graph-desktop",
        description="Open Adventure Graph without installing or using a command line.",
    )
    parser.add_argument("workspace", nargs="?", type=Path)
    parser.add_argument("--no-browser", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--smoke-test", type=Path, help=argparse.SUPPRESS)
    return parser.parse_args(argv)


def _start_workspace_server(app: WSGIApplication) -> LoopbackWebServer:
    return start_web_app(app, host="127.0.0.1", port=0)


def _run_smoke_test(workspace: Path) -> int:
    session = DesktopSession(browser_open=lambda _url: None)
    try:
        url = session.open_workspace(workspace, remember=False, open_browser=False)
        body = _read_when_ready(url)
        if b"Adventure Graph" not in body:
            raise RuntimeError("The packaged desktop server returned an unexpected page.")
    finally:
        session.close()
    return 0


def _read_when_ready(url: str) -> bytes:
    deadline = time.monotonic() + _BROWSER_TIMEOUT_SECONDS
    last_error: OSError | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.status != 200:
                    raise RuntimeError(
                        f"The packaged desktop server returned HTTP {response.status}."
                    )
                return response.read()
        except urllib.error.URLError as error:
            last_error = error
            time.sleep(0.05)
    raise RuntimeError("The packaged desktop server did not become ready.") from last_error


def _run_window(initial_workspace: Path | None, *, open_browser: bool) -> int:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("Adventure Graph")
    root.minsize(560, 240)
    root.geometry("640x260")

    session = DesktopSession()
    path_text = tk.StringVar(value="No workspace selected")
    status_text = tk.StringVar(value="Choose a folder that will contain your adventures.")

    frame = ttk.Frame(root, padding=24)
    frame.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)

    ttk.Label(frame, text="Adventure Graph", font=("TkDefaultFont", 18, "bold")).grid(
        row=0, column=0, sticky="w"
    )
    ttk.Label(
        frame,
        text="Keep this small launcher open while you use the browser interface.",
    ).grid(row=1, column=0, sticky="w", pady=(4, 16))
    ttk.Label(frame, textvariable=path_text, wraplength=580).grid(row=2, column=0, sticky="w")
    ttk.Label(frame, textvariable=status_text, wraplength=580).grid(
        row=3, column=0, sticky="w", pady=(6, 18)
    )

    buttons = ttk.Frame(frame)
    buttons.grid(row=4, column=0, sticky="w")

    open_button = ttk.Button(buttons, text="Open in browser", state="disabled")
    open_button.grid(row=0, column=0, padx=(0, 8))
    choose_button = ttk.Button(buttons, text="Choose workspace…")
    choose_button.grid(row=0, column=1, padx=(0, 8))
    quit_button = ttk.Button(buttons, text="Quit")
    quit_button.grid(row=0, column=2)

    def report_error(error: BaseException) -> None:
        messagebox.showerror("Adventure Graph", str(error), parent=root)
        status_text.set("Adventure Graph is not running.")

    def update_running_state() -> None:
        workspace = session.workspace
        path_text.set("No workspace selected" if workspace is None else str(workspace))
        if session.url is None:
            status_text.set("Choose a folder that will contain your adventures.")
            open_button.configure(state="disabled")
        else:
            status_text.set("Running locally. Close this launcher to stop Adventure Graph.")
            open_button.configure(state="normal")

    def open_selected(workspace: Path) -> None:
        try:
            session.open_workspace(workspace, open_browser=open_browser)
        except (OSError, RuntimeError, ValueError) as error:
            report_error(error)
        update_running_state()

    def choose_workspace() -> None:
        current = session.workspace
        selected = filedialog.askdirectory(
            parent=root,
            title="Choose an Adventure Graph workspace",
            initialdir=str(current or Path.home()),
            mustexist=True,
        )
        if selected:
            open_selected(Path(selected))

    def reopen_browser() -> None:
        try:
            session.open_browser()
        except RuntimeError as error:
            report_error(error)

    def close_window() -> None:
        try:
            session.close()
        finally:
            root.destroy()

    open_button.configure(command=reopen_browser)
    choose_button.configure(command=choose_workspace)
    quit_button.configure(command=close_window)
    root.protocol("WM_DELETE_WINDOW", close_window)

    candidate = initial_workspace
    if candidate is None:
        try:
            candidate = session.remembered_workspace()
        except (OSError, ValueError) as error:
            report_error(error)
    if candidate is not None:
        root.after_idle(lambda: open_selected(candidate))
    else:
        root.after_idle(choose_workspace)

    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
