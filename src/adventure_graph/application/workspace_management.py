"""Workspace-level adventure discovery, creation, selection, and default settings."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from adventure_graph.application.errors import NoChangesRequestedError
from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.application.project_initialization import instantiate_adventure_template
from adventure_graph.domain.adventure import (
    Adventure,
    AdventureTags,
    Encounter,
)
from adventure_graph.domain.identifiers import (
    identifier_slug,
    new_adventure_identifier,
)
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation_models import ValidationPolicy


class WorkspaceRevisionConflictError(ValueError):
    """Raised when a workspace mutation was based on an obsolete catalog snapshot."""


@dataclass(frozen=True, slots=True)
class WorkspaceRevision:
    """Opaque revision token for one adventure-workspace snapshot."""

    value: str


@dataclass(frozen=True, slots=True)
class AdventureCatalogEntry:
    """One adventure available to the local browser workspace."""

    key: str
    title: str
    synopsis: str
    encounter_count: int = 0
    revelation_count: int = 0
    clue_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    tags: AdventureTags = field(default_factory=AdventureTags)
    adventure_id: str = ""


@dataclass(frozen=True, slots=True)
class WorkspaceProjectDiagnostic:
    """One canonical project source that could not be loaded into the catalog."""

    key: str
    message: str


@dataclass(frozen=True, slots=True)
class WorkspaceSettings:
    """Persisted workspace selection and defaults for future adventures."""

    selected_adventure_key: str | None = None
    validator_defaults: ValidationPolicy = field(default_factory=ValidationPolicy)


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshot:
    """Discovered adventures and persisted workspace settings at one revision."""

    adventures: tuple[AdventureCatalogEntry, ...]
    settings: WorkspaceSettings
    revision: WorkspaceRevision
    diagnostics: tuple[WorkspaceProjectDiagnostic, ...] = ()
    reserved_directory_names: tuple[str, ...] = ()

    @property
    def selected_adventure(self) -> AdventureCatalogEntry | None:
        """Return the selected catalog entry, if one remains available."""
        selected = self.settings.selected_adventure_key
        return next((entry for entry in self.adventures if entry.key == selected), None)


class AdventureWorkspace(Protocol):
    """Application-facing port for local multi-adventure workspace persistence."""

    def load(self) -> WorkspaceSnapshot:
        """Load discovered adventures, selection, defaults, and revision."""
        ...

    def commit_settings(
        self,
        settings: WorkspaceSettings,
        expected_revision: WorkspaceRevision,
    ) -> WorkspaceRevision:
        """Commit workspace settings only against the expected revision."""
        ...

    def create_project(
        self,
        directory_name: str,
        adventure: Adventure,
        play_state: PlayState,
        settings: WorkspaceSettings,
        expected_revision: WorkspaceRevision,
    ) -> WorkspaceRevision:
        """Create one project and commit its selected workspace state atomically."""
        ...


@dataclass(frozen=True, slots=True)
class SelectAdventureCommand:
    """Select one discovered adventure for subsequent browser requests."""

    adventure_key: str
    expected_revision: WorkspaceRevision


@dataclass(frozen=True, slots=True)
class UpdateValidatorDefaultsCommand:
    """Replace the defaults applied when the workspace creates a new adventure."""

    policy: ValidationPolicy
    expected_revision: WorkspaceRevision


@dataclass(frozen=True, slots=True)
class CreateAdventureCommand:
    """Create a project shell, optionally including one distinguished start encounter."""

    title: str
    synopsis: str
    premise: str
    explanation: str
    opening_title: str
    opening_summary: str
    opening_view: str
    expected_revision: WorkspaceRevision
    tags: AdventureTags = field(default_factory=AdventureTags)


@dataclass(frozen=True, slots=True)
class CreateAdventureFromTemplateCommand:
    """Create one editable project from reusable authored template content."""

    template: Adventure
    expected_revision: WorkspaceRevision


@dataclass(frozen=True, slots=True)
class CreateAdventureResult:
    """New catalog entry and refreshed workspace snapshot."""

    adventure: Adventure
    entry: AdventureCatalogEntry
    snapshot: WorkspaceSnapshot


@dataclass(frozen=True, slots=True)
class ImportAdventureCommand:
    """Import one canonical adventure while preserving its authored identity."""

    adventure: Adventure
    expected_revision: WorkspaceRevision


@dataclass(frozen=True, slots=True)
class ImportAdventureResult:
    """Imported adventure, catalog entry, and refreshed workspace snapshot."""

    adventure: Adventure
    entry: AdventureCatalogEntry
    snapshot: WorkspaceSnapshot


class GetWorkspaceOverview:
    """Load the current multi-adventure workspace state."""

    def __init__(self, workspace: AdventureWorkspace) -> None:
        self._workspace = workspace

    def execute(self) -> WorkspaceSnapshot:
        """Return the current catalog, selection, defaults, and revision."""
        return self._workspace.load()


class SelectAdventure:
    """Persist a selected adventure after checking catalog membership and revision."""

    def __init__(self, workspace: AdventureWorkspace) -> None:
        self._workspace = workspace

    def execute(self, command: SelectAdventureCommand) -> WorkspaceSnapshot:
        """Select one available adventure and return the refreshed workspace."""
        snapshot = self._workspace.load()
        _require_workspace_revision(snapshot, command.expected_revision)
        if command.adventure_key not in {entry.key for entry in snapshot.adventures}:
            raise ValueError("The selected adventure is no longer available in this workspace.")
        settings = WorkspaceSettings(command.adventure_key, snapshot.settings.validator_defaults)
        self._workspace.commit_settings(settings, snapshot.revision)
        return self._workspace.load()


class UpdateValidatorDefaults:
    """Persist validator defaults for adventures created later in this workspace."""

    def __init__(self, workspace: AdventureWorkspace) -> None:
        self._workspace = workspace

    def execute(self, command: UpdateValidatorDefaultsCommand) -> WorkspaceSnapshot:
        """Commit future-adventure defaults without mutating existing adventures."""
        snapshot = self._workspace.load()
        _require_workspace_revision(snapshot, command.expected_revision)
        settings = WorkspaceSettings(
            snapshot.settings.selected_adventure_key,
            command.policy,
        )
        if settings == snapshot.settings:
            raise NoChangesRequestedError("No workspace default changes were requested.")
        self._workspace.commit_settings(settings, snapshot.revision)
        return self._workspace.load()


class CreateAdventure:
    """Create a new adventure project using the workspace's current defaults."""

    def __init__(
        self,
        workspace: AdventureWorkspace,
        adventure_id_factory: Callable[[], str] = new_adventure_identifier,
    ) -> None:
        self._workspace = workspace
        self._adventure_id_factory = adventure_id_factory

    def execute(self, command: CreateAdventureCommand) -> CreateAdventureResult:
        """Create and select one project with opaque adventure identity."""
        snapshot = self._workspace.load()
        _require_workspace_revision(snapshot, command.expected_revision)
        title = command.title.strip()
        opening_title = command.opening_title.strip()
        opening_summary = command.opening_summary.strip()
        opening_view = command.opening_view.strip()
        if not title:
            raise ValueError("Adventure title must not be empty.")
        if not opening_title and (opening_summary or opening_view):
            raise ValueError(
                "Opening encounter title is required when opening encounter details are supplied."
            )

        encounters: tuple[Encounter, ...] = ()
        if opening_title:
            encounters = (
                Encounter(
                    id=identifier_slug(opening_title),
                    title=opening_title,
                    summary=opening_summary,
                    opening_view=opening_view,
                    start=True,
                ),
            )

        adventure = Adventure(
            id=self._adventure_id_factory(),
            title=title,
            synopsis=command.synopsis,
            premise=command.premise,
            explanation=command.explanation,
            tags=command.tags,
            encounters=encounters,
            revelations=(),
            clues=(),
            validation_policy=snapshot.settings.validator_defaults,
        )
        entry, refreshed = _create_workspace_project(self._workspace, snapshot, adventure)
        return CreateAdventureResult(adventure, entry, refreshed)


