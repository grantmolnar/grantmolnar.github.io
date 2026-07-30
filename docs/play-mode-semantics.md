# Play Mode Semantics

## Status

This document fixes the domain vocabulary and journal design for the first table-centered Play mode.
It is the accepted design for milestones 2 through 6 of the Play mode roadmap. Those milestones
now implement the canonical version-6 journal, application and CLI commands, richer
projections, browser encounter-running workflow, atomic transition, bounded parser, secure roller,
ephemeral tray, notebook insertion, and explicit significant-roll recording described here.

The purpose of this document is to make every table-facing action answerable in domain language before
a browser control depends on it. Interface state is included only where it must be distinguished from
canonical play history.

## State boundaries

Adventure Graph maintains three kinds of state.

### Authored state

Authored state describes the reusable adventure: encounters, clues, revelations, validation policy, and
narrative text. It lives in `adventure.json` and changes only through authoring operations.

Play may expose return-safe shortcuts into those same authoring operations for table improvisation.
Creating an encounter, clue, revelation, or reference from the Play workspace still changes authored
state only. The resulting value has the same domain type, schema, validation rules, identity rules, and
editing lifecycle as one created before the first session; creation context does not define a second
ontology. It does not append a journal event, create or move a visit, unlock an encounter, spot a clue,
establish a revelation, or commit a note. The first visit and later table outcomes record what happened
in play. If authoring provenance or revision history is later required, it should use separate authored
metadata or a revision log rather than turning Play-created entities into runtime subtypes. Revelation
creation continues into clue creation when opened with encounter context; reference creation may
atomically link the new authored record to that encounter.

### Canonical play history

Canonical play history records table facts and explicit GM judgments. It lives in `play-state.json` as
an append-only journal. Current state is always reconstructed from active events after corrections are
applied.

Canonical history includes:

- explicit session boundaries;
- encounter visits and revisits;
- clue discoveries and missed opportunities;
- revelation establishment, foreclosure, and reopening;
- explicit encounter unlocks;
- committed visit notes;
- chronological notes associated with persistent authored references;
- durable encounter consequences;
- deliberately recorded dice rolls; and
- append-only corrections.

### Ephemeral workspace state

Ephemeral workspace state helps one GM operate one browser. It is not evidence about what happened at
the table and must not enter `play-state.json`.

It includes:

- the focused encounter and any independently selected reference;
- typed encounter and reference pins;
- recent encounter-focus history;
- open drawers and selected ledger filters;
- uncommitted visit-note drafts;
- recent dice expressions and unrecorded rolls;
- display density, appearance, and player-window state; and
- unsent form values preserved after a rejected write.

The initial Play mode may keep this state in browser storage. Cross-device synchronization, if later
required, must use a separate adapter and file format rather than extending the play journal.

The six focused-encounter boxes are presentation containers, not domain subdivisions. Opening
Description, GM orientation, encounter material, linked references, encounter-local clues and paths,
and encounter notes remain ordinary views over authored or projected data. Their expanded state,
internal scroll position, and page position are ephemeral. Collapsing a box cannot conceal or change a
canonical fact, and printing or another adapter may present the same content without those containers.

## Focus, pin, visit, and revisit

These actions are independent.

- **Focus** means “show this encounter as the Play workspace context.” It is ephemeral and creates no
  journal event.
- **Select reference** means “open this authored dossier beside the focused encounter.” It is ephemeral,
  creates no event, and does not replace encounter focus.
- **Pin** means “keep this encounter or reference readily available.” It is ephemeral and creates no
  event.
- **Visit** means “the party entered this encounter.” It appends `encounter_visited`.
- **Revisit** is another visit to a previously visited encounter. It appends another `encounter_visited` with the
  next global visit number.

The latest active visit is the canonical current visit. Focusing another encounter or selecting,
opening, closing, searching for, or pinning a reference does not change it. Ending a session does not
erase it; Play mode may reopen the latest visit as context when a new session begins.

### Read-only authored references and playthrough notes

References remain authored adventure data during Play. The focused encounter presents linked references
in authored link order with encounter-local relevance text. A selected full reference may show canonical
prose, aliases, tags, and derived backlinks without duplicating that information into the journal.
Unlinked references may still be found through authored-material search. Selecting, searching, opening,
closing, or pinning a reference remains browser-only retrieval: it creates no visit, clue outcome, note,
consequence, or generic runtime event.

