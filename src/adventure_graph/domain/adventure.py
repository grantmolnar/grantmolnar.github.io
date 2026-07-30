"""Authored values for lead-driven adventure graphs.

The persisted model name ``Clue`` remains stable for schema and API compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, TypeAlias

from adventure_graph.domain.identifiers import is_canonical_uuid4
from adventure_graph.domain.validation_models import ValidationPolicy

CombatIntensity: TypeAlias = Literal["none", "light", "moderate", "heavy"]
ReferenceKind: TypeAlias = Literal["person", "place", "organization", "object", "other"]

_REFERENCE_KINDS = ("person", "place", "organization", "object", "other")


def _validate_reference_labels(values: tuple[str, ...], label: str) -> None:
    if any(
        not isinstance(value, str) or not value.strip() or value != value.strip()
        for value in values
    ):
        raise ValueError(f"Reference {label} must be nonempty trimmed strings.")
    if len({value.casefold() for value in values}) != len(values):
        raise ValueError(f"Reference {label} must be unique without regard to case.")


@dataclass(frozen=True, slots=True)
class AdventureTags:
    """Structured discovery facets plus open-ended descriptive keywords."""

    genres: tuple[str, ...] = ()
    game_systems: tuple[str, ...] = ()
    settings: tuple[str, ...] = ()
    party_size_min: int | None = None
    party_size_max: int | None = None
    level_min: int | None = None
    level_max: int | None = None
    combat_intensity: CombatIntensity | None = None
    keywords: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject malformed ranges and unsupported combat labels."""
        for label, values in (
            ("genre", self.genres),
            ("game system", self.game_systems),
            ("setting", self.settings),
            ("keyword", self.keywords),
        ):
            if any(not value.strip() or value != value.strip() for value in values):
                raise ValueError(f"Adventure {label} tags must be nonempty and trimmed.")
            if len({value.casefold() for value in values}) != len(values):
                raise ValueError(f"Adventure {label} tags must be unique.")
        for label, minimum, maximum in (
            ("party size", self.party_size_min, self.party_size_max),
            ("level", self.level_min, self.level_max),
        ):
            if minimum is not None and minimum < 1:
                raise ValueError(f"Adventure {label} minimum must be positive.")
            if maximum is not None and maximum < 1:
                raise ValueError(f"Adventure {label} maximum must be positive.")
            if minimum is not None and maximum is not None and minimum > maximum:
                raise ValueError(f"Adventure {label} minimum cannot exceed its maximum.")
        if self.combat_intensity not in {None, "none", "light", "moderate", "heavy"}:
            raise ValueError("Adventure combat intensity is unsupported.")


@dataclass(frozen=True, slots=True)
class ReferenceLink:
    """An encounter-owned contextual association with one adventure reference."""

    reference_id: str
    context: str = ""

    def __post_init__(self) -> None:
        """Reject malformed reference identity and non-text context values."""
        if not is_canonical_uuid4(self.reference_id):
            raise ValueError("Reference link identifier must be canonical UUIDv4 text.")
        if not isinstance(self.context, str):
            raise ValueError("Reference link context must be a string.")


@dataclass(frozen=True, slots=True)
class Reference:
    """A persistent adventure-owned person, place, organization, object, or other subject."""

    id: str
    kind: ReferenceKind
    title: str
    aliases: tuple[str, ...] = ()
    summary: str = ""
    content: str = ""
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject malformed identity, kind, names, prose, and authored-search labels."""
        if not is_canonical_uuid4(self.id):
            raise ValueError("Reference identifier must be canonical UUIDv4 text.")
        if self.kind not in _REFERENCE_KINDS:
            raise ValueError("Reference kind is unsupported.")
        if (
            not isinstance(self.title, str)
            or not self.title.strip()
            or self.title != self.title.strip()
        ):
            raise ValueError("Reference title must be a nonempty trimmed string.")
        _validate_reference_labels(self.aliases, "aliases")
        _validate_reference_labels(self.tags, "tags")
        if self.title.casefold() in {alias.casefold() for alias in self.aliases}:
            raise ValueError("Reference aliases must not duplicate the title.")
        if not isinstance(self.summary, str):
            raise ValueError("Reference summary must be a string.")
        if not isinstance(self.content, str):
            raise ValueError("Reference content must be a string.")


@dataclass(frozen=True, slots=True)
class Encounter:
    """A playable encounter, location, person, event, or higher-level scenario component."""

    id: str
    title: str
    summary: str
    opening_view: str = ""
    content: str = ""
    required: bool = True
    start: bool = False
    end: bool = False
    tags: tuple[str, ...] = ()
    reference_links: tuple[ReferenceLink, ...] = ()


@dataclass(frozen=True, slots=True)
class Revelation:
    """A conclusion supported by leads, optionally unlocking another encounter."""

    id: str
    title: str
    description: str
    unlocks_encounter_id: str | None = None
    required: bool = True


@dataclass(frozen=True, slots=True)
class Clue:
    """A persisted lead located at one encounter and supporting one revelation."""

    id: str
    title: str
    source_encounter_id: str
    revelation_id: str
    description: str = ""
    discovery: str = "search"


@dataclass(frozen=True, slots=True)
class Adventure:
    """The complete authored definition of a lead-driven adventure."""

    id: str
    title: str
    synopsis: str
    premise: str
    explanation: str
    encounters: tuple[Encounter, ...]
    revelations: tuple[Revelation, ...]
    clues: tuple[Clue, ...]
    references: tuple[Reference, ...] = ()
    tags: AdventureTags = field(default_factory=AdventureTags)
    validation_policy: ValidationPolicy = field(default_factory=ValidationPolicy)

    def encounter_index(self) -> dict[str, Encounter]:
        """Return encounters keyed by identifier."""
        return {encounter.id: encounter for encounter in self.encounters}

    def revelation_index(self) -> dict[str, Revelation]:
        """Return revelations keyed by identifier."""
        return {revelation.id: revelation for revelation in self.revelations}

    def clue_index(self) -> dict[str, Clue]:
        """Return clues keyed by identifier."""
        return {clue.id: clue for clue in self.clues}

    def reference_index(self) -> dict[str, Reference]:
        """Return references keyed by stable UUIDv4 identifier."""
        return {reference.id: reference for reference in self.references}
