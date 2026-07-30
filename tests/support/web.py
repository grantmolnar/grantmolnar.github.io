"""Reusable WSGI harness and web-application builders for tests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from html.parser import HTMLParser
from io import BytesIO
from types import TracebackType
from typing import TypeAlias, cast
from urllib.parse import urlencode
from wsgiref.types import StartResponse, WSGIApplication, WSGIEnvironment

from adventure_graph.application.adventure_authoring import UpdateAdventure
from adventure_graph.application.dice import RollDice
from adventure_graph.application.encounter_authoring import (
    GetEncounterDetail,
    RemoveEncounter,
    UpdateEncounter,
)
from adventure_graph.application.journal_workspace import GetJournalWorkspace
from adventure_graph.application.play_journal import CorrectLatestPlayOperation
from adventure_graph.application.play_ledger_workspace import GetPlayLedgerWorkspace
from adventure_graph.application.play_ledgers import GetPlayLedgers
from adventure_graph.application.play_tracking import (
    new_play_state,
    record_visit,
)
from adventure_graph.application.project import AuthoringProject, RelatedPlayState
from adventure_graph.application.project_browsing import (
    GetAdventureOverview,
    GetClueDetail,
    GetRevelationDetail,
)
from adventure_graph.application.reference_authoring import (
    CreateAndLinkReference,
    CreateReference,
    GetReferenceDetail,
    LinkReference,
    RemoveReference,
    UnlinkReference,
    UpdateReference,
)
from adventure_graph.application.run_workspace import (
    AddPlayVisitNote,
    EndPlaySession,
    EstablishPlayRevelation,
    ForeclosePlayRevelation,
    GetRunDashboard,
    MissPlayClue,
    RecordPlayDiceRoll,
    RecordPlayEncounterConsequence,
    RecordPlayReferenceNote,
    RecordPlayVisit,
    ReopenPlayRevelation,
    SpotPlayClue,
    StartPlaySession,
    TransitionPlayVisit,
    UnlockPlayEncounter,
)
from adventure_graph.application.structural_authoring import (
    CreateClue,
    CreateEncounter,
    CreateRevelation,
    GetStructuralOverview,
    UpdateClue,
    UpdateRevelation,
)
from adventure_graph.application.validation_settings import UpdateValidationPolicy
from adventure_graph.domain.adventure import Adventure
from adventure_graph.domain.play_state import PlayState
from adventure_graph.interfaces.web.app import AuthoringWebApplication
from adventure_graph.interfaces.web.contracts import (
    AuthoringCommands,
    AuthoringQueries,
    PlayCapability,
    PlayCommands,
    PlayLedgerQueries,
    PlayQueries,
)
from tests.support.adventures import complete_four_encounter_adventure
from tests.support.projects import (
    InMemoryAuthoringProject,
    InMemoryPlayProject,
    authoring_project,
    play_project,
)

WSGIRequestEnvironment: TypeAlias = WSGIEnvironment
WSGIStartResponse: TypeAlias = StartResponse
FormValue: TypeAlias = str | Sequence[str]
UploadedFormFile: TypeAlias = tuple[str, bytes, str]

CSRF_TOKEN = "known-token"


@dataclass
class CapturedWSGIResponse:
    """Capture status and headers from one in-process WSGI response."""

    status: str = ""
    headers: list[tuple[str, str]] = field(default_factory=list)

    def start_response(
        self,
        status: str,
        headers: list[tuple[str, str]],
        exc_info: tuple[type[BaseException], BaseException, TracebackType] | None = None,
        /,
    ) -> Callable[[bytes], object]:
        del exc_info
        self.status = status
        self.headers = headers

        def write(data: bytes) -> object:
            del data
            return None

        return write


def build_wsgi_environ(
    path: str,
    *,
    method: str = "GET",
    query: str = "",
    body: bytes = b"",
    content_type: str = "",
    host_authority: str | None = None,
    extra_environ: Mapping[str, object] | None = None,
) -> WSGIEnvironment:
    """Build one deterministic in-process WSGI environment."""
    values: dict[str, object] = {
        "REQUEST_METHOD": method,
        "SCRIPT_NAME": "",
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(body)) if method == "POST" else "",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http",
        "wsgi.input": BytesIO(body),
        "wsgi.errors": BytesIO(),
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }
    if host_authority is not None:
        values["HTTP_HOST"] = host_authority
    values.update(extra_environ or {})
    return cast(WSGIEnvironment, values)


def authoring_queries(project: AuthoringProject) -> AuthoringQueries:
    """Build the canonical browser query contract around one authoring project."""
    return AuthoringQueries(
        get_overview=GetAdventureOverview(project).execute,
        get_structure=GetStructuralOverview(project).execute,
        get_encounter=GetEncounterDetail(project).execute,
        get_revelation=GetRevelationDetail(project).execute,
        get_clue=GetClueDetail(project).execute,
        get_reference=GetReferenceDetail(project).execute,
    )


def authoring_commands(project: AuthoringProject) -> AuthoringCommands:
    """Build the canonical browser mutation contract around one authoring project."""
    return AuthoringCommands(
        update_adventure=UpdateAdventure(project).execute,
        create_encounter=CreateEncounter(project).execute,
        update_encounter=UpdateEncounter(project).execute,
        remove_encounter=RemoveEncounter(project).execute,
        create_reference=CreateReference(project).execute,
        create_and_link_reference=CreateAndLinkReference(project).execute,
        update_reference=UpdateReference(project).execute,
        link_reference=LinkReference(project).execute,
        unlink_reference=UnlinkReference(project).execute,
        remove_reference=RemoveReference(project).execute,
        update_revelation=UpdateRevelation(project).execute,
        update_clue=UpdateClue(project).execute,
        create_clue=CreateClue(project).execute,
        create_revelation=CreateRevelation(project).execute,
        update_validation_policy=UpdateValidationPolicy(project).execute,
    )


def build_authoring_app(
    adventure: Adventure | None = None,
    *,
    related_play_states: tuple[RelatedPlayState, ...] = (),
) -> tuple[AuthoringWebApplication, InMemoryAuthoringProject]:
    """Build the authoring WSGI adapter around an in-memory project."""
    project = authoring_project(adventure, related_play_states=related_play_states)
    app = AuthoringWebApplication(
        authoring_queries(project),
        authoring_commands(project),
        project_label="memory://adventure.json",
        csrf_token=CSRF_TOKEN,
    )
    return app, project


def build_play_app(
    adventure: Adventure | None = None,
    state: PlayState | None = None,
) -> tuple[AuthoringWebApplication, InMemoryPlayProject]:
    """Build the authoring adapter with an attached in-memory play journal."""
    resolved_adventure = adventure or complete_four_encounter_adventure()
    app, _ = build_authoring_app(resolved_adventure)
    resolved_state = state or record_visit(
        resolved_adventure,
        new_play_state(resolved_adventure),
        "alpha",
        ("alpha-to-beta",),
        ("Wrong click.",),
    )
    project = play_project(
        resolved_state,
        resolved_adventure,
        revision="play-revision-1",
        revision_prefix="play-revision",
        fixed_commit_revision="play-revision-2",
    )
    return (
        replace(
            app,
            play=PlayCapability(
                queries=PlayQueries(
                    get_journal_workspace=GetJournalWorkspace(project).execute,
                    get_run=GetRunDashboard(project).execute,
                    ledgers=PlayLedgerQueries(
                        get_workspace=GetPlayLedgerWorkspace(project).execute,
                        get_ledgers=GetPlayLedgers(project).execute,
                    ),
                ),
                commands=PlayCommands(
                    correct_latest=CorrectLatestPlayOperation(project).execute,
                    start_session=StartPlaySession(project).execute,
                    end_session=EndPlaySession(project).execute,
                    record_visit=RecordPlayVisit(project).execute,
                    transition_visit=TransitionPlayVisit(project).execute,
                    spot_clue=SpotPlayClue(project).execute,
                    miss_clue=MissPlayClue(project).execute,
                    establish_revelation=EstablishPlayRevelation(project).execute,
                    foreclose_revelation=ForeclosePlayRevelation(project).execute,
                    reopen_revelation=ReopenPlayRevelation(project).execute,
                    unlock_encounter=UnlockPlayEncounter(project).execute,
                    add_visit_note=AddPlayVisitNote(project).execute,
                    record_reference_note=RecordPlayReferenceNote(project).execute,
                    record_consequence=RecordPlayEncounterConsequence(project).execute,
                    roll_dice=RollDice(randbelow=lambda bound: bound - 1).execute,
                    record_dice_roll=RecordPlayDiceRoll(project).execute,
                ),
            ),
        ),
        project,
    )


def request_wsgi(
    app: WSGIApplication,
    path: str,
    method: str = "GET",
    *,
    query: str = "",
    form: Mapping[str, FormValue] | None = None,
    files: Mapping[str, UploadedFormFile] | None = None,
    content_type: str | None = None,
    host_authority: str | None = None,
    extra_environ: Mapping[str, object] | None = None,
) -> tuple[str, dict[str, str], str]:
    """Issue one deterministic in-process WSGI request."""
    if files:
        encoded_form, multipart_content_type = _multipart_form_body(form or {}, files)
        resolved_content_type = content_type or multipart_content_type
    else:
        encoded_form = urlencode(form or {}, doseq=True).encode("utf-8")
        resolved_content_type = content_type or (
            "application/x-www-form-urlencoded" if method == "POST" else ""
        )
    environ = build_wsgi_environ(
        path,
        method=method,
        query=query,
        body=encoded_form if method == "POST" else b"",
        content_type=resolved_content_type,
        host_authority=host_authority,
        extra_environ=extra_environ,
    )
    captured = CapturedWSGIResponse()
    content = b"".join(app(environ, cast(StartResponse, captured.start_response))).decode("utf-8")
    return captured.status, dict(captured.headers), content


def _multipart_form_body(
    form: Mapping[str, FormValue],
    files: Mapping[str, UploadedFormFile],
) -> tuple[bytes, str]:
    boundary = "AdventureGraphTestBoundary"
    chunks: list[bytes] = []
    for name, raw_values in form.items():
        values = (raw_values,) if isinstance(raw_values, str) else raw_values
        for value in values:
            chunks.extend(
                (
                    f"--{boundary}\r\n".encode(),
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                    value.encode("utf-8"),
                    b"\r\n",
                )
            )
    for name, (filename, content, media_type) in files.items():
        chunks.extend(
            (
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                ).encode(),
                f"Content-Type: {media_type}\r\n\r\n".encode(),
                content,
                b"\r\n",
            )
        )
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def post_form(
    app: WSGIApplication,
    path: str,
    form: Mapping[str, FormValue],
) -> tuple[str, dict[str, str], str]:
    """Submit one URL-encoded form to an in-process WSGI application."""
    return request_wsgi(app, path, method="POST", form=form)


class _VisiblePageText(HTMLParser):
    """Collect visible copy and accessibility labels while ignoring technical attributes."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        for name, value in attrs:
            if name in {"aria-label", "title", "placeholder", "alt"} and value:
                self.parts.append(value)

    def normalized(self) -> str:
        """Return whitespace-normalized visible text."""
        return " ".join(" ".join(self.parts).split())


