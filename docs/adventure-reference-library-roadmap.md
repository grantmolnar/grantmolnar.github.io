# Adventure reference library roadmap

## Status

The adventure reference library is an **accepted pre-beta product direction**. Adventure Graph will keep
encounters as the operational, clue-bearing units of play and add a separate authored library for
persistent people, places, organizations, objects, and other subjects that recur across encounters.

This roadmap commits the product boundary and beta intent. Phases 1 through 6 are complete: the exact
authored association design is fixture-backed; the domain, schema, persistence, commands, CLI recovery,
Author interface, Play retrieval, generated packets, and selective corpus use all preserve the accepted
reference boundary. Phase 7 has completed the whole-application local GM cold-read, responsive correction,
clean-wheel lifecycle, and installed-source convergence. Runtime event targeting remains deferred:
authored references do not change the first-beta journal contract. The accepted decision record and
evidence live in `adventure-reference-library-phase-1-design.md`,
`adventure-reference-library-phase-1-fixtures.json`,
`adventure-reference-library-phase-6-corpus-audit.md`, and
`adventure-reference-library-phase-7-cold-read.md`.

The reference feature is part of the accepted local beta source. Native Linux, Windows, and macOS artifact
builds plus real-platform launcher protocols remain external release evidence. The desktop pipeline remains
unchanged and must build all three artifacts from one accepted source revision before distribution.

The corpus follow-through is also complete. All thirteen authoritative example adventures have passed the
four-session extraction, voice, and coherence sequence; the source now contains 224 canonical references and
1,305 ordered encounter-local links. The final encounter-name ledger accepted four title-only
deconflictions, preserved all stable IDs and journals, reviewed eighteen remaining candidates, and left no
unresolved naming ambiguity. Further corpus work is maintenance rather than an unfinished reference-library
phase.

## Product boundary

Adventure Graph distinguishes two complementary authored concepts:

- An **encounter** is a playable locus of interaction. It may be centered on a person, place,
  organization, event, activity, or other scenario component. Encounters source clues, receive route and
  resilience analysis, and participate in table chronology.
- A **reference record** is reusable canonical information about an enduring subject that may matter in
  several encounters. It is not automatically a graph node, a visitable unit, or a source of graph
  connectivity.

This preserves the breadth of node-based scenario design without forcing every NPC, location, faction,
or object into encounter-shaped data merely to give the GM somewhere to write persistent information.
Interviewing Captain Vale may be an encounter; Captain Vale's recurring dossier is a reference record.
Exploring the Old Mill may be an encounter; the Old Mill's reusable description and inhabitants belong
in a place reference that several encounters may share.

## Accepted beta scope

The first beta-facing reference feature should provide:

- adventure-owned portable reference records with stable opaque identity;
- a small useful subject vocabulary covering at least people, places, organizations or factions,
  objects or assets, and other material;
- concise summary and detailed GM-facing authored prose;
- tags or keywords consistent with existing adventure search behavior;
- explicit links between encounters and zero or more reference records;
- generated backlinks from each reference to every linked encounter;
- Author views for browsing, creating, editing, linking, unlinking, and dependency-aware removal;
- contextual reference creation and linking from an encounter;
- Play-time access to the references linked to the focused encounter;
- global authored-material search and browser-local pinning that include references; and
- generated adventure-packet output containing a reference index and reference sheets.

The reference library travels with the adventure through ordinary copy, relocation, archive pairing,
campaign-owned import copies, and clean standalone export.

## Explicit first-version exclusions

The first beta version should not add:

- an untyped universal node replacing encounters;
- graph connectivity derived merely from reference links;
- automatic extraction of people or places from prose;
- automatic merging of similarly named references;
- live synchronization between references in separate adventures;
- campaign-level entity identity or cross-adventure entity reconciliation;
- a full faction, calendar, settlement, inventory, or world-management subsystem;
- direct clue or revelation subject links unless fixtures show a table-critical need;
- player-facing dossier fields unless the cold-read establishes a concrete workflow; or
- new runtime events targeting references merely because authored references exist.

Play-time changes such as altered allegiance, destruction, injury, ownership, or changed disposition
remain append-only notes and consequences in the existing journal for the first beta. A later design may
let those events target reference IDs so the application can assemble reference-specific history, but
that is a separate runtime contract.

## Representative fixtures

No schema should be accepted until it handles at least these fixtures cleanly:

1. **Recurring person.** One NPC appears in four encounters, has information that should be edited once,
   and changes allegiance during play.
2. **Shared place.** One location hosts three distinct encounters without requiring those encounters to
   duplicate geography, inhabitants, or sensory description.
3. **Distributed organization.** One faction operates through several people and places and is relevant
   to clues in several encounters.
4. **Recurring object.** One important object moves among encounters while its canonical description and
   properties remain stable.
