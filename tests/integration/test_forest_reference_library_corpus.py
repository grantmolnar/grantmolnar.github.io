"""Forest reference-library completion and preservation evidence."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlencode

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.journal_archive_store import load_journal_archive
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.integration.forest_support import assert_historical_archive_structure
from tests.support.web import build_authoring_app, build_play_app, request_wsgi

pytestmark = pytest.mark.corpus

FOREST_ROOT = Path("examples/the-forest-that-carries-dawn")
ORRA_ID = "66e19be9-14c6-41e3-833f-2c532fe37337"
HESSA_ID = "4f85895f-92d6-4386-98ee-0228b34b72b9"
NAHL_ID = "266c943b-9aa9-4cd1-aed2-12be6b9e2cb9"
PELEN_ID = "8b50ba07-c72a-4f4e-b256-262ddb032f89"
SIO_ID = "14d29a1c-1c91-4787-bfc0-f39c7dfcb204"
JUN_ID = "05574ea0-6d5a-4187-ab70-91a2d2cb7836"
MEREWASH_ID = "5a740217-a92f-4222-a49d-d8b2ce5251d3"
SALT_AND_GLASS_ID = "891a38f1-e18c-4cb3-b178-7a2b583b4491"
BEARER_ID = "a5e45f21-b17d-4663-a069-0f340cc6851b"

FOREST_REFERENCE_IDS = (
    ORRA_ID,
    HESSA_ID,
    NAHL_ID,
    PELEN_ID,
    SIO_ID,
    JUN_ID,
    MEREWASH_ID,
    SALT_AND_GLASS_ID,
    BEARER_ID,
)
FOREST_REFERENCE_LINK_COUNTS = {
    ORRA_ID: 4,
    HESSA_ID: 4,
    NAHL_ID: 8,
    PELEN_ID: 5,
    SIO_ID: 3,
    JUN_ID: 6,
    MEREWASH_ID: 4,
    SALT_AND_GLASS_ID: 3,
    BEARER_ID: 5,
}

FOREST_REFERENCE_BODY_HASHES = {
    ORRA_ID: "030c1f9c5b98c732d2399ce13d213031cfa897ef89f2f0555fbb9009e72de907",
    HESSA_ID: "feabb242076f19f6337dd4a72f094c62dceb67f8baef9fbef527cc6ff5998547",
    NAHL_ID: "62bcc5a42d0f85e45e8f6955b2d539964510a659f3001e5f6bcec066148f1337",
    PELEN_ID: "c7cd5ccf1daac0d86a078bb7d387e8fb0fd18e8fe8b8dc030e454d9b2d366ede",
    SIO_ID: "d9eec05691c5984586d648325481f6fb9ddaf6a2507579fe7c6225b976ee0617",
    JUN_ID: "e9c2719d50d132cba86093072cf22655d7b6c070df5da1ec9cf36f14188a088a",
    MEREWASH_ID: "06adc0920746582e6c7d60d374292543309e3efcacfbba7034987b32adfae268",
    SALT_AND_GLASS_ID: "8a4326c901a9b42174aaa878c0ffc20306f301a25569eddfd929a297396552b0",
    BEARER_ID: "97d33444659502efd1c82b2cc4440089a41b78aeba32acbc84eae2cd74218af8",
}

FOREST_ENCOUNTER_REFERENCE_IDS = {
    "camp-under-new-leaves": (
        ORRA_ID,
        HESSA_ID,
        SALT_AND_GLASS_ID,
        BEARER_ID,
        MEREWASH_ID,
        NAHL_ID,
        SIO_ID,
    ),
    "wagons-in-the-forked-roots": (HESSA_ID, PELEN_ID, JUN_ID),
    "soilbearer-road": (PELEN_ID, NAHL_ID, ORRA_ID),
    "lantern-canopy": (NAHL_ID,),
    "warm-rain-basins": (ORRA_ID, NAHL_ID, BEARER_ID, JUN_ID),
    "hollow-of-kept-voices": (NAHL_ID, SIO_ID, MEREWASH_ID, HESSA_ID, JUN_ID),
    "blackgrass-burn": (PELEN_ID, NAHL_ID),
    "root-breath-chamber": (BEARER_ID, PELEN_ID, NAHL_ID, JUN_ID),
    "crown-of-unfallen-rain": (MEREWASH_ID, BEARER_ID, SALT_AND_GLASS_ID, JUN_ID),
    "glass-verge": (
        SALT_AND_GLASS_ID,
        ORRA_ID,
        HESSA_ID,
        MEREWASH_ID,
        NAHL_ID,
        PELEN_ID,
        SIO_ID,
        BEARER_ID,
        JUN_ID,
    ),
}


def test_forest_complete_library_retains_stable_subjects_without_live_state() -> None:
    adventure = load_adventure(FOREST_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references) == FOREST_REFERENCE_IDS
    assert tuple(reference.kind for reference in adventure.references) == (
        "person",
        "person",
        "person",
        "person",
        "person",
        "person",
        "place",
        "place",
        "other",
    )
    assert references[ORRA_ID].aliases == ("Caravan Master Orra Venn", "Orra")
    assert references[HESSA_ID].aliases == ("Hessa", "Roster Keeper Hessa Clay")
    assert references[NAHL_ID].aliases == ("Nahl", "Watershed Assessor Nahl Reed")
    assert references[PELEN_ID].aliases == ("Pelen", "Wheelwright Pelen Marr")
    assert references[SIO_ID].aliases == ("Sio", "Route-singer Sio Tern")
    assert references[JUN_ID].aliases == ("Jun", "Drover Jun Alder")
    assert references[MEREWASH_ID].aliases == ()
    assert references[SALT_AND_GLASS_ID].aliases == ("White Salt", "Glass Waste")
    assert references[BEARER_ID].aliases == (
        "the root animal",
        "the immense root animal",
    )

    assert "private cargo" in references[ORRA_ID].content
    assert "A voice is not a person" in references[HESSA_ID].content
    assert "A working course gives no order" in references[NAHL_ID].content
    assert "Responsibility without title" in references[PELEN_ID].content
    assert "inheritance cannot certify" in references[SIO_ID].content
    assert "Before east becomes a road" in references[JUN_ID].content
    assert "Ground that can receive a course" in references[MEREWASH_ID].content
    assert "Dawn closes the salt" in references[SALT_AND_GLASS_ID].content
    assert "A forest carried, not one will" in references[BEARER_ID].content
    assert "Current burdens, cooling, favored band" in references[BEARER_ID].content
    assert "Current cargo, seed condition, custody" in references[MEREWASH_ID].content
    assert "Exact route capacity and current departure groups" in references[
        SALT_AND_GLASS_ID
    ].content

    actual_link_counts = dict.fromkeys(FOREST_REFERENCE_IDS, 0)
    for encounter in adventure.encounters:
        assert tuple(link.reference_id for link in encounter.reference_links) == (
            FOREST_ENCOUNTER_REFERENCE_IDS[encounter.id]
        )
        for link in encounter.reference_links:
            actual_link_counts[link.reference_id] += 1
            assert link.context
    assert actual_link_counts == FOREST_REFERENCE_LINK_COUNTS
    assert sum(actual_link_counts.values()) == 42
    assert validate_adventure(adventure).is_valid


def test_forest_reference_library_is_retrievable_and_journal_neutral() -> None:
    adventure = load_adventure(FOREST_ROOT / "adventure.json")
    state = load_play_state(FOREST_ROOT / "play-state.example.json")

    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    for title in ("Orra Venn", "Merewash", "The White Salt and the Glass Waste", "The Bearer"):
        assert title in library
    assert library.index(f"/references/{ORRA_ID}") < library.index(
        f"/references/{MEREWASH_ID}"
    )
    assert library.index(f"/references/{MEREWASH_ID}") < library.index(
        f"/references/{BEARER_ID}"
    )

    status, _, detail = request_wsgi(author_app, f"/references/{BEARER_ID}")
    assert status == "200 OK"
    assert "Traction, venting, one deep breath" in detail
    assert "Root-Breath Chamber" in detail
    assert "Glass Verge" in detail

    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, play = request_wsgi(
        play_app,
        "/play",
        query=urlencode(
            {
                "encounter": "root-breath-chamber",
                "reference": BEARER_ID,
            }
        ),
    )
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{BEARER_ID}"' in play
    assert "A forest carried, not one will" in play
    assert 'data-play-pin-kind="reference"' in play
    assert project.snapshot == before


def test_forest_generated_packet_and_historical_archive_remain_synchronized() -> None:
    adventure = load_adventure(FOREST_ROOT / "adventure.json")
    state = load_play_state(FOREST_ROOT / "play-state.example.json")
    archive = load_journal_archive(
        FOREST_ROOT / "archives/saltward-four-demonstrated-playthrough.journal.json"
    )
    documents = render_adventure_documents(
        adventure,
        validate_adventure(adventure),
        state,
    )

    assert documents["references/index.md"] == (
        FOREST_ROOT / "generated" / "references" / "index.md"
    ).read_text(encoding="utf-8")
    assert "## People" in documents["references/index.md"]
    assert "## Places" in documents["references/index.md"]
    assert "## Other" in documents["references/index.md"]
    for reference_id in FOREST_REFERENCE_IDS:
        sheet_name = f"references/{reference_id}.md"
        assert sheet_name in documents
        assert documents[sheet_name] == (
            FOREST_ROOT / "generated" / "references" / f"{reference_id}.md"
        ).read_text(encoding="utf-8")
    for encounter in adventure.encounters:
        sheet_name = f"encounters/{encounter.id}.md"
        assert documents[sheet_name] == (
            FOREST_ROOT / "generated" / sheet_name
        ).read_text(encoding="utf-8")

    assert len(state.events) == 196
    assert archive.event_count == 196
    assert archive.play_state == state
    assert not archive.adventure_snapshot.references
    assert all(
        not encounter.reference_links for encounter in archive.adventure_snapshot.encounters
    )
    assert_historical_archive_structure(archive.adventure_snapshot, adventure)


def test_forest_voice_iii_repairs_seams_without_moving_operational_state() -> None:
    adventure = load_adventure(FOREST_ROOT / "adventure.json")
    archive = load_journal_archive(
        FOREST_ROOT / "archives/saltward-four-demonstrated-playthrough.journal.json"
    )
    encounters = adventure.encounter_index()
    references = adventure.reference_index()

    assert "sets a closed shining flower between" in encounters[
        "camp-under-new-leaves"
    ].content
    assert "Nahl spreads Merewash's notes beneath the cords" in encounters[
        "hollow-of-kept-voices"
    ].content
    assert "A wagon bell hangs still in the seam" in encounters[
        "root-breath-chamber"
    ].content
    assert "## Four beats under load" in encounters["root-breath-chamber"].content
    assert "These are not six objects tipped into one shell" in encounters[
        "crown-of-unfallen-rain"
    ].content
    assert "## The crown bears no claim" in encounters[
        "crown-of-unfallen-rain"
    ].content
    assert "## Three roads before the salt closes" in encounters["glass-verge"].content
    assert "Silence, absence, and unheard plans make no departure entry" in encounters[
        "glass-verge"
    ].content

    assert "a watershed assessor bound for Merewash" not in encounters[
        "camp-under-new-leaves"
    ].content
    assert "Merewash lies below a stony northern rise" not in encounters[
        "hollow-of-kept-voices"
    ].content
    assert "The Bearer moves without legs" not in encounters[
        "root-breath-chamber"
    ].content
    assert "The Glass Verge is the moving edge" not in encounters["glass-verge"].content

    for reference_id, expected_hash in FOREST_REFERENCE_BODY_HASHES.items():
        body = "\n".join(
            line
            for line in references[reference_id].content.splitlines()
            if not line.startswith("## ")
        )
        assert hashlib.sha256(body.encode()).hexdigest() == expected_hash

    assert tuple(reference.id for reference in adventure.references) == FOREST_REFERENCE_IDS
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 42
    assert len(adventure.encounters) == 10
    assert len(adventure.revelations) == 18
    assert len(adventure.clues) == 94
    assert sum(len(encounter.opening_view.split()) for encounter in adventure.encounters) == 620
    assert_historical_archive_structure(archive.adventure_snapshot, adventure)


def test_forest_coherence_iii_closes_the_library_without_freezing_live_state() -> None:
    adventure = load_adventure(FOREST_ROOT / "adventure.json")
    state = load_play_state(FOREST_ROOT / "play-state.example.json")
    archive = load_journal_archive(
        FOREST_ROOT / "archives/saltward-four-demonstrated-playthrough.journal.json"
    )
    report = validate_adventure(adventure)

    necessary_revelation_ids = {
        revelation.id for revelation in adventure.revelations if revelation.required
    }
    sources_by_revelation = {
        revelation_id: set() for revelation_id in necessary_revelation_ids
    }
    for clue in adventure.clues:
        if clue.revelation_id in sources_by_revelation:
            sources_by_revelation[clue.revelation_id].add(clue.source_encounter_id)

    assert len(necessary_revelation_ids) == 18
    for skipped in adventure.encounters:
        assert min(
            len(sources - {skipped.id}) for sources in sources_by_revelation.values()
        ) >= 2
    assert report.is_valid
    assert report.edge_connectivity == 5

    rescue = (FOREST_ROOT / "CARAVAN-AND-RESCUE-LEDGER.md").read_text(
        encoding="utf-8"
    )
    migration = (FOREST_ROOT / "MIGRATION-LEDGER.md").read_text(encoding="utf-8")
    ecology = (FOREST_ROOT / "ECOLOGY-OPERATING-SHEET.md").read_text(
        encoding="utf-8"
    )
    crown = (FOREST_ROOT / "CROWN-VERGE-OPERATING-SHEET.md").read_text(
        encoding="utf-8"
    )
    gm_sheet = (FOREST_ROOT / "GM-OPERATING-SHEET.md").read_text(
        encoding="utf-8"
    )
    verge = adventure.encounter_index()["glass-verge"].content

    assert "Never add the adventurers on top of the roster" in rescue
    assert "A person under immediate load does not meaningfully consent" in rescue
    assert "No NPC, team, wagon component, or current-carrying object" in gm_sheet
    assert "One destroyed or inaccessible source still leaves at least two" in gm_sheet
    assert "Accommodation is not diplomacy" in ecology
    assert "A strong current can compensate for one *weak* adjacent relationship" in ecology
    assert "Do not merge distinct choices into “the caravan decided.”" in crown
    assert "Silence, absence, and unheard plans make no departure entry" in verge


    documents = render_adventure_documents(adventure, report, state)
    assert len(documents) == 26
    assert len(state.events) == archive.event_count == 196
    assert archive.play_state == state
    assert_historical_archive_structure(archive.adventure_snapshot, adventure)

    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")

    assert (
        "Completed *The Forest That Carries Dawn* Reference Defragmentation "
        "Coherence III" in changelog
    )