def visible_page_text(body: str) -> str:
    """Extract user-visible and accessibility copy from rendered HTML."""
    parser = _VisiblePageText()
    parser.feed(body)
    return parser.normalized()


@dataclass(frozen=True, slots=True)
class RenderedPostForm:
    """One rendered POST form and the CSRF tokens it contains."""

    action: str
    csrf_tokens: tuple[str, ...]


class _PostFormParser(HTMLParser):
    """Collect POST form actions and hidden CSRF token values."""

    def __init__(self) -> None:
        super().__init__()
        self.forms: list[RenderedPostForm] = []
        self._action: str | None = None
        self._tokens: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "form" and (values.get("method") or "get").casefold() == "post":
            self._action = values.get("action") or ""
            self._tokens = []
        elif tag == "input" and self._action is not None and values.get("name") == "csrf_token":
            self._tokens.append(values.get("value") or "")

    def handle_endtag(self, tag: str) -> None:
        if tag != "form" or self._action is None:
            return
        self.forms.append(RenderedPostForm(self._action, tuple(self._tokens)))
        self._action = None
        self._tokens = []


def rendered_post_forms(body: str) -> tuple[RenderedPostForm, ...]:
    """Return every POST form and its rendered CSRF-token values."""
    parser = _PostFormParser()
    parser.feed(body)
    return tuple(parser.forms)


