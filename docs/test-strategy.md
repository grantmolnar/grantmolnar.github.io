# Test strategy

## Purpose

Adventure Graph protects three different kinds of product evidence:

1. runtime behavior and persistence invariants;
2. development-corpus and generated-packet contracts; and
3. release behavior that can only be exercised in a browser or on a native desktop.

The test tiers separate those costs without creating weaker definitions of correctness. A release candidate
must satisfy every applicable tier.

## Local test tiers

- `make test-fast` runs deterministic runtime tests without the source development corpus, browser, or
  property suites.
- `make test` runs the complete deterministic Python suite, including corpus contracts.
- `make test-unit`, `make test-integration`, `make test-smoke`, and `make test-architecture` isolate the
  corresponding layer when diagnosing a failure.
- `make test-corpus` runs source development-corpus synchronization and editorial contracts.
- `make test-browser` starts the real loopback application and drives Chromium through Playwright.
- `make test-property` runs feature-local Hypothesis tests and fails immediately when Hypothesis is absent.
- `make coverage` runs the deterministic suite with branch coverage and a 90% minimum threshold.
- `make validate` combines metadata, formatting, type checking, schema validation, property evidence,
  coverage, dependency checks, and architecture checks.

Browser and property tests are not silently skipped when their tools are unavailable. Non-browser targets
omit browser modules and property modules by path so marker selection does not import optional test tooling,
while the release-oriented browser and property targets fail closed.

## Behavioral ownership

Tests should fail at the layer that owns the rule:

- domain tests protect identities, graph rules, value bounds, and immutable state transitions;
- application tests protect authoring transformations, journal projection, correction, and document
  generation;
- infrastructure tests protect canonical decoding, round trips, transaction recovery, size ceilings, and
  safe filesystem boundaries;
- interface tests protect transport parsing, refusal behavior, rendering contracts, and return context;
- browser tests protect visible JavaScript behavior that static HTML or source-string assertions cannot;
- package and smoke tests protect installed entry points, wheel contents, and the end-to-end beta path.

Every repaired defect receives a focused regression at its owning layer. Indirect corpus protection is useful
additional evidence, not a substitute for a precise boundary test.

## Browser evidence

`tests/browser/test_play_interface.py` executes the actual WSGI application in isolated temporary
workspaces. The current workflows protect:

- the six central Play disclosures and persisted browser-local preferences;
- notebook-draft recovery without canonical journal mutation;
- mobile drawer focus, inert state, Escape handling, and desktop-breakpoint cleanup;
- dice-tray ordering, local recents, notebook insertion, and journal neutrality; and
- Play-originated reference authoring through the ordinary revision-aware adventure path.

This gate was justified by a concrete mutant: reversing disclosure visibility survived 232 static and
server-level tests but failed immediately in Chromium because expanded sections were no longer visible.

## Corpus contracts

Bundled-adventure tests use four explicit contract types:

- **Structural contracts** protect headings, authored order, counts, identifiers, or topology without
  freezing unrelated prose.
- **Semantic contracts** protect durable ideas while permitting sentence-level voice revision.
- **Editorial phrase locks** preserve exact legal, ritual, procedural, or consciously frozen language.
- **Generated-artifact contracts** compare deterministic packet output exactly.

`tests/support/corpus_contracts.py` contains the shared structural, semantic, exact-lock, and retired-phrase
helpers. A raw substring assertion is appropriate only when the exact substring is itself the contract.

## Property evidence

Feature-local Hypothesis tests cover:

- exact graph cuts against brute-force calculation;
- canonical adventure and play-journal object and byte round trips;
- dice canonicalization, result validation, and maximum-roll arithmetic; and
- deterministic journal projection plus append-only correction of the latest active operation.

Property modules follow the `test_*_properties.py` naming convention and remain beside the feature layer they
exercise.

## Mutation evidence

The bounded hardening campaign reviewed 27 explicit mutations across graph logic, dice, Play projection,
canonical persistence, and crash-recoverable transactions. Fifteen were killed immediately. Nine meaningful
survivors received focused tests and are now killed. Three remaining survivors were classified as equivalent
or redundant. The machine-readable classifications are in
[`test-hardening-mutation-report.json`](test-hardening-mutation-report.json).

The campaign is evidence for selected high-risk seams, not a claim of exhaustive mutation enumeration.
`make mutation` remains available when the declared `mutmut` dependency is installed.

## Source-snapshot evidence boundary

Source handoffs have their own packaging contract. `scripts/source_snapshot.py` audits the repository path
budget, writes a deterministic ZIP beneath the stable `adventure-graph/` root, excludes local build and
environment state, and rejects unsafe, duplicate, case-colliding, encrypted, symbolic-link, or over-budget
members. `make source-package` verifies the archive it creates and is part of `make ci`.

Automated tests cover the live repository maximum, deterministic bytes, stable root, the declared
120-character extraction prefix, rejection of the former descriptive internal root, unsafe and
case-colliding members, and local-artifact exclusions. The ordinary Windows Explorer **Extract All**
acceptance run passed; Linux ZIP extraction remains supporting rather than substitutive evidence for that
native behavior.

## Desktop evidence boundary

Automated platform-independent tests cover settings, workspace validation, server ownership, browser
refusal, readiness retries, timeout diagnostics, cleanup, archive verification, and frozen headless smoke.
Native build automation covers the exact PyInstaller lock, one-folder construction, archive safety,
manifest inventory, size ceilings, expected executables, and shared source revision. Archive verification
resolves valid in-bundle symbolic-link chains such as the macOS Python framework while continuing to reject
absolute targets, root escape, cycles, and missing final members.

The Tk window and operating-system integration remain native-manual evidence. The checked-in desktop
protocol must exercise directory selection, default-browser opening, reopen, workspace switching, close
behavior, scaling, keyboard use, long notes, archives, restart, relocation, malformed files, and operating-
system trust prompts. Signing and notarization are separate release gates.

## Revision-specific evidence

This document defines the durable test tiers and evidence boundaries. It deliberately does not duplicate a
mutable total test count, corpus-case count, coverage percentage, or browser-case count. Those values change
whenever a focused regression is added, a corpus contract is refined, or collection is reorganized, and a
number copied here can become stale while every executable gate remains correct.

[`private-beta-release-qualification.md`](private-beta-release-qualification.md) is a frozen evidence record
for the exact source snapshot named there. Later maintenance handoffs record local addenda for their own
source archives. Neither record automatically qualifies a descendant revision: any source change invalidates
prior wheel, digest, browser, native-artifact, and manual evidence to the extent that the change can affect it.

Measure the tree being qualified by running the checked-in targets. Record the exact revision, environment,
partition results, coverage result, unavailable gates, artifact digests, and native evidence beside that
revision. Local environments that cannot provide Chromium, Hypothesis, connected quality tools, or native
desktop runners must report those checks as unavailable rather than infer their result from another tier.
