# Local Web Interface

## Status

Adventure Graph includes a local interface for browsing and editing an adventure, inspecting
structure, maintaining recurring reference material, creating leads and revelations, navigating an
adventure at the table, recording a live session, reviewing or correcting the active play journal,
reading and publishing reports, and managing immutable journal archives. This is the primary GM-facing surface. The CLI remains
available for developers, automation, advanced moves and removals, and recovery workflows.

## Interface vocabulary

The GM-facing browser and desktop interface calls authored clue records **leads**. Existing JSON fields,
URLs, Python types, event names, CLI commands, and stable filenames continue to use `clue`; this keeps
all beta adventures and playthroughs compatible. The same **lead** vocabulary now applies to player-safe recaps, so the application uses one
neutral term for prepared information and information the players have discovered.

The browser currently supports:

- workspace-level adventure discovery, selection, guided project creation, canonical adventure import/export, and identity-routed playthrough import;
- workspace defaults and per-adventure validator-policy editing;
- a global Help page explaining node-based preparation, the Author and Play loops, core terminology,
  further reading, and the project's independent status;
- revision-aware adventure, encounter, reference, revelation, and lead editing;
- one adventure-owned reference library with kind filtering, aliases, Markdown content, tags, derived
  encounter backlinks, contextual link and unlink actions, and explicit cascade previews;
- Author navigation filtering across encounter, reference, revelation, and lead titles, with reference
  aliases and prose included in reference matches;
- encounter opening views and start/end roles;
- contextual lead and revelation creation;
- revelation coverage by lead count and distinct source encounter;
- an interactive encounter graph with wrapped titles, dynamic sizing, minimum-cut highlighting, and dense-graph controls;
- validation findings and prefilled structural repair links;
- read-only dependency previews for title-change, move, and removal effects;
- raw journal operation history with revision-aware latest-operation correction;
- a navigation-first Play workspace with chronological route history, independent focused-encounter
  reading, linked and globally searchable reference material, typed browser-local encounter/reference
  pins, recent encounter focus, keyboard shortcuts, and tablet drawers;
- a lower-level Recovery console for visits, lead discovery, revelation establishment, explicit unlocks,
  encounter notes, and recent operation history;
- a Reports workspace for long-form reading, Markdown download, printing, and packet generation; and
- an Archives workspace for playthrough import/export, snapshot comparison, restore, and exact-confirmation deletion.

Adventure, encounter, reference, revelation, and lead title edits preserve durable internal
identifiers and therefore require no journal remapping. Internal identifiers remain transport values in
URLs and form payloads but are not presented as GM-facing labels. Reference and encounter removal use
browser dependency previews and explicit cascade confirmation; other advanced moves and destructive
repairs remain developer CLI workflows.

The application-wide **Help** destination remains available even when no adventure is selected. It
defines encounters, leads, and revelations; explains how Author mode prepares possibilities and how
Play mode follows the table; and links to Justin Alexander's Node-Based Scenario Design sequence and
*So You Want to Be a Game Master*. The page also states that Adventure Graph is an independent,
unaffiliated project and displays the installed application version with privacy-conscious beta-feedback
guidance.

The overview treats **Play adventure** as the primary GM action. A persistent **Author / Play**
switch changes working context without changing files or journal state. Author pages retain their
left-navigation authored-material filter, including reference aliases and prose; Play search covers
encounters, leads, revelations, references, and encounter-local reference context. Filesystem paths,
revision hashes, and diagnostic codes are intentionally absent from ordinary browser chrome.
Protected-save notices and validation headings are phrased in GM-facing language,
while the underlying values remain available to developer tools and persisted contracts.

## Start the interface

Install the package once from the unpacked source checkout:

```bash
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install .
adventure-graph ui examples
```

For your own material, pass a workspace directory or a project directory containing
`adventure.json`:

```bash
adventure-graph ui path/to/adventure-workspace
adventure-graph ui path/to/adventure-workspace/my-adventure
```

The command starts a local server at `http://127.0.0.1:8765/` and opens the default browser. Use a
different loopback port or suppress browser launch with:

```bash
adventure-graph ui path/to/adventure-workspace --port 9000 --no-browser
```

