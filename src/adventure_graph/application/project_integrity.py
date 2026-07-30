"""Shared integrity checks for authored changes against related play journals."""

from adventure_graph.application.play_tracking import project_play_state
from adventure_graph.application.project import RelatedPlayState
from adventure_graph.domain.adventure import Adventure


def validate_related_play_states(
    adventure: Adventure,
    related_play_states: tuple[RelatedPlayState, ...],
) -> None:
    """Refuse an authored change that would invalidate any known play journal."""
    for related in related_play_states:
        try:
            project_play_state(adventure, related.state)
        except ValueError as error:
            raise ValueError(
                f"Related play state {related.source} would be invalid after this change: {error}"
            ) from error
