"""Seven Reeds reference extraction and preservation evidence."""

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

MANDATE_ROOT = Path("examples/the-mandate-of-seven-reeds")
OTOMO_ID = "06b9c081-61b3-494b-a8d9-0c2d9221d44f"
SEPPUN_ID = "0f0f98d1-1df4-4fa9-87ac-7231ddc63339"
MIYA_ID = "cdaf6388-9ed4-4df7-bb8a-218934b414c4"
REI_ID = "d11869d8-5fc7-40a6-b2b6-451ff030d755"
HOJUN_ID = "298bc3fb-a199-4fcd-9b49-36f442507546"
SABURO_ID = "0e8c4594-3da6-403e-b886-424d1e590eb5"
KENTA_ID = "dc9e55ca-3328-4f9e-8881-f5bf9ea5c5d7"

MASUYO_ID = "55bb719c-6a0c-424e-890b-79005dfa32fd"
TADANOBU_ID = "d228eef5-90b5-40f6-bb24-79cea04e1ea5"
ETSUKO_ID = "49ec59bf-90f1-4af7-a386-3dbecfbb4c56"
HARUNORI_ID = "c3e35968-2ca2-4622-9e80-c373cc1d461c"
NAMIKA_ID = "909402eb-2030-4b7c-a0b9-fbca1b296d18"
SACHIKO_ID = "4952957e-5858-4388-8dec-3cc5755e1339"
MASASHIGE_ID = "dda4a93a-90b1-4b8b-9074-afe167442977"
SEVEN_REEDS_ID = "ad3b1038-5dfa-4abf-8948-3c2230654852"
REEDWATER_ID = "985f1d87-52db-4cf3-bc45-4100ec25f524"
BURDEN_LEDGER_ID = "5c6dad77-cabe-4856-9c38-18c8d2399411"
SUBMISSION_REGISTER_ID = "8002df92-4f09-4c39-9a1b-ca8f3654ab24"

MANDATE_REFERENCE_IDS = (
    OTOMO_ID,
    SEPPUN_ID,
    MIYA_ID,
    REI_ID,
    HOJUN_ID,
    SABURO_ID,
    KENTA_ID,
)

MANDATE_ALL_REFERENCE_IDS = MANDATE_REFERENCE_IDS + (
    MASUYO_ID,
    TADANOBU_ID,
    ETSUKO_ID,
    HARUNORI_ID,
    NAMIKA_ID,
    SACHIKO_ID,
    MASASHIGE_ID,
    SEVEN_REEDS_ID,
    REEDWATER_ID,
    BURDEN_LEDGER_ID,
    SUBMISSION_REGISTER_ID,
)

MANDATE_REFERENCE_BODY_HASHES = {
    OTOMO_ID: "5b366a34491728e0510b7622bf2e4c5dcc0e574f7ccf807be99f0cdc86b48c50",
    SEPPUN_ID: "7fd9635566b1ec2106599021aa2e510786d50fbc0f5f30667f892e700357c12b",
    MIYA_ID: "29380d46305a4b55aae5ce53f63dcaa41de7b47bff17e075399358ab4cedf1c8",
    REI_ID: "77aed8ea353c34683d0723b6e15c4919acdee956b02f359e677f067a770d19e0",
    HOJUN_ID: "bf6faad98129649481cf010264e4739b441e9364ae894ee5b7ddac74b457f169",
    SABURO_ID: "a645532e3f9c4a4dd4d7611633407c04afef298e7234e5a849f47d230f104165",
    KENTA_ID: "d1ccbcbf6dc8b4d67f995c9aa8fc4b5071954936a00dff49965d2bceb88e53e3",
    MASUYO_ID: "20cf351e021298e64d851b000a84c3ad8bcfa3ad7f2a77f4b5610da2c287b5cd",
    TADANOBU_ID: "35a3a94c94d008d7f93e622775deef0b289b76776bad25c556116dbb52aa8ca5",
    ETSUKO_ID: "01de28d6ea692e258e0d1f3b509e48c77cbcc2b00473eda9d18497f1bf4d3de3",
    HARUNORI_ID: "fa8944f17eccfa303ec2d91158e62e6df85bafd81c64c882c5cb1e206e11961d",
    NAMIKA_ID: "cc5c3231861e2b203f1e046024a46b46d60462b2411b44e96dc4ca58abf1d111",
    SACHIKO_ID: "2e278e4faa66ba09d288dd85f9d26387f72324353e6d1cc64a20439b4369346e",
    MASASHIGE_ID: "23dc3a83082d4d60afb142725719eadcf0dcb1a0ef401369e492a9f862edc810",
    SEVEN_REEDS_ID: "a8b1b36405868434042f23d0adc47758e56fbfa2f948845269c2949256642813",
    REEDWATER_ID: "df81f9cd99318b15ee6817100960449d02c8f056b8db5becfe14a4c48547a027",
    BURDEN_LEDGER_ID: "f2ed4d1c92e492ebed99e3e587f3ac022e60946c17c4570a553bf8671a02374d",
    SUBMISSION_REGISTER_ID: "446feda6441d4f46b39ec322a1a8918aeb474ec249116c64dd2b38ee151d155f",
}

