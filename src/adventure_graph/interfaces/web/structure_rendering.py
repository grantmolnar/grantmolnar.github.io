"""HTML rendering for authored graph structure and diagnostics."""

from __future__ import annotations

from urllib.parse import urlencode

from adventure_graph.application.structural_authoring import StructuralOverviewResult
from adventure_graph.interfaces.web.graph_layout import build_graph_layout
from adventure_graph.interfaces.web.page_rendering import (
    entity_url,
    escape_html,
    render_empty_card,
    render_issue,
    render_metrics,
    render_page,
)


def render_structure(result: StructuralOverviewResult, project_label: str) -> str:
    """Render synchronized graph, revelation coverage, and diagnostics."""
    adventure = result.adventure
    necessary_rows = tuple(row for row in result.coverage if row.revelation.required)
    sufficient = sum(row.is_sufficient for row in necessary_rows)
    connectivity = result.validation_report.edge_connectivity
    body = f"""
      <div class="page-heading-row">
        <div><p class="eyebrow">Structure workspace</p><h1>Adventure structure</h1></div>
        <div class="button-row">
          <a class="button secondary" href="/encounters/new">Add encounter</a>
          <a class="button secondary" href="/revelations/new">Add revelation</a>
          <a class="button primary" href="/clues/new">Add lead</a>
        </div>
      </div>
      <p class="lede">Review routes and lead coverage together. Open a finding to edit the related material.</p>
      {render_metrics(((str(len(result.graph_edges)), "Unique encounter edges"), (str(sufficient), "Necessary revelations covered"), (str(len(necessary_rows) - sufficient), "Necessary coverage deficits"), ("n/a" if connectivity is None else str(connectivity), "Structural resilience")))}
      <section class="section">
        <div class="section-heading"><h2>Encounter graph</h2><span>Click an encounter to inspect it</span></div>
        {_encounter_graph(result)}
        {_minimum_cut_panel(result)}
      </section>
      <section class="section">
        <div class="section-heading"><h2>Revelation coverage</h2><span>Lead count and source diversity</span></div>
        {_coverage_matrix(result)}
      </section>
      <section class="section">
        <div class="section-heading"><h2>Validation findings</h2><span>{len(result.validation_report.issues)} findings</span></div>
        <div class="diagnostic-list">{"".join(render_issue(issue, adventure) for issue in result.validation_report.issues) or render_empty_card("No structural findings.")}</div>
      </section>
    """
    return render_page(
        title=f"Structure — {adventure.title}",
        project_label=project_label,
        adventure=adventure,
        report=result.validation_report,
        current_kind="structure",
        current_id=None,
        body=body,
        related_issues=result.validation_report.issues,
        revision=result.revision.value,
    )