The server accepts only `127.0.0.1` or `localhost`. It also rejects requests whose HTTP `Host`
authority is not one of those names, with an optional valid port. Proxy forwarding headers are ignored:
reverse proxies, alternate aliases, IPv6 loopback, LAN exposure, and hosted-service deployment are not
supported by the private beta. Open the exact address printed by the command. Press `Ctrl+C` in the
launching terminal to stop it. A project directory containing `adventure.json` opens as a one-project
workspace. You may also pass the canonical `adventure.json` file explicitly; its containing directory
becomes the workspace root. Root-level `<name>.adventure.json` files are valid for file-oriented CLI
commands but are not browser workspace projects.

The beta workspace layout is deliberately small:

```text
adventure-workspace/
├── .adventure-graph/settings.json       # created by the browser
├── adventure.json                       # optional root project
└── another-adventure/
    ├── adventure.json
    ├── play-state.json
    ├── generated/
    └── archives/
```

Discovery checks only `adventure.json` at the workspace root and `adventure.json` inside visible direct
child directories. It does not recurse into collection directories, generated output, archives, hidden
directories, or symlinked directories. A canonical project that cannot be decoded remains visible in
the Adventures catalog under **Some adventure projects need attention**, with its workspace-relative
source and the load error. Explicitly opening a malformed project fails at startup with the same
diagnostic instead of silently selecting another adventure.

## Adventure menu and project creation

Choose **Adventures** in the top bar to browse and open projects without restarting the local server.
The library shows each adventure's synopsis; encounter, revelation, and lead counts; current validation
error or warning count; and discovery tags. Filter controls combine free-text search with structured
facets for genre, game system, setting, group size, character level, and combat intensity. Group-size
and level filters match adventures whose inclusive range contains the requested value; adventures with
an unspecified range are omitted from that filtered result rather than treated as universal matches.
**Open adventure** selects the project when necessary and goes directly to its overview rather than
leaving selection as a separate intermediate step.

The selected project and defaults are stored in `.adventure-graph/settings.json`; adventure content and
play history remain in their project directories. A workspace with one loadable project and no malformed
project diagnostics opens it automatically. A workspace with several projects and no saved selection opens this
catalog. If the saved project is removed, renamed, or malformed, Adventure Graph preserves that unavailable selection, opens
the catalog, and asks for an explicit replacement rather than substituting another project.

The **New adventure** form creates a title-derived child directory containing canonical
`adventure.json` and `play-state.json` files plus empty `generated/` and `archives/` directories. The
directory remains human-readable, while the adventure stored inside receives an opaque UUID identity.
Generated directory names are case-insensitively collision-safe, avoid Windows device names, reserve
existing visible files and directories even when they are not valid projects, and are bounded to 80
ASCII characters for portable copying.
Only the adventure title is required. Synopsis, premise, explanation, tags, and the opening encounter may
all be left blank; the resulting project has empty authored collections and an empty matching journal.
If an opening encounter is supplied, it becomes the distinguished start encounter. Opening **Play** for a
title-only shell shows an explicit no-encounters state rather than attempting to focus nonexistent authored
material. From there, **Add first encounter** opens the contextual encounter form and returns to Play after
creation. The same shell can create its first encounter from **Add encounter** in the authoring navigation
or Structure workspace; every first-encounter form selects the start role by default. Empty premise or
explanation fields are preserved
and reported through the standard warnings rather than rejected.

Each catalog card provides **Export adventure**, which downloads the canonical authored document as
`<title>.adventure.json`. The download contains the adventure only: it does not include the active
journal, generated reports, or archives. **Import adventure** accepts the same canonical JSON format,
preserves the adventure and entity identifiers, creates a collision-safe project directory with an empty
matching journal, and selects the imported project. An adventure identity already present in the workspace
is rejected rather than duplicated under another directory.

**Import playthrough** on the catalog accepts one canonical `*.journal.json` file up to 8 MiB and resolves
its embedded adventure identity against the complete workspace. Exactly one matching adventure must exist. A
missing match instructs the user to import the adventure first; duplicate adventure identities are rejected
as an ambiguous workspace that must be repaired. Successful import adds an immutable archive to the matching
project without changing workspace selection or replacing any active journal. Malformed, oversize, stale, or
invalid uploads re-render the import page with a current revision and an announced error rather than sending
the user to a generic failure page.

