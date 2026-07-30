"""Structural validation and repair diagnostics for lead-driven adventure graphs."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable

from adventure_graph.domain.adventure import Adventure, Clue, Revelation
from adventure_graph.domain.graph import (
    EdgeCutWitness,
    directed_reachable,
    terminal_minimum_edge_cut,
)
from adventure_graph.domain.validation_models import (
    GraphConnectivityDiagnosis,
    GraphRepairSuggestion,
    ValidationIssue,
    ValidationReport,
)


def validate_adventure(adventure: Adventure) -> ValidationReport:
    """Validate identifiers, clue duality, reachability, and graph resilience."""
    encounter_ids = [encounter.id for encounter in adventure.encounters]
    issues = [
        *_adventure_text_issues(adventure),
        *_encounter_role_issues(adventure),
        *_duplicate_issues("encounter", encounter_ids, display_kind="encounter"),
        *_duplicate_issues("revelation", [item.id for item in adventure.revelations]),
        *_duplicate_issues("clue", [item.id for item in adventure.clues]),
        *_duplicate_issues("reference", [item.id for item in adventure.references]),
        *_reference_library_issues(adventure),
    ]

    valid_clues, graph_reference_issues = _validate_graph_references(adventure)
    issues.extend(graph_reference_issues)
    clues_by_revelation, clues_by_source = _group_clues(valid_clues)
    issues.extend(_revelation_support_issues(adventure, clues_by_revelation))
    issues.extend(_encounter_incoming_issues(adventure, valid_clues))

    encounter_edges = _encounter_edges(adventure, valid_clues)
    issues.extend(_encounter_outgoing_issues(adventure, clues_by_source, encounter_edges))
    issues.extend(_reachability_issues(adventure, encounter_ids, encounter_edges))

    required_encounter_ids = [
        encounter.id for encounter in adventure.encounters if encounter.required
    ]
    witness = terminal_minimum_edge_cut(encounter_ids, encounter_edges, required_encounter_ids)
    diagnosis = _connectivity_diagnosis(adventure, encounter_edges, witness)
    connectivity_issue = _connectivity_issue(encounter_ids, diagnosis)
    if connectivity_issue is not None:
        issues.append(connectivity_issue)

    connectivity = None if witness is None else witness.connectivity
    return ValidationReport(tuple(issues), connectivity, diagnosis)


def _validate_graph_references(
    adventure: Adventure,
) -> tuple[list[Clue], list[ValidationIssue]]:
    encounter_index = adventure.encounter_index()
    revelation_index = adventure.revelation_index()
    issues: list[ValidationIssue] = []
    valid_clues: list[Clue] = []

    for clue in adventure.clues:
        source_exists = clue.source_encounter_id in encounter_index
        revelation_exists = clue.revelation_id in revelation_index
        if not source_exists:
            issues.append(
                ValidationIssue(
                    "clue-source-missing",
                    "error",
                    f"Lead {clue.id!r} refers to missing source encounter "
                    f"{clue.source_encounter_id!r}.",
                    clue.id,
                    "Change the lead source to an existing encounter or create the "
                    "referenced encounter.",
                )
            )
        if not revelation_exists:
            issues.append(
                ValidationIssue(
                    "clue-revelation-missing",
                    "error",
                    f"Lead {clue.id!r} refers to missing revelation {clue.revelation_id!r}.",
                    clue.id,
                    "Change the lead destination to an existing revelation or create it.",
                )
            )
        if source_exists and revelation_exists:
            valid_clues.append(clue)

    issues.extend(
        ValidationIssue(
            "revelation-encounter-missing",
            "error",
            f"Revelation {revelation.id!r} unlocks missing encounter "
            f"{revelation.unlocks_encounter_id!r}.",
            revelation.id,
            "Change the unlocked encounter identifier or create the referenced encounter.",
        )
        for revelation in adventure.revelations
        if revelation.unlocks_encounter_id is not None
        and revelation.unlocks_encounter_id not in encounter_index
    )
    return valid_clues, issues


def _reference_library_issues(adventure: Adventure) -> list[ValidationIssue]:
    reference_ids = {reference.id for reference in adventure.references}
    issues: list[ValidationIssue] = []

    issues.extend(
        ValidationIssue(
            "reference-prose-empty",
            "warning",
            f"Reference {reference.id!r} has neither summary nor detailed content.",
            reference.id,
            "Add a concise summary, detailed Markdown content, or both when the subject "
            "needs more than a title.",
        )
        for reference in adventure.references
        if not reference.summary.strip() and not reference.content.strip()
    )

    exposed_names: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for reference in adventure.references:
        for name in (reference.title, *reference.aliases):
            exposed_names[name.casefold()].append((reference.id, name))
    for matches in exposed_names.values():
        distinct_records = {reference_id for reference_id, _name in matches}
        if len(distinct_records) < 2:
            continue
        displayed_name = matches[0][1]
        identifiers = tuple(dict.fromkeys(reference_id for reference_id, _name in matches))
        issues.append(
            ValidationIssue(
                "reference-name-ambiguous",
                "warning",
                f"The exposed reference name {displayed_name!r} is shared by records "
                f"{_quoted(identifiers)}.",
                identifiers[0],
                "Keep the shared name when intentional; otherwise revise a title or alias so "
                "authored search results are unambiguous.",
            )
        )

    for encounter in adventure.encounters:
        linked_ids = [link.reference_id for link in encounter.reference_links]
        for reference_id, count in Counter(linked_ids).items():
            if count > 1:
                issues.append(
                    ValidationIssue(
                        "duplicate-encounter-reference-link",
                        "error",
                        f"Encounter {encounter.id!r} links reference {reference_id!r} "
                        "more than once.",
                        encounter.id,
                        "Keep one contextual link for this encounter and reference.",
                    )
                )
        issues.extend(
            ValidationIssue(
                "encounter-reference-missing",
                "error",
                f"Encounter {encounter.id!r} links missing reference {link.reference_id!r}.",
                encounter.id,
                "Change the link to an existing reference or create the referenced record.",
            )
            for link in encounter.reference_links
            if link.reference_id not in reference_ids
        )
    return issues


def _group_clues(
    clues: Iterable[Clue],
) -> tuple[dict[str, list[Clue]], dict[str, list[Clue]]]:
    clues_by_revelation: dict[str, list[Clue]] = defaultdict(list)
    clues_by_source: dict[str, list[Clue]] = defaultdict(list)
    for clue in clues:
        clues_by_revelation[clue.revelation_id].append(clue)
        clues_by_source[clue.source_encounter_id].append(clue)
    return clues_by_revelation, clues_by_source


def _revelation_support_issues(
    adventure: Adventure, clues_by_revelation: dict[str, list[Clue]]
) -> list[ValidationIssue]:
    policy = adventure.validation_policy
    start_ids = {encounter.id for encounter in adventure.encounters if encounter.start}
    issues: list[ValidationIssue] = []
    for revelation in adventure.revelations:
        if revelation.unlocks_encounter_id in start_ids:
            continue
        supporting = clues_by_revelation[revelation.id]
        if not revelation.required:
            if not supporting:
                issues.append(
                    ValidationIssue(
                        "optional-revelation-unclued",
                        "warning",
                        f"Optional revelation {revelation.id!r} has no supporting leads.",
                        revelation.id,
                        "Add at least one lead so the optional revelation can arise in play.",
                    )
                )
            continue
        source_ids = {clue.source_encounter_id for clue in supporting}
        clue_deficit = max(0, policy.minimum_clues_per_revelation - len(supporting))
        source_deficit = max(0, policy.minimum_source_encounters_per_revelation - len(source_ids))
        candidates = _candidate_source_encounters(
            adventure,
            source_ids,
            revelation.unlocks_encounter_id,
        )
        if clue_deficit:
            repair = f"Add {clue_deficit} lead(s) supporting {revelation.id!r}."
            if source_deficit and candidates:
                repair += f" Prefer new source encounters: {_quoted(candidates)}."
            issues.append(
                ValidationIssue(
                    "revelation-insufficient-clues",
                    "error",
                    f"Necessary revelation {revelation.id!r} has {len(supporting)} leads; "
                    f"requires {policy.minimum_clues_per_revelation}.",
                    revelation.id,
                    repair,
                )
            )
        if source_deficit:
            repair = (
                f"Add supporting leads at {source_deficit} additional source "
                f"encounter{'s' if source_deficit != 1 else ''}."
            ) + (f" Candidates: {_quoted(candidates)}." if candidates else "")
            issues.append(
                ValidationIssue(
                    "revelation-insufficient-sources",
                    "error",
                    f"Necessary revelation {revelation.id!r} has leads from {len(source_ids)} "
                    "distinct encounters; requires "
                    f"{policy.minimum_source_encounters_per_revelation}.",
                    revelation.id,
                    repair,
                )
            )
    return issues


def _encounter_incoming_issues(
    adventure: Adventure,
    valid_clues: Iterable[Clue],
) -> list[ValidationIssue]:
    """Validate necessary-encounter locator coverage and optional-encounter discoverability."""
    revelation_index = adventure.revelation_index()
    clues_by_target: dict[str, list[Clue]] = defaultdict(list)
    for clue in valid_clues:
        target = revelation_index[clue.revelation_id].unlocks_encounter_id
        if target is not None:
            clues_by_target[target].append(clue)

    policy = adventure.validation_policy
    issues: list[ValidationIssue] = []
    for encounter in adventure.encounters:
        if encounter.start:
            continue
        incoming = clues_by_target[encounter.id]
        source_ids = {clue.source_encounter_id for clue in incoming}
        if not encounter.required:
            if not incoming:
                issues.append(
                    ValidationIssue(
                        "optional-encounter-unclued",
                        "warning",
                        f"Optional encounter {encounter.id!r} has no leads leading to it.",
                        encounter.id,
                        "Add at least one lead supporting a revelation that unlocks this "
                        "encounter.",
                    )
                )
            continue

        clue_deficit = max(0, policy.minimum_incoming_clues_per_encounter - len(incoming))
        source_deficit = max(
            0,
            policy.minimum_incoming_source_encounters_per_encounter - len(source_ids),
        )
        unlocking = tuple(
            revelation
            for revelation in adventure.revelations
            if revelation.unlocks_encounter_id == encounter.id
        )
        if clue_deficit:
            repair = (
                f"Add {clue_deficit} lead(s) leading to {encounter.id!r} through an unlocking "
                "revelation."
            )
            if not unlocking:
                repair = (
                    f"Create a revelation unlocking {encounter.id!r}, then add at least "
                    f"{policy.minimum_incoming_clues_per_encounter} supporting lead(s)."
                )
            issues.append(
                ValidationIssue(
                    "encounter-insufficient-incoming-clues",
                    "error",
                    f"Necessary encounter {encounter.id!r} has {len(incoming)} leads "
                    "leading to it; "
                    f"requires {policy.minimum_incoming_clues_per_encounter}.",
                    encounter.id,
                    repair,
                )
            )
        if source_deficit:
            repair = (
                f"Add leads leading to this encounter from {source_deficit} additional source "
                f"encounter{'s' if source_deficit != 1 else ''}."
            )
            issues.append(
                ValidationIssue(
                    "encounter-insufficient-incoming-sources",
                    "error",
                    f"Necessary encounter {encounter.id!r} has incoming leads from "
                    f"{len(source_ids)} "
                    "distinct encounters; requires "
                    f"{policy.minimum_incoming_source_encounters_per_encounter}.",
                    encounter.id,
                    repair,
                )
            )
    return issues


def _encounter_outgoing_issues(
    adventure: Adventure,
    clues_by_source: dict[str, list[Clue]],
    encounter_edges: tuple[tuple[str, str], ...],
) -> list[ValidationIssue]:
    outgoing_targets: dict[str, set[str]] = defaultdict(set)
    for source, target in encounter_edges:
        outgoing_targets[source].add(target)

    revelations_by_target = _revelations_by_target(adventure)
    policy = adventure.validation_policy
    issues: list[ValidationIssue] = []
    for encounter in adventure.encounters:
        if encounter.end:
            continue
        outgoing_clues = clues_by_source[encounter.id]
        clue_deficit = max(0, policy.minimum_outgoing_clues_per_encounter - len(outgoing_clues))
        target_deficit = max(
            0,
            policy.minimum_distinct_encounter_targets_per_encounter
            - len(outgoing_targets[encounter.id]),
        )
        candidates = _target_candidates(
            adventure,
            encounter.id,
            outgoing_targets[encounter.id],
            revelations_by_target,
        )
        if clue_deficit:
            repair = f"Add {clue_deficit} lead(s) at encounter {encounter.id!r}."
            if candidates:
                repair += f" Candidate destinations: {_format_target_candidates(candidates)}."
            issues.append(
                ValidationIssue(
                    "encounter-insufficient-outgoing-clues",
                    "error",
                    f"Encounter {encounter.id!r} contains {len(outgoing_clues)} leads; requires "
                    f"{policy.minimum_outgoing_clues_per_encounter}.",
                    encounter.id,
                    repair,
                )
            )
        if target_deficit:
            repair = (
                f"Add leads from this encounter to {target_deficit} new destination "
                f"encounter{'s' if target_deficit != 1 else ''}."
            )
            if candidates:
                repair += f" Candidate destinations: {_format_target_candidates(candidates)}."
            issues.append(
                ValidationIssue(
                    "encounter-insufficient-targets",
                    "error",
                    f"Encounter {encounter.id!r} points to {len(outgoing_targets[encounter.id])} "
                    "distinct encounters; requires "
                    f"{policy.minimum_distinct_encounter_targets_per_encounter}.",
                    encounter.id,
                    repair,
                )
            )
    return issues


def _reachability_issues(
    adventure: Adventure,
    encounter_ids: list[str],
    encounter_edges: tuple[tuple[str, str], ...],
) -> list[ValidationIssue]:
    start_ids = {encounter.id for encounter in adventure.encounters if encounter.start}
    if not start_ids:
        return []
    if not adventure.validation_policy.require_directed_reachability:
        return []

    reached = directed_reachable(start_ids, encounter_edges)
    reachable_sources = tuple(sorted(reached))
    revelations_by_target = _revelations_by_target(adventure)
    issues: list[ValidationIssue] = []
    encounter_index = adventure.encounter_index()
    incoming_targets = {target for _source, target in encounter_edges}
    for encounter_id in sorted(set(encounter_ids) - reached):
        encounter = encounter_index[encounter_id]
        if not encounter.required and encounter_id not in incoming_targets:
            continue
        revelations = revelations_by_target.get(encounter_id, ())
        if revelations:
            repair = (
                f"Add a lead in a reachable encounter ({_quoted(reachable_sources)}) supporting "
                f"revelation {revelations[0].id!r}, which unlocks {encounter_id!r}."
            )
        else:
            repair = (
                f"Create a revelation unlocking {encounter_id!r}, then support it with a lead in a "
                f"reachable encounter ({_quoted(reachable_sources)})."
            )
        issues.append(
            ValidationIssue(
                "encounter-unreachable" if encounter.required else "optional-encounter-unreachable",
                "error" if encounter.required else "warning",
                (
                    f"Necessary encounter {encounter_id!r} is not reachable from any "
                    "start encounter."
                    if encounter.required
                    else (
                        f"Optional encounter {encounter_id!r} has leads but is not reachable "
                        "from a start encounter."
                    )
                ),
                encounter_id,
                repair,
            )
        )
    return issues


def _connectivity_diagnosis(
    adventure: Adventure,
    encounter_edges: tuple[tuple[str, str], ...],
    witness: EdgeCutWitness | None,
) -> GraphConnectivityDiagnosis | None:
    if witness is None:
        return None
    required = adventure.validation_policy.minimum_edge_connectivity
    needed = max(0, required - witness.connectivity)
    suggestions = _connectivity_repair_suggestions(adventure, encounter_edges, witness, needed)
    return GraphConnectivityDiagnosis(
        edge_connectivity=witness.connectivity,
        required_edge_connectivity=required,
        side_a=witness.side_a,
        side_b=witness.side_b,
        cut_edges=witness.cut_edges,
        additional_connections_needed=needed,
        repair_suggestions=suggestions,
    )


def _connectivity_issue(
    encounter_ids: list[str],
    diagnosis: GraphConnectivityDiagnosis | None,
) -> ValidationIssue | None:
    if diagnosis is None or len(set(encounter_ids)) <= 1:
        return None
    required = diagnosis.required_edge_connectivity
    maximum_possible = len(set(encounter_ids)) - 1
    if required > maximum_possible:
        encounters_needed = required + 1 - len(set(encounter_ids))
        return ValidationIssue(
            "graph-edge-connectivity-impossible",
            "error",
            f"Necessary-encounter edge connectivity {required} is impossible with "
            f"{len(set(encounter_ids))} encounters; a simple graph on this many encounters "
            f"has connectivity at most {maximum_possible}.",
            repair=(
                f"Add at least {encounters_needed} "
                f"encounter{'s' if encounters_needed != 1 else ''}, "
                "or lower minimum_edge_connectivity to "
                f"{maximum_possible}."
            ),
        )
    if diagnosis.edge_connectivity >= required:
        return None
    cut_text = _format_cut_edges(diagnosis.cut_edges)
    return ValidationIssue(
        "graph-edge-connectivity-low",
        "error",
        f"The necessary-encounter structure has edge connectivity "
        f"{diagnosis.edge_connectivity}; requires {required}. The witnessed partition is joined "
        f"by {cut_text}.",
        repair=(
            f"Add at least {diagnosis.additional_connections_needed} distinct cross-partition "
            f"encounter connection{'s' if diagnosis.additional_connections_needed != 1 else ''}, "
            "then revalidate. Additional leads along an existing encounter pair "
            "do not increase structural connectivity."
        ),
    )


def _connectivity_repair_suggestions(
    adventure: Adventure,
    encounter_edges: tuple[tuple[str, str], ...],
    witness: EdgeCutWitness,
    needed: int,
) -> tuple[GraphRepairSuggestion, ...]:
    if needed <= 0:
        return ()
    existing = {
        (min(source, target), max(source, target))
        for source, target in encounter_edges
        if source != target
    }
    encounter_index = adventure.encounter_index()
    revelations_by_target = _revelations_by_target(adventure)
    outgoing_counts = Counter(source for source, _target in encounter_edges)
    candidates: list[tuple[tuple[object, ...], GraphRepairSuggestion]] = []
    for first in witness.side_a:
        for second in witness.side_b:
            pair = (min(first, second), max(first, second))
            if pair in existing:
                continue
            directions = (
                _repair_direction(
                    first,
                    second,
                    encounter_index[first].end,
                    encounter_index[second].required,
                    outgoing_counts[first],
                    revelations_by_target,
                ),
                _repair_direction(
                    second,
                    first,
                    encounter_index[second].end,
                    encounter_index[first].required,
                    outgoing_counts[second],
                    revelations_by_target,
                ),
            )
            candidates.append(min(directions, key=lambda item: item[0]))

    limit = max(6, needed)
    return tuple(item[1] for item in sorted(candidates, key=lambda item: item[0])[:limit])


def _repair_direction(
    source: str,
    target: str,
    source_end: bool,
    target_required: bool,
    outgoing_count: int,
    revelations_by_target: dict[str, tuple[Revelation, ...]],
) -> tuple[tuple[object, ...], GraphRepairSuggestion]:
    revelations = revelations_by_target.get(target, ())
    revelation = revelations[0] if revelations else None
    revelation_rank = (
        0 if revelation is not None and revelation.required else 1 if revelation else 2
    )
    score: tuple[object, ...] = (
        not target_required,
        revelation_rank,
        source_end,
        outgoing_count,
        source,
        target,
    )
    return score, GraphRepairSuggestion(
        source_encounter_id=source,
        target_encounter_id=target,
        revelation_id=None if revelation is None else revelation.id,
    )


def _candidate_source_encounters(
    adventure: Adventure,
    current_sources: set[str],
    unlocked_encounter_id: str | None,
) -> tuple[str, ...]:
    candidates = [
        encounter for encounter in adventure.encounters if encounter.id not in current_sources
    ]
    candidates.sort(
        key=lambda encounter: (
            encounter.id == unlocked_encounter_id,
            encounter.end,
            encounter.id,
        )
    )
    return tuple(encounter.id for encounter in candidates[:6])


def _target_candidates(
    adventure: Adventure,
    source_encounter_id: str,
    existing_targets: set[str],
    revelations_by_target: dict[str, tuple[Revelation, ...]],
) -> tuple[tuple[str, str | None], ...]:
    candidates: list[tuple[tuple[object, ...], tuple[str, str | None]]] = []
    for encounter in adventure.encounters:
        if (
            encounter.id == source_encounter_id
            or encounter.id in existing_targets
            or encounter.start
        ):
            continue
        revelations = revelations_by_target.get(encounter.id, ())
        revelation = revelations[0] if revelations else None
        rank = 0 if revelation is not None and revelation.required else 1 if revelation else 2
        candidates.append(
            (
                (not encounter.required, rank, encounter.end, encounter.id),
                (encounter.id, None if revelation is None else revelation.id),
            )
        )
    return tuple(item[1] for item in sorted(candidates, key=lambda item: item[0])[:6])


def _revelations_by_target(adventure: Adventure) -> dict[str, tuple[Revelation, ...]]:
    grouped: dict[str, list[Revelation]] = defaultdict(list)
    for revelation in adventure.revelations:
        if revelation.unlocks_encounter_id is not None:
            grouped[revelation.unlocks_encounter_id].append(revelation)
    return {
        target: tuple(sorted(items, key=lambda item: (not item.required, item.id)))
        for target, items in grouped.items()
    }


def _duplicate_issues(
    kind: str, identifiers: list[str], *, display_kind: str | None = None
) -> list[ValidationIssue]:
    label = display_kind or kind
    return [
        ValidationIssue(
            f"duplicate-{kind}-id",
            "error",
            f"Duplicate {label} identifier {identifier!r}.",
            identifier,
            f"Rename or remove all but one {label} using this identifier.",
        )
        for identifier, count in Counter(identifiers).items()
        if count > 1
    ]


def _adventure_text_issues(adventure: Adventure) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if not adventure.premise.strip():
        issues.append(
            ValidationIssue(
                "adventure-premise-empty",
                "warning",
                "The adventure premise is empty.",
                repair=(
                    "Write one player-facing paragraph that establishes the situation and poses "
                    "the adventure's core problem."
                ),
            )
        )
    if not adventure.explanation.strip():
        issues.append(
            ValidationIssue(
                "adventure-explanation-empty",
                "warning",
                "The GM-facing explanation is empty.",
                repair="Explain what is actually happening and what forces sustain the problem.",
            )
        )
    return issues


def _encounter_role_issues(adventure: Adventure) -> list[ValidationIssue]:
    starts = tuple(encounter for encounter in adventure.encounters if encounter.start)
    ends = tuple(encounter for encounter in adventure.encounters if encounter.end)
    issues: list[ValidationIssue] = []
    if not starts:
        issues.append(
            ValidationIssue(
                "start-encounter-missing",
                "warning",
                "No encounter is marked as the adventure's start.",
                repair="Mark the encounter where play begins as the start encounter.",
            )
        )
    if len(starts) > 1:
        issues.append(
            ValidationIssue(
                "multiple-start-encounters",
                "warning",
                "More than one encounter is marked as the adventure's start: "
                f"{_quoted(encounter.id for encounter in starts)}.",
                repair=(
                    "Keep one start encounter unless the adventure intentionally offers "
                    "several openings."
                ),
            )
        )
    if len(ends) > 1:
        issues.append(
            ValidationIssue(
                "multiple-end-encounters",
                "warning",
                "More than one encounter is marked as an adventure end: "
                f"{_quoted(encounter.id for encounter in ends)}.",
                repair=(
                    "Keep one end encounter unless the adventure intentionally has several finales."
                ),
            )
        )
    return issues


def _encounter_edges(adventure: Adventure, clues: Iterable[Clue]) -> tuple[tuple[str, str], ...]:
    encounter_index = adventure.encounter_index()
    revelation_index = adventure.revelation_index()
    edges: set[tuple[str, str]] = set()
    for clue in clues:
        revelation = revelation_index[clue.revelation_id]
        target = revelation.unlocks_encounter_id
        if target is None or target not in encounter_index:
            continue
        edges.add((clue.source_encounter_id, target))
    return tuple(sorted(edges))


def _quoted(values: Iterable[str]) -> str:
    return ", ".join(repr(value) for value in values)


def _format_target_candidates(candidates: tuple[tuple[str, str | None], ...]) -> str:
    return ", ".join(
        f"{encounter_id!r} via {revelation_id!r}"
        if revelation_id is not None
        else f"{encounter_id!r} (create an unlocking revelation)"
        for encounter_id, revelation_id in candidates
    )


def _format_cut_edges(edges: tuple[tuple[str, str], ...]) -> str:
    if not edges:
        return "no connections"
    return ", ".join(f"{source!r}—{target!r}" for source, target in edges)
