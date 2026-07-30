# Source snapshot portability roadmap

## Status

This bounded release-engineering interruption began after the Windows compressed-folder copy operation for
`adventure-graph-0.10.0-aurelune-reference-defragmentation-session-04` failed with error `0x80010135`
(`Path too long`). The replacement source snapshot subsequently completed an ordinary Windows Explorer
**Extract All** operation without the error recurring. The accepted Aurelune content remains unchanged, all
six phases are complete, and the corpus checkpoint resumes at *The Forest That Carries Dawn — Reference
Extraction I*.

## Characterized defect

The failed archive repeated its 68-character descriptive session label as its internal root. Its longest
repository-relative path was 106 characters, but its longest ZIP member was 175 characters. The reported
Cauldron reference member was 168 characters. The archive therefore converted an acceptable repository tree
into a fragile packaged tree before the user's destination directory and Explorer's own working paths were
added.

The defect is in source-snapshot construction, not in reference identity, generated-sheet naming, Aurelune
content, or the desktop artifact contract.

## Accepted contract

A maintained source snapshot must:

- use `adventure-graph/` as its sole internal root regardless of the descriptive ZIP filename;
- contain only regular repository files and no symbolic links, cache directories, virtual environments,
  build output, local environment files, or nested prior artifacts;
- use deterministic ordering, timestamps, permissions, and compression;
- contain no duplicate, case-colliding, absolute, parent-traversing, backslash, or encrypted member;
- keep every archive member at or below 138 characters;
- thereby support an extraction destination prefix of up to 120 characters while keeping the complete
  extracted path at or below the project's 259-character legacy-Windows ceiling;
- include the private-beta terms, README, project metadata, and runtime package root; and
- verify itself immediately after construction.

The 138-character member budget leaves the repository 122 characters for a relative path beneath the stable
root. The current maximum is 106 repository-relative characters and 122 archive-member characters.

## Roadmap

### Phase 1 — Reproduce, measure, and freeze content — complete

- Measured the old internal root, failing member, maximum member, and repository-relative maximum.
- Confirmed that the 68-character duplicated root accounts for the packaging inflation.
- Preserved the accepted Aurelune authored source, generated packet, reference identities, and journal
  evidence without modification.

### Phase 2 — Establish the source-snapshot contract — complete

- Chose a short recognizable root rather than a cryptic root or a rootless archive.
- Reserved a conservative destination-prefix budget rather than depending on machine-wide long-path policy.
- Kept descriptive version and session information in the external ZIP filename only.
- Declined to rename UUID-backed generated references or shorten adventure directories without evidence that
  the corrected archive remains unsafe.

### Phase 3 — Implement construction and verification — complete

- Added `scripts/source_snapshot.py` with `audit`, `build`, and `verify` commands.
- Added deterministic ZIP construction and fail-closed path, collision, symlink, secret, and required-member
  checks.
- Added `make source-audit`, `make source-package`, and `make source-verify`.
- Integrated source-snapshot construction into `make ci`.

### Phase 4 — Add regression evidence and maintainer guidance — complete

- Added focused tests for the live repository budget, deterministic output, stable internal root, declared
  extraction prefix, legacy descriptive-root rejection, over-budget members, unsafe paths, case collisions,
  and local-artifact exclusions.
- Added a durable source-snapshot guide and updated the README, test strategy, changelog, and active corpus
  roadmap.
- Built and verified a replacement archive from the unchanged content baseline.

### Phase 5 — Native Windows acceptance — complete

- The replacement ZIP was unpacked through the ordinary Windows Explorer workflow without error
  `0x80010135` recurring.
- No drive-root relocation, global long-path policy, or third-party extractor was required.
- The user confirmed successful unpacking; the exact destination string was not retained in the acceptance
  report. This does not weaken the observed extraction result, but future acceptance records should retain
  the destination for reproducibility.
- This was an extraction acceptance check, not a complete native desktop signoff.

### Phase 6 — Close or escalate — complete

- Closed the portability interruption after native acceptance.
- Retained `adventure-graph/` as the internal root; the authorized `ag/` fallback and repository-path
  shortening were unnecessary.
- Resumed the corpus roadmap at Forest Reference Extraction I from the portability-repaired source.

## Local implementation evidence

The repaired source records the following local evidence:

- 907 eligible source files audited;
- longest repository-relative path: 106 of 122 permitted characters;
- longest archive member: 122 of 138 permitted characters;
- 659 unit tests passed;
- 53 architecture tests passed;
- 344 integration tests passed, including 280 corpus/content tests and 64 CLI/browser-boundary tests;
- 44 package-metadata and tooling-configuration tests passed;
- all 47 smoke assertions passed in bounded runs, although this managed host did not let the combined smoke
  process terminate after the `web_composition` import group;
- 39 JSON documents validated against the published schemas;
- Python compilation and JavaScript syntax validation passed; and
- a full Linux extraction simulation opened the exact Cauldron UUID sheet reported by Windows.

The wheel built successfully. The clean-wheel beta lifecycle did not complete in this managed host before
the execution limit and is not claimed. Ruff, Pyright, and Hypothesis were unavailable and are not claimed.
The ordinary native Windows Explorer extraction check subsequently passed.

## Deliberate non-changes

- No authored adventure, play journal, schema, UUID, generated-reference filename, or content roadmap item
  changed.
- Desktop application archives retain their separate native artifact and manifest contract.
- The source snapshot remains a maintainer/development handoff, not the lightweight end-user application.
- Handoffs remain outside the source ZIP so the archive does not accumulate its own continuation records.
