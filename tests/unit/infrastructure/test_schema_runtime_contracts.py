"""Contracts between runtime JSON decoders and the published schemas."""

from __future__ import annotations

import json
from collections.abc import Callable
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest
from tests.support.adventures import (
    complete_four_encounter_adventure,
    reference_library_adventure,
)
from tests.support.paths import PROJECT_ROOT

from adventure_graph.application.archive_management import JournalArchiveSnapshot
from adventure_graph.application.workspace_management import WorkspaceSettings
from adventure_graph.domain.play_events import (
    ClueMissedEvent,
    ClueSpottedEvent,
    DiceGroupResult,
    DiceModifierResult,
    DiceRollRecordedEvent,
    EncounterConsequenceRecordedEvent,
    EncounterUnlockedEvent,
    EncounterVisitedEvent,
    PlayEvent,
    PlayEventKind,
    PlayOperationVoidedEvent,
    ReferenceNoteRecordedEvent,
    RevelationEstablishedEvent,
    RevelationForeclosedEvent,
    RevelationReopenedEvent,
    SessionEndedEvent,
    SessionStartedEvent,
    VisitNoteRecordedEvent,
)
from adventure_graph.domain.play_state import PlayState
from adventure_graph.infrastructure.adventure_store import (
    ADVENTURE_METADATA_FIELDS,
    ADVENTURE_ROOT_FIELDS,
    ADVENTURE_TAG_FIELDS,
    CLUE_FIELDS,
    ENCOUNTER_FIELDS,
    OPTIONAL_POSITIVE_RANGE_FIELDS,
    REFERENCE_FIELDS,
    REFERENCE_LINK_FIELDS,
    REVELATION_FIELDS,
    VALIDATION_POLICY_FIELDS,
    adventure_data,
    adventure_from_data,
)
from adventure_graph.infrastructure.journal_archive_store import (
    JOURNAL_ARCHIVE_METADATA_FIELDS,
    JOURNAL_ARCHIVE_ROOT_FIELDS,
    journal_archive_data,
    journal_archive_from_data,
)
from adventure_graph.infrastructure.json_values import JsonObject, UnsupportedFieldError
from adventure_graph.infrastructure.local_adventure_workspace import (
    WORKSPACE_SETTINGS_ROOT_FIELDS,
    WORKSPACE_VALIDATOR_DEFAULT_FIELDS,
    workspace_settings_data,
    workspace_settings_from_data,
)
from adventure_graph.infrastructure.play_state_store import (
    PLAY_STATE_ROOT_FIELDS,
    dice_term_object_fields,
    play_event_object_fields,
    play_state_data,
    play_state_from_data,
)

_SCHEMA_PATHS = {
    name: PROJECT_ROOT / "schemas" / name
    for name in (
        "adventure.schema.json",
        "play-state.schema.json",
        "journal-archive.schema.json",
        "workspace-settings.schema.json",
    )
}
_SCHEMAS: dict[str, JsonObject] = {
    name: cast(JsonObject, json.loads(path.read_text(encoding="utf-8")))
    for name, path in _SCHEMA_PATHS.items()
}
_EVENT_SCHEMA_DEFS: dict[PlayEventKind, str] = {
    "session_started": "sessionStarted",
    "session_ended": "sessionEnded",
    "encounter_visited": "encounterVisited",
    "clue_spotted": "clueSpotted",
    "clue_missed": "clueMissed",
    "revelation_established": "revelationEstablished",
    "revelation_foreclosed": "revelationForeclosed",
    "revelation_reopened": "revelationReopened",
    "dice_roll_recorded": "diceRollRecorded",
    "encounter_unlocked": "encounterUnlocked",
    "visit_note_recorded": "visitNoteRecorded",
    "reference_note_recorded": "referenceNoteRecorded",
    "encounter_consequence_recorded": "encounterConsequenceRecorded",
    "operation_voided": "operationVoided",
}


