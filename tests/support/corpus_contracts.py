"""Explicit contract helpers for authored corpus regression tests."""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from adventure_graph.domain.adventure import Clue

SemanticRequirements = Mapping[str, Sequence[Sequence[str]]]


def group_clues_by_revelation(
    clues: Iterable[Clue],
) -> defaultdict[str, list[Clue]]:
    """Group stable ``Clue`` models by their revelation identifier."""
    grouped: defaultdict[str, list[Clue]] = defaultdict(list)
    for clue in clues:
        grouped[clue.revelation_id].append(clue)
    return grouped


def group_clues_by_encounter(
    clues: Iterable[Clue],
) -> defaultdict[str, list[Clue]]:
    """Group stable ``Clue`` models by their source encounter identifier."""
    grouped: defaultdict[str, list[Clue]] = defaultdict(list)
    for clue in clues:
        grouped[clue.source_encounter_id].append(clue)
    return grouped


def assert_rendered_documents_match(
    documents: Mapping[str, str],
    generated_directory: Path,
) -> None:
    """Assert that rendered documents reproduce their checked-in packet files."""
    mismatches: list[str] = []
    for relative_path, expected_content in documents.items():
        checked_in_path = generated_directory / relative_path
        if not checked_in_path.is_file():
            mismatches.append(f"{relative_path}: missing")
            continue
        actual_content = checked_in_path.read_text(encoding="utf-8")
        if actual_content != expected_content:
            mismatches.append(f"{relative_path}: content differs")
    assert not mismatches, f"Generated packet drift: {mismatches!r}"


def assert_markdown_sections(text: str, headings: Sequence[str], *, ordered: bool = True) -> None:
    """Assert that structural Markdown headings exist, optionally in authored order."""
    missing = [heading for heading in headings if heading not in text]
    assert not missing, f"Missing Markdown sections: {missing!r}"
    if ordered:
        positions = [text.index(heading) for heading in headings]
        assert positions == sorted(positions), (
            f"Markdown sections are not in the required authored order: {list(headings)!r}"
        )


def assert_editorial_phrase_locks(text: str, phrases: Iterable[str]) -> None:
    """Assert consciously frozen wording whose exact language is part of the product."""
    missing = [phrase for phrase in phrases if phrase not in text]
    assert not missing, f"Missing deliberate editorial phrase locks: {missing!r}"


def assert_deprecated_editorial_phrases_absent(text: str, phrases: Iterable[str]) -> None:
    """Assert consciously retired wording does not return verbatim."""
    present = [phrase for phrase in phrases if phrase in text]
    assert not present, f"Deprecated editorial phrases remain present: {present!r}"


def assert_semantic_concepts(text: str, concepts: SemanticRequirements) -> None:
    """Assert concepts without freezing punctuation, capitalization, or one sentence form.

    Each concept maps to required groups. Every group must match at least one alternative,
    while the groups themselves are conjunctive. For example, ``(("public",),
    ("wording", "language"))`` requires publicness and either wording or language.
    """
    normalized = _normalize(text)
    missing: dict[str, list[tuple[str, ...]]] = {}
    for label, required_groups in concepts.items():
        absent_groups = [
            tuple(alternatives)
            for alternatives in required_groups
            if not any(_normalize(alternative) in normalized for alternative in alternatives)
        ]
        if absent_groups:
            missing[label] = absent_groups
    assert not missing, f"Missing semantic corpus concepts: {missing!r}"


def _normalize(text: str) -> str:
    translated = text.casefold().translate(
        str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'})
    )
    return re.sub(r"\s+", " ", translated).strip()
