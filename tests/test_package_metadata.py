"""Baseline package metadata and documentation tests."""

from __future__ import annotations

import json
import re
import tomllib
from uuid import UUID

from adventure_graph import __version__
from tests.support.paths import PROJECT_ROOT

_SEMVER_PATTERN = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def test_package_version_matches_pyproject_metadata() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert __version__ in {pyproject["project"]["version"], "0.0.0+unknown"}


def test_project_version_uses_plain_semantic_versioning() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    version = pyproject["project"]["version"]

    assert isinstance(version, str)
    assert _SEMVER_PATTERN.fullmatch(version) is not None


def test_required_documentation_stubs_exist() -> None:
    required_paths = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "docs" / "architecture.md",
        PROJECT_ROOT / "docs" / "standards.md",
        PROJECT_ROOT / "docs" / "beta-guide.md",
        PROJECT_ROOT / "docs" / "desktop-distribution.md",
        PROJECT_ROOT / "docs" / "adventure-reference-library-roadmap.md",
        PROJECT_ROOT / "docs" / "post-reference-defragmentation-beta-maintenance-triage.md",
        PROJECT_ROOT / "docs" / "test-strategy.md",
        PROJECT_ROOT / "docs" / "README.md",
        PROJECT_ROOT / "docs" / "cli-reference.md",
        PROJECT_ROOT / "docs" / "maintainer-guide.md",
    ]

    missing_paths = [path for path in required_paths if not path.is_file()]

    assert missing_paths == []


def test_test_strategy_keeps_policy_separate_from_revision_evidence() -> None:
    strategy = (PROJECT_ROOT / "docs" / "test-strategy.md").read_text(encoding="utf-8")
    qualification = (
        PROJECT_ROOT / "docs" / "private-beta-release-qualification.md"
    ).read_text(encoding="utf-8")

    assert "## Revision-specific evidence" in strategy
    assert "private-beta-release-qualification.md" in strategy
    assert "## Current baseline" not in strategy
    for stale_claim in [
        "1,163 deterministic tests",
        "280 corpus contracts",
        "91% branch-aware coverage",
        "five mandatory browser workflows",
    ]:
        assert stale_claim not in strategy
    normalized_qualification = " ".join(qualification.replace(">", " ").split())
    assert "Historical evidence record" in normalized_qualification
    assert (
        "must not be read as evidence for a descendant source tree"
        in normalized_qualification
    )


def test_ui_architecture_records_the_completed_application_seam() -> None:
    architecture = (PROJECT_ROOT / "docs" / "ui-architecture.md").read_text(encoding="utf-8")

    assert "## Current application seam" in architecture
    assert "The formerly planned orchestration extraction is complete." in architecture
    assert "`bootstrap.py` is now a deliberately small" in architecture
    assert "`bootstrap.py` is the current pressure point" not in architecture
    assert "Presentation copy must use Lead/Leads" in architecture


def test_make_clean_uses_the_tested_portable_cleanup_script() -> None:
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    clean_target = makefile.split("\nclean:\n", maxsplit=1)[1].split("\n\n", maxsplit=1)[0]

    assert "$(PYTHON) scripts/clean_repository.py" in clean_target
    assert "rm -rf" not in clean_target


def test_maintainer_guide_documents_primary_make_targets() -> None:
    guide = (PROJECT_ROOT / "docs" / "maintainer-guide.md").read_text(encoding="utf-8")

    for target in [
        "make install",
        "make test",
        "make lint",
        "make format",
        "make format-check",
        "make validate",
        "make validate-all",
    ]:
        assert target in guide


