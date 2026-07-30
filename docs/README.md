# Documentation index

This index is the navigation owner for Adventure Graph documentation. The root `README.md` is the product
entry point; this file separates current operating guidance, durable contracts, maintainer procedures, active
plans, and historical evidence.

## Start here

- [Beta guide](beta-guide.md) — installation, workspace layout, upgrade boundary, and feedback.
- [Local web interface](ui-usage.md) — Author, Play, reports, archives, recovery, and interface security.
- [Command-line reference](cli-reference.md) — complete stable command map and CLI workflows.
- [Maintainer guide](maintainer-guide.md) — quality gates, source snapshots, and native desktop packaging.

## Durable product and data contracts

- [Architecture](architecture.md) — domain model, dependency direction, graph semantics, and generated views.
- [File format](file-format.md) — authored and runtime JSON schemas and compatibility rules.
- [Authoring lifecycle](authoring-lifecycle.md) — stable identity, revisions, edits, moves, removals, and journal
  safety.
- [Runtime state](runtime-state.md) — append-only events, operations, projections, and correction semantics.
- [Play mode semantics](play-mode-semantics.md) — sessions, visits, lead outcomes, revelations, transitions,
  notes, dice, and recovery behavior.
- [Journal archives](journal-archives.md) — archive creation, compatibility, restoration, and deletion.
- [Necessary and optional structure](necessity-model.md) — necessity, reachability, and connectivity.
- [Validation diagnostics](validation-diagnostics.md) — redundancy, graph cuts, warnings, and repair candidates.

## Interface and implementation architecture

- [User-interface architecture](ui-architecture.md) — adapter boundaries, browser-local state, composition, and
  route-family ownership.
- [Backend maintenance map](backend-maintenance-map.md) — authoritative seams, pressure points, and conditional
  extraction triggers.
- [Engineering standards](standards.md) — repository, testing, documentation, release, and compatibility
  discipline.
- [Test strategy](test-strategy.md) — durable test tiers and evidence policy.
- [Test audit](test-audit.md) — 2026-07-30 selector, coverage, validation, and performance review.
- [Comment audit](comment-audit.md) — source-comment, docstring, suppression, and stylesheet-label review.
- [Portable source snapshots](source-snapshots.md) — deterministic source-package construction and verification.
- [Desktop distribution](desktop-distribution.md) — launcher lifecycle and native artifact contract.
- [Desktop interaction protocol](beta-platform-manual-protocol.md) — real-platform manual qualification.

## Current maintenance and future product work

- [Post-reference beta maintenance triage](post-reference-defragmentation-beta-maintenance-triage.md) — current
  compatibility-aware maintenance priorities.
- [Campaign graph roadmap](campaign-graph-roadmap.md) — accepted post-beta campaign direction and sequencing.
- [Graph-scale design notebook](graph-scale-design-notebook.md) — provisional campaign questions that are not
  yet product contracts.
- [Publication and commercialization strategy](publication-strategy.md) — long-range distribution, provenance,
  licensing, and discovery considerations.

## Accepted design and corpus records

These records are retained because they define accepted scope, fixtures, editorial invariants, or evidence
that remains useful when maintaining the bundled corpus. They are not active implementation queues.

- [Adventure reference-library roadmap](adventure-reference-library-roadmap.md)
- [Reference-library phase 1 design](adventure-reference-library-phase-1-design.md)
- [Reference-library phase 6 corpus audit](adventure-reference-library-phase-6-corpus-audit.md)
- [Reference-library phase 7 cold-read](adventure-reference-library-phase-7-cold-read.md)
- [Adventure reference-defragmentation record](adventure-reference-defragmentation-roadmap.md)
- [Adventure corpus quality record](adventure-second-look-roadmap.md)
- [Final corpus differentiation audit](final-corpus-differentiation-audit.md)
- [Final encounter-name ledger](example-encounter-name-ledger.md)
- [Play-interface panel cold-read](play-interface-panel-cold-read.md)

Machine-readable companions:

- [`adventure-reference-library-phase-1-fixtures.json`](adventure-reference-library-phase-1-fixtures.json)
- [`example-encounter-name-dispositions.json`](example-encounter-name-dispositions.json)
- [`intentional-shared-encounter-titles.json`](intentional-shared-encounter-titles.json)
- [`test-hardening-mutation-report.json`](test-hardening-mutation-report.json)

## Historical release and workstream evidence

These documents are frozen records. They may explain why a contract exists, but they do not establish the
current revision's qualification status.

- [Beta-readiness roadmap](beta-readiness-roadmap.md)
- [Private-beta breaking-change audit](private-beta-breaking-change-audit.md)
- [Private-beta release hardening roadmap](private-beta-release-hardening-roadmap.md)
- [Private-beta release qualification](private-beta-release-qualification.md)
- [Source-snapshot portability roadmap](source-snapshot-portability-roadmap.md)
- [Corpus differentiation workstream 1](corpus-differentiation-workstream-01.md)
- [Corpus differentiation workstream 2](corpus-differentiation-workstream-02.md)
- [Corpus differentiation workstream 3](corpus-differentiation-workstream-03.md)
- [Corpus differentiation workstream 4](corpus-differentiation-workstream-04.md)
- [Corpus differentiation workstream 5](corpus-differentiation-workstream-05.md)
- [Corpus differentiation workstream 6](corpus-differentiation-workstream-06.md)

## Documentation discipline

- Put tester-facing instructions in the beta or interface guides.
- Put command syntax in the command-line reference.
- Put source-build and release procedures in the maintainer guide or their specialist contract document.
- Put durable architecture and compatibility rules in the contract documents above.
- Keep revision-specific handoffs outside the packaged repository after their durable outcomes are
  consolidated.
- Do not duplicate volatile test totals or qualification claims across durable documents.
