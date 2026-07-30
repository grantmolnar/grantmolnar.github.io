"""Bramblewick reference-library extraction and preservation evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlencode

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.domain.adventure import Clue
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.web import build_authoring_app, build_play_app, request_wsgi

pytestmark = pytest.mark.corpus

BRAMBLEWICK_ROOT = Path("examples/the-last-bell-of-bramblewick")
MERRIT_ID = "ebd4c505-37a2-4c07-8358-c449ccd4561f"
ORLO_ID = "33339ed8-373a-456a-8899-fec4007260ea"
HESTER_ID = "40ac8ad0-a605-46ce-8964-5dff2bc84c8b"
WIL_ID = "459d69fc-b40f-403f-bd03-9d87be597512"
AMITY_ID = "fe655672-7df2-49e9-a4ed-0de4764069ca"
NIM_ID = "59f78a00-e4c0-4b1c-9853-ae9409715e8a"
BRAM_ID = "93ccf6ae-a597-41d7-bf78-623bc46d8ba7"
MARA_ID = "6ca613bc-901c-4903-b629-7616e1de7138"
CORA_ID = "7b980ead-bd09-4034-a5a8-b18c1ceaaf45"
PERRIN_ID = "f306d63b-3fd3-4eaa-b581-035ed71172b0"
HEARTH_BOOK_ID = "5986fde0-8b35-423a-892c-b9168c87e3c5"
COMMON_CHEST_ID = "b0fbb6aa-8f2c-49d4-86ee-22a96e08ef70"
FIRST_BELL_MOOT_ID = "6540034b-60ec-404a-9768-173890c55c68"
SCHOOL_ID = "83fb58dc-f264-4e88-aaa5-0981fd907b11"
CHAPEL_ID = "b4d821cc-ccfa-42ac-80ed-fe842bd3d9ee"
NORTH_HEDGE_ID = "586737d7-f233-4db3-80b8-a3e064612a6d"

BRAMBLEWICK_REFERENCE_IDS = (
    MERRIT_ID,
    ORLO_ID,
    HESTER_ID,
    WIL_ID,
    AMITY_ID,
    NIM_ID,
    BRAM_ID,
    MARA_ID,
    CORA_ID,
    PERRIN_ID,
    HEARTH_BOOK_ID,
    COMMON_CHEST_ID,
    FIRST_BELL_MOOT_ID,
    SCHOOL_ID,
    CHAPEL_ID,
    NORTH_HEDGE_ID,
)
BRAMBLEWICK_REFERENCE_LINK_COUNTS = {
    MERRIT_ID: 10,
    ORLO_ID: 8,
    HESTER_ID: 8,
    WIL_ID: 5,
    AMITY_ID: 4,
    NIM_ID: 2,
    BRAM_ID: 4,
    MARA_ID: 3,
    CORA_ID: 3,
    PERRIN_ID: 3,
    HEARTH_BOOK_ID: 6,
    COMMON_CHEST_ID: 7,
    FIRST_BELL_MOOT_ID: 6,
    SCHOOL_ID: 7,
    CHAPEL_ID: 5,
    NORTH_HEDGE_ID: 7,
}
BRAMBLEWICK_REFERENCE_BODY_HASHES = {
    MERRIT_ID: "79c1f07d8704bd736590f3aa5610abf0fd4ae3e0197e29e7d2f621c7a235cffb",
    ORLO_ID: "091c21b6e33566cf288c60064ee8a6f4f9ef16a78d4001758f1ccfbf39403ee7",
    HESTER_ID: "b4cd0630dc752e61991467bb7c91cbd659629072f0bae34c4e298f3981eda984",
    WIL_ID: "cf15cc52be6f367631594a914493c0fa79d7d84054085138e08a40f5f52e94fe",
    AMITY_ID: "7e95cf4aa96571652fbd4194e384f1125bc8d91a296aaa6e65dd6cb0fc885d7e",
    NIM_ID: "850970b6b1c2416caa5c2c924ede442b1d198c621b893b1d1c63d5863d3b16e0",
    BRAM_ID: "ca94e4f49d6e2300a826bedf298766d13b45c99cb7b71d10602ec095d29797ef",
    MARA_ID: "a99bb1524918647e08764ba0f3cbce39f2fa8a19e71d199b49c91ba6b6091694",
    CORA_ID: "90e8ba5c0d34f381d49c9a1993147b3480ad85255369951c5b5dbc0fcf05688b",
    PERRIN_ID: "d93a748d908a5b7829e16d45d1a6267ad6f786d739a1a919ff1dca05f25d6ca1",
    HEARTH_BOOK_ID: "9539396b323dc2fbdc4963bc03d360d7b366b5f154f029da2d01453fee2033dc",
    COMMON_CHEST_ID: "1af9e05048499210b4b9b2a2523931c1868a3e94f841ba110c41af962878e0e6",
    FIRST_BELL_MOOT_ID: "32528e6472f2a2ad2075e0c129123adcb680c4d2091721f149dbc3e73fe0350a",
    SCHOOL_ID: "c8b964ddb6a86e685b92e94b870cf07ac4e0f5f3cb62ffc54e2cd157a3eb6042",
    CHAPEL_ID: "8b45fee178d0f3dc24499ad41304258f449457f837543c4ef6d85aa905122b0b",
    NORTH_HEDGE_ID: "64a06280306eeaa6ec299ae4597dd632d241647bf2e0eba4ef803d2c1daeb13a",
}
BRAMBLEWICK_ENCOUNTER_REFERENCE_IDS = {
    "hearth-hall-and-the-map-room": (
        MERRIT_ID,
        HEARTH_BOOK_ID,
        BRAM_ID,
        MARA_ID,
        CORA_ID,
        PERRIN_ID,
        ORLO_ID,
        SCHOOL_ID,
        HESTER_ID,
        WIL_ID,
        NORTH_HEDGE_ID,
        COMMON_CHEST_ID,
        FIRST_BELL_MOOT_ID,
    ),
    "merrit-alder-s-burrow": (
        MERRIT_ID,
        HEARTH_BOOK_ID,
        BRAM_ID,
        ORLO_ID,
        HESTER_ID,
        COMMON_CHEST_ID,
        CHAPEL_ID,
        FIRST_BELL_MOOT_ID,
    ),
    "the-copper-kettle-and-long-pantry": (
        MARA_ID,
        MERRIT_ID,
        ORLO_ID,
        SCHOOL_ID,
        HESTER_ID,
        COMMON_CHEST_ID,
        NORTH_HEDGE_ID,
    ),
    "moss-apothecary": (PERRIN_ID, MERRIT_ID, HESTER_ID, WIL_ID),
    "alder-orchard": (BRAM_ID, MERRIT_ID, HESTER_ID, NORTH_HEDGE_ID),
    "bramble-mill": (
        CORA_ID,
        MERRIT_ID,
        HESTER_ID,
        COMMON_CHEST_ID,
        NORTH_HEDGE_ID,
    ),
    "the-common-chest": (
        COMMON_CHEST_ID,
        NIM_ID,
        HESTER_ID,
        MERRIT_ID,
        HEARTH_BOOK_ID,
        ORLO_ID,
        SCHOOL_ID,
        AMITY_ID,
        CHAPEL_ID,
        FIRST_BELL_MOOT_ID,
    ),
    "chapel-of-the-open-door": (
        CHAPEL_ID,
        AMITY_ID,
        MERRIT_ID,
        HEARTH_BOOK_ID,
        ORLO_ID,
        SCHOOL_ID,
        FIRST_BELL_MOOT_ID,
    ),
    "bramblewick-school": (
        SCHOOL_ID,
        ORLO_ID,
        AMITY_ID,
        WIL_ID,
        MERRIT_ID,
        HEARTH_BOOK_ID,
        COMMON_CHEST_ID,
        CHAPEL_ID,
        NORTH_HEDGE_ID,
        FIRST_BELL_MOOT_ID,
    ),
    "the-north-hedge": (NORTH_HEDGE_ID, ORLO_ID, WIL_ID, SCHOOL_ID),
    "the-first-bell-moot": (
        FIRST_BELL_MOOT_ID,
        MERRIT_ID,
        HEARTH_BOOK_ID,
        ORLO_ID,
        SCHOOL_ID,
        HESTER_ID,
        WIL_ID,
        AMITY_ID,
        CHAPEL_ID,
        NIM_ID,
        COMMON_CHEST_ID,
        BRAM_ID,
        MARA_ID,
        CORA_ID,
        PERRIN_ID,
        NORTH_HEDGE_ID,
    ),
}


def test_bramblewick_complete_library_preserves_authority_without_solution_cards() -> None:
    adventure = load_adventure(BRAMBLEWICK_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references) == (
        BRAMBLEWICK_REFERENCE_IDS
    )
    assert tuple(reference.kind for reference in adventure.references) == (
        ("person",) * 10
        + ("object", "object", "other", "organization", "organization", "place")
    )
    assert references[MERRIT_ID].aliases == ("Keeper Merrit Alder", "Merrit")
    assert references[ORLO_ID].aliases == ("Schoolmaster Orlo Vane", "Orlo")
    assert references[HESTER_ID].aliases == ("Reeve Hester Rowan", "Hester")
    assert references[WIL_ID].aliases == ("Constable Wil Sloe", "Wil")
    assert references[AMITY_ID].aliases == ("Sister Amity", "Amity")
    assert references[NIM_ID].aliases == ("Nim", "Autumn Lot-holder Nim Thatch")
    assert references[BRAM_ID].aliases == ("Bram", "Merrit's heir")
    assert references[MARA_ID].aliases == ("Mara", "Mistress Mara Kettle")
    assert references[CORA_ID].aliases == ("Cora", "Miller Cora Bramble")
    assert references[PERRIN_ID].aliases == ("Perrin", "Apothecary Perrin Moss")

    expected_headings = {
        BRAM_ID: "The orchard keeps its own time",
        MARA_ID: "A house measured in servings",
        CORA_ID: "Water, grain, and the brake",
        PERRIN_ID: "A shop of measured harms",
        HEARTH_BOOK_ID: "One village, two copies",
        COMMON_CHEST_ID: "Two doors and two keys",
        FIRST_BELL_MOOT_ID: "A morning burden, not a trial",
        SCHOOL_ID: "A room that belongs to its pupils",
        CHAPEL_ID: "An open arch and a closed confidence",
        NORTH_HEDGE_ID: "A lane used by everyone",
    }
    for reference_id, heading in expected_headings.items():
        assert heading in references[reference_id].content

    forbidden_by_reference = {
        ORLO_ID: ("killed Merrit", "murderer", "ghost hearth", "8:54", "confession"),
        HESTER_ID: ("without authorization", "served pie", "resignation"),
        MERRIT_ID: ("name Orlo", "beneficiary families", "brass acorn"),
        AMITY_ID: ("Dolly", "Pipkin", "selected them"),
        NIM_ID: ("ghost hearth", "Orlo's hand", "beneficiary box"),
        BRAM_ID: ("6:10", "cuff thread", "searched Merrit's papers", "cleared"),
        MARA_ID: ("brandy", "paid for silence", "burst crock", "cleared"),
        CORA_ID: ("ergot", "confronted Merrit", "during the murder", "cleared"),
        PERRIN_ID: ("altered dosage", "did not kill", "wrist scrape", "cleared"),
        HEARTH_BOOK_ID: ("ghost hearth", "Orlo's hand", "torn leaves"),
        COMMON_CHEST_ID: ("ghost hearth", "Hester's spending", "beneficiary box"),
        FIRST_BELL_MOOT_ID: ("Orlo", "murderer", "confession", "detained"),
        SCHOOL_ID: ("Orlo", "beneficiary box", "blood", "blue chalk"),
        CHAPEL_ID: ("Dolly", "Milo", "Pipkin", "Orlo"),
        NORTH_HEDGE_ID: ("Orlo", "blue thread", "lime", "8:54"),
    }
    for reference_id, forbidden_phrases in forbidden_by_reference.items():
        text = references[reference_id].summary + "\n" + references[reference_id].content
        for phrase in forbidden_phrases:
            assert phrase not in text

    actual_link_counts = dict.fromkeys(BRAMBLEWICK_REFERENCE_IDS, 0)
    for encounter in adventure.encounters:
        assert tuple(link.reference_id for link in encounter.reference_links) == (
            BRAMBLEWICK_ENCOUNTER_REFERENCE_IDS[encounter.id]
        )
        for link in encounter.reference_links:
            actual_link_counts[link.reference_id] += 1
            assert link.context
    assert actual_link_counts == BRAMBLEWICK_REFERENCE_LINK_COUNTS
    assert sum(actual_link_counts.values()) == 88
    assert validate_adventure(adventure).is_valid


def test_bramblewick_reference_views_are_retrievable_and_journal_neutral() -> None:
    adventure = load_adventure(BRAMBLEWICK_ROOT / "adventure.json")
    state = load_play_state(BRAMBLEWICK_ROOT / "play-state.example.json")

    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    for title in (
        "Merrit Alder",
        "Orlo Vane",
        "Hester Rowan",
        "Wil Sloe",
        "Sister Amity Thorne",
        "Nim Thatch",
        "Bram Alder",
        "Mara Kettle",
        "Cora Bramble",
        "Perrin Moss",
        "The Hearth Book",
        "The Common Chest",
        "The First-Bell Moot",
        "Bramblewick School",
        "The Chapel of the Open Door",
        "The North Hedge",
    ):
        assert title in library

    status, _, detail = request_wsgi(author_app, f"/references/{FIRST_BELL_MOOT_ID}")
    assert status == "200 OK"
    assert "A morning burden, not a trial" in detail
    assert "Hearth Hall and the Map Room" in detail
    assert "The First-Bell Moot" in detail

    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, play = request_wsgi(
        play_app,
        "/play",
        query=urlencode(
            {
                "encounter": "the-north-hedge",
                "reference": NORTH_HEDGE_ID,
            }
        ),
    )
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{NORTH_HEDGE_ID}"' in play
    assert "A lane used by everyone" in play
    assert 'data-play-pin-kind="reference"' in play
    assert project.snapshot == before


def test_bramblewick_packet_closes_reference_views_without_changing_the_journal() -> None:
    adventure = load_adventure(BRAMBLEWICK_ROOT / "adventure.json")
    state_path = BRAMBLEWICK_ROOT / "play-state.example.json"
    state = load_play_state(state_path)
    documents = render_adventure_documents(
        adventure,
        validate_adventure(adventure),
        state,
    )

    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "d9aed06752d3ece4ddefe28038f759057a3e88bd1111f36e9527bc745479836c"
    )
    assert len(state.events) == 156
    assert len(state.active_events) == 154
    assert len(documents) == 34
    assert "## People" in documents["references/index.md"]
    assert "## Objects" in documents["references/index.md"]
    assert "## Organizations" in documents["references/index.md"]
    assert "## Places" in documents["references/index.md"]
    assert "## Other" in documents["references/index.md"]
    for reference_id in BRAMBLEWICK_REFERENCE_IDS:
        sheet_name = f"references/{reference_id}.md"
        assert documents[sheet_name] == (
            BRAMBLEWICK_ROOT / "generated" / sheet_name
        ).read_text(encoding="utf-8")
    for encounter in adventure.encounters:
        sheet_name = f"encounters/{encounter.id}.md"
        assert documents[sheet_name] == (
            BRAMBLEWICK_ROOT / "generated" / sheet_name
        ).read_text(encoding="utf-8")


def test_bramblewick_voice_iii_keeps_live_work_in_encounters() -> None:
    adventure = load_adventure(BRAMBLEWICK_ROOT / "adventure.json")
    encounters = adventure.encounter_index()
    references = adventure.reference_index()

    expected_live_phrases = {
        "hearth-hall-and-the-map-room": (
            "Merrit's invitation lies open beneath Hester's hand.",
            "No paper in the room gives them a private door or a verdict.",
        ),
        "the-common-chest": (
            "Nim arrives with the second key and rain on his shoulders.",
            "The first disagreement begins before the paper does",
        ),
        "bramblewick-school": (
            "Orlo stands between both doors and the locked record cupboard.",
            "Do not ask a child whether Orlo killed Merrit.",
        ),
        "chapel-of-the-open-door": (
            "Rain has crossed the open arch and darkened the nearest floor stones.",
            "The register stays on its shelf.",
        ),
        "the-north-hedge": (
            "Wil's kitchen cord has already failed.",
            "Read what remains by depth and overlap, not by shape alone.",
        ),
        "the-first-bell-moot": (
            "Hester lays the reeve's chain on the table rather than around her neck.",
            "what Bramblewick knows well enough to do before the bridge opens",
        ),
    }
    for encounter_id, phrases in expected_live_phrases.items():
        for phrase in phrases:
            assert phrase in encounters[encounter_id].content

    retired_static_openings = {
        "hearth-hall-and-the-map-room": (
            "Merrit's signed invitation names the newcomers as outside witnesses"
        ),
        "the-common-chest": "The Common Chest fills a dry stone room",
        "bramblewick-school": "Bramblewick School is one turf-roofed room",
        "chapel-of-the-open-door": (
            "The Chapel of the Open Door is a round whitewashed room"
        ),
        "the-north-hedge": "The North Hedge is a working boundary, not a pristine track",
        "the-first-bell-moot": (
            "Hester calls the moot because no magistrate can cross the flooded bridge"
        ),
    }
    for encounter_id, phrase in retired_static_openings.items():
        assert phrase not in encounters[encounter_id].content

    expected_reference_headings = {
        MERRIT_ID: ("## The paper he left alive", "## Drawers are not a verdict"),
        ORLO_ID: ("## The school bell stops at the door", "## A timetable proves only its marks"),
        HESTER_ID: ("## No hand holds both keys", "## Her mark enters the same book"),
        WIL_ID: ("## String, seal, and every hand", "## A locked door needs a present danger"),
        AMITY_ID: ("## Copies leave; the register stays", "## A burial date carries no motive"),
        NIM_ID: ("## Two turns of brass prove no story",),
        BRAM_ID: ("## The green key opens a door, not an hour", "## The will waits for daylight"),
        MARA_ID: ("## Flour, trays, and the order of work", "## A quiet alcove is not silence"),
        CORA_ID: ("## Bell, gauge, brake, rope", "## Stop the wheel before blame"),
        PERRIN_ID: ("## Measure the wound before the blame", "## Wax records a bottle, not its whole history"),
        HEARTH_BOOK_ID: ("## A hearth carries names, debts, and bread", "## Red ink still needs a witness"),
        COMMON_CHEST_ID: ("## Name the bundle before the lock turns", "## One clean chain, few public names"),
        FIRST_BELL_MOOT_ID: ("## Lay the whole crossing on the table", "## Morning may hold; it may not punish"),
        SCHOOL_ID: ("## Bread, slate, soap, red pencil", "## Six pupils, six separate voices"),
        CHAPEL_ID: ("## The register does not cross the threshold", "## Three names, no verdict"),
        NORTH_HEDGE_ID: ("## Mud keeps order longer than ownership", "## Cord the marks, not the village"),
    }
    for reference_id, headings in expected_reference_headings.items():
        for heading in headings:
            assert heading in references[reference_id].content

    for reference_id, expected_hash in BRAMBLEWICK_REFERENCE_BODY_HASHES.items():
        body = "\n".join(
            line
            for line in references[reference_id].content.splitlines()
            if not line.startswith("## ")
        )
        assert hashlib.sha256(body.encode()).hexdigest() == expected_hash

    assert tuple(reference.id for reference in adventure.references) == (
        BRAMBLEWICK_REFERENCE_IDS
    )
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 88
    assert len(adventure.encounters) == 11
    assert len(adventure.revelations) == 26
    assert len(adventure.clues) == 123
    assert hashlib.sha256(
        (BRAMBLEWICK_ROOT / "play-state.example.json").read_bytes()
    ).hexdigest() == "d9aed06752d3ece4ddefe28038f759057a3e88bd1111f36e9527bc745479836c"


def test_bramblewick_coherence_iii_closes_sequence_without_canonical_repair() -> None:
    """Reconcile the closed library with routes, procedure, packet, and journal."""
    adventure_path = BRAMBLEWICK_ROOT / "adventure.json"
    state_path = BRAMBLEWICK_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    encounters = adventure.encounter_index()
    references = adventure.reference_index()

    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "19d0a372fba57b72965ab59ea457dec8bb99c38d2a2d838da109371974ad20b9"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "d9aed06752d3ece4ddefe28038f759057a3e88bd1111f36e9527bc745479836c"
    )
    assert len(state.events) == 156
    assert len(state.active_events) == 154
    assert all(
        type(event).__name__ != "ReferenceNoteRecordedEvent"
        for event in state.events
    )

    report = validate_adventure(adventure)
    assert report.is_valid
    assert report.edge_connectivity == 3
    assert len(adventure.encounters) == 11
    assert len(adventure.revelations) == 26
    assert len(adventure.clues) == 123
    assert len(adventure.references) == 16
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 88

    clues_by_revelation: dict[str, list[Clue]] = {}
    for clue in adventure.clues:
        clues_by_revelation.setdefault(clue.revelation_id, []).append(clue)
    encounter_ids = {encounter.id for encounter in adventure.encounters}
    reference_ids = {reference.id for reference in adventure.references}
    assert {clue.source_encounter_id for clue in adventure.clues} <= encounter_ids
    assert {clue.source_encounter_id for clue in adventure.clues}.isdisjoint(reference_ids)
    for revelation in adventure.revelations:
        if not revelation.required:
            continue
        supporting = clues_by_revelation[revelation.id]
        assert len({clue.source_encounter_id for clue in supporting}) >= 3
        for lost_encounter_id in encounter_ids:
            remaining_sources = {
                clue.source_encounter_id
                for clue in supporting
                if clue.source_encounter_id != lost_encounter_id
            }
            assert len(remaining_sources) >= 2

    assert "No paper in the room gives them a private door or a verdict." in encounters[
        "hearth-hall-and-the-map-room"
    ].content
    assert "Nim numbers each removed bundle aloud while Hester writes." in encounters[
        "the-common-chest"
    ].content
    assert "The register stays on its shelf." in encounters[
        "chapel-of-the-open-door"
    ].content
    assert "Do not ask a child whether Orlo killed Merrit." in encounters[
        "bramblewick-school"
    ].content
    assert "Capture secures him; it does not prove the murder." in encounters[
        "the-first-bell-moot"
    ].content
    assert "The first presentation changes the room. It need not finish it." in encounters[
        "the-first-bell-moot"
    ].content
    assert "A suspect's unrelated offense does not change the murder." in encounters[
        "the-first-bell-moot"
    ].content

    assert "Current seal condition, key possession" in references[COMMON_CHEST_ID].content
    assert "Current attendance, testimony, exhibits" in references[SCHOOL_ID].content
    assert "Current tracks, weather damage, searches" in references[NORTH_HEDGE_ID].content
    assert "Current speakers, exhibits, votes" in references[FIRST_BELL_MOOT_ID].content

    documents = render_adventure_documents(adventure, report, state)
    assert len(documents) == 34
    for relative_name, rendered in documents.items():
        assert rendered == (BRAMBLEWICK_ROOT / "generated" / relative_name).read_text(
            encoding="utf-8"
        )