def test_cli_reference_maps_every_cli_command() -> None:
    cli_reference = (PROJECT_ROOT / "docs" / "cli-reference.md").read_text(
        encoding="utf-8"
    )
    commands = {
        "init",
        "ui",
        "validate",
        "render",
        "summary",
        "list",
        "inspect",
        "add-encounter",
        "add-reference",
        "add-revelation",
        "add-clue",
        "edit-encounter",
        "edit-reference",
        "edit-revelation",
        "edit-clue",
        "move-clue",
        "link-reference",
        "unlink-reference",
        "remove-encounter",
        "remove-reference",
        "remove-revelation",
        "remove-clue",
        "start-session",
        "end-session",
        "archive",
        "list-archives",
        "restore-archive",
        "delete-archive",
        "visit",
        "spot-clue",
        "miss-clue",
        "establish-revelation",
        "foreclose-revelation",
        "reopen-revelation",
        "unlock-encounter",
        "consequence",
        "note",
        "correct-latest",
    }

    missing = sorted(
        command for command in commands if f"`{command}`" not in cli_reference
    )

    assert missing == []


def test_documentation_routes_operating_detail_to_owned_guides() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    cli_reference = (PROJECT_ROOT / "docs" / "cli-reference.md").read_text(encoding="utf-8")
    maintainer_guide = (PROJECT_ROOT / "docs" / "maintainer-guide.md").read_text(
        encoding="utf-8"
    )

    for required in [
        "adventure-graph --help",
        "adventure-graph <command> --help",
        "summary adventure.json play-state.json \\",
        "--output generated/05-play-summary.md",
        "## Authoring workflow",
        "## GM workflow",
        "### Before a session",
        "### During a session",
        "### After a session",
        "authoring-lifecycle.md",
        "runtime-state.md",
        "journal-archives.md",
        "validation-diagnostics.md",
        "file-format.md",
        "architecture.md",
    ]:
        assert required in cli_reference

    for required in [
        "## Desktop launcher and exporting native bundles",
        "gh workflow run desktop.yml",
        "gh run list --workflow desktop.yml --limit 5",
        "--require-platforms linux windows macos",
        "desktop-distribution.md",
        "test-strategy.md",
    ]:
        assert required in maintainer_guide
    assert '--branch "$BRANCH"' not in maintainer_guide

    for required in [
        "docs/README.md",
        "docs/cli-reference.md",
        "docs/maintainer-guide.md",
        "docs/beta-guide.md",
        "docs/ui-usage.md",
    ]:
        assert required in readme


def test_readme_uses_the_beta_pip_installation_contract() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "python -m pip install -e ." in readme
    assert "adventure-graph ui adventure-workspace" in readme
    assert "poetry run adventure-graph" not in readme


def test_beta_roadmap_preserves_the_lightweight_desktop_distribution_contract() -> None:
    roadmap = (PROJECT_ROOT / "docs" / "beta-readiness-roadmap.md").read_text(encoding="utf-8")

    required_text = [
        "## Adventure reference library — accepted for beta, headless lifecycle complete",
        "## Tester-facing UI cleanup and onboarding — locally complete",
        "split-party labels",
        "off-script",
        "Help/Introduction page",
        "## One-click desktop distribution — pipeline implemented, platform signoff open",
        "This is a distribution task, not a second product",
        "operating system directory",
        "PyInstaller one-folder",
        "frozen executable",
        "SHA-256 manifest",
        "do not introduce Electron",
        "target a compressed artifact below 100 MiB per platform",
        "approaching 1 GiB is a failed",
        "testers are not expected to work through the command line",
    ]

    missing = [item for item in required_text if item not in roadmap]

    assert missing == []