MANDATE_REFERENCE_LINK_COUNTS = {
    OTOMO_ID: 5,
    SEPPUN_ID: 6,
    MIYA_ID: 6,
    REI_ID: 6,
    HOJUN_ID: 7,
    SABURO_ID: 6,
    KENTA_ID: 6,
}
MANDATE_ENCOUNTER_REFERENCE_IDS = {
    "hall-of-the-chrysanthemum-throne": (OTOMO_ID, SEPPUN_ID, MIYA_ID),
    "ministry-of-divided-ink": (OTOMO_ID,),
    "garden-of-white-gravel": (SEPPUN_ID,),
    "hall-of-open-roads": (MIYA_ID, REI_ID, HOJUN_ID, SABURO_ID, KENTA_ID),
    "pavilion-of-first-rain": (),
    "hall-of-red-standards": (SEPPUN_ID,),
    "shrine-of-listening-water": (HOJUN_ID,),
    "stone-and-moss-court": (KENTA_ID,),
    "theater-of-a-thousand-sleeves": (),
    "courtyard-of-bells": (SABURO_ID,),
    "hall-of-joined-timbers": (REI_ID, HOJUN_ID),
    "guesthouse-of-the-bent-reed": (MIYA_ID, REI_ID, HOJUN_ID, SABURO_ID, KENTA_ID),
    "evening-of-the-chrysanthemum-moon": (
        MIYA_ID,
        SEPPUN_ID,
        OTOMO_ID,
        REI_ID,
        HOJUN_ID,
        SABURO_ID,
        KENTA_ID,
    ),
    "chamber-of-seven-reeds": (
        OTOMO_ID,
        MIYA_ID,
        SEPPUN_ID,
        REI_ID,
        HOJUN_ID,
        SABURO_ID,
        KENTA_ID,
    ),
    "the-second-audience": (
        OTOMO_ID,
        SEPPUN_ID,
        MIYA_ID,
        REI_ID,
        HOJUN_ID,
        SABURO_ID,
        KENTA_ID,
    ),
}

