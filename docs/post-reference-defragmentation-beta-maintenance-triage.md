# Post-reference-defragmentation beta maintenance triage I

## Decision

The thirteen-adventure reference-defragmentation workstream is closed. Adventure Graph remains an
adventure-only private beta with one tester-facing packaged sample, *The Glass Saint*. The next source
work must be driven by a demonstrated beta defect, data-integrity risk, or release-evidence failure rather
than by another broad editorial or refactoring cycle.

This triage found no open persisted-data, graph, archive, import/export, or journal defect. It accepted three
bounded maintenance corrections:

1. `make clean` now delegates to a tested Python cleanup script that removes generated metadata at any
   repository depth, including `src/adventure_graph.egg-info`. That directory survived the former
   root-only `*.egg-info` pattern during the final corpus packaging run.
2. The application-wide Help page now displays the installed Adventure Graph version and concise
   privacy-conscious feedback guidance. Desktop and browser-first testers no longer need a terminal command
   merely to identify the build they are reporting.
3. Portable source snapshots now exclude parallel coverage data named `.coverage.*` as well as the ordinary
   `.coverage` file. Snapshot safety no longer depends on a cleanup command having run immediately before the
   audit or build.

Neither correction changes an authored schema, journal schema, workspace format, stable identity, archive,
import/export payload, or campaign model.

## Frozen compatibility boundary

The maintenance baseline remains:

- adventure schema 3;
- play-state schema 6;
- workspace-settings schema 1;
- stable opaque adventure, encounter, revelation, clue, and reference identities;
- non-destructive archives and revision-aware mutations;
- one packaged tester-facing sample adventure;
- thirteen internal development adventures with 138 encounters, 224 references, and 1,305 ordered
  encounter-reference links; and
- no campaign aggregate, campaign schema, or campaign runtime.

Any proposal that changes a schema, journal event, archive identity, workspace discovery rule, import/export
contract, or stable entity identity requires a separate compatibility review and a migration strategy before
implementation.

## Remaining-work inventory

### 1. External release evidence — highest release priority, not speculative source work

The connected formatter, lint, strict type, property, dependency, import-boundary, dead-code, complexity,
docstring, static-security, and dependency-audit gates remain unverified in this restricted environment.
The six live-server browser cases remain blocked at loopback navigation before application code loads.
Native Linux, Windows, and macOS artifacts, adjacent manifests, aggregate artifact verification, and the
real-platform manual protocol also remain external evidence.

Disposition: run these gates against one frozen source revision. Change source only for a reproducible
failure, then invalidate and rebuild the affected evidence.

### 2. Concrete correctness and data integrity — interrupt immediately when demonstrated

No open defect is presently recorded. The cleanup-depth defect found during final packaging is corrected in
this tranche. Future failures involving writes, recovery, archives, imports, exports, schema decoding,
identity routing, or journal projection outrank all aesthetic and campaign work.

Disposition: keep this queue empty unless a test, platform run, or beta report supplies exact reproduction
evidence. Every accepted defect receives a focused regression at its owning layer.

### 3. Conditional technical debt — triggers have not occurred

The pressure points in `backend-maintenance-map.md` remain conditional. No additional composite read,
validator-policy dimension, Recovery-console action, authored entity family, second adapter, or play-event
kind has appeared. Profiling has not shown material projection cost.

Disposition: do not split modules for line count. Revisit a pressure point only when its recorded trigger
occurs and the change deletes duplication or reduces coupling without changing public or persisted
contracts.

### 4. Tester-facing UI polish — evidence-driven only

The whole-application cold-read and focused Play-panel cold-read remain accepted local evidence. This tranche
adds build identification and feedback guidance to Help. Further UI changes should come from the real-platform
manual protocol or an observed tester workflow, especially keyboard, scaling, responsive layout, chooser,
archive, restart, relocation, and malformed-file recovery findings.

Disposition: do not start another general polish pass. Resolve objective platform or tester findings in
small, reversible slices.

### 5. Adventure-content maintenance — closed except for fresh play evidence

The internal corpus is a completed research and regression asset, not the tester-facing catalog. No further
corpus-wide extraction, voice, coherence, or naming workstream is scheduled.

Disposition: revise an adventure only after fresh play, a newly demonstrated content defect, or a separately
scoped publication requirement. Rebuild only the affected packet and preserve historical journals and audits.

### 6. Campaign-mode research and design — deferred

The campaign initiative remains in Phase 0. Its identity, copy-import, clean-export, explicit binding, and
absolute chronology constraints are useful design inputs, but the open source-reference, effect, update,
export, validation-profile, and repeated-run questions still need representative fixtures and beta evidence.

Disposition: do not add a campaign schema or runtime. The next campaign step is fixture-backed model review,
not implementation.

## Prioritized maintenance queue

1. Freeze this source revision and run the connected quality and live-browser gates.
2. Build and verify native artifacts for every claimed platform, then execute the checked-in manual protocol.
3. Triage real beta reports, prioritizing data integrity, recovery, and blocked ordinary workflows.
4. Activate a conditional technical-debt item only when its documented trigger occurs.
5. Begin campaign fixture design only after adventure-only beta evidence is available and the bounded model is
   explicitly accepted.

## Exit condition and next checkpoint

This triage is complete when the two accepted corrections pass the deterministic, schema, syntax, package,
installed-lifecycle, and portable-source gates and the current qualification record is refreshed against the
same final tree.

The exact next checkpoint is **Connected beta qualification and native platform evidence I**. If that work
reveals no source defect, it should produce evidence rather than another code tranche.
