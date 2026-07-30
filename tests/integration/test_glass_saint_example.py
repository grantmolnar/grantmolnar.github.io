"""Regression checks for the expanded Glass Saint initialization adventure."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.infrastructure.adventure_store import load_adventure
from tests.integration.glass_saint_support import (
    DIRECTORY_ADVENTURE_PATH,
    EXAMPLE_PATH,
    MANOR_SHEET_PATH,
    PUBLIC_LEDGER_PATH,
    RESOURCE_PATH,
    RITUAL_SHEET_PATH,
    ROUTE_SHEET_PATH,
)

pytestmark = pytest.mark.corpus


def test_glass_saint_expansion_forms_a_full_material_public_and_moral_chain() -> None:
    """Protect the expanded authority, witness, ritual, bell, and finale architecture."""
    adventure = load_adventure(EXAMPLE_PATH)
    report = validate_adventure(adventure)
    encounters = adventure.encounter_index()

    assert report.is_valid
    assert report.edge_connectivity == 5
    assert len(adventure.encounters) == 9
    assert len(adventure.revelations) == 16
    assert len(adventure.clues) == 69
    assert "emergency witness charter" in adventure.premise
    assert "procession court" in adventure.premise
    assert "Assistant conservator Tavia Sorn joined him" in adventure.explanation
    assert "The rite joins four materials" in adventure.explanation
    assert "The investigation contests who may make a fact public" in adventure.explanation

    assert "The painted bone copy remains strapped" in encounters["the-shattered-gallery"].content
    assert (
        "The city gets the words before you get the bell"
        in encounters["the-procession-court"].content
    )
    assert "credible and materially significant" in encounters["the-archive-vault"].content
    assert (
        "Build the hearing from four kinds of proof" in encounters["the-trustees-chamber"].content
    )
    assert "will not be commanded by her image" in encounters["the-west-infirmary"].content
    assert "carries more than names" in encounters["the-house-of-petitions"].content
    assert "The rehearsal still answers" in encounters["the-bell-chapel"].content
    assert (
        "The three live pins remain **witness**, **mouth**, and **crown**"
        in encounters["the-grand-belfry"].content
    )
    assert (
        "**The three notes borrow body, voice, and reach in order.**"
        in encounters["vale-manor"].content
    )
    assert "**What survives decides the ending.**" in encounters["vale-manor"].content


def test_glass_saint_expansion_keeps_routes_irregular_mirrored_and_documented() -> None:
    """Keep the full graph, initialized identifiers, resource mirror, and roadmap synchronized."""
    adventure = load_adventure(EXAMPLE_PATH)
    clues_by_revelation = Counter(clue.revelation_id for clue in adventure.clues)
    clues_by_source = Counter(clue.source_encounter_id for clue in adventure.clues)
    revelation_index = adventure.revelation_index()
    edges = {
        (clue.source_encounter_id, revelation_index[clue.revelation_id].unlocks_encounter_id)
        for clue in adventure.clues
        if revelation_index[clue.revelation_id].unlocks_encounter_id is not None
        and clue.source_encounter_id != revelation_index[clue.revelation_id].unlocks_encounter_id
    }

    assert set(clues_by_source.values()) == {6, 7, 8, 9, 10}
    assert min(clues_by_revelation.values()) == 3
    assert max(clues_by_revelation.values()) == 7
    assert len(edges) == 35
    assert adventure.encounter_index()["the-trustees-chamber"].required is False
    assert adventure.encounter_index()["the-house-of-petitions"].required is False
    assert "accession-number-on-a-glass-shard" in adventure.clue_index()
    assert "the-archive-vault-contains-the-relics-hidden-provenance" in revelation_index
    assert EXAMPLE_PATH.read_bytes() == RESOURCE_PATH.read_bytes()
    assert EXAMPLE_PATH.read_bytes() == DIRECTORY_ADVENTURE_PATH.read_bytes()


    documents = render_adventure_documents(adventure, validate_adventure(adventure))
    expected_documents = {
        "00-overview.md",
        "01-encounter-index.md",
        "02-clue-list.md",
        "03-revelation-list.md",
        "04-validation-report.md",
        "encounters/the-archive-vault.md",
        "encounters/the-bell-chapel.md",
        "encounters/the-grand-belfry.md",
        "encounters/the-house-of-petitions.md",
        "encounters/the-procession-court.md",
        "encounters/the-shattered-gallery.md",
        "encounters/the-trustees-chamber.md",
        "encounters/the-west-infirmary.md",
        "encounters/vale-manor.md",
        "references/index.md",
    }
    expected_documents.update(f"references/{reference.id}.md" for reference in adventure.references)
    assert set(documents) == expected_documents
    assert tuple(reference.title for reference in adventure.references) == (
        "Saint Olyra",
        "Iria Vale",
        "Edrin Vale",
        "Tavia Sorn",
        "Provost Helian Dorr",
        "Captain Ors Renn",
        "Registrar Senna Drail",
        "Sister Caldra Fen",
        "Nessa Quill",
        "Bellmaster Jori Kest",
        "Alis Vale",
        "The House of Petitions",
        "The West Infirmary",
        "The Vale Winter Garden",
        "The Grand Belfry",
    )
    assert tuple(reference.id for reference in adventure.references) == (
        "8506dafa-ac5f-443d-b537-b18cb97d6f90",
        "d15869c0-3889-4f6e-aa25-b840bfea30b7",
        "b9e6abc5-6255-46a3-b218-fd7682b47e4c",
        "ded2083d-b24d-4d98-ad09-b785016fee09",
        "d656408a-6014-4c49-a264-dee525fbbfdf",
        "58de71c7-986d-42cd-ac39-511984f7fdbf",
        "0cf2cfc1-7cef-4378-b20f-0ab489c5f6de",
        "d66bca78-7d84-4a07-b7fc-224068bde904",
        "b29d5f11-8145-4c6a-b5a3-b2f97af88d1b",
        "ca4d3059-1eac-4b0b-b13b-4115e8751d38",
        "f418156c-5ad3-4a30-ac15-35051eb07a4d",
        "baf4dcd9-9f96-4099-8bab-a487cc3e93f1",
        "af698a7e-01e3-4e9b-b5cb-3ccf7830d7a2",
        "2496cf62-c44a-4a52-b1dd-8ed40244f0e5",
        "adf71e90-d724-486a-94e8-7d4e630bf82e",
    )
    assert sum(len(encounter.reference_links) for encounter in adventure.encounters) == 93
    assert "emergency witness charter" in documents["00-overview.md"]
    assert (
        "The three live pins remain **witness**, **mouth**, and **crown**"
        in documents["encounters/the-grand-belfry.md"]
    )
    assert (
        "**The three notes borrow body, voice, and reach in order.**"
        in documents["encounters/vale-manor.md"]
    )
    assert (
        "Any Glass Saint is a disputed composite assembled by the living."
        in documents["references/8506dafa-ac5f-443d-b537-b18cb97d6f90.md"]
    )
    assert (
        "He pauses for a hearing that already has public anchors"
        in documents["references/b9e6abc5-6255-46a3-b218-fd7682b47e4c.md"]
    )
    assert (
        "Every action remains bounded by the authority actually written"
        in documents["references/58de71c7-986d-42cd-ac39-511984f7fdbf.md"]
    )
    assert (
        "four caucuses argue over what the record should require"
        in documents["references/b29d5f11-8145-4c6a-b5a3-b2f97af88d1b.md"]
    )
    assert (
        "The nearest living Vale inside the outer pane circle"
        in documents["references/2496cf62-c44a-4a52-b1dd-8ed40244f0e5.md"]
    )
    assert "Mara" not in EXAMPLE_PATH.read_text()


def test_glass_saint_public_investigation_has_operational_authority_and_failure_states() -> None:
    adventure = load_adventure(EXAMPLE_PATH)
    encounters = adventure.encounter_index()

    assert "It permits independent inspection" in encounters["the-shattered-gallery"].content
    assert "fixed order makes every break visible" in encounters["the-procession-court"].content
    assert "Four packets compete" in encounters["the-archive-vault"].content
    assert (
        "Build the hearing from four kinds of proof" in encounters["the-trustees-chamber"].content
    )
    assert (
        "Caldra finishes a bandage before she discusses the record"
        in encounters["the-west-infirmary"].content
    )
    assert "Tavia is a culpable witness in motion" in encounters["the-house-of-petitions"].content
    assert "Carry five public facts from scene to scene" in adventure.explanation

    ledger = PUBLIC_LEDGER_PATH.read_text()
    for phrase in (
        "## Five public facts",
        "## Evidence custody",
        "## Proof categories and authority outputs",
        "## Fixed witness roster",
        "## Factions and breakpoints",
        "## Tavia state",
        "## Failure-forward route tests",
    ):
        assert phrase in ledger

    documents = render_adventure_documents(adventure, validate_adventure(adventure))
    assert (
        "Sort the scene into three evidence chains"
        in documents["encounters/the-shattered-gallery.md"]
    )
    assert (
        "Proof becomes authority in combinations" in documents["encounters/the-trustees-chamber.md"]
    )
    assert (
        "Tavia is a culpable witness in motion" in documents["encounters/the-house-of-petitions.md"]
    )


def test_glass_saint_ritual_and_bell_system_is_operational_and_late_actionable() -> None:
    adventure = load_adventure(EXAMPLE_PATH)
    encounters = adventure.encounter_index()
    chapel = encounters["the-bell-chapel"].content
    belfry = encounters["the-grand-belfry"].content

    for phrase in (
        "Four workings cross the nave",
        "The **counterkey** answers the rite in three pieces",
        "witness**, **mouth**, and **crown",
        "Relay pins repeat the crown note",
        "Record what survives",
    ):
        assert phrase in chapel
    for phrase in (
        "Name every hand on a rope before the first lift",
        "The crew is split across the tower",
        "The three live pins remain **witness**, **mouth**, and **crown**",
        "Choose what the bells will be allowed to do",
        "A sounded note cannot be unsounded; every later note remains contestable",
    ):
        assert phrase in belfry
    assert "Six answer-pins cast from the old infirmary bell" in adventure.explanation
    assert "Advance pressure through acts the table can see" in adventure.explanation
    assert "Neither answers information that never reaches him" in adventure.explanation

    sheet = RITUAL_SHEET_PATH.read_text()
    for heading in (
        "## The six answer-pins",
        "## Four workings in the Bell Chapel",
        "## The three-part counterkey",
        "## Hands on the Grand Belfry ropes",
        "## Event-based pressure sequence",
        "## Information channels and bounded responses",
        "## What each bell answer changes",
        "## What the bells remember",
    ):
        assert heading in sheet

    documents = render_adventure_documents(adventure, validate_adventure(adventure))
    assert (
        "The **counterkey** answers the rite in three pieces"
        in documents["encounters/the-bell-chapel.md"]
    )
    assert (
        "A sounded note cannot be unsounded; every later note remains contestable"
        in documents["encounters/the-grand-belfry.md"]
    )


def test_glass_saint_manor_finale_and_aftermath_are_stateful_and_separable() -> None:
    adventure = load_adventure(EXAMPLE_PATH)
    manor = adventure.encounter_index()["vale-manor"].content

    for phrase in (
        "Before Edrin speaks, read the city already gathered at the glass",
        "**Six ways through the doors.**",
        "**The household at the glass.**",
        "**Five joined things give the saint a body.**",
        "When the mouth note completes, the nearest living Vale inside the outer pane circle",
        "**Edrin listens only for a hearing that already exists.**",
        "**The three notes borrow body, voice, and reach in order.**",
        "**Every command opens one door and breaks another.**",
        "**What survives decides the ending.**",
        "**Before dawn, the stolen voice may choose return.**",
        "**After the bells, the city keeps five reckonings.**",
    ):
        assert phrase in manor
    assert "Leva Orm" in manor
    assert "Peren Holt" in manor
    assert "A phrase supported by two streams governs" in manor
    assert "An involuntary transfer outlives the figure" in manor
    assert (
        "Before the winter-garden doors open, carry forward the facts already made"
        in adventure.explanation
    )
    assert "First decide what the bells did to a body and voice" in adventure.explanation

    sheet = MANOR_SHEET_PATH.read_text()
    for heading in (
        "## What reaches the garden first",
        "## Six ways through the doors",
        "## The household at the glass",
        "## Five joined things in the winter garden",
        "## The hearing Edrin will recognize",
        "## Body, voice, and reach",
        "## Which words the glass will carry",
        "## What survives decides the ending",
        "## The stolen voice before dawn",
        "## Five public reckonings",
    ):
        assert heading in sheet

    documents = render_adventure_documents(adventure, validate_adventure(adventure))
    rendered_manor = documents["encounters/vale-manor.md"]
    assert "**Six ways through the doors.**" in rendered_manor
    assert "**Five joined things give the saint a body.**" in rendered_manor
    assert "**Before dawn, the stolen voice may choose return.**" in rendered_manor


def test_glass_saint_expansion_five_preserves_route_open_offscreen_continuity() -> None:
    adventure = load_adventure(EXAMPLE_PATH)
    encounters = adventure.encounter_index()

    assert "Keep four pages distinct during route-open play" in adventure.explanation
    assert "Unvisited places continue through fixed hands and channels" in adventure.explanation
    skipped_phrases = {
        "the-shattered-gallery": "**If skipped or left early.**",
        "the-procession-court": "**If skipped or reached late.**",
        "the-archive-vault": "**If skipped or reached late.**",
        "the-trustees-chamber": "**If skipped or reached late.**",
        "the-west-infirmary": "**If skipped or reached late.**",
        "the-house-of-petitions": "**If skipped or reached late.**",
        "the-bell-chapel": "**If skipped or reached late.**",
        "the-grand-belfry": "**If skipped entirely.**",
    }
    for encounter_id, phrase in skipped_phrases.items():
        assert phrase in encounters[encounter_id].content

    route_sheet = ROUTE_SHEET_PATH.read_text()

    for heading in (
        "## Four separate records",
        "## Route transfer table",
        "## Off-screen continuity",
        "## Failed-action doctrine",
        "## Finale checklist",
    ):
        assert heading in route_sheet


def test_glass_saint_clue_density_is_irregular_independent_and_route_safe() -> None:
    """Protect the completed density matrix, added evidence, and next editorial stage."""
    adventure = load_adventure(EXAMPLE_PATH)
    report = validate_adventure(adventure)
    clues_by_source = Counter(clue.source_encounter_id for clue in adventure.clues)
    clues_by_revelation = Counter(clue.revelation_id for clue in adventure.clues)
    sources_by_revelation: dict[str, set[str]] = {}
    for clue in adventure.clues:
        sources_by_revelation.setdefault(clue.revelation_id, set()).add(clue.source_encounter_id)

    assert report.is_valid
    assert report.edge_connectivity == 5
    assert len(adventure.clues) == 69
    assert clues_by_source == Counter(
        {
            "the-shattered-gallery": 8,
            "the-procession-court": 7,
            "the-archive-vault": 10,
            "the-trustees-chamber": 6,
            "the-west-infirmary": 7,
            "the-house-of-petitions": 8,
            "the-bell-chapel": 9,
            "the-grand-belfry": 6,
            "vale-manor": 8,
        }
    )
    assert min(clues_by_revelation.values()) == 3
    assert max(clues_by_revelation.values()) == 7
    assert all(
        clues_by_revelation[revelation_id] == len(source_ids)
        for revelation_id, source_ids in sources_by_revelation.items()
    )
    assert {
        "counter-signed-custody-copy-outside-the-museum",
        "fresh-vale-wax-on-the-replacement-strap",
        "cut-leaf-matched-to-tavias-shelf-request",
        "hospice-glass-repeats-nearby-prayers",
        "warning-peal-creates-a-public-anchor",
        "censored-accusation-in-the-stolen-dossier",
    } <= set(adventure.clue_index())