MANDATE_COMPLETE_ENCOUNTER_REFERENCE_IDS = {
    "hall-of-the-chrysanthemum-throne": (
        OTOMO_ID,
        SEPPUN_ID,
        MIYA_ID,
        SEVEN_REEDS_ID,
        REEDWATER_ID,
        MASUYO_ID,
        TADANOBU_ID,
        ETSUKO_ID,
        HARUNORI_ID,
        NAMIKA_ID,
        SACHIKO_ID,
        MASASHIGE_ID,
    ),
    "ministry-of-divided-ink": (OTOMO_ID, SEVEN_REEDS_ID),
    "garden-of-white-gravel": (SEPPUN_ID, SUBMISSION_REGISTER_ID),
    "hall-of-open-roads": (
        MIYA_ID,
        REI_ID,
        HOJUN_ID,
        SABURO_ID,
        KENTA_ID,
        SEVEN_REEDS_ID,
        REEDWATER_ID,
        BURDEN_LEDGER_ID,
    ),
    "pavilion-of-first-rain": (MASUYO_ID, REEDWATER_ID),
    "hall-of-red-standards": (
        SEPPUN_ID,
        TADANOBU_ID,
        MASUYO_ID,
        SUBMISSION_REGISTER_ID,
    ),
    "shrine-of-listening-water": (
        HOJUN_ID,
        ETSUKO_ID,
        HARUNORI_ID,
        MASASHIGE_ID,
        REEDWATER_ID,
    ),
    "stone-and-moss-court": (KENTA_ID, HARUNORI_ID, NAMIKA_ID),
    "theater-of-a-thousand-sleeves": (NAMIKA_ID, HARUNORI_ID),
    "courtyard-of-bells": (SABURO_ID, SACHIKO_ID, REEDWATER_ID),
    "hall-of-joined-timbers": (
        REI_ID,
        HOJUN_ID,
        MASASHIGE_ID,
        TADANOBU_ID,
        HARUNORI_ID,
        NAMIKA_ID,
        REEDWATER_ID,
        BURDEN_LEDGER_ID,
    ),
    "guesthouse-of-the-bent-reed": (
        MIYA_ID,
        REI_ID,
        HOJUN_ID,
        SABURO_ID,
        KENTA_ID,
        SACHIKO_ID,
        REEDWATER_ID,
        BURDEN_LEDGER_ID,
    ),
    "evening-of-the-chrysanthemum-moon": (
        MIYA_ID,
        SEPPUN_ID,
        OTOMO_ID,
        REI_ID,
        HOJUN_ID,
        SABURO_ID,
        KENTA_ID,
        MASUYO_ID,
        TADANOBU_ID,
        ETSUKO_ID,
        HARUNORI_ID,
        NAMIKA_ID,
        SACHIKO_ID,
        MASASHIGE_ID,
        REEDWATER_ID,
        BURDEN_LEDGER_ID,
        SUBMISSION_REGISTER_ID,
    ),
    "chamber-of-seven-reeds": (
        OTOMO_ID,
        MIYA_ID,
        SEPPUN_ID,
        REI_ID,
        HOJUN_ID,
        SABURO_ID,
        KENTA_ID,
        SEVEN_REEDS_ID,
        MASUYO_ID,
        TADANOBU_ID,
        ETSUKO_ID,
        HARUNORI_ID,
        NAMIKA_ID,
        SACHIKO_ID,
        MASASHIGE_ID,
        REEDWATER_ID,
        BURDEN_LEDGER_ID,
        SUBMISSION_REGISTER_ID,
    ),
    "the-second-audience": (
        OTOMO_ID,
        SEPPUN_ID,
        MIYA_ID,
        REI_ID,
        HOJUN_ID,
        SABURO_ID,
        KENTA_ID,
        SEVEN_REEDS_ID,
        MASUYO_ID,
        TADANOBU_ID,
        ETSUKO_ID,
        HARUNORI_ID,
        NAMIKA_ID,
        SACHIKO_ID,
        MASASHIGE_ID,
        REEDWATER_ID,
        BURDEN_LEDGER_ID,
        SUBMISSION_REGISTER_ID,
    ),
}


def _without_reference_layer() -> str:
    payload = json.loads((MANDATE_ROOT / "adventure.json").read_text(encoding="utf-8"))
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


