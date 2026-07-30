# Campaign graph initiative

## Status and timing

Campaign design is a planned post-first-beta initiative. It is documented now so that ordinary
adventure development, packaging, and later refactoring do not accidentally assume that an adventure
must always be Adventure Graph's top-level authored object. It does not change the 0.10.0 adventure
schemas, workspace layout, launcher contract, or current beta scope.

Implementation should begin after the first adventure-only beta has produced concrete feedback about
graph navigation, clue authoring, revelation coverage, terminology, and table use. The campaign work
should reuse accepted adventure behavior rather than duplicating untested assumptions at a second
scale.

## Product intent

Adventure Graph should support a campaign as a clue-driven, node-based scenario whose playable nodes
are adventures rather than encounters.

The campaign layer is not merely a flowchart or ordered list of adventures. It should preserve the
same two complementary structural views that make an adventure useful:

- a **campaign clue list**, organized by the adventure entry or other explicit campaign source where
  the clue can be learned; and
- a **campaign revelation list**, organized by the conclusion, opportunity, destination, threat, or
  campaign truth supported by those clues.

Campaign connectivity is therefore derived from authored clues and revelations. A campaign clue found
in one adventure may support a revelation that exposes, makes meaningful, or unlocks another
adventure. The application may project that relationship as an adventure-to-adventure edge, but an
arbitrary persisted edge is not a substitute for the clue that makes the transition intelligible at
the table.

Example:

1. The party completes an adventure in the flooded archive.
2. Several campaign clues there support the revelation that the drowned observatory can be entered at
   low tide.
3. Establishing that revelation makes the observatory adventure available.

The GM can still choose a different route, introduce an adventure directly, or improvise a campaign
clue. The graph is preparation and operational guidance, not a script.

## Aggregate and identity model

A campaign is a separate authored aggregate with stable identity. Its eventual persisted form should
include, at minimum:

- stable `campaign_id` independent of the campaign title;
- campaign title, premise, description, discovery tags, and validation policy;
- stable campaign-entry identities for the adventures placed in the campaign;
- campaign clues and campaign revelations with stable identities;
- mappings from campaign revelations to the adventure entries, consequences, or conclusions they
  expose or unlock; and
- campaign-level notes and structural metadata that do not alter the imported adventure payload.

A campaign adventure entry and the contained adventure have different identities:

- the **adventure ID** identifies the portable authored adventure; and
- the **campaign-entry ID** identifies one placement or instance of that adventure in one campaign.

This distinction must be preserved even when a campaign contains only one copy of an adventure. It
allows the same portable adventure to appear in multiple campaigns, allows deliberate repeated or
variant placements inside one campaign, and prevents campaign topology from being coupled to an
adventure title or directory name.

An adventure remains a complete, independently valid aggregate whether or not it has been imported
into a campaign. Campaign support must not make standalone `adventure.json` projects second-class or
require existing projects to migrate before they can still be authored and played.

## Persistent campaign entities and adventure compatibility

A campaign needs persistent people, places, organizations, objects, and other subjects that can recur
across several imported adventures. The campaign should own a reference library that follows the same
stable-identity and initial kind vocabulary as adventure references, but campaign identity must remain
separate from every adventure-local reference identity.

Each campaign-owned adventure copy preserves its ordinary `references` and encounter
`reference_links` exactly as portable adventure data. The campaign relates a persistent entity to those
records through explicit campaign-owned bindings containing, at minimum:

- the stable campaign-entity ID;
- the campaign-entry ID; and
- the adventure-reference ID inside that entry's owned snapshot.

Bindings are correspondence records, not live inheritance. They must not rewrite imported adventures,
merge prose, create graph edges, or infer identity from names and aliases. One campaign entity may bind
to references in several adventure entries, and one imported adventure remains runnable and exportable
without the campaign layer. Exact provenance from a prior campaign export may support deliberate
reconciliation, but ordinary import must fail open to an unbound local reference rather than guess.

The campaign reference owns cross-adventure baseline material and campaign-wide preparation. Each
adventure reference owns the local presentation needed by that standalone adventure. Campaign runtime
changes and run outcomes belong to append-only campaign history associated with the campaign entity;
they do not silently mutate either layer of authored reference prose. Campaign-wide backlinks to
adventure entries, encounters, calendar entries, clues, and run outcomes are derived from explicit
bindings and links.

## Campaign clues and revelations

Campaign clues are first-class authored records, not labels attached directly to graph arrows. The
initial model should parallel the proven adventure model while allowing campaign-specific language
and validation:

- each clue has stable identity;
- each clue has one explicit source;
- each clue has explicit campaign-revelation support, while the initial clue-to-revelation cardinality remains open;
- each revelation can be supported by clues from several adventure entries;
- a revelation may expose or unlock one or more adventure entries, establish a campaign truth, warn of
  a threat, or support a campaign-level conclusion; and
- campaign validation measures revelation support and route fragility without assuming that every
  campaign should have the same clue thresholds as an individual adventure.

A campaign clue has one explicit campaign-layer source reference. When the source is an imported
adventure, that reference should normally descend to the most useful delivery scale:

- an **encounter placement**, identified by campaign-entry ID plus an encounter ID in the
  campaign-owned adventure snapshot;
- an **adventure outcome placement**, identified by campaign-entry ID when the clue arises from the
  adventure as a whole, its completion, or an adjudicated ending rather than one encounter; or
- another explicit **campaign source**, such as downtime, a faction, a patron, travel, a calendar, or a
  world event.

The first implementation must not represent non-adventure sources as fake adventures merely to satisfy
the graph model. It should provide a small explicit campaign-source record or defer a source category
until that record has a clear domain contract. Encounter placements must be validated against the
campaign-owned snapshot, not against an external source directory that may later move or change.

This is a downward operational placement, not a conversion into an ordinary adventure clue. Campaign
clues belong to the campaign overlay and should not be silently inserted into an imported adventure's
`clues` collection. Encounter clues explain movement and understanding within an adventure; campaign
clues explain movement and understanding among adventures and across the campaign as a whole. The same
encounter may therefore display both kinds, but their identities, revelations, validation, runtime
judgments, import ownership, and export behavior remain separate.

A campaign author may deliberately use an existing encounter clue as the fictional basis for a
campaign clue, but the application must not infer or duplicate that relationship automatically. If the
relationship needs to remain explicit, a future overlay record may reference the adventure clue's
stable ID as provenance while retaining a distinct campaign-clue identity.

The UI should provide both structural projections:

- **By source:** open an adventure entry and see its campaign clues, grouped further by encounter,
  adventure outcome, or other source where useful.
- **By revelation:** open a campaign revelation and see all supporting clues, their source adventures
  and encounter placements, and any adventure entries or consequences the revelation exposes.

A campaign graph view may draw projected edges between adventure entries, but selecting an edge should
show the clue or revelation path that justifies it. The product should not leave the GM with an
unexplained arrow.

## Layer handoff and revelation effects

No new revelation kind is required merely because a campaign clue is placed inside an encounter. The
clue's source reference answers **where the clue can be learned**; the campaign revelation answers
**what the clue supports at campaign scale**. Treating encounter placement as a revelation kind would
mix source geometry with semantic consequence.

Campaign revelations should instead have explicit typed effects or targets. The initial set may cover:

- exposing or unlocking one or more campaign adventure entries;
- establishing a campaign truth, opportunity, threat, or conclusion without unlocking an entry; and
- applying a campaign-scale consequence or availability change once the runtime model exists.

The exact persisted shape should be chosen during Phase 1, but a typed effect collection is preferable
to overloading one nullable target field as the number of campaign consequences grows.

A campaign revelation should not normally unlock a raw encounter inside another adventure. Once a
campaign entry becomes available and play enters that adventure, the adventure's own start encounters,
clues, and revelations take over. This preserves adventure portability and avoids coupling the campaign
overlay to internal route details in a destination adventure.

If real campaigns later require several deliberate ways to enter one adventure, add an explicit,
portable **adventure entry-point** contract to the adventure format and let a campaign effect select one
of those entry points. Do not solve that problem by storing an untyped pointer to an arbitrary internal
encounter.

## Import ownership and synchronization

The first campaign version should use **copy semantics**, not live filesystem links.

Importing an adventure should:

1. validate the source as a complete supported Adventure Graph project;
2. copy the authored adventure into campaign-managed storage;
3. preserve its adventure identity unless a documented identity collision requires an explicit choice;
4. assign a fresh campaign-entry identity;
5. create no campaign clues or revelations merely by guessing from encounter-level content; and
6. leave the original standalone project untouched.

The campaign owns the imported snapshot. Editing it inside the campaign does not silently edit the
original project, and editing the original does not silently alter the campaign. This makes archives,
reproduction, collaboration, and table use predictable when the original directory is moved,
unmounted, or changed.

A later version may add an explicit **update from source** or **compare with source** workflow. That
workflow must be revision-aware, show conflicts, and distinguish adventure-content changes from
campaign-overlay changes. Automatic bidirectional synchronization is out of scope until real use shows
that explicit copies are inadequate.

