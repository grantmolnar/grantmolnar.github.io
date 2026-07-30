"""When the Swine Kneel reference defragmentation and preservation evidence."""

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
SWINE_ROOT = Path("examples/when-the-swine-kneel")

SESSION_ONE_REFERENCE_IDS = ('5b4c72ce-32c7-44fd-b37b-4f91b49d0266',
 'bcaa6c5b-213d-4196-92c6-e9b9ed91dd2b',
 'd2d941dd-db72-447d-8c53-0ece9de800be',
 '7bdf27b6-3ac1-482b-80d3-1276dfe3611e',
 'ac969ee5-c1d9-4bb5-b0c6-256744413b40',
 'd41a4f2a-dfd4-4672-8360-b317020551e4',
 '021c5c85-633d-49d8-8004-dad626283a0c',
 'cd71ccee-a344-408a-b4c9-83fb963c5390',
 '0506346e-15b0-4109-9f66-d9d7fadcecb5',
 '6f322cc5-f45f-418b-8dba-a265b1b3b3c5')
SESSION_TWO_REFERENCE_IDS = ('94df4e5e-13e1-449c-ae42-64c6840df10a',
 'de09340e-8754-4ca8-af35-c5f8a609a2ee',
 '5e1874c7-837e-4666-8563-2a4032b5b78b',
 '99208e47-eff8-473d-a2db-f62fcdd806fd',
 '5ac2ecc1-1f2e-413f-b3da-d6cc8463fea9',
 '9622f400-e8c6-4c9c-a660-1eeb6300913e',
 '138a7daf-e2f7-4640-a59c-3833ba4fc5f0',
 '1aeac0e3-80de-4749-ae76-1b3c1a4668e4',
 '8c3fbd04-1098-423b-bbbe-27b0f6dc4bdb',
 '9a4f61cc-cdbc-41b2-8946-f385b2d44eb5',
 'cab148c1-a14a-495d-9caf-da41884d028e')
REFERENCE_IDS = SESSION_ONE_REFERENCE_IDS + SESSION_TWO_REFERENCE_IDS
SESSION_ONE_LINKS = {'the-hall-of-petitions': ('5b4c72ce-32c7-44fd-b37b-4f91b49d0266',
                           'bcaa6c5b-213d-4196-92c6-e9b9ed91dd2b',
                           'ac969ee5-c1d9-4bb5-b0c6-256744413b40',
                           '0506346e-15b0-4109-9f66-d9d7fadcecb5'),
 'southgate-stockyards': ('5b4c72ce-32c7-44fd-b37b-4f91b49d0266',
                          'bcaa6c5b-213d-4196-92c6-e9b9ed91dd2b',
                          'ac969ee5-c1d9-4bb5-b0c6-256744413b40',
                          'd41a4f2a-dfd4-4672-8360-b317020551e4',
                          '0506346e-15b0-4109-9f66-d9d7fadcecb5'),
 'the-college-of-civic-measure': ('5b4c72ce-32c7-44fd-b37b-4f91b49d0266',
                                  'bcaa6c5b-213d-4196-92c6-e9b9ed91dd2b',
                                  'd2d941dd-db72-447d-8c53-0ece9de800be',
                                  '021c5c85-633d-49d8-8004-dad626283a0c',
                                  '0506346e-15b0-4109-9f66-d9d7fadcecb5',
                                  '6f322cc5-f45f-418b-8dba-a265b1b3b3c5'),
 'rillcross-farm-belt': ('5b4c72ce-32c7-44fd-b37b-4f91b49d0266',
                         'bcaa6c5b-213d-4196-92c6-e9b9ed91dd2b',
                         'd2d941dd-db72-447d-8c53-0ece9de800be',
                         'ac969ee5-c1d9-4bb5-b0c6-256744413b40',
                         'd41a4f2a-dfd4-4672-8360-b317020551e4',
                         'cd71ccee-a344-408a-b4c9-83fb963c5390'),
 'the-chapel-of-the-first-survey': ('5b4c72ce-32c7-44fd-b37b-4f91b49d0266',
                                    'bcaa6c5b-213d-4196-92c6-e9b9ed91dd2b',
                                    'd2d941dd-db72-447d-8c53-0ece9de800be',
                                    '021c5c85-633d-49d8-8004-dad626283a0c',
                                    'cd71ccee-a344-408a-b4c9-83fb963c5390',
                                    '0506346e-15b0-4109-9f66-d9d7fadcecb5',
                                    '6f322cc5-f45f-418b-8dba-a265b1b3b3c5'),
 'the-nine-mile-pump-house': ('5b4c72ce-32c7-44fd-b37b-4f91b49d0266',
                              'bcaa6c5b-213d-4196-92c6-e9b9ed91dd2b',
                              'd2d941dd-db72-447d-8c53-0ece9de800be',
                              '7bdf27b6-3ac1-482b-80d3-1276dfe3611e',
                              'ac969ee5-c1d9-4bb5-b0c6-256744413b40',
                              'd41a4f2a-dfd4-4672-8360-b317020551e4',
                              '021c5c85-633d-49d8-8004-dad626283a0c',
                              'cd71ccee-a344-408a-b4c9-83fb963c5390',
                              '0506346e-15b0-4109-9f66-d9d7fadcecb5',
                              '6f322cc5-f45f-418b-8dba-a265b1b3b3c5'),
 'the-deep-bell': ('5b4c72ce-32c7-44fd-b37b-4f91b49d0266',
                   'bcaa6c5b-213d-4196-92c6-e9b9ed91dd2b',
                   'd2d941dd-db72-447d-8c53-0ece9de800be',
                   '7bdf27b6-3ac1-482b-80d3-1276dfe3611e',
                   'ac969ee5-c1d9-4bb5-b0c6-256744413b40',
                   'd41a4f2a-dfd4-4672-8360-b317020551e4',
                   '021c5c85-633d-49d8-8004-dad626283a0c',
                   'cd71ccee-a344-408a-b4c9-83fb963c5390',
                   '0506346e-15b0-4109-9f66-d9d7fadcecb5',
                   '6f322cc5-f45f-418b-8dba-a265b1b3b3c5')}
