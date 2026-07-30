"""Tests for clue and encounter graph validation."""

from __future__ import annotations

from dataclasses import replace

from tests.support.adventures import (
    PERSON_REFERENCE_ID,
    PLACE_REFERENCE_ID,
    complete_four_encounter_adventure,
    reference_library_adventure,
)

from adventure_graph.domain.adventure import (
    Clue,
    Encounter,
    Reference,
    ReferenceLink,
    Revelation,
)
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import GraphRepairSuggestion


def test_encounters_and_revelations_default_to_necessary() -> None:
    assert Encounter("scene", "Scene", "A scene.").required
    assert Revelation("truth", "Truth", "A conclusion.").required


def test_complete_four_encounter_adventure_passes_default_policy() -> None:
    report = validate_adventure(complete_four_encounter_adventure())

    assert report.is_valid
    assert report.edge_connectivity == 3
    assert report.issues == ()


def test_required_revelation_needs_three_clues_from_three_sources() -> None:
    adventure = complete_four_encounter_adventure()
    reduced_clues = tuple(
        clue for clue in adventure.clues if clue.id not in {"alpha-to-beta", "gamma-to-beta"}
    )

    report = validate_adventure(replace(adventure, clues=reduced_clues))
    codes = {issue.code for issue in report.issues if issue.subject_id == "find-beta"}

    assert "revelation-insufficient-clues" in codes
    assert "revelation-insufficient-sources" in codes


def test_optional_revelation_with_one_clue_is_exempt_from_configured_minimums() -> None:
    adventure = complete_four_encounter_adventure()
    revelations = tuple(
        replace(revelation, required=False) if revelation.id == "find-beta" else revelation
        for revelation in adventure.revelations
    )
    clues = tuple(clue for clue in adventure.clues if clue.id == "alpha-to-beta")
    relaxed = replace(
        adventure,
        revelations=revelations,
        clues=clues,
        validation_policy=replace(
            adventure.validation_policy,
            minimum_incoming_clues_per_encounter=0,
            minimum_incoming_source_encounters_per_encounter=0,
            minimum_outgoing_clues_per_encounter=0,
            minimum_distinct_encounter_targets_per_encounter=0,
            minimum_edge_connectivity=0,
            require_directed_reachability=False,
        ),
    )

    report = validate_adventure(relaxed)
    codes = {issue.code for issue in report.issues if issue.subject_id == "find-beta"}

    assert "revelation-insufficient-clues" not in codes
    assert "revelation-insufficient-sources" not in codes
    assert "optional-revelation-unclued" not in codes


def test_optional_revelation_without_clues_raises_warning() -> None:
    adventure = complete_four_encounter_adventure()
    revelations = tuple(
        replace(revelation, required=False) if revelation.id == "find-beta" else revelation
        for revelation in adventure.revelations
    )
    report = validate_adventure(
        replace(
            adventure,
            revelations=revelations,
            clues=tuple(clue for clue in adventure.clues if clue.revelation_id != "find-beta"),
            validation_policy=replace(
                adventure.validation_policy,
                minimum_incoming_clues_per_encounter=0,
                minimum_incoming_source_encounters_per_encounter=0,
                minimum_outgoing_clues_per_encounter=0,
                minimum_distinct_encounter_targets_per_encounter=0,
                minimum_edge_connectivity=0,
                require_directed_reachability=False,
            ),
        )
    )

    issue = next(issue for issue in report.issues if issue.code == "optional-revelation-unclued")

    assert issue.severity == "warning"
    assert issue.subject_id == "find-beta"
    assert report.is_valid


def test_necessary_encounter_needs_configured_incoming_clues_and_sources() -> None:
    adventure = complete_four_encounter_adventure()
    reduced = replace(
        adventure,
        clues=tuple(clue for clue in adventure.clues if clue.id == "alpha-to-beta"),
        validation_policy=replace(
            adventure.validation_policy,
            minimum_clues_per_revelation=0,
            minimum_source_encounters_per_revelation=0,
            minimum_outgoing_clues_per_encounter=0,
            minimum_distinct_encounter_targets_per_encounter=0,
            minimum_edge_connectivity=0,
            require_directed_reachability=False,
        ),
    )

    report = validate_adventure(reduced)
    codes = {issue.code for issue in report.issues if issue.subject_id == "beta"}

    assert "encounter-insufficient-incoming-clues" in codes
    assert "encounter-insufficient-incoming-sources" in codes


