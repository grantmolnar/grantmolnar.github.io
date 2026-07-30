"""Form translation for live-run and journal correction operations."""

from __future__ import annotations

from wsgiref.types import WSGIEnvironment

from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.run_workspace import (
    AddVisitNoteCommand,
    EstablishRevelationCommand,
    RecordEncounterConsequenceCommand,
    RecordVisitCommand,
    SpotClueCommand,
    UnlockEncounterCommand,
)
from adventure_graph.interfaces.web.form_parsing import (
    many_form_values,
    one_form_value,
    optional_positive_int,
    parse_form_fields,
    require_allowed_fields,
    require_revision_value,
    required_positive_int,
)
from adventure_graph.interfaces.web.view_models import RunFormValues


def parse_run_visit_form(
    environ: WSGIEnvironment,
) -> tuple[RunFormValues, RecordVisitCommand, str]:
    """Parse a visit form into preserved values, an application command, and its token."""
    fields = parse_form_fields(environ, max_num_fields=512)
    allowed = {"csrf_token", "expected_revision", "encounter_id", "clue_id", "note"}
    require_allowed_fields(fields, allowed)
    token, revision = _common_run_form_values(fields)
    encounter_id = one_form_value(fields, "encounter_id")
    clue_ids = many_form_values(fields, "clue_id")
    note = one_form_value(fields, "note")
    notes = (note,) if note.strip() else ()
    values = RunFormValues(
        visit_encounter_id=encounter_id,
        visit_clue_ids=clue_ids,
        visit_note=note,
    )
    return (
        values,
        RecordVisitCommand(
            expected_revision=ProjectRevision(revision),
            encounter_id=encounter_id,
            spotted_clue_ids=clue_ids,
            notes=notes,
        ),
        token,
    )


def parse_run_clue_form(
    environ: WSGIEnvironment,
) -> tuple[RunFormValues, SpotClueCommand, str]:
    """Parse a clue-discovery form into preserved values, a command, and its token."""
    fields = parse_form_fields(environ, max_num_fields=5)
    required = {"csrf_token", "expected_revision", "clue_id", "visit_number"}
    require_allowed_fields(fields, required)
    token, revision = _common_run_form_values(fields)
    clue_id = one_form_value(fields, "clue_id")
    visit_number = optional_positive_int(one_form_value(fields, "visit_number"), "visit_number")
    values = RunFormValues(clue_id=clue_id, clue_visit_number=visit_number)
    return (
        values,
        SpotClueCommand(
            expected_revision=ProjectRevision(revision),
            clue_id=clue_id,
            visit_number=visit_number,
        ),
        token,
    )


def parse_run_revelation_form(
    environ: WSGIEnvironment,
) -> tuple[RunFormValues, EstablishRevelationCommand, str]:
    """Parse a revelation form into preserved values, a command, and its token."""
    fields = parse_form_fields(environ, max_num_fields=512)
    allowed = {
        "csrf_token",
        "expected_revision",
        "revelation_id",
        "supporting_clue_id",
        "note",
    }
    require_allowed_fields(fields, allowed)
    token, revision = _common_run_form_values(fields)
    revelation_id = one_form_value(fields, "revelation_id")
    supporting_clue_ids = many_form_values(fields, "supporting_clue_id")
    note = one_form_value(fields, "note")
    values = RunFormValues(
        revelation_id=revelation_id,
        supporting_clue_ids=supporting_clue_ids,
        revelation_note=note,
    )
    return (
        values,
        EstablishRevelationCommand(
            expected_revision=ProjectRevision(revision),
            revelation_id=revelation_id,
            supporting_clue_ids=supporting_clue_ids,
            note=note,
        ),
        token,
    )


def parse_run_unlock_form(
    environ: WSGIEnvironment,
) -> tuple[RunFormValues, UnlockEncounterCommand, str]:
    """Parse an explicit unlock form into preserved values, a command, and its token."""
    fields = parse_form_fields(environ, max_num_fields=5)
    required = {"csrf_token", "expected_revision", "encounter_id", "reason"}
    require_allowed_fields(fields, required)
    token, revision = _common_run_form_values(fields)
    encounter_id = one_form_value(fields, "encounter_id")
    reason = one_form_value(fields, "reason")
    values = RunFormValues(unlock_encounter_id=encounter_id, unlock_reason=reason)
    return (
        values,
        UnlockEncounterCommand(
            expected_revision=ProjectRevision(revision),
            encounter_id=encounter_id,
            reason=reason,
        ),
        token,
    )


def parse_run_note_form(
    environ: WSGIEnvironment,
) -> tuple[RunFormValues, AddVisitNoteCommand, str]:
    """Parse a visit-note form into preserved values, a command, and its token."""
    fields = parse_form_fields(environ, max_num_fields=5)
    required = {"csrf_token", "expected_revision", "visit_number", "text"}
    require_allowed_fields(fields, required)
    token, revision = _common_run_form_values(fields)
    visit_number = required_positive_int(one_form_value(fields, "visit_number"), "visit_number")
    text = one_form_value(fields, "text")
    values = RunFormValues(note_visit_number=visit_number, note_text=text)
    return (
        values,
        AddVisitNoteCommand(
            expected_revision=ProjectRevision(revision),
            visit_number=visit_number,
            text=text,
        ),
        token,
    )


def parse_run_consequence_form(
    environ: WSGIEnvironment,
) -> tuple[RunFormValues, RecordEncounterConsequenceCommand, str]:
    """Parse a consequence form into preserved values, a command, and its token."""
    fields = parse_form_fields(environ, max_num_fields=5)
    required = {"csrf_token", "expected_revision", "encounter_id", "text"}
    require_allowed_fields(fields, required)
    token, revision = _common_run_form_values(fields)
    encounter_id = one_form_value(fields, "encounter_id")
    text = one_form_value(fields, "text")
    values = RunFormValues(consequence_encounter_id=encounter_id, consequence_text=text)
    return (
        values,
        RecordEncounterConsequenceCommand(
            expected_revision=ProjectRevision(revision),
            encounter_id=encounter_id,
            text=text,
        ),
        token,
    )


def parse_correction_form(environ: WSGIEnvironment) -> tuple[str, str, str]:
    """Parse a correction reason, revision, and CSRF token."""
    fields = parse_form_fields(environ, max_num_fields=3)
    required = ("csrf_token", "expected_revision", "reason")
    require_allowed_fields(fields, set(required))
    values = {name: one_form_value(fields, name) for name in required}
    require_revision_value(values["expected_revision"])
    return values["reason"], values["expected_revision"], values["csrf_token"]


def _common_run_form_values(fields: dict[str, list[str]]) -> tuple[str, str]:
    token = one_form_value(fields, "csrf_token")
    revision = one_form_value(fields, "expected_revision")
    require_revision_value(revision)
    return token, revision
