# Private-beta release qualification evidence

> **Historical evidence record.** This file records the exact local candidate described below. It predates
> subsequent Lead-presentation and compatibility-safe maintenance changes and must not be read as evidence
> for a descendant source tree. Later handoffs are revision-specific addenda; a distributable candidate must
> refresh every affected gate against one newly frozen revision.

## Decision

The Adventure Graph 0.10.0 application-and-sample tree captured by this record was accepted as the
local executable, packaging, and maintenance candidate for connected qualification and native artifact
construction. The
deterministic runtime, schemas, browser-static contracts, repository cleanup, wheel, installed-wheel
workflow, and source portability passed in this environment. The tester-facing runtime contains one
packaged adventure template, *The Glass Saint*.

This is not native platform signoff. Strict formatter, lint, type, property, dependency-analysis,
complexity, docstring, and security tools are unavailable in this restricted environment. Browser policy
also blocks live Playwright navigation to loopback. Those gates, native artifact construction, manifest
verification, and the real-platform manual protocol must run against this exact source revision before an
artifact is handed to a tester.

## Source under qualification

- Project version: `0.10.0`.
- Runtime under test: CPython 3.13.5 on Linux x86_64.
- Adventure schema: 3.
- Play-state schema: 6.
- Workspace-settings schema: 1.
- Wheel: `adventure_graph-0.10.0-py3-none-any.whl`.
- Wheel size: 356,089 bytes.
- Wheel SHA-256: `5e5307b0b77e02a8e575c71f55e4beb002fad70d853a173ddfefba568230b15a`.
- Portable source-tree audit before the final handoff: 1,150 admitted files.

The final portable snapshot is rebuilt after the handoff is added. Its final file count, digest, and
archive size belong in that handoff rather than being copied back into this durable qualification record.

## Passed local evidence

### Deterministic Python tests and coverage

The deterministic suite passed in bounded complete partitions:

- 710 unit tests;
- 431 integration tests;
- 54 architecture tests;
- 49 smoke tests; and
- 45 package, metadata, and tooling-contract tests.

That is 1,289 passing deterministic tests. The same selection passed under bounded branch instrumentation
at 92% combined coverage, above the checked-in 80% minimum. Four optional Hypothesis property modules were
not executed because Hypothesis is unavailable; no property result is inferred from that absence.

### Browser contracts

Fifteen executable Chromium tests passed for the Adventures catalog, sample onboarding, transfer forms,
responsive containment, reference notes, and static Play layout contracts. The six live-server Playwright
cases failed only at navigation to `127.0.0.1` with `ERR_BLOCKED_BY_ADMINISTRATOR`, before application code
loaded. They remain unverified browser evidence, not product failures and not passing loopback evidence.

The application-wide Help page now exposes the installed Adventure Graph version and privacy-conscious
feedback guidance without displaying local paths, project contents, revision hashes, or diagnostic codes.

### Schemas, syntax, package, and installed lifecycle

- All 39 canonical and sparse-compatible JSON documents passed schema validation.
- Python byte-compilation passed for `src`, `tests`, `scripts`, and `packaging`.
- Every shipped JavaScript file passed `node --check`.
- The wheel built without third-party runtime dependencies and contains exactly one adventure JSON resource:
  `the-glass-saint.adventure.json`.
- The isolated installed-wheel beta lifecycle passed title-only Play onboarding, explicit browser sample
  onboarding, CLI and browser authoring, multi-session play, correction, persistent-reference notes, archive
  lifecycles, recorded browser dice, malformed-file repair, Unicode and spaced paths, direct project-directory
  launch, multi-project selection refusal, relocation, both CLI entry points, the installed desktop-launcher
  entry point, and repeated UI launch.
- `pip check` passed inside the isolated wheel environment.

### Repository cleanup and portable source

The wheel build reproduced `src/adventure_graph.egg-info`, the nested editable-install metadata that survived
the former root-only cleanup command during the final corpus packaging run. The new tested Python cleanup
removed that directory, all `__pycache__` directories, coverage files, caches, and root build outputs while
preserving authored source. The source-snapshot builder also excludes parallel `.coverage.*` data directly,
so audit and build safety do not depend on cleanup order. The source portability audit then passed the
stable-root, archive-safety, Windows-path, and inventory contracts.

## Unavailable or external gates

The following checked-in gates remain unclaimed:

- Ruff formatting and lint;
- strict Pyright;
- Hypothesis property tests;
- Deptry and Import Linter;
- Vulture and Radon;
- docstring-format-checker;
- Bandit and pip-audit;
- all six live-server Playwright tests;
- PyInstaller construction and frozen-executable smoke; and
- real Linux, Windows, and macOS interaction through the manual protocol.

The native build environment remains unavailable. The exact checked-in desktop dependency lock must not be
weakened to manufacture an artifact in a mismatched environment.

## Maintainer qualification sequence

Run the following from the exact source snapshot intended for distribution in a connected development
environment:

```bash
python -m venv .venv-quality
source .venv-quality/bin/activate
python -m pip install -e ".[dev]"
make ci
make test-browser
```

On Windows PowerShell, activate the environment with
`.venv-quality\Scripts\Activate.ps1`. Resolve every failure in source and rebuild the source snapshot; do
not waive a gate merely because an executable is needed soon.

Build the native artifact in a fresh environment on the target operating system:

```bash
python -m venv .venv-desktop
source .venv-desktop/bin/activate
make install-desktop-build
make desktop-package
make desktop-verify
```

Then execute `docs/beta-platform-manual-protocol.md` against the frozen artifact on that real operating
system. Retain the adjacent manifest and checksum evidence with the artifact sent to the tester.

## Release boundary

Once the connected static, property, live-browser, native-build, manifest, and manual checks pass, this
source revision may be treated as the next private-beta distribution candidate. Any source change after
that qualification invalidates the wheel, source digest, native artifact, and manual evidence and must
restart the affected gates.
