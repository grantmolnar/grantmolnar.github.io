# Graph-scale design notebook

## Status

This document records unresolved campaign product and architecture questions for later design work. It
is an **active notebook, not an accepted campaign contract**. The campaign answers below remain working
recommendations only. They do not change the campaign schema, runtime journal, validation policy, UI,
or import/export behavior.

The adventure-level encounter/reference distinction recorded in questions 13 and 14 has since been
accepted as a pre-beta product direction and moved into `adventure-reference-library-roadmap.md`. Its
exact schema, association shape, runtime extensions, and migration version remain open until the
roadmap's fixtures and design tranche accept them.

A campaign proposal becomes binding only after representative fixtures, beta evidence, and an explicit
design review move it into the appropriate architecture, file-format, runtime, or product document.

## Campaign structure questions

### 1. How many revelations may one campaign clue support?

**Question.** The current adventure model uses one clue to support exactly one revelation, while early
campaign notes allowed a campaign clue to support several revelations.

**Provisional recommendation.** Begin with one campaign clue supporting one campaign revelation. This
preserves the proven dual clue-list/revelation-list model and keeps support coverage legible. If real
campaign fixtures show that one discovered fact must support several conclusions without artificial
clue duplication, add an explicit support-association model rather than placing an unconstrained list of
revelation IDs directly on every clue.

**Revisit with.** A fixture in which one fact genuinely and usefully supports several distinct campaign
conclusions.

### 2. What does a campaign revelation do to an adventure entry?

**Question.** "Unlock" currently risks conflating learning that an adventure exists, making it
playable, beginning it, completing it, and making it available again.

**Provisional recommendation.** Separate authored revelation effects from runtime entry status. An
authored revelation may make an entry known, available, or apply another typed campaign consequence.
Runtime state separately records unavailable, available, active, completed, abandoned, bypassed, or
revisitable status.

**Revisit with.** A short arc containing a rumored adventure that is known before it is actionable, and
a revisitable adventure whose availability changes more than once.

### 3. How should adventure outcomes participate in campaign structure?

**Question.** Campaign clues and consequences may arise from completing an adventure or reaching one of
several endings, but the current portable adventure format has end encounters rather than explicit
stable outcome records.

**Provisional recommendation.** In the first campaign version, define campaign-owned outcomes on each
campaign entry. The campaign records which outcome occurred and may source campaign clues or effects
from it. Do not add portable adventure-level outcomes until several fixtures establish the necessary
fields and semantics.

**Revisit with.** Adventures whose materially different endings affect later campaign routes.

### 4. How are campaign clues recorded when they appear inside adventure play?

**Question.** A campaign clue may be placed at an encounter, but spotting it belongs to campaign state
rather than the adventure's ordinary clue state.

**Provisional recommendation.** Display the campaign clue in encounter context while recording its
judgment in the campaign journal. If one UI action writes both adventure and campaign history, use a
coordinated recoverable transaction; do not pretend that the two journals are one aggregate.

**Revisit with.** A fixture that discovers an adventure clue and a campaign clue in the same table
action, including an interrupted-write test.

### 5. What provenance follows an imported adventure?

**Question.** Copy semantics establish campaign ownership but not how the campaign recognizes later
divergence, variants, or identity collisions.

**Provisional recommendation.** Retain the imported adventure ID, source revision or content hash,
import timestamp, campaign-local revision, divergence status, and optional original source location for
comparison. Ordinary campaign-local edits preserve the adventure ID; an explicit clone or variant gets
a new adventure ID. A different payload with the same adventure ID requires a visible comparison or
collision decision, never silent replacement.

**Revisit with.** Two revisions of one adventure, a deliberate variant, and two unrelated payloads that
claim the same adventure identity.

### 6. How does "update from source" work?

**Question.** Campaign overlay records may refer to encounter IDs or other stable adventure records that
an incoming revision has removed or replaced.

**Provisional recommendation.** Preserve the current campaign copy until conflicts are resolved. Show
every affected overlay record, allow references to be remapped or retired, never delete campaign
material automatically, and replace the contained adventure atomically only after resolution.

**Revisit with.** An imported revision that renames one encounter, removes another, and splits a third
while campaign clues are placed at all three.

### 7. What is the difference between a campaign entry and an adventure run?

**Question.** One authored placement may be played more than once, by more than one party, or in more
than one timeline.

**Provisional recommendation.** Keep a stable campaign-entry ID separate from a stable adventure-run
ID. A run records the exact adventure snapshot and revision used. Campaign outcomes and consequences
identify the run that produced them. The entry controls whether several runs are permitted and how one
run becomes authoritative for campaign progression.

**Revisit with.** A failed first attempt, a later successful attempt, and two parties interacting with
the same adventure entry.

### 8. What counts as independent campaign clue support?

**Question.** Several clues in several encounters inside one adventure may still depend on one fragile
campaign source.

**Provisional recommendation.** Campaign validation should measure independence at meaningful source
boundaries: different adventure entries, outcomes, factions, patrons, world events, or genuinely
independent delivery mechanisms. Use named preparation profiles rather than one universal threshold for
campaigns of every size.

