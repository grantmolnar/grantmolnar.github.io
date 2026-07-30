"""JSON persistence for authored adventure definitions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

from adventure_graph.domain.adventure import (
    Adventure,
    AdventureTags,
    Clue,
    CombatIntensity,
    Encounter,
    Reference,
    ReferenceKind,
    ReferenceLink,
    Revelation,
)
from adventure_graph.domain.validation_models import ValidationPolicy
from adventure_graph.infrastructure.atomic_files import write_json_object
from adventure_graph.infrastructure.json_values import (
    JsonObject,
    UnsupportedFieldError,
    boolean_value,
    integer_value,
    nonempty_string_value,
    nullable_string,
    object_list,
    object_value,
    read_object,
    reject_unknown_fields,
    string_list,
    string_value,
    unique_nonempty_string_list,
)

ADVENTURE_SCHEMA_VERSION = 3
_ADVENTURE_IDENTIFIER_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"

ADVENTURE_ROOT_FIELDS = (
    "schema_version",
    "adventure",
    "references",
    "encounters",
    "revelations",
    "clues",
)
ADVENTURE_METADATA_FIELDS = (
    "id",
    "title",
    "synopsis",
    "premise",
    "explanation",
    "tags",
    "validation",
)
ADVENTURE_TAG_FIELDS = (
    "genres",
    "game_systems",
    "settings",
    "party_size",
    "level",
    "combat_intensity",
    "keywords",
)
OPTIONAL_POSITIVE_RANGE_FIELDS = ("minimum", "maximum")
VALIDATION_POLICY_FIELDS = (
    "minimum_clues_per_revelation",
    "minimum_source_encounters_per_revelation",
    "minimum_incoming_clues_per_encounter",
    "minimum_incoming_source_encounters_per_encounter",
    "minimum_outgoing_clues_per_encounter",
    "minimum_distinct_encounter_targets_per_encounter",
    "minimum_edge_connectivity",
    "require_directed_reachability",
)
ENCOUNTER_FIELDS = (
    "id",
    "title",
    "summary",
    "opening_view",
    "content",
    "required",
    "start",
    "end",
    "tags",
    "reference_links",
)
REFERENCE_FIELDS = ("id", "kind", "title", "aliases", "summary", "content", "tags")
REFERENCE_LINK_FIELDS = ("reference_id", "context")
REVELATION_FIELDS = ("id", "title", "description", "unlocks_encounter_id", "required")
CLUE_FIELDS = (
    "id",
    "title",
    "source_encounter_id",
    "revelation_id",
    "description",
    "discovery",
)


def load_adventure(path: Path) -> Adventure:
    """Load an adventure from its versioned JSON source document."""
    return adventure_from_data(read_object(path), source=path)


def adventure_from_data(
    data: JsonObject,
    *,
    source: str | Path = "adventure document",
) -> Adventure:
    """Decode one canonical adventure JSON object."""
    if data.get("schema_version") != ADVENTURE_SCHEMA_VERSION:
        raise ValueError(
            f"Only adventure schema_version {ADVENTURE_SCHEMA_VERSION} is supported in {source}."
        )
    try:
        return _adventure_from_current_schema(data, source)
    except UnsupportedFieldError:
        raise
    except ValueError as error:
        raise ValueError(f"Malformed adventure document in {source}: {error}") from error


def _adventure_from_current_schema(data: JsonObject, source: str | Path) -> Adventure:
    reject_unknown_fields(data, ADVENTURE_ROOT_FIELDS, f"{source} root")
    metadata = object_value(data, "adventure")
    reject_unknown_fields(metadata, ADVENTURE_METADATA_FIELDS, f"{source} adventure")
    policy_data = _optional_object(metadata, "validation")
    reject_unknown_fields(policy_data, VALIDATION_POLICY_FIELDS, f"{source} adventure.validation")
    policy = ValidationPolicy(
        minimum_clues_per_revelation=integer_value(policy_data, "minimum_clues_per_revelation", 3),
        minimum_source_encounters_per_revelation=integer_value(
            policy_data, "minimum_source_encounters_per_revelation", 3
        ),
        minimum_incoming_clues_per_encounter=integer_value(
            policy_data, "minimum_incoming_clues_per_encounter", 3
        ),
        minimum_incoming_source_encounters_per_encounter=integer_value(
            policy_data, "minimum_incoming_source_encounters_per_encounter", 3
        ),
        minimum_outgoing_clues_per_encounter=integer_value(
            policy_data, "minimum_outgoing_clues_per_encounter", 3
        ),
        minimum_distinct_encounter_targets_per_encounter=integer_value(
            policy_data, "minimum_distinct_encounter_targets_per_encounter", 3
        ),
        minimum_edge_connectivity=integer_value(policy_data, "minimum_edge_connectivity", 3),
        require_directed_reachability=boolean_value(
            policy_data, "require_directed_reachability", True
        ),
    )
    tags_data = _optional_object(metadata, "tags")
    reject_unknown_fields(tags_data, ADVENTURE_TAG_FIELDS, f"{source} adventure.tags")
    party_size_data = _optional_object(tags_data, "party_size")
    reject_unknown_fields(
        party_size_data,
        OPTIONAL_POSITIVE_RANGE_FIELDS,
        f"{source} adventure.tags.party_size",
    )
    level_data = _optional_object(tags_data, "level")
    reject_unknown_fields(
        level_data,
        OPTIONAL_POSITIVE_RANGE_FIELDS,
        f"{source} adventure.tags.level",
    )
    combat_intensity = tags_data.get("combat_intensity")
    if combat_intensity is not None and not isinstance(combat_intensity, str):
        raise ValueError("combat_intensity must be a string or null.")
    tags = AdventureTags(
        genres=tuple(unique_nonempty_string_list(tags_data, "genres", [])),
        game_systems=tuple(unique_nonempty_string_list(tags_data, "game_systems", [])),
        settings=tuple(unique_nonempty_string_list(tags_data, "settings", [])),
        party_size_min=_nullable_positive_integer(party_size_data, "minimum"),
        party_size_max=_nullable_positive_integer(party_size_data, "maximum"),
        level_min=_nullable_positive_integer(level_data, "minimum"),
        level_max=_nullable_positive_integer(level_data, "maximum"),
        combat_intensity=cast(CombatIntensity | None, combat_intensity),
        keywords=tuple(unique_nonempty_string_list(tags_data, "keywords", [])),
    )
    return Adventure(
        id=_identifier_value(metadata, "id"),
        title=nonempty_string_value(metadata, "title"),
        synopsis=string_value(metadata, "synopsis", ""),
        premise=string_value(metadata, "premise", ""),
        explanation=string_value(metadata, "explanation", ""),
        references=tuple(
            _reference(item, source, index)
            for index, item in enumerate(_optional_object_list(data, "references"), start=1)
        ),
        encounters=tuple(
            _encounter(item, source, index)
            for index, item in enumerate(object_list(data, "encounters"), start=1)
        ),
        revelations=tuple(
            _revelation(item, source, index)
            for index, item in enumerate(object_list(data, "revelations"), start=1)
        ),
        clues=tuple(
            _clue(item, source, index)
            for index, item in enumerate(object_list(data, "clues"), start=1)
        ),
        tags=tags,
        validation_policy=policy,
    )


def save_adventure(path: Path, adventure: Adventure) -> None:
    """Persist an adventure in the canonical JSON representation."""
    write_json_object(path, adventure_data(adventure))


def adventure_data(adventure: Adventure) -> JsonObject:
    """Return the canonical JSON object for an adventure."""
    _validate_persisted_adventure_values(adventure)
    policy = adventure.validation_policy
    return {
        "schema_version": ADVENTURE_SCHEMA_VERSION,
        "adventure": {
            "id": adventure.id,
            "title": adventure.title,
            "synopsis": adventure.synopsis,
            "premise": adventure.premise,
            "explanation": adventure.explanation,
            "tags": {
                "genres": list(adventure.tags.genres),
                "game_systems": list(adventure.tags.game_systems),
                "settings": list(adventure.tags.settings),
                "party_size": {
                    "minimum": adventure.tags.party_size_min,
                    "maximum": adventure.tags.party_size_max,
                },
                "level": {
                    "minimum": adventure.tags.level_min,
                    "maximum": adventure.tags.level_max,
                },
                "combat_intensity": adventure.tags.combat_intensity,
                "keywords": list(adventure.tags.keywords),
            },
            "validation": {
                "minimum_clues_per_revelation": policy.minimum_clues_per_revelation,
                "minimum_source_encounters_per_revelation": (
                    policy.minimum_source_encounters_per_revelation
                ),
                "minimum_incoming_clues_per_encounter": policy.minimum_incoming_clues_per_encounter,
                "minimum_incoming_source_encounters_per_encounter": (
                    policy.minimum_incoming_source_encounters_per_encounter
                ),
                "minimum_outgoing_clues_per_encounter": policy.minimum_outgoing_clues_per_encounter,
                "minimum_distinct_encounter_targets_per_encounter": (
                    policy.minimum_distinct_encounter_targets_per_encounter
                ),
                "minimum_edge_connectivity": policy.minimum_edge_connectivity,
                "require_directed_reachability": policy.require_directed_reachability,
            },
        },
        "references": [
            {
                "id": reference.id,
                "kind": reference.kind,
                "title": reference.title,
                "aliases": list(reference.aliases),
                "summary": reference.summary,
                "content": reference.content,
                "tags": list(reference.tags),
            }
            for reference in adventure.references
        ],
        "encounters": [
            {
                "id": encounter.id,
                "title": encounter.title,
                "summary": encounter.summary,
                "opening_view": encounter.opening_view,
                "content": encounter.content,
                "required": encounter.required,
                "start": encounter.start,
                "end": encounter.end,
                "tags": list(encounter.tags),
                "reference_links": [
                    {
                        "reference_id": link.reference_id,
                        "context": link.context,
                    }
                    for link in encounter.reference_links
                ],
            }
            for encounter in adventure.encounters
        ],
        "revelations": [
            {
                "id": revelation.id,
                "title": revelation.title,
                "description": revelation.description,
                "unlocks_encounter_id": revelation.unlocks_encounter_id,
                "required": revelation.required,
            }
            for revelation in adventure.revelations
        ],
        "clues": [
            {
                "id": clue.id,
                "title": clue.title,
                "source_encounter_id": clue.source_encounter_id,
                "revelation_id": clue.revelation_id,
                "description": clue.description,
                "discovery": clue.discovery,
            }
            for clue in adventure.clues
        ],
    }


def _optional_object(data: JsonObject, key: str) -> JsonObject:
    value = data.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object.")
    return cast(JsonObject, value)


def _optional_object_list(data: JsonObject, key: str) -> list[JsonObject]:
    value = data.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list of objects.")
    objects: list[JsonObject] = []
    for item in cast(list[object], value):
        if not isinstance(item, dict):
            raise ValueError(f"{key} must be a list of objects.")
        objects.append(cast(JsonObject, item))
    return objects


def _nullable_positive_integer(data: dict[str, Any], key: str) -> int | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{key} must be a positive integer or null.")
    return value


def _encounter(data: JsonObject, source: str | Path, index: int) -> Encounter:
    reject_unknown_fields(data, ENCOUNTER_FIELDS, f"{source} encounters[{index}]")
    return Encounter(
        id=_identifier_value(data, "id"),
        title=nonempty_string_value(data, "title"),
        summary=string_value(data, "summary", ""),
        opening_view=string_value(data, "opening_view", ""),
        content=string_value(data, "content", ""),
        required=boolean_value(data, "required", True),
        start=boolean_value(data, "start", False),
        end=boolean_value(data, "end", False),
        tags=tuple(string_list(data, "tags", [])),
        reference_links=tuple(
            _reference_link(item, source, index, link_index)
            for link_index, item in enumerate(
                _optional_object_list(data, "reference_links"), start=1
            )
        ),
    )


def _reference(data: JsonObject, source: str | Path, index: int) -> Reference:
    reject_unknown_fields(data, REFERENCE_FIELDS, f"{source} references[{index}]")
    kind = string_value(data, "kind")
    return Reference(
        id=string_value(data, "id"),
        kind=cast(ReferenceKind, kind),
        title=string_value(data, "title"),
        aliases=tuple(string_list(data, "aliases", [])),
        summary=string_value(data, "summary", ""),
        content=string_value(data, "content", ""),
        tags=tuple(string_list(data, "tags", [])),
    )


def _reference_link(
    data: JsonObject, source: str | Path, encounter_index: int, link_index: int
) -> ReferenceLink:
    reject_unknown_fields(
        data,
        REFERENCE_LINK_FIELDS,
        f"{source} encounters[{encounter_index}].reference_links[{link_index}]",
    )
    return ReferenceLink(
        reference_id=string_value(data, "reference_id"),
        context=string_value(data, "context", ""),
    )


def _revelation(data: JsonObject, source: str | Path, index: int) -> Revelation:
    reject_unknown_fields(data, REVELATION_FIELDS, f"{source} revelations[{index}]")
    return Revelation(
        id=_identifier_value(data, "id"),
        title=nonempty_string_value(data, "title"),
        description=string_value(data, "description", ""),
        unlocks_encounter_id=_nullable_identifier_value(data, "unlocks_encounter_id"),
        required=boolean_value(data, "required", True),
    )


def _clue(data: JsonObject, source: str | Path, index: int) -> Clue:
    reject_unknown_fields(data, CLUE_FIELDS, f"{source} clues[{index}]")
    return Clue(
        id=_identifier_value(data, "id"),
        title=nonempty_string_value(data, "title"),
        source_encounter_id=_identifier_value(data, "source_encounter_id"),
        revelation_id=_identifier_value(data, "revelation_id"),
        description=string_value(data, "description", ""),
        discovery=string_value(data, "discovery", "search"),
    )


def _identifier_value(data: JsonObject, key: str) -> str:
    value = nonempty_string_value(data, key)
    _require_identifier(value, key)
    return value


def _nullable_identifier_value(data: JsonObject, key: str) -> str | None:
    value = nullable_string(data, key)
    if value is not None:
        _require_identifier(value, key)
    return value


def _require_identifier(value: str, label: str) -> None:
    if re.fullmatch(_ADVENTURE_IDENTIFIER_PATTERN, value) is None:
        raise ValueError(
            f"{label} must contain lowercase letters or digits separated by single hyphens."
        )


def _require_nonempty(value: str, label: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{label} must be a nonempty string.")


def _validate_persisted_adventure_values(adventure: Adventure) -> None:
    _require_identifier(adventure.id, "adventure.id")
    _require_nonempty(adventure.title, "adventure.title")
    for index, reference in enumerate(adventure.references, start=1):
        try:
            Reference(
                id=reference.id,
                kind=reference.kind,
                title=reference.title,
                aliases=reference.aliases,
                summary=reference.summary,
                content=reference.content,
                tags=reference.tags,
            )
        except ValueError as error:
            raise ValueError(f"references[{index}] is malformed: {error}") from error
    for index, encounter in enumerate(adventure.encounters, start=1):
        _require_identifier(encounter.id, f"encounters[{index}].id")
        _require_nonempty(encounter.title, f"encounters[{index}].title")
        for link_index, link in enumerate(encounter.reference_links, start=1):
            try:
                ReferenceLink(reference_id=link.reference_id, context=link.context)
            except ValueError as error:
                raise ValueError(
                    f"encounters[{index}].reference_links[{link_index}] is malformed: {error}"
                ) from error
    for index, revelation in enumerate(adventure.revelations, start=1):
        _require_identifier(revelation.id, f"revelations[{index}].id")
        _require_nonempty(revelation.title, f"revelations[{index}].title")
        if revelation.unlocks_encounter_id is not None:
            _require_identifier(
                revelation.unlocks_encounter_id,
                f"revelations[{index}].unlocks_encounter_id",
            )
    for index, clue in enumerate(adventure.clues, start=1):
        _require_identifier(clue.id, f"clues[{index}].id")
        _require_nonempty(clue.title, f"clues[{index}].title")
        _require_identifier(clue.source_encounter_id, f"clues[{index}].source_encounter_id")
        _require_identifier(clue.revelation_id, f"clues[{index}].revelation_id")
