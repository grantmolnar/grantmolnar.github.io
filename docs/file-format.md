# File Format

Adventure definitions and play state are separate UTF-8 JSON documents with independent schema
versions.

Hidden files beginning `.adventure-graph-transaction-` and the temporary
`.adventure-graph-project-creation.json` file are private recovery metadata, not canonical documents
and not part of any public JSON schema. They may appear after abnormal process termination. Reopen
the project normally so Adventure Graph can recover them; do not edit or delete them manually.

All canonical JSON documents have an 8 MiB operational size ceiling and a maximum structural nesting
depth of 64 objects or arrays. Play journals additionally contain at most 10,000 events. These limits
bound local parsing and projection work; they do not advance a schema version or change the meaning of
any accepted field. Browser-owned canonical files, generated reports, archives, workspace settings,
and recovery artifacts must remain below their resolved owner root and may not use symlinks.

## Adventure source: schema version 3

`adventure-graph init` copies the packaged starter content but assigns a fresh UUIDv4 adventure
identifier and creates a matching empty journal. The authoritative packaged example retains its legacy
readable identifier because it is an existing adventure; independently initialized editable projects
are distinct canonical adventures.

Schema version 3 establishes the encounter vocabulary throughout the authored contract. It replaces
schema version 2 rather than maintaining a dual reader: `encounters`, `source_encounter_id`,
`unlocks_encounter_id`, and the encounter-named validation settings are canonical. Bundled adventures,
archive snapshots, examples, schemas, and generated packets were migrated atomically before beta.

Schema versions mark incompatible structural boundaries. Within one current version, newer readers
remain backward-compatible with omitted known fields: missing prose loads as an empty string, missing
encounter roles load as `false`, missing discovery metadata loads as empty tags, and missing encounter
tags load as an empty list. A supplied value with the wrong type is rejected, and saving writes the
complete current shape.

Current-version evolution is one-way safe rather than silently permissive. A reader rejects every
unknown object field named outside its published schema and identifies the source document and object
boundary. It also enforces the schema's current value constraints, including nonempty values only where
the schema requires them, identifier grammar, uniqueness, numeric minima, and date or date-time syntax.
Canonical writers apply
the same checks before replacing a file, so application loading, schema validation, and serialization do
not define competing current formats. Thus a newer release may read an older document by applying known
defaults, while an older release fails closed on a document containing newer fields instead of erasing
those fields on its next save. Reinterpreting an existing valid field or otherwise requiring two-way
compatibility requires a new schema version. Tightening runtime enforcement to reject a value already
invalid under the published schema does not.

### Adventure metadata

The `adventure` object contains:

- `id`: a durable adventure identifier; new adventures use UUIDv4, while existing legal IDs remain
  stable;
- `title`: the user-facing adventure name;
- `synopsis`: a concise summary of the whole adventure;
- `premise`: the player-facing situation and core problem;
- `explanation`: the GM-facing account of what is actually happening;
- `tags`: structured discovery facets and open-ended descriptive keywords; and
- optional `validation` policy overrides.

Empty `synopsis`, `premise`, or `explanation` values are structurally legal. Empty premise or
explanation values raise validation warnings. The `encounters`, `revelations`, and `clues` arrays may all
be empty, so a new adventure may begin as only a titled shell with generated identity and a matching
empty journal. The guided creation form's opening encounter is optional; later encounters, including the
first encounter of an empty shell, can be added through the revision-aware browser authoring workflow.

#### Adventure discovery tags

The `tags` object uses a hybrid model. Stable filtering concepts are represented explicitly, while
`keywords` remains open-ended for themes, structures, and play styles that do not justify permanent
schema fields. It contains:

- `genres`: zero or more genre labels;
- `game_systems`: zero or more intended or supported game systems;
- `settings`: zero or more worlds, campaign settings, or broad setting labels;
- `party_size.minimum` and `party_size.maximum`: optional inclusive group-size bounds;
- `level.minimum` and `level.maximum`: optional inclusive character-level bounds;
- `combat_intensity`: `none`, `light`, `moderate`, `heavy`, or `null`; and
- `keywords`: zero or more additional descriptive tags.

Labels are trimmed, nonempty, and unique within their facet without regard to case. Range endpoints
must be positive when supplied, and a minimum cannot exceed its maximum. Group size counts player
characters, not the GM. An omitted range is not an assertion that the adventure suits every group
size or level; it means that the author has not specified that facet. This distinction is especially
important for system-agnostic, levelless, or mechanics-light adventures. Use `System-agnostic` only
when the adventure is not intended for a named rules system; a setting-specific but mechanically
light adventure can still name its intended system.