During an active session, the selected-reference panel may append `reference_note_recorded`. This is an
explicit canonical action, not selection telemetry. It stores the reference's stable identity and new GM
text in chronological play history while leaving the authored summary and detailed dossier unchanged.
The selected-reference panel projects active notes for that identity in event order. The complete Journal,
GM narrative ledger, and generated play summary include them; the player-safe recap does not. A correction
may void the latest reference-note operation without rewriting its original event.

A visit may carry an optional `party_label`. This is a lightweight route label such as `Main party`,
`Mara and Sera`, or `West team`. It allows a chronological journal to represent split-party
alternation without introducing separate timelines or character-sheet state. The label is descriptive
and imposes no rules.

Visits remain globally numbered across the entire playthrough. Session boundaries do not reset visit
numbers.

## Explicit sessions

A playthrough may contain an unsegmented portion followed by any number of explicit sessions.
Sessions never partition or replace the journal; they annotate ranges in the one continuous history.

### Session start

`session_started` records:

- a one-based `session_number`;
- an optional `title`;
- an optional ISO calendar date `played_on`;
- zero or more `participants`;
- an optional `attendance_note`; and
- an optional `opening_note`.

Session numbers are contiguous among active session starts. At most one session may be active.
Starting a session while another is active is invalid.

### Session end

`session_ended` records:

- the active `session_number`; and
- an optional `closing_note`.

Ending a session when no session is active, or naming any session other than the active one, is
invalid.

### Unsegmented and out-of-session behavior

A schema-version-6 journal may contain an initial unsegmented portion with no session number. This
preserves journals that began before the table chose to record explicit sessions without requiring an
older persisted schema.

A journal that has never contained an active `session_started` event may continue
to accept ordinary play operations outside a session. Once the first explicit session is started,
subsequent non-correction play operations must occur inside an active session. Corrections may occur
outside a session because post-session data repair must remain possible.

This rule gives existing journals a conservative migration path while making explicit sessions the
normal invariant for new Play mode use.

### Session projection

A session projection records its metadata, start and optional end sequence, active status, operation
range, and visit range. Events between a start and its matching end belong to that session. Correction
events retain their actual sequence but affect the active projection in the usual way.

Voiding the latest session-end operation reopens that session. Voiding a session start is possible
only after every later active operation has already been voided, so it cannot orphan active content.

## Clue outcomes

Authored clues do not acquire one permanent runtime status. Play history records discoveries and
missed opportunities.

### Unresolved

A clue is unresolved when it has not been spotted. It may have no missed opportunities or several.
Unresolved is derived, not an event.

### Missed on a visit

`clue_missed` records one missed opportunity and identifies:

- the authored `clue_id`; and
- the source `visit_number`.

The visit must exist and must be to the clue's authored source encounter. The same clue cannot be marked
missed twice on the same visit. A clue already spotted cannot acquire a later missed event.

A miss does not make the clue unavailable. The clue may be spotted on a later revisit. It may also be
spotted later during the same visit if circumstances produce another genuine opportunity; the ledger
then truthfully shows both the earlier miss and the later discovery.

### Found

`clue_spotted` retains its current meaning: the first recorded discovery of the clue, tied to a visit
to its authored source encounter. A clue can be spotted only once among active operations.

A found clue remains found even if it had earlier missed opportunities. The clue ledger preserves
those misses as history.

### Unavailable

“Unavailable” is not a first-class clue state in version 4. If a clue can no longer be recovered, the
GM records the fictional cause as an encounter consequence. A future availability model may promote this to
an explicit rule only after the project can represent changing clue opportunities generally.

## Revelation states

Support and knowledge remain different.

### Unsupported

A revelation is unsupported when no authored supporting clue has been spotted. This is derived.

### Supported

A revelation is supported when at least one authored supporting clue has been spotted but the
revelation has not been established or currently foreclosed. Support does not automatically establish
knowledge.

### Established

`revelation_established` records an explicit conclusion reached by the players or GM. It may cite zero
or more previously spotted supporting clues and may include a note. An empty clue basis remains valid
for direct testimony, magic, deduction outside authored clues, or another adjudicated route.

