"""Form translation for authoring, reports, and journal archives."""

from __future__ import annotations

from dataclasses import dataclass
from wsgiref.types import WSGIEnvironment

from adventure_graph.interfaces.web.form_parsing import (
    InvalidFormError,
    adventure_tags_from_values,
    checkbox_value,
    one_form_value,
    parse_form_fields,
    require_allowed_fields,
    require_revision_value,
)
from adventure_graph.interfaces.web.routing import normalize_play_return_target
from adventure_graph.interfaces.web.view_models import (
    AdventureEditValues,
    ClueCreateValues,
    ClueEditValues,
    EncounterCreateValues,
    EncounterEditValues,
    ReferenceCreateValues,
    ReferenceEditValues,
    RevelationCreateValues,
    RevelationEditValues,
)


@dataclass(frozen=True, slots=True)
class ReferenceLinkValues:
    """Submitted values for one encounter-local reference link."""

    expected_revision: str
    reference_id: str
    context: str


@dataclass(frozen=True, slots=True)
class ReferenceUnlinkValues:
    """Submitted values for removing one encounter/reference pair."""

    expected_revision: str
    reference_id: str


@dataclass(frozen=True, slots=True)
class RemovalValues:
    """Submitted values for one dependency-aware authored removal."""

    expected_revision: str
    cascade: bool


@dataclass(frozen=True, slots=True)
class ArchiveCreateValues:
    """Submitted values for archiving the active journal."""

    expected_revision: str
    label: str
    name: str


@dataclass(frozen=True, slots=True)
class ArchiveActionValues:
    """Submitted values for restoring or deleting one archive."""

    expected_revision: str
    confirmation: str = ""


def parse_adventure_form(environ: WSGIEnvironment) -> tuple[AdventureEditValues, str]:
    """Parse adventure metadata editor values and their CSRF token."""
    fields = parse_form_fields(environ, max_num_fields=18)
    required = {
        "csrf_token",
        "expected_revision",
        "title",
        "synopsis",
        "premise",
        "explanation",
    }
    tag_fields = {
        "genres",
        "game_systems",
        "settings",
        "party_size_min",
        "party_size_max",
        "level_min",
        "level_max",
        "combat_intensity",
        "keywords",
    }
    require_allowed_fields(fields, required | tag_fields)
    values = {name: one_form_value(fields, name) for name in required}
    require_revision_value(values["expected_revision"])
    submitted_tag_fields = tag_fields & set(fields)
    if submitted_tag_fields and submitted_tag_fields != tag_fields:
        raise InvalidFormError("Adventure tag fields must be submitted together.")
    tags = None
    if submitted_tag_fields:
        tag_values = {name: one_form_value(fields, name) for name in tag_fields}
        tags = adventure_tags_from_values(tag_values)
    return (
        AdventureEditValues(
            title=values["title"],
            synopsis=values["synopsis"],
            premise=values["premise"],
            explanation=values["explanation"],
            tags=tags,
            expected_revision=values["expected_revision"],
        ),
        values["csrf_token"],
    )


def parse_encounter_form(
    environ: WSGIEnvironment,
    *,
    include_return_to: bool = False,
) -> tuple[EncounterEditValues, str]:
    """Parse encounter editor values and their CSRF token."""
    fields = parse_form_fields(environ, max_num_fields=15 if include_return_to else 14)
    allowed = {
        "csrf_token",
        "expected_revision",
        "title",
        "summary",
        "opening_view",
        "content",
        "tags",
        "required",
        "start",
        "end",
    }
    if include_return_to:
        allowed.add("return_to")
    require_allowed_fields(fields, allowed)
    required = (
        "csrf_token",
        "expected_revision",
        "title",
        "summary",
        "opening_view",
        "content",
        "tags",
    )
    values = {name: one_form_value(fields, name) for name in required}
    require_revision_value(values["expected_revision"])
    return (
        EncounterEditValues(
            title=values["title"],
            summary=values["summary"],
            opening_view=values["opening_view"],
            content=values["content"],
            tags=values["tags"],
            required=checkbox_value(fields, "required"),
            start=checkbox_value(fields, "start"),
            end=checkbox_value(fields, "end"),
            expected_revision=values["expected_revision"],
            return_to=_play_return_to(fields) if include_return_to else "",
        ),
        values["csrf_token"],
    )