def new_encounter_form(**changes: str) -> dict[str, str]:
    """Return a valid encounter-creation form."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "title": "The Fifth Chamber",
        "summary": "A newly authored place.",
        "opening_view": "A fifth door stands open.",
        "content": "",
        "tags": "new",
        "required": "1",
    }
    values.update(changes)
    return values


def encounter_form(**changes: str) -> dict[str, str]:
    """Return a valid edit form for the Alphan encounter."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "title": "Alpha",
        "summary": "Summary for alpha.",
        "opening_view": "",
        "content": "",
        "tags": "",
        "required": "1",
        "start": "1",
    }
    values.update(changes)
    return values


def adventure_form(**changes: str) -> dict[str, str]:
    """Return a valid adventure metadata form."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "title": "Complete Four",
        "synopsis": "Four encounters form a complete clue graph.",
        "premise": "Investigate four connected encounters.",
        "explanation": "Every encounter points to every other encounter.",
    }
    values.update(changes)
    return values


def existing_clue_form(**changes: str) -> dict[str, str]:
    """Return a valid edit form for the alpha-to-beta clue."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "title": "alpha points to beta",
        "source_encounter_id": "alpha",
        "revelation_id": "find-beta",
        "description": "",
        "discovery": "search",
    }
    values.update(changes)
    return values