def _representative_events() -> tuple[PlayEvent, ...]:
    return (
        SessionStartedEvent(
            sequence=1,
            session_number=1,
            operation_number=1,
            title="Opening",
            played_on="2026-07-24",
            participants=("Ari", "Bryn"),
            attendance_note="All present",
            opening_note="At the gate",
        ),
        SessionEndedEvent(2, 1, 2, "At rest"),
        EncounterVisitedEvent(3, 1, "alpha", 3, "The Lantern Company"),
        ClueSpottedEvent(4, "clue-a", 1, 4),
        ClueMissedEvent(5, "clue-b", 1, 5),
        RevelationEstablishedEvent(6, "truth", 6, ("clue-a",), "Confirmed"),
        RevelationForeclosedEvent(7, "lost-truth", "The witness departed", 7),
        RevelationReopenedEvent(8, "lost-truth", "The witness returned", 8),
        DiceRollRecordedEvent(
            sequence=9,
            expression="2d6+1",
            terms=(DiceGroupResult(1, 6, (2, 5)), DiceModifierResult(1)),
            total=8,
            operation_number=9,
            label="Search",
        ),
        EncounterUnlockedEvent(10, "vault", 10, "truth", "The seal yields"),
        VisitNoteRecordedEvent(11, 1, "The gate remains watched.", 11),
        ReferenceNoteRecordedEvent(12, "reference-a", "The witness now trusts them.", 12),
        EncounterConsequenceRecordedEvent(13, "alpha", "The ward is broken.", 13),
        PlayOperationVoidedEvent(14, 14, 13, "Recorded against the wrong encounter."),
    )


def _canonical_documents() -> tuple[JsonObject, JsonObject, JsonObject, JsonObject]:
    adventure = complete_four_encounter_adventure()
    state = PlayState(adventure.id, _representative_events())
    archive = JournalArchiveSnapshot(
        archive_id="schema-contract",
        label="Schema contract",
        archived_at="2026-07-24T18:00:00Z",
        source_state_name="play-state.json",
        adventure_snapshot=adventure,
        play_state=state,
    )
    return (
        adventure_data(adventure),
        play_state_data(state),
        journal_archive_data(archive),
        workspace_settings_data(WorkspaceSettings()),
    )


def _properties(node: dict[str, Any]) -> frozenset[str]:
    return frozenset(cast(dict[str, Any], node["properties"]))


def test_adventure_closed_object_boundaries_match_runtime_field_sets() -> None:
    schema = _SCHEMAS["adventure.schema.json"]
    properties = cast(dict[str, Any], schema["properties"])
    definitions = cast(dict[str, Any], schema["$defs"])
    metadata = cast(dict[str, Any], properties["adventure"])
    metadata_properties = cast(dict[str, Any], metadata["properties"])
    tags = cast(dict[str, Any], metadata_properties["tags"])

    nodes = {
        "root": schema,
        "adventure": metadata,
        "tags": tags,
        "optional_positive_range": cast(dict[str, Any], definitions["optional_positive_range"]),
        "validation": cast(dict[str, Any], metadata_properties["validation"]),
        "encounter": cast(dict[str, Any], definitions["encounter"]),
        "reference": cast(dict[str, Any], definitions["reference"]),
        "reference_link": cast(dict[str, Any], definitions["reference_link"]),
        "revelation": cast(dict[str, Any], definitions["revelation"]),
        "clue": cast(dict[str, Any], definitions["clue"]),
    }

    runtime_fields = {
        "root": ADVENTURE_ROOT_FIELDS,
        "adventure": ADVENTURE_METADATA_FIELDS,
        "tags": ADVENTURE_TAG_FIELDS,
        "optional_positive_range": OPTIONAL_POSITIVE_RANGE_FIELDS,
        "validation": VALIDATION_POLICY_FIELDS,
        "encounter": ENCOUNTER_FIELDS,
        "reference": REFERENCE_FIELDS,
        "reference_link": REFERENCE_LINK_FIELDS,
        "revelation": REVELATION_FIELDS,
        "clue": CLUE_FIELDS,
    }
    assert set(nodes) == set(runtime_fields)
    for name, node in nodes.items():
        assert node["additionalProperties"] is False
        assert _properties(node) == frozenset(runtime_fields[name])


