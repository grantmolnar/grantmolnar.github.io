"""Shared historical-snapshot helpers for the Swine corpus tests."""

from __future__ import annotations

from copy import deepcopy

VOICE_III_ENCOUNTER_IDS = (
    "the-hall-of-petitions",
    "southgate-stockyards",
    "the-college-of-civic-measure",
    "rillcross-farm-belt",
    "the-chapel-of-the-first-survey",
    "the-nine-mile-pump-house",
    "the-deep-bell",
)

_CURRENT_TO_HISTORICAL_TITLES = {
    "The Hall of Condemnations": "The Hall of Petitions",
}


def _restore_historical_titles(value: object) -> object:
    """Project accepted title-only deconflictions back to archive wording."""
    if isinstance(value, str):
        restored = value
        for current, historical in _CURRENT_TO_HISTORICAL_TITLES.items():
            restored = restored.replace(current, historical)
        return restored
    if isinstance(value, list):
        return [_restore_historical_titles(item) for item in value]
    if isinstance(value, dict):
        return {key: _restore_historical_titles(item) for key, item in value.items()}
    return value


def without_references(raw: dict[str, object]) -> dict[str, object]:
    """Project current authored data back to its reference-free source shape."""
    projected = deepcopy(raw)
    projected.pop("references", None)
    encounters = projected.get("encounters", [])
    assert isinstance(encounters, list)
    for encounter in encounters:
        assert isinstance(encounter, dict)
        encounter.pop("reference_links", None)
    return projected


def assert_historical_archive_structure(
    snapshot: dict[str, object],
    current: dict[str, object],
) -> None:
    """Keep the immutable archive aligned outside the seven Voice III bodies."""
    projected_raw = without_references(current)
    projected = _restore_historical_titles(projected_raw)
    assert isinstance(projected, dict)
    historical = deepcopy(snapshot)

    historical_encounters = historical.pop("encounters")
    current_encounters = projected.pop("encounters")
    assert historical == projected
    assert isinstance(historical_encounters, list)
    assert isinstance(current_encounters, list)
    assert len(historical_encounters) == len(current_encounters)

    changed_ids: list[str] = []
    for historical_encounter, current_encounter in zip(
        historical_encounters,
        current_encounters,
        strict=True,
    ):
        assert isinstance(historical_encounter, dict)
        assert isinstance(current_encounter, dict)
        historical_content = historical_encounter.pop("content")
        current_content = current_encounter.pop("content")
        assert historical_encounter == current_encounter
        if historical_content != current_content:
            encounter_id = current_encounter.get("id")
            assert isinstance(encounter_id, str)
            changed_ids.append(encounter_id)

    assert tuple(changed_ids) == VOICE_III_ENCOUNTER_IDS