An established revelation cannot be foreclosed. If it unlocks an encounter, the matching `encounter_unlocked`
event remains in the same operation.

### Foreclosed

`revelation_foreclosed` records that the GM judges the revelation no longer establishable in the
current fictional situation. It requires a nonblank reason.

Foreclosure is never inferred from clue counts, encounter exits, missed clues, or validation thresholds. A
supported revelation may be foreclosed, and later clue discoveries may remain historically relevant,
but the current state remains foreclosed until explicitly reopened.

An established revelation cannot be foreclosed, and a foreclosed revelation cannot be established
until reopened.

### Reopened

`revelation_reopened` reverses an active foreclosure and requires a nonblank reason. It exists because
the existing correction command can only void the latest active operation. A GM must be able to
change a foreclosure judgment later without rolling back unrelated intervening play.

Reopening does not establish the revelation, erase the earlier foreclosure, or change clue support.
It restores the revelation to unsupported or supported according to the clues spotted so far. A
revelation may be foreclosed and reopened more than once.

## Encounter notes and legacy consequences

### Working visit notebook

A working notebook is ephemeral. Autosave must not append journal events per keystroke. The first Play
mode may persist drafts in browser storage, keyed by adventure identity and visit number, with a
visible local-save state.

A draft becomes canonical only when the GM explicitly commits it, completes a transition that
includes it, or ends the session and chooses to save it. Failed or stale writes must preserve the
submitted draft.

### Committed visit notes

`visit_note_recorded` remains an append-only note attached to an active visit. A later clarification is
another note. The original event is never edited.

### Legacy encounter consequences

`encounter_consequence_recorded` remains part of the journal contract so existing play records continue to
project correctly. It stores a durable change attached to an authored encounter rather than a visit.
The ordinary GM interface no longer asks the GM to classify a note this way: a single encounter-note
composer accepts immediate events, future-facing consequences, and any other table record. When an
older journal contains consequence events, Play mode surfaces them as **earlier persistent notes** on
future visits. Developer commands and recovery adapters may continue to read or write the legacy event
until a later schema migration retires it.

## Dice expressions and recorded rolls

Dice are a table utility first and journal content only by explicit choice.

### Grammar

The accepted grammar is:

```text
expression := signed_term (space? add_op space? term)*
signed_term := [add_op] term
add_op := "+" | "-"
term := dice | integer
dice := [count] ("d" | "D") faces
count := positive decimal integer
faces := decimal integer greater than or equal to 2
integer := nonnegative decimal integer
```

Examples:

```text
4d6
2d8 + 1d4
12d10 + 7
2d20 - 1d4 + 3
-d6 + 10
```

A missing count means one die. Whitespace is insignificant between terms and operators. The parser
normalizes `D` to `d`, inserts an explicit count, removes redundant leading plus signs, and emits one
canonical expression for display and recording.

### Resource limits

The first implementation uses the following limits:

- at most 256 input characters;
- at most 20 terms;
- at most 1,000 dice in one expression;
- at most 1,000 dice in one group;
- between 2 and 1,000,000 faces per die; and
- absolute integer modifiers no greater than 1,000,000,000; and
- optional roll labels no longer than 160 characters.

Malformed expressions and limit violations are rejected before random values are generated.

### Randomness

Rolls use the operating system through `secrets.randbelow(faces) + 1` or an injected equivalent. The
production roller must not use a predictable seeded pseudo-random generator. Tests use an injected
deterministic source rather than weakening production randomness.

### Result model

A roll result preserves ordered terms. A dice term records its sign, face count, and individual
results. A modifier term records its signed integer value. Group subtotals and the final total are
derived and validated.

An unrecorded result remains ephemeral. `dice_roll_recorded` stores only a roll the GM explicitly
chooses to retain. It records:

- the normalized `expression`;
- an optional `label`;
- the ordered result `terms`; and
- the validated final `total`.

No timestamp is added solely for dice. The journal preserves order, and explicit session metadata
provides the table context without introducing a second time model.

## Schema-version-6 event contract

Version 6 retains the complete version-5 encounter vocabulary and adds `reference_note_recorded` with a
stable `reference_id` and nonempty `text`. Canonical JSON uses `encounter_visited`,
`encounter_unlocked`, and `encounter_consequence_recorded`, with `encounter_id` on each event. Every
visit writes `party_label`, using an empty string when the table has no split-party label.