def _encounter_graph(result: StructuralOverviewResult) -> str:
    encounters = result.adventure.encounters
    if not encounters:
        return render_empty_card("No encounters are available to graph.")

    layout = build_graph_layout(encounters, result.graph_edges)
    diagnosis = result.validation_report.connectivity_diagnosis
    cut_edges: set[tuple[str, str]] = (
        {
            (source, target) if source <= target else (target, source)
            for source, target in diagnosis.cut_edges
        }
        if diagnosis is not None
        else set()
    )
    side_a: set[str] = set(diagnosis.side_a) if diagnosis is not None else set()
    side_b: set[str] = set(diagnosis.side_b) if diagnosis is not None else set()

    edges: list[str] = []
    for routed in layout.edges:
        edge = routed.edge
        edge_key = (
            (edge.source_encounter.id, edge.target_encounter.id)
            if edge.source_encounter.id <= edge.target_encounter.id
            else (edge.target_encounter.id, edge.source_encounter.id)
        )
        is_cut = edge_key in cut_edges
        title = ", ".join(clue.title for clue in edge.clues)
        edges.append(
            f'<path class="graph-edge{" cut-edge" if is_cut else ""}" d="{routed.path}" '
            f'data-source-encounter="{escape_html(edge.source_encounter.id)}" '
            f'data-target-encounter="{escape_html(edge.target_encounter.id)}" '
            f'marker-end="url(#graph-arrow)"><title>'
            f"{escape_html(edge.source_encounter.title)} → {escape_html(edge.target_encounter.title)}: "
            f"{escape_html(title)}</title></path>"
        )

    encounter_shapes: list[str] = []
    for item in layout.encounters:
        encounter = item.encounter
        partition = (
            " side-a" if encounter.id in side_a else " side-b" if encounter.id in side_b else ""
        )
        role = " start" if encounter.start else " end" if encounter.end else ""
        necessity = " necessary" if encounter.required else " optional"
        first_y = -((len(item.lines) - 1) * 8.0) + 4.0
        lines = "".join(
            f'<tspan x="0" y="{first_y + index * 16.0:.1f}">{escape_html(line)}</tspan>'
            for index, line in enumerate(item.lines)
        )
        roles = (
            ", ".join(
                value
                for active, value in (
                    (encounter.start, "start"),
                    (encounter.end, "end"),
                    (not encounter.required, "optional"),
                )
                if active
            )
            or "necessary"
        )
        encounter_shapes.append(
            f'<a class="graph-encounter-link" href="{entity_url("encounter", encounter.id)}" '
            f'aria-label="Open {escape_html(encounter.title)} ({roles})" '
            f'data-graph-encounter-link="{escape_html(encounter.id)}">'
            f'<g class="graph-encounter{partition}{role}{necessity}" '
            f'data-graph-encounter-id="{escape_html(encounter.id)}" '
            f'transform="translate({item.x:.1f} {item.y:.1f})">'
            f'<rect x="{-item.width / 2.0:.1f}" y="{-item.height / 2.0:.1f}" '
            f'width="{item.width:.1f}" height="{item.height:.1f}" rx="14" ry="14"></rect>'
            f'<text text-anchor="middle" aria-hidden="true">{lines}</text>'
            f"<title>{escape_html(encounter.title)} — {roles}</title></g></a>"
        )

    legend_items = [
        '<span><i class="legend-start"></i> Start encounter</span>',
        '<span><i class="legend-end"></i> End encounter</span>',
        '<span><i class="legend-optional"></i> Optional encounter</span>',
    ]
    if diagnosis is not None:
        legend_items.extend(
            (
                '<span><i class="legend-a"></i> Cut side A</span>',
                '<span><i class="legend-b"></i> Cut side B</span>',
                '<span><i class="legend-cut"></i> Witnessed cut edge</span>',
            )
        )
    legend = f'<div class="graph-legend">{"".join(legend_items)}</div>'
    view_box = f"0 0 {layout.width:.1f} {layout.height:.1f}"
    return f"""
      <div class="graph-shell" data-graph-shell>
        <div class="graph-toolbar">
          <div class="graph-controls" role="group" aria-label="Graph view controls">
            <button class="graph-control" type="button" data-graph-zoom="out" aria-label="Zoom out">&minus;</button>
            <button class="graph-control" type="button" data-graph-reset>Fit all</button>
            <button class="graph-control" type="button" data-graph-zoom="in" aria-label="Zoom in">+</button>
            <button class="graph-control graph-expand-control" type="button" data-graph-expand aria-pressed="false">Expand</button>
          </div>
          <p><span data-graph-status aria-live="polite">100%</span> · Drag or use arrow keys to pan. Hover or focus an encounter to isolate its connections.</p>
        </div>
        <div class="graph-viewport" data-graph-viewport tabindex="0" aria-label="Interactive authored encounter graph. Use plus and minus to zoom, arrow keys to pan, and zero to fit the graph.">
          <svg class="encounter-graph" data-encounter-graph viewBox="{view_box}" data-initial-view-box="{view_box}" role="img" aria-labelledby="encounter-graph-title encounter-graph-description" preserveAspectRatio="xMidYMid meet">
            <title id="encounter-graph-title">Authored encounter graph</title>
            <desc id="encounter-graph-description">Full encounter titles are wrapped inside variable-size boxes. Directed curved edges represent lead-supported unlocks.</desc>
            <defs><marker id="graph-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z"></path></marker></defs>
            <g class="graph-edges">{"".join(edges)}</g>
            <g class="graph-encounters">{"".join(encounter_shapes)}</g>
          </svg>
        </div>
        {legend}
      </div>
    """