APPENDED_LINKS = {'the-hall-of-petitions': ('94df4e5e-13e1-449c-ae42-64c6840df10a',
                           'de09340e-8754-4ca8-af35-c5f8a609a2ee',
                           '99208e47-eff8-473d-a2db-f62fcdd806fd',
                           '1aeac0e3-80de-4749-ae76-1b3c1a4668e4',
                           '8c3fbd04-1098-423b-bbbe-27b0f6dc4bdb',
                           '9a4f61cc-cdbc-41b2-8946-f385b2d44eb5',
                           'cab148c1-a14a-495d-9caf-da41884d028e'),
 'southgate-stockyards': ('94df4e5e-13e1-449c-ae42-64c6840df10a',
                          'de09340e-8754-4ca8-af35-c5f8a609a2ee',
                          '99208e47-eff8-473d-a2db-f62fcdd806fd',
                          '138a7daf-e2f7-4640-a59c-3833ba4fc5f0',
                          '1aeac0e3-80de-4749-ae76-1b3c1a4668e4',
                          '8c3fbd04-1098-423b-bbbe-27b0f6dc4bdb',
                          '9a4f61cc-cdbc-41b2-8946-f385b2d44eb5',
                          'cab148c1-a14a-495d-9caf-da41884d028e'),
 'the-college-of-civic-measure': ('94df4e5e-13e1-449c-ae42-64c6840df10a',
                                  '5e1874c7-837e-4666-8563-2a4032b5b78b',
                                  '5ac2ecc1-1f2e-413f-b3da-d6cc8463fea9',
                                  '9622f400-e8c6-4c9c-a660-1eeb6300913e',
                                  '138a7daf-e2f7-4640-a59c-3833ba4fc5f0',
                                  '1aeac0e3-80de-4749-ae76-1b3c1a4668e4',
                                  '9a4f61cc-cdbc-41b2-8946-f385b2d44eb5',
                                  'cab148c1-a14a-495d-9caf-da41884d028e'),
 'rillcross-farm-belt': ('94df4e5e-13e1-449c-ae42-64c6840df10a',
                         'de09340e-8754-4ca8-af35-c5f8a609a2ee',
                         '5e1874c7-837e-4666-8563-2a4032b5b78b',
                         '99208e47-eff8-473d-a2db-f62fcdd806fd',
                         '5ac2ecc1-1f2e-413f-b3da-d6cc8463fea9',
                         '9622f400-e8c6-4c9c-a660-1eeb6300913e',
                         '138a7daf-e2f7-4640-a59c-3833ba4fc5f0',
                         '1aeac0e3-80de-4749-ae76-1b3c1a4668e4',
                         '9a4f61cc-cdbc-41b2-8946-f385b2d44eb5',
                         'cab148c1-a14a-495d-9caf-da41884d028e'),
 'the-chapel-of-the-first-survey': ('94df4e5e-13e1-449c-ae42-64c6840df10a',
                                    '5e1874c7-837e-4666-8563-2a4032b5b78b',
                                    '99208e47-eff8-473d-a2db-f62fcdd806fd',
                                    '5ac2ecc1-1f2e-413f-b3da-d6cc8463fea9',
                                    '9622f400-e8c6-4c9c-a660-1eeb6300913e',
                                    '138a7daf-e2f7-4640-a59c-3833ba4fc5f0',
                                    '1aeac0e3-80de-4749-ae76-1b3c1a4668e4',
                                    '9a4f61cc-cdbc-41b2-8946-f385b2d44eb5',
                                    'cab148c1-a14a-495d-9caf-da41884d028e'),
 'the-nine-mile-pump-house': ('94df4e5e-13e1-449c-ae42-64c6840df10a',
                              'de09340e-8754-4ca8-af35-c5f8a609a2ee',
                              '5e1874c7-837e-4666-8563-2a4032b5b78b',
                              '99208e47-eff8-473d-a2db-f62fcdd806fd',
                              '5ac2ecc1-1f2e-413f-b3da-d6cc8463fea9',
                              '9622f400-e8c6-4c9c-a660-1eeb6300913e',
                              '138a7daf-e2f7-4640-a59c-3833ba4fc5f0',
                              '1aeac0e3-80de-4749-ae76-1b3c1a4668e4',
                              '9a4f61cc-cdbc-41b2-8946-f385b2d44eb5',
                              'cab148c1-a14a-495d-9caf-da41884d028e'),
 'the-deep-bell': ('94df4e5e-13e1-449c-ae42-64c6840df10a',
                   'de09340e-8754-4ca8-af35-c5f8a609a2ee',
                   '5e1874c7-837e-4666-8563-2a4032b5b78b',
                   '99208e47-eff8-473d-a2db-f62fcdd806fd',
                   '5ac2ecc1-1f2e-413f-b3da-d6cc8463fea9',
                   '9622f400-e8c6-4c9c-a660-1eeb6300913e',
                   '138a7daf-e2f7-4640-a59c-3833ba4fc5f0',
                   '1aeac0e3-80de-4749-ae76-1b3c1a4668e4',
                   '8c3fbd04-1098-423b-bbbe-27b0f6dc4bdb',
                   '9a4f61cc-cdbc-41b2-8946-f385b2d44eb5',
                   'cab148c1-a14a-495d-9caf-da41884d028e')}
