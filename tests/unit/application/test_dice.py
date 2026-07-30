"""Tests for bounded dice notation and injected secure rolling."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from adventure_graph.application.dice import (
    MAX_EXPRESSION_CHARACTERS,
    MAX_TERMS,
    DiceEntropyError,
    DiceExpressionError,
    DiceRollResult,
    RollDice,
    RollDiceCommand,
    format_dice_roll,
    parse_dice_expression,
    roll_dice,
    validate_dice_roll,
)
from adventure_graph.domain.play_events import (
    DiceGroupResult,
    DiceModifierResult,
)


@pytest.mark.parametrize(
    ("source", "normalized", "dice_count"),
    [
        ("4d6", "4d6", 4),
        ("2d8 + 1d4", "2d8 + 1d4", 3),
        (" 12D10+7 ", "12d10 + 7", 12),
        ("2d20 - d4 + 3", "2d20 - 1d4 + 3", 3),
        ("-d6 + 10", "-1d6 + 10", 1),
        ("+0002d06 - 000", "2d6 + 0", 2),
    ],
)
def test_parser_normalizes_supported_notation(
    source: str, normalized: str, dice_count: int
) -> None:
    parsed = parse_dice_expression(source)

    assert parsed.expression == normalized
    assert parsed.dice_count == dice_count


@pytest.mark.parametrize(
    "source",
    [
        "",
        "   ",
        "d",
        "d1",
        "0d6",
        "1d6 +",
        "1d6 1d8",
        "1d6 + -2",
        "1 d6",
        "1001d6",
        "1d1000001",
        "1000d6 + 1d6",
        "1000000001",
        " + ",
        "1d6 * 2",
    ],
)
def test_parser_rejects_malformed_or_unbounded_notation(source: str) -> None:
    with pytest.raises(DiceExpressionError):
        parse_dice_expression(source)


def test_parser_accepts_the_exact_total_dice_limit() -> None:
    parsed = parse_dice_expression("1000d6")

    assert parsed.expression == "1000d6"
    assert parsed.dice_count == 1000


def test_parser_accepts_exact_expression_and_term_limits() -> None:
    exact_terms = "+".join("1" for _ in range(MAX_TERMS))
    exact_characters = f"1d6{' ' * (MAX_EXPRESSION_CHARACTERS - 3)}"

    assert len(exact_characters) == MAX_EXPRESSION_CHARACTERS
    assert len(parse_dice_expression(exact_terms).terms) == MAX_TERMS
    assert parse_dice_expression(exact_characters).expression == "1d6"


def test_parser_rejects_too_many_terms_and_input_characters() -> None:
    with pytest.raises(DiceExpressionError, match="at most 20 terms"):
        parse_dice_expression(" + ".join("1" for _ in range(MAX_TERMS + 1)))
    with pytest.raises(DiceExpressionError, match="256 characters"):
        parse_dice_expression("1" * (MAX_EXPRESSION_CHARACTERS + 1))


def test_roll_uses_injected_entropy_after_complete_validation() -> None:
    requested_bounds: list[int] = []
    values: Iterator[int] = iter((5, 2, 1))

    def randbelow(bound: int) -> int:
        requested_bounds.append(bound)
        return next(values)

    result = roll_dice("2d8 + d4 + 3", randbelow=randbelow)

    assert result.expression == "2d8 + 1d4 + 3"
    assert result.terms == (
        DiceGroupResult(1, 8, (6, 3)),
        DiceGroupResult(1, 4, (2,)),
        DiceModifierResult(3),
    )
    assert result.total == 14
    assert requested_bounds == [8, 8, 4]
    assert format_dice_roll(result, label="Hold the gate") == (
        "Hold the gate — 2d8 + 1d4 + 3 = 14 (2d8 [6, 3] = 9; + 1d4 [2] = 2; +3)"
    )


def test_parser_rejects_limits_before_requesting_entropy() -> None:
    calls = 0

    def randbelow(_bound: int) -> int:
        nonlocal calls
        calls += 1
        return 0

    with pytest.raises(DiceExpressionError):
        roll_dice("1001d6", randbelow=randbelow)

    assert calls == 0


def test_roll_rejects_entropy_outside_randbelow_contract() -> None:
    bad_values: tuple[object, ...] = (-1, 6, True, 1.5)
    for bad_value in bad_values:

        def invalid_randbelow(_bound: int, *, value: object = bad_value) -> object:
            return value

        with pytest.raises(DiceEntropyError):
            roll_dice("1d6", randbelow=invalid_randbelow)


def test_result_validation_checks_expression_shape_bounds_and_total() -> None:
    valid = DiceRollResult(
        "2d6 - 3",
        (DiceGroupResult(1, 6, (4, 5)), DiceModifierResult(-3)),
        6,
    )
    validate_dice_roll(valid)

    invalid_results = (
        DiceRollResult("d6", (DiceGroupResult(1, 6, (4,)),), 4),
        DiceRollResult("2d6", (DiceGroupResult(1, 6, (4,)),), 4),
        DiceRollResult("1d6", (DiceGroupResult(1, 6, (7,)),), 7),
        DiceRollResult("1d6 + 2", (DiceGroupResult(1, 6, (4,)), DiceModifierResult(3)), 7),
        DiceRollResult("1d6", (DiceGroupResult(1, 6, (4,)),), 5),
    )
    for result in invalid_results:
        with pytest.raises(DiceExpressionError):
            validate_dice_roll(result)


def test_roll_service_uses_the_same_application_boundary() -> None:
    service = RollDice(randbelow=lambda bound: bound - 1)

    result = service.execute(RollDiceCommand("-2d4 + 10"))

    assert result.terms == (DiceGroupResult(-1, 4, (4, 4)), DiceModifierResult(10))
    assert result.total == 2
