# Maintainer guide

This guide collects source-snapshot, native desktop packaging, and development-quality procedures. It is
for maintainers working from a source checkout; beta testers should begin with the [beta guide](beta-guide.md).

## Portable source snapshots

Maintainer handoffs use a descriptive ZIP filename but a short, stable `adventure-graph/` internal root.
This avoids repeating long session labels inside every member path and preserves a declared Windows
extraction budget without renaming UUID-backed generated documents. Audit, build, and verify with:

```bash
make source-audit
make source-package
make source-verify
```

Set `SOURCE_SNAPSHOT_PATH` when the external handoff filename should include a workstream or session label.
The builder is deterministic, excludes local build state and environment files, and verifies the completed
archive before returning success. See [portable source snapshots](source-snapshots.md) for the archive
contract and ordinary Windows Explorer acceptance check.

## Desktop launcher and exporting native bundles

Adventure Graph includes a thin desktop launcher around the same loopback browser application. The
launcher uses the operating system's directory chooser, remembers the last existing workspace in the
user configuration area, starts one owned server on an available loopback port, opens the default
browser, and stops that server when the launcher closes. It does not duplicate the product UI or store
adventure data inside the application bundle.

Developers can exercise the launcher from an installed source tree with:

```bash
adventure-graph-desktop
```

### Export all supported desktop apps from WSL or another maintainer shell

The recommended multi-platform export path is the checked-in GitHub Actions workflow. WSL acts as the
control shell; each artifact is built and smoke-tested on its native hosted operating system. Commit and
push the exact source revision first, then run:

```bash
gh auth login
BRANCH="$(git branch --show-current)"
gh workflow run desktop.yml --ref "$BRANCH"
gh run list --workflow desktop.yml --limit 5
# Replace <run-id> with the workflow-dispatch run shown above.
gh run watch <run-id>
rm -rf dist/desktop-evidence
gh run download <run-id> --dir dist/desktop-evidence
python scripts/verify_desktop_artifacts.py dist/desktop-evidence \
  --require-platforms linux windows macos \
  --source-revision "$(git rev-parse HEAD)"
```

The download contains one native archive and adjacent manifest per platform. The verifier checks hashes,
internal inventory, safe paths, exact build dependencies, native runner provenance, architecture, and one
shared source revision. A PyInstaller process running inside WSL itself produces a Linux artifact only; it
does not cross-compile Windows or macOS. Use Windows Python for a local Windows build, and a native Mac or
the hosted workflow for macOS.

### Build only the current operating system locally

On a native development machine with the exact build lock available:

```bash
make install-desktop-build
ADVENTURE_GRAPH_SOURCE_REVISION="$(git rev-parse HEAD)" make desktop-package
make desktop-verify
```

Windows maintainers without `make` can run the equivalent Python commands from PowerShell; the
[desktop distribution guide](desktop-distribution.md) includes the complete WSL/PowerShell procedure.
Build output is written under `dist/desktop/`. Linux produces a `.tar.gz`; Windows and macOS produce
`.zip` archives, with the macOS archive containing `Adventure Graph.app`.

Every archive excludes user adventures, smoke-tests the frozen executable, carries a strict manifest, and
must remain below the 100 MiB compressed ceiling. Signing, notarization, installer packaging, native manual
interaction, and final release approval are separate gates. See the
[desktop distribution guide](desktop-distribution.md) for the artifact contract and release sequence.

## Development

The [test strategy](test-strategy.md) defines the durable quality tiers and the boundary between policy and
revision-specific evidence. Create and activate a virtual environment first, then:

```bash
make install
make test-fast       # Runtime-focused local feedback
make test            # Full local deterministic and corpus suite
make test-corpus     # Bundled-adventure/editorial contracts
make test-property   # Mandatory feature-local Hypothesis evidence
make test-browser    # Executable Chromium behavior
make lint
make format
make format-check
make validate
make validate-all
# `make validate` requires every declared development tool, including Hypothesis.
# Install Chromium once for the browser gate with:
python -m playwright install chromium
# Maintainer source snapshots:
make source-audit
make source-package
make source-verify
# Native desktop packaging, when needed:
make install-desktop-build
make desktop-package
make desktop-verify
```

The package uses clean-architecture layering:

```text
interfaces / infrastructure
          ↓
      application
          ↓
        domain
```

`adventure_graph.bootstrap` is the minimal process entry point. Package-root CLI command modules and
`web_composition.py` wire outer adapters to application use cases; domain validation does not depend
on JSON, Markdown, the CLI, or filesystem state.
