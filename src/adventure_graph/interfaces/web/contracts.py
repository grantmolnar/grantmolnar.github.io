"""Typed application callables consumed by the local web adapter."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Protocol
from wsgiref.types import StartResponse, WSGIEnvironment

from adventure_graph.application.adventure_authoring import (
    UpdateAdventureCommand,
    UpdateAdventureResult,
)
from adventure_graph.application.archive_management import (
    ArchiveActiveJournalCommand,
    ArchiveCatalogResult,
    ArchiveDetailResult,
    ArchiveMutationResult,
    DeleteJournalArchiveCommand,
    ExportActiveJournalCommand,
    RestoreJournalArchiveCommand,
)
from adventure_graph.application.dice import DiceRollResult, RollDiceCommand
from adventure_graph.application.encounter_authoring import (
    EncounterDetailResult,
    RemoveEncounterCommand,
    RemoveEncounterResult,
    UpdateEncounterCommand,
    UpdateEncounterResult,
)
from adventure_graph.application.journal_workspace import JournalWorkspaceResult
from adventure_graph.application.play_journal import (
    CorrectLatestPlayOperationCommand,
    CorrectLatestPlayOperationResult,
)
from adventure_graph.application.play_ledger_workspace import PlayLedgerWorkspaceResult
from adventure_graph.application.play_ledgers import PlayLedgerScope, PlayLedgersResult
from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.project_browsing import (
    AdventureOverviewResult,
    ClueDetailResult,
    RevelationDetailResult,
)
from adventure_graph.application.reference_authoring import (
    CreateAndLinkReferenceCommand,
    CreateAndLinkReferenceResult,
    CreateReferenceCommand,
    CreateReferenceResult,
    LinkReferenceCommand,
    LinkReferenceResult,
    ReferenceDetailResult,
    RemoveReferenceCommand,
    RemoveReferenceResult,
    UnlinkReferenceCommand,
    UnlinkReferenceResult,
    UpdateReferenceCommand,
    UpdateReferenceResult,
)
from adventure_graph.application.reporting import (
    PublishReportPacketCommand,
    PublishReportPacketResult,
    ReportPacketResult,
)
from adventure_graph.application.run_workspace import (
    AddVisitNoteCommand,
    EndSessionCommand,
    EstablishRevelationCommand,
    MissClueCommand,
    PlayOperationResult,
    RecordDiceRollCommand,
    RecordEncounterConsequenceCommand,
    RecordReferenceNoteCommand,
    RecordVisitCommand,
    RecordVisitResult,
    RevelationJudgmentCommand,
    RunDashboardResult,
    SpotClueCommand,
    StartSessionCommand,
    TransitionVisitCommand,
    TransitionVisitResult,
    UnlockEncounterCommand,
)
from adventure_graph.application.structural_authoring import (
    CreateClueCommand,
    CreateClueResult,
    CreateEncounterCommand,
    CreateEncounterResult,
    CreateRevelationCommand,
    CreateRevelationResult,
    StructuralOverviewResult,
    UpdateClueCommand,
    UpdateClueResult,
    UpdateRevelationCommand,
    UpdateRevelationResult,
)
from adventure_graph.application.validation_settings import (
    UpdateValidationPolicyCommand,
    UpdateValidationPolicyResult,
)
from adventure_graph.application.workspace_management import (
    CreateAdventureCommand,
    CreateAdventureResult,
    ImportAdventureResult,
    SelectAdventureCommand,
    UpdateValidatorDefaultsCommand,
    WorkspaceRevision,
    WorkspaceSnapshot,
)
from adventure_graph.application.workspace_transfer import ImportWorkspacePlaythroughResult


@dataclass(frozen=True, slots=True)
class DownloadDocument:
    """One trusted browser download assembled at the composition boundary."""

    filename: str
    body: str
    content_type: str = "application/json; charset=utf-8"


@dataclass(frozen=True, slots=True)
class AuthoringQueries:
    """Application queries required by the local authoring shell."""

    get_overview: Callable[[], AdventureOverviewResult]
    get_structure: Callable[[], StructuralOverviewResult]
    get_encounter: Callable[[str], EncounterDetailResult]
    get_revelation: Callable[[str], RevelationDetailResult]
    get_clue: Callable[[str], ClueDetailResult]
    get_reference: Callable[[str], ReferenceDetailResult]


@dataclass(frozen=True, slots=True)
class AuthoringCommands:
    """Application commands exposed by the current authoring milestone."""

    update_adventure: Callable[[UpdateAdventureCommand], UpdateAdventureResult]
    create_encounter: Callable[[CreateEncounterCommand], CreateEncounterResult]
    update_encounter: Callable[[UpdateEncounterCommand], UpdateEncounterResult]
    remove_encounter: Callable[[RemoveEncounterCommand], RemoveEncounterResult]
    create_reference: Callable[[CreateReferenceCommand], CreateReferenceResult]
    create_and_link_reference: Callable[
        [CreateAndLinkReferenceCommand], CreateAndLinkReferenceResult
    ]
    update_reference: Callable[[UpdateReferenceCommand], UpdateReferenceResult]
    link_reference: Callable[[LinkReferenceCommand], LinkReferenceResult]
    unlink_reference: Callable[[UnlinkReferenceCommand], UnlinkReferenceResult]
    remove_reference: Callable[[RemoveReferenceCommand], RemoveReferenceResult]
    update_revelation: Callable[[UpdateRevelationCommand], UpdateRevelationResult]
    update_clue: Callable[[UpdateClueCommand], UpdateClueResult]
    create_clue: Callable[[CreateClueCommand], CreateClueResult]
    create_revelation: Callable[[CreateRevelationCommand], CreateRevelationResult]
    update_validation_policy: Callable[
        [UpdateValidationPolicyCommand], UpdateValidationPolicyResult
    ]


class AdventureWebApplication(Protocol):
    """Selected-adventure WSGI capability required by the workspace shell."""

    def __call__(
        self,
        environ: WSGIEnvironment,
        start_response: StartResponse,
    ) -> Iterable[bytes]:
        """Serve one selected-adventure WSGI request."""
        ...


@dataclass(frozen=True, slots=True)
class PlayLedgerQueries:
    """Standalone and composite queries for the optional ledger workspace."""

    get_workspace: Callable[[PlayLedgerScope], PlayLedgerWorkspaceResult]
    get_ledgers: Callable[[PlayLedgerScope], PlayLedgersResult]


@dataclass(frozen=True, slots=True)
class PlayQueries:
    """Play-journal queries required by session, ledger, and history workspaces."""

    get_journal_workspace: Callable[[], JournalWorkspaceResult]
    get_run: Callable[[], RunDashboardResult]
    ledgers: PlayLedgerQueries | None = None


@dataclass(frozen=True, slots=True)
class PlayCommands:
    """Play-journal commands exposed by session and history workspaces."""

    correct_latest: Callable[
        [CorrectLatestPlayOperationCommand],
        CorrectLatestPlayOperationResult,
    ]
    start_session: Callable[[StartSessionCommand], PlayOperationResult]
    end_session: Callable[[EndSessionCommand], PlayOperationResult]
    record_visit: Callable[[RecordVisitCommand], RecordVisitResult]
    transition_visit: Callable[[TransitionVisitCommand], TransitionVisitResult]
    spot_clue: Callable[[SpotClueCommand], PlayOperationResult]
    miss_clue: Callable[[MissClueCommand], PlayOperationResult]
    establish_revelation: Callable[[EstablishRevelationCommand], PlayOperationResult]
    foreclose_revelation: Callable[[RevelationJudgmentCommand], PlayOperationResult]
    reopen_revelation: Callable[[RevelationJudgmentCommand], PlayOperationResult]
    unlock_encounter: Callable[[UnlockEncounterCommand], PlayOperationResult]
    add_visit_note: Callable[[AddVisitNoteCommand], PlayOperationResult]
    record_reference_note: Callable[[RecordReferenceNoteCommand], PlayOperationResult]
    record_consequence: Callable[[RecordEncounterConsequenceCommand], PlayOperationResult]
    roll_dice: Callable[[RollDiceCommand], DiceRollResult]
    record_dice_roll: Callable[[RecordDiceRollCommand], PlayOperationResult]


@dataclass(frozen=True, slots=True)
class PlayCapability:
    """Complete read/write capability required by the cohesive play workspace."""

    queries: PlayQueries
    commands: PlayCommands


@dataclass(frozen=True, slots=True)
class ReportQueries:
    """Generated-report queries required by the reporting workspace."""

    get_packet: Callable[[], ReportPacketResult]


@dataclass(frozen=True, slots=True)
class ReportCommands:
    """Generated-report commands exposed by the reporting workspace."""

    publish_packet: Callable[[PublishReportPacketCommand], PublishReportPacketResult]


@dataclass(frozen=True, slots=True)
class ArchiveQueries:
    """Journal archive queries required by the archive workspace."""

    list_archives: Callable[[], ArchiveCatalogResult]
    get_archive: Callable[[str], ArchiveDetailResult]
    export_archive: Callable[[str], DownloadDocument]


@dataclass(frozen=True, slots=True)
class ArchiveCommands:
    """Revision-aware journal archive mutations exposed by the browser."""

    create_archive: Callable[[ArchiveActiveJournalCommand], ArchiveMutationResult]
    restore_archive: Callable[[RestoreJournalArchiveCommand], ArchiveMutationResult]
    delete_archive: Callable[[DeleteJournalArchiveCommand], ArchiveMutationResult]
    export_active: Callable[[ExportActiveJournalCommand], DownloadDocument]
    import_archive_document: Callable[[bytes, ProjectRevision], ArchiveMutationResult]


@dataclass(frozen=True, slots=True)
class WorkspaceQueries:
    """Workspace catalog and selected-adventure settings queries."""

    get_workspace: Callable[[], WorkspaceSnapshot]
    get_adventure_overview: Callable[[str], AdventureOverviewResult]
    export_adventure: Callable[[str], DownloadDocument]


@dataclass(frozen=True, slots=True)
class WorkspaceCommands:
    """Workspace-level selection, creation, transfer, and default-setting commands."""

    select_adventure: Callable[[SelectAdventureCommand], WorkspaceSnapshot]
    create_adventure: Callable[[CreateAdventureCommand], CreateAdventureResult]
    create_sample_adventure: Callable[[WorkspaceRevision], CreateAdventureResult]
    import_adventure_document: Callable[[bytes, WorkspaceRevision], ImportAdventureResult]
    import_playthrough_document: Callable[
        [bytes, WorkspaceRevision], ImportWorkspacePlaythroughResult
    ]
    update_validator_defaults: Callable[[UpdateValidatorDefaultsCommand], WorkspaceSnapshot]
    update_adventure_validation_policy: Callable[
        [str, UpdateValidationPolicyCommand], UpdateValidationPolicyResult
    ]
