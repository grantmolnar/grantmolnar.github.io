"""Browser Author regressions for adventure-owned reference records."""

from __future__ import annotations

from dataclasses import replace

from adventure_graph.application.play_tracking import new_play_state, record_reference_note
from adventure_graph.application.project import RelatedPlayState
from adventure_graph.domain.adventure import Reference
from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    PLACE_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)
from tests.support.web import (
    build_authoring_app,
    reference_create_form,
    reference_edit_form,
    reference_link_form,
    reference_unlink_form,
    removal_form,
    request_wsgi,
)


def test_reference_library_supports_reference_light_adventures_and_kind_filters() -> None:
    empty_app, _ = build_authoring_app(complete_four_encounter_adventure())

    empty_status, _, empty_body = request_wsgi(empty_app, "/references")

    assert empty_status == "200 OK"
    assert "No reference records" in empty_body
    assert "Reference-light adventures are valid" in empty_body
    assert 'href="/references/new"' in empty_body

    app, _ = build_authoring_app(reference_library_adventure())
    all_status, _, all_body = request_wsgi(app, "/references")
    person_status, _, person_body = request_wsgi(app, "/references", query="kind=person")

    assert all_status == person_status == "200 OK"
    assert "Cora Pike" in all_body
    assert "Blackbriar Hall" in all_body
    assert 'href="/references?kind=person"' in all_body
    assert "Cora Pike" in person_body
    main = person_body[person_body.index("<main") : person_body.index("</main>")]
    assert "Cora Pike" in main
    assert "Blackbriar Hall" not in main


def test_reference_navigation_search_includes_aliases_and_authored_context() -> None:
    app, _ = build_authoring_app(reference_library_adventure())

    status, _, body = request_wsgi(app, "/references")

    assert status == "200 OK"
    assert 'href="/references/' + PERSON_REFERENCE_ID + '"' in body
    assert "the housekeeper" in body.casefold()
    navigation_fragment = body[body.index("data-navigation-filter") :]
    assert "the housekeeper" in navigation_fragment.casefold()
    assert "observant housekeeper" in navigation_fragment.casefold()
    assert "staff witness" in navigation_fragment.casefold()


def test_reference_detail_and_encounter_panels_preserve_order_and_context() -> None:
    app, _ = build_authoring_app(reference_library_adventure())

    reference_status, _, reference_body = request_wsgi(app, f"/references/{PERSON_REFERENCE_ID}")
    encounter_status, _, encounter_body = request_wsgi(app, "/encounters/alpha")
    edit_status, _, edit_body = request_wsgi(app, "/encounters/alpha/edit")

    assert reference_status == encounter_status == edit_status == "200 OK"
    assert "Encounter backlinks" in reference_body
    assert reference_body.index("Alpha") < reference_body.index("Beta")
    assert "Cora controls access to the first-floor rooms." in reference_body
    assert "Cora may change allegiance after hearing the testimony." in reference_body
    assert encounter_body.index("Cora Pike") < encounter_body.index("Blackbriar Hall")
    assert "Every existing reference is already linked here." in encounter_body
    assert "Create and link new reference" in encounter_body
    assert "Unlink" in encounter_body
    assert "Links preserved" not in edit_body
    assert "Linked references" in edit_body
    assert "Unlink" not in edit_body


def test_standalone_reference_create_and_edit_preserve_stable_identity() -> None:
    app, project = build_authoring_app(complete_four_encounter_adventure())

    create_status, create_headers, create_body = request_wsgi(
        app,
        "/references/new",
        "POST",
        form=reference_create_form(),
    )

    assert create_status == "303 See Other"
    assert create_body == ""
    assert project.commit_count == 1
    created = project.snapshot.adventure.references[0]
    assert create_headers["Location"] == f"/references/{created.id}?created=1&draft=new"
    assert created.aliases == ("The Bellkeeper",)
    assert created.tags == ("witness", "staff")

    edit_status, edit_headers, edit_body = request_wsgi(
        app,
        f"/references/{created.id}/edit",
        "POST",
        form=reference_edit_form(
            expected_revision="revision-2",
            title="Mara Venn, Keeper of Bells",
            aliases="The Bellkeeper, Mara",
            summary="A revised canonical summary.",
            content="## Mara\n\nRevised material.",
            tags="staff, chronicler",
        ),
    )

    assert edit_status == "303 See Other"
    assert edit_body == ""
    assert edit_headers["Location"] == f"/references/{created.id}?saved=1&draft={created.id}"
    revised = project.snapshot.adventure.reference_index()[created.id]
    assert revised.id == created.id
    assert revised.title == "Mara Venn, Keeper of Bells"
    assert revised.aliases == ("The Bellkeeper", "Mara")
    assert project.commit_count == 2


