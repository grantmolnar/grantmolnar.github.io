"""Revision-aware POST orchestration for the local authoring interface."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from http import HTTPStatus
from typing import cast
from urllib.parse import urlencode
from wsgiref.types import WSGIEnvironment

from adventure_graph.application.adventure_authoring import UpdateAdventureCommand
from adventure_graph.application.encounter_authoring import (
    RemoveEncounterCommand,
    UpdateEncounterCommand,
)
from adventure_graph.application.project import ProjectRevision, RevisionConflictError
from adventure_graph.application.reference_authoring import (
    CreateAndLinkReferenceCommand,
    CreateReferenceCommand,
    LinkReferenceCommand,
    RemoveReferenceCommand,
    UnlinkReferenceCommand,
    UpdateReferenceCommand,
)
from adventure_graph.application.structural_authoring import (
    CreateClueCommand,
    CreateEncounterCommand,
    CreateRevelationCommand,
    UpdateClueCommand,
    UpdateRevelationCommand,
)
from adventure_graph.domain.adventure import ReferenceKind
from adventure_graph.interfaces.web.adventure_rendering import render_adventure_edit
from adventure_graph.interfaces.web.authoring_forms import (
    parse_adventure_form,
    parse_clue_edit_form,
    parse_clue_form,
    parse_encounter_create_form,
    parse_encounter_form,
    parse_reference_form,
    parse_reference_link_form,
    parse_reference_unlink_form,
    parse_removal_form,
    parse_revelation_edit_form,
    parse_revelation_form,
)
from adventure_graph.interfaces.web.authoring_updates import execute_authoring_update
from adventure_graph.interfaces.web.clue_rendering import (
    render_clue_create,
    render_clue_edit,
)
from adventure_graph.interfaces.web.contracts import AuthoringCommands, AuthoringQueries
from adventure_graph.interfaces.web.encounter_rendering import (
    render_encounter,
    render_encounter_create,
    render_encounter_edit,
    render_encounter_remove,
)
from adventure_graph.interfaces.web.form_parsing import parse_tags
from adventure_graph.interfaces.web.http import WebResponse, redirect, require_csrf
from adventure_graph.interfaces.web.reference_rendering import (
    REFERENCE_KINDS,
    render_reference_create,
    render_reference_edit,
    render_reference_remove,
)
from adventure_graph.interfaces.web.revelation_rendering import (
    render_revelation_create,
    render_revelation_edit,
)
from adventure_graph.interfaces.web.routing import (
    encounter_reference_action_route,
    entity_edit_route,
    entity_remove_route,
    play_authoring_return_location,
    quote_identifier,
)
from adventure_graph.interfaces.web.view_models import (
    AdventureEditValues,
    ClueCreateValues,
    ClueEditValues,
    EncounterCreateValues,
    EncounterEditValues,
    PageNotice,
    ReferenceCreateValues,
    ReferenceEditValues,
    RevelationCreateValues,
    RevelationEditValues,
)


@dataclass(frozen=True, slots=True)
class AuthoringActionWorkspace:
    """Translate explicit authoring POST routes into application commands."""

    queries: AuthoringQueries
    commands: AuthoringCommands
    project_label: str
    csrf_token: str

    def write(self, path: str, environ: WSGIEnvironment) -> WebResponse | None:
        """Handle one authoring mutation route, or decline unrelated paths."""
        if path == "/adventure/edit":
            return self._update_adventure(environ)
        if path == "/references/new":
            return self._create_reference(environ)
        if path == "/encounters/new":
            return self._create_encounter(environ)
        if path == "/clues/new":
            return self._create_clue(environ)
        if path == "/revelations/new":
            return self._create_revelation(environ)

        reference_action = encounter_reference_action_route(path)
        if reference_action is not None:
            encounter_id, action = reference_action
            return (
                self._link_reference(encounter_id, environ)
                if action == "link"
                else self._unlink_reference(encounter_id, environ)
            )

        remove_route = entity_remove_route(path)
        if remove_route is not None:
            kind, identifier = remove_route
            if kind == "encounter":
                return self._remove_encounter(identifier, environ)
            if kind == "reference":
                return self._remove_reference(identifier, environ)
            return None

        edit_route = entity_edit_route(path)
        if edit_route is None:
            return None
        kind, identifier = edit_route
        if kind == "encounter":
            return self._update_encounter(identifier, environ)
        if kind == "reference":
            return self._update_reference(identifier, environ)
        if kind == "revelation":
            return self._update_revelation(identifier, environ)
        return self._update_clue(identifier, environ)

    def draft_key(self, kind: str, identifier: str) -> str:
        """Return the stable browser-local draft key for one authoring form."""
        return self._draft_key(kind, identifier)

    def _update_adventure(self, environ: WSGIEnvironment) -> WebResponse:
        values, submitted_token = parse_adventure_form(environ)
        self._require_csrf(submitted_token)
        command = UpdateAdventureCommand(
            expected_revision=ProjectRevision(values.expected_revision),
            title=values.title,
            synopsis=values.synopsis,
            premise=values.premise,
            explanation=values.explanation,
            tags=values.tags,
        )
        result = execute_authoring_update(
            command,
            self.commands.update_adventure,
            unchanged_location="/?saved=unchanged",
            render_error=lambda error, status, heading: self._adventure_edit_error(
                values, error, status, heading
            ),
            rejected_heading="Adventure was not saved",
        )
        if isinstance(result, WebResponse):
            return result
        return redirect(f"/?{urlencode({'saved': '1', 'draft': result.before.id})}")

    def _create_reference(self, environ: WSGIEnvironment) -> WebResponse:
        parsed, submitted_token = parse_reference_form(environ, include_encounter=True)
        values = cast(ReferenceCreateValues, parsed)
        self._require_csrf(submitted_token)
        try:
            if values.encounter_id:
                result = self.commands.create_and_link_reference(
                    CreateAndLinkReferenceCommand(
                        encounter_id=values.encounter_id,
                        expected_revision=ProjectRevision(values.expected_revision),
                        kind=_reference_kind(values.kind),
                        title=values.title,
                        aliases=parse_tags(values.aliases),
                        summary=values.summary,
                        content=values.content,
                        tags=parse_tags(values.tags),
                        context=values.context,
                    )
                )
                draft_id = f"new:{values.encounter_id}"
                query = urlencode({"linked": "1", "draft": draft_id})
            else:
                result = self.commands.create_reference(
                    CreateReferenceCommand(
                        expected_revision=ProjectRevision(values.expected_revision),
                        kind=_reference_kind(values.kind),
                        title=values.title,
                        aliases=parse_tags(values.aliases),
                        summary=values.summary,
                        content=values.content,
                        tags=parse_tags(values.tags),
                    )
                )
                query = urlencode({"created": "1", "draft": "new"})
        except RevisionConflictError as error:
            return self._reference_create_error(
                values,
                error,
                HTTPStatus.CONFLICT,
                "Revision conflict",
            )
        except ValueError as error:
            return self._reference_create_error(
                values,
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Reference was not created",
            )
        if values.return_to:
            return redirect(
                play_authoring_return_location(
                    values.return_to,
                    action="reference-authored",
                    focus_encounter_id=values.encounter_id or None,
                )
            )
        return redirect(f"/references/{quote_identifier(result.reference.id)}?{query}")

    def _update_reference(
        self,
        reference_id: str,
        environ: WSGIEnvironment,
    ) -> WebResponse:
        parsed, submitted_token = parse_reference_form(environ, include_encounter=False)
        values = cast(ReferenceEditValues, parsed)
        self._require_csrf(submitted_token)
        command = UpdateReferenceCommand(
            reference_id=reference_id,
            expected_revision=ProjectRevision(values.expected_revision),
            kind=_reference_kind(values.kind),
            title=values.title,
            aliases=parse_tags(values.aliases),
            summary=values.summary,
            content=values.content,
            tags=parse_tags(values.tags),
        )
        result = execute_authoring_update(
            command,
            self.commands.update_reference,
            unchanged_location=(f"/references/{quote_identifier(reference_id)}?saved=unchanged"),
            render_error=lambda error, status, heading: self._reference_edit_error(
                reference_id,
                values,
                error,
                status,
                heading,
            ),
            rejected_heading="Reference was not saved",
        )
        if isinstance(result, WebResponse):
            return result
        query = urlencode({"saved": "1", "draft": result.before.id})
        return redirect(f"/references/{quote_identifier(result.after.id)}?{query}")

    def _link_reference(
        self,
        encounter_id: str,
        environ: WSGIEnvironment,
    ) -> WebResponse:
        values, submitted_token = parse_reference_link_form(environ)
        self._require_csrf(submitted_token)
        try:
            self.commands.link_reference(
                LinkReferenceCommand(
                    encounter_id=encounter_id,
                    reference_id=values.reference_id,
                    expected_revision=ProjectRevision(values.expected_revision),
                    context=values.context,
                )
            )
        except RevisionConflictError as error:
            return self._encounter_reference_error(
                encounter_id,
                error,
                HTTPStatus.CONFLICT,
                "Revision conflict",
            )
        except ValueError as error:
            return self._encounter_reference_error(
                encounter_id,
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Reference was not linked",
            )
        return redirect(f"/encounters/{quote_identifier(encounter_id)}?reference=linked")

    def _unlink_reference(
        self,
        encounter_id: str,
        environ: WSGIEnvironment,
    ) -> WebResponse:
        values, submitted_token = parse_reference_unlink_form(environ)
        self._require_csrf(submitted_token)
        try:
            self.commands.unlink_reference(
                UnlinkReferenceCommand(
                    encounter_id=encounter_id,
                    reference_id=values.reference_id,
                    expected_revision=ProjectRevision(values.expected_revision),
                )
            )
        except RevisionConflictError as error:
            return self._encounter_reference_error(
                encounter_id,
                error,
                HTTPStatus.CONFLICT,
                "Revision conflict",
            )
        except ValueError as error:
            return self._encounter_reference_error(
                encounter_id,
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Reference was not unlinked",
            )
        return redirect(f"/encounters/{quote_identifier(encounter_id)}?reference=unlinked")

    def _remove_reference(
        self,
        reference_id: str,
        environ: WSGIEnvironment,
    ) -> WebResponse:
        values, submitted_token = parse_removal_form(environ)
        self._require_csrf(submitted_token)
        try:
            self.commands.remove_reference(
                RemoveReferenceCommand(
                    reference_id=reference_id,
                    expected_revision=ProjectRevision(values.expected_revision),
                    cascade=values.cascade,
                )
            )
        except RevisionConflictError as error:
            return self._reference_remove_error(
                reference_id,
                error,
                HTTPStatus.CONFLICT,
                "Revision conflict",
            )
        except ValueError as error:
            return self._reference_remove_error(
                reference_id,
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Reference was not removed",
            )
        return redirect("/references?removed=1")

    def _remove_encounter(
        self,
        encounter_id: str,
        environ: WSGIEnvironment,
    ) -> WebResponse:
        values, submitted_token = parse_removal_form(environ)
        self._require_csrf(submitted_token)
        try:
            self.commands.remove_encounter(
                RemoveEncounterCommand(
                    encounter_id=encounter_id,
                    expected_revision=ProjectRevision(values.expected_revision),
                    cascade=values.cascade,
                )
            )
        except RevisionConflictError as error:
            return self._encounter_remove_error(
                encounter_id,
                error,
                HTTPStatus.CONFLICT,
                "Revision conflict",
            )
        except ValueError as error:
            return self._encounter_remove_error(
                encounter_id,
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Encounter was not removed",
            )
        return redirect("/?encounter_removed=1")

    def _update_revelation(self, revelation_id: str, environ: WSGIEnvironment) -> WebResponse:
        values, submitted_token = parse_revelation_edit_form(environ)
        self._require_csrf(submitted_token)
        command = UpdateRevelationCommand(
            revelation_id=revelation_id,
            expected_revision=ProjectRevision(values.expected_revision),
            title=values.title,
            description=values.description,
            unlocks_encounter_id=values.unlocks_encounter_id or None,
            required=values.required,
        )
        result = execute_authoring_update(
            command,
            self.commands.update_revelation,
            unchanged_location=(f"/revelations/{quote_identifier(revelation_id)}?saved=unchanged"),
            render_error=lambda error, status, heading: self._revelation_edit_error(
                revelation_id, values, error, status, heading
            ),
            rejected_heading="Revelation was not saved",
        )
        if isinstance(result, WebResponse):
            return result
        query = urlencode({"saved": "1", "draft": result.before.id})
        return redirect(f"/revelations/{quote_identifier(result.after.id)}?{query}")

    def _update_clue(self, clue_id: str, environ: WSGIEnvironment) -> WebResponse:
        values, submitted_token = parse_clue_edit_form(environ)
        self._require_csrf(submitted_token)
        command = UpdateClueCommand(
            clue_id=clue_id,
            expected_revision=ProjectRevision(values.expected_revision),
            title=values.title,
            source_encounter_id=values.source_encounter_id,
            revelation_id=values.revelation_id,
            description=values.description,
            discovery=values.discovery,
        )
        result = execute_authoring_update(
            command,
            self.commands.update_clue,
            unchanged_location=f"/clues/{quote_identifier(clue_id)}?saved=unchanged",
            render_error=lambda error, status, heading: self._clue_edit_error(
                clue_id, values, error, status, heading
            ),
            rejected_heading="Lead was not saved",
        )
        if isinstance(result, WebResponse):
            return result
        query = urlencode({"saved": "1", "draft": result.before.id})
        return redirect(f"/clues/{quote_identifier(result.after.id)}?{query}")

    def _update_encounter(self, encounter_id: str, environ: WSGIEnvironment) -> WebResponse:
        values, submitted_token = parse_encounter_form(environ)
        self._require_csrf(submitted_token)
        command = UpdateEncounterCommand(
            encounter_id=encounter_id,
            expected_revision=ProjectRevision(values.expected_revision),
            title=values.title,
            summary=values.summary,
            opening_view=values.opening_view,
            content=values.content,
            required=values.required,
            start=values.start,
            end=values.end,
            tags=parse_tags(values.tags),
        )
        result = execute_authoring_update(
            command,
            self.commands.update_encounter,
            unchanged_location=f"/encounters/{quote_identifier(encounter_id)}?saved=unchanged",
            render_error=lambda error, status, heading: self._encounter_edit_error(
                encounter_id, values, error, status, heading
            ),
            rejected_heading="Encounter was not saved",
        )
        if isinstance(result, WebResponse):
            return result
        query = urlencode({"saved": "1", "draft": result.before.id})
        return redirect(f"/encounters/{quote_identifier(result.after.id)}?{query}")

    def _create_encounter(self, environ: WSGIEnvironment) -> WebResponse:
        values, submitted_token = parse_encounter_create_form(environ)
        self._require_csrf(submitted_token)
        try:
            result = self.commands.create_encounter(
                CreateEncounterCommand(
                    expected_revision=ProjectRevision(values.expected_revision),
                    title=values.title,
                    summary=values.summary,
                    opening_view=values.opening_view,
                    content=values.content,
                    required=values.required,
                    start=values.start,
                    end=values.end,
                    tags=parse_tags(values.tags),
                )
            )
        except RevisionConflictError as error:
            return self._encounter_create_error(
                values, error, HTTPStatus.CONFLICT, "Revision conflict"
            )
        except ValueError as error:
            return self._encounter_create_error(
                values, error, HTTPStatus.UNPROCESSABLE_ENTITY, "Encounter was not created"
            )
        if values.return_to:
            return redirect(
                play_authoring_return_location(
                    values.return_to,
                    action="encounter-authored",
                    focus_encounter_id=result.encounter.id,
                )
            )
        return redirect(f"/encounters/{quote_identifier(result.encounter.id)}?created=1")

    def _create_clue(self, environ: WSGIEnvironment) -> WebResponse:
        values, submitted_token = parse_clue_form(environ, include_return_to=True)
        self._require_csrf(submitted_token)
        try:
            result = self.commands.create_clue(
                CreateClueCommand(
                    expected_revision=ProjectRevision(values.expected_revision),
                    title=values.title,
                    source_encounter_id=values.source_encounter_id,
                    revelation_id=values.revelation_id,
                    description=values.description,
                    discovery=values.discovery,
                )
            )
        except RevisionConflictError as error:
            return self._clue_form_error(values, error, HTTPStatus.CONFLICT, "Revision conflict")
        except ValueError as error:
            return self._clue_form_error(
                values,
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Lead was not created",
            )
        if values.return_to:
            return redirect(
                play_authoring_return_location(
                    values.return_to,
                    action="clue-authored",
                    focus_encounter_id=result.clue.source_encounter_id,
                )
            )
        return redirect(f"/clues/{quote_identifier(result.clue.id)}?created=1")

    def _create_revelation(self, environ: WSGIEnvironment) -> WebResponse:
        values, submitted_token = parse_revelation_form(environ, include_return_to=True)
        self._require_csrf(submitted_token)
        try:
            result = self.commands.create_revelation(
                CreateRevelationCommand(
                    expected_revision=ProjectRevision(values.expected_revision),
                    title=values.title,
                    description=values.description,
                    unlocks_encounter_id=values.unlocks_encounter_id or None,
                    required=values.required,
                )
            )
        except RevisionConflictError as error:
            return self._revelation_form_error(
                values,
                error,
                HTTPStatus.CONFLICT,
                "Revision conflict",
            )
        except ValueError as error:
            return self._revelation_form_error(
                values,
                error,
                HTTPStatus.UNPROCESSABLE_ENTITY,
                "Revelation was not created",
            )
        if values.source_encounter_id:
            parameters = {
                "source": values.source_encounter_id,
                "revelation": result.revelation.id,
                "created_revelation": "1",
            }
            if values.return_to:
                parameters["return_to"] = values.return_to
            query = urlencode(parameters)
            return redirect(f"/clues/new?{query}")
        return redirect(f"/revelations/{quote_identifier(result.revelation.id)}?created=1")

    def _adventure_edit_error(
        self,
        values: AdventureEditValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_overview()
        return WebResponse(
            status,
            render_adventure_edit(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("adventure", current.adventure.id),
                values=values,
                notice=PageNotice("error", heading, str(error)),
                server_values=True,
            ),
        )

    def _encounter_create_error(
        self,
        values: EncounterCreateValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_structure()
        return WebResponse(
            status,
            render_encounter_create(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("encounter", "new"),
                values=values,
                notice=PageNotice("error", heading, str(error)),
                server_values=True,
            ),
        )

    def _encounter_edit_error(
        self,
        encounter_id: str,
        values: EncounterEditValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_encounter(encounter_id)
        return WebResponse(
            status,
            render_encounter_edit(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("encounter", encounter_id),
                values=values,
                notice=PageNotice("error", heading, str(error)),
                server_values=True,
            ),
        )

    def _reference_create_error(
        self,
        values: ReferenceCreateValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_overview()
        draft_id = f"new:{values.encounter_id}" if values.encounter_id else "new"
        return WebResponse(
            status,
            render_reference_create(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("reference", draft_id),
                values=values,
                notice=PageNotice("error", heading, str(error)),
                server_values=True,
            ),
        )

    def _reference_edit_error(
        self,
        reference_id: str,
        values: ReferenceEditValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_reference(reference_id)
        return WebResponse(
            status,
            render_reference_edit(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("reference", reference_id),
                values=values,
                notice=PageNotice("error", heading, str(error)),
                server_values=True,
            ),
        )

    def _encounter_reference_error(
        self,
        encounter_id: str,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_encounter(encounter_id)
        return WebResponse(
            status,
            render_encounter(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                notice=PageNotice("error", heading, str(error)),
            ),
        )

    def _reference_remove_error(
        self,
        reference_id: str,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_reference(reference_id)
        return WebResponse(
            status,
            render_reference_remove(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                notice=PageNotice("error", heading, str(error)),
            ),
        )

    def _encounter_remove_error(
        self,
        encounter_id: str,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_encounter(encounter_id)
        return WebResponse(
            status,
            render_encounter_remove(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                notice=PageNotice("error", heading, str(error)),
            ),
        )

    def _revelation_edit_error(
        self,
        revelation_id: str,
        values: RevelationEditValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_revelation(revelation_id)
        return WebResponse(
            status,
            render_revelation_edit(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("revelation", revelation_id),
                values=values,
                notice=PageNotice("error", heading, str(error)),
                server_values=True,
            ),
        )

    def _clue_edit_error(
        self,
        clue_id: str,
        values: ClueEditValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_clue(clue_id)
        return WebResponse(
            status,
            render_clue_edit(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("clue", clue_id),
                values=values,
                notice=PageNotice("error", heading, str(error)),
                server_values=True,
            ),
        )

    def _clue_form_error(
        self,
        values: ClueCreateValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_structure()
        return WebResponse(
            status,
            render_clue_create(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("clue", "new"),
                values=values,
                notice=PageNotice("error", heading, str(error)),
                server_values=True,
            ),
        )

    def _revelation_form_error(
        self,
        values: RevelationCreateValues,
        error: ValueError,
        status: HTTPStatus,
        heading: str,
    ) -> WebResponse:
        current = self.queries.get_structure()
        return WebResponse(
            status,
            render_revelation_create(
                current,
                self.project_label,
                csrf_token=self.csrf_token,
                draft_key=self._draft_key("revelation", "new"),
                values=values,
                notice=PageNotice("error", heading, str(error)),
                server_values=True,
            ),
        )

    def _require_csrf(self, submitted_token: str) -> None:
        require_csrf(submitted_token, self.csrf_token)

    def _draft_key(self, kind: str, identifier: str) -> str:
        project_key = hashlib.sha256(self.project_label.encode("utf-8")).hexdigest()[:16]
        return f"adventure-graph:draft:{project_key}:{kind}:{identifier}"


def _reference_kind(value: str) -> ReferenceKind:
    if value not in REFERENCE_KINDS:
        raise ValueError("Reference kind is unsupported.")
    return value