**Revisit with.** A three-adventure arc and a broad sandbox whose appropriate redundancy expectations
are visibly different.

### 9. Which graph is canonical?

**Question.** A projected adventure-to-adventure graph loses information when clues originate outside
adventures or one revelation affects several entries.

**Provisional recommendation.** Keep the canonical campaign structure as sources to clues to
revelations to typed effects or entries. Treat adventure-to-adventure edges as a derived projection.
Never serialize an unexplained projected edge as independent authored truth.

**Revisit with.** A revelation jointly supported from several entries that unlocks two alternatives and
also records a campaign truth.

### 10. How rich are non-adventure campaign sources?

**Question.** Campaign clues may come from factions, patrons, travel, calendars, downtime, or world
events, but implementing each as a complete subsystem would expand the initial campaign feature
indefinitely.

**Provisional recommendation.** Start with a small generic campaign-source record carrying stable
identity, title, description, and category. Add specialized faction, calendar, settlement, or world
models only when repeated use demonstrates distinct behavior that a generic source cannot express.

**Revisit with.** Fixtures using at least three non-adventure source categories and one source that
proves the generic record inadequate.

### 11. What is the campaign storage and archive layout?

**Question.** Campaign authorship, campaign runtime, campaign-owned adventure copies, individual
adventure journals, repeated runs, exports, and archives need clear ownership and relocation boundaries.

**Provisional recommendation.** Keep one portable campaign root containing a campaign authored
document, a separate campaign journal, campaign-owned adventure-entry directories, run-specific
adventure journals and archives, and disposable generated outputs. A campaign archive must identify the
exact campaign snapshot, entry snapshots, and run records it describes. Choose exact filenames only
after transaction and relocation fixtures exercise the layout.

**Revisit with.** Project relocation, archive and restore, repeated runs, malformed recovery metadata,
and clean entry export.

### 12. How much backend abstraction should campaign support reuse?

**Question.** Encounter and campaign graphs share algorithms but not necessarily domain entities,
validation, or UI semantics.

**Provisional recommendation.** Reuse graph primitives, identity rules, projections, and validation
algorithms where they remain scale-independent. Keep explicit `EncounterGraph` and `CampaignGraph`
models rather than forcing encounters and campaign entries into one generic entity. Review the current
architecture sentence suggesting that an encounter might become an entire adventure at campaign scale;
it may describe algorithmic reuse too broadly.

**Revisit with.** The first headless campaign fixture and an attempted shared abstraction reviewed for
whether it preserves domain language and validation clarity.

## Adventure node and reference disposition

### 13. Are encounter-only graph nodes too narrow?

**Question.** Node-based scenario design can treat locations, characters, organizations, events, and
activities as nodes. Adventure Graph currently presents graph nodes as encounters. Does that discard
useful flexibility?

**Current evidence.** The runtime model already defines an encounter broadly as a playable location,
person, event, faction, or other scenario component. The practical narrowing occurs in workflow:
encounters are visited, receive notes, source clues, and participate in route and resilience validation.
That operational meaning is valuable, but it is not the same as saying that every persistent person or
place in the fiction is an encounter.

**Accepted product direction.** Preserve the encounter graph as the operational clue-bearing layer. An
encounter may be centered on a person, place, faction, event, or activity whenever the players can go to
or otherwise interact with it as a meaningful unit of play. Do not require every mentioned NPC or
location to become an encounter merely so the GM has somewhere to store information about it.

The likely missing abstraction is a separate reusable reference layer, not a return to an untyped
universal graph node. A person such as Captain Vale may have one persistent reference record while
appearing in several encounters; interviewing Captain Vale may itself be an encounter. A place such as
the Old Mill may have one persistent place record while hosting several encounters; exploring the Old
Mill may also be one encounter when that is the useful playable scale.

Do not add encounter kinds merely for taxonomy unless they improve authoring, filtering, validation, or
Play behavior. The important distinction is operational versus referential:

- an **encounter** answers where or when a playable interaction and its clues occur;
- a **reference record** answers what an enduring person, place, faction, object, or other subject is.

**Revisit with.** One investigation dominated by interviews, one location-based scenario with several
encounters in the same place, one proactive NPC, and one organization operating through multiple people
and sites.

### 14. Where should cross-encounter NPC, location, and setting information live?

**Question.** The adventure currently provides whole-adventure explanation and encounter prose, but no
first-class canonical place for an NPC dossier, location gazetteer entry, faction brief, recurring
object, or other information used across several encounters.

**Accepted product direction.** Add an adventure-owned **reference library** as a pre-beta authored
surface. A minimal reference record would probably have:

- stable identity independent of its displayed name;
- a small kind vocabulary such as person, place, faction or organization, object or asset, and other;
- title or name;
- concise summary;
- GM-facing detailed content; and
- tags or keywords.