def test_contextual_create_and_link_is_one_atomic_browser_mutation() -> None:
    app, project = build_authoring_app(complete_four_encounter_adventure())

    status, headers, body = request_wsgi(
        app,
        "/references/new",
        "POST",
        form=reference_create_form(
            encounter_id="gamma",
            context="Mara hears the bells from the western gallery.",
        ),
    )

    assert status == "303 See Other"
    assert body == ""
    assert project.commit_count == 1
    created = project.snapshot.adventure.references[0]
    gamma = project.snapshot.adventure.encounter_index()["gamma"]
    assert headers["Location"] == (f"/references/{created.id}?linked=1&draft=new%3Agamma")
    assert gamma.reference_links[0].reference_id == created.id
    assert gamma.reference_links[0].context == ("Mara hears the bells from the western gallery.")


def test_contextual_reference_create_rejects_untrusted_play_return_target() -> None:
    app, project = build_authoring_app(complete_four_encounter_adventure())

    status, _, body = request_wsgi(
        app,
        "/references/new",
        "POST",
        form=reference_create_form(
            encounter_id="gamma",
            context="Mara hears the bells from the western gallery.",
            return_to="https://example.com/play",
        ),
    )

    assert status == "400 Bad Request"
    assert "authoring return target is invalid" in body
    assert project.commit_count == 0
    assert not project.snapshot.adventure.references


def test_link_duplicate_refusal_and_unlink_are_revision_aware() -> None:
    app, project = build_authoring_app(reference_library_adventure())

    link_status, link_headers, _ = request_wsgi(
        app,
        "/encounters/gamma/references/link",
        "POST",
        form=reference_link_form(
            PLACE_REFERENCE_ID,
            context="The gallery overlooks the hall.",
        ),
    )

    assert link_status == "303 See Other"
    assert link_headers["Location"] == "/encounters/gamma?reference=linked"
    linked_reference_id = (
        project.snapshot.adventure.encounter_index()["gamma"].reference_links[0].reference_id
    )
    assert linked_reference_id == PLACE_REFERENCE_ID
    assert project.commit_count == 1

    before_duplicate = project.snapshot.adventure
    duplicate_status, _, duplicate_body = request_wsgi(
        app,
        "/encounters/gamma/references/link",
        "POST",
        form=reference_link_form(
            PLACE_REFERENCE_ID,
            expected_revision="revision-2",
            context="A duplicate contextual link.",
        ),
    )

    assert duplicate_status == "422 Unprocessable Content"
    assert "Reference was not linked" in duplicate_body
    assert project.snapshot.adventure == before_duplicate
    assert project.commit_count == 1

    stale_status, _, stale_body = request_wsgi(
        app,
        "/encounters/gamma/references/unlink",
        "POST",
        form=reference_unlink_form(PLACE_REFERENCE_ID, expected_revision="revision-1"),
    )

    assert stale_status == "409 Conflict"
    assert "Revision conflict" in stale_body
    assert project.snapshot.adventure == before_duplicate

    unlink_status, unlink_headers, _ = request_wsgi(
        app,
        "/encounters/gamma/references/unlink",
        "POST",
        form=reference_unlink_form(PLACE_REFERENCE_ID, expected_revision="revision-2"),
    )

    assert unlink_status == "303 See Other"
    assert unlink_headers["Location"] == "/encounters/gamma?reference=unlinked"
    assert not project.snapshot.adventure.encounter_index()["gamma"].reference_links
    assert project.commit_count == 2