class CreateAdventureFromTemplate:
    """Create a freshly identified editable project from reusable template content."""

    def __init__(
        self,
        workspace: AdventureWorkspace,
        adventure_id_factory: Callable[[], str] = new_adventure_identifier,
    ) -> None:
        self._workspace = workspace
        self._adventure_id_factory = adventure_id_factory

    def execute(
        self,
        command: CreateAdventureFromTemplateCommand,
    ) -> CreateAdventureResult:
        """Clone, select, and return one template-backed workspace project."""
        snapshot = self._workspace.load()
        _require_workspace_revision(snapshot, command.expected_revision)
        adventure = instantiate_adventure_template(
            command.template,
            self._adventure_id_factory,
        )
        entry, refreshed = _create_workspace_project(self._workspace, snapshot, adventure)
        return CreateAdventureResult(adventure, entry, refreshed)


class ImportAdventure:
    """Create a new local project from one canonical adventure document."""

    def __init__(self, workspace: AdventureWorkspace) -> None:
        self._workspace = workspace

    def execute(self, command: ImportAdventureCommand) -> ImportAdventureResult:
        """Import and select one adventure without changing stable identifiers."""
        snapshot = self._workspace.load()
        _require_workspace_revision(snapshot, command.expected_revision)
        adventure = command.adventure
        duplicate = next(
            (entry for entry in snapshot.adventures if entry.adventure_id == adventure.id),
            None,
        )
        if duplicate is not None:
            raise ValueError(
                f"This adventure is already present in the workspace as {duplicate.title!r}."
            )
        entry, refreshed = _create_workspace_project(self._workspace, snapshot, adventure)
        return ImportAdventureResult(adventure, entry, refreshed)


