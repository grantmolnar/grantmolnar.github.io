"""Structural read models and revision-aware clue and revelation creation."""

from __future__ import annotations

from dataclasses import dataclass, replace

from adventure_graph.application.authoring import (
    add_clue,
    add_encounter,
    add_revelation,
    update_clue,
    update_revelation,
)
from adventure_graph.application.errors import NoChangesRequestedError
from adventure_graph.application.project import (
    AuthoringProject,
    ProjectRevision,
    RevisionConflictError,
)
from adventure_graph.application.project_integrity import validate_related_play_states
from adventure_graph.domain.adventure import (
    Adventure,
    Clue,
    Encounter,
    Revelation,
)
from adventure_graph.domain.identifiers import unique_identifier
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import ValidationReport


@dataclass(frozen=True, slots=True)
class RevelationCoverage:
    """One revelation's clue and source-encounter coverage against project policy."""

    revelation: Revelation
    supporting_clues: tuple[Clue, ...]
    source_encounters: tuple[Encounter, ...]
    clue_deficit: int
    source_deficit: int

    @property
    def is_sufficient(self) -> bool:
        """Return whether clue count and source diversity both satisfy policy."""
        return self.clue_deficit == 0 and self.source_deficit == 0


@dataclass(frozen=True, slots=True)
class EncounterGraphEdge:
    """One unique authored encounter connection with its supporting records."""

    source_encounter: Encounter
    target_encounter: Encounter
    revelations: tuple[Revelation, ...]
    clues: tuple[Clue, ...]


@dataclass(frozen=True, slots=True)
class StructuralOverviewResult:
    """Coverage, encounter edges, diagnostics, and project revision for the structure workspace."""

    adventure: Adventure
    revision: ProjectRevision
    validation_report: ValidationReport
    coverage: tuple[RevelationCoverage, ...]
    graph_edges: tuple[EncounterGraphEdge, ...]


@dataclass(frozen=True, slots=True)
class CreateEncounterCommand:
    """Requested encounter creation based on one known project revision."""

    expected_revision: ProjectRevision
    title: str
    summary: str = ""
    opening_view: str = ""
    content: str = ""
    required: bool = True
    start: bool = False
    end: bool = False
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CreateEncounterResult:
    """Committed encounter creation and the resulting project state."""

    encounter: Encounter
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class CreateClueCommand:
    """Requested clue creation based on one known project revision."""

    expected_revision: ProjectRevision
    title: str
    source_encounter_id: str
    revelation_id: str
    description: str = ""
    discovery: str = "search"


@dataclass(frozen=True, slots=True)
class UpdateClueCommand:
    """Requested clue changes based on one known project revision."""

    clue_id: str
    expected_revision: ProjectRevision
    title: str
    source_encounter_id: str
    revelation_id: str
    description: str = ""
    discovery: str = "search"


@dataclass(frozen=True, slots=True)
class UpdateClueResult:
    """Committed clue update and resulting project state."""

    before: Clue
    after: Clue
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class UpdateRevelationCommand:
    """Requested revelation changes based on one known project revision."""

    revelation_id: str
    expected_revision: ProjectRevision
    title: str
    description: str
    unlocks_encounter_id: str | None = None
    required: bool = True


@dataclass(frozen=True, slots=True)
class UpdateRevelationResult:
    """Committed revelation update and resulting project state."""

    before: Revelation
    after: Revelation
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class CreateClueResult:
    """Committed clue creation and resulting project state."""

    clue: Clue
    revision: ProjectRevision
    validation_report: ValidationReport


@dataclass(frozen=True, slots=True)
class CreateRevelationCommand:
    """Requested revelation creation based on one known project revision."""

    expected_revision: ProjectRevision
    title: str
    description: str
    unlocks_encounter_id: str | None = None
    required: bool = True


@dataclass(frozen=True, slots=True)
class CreateRevelationResult:
    """Committed revelation creation and resulting project state."""

    revelation: Revelation
    revision: ProjectRevision
    validation_report: ValidationReport