def test_seven_reeds_extraction_i_records_remain_unchanged_as_prefix() -> None:
    adventure = load_adventure(MANDATE_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references[:7]) == MANDATE_REFERENCE_IDS
    assert tuple(reference.kind for reference in adventure.references[:7]) == ("person",) * 7
    assert references[OTOMO_ID].aliases == ("Kazetada", "Senior Minister Otomo Kazetada")
    assert references[SEPPUN_ID].aliases == ("Tomoe", "Commander Seppun Tomoe")
    assert references[MIYA_ID].aliases == ("Shun", "Herald Miya Shun")
    assert references[REI_ID].aliases == ("Rei", "Headwoman Rei")
    assert references[HOJUN_ID].aliases == ("Hojun", "Keeper Hojun")
    assert references[SABURO_ID].aliases == ("Saburo", "Master Saburo")
    assert references[KENTA_ID].aliases == ("Kenta", "Natsugawa")

    forbidden = (
        "Hundred-Day Brace",
        "current draft",
        "current coalition",
        "current assent",
        "final Mandate",
        "the Emperor adopts",
        "the Emperor rejects",
        "the Witnesses choose",
        "currently holds",
        "current titleholder",
        "current executor",
    )
    for reference in adventure.references:
        text = reference.summary + "\n" + reference.content
        for phrase in forbidden:
            assert phrase not in text

    actual_link_counts = dict.fromkeys(MANDATE_REFERENCE_IDS, 0)
    for encounter in adventure.encounters:
        expected_prefix = MANDATE_ENCOUNTER_REFERENCE_IDS[encounter.id]
        assert tuple(link.reference_id for link in encounter.reference_links[: len(expected_prefix)]) == expected_prefix
        for link in encounter.reference_links:
            if link.reference_id in actual_link_counts:
                actual_link_counts[link.reference_id] += 1
            assert link.context
    assert actual_link_counts == MANDATE_REFERENCE_LINK_COUNTS
    assert sum(actual_link_counts.values()) == 42
    assert validate_adventure(adventure).is_valid


def test_seven_reeds_reference_layer_is_semantically_additive() -> None:
    adventure = load_adventure(MANDATE_ROOT / "adventure.json")

    assert _without_reference_layer() == (
        "bd58eaa995e72dd66e102d1b5d5608cdaa9e96d84f52b6726e79b68820ecc5a3"
    )
    assert len(adventure.encounters) == 15
    assert len(adventure.revelations) == 44
    assert len(adventure.clues) == 221
    assert validate_adventure(adventure).edge_connectivity == 4


def test_seven_reeds_reference_views_are_retrievable_and_journal_neutral() -> None:
    adventure = load_adventure(MANDATE_ROOT / "adventure.json")
    state = load_play_state(MANDATE_ROOT / "play-state.example.json")

    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    for title in (
        "Otomo Kazetada",
        "Seppun Tomoe",
        "Miya Shun",
        "Rei of Reed Bank",
        "Brother Hojun",
        "Saburo of the Three Crossings",
        "Natsugawa Kenta",
    ):
        assert title in library

    status, _, detail = request_wsgi(author_app, f"/references/{MIYA_ID}")
    assert status == "200 OK"
    assert "Hall of Open Roads" in detail
    assert "The Second Audience" in detail

    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, body = request_wsgi(
        play_app,
        "/play",
        query=urlencode(
            {
                "encounter": "guesthouse-of-the-bent-reed",
                "reference": HOJUN_ID,
            }
        ),
    )
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{HOJUN_ID}"' in body
    assert "Brother Hojun" in body
    assert project.snapshot == before


def test_seven_reeds_packet_adds_reference_views_without_changing_demonstration() -> None:
    adventure = load_adventure(MANDATE_ROOT / "adventure.json")
    state_path = MANDATE_ROOT / "play-state.example.json"
    state = load_play_state(state_path)
    documents = render_adventure_documents(
        adventure,
        validate_adventure(adventure),
        state,
    )

    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "382e684e3e865b63148844d29a6846e2f890fa54ab7d1ca46d6a86bdf98f4a96"
    )
    assert len(state.events) == 288
    assert len(state.active_events) == 286
    assert len(documents) == 40
    assert "## People" in documents["references/index.md"]
    for reference_id in MANDATE_ALL_REFERENCE_IDS:
        sheet_name = f"references/{reference_id}.md"
        assert documents[sheet_name] == (
            MANDATE_ROOT / "generated" / sheet_name
        ).read_text(encoding="utf-8")
    for encounter in adventure.encounters:
        sheet_name = f"encounters/{encounter.id}.md"
        assert documents[sheet_name] == (
            MANDATE_ROOT / "generated" / sheet_name
        ).read_text(encoding="utf-8")


