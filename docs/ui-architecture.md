# User Interface Architecture

The loopback browser is a user interface, not an HTTP integration API. User-visible workflows are part
of the private-beta product contract; raw route paths, form-field names, hidden revision and CSRF
values, DOM structure, CSS selectors, and browser-local storage keys remain internal. Stable entity
identifiers preserve links across title edits within a release, while supported automation uses the
CLI and versioned JSON schemas.

## Status

This document records the architectural direction for a graphical Adventure Graph interface. It is
an implementation constraint and sequencing guide, not a commitment to a particular browser
framework.

## Problem

The command-line interface exposes the current capabilities accurately, but it is a poor primary
surface for long prose, relationship-heavy authoring, structural diagnosis, and live session use.
Those workflows need persistent context, multiline editing, synchronized views, and direct
navigation among encounters, leads, revelations, validation findings, and play history.

The solution must not move interface concerns into the domain or application layers. Adventure
Graph should gain a second interface adapter, not a second implementation of its behavior.

## Decision

Adventure Graph will add a local-first web interface while retaining the CLI as a supported adapter.
Both interfaces will invoke the same application use cases. The web interface will bind to the local
machine and operate on the existing authored adventure, active journal, generated documents, and
journal archives.

The target dependency direction is:

```text
CLI adapter          Web adapter
      \                /
       \              /
        application use cases
                  |
                domain

infrastructure adapters -> application ports

bootstrap -> interfaces + infrastructure + application
```

The arrows above mean "depends on." The composition root may import every layer in order to wire the
process. No other module receives that exception.

## Architectural rules

### The web interface is an adapter

The web layer may own:

- HTTP routes and request parsing;
- HTML templates and browser assets;
- form validation used only to improve interaction;
- page, panel, modal, and navigation state;
- Markdown editor integration;
- graph layout and selection behavior; and
- conversion between application result objects and rendered responses.

The web layer may not own:

- adventure validation policy;
- dependency analysis for edits, renames, or removals;
- journal legality or projection rules;
- archive compatibility rules;
- authoritative identifier validation;
- persistence coordination; or
- generated-document semantics.

The CLI follows the same rule. It parses arguments, invokes a use case, and presents the result. It
must not remain the only place where a supported operation is coordinated.

### Framework types stop at the interface boundary

Application and domain functions must not accept or return HTTP requests, responses, HTML fragments,
form objects, browser events, route parameters, CLI namespaces, terminal streams, or framework
session objects.

Interfaces translate their inputs into plain typed commands and queries. Application use cases
return plain typed result objects. Presentation is an outward concern.

### Domain rules remain authoritative

The browser may perform non-authoritative checks such as warning about an empty title or unsaved
text. Every operation must still pass through the same application and domain validation used by
the CLI. Client-side checks cannot create a second version of the rules.

### UI state is not authored state

The following do not belong in `adventure.json` or `play-state.json`:

- graph coordinates;
- the focused Play encounter and independently selected Play reference;
- typed browser-local Play pins for encounters and references;
- recent Play encounter-focus history;
- collapsed panels and open Play drawers;
- active tabs;
- editor cursor positions;
- recent-project lists;
- local drafts;
- window dimensions; and
- interface preferences.

Ephemeral state should remain in browser storage. Durable project-specific UI state may later use a
sidecar under `.adventure-graph/`, with a separate schema and no effect on domain equality,
validation, rendering, or journal compatibility.

Disclosure state follows this boundary. Author navigation groups and Play workspace sections may
remember whether the user expanded them, but the preference remains browser-local, is subordinate to
accessible HTML disclosure semantics, and may be temporarily overridden by search without rewriting
the stored preference. A single reusable web-adapter behavior should own this interaction rather than
each page inventing a separate collapse mechanism.

### Play may enter authoring without owning authored data

Play is a projection and recording layer over the authored adventure, not a second authoring model.
Convenience actions opened from Play must invoke the ordinary revision-aware authoring use cases. An
encounter, lead, revelation, or reference created there is an ordinary authored entity with the same
ontology and lifecycle as one created before play, and is committed to `adventure.json`; the return
flow restores Play focus without appending a journal operation, changing the current visit, unlocking
an encounter, or treating the edit as table history. Creation timing is not currently persisted.
Future authoring provenance belongs in separate metadata or revision history, not in a Play-specific
entity subtype.

