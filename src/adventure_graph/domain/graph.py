"""Small exact graph algorithms used by adventure validation."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    Edge = tuple[str, str]


@dataclass(frozen=True, slots=True)
class EdgeCutWitness:
    """One exact global minimum cut in a simple undirected graph projection."""

    connectivity: int
    side_a: tuple[str, ...]
    side_b: tuple[str, ...]
    cut_edges: tuple[tuple[str, str], ...]


def directed_reachable(start_encounters: Iterable[str], edges: Iterable[Edge]) -> set[str]:
    """Return all vertices reachable along directed edges from the supplied starts."""
    adjacency: dict[str, set[str]] = {}
    for source, target in edges:
        adjacency.setdefault(source, set()).add(target)

    reached = set(start_encounters)
    queue = deque(reached)
    while queue:
        source = queue.popleft()
        for target in adjacency.get(source, set()):
            if target not in reached:
                reached.add(target)
                queue.append(target)
    return reached


def undirected_components(
    vertices: Iterable[str], edges: Iterable[Edge]
) -> tuple[frozenset[str], ...]:
    """Return weak components of a simple undirected projection."""
    adjacency = _undirected_adjacency(vertices, edges)
    unseen = set(adjacency)
    components: list[frozenset[str]] = []
    while unseen:
        root = min(unseen)
        component = {root}
        queue = deque([root])
        unseen.remove(root)
        while queue:
            vertex = queue.popleft()
            for neighbor in adjacency[vertex]:
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(frozenset(component))
    return tuple(sorted(components, key=lambda item: (len(item), tuple(sorted(item)))))


def global_minimum_edge_cut(
    vertices: Iterable[str], edges: Iterable[Edge]
) -> EdgeCutWitness | None:
    """Return an exact minimum-cut witness for the simple undirected projection.

    Adventure graphs are ordinarily small, so this intentionally uses exact unit-capacity max flow
    for every vertex pair instead of adding a graph dependency or hiding approximation behavior.
    """
    vertex_set = set(vertices)
    if len(vertex_set) < 2:
        return None

    simple_edges = _simple_edges(vertex_set, edges)
    components = undirected_components(vertex_set, simple_edges)
    if len(components) > 1:
        side_a = set(components[0])
        return _cut_witness(0, side_a, vertex_set - side_a, simple_edges)

    adjacency = _undirected_adjacency(vertex_set, simple_edges)
    best: EdgeCutWitness | None = None
    ordered = sorted(vertex_set)
    for index, source in enumerate(ordered):
        for target in ordered[index + 1 :]:
            flow, reachable = _unit_capacity_max_flow(adjacency, source, target)
            candidate = _cut_witness(flow, reachable, vertex_set - reachable, simple_edges)
            if best is None or _witness_key(candidate) < _witness_key(best):
                best = candidate
    return best


def terminal_minimum_edge_cut(
    vertices: Iterable[str],
    edges: Iterable[Edge],
    terminals: Iterable[str],
) -> EdgeCutWitness | None:
    """Return the weakest exact edge cut separating any two necessary vertices.

    Optional vertices remain available as intermediate routes, but a fragile optional spur does not
    lower the resilience of the adventure's necessary structure.
    """
    vertex_set = set(vertices)
    terminal_set = set(terminals) & vertex_set
    if len(terminal_set) < 2:
        return None

    simple_edges = _simple_edges(vertex_set, edges)
    adjacency = _undirected_adjacency(vertex_set, simple_edges)
    best: EdgeCutWitness | None = None
    ordered = sorted(terminal_set)
    for index, source in enumerate(ordered):
        for target in ordered[index + 1 :]:
            flow, reachable = _unit_capacity_max_flow(adjacency, source, target)
            candidate = _cut_witness(flow, reachable, vertex_set - reachable, simple_edges)
            if best is None or _witness_key(candidate) < _witness_key(best):
                best = candidate
    return best


def global_edge_connectivity(vertices: Iterable[str], edges: Iterable[Edge]) -> int | None:
    """Return exact edge connectivity of the simple undirected projection."""
    witness = global_minimum_edge_cut(vertices, edges)
    return None if witness is None else witness.connectivity


def _simple_edges(vertices: set[str], edges: Iterable[Edge]) -> set[tuple[str, str]]:
    return {
        (min(source, target), max(source, target))
        for source, target in edges
        if source != target and source in vertices and target in vertices
    }


def _cut_witness(
    connectivity: int,
    side_a: Iterable[str],
    side_b: Iterable[str],
    edges: Iterable[Edge],
) -> EdgeCutWitness:
    first = tuple(sorted(side_a))
    second = tuple(sorted(side_b))
    if (len(second), second) < (len(first), first):
        first, second = second, first
    first_set = set(first)
    cut_edges = tuple(
        sorted(
            (min(source, target), max(source, target))
            for source, target in edges
            if (source in first_set) != (target in first_set)
        )
    )
    return EdgeCutWitness(connectivity, first, second, cut_edges)


def _witness_key(witness: EdgeCutWitness) -> tuple[object, ...]:
    return (
        witness.connectivity,
        min(len(witness.side_a), len(witness.side_b)),
        witness.side_a,
        witness.side_b,
        witness.cut_edges,
    )


def _undirected_adjacency(vertices: Iterable[str], edges: Iterable[Edge]) -> dict[str, set[str]]:
    adjacency: dict[str, set[str]] = {vertex: set() for vertex in vertices}
    for source, target in edges:
        if source == target or source not in adjacency or target not in adjacency:
            continue
        adjacency[source].add(target)
        adjacency[target].add(source)
    return adjacency


def _unit_capacity_max_flow(
    adjacency: Mapping[str, set[str]], source: str, target: str
) -> tuple[int, set[str]]:
    residual: dict[str, dict[str, int]] = {vertex: {} for vertex in adjacency}
    for vertex, neighbors in adjacency.items():
        for neighbor in neighbors:
            residual[vertex][neighbor] = 1

    flow = 0
    while True:
        parents, reached = _augmenting_path(residual, source, target)
        if target not in parents:
            return flow, reached
        cursor = target
        while cursor != source:
            parent = parents[cursor]
            residual[parent][cursor] -= 1
            residual[cursor][parent] = residual[cursor].get(parent, 0) + 1
            cursor = parent
        flow += 1


def _augmenting_path(
    residual: Mapping[str, Mapping[str, int]], source: str, target: str
) -> tuple[dict[str, str], set[str]]:
    parents: dict[str, str] = {}
    queue = deque([source])
    seen = {source}
    while queue:
        vertex = queue.popleft()
        for neighbor, capacity in residual[vertex].items():
            if capacity <= 0 or neighbor in seen:
                continue
            seen.add(neighbor)
            parents[neighbor] = vertex
            if neighbor == target:
                return parents, seen
            queue.append(neighbor)
    return parents, seen
