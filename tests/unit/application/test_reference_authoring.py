"""Tests for revision-aware reference-library queries and mutations."""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    PLACE_REFERENCE_ID,
    reference_library_adventure,
)
from tests.support.projects import InMemoryAuthoringProject, authoring_project

from adventure_graph.application.authoring import AuthoringError
from adventure_graph.application.errors import NoChangesRequestedError
from adventure_graph.application.play_tracking import new_play_state, record_reference_note
from adventure_graph.application.project import (
    ProjectRevision,
    RelatedPlayState,
    RevisionConflictError,
)
from adventure_graph.application.reference_authoring import (
    CreateAndLinkReference,
    CreateAndLinkReferenceCommand,
    CreateReference,
    CreateReferenceCommand,
    GetReferenceDetail,
    LinkReference,
    LinkReferenceCommand,
    RemoveReference,
    RemoveReferenceCommand,
    UnlinkReference,
    UnlinkReferenceCommand,
    UpdateReference,
    UpdateReferenceCommand,
)
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.validation import validate_adventure

NEW_REFERENCE_ID = "4e66fa28-aac8-4b77-a840-a0ae6ad2a4cb"


def _project(adventure: Adventure | None = None) -> InMemoryAuthoringProject:
    return authoring_project(adventure)


def test_create_reference_generates_identity_once_and_appends_in_authored_order() -> None:
    project = _project()
    calls = 0

    def identifier() -> str:
        nonlocal calls
        calls += 1
        return NEW_REFERENCE_ID

    result = CreateReference(project, identifier).execute(
        CreateReferenceCommand(
            expected_revision=ProjectRevision("revision-1"),
            kind="organization",
            title="  Saint Mercy House  ",
            aliases=("The Mercy",),
            summary="A dispersed charitable house.",
            tags=("faction",),
        )
    )

    assert calls == 1
    assert result.reference.id == NEW_REFERENCE_ID
    assert result.reference.title == "Saint Mercy House"
    assert result.revision == ProjectRevision("revision-2")
    assert project.snapshot.adventure.references == (result.reference,)


def test_create_and_link_reference_commits_both_changes_atomically() -> None:
    project = _project()

    result = CreateAndLinkReference(project, lambda: NEW_REFERENCE_ID).execute(
        CreateAndLinkReferenceCommand(
            encounter_id="alpha",
            expected_revision=ProjectRevision("revision-1"),
            kind="person",
            title="Cora Pike",
            aliases=("The Housekeeper",),
            summary="The keeper of Blackbriar Hall.",
            context="Cora controls access to the first-floor rooms.",
        )
    )

    assert result.reference.id == NEW_REFERENCE_ID
    assert result.link.reference_id == NEW_REFERENCE_ID
    assert result.encounter.reference_links == (result.link,)
    assert project.commit_count == 1
    assert project.snapshot.adventure.references == (result.reference,)


def test_create_and_link_reference_refuses_unknown_encounter_without_partial_write() -> None:
    project = _project()

    with pytest.raises(AuthoringError, match="Unknown encounter"):
        CreateAndLinkReference(project, lambda: NEW_REFERENCE_ID).execute(
            CreateAndLinkReferenceCommand(
                encounter_id="missing",
                expected_revision=ProjectRevision("revision-1"),
                kind="person",
                title="Cora Pike",
            )
        )

    assert project.committed_adventure is None
    assert project.snapshot.adventure.references == ()


def test_create_reference_refuses_stale_revision_before_generating_identity() -> None:
    project = _project()
    calls = 0

    def identifier() -> str:
        nonlocal calls
        calls += 1
        return NEW_REFERENCE_ID

    with pytest.raises(RevisionConflictError, match="reference operation"):
        CreateReference(project, identifier).execute(
            CreateReferenceCommand(
                expected_revision=ProjectRevision("stale"),
                kind="person",
                title="Cora Pike",
            )
        )

    assert calls == 0
    assert project.committed_adventure is None


