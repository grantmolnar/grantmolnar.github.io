# Command-line reference

This guide documents the stable Adventure Graph command-line surface. The browser and desktop interfaces
use **Lead/Leads** in presentation. Command names, JSON fields, journal event kinds, and generated filenames
retain `clue` for backward compatibility.

For command-specific options, run:

```bash
adventure-graph --help
adventure-graph <command> --help
```

## Command map

### Project and output

| Command | Purpose | Detailed guidance |
| --- | --- | --- |
| `init` | Create a fresh editable starter project with new UUIDv4 identity. | [File format](file-format.md) |
| `ui` | Open the local browser authoring interface. | [Local web interface](ui-usage.md) |
| `validate` | Validate leads, revelations, reachability, and graph resilience. | [Validation diagnostics](validation-diagnostics.md) |
| `render` | Generate the complete Markdown adventure packet. | [Architecture](architecture.md) |
| `summary` | Print or save the current play summary. | [Runtime state](runtime-state.md) |

### Authoring

| Commands | Purpose | Detailed guidance |
| --- | --- | --- |
| `list`, `inspect` | Review authored entities and direct dependencies. | [Authoring lifecycle](authoring-lifecycle.md) |
| `add-encounter`, `add-reference`, `add-revelation`, `add-clue` | Append new authored material. | [File format](file-format.md) |
| `edit-encounter`, `edit-reference`, `edit-revelation`, `edit-clue`, `move-clue` | Change fields or relocate a lead safely. | [Authoring lifecycle](authoring-lifecycle.md) |
| `link-reference`, `unlink-reference` | Maintain ordered contextual encounter/reference associations. | [Authoring lifecycle](authoring-lifecycle.md) |
| `remove-encounter`, `remove-reference`, `remove-revelation`, `remove-clue` | Remove material with dependency-aware refusal or cascade. | [Authoring lifecycle](authoring-lifecycle.md) |

### GM processing

| Commands | Purpose | Detailed guidance |
| --- | --- | --- |
| `start-session`, `end-session` | Record explicit tabletop-session boundaries and metadata. | [Runtime state](runtime-state.md) |
| `visit`, `spot-clue`, `miss-clue` | Record where a party went and which lead opportunities were found or missed. | [Runtime state](runtime-state.md) |
| `establish-revelation`, `foreclose-revelation`, `reopen-revelation`, `unlock-encounter` | Record interpreted conclusions, later judgments, and newly available encounters. | [Runtime state](runtime-state.md) |
| `note`, `reference-note`, `consequence` | Append visit commentary, persistent-reference notes, and durable encounter changes. | [Runtime state](runtime-state.md) |
| `correct-latest` | Append an audit event voiding the latest active table operation. | [Runtime state](runtime-state.md) |
| `archive`, `list-archives`, `restore-archive`, `delete-archive` | Preserve, inspect, restore, or permanently delete journal archives. | [Journal archives](journal-archives.md) |

## Authoring workflow

### 1. Initialize or write the source

```bash
mkdir adventure-workspace
adventure-graph init adventure-workspace/my-adventure
cd adventure-workspace/my-adventure
```

This creates a complete directory project:

```text
adventure.json
play-state.json
generated/
archives/
```

Each initialization copies the starter content but assigns a fresh UUIDv4 adventure identity, so
separately initialized projects never masquerade as the same canonical adventure. The initialized
example is a complete urban investigation rather than a four-encounter topology
demonstration. Its nine encounters support public, documentary, legal, witness, ritual, bell-control,
and direct-manor routes while retaining conservative lead and connectivity validation defaults. The
public half includes named witnesses, divided civic authority, evidence-custody choices, and persistent
hearing states rather than a single influence score. The ritual half fixes separate witness, mouth, crown,
and relay pins; a three-part counterkey; a named bell crew; event-based pressure; and late-arrival
counter-operations. The repository example and packaged initialization resource remain identical;
only the new project's adventure identifier is regenerated during initialization.

The source model begins:

```json
{
  "schema_version": 3,
  "adventure": {
    "id": "the-glass-saint",
    "title": "The Glass Saint",
    "synopsis": "A compact account of the whole adventure.",
    "premise": "The player-facing situation and core problem.",
    "explanation": "The GM-facing account of what is actually happening.",
    "tags": {
      "genres": ["Investigation", "Gothic mystery"],
      "game_systems": ["System-agnostic"],
      "settings": ["Original fantasy"],
      "party_size": {"minimum": 3, "maximum": 5},
      "level": {"minimum": null, "maximum": null},
      "combat_intensity": "light",
      "keywords": ["Museum", "Relic", "Urban mystery"]
    },
    "validation": {
      "minimum_clues_per_revelation": 3,
      "minimum_source_encounters_per_revelation": 3,
      "minimum_incoming_clues_per_encounter": 3,
      "minimum_incoming_source_encounters_per_encounter": 3,
      "minimum_outgoing_clues_per_encounter": 3,
      "minimum_distinct_encounter_targets_per_encounter": 3,
      "minimum_edge_connectivity": 3,
      "require_directed_reachability": true
    }
  },
  "encounters": [],
  "revelations": [],
  "clues": []
}
```

A lead has exactly one source encounter and supports exactly one revelation. A revelation may unlock an
encounter or represent a non-spatial conclusion such as “the duke hired the killers.”

Adventure-level `tags` use structured fields for stable catalog filters and an open-ended `keywords`
list for themes and play styles. Party-size and level bounds are inclusive and optional; leaving them
unspecified records no claim about compatibility. Encounter tags remain separate and classify material
inside one adventure. See [the file-format guide](file-format.md) for the complete contract.

See `examples/the-glass-saint.adventure.json`, `schemas/adventure.schema.json`, and
[the architecture guide](architecture.md). For a complete seven-encounter adventure, generated
packet, route stress tests, archived synthetic playthrough, and staged party-journal design, see
`examples/when-the-swine-kneel/`.

The thirteen-adventure second-look and six-workstream corpus differentiation program is complete. See
[`docs/final-corpus-differentiation-audit.md`](final-corpus-differentiation-audit.md) for the comparative
judgment and [`docs/corpus-differentiation-workstream-06.md`](corpus-differentiation-workstream-06.md)
for the final naming, fresh-play, cadence, and validation closure.

### 2. Add encounters, references, revelations, and leads

The JSON file remains human-editable, but focused commands make routine additions safer and preserve
canonical formatting:

```bash
adventure-graph add-encounter adventure.json "The Hidden Dock" \
  --summary "Smugglers transfer ritual cargo beneath the customs house." \
  --opening-view "Black water moves beneath a customs stair that should end in stone." \
  --content "Crates, tide tables, and a nervous harbor clerk define the encounter." \
  --tag location \
  --tag investigation

adventure-graph add-revelation adventure.json "Locate the Hidden Dock" \
  --description "Several independent leads identify the dock beneath the customs house." \
  --unlocks the-hidden-dock

adventure-graph add-clue adventure.json "Salt-stained Invoice" \
  --source the-shattered-gallery \
  --revelation locate-the-hidden-dock \
  --description "The invoice names a customs-house subcellar and a midnight delivery." \
  --discovery search

adventure-graph add-reference adventure.json person "Captain Cora Pike" \
  --alias "Cora Pike" \
  --summary "An investigator whose allegiance may change during the adventure." \
  --tag investigator
```

Encounter, revelation, and lead creation commands derive stable readable identifiers from initial titles. New
references receive opaque UUIDv4 identity exactly once. These commands reject dangling structural
references; reference prose may be completed incrementally, with title-only records reported as
validation warnings.

Readable identifiers add numeric suffixes when necessary. Encounter summaries and revelation
descriptions are optional in both the CLI and browser, matching the persisted schema. Validation remains
separate because newly added material may be intentionally incomplete while it is being written.

### 3. Inspect and refactor

```bash
adventure-graph list adventure.json encounter
adventure-graph inspect adventure.json encounter the-shattered-gallery
adventure-graph inspect adventure.json revelation the-archive-vault-contains-the-relics-hidden-provenance
adventure-graph inspect adventure.json clue accession-number-on-a-glass-shard
adventure-graph list adventure.json reference
adventure-graph inspect adventure.json reference REFERENCE_UUID
adventure-graph inspect adventure.json encounter the-shattered-gallery \
  --state play-state.json

adventure-graph edit-encounter adventure.json the-shattered-gallery \
  --title "The Broken Gallery" \
  --tag location \
  --tag glass

adventure-graph edit-revelation adventure.json the-archive-vault-contains-the-relics-hidden-provenance \
  --title "Identify the restricted archive"

adventure-graph edit-clue adventure.json accession-number-on-a-glass-shard --discovery automatic
adventure-graph move-clue adventure.json accession-number-on-a-glass-shard the-bell-chapel
adventure-graph edit-reference adventure.json REFERENCE_UUID --title "Captain Pike"
adventure-graph link-reference adventure.json the-shattered-gallery REFERENCE_UUID \
  --context "She audits the restoration ledgers during the opening investigation."
adventure-graph unlink-reference adventure.json the-shattered-gallery REFERENCE_UUID
```

