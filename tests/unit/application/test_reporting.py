"""Tests for report packet generation and publication."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tests.support.adventures import complete_four_encounter_adventure

from adventure_graph.application.play_journal import PlayJournalSnapshot
from adventure_graph.application.play_tracking import new_play_state
from adventure_graph.application.project import ProjectRevision
from adventure_graph.application.reporting import (
    GetReportPacket,
    PublishReportPacket,
    PublishReportPacketCommand,
)


@dataclass
class MemoryReportProject:
    """In-memory report output port for application tests."""

    published: dict[str, str]

    @property
    def output_label(self) -> str:
        return "memory://generated"

    def load(self) -> PlayJournalSnapshot:
        adventure = complete_four_encounter_adventure()
        return PlayJournalSnapshot(adventure, new_play_state(adventure), ProjectRevision("r1"))

    def publish(
        self,
        documents: Mapping[str, str],
        expected_revision: ProjectRevision,
    ) -> tuple[str, ...]:
        assert expected_revision == ProjectRevision("r1")
        self.published = dict(documents)
        return tuple(sorted(documents))


def test_report_query_returns_live_markdown_and_publish_uses_same_packet() -> None:
    project = MemoryReportProject({})

    packet = GetReportPacket(project).execute()
    result = PublishReportPacket(project).execute(PublishReportPacketCommand(packet.revision))

    assert packet.event_count == 0
    assert "00-overview.md" in packet.document_index()
    assert packet.document_index()["00-overview.md"].title == "Complete Four"
    assert result.output_label == "memory://generated"
    assert set(result.document_names) == set(project.published)
