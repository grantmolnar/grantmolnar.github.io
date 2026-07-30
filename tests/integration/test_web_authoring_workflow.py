"""Filesystem integration coverage for the local encounter-authoring workflow."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import cast

from adventure_graph.application.archive_management import (
    ArchiveActiveJournal,
    ArchiveMutationResult,
    DeleteJournalArchive,
    GetJournalArchiveDetail,
    ListJournalArchives,
    RestoreJournalArchive,
)
from adventure_graph.application.dice import RollDice
from adventure_graph.application.journal_workspace import GetJournalWorkspace
from adventure_graph.application.play_journal import CorrectLatestPlayOperation
from adventure_graph.application.play_tracking import (
    establish_revelation,
    new_play_state,
    record_visit,
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
from adventure_graph.bootstrap import main
from adventure_graph.domain.play_events import (
    ClueSpottedEvent,
    DiceGroupResult,
    DiceRollRecordedEvent,
    EncounterUnlockedEvent,
    RevelationEstablishedEvent,
)
from adventure_graph.infrastructure.adventure_store import (
    load_adventure,
    save_adventure,
)
from adventure_graph.infrastructure.local_authoring_project import LocalAuthoringProject
from adventure_graph.infrastructure.local_generated_reports import (
    LocalGeneratedReportProject,
)
from adventure_graph.infrastructure.local_journal_archives import (
    LocalJournalArchiveProject,
)
from adventure_graph.infrastructure.local_play_journal import LocalPlayJournalProject
from adventure_graph.infrastructure.play_state_store import (
    load_play_state,
    save_play_state,
)
from adventure_graph.interfaces.web.app import AuthoringWebApplication
from adventure_graph.interfaces.web.contracts import (
    ArchiveCommands,
    ArchiveQueries,
    DownloadDocument,
    PlayCapability,
    PlayCommands,
    PlayQueries,
    ReportCommands,
    ReportQueries,
)
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.web import (
    authoring_commands,
    authoring_queries,
    post_form,
    request_wsgi,
)


def _app(adventure_path: Path) -> AuthoringWebApplication:
    project = LocalAuthoringProject(adventure_path)
    return AuthoringWebApplication(
        authoring_queries(project),
        authoring_commands(project),
        project_label=str(adventure_path),
        csrf_token="integration-token",
    )


def _encounter_form(revision: str, *, content: str) -> dict[str, str]:
    return {
        "csrf_token": "integration-token",
        "expected_revision": revision,
        "title": "The Shattered Gallery",
        "summary": "A ruined exhibition hall whose broken saint-statue points toward a conspiracy.",
        "opening_view": "Broken glass catches the morning light.",
        "content": content,
        "tags": "location",
        "start": "1",
    }


def test_web_encounter_save_writes_real_project_and_refuses_a_stale_followup(
    tmp_path: Path,
) -> None:
    project_directory = tmp_path / "web-authoring"
    assert main(["init", str(project_directory)]) == 0
    adventure_path = project_directory / "adventure.json"
    project = LocalAuthoringProject(adventure_path)
    app = _app(adventure_path)
    first_revision = project.load().revision.value

    status, headers, body = post_form(
        app,
        "/encounters/the-shattered-gallery/edit",
        _encounter_form(
            first_revision, content="## Revised gallery\n\nThe plaster dust is still warm."
        ),
    )

    assert status == "303 See Other"
    assert (
        headers["Location"]
        == "/encounters/the-shattered-gallery?saved=1&draft=the-shattered-gallery"
    )
    assert body == ""
    saved = load_adventure(adventure_path).encounter_index()["the-shattered-gallery"]
    assert saved.content == "## Revised gallery\n\nThe plaster dust is still warm."
    assert saved.tags == ("location",)
    assert saved.start

    second_revision = project.load().revision.value
    adventure = load_adventure(adventure_path)
    externally_changed = replace(
        adventure,
        encounters=tuple(
            replace(encounter, summary="Changed outside the browser.")
            if encounter.id == "the-shattered-gallery"
            else encounter
            for encounter in adventure.encounters
        ),
    )
    save_adventure(adventure_path, externally_changed)

    conflict_status, _, conflict_body = post_form(
        app,
        "/encounters/the-shattered-gallery/edit",
        _encounter_form(second_revision, content="Browser text that must not overwrite the file."),
    )

    assert conflict_status == "409 Conflict"
    assert "Revision conflict" in conflict_body
    assert "Browser text that must not overwrite the file." in conflict_body
    current = load_adventure(adventure_path).encounter_index()["the-shattered-gallery"]
    assert current.summary == "Changed outside the browser."
    assert current.content == "## Revised gallery\n\nThe plaster dust is still warm."


def test_web_structural_creation_writes_revelation_and_clue_to_real_project(
    tmp_path: Path,
) -> None:
    project_directory = tmp_path / "web-structure"
    assert main(["init", str(project_directory)]) == 0
    adventure_path = project_directory / "adventure.json"
    project = LocalAuthoringProject(adventure_path)
    app = _app(adventure_path)

    revelation_revision = project.load().revision.value
    revelation_status, revelation_headers, revelation_body = post_form(
        app,
        "/revelations/new",
        {
            "csrf_token": "integration-token",
            "expected_revision": revelation_revision,
            "title": "Find the lantern room",
            "description": "The shattered saint points toward a hidden lamp chamber.",
            "unlocks_encounter_id": "the-shattered-gallery",
            "source_encounter_id": "",
            "required": "1",
        },
    )

    assert revelation_status == "303 See Other"
    assert revelation_headers["Location"] == "/revelations/find-the-lantern-room?created=1"
    assert revelation_body == ""
    saved_revelation = load_adventure(adventure_path).revelation_index()["find-the-lantern-room"]
    assert saved_revelation.unlocks_encounter_id == "the-shattered-gallery"

    clue_revision = project.load().revision.value
    clue_status, clue_headers, clue_body = post_form(
        app,
        "/clues/new",
        {
            "csrf_token": "integration-token",
            "expected_revision": clue_revision,
            "title": "The saint points toward the lantern room",
            "source_encounter_id": "the-shattered-gallery",
            "revelation_id": "find-the-lantern-room",
            "description": "The statue's remaining hand aligns with a sealed arch.",
            "discovery": "inspection",
        },
    )

    assert clue_status == "303 See Other"
    assert clue_headers["Location"] == "/clues/the-saint-points-toward-the-lantern-room?created=1"
    assert clue_body == ""
    saved_clue = load_adventure(adventure_path).clue_index()[
        "the-saint-points-toward-the-lantern-room"
    ]
    assert saved_clue.source_encounter_id == "the-shattered-gallery"
    assert saved_clue.revelation_id == "find-the-lantern-room"


def _run_app(adventure_path: Path, state_path: Path) -> AuthoringWebApplication:
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
        report_queries=ReportQueries(
            get_packet=GetReportPacket(
                LocalGeneratedReportProject(play_project, adventure_path.parent / "generated")
            ).execute
        ),
        report_commands=ReportCommands(
            publish_packet=PublishReportPacket(
                LocalGeneratedReportProject(play_project, adventure_path.parent / "generated")
            ).execute
        ),
        archive_queries=ArchiveQueries(
            list_archives=ListJournalArchives(
                LocalJournalArchiveProject(
                    adventure_path,
                    state_path,
                    adventure_path.parent / "archives",
                )
            ).execute,
            get_archive=GetJournalArchiveDetail(
                LocalJournalArchiveProject(
                    adventure_path,
                    state_path,
                    adventure_path.parent / "archives",
                )
            ).execute,
            export_archive=lambda _archive_id: cast(DownloadDocument, object()),
        ),
        archive_commands=ArchiveCommands(
            create_archive=ArchiveActiveJournal(
                LocalJournalArchiveProject(
                    adventure_path,
                    state_path,
                    adventure_path.parent / "archives",
                )
            ).execute,
            restore_archive=RestoreJournalArchive(
                LocalJournalArchiveProject(
                    adventure_path,
                    state_path,
                    adventure_path.parent / "archives",
                )
            ).execute,
            delete_archive=DeleteJournalArchive(
                LocalJournalArchiveProject(
                    adventure_path,
                    state_path,
                    adventure_path.parent / "archives",
                )
            ).execute,
            export_active=lambda _command: cast(DownloadDocument, object()),
            import_archive_document=lambda _content, _revision: cast(
                ArchiveMutationResult, object()
            ),
        ),
        csrf_token="integration-token",
    )


def test_web_title_edits_preserve_real_journal_identifiers(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta",),
    )
    state = establish_revelation(adventure, state, "find-beta", ("alpha-to-beta",))
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, state)
    project = LocalAuthoringProject(adventure_path)
    app = _app(adventure_path)

    adventure_status, adventure_headers, _ = post_form(
        app,
        "/adventure/edit",
        {
            "csrf_token": "integration-token",
            "expected_revision": project.load().revision.value,
            "title": "The Complete Four",
            "synopsis": adventure.synopsis,
            "premise": adventure.premise,
            "explanation": adventure.explanation,
            "genres": "Investigation, Political intrigue",
            "game_systems": "System-agnostic",
            "settings": "Original fantasy",
            "party_size_min": "3",
            "party_size_max": "5",
            "level_min": "",
            "level_max": "",
            "combat_intensity": "moderate",
            "keywords": "Deadline, Branching",
        },
    )

    assert adventure_status == "303 See Other"
    assert adventure_headers["Location"] == "/?saved=1&draft=complete-four"
    saved_adventure = load_adventure(adventure_path)
    assert saved_adventure.tags.genres == ("Investigation", "Political intrigue")
    assert saved_adventure.tags.party_size_min == 3
    assert saved_adventure.tags.party_size_max == 5
    assert saved_adventure.tags.combat_intensity == "moderate"
    assert load_play_state(state_path).adventure_id == "complete-four"

    revelation_status, revelation_headers, _ = post_form(
        app,
        "/revelations/find-beta/edit",
        {
            "csrf_token": "integration-token",
            "expected_revision": project.load().revision.value,
            "title": "Locate Beta",
            "description": "The group can locate beta.",
            "unlocks_encounter_id": "beta",
            "source_encounter_id": "",
            "required": "1",
        },
    )

    assert revelation_status == "303 See Other"
    assert revelation_headers["Location"] == ("/revelations/find-beta?saved=1&draft=find-beta")
    renamed_state = load_play_state(state_path)
    established = next(
        event for event in renamed_state.events if isinstance(event, RevelationEstablishedEvent)
    )
    unlocked = next(
        event for event in renamed_state.events if isinstance(event, EncounterUnlockedEvent)
    )
    assert established.revelation_id == "find-beta"
    assert unlocked.source_revelation_id == "find-beta"

    clue_status, clue_headers, _ = post_form(
        app,
        "/clues/alpha-to-beta/edit",
        {
            "csrf_token": "integration-token",
            "expected_revision": project.load().revision.value,
            "title": "The first path to Beta",
            "source_encounter_id": "alpha",
            "revelation_id": "find-beta",
            "description": "",
            "discovery": "search",
        },
    )

    assert clue_status == "303 See Other"
    assert clue_headers["Location"] == ("/clues/alpha-to-beta?saved=1&draft=alpha-to-beta")
    final_state = load_play_state(state_path)
    spotted = next(event for event in final_state.events if isinstance(event, ClueSpottedEvent))
    established = next(
        event for event in final_state.events if isinstance(event, RevelationEstablishedEvent)
    )
    assert spotted.clue_id == "alpha-to-beta"
    assert established.supporting_clue_ids == ("alpha-to-beta",)


def test_web_play_mode_reads_real_journal_without_mutation(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, record_visit(adventure, new_play_state(adventure), "alpha"))
    app = _run_app(adventure_path, state_path)
    before = state_path.read_bytes()

    status, _, body = request_wsgi(app, "/play", query="encounter=omega")

    assert status == "200 OK"
    assert "Chronological route" in body
    assert "<h1>Omega</h1>" in body
    assert "the current recorded visit remains Alpha" in body
    assert "<span>Locked</span>" in body
    assert state_path.read_bytes() == before


def test_web_play_dice_roll_is_ephemeral_then_records_exact_result(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, record_visit(adventure, new_play_state(adventure), "alpha"))
    project = LocalPlayJournalProject(adventure_path, state_path)
    app = _run_app(adventure_path, state_path)
    before = state_path.read_bytes()

    status, _, body = post_form(
        app,
        "/play/dice/roll",
        {
            "csrf_token": "integration-token",
            "focus_encounter_id": "alpha",
            "expression": "2d8 - 1",
            "label": "Cross the chasm",
        },
    )

    assert status == "200 OK"
    assert 'data-expression="2d8 - 1"' in body
    assert "<strong>15</strong>" in body
    assert state_path.read_bytes() == before

    payload = json.dumps(
        {
            "expression": "2d8 - 1",
            "terms": [
                {"kind": "dice", "sign": 1, "faces": 8, "results": [8, 8]},
                {"kind": "modifier", "value": -1},
            ],
            "total": 15,
        },
        separators=(",", ":"),
    )
    record_status, record_headers, _ = post_form(
        app,
        "/play/dice/record",
        {
            "csrf_token": "integration-token",
            "expected_revision": project.load().revision.value,
            "focus_encounter_id": "alpha",
            "label": "Cross the chasm",
            "roll_payload": payload,
        },
    )

    assert record_status == "303 See Other"
    assert record_headers["Location"] == "/play?action=dice-recorded&operation=2&encounter=alpha"
    event = load_play_state(state_path).events[-1]
    assert isinstance(event, DiceRollRecordedEvent)
    assert event.label == "Cross the chasm"
    assert event.total == 15
    group = event.terms[0]
    assert isinstance(group, DiceGroupResult)
    assert group.results == (8, 8)


def test_web_run_workspace_commits_atomic_operations_to_real_journal(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, new_play_state(adventure))
    project = LocalPlayJournalProject(adventure_path, state_path)
    app = _run_app(adventure_path, state_path)

    first_revision = project.load().revision.value
    visit_status, visit_headers, visit_body = post_form(
        app,
        "/run/visit",
        {
            "csrf_token": "integration-token",
            "expected_revision": first_revision,
            "encounter_id": "alpha",
            "clue_id": "alpha-to-beta",
            "note": "The party follows the brass inlay.",
        },
    )

    assert visit_status == "303 See Other"
    assert visit_headers["Location"] == "/run?action=visit&operation=1&visit=1"
    assert visit_body == ""
    state = load_play_state(state_path)
    assert len(state.events) == 3
    assert {event.operation_number for event in state.events} == {1}

    second_revision = project.load().revision.value
    revelation_status, revelation_headers, revelation_body = post_form(
        app,
        "/run/revelation",
        {
            "csrf_token": "integration-token",
            "expected_revision": second_revision,
            "revelation_id": "find-beta",
            "supporting_clue_id": "alpha-to-beta",
            "note": "The route to Beta is established.",
        },
    )

    assert revelation_status == "303 See Other"
    assert revelation_headers["Location"] == "/run?action=revelation&operation=2"
    assert revelation_body == ""
    state = load_play_state(state_path)
    assert len(state.events) == 5
    assert state.events[-1].operation_number == 2
    dashboard = GetRunDashboard(project).execute()
    assert {item.encounter.id for item in dashboard.available_encounters} == {"alpha", "beta"}


def test_web_reports_render_download_and_publish_real_packet(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, record_visit(adventure, new_play_state(adventure), "alpha"))
    app = _run_app(adventure_path, state_path)
    revision = LocalPlayJournalProject(adventure_path, state_path).load().revision.value

    status, _, body = request_wsgi(app, "/reports", query="document=05-play-summary.md")
    download_status, download_headers, download_body = request_wsgi(
        app,
        "/reports/download",
        query="document=05-play-summary.md",
    )
    publish_status, publish_headers, publish_body = post_form(
        app,
        "/reports/generate",
        {
            "csrf_token": "integration-token",
            "expected_revision": revision,
        },
    )

    assert status == "200 OK"
    assert "Adventure packet" in body
    assert '<a href="/" aria-current="page">Author</a>' in body
    assert 'aria-label="Adventure navigation"' in body
    assert 'aria-label="Play navigation"' not in body
    assert "This is not the chronological record of table play" in body
    assert "Play Summary: Complete Four" in body
    assert download_status == "200 OK"
    assert download_headers["Content-Type"] == "text/markdown; charset=utf-8"
    assert download_headers["Content-Disposition"] == 'attachment; filename="05-play-summary.md"'
    assert download_body.startswith("# Play Summary: Complete Four")
    assert publish_status == "303 See Other"
    assert publish_headers["Location"] == "/reports?generated=1"
    assert publish_body == ""
    assert (tmp_path / "generated" / "05-play-summary.md").exists()
    assert (tmp_path / "generated" / "encounters" / "alpha.md").exists()


def test_web_archive_catalog_compares_restores_and_confirms_delete(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    archive_directory = tmp_path / "archives"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, record_visit(adventure, new_play_state(adventure), "alpha"))
    app = _run_app(adventure_path, state_path)
    project = LocalJournalArchiveProject(adventure_path, state_path, archive_directory)

    create_status, create_headers, create_body = post_form(
        app,
        "/archives/create",
        {
            "csrf_token": "integration-token",
            "expected_revision": project.load().revision.value,
            "label": "First Session",
            "name": "first-session",
        },
    )

    assert create_status == "303 See Other"
    assert create_body == ""
    assert create_headers["Location"].startswith("/archives?action=created&archive=")
    archive = project.load().archives[0]
    archive_path = archive_directory / f"{archive.archive_id}.journal.json"
    archive_payload = archive_path.read_bytes()
    assert not load_play_state(state_path).events

    detail_status, _, detail_body = request_wsgi(app, f"/archives/{archive.archive_id}")
    assert detail_status == "200 OK"
    assert "Adventure snapshot comparison" in detail_body
    assert "Compatible with current adventure" in detail_body

    wrong_restore_status, _, wrong_restore_body = post_form(
        app,
        f"/archives/{archive.archive_id}/restore",
        {
            "csrf_token": "wrong-token",
            "expected_revision": project.load().revision.value,
        },
    )
    assert wrong_restore_status == "403 Forbidden"
    assert "Form token rejected" in wrong_restore_body
    assert not load_play_state(state_path).events
    assert archive_path.read_bytes() == archive_payload

    restore_status, restore_headers, _ = post_form(
        app,
        f"/archives/{archive.archive_id}/restore",
        {
            "csrf_token": "integration-token",
            "expected_revision": project.load().revision.value,
        },
    )
    assert restore_status == "303 See Other"
    assert "action=restored" in restore_headers["Location"]
    assert load_play_state(state_path).events
    restored_catalog = project.load()
    assert restored_catalog.archives == (archive,)
    assert archive_path.read_bytes() == archive_payload
    assert restored_catalog.archives[0].adventure_snapshot == adventure
    assert restored_catalog.archives[0].play_state == archive.play_state

    second_create_status, _, _ = post_form(
        app,
        "/archives/create",
        {
            "csrf_token": "integration-token",
            "expected_revision": project.load().revision.value,
            "label": "Disposable",
            "name": "disposable",
        },
    )
    assert second_create_status == "303 See Other"
    disposable = next(
        stored for stored in project.load().archives if stored.archive_id == "disposable"
    )

    wrong_delete_status, _, wrong_delete_body = post_form(
        app,
        f"/archives/{disposable.archive_id}/delete",
        {
            "csrf_token": "wrong-token",
            "expected_revision": project.load().revision.value,
            "confirmation": disposable.archive_id,
        },
    )
    assert wrong_delete_status == "403 Forbidden"
    assert "Form token rejected" in wrong_delete_body
    assert disposable.archive_id in {stored.archive_id for stored in project.load().archives}

    refused_status, _, refused_body = post_form(
        app,
        f"/archives/{disposable.archive_id}/delete",
        {
            "csrf_token": "integration-token",
            "expected_revision": project.load().revision.value,
            "confirmation": "wrong",
        },
    )
    assert refused_status == "422 Unprocessable Content"
    assert "confirmation must exactly match" in refused_body
    assert {stored.archive_id for stored in project.load().archives} == {
        archive.archive_id,
        disposable.archive_id,
    }

    delete_status, delete_headers, _ = post_form(
        app,
        f"/archives/{disposable.archive_id}/delete",
        {
            "csrf_token": "integration-token",
            "expected_revision": project.load().revision.value,
            "confirmation": disposable.archive_id,
        },
    )
    assert delete_status == "303 See Other"
    assert "action=deleted" in delete_headers["Location"]
    assert tuple(stored.archive_id for stored in project.load().archives) == (archive.archive_id,)


def test_play_improvisation_returns_to_table_without_changing_play_history(
    tmp_path: Path,
) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    state = record_visit(adventure, new_play_state(adventure), "alpha", ())
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, state)
    app = _run_app(adventure_path, state_path)
    original_state = state_path.read_bytes()

    play_status, _, play_body = request_wsgi(app, "/play", query="encounter=alpha")

    assert play_status == "200 OK"
    assert "Add to adventure" in play_body
    assert 'href="/clues/new?source=alpha&amp;return_to=%2Fplay%3Fencounter%3Dalpha"' in play_body
    assert 'href="/encounters/new?return_to=%2Fplay%3Fencounter%3Dalpha"' in play_body
    assert (
        'href="/revelations/new?source=alpha&amp;return_to=%2Fplay%3Fencounter%3Dalpha"'
        in play_body
    )
    assert (
        'href="/references/new?encounter=alpha&amp;return_to=%2Fplay%3Fencounter%3Dalpha"'
        in play_body
    )
    assert "Add revelation and lead here" in play_body
    assert "Add linked reference" in play_body

    encounter_form_status, _, encounter_form_body = request_wsgi(
        app,
        "/encounters/new",
        query="return_to=%2Fplay%3Fencounter%3Dalpha",
    )
    assert encounter_form_status == "200 OK"
    assert "Add an encounter during play" in encounter_form_body
    assert 'name="return_to" value="/play?encounter=alpha"' in encounter_form_body
    assert ">Back to table</a>" in encounter_form_body

    encounter_revision = LocalAuthoringProject(adventure_path).load().revision.value
    encounter_status, encounter_headers, _ = post_form(
        app,
        "/encounters/new",
        {
            "csrf_token": "integration-token",
            "expected_revision": encounter_revision,
            "title": "The Flooded Cellar",
            "summary": "An improvised refuge below the street.",
            "opening_view": "Water laps against the lowest stair.",
            "content": "A hurried encounter created while the session remains in progress.",
            "tags": "improvised",
            "required": "1",
            "return_to": "/play?encounter=alpha",
        },
    )

    assert encounter_status == "303 See Other"
    assert encounter_headers["Location"] == (
        "/play?encounter=the-flooded-cellar&action=encounter-authored"
    )
    assert state_path.read_bytes() == original_state
    assert "the-flooded-cellar" in load_adventure(adventure_path).encounter_index()

    returned_status, _, returned_body = request_wsgi(
        app,
        "/play",
        query="encounter=the-flooded-cellar&action=encounter-authored",
    )
    assert returned_status == "200 OK"
    assert "Encounter added" in returned_body
    assert "current visit and play history did not change" in returned_body
    assert "The Flooded Cellar" in returned_body
    assert "current recorded visit remains Alpha" in returned_body

    clue_form_status, _, clue_form_body = request_wsgi(
        app,
        "/clues/new",
        query="source=alpha&return_to=%2Fplay%3Fencounter%3Dalpha",
    )
    assert clue_form_status == "200 OK"
    assert "Add a lead during play" in clue_form_body
    assert '<option value="alpha" selected>Alpha</option>' in clue_form_body
    assert "Create a revelation first" in clue_form_body

    clue_revision = LocalAuthoringProject(adventure_path).load().revision.value
    clue_status, clue_headers, _ = post_form(
        app,
        "/clues/new",
        {
            "csrf_token": "integration-token",
            "expected_revision": clue_revision,
            "title": "Mud on the cellar stairs",
            "source_encounter_id": "beta",
            "revelation_id": "find-beta",
            "description": "Fresh mud shows that someone recently fled toward Beta.",
            "discovery": "inspection",
            "return_to": "/play?encounter=alpha",
        },
    )

    assert clue_status == "303 See Other"
    assert clue_headers["Location"] == "/play?encounter=beta&action=clue-authored"
    assert state_path.read_bytes() == original_state
    assert "mud-on-the-cellar-stairs" in load_adventure(adventure_path).clue_index()

    clue_return_status, _, clue_return_body = request_wsgi(
        app,
        "/play",
        query="encounter=beta&action=clue-authored",
    )
    assert clue_return_status == "200 OK"
    assert "Lead added" in clue_return_body
    assert "Mud on the cellar stairs" in clue_return_body
    assert "current recorded visit remains Alpha" in clue_return_body


def test_play_clue_revelation_chain_preserves_return_context(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, new_play_state(adventure))
    app = _run_app(adventure_path, state_path)

    status, _, body = request_wsgi(
        app,
        "/revelations/new",
        query="source=alpha&return_to=%2Fplay%3Fencounter%3Dalpha",
    )

    assert status == "200 OK"
    assert "Play improvisation" in body
    assert 'name="source_encounter_id" value="alpha"' in body
    assert 'name="return_to" value="/play?encounter=alpha"' in body
    assert 'href="/clues/new?source=alpha&amp;return_to=%2Fplay%3Fencounter%3Dalpha"' in body

    revision = LocalAuthoringProject(adventure_path).load().revision.value
    create_status, headers, _ = post_form(
        app,
        "/revelations/new",
        {
            "csrf_token": "integration-token",
            "expected_revision": revision,
            "title": "The cellar connects to the old well",
            "description": "The improvised route reaches the buried well shaft.",
            "unlocks_encounter_id": "",
            "source_encounter_id": "alpha",
            "required": "1",
            "return_to": "/play?encounter=alpha",
        },
    )

    assert create_status == "303 See Other"
    assert headers["Location"] == (
        "/clues/new?source=alpha&revelation=the-cellar-connects-to-the-old-well"
        "&created_revelation=1&return_to=%2Fplay%3Fencounter%3Dalpha"
    )
