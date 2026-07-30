"""Actual-play journal CLI commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from adventure_graph.application.play_journal import (
    CorrectLatestPlayOperation,
    CorrectLatestPlayOperationCommand,
)
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.application.run_workspace import (
    AddPlayVisitNote,
    AddVisitNoteCommand,
    EndPlaySession,
    EndSessionCommand,
    EstablishPlayRevelation,
    EstablishRevelationCommand,
    ForeclosePlayRevelation,
    MissClueCommand,
    MissPlayClue,
    RecordEncounterConsequenceCommand,
    RecordPlayEncounterConsequence,
    RecordPlayReferenceNote,
    RecordPlayVisit,
    RecordReferenceNoteCommand,
    RecordVisitCommand,
    ReopenPlayRevelation,
    RevelationJudgmentCommand,
    SpotClueCommand,
    SpotPlayClue,
    StartPlaySession,
    StartSessionCommand,
    UnlockEncounterCommand,
    UnlockPlayEncounter,
)
from adventure_graph.infrastructure.local_play_journal import LocalPlayJournalProject


def handle_visit(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    result = RecordPlayVisit(project).execute(
        RecordVisitCommand(
            expected_revision=snapshot.revision,
            encounter_id=args.encounter,
            spotted_clue_ids=tuple(args.clue),
            notes=tuple(args.note),
            party_label=args.party,
        )
    )
    print(f"Recorded visit {result.visit_number} to {args.encounter}.")
    return 0


def handle_start_session(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    StartPlaySession(project).execute(
        StartSessionCommand(
            expected_revision=snapshot.revision,
            title=args.title,
            played_on=args.played_on,
            participants=tuple(args.participant),
            attendance_note=args.attendance_note,
            opening_note=args.opening_note,
        )
    )
    updated_snapshot = project.load()
    projection = project_play_state(updated_snapshot.adventure, updated_snapshot.state)
    print(f"Started session {projection.active_session_number}.")
    return 0


def handle_end_session(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    active_session = project_play_state(snapshot.adventure, snapshot.state).active_session_number
    EndPlaySession(project).execute(
        EndSessionCommand(
            expected_revision=snapshot.revision,
            closing_note=args.closing_note,
        )
    )
    print(f"Ended session {active_session}.")
    return 0


def handle_spot_clue(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    SpotPlayClue(project).execute(
        SpotClueCommand(
            expected_revision=snapshot.revision,
            clue_id=args.clue,
            visit_number=args.visit,
        )
    )
    print(f"Spotted lead {args.clue}.")
    return 0


def handle_miss_clue(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    MissPlayClue(project).execute(
        MissClueCommand(
            expected_revision=snapshot.revision,
            clue_id=args.clue,
            visit_number=args.visit,
        )
    )
    print(f"Marked lead {args.clue} missed.")
    return 0


def handle_establish_revelation(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    revelation = snapshot.adventure.revelation_index().get(args.revelation)
    if revelation is None:
        raise ValueError(f"Unknown revelation {args.revelation!r}.")
    available_before = set(
        project_play_state(snapshot.adventure, snapshot.state).available_encounter_ids
    )
    EstablishPlayRevelation(project).execute(
        EstablishRevelationCommand(
            expected_revision=snapshot.revision,
            revelation_id=args.revelation,
            supporting_clue_ids=tuple(args.clue),
            note=args.note,
        )
    )
    print(f"Established revelation {args.revelation}.")
    if (
        revelation.unlocks_encounter_id is not None
        and revelation.unlocks_encounter_id not in available_before
    ):
        print(f"Unlocked encounter {revelation.unlocks_encounter_id}.")
    return 0


def handle_foreclose_revelation(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    ForeclosePlayRevelation(project).execute(
        RevelationJudgmentCommand(
            expected_revision=snapshot.revision,
            revelation_id=args.revelation,
            reason=args.reason,
        )
    )
    print(f"Foreclosed revelation {args.revelation}.")
    return 0


def handle_reopen_revelation(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    ReopenPlayRevelation(project).execute(
        RevelationJudgmentCommand(
            expected_revision=snapshot.revision,
            revelation_id=args.revelation,
            reason=args.reason,
        )
    )
    print(f"Reopened revelation {args.revelation}.")
    return 0


def handle_unlock_encounter(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    UnlockPlayEncounter(project).execute(
        UnlockEncounterCommand(
            expected_revision=snapshot.revision,
            encounter_id=args.encounter,
            reason=args.reason,
        )
    )
    print(f"Unlocked encounter {args.encounter}.")
    return 0


def handle_consequence(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    RecordPlayEncounterConsequence(project).execute(
        RecordEncounterConsequenceCommand(
            expected_revision=snapshot.revision,
            encounter_id=args.encounter,
            text=args.text,
        )
    )
    print(f"Recorded lasting change for encounter {args.encounter}.")
    return 0


def handle_note(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    AddPlayVisitNote(project).execute(
        AddVisitNoteCommand(
            expected_revision=snapshot.revision,
            visit_number=args.visit,
            text=args.text,
        )
    )
    print(f"Added note to visit {args.visit}.")
    return 0


def handle_reference_note(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    RecordPlayReferenceNote(project).execute(
        RecordReferenceNoteCommand(
            expected_revision=snapshot.revision,
            reference_id=args.reference,
            text=args.text,
        )
    )
    print(f"Added playthrough note to reference {args.reference}.")
    return 0


def handle_correct_latest(args: argparse.Namespace) -> int:
    project = _play_journal_project(args.adventure, args.state)
    snapshot = project.load()
    result = CorrectLatestPlayOperation(project).execute(
        CorrectLatestPlayOperationCommand(
            reason=args.reason,
            expected_revision=snapshot.revision,
        )
    )
    print(
        f"Corrected play operation {result.target_operation_number}; "
        f"recorded audit event {result.correction_sequence}."
    )
    return 0


def _play_journal_project(adventure: str, state: str) -> LocalPlayJournalProject:
    return LocalPlayJournalProject(Path(adventure), Path(state))


__all__ = [
    "handle_consequence",
    "handle_correct_latest",
    "handle_end_session",
    "handle_establish_revelation",
    "handle_foreclose_revelation",
    "handle_miss_clue",
    "handle_note",
    "handle_reference_note",
    "handle_reopen_revelation",
    "handle_spot_clue",
    "handle_start_session",
    "handle_unlock_encounter",
    "handle_visit",
]