def test_optional_encounter_with_one_incoming_clue_is_exempt_from_configured_minimums() -> None:
    adventure = complete_four_encounter_adventure()
    encounters = tuple(
        replace(encounter, required=False) if encounter.id == "beta" else encounter
        for encounter in adventure.encounters
    )
    reduced = replace(
        adventure,
        encounters=encounters,
        clues=tuple(clue for clue in adventure.clues if clue.id == "alpha-to-beta"),
        validation_policy=replace(
            adventure.validation_policy,
            minimum_clues_per_revelation=0,
            minimum_source_encounters_per_revelation=0,
            minimum_outgoing_clues_per_encounter=0,
            minimum_distinct_encounter_targets_per_encounter=0,
            minimum_edge_connectivity=0,
            require_directed_reachability=False,
        ),
    )

    report = validate_adventure(reduced)
    codes = {issue.code for issue in report.issues if issue.subject_id == "beta"}

    assert "encounter-insufficient-incoming-clues" not in codes
    assert "encounter-insufficient-incoming-sources" not in codes
    assert "optional-encounter-unclued" not in codes


def test_optional_encounter_without_incoming_clues_raises_warning() -> None:
    adventure = complete_four_encounter_adventure()
    optional = Encounter("side-scene", "Side Scene", "An optional scene.", required=False)
    report = validate_adventure(
        replace(
            adventure,
            encounters=(*adventure.encounters, optional),
            validation_policy=replace(
                adventure.validation_policy,
                minimum_outgoing_clues_per_encounter=0,
                minimum_distinct_encounter_targets_per_encounter=0,
                minimum_edge_connectivity=0,
                require_directed_reachability=False,
            ),
        )
    )

    issue = next(issue for issue in report.issues if issue.code == "optional-encounter-unclued")

    assert issue.severity == "warning"
    assert issue.subject_id == "side-scene"
    assert report.is_valid


def test_optional_encounter_unreachable_with_authored_clue_is_warning() -> None:
    adventure = complete_four_encounter_adventure()
    optional = Encounter("side-scene", "Side Scene", "An optional scene.", required=False)
    locator = Revelation(
        "find-side-scene",
        "Find Side Scene",
        "A hidden side scene can be located.",
        unlocks_encounter_id="side-scene",
        required=False,
    )
    clue = Clue("side-to-side", "Circular lead", "side-scene", "find-side-scene")
    report = validate_adventure(
        replace(
            adventure,
            encounters=(*adventure.encounters, optional),
            revelations=(*adventure.revelations, locator),
            clues=(*adventure.clues, clue),
            validation_policy=replace(
                adventure.validation_policy,
                minimum_outgoing_clues_per_encounter=0,
                minimum_distinct_encounter_targets_per_encounter=0,
                minimum_edge_connectivity=0,
            ),
        )
    )

    issue = next(issue for issue in report.issues if issue.code == "optional-encounter-unreachable")

    assert issue.severity == "warning"
    assert issue.subject_id == "side-scene"
    assert report.is_valid


def test_low_connectivity_is_reported_even_when_thresholds_are_relaxed() -> None:
    adventure = complete_four_encounter_adventure()
    retained = {
        "alpha-to-beta",
        "beta-to-alpha",
        "beta-to-gamma",
        "gamma-to-beta",
        "gamma-to-omega",
        "omega-to-gamma",
    }
    policy = replace(
        adventure.validation_policy,
        minimum_clues_per_revelation=0,
        minimum_source_encounters_per_revelation=0,
        minimum_outgoing_clues_per_encounter=0,
        minimum_distinct_encounter_targets_per_encounter=0,
    )
    sparse = replace(
        adventure,
        clues=tuple(clue for clue in adventure.clues if clue.id in retained),
        validation_policy=policy,
    )

    report = validate_adventure(sparse)

    assert report.edge_connectivity == 1
    assert any(issue.code == "graph-edge-connectivity-low" for issue in report.issues)