def existing_revelation_form(**changes: str) -> dict[str, str]:
    """Return a valid edit form for the find-beta revelation."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "title": "Find Beta",
        "description": "The group can locate beta.",
        "unlocks_encounter_id": "beta",
        "required": "1",
        "source_encounter_id": "",
    }
    values.update(changes)
    return values


def new_clue_form(**changes: str) -> dict[str, str]:
    """Return a valid clue-creation form."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "title": "Another path to Beta",
        "source_encounter_id": "alpha",
        "revelation_id": "find-beta",
        "description": "A second authored sign.",
        "discovery": "inspection",
    }
    values.update(changes)
    return values


def new_revelation_form(**changes: str) -> dict[str, str]:
    """Return a valid revelation-creation form."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "title": "Find the hidden vault",
        "description": "The group can locate a sealed archive.",
        "unlocks_encounter_id": "omega",
        "source_encounter_id": "alpha",
        "required": "1",
    }
    values.update(changes)
    return values


def reference_create_form(**changes: str) -> dict[str, str]:
    """Return a valid standalone reference-creation form."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "kind": "person",
        "title": "Mara Venn",
        "aliases": "The Bellkeeper",
        "summary": "A recurring witness who knows the old routes.",
        "content": "## Mara Venn\n\nMara records every midnight arrival.",
        "tags": "witness, staff",
        "encounter_id": "",
        "context": "",
        "return_to": "",
    }
    values.update(changes)
    return values


def reference_edit_form(**changes: str) -> dict[str, str]:
    """Return a valid reference-edit form for the Cora Pike fixture."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "kind": "person",
        "title": "Cora Pike",
        "aliases": "The Housekeeper",
        "summary": "The hall's observant housekeeper.",
        "content": "## Cora Pike\n\nCora protects the household before its owner.",
        "tags": "staff, witness",
    }
    values.update(changes)
    return values


def reference_link_form(reference_id: str, **changes: str) -> dict[str, str]:
    """Return a valid encounter/reference link form."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "reference_id": reference_id,
        "context": "Relevant to this encounter.",
    }
    values.update(changes)
    return values


def reference_unlink_form(reference_id: str, **changes: str) -> dict[str, str]:
    """Return a valid encounter/reference unlink form."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
        "reference_id": reference_id,
    }
    values.update(changes)
    return values


def removal_form(**changes: str) -> dict[str, str]:
    """Return a valid authored-entity removal form."""
    values = {
        "csrf_token": CSRF_TOKEN,
        "expected_revision": "revision-1",
    }
    values.update(changes)
    return values