EXPECTED_LINKS = {
    encounter_id: SESSION_ONE_LINKS[encounter_id] + APPENDED_LINKS[encounter_id]
    for encounter_id in SESSION_ONE_LINKS
}
EXPECTED_COUNTS = {'5b4c72ce-32c7-44fd-b37b-4f91b49d0266': 7,
 'bcaa6c5b-213d-4196-92c6-e9b9ed91dd2b': 7,
 'ac969ee5-c1d9-4bb5-b0c6-256744413b40': 5,
 '0506346e-15b0-4109-9f66-d9d7fadcecb5': 6,
 '94df4e5e-13e1-449c-ae42-64c6840df10a': 7,
 'de09340e-8754-4ca8-af35-c5f8a609a2ee': 5,
 '99208e47-eff8-473d-a2db-f62fcdd806fd': 6,
 '1aeac0e3-80de-4749-ae76-1b3c1a4668e4': 7,
 '8c3fbd04-1098-423b-bbbe-27b0f6dc4bdb': 3,
 '9a4f61cc-cdbc-41b2-8946-f385b2d44eb5': 7,
 'cab148c1-a14a-495d-9caf-da41884d028e': 7,
 'd41a4f2a-dfd4-4672-8360-b317020551e4': 4,
 '138a7daf-e2f7-4640-a59c-3833ba4fc5f0': 6,
 'd2d941dd-db72-447d-8c53-0ece9de800be': 5,
 '021c5c85-633d-49d8-8004-dad626283a0c': 4,
 '6f322cc5-f45f-418b-8dba-a265b1b3b3c5': 4,
 '5e1874c7-837e-4666-8563-2a4032b5b78b': 5,
 '5ac2ecc1-1f2e-413f-b3da-d6cc8463fea9': 5,
 '9622f400-e8c6-4c9c-a660-1eeb6300913e': 5,
 'cd71ccee-a344-408a-b4c9-83fb963c5390': 4,
 '7bdf27b6-3ac1-482b-80d3-1276dfe3611e': 2}
