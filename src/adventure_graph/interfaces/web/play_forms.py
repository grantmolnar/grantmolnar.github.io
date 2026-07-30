"""Form translation for table-centered Play mode operations."""

from __future__ import annotations

import json
from typing import Literal, TypeGuard, cast, overload
from wsgiref.types import WSGIEnvironment

from adventure_graph.application.dice import (
    MAX_LABEL_CHARACTERS,
    MAX_TERMS,
    MAX_TOTAL_DICE,
    DiceExpressionError,
    DiceRollResult,
    RollDiceCommand,
    validate_dice_roll,
)
from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.run_workspace import (
    AddVisitNoteCommand,
    EndSessionCommand,
    EstablishRevelationCommand,
    MissClueCommand,
    RecordDiceRollCommand,
    RecordEncounterConsequenceCommand,
    RecordReferenceNoteCommand,
    RecordVisitCommand,
    RevelationJudgmentCommand,
    SpotClueCommand,
    StartSessionCommand,
    TransitionVisitCommand,
    UnlockEncounterCommand,
)
from adventure_graph.domain.play_events import (
    DiceGroupResult,
    DiceModifierResult,
)
from adventure_graph.interfaces.web.form_parsing import (
    InvalidFormError,
    many_form_values,
    one_form_value,
    parse_form_fields,
    parse_tags,
    require_allowed_fields,
    require_revision_value,
    required_positive_int,
)
from adventure_graph.interfaces.web.view_models import PlayFormValues


def parse_play_start_session_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, StartSessionCommand, str]:
    """Parse an explicit session-start form."""
    fields = parse_form_fields(environ, max_num_fields=9)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "title",
        "played_on",
        "participants",
        "attendance_note",
        "opening_note",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    title = one_form_value(fields, "title")
    played_on = one_form_value(fields, "played_on")
    participants = one_form_value(fields, "participants")
    attendance_note = one_form_value(fields, "attendance_note")
    opening_note = one_form_value(fields, "opening_note")
    values = PlayFormValues(
        focus_encounter_id=focus,
        session_title=title,
        session_played_on=played_on,
        session_participants=participants,
        session_attendance_note=attendance_note,
        session_opening_note=opening_note,
    )
    return (
        values,
        StartSessionCommand(
            expected_revision=ProjectRevision(revision),
            title=title,
            played_on=played_on or None,
            participants=parse_tags(participants),
            attendance_note=attendance_note,
            opening_note=opening_note,
        ),
        token,
    )


def parse_play_end_session_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, EndSessionCommand, str]:
    """Parse an explicit session-end form."""
    fields = parse_form_fields(environ, max_num_fields=5)
    allowed = {"csrf_token", "expected_revision", "focus_encounter_id", "closing_note"}
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    closing_note = one_form_value(fields, "closing_note")
    return (
        PlayFormValues(focus_encounter_id=focus, session_closing_note=closing_note),
        EndSessionCommand(ProjectRevision(revision), closing_note),
        token,
    )


def parse_play_enter_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, RecordVisitCommand, str]:
    """Parse one explicit encounter entry or revisit."""
    fields = parse_form_fields(environ, max_num_fields=6)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "encounter_id",
        "party_label",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    encounter_id = one_form_value(fields, "encounter_id")
    party_label = one_form_value(fields, "party_label")
    return (
        PlayFormValues(
            focus_encounter_id=focus,
            enter_encounter_id=encounter_id,
            enter_party_label=party_label,
        ),
        RecordVisitCommand(
            expected_revision=ProjectRevision(revision),
            encounter_id=encounter_id,
            party_label=party_label,
        ),
        token,
    )


@overload
def parse_play_clue_form(
    environ: WSGIEnvironment,
    *,
    missed: Literal[False],
) -> tuple[PlayFormValues, SpotClueCommand, str]: ...


@overload
def parse_play_clue_form(
    environ: WSGIEnvironment,
    *,
    missed: Literal[True],
) -> tuple[PlayFormValues, MissClueCommand, str]: ...