Contextual revelation creation should continue into clue creation so the new conclusion acquires an
authored source instead of becoming an accidental orphan. Contextual reference creation should create
and link one adventure-owned record atomically. Local return targets must remain canonical and
fail-closed.

### Existing files remain the source of truth

The graphical interface does not introduce a database or a proprietary project format. The
existing versioned JSON files remain authoritative. Generated Markdown remains disposable output.
Journal archives remain immutable historical values.

## Current application seam

The formerly planned orchestration extraction is complete. Domain modules are independent of persistence
and presentation. Shared authoring, play, archive, reporting, and workspace behavior sits behind application
commands, queries, and narrow project ports. CLI and web adapters translate their own inputs and present the
same transport-neutral results.

`bootstrap.py` is now a deliberately small installed-entry-point dispatcher and expected-error boundary.
Package-root CLI command modules and `web_composition.py` are process adapters that wire application use
cases to local infrastructure. They may combine outward layers for composition, but canonical business
rules and coordinated commit semantics do not live there.

Future extraction is conditional rather than scheduled. Split an adapter or rendering module only when a
new route family, entity family, event kind, or second adapter demonstrates duplicated orchestration or a
separate reason to change. Line count alone is not an architectural trigger. The maintained distinction is:

- domain and application transformations are pure where practical;
- persistence adapters own JSON and filesystem behavior;
- coordinated commits remain infrastructure behavior behind application-facing ports; and
- composition roots own object construction, configuration, process startup, and adapter dispatch only.

## Application boundary

### Commands

Commands request a state change. Representative compatibility-era type names are:

```text
UpdateEncounter
CreateClue
RenameEntity
RemoveEntity
StartVisit
SpotClue
EstablishRevelation
RecordVisitNote
RecordEncounterConsequence
ArchiveJournal
RestoreJournalArchive
DeleteJournalArchive
RenderDocuments
```

A command contains domain-oriented values, not interface concepts. For example, `UpdateEncounter` may
carry an identifier, edited fields, and an expected project revision. It does not carry a form,
request, or path supplied by a route handler.

Command results should expose facts needed by any interface, such as:

- the updated entity;
- the new project revision;
- validation changes;
- rewritten identifiers;
- affected journals;
- dependency impacts;
- warnings; and
- refusal details.

They should not prescribe a toast, redirect, status badge, or modal.

### Queries

Queries return read models designed for use rather than persistence. Representative compatibility-era type names are:

```text
GetAdventureOverview
GetEncounterDetail
GetReferenceDetail
GetRevelationDetail
GetClueDetail
GetRevelationCoverage
GetValidationDashboard
GetRunDashboard
ListJournalArchives
GetPlaySummary
```

A read model may combine information from several domain values. An encounter detail result may include the
encounter, leads sourced there, incoming revelations, reachable destinations, validation findings, and
recorded consequences. This is legitimate application-level projection so long as it remains plain
structured data and does not contain HTML or browser-specific state.

Read models should not be persisted as a new source of truth.

The public interface calls authored `Clue` records **leads**. Compatibility-era command and query class
names such as `CreateClue`, `SpotClue`, and `GetClueDetail` remain internal identifiers because renaming them
would add churn without changing the product model. Presentation copy must use Lead/Leads and must never
rewrite authored prose globally.

### Ports

Application use cases may depend on narrow protocols for effects they require. Ports are added only as
real use cases demand them. Current port responsibilities include:

- reading a project snapshot;
- committing an authored adventure and any rewritten journals atomically;
- committing an active journal;
- listing, reading, creating, restoring, and deleting journal archives;
- writing generated documents; and
- obtaining the current time for archive metadata.

Infrastructure implements these ports using the existing JSON serializers and the crash-recoverable
local transaction layer. Application code must not import `Path`-bound stores merely because the
first adapter is local.

A single catch-all repository or `WorkspaceService` should be avoided if it grows into an interface-
shaped facade. Prefer use cases with the narrow capabilities they actually need. Shared data-loading
machinery may still be composed behind small ports.

## Project revisions and safe editing