Combat intensity is a deliberately coarse catalog judgment:

- `none`: combat is neither expected nor needed;
- `light`: combat is rare, optional, or secondary;
- `moderate`: combat recurs but shares the adventure with other primary modes; and
- `heavy`: combat is a principal mode of play and occupies a substantial share of the adventure.

Adventure tags support catalog discovery and generated-reference metadata. They do not alter graph
validation or play-state semantics. Encounter `tags` remain a separate lightweight classification
for material inside one adventure.

### Encounters (`encounters` internally)

Every encounter stores `id`, `title`, `summary`, `opening_view`, `content`, `required`, `start`, `end`, and `tags`.

- `summary` is a concise GM-facing orientation to this encounter, not a synopsis of the whole
  adventure.
- `opening_view` is a table-ready, player-facing description presented when the characters enter.
  It should normally provide enough concrete sensory and situational detail to read or paraphrase
  without mining the later encounter material for an opening scene.
- `content` is the remaining Markdown encounter material.
- `required` defaults to `true`. Necessary encounters use configured incoming locator-clue and source
  minima. Optional encounters need at least one incoming locator clue or raise a warning.
- `start` marks where play begins. No start locator clues are required, regardless of necessity.
- `end` marks a possible conclusion. Outgoing clue requirements are waived for end encounters.

No start encounter, multiple start encounters, or multiple end encounters raise warnings. Several starts or ends are
permitted when intentional.

### Revelations

Every revelation stores `id`, `title`, `description`, `unlocks_encounter_id`, and `required`.
`required` defaults to `true`. Necessary revelations use configured clue-count and source-diversity
minima. Optional revelations need at least one supporting clue or raise a warning. `unlocks_encounter_id`
may be `null`. Revelations that unlock a start encounter are exempt from locator-support requirements.

### Clues

Every clue stores `id`, `title`, `source_encounter_id`, `revelation_id`, `description`, and `discovery`.
A clue has exactly one source and supports exactly one revelation.

### Reference-library extension (headless implementation complete)

Adventure schema version 3 includes the following additive fields without changing existing encounter,
revelation, clue, or journal semantics. The runtime reader, canonical writer, validator, and archive
snapshot path implement this contract; application mutation commands and user interfaces belong to
later phases.

The root document gains an ordered `references` array. Each reference stores:

- `id`: canonical UUIDv4 text, generated once and independent of the displayed title;
- `kind`: `person`, `place`, `organization`, `object`, or `other`;
- `title`: a trimmed nonempty display name;
- `aliases`: ordered trimmed alternate names;
- `summary`: concise GM-facing orientation;
- `content`: detailed GM-facing Markdown; and
- `tags`: ordered trimmed authored-search labels.

Each encounter gains an ordered `reference_links` array. Each subordinate link stores `reference_id` and
optional encounter-specific `context`. A pair may occur at most once within one encounter. Links have no
independent identifier, backlinks are derived, and associations do not create graph edges.

Omitted `references`, `reference_links`, aliases, summary, content, tags, and context values receive empty
defaults. Current writers serialize the complete shape. Unknown fields remain unsupported and fail
closed. Duplicate or malformed reference IDs, unsupported kinds, malformed aliases or tags, dangling
links, and duplicate links are errors. Empty reference prose and ambiguous duplicate exposed names are
validation warnings.

Generated reference material groups people, places, organizations, objects, then other records, preserving
top-level authored order within each group. Encounter-local display preserves link order; derived
backlinks preserve adventure encounter order.

The extension does not advance adventure schema version 3 because it adds known fields with documented
omission defaults and does not reinterpret any existing valid field. Older binaries reject populated
reference fields rather than erasing them. Journal archive schema version 1 remains unchanged because an
archive still embeds a complete authored adventure snapshot. See
`adventure-reference-library-phase-1-design.md` for portability, revision, and removal rules.

### Internal identifiers

Identifiers are durable machine fields and are never inferred again after creation. New adventures
use canonical UUIDv4 text. Existing adventures may retain earlier slug-shaped IDs; those values are
equally stable and require no migration. New encounter, revelation, and clue identifiers are
initialized from
their titles as lower-case ASCII words separated by hyphens, with numeric suffixes such as `-2` for
uniqueness within the adventure. Later title edits preserve all identifiers and references.