def _minimum_cut_panel(result: StructuralOverviewResult) -> str:
    diagnosis = result.validation_report.connectivity_diagnosis
    if diagnosis is None:
        return '<div class="diagnostic-panel"><strong>No minimum-cut witness</strong><p>The graph does not presently yield a multi-encounter connectivity diagnosis.</p></div>'
    adventure = result.adventure
    encounter_index = adventure.encounter_index()
    revelation_index = adventure.revelation_index()
    suggestions: list[str] = []
    for suggestion in diagnosis.repair_suggestions:
        source_title = encounter_index[suggestion.source_encounter_id].title
        target_title = encounter_index[suggestion.target_encounter_id].title
        if suggestion.revelation_id is not None:
            revelation_title = revelation_index[suggestion.revelation_id].title
            href = f"/clues/new?{urlencode({'source': suggestion.source_encounter_id, 'revelation': suggestion.revelation_id})}"
            label = f"Add lead from {source_title} supporting {revelation_title}"
        else:
            href = f"/revelations/new?{urlencode({'unlocks': suggestion.target_encounter_id, 'source': suggestion.source_encounter_id})}"
            label = f"Create revelation unlocking {target_title}, then add a lead from {source_title}"
        suggestions.append(f'<li><a href="{href}">{escape_html(label)}</a></li>')
    repairs = (
        f'<ol class="repair-list">{"".join(suggestions)}</ol>'
        if suggestions
        else "<p>No additional repair suggestions are needed.</p>"
    )
    side_a = ", ".join(encounter_index[item].title for item in diagnosis.side_a)
    side_b = ", ".join(encounter_index[item].title for item in diagnosis.side_b)
    return f'<div class="diagnostic-panel"><strong>Minimum-cut witness: {diagnosis.edge_connectivity} / {diagnosis.required_edge_connectivity}</strong><p>Side A: {escape_html(side_a)}. Side B: {escape_html(side_b)}. Additional distinct connections needed: {diagnosis.additional_connections_needed}.</p>{repairs}</div>'


def _coverage_matrix(result: StructuralOverviewResult) -> str:
    rows: list[str] = []
    for row in result.coverage:
        if not row.revelation.required:
            status = "Optional" if row.supporting_clues else "Optional · no leads"
            status_class = "ok" if row.supporting_clues else "deficit"
        else:
            status = "Sufficient" if row.is_sufficient else "Needs leads"
            status_class = "ok" if row.is_sufficient else "deficit"
        sources = ", ".join(encounter.title for encounter in row.source_encounters) or "None"
        action = f"/clues/new?{urlencode({'revelation': row.revelation.id})}"
        rows.append(
            f'<tr><th scope="row"><a href="{entity_url("revelation", row.revelation.id)}">{escape_html(row.revelation.title)}</a><small>{"Necessary" if row.revelation.required else "Optional"}</small></th><td>{len(row.supporting_clues)}<small>deficit {row.clue_deficit}</small></td><td>{len(row.source_encounters)}<small>deficit {row.source_deficit}</small></td><td>{escape_html(sources)}</td><td><span class="coverage-status {status_class}">{status}</span><a class="table-action" href="{action}">Add lead</a></td></tr>'
        )
    return f'<div class="table-scroll"><table class="coverage-table"><thead><tr><th>Revelation</th><th>Leads</th><th>Sources</th><th>Source encounters</th><th>Status</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
