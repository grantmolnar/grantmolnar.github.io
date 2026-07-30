# Private-beta breaking-change audit

## Scope and decision rule

This audit was performed immediately before the first externally shared desktop build, while repository
compatibility was still the only compatibility obligation. It reviewed the current persisted schemas,
canonical JSON pipeline, workspace and adventure identity, journal archive identity, coordinated file
transactions, desktop settings, browser composition, and release-path module boundaries.

A change was accepted only when it closed a concrete data-integrity or cross-platform portability hazard.
Large-file cleanup and speculative abstractions were not treated as release hardening.

## Accepted pre-beta contract corrections

### Play journals advance to schema 6 for persistent-reference notes

The final pre-distribution feature slice adds `reference_note_recorded`, carrying one stable authored
`reference_id` and nonempty note text. The event is append-only, participates in ordinary operation
correction, appears in GM chronological records, and remains outside the player-safe recap. Authoring
removal is blocked while a related journal names that reference, so the historical association cannot
become dangling.

This is an intentional pre-beta schema migration from play-state version 5 to version 6. Every bundled
active journal and archive journal was converted atomically. The loader rejects versions 1 through 5;
version 6 retains all version-5 event shapes and adds only the new event variant. No tester-created
workspace existed when this boundary moved.

### Canonical JSON output is bounded before mutation

Readers, browser uploads, and transaction recovery already imposed an 8 MiB ceiling, but canonical writers
could previously serialize a larger object. Such a write could produce a file that the same release could not
reopen and a transaction artifact that recovery would reject. All canonical JSON encoding now passes through
one application-boundary byte limit before any single or coordinated replacement begins. A multi-file write
encodes and validates every destination before mutating any destination.

This does not change a schema shape or field meaning. It makes the documented operational ceiling symmetric
across reads, uploads, downloads, writes, and recovery artifacts.

### Journal archive identifiers are filesystem-portable

Archive identifiers now contain at most 80 ASCII filename-safe characters and remain unique without regard
to case inside one archive catalog. Explicit identifiers fail before mutation, derived identifiers preserve
the timestamp prefix and truncate only their title- or label-derived suffix, imports use the same rule, and a
catalog containing manually introduced case-only duplicates fails closed.

The schema-1 `archive.id` definition now records the 80-character ceiling. This is an intentional pre-release
tightening of schema 1 rather than a schema migration: no external beta workspace existed, the five bundled
archives already satisfy it, and preserving the previously unbounded filename surface would create avoidable
Windows and macOS transfer risk. Once private-beta workspaces exist, an equivalent accepted-value change must
use the normal schema and migration decision process.

### Browser adventure download names are bounded

Adventure identity and content are unchanged, but a title-derived browser download filename now limits its
slug stem to 80 characters. This prevents a valid long title from producing an unnecessarily fragile local
filename. Import never uses that filename as adventure identity.

## Reviewed contracts retained unchanged

- Adventure schema 3, workspace-settings schema 1, and journal-archive payload version 1 retain their
  object structures and field meanings. Play-state schema 6 retains every schema-5 field meaning and adds
  the explicit persistent-reference note event described above.
- Stable adventure identity remains the embedded adventure identifier, not a title, workspace directory, or
  download filename.
- Workspace selection remains a workspace-relative source key; relocation behavior and root/direct-child
  discovery remain unchanged.
- Portable adventure import continues to create a new project and empty journal. Portable playthrough import
  continues to resolve or verify embedded adventure identity and never replaces the active journal.
- Transaction marker version 1, commit protocol, recovery states, and on-disk marker shape remain unchanged.
- Desktop settings remain a small external launcher preference containing the last workspace. Malformed or
  unavailable settings still recover through explicit workspace selection rather than silent project edits.

## Module-responsibility findings

No release-path decomposition was justified in this pass. This is a historical pre-release finding. A
later compatibility-safe maintenance pass extracted the complete authoring POST family—not isolated
branches—into `interfaces/web/authoring_action_workspace.py` after that family had a distinct mutation,
redirect, and form-reconstruction reason to change.

- `interfaces/web/app.py` is large, but its remaining authoring dispatch still forms one cohesive route family.
  Extracting isolated branches would increase indirection without removing a dependency or failure mode.
- `interfaces/web/play_rendering.py` remains a substantial presentation module, but archive, report, journal,
  run, and authored-entity rendering already have clear owners. A template framework would be disproportionate
  before beta.
- `web_composition.py` correctly owns concrete adapter wiring and path-free translation of local transfer
  failures. Its repeated project construction should become a shared factory only when another process adapter
  needs the same aggregate or the set of project adapters changes materially.
- `desktop.py` and `infrastructure/desktop_settings.py` have distinct launcher and persistence responsibilities.
  Their current callback structure does not justify another abstraction while the launcher remains thin.

## Deferred cleanup triggers

These are not beta blockers:

- Introduce a typed descriptor for generated download names only if another portable document family appears.
- Revisit browser composition factories if a second non-browser process needs the complete local project
  aggregate.
- Split desktop UI callbacks only if the launcher gains settings beyond workspace selection and open/reopen.
- Continue route-family extraction only when a complete family owns parsing, execution, redirects, and error
  rendering end to end.

## Compatibility conclusion

The accepted changes intentionally reject only states that can make a canonical file unreadable by the same
release or make an archive catalog ambiguous across supported filesystems. No migration is required for the
source development corpus. After the first tester receives a build, this pre-release amendment window is closed and future
persisted-contract changes must account for tester-created workspaces explicitly.
