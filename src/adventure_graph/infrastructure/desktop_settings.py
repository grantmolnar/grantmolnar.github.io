"""Per-user settings for the lightweight desktop launcher."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from adventure_graph.infrastructure.atomic_files import write_json_object
from adventure_graph.infrastructure.json_values import (
    JsonObject,
    nullable_nonempty_string,
    read_object,
    reject_unknown_fields,
)

_SETTINGS_SCHEMA_VERSION = 1
_SETTINGS_FILENAME = "launcher-settings.json"
_ENVIRONMENT_OVERRIDE = "ADVENTURE_GRAPH_CONFIG_HOME"


@dataclass(frozen=True, slots=True)
class DesktopLauncherSettings:
    """The last workspace selected by the local desktop launcher."""

    workspace: Path | None = None


class LocalDesktopSettingsStore:
    """Load and atomically replace launcher settings outside the application bundle."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = (path or desktop_settings_path()).expanduser().resolve()

    def load(self) -> DesktopLauncherSettings:
        """Return persisted settings, or defaults when no settings file exists."""
        if not self.path.exists():
            return DesktopLauncherSettings()
        if self.path.is_symlink() or not self.path.is_file():
            raise ValueError(f"Desktop settings must be a regular file: {self.path}.")
        return desktop_settings_from_data(read_object(self.path), self.path)

    def save(self, settings: DesktopLauncherSettings) -> None:
        """Persist settings through the shared atomic local-file writer."""
        write_json_object(self.path, desktop_settings_data(settings))


def desktop_settings_path(
    *,
    platform: str | None = None,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the platform-appropriate per-user launcher settings path."""
    selected_platform = platform or sys.platform
    selected_environment = os.environ if environment is None else environment
    override = selected_environment.get(_ENVIRONMENT_OVERRIDE)
    if override:
        root = Path(override).expanduser()
    elif selected_platform == "win32":
        app_data = selected_environment.get("LOCALAPPDATA")
        root = Path(app_data) if app_data else (home or Path.home()) / "AppData" / "Local"
        root /= "Adventure Graph"
    elif selected_platform == "darwin":
        root = (home or Path.home()) / "Library" / "Application Support" / "Adventure Graph"
    else:
        config_home = selected_environment.get("XDG_CONFIG_HOME")
        root = Path(config_home) if config_home else (home or Path.home()) / ".config"
        root /= "adventure-graph"
    return root / _SETTINGS_FILENAME


def desktop_settings_data(settings: DesktopLauncherSettings) -> JsonObject:
    """Encode launcher settings as one versioned JSON object."""
    return {
        "schema_version": _SETTINGS_SCHEMA_VERSION,
        "workspace": None if settings.workspace is None else str(settings.workspace),
    }


def desktop_settings_from_data(data: JsonObject, source: Path) -> DesktopLauncherSettings:
    """Decode one current launcher-settings document strictly."""
    reject_unknown_fields(data, ("schema_version", "workspace"), f"{source} root")
    schema_version = data.get("schema_version")
    if schema_version != _SETTINGS_SCHEMA_VERSION:
        raise ValueError(
            f"{source}: unsupported desktop settings schema_version {schema_version!r}."
        )
    workspace_value = nullable_nonempty_string(data, "workspace")
    if workspace_value is None:
        return DesktopLauncherSettings()
    workspace = Path(workspace_value).expanduser()
    return DesktopLauncherSettings(workspace.resolve())
