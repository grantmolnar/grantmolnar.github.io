# Adventure reference library — Phase 1 design

## Status

Phase 1 remains the fixture-backed domain and file-format decision record. Phase 2 has implemented
the runtime models, schemas, persistence, archive preservation, validation, and revision contracts.
Application commands, browser views, Play access, and generated output remain later-phase work.

The representative evidence is recorded in
`adventure-reference-library-phase-1-fixtures.json`. It uses existing corpus material wherever the
current adventures genuinely exercise the feature:

- Cora Pike in *The Witch of Blackbriar Hall* supplies a recurring person whose allegiance changes in
  the existing demonstrated playthrough;
- Blackbriar Hall and its grounds supply one place shared by three distinct encounters;
- Saint Mercy House supplies an organization expressed through staff, dependents, records, routes, and
  several places;
- the Aulonite bronze seal in *The Princess on the Salt Road* supplies a recurring object whose custody
  and use vary by encounter; and
- *When the Swine Kneel* remains deliberately reference-light with no reference records.

The fixtures also specify relocation, export, archive, revision, and dependency-removal behavior. They
are design evidence, not canonical schema-version-3 adventure files.

## Association alternatives

### Candidate A — bare reference IDs on encounters

```json
{
  "reference_ids": ["8e2bd3ba-20fb-456c-9c73-cb9bab481e26"]
}
```

This is the smallest persisted shape and places ownership on the encounter, where contextual linking
occurs. It cannot explain why the subject matters in this encounter. The recurring-person,
distributed-organization, and moving-object fixtures all benefit from a brief encounter-specific note;
adding one later would require replacing the scalar array or maintaining parallel metadata.

### Candidate B — encounter IDs on references

```json
{
  "encounter_ids": ["house-of-blue-lamps", "red-bridge"]
}
```

This makes the desired backlink authored rather than derived. Contextual linking from an encounter
would mutate a remote reference record, encounter-local ordering would be unavailable, and deleting an
encounter would require scanning and rewriting every reference. It also makes the canonical reference
record own facts about where it is used rather than facts about the enduring subject.

### Candidate C — top-level association collection

```json
{
  "reference_links": [
    {
      "encounter_id": "red-bridge",
      "reference_id": "8e2bd3ba-20fb-456c-9c73-cb9bab481e26",
      "context": "The seal can authenticate orders or expose the escort."
    }
  ]
}
```

This supports metadata and symmetrical querying but introduces a third top-level collection, global
association ordering, duplicate-pair rules, and pressure to give links their own identity. None of the
Phase 1 fixtures needs an association lifecycle independent of its encounter.

### Accepted design — subordinate link records on encounters

```json
{
  "reference_links": [
    {
      "reference_id": "8e2bd3ba-20fb-456c-9c73-cb9bab481e26",
      "context": "The seal can authenticate orders or expose the escort."
    }
  ]
}
```

Each encounter owns an ordered array of explicit link records. A link has no independent identity and
contains only `reference_id` plus optional encounter-specific `context`. The application derives each
reference's backlinks by scanning encounter links.

This preserves the accepted statement that encounters explicitly link to references, supports the Play
workflow without duplicating canonical prose, and avoids a general association subsystem. Reference
links never create graph edges and never become clue sources.

## Accepted reference record

The adventure gains a top-level ordered `references` array. Each record contains:

- `id`: required canonical UUIDv4 text, generated once and never inferred from the title;
- `kind`: required closed value `person`, `place`, `organization`, `object`, or `other`;
- `title`: required trimmed nonempty display name;
- `aliases`: ordered alternate names, defaulting to an empty array;
- `summary`: concise GM-facing orientation, defaulting to an empty string;
- `content`: detailed GM-facing Markdown, defaulting to an empty string;
- `tags`: ordered trimmed search labels, defaulting to an empty array.

References use UUIDv4 rather than title-derived slugs because the accepted product direction requires
opaque portable identity and the feature has no legacy reference identifiers to preserve. Titles and
aliases may change without rewriting links.

