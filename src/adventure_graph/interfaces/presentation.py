"""Plain-text presentation for CLI query and validation results."""

from __future__ import annotations

from adventure_graph.application.authoring import (
    clue_dependencies,
    revelation_dependencies,
)
from adventure_graph.application.dependency_previews import DependencyPreview
from adventure_graph.application.encounter_authoring import EncounterDetail
from adventure_graph.application.reference_authoring import ReferenceDetail
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.validation_models import (
    GraphConnectivityDiagnosis,
    GraphRepairSuggestion,
    ValidationReport,
)


def print_entity_list(adventure: Adventure, kind: str) -> None:
    """Print one or all compact authored-entity inventories."""
    if kind in {"all", "encounter"}:
        _print_encounter_list(adventure)
    if kind in {"all", "reference"}:
        _print_reference_list(adventure)
    if kind in {"all", "revelation"}:
        _print_revelation_list(adventure)
    if kind in {"all", "clue"}:
        _print_clue_list(adventure)


def print_entity_inspection(adventure: Adventure, kind: str, identifier: str) -> None:
    """Print one non-encounter authored entity together with its direct dependencies."""
    if kind == "revelation":
        _print_revelation_inspection(adventure, identifier)
    elif kind == "clue":
        _print_clue_inspection(adventure, identifier)
    else:
        raise ValueError(f"Unsupported direct inspection kind {kind!r}.")


def print_encounter_detail(detail: EncounterDetail) -> None:
    """Print a transport-neutral encounter-detail read model."""
    encounter = detail.encounter
    print(f"Encounter {encounter.id}: {encounter.title}")
    print(f"Necessary: {str(encounter.required).lower()}")
    print(f"Start: {str(encounter.start).lower()}")
    print(f"End: {str(encounter.end).lower()}")
    print(f"Tags: {', '.join(encounter.tags) or 'none'}")
    print(f"Summary: {encounter.summary}")
    print("Content:")
    print(encounter.content or "  (none)")
    print("Linked references:")
    if not detail.linked_references:
        print("  none")
    for linked in detail.linked_references:
        if linked.reference is None:
            label = f"missing reference {linked.reference_id}"
        else:
            label = f"{linked.reference.title} [{linked.reference.kind}] ({linked.reference_id})"
        context = f" — {linked.context}" if linked.context else ""
        print(f"  {label}{context}")
    _print_identifier_group("Leads sourced here", tuple(clue.id for clue in detail.sourced_clues))
    _print_identifier_group(
        "Revelations unlocking this encounter",
        tuple(revelation.id for revelation in detail.unlocking_revelations),
    )
    _print_identifier_group(
        "Incoming leads through those revelations",
        tuple(clue.id for clue in detail.incoming_clues),
    )
    _print_dependency_preview(detail.dependency_preview)


def print_reference_detail(detail: ReferenceDetail) -> None:
    """Print one reference with aliases, backlinks, contexts, and removal effects."""
    reference = detail.reference
    print(f"Reference {reference.id}: {reference.title}")
    print(f"Kind: {reference.kind}")
    print(f"Aliases: {', '.join(reference.aliases) or 'none'}")
    print(f"Tags: {', '.join(reference.tags) or 'none'}")
    print(f"Summary: {reference.summary or '(none)'}")
    print("Content:")
    print(reference.content or "  (none)")
    print("Backlinks:")
    if not detail.backlinks:
        print("  none")
    for backlink in detail.backlinks:
        context = f" — {backlink.context}" if backlink.context else ""
        print(f"  {backlink.encounter.id}: {backlink.encounter.title}{context}")
    _print_dependency_preview(detail.dependency_preview)


def print_validation_report(report: ValidationReport) -> int:
    """Print a structural validation report and return its process status."""
    connectivity = "n/a" if report.edge_connectivity is None else str(report.edge_connectivity)
    print(f"necessary-encounter edge connectivity: {connectivity}")
    if report.connectivity_diagnosis is not None:
        _print_connectivity_diagnosis(report.connectivity_diagnosis)
    if not report.issues:
        print("PASS: no validation issues")
        return 0
    for issue in report.issues:
        subject = f" [{issue.subject_id}]" if issue.subject_id else ""
        print(f"{issue.severity.upper()} {issue.code}{subject}: {issue.message}")
        if issue.repair:
            print(f"  repair: {issue.repair}")
    return 0 if report.is_valid else 1


def _print_encounter_list(adventure: Adventure) -> None:
    print(f"Encounters ({len(adventure.encounters)}):")
    for encounter in adventure.encounters:
        roles = [
            name for name, active in (("start", encounter.start), ("end", encounter.end)) if active
        ]
        roles.insert(0, "necessary" if encounter.required else "optional")
        suffix = f" [{', '.join(roles)}]"
        print(f"  {encounter.id}: {encounter.title}{suffix}")


