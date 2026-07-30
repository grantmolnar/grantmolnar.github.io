# Architecture

## Purpose

Adventure Graph keeps authored scenario structure, structural validation, generated reference
material, and actual-play state separate. The package is deliberately small: immutable dataclasses,
standard-library JSON persistence, exact graph algorithms, and Markdown generation.

## Domain model

### Adventure metadata

An adventure carries reusable discovery metadata separately from its encounter graph. Structured
facets cover genre, game system, setting, inclusive group-size and level ranges, and combat
intensity. Open-ended keywords preserve themes, formats, and play styles without forcing every useful
description into a permanent schema field. These tags support catalog discovery and generated
reference material; they do not affect structural validation or runtime state.

### Encounter

An encounter is a playable unit: a location, person, event, faction, or eventually an entire
adventure at campaign scale. The model therefore avoids encounter-specific fields that would make
higher-level reuse awkward. An encounter is necessary by default and may be marked optional independently
of its start or end role. It also carries an opening view for the characters' first impression.

### Revelation

A revelation is a conclusion the players can reach. It is necessary by default and may be marked
optional independently of any encounter it unlocks. Separating revelations from encounters preserves the
distinction between:

- discovering a destination; and
- learning a fact that changes the players' understanding or options.

### Clue

A clue belongs to exactly one source encounter and supports exactly one revelation. This gives two exact,
automatically generated duals:

```text
clue list:       source encounter -> clues -> revelations
revelation list: revelation <- clues <- source encounters
```

The first is the outgoing authoring/runtime view. The second is the incoming audit view used for the
Three Clue Rule.

### Play state

Play state is not mixed into authored content. It is an append-only journal of typed events:

- encounter visits;
- clues first spotted during a visit;
- revelations explicitly established, optionally with their evidentiary clue basis;
- encounter unlocks;
- visit notes;
- durable encounter consequences; and
- append-only operation corrections.

Every event belongs to an explicit operation. Compound table actions share one operation number, and
a correction appends an audit event that voids only the latest active content operation. Visits are
a derived view rather than the persistence unit. This preserves the true chronology,
keeps clue discovery distinct from player interpretation, and allows current state to be rebuilt and
validated deterministically. See `runtime-state.md` for the event and projection invariants.

### Journal archives

A journal archive freezes a complete play state together with the adventure snapshot against which
it was recorded. Archives are immutable historical values, not related live journals: later
authoring operations do not rewrite them. Restoring an archive projects its journal against the
current adventure and refuses incompatible history. Archive/reset uses a crash-recoverable local multi-file
transaction. Restoration replaces only the active journal and leaves the immutable archive untouched, so
a partial write cannot destroy the historical copy.

## Validation

Validation proceeds in layers so malformed references do not contaminate graph diagnostics:

1. identifier uniqueness;
2. clue and revelation referential integrity;
3. revelation support counts and source diversity;
4. incoming locator coverage for non-start encounters;
5. encounter outgoing clue and destination diversity;
6. directed reachability from start encounters; and
7. necessary-encounter edge connectivity.

### Encounter graph

A directed encounter edge `A -> B` exists when a clue at encounter A supports a revelation that unlocks encounter B.
Non-encounter revelations do not create encounter edges.

Directed reachability answers whether the authored information flow can reach every necessary encounter
from the start set. An optional encounter with authored incoming clues but no directed route produces a
warning rather than an error.

Resilience is computed on the **simple undirected projection** of this graph. Multiple clues from A
to B collapse to one structural edge. This is intentional: three clues all traveling across the same
pair of encounters provide clue redundancy, but they do not provide three independent routes between two
regions of the adventure.

The package computes exact terminal edge connectivity using unit-capacity maximum flow between all
pairs of necessary encounters. Optional encounters remain available as intermediate routes, but a one-edge
optional spur does not lower the resilience of the necessary structure. The residual graph supplies
an exact minimum-cut witness: two encounter partitions and the simple edges crossing between them.
Adventure graphs are small enough that this transparent implementation is preferable to adding a
graph-library dependency.

Validation then maps the graph witness back into authored concepts. For every unused encounter pair across
the cut, it chooses the more useful clue direction, preferring an existing necessary revelation that
unlocks the target, a non-end source, and a source with fewer outgoing destinations. These
ranked candidates are deliberately structural: they identify where a clue can strengthen the graph,
but they do not invent clue content or assert that every candidate makes narrative sense.

The diagnostic states how many additional distinct encounter pairs must cross the witnessed partition to
bring that necessary-encounter cut up to policy. It does not claim that those edits complete validation: once the cut is
strengthened, another cut can become globally minimal, so the adventure must be revalidated.

