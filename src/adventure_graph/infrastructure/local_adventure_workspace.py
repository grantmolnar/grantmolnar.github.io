"""Local filesystem adapter for a multi-adventure browser workspace."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

from adventure_graph.application.workspace_management import (
    AdventureCatalogEntry,
    AdventureWorkspace,
    WorkspaceProjectDiagnostic,
    WorkspaceRevision,
    WorkspaceRevisionConflictError,
    WorkspaceSettings,
    WorkspaceSnapshot,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import ValidationPolicy
from adventure_graph.infrastructure.adventure_store import (
    adventure_data,
    load_adventure,
)
from adventure_graph.infrastructure.atomic_files import (
    create_directory,
    remove_directory,
    remove_file,
    write_json_object,
    write_json_objects,
)
from adventure_graph.infrastructure.file_transactions import (
    recover_pending_transactions_in_directories,
)
from adventure_graph.infrastructure.json_values import (
    JsonObject,
    UnsupportedFieldError,
    boolean_value,
    integer_value,
    read_object,
    reject_unknown_fields,
)
from adventure_graph.infrastructure.local_path_safety import (
    require_contained_directory,
    require_contained_file,
    require_symlink_free_tree,
)
from adventure_graph.infrastructure.play_state_store import play_state_data
from adventure_graph.infrastructure.workspace_discovery import (
    discover_workspace_adventure_sources,
)

_WORKSPACE_SCHEMA_VERSION = 1
_SETTINGS_DIRECTORY = ".adventure-graph"
_SETTINGS_FILE = "settings.json"
_PROJECT_CREATION_FILE = ".adventure-graph-project-creation.json"
_PROJECT_CREATION_SCHEMA_VERSION = 1
_PROJECT_CREATION_STATES = ("creating", "committed")

WORKSPACE_SETTINGS_ROOT_FIELDS = (
    "schema_version",
    "selected_adventure_key",
    "validator_defaults",
)
WORKSPACE_VALIDATOR_DEFAULT_FIELDS = (
    "minimum_clues_per_revelation",
    "minimum_source_encounters_per_revelation",
    "minimum_incoming_clues_per_encounter",
    "minimum_incoming_source_encounters_per_encounter",
    "minimum_outgoing_clues_per_encounter",
    "minimum_distinct_encounter_targets_per_encounter",
    "minimum_edge_connectivity",
    "require_directed_reachability",
)


class LocalAdventureWorkspace(AdventureWorkspace):
    """Discover and create adventure projects below one local workspace root."""

    def __init__(self, root: Path) -> None:
        resolved_root = root.resolve()
        if not resolved_root.exists():
            raise FileNotFoundError(
                f"Workspace does not exist: {resolved_root}. "
                "Create it first or initialize a project beneath it."
            )
        if not resolved_root.is_dir():
            raise ValueError(f"Workspace must be a directory: {resolved_root}.")
        self.root = resolved_root
        self.settings_path = self.root / _SETTINGS_DIRECTORY / _SETTINGS_FILE

    def select_initial_adventure(self, path: Path) -> None:
        """Persist one explicitly requested canonical adventure before server startup."""
        key = self.key_for_path(path)
        snapshot = self.load()
        if key not in {entry.key for entry in snapshot.adventures}:
            diagnostic = next(
                (item for item in snapshot.diagnostics if item.key == key),
                None,
            )
            if diagnostic is not None:
                raise ValueError(f"Cannot open selected adventure {key}: {diagnostic.message}")
            raise ValueError(
                "The selected file is not a canonical workspace adventure. "
                "Open a project directory containing adventure.json, or its adventure.json file."
            )
        settings = replace(snapshot.settings, selected_adventure_key=key)
        if settings != snapshot.settings:
            self.commit_settings(settings, snapshot.revision)

    def load(self) -> WorkspaceSnapshot:
        """Load discovered projects after recovering interrupted workspace writes."""
        self._recover_pending_writes()
        entries, diagnostics = self._discover()
        settings = self._load_settings()
        selected = settings.selected_adventure_key
        if selected is None and len(entries) == 1 and not diagnostics:
            settings = replace(settings, selected_adventure_key=entries[0].key)
        reserved_directory_names = tuple(
            sorted(
                (child.name for child in self.root.iterdir() if not child.name.startswith(".")),
                key=str.casefold,
            )
        )
        return WorkspaceSnapshot(
            entries,
            settings,
            self._revision(entries, diagnostics, settings, reserved_directory_names),
            diagnostics,
            reserved_directory_names,
        )

    def commit_settings(
        self,
        settings: WorkspaceSettings,
        expected_revision: WorkspaceRevision,
    ) -> WorkspaceRevision:
        """Write selection and defaults if the workspace revision remains current."""
        current = self.load()
        if current.revision != expected_revision:
            raise WorkspaceRevisionConflictError("The adventure workspace changed; reload it.")
        write_json_object(self.settings_path, workspace_settings_data(settings))
        return self.load().revision

    def create_project(
        self,
        directory_name: str,
        adventure: Adventure,
        play_state: PlayState,
        settings: WorkspaceSettings,
        expected_revision: WorkspaceRevision,
    ) -> WorkspaceRevision:
        """Create canonical project files and select them in one guarded operation."""
        current = self.load()
        if current.revision != expected_revision:
            raise WorkspaceRevisionConflictError("The adventure workspace changed; reload it.")
        requested_destination = self.root / Path(directory_name)
        if requested_destination.parent != self.root:
            raise ValueError("New adventure directories must be direct workspace children.")
        destination = require_contained_directory(
            requested_destination,
            self.root,
            allow_missing=True,
            label="New adventure directory",
        )
        if destination.exists():
            raise OSError(f"Adventure directory already exists: {destination.name}.")
        creation_path = destination / _PROJECT_CREATION_FILE
        try:
            write_json_object(creation_path, _project_creation_data("creating"))
        except BaseException:
            if destination.is_dir() and not any(destination.iterdir()):
                remove_directory(destination)
            raise
        try:
            write_json_objects(
                {
                    destination / "adventure.json": adventure_data(adventure),
                    destination / "play-state.json": play_state_data(play_state),
                    self.settings_path: workspace_settings_data(settings),
                    creation_path: _project_creation_data("committed"),
                }
            )
        except BaseException:
            self._discard_uncommitted_project(destination, creation_path)
            raise
        self._finish_committed_project(destination, creation_path)
        return self.load().revision

    def path_for_key(self, key: str) -> Path:
        """Resolve one discovered key to an adventure source below the workspace root."""
        candidate = require_contained_file(
            self.root / Path(key),
            self.root,
            label="Selected adventure",
        )
        if candidate not in self._candidate_paths():
            raise ValueError("The selected adventure is not available in this workspace.")
        return candidate

    def key_for_path(self, path: Path) -> str:
        """Return the relative catalog key for one source path below the root."""
        candidate = require_contained_file(
            path,
            self.root,
            label="Adventure path",
        )
        return candidate.relative_to(self.root).as_posix()

    def _recover_pending_writes(self) -> None:
        self._validate_workspace_surfaces()
        directories = [self.root, self.settings_path.parent]
        directories.extend(
            child for child in self.root.iterdir() if child.is_dir() and not child.is_symlink()
        )
        recover_pending_transactions_in_directories(directories, containment_root=self.root)
        self._recover_project_creations()

    def _recover_project_creations(self) -> None:
        for directory in self.root.iterdir():
            if not directory.is_dir() or directory.is_symlink():
                continue
            creation_path = directory / _PROJECT_CREATION_FILE
            if not creation_path.exists() and not creation_path.is_symlink():
                continue
            require_contained_file(
                creation_path,
                directory,
                label="Project creation marker",
            )
            state = _project_creation_state(read_object(creation_path), creation_path)
            if state == "creating":
                self._discard_uncommitted_project(directory, creation_path)
            else:
                self._finish_committed_project(directory, creation_path)

    @staticmethod
    def _discard_uncommitted_project(directory: Path, creation_path: Path) -> None:
        if not creation_path.exists() and not creation_path.is_symlink():
            return
        require_contained_file(
            creation_path,
            directory,
            label="Project creation marker",
        )
        state = _project_creation_state(read_object(creation_path), creation_path)
        if state != "creating":
            return
        unexpected = tuple(path for path in directory.iterdir() if path != creation_path)
        if unexpected:
            names = ", ".join(sorted(path.name for path in unexpected))
            raise ValueError(
                f"Interrupted project creation in {directory} contains unexpected files: {names}."
            )
        remove_file(creation_path)
        remove_directory(directory)

    @staticmethod
    def _finish_committed_project(directory: Path, creation_path: Path) -> None:
        adventure_path = directory / "adventure.json"
        state_path = directory / "play-state.json"
        try:
            require_contained_file(adventure_path, directory, label="Committed adventure source")
            require_contained_file(state_path, directory, label="Committed play journal")
        except (FileNotFoundError, ValueError) as error:
            raise ValueError(
                f"Committed project creation in {directory} is missing safe canonical files."
            ) from error
        create_directory(directory / "generated")
        create_directory(directory / "archives")
        remove_file(creation_path)

    def _discover(
        self,
    ) -> tuple[tuple[AdventureCatalogEntry, ...], tuple[WorkspaceProjectDiagnostic, ...]]:
        entries: list[AdventureCatalogEntry] = []
        diagnostics: list[WorkspaceProjectDiagnostic] = []
        for path in self._candidate_paths():
            key = path.relative_to(self.root).as_posix()
            try:
                adventure = load_adventure(path)
            except (OSError, ValueError) as error:
                diagnostics.append(
                    WorkspaceProjectDiagnostic(key, _relative_error_message(error, self.root))
                )
                continue
            report = validate_adventure(adventure)
            entries.append(
                AdventureCatalogEntry(
                    key=key,
                    title=adventure.title,
                    synopsis=adventure.synopsis,
                    encounter_count=len(adventure.encounters),
                    revelation_count=len(adventure.revelations),
                    clue_count=len(adventure.clues),
                    error_count=sum(issue.severity == "error" for issue in report.issues),
                    warning_count=sum(issue.severity == "warning" for issue in report.issues),
                    tags=adventure.tags,
                    adventure_id=adventure.id,
                )
            )
        sorted_entries = tuple(sorted(entries, key=lambda item: (item.title.casefold(), item.key)))
        sorted_diagnostics = tuple(sorted(diagnostics, key=lambda item: item.key))
        return sorted_entries, sorted_diagnostics

    def _candidate_paths(self) -> tuple[Path, ...]:
        return discover_workspace_adventure_sources(self.root)

    def _load_settings(self) -> WorkspaceSettings:
        if not self.settings_path.exists() and not self.settings_path.is_symlink():
            return WorkspaceSettings()
        require_contained_file(
            self.settings_path,
            self.root,
            label="Workspace settings file",
        )
        return workspace_settings_from_data(read_object(self.settings_path), self.settings_path)

    def _validate_workspace_surfaces(self) -> None:
        require_symlink_free_tree(
            self.settings_path.parent,
            self.root,
            label="Workspace settings directory",
        )

    def _revision(
        self,
        entries: tuple[AdventureCatalogEntry, ...],
        diagnostics: tuple[WorkspaceProjectDiagnostic, ...],
        settings: WorkspaceSettings,
        reserved_directory_names: tuple[str, ...],
    ) -> WorkspaceRevision:
        digest = hashlib.sha256()
        digest.update(repr(settings).encode("utf-8"))
        for entry in entries:
            digest.update(repr(entry).encode("utf-8"))
        for diagnostic in diagnostics:
            digest.update(repr(diagnostic).encode("utf-8"))
        for name in reserved_directory_names:
            digest.update(name.casefold().encode("utf-8"))
        return WorkspaceRevision(digest.hexdigest())


def _project_creation_data(state: str) -> JsonObject:
    if state not in _PROJECT_CREATION_STATES:
        raise ValueError(f"Unsupported project creation state {state!r}.")
    return {"schema_version": _PROJECT_CREATION_SCHEMA_VERSION, "state": state}


def _project_creation_state(data: JsonObject, source: Path) -> str:
    reject_unknown_fields(data, ("schema_version", "state"), f"{source} root")
    if data.get("schema_version") != _PROJECT_CREATION_SCHEMA_VERSION:
        raise ValueError(f"Unsupported project creation marker version in {source}.")
    state = data.get("state")
    if state not in _PROJECT_CREATION_STATES:
        raise ValueError(f"Malformed project creation marker in {source}.")
    return cast(str, state)


def workspace_settings_from_data(
    data: JsonObject,
    source: str | Path = "workspace settings document",
) -> WorkspaceSettings:
    if data.get("schema_version") != _WORKSPACE_SCHEMA_VERSION:
        raise ValueError(
            "Only workspace settings schema_version "
            f"{_WORKSPACE_SCHEMA_VERSION} is supported in {source}."
        )
    try:
        return _workspace_settings_from_current_schema(data, source)
    except UnsupportedFieldError:
        raise
    except ValueError as error:
        raise ValueError(f"Malformed workspace settings in {source}: {error}") from error


def _workspace_settings_from_current_schema(
    data: JsonObject,
    source: str | Path,
) -> WorkspaceSettings:
    reject_unknown_fields(data, WORKSPACE_SETTINGS_ROOT_FIELDS, f"{source} root")
    selected = data.get("selected_adventure_key")
    if selected is not None and not isinstance(selected, str):
        raise ValueError("Workspace selected_adventure_key must be a string or null.")
    defaults_value = data.get("validator_defaults", {})
    if not isinstance(defaults_value, dict):
        raise ValueError("Workspace validator_defaults must be an object.")
    defaults_data = cast(dict[str, Any], defaults_value)
    reject_unknown_fields(
        defaults_data,
        WORKSPACE_VALIDATOR_DEFAULT_FIELDS,
        f"{source} validator_defaults",
    )
    return WorkspaceSettings(selected, _policy_from_data(defaults_data))


def _relative_error_message(error: BaseException, root: Path) -> str:
    message = str(error).strip() or error.__class__.__name__
    return message.replace(str(root), ".")


def workspace_settings_data(settings: WorkspaceSettings) -> JsonObject:
    policy = settings.validator_defaults
    return {
        "schema_version": _WORKSPACE_SCHEMA_VERSION,
        "selected_adventure_key": settings.selected_adventure_key,
        "validator_defaults": {
            "minimum_clues_per_revelation": policy.minimum_clues_per_revelation,
            "minimum_source_encounters_per_revelation": (
                policy.minimum_source_encounters_per_revelation
            ),
            "minimum_incoming_clues_per_encounter": policy.minimum_incoming_clues_per_encounter,
            "minimum_incoming_source_encounters_per_encounter": (
                policy.minimum_incoming_source_encounters_per_encounter
            ),
            "minimum_outgoing_clues_per_encounter": policy.minimum_outgoing_clues_per_encounter,
            "minimum_distinct_encounter_targets_per_encounter": (
                policy.minimum_distinct_encounter_targets_per_encounter
            ),
            "minimum_edge_connectivity": policy.minimum_edge_connectivity,
            "require_directed_reachability": policy.require_directed_reachability,
        },
    }


def _policy_from_data(data: dict[str, Any]) -> ValidationPolicy:
    return ValidationPolicy(
        minimum_clues_per_revelation=integer_value(data, "minimum_clues_per_revelation", 3),
        minimum_source_encounters_per_revelation=integer_value(
            data, "minimum_source_encounters_per_revelation", 3
        ),
        minimum_incoming_clues_per_encounter=integer_value(
            data, "minimum_incoming_clues_per_encounter", 3
        ),
        minimum_incoming_source_encounters_per_encounter=integer_value(
            data, "minimum_incoming_source_encounters_per_encounter", 3
        ),
        minimum_outgoing_clues_per_encounter=integer_value(
            data, "minimum_outgoing_clues_per_encounter", 3
        ),
        minimum_distinct_encounter_targets_per_encounter=integer_value(
            data, "minimum_distinct_encounter_targets_per_encounter", 3
        ),
        minimum_edge_connectivity=integer_value(data, "minimum_edge_connectivity", 3),
        require_directed_reachability=boolean_value(data, "require_directed_reachability", True),
    )