def test_low_connectivity_includes_exact_cut_and_repair_candidates() -> None:
    adventure = complete_four_encounter_adventure()
    retained = {
        "alpha-to-beta",
        "beta-to-alpha",
        "beta-to-gamma",
        "gamma-to-beta",
        "gamma-to-omega",
        "omega-to-gamma",
    }
    policy = replace(
        adventure.validation_policy,
        minimum_clues_per_revelation=0,
        minimum_source_encounters_per_revelation=0,
        minimum_outgoing_clues_per_encounter=0,
        minimum_distinct_encounter_targets_per_encounter=0,
    )
    sparse = replace(
        adventure,
        clues=tuple(clue for clue in adventure.clues if clue.id in retained),
        validation_policy=policy,
    )

    report = validate_adventure(sparse)
    diagnosis = report.connectivity_diagnosis

    assert diagnosis is not None
    assert diagnosis.side_a == ("alpha",)
    assert diagnosis.side_b == ("beta", "gamma", "omega")
    assert diagnosis.cut_edges == (("alpha", "beta"),)
    assert diagnosis.additional_connections_needed == 2
    assert diagnosis.repair_suggestions == (
        GraphRepairSuggestion("alpha", "gamma", "find-gamma"),
        GraphRepairSuggestion("alpha", "omega", "find-omega"),
    )
    issue = next(issue for issue in report.issues if issue.code == "graph-edge-connectivity-low")
    assert "duplicate clues" not in issue.repair.lower()
    assert "existing encounter pair" in issue.repair


def test_connectivity_policy_reports_when_threshold_is_impossible() -> None:
    adventure = complete_four_encounter_adventure()
    three_encounters = {"alpha", "beta", "gamma"}
    reduced = replace(
        adventure,
        encounters=tuple(
            encounter for encounter in adventure.encounters if encounter.id in three_encounters
        ),
        revelations=tuple(
            revelation
            for revelation in adventure.revelations
            if revelation.unlocks_encounter_id in three_encounters
        ),
        clues=tuple(
            clue
            for clue in adventure.clues
            if clue.source_encounter_id in three_encounters
            and clue.revelation_id in {"find-alpha", "find-beta", "find-gamma"}
        ),
        validation_policy=replace(
            adventure.validation_policy,
            minimum_clues_per_revelation=0,
            minimum_source_encounters_per_revelation=0,
            minimum_outgoing_clues_per_encounter=0,
            minimum_distinct_encounter_targets_per_encounter=0,
        ),
    )

    report = validate_adventure(reduced)
    issue = next(
        issue for issue in report.issues if issue.code == "graph-edge-connectivity-impossible"
    )

    assert report.edge_connectivity == 2
    assert "at most 2" in issue.message
    assert "Add at least 1 encounter" in issue.repair


def test_revelation_and_encounter_deficits_include_concrete_repairs() -> None:
    adventure = complete_four_encounter_adventure()
    reduced = replace(
        adventure,
        clues=tuple(clue for clue in adventure.clues if clue.id == "alpha-to-beta"),
        validation_policy=replace(adventure.validation_policy, minimum_edge_connectivity=0),
    )

    report = validate_adventure(reduced)

    revelation_issue = next(
        issue
        for issue in report.issues
        if issue.code == "revelation-insufficient-sources" and issue.subject_id == "find-beta"
    )
    outgoing_issue = next(
        issue
        for issue in report.issues
        if issue.code == "encounter-insufficient-targets" and issue.subject_id == "alpha"
    )
    unreachable_issue = next(
        issue
        for issue in report.issues
        if issue.code == "encounter-unreachable" and issue.subject_id == "gamma"
    )

    assert "Candidates:" in revelation_issue.repair
    assert "find-gamma" in outgoing_issue.repair
    assert "supporting revelation 'find-gamma'" in unreachable_issue.repair


def test_empty_premise_and_explanation_raise_warnings_without_invalidating_graph() -> None:
    adventure = replace(complete_four_encounter_adventure(), premise="  ", explanation="")

    report = validate_adventure(adventure)

    assert report.is_valid
    assert {issue.code for issue in report.issues} == {
        "adventure-premise-empty",
        "adventure-explanation-empty",
    }
    assert all(issue.severity == "warning" for issue in report.issues)


def test_missing_or_duplicate_start_and_duplicate_end_encounters_raise_warnings() -> None:
    adventure = complete_four_encounter_adventure()
    no_start = replace(
        adventure,
        encounters=tuple(replace(encounter, start=False) for encounter in adventure.encounters),
    )
    duplicate_roles = replace(
        adventure,
        encounters=tuple(
            replace(
                encounter,
                start=encounter.id in {"alpha", "beta"},
                end=encounter.id in {"gamma", "omega"},
            )
            for encounter in adventure.encounters
        ),
    )

    no_start_report = validate_adventure(no_start)
    duplicate_report = validate_adventure(duplicate_roles)

    assert no_start_report.is_valid
    assert {issue.code for issue in no_start_report.issues} == {"start-encounter-missing"}
    assert duplicate_report.is_valid
    assert {issue.code for issue in duplicate_report.issues} == {
        "multiple-start-encounters",
        "multiple-end-encounters",
    }


