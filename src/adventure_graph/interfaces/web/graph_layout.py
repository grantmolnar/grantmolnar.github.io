"""Deterministic SVG layout primitives for the browser encounter graph."""

from __future__ import annotations

import math
from dataclasses import dataclass

from adventure_graph.application.structural_authoring import EncounterGraphEdge
from adventure_graph.domain.adventure import Encounter

_MIN_ENCOUNTER_WIDTH = 136.0
_MAX_ENCOUNTER_WIDTH = 224.0
_ENCOUNTER_HORIZONTAL_PADDING = 30.0
_ENCOUNTER_VERTICAL_PADDING = 34.0
_LINE_HEIGHT = 16.0
_LAYOUT_MARGIN = 62.0
_COLLISION_GAP = 30.0


@dataclass(frozen=True, slots=True)
class GraphEncounterLayout:
    """One positioned encounter box with wrapped display text."""

    encounter: Encounter
    lines: tuple[str, ...]
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class GraphEdgeLayout:
    """One routed directed edge between encounter-box boundaries."""

    edge: EncounterGraphEdge
    path: str


@dataclass(frozen=True, slots=True)
class GraphLayout:
    """Complete deterministic layout for one authored encounter graph."""

    width: float
    height: float
    encounters: tuple[GraphEncounterLayout, ...]
    edges: tuple[GraphEdgeLayout, ...]


def wrap_graph_title(title: str, *, maximum_line_width: float = 164.0) -> tuple[str, ...]:
    """Wrap an encounter title without truncating authored words."""
    words = _split_long_words(title.split(), maximum_line_width)
    if not words:
        return ("Untitled encounter",)

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _estimated_text_width(candidate) <= maximum_line_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return tuple(lines)


def build_graph_layout(
    encounters: tuple[Encounter, ...],
    edges: tuple[EncounterGraphEdge, ...],
) -> GraphLayout:
    """Lay out graph encounters and curved edges without external dependencies."""
    if not encounters:
        return GraphLayout(width=900.0, height=560.0, encounters=(), edges=())

    dimensions = {encounter.id: _encounter_dimensions(encounter) for encounter in encounters}
    width, height = _canvas_dimensions(len(encounters), dimensions)
    positions = _initial_positions(encounters, width, height)
    adjacency = _adjacency(encounters, edges)
    _relax_positions(encounters, edges, dimensions, positions, width, height)
    _resolve_overlaps(encounters, dimensions, positions, width, height)

    encounter_layouts = tuple(
        GraphEncounterLayout(
            encounter=encounter,
            lines=dimensions[encounter.id][2],
            x=positions[encounter.id][0],
            y=positions[encounter.id][1],
            width=dimensions[encounter.id][0],
            height=dimensions[encounter.id][1],
        )
        for encounter in encounters
    )
    layout_by_id = {item.encounter.id: item for item in encounter_layouts}
    directed_pairs = {(edge.source_encounter.id, edge.target_encounter.id) for edge in edges}
    reciprocal_pairs = {pair for pair in directed_pairs if (pair[1], pair[0]) in directed_pairs}
    edge_layouts = tuple(
        GraphEdgeLayout(
            edge=edge,
            path=_edge_path(
                layout_by_id[edge.source_encounter.id],
                layout_by_id[edge.target_encounter.id],
                width,
                height,
                reciprocal=(edge.source_encounter.id, edge.target_encounter.id) in reciprocal_pairs,
                source_degree=len(adjacency[edge.source_encounter.id]),
                target_degree=len(adjacency[edge.target_encounter.id]),
            ),
        )
        for edge in edges
    )
    return GraphLayout(width=width, height=height, encounters=encounter_layouts, edges=edge_layouts)


def _encounter_dimensions(encounter: Encounter) -> tuple[float, float, tuple[str, ...]]:
    lines = wrap_graph_title(encounter.title)
    text_width = max(_estimated_text_width(line) for line in lines)
    width = min(
        _MAX_ENCOUNTER_WIDTH,
        max(_MIN_ENCOUNTER_WIDTH, text_width + _ENCOUNTER_HORIZONTAL_PADDING),
    )
    height = max(62.0, len(lines) * _LINE_HEIGHT + _ENCOUNTER_VERTICAL_PADDING)
    return width, height, lines