def parse_play_clue_form(
    environ: WSGIEnvironment,
    *,
    missed: bool,
) -> tuple[PlayFormValues, SpotClueCommand | MissClueCommand, str]:
    """Parse a current-visit clue discovery or missed opportunity."""
    fields = parse_form_fields(environ, max_num_fields=6)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "clue_id",
        "visit_number",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    clue_id = one_form_value(fields, "clue_id")
    visit_number = required_positive_int(one_form_value(fields, "visit_number"), "visit_number")
    values = PlayFormValues(focus_encounter_id=focus, clue_id=clue_id)
    command_type = MissClueCommand if missed else SpotClueCommand
    return (
        values,
        command_type(
            expected_revision=ProjectRevision(revision),
            clue_id=clue_id,
            visit_number=visit_number,
        ),
        token,
    )


def parse_play_revelation_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, EstablishRevelationCommand, str]:
    """Parse one revelation establishment form."""
    fields = parse_form_fields(environ, max_num_fields=512)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "revelation_id",
        "supporting_clue_id",
        "note",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    revelation_id = one_form_value(fields, "revelation_id")
    supporting_clue_ids = many_form_values(fields, "supporting_clue_id")
    note = one_form_value(fields, "note")
    values = PlayFormValues(
        focus_encounter_id=focus,
        revelation_id=revelation_id,
        supporting_clue_ids=supporting_clue_ids,
        revelation_note=note,
    )
    return (
        values,
        EstablishRevelationCommand(
            ProjectRevision(revision), revelation_id, supporting_clue_ids, note
        ),
        token,
    )


def parse_play_judgment_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, RevelationJudgmentCommand, str]:
    """Parse one revelation foreclosure or reopening form."""
    fields = parse_form_fields(environ, max_num_fields=6)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "revelation_id",
        "reason",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    revelation_id = one_form_value(fields, "revelation_id")
    reason = one_form_value(fields, "reason")
    return (
        PlayFormValues(
            focus_encounter_id=focus,
            revelation_id=revelation_id,
            judgment_reason=reason,
        ),
        RevelationJudgmentCommand(ProjectRevision(revision), revelation_id, reason),
        token,
    )


def parse_play_unlock_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, UnlockEncounterCommand, str]:
    """Parse one explicit encounter unlock from Play mode."""
    fields = parse_form_fields(environ, max_num_fields=6)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "encounter_id",
        "reason",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    encounter_id = one_form_value(fields, "encounter_id")
    reason = one_form_value(fields, "reason")
    return (
        PlayFormValues(
            focus_encounter_id=focus,
            unlock_encounter_id=encounter_id,
            unlock_reason=reason,
        ),
        UnlockEncounterCommand(ProjectRevision(revision), encounter_id, reason),
        token,
    )


def parse_play_note_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, AddVisitNoteCommand, str]:
    """Parse one committed working-notebook entry."""
    fields = parse_form_fields(environ, max_num_fields=6)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "visit_number",
        "text",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    visit_number = required_positive_int(one_form_value(fields, "visit_number"), "visit_number")
    text = one_form_value(fields, "text")
    return (
        PlayFormValues(
            focus_encounter_id=focus,
            note_visit_number=visit_number,
            note_text=text,
        ),
        AddVisitNoteCommand(ProjectRevision(revision), visit_number, text),
        token,
    )


def parse_play_reference_note_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, RecordReferenceNoteCommand, str]:
    """Parse one note associated with a persistent authored reference."""
    fields = parse_form_fields(environ, max_num_fields=6)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "reference_id",
        "text",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    reference_id = one_form_value(fields, "reference_id")
    text = one_form_value(fields, "text")
    return (
        PlayFormValues(
            focus_encounter_id=focus,
            selected_reference_id=reference_id,
            reference_note_text=text,
        ),
        RecordReferenceNoteCommand(ProjectRevision(revision), reference_id, text),
        token,
    )


