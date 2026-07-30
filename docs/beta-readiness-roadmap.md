# Beta-readiness roadmap

## Status

Adventure Graph 0.10.0 has a deliberately narrow tester-facing content scope. The wheel and native
application package one sample adventure, *The Glass Saint*. The remaining adventures under `examples/`
are an internal development corpus: they remain valuable for tests and editorial work, but they are not
shipped in the runtime artifacts and do not block the first application beta.

The browser now exposes the packaged sample without requiring the CLI. An empty catalog offers an explicit
**Add The Glass Saint sample** action, and the New Adventure page offers the same choice. Each use creates a
freshly identified editable project with an empty playthrough; no workspace is modified merely by opening
it. A packaging contract requires that no other adventure JSON be present in runtime resources.

The remaining release sequence is:

1. run the connected static-analysis, property, dependency, security, and live-browser pipelines against
   the exact accepted application-and-sample revision;
2. build and retain native desktop artifacts on the intended tester platform, with hosted cross-platform
   evidence where support is claimed;
3. verify each downloaded archive against its adjacent manifest and accepted source revision; and
4. complete the checked-in manual platform protocol against the artifact actually sent to the tester.

The desktop launcher and native build pipeline are implemented. Local qualification has been refreshed
against the application-and-sample source: deterministic tests, coverage, static Chromium checks, schemas,
source portability, wheel construction, and the installed lifecycle pass. No native executable is represented
as passing until the connected pipelines, native build, manifest verification, and real-platform manual
protocol pass against this exact source revision.

## Operating rules

- Correctness, data integrity, security, and reproducibility defects may interrupt the roadmap.
- Do not reopen a frozen contract merely to make an internal implementation more elegant.
- Browser and CLI mutations continue to cross the same application boundaries.
- Persisted data changes require an explicit schema and migration decision.
- Local evidence and hosted or manual platform evidence must remain clearly distinguished.
- Conditional cleanup findings belong in `backend-maintenance-map.md`, not in progress diaries.

## Frozen 0.10.0 contracts

The completed beta-readiness work established these durable contracts:

- every adventure, encounter, revelation, and clue has stable opaque identity independent of its title;
- all ordinary CLI and browser mutations use revision-aware application or project boundaries;
- archive restoration is non-destructive and archive filenames are part of archive identity;
- current readers default omitted known fields but reject unknown fields and out-of-range values;
- coordinated local-file writes have an explicit commit point and startup/read recovery;
- the loopback server rejects unsafe Host headers, ambiguous targets, malformed or oversized input,
  unsafe paths, excessive JSON depth, excessive journal length, and unescaped rendered values;
- workspace discovery is root/direct-child only, rejects hidden and symlinked project directories, and
  never silently substitutes a different project for a missing saved selection;
- each initialized project receives fresh UUIDv4 identity and a portable bounded directory name;
- a project directory containing `adventure.json` may be launched directly;
- the wheel is runtime-only, contains the enforced package payload, and is capped at 2 MiB; and
- the supported Python range is CPython 3.11 through 3.13.

These contracts are protected by the test suite, schemas, clean-wheel smoke, engineering standards,
and the durable architecture and format documentation. The former per-session reports have been
removed because they duplicated those authoritative sources.

## Platform signoff — open

Run `beta-platform-manual-protocol.md` on Windows, macOS, and Ubuntu using the clean installed artifact.
Record browser, keyboard, display-scaling, responsive-layout, archive, restart, relocation, malformed-
file recovery, long-note, and alternate-theme results. A local Linux/browser probe does not satisfy
this gate for the other platforms.

## Post-reference-defragmentation beta maintenance — triaged locally

