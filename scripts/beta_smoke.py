"""Build-artifact smoke test for the documented beta installation and workflow path."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import venv
from email.parser import Parser
from html.parser import HTMLParser
from pathlib import Path
from uuid import UUID
from zipfile import ZipFile


ARCHIVE_ID = "beta-audit"
ARCHIVE_FILENAME = f"{ARCHIVE_ID}.journal.json"
AUDIT_REFERENCE_ID = "8506dafa-ac5f-443d-b537-b18cb97d6f90"
AUDIT_WORKSPACE_NAME = "Beta Workspace – Ω"
AUDIT_PROJECT_NAME = "Sample Adventure – Café"
AUDIT_SECOND_PROJECT_NAME = "Second Project – Niño"
AUDIT_COPY_WORKSPACE_NAME = "Copied Workspace – Δ"
AUDIT_COPY_PROJECT_NAME = "Copied Project – Café"
AUDIT_RENAMED_PROJECT_NAME = "Renamed Project – Ω"
AUDIT_SAMPLE_WORKSPACE_NAME = "Sample Onboarding – Luz"
AUDIT_BLANK_WORKSPACE_NAME = "Blank Adventure – Vacío"


def main() -> int:
    """Install one built wheel in a clean environment and exercise the beta path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel-dir", type=Path, default=Path("dist"))
    args = parser.parse_args()
    wheels = tuple(sorted(args.wheel_dir.glob("adventure_graph-*.whl")))
    if len(wheels) != 1:
        raise SystemExit(f"Expected exactly one Adventure Graph wheel in {args.wheel_dir}.")
    _verify_wheel_contract(wheels[0])

    with tempfile.TemporaryDirectory(prefix="adventure-graph-beta-") as temporary:
        root = Path(temporary)
        environment = root / ".venv"
        venv.EnvBuilder(with_pip=True, clear=True).create(environment)
        python = _environment_executable(environment, "python")
        command = _environment_executable(environment, "adventure-graph")
        desktop_command = _environment_executable(environment, "adventure-graph-desktop")
        _run(python, "-m", "pip", "install", "--no-index", str(wheels[0].resolve()))
        _run(python, "-m", "pip", "check")
        _run(command, "--help")
        _run(command, "--version")
        _run(python, "-m", "adventure_graph", "--help")
        _run(python, "-m", "adventure_graph", "--version")
        _exercise_installed_desktop_launcher(desktop_command, root)
        blank_workspace = root / AUDIT_BLANK_WORKSPACE_NAME
        blank_workspace.mkdir()
        _exercise_browser_blank_adventure_onboarding(command, blank_workspace)
        sample_workspace = root / AUDIT_SAMPLE_WORKSPACE_NAME
        sample_workspace.mkdir()
        _exercise_browser_sample_onboarding(command, sample_workspace)

        workspace = root / AUDIT_WORKSPACE_NAME
        project = workspace / AUDIT_PROJECT_NAME
        _run(command, "init", str(project))
        adventure = project / "adventure.json"
        state = project / "play-state.json"
        _verify_initialized_identity(adventure, state)
        _run(command, "validate", str(adventure))
        _exercise_authoring_workflow(command, adventure)
        _launch_and_probe(
            command,
            project,
            page_path="/adventures",
            expected_text="The Glass Saint",
        )
        _launch_and_probe(
            command,
            workspace,
            page_path="/adventures",
            expected_text="The Glass Saint",
        )
        second_project = workspace / AUDIT_SECOND_PROJECT_NAME
        _run(command, "init", str(second_project))
        _launch_and_probe(
            command,
            workspace,
            page_path="/",
            expected_text="Browse your adventures",
        )
        _exercise_play_workflow(command, adventure, state, root)
        _exercise_post_play_authoring(command, adventure)
        _exercise_archive_workflow(command, adventure, state, project)
        _exercise_malformed_file_repair(command, adventure)
        _exercise_browser_workflow(command, adventure, state, project)
        _launch_and_probe(
            command,
            adventure,
            page_path="/journal",
            expected_text="Browser dice audit",
        )
        _exercise_copy_rename_and_reopen(command, project, root)

    print(
        "Clean wheel install, title-only Play onboarding, browser sample onboarding, CLI and "
        "browser authoring, multi-session "
        "play, correction, CLI and browser persistent-reference notes, archive lifecycles, "
        "recorded browser dice, "
        "malformed-file repair, Unicode and spaced "
        "paths, direct project-directory launch, multi-project selection refusal, project "
        "relocation, both CLI entry points, the installed desktop-launcher entry point, and "
        "repeated UI launch passed."
    )
    return 0