def parse_play_consequence_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, RecordEncounterConsequenceCommand, str]:
    """Parse one durable current-encounter consequence."""
    fields = parse_form_fields(environ, max_num_fields=6)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "encounter_id",
        "text",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    encounter_id = one_form_value(fields, "encounter_id")
    text = one_form_value(fields, "text")
    return (
        PlayFormValues(
            focus_encounter_id=focus,
            consequence_encounter_id=encounter_id,
            consequence_text=text,
        ),
        RecordEncounterConsequenceCommand(ProjectRevision(revision), encounter_id, text),
        token,
    )


def parse_play_transition_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, TransitionVisitCommand, str]:
    """Parse one atomic current-encounter transition form."""
    fields = parse_form_fields(environ, max_num_fields=1024)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "source_visit_number",
        "note",
        "spotted_clue_id",
        "missed_clue_id",
        "established_revelation_id",
        "consequence",
        "destination_encounter_id",
        "party_label",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    source_visit_number = required_positive_int(
        one_form_value(fields, "source_visit_number"), "source_visit_number"
    )
    note = one_form_value(fields, "note")
    spotted = many_form_values(fields, "spotted_clue_id")
    missed = many_form_values(fields, "missed_clue_id")
    revelations = many_form_values(fields, "established_revelation_id")
    consequence_values = fields.get("consequence", [])
    if len(consequence_values) > 1:
        raise InvalidFormError("Expected at most one value for consequence.")
    consequence = consequence_values[0] if consequence_values else ""
    destination = one_form_value(fields, "destination_encounter_id")
    party_label = one_form_value(fields, "party_label")
    values = PlayFormValues(
        focus_encounter_id=focus,
        transition_source_visit_number=source_visit_number,
        transition_note=note,
        transition_spotted_clue_ids=spotted,
        transition_missed_clue_ids=missed,
        transition_revelation_ids=revelations,
        transition_consequence=consequence,
        transition_destination_encounter_id=destination,
        transition_party_label=party_label,
    )
    return (
        values,
        TransitionVisitCommand(
            expected_revision=ProjectRevision(revision),
            source_visit_number=source_visit_number,
            notes=(note,) if note.strip() else (),
            spotted_clue_ids=spotted,
            missed_clue_ids=missed,
            established_revelation_ids=revelations,
            consequence_texts=(consequence,) if consequence.strip() else (),
            destination_encounter_id=destination or None,
            destination_party_label=party_label,
        ),
        token,
    )


def parse_play_dice_roll_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, RollDiceCommand, str]:
    """Parse one ephemeral dice-tray roll without requiring a journal revision."""
    fields = parse_form_fields(environ, max_num_fields=5)
    allowed = {"csrf_token", "focus_encounter_id", "expression", "label"}
    require_allowed_fields(fields, allowed)
    token = one_form_value(fields, "csrf_token")
    focus = one_form_value(fields, "focus_encounter_id")
    expression = one_form_value(fields, "expression")
    label = _dice_label(fields)
    return (
        PlayFormValues(
            focus_encounter_id=focus,
            dice_expression=expression,
            dice_label=label,
        ),
        RollDiceCommand(expression),
        token,
    )


def parse_play_dice_record_form(
    environ: WSGIEnvironment,
) -> tuple[PlayFormValues, RecordDiceRollCommand, str]:
    """Parse one server-rendered roll selected for canonical recording."""
    fields = parse_form_fields(environ, max_num_fields=6)
    allowed = {
        "csrf_token",
        "expected_revision",
        "focus_encounter_id",
        "label",
        "roll_payload",
    }
    require_allowed_fields(fields, allowed)
    token, revision, focus = _common_values(fields)
    label = _dice_label(fields)
    result = _dice_roll_payload(one_form_value(fields, "roll_payload"))
    return (
        PlayFormValues(
            focus_encounter_id=focus,
            dice_expression=result.expression,
            dice_label=label,
        ),
        RecordDiceRollCommand(ProjectRevision(revision), result, label),
        token,
    )


def _dice_label(fields: dict[str, list[str]]) -> str:
    label = one_form_value(fields, "label").strip()
    if len(label) > MAX_LABEL_CHARACTERS:
        raise InvalidFormError(
            f"Dice-roll labels may not exceed {MAX_LABEL_CHARACTERS} characters."
        )
    return label


