"""Tests for conservative safe rendering of authored prose."""

from adventure_graph.interfaces.web.markdown import render_safe_markdown


def test_safe_markdown_renders_supported_block_and_inline_forms() -> None:
    source = """# Heading

A **strong** and *emphasized* paragraph with `code`.

- first
- second

1. one
2. two

> quoted

```python
<script>alert(1)</script>
```
"""

    rendered = render_safe_markdown(source)

    assert "<h1>Heading</h1>" in rendered
    assert "<strong>strong</strong>" in rendered
    assert "<em>emphasized</em>" in rendered
    assert "<code>code</code>" in rendered
    assert "<ul><li>first</li><li>second</li></ul>" in rendered
    assert "<ol><li>one</li><li>two</li></ol>" in rendered
    assert "<blockquote>quoted</blockquote>" in rendered
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in rendered
    assert "<script>" not in rendered


def test_safe_markdown_handles_empty_and_unclosed_code_blocks() -> None:
    assert "No long-form material" in render_safe_markdown("  \n")

    rendered = render_safe_markdown("```\nunsafe <tag>")

    assert rendered == "<pre><code>unsafe &lt;tag&gt;</code></pre>"
