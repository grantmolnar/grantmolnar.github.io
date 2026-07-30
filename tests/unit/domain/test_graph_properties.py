"""Property tests for exact graph diagnostics."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import combinations

import pytest

pytest.importorskip("hypothesis")

from hypothesis import given, settings
from hypothesis import strategies as st

from adventure_graph.domain.graph import global_minimum_edge_cut


@pytest.mark.property
@settings(max_examples=80, deadline=None)
@given(
    vertex_count=st.integers(min_value=2, max_value=6),
    selected_edges=st.sets(
        st.tuples(st.integers(min_value=0, max_value=5), st.integers(min_value=0, max_value=5)),
        max_size=15,
    ),
)
def test_exact_witness_matches_brute_force_edge_removal(
    vertex_count: int, selected_edges: set[tuple[int, int]]
) -> None:
    vertices = {str(index) for index in range(vertex_count)}
    edges = {
        (str(min(source, target)), str(max(source, target)))
        for source, target in selected_edges
        if source < vertex_count and target < vertex_count and source != target
    }

    witness = global_minimum_edge_cut(vertices, edges)

    assert witness is not None
    assert witness.connectivity == _brute_force_connectivity(vertices, edges)
    assert len(witness.cut_edges) == witness.connectivity
    assert set(witness.side_a).isdisjoint(witness.side_b)
    assert set(witness.side_a) | set(witness.side_b) == vertices
    side_a = set(witness.side_a)
    assert all((source in side_a) != (target in side_a) for source, target in witness.cut_edges)


def _brute_force_connectivity(vertices: set[str], edges: set[tuple[str, str]]) -> int:
    if not _is_connected(vertices, edges):
        return 0
    ordered_edges = sorted(edges)
    for removal_count in range(1, len(ordered_edges) + 1):
        for removed in combinations(ordered_edges, removal_count):
            if not _is_connected(vertices, edges - set(removed)):
                return removal_count
    raise AssertionError("A connected graph with at least two vertices must have a finite cut.")


def _is_connected(vertices: set[str], edges: Iterable[tuple[str, str]]) -> bool:
    adjacency: dict[str, set[str]] = {vertex: set() for vertex in vertices}
    for source, target in edges:
        adjacency[source].add(target)
        adjacency[target].add(source)
    reached = {min(vertices)}
    frontier = list(reached)
    while frontier:
        vertex = frontier.pop()
        for neighbor in adjacency[vertex] - reached:
            reached.add(neighbor)
            frontier.append(neighbor)
    return reached == vertices
