"""Transport-neutral report packet queries and publication commands."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from adventure_graph.application.documents import render_adventure_documents
from adventure_graph.application.play_journal import PlayJournalSnapshot
from adventure_graph.application.project import ProjectRevision
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.validation import validate_adventure
from adventure_graph.domain.validation_models import ValidationReport


@dataclass(frozen=True, slots=True)
class ReportDocument:
    """One generated report document before interface-specific rendering."""

    name: str
    title: str
    content: str


@dataclass(frozen=True, slots=True)
class ReportPacketResult:
    """Generated reports and their source revision."""

    adventure: Adventure
    validation_report: ValidationReport
    revision: ProjectRevision
    documents: tuple[ReportDocument, ...]
    event_count: int
    output_label: str

    def document_index(self) -> dict[str, ReportDocument]:
        """Return generated documents keyed by relative packet name."""
        return {document.name: document for document in self.documents}


@dataclass(frozen=True, slots=True)
class PublishReportPacketCommand:
    """Publish generated reports from one expected source revision."""

    expected_revision: ProjectRevision


@dataclass(frozen=True, slots=True)
class PublishReportPacketResult:
    """Names written by one report publication."""

    document_names: tuple[str, ...]
    output_label: str


class GeneratedReportProject(Protocol):
    """Application-facing port for report source state and generated output."""

    @property
    def output_label(self) -> str:
        """Return a user-facing description of the configured output destination."""
        ...

    def load(self) -> PlayJournalSnapshot:
        """Load the current adventure and journal at one source revision."""
        ...

    def publish(
        self,
        documents: Mapping[str, str],
        expected_revision: ProjectRevision,
    ) -> tuple[str, ...]:
        """Write reports only when their source revision is still current."""
        ...


class GetReportPacket:
    """Generate the current report packet without writing files."""

    def __init__(self, project: GeneratedReportProject) -> None:
        self._project = project

    def execute(self) -> ReportPacketResult:
        """Return all current generated reports as plain Markdown values."""
        snapshot = self._project.load()
        report = validate_adventure(snapshot.adventure)
        rendered = render_adventure_documents(snapshot.adventure, report, snapshot.state)
        return ReportPacketResult(
            adventure=snapshot.adventure,
            validation_report=report,
            revision=snapshot.revision,
            documents=tuple(
                ReportDocument(name, _report_title(name, content), content)
                for name, content in rendered.items()
            ),
            event_count=len(snapshot.state.events),
            output_label=self._project.output_label,
        )


class PublishReportPacket:
    """Publish a generated packet through a revision-aware output port."""

    def __init__(self, project: GeneratedReportProject) -> None:
        self._project = project

    def execute(self, command: PublishReportPacketCommand) -> PublishReportPacketResult:
        """Regenerate and publish reports without stale-source overwrite."""
        snapshot = self._project.load()
        report = validate_adventure(snapshot.adventure)
        documents = render_adventure_documents(snapshot.adventure, report, snapshot.state)
        names = self._project.publish(documents, command.expected_revision)
        return PublishReportPacketResult(names, self._project.output_label)


def _report_title(name: str, content: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return name.rsplit("/", 1)[-1].removesuffix(".md").replace("-", " ").title()
