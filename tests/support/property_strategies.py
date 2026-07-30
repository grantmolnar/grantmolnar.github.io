"""Hypothesis strategies shared by feature-local property tests."""

from __future__ import annotations

from dataclasses import dataclass, replace
from string import ascii_letters, ascii_lowercase, digits
from typing import Protocol, TypeVar, cast

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from adventure_graph.application.dice import roll_dice
from adventure_graph.application.play_tracking import (
    end_session,
    establish_revelation,
    new_play_state,
    record_dice_roll,
    record_encounter_consequence,
    record_visit,
    start_session,
)
from adventure_graph.domain.adventure import (
    Adventure,
    AdventureTags,
    CombatIntensity,
    Reference,
    ReferenceKind,
    ReferenceLink,
)
from adventure_graph.domain.play_state import PlayState
from adventure_graph.domain.validation_models import ValidationPolicy
from tests.support.adventures import complete_four_encounter_adventure

T = TypeVar("T")


class Draw(Protocol):
    """Typed public shape supplied by ``hypothesis.strategies.composite``."""

    def __call__(self, strategy: SearchStrategy[T]) -> T:
        """Draw one value from a strategy."""
        ...


_WORD = st.text(alphabet=ascii_letters + digits + "'-", min_size=1, max_size=14)
_NONEMPTY_TEXT = st.lists(_WORD, min_size=1, max_size=6).map(" ".join)
_OPTIONAL_TEXT = st.lists(_WORD, min_size=0, max_size=8).map(" ".join)
_TAGS = st.lists(_WORD, max_size=5, unique_by=str.casefold).map(tuple)
_IDENTIFIER = st.lists(
    st.text(alphabet=ascii_lowercase + digits, min_size=1, max_size=8),
    min_size=1,
    max_size=3,
).map("-".join)
_REFERENCE_KINDS = st.sampled_from(("person", "place", "organization", "object", "other"))
_COMBAT_INTENSITIES = st.sampled_from((None, "none", "light", "moderate", "heavy"))


@st.composite
def authored_adventures(draw: Draw) -> Adventure:
    """Generate small canonically serializable adventures with references and tags."""
    base = complete_four_encounter_adventure()
    reference_count = draw(st.integers(min_value=0, max_value=3))
    reference_ids = draw(
        st.lists(
            st.uuids(version=4).map(str),
            min_size=reference_count,
            max_size=reference_count,
            unique=True,
        )
    )
    references: list[Reference] = []
    for index, reference_id in enumerate(reference_ids):
        title = f"{draw(_NONEMPTY_TEXT)} {index + 1}"
        aliases = (f"Alias {index + 1}",) if draw(st.booleans()) else ()
        references.append(
            Reference(
                id=reference_id,
                kind=cast(ReferenceKind, draw(_REFERENCE_KINDS)),
                title=title,
                aliases=aliases,
                summary=draw(_OPTIONAL_TEXT),
                content=draw(_OPTIONAL_TEXT),
                tags=draw(_TAGS),
            )
        )

    encounters = []
    for encounter in base.encounters:
        links = tuple(
            ReferenceLink(reference.id, draw(_OPTIONAL_TEXT))
            for reference in references
            if draw(st.booleans())
        )
        encounters.append(
            replace(
                encounter,
                title=draw(_NONEMPTY_TEXT),
                summary=draw(_OPTIONAL_TEXT),
                opening_view=draw(_OPTIONAL_TEXT),
                content=draw(_OPTIONAL_TEXT),
                tags=draw(_TAGS),
                reference_links=links,
            )
        )

    revelations = tuple(
        replace(
            revelation,
            title=draw(_NONEMPTY_TEXT),
            description=draw(_OPTIONAL_TEXT),
            required=draw(st.booleans()),
        )
        for revelation in base.revelations
    )
    clues = tuple(
        replace(
            clue,
            title=draw(_NONEMPTY_TEXT),
            description=draw(_OPTIONAL_TEXT),
            discovery=draw(st.sampled_from(("search", "conversation", "automatic", "cost"))),
        )
        for clue in base.clues
    )

    party_min = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=8)))
    party_max = draw(
        st.none()
        if party_min is None
        else st.one_of(st.none(), st.integers(min_value=party_min, max_value=12))
    )
    level_min = draw(st.one_of(st.none(), st.integers(min_value=1, max_value=15)))
    level_max = draw(
        st.none()
        if level_min is None
        else st.one_of(st.none(), st.integers(min_value=level_min, max_value=20))
    )
    tags = AdventureTags(
        genres=draw(_TAGS),
        game_systems=draw(_TAGS),
        settings=draw(_TAGS),
        party_size_min=party_min,
        party_size_max=party_max,
        level_min=level_min,
        level_max=level_max,
        combat_intensity=cast(CombatIntensity | None, draw(_COMBAT_INTENSITIES)),
        keywords=draw(_TAGS),
    )
    policy_values = draw(st.lists(st.integers(min_value=0, max_value=5), min_size=7, max_size=7))
    policy = ValidationPolicy(
        minimum_clues_per_revelation=policy_values[0],
        minimum_source_encounters_per_revelation=policy_values[1],
        minimum_incoming_clues_per_encounter=policy_values[2],
        minimum_incoming_source_encounters_per_encounter=policy_values[3],
        minimum_outgoing_clues_per_encounter=policy_values[4],
        minimum_distinct_encounter_targets_per_encounter=policy_values[5],
        minimum_edge_connectivity=policy_values[6],
        require_directed_reachability=draw(st.booleans()),
    )

    return replace(
        base,
        id=draw(_IDENTIFIER),
        title=draw(_NONEMPTY_TEXT),
        synopsis=draw(_OPTIONAL_TEXT),
        premise=draw(_OPTIONAL_TEXT),
        explanation=draw(_OPTIONAL_TEXT),
        references=tuple(references),
        encounters=tuple(encounters),
        revelations=revelations,
        clues=clues,
        tags=tags,
        validation_policy=policy,
    )