SESSION_ONE_BODY_HASHES = {'5b4c72ce-32c7-44fd-b37b-4f91b49d0266': 'b8a2f5c104f036498f2d3d6e1c28988cc93a079e064c40768bc25b056b1218c4',
 'bcaa6c5b-213d-4196-92c6-e9b9ed91dd2b': 'ed4af2e607e99e59523a8648151725344164a28ad54b3d8fb270c9d0d26a6968',
 'd2d941dd-db72-447d-8c53-0ece9de800be': '66428ae38823fa51455f176e019c40de4645caa1f6fe18fa9fa7c1cf4757010a',
 '7bdf27b6-3ac1-482b-80d3-1276dfe3611e': 'c6c89e69c3ac486b1098f1e0f11db509e185d009736db67f9d71986b9f6d8922',
 'ac969ee5-c1d9-4bb5-b0c6-256744413b40': 'efa2a8902f68fa1a363ed2a75db0199fbc9265947194b598c10f6bc3ffc570ec',
 'd41a4f2a-dfd4-4672-8360-b317020551e4': 'a163fe29b9bcdfd8627328bde8da542ab1283777636089a970be441e5be54605',
 '021c5c85-633d-49d8-8004-dad626283a0c': '06b2eb03754eac973e6263a1f5724a0c4c26dd422b71e225bc3aa4df314fdbdd',
 'cd71ccee-a344-408a-b4c9-83fb963c5390': '8fa913b3e4c78114e98f2ced4c2299a8453ad4c64ea7b35179b50d88ba6b03d9',
 '0506346e-15b0-4109-9f66-d9d7fadcecb5': 'e7f1f53235b5a97f5aef3bcca0009d7565d93f06c312d805ed7455e13fa49880',
 '6f322cc5-f45f-418b-8dba-a265b1b3b3c5': 'a60c1a3ccb87040a8a3eec0187e0fd6d43ab0b70a0977bc7db7ae619fed9fedc'}
SESSION_TWO_BODY_HASHES = {
    "94df4e5e-13e1-449c-ae42-64c6840df10a": "d9ef48230356d0234eef4e59efb1fa4165038cbf416631c0e5ff750369296b11",
    "de09340e-8754-4ca8-af35-c5f8a609a2ee": "d1f21abc0ef384214b868e247739b931040e131b04bc8f5e19f915b7027399f1",
    "5e1874c7-837e-4666-8563-2a4032b5b78b": "f755f8d4435e831cd2274e0460ad0b9a93b33ecdf4e11344941a722bae15d91a",
    "99208e47-eff8-473d-a2db-f62fcdd806fd": "9a4a033c73f307122b7cbabb13fcf0649ab410ed9cf2474e740e6e463ee2e286",
    "5ac2ecc1-1f2e-413f-b3da-d6cc8463fea9": "0f580268d5f6ba7baba31087b7fa1acaa6bd27b594962cd94859bc1fb45db6c5",
    "9622f400-e8c6-4c9c-a660-1eeb6300913e": "54b8c7832c887fd182db875bd2deb9fd7d577b152b62e121906265b76fa73bf1",
    "138a7daf-e2f7-4640-a59c-3833ba4fc5f0": "d6917097baeff34e242696b628e22888d268e96ba873a69fd6cc7614c2e9d655",
    "1aeac0e3-80de-4749-ae76-1b3c1a4668e4": "7edc89803725710711e8f1ccebc1b38f38c5fd07194ccbfae87d1aa9f6a7ad88",
    "8c3fbd04-1098-423b-bbbe-27b0f6dc4bdb": "27b4f29ca24b5a5e915499fa90f35be20075aa1eea44da1754c18c3052cccf1f",
    "9a4f61cc-cdbc-41b2-8946-f385b2d44eb5": "1423b23306762fc7289f7d44e02334f0257c0c5b294c8c98937031c4e4343377",
    "cab148c1-a14a-495d-9caf-da41884d028e": "5d2270c2497817c9f7f7178247637e999930bff6dbff02d87c3cf8dba2eb05f9",
}

ALDA_ID = SESSION_ONE_REFERENCE_IDS[0]
DAST_ID = SESSION_ONE_REFERENCE_IDS[1]
INA_ID = SESSION_ONE_REFERENCE_IDS[5]
SEN_ID = SESSION_ONE_REFERENCE_IDS[9]
HALL_ID = SESSION_TWO_REFERENCE_IDS[0]
BELL_ID = SESSION_TWO_REFERENCE_IDS[6]
WATERS_ID = SESSION_TWO_REFERENCE_IDS[7]
PINS_ID = SESSION_TWO_REFERENCE_IDS[10]