A long-lived graphical editor creates a concurrency problem that a one-shot CLI rarely encounters:
the files may change after a page loads. Every mutable project snapshot should therefore carry an
opaque revision token derived by the infrastructure adapter from the relevant source files.

A modifying command supplies the revision it edited. The commit refuses if the on-disk revision no
longer matches. The interface then presents a reload or comparison flow rather than silently
clobbering external changes.

Revision tokens are application boundary values, not domain fields. Domain entities remain unaware
of files, hashes, modification times, and browser sessions.

## Drafts and saving

Long prose needs recovery from browser closure or accidental navigation. Draft preservation and
committed authoring are different operations:

- browser-local drafts may be updated continuously;
- committing to the project remains an explicit use case;
- drafts are never treated as validated authored content; and
- successful commits clear the corresponding local draft.

The first implementation should use explicit Save and `Ctrl+S`. Automatic domain commits after every
keystroke would make validation, revision handling, and journal compatibility harder to understand.

## Journal correction semantics

The run interface will turn journal operations into low-friction clicks, so accidental entries need
an honest correction path. Schema version 4 retains the explicit operation boundary introduced in
version 3. Compound table actions, such as a visit with immediate clues and notes, share one
operation number.

A correction appends an `operation_voided` audit event targeting only the latest still-active content
operation. The original events remain in history but are excluded from the current-state projection.
Repeated corrections therefore walk backward without arbitrary retroactive editing or silent journal
rewrites. The CLI and browser Journal page invoke the same revision-aware application command.

This shared domain behavior removes the prerequisite that blocked the Recovery workspace.

## Product workspaces

The interface should organize behavior around GM workflows rather than reproduce the command list as
buttons.

### Adventure

The authoring workspace provides persistent navigation among encounters, references, revelations, and
clues; spacious Markdown editing; contextual creation; relationship inspection; and dependency-aware
refactoring. The reference library is one adventure-owned collection with kind filters, not five domain
silos. Encounter links carry only encounter-local relevance; canonical reference prose remains owned by
the reference record. Identifier changes remain explicit operations with an impact preview.

### Structure

The structural workspace synchronizes:

- the encounter graph;
- revelation coverage by clue and source encounter; and
- validation findings, including reachability and minimum-cut witnesses.

A diagnostic may prefill a proposed structural action, but it must not invent authored prose or apply
a repair without confirmation.

### Run

The session workspace shows the current visit, discoverable clues, available destinations,
revelation progress, encounter notes, and recent events. One flexible note composer serves ordinary
GM recording; older durable-consequence records remain visible only as legacy persistent notes. It
invokes the same play-state use cases as the CLI.

This workspace is the proven lower-level runtime and recovery surface. The table-centered Play
mode is specified and sequenced in [the Play mode roadmap](play-mode-semantics.md).

### Reports and history

Reports are application read models rendered for browser use, printing, and export. Archive controls
show immutable journal snapshots and use the same compatibility and confirmation rules as other
adapters.

## Framework and packaging constraints

The first implementation should favor a small server-rendered web layer with focused client-side
code. Rich client behavior is justified for the Markdown editor and graph, not as a reason to
reimplement project state in JavaScript.

UI dependencies should be optional. Installing and using the existing CLI should not require the web
server, editor, or graph packages. The package may expose an extra such as `adventure-graph[ui]` once
the dependency set is chosen.

The browser server must bind to loopback by default. Authored Markdown must be sanitized before HTML
rendering even though the application is local.

No framework choice in this document weakens the layer rules. Replacing the web framework should not
require changes to the domain or application behavior.

## Testing strategy

### Domain and application

Existing unit and property tests remain authoritative. New use cases receive tests using in-memory or
purpose-built fake ports. These tests should verify behavior, refusal paths, revision conflicts, and
result values without starting a server.

### Infrastructure

Adapter tests verify versioned JSON, revision calculation, transaction commit points, repeatable
rollback and startup recovery, archive operations, and generated output against temporary
directories.

### Interface

Web tests verify request translation and response presentation. A separate Playwright/Chromium gate
executes a small set of complete browser workflows against the real loopback application; static HTML,
CSS, and JavaScript inventory assertions are not substitutes for visible behavior. The executable gate is
kept outside the ordinary Python loop so application tests remain fast and the runtime package acquires no
browser dependency. Browser workflows should not duplicate every domain test.

