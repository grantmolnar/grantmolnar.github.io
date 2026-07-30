"""Tests for workspace-level selection, defaults, and project creation."""

from __future__ import annotations

from dataclasses import dataclass

import pytest
from tests.support.adventures import complete_four_encounter_adventure

from adventure_graph.application.errors import NoChangesRequestedError
from adventure_graph.application.workspace_management import (
    AdventureCatalogEntry,
    CreateAdventure,
    CreateAdventureCommand,
    CreateAdventureFromTemplate,
    CreateAdventureFromTemplateCommand,
    ImportAdventure,
    ImportAdventureCommand,
    SelectAdventure,
    SelectAdventureCommand,
    UpdateValidatorDefaults,
    UpdateValidatorDefaultsCommand,
    WorkspaceRevision,
    WorkspaceRevisionConflictError,
    WorkspaceSettings,
    WorkspaceSnapshot,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation_models import ValidationPolicy


@dataclass
class MemoryWorkspace:
    """Mutable workspace port for application use-case tests."""

    snapshot: WorkspaceSnapshot
    created: tuple[str, Adventure, PlayState] | None = None

    def load(self) -> WorkspaceSnapshot:
        return self.snapshot

    def commit_settings(
        self, settings: WorkspaceSettings, expected_revision: WorkspaceRevision
    ) -> WorkspaceRevision:
        if expected_revision != self.snapshot.revision:
            raise WorkspaceRevisionConflictError("stale")
        revision = WorkspaceRevision(f"revision-{int(self.snapshot.revision.value[-1]) + 1}")
        self.snapshot = WorkspaceSnapshot(
            self.snapshot.adventures,
            settings,
            revision,
            reserved_directory_names=self.snapshot.reserved_directory_names,
        )
        return revision

    def create_project(
        self,
        directory_name: str,
        adventure: Adventure,
        play_state: PlayState,
        settings: WorkspaceSettings,
        expected_revision: WorkspaceRevision,
    ) -> WorkspaceRevision:
        if expected_revision != self.snapshot.revision:
            raise WorkspaceRevisionConflictError("stale")
        self.created = directory_name, adventure, play_state
        entry = AdventureCatalogEntry(
            f"{directory_name}/adventure.json",
            adventure.title,
            adventure.synopsis,
            adventure_id=adventure.id,
        )
        revision = WorkspaceRevision("revision-2")
        self.snapshot = WorkspaceSnapshot(
            (*self.snapshot.adventures, entry),
            settings,
            revision,
            reserved_directory_names=(
                *self.snapshot.reserved_directory_names,
                directory_name,
            ),
        )
        return revision


def _workspace() -> MemoryWorkspace:
    entries = (
        AdventureCatalogEntry("alpha/adventure.json", "Alpha", "First.", adventure_id="alpha-id"),
        AdventureCatalogEntry("beta/adventure.json", "Beta", "Second.", adventure_id="beta-id"),
    )
    return MemoryWorkspace(
        WorkspaceSnapshot(
            entries,
            WorkspaceSettings("alpha/adventure.json", ValidationPolicy()),
            WorkspaceRevision("revision-1"),
        )
    )


def test_select_adventure_persists_catalog_choice() -> None:
    workspace = _workspace()

    snapshot = SelectAdventure(workspace).execute(
        SelectAdventureCommand("beta/adventure.json", WorkspaceRevision("revision-1"))
    )

    assert snapshot.settings.selected_adventure_key == "beta/adventure.json"
    assert snapshot.selected_adventure is not None
    assert snapshot.selected_adventure.title == "Beta"


def test_workspace_defaults_do_not_rewrite_existing_entries() -> None:
    workspace = _workspace()
    policy = ValidationPolicy(minimum_clues_per_revelation=4)

    snapshot = UpdateValidatorDefaults(workspace).execute(
        UpdateValidatorDefaultsCommand(policy, WorkspaceRevision("revision-1"))
    )

    assert snapshot.settings.validator_defaults == policy
    assert snapshot.adventures == workspace.snapshot.adventures


def test_workspace_defaults_report_no_change_as_a_typed_outcome() -> None:
    workspace = _workspace()

    with pytest.raises(NoChangesRequestedError, match="No workspace default changes"):
        UpdateValidatorDefaults(workspace).execute(
            UpdateValidatorDefaultsCommand(
                workspace.snapshot.settings.validator_defaults,
                WorkspaceRevision("revision-1"),
            )
        )


def test_create_adventure_uses_defaults_and_unique_directory_name() -> None:
    workspace = _workspace()
    policy = ValidationPolicy(minimum_edge_connectivity=1)
    workspace.snapshot = WorkspaceSnapshot(
        workspace.snapshot.adventures,
        WorkspaceSettings("alpha/adventure.json", policy),
        WorkspaceRevision("revision-1"),
    )

    result = CreateAdventure(
        workspace,
        adventure_id_factory=lambda: "11111111-2222-4333-8444-555555555555",
    ).execute(
        CreateAdventureCommand(
            title="Alpha",
            synopsis="A new alpha.",
            premise="Begin here.",
            explanation="The truth.",
            opening_title="At the Gate",
            opening_summary="The party arrives.",
            opening_view="Rain runs down the gatehouse.",
            expected_revision=WorkspaceRevision("revision-1"),
        )
    )

    assert workspace.created is not None
    directory, adventure, play_state = workspace.created
    assert directory == "alpha-2"
    assert adventure.id == "11111111-2222-4333-8444-555555555555"
    assert adventure.validation_policy == policy
    assert adventure.encounters[0].start
    assert adventure.encounters[0].opening_view == "Rain runs down the gatehouse."
    assert play_state.adventure_id == adventure.id
    assert result.snapshot.settings.selected_adventure_key == "alpha-2/adventure.json"


def test_create_adventure_can_start_with_only_a_title() -> None:
    workspace = _workspace()

    result = CreateAdventure(
        workspace,
        adventure_id_factory=lambda: "11111111-2222-4333-8444-555555555555",
    ).execute(
        CreateAdventureCommand(
            title="A Bare Beginning",
            synopsis="",
            premise="",
            explanation="",
            opening_title="",
            opening_summary="",
            opening_view="",
            expected_revision=WorkspaceRevision("revision-1"),
        )
    )

    assert workspace.created is not None
    directory, adventure, play_state = workspace.created
    assert directory == "a-bare-beginning"
    assert adventure.title == "A Bare Beginning"
    assert adventure.synopsis == ""
    assert adventure.premise == ""
    assert adventure.explanation == ""
    assert adventure.encounters == ()
    assert adventure.revelations == ()
    assert adventure.clues == ()
    assert play_state.adventure_id == adventure.id
    assert play_state.events == ()
    assert result.snapshot.settings.selected_adventure_key == ("a-bare-beginning/adventure.json")


def test_create_from_template_preserves_content_under_fresh_identity() -> None:
    workspace = _workspace()
    template = complete_four_encounter_adventure()

    result = CreateAdventureFromTemplate(
        workspace,
        adventure_id_factory=lambda: "11111111-2222-4333-8444-555555555555",
    ).execute(
        CreateAdventureFromTemplateCommand(
            template,
            WorkspaceRevision("revision-1"),
        )
    )

    assert workspace.created is not None
    directory, adventure, play_state = workspace.created
    assert directory == "complete-four"
    assert adventure.id == "11111111-2222-4333-8444-555555555555"
    assert adventure.title == template.title
    assert adventure.encounters == template.encounters
    assert adventure.revelations == template.revelations
    assert adventure.clues == template.clues
    assert adventure.validation_policy == template.validation_policy
    assert play_state.adventure_id == adventure.id
    assert play_state.events == ()
    assert result.snapshot.settings.selected_adventure_key == "complete-four/adventure.json"
    assert template.id != adventure.id


def test_import_adventure_preserves_identity_and_starts_with_an_empty_journal() -> None:
    workspace = _workspace()
    adventure = complete_four_encounter_adventure()

    result = ImportAdventure(workspace).execute(
        ImportAdventureCommand(adventure, WorkspaceRevision("revision-1"))
    )

    assert workspace.created is not None
    directory, imported, play_state = workspace.created
    assert directory == "complete-four"
    assert imported == adventure
    assert play_state.adventure_id == adventure.id
    assert play_state.events == ()
    assert result.entry.adventure_id == adventure.id
    assert result.snapshot.settings.selected_adventure_key == "complete-four/adventure.json"


def test_import_adventure_rejects_duplicate_identity() -> None:
    workspace = _workspace()
    adventure = complete_four_encounter_adventure()
    existing = AdventureCatalogEntry(
        "existing/adventure.json",
        "Existing Copy",
        "",
        adventure_id=adventure.id,
    )
    workspace.snapshot = WorkspaceSnapshot(
        (*workspace.snapshot.adventures, existing),
        workspace.snapshot.settings,
        workspace.snapshot.revision,
    )

    with pytest.raises(ValueError, match="already present"):
        ImportAdventure(workspace).execute(
            ImportAdventureCommand(adventure, WorkspaceRevision("revision-1"))
        )

    assert workspace.created is None


def test_create_adventure_rejects_opening_details_without_an_opening_title() -> None:
    workspace = _workspace()

    with pytest.raises(ValueError, match="title is required"):
        CreateAdventure(workspace).execute(
            CreateAdventureCommand(
                title="Incomplete Opening",
                synopsis="",
                premise="",
                explanation="",
                opening_title="",
                opening_summary="The party arrives.",
                opening_view="",
                expected_revision=WorkspaceRevision("revision-1"),
            )
        )

    assert workspace.created is None


def test_workspace_commands_reject_stale_or_unknown_selection() -> None:
    workspace = _workspace()
    with pytest.raises(WorkspaceRevisionConflictError):
        SelectAdventure(workspace).execute(
            SelectAdventureCommand("beta/adventure.json", WorkspaceRevision("stale"))
        )
    with pytest.raises(ValueError, match="no longer available"):
        SelectAdventure(workspace).execute(
            SelectAdventureCommand("missing/adventure.json", WorkspaceRevision("revision-1"))
        )


@pytest.mark.parametrize(
    ("title", "reserved", "expected"),
    [
        ("The Ember Road", ("The-Ember-Road",), "the-ember-road-2"),
        ("CON", (), "adventure-con"),
        ("NUL", (), "adventure-nul"),
        ("A" * 200, (), "a" * 80),
        ("A" * 200, ("a" * 80,), f"{'a' * 78}-2"),
    ],
)
def test_create_adventure_uses_portable_collision_safe_directory_names(
    title: str,
    reserved: tuple[str, ...],
    expected: str,
) -> None:
    workspace = _workspace()
    workspace.snapshot = WorkspaceSnapshot(
        workspace.snapshot.adventures,
        workspace.snapshot.settings,
        workspace.snapshot.revision,
        reserved_directory_names=reserved,
    )

    CreateAdventure(
        workspace,
        adventure_id_factory=lambda: "11111111-2222-4333-8444-555555555555",
    ).execute(
        CreateAdventureCommand(
            title=title,
            synopsis="",
            premise="",
            explanation="",
            opening_title="",
            opening_summary="",
            opening_view="",
            expected_revision=WorkspaceRevision("revision-1"),
        )
    )

    assert workspace.created is not None
    assert workspace.created[0] == expected
