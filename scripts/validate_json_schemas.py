"""Validate canonical and compatibility-sparse JSON against published schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from adventure_graph.application.archive_management import JournalArchiveSnapshot
from adventure_graph.application.workspace_management import WorkspaceSettings
from adventure_graph.domain.play_events import EncounterVisitedEvent
from adventure_graph.domain.play_state import PlayState
from adventure_graph.infrastructure.adventure_store import adventure_data, load_adventure
from adventure_graph.infrastructure.journal_archive_store import journal_archive_data
from adventure_graph.infrastructure.local_adventure_workspace import workspace_settings_data
from adventure_graph.infrastructure.play_state_store import play_state_data

PROJECT_ROOT = Path(__file__).resolve().parents[1]
JsonObject = dict[str, Any]

SCHEMA_DIRECTORY = PROJECT_ROOT / "schemas"


def _schemas() -> tuple[dict[str, JsonObject], Registry[Any]]:
    schemas = {
        path.name: cast(JsonObject, json.loads(path.read_text(encoding="utf-8")))
        for path in SCHEMA_DIRECTORY.glob("*.json")
    }
    registry: Registry[Any] = Registry().with_resources(
        (cast(str, schema["$id"]), Resource.from_contents(schema))
        for schema in schemas.values()
    )
    return schemas, registry


def _repository_documents() -> list[tuple[str, str, JsonObject]]:
    documents: list[tuple[str, str, JsonObject]] = []
    adventure_paths = [
        *sorted((PROJECT_ROOT / "examples").rglob("adventure.json")),
        PROJECT_ROOT / "examples" / "the-glass-saint.adventure.json",
        PROJECT_ROOT
        / "src"
        / "adventure_graph"
        / "resources"
        / "the-glass-saint.adventure.json",
    ]
    play_paths = sorted((PROJECT_ROOT / "examples").rglob("play-state*.json"))
    archive_paths = sorted((PROJECT_ROOT / "examples").rglob("*.journal.json"))
    for schema_name, paths in (
        ("adventure.schema.json", adventure_paths),
        ("play-state.schema.json", play_paths),
        ("journal-archive.schema.json", archive_paths),
    ):
        documents.extend(
            (
                schema_name,
                path.relative_to(PROJECT_ROOT).as_posix(),
                cast(JsonObject, json.loads(path.read_text(encoding="utf-8"))),
            )
            for path in paths
        )
    return documents


def _compatibility_documents() -> list[tuple[str, str, JsonObject]]:
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
    sparse_settings: JsonObject = {"schema_version": 1}

    adventure_path = (
        PROJECT_ROOT / "src" / "adventure_graph" / "resources" / "the-glass-saint.adventure.json"
    )
    adventure = load_adventure(adventure_path)
    state = PlayState(
        adventure.id,
        (EncounterVisitedEvent(1, 1, adventure.encounters[0].id, 1),),
    )
    archive = journal_archive_data(
        JournalArchiveSnapshot(
            archive_id="schema-defaults",
            label="",
            archived_at="2026-07-24T18:00:00Z",
            source_state_name="play-state.json",
            adventure_snapshot=adventure,
            play_state=state,
        )
    )
    cast(JsonObject, archive["archive"]).pop("label")

    return [
        ("adventure.schema.json", "runtime canonical adventure", adventure_data(adventure)),
        ("play-state.schema.json", "runtime canonical play state", play_state_data(state)),
        ("journal-archive.schema.json", "runtime sparse archive", archive),
        (
            "workspace-settings.schema.json",
            "runtime canonical workspace settings",
            workspace_settings_data(WorkspaceSettings()),
        ),
        ("play-state.schema.json", "runtime sparse play defaults", sparse_play),
        ("workspace-settings.schema.json", "runtime sparse workspace defaults", sparse_settings),
    ]


def main() -> int:
    """Validate every selected document and print a compact success count."""
    schemas, registry = _schemas()
    documents = [*_repository_documents(), *_compatibility_documents()]
    for schema_name, source, data in documents:
        try:
            Draft202012Validator(
                schemas[schema_name],
                registry=registry,
                format_checker=FormatChecker(),
            ).validate(data)
        except Exception as error:
            raise SystemExit(f"{source} violates {schema_name}: {error}") from error
    print(f"Validated {len(documents)} JSON documents against the published schemas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
