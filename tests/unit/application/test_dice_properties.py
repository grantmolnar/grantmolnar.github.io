"""Property evidence for bounded dice notation and auditable rolls."""

from __future__ import annotations

import pytest

pytest.importorskip("hypothesis")

from hypothesis import given, settings
from tests.support.property_strategies import (
    DiceExpressionCase,
    dice_expression_cases,
)

from adventure_graph.application.dice import (
    parse_dice_expression,
    roll_dice,
    validate_dice_roll,
)

pytestmark = pytest.mark.property


@settings(max_examples=100, deadline=None, derandomize=True)
@given(case=dice_expression_cases())
def test_dice_parser_canonicalization_is_idempotent(case: DiceExpressionCase) -> None:
    """Whitespace, case, and omitted one-die counts normalize to one stable expression."""
    parsed = parse_dice_expression(case.source)

    assert parsed.expression == case.canonical
    assert parsed.dice_count == case.dice_count
    assert parse_dice_expression(parsed.expression) == parsed


@settings(max_examples=80, deadline=None, derandomize=True)
@given(case=dice_expression_cases())
def test_bounded_dice_rolls_validate_and_recompute_their_total(case: DiceExpressionCase) -> None:
    """Every generated bounded expression yields auditable in-range terms and arithmetic."""
    result = roll_dice(case.source, randbelow=lambda upper_bound: upper_bound - 1)

    validate_dice_roll(result)
    assert result.expression == case.canonical
    assert result.total == case.maximum_total