The completed thirteen-adventure corpus has been reconciled back into the beta maintenance queue. No open
persisted-data, archive, import/export, journal, graph, or identity defect is recorded. Two bounded
maintenance corrections were accepted: the Help page now displays the installed version with
privacy-conscious beta-feedback guidance, and `make clean` now uses a tested portable cleanup script that
removes nested editable-install metadata before source packaging. The source-snapshot builder also excludes
parallel `.coverage.*` data directly, so source safety does not depend on cleanup order.

The remaining queue is deliberately narrow: connected quality and live-browser gates, native artifact and
manifest evidence, the real-platform manual protocol, and defects demonstrated by those gates or actual beta
use. Conditional backend pressure points remain inactive; the internal adventure corpus is closed except for
fresh play evidence; and campaign implementation remains deferred pending representative fixtures and
adventure-only beta findings. See `post-reference-defragmentation-beta-maintenance-triage.md`.

## Previous code-candidate review — superseded by sample-scope revision

The final local once-over froze direct project-directory launch, archive path classification,
runtime-only wheel contents, and the wheel-size ceiling. No additional breaking change was found worth
imposing before testers create real workspaces. Any later breaking proposal must identify a concrete
correctness, safety, or migration failure rather than an aesthetic preference.


## Adventure reference library — accepted for beta, headless lifecycle complete, corpus-audited, and locally cold-read

Adventure Graph preserves encounters as playable clue-bearing units and now has a separate portable
authored domain and persisted library for recurring people, places, organizations, objects, and other
cross-encounter material. Encounters own contextual reference links; the current schema, canonical
writer, validation, archives, project revisions, application commands, CLI recovery workflows, and
browser Author interface now preserve and exercise the complete authored lifecycle.

This feature is part of the intended first beta, not a post-beta enhancement. Representative fixtures
settled the schema and association representation. The Author workspace provides the unified library,
kind filtering, stable-identity editing, encounter-local linking, derived backlinks, alias-aware search,
and dependency-aware removal. Play now provides linked and globally searchable read-only references,
an independent full-reference panel, and bounded typed encounter/reference pins without journal events.
Generated packets provide a grouped reference index, stable UUID-named sheets, backlinks, and contextual
encounter links. The subsequent reference-defragmentation workstream is complete across all thirteen
authoritative example adventures, yielding 224 canonical records and 1,305 ordered encounter-local links
without changing their clue graphs or demonstrated journals. Its final corpus naming pass accepted four
title-only deconflictions, preserved every stable encounter ID, and closed with no unresolved candidate. The
whole-application and focused Play-panel local GM cold-reads remain accepted engineering evidence, and the
tablet-width Author correction remains protected. The first version will not replace encounters with universal nodes, derive
graph edges from references, add
automatic entity merging, or introduce reference-targeted runtime events merely because authored
references exist. See `adventure-reference-library-roadmap.md` for scope, exclusions, fixtures, and
sequencing.

The broader source corpus may continue evolving independently. Release qualification must be rebuilt
only when the application code or packaged *Glass Saint* template changes. Native Linux, Windows, and
macOS artifacts plus real-platform launcher protocols remain open release evidence for every platform
actually claimed.

## Tester-facing UI cleanup and onboarding — locally complete

Local status: the cold-read is complete; frozen platform checks remain open.

Completed work:

- removed internal-development prose, implementation-facing save language, and keyboard notation from
  primary action labels;
- clarified split-party labels and distinguished note-only, outcome-only, and transition recording;
- renamed and demoted the older all-at-once workflow as the Recovery console;
- separated global top-bar destinations from Table-local Play navigation;
- added return-safe off-script encounter and clue creation during Play through the existing authoring commands,
  with regressions proving the active journal remains byte-for-byte unchanged;
- repaired long-note overlap and compact-width height expansion in both appearance themes; and
- added a global Help/Introduction page that explains encounters, clues, revelations, Author and Play
  workflows, credits Justin Alexander's practical influence, links to the Node-Based Scenario Design
  sequence and *So You Want to Be a Game Master*, and states clearly that Adventure Graph is
  unaffiliated; and