## Export and portability

Exporting a campaign adventure entry should always be able to produce an ordinary standalone Adventure
Graph project:

1. copy the contained authored adventure;
2. preserve its adventure identity and authored content;
3. exclude the campaign's active journal and unrelated campaign data;
4. validate the exported project as a standalone adventure; and
5. never require Adventure Graph campaign support merely to reopen or play the export.

Campaign-only clues, revelations, placement notes, and consequences cannot be written into the
standalone adventure silently. The eventual export UI should offer two deliberate products:

- a **clean standalone adventure**, containing only the portable adventure project; and
- an **adventure with campaign companion metadata**, containing the standalone project plus an
  optional, versioned companion record for campaign hooks and placement context.

The companion record's exact filename and schema should be chosen during implementation rather than
frozen by this roadmap. Importing such a package may offer to restore compatible campaign-facing clues
and context, but the adventure itself remains valid without the companion record.

## Authored and runtime state boundaries

Campaign authorship and campaign play should remain separate, as adventure authorship and adventure
play are now.

The campaign authored surface should contain:

- campaign entries and their contained adventure snapshots;
- campaign clues and revelations;
- revelation-to-adventure availability mappings;
- campaign-level descriptions, factions, fronts, timelines, and preparation notes; and
- validation policy.

The campaign runtime surface should record campaign-scale facts such as:

- which adventure entries are unavailable, available, active, completed, abandoned, bypassed, or
  revisitable;
- which campaign clues were learned or missed;
- which campaign revelations were established, foreclosed, or reopened;
- cross-adventure consequences and durable world changes;
- campaign chronology and between-adventure notes; and
- which campaign entry and adventure run produced a recorded result.

Detailed encounter visits, encounter notes, encounter clues, and adventure revelations remain in the
relevant adventure play journal. The campaign journal may reference or summarize an adventure run, but
it should not flatten every encounter event into one enormous campaign event stream.

A campaign entry may eventually retain several archived runs of the same adventure. The campaign must
identify which run supplied campaign-level outcomes rather than assuming that an adventure can be
played only once.

## Absolute campaign chronology and calendar projections

The campaign should provide one absolute chronology capable of indexing encounter occurrences,
adventure milestones, and external world events. Canonical chronology must not depend on a displayed
month name, era label, or locale-specific rendering. The first design should use a stable absolute
coordinate, initially an integer day index with an optional within-day position or explicit precision,
and let campaign-owned calendar definitions render that coordinate into one or more setting calendars.

Portable encounters do not acquire campaign dates. A campaign-owned calendar entry instead has stable
identity and may target:

- an encounter occurrence through campaign-entry ID plus encounter ID;
- an adventure-wide milestone or outcome; or
- an external campaign event with its own authored title and description.

Calendar entries may explicitly link to persistent campaign entities. Entity timelines and backlinks
are derived from those links; no date label, title match, or prose extraction establishes identity. An
external event may serve as an explicit campaign-clue source without becoming a fake adventure or
encounter.

Authored chronology and runtime history remain separate. Fixed events, forecasts, schedules, and
contingent plans belong to campaign authorship. What actually occurred, including delays, cancellations,
rescheduling, and realized outcomes, belongs to append-only campaign runtime history and may cite the
authored entry it realizes or supersedes. This separation preserves counterfactual preparation and an
auditable play record.

Phase 1 must exercise exact dates, ranges, uncertain precision, durations, simultaneous events,
rescheduling, recurring events, multiple display calendars for one absolute coordinate, backlinks to
several entities, and a clean adventure export that contains no campaign chronology. Specialized month,
season, festival, faction, settlement, or world-simulation features remain later extensions.

## Reuse and architectural boundary

Reuse the existing graph algorithms, identity patterns, validation concepts, revision-aware commands,
projections, and visual interaction where they genuinely apply. Do not force encounters and adventures
into one vague universal domain entity.

The intended layering is:

- generic graph primitives and algorithms where behavior is truly scale-independent;
- an encounter graph with encounter, clue, and revelation invariants;
- a campaign graph with adventure-entry, campaign-clue, and campaign-revelation invariants; and
- shared adapter components only when their inputs and behavior can remain explicit.

The campaign initiative is a test of the current backend seams. If an abstraction cannot express both
scales without weakening domain language or validation, prefer two clear domain models over one
prematurely generic model.

## User experience direction

Campaign support should add a top-level campaign context without replacing the existing adventure
workspace. A likely workflow is:

1. create or open a campaign;
2. import an existing adventure or create a new adventure entry;
3. author campaign revelations and the clues supplied by each adventure entry;
4. inspect clue coverage and projected routes across the campaign;
5. open an entry into the existing adventure Author or Play interface; and
6. return to the campaign overview with campaign context preserved.

The campaign UI should make import and export ordinary visible actions, not technical recovery
commands. It should also preserve a future capability boundary: a play-focused edition may restrict
campaign or adventure authoring controls without changing the portable data format or requiring a
separate backend implementation.

## Validation principles

The campaign validator should eventually detect at least:

- revelations with insufficient independent support;
- adventure entries that can be reached only through one fragile clue or source;
- clues whose source entry is missing;
- clues that support missing revelations;
- revelations that expose missing adventure entries;
- duplicate or colliding stable identities;
- campaign entries whose contained adventure is invalid;
- cycles or dead ends only when they violate an explicit campaign policy, not merely because they exist;
- imported snapshots whose provenance or companion metadata is malformed; and
- runtime references to campaign entries, clues, revelations, or adventure runs that do not exist in
  the paired authored snapshot.

Validation should distinguish structural warnings from creation failures, just as the adventure
application now permits an almost-blank authored starting point while providing useful guidance.

## Staged implementation roadmap

### Phase 0 — learn from the adventure beta

Complete the first adventure-only beta and collect specific findings about clue authoring, revelation
coverage, graph inspection, navigation, improvisation, archives, and Play mode. Classify which findings
are adventure-specific and which should shape both graph scales.

### Phase 1 — domain and format design

Define campaign, campaign-entry, campaign-reference, reference-binding, campaign-clue,
campaign-revelation, calendar-entry, absolute-coordinate, display-calendar, and campaign-runtime
identities. Specify ownership, copy import, clean export, companion metadata, chronology, revision,
collision, and archive semantics. Add schemas and migration policy only after representative campaign
fixtures exercise entity correspondence, calendar indexing, backlinks, and the ordinary campaign graph.

### Phase 2 — headless campaign operations

Implement creation, validation, import, export, entry replacement, campaign clue and revelation
commands, and structural projections without a browser dependency. Prove that existing standalone
adventures remain unchanged and that an import/export round trip preserves the adventure payload.

### Phase 3 — campaign authoring interface

Add campaign roster, campaign overview, by-source clue view, by-revelation support view, projected
adventure graph, contextual creation, and direct entry into the existing adventure Author interface.

### Phase 4 — campaign play and chronology

Add campaign sessions or arcs, adventure availability and completion state, campaign clue and
revelation judgments, cross-adventure consequences, run selection, and return-safe navigation between
the campaign and an active adventure.

### Phase 5 — interoperability and hardening

Exercise identity collisions, multiple instances of one adventure, repeated adventure runs, archive
pairing, project relocation, malformed companion metadata, explicit source updates, and imported
adventures from older supported formats. Add campaign-level reports and player-safe recap projections.

### Phase 6 — campaign beta

Run a separate beta centered on campaign preparation and multi-adventure play. Do not treat successful
adventure-only beta feedback as evidence that the campaign-scale clue model or UI is already proven.

## Decisions recorded now

The following decisions should be treated as the initiative's starting constraints unless concrete
implementation evidence requires reopening them:

- campaign nodes are campaign entries containing portable adventures;
- campaign structure is clue- and revelation-oriented, not merely a persisted adjacency graph;
- campaign clues may be placed at specific encounters but remain campaign-owned and separate from encounter clues;
- a campaign entry has identity distinct from the contained adventure;
- imported adventures use copy semantics in the first version;
- standalone adventures remain complete and valid outside campaigns;
- clean standalone export is mandatory;
- optional campaign companion metadata must be explicit and versioned;
- detailed encounter play remains in adventure journals;
- campaign runtime records campaign-scale knowledge, availability, chronology, and consequences; and
- implementation follows the first adventure beta rather than delaying that beta.

## Open design questions for implementation

The complete question set and working recommendations are recorded in
[`graph-scale-design-notebook.md`](graph-scale-design-notebook.md). Those recommendations are explicitly
provisional and are not accepted campaign contracts. The following summary remains intentionally
deferred until representative fixtures and beta findings can inform it:

- the exact source-reference union for encounter placement, adventure outcomes, and non-adventure campaign sources;
- the initial typed campaign-revelation effects and whether one revelation may unlock several alternative
  adventure entries with additional conditions;
- how an explicit update-from-source workflow presents and resolves conflicts;
- how much campaign companion metadata should accompany a default export;
- whether campaign validation defaults should scale with campaign length or use named preparation
  profiles; and
- how campaign chronology relates several archived runs of the same adventure entry.