def _without_reference_layer() -> str:
    payload = json.loads((SWINE_ROOT / "adventure.json").read_text(encoding="utf-8"))
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
    payload = json.loads((SWINE_ROOT / "adventure.json").read_text(encoding="utf-8"))
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


def test_swine_extraction_i_records_and_links_remain_exact_prefixes() -> None:
    adventure = load_adventure(SWINE_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references[:10]) == (
        SESSION_ONE_REFERENCE_IDS
    )
    assert _session_one_prefix_hash() == (
        "bf13eebcc836de6f0a8499d3b967e65fb234dde0c2b236280a780c37142ad371"
    )
    for reference_id in SESSION_ONE_REFERENCE_IDS:
        assert hashlib.sha256(references[reference_id].content.encode()).hexdigest() == (
            SESSION_ONE_BODY_HASHES[reference_id]
        )

    counts: Counter[str] = Counter()
    for encounter in adventure.encounters:
        prefix = SESSION_ONE_LINKS[encounter.id]
        actual = tuple(
            link.reference_id for link in encounter.reference_links[: len(prefix)]
        )
        assert actual == prefix
        counts.update(actual)
    assert sum(counts.values()) == 48


def test_swine_extraction_ii_records_and_links_are_bounded_and_ordered() -> None:
    adventure = load_adventure(SWINE_ROOT / "adventure.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references) == REFERENCE_IDS
    assert tuple(reference.kind for reference in adventure.references) == (
        *("person",) * 10,
        *("place",) * 7,
        *("organization",) * 3,
        "object",
    )
    assert all(UUID(reference.id).version == 4 for reference in adventure.references)
    assert references[HALL_ID].aliases == (
        "Hall of Petitions",
        "the Hall",
        "Veyr council house",
    )
    assert references[BELL_ID].aliases == (
        "The Deep Bell",
        "Deep Bell",
        "Six-Line Bell",
        "the Bell",
    )
    assert references[WATERS_ID].aliases == (
        "Office of Waters",
        "Water Office",
        "Waters",
    )
    assert references[PINS_ID].aliases == (
        "sounding pins",
        "field pins",
        "bronze markers",
        "survey pins",
    )

    counts: Counter[str] = Counter()
    for encounter in adventure.encounters:
        actual = tuple(link.reference_id for link in encounter.reference_links)
        assert actual == EXPECTED_LINKS[encounter.id]
        for link in encounter.reference_links:
            counts[link.reference_id] += 1
            assert link.context
            assert "Ashlar Company" not in link.context
            assert "five-line retuning" not in link.context
    assert dict(counts) == EXPECTED_COUNTS
    assert sum(counts.values()) == 111

    forbidden = (
        "Mara",
        "Nell",
        "Orris",
        "Sera Dain",
        "Dast is under guard",
        "Southgate line is isolated",
        "five-line retuning",
        "the pigs have survived",
        "Tamar has been rescued",
    )
    boundary_phrases = {
        SESSION_TWO_REFERENCE_IDS[0]: "The Hall does not carry its own case",
        SESSION_TWO_REFERENCE_IDS[1]: "The yards do not preserve a herd",
        SESSION_TWO_REFERENCE_IDS[2]: "A result survives through particular apparatus",
        SESSION_TWO_REFERENCE_IDS[3]: "The lines do not turn households",
        SESSION_TWO_REFERENCE_IDS[4]: "The crypt keeps doctrine, not present permission",
        SESSION_TWO_REFERENCE_IDS[5]: "A station diagram cannot say",
        SESSION_TWO_REFERENCE_IDS[6]: "The sheet names the chamber and three approaches",
        SESSION_TWO_REFERENCE_IDS[7]: "An office chart cannot make today's order executable",
        SESSION_TWO_REFERENCE_IDS[8]: "The Compact can mobilize commerce",
        SESSION_TWO_REFERENCE_IDS[9]: "The dissolved office leaves methods, not command",
        SESSION_TWO_REFERENCE_IDS[10]: "A pin matters where it is found",
    }
    for reference_id in SESSION_TWO_REFERENCE_IDS:
        reference = references[reference_id]
        text = reference.summary + "\n" + reference.content
        for phrase in forbidden:
            assert phrase not in text
        assert boundary_phrases[reference_id] in reference.content
        assert hashlib.sha256(reference.content.encode()).hexdigest() == (
            SESSION_TWO_BODY_HASHES[reference_id]
        )

    assert validate_adventure(adventure).is_valid


def test_swine_reference_layer_is_semantically_additive() -> None:
    adventure_path = SWINE_ROOT / "adventure.json"
    state_path = SWINE_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)

    assert _without_reference_layer() == (
        "6a809cd7bb95682972425f1e9d8430bbac69266659c67f4cc740075e96b0ffe2"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "4507a3cb7ed4312251e1d9a6cf3c107b8783969a2d906bbf4ce88004b2b06387"
    )
    assert len(adventure.encounters) == 7
    assert len(adventure.revelations) == 10
    assert sum(revelation.required for revelation in adventure.revelations) == 9
    assert len(adventure.clues) == 38
    assert len(adventure.references) == 21
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 111
    assert len(state.events) == 96
    assert validate_adventure(adventure).edge_connectivity == 3

    final_encounter = adventure.encounter_index()["the-deep-bell"]
    assert final_encounter.title == "The Six-Line Bell"
    assert final_encounter.end