def test_play_state_closed_object_boundaries_match_runtime_field_sets() -> None:
    schema = _SCHEMAS["play-state.schema.json"]
    definitions = cast(dict[str, Any], schema["$defs"])

    assert schema["additionalProperties"] is False
    assert _properties(schema) == frozenset(PLAY_STATE_ROOT_FIELDS)
    for event_kind, definition_name in _EVENT_SCHEMA_DEFS.items():
        node = cast(dict[str, Any], definitions[definition_name])
        assert node["additionalProperties"] is False
        assert _properties(node) == frozenset(play_event_object_fields(event_kind))

    dice_nodes = {
        "dice": cast(dict[str, Any], definitions["diceGroupResult"]),
        "modifier": cast(dict[str, Any], definitions["diceModifierResult"]),
    }
    for term_kind, node in dice_nodes.items():
        assert node["additionalProperties"] is False
        assert _properties(node) == frozenset(dice_term_object_fields(term_kind))


def test_archive_and_settings_closed_boundaries_match_runtime_field_sets() -> None:
    archive_schema = _SCHEMAS["journal-archive.schema.json"]
    archive_metadata = cast(
        dict[str, Any], cast(dict[str, Any], archive_schema["properties"])["archive"]
    )
    archive_nodes = {"root": archive_schema, "archive": archive_metadata}
    archive_fields = {
        "root": JOURNAL_ARCHIVE_ROOT_FIELDS,
        "archive": JOURNAL_ARCHIVE_METADATA_FIELDS,
    }
    for name, node in archive_nodes.items():
        assert node["additionalProperties"] is False
        assert _properties(node) == frozenset(archive_fields[name])

    settings_schema = _SCHEMAS["workspace-settings.schema.json"]
    validator_defaults = cast(
        dict[str, Any], cast(dict[str, Any], settings_schema["properties"])["validator_defaults"]
    )
    settings_nodes = {"root": settings_schema, "validator_defaults": validator_defaults}
    settings_fields = {
        "root": WORKSPACE_SETTINGS_ROOT_FIELDS,
        "validator_defaults": WORKSPACE_VALIDATOR_DEFAULT_FIELDS,
    }
    for name, node in settings_nodes.items():
        assert node["additionalProperties"] is False
        assert _properties(node) == frozenset(settings_fields[name])


def test_adventure_decoder_rejects_unknown_fields_at_every_closed_boundary() -> None:
    canonical = adventure_data(reference_library_adventure())
    targets = {
        "root": lambda data: data,
        "adventure": lambda data: cast(JsonObject, data["adventure"]),
        "adventure.tags": lambda data: cast(
            JsonObject, cast(JsonObject, data["adventure"])["tags"]
        ),
        "adventure.tags.party_size": lambda data: cast(
            JsonObject, cast(JsonObject, cast(JsonObject, data["adventure"])["tags"])["party_size"]
        ),
        "adventure.tags.level": lambda data: cast(
            JsonObject, cast(JsonObject, cast(JsonObject, data["adventure"])["tags"])["level"]
        ),
        "adventure.validation": lambda data: cast(
            JsonObject, cast(JsonObject, data["adventure"])["validation"]
        ),
        "references[1]": lambda data: cast(list[JsonObject], data["references"])[0],
        "encounters[1]": lambda data: cast(list[JsonObject], data["encounters"])[0],
        "encounters[1].reference_links[1]": lambda data: cast(
            list[JsonObject],
            cast(list[JsonObject], data["encounters"])[0]["reference_links"],
        )[0],
        "revelations[1]": lambda data: cast(list[JsonObject], data["revelations"])[0],
        "clues[1]": lambda data: cast(list[JsonObject], data["clues"])[0],
    }

    for context, select in targets.items():
        data = deepcopy(canonical)
        select(data)["future_field"] = "must survive"
        with pytest.raises(UnsupportedFieldError) as raised:
            adventure_from_data(data, source="adventure-fixture.json")
        message = str(raised.value)
        assert "adventure-fixture.json" in message
        assert context in message
        assert "'future_field'" in message
        assert "newer Adventure Graph release" in message