def _canvas_dimensions(
    encounter_count: int,
    dimensions: dict[str, tuple[float, float, tuple[str, ...]]],
) -> tuple[float, float]:
    widest = max(item[0] for item in dimensions.values())
    tallest = max(item[1] for item in dimensions.values())
    columns = max(3, math.ceil(math.sqrt(encounter_count)))
    rows = math.ceil(encounter_count / columns)
    width = max(920.0, columns * (widest + 42.0) + 2 * _LAYOUT_MARGIN)
    height = max(560.0, rows * (tallest + 82.0) + 2 * _LAYOUT_MARGIN)
    return width, height


def _initial_positions(
    encounters: tuple[Encounter, ...], width: float, height: float
) -> dict[str, list[float]]:
    center_x, center_y = width / 2.0, height / 2.0
    radius_x = width * 0.39
    radius_y = height * 0.37
    starts = [encounter for encounter in encounters if encounter.start]
    ends = [encounter for encounter in encounters if encounter.end]
    anchored_ids = {encounter.id for encounter in (*starts, *ends)}
    ordinary = [encounter for encounter in encounters if encounter.id not in anchored_ids]
    positions: dict[str, list[float]] = {}

    for index, encounter in enumerate(starts):
        offset = (index - (len(starts) - 1) / 2.0) * 105.0
        positions[encounter.id] = [_LAYOUT_MARGIN + 70.0, center_y + offset]
    for index, encounter in enumerate(ends):
        offset = (index - (len(ends) - 1) / 2.0) * 105.0
        positions[encounter.id] = [width - _LAYOUT_MARGIN - 70.0, center_y + offset]

    if ordinary:
        start_angle = -math.pi / 2.0
        for index, encounter in enumerate(ordinary):
            angle = start_angle + (2.0 * math.pi * index / len(ordinary))
            positions[encounter.id] = [
                center_x + radius_x * math.cos(angle),
                center_y + radius_y * math.sin(angle),
            ]
    return positions


