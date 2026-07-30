"""Bounded dice-expression parsing, secure rolling, and result validation."""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeAlias

from adventure_graph.domain.play_events import (
    DiceGroupResult,
    DiceModifierResult,
    DiceRollTerm,
)

MAX_EXPRESSION_CHARACTERS = 256
MAX_TERMS = 20
MAX_TOTAL_DICE = 1_000
MAX_DICE_PER_GROUP = 1_000
MAX_FACES = 1_000_000
MAX_MODIFIER = 1_000_000_000
MAX_LABEL_CHARACTERS = 160

_TERM_PATTERN = r"(?:(?P<count>\d*)[dD](?P<faces>\d+)|(?P<integer>\d+))"


class DiceExpressionError(ValueError):
    """Raised when dice notation is malformed or exceeds a resource bound."""


class DiceEntropyError(ValueError):
    """Raised when an injected entropy source violates the randbelow contract."""


@dataclass(frozen=True, slots=True)
class DiceGroupSpec:
    """One signed group of like-faced dice before results are generated."""

    sign: int
    count: int
    faces: int


@dataclass(frozen=True, slots=True)
class DiceModifierSpec:
    """One signed integer modifier before a roll is generated."""

    value: int


DiceExpressionTerm: TypeAlias = DiceGroupSpec | DiceModifierSpec


@dataclass(frozen=True, slots=True)
class ParsedDiceExpression:
    """One validated expression normalized for display and journal recording."""

    expression: str
    terms: tuple[DiceExpressionTerm, ...]
    dice_count: int


@dataclass(frozen=True, slots=True)
class DiceRollResult:
    """One complete roll with auditable individual results and a derived total."""

    expression: str
    terms: tuple[DiceRollTerm, ...]
    total: int


@dataclass(frozen=True, slots=True)
class RollDiceCommand:
    """Request one ephemeral roll from bounded ordinary dice notation."""

    expression: str


class RollDice:
    """Generate one roll through an injected randbelow-compatible entropy source."""

    def __init__(self, randbelow: Callable[[int], object] = secrets.randbelow) -> None:
        self._randbelow = randbelow

    def execute(self, command: RollDiceCommand) -> DiceRollResult:
        """Parse and roll one expression without touching canonical play state."""
        return roll_dice(command.expression, randbelow=self._randbelow)


def parse_dice_expression(expression: str) -> ParsedDiceExpression:
    """Parse bounded ordinary dice notation and return its canonical form."""
    if len(expression) > MAX_EXPRESSION_CHARACTERS:
        raise DiceExpressionError(
            f"Dice expressions may not exceed {MAX_EXPRESSION_CHARACTERS} characters."
        )
    if not expression.strip():
        raise DiceExpressionError("Enter a dice expression to roll.")

    position = _skip_whitespace(expression, 0)
    sign, position = _leading_sign(expression, position)
    terms: list[DiceExpressionTerm] = []
    dice_count = 0

    while True:
        term, position = _parse_term(expression, position, sign)
        terms.append(term)
        if len(terms) > MAX_TERMS:
            raise DiceExpressionError(f"Dice expressions may contain at most {MAX_TERMS} terms.")
        if isinstance(term, DiceGroupSpec):
            dice_count += term.count
            if dice_count > MAX_TOTAL_DICE:
                raise DiceExpressionError(
                    f"Dice expressions may roll at most {MAX_TOTAL_DICE} dice in total."
                )

        position = _skip_whitespace(expression, position)
        if position == len(expression):
            break
        operator = expression[position]
        if operator not in "+-":
            raise DiceExpressionError(f"Expected '+' or '-' at character {position + 1}.")
        sign = 1 if operator == "+" else -1
        position = _skip_whitespace(expression, position + 1)
        if position == len(expression):
            raise DiceExpressionError("A dice expression cannot end with an operator.")

    normalized = _canonical_expression(tuple(terms))
    return ParsedDiceExpression(normalized, tuple(terms), dice_count)


def roll_dice(
    expression: str,
    *,
    randbelow: Callable[[int], object] = secrets.randbelow,
) -> DiceRollResult:
    """Roll one fully parsed expression using secure or injected entropy."""
    parsed = parse_dice_expression(expression)
    results: list[DiceRollTerm] = []
    total = 0
    for term in parsed.terms:
        if isinstance(term, DiceGroupSpec):
            values = tuple(_bounded_random(randbelow, term.faces) + 1 for _ in range(term.count))
            result = DiceGroupResult(term.sign, term.faces, values)
            results.append(result)
            total += term.sign * sum(values)
        else:
            result = DiceModifierResult(term.value)
            results.append(result)
            total += term.value
    return DiceRollResult(parsed.expression, tuple(results), total)