## Authoring lifecycle

Authoring operations are immutable transformations over the complete `Adventure` value. Titles are
user-facing presentation; identifiers are durable machine identity. New adventures receive opaque
UUID identity. Nested authored records receive readable identifiers from their initial titles, but
subsequent
title edits preserve those identifiers. Ordinary authoring therefore does not rewrite authored
references, play journals, routes, or browser draft keys merely because prose changed.

Internal identifier-renaming and journal-remapping functions remain focused migration primitives
rather
than user operations. Structural edits, clue moves, and removals still project every known related
journal against the proposed adventure before commit. A change is refused if an event would become
invalid—for example, if a spotted clue moved away from its recorded visit or a visited start encounter
became unavailable.

Removal performs authored dependency analysis before persistence. Encounter cascades remove clues sourced
there and clear revelation destinations; revelation cascades remove supporting clues. Cascades never
erase play events, so referenced entities still block removal. This includes persistent references named
by chronological reference-note events.

The authoring store commits the adventure and all affected journals through the local write-ahead
transaction layer. New payloads and original-byte backups are fsynced before replacement. A process
interruption before the committed marker is rolled back on the next canonical read; interruption
after that marker retains the complete new revision and finishes cleanup. This remains a local,
single-writer filesystem transaction rather than a distributed lock; additional journals must be
passed with `--state` so they can be validated or rewritten.

Canonical JSON decoders mirror every schema object boundary. Omitted known fields may receive
schema-documented defaults, but unknown keys raise a source-specific unsupported-field error before a
domain value is built. Malformed known values produce a separate source-specific diagnostic. This
prevents an older current-version writer from loading and then silently erasing data it cannot
preserve.

## Layering

```text
adventure_graph.domain
    models, graph algorithms, validation

adventure_graph.application
    authoring commands, project queries, document generation, play-state use cases

adventure_graph.infrastructure
    adventure, play-journal, and archive JSON; crash-recoverable local writes; generated output

adventure_graph.interfaces
    CLI argument definitions, plain-text presentation, and the local authoring web adapter

adventure_graph.cli_*_commands
    command-line orchestration over application use cases and local adapters

adventure_graph.web_composition
    local adapter wiring for workspace and selected-adventure browser applications

adventure_graph.bootstrap
    minimal CLI process dispatch and expected error translation

adventure_graph.desktop
    native launcher composition, remembered workspace, browser opening, and server ownership
```

Layer package initializers are intentionally empty of runtime exports. Internal code and tests import the module that owns each value or use case; the pre-beta 0.7.0 cleanup removed the former `domain.models` and aggregate web-rendering compatibility modules.

Dependency direction is inward. Package-root process-adapter modules are the only modules expected to combine interfaces, infrastructure, and application use cases. `bootstrap.py` remains the installed CLI entry point and a deliberately small dispatcher; `cli_*_commands.py` contain terminal-command orchestration, and `web_composition.py` contains browser wiring. The installed console command and `python -m adventure_graph` both enter through `bootstrap.py`. The separate package-root `desktop.py` composition root owns the native launcher lifecycle while reusing `web_composition.py`; it is permitted to combine the desktop interface, local workspace adapter, and loopback server without moving those concerns inward.

Canonical mutations at both process adapters cross an application command and an application-facing
project port. CLI note recording therefore loads the adventure and journal together; archive deletion
loads the adventure, active journal, and archive catalog together; and `init` executes the dedicated
starter-project command through `LocalProjectInitializer`. Browser writes use equivalent injected
command contracts. Static architecture coverage rejects direct imports of canonical persistence
writers from every CLI command module and browser module.

Actual-play application logic is divided by reason to change. `play_tracking.py` is the cohesive command surface; its private pending-operation owner assigns final sequence and operation metadata while compound table actions are assembled. `play_journal_validation.py` owns append-only journal invariants; `play_projection.py` derives current state and narrative records; and `play_errors.py` defines the shared application error. Projection and validation do not import the command facade, preventing a circular dependency without relying on package-level re-export barrels.

The test architecture follows the same boundaries. Shared in-memory ports model optimistic concurrency, a single WSGI harness owns transport construction, and feature modules are organized by behavior rather than by one large adapter surface. Static tests cap review units before they become grab bags and prevent low-level WSGI setup from being copied back into feature tests. Filesystem, workspace, CLI, and bundled-adventure integration suites remain separate because each exercises a distinct composition boundary.

