"""Form translation for adventure-workspace management and validator settings."""

from __future__ import annotations

from dataclasses import dataclass
from wsgiref.types import WSGIEnvironment

from adventure_graph.domain.adventure import AdventureTags
from adventure_graph.domain.validation_models import ValidationPolicy
from adventure_graph.interfaces.web.form_parsing import (
    InvalidFormError,
    adventure_tags_from_values,
    checkbox_value,
    one_form_value,
    parse_form_fields,
    require_allowed_fields,
    require_revision_value,
)


@dataclass(frozen=True, slots=True)
class AdventureCreateValues:
    """Submitted values for the guided new-adventure flow."""

    title: str
    synopsis: str
    premise: str
    explanation: str
    tags: AdventureTags
    opening_title: str
    opening_summary: str
    opening_view: str
    expected_revision: str


@dataclass(frozen=True, slots=True)
class WorkspaceSelectionValues:
    """Submitted adventure selection and workspace revision."""

    adventure_key: str
    expected_revision: str


def parse_adventure_create_form(
    environ: WSGIEnvironment,
) -> tuple[AdventureCreateValues, str]:
    """Parse the guided project-creation form."""
    fields = parse_form_fields(environ, max_num_fields=22)
    required = {
        "csrf_token",
        "expected_revision",
        "title",
        "synopsis",
        "premise",
        "explanation",
        "opening_title",
        "opening_summary",
        "opening_view",
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
    tags = AdventureTags()
    if submitted_tag_fields:
        tag_values = {name: one_form_value(fields, name) for name in tag_fields}
        tags = adventure_tags_from_values(tag_values)
    return (
        AdventureCreateValues(
            title=values["title"],
            synopsis=values["synopsis"],
            premise=values["premise"],
            explanation=values["explanation"],
            tags=tags,
            opening_title=values["opening_title"],
            opening_summary=values["opening_summary"],
            opening_view=values["opening_view"],
            expected_revision=values["expected_revision"],
        ),
        values["csrf_token"],
    )


def parse_workspace_selection_form(
    environ: WSGIEnvironment,
) -> tuple[WorkspaceSelectionValues, str]:
    """Parse one adventure-switch request."""
    fields = parse_form_fields(environ, max_num_fields=4)
    required = {"csrf_token", "expected_revision", "adventure_key"}
    require_allowed_fields(fields, required)
    values = {name: one_form_value(fields, name) for name in required}
    require_revision_value(values["expected_revision"])
    return (
        WorkspaceSelectionValues(
            adventure_key=values["adventure_key"],
            expected_revision=values["expected_revision"],
        ),
        values["csrf_token"],
    )


def parse_workspace_revision_form(
    environ: WSGIEnvironment,
) -> tuple[str, str]:
    """Parse a CSRF-protected mutation carrying only workspace revision."""
    fields = parse_form_fields(environ, max_num_fields=3)
    required = {"csrf_token", "expected_revision"}
    require_allowed_fields(fields, required)
    values = {name: one_form_value(fields, name) for name in required}
    require_revision_value(values["expected_revision"])
    return values["expected_revision"], values["csrf_token"]


def parse_validation_policy_form(
    environ: WSGIEnvironment,
) -> tuple[ValidationPolicy, str, str]:
    """Parse validator thresholds, reachability, revision, and CSRF token."""
    fields = parse_form_fields(environ, max_num_fields=12)
    allowed = {
        "csrf_token",
        "expected_revision",
        "minimum_clues_per_revelation",
        "minimum_source_encounters_per_revelation",
        "minimum_incoming_clues_per_encounter",
        "minimum_incoming_source_encounters_per_encounter",
        "minimum_outgoing_clues_per_encounter",
        "minimum_distinct_encounter_targets_per_encounter",
        "minimum_edge_connectivity",
        "require_directed_reachability",
    }
    require_allowed_fields(fields, allowed)
    required = allowed - {"require_directed_reachability"}
    values = {name: one_form_value(fields, name) for name in required}
    require_revision_value(values["expected_revision"])
    try:
        policy = ValidationPolicy(
            minimum_clues_per_revelation=int(values["minimum_clues_per_revelation"]),
            minimum_source_encounters_per_revelation=int(
                values["minimum_source_encounters_per_revelation"]
            ),
            minimum_incoming_clues_per_encounter=int(
                values["minimum_incoming_clues_per_encounter"]
            ),
            minimum_incoming_source_encounters_per_encounter=int(
                values["minimum_incoming_source_encounters_per_encounter"]
            ),
            minimum_outgoing_clues_per_encounter=int(
                values["minimum_outgoing_clues_per_encounter"]
            ),
            minimum_distinct_encounter_targets_per_encounter=int(
                values["minimum_distinct_encounter_targets_per_encounter"]
            ),
            minimum_edge_connectivity=int(values["minimum_edge_connectivity"]),
            require_directed_reachability=checkbox_value(fields, "require_directed_reachability"),
        )
    except ValueError as error:
        raise InvalidFormError(
            "Validator minimums must be whole numbers zero or greater."
        ) from error
    return policy, values["expected_revision"], values["csrf_token"]