def test_seven_reeds_extraction_ii_planned_closed_library() -> None:
    adventure = load_adventure(MANDATE_ROOT / "adventure.json")

    expected = {
        "06b9c081-61b3-494b-a8d9-0c2d9221d44f": ("Otomo Kazetada", "person", 5),
        "0f0f98d1-1df4-4fa9-87ac-7231ddc63339": ("Seppun Tomoe", "person", 6),
        "cdaf6388-9ed4-4df7-bb8a-218934b414c4": ("Miya Shun", "person", 6),
        "d11869d8-5fc7-40a6-b2b6-451ff030d755": ("Rei of Reed Bank", "person", 6),
        "298bc3fb-a199-4fcd-9b49-36f442507546": ("Brother Hojun", "person", 7),
        "0e8c4594-3da6-403e-b886-424d1e590eb5": ("Saburo of the Three Crossings", "person", 6),
        "dc9e55ca-3328-4f9e-8881-f5bf9ea5c5d7": ("Natsugawa Kenta", "person", 6),
        "55bb719c-6a0c-424e-890b-79005dfa32fd": ("Doji Masuyo", "person", 6),
        "d228eef5-90b5-40f6-bb24-79cea04e1ea5": ("Akodo Tadanobu", "person", 6),
        "49ec59bf-90f1-4af7-a386-3dbecfbb4c56": ("Isawa Etsuko", "person", 5),
        "c3e35968-2ca2-4622-9e80-c373cc1d461c": ("Kitsuki Harunori", "person", 8),
        "909402eb-2030-4b7c-a0b9-fbca1b296d18": ("Bayushi Namika", "person", 7),
        "4952957e-5858-4388-8dec-3cc5755e1339": ("Ide Sachiko", "person", 6),
        "dda4a93a-90b1-4b8b-9074-afe167442977": ("Kaiu Masashige", "person", 6),
        "ad3b1038-5dfa-4abf-8948-3c2230654852": ("The Seven Reeds", "other", 5),
        "985f1d87-52db-4cf3-bc45-4100ec25f524": ("Reedwater Province", "place", 10),
        "5c6dad77-cabe-4856-9c38-18c8d2399411": ("The Cumulative Burden Ledger", "object", 6),
        "8002df92-4f09-4c39-9a1b-ca8f3654ab24": ("The Submission Register", "object", 5),
    }

    assert len(adventure.references) == 18
    actual = {reference.id: (reference.title, reference.kind) for reference in adventure.references}
    assert actual == {key: value[:2] for key, value in expected.items()}

    counts = dict.fromkeys(expected, 0)
    for encounter in adventure.encounters:
        assert tuple(link.reference_id for link in encounter.reference_links) == (
            MANDATE_COMPLETE_ENCOUNTER_REFERENCE_IDS[encounter.id]
        )
        for link in encounter.reference_links:
            counts[link.reference_id] += 1
            assert link.context
    assert counts == {key: value[2] for key, value in expected.items()}
    assert sum(counts.values()) == 112


