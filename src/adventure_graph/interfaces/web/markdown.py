"""Conservative, HTML-safe rendering for authored Markdown-like prose."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

_INLINE_CODE_PATTERN = r"`([^`]+)`"
_STRONG_PATTERN = r"\*\*([^*]+)\*\*"
_EMPHASIS_PATTERN = r"(?<!\*)\*([^*]+)\*(?!\*)"
_ORDERED_ITEM_PATTERN = r"^\d+[.)]\s+(.*)$"


def _string_list() -> list[str]:
    return []


def render_safe_markdown(source: str) -> str:
    """Render a deliberately small Markdown subset after escaping all authored HTML."""
    if not source.strip():
        return '<p class="empty-copy">No long-form material has been written yet.</p>'
    return _MarkdownRenderer().render(source)


@dataclass
class _MarkdownRenderer:
    output: list[str] = field(default_factory=_string_list)
    paragraph: list[str] = field(default_factory=_string_list)
    code_lines: list[str] = field(default_factory=_string_list)
    list_kind: str | None = None
    in_code: bool = False

    def render(self, source: str) -> str:
        for raw_line in source.splitlines():
            self._consume(raw_line)
        if self.in_code:
            self._emit_code()
        self._flush_paragraph()
        self._close_list()
        return "".join(self.output)

    def _consume(self, raw_line: str) -> None:
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            self._toggle_code()
        elif self.in_code:
            self.code_lines.append(raw_line)
        elif not stripped:
            self._flush_blocks()
        elif self._emit_heading(stripped) or self._emit_list_item(stripped):
            return
        elif stripped.startswith("> "):
            self._flush_blocks()
            self.output.append(f"<blockquote>{_inline(stripped[2:])}</blockquote>")
        else:
            self.paragraph.append(stripped)

    def _toggle_code(self) -> None:
        self._flush_blocks()
        if self.in_code:
            self._emit_code()
        else:
            self.in_code = True

    def _emit_code(self) -> None:
        escaped = html.escape("\n".join(self.code_lines))
        self.output.append(f"<pre><code>{escaped}</code></pre>")
        self.code_lines.clear()
        self.in_code = False

    def _emit_heading(self, line: str) -> bool:
        level = _heading_level(line)
        if level is None:
            return False
        self._flush_blocks()
        self.output.append(f"<h{level}>{_inline(line[level + 1 :])}</h{level}>")
        return True

    def _emit_list_item(self, line: str) -> bool:
        ordered_match = re.match(_ORDERED_ITEM_PATTERN, line)
        unordered_text = line[2:] if line.startswith(("- ", "* ")) else None
        if ordered_match is None and unordered_text is None:
            return False
        self._flush_paragraph()
        desired_kind = "ol" if ordered_match is not None else "ul"
        self._open_list(desired_kind)
        item = ordered_match.group(1) if ordered_match is not None else unordered_text
        self.output.append(f"<li>{_inline(item or '')}</li>")
        return True

    def _open_list(self, kind: str) -> None:
        if self.list_kind == kind:
            return
        self._close_list()
        self.output.append(f"<{kind}>")
        self.list_kind = kind

    def _flush_blocks(self) -> None:
        self._flush_paragraph()
        self._close_list()

    def _flush_paragraph(self) -> None:
        if not self.paragraph:
            return
        self.output.append(f"<p>{_inline(' '.join(self.paragraph))}</p>")
        self.paragraph.clear()

    def _close_list(self) -> None:
        if self.list_kind is None:
            return
        self.output.append(f"</{self.list_kind}>")
        self.list_kind = None


def _heading_level(line: str) -> int | None:
    marker = len(line) - len(line.lstrip("#"))
    if 1 <= marker <= 4 and len(line) > marker and line[marker] == " ":
        return marker
    return None


def _inline(source: str) -> str:
    escaped = html.escape(source)
    escaped = re.sub(_INLINE_CODE_PATTERN, r"<code>\1</code>", escaped)
    escaped = re.sub(_STRONG_PATTERN, r"<strong>\1</strong>", escaped)
    return re.sub(_EMPHASIS_PATTERN, r"<em>\1</em>", escaped)
