"""Tests for operational play ledgers and the player-safe recap."""

from __future__ import annotations

from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)
from tests.support.projects import ReadOnlyPlayProject, read_only_play_project

from adventure_graph.application.play_ledgers import GetPlayLedgers
from adventure_graph.application.play_tracking import (
    add_visit_note,
    end_session,
    establish_revelation,
    foreclose_revelation,
    miss_clue,
    new_play_state,
    record_encounter_consequence,
    record_reference_note,
    record_visit,
    spot_clue,
    start_session,
)


def _played_project() -> ReadOnlyPlayProject:
    adventure = complete_four_encounter_adventure()
    state = start_session(
        new_play_state(adventure),
        title="Opening Night",
        played_on="2026-07-14",
        participants=("Ada", "Bert"),
        opening_note="GM-only opening note.",
    )
    state = record_visit(adventure, state, "alpha")
    state = spot_clue(adventure, state, "alpha-to-beta")
    state = add_visit_note(state, 1, "GM-only visit note.")
    state = record_encounter_consequence(adventure, state, "alpha", "GM-only consequence.")
    state = establish_revelation(
        adventure,
        state,
        "find-beta",
        ("alpha-to-beta",),
        "The group understood the route.",
    )
    state = foreclose_revelation(adventure, state, "find-omega", "The ferry burned.")
    state = end_session(state, "GM-only closing note.")

    state = start_session(state, title="Return Journey")
    state = record_visit(adventure, state, "beta", party_label="North party")
    state = miss_clue(adventure, state, "beta-to-gamma")
    state = record_visit(adventure, state, "beta", party_label="North party")
    state = spot_clue(adventure, state, "beta-to-gamma")
    state = end_session(state)
    return read_only_play_project(state, adventure, revision="ledger-revision")


def test_whole_playthrough_ledgers_keep_current_status_and_complete_history() -> None:
    result = GetPlayLedgers(_played_project()).execute("playthrough")

    clue = next(entry for entry in result.clues if entry.clue.id == "beta-to-gamma")
    assert clue.status == "found"
    assert clue.missed_visit_numbers == (2,)
    assert clue.spotted_visit_number == 3

    revelation = next(entry for entry in result.revelations if entry.revelation.id == "find-beta")
    assert revelation.status == "established"
    assert tuple(clue.id for clue in revelation.spotted_clues) == ("alpha-to-beta",)

    omega = next(entry for entry in result.revelations if entry.revelation.id == "find-omega")
    assert omega.status == "foreclosed"
    assert omega.foreclosure_reason == "The ferry burned."

    beta = next(entry for entry in result.encounters if entry.encounter.id == "beta")
    assert beta.status == "current"
    assert beta.visit_numbers == (2, 3)
    assert result.scope_label == "Whole playthrough"


def test_session_scope_reviews_latest_session_without_rewriting_global_status() -> None:
    result = GetPlayLedgers(_played_project()).execute("session")

    assert result.is_session_scope
    assert result.scope_label == "Return Journey"
    assert result.selected_session is not None
    assert result.selected_session.session_number == 2
    assert {entry.source_encounter.id for entry in result.clues} == {"beta"}

    recovered = next(entry for entry in result.clues if entry.clue.id == "beta-to-gamma")
    assert recovered.status == "found"
    assert recovered.spotted_in_scope
    assert recovered.missed_visit_numbers_in_scope == (2,)

    assert {entry.encounter.id for entry in result.encounters} == {"alpha", "beta"}
    beta = next(entry for entry in result.encounters if entry.encounter.id == "beta")
    assert beta.visit_numbers_in_scope == (2, 3)
    assert all(entry.session_number == 2 for entry in result.narrative)


def test_player_recap_is_an_allowlisted_projection_not_a_redacted_gm_ledger() -> None:
    result = GetPlayLedgers(_played_project()).execute("playthrough")
    recap = "\n".join(f"{entry.title} {entry.detail}" for entry in result.player_recap)

    assert "Alpha" in recap
    assert "alpha points to beta" in recap
    assert "Find Beta" in recap
    assert "GM-only" not in recap
    assert "beta points to gamma" in recap
    assert "missed" not in recap.lower()
    assert "foreclosed" not in recap.lower()
    assert "ferry burned" not in recap.lower()

    recap_document = result.document_index()["recap"]
    assert recap_document.name == "playthrough-recap.md"
    assert "Player-Safe Recap" in recap_document.content
    assert "discovered leads" in recap_document.content
    assert "discovered clues" not in recap_document.content
    assert "GM-only" not in recap_document.content


def test_reference_notes_are_chronological_gm_narrative_but_not_player_recap() -> None:
    adventure = reference_library_adventure()
    state = start_session(new_play_state(adventure), title="The House Opens")
    state = record_reference_note(
        adventure,
        state,
        PERSON_REFERENCE_ID,
        "Cora accepted responsibility for the hidden stair.",
    )
    state = end_session(state)

    result = GetPlayLedgers(
        read_only_play_project(state, adventure, revision="reference-note")
    ).execute("playthrough")

    note = next(entry for entry in result.narrative if entry.kind == "reference_note_recorded")
    assert note.title == "Note on Cora Pike"
    assert note.detail == "Cora accepted responsibility for the hidden stair."
    assert note.reference_id == PERSON_REFERENCE_ID
    assert note.session_number == 1
    assert all(entry.kind != "reference_note_recorded" for entry in result.player_recap)
    assert "Cora accepted responsibility" in result.document_index()["narrative"].content
    assert "Cora accepted responsibility" not in result.document_index()["recap"].content


def test_session_scope_without_explicit_sessions_is_empty_but_well_formed() -> None:
    adventure = complete_four_encounter_adventure()
    project = read_only_play_project(
        record_visit(adventure, new_play_state(adventure), "alpha"),
        adventure,
        revision="legacy",
    )

    result = GetPlayLedgers(project).execute("session")

    assert not result.is_session_scope
    assert result.selected_session is None
    assert result.scope_label == "No explicit session"
    assert result.document_index()["narrative"].name == "session-unavailable-narrative.md"
    assert result.clues == ()
    assert result.narrative == ()
    assert "No narrative events are in this scope." in result.document_index()["narrative"].content