5. **Reference-light adventure.** A small adventure remains valid with no references and incurs no
   needless authoring burden.
6. **Portable project.** The authored adventure, generated packet, journal archive, relocation flow, and
   clean export preserve reference identity and links.
7. **Dependency change.** Removing an encounter or reference exposes all affected links and fails closed
   until the author chooses a safe disposition.

The bundled corpus should supply concrete examples rather than synthetic records alone. The fixtures
must preserve each adventure's voice and should not create reference records for one-off names that are
clearer in encounter prose.

## Accepted Phase 1 decisions

The fixture review accepted the following first-version contract:

- references are adventure-owned records in one ordered top-level `references` array;
- new reference IDs are canonical UUIDv4 values and remain independent of displayed names;
- kinds are the closed set `person`, `place`, `organization`, `object`, and `other`;
- records contain `id`, `kind`, `title`, ordered `aliases`, `summary`, Markdown `content`, and ordered
  `tags`;
- encounters own ordered `reference_links` records containing `reference_id` and optional `context`;
- link records have no identity independent of their encounter, and backlinks are derived;
- array order supplies authored ordering without separate numeric positions;
- generated reference material groups people, places, organizations, objects, then other records while
  preserving authored order within each group;
- adventure source remains schema version 3 with additive omitted-field defaults and strict
  unknown-field rejection;
- journal archive schema remains version 1 because it still embeds a complete authored adventure
  snapshot;
- any reference or link edit changes the ordinary project revision through the existing canonical-byte
  fingerprint; and
- dependency-aware removal refuses linked changes until explicit cascade removes only the subordinate
  links described in the Phase 1 design.

Aliases participate in authored search. Duplicate IDs, malformed UUIDs, unsupported kinds, malformed
aliases or tags, dangling links, duplicate encounter/reference pairs, and unknown fields are errors.
Empty prose and ambiguous exposed names are warnings rather than structural failures.

The accepted shape is documented in `adventure-reference-library-phase-1-design.md`. Clue or revelation
subject links, reference-targeted runtime events, player-facing dossier prose, custom kinds, association
identity, and campaign reconciliation remain explicitly deferred.

## Implementation sequence

The work may span several sessions. Keep each tranche bounded and leave the repository green.

### Phase 1 — fixture and schema design — complete

Representative corpus-backed fixtures exercise a recurring person, shared place, distributed
organization, moving object, reference-light adventure, relocation and archive preservation, and
fail-closed removal. Four association shapes were compared; subordinate explicit link records on
encounters were accepted.

**Exit met:** `adventure-reference-library-phase-1-design.md` records the accepted domain and
file-format proposal, and `adventure-reference-library-phase-1-fixtures.json` preserves the evidence.
No runtime or UI implementation was added.

### Phase 2 — domain, schema, and persistence — complete

Immutable `Reference` and `ReferenceLink` values now extend the adventure domain, encounters own
ordered links, adventures expose a reference index, and the schema-version-3 reader and writer support
the additive fields with exact unknown-field rejection and sparse defaults. Validation reports
duplicate identities, dangling or repeated encounter links, empty prose, and ambiguous exposed names.
Archive snapshots preserve the complete shape, and reference or link changes use the ordinary project
revision. Existing bundled adventures remain valid reference-light inputs rather than receiving forced
records.

**Exit met:** populated and reference-light adventures round-trip canonically, sparse current-version
inputs default safely, archive snapshots preserve identities and links, and all corpus documents
validate against the published schemas.

### Phase 3 — application operations and CLI recovery surface — complete

Revision-aware application commands now create and edit references, append and remove contextual
encounter links, and perform dependency-aware reference and encounter removal. No separate reorder
command was needed: reference order and encounter-local link order remain append-authored order, and
unrelated edits preserve both. Duplicate links and missing unlink pairs fail closed. Reference cascade
removal deletes only the record and its encounter-owned links; encounter cascade removal deletes its
subordinate links while retaining all reference records. Known journals still block encounter removal.

The CLI exposes these application commands as recovery and automation surfaces. `list` and `inspect`
show identities, kinds, aliases, ordered links, derived backlinks, contexts, and removal projections;
`inspect --state PATH` adds journal blockers without making ordinary authored inspection depend on a
healthy companion journal. Generic validation presentation already reports the Phase 2 reference
diagnostics.

**Exit met:** the complete authored lifecycle is exercised without the browser through one canonical
application mutation path and regression-tested CLI workflows.

### Phase 4 — Author interface — complete

The browser now presents one adventure-owned reference library with kind filters rather than separate
domain silos. GMs can create, inspect, and edit stable reference records; browse aliases, tags, and
canonical prose; follow derived encounter backlinks; and search references through the ordinary Author
navigation filter. Encounter pages show ordered contextual links and support linking an existing record,
unlinking one pair, or creating and linking a new reference through one atomic revision-aware command.
Reference and encounter removal pages expose exact dependency projections and require explicit cascade
confirmation where subordinate links will change. Reference-light adventures receive restrained empty
states rather than required placeholder records.