def test_swine_voice_iii_repairs_only_the_documented_seams() -> None:
    adventure_path = SWINE_ROOT / "adventure.json"
    state_path = SWINE_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    encounters = adventure.encounter_index()
    references = adventure.reference_index()

    expected_encounter_hashes = {
        "the-hall-of-petitions": "971753b43561d7ba88d41d3896058b57f530aa4ad0f67b79d34dc78d4fce8e2b",
        "southgate-stockyards": "ab05bba1a75b605f0fe7be9ca2a8c616f670020d0d20f187a2e8599717d1814d",
        "the-college-of-civic-measure": "407b222813c1eaf2d640beb28067fa883763aea94f84d55eceb90183ab3d4aaf",
        "rillcross-farm-belt": "568e0f52c16fbe633c3be8bbd165688f224267ee3df6b86cb30228a1fbb0a245",
        "the-chapel-of-the-first-survey": "3a8100d784fda04bd43cf2b01486e77b1bfd550a1baee6c9f6c0283ad1c2f7b7",
        "the-nine-mile-pump-house": "2f2a26816d3904ab31e60526cc0a8a182c474b844128a84c8828a62536fb2c13",
        "the-deep-bell": "edb2c9e1560230cb2a2f541117e7680011b619727c6d6c12a49176338f5dff89",
    }
    expected_reference_hashes = {
        **SESSION_ONE_BODY_HASHES,
        **SESSION_TWO_BODY_HASHES,
    }

    for encounter_id, expected_hash in expected_encounter_hashes.items():
        actual = hashlib.sha256(encounters[encounter_id].content.encode()).hexdigest()
        assert actual == expected_hash
    for reference_id, expected_hash in expected_reference_hashes.items():
        actual = hashlib.sha256(references[reference_id].content.encode()).hexdigest()
        assert actual == expected_hash

    assert sum(len(item.content.split()) for item in adventure.encounters) == 5592
    assert sum(len(item.content.split()) for item in adventure.references) == 4405
    assert sum(len(item.content.split()) for item in adventure.references[:10]) == 1984
    assert sum(len(item.content.split()) for item in adventure.references[10:]) == 2421
    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "6a444141754d0d01bc32c60d57550d8fcea6e1bf5f6681715967e0037b0c9032"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "4507a3cb7ed4312251e1d9a6cf3c107b8783969a2d906bbf4ce88004b2b06387"
    )

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
        "97311c5f1faaa1f7d1a5406981404be71c213ad42c190679e897b7eb5086060e"
    )

    expected_live_seams = {
        "the-hall-of-petitions": (
            "Two dead piglets and a rooted bronze pin reach the signing table"
        ),
        "southgate-stockyards": (
            "Several thousand Convocation pigs refuse one line through the eastern pens"
        ),
        "the-college-of-civic-measure": (
            "Quill's pendulums have turned south inside the sealed laboratory"
        ),
        "rillcross-farm-belt": "Quarantine boards rise at six lanes",
        "the-chapel-of-the-first-survey": "Water lifts through the crypt joints",
        "the-nine-mile-pump-house": "Nine-Mile is under uninterrupted high load",
        "the-deep-bell": "The company reaches only the controls its route exposes",
    }
    for encounter_id, phrase in expected_live_seams.items():
        assert phrase in encounters[encounter_id].content

    retired_repetition = {
        "the-hall-of-petitions": (
            "The Hall of Petitions occupies the ground floor"
        ),
        "southgate-stockyards": "Southgate Stockyards presses pens",
        "the-college-of-civic-measure": (
            "The College of Civic Measure certifies Veyr's weights"
        ),
        "rillcross-farm-belt": "Rillcross is a belt of holdings",
        "the-chapel-of-the-first-survey": (
            "The Chapel of the First Survey stands on a low rise"
        ),
        "the-nine-mile-pump-house": "The Nine-Mile Pump House straddles",
        "the-deep-bell": "The Deep Bell hangs in a chamber older than most of Veyr",
    }
    for encounter_id, phrase in retired_repetition.items():
        assert phrase not in encounters[encounter_id].content

    for reference_id in SESSION_ONE_REFERENCE_IDS:
        actual = hashlib.sha256(references[reference_id].content.encode()).hexdigest()
        assert actual == SESSION_ONE_BODY_HASHES[reference_id]
    for reference_id in SESSION_TWO_REFERENCE_IDS:
        assert "remain live" not in references[reference_id].content
        assert "remain play state" not in references[reference_id].content

    final_encounter = encounters["the-deep-bell"]
    assert final_encounter.title == "The Six-Line Bell"
    assert final_encounter.end


