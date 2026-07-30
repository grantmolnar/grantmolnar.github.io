# Comment audit — 2026-07-30

This audit reviewed Python comments and docstrings, JavaScript comments, CSS section labels, and inline
static-analysis suppressions. It was performed after the test audit and the authoring-action workspace
extraction. The changes are explanatory only except where an unnecessary suppression was replaced by clearer
code; no supported runtime or persisted contract changed.

## Findings

- The repository contained no commented-out code and no `TODO`, `FIXME`, `HACK`, or `XXX` work markers.
  Durable work remains in owned roadmaps and issue records rather than source comments.
- The small number of ordinary Python comments generally explained real invariants: exhaustive event-algebra
  dispatch, crash-recovery commit points, lexical path containment, and archive-root inference.
- Several local lint suppressions were valid but unexplained. Others were avoidable because the code could
  express the intent directly.
- CSS section labels had accumulated historical implementation language such as “interaction polish,”
  “stable mode,” and “return-safe authoring.” One section was inaccurately labeled “Recovery console.”
- The public **Lead** vocabulary and persisted `Clue` vocabulary were not explained at the domain type seam,
  even though the distinction is a compatibility invariant.

## Corrections

- Every remaining inline `noqa` suppression now states its local rationale. Loopback URL checks, broad adapter
  containment, process-interruption cleanup, lexical path normalization, and exact authored punctuation are
  explicit rather than implicit exceptions.
- Direct defining-module imports remain in two fault-injection tests because the tests patch module-owned
  private seams and the architecture contract rejects package-facade imports. The request-handler override
  likewise retains the standard-library parameter name. Those local exceptions are now explicit. Two
  intentional invalid-type tests now express their runtime inputs through `Any` rather than suppression
  comments.
- CSS comments now name maintained structural regions: workspace catalog, themes and focus states, primary
  and secondary Play workspaces, encounter reader sections, ledgers, references, and Play-to-Author
  navigation. They no longer read like completed implementation tranches.
- The domain model now records that `Clue` is the stable persisted and Python name for a user-facing lead.
  Conceptual module and aggregate docstrings use “lead-driven” while compatibility-bearing symbols remain
  unchanged.

## Guardrails

Architecture tests now require every inline tool suppression to include a `--` rationale and reject work-item
markers in Python comments. They also reject development-session numbers in comments and docstrings. Ruff's
`ERA` rules remain the primary commented-out-code check, and the connected `docstring-format-checker` gate
remains the owner of public docstring shape.

Comments should explain why a constraint exists, why an unusual failure path is deliberate, or why a stable
compatibility name differs from the product vocabulary. They should not narrate visible mechanics, preserve
session history, or substitute for an owned maintenance record.

## Verification

- `make test` passed 1,341 deterministic tests in 31.95 seconds.
- The disjoint coverage partitions combined to 92 percent branch-aware coverage against the 90 percent floor.
- All 39 published-schema JSON documents, Python byte compilation, and the packaged JavaScript syntax check
  passed.
- The clean wheel built at 345,766 bytes and the complete installed beta lifecycle passed.
- The portable-source audit admitted 1,129 files.
- Fifteen browser tests passed; six live-loopback cases were blocked before application code loaded by
  `ERR_BLOCKED_BY_ADMINISTRATOR`.
- Ruff, Pyright, Hypothesis, and `docstring-format-checker` were unavailable in the audit environment.