def test_reference_removal_previews_dependencies_and_requires_explicit_cascade() -> None:
    app, project = build_authoring_app(reference_library_adventure())

    get_status, _, get_body = request_wsgi(app, f"/references/{PERSON_REFERENCE_ID}/remove")

    assert get_status == "200 OK"
    assert "Cora controls access to the first-floor rooms." in get_body
    assert "Cora may change allegiance after hearing the testimony." in get_body
    assert 'name="cascade" value="1" required' in get_body

    refused_status, _, refused_body = request_wsgi(
        app,
        f"/references/{PERSON_REFERENCE_ID}/remove",
        "POST",
        form=removal_form(),
    )

    assert refused_status == "422 Unprocessable Content"
    assert "Reference was not removed" in refused_body
    assert PERSON_REFERENCE_ID in project.snapshot.adventure.reference_index()
    assert project.commit_count == 0

    removed_status, removed_headers, _ = request_wsgi(
        app,
        f"/references/{PERSON_REFERENCE_ID}/remove",
        "POST",
        form=removal_form(cascade="1"),
    )

    assert removed_status == "303 See Other"
    assert removed_headers["Location"] == "/references?removed=1"
    assert PERSON_REFERENCE_ID not in project.snapshot.adventure.reference_index()
    assert PLACE_REFERENCE_ID in project.snapshot.adventure.reference_index()
    assert all(
        link.reference_id != PERSON_REFERENCE_ID
        for encounter in project.snapshot.adventure.encounters
        for link in encounter.reference_links
    )
    assert project.commit_count == 1


def test_encounter_removal_retains_reference_records_but_removes_links() -> None:
    app, project = build_authoring_app(reference_library_adventure())

    get_status, _, get_body = request_wsgi(app, "/encounters/alpha/remove")

    assert get_status == "200 OK"
    assert "Reference records themselves are retained" in get_body
    assert "Cora Pike" in get_body
    assert "Blackbriar Hall" in get_body
    assert 'name="cascade" value="1" required' in get_body

    status, headers, _ = request_wsgi(
        app,
        "/encounters/alpha/remove",
        "POST",
        form=removal_form(cascade="1"),
    )

    assert status == "303 See Other"
    assert headers["Location"] == "/?encounter_removed=1"
    assert "alpha" not in project.snapshot.adventure.encounter_index()
    assert PERSON_REFERENCE_ID in project.snapshot.adventure.reference_index()
    assert PLACE_REFERENCE_ID in project.snapshot.adventure.reference_index()
    assert project.commit_count == 1


def test_reference_forms_fail_closed_and_render_authored_text_safely() -> None:
    malicious = Reference(
        id=PERSON_REFERENCE_ID,
        kind="person",
        title='<script>alert("title")</script>',
        aliases=("<img src=x onerror=alert(1)>",),
        summary="<b>summary</b>",
        content='<script>alert("content")</script> **safe**',
        tags=("<tag>",),
    )
    adventure = replace(complete_four_encounter_adventure(), references=(malicious,))
    app, project = build_authoring_app(adventure)

    status, _, body = request_wsgi(app, f"/references/{PERSON_REFERENCE_ID}")

    assert status == "200 OK"
    assert "<script>" not in body
    assert "<img src=x" not in body
    assert "&lt;script&gt;" in body
    assert "&lt;img src=x onerror=alert(1)&gt;" in body
    assert "&lt;b&gt;summary&lt;/b&gt;" in body

    before = project.snapshot.adventure
    invalid_status, _, invalid_body = request_wsgi(
        app,
        "/references/new",
        "POST",
        form=reference_create_form(kind="faction"),
    )

    assert invalid_status == "422 Unprocessable Content"
    assert "Reference was not created" in invalid_body
    assert project.snapshot.adventure == before
    assert project.commit_count == 0


def test_reference_controls_have_responsive_styles() -> None:
    app, _ = build_authoring_app(reference_library_adventure())

    status, _, css = request_wsgi(app, "/assets/app.css")

    assert status == "200 OK"
    assert ".filter-row" in css
    assert ".reference-link-actions" in css
    assert ".compact-authoring-form" in css
    assert ".confirmation-check" in css
    assert "@media (max-width: 900px)" in css
    assert "@media (max-width: 660px)" in css


def test_reference_removal_is_blocked_when_playthrough_notes_use_its_identity() -> None:
    adventure = reference_library_adventure()
    state = record_reference_note(
        adventure,
        new_play_state(adventure),
        PERSON_REFERENCE_ID,
        "Cora now carries the disputed seal.",
    )
    app, project = build_authoring_app(
        adventure,
        related_play_states=(RelatedPlayState("active playthrough", state),),
    )

    status, _, body = request_wsgi(app, f"/references/{PERSON_REFERENCE_ID}/remove")

    assert status == "200 OK"
    assert "active playthrough (event sequences 1)" in body
    assert "Removal blocked by play history." in body
    assert "playthrough notes" in body
    danger = body.split('<section class="section danger-zone">', 1)[1]
    assert 'type="submit">Remove reference</button>' not in danger
    assert project.commit_count == 0