def _print_reference_list(adventure: Adventure) -> None:
    backlink_counts: dict[str, int] = {reference.id: 0 for reference in adventure.references}
    for encounter in adventure.encounters:
        for link in encounter.reference_links:
            if link.reference_id in backlink_counts:
                backlink_counts[link.reference_id] += 1
    print(f"References ({len(adventure.references)}):")
    for reference in adventure.references:
        aliases = f"; aliases: {', '.join(reference.aliases)}" if reference.aliases else ""
        print(
            f"  {reference.id}: {reference.title} "
            f"[{reference.kind}; links: {backlink_counts[reference.id]}{aliases}]"
        )


def _print_revelation_list(adventure: Adventure) -> None:
    print(f"Revelations ({len(adventure.revelations)}):")
    for revelation in adventure.revelations:
        requirement = "necessary" if revelation.required else "optional"
        destination = (
            f" -> {revelation.unlocks_encounter_id}"
            if revelation.unlocks_encounter_id is not None
            else ""
        )
        print(f"  {revelation.id}: {revelation.title} [{requirement}]{destination}")


def _print_clue_list(adventure: Adventure) -> None:
    print(f"Leads ({len(adventure.clues)}):")
    for clue in adventure.clues:
        print(f"  {clue.id}: {clue.title} [{clue.source_encounter_id} -> {clue.revelation_id}]")


def _print_revelation_inspection(adventure: Adventure, revelation_id: str) -> None:
    revelation = adventure.revelation_index().get(revelation_id)
    if revelation is None:
        raise ValueError(f"Unknown revelation {revelation_id!r}.")
    dependencies = revelation_dependencies(adventure, revelation_id)
    source_encounters = tuple(
        dict.fromkeys(
            adventure.clue_index()[clue_id].source_encounter_id
            for clue_id in dependencies.supporting_clue_ids
        )
    )
    print(f"Revelation {revelation.id}: {revelation.title}")
    print(f"Necessary: {str(revelation.required).lower()}")
    print(f"Unlocks encounter: {revelation.unlocks_encounter_id or 'none'}")
    print(f"Description: {revelation.description}")
    _print_identifier_group("Supporting leads", dependencies.supporting_clue_ids)
    _print_identifier_group("Distinct source encounters", source_encounters)


def _print_clue_inspection(adventure: Adventure, clue_id: str) -> None:
    clue = adventure.clue_index().get(clue_id)
    if clue is None:
        raise ValueError(f"Unknown lead {clue_id!r}.")
    dependencies = clue_dependencies(adventure, clue_id)
    revelation = adventure.revelation_index()[dependencies.revelation_id]
    print(f"Lead {clue.id}: {clue.title}")
    print(f"Source encounter: {dependencies.source_encounter_id}")
    print(f"Supports revelation: {dependencies.revelation_id}")
    print(f"Destination encounter: {revelation.unlocks_encounter_id or 'none'}")
    print(f"Discovery: {clue.discovery}")
    print(f"Description: {clue.description or '(none)'}")


def _print_identifier_group(label: str, identifiers: tuple[str, ...]) -> None:
    print(f"{label}: {', '.join(identifiers) or 'none'}")


def _print_dependency_preview(preview: DependencyPreview) -> None:
    print("Removal dependencies:")
    if not preview.removal_dependencies:
        print("  none")
    for item in preview.removal_dependencies:
        print(f"  {item}")
    print("Cascade effects:")
    if not preview.cascade_effects:
        print("  none")
    for item in preview.cascade_effects:
        print(f"  {item}")
    print("Journal blockers:")
    if not preview.journal_references:
        print("  none")
    for item in preview.journal_references:
        print(f"  {item}")


def _print_connectivity_diagnosis(diagnosis: GraphConnectivityDiagnosis) -> None:
    print(f"minimum cut A: {', '.join(diagnosis.side_a)}")
    print(f"minimum cut B: {', '.join(diagnosis.side_b)}")
    edges = ", ".join(f"{source}--{target}" for source, target in diagnosis.cut_edges)
    print(f"cut edges: {edges or 'none'}")
    if diagnosis.additional_connections_needed <= 0:
        return
    print(f"additional cross-cut connections needed: {diagnosis.additional_connections_needed}")
    for suggestion in diagnosis.repair_suggestions:
        print(f"  candidate: {_format_repair_suggestion(suggestion)}")


def _format_repair_suggestion(suggestion: GraphRepairSuggestion) -> str:
    if suggestion.revelation_id is None:
        return (
            f"{suggestion.source_encounter_id} -> {suggestion.target_encounter_id} "
            "via a new unlocking revelation"
        )
    return (
        f"{suggestion.source_encounter_id} -> {suggestion.target_encounter_id} "
        f"via {suggestion.revelation_id}"
    )