Choose **Settings** to edit two separate policies. Workspace defaults seed only adventures created
later. The selected adventure's policy is persisted in that adventure and affects validation
immediately. Both forms expose lead, source-encounter, outgoing-lead, distinct-destination, edge
connectivity, and directed-reachability requirements. A numeric zero deliberately disables that
threshold; negative values are rejected.

## Available views

The application shell provides persistent navigation among:

- the adventure overview, synopsis, premise, explanation, discovery tags, counts, and structural status;
- encounter material, leads sourced there, destinations, and incoming pathways;
- revelation descriptions, lead coverage, distinct source encounters, and unlocked destinations;
- lead source-to-revelation-to-destination pathways;
- the unified reference library, stable reference records, and encounter-local reference links;
- the Structure workspace;
- the navigation-first Play workspace;
- the Recovery console;
- the Journal history and correction workspace;
- the Reports reading, printing, download, and generation workspace;
- the Archives catalog and snapshot-comparison workspace.

Every entity page includes a read-only dependency preview. It lists authored title-change effects, move
context where relevant, removal blockers, cascade effects, and references from known related play
journals. The preview does not expose a destructive action.

Every page carries the loaded revision and related validation findings. Authored prose is escaped
before a conservative Markdown subset is rendered. Project pages use `no-store` responses and a
restrictive content security policy.

The Encounters, Revelations, Leads, and References groups in the Author rail begin collapsed. Select a
group header to expand or collapse its records; the adjacent **Add** action remains independently
available. The browser remembers each preference locally. Using **Find authored material** temporarily
opens groups containing matches without replacing those saved preferences.


## Reference library

Choose **References** in the Author navigation to maintain recurring people, places, organizations,
objects, and other subjects in one adventure-owned collection. **All** shows the complete authored
order; kind buttons filter the main collection without creating separate storage or preventing other
references from remaining available through the global Author filter. A reference-light adventure is
valid and receives an empty state that explains when a canonical record is useful without requiring
one-off names to be promoted.

A reference record owns its stable identity, kind, title, alternate names, concise summary, detailed
Markdown material, and tags. Editing any displayed field preserves identity and every encounter link.
Reference detail derives backlinks from encounter-owned links and shows each encounter-specific context;
backlinks are read-only and are never saved as a second association list.

Use a reference when stable information is otherwise fragmented across several encounters and will be
useful through search, Play, pins, or generated sheets. Keep scene action, leads, sensory prose, and
changing state in encounters. Keep dense comparison or state matrices in their specialized ledgers: the
source development corpus deliberately gives Theron Eiral, the Sunseed, and the Salt Wardens dossiers while leaving
large court-house matrices, evolving dungeon machinery, and compact adventures reference-light.

Encounter detail shows linked references in authored order. The GM may link an existing record with
encounter-local relevance, unlink exactly one pair, or choose **Create and link new reference**. That
contextual creation is one atomic revision-aware operation: a refusal or revision conflict leaves both
the library and encounter unchanged. Encounter editing displays the same links read-only so canonical
reference prose is not duplicated in encounter fields.

**Remove reference** first lists every affected encounter link. A linked reference requires explicit
cascade confirmation, which removes only that record and its links. **Remove encounter** previews leads,
revelation destinations, and reference links together; its cascade removes subordinate links while
retaining all reference records. Known play-journal dependencies still block encounter removal.
Reference notes likewise block removal of their stable authored reference, because deleting it would
leave the chronological play record without a valid subject.

## Structure workspace

Choose **Structure** in the project navigation to open three synchronized structural views.

### Encounter graph

The graph displays the unique authored encounter edges implied by leads and revelations. Multiple leads
between the same source and destination remain visible through edge details but count as one
structural connection. Encounters and edges link back to their authored records.

Encounter titles are wrapped without truncation, and each box grows to fit its rendered lines. Directed
edges curve between box boundaries rather than crossing through labels. Start, end, and optional
encounters retain separate visual treatments. When validation supplies a minimum-cut witness, the graph
distinguishes both encounter partitions and highlights the witnessed crossing edges.

The default view fits the complete graph so its overall topology remains visible. Use the toolbar,
mouse wheel, or `+`, `-`, and `0` keys to zoom or restore the full view; drag or use the arrow keys to
pan. Hovering or focusing an encounter isolates its incident connections. **Expand** opens a larger graph
workspace for dense adventures without changing the authored data or browser route.