The reusable authoring seam now includes entity-detail and structural-overview queries, plus the
revision-aware `UpdateEncounter`, `CreateClue`, and `CreateRevelation` commands through an
`AuthoringProject` port. Structural read models contain coverage, unique authored encounter edges,
validation diagnoses, and dependency impacts as plain data. Graph coordinates, HTML, forms, and
repair-link presentation remain in the web adapter.

The local-file implementation remains an infrastructure adapter. Package-root composition modules
inject application queries and commands into CLI and web adapters; neither interface imports the
local adapter directly. Desktop launcher settings are a separate infrastructure value stored in the
user's platform configuration directory. They contain only the remembered workspace path and never
become part of an adventure workspace, authored document, play journal, or application bundle. CLI orchestration remains outside the application layer until a second
adapter demonstrates a reusable use case that can be expressed without local paths or terminal
presentation. See `backend-maintenance-map.md` for the current pressure points,
`ui-architecture.md` for the browser boundary, and `ui-usage.md` for the current browser surface.

## Encounters and reusable references

Encounters remain the operational clue-bearing units of an adventure. They may be centered on people,
places, organizations, events, activities, or other scenario components, but persistent fictional
subjects are not forced into the graph merely to store reusable prose.

The accepted pre-beta reference-library direction adds separate adventure-owned records for recurring
people, places, organizations, objects, and other subjects. Each reference has opaque UUIDv4 identity,
a closed first-version kind, title, aliases, concise summary, detailed Markdown content, and tags.
References live in one ordered adventure collection.

Encounters own ordered subordinate link records. Each link names one reference and may carry a brief
encounter-specific context note; it has no independent identity. The application derives backlinks by
scanning encounter links. This ownership supports contextual Author and Play workflows while keeping
canonical subject prose on the reference. Reference associations do not create graph connectivity or
replace clue and revelation structure.

The additive persisted fields remain within adventure schema version 3. Omitted collections and optional
fields receive empty defaults, current writers emit the complete shape, and older binaries fail closed
on fields they do not understand. Journal archives continue to embed the complete adventure snapshot.

Revision-aware application commands own reference creation, editing, linking, unlinking, and removal.
The CLI calls those commands rather than mutating persisted objects directly, and the Author browser
reuses the same operations. Dependency projections are transport-neutral read models: reference previews
derive encounter backlinks and cascade effects, while encounter previews include subordinate reference
links and any explicitly loaded journal blockers. The Play run projection likewise exposes ordered
references, derived encounter backlinks, and active chronological notes grouped by stable reference
identity. Selected-reference state and typed pins remain browser-only; appending a reference note is a
separate revision-aware application command that writes `reference_note_recorded` without mutating
authored prose.
Generated-document assembly owns grouped indexes, stable UUID-named sheets, and ordered contextual links,
while infrastructure only publishes those derived paths. Ordinary encounter edits preserve links. No
separate association identity, revision stream, or reorder mechanism exists.

See `adventure-reference-library-phase-1-design.md` for the accepted tradeoffs and
`adventure-reference-library-roadmap.md` for implementation sequencing.

## Extension path

The planned campaign layer reuses the proven graph algorithms and clue/revelation projections without
pretending that an adventure is an encounter with different prose. A campaign is a separate aggregate
whose nodes are campaign entries containing portable adventures. Campaign clues originate from an
adventure entry or another explicit campaign source and may be placed at a particular encounter inside
the campaign-owned adventure snapshot without becoming part of that adventure's own clue collection.
They support campaign revelations and may thereby expose or unlock other adventure entries. Any
projected adventure-to-adventure edge must remain traceable to those authored clues and revelations.
Encounter placement belongs to the clue source reference; campaign consequences belong to typed
revelation effects rather than to a special descent revelation kind.

Persistent campaign people, places, organizations, objects, and other subjects should remain
campaign-owned entities with stable identities. Campaign-owned bindings may associate them explicitly
with adventure-local references inside imported adventure copies; they must not infer identity from
names or live-merge records across aggregate boundaries. Campaign chronology should similarly be a
campaign-owned structure using a display-independent absolute coordinate to index encounter occurrences
and external events, with explicit entity associations and derived backlinks. Authored schedules remain
separate from append-only runtime occurrence history.

The campaign and encounter models should share scale-independent graph primitives, identity patterns,
validation concepts, and adapter components where their contracts genuinely coincide. They should
retain separate domain entities and invariants where campaign entries, campaign clues, campaign entities,
absolute chronology, campaign runtime, import ownership, or export portability differ from encounter
play. See `campaign-graph-roadmap.md` for the recorded product and architectural constraints.