def test_campaign_graph_roadmap_preserves_clue_oriented_portability_contract() -> None:
    roadmap = (PROJECT_ROOT / "docs" / "campaign-graph-roadmap.md").read_text(encoding="utf-8")
    architecture = (PROJECT_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    beta_roadmap = (PROJECT_ROOT / "docs" / "beta-readiness-roadmap.md").read_text(encoding="utf-8")
    docs_index = (PROJECT_ROOT / "docs" / "README.md").read_text(encoding="utf-8")

    required_text = [
        "campaign clue list",
        "campaign revelation list",
        "Campaign connectivity is therefore derived from authored clues and revelations",
        "campaign-entry ID",
        "copy semantics",
        "clean standalone adventure",
        "campaign companion metadata",
        "encounter placement",
        (
            "This is a downward operational placement, not a conversion into an ordinary "
            "adventure clue"
        ),
        "No new revelation kind is required",
        "typed effects or targets",
        "adventure entry-point",
        "Detailed encounter visits",
        "Phase 0 — learn from the adventure beta",
        "implementation follows the first adventure beta",
        "Persistent campaign entities and adventure compatibility",
        "explicit campaign-owned bindings",
        "Absolute campaign chronology and calendar projections",
        "campaign-entry ID plus encounter ID",
        "Authored chronology and runtime history remain separate",
    ]
    missing = [item for item in required_text if item not in roadmap]

    assert missing == []
    assert "campaign-graph-roadmap.md" in architecture
    assert (
        "## Post-beta campaign graph initiative — documented, implementation deferred"
        in beta_roadmap
    )
    assert "campaign-graph-roadmap.md" in docs_index


def test_adventure_reference_library_roadmap_preserves_accepted_beta_scope() -> None:
    roadmap = (PROJECT_ROOT / "docs" / "adventure-reference-library-roadmap.md").read_text(
        encoding="utf-8"
    )
    beta_roadmap = (PROJECT_ROOT / "docs" / "beta-readiness-roadmap.md").read_text(encoding="utf-8")
    architecture = (PROJECT_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    docs_index = (PROJECT_ROOT / "docs" / "README.md").read_text(encoding="utf-8")

    required_text = [
        "accepted pre-beta product direction",
        "operational, clue-bearing units",
        "reference record",
        "explicit links between encounters",
        "generated backlinks",
        "Play-time access",
        "generated adventure-packet output",
        "an untyped universal node replacing encounters",
        "Representative fixtures",
        "Phase 1 — fixture and schema design",
        "Phase 7 — beta convergence",
        "should not begin external beta testing",
    ]
    missing = [item for item in required_text if item not in roadmap]

    assert missing == []
    assert "Adventure reference library — accepted for beta" in beta_roadmap
    assert "adventure-reference-library-roadmap.md" in architecture
    assert "adventure-reference-library-roadmap.md" in docs_index


def test_reference_library_phase_one_decision_is_fixture_backed() -> None:
    fixture_path = PROJECT_ROOT / "docs" / "adventure-reference-library-phase-1-fixtures.json"
    design_path = PROJECT_ROOT / "docs" / "adventure-reference-library-phase-1-design.md"
    roadmap_path = PROJECT_ROOT / "docs" / "adventure-reference-library-roadmap.md"

    assert fixture_path.is_file()
    assert design_path.is_file()

    fixture_document = json.loads(fixture_path.read_text(encoding="utf-8"))
    contract = fixture_document["candidate_contract"]
    fixtures = {fixture["id"]: fixture for fixture in fixture_document["fixtures"]}

    assert contract["reference_kinds"] == [
        "person",
        "place",
        "organization",
        "object",
        "other",
    ]
    assert contract["encounter_link_field"] == "reference_links"
    assert contract["link_fields"] == ["reference_id", "context"]
    assert set(fixtures) == {
        "recurring-person-cora-pike",
        "shared-place-blackbriar-estate",
        "distributed-organization-saint-mercy",
        "recurring-object-bronze-seal",
        "reference-light-existing-adventure",
        "portable-project-and-archive",
        "dependency-aware-removal",
    }

    reference_ids: set[str] = set()
    for fixture in fixtures.values():
        reference = fixture.get("reference")
        if reference is None:
            continue
        reference_id = reference["id"]
        parsed = UUID(reference_id)
        assert parsed.version == 4
        assert str(parsed) == reference_id
        assert reference_id not in reference_ids
        reference_ids.add(reference_id)

        source_path = PROJECT_ROOT / fixture["source_adventure"]
        source = json.loads(source_path.read_text(encoding="utf-8"))
        encounter_ids = {encounter["id"] for encounter in source["encounters"]}
        links = fixture["links"]
        assert links
        assert len({link["encounter_id"] for link in links}) == len(links)
        assert {link["encounter_id"] for link in links}.issubset(encounter_ids)

    recurring_person = fixtures["recurring-person-cora-pike"]
    archive_path = PROJECT_ROOT / recurring_person["runtime_evidence"]["archive"]
    archive = json.loads(archive_path.read_text(encoding="utf-8"))
    event_sequences = {event["sequence"] for event in archive["play_state"]["events"]}
    assert set(recurring_person["runtime_evidence"]["event_sequences"]).issubset(event_sequences)
    assert len(recurring_person["links"]) == 4
    assert len(fixtures["shared-place-blackbriar-estate"]["links"]) == 3
    assert len(fixtures["distributed-organization-saint-mercy"]["links"]) >= 4
    assert len(fixtures["recurring-object-bronze-seal"]["links"]) >= 4
    assert fixtures["reference-light-existing-adventure"]["references"] == []

    design = design_path.read_text(encoding="utf-8")
    roadmap = roadmap_path.read_text(encoding="utf-8")
    architecture = (PROJECT_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    file_format = (PROJECT_ROOT / "docs" / "file-format.md").read_text(encoding="utf-8")
    lifecycle = (PROJECT_ROOT / "docs" / "authoring-lifecycle.md").read_text(encoding="utf-8")

    normalized_design = " ".join(design.split())
    for required in [
        "subordinate link records on encounters",
        "canonical UUIDv4 text",
        "Adventure source remains schema version 3",
        "Journal archive schema version 1 also remains unchanged",
        "Removing a linked reference without explicit cascade is refused",
    ]:
        assert required in normalized_design
    assert "## Accepted Phase 1 decisions" in roadmap
    assert "Phase 1 — fixture and schema design — complete" in roadmap
    assert "Encounters own ordered subordinate link records" in architecture
    assert "Reference-library extension (headless implementation complete)" in file_format
    assert "Cascading a reference removes the record" in " ".join(lifecycle.split())


def test_reference_library_phase_two_headless_contract_is_documented() -> None:
    roadmap = (PROJECT_ROOT / "docs" / "adventure-reference-library-roadmap.md").read_text(
        encoding="utf-8"
    )
    file_format = (PROJECT_ROOT / "docs" / "file-format.md").read_text(encoding="utf-8")
    architecture = (PROJECT_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")

    assert "Phase 2 — domain, schema, and persistence — complete" in roadmap
    assert "Archive snapshots preserve the complete shape" in roadmap
    assert "Reference-library extension (headless implementation complete)" in file_format
    assert "Encounters own ordered subordinate link records" in architecture
    assert "Reference associations do not create graph connectivity" in architecture


def test_reference_library_phase_three_headless_lifecycle_is_documented() -> None:
    roadmap = (PROJECT_ROOT / "docs" / "adventure-reference-library-roadmap.md").read_text(
        encoding="utf-8"
    )
    lifecycle = (PROJECT_ROOT / "docs" / "authoring-lifecycle.md").read_text(encoding="utf-8")
    architecture = (PROJECT_ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
    beta_roadmap = (PROJECT_ROOT / "docs" / "beta-readiness-roadmap.md").read_text(encoding="utf-8")

    assert "Phase 3 — application operations and CLI recovery surface — complete" in roadmap
    assert "complete authored lifecycle is exercised without the browser" in roadmap
    for command in [
        "add-reference",
        "edit-reference",
        "link-reference",
        "unlink-reference",
        "remove-reference",
        "inspect --state PATH",
    ]:
        assert command in lifecycle
    assert "Revision-aware application commands own reference creation" in architecture
    assert "headless lifecycle complete" in beta_roadmap
    assert "Phase 4 — Author interface — complete" in roadmap


def test_reference_library_phase_five_play_and_packet_contract_is_documented() -> None:
    roadmap = (PROJECT_ROOT / "docs" / "adventure-reference-library-roadmap.md").read_text(
        encoding="utf-8"
    )
    ui_architecture = (PROJECT_ROOT / "docs" / "ui-architecture.md").read_text(encoding="utf-8")
    ui_usage = (PROJECT_ROOT / "docs" / "ui-usage.md").read_text(encoding="utf-8")
    play_semantics = (PROJECT_ROOT / "docs" / "play-mode-semantics.md").read_text(encoding="utf-8")

    normalized_roadmap = " ".join(roadmap.split())
    normalized_ui_architecture = " ".join(ui_architecture.split())
    normalized_ui_usage = " ".join(ui_usage.split())
    normalized_play_semantics = " ".join(play_semantics.split())
    for required in [
        "Phase 5 — Play and generated packet integration — complete",
        "typed encounter or reference bookmarks",
        "references/index.md",
        "stable UUID-named sheet",
        "appends no visit, operation, or other journal event",
    ]:
        assert required in normalized_roadmap
    for required in [
        "independently selected reference",
        "typed pins",
        "Reference-library Play retrieval and generated packets — complete",
        "stable packet paths",
    ]:
        assert required in normalized_ui_architecture
    for required in [
        "typed encounter/reference bookmarks",
        "Open full reference",
        "UUID-named reference sheets",
        "reference-light adventure omits the reference namespace",
    ]:
        assert required in normalized_ui_usage
    for required in [
        "Read-only authored references",
        "typed encounter and reference pins",
        "creates no visit, clue outcome, note, consequence, or generic runtime event",
    ]:
        assert required in normalized_play_semantics
    assert "Phase 6 — corpus pass and usability audit — complete" in normalized_roadmap


def test_reference_library_phase_six_corpus_contract_is_documented() -> None:
    roadmap = (PROJECT_ROOT / "docs" / "adventure-reference-library-roadmap.md").read_text(
        encoding="utf-8"
    )
    audit = (
        PROJECT_ROOT / "docs" / "adventure-reference-library-phase-6-corpus-audit.md"
    ).read_text(encoding="utf-8")
    ui_usage = (PROJECT_ROOT / "docs" / "ui-usage.md").read_text(encoding="utf-8")
    cold_read_path = PROJECT_ROOT / "docs" / "adventure-reference-library-phase-7-cold-read.md"

    normalized_roadmap = " ".join(roadmap.split())
    normalized_audit = " ".join(audit.split())
    normalized_usage = " ".join(ui_usage.split())
    for required in [
        "Phase 6 — corpus pass and usability audit — complete",
        "Theron Eiral",
        "The Sunseed",
        "The Salt Wardens",
        "When the Swine Kneel",
        "reference-light",
    ]:
        assert required in normalized_roadmap
    for required in [
        "Retained records",
        "Considered, rejected, or deferred records",
        "Deferred in Phase 6; later retained",
        "existing operational ledger remains the stronger view",
        "clean standalone export",
        "journal archive snapshot",
        "introduces no schema, journal, campaign, or calendar expansion",
    ]:
        assert required in normalized_audit
    for required in [
        "stable information is otherwise fragmented",
        "Keep scene action, leads, sensory prose, and changing state in encounters",
        "specialized ledgers",
    ]:
        assert required in normalized_usage
    assert cold_read_path.is_file()
    assert "Phase 7 — beta convergence" in normalized_roadmap


def test_reference_library_phase_seven_local_convergence_contract_is_documented() -> None:
    roadmap = (PROJECT_ROOT / "docs" / "adventure-reference-library-roadmap.md").read_text(
        encoding="utf-8"
    )
    beta_roadmap = (PROJECT_ROOT / "docs" / "beta-readiness-roadmap.md").read_text(encoding="utf-8")
    cold_read_path = PROJECT_ROOT / "docs" / "adventure-reference-library-phase-7-cold-read.md"
    desktop_guide = (PROJECT_ROOT / "docs" / "desktop-distribution.md").read_text(encoding="utf-8")
    manual_protocol = (PROJECT_ROOT / "docs" / "beta-platform-manual-protocol.md").read_text(
        encoding="utf-8"
    )

    normalized_roadmap = " ".join(roadmap.split())
    normalized_beta = " ".join(beta_roadmap.split())
    assert cold_read_path.is_file()
    cold_read = " ".join(cold_read_path.read_text(encoding="utf-8").split())

    for required in [
        "Phase 7 — beta convergence",
        "**Local status:** complete; native platform signoff remains open",
        "tablet-width top-bar overflow",
        "accepted beta source and clean wheel",
    ]:
        assert required in normalized_roadmap
    for required in [
        "The broader source corpus may continue evolving independently",
        "whole-application local GM cold-read",
        "packaged *Glass Saint* template changes",
        "Native Linux, Windows, and macOS artifacts",
    ]:
        assert required in normalized_beta
    for required in [
        "F-01 — Author top-bar overflow at tablet width — resolved",
        "byte-for-byte unchanged",
        "clean installed-wheel audit",
        "no native bundle was built locally",
        "no artifact manifest was fabricated",
    ]:
        assert required in cold_read
    assert "Recommended multi-platform export from WSL" in desktop_guide
    assert "same source revision" in desktop_guide
    assert "exact build dependency map and requirements digest" in manual_protocol


def test_graph_scale_design_notebook_keeps_campaign_recommendations_provisional() -> None:
    notebook = (PROJECT_ROOT / "docs" / "graph-scale-design-notebook.md").read_text(
        encoding="utf-8"
    )
    roadmap = (PROJECT_ROOT / "docs" / "campaign-graph-roadmap.md").read_text(encoding="utf-8")
    docs_index = (PROJECT_ROOT / "docs" / "README.md").read_text(encoding="utf-8")

    required_text = [
        "active notebook, not an accepted campaign contract",
        "one campaign clue supporting one campaign revelation",
        "Separate authored revelation effects from runtime entry status",
        "campaign-owned outcomes",
        "coordinated recoverable transaction",
        "stable campaign-entry ID separate",
        "canonical campaign structure as sources to clues",
        "Are encounter-only graph nodes too narrow?",
        "Accepted product direction",
        "Preserve the encounter graph as the operational clue-bearing layer",
        "reference library",
        "operational versus referential",
        "append-only runtime history rather than silently rewriting authored dossiers",
        "Reference-library implementation details still unresolved",
        "How should persistent campaign entities relate to adventure references?",
        "How should an absolute campaign calendar index encounters and world events?",
        "integer day index",
    ]
    missing = [item for item in required_text if item not in notebook]

    assert missing == []
    assert "graph-scale-design-notebook.md" in roadmap
    assert "not accepted campaign contracts" in roadmap
    assert "adventure-reference-library-roadmap.md" in notebook
    assert "graph-scale-design-notebook.md" in docs_index


def test_beta_guide_keeps_raw_browser_transport_internal() -> None:
    guide = (PROJECT_ROOT / "docs" / "beta-guide.md").read_text(encoding="utf-8")

    assert "documented user-visible loopback browser workflows" in guide
    assert "Raw HTTP paths, hidden form fields" in guide
    assert "Use the CLI and published JSON schemas for automation" in guide
    assert "documented loopback browser routes and submitted form fields" not in guide


def test_readme_documents_fresh_starter_identity() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "fresh UUIDv4 adventure identity" in readme
    assert "generated/" in readme
    assert "archives/" in readme


def test_private_beta_terms_match_project_version() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    terms = (PROJECT_ROOT / "BETA-TERMS.md").read_text(encoding="utf-8")

    assert f"Adventure Graph {pyproject['project']['version']} is provided" in terms
    assert "Adventure Graph 0.9.0 is provided" not in terms


def test_release_facing_docs_describe_the_local_code_candidate() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    beta_guide = (PROJECT_ROOT / "docs" / "beta-guide.md").read_text(encoding="utf-8")
    changelog = (PROJECT_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert "This 0.10.0 source snapshot" in readme
    assert "final code-candidate wheel will be rebuilt" not in readme
    assert "local code-candidate wheel" in beta_guide
    assert "contains no development payload" in beta_guide
    assert changelog.startswith("## 0.10.0 — Beta-readiness audit (local code candidate)")


def test_user_guides_document_direct_project_directory_launch() -> None:
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    beta_guide = (PROJECT_ROOT / "docs" / "beta-guide.md").read_text(encoding="utf-8")
    ui_guide = (PROJECT_ROOT / "docs" / "ui-usage.md").read_text(encoding="utf-8")

    assert "Passing a project directory containing `adventure.json`" in readme
    assert "adventure-graph ui adventure-workspace/my-adventure" in beta_guide
    assert "adventure-graph ui path/to/adventure-workspace/my-adventure" in ui_guide


def test_beta_roadmap_records_the_local_freeze_disposition() -> None:
    roadmap = (PROJECT_ROOT / "docs" / "beta-readiness-roadmap.md").read_text(encoding="utf-8")
    normalized = " ".join(roadmap.split())

    assert "## Previous code-candidate review — superseded by sample-scope revision" in normalized
    assert "Adventure reference library — accepted for beta" in normalized
    assert "capped at 2 MiB" in normalized
    assert "exact accepted application-and-sample revision" in normalized
    assert "Native Linux, Windows, and macOS artifacts" in normalized


def test_repository_does_not_reaccumulate_completed_progress_diaries() -> None:
    docs = PROJECT_ROOT / "docs"
    forbidden_names = sorted(
        path.name
        for pattern in (
            "backend-cleanup-session-*.md",
            "beta-readiness-session-*.md",
            "technical-cleanup-session-*.md",
            "ui-cleanup-session-*.md",
        )
        for path in docs.glob(pattern)
    )

    assert forbidden_names == []


def test_runtime_comments_do_not_encode_progress_session_numbers() -> None:
    asset_root = PROJECT_ROOT / "src" / "adventure_graph" / "interfaces" / "web" / "assets"
    stale_comments: list[str] = []
    for path in sorted(asset_root.glob("*")):
        if path.suffix not in {".css", ".js"}:
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if re.search(r"(?:/\*|//).*\bSession \d", line):
                stale_comments.append(f"{path.relative_to(PROJECT_ROOT)}:{line_number}")

    assert stale_comments == []


def test_local_markdown_links_resolve() -> None:
    markdown_paths = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "BETA-TERMS.md",
        PROJECT_ROOT / "CHANGELOG.md",
        *sorted((PROJECT_ROOT / "docs").glob("*.md")),
    ]
    broken: list[str] = []
    for path in markdown_paths:
        document = path.read_text(encoding="utf-8")
        for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", document):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative_path = target.split("#", maxsplit=1)[0]
            if not relative_path:
                continue
            destination = (path.parent / relative_path).resolve()
            if not destination.exists():
                line_number = document[: match.start()].count("\n") + 1
                broken.append(
                    f"{path.relative_to(PROJECT_ROOT)}:{line_number}: {target}"
                )

    assert broken == []


def test_documentation_index_is_complete_and_root_is_handoff_free() -> None:
    docs_index = (PROJECT_ROOT / "docs" / "README.md").read_text(encoding="utf-8")
    markdown_docs = sorted(
        path.name
        for path in (PROJECT_ROOT / "docs").glob("*.md")
        if path.name != "README.md"
    )
    missing = [name for name in markdown_docs if f"({name})" not in docs_index]

    assert missing == []
    assert list(PROJECT_ROOT.glob("ADVENTURE_GRAPH_*_HANDOFF.md")) == []
    assert len((PROJECT_ROOT / "README.md").read_text(encoding="utf-8").splitlines()) < 300


def test_desktop_entrypoint_and_build_extra_are_declared() -> None:
    pyproject = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]
    extras = pyproject["project"]["optional-dependencies"]

    assert scripts["adventure-graph-desktop"] == "adventure_graph.desktop:main"
    requirements = [
        line.strip().replace('"', "'")
        for line in (PROJECT_ROOT / "packaging" / "desktop-build-requirements.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert extras["desktop-build"] == requirements


def test_desktop_distribution_contract_is_checked_in() -> None:
    guide = (PROJECT_ROOT / "docs" / "desktop-distribution.md").read_text(encoding="utf-8")
    spec = (PROJECT_ROOT / "packaging" / "adventure_graph_desktop.spec").read_text(encoding="utf-8")
    build_script = (PROJECT_ROOT / "scripts" / "build_desktop.py").read_text(encoding="utf-8")
    artifact_contract = (PROJECT_ROOT / "scripts" / "desktop_artifacts.py").read_text(
        encoding="utf-8"
    )
    verifier = (PROJECT_ROOT / "scripts" / "verify_desktop_artifacts.py").read_text(
        encoding="utf-8"
    )
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "desktop.yml").read_text(encoding="utf-8")

    assert "gh run list --workflow desktop.yml --limit 5" in guide
    assert '--branch "$BRANCH"' not in guide

    for text in [
        "one server",
        "ADVENTURE_GRAPH_CONFIG_HOME",
        "100 MiB",
        "frozen executable",
        "Signing, notarization",
        "bundle-inventory SHA-256",
        "exact build dependency lock",
        "native runner provenance",
    ]:
        assert text in guide
    assert "collect_data_files" in spec
    assert "console=False" in spec
    assert '"--smoke-test"' in build_script
    assert "_reject_canonical_user_data" in build_script
    assert "BUNDLE_LIMIT_BYTES = 100 * 1024 * 1024" in artifact_contract
    assert "bundle_inventory_sha256" in artifact_contract
    assert "build_requirements_sha256" in artifact_contract
    assert "runner_image_version" in artifact_contract
    assert "verify_artifact_set" in verifier
    assert "actions/upload-artifact@v7" in workflow
    assert "actions/download-artifact@v8" in workflow
    assert "--require-platforms linux windows macos" in workflow
    assert "--source-revision" in workflow


def test_play_interface_panel_refactor_local_convergence_is_documented() -> None:
    cold_read_path = PROJECT_ROOT / "docs" / "play-interface-panel-cold-read.md"
    ui_architecture = (PROJECT_ROOT / "docs" / "ui-architecture.md").read_text(encoding="utf-8")
    ui_usage = (PROJECT_ROOT / "docs" / "ui-usage.md").read_text(encoding="utf-8")
    semantics = (PROJECT_ROOT / "docs" / "play-mode-semantics.md").read_text(encoding="utf-8")

    assert cold_read_path.is_file()
    normalized_cold_read = " ".join(cold_read_path.read_text(encoding="utf-8").split())
    normalized_architecture = " ".join(ui_architecture.split())
    normalized_usage = " ".join(ui_usage.split())
    normalized_semantics = " ".join(semantics.split())

    for required in [
        "When the Swine Kneel",
        "The Concord of Aurelune",
        "Creation context does not define a second ontology",
        "No new behavior correction was accepted during convergence",
    ]:
        assert required in normalized_cold_read
    assert "six peer disclosure sections" in normalized_architecture
    assert "six peer boxes" in normalized_usage
    assert "same ontology and lifecycle" in normalized_usage
    assert "presentation containers, not domain subdivisions" in normalized_semantics


def test_source_snapshot_portability_contract_is_checked_in() -> None:
    guide = (PROJECT_ROOT / "docs" / "source-snapshots.md").read_text(encoding="utf-8")
    roadmap = (PROJECT_ROOT / "docs" / "source-snapshot-portability-roadmap.md").read_text(
        encoding="utf-8"
    )
    script = (PROJECT_ROOT / "scripts" / "source_snapshot.py").read_text(encoding="utf-8")
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "adventure-graph/" in guide
    assert "120 characters" in guide
    assert "Windows Explorer" in guide
    assert "Phase 5 — Native Windows acceptance — complete" in roadmap
    assert "Phase 6 — Close or escalate — complete" in roadmap
    assert 'ARCHIVE_ROOT = "adventure-graph"' in script
    assert "MAX_ARCHIVE_MEMBER_PATH_CHARS" in script
    assert "source-package:" in makefile
    assert "scripts/source_snapshot.py build" in makefile
