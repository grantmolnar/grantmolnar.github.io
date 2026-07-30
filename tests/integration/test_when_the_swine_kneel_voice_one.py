"""Regression checks for the When the Swine Kneel Voice I pass."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.journal_archive_store import load_journal_archive
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.integration.swine_support import assert_historical_archive_structure
from tests.support.corpus_contracts import assert_rendered_documents_match

pytestmark = pytest.mark.corpus

EXAMPLE = Path("examples/when-the-swine-kneel")
SOURCE = EXAMPLE / "adventure.json"
STATE = EXAMPLE / "play-state.example.json"
ARCHIVE = EXAMPLE / "archives" / "synthetic-complete-playthrough.journal.json"


def _word_counts() -> dict[str, int]:
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    counts = {
        "overview": sum(
            len(raw["adventure"][key].split()) for key in ("synopsis", "premise", "explanation")
        ),
        "summaries": sum(len(encounter["summary"].split()) for encounter in raw["encounters"]),
        "openings": sum(len(encounter["opening_view"].split()) for encounter in raw["encounters"]),
        "bodies": sum(len(encounter["content"].split()) for encounter in raw["encounters"]),
        "revelations": sum(
            len(revelation["description"].split()) for revelation in raw["revelations"]
        ),
        "clues": sum(len(clue["description"].split()) for clue in raw["clues"]),
    }
    counts["total"] = sum(counts.values())
    return counts


def test_swine_voice_one_has_distinct_source_registers() -> None:
    """Keep the revised layers specific to their institutions and materials."""
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    revised = [raw["adventure"][key] for key in ("synopsis", "premise", "explanation")]
    revised.extend(encounter["summary"] for encounter in raw["encounters"])
    revised.extend(encounter["content"] for encounter in raw["encounters"])
    combined = "\n".join(revised)

    for generic in ("party", "adventurer", "players", "player agency"):
        assert re.search(rf"\b{re.escape(generic)}\b", combined, re.IGNORECASE) is None
    for demonstrator in (
        "Ashlar Company",
        "Mara Venn",
        "Nell Harth",
        "Orris Cale",
        "Sera Dain",
    ):
        assert demonstrator not in combined

    encounter_index = {encounter["id"]: encounter for encounter in raw["encounters"]}
    expected_registers = {
        "the-hall-of-petitions": "official life",
        "southgate-stockyards": "thirsty pigs",
        "the-college-of-civic-measure": "certify the buried pulse",
        "rillcross-farm-belt": "one buried map",
        "the-chapel-of-the-first-survey": "dead that Veyr wants to use",
        "the-nine-mile-pump-house": "whose danger counts",
        "the-deep-bell": "living herds before officials can hide",
    }
    for encounter_id, phrase in expected_registers.items():
        assert phrase in encounter_index[encounter_id]["summary"]

    assert _word_counts() == {
        "overview": 538,
        "summaries": 122,
        "openings": 546,
        "bodies": 5592,
        "revelations": 191,
        "clues": 1046,
        "total": 8035,
    }


def test_swine_voice_one_preserves_graph_and_demonstrated_play() -> None:
    """Keep the source-only voice pass from altering structure or runtime state."""
    adventure = load_adventure(SOURCE)
    state = load_play_state(STATE)
    archive = load_journal_archive(ARCHIVE)
    projection = project_play_state(adventure, state)
    report = validate_adventure(adventure)
    archive_raw = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    source_raw = json.loads(SOURCE.read_text(encoding="utf-8"))

    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(adventure.encounters) == 7
    assert len(adventure.revelations) == 10
    assert len(adventure.clues) == 38
    assert len(state.events) == 96
    assert len(archive.play_state.events) == 74
    assert len(projection.spotted_clue_ids) == 25
    assert len(set(adventure.clue_index()) - set(projection.spotted_clue_ids)) == 13
    assert_historical_archive_structure(archive_raw["adventure_snapshot"], source_raw)
    assert archive_raw["archive"]["event_count"] == 74


def test_swine_voice_one_records_the_voice_two_handoff() -> None:
    """Keep the audit, README, roadmap, and generated packet synchronized."""


    adventure = load_adventure(SOURCE)
    state = load_play_state(STATE)
    documents = render_adventure_documents(
        adventure,
        validate_adventure(adventure),
        state,
    )
    assert len(documents) == 35
    assert_rendered_documents_match(
        documents, EXAMPLE / "generated"
    )