def parse_encounter_create_form(
    environ: WSGIEnvironment,
) -> tuple[EncounterCreateValues, str]:
    """Parse encounter creation values and their CSRF token."""
    values, token = parse_encounter_form(environ, include_return_to=True)
    return (
        EncounterCreateValues(
            title=values.title,
            summary=values.summary,
            opening_view=values.opening_view,
            content=values.content,
            tags=values.tags,
            required=values.required,
            start=values.start,
            end=values.end,
            expected_revision=values.expected_revision,
            return_to=values.return_to,
        ),
        token,
    )


def parse_clue_form(
    environ: WSGIEnvironment,
    *,
    include_return_to: bool = False,
) -> tuple[ClueCreateValues, str]:
    """Parse clue values and their CSRF token."""
    fields = parse_form_fields(environ, max_num_fields=13 if include_return_to else 12)
    required = (
        "csrf_token",
        "expected_revision",
        "title",
        "source_encounter_id",
        "revelation_id",
        "description",
        "discovery",
    )
    allowed: set[str] = set(required)
    if include_return_to:
        allowed.add("return_to")
    require_allowed_fields(fields, allowed)
    values = {name: one_form_value(fields, name) for name in required}
    require_revision_value(values["expected_revision"])
    return (
        ClueCreateValues(
            title=values["title"],
            source_encounter_id=values["source_encounter_id"],
            revelation_id=values["revelation_id"],
            description=values["description"],
            discovery=values["discovery"],
            expected_revision=values["expected_revision"],
            return_to=_play_return_to(fields) if include_return_to else "",
        ),
        values["csrf_token"],
    )


def parse_revelation_form(
    environ: WSGIEnvironment,
    *,
    include_return_to: bool = False,
) -> tuple[RevelationCreateValues, str]:
    """Parse revelation values and their CSRF token."""
    fields = parse_form_fields(environ, max_num_fields=13 if include_return_to else 12)
    allowed = {
        "csrf_token",
        "expected_revision",
        "title",
        "description",
        "unlocks_encounter_id",
        "required",
        "source_encounter_id",
    }
    if include_return_to:
        allowed.add("return_to")
    require_allowed_fields(fields, allowed)
    required = (
        "csrf_token",
        "expected_revision",
        "title",
        "description",
        "unlocks_encounter_id",
        "source_encounter_id",
    )
    values = {name: one_form_value(fields, name) for name in required}
    require_revision_value(values["expected_revision"])
    return (
        RevelationCreateValues(
            title=values["title"],
            description=values["description"],
            unlocks_encounter_id=values["unlocks_encounter_id"],
            required=checkbox_value(fields, "required"),
            source_encounter_id=values["source_encounter_id"],
            expected_revision=values["expected_revision"],
            return_to=_play_return_to(fields) if include_return_to else "",
        ),
        values["csrf_token"],
    )


def parse_clue_edit_form(environ: WSGIEnvironment) -> tuple[ClueEditValues, str]:
    """Parse clue editor values and their CSRF token."""
    values, token = parse_clue_form(environ)
    return (
        ClueEditValues(
            title=values.title,
            source_encounter_id=values.source_encounter_id,
            revelation_id=values.revelation_id,
            description=values.description,
            discovery=values.discovery,
            expected_revision=values.expected_revision,
        ),
        token,
    )


def parse_revelation_edit_form(
    environ: WSGIEnvironment,
) -> tuple[RevelationEditValues, str]:
    """Parse revelation editor values and their CSRF token."""
    values, token = parse_revelation_form(environ)
    return (
        RevelationEditValues(
            title=values.title,
            description=values.description,
            unlocks_encounter_id=values.unlocks_encounter_id,
            required=values.required,
            expected_revision=values.expected_revision,
        ),
        token,
    )


def parse_reference_form(
    environ: WSGIEnvironment,
    *,
    include_encounter: bool,
) -> tuple[ReferenceCreateValues | ReferenceEditValues, str]:
    """Parse reference editor values and their CSRF token."""
    fields = parse_form_fields(environ, max_num_fields=13)
    required = {
        "csrf_token",
        "expected_revision",
        "kind",
        "title",
        "aliases",
        "summary",
        "content",
        "tags",
    }
    allowed = set(required)
    if include_encounter:
        allowed.update({"encounter_id", "context", "return_to"})
    require_allowed_fields(fields, allowed)
    values = {name: one_form_value(fields, name) for name in required}
    require_revision_value(values["expected_revision"])
    if include_encounter:
        return (
            ReferenceCreateValues(
                kind=values["kind"],
                title=values["title"],
                aliases=values["aliases"],
                summary=values["summary"],
                content=values["content"],
                tags=values["tags"],
                expected_revision=values["expected_revision"],
                encounter_id=one_form_value(fields, "encounter_id"),
                context=one_form_value(fields, "context"),
                return_to=_play_return_to(fields),
            ),
            values["csrf_token"],
        )
    return (
        ReferenceEditValues(
            kind=values["kind"],
            title=values["title"],
            aliases=values["aliases"],
            summary=values["summary"],
            content=values["content"],
            tags=values["tags"],
            expected_revision=values["expected_revision"],
        ),
        values["csrf_token"],
    )


