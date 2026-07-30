"""Tests for per-user desktop-launcher settings."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adventure_graph.infrastructure.desktop_settings import (
    DesktopLauncherSettings,
    LocalDesktopSettingsStore,
    desktop_settings_path,
)


def test_settings_paths_follow_each_platform_convention(tmp_path: Path) -> None:
    assert (
        desktop_settings_path(platform="linux", environment={}, home=tmp_path)
        == tmp_path / ".config" / "adventure-graph" / "launcher-settings.json"
    )
    assert desktop_settings_path(platform="darwin", environment={}, home=tmp_path) == (
        tmp_path / "Library" / "Application Support" / "Adventure Graph" / "launcher-settings.json"
    )
    assert desktop_settings_path(platform="win32", environment={}, home=tmp_path) == (
        tmp_path / "AppData" / "Local" / "Adventure Graph" / "launcher-settings.json"
    )


def test_environment_override_keeps_settings_outside_the_bundle(tmp_path: Path) -> None:
    config = tmp_path / "isolated-config"

    assert desktop_settings_path(environment={"ADVENTURE_GRAPH_CONFIG_HOME": str(config)}) == (
        config / "launcher-settings.json"
    )


def test_store_round_trips_the_selected_workspace(tmp_path: Path) -> None:
    path = tmp_path / "config" / "launcher-settings.json"
    workspace = tmp_path / "adventures"
    workspace.mkdir()
    store = LocalDesktopSettingsStore(path)

    assert store.load() == DesktopLauncherSettings()
    store.save(DesktopLauncherSettings(workspace))

    assert store.load() == DesktopLauncherSettings(workspace.resolve())
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"schema_version": 1, "workspace": str(workspace)}


def test_store_rejects_unknown_or_future_settings(tmp_path: Path) -> None:
    path = tmp_path / "launcher-settings.json"
    path.write_text('{"schema_version": 1, "workspace": null, "future": true}\n')

    with pytest.raises(ValueError, match="Unsupported field"):
        LocalDesktopSettingsStore(path).load()

    path.write_text('{"schema_version": 2, "workspace": null}\n')
    with pytest.raises(ValueError, match="unsupported desktop settings"):
        LocalDesktopSettingsStore(path).load()
