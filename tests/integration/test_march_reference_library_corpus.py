"""March on Vossgard reference defragmentation and preservation evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.corpus_contracts import assert_rendered_documents_match
from tests.support.web import build_authoring_app, build_play_app, request_wsgi

pytestmark = pytest.mark.corpus

MARCH_ROOT = Path("examples/the-march-on-vossgard")
RUSK_ID = "e714bd67-22b9-462d-889a-c1d70af6170f"
HOLT_ID = "b9b91d52-59d8-41ba-b73e-05ab1d3e15c4"
MERROW_ID = "1fe01544-1445-48cb-b8af-c8f2d630a7cf"
VALE_ID = "bdc6dade-caff-49e9-8c4d-1f6b5eca9469"
DANE_ID = "892dbdaa-9163-44f0-8e4a-369a43864d82"
VOSS_ID = "d6384410-c4d7-4cb9-91da-ce1e19c30d0d"
MORCANT_ID = "2cfd0b01-d287-4d40-b785-ea11bc1aa001"
WARRANT_ID = "be727f0b-3d2e-44b8-9309-896dcc57726c"
GATE_ID = "545ffe74-1efc-4b32-bdf6-8ec831f34e51"
CAUSEWAY_ID = "ed795697-5230-4578-8ea0-e625d05b61ff"
VILLAGES_ID = "c7b208a6-4626-40b4-8321-54b840918905"
ABBEY_ID = "7247ca22-2063-4332-ba40-0bf7face6275"
BELL_ID = "cab5eeb5-ca45-443e-a7f7-2425c38b1ea4"
SLUICE_ID = "e510af2a-eb44-4055-945b-b09c79985a47"
VOSSGARD_ID = "613c3c19-2fd2-4de7-93ed-ba0e279e1777"

EXTRACTION_I_IDS = (RUSK_ID, HOLT_ID, MERROW_ID, VALE_ID, DANE_ID, VOSS_ID, MORCANT_ID)
EXTRACTION_II_IDS = (
    WARRANT_ID,
    GATE_ID,
    CAUSEWAY_ID,
    VILLAGES_ID,
    ABBEY_ID,
    BELL_ID,
    SLUICE_ID,
    VOSSGARD_ID,
)
REFERENCE_IDS = EXTRACTION_I_IDS + EXTRACTION_II_IDS

EXTRACTION_I_LINKS = {
    "the-ashen-gate": EXTRACTION_I_IDS,
    "the-iron-causeway": (HOLT_ID, MERROW_ID, DANE_ID, VOSS_ID),
    "the-tithe-villages": (DANE_ID, VOSS_ID),
    "the-thorn-barrows": (VALE_ID, VOSS_ID, MORCANT_ID),
    "the-red-abbey": (RUSK_ID, DANE_ID, VOSS_ID),
    "the-black-bell-redoubt": (HOLT_ID, VALE_ID, VOSS_ID),
    "the-drowned-sluice": (MERROW_ID, VOSS_ID),
    "vossgard": EXTRACTION_I_IDS,
}
EXPECTED_LINKS = {
    "the-ashen-gate": EXTRACTION_I_LINKS["the-ashen-gate"]
    + (WARRANT_ID, GATE_ID, CAUSEWAY_ID, VILLAGES_ID, VOSSGARD_ID),
    "the-iron-causeway": EXTRACTION_I_LINKS["the-iron-causeway"]
    + (WARRANT_ID, GATE_ID, CAUSEWAY_ID, VOSSGARD_ID),
    "the-tithe-villages": EXTRACTION_I_LINKS["the-tithe-villages"]
    + (WARRANT_ID, GATE_ID, VILLAGES_ID, SLUICE_ID, VOSSGARD_ID),
    "the-thorn-barrows": EXTRACTION_I_LINKS["the-thorn-barrows"]
    + (WARRANT_ID, BELL_ID, VOSSGARD_ID),
    "the-red-abbey": EXTRACTION_I_LINKS["the-red-abbey"]
    + (WARRANT_ID, ABBEY_ID, VOSSGARD_ID),
    "the-black-bell-redoubt": EXTRACTION_I_LINKS["the-black-bell-redoubt"]
    + (WARRANT_ID, VILLAGES_ID, ABBEY_ID, BELL_ID, VOSSGARD_ID),
    "the-drowned-sluice": EXTRACTION_I_LINKS["the-drowned-sluice"]
    + (WARRANT_ID, VILLAGES_ID, SLUICE_ID, VOSSGARD_ID),
    "vossgard": EXTRACTION_I_LINKS["vossgard"] + EXTRACTION_II_IDS,
}
EXPECTED_COUNTS = {
    RUSK_ID: 3,
    HOLT_ID: 4,
    MERROW_ID: 4,
    VALE_ID: 4,
    DANE_ID: 5,
    VOSS_ID: 8,
    MORCANT_ID: 3,
    WARRANT_ID: 8,
    GATE_ID: 4,
    CAUSEWAY_ID: 3,
    VILLAGES_ID: 5,
    ABBEY_ID: 3,
    BELL_ID: 3,
    SLUICE_ID: 3,
    VOSSGARD_ID: 8,
}

REFERENCE_BODY_HASHES = {
    RUSK_ID: "bc9a4af6c174e99f6b5756c19f8054fc814a93a06997c6f555c96cc4cf19c43a",
    HOLT_ID: "d00191170f8e50a3b736b48acf9f5453582e9f6dd1482fe59921c1b6e82dbaf8",
    MERROW_ID: "c81defd66abbbaae191f130ec32e77ed60202e74556a307f80c5911e743983a6",
    VALE_ID: "1bf56937cc6695b773c5c3460df8938ac4e1dd328693c6db29dca303bb7ab2c1",
    DANE_ID: "8ad3e910aeec4b2b2c0cf33d587f586577ac636cd85e0ed869b33e1323405988",
    VOSS_ID: "0effdca653a7872d6110f0691561c7c2de0104b621098b1a25a0eee16b965554",
    MORCANT_ID: "ce83ff01446e7872ddcd6c49eae44ca5550a95621646a0e0b401945fbd766d55",
    WARRANT_ID: "bd2129def78c60f0a24dd64a95be780f25b4dd58ffe9ca8fec88e70669221341",
    GATE_ID: "f68d5a7b207b1cbc3120526040a22c69356a029a1cfe9470815f3fae1ef9abff",
    CAUSEWAY_ID: "d8484fd473970dbf33136db227b8c6880c45a8ef8f83a9751a3b64a3c4d210fa",
    VILLAGES_ID: "014fd60f54fb322628df79ae8d87e96f9d4d5fad54214162b8268dc19d9350b5",
    ABBEY_ID: "a4751f8a1fa4830ea6aec7b20dcf315eafa8719f4728a1097703a7783cc52187",
    BELL_ID: "56d6c54fb93510eb1c961c7cf730525db8dd2a2c52e952f260c18019dff60129",
    SLUICE_ID: "af6cb8b7225b5b5c89bb7ab20a399279c3fdc5038f111662c029f8adc2ae40ae",
    VOSSGARD_ID: "cc97dead80eb46160e3bfe6c2b96d064a8d22f6e9f5624c19bdefd213e0a995d",
}


def _without_reference_layer() -> str:
    payload = json.loads((MARCH_ROOT / "adventure.json").read_text(encoding="utf-8"))
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


def test_march_extraction_i_records_and_links_remain_exact_prefixes() -> None:
    adventure = load_adventure(MARCH_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references[:7]) == EXTRACTION_I_IDS
    assert tuple(reference.kind for reference in adventure.references[:7]) == ("person",) * 7
    assert references[RUSK_ID].aliases == ("Aveline Rusk", "Rusk")
    assert references[VOSS_ID].aliases == ("Othmar Voss", "Voss", "Count Voss")

    for encounter in adventure.encounters:
        old_links = EXTRACTION_I_LINKS[encounter.id]
        assert tuple(
            link.reference_id for link in encounter.reference_links[: len(old_links)]
        ) == old_links


def test_march_extraction_ii_closes_bounded_library_with_ordered_backlinks() -> None:
    adventure = load_adventure(MARCH_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references) == REFERENCE_IDS
    assert tuple(reference.kind for reference in adventure.references) == (
        *("person",) * 7,
        "object",
        "place",
        "place",
        "place",
        "place",
        "object",
        "place",
        "place",
    )
    assert references[WARRANT_ID].aliases == (
        "Ash Warrant",
        "the Warrant",
        "blackened field plate",
    )
    assert references[VOSSGARD_ID].aliases == ("the fortress", "Voss's fortress")

    forbidden = (
        "currently holds",
        "the demonstration party",
        "Lucan Vey",
        "Tala Marrick",
        "Sorin Halvek",
        "Maelin Rook",
    )
    counts = dict.fromkeys(REFERENCE_IDS, 0)
    for reference in adventure.references:
        text = reference.summary + "\n" + reference.content
        for phrase in forbidden:
            assert phrase not in text
    for encounter in adventure.encounters:
        assert tuple(link.reference_id for link in encounter.reference_links) == EXPECTED_LINKS[
            encounter.id
        ]
        for link in encounter.reference_links:
            counts[link.reference_id] += 1
            assert link.context
    assert counts == EXPECTED_COUNTS
    assert sum(counts.values()) == 68
    assert validate_adventure(adventure).is_valid


def test_march_reference_layer_is_semantically_additive() -> None:
    adventure = load_adventure(MARCH_ROOT / "adventure.json")

    assert _without_reference_layer() == (
        "c8145c2be681482270e725a7edf3033f038d259ec0700b7e2f92842f51b0af8f"
    )
    assert len(adventure.encounters) == 8
    assert len(adventure.revelations) == 12
    assert len(adventure.clues) == 51
    assert validate_adventure(adventure).edge_connectivity == 3


def test_march_reference_views_are_retrievable_and_journal_neutral() -> None:
    adventure = load_adventure(MARCH_ROOT / "adventure.json")
    state = load_play_state(MARCH_ROOT / "play-state.example.json")

    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    for title in (
        "Marshal Aveline Rusk",
        "Brigadier Tamsin Holt",
        "Colonel Dain Merrow",
        "Captain Jessa Vale",
        "Provost Liora Dane",
        "Count Othmar Voss",
        "Dame Kasia Morcant",
        "The Ash Warrant",
        "The Ashen Gate",
        "The Iron Causeway",
        "The Tithe Villages",
        "The Red Abbey",
        "The Black Bell",
        "The Drowned Sluice",
        "Vossgard",
    ):
        assert title in library

    status, _, detail = request_wsgi(author_app, f"/references/{VOSSGARD_ID}")
    assert status == "200 OK"
    assert "The Ashen Gate" in detail
    assert "The Drowned Sluice" in detail
    assert "Vossgard" in detail

    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, body = request_wsgi(
        play_app,
        "/play",
        query=urlencode({"encounter": "vossgard", "reference": WARRANT_ID}),
    )
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{WARRANT_ID}"' in body
    assert "The Ash Warrant" in body
    assert project.snapshot == before


def test_march_packet_adds_reference_views_without_changing_demonstration() -> None:
    adventure = load_adventure(MARCH_ROOT / "adventure.json")
    state_path = MARCH_ROOT / "play-state.example.json"
    state = load_play_state(state_path)
    documents = render_adventure_documents(adventure, validate_adventure(adventure), state)

    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "6674c2ed934de189533d1e0da841c0301f69b310ce8e4e37ea423f6bae0f276a"
    )
    assert len(state.events) == 78
    assert len(documents) == 30
    assert "## People" in documents["references/index.md"]
    assert "## Places" in documents["references/index.md"]
    assert "## Objects" in documents["references/index.md"]
    assert_rendered_documents_match(
        documents, MARCH_ROOT / "generated"
    )


def test_march_voice_iii_repairs_all_seams_without_moving_campaign_state() -> None:
    adventure_path = MARCH_ROOT / "adventure.json"
    state_path = MARCH_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    encounters = adventure.encounter_index()
    references = adventure.reference_index()

    expected_live_phrases = {
        "the-ashen-gate": (
            "Rusk's campaign map is pinned to a hospital trestle",
            "Five lines wait beneath every field act",
        ),
        "the-iron-causeway": (
            "The lead ram stops short of the west gate",
            "a white engineer's scarf from the west gate",
        ),
        "the-tithe-villages": (
            "Three council tables stand at the raised crossroads",
            "Lume's volunteers pull tithe books and collaborator names",
        ),
        "the-thorn-barrows": (
            "Vale's scouts find riderless horses behind three sealed mounds",
            "Morcant begins with roughly ninety night riders",
        ),
        "the-red-abbey": (
            "The ridge road is already moving",
            "which asset to stop, which people to protect",
        ),
        "the-black-bell-redoubt": (
            "The Warrant reaches the redoubt between peals",
            "The Bell coordinates only what still answers it",
        ),
        "the-drowned-sluice": (
            "the lowest flood mark has been scraped away",
            "The route must be taken in order even when the fighting is not",
        ),
        "vossgard": (
            "Vossgard is now a deployment board, not a riddle",
            "Voss reads the same board from inside the keep",
        ),
    }
    for encounter_id, phrases in expected_live_phrases.items():
        for phrase in phrases:
            assert phrase in encounters[encounter_id].content

    retired_static_phrases = {
        "the-ashen-gate": "The Ashen Gate stands upright in empty air",
        "the-iron-causeway": "The Iron Causeway crosses a plain",
        "the-tithe-villages": "Garren, Orra, and Lume stand on the only broad fields",
        "the-thorn-barrows": "The eastern road runs through a chain of burial mounds",
        "the-red-abbey": "The Red Abbey crowns a ridge northwest of Vossgard",
        "the-black-bell-redoubt": "A black iron bell hangs in an open tower",
        "the-drowned-sluice": "The old military canal reaches Vossgard",
        "vossgard": "Vossgard is a fortress, not a riddle",
    }
    for encounter_id, phrase in retired_static_phrases.items():
        assert phrase not in encounters[encounter_id].content

    expected_reference_headings = {
        RUSK_ID: (
            "## Gate ledger: road, beds, wagons, reserve",
            "## Field plate returned with duplicate terms",
            "## Allocate only named strength",
        ),
        HOLT_ID: (
            "## Battalion frontage on the assigned road",
            "## Breach order or interdiction line",
            "## Mark the companies still present",
        ),
        MERROW_ID: (
            "## Span, gallery, lock, pylon, load",
            "## Preserve, disable, or demolish by order",
            "## One Gatewright section cannot serve every axis",
        ),
        VALE_ID: (
            "## Distance written in remounts and hours",
            "## Screen, intercept, report, redeploy",
            "## A courier mark does not close the road",
        ),
        DANE_ID: (
            "## Name the protected people and holding officer",
            "## Guards, transport, record, hearing",
            "## Custody preserves the question",
        ),
        VOSS_ID: (
            "## Seventy-three years of roads under one command",
            "## Withdraw the force that can still obey",
            "## Gate, bell, canal, levy, blood",
        ),
        MORCANT_ID: (
            "## Remount strings behind the next road",
            "## Spend the mound; preserve the riders",
            "## Mark where the mobile force still answers",
        ),
        WARRANT_ID: (
            "## Blackened plate between separated commands",
            "## Unit, enforcing hand, matériel, end, review",
            "## No blank line supplies a missing formation",
        ),
        GATE_ID: (
            "## Pylon light across the inner apron",
            "## One rutted lane, two directions",
            "## Mark strain on the bridgehead board",
        ),
        CAUSEWAY_ID: (
            "## West gate, east gate, span, galleries",
            "## Visible road above, demolition order below",
            "## Record the load path that remains",
        ),
        VILLAGES_ID: (
            "## Garren, Orra, Lume on raised roads",
            "## Grain, labor, levy, blood, household",
            "## Guards and receipts outlast the column",
        ),
        ABBEY_ID: (
            "## Ridge postern, prison yard, vault, nave",
            "## Blood, prisoners, knights on one road",
            "## Consecrate only held ground",
        ),
        BELL_ID: (
            "## Peal, courier, receiver, road",
            "## Programmed dead beneath living command",
            "## Silence, seizure, isolation, contradiction",
        ),
        SLUICE_ID: (
            "## Outer Chain, Sunken Turn, Underkeep Gate",
            "## Chamber order against flood marks",
            "## Crew, protection, sequence, load",
        ),
        VOSSGARD_ID: (
            "## Bell gate, ridge postern, Underkeep Gate",
            "## Every outer position arrives at the wall",
            "## Breach, surrender, prisoners, pursuit, night command",
        ),
    }
    for reference_id, headings in expected_reference_headings.items():
        for heading in headings:
            assert heading in references[reference_id].content

    for reference_id, expected_hash in REFERENCE_BODY_HASHES.items():
        body = "\n".join(
            line
            for line in references[reference_id].content.splitlines()
            if not line.startswith("## ")
        )
        assert hashlib.sha256(body.encode()).hexdigest() == expected_hash

    non_prose = json.loads(adventure_path.read_text(encoding="utf-8"))
    for encounter in non_prose["encounters"]:
        encounter.pop("content", None)
    for reference in non_prose["references"]:
        reference.pop("content", None)
    canonical = json.dumps(
        non_prose,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode()
    assert hashlib.sha256(canonical).hexdigest() == (
        "35e1e6d3c31cac746ecd0063565401e9ef0a6fc240244f54701cbec8db95384b"
    )

    assert sum(len(encounter.content.split()) for encounter in adventure.encounters) == 9013
    assert len(adventure.encounters) == 8
    assert len(adventure.revelations) == 12
    assert len(adventure.clues) == 51
    assert len(adventure.references) == 15
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 68
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "6674c2ed934de189533d1e0da841c0301f69b310ce8e4e37ea423f6bae0f276a"
    )


def test_march_coherence_iii_closes_campaign_without_moving_canonical_state() -> None:
    adventure_path = MARCH_ROOT / "adventure.json"
    state_path = MARCH_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    encounters = adventure.encounter_index()

    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "3b5406ce4792aac9bc8c9dece9ef32772a897eb1668859a82ddf36a13efb71ee"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "6674c2ed934de189533d1e0da841c0301f69b310ce8e4e37ea423f6bae0f276a"
    )
    assert len(state.events) == 78
    assert len(state.active_events) == 76
    assert state.voided_operation_numbers == frozenset({14})

    source_encounters: dict[str, set[str]] = {
        revelation.id: set() for revelation in adventure.revelations
    }
    for clue in adventure.clues:
        source_encounters[clue.revelation_id].add(clue.source_encounter_id)

    assert all(revelation.required for revelation in adventure.revelations)
    for removed_encounter in encounters:
        for revelation in adventure.revelations:
            remaining = source_encounters[revelation.id] - {removed_encounter}
            assert len(remaining) >= 2

    required_procedural_phrases = {
        "the-ashen-gate": (
            "Report remote developments before they take effect",
            "A contained force cannot execute that movement unless it first breaks containment",
            "turn receipt into delivery",
        ),
        "the-iron-causeway": (
            "Winning the visible road does not secure the galleries",
            "### Reduced",
            "### Contained",
            "### Bypassed",
        ),
        "the-black-bell-redoubt": (
            "The Bell coordinates only what still answers it",
            "Reaching the mechanism, cutting couriers, forcing the reserve to deploy, and controlling the roads are separate acts",
            "Do not also grant every other position a full withdrawal",
        ),
        "the-drowned-sluice": (
            "The route must be taken in order even when the fighting is not",
            "The three mechanisms create simultaneous demands",
            "### Block rather than open",
        ),
        "vossgard": (
            "contained forces must break their named interdiction line before they can move",
            "Such a flight becomes a pursuit through the line and carries no organized remnant",
            "It cannot settle permanent sovereignty or grant final amnesty",
        ),
    }
    for encounter_id, phrases in required_procedural_phrases.items():
        for phrase in phrases:
            assert phrase in encounters[encounter_id].content

    reference_text = "\n".join(
        reference.summary + "\n" + reference.content
        for reference in adventure.references
    )
    for demonstrated_state in (
        "Vossgard falls",
        "Holt commands the fortress overnight",
        "Morcant survives with scattered riders",
        "the causeway remains contained",
        "the Red Abbey is reduced",
        "the living garrison stands down",
        "the Outer Chain and Sunken Turn remain uncontrolled",
    ):
        assert demonstrated_state not in reference_text

    consequences = "\n".join(
        event.text
        for event in state.active_events
        if type(event).__name__ == "EncounterConsequenceRecordedEvent"
    )
    assert "containment, not reduction" in consequences
    assert "The Drowned Sluice is deliberately bypassed" in consequences
    assert "the canal is not reduced" in consequences
    assert "Vossgard falls" in consequences


