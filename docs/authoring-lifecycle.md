# Authoring Lifecycle

## Scope

The authored adventure is one immutable aggregate. The browser is the primary GM-facing interface;
the CLI exposes the same application seams for development, automation, and recovery. Neither
interface partially mutates nested records.

## Queries

`list` and `inspect` expose compact inventories and direct dependencies. They are developer tools and
do not require a play-state file. Repeat `inspect --state PATH` when a dependency preview should also
identify journal blockers; ordinary inspection remains available when a companion journal is missing or
malformed.

## Stable identity

Adventure, encounter, revelation, clue, and reference identifiers are durable machine identity, not
editable presentation. New adventures and new references receive opaque UUIDv4 identifiers. New
encounters, revelations, and clues receive readable identifiers derived from their initial titles, with
numeric suffixes when necessary for local uniqueness. Existing slug-shaped adventure IDs remain valid
stable identifiers.

Editing a title never changes an identifier. It therefore never rewrites authored references, play
journals, browser routes, draft keys, bookmarks, or automation. Ordinary authoring exposes no raw
identifier field or rename command. Internal rename and journal-remapping helpers exist only for
controlled repair and explicit future migrations.

## Minimal project creation

A browser-created adventure requires only a title. Creation assigns opaque adventure identity, writes a
matching empty journal, and permits empty encounter, revelation, and clue collections. Optional authored
prose and tags may be added later. The opening encounter in the creation wizard is a convenience rather
than a structural prerequisite. When it is omitted, the browser's encounter-creation command can add the
first encounter later and selects the start role by default.


## Incremental creation

An encounter requires only a title; summary, opening description, body, and tags may remain empty. A
revelation likewise requires only a title; its description and destination are optional. A reference
requires a kind and title; aliases, summary, Markdown content, and tags may remain empty, although a
title-only record produces a validation warning. `add-reference` creates that record with opaque UUIDv4
identity, and `link-reference` appends an optional contextual link to one encounter. The browser's
contextual creation action uses `CreateAndLinkReference` so identity creation, reference insertion, and
the first encounter link either commit together or do not change the project. The current-schema
contract therefore supports incremental authoring without placeholder prose.

## Field updates and clue moves

`edit-encounter`, `edit-reference`, `edit-revelation`, and `edit-clue` update descriptive and
structural fields. A title or alias change preserves the internal identifier and existing links.
`move-clue` changes only the clue source. `link-reference` and `unlink-reference` change only one
encounter-owned association while preserving the order of every remaining record. All referenced
sources, revelations, destinations, encounters, and references must already exist, duplicate links fail
closed, missing unlink pairs fail clearly, and no-op edits are refused.

Before persistence, every known related play journal is projected against the proposed adventure.
This rejects changes that would falsify recorded play, including moving a discovered clue away from
its recorded visit or changing a revelation destination after its automatic unlock was recorded.

## Related play-state discovery

Structural edits accept repeatable `--state PATH` options. Without them, the CLI uses the canonical
companion journal when present: `play-state.json` beside `adventure.json`, or
`<name>.play-state.json` beside a standalone `<name>.adventure.json`. Supplying any explicit state
path disables implicit discovery. The package cannot discover arbitrary journals elsewhere.

## Dependency-aware removal

The implemented reference-library lifecycle preserves the existing fail-closed removal rule.

Removal refuses authored dependents unless `--cascade` is explicit. Cascading an encounter removes clues
sourced there, clears revelation destinations, and removes its subordinate reference links while
retaining the referenced records. Cascading a revelation removes its supporting clues. Cascading a
reference removes the record and unlinks it from every encounter without removing those encounters. The
CLI exposes this operation as `remove-reference`; `edit-reference`, `link-reference`, and
`unlink-reference` cover the non-destructive lifecycle. Every preview reports the affected links before
persistence.

A known journal always prevents removal of an encounter, revelation, or clue it references. First-beta
journals do not target references, so they do not block reference removal; immutable archives retain
their own historical adventure snapshots. There is no force option that rewrites history.

## Persistence contract

Ordinary title and field edits persist only the adventure because identity and journal references
remain
unchanged. Structural edits are still validated against every known related journal before commit.
Operations that genuinely change both adventure and journal bytes use the coordinated authoring
commit. The infrastructure writes transaction markers, fsynced new payloads, and original-byte
backups before replacing destinations. An interruption before the committed marker restores the prior
revision on the next canonical read; an interruption after that marker retains the complete new
revision and cleans its artifacts. This guarantee is local-filesystem and single-writer, not a
distributed transaction or substitute for version control. See the Session 5 durability record for
platform limits.