def _exercise_browser_blank_adventure_onboarding(command: str, workspace: Path) -> None:
    """Create a title-only adventure and cross the installed Play boundary safely."""
    with _running_ui(command, workspace) as base_url:
        client = _BrowserClient(base_url)
        status, _, page = client.get("/adventures/new")
        if status != 200:
            raise RuntimeError("Installed browser did not open blank-adventure onboarding.")
        status, _, page = client.submit(
            page,
            "/adventures/new",
            {
                "title": "The Unwritten Door",
                "synopsis": "",
                "premise": "",
                "explanation": "",
                "opening_title": "",
                "opening_summary": "",
                "opening_view": "",
            },
        )
        if status != 200 or "The Unwritten Door" not in page:
            raise RuntimeError("Installed browser did not create a title-only adventure.")

        status, _, page = client.get("/play")
        if (
            status != 200
            or "This adventure has no encounters yet." not in page
            or "Add first encounter" not in page
            or "Workspace could not be loaded" in page
        ):
            raise RuntimeError(
                "Installed browser did not render the title-only Play empty state."
            )

        status, _, page = client.get("/encounters/new?return_to=%2Fplay")
        if (
            status != 200
            or "Add an encounter during play" not in page
            or 'name="start" value="1" data-draft-field checked' not in page
        ):
            raise RuntimeError(
                "Installed browser did not offer a start-selected first encounter."
            )
        status, _, page = client.submit(
            page,
            "/encounters/new",
            {
                "title": "The First Room",
                "summary": "",
                "opening_view": "",
                "content": "",
                "tags": "",
            },
        )
        if (
            status != 200
            or "The First Room" not in page
            or "This adventure has no encounters yet." in page
        ):
            raise RuntimeError(
                "Installed browser did not return the first encounter to Play mode."
            )

    projects = tuple(
        child
        for child in workspace.iterdir()
        if child.is_dir() and (child / "adventure.json").is_file()
    )
    if len(projects) != 1:
        raise RuntimeError("Blank-adventure onboarding created an unexpected project set.")
    encounters = _json_object(projects[0] / "adventure.json").get("encounters")
    if not isinstance(encounters, list) or [item.get("id") for item in encounters] != [
        "the-first-room"
    ]:
        raise RuntimeError("Blank-adventure onboarding did not persist its first encounter.")


def _exercise_browser_sample_onboarding(command: str, workspace: Path) -> None:
    """Create the one packaged beta sample through the installed browser."""
    with _running_ui(command, workspace) as base_url:
        client = _BrowserClient(base_url)
        status, _, page = client.get("/adventures")
        if (
            status != 200
            or "Add The Glass Saint sample" not in page
            or "Create blank adventure" not in page
        ):
            raise RuntimeError("Installed browser did not expose empty-workspace onboarding.")
        status, _, page = client.submit(page, "/adventures/sample")
        if status != 200 or "Sample added" not in page:
            raise RuntimeError("Installed browser did not add the packaged Glass Saint sample.")

    projects = tuple(
        sorted(
            (
                child
                for child in workspace.iterdir()
                if child.is_dir() and (child / "adventure.json").is_file()
            ),
            key=lambda child: child.name,
        )
    )
    if tuple(project.name for project in projects) != ("the-glass-saint",):
        raise RuntimeError(
            "Empty-workspace onboarding created an unexpected sample project set: "
            f"{tuple(project.name for project in projects)!r}."
        )
    adventure = projects[0] / "adventure.json"
    state = projects[0] / "play-state.json"
    _verify_initialized_identity(adventure, state)
    payload = _json_object(adventure)
    metadata = payload.get("adventure")
    if not isinstance(metadata, dict) or metadata.get("title") != "The Glass Saint":
        raise RuntimeError("Browser onboarding did not persist The Glass Saint template.")
    state_payload = _json_object(state)
    if state_payload.get("events") != []:
        raise RuntimeError("Browser onboarding did not create an empty playthrough.")


def _exercise_installed_desktop_launcher(command: str, root: Path) -> None:
    workspace = root / "Desktop launcher smoke"
    workspace.mkdir()
    config_home = root / "desktop-launcher-config"
    environment = os.environ.copy()
    environment["ADVENTURE_GRAPH_CONFIG_HOME"] = str(config_home)
    _run_with_environment(
        environment,
        command,
        "--smoke-test",
        str(workspace),
    )
    if config_home.exists():
        raise RuntimeError("Installed desktop smoke mode persisted launcher settings.")


def _verify_initialized_identity(adventure: Path, state: Path) -> None:
    adventure_payload = _json_object(adventure)
    metadata = adventure_payload.get("adventure")
    if not isinstance(metadata, dict):
        raise RuntimeError("Installed init did not persist adventure metadata.")
    adventure_id = metadata.get("id")
    if not isinstance(adventure_id, str) or UUID(adventure_id).version != 4:
        raise RuntimeError("Installed init did not assign fresh UUIDv4 adventure identity.")
    state_payload = _json_object(state)
    if state_payload.get("adventure_id") != adventure_id:
        raise RuntimeError("Installed init created a journal for a different adventure identity.")