The complete event vocabulary remains closed and fail-closed: session boundaries, encounter visits,
clue outcomes, revelation judgments, recorded dice, encounter unlocks, visit notes, encounter
consequences, persistent-reference notes, and append-only corrections. Every event carries contiguous
one-based `sequence` and `operation_number` fields. The flat event journal remains canonical; version 6 does not introduce
nested operation objects.

## Operation grouping

The following narrow commands each append one operation:

- start session;
- end session;
- enter or revisit an encounter, optionally with immediate clues and initial notes;
- spot one clue;
- mark one clue missed;
- establish one revelation and perform its automatic unlock if needed;
- foreclose one revelation;
- reopen one revelation;
- unlock one encounter explicitly;
- append one visit note;
- append one persistent-reference note;
- record one encounter consequence;
- record one significant dice roll; and
- correct the latest active operation.

The transition command may append several event variants under one operation number. It
uses this phase order:

1. notes committed to the visit being left;
2. clue discoveries and missed opportunities for that visit;
3. revelation establishments, each followed immediately by its automatic unlock when needed;
4. revelation foreclosure or reopening judgments;
5. encounter consequences;
6. an optional final `encounter_visited` for the destination.

The destination visit, when present, is last. The transition operation does not include immediate
clues or notes for the destination; those belong to later table actions. Every referenced visit before
the optional destination must be the current visit at the start of the operation.

No marker event is required. The journal validator recognizes the compound operation by its event
set and phase ordering. The entire operation is committed in one project write and is voided as one
unit by the correction command.

A transition may omit every category except at least one content event. Merely changing browser focus
or clearing an empty draft is not a canonical operation.

## Correction behavior

The current correction rule remains: `operation_voided` may target only the latest active content
operation. It preserves all target events for audit and removes their effect from the active
projection.

Applied to new events:

- voiding `session_started` removes the boundary and its metadata, but only after later active content
  has already been voided;
- voiding `session_ended` reopens the session;
- voiding `clue_missed` removes that missed opportunity;
- voiding `revelation_foreclosed` restores the prior revelation state;
- voiding `revelation_reopened` restores the foreclosure;
- voiding `dice_roll_recorded` removes only the canonical record, not any real-world roll; and
- voiding `reference_note_recorded` removes that note from active reference and narrative projections;
- voiding `encounter_consequence_recorded` removes that consequence from the active projection; and
- voiding a compound transition removes every event in that transition, including its destination
  visit.

A later change of judgment is not necessarily an error. Revelation reopening is therefore a normal
content event rather than a targeted historical correction. Likewise, finding a clue after a miss is
new play, not correction.

## Pre-beta schema boundary

Schema version 6 is an intentional final pre-beta breaking boundary. The loader rejects play-state
versions 1 through 5. The repository migrated every bundled active journal, archive journal, schema,
example, and test in the same change. Version 6 preserves all version-5 event shapes and adds the
reference-note event before tester-created journals become compatibility inputs.

This policy is limited to the pre-beta window. After the beta contract is frozen, any incompatible
journal change requires an explicit versioned migration decision.

## Worked histories

### Missed clue recovered on a revisit

```json
[
  {
    "sequence": 1,
    "operation_number": 1,
    "type": "session_started",
    "session_number": 1,
    "title": "The Hall and the Stockyards",
    "played_on": "2026-07-18",
    "participants": ["Mara", "Sera", "Nell", "Orris"],
    "attendance_note": "",
    "opening_note": ""
  },
  {
    "sequence": 2,
    "operation_number": 2,
    "type": "encounter_visited",
    "visit_number": 1,
    "encounter_id": "southgate-stockyards",
    "party_label": "Main party"
  },
  {
    "sequence": 3,
    "operation_number": 3,
    "type": "clue_missed",
    "clue_id": "the-obsolete-survey-marker-socket",
    "visit_number": 1
  },
  {
    "sequence": 4,
    "operation_number": 4,
    "type": "encounter_visited",
    "visit_number": 2,
    "encounter_id": "southgate-stockyards",
    "party_label": "Mara and Orris"
  },
  {
    "sequence": 5,
    "operation_number": 5,
    "type": "clue_spotted",
    "clue_id": "the-obsolete-survey-marker-socket",
    "visit_number": 2
  }
]
```

