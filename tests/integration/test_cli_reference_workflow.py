"""Integration coverage for the headless adventure reference-library lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest

from adventure_graph.bootstrap import main
from adventure_graph.infrastructure.adventure_store import load_adventure


def _initialize_reference_project(tmp_path: Path) -> tuple[Path, Path, str]:
    project = tmp_path / "reference-project"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    state_path = project / "play-state.json"
    assert (
        main(
            [
                "add-reference",
                str(adventure_path),
                "person",
                "Cora Pike",
                "--alias",
                "Captain Pike",
                "--summary",
                "A recurring investigator whose loyalties are uncertain.",
                "--tag",
                "investigator",
            ]
        )
        == 0
    )
    reference = load_adventure(adventure_path).references[-1]
    return adventure_path, state_path, reference.id


def test_cli_reference_create_list_link_inspect_edit_and_unlink(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    adventure_path, _state_path, reference_id = _initialize_reference_project(tmp_path)
    capsys.readouterr()

    assert main(["list", str(adventure_path), "reference"]) == 0
    listed = capsys.readouterr().out
    assert f"{reference_id}: Cora Pike" in listed
    assert "person; links: 0; aliases: Captain Pike" in listed

    before_duplicate = adventure_path.read_bytes()
    assert (
        main(
            [
                "link-reference",
                str(adventure_path),
                "the-shattered-gallery",
                reference_id,
                "--context",
                "She quietly audits the restoration ledgers.",
            ]
        )
        == 0
    )
    linked_bytes = adventure_path.read_bytes()
    assert linked_bytes != before_duplicate
    assert (
        main(
            [
                "link-reference",
                str(adventure_path),
                "the-shattered-gallery",
                reference_id,
            ]
        )
        == 2
    )
    assert adventure_path.read_bytes() == linked_bytes
    assert "already links reference" in capsys.readouterr().err

    assert main(["inspect", str(adventure_path), "reference", reference_id]) == 0
    reference_detail = capsys.readouterr().out
    assert f"Reference {reference_id}: Cora Pike" in reference_detail
    assert "the-shattered-gallery: The Shattered Gallery" in reference_detail
    assert "She quietly audits the restoration ledgers." in reference_detail
    assert (
        "Unlink from encounter: The Shattered Gallery (the-shattered-gallery)" in reference_detail
    )

    assert (
        main(
            [
                "inspect",
                str(adventure_path),
                "encounter",
                "the-shattered-gallery",
            ]
        )
        == 0
    )
    encounter_detail = capsys.readouterr().out
    assert f"Cora Pike [person] ({reference_id})" in encounter_detail
    assert "She quietly audits the restoration ledgers." in encounter_detail

    assert (
        main(
            [
                "edit-reference",
                str(adventure_path),
                reference_id,
                "--title",
                "Captain Cora Pike",
                "--alias",
                "Cora Pike",
                "--content",
                "She can appear in several encounters without becoming a graph node.",
            ]
        )
        == 0
    )
    edited = load_adventure(adventure_path)
    assert edited.references[-1].id == reference_id
    assert edited.references[-1].title == "Captain Cora Pike"
    assert any(
        link.reference_id == reference_id
        for link in edited.encounter_index()["the-shattered-gallery"].reference_links
    )

    assert (
        main(
            [
                "unlink-reference",
                str(adventure_path),
                "the-shattered-gallery",
                reference_id,
            ]
        )
        == 0
    )
    unlinked_bytes = adventure_path.read_bytes()
    assert (
        main(
            [
                "unlink-reference",
                str(adventure_path),
                "the-shattered-gallery",
                reference_id,
            ]
        )
        == 2
    )
    assert adventure_path.read_bytes() == unlinked_bytes
    assert "does not link reference" in capsys.readouterr().err


def test_cli_validation_presents_reference_warnings(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    project = tmp_path / "reference-warning"
    assert main(["init", str(project)]) == 0
    adventure_path = project / "adventure.json"
    assert (
        main(
            [
                "add-reference",
                str(adventure_path),
                "object",
                "The Unwritten Key",
            ]
        )
        == 0
    )
    reference_id = load_adventure(adventure_path).references[-1].id
    capsys.readouterr()

    assert main(["validate", str(adventure_path)]) == 0
    output = capsys.readouterr().out
    assert f"WARNING reference-prose-empty [{reference_id}]" in output


def test_cli_reference_removal_refuses_then_cascades_with_exact_bounds(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    adventure_path, _state_path, reference_id = _initialize_reference_project(tmp_path)
    assert (
        main(
            [
                "link-reference",
                str(adventure_path),
                "the-shattered-gallery",
                reference_id,
                "--context",
                "Present during the opening investigation.",
            ]
        )
        == 0
    )
    assert (
        main(
            [
                "link-reference",
                str(adventure_path),
                "the-archive-vault",
                reference_id,
                "--context",
                "Her allegiance changes after the vault is opened.",
            ]
        )
        == 0
    )
    capsys.readouterr()
    before = adventure_path.read_bytes()

    assert main(["remove-reference", str(adventure_path), reference_id]) == 2
    assert adventure_path.read_bytes() == before
    refusal = capsys.readouterr().err
    assert "encounter links exist in: 'the-shattered-gallery', 'the-archive-vault'" in refusal
    assert "cascade=True" in refusal

    assert (
        main(
            [
                "remove-reference",
                str(adventure_path),
                reference_id,
                "--cascade",
            ]
        )
        == 0
    )
    adventure = load_adventure(adventure_path)
    assert reference_id not in adventure.reference_index()
    assert "the-shattered-gallery" in adventure.encounter_index()
    assert "the-archive-vault" in adventure.encounter_index()
    assert all(
        link.reference_id != reference_id
        for encounter in adventure.encounters
        for link in encounter.reference_links
    )
    output = capsys.readouterr().out
    assert "Cascade removed 2 encounter link(s)." in output


def test_cli_encounter_removal_reports_reference_links_and_journal_blockers(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    adventure_path, state_path, reference_id = _initialize_reference_project(tmp_path)
    assert (
        main(
            [
                "link-reference",
                str(adventure_path),
                "the-shattered-gallery",
                reference_id,
                "--context",
                "Opening-scene contact.",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert (
        main(
            [
                "inspect",
                str(adventure_path),
                "encounter",
                "the-shattered-gallery",
            ]
        )
        == 0
    )
    preview = capsys.readouterr().out
    assert f"Reference link: Cora Pike ({reference_id})" in preview
    assert f"Discard reference link: Cora Pike ({reference_id})" in preview
    assert "Journal blockers:\n  none" in preview

    assert main(["visit", str(adventure_path), str(state_path), "the-shattered-gallery"]) == 0
    capsys.readouterr()
    assert (
        main(
            [
                "inspect",
                str(adventure_path),
                "encounter",
                "the-shattered-gallery",
                "--state",
                str(state_path),
            ]
        )
        == 0
    )
    preview = capsys.readouterr().out
    assert "Journal blockers:" in preview
    assert str(state_path) in preview
    assert "event sequences 1" in preview

    before = adventure_path.read_bytes()
    assert (
        main(
            [
                "remove-encounter",
                str(adventure_path),
                "the-shattered-gallery",
                "--cascade",
            ]
        )
        == 2
    )
    assert adventure_path.read_bytes() == before
    assert "would be invalid after this change" in capsys.readouterr().err