@dataclass(frozen=True, slots=True)
class DiceExpressionCase:
    """One noncanonical input and its expected canonical arithmetic."""

    source: str
    canonical: str
    dice_count: int
    maximum_total: int


DiceTerm = tuple[str, int, int, int]


@st.composite
def dice_expression_cases(draw: Draw) -> DiceExpressionCase:
    """Generate bounded ordinary notation with whitespace and case variation."""
    dice_term = st.tuples(
        st.just("dice"),
        st.sampled_from((-1, 1)),
        st.integers(min_value=1, max_value=20),
        st.integers(min_value=2, max_value=100),
    )
    modifier_term = st.tuples(
        st.just("modifier"),
        st.sampled_from((-1, 1)),
        st.integers(min_value=1, max_value=10_000),
        st.just(0),
    )
    terms: list[DiceTerm] = draw(
        st.lists(st.one_of(dice_term, modifier_term), min_size=1, max_size=8)
    )
    terms = [term for term in terms if term[0] == "modifier" or term[2] > 0]
    while sum(term[2] for term in terms if term[0] == "dice") > 80:
        terms.pop()

    source_parts: list[str] = []
    canonical_parts: list[str] = []
    dice_count = 0
    maximum_total = 0
    leading_plus = draw(st.booleans())
    for index, (kind, sign, magnitude, faces) in enumerate(terms):
        if kind == "dice":
            dice_count += magnitude
            maximum_total += sign * magnitude * faces
            omit_one = magnitude == 1 and draw(st.booleans())
            marker = "D" if draw(st.booleans()) else "d"
            body = f"{'' if omit_one else magnitude}{marker}{faces}"
            canonical_body = f"{magnitude}d{faces}"
        else:
            maximum_total += sign * magnitude
            body = str(magnitude)
            canonical_body = body

        whitespace = draw(st.sampled_from(("", " ", "  ", "\t")))
        if index == 0:
            source_sign = "-" if sign < 0 else "+" if leading_plus else ""
            source_parts.append(f"{whitespace}{source_sign}{whitespace}{body}{whitespace}")
            canonical_parts.append(f"{'-' if sign < 0 else ''}{canonical_body}")
        else:
            operator = "-" if sign < 0 else "+"
            source_parts.append(f"{whitespace}{operator}{whitespace}{body}{whitespace}")
            canonical_parts.append(f" {operator} {canonical_body}")

    return DiceExpressionCase(
        source="".join(source_parts),
        canonical="".join(canonical_parts),
        dice_count=dice_count,
        maximum_total=maximum_total,
    )


@dataclass(frozen=True, slots=True)
class JournalCase:
    """One valid authored adventure and append-only play journal."""

    adventure: Adventure
    state: PlayState


@st.composite
def valid_journal_cases(draw: Draw) -> JournalCase:
    """Generate valid journals through public commands rather than raw event construction."""
    adventure = complete_four_encounter_adventure()
    ordered_targets = ("beta", "gamma", "omega")
    selected = draw(st.sets(st.sampled_from(ordered_targets), max_size=len(ordered_targets)))
    targets = tuple(target for target in ordered_targets if target in selected)
    spotted = draw(st.sets(st.sampled_from(ordered_targets), max_size=len(ordered_targets)))
    use_session = draw(st.booleans())
    close_session = use_session and draw(st.booleans())
    record_roll = draw(st.booleans())

    state = new_play_state(adventure)
    if use_session:
        state = start_session(
            state,
            title=draw(_OPTIONAL_TEXT),
            participants=("Mara", "Sera") if draw(st.booleans()) else (),
            opening_note=draw(_OPTIONAL_TEXT),
        )

    alpha_clues = tuple(f"alpha-to-{target}" for target in targets if target in spotted)
    alpha_note = draw(_OPTIONAL_TEXT)
    state = record_visit(
        adventure,
        state,
        "alpha",
        alpha_clues,
        (alpha_note,) if alpha_note else (),
        party_label=draw(_OPTIONAL_TEXT),
    )

    for target in targets:
        support = (f"alpha-to-{target}",) if target in spotted else ()
        state = establish_revelation(
            adventure,
            state,
            f"find-{target}",
            support,
            draw(_OPTIONAL_TEXT),
        )
        visit_note = draw(_OPTIONAL_TEXT)
        state = record_visit(
            adventure,
            state,
            target,
            (f"{target}-to-alpha",),
            (visit_note,) if visit_note else (),
            party_label=draw(_OPTIONAL_TEXT),
        )
        if draw(st.booleans()):
            state = record_encounter_consequence(
                adventure,
                state,
                target,
                draw(_NONEMPTY_TEXT),
            )

    if record_roll:
        result = roll_dice("2d6 + 1", randbelow=lambda upper_bound: upper_bound - 1)
        state = record_dice_roll(state, result, draw(_OPTIONAL_TEXT))
    if close_session:
        state = end_session(state, draw(_OPTIONAL_TEXT))
    return JournalCase(adventure, state)
