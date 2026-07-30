"""Tests for the authored-corpus contract vocabulary."""

from __future__ import annotations

from pathlib import Path

import pytest

from adventure_graph.domain.adventure import Clue
from tests.support.corpus_contracts import (
    assert_deprecated_editorial_phrases_absent,
    assert_editorial_phrase_locks,
    assert_markdown_sections,
    assert_rendered_documents_match,
    assert_semantic_concepts,
    group_clues_by_encounter,
    group_clues_by_revelation,
)


def test_markdown_section_contract_checks_presence_and_authored_order() -> None:
    text = "# Record\n\n## Identity\n\nBody.\n\n## Authority\n\nMore."

    assert_markdown_sections(text, ("## Identity", "## Authority"))

    with pytest.raises(AssertionError, match="authored order"):
        assert_markdown_sections(text, ("## Authority", "## Identity"))


def test_editorial_phrase_contract_preserves_exact_language() -> None:
    assert_editorial_phrase_locks("The bell is old. The knot is new.", ("The bell is old.",))

    with pytest.raises(AssertionError, match="editorial phrase locks"):
        assert_editorial_phrase_locks("The old bell sounds.", ("The bell is old.",))


def test_semantic_contract_allows_case_punctuation_and_alternative_wording() -> None:
    text = "The doors remain PUBLIC. Preference hides in the court's language."

    assert_semantic_concepts(
        text,
        {
            "public preference encoded in wording": (
                ("public",),
                ("preference", "partiality"),
                ("nouns", "wording", "language"),
            )
        },
    )


def test_semantic_contract_reports_only_unmet_concept_groups() -> None:
    with pytest.raises(AssertionError, match="custody"):
        assert_semantic_concepts(
            "The route is public.",
            {"custody remains bounded": (("custody",), ("bounded", "limited"))},
        )


def test_deprecated_editorial_phrase_contract_rejects_exact_return() -> None:
    assert_deprecated_editorial_phrases_absent(
        "The scene presents several possible resolutions.",
        ("There is only one correct resolution.",),
    )

    with pytest.raises(AssertionError, match="Deprecated editorial phrases"):
        assert_deprecated_editorial_phrases_absent(
            "There is only one correct resolution.",
            ("There is only one correct resolution.",),
        )


def test_clue_grouping_helpers_preserve_order_and_missing_key_behavior() -> None:
    clues = (
        Clue("lead-a", "A", "encounter-1", "revelation-1"),
        Clue("lead-b", "B", "encounter-2", "revelation-1"),
        Clue("lead-c", "C", "encounter-1", "revelation-2"),
    )

    by_revelation = group_clues_by_revelation(clues)
    by_encounter = group_clues_by_encounter(clues)

    assert [clue.id for clue in by_revelation["revelation-1"]] == ["lead-a", "lead-b"]
    assert [clue.id for clue in by_encounter["encounter-1"]] == ["lead-a", "lead-c"]
    assert by_revelation["missing"] == []


def test_rendered_document_contract_reports_missing_and_changed_files(tmp_path: Path) -> None:
    (tmp_path / "matching.md").write_text("same", encoding="utf-8")
    (tmp_path / "changed.md").write_text("old", encoding="utf-8")

    with pytest.raises(AssertionError, match="changed.md: content differs") as exc_info:
        assert_rendered_documents_match(
            {
                "matching.md": "same",
                "changed.md": "new",
                "missing.md": "absent",
            },
            tmp_path,
        )

    assert "missing.md: missing" in str(exc_info.value)