Graph coordinates, SVG geometry, and interaction are browser concerns; the application query returns
only authored edges and the validation diagnosis.

### Revelation coverage

The coverage matrix shows, for each revelation:

- supporting lead count;
- distinct source-encounter count;
- deficits against the adventure validation policy;
- source encounters already represented; and
- a contextual link to add another supporting lead.

### Diagnostics and repair links

Validation findings remain authoritative application results. Where the minimum-cut diagnosis
suggests a useful cross-partition connection, the browser can prefill a lead or revelation form with
the proposed source and destination context. The link does not invent prose and does not apply a
repair until the author completes and submits the form.

## Play mode

Choose **Play** in the Author / Play switch to open the navigation-first table workspace. The top bar
owns the Author / Play switch plus application-wide Adventures and Settings destinations. The Play rail
owns Table, History, Trackers, Correct history, Recovery console, Archives, authored-material search,
session controls, and route chronology. Loading, searching, focusing, or pinning an encounter or
reference does not append a journal event. The focused encounter may differ from the current recorded
visit, and an independently selected reference may be open above that encounter without changing either
state. The page labels the canonical and browser-only states explicitly.

The desktop workspace has three regions:

- a chronological route rail grouped by explicit sessions, with current and focused visit markers;
- a focused-encounter reader with an independently selected full reference panel when requested and
  six page-scrolling, independently collapsible sections for the opening description, GM orientation,
  encounter material, linked references, leads and supported paths, and encounter notes; and
- a utility rail containing the current visit, typed browser-local encounter/reference pins, authored-
  material search, recent encounter focus, and keyboard guidance.

Pins and recent encounter focus are stored in browser local storage under the current adventure
identifier. Pins are typed encounter/reference bookmarks, migrate legacy encounter-ID arrays, discard
malformed or stale values, and remain bounded. They are workspace conveniences, not authored facts or
canonical play history, and do not follow the journal to another browser. Search covers encounter titles
and prose; lead titles, descriptions, and procedures; revelation titles and descriptions; and reference
titles, aliases, summaries, prose, tags, and encounter-local link context. Encounter and lead results
focus the relevant encounter; reference results open the complete read-only reference panel while
preserving encounter focus.

On narrower tablet layouts, the route and utility rails become drawers opened from the bottom
navigation. The drawer scrim, Escape key, and repeated panel button close them without changing focus
or play state.

Keyboard shortcuts are intentionally limited while text fields are active:

- `/` focuses Play search;
- `P` pins or unpins the focused encounter;
- `G` returns focus to the current recorded visit;
- `[` and `]` move through recorded route visits; and
- Escape clears search or closes an open drawer.

Play mode contains the ordinary canonical table workflow. **Begin session** and **End session** are
always visible in the route rail; optional date, attendance, opening-note, and closing-note fields
remain secondary. Focusing an encounter only opens its authored material. **Start visit** is the
separate canonical action that records table play at that encounter; after a prior visit it becomes
**Start another visit**. The same header can explicitly unlock a locked encounter with a reason.
During an active current visit, lead cards record discoveries or visit-specific misses, and revelation
cards establish supported conclusions or record foreclosure and reopening judgments.

The focused encounter's **Linked references** section follows encounter-authored link order and shows
its local relevance text rather than duplicating canonical prose. **Open full reference** selects the
complete dossier above the encounter reader, including aliases, tags, Markdown content, and derived
encounter backlinks with their local contexts. Unlinked records remain reachable through Play search.
Closing the panel returns to the same focused encounter. Selecting, searching, opening, closing, and
pinning a reference do not record a visit, change the current visit, or append a journal operation.

The full-reference panel also shows that reference's active playthrough notes in chronological event
order. During an active session, **Save reference note** appends one revision-aware journal operation
associated with the stable reference identity. The note augments this playthrough without editing the
authored summary or detailed dossier. Between explicit sessions the history remains readable but the
composer is unavailable until a new session begins. Rejected writes preserve the selected reference and
submitted text. The same note appears in History, the complete Journal audit, GM narrative exports, and
the generated play summary; it is intentionally absent from the player-safe recap.