def test_adventure_decoder_rejects_zero_in_optional_positive_ranges() -> None:
    for range_name in ("party_size", "level"):
        for endpoint in ("minimum", "maximum"):
            data = adventure_data(complete_four_encounter_adventure())
            tags = cast(JsonObject, cast(JsonObject, data["adventure"])["tags"])
            cast(JsonObject, tags[range_name])[endpoint] = 0

            with pytest.raises(ValueError, match="positive integer or null"):
                adventure_from_data(data, source="adventure-fixture.json")


def test_play_state_decoder_rejects_boolean_signed_dice_integers() -> None:
    canonical = play_state_data(PlayState("contract", _representative_events()))
    events = cast(list[JsonObject], canonical["events"])
    dice_index = next(
        index for index, event in enumerate(events) if event["type"] == "dice_roll_recorded"
    )

    mutations: tuple[tuple[str, Callable[[JsonObject], None]], ...] = (
        ("total", lambda event: event.__setitem__("total", True)),
        (
            "dice sign",
            lambda event: cast(list[JsonObject], event["terms"])[0].__setitem__("sign", True),
        ),
        (
            "modifier value",
            lambda event: cast(list[JsonObject], event["terms"])[1].__setitem__("value", True),
        ),
    )
    for _label, mutate in mutations:
        data = deepcopy(canonical)
        event = cast(list[JsonObject], data["events"])[dice_index]
        mutate(event)
        with pytest.raises(ValueError, match="must be an integer"):
            play_state_from_data(data, source="play-fixture.json")


def test_play_state_decoder_rejects_unknown_fields_at_every_closed_boundary() -> None:
    canonical = play_state_data(PlayState("contract", _representative_events()))

    root_data = deepcopy(canonical)
    root_data["future_field"] = "must survive"
    with pytest.raises(UnsupportedFieldError, match="future_field"):
        play_state_from_data(root_data, source="play-fixture.json")

    events = cast(list[JsonObject], canonical["events"])
    for index, event in enumerate(events, start=1):
        data = deepcopy(canonical)
        mutated_event = cast(list[JsonObject], data["events"])[index - 1]
        mutated_event["future_field"] = "must survive"
        with pytest.raises(UnsupportedFieldError) as raised:
            play_state_from_data(data, source="play-fixture.json")
        message = str(raised.value)
        assert f"events[{index}]" in message
        assert str(event["type"]) in message
        assert "'future_field'" in message

    dice_event_index = next(
        index for index, event in enumerate(events) if event["type"] == "dice_roll_recorded"
    )
    dice_terms = cast(list[JsonObject], events[dice_event_index]["terms"])
    for term_index in range(len(dice_terms)):
        data = deepcopy(canonical)
        event = cast(list[JsonObject], data["events"])[dice_event_index]
        term = cast(list[JsonObject], event["terms"])[term_index]
        term["future_field"] = "must survive"
        with pytest.raises(UnsupportedFieldError) as raised:
            play_state_from_data(data, source="play-fixture.json")
        assert f"terms[{term_index + 1}]" in str(raised.value)


