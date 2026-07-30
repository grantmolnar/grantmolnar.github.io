"""Composition of local persistence adapters with the browser application."""

from __future__ import annotations

import secrets
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

from adventure_graph.application.adventure_authoring import UpdateAdventure
from adventure_graph.application.archive_management import (
    ArchiveActiveJournal,
    ArchiveMutationResult,
    DeleteJournalArchive,
    ExportActiveJournal,
    ExportActiveJournalCommand,
    GetJournalArchiveDetail,
    ImportJournalArchive,
    ImportJournalArchiveCommand,
    ListJournalArchives,
    RestoreJournalArchive,
)
from adventure_graph.application.dice import RollDice
from adventure_graph.application.document_limits import MAX_PORTABLE_FILENAME_STEM_LENGTH
from adventure_graph.application.encounter_authoring import (
    GetEncounterDetail,
    RemoveEncounter,
    UpdateEncounter,
)
from adventure_graph.application.errors import TransferStorageError
from adventure_graph.application.journal_workspace import GetJournalWorkspace
from adventure_graph.application.play_journal import CorrectLatestPlayOperation
from adventure_graph.application.play_ledger_workspace import GetPlayLedgerWorkspace
from adventure_graph.application.play_ledgers import GetPlayLedgers
from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.project_browsing import (
    AdventureOverviewResult,
    GetAdventureOverview,
    GetClueDetail,
    GetRevelationDetail,
)
from adventure_graph.application.reference_authoring import (
    CreateAndLinkReference,
    CreateReference,
    GetReferenceDetail,
    LinkReference,
    RemoveReference,
    UnlinkReference,
    UpdateReference,
)
from adventure_graph.application.reporting import (
    GetReportPacket,
    PublishReportPacket,
)
from adventure_graph.application.run_workspace import (
    AddPlayVisitNote,
    EndPlaySession,
    EstablishPlayRevelation,
    ForeclosePlayRevelation,
    GetRunDashboard,
    MissPlayClue,
    RecordPlayDiceRoll,
    RecordPlayEncounterConsequence,
    RecordPlayReferenceNote,
    RecordPlayVisit,
    ReopenPlayRevelation,
    SpotPlayClue,
    StartPlaySession,
    TransitionPlayVisit,
    UnlockPlayEncounter,
)
from adventure_graph.application.structural_authoring import (
    CreateClue,
    CreateEncounter,
    CreateRevelation,
    GetStructuralOverview,
    UpdateClue,
    UpdateRevelation,
)
from adventure_graph.application.validation_settings import (
    UpdateValidationPolicy,
    UpdateValidationPolicyCommand,
    UpdateValidationPolicyResult,
)
from adventure_graph.application.workspace_management import (
    CreateAdventure,
    CreateAdventureFromTemplate,
    CreateAdventureFromTemplateCommand,
    CreateAdventureResult,
    GetWorkspaceOverview,
    ImportAdventure,
    ImportAdventureCommand,
    ImportAdventureResult,
    SelectAdventure,
    UpdateValidatorDefaults,
    WorkspaceRevision,
)
from adventure_graph.application.workspace_transfer import (
    ImportWorkspacePlaythrough,
    ImportWorkspacePlaythroughCommand,
    ImportWorkspacePlaythroughResult,
)
from adventure_graph.domain.identifiers import identifier_slug
from adventure_graph.infrastructure.adventure_store import adventure_data, adventure_from_data
from adventure_graph.infrastructure.bundled_adventures import load_glass_saint_template
from adventure_graph.infrastructure.journal_archive_store import (
    canonical_archive_filename,
    journal_archive_data,
    journal_archive_from_data,
)
from adventure_graph.infrastructure.json_values import decode_object_bytes, encode_object_text
from adventure_graph.infrastructure.local_adventure_workspace import LocalAdventureWorkspace
from adventure_graph.infrastructure.local_authoring_project import LocalAuthoringProject
from adventure_graph.infrastructure.local_generated_reports import LocalGeneratedReportProject
from adventure_graph.infrastructure.local_journal_archives import LocalJournalArchiveProject
from adventure_graph.infrastructure.local_path_safety import (
    UnsafeFilesystemLayoutError,
    require_contained_file,
    require_symlink_free_tree,
)
from adventure_graph.infrastructure.local_play_journal import LocalPlayJournalProject
from adventure_graph.infrastructure.local_project_paths import local_project_paths
from adventure_graph.interfaces.web.app import AuthoringWebApplication
from adventure_graph.interfaces.web.contracts import (
    ArchiveCommands,
    ArchiveQueries,
    AuthoringCommands,
    AuthoringQueries,
    DownloadDocument,
    PlayCapability,
    PlayCommands,
    PlayLedgerQueries,
    PlayQueries,
    ReportCommands,
    ReportQueries,
    WorkspaceCommands,
    WorkspaceQueries,
)
from adventure_graph.interfaces.web.workspace_app import WorkspaceWebApplication