def _common_values(fields: dict[str, list[str]]) -> tuple[str, str, str]:
    token = one_form_value(fields, "csrf_token")
    revision = one_form_value(fields, "expected_revision")
    require_revision_value(revision)
    focus = one_form_value(fields, "focus_encounter_id")
    return token, revision, focus


def _dice_roll_payload(payload: str) -> DiceRollResult:
    if len(payload) > 100_000:
        raise InvalidFormError("The submitted dice result is too large.")
    try:
        data: object = json.loads(payload)
    except json.JSONDecodeError as error:
        raise InvalidFormError("The submitted dice result is not valid JSON.") from error
    expression, items, total = _dice_payload_fields(data)
    terms = _dice_payload_terms(items)
    result = DiceRollResult(expression, terms, total)
    try:
        validate_dice_roll(result)
    except DiceExpressionError as error:
        raise InvalidFormError(str(error)) from error
    return result


def _dice_payload_fields(data: object) -> tuple[str, list[object], int]:
    if not isinstance(data, dict):
        raise InvalidFormError("The submitted dice result has an invalid shape.")
    mapping = cast(dict[object, object], data)
    if set(mapping) != {"expression", "terms", "total"}:
        raise InvalidFormError("The submitted dice result has an invalid shape.")
    expression = mapping["expression"]
    raw_items = mapping["terms"]
    total = mapping["total"]
    if (
        not isinstance(expression, str)
        or not isinstance(raw_items, list)
        or not _is_json_int(total)
    ):
        raise InvalidFormError("The submitted dice result has invalid field types.")
    items = cast(list[object], raw_items)
    if not items or len(items) > MAX_TERMS:
        raise InvalidFormError("The submitted dice result has an invalid number of terms.")
    return expression, items, total


def _dice_payload_terms(
    items: list[object],
) -> tuple[DiceGroupResult | DiceModifierResult, ...]:
    terms: list[DiceGroupResult | DiceModifierResult] = []
    dice_count = 0
    for item in items:
        if not isinstance(item, dict):
            raise InvalidFormError("The submitted dice result contains an invalid term.")
        mapping = cast(dict[object, object], item)
        kind = mapping.get("kind")
        if kind == "dice":
            term = _dice_group_payload(mapping)
            dice_count += len(term.results)
            if dice_count > MAX_TOTAL_DICE:
                raise InvalidFormError("The submitted dice result contains too many dice.")
            terms.append(term)
        elif kind == "modifier":
            terms.append(_dice_modifier_payload(mapping))
        else:
            raise InvalidFormError("The submitted dice result contains an unknown term kind.")
    return tuple(terms)


def _dice_group_payload(item: dict[object, object]) -> DiceGroupResult:
    if set(item) != {"kind", "sign", "faces", "results"}:
        raise InvalidFormError("The submitted dice group has an invalid shape.")
    sign = item["sign"]
    faces = item["faces"]
    if not _is_json_int(sign) or not _is_json_int(faces):
        raise InvalidFormError("The submitted dice group has invalid field types.")
    results = _dice_result_values(item["results"])
    return DiceGroupResult(sign, faces, results)


def _dice_result_values(value: object) -> tuple[int, ...]:
    if not isinstance(value, list):
        raise InvalidFormError("The submitted dice group has invalid field types.")
    raw_values = cast(list[object], value)
    if not raw_values or len(raw_values) > MAX_TOTAL_DICE:
        raise InvalidFormError("The submitted dice group has invalid field types.")
    results: list[int] = []
    for raw_value in raw_values:
        if not _is_json_int(raw_value):
            raise InvalidFormError("The submitted dice group has invalid field types.")
        results.append(raw_value)
    return tuple(results)


def _dice_modifier_payload(item: dict[object, object]) -> DiceModifierResult:
    if set(item) != {"kind", "value"}:
        raise InvalidFormError("The submitted dice modifier has an invalid shape.")
    value = item["value"]
    if not _is_json_int(value):
        raise InvalidFormError("The submitted dice modifier has an invalid shape.")
    return DiceModifierResult(value)


def _is_json_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)