The clue is currently found. Its ledger also records one missed opportunity at visit 1.

### Foreclosure later reversed

```json
[
  {
    "sequence": 8,
    "operation_number": 8,
    "type": "revelation_foreclosed",
    "revelation_id": "the-council-will-open-the-lower-gate",
    "reason": "The council adjourned after the forged order was exposed."
  },
  {
    "sequence": 9,
    "operation_number": 9,
    "type": "encounter_consequence_recorded",
    "encounter_id": "the-council-vault",
    "text": "Captain Vey took custody of the forged order."
  },
  {
    "sequence": 10,
    "operation_number": 10,
    "type": "revelation_reopened",
    "revelation_id": "the-council-will-open-the-lower-gate",
    "reason": "The rescued archivist can compel an emergency reconvening."
  }
]
```

The consequence remains active. The revelation returns to supported or unsupported according to the
clues found so far.

### Split-party alternation

```json
[
  {
    "sequence": 12,
    "operation_number": 12,
    "type": "encounter_visited",
    "visit_number": 5,
    "encounter_id": "the-college-of-civic-measure",
    "party_label": "Orris and Sera"
  },
  {
    "sequence": 13,
    "operation_number": 13,
    "type": "encounter_visited",
    "visit_number": 6,
    "encounter_id": "rillcross-farm-belt",
    "party_label": "Mara and Nell"
  },
  {
    "sequence": 14,
    "operation_number": 14,
    "type": "encounter_visited",
    "visit_number": 7,
    "encounter_id": "the-college-of-civic-measure",
    "party_label": "Orris and Sera"
  }
]
```

The route remains one honest table chronology. Party labels make the alternation legible without
creating parallel mutable journals.

### Significant recorded roll

```json
{
  "sequence": 20,
  "operation_number": 20,
  "type": "dice_roll_recorded",
  "expression": "2d8 + 1d4 + 3",
  "label": "Hold the west gate",
  "terms": [
    {"kind": "dice", "sign": 1, "faces": 8, "results": [6, 3]},
    {"kind": "dice", "sign": 1, "faces": 4, "results": [2]},
    {"kind": "modifier", "value": 3}
  ],
  "total": 14
}
```

The expression, individual dice, and total are auditable. An ordinary unrecorded roll creates no
journal event.

## Acceptance scenarios and delivery status

Milestone 2 is complete when automated tests prove the canonical journal and projection behavior:

1. Versions 1 through 5 are rejected, while schema version 6 round-trips every event variant.
2. An unsegmented schema-version-6 journal may continue outside a session until its first explicit session begins.
3. Sessions cannot overlap, end out of order, or reuse session numbers.
4. Visit numbers remain global and contiguous across sessions.
5. Alternating `party_label` values do not affect visit legality or route chronology.
6. A clue may be missed on visit 1 and spotted on visit 3.
7. A duplicate miss for one clue and visit is rejected.
8. A clue already spotted cannot later be marked missed.
9. A supported revelation may be foreclosed.
10. An established revelation cannot be foreclosed.
11. A foreclosed revelation cannot be established until reopened.
12. Reopening restores support derived from existing spotted clues.
13. Corrections correctly reopen sessions and restore prior revelation judgments.
14. Recorded dice results round-trip and reject inconsistent totals.
15. A reference note retains stable identity, appears in chronological GM records, and remains outside
    the player-safe recap.
16. Encounter focus, selected references, typed encounter/reference pins, drafts, and unrecorded rolls
    remain absent from canonical play-state JSON.

Those scenarios are implemented and covered at the domain, persistence, application, CLI, and
browser layers. The atomic transition now commits completely in one project write, preserves
submitted browser values after rejected writes, and is voided as one operation. One accepted
semantic deliberately lands later because it belongs to a separate vertical slice:

- dice parsing enforces every resource limit before requesting randomness in milestone 6.

## Deferred questions

The following remain deliberately outside version 6:

- first-class clue unavailability;
- parallel journals for independently operating parties;
- structured character or player identities;
- selective correction of arbitrary historical operations;
- timestamps on every event;
- editable session metadata through targeted amendment events;
- campaign-wide state spanning several adventures; and
- system-specific dice semantics such as advantage, exploding dice, success counting, or keep/drop.

Each may be added later without changing the state boundary fixed here.
