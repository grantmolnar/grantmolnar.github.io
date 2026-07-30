"""Validation policy and diagnostic values for adventure graphs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

Severity: TypeAlias = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class ValidationPolicy:
    """Configurable structural requirements for an adventure graph."""

    minimum_clues_per_revelation: int = 3
    minimum_source_encounters_per_revelation: int = 3
    minimum_incoming_clues_per_encounter: int = 3
    minimum_incoming_source_encounters_per_encounter: int = 3
    minimum_outgoing_clues_per_encounter: int = 3
    minimum_distinct_encounter_targets_per_encounter: int = 3
    minimum_edge_connectivity: int = 3
    require_directed_reachability: bool = True

    def __post_init__(self) -> None:
        """Reject negative structural thresholds while permitting intentionally disabled checks."""
        values = (
            self.minimum_clues_per_revelation,
            self.minimum_source_encounters_per_revelation,
            self.minimum_incoming_clues_per_encounter,
            self.minimum_incoming_source_encounters_per_encounter,
            self.minimum_outgoing_clues_per_encounter,
            self.minimum_distinct_encounter_targets_per_encounter,
            self.minimum_edge_connectivity,
        )
        if any(value < 0 for value in values):
            raise ValueError("Validation minimums must be zero or greater.")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """One actionable structural finding."""

    code: str
    severity: Severity
    message: str
    subject_id: str | None = None
    repair: str = ""


@dataclass(frozen=True, slots=True)
class GraphRepairSuggestion:
    """One concrete clue connection that would strengthen a witnessed cut."""

    source_encounter_id: str
    target_encounter_id: str
    revelation_id: str | None = None


@dataclass(frozen=True, slots=True)
class GraphConnectivityDiagnosis:
    """Exact minimum-cut witness and authored repair candidates."""

    edge_connectivity: int
    required_edge_connectivity: int
    side_a: tuple[str, ...]
    side_b: tuple[str, ...]
    cut_edges: tuple[tuple[str, str], ...]
    additional_connections_needed: int
    repair_suggestions: tuple[GraphRepairSuggestion, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Aggregate validation result and computed graph diagnostics."""

    issues: tuple[ValidationIssue, ...]
    edge_connectivity: int | None
    connectivity_diagnosis: GraphConnectivityDiagnosis | None = None

    @property
    def is_valid(self) -> bool:
        """Return whether no error-level issue was found."""
        return all(issue.severity != "error" for issue in self.issues)
