# Engineering Standards

Adventure Graph is a small local-first package. Its engineering rules should protect the authored
adventure, the append-only play journal, and the clarity of its user interfaces without
introducing infrastructure the project does not use.

## Dependency direction

Dependencies point inward:

```text
interfaces / infrastructure -> application -> domain
```

- `domain` owns authored entities, play events, graph algorithms, and structural rules.
- `application` owns authoring transformations, play-state use cases, projections, and document
  generation.
- `interfaces` owns transport parsing and presentation, including the CLI and local web adapters.
- `infrastructure` owns versioned JSON, crash-recoverable local-file writes, and generated output.
- Package-root process adapters compose the outer layers: `bootstrap.py` dispatches,
  `cli_*_commands.py` execute terminal workflows, and `web_composition.py` wires browser
  applications.

Domain and application modules must not read files, print output, inspect process arguments or
HTTP requests, render interface markup, or import outward-facing layers. Interfaces may import
application contracts but must not import infrastructure implementations; package-root process
adapters wire them together.

## Module boundaries

A module should have one reason to change. In particular:

- authored-adventure serialization and play-journal serialization remain separate;
- local transaction and atomic replacement mechanics are independent of every JSON schema;
- CLI parsing is independent of command execution;
- CLI presentation is independent of persistence; and
- generated Markdown is derived output, never the source of truth.

Do not add an abstraction until two real callers require the same concept. Remove dead compatibility
layers instead of preserving hypothetical uses.

## Domain and state invariants

- Authored values are immutable dataclasses.
- Clues have one source encounter and support one revelation.
- Revelation establishment is distinct from clue discovery.
- Encounter availability is explicit and must precede a visit unless the encounter is a start.
- Play state is append-only; corrections append audit events and ordinary edits do not rewrite
  history.
- User-facing titles and durable internal identifiers have separate lifecycles. Title changes preserve
  identifiers and historical references; removals and semantic edits may not falsify recorded events.
- Multi-file canonical commits cross an explicit local transaction commit point and recover before decoding.
- One Adventure Graph writer process may mutate a workspace at a time. Optimistic revisions reject
  stale requests but do not provide a cross-process file lock.

Changes to these rules require focused tests and corresponding documentation updates.

## Code

- Use intention-revealing names and narrow functions.
- Prefer structured return values to string protocols.
- Keep I/O and printing at the edges.
- Raise specific boundary errors; do not catch broad exceptions inside package logic.
- Do not mutate `sys.path`, invoke shell commands through unsafe APIs, or perform work at import
  time.
- Keep production source clean under strict Pyright and keep source and tests clean under Ruff.
  Pytest fixtures, monkeypatches, corpus JSON dictionaries, and deliberate private-helper tests are
  validated by runtime and architecture tests rather than strict unknown-type diagnostics.
- Run Bandit through the repository configuration. B608 is disabled because the package has no SQL
  layer and its HTML form templates trigger that heuristic; re-enable it before introducing any
  database access.
- Comments explain non-obvious constraints, invariants, or deliberately unusual failure handling; they do
  not narrate mechanics already visible in code or preserve session progress.
- Put repository-wide lint exceptions and their rationale in `pyproject.toml`. Keep an inline suppression
  only when the exception is genuinely local and the reason would be lost at configuration level.

## Commands and entry points

The supported entry points are the installed `adventure-graph` console command and
`python -m adventure_graph`. Both dispatch through `adventure_graph.bootstrap:main`; there is no
second script implementation.

A new interface operation should have:

1. transport parsing and presentation in the relevant interface adapter;
2. transport-neutral coordination in an application command or query;
3. reusable rules in the appropriate application or domain module;
4. effectful behavior behind application-facing ports; and
5. integration coverage for success and refusal paths.

Package-root process adapters construct adapters and use cases. `bootstrap.py` should remain a small
dispatcher, and no process-adapter module should become the permanent home of behavior shared by
more than one interface.

## Tests

- Unit tests live beside the layer they exercise.
- Integration tests cover CLI-to-storage workflows and transaction persistence.
- Architecture tests guard dependency direction, import-time discipline, repository hygiene, and
  test discipline.
- Property tests remain beside the graph behavior they verify, but dependency-heavy property modules
  must be isolated so deterministic tests remain collectable when optional developer tools are
  absent.
- Skips and xfails require explicit reasons.
- Every repaired bug receives a regression test.

The default suite must remain fast and deterministic. External advisory-data checks, such as
`pip-audit`, are separate from the local deterministic validation gate.

## Documentation and release discipline

- `README.md` is the concise product entry point: installation, first launch, primary concepts,
  compatibility boundary, and links to owned guides.
- `docs/README.md` is the documentation navigation owner and must link every Markdown document under
  `docs/`.
- `docs/cli-reference.md` owns complete command syntax and CLI workflows.
- `docs/maintainer-guide.md` owns source-snapshot, desktop-export, and connected development procedures.
- `docs/architecture.md` records boundaries and non-obvious design decisions.
- Commit durable contracts, operating guidance, active roadmaps, release history, and evidence that is
  still needed to reproduce a quality claim. Do not retain per-session handoffs, completed cleanup
  diaries, or tranche reports after their outcomes have been consolidated.
- Keep handoff notes outside the repository artifact unless they define an active contract that has no
  durable owner yet. Before packaging, remove stale progress comments and verify that documentation
  contains no links to deleted records.
- Bundled adventure directories contain authoritative JSON, reproducible generated output, subordinate
  demonstration state, concise adventure guidance, and maintained table aids. Completed construction
  sessions, editorial audits, stress-test reports, build plans, and reference-extraction logs are not
  maintained corpus artifacts; consolidate their durable conclusions and remove the workbench files.
- Schema and lifecycle documents must match the actual persisted formats and refusal behavior.
- Missing attributes introduced within the current schema version load through explicit model
  defaults; canonical saves materialize the complete current shape. Present malformed values still
  fail at the persistence boundary.
- The packaged Glass Saint template and repository example are byte-identical.
- Incompatible schema-version changes must migrate every bundled example and be described explicitly
  in release notes; do not retain dead compatibility paths.

- `make validate` is the required deterministic gate and includes branch-aware coverage at or above
  the configured threshold.
- CI runs that gate on every supported Python minor version, runs the heavier dead-code, complexity,
  docstring, and security gates once, and exercises the built wheel on Linux, Windows, and macOS.
- Package metadata, documentation, and CI must name the same supported Python range and
  distribution terms.

## Desktop distribution discipline

- The native launcher is a lifecycle shell around the existing browser application, not a second UI.
- User projects, workspace settings, and launcher settings must remain outside the application bundle.
- Desktop builds are native per operating system; do not describe a locally built artifact as evidence for
  another platform.
- Every bundle must pass the frozen-executable smoke, canonical-user-data exclusion, archive-size ceiling,
  and strict manifest generation before upload. The hosted matrix must then download and independently
  verify the complete Linux, Windows, and macOS evidence set from one source revision.
- Signing, notarization, manual platform interaction, and final GM acceptance are release gates distinct
  from successful compilation.