def test_archive_and_settings_decoders_reject_unknown_fields_at_every_boundary() -> None:
    _, _, canonical_archive, canonical_settings = _canonical_documents()

    for context, select in (
        ("root", lambda data: data),
        ("archive", lambda data: cast(JsonObject, data["archive"])),
    ):
        data = deepcopy(canonical_archive)
        select(data)["future_field"] = "must survive"
        with pytest.raises(UnsupportedFieldError) as raised:
            journal_archive_from_data(data, source="archive-fixture.json")
        assert context in str(raised.value)
        assert "archive-fixture.json" in str(raised.value)

    for context, select in (
        ("root", lambda data: data),
        (
            "validator_defaults",
            lambda data: cast(JsonObject, data["validator_defaults"]),
        ),
    ):
        data = deepcopy(canonical_settings)
        select(data)["future_field"] = "must survive"
        with pytest.raises(UnsupportedFieldError) as raised:
            workspace_settings_from_data(data, source="settings-fixture.json")
        assert context in str(raised.value)
        assert "settings-fixture.json" in str(raised.value)


def test_known_omitted_fields_receive_runtime_defaults() -> None:
    sparse_play: JsonObject = {
        "schema_version": 6,
        "adventure_id": "contract",
        "events": [
            {
                "sequence": 1,
                "operation_number": 1,
                "type": "session_started",
                "session_number": 1,
            },
            {
                "sequence": 2,
                "operation_number": 2,
                "type": "session_ended",
                "session_number": 1,
            },
            {
                "sequence": 3,
                "operation_number": 3,
                "type": "encounter_visited",
                "visit_number": 1,
                "encounter_id": "alpha",
            },
            {
                "sequence": 4,
                "operation_number": 4,
                "type": "revelation_established",
                "revelation_id": "truth",
            },
            {
                "sequence": 5,
                "operation_number": 5,
                "type": "dice_roll_recorded",
                "expression": "1d6",
                "terms": [{"kind": "dice", "sign": 1, "faces": 6, "results": [4]}],
                "total": 4,
            },
            {
                "sequence": 6,
                "operation_number": 6,
                "type": "encounter_unlocked",
                "encounter_id": "vault",
            },
        ],
    }
    state = play_state_from_data(sparse_play)
    started = cast(SessionStartedEvent, state.events[0])
    ended = cast(SessionEndedEvent, state.events[1])
    visited = cast(EncounterVisitedEvent, state.events[2])
    established = cast(RevelationEstablishedEvent, state.events[3])
    roll = cast(DiceRollRecordedEvent, state.events[4])
    unlocked = cast(EncounterUnlockedEvent, state.events[5])
    assert (started.title, started.played_on, started.participants) == ("", None, ())
    assert (started.attendance_note, started.opening_note) == ("", "")
    assert ended.closing_note == ""
    assert visited.party_label == ""
    assert (established.supporting_clue_ids, established.note) == ((), "")
    assert roll.label == ""
    assert (unlocked.source_revelation_id, unlocked.reason) == (None, "")

    adventure = complete_four_encounter_adventure()
    state_with_event = PlayState(adventure.id, (EncounterVisitedEvent(1, 1, "alpha", 1),))
    archive = journal_archive_data(
        JournalArchiveSnapshot(
            "sparse-label",
            "",
            "2026-07-24T18:00:00Z",
            "play-state.json",
            adventure,
            state_with_event,
        )
    )
    cast(JsonObject, archive["archive"]).pop("label")
    assert journal_archive_from_data(archive).label == ""

    sparse_settings: JsonObject = {"schema_version": 1}
    assert workspace_settings_from_data(sparse_settings) == WorkspaceSettings()


