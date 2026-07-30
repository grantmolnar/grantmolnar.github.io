# Private-beta release hardening roadmap

## Purpose

This workstream prepares the first externally shared Adventure Graph desktop build. It is the final
window for justified breaking changes before tester-created workspaces become compatibility inputs.
The objective is not to freeze defects quickly. It is to remove avoidable release risk while preserving
clear domain, application, adapter, and interface boundaries.

## Operating rules

- Correctness, data integrity, recovery, security, and comprehensible user workflows take precedence
  over preserving pre-beta behavior.
- Persisted-format changes require an explicit schema and migration decision rather than an incidental
  writer change.
- Browser features must invoke existing application commands and queries or add transport-neutral
  application services; the web layer must not reproduce persistence or validation rules.
- A release candidate is not accepted from unit tests alone. It must pass the deterministic suite,
  source and wheel checks, a clean installed smoke, and the checked-in manual desktop protocol.
- Work may span as many sessions as the design, implementation, and validation require.

## Session sequence

### 1. Baseline and catalog correction — complete

- Reconcile the reported browser behavior with the uploaded portable-transfer source.
- Confirm which adventure and playthrough transfer workflows already exist.
- Repair the adventure-filter layout at the actual bounded content width rather than the viewport width.
- Make each adventure card a direct entry point to that adventure's playthrough archive workspace.
- Add focused integration coverage for the catalog transfer affordances and selection redirect.

### 2. Workspace-level playthrough import — complete

- Add an application-level use case that resolves an uploaded portable playthrough to its adventure by
  stable adventure identity.
- Reject absent or ambiguous matches without changing the selected adventure or active journal.
- Expose the use case from the Adventures catalog so a user need not open the correct adventure first.
- Preserve the existing project-level revision, archive-collision, schema, size, and path-safety checks.

### 3. Transfer information architecture and error recovery — complete

- Cold-read adventure import, adventure export, active-playthrough export, archived-playthrough export,
  and playthrough import as one coherent workflow.
- Remove duplicate or misleading controls and ensure empty-journal states explain unavailable exports
  without presenting dead actions.
- Verify stale revisions, malformed uploads, identity mismatches, duplicates, and oversize documents
  produce bounded actionable responses without exposing local paths.

### 4. Breaking-change and technical-debt audit — complete

- Revisit schema, persistence, workspace identity, archive identity, and desktop configuration for any
  concrete pre-beta migration hazards.
- Audit large or multi-responsibility release-path modules and make only decompositions that reduce
  near-term defect risk.
- Review comments, README, beta guide, transfer documentation, and packaging instructions against the
  implemented interface.
- Record lower-priority line-level cleanup separately rather than mixing it into release-critical work.

### 5. Persistent-reference play notes — complete

- Add one explicit append-only event associated with a stable authored reference rather than mutating
  reusable adventure prose or inventing a generic annotation subsystem.
- Reuse the existing journal, optimistic revision, projection, correction, chronological ledger, and
  generated-summary machinery.
- Expose note history and composition from the selected-reference Play panel, preserve rejected form
  values, and keep selection and pinning non-canonical.
- Block authored reference removal when active or archived play history names that identity.
- Advance the pre-beta play-state schema atomically and document the compatibility boundary.

### 6. Full qualification and packaging evidence — local evidence complete; external gates open

- Run formatting, lint, strict type checking, schemas, deterministic tests, property tests, coverage,
  architecture checks, dependency checks, static security checks, package build, installed beta smoke,
  and source snapshot verification.
- Build the native artifact on the available platform and run the checked-in manual protocol.
- Record any unavailable platform evidence explicitly; do not infer Windows or macOS behavior from a
  Linux build.
- Produce the final source snapshot only after all accepted corrections are included.

### 7. Tester-facing sample scope — locally complete; external gates open

- Package only *The Glass Saint* as tester-facing sample content; retain the other adventures solely as
  source-development corpus and test fixtures.
- Expose the packaged sample from an empty Adventures catalog and the New Adventure page without silently
  writing to a selected workspace.
- Reuse one transport-neutral template-instantiation use case for CLI and browser creation, assigning fresh
  adventure identity and an empty matching playthrough each time.
- Add packaging, application, filesystem, browser, and responsive-layout regressions proving the sample is
  available and no other adventure resource can enter runtime artifacts.
- Update beta guidance so unfinished development adventures are not represented as polished release
  content or as a blocker for application signoff.

### 8. Post-reference-defragmentation maintenance triage — complete

- Reconcile release evidence, correctness maintenance, conditional technical debt, tester-facing UI,
  internal adventure content, and campaign research into one compatibility-aware queue.
- Correct the repository cleanup path so nested editable-install metadata cannot survive into a source
  handoff.
- Exclude parallel `.coverage.*` data from portable snapshots even when a maintainer audits or builds before
  cleaning the tree.
- Make the installed application version available from browser Help so desktop-first beta reports do not
  require a terminal command.
- Refresh local qualification evidence against the final source tree while leaving connected, native, and
  real-platform gates explicitly open.


## Current state

Sessions 1 through 5 are implementation-complete in this working tree. The Adventures catalog exposes
canonical adventure import/export, direct per-adventure archive access, and workspace-level playthrough
import. Transfer forms distinguish identity-routed catalog import from selected-adventure import, present
one primary action, state the 8 MiB ceiling, and remain bounded at compact widths. Empty journals explain
unavailable actions, and transfer failures return bounded, actionable responses without local paths. The
breaking-change audit made the documented JSON byte ceiling symmetric across reads, writes, downloads,
and transaction recovery; bounded archive identifiers to 80 portable characters; rejected case-only
archive collisions; and bounded browser adventure download names. It retained existing payload shapes,
identity rules, transaction formats, desktop settings, and release-path module boundaries.

The persistent-reference note slice is complete across the domain event, schema-6 persistence, projection,
revision-aware application and CLI commands, selected-reference Play form, chronological Journal and GM
narrative surfaces, generated summary, player-recap exclusion, correction behavior, reference-removal
guard, responsive browser contract, and clean-wheel smoke path.

Session 7 narrowed the tester-facing content boundary to *The Glass Saint*, added explicit browser sample
creation through the same fresh-template semantics as CLI initialization, and enforced a one-resource
runtime package. Session 8 then reconciled the completed internal corpus back into beta maintenance,
corrected nested build-metadata cleanup, and exposed the installed version from Help for reproducible
desktop-first feedback. The current local qualification evidence is recorded in
`private-beta-release-qualification.md`; connected, native, and real-platform gates remain separate.

The restricted environment could not supply the strict static-analysis, property, dependency, security,
or exact PyInstaller toolchains, and its browser policy blocks live Playwright navigation to loopback.
Those gates, native artifact construction, manifest verification, and the real-platform manual protocol
remain open and must pass against this exact source revision before tester handoff. The evidence and exact
builder sequence are recorded in `private-beta-release-qualification.md`.