def test_end_encounters_are_exempt_from_outgoing_clue_requirements() -> None:
    adventure = complete_four_encounter_adventure()
    without_end_clues = replace(
        adventure,
        clues=tuple(clue for clue in adventure.clues if clue.source_encounter_id != "omega"),
        validation_policy=replace(
            adventure.validation_policy,
            minimum_clues_per_revelation=0,
            minimum_source_encounters_per_revelation=0,
            minimum_edge_connectivity=0,
        ),
    )

    report = validate_adventure(without_end_clues)

    assert not any(
        issue.subject_id == "omega"
        and issue.code
        in {"encounter-insufficient-outgoing-clues", "encounter-insufficient-targets"}
        for issue in report.issues
    )


def test_revelations_unlocking_start_encounters_are_exempt_from_locator_support() -> None:
    adventure = complete_four_encounter_adventure()
    revelations = tuple(
        replace(revelation, required=True) if revelation.id == "find-alpha" else revelation
        for revelation in adventure.revelations
    )
    without_start_locators = replace(
        adventure,
        revelations=revelations,
        clues=tuple(clue for clue in adventure.clues if clue.revelation_id != "find-alpha"),
        validation_policy=replace(
            adventure.validation_policy,
            minimum_outgoing_clues_per_encounter=0,
            minimum_distinct_encounter_targets_per_encounter=0,
            minimum_edge_connectivity=0,
        ),
    )

    report = validate_adventure(without_start_locators)

    assert not any(
        issue.subject_id == "find-alpha"
        and issue.code
        in {
            "revelation-insufficient-clues",
            "revelation-insufficient-sources",
            "optional-revelation-unclued",
        }
        for issue in report.issues
    )


def test_reference_library_passes_validation_without_changing_graph_diagnostics() -> None:
    report = validate_adventure(reference_library_adventure())

    assert report.is_valid
    assert report.edge_connectivity == 3
    assert report.issues == ()


def test_duplicate_reference_identifiers_are_errors() -> None:
    adventure = reference_library_adventure()
    duplicated = replace(adventure, references=(*adventure.references, adventure.references[0]))

    report = validate_adventure(duplicated)
    issue = next(issue for issue in report.issues if issue.code == "duplicate-reference-id")

    assert issue.severity == "error"
    assert issue.subject_id == PERSON_REFERENCE_ID
    assert not report.is_valid


def test_dangling_and_duplicate_encounter_reference_links_are_errors() -> None:
    adventure = reference_library_adventure()
    alpha = adventure.encounters[0]
    missing_id = "31ab17d5-a010-4ca9-99dd-952a63cc8a8d"
    changed_alpha = replace(
        alpha,
        reference_links=(
            alpha.reference_links[0],
            alpha.reference_links[0],
            ReferenceLink(missing_id),
        ),
    )

    report = validate_adventure(
        replace(adventure, encounters=(changed_alpha, *adventure.encounters[1:]))
    )
    codes = {issue.code for issue in report.issues}

    assert "duplicate-encounter-reference-link" in codes
    assert "encounter-reference-missing" in codes
    assert not report.is_valid


def test_empty_reference_prose_is_a_warning() -> None:
    adventure = complete_four_encounter_adventure()
    title_only = Reference(PERSON_REFERENCE_ID, "person", "Cora Pike")

    report = validate_adventure(replace(adventure, references=(title_only,)))
    issue = next(issue for issue in report.issues if issue.code == "reference-prose-empty")

    assert issue.severity == "warning"
    assert issue.subject_id == PERSON_REFERENCE_ID
    assert report.is_valid


def test_ambiguous_reference_titles_and_aliases_are_warnings() -> None:
    adventure = reference_library_adventure()
    ambiguous = Reference(
        id="31ab17d5-a010-4ca9-99dd-952a63cc8a8d",
        kind="person",
        title="The Housekeeper",
        summary="A different household employee with the same exposed name.",
    )

    report = validate_adventure(replace(adventure, references=(*adventure.references, ambiguous)))
    issue = next(issue for issue in report.issues if issue.code == "reference-name-ambiguous")

    assert issue.severity == "warning"
    assert PERSON_REFERENCE_ID in issue.message
    assert ambiguous.id in issue.message
    assert report.is_valid


def test_reference_index_uses_stable_identity_instead_of_display_names() -> None:
    adventure = reference_library_adventure()

    assert adventure.reference_index()[PERSON_REFERENCE_ID].title == "Cora Pike"
    assert adventure.reference_index()[PLACE_REFERENCE_ID].title == "Blackbriar Hall"
