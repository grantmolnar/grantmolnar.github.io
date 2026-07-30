"""Application command for creating an editable project from a packaged starter."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Protocol

from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.identifiers import new_adventure_identifier
from adventure_graph.domain.play_state import PlayState


class ProjectInitializer(Protocol):
    """Application-facing port for one new canonical project directory."""

    def create(self, adventure: Adventure, play_state: PlayState) -> None:
        """Create the authored source and matching empty journal."""
        ...


@dataclass(frozen=True, slots=True)
class InitializedStarterProject:
    """Freshly identified starter adventure and its matching empty journal."""

    adventure: Adventure
    play_state: PlayState


def instantiate_adventure_template(
    template: Adventure,
    adventure_id_factory: Callable[[], str] = new_adventure_identifier,
) -> Adventure:
    """Copy one reusable template under fresh canonical identity."""
    return replace(template, id=adventure_id_factory())


class InitializeStarterProject:
    """Clone one starter's content while assigning fresh canonical identity."""

    def __init__(
        self,
        project: ProjectInitializer,
        starter: Adventure,
        adventure_id_factory: Callable[[], str] = new_adventure_identifier,
    ) -> None:
        self._project = project
        self._starter = starter
        self._adventure_id_factory = adventure_id_factory

    def execute(self) -> InitializedStarterProject:
        """Create a distinct project even when the starter is copied repeatedly."""
        adventure = instantiate_adventure_template(self._starter, self._adventure_id_factory)
        play_state = new_play_state(adventure)
        self._project.create(adventure, play_state)
        return InitializedStarterProject(adventure, play_state)
