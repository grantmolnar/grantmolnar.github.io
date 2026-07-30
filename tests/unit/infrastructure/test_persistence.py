"""Tests for canonical JSON persistence."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)

from adventure_graph.application.authoring import (
    remap_play_state_identifiers,
    rename_encounter,
)
from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.application.play_tracking import (
    add_visit_note,
    correct_latest_operation,
    end_session,
    establish_revelation,
    foreclose_revelation,
    miss_clue,
    new_play_state,
    project_play_state,
    record_visit,
    reopen_revelation,
    start_session,
)
from adventure_graph.application.project import RevisionConflictError
from adventure_graph.domain.adventure import AdventureTags
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    DiceGroupResult,
    DiceModifierResult,
    DiceRollRecordedEvent,
    EncounterVisitedEvent,
    PlayOperationVoidedEvent,
    RevelationForeclosedEvent,
    RevelationReopenedEvent,
    SessionEndedEvent,
    SessionStartedEvent,
)
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import (
    load_adventure,
    save_adventure,
)
from adventure_graph.infrastructure.atomic_files import write_json_object
from adventure_graph.infrastructure.authoring_store import save_authoring_bundle
from adventure_graph.infrastructure.journal_archive_store import (
    JournalArchive,
    journal_archive_data,
    load_journal_archive,
    restore_journal_archive,
    save_archive_and_reset,
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


def test_adventure_round_trip_preserves_domain_model(tmp_path: Path) -> None:
    path = tmp_path / "adventure.json"
    adventure = complete_four_encounter_adventure()

    save_adventure(path, adventure)

    assert load_adventure(path) == adventure


def test_pre_beta_adventure_schema_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "legacy-adventure.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "adventure": {
                    "id": "legacy",
                    "title": "Legacy",
                    "premise": "Old combined synopsis.",
                    "truth": "Old explanation.",
                },
                "encounters": [],
                "revelations": [],
                "clues": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Only adventure schema_version 3 is supported"):
        load_adventure(path)


@pytest.mark.parametrize("schema_version", [1, 2, 3, 4, 5])
def test_pre_beta_play_state_schemas_are_rejected(tmp_path: Path, schema_version: int) -> None:
    path = tmp_path / f"legacy-play-state-v{schema_version}.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "adventure_id": "complete-four",
                "events": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Only play-state schema_version 6 is supported"):
        load_play_state(path)


def test_play_state_v6_round_trip_preserves_event_order(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(
        adventure,
        new_play_state(adventure),
        "alpha",
        ("alpha-to-beta",),
        ("A note.",),
    )
    state = establish_revelation(adventure, state, "find-beta", ("alpha-to-beta",))
    path = tmp_path / "play-state.json"

    save_play_state(path, state)

    assert load_play_state(path) == state
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["schema_version"] == 6
    assert [event["type"] for event in raw["events"]] == [
        "encounter_visited",
        "clue_spotted",
        "visit_note_recorded",
        "revelation_established",
        "encounter_unlocked",
    ]
    assert raw["events"][0]["party_label"] == ""


def test_authoring_bundle_commits_adventure_and_related_states(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    updated_adventure = rename_encounter(adventure, "alpha", "atrium")
    updated_state = remap_play_state_identifiers(state, encounter_ids={"alpha": "atrium"})
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"

    save_authoring_bundle(adventure_path, updated_adventure, {state_path: updated_state})

    assert load_adventure(adventure_path) == updated_adventure
    assert load_play_state(state_path) == updated_state


def test_authoring_bundle_rolls_back_when_a_later_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, state)
    original_adventure = adventure_path.read_bytes()
    original_state = state_path.read_bytes()

    updated_adventure = rename_encounter(adventure, "alpha", "atrium")
    updated_state = remap_play_state_identifiers(state, encounter_ids={"alpha": "atrium"})
    original_replace = Path.replace
    failed = False

    def fail_once_for_state(source: Path, target: str | Path) -> Path:
        nonlocal failed
        if Path(target) == state_path and not failed:
            failed = True
            raise OSError("simulated replacement failure")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_once_for_state)

    with pytest.raises(OSError, match="simulated replacement failure"):
        save_authoring_bundle(adventure_path, updated_adventure, {state_path: updated_state})

    assert adventure_path.read_bytes() == original_adventure
    assert state_path.read_bytes() == original_state


def test_journal_archive_round_trip_preserves_snapshot_and_events(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha", ("alpha-to-beta",))
    archive = JournalArchive(
        archive_id="first-run",
        label="First run",
        archived_at="2026-07-12T18:00:00Z",
        source_state_name="play-state.json",
        adventure_snapshot=adventure,
        play_state=state,
    )
    path = tmp_path / "first-run.journal.json"

    write_json_object(path, journal_archive_data(archive))

    assert load_journal_archive(path) == archive


def test_archive_reset_and_restore_preserve_both_canonical_documents(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    active = record_visit(adventure, new_play_state(adventure), "alpha", ("alpha-to-beta",))
    state_path = tmp_path / "play-state.json"
    archive_path = tmp_path / "archives" / "first-run.journal.json"
    save_play_state(state_path, active)
    original_active_payload = state_path.read_bytes()
    archive = JournalArchive(
        archive_id="first-run",
        label="First run",
        archived_at="2026-07-12T18:00:00Z",
        source_state_name=state_path.name,
        adventure_snapshot=adventure,
        play_state=active,
    )

    save_archive_and_reset(archive_path, archive, state_path, new_play_state(adventure))

    assert load_journal_archive(archive_path) == archive
    assert load_play_state(state_path) == new_play_state(adventure)
    original_archive_payload = archive_path.read_bytes()

    restore_journal_archive(archive_path, state_path, archive.play_state)

    assert archive_path.read_bytes() == original_archive_payload
    assert state_path.read_bytes() == original_active_payload
    assert load_journal_archive(archive_path) == archive
    assert load_play_state(state_path) == active


def test_restore_archive_preserves_both_files_when_state_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adventure = complete_four_encounter_adventure()
    archived_state = record_visit(adventure, new_play_state(adventure), "alpha")
    active_state = new_play_state(adventure)
    state_path = tmp_path / "play-state.json"
    archive_path = tmp_path / "first-run.journal.json"
    save_play_state(state_path, archived_state)
    archive = JournalArchive(
        archive_id="first-run",
        label="",
        archived_at="2026-07-12T18:00:00Z",
        source_state_name=state_path.name,
        adventure_snapshot=adventure,
        play_state=archived_state,
    )
    save_archive_and_reset(archive_path, archive, state_path, active_state)
    original_state = state_path.read_bytes()
    original_archive = archive_path.read_bytes()
    original_replace = Path.replace
    failed = False

    def fail_once_for_active_state(source: Path, target: str | Path) -> Path:
        nonlocal failed
        if Path(target) == state_path and not failed:
            failed = True
            raise OSError("simulated restore failure")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_once_for_active_state)

    with pytest.raises(OSError, match="simulated restore failure"):
        restore_journal_archive(archive_path, state_path, archived_state)

    assert state_path.read_bytes() == original_state
    assert archive_path.read_bytes() == original_archive


def test_restore_journal_archive_requires_the_source_archive(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    state_path = tmp_path / "play-state.json"
    missing_archive = tmp_path / "missing.journal.json"
    empty_state = new_play_state(adventure)
    restored_state = record_visit(adventure, empty_state, "alpha")
    save_play_state(state_path, empty_state)
    original_state = state_path.read_bytes()

    with pytest.raises(FileNotFoundError, match="Archive does not exist"):
        restore_journal_archive(missing_archive, state_path, restored_state)

    assert state_path.read_bytes() == original_state


def test_journal_archive_rejects_inconsistent_event_count(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    archive = JournalArchive(
        archive_id="tampered",
        label="",
        archived_at="2026-07-12T18:00:00Z",
        source_state_name="play-state.json",
        adventure_snapshot=adventure,
        play_state=state,
    )
    payload = journal_archive_data(archive)
    payload["archive"]["event_count"] = 99
    path = tmp_path / "tampered.journal.json"
    write_json_object(path, payload)

    with pytest.raises(ValueError, match="event_count does not match"):
        load_journal_archive(path)


def test_local_authoring_project_revision_tracks_adventure_and_related_state(
    tmp_path: Path,
) -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, state)
    project = LocalAuthoringProject(adventure_path)

    before = project.load()
    save_play_state(state_path, add_visit_note(state, 1, "Changed."))
    after = project.load()

    assert before.adventure == adventure
    assert before.related_play_states[0].state == state
    assert before.revision != after.revision


def test_local_authoring_project_refuses_revision_conflict(tmp_path: Path) -> None:

    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    save_adventure(adventure_path, adventure)
    project = LocalAuthoringProject(adventure_path)
    snapshot = project.load()
    external = replace(adventure, title="External edit")
    save_adventure(adventure_path, external)

    with pytest.raises(RevisionConflictError, match="changed after this encounter was loaded"):
        project.commit_adventure(replace(adventure, title="Local edit"), snapshot.revision)

    assert load_adventure(adventure_path) == external


def test_correction_event_round_trip_preserves_voided_operation(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    state = correct_latest_operation(adventure, state, "Wrong visit.")
    path = tmp_path / "play-state.json"

    save_play_state(path, state)
    loaded = load_play_state(path)

    assert loaded == state
    assert isinstance(loaded.events[-1], PlayOperationVoidedEvent)
    assert loaded.active_events == ()


def test_local_play_journal_refuses_stale_commit(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, record_visit(adventure, new_play_state(adventure), "alpha"))
    project = LocalPlayJournalProject(adventure_path, state_path)
    snapshot = project.load()
    external = add_visit_note(snapshot.state, 1, "External change.")
    save_play_state(state_path, external)

    with pytest.raises(RevisionConflictError, match="changed after this history was loaded"):
        project.commit_state(snapshot.state, snapshot.revision)

    assert load_play_state(state_path) == external


def test_local_generated_report_project_refuses_stale_source_revision(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    output_path = tmp_path / "generated"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, new_play_state(adventure))
    journal = LocalPlayJournalProject(adventure_path, state_path)
    project = LocalGeneratedReportProject(journal, output_path)
    snapshot = project.load()
    save_play_state(state_path, record_visit(adventure, snapshot.state, "alpha"))

    with pytest.raises(RevisionConflictError, match="changed after these reports were loaded"):
        project.publish({"report.md": "# Stale"}, snapshot.revision)

    assert not output_path.exists()


def test_local_generated_report_project_writes_nested_reference_documents(tmp_path: Path) -> None:
    adventure = reference_library_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    output_path = tmp_path / "generated"
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, new_play_state(adventure))
    journal = LocalPlayJournalProject(adventure_path, state_path)
    project = LocalGeneratedReportProject(journal, output_path)
    snapshot = project.load()
    documents = render_adventure_documents(adventure, validate_adventure(adventure))

    names = project.publish(documents, snapshot.revision)

    assert "references/index.md" in names
    assert f"references/{PERSON_REFERENCE_ID}.md" in names
    assert (output_path / "references" / "index.md").exists()
    sheet = output_path / "references" / f"{PERSON_REFERENCE_ID}.md"
    assert sheet.exists()
    assert "Cora controls access to the first-floor rooms." in sheet.read_text()


def test_local_archive_project_revision_tracks_catalog_and_refuses_stale_mutation(
    tmp_path: Path,
) -> None:
    adventure = complete_four_encounter_adventure()
    adventure_path = tmp_path / "adventure.json"
    state_path = tmp_path / "play-state.json"
    archive_directory = tmp_path / "archives"
    active = record_visit(adventure, new_play_state(adventure), "alpha")
    save_adventure(adventure_path, adventure)
    save_play_state(state_path, active)
    project = LocalJournalArchiveProject(adventure_path, state_path, archive_directory)
    snapshot = project.load()
    archive = JournalArchive(
        archive_id="first-run",
        label="First run",
        archived_at="2026-07-13T18:00:00Z",
        source_state_name=state_path.name,
        adventure_snapshot=adventure,
        play_state=active,
    )
    save_play_state(state_path, add_visit_note(active, 1, "External change."))

    with pytest.raises(RevisionConflictError, match="archive catalog changed"):
        project.create_and_reset(archive, new_play_state(adventure), snapshot.revision)

    assert not archive_directory.exists()


def test_adventure_discovery_tags_round_trip_canonically(tmp_path: Path) -> None:
    path = tmp_path / "tagged.json"
    adventure = replace(
        complete_four_encounter_adventure(),
        tags=AdventureTags(
            genres=("Investigation", "Horror"),
            game_systems=("System-agnostic",),
            settings=("Original fantasy",),
            party_size_min=3,
            party_size_max=5,
            level_min=2,
            level_max=4,
            combat_intensity="light",
            keywords=("Museum", "Deadline"),
        ),
    )

    save_adventure(path, adventure)
    loaded = load_adventure(path)

    assert loaded.tags == adventure.tags
    assert json.loads(path.read_text())["adventure"]["tags"]["party_size"] == {
        "minimum": 3,
        "maximum": 5,
    }


def test_missing_current_schema_attributes_load_with_defaults_and_save_canonically(
    tmp_path: Path,
) -> None:
    path = tmp_path / "sparse-adventure.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "adventure": {"id": "sparse", "title": "Sparse Adventure"},
                "encounters": [{"id": "arrival", "title": "Arrival"}],
                "revelations": [{"id": "learn-truth", "title": "Learn the truth"}],
                "clues": [
                    {
                        "id": "first-sign",
                        "title": "First sign",
                        "source_encounter_id": "arrival",
                        "revelation_id": "learn-truth",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    adventure = load_adventure(path)

    assert adventure.synopsis == adventure.premise == adventure.explanation == ""
    assert adventure.encounters[0].summary == ""
    assert adventure.encounters[0].opening_view == ""
    assert adventure.encounters[0].content == ""
    assert adventure.encounters[0].required
    assert not adventure.encounters[0].start
    assert not adventure.encounters[0].end
    assert adventure.encounters[0].tags == ()
    assert adventure.encounters[0].reference_links == ()
    assert adventure.references == ()
    assert adventure.revelations[0].description == ""
    assert adventure.revelations[0].unlocks_encounter_id is None
    assert adventure.revelations[0].required
    assert adventure.clues[0].description == ""
    assert adventure.clues[0].discovery == "search"

    save_adventure(path, adventure)
    raw = json.loads(path.read_text(encoding="utf-8"))

    assert raw["adventure"] == {
        "id": "sparse",
        "title": "Sparse Adventure",
        "synopsis": "",
        "premise": "",
        "explanation": "",
        "tags": {
            "genres": [],
            "game_systems": [],
            "settings": [],
            "party_size": {"minimum": None, "maximum": None},
            "level": {"minimum": None, "maximum": None},
            "combat_intensity": None,
            "keywords": [],
        },
        "validation": {
            "minimum_clues_per_revelation": 3,
            "minimum_source_encounters_per_revelation": 3,
            "minimum_incoming_clues_per_encounter": 3,
            "minimum_incoming_source_encounters_per_encounter": 3,
            "minimum_outgoing_clues_per_encounter": 3,
            "minimum_distinct_encounter_targets_per_encounter": 3,
            "minimum_edge_connectivity": 3,
            "require_directed_reachability": True,
        },
    }
    assert raw["references"] == []
    assert raw["encounters"][0] == {
        "id": "arrival",
        "title": "Arrival",
        "summary": "",
        "opening_view": "",
        "content": "",
        "required": True,
        "start": False,
        "end": False,
        "tags": [],
        "reference_links": [],
    }
    assert raw["revelations"][0] == {
        "id": "learn-truth",
        "title": "Learn the truth",
        "description": "",
        "unlocks_encounter_id": None,
        "required": True,
    }
    assert raw["clues"][0] == {
        "id": "first-sign",
        "title": "First sign",
        "source_encounter_id": "arrival",
        "revelation_id": "learn-truth",
        "description": "",
        "discovery": "search",
    }


@pytest.mark.parametrize(
    ("tags", "message"),
    [
        ([], "tags must be an object"),
        ({"party_size": []}, "party_size must be an object"),
        ({"level": []}, "level must be an object"),
        ({"combat_intensity": "extreme"}, "combat intensity is unsupported"),
    ],
)
def test_malformed_adventure_discovery_tags_are_rejected(
    tmp_path: Path,
    tags: object,
    message: str,
) -> None:
    path = tmp_path / "malformed-tags.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "adventure": {
                    "id": "malformed-tags",
                    "title": "Malformed Tags",
                    "tags": tags,
                },
                "encounters": [],
                "revelations": [],
                "clues": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        load_adventure(path)


def test_present_current_schema_attribute_with_wrong_type_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "malformed-adventure.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "adventure": {
                    "id": "malformed",
                    "title": "Malformed",
                    "explanation": ["not", "text"],
                },
                "encounters": [],
                "revelations": [],
                "clues": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="explanation must be a string"):
        load_adventure(path)


def test_reference_library_round_trip_writes_complete_canonical_shape(tmp_path: Path) -> None:
    path = tmp_path / "references.json"
    adventure = reference_library_adventure()

    save_adventure(path, adventure)

    assert load_adventure(path) == adventure
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["references"][0] == {
        "id": PERSON_REFERENCE_ID,
        "kind": "person",
        "title": "Cora Pike",
        "aliases": ["The Housekeeper"],
        "summary": "The hall's observant housekeeper.",
        "content": "## Cora Pike\n\nCora protects the household before its owner.",
        "tags": ["staff", "witness"],
    }
    assert raw["encounters"][0]["reference_links"][0] == {
        "reference_id": PERSON_REFERENCE_ID,
        "context": "Cora controls access to the first-floor rooms.",
    }


def test_sparse_reference_fields_receive_defaults_and_save_completely(tmp_path: Path) -> None:
    path = tmp_path / "sparse-references.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "adventure": {"id": "sparse-references", "title": "Sparse References"},
                "references": [
                    {
                        "id": PERSON_REFERENCE_ID,
                        "kind": "person",
                        "title": "Cora Pike",
                    }
                ],
                "encounters": [
                    {
                        "id": "arrival",
                        "title": "Arrival",
                        "reference_links": [{"reference_id": PERSON_REFERENCE_ID}],
                    }
                ],
                "revelations": [],
                "clues": [],
            }
        ),
        encoding="utf-8",
    )

    adventure = load_adventure(path)

    assert adventure.references[0].aliases == ()
    assert adventure.references[0].summary == ""
    assert adventure.references[0].content == ""
    assert adventure.references[0].tags == ()
    assert adventure.encounters[0].reference_links[0].context == ""

    save_adventure(path, adventure)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["references"][0] == {
        "id": PERSON_REFERENCE_ID,
        "kind": "person",
        "title": "Cora Pike",
        "aliases": [],
        "summary": "",
        "content": "",
        "tags": [],
    }
    assert raw["encounters"][0]["reference_links"] == [
        {"reference_id": PERSON_REFERENCE_ID, "context": ""}
    ]


@pytest.mark.parametrize(
    ("reference_patch", "message"),
    [
        ({"id": "not-a-uuid"}, "canonical UUIDv4"),
        ({"kind": "faction"}, "kind is unsupported"),
        ({"title": " Cora Pike"}, "title must be a nonempty trimmed string"),
        ({"aliases": ["Cora Pike"]}, "aliases must not duplicate the title"),
        ({"aliases": ["Housekeeper", "housekeeper"]}, "aliases must be unique"),
        ({"tags": [" witness"]}, "tags must be nonempty trimmed strings"),
    ],
)
def test_malformed_reference_values_are_rejected(
    tmp_path: Path, reference_patch: dict[str, object], message: str
) -> None:
    path = tmp_path / "malformed-reference.json"
    reference = {
        "id": PERSON_REFERENCE_ID,
        "kind": "person",
        "title": "Cora Pike",
    }
    reference.update(reference_patch)
    path.write_text(
        json.dumps(
            {
                "schema_version": 3,
                "adventure": {"id": "malformed-reference", "title": "Malformed Reference"},
                "references": [reference],
                "encounters": [],
                "revelations": [],
                "clues": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        load_adventure(path)


def test_archive_round_trip_preserves_references_and_links(tmp_path: Path) -> None:
    adventure = reference_library_adventure()
    archive = JournalArchive(
        archive_id="reference-run",
        label="Reference run",
        archived_at="2026-07-25T18:00:00Z",
        source_state_name="play-state.json",
        adventure_snapshot=adventure,
        play_state=record_visit(adventure, new_play_state(adventure), "alpha"),
    )
    path = tmp_path / "reference-run.journal.json"

    write_json_object(path, journal_archive_data(archive))

    loaded = load_journal_archive(path)
    assert loaded == archive
    assert loaded.adventure_snapshot.reference_index()[PERSON_REFERENCE_ID].title == "Cora Pike"
    assert loaded.adventure_snapshot.encounters[0].reference_links[0].reference_id == (
        PERSON_REFERENCE_ID
    )


def test_play_state_v6_round_trips_sessions_judgments_misses_and_recorded_rolls(
    tmp_path: Path,
) -> None:
    adventure = complete_four_encounter_adventure()
    state = start_session(
        new_play_state(adventure),
        title="The Hall",
        played_on="2026-07-18",
        participants=("Mara", "Sera"),
    )
    state = record_visit(adventure, state, "alpha", party_label="Main party")
    state = miss_clue(adventure, state, "alpha-to-beta", 1)
    state = foreclose_revelation(adventure, state, "find-beta", "The witness departed.")
    state = reopen_revelation(adventure, state, "find-beta", "The witness returned.")
    state = replace(
        state,
        events=(
            *state.events,
            DiceRollRecordedEvent(
                sequence=len(state.events) + 1,
                expression="2d8 + 3",
                label="Hold the gate",
                terms=(DiceGroupResult(1, 8, (6, 3)), DiceModifierResult(3)),
                total=12,
                operation_number=state.events[-1].operation_number + 1,
            ),
        ),
    )
    project_play_state(adventure, state)
    state = end_session(state, "The party withdrew.")
    path = tmp_path / "play-state.json"

    save_play_state(path, state)
    loaded = load_play_state(path)

    assert loaded == state
    assert [type(event) for event in loaded.events] == [
        SessionStartedEvent,
        EncounterVisitedEvent,
        ClueMissedEvent,
        RevelationForeclosedEvent,
        RevelationReopenedEvent,
        DiceRollRecordedEvent,
        SessionEndedEvent,
    ]
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["events"][1]["party_label"] == "Main party"
    assert raw["events"][5]["terms"] == [
        {"kind": "dice", "sign": 1, "faces": 8, "results": [6, 3]},
        {"kind": "modifier", "value": 3},
    ]


def test_sparse_v6_visit_loads_safe_party_label_default(tmp_path: Path) -> None:
    path = tmp_path / "sparse-v6.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 6,
                "adventure_id": "complete-four",
                "events": [
                    {
                        "sequence": 1,
                        "operation_number": 1,
                        "type": "encounter_visited",
                        "visit_number": 1,
                        "encounter_id": "alpha",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    state = load_play_state(path)

    assert isinstance(state.events[0], EncounterVisitedEvent)
    assert state.events[0].party_label == ""


def test_journal_archive_rejects_invalid_embedded_identifier(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    archive = JournalArchive(
        archive_id="invalid/name",
        label="",
        archived_at="2026-07-12T18:00:00Z",
        source_state_name="play-state.json",
        adventure_snapshot=adventure,
        play_state=state,
    )

    with pytest.raises(ValueError, match="Archive identifiers must contain only"):
        journal_archive_data(archive)


def test_journal_archive_loader_rejects_filename_identity_mismatch(tmp_path: Path) -> None:
    adventure = complete_four_encounter_adventure()
    state = record_visit(adventure, new_play_state(adventure), "alpha")
    archive = JournalArchive(
        archive_id="canonical-name",
        label="",
        archived_at="2026-07-12T18:00:00Z",
        source_state_name="play-state.json",
        adventure_snapshot=adventure,
        play_state=state,
    )
    path = tmp_path / "renamed-copy.journal.json"
    write_json_object(path, journal_archive_data(archive))

    with pytest.raises(ValueError, match="does not match embedded identifier"):
        load_journal_archive(path)