def test_seven_reeds_voice_iii_repairs_seams_without_moving_court_state() -> None:
    adventure_path = MANDATE_ROOT / "adventure.json"
    state_path = MANDATE_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    encounters = adventure.encounter_index()
    references = adventure.reference_index()

    expected_live_phrases = {
        "hall-of-the-chrysanthemum-throne": (
            "The senior delegates do not repeat their credentials.",
            "Their questions do not compete for a Reed",
        ),
        "ministry-of-divided-ink": (
            "Kazetada lays one Reed tablet across four slips of paper",
            "The flood has already supplied his objection",
        ),
        "garden-of-white-gravel": (
            "Tomoe has placed a covered Lion spearhead",
            "The object moves only when they name the receiving officer",
        ),
        "hall-of-open-roads": (
            "On it lie a rain-stiff proclamation",
            "who may amend it, how the village learns of the change",
        ),
        "guesthouse-of-the-bent-reed": (
            "Rei lays duty sticks across the mat",
            "Hojun lays two bell clappers beside a household calendar",
            "Saburo empties requisition receipts onto the mat",
            "Kenta places three surviving copies of the lost Natsugawa archive",
        ),
    }
    for encounter_id, phrases in expected_live_phrases.items():
        for phrase in phrases:
            assert phrase in encounters[encounter_id].content

    retired_static_phrases = {
        "hall-of-the-chrysanthemum-throne": "The senior delegates state their claims",
        "ministry-of-divided-ink": "Kazetada is a senior Otomo minister",
        "garden-of-white-gravel": "Tomoe commands part of the palace guard",
        "hall-of-open-roads": "Shun is a senior herald and cousin",
        "guesthouse-of-the-bent-reed": "Rei is the headwoman of a large farming village",
    }
    for encounter_id, phrase in retired_static_phrases.items():
        assert phrase not in encounters[encounter_id].content

    expected_reference_headings = {
        OTOMO_ID: ("## One tablet, four authorities", "## Review written in Imperial ink"),
        SEPPUN_ID: ("## A standard lowered into a named hand", "## The field order behind the bow"),
        MIYA_ID: ("## Read it at the drowned gate", "## Date, courier, recipient, correction"),
        REI_ID: ("## Subtract every burden already borne", "## Land, water, seed, graves, date"),
        HOJUN_ID: ("## Bell, keeper, calendar, household", "## Necessity leaves a restoration debt"),
        SABURO_ID: ("## Receipt, condition, debtor, due date", "## Open road, bounded taking"),
        KENTA_ID: ("## The seal after imported banners depart", "## Successor, clerk, store, horse, pay"),
        MASUYO_ID: ("## White cord through granary, barge, and household", "## Seed keys outside the sword hand"),
        TADANOBU_ID: ("## One command, one named superior, one end", "## Standard, roster, recipient, effective hour"),
        ETSUKO_ID: ("## Name the keeper behind the sacred claim", "## Notice, speaker, deadline, bypass"),
        HARUNORI_ID: ("## Set the conflicting records side by side", "## Recuse to a named substitute"),
        NAMIKA_ID: ("## Access, preservation, report, restraint, review, sanction", "## Seal the source; test the substance"),
        SACHIKO_ID: ("## One dispatch law from station to station", "## Condition, valuation, debtor, repayment"),
        MASASHIGE_ID: ("## Draw the load through every office", "## Record who chose the sacrifice"),
        SEVEN_REEDS_ID: ("## Seven tablets, seven domains", "## A constitutional grammar awaiting names"),
        REEDWATER_ID: ("## The flood killed the lawful joints", "## District voices, no single provincial mouth"),
        BURDEN_LEDGER_ID: ("## Count the household once across seven demands", "## The total changes only through live entries"),
        SUBMISSION_REGISTER_ID: ("## Enter the act, not the symbol alone", "## Receipt does not prove performance"),
    }
    for reference_id, headings in expected_reference_headings.items():
        for heading in headings:
            assert heading in references[reference_id].content

    for reference_id, expected_hash in MANDATE_REFERENCE_BODY_HASHES.items():
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
        "462442544be7b2a6b62741fea3af0661024946e8465ad0389c52ca3e6879cdcf"
    )

    assert sum(len(encounter.content.split()) for encounter in adventure.encounters) == 28326
    assert len(adventure.encounters) == 15
    assert len(adventure.revelations) == 44
    assert len(adventure.clues) == 221
    assert len(adventure.references) == 18
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 112
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "382e684e3e865b63148844d29a6846e2f890fa54ab7d1ca46d6a86bdf98f4a96"
    )


