"""Regression tests for encoded and non-canonical local UI route segments."""

from __future__ import annotations

import pytest

from adventure_graph.interfaces.web.routing import (
    archive_action_route,
    archive_detail_route,
    entity_edit_route,
    entity_route,
    normalize_play_return_target,
    play_authoring_return_location,
)


@pytest.mark.parametrize(
    "path",
    [
        "/encounters/alpha%2Fbeta",
        "/encounters/alpha%5Cbeta",
        "/encounters/%2E%2E",
        "/encounters/alpha%00beta",
        "/encounters/alpha%ZZbeta",
    ],
)
def test_entity_routes_reject_encoded_separators_dot_segments_and_controls(path: str) -> None:
    assert entity_route(path) is None


@pytest.mark.parametrize(
    "path",
    [
        "/encounters/alpha%2Fbeta/edit",
        "/encounters/alpha%5Cbeta/edit",
        "/encounters/%2E%2E/edit",
        "/encounters/alpha%00beta/edit",
        "/encounters/alpha%ZZbeta/edit",
    ],
)
def test_entity_edit_routes_reject_ambiguous_identifiers(path: str) -> None:
    assert entity_edit_route(path) is None


def test_archive_routes_reject_ambiguous_identifiers() -> None:
    assert archive_detail_route("/archives/alpha%2Fbeta") is None
    assert archive_action_route("/archives/%2E%2E/delete") is None


def test_play_authoring_return_targets_are_canonical_and_local() -> None:
    assert normalize_play_return_target("/play") == "/play"
    assert normalize_play_return_target("/play?encounter=alpha") == "/play?encounter=alpha"
    assert (
        play_authoring_return_location(
            "/play?encounter=alpha",
            action="encounter-authored",
            focus_encounter_id="off-script-cellar",
        )
        == "/play?encounter=off-script-cellar&action=encounter-authored"
    )
    assert (
        play_authoring_return_location(
            "/play?encounter=alpha",
            action="clue-authored",
        )
        == "/play?encounter=alpha&action=clue-authored"
    )
    assert (
        play_authoring_return_location(
            "/play?encounter=alpha",
            action="reference-authored",
        )
        == "/play?encounter=alpha&action=reference-authored"
    )


@pytest.mark.parametrize(
    "target",
    [
        "https://example.com/play",
        "//example.com/play",
        "/play/../settings",
        "/settings",
        "/play?encounter=Alpha",
        "/play?encounter=alpha&action=visit",
        "/play?encounter=alpha%2Fbeta",
        "/play#fragment",
    ],
)
def test_play_authoring_return_targets_reject_external_or_ambiguous_values(target: str) -> None:
    assert normalize_play_return_target(target) is None