Critical end-to-end workflows include:

1. open a local project;
2. select and edit an encounter;
3. save against the expected revision;
4. observe updated relationships and validation;
5. encounter a revision conflict without data loss; and
6. recover an unsaved browser draft.

Architecture tests must continue to enforce inward dependencies. The web package may import
application contracts but must not import infrastructure implementations. Bootstrap remains the only
place that wires the two together.

### Corpus and property contracts

Bundled-adventure tests distinguish four kinds of evidence. Structural contracts assert heading presence
and authored order. Semantic contracts require durable concepts while allowing sentence-level voice edits.
Editorial phrase locks preserve exact language only when wording itself controls procedure, law, ritual,
identity, or a consciously frozen line. Generated-packet contracts may remain byte-exact because those
artifacts are deterministic projections of canonical source. Shared helpers make the intended contract type
visible at the assertion site rather than hiding it behind undifferentiated substring checks.

Property tests live beside the feature layer they exercise and use the `test_*_properties.py` naming
contract. Dependency-light deterministic targets omit those modules entirely; the release-oriented property
and validation targets require Hypothesis and fail immediately when it is unavailable. Current property
evidence covers exact graph cuts, canonical adventure and play-journal persistence, bounded dice
normalization and roll validation, and append-only projection/correction invariants.

A bounded mutation campaign should target high-risk behavior rather than report a repository-wide score
without review. Meaningful survivors receive focused tests at the owning layer; equivalent or redundant
mutants are recorded with reasons. The current campaign covers graph traversal and cuts, dice bounds and
validation, Play projection and tracking, persisted numeric contracts, and transaction recovery.

The desktop launcher separates portable automation from native interaction evidence. All logic outside the
Tk window is unit- and smoke-tested. Native directory choosers, default-browser integration, real window
lifecycle, display scaling, operating-system trust prompts, and signing behavior remain a concise manual
protocol on each built platform.

## Implementation status

Milestones 1 through 8 are complete.

The shared application boundary now consists of:

- `AuthoringProject`, `AuthoringSnapshot`, and opaque `ProjectRevision` values in a project-level
  application module;
- `GetAdventureOverview`, `GetEncounterDetail`, `GetRevelationDetail`, `GetClueDetail`, and
  `GetStructuralOverview` queries returning transport-neutral navigation, relationship, coverage,
  graph-edge, dependency, and validation context;
- `UpdateEncounter`, `CreateClue`, and `CreateRevelation`, which accept domain-oriented values and an
  expected project revision;
- `GetPlayJournalStatus`, `GetRunDashboard`, session-aware play projections, and narrow
  revision-aware commands for sessions, correction, visits, found and missed lead outcomes, revelation
  establishment and judgments, explicit unlocks, notes, consequences, and significant rolls;
- `GetReportPacket`, `PublishReportPacket`, `ListJournalArchives`, `GetJournalArchiveDetail`, and
  narrow revision-aware archive mutations;
- `LocalAuthoringProject`, `LocalPlayJournalProject`, `LocalGeneratedReportProject`, and
  `LocalJournalArchiveProject`, which implement the application ports over the existing JSON files,
  generated directory, and archive catalog with opaque revision tokens; and
- CLI and web adapters that receive these use cases only through bootstrap composition.

The web interface uses the standard-library WSGI server and packaged CSS and JavaScript, so it
adds no runtime dependency. The web package owns routes, form parsing, CSRF validation, browser
local-storage drafts, HTML, safe prose rendering, browser security headers, and responsive layout.
Presentation vocabulary is supplied explicitly by UI copy and application error messages. Renderers do
not perform global word substitution over arbitrary text, because authored titles and notes may
legitimately contain compatibility-era words such as `Clue` and must remain verbatim.
Shared page chrome and the Play, Run, Journal, Reports, and Archives renderers live in focused
interface modules; `rendering.py` retains the established page-renderer imports as a compatibility
facade. Play mode consumes the existing transport-neutral run projection for canonical facts, including the
reference records and derived encounter backlinks needed for table retrieval. Its focused encounter,
independently selected reference, typed pins, recent encounter history, search text, and drawer state
remain browser concerns. Generated packet assembly remains an application projection, while stable
filesystem publication remains infrastructure behavior. The web layer does not import infrastructure
implementations, parse source JSON, coordinate domain behavior, or persist selected reference state.
Static architecture checks and Import Linter enforce the same boundary for both interfaces.

