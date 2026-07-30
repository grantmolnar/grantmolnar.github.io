"""Aurelune reference-library corpus and portability evidence."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

import pytest

from adventure_graph.application.archive_management import JournalArchiveSnapshot
from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure, save_adventure
from adventure_graph.infrastructure.journal_archive_store import (
    load_journal_archive,
    save_archive_and_reset,
)
from adventure_graph.infrastructure.play_state_store import load_play_state, save_play_state
from tests.support.web import build_authoring_app, build_play_app, request_wsgi

pytestmark = pytest.mark.corpus

CONCORD_ROOT = Path("examples/the-concord-of-aurelune")

THERON_ID = "97bd3a99-1a45-45ad-9d0d-ffd1418e6db9"
SUNSEED_ID = "eb53de5a-93b2-4383-bd1a-0adbd6fb0b93"
CAELIR_ID = "e6b95d47-51e1-4be3-9ee3-901d903e1254"
MARA_VENN_ID = "9b4e0d4c-ff0d-4ab6-a045-1467020b73df"
YSANDRE_SERATHIEL_ID = "2c1e9617-655b-47d5-adca-d8710d016456"
MIRELLE_ORELLE_ID = "51f114d4-1818-4465-95be-3124ec3faa39"
PELION_NAMARIS_ID = "9f9b61d5-545c-4a2d-875a-283c191a4594"
CALDUS_SEREVIN_ID = "39900332-f46e-4c17-9c27-4ef56995f6ac"
ORISON_ID = "ef010fba-64a6-4f48-b912-c6a1867db6f8"
ASHEN_BOUGH_ID = "7b0624aa-9728-4a8f-aa8f-5c70e68b5560"
PALL_ID = "f837f83d-51fd-43ea-872c-44d96ba9beb7"
CONCORD_OF_OPEN_HANDS_ID = "f92c1071-7366-4f0b-b3e1-298d3e2d2a45"
UNBROKEN_WORD_ID = "d91a965f-f0d9-42dc-9257-f2f430f81a1f"
LANTERN_ROAD_COMPACT_ID = "6d94f652-9012-4baa-a80b-dc9c474c30bc"

CONCORD_REFERENCE_IDS = (
    THERON_ID,
    SUNSEED_ID,
    CAELIR_ID,
    MARA_VENN_ID,
    YSANDRE_SERATHIEL_ID,
    MIRELLE_ORELLE_ID,
    PELION_NAMARIS_ID,
    CALDUS_SEREVIN_ID,
    ORISON_ID,
    ASHEN_BOUGH_ID,
    PALL_ID,
    CONCORD_OF_OPEN_HANDS_ID,
    UNBROKEN_WORD_ID,
    LANTERN_ROAD_COMPACT_ID,
)

CONCORD_REFERENCE_LINK_COUNTS = {
    THERON_ID: 6,
    SUNSEED_ID: 7,
    CAELIR_ID: 8,
    MARA_VENN_ID: 6,
    YSANDRE_SERATHIEL_ID: 3,
    MIRELLE_ORELLE_ID: 3,
    PELION_NAMARIS_ID: 3,
    CALDUS_SEREVIN_ID: 4,
    ORISON_ID: 8,
    ASHEN_BOUGH_ID: 3,
    PALL_ID: 7,
    CONCORD_OF_OPEN_HANDS_ID: 6,
    UNBROKEN_WORD_ID: 4,
    LANTERN_ROAD_COMPACT_ID: 4,
}


def test_concord_retains_complete_reference_library_without_replacing_ledgers() -> None:
    adventure = load_adventure(CONCORD_ROOT / "adventure.json")
    state = load_play_state(CONCORD_ROOT / "play-state.example.json")
    references = adventure.reference_index()

    assert tuple(reference.id for reference in adventure.references) == CONCORD_REFERENCE_IDS
    assert tuple(reference.kind for reference in adventure.references) == (
        "person",
        "object",
        "person",
        "person",
        "person",
        "person",
        "person",
        "person",
        "place",
        "organization",
        "other",
        "other",
        "other",
        "other",
    )
    assert references[THERON_ID].aliases == (
        "Lord Chamberlain Theron Eiral",
        "Chamberlain Theron",
    )
    assert references[SUNSEED_ID].kind == "object"
    assert references[CAELIR_ID].aliases == ("Caelir III", "Caelir")
    assert "cannot veto a valid Concord" in references[CAELIR_ID].content
    assert references[MARA_VENN_ID].aliases == ("Mara Venn", "Mara")
    assert "does not replace seven banner seals" in references[MARA_VENN_ID].content
    assert references[YSANDRE_SERATHIEL_ID].aliases == (
        "Ysandre Serathiel",
        "Ysandre",
        "Marshal Serathiel",
    )
    assert (
        "does not by itself confer authority over Orison"
        in references[YSANDRE_SERATHIEL_ID].content
    )
    assert "Loss for what is consumed" in references[MIRELLE_ORELLE_ID].content
    assert "does not certify the Concord" in references[PELION_NAMARIS_ID].content
    assert (
        "cannot recall the Sunseed merely because he fears" in references[CALDUS_SEREVIN_ID].content
    )
    assert references[ORISON_ID].kind == "place"
    assert "does not predefine a fresh delegation" in references[ORISON_ID].content
    assert references[ASHEN_BOUGH_ID].kind == "organization"
    assert "Lady Mirath Avarre" in references[ASHEN_BOUGH_ID].content
    assert "Aven Tal" in references[ASHEN_BOUGH_ID].content
    assert "current holder" in references[ASHEN_BOUGH_ID].content
    assert "Court Day Seven" in references[PALL_ID].content
    assert (
        "royal joinder improves cooperation without creating validity"
        in references[CONCORD_OF_OPEN_HANDS_ID].content
    )
    assert "does not require relevance, completeness" in references[UNBROKEN_WORD_ID].content
    assert (
        "does not recognize Orison as Aurelune's treaty equal"
        in references[LANTERN_ROAD_COMPACT_ID].content
    )
    expected_headings = {
        THERON_ID: (
            "One robe, two rings",
            "What the black desk must certify",
            "What the laurel table wants",
        ),
        SUNSEED_ID: (
            "Dawn beneath the throne",
            "The road closes before custody begins",
            "What uprooting places at risk",
        ),
        CAELIR_ID: (
            "The trust beneath his throne",
            "Six days under the Crown",
            "What seven banners can compel",
        ),
        MARA_VENN_ID: (
            "A sealed commission and a black-frosted stone",
            "What Orison may accept",
            "The promise a changed word releases",
        ),
        YSANDRE_SERATHIEL_ID: (
            "Every mercy needs an order",
            "Route, guard, tempo, return",
            "What she yields before command",
        ),
        MIRELLE_ORELLE_ID: (
            "Loss, Capital, Advantage",
            "What her ledgers make executable",
            "Every bearer and benefit named",
        ),
        PELION_NAMARIS_ID: (
            "The later case waits in the index",
            "What the amber quills can separate",
            "Words that survive their authors",
        ),
        CALDUS_SEREVIN_ID: (
            "Needles against the old rings",
            "What the eastern watch may command",
            "A breach that can be measured",
        ),
        ORISON_ID: (
            "A city under a failing sky",
            "Standing without wardship",
            "Which city survives the rescue",
        ),
        ASHEN_BOUGH_ID: (
            "One empty chair, two true claims",
            "Six banners, five banners, or none",
            "What judgment may and may not settle",
        ),
        PALL_ID: (
            "Dusk after the host has gone",
            "The ring closes at moonrise",
            "Which rescue the Sunseed performs",
        ),
        CONCORD_OF_OPEN_HANDS_ID: (
            "Seven seals and every season",
            "Seal, certification, acceptance, joinder",
            "What a changed word releases",
        ),
        UNBROKEN_WORD_ID: (
            "The leaves turn toward the speaker",
            "Truth without completeness",
            "What mirrors and seals preserve",
        ),
        LANTERN_ROAD_COMPACT_ID: (
            "An audience and one Crown Passage",
            "Standing is not sovereignty",
            "The road closes before the loan begins",
        ),
    }
    for reference_id, headings in expected_headings.items():
        assert (
            tuple(
                line.removeprefix("## ")
                for line in references[reference_id].content.splitlines()
                if line.startswith("## ")
            )
            == headings
        )

    encounters = adventure.encounter_index()
    assert (
        "black grain from her palm across three open books"
        in encounters["the-golden-sheaf-exchange"].content
    )
    assert (
        "sets an eighth cup beside the king's"
        in encounters["the-twilight-laurel-apartments"].content
    )
    assert "three instruments beneath the branch" in encounters["the-ashen-bough-hearing"].content
    assert (
        "orders disappear when two dangers arrive at once"
        in encounters["the-noon-spear-court"].content
    )
    assert not {
        "Lady Saelira Ilyrion",
        "Prince-Regent Othalan Maelith",
        "Lord Avar Vaudren",
        "Duchess Eirath Thalan",
        "Lady Mirath Avarre",
        "Aven Tal",
    } & {reference.title for reference in adventure.references}

    actual_link_counts = dict.fromkeys(CONCORD_REFERENCE_IDS, 0)
    for encounter in adventure.encounters:
        for link in encounter.reference_links:
            actual_link_counts[link.reference_id] += 1
    assert actual_link_counts == CONCORD_REFERENCE_LINK_COUNTS
    assert sum(actual_link_counts.values()) == 72
    assert sum(bool(encounter.reference_links) for encounter in adventure.encounters) == 13

    argent_links = adventure.encounter_index()["the-argent-canopy"].reference_links
    assert tuple(link.reference_id for link in argent_links) == (
        CAELIR_ID,
        MARA_VENN_ID,
        THERON_ID,
        CONCORD_OF_OPEN_HANDS_ID,
        UNBROKEN_WORD_ID,
        LANTERN_ROAD_COMPACT_ID,
        ORISON_ID,
        PALL_ID,
        SUNSEED_ID,
    )
    assert "six-day Crown expedition" in argent_links[0].context
    assert "emergency mandate" in argent_links[1].context
    assert "separates certification" in argent_links[2].context
    assert "seven-seal" in argent_links[3].context
    assert "knowing falsehood" in argent_links[4].context
    assert "passage deadline" in argent_links[-1].context

    chamber_links = adventure.encounter_index()[
        "the-chamber-of-the-fourfold-petition"
    ].reference_links
    assert tuple(link.reference_id for link in chamber_links) == (
        THERON_ID,
        PELION_NAMARIS_ID,
        CONCORD_OF_OPEN_HANDS_ID,
        UNBROKEN_WORD_ID,
        LANTERN_ROAD_COMPACT_ID,
        MARA_VENN_ID,
        YSANDRE_SERATHIEL_ID,
        MIRELLE_ORELLE_ID,
        CALDUS_SEREVIN_ID,
        ORISON_ID,
        CAELIR_ID,
        PALL_ID,
        SUNSEED_ID,
    )

    author_app, _ = build_authoring_app(adventure)
    status, _, library = request_wsgi(author_app, "/references")
    assert status == "200 OK"
    theron_href = f'href="/references/{THERON_ID}"'
    sunseed_href = f'href="/references/{SUNSEED_ID}"'
    mara_href = f'href="/references/{MARA_VENN_ID}"'
    ysandre_href = f'href="/references/{YSANDRE_SERATHIEL_ID}"'
    caldus_href = f'href="/references/{CALDUS_SEREVIN_ID}"'
    orison_href = f'href="/references/{ORISON_ID}"'
    ashen_href = f'href="/references/{ASHEN_BOUGH_ID}"'
    pall_href = f'href="/references/{PALL_ID}"'
    assert library.index(theron_href) < library.index(sunseed_href)
    assert library.index(mara_href) < library.index(ysandre_href)
    assert library.index(caldus_href) < library.index(orison_href)
    assert library.index(ashen_href) < library.index(pall_href)
    status, _, detail = request_wsgi(author_app, f"/references/{UNBROKEN_WORD_ID}")
    assert status == "200 OK"
    assert "the court does not secretly lie around it" in detail
    assert "The Masque of Plain Faces" in detail

    play_app, project = build_play_app(adventure, state)
    before = project.snapshot
    status, _, play = request_wsgi(
        play_app,
        "/play",
        query=urlencode(
            {
                "encounter": "the-chamber-of-the-fourfold-petition",
                "reference": CONCORD_OF_OPEN_HANDS_ID,
            }
        ),
    )
    assert status == "200 OK"
    assert f'data-play-selected-reference-id="{CONCORD_OF_OPEN_HANDS_ID}"' in play
    linked = play.split('id="encounter-references"', 1)[1].split("</section>", 1)[0]
    assert linked.index("Theron Eiral") < linked.index("Archivist-Lord Pelion Namaris")
    assert linked.index("Archivist-Lord Pelion Namaris") < linked.index("The Concord of Open Hands")
    assert linked.index("The Concord of Open Hands") < linked.index("The Oath of the Unbroken Word")
    assert "governs material amendments" in linked.lower()
    assert "open hands" in play.lower()
    assert project.snapshot == before

    documents = render_adventure_documents(adventure, validate_adventure(adventure))
    assert "references/index.md" in documents
    assert len([name for name in documents if name.startswith("references/")]) == 15
    for reference_id in CONCORD_REFERENCE_IDS:
        sheet_name = f"references/{reference_id}.md"
        assert sheet_name in documents
        assert documents[sheet_name] == (
            CONCORD_ROOT / "generated" / "references" / f"{reference_id}.md"
        ).read_text(encoding="utf-8")
    index = documents["references/index.md"]
    assert index.index("## People") < index.index("## Places")
    assert index.index("## Places") < index.index("## Organizations")
    assert index.index("## Organizations") < index.index("## Objects")
    assert index.index("## Objects") < index.index("## Other")


def test_populated_sample_survives_relocation_clean_export_and_archive(
    tmp_path: Path,
) -> None:
    adventure = load_adventure(CONCORD_ROOT / "adventure.json")
    state = load_play_state(CONCORD_ROOT / "play-state.example.json")

    relocated = tmp_path / "relocated"
    relocated.mkdir()
    relocated_adventure = relocated / "adventure.json"
    relocated_state = relocated / "play-state.json"
    save_adventure(relocated_adventure, adventure)
    save_play_state(relocated_state, state)
    assert load_adventure(relocated_adventure) == adventure
    assert load_play_state(relocated_state) == state

    standalone = tmp_path / "standalone-adventure.json"
    save_adventure(standalone, load_adventure(relocated_adventure))
    exported = load_adventure(standalone)
    assert tuple(reference.id for reference in exported.references) == CONCORD_REFERENCE_IDS
    assert tuple(
        link.reference_id
        for link in exported.encounter_index()["the-argent-canopy"].reference_links
    ) == (
        CAELIR_ID,
        MARA_VENN_ID,
        THERON_ID,
        CONCORD_OF_OPEN_HANDS_ID,
        UNBROKEN_WORD_ID,
        LANTERN_ROAD_COMPACT_ID,
        ORISON_ID,
        PALL_ID,
        SUNSEED_ID,
    )

    archive = JournalArchiveSnapshot(
        archive_id="reference-corpus-sample",
        label="Reference corpus sample",
        archived_at="2026-07-25T12:00:00Z",
        source_state_name=relocated_state.name,
        adventure_snapshot=exported,
        play_state=state,
    )
    archive_path = tmp_path / "reference-corpus-sample.journal.json"
    save_archive_and_reset(
        archive_path,
        archive,
        relocated_state,
        new_play_state(exported),
    )
    loaded_archive = load_journal_archive(archive_path)
    assert (
        tuple(reference.id for reference in loaded_archive.adventure_snapshot.references)
        == CONCORD_REFERENCE_IDS
    )
    assert tuple(
        link.reference_id
        for link in loaded_archive.adventure_snapshot.encounter_index()[
            "the-argent-canopy"
        ].reference_links
    ) == (
        CAELIR_ID,
        MARA_VENN_ID,
        THERON_ID,
        CONCORD_OF_OPEN_HANDS_ID,
        UNBROKEN_WORD_ID,
        LANTERN_ROAD_COMPACT_ID,
        ORISON_ID,
        PALL_ID,
        SUNSEED_ID,
    )
    assert load_play_state(relocated_state).events == ()


def test_concord_coherence_iii_closes_the_library_without_freezing_play() -> None:
    adventure = load_adventure(CONCORD_ROOT / "adventure.json")
    state_path = CONCORD_ROOT / "play-state.example.json"

    required_revelation_ids = {
        revelation.id for revelation in adventure.revelations if revelation.required
    }
    sources_by_revelation: dict[str, set[str]] = {
        revelation_id: set() for revelation_id in required_revelation_ids
    }
    for clue in adventure.clues:
        if clue.revelation_id in sources_by_revelation:
            sources_by_revelation[clue.revelation_id].add(clue.source_encounter_id)
    for skipped in adventure.encounters:
        assert min(len(sources - {skipped.id}) for sources in sources_by_revelation.values()) >= 4

    assert len(state_path.read_text(encoding="utf-8")) > 0