The focused-encounter header also provides **Add to adventure** for authoring without leaving the table
context. **Add lead here** opens the existing revision-aware lead workflow with the focused encounter
selected. **Add revelation and lead here** creates the conclusion first and then resumes in lead creation
so it receives an encounter-local source. **Add linked reference** atomically creates an adventure-owned
reference and links it to the focused encounter. **Add encounter** opens the ordinary encounter editor.
Canceling returns to the same Table focus. Saving returns to Play with the relevant encounter focused for
review. These controls create ordinary authored entities with the same ontology and lifecycle as entities
created before play. They do not add a journal event, unlock an encounter, replace the current visit, or
move the party. A later play-only distribution may hide these author-level links without requiring a
second mutation path.

The focused encounter uses a page-scrolling stack of six peer boxes: **Opening description**, **GM
orientation**, **Encounter material**, **Linked references**, **Leads at this encounter**, and
**Encounter notes**. Each box begins expanded, uses the same accessible single-click disclosure behavior,
remembers its preference in browser-local storage, and gains its own bounded internal scroll region when
content grows long. The browser page itself remains scrollable, so the GM may traverse the encounter as a
document without fitting the whole workspace into one viewport. The center column uses the available
width; readable prose measure is constrained inside prose content instead of narrowing the complete
dashboard. Draft text and section preferences remain browser-local. **Save note only** records the
notebook without changing lead outcomes or moving play.

An **encounter note** is the single flexible GM record for a visit. It may include immediate events,
open questions, consequences, and facts expected to remain true when the party returns. The **Current visit actions** form saves notebook text with lead outcomes, revelation establishments,
and an optional destination visit as one correctable action. With no destination it saves outcomes
without moving; with a destination its button changes to **Save visit and move**. Unusually broad or
mixed submissions show a concise **This will record:** summary before saving; ordinary submissions do
not. If validation or optimistic concurrency rejects a write, the notice names the relevant authored
material rather than an internal operation index, and submitted values and the local notebook remain
available for repair. Ordinary lead, revelation, dice, note, and
transition submissions restore the panel and rail scroll positions from before the write instead of
returning the GM to the top. Journals created by older versions may still contain durable consequence
records; Play mode reads them as legacy persistent notes but does not expose a separate composer for
new ones.

The **Recovery console** remains directly accessible as a lower-level comparison and exceptional-repair surface.
Latest-operation correction remains available there and in the Journal workspace; browsing, focus,
pins, and uncommitted notebook text remain non-canonical.

### Dice tray

The utility rail places the dice tray above **Current visit actions** for immediate table access. It
accepts bounded expressions such as `1d20`, `4d6`, or
`2d8 + 1d4 - 3`. The application parser normalizes notation and rejects malformed or excessive
expressions before requesting random values. Production rolls use the operating system's secure
random source; the browser only submits an expression and renders the validated result returned by
the application layer.

A result shows every individual die, each signed group subtotal, modifiers, and the final sum.
Successful expressions and optional labels of at most 160 characters are retained only in browser
local storage for quick reuse. They are not copied into authored files or the play journal.

**Insert in notebook** appends a compact textual account of the exact result to the active visit's
working notebook and uses the notebook's existing local autosave. **Record in journal** is a separate
explicit action for a significant roll. It stores the already-generated result without rerolling,
validates every die and the arithmetic again, and commits one revision-aware journal operation. A
throwaway roll therefore leaves `play-state.json` unchanged.

### History, trackers, and exports

Choose **History** to inspect the chronological GM-facing narrative or a player-safe recap. Choose
**Trackers** for encounter, lead, and revelation status. These are readable projections derived from the
canonical journal, not competing stores of play data.

Each ledger can show the whole playthrough or the latest explicit session. Session scope filters the
history under review while current statuses remain grounded in the complete active journal, so a
lead may accurately read “missed in this session, found later” rather than acquiring a contradictory
second state.

The encounter ledger answers what has been visited, what is current, what remains available, and which
consequences were recorded. The lead ledger distinguishes found, missed, and unresolved material;
the revelation ledger distinguishes unsupported, supported, established, and foreclosed
conclusions. The narrative ledger preserves chronological GM-facing operations and notes.

