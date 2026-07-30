# Test audit

## Scope

This audit reviewed the test suite as release evidence rather than treating a passing total as sufficient.
It covered selector behavior, marker discipline, behavioral ownership, high-risk persistence validation,
coverage policy, browser and property boundaries, mutation evidence, fixture realism, corpus-test cost, and
aggregate execution.

The audit baseline was the `adventure-graph-0.10.0-beta-documentation-cleanup-i` source archive. The changes
below are compatibility-neutral: they alter test infrastructure, tests, one unreachable defensive branch,
and documentation, but no persisted format, command, route, identifier, or supported runtime behavior.

## Existing strengths

The suite already had a strong shape before this audit:

- domain, application, infrastructure, interface, browser, corpus, architecture, smoke, and packaging
  responsibilities are separated clearly;
- repaired defects generally have focused tests at the layer that owns the rule;
- browser tests protect real JavaScript behavior that survived static and server-rendering tests;
- property tests cover graph cuts, canonical persistence, dice, projection, and correction;
- crash-recoverable transactions have process-termination and mutation evidence;
- corpus tests distinguish structural contracts, semantic contracts, exact phrase locks, and generated
  artifacts; and
- the installed-wheel lifecycle exercises the actual beta path rather than only the source checkout.

The audit did not find a reason to replace these tests with broader snapshots or a new test framework.

## Findings and repairs

### Empty advertised tiers

The `external`, `slow`, and `integration` custom markers were registered without any marked tests. The first
two also had Make targets that always failed with pytest exit code 5 because they selected nothing.

The empty targets and unused markers were removed. Integration remains a directory-owned layer through
`tests/integration` and `make test-integration`; it does not need a second marker vocabulary. A static contract
now requires every registered custom marker to be exercised by at least one test.

### Selector isolation

Marker-selected non-browser commands previously collected browser modules and optional property modules
before deselecting them. This made ordinary deterministic commands import Playwright and report Hypothesis
skips even though neither suite was requested.

The Makefile now ignores `tests/browser` and feature-local property modules by path for non-browser aggregate
commands. `make test-browser` and `make test-property` remain explicit fail-closed gates.

### Coverage floor

The branch-aware coverage gate allowed the suite to fall to 80 percent even though the maintained baseline
is approximately 92 percent. That margin was too large to protect against accidental deletion of meaningful
tests.

The configured floor is now 90 percent. This still leaves room for platform-specific desktop UI code and
intentional defensive branches while preventing a substantial unnoticed regression.

### Play-journal validation ownership

Append-only journal validation is a customer-data boundary, but many malformed operation groups and active
state transitions were covered only indirectly, if at all. Focused parameterized tests now protect:

- contiguous positive operation numbers;
- correction isolation, target availability, and nonblank reasons;
- visit-operation grouping and visit identity;
- transition phase ordering, source-visit consistency, unlock pairing, and terminal destination placement;
- explicit-session numbering, nesting, dates, participants, ends, and between-session content;
- missed and spotted lead state;
- revelation establishment, foreclosure, and reopening state;
- duplicate encounter unlocks; and
- blank or orphaned visit, reference, and consequence notes.

The focused module now reaches roughly 91 percent branch-aware coverage by itself. One duplicate-destination
branch was removed after the audit proved it unreachable: the earlier destination necessarily triggers the
stronger rule that a transition must end with its destination visit.

### Corpus-test cost

The character-name collision contract rescanned approximately 2.8 MB of corpus text once for every candidate
name. Its principal test took about 12 seconds despite performing a deterministic set-membership check.

The test now compiles one bounded alternation and scans each adventure once. The same contract completes in
well under one second, and the demonstration-name leakage check uses the same exact matching primitive.

### Aggregate execution

An apparent aggregate-run hang was investigated because partitioned green results are not a substitute for a
working advertised command. A detached invocation of `make test` completed all 1,338 deterministic tests in
36.61 seconds with exit status 0. The prior symptom was attributable to the execution harness's streamed-output
capture, not repository test order or leaked processes. No product workaround was added.

## Residual evidence boundaries

- Property tests remain fail-closed but require Hypothesis to be installed. They were inspected but could not
  be executed in the audit environment.
- Real-loopback browser tests require a usable Chromium and an environment that permits local HTTP. A blocked
  loopback environment is unavailable evidence, not a passing result.
- Native Tk behavior, operating-system integration, trust prompts, signing, and notarization remain native
  manual or platform evidence.
- The mutation report is a bounded high-risk campaign, not an exhaustive mutation score for the repository.
- Low coverage in graphical desktop code is acceptable only because headless lifecycle tests and a detailed
  native protocol own different parts of that evidence boundary.

## Disposition

The suite is suitable for beta maintenance after these repairs. Further test work should be driven by an
observed defect, a new compatibility-bearing feature, or a demonstrated survivor—not by test-count growth.
The next release candidate still requires the connected property, browser, static-quality, dependency,
security, native-artifact, and manual-platform gates applicable to that exact revision.