def _verify_wheel_contract(wheel: Path) -> None:
    maximum_wheel_bytes = 2 * 1024 * 1024
    if wheel.stat().st_size > maximum_wheel_bytes:
        raise RuntimeError(
            f"Wheel is unexpectedly large: {wheel.stat().st_size} bytes; "
            f"limit is {maximum_wheel_bytes}."
        )
    with ZipFile(wheel) as archive:
        names = tuple(archive.namelist())
        forbidden_fragments = (
            "/__pycache__/",
            ".pyc",
            ".pyo",
            "adventure_graph/tests/",
            "adventure_graph/scripts/",
            "adventure_graph/docs/",
            "adventure_graph/examples/",
            "adventure_graph/schemas/",
        )
        forbidden = [
            name
            for name in names
            if any(fragment in name for fragment in forbidden_fragments)
        ]
        if forbidden:
            raise RuntimeError(f"Wheel contains development-only payload: {forbidden!r}.")
        unexpected_roots = [
            name
            for name in names
            if not name.startswith("adventure_graph/")
            and ".dist-info/" not in name
        ]
        if unexpected_roots:
            raise RuntimeError(
                f"Wheel contains unexpected top-level payload: {unexpected_roots!r}."
            )
        adventure_resources = {
            name
            for name in names
            if name.startswith("adventure_graph/resources/")
            and name.endswith(".adventure.json")
        }
        expected_adventure_resources = {
            "adventure_graph/resources/the-glass-saint.adventure.json"
        }
        if adventure_resources != expected_adventure_resources:
            raise RuntimeError(
                "Wheel contains an unexpected tester-facing adventure resource set: "
                f"{sorted(adventure_resources)!r}."
            )

        required_runtime_files = {
            "adventure_graph/py.typed",
            "adventure_graph/desktop.py",
            "adventure_graph/infrastructure/desktop_settings.py",
            "adventure_graph/resources/the-glass-saint.adventure.json",
            "adventure_graph/interfaces/web/assets/app.css",
            "adventure_graph/interfaces/web/assets/app.js",
        }
        missing_runtime_files = sorted(required_runtime_files.difference(names))
        if missing_runtime_files:
            raise RuntimeError(
                f"Wheel is missing required runtime payload: {missing_runtime_files!r}."
            )
        metadata_names = [
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        ]
        terms_names = [
            name
            for name in archive.namelist()
            if name.endswith(".dist-info/licenses/BETA-TERMS.md")
        ]
        if len(metadata_names) != 1 or len(terms_names) != 1:
            raise RuntimeError("Wheel does not contain one metadata record and private-beta terms.")
        metadata = Parser().parsestr(archive.read(metadata_names[0]).decode("utf-8"))
        requires_python = metadata.get("Requires-Python")
        if requires_python not in {">=3.11,<3.14", "<3.14,>=3.11"}:
            raise RuntimeError(f"Unexpected wheel Python contract: {requires_python!r}.")
        if metadata.get("License-Expression") != "LicenseRef-Adventure-Graph-Beta":
            raise RuntimeError("Wheel does not declare the private-beta license expression.")
        wheel_version = metadata.get("Version")
        if not wheel_version:
            raise RuntimeError("Wheel metadata does not declare a version.")
        terms = archive.read(terms_names[0]).decode("utf-8")
        if (
            f"Adventure Graph {wheel_version} is provided for private beta evaluation"
            not in terms
            or "All rights reserved" not in terms
        ):
            raise RuntimeError("Wheel contains stale or unexpected private-beta terms.")


def authoring_command_arguments(adventure: Path) -> tuple[tuple[str, ...], ...]:
    """Return the installed-CLI commands used by the authoring audit."""
    adventure_text = str(adventure)
    return (
        (
            "add-encounter",
            adventure_text,
            "Beta Annex",
            "--opening-view",
            "Three catalog chests stand beneath a cracked blue window.",
            "--optional",
            "--tag",
            "audit",
        ),
        (
            "add-clue",
            adventure_text,
            "Annex provenance ledger",
            "--source",
            "beta-annex",
            "--revelation",
            "the-archive-vault-contains-the-relics-hidden-provenance",
            "--description",
            "The annex ledger repeats the restricted accession sequence.",
            "--discovery",
            "automatic",
        ),
        (
            "add-clue",
            adventure_text,
            "Annex ritual chalk",
            "--source",
            "beta-annex",
            "--revelation",
            "the-bell-chapel-is-being-used-for-ritual-preparation",
            "--description",
            "Chalk residues match the chapel's preparation marks.",
        ),
        (
            "add-clue",
            adventure_text,
            "Annex witness list",
            "--source",
            "beta-annex",
            "--revelation",
            "the-procession-court-holds-the-thefts-public-witnesses",
            "--description",
            "A copied list names witnesses assigned to the procession court.",
        ),
        (
            "edit-encounter",
            adventure_text,
            "beta-annex",
            "--title",
            "Beta Annex Reopened",
        ),
        ("validate", adventure_text),
        ("inspect", adventure_text, "encounter", "beta-annex"),
    )


