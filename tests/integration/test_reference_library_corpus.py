"""Corpus evidence for selective adventure reference-library use."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.web import build_authoring_app, build_play_app, request_wsgi

pytestmark = pytest.mark.corpus

HARROWGATE_ROOT = Path("examples/the-bell-beneath-harrowgate")
CAULDRON_ROOT = Path("examples/the-cauldron-of-nine-silences")
SWINE_ROOT = Path("examples/when-the-swine-kneel")

SALT_WARDENS_ID = "7d10d123-1d6b-4b7f-b09b-ac6d976a98f4"
LADY_VEY_ID = "70f54526-9ee3-4fbd-97e4-ba7b1393fdd6"
MAELIN_ROOK_ID = "70dbadad-c4c0-459a-8df6-1bc5417bbb0d"
ORREN_SAYE_ID = "ddb3c840-1e11-4f47-b790-8dc67ec28dc7"
PELL_VARO_ID = "0e3023d6-2580-41fb-bd67-6bfe72480d77"
QUEEN_AVARRA_ID = "7450c8fa-6633-4b79-a24d-1f4b639ae2dc"

CHIEF_FACTOR_COSS_ID = "c776856e-eea8-4a35-b64d-789cf16a8086"
SAMET_RHUN_ID = "9c2e68e3-bf5b-4d1a-8388-2527775e95fa"
ARDEL_QUOIN_ID = "6bb941f4-f47d-44f5-9427-a2d03b8cb931"
ODRAN_GREVE_ID = "eba87b8e-8c93-4624-bdde-f0fd3ae282bc"
TAVIA_HEST_ID = "b91c3329-612c-4320-98aa-37f7a40d81cc"
RHEA_COLM_ID = "ca9adfa1-d0d7-465b-91c7-dcf0cdd67742"
NARA_ID = "b365284a-6604-45d3-9305-997ad660f7ad"
EMBER_COMPANY_ID = "0ee5aa87-9379-4170-afd6-97de3c5badd6"
LOW_CHOIR_ID = "05588cfb-6f87-4072-a6e0-44523968d7c4"
CHAIN_SCRIPTORIUM_ID = "8e4c88cb-067e-4701-9364-7c61e104a710"
FEAST_ID = "eb5bc5a6-28dd-43db-a2f0-a4b5e13e6206"
KINGS_GRAVE_ID = "2f1ca17b-5166-4598-be11-617cd4cdcaff"
COUNTERWEIGHT_WELLS_ID = "adcf2968-b7f4-45fa-85e1-7da7118b404e"
DEEP_BELL_ID = "4b3bdda6-6e52-4409-bfe7-fb9c7d53e0db"
MOUTH_BELOW_ID = "05e3da93-ea8c-4cb4-a611-19a8c9612a4c"
CROWN_OF_MEASURE_ID = "eeae1101-1cb5-471f-92d8-eb27757ca095"
COMMON_MEASURE_ID = "ca76d25a-8e6f-40e0-9cc5-96ab287f0bc1"

GWYNE_MARR_ID = "08a5bb82-4600-4c11-832f-6b67ae17ca04"
LORD_MAEL_TARAN_ID = "c9a4c98c-ba0b-43e5-8c0d-9f111b757c91"
KING_BRANOC_ID = "02aca2e8-7cb6-42f7-8365-1e06e245d790"
LADY_ADERYN_TARAN_ID = "416e34bd-4b3a-4fd8-b08f-e07b6c92bfe0"
BROTHER_CADDOC_ID = "1be57339-886c-4e53-83cc-bde88fac7421"
EDRIC_TARAN_ID = "63306f5c-35d7-41d0-a904-86838922f507"
CAPTAIN_RHOD_VANE_ID = "8a6dd529-71e1-49b7-a962-7c5bfc0ee131"
MOTHER_ELUNED_ID = "49140281-8273-4d4d-8272-b1f0a769aec3"
TOMAS_WREN_ID = "722a7e08-d425-43b3-acbc-a9d002d90929"
MARSHAL_HEW_PALE_ID = "5721becd-9641-4b74-a3f8-dd9ecbb0c9ac"
NESSA_PIKE_ID = "7752c66e-eaec-4ef4-93e9-517c428beca2"
EFA_RILL_ID = "06e96b1a-a1e4-4f3a-9432-7c6eb1412e95"
GREEN_LARKS_ID = "b002fc7a-db5f-4ac1-9f6d-343357c2d956"
NINE_HEARTH_TRUST_ID = "0d9aca64-f4d8-4b8d-a3c1-959307d7159e"
CAULDRON_OF_NINE_SILENCES_ID = "2c44f943-72c8-464a-bac2-7cb5f0c60c27"
BRANOC_OATH_RING_ID = "5853b0fa-8880-4f6c-b73f-690ae6929cfa"
GATE_COMPACT_ID = "8cf58ff7-1439-4292-adfd-44715acb99f9"
FULL_ASKING_ID = "ea9eab0a-65ee-461c-8f64-87ced3c2ee47"
GREAT_MUSTER_ID = "dd8d50e6-df51-48db-b98c-cc2a6eb27731"

CAULDRON_PRIMARY_REFERENCE_IDS = (
    GWYNE_MARR_ID,
    LORD_MAEL_TARAN_ID,
    KING_BRANOC_ID,
    LADY_ADERYN_TARAN_ID,
    BROTHER_CADDOC_ID,
    EDRIC_TARAN_ID,
)

CAULDRON_EXTRACTION_II_REFERENCE_IDS = (
    CAPTAIN_RHOD_VANE_ID,
    MOTHER_ELUNED_ID,
    TOMAS_WREN_ID,
    MARSHAL_HEW_PALE_ID,
    NESSA_PIKE_ID,
    EFA_RILL_ID,
    GREEN_LARKS_ID,
    NINE_HEARTH_TRUST_ID,
    CAULDRON_OF_NINE_SILENCES_ID,
    BRANOC_OATH_RING_ID,
    GATE_COMPACT_ID,
    FULL_ASKING_ID,
    GREAT_MUSTER_ID,
)

CAULDRON_REFERENCE_IDS = (
    *CAULDRON_PRIMARY_REFERENCE_IDS,
    *CAULDRON_EXTRACTION_II_REFERENCE_IDS,
)

CAULDRON_REFERENCE_LINK_COUNTS = {
    GWYNE_MARR_ID: 7,
    LORD_MAEL_TARAN_ID: 9,
    KING_BRANOC_ID: 7,
    LADY_ADERYN_TARAN_ID: 8,
    BROTHER_CADDOC_ID: 8,
    EDRIC_TARAN_ID: 7,
    CAPTAIN_RHOD_VANE_ID: 8,
    MOTHER_ELUNED_ID: 4,
    TOMAS_WREN_ID: 6,
    MARSHAL_HEW_PALE_ID: 4,
    NESSA_PIKE_ID: 3,
    EFA_RILL_ID: 5,
    GREEN_LARKS_ID: 6,
    NINE_HEARTH_TRUST_ID: 5,
    CAULDRON_OF_NINE_SILENCES_ID: 10,
    BRANOC_OATH_RING_ID: 10,
    GATE_COMPACT_ID: 6,
    FULL_ASKING_ID: 8,
    GREAT_MUSTER_ID: 6,
}

CAULDRON_ENCOUNTER_REFERENCE_LINK_COUNTS = {
    "crooked-magpie": 16,
    "white-hart-court": 15,
    "smoke-kitchens": 9,
    "rookwalk": 8,
    "chapel-last-word": 13,
    "widows-solar": 11,
    "barrow-stair": 12,
    "house-borrowed-voices": 9,
    "cauldron-vault": 18,
    "reed-weir": 16,
}

HARROWGATE_REFERENCE_IDS = (
    SALT_WARDENS_ID,
    LADY_VEY_ID,
    MAELIN_ROOK_ID,
    ORREN_SAYE_ID,
    PELL_VARO_ID,
    QUEEN_AVARRA_ID,
    CHIEF_FACTOR_COSS_ID,
    SAMET_RHUN_ID,
    ARDEL_QUOIN_ID,
    ODRAN_GREVE_ID,
    TAVIA_HEST_ID,
    RHEA_COLM_ID,
    NARA_ID,
    EMBER_COMPANY_ID,
    LOW_CHOIR_ID,
    CHAIN_SCRIPTORIUM_ID,
    FEAST_ID,
    KINGS_GRAVE_ID,
    COUNTERWEIGHT_WELLS_ID,
    DEEP_BELL_ID,
    MOUTH_BELOW_ID,
    CROWN_OF_MEASURE_ID,
    COMMON_MEASURE_ID,
)

HARROWGATE_REFERENCE_LINK_COUNTS = {
    SALT_WARDENS_ID: 8,
    LADY_VEY_ID: 9,
    MAELIN_ROOK_ID: 5,
    ORREN_SAYE_ID: 10,
    PELL_VARO_ID: 7,
    QUEEN_AVARRA_ID: 8,
    CHIEF_FACTOR_COSS_ID: 4,
    SAMET_RHUN_ID: 4,
    ARDEL_QUOIN_ID: 5,
    ODRAN_GREVE_ID: 5,
    TAVIA_HEST_ID: 3,
    RHEA_COLM_ID: 5,
    NARA_ID: 5,
    EMBER_COMPANY_ID: 10,
    LOW_CHOIR_ID: 13,
    CHAIN_SCRIPTORIUM_ID: 5,
    FEAST_ID: 5,
    KINGS_GRAVE_ID: 7,
    COUNTERWEIGHT_WELLS_ID: 8,
    DEEP_BELL_ID: 12,
    MOUTH_BELOW_ID: 5,
    CROWN_OF_MEASURE_ID: 9,
    COMMON_MEASURE_ID: 8,
}


def test_harrowgate_retains_primary_people_and_cross_dungeon_wardens() -> None:
    adventure = load_adventure(HARROWGATE_ROOT / "adventure.json")
    state = load_play_state(HARROWGATE_ROOT / "play-state.example.json")
    references = adventure.reference_index()

    expected_ids = HARROWGATE_REFERENCE_IDS
    assert tuple(item.id for item in adventure.references) == expected_ids
    assert references[SALT_WARDENS_ID].kind == "organization"
    assert references[SALT_WARDENS_ID].aliases == (
        "Harrowgate Wardens",
        "the Wardens",
    )
    assert references[LADY_VEY_ID].aliases == ("Lady Vey", "Merrow Vey")
    assert references[MAELIN_ROOK_ID].aliases == (
        "Maelin Rook",
        "Captain Rook",
        "Rook",
    )
    assert references[PELL_VARO_ID].aliases == ("Pell Varo", "Engineer Varo")
    assert references[NARA_ID].kind == "person"
    assert references[NARA_ID].aliases == ("Nara Vale", "Nara")
    assert references[EMBER_COMPANY_ID].kind == "organization"
    assert references[CHAIN_SCRIPTORIUM_ID].kind == "place"
    assert references[CROWN_OF_MEASURE_ID].kind == "object"
    assert references[COMMON_MEASURE_ID].kind == "object"
    assert "seven names" in references[NARA_ID].summary
    assert "does not answer questions" in references[CHAIN_SCRIPTORIUM_ID].content.lower()

    expected_link_counts = HARROWGATE_REFERENCE_LINK_COUNTS
    actual_link_counts = dict.fromkeys(expected_ids, 0)
    for encounter in adventure.encounters:
        for link in encounter.reference_links:
            actual_link_counts[link.reference_id] += 1
    assert actual_link_counts == expected_link_counts

    linked_encounters = tuple(
        encounter.id
        for encounter in adventure.encounters
        if any(link.reference_id == SALT_WARDENS_ID for link in encounter.reference_links)
    )
    assert linked_encounters == (
        "hall-of-bent-knees",
        "salt-barracks",
        "inverted-chapel",
        "counterweight-wells",
        "choir-of-iron-tongues",
        "black-rain-cistern",
        "deep-bell",
        "mouth-below",
    )

    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    assert library.index("The Salt Wardens") < library.index("Lady Merrow Vey")
    assert library.index("Lady Merrow Vey") < library.index("Captain Maelin Rook")
    assert "Nara-of-the-Seventh-Name" in library
    assert "The Chain Scriptorium" in library
    assert "The Crown of Measure" in library
    status, _, detail = request_wsgi(author_app, f"/references/{QUEEN_AVARRA_ID}")
    assert status == "200 OK"
    assert "Avarra does not survive as one complete person" in detail
    assert "The Mouth Below" in detail

    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, play = request_wsgi(
        play_app,
        "/play",
        query=urlencode(
            {
                "encounter": "counterweight-wells",
                "reference": MAELIN_ROOK_ID,
            }
        ),
    )
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{MAELIN_ROOK_ID}"' in play
    assert "holds the Civic-Funerary platform" in play
    assert "captain rook" in play
    assert 'data-play-pin-kind="reference"' in play
    assert project.snapshot == before

    documents = render_adventure_documents(adventure, validate_adventure(adventure))
    assert "references/index.md" in documents
    assert "## People" in documents["references/index.md"]
    assert "## Organizations" in documents["references/index.md"]
    assert "## Places" in documents["references/index.md"]
    assert "## Objects" in documents["references/index.md"]
    for reference_id in expected_ids:
        sheet_name = f"references/{reference_id}.md"
        assert sheet_name in documents
        assert documents[sheet_name] == (
            HARROWGATE_ROOT / "generated" / "references" / f"{reference_id}.md"
        ).read_text(encoding="utf-8")


def test_cauldron_retains_complete_library_without_replacing_operating_ledgers() -> None:
    adventure = load_adventure(CAULDRON_ROOT / "adventure.json")
    state = load_play_state(CAULDRON_ROOT / "play-state.example.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references) == CAULDRON_REFERENCE_IDS
    assert tuple(reference.kind for reference in adventure.references) == (
        *("person" for _ in range(12)),
        "organization",
        "organization",
        "object",
        "object",
        "other",
        "other",
        "other",
    )
    assert references[GWYNE_MARR_ID].aliases == ("Gwyne",)
    assert references[LORD_MAEL_TARAN_ID].aliases == (
        "Lord Mael",
        "Mael Taran",
        "Mael",
    )
    assert references[KING_BRANOC_ID].aliases == ("Branoc",)
    assert references[LADY_ADERYN_TARAN_ID].aliases == (
        "Lady Aderyn",
        "Aderyn",
    )
    assert references[BROTHER_CADDOC_ID].aliases == ("Caddoc",)
    assert references[EDRIC_TARAN_ID].aliases == ("Edric",)
    assert references[CAPTAIN_RHOD_VANE_ID].aliases == (
        "Captain Vane",
        "Rhod Vane",
        "Vane",
    )
    assert references[MOTHER_ELUNED_ID].aliases == (
        "Mother Eluned of the Mere House",
        "Eluned",
    )
    assert references[GREEN_LARKS_ID].kind == "organization"
    assert references[NINE_HEARTH_TRUST_ID].kind == "organization"
    assert references[CAULDRON_OF_NINE_SILENCES_ID].kind == "object"
    assert references[BRANOC_OATH_RING_ID].kind == "object"
    assert references[GATE_COMPACT_ID].kind == "other"
    assert references[FULL_ASKING_ID].kind == "other"
    assert references[GREAT_MUSTER_ID].kind == "other"
    assert "historical and constitutional evidence" in references[KING_BRANOC_ID].content
    assert "not proof of Mael's present authority" in references[EDRIC_TARAN_ID].content
    assert (
        "deliberately carries no key to the Cauldron Vault"
        in references[CAPTAIN_RHOD_VANE_ID].content
    )
    assert "Three hearths are not nine" in references[NINE_HEARTH_TRUST_ID].content
    assert "not interchangeable charges" in references[CAULDRON_OF_NINE_SILENCES_ID].content
    assert "does not compel acceptance" in references[BRANOC_OATH_RING_ID].content
    assert "not self-executing law" in references[FULL_ASKING_ID].content
    assert "does not create consent" in references[GREAT_MUSTER_ID].content

    actual_link_counts = dict.fromkeys(CAULDRON_REFERENCE_IDS, 0)
    actual_encounter_counts = {}
    for encounter in adventure.encounters:
        actual_encounter_counts[encounter.id] = len(encounter.reference_links)
        for link in encounter.reference_links:
            actual_link_counts[link.reference_id] += 1
    assert actual_link_counts == CAULDRON_REFERENCE_LINK_COUNTS
    assert actual_encounter_counts == CAULDRON_ENCOUNTER_REFERENCE_LINK_COUNTS
    assert sum(actual_link_counts.values()) == 127

    magpie_links = adventure.encounter_index()["crooked-magpie"].reference_links
    assert (
        tuple(link.reference_id for link in magpie_links[: len(CAULDRON_PRIMARY_REFERENCE_IDS)])
        == CAULDRON_PRIMARY_REFERENCE_IDS
    )
    assert tuple(link.reference_id for link in magpie_links[6:]) == (
        MOTHER_ELUNED_ID,
        TOMAS_WREN_ID,
        EFA_RILL_ID,
        GREEN_LARKS_ID,
        NINE_HEARTH_TRUST_ID,
        CAULDRON_OF_NINE_SILENCES_ID,
        BRANOC_OATH_RING_ID,
        GATE_COMPACT_ID,
        FULL_ASKING_ID,
        GREAT_MUSTER_ID,
    )
    assert "exact first question" in magpie_links[0].context
    assert "refuses to assume either guilt or vindication" in magpie_links[5].context
    assert "rival custody claim" in magpie_links[6].context
    assert "rather than ordinary thieves" in magpie_links[9].context

    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    gwyne_href = f'href="/references/{GWYNE_MARR_ID}"'
    vane_href = f'href="/references/{CAPTAIN_RHOD_VANE_ID}"'
    larks_href = f'href="/references/{GREEN_LARKS_ID}"'
    cauldron_href = f'href="/references/{CAULDRON_OF_NINE_SILENCES_ID}"'
    compact_href = f'href="/references/{GATE_COMPACT_ID}"'
    assert library.index(gwyne_href) < library.index(vane_href)
    assert library.index(vane_href) < library.index(larks_href)
    assert library.index(larks_href) < library.index(cauldron_href)
    assert library.index(cauldron_href) < library.index(compact_href)
    status, _, detail = request_wsgi(author_app, f"/references/{FULL_ASKING_ID}")
    assert status == "200 OK"
    assert "What command did you give Edric Taran at the western gate?" in detail
    assert "not self-executing law" in detail

    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, play = request_wsgi(
        play_app,
        "/play",
        query=urlencode(
            {
                "encounter": "cauldron-vault",
                "reference": CAULDRON_OF_NINE_SILENCES_ID,
            }
        ),
    )
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{CAULDRON_OF_NINE_SILENCES_ID}"' in play
    assert "Current band condition, dog state, load, route" in play
    assert 'data-play-pin-kind="reference"' in play
    assert project.snapshot == before

    documents = render_adventure_documents(adventure, validate_adventure(adventure))
    assert "references/index.md" in documents
    assert "## People" in documents["references/index.md"]
    assert "## Organizations" in documents["references/index.md"]
    assert "## Objects" in documents["references/index.md"]
    assert "## Other" in documents["references/index.md"]
    assert len(documents) == 35
    for reference_id in CAULDRON_REFERENCE_IDS:
        sheet_name = f"references/{reference_id}.md"
        assert sheet_name in documents
        assert documents[sheet_name] == (
            CAULDRON_ROOT / "generated" / "references" / f"{reference_id}.md"
        ).read_text(encoding="utf-8")


def test_cauldron_voice_iii_uses_references_without_weakening_table_procedures() -> None:
    adventure = load_adventure(CAULDRON_ROOT / "adventure.json")
    encounters = adventure.encounter_index()
    references = adventure.reference_index()

    assert "keeps the question strip beside the lead box" in encounters["crooked-magpie"].content
    assert "Her mother\u2019s line descends" not in encounters["crooked-magpie"].content
    assert (
        "stands between the central fire and the chained memorial rolls"
        in encounters["white-hart-court"].content
    )
    assert "## Caddoc at the candles" in encounters["chapel-last-word"].content
    assert "the dawn renewal text occupy three corners" in encounters["widows-solar"].content
    assert "## The Nine Hearth claim" in encounters["reed-weir"].content

    assert "## What the record can bear" in references[GWYNE_MARR_ID].content
    assert "## What the dead king cannot command" in references[KING_BRANOC_ID].content
    assert "## Preserve the water" in references[CAPTAIN_RHOD_VANE_ID].content
    assert "## Receiver, not owner" in references[TOMAS_WREN_ID].content
    assert "## Movement is not keeping" in references[GREEN_LARKS_ID].content
    assert "## The keeper at the threshold" in references[CAULDRON_OF_NINE_SILENCES_ID].content
    assert "## Testimony, not command" in references[FULL_ASKING_ID].content
    assert "## What the Muster cannot make lawful" in references[GREAT_MUSTER_ID].content


def test_cauldron_coherence_iii_reconciles_authority_custody_and_failure_paths() -> None:
    adventure = load_adventure(CAULDRON_ROOT / "adventure.json")
    state_path = CAULDRON_ROOT / "play-state.example.json"
    encounters = adventure.encounter_index()

    threshold = (
        "One authenticated black-water leaf, supported by two named witnesses, "
        "stays the oath until noon"
    )
    assert threshold in encounters["white-hart-court"].content
    assert (
        "One authenticated black-water leaf contradicting"
        not in encounters["white-hart-court"].content
    )

    exact_command = (
        "Bar the great leaves against the riders. Keep the wicket and the river stair "
        "until the outer ward is within. If the wall cannot hold, leave Dunwarren "
        "and save the people. A fort is a vessel; the realm is those it shelters."
    )

    playthrough = (CAULDRON_ROOT / "FULL-PLAYTHROUGH.md").read_text(encoding="utf-8")
    assert "Mabli Quill, three other Green Larks, and the second skiff" in playthrough
    assert "Mabli Quill, four Green Larks, and the second skiff" not in playthrough

    required_revelation_ids = {
        revelation.id for revelation in adventure.revelations if revelation.required
    }
    outside_solar_sources: dict[str, set[str]] = {
        revelation_id: set() for revelation_id in required_revelation_ids
    }
    for clue in adventure.clues:
        if (
            clue.revelation_id in outside_solar_sources
            and clue.source_encounter_id != "widows-solar"
        ):
            outside_solar_sources[clue.revelation_id].add(clue.source_encounter_id)
    assert min(len(sources) for sources in outside_solar_sources.values()) >= 2

    assert len(adventure.references) == 19
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 127
    assert len(state_path.read_text(encoding="utf-8")) > 0


def test_historical_selective_audit_survives_swine_reference_extraction() -> None:
    swine = load_adventure(SWINE_ROOT / "adventure.json")

    assert len(swine.references) == 21
    assert (SWINE_ROOT / "generated" / "references").is_dir()

    state = load_play_state(SWINE_ROOT / "play-state.example.json")
    play_app, project = build_play_app(swine, state)
    before = project.snapshot
    status, _, body = request_wsgi(
        play_app,
        "/play",
        query="encounter=the-hall-of-petitions",
    )
    assert status == "200 OK"
    assert "First Deputy Clerk Alda Mere" in body
    assert "This adventure has no persistent references." not in body
    assert project.snapshot == before