## Delivery sequence

### Milestone 1: application seam — complete

- Define the minimum command, query, result, and port types needed by one authoring workflow.
- Extract encounter-detail loading and encounter-update coordination from `bootstrap.py`.
- Make the existing CLI invoke the extracted use case.
- Add revision-aware local persistence for that workflow.
- Strengthen architecture tests so interface packages cannot import infrastructure adapters.

The milestone is complete when CLI behavior is preserved and the use case can be exercised without
CLI parsing or real filesystem access.

### Milestone 2: read-only shell — complete

- Added the local WSGI package and bootstrap composition wiring.
- Opened a project and rendered its overview and validation status.
- Added persistent navigation among encounters, revelations, and clues.
- Rendered encounter, revelation, clue, relationship, and validation read models.
- Established the responsive three-column visual vocabulary and packaged browser assets.
- Restricted hosting to loopback and escaped authored prose before conservative Markdown rendering.

The milestone is intentionally read-only. No authored mutation enters through the web adapter.

### Milestone 3: first complete authoring slice — complete

Implemented the reference workflow:

```text
open project
-> select an encounter
-> edit long-form content
-> save safely
-> see relationships and validation update
```

The encounter editor now includes browser-local drafts, explicit stale-draft recovery, CSRF-protected
form submission, revision-conflict handling that preserves submitted prose, keyboard save, safe
redirect-after-commit behavior, and focused application, interface, and composition coverage.

### Milestone 4: structural authoring — complete

- Added contextual clue and revelation creation through narrow revision-aware application commands.
- Added read-only dependency previews for rename, move, removal, cascade effects, and known journal
  references.
- Added a revelation coverage matrix showing clue and distinct-source deficits against policy.
- Added a clickable SVG encounter graph with minimum-cut partitions and witnessed cut edges highlighted.
- Added repair links that prefill, but never apply, proposed structural additions.

The application supplies authored edges, coverage, validation diagnoses, and dependency impacts as
plain typed data. The web adapter alone chooses graph coordinates, SVG markup, table layout, URLs,
and form defaults.

### Reference-library Author interface — complete

- Added one unified Author library for people, places, organizations, objects, and other recurring
  subjects, with kind filters and restrained reference-light empty states.
- Added stable-identity create, detail, and edit surfaces for title, kind, aliases, summary, Markdown
  content, and tags.
- Added encounter-local ordered links, derived read-only backlinks, contextual link and unlink actions,
  and an atomic create-and-link application command for the compound browser workflow.
- Included reference titles, aliases, prose, and tags in the existing Author navigation search without
  persisting a second index.
- Added exact reference and encounter removal previews with explicit cascade confirmation; encounter
  cascade removes links but retains the referenced records.
- Preserved browser drafts, CSRF, optimistic revisions, output escaping, and the capability-contract
  composition boundary.

The application owns identity generation, atomicity, duplicate-link refusal, ordering, dependency
projection, validation, and commits. The web adapter owns kind-filter links, forms, responsive layout,
redirect notices, and search metadata.

### Reference-library Play retrieval and generated packets — complete

- Extended the transport-neutral run projection with ordered reference records and derived encounter
  backlinks rather than making the web adapter infer relationships from persisted JSON.
- Added linked-reference cards to the focused encounter in authored link order, including local relevance
  text, and a complete independently selected read-only reference panel that preserves encounter focus
  and the canonical current visit.
- Extended Play search across reference titles, aliases, summaries, Markdown prose, tags, and encounter-
  local link contexts, including unlinked records.
- Replaced encounter-only browser pins with bounded typed encounter/reference bookmarks; the asset layer
  migrates legacy encounter-ID arrays and discards malformed, duplicate, or stale values.
- Added generated `references/index.md`, stable UUID-named reference sheets, derived encounter backlinks,
  and ordered reference sections on encounter sheets while keeping reference-light packets sparse.
- Preserved the journal boundary: selecting, searching, opening, closing, focusing, or pinning a reference
  is read-only interface state and appends no play operation.