def play_command_arguments(adventure: Path, state: Path) -> tuple[tuple[str, ...], ...]:
    """Return the installed-CLI commands used by the multi-session play audit."""
    adventure_text = str(adventure)
    state_text = str(state)
    return (
        (
            "start-session",
            adventure_text,
            state_text,
            "--title",
            "First beta table",
            "--played-on",
            "2026-07-25",
            "--participant",
            "Test GM",
            "--participant",
            "Test Player",
            "--opening-note",
            "The table begins at the shattered gallery.",
        ),
        (
            "visit",
            adventure_text,
            state_text,
            "the-shattered-gallery",
            "--party",
            "Beta table",
            "--clue",
            "accession-number-on-a-glass-shard",
            "--note",
            "The witnesses preserve the first evidence chain.",
        ),
        (
            "note",
            adventure_text,
            state_text,
            "1",
            "The curator keeps an authenticated copy.",
        ),
        (
            "reference-note",
            adventure_text,
            state_text,
            AUDIT_REFERENCE_ID,
            "Saint Olyra's name is now part of the witnesses' working theory.",
        ),
        (
            "miss-clue",
            adventure_text,
            state_text,
            "service-door-witness-line",
            "--visit",
            "1",
        ),
        (
            "establish-revelation",
            adventure_text,
            state_text,
            "the-archive-vault-contains-the-relics-hidden-provenance",
            "--clue",
            "accession-number-on-a-glass-shard",
            "--note",
            "The accession sequence identifies the restricted archive.",
        ),
        (
            "consequence",
            adventure_text,
            state_text,
            "the-shattered-gallery",
            "The registrar seals the public doors.",
        ),
        (
            "correct-latest",
            adventure_text,
            state_text,
            "--reason",
            "The registrar had not yet arrived.",
        ),
        (
            "end-session",
            adventure_text,
            state_text,
            "--closing-note",
            "The archive route is open, but one witness remains unheard.",
        ),
        (
            "start-session",
            adventure_text,
            state_text,
            "--title",
            "Second beta table",
            "--played-on",
            "2026-07-26",
            "--participant",
            "Test GM",
            "--attendance-note",
            "The same table reconvenes.",
        ),
        ("visit", adventure_text, state_text, "the-archive-vault"),
        ("spot-clue", adventure_text, state_text, "curator-incident-memorandum"),
        (
            "foreclose-revelation",
            adventure_text,
            state_text,
            "the-glass-saint-will-not-be-olyra",
            "--reason",
            "The table temporarily accepts the false identity.",
        ),
        (
            "reopen-revelation",
            adventure_text,
            state_text,
            "the-glass-saint-will-not-be-olyra",
            "--reason",
            "The copied memorandum reopens the question.",
        ),
        (
            "unlock-encounter",
            adventure_text,
            state_text,
            "beta-annex",
            "--reason",
            "The GM adjudicates a service stair between archive rooms.",
        ),
        (
            "visit",
            adventure_text,
            state_text,
            "beta-annex",
            "--clue",
            "annex-provenance-ledger",
            "--note",
            "The party inventories the annex before leaving.",
        ),
        (
            "consequence",
            adventure_text,
            state_text,
            "beta-annex",
            "The copied witness list is now in the party's custody.",
        ),
        (
            "end-session",
            adventure_text,
            state_text,
            "--closing-note",
            "The annex evidence survives the second session.",
        ),
    )


def _exercise_authoring_workflow(command: str, adventure: Path) -> None:
    for arguments in authoring_command_arguments(adventure):
        _run(command, *arguments)


def _exercise_play_workflow(
    command: str,
    adventure: Path,
    state: Path,
    root: Path,
) -> None:
    summary = root / "Play Summary – β.md"
    for arguments in play_command_arguments(adventure, state):
        _run(command, *arguments)
    _run(command, "summary", str(adventure), str(state), "--output", str(summary))

    payload = _json_object(state)
    events = payload.get("events")
    if not isinstance(events, list):
        raise RuntimeError("Installed CLI did not persist a play-event list.")
    event_types = {event.get("type") for event in events if isinstance(event, dict)}
    required_types = {
        "session_started",
        "session_ended",
        "encounter_visited",
        "clue_spotted",
        "clue_missed",
        "revelation_established",
        "revelation_foreclosed",
        "revelation_reopened",
        "encounter_unlocked",
        "visit_note_recorded",
        "reference_note_recorded",
        "encounter_consequence_recorded",
        "operation_voided",
    }
    if payload.get("schema_version") != 6 or not required_types.issubset(event_types):
        raise RuntimeError("Installed CLI did not persist the expected multi-session workflow.")
    session_starts = [event for event in events if event.get("type") == "session_started"]
    if len(session_starts) != 2:
        raise RuntimeError("Installed CLI did not persist both explicit play sessions.")
    summary_text = summary.read_text(encoding="utf-8")
    required_summary_text = (
        "First beta table",
        "Second beta table",
        "Beta Annex Reopened",
        "Saint Olyra's name is now part of the witnesses' working theory.",
        "The annex evidence survives the second session.",
    )
    if any(fragment not in summary_text for fragment in required_summary_text):
        raise RuntimeError("Installed CLI did not render the expected multi-session summary.")


def _exercise_post_play_authoring(command: str, adventure: Path) -> None:
    _run(
        command,
        "edit-encounter",
        str(adventure),
        "beta-annex",
        "--summary",
        "A revised annex summary that preserves every recorded identifier.",
    )
    before = adventure.read_bytes()
    failure = _run_expect_failure(
        command,
        "move-clue",
        str(adventure),
        "annex-provenance-ledger",
        "the-shattered-gallery",
    )
    if "would be invalid after this change" not in failure.stderr:
        raise RuntimeError("Installed CLI did not explain the refused post-play structural edit.")
    if adventure.read_bytes() != before:
        raise RuntimeError("A refused post-play structural edit changed the authored adventure.")