def test_seven_reeds_coherence_iii_closes_the_library_without_moving_court_state() -> None:
    adventure_path = MANDATE_ROOT / "adventure.json"
    state_path = MANDATE_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    encounters = adventure.encounter_index()
    references = adventure.reference_index()
    report = validate_adventure(adventure)

    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "3b7f6608505a95c262b81f80647dfc228a797623146d58156356a0ec6fa3c739"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "382e684e3e865b63148844d29a6846e2f890fa54ab7d1ca46d6a86bdf98f4a96"
    )
    assert report.is_valid
    assert report.edge_connectivity == 4
    assert len(adventure.encounters) == 15
    assert len(adventure.revelations) == 44
    assert len(adventure.clues) == 221
    assert len(adventure.references) == 18
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 112
    assert len(state.events) == 288
    assert len(state.active_events) == 286

    source_encounters_by_revelation = {
        revelation.id: {
            clue.source_encounter_id
            for clue in adventure.clues
            if clue.revelation_id == revelation.id
        }
        for revelation in adventure.revelations
    }
    institutional_lane = {
        "hall-of-the-chrysanthemum-throne": "imperial-opening",
        "ministry-of-divided-ink": "otomo-review",
        "garden-of-white-gravel": "seppun-command",
        "hall-of-open-roads": "miya-transmission",
        "pavilion-of-first-rain": "crane-proceeding",
        "hall-of-red-standards": "lion-proceeding",
        "shrine-of-listening-water": "phoenix-proceeding",
        "stone-and-moss-court": "dragon-proceeding",
        "theater-of-a-thousand-sleeves": "scorpion-proceeding",
        "courtyard-of-bells": "unicorn-proceeding",
        "hall-of-joined-timbers": "crab-proceeding",
        "guesthouse-of-the-bent-reed": "reedwater-witnesses",
        "evening-of-the-chrysanthemum-moon": "optional-public-obligation",
        "chamber-of-seven-reeds": "drafting",
        "the-second-audience": "imperial-judgment",
    }
    clan_proceedings = {
        "pavilion-of-first-rain",
        "hall-of-red-standards",
        "shrine-of-listening-water",
        "stone-and-moss-court",
        "theater-of-a-thousand-sleeves",
        "courtyard-of-bells",
        "hall-of-joined-timbers",
    }
    for removed_encounter_id in clan_proceedings:
        for revelation in adventure.revelations:
            if not revelation.required:
                continue
            surviving_sources = source_encounters_by_revelation[revelation.id] - {
                removed_encounter_id
            }
            assert len(surviving_sources) >= 2
            assert len({institutional_lane[source] for source in surviving_sources}) >= 2

    for revelation in adventure.revelations:
        if revelation.required:
            assert len(
                source_encounters_by_revelation[revelation.id]
                - {"evening-of-the-chrysanthemum-moon"}
            ) >= 3

    reference_ids = set(references)
    assert all(clue.source_encounter_id not in reference_ids for clue in adventure.clues)
    assert all(revelation.unlocks_encounter_id not in reference_ids for revelation in adventure.revelations)

    moon = encounters["evening-of-the-chrysanthemum-moon"].content
    chamber = encounters["chamber-of-seven-reeds"].content
    audience = encounters["the-second-audience"].content
    assert "The evening cannot enact a clause" in moon
    assert "That visibility is not permanent allegiance" in moon
    assert "## Five documents, one chain of provincial command" in chamber
    assert "## Amendment discipline" in chamber
    assert "## Two executable provincial governments" in chamber
    assert "Clan approval matters as evidence of implementation, not as a vote" in audience
    assert "He may also reject the premise that either draft exhausts his choices" in audience
    assert "The Emperor may reject the primary, choose the fallback" in audience

    burden_ledger = references[BURDEN_LEDGER_ID].content
    submission_register = references[SUBMISSION_REGISTER_ID].content
    for phrase in (
        "prior service",
        "planting and seasonal timing",
        "displacement",
        "compensation",
        "duplicate calls",
        "material diversion",
        "successor promised without staff",
        "sacrifice the court chooses to compel",
    ):
        assert phrase in burden_ledger
    for phrase in (
        "Lowered standards",
        "displayed keys",
        "opened ledgers",
        "surrendered seals",
        "receiving officer",
        "effective time",
        "acknowledgment route",
        "recipient is absent, refuses, cannot perform",
        "transfer is incomplete",
        "Receipt does not prove performance",
    ):
        assert phrase in submission_register

    documents = render_adventure_documents(adventure, report, state)
    assert len(documents) == 40
    assert len([name for name in documents if name.startswith("encounters/")]) == 15
    assert len([name for name in documents if name.startswith("references/")]) == 19
    assert_rendered_documents_match(
        documents, MANDATE_ROOT / "generated"
    )