def _create_workspace_project(
    workspace: AdventureWorkspace,
    snapshot: WorkspaceSnapshot,
    adventure: Adventure,
) -> tuple[AdventureCatalogEntry, WorkspaceSnapshot]:
    occupied_names = {name.casefold() for name in snapshot.reserved_directory_names}
    occupied_names.update(
        _project_storage_name(entry.key).casefold() for entry in snapshot.adventures
    )
    directory_name = _unique_project_directory_name(adventure.title, occupied_names)
    key = f"{directory_name}/adventure.json"
    settings = WorkspaceSettings(key, snapshot.settings.validator_defaults)
    workspace.create_project(
        directory_name,
        adventure,
        new_play_state(adventure),
        settings,
        snapshot.revision,
    )
    refreshed = workspace.load()
    entry = next((item for item in refreshed.adventures if item.key == key), None)
    if entry is None:
        raise OSError("The adventure was created but could not be rediscovered.")
    return entry, refreshed


def _require_workspace_revision(
    snapshot: WorkspaceSnapshot,
    expected_revision: WorkspaceRevision,
) -> None:
    if snapshot.revision != expected_revision:
        raise WorkspaceRevisionConflictError(
            "The adventure catalog changed after this page was loaded; reload before saving."
        )


_MAX_PROJECT_DIRECTORY_LENGTH = 80


def _unique_project_directory_name(title: str, occupied_names: set[str]) -> str:
    """Return a bounded, cross-platform project directory name."""
    base = identifier_slug(title)[:_MAX_PROJECT_DIRECTORY_LENGTH].rstrip("-") or "adventure"
    if _is_windows_reserved_directory_name(base):
        base = f"adventure-{base}"[:_MAX_PROJECT_DIRECTORY_LENGTH].rstrip("-")
    if base.casefold() not in occupied_names:
        return base
    suffix = 2
    while True:
        rendered_suffix = f"-{suffix}"
        prefix = base[: _MAX_PROJECT_DIRECTORY_LENGTH - len(rendered_suffix)].rstrip("-")
        candidate = f"{prefix}{rendered_suffix}"
        if candidate.casefold() not in occupied_names:
            return candidate
        suffix += 1


def _is_windows_reserved_directory_name(name: str) -> bool:
    return name.casefold() in (
        "con",
        "prn",
        "aux",
        "nul",
        "clock$",
        "conin$",
        "conout$",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
    )


def _project_storage_name(key: str) -> str:
    first_segment = key.split("/", maxsplit=1)[0]
    if first_segment.endswith(".adventure.json"):
        return first_segment.removesuffix(".adventure.json")
    if first_segment == "adventure.json":
        return "adventure"
    return first_segment
