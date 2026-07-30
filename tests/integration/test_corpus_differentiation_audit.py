"""Regression checks for the final corpus-wide differentiation audit."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import pytest

pytestmark = pytest.mark.corpus

AUDIT = Path("docs/final-corpus-differentiation-audit.md")
ROADMAP = Path("docs/adventure-second-look-roadmap.md")
ALLOWLIST = Path("docs/intentional-shared-encounter-titles.json")
NAME_LEDGER = Path("docs/example-encounter-name-ledger.md")
WORKSTREAM_TWO = Path("docs/corpus-differentiation-workstream-02.md")
WORKSTREAM_THREE = Path("docs/corpus-differentiation-workstream-03.md")
WORKSTREAM_FOUR = Path("docs/corpus-differentiation-workstream-04.md")
WORKSTREAM_FIVE = Path("docs/corpus-differentiation-workstream-05.md")
WORKSTREAM_SIX = Path("docs/corpus-differentiation-workstream-06.md")
ADVENTURE_PATHS = tuple(sorted(Path("examples").glob("*/adventure.json")))


def _load_sources() -> tuple[dict[str, object], ...]:
    return tuple(json.loads(path.read_text(encoding="utf-8")) for path in ADVENTURE_PATHS)


def test_corpus_differentiation_audit_covers_the_complete_source_corpus() -> None:
    """Keep the comparative audit tied to the complete thirteen-adventure corpus."""
    sources = _load_sources()
    audit = AUDIT.read_text(encoding="utf-8")

    assert len(sources) == 13
    assert sum(len(source["encounters"]) for source in sources) == 138
    assert sum(len(source["revelations"]) for source in sources) == 305
    assert sum(len(source["clues"]) for source in sources) == 1_385

    for source in sources:
        title = source["adventure"]["title"]
        assert title in audit

    for heading in (
        "## Judgment",
        "## Scope and method",
        "## What is already distinct",
        "## Material findings",
        "## Adventure-by-adventure dispositions",
        "## Ordered repair program",
        "## Guardrails for all repair work",
        "## Completion state",
    ):
        assert heading in audit


def test_encounter_titles_are_unique_except_for_documented_shared_institutions() -> None:
    """Reject accidental encounter-title collisions across the source corpus."""
    titles: defaultdict[str, list[str]] = defaultdict(list)
    for source in _load_sources():
        adventure_title = source["adventure"]["title"]
        for encounter in source["encounters"]:
            titles[encounter["title"]].append(adventure_title)

    collisions = {
        title: tuple(sorted(adventures))
        for title, adventures in titles.items()
        if len(adventures) > 1
    }

    allowlist = json.loads(ALLOWLIST.read_text(encoding="utf-8"))
    assert allowlist["schema_version"] == 1
    documented = {
        entry["title"]: tuple(sorted(entry["adventures"]))
        for entry in allowlist["encounter_title_duplicates"]
    }
    for entry in allowlist["encounter_title_duplicates"]:
        assert entry["rationale"].strip()

    assert collisions == documented

    ledger = NAME_LEDGER.read_text(encoding="utf-8")
    assert "- Adventures: **13**" in ledger
    assert "- Encounter titles: **138**" in ledger
    assert "- Exact cross-adventure duplicates: **0**" in ledger
    assert "- Article-and-punctuation-insensitive duplicates: **0**" in ledger
    assert "- Accepted title-only deconflictions: **4**" in ledger
    assert "- Unresolved candidates: **0**" in ledger
    for source in _load_sources():
        adventure_title = source["adventure"]["title"]
        for encounter in source["encounters"]:
            assert f"| {adventure_title} | {encounter['title']} | `{encounter['id']}` |" in ledger


def test_workstream_one_uses_the_current_encounter_identifiers() -> None:
    """Keep repaired titles and identifiers synchronized in unplayed adventures."""
    sources = {source["adventure"]["title"]: source for source in _load_sources()}

    swine = {
        encounter["id"]: encounter["title"]
        for encounter in sources["When the Swine Kneel"]["encounters"]
    }
    blackbriar = {
        encounter["id"]: encounter["title"]
        for encounter in sources["The Witch of Blackbriar Hall"]["encounters"]
    }

    wedding = {
        encounter["id"]: encounter["title"]
        for encounter in sources["A Wedding for the River"]["encounters"]
    }
    stone = {
        encounter["id"]: encounter["title"]
        for encounter in sources["The Siege of the Stone Lung"]["encounters"]
    }
    aurelune = {
        encounter["id"]: encounter["title"]
        for encounter in sources["The Concord of Aurelune"]["encounters"]
    }

    assert wedding["shrine-of-the-open-door"] == "The Doorless Shrine"
    assert stone["the-black-cisterns"] == "The Cisterns of Black Breath"
    assert swine["the-hall-of-petitions"] == "The Hall of Condemnations"
    assert swine["the-deep-bell"] == "The Six-Line Bell"
    assert aurelune["the-white-hart-gallery"] == "The Gallery of Silver Kin"
    assert blackbriar["chapel-of-the-free-witness"] == "Chapel of the Free Witness"


def test_blackbriar_identity_migration_is_exhaustive() -> None:
    """Reject residual antagonist names, slugs, or the superseded chapel identity."""
    blackbriar_root = Path("examples/the-witch-of-blackbriar-hall")
    text_paths = tuple(
        path
        for path in blackbriar_root.rglob("*")
        if path.is_file() and path.suffix in {".json", ".md", ".py"}
    )

    assert text_paths
    for path in text_paths:
        content = path.read_text(encoding="utf-8")
        lowered = content.lower()
        assert "hes" + "ter" not in lowered, path
        assert "chapel-of-the-open-door" not in lowered, path
        assert "chapel of the open door" not in lowered, path

    source = json.loads((blackbriar_root / "adventure.json").read_text(encoding="utf-8"))
    serialized = json.dumps(source, sort_keys=True).lower()
    assert "judith crowl" in serialized
    assert "judith-crowl-is-the-witch-and-manufactured-the-prosecutions" in serialized
    assert "chapel-of-the-free-witness" in serialized
    assert (blackbriar_root / "generated/encounters/chapel-of-the-free-witness.md").is_file()
    assert not (blackbriar_root / "generated/encounters/chapel-of-the-open-door.md").exists()


def test_superseded_blackbriar_name_is_confined_to_bramblewick() -> None:
    """Catch stale Blackbriar references outside its own project tree."""
    for path in Path().rglob("*"):
        if not path.is_file() or path.suffix not in {".json", ".md", ".py"}:
            continue
        if Path("examples/the-last-bell-of-bramblewick") in path.parents:
            continue
        if path.name.startswith("ADVENTURE_GRAPH_BRAMBLEWICK_"):
            continue
        if path in {
            Path("tests/integration/test_bramblewick_example.py"),
            Path("tests/integration/test_bramblewick_reference_library_corpus.py"),
        }:
            continue
        content = path.read_text(encoding="utf-8").replace("Hester Rowan", "")
        assert "hes" + "ter" not in content.lower(), path


def test_workstream_two_assigns_distinct_terminal_procedures() -> None:
    """Keep Stone Lung military and Swine dependent on live surface readings."""
    sources = {source["adventure"]["title"]: source for source in _load_sources()}
    stone = next(
        encounter
        for encounter in sources["The Siege of the Stone Lung"]["encounters"]
        if encounter["id"] == "the-stone-lung"
    )
    swine = next(
        encounter
        for encounter in sources["When the Swine Kneel"]["encounters"]
        if encounter["id"] == "the-deep-bell"
    )

    assert "## Heartstrike under fire" in stone["content"]
    assert "## Battlefronts and commands" in stone["content"]
    assert "Bas's initiative" in stone["content"]
    assert "costs a named sector, formation, or route" in stone["content"]
    assert "## Stations" not in stone["content"]
    assert "Do not spend an abstract grace cycle" in stone["content"]
    assert "adds one grace cycle" not in stone["content"]

    assert "## The living survey" in swine["content"]
    assert "## Reading the failure" in swine["content"]
    assert "There is no fixed allotment of three cycles" in swine["content"]
    assert "Every major intervention below produces a new report above" in swine["content"]
    assert "## The resonance clock" not in swine["content"]
    assert "grace cycle" not in swine["content"]

    assert "enemy" in stone["summary"].lower() or "battle" in stone["summary"].lower()
    assert "living herds" in swine["summary"].lower()


def test_workstream_two_document_records_comparison_and_verification() -> None:
    """Keep the paired terminal repair documented as a closed workstream."""
    document = WORKSTREAM_TWO.read_text(encoding="utf-8")
    for heading in (
        "## Judgment",
        "## Paragraph-level comparison",
        "## Distinct dramatic ownership",
        "## Stone Lung repair",
        "## Swine repair",
        "## Synchronization",
        "## Fingerprints",
        "## Permanent regressions",
        "## Preserved invariants",
        "## Verification",
        "## Disposition",
    ):
        assert heading in document
    assert "All 587 executable repository tests passed" in document
    assert "Workstream 3" in document


def test_workstream_three_assigns_glass_saint_native_ritual_grammar() -> None:
    """Keep Glass Saint operational while rejecting generic civic-machine scaffolding."""
    sources = {source["adventure"]["title"]: source for source in _load_sources()}
    glass = sources["The Glass Saint"]
    encounters = {encounter["id"]: encounter for encounter in glass["encounters"]}
    chapel = encounters["the-bell-chapel"]
    belfry = encounters["the-grand-belfry"]
    manor = encounters["vale-manor"]

    assert "Four workings cross the nave" in chapel["content"]
    assert "answers the rite in three pieces" in chapel["content"]
    assert "Every answer changes what the city will hear" in chapel["content"]
    assert "Name every hand on a rope before the first lift" in belfry["content"]
    assert "A sounded note cannot be unsounded" in belfry["content"]
    assert "**Six ways through the doors.**" in manor["content"]
    assert "**Five joined things give the saint a body.**" in manor["content"]
    assert "**The three notes borrow body, voice, and reach in order.**" in manor["content"]
    assert "**Every command opens one door and breaks another.**" in manor["content"]
    assert "**After the bells, the city keeps five reckonings.**" in manor["content"]

    serialized = json.dumps(glass, sort_keys=True)
    for stale in (
        "Four stations divide the nave",
        "three-part working set",
        "Fix the crew before the ropes move",
        "Three levels divide the work",
        "Choose an operation",
        "Arrival time removes only completed work",
        "Fix the arrival state before Edrin speaks",
        "**Six approaches.**",
        "**Fixed household positions.**",
        "**Five apparatus zones.**",
        "**Negotiation has material states.**",
        "**Run the three notes exactly.**",
        "**Commands create mixed emergencies.**",
        "**Resolution states branch from what survives.**",
        "**Voice restoration before dawn.**",
        "**Aftermath uses five separate ledgers.**",
    ):
        assert stale not in serialized


def test_workstream_three_current_layers_are_exhaustively_synchronized() -> None:
    """Reject stale source diction in every current Glass Saint projection and aid."""
    paths = (
        Path("examples/the-glass-saint.adventure.json"),
        Path("examples/the-glass-saint/adventure.json"),
        Path("src/adventure_graph/resources/the-glass-saint.adventure.json"),
        Path(
            "examples/the-glass-saint/archives/counterseal-witnesses-demonstrated-playthrough.journal.json"
        ),
        Path("examples/the-glass-saint/README.md"),
        Path("examples/the-glass-saint/RITUAL-AND-BELL-OPERATING-SHEET.md"),
        Path("examples/the-glass-saint/VALE-MANOR-AND-AFTERMATH-OPERATING-SHEET.md"),
        Path("examples/the-glass-saint/GM-ROUTE-AND-CONTINUITY-SHEET.md"),
        Path("examples/the-glass-saint/generated/00-overview.md"),
        Path("examples/the-glass-saint/generated/encounters/the-bell-chapel.md"),
        Path("examples/the-glass-saint/generated/encounters/the-grand-belfry.md"),
        Path("examples/the-glass-saint/generated/encounters/vale-manor.md"),
    )
    stale_phrases = (
        "Four stations divide the nave",
        "three-part working set",
        "Fix the crew before the ropes move",
        "Three levels divide the work",
        "Choose an operation",
        "Arrival time removes only completed work",
        "Fix the arrival state before Edrin speaks",
        "Six approaches",
        "Fixed household positions",
        "Five apparatus zones",
        "Negotiation has material states",
        "Run the three notes exactly",
        "Commands create mixed emergencies",
        "Resolution states branch from what survives",
        "Voice restoration before dawn",
        "Aftermath uses five separate ledgers",
    )

    combined = []
    for path in paths:
        assert path.is_file(), path
        content = path.read_text(encoding="utf-8")
        combined.append(content.lower())
        for phrase in stale_phrases:
            assert phrase not in content, (path, phrase)

    all_current = "\n".join(combined)
    for word in ("page", "pane", "vow", "voice", "breath", "door", "peal"):
        assert word in all_current


def test_workstream_three_document_records_scope_and_verification() -> None:
    """Keep the seven-field Glass Saint repair documented as a closed workstream."""
    document = WORKSTREAM_THREE.read_text(encoding="utf-8")
    for heading in (
        "## Judgment",
        "## Comparative target",
        "## Residual diction",
        "## Authoritative repair",
        "## Native dramatic grammar",
        "## Synchronization",
        "## Fingerprints",
        "## Permanent regressions",
        "## Preserved invariants",
        "## Verification",
        "## Disposition",
    ):
        assert heading in document
    assert "seven authoritative fields" in document
    assert "Workstream 4" in document


def test_workstream_four_assigns_distinct_court_grammars() -> None:
    """Keep Aurelune recognitional and Seven Reeds administrative."""
    sources = {source["adventure"]["title"]: source for source in _load_sources()}
    aurelune = sources["The Concord of Aurelune"]
    reeds = sources["The Mandate of Seven Reeds"]
    aurelune_encounters = {encounter["id"]: encounter for encounter in aurelune["encounters"]}
    reeds_encounters = {encounter["id"]: encounter for encounter in reeds["encounters"]}

    assert "assembling a coalition, not filling offices" in aurelune["adventure"]["explanation"]
    for term in ("Canopy", "plaques", "oath-mirrors", "banner seals", "Sunseed"):
        assert term in aurelune["adventure"]["explanation"]
    assert "## What Spring must recognize" in aurelune_encounters["the-unfurling-branch"]["content"]
    assert (
        "## What the White Hart must recognize"
        in aurelune_encounters["the-white-hart-gallery"]["content"]
    )
    assert (
        "## What the Noon Spear must recognize"
        in aurelune_encounters["the-noon-spear-court"]["content"]
    )
    assert (
        "## What the Red Rose must recognize"
        in aurelune_encounters["the-red-rose-pavilion"]["content"]
    )
    assert (
        "## Where the banner bargains touch"
        in aurelune_encounters["the-chamber-of-the-fourfold-petition"]["content"]
    )
    assert (
        "## How the Sunseed reads the coalition"
        in aurelune_encounters["the-crown-conclave"]["content"]
    )

    assert "The court is not assembling a coalition" in reeds["adventure"]["explanation"]
    for term in (
        "submission instrument",
        "field recipient",
        "effective hour",
        "acknowledgment route",
    ):
        assert term in reeds["adventure"]["explanation"]
    serialized_reeds = json.dumps(reeds, sort_keys=True)
    assert "## Bargains available here" not in serialized_reeds
    assert "## Four interlocking public bargains" not in serialized_reeds
    assert (
        "## What the commission can and cannot command"
        in reeds_encounters["hall-of-the-chrysanthemum-throne"]["content"]
    )
    assert (
        "## Five documents, one chain of provincial command"
        in reeds_encounters["chamber-of-seven-reeds"]["content"]
    )
    assert "## Order before dispatch" in reeds_encounters["the-second-audience"]["content"]
    assert "## Imperial issuance" in reeds_encounters["the-second-audience"]["content"]


def test_workstream_four_current_layers_are_synchronized() -> None:
    """Reject the superseded court skeleton in current source, aids, and packets."""
    paths = (
        Path("examples/the-concord-of-aurelune/adventure.json"),
        Path("examples/the-concord-of-aurelune/COURT-LEDGER.md"),
        Path("examples/the-concord-of-aurelune/PETITION-CLAUSE-MATRIX.md"),
        Path("examples/the-concord-of-aurelune/generated/00-overview.md"),
        Path("examples/the-concord-of-aurelune/generated/encounters/the-unfurling-branch.md"),
        Path("examples/the-concord-of-aurelune/generated/encounters/the-chamber-of-the-fourfold-petition.md"),
        Path("examples/the-concord-of-aurelune/generated/encounters/the-crown-conclave.md"),
        Path("examples/the-mandate-of-seven-reeds/adventure.json"),
        Path("examples/the-mandate-of-seven-reeds/COURT-LEDGER.md"),
        Path("examples/the-mandate-of-seven-reeds/DRAFTING-AND-IMPERIAL-JUDGMENT.md"),
        Path("examples/the-mandate-of-seven-reeds/generated/00-overview.md"),
        Path("examples/the-mandate-of-seven-reeds/generated/encounters/hall-of-the-chrysanthemum-throne.md"),
        Path("examples/the-mandate-of-seven-reeds/generated/encounters/chamber-of-seven-reeds.md"),
        Path("examples/the-mandate-of-seven-reeds/generated/encounters/the-second-audience.md"),
    )
    current = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    for stale in (
        "## The required settlement",
        "## Bargains available here",
        "## Four interlocking public bargains",
        "## Five documents, one settlement",
        "## The order of presentation",
        "## What agreement can and cannot do",
    ):
        assert stale not in current
    for phrase in (
        "makes the coalition visible",
        "Recognition grammar",
        "Administrative grammar",
        "dispatch, not ratification",
        "field recipient",
    ):
        assert phrase in current


def test_workstream_four_document_records_scope_and_verification() -> None:
    """Keep the paired court repair documented as a closed workstream."""
    document = WORKSTREAM_FOUR.read_text(encoding="utf-8")
    for heading in (
        "## Judgment",
        "## Comparative diagnosis",
        "## Start commissions",
        "## Faction encounter rhythm",
        "## Bargain and allocation representation",
        "## Final audiences",
        "## Authoritative repair",
        "## Synchronization",
        "## Fingerprints",
        "## Permanent regressions",
        "## Preserved invariants",
        "## Verification",
        "## Disposition",
    ):
        assert heading in document
    assert "thirty-three authoritative fields" in document
    assert "Workstream 5" in document


def test_workstream_five_assigns_distinct_adversary_conduct() -> None:
    """Keep the six audited adversaries behaviorally rather than verdict-level distinct."""
    sources = {source["adventure"]["title"]: source for source in _load_sources()}

    swine = json.dumps(sources["When the Swine Kneel"], sort_keys=True)
    stone = json.dumps(sources["The Siege of the Stone Lung"], sort_keys=True)
    salt = json.dumps(sources["The Princess on the Salt Road"], sort_keys=True)
    bramble = json.dumps(sources["The Last Bell of Bramblewick"], sort_keys=True)
    cauldron = json.dumps(sources["The Cauldron of Nine Silences"], sort_keys=True)
    blackbriar = json.dumps(sources["The Witch of Blackbriar Hall"], sort_keys=True)

    assert "treated custody as indemnity" in swine
    assert "whose hand will sign the ration order" in swine
    assert "speak every affected corridor by its inhabited name" in swine

    assert "## How Kest Mourne admits a fact" in stone
    assert "copied into all six sector ledgers" in stone
    assert "southern keys pass to mixed crews" in stone

    assert "never enlarges the warrant in private" in salt
    assert "writes each concession twice" in salt
    assert "resumes the custody demand at the exact clause" in salt

    assert "concedes one object at a time and changes the sentence around it" in bramble
    assert "asks the investigators to read the recipient names aloud" in bramble
    assert "Hes" + "ter reads only the warrant numbers" in bramble

    assert "annexing each safeguard" in cauldron
    assert "tests every clause for a seat, countersignature, emergency override" in cauldron
    assert "remains where the covenant explicitly places him and nowhere else" in cauldron

    assert "not an independent good she later corrupted" in blackbriar
    assert "punishes the first person who answers" in blackbriar
    assert "Every concession substitutes a new victim" in blackbriar


def test_workstream_five_current_layers_are_synchronized() -> None:
    """Reject superseded balanced-official formulas in current source, aids, and packets."""
    paths = (
        Path("examples/when-the-swine-kneel/adventure.json"),
        Path("examples/when-the-swine-kneel/README.md"),
        Path("examples/when-the-swine-kneel/archives/synthetic-complete-playthrough.journal.json"),
        Path("examples/when-the-swine-kneel/generated/encounters/the-nine-mile-pump-house.md"),
        Path("examples/when-the-swine-kneel/generated/encounters/the-deep-bell.md"),
        Path("examples/the-siege-of-the-stone-lung/adventure.json"),
        Path("examples/the-siege-of-the-stone-lung/README.md"),
        Path("examples/the-siege-of-the-stone-lung/generated/encounters/the-lantern-court.md"),
        Path("examples/the-siege-of-the-stone-lung/generated/encounters/the-stone-lung.md"),
        Path("examples/the-princess-on-the-salt-road/adventure.json"),
        Path("examples/the-princess-on-the-salt-road/README.md"),
        Path("examples/the-princess-on-the-salt-road/GM-OPERATING-SHEET.md"),
        Path(
            "examples/the-princess-on-the-salt-road/generated/encounters/house-at-three-cypresses.md"
        ),
        Path("examples/the-princess-on-the-salt-road/generated/encounters/myrine-harbor.md"),
        Path("examples/the-last-bell-of-bramblewick/adventure.json"),
        Path("examples/the-last-bell-of-bramblewick/README.md"),
        Path("examples/the-last-bell-of-bramblewick/GM-QUICKSTART.md"),
        Path("examples/the-last-bell-of-bramblewick/generated/encounters/bramblewick-school.md"),
        Path("examples/the-last-bell-of-bramblewick/generated/encounters/the-first-bell-moot.md"),
        Path("examples/the-cauldron-of-nine-silences/adventure.json"),
        Path("examples/the-cauldron-of-nine-silences/README.md"),
        Path("examples/the-cauldron-of-nine-silences/GM-OPERATING-SHEET.md"),
        Path("examples/the-cauldron-of-nine-silences/generated/encounters/white-hart-court.md"),
        Path("examples/the-cauldron-of-nine-silences/generated/encounters/cauldron-vault.md"),
        Path("examples/the-witch-of-blackbriar-hall/adventure.json"),
        Path("examples/the-witch-of-blackbriar-hall/README.md"),
        Path("examples/the-witch-of-blackbriar-hall/GM-OPERATING-SHEET.md"),
        Path(
            "examples/the-witch-of-blackbriar-hall/archives/blackbriar-commission-demonstrated-playthrough.journal.json"
        ),
        Path("examples/the-witch-of-blackbriar-hall/generated/encounters/saint-mercy-house.md"),
        Path(
            "examples/the-witch-of-blackbriar-hall/generated/encounters/underhall-of-the-hollow-feast.md"
        ),
    )
    current = []
    for path in paths:
        assert path.is_file(), path
        current.append(path.read_text(encoding="utf-8"))
    combined = "\n".join(current)

    for stale in (
        "Dast may help save Veyr and still answer for concealment",
        "The invasion is real. So is Kest Mourne's crime",
        "Dorion does not behave as an assassin with soldiers",
        "The good was real.",
        "Mael may remain in power under bounded authority",
        "Judith made the charity useful because a sham could be rejected",
    ):
        assert stale not in combined

    for phrase in (
        "treated custody as indemnity",
        "How Kest Mourne admits a fact",
        "Dorion's warrant discipline",
        "grammatical retreat",
        "Mael's annexation test",
        "Judith's concession rule",
    ):
        assert phrase in combined


def test_workstream_five_document_records_scope_and_verification() -> None:
    """Keep the six-adversary repair documented as a closed workstream."""
    document = WORKSTREAM_FIVE.read_text(encoding="utf-8")
    for heading in (
        "## Judgment",
        "## Comparative diagnosis",
        "## Distinct conduct",
        "### Corven Dast",
        "### Kest Mourne",
        "### Captain Dorion Vey",
        "### Orlo Vane",
        "### Lord Mael Taran",
        "### Judith Crowl",
        "## Authoritative repair",
        "## Synchronization",
        "## Fingerprints",
        "## Permanent regressions",
        "## Preserved invariants",
        "## Verification",
        "## Disposition",
    ):
        assert heading in document
    assert "seventeen authoritative fields" in document
    assert "Workstream 6" in document


def test_corpus_quality_record_closes_historical_workstreams() -> None:
    """Keep the completed comparative program closed without restoring workbench logs."""
    record = ROADMAP.read_text(encoding="utf-8")

    assert "The corpus-wide differentiation pass is also complete." in record
    assert "Future editorial changes should arise from concrete playtest evidence" in record
    for title in (
        "A Wedding for the River",
        "The Glass Saint",
        "The Mandate of Seven Reeds",
        "When the Swine Kneel",
    ):
        assert title in record


_PERSON_TITLES = (
    "Bellmaster",
    "Brother",
    "Captain",
    "Chief",
    "Curator",
    "Dame",
    "Doctor",
    "Engineer",
    "Envoy",
    "Factor",
    "Father",
    "Keeper",
    "King",
    "Lady",
    "Lord",
    "Marshal",
    "Master",
    "Mother",
    "Prince",
    "Princess",
    "Provost",
    "Queen",
    "Reeve",
    "Sir",
    "Sister",
    "Steward",
    "Warden",
)
_NAME_TOKEN = r"[A-Z][A-Za-z'\u2019.-]+"
_PERSON_TITLE_PATTERN = "|".join(_PERSON_TITLES)
_TITLE_PREFIX = re.compile(rf"^(?:{_PERSON_TITLE_PATTERN})\s+")
_FULL_NAME = re.compile(rf"^{_NAME_TOKEN}(?:\s+{_NAME_TOKEN}){{1,2}}$")
_TITLED_FULL_NAME = re.compile(
    rf"\b(?:{_PERSON_TITLE_PATTERN})\s+({_NAME_TOKEN}\s+{_NAME_TOKEN})\b"
)
_PARTY_HEADING = re.compile(rf"^#{{2,3}}\s+({_NAME_TOKEN}(?:\s+{_NAME_TOKEN}){{1,3}})\s*$")
_NON_PERSON_FIRST_TOKENS = {
    "Black",
    "Common",
    "Deep",
    "East",
    "Grand",
    "Great",
    "High",
    "Low",
    "New",
    "North",
    "Old",
    "Open",
    "Red",
    "Royal",
    "Saint",
    "South",
    "The",
    "West",
    "White",
}
_PARTY_HEADING_EXCLUSIONS = {
    "Authority",
    "Course",
    "Delegation",
    "Demonstrated",
    "Fresh",
    "Party",
    "Pressure",
    "Purpose",
    "The",
    "Useful",
    "Why",
}


def _walk_text(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(text for item in value for text in _walk_text(item))
    if isinstance(value, dict):
        return tuple(text for item in value.values() for text in _walk_text(item))
    return ()


def _anchored_person_names(source: dict[str, object]) -> set[str]:
    anchors: set[str] = set()
    for text in _walk_text(source):
        for bold in re.findall(r"\*\*([^*]+)\*\*", text):
            candidate = _TITLE_PREFIX.sub("", bold.strip().rstrip(".,:;"))
            if not _FULL_NAME.fullmatch(candidate):
                continue
            if candidate.split()[0] in _NON_PERSON_FIRST_TOKENS:
                continue
            anchors.add(candidate)
        anchors.update(_TITLED_FULL_NAME.findall(text))
    return anchors


def _demonstration_character_names() -> set[str]:
    names: set[str] = set()
    for path in sorted(Path("examples").glob("*/PARTY-DESIGN.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _PARTY_HEADING.match(line)
            if not match:
                continue
            candidate = match.group(1)
            if candidate.split()[0] in _PARTY_HEADING_EXCLUSIONS:
                continue
            names.add(candidate)
    return names


def _name_owners(names: set[str], source_text: dict[str, str]) -> dict[str, set[str]]:
    """Find exact bounded names with one corpus scan per adventure."""
    if not names:
        return {}
    ordered_names = sorted(names, key=lambda candidate: (-len(candidate), candidate))
    alternatives = "|".join(re.escape(name) for name in ordered_names)
    exact_name = re.compile(
        rf"(?<![A-Za-z'\u2019.-])(?:{alternatives})(?![A-Za-z'\u2019.-])"
    )
    owners: defaultdict[str, set[str]] = defaultdict(set)
    for title, text in source_text.items():
        for match in exact_name.finditer(text):
            owners[match.group(0)].add(title)
    return owners


def test_workstream_six_removes_exact_character_name_collisions() -> None:
    """Reject exact full-name reuse and repeated titled first names across adventures."""
    sources = _load_sources()
    source_text = {
        source["adventure"]["title"]: "\n".join(_walk_text(source)) for source in sources
    }
    anchors = set().union(*(_anchored_person_names(source) for source in sources))
    owners = _name_owners(anchors, source_text)
    collisions = {
        name: tuple(sorted(titles)) for name, titles in owners.items() if len(titles) > 1
    }
    assert collisions == {}

    titled_first_names: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    title_pattern = re.compile(
        rf"\b({'|'.join(_PERSON_TITLES)})\s+({_NAME_TOKEN})\s+{_NAME_TOKEN}\b"
    )
    for title, text in source_text.items():
        for role, first_name in title_pattern.findall(text):
            titled_first_names[(role, first_name)].add(title)
    assert {
        key: tuple(sorted(titles)) for key, titles in titled_first_names.items() if len(titles) > 1
    } == {}


def test_workstream_six_keeps_demonstration_names_out_of_authoritative_source() -> None:
    """Keep named validation parties subordinate to fresh-play adventure source."""
    source_text = {
        source["adventure"]["title"]: "\n".join(_walk_text(source))
        for source in _load_sources()
    }
    leaked = sorted(_name_owners(_demonstration_character_names(), source_text))
    assert leaked == []

    harrowgate = json.loads(
        Path("examples/the-bell-beneath-harrowgate/adventure.json").read_text(encoding="utf-8")
    )
    authoritative = json.dumps(harrowgate, ensure_ascii=False, sort_keys=True)
    assert "Torren Pike" not in authoritative
    assert "A player character may be that survivor" in authoritative
    assert "otherwise the porter briefs the commission" in authoritative


def test_workstream_six_name_repairs_are_exhaustive_in_current_trees() -> None:
    """Reject stale repeated names across source, aids, journals, archives, and packets."""
    replacements = {
        Path("examples/the-glass-saint"): (
            ("Mara Vale", "Iria Vale"),
            ("Corven Ash", "Halwen Gorse"),
        ),
        Path("examples/the-bell-beneath-harrowgate"): (
            ("Mara Venn", "Rhea Colm"),
            ("Ansel Greve", "Odran Greve"),
        ),
        Path("examples/the-witch-of-blackbriar-hall"): (("Brann Cleft", "Varro Cleft"),),
        Path("examples/the-last-bell-of-bramblewick"): (("Elian Marr", "Teren Malk"),),
        Path("examples/when-the-swine-kneel"): (("Mara Venn", "Tessa Rane"),),
    }
    for root, pairs in replacements.items():
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in root.rglob("*")
            if path.is_file() and path.suffix in {".json", ".md", ".py"}
        )
        for stale, current in pairs:
            assert stale not in text, (root, stale)
            assert current in text, (root, current)

    glass = Path("examples/the-glass-saint/adventure.json").read_bytes()
    assert Path("examples/the-glass-saint.adventure.json").read_bytes() == glass
    assert (
        Path("src/adventure_graph/resources/the-glass-saint.adventure.json").read_bytes() == glass
    )


def test_workstream_six_reduces_repeated_editorial_verdict_cadence() -> None:
    """Keep useful distinctions while rejecting the corpus-wide repeated verdict formulas."""
    texts = {
        source["adventure"]["title"]: "\n".join(_walk_text(source)).lower()
        for source in _load_sources()
    }
    assert sum("is not the same as" in text for text in texts.values()) == 1
    assert sum("it does not erase" in text for text in texts.values()) == 0
    assert sum("does not decide" in text for text in texts.values()) == 0

    wedding = texts["A Wedding for the River"]
    assert "that is not the same as disappearing behind him" in wedding
    assert "a promise enduring through changed words and footing" in wedding


def test_workstream_six_document_records_final_closure() -> None:
    """Keep the final cadence, naming, fresh-play, and validation sweep documented."""
    document = WORKSTREAM_SIX.read_text(encoding="utf-8")
    for heading in (
        "## Judgment",
        "## Naming audit",
        "## Fresh-play leakage repair",
        "## Cadence sweep",
        "## Authoritative repair",
        "## Synchronization",
        "## Fingerprints",
        "## Permanent regressions",
        "## Preserved invariants",
        "## Verification",
        "## Closure",
    ):
        assert heading in document
    assert "all six workstreams are complete" in document.lower()


def test_roadmap_closes_after_workstream_six() -> None:
    """Close the comparative editorial program without scheduling another repair cycle."""
    roadmap = ROADMAP.read_text(encoding="utf-8")
    audit = AUDIT.read_text(encoding="utf-8")

    assert "The corpus-wide differentiation pass is also complete." in roadmap
    assert "Future editorial changes should arise from concrete playtest evidence" in roadmap
    assert "The comparative audit and all six workstreams are complete." in audit
    assert "No further corpus-wide repair workstream is scheduled." in audit