_TransferResult = TypeVar("_TransferResult")


def _run_transfer_write(
    operation: Callable[[], _TransferResult],
    *,
    subject: str,
) -> _TransferResult:
    """Map local write failures to one path-free application outcome."""
    try:
        return operation()
    except UnsafeFilesystemLayoutError as error:
        raise TransferStorageError(
            f"Adventure Graph refused to save the {subject} because the destination uses "
            "an unsafe filesystem layout. Remove symlinks or unsupported entries from the "
            "project, then retry."
        ) from error
    except OSError as error:
        raise TransferStorageError(
            f"Adventure Graph could not save the {subject}. Check workspace permissions and "
            "available disk space, then retry."
        ) from error


@dataclass(frozen=True)
class LocalWebProjects:
    """Concrete local projects used by one selected adventure application."""

    adventure_path: Path
    authoring: LocalAuthoringProject
    play: LocalPlayJournalProject
    reports: LocalGeneratedReportProject
    archives: LocalJournalArchiveProject

    @classmethod
    def open(cls, adventure_path: Path) -> LocalWebProjects:
        """Construct all local project adapters for one adventure workspace."""
        project_root = adventure_path.parent.resolve(strict=True)
        safe_adventure_path = require_contained_file(
            adventure_path,
            project_root,
            label="Adventure source",
        )
        paths = local_project_paths(safe_adventure_path)
        require_contained_file(
            paths.play_state,
            project_root,
            allow_missing=True,
            label="Active play journal",
        )
        require_symlink_free_tree(
            paths.generated,
            project_root,
            label="Generated report directory",
        )
        require_symlink_free_tree(
            paths.archives,
            project_root,
            label="Journal archive directory",
        )
        play = LocalPlayJournalProject(
            safe_adventure_path,
            paths.play_state,
            containment_root=project_root,
        )
        return cls(
            adventure_path=safe_adventure_path,
            authoring=LocalAuthoringProject(
                safe_adventure_path,
                containment_root=project_root,
            ),
            play=play,
            reports=LocalGeneratedReportProject(play, paths.generated),
            archives=LocalJournalArchiveProject(
                safe_adventure_path,
                paths.play_state,
                paths.archives,
                containment_root=project_root,
            ),
        )