def _exercise_archive_workflow(
    command: str,
    adventure: Path,
    state: Path,
    project: Path,
) -> None:
    active_before = state.read_bytes()
    _run(
        command,
        "archive",
        str(adventure),
        str(state),
        "--name",
        ARCHIVE_ID,
        "--label",
        "Installed workflow archive – café",
    )
    archive = project / "archives" / ARCHIVE_FILENAME
    if not archive.is_file():
        raise RuntimeError("Installed CLI did not create the expected journal archive.")
    archive_before = archive.read_bytes()
    active_payload = _json_object(state)
    if active_payload.get("events") != []:
        raise RuntimeError("Archiving did not replace the active journal with an empty journal.")
    listing = _run(command, "list-archives", str(project / "archives"))
    if (
        ARCHIVE_ID not in listing.stdout
        or "Installed workflow archive – café" not in listing.stdout
    ):
        raise RuntimeError("Installed CLI did not list the created archive.")

    renamed_archive = project / "archives" / "renamed-copy.journal.json"
    renamed_archive.write_bytes(archive_before)
    failure = _run_expect_failure(command, "list-archives", str(project / "archives"))
    if "does not match embedded identifier" not in failure.stderr:
        raise RuntimeError("Installed CLI accepted a renamed archive with ambiguous identity.")
    renamed_archive.unlink()

    _run(command, "restore-archive", str(adventure), str(state), str(archive))
    if state.read_bytes() != active_before:
        raise RuntimeError("Restored active journal bytes differ from the pre-archive journal.")
    if archive.read_bytes() != archive_before:
        raise RuntimeError("Restore changed the immutable archive bytes.")

    _run(
        command,
        "delete-archive",
        str(adventure),
        str(state),
        str(archive),
        "--confirm",
        ARCHIVE_ID,
    )
    if archive.exists():
        raise RuntimeError("Confirmed archive deletion did not remove the archive.")


def _exercise_malformed_file_repair(command: str, adventure: Path) -> None:
    original = adventure.read_bytes()
    payload = _json_object(adventure)
    metadata = payload.get("adventure")
    if not isinstance(metadata, dict):
        raise RuntimeError("Initialized adventure does not contain adventure metadata.")
    metadata["unsupported_beta_field"] = "must fail closed"
    adventure.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    failure = _run_expect_failure(command, "validate", str(adventure))
    if "unsupported field" not in failure.stderr.lower():
        raise RuntimeError("Malformed-file diagnostic did not identify the unsupported field.")
    adventure.write_bytes(original)
    _run(command, "validate", str(adventure))