def test_swine_coherence_iii_closes_the_sequence_without_canonical_change() -> None:
    adventure_path = SWINE_ROOT / "adventure.json"
    state_path = SWINE_ROOT / "play-state.example.json"
    adventure = load_adventure(adventure_path)
    state = load_play_state(state_path)
    encounters = adventure.encounter_index()
    revelations = adventure.revelation_index()

    assert hashlib.sha256(adventure_path.read_bytes()).hexdigest() == (
        "6a444141754d0d01bc32c60d57550d8fcea6e1bf5f6681715967e0037b0c9032"
    )
    assert hashlib.sha256(state_path.read_bytes()).hexdigest() == (
        "4507a3cb7ed4312251e1d9a6cf3c107b8783969a2d906bbf4ce88004b2b06387"
    )
    assert len(adventure.encounters) == 7
    assert len(adventure.revelations) == 10
    assert sum(revelation.required for revelation in adventure.revelations) == 9
    assert len(adventure.clues) == 38
    assert len(adventure.references) == 21
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 111
    assert len(state.events) == 96
    assert len(state.active_events) == 96
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
        "97311c5f1faaa1f7d1a5406981404be71c213ad42c190679e897b7eb5086060e"
    )

    source_encounters: dict[str, set[str]] = {
        revelation.id: set()
        for revelation in adventure.revelations
        if revelation.required
    }
    for clue in adventure.clues:
        if clue.revelation_id in source_encounters:
            source_encounters[clue.revelation_id].add(clue.source_encounter_id)
    assert len(source_encounters) == 9
    assert {len(sources) for sources in source_encounters.values()} == {3, 5, 6}
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

    reached = {"the-hall-of-petitions"}
    frontier = ["the-hall-of-petitions"]
    while frontier:
        source = frontier.pop()
        for target in directed_edges[source] - reached:
            reached.add(target)
            frontier.append(target)
    assert reached == set(encounters)
    assert directed_edges["the-hall-of-petitions"] >= {
        "southgate-stockyards",
        "the-college-of-civic-measure",
        "rillcross-farm-belt",
    }
    assert {
        clue.source_encounter_id
        for clue in adventure.clues
        if clue.revelation_id == "the-deep-bell-lies-beneath-veyr"
    } == {
        "rillcross-farm-belt",
        "the-chapel-of-the-first-survey",
        "the-nine-mile-pump-house",
    }

    live_state_phrases = {
        "the-hall-of-petitions": (
            "Alda's first writ lasts one resonance cycle",
            "These powers remain provisional",
            "Delegation creates vulnerable parallel action",
        ),
        "southgate-stockyards": (
            "Poleaxes are being issued.",
            "Observation requires space made by work",
            "Southgate should leave behind control or loss of the gates",
        ),
        "the-college-of-civic-measure": (
            "The result becomes usable only if the apparatus, trace, witnesses, "
            "and a College signature survive the seizure.",
            "Information already made observable remains available to those who saw it.",
            "letting the cart depart moves that evidence to Nine-Mile rather than deleting it.",
        ),
        "rillcross-farm-belt": (
            "three linked sites within a compact landscape",
            "A method, assigned line, agreed signal, and protection from immediate seizure",
            "Confiscation, panic, broken roads, or a worsening line can still silence them.",
        ),
        "the-chapel-of-the-first-survey": (
            "Anja will not open the founder's tomb without terms for custody, "
            "attribution, copies, and the handling of human remains.",
            "Named chapel teams can copy, dry, and interpret records while the company moves",
            "Neither archive can operate the system alone.",
        ),
        "the-nine-mile-pump-house": (
            "A lawful transfer still requires Thane to recognize the order and Salk "
            "or another competent engineer to accept an executable sequence.",
            "Removing him transfers those four functions separately rather than "
            "pretending one replacement inherits his whole office.",
            "subject to injury, lost contact, or renewed orders.",
        ),
        "the-deep-bell": (
            "The company reaches only the controls its route exposes",
            "Keep at least one means of communication visible",
            "There is no fixed allotment of three cycles",
            "Every line must be heard; every line need not survive.",
            "Permanent water governance and criminal judgment come later.",
        ),
    }
    for encounter_id, phrases in live_state_phrases.items():
        for phrase in phrases:
            assert phrase in encounters[encounter_id].content

    reference_text = "\n".join(
        reference.summary + "\n" + reference.content
        for reference in adventure.references
    )
    demonstrated_states = (
        "Alda Mere issued the Ashlar Company a narrow written commission",
        "The eastern herd survived",
        "Ina Rill and the farm families maintain a six-holding observation relay",
        "The College preserved its archive and calibration instruments",
        "Tamar Vey and Oren Salk hold operational command of Nine-Mile",
        "Corven Dast remains under Captain Thane's guard as a technical adviser",
        "Five sounding lines were retuned",
        "The failing Southgate line was isolated and remains permanently dead",
        "A public return hearing will examine Dast's concealment",
    )
    for demonstrated_state in demonstrated_states:
        assert demonstrated_state not in reference_text

    projection = project_play_state(adventure, state)
    consequences = "\n".join(
        consequence.text for consequence in projection.consequences
    )
    for demonstrated_state in demonstrated_states:
        assert demonstrated_state in consequences
    assert len(projection.visits) == 8
    assert len(projection.spotted_clue_ids) == 25
    assert len(projection.corrections) == 0
    assert len(projection.consequences) == 18
    assert all(item.is_established for item in projection.revelation_progress)


    documents = render_adventure_documents(
        adventure,
        validate_adventure(adventure),
        state,
    )
    assert len(documents) == 35
    assert_rendered_documents_match(
        documents, SWINE_ROOT / "generated"
    )


