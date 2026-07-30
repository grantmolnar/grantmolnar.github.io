"""Tests for deterministic browser graph layout primitives."""

from __future__ import annotations

import re

from adventure_graph.application.structural_authoring import EncounterGraphEdge
from adventure_graph.domain.adventure import Encounter
from adventure_graph.interfaces.web.graph_layout import build_graph_layout, wrap_graph_title


def _encounter(
    identifier: str,
    title: str,
    *,
    start: bool = False,
    end: bool = False,
) -> Encounter:
    return Encounter(id=identifier, title=title, summary="", start=start, end=end)


def _edge(source: Encounter, target: Encounter) -> EncounterGraphEdge:
    return EncounterGraphEdge(
        source_encounter=source, target_encounter=target, revelations=(), clues=()
    )


def test_long_graph_titles_wrap_without_truncation() -> None:
    title = "The Chamber of the Fourfold Petition"

    lines = wrap_graph_title(title)

    assert len(lines) > 1
    assert " ".join(lines) == title
    assert all("…" not in line for line in lines)


def test_layout_uses_variable_boxes_and_keeps_them_inside_the_canvas() -> None:
    short = _encounter("short", "Inn", start=True)
    long = _encounter("long", "The Chamber of the Fourfold Petition", end=True)

    layout = build_graph_layout((short, long), (_edge(short, long),))
    by_id = {item.encounter.id: item for item in layout.encounters}

    assert by_id["long"].width > by_id["short"].width
    assert by_id["long"].height > by_id["short"].height
    for item in layout.encounters:
        assert item.x - item.width / 2 >= 0
        assert item.x + item.width / 2 <= layout.width
        assert item.y - item.height / 2 >= 0
        assert item.y + item.height / 2 <= layout.height


def test_start_and_end_encounters_anchor_the_reading_direction() -> None:
    start = _encounter("start", "Village Gate", start=True)
    middle = _encounter("middle", "Market Square")
    end = _encounter("end", "Final Hearing", end=True)

    layout = build_graph_layout(
        (start, middle, end),
        (_edge(start, middle), _edge(middle, end)),
    )
    by_id = {item.encounter.id: item for item in layout.encounters}

    assert by_id["start"].x < by_id["middle"].x < by_id["end"].x


def test_edges_curve_between_box_boundaries_instead_of_encounter_centers() -> None:
    source = _encounter("source", "Source", start=True)
    target = _encounter("target", "A Longer Destination", end=True)

    layout = build_graph_layout((source, target), (_edge(source, target),))
    routed = layout.edges[0]
    values = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", routed.path)]
    source_layout, target_layout = layout.encounters

    assert routed.path.startswith("M ")
    assert " Q " in routed.path
    assert values[0:2] != [source_layout.x, source_layout.y]
    assert values[-2:] != [target_layout.x, target_layout.y]


def test_layout_avoids_overlapping_encounter_boxes_for_a_dense_example() -> None:
    encounters = tuple(
        _encounter(
            f"encounter-{index}",
            f"The Deliberately Long Encounter Title Number {index}",
            start=index == 0,
            end=index == 11,
        )
        for index in range(12)
    )
    edges = tuple(
        _edge(source, target)
        for source_index, source in enumerate(encounters)
        for target_index, target in enumerate(encounters)
        if source_index != target_index and (source_index + target_index) % 3 == 0
    )

    layout = build_graph_layout(encounters, edges)

    for index, left in enumerate(layout.encounters):
        for right in layout.encounters[index + 1 :]:
            overlap_x = (left.width + right.width) / 2 - abs(left.x - right.x)
            overlap_y = (left.height + right.height) / 2 - abs(left.y - right.y)
            assert overlap_x <= 0 or overlap_y <= 0