def test_reference_mutations_all_refuse_stale_revisions_without_committing() -> None:
    adventure = reference_library_adventure()
    reference = adventure.reference_index()[PERSON_REFERENCE_ID]
    project = _project(adventure)
    operations = (
        lambda: CreateAndLinkReference(project, lambda: NEW_REFERENCE_ID).execute(
            CreateAndLinkReferenceCommand(
                encounter_id="gamma",
                expected_revision=ProjectRevision("stale"),
                kind="person",
                title="Cora Pike",
            )
        ),
        lambda: UpdateReference(project).execute(
            UpdateReferenceCommand(
                reference_id=reference.id,
                expected_revision=ProjectRevision("stale"),
                kind=reference.kind,
                title="Cora Vale",
                aliases=reference.aliases,
                summary=reference.summary,
                content=reference.content,
                tags=reference.tags,
            )
        ),
        lambda: LinkReference(project).execute(
            LinkReferenceCommand(
                encounter_id="gamma",
                reference_id=PERSON_REFERENCE_ID,
                expected_revision=ProjectRevision("stale"),
            )
        ),
        lambda: UnlinkReference(project).execute(
            UnlinkReferenceCommand(
                encounter_id="alpha",
                reference_id=PERSON_REFERENCE_ID,
                expected_revision=ProjectRevision("stale"),
            )
        ),
        lambda: RemoveReference(project).execute(
            RemoveReferenceCommand(
                reference_id=PERSON_REFERENCE_ID,
                expected_revision=ProjectRevision("stale"),
                cascade=True,
            )
        ),
    )

    for operation in operations:
        with pytest.raises(RevisionConflictError, match="reference operation"):
            operation()

    assert project.committed_adventure is None


def test_reference_detail_derives_backlinks_in_encounter_order_with_contexts() -> None:
    result = GetReferenceDetail(_project(reference_library_adventure())).execute(
        PERSON_REFERENCE_ID
    )

    assert result.detail.reference.title == "Cora Pike"
    assert tuple(backlink.encounter.id for backlink in result.detail.backlinks) == (
        "alpha",
        "beta",
    )
    assert result.detail.backlinks[1].context == (
        "Cora may change allegiance after hearing the testimony."
    )
    assert result.detail.dependency_preview.removal_dependencies == (
        "Alpha (alpha) — Cora controls access to the first-floor rooms.",
        "Beta (beta) — Cora may change allegiance after hearing the testimony.",
    )
    assert result.detail.dependency_preview.journal_references == ()


def test_update_reference_preserves_identity_links_and_authored_position() -> None:
    adventure = reference_library_adventure()
    project = _project(adventure)
    before = adventure.reference_index()[PERSON_REFERENCE_ID]

    result = UpdateReference(project).execute(
        UpdateReferenceCommand(
            reference_id=PERSON_REFERENCE_ID,
            expected_revision=ProjectRevision("revision-1"),
            kind="person",
            title="Cora Vale",
            aliases=("Cora Pike", "The Housekeeper"),
            summary=before.summary,
            content=before.content,
            tags=before.tags,
        )
    )

    assert result.after.id == PERSON_REFERENCE_ID
    assert tuple(reference.id for reference in project.snapshot.adventure.references) == (
        PERSON_REFERENCE_ID,
        PLACE_REFERENCE_ID,
    )
    assert tuple(
        link.reference_id
        for encounter in project.snapshot.adventure.encounters
        for link in encounter.reference_links
        if link.reference_id == PERSON_REFERENCE_ID
    ) == (PERSON_REFERENCE_ID, PERSON_REFERENCE_ID)


def test_update_reference_refuses_noop() -> None:
    adventure = reference_library_adventure()
    reference = adventure.reference_index()[PERSON_REFERENCE_ID]
    project = _project(adventure)

    with pytest.raises(NoChangesRequestedError, match="No authoring changes"):
        UpdateReference(project).execute(
            UpdateReferenceCommand(
                reference_id=reference.id,
                expected_revision=ProjectRevision("revision-1"),
                kind=reference.kind,
                title=reference.title,
                aliases=reference.aliases,
                summary=reference.summary,
                content=reference.content,
                tags=reference.tags,
            )
        )