@pytest.mark.parametrize(
    ("source", "decode"),
    [
        (
            "broken-adventure.json",
            lambda: adventure_from_data(
                {
                    "schema_version": 3,
                    "adventure": {"id": "broken", "title": "Broken", "explanation": []},
                    "encounters": [],
                    "revelations": [],
                    "clues": [],
                },
                source="broken-adventure.json",
            ),
        ),
        (
            "broken-play.json",
            lambda: play_state_from_data(
                {"schema_version": 6, "adventure_id": 4, "events": []},
                source="broken-play.json",
            ),
        ),
        (
            "broken-settings.json",
            lambda: workspace_settings_from_data(
                {"schema_version": 1, "selected_adventure_key": 4},
                source="broken-settings.json",
            ),
        ),
    ],
)
def test_malformed_value_diagnostics_name_their_source(
    source: str,
    decode: Callable[[], object],
) -> None:
    with pytest.raises(ValueError, match="Malformed ") as raised:
        decode()
    message = str(raised.value)
    assert message.startswith("Malformed ")
    assert source in message
    assert not isinstance(raised.value, UnsupportedFieldError)


def test_archive_malformed_value_diagnostic_names_its_source() -> None:
    _, _, archive, _ = _canonical_documents()
    cast(JsonObject, archive["archive"])["event_count"] = "many"

    with pytest.raises(ValueError, match="Malformed journal archive document") as raised:
        journal_archive_from_data(archive, source=Path("broken-archive.json"))

    assert str(raised.value).startswith("Malformed journal archive document")
    assert "broken-archive.json" in str(raised.value)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: cast(JsonObject, data["adventure"]).__setitem__("id", ""),
        lambda data: cast(JsonObject, data["adventure"]).__setitem__("id", "Bad ID"),
        lambda data: cast(JsonObject, data["adventure"]).__setitem__("title", ""),
        lambda data: cast(list[JsonObject], data["encounters"])[0].__setitem__("id", "UPPER"),
        lambda data: cast(list[JsonObject], data["encounters"])[0].__setitem__("title", ""),
        lambda data: cast(list[JsonObject], data["revelations"])[0].__setitem__("id", "x_y"),
        lambda data: cast(list[JsonObject], data["revelations"])[0].__setitem__("title", ""),
        lambda data: cast(list[JsonObject], data["revelations"])[0].__setitem__(
            "unlocks_encounter_id", "Bad ID"
        ),
        lambda data: cast(list[JsonObject], data["clues"])[0].__setitem__("id", ""),
        lambda data: cast(list[JsonObject], data["clues"])[0].__setitem__("title", ""),
        lambda data: cast(list[JsonObject], data["clues"])[0].__setitem__(
            "source_encounter_id", "Bad ID"
        ),
        lambda data: cast(list[JsonObject], data["clues"])[0].__setitem__(
            "revelation_id", "Bad ID"
        ),
    ],
)
def test_adventure_decoder_rejects_published_identifier_and_required_text_violations(
    mutate: Callable[[JsonObject], object],
) -> None:
    canonical, _, _, _ = _canonical_documents()
    mutate(canonical)

    with pytest.raises(ValueError, match="Malformed adventure document"):
        adventure_from_data(canonical, source="invalid-values.adventure.json")


def test_adventure_writer_refuses_schema_invalid_domain_values() -> None:
    adventure = complete_four_encounter_adventure()

    with pytest.raises(ValueError, match=r"adventure\.id"):
        adventure_data(replace(adventure, id="Bad ID"))
    with pytest.raises(ValueError, match=r"encounters\[1\]\.title"):
        adventure_data(
            replace(
                adventure,
                encounters=(replace(adventure.encounters[0], title=""), *adventure.encounters[1:]),
            )
        )


