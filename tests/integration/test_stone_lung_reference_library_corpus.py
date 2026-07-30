"""Stone Lung reference defragmentation and preservation evidence."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlencode
from uuid import UUID

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.play_state_store import load_play_state
from tests.support.corpus_contracts import assert_rendered_documents_match
from tests.support.web import build_authoring_app, build_play_app, request_wsgi

pytestmark = pytest.mark.corpus

STONE_LUNG_ROOT = Path("examples/the-siege-of-the-stone-lung")
ILYRA_ID = "f4f7d2d8-d36a-4156-a898-981753326347"
EDDA_ID = "a3b7aaad-961e-49e0-b33e-a37815d2cffc"
TAMAR_ID = "b79f9499-c3d6-40c5-afe0-ec75c1982ec5"
BRANN_ID = "4727a70d-0368-4a88-b86a-b250cc04e3eb"
VENN_ID = "485df0e9-f855-4d58-8064-300109947e36"
BAS_ID = "02ddfa9a-79a7-42d8-b614-243664f38efd"
COMMISSION_ID = "dc7c0b7b-b1c4-4e72-8885-71fcd785a384"
LANTERN_COURT_ID = "d8d49895-57e8-4cef-a91a-5f899c590d54"
SHATTERED_GATE_ID = "d7db595d-38cd-4c33-b557-13016ba8e619"
CINDER_FOUNDRY_ID = "81df1171-965f-48c4-9f43-da801acc0f02"
PALE_GARDENS_ID = "4c80a05c-1d71-41be-ab35-c931f7dee682"
REFUGE_GALLERIES_ID = "61728d3c-7a1b-4838-9f0e-6076d8ba0cbf"
BLACK_CISTERNS_ID = "308b133e-a63a-4417-b61b-9d743637f728"
COUNTERMINE_ID = "52fb318a-cbfe-4e77-a507-4c9a487073d0"
STONE_LUNG_ID = "c4c8f3a7-9a58-4daa-ab12-7df774a22794"
HOST_ID = "7ed444b4-60d6-4e12-aff3-fbf17f3682d2"
MINUTES_ID = "9fafc73c-5456-42fb-bad4-6b10eb9cf550"
CONDUIT_PLATE_ID = "d6d9ad8e-c9ff-439f-8d4b-75d1b379d60c"
HEARTSTRIKE_ID = "c66d1a1b-0e9e-4868-bdc3-d19740c8dd8a"

SESSION_ONE_REFERENCE_IDS = (
    ILYRA_ID,
    EDDA_ID,
    TAMAR_ID,
    BRANN_ID,
    VENN_ID,
    BAS_ID,
)
SESSION_TWO_REFERENCE_IDS = (
    COMMISSION_ID,
    LANTERN_COURT_ID,
    SHATTERED_GATE_ID,
    CINDER_FOUNDRY_ID,
    PALE_GARDENS_ID,
    REFUGE_GALLERIES_ID,
    BLACK_CISTERNS_ID,
    COUNTERMINE_ID,
    STONE_LUNG_ID,
    HOST_ID,
    MINUTES_ID,
    CONDUIT_PLATE_ID,
    HEARTSTRIKE_ID,
)
REFERENCE_IDS = SESSION_ONE_REFERENCE_IDS + SESSION_TWO_REFERENCE_IDS

SESSION_ONE_LINKS = {
    "the-lantern-court": SESSION_ONE_REFERENCE_IDS,
    "the-shattered-gate": (ILYRA_ID, BRANN_ID, VENN_ID, BAS_ID),
    "the-cinder-foundry": (ILYRA_ID, TAMAR_ID, BRANN_ID, VENN_ID, BAS_ID),
    "the-pale-gardens": (ILYRA_ID, EDDA_ID, TAMAR_ID, VENN_ID, BAS_ID),
    "the-refuge-galleries": (ILYRA_ID, EDDA_ID, TAMAR_ID, VENN_ID),
    "the-black-cisterns": (ILYRA_ID, EDDA_ID, TAMAR_ID, VENN_ID, BAS_ID),
    "the-countermine": (ILYRA_ID, TAMAR_ID, BRANN_ID, VENN_ID, BAS_ID),
    "the-stone-lung": SESSION_ONE_REFERENCE_IDS,
}
APPENDED_LINKS = {
    "the-lantern-court": (
        COMMISSION_ID,
        LANTERN_COURT_ID,
        STONE_LUNG_ID,
        HOST_ID,
        MINUTES_ID,
        CONDUIT_PLATE_ID,
        HEARTSTRIKE_ID,
    ),
    "the-shattered-gate": (
        SHATTERED_GATE_ID,
        CINDER_FOUNDRY_ID,
        COUNTERMINE_ID,
        STONE_LUNG_ID,
        HOST_ID,
    ),
    "the-cinder-foundry": (
        COMMISSION_ID,
        SHATTERED_GATE_ID,
        CINDER_FOUNDRY_ID,
        STONE_LUNG_ID,
        HOST_ID,
        HEARTSTRIKE_ID,
    ),
    "the-pale-gardens": (
        CINDER_FOUNDRY_ID,
        PALE_GARDENS_ID,
        REFUGE_GALLERIES_ID,
        STONE_LUNG_ID,
        HOST_ID,
        MINUTES_ID,
    ),
    "the-refuge-galleries": (
        COMMISSION_ID,
        LANTERN_COURT_ID,
        PALE_GARDENS_ID,
        REFUGE_GALLERIES_ID,
        BLACK_CISTERNS_ID,
        STONE_LUNG_ID,
        MINUTES_ID,
        CONDUIT_PLATE_ID,
    ),
    "the-black-cisterns": (
        REFUGE_GALLERIES_ID,
        BLACK_CISTERNS_ID,
        COUNTERMINE_ID,
        STONE_LUNG_ID,
        CONDUIT_PLATE_ID,
        HEARTSTRIKE_ID,
    ),
    "the-countermine": (
        COMMISSION_ID,
        SHATTERED_GATE_ID,
        BLACK_CISTERNS_ID,
        COUNTERMINE_ID,
        STONE_LUNG_ID,
        HOST_ID,
        HEARTSTRIKE_ID,
    ),
    "the-stone-lung": (
        COMMISSION_ID,
        SHATTERED_GATE_ID,
        CINDER_FOUNDRY_ID,
        REFUGE_GALLERIES_ID,
        COUNTERMINE_ID,
        STONE_LUNG_ID,
        HOST_ID,
        HEARTSTRIKE_ID,
    ),
}
EXPECTED_LINKS = {
    encounter_id: SESSION_ONE_LINKS[encounter_id] + APPENDED_LINKS[encounter_id]
    for encounter_id in SESSION_ONE_LINKS
}
EXPECTED_COUNTS = {
    ILYRA_ID: 8,
    EDDA_ID: 5,
    TAMAR_ID: 7,
    BRANN_ID: 5,
    VENN_ID: 8,
    BAS_ID: 7,
    COMMISSION_ID: 5,
    LANTERN_COURT_ID: 2,
    SHATTERED_GATE_ID: 4,
    CINDER_FOUNDRY_ID: 4,
    PALE_GARDENS_ID: 2,
    REFUGE_GALLERIES_ID: 4,
    BLACK_CISTERNS_ID: 3,
    COUNTERMINE_ID: 4,
    STONE_LUNG_ID: 8,
    HOST_ID: 6,
    MINUTES_ID: 3,
    CONDUIT_PLATE_ID: 3,
    HEARTSTRIKE_ID: 5,
}
SESSION_ONE_BODY_HASHES = {
    ILYRA_ID: "a9254251ae97149a104274f40bdc95d0702b51aa99982adda599259ebee3bfdf",
    EDDA_ID: "5716c0b9406ea5e52de3d53e48832695f0aa156dd8a07afbffe376fbcd41e267",
    TAMAR_ID: "c994de53985de7fbd6359c1cd0420f2cb9668a30a9ccdb6fe7e55b7de76d988b",
    BRANN_ID: "b3ab51ce96bb996d08db73bcb1832751438fb3f11a935620402893d01ff95b98",
    VENN_ID: "63eae930bbff48ee9c84615d284390f93587c010b5d825264944c8c8e458cfa2",
    BAS_ID: "45686f38d0cfbece5f91e6b14a667b1ecacd3825b2ca7e34a15a6698c0a3b04e",
}


def _without_reference_layer() -> str:
    payload = json.loads((STONE_LUNG_ROOT / "adventure.json").read_text(encoding="utf-8"))
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
    payload = json.loads((STONE_LUNG_ROOT / "adventure.json").read_text(encoding="utf-8"))
    prefix = {
        "references": payload["references"][: len(SESSION_ONE_REFERENCE_IDS)],
        "reference_links": {
            encounter["id"]: encounter["reference_links"][
                : len(SESSION_ONE_LINKS[encounter["id"]])
            ]
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


def test_stone_lung_extraction_i_records_and_links_remain_exact_prefixes() -> None:
    adventure = load_adventure(STONE_LUNG_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references[:6]) == (
        SESSION_ONE_REFERENCE_IDS
    )
    assert _session_one_prefix_hash() == (
        "e76d254d9f8a0f63074e51150e041123b28be9fe681d9737afbd20ca673d3286"
    )
    for reference_id in SESSION_ONE_REFERENCE_IDS:
        assert hashlib.sha256(references[reference_id].content.encode()).hexdigest() == (
            SESSION_ONE_BODY_HASHES[reference_id]
        )

    counts: Counter[str] = Counter()
    for encounter in adventure.encounters:
        expected_prefix = SESSION_ONE_LINKS[encounter.id]
        actual_prefix = tuple(
            link.reference_id for link in encounter.reference_links[: len(expected_prefix)]
        )
        assert actual_prefix == expected_prefix
        counts.update(actual_prefix)
    assert dict(counts) == {
        ILYRA_ID: 8,
        EDDA_ID: 5,
        TAMAR_ID: 7,
        BRANN_ID: 5,
        VENN_ID: 8,
        BAS_ID: 7,
    }
    assert sum(counts.values()) == 40


def test_stone_lung_extraction_ii_records_and_links_are_bounded_and_ordered() -> None:
    adventure = load_adventure(STONE_LUNG_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references) == REFERENCE_IDS
    assert tuple(reference.kind for reference in adventure.references) == (
        *("person",) * 6,
        "other",
        *("place",) * 8,
        "organization",
        *("object",) * 3,
    )
    assert references[COMMISSION_ID].aliases == (
        "six-lantern writ",
        "copied commission",
        "commission writ",
    )
    assert references[STONE_LUNG_ID].aliases == (
        "Stone Lung",
        "the Lung",
        "breathing engine",
    )
    assert references[HOST_ID].aliases == (
        "the Host",
        "Lower Road Host",
        "Lorn host",
    )
    assert references[HEARTSTRIKE_ID].aliases == (
        "Heartstrike charge",
        "resonance charge",
        "Heartstrike line",
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
            assert "Basalt Hand" not in link.context
    assert dict(counts) == EXPECTED_COUNTS
    assert sum(counts.values()) == 93

    forbidden = (
        "Maela Orin",
        "Orren Caul",
        "Siva Merrow",
        "Hadrik Sol",
        "currently held",
        "currently breached",
        "Venn has revoked",
        "Heartstrike has fired",
    )
    boundary_phrases = {
        COMMISSION_ID: "decided in play",
        LANTERN_COURT_ID: "change with the siege",
        SHATTERED_GATE_ID: "current siege",
        CINDER_FOUNDRY_ID: "settled in play",
        PALE_GARDENS_ID: "discovered in the beds",
        REFUGE_GALLERIES_ID: "change with the emergency",
        BLACK_CISTERNS_ID: "measured below the waterline",
        COUNTERMINE_ID: "live in the tunnel",
        STONE_LUNG_ID: "belong to the finale",
        HOST_ID: "change with play",
        MINUTES_ID: "is current state",
        CONDUIT_PLATE_ID: "current crisis",
        HEARTSTRIKE_ID: "current siege",
    }
    for reference_id in SESSION_TWO_REFERENCE_IDS:
        reference = references[reference_id]
        text = reference.summary + "\n" + reference.content
        for phrase in forbidden:
            assert phrase not in text
        assert boundary_phrases[reference_id] in reference.content

    assert validate_adventure(adventure).is_valid


def test_stone_lung_reference_layer_is_semantically_additive() -> None:
    adventure_path = STONE_LUNG_ROOT / "adventure.json"
    state_path = STONE_LUNG_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)

    assert _without_reference_layer() == (
        "9b63019707689faad187f50785af98088815f2cdd4d85f4e3781822fb7ea0836"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "67c9b16c6b1d9322706ea4af91aa433e93ad5ad54723f3890dc3aefacd9a2268"
    )
    assert len(adventure.encounters) == 8
    assert len(adventure.revelations) == 12
    assert len(adventure.clues) == 46
    assert len(adventure.references) == 19
    assert len(state.events) == 85
    assert validate_adventure(adventure).edge_connectivity == 3


def test_stone_lung_voice_iii_freezes_every_non_prose_semantic() -> None:
    adventure_path = STONE_LUNG_ROOT / "adventure.json"
    state_path = STONE_LUNG_ROOT / "play-state.example.json"
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
        "2979459da44f96229f5a98f3fdca3eb65366aaf2fe5b3cf769bdc97b8b0980f8"
    )
    assert tuple(encounter_content) == tuple(EXPECTED_LINKS)
    assert tuple(reference_content) == REFERENCE_IDS
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "67c9b16c6b1d9322706ea4af91aa433e93ad5ad54723f3890dc3aefacd9a2268"
    )


def test_stone_lung_reference_views_are_retrievable_and_journal_neutral() -> None:
    adventure = load_adventure(STONE_LUNG_ROOT / "adventure.json")
    state = load_play_state(STONE_LUNG_ROOT / "play-state.example.json")

    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    for title in (
        "First Warden Ilyra Dain",
        "Speaker Edda Marr",
        "Ventwright Tamar Ohn",
        "Gate Captain Brann Sile",
        "Marshal Sera Venn",
        "Engineer Korr Bas",
        "The Six-Lantern Commission",
        "The Lantern Court",
        "The Shattered Gate",
        "The Cinder Foundry",
        "The Pale Gardens",
        "The Refuge Galleries",
        "The Cisterns of Black Breath",
        "The Countermine",
        "The Stone Lung",
        "The Host of the Lower Road",
        "The Sealed Blight Minutes",
        "The Original Lorn Conduit Plate",
        "Heartstrike",
    ):
        assert title in library

    status, _, detail = request_wsgi(author_app, f"/references/{STONE_LUNG_ID}")
    assert status == "200 OK"
    assert "The Lantern Court" in detail
    assert "The Shattered Gate" in detail
    assert "The Cinder Foundry" in detail
    assert "The Refuge Galleries" in detail
    assert "The Cisterns of Black Breath" in detail
    assert "The Countermine" in detail

    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, body = request_wsgi(
        play_app,
        "/play",
        query=urlencode(
            {
                "encounter": "the-stone-lung",
                "reference": HEARTSTRIKE_ID,
            }
        ),
    )
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{HEARTSTRIKE_ID}"' in body
    assert "Heartstrike" in body
    assert project.snapshot == before


def test_stone_lung_packet_adds_reference_views_without_changing_demonstration() -> None:
    adventure = load_adventure(STONE_LUNG_ROOT / "adventure.json")
    state_path = STONE_LUNG_ROOT / "play-state.example.json"
    state = load_play_state(state_path)
    documents = render_adventure_documents(adventure, validate_adventure(adventure), state)

    assert len(documents) == 34
    index = documents["references/index.md"]
    for heading in ("## People", "## Places", "## Organizations", "## Objects", "## Other"):
        assert heading in index
    for reference_id in REFERENCE_IDS:
        assert f"references/{reference_id}.md" in documents
    assert_rendered_documents_match(
        documents, STONE_LUNG_ROOT / "generated"
    )


def test_stone_lung_voice_iii_repairs_only_the_documented_seams() -> None:
    adventure_path = STONE_LUNG_ROOT / "adventure.json"
    adventure = load_adventure(adventure_path)
    encounters = adventure.encounter_index()
    references = adventure.reference_index()

    expected_encounter_hashes = {
        "the-lantern-court": "e810bf3b0036b406325e67f98a963620a5ec1a1af3877f2a56a8966316b2535f",
        "the-shattered-gate": "f6a49e86a2b99c65c4930d897ddec036f0066034c6918e6cf73456922d16dc29",
        "the-cinder-foundry": "095b3f39cf908388b30e8e4ac6509f76177370074fe71bc853f9b4ca15adde7e",
        "the-pale-gardens": "a1a7a73c784a4768fd608c005c3a875f8ab8d8ec8203aaa4f21f0932b0e56550",
        "the-refuge-galleries": "b4a295ca8f672c43e2821238b38030b35aaa5e401b91200100f18fe63223a607",
        "the-black-cisterns": "ba83f71fe7f2dab387f2bee121a321472374bfa4be5591ec794af9e282af0ace",
        "the-countermine": "59d3fbdbc26a91d0d9252c536f79af0193a521fd884f11de7605821f1e2c3040",
        "the-stone-lung": "61ca8e823535c6c7c649c82328fa7b4cf1e3bad30af17efaac63a4f290c30232",
    }
    expected_reference_hashes = {
        ILYRA_ID: "a9254251ae97149a104274f40bdc95d0702b51aa99982adda599259ebee3bfdf",
        EDDA_ID: "5716c0b9406ea5e52de3d53e48832695f0aa156dd8a07afbffe376fbcd41e267",
        TAMAR_ID: "c994de53985de7fbd6359c1cd0420f2cb9668a30a9ccdb6fe7e55b7de76d988b",
        BRANN_ID: "b3ab51ce96bb996d08db73bcb1832751438fb3f11a935620402893d01ff95b98",
        VENN_ID: "63eae930bbff48ee9c84615d284390f93587c010b5d825264944c8c8e458cfa2",
        BAS_ID: "45686f38d0cfbece5f91e6b14a667b1ecacd3825b2ca7e34a15a6698c0a3b04e",
        COMMISSION_ID: "f5579dc47bdef9db7598a8bb70aabddaecb7403aee4d203a765558d985b7605c",
        LANTERN_COURT_ID: "bf90e2eb4957cdad9d646f71be21644f29319483ec90f8152cd67367118c321c",
        SHATTERED_GATE_ID: "a4b703bd3c17dc12fdf4b0b8e7d723dfa3a01460c23448a5ffaacec6728ecc00",
        CINDER_FOUNDRY_ID: "bae0420bf7ef954a5afadb3596dc124e8d47357845063e0657f66dabf9d3e536",
        PALE_GARDENS_ID: "eadabc7a4760b56ef055f602ed35e4f4177bed22d29a21b2c8aa6f23dba30661",
        REFUGE_GALLERIES_ID: "43480d49681b798a35675363032da79a98fd92793975814e445938014149c25f",
        BLACK_CISTERNS_ID: "6556180e60cb30fc4cc41d04872fe7fea2e15f31453b6e33e76c586fd207ed6a",
        COUNTERMINE_ID: "215e0eacb055417ff6c6f771950979506b2685ba960072defb834a939b78ab18",
        STONE_LUNG_ID: "ae9a4bcef383cfb7dea108a55b3dee97902d3c5a9f4e97e09968de9cde2fdda8",
        HOST_ID: "39e4d904262d22064b15400684cf85e350d605539477d3f85ac20eb548f4aa5f",
        MINUTES_ID: "4c5b7ff201bcd0793a5e468141ef76a9596a12e9e0bb59323efd2175a123936d",
        CONDUIT_PLATE_ID: "e4dfe527d1113e8933494f734afd72999f9c0b9728378898c87a23b8e789f48e",
        HEARTSTRIKE_ID: "fc9e8a123b44239991bf65b26f668c0d4a9f8b61970471a29a6739e71d8dd628",
    }

    for encounter_id, expected_hash in expected_encounter_hashes.items():
        assert hashlib.sha256(encounters[encounter_id].content.encode()).hexdigest() == (
            expected_hash
        )
    for reference_id, expected_hash in expected_reference_hashes.items():
        assert hashlib.sha256(references[reference_id].content.encode()).hexdigest() == (
            expected_hash
        )

    assert sum(len(encounter.content.split()) for encounter in adventure.encounters) == 5162
    assert sum(len(reference.content.split()) for reference in adventure.references) == 3331
    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "50ddc63038a4a534c497e9a5791edb74cbac7fb43e8ed75a794cd653b98457b1"
    )

    expected_live_seams = {
        "the-lantern-court": "Pale Gardens lantern gutters blue just as a runner",
        "the-shattered-gate": "Every proposal must name what leaves Brann's wall",
        "the-cinder-foundry": "unexploded shell buried in the east furnace answers",
        "the-pale-gardens": "Two frightened officials bring Sen Tahl opposite orders",
        "the-refuge-galleries": "Eleven ration sacks are missing",
        "the-black-cisterns": "Three workers are missing beyond a barred inspection arch",
        "the-countermine": "two orders from different chains, both valid-looking",
        "the-stone-lung": "Each stroke makes the pressure vault declare itself",
    }
    for encounter_id, phrase in expected_live_seams.items():
        assert phrase in encounters[encounter_id].content

    retired_repetition = {
        "the-lantern-court": "The nineteenth day of the siege begins beneath six iron lanterns",
        "the-shattered-gate": "Brann has no patience for claims that remove bodies",
        "the-cinder-foundry": "The Cinder Foundry descends through three halls",
        "the-pale-gardens": "The Pale Gardens descend beneath curtains",
        "the-refuge-galleries": "The Refuge Galleries were built for processions",
        "the-black-cisterns": "The Cisterns of Black Breath lie beneath Kest Mourne's oldest wards",
        "the-countermine": "Under the Host's wartime articles, Bas controls calibration",
        "the-stone-lung": "The Stone Lung fills a pressure vault beneath Kest Mourne",
    }
    for encounter_id, phrase in retired_repetition.items():
        assert phrase not in encounters[encounter_id].content

    for reference_id in SESSION_ONE_REFERENCE_IDS:
        assert hashlib.sha256(references[reference_id].content.encode()).hexdigest() == (
            SESSION_ONE_BODY_HASHES[reference_id]
        )
    for reference_id in SESSION_TWO_REFERENCE_IDS:
        assert "remain live adventure state" not in references[reference_id].content


def test_stone_lung_coherence_iii_closes_the_sequence_without_canonical_change() -> None:
    adventure_path = STONE_LUNG_ROOT / "adventure.json"
    state_path = STONE_LUNG_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    encounters = adventure.encounter_index()
    revelations = adventure.revelation_index()

    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "50ddc63038a4a534c497e9a5791edb74cbac7fb43e8ed75a794cd653b98457b1"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "67c9b16c6b1d9322706ea4af91aa433e93ad5ad54723f3890dc3aefacd9a2268"
    )
    assert len(adventure.encounters) == 8
    assert len(adventure.revelations) == 12
    assert sum(revelation.required for revelation in adventure.revelations) == 11
    assert len(adventure.clues) == 46
    assert len(adventure.references) == 19
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 93
    assert len(state.events) == 85
    assert len(state.active_events) == 83
    assert validate_adventure(adventure).edge_connectivity == 3

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
        "2979459da44f96229f5a98f3fdca3eb65366aaf2fe5b3cf769bdc97b8b0980f8"
    )

    source_encounters: dict[str, set[str]] = {
        revelation.id: set()
        for revelation in adventure.revelations
        if revelation.required
    }
    for clue in adventure.clues:
        if clue.revelation_id in source_encounters:
            source_encounters[clue.revelation_id].add(clue.source_encounter_id)
    assert len(source_encounters) == 11
    assert {len(sources) for sources in source_encounters.values()} == {3, 4, 5}
    for sources in source_encounters.values():
        for removed in encounters:
            assert len(sources - {removed}) >= 2

    directed_edges: dict[str, set[str]] = {
        encounter.id: set() for encounter in adventure.encounters
    }
    for clue in adventure.clues:
        target = revelations[clue.revelation_id].unlocks_encounter_id
        if target is not None and target != clue.source_encounter_id:
            directed_edges[clue.source_encounter_id].add(target)

    reached = {"the-lantern-court"}
    frontier = ["the-lantern-court"]
    while frontier:
        source = frontier.pop()
        for target in directed_edges[source] - reached:
            reached.add(target)
            frontier.append(target)
    assert reached == set(encounters)
    assert directed_edges["the-cinder-foundry"] >= {"the-stone-lung"}
    assert directed_edges["the-refuge-galleries"] >= {"the-stone-lung"}
    assert directed_edges["the-countermine"] >= {"the-stone-lung"}
    approach_revelation = revelations[
        "three-routes-converge-on-the-stone-lung-and-heartstrike-charge"
    ]
    assert approach_revelation.unlocks_encounter_id == "the-stone-lung"
    assert {
        clue.source_encounter_id
        for clue in adventure.clues
        if clue.revelation_id == approach_revelation.id
    } == {
        "the-cinder-foundry",
        "the-refuge-galleries",
        "the-countermine",
    }

    live_state_phrases = {
        "the-lantern-court": (
            "parchment cannot supply missing crews, roads, or hours",
            "Early reconnaissance at the Stone Lung does not by itself begin Heartstrike",
            "Name the reserve, crew, road, and hour a proposal requires",
        ),
        "the-shattered-gate": (
            "what leaves Brann's wall, what that absence buys",
            "Keep them alive and compare their orders",
            "the Stone Lung begins with less time",
        ),
        "the-cinder-foundry": (
            "one full shift of skilled labor remains",
            "Record what is full, what is diminished",
            "The shell remembers vibration",
        ),
        "the-pale-gardens": (
            "Two frightened officials bring Sen Tahl opposite orders",
            "One fire would consume the poison, the harvest, the living filters",
        ),
        "the-refuge-galleries": (
            "Eleven ration sacks are missing",
            "Grief preserved a route",
        ),
        "the-black-cisterns": (
            "Three workers are missing beyond a barred inspection arch",
            "Opening the wrong bypass saves them quickly and sends black water toward the Refuge",
        ),
        "the-countermine": (
            "two orders from different chains, both valid-looking",
            "Each road gains access by spending something",
        ),
        "the-stone-lung": (
            "An approach is a military road, not merely an entrance",
            "An early visit finds Bas still deploying the weapon",
            "Technical competence without a held road arrives too late",
            "Heartstrike fires unless disabled, delayed, deceived, or seized",
        ),
    }
    for encounter_id, phrases in live_state_phrases.items():
        for phrase in phrases:
            assert phrase in encounters[encounter_id].content

    reference_text = "\n".join(
        reference.summary + "\n" + reference.content
        for reference in adventure.references
    )
    for demonstrated_state in (
        "The Shattered Gate is held",
        "The Cinder Foundry is held at a cost",
        "The Pale Gardens are held",
        "The Refuge Galleries are held",
        "The Black Cisterns are held at a cost",
        "The Countermine is held by local truce",
        "Heartstrike is detuned",
        "the southern branch reopens",
        "The outer gate falls",
    ):
        assert demonstrated_state not in reference_text

    projection = project_play_state(adventure, state)
    consequences = "\n".join(
        consequence.text for consequence in projection.consequences
    )
    for demonstrated_state in (
        "The Shattered Gate is held",
        "The Cinder Foundry is held at a cost",
        "The Pale Gardens are held",
        "The Refuge Galleries are held",
        "The Black Cisterns are held at a cost",
        "The Countermine is held by local truce",
        "The outer gate falls",
        "Heartstrike is detuned",
        "the southern branch reopens",
        "a seventh unlit lantern",
    ):
        assert demonstrated_state in consequences
    assert len(projection.visits) == 10
    assert len(projection.spotted_clue_ids) == 32
    assert len(projection.corrections) == 1
    assert len(projection.consequences) == 12
    assert all(item.is_established for item in projection.revelation_progress)


    documents = render_adventure_documents(
        adventure,
        validate_adventure(adventure),
        state,
    )
    assert len(documents) == 34
    assert_rendered_documents_match(
        documents, STONE_LUNG_ROOT / "generated"
    )