class _FormParser(HTMLParser):
    """Collect submitted fields from ordinary HTML forms by action path."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.forms: list[tuple[str, dict[str, str]]] = []
        self._action: str | None = None
        self._fields: dict[str, str] = {}
        self._textarea_name: str | None = None
        self._textarea_parts: list[str] = []
        self._select_name: str | None = None
        self._selected_option: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "form":
            self._action = attributes.get("action", "")
            self._fields = {}
        elif self._action is not None and tag == "input":
            self._capture_input(attributes)
        elif self._action is not None and tag == "textarea":
            self._textarea_name = attributes.get("name")
            self._textarea_parts = []
        elif self._action is not None and tag == "select":
            self._select_name = attributes.get("name")
            self._selected_option = None
        elif self._select_name is not None and tag == "option":
            if "selected" in attributes:
                self._selected_option = attributes.get("value", "")

    def handle_data(self, data: str) -> None:
        if self._textarea_name is not None:
            self._textarea_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "textarea" and self._textarea_name is not None:
            self._fields[self._textarea_name] = "".join(self._textarea_parts)
            self._textarea_name = None
            self._textarea_parts = []
        elif tag == "select" and self._select_name is not None:
            self._fields[self._select_name] = self._selected_option or ""
            self._select_name = None
            self._selected_option = None
        elif tag == "form" and self._action is not None:
            self.forms.append((self._action, dict(self._fields)))
            self._action = None
            self._fields = {}

    def _capture_input(self, attributes: dict[str, str | None]) -> None:
        name = attributes.get("name")
        if not name or "disabled" in attributes:
            return
        input_type = attributes.get("type", "text")
        if input_type in {"checkbox", "radio"} and "checked" not in attributes:
            return
        self._fields[name] = attributes.get("value", "") or ""


def _form_fields(page: str, action: str) -> dict[str, str]:
    parser = _FormParser()
    parser.feed(page)
    matches = [fields for form_action, fields in parser.forms if form_action == action]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one browser form for {action!r}, found {len(matches)}.")
    return matches[0]


class _BrowserClient:
    """Small standard-library browser used by the installed-wheel audit."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.opener = urllib.request.build_opener()

    def get(self, path: str) -> tuple[int, str, str]:
        request = urllib.request.Request(self.base_url + path, method="GET")
        return self._open(request)

    def submit(
        self,
        page: str,
        action: str,
        overrides: dict[str, str | None] | None = None,
    ) -> tuple[int, str, str]:
        fields = _form_fields(page, action)
        for name, value in (overrides or {}).items():
            if value is None:
                fields.pop(name, None)
            else:
                fields[name] = value
        return self.post_form(action, fields)

    def post_form(self, action: str, fields: dict[str, str]) -> tuple[int, str, str]:
        """Submit already-resolved URL-encoded fields to one action."""
        request = urllib.request.Request(
            self.base_url + action,
            data=urllib.parse.urlencode(fields).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return self._open(request)

    def upload(
        self,
        page: str,
        action: str,
        *,
        file_field: str,
        filename: str,
        content: bytes,
    ) -> tuple[int, str, str]:
        """Submit one JSON file through a browser multipart form."""
        fields = _form_fields(page, action)
        fields.pop(file_field, None)
        boundary = f"adventure-graph-beta-{os.urandom(12).hex()}"
        chunks: list[bytes] = []
        for name, value in fields.items():
            chunks.extend(
                (
                    f"--{boundary}\r\n".encode("ascii"),
                    f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(
                        "ascii"
                    ),
                    value.encode("utf-8"),
                    b"\r\n",
                )
            )
        chunks.extend(
            (
                f"--{boundary}\r\n".encode("ascii"),
                (
                    f'Content-Disposition: form-data; name="{file_field}"; '
                    f'filename="{filename}"\r\n'
                ).encode("ascii"),
                b"Content-Type: application/json\r\n\r\n",
                content,
                b"\r\n",
                f"--{boundary}--\r\n".encode("ascii"),
            )
        )
        request = urllib.request.Request(
            self.base_url + action,
            data=b"".join(chunks),
            method="POST",
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        return self._open(request)

    def _open(self, request: urllib.request.Request) -> tuple[int, str, str]:
        try:
            with self.opener.open(  # noqa: S310 -- generated loopback URL.
                request, timeout=2
            ) as response:
                return (
                    response.status,
                    response.geturl(),
                    response.read().decode("utf-8"),
                )
        except urllib.error.HTTPError as error:
            return error.code, error.geturl(), error.read().decode("utf-8")


def _exercise_browser_workflow(
    command: str,
    adventure: Path,
    state: Path,
    project: Path,
) -> None:
    before_browser = state.read_bytes()
    with _running_ui(command, adventure) as base_url:
        client = _BrowserClient(base_url)
        _exercise_browser_authoring(client, adventure)
        _exercise_browser_play(client, state)
        _exercise_browser_archives(client, state, project)

    payload = _json_object(state)
    events = payload.get("events")
    if not isinstance(events, list):
        raise RuntimeError("Browser workflow did not preserve a play-event list.")
    event_types = [event.get("type") for event in events if isinstance(event, dict)]
    if event_types.count("session_started") < 3 or event_types.count("session_ended") < 3:
        raise RuntimeError("Browser workflow did not persist its explicit play session.")
    dice_events = [
        event
        for event in events
        if isinstance(event, dict) and event.get("type") == "dice_roll_recorded"
    ]
    if not dice_events or dice_events[-1].get("label") != "Browser dice audit":
        raise RuntimeError("Browser workflow did not persist the exact rolled dice result.")
    reference_notes = [
        event
        for event in events
        if isinstance(event, dict) and event.get("type") == "reference_note_recorded"
    ]
    if not reference_notes or reference_notes[-1].get("text") != (
        "The browser audit records Olyra as a contested identity."
    ):
        raise RuntimeError("Browser workflow did not persist the selected-reference note.")
    if state.read_bytes() == before_browser:
        raise RuntimeError("Browser workflow completed without changing the active journal.")


def _exercise_browser_authoring(client: _BrowserClient, adventure: Path) -> None:
    status, _, page = client.get("/encounters/new")
    if status != 200:
        raise RuntimeError("Installed browser did not open the encounter creation form.")
    status, _, page = client.submit(
        page,
        "/encounters/new",
        {
            "title": "Browser Created Gallery",
            "summary": "An encounter created entirely through the installed browser.",
            "opening_view": "A gallery of sealed maps waits behind clear glass.",
            "content": (
                "## Browser-created encounter\n\n"
                "This material crossed the live HTTP boundary."
            ),
            "tags": "browser-created",
            "required": None,
            "end": "1",
        },
    )
    if status != 200 or "Encounter created" not in page:
        raise RuntimeError("Installed browser did not create a new encounter.")
    created = next(
        (
            item
            for item in _json_object(adventure).get("encounters", [])
            if isinstance(item, dict) and item.get("id") == "browser-created-gallery"
        ),
        None,
    )
    if created is None or created.get("summary") != (
        "An encounter created entirely through the installed browser."
    ):
        raise RuntimeError("Browser encounter creation did not reach canonical persistence.")

    status, _, page = client.get("/encounters/beta-annex/edit")
    if status != 200:
        raise RuntimeError("Installed browser did not open the authored encounter editor.")
    status, _, page = client.submit(
        page,
        "/encounters/beta-annex/edit",
        {
            "opening_view": "A browser-tested catalog lamp burns beneath the cracked blue window.",
            "content": "## Browser verification\n\nThe annex remains writable after recorded play.",
        },
    )
    if status != 200 or "Encounter saved" not in page:
        raise RuntimeError("Installed browser did not save the post-play presentation edit.")
    encounter = next(
        item
        for item in _json_object(adventure).get("encounters", [])
        if isinstance(item, dict) and item.get("id") == "beta-annex"
    )
    if encounter.get("opening_view") != (
        "A browser-tested catalog lamp burns beneath the cracked blue window."
    ):
        raise RuntimeError("Browser encounter edit did not reach canonical persistence.")


def _exercise_browser_play(client: _BrowserClient, state: Path) -> None:
    status, _, page = client.get("/play")
    if status != 200 or "Beta Annex Reopened" not in page:
        raise RuntimeError("Installed browser did not open the authored play workspace.")

    status, _, page = client.submit(
        page,
        "/play/session/start",
        {
            "title": "Browser verification session",
            "played_on": "2026-07-27",
            "participants": "Browser GM, Browser Player",
            "attendance_note": "The installed browser path is under audit.",
            "opening_note": "The table resumes at the annex.",
        },
    )
    if status != 200 or "Session begun" not in page:
        raise RuntimeError("Installed browser did not start an explicit play session.")

    status, _, page = client.submit(
        page,
        "/play/note",
        {"text": "The browser audit preserves this encounter note."},
    )
    if status != 200 or "Encounter note committed" not in page:
        raise RuntimeError("Installed browser did not record the encounter note.")

    status, _, page = client.get(
        f"/play?encounter=beta-annex&reference={AUDIT_REFERENCE_ID}"
    )
    if status != 200 or "Save reference note" not in page:
        raise RuntimeError("Installed browser did not open the reference-note form.")
    status, _, page = client.submit(
        page,
        "/play/reference/note",
        {"text": "The browser audit records Olyra as a contested identity."},
    )
    if status != 200 or "Reference note committed" not in page:
        raise RuntimeError("Installed browser did not record the selected-reference note.")

    before_roll = state.read_bytes()
    status, _, rolled_page = client.submit(
        page,
        "/play/dice/roll",
        {"expression": "2d8 - 1", "label": "Browser dice audit"},
    )
    if status != 200 or 'data-expression="2d8 - 1"' not in rolled_page:
        raise RuntimeError("Installed browser did not render the requested dice roll.")
    if state.read_bytes() != before_roll:
        raise RuntimeError("Ephemeral browser dice roll changed the canonical journal.")

    status, _, page = client.submit(rolled_page, "/play/dice/record")
    if status != 200 or "Dice roll recorded" not in page:
        raise RuntimeError("Installed browser did not record the exact displayed dice result.")

    status, _, page = client.submit(
        page,
        "/play/session/end",
        {"closing_note": "The installed browser path completed successfully."},
    )
    if status != 200 or "Session ended" not in page:
        raise RuntimeError("Installed browser did not end the explicit play session.")


def _exercise_browser_archives(
    client: _BrowserClient,
    state: Path,
    project: Path,
) -> None:
    active_before = state.read_bytes()
    status, _, page = client.get("/archives")
    if status != 200 or "Current playthrough" not in page:
        raise RuntimeError("Installed browser did not open the archive catalog.")

    export_fields = _form_fields(page, "/archives/create")
    export_fields.update({"label": "Portable browser export", "name": "browser-export"})
    status, _, exported = client.post_form("/archives/export-active", export_fields)
    if status != 200 or '"id": "browser-export"' not in exported:
        raise RuntimeError(
            f"Installed browser did not export the active playthrough: "
            f"status={status}, body={exported[:500]!r}."
        )
    if state.read_bytes() != active_before:
        raise RuntimeError("Exporting the active playthrough changed the canonical journal.")
    imported_archive = project / "archives" / "browser-export.journal.json"
    if imported_archive.exists():
        raise RuntimeError("Exporting the active playthrough unexpectedly created a local archive.")

    status, _, page = client.get("/archives")
    status, _, page = client.upload(
        page,
        "/archives/import",
        file_field="archive_file",
        filename="browser-export.journal.json",
        content=exported.encode("utf-8"),
    )
    if status != 200 or "Playthrough imported" not in page:
        raise RuntimeError("Installed browser did not import the portable playthrough.")
    if imported_archive.read_text(encoding="utf-8") != exported:
        raise RuntimeError("Imported playthrough bytes differ from the browser export.")
    status, _, downloaded = client.get("/archives/browser-export/download")
    if status != 200 or downloaded != exported:
        raise RuntimeError("Installed browser did not re-export the stored playthrough exactly.")

    status, _, page = client.get("/archives")
    status, _, page = client.submit(
        page,
        "/archives/create",
        {"label": "Browser workflow archive – café", "name": "browser-workflow"},
    )
    if status != 200 or "Journal archived" not in page:
        raise RuntimeError("Installed browser did not archive and reset the active journal.")

    archive = project / "archives" / "browser-workflow.journal.json"
    if not archive.is_file():
        raise RuntimeError("Installed browser did not create the expected archive file.")
    archive_before = archive.read_bytes()
    if _json_object(state).get("events") != []:
        raise RuntimeError("Browser archive did not reset the active journal.")

    status, _, detail = client.get("/archives/browser-workflow")
    if (
        status != 200
        or "Adventure snapshot comparison" not in detail
        or "Compatible with current adventure" not in detail
    ):
        raise RuntimeError("Installed browser did not inspect the created archive.")
    status, _, page = client.submit(detail, "/archives/browser-workflow/restore")
    if status != 200 or "Archive restored" not in page:
        raise RuntimeError("Installed browser did not restore the immutable archive.")
    if state.read_bytes() != active_before or archive.read_bytes() != archive_before:
        raise RuntimeError("Browser restore did not preserve active and archive bytes exactly.")

    status, _, detail = client.get("/archives/browser-workflow")
    if status != 200:
        raise RuntimeError("Installed browser could not reopen the restored archive detail.")
    refused_status, _, refused_page = client.submit(
        detail,
        "/archives/browser-workflow/delete",
        {"confirmation": "wrong"},
    )
    if refused_status != 422 or "confirmation must exactly match" not in refused_page:
        raise RuntimeError("Installed browser did not enforce exact archive deletion confirmation.")
    if not archive.is_file():
        raise RuntimeError("Refused browser archive deletion removed the archive.")

    status, _, detail = client.get("/archives/browser-workflow")
    if status != 200:
        raise RuntimeError("Installed browser could not refresh archive deletion controls.")
    status, _, page = client.submit(
        detail,
        "/archives/browser-workflow/delete",
        {"confirmation": "browser-workflow"},
    )
    if status != 200 or "Archive deleted" not in page or archive.exists():
        raise RuntimeError("Installed browser did not permanently delete the confirmed archive.")


def _exercise_copy_rename_and_reopen(command: str, project: Path, root: Path) -> None:
    copied_workspace = root / AUDIT_COPY_WORKSPACE_NAME
    copied_project = copied_workspace / AUDIT_COPY_PROJECT_NAME
    shutil.copytree(project, copied_project)
    renamed_project = copied_workspace / AUDIT_RENAMED_PROJECT_NAME
    copied_project.rename(renamed_project)
    copied_adventure = renamed_project / "adventure.json"
    copied_state = renamed_project / "play-state.json"
    _run(command, "validate", str(copied_adventure))
    _run(command, "summary", str(copied_adventure), str(copied_state))
    _launch_and_probe(
        command,
        copied_adventure,
        page_path="/encounters/beta-annex",
        expected_text="The annex remains writable after recorded play.",
    )


def _json_object(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected a JSON object in {path}.")
    return payload


def _environment_executable(environment: Path, name: str) -> str:
    scripts = environment / ("Scripts" if os.name == "nt" else "bin")
    suffix = ".exe" if os.name == "nt" else ""
    return str(scripts / f"{name}{suffix}")


def _run(*command: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        rendered = " ".join(command)
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {rendered}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def _run_with_environment(
    environment: dict[str, str],
    *command: str,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=environment,
    )
    if result.returncode != 0:
        rendered = " ".join(command)
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: {rendered}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def _run_expect_failure(*command: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode == 0:
        raise RuntimeError(f"Command unexpectedly succeeded: {command!r}")
    return result


def _launch_and_probe(
    command: str,
    target: Path,
    *,
    page_path: str,
    expected_text: str,
) -> None:
    with _running_ui(command, target) as base_url:
        with urllib.request.urlopen(  # noqa: S310 -- generated loopback URL.
            base_url + page_path, timeout=0.5
        ) as response:
            page = response.read().decode("utf-8")
            if response.status != 200 or expected_text not in page:
                raise RuntimeError("Installed UI did not expose the expected persisted content.")


class _RunningUI:
    """Context manager for one installed loopback UI process."""

    def __init__(self, command: str, target: Path) -> None:
        self.command = command
        self.target = target
        self.process: subprocess.Popen[str] | None = None
        self.base_url = ""

    def __enter__(self) -> str:
        port = _available_loopback_port()
        self.base_url = f"http://127.0.0.1:{port}"
        self.process = subprocess.Popen(
            [
                self.command,
                "ui",
                str(self.target),
                "--port",
                str(port),
                "--no-browser",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                raise RuntimeError(
                    f"Installed UI exited before startup. stdout={stdout!r} stderr={stderr!r}"
                )
            try:
                with urllib.request.urlopen(  # noqa: S310 -- generated loopback URL.
                    self.base_url + "/healthz",
                    timeout=0.5,
                ) as response:
                    if response.status == 200 and response.read() == b"ok\n":
                        return self.base_url
            except (OSError, urllib.error.URLError):
                time.sleep(0.05)
        self.__exit__(None, None, None)
        raise RuntimeError("Installed UI did not expose its loopback health endpoint.")

    def __exit__(self, *_: object) -> None:
        if self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)


def _running_ui(command: str, target: Path) -> _RunningUI:
    return _RunningUI(command, target)


def _available_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


if __name__ == "__main__":
    raise SystemExit(main())