class GetStructuralOverview:
    """Load the synchronized structural authoring read model."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self) -> StructuralOverviewResult:
        """Return revelation coverage, graph edges, validation, and revision."""
        snapshot = self._project.load()
        report = validate_adventure(snapshot.adventure)
        return StructuralOverviewResult(
            adventure=snapshot.adventure,
            revision=snapshot.revision,
            validation_report=report,
            coverage=_coverage(snapshot.adventure),
            graph_edges=_graph_edges(snapshot.adventure),
        )


class CreateEncounter:
    """Create and commit one revision-aware encounter."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: CreateEncounterCommand) -> CreateEncounterResult:
        """Create an encounter without allowing stale or journal-invalidating writes."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        title = command.title.strip()
        if not title:
            raise ValueError("Encounter title must not be empty.")
        encounter = Encounter(
            id=unique_identifier(title, snapshot.adventure.encounter_index()),
            title=title,
            summary=command.summary,
            opening_view=command.opening_view,
            content=command.content,
            required=command.required,
            start=command.start,
            end=command.end,
            tags=command.tags,
        )
        adventure = add_encounter(snapshot.adventure, encounter)
        validate_related_play_states(adventure, snapshot.related_play_states)
        report = validate_adventure(adventure)
        revision = self._project.commit_adventure(adventure, snapshot.revision)
        return CreateEncounterResult(encounter, revision, report)


class CreateClue:
    """Validate and commit one revision-aware clue creation."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: CreateClueCommand) -> CreateClueResult:
        """Create a clue without allowing stale or journal-invalidating writes."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        clue = Clue(
            id=unique_identifier(command.title, snapshot.adventure.clue_index()),
            title=command.title,
            source_encounter_id=command.source_encounter_id,
            revelation_id=command.revelation_id,
            description=command.description,
            discovery=command.discovery,
        )
        adventure = add_clue(snapshot.adventure, clue)
        validate_related_play_states(adventure, snapshot.related_play_states)
        report = validate_adventure(adventure)
        revision = self._project.commit_adventure(adventure, snapshot.revision)
        return CreateClueResult(clue=clue, revision=revision, validation_report=report)


class CreateRevelation:
    """Validate and commit one revision-aware revelation creation."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: CreateRevelationCommand) -> CreateRevelationResult:
        """Create a revelation without allowing stale or journal-invalidating writes."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        revelation = Revelation(
            id=unique_identifier(command.title, snapshot.adventure.revelation_index()),
            title=command.title,
            description=command.description,
            unlocks_encounter_id=command.unlocks_encounter_id,
            required=command.required,
        )
        adventure = add_revelation(snapshot.adventure, revelation)
        validate_related_play_states(adventure, snapshot.related_play_states)
        report = validate_adventure(adventure)
        revision = self._project.commit_adventure(adventure, snapshot.revision)
        return CreateRevelationResult(
            revelation=revelation,
            revision=revision,
            validation_report=report,
        )


class UpdateClue:
    """Validate and commit one revision-aware clue edit."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: UpdateClueCommand) -> UpdateClueResult:
        """Edit a clue while preserving its stable identifier."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        before = snapshot.adventure.clue_index().get(command.clue_id)
        if before is None:
            raise ValueError(f"Unknown lead {command.clue_id!r}.")
        title = command.title.strip()
        if not title:
            raise ValueError("Lead title must not be empty.")
        after = replace(
            before,
            title=title,
            source_encounter_id=command.source_encounter_id,
            revelation_id=command.revelation_id,
            description=command.description,
            discovery=command.discovery,
        )
        if after == before:
            raise NoChangesRequestedError("No authoring changes were requested.")
        adventure = update_clue(snapshot.adventure, after)
        validate_related_play_states(adventure, snapshot.related_play_states)
        report = validate_adventure(adventure)
        revision = self._project.commit_adventure(adventure, snapshot.revision)
        return UpdateClueResult(before, after, revision, report)


class UpdateRevelation:
    """Validate and commit one revision-aware revelation edit."""

    def __init__(self, project: AuthoringProject) -> None:
        self._project = project

    def execute(self, command: UpdateRevelationCommand) -> UpdateRevelationResult:
        """Edit a revelation while preserving its stable identifier."""
        snapshot = self._project.load()
        _require_revision(snapshot.revision, command.expected_revision)
        before = snapshot.adventure.revelation_index().get(command.revelation_id)
        if before is None:
            raise ValueError(f"Unknown revelation {command.revelation_id!r}.")
        title = command.title.strip()
        if not title:
            raise ValueError("Revelation title must not be empty.")
        after = replace(
            before,
            title=title,
            description=command.description,
            unlocks_encounter_id=command.unlocks_encounter_id,
            required=command.required,
        )
        if after == before:
            raise NoChangesRequestedError("No authoring changes were requested.")
        adventure = update_revelation(snapshot.adventure, after)
        validate_related_play_states(adventure, snapshot.related_play_states)
        report = validate_adventure(adventure)
        revision = self._project.commit_adventure(adventure, snapshot.revision)
        return UpdateRevelationResult(before, after, revision, report)


def _require_revision(current: ProjectRevision, expected: ProjectRevision) -> None:
    if current != expected:
        raise RevisionConflictError(
            "The project changed after this authoring form was loaded; reload before saving."
        )


def _coverage(adventure: Adventure) -> tuple[RevelationCoverage, ...]:
    policy = adventure.validation_policy
    encounter_index = adventure.encounter_index()
    rows: list[RevelationCoverage] = []
    for revelation in adventure.revelations:
        clues = tuple(
            clue
            for clue in adventure.clues
            if clue.revelation_id == revelation.id and clue.source_encounter_id in encounter_index
        )
        source_ids = tuple(dict.fromkeys(clue.source_encounter_id for clue in clues))
        sources = tuple(encounter_index[source_id] for source_id in source_ids)
        clue_deficit = (
            max(0, policy.minimum_clues_per_revelation - len(clues)) if revelation.required else 0
        )
        source_deficit = (
            max(0, policy.minimum_source_encounters_per_revelation - len(sources))
            if revelation.required
            else 0
        )
        rows.append(
            RevelationCoverage(
                revelation=revelation,
                supporting_clues=clues,
                source_encounters=sources,
                clue_deficit=clue_deficit,
                source_deficit=source_deficit,
            )
        )
    return tuple(rows)


def _graph_edges(adventure: Adventure) -> tuple[EncounterGraphEdge, ...]:
    encounter_index = adventure.encounter_index()
    revelation_index = adventure.revelation_index()
    grouped: dict[tuple[str, str], list[Clue]] = {}
    for clue in adventure.clues:
        revelation = revelation_index.get(clue.revelation_id)
        if revelation is None or clue.source_encounter_id not in encounter_index:
            continue
        target_id = revelation.unlocks_encounter_id
        if target_id is None or target_id not in encounter_index:
            continue
        grouped.setdefault((clue.source_encounter_id, target_id), []).append(clue)

    edges: list[EncounterGraphEdge] = []
    for (source_id, target_id), clues in sorted(grouped.items()):
        revelation_ids = tuple(dict.fromkeys(clue.revelation_id for clue in clues))
        edges.append(
            EncounterGraphEdge(
                source_encounter=encounter_index[source_id],
                target_encounter=encounter_index[target_id],
                revelations=tuple(revelation_index[item] for item in revelation_ids),
                clues=tuple(clues),
            )
        )
    return tuple(edges)