The application owns reference lookup, backlink derivation, generated-document ordering, stable packet
paths, and reference-light omission. The web adapter owns the selected-reference query parameter, typed
local-storage pins, HTML composition, responsive presentation, and safe Markdown rendering.

### Reference-library corpus evidence — complete

The representative corpus pass retained two Aurelune records and one Harrowgate organization while
leaving a ledger-heavy heist and a compact civic investigation reference-light. The interface therefore
continues to treat references as optional retrieval aids rather than a completeness taxonomy. Author and
Play render the same canonical records and encounter-owned contexts; specialized ledgers remain separate
adventure documentation, and no browser layer infers entities from names or promotes them automatically.

### Milestone 5: journal correction semantics — complete

- Added explicit operation numbers to schema-version-3 play journals.
- Grouped compound visit and revelation/unlock actions into atomic operations.
- Added append-only correction events that void only the latest still-active content operation.
- Added conservative migrations from schema versions 1 and 2.
- Added a revision-aware play-journal application port, query, and correction command.
- Added matching CLI and browser Journal translations with conflict refusal and preserved reasons.
- Kept raw history visible while projecting only active operations.

### Milestone 6: run workspace — complete

- Added `GetRunDashboard`, a transport-neutral query over authored content and the current active
  projection.
- Added narrow revision-aware commands for visits, lead discovery, revelation establishment,
  explicit unlocks, visit notes, and durable encounter consequences.
- Added a live browser workspace with current-encounter material, discoverable leads, available
  destinations, revelation progress, encounter notes, legacy consequence display, recent operations,
  and atomic correction.
- Preserved rejected form values on domain errors and stale revisions; successful writes use
  redirect-after-commit behavior.
- Routed the corresponding adventure-aware CLI play commands through the same application use cases.

The application decides what is available, spotted, established, locked, and correctable. The web
adapter owns only layout, forms, CSRF handling, browser drafts, and presentation.

### Milestone 7: reports and archives — complete

- Added `GetReportPacket` and `PublishReportPacket` over a revision-aware generated-report port.
- Added a browser report reader with packet navigation, safe Markdown rendering, individual
  downloads, print-specific layout, and explicit publication to `generated/`.
- Added a revision-aware archive catalog covering the active journal, immutable archive values, and
  the aggregate archive-directory revision.
- Added archive creation with atomic journal reset, snapshot comparison, compatibility diagnosis,
  restore into an empty journal, and exact-identifier confirmed deletion.
- Kept generated paths, archive filenames, atomic file replacement, and directory scanning inside
  infrastructure adapters.
- Added browser integration coverage for publication, downloads, archive creation, restore,
  refusal, and permanent deletion.

### Milestone 8: multi-adventure workspace and validator settings — complete

- Added transport-neutral workspace catalog, selection, creation, and default-setting use cases.
- Added a local workspace adapter with bounded discovery across root sources, immediate-child projects, and one visible collection directory.
- Added a persistent shell above the selected adventure adapter without moving project-specific
  authoring, Run, Journal, Reports, or Archives logic into the shell.
- Added guided creation of canonical project files and one distinguished start encounter.
- Added independent workspace-default and per-adventure validator-policy forms with separate
  optimistic revisions.
- Kept directory discovery, workspace-relative keys, and `.adventure-graph/settings.json` inside the
  infrastructure adapter.

The staged interaction and graph-presentation cleanup is also complete. Direct-edit entry continues
to use the established revision-aware forms; appearance remains browser-local; and the encounter graph now
uses wrapped full titles, dynamic boxes, boundary-aware curved edges, pan, zoom, connection focus, and
an expanded inspection workspace. Coordinates, SVG markup, and interaction remain interface concerns.
The local GM cold-read and browser coherence audit are complete. Destructive authored-entity operations
remain deliberate future product work rather than unfinished workspace plumbing.

### Play mode shell and navigation — complete

- Added an explicit Author / Play context switch without forking project or journal state.
- Added a navigation-first `/play` route over the injected `GetRunDashboard` query.
- Added a chronological route rail grouped by explicit sessions and labeled current and focused
  visits independently.
- Added focused-encounter reading, including authored prose, legacy persistent records when present,
  clue progress, revelation status, and destination availability, without appending journal events.