- completed the whole-application local GM cold-read across fresh and populated projects, both themes,
  desktop, tablet, and compact widths, reference-light controls, recovery paths, and the installed wheel;
  the only accepted finding hid a redundant current-project title block that overflowed at tablet width;
- completed the focused Play-panel convergence cold-read with reference-light *When the Swine Kneel* and
  reference-rich *The Concord of Aurelune*, confirming the six-box center, scroll boundaries, rail order,
  and authored-versus-Play language without another product correction.

Remaining work:

- repeat the checked-in manual protocol through frozen launchers on real Linux, Windows, and macOS
  desktops and resolve only objective platform-specific findings.

Exit condition: a new GM can explain every ordinary control, improvise authored material without losing
table context, find concise conceptual guidance from either mode, and encounter no duplicate primary
navigation, internal-development prose, or overlapping notes.

## One-click desktop distribution — pipeline implemented, platform signoff open

This is a distribution task, not a second product. The implementation reuses the existing loopback WSGI
application, local workspace format, application commands, browser assets, and validation behavior.

Completed pipeline contracts:

- a small native launcher chooses or remembers one workspace through the operating system directory
  chooser;
- one owned server binds to `127.0.0.1` on an operating-system-selected available port;
- **Open in browser** reuses that server, workspace replacement stops the former server, and closing the
  launcher releases the owned socket;
- launcher settings live in the user's platform configuration area while projects remain ordinary
  user-owned directories outside the bundle;
- a checked-in PyInstaller one-folder specification builds separate native artifacts rather than one
  oversized universal bundle;
- an exact checked-in build dependency lock is installed directly, verified before freezing, and recorded
  with the native runner provenance in each artifact manifest;
- the build script rejects canonical user-data payloads, runs the frozen executable against a temporary
  empty workspace, confirms smoke mode writes no launcher settings, creates a normalized archive and
  SHA-256 manifest, and enforces the compressed size ceiling;
- a native GitHub Actions matrix builds Linux, Windows, and macOS artifacts; and
- an aggregate evidence job downloads all three uploaded sets and verifies archive integrity, internal
  inventory, source revision, exact build inputs, native runner provenance, safe paths, required
  executables, and platform completeness.

Packaging constraints remain:

- do not introduce Electron or bundle a general-purpose Chromium runtime;
- target a compressed artifact below 100 MiB per platform;
- approaching 1 GiB is a failed packaging design for this product; and
- testers are not expected to work through the command line, although the wheel and CLI remain recovery
  and developer surfaces.

Open release evidence:

- run and retain successful native hosted builds for all three operating systems;
- execute the manual launcher and browser protocol on Windows, macOS, and Ubuntu;
- decide and implement Windows signing and macOS signing/notarization before any public release claim;
- build all artifacts from the accepted source revision and repeat frozen smoke and manual checks.

See `desktop-distribution.md` for the build and user-data contract.

## Post-beta campaign graph initiative — documented, implementation deferred

Adventure Graph is intended eventually to support clue-driven campaign design at a second scale:
campaign entries containing portable adventures serve as the playable nodes; campaign clues are
organized by the adventure or explicit campaign source where they can be learned and may be placed at
specific encounters without becoming encounter clues; campaign revelations collect their support and
may expose or unlock other adventures. The campaign will also need persistent campaign-owned entities
that bind explicitly to adventure-local references, plus an absolute chronology that indexes encounter
occurrences and external events and derives backlinks to those entities. Projected connections
between adventures must remain traceable to authored clues and revelations rather than becoming
unexplained arrows.

This initiative is deliberately not part of the 0.10.0 beta. The first adventure-only beta should
inform the campaign model and interface before implementation begins. Existing adventure schemas and
workspaces remain unchanged. The recorded identity, copy-import, clean-export, companion-metadata,
runtime-layering, validation, and phased implementation decisions live in
`campaign-graph-roadmap.md`.