**Exit met:** a GM can create and maintain recurring information efficiently from either the library or
an encounter without duplicating canonical prose or bypassing the application mutation path.

### Phase 5 — Play and generated packet integration — complete

Play now shows linked references beside the focused encounter in encounter-authored order, preserves each
link's local relevance text, and opens complete reference prose in an independently selected read-only
panel. Reference titles, aliases, summaries, prose, tags, and link contexts participate in authored-
material search, including records not linked to the focused encounter. Browser-local pins now use typed
encounter or reference bookmarks, migrate legacy encounter-ID arrays, discard stale values, and remain
bounded without entering authored or journal files.

Generated packets now contain a grouped `references/index.md`, one stable UUID-named sheet per reference,
derived encounter backlinks with local contexts, and ordered reference links on encounter sheets.
Reference-light adventures still omit the namespace. Opening, searching, focusing, or pinning reference
material appends no visit, operation, or other journal event and does not change the current or focused
encounter.

**Exit met:** the GM can reach relevant recurring information during table play without leaving Play mode
or recording spurious visits, and can publish the same material through stable generated packet paths.

### Phase 6 — corpus pass and usability audit — complete

The selective corpus pass retained only three records across two contrasting adventures: Theron Eiral
and The Sunseed in *The Concord of Aurelune*, and The Salt Wardens in *The Bell Beneath Harrowgate*.
Encounter-local links preserve procedure, stakes, and authored order without moving scene action into
the dossiers. *The Cauldron of Nine Silences* remains ledger-centralized and reference-light, while
*When the Swine Kneel* remains compact and reference-light. The rejected candidates demonstrate that
whole-adventure places, dynamic machinery, large comparative factions, and one-scene actors should not
be promoted merely because they are named.

The retained records were exercised through Author aliases and backlinks, Play linked cards, full-panel
retrieval, global search, typed pins, stable generated sheets, relocation, clean standalone export, and
an immutable journal archive snapshot. Reference interactions remained journal-neutral. The durable
evidence and every retained or rejected candidate appear in
`adventure-reference-library-phase-6-corpus-audit.md`.

**Exit met:** corpus evidence demonstrates both material retrieval value and deliberate restraint without
changing schema, journal semantics, campaign data, clue structure, or differentiated encounter voice.

### Phase 7 — beta convergence

**Local status:** complete; native platform signoff remains open.

The whole-application GM cold-read exercised fresh and populated workspaces, reference-light and populated
adventures, Author and Play retrieval, keyboard and compact layouts, both appearance themes, journal
neutrality, recovery, relocation, archive behavior, generated output, and the clean installed-wheel
lifecycle. One objective tablet-width top-bar overflow was corrected by hiding a redundant project-title
block below 1181 pixels and protected by a regression contract. The complete evidence is recorded in
`adventure-reference-library-phase-7-cold-read.md`.

The exact native PyInstaller build lock was unavailable in this execution environment, so no native
artifact was fabricated or represented as passing. Linux, Windows, and macOS native builds, aggregate
manifest verification, and real-platform manual protocols remain open.

**Local exit met:** reference support is part of the accepted beta source and clean wheel. **Distribution
exit open:** all supported native artifacts and manual platform evidence must identify the same source
revision.

## Interaction with other roadmaps

- **UI cleanup:** the local whole-application GM cold-read is complete. Real-platform frozen-launcher
  interaction remains part of native signoff rather than a second product-design pass.
- **Desktop distribution:** no redesign is expected. The existing launcher and native build pipeline
  package the revised application; all native artifacts must be rebuilt after the reference work.
- **Campaign graph:** implementation remains post-beta. Campaign-owned adventure copies will inherit
  adventure-local references as ordinary portable authored data. The provisional campaign design now
  gives persistent campaign entities their own stable identity and explicit bindings to those copied
  references, without live merging, and gives campaign chronology a display-independent absolute
  coordinate for encounter occurrences and external events with derived entity backlinks. Exact binding
  lifecycle and calendar-display details remain fixture decisions for the campaign workstream.
- **Technical debt:** correctness, safety, migration, and evidence defects may interrupt the work.
  Opportunistic cleanup should be recorded in the maintenance map rather than expanding a tranche.

## Beta exit statement

The local source now satisfies the reference-library beta criteria below. Adventure Graph should not begin external beta testing
through desktop bundles until the native artifact and manual-platform
evidence named in the beta-readiness roadmap are complete. A GM can:

1. keep recurring people, places, organizations, and objects in one canonical authored location;
2. link that material to every encounter where it matters;
3. retrieve it quickly during Play;
4. export and relocate the adventure without losing identity or links; and
5. understand that references support encounters but do not replace the clue-oriented encounter graph.
