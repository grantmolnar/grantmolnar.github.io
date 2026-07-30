"""Tests for opaque adventure identity and title-derived entity identifiers."""

from uuid import UUID

from adventure_graph.domain.identifiers import (
    identifier_slug,
    is_canonical_uuid4,
    new_adventure_identifier,
    new_reference_identifier,
    unique_identifier,
)


def test_identifier_slug_normalizes_case_spacing_punctuation_and_diacritics() -> None:
    assert identifier_slug("  Élodie's North Gate!  ") == "elodie-s-north-gate"


def test_identifier_slug_uses_item_when_title_has_no_ascii_word_characters() -> None:
    assert identifier_slug("---") == "item"


def test_unique_identifier_adds_the_first_available_numeric_suffix() -> None:
    assert unique_identifier("North Gate", {"north-gate", "north-gate-2", "north-gate-3"}) == (
        "north-gate-4"
    )


def test_unique_identifier_does_not_collide_with_the_entity_being_updated() -> None:
    assert (
        unique_identifier(
            "North Gate",
            {"north-gate", "south-gate"},
            current_identifier="north-gate",
        )
        == "north-gate"
    )


def test_new_adventure_identifier_returns_a_version_four_uuid() -> None:
    identifier = new_adventure_identifier()

    parsed = UUID(identifier)

    assert parsed.version == 4
    assert str(parsed) == identifier


def test_new_reference_identifier_returns_canonical_version_four_uuid() -> None:
    identifier = new_reference_identifier()

    assert is_canonical_uuid4(identifier)
    assert not is_canonical_uuid4(identifier.upper())
    assert not is_canonical_uuid4("not-a-uuid")