def compose_workspace_web_application(
    workspace: LocalAdventureWorkspace,
) -> WorkspaceWebApplication:
    """Wire the multi-adventure shell and its dynamically selected applications."""

    def projects_for_key(key: str) -> LocalWebProjects:
        return LocalWebProjects.open(workspace.path_for_key(key))

    def adventure_application(key: str, csrf_token: str) -> AuthoringWebApplication:
        return compose_adventure_web_application(
            projects_for_key(key),
            csrf_token=csrf_token,
        )

    def get_adventure_overview(key: str) -> AdventureOverviewResult:
        return GetAdventureOverview(projects_for_key(key).authoring).execute()

    def update_adventure_validation_policy(
        key: str, command: UpdateValidationPolicyCommand
    ) -> UpdateValidationPolicyResult:
        return UpdateValidationPolicy(projects_for_key(key).authoring).execute(command)

    create_sample = CreateAdventureFromTemplate(workspace)
    glass_saint_template = load_glass_saint_template()
    import_adventure = ImportAdventure(workspace)
    import_playthrough = ImportWorkspacePlaythrough(
        workspace,
        lambda key: projects_for_key(key).archives,
    )

    def export_adventure(key: str) -> DownloadDocument:
        adventure = get_adventure_overview(key).adventure
        stem = identifier_slug(adventure.title)[:MAX_PORTABLE_FILENAME_STEM_LENGTH].rstrip("-")
        filename = f"{stem or 'adventure'}.adventure.json"
        return DownloadDocument(filename, encode_object_text(adventure_data(adventure)))

    def create_sample_adventure(
        expected_revision: WorkspaceRevision,
    ) -> CreateAdventureResult:
        return _run_transfer_write(
            lambda: create_sample.execute(
                CreateAdventureFromTemplateCommand(
                    glass_saint_template,
                    expected_revision,
                )
            ),
            subject="sample adventure",
        )

    def import_adventure_document(
        content: bytes,
        expected_revision: WorkspaceRevision,
    ) -> ImportAdventureResult:
        adventure = adventure_from_data(
            decode_object_bytes(content, "uploaded adventure document"),
            source="uploaded adventure document",
        )
        return _run_transfer_write(
            lambda: import_adventure.execute(ImportAdventureCommand(adventure, expected_revision)),
            subject="imported adventure",
        )

    def import_playthrough_document(
        content: bytes,
        expected_revision: WorkspaceRevision,
    ) -> ImportWorkspacePlaythroughResult:
        archive = journal_archive_from_data(
            decode_object_bytes(content, "uploaded playthrough archive"),
            source="uploaded playthrough archive",
        )
        return _run_transfer_write(
            lambda: import_playthrough.execute(
                ImportWorkspacePlaythroughCommand(archive, expected_revision)
            ),
            subject="imported playthrough",
        )

    return WorkspaceWebApplication(
        queries=WorkspaceQueries(
            get_workspace=GetWorkspaceOverview(workspace).execute,
            get_adventure_overview=get_adventure_overview,
            export_adventure=export_adventure,
        ),
        commands=WorkspaceCommands(
            select_adventure=SelectAdventure(workspace).execute,
            create_adventure=CreateAdventure(workspace).execute,
            create_sample_adventure=create_sample_adventure,
            import_adventure_document=import_adventure_document,
            import_playthrough_document=import_playthrough_document,
            update_validator_defaults=UpdateValidatorDefaults(workspace).execute,
            update_adventure_validation_policy=update_adventure_validation_policy,
        ),
        adventure_application=adventure_application,
        workspace_label=str(workspace.root),
    )