def validate_dice_roll(result: DiceRollResult) -> None:
    """Reject a result whose expression, terms, bounds, or total disagree."""
    parsed = parse_dice_expression(result.expression)
    if parsed.expression != result.expression:
        raise DiceExpressionError(
            f"Recorded dice expression must use canonical notation {parsed.expression!r}."
        )
    if len(parsed.terms) != len(result.terms):
        raise DiceExpressionError("Recorded dice terms do not match the expression.")

    total = 0
    for spec, term in zip(parsed.terms, result.terms, strict=True):
        if isinstance(spec, DiceGroupSpec):
            if not isinstance(term, DiceGroupResult):
                raise DiceExpressionError("Recorded dice terms do not match the expression.")
            if (term.sign, len(term.results), term.faces) != (
                spec.sign,
                spec.count,
                spec.faces,
            ):
                raise DiceExpressionError("Recorded dice group does not match the expression.")
            if any(value < 1 or value > term.faces for value in term.results):
                raise DiceExpressionError("Recorded die result falls outside its die bounds.")
            total += term.sign * sum(term.results)
        else:
            if not isinstance(term, DiceModifierResult) or term.value != spec.value:
                raise DiceExpressionError("Recorded modifier does not match the expression.")
            total += term.value
    if total != result.total:
        raise DiceExpressionError(
            f"Recorded dice total {result.total} does not match the term total {total}."
        )


def format_dice_roll(result: DiceRollResult, *, label: str = "") -> str:
    """Render one compact plain-text result for notebooks and terminal output."""
    validate_dice_roll(result)
    rendered_terms: list[str] = []
    for term in result.terms:
        if isinstance(term, DiceGroupResult):
            sign = "-" if term.sign < 0 else "+"
            values = ", ".join(str(value) for value in term.results)
            subtotal = term.sign * sum(term.results)
            rendered_terms.append(
                f"{sign} {len(term.results)}d{term.faces} [{values}] = {subtotal}"
            )
        else:
            rendered_terms.append(f"{term.value:+d}")
    detail = "; ".join(rendered_terms).lstrip("+ ")
    prefix = f"{label.strip()} — " if label.strip() else ""
    return f"{prefix}{result.expression} = {result.total} ({detail})"


def _parse_term(expression: str, position: int, sign: int) -> tuple[DiceExpressionTerm, int]:
    match = re.match(_TERM_PATTERN, expression[position:])
    if match is None:
        raise DiceExpressionError(f"Expected a die group or integer at character {position + 1}.")
    if match.group("integer") is not None:
        magnitude = int(match.group("integer"))
        if magnitude > MAX_MODIFIER:
            raise DiceExpressionError(
                f"Integer modifiers may not exceed {MAX_MODIFIER:,} in absolute value."
            )
        value = sign * magnitude
        return DiceModifierSpec(0 if value == 0 else value), position + match.end()

    raw_count = match.group("count")
    count = 1 if raw_count == "" else int(raw_count)
    faces = int(match.group("faces"))
    if count <= 0:
        raise DiceExpressionError("A dice group must contain at least one die.")
    if count > MAX_DICE_PER_GROUP:
        raise DiceExpressionError(f"One dice group may contain at most {MAX_DICE_PER_GROUP} dice.")
    if faces < 2:
        raise DiceExpressionError("Dice must have at least two faces.")
    if faces > MAX_FACES:
        raise DiceExpressionError(f"Dice may have at most {MAX_FACES:,} faces.")
    return DiceGroupSpec(sign, count, faces), position + match.end()


def _leading_sign(expression: str, position: int) -> tuple[int, int]:
    if position < len(expression) and expression[position] in "+-":
        sign = 1 if expression[position] == "+" else -1
        return sign, _skip_whitespace(expression, position + 1)
    return 1, position


def _skip_whitespace(expression: str, position: int) -> int:
    while position < len(expression) and expression[position].isspace():
        position += 1
    return position


def _canonical_expression(terms: tuple[DiceExpressionTerm, ...]) -> str:
    rendered: list[str] = []
    for index, term in enumerate(terms):
        if isinstance(term, DiceGroupSpec):
            negative = term.sign < 0
            body = f"{term.count}d{term.faces}"
        else:
            negative = term.value < 0
            body = str(abs(term.value))
        if index == 0:
            rendered.append(f"{'-' if negative else ''}{body}")
        else:
            rendered.append(f" {'-' if negative else '+'} {body}")
    return "".join(rendered)


def _bounded_random(randbelow: Callable[[int], object], upper_bound: int) -> int:
    value = randbelow(upper_bound)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value >= upper_bound:
        raise DiceEntropyError(
            f"The dice entropy source returned {value!r} outside [0, {upper_bound})."
        )
    return value