@pytest.mark.parametrize(
    ("event_index", "field", "value"),
    [
        (0, "played_on", "2026-02-30"),
        (0, "participants", [""]),
        (0, "participants", ["Ari", "Ari"]),
        (2, "encounter_id", ""),
        (3, "clue_id", ""),
        (5, "revelation_id", ""),
        (5, "supporting_clue_ids", [""]),
        (5, "supporting_clue_ids", ["clue-a", "clue-a"]),
        (6, "reason", ""),
        (7, "reason", ""),
        (8, "expression", ""),
        (8, "terms", []),
        (9, "encounter_id", ""),
        (9, "source_revelation_id", ""),
        (10, "text", ""),
        (11, "reference_id", ""),
        (11, "text", ""),
        (12, "text", ""),
        (13, "reason", ""),
    ],
)
def test_play_decoder_rejects_published_value_constraint_violations(
    event_index: int,
    field: str,
    value: object,
) -> None:
    _, canonical, _, _ = _canonical_documents()
    cast(list[JsonObject], canonical["events"])[event_index][field] = value

    with pytest.raises(ValueError, match="Malformed play-state document"):
        play_state_from_data(canonical, source="invalid-values.play-state.json")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("faces", 1),
        ("results", []),
        ("results", [7]),
    ],
)
def test_play_decoder_rejects_impossible_or_schema_invalid_dice_groups(
    field: str,
    value: object,
) -> None:
    _, canonical, _, _ = _canonical_documents()
    roll = cast(list[JsonObject], canonical["events"])[8]
    cast(list[JsonObject], roll["terms"])[0][field] = value

    with pytest.raises(ValueError, match="Malformed play-state document"):
        play_state_from_data(canonical, source="invalid-dice.play-state.json")


def test_play_decoder_and_writer_reject_a_dice_total_disagreeing_with_terms() -> None:
    _, canonical, _, _ = _canonical_documents()
    cast(list[JsonObject], canonical["events"])[8]["total"] = 999

    with pytest.raises(ValueError, match="total must equal"):
        play_state_from_data(canonical)

    events = list(_representative_events())
    roll = cast(DiceRollRecordedEvent, events[8])
    events[8] = DiceRollRecordedEvent(
        roll.sequence,
        roll.expression,
        roll.terms,
        999,
        roll.operation_number,
        roll.label,
    )
    with pytest.raises(ValueError, match="total must equal"):
        play_state_data(PlayState("contract", tuple(events)))


def test_play_writer_refuses_schema_invalid_identifiers_dates_and_required_text() -> None:
    events = list(_representative_events())
    started = cast(SessionStartedEvent, events[0])
    events[0] = SessionStartedEvent(
        started.sequence,
        started.session_number,
        started.operation_number,
        started.title,
        "2026-02-30",
        started.participants,
        started.attendance_note,
        started.opening_note,
    )
    with pytest.raises(ValueError, match="played_on"):
        play_state_data(PlayState("contract", tuple(events)))

    invalid_reason_events = list(_representative_events())
    foreclosed = cast(RevelationForeclosedEvent, invalid_reason_events[6])
    invalid_reason_events[6] = replace(foreclosed, reason="")
    with pytest.raises(ValueError, match="reason"):
        play_state_data(PlayState("contract", tuple(invalid_reason_events)))

    duplicate_participant_events = list(_representative_events())
    started = cast(SessionStartedEvent, duplicate_participant_events[0])
    duplicate_participant_events[0] = replace(started, participants=("Ari", "Ari"))
    with pytest.raises(ValueError, match="participants"):
        play_state_data(PlayState("contract", tuple(duplicate_participant_events)))

    with pytest.raises(ValueError, match="adventure_id"):
        play_state_data(PlayState("", ()))


def test_archive_decoder_and_writer_reject_invalid_metadata_values() -> None:
    _, _, canonical, _ = _canonical_documents()

    for field, value in (
        ("archived_at", "not-a-date"),
        ("source_state_name", ""),
    ):
        data = deepcopy(canonical)
        cast(JsonObject, data["archive"])[field] = value
        with pytest.raises(ValueError, match="Malformed journal archive document"):
            journal_archive_from_data(data, source="invalid-values.journal.json")

    archive = JournalArchiveSnapshot(
        archive_id="invalid-metadata",
        label="",
        archived_at="not-a-date",
        source_state_name="play-state.json",
        adventure_snapshot=complete_four_encounter_adventure(),
        play_state=PlayState("contract", _representative_events()),
    )
    with pytest.raises(ValueError, match="archived_at"):
        journal_archive_data(archive)