The shared identifier schema deliberately accepts both UUID text and readable slug-shaped nested
IDs. Identifier shape does not determine mutability. Controlled repair code may explicitly migrate
an ID and
its references, but ordinary authoring never performs that operation implicitly.

## Play state: schema version 6

Play state contains the matching `adventure_id` and an ordered `events` array. Every event has a
one-based contiguous `sequence` and `operation_number`. Version 6 retains the complete version-5 event
set and adds append-only notes associated with persistent authored references. Earlier version-5 work
introduced explicit sessions, visit-specific clue misses, revelation foreclosure and reopening,
optional party labels on visits, and auditable recorded dice results.

Supported event types are:

- `session_started` and `session_ended`;
- `encounter_visited`, with a canonical `party_label` string;
- `clue_spotted` and `clue_missed`;
- `revelation_established`, `revelation_foreclosed`, and `revelation_reopened`;
- `dice_roll_recorded`;
- `encounter_unlocked`;
- `visit_note_recorded`;
- `reference_note_recorded`;
- `encounter_consequence_recorded`; and
- `operation_voided`.

Known optional event fields may be omitted and receive their documented defaults. These include empty
session titles and notes, null played dates, empty participant lists, empty party labels, empty
revelation support notes, empty dice labels, null encounter-unlock source-revelation IDs, and empty
unlock reasons. Every unknown event or recorded-dice-term field is rejected before projection or save.
Required identifiers and text are nonempty; session dates must be real canonical calendar dates;
participant and supporting-clue lists are unique and nonempty by item; and recorded dice totals must
agree with possible results.

Once a journal records its first explicit session, ordinary content events must occur inside an
active session. Earlier unsegmented history remains valid. Session and visit numbers are independently
one-based and contiguous; visit numbers continue globally across session boundaries.

A missed clue names both the clue and the visit at which the opportunity passed. It does not prevent
later discovery. Revelation foreclosure and reopening are explicit GM judgments with reasons; neither
is inferred from clue counts. Recorded dice events store the original expression, every individual
result, modifiers, and the validated total. A reference note names one stable authored `reference_id`
and carries nonempty GM text. It augments the chronological playthrough without editing the reusable
reference description. Unrecorded rolls, focused encounters, selected references, pins, and working
drafts are not canonical events.

Schema version 6 is the final pre-beta breaking boundary and adds `reference_note_recorded` while
retaining every version-5 event shape. The loader deliberately rejects versions 1 through 5 instead of
preserving a permanent migration surface. Bundled active journals and archive journals were migrated
atomically. See
`play-mode-semantics.md`, `runtime-state.md`, and `schemas/play-state.schema.json` for operation and
projection invariants.

## Journal archive: schema version 1

A journal archive is the canonical portable playthrough format. Browser export of either the active
journal or a stored archive produces this document; browser import validates it and adds it to the archive
catalog for the adventure identified by its embedded snapshot. Import never rewrites the active journal.

A journal archive contains archive metadata, a complete schema-version-3 adventure snapshot, and a
complete schema-version-6 play journal. The archive label may be absent and defaults to an empty
string; all other archive metadata remains required. Archive identifiers use at most 80 letters, digits, periods, underscores, and hyphens, beginning with a
letter or digit. They are unique without regard to case so a catalog remains unambiguous when moved
between case-sensitive and case-insensitive filesystems. The containing filename is canonical and must be
exactly `<archive-id>.journal.json`; renamed or duplicated identities are rejected. The loader
rejects unknown archive fields and verifies matching adventure identity and event count. See
`schemas/journal-archive.schema.json`, `journal-archives.md`, and `necessity-model.md`.


## Workspace settings

The browser workspace stores its selected adventure and future-project validator defaults in
`.adventure-graph/settings.json` below the workspace root. This file is not part of any adventure and
does not alter existing projects when its defaults change. Its canonical schema is documented in
`schemas/workspace-settings.schema.json`.

Workspace settings schema version 1 follows the same fail-closed evolution rule. The selected
adventure key and validator-defaults object may be absent in an older current-version file; missing
known values receive model defaults, malformed values fail, unknown values are rejected, and the next
save writes the complete current shape. The selected adventure is represented by a workspace-relative
source key. It may be null when no selection has been made or no loadable adventures exist. One loadable
project with no malformed project diagnostics is selected implicitly for convenience; several projects
without a saved selection open the catalog. A saved key that becomes unavailable is retained as an explicit stale selection, so the browser
requires the user to choose a replacement instead of silently falling back to another project.
