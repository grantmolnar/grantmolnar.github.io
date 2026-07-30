"""Filesystem integration coverage for browser reference authoring."""

from __future__ import annotations

from pathlib import Path

from adventure_graph.bootstrap import main
from adventure_graph.infrastructure.adventure_store import load_adventure
from adventure_graph.infrastructure.local_authoring_project import LocalAuthoringProject
from adventure_graph.web_composition import (
    LocalWebProjects,
    compose_adventure_web_application,
)
from tests.support.web import post_form, request_wsgi


def test_web_reference_create_and_link_round_trips_through_real_project(
    tmp_path: Path,
) -> None:
    project_directory = tmp_path / "web-references"
    assert main(["init", str(project_directory)]) == 0
    adventure_path = project_directory / "adventure.json"
    project = LocalAuthoringProject(adventure_path)
    app = compose_adventure_web_application(
        LocalWebProjects.open(adventure_path),
        csrf_token="integration-token",
    )

    create_revision = project.load().revision.value
    create_status, create_headers, create_body = post_form(
        app,
        "/references/new",
        {
            "csrf_token": "integration-token",
            "expected_revision": create_revision,
            "kind": "person",
            "title": "Mara Venn",
            "aliases": "The Bellkeeper",
            "summary": "A recurring witness who knows the old routes.",
            "content": "## Mara Venn\n\nMara records every midnight arrival.",
            "tags": "witness, staff",
            "encounter_id": "the-shattered-gallery",
            "context": "Mara heard the bell from the ruined gallery.",
        },
    )

    assert create_status == "303 See Other"
    assert create_body == ""
    saved = load_adventure(adventure_path)
    reference = next(item for item in saved.references if item.title == "Mara Venn")
    assert create_headers["Location"] == (
        f"/references/{reference.id}?linked=1&draft=new%3Athe-shattered-gallery"
    )
    assert reference.aliases == ("The Bellkeeper",)
    link = next(
        item
        for item in saved.encounter_index()["the-shattered-gallery"].reference_links
        if item.reference_id == reference.id
    )
    assert link.context == "Mara heard the bell from the ruined gallery."

    detail_status, _, detail_body = request_wsgi(app, f"/references/{reference.id}")
    assert detail_status == "200 OK"
    assert "Mara Venn" in detail_body
    assert "The Shattered Gallery" in detail_body

    edit_revision = project.load().revision.value
    edit_status, edit_headers, edit_body = post_form(
        app,
        f"/references/{reference.id}/edit",
        {
            "csrf_token": "integration-token",
            "expected_revision": edit_revision,
            "kind": "person",
            "title": "Mara Venn, Bellkeeper",
            "aliases": "The Bellkeeper, Mara",
            "summary": "The recurring witness and keeper of the western bell.",
            "content": "## Mara Venn\n\nHer record survives in the gallery wall.",
            "tags": "staff, witness",
        },
    )

    assert edit_status == "303 See Other"
    assert edit_body == ""
    assert edit_headers["Location"] == (f"/references/{reference.id}?saved=1&draft={reference.id}")
    revised = load_adventure(adventure_path)
    revised_reference = revised.reference_index()[reference.id]
    assert revised_reference.id == reference.id
    assert revised_reference.title == "Mara Venn, Bellkeeper"
    revised_link = next(
        item
        for item in revised.encounter_index()["the-shattered-gallery"].reference_links
        if item.reference_id == reference.id
    )
    assert revised_link.reference_id == reference.id
