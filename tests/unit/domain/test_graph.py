"""Tests for exact graph diagnostics."""

from __future__ import annotations

from adventure_graph.domain.graph import (
    directed_reachable,
    global_edge_connectivity,
    global_minimum_edge_cut,
    terminal_minimum_edge_cut,
)


def test_directed_reachability_follows_transitive_paths_without_reversing_edges() -> None:
    reached = directed_reachable(
        ("start",),
        (("start", "middle"), ("middle", "end"), ("isolated", "start")),
    )

    assert reached == {"start", "middle", "end"}


def test_complete_graph_on_four_vertices_has_edge_connectivity_three() -> None:
    vertices = {"a", "b", "c", "d"}
    edges = {(source, target) for source in vertices for target in vertices if source < target}

    witness = global_minimum_edge_cut(vertices, edges)

    assert global_edge_connectivity(vertices, edges) == 3
    assert witness is not None
    assert witness.connectivity == 3
    assert len(witness.cut_edges) == 3
    assert set(witness.side_a).isdisjoint(witness.side_b)
    assert set(witness.side_a) | set(witness.side_b) == vertices


def test_parallel_directed_links_count_as_one_structural_connection() -> None:
    vertices = {"a", "b", "c"}
    edges = [("a", "b"), ("b", "a"), ("a", "b"), ("b", "c"), ("c", "b")]

    witness = global_minimum_edge_cut(vertices, edges)

    assert global_edge_connectivity(vertices, edges) == 1
    assert witness is not None
    assert witness.cut_edges in ((("a", "b"),), (("b", "c"),))


def test_disconnected_graph_returns_a_zero_edge_partition() -> None:
    witness = global_minimum_edge_cut({"a", "b", "c"}, [("a", "b")])

    assert witness is not None
    assert witness.connectivity == 0
    assert witness.side_a == ("c",)
    assert witness.side_b == ("a", "b")
    assert witness.cut_edges == ()


def test_single_vertex_has_no_edge_cut() -> None:
    assert global_minimum_edge_cut({"a"}, []) is None
    assert global_edge_connectivity({"a"}, []) is None


def test_terminal_cut_ignores_fragile_optional_spurs() -> None:
    vertices = {"start", "left", "right", "end", "optional"}
    edges = {
        ("start", "left"),
        ("left", "end"),
        ("start", "right"),
        ("right", "end"),
        ("left", "right"),
        ("left", "optional"),
    }

    global_witness = global_minimum_edge_cut(vertices, edges)
    terminal_witness = terminal_minimum_edge_cut(vertices, edges, {"start", "end"})

    assert global_witness is not None
    assert global_witness.connectivity == 1
    assert terminal_witness is not None
    assert terminal_witness.connectivity == 2


def test_terminal_cut_uses_optional_encounters_as_independent_routes() -> None:
    vertices = {"start", "route-a", "route-b", "route-c", "end"}
    edges = {
        ("start", "route-a"),
        ("route-a", "end"),
        ("start", "route-b"),
        ("route-b", "end"),
        ("start", "route-c"),
        ("route-c", "end"),
    }

    witness = terminal_minimum_edge_cut(vertices, edges, {"start", "end"})

    assert witness is not None
    assert witness.connectivity == 3


def test_terminal_cut_ignores_terminals_that_are_not_graph_vertices() -> None:
    witness = terminal_minimum_edge_cut(
        {"start", "middle", "end"},
        {("start", "middle"), ("middle", "end")},
        {"start", "end", "retired-encounter"},
    )

    assert witness is not None
    assert witness.connectivity == 1
    assert set(witness.side_a) | set(witness.side_b) == {"start", "middle", "end"}
