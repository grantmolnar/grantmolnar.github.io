"""Integration test for the local author-validate-play-render workflow."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID

import pytest

from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.bootstrap import main
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.local_adventure_workspace import (
    LocalAdventureWorkspace,
)
from adventure_graph.infrastructure.play_state_store import load_play_state
from adventure_graph.interfaces.web.workspace_app import WorkspaceWebApplication


def test_cli_init_assigns_distinct_uuid_identity_and_complete_project(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first starter"
    second = tmp_path / "second starter"

    assert main(["init", str(first)]) == 0
    assert main(["init", str(second)]) == 0

    first_adventure = load_adventure(first / "adventure.json")
    second_adventure = load_adventure(second / "adventure.json")
    first_state = load_play_state(first / "play-state.json")
    second_state = load_play_state(second / "play-state.json")

    assert UUID(first_adventure.id).version == 4
    assert UUID(second_adventure.id).version == 4
    assert first_adventure.id != second_adventure.id
    assert first_adventure.id != "the-glass-saint"
    assert first_state.adventure_id == first_adventure.id
    assert second_state.adventure_id == second_adventure.id
    assert (first / "generated").is_dir()
    assert (first / "archives").is_dir()


def test_cli_initializes_validates_tracks_and_renders(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "project"

    assert main(["init", str(project)]) == 0
    adventure = project / "adventure.json"
    state = project / "play-state.json"
    generated = project / "generated"
    reference_id = load_adventure(adventure).references[0].id

    assert main(["validate", str(adventure)]) == 0
    assert (
        main(
            [
                "visit",
                str(adventure),
                str(state),
                "the-shattered-gallery",
                "--clue",
                "accession-number-on-a-glass-shard",
                "--note",
                "The group copied the accession number.",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "note",
                str(adventure),
                str(state),
                "1",
                "They concealed this from the curator.",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "establish-revelation",
                str(adventure),
                str(state),
                "the-archive-vault-contains-the-relics-hidden-provenance",
                "--clue",
                "accession-number-on-a-glass-shard",
                "--note",
                "The accession number identifies the restricted vault.",
            ]
        )
        == 0
    )
    assert main(["visit", str(adventure), str(state), "the-archive-vault"]) == 0
    assert (
        main(
            [
                "spot-clue",
                str(adventure),
                str(state),
                "curator-incident-memorandum",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "consequence",
                str(adventure),
                str(state),
                "the-archive-vault",
                "The registrar now knows the group copied the ledger.",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "reference-note",
                str(adventure),
                str(state),
                reference_id,
                "The registrar now trusts the group.",
            ]
        )
        == 0
    )
    assert main(["render", str(adventure), str(generated), "--state", str(state)]) == 0

    summary = (generated / "05-play-summary.md").read_text(encoding="utf-8")
    assert "Accession number beneath the painted bone copy" in summary
    assert "They concealed this from the curator." in summary
    assert "Revelation established" in summary
    assert "The Archive Vault" in summary
    assert "The registrar now knows" in summary
    assert "The registrar now trusts the group." in summary
    assert (generated / "02-clue-list.md").is_file()
    assert (generated / "03-revelation-list.md").is_file()

    output = capsys.readouterr().out
    assert "PASS: no validation issues" in output
    assert (
        "Established revelation the-archive-vault-contains-the-relics-hidden-provenance" in output
    )
    assert "Unlocked encounter the-archive-vault" in output
    assert f"Added playthrough note to reference {reference_id}." in output


def test_cli_authoring_commands_append_consistent_records(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "authoring"
    assert main(["init", str(project)]) == 0
    adventure = project / "adventure.json"

    assert (
        main(
            [
                "add-encounter",
                str(adventure),
                "Hidden Dock",
                "--summary",
                "A concealed transfer point.",
                "--tag",
                "location",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "add-revelation",
                str(adventure),
                "Locate Hidden Dock",
                "--description",
                "The dock can be located.",
                "--unlocks",
                "hidden-dock",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "add-clue",
                str(adventure),
                "Salt-stained invoice",
                "--source",
                "the-shattered-gallery",
                "--revelation",
                "locate-hidden-dock",
            ]
        )
        == 0
    )

    authored = load_adventure(adventure)
    assert authored.encounter_index()["hidden-dock"].required
    assert authored.revelation_index()["locate-hidden-dock"].required

    output = capsys.readouterr().out
    assert "Added encounter Hidden Dock." in output
    assert "Added revelation Locate Hidden Dock." in output
    assert "Added lead Salt-stained invoice." in output


def test_cli_validate_prints_exact_cut_and_repair_candidates(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "diagnostics"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    payload = json.loads(adventure_path.read_text(encoding="utf-8"))
    retained = {
        "accession-number-on-a-glass-shard",
        "curator-incident-memorandum",
        "restorers-marginal-diagram",
        "copied-catalogue-folio",
        "winter-garden-timing-notes",
        "bell-rope-ritual-key",
    }
    payload["clues"] = [clue for clue in payload["clues"] if clue["id"] in retained]
    policy = payload["adventure"]["validation"]
    policy["minimum_clues_per_revelation"] = 0
    policy["minimum_source_encounters_per_revelation"] = 0
    policy["minimum_outgoing_clues_per_encounter"] = 0
    policy["minimum_distinct_encounter_targets_per_encounter"] = 0
    adventure_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    assert main(["validate", str(adventure_path)]) == 1

    output = capsys.readouterr().out
    assert "minimum cut A:" in output
    assert "minimum cut B:" in output
    assert "cut edges:" in output
    assert "additional cross-cut connections needed:" in output
    assert "candidate:" in output
    assert "repair:" in output


def test_cli_lists_and_inspects_authored_entities(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "queries"
    assert main(["init", str(project)]) == 0
    adventure = project / "adventure.json"

    assert main(["list", str(adventure), "encounter"]) == 0
    assert main(["inspect", str(adventure), "encounter", "the-shattered-gallery"]) == 0
    assert (
        main(
            [
                "inspect",
                str(adventure),
                "revelation",
                "the-archive-vault-contains-the-relics-hidden-provenance",
            ]
        )
        == 0
    )
    assert main(["inspect", str(adventure), "clue", "accession-number-on-a-glass-shard"]) == 0

    output = capsys.readouterr().out
    assert "Encounters (9):" in output
    assert "the-shattered-gallery: The Shattered Gallery [necessary, start]" in output
    assert (
        "Leads sourced here: accession-number-on-a-glass-shard, bell-metal-dust, "
        "vale-family-carriage-seal, service-door-witness-line" in output
    )
    assert (
        "Supporting leads: accession-number-on-a-glass-shard, copied-catalogue-folio, "
        "stolen-provenance-dossier, tavias-restricted-shelf-slip" in output
    )
    assert "Source encounter: the-shattered-gallery" in output
    assert "Destination encounter: the-archive-vault" in output


def test_cli_encounter_inspection_does_not_require_a_valid_companion_journal(
    tmp_path: Path,
) -> None:
    project = tmp_path / "inspection-with-broken-state"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    (project / "play-state.json").write_text("not valid JSON", encoding="utf-8")

    assert main(["inspect", str(adventure_path), "encounter", "the-shattered-gallery"]) == 0


def test_cli_title_edits_preserve_internal_ids_and_companion_play_state(
    tmp_path: Path,
) -> None:
    project = tmp_path / "rename"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    state_path = project / "play-state.json"
    assert (
        main(
            [
                "visit",
                str(adventure_path),
                str(state_path),
                "the-shattered-gallery",
                "--clue",
                "accession-number-on-a-glass-shard",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "establish-revelation",
                str(adventure_path),
                str(state_path),
                "the-archive-vault-contains-the-relics-hidden-provenance",
                "--clue",
                "accession-number-on-a-glass-shard",
            ]
        )
        == 0
    )

    assert (
        main(
            [
                "edit-encounter",
                str(adventure_path),
                "the-shattered-gallery",
                "--title",
                "Glass Gallery",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "edit-revelation",
                str(adventure_path),
                "the-archive-vault-contains-the-relics-hidden-provenance",
                "--title",
                "Find Archive",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "edit-clue",
                str(adventure_path),
                "accession-number-on-a-glass-shard",
                "--title",
                "Accession Shard",
            ]
        )
        == 0
    )

    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    projection = project_play_state(adventure, state)
    assert projection.visits[0].encounter_id == "the-shattered-gallery"
    assert projection.spotted_clue_ids == ("accession-number-on-a-glass-shard",)
    progress = projection.revelation_progress_index()[
        "the-archive-vault-contains-the-relics-hidden-provenance"
    ]
    assert progress.is_established
    assert progress.establishment_clue_ids == ("accession-number-on-a-glass-shard",)
    assert (
        adventure.clue_index()["accession-number-on-a-glass-shard"].source_encounter_id
        == "the-shattered-gallery"
    )
    assert adventure.encounter_index()["the-shattered-gallery"].title == "Glass Gallery"
    assert (
        adventure.revelation_index()[
            "the-archive-vault-contains-the-relics-hidden-provenance"
        ].title
        == "Find Archive"
    )


def test_cli_refuses_structural_edits_that_invalidate_companion_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "unsafe-edit"
    assert main(["init", str(project)]) == 0
    adventure = project / "adventure.json"
    state = project / "play-state.json"
    assert (
        main(
            [
                "visit",
                str(adventure),
                str(state),
                "the-shattered-gallery",
                "--clue",
                "accession-number-on-a-glass-shard",
            ]
        )
        == 0
    )
    before = adventure.read_bytes()

    assert (
        main(
            ["move-clue", str(adventure), "accession-number-on-a-glass-shard", "the-archive-vault"]
        )
        == 2
    )
    assert adventure.read_bytes() == before
    assert main(["remove-clue", str(adventure), "accession-number-on-a-glass-shard"]) == 2
    assert adventure.read_bytes() == before
    assert main(["edit-encounter", str(adventure), "the-shattered-gallery", "--not-start"]) == 2
    assert adventure.read_bytes() == before

    error = capsys.readouterr().err
    assert "would be invalid after this change" in error
    assert "belongs to encounter" in error or "Unknown lead" in error
    assert "visits locked encounter" in error


def test_cli_authoring_uses_explicit_related_journal_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "explicit-related-state"
    assert main(["init", str(project)]) == 0
    adventure = project / "adventure.json"
    external_state = tmp_path / "external-play-state.json"
    assert (
        main(
            [
                "visit",
                str(adventure),
                str(external_state),
                "the-shattered-gallery",
                "--clue",
                "accession-number-on-a-glass-shard",
            ]
        )
        == 0
    )
    before = adventure.read_bytes()

    assert (
        main(
            [
                "move-clue",
                str(adventure),
                "accession-number-on-a-glass-shard",
                "the-archive-vault",
                "--state",
                str(external_state),
            ]
        )
        == 2
    )
    assert adventure.read_bytes() == before
    assert "would be invalid after this change" in capsys.readouterr().err


def test_cli_dependency_aware_removal_refuses_then_cascades(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "removal"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    before = adventure_path.read_bytes()

    assert main(["remove-encounter", str(adventure_path), "the-archive-vault"]) == 2
    assert adventure_path.read_bytes() == before
    refusal = capsys.readouterr().err
    assert "authored dependencies exist" in refusal
    assert "source leads" in refusal
    assert "unlocking revelations" in refusal

    assert (
        main(
            [
                "remove-encounter",
                str(adventure_path),
                "the-archive-vault",
                "--cascade",
            ]
        )
        == 0
    )
    adventure = load_adventure(adventure_path)
    assert "the-archive-vault" not in adventure.encounter_index()
    assert all(clue.source_encounter_id != "the-archive-vault" for clue in adventure.clues)
    assert (
        adventure.revelation_index()[
            "the-archive-vault-contains-the-relics-hidden-provenance"
        ].unlocks_encounter_id
        is None
    )
    output = capsys.readouterr().out
    assert "Cascade removed 10 source lead(s)" in output
    assert "cleared 1 revelation destination(s)" in output


def test_cli_edit_commands_and_focused_move_apply_safe_changes(tmp_path: Path) -> None:
    project = tmp_path / "editing"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"

    assert (
        main(
            [
                "edit-encounter",
                str(adventure_path),
                "the-shattered-gallery",
                "--title",
                "The Broken Gallery",
                "--end",
                "--optional",
                "--tag",
                "location",
                "--tag",
                "glass",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "edit-revelation",
                str(adventure_path),
                "vale-manor-is-the-conspiracys-operational-center",
                "--title",
                "Identify Vale Manor",
                "--optional",
                "--clear-unlocks",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "edit-clue",
                str(adventure_path),
                "bell-rope-ritual-key",
                "--title",
                "A revised invitation",
                "--discovery",
                "automatic",
            ]
        )
        == 0
    )
    assert main(["move-clue", str(adventure_path), "bell-rope-ritual-key", "the-bell-chapel"]) == 0

    adventure = load_adventure(adventure_path)
    encounter = adventure.encounter_index()["the-shattered-gallery"]
    assert encounter.title == "The Broken Gallery"
    assert encounter.end
    assert not encounter.required
    assert encounter.tags == ("location", "glass")
    revelation = adventure.revelation_index()["vale-manor-is-the-conspiracys-operational-center"]
    assert revelation.title == "Identify Vale Manor"
    assert not revelation.required
    assert revelation.unlocks_encounter_id is None
    clue = adventure.clue_index()["bell-rope-ritual-key"]
    assert clue.title == "A revised invitation"
    assert clue.discovery == "automatic"
    assert clue.source_encounter_id == "the-bell-chapel"


def test_cli_ui_wires_authoring_use_cases_without_starting_a_real_server(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "authoring-ui"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    captured: dict[str, object] = {}
    workspace_open_count = 0

    class RecordingWorkspace(LocalAdventureWorkspace):
        def select_initial_adventure(self, path: Path) -> None:
            captured["initial_selection"] = path
            super().select_initial_adventure(path)

    def open_workspace(root: Path) -> LocalAdventureWorkspace:
        nonlocal workspace_open_count
        workspace_open_count += 1
        return RecordingWorkspace(root)

    def fake_serve(
        app: object,
        *,
        host: str,
        port: int,
        open_browser: bool,
    ) -> None:
        assert isinstance(app, WorkspaceWebApplication)
        workspace = app.queries.get_workspace()
        selected = workspace.selected_adventure
        assert selected is not None
        adventure_app = app.adventure_application(selected.key, app.csrf_token)
        captured["title"] = adventure_app.queries.get_overview().adventure.title
        encounter = adventure_app.queries.get_encounter("the-shattered-gallery")
        captured["encounter"] = encounter.detail.encounter.title
        captured["can_update_encounter"] = callable(adventure_app.commands.update_encounter)
        captured["host"] = host
        captured["port"] = port
        captured["open_browser"] = open_browser

    monkeypatch.setattr("adventure_graph.bootstrap.LocalAdventureWorkspace", open_workspace)
    monkeypatch.setattr("adventure_graph.bootstrap.serve_web_app", fake_serve)

    assert (
        main(
            [
                "ui",
                str(adventure_path),
                "--host",
                "localhost",
                "--port",
                "0",
                "--no-browser",
            ]
        )
        == 0
    )
    assert workspace_open_count == 1
    assert captured == {
        "title": "The Glass Saint",
        "encounter": "The Shattered Gallery",
        "can_update_encounter": True,
        "host": "localhost",
        "port": 0,
        "open_browser": False,
        "initial_selection": adventure_path,
    }


def test_cli_correct_latest_appends_audit_event_and_voids_operation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "correction"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    state_path = project / "play-state.json"

    assert (
        main(
            [
                "visit",
                str(adventure_path),
                str(state_path),
                "the-shattered-gallery",
                "--clue",
                "accession-number-on-a-glass-shard",
                "--note",
                "This operation was accidental.",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "correct-latest",
                str(adventure_path),
                str(state_path),
                "--reason",
                "The group never entered the gallery.",
            ]
        )
        == 0
    )

    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    projection = project_play_state(adventure, state)

    assert state.active_events == ()
    assert projection.visits == ()
    assert projection.corrections[0].target_operation_number == 1
    assert "Corrected play operation 1" in capsys.readouterr().out


def test_cli_records_multi_session_missed_then_found_history(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    project = tmp_path / "sessions"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    state_path = project / "play-state.json"
    clue_id = "accession-number-on-a-glass-shard"
    revelation_id = "the-archive-vault-contains-the-relics-hidden-provenance"

    assert (
        main(
            [
                "start-session",
                str(adventure_path),
                str(state_path),
                "--title",
                "The Gallery",
                "--played-on",
                "2026-07-18",
                "--participant",
                "Mara",
                "--participant",
                "Sera",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "visit",
                str(adventure_path),
                str(state_path),
                "the-shattered-gallery",
                "--party",
                "Mara and Sera",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "miss-clue",
                str(adventure_path),
                str(state_path),
                clue_id,
                "--visit",
                "1",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "foreclose-revelation",
                str(adventure_path),
                str(state_path),
                revelation_id,
                "--reason",
                "The registrar sealed the archive.",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "reopen-revelation",
                str(adventure_path),
                str(state_path),
                revelation_id,
                "--reason",
                "The curator produced a warrant.",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "end-session",
                str(adventure_path),
                str(state_path),
                "--closing-note",
                "The group withdrew to compare notes.",
            ]
        )
        == 0
    )
    assert main(["visit", str(adventure_path), str(state_path), "the-shattered-gallery"]) == 2
    assert main(["start-session", str(adventure_path), str(state_path), "--title", "Return"]) == 0
    assert (
        main(
            [
                "visit",
                str(adventure_path),
                str(state_path),
                "the-shattered-gallery",
                "--party",
                "Mara",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "spot-clue",
                str(adventure_path),
                str(state_path),
                clue_id,
                "--visit",
                "2",
            ]
        )
        == 0
    )

    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    projection = project_play_state(adventure, state)

    assert [session.title for session in projection.sessions] == ["The Gallery", "Return"]
    assert projection.sessions[0].visit_numbers == (1,)
    assert projection.sessions[1].visit_numbers == (2,)
    assert projection.active_session_number == 2
    assert projection.visits[0].party_label == "Mara and Sera"
    assert projection.visits[1].party_label == "Mara"
    clue = projection.clue_progress_index()[clue_id]
    assert clue.missed_visit_numbers == (1,)
    assert clue.spotted_visit_number == 2
    assert not projection.revelation_progress_index()[revelation_id].is_foreclosed

    captured = capsys.readouterr()
    assert "Started session 1." in captured.out
    assert "Marked lead accession-number-on-a-glass-shard missed." in captured.out
    assert "Explicit sessions have begun" in captured.err


def test_cli_creation_allows_omitted_optional_encounter_and_revelation_prose(
    tmp_path: Path,
) -> None:
    project = tmp_path / "minimal-cli-authoring"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"

    assert (
        main(
            [
                "add-encounter",
                str(adventure_path),
                "A Spare Room",
                "--optional",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "add-revelation",
                str(adventure_path),
                "An Unwritten Truth",
                "--optional",
            ]
        )
        == 0
    )

    adventure = load_adventure(adventure_path)
    assert adventure.encounter_index()["a-spare-room"].summary == ""
    assert adventure.revelation_index()["an-unwritten-truth"].description == ""