def compose_adventure_web_application(
    projects: LocalWebProjects,
    *,
    csrf_token: str | None = None,
) -> AuthoringWebApplication:
    """Wire one adventure's adapters to browser-facing command and query contracts."""
    archive_detail = GetJournalArchiveDetail(projects.archives)
    export_active = ExportActiveJournal(projects.archives)
    import_archive = ImportJournalArchive(projects.archives)

    def archive_download(archive_id: str) -> DownloadDocument:
        archive = archive_detail.execute(archive_id).archive
        return DownloadDocument(
            canonical_archive_filename(archive.archive_id),
            encode_object_text(journal_archive_data(archive)),
        )

    def export_active_document(command: ExportActiveJournalCommand) -> DownloadDocument:
        archive = export_active.execute(command)
        return DownloadDocument(
            canonical_archive_filename(archive.archive_id),
            encode_object_text(journal_archive_data(archive)),
        )

    def import_archive_document(
        content: bytes,
        expected_revision: ProjectRevision,
    ) -> ArchiveMutationResult:
        archive = journal_archive_from_data(
            decode_object_bytes(content, "uploaded playthrough archive"),
            source="uploaded playthrough archive",
        )
        return _run_transfer_write(
            lambda: import_archive.execute(ImportJournalArchiveCommand(archive, expected_revision)),
            subject="imported playthrough",
        )

    return AuthoringWebApplication(
        AuthoringQueries(
            get_overview=GetAdventureOverview(projects.authoring).execute,
            get_structure=GetStructuralOverview(projects.authoring).execute,
            get_encounter=GetEncounterDetail(projects.authoring).execute,
            get_revelation=GetRevelationDetail(projects.authoring).execute,
            get_clue=GetClueDetail(projects.authoring).execute,
            get_reference=GetReferenceDetail(projects.authoring).execute,
        ),
        AuthoringCommands(
            update_adventure=UpdateAdventure(projects.authoring).execute,
            create_encounter=CreateEncounter(projects.authoring).execute,
            update_encounter=UpdateEncounter(projects.authoring).execute,
            remove_encounter=RemoveEncounter(projects.authoring).execute,
            create_reference=CreateReference(projects.authoring).execute,
            create_and_link_reference=CreateAndLinkReference(projects.authoring).execute,
            update_reference=UpdateReference(projects.authoring).execute,
            link_reference=LinkReference(projects.authoring).execute,
            unlink_reference=UnlinkReference(projects.authoring).execute,
            remove_reference=RemoveReference(projects.authoring).execute,
            update_revelation=UpdateRevelation(projects.authoring).execute,
            update_clue=UpdateClue(projects.authoring).execute,
            create_clue=CreateClue(projects.authoring).execute,
            create_revelation=CreateRevelation(projects.authoring).execute,
            update_validation_policy=UpdateValidationPolicy(projects.authoring).execute,
        ),
        project_label=str(projects.adventure_path),
        play=PlayCapability(
            queries=PlayQueries(
                get_journal_workspace=GetJournalWorkspace(projects.play).execute,
                get_run=GetRunDashboard(projects.play).execute,
                ledgers=PlayLedgerQueries(
                    get_workspace=GetPlayLedgerWorkspace(projects.play).execute,
                    get_ledgers=GetPlayLedgers(projects.play).execute,
                ),
            ),
            commands=PlayCommands(
                correct_latest=CorrectLatestPlayOperation(projects.play).execute,
                start_session=StartPlaySession(projects.play).execute,
                end_session=EndPlaySession(projects.play).execute,
                record_visit=RecordPlayVisit(projects.play).execute,
                transition_visit=TransitionPlayVisit(projects.play).execute,
                spot_clue=SpotPlayClue(projects.play).execute,
                miss_clue=MissPlayClue(projects.play).execute,
                establish_revelation=EstablishPlayRevelation(projects.play).execute,
                foreclose_revelation=ForeclosePlayRevelation(projects.play).execute,
                reopen_revelation=ReopenPlayRevelation(projects.play).execute,
                unlock_encounter=UnlockPlayEncounter(projects.play).execute,
                add_visit_note=AddPlayVisitNote(projects.play).execute,
                record_reference_note=RecordPlayReferenceNote(projects.play).execute,
                record_consequence=RecordPlayEncounterConsequence(projects.play).execute,
                roll_dice=RollDice().execute,
                record_dice_roll=RecordPlayDiceRoll(projects.play).execute,
            ),
        ),
        report_queries=ReportQueries(get_packet=GetReportPacket(projects.reports).execute),
        report_commands=ReportCommands(
            publish_packet=PublishReportPacket(projects.reports).execute,
        ),
        archive_queries=ArchiveQueries(
            list_archives=ListJournalArchives(projects.archives).execute,
            get_archive=archive_detail.execute,
            export_archive=archive_download,
        ),
        archive_commands=ArchiveCommands(
            create_archive=ArchiveActiveJournal(projects.archives).execute,
            restore_archive=RestoreJournalArchive(projects.archives).execute,
            delete_archive=DeleteJournalArchive(projects.archives).execute,
            export_active=export_active_document,
            import_archive_document=import_archive_document,
        ),
        csrf_token=csrf_token or secrets.token_urlsafe(32),
    )


__all__ = [
    "LocalWebProjects",
    "compose_adventure_web_application",
    "compose_workspace_web_application",
]