def test_link_and_unlink_reference_preserve_encounter_local_order() -> None:
    project = _project(reference_library_adventure())

    linked = LinkReference(project).execute(
        LinkReferenceCommand(
            encounter_id="gamma",
            reference_id=PLACE_REFERENCE_ID,
            expected_revision=ProjectRevision("revision-1"),
            context="The road overlooks the estate.",
        )
    )
    assert linked.encounter.reference_links[-1] == linked.link

    unlinked = UnlinkReference(project).execute(
        UnlinkReferenceCommand(
            encounter_id="alpha",
            reference_id=PERSON_REFERENCE_ID,
            expected_revision=linked.revision,
        )
    )
    assert unlinked.removed_link.context == "Cora controls access to the first-floor rooms."
    assert tuple(link.reference_id for link in unlinked.encounter.reference_links) == (
        PLACE_REFERENCE_ID,
    )


def test_link_and_unlink_fail_closed_for_existing_or_missing_pairs() -> None:
    project = _project(reference_library_adventure())

    with pytest.raises(AuthoringError, match="already links reference"):
        LinkReference(project).execute(
            LinkReferenceCommand(
                encounter_id="alpha",
                reference_id=PERSON_REFERENCE_ID,
                expected_revision=ProjectRevision("revision-1"),
            )
        )
    with pytest.raises(ValueError, match="does not link reference"):
        UnlinkReference(project).execute(
            UnlinkReferenceCommand(
                encounter_id="gamma",
                reference_id=PERSON_REFERENCE_ID,
                expected_revision=ProjectRevision("revision-1"),
            )
        )

    assert project.committed_adventure is None


def test_remove_reference_refuses_links_then_cascades_only_links_and_record() -> None:
    project = _project(reference_library_adventure())

    with pytest.raises(AuthoringError, match="encounter links exist"):
        RemoveReference(project).execute(
            RemoveReferenceCommand(
                reference_id=PERSON_REFERENCE_ID,
                expected_revision=ProjectRevision("revision-1"),
            )
        )

    result = RemoveReference(project).execute(
        RemoveReferenceCommand(
            reference_id=PERSON_REFERENCE_ID,
            expected_revision=ProjectRevision("revision-1"),
            cascade=True,
        )
    )

    assert tuple(link.encounter_id for link in result.dependencies.links) == ("alpha", "beta")
    assert PERSON_REFERENCE_ID not in project.snapshot.adventure.reference_index()
    assert PLACE_REFERENCE_ID in project.snapshot.adventure.reference_index()
    assert len(project.snapshot.adventure.encounters) == 4
    assert all(
        link.reference_id != PERSON_REFERENCE_ID
        for encounter in project.snapshot.adventure.encounters
        for link in encounter.reference_links
    )


def test_reference_edit_can_repair_an_empty_prose_warning() -> None:
    adventure = reference_library_adventure()
    reference = adventure.reference_index()[PLACE_REFERENCE_ID]
    adventure = replace(
        adventure,
        references=tuple(
            replace(reference, summary="") if item.id == PLACE_REFERENCE_ID else item
            for item in adventure.references
        ),
    )
    assert any(
        issue.code == "reference-prose-empty" for issue in validate_adventure(adventure).issues
    )
    project = _project(adventure)

    result = UpdateReference(project).execute(
        UpdateReferenceCommand(
            reference_id=PLACE_REFERENCE_ID,
            expected_revision=ProjectRevision("revision-1"),
            kind=reference.kind,
            title=reference.title,
            aliases=reference.aliases,
            summary="The estate contains several distinct encounter sites.",
            content=reference.content,
            tags=reference.tags,
        )
    )

    assert not any(
        issue.code == "reference-prose-empty" for issue in result.validation_report.issues
    )


def test_reference_playthrough_notes_are_removal_blockers() -> None:
    adventure = reference_library_adventure()
    state = record_reference_note(
        adventure,
        new_play_state(adventure),
        PERSON_REFERENCE_ID,
        "Cora knows where the party hid the seal.",
    )
    project = authoring_project(
        adventure,
        related_play_states=(RelatedPlayState("active playthrough", state),),
    )

    detail = GetReferenceDetail(project).execute(PERSON_REFERENCE_ID)

    assert detail.detail.dependency_preview.journal_references == (
        "active playthrough (event sequences 1)",
    )
    with pytest.raises(ValueError, match="Related play state active playthrough would be invalid"):
        RemoveReference(project).execute(
            RemoveReferenceCommand(
                reference_id=PERSON_REFERENCE_ID,
                expected_revision=ProjectRevision("revision-1"),
                cascade=True,
            )
        )
    assert project.commit_count == 0