- Replaced the viewport-bound reference/notes split with six peer disclosure sections for opening
  description, GM orientation, encounter material, linked references, encounter-local clues and paths,
  and encounter notes. Each section owns only browser-local disclosure and scroll state; the page remains
  scrollable and prose measure is constrained inside prose content rather than across the dashboard.
- Added browser-local pins, recent focus, broad authored-material search, keyboard navigation, and
  responsive tablet drawers.
- Preserved the existing `/run` workspace as the canonical recording and recovery surface during
  the staged replacement.

The application remains authoritative for session, visit, clue, revelation, encounter-availability, and
consequence facts. The web adapter chooses route links, search indexing, responsive layout, and
local-storage keys. Browsing a locked encounter is therefore legal and non-canonical; entering it remains
an explicit application command subject to projection rules.

### Play mode encounter-running vertical slice — complete

- Added injected Play commands for explicit session boundaries, clue misses, revelation judgments,
  visit notes, consequences, and compound transitions.
- Added `TransitionPlayVisit` as one revision-aware application service that validates all phases and
  commits one journal write; the web adapter does not coordinate partial writes.
- Added encounter-context forms for entering, unlocking, clue outcomes, revelation state, and consequences.
- Added a browser-local visit notebook whose autosave never writes canonical state and whose explicit
  commit or transition does.
- Added a table transition form that orders source-visit notes, clue outcomes, revelation
  establishments and automatic unlocks, consequences, and an optional destination under one
  correctable operation number.
- Preserved submitted form values and notebook content after revision conflicts and domain refusals.

The browser remains a translator over application commands. It owns form layout, local-storage draft
keys, and redirect notices; the application owns operation ordering, reference validation,
availability, atomicity, and optimistic revision checks. The existing Recovery workspace remains a
recovery surface rather than a hidden dependency of Play mode.

### Play mode operational ledgers and exports — complete

- Added `GetPlayLedgers` as one side-effect-free application query over the authored adventure and
  active journal projection.
- Added encounter, clue, revelation, narrative, and player-safe read models with whole-playthrough and
  latest-explicit-session scopes.
- Kept session scope honest: it selects activity for review while current status continues to come
  from the complete playthrough projection.
- Added standalone browser ledger pages, clean print treatment, and derived Markdown downloads.
- Added end-session review links into the latest-session views.
- Constructed the player-safe recap from an explicit event allowlist rather than passing hidden GM
  material to a presentation template.

The application module owns scope selection, status derivation, safe-event selection, and Markdown
content. The web adapter owns tabs, links, response headers, and print layout. No generated ledger is
persisted or read back into the application.

## Established implementation boundary

All eight completed authoring-interface milestones, the staged GM-interface cleanup, and the
completed Play navigation, encounter-running, and operational-ledger milestones have preserved the intended sequence: reusable application use cases are
extracted before a browser route depends on them. The web adapter receives injected commands and
queries, while bootstrap remains the only module that combines interface and infrastructure
implementations.

Future work should continue this incremental pattern rather than create a general UI-shaped service
or migrate every CLI command speculatively. Each new workspace must first establish shared domain or
application semantics, then add sibling CLI and browser translations as needed.

## Rail responsibility contract

The desktop interface uses the same directional model in Author and Play whenever the concepts
overlap:

- the **left rail** answers *where can I go and how do I find authored material?* It owns mode-local
  workspace navigation, encounter/revelation/clue retrieval, and—during ordinary Play—the recorded
  chronological route;
- the **center workspace** owns the document or operation currently being performed; and
- the **right rail** answers *what is true or useful about the current context?* It owns project or
  table status, browser-local shortcuts such as pins and recent focus, current-visit actions, dice,
  and other contextual utilities.

Changing main screens inside Author or Play must not replace those rails with unrelated navigation.
A screen may add context-specific modules, but the mode switcher and authored-material retrieval
remain in the same rail. Empty contextual modules must collapse completely; in particular, the
browser-local pin shelf is absent until at least one encounter is pinned.

Author and Play may present different controls because their operations differ, but shared concepts
keep their position. **Find authored material** therefore belongs on the left in both modes. The
right rail is not a second navigation menu and should not contain links whose ordinary effect is to
strand the user outside the current mode chrome.