The player-safe recap is a separate allowlisted projection, not a GM page with CSS redactions. It
contains only explicit session boundaries, visited encounters, found leads, and established revelations.
GM notes, missed leads, revelation judgments, unlock reasons, consequences, and recorded rolls never
enter that projection. End-session confirmation links directly to the latest-session ledgers.

Every view has a print layout and a derived Markdown download. Downloads are disposable projections
of the authored adventure and active journal; editing or deleting them cannot change canonical play
state. A journal without explicit session markers receives an empty **No explicit session** scope
rather than silently falling back to the whole playthrough.

## Recovery console

Choose **Recovery console** to open the older Run controls. This is an exceptional recovery and
all-at-once recording surface rather than the ordinary path through Play. The page is derived
from the authored adventure
and the current active journal projection; it does not read or mutate JSON directly.

The current-encounter panel shows encounter prose, the active visit number, encounter notes, lasting
changes, and every lead authored at that encounter. Unresolved leads can be recorded against the
current visit with one action. Previously found leads remain visible with their first-discovery
visit.

The workspace also provides:

- available-encounter visit forms, including optional immediate leads and an initial note committed as
  one atomic operation;
- revelation progress showing spotted support, establishment state, and any destination encounter;
- revelation-establishment forms that can cite found supporting leads and add an adjudication
  note;
- explicit encounter unlocks with a required reason;
- append-only notes for any active visit;
- durable encounter consequences that remain separate from authored encounter material;
- recent raw operations, including voided actions and correction audit events; and
- correction of the latest active operation with a required reason.

Only encounters in the application projection's `available_encounter_ids` are offered for visits. Route labels
indicate authored destinations from the current encounter, but the browser does not calculate
availability. Revelation establishment and its automatic destination unlock remain one operation, as
do a visit and any leads or notes recorded with it.

Every Run form carries the loaded journal revision. A stale submission receives HTTP 409 and keeps
its submitted values visible for review. Domain errors receive HTTP 422 and likewise preserve the
form. A successful operation redirects to a fresh dashboard and reports the committed operation
number.


## Adventure packet

Choose **Adventure packet** to read authored reference documents without first writing disposable
files. The packet is distinct from **History**: it describes the reusable adventure rather than
serving as the chronological account of what happened at the table. The
application query derives every document from the current adventure, validation report, and active
journal. A packet table of contents selects the overview, indexes, lead and revelation lists, grouped
reference index, UUID-named reference sheets, validation report, encounter sheets, or play summary.
Reference sheets derive encounter backlinks in encounter order with local relevance context; encounter
sheets preserve their authored reference-link order. A reference-light adventure omits the reference
namespace rather than generating empty placeholder files.

The selected report is rendered through the same conservative safe-Markdown path as authored prose.
It can be downloaded as its original Markdown document or printed through a layout that removes the
application chrome and formats only the report. **Write generated packet** invokes a revision-aware
application command and publishes the same documents under the sibling `generated/` directory. A
source change after the page loads causes HTTP 409 rather than publishing a stale packet.

## Archives workspace

Choose **Archives** to inspect the active-journal event count and every immutable journal archive.
**Export current playthrough** downloads the non-empty active journal as a self-contained portable
archive without changing or resetting it. **Archive and reset journal** stores the same kind of snapshot
locally and atomically replaces the active journal with an empty one. Each archive detail page also offers
**Export playthrough** for an already stored archive.

**Import for this adventure** in the Archives workspace accepts one canonical `*.journal.json` archive up
to 8 MiB and adds it to the selected adventure. The embedded adventure identity must match that adventure,
and the archive identifier must not already exist there. Identifiers use at most 80 ASCII filename-safe
characters and are unique without regard to case. The Adventures catalog provides the corresponding
workspace-level import when the destination is not already selected. Neither path replaces the active
journal; use the existing guarded **Restore into active journal** action afterward when restoration is
intended. An empty active journal shows no export or archive controls and explains that play must be recorded
first.

An archive detail page compares its snapshot with the current adventure at the encounter, revelation,
clue, and top-level prose levels. Compatibility is determined by projecting the archived journal
against the current adventure, not by visual heuristics. Restore is enabled only when the active
journal is empty and the archived journal remains compatible. Restoring retains the immutable
archive in the catalog.