def _adjacency(
    encounters: tuple[Encounter, ...],
    edges: tuple[EncounterGraphEdge, ...],
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {encounter.id: set() for encounter in encounters}
    for edge in edges:
        source_id = edge.source_encounter.id
        target_id = edge.target_encounter.id
        if source_id in result and target_id in result and source_id != target_id:
            result[source_id].add(target_id)
            result[target_id].add(source_id)
    return result


def _relax_positions(
    encounters: tuple[Encounter, ...],
    edges: tuple[EncounterGraphEdge, ...],
    dimensions: dict[str, tuple[float, float, tuple[str, ...]]],
    positions: dict[str, list[float]],
    width: float,
    height: float,
) -> None:
    center = (width / 2.0, height / 2.0)
    anchors = {
        encounter.id: (positions[encounter.id][0], positions[encounter.id][1])
        for encounter in encounters
        if encounter.start or encounter.end
    }
    encounter_ids = [encounter.id for encounter in encounters]

    for iteration in range(220):
        forces = {encounter_id: [0.0, 0.0] for encounter_id in encounter_ids}
        temperature = max(0.8, 12.0 * (1.0 - iteration / 220.0))
        _apply_pair_forces(encounter_ids, dimensions, positions, forces)
        _apply_edge_forces(edges, positions, forces)
        _apply_anchor_forces(encounters, positions, forces, center, anchors)
        _move_encounters(encounter_ids, dimensions, positions, forces, width, height, temperature)


def _apply_pair_forces(
    encounter_ids: list[str],
    dimensions: dict[str, tuple[float, float, tuple[str, ...]]],
    positions: dict[str, list[float]],
    forces: dict[str, list[float]],
) -> None:
    for left_index, left_id in enumerate(encounter_ids):
        left_x, left_y = positions[left_id]
        left_width, left_height, _ = dimensions[left_id]
        for right_id in encounter_ids[left_index + 1 :]:
            right_x, right_y = positions[right_id]
            right_width, right_height, _ = dimensions[right_id]
            dx = left_x - right_x
            dy = left_y - right_y
            distance = max(1.0, math.hypot(dx, dy))
            repulsion = 21000.0 / (distance * distance)
            unit_x, unit_y = dx / distance, dy / distance
            forces[left_id][0] += unit_x * repulsion
            forces[left_id][1] += unit_y * repulsion
            forces[right_id][0] -= unit_x * repulsion
            forces[right_id][1] -= unit_y * repulsion
            _apply_collision_force(
                left_id,
                right_id,
                left_width,
                left_height,
                right_width,
                right_height,
                dx,
                dy,
                forces,
            )


def _apply_collision_force(
    left_id: str,
    right_id: str,
    left_width: float,
    left_height: float,
    right_width: float,
    right_height: float,
    dx: float,
    dy: float,
    forces: dict[str, list[float]],
) -> None:
    overlap_x = (left_width + right_width) / 2.0 + _COLLISION_GAP - abs(dx)
    overlap_y = (left_height + right_height) / 2.0 + _COLLISION_GAP - abs(dy)
    if overlap_x <= 0.0 or overlap_y <= 0.0:
        return
    if overlap_x < overlap_y:
        direction = 1.0 if dx >= 0.0 else -1.0
        push = overlap_x * 0.13
        forces[left_id][0] += direction * push
        forces[right_id][0] -= direction * push
    else:
        direction = 1.0 if dy >= 0.0 else -1.0
        push = overlap_y * 0.13
        forces[left_id][1] += direction * push
        forces[right_id][1] -= direction * push


def _apply_edge_forces(
    edges: tuple[EncounterGraphEdge, ...],
    positions: dict[str, list[float]],
    forces: dict[str, list[float]],
) -> None:
    for edge in edges:
        source_id = edge.source_encounter.id
        target_id = edge.target_encounter.id
        if source_id == target_id:
            continue
        source_x, source_y = positions[source_id]
        target_x, target_y = positions[target_id]
        dx = target_x - source_x
        dy = target_y - source_y
        distance = max(1.0, math.hypot(dx, dy))
        attraction = (distance - 238.0) * 0.0065
        unit_x, unit_y = dx / distance, dy / distance
        forces[source_id][0] += unit_x * attraction
        forces[source_id][1] += unit_y * attraction
        forces[target_id][0] -= unit_x * attraction
        forces[target_id][1] -= unit_y * attraction


def _apply_anchor_forces(
    encounters: tuple[Encounter, ...],
    positions: dict[str, list[float]],
    forces: dict[str, list[float]],
    center: tuple[float, float],
    anchors: dict[str, tuple[float, float]],
) -> None:
    center_x, center_y = center
    for encounter in encounters:
        encounter_id = encounter.id
        x, y = positions[encounter_id]
        forces[encounter_id][0] += (center_x - x) * 0.0025
        forces[encounter_id][1] += (center_y - y) * 0.0025
        if encounter_id in anchors:
            anchor_x, anchor_y = anchors[encounter_id]
            forces[encounter_id][0] += (anchor_x - x) * 0.045
            forces[encounter_id][1] += (anchor_y - y) * 0.045


def _move_encounters(
    encounter_ids: list[str],
    dimensions: dict[str, tuple[float, float, tuple[str, ...]]],
    positions: dict[str, list[float]],
    forces: dict[str, list[float]],
    width: float,
    height: float,
    temperature: float,
) -> None:
    for encounter_id in encounter_ids:
        force_x, force_y = forces[encounter_id]
        magnitude = max(1.0, math.hypot(force_x, force_y))
        step = min(temperature, magnitude)
        positions[encounter_id][0] += force_x / magnitude * step
        positions[encounter_id][1] += force_y / magnitude * step
        _clamp_position(encounter_id, dimensions, positions, width, height)


def _resolve_overlaps(
    encounters: tuple[Encounter, ...],
    dimensions: dict[str, tuple[float, float, tuple[str, ...]]],
    positions: dict[str, list[float]],
    width: float,
    height: float,
) -> None:
    encounter_ids = [encounter.id for encounter in encounters]
    for _ in range(100):
        changed = False
        for left_index, left_id in enumerate(encounter_ids):
            left_width, left_height, _ = dimensions[left_id]
            for right_id in encounter_ids[left_index + 1 :]:
                right_width, right_height, _ = dimensions[right_id]
                dx = positions[left_id][0] - positions[right_id][0]
                dy = positions[left_id][1] - positions[right_id][1]
                overlap_x = (left_width + right_width) / 2.0 + 2.0 - abs(dx)
                overlap_y = (left_height + right_height) / 2.0 + 2.0 - abs(dy)
                if overlap_x <= 0.0 or overlap_y <= 0.0:
                    continue
                changed = True
                if overlap_x < overlap_y:
                    direction = 1.0 if dx >= 0.0 else -1.0
                    movement = overlap_x / 2.0 + 0.5
                    positions[left_id][0] += direction * movement
                    positions[right_id][0] -= direction * movement
                else:
                    direction = 1.0 if dy >= 0.0 else -1.0
                    movement = overlap_y / 2.0 + 0.5
                    positions[left_id][1] += direction * movement
                    positions[right_id][1] -= direction * movement
                _clamp_position(left_id, dimensions, positions, width, height)
                _clamp_position(right_id, dimensions, positions, width, height)
        if not changed:
            return


def _clamp_position(
    encounter_id: str,
    dimensions: dict[str, tuple[float, float, tuple[str, ...]]],
    positions: dict[str, list[float]],
    width: float,
    height: float,
) -> None:
    encounter_width, encounter_height, _ = dimensions[encounter_id]
    positions[encounter_id][0] = min(
        width - _LAYOUT_MARGIN - encounter_width / 2.0,
        max(_LAYOUT_MARGIN + encounter_width / 2.0, positions[encounter_id][0]),
    )
    positions[encounter_id][1] = min(
        height - _LAYOUT_MARGIN - encounter_height / 2.0,
        max(_LAYOUT_MARGIN + encounter_height / 2.0, positions[encounter_id][1]),
    )


def _edge_path(
    source: GraphEncounterLayout,
    target: GraphEncounterLayout,
    canvas_width: float,
    canvas_height: float,
    *,
    reciprocal: bool,
    source_degree: int,
    target_degree: int,
) -> str:
    if source.encounter.id == target.encounter.id:
        return _self_loop_path(source)

    dx = target.x - source.x
    dy = target.y - source.y
    distance = max(1.0, math.hypot(dx, dy))
    normal_x, normal_y = -dy / distance, dx / distance
    midpoint_x = (source.x + target.x) / 2.0
    midpoint_y = (source.y + target.y) / 2.0
    outward_x = midpoint_x - canvas_width / 2.0
    outward_y = midpoint_y - canvas_height / 2.0
    if not reciprocal and normal_x * outward_x + normal_y * outward_y < 0.0:
        normal_x *= -1.0
        normal_y *= -1.0

    density_bonus = min(20.0, max(source_degree, target_degree) * 2.0)
    curvature = min(82.0, max(24.0, distance * 0.105 + density_bonus))
    control_x = midpoint_x + normal_x * curvature
    control_y = midpoint_y + normal_y * curvature
    source_x, source_y = _rectangle_boundary(source, control_x, control_y)
    target_x, target_y = _rectangle_boundary(target, control_x, control_y)
    return (
        f"M {source_x:.1f} {source_y:.1f} "
        f"Q {control_x:.1f} {control_y:.1f} {target_x:.1f} {target_y:.1f}"
    )


def _self_loop_path(encounter: GraphEncounterLayout) -> str:
    right = encounter.x + encounter.width / 2.0
    top = encounter.y - encounter.height / 2.0
    return (
        f"M {right - 8.0:.1f} {top + 12.0:.1f} "
        f"C {right + 70.0:.1f} {top - 60.0:.1f}, "
        f"{right + 70.0:.1f} {top + encounter.height + 60.0:.1f}, "
        f"{right - 8.0:.1f} {top + encounter.height - 12.0:.1f}"
    )


def _rectangle_boundary(
    encounter: GraphEncounterLayout, target_x: float, target_y: float
) -> tuple[float, float]:
    dx = target_x - encounter.x
    dy = target_y - encounter.y
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return encounter.x, encounter.y
    scale = 1.0 / max(
        abs(dx) / (encounter.width / 2.0),
        abs(dy) / (encounter.height / 2.0),
    )
    return encounter.x + dx * scale, encounter.y + dy * scale


def _split_long_words(words: list[str], maximum_line_width: float) -> list[str]:
    result: list[str] = []
    for word in words:
        if _estimated_text_width(word) <= maximum_line_width:
            result.append(word)
            continue
        current = ""
        for character in word:
            candidate = current + character
            if current and _estimated_text_width(candidate) > maximum_line_width:
                result.append(current)
                current = character
            else:
                current = candidate
        if current:
            result.append(current)
    return result


def _estimated_text_width(text: str) -> float:
    width = 0.0
    for character in text:
        if character.isspace():
            width += 3.5
        elif character in "ilI.,'`|!:;":
            width += 3.6
        elif character in "MW@#%&":
            width += 9.4
        elif character.isupper():
            width += 7.5
        else:
            width += 6.4
    return width
