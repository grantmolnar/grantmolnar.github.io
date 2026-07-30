# Adventure reference library Phase 7 cold-read and local convergence record

## Status

The whole-application local GM cold-read is complete for the accepted Adventure Graph 0.10.0 source.
The reference library is now part of the locally accepted beta source. Source, wheel, CLI, loopback
browser, archive, relocation, and installed-lifecycle evidence are green.

Native platform signoff remains separate evidence. This execution environment could not install the
exact checked-in PyInstaller build lock, so it did not produce or represent Linux, Windows, or macOS
native artifacts. The lock was not relaxed and no substitute artifact was accepted.

## Scope and environment

The cold-read began from the Phase 6 corpus-audited repository and preserved the accepted reference
schema, journal boundary, campaign exclusions, and packaging architecture. It exercised a fresh
workspace and the four-adventure corpus through the existing application and browser surfaces.

Real-browser checks used Chromium 144.0.7559.96 on Linux at desktop, tablet, and compact dimensions,
including 1440×1000, 1280×900, 1024×900, and 390×844. Both appearance themes, keyboard-operated
drawers, browser-local pins, reload, and focused-encounter changes were included. The managed browser
policy that normally blocks navigation in this execution environment was relaxed only for each bounded
local test process and restored immediately afterward.

## Fresh-project evidence

The browser cold-read created a nearly blank adventure, added its first encounter, and used contextual
create-and-link to create a recurring person. Editing the title and aliases preserved the reference's
stable UUID. The complete multi-encounter link, backlink, dependency-preview, publication, relocation,
and removal paths are also exercised by the real-filesystem and installed-wheel integration suites.

Reference-light behavior remained inexpensive: a project with no records presents a small explicit
empty state rather than placeholder dossiers or mandatory taxonomy.

## Existing-corpus evidence

- In *The Concord of Aurelune*, Theron Eiral and The Sunseed appear beside the Argent Canopy in
  encounter-authored order with distinct local context. Each full dossier opens independently without
  changing encounter focus.
- In *The Bell Beneath Harrowgate*, The Salt Wardens can be found globally, pinned as a typed reference,
  retained across reload, and carried across changes to the focused encounter.
- *The Cauldron of Nine Silences* remains usefully ledger-centered and reference-light.
- *When the Swine Kneel* retains a compact explicit reference-light Play state.

Read-only browser activity left every companion journal byte-for-byte unchanged. The observed SHA-256
values before and after the cold-read were:

- Aurelune: `1a141cfc7892ba3e9b27c85fb6d2b5c668e2794236bea02e1587ea1c41e04d69`;
- Harrowgate: `187974c802556349f744bfd695647e5c7522851ba7a4b451485b730a90513444`;
- the Cauldron: `f84bdc2560681cf7483db11b69cdc36fc4cb89826a40f969a41df4e6f5419f8e`; and
- *When the Swine Kneel*: `7585f7810216d1afa284527ef56fd697fea71bd2507be0a90c45705b6ce649b8`.

## Responsive and interaction finding

### F-01 — Author top-bar overflow at tablet width — resolved

At 1024 pixels wide, the current-adventure title block could extend the Author top bar beyond the
viewport. The title duplicated context already available in the page heading and navigation. The
accepted correction hides that secondary block at widths up to 1180 pixels while retaining the primary
brand, destinations, and theme control.

A browser contract now protects the responsive rule. A final real-browser rerun confirmed:

- no horizontal overflow in the Author interface at 1024×900;
- the redundant project block is hidden at that width;
- no horizontal overflow in Play at 390×844; and
- no JavaScript page errors in the bounded rerun.

No other objective UI defect survived the cold-read. Compact route and utility drawers opened and
closed through their controls, Escape, and the scrim; dark appearance persisted through reload; and a
Play search field treated the `p` key as text rather than invoking the pin shortcut.

## Safety and recovery evidence

The bounded application and integration suites cover stale-revision HTTP 409 behavior, duplicate and
dangling link refusal, dependency previews, cancellation, explicit cascade, malformed companion
journals, authored inspection during journal failure, project relocation, clean standalone export,
generated packet publication, archive creation and restoration, and immutable archive snapshots.

Focused Phase 7 execution passed 98 reference, browser, workspace, CLI, archive, and corpus tests. The
clean installed-wheel audit then exercised:

- offline installation into a new virtual environment and `pip check`;
- both CLI entry points and the installed desktop-launcher entry point;
- Unicode and spaced paths;
- fresh identity and authoring;
- repeated browser launch and direct project-directory launch;
- multi-session play, correction, and recorded browser dice;
- malformed-file repair;
- archive create, restore, and delete;
- workspace copy, rename, relocation, and reopen; and
- launcher smoke mode without persisted launcher settings.

## Packaging evidence and boundary

The final source wheel is 324,761 bytes with SHA-256
`b9182bd61220469376e520315c69a859f1f729a0b55210066c755d8b556ca404`. It remains below the 2 MiB
wheel ceiling and contains the required runtime assets without source tests, documentation, schemas,
examples, or generated caches. The clean installed lifecycle is accepted local release evidence.

The native build script and manifest verifier remain unchanged. A native build requires the exact
versions in `packaging/desktop-build-requirements.txt`. The configured package mirror did not provide
that complete lock, including PyInstaller 6.21.0, and direct external archive retrieval is unavailable
in this execution environment. Therefore:

- no native bundle was built locally;
- no artifact manifest was fabricated;
- no Linux launcher GUI or operating-system directory chooser was manually exercised;
- no Windows or macOS artifact was produced; and
- no Windows, macOS, or Ubuntu manual-platform protocol was claimed.

The next evidence tranche must build on native runners from one accepted source revision, verify the
complete three-platform artifact set, and execute the checked-in manual protocol on real systems.

## Verification baseline

Fresh bounded verification against the frozen Phase 7 source completed with:

- unit: 616 passed, 1 optional Hypothesis property test skipped because Hypothesis is not installed;
- architecture, metadata, and tooling contracts: 92 passed;
- integration: 339 passed; and
- smoke: 47 passed.

Total: **1,094 passed, 1 optional skip**. Each bounded suite exited cleanly.

Additional successful checks:

- 39 JSON documents validated against the published schemas;
- Python source, tests, scripts, and packaging modules compiled;
- JavaScript syntax validation passed for the packaged browser asset;
- 109 local Markdown links resolved across 508 Markdown files;
- the focused reference, browser, workspace, CLI, archive, and corpus set passed 98 tests;
- the final 1024-pixel Author and 390-pixel Play real-browser rerun reported no horizontal overflow or
  page error; and
- the clean wheel installed offline into a new environment and completed the documented installed
  lifecycle with `pip check`.

Ruff, Pyright, Import Linter, Bandit, Deptry, Vulture, and the other optional static executables are not
installed in this execution environment, so they remain explicitly unavailable rather than passing
gates. The repository's architecture and metadata contracts still enforce import ownership, added-line
length, tooling configuration, package payload, and documentation invariants. The shared host
environment's `pip check` still reports its pre-existing MoviePy/Pillow version conflict; the isolated
wheel environment passed `pip check`, and Adventure Graph depends on neither package.
