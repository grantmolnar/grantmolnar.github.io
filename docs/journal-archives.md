# Journal Archives

Actual-play journals are disposable only when the user chooses to make them disposable. Adventure
Graph therefore treats reset as an archival operation rather than truncating `play-state.json` in
place.

## Browser workspace

The local web interface provides an **Archives** workspace beside the CLI commands described below.
It lists immutable archives, reports the active-journal event count, and compares each archived
adventure snapshot with the current authored project at the encounter, revelation, clue, and top-level
prose levels. Compatibility is determined by projecting the archived journal against the current
adventure.

The browser can export a non-empty active journal without resetting it, export any stored archive, and
import a portable archive through either the Adventures catalog or the selected adventure's Archives
workspace. Catalog import resolves the embedded adventure identity to exactly one workspace project;
Archives import requires that identity to match the selected adventure. Both paths persist the validated
canonical content under its embedded identifier, refuse an identifier already present in the destination
catalog, add an immutable archive, and leave the active journal unchanged.

Browser archive creation, export, import, restore, and deletion use the same application boundaries as
local persistence. Each modifying form carries an aggregate revision covering the adventure, active
journal, and archive directory. A stale submission receives HTTP 409 before any file changes occur. Restore remains available only
when the active journal is empty and the archived journal is compatible. Restoration leaves the
archive unchanged; permanent deletion remains a separate action requiring the exact identifier.

## Portable export and import

In the browser, **Export current playthrough** packages the current non-empty journal with the exact
adventure snapshot while leaving `play-state.json` unchanged. **Export playthrough** on an archive detail
page downloads an existing immutable archive. Both produce the canonical filename
`<archive-id>.journal.json`.

Use **Import playthrough** in the Adventures catalog when the application should locate the destination
from the file itself. The workspace importer requires exactly one project with the embedded stable
adventure identity and does not change the selected adventure. Use **Import for this adventure** in the
Archives workspace when the intended destination is already selected. That narrower form requires the same
identity
to match the selected adventure explicitly.

Both import paths accept one canonical JSON document up to 8 MiB and validate the complete archive,
embedded journal, event count, adventure identity, canonical identifier, and current project revision before
writing. Archive identifiers contain at most 80 ASCII filename-safe characters and are unique without regard
to case so a workspace remains portable across supported filesystems. A matching imported archive appears in the destination catalog and can then be compared or restored
through the ordinary guarded workflow. Titles are never used as identity, and a duplicate archive identifier
is rejected. Malformed, oversize, stale, or invalid uploads leave the catalog unchanged and return the user to
the relevant form with an actionable message. Local write failures report permission, disk-space, or unsafe
layout guidance without placing workspace paths in the browser response.

Portable adventure documents are transferred separately from the Adventures catalog. Exporting an
adventure downloads only its canonical authored JSON; importing it creates a new project with an empty
journal. When no project matches a playthrough, transfer the adventure first and then retry catalog import.

## Archive

```bash
adventure-graph archive adventure.json play-state.json \
  --label "First table run"
```

The command:

1. loads and projects the active journal against the current adventure;
2. refuses an empty journal;
3. writes a self-contained `*.journal.json` archive below a sibling `archives/` directory by
   default; and
4. replaces the active state with a canonical empty schema-version-6 journal.

Use `--archive-dir PATH` to choose another directory. Use `--name ID` to supply a stable archive
identifier; otherwise the command derives one from the UTC timestamp and label or adventure title.
Archive names may contain at most 80 letters, digits, periods, underscores, and hyphens and must begin
with a letter or digit. Names are unique without regard to case. The persisted filename is canonical and
must be exactly `<archive-id>.journal.json`. Do not rename or duplicate an archive file inside an active
archive directory; the catalog rejects a filename that disagrees with the embedded identifier or creates a
case-only collision rather than choosing one of several ambiguous copies.

Each archive contains:

- metadata and event count;
- the exact authored adventure snapshot active at archival time; and
- the complete play-state journal.

The snapshot makes the historical journal interpretable even after later authoring changes. Archives
are immutable and are not rewritten by encounter, revelation, or clue renames.

## List

```bash
adventure-graph list-archives archives
```

The listing reports the archive identifier, adventure title, event count, UTC archival timestamp,
and optional label.

## Restore

```bash
adventure-graph restore-archive \
  adventure.json \
  play-state.json \
  archives/first-table-run.journal.json
```

Restoration copies the embedded journal into the active state path and retains the immutable archive.
The active journal must be empty; otherwise the command refuses to overwrite it and instructs the
user to archive it first. There is no `--consume` mode: users who intentionally want to remove the
archive must perform the separate, confirmed `delete-archive` operation.

The restored journal is projected against the current adventure before any file changes occur. A
historical archive can therefore be restored after harmless prose changes, but not after an
incompatible authoring change that makes its events false. When the current adventure differs from
the archived snapshot but remains compatible, the command reports that fact.

The archive file is not rewritten, renamed, or temporarily moved. Restoration performs one
same-directory atomic replacement of the active journal. Archive-and-reset uses the multi-file
transaction layer: interruption before its committed marker restores the original active journal and
removes the new archive; interruption after that marker retains both the complete archive and the
canonical empty journal. Because restoration retains the archive, its exact adventure snapshot and
journal pairing can still be inspected or restored again later.

## Delete

```bash
adventure-graph delete-archive \
  adventure.json \
  play-state.json \
  archives/first-table-run.journal.json \
  --confirm first-table-run
```

Deletion is permanent. The confirmation must exactly match the archive identifier. When `--confirm`
is omitted, the CLI prompts for the identifier. There is intentionally no generic `--yes` bypass.

The command loads the current adventure, active journal, and complete archive catalog at one
aggregate revision. It refuses stale requests, invalid adventure/journal pairings, and archives that
belong to a different adventure before deleting any file. The browser uses the same application
command and revision-aware local archive project.

The `delete-archive` command applies only to journal archives. Authored entities continue to use the
`remove-encounter`, `remove-revelation`, and `remove-clue` commands with their separate dependency rules.
