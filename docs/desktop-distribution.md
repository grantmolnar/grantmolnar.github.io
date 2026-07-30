# Desktop distribution

## Purpose

The desktop build is a thin native launcher around the existing Adventure Graph runtime. It does not
replace the loopback browser application, duplicate Author or Play behavior, or introduce a second
persistence format. The wheel, CLI, and desktop bundle use the same WSGI application, schemas, workspace
discovery, application commands, and browser assets.

The launcher lets a tester double-click an application instead of installing Python or using a terminal. A
small native window chooses or remembers one workspace, owns one loopback server, opens the ordinary browser
interface, and stops that server when the launcher closes.

## What exporting means

Exporting the app freezes the current source revision and Python runtime into one native, one-folder bundle
for a specific operating system. It does not export or embed adventures. User projects, journals, archives,
reports, and launcher settings remain outside the application bundle.

PyInstaller builds for the operating system on which it runs. A Linux process inside WSL therefore produces
a Linux artifact only. Windows requires Windows Python or a Windows runner; macOS requires a native Mac or a
macOS runner. WSL is useful as the control shell for the hosted multi-platform workflow, not as a macOS or
Windows cross-compiler.

## User-data boundary

The bundle contains runtime code and static package resources only. It must not contain or create a
canonical `adventure.json`, `play-state.json`, journal archive, generated report, or workspace settings file
inside the installation directory.

The remembered workspace path is stored in the user's configuration area:

- Windows: `%LOCALAPPDATA%\Adventure Graph\launcher-settings.json`
- macOS: `~/Library/Application Support/Adventure Graph/launcher-settings.json`
- Linux: `$XDG_CONFIG_HOME/adventure-graph/launcher-settings.json`, or
  `~/.config/adventure-graph/launcher-settings.json` when `XDG_CONFIG_HOME` is unset

`ADVENTURE_GRAPH_CONFIG_HOME` overrides this location for isolated tests. The selected workspace and all
adventure data remain ordinary user-owned directories outside the application bundle.

## Runtime lifecycle

1. The launcher loads the last existing workspace, if any.
2. Otherwise it opens the operating system's directory chooser.
3. It composes the existing workspace web application.
4. It binds one server to `127.0.0.1` on port `0`, allowing the operating system to choose an available
   local port.
5. It opens the resulting URL in the user's default browser.
6. **Open in browser** reopens the same server without starting another one.
7. Choosing another workspace stops the previous server before starting the replacement.
8. Closing the launcher shuts down the owned server and releases its socket.

The browser remains the product interface. The native window is only a lifecycle and workspace-selection
shell.

## Recommended multi-platform export from WSL

The checked-in `.github/workflows/desktop.yml` workflow is the simplest reproducible way to obtain Linux,
Windows, and macOS artifacts from the same source revision. Before dispatching it:

1. commit the exact source to build;
2. push that commit to GitHub;
3. confirm the GitHub CLI is authenticated; and
4. run the workflow against the branch containing that commit.

From WSL or another shell with `git` and `gh`:

```bash
gh auth login
BRANCH="$(git branch --show-current)"
gh workflow run desktop.yml --ref "$BRANCH"
gh run list --workflow desktop.yml --limit 5
```

Copy the workflow-dispatch run ID, then wait for and download that exact run:

```bash
gh run watch <run-id>
rm -rf dist/desktop-evidence
gh run download <run-id> --dir dist/desktop-evidence
python scripts/verify_desktop_artifacts.py dist/desktop-evidence \
  --require-platforms linux windows macos \
  --source-revision "$(git rev-parse HEAD)"
```

Do not verify against an uncommitted working tree: the hosted manifests record the pushed commit, not local
uncommitted changes. `gh run download` may create one subdirectory per uploaded artifact; the verifier scans
recursively.

The workflow installs the exact checked-in build dependency lock, builds on native hosted runners,
smoke-tests each frozen executable, uploads each archive with its adjacent manifest, and runs an independent
aggregate verification job. The aggregate verifier follows valid in-bundle symbolic-link chains, including
macOS framework links whose path traverses another link, while rejecting absolute targets, root escape,
cycles, and missing final members. The downloaded evidence set is ready for native manual testing only after
the local verifier also passes.

## Local build for the current operating system

The exact build dependencies are pinned in `packaging/desktop-build-requirements.txt`. On Linux or macOS,
or on Windows with GNU Make available:

```bash
make install-desktop-build
ADVENTURE_GRAPH_SOURCE_REVISION="$(git rev-parse HEAD)" make desktop-package
make desktop-verify
```

Equivalent direct commands are:

```bash
python -m pip install -r packaging/desktop-build-requirements.txt
python -m pip install --no-build-isolation --no-deps -e .
python -m pip check
ADVENTURE_GRAPH_SOURCE_REVISION="$(git rev-parse HEAD)" \
  python scripts/build_desktop.py --output-dir dist/desktop
python scripts/verify_desktop_artifacts.py dist/desktop
```

For destructive-cleanup safety, `--output-dir` must remain inside the repository `dist/` directory.

## Local Windows build controlled from WSL

Keep the checkout on the Windows filesystem when Windows Python is building it, for example
`C:\dev\adventure-graph`, visible from WSL as `/mnt/c/dev/adventure-graph`. Open Windows PowerShell from WSL
with `powershell.exe`, then run the build with Windows Python:

```powershell
Set-Location C:\dev\adventure-graph
py -3.13 -m venv .venv-desktop
.\.venv-desktop\Scripts\python.exe -m pip install `
  -r packaging\desktop-build-requirements.txt
.\.venv-desktop\Scripts\python.exe -m pip install `
  --no-build-isolation --no-deps -e .
.\.venv-desktop\Scripts\python.exe -m pip check
$env:ADVENTURE_GRAPH_SOURCE_REVISION = (git rev-parse HEAD)
.\.venv-desktop\Scripts\python.exe scripts\build_desktop.py `
  --output-dir dist\desktop
.\.venv-desktop\Scripts\python.exe scripts\verify_desktop_artifacts.py `
  dist\desktop
```

This produces only the Windows archive. Use the hosted workflow or a native Mac for the macOS archive.

## Build and artifact contract

PyInstaller creates a one-folder bundle. One-folder mode keeps startup transparent, makes contents
inspectable, and avoids extracting the runtime into a temporary directory on every launch. The bundle must
remain below the project's 100 MiB compressed ceiling.

The build script:

- removes prior desktop outputs unless `--no-clean` is supplied;
- verifies the exact platform-specific build dependency lock;
- runs the checked-in PyInstaller specification;
- excludes development-only tools and canonical user data;
- launches the frozen executable in headless smoke mode against an empty temporary workspace;
- confirms smoke mode does not persist launcher settings;
- creates a normalized platform archive;
- enforces the compressed-size ceiling; and
- writes a versioned JSON manifest containing source revision, version, platform, architecture, Python and
  PyInstaller versions, complete build dependencies, exact build dependency lock SHA-256, native runner provenance, compressed
  and unpacked sizes, file and symbolic-link counts, archive SHA-256, and bundle-inventory SHA-256.

Linux produces `.tar.gz`; Windows and macOS produce `.zip`. The macOS archive contains `Adventure Graph.app`.
Artifact names include the version, platform, and architecture; consumers should use the adjacent manifest
rather than infer compatibility from a remembered filename.

Verify one local or downloaded evidence directory with:

```bash
python scripts/verify_desktop_artifacts.py dist/desktop
```

Verify a complete hosted evidence set with:

```bash
python scripts/verify_desktop_artifacts.py dist/desktop-evidence \
  --require-platforms linux windows macos \
  --source-revision <accepted-commit-sha>
```

`make desktop-verify` runs the single-directory form and accepts `DESKTOP_ARTIFACT_DIR` as an override.

## Release sequence

A successful build is not by itself a public release. For each accepted source revision:

1. build every supported native artifact from that exact revision;
2. pass archive and manifest verification;
3. execute the frozen headless smoke;
4. run the checked-in manual protocol on real target systems;
5. resolve objective platform defects and rebuild every affected artifact;
6. complete Signing, notarization, and any installer packaging required beyond a private unsigned beta; and
7. publish only the final verified archives and their matching manifests.

Automated tests cover every non-Tk launcher branch. The native protocol remains necessary for directory
selection, default-browser integration, reopen, workspace switching, close behavior, display scaling,
keyboard use, long notes, archive operations, restart, relocation, malformed-file recovery, and operating-
system trust prompts. An unsigned locally built artifact is not represented as a signed or platform-approved
public release.