The five-value kind vocabulary is closed for the first version. `organization` includes factions;
`object` includes assets; `other` plus tags covers unusual subjects. Custom kind labels are deferred
until corpus use demonstrates behavior that filtering and tags cannot express.

A title-only reference is structurally legal so contextual creation stays inexpensive. Validation should
warn when both summary and content are empty, but it should not force placeholder prose.

## Ordering and generated output

Array order is authored order. There are no persisted numeric positions.

- The top-level `references` array determines order within each kind.
- Each encounter's `reference_links` array determines contextual Play and encounter-sheet order.
- Generated reference indexes and sheets group kinds in this fixed order: people, places,
  organizations, objects, other.
- Within each group, generated output preserves top-level authored order.
- Derived backlinks use adventure encounter order; each backlink includes its encounter-specific context
  when nonempty.

Aliases participate in authored-material search but do not create duplicate reference sheets or graph
identity.

## Validation diagnostics

The Phase 2 implementation distinguishes malformed data from structurally valid but weak authoring.

Errors:

- a reference ID is not canonical UUIDv4 text;
- reference IDs are duplicated;
- a reference kind is unsupported;
- a title is empty or untrimmed;
- aliases or tags contain empty, untrimmed, or case-insensitive duplicate values;
- an alias duplicates the record title without regard to case;
- an encounter link targets an unknown reference;
- an encounter links the same reference more than once; or
- an unknown field occurs at the reference or link boundary.

Warnings:

- both reference summary and content are empty; or
- two records expose the same title or alias without regard to case. Distinct people and places may
  legitimately share names, so this is not an error.

A blank `context` is valid and canonicalizes to an empty string. Unknown persisted fields continue to
fail closed.

## Schema and compatibility decision

Adventure source remains schema version 3. The change is additive and follows the existing
current-version compatibility rule:

- omitted top-level `references` defaults to an empty array;
- omitted encounter `reference_links` defaults to an empty array;
- omitted aliases, summary, content, tags, and link context receive their documented empty defaults;
- current writers serialize the complete accepted shape; and
- older binaries reject the newly named fields rather than loading and erasing them.

No legacy content migration is required. Bundled adventures may be migrated selectively during the
corpus phase; reference-light adventures remain semantically unchanged. Journal archive schema version 1
also remains unchanged because its envelope semantics do not change: an archive continues to embed a
complete authored adventure snapshot, which now may contain the additive schema-version-3 fields.

## Revision, relocation, export, and archive effects

Project revisions already fingerprint the canonical adventure bytes together with related journal bytes.
Any reference or link edit therefore changes the project revision automatically; no second reference
revision is introduced. The first save by a current writer may also change bytes by writing explicit
empty arrays for a sparse older document.

Relocation preserves the same canonical files and therefore preserves reference IDs and links. Clean
standalone export copies the complete adventure-owned library without name-based merging. New journal
archives embed references and links in the adventure snapshot; old archives remain immutable historical
values. Generated packets record the ordinary source revision and may use reference IDs for stable
internal anchors.

## Dependency-aware removal

Reference links are authored dependencies subordinate to encounters.

- Removing a linked reference without explicit cascade is refused and reports every encounter link.
- Cascading reference removal deletes only those links and the reference record. It never deletes an
  encounter or rewrites journal history.
- Removing an encounter with reference links without explicit cascade is refused alongside its existing
  clue and revelation dependencies.
- Cascading encounter removal deletes its subordinate links but retains the reference records.
- Existing journal rules remain authoritative: a known journal mentioning an encounter still blocks its
  removal even when cascade was requested.
- Current journals do not target references, so they do not block reference removal. Immutable archives
  retain the reference in their own embedded historical snapshot.

The browser and CLI must expose the same dependency preview and canonical mutation commands in later
phases.

## Explicit deferrals

Phase 1 does not add clue or revelation subject links, reference-targeted runtime events, player-facing
reference prose, custom kinds, cross-adventure synchronization, campaign reconciliation, association
identity, or reference-derived graph connectivity.