def parse_reference_link_form(
    environ: WSGIEnvironment,
) -> tuple[ReferenceLinkValues, str]:
    """Parse one existing-reference link form."""
    fields = parse_form_fields(environ, max_num_fields=4)
    required = {"csrf_token", "expected_revision", "reference_id", "context"}
    require_allowed_fields(fields, required)
    revision = one_form_value(fields, "expected_revision")
    require_revision_value(revision)
    return (
        ReferenceLinkValues(
            expected_revision=revision,
            reference_id=one_form_value(fields, "reference_id"),
            context=one_form_value(fields, "context"),
        ),
        one_form_value(fields, "csrf_token"),
    )


def parse_reference_unlink_form(
    environ: WSGIEnvironment,
) -> tuple[ReferenceUnlinkValues, str]:
    """Parse one encounter/reference unlink form."""
    fields = parse_form_fields(environ, max_num_fields=3)
    required = {"csrf_token", "expected_revision", "reference_id"}
    require_allowed_fields(fields, required)
    revision = one_form_value(fields, "expected_revision")
    require_revision_value(revision)
    return (
        ReferenceUnlinkValues(
            expected_revision=revision,
            reference_id=one_form_value(fields, "reference_id"),
        ),
        one_form_value(fields, "csrf_token"),
    )


def parse_removal_form(environ: WSGIEnvironment) -> tuple[RemovalValues, str]:
    """Parse one dependency-aware removal form."""
    fields = parse_form_fields(environ, max_num_fields=3)
    require_allowed_fields(fields, {"csrf_token", "expected_revision", "cascade"})
    revision = one_form_value(fields, "expected_revision")
    require_revision_value(revision)
    return (
        RemovalValues(
            expected_revision=revision,
            cascade=checkbox_value(fields, "cascade"),
        ),
        one_form_value(fields, "csrf_token"),
    )


def _play_return_to(fields: dict[str, list[str]]) -> str:
    """Return one optional, canonical Play-table return target from a create form."""
    values = fields.get("return_to", [])
    if not values:
        return ""
    if len(values) != 1:
        raise InvalidFormError("Form field 'return_to' was submitted more than once.")
    if not values[0]:
        return ""
    normalized = normalize_play_return_target(values[0])
    if normalized is None:
        raise InvalidFormError("The authoring return target is invalid.")
    return normalized


def parse_publish_report_form(environ: WSGIEnvironment) -> tuple[str, str]:
    """Parse the expected revision and CSRF token for report publication."""
    fields = parse_form_fields(environ, max_num_fields=2)
    require_allowed_fields(fields, {"csrf_token", "expected_revision"})
    token = one_form_value(fields, "csrf_token")
    revision = one_form_value(fields, "expected_revision")
    require_revision_value(revision)
    return revision, token


def parse_archive_create_form(
    environ: WSGIEnvironment,
) -> tuple[ArchiveCreateValues, str]:
    """Parse archive creation values and their CSRF token."""
    fields = parse_form_fields(environ, max_num_fields=4)
    required = {"csrf_token", "expected_revision", "label", "name"}
    require_allowed_fields(fields, required)
    revision = one_form_value(fields, "expected_revision")
    require_revision_value(revision)
    return (
        ArchiveCreateValues(
            expected_revision=revision,
            label=one_form_value(fields, "label"),
            name=one_form_value(fields, "name"),
        ),
        one_form_value(fields, "csrf_token"),
    )


def parse_archive_action_form(
    environ: WSGIEnvironment,
    *,
    include_confirmation: bool,
) -> tuple[ArchiveActionValues, str]:
    """Parse archive action values and their CSRF token."""
    fields = parse_form_fields(environ, max_num_fields=3)
    allowed = {"csrf_token", "expected_revision"}
    if include_confirmation:
        allowed.add("confirmation")
    require_allowed_fields(fields, allowed)
    revision = one_form_value(fields, "expected_revision")
    require_revision_value(revision)
    confirmation = one_form_value(fields, "confirmation") if include_confirmation else ""
    return (
        ArchiveActionValues(expected_revision=revision, confirmation=confirmation),
        one_form_value(fields, "csrf_token"),
    )