Encounters would link to zero or more reference records, and the application would generate backlinks
showing every encounter in which each reference is relevant. The Author interface would provide People,
Places, and Other Reference views plus contextual creation from an encounter. Play would show and allow
pinning the references linked to the focused encounter without duplicating their prose into every
encounter.

Clue and revelation subject links may eventually improve search and generated indexes, but they should
not affect graph connectivity unless a later explicit design says so. Begin with encounter-to-reference
associations and add finer links only when fixtures demonstrate a table need.

The authored reference library should describe the reusable baseline. Changes discovered during play
should remain append-only runtime history rather than silently rewriting authored dossiers. A later
runtime design may allow notes or consequences to target reference IDs so the application can assemble
an NPC or location history across encounters; that event shape is still open.

Adventure import, export, archives, and campaign-owned copies would carry the reference library as part
of the portable adventure. Campaign-level people and places may later relate to adventure-local
references, but imports should not merge similarly named entities automatically.

**Revisit with.** A recurring NPC who changes allegiance, a location visited in three encounters, a
faction represented by several characters, a portable export, and a completed journal whose changes can
be read by reference without altering the authored baseline.

### 15. How should persistent campaign entities relate to adventure references?

**Question.** A person, place, organization, object, or other subject may persist across several
adventures. Each imported adventure must remain independently portable, but the campaign also needs one
stable identity for the subject and campaign-wide backlinks.

**Provisional recommendation.** Give the campaign its own reference library using the same initial kind
vocabulary and stable-identity discipline as adventure references. Preserve every imported
adventure-local reference unchanged inside its campaign-owned adventure copy. Relate the two layers with
explicit campaign-owned binding records keyed by campaign-entity ID, campaign-entry ID, and
adventure-reference ID. A binding declares identity correspondence; it does not merge records, rewrite
the adventure, or create graph connectivity.

The campaign reference should hold cross-adventure baseline material and campaign-wide preparation. The
adventure reference should remain the portable, adventure-specific presentation required to run that
adventure alone. Campaign runtime changes should be append-only campaign history associated with the
campaign entity or an adventure run, not silent edits propagated into every bound adventure reference.
Backlinks from a campaign entity to adventures, encounters, clues, calendar entries, and run outcomes
should be derived from explicit bindings and links. Import may recognize exact provenance from a prior
campaign export, but it must never reconcile entities by displayed name alone.

**Revisit with.** One NPC appearing under different titles in three adventures, two adventures that each
contain a local reference for the same place, a clean standalone export, a later source-adventure update,
and a campaign runtime change that must remain visible without mutating either authored adventure.

### 16. How should an absolute campaign calendar index encounters and world events?

**Question.** Campaign play needs one chronology that can place encounter occurrences and external world
events on an absolute timeline while producing backlinks to persistent campaign entities. A display
calendar alone is insufficient because names, eras, and calendar presentations may change.

**Provisional recommendation.** Store campaign chronology against a canonical absolute coordinate that
is independent of its displayed calendar label. Begin with an integer day index plus an optional
within-day position or precision marker; let one or more campaign calendar definitions render that
coordinate as setting-specific dates. Do not write dates directly into portable encounter records.
Instead, create stable campaign-owned calendar entries that may target:

- an encounter occurrence, identified by campaign-entry ID plus encounter ID;
- an adventure-wide milestone or outcome; or
- an external event with its own title and description.

Calendar entries should carry explicit links to campaign entities, and entity timelines and backlinks
should be derived from those links. An external event may later serve as a campaign-clue source without
being represented as a fake encounter or adventure. Keep authored schedules, forecasts, and fixed world
events separate from the append-only record of what actually occurred in campaign play; runtime
occurrences may cite or realize an authored calendar entry but should not overwrite it.

The first calendar fixtures should force decisions about exact instants versus date ranges, uncertain
dates, durations, rescheduling, recurring events, simultaneous events, and conversion among display
calendars. The absolute coordinate and identity contract should be settled before specialized month,
season, festival, or faction subsystems are added.

**Revisit with.** A scheduled encounter delayed by player action, an external event that occurs while the
party is elsewhere, one event linked to several persistent entities, two display calendars rendering the
same absolute day, an uncertain date range, and an adventure exported without campaign chronology.

## Reference-library implementation details still unresolved

The adventure-level schema, kind vocabulary, and encounter-owned association shape are now accepted in
`adventure-reference-library-roadmap.md`. The campaign design still does not choose:

- the exact campaign-reference and binding schemas;
- whether campaign references need fields beyond the adventure reference shape;
- how runtime notes, consequences, and run outcomes target campaign entities;
- whether clues and revelations receive direct campaign-entity subject links;
- the absolute chronology precision and display-calendar schema;
- the authored schedule and runtime occurrence event shapes;
- whether any campaign reference can also become a proactive source of play without an encounter; or
- which of these changes belong in the first campaign implementation.

These details should remain open until representative adventure fixtures and beta feedback make their
costs and benefits concrete.

The accepted beta scope and implementation sequence now live in
`adventure-reference-library-roadmap.md`. The list above remains a design checklist, not a reason to
reopen the accepted encounter-versus-reference product boundary.