Titles and identifiers have separate lifecycles. Editing a title preserves the adventure, encounter,
revelation, lead, or reference identifier, so routes, scripts, encounter links, and recorded journal
events remain stable. New adventures and references receive opaque UUID identity; encounters,
revelations, and leads receive readable identifiers from their initial titles. Raw identifier migration
is intentionally absent from ordinary CLI and browser authoring. When no `--state` option is supplied, authoring commands discover the
canonical companion journal if present: `play-state.json` beside a directory project's
`adventure.json`, or `<name>.play-state.json` beside a standalone `<name>.adventure.json`. Repeat
`--state PATH` to validate multiple journals before structural changes.

Removal is dependency-aware and conservative:

```bash
adventure-graph remove-clue adventure.json obsolete-clue
adventure-graph remove-revelation adventure.json obsolete-conclusion
adventure-graph remove-revelation adventure.json obsolete-conclusion --cascade
adventure-graph remove-reference adventure.json REFERENCE_UUID --cascade
adventure-graph remove-encounter adventure.json abandoned-wing --cascade
```

Without `--cascade`, a removal with authored dependents is refused and reports their exact
identifiers. A cascade is still refused when it would invalidate a related play journal. Historical
events are never silently erased. See the [authoring lifecycle](authoring-lifecycle.md) for the
full safety and persistence contract.

### 4. Validate and prepare the GM packet

```bash
adventure-graph validate adventure.json
adventure-graph render adventure.json generated
```

Validation reports lead-count and source-diversity deficits, outgoing-link problems, unreachable
encounters, referential errors, and the exact global minimum cut. When graph connectivity is below policy,
it proposes unused cross-partition encounter pairs as structural repair candidates. The GM still decides
which connection belongs in the fiction and what lead should express it.

Generated files are:

```text
00-overview.md
01-encounter-index.md
02-clue-list.md
03-revelation-list.md
04-validation-report.md
encounters/<encounter-id>.md
```

## GM workflow

### Before a session

Validate the authored adventure and render the current table-facing packet:

```bash
adventure-graph validate adventure.json
adventure-graph render adventure.json generated --state play-state.json
```

Supplying `--state` adds `05-play-summary.md`. That summary distinguishes spotted leads,
supported-but-unconfirmed revelations, established revelations, available and locked encounters, visit
history, and lasting changes.

### During a session

Begin an explicit session. Existing unsegmented journals remain valid, but once explicit sessions
begin the application requires ordinary play operations to occur inside an active session:

```bash
adventure-graph start-session adventure.json play-state.json \
  --title "The western breach" \
  --played-on 2026-07-14 \
  --participant "Ilyra" \
  --participant "Torren"
```

Record an encounter visit, including leads found immediately, initial notes, and an optional split-party
label:

```bash
adventure-graph visit adventure.json play-state.json the-shattered-gallery \
  --party "Gallery team" \
  --clue accession-number-on-a-glass-shard \
  --note "The group distrusted the curator and copied the accession number."
```

A lead can be spotted only at its authored source encounter and only once. Record a lead found later in
the same encounter with `spot-clue`:

```bash
adventure-graph spot-clue adventure.json play-state.json curator-incident-memorandum
```

By default, `spot-clue` uses the latest visit to that lead's source encounter. Use `--visit` to attach it
to an earlier visit explicitly. A missed opportunity is also visit-specific and does not prevent a
later discovery:

```bash
adventure-graph miss-clue \
  adventure.json play-state.json curator-incident-memorandum --visit 1
```

Spotting a lead does not automatically establish the revelation it supports. Record the players'
actual conclusion separately:

```bash
adventure-graph establish-revelation \
  adventure.json play-state.json the-archive-vault-contains-the-relics-hidden-provenance \
  --clue accession-number-on-a-glass-shard \
  --note "They matched the accession number to the restricted vault index."
```

An unestablished revelation may also be explicitly foreclosed and later reopened. Both judgments
require reasons and remain correctable:

```bash
adventure-graph foreclose-revelation \
  adventure.json play-state.json the-curator-serves-the-glass-court \
  --reason "The last witness has left the city."

adventure-graph reopen-revelation \
  adventure.json play-state.json the-curator-serves-the-glass-court \
  --reason "The party recovered the witness's encoded deposition."
```

When an established revelation unlocks an encounter, the journal receives a separate encounter-unlock event. A
GM may also make an encounter available through an unmodeled route:

```bash
adventure-graph unlock-encounter adventure.json play-state.json hidden-dock \
  --reason "The ferryman agreed to carry the group there directly."
```

Append commentary to an existing visit or record a durable change affecting an encounter:

```bash
adventure-graph note adventure.json play-state.json 1 \
  "They later recognized the carriage seal."

adventure-graph consequence adventure.json play-state.json the-archive-vault \
  "The registrar now knows the group copied the ledger."
```

Append a chronological note to a persistent person, place, organization, object, or other authored
reference without changing its reusable description:

```bash
adventure-graph reference-note adventure.json play-state.json REFERENCE_UUID \
  "The registrar now trusts the group with the west stair key."
```

Encounters may be revisited, but a locked encounter cannot be visited. If the most recent table action was
entered accidentally, append a correction rather than rewriting the journal:

```bash
adventure-graph correct-latest adventure.json play-state.json \
  --reason "The group had not actually opened the cabinet."
```

A compound visit or revelation/unlock action is corrected atomically. The original events remain in
the audit history but no longer affect the current projection. See [runtime state](runtime-state.md)
and `schemas/play-state.schema.json` for the journal model and invariants.

### After a session

Close the explicit session before producing the recap:

```bash
adventure-graph end-session adventure.json play-state.json \
  --closing-note "The party secured the archive but lost the western stairs."
```

Print the current summary:

```bash
adventure-graph summary adventure.json play-state.json
```

Save the summary directly to a file:

```bash
adventure-graph summary adventure.json play-state.json \
  --output generated/05-play-summary.md
```

Or regenerate the complete packet, including the summary:

```bash
adventure-graph render adventure.json generated --state play-state.json
```

The active journal is append-only. Notes, consequences, and corrections become new events rather
than rewriting past visits.

## Archive, restore, and delete journals

The browser **Archives** workspace can download the non-empty active journal without resetting it,
download any stored archive, and import a matching `*.journal.json` playthrough into the archive catalog.
Imported playthroughs must carry the same adventure identity and do not replace the active journal.

Archiving is the normal reset operation. It preserves the active journal and its adventure snapshot,
then replaces `play-state.json` with a canonical empty journal:

```bash
adventure-graph archive adventure.json play-state.json \
  --name first-table-run \
  --label "First table run"
```

The default destination is `archives/first-table-run.journal.json`. Empty journals are not archived.
The filename is part of archive identity and must remain `<archive-id>.journal.json`. Archive identifiers
use at most 80 ASCII filename-safe characters and are unique without regard to case; renamed, duplicated,
or case-colliding files fail closed instead of creating an ambiguous archive catalog.
List preserved runs with:

```bash
adventure-graph list-archives archives
```

Restore an archive into an empty active journal:

```bash
adventure-graph restore-archive \
  adventure.json play-state.json archives/first-table-run.journal.json
```

Restore validates the historical journal against the current adventure before changing the active
journal. A successful restore retains the immutable archive byte-for-byte. Archive/reset uses the
crash-recoverable local transaction layer; restoration uses one same-directory atomic journal
replacement.

Permanent deletion requires the exact archive identifier:

```bash
adventure-graph delete-archive \
  adventure.json play-state.json archives/first-table-run.journal.json \
  --confirm first-table-run
```

When `--confirm` is omitted, the command prompts for the identifier. There is intentionally no
generic `--yes` bypass. See [journal archives](journal-archives.md) for the complete lifecycle
contract.

## Validation policy

The default policy is intentionally strict but configurable per adventure:

1. Every necessary revelation needs at least three leads from at least three distinct source encounters.
2. Every necessary non-start encounter needs at least three incoming locator leads from at least three
   distinct source encounters.
3. Optional revelations and optional non-start encounters need at least one incoming lead; absence is a
   warning rather than an error.
4. Every non-end encounter must contain at least three outgoing leads and point to at least three distinct
   encounter destinations.
5. Every necessary encounter must be reachable by directed lead links from a start encounter. An authored but
   unreachable optional encounter produces a warning.
6. The simple undirected structure connecting necessary encounters must have edge connectivity at least
   three. Optional encounters may supply alternate paths but do not lower the measured floor merely by
   existing as a fragile spur.

Rule 6 is stronger than ordinary connectedness: no pair of necessary regions can be separated by
removing only one or two distinct encounter-to-encounter links. Parallel leads between the same pair count as
one structural connection. The validator reports the exact partition and crossing edges, not merely
a number.

These defaults implement this project's chosen safety invariant; they are not a claim that every
valid adventure must use the same thresholds. See
[validation diagnostics](validation-diagnostics.md) for policy and repair semantics.
