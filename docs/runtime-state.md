# Runtime State

## Purpose

Authored adventure structure and actual play are separate. `adventure.json` says what exists and how
clues support revelations. `play-state.json` records what happened at the table.

Play state is an append-only event journal. Application services never rewrite earlier events. The
current route, clue status, revelation status, encounter availability, session ledger, and narrative are
projections rebuilt from active events after corrections are applied.

The canonical play-state format is schema version 6. Versions 1 through 5 are pre-beta formats and
are rejected rather than supported through a permanent dual reader. Its accepted semantics are also
recorded in [Play mode semantics](play-mode-semantics.md).

## Events and operations

Every event has a global, one-based `sequence` and belongs to a one-based `operation_number`.
Sequences and operation numbers are contiguous. An operation is the smallest table-facing action
that must succeed or be corrected as one unit.

Most operations contain one event. Two compound operations are currently intentional:

- recording a visit can append the visit, clues spotted immediately, and initial notes under one
  operation number; and
- establishing a revelation can append the establishment and its automatic encounter unlock under one
  operation number.

Visit events also carry a one-based `visit_number`. Visit numbering remains global across session
boundaries, because the playthrough has one chronological route.

### `session_started`

Begins the next explicit tabletop session. It carries a contiguous `session_number` and optional
title, ISO calendar date, participant names, attendance note, and opening note.

Unsegmented history may precede the first explicit session. Once the first active `session_started` event
exists, ordinary content events must occur inside an active session. Corrections remain legal outside
a session so that an accidental end or start can be reversed honestly.

### `session_ended`

Ends the currently active explicit session and may include a closing note. Sessions cannot overlap,
end out of order, or reuse numbers.

### `encounter_visited`

Records entry into one available encounter. Start encounters are available from the beginning. Other encounters must
first receive a `encounter_unlocked` event. An optional `party_label` distinguishes alternating groups in
one shared chronology without creating parallel journals.

### `clue_spotted`

Records the first time a clue was noticed, tied to a visit to the clue's authored source encounter. A clue
can be spotted only once among active operations.

Spotting a clue does **not** establish its revelation. The clue may be misunderstood, ignored, or
recognized only much later.

### `clue_missed`

Records that one clue was not discovered during one specific visit to its authored source encounter. The
same clue cannot be marked missed twice on one visit, and a clue already spotted cannot later be
marked missed.

A miss is an opportunity record, not a permanent global state. The clue may still be spotted during a
later visit.

### `revelation_established`

Records that the players established a conclusion. The event can cite zero or more previously
spotted supporting clues and can include an adjudication note.

An empty clue basis is valid. A revelation may be learned through direct testimony, a spell, player
reasoning not captured by the authored clues, or another GM-adjudicated route.

If the authored revelation unlocks an encounter, the application appends a distinct `encounter_unlocked` event
in the same operation unless that encounter is already available.

### `revelation_foreclosed`

Records an explicit GM judgment that an unestablished revelation can no longer be established in
this playthrough. Foreclosure requires a reason and is never inferred from missed clues or clue
counts.

### `revelation_reopened`

Reverses a currently active foreclosure through a later explicit judgment with its own reason. A
reopened revelation immediately regains whatever support is already derived from spotted clues.

### `dice_roll_recorded`

Stores a deliberately retained roll: its original expression, optional label, ordered dice groups,
individual results, integer modifiers, and total. Projection rejects empty groups, invalid die sizes,
out-of-range results, bad signs, and totals inconsistent with the stored terms.

Play mode now supplies the bounded parser, operating-system-backed secure roller, ephemeral tray,
notebook insertion, and explicit revision-aware record command. Schema version 4 provides the
durable representation, while ordinary unrecorded rolls and recent expressions remain browser-local
and never enter the journal.

### `encounter_unlocked`

Records that an encounter became available. The event either cites the established revelation that
unlocked it or gives a free-form reason for explicit GM adjudication.

### `visit_note_recorded`

Appends a note to an earlier visit. The note is a new event; the original visit event is unchanged.

### `reference_note_recorded`

Appends a chronological GM note to one stable authored reference. The reference may represent a person,
place, organization, object, or other persistent subject. The event stores the authored `reference_id`
and nonempty note text; it does not copy or mutate the reusable reference description.

Reference notes appear in the selected-reference history, the complete Journal audit, the GM narrative
ledger, and generated play summaries. They are excluded from the player-safe recap unless a future
explicit disclosure event or policy says otherwise. Removing a reference used by an active or otherwise
explicitly related journal is blocked so the historical association cannot become dangling. Immutable
archives remain interpretable through their own embedded adventure snapshots.

### `encounter_consequence_recorded`

Records a durable change affecting an encounter, such as an alerted faction, destroyed evidence, a burned
safe house, or an NPC's changed disposition. Consequences do not modify authored encounter content.

### `operation_voided`

Records an honest correction of the latest still-active content operation. It names the target
operation and requires a reason. The target events remain in the file and in audit views, but the
current-state projection ignores them.

A correction is itself a new one-event operation. It cannot void another correction, skip over a
later active content operation, or reactivate a previously voided operation. Repeating the command
therefore walks backward through the remaining active operations without rewriting history.

Use the CLI correction command when the most recent table action was entered accidentally:

```bash
adventure-graph correct-latest adventure.json play-state.json \
  --reason "The clue was clicked before the players searched the cabinet."
```

The browser Journal page invokes the same application command and requires the current journal
revision, so an externally changed file is never silently overwritten.

## Session-aware CLI workflow

Schema-version-6 operations are available through application services and the CLI before their
full table-centered browser surfaces are added.

Begin a session:

```bash
adventure-graph start-session adventure.json play-state.json \
  --title "The western breach" \
  --played-on 2026-07-14 \
  --participant "Ilyra" \
  --participant "Torren" \
  --opening-note "The party resumed beneath the cracked aqueduct."
```

A visit may carry a lightweight split-party label:

```bash
adventure-graph visit adventure.json play-state.json drowned-archive \
  --party "Canal team"
```

Record a missed opportunity, later discovery, and revelation judgment:

```bash
adventure-graph miss-clue adventure.json play-state.json broken-seal --visit 3
adventure-graph spot-clue adventure.json play-state.json broken-seal --visit 7
adventure-graph foreclose-revelation adventure.json play-state.json hidden-patron \
  --reason "The only surviving witness has left the city."
adventure-graph reopen-revelation adventure.json play-state.json hidden-patron \
  --reason "The party recovered the witness's encoded deposition."
adventure-graph note adventure.json play-state.json 7 \
  "The witness recognized the seal after leaving the archive."
adventure-graph reference-note adventure.json play-state.json REFERENCE_UUID \
  "The witness now trusts the party with the hidden route."
```

The note commands require both canonical files. They validate the adventure/journal pairing and
commit through the same optimistic revision boundary as browser note recording. `note` associates its
text with a numbered encounter visit; `reference-note` associates its text with a persistent authored
reference while leaving that reference's static description unchanged.

End the session:

```bash
adventure-graph end-session adventure.json play-state.json \
  --closing-note "The party secured the archive but lost the western stairs."
```

After explicit sessions begin, the application refuses new visits, discoveries, judgments, notes,
unlocks, or consequences between sessions. This prevents accidental unsegmented history while
preserving older journals that never recorded boundaries.

## Current browser workflow

The browser now separates navigation from canonical recording. The Play workspace renders the
chronological route, current visit, focused encounter, authored prose, clue progress, revelation status,
and consequences from the same session-aware projection. Focusing, searching, or pinning material
is explicitly non-canonical and does not write `play-state.json`; pins and recent focus remain in
browser-local storage.

Play mode now invokes revision-aware application commands for explicit sessions, visits, clue
findings and visit-specific misses, revelation establishment and judgments, unlocks, encounter notes,
and atomic transitions. The GM-facing workflow uses one flexible encounter-note composer. Legacy
`encounter_consequence_recorded` events remain readable for journal compatibility, while the existing Run
console remains a lower-level recovery and comparison surface with latest-operation correction.

Each recording form carries an opaque revision derived from both the adventure and active journal.
If either file changes after the page was loaded, the application refuses the write rather than
overwriting the newer state. The web adapter preserves submitted values, but it does not decide encounter
availability, clue legality, revelation support, operation grouping, or correction order.

The remaining final GM playthrough audit is sequenced in
[the Play mode roadmap](play-mode-semantics.md).

## Derived projection

The application first identifies voided operation numbers, then validates and projects only active
content events. It derives:

- explicit sessions, their metadata, operation ranges, visit ranges, and active status;
- visits, party labels, spotted clues, missed clues, and committed notes;
- clue progress with every missed visit and the eventual discovery visit;
- spotted support, establishment, foreclosure, and reopening history for every revelation;
- encounter availability and global visit history;
- explicit unlock history;
- encounter consequences;
- correction audit records; and
- a session-aware chronological narrative of active events.

These are transport-neutral application and domain read models. Browser pages, operational
ledgers, and exports render them rather than recomputing state in an interface adapter.

`GetPlayLedgers` derives encounter, clue, revelation, narrative, and player-safe views for the whole
playthrough or latest explicit session. Session scope filters relevant activity while current status
continues to come from the complete active projection. The player recap is constructed from an
explicit safe-event allowlist rather than by redacting the GM narrative. Printable pages and
Markdown downloads remain derived output and are never read back as canonical state.

## Journal invariants

Projection rejects inconsistent state, including:

- noncontiguous event, operation, session, or visit numbering;
- a content operation appearing again after a later operation has begun;
- malformed multi-event operations;
- correction operations containing more than one event;
- a correction without a reason;
- a correction targeting anything except the latest active content operation;
- overlapping, out-of-order, or reused explicit sessions;
- ordinary content outside a session after explicit session history begins;
- invalid session dates or duplicate or blank participant names;
- unknown authored identifiers;
- visits to locked encounters;
- clues spotted or missed outside their source encounter;
- duplicate clue discoveries;
- duplicate misses for the same clue and visit;
- misses recorded after discovery;
- establishment events citing unspotted or unrelated clues;
- duplicate active revelation establishments;
- foreclosure of an established or already foreclosed revelation;
- reopening of a revelation that is not currently foreclosed;
- establishment while a revelation remains foreclosed;
- revelation-based unlocks that precede establishment or target the wrong encounter;
- duplicate active explicit unlock events;
- notes referring to nonexistent active visits;
- reference notes naming unknown authored references;
- blank canonical notes, consequences, reasons, or dice expressions; and
- malformed or arithmetically inconsistent recorded dice results.

## Pre-beta schema boundary

Schema version 6 is the only supported play-state format. Versions 1 through 5 were internal pre-beta
formats and are rejected rather than migrated through a permanent dual reader. Every bundled active
journal and archive journal was converted atomically. Version 6 preserves all version-5 event shapes and
adds `reference_note_recorded` before external testers create compatibility-bearing journals.

After the beta contract is frozen, any incompatible journal change requires an explicit versioned
migration decision.

## Reset and historical archives

The active play state remains separate from authored content. Reset is therefore implemented by
archiving the current journal and writing a new empty version-6 journal, not by editing or truncating
the adventure. Archives include the adventure snapshot active when the events were recorded. See
[journal archives](journal-archives.md) for archive, non-destructive restoration, listing,
compatibility, rollback, and confirmed `delete-archive` semantics.
