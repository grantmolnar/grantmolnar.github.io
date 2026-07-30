"""Salt Road reference defragmentation and preservation evidence."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode
from uuid import UUID

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.corpus_contracts import assert_rendered_documents_match
from tests.support.web import build_authoring_app, build_play_app, request_wsgi

pytestmark = pytest.mark.corpus

SALT_ROAD_ROOT = Path("examples/the-princess-on-the-salt-road")
IANTHE_ID = "644282b7-3868-49ce-b3f0-d3dc07adc9dd"
KALLIAS_ID = "04503a2a-aaaf-45e2-861a-82086beb6b08"
DORION_ID = "f02f94a8-169f-4631-a568-097aa3cd1874"
NAEVAN_ID = "dd602e22-aad8-4764-a247-4fe51c51e0b4"
SERATHIEL_ID = "160fb7e4-c2bb-43d0-a1c2-6a93cdbe9d26"
SABLE_ID = "d95abd3e-46a9-428a-a156-8209e470aaab"
GATE_HORNS_ID = "7629c10a-cdd0-461c-a726-46e8d5d97bce"
CYPRESS_GATE_ID = "1f0a8db8-dbf8-4a1a-8d4f-b4bf1dbbc83e"
RED_BRIDGE_ID = "39a5afa6-d1c3-43d3-9f9a-ecffcfd76d03"
REED_VILLAGES_ID = "84c000cd-1862-436c-9f8e-c98fce5634f9"
BEACON_HILL_ID = "bcee41cb-fe8c-4fd1-99a3-00906f76d751"
MYRINE_HARBOR_ID = "64f67879-a64e-46ec-ab14-1e5ef542dffd"
WHITE_CYPRESS_ID = "33e2c1c9-6187-411f-b356-7627db7b2a92"
ASH_KNIVES_ID = "a4c3844d-a690-499a-9520-9e59f57d1919"
BRONZE_SEAL_ID = "c487ef1c-b7f3-46ea-8ce8-cf61b5655c6e"

SESSION_ONE_REFERENCE_IDS = (
    IANTHE_ID,
    KALLIAS_ID,
    DORION_ID,
    NAEVAN_ID,
    SERATHIEL_ID,
)
SESSION_TWO_REFERENCE_IDS = (
    SABLE_ID,
    GATE_HORNS_ID,
    CYPRESS_GATE_ID,
    RED_BRIDGE_ID,
    REED_VILLAGES_ID,
    BEACON_HILL_ID,
    MYRINE_HARBOR_ID,
    WHITE_CYPRESS_ID,
    ASH_KNIVES_ID,
    BRONZE_SEAL_ID,
)
REFERENCE_IDS = SESSION_ONE_REFERENCE_IDS + SESSION_TWO_REFERENCE_IDS

SESSION_ONE_LINKS = {
    "house-of-blue-lamps": (IANTHE_ID, KALLIAS_ID, DORION_ID, SERATHIEL_ID),
    "gate-of-horns": (IANTHE_ID, KALLIAS_ID, DORION_ID),
    "dry-aqueduct": (IANTHE_ID, KALLIAS_ID, DORION_ID),
    "cypress-gate": (IANTHE_ID, KALLIAS_ID, DORION_ID),
    "house-at-three-cypresses": SESSION_ONE_REFERENCE_IDS,
    "red-bridge": (IANTHE_ID, KALLIAS_ID, DORION_ID),
    "reed-villages": SESSION_ONE_REFERENCE_IDS,
    "beacon-hill": (IANTHE_ID, KALLIAS_ID, DORION_ID, NAEVAN_ID),
    "myrine-harbor": SESSION_ONE_REFERENCE_IDS,
}

APPENDED_LINKS = {
    "house-of-blue-lamps": (
        SABLE_ID,
        GATE_HORNS_ID,
        CYPRESS_GATE_ID,
        RED_BRIDGE_ID,
        REED_VILLAGES_ID,
        MYRINE_HARBOR_ID,
        ASH_KNIVES_ID,
        BRONZE_SEAL_ID,
    ),
    "gate-of-horns": (GATE_HORNS_ID, RED_BRIDGE_ID, ASH_KNIVES_ID, BRONZE_SEAL_ID),
    "dry-aqueduct": (ASH_KNIVES_ID, BRONZE_SEAL_ID),
    "cypress-gate": (CYPRESS_GATE_ID, ASH_KNIVES_ID),
    "house-at-three-cypresses": (
        SABLE_ID,
        GATE_HORNS_ID,
        CYPRESS_GATE_ID,
        RED_BRIDGE_ID,
        REED_VILLAGES_ID,
        BEACON_HILL_ID,
        MYRINE_HARBOR_ID,
        WHITE_CYPRESS_ID,
        ASH_KNIVES_ID,
        BRONZE_SEAL_ID,
    ),
    "red-bridge": (
        SABLE_ID,
        RED_BRIDGE_ID,
        REED_VILLAGES_ID,
        BEACON_HILL_ID,
        ASH_KNIVES_ID,
        BRONZE_SEAL_ID,
    ),
    "reed-villages": (
        SABLE_ID,
        RED_BRIDGE_ID,
        REED_VILLAGES_ID,
        BEACON_HILL_ID,
        MYRINE_HARBOR_ID,
        WHITE_CYPRESS_ID,
        ASH_KNIVES_ID,
        BRONZE_SEAL_ID,
    ),
    "beacon-hill": (
        RED_BRIDGE_ID,
        REED_VILLAGES_ID,
        BEACON_HILL_ID,
        MYRINE_HARBOR_ID,
        WHITE_CYPRESS_ID,
        ASH_KNIVES_ID,
        BRONZE_SEAL_ID,
    ),
    "myrine-harbor": (
        REED_VILLAGES_ID,
        BEACON_HILL_ID,
        MYRINE_HARBOR_ID,
        WHITE_CYPRESS_ID,
        ASH_KNIVES_ID,
        BRONZE_SEAL_ID,
    ),
}
EXPECTED_LINKS = {
    encounter_id: SESSION_ONE_LINKS[encounter_id] + APPENDED_LINKS[encounter_id]
    for encounter_id in SESSION_ONE_LINKS
}
EXPECTED_COUNTS = {
    IANTHE_ID: 9,
    KALLIAS_ID: 9,
    DORION_ID: 9,
    NAEVAN_ID: 4,
    SERATHIEL_ID: 4,
    SABLE_ID: 4,
    GATE_HORNS_ID: 3,
    CYPRESS_GATE_ID: 3,
    RED_BRIDGE_ID: 6,
    REED_VILLAGES_ID: 6,
    BEACON_HILL_ID: 5,
    MYRINE_HARBOR_ID: 5,
    WHITE_CYPRESS_ID: 4,
    ASH_KNIVES_ID: 9,
    BRONZE_SEAL_ID: 8,
}


def _without_reference_layer() -> str:
    payload = json.loads((SALT_ROAD_ROOT / "adventure.json").read_text(encoding="utf-8"))
    payload.pop("references", None)
    for encounter in payload["encounters"]:
        encounter.pop("reference_links", None)
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


def _session_one_prefix_hash() -> str:
    payload = json.loads((SALT_ROAD_ROOT / "adventure.json").read_text(encoding="utf-8"))
    prefix = {
        "references": payload["references"][: len(SESSION_ONE_REFERENCE_IDS)],
        "reference_links": {
            encounter["id"]: encounter["reference_links"][: len(SESSION_ONE_LINKS[encounter["id"]])]
            for encounter in payload["encounters"]
        },
    }
    canonical = json.dumps(
        prefix,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    return hashlib.sha256(canonical).hexdigest()


def test_salt_road_extraction_i_records_and_links_remain_exact_prefixes() -> None:
    adventure = load_adventure(SALT_ROAD_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references[:5]) == SESSION_ONE_REFERENCE_IDS
    assert _session_one_prefix_hash() == (
        "a891469a7cd0996f8d787cb6e7fe13bd0443709a15fa859f298d5a4bed2c33e6"
    )
    assert references[IANTHE_ID].aliases == (
        "Ianthe Aulonid",
        "Ianthe",
        "Princess Ianthe",
    )
    assert references[NAEVAN_ID].aliases == ("Naevan", "Serathiel's envoy")

    counts: Counter[str] = Counter()
    for encounter in adventure.encounters:
        expected_prefix = SESSION_ONE_LINKS[encounter.id]
        actual_prefix = tuple(
            link.reference_id for link in encounter.reference_links[: len(expected_prefix)]
        )
        assert actual_prefix == expected_prefix
        counts.update(actual_prefix)
    assert dict(counts) == {
        IANTHE_ID: 9,
        KALLIAS_ID: 9,
        DORION_ID: 9,
        NAEVAN_ID: 4,
        SERATHIEL_ID: 4,
    }
    assert sum(counts.values()) == 35


def test_salt_road_extraction_ii_records_and_links_are_bounded_and_ordered() -> None:
    adventure = load_adventure(SALT_ROAD_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references) == REFERENCE_IDS
    assert tuple(reference.kind for reference in adventure.references) == (
        *("person",) * 5,
        "organization",
        *("place",) * 6,
        "organization",
        "organization",
        "object",
    )
    assert references[SABLE_ID].aliases == (
        "Sable courier network",
        "House of Blue Lamps",
        "House at Three Cypresses",
    )
    assert references[REED_VILLAGES_ID].aliases == (
        "Kalamai, Vathys, and Nesos",
        "reed channels",
    )
    assert references[BRONZE_SEAL_ID].aliases == (
        "bronze seal",
        "royal seal",
        "city seal",
    )
    assert all(UUID(reference.id).version == 4 for reference in adventure.references)

    counts: Counter[str] = Counter()
    for encounter in adventure.encounters:
        assert tuple(link.reference_id for link in encounter.reference_links) == EXPECTED_LINKS[
            encounter.id
        ]
        for link in encounter.reference_links:
            counts[link.reference_id] += 1
            assert link.context
    assert dict(counts) == EXPECTED_COUNTS
    assert sum(counts.values()) == 88

    forbidden = (
        "Damon",
        "Melia",
        "Phaedra",
        "Thaleia",
        "currently holds",
        "has accepted",
        "has reached Myrine",
        "the Sea-Lark is waiting",
        "the petition has begun",
    )
    for reference_id in SESSION_TWO_REFERENCE_IDS:
        reference = references[reference_id]
        text = reference.summary + "\n" + reference.content
        for phrase in forbidden:
            assert phrase not in text
        assert "remain live" in reference.content

    assert validate_adventure(adventure).is_valid


def test_salt_road_reference_layer_is_semantically_additive() -> None:
    adventure_path = SALT_ROAD_ROOT / "adventure.json"
    state_path = SALT_ROAD_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)

    assert _without_reference_layer() == (
        "d48e7f2528451a0237d04ec800eac0b3b4eb20037f5c3847d4d8282b34d8b537"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "5aa60873b24c332a788fbb3dcb35daf59079398a711cf29aae5bc9f28c15af1e"
    )
    assert len(adventure.encounters) == 9
    assert len(adventure.revelations) == 20
    assert len(adventure.clues) == 93
    assert len(adventure.references) == 15
    assert len(state.events) == 136
    assert validate_adventure(adventure).edge_connectivity == 4


def test_salt_road_reference_views_are_retrievable_and_journal_neutral() -> None:
    adventure = load_adventure(SALT_ROAD_ROOT / "adventure.json")
    state = load_play_state(SALT_ROAD_ROOT / "play-state.example.json")

    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    for title in (
        "Princess Ianthe Aulonid",
        "Strategos Kallias Arven",
        "Captain Dorion Vey",
        "Naevan of the White Cypress",
        "Serathiel of the White Cypress",
        "The Sable Courier Houses",
        "The Gate of Horns",
        "The Cypress Gate",
        "The Red Bridge",
        "The Reed Villages",
        "Beacon Hill",
        "Myrine Harbor",
        "The White Cypress",
        "The Ash Knives",
        "The Aulonite Bronze Seal",
    ):
        assert title in library

    status, _, detail = request_wsgi(author_app, f"/references/{SABLE_ID}")
    assert status == "200 OK"
    assert "The House of Blue Lamps" in detail
    assert "The House at Three Cypresses" in detail
    assert "The Red Bridge" in detail
    assert "The Reed Villages" in detail

    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, body = request_wsgi(
        play_app,
        "/play",
        query=urlencode(
            {
                "encounter": "myrine-harbor",
                "reference": BRONZE_SEAL_ID,
            }
        ),
    )
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{BRONZE_SEAL_ID}"' in body
    assert "The Aulonite Bronze Seal" in body
    assert project.snapshot == before


def test_salt_road_packet_adds_reference_views_without_changing_demonstration() -> None:
    adventure = load_adventure(SALT_ROAD_ROOT / "adventure.json")
    state_path = SALT_ROAD_ROOT / "play-state.example.json"
    state = load_play_state(state_path)
    documents = render_adventure_documents(adventure, validate_adventure(adventure), state)

    assert len(documents) == 31
    index = documents["references/index.md"]
    for heading in ("## People", "## Places", "## Organizations", "## Objects"):
        assert heading in index
    for reference_id in REFERENCE_IDS:
        assert f"references/{reference_id}.md" in documents
    assert_rendered_documents_match(
        documents, SALT_ROAD_ROOT / "generated"
    )


def test_salt_road_voice_iii_freezes_every_non_prose_semantic() -> None:
    adventure_path = SALT_ROAD_ROOT / "adventure.json"
    state_path = SALT_ROAD_ROOT / "play-state.example.json"
    payload = json.loads(adventure_path.read_text(encoding="utf-8"))

    encounter_content = {
        encounter["id"]: encounter.pop("content") for encounter in payload["encounters"]
    }
    reference_content = {
        reference["id"]: reference.pop("content") for reference in payload["references"]
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()

    assert hashlib.sha256(canonical).hexdigest() == (
        "9d166c6415528c55a1358e21404b2fddbf35d44bc3a711c27a6e26b40089f8e9"
    )
    assert tuple(encounter_content) == tuple(EXPECTED_LINKS)
    assert tuple(reference_content) == REFERENCE_IDS
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "5aa60873b24c332a788fbb3dcb35daf59079398a711cf29aae5bc9f28c15af1e"
    )


def test_salt_road_voice_iii_repairs_only_the_documented_seams() -> None:
    adventure_path = SALT_ROAD_ROOT / "adventure.json"
    adventure = load_adventure(adventure_path)
    encounters = adventure.encounter_index()
    references = adventure.reference_index()

    expected_encounter_hashes = {
        "house-of-blue-lamps": "20e25e179c6a0e8cd061dacab10041afdb7ce9049e8ff0663b924eb606317509",
        "gate-of-horns": "30acbde513fc8eb32a0f49e4e1ba425ae0368ce28bf2b65ab683fe6c79088b88",
        "dry-aqueduct": "06d1dd2ede13f91e7cc4354de66ed1896d9a4b158275f097b5eab649ea8759db",
        "cypress-gate": "d708e586890526079f308ec11103d7217c65fa1ac8fb41a3b6fd0e98a2be525d",
        "house-at-three-cypresses": "762bea4a3ebd5f2e134e6c93b3efa6271ba9e195f4b47fca5cc16942a4d3c129",
        "red-bridge": "00d531f86d5f2ccfcb8732d92ce2c8b8b3b56944917bfb68ea88832ebd003359",
        "reed-villages": "652eb38b90974a5b995c80107ce58c8056f9173f5e1b8ecd206bfb0b19697150",
        "beacon-hill": "f67cded2d813353ad4fc3e13cee848bbc15e93990ec92e3e7ab68a905f76b480",
        "myrine-harbor": "32f40e2c882d3784aa3b44796417b9634a8eea27b55e7316ba91b22f8e36d16d",
    }
    expected_reference_hashes = {
        IANTHE_ID: "f96f9847eea2c1cb8885a26d33337df0b975d1acab55775eb113167d55177169",
        KALLIAS_ID: "ba1e11c8757112cad6fb249c8f2bedfa9a90a69d0db218839238ab35da25968b",
        DORION_ID: "f94089d25f0febb2926b8dc898a3cb48c2649c76b3e2d59cd302f7c38ba6f995",
        NAEVAN_ID: "d0a4da983da4c6cfa2edd9552321fd0f1e371fbe5a6672a93da050f92d7f5b10",
        SERATHIEL_ID: "8c91fb14de48836268f18e1e68faa5705d2f967b1adc2ff7c52b414b0f661b7f",
        SABLE_ID: "a166fdab34df94ed5104ea141647e4cbf3b1e29eecc705533489b7cbbd337bec",
        GATE_HORNS_ID: "6d29a5db1c23542c43aeb09260c0ab040cf1e7f57bcb971c0f40f8b5acb449b0",
        CYPRESS_GATE_ID: "0d649d41f2ab52e19c2329a41cc7eb151fff3adb39e252bc51ad93af0a2b60eb",
        RED_BRIDGE_ID: "e4ba8869e0aba300c49c92db210611c2f755f548342159202600ce1deedb59a0",
        REED_VILLAGES_ID: "04fb372e26af40566e2d9a1f77aaa644792463730e64d3353e9ebf0311976040",
        BEACON_HILL_ID: "f7052b6c614dc994e5a5ee7ca7c3fda9cbefbe91e9354a21b0e5f150496c6e79",
        MYRINE_HARBOR_ID: "ccf25ac944d3d9d5296632d576f992fdfe7463556f27ce562b68585e444788ec",
        WHITE_CYPRESS_ID: "08b6b509315a1a34e5efa607f60f5ec517e4d47c10fe13042cc3ec9d839c7b60",
        ASH_KNIVES_ID: "cdb3617a3a558f4b71962770153651dc085b687f9805d12e89db8299ec3418b1",
        BRONZE_SEAL_ID: "af2be89519e4d50cf1f842af1d6a85055dd8c490ec7a977cf96eb33e06198585",
    }

    for encounter_id, expected_hash in expected_encounter_hashes.items():
        assert hashlib.sha256(encounters[encounter_id].content.encode()).hexdigest() == expected_hash
    for reference_id, expected_hash in expected_reference_hashes.items():
        assert hashlib.sha256(references[reference_id].content.encode()).hexdigest() == expected_hash

    assert sum(len(encounter.content.split()) for encounter in adventure.encounters) == 23463
    assert sum(len(reference.content.split()) for reference in adventure.references) == 3147
    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "25b2d169ff152566ca4b7666931ccd9215abb4b0e343de587e2191c3dd639150"
    )

    expected_live_openings = {
        "house-of-blue-lamps": "Myrto has shuttered the blue lamps",
        "gate-of-horns": "Kallias’s white command lamps burn above the paired towers",
        "cypress-gate": "Mourning lamps move toward Aulon’s western wall",
        "house-at-three-cypresses": "She puts two names on the stable table",
        "red-bridge": "two incompatible writs wait in one wax box",
        "reed-villages": "A confiscation board has turned the three Reed Villages",
        "beacon-hill": "Myrine already acting on someone else’s nouns",
        "myrine-harbor": "Captain Eudora is already assigning armed arrivals",
    }
    for encounter_id, phrase in expected_live_openings.items():
        assert phrase in encounters[encounter_id].content

    retired_repetition = {
        "house-of-blue-lamps": "The House of Blue Lamps belongs to **Myrto Sable**",
        "gate-of-horns": "The Gate of Horns was built to make passage public",
        "cypress-gate": "The Cypress Gate exists so the dead never pass through the market",
        "red-bridge": "Six red-stone arches carry the road across Kestros Gorge",
        "reed-villages": "**Kalamai** dries mats along the upper channels",
        "beacon-hill": "Beacon Hill is the last height between the inland road and Myrine Harbor",
    }
    for encounter_id, phrase in retired_repetition.items():
        assert phrase not in encounters[encounter_id].content


def test_salt_road_coherence_iii_closes_the_sequence_without_canonical_change() -> None:
    adventure_path = SALT_ROAD_ROOT / "adventure.json"
    state_path = SALT_ROAD_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    encounters = adventure.encounter_index()

    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "25b2d169ff152566ca4b7666931ccd9215abb4b0e343de587e2191c3dd639150"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "5aa60873b24c332a788fbb3dcb35daf59079398a711cf29aae5bc9f28c15af1e"
    )
    assert len(adventure.encounters) == 9
    assert len(adventure.revelations) == 20
    assert len(adventure.clues) == 93
    assert len(adventure.references) == 15
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 88
    assert len(state.events) == 136
    assert validate_adventure(adventure).edge_connectivity == 4

    source_encounters: dict[str, set[str]] = {
        revelation.id: set() for revelation in adventure.revelations if revelation.required
    }
    for clue in adventure.clues:
        if clue.revelation_id in source_encounters:
            source_encounters[clue.revelation_id].add(clue.source_encounter_id)
    assert len(source_encounters) == 20
    for sources in source_encounters.values():
        assert len(sources) >= 3
        for removed in encounters:
            assert len(sources - {removed}) >= 2


    reference_text = "\n".join(
        reference.summary + "\n" + reference.content for reference in adventure.references
    )
    for demonstrated_state in (
        "pursuit begins Unfixed",
        "the pursuit becomes Named",
        "Dorion reaches Contact",
        "Myrine takes the bronze seal",
        "Ianthe completes a free petition",
        "Ianthe, Melia, and Thaleia sail",
        "Damon and Phaedra remain free",
        "the deadline becomes doubtful",
    ):
        assert demonstrated_state not in reference_text

    consequences = "\n".join(
        event.text
        for event in state.active_events
        if type(event).__name__ == "EncounterConsequenceRecordedEvent"
    )
    for phrase in (
        "pursuit begins Unfixed",
        "The pursuit becomes Named",
        "Dorion takes physical custody of the bronze seal",
        "Myrine takes the bronze seal",
        "Ianthe completes a free petition",
        "Ianthe, Melia, and Thaleia sail",
        "Damon and Phaedra remain free",
    ):
        assert phrase in consequences

    documents = render_adventure_documents(adventure, validate_adventure(adventure), state)
    assert len(documents) == 31
    assert_rendered_documents_match(
        documents, SALT_ROAD_ROOT / "generated"
    )