def test_swine_reference_views_are_retrievable_and_journal_neutral() -> None:
    adventure = load_adventure(SWINE_ROOT / "adventure.json")
    state = load_play_state(SWINE_ROOT / "play-state.example.json")

    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    for title in (
        "First Deputy Clerk Alda Mere",
        "Master of Waters Corven Dast",
        "The Hall of Condemnations",
        "Southgate Stockyards",
        "The College of Civic Measure",
        "Rillcross Farm Belt",
        "The Chapel of the First Survey",
        "The Nine-Mile Pump House",
        "The Six-Line Bell",
        "The Office of Waters",
        "The Slaughterers&#x27; Compact",
        "The First Survey",
        "Bronze Sounding Pins",
    ):
        assert title in library

    status, _, detail = request_wsgi(author_app, f"/references/{WATERS_ID}")
    assert status == "200 OK"
    for title in (
        "The Hall of Condemnations",
        "Southgate Stockyards",
        "The College of Civic Measure",
        "Rillcross Farm Belt",
        "The Chapel of the First Survey",
        "The Nine-Mile Pump House",
        "The Six-Line Bell",
    ):
        assert title in detail

    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, body = request_wsgi(
        play_app,
        "/play",
        query=urlencode({"encounter": "the-deep-bell", "reference": BELL_ID}),
    )
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{BELL_ID}"' in body
    assert "The Six-Line Bell" in body
    assert project.snapshot == before


def test_swine_packet_adds_reference_views_without_changing_demonstration() -> None:
    adventure = load_adventure(SWINE_ROOT / "adventure.json")
    state = load_play_state(SWINE_ROOT / "play-state.example.json")
    documents = render_adventure_documents(
        adventure,
        validate_adventure(adventure),
        state,
    )

    assert len(documents) == 35
    assert "## People" in documents["references/index.md"]
    assert "## Places" in documents["references/index.md"]
    assert "## Organizations" in documents["references/index.md"]
    assert "## Objects" in documents["references/index.md"]
    for reference_id in REFERENCE_IDS:
        assert f"references/{reference_id}.md" in documents
    assert_rendered_documents_match(
        documents, SWINE_ROOT / "generated"
    )


