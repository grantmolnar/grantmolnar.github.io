"""Filesystem-backed web application builders for integration tests."""

from __future__ import annotations

from pathlib import Path

from adventure_graph.application.dice import RollDice
from adventure_graph.application.journal_workspace import GetJournalWorkspace
from adventure_graph.application.play_journal import CorrectLatestPlayOperation
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
from adventure_graph.infrastructure.local_authoring_project import LocalAuthoringProject
from adventure_graph.infrastructure.local_play_journal import LocalPlayJournalProject
from adventure_graph.interfaces.web.app import AuthoringWebApplication
from adventure_graph.interfaces.web.contracts import PlayCapability, PlayCommands, PlayQueries
from tests.support.web import authoring_commands, authoring_queries


def build_local_play_app(
    adventure_path: Path,
    state_path: Path,
    *,
    csrf_token: str = "integration-token",
) -> AuthoringWebApplication:
    """Build the browser adapter around real authored and play-state files."""
    authoring_project = LocalAuthoringProject(adventure_path)
    play_project = LocalPlayJournalProject(adventure_path, state_path)
    return AuthoringWebApplication(
        authoring_queries(authoring_project),
        authoring_commands(authoring_project),
        project_label=str(adventure_path),
        play=PlayCapability(
            queries=PlayQueries(
                get_journal_workspace=GetJournalWorkspace(play_project).execute,
                get_run=GetRunDashboard(play_project).execute,
            ),
            commands=PlayCommands(
                correct_latest=CorrectLatestPlayOperation(play_project).execute,
                start_session=StartPlaySession(play_project).execute,
                end_session=EndPlaySession(play_project).execute,
                record_visit=RecordPlayVisit(play_project).execute,
                transition_visit=TransitionPlayVisit(play_project).execute,
                spot_clue=SpotPlayClue(play_project).execute,
                miss_clue=MissPlayClue(play_project).execute,
                establish_revelation=EstablishPlayRevelation(play_project).execute,
                foreclose_revelation=ForeclosePlayRevelation(play_project).execute,
                reopen_revelation=ReopenPlayRevelation(play_project).execute,
                unlock_encounter=UnlockPlayEncounter(play_project).execute,
                add_visit_note=AddPlayVisitNote(play_project).execute,
                record_reference_note=RecordPlayReferenceNote(play_project).execute,
                record_consequence=RecordPlayEncounterConsequence(play_project).execute,
                roll_dice=RollDice(randbelow=lambda bound: bound - 1).execute,
                record_dice_roll=RecordPlayDiceRoll(play_project).execute,
            ),
        ),
        csrf_token=csrf_token,
    )