Permanent deletion requires typing the exact archive identifier. The optional archive identifier field accepts
at most 80 letters, digits, periods, underscores, or hyphens and must begin with a letter or digit; leaving it
blank derives a bounded identifier from the timestamp and label. Archive creation, active export, import,
restore, and deletion carry the aggregate adventure/journal/archive revision, require the browser CSRF
token, and refuse
stale submissions without silently replacing newer files.

## Editing authored material

Choose **Edit adventure** from the overview to change the title, synopsis, player-facing premise,
and GM-facing explanation. Open a revelation or lead and choose its edit action to change its title,
prose, role, or relationship endpoints. Open an encounter and choose **Edit encounter**. The encounter editor exposes:

- title and summary;
- the opening view and long-form Markdown encounter material;
- comma-separated tags;
- start and end roles; and
- the project revision against which the edit was prepared.

Saving is explicit. Use the relevant save button or `Ctrl+S`/`Cmd+S`. Each request invokes a
transport-neutral application command, validates related play journals before committing, and then
returns to the updated authored page with current validation results. A title change preserves the
stable machine identifier, every authored reference, every journal event, and the current route.

On read pages, editable titles and prose have a direct-edit affordance. Double-click the surface, or
focus it and press Enter, to open the established editor at that exact field. The field is focused and
scrolled into view. This is navigation into the same explicit-save form, not in-place `contenteditable`
mutation, so revision conflicts, journal validation, Markdown safety, and application validation remain
unchanged. The visible Edit buttons remain the primary discoverable action.

## Creating leads and revelations

Creation is available from the navigation and from contextual actions on entity and structure pages.

A lead form accepts its title, description, discovery guidance, source encounter, and supported
revelation. Its stable internal identifier is derived from the title only when the record is
created. Opening it from an encounter, revelation, coverage deficit, or repair suggestion preselects
the
known relationship values.

A revelation form accepts its title, description, required status, and optional unlocked encounter. Its
stable internal identifier is derived from the title only when the record is created. When opened
from a structural repair that also names a proposed lead source, a successful
revelation save continues to a lead form with both values preselected. This supports the authoring
chain without combining two domain commits or silently creating prose.

Both creation commands validate the expected revision, preserve list order through the existing
authoring transformations, verify every related journal against the proposed adventure, and return
the new project revision and validation report.

## Browser drafts

Authoring form fields are preserved in browser-local storage as they change. Drafts are not written
to `adventure.json`, are not validated authored state, and are scoped to the project and operation.
The guided new-adventure form uses the same contract.

A draft based on the currently loaded revision is restored automatically. A draft from an older
revision is not applied silently: the editor offers an explicit recovery action that places it onto
the current revision for review. **Discard browser draft** restores the values supplied by the page;
on a conflict response it does not silently rebase the preserved submission. A cross-tab change to
the same draft key produces a notice rather than replacing fields in place.

A successful save, a confirmed no-op save, or successful adventure creation clears the corresponding
draft. `Escape` returns to the read page after preserving changed fields, while `Ctrl+S`/`Cmd+S`
submits. Browser-storage failure does not block explicit submission.

## Appearance

Use the top-bar appearance toggle to switch between light and dark mode. The choice is stored in the
browser under `adventure-graph:appearance` and applies across adventure pages, the adventure catalog,
and validator settings. It is intentionally not written to an adventure, workspace settings, or play
journal. Print output remains light.

## Revision conflicts

Every authoring form carries an opaque project revision. If the adventure or a related journal
changes before submission, the application refuses the write with HTTP 409. Submitted fields remain
visible and remain in the browser draft. Reloading exposes the newer project state; the older draft
can then be deliberately recovered onto that revision and reviewed before another save.

This is optimistic local-file concurrency protection. It prevents ordinary stale browser saves from
silently overwriting a project changed through another Adventure Graph process. It cannot coordinate
with unrelated programs that ignore the project revision protocol.

## Request safety

The authoring interface:

- binds only to loopback and rejects non-loopback HTTP authorities before project dispatch;
- does not trust proxy forwarding headers or claim support for reverse-proxy deployment;
- rejects raw or encoded separators, dot segments, backslashes, and controls in request paths;
- accepts writes only at explicit encounter-edit, clue-create, revelation-create, Run-operation,
  journal-correction, report-generation, and archive-management routes;
