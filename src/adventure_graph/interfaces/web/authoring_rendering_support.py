"""Shared HTML helpers for authoring-specific page renderers."""

from __future__ import annotations

from collections.abc import Iterable

from adventure_graph.application.dependency_previews import DependencyPreview
from adventure_graph.domain.adventure import Encounter, Revelation
from adventure_graph.interfaces.web.markdown import render_safe_markdown
from adventure_graph.interfaces.web.page_rendering import escape_html


def dependency_section(preview: DependencyPreview, kind: str) -> str:
    display_kind = "encounter" if kind == "encounter" else kind
    references = _dependency_items(
        preview.authored_references,
        "No authored records reference this identifier.",
    )
    move = _dependency_items(preview.move_context, "This item cannot be moved.")
    removal = _dependency_items(preview.removal_dependencies, "No authored records block removal.")
    cascade = _dependency_items(preview.cascade_effects, "No authored cascade effects.")
    journals = _dependency_items(
        preview.journal_references, "No known play journal references this record."
    )
    return f"""
      <section class="section dependency-preview">
        <div class="section-heading"><h2>Dependency preview</h2><span>Connections affected by structural changes</span></div>
        <div class="dependency-grid">
          <article><h3>Authored references</h3>{references}</article>
          <article><h3>Move context</h3>{move}</article>
          <article><h3>Removal blockers</h3>{removal}</article>
          <article><h3>Cascade effects</h3>{cascade}</article>
          <article class="dependency-wide"><h3>Journal references</h3>{journals}</article>
        </div>
        <p class="form-help">Review what this {display_kind} is connected to before moving or removing it.</p>
      </section>
    """


def _dependency_items(items: tuple[str, ...], empty: str) -> str:
    if not items:
        return f'<p class="muted-note">{escape_html(empty)}</p>'
    return f'<ul class="compact-list">{"".join(f"<li>{escape_html(item)}</li>" for item in items)}</ul>'


def select_options(
    entities: Iterable[Encounter | Revelation],
    selected_id: str,
    *,
    allow_empty: bool,
    empty_label: str = "Select…",
) -> str:
    options = [f'<option value="">{escape_html(empty_label)}</option>'] if allow_empty else []
    options.extend(
        f'<option value="{escape_html(entity.id)}"{" selected" if entity.id == selected_id else ""}>{escape_html(entity.title)}</option>'
        for entity in entities
    )
    return "".join(options)


def edit_attributes(href: str, label: str) -> str:
    return (
        f'data-edit-href="{escape_html(href)}" tabindex="0" role="link" '
        f'aria-label="Edit {escape_html(label)}" '
        'title="Double-click or press Enter to edit"'
    )


def editable_plain_text(
    value: str,
    href: str,
    label: str,
    empty_copy: str,
    *,
    class_name: str,
) -> str:
    content = (
        escape_html(value)
        if value
        else f'<span class="empty-copy">{escape_html(empty_copy)}</span>'
    )
    return f'<p class="{class_name} editable-surface" {edit_attributes(href, label)}>{content}</p>'


def editable_markdown(value: str, href: str, label: str, empty_copy: str) -> str:
    content = (
        render_safe_markdown(value)
        if value
        else f'<p class="empty-copy">{escape_html(empty_copy)}</p>'
    )
    return f'<div class="prose editable-surface" {edit_attributes(href, label)}>{content}</div>'


def form_hidden(csrf_token: str, revision: str) -> str:
    return f'<input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}"><input type="hidden" name="expected_revision" value="{escape_html(revision)}">'


def editor_toolbar(label: str, action: str) -> str:
    return f'<div class="editor-toolbar"><div><strong>{escape_html(label)}</strong><span data-draft-status>Unsaved changes are preserved in this browser.</span><div class="draft-actions"><button class="text-button" type="button" data-recover-draft hidden>Recover older draft</button><button class="text-button" type="button" data-discard-draft hidden>Discard browser draft</button></div></div><button class="button primary" type="submit">{escape_html(action)}</button></div>'


def editor_footer(revision: str, action: str) -> str:
    del revision
    return f'<div class="editor-footer"><p>Ctrl/⌘ S saves · Esc returns without discarding this browser draft</p><button class="button primary" type="submit">{escape_html(action)}</button></div>'


def revision_warning(expected: str, current: str) -> str:
    if expected == current:
        return ""
    return '<p class="form-help conflict-copy">The adventure changed after this page opened. Reload, recover this browser draft, and save it against the latest version.</p>'
