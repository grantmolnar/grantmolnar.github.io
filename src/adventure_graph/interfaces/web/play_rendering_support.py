"""Shared rendering helpers for Play-mode forms and feedback."""

from __future__ import annotations

import re

from adventure_graph.domain.adventure import Adventure
from adventure_graph.interfaces.web.page_rendering import (
    escape_html,
    humanize_authored_identifiers,
)


def render_play_hidden_fields(
    csrf_token: str,
    revision: str,
    focus_encounter_id: str,
) -> str:
    """Render the common revision-safe fields used by Play write forms."""
    return f"""
      <input type="hidden" name="csrf_token" value="{escape_html(csrf_token)}">
      <input type="hidden" name="expected_revision" value="{escape_html(revision)}">
      <input type="hidden" name="focus_encounter_id" value="{escape_html(focus_encounter_id)}">
    """


def present_play_error(error: ValueError, adventure: Adventure) -> str:
    """Replace internal operation indexes and authored IDs in GM-facing errors."""
    message = humanize_authored_identifiers(str(error), adventure)
    substitutions = (
        (r"Revelation operation \d+", "The submitted revelation update"),
        (r"Transition operation \d+", "The submitted visit update"),
        (r"Visit operation \d+", "The submitted visit update"),
        (r"Operation \d+", "The submitted play update"),
    )
    for pattern, replacement in substitutions:
        message = re.sub(pattern, replacement, message)
    return message