- requires an interface-owned CSRF token on every write and rejects token failures with HTTP 403
  before command execution or submitted-text redisplay;
- bounds form bodies to 2,000,000 bytes and rejects an oversize declaration before reading;
- accepts only URL-encoded forms with canonical lengths, valid percent escapes, and strict UTF-8;
- bounds query strings before project dispatch and rejects malformed percent encoding or UTF-8;
- escapes every persisted authored and journal text value at its final HTML sink; authored
  Markdown is escaped before the small safe-Markdown subset is applied;
- validates local redirects, download filenames, and emitted response-header syntax;
- suppresses unexpected local paths and exception details from HTTP 500 responses while reporting
  them to the local server error stream; and
- sends restrictive content-security, cross-origin, permissions, framing, referrer, and MIME-sniffing
  headers.

## Architecture

The web package receives application callables grouped as:

```text
AuthoringQueries
  GetAdventureOverview
  GetEncounterDetail
  GetRevelationDetail
  GetClueDetail
  GetStructuralOverview

AuthoringCommands
  UpdateEncounter
  CreateClue
  CreateRevelation

PlayQueries
  GetPlayJournalStatus
  GetRunDashboard

PlayCommands
  CorrectLatestPlayOperation
  RecordPlayVisit
  SpotPlayClue
  EstablishPlayRevelation
  UnlockPlayEncounter
  AddPlayVisitNote
  RecordPlayEncounterConsequence

ReportQueries
  GetReportPacket

ReportCommands
  PublishReportPacket

ArchiveQueries
  ListJournalArchives
  GetJournalArchiveDetail

ArchiveCommands
  ArchiveActiveJournal
  ExportActiveJournal
  ImportJournalArchive
  RestoreJournalArchive
  DeleteJournalArchive
```

It does not import the local-file adapter. `bootstrap.py` constructs `LocalAuthoringProject`, creates
the application use cases, and injects them into the web adapter. The CLI and browser therefore
remain sibling adapters around the same application boundary.

The application owns revision checks, immutable authoring transformations, related-journal
compatibility, revelation coverage, unique authored encounter edges, validation, dependency analysis,
journal operation projection, session availability, lead and revelation progress, atomic play
operations, and correction semantics.
HTTP routing, form parsing, CSRF handling, browser drafts, appearance preference, direct-edit field
targeting, graph coordinates, SVG, HTML, safe prose rendering, JavaScript, and CSS remain outward
interface concerns. No HTTP, WSGI, URL, HTML, form, or
browser type appears in the application or domain layers.

## Journal history and correction

The Journal workspace shows raw operations newest first, including active operations, voided
operations, and correction audit events. Correcting the latest active operation requires a reason and
the current project revision. A stale submission receives HTTP 409 and preserves the entered reason.
The browser invokes the same `CorrectLatestPlayOperation` application command as the CLI.

Corrections never delete or rewrite existing events. They append one `operation_voided` event and the
active projection ignores the target operation. Compound visits and revelation/unlock actions are
therefore corrected atomically.

## Current boundary

The original graphical-interface milestones, GM-interface cleanup sessions, Play panel refactor, and
local GM cold-read are complete. Future browser features should continue to add application use cases
before routes, especially for destructive authored-entity changes. Native launcher and platform checks
remain release evidence rather than unfinished browser architecture.

## Navigation rails

Author and Play follow one stable spatial convention. The left side is for navigation and retrieval:
workspace links and **Find authored material** remain there as you move among screens. In ordinary
Play, the session route also lives on the left because it is navigation through recorded table
history. The right side is contextual: current table state, pins, recent focus, dice, and other tools.
The pin shelf is hidden until at least one encounter is pinned, so an unused browser-local feature
does not reserve space.

Opening History, Trackers, Correct history, Recovery console, or Archives preserves the same Play
workspace links and authored-material search. Returning to the encounter reader never requires the
browser Back command. Author pages likewise retain their adventure navigation while moving among the
overview, Structure, packet, encounters, revelations, leads, and editors.

Within an active encounter, **Encounter notes** are the only ordinary note composer. **Save note
only** records that text without outcomes or movement. **Current visit actions** uses the same notebook
text when saving lead outcomes and either remaining at the encounter or moving to the next one. The
right rail summarizes recent history without duplicating workspace links. Leads link directly to the revelation
they support.
