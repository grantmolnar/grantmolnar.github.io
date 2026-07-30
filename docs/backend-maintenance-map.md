# Backend maintenance map

This map identifies the authoritative seams and the next likely pressure points. It is guidance for
future changes, not a mandate to split files solely because they are long.

## Stable seams

### Domain

- `domain/adventure.py`: authored encounter, revelation, clue, and discovery-tag values.
- `domain/play_events.py`: append-only play-event algebra and closed event-kind vocabulary.
- `domain/play_state.py`: journal aggregate and projected play-state values.
- `domain/validation_models.py`: validator policy, issues, reports, and repair diagnostics.
- `domain/graph.py`: exact graph construction and connectivity algorithms.
- `domain/validation.py`: layered structural policy and diagnostics.

Domain code must not import application, infrastructure, or interface modules.

### Application

- `play_tracking.py`: stable actual-play command facade.
- `play_journal_validation.py`: persisted append-only journal invariants.
- `play_projection.py`: deterministic current-state and narrative projection.
- `play_ledgers.py`: scoped operational and player-safe read models.
- focused authoring, reporting, archive, workspace, and validation-setting use cases.

Application code owns orchestration over ports and domain values. It must not import local-file or
web adapters.

### Infrastructure

Local JSON and filesystem modules own serialization, migration, coordinated writes, and project
adapter implementations. They should not contain HTML, terminal presentation, or domain policy.

### Interfaces and process adapters

- `interfaces/cli.py`: argument definitions only.
- `interfaces/presentation.py`: terminal rendering only.
- `interfaces/web/*`: WSGI translation, forms, HTML, browser assets, and route workspaces.
- `cli_*_commands.py`: command-line orchestration over application use cases and local adapters.
- `web_composition.py`: local adapter wiring for browser applications.
- `bootstrap.py`: process dispatch and expected error translation.

## Current pressure points

### Browser application dispatch

`interfaces/web/app.py` owns the selected-adventure WSGI boundary, read routing, and delegation to
report, archive, Play, and authoring workspaces. `interfaces/web/authoring_action_workspace.py` owns the
complete revision-aware authoring POST family: form parsing, command construction, redirects, and
server-side form reconstruction. `interfaces/web/play_workspace.py` owns live-play, run, journal, and
ledger routes. Continue extraction only when another complete route family has an independent reason
to change; avoid moving isolated branches into helpers while leaving a central conditional coupled to
every feature.

### HTML rendering

`interfaces/web/play_rendering.py` remains the largest presentation module. Authoring, archive,
report, journal, run, and entity rendering now have explicit owner modules; there is no aggregate
rendering facade. Prefer extracting coherent page sections or reusable view components, and do not
introduce a template framework merely to reduce line counts.

### Validation policy

`domain/validation.py` should be split only along existing validation phases, with diagnostics and
ordering preserved by characterization tests. Do not distribute graph-policy decisions across model
methods.

### CLI authoring orchestration

Every CLI authoring mutation now crosses one revision-aware `LocalAuthoringProject` boundary. Clue and
revelation creation, editing, renaming, and movement reuse the browser's application commands; encounter
creation and dependency-aware removals use pure domain transformations against one loaded snapshot and
the shared related-journal integrity check. Do not add application wrappers for those remaining
single-adapter operations merely to make the process module shorter. Promote them when a second adapter
needs the same command semantics. Local paths remain outside the application layer.

## Conditional cleanup findings

These are contingent design pressure points, not scheduled work. Act only when the stated trigger occurs.

- `GetJournalWorkspace` and `GetPlayLedgerWorkspace` repeat inexpensive projection work. Introduce one
  private application-layer read context only if another composite read appears or profiling shows a
  material cost.
- `AdventureTags.__post_init__` validates several related collections and ranges. Extract named
  validators only when discovery metadata gains another dimension.
- Validator-policy metadata is repeated across domain, adapters, schemas, CLI flags, forms, and
  renderers. Consider one typed application-boundary descriptor table before adding another policy
  dimension; do not centralize merely to hide the current explicit contract.
- `PlayWebWorkspace._run_write` remains a small Recovery-console dispatcher. Split it only if that
  exceptional workflow gains another action or more complex draft-preservation behavior.
- `AuthoringWebApplication._page_response()` owns three stable authored entity families. Split the read
  side by entity only if a fourth family, another notice state, or reusable page orchestration creates a
  second concrete reason to change.
- `AuthoringActionWorkspace` is intentionally one complete POST route family. Split form-error
  reconstruction from command dispatch only if another adapter reuses one side independently or the
  error views acquire their own lifecycle.
- Encounter creation and dependency-aware removal remain pure domain transformations in the CLI adapter.
  Promote them to application use cases if a second adapter needs the same orchestration.
- Persistence, projections, Markdown, operational ledgers, and HTML intentionally remain separate
  exhaustive consumers of the play-event algebra. Add shared typed descriptors only when a new event
  kind demonstrates real duplicated structure; do not introduce a generic visitor that obscures
  persistence or presentation-specific behavior.

## Change discipline

Before extracting a module, identify:

1. its distinct reason to change;
2. the dependency direction after extraction;
3. the public or persisted contracts that must remain stable;
4. the focused tests that characterize that contract; and
5. the deleted duplication or reduced coupling that justifies the move.

A shorter file without a clearer responsibility is not a cleanup.

## Quality gates

The ordinary `make validate` gate is:

1. installed-package metadata consistency;
2. Ruff formatting and lint;
3. strict Pyright over the production package;
4. the default unit, integration, architecture, smoke, metadata, and tooling suite;
5. branch-aware coverage at or above the configured threshold; and
6. Deptry and Import Linter contracts.

CI runs that gate on CPython 3.11, 3.12, and 3.13. A separate required job runs Vulture, Radon,
docstring-format-checker, Bandit, and pip-audit once on Python 3.13. The clean built wheel is then
installed and exercised on Linux, Windows, and macOS. Mutation testing remains a deliberate periodic
gate rather than a per-commit blocker.

## Private-beta release audit disposition

The pre-release breaking-change audit found no module extraction whose benefit outweighed its churn. The
release-path responsibilities above remain the intended boundaries. The accepted corrections were instead
placed at shared application and persistence seams: one canonical JSON byte ceiling, one archive-identifier
contract, and bounded title-derived browser download names. See
[`private-beta-breaking-change-audit.md`](private-beta-breaking-change-audit.md) for the retained contracts and
explicit deferred triggers.
